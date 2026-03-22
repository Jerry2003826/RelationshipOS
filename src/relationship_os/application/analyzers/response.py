"""Response drafting, rendering, post-audit, sequencing, and normalization."""

from __future__ import annotations

import re

from relationship_os.application.analyzers._utils import (
    _compact,
    _contains_any,
    _contains_chinese,
)
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    ConversationCadencePlan,
    EmpowermentAudit,
    ExpressionPlan,
    GuidancePlan,
    KnowledgeBoundaryDecision,
    PolicyGateDecision,
    RehearsalResult,
    RepairAssessment,
    RepairPlan,
    ResponseDraftPlan,
    ResponseNormalizationResult,
    ResponsePostAudit,
    ResponseRenderingPolicy,
    ResponseSequencePlan,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
)


def build_response_draft_plan(
    *,
    context_frame: ContextFrame,
    policy_gate: PolicyGateDecision,
    repair_plan: RepairPlan,
    confidence_assessment: ConfidenceAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    expression_plan: ExpressionPlan,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
) -> ResponseDraftPlan:
    opening_move = "acknowledge_and_orient"
    structure = ["name the current context", "offer one concrete next step"]
    must_include = list(expression_plan.goals)
    must_avoid = list(expression_plan.avoid)
    phrasing_constraints: list[str] = []
    question_strategy = "none"

    if repair_plan.rupture_detected:
        opening_move = "repair_then_orient"
        structure = [
            "briefly acknowledge the user's current state",
            "repair understanding",
            "offer one concrete next step",
        ]

    if runtime_coordination_snapshot.ritual_phase == "opening_ritual":
        structure.insert(0, "set a simple session frame")
    elif runtime_coordination_snapshot.ritual_phase == "re_anchor":
        structure.insert(0, "briefly re-anchor shared context")

    if guidance_plan.lead_with == "regulate_first":
        opening_move = "stabilize_then_orient"
    elif guidance_plan.lead_with == "attunement_repair":
        opening_move = "repair_then_orient"
    elif guidance_plan.lead_with == "clarify_gap":
        opening_move = "clarify_with_reason"
    elif guidance_plan.lead_with == "boundary_frame":
        opening_move = "bound_the_answer"
    elif guidance_plan.lead_with == "shared_context_reanchor":
        structure.insert(0, "briefly re-anchor shared context")
    elif guidance_plan.lead_with == "micro_commitment":
        structure.insert(0, "guide one small next step")
    elif guidance_plan.lead_with == "reflect_then_step":
        structure.insert(0, "briefly reflect the user's state")

    if runtime_coordination_snapshot.cognitive_load_band == "high":
        opening_move = "stabilize_then_orient"
        phrasing_constraints.append(
            "keep processing load low with shorter and more concrete sentences"
        )
    if guidance_plan.ritual_action:
        structure.insert(0, guidance_plan.ritual_action.replace("_", " "))
    if session_ritual_plan.opening_move:
        structure.insert(0, session_ritual_plan.opening_move.replace("_", " "))
    if guidance_plan.checkpoint_style:
        structure.append(guidance_plan.checkpoint_style.replace("_", " "))
    if session_ritual_plan.bridge_move:
        structure.append(session_ritual_plan.bridge_move.replace("_", " "))
    if cadence_plan.turn_shape == "question_then_pause":
        structure.append("pause after the focused question")
    elif cadence_plan.turn_shape == "reanchor_then_step":
        structure.insert(0, "re-open with a shared-context bridge")
    elif cadence_plan.turn_shape == "reflect_then_step":
        structure.insert(0, "reflect briefly before naming the next step")
    if cadence_plan.next_checkpoint:
        structure.append(cadence_plan.next_checkpoint.replace("_", " "))

    phrasing_constraints.append(
        f"offer no more than {guidance_plan.step_budget} guided step(s) at once"
    )
    if guidance_plan.pacing == "slow":
        phrasing_constraints.append("slow the tempo before advancing")
    elif guidance_plan.pacing == "gentle":
        phrasing_constraints.append("re-enter gently instead of pushing pace")
    if guidance_plan.agency_mode in {
        "explicit_autonomy",
        "low_pressure_invitation",
        "light_reentry",
    }:
        must_include.append("keep the user's choice explicit")
    if cadence_plan.user_space_mode in {
        "spacious",
        "explicit_autonomy_space",
        "consent_space",
    }:
        phrasing_constraints.append(
            "leave deliberate conversational space after the checkpoint"
        )
    if guidance_plan.agency_mode == "focused_question":
        question_strategy = "single_focused_question"
    must_include.extend(guidance_plan.micro_actions[:2])
    must_include.extend(cadence_plan.cadence_actions[:2])
    must_include.extend(session_ritual_plan.micro_rituals[:2])
    must_include.extend(somatic_orchestration_plan.micro_actions[:2])
    if guidance_plan.handoff_mode in {
        "resume_bridge",
        "no_pressure_checkin",
        "autonomy_preserving_ping",
    }:
        must_include.append("leave a clear low-pressure handoff")
    if cadence_plan.somatic_track != "none":
        must_include.append("include one brief grounding cue before progress")
    if session_ritual_plan.somatic_shortcut != "none":
        must_include.append("start with one simple body-based reset")
    if somatic_orchestration_plan.status == "active":
        phrasing_constraints.extend(somatic_orchestration_plan.phrasing_guardrails[:2])
        if somatic_orchestration_plan.allow_in_followup:
            must_include.append("keep the body cue reusable in later follow-up")
    if cadence_plan.transition_intent == "pause_for_missing_detail":
        question_strategy = "single_focused_question"

    if knowledge_boundary_decision.decision == "answer_with_uncertainty":
        opening_move = "bound_the_answer"
        must_include.extend(
            [
                "state limits explicitly",
                "pair uncertainty with a bounded next step",
            ]
        )
        must_avoid.append("false_certainty")
        phrasing_constraints.append(
            "use calibrated language instead of guarantees or predictions"
        )
    elif knowledge_boundary_decision.decision == "clarify_before_answer":
        opening_move = "clarify_with_reason"
        question_strategy = "single_focused_question"
        must_include.extend(
            [
                "explain why the clarifying question helps",
                "ask only one focused question",
            ]
        )
        must_avoid.append("multi_question_barrage")
        phrasing_constraints.append("keep the clarifying question concrete and short")
    elif expression_plan.include_question:
        question_strategy = "check_alignment"

    if policy_gate.red_line_status == "boundary_sensitive":
        must_include.append("frame support collaboratively")
        must_avoid.extend(
            [
                "exclusive_rescue_language",
                "dependency_reinforcement",
            ]
        )
        phrasing_constraints.append(
            "avoid implying the assistant is the user's only source of support"
        )

    if confidence_assessment.response_mode == "repair_first":
        structure.insert(0, "slow the tempo before giving direction")
    if rehearsal_result.projected_risk_level == "high":
        phrasing_constraints.extend(rehearsal_result.recommended_adjustments[:2])
    if empowerment_audit.transparency_required:
        must_include.append("make uncertainty or limits visible")
    if empowerment_audit.status == "revise":
        opening_move = "slow_down_and_reframe"
        phrasing_constraints.extend(empowerment_audit.recommended_adjustments[:2])

    return ResponseDraftPlan(
        opening_move=opening_move,
        structure=_compact(structure, limit=4),
        must_include=_compact(must_include, limit=5),
        must_avoid=_compact(must_avoid, limit=5),
        phrasing_constraints=_compact(phrasing_constraints, limit=5),
        question_strategy=question_strategy,
        approved=empowerment_audit.approved,
    )


def build_response_rendering_policy(
    *,
    context_frame: ContextFrame,
    confidence_assessment: ConfidenceAssessment,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    response_draft_plan: ResponseDraftPlan,
    empowerment_audit: EmpowermentAudit,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
) -> ResponseRenderingPolicy:
    rendering_mode = "supportive_progress"
    max_sentences = 4
    include_validation = context_frame.appraisal == "negative"
    include_next_step = True
    include_boundary_statement = False
    include_uncertainty_statement = (
        knowledge_boundary_decision.should_disclose_uncertainty
    )
    question_count_limit = 0
    style_guardrails = list(response_draft_plan.phrasing_constraints)

    if repair_assessment.repair_needed:
        rendering_mode = "repair_first"
        include_validation = True
    if confidence_assessment.response_mode == "clarify":
        rendering_mode = "clarifying"
        max_sentences = 3
        include_next_step = False
        question_count_limit = 1
        style_guardrails.append("ask no more than one clarifying question")
    elif confidence_assessment.response_mode == "calibrated":
        rendering_mode = "calibrated"
        include_uncertainty_statement = True
    elif knowledge_boundary_decision.decision == "support_with_boundary":
        rendering_mode = "boundary_support"
        include_boundary_statement = True
        include_validation = True
    elif empowerment_audit.status == "revise":
        rendering_mode = "guardrailed_reframe"
        max_sentences = 3
        include_validation = True

    if response_draft_plan.question_strategy == "single_focused_question":
        question_count_limit = 1
    elif response_draft_plan.question_strategy == "check_alignment":
        question_count_limit = max(question_count_limit, 1)

    if runtime_coordination_snapshot.cognitive_load_band == "high":
        max_sentences = min(max_sentences, 3)
        style_guardrails.append("reduce cognitive load with shorter chunks")
        if confidence_assessment.response_mode != "clarify":
            question_count_limit = min(question_count_limit, 1)
    elif runtime_coordination_snapshot.cognitive_load_band == "medium":
        max_sentences = min(max_sentences, 4)

    if runtime_coordination_snapshot.time_awareness_mode in {"reengagement", "resume"}:
        include_validation = True
        style_guardrails.append("briefly re-anchor shared context before progressing")

    if runtime_coordination_snapshot.proactive_followup_eligible:
        style_guardrails.append(
            "leave room for a light future follow-up instead of over-explaining now"
        )

    if knowledge_boundary_decision.decision == "support_with_boundary":
        include_boundary_statement = True
    if not response_draft_plan.approved or not empowerment_audit.approved:
        rendering_mode = "guardrailed_reframe"
        max_sentences = min(max_sentences, 3)

    return ResponseRenderingPolicy(
        rendering_mode=rendering_mode,
        max_sentences=max_sentences,
        include_validation=include_validation,
        include_next_step=include_next_step,
        include_boundary_statement=include_boundary_statement,
        include_uncertainty_statement=include_uncertainty_statement,
        question_count_limit=question_count_limit,
        style_guardrails=_compact(style_guardrails, limit=5),
        approved=response_draft_plan.approved and empowerment_audit.approved,
    )


def _count_sentences(text: str) -> int:
    parts = [part.strip() for part in re.split(r"[.!?。！？]+", text) if part.strip()]
    return len(parts)


def _contains_forbidden_false_certainty_language(text: str) -> bool:
    lowered = text.lower()
    english_patterns = [
        "definitely will",
        "will definitely",
        "guaranteed to",
        "absolutely will",
    ]
    chinese_patterns = ["一定会", "绝对会", "肯定会", "保证会", "百分之百会"]
    if any(pattern in lowered for pattern in english_patterns):
        return True
    if "for sure" in lowered and not any(
        safe_phrase in lowered
        for safe_phrase in ["can't know for sure", "cannot know for sure", "not for sure"]
    ):
        return True
    return any(
        pattern in text for pattern in chinese_patterns
    )


def _contains_forbidden_dependency_language(text: str) -> bool:
    lowered = text.lower()
    english_patterns = [
        "only one who can help",
        "your only support",
        "only support you need",
        "can't do without me",
    ]
    chinese_patterns = ["只有我能帮你", "只能靠我", "我是你唯一", "唯一依赖"]
    return any(pattern in lowered for pattern in english_patterns) or any(
        pattern in text for pattern in chinese_patterns
    )


def build_response_post_audit(
    *,
    assistant_response: str,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
) -> ResponsePostAudit:
    sentence_count = _count_sentences(assistant_response)
    question_count = assistant_response.count("?") + assistant_response.count("？")
    includes_validation = _contains_any(
        assistant_response,
        english_tokens=["i've got your message", "i hear you", "i understand"],
        chinese_tokens=["我已经收到你的输入", "我听到", "我理解"],
    )
    includes_next_step = _contains_any(
        assistant_response,
        english_tokens=["next step", "we can start", "keep us moving"],
        chinese_tokens=["下一步", "接下来", "可以先", "继续推进"],
    )
    includes_boundary_statement = _contains_any(
        assistant_response,
        english_tokens=[
            "not your only support",
            "collaborative",
            "instead of treating me as your only support",
        ],
        chinese_tokens=["不是唯一", "协作式", "不把我说成你唯一能依赖的对象"],
    )
    includes_uncertainty_statement = _contains_any(
        assistant_response,
        english_tokens=[
            "can't guarantee",
            "uncertain",
            "not certain",
            "can't know for sure",
        ],
        chinese_tokens=["不能保证", "不确定", "不能确定", "无法保证"],
    )

    violations: list[str] = []
    if sentence_count > response_rendering_policy.max_sentences:
        violations.append("sentence_budget_exceeded")
    if question_count > response_rendering_policy.question_count_limit:
        violations.append("question_budget_exceeded")
    if (
        response_rendering_policy.include_validation
        and not includes_validation
    ):
        violations.append("missing_validation")
    if (
        response_rendering_policy.include_next_step
        and not includes_next_step
    ):
        violations.append("missing_next_step")
    if (
        response_rendering_policy.include_boundary_statement
        and not includes_boundary_statement
    ):
        violations.append("missing_boundary_statement")
    if (
        response_rendering_policy.include_uncertainty_statement
        and not includes_uncertainty_statement
    ):
        violations.append("missing_uncertainty_statement")
    if "false_certainty" in response_draft_plan.must_avoid and (
        _contains_forbidden_false_certainty_language(assistant_response)
    ):
        violations.append("forbidden_false_certainty_language")
    if any(
        item in response_draft_plan.must_avoid
        for item in ["exclusive_rescue_language", "dependency_reinforcement"]
    ) and _contains_forbidden_dependency_language(assistant_response):
        violations.append("forbidden_dependency_language")

    notes: list[str] = []
    if includes_validation:
        notes.append("validation_present")
    if includes_next_step:
        notes.append("next_step_present")
    if includes_boundary_statement:
        notes.append("boundary_statement_present")
    if includes_uncertainty_statement:
        notes.append("uncertainty_statement_present")

    critical_violations = {
        "sentence_budget_exceeded",
        "question_budget_exceeded",
        "missing_boundary_statement",
        "missing_uncertainty_statement",
        "forbidden_false_certainty_language",
        "forbidden_dependency_language",
    }
    if not violations:
        status = "pass"
    elif any(item in critical_violations for item in violations):
        status = "revise"
    else:
        status = "review"

    return ResponsePostAudit(
        status=status,
        sentence_count=sentence_count,
        question_count=question_count,
        includes_validation=includes_validation,
        includes_next_step=includes_next_step,
        includes_boundary_statement=includes_boundary_statement,
        includes_uncertainty_statement=includes_uncertainty_statement,
        violations=_compact(violations, limit=6),
        notes=_compact(notes, limit=4),
        approved=status == "pass",
    )


def _append_sentence(text: str, addition: str) -> str:
    base = text.strip()
    extra = addition.strip()
    if not extra:
        return base
    if not base:
        return extra
    separator = "" if _contains_chinese(base[-1]) else " "
    return f"{base}{separator}{extra}".strip()


def _prefix_sentence(text: str, prefix: str) -> str:
    base = text.strip()
    head = prefix.strip()
    if not base:
        return head
    return f"{head} {base}".strip()


def _limit_question_count(text: str, limit: int) -> str:
    if limit < 0:
        limit = 0
    remaining = limit
    chars: list[str] = []
    for char in text:
        if char in {"?", "？"}:
            if remaining > 0:
                chars.append(char)
                remaining -= 1
            else:
                chars.append("." if char == "?" else "。")
            continue
        chars.append(char)
    return "".join(chars).strip()


def _limit_sentence_budget(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    parts = re.findall(r"[^.!?。！？]+[.!?。！？]?", text)
    compact_parts = [part.strip() for part in parts if part.strip()]
    if len(compact_parts) <= limit:
        return text.strip()
    return " ".join(compact_parts[:limit]).strip()


def _split_response_sentences(text: str) -> list[str]:
    parts = re.findall(r"[^.!?。！？]+[.!?。！？]?", text)
    return [part.strip() for part in parts if part.strip()]


def _build_canonical_response(
    *,
    response_rendering_policy: ResponseRenderingPolicy,
) -> str:
    sentences: list[str] = []
    if response_rendering_policy.include_validation:
        sentences.append("I hear you, and I want to keep this grounded.")
    if response_rendering_policy.include_uncertainty_statement:
        sentences.append("I can't know for sure, so I won't overclaim.")
    if response_rendering_policy.include_boundary_statement:
        sentences.append(
            "I'll keep the support collaborative instead of treating me as your only support."
        )
    if response_rendering_policy.include_next_step:
        sentences.append("The next step is to take one small concrete action.")
    if response_rendering_policy.question_count_limit > 0:
        sentences.append("What is the single detail that matters most right now?")
    return " ".join(sentences[: response_rendering_policy.max_sentences]).strip()


def build_response_sequence_plan(
    *,
    assistant_response: str,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
) -> ResponseSequencePlan:
    sentence_count = _count_sentences(assistant_response)
    reasons: list[str] = []
    segment_labels = ["complete"]
    mode = "single_message"

    if sentence_count >= 2:
        if (
            response_draft_plan.question_strategy != "none"
            and response_rendering_policy.question_count_limit > 0
        ):
            mode = "two_part_sequence"
            reasons.append("question_then_progress")
            segment_labels = ["orientation", "question"]
        elif (
            knowledge_boundary_decision.decision == "support_with_boundary"
            and response_rendering_policy.include_boundary_statement
            and response_rendering_policy.include_next_step
        ):
            mode = "two_part_sequence"
            reasons.append("boundary_then_next_step")
            segment_labels = ["boundary", "next_step"]
        elif (
            knowledge_boundary_decision.decision == "answer_with_uncertainty"
            and response_rendering_policy.include_uncertainty_statement
            and response_rendering_policy.include_next_step
        ):
            mode = "two_part_sequence"
            reasons.append("uncertainty_then_next_step")
            segment_labels = ["uncertainty", "next_step"]
        elif (
            repair_assessment.severity == "high"
            and response_rendering_policy.include_next_step
        ):
            mode = "two_part_sequence"
            reasons.append("repair_then_progress")
            segment_labels = ["repair", "next_step"]

    unit_count = 2 if mode == "two_part_sequence" else 1
    return ResponseSequencePlan(
        mode=mode,
        unit_count=unit_count,
        reasons=_compact(reasons, limit=3),
        segment_labels=segment_labels,
    )


def build_response_output_units(
    *,
    assistant_response: str,
    response_sequence_plan: ResponseSequencePlan,
) -> list[dict[str, str]]:
    normalized = assistant_response.strip()
    if not normalized:
        return []

    sentences = _split_response_sentences(normalized)
    if response_sequence_plan.mode != "two_part_sequence" or len(sentences) < 2:
        label = response_sequence_plan.segment_labels[0]
        return [{"label": label, "content": normalized}]

    first_reason = response_sequence_plan.reasons[0] if response_sequence_plan.reasons else ""
    if first_reason == "question_then_progress":
        question_indexes = [
            index
            for index, sentence in enumerate(sentences)
            if "?" in sentence or "？" in sentence
        ]
        pivot = question_indexes[0] if question_indexes else len(sentences) - 1
        pivot = max(1, pivot)
        first = " ".join(sentences[:pivot]).strip()
        second = " ".join(sentences[pivot:]).strip()
    else:
        first = sentences[0].strip()
        second = " ".join(sentences[1:]).strip()

    units = [first, second]
    labels = list(response_sequence_plan.segment_labels[:2])
    while len(labels) < len(units):
        labels.append(f"part_{len(labels) + 1}")

    result: list[dict[str, str]] = []
    for index, content in enumerate(units):
        cleaned = content.strip()
        if not cleaned:
            continue
        result.append({"label": labels[index], "content": cleaned})

    if len(result) <= 1:
        label = response_sequence_plan.segment_labels[0]
        return [{"label": label, "content": normalized}]
    return result


def build_response_normalization_result(
    *,
    assistant_response: str,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
    response_post_audit: ResponsePostAudit,
) -> tuple[str, ResponseNormalizationResult, ResponsePostAudit]:
    normalized = assistant_response.strip()
    applied_repairs: list[str] = []
    is_chinese = _contains_chinese(normalized)

    if "forbidden_false_certainty_language" in response_post_audit.violations:
        replacements = [
            ("definitely", "likely"),
            ("guaranteed", "more likely"),
            ("guarantee", "promise"),
            ("certain", "fully sure"),
            ("一定会", "未必会"),
            ("绝对会", "不一定会"),
            ("保证会", "不能直接断言会"),
        ]
        for source, target in replacements:
            normalized = normalized.replace(source, target)
        applied_repairs.append("softened_false_certainty_language")

    if "forbidden_dependency_language" in response_post_audit.violations:
        replacements = [
            ("only one who can help", "someone who can support"),
            ("your only support", "part of your support system"),
            ("only support you need", "one source of support"),
            ("can't do without me", "should not depend on me alone"),
            ("只有我能帮你", "我可以支持你，但不是唯一支持来源"),
            ("只能靠我", "不该只靠我"),
            ("唯一依赖", "支持来源之一"),
        ]
        for source, target in replacements:
            normalized = normalized.replace(source, target)
        applied_repairs.append("softened_dependency_language")

    if "missing_validation" in response_post_audit.violations:
        prefix = (
            "我知道你现在的处境需要稳一点。"
            if is_chinese
            else "I hear you, and I want to keep this grounded."
        )
        normalized = _prefix_sentence(normalized, prefix)
        applied_repairs.append("added_validation")

    if "missing_uncertainty_statement" in response_post_audit.violations:
        sentence = (
            "我现在不能确定结果，所以不会把话说满。"
            if is_chinese
            else "I can't know for sure, so I won't overclaim."
        )
        normalized = _append_sentence(normalized, sentence)
        applied_repairs.append("added_uncertainty_statement")

    if "missing_boundary_statement" in response_post_audit.violations:
        sentence = (
            "我会保持支持是协作式的，不把我说成你唯一能依赖的对象。"
            if is_chinese
            else "I'll keep the support collaborative instead of treating me as your only support."
        )
        normalized = _append_sentence(normalized, sentence)
        applied_repairs.append("added_boundary_statement")

    if "missing_next_step" in response_post_audit.violations:
        sentence = (
            "下一步是先做一个小而明确的动作。"
            if is_chinese
            else "The next step is to take one small concrete action."
        )
        normalized = _append_sentence(normalized, sentence)
        applied_repairs.append("added_next_step")

    if "question_budget_exceeded" in response_post_audit.violations:
        normalized = _limit_question_count(
            normalized,
            response_rendering_policy.question_count_limit,
        )
        applied_repairs.append("trimmed_question_budget")

    if "sentence_budget_exceeded" in response_post_audit.violations:
        normalized = _limit_sentence_budget(
            normalized,
            response_rendering_policy.max_sentences,
        )
        applied_repairs.append("trimmed_sentence_budget")

    final_post_audit = build_response_post_audit(
        assistant_response=normalized,
        response_draft_plan=response_draft_plan,
        response_rendering_policy=response_rendering_policy,
    )

    if final_post_audit.status != "pass":
        canonical = _build_canonical_response(
            response_rendering_policy=response_rendering_policy,
        )
        if canonical and canonical != normalized:
            normalized = canonical
            applied_repairs.append("rebuilt_response_to_fit_policy")
            final_post_audit = build_response_post_audit(
                assistant_response=normalized,
                response_draft_plan=response_draft_plan,
                response_rendering_policy=response_rendering_policy,
            )

    result = ResponseNormalizationResult(
        changed=normalized != assistant_response.strip(),
        trigger_status=response_post_audit.status,
        final_status=final_post_audit.status,
        trigger_violations=list(response_post_audit.violations),
        applied_repairs=_compact(applied_repairs, limit=6),
        normalized_content=normalized,
        approved=final_post_audit.approved,
    )
    return normalized, result, final_post_audit
