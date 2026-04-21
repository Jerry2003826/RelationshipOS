"""System 3 meta-runtime: governance snapshot and quality doctor."""

from __future__ import annotations

import re

from relationship_os.application.analyzers._governance_phase2 import (
    _System3Prelude,
    build_system3_phase2_snapshot,
)
from relationship_os.application.analyzers._utils import (
    _clamp,
    _compact,
    _contains_any,
    _contains_chinese,
    _contains_forbidden_dependency_language,
    _contains_forbidden_false_certainty_language,
    _has_mixed_language,
)
from relationship_os.application.policy_registry import get_default_compiled_policy_set
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    EmpowermentAudit,
    KnowledgeBoundaryDecision,
    MemoryBundle,
    PolicyGateDecision,
    RehearsalResult,
    RelationshipState,
    RepairAssessment,
    ResponseNormalizationResult,
    ResponsePostAudit,
    ResponseSequencePlan,
    RuntimeQualityDoctorReport,
    StrategyDecision,
    System3Snapshot,
)

_PROACTIVE_GOVERNANCE_DOMAINS = (
    "safety",
    "autonomy",
    "boundary",
    "support",
    "clarity",
    "pacing",
    "attunement",
    "commitment",
    "disclosure",
    "reciprocity",
    "progress",
    "stability",
    "pressure",
    "trust",
    "continuity",
    "repair",
    "relational",
)


def _governance_policy() -> dict[str, object]:
    compiled = get_default_compiled_policy_set()
    if compiled is None:
        return {}
    return dict(compiled.conscience_policy.get("governance") or {})


def _governance_section(key: str) -> dict[str, object]:
    raw = _governance_policy().get(key) or {}
    return dict(raw) if isinstance(raw, dict) else {}


def build_runtime_quality_doctor_report(
    *,
    transcript_messages: list[dict[str, str]],
    user_message: str,
    assistant_responses: list[str],
    triggered_turn_index: int,
    window_turns: int,
) -> RuntimeQualityDoctorReport:
    doctor_policy = _governance_section("runtime_quality_doctor")
    recent_messages = list(transcript_messages)
    recent_messages.append({"role": "user", "content": user_message})
    recent_messages.extend(
        {"role": "assistant", "content": content}
        for content in assistant_responses
        if content.strip()
    )
    max_window_messages = max(
        int(doctor_policy.get("min_window_messages", 2)),
        window_turns * int(doctor_policy.get("window_messages_per_turn", 3)),
    )
    window_messages = recent_messages[-max_window_messages:]
    assistant_window = [
        str(message.get("content", "")).strip()
        for message in window_messages
        if message.get("role") == "assistant" and str(message.get("content", "")).strip()
    ]

    issues: list[str] = []
    recommended_repairs: list[str] = []
    notes: list[str] = []

    mixed_language_count = sum(
        1 for message in window_messages if _has_mixed_language(str(message.get("content", "")))
    )
    if mixed_language_count > 0:
        issues.append("language_mixing")
        recommended_repairs.append("keep one response segment in one primary language")

    opening_counts: dict[str, int] = {}
    signature_token_count = int(doctor_policy.get("opening_signature_token_count", 3))
    for content in assistant_window:
        tokens = re.findall(r"\b\w+\b", content.lower())
        signature = " ".join(tokens[:signature_token_count]).strip()
        if signature:
            opening_counts[signature] = opening_counts.get(signature, 0) + 1
    repeated_opening_count = sum(count for count in opening_counts.values() if count > 1)
    if repeated_opening_count >= int(doctor_policy.get("repetitive_openings_threshold", 2)):
        issues.append("repetitive_openings")
        recommended_repairs.append("vary openings and sentence framing across turns")

    adjacent_duplicate_count = 0
    for previous, current in zip(assistant_window, assistant_window[1:], strict=False):
        if previous.strip().lower() == current.strip().lower():
            adjacent_duplicate_count += 1
    if adjacent_duplicate_count > 0:
        issues.append("duplicate_response_segments")
        recommended_repairs.append("deduplicate adjacent assistant segments")

    format_noise_count = sum(
        1
        for content in assistant_window
        if "\n\n" in content
        or "  " in content
        or content.count("...") >= int(doctor_policy.get("format_noise_ellipsis_threshold", 2))
    )
    if format_noise_count > 0:
        issues.append("format_noise")
        recommended_repairs.append("normalize spacing and reduce filler punctuation")

    contradiction_count = 0
    certainty_conflict = any(
        _contains_forbidden_false_certainty_language(content) for content in assistant_window
    ) and any(
        _contains_any(
            content,
            english_tokens=["can't know for sure", "cannot know for sure", "uncertain"],
            chinese_tokens=["不能确定", "不确定", "不能保证"],
        )
        for content in assistant_window
    )
    if certainty_conflict:
        contradiction_count += 1
    boundary_conflict = any(
        _contains_forbidden_dependency_language(content) for content in assistant_window
    ) and any(
        _contains_any(
            content,
            english_tokens=["collaborative", "not your only support"],
            chinese_tokens=["协作式", "不是唯一"],
        )
        for content in assistant_window
    )
    if boundary_conflict:
        contradiction_count += 1
    if contradiction_count > 0:
        issues.append("logic_contradiction")
        recommended_repairs.append(
            "align boundary, certainty, and support claims across the window"
        )

    notes.extend(
        [
            f"assistant_segments={len(assistant_window)}",
            f"mixed_language_count={mixed_language_count}",
            f"repeated_opening_count={repeated_opening_count}",
            f"adjacent_duplicate_count={adjacent_duplicate_count}",
            f"contradiction_count={contradiction_count}",
        ]
    )

    if "logic_contradiction" in issues or len(issues) >= int(
        doctor_policy.get("revise_issue_count_threshold", 3)
    ):
        status = "revise"
    elif issues:
        status = "watch"
    else:
        status = "pass"

    return RuntimeQualityDoctorReport(
        status=status,
        triggered_turn_index=triggered_turn_index,
        window_turn_count=min(window_turns, triggered_turn_index),
        issue_count=len(issues),
        issues=_compact(issues, limit=6),
        recommended_repairs=_compact(recommended_repairs, limit=6),
        notes=_compact(notes, limit=6),
    )


def _build_identity_prelude(
    *,
    context_frame: ContextFrame,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    confidence_assessment: ConfidenceAssessment,
    response_post_audit: ResponsePostAudit | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
    empowerment_audit: EmpowermentAudit,
    response_normalization: ResponseNormalizationResult | None,
) -> dict[str, object]:
    identity_policy = _governance_section("identity")
    topic_anchors = dict(identity_policy.get("topic_identity_anchors") or {})
    if knowledge_boundary_decision.decision == "support_with_boundary":
        identity_anchor = str(
            identity_policy.get(
                "boundary_support_anchor",
                "collaborative_boundaried_support",
            )
        )
    elif context_frame.topic in topic_anchors:
        identity_anchor = str(topic_anchors[context_frame.topic])
    elif context_frame.bid_signal == "connection_request":
        identity_anchor = str(
            identity_policy.get("connection_request_anchor", "relational_support_partner")
        )
    else:
        identity_anchor = str(
            identity_policy.get(
                "default_anchor",
                "collaborative_reflective_support",
            )
        )

    identity_consistency = "stable"
    if (
        (response_post_audit and response_post_audit.status == "revise")
        or (runtime_quality_doctor_report and runtime_quality_doctor_report.status == "revise")
        or empowerment_audit.status == "revise"
    ):
        identity_consistency = "drift"
    elif (
        (response_post_audit and response_post_audit.status == "review")
        or (runtime_quality_doctor_report and runtime_quality_doctor_report.status == "watch")
        or (response_normalization and response_normalization.changed)
    ):
        identity_consistency = "watch"

    identity_confidence = _clamp(
        confidence_assessment.score
        + (
            float(identity_policy.get("stable_bonus", 0.08))
            if identity_consistency == "stable"
            else 0.0
        )
        - (
            float(identity_policy.get("watch_penalty", 0.08))
            if identity_consistency == "watch"
            else float(identity_policy.get("drift_penalty", 0.18))
            if identity_consistency == "drift"
            else 0.0
        )
    )

    identity_trajectory_target = identity_anchor
    identity_trajectory_notes: list[str] = []
    if identity_consistency == "drift":
        identity_trajectory_status = "recenter"
        if response_post_audit and response_post_audit.status == "revise":
            identity_trajectory_trigger = "response_post_audit_drift"
            identity_trajectory_notes.append("post_audit_revision_forced_identity_recenter")
        elif runtime_quality_doctor_report and runtime_quality_doctor_report.status == "revise":
            identity_trajectory_trigger = "runtime_quality_doctor_drift"
            identity_trajectory_notes.append("quality_doctor_revise_flagged_identity_slip")
        elif empowerment_audit.status == "revise":
            identity_trajectory_trigger = "empowerment_revision_drift"
            identity_trajectory_notes.append("empowerment_risk_requires_identity_recenter")
        else:
            identity_trajectory_trigger = "identity_confidence_drop"
            identity_trajectory_notes.append("identity_confidence_dropped_below_stable_band")
    elif identity_consistency == "watch":
        identity_trajectory_status = "watch"
        if response_normalization is not None and response_normalization.changed:
            identity_trajectory_trigger = "response_normalization_adjustment"
            identity_trajectory_notes.append("normalization_adjusted_identity_presentation")
        elif runtime_quality_doctor_report and runtime_quality_doctor_report.status == "watch":
            identity_trajectory_trigger = "runtime_quality_doctor_watch"
            identity_trajectory_notes.append("quality_doctor_watch_requires_identity_attention")
        else:
            identity_trajectory_trigger = "identity_soft_drift"
            identity_trajectory_notes.append("identity_signals_show_soft_drift")
    else:
        identity_trajectory_status = "stable"
        identity_trajectory_trigger = "identity_consistent"
        if identity_confidence >= float(identity_policy.get("stable_confidence_threshold", 0.72)):
            identity_trajectory_notes.append("identity_anchor_holding_steady")

    return {
        "identity_anchor": identity_anchor,
        "identity_consistency": identity_consistency,
        "identity_confidence": identity_confidence,
        "identity_trajectory_status": identity_trajectory_status,
        "identity_trajectory_target": identity_trajectory_target,
        "identity_trajectory_trigger": identity_trajectory_trigger,
        "identity_trajectory_notes": identity_trajectory_notes,
    }


def _build_emotional_debt_prelude(
    *,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    response_post_audit: ResponsePostAudit | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
    response_normalization: ResponseNormalizationResult | None,
    empowerment_audit: EmpowermentAudit,
) -> dict[str, object]:
    debt_policy = _governance_section("emotional_debt")
    repair_weights = dict(debt_policy.get("repair_severity_weights") or {})
    post_audit_weights = dict(debt_policy.get("post_audit_weights") or {})
    quality_doctor_weights = dict(debt_policy.get("quality_doctor_weights") or {})
    status_thresholds = dict(debt_policy.get("status_thresholds") or {})
    emotional_debt_score = 0.0
    debt_signals: list[str] = []
    if repair_assessment.repair_needed:
        emotional_debt_score += float(
            repair_weights.get(
                repair_assessment.severity,
                repair_weights.get("default", 0.22),
            )
        )
        debt_signals.append(f"repair_{repair_assessment.severity}")
    if relationship_state.turbulence_risk == "elevated":
        emotional_debt_score += float(debt_policy.get("turbulence_pressure_weight", 0.14))
        debt_signals.append("turbulence_pressure")
    if relationship_state.dependency_risk == "elevated":
        emotional_debt_score += float(debt_policy.get("dependency_pressure_weight", 0.2))
        debt_signals.append("dependency_boundary_pressure")
    if response_post_audit is not None and response_post_audit.status in {"review", "revise"}:
        emotional_debt_score += float(
            post_audit_weights.get(
                response_post_audit.status,
                0.08 if response_post_audit.status == "review" else 0.18,
            )
        )
        debt_signals.append(f"post_audit_{response_post_audit.status}")
    if runtime_quality_doctor_report is not None and runtime_quality_doctor_report.status in {
        "watch",
        "revise",
    }:
        emotional_debt_score += float(
            quality_doctor_weights.get(
                runtime_quality_doctor_report.status,
                0.1 if runtime_quality_doctor_report.status == "watch" else 0.2,
            )
        )
        debt_signals.append(f"quality_doctor_{runtime_quality_doctor_report.status}")
    if response_normalization is not None and response_normalization.changed:
        emotional_debt_score += float(debt_policy.get("response_normalized_weight", 0.08))
        debt_signals.append("response_normalized")
    emotional_debt_score = round(min(emotional_debt_score, 1.0), 3)
    if emotional_debt_score >= float(status_thresholds.get("elevated", 0.56)):
        emotional_debt_status = "elevated"
    elif emotional_debt_score >= float(status_thresholds.get("watch", 0.24)):
        emotional_debt_status = "watch"
    else:
        emotional_debt_status = "low"

    emotional_debt_trajectory_notes: list[str] = []
    if emotional_debt_status == "elevated":
        emotional_debt_trajectory_status = "decompression_required"
        if repair_assessment.repair_needed:
            emotional_debt_trajectory_target = "repair_first_decompression"
            emotional_debt_trajectory_trigger = "repair_pressure_with_elevated_debt"
            emotional_debt_trajectory_notes.append(
                "repair_pressure_and_debt_require_relational_decompression"
            )
        elif (
            response_post_audit is not None and response_post_audit.status in {"review", "revise"}
        ) or (
            runtime_quality_doctor_report is not None
            and runtime_quality_doctor_report.status in {"watch", "revise"}
        ):
            emotional_debt_trajectory_target = "quality_stabilization_decompression"
            emotional_debt_trajectory_trigger = "quality_drift_with_elevated_debt"
            emotional_debt_trajectory_notes.append(
                "quality_drift_is_accumulating_relational_debt_and_requires_decompression"
            )
        else:
            emotional_debt_trajectory_target = "relational_decompression"
            emotional_debt_trajectory_trigger = "elevated_debt_detected"
            emotional_debt_trajectory_notes.append(
                "relational_load_is_high_enough_to_require_decompression"
            )
    elif emotional_debt_status == "watch":
        emotional_debt_trajectory_status = "watch"
        if empowerment_audit.status == "caution":
            emotional_debt_trajectory_target = "autonomy_preserving_decompression"
            emotional_debt_trajectory_trigger = "empowerment_caution_with_debt"
            emotional_debt_trajectory_notes.append(
                "empowerment_caution_keeps_debt_line_under_low_pressure_watch"
            )
        elif repair_assessment.repair_needed:
            emotional_debt_trajectory_target = "soft_repair_buffer"
            emotional_debt_trajectory_trigger = "soft_repair_pressure"
            emotional_debt_trajectory_notes.append(
                "repair_pressure_is_present_but_not_yet_in_full_decompression_mode"
            )
        else:
            emotional_debt_trajectory_target = "steadying_buffer"
            emotional_debt_trajectory_trigger = "soft_debt_watch"
            emotional_debt_trajectory_notes.append(
                "relational_load_is_rising_but_still_inside_watch_band"
            )
    else:
        emotional_debt_trajectory_status = "stable"
        emotional_debt_trajectory_target = "steady_low_debt"
        emotional_debt_trajectory_trigger = "debt_stable"
        emotional_debt_trajectory_notes.append("relational_debt_line_is_holding_low_and_stable")

    return {
        "emotional_debt_status": emotional_debt_status,
        "emotional_debt_score": emotional_debt_score,
        "debt_signals": debt_signals,
        "emotional_debt_trajectory_status": emotional_debt_trajectory_status,
        "emotional_debt_trajectory_target": emotional_debt_trajectory_target,
        "emotional_debt_trajectory_trigger": emotional_debt_trajectory_trigger,
        "emotional_debt_trajectory_notes": emotional_debt_trajectory_notes,
    }


def _build_growth_user_context(
    *,
    turn_index: int,
    recent_user_text: str,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    confidence_assessment: ConfidenceAssessment,
    response_sequence_plan: ResponseSequencePlan | None,
    memory_bundle: MemoryBundle,
    recall_count: int,
    filtered_recall_count: int,
    emotional_debt_status: str,
) -> dict[str, object]:
    growth_policy = _governance_section("growth_user_context")
    forming_turn_threshold = int(growth_policy.get("forming_turn_threshold", 1))
    stabilizing_turn_threshold = int(growth_policy.get("stabilizing_turn_threshold", 3))
    deepening_safety_threshold = float(
        growth_policy.get("deepening_psychological_safety_threshold", 0.75)
    )
    deepening_min_recall_count = int(growth_policy.get("deepening_min_recall_count", 1))
    if emotional_debt_status == "elevated":
        growth_stage = "repairing"
        growth_signal = "emotional_debt_accumulating"
    elif turn_index <= forming_turn_threshold:
        growth_stage = "forming"
        growth_signal = "initial_alignment"
    elif turn_index <= stabilizing_turn_threshold:
        growth_stage = "stabilizing"
        growth_signal = "relationship_patterning"
    elif (
        relationship_state.psychological_safety >= deepening_safety_threshold
        and relationship_state.dependency_risk == "low"
        and recall_count >= deepening_min_recall_count
    ):
        growth_stage = "deepening"
        growth_signal = "memory_continuity_plus_safety"
    else:
        growth_stage = "steadying"
        growth_signal = "ongoing_regulation"

    user_needs: list[str] = []
    if context_frame.appraisal == "negative" or context_frame.bid_signal == "connection_request":
        user_needs.append("validation")
    if context_frame.dialogue_act in {"question", "request"}:
        user_needs.append("clarity")
    if context_frame.topic in {"planning", "technical", "work"}:
        user_needs.append("concrete_next_step")
    if repair_assessment.repair_needed:
        user_needs.append("repair")
    if confidence_assessment.needs_clarification:
        user_needs.append("calibration")

    user_preferences: list[str] = []
    if _contains_chinese(recent_user_text):
        user_preferences.append("zh_context")
    if context_frame.attention in {"focused", "high"}:
        user_preferences.append("low_cognitive_load")
    if context_frame.dialogue_act == "question":
        user_preferences.append("direct_answer_first")
    if response_sequence_plan is not None and response_sequence_plan.mode == "two_part_sequence":
        user_preferences.append("segmented_delivery")
    if recall_count > 0:
        user_preferences.append("continuity_across_turns")
    if filtered_recall_count > 0:
        user_preferences.append("context_sensitive_recall")

    user_model_confidence = _clamp(
        float(growth_policy.get("user_model_confidence_base", 0.38))
        + min(turn_index, int(growth_policy.get("turn_cap", 5)))
        * float(growth_policy.get("turn_weight", 0.07))
        + min(recall_count, int(growth_policy.get("recall_cap", 3)))
        * float(growth_policy.get("recall_weight", 0.05))
        + (
            float(growth_policy.get("working_memory_bonus", 0.04))
            if len(memory_bundle.working_memory)
            >= int(growth_policy.get("working_memory_bonus_threshold", 2))
            else 0.0
        )
    )

    return {
        "growth_stage": growth_stage,
        "growth_signal": growth_signal,
        "user_needs": user_needs,
        "user_preferences": user_preferences,
        "user_model_confidence": user_model_confidence,
    }


def _build_strategy_audit(
    *,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    strategy_decision: StrategyDecision,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_post_audit: ResponsePostAudit | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
    emotional_debt_status: str,
) -> dict[str, object]:
    strategy_policy = _governance_section("strategy_audit")
    revise_statuses = {
        key: {str(item) for item in value or []}
        for key, value in dict(strategy_policy.get("revise_statuses") or {}).items()
    }
    watch_statuses = {
        key: {str(item) for item in value or []}
        for key, value in dict(strategy_policy.get("watch_statuses") or {}).items()
    }
    strategy_fit = "aligned"
    strategy_audit_notes: list[str] = []
    if (
        repair_assessment.repair_needed
        and str(strategy_policy.get("repair_strategy_token", "repair"))
        not in strategy_decision.strategy
        and policy_gate.selected_path != "repair_first"
    ):
        strategy_fit = "mismatch"
        strategy_audit_notes.append("repair_pressure_not_leading_strategy")
    elif (
        knowledge_boundary_decision.decision
        != str(strategy_policy.get("answer_directly_decision", "answer_directly"))
        and not knowledge_boundary_decision.should_disclose_uncertainty
        and strategy_decision.strategy
        == str(strategy_policy.get("uncertainty_strategy", "answer_with_uncertainty"))
    ):
        strategy_fit = "partial"
        strategy_audit_notes.append("boundary_path_more_conservative_than_needed")
    elif knowledge_boundary_decision.decision == str(
        strategy_policy.get("boundary_support_decision", "support_with_boundary")
    ) and policy_gate.red_line_status != str(
        strategy_policy.get("required_boundary_gate", "boundary_sensitive")
    ):
        strategy_fit = "partial"
        strategy_audit_notes.append("boundary_support_without_boundary_sensitive_gate")

    if rehearsal_result.projected_risk_level == "high":
        strategy_audit_notes.append("high_rehearsal_risk")
    if empowerment_audit.status in {"caution", "revise"}:
        strategy_audit_notes.append(f"empowerment_{empowerment_audit.status}")
    if response_post_audit is not None and response_post_audit.status in {"review", "revise"}:
        strategy_audit_notes.append(f"post_audit_{response_post_audit.status}")
    if runtime_quality_doctor_report is not None and runtime_quality_doctor_report.status in {
        "watch",
        "revise",
    }:
        strategy_audit_notes.append(f"quality_doctor_{runtime_quality_doctor_report.status}")

    if (
        empowerment_audit.status in revise_statuses.get("empowerment", {"revise"})
        or (
            response_post_audit
            and response_post_audit.status in revise_statuses.get("post_audit", {"revise"})
        )
        or (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status
            in revise_statuses.get("quality_doctor", {"revise"})
        )
        or strategy_fit == "mismatch"
    ):
        strategy_audit_status = "revise"
    elif (
        rehearsal_result.projected_risk_level in watch_statuses.get("rehearsal_risk", {"high"})
        or empowerment_audit.status in watch_statuses.get("empowerment", {"caution"})
        or (
            response_post_audit
            and response_post_audit.status in watch_statuses.get("post_audit", {"review"})
        )
        or (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status
            in watch_statuses.get("quality_doctor", {"watch"})
        )
        or emotional_debt_status in watch_statuses.get("emotional_debt", {"elevated"})
    ):
        strategy_audit_status = "watch"
    else:
        strategy_audit_status = "pass"

    return {
        "strategy_fit": strategy_fit,
        "strategy_audit_status": strategy_audit_status,
        "strategy_audit_notes": strategy_audit_notes,
    }


def _build_strategy_audit_trajectory(
    *,
    strategy_audit_status: str,
    strategy_fit: str,
    repair_assessment: RepairAssessment,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_post_audit: ResponsePostAudit | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
) -> dict[str, object]:
    strategy_audit_trajectory_notes: list[str] = []
    if strategy_audit_status == "revise":
        strategy_audit_trajectory_status = "corrective"
        if repair_assessment.repair_needed and strategy_fit == "mismatch":
            strategy_audit_trajectory_target = "repair_first_correction"
            strategy_audit_trajectory_trigger = "repair_alignment_correction"
            strategy_audit_trajectory_notes.append(
                "repair_pressure_keeps_strategy_audit_line_in_corrective_mode"
            )
        elif response_post_audit and response_post_audit.status == "revise":
            strategy_audit_trajectory_target = "post_audit_correction"
            strategy_audit_trajectory_trigger = "post_audit_correction_required"
            strategy_audit_trajectory_notes.append(
                "post_audit_revision_keeps_strategy_audit_line_corrective"
            )
        elif empowerment_audit.status == "revise":
            strategy_audit_trajectory_target = "empowerment_safe_correction"
            strategy_audit_trajectory_trigger = "empowerment_correction_required"
            strategy_audit_trajectory_notes.append(
                "empowerment_revision_keeps_strategy_audit_line_corrective"
            )
        elif runtime_quality_doctor_report and runtime_quality_doctor_report.status == "revise":
            strategy_audit_trajectory_target = "quality_safe_correction"
            strategy_audit_trajectory_trigger = "quality_correction_required"
            strategy_audit_trajectory_notes.append(
                "quality_revision_keeps_strategy_audit_line_corrective"
            )
        else:
            strategy_audit_trajectory_target = "strategy_fit_correction"
            strategy_audit_trajectory_trigger = "strategy_correction_required"
            strategy_audit_trajectory_notes.append(
                "strategy_fit_mismatch_keeps_strategy_audit_line_corrective"
            )
    elif strategy_audit_status == "watch":
        strategy_audit_trajectory_status = "watch"
        if rehearsal_result.projected_risk_level == "high":
            strategy_audit_trajectory_target = "risk_sensitive_strategy"
            strategy_audit_trajectory_trigger = "rehearsal_watch_active"
            strategy_audit_trajectory_notes.append(
                "rehearsal_risk_keeps_strategy_audit_line_under_watch"
            )
        elif empowerment_audit.status == "caution":
            strategy_audit_trajectory_target = "empowerment_guarded_strategy"
            strategy_audit_trajectory_trigger = "empowerment_watch_active"
            strategy_audit_trajectory_notes.append(
                "empowerment_caution_keeps_strategy_audit_line_under_watch"
            )
        elif response_post_audit and response_post_audit.status == "review":
            strategy_audit_trajectory_target = "post_audit_guarded_strategy"
            strategy_audit_trajectory_trigger = "post_audit_watch_active"
            strategy_audit_trajectory_notes.append(
                "post_audit_review_keeps_strategy_audit_line_under_watch"
            )
        elif runtime_quality_doctor_report and runtime_quality_doctor_report.status == "watch":
            strategy_audit_trajectory_target = "quality_guarded_strategy"
            strategy_audit_trajectory_trigger = "quality_watch_active"
            strategy_audit_trajectory_notes.append(
                "quality_watch_keeps_strategy_audit_line_under_watch"
            )
        else:
            strategy_audit_trajectory_target = "guarded_strategy_path"
            strategy_audit_trajectory_trigger = "strategy_watch_active"
            strategy_audit_trajectory_notes.append(
                "strategy_audit_watch_keeps_strategy_line_guarded"
            )
    else:
        strategy_audit_trajectory_status = "stable"
        strategy_audit_trajectory_target = "aligned_strategy_path"
        strategy_audit_trajectory_trigger = "strategy_line_stable"
        if strategy_fit == "aligned":
            strategy_audit_trajectory_notes.append("strategy_audit_line_is_holding_stable")

    return {
        "strategy_audit_trajectory_status": strategy_audit_trajectory_status,
        "strategy_audit_trajectory_target": strategy_audit_trajectory_target,
        "strategy_audit_trajectory_trigger": strategy_audit_trajectory_trigger,
        "strategy_audit_trajectory_notes": strategy_audit_trajectory_notes,
    }


def _build_strategy_supervision(
    *,
    strategy_audit_status: str,
    strategy_fit: str,
    repair_assessment: RepairAssessment,
    policy_gate: PolicyGateDecision,
    strategy_decision: StrategyDecision,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_post_audit: ResponsePostAudit | None,
) -> dict[str, object]:
    strategy_supervision_notes: list[str] = []
    if (
        strategy_audit_status == "revise"
        and repair_assessment.repair_needed
        and policy_gate.selected_path == "repair_first"
    ):
        strategy_supervision_status = "revise"
        strategy_supervision_mode = "repair_override_supervision"
        strategy_supervision_trigger = "repair_pressure_override"
        strategy_supervision_notes.append("repair_load_requires_supervised_strategy_override")
    elif strategy_audit_status == "revise" and policy_gate.red_line_status in {
        "boundary_sensitive",
        "blocked",
    }:
        strategy_supervision_status = "revise"
        strategy_supervision_mode = "boundary_lock_supervision"
        strategy_supervision_trigger = "policy_gate_boundary_lock"
        strategy_supervision_notes.append(
            "boundary_sensitive_gate_requires_hard_strategy_supervision"
        )
    elif strategy_audit_status == "revise":
        strategy_supervision_status = "revise"
        strategy_supervision_mode = "corrective_supervision"
        if empowerment_audit.status == "revise":
            strategy_supervision_trigger = "empowerment_revision_required"
            strategy_supervision_notes.append("empowerment_revision_requires_strategy_correction")
        elif response_post_audit and response_post_audit.status == "revise":
            strategy_supervision_trigger = "post_audit_revision_required"
            strategy_supervision_notes.append("post_audit_revision_requires_strategy_correction")
        elif rehearsal_result.projected_risk_level == "high":
            strategy_supervision_trigger = "rehearsal_risk_detected"
            strategy_supervision_notes.append("high_rehearsal_risk_requires_strategy_correction")
        else:
            strategy_supervision_trigger = "strategy_mismatch_requires_correction"
            strategy_supervision_notes.append("strategy_fit_mismatch_requires_explicit_supervision")
    elif (
        strategy_audit_status == "watch"
        or policy_gate.red_line_status == "boundary_sensitive"
        or strategy_decision.diversity_status == "intervened"
    ):
        strategy_supervision_status = "watch"
        if strategy_decision.diversity_status == "intervened":
            strategy_supervision_mode = "exploratory_supervision"
            strategy_supervision_trigger = "diversity_intervention_watch"
            strategy_supervision_notes.append("explored_strategy_needs_supervised_observation")
        elif policy_gate.red_line_status == "boundary_sensitive":
            strategy_supervision_mode = "boundary_guided_supervision"
            strategy_supervision_trigger = "policy_gate_boundary_watch"
            strategy_supervision_notes.append(
                "boundary_sensitive_gate_requires_tighter_strategy_watch"
            )
        elif rehearsal_result.projected_risk_level == "high":
            strategy_supervision_mode = "risk_guided_supervision"
            strategy_supervision_trigger = "rehearsal_risk_watch"
            strategy_supervision_notes.append("rehearsal_risk_keeps_strategy_under_watch")
        else:
            strategy_supervision_mode = "guided_supervision"
            strategy_supervision_trigger = "strategy_watch_required"
            strategy_supervision_notes.append("strategy_audit_watch_keeps_supervision_active")
    else:
        strategy_supervision_status = "pass"
        strategy_supervision_mode = "steady_supervision"
        strategy_supervision_trigger = "strategy_stable"
        if strategy_fit == "aligned":
            strategy_supervision_notes.append("strategy_shape_is_stable_under_current_constraints")

    return {
        "strategy_supervision_status": strategy_supervision_status,
        "strategy_supervision_mode": strategy_supervision_mode,
        "strategy_supervision_trigger": strategy_supervision_trigger,
        "strategy_supervision_notes": strategy_supervision_notes,
    }


def _build_strategy_supervision_trajectory(
    *,
    strategy_supervision_status: str,
    strategy_supervision_mode: str,
) -> dict[str, object]:
    strategy_supervision_trajectory_notes: list[str] = []
    if strategy_supervision_status == "revise":
        strategy_supervision_trajectory_status = "tighten"
        if strategy_supervision_mode == "repair_override_supervision":
            strategy_supervision_trajectory_target = "repair_override_supervision"
            strategy_supervision_trajectory_trigger = "repair_override_required"
            strategy_supervision_trajectory_notes.append(
                "repair_pressure_requires_tighter_strategy_supervision"
            )
        elif strategy_supervision_mode == "boundary_lock_supervision":
            strategy_supervision_trajectory_target = "boundary_lock_supervision"
            strategy_supervision_trajectory_trigger = "boundary_lock_required"
            strategy_supervision_trajectory_notes.append(
                "boundary_conditions_require_hard_supervision_lock"
            )
        else:
            strategy_supervision_trajectory_target = "corrective_supervision"
            strategy_supervision_trajectory_trigger = "corrective_supervision_required"
            strategy_supervision_trajectory_notes.append(
                "strategy_path_requires_explicit_corrective_tightening"
            )
    elif strategy_supervision_status == "watch":
        strategy_supervision_trajectory_status = "watch"
        if strategy_supervision_mode == "exploratory_supervision":
            strategy_supervision_trajectory_target = "exploratory_supervision"
            strategy_supervision_trajectory_trigger = "diversity_supervision_watch"
            strategy_supervision_trajectory_notes.append(
                "exploratory_strategy_keeps_supervision_line_under_watch"
            )
        elif strategy_supervision_mode == "boundary_guided_supervision":
            strategy_supervision_trajectory_target = "boundary_guided_supervision"
            strategy_supervision_trajectory_trigger = "boundary_supervision_watch"
            strategy_supervision_trajectory_notes.append(
                "boundary_sensitive_conditions_keep_supervision_line_under_watch"
            )
        elif strategy_supervision_mode == "risk_guided_supervision":
            strategy_supervision_trajectory_target = "risk_guided_supervision"
            strategy_supervision_trajectory_trigger = "risk_supervision_watch"
            strategy_supervision_trajectory_notes.append(
                "risk_pressure_keeps_supervision_line_under_tighter_watch"
            )
        else:
            strategy_supervision_trajectory_target = "guided_supervision"
            strategy_supervision_trajectory_trigger = "strategy_watch_active"
            strategy_supervision_trajectory_notes.append(
                "strategy_watch_keeps_supervision_line_active"
            )
    else:
        strategy_supervision_trajectory_status = "stable"
        strategy_supervision_trajectory_target = "steady_supervision"
        strategy_supervision_trajectory_trigger = "strategy_supervision_stable"
        strategy_supervision_trajectory_notes.append("strategy_supervision_line_is_holding_steady")

    return {
        "strategy_supervision_trajectory_status": (strategy_supervision_trajectory_status),
        "strategy_supervision_trajectory_target": (strategy_supervision_trajectory_target),
        "strategy_supervision_trajectory_trigger": (strategy_supervision_trajectory_trigger),
        "strategy_supervision_trajectory_notes": (strategy_supervision_trajectory_notes),
    }


def _build_strategy_prelude(
    *,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    strategy_decision: StrategyDecision,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_post_audit: ResponsePostAudit | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
    emotional_debt_status: str,
) -> dict[str, object]:
    audit = _build_strategy_audit(
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        strategy_decision=strategy_decision,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
        emotional_debt_status=emotional_debt_status,
    )
    audit_trajectory = _build_strategy_audit_trajectory(
        strategy_audit_status=str(audit["strategy_audit_status"]),
        strategy_fit=str(audit["strategy_fit"]),
        repair_assessment=repair_assessment,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
    )
    supervision = _build_strategy_supervision(
        strategy_audit_status=str(audit["strategy_audit_status"]),
        strategy_fit=str(audit["strategy_fit"]),
        repair_assessment=repair_assessment,
        policy_gate=policy_gate,
        strategy_decision=strategy_decision,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
        response_post_audit=response_post_audit,
    )
    supervision_trajectory = _build_strategy_supervision_trajectory(
        strategy_supervision_status=str(supervision["strategy_supervision_status"]),
        strategy_supervision_mode=str(supervision["strategy_supervision_mode"]),
    )

    return {
        **audit,
        **audit_trajectory,
        **supervision,
        **supervision_trajectory,
    }


def _build_moral_prelude(
    *,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    strategy_decision: StrategyDecision,
    empowerment_audit: EmpowermentAudit,
) -> dict[str, object]:
    moral_principles: list[str] = ["care", "respect_for_autonomy"]
    moral_notes: list[str] = []
    if knowledge_boundary_decision.should_disclose_uncertainty:
        moral_principles.append("truthfulness_about_limits")
    if relationship_state.dependency_risk == "elevated":
        moral_principles.append("dependency_safety")
    if repair_assessment.repair_needed:
        moral_principles.append("repair_before_pressure")
    if policy_gate.red_line_status == "boundary_sensitive":
        moral_principles.append("boundary_protection")

    if relationship_state.dependency_risk == "elevated":
        moral_conflict = "support_vs_dependency"
        moral_posture = "protective_boundary_care"
        moral_notes.append("dependency_pressure_requires_relational_boundary")
    elif knowledge_boundary_decision.should_disclose_uncertainty:
        moral_conflict = "truth_vs_comfort"
        moral_posture = "truthful_clarity"
        moral_notes.append("uncertainty_needs_explicit_disclosure")
    elif repair_assessment.repair_needed:
        moral_conflict = "care_vs_directness"
        moral_posture = "repair_first_care"
        moral_notes.append("repair_load_requires_softer_progress")
    else:
        moral_conflict = "none"
        moral_posture = "steady_progress_care"

    if (
        policy_gate.red_line_status == "blocked"
        or (
            relationship_state.dependency_risk == "elevated"
            and knowledge_boundary_decision.decision != "support_with_boundary"
        )
        or (
            knowledge_boundary_decision.should_disclose_uncertainty
            and strategy_decision.strategy != "answer_with_uncertainty"
        )
    ):
        moral_reasoning_status = "revise"
    elif (
        moral_conflict != "none"
        or empowerment_audit.status == "caution"
        or policy_gate.red_line_status == "boundary_sensitive"
    ):
        moral_reasoning_status = "watch"
    else:
        moral_reasoning_status = "pass"

    moral_trajectory_notes: list[str] = []
    if moral_reasoning_status == "revise":
        moral_trajectory_status = "recenter"
        if moral_conflict == "support_vs_dependency":
            moral_trajectory_target = "dependency_safe_care"
            moral_trajectory_trigger = "dependency_pressure_detected"
            moral_trajectory_notes.append(
                "dependency_pressure_requires_moral_recenter_toward_safer_boundaries"
            )
        elif moral_conflict == "truth_vs_comfort":
            moral_trajectory_target = "truthful_limit_clarity"
            moral_trajectory_trigger = "uncertainty_disclosure_required"
            moral_trajectory_notes.append(
                "truth_comfort_tension_requires_recenter_toward_clear_limit_disclosure"
            )
        elif moral_conflict == "care_vs_directness":
            moral_trajectory_target = "repair_first_care"
            moral_trajectory_trigger = "repair_pressure_detected"
            moral_trajectory_notes.append(
                "repair_pressure_requires_moral_recenter_toward_repair_first_care"
            )
        else:
            moral_trajectory_target = "boundary_protective_care"
            moral_trajectory_trigger = "moral_recenter_required"
            moral_trajectory_notes.append(
                "moral_line_requires_recentering_under_competing_constraints"
            )
    elif moral_reasoning_status == "watch":
        moral_trajectory_status = "watch"
        if policy_gate.red_line_status == "boundary_sensitive":
            moral_trajectory_target = "boundary_protection"
            moral_trajectory_trigger = "boundary_sensitive_guard"
            moral_trajectory_notes.append(
                "boundary_sensitive_policy_gate_keeps_moral_line_under_watch"
            )
        elif moral_conflict == "truth_vs_comfort":
            moral_trajectory_target = "truthful_limit_clarity"
            moral_trajectory_trigger = "comfort_truth_balance_watch"
            moral_trajectory_notes.append("truth_comfort_tension_is_present_but_not_yet_off_center")
        elif empowerment_audit.status == "caution":
            moral_trajectory_target = "empowerment_safe_care"
            moral_trajectory_trigger = "empowerment_caution_detected"
            moral_trajectory_notes.append(
                "empowerment_caution_keeps_moral_line_under_supervised_watch"
            )
        else:
            moral_trajectory_target = "steady_progress_care"
            moral_trajectory_trigger = "moral_tension_watch"
            moral_trajectory_notes.append("moral_tension_is_present_without_full_recentering")
    else:
        moral_trajectory_status = "stable"
        moral_trajectory_target = "steady_progress_care"
        moral_trajectory_trigger = "moral_line_stable"
        moral_trajectory_notes.append(
            "moral_line_is_holding_stable_under_current_relational_constraints"
        )

    return {
        "moral_reasoning_status": moral_reasoning_status,
        "moral_posture": moral_posture,
        "moral_conflict": moral_conflict,
        "moral_principles": moral_principles,
        "moral_notes": moral_notes,
        "moral_trajectory_status": moral_trajectory_status,
        "moral_trajectory_target": moral_trajectory_target,
        "moral_trajectory_trigger": moral_trajectory_trigger,
        "moral_trajectory_notes": moral_trajectory_notes,
    }


def _build_user_model_prelude(
    *,
    turn_index: int,
    context_frame: ContextFrame,
    repair_assessment: RepairAssessment,
    memory_bundle: MemoryBundle,
    recall_count: int,
    filtered_recall_count: int,
    user_needs: list[str],
    user_preferences: list[str],
    user_model_confidence: float,
) -> dict[str, object]:
    model_memory_text = " ".join(
        [
            *memory_bundle.semantic_memory[-4:],
            *memory_bundle.relational_memory[-4:],
            *memory_bundle.reflective_memory[-2:],
        ]
    ).lower()
    user_model_evolution_notes: list[str] = []
    if filtered_recall_count > 0:
        user_model_shift_signal = "context_drift"
        user_model_revision_mode = "memory_recalibration"
        user_model_evolution_notes.append("filtered_recall_signals_context_mismatch")
    elif repair_assessment.repair_needed:
        user_model_shift_signal = "repair_pressure"
        user_model_revision_mode = "repair_reframing"
        user_model_evolution_notes.append("repair_signal_requires_user_model_softening")
    elif (
        context_frame.attention in {"focused", "high"} and "low_cognitive_load" in user_preferences
    ):
        user_model_shift_signal = "delivery_preference_reinforced"
        user_model_revision_mode = "delivery_preference_refinement"
        user_model_evolution_notes.append("focused_attention_reinforces_low_load_preference")
    elif recall_count == 0 and turn_index >= 3:
        user_model_shift_signal = "underfit_memory"
        user_model_revision_mode = "needs_recalibration"
        user_model_evolution_notes.append("later_turn_without_recall_signals_model_underfit")
    else:
        user_model_shift_signal = "stable"
        user_model_revision_mode = "steady_refinement"

    remembered_validation = "validation" in model_memory_text or "support" in model_memory_text
    remembered_clarity = "clarity" in model_memory_text or "direct" in model_memory_text
    remembered_low_load = "low_cognitive_load" in model_memory_text or "simple" in model_memory_text
    if "validation" in user_needs and not remembered_validation and recall_count > 0:
        user_model_evolution_notes.append("validation_need_not_yet_grounded_in_memory")
    if "clarity" in user_needs and not remembered_clarity and recall_count > 0:
        user_model_evolution_notes.append("clarity_need_requires_model_refresh")
    if "low_cognitive_load" in user_preferences and not remembered_low_load and recall_count > 0:
        user_model_evolution_notes.append("delivery_preference_not_yet_persisted")

    if filtered_recall_count > 0 or (
        recall_count > 0
        and len(user_model_evolution_notes) >= 2
        and user_model_shift_signal != "delivery_preference_reinforced"
    ):
        user_model_evolution_status = "revise"
    elif (
        user_model_shift_signal != "stable"
        or len(user_model_evolution_notes) > 0
        or user_model_confidence < 0.5
    ):
        user_model_evolution_status = "watch"
    else:
        user_model_evolution_status = "pass"

    user_model_trajectory_notes: list[str] = []
    if user_model_evolution_status == "revise":
        user_model_trajectory_status = "recenter"
        if user_model_shift_signal == "context_drift":
            user_model_trajectory_target = "context_model_recenter"
            user_model_trajectory_trigger = "context_drift_detected"
            user_model_trajectory_notes.append("context_mismatch_requires_user_model_recenter")
        elif user_model_shift_signal == "repair_pressure":
            user_model_trajectory_target = "repair_sensitive_model"
            user_model_trajectory_trigger = "repair_pressure_detected"
            user_model_trajectory_notes.append("repair_pressure_requires_relational_model_reframe")
        elif user_model_shift_signal == "underfit_memory":
            user_model_trajectory_target = "memory_grounded_model"
            user_model_trajectory_trigger = "underfit_memory_detected"
            user_model_trajectory_notes.append("memory_underfit_requires_user_model_recenter")
        else:
            user_model_trajectory_target = "preference_recenter"
            user_model_trajectory_trigger = "model_revision_required"
            user_model_trajectory_notes.append(
                "user_model_revision_requires_recentered_preferences"
            )
    elif user_model_evolution_status == "watch":
        user_model_trajectory_status = "watch"
        if user_model_shift_signal == "delivery_preference_reinforced":
            user_model_trajectory_target = "delivery_preference_refinement"
            user_model_trajectory_trigger = "delivery_preference_reinforced"
            user_model_trajectory_notes.append("delivery_preference_is_shifting_but_still_stable")
        elif user_model_shift_signal == "repair_pressure":
            user_model_trajectory_target = "repair_sensitive_model"
            user_model_trajectory_trigger = "repair_pressure_watch"
            user_model_trajectory_notes.append("repair_pressure_keeps_user_model_under_watch")
        else:
            user_model_trajectory_target = "steady_refinement"
            user_model_trajectory_trigger = "soft_model_drift"
            user_model_trajectory_notes.append("user_model_is_shifting_without_full_recenter")
    else:
        user_model_trajectory_status = "stable"
        user_model_trajectory_target = "steady_refinement"
        user_model_trajectory_trigger = "model_stable"
        if user_model_confidence >= 0.58:
            user_model_trajectory_notes.append("user_model_is_holding_stable_across_turns")

    return {
        "user_model_evolution_status": user_model_evolution_status,
        "user_model_revision_mode": user_model_revision_mode,
        "user_model_shift_signal": user_model_shift_signal,
        "user_model_evolution_notes": user_model_evolution_notes,
        "user_model_trajectory_status": user_model_trajectory_status,
        "user_model_trajectory_target": user_model_trajectory_target,
        "user_model_trajectory_trigger": user_model_trajectory_trigger,
        "user_model_trajectory_notes": user_model_trajectory_notes,
    }


def _build_expectation_calibration_prelude(
    *,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    confidence_assessment: ConfidenceAssessment,
    response_sequence_plan: ResponseSequencePlan | None,
) -> dict[str, object]:
    expectation_state = _build_expectation_calibration_state(
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        confidence_assessment=confidence_assessment,
        response_sequence_plan=response_sequence_plan,
    )
    expectation_calibration_status = str(expectation_state["status"])
    expectation_calibration_target = str(expectation_state["target"])
    expectation_calibration_trigger = str(expectation_state["trigger"])
    expectation_calibration_notes = list(expectation_state["notes"])
    expectation_trajectory = _build_expectation_calibration_trajectory(
        status=expectation_calibration_status,
        trigger=expectation_calibration_trigger,
        target=expectation_calibration_target,
    )
    expectation_calibration_trajectory_status = str(expectation_trajectory["trajectory_status"])
    expectation_calibration_trajectory_target = str(expectation_trajectory["trajectory_target"])
    expectation_calibration_trajectory_trigger = str(expectation_trajectory["trajectory_trigger"])
    expectation_calibration_trajectory_notes = list(expectation_trajectory["trajectory_notes"])

    return {
        "expectation_calibration_status": expectation_calibration_status,
        "expectation_calibration_target": expectation_calibration_target,
        "expectation_calibration_trigger": expectation_calibration_trigger,
        "expectation_calibration_notes": expectation_calibration_notes,
        "expectation_calibration_trajectory_status": (expectation_calibration_trajectory_status),
        "expectation_calibration_trajectory_target": (expectation_calibration_trajectory_target),
        "expectation_calibration_trajectory_trigger": (expectation_calibration_trajectory_trigger),
        "expectation_calibration_trajectory_notes": (expectation_calibration_trajectory_notes),
    }


def _build_expectation_calibration_state(
    *,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    confidence_assessment: ConfidenceAssessment,
    response_sequence_plan: ResponseSequencePlan | None,
) -> dict[str, object]:
    if relationship_state.dependency_risk == "elevated":
        if knowledge_boundary_decision.decision == "support_with_boundary":
            return {
                "status": "revise",
                "target": "bounded_relational_support",
                "trigger": "relational_boundary_required",
                "notes": ["dependency_pressure_requires_relational_expectation_reset"],
            }
        return {
            "status": "revise",
            "target": "agency_preserving_support",
            "trigger": "dependency_pressure_detected",
            "notes": ["dependency_pressure_requires_agency_preserving_expectation_reset"],
        }
    if knowledge_boundary_decision.decision == "answer_with_uncertainty":
        if confidence_assessment.level == "low":
            return {
                "status": "revise",
                "target": "uncertainty_honest_support",
                "trigger": "certainty_request_requires_reset",
                "notes": ["certainty_request_requires_explicit_expectation_reset"],
            }
        return {
            "status": "watch",
            "target": "uncertainty_honest_support",
            "trigger": "uncertainty_disclosure_required",
            "notes": ["uncertainty_disclosure_keeps_expectation_line_under_watch"],
        }
    if confidence_assessment.needs_clarification:
        return {
            "status": "watch",
            "target": "context_before_commitment",
            "trigger": "clarification_required",
            "notes": ["missing_context_requires_context_first_expectation"],
        }
    if repair_assessment.repair_needed and policy_gate.selected_path == "repair_first":
        return {
            "status": "watch",
            "target": "low_pressure_repair_support",
            "trigger": "repair_pressure_requires_soft_expectation",
            "notes": ["repair_pressure_requires_lower_pressure_relational_expectation"],
        }
    if response_sequence_plan is not None and response_sequence_plan.mode == "two_part_sequence":
        return {
            "status": "watch",
            "target": "segmented_progress_expectation",
            "trigger": "segmented_delivery_active",
            "notes": ["segmented_delivery_signals_expectation_should_stay_stepwise"],
        }
    return {
        "status": "pass",
        "target": "bounded_progress_expectation",
        "trigger": "expectation_line_stable",
        "notes": [],
    }


def _build_expectation_calibration_trajectory(
    *,
    status: str,
    trigger: str,
    target: str,
) -> dict[str, object]:
    if status == "revise":
        if trigger == "relational_boundary_required":
            return {
                "trajectory_status": "reset",
                "trajectory_target": "bounded_relational_support",
                "trajectory_trigger": "relational_boundary_expectation_reset",
                "trajectory_notes": ["relational_boundary_keeps_expectation_line_in_reset_mode"],
            }
        if trigger == "dependency_pressure_detected":
            return {
                "trajectory_status": "reset",
                "trajectory_target": "agency_preserving_support",
                "trajectory_trigger": "dependency_expectation_reset",
                "trajectory_notes": ["dependency_pressure_keeps_expectation_line_in_reset_mode"],
            }
        if trigger == "certainty_request_requires_reset":
            return {
                "trajectory_status": "reset",
                "trajectory_target": "uncertainty_honest_support",
                "trajectory_trigger": "uncertainty_expectation_reset",
                "trajectory_notes": ["certainty_request_keeps_expectation_line_in_reset_mode"],
            }
        return {
            "trajectory_status": "reset",
            "trajectory_target": target,
            "trajectory_trigger": "expectation_reset_required",
            "trajectory_notes": ["expectation_line_requires_active_reset"],
        }
    if status == "watch":
        if trigger == "uncertainty_disclosure_required":
            return {
                "trajectory_status": "watch",
                "trajectory_target": "uncertainty_honest_support",
                "trajectory_trigger": "uncertainty_expectation_watch",
                "trajectory_notes": ["uncertainty_disclosure_keeps_expectation_line_under_watch"],
            }
        if trigger == "clarification_required":
            return {
                "trajectory_status": "watch",
                "trajectory_target": "context_before_commitment",
                "trajectory_trigger": "clarification_expectation_watch",
                "trajectory_notes": ["clarification_need_keeps_expectation_line_under_watch"],
            }
        if trigger == "repair_pressure_requires_soft_expectation":
            return {
                "trajectory_status": "watch",
                "trajectory_target": "low_pressure_repair_support",
                "trajectory_trigger": "repair_expectation_watch",
                "trajectory_notes": ["repair_pressure_keeps_expectation_line_under_watch"],
            }
        if trigger == "segmented_delivery_active":
            return {
                "trajectory_status": "watch",
                "trajectory_target": "segmented_progress_expectation",
                "trajectory_trigger": "segmented_expectation_watch",
                "trajectory_notes": ["segmented_delivery_keeps_expectation_line_under_watch"],
            }
        return {
            "trajectory_status": "watch",
            "trajectory_target": "bounded_progress_expectation",
            "trajectory_trigger": "expectation_watch_active",
            "trajectory_notes": ["expectation_line_is_shifting_without_full_reset"],
        }
    return {
        "trajectory_status": "stable",
        "trajectory_target": "bounded_progress_expectation",
        "trajectory_trigger": "expectation_line_stable",
        "trajectory_notes": ["expectation_line_is_holding_stable"],
    }


def _build_system3_prelude(
    *,
    turn_index: int,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    response_sequence_plan: ResponseSequencePlan | None,
    response_post_audit: ResponsePostAudit | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
    confidence_assessment: ConfidenceAssessment,
    identity: dict[str, object],
    growth_user_context: dict[str, object],
    emotional_debt: dict[str, object],
    strategy: dict[str, object],
    moral: dict[str, object],
    user_model: dict[str, object],
    expectation: dict[str, object],
    recall_count: int,
    filtered_recall_count: int,
) -> _System3Prelude:
    return _System3Prelude(
        turn_index=turn_index,
        recall_count=recall_count,
        filtered_recall_count=filtered_recall_count,
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        response_sequence_plan=response_sequence_plan,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
        confidence_assessment=confidence_assessment,
        identity_anchor=str(identity["identity_anchor"]),
        identity_consistency=str(identity["identity_consistency"]),
        identity_confidence=float(identity["identity_confidence"]),
        identity_trajectory_status=str(identity["identity_trajectory_status"]),
        identity_trajectory_target=str(identity["identity_trajectory_target"]),
        identity_trajectory_trigger=str(identity["identity_trajectory_trigger"]),
        identity_trajectory_notes=list(identity["identity_trajectory_notes"]),
        growth_stage=str(growth_user_context["growth_stage"]),
        growth_signal=str(growth_user_context["growth_signal"]),
        user_model_confidence=float(growth_user_context["user_model_confidence"]),
        user_needs=list(growth_user_context["user_needs"]),
        user_preferences=list(growth_user_context["user_preferences"]),
        emotional_debt_status=str(emotional_debt["emotional_debt_status"]),
        emotional_debt_score=float(emotional_debt["emotional_debt_score"]),
        debt_signals=list(emotional_debt["debt_signals"]),
        emotional_debt_trajectory_status=str(emotional_debt["emotional_debt_trajectory_status"]),
        emotional_debt_trajectory_target=str(emotional_debt["emotional_debt_trajectory_target"]),
        emotional_debt_trajectory_trigger=str(emotional_debt["emotional_debt_trajectory_trigger"]),
        emotional_debt_trajectory_notes=list(emotional_debt["emotional_debt_trajectory_notes"]),
        strategy_audit_status=str(strategy["strategy_audit_status"]),
        strategy_fit=str(strategy["strategy_fit"]),
        strategy_audit_notes=list(strategy["strategy_audit_notes"]),
        strategy_audit_trajectory_status=str(strategy["strategy_audit_trajectory_status"]),
        strategy_audit_trajectory_target=str(strategy["strategy_audit_trajectory_target"]),
        strategy_audit_trajectory_trigger=str(strategy["strategy_audit_trajectory_trigger"]),
        strategy_audit_trajectory_notes=list(strategy["strategy_audit_trajectory_notes"]),
        strategy_supervision_status=str(strategy["strategy_supervision_status"]),
        strategy_supervision_mode=str(strategy["strategy_supervision_mode"]),
        strategy_supervision_trigger=str(strategy["strategy_supervision_trigger"]),
        strategy_supervision_notes=list(strategy["strategy_supervision_notes"]),
        strategy_supervision_trajectory_status=str(
            strategy["strategy_supervision_trajectory_status"]
        ),
        strategy_supervision_trajectory_target=str(
            strategy["strategy_supervision_trajectory_target"]
        ),
        strategy_supervision_trajectory_trigger=str(
            strategy["strategy_supervision_trajectory_trigger"]
        ),
        strategy_supervision_trajectory_notes=list(
            strategy["strategy_supervision_trajectory_notes"]
        ),
        moral_reasoning_status=str(moral["moral_reasoning_status"]),
        moral_posture=str(moral["moral_posture"]),
        moral_conflict=str(moral["moral_conflict"]),
        moral_principles=list(moral["moral_principles"]),
        moral_notes=list(moral["moral_notes"]),
        moral_trajectory_status=str(moral["moral_trajectory_status"]),
        moral_trajectory_target=str(moral["moral_trajectory_target"]),
        moral_trajectory_trigger=str(moral["moral_trajectory_trigger"]),
        moral_trajectory_notes=list(moral["moral_trajectory_notes"]),
        user_model_evolution_status=str(user_model["user_model_evolution_status"]),
        user_model_revision_mode=str(user_model["user_model_revision_mode"]),
        user_model_shift_signal=str(user_model["user_model_shift_signal"]),
        user_model_evolution_notes=list(user_model["user_model_evolution_notes"]),
        user_model_trajectory_status=str(user_model["user_model_trajectory_status"]),
        user_model_trajectory_target=str(user_model["user_model_trajectory_target"]),
        user_model_trajectory_trigger=str(user_model["user_model_trajectory_trigger"]),
        user_model_trajectory_notes=list(user_model["user_model_trajectory_notes"]),
        expectation_calibration_status=str(expectation["expectation_calibration_status"]),
        expectation_calibration_target=str(expectation["expectation_calibration_target"]),
        expectation_calibration_trigger=str(expectation["expectation_calibration_trigger"]),
        expectation_calibration_notes=list(expectation["expectation_calibration_notes"]),
        expectation_calibration_trajectory_status=str(
            expectation["expectation_calibration_trajectory_status"]
        ),
        expectation_calibration_trajectory_target=str(
            expectation["expectation_calibration_trajectory_target"]
        ),
        expectation_calibration_trajectory_trigger=str(
            expectation["expectation_calibration_trajectory_trigger"]
        ),
        expectation_calibration_trajectory_notes=list(
            expectation["expectation_calibration_trajectory_notes"]
        ),
    )


def build_system3_snapshot(
    *,
    turn_index: int,
    transcript_messages: list[dict[str, str]],
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    memory_bundle: MemoryBundle,
    memory_recall: dict[str, object] | None,
    confidence_assessment: ConfidenceAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    strategy_decision: StrategyDecision,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_sequence_plan: ResponseSequencePlan | None,
    response_post_audit: ResponsePostAudit | None,
    response_normalization: ResponseNormalizationResult | None,
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None,
) -> System3Snapshot:
    recent_user_messages = [
        str(message.get("content", "")).strip()
        for message in transcript_messages[-8:]
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]
    recent_user_text = " ".join(recent_user_messages[-3:])
    recall_count = int((memory_recall or {}).get("recall_count", 0))
    filtered_recall_count = int(
        ((memory_recall or {}).get("integrity_summary", {}) or {}).get("filtered_count", 0)
    )

    identity = _build_identity_prelude(
        context_frame=context_frame,
        knowledge_boundary_decision=knowledge_boundary_decision,
        confidence_assessment=confidence_assessment,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
        empowerment_audit=empowerment_audit,
        response_normalization=response_normalization,
    )
    emotional_debt = _build_emotional_debt_prelude(
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
        response_normalization=response_normalization,
        empowerment_audit=empowerment_audit,
    )
    growth_user_context = _build_growth_user_context(
        turn_index=turn_index,
        recent_user_text=recent_user_text,
        context_frame=context_frame,
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        confidence_assessment=confidence_assessment,
        response_sequence_plan=response_sequence_plan,
        memory_bundle=memory_bundle,
        recall_count=recall_count,
        filtered_recall_count=filtered_recall_count,
        emotional_debt_status=str(emotional_debt["emotional_debt_status"]),
    )
    strategy = _build_strategy_prelude(
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        strategy_decision=strategy_decision,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
        emotional_debt_status=str(emotional_debt["emotional_debt_status"]),
    )
    moral = _build_moral_prelude(
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        strategy_decision=strategy_decision,
        empowerment_audit=empowerment_audit,
    )
    user_model = _build_user_model_prelude(
        turn_index=turn_index,
        context_frame=context_frame,
        repair_assessment=repair_assessment,
        memory_bundle=memory_bundle,
        recall_count=recall_count,
        filtered_recall_count=filtered_recall_count,
        user_needs=list(growth_user_context["user_needs"]),
        user_preferences=list(growth_user_context["user_preferences"]),
        user_model_confidence=float(growth_user_context["user_model_confidence"]),
    )
    expectation = _build_expectation_calibration_prelude(
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        confidence_assessment=confidence_assessment,
        response_sequence_plan=response_sequence_plan,
    )
    prelude = _build_system3_prelude(
        turn_index=turn_index,
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        response_sequence_plan=response_sequence_plan,
        response_post_audit=response_post_audit,
        runtime_quality_doctor_report=runtime_quality_doctor_report,
        confidence_assessment=confidence_assessment,
        identity=identity,
        growth_user_context=growth_user_context,
        emotional_debt=emotional_debt,
        strategy=strategy,
        moral=moral,
        user_model=user_model,
        expectation=expectation,
        recall_count=recall_count,
        filtered_recall_count=filtered_recall_count,
    )
    return build_system3_phase2_snapshot(prelude=prelude)
