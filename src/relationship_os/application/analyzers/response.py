"""Response drafting, rendering, post-audit, sequencing, and normalization."""

from __future__ import annotations

import re

from relationship_os.application.analyzers._utils import (
    _compact,
    _contains_any,
    _contains_chinese,
)
from relationship_os.application.policy_registry import get_default_compiled_policy_set
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


def _rendering_policy(
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> dict[str, object]:
    compiled = get_default_compiled_policy_set(
        runtime_profile=runtime_profile,
        archetype=archetype or "default",
    )
    return dict(compiled.rendering_policy) if compiled else {}


def _rendering_section(
    key: str,
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> dict[str, object]:
    return dict(
        _rendering_policy(
            runtime_profile=runtime_profile,
            archetype=archetype,
        ).get(key)
        or {}
    )


def _repair_replacements(
    kind: str,
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> list[tuple[str, str]]:
    replacements = dict(
        _rendering_section(
            "repair_replacements",
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
    )
    raw_pairs = list(replacements.get(kind) or [])
    compiled: list[tuple[str, str]] = []
    for pair in raw_pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            continue
        compiled.append((str(pair[0]), str(pair[1])))
    return compiled


def _response_rendering_section(
    key: str,
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> dict[str, object]:
    raw = (
        _rendering_section(
            "response_rendering",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ).get(key)
        or {}
    )
    return dict(raw) if isinstance(raw, dict) else {}


def _apply_rendering_override(
    state: dict[str, object],
    override: dict[str, object],
) -> None:
    if not override:
        return
    for field in (
        "rendering_mode",
        "max_sentences",
        "include_validation",
        "include_next_step",
        "include_boundary_statement",
        "include_uncertainty_statement",
        "question_count_limit",
    ):
        if field in override:
            state[field] = override[field]
    if "max_sentences_cap" in override:
        state["max_sentences"] = min(
            int(state.get("max_sentences", 4)),
            int(override["max_sentences_cap"]),
        )
    if "question_count_limit_cap" in override:
        state["question_count_limit"] = min(
            int(state.get("question_count_limit", 0)),
            int(override["question_count_limit_cap"]),
        )
    style_guardrails = state.setdefault("style_guardrails", [])
    style_guardrails.extend(str(item) for item in override.get("style_guardrails", []) or [])


def _rendering_template(
    key: str,
    *,
    is_chinese: bool,
    default_en: str,
    default_zh: str,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> str:
    template = dict(
        _rendering_section(
            "canonical_response",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ).get(key)
        or {}
    )
    if is_chinese:
        return str(template.get("zh") or default_zh)
    return str(template.get("en") or default_en)


def _is_friend_chat_runtime(runtime_profile: str | None) -> bool:
    return str(runtime_profile or "").strip() == "friend_chat_zh_v1"


def _post_audit_presence_tokens(
    kind: str,
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> tuple[list[str], list[str]]:
    section = dict(
        _rendering_section(
            "post_audit",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ).get("presence_tokens")
        or {}
    )
    bucket = dict(section.get(kind) or {})
    english = [str(item) for item in bucket.get("en", []) or []]
    chinese = [str(item) for item in bucket.get("zh", []) or []]
    return english, chinese


def _critical_post_audit_violations(
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> set[str]:
    section = dict(
        _rendering_section(
            "post_audit",
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
    )
    configured = [str(item) for item in section.get("critical_violations", []) or []]
    if configured:
        return set(configured)
    return {
        "sentence_budget_exceeded",
        "question_budget_exceeded",
        "missing_boundary_statement",
        "missing_uncertainty_statement",
        "forbidden_false_certainty_language",
        "forbidden_dependency_language",
    }


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
    state = _build_response_draft_state(expression_plan=expression_plan)
    _apply_repair_and_runtime_draft_rules(
        state,
        repair_plan=repair_plan,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
    )
    _apply_guidance_and_cadence_draft_rules(
        state,
        guidance_plan=guidance_plan,
        cadence_plan=cadence_plan,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
    )
    _apply_boundary_and_policy_draft_rules(
        state,
        knowledge_boundary_decision=knowledge_boundary_decision,
        expression_plan=expression_plan,
        policy_gate=policy_gate,
    )
    _apply_confidence_and_audit_draft_rules(
        state,
        confidence_assessment=confidence_assessment,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
    )
    return _materialize_response_draft_plan(
        state,
        empowerment_audit=empowerment_audit,
    )


def _build_response_draft_state(
    *,
    expression_plan: ExpressionPlan,
) -> dict[str, object]:
    return {
        "opening_move": "acknowledge_and_orient",
        "structure": ["name the current context", "offer one concrete next step"],
        "must_include": list(expression_plan.goals),
        "must_avoid": list(expression_plan.avoid),
        "phrasing_constraints": [],
        "question_strategy": "none",
    }


def _apply_repair_and_runtime_draft_rules(
    state: dict[str, object],
    *,
    repair_plan: RepairPlan,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
) -> None:
    structure = state["structure"]
    phrasing_constraints = state["phrasing_constraints"]
    if repair_plan.rupture_detected:
        state["opening_move"] = "repair_then_orient"
        state["structure"] = [
            "briefly acknowledge the user's current state",
            "repair understanding",
            "offer one concrete next step",
        ]
        structure = state["structure"]

    if runtime_coordination_snapshot.ritual_phase == "opening_ritual":
        structure.insert(0, "set a simple session frame")
    elif runtime_coordination_snapshot.ritual_phase == "re_anchor":
        structure.insert(0, "briefly re-anchor shared context")

    if runtime_coordination_snapshot.cognitive_load_band == "high":
        state["opening_move"] = "stabilize_then_orient"
        phrasing_constraints.append(
            "keep processing load low with shorter and more concrete sentences"
        )


def _apply_guidance_and_cadence_draft_rules(
    state: dict[str, object],
    *,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
) -> None:
    structure = state["structure"]
    must_include = state["must_include"]
    phrasing_constraints = state["phrasing_constraints"]

    if guidance_plan.lead_with == "regulate_first":
        state["opening_move"] = "stabilize_then_orient"
    elif guidance_plan.lead_with == "attunement_repair":
        state["opening_move"] = "repair_then_orient"
    elif guidance_plan.lead_with == "clarify_gap":
        state["opening_move"] = "clarify_with_reason"
    elif guidance_plan.lead_with == "boundary_frame":
        state["opening_move"] = "bound_the_answer"
    elif guidance_plan.lead_with == "shared_context_reanchor":
        structure.insert(0, "briefly re-anchor shared context")
    elif guidance_plan.lead_with == "micro_commitment":
        structure.insert(0, "guide one small next step")
    elif guidance_plan.lead_with == "reflect_then_step":
        structure.insert(0, "briefly reflect the user's state")

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
        phrasing_constraints.append("leave deliberate conversational space after the checkpoint")
    if guidance_plan.agency_mode == "focused_question":
        state["question_strategy"] = "single_focused_question"
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
        state["question_strategy"] = "single_focused_question"


def _apply_boundary_and_policy_draft_rules(
    state: dict[str, object],
    *,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    expression_plan: ExpressionPlan,
    policy_gate: PolicyGateDecision,
) -> None:
    must_include = state["must_include"]
    must_avoid = state["must_avoid"]
    phrasing_constraints = state["phrasing_constraints"]

    if knowledge_boundary_decision.decision == "answer_with_uncertainty":
        state["opening_move"] = "bound_the_answer"
        must_include.extend(
            [
                "state limits explicitly",
                "pair uncertainty with a bounded next step",
            ]
        )
        must_avoid.append("false_certainty")
        phrasing_constraints.append("use calibrated language instead of guarantees or predictions")
    elif knowledge_boundary_decision.decision == "clarify_before_answer":
        state["opening_move"] = "clarify_with_reason"
        state["question_strategy"] = "single_focused_question"
        must_include.extend(
            [
                "explain why the clarifying question helps",
                "ask only one focused question",
            ]
        )
        must_avoid.append("multi_question_barrage")
        phrasing_constraints.append("keep the clarifying question concrete and short")
    elif expression_plan.include_question:
        state["question_strategy"] = "check_alignment"

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


def _apply_confidence_and_audit_draft_rules(
    state: dict[str, object],
    *,
    confidence_assessment: ConfidenceAssessment,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
) -> None:
    structure = state["structure"]
    must_include = state["must_include"]
    phrasing_constraints = state["phrasing_constraints"]

    if confidence_assessment.response_mode == "repair_first":
        structure.insert(0, "slow the tempo before giving direction")
    if rehearsal_result.projected_risk_level == "high":
        phrasing_constraints.extend(rehearsal_result.recommended_adjustments[:2])
    if empowerment_audit.transparency_required:
        must_include.append("make uncertainty or limits visible")
    if empowerment_audit.status == "revise":
        state["opening_move"] = "slow_down_and_reframe"
        phrasing_constraints.extend(empowerment_audit.recommended_adjustments[:2])


def _materialize_response_draft_plan(
    state: dict[str, object],
    *,
    empowerment_audit: EmpowermentAudit,
) -> ResponseDraftPlan:
    return ResponseDraftPlan(
        opening_move=str(state["opening_move"]),
        structure=_compact(state["structure"], limit=4),
        must_include=_compact(state["must_include"], limit=5),
        must_avoid=_compact(state["must_avoid"], limit=5),
        phrasing_constraints=_compact(state["phrasing_constraints"], limit=5),
        question_strategy=str(state["question_strategy"]),
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
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> ResponseRenderingPolicy:
    defaults = _response_rendering_section(
        "defaults",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    state: dict[str, object] = {
        "rendering_mode": str(defaults.get("rendering_mode", "supportive_progress")),
        "max_sentences": int(defaults.get("max_sentences", 4)),
        "include_validation": (
            context_frame.appraisal == "negative"
            if defaults.get("include_validation_on_negative_appraisal", True)
            else False
        ),
        "include_next_step": (
            context_frame.appraisal == "negative"
            if defaults.get("include_next_step_on_negative_appraisal", True)
            else False
        ),
        "include_boundary_statement": False,
        "include_uncertainty_statement": (
            knowledge_boundary_decision.should_disclose_uncertainty
            if defaults.get("include_uncertainty_from_boundary_decision", True)
            else False
        ),
        "question_count_limit": int(defaults.get("question_count_limit", 0)),
        "style_guardrails": list(response_draft_plan.phrasing_constraints),
    }

    if repair_assessment.repair_needed:
        _apply_rendering_override(
            state,
            _response_rendering_section(
                "repair_needed",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ),
        )
    if confidence_assessment.response_mode == "clarify":
        _apply_rendering_override(
            state,
            _response_rendering_section(
                "clarify",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ),
        )
    elif confidence_assessment.response_mode == "calibrated":
        _apply_rendering_override(
            state,
            _response_rendering_section(
                "calibrated",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ),
        )
    elif knowledge_boundary_decision.decision == "support_with_boundary":
        _apply_rendering_override(
            state,
            _response_rendering_section(
                "support_with_boundary",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ),
        )
    elif empowerment_audit.status == "revise":
        _apply_rendering_override(
            state,
            _response_rendering_section(
                "empowerment_revise",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ),
        )

    strategy_limits = _response_rendering_section(
        "question_strategy_limits",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    if response_draft_plan.question_strategy == "single_focused_question":
        state["question_count_limit"] = int(strategy_limits.get("single_focused_question", 1))
    elif response_draft_plan.question_strategy == "check_alignment":
        state["question_count_limit"] = max(
            int(state.get("question_count_limit", 0)),
            int(strategy_limits.get("check_alignment_min", 1)),
        )

    cognitive_load = dict(
        _response_rendering_section(
            "cognitive_load",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ).get(
            runtime_coordination_snapshot.cognitive_load_band,
            {},
        )
        or {}
    )
    if runtime_coordination_snapshot.cognitive_load_band == "high":
        _apply_rendering_override(state, cognitive_load)
        skip_modes = {
            str(item)
            for item in cognitive_load.get("skip_question_cap_for_response_modes", []) or []
        }
        if confidence_assessment.response_mode in skip_modes:
            pass
        elif "question_count_limit_cap" in cognitive_load:
            state["question_count_limit"] = min(
                int(state.get("question_count_limit", 0)),
                int(cognitive_load["question_count_limit_cap"]),
            )
    elif runtime_coordination_snapshot.cognitive_load_band == "medium":
        _apply_rendering_override(state, cognitive_load)

    time_awareness = dict(
        _response_rendering_section(
            "time_awareness_modes",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ).get(
            runtime_coordination_snapshot.time_awareness_mode,
            {},
        )
        or {}
    )
    if runtime_coordination_snapshot.time_awareness_mode in {"reengagement", "resume"}:
        _apply_rendering_override(state, time_awareness)

    if runtime_coordination_snapshot.proactive_followup_eligible:
        proactive_guardrail = str(
            _rendering_section(
                "response_rendering",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ).get(
                "proactive_followup_style_guardrail",
                "leave room for a light future follow-up instead of over-explaining now",
            )
        ).strip()
        if proactive_guardrail:
            state["style_guardrails"].append(proactive_guardrail)

    if knowledge_boundary_decision.decision == "support_with_boundary":
        state["include_boundary_statement"] = True
    if not response_draft_plan.approved or not empowerment_audit.approved:
        _apply_rendering_override(
            state,
            _response_rendering_section(
                "not_approved",
                runtime_profile=runtime_profile,
                archetype=archetype,
            ),
        )

    return ResponseRenderingPolicy(
        rendering_mode=str(state["rendering_mode"]),
        max_sentences=int(state["max_sentences"]),
        include_validation=bool(state["include_validation"]),
        include_next_step=bool(state["include_next_step"]),
        include_boundary_statement=bool(state["include_boundary_statement"]),
        include_uncertainty_statement=bool(state["include_uncertainty_statement"]),
        question_count_limit=int(state["question_count_limit"]),
        style_guardrails=_compact(state["style_guardrails"], limit=5),
        approved=response_draft_plan.approved and empowerment_audit.approved,
    )


def _count_sentences(text: str) -> int:
    parts = [part.strip() for part in re.split(r"[.!?。！？]+", text) if part.strip()]
    return len(parts)


def _contains_forbidden_false_certainty_language(
    text: str,
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> bool:
    lowered = text.lower()
    policy = _rendering_section(
        "forbidden_false_certainty",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    english_patterns = list(
        policy.get("en")
        or [
            "definitely will",
            "will definitely",
            "guaranteed to",
            "absolutely will",
        ]
    )
    chinese_patterns = list(
        policy.get("zh") or ["一定会", "绝对会", "肯定会", "保证会", "百分之百会"]
    )
    safe_english_patterns = list(
        policy.get("safe_en") or ["can't know for sure", "cannot know for sure", "not for sure"]
    )
    if any(pattern in lowered for pattern in english_patterns):
        return True
    if "for sure" in lowered and not any(
        safe_phrase in lowered for safe_phrase in safe_english_patterns
    ):
        return True
    return any(pattern in text for pattern in chinese_patterns)


def _contains_forbidden_dependency_language(
    text: str,
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> bool:
    lowered = text.lower()
    policy = _rendering_section(
        "forbidden_dependency",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    english_patterns = list(
        policy.get("en")
        or [
            "only one who can help",
            "your only support",
            "only support you need",
            "can't do without me",
        ]
    )
    chinese_patterns = list(
        policy.get("zh") or ["只有我能帮你", "只能靠我", "我是你唯一", "唯一依赖"]
    )
    return any(pattern in lowered for pattern in english_patterns) or any(
        pattern in text for pattern in chinese_patterns
    )


def build_response_post_audit(
    *,
    assistant_response: str,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> ResponsePostAudit:
    sentence_count = _count_sentences(assistant_response)
    question_count = assistant_response.count("?") + assistant_response.count("？")
    validation_en, validation_zh = _post_audit_presence_tokens(
        "validation",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    includes_validation = _contains_any(
        assistant_response,
        english_tokens=validation_en or ["i've got your message", "i hear you", "i understand"],
        chinese_tokens=validation_zh or ["我已经收到你的输入", "我听到", "我理解"],
    )
    next_step_en, next_step_zh = _post_audit_presence_tokens(
        "next_step",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    includes_next_step = _contains_any(
        assistant_response,
        english_tokens=next_step_en or ["next step", "we can start", "keep us moving"],
        chinese_tokens=next_step_zh or ["下一步", "接下来", "可以先", "继续推进"],
    )
    boundary_en, boundary_zh = _post_audit_presence_tokens(
        "boundary_statement",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    includes_boundary_statement = _contains_any(
        assistant_response,
        english_tokens=boundary_en
        or [
            "not your only support",
            "collaborative",
            "instead of treating me as your only support",
        ],
        chinese_tokens=boundary_zh or ["不是唯一", "协作式", "不把我说成你唯一能依赖的对象"],
    )
    uncertainty_en, uncertainty_zh = _post_audit_presence_tokens(
        "uncertainty_statement",
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
    includes_uncertainty_statement = _contains_any(
        assistant_response,
        english_tokens=uncertainty_en
        or [
            "can't guarantee",
            "uncertain",
            "not certain",
            "can't know for sure",
        ],
        chinese_tokens=uncertainty_zh or ["不能保证", "不确定", "不能确定", "无法保证"],
    )

    violations: list[str] = []
    if sentence_count > response_rendering_policy.max_sentences:
        violations.append("sentence_budget_exceeded")
    if question_count > response_rendering_policy.question_count_limit:
        violations.append("question_budget_exceeded")
    if response_rendering_policy.include_validation and not includes_validation:
        violations.append("missing_validation")
    if response_rendering_policy.include_next_step and not includes_next_step:
        violations.append("missing_next_step")
    if response_rendering_policy.include_boundary_statement and not includes_boundary_statement:
        violations.append("missing_boundary_statement")
    if (
        response_rendering_policy.include_uncertainty_statement
        and not includes_uncertainty_statement
    ):
        violations.append("missing_uncertainty_statement")
    if "false_certainty" in response_draft_plan.must_avoid and (
        _contains_forbidden_false_certainty_language(
            assistant_response,
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
    ):
        violations.append("forbidden_false_certainty_language")
    if any(
        item in response_draft_plan.must_avoid
        for item in ["exclusive_rescue_language", "dependency_reinforcement"]
    ) and _contains_forbidden_dependency_language(
        assistant_response,
        runtime_profile=runtime_profile,
        archetype=archetype,
    ):
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

    critical_violations = _critical_post_audit_violations(
        runtime_profile=runtime_profile,
        archetype=archetype,
    )
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


def _friend_chat_sentence_priority(
    sentence: str,
    *,
    must_keep_question: bool,
) -> tuple[int, int, int]:
    has_question = 1 if ("?" in sentence or "？" in sentence) else 0
    has_colloquial_tone = (
        1
        if _contains_any(
            sentence,
            english_tokens=["yeah", "okay", "right", "kind of"],
            chinese_tokens=["嗯", "就", "吧", "啊", "呢", "慢慢", "先"],
        )
        else 0
    )
    looks_explanatory = (
        1
        if _contains_any(
            sentence,
            english_tokens=["first", "next step", "to summarize", "in short"],
            chinese_tokens=["首先", "下一步", "总结一下", "也就是说"],
        )
        else 0
    )
    question_bonus = 2 if must_keep_question and has_question else has_question
    return (question_bonus, has_colloquial_tone, -looks_explanatory)


def _extract_friend_chat_policy_safe_subset(
    text: str,
    *,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> str:
    sentences = _split_response_sentences(text)
    if not sentences:
        return text.strip()

    filtered: list[str] = []
    allow_false_certainty = "false_certainty" not in response_draft_plan.must_avoid
    allow_dependency = not any(
        item in response_draft_plan.must_avoid
        for item in ["exclusive_rescue_language", "dependency_reinforcement"]
    )
    for sentence in sentences:
        if not allow_false_certainty and _contains_forbidden_false_certainty_language(
            sentence,
            runtime_profile=runtime_profile,
            archetype=archetype,
        ):
            continue
        if not allow_dependency and _contains_forbidden_dependency_language(
            sentence,
            runtime_profile=runtime_profile,
            archetype=archetype,
        ):
            continue
        filtered.append(sentence)

    if not filtered:
        filtered = [sentences[0]]

    must_keep_question = response_rendering_policy.question_count_limit > 0
    ranked = sorted(
        enumerate(filtered),
        key=lambda item: (
            _friend_chat_sentence_priority(
                item[1],
                must_keep_question=must_keep_question,
            ),
            -item[0],
        ),
        reverse=True,
    )
    selected_indexes = sorted(
        index for index, _ in ranked[: response_rendering_policy.max_sentences]
    )
    selected = [filtered[index] for index in selected_indexes]
    compact = " ".join(selected).strip()
    compact = _limit_question_count(
        compact,
        response_rendering_policy.question_count_limit,
    )
    compact = _limit_sentence_budget(
        compact,
        response_rendering_policy.max_sentences,
    )
    return compact.strip() or text.strip()


def _build_canonical_response(
    *,
    response_rendering_policy: ResponseRenderingPolicy,
    is_chinese: bool = False,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> str:
    sentences: list[str] = []
    if response_rendering_policy.include_validation:
        sentences.append(
            _rendering_template(
                "validation",
                is_chinese=is_chinese,
                default_en="I hear you.",
                default_zh="我在听。",
                runtime_profile=runtime_profile,
                archetype=archetype,
            )
        )
    if response_rendering_policy.include_uncertainty_statement:
        sentences.append(
            _rendering_template(
                "uncertainty",
                is_chinese=is_chinese,
                default_en="I won't overclaim.",
                default_zh="有些事我不说满。",
                runtime_profile=runtime_profile,
                archetype=archetype,
            )
        )
    if response_rendering_policy.include_boundary_statement:
        sentences.append(
            _rendering_template(
                "boundary",
                is_chinese=is_chinese,
                default_en="I'm not your only support.",
                default_zh="我不是你唯一的支点。",
                runtime_profile=runtime_profile,
                archetype=archetype,
            )
        )
    if response_rendering_policy.include_next_step:
        sentences.append(
            _rendering_template(
                "next_step",
                is_chinese=is_chinese,
                default_en="Which part first?",
                default_zh="先说哪一块？",
                runtime_profile=runtime_profile,
                archetype=archetype,
            )
        )
    if response_rendering_policy.question_count_limit > 0 and not sentences:
        sentences.append(
            _rendering_template(
                "question_only",
                is_chinese=is_chinese,
                default_en="What matters most right now?",
                default_zh="现在最在意哪一块？",
                runtime_profile=runtime_profile,
                archetype=archetype,
            )
        )
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
        elif repair_assessment.severity == "high" and response_rendering_policy.include_next_step:
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
            index for index, sentence in enumerate(sentences) if "?" in sentence or "？" in sentence
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
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> tuple[str, ResponseNormalizationResult, ResponsePostAudit]:
    normalized = assistant_response.strip()
    applied_repairs: list[str] = []
    is_chinese = _contains_chinese(normalized)
    friend_chat_runtime = _is_friend_chat_runtime(runtime_profile)

    if (
        "forbidden_false_certainty_language" in response_post_audit.violations
        and not friend_chat_runtime
    ):
        replacements = _repair_replacements(
            "false_certainty",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ) or [
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

    if (
        "forbidden_dependency_language" in response_post_audit.violations
        and not friend_chat_runtime
    ):
        replacements = _repair_replacements(
            "dependency",
            runtime_profile=runtime_profile,
            archetype=archetype,
        ) or [
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

    if "missing_validation" in response_post_audit.violations and not friend_chat_runtime:
        prefix = _rendering_template(
            "validation",
            is_chinese=is_chinese,
            default_en="I hear you.",
            default_zh="我在听。",
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
        normalized = _prefix_sentence(normalized, prefix)
        applied_repairs.append("added_validation")

    if (
        "missing_uncertainty_statement" in response_post_audit.violations
        and not friend_chat_runtime
    ):
        sentence = _rendering_template(
            "uncertainty",
            is_chinese=is_chinese,
            default_en="I won't overclaim.",
            default_zh="有些事我不说满。",
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
        normalized = _append_sentence(normalized, sentence)
        applied_repairs.append("added_uncertainty_statement")

    if "missing_boundary_statement" in response_post_audit.violations and not friend_chat_runtime:
        sentence = _rendering_template(
            "boundary",
            is_chinese=is_chinese,
            default_en="I'm not your only support.",
            default_zh="我不是你唯一的支点。",
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
        normalized = _append_sentence(normalized, sentence)
        applied_repairs.append("added_boundary_statement")

    if "missing_next_step" in response_post_audit.violations and not friend_chat_runtime:
        sentence = _rendering_template(
            "next_step",
            is_chinese=is_chinese,
            default_en="Which part first?",
            default_zh="先说哪一块？",
            runtime_profile=runtime_profile,
            archetype=archetype,
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
        runtime_profile=runtime_profile,
        archetype=archetype,
    )

    if friend_chat_runtime and final_post_audit.status != "pass":
        extracted = _extract_friend_chat_policy_safe_subset(
            normalized,
            response_draft_plan=response_draft_plan,
            response_rendering_policy=response_rendering_policy,
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
        if extracted and extracted != normalized:
            normalized = extracted
            applied_repairs.append("extracted_friend_chat_policy_safe_subset")
            final_post_audit = build_response_post_audit(
                assistant_response=normalized,
                response_draft_plan=response_draft_plan,
                response_rendering_policy=response_rendering_policy,
                runtime_profile=runtime_profile,
                archetype=archetype,
            )

    if final_post_audit.status != "pass":
        remaining = [v for v in final_post_audit.violations if v.startswith("forbidden_")]
        if remaining and not friend_chat_runtime:
            canonical = _build_canonical_response(
                response_rendering_policy=response_rendering_policy,
                is_chinese=is_chinese,
                runtime_profile=runtime_profile,
                archetype=archetype,
            )
            if canonical and canonical != normalized:
                normalized = canonical
                applied_repairs.append("rebuilt_response_to_fit_policy")
                final_post_audit = build_response_post_audit(
                    assistant_response=normalized,
                    response_draft_plan=response_draft_plan,
                    response_rendering_policy=response_rendering_policy,
                    runtime_profile=runtime_profile,
                    archetype=archetype,
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
