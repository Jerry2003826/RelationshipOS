"""System 3 meta-runtime: governance snapshot and quality doctor."""

from __future__ import annotations

import re

from relationship_os.application.analyzers._utils import (
    _clamp,
    _compact,
    _contains_any,
    _contains_chinese,
    _contains_forbidden_dependency_language,
    _contains_forbidden_false_certainty_language,
    _has_mixed_language,
)
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


def build_runtime_quality_doctor_report(
    *,
    transcript_messages: list[dict[str, str]],
    user_message: str,
    assistant_responses: list[str],
    triggered_turn_index: int,
    window_turns: int,
) -> RuntimeQualityDoctorReport:
    recent_messages = list(transcript_messages)
    recent_messages.append({"role": "user", "content": user_message})
    recent_messages.extend(
        {"role": "assistant", "content": content}
        for content in assistant_responses
        if content.strip()
    )
    max_window_messages = max(2, window_turns * 3)
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
    for content in assistant_window:
        tokens = re.findall(r"\b\w+\b", content.lower())
        signature = " ".join(tokens[:3]).strip()
        if signature:
            opening_counts[signature] = opening_counts.get(signature, 0) + 1
    repeated_opening_count = sum(count for count in opening_counts.values() if count > 1)
    if repeated_opening_count >= 2:
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
        if "\n\n" in content or "  " in content or content.count("...") >= 2
    )
    if format_noise_count > 0:
        issues.append("format_noise")
        recommended_repairs.append("normalize spacing and reduce filler punctuation")

    contradiction_count = 0
    certainty_conflict = any(
        _contains_forbidden_false_certainty_language(content)
        for content in assistant_window
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
        _contains_forbidden_dependency_language(content)
        for content in assistant_window
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

    if "logic_contradiction" in issues or len(issues) >= 3:
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

    if knowledge_boundary_decision.decision == "support_with_boundary":
        identity_anchor = "collaborative_boundaried_support"
    elif context_frame.topic in {"planning", "technical", "work"}:
        identity_anchor = "grounded_progress_partner"
    elif context_frame.bid_signal == "connection_request":
        identity_anchor = "relational_support_partner"
    else:
        identity_anchor = "collaborative_reflective_support"

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
        + (0.08 if identity_consistency == "stable" else 0.0)
        - (
            0.08
            if identity_consistency == "watch"
            else 0.18 if identity_consistency == "drift" else 0.0
        )
    )

    identity_trajectory_target = identity_anchor
    identity_trajectory_notes: list[str] = []
    if identity_consistency == "drift":
        identity_trajectory_status = "recenter"
        if response_post_audit and response_post_audit.status == "revise":
            identity_trajectory_trigger = "response_post_audit_drift"
            identity_trajectory_notes.append("post_audit_revision_forced_identity_recenter")
        elif (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "revise"
        ):
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
        elif (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "watch"
        ):
            identity_trajectory_trigger = "runtime_quality_doctor_watch"
            identity_trajectory_notes.append("quality_doctor_watch_requires_identity_attention")
        else:
            identity_trajectory_trigger = "identity_soft_drift"
            identity_trajectory_notes.append("identity_signals_show_soft_drift")
    else:
        identity_trajectory_status = "stable"
        identity_trajectory_trigger = "identity_consistent"
        if identity_confidence >= 0.72:
            identity_trajectory_notes.append("identity_anchor_holding_steady")

    emotional_debt_score = 0.0
    debt_signals: list[str] = []
    if repair_assessment.repair_needed:
        emotional_debt_score += (
            0.34 if repair_assessment.severity == "high" else 0.22
        )
        debt_signals.append(f"repair_{repair_assessment.severity}")
    if relationship_state.turbulence_risk == "elevated":
        emotional_debt_score += 0.14
        debt_signals.append("turbulence_pressure")
    if relationship_state.dependency_risk == "elevated":
        emotional_debt_score += 0.2
        debt_signals.append("dependency_boundary_pressure")
    if response_post_audit is not None and response_post_audit.status in {"review", "revise"}:
        emotional_debt_score += 0.08 if response_post_audit.status == "review" else 0.18
        debt_signals.append(f"post_audit_{response_post_audit.status}")
    if runtime_quality_doctor_report is not None and runtime_quality_doctor_report.status in {
        "watch",
        "revise",
    }:
        emotional_debt_score += (
            0.1 if runtime_quality_doctor_report.status == "watch" else 0.2
        )
        debt_signals.append(f"quality_doctor_{runtime_quality_doctor_report.status}")
    if response_normalization is not None and response_normalization.changed:
        emotional_debt_score += 0.08
        debt_signals.append("response_normalized")
    emotional_debt_score = round(min(emotional_debt_score, 1.0), 3)
    if emotional_debt_score >= 0.56:
        emotional_debt_status = "elevated"
    elif emotional_debt_score >= 0.24:
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
            response_post_audit is not None
            and response_post_audit.status in {"review", "revise"}
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
        emotional_debt_trajectory_notes.append(
            "relational_debt_line_is_holding_low_and_stable"
        )

    if emotional_debt_status == "elevated":
        growth_stage = "repairing"
        growth_signal = "emotional_debt_accumulating"
    elif turn_index <= 1:
        growth_stage = "forming"
        growth_signal = "initial_alignment"
    elif turn_index <= 3:
        growth_stage = "stabilizing"
        growth_signal = "relationship_patterning"
    elif (
        relationship_state.psychological_safety >= 0.75
        and relationship_state.dependency_risk == "low"
        and recall_count > 0
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
        0.38
        + min(turn_index, 5) * 0.07
        + min(recall_count, 3) * 0.05
        + (0.04 if len(memory_bundle.working_memory) >= 2 else 0.0)
    )

    strategy_fit = "aligned"
    strategy_audit_notes: list[str] = []
    if (
        repair_assessment.repair_needed
        and "repair" not in strategy_decision.strategy
        and policy_gate.selected_path != "repair_first"
    ):
        strategy_fit = "mismatch"
        strategy_audit_notes.append("repair_pressure_not_leading_strategy")
    elif (
        knowledge_boundary_decision.decision != "answer_directly"
        and not knowledge_boundary_decision.should_disclose_uncertainty
        and strategy_decision.strategy == "answer_with_uncertainty"
    ):
        strategy_fit = "partial"
        strategy_audit_notes.append("boundary_path_more_conservative_than_needed")
    elif (
        knowledge_boundary_decision.decision == "support_with_boundary"
        and policy_gate.red_line_status != "boundary_sensitive"
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
        strategy_audit_notes.append(
            f"quality_doctor_{runtime_quality_doctor_report.status}"
        )

    if (
        empowerment_audit.status == "revise"
        or (response_post_audit and response_post_audit.status == "revise")
        or (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "revise"
        )
        or strategy_fit == "mismatch"
    ):
        strategy_audit_status = "revise"
    elif (
        rehearsal_result.projected_risk_level == "high"
        or empowerment_audit.status == "caution"
        or (response_post_audit and response_post_audit.status == "review")
        or (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "watch"
        )
        or emotional_debt_status == "elevated"
    ):
        strategy_audit_status = "watch"
    else:
        strategy_audit_status = "pass"

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
        elif (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "revise"
        ):
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
        elif (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "watch"
        ):
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
            strategy_audit_trajectory_notes.append(
                "strategy_audit_line_is_holding_stable"
            )

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
    elif (
        strategy_audit_status == "revise"
        and policy_gate.red_line_status in {"boundary_sensitive", "blocked"}
    ):
        strategy_supervision_status = "revise"
        strategy_supervision_mode = "boundary_lock_supervision"
        strategy_supervision_trigger = "policy_gate_boundary_lock"
        strategy_supervision_notes.append("boundary_sensitive_gate_requires_hard_strategy_supervision")
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
            strategy_supervision_notes.append("boundary_sensitive_gate_requires_tighter_strategy_watch")
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
        strategy_supervision_trajectory_notes.append(
            "strategy_supervision_line_is_holding_steady"
        )

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
            moral_trajectory_notes.append(
                "truth_comfort_tension_is_present_but_not_yet_off_center"
            )
        elif empowerment_audit.status == "caution":
            moral_trajectory_target = "empowerment_safe_care"
            moral_trajectory_trigger = "empowerment_caution_detected"
            moral_trajectory_notes.append(
                "empowerment_caution_keeps_moral_line_under_supervised_watch"
            )
        else:
            moral_trajectory_target = "steady_progress_care"
            moral_trajectory_trigger = "moral_tension_watch"
            moral_trajectory_notes.append(
                "moral_tension_is_present_without_full_recentering"
            )
    else:
        moral_trajectory_status = "stable"
        moral_trajectory_target = "steady_progress_care"
        moral_trajectory_trigger = "moral_line_stable"
        moral_trajectory_notes.append(
            "moral_line_is_holding_stable_under_current_relational_constraints"
        )

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
        context_frame.attention in {"focused", "high"}
        and "low_cognitive_load" in user_preferences
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

    if (
        filtered_recall_count > 0
        or (
            recall_count > 0
            and len(user_model_evolution_notes) >= 2
            and user_model_shift_signal != "delivery_preference_reinforced"
        )
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
            user_model_trajectory_notes.append("user_model_revision_requires_recentered_preferences")
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

    expectation_calibration_notes: list[str] = []
    if relationship_state.dependency_risk == "elevated":
        if knowledge_boundary_decision.decision == "support_with_boundary":
            expectation_calibration_status = "revise"
            expectation_calibration_target = "bounded_relational_support"
            expectation_calibration_trigger = "relational_boundary_required"
            expectation_calibration_notes.append(
                "dependency_pressure_requires_relational_expectation_reset"
            )
        else:
            expectation_calibration_status = "revise"
            expectation_calibration_target = "agency_preserving_support"
            expectation_calibration_trigger = "dependency_pressure_detected"
            expectation_calibration_notes.append(
                "dependency_pressure_requires_agency_preserving_expectation_reset"
            )
    elif knowledge_boundary_decision.decision == "answer_with_uncertainty":
        if confidence_assessment.level == "low":
            expectation_calibration_status = "revise"
            expectation_calibration_target = "uncertainty_honest_support"
            expectation_calibration_trigger = "certainty_request_requires_reset"
            expectation_calibration_notes.append(
                "certainty_request_requires_explicit_expectation_reset"
            )
        else:
            expectation_calibration_status = "watch"
            expectation_calibration_target = "uncertainty_honest_support"
            expectation_calibration_trigger = "uncertainty_disclosure_required"
            expectation_calibration_notes.append(
                "uncertainty_disclosure_keeps_expectation_line_under_watch"
            )
    elif confidence_assessment.needs_clarification:
        expectation_calibration_status = "watch"
        expectation_calibration_target = "context_before_commitment"
        expectation_calibration_trigger = "clarification_required"
        expectation_calibration_notes.append(
            "missing_context_requires_context_first_expectation"
        )
    elif repair_assessment.repair_needed and policy_gate.selected_path == "repair_first":
        expectation_calibration_status = "watch"
        expectation_calibration_target = "low_pressure_repair_support"
        expectation_calibration_trigger = "repair_pressure_requires_soft_expectation"
        expectation_calibration_notes.append(
            "repair_pressure_requires_lower_pressure_relational_expectation"
        )
    elif (
        response_sequence_plan is not None
        and response_sequence_plan.mode == "two_part_sequence"
    ):
        expectation_calibration_status = "watch"
        expectation_calibration_target = "segmented_progress_expectation"
        expectation_calibration_trigger = "segmented_delivery_active"
        expectation_calibration_notes.append(
            "segmented_delivery_signals_expectation_should_stay_stepwise"
        )
    else:
        expectation_calibration_status = "pass"
        expectation_calibration_target = "bounded_progress_expectation"
        expectation_calibration_trigger = "expectation_line_stable"

    expectation_calibration_trajectory_notes: list[str] = []
    if expectation_calibration_status == "revise":
        expectation_calibration_trajectory_status = "reset"
        if expectation_calibration_trigger == "relational_boundary_required":
            expectation_calibration_trajectory_target = "bounded_relational_support"
            expectation_calibration_trajectory_trigger = (
                "relational_boundary_expectation_reset"
            )
            expectation_calibration_trajectory_notes.append(
                "relational_boundary_keeps_expectation_line_in_reset_mode"
            )
        elif expectation_calibration_trigger == "dependency_pressure_detected":
            expectation_calibration_trajectory_target = "agency_preserving_support"
            expectation_calibration_trajectory_trigger = (
                "dependency_expectation_reset"
            )
            expectation_calibration_trajectory_notes.append(
                "dependency_pressure_keeps_expectation_line_in_reset_mode"
            )
        elif expectation_calibration_trigger == "certainty_request_requires_reset":
            expectation_calibration_trajectory_target = "uncertainty_honest_support"
            expectation_calibration_trajectory_trigger = (
                "uncertainty_expectation_reset"
            )
            expectation_calibration_trajectory_notes.append(
                "certainty_request_keeps_expectation_line_in_reset_mode"
            )
        else:
            expectation_calibration_trajectory_target = (
                expectation_calibration_target
            )
            expectation_calibration_trajectory_trigger = "expectation_reset_required"
            expectation_calibration_trajectory_notes.append(
                "expectation_line_requires_active_reset"
            )
    elif expectation_calibration_status == "watch":
        expectation_calibration_trajectory_status = "watch"
        if expectation_calibration_trigger == "uncertainty_disclosure_required":
            expectation_calibration_trajectory_target = "uncertainty_honest_support"
            expectation_calibration_trajectory_trigger = (
                "uncertainty_expectation_watch"
            )
            expectation_calibration_trajectory_notes.append(
                "uncertainty_disclosure_keeps_expectation_line_under_watch"
            )
        elif expectation_calibration_trigger == "clarification_required":
            expectation_calibration_trajectory_target = "context_before_commitment"
            expectation_calibration_trajectory_trigger = (
                "clarification_expectation_watch"
            )
            expectation_calibration_trajectory_notes.append(
                "clarification_need_keeps_expectation_line_under_watch"
            )
        elif (
            expectation_calibration_trigger
            == "repair_pressure_requires_soft_expectation"
        ):
            expectation_calibration_trajectory_target = "low_pressure_repair_support"
            expectation_calibration_trajectory_trigger = "repair_expectation_watch"
            expectation_calibration_trajectory_notes.append(
                "repair_pressure_keeps_expectation_line_under_watch"
            )
        elif expectation_calibration_trigger == "segmented_delivery_active":
            expectation_calibration_trajectory_target = (
                "segmented_progress_expectation"
            )
            expectation_calibration_trajectory_trigger = (
                "segmented_expectation_watch"
            )
            expectation_calibration_trajectory_notes.append(
                "segmented_delivery_keeps_expectation_line_under_watch"
            )
        else:
            expectation_calibration_trajectory_target = (
                "bounded_progress_expectation"
            )
            expectation_calibration_trajectory_trigger = "expectation_watch_active"
            expectation_calibration_trajectory_notes.append(
                "expectation_line_is_shifting_without_full_reset"
            )
    else:
        expectation_calibration_trajectory_status = "stable"
        expectation_calibration_trajectory_target = "bounded_progress_expectation"
        expectation_calibration_trajectory_trigger = "expectation_line_stable"
        expectation_calibration_trajectory_notes.append(
            "expectation_line_is_holding_stable"
        )

    dependency_governance_notes: list[str] = []
    if relationship_state.dependency_risk == "elevated":
        dependency_governance_status = "revise"
        if knowledge_boundary_decision.decision == "support_with_boundary":
            dependency_governance_target = "bounded_relational_support"
            dependency_governance_trigger = "relational_boundary_required"
            dependency_governance_notes.append(
                "dependency_pressure_requires_explicit_relational_boundary"
            )
        elif repair_assessment.repair_needed:
            dependency_governance_target = "repair_before_reliance"
            dependency_governance_trigger = "repair_before_reliance_required"
            dependency_governance_notes.append(
                "dependency_pressure_and_repair_load_require_repair_before_reliance"
            )
        else:
            dependency_governance_target = "agency_preserving_support"
            dependency_governance_trigger = "dependency_pressure_detected"
            dependency_governance_notes.append(
                "dependency_pressure_requires_agency_preserving_support"
            )
    elif expectation_calibration_status == "revise":
        dependency_governance_status = "watch"
        dependency_governance_target = expectation_calibration_target
        if expectation_calibration_trigger == "certainty_request_requires_reset":
            dependency_governance_trigger = "certainty_support_boundary_watch"
            dependency_governance_notes.append(
                "certainty_requests_keep_dependency_line_under_support_boundary_watch"
            )
        else:
            dependency_governance_trigger = "expectation_dependency_watch"
            dependency_governance_notes.append(
                "expectation_reset_signals_dependency_line_needs_watch"
            )
    elif (
        expectation_calibration_status == "watch"
        and expectation_calibration_target
        in {
            "low_pressure_repair_support",
            "context_before_commitment",
            "uncertainty_honest_support",
        }
    ):
        dependency_governance_status = "watch"
        dependency_governance_target = expectation_calibration_target
        dependency_governance_trigger = "expectation_support_watch"
        dependency_governance_notes.append(
            "expectation_watch_keeps_dependency_line_under_observation"
        )
    elif emotional_debt_status in {"watch", "elevated"} and repair_assessment.repair_needed:
        dependency_governance_status = "watch"
        dependency_governance_target = "repair_before_reliance"
        dependency_governance_trigger = "repair_load_dependency_watch"
        dependency_governance_notes.append(
            "repair_load_and_relational_debt_keep_dependency_line_under_watch"
        )
    else:
        dependency_governance_status = "pass"
        dependency_governance_target = "steady_low_dependency_support"
        dependency_governance_trigger = "dependency_line_stable"

    dependency_governance_trajectory_notes: list[str] = []
    if dependency_governance_status == "revise":
        dependency_governance_trajectory_status = "recenter"
        if dependency_governance_trigger == "relational_boundary_required":
            dependency_governance_trajectory_target = "bounded_relational_support"
            dependency_governance_trajectory_trigger = (
                "relational_boundary_dependency_recenter"
            )
            dependency_governance_trajectory_notes.append(
                "relational_boundary_keeps_dependency_line_in_recenter_mode"
            )
        elif dependency_governance_trigger == "repair_before_reliance_required":
            dependency_governance_trajectory_target = "repair_before_reliance"
            dependency_governance_trajectory_trigger = (
                "repair_before_reliance_dependency_recenter"
            )
            dependency_governance_trajectory_notes.append(
                "repair_load_keeps_dependency_line_recentered_toward_repair_first_support"
            )
        else:
            dependency_governance_trajectory_target = "agency_preserving_support"
            dependency_governance_trajectory_trigger = "dependency_recenter_required"
            dependency_governance_trajectory_notes.append(
                "dependency_pressure_keeps_dependency_line_in_recenter_mode"
            )
    elif dependency_governance_status == "watch":
        dependency_governance_trajectory_status = "watch"
        if dependency_governance_trigger == "growth_rebalance_required":
            dependency_governance_trajectory_target = "steady_low_dependency_support"
            dependency_governance_trajectory_trigger = "growth_dependency_watch"
            dependency_governance_trajectory_notes.append(
                "growth_rebalancing_keeps_dependency_line_under_watch"
            )
        elif dependency_governance_trigger == "repair_load_dependency_watch":
            dependency_governance_trajectory_target = "repair_before_reliance"
            dependency_governance_trajectory_trigger = "repair_dependency_watch"
            dependency_governance_trajectory_notes.append(
                "repair_load_keeps_dependency_line_under_watch"
            )
        elif dependency_governance_trigger == "certainty_support_boundary_watch":
            dependency_governance_trajectory_target = "uncertainty_honest_support"
            dependency_governance_trajectory_trigger = "certainty_dependency_watch"
            dependency_governance_trajectory_notes.append(
                "certainty_pressure_keeps_dependency_line_under_watch"
            )
        elif dependency_governance_target == "context_before_commitment":
            dependency_governance_trajectory_target = "context_before_commitment"
            dependency_governance_trajectory_trigger = "clarification_dependency_watch"
            dependency_governance_trajectory_notes.append(
                "clarification_need_keeps_dependency_line_under_watch"
            )
        else:
            dependency_governance_trajectory_target = dependency_governance_target
            dependency_governance_trajectory_trigger = "dependency_watch_active"
            dependency_governance_trajectory_notes.append(
                "dependency_line_is_shifting_without_full_recenter"
            )
    else:
        dependency_governance_trajectory_status = "stable"
        dependency_governance_trajectory_target = "steady_low_dependency_support"
        dependency_governance_trajectory_trigger = "dependency_governance_stable"
        dependency_governance_trajectory_notes.append(
            "dependency_line_is_holding_stable_and_low_pressure"
        )

    autonomy_governance_notes: list[str] = []
    if relationship_state.dependency_risk == "elevated":
        autonomy_governance_status = "revise"
        if knowledge_boundary_decision.decision == "support_with_boundary":
            autonomy_governance_target = "explicit_autonomy_boundary_support"
            autonomy_governance_trigger = "dependency_boundary_autonomy_reset"
            autonomy_governance_notes.append(
                "dependency_pressure_requires_visible_autonomy_and_boundary_support"
            )
        else:
            autonomy_governance_target = "explicit_autonomy_support"
            autonomy_governance_trigger = "dependency_autonomy_reset"
            autonomy_governance_notes.append(
                "dependency_pressure_requires_explicit_autonomy_reset"
            )
    elif repair_assessment.repair_needed and policy_gate.selected_path == "repair_first":
        autonomy_governance_status = "watch"
        autonomy_governance_target = "repair_with_user_space"
        autonomy_governance_trigger = "repair_pressure_autonomy_watch"
        autonomy_governance_notes.append(
            "repair_pressure_requires_more_user_space_and_lower_push"
        )
    elif confidence_assessment.needs_clarification:
        autonomy_governance_status = "watch"
        autonomy_governance_target = "context_before_commitment"
        autonomy_governance_trigger = "clarification_autonomy_watch"
        autonomy_governance_notes.append(
            "clarification_need_requires_context_first_autonomy_posture"
        )
    elif knowledge_boundary_decision.should_disclose_uncertainty:
        autonomy_governance_status = "watch"
        autonomy_governance_target = "uncertainty_with_opt_out"
        autonomy_governance_trigger = "uncertainty_autonomy_watch"
        autonomy_governance_notes.append(
            "uncertainty_disclosure_requires_explicit_opt_out_space"
        )
    elif (
        response_sequence_plan is not None
        and response_sequence_plan.mode == "two_part_sequence"
    ):
        autonomy_governance_status = "watch"
        autonomy_governance_target = "segmented_with_user_space"
        autonomy_governance_trigger = "segmented_autonomy_watch"
        autonomy_governance_notes.append(
            "segmented_delivery_requires_explicit_spacing_and_user_space"
        )
    else:
        autonomy_governance_status = "pass"
        autonomy_governance_target = "steady_explicit_autonomy"
        autonomy_governance_trigger = "autonomy_line_stable"

    autonomy_governance_trajectory_notes: list[str] = []
    if autonomy_governance_status == "revise":
        autonomy_governance_trajectory_status = "recenter"
        if autonomy_governance_trigger == "dependency_boundary_autonomy_reset":
            autonomy_governance_trajectory_target = (
                "explicit_autonomy_boundary_support"
            )
            autonomy_governance_trajectory_trigger = (
                "boundary_autonomy_recenter"
            )
            autonomy_governance_trajectory_notes.append(
                "boundary-sensitive dependency pressure keeps autonomy line in recenter mode"
            )
        else:
            autonomy_governance_trajectory_target = "explicit_autonomy_support"
            autonomy_governance_trajectory_trigger = "autonomy_recenter_required"
            autonomy_governance_trajectory_notes.append(
                "dependency pressure keeps autonomy line in recenter mode"
            )
    elif autonomy_governance_status == "watch":
        autonomy_governance_trajectory_status = "watch"
        if autonomy_governance_trigger == "repair_pressure_autonomy_watch":
            autonomy_governance_trajectory_target = "repair_with_user_space"
            autonomy_governance_trajectory_trigger = "repair_autonomy_watch"
            autonomy_governance_trajectory_notes.append(
                "repair pressure keeps autonomy line under watch"
            )
        elif autonomy_governance_trigger == "clarification_autonomy_watch":
            autonomy_governance_trajectory_target = "context_before_commitment"
            autonomy_governance_trajectory_trigger = "clarification_autonomy_watch"
            autonomy_governance_trajectory_notes.append(
                "clarification keeps autonomy line under watch"
            )
        elif autonomy_governance_trigger == "uncertainty_autonomy_watch":
            autonomy_governance_trajectory_target = "uncertainty_with_opt_out"
            autonomy_governance_trajectory_trigger = "uncertainty_autonomy_watch"
            autonomy_governance_trajectory_notes.append(
                "uncertainty keeps autonomy line under watch"
            )
        elif autonomy_governance_trigger == "segmented_autonomy_watch":
            autonomy_governance_trajectory_target = "segmented_with_user_space"
            autonomy_governance_trajectory_trigger = "segmented_autonomy_watch"
            autonomy_governance_trajectory_notes.append(
                "segmented delivery keeps autonomy line under watch"
            )
        else:
            autonomy_governance_trajectory_target = autonomy_governance_target
            autonomy_governance_trajectory_trigger = "autonomy_watch_active"
            autonomy_governance_trajectory_notes.append(
                "autonomy line is shifting without full recenter"
            )
    else:
        autonomy_governance_trajectory_status = "stable"
        autonomy_governance_trajectory_target = "steady_explicit_autonomy"
        autonomy_governance_trajectory_trigger = "autonomy_governance_stable"
        autonomy_governance_trajectory_notes.append(
            "autonomy line is holding stable and explicit"
        )

    boundary_governance_notes: list[str] = []
    if policy_gate.red_line_status == "blocked":
        boundary_governance_status = "revise"
        boundary_governance_target = "hard_boundary_containment"
        boundary_governance_trigger = "policy_gate_blocked"
        boundary_governance_notes.append(
            "blocked_policy_gate_requires_hard_boundary_containment"
        )
    elif (
        policy_gate.red_line_status == "boundary_sensitive"
        or knowledge_boundary_decision.decision == "support_with_boundary"
    ):
        boundary_governance_status = "revise"
        boundary_governance_target = "explicit_boundary_support"
        if policy_gate.red_line_status == "boundary_sensitive":
            boundary_governance_trigger = "boundary_sensitive_gate_active"
            boundary_governance_notes.append(
                "boundary_sensitive_gate_requires_explicit_boundary_support"
            )
        else:
            boundary_governance_trigger = "support_with_boundary_required"
            boundary_governance_notes.append(
                "knowledge_boundary_requires_explicit_boundary_support"
            )
    elif relationship_state.dependency_risk == "elevated":
        boundary_governance_status = "watch"
        boundary_governance_target = "dependency_safe_boundary_support"
        boundary_governance_trigger = "dependency_boundary_watch"
        boundary_governance_notes.append(
            "dependency_pressure_keeps_boundary_line_under_watch"
        )
    elif knowledge_boundary_decision.should_disclose_uncertainty:
        boundary_governance_status = "watch"
        boundary_governance_target = "uncertainty_boundary_support"
        boundary_governance_trigger = "uncertainty_boundary_watch"
        boundary_governance_notes.append(
            "uncertainty_disclosure_keeps_boundary_line_under_watch"
        )
    elif confidence_assessment.needs_clarification:
        boundary_governance_status = "watch"
        boundary_governance_target = "clarify_before_boundary_commitment"
        boundary_governance_trigger = "clarification_boundary_watch"
        boundary_governance_notes.append(
            "clarification_need_keeps_boundary_line_context_first"
        )
    elif repair_assessment.repair_needed and policy_gate.selected_path == "repair_first":
        boundary_governance_status = "watch"
        boundary_governance_target = "repair_first_boundary_softening"
        boundary_governance_trigger = "repair_boundary_watch"
        boundary_governance_notes.append(
            "repair_pressure_requires_boundary_softening_without_boundary_loss"
        )
    else:
        boundary_governance_status = "pass"
        boundary_governance_target = "steady_clear_boundary_support"
        boundary_governance_trigger = "boundary_line_stable"

    boundary_governance_trajectory_notes: list[str] = []
    if boundary_governance_status == "revise":
        boundary_governance_trajectory_status = "recenter"
        if boundary_governance_trigger == "policy_gate_blocked":
            boundary_governance_trajectory_target = "hard_boundary_containment"
            boundary_governance_trajectory_trigger = "blocked_boundary_recenter"
            boundary_governance_trajectory_notes.append(
                "blocked_policy_gate_keeps_boundary_line_in_recenter_mode"
            )
        else:
            boundary_governance_trajectory_target = "explicit_boundary_support"
            boundary_governance_trajectory_trigger = "boundary_support_recenter"
            boundary_governance_trajectory_notes.append(
                "boundary_sensitive_conditions_keep_boundary_line_in_recenter_mode"
            )
    elif boundary_governance_status == "watch":
        boundary_governance_trajectory_status = "watch"
        if boundary_governance_trigger == "dependency_boundary_watch":
            boundary_governance_trajectory_target = (
                "dependency_safe_boundary_support"
            )
            boundary_governance_trajectory_trigger = "dependency_boundary_watch"
            boundary_governance_trajectory_notes.append(
                "dependency_pressure_keeps_boundary_line_under_watch"
            )
        elif boundary_governance_trigger == "uncertainty_boundary_watch":
            boundary_governance_trajectory_target = "uncertainty_boundary_support"
            boundary_governance_trajectory_trigger = "uncertainty_boundary_watch"
            boundary_governance_trajectory_notes.append(
                "uncertainty_keeps_boundary_line_under_watch"
            )
        elif boundary_governance_trigger == "clarification_boundary_watch":
            boundary_governance_trajectory_target = (
                "clarify_before_boundary_commitment"
            )
            boundary_governance_trajectory_trigger = (
                "clarification_boundary_watch"
            )
            boundary_governance_trajectory_notes.append(
                "clarification_keeps_boundary_line_under_watch"
            )
        elif boundary_governance_trigger == "repair_boundary_watch":
            boundary_governance_trajectory_target = (
                "repair_first_boundary_softening"
            )
            boundary_governance_trajectory_trigger = "repair_boundary_watch"
            boundary_governance_trajectory_notes.append(
                "repair_pressure_keeps_boundary_line_under_watch"
            )
        else:
            boundary_governance_trajectory_target = boundary_governance_target
            boundary_governance_trajectory_trigger = "boundary_watch_active"
            boundary_governance_trajectory_notes.append(
                "boundary_line_is_shifting_without_full_recenter"
            )
    else:
        boundary_governance_trajectory_status = "stable"
        boundary_governance_trajectory_target = "steady_clear_boundary_support"
        boundary_governance_trajectory_trigger = "boundary_governance_stable"
        boundary_governance_trajectory_notes.append(
            "boundary_line_is_holding_stable_and_clear"
        )

    support_governance_notes: list[str] = []
    if (
        dependency_governance_status == "revise"
        or autonomy_governance_status == "revise"
        or boundary_governance_status == "revise"
    ):
        support_governance_status = "revise"
        if dependency_governance_status == "revise":
            support_governance_target = "agency_preserving_bounded_support"
            support_governance_trigger = "dependency_support_recenter"
            support_governance_notes.append(
                "dependency_pressure_requires_support_line_recenter"
            )
        elif boundary_governance_status == "revise":
            support_governance_target = "explicit_boundary_scaffold"
            support_governance_trigger = "boundary_support_recenter"
            support_governance_notes.append(
                "boundary_pressure_requires_support_line_recenter"
            )
        else:
            support_governance_target = "explicit_user_led_support"
            support_governance_trigger = "autonomy_support_recenter"
            support_governance_notes.append(
                "autonomy_pressure_requires_more_user_led_support"
            )
    elif (
        dependency_governance_status == "watch"
        or autonomy_governance_status == "watch"
        or boundary_governance_status == "watch"
        or expectation_calibration_status == "watch"
    ):
        support_governance_status = "watch"
        if repair_assessment.repair_needed and policy_gate.selected_path == "repair_first":
            support_governance_target = "repair_first_low_pressure_support"
            support_governance_trigger = "repair_support_watch"
            support_governance_notes.append(
                "repair_pressure_keeps_support_line_low_pressure"
            )
        elif confidence_assessment.needs_clarification:
            support_governance_target = "context_before_support_commitment"
            support_governance_trigger = "clarification_support_watch"
            support_governance_notes.append(
                "clarification_need_keeps_support_line_context_first"
            )
        elif knowledge_boundary_decision.should_disclose_uncertainty:
            support_governance_target = "uncertainty_honest_support"
            support_governance_trigger = "uncertainty_support_watch"
            support_governance_notes.append(
                "uncertainty_keeps_support_line_under_watch"
            )
        elif (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        ):
            support_governance_target = "stepwise_segmented_support"
            support_governance_trigger = "segmented_support_watch"
            support_governance_notes.append(
                "segmented_delivery_keeps_support_line_stepwise"
            )
        else:
            support_governance_target = "steady_bounded_support"
            support_governance_trigger = "support_watch_active"
            support_governance_notes.append(
                "support_line_requires_active_watch_under_mixed_governance_signals"
            )
    else:
        support_governance_status = "pass"
        support_governance_target = "steady_bounded_support"
        support_governance_trigger = "support_line_stable"

    support_governance_trajectory_notes: list[str] = []
    if support_governance_status == "revise":
        support_governance_trajectory_status = "recenter"
        if support_governance_trigger == "dependency_support_recenter":
            support_governance_trajectory_target = (
                "agency_preserving_bounded_support"
            )
            support_governance_trajectory_trigger = (
                "dependency_support_recenter"
            )
            support_governance_trajectory_notes.append(
                "dependency_pressure_keeps_support_line_in_recenter_mode"
            )
        elif support_governance_trigger == "boundary_support_recenter":
            support_governance_trajectory_target = "explicit_boundary_scaffold"
            support_governance_trajectory_trigger = (
                "boundary_support_recenter"
            )
            support_governance_trajectory_notes.append(
                "boundary_pressure_keeps_support_line_in_recenter_mode"
            )
        else:
            support_governance_trajectory_target = "explicit_user_led_support"
            support_governance_trajectory_trigger = "autonomy_support_recenter"
            support_governance_trajectory_notes.append(
                "autonomy_pressure_keeps_support_line_in_recenter_mode"
            )
    elif support_governance_status == "watch":
        support_governance_trajectory_status = "watch"
        if support_governance_trigger == "repair_support_watch":
            support_governance_trajectory_target = (
                "repair_first_low_pressure_support"
            )
            support_governance_trajectory_trigger = "repair_support_watch"
            support_governance_trajectory_notes.append(
                "repair_pressure_keeps_support_line_under_watch"
            )
        elif support_governance_trigger == "clarification_support_watch":
            support_governance_trajectory_target = (
                "context_before_support_commitment"
            )
            support_governance_trajectory_trigger = (
                "clarification_support_watch"
            )
            support_governance_trajectory_notes.append(
                "clarification_keeps_support_line_under_watch"
            )
        elif support_governance_trigger == "uncertainty_support_watch":
            support_governance_trajectory_target = "uncertainty_honest_support"
            support_governance_trajectory_trigger = "uncertainty_support_watch"
            support_governance_trajectory_notes.append(
                "uncertainty_keeps_support_line_under_watch"
            )
        elif support_governance_trigger == "segmented_support_watch":
            support_governance_trajectory_target = "stepwise_segmented_support"
            support_governance_trajectory_trigger = "segmented_support_watch"
            support_governance_trajectory_notes.append(
                "segmented_delivery_keeps_support_line_under_watch"
            )
        else:
            support_governance_trajectory_target = support_governance_target
            support_governance_trajectory_trigger = "support_watch_active"
            support_governance_trajectory_notes.append(
                "support_line_is_shifting_without_full_recenter"
            )
    else:
        support_governance_trajectory_status = "stable"
        support_governance_trajectory_target = "steady_bounded_support"
        support_governance_trajectory_trigger = "support_governance_stable"
        support_governance_trajectory_notes.append(
            "support_line_is_holding_stable_and_bounded"
        )

    continuity_governance_notes: list[str] = []
    if filtered_recall_count > 0:
        continuity_governance_status = "revise"
        continuity_governance_target = "context_reanchor_continuity"
        continuity_governance_trigger = "filtered_recall_continuity_reset"
        continuity_governance_notes.append(
            "filtered_recall_requires_context_reanchor_before_continuity_deepens"
        )
    elif (
        user_model_evolution_status == "revise"
        and recall_count == 0
        and turn_index >= 3
    ):
        continuity_governance_status = "revise"
        continuity_governance_target = "memory_regrounded_continuity"
        continuity_governance_trigger = "underfit_memory_continuity_reset"
        continuity_governance_notes.append(
            "thin_memory_under_model_shift_requires_regrounded_continuity"
        )
    elif (
        support_governance_status == "watch"
        or confidence_assessment.needs_clarification
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
        or (recall_count == 0 and turn_index >= 2)
    ):
        continuity_governance_status = "watch"
        if support_governance_status == "watch":
            continuity_governance_target = "low_pressure_continuity"
            continuity_governance_trigger = "support_continuity_watch"
            continuity_governance_notes.append(
                "support_watch_keeps_continuity_line_low_pressure"
            )
        elif confidence_assessment.needs_clarification:
            continuity_governance_target = "clarified_context_continuity"
            continuity_governance_trigger = "clarification_continuity_watch"
            continuity_governance_notes.append(
                "clarification_need_keeps_continuity_line_context_first"
            )
        elif (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        ):
            continuity_governance_target = "stepwise_continuity"
            continuity_governance_trigger = "segmented_continuity_watch"
            continuity_governance_notes.append(
                "segmented_delivery_keeps_continuity_line_stepwise"
            )
        else:
            continuity_governance_target = "thin_context_continuity"
            continuity_governance_trigger = "thin_context_continuity_watch"
            continuity_governance_notes.append(
                "thin_recent_context_keeps_continuity_line_under_watch"
            )
    else:
        continuity_governance_status = "pass"
        continuity_governance_target = "steady_contextual_continuity"
        continuity_governance_trigger = "continuity_line_stable"

    continuity_governance_trajectory_notes: list[str] = []
    if continuity_governance_status == "revise":
        continuity_governance_trajectory_status = "recenter"
        if continuity_governance_trigger == "filtered_recall_continuity_reset":
            continuity_governance_trajectory_target = "context_reanchor_continuity"
            continuity_governance_trajectory_trigger = (
                "context_reanchor_recenter"
            )
            continuity_governance_trajectory_notes.append(
                "filtered_recall_keeps_continuity_line_in_context_reanchor_mode"
            )
        else:
            continuity_governance_trajectory_target = "memory_regrounded_continuity"
            continuity_governance_trajectory_trigger = "memory_reground_recenter"
            continuity_governance_trajectory_notes.append(
                "model_shift_with_thin_memory_keeps_continuity_line_in_reground_mode"
            )
    elif continuity_governance_status == "watch":
        continuity_governance_trajectory_status = "watch"
        if continuity_governance_trigger == "support_continuity_watch":
            continuity_governance_trajectory_target = "low_pressure_continuity"
            continuity_governance_trajectory_trigger = "support_continuity_watch"
            continuity_governance_trajectory_notes.append(
                "support_watch_keeps_continuity_line_under_low_pressure_watch"
            )
        elif continuity_governance_trigger == "clarification_continuity_watch":
            continuity_governance_trajectory_target = "clarified_context_continuity"
            continuity_governance_trajectory_trigger = (
                "clarification_continuity_watch"
            )
            continuity_governance_trajectory_notes.append(
                "clarification_keeps_continuity_line_under_watch"
            )
        elif continuity_governance_trigger == "segmented_continuity_watch":
            continuity_governance_trajectory_target = "stepwise_continuity"
            continuity_governance_trajectory_trigger = "segmented_continuity_watch"
            continuity_governance_trajectory_notes.append(
                "segmented_delivery_keeps_continuity_line_under_watch"
            )
        elif continuity_governance_trigger == "thin_context_continuity_watch":
            continuity_governance_trajectory_target = "thin_context_continuity"
            continuity_governance_trajectory_trigger = (
                "thin_context_continuity_watch"
            )
            continuity_governance_trajectory_notes.append(
                "thin_context_keeps_continuity_line_under_watch"
            )
        else:
            continuity_governance_trajectory_target = continuity_governance_target
            continuity_governance_trajectory_trigger = "continuity_watch_active"
            continuity_governance_trajectory_notes.append(
                "continuity_line_is_shifting_without_full_recenter"
            )
    else:
        continuity_governance_trajectory_status = "stable"
        continuity_governance_trajectory_target = "steady_contextual_continuity"
        continuity_governance_trajectory_trigger = "continuity_governance_stable"
        continuity_governance_trajectory_notes.append(
            "continuity_line_is_holding_stable_with_enough_context"
        )

    repair_governance_notes: list[str] = []
    if repair_assessment.repair_needed and repair_assessment.severity == "high":
        repair_governance_status = "revise"
        if repair_assessment.rupture_type == "boundary_risk":
            repair_governance_target = "boundary_safe_repair_containment"
            repair_governance_trigger = "boundary_repair_recenter"
            repair_governance_notes.append(
                "boundary_risk_requires_explicit_repair_containment"
            )
        elif repair_assessment.rupture_type == "attunement_gap":
            repair_governance_target = "attunement_repair_scaffold"
            repair_governance_trigger = "attunement_repair_recenter"
            repair_governance_notes.append(
                "high_severity_attunement_gap_requires_explicit_repair_scaffold"
            )
        else:
            repair_governance_target = "clarity_repair_scaffold"
            repair_governance_trigger = "clarity_repair_recenter"
            repair_governance_notes.append(
                "high_severity_clarity_gap_requires_explicit_repair_scaffold"
            )
    elif (
        repair_assessment.repair_needed
        or emotional_debt_status in {"watch", "elevated"}
        or continuity_governance_status == "watch"
        or support_governance_status == "watch"
    ):
        repair_governance_status = "watch"
        if emotional_debt_status in {"watch", "elevated"}:
            repair_governance_target = "debt_buffered_repair"
            repair_governance_trigger = "debt_repair_watch"
            repair_governance_notes.append(
                "emotional_debt_keeps_repair_line_buffered_and_low_pressure"
            )
        elif continuity_governance_status == "watch":
            repair_governance_target = "continuity_reanchor_repair"
            repair_governance_trigger = "continuity_repair_watch"
            repair_governance_notes.append(
                "continuity_watch_keeps_repair_line_context_reanchored"
            )
        elif support_governance_status == "watch":
            repair_governance_target = "low_pressure_repair_watch"
            repair_governance_trigger = "support_repair_watch"
            repair_governance_notes.append(
                "support_watch_keeps_repair_line_low_pressure"
            )
        elif repair_assessment.rupture_type == "attunement_gap":
            repair_governance_target = "attunement_repair_scaffold"
            repair_governance_trigger = "attunement_repair_watch"
            repair_governance_notes.append(
                "attunement_gap_keeps_repair_line_under_watch"
            )
        else:
            repair_governance_target = "clarity_repair_scaffold"
            repair_governance_trigger = "clarity_repair_watch"
            repair_governance_notes.append(
                "clarity_gap_keeps_repair_line_under_watch"
            )
    else:
        repair_governance_status = "pass"
        repair_governance_target = "steady_relational_repair_posture"
        repair_governance_trigger = "repair_line_stable"

    repair_governance_trajectory_notes: list[str] = []
    if repair_governance_status == "revise":
        repair_governance_trajectory_status = "recenter"
        if repair_governance_trigger == "boundary_repair_recenter":
            repair_governance_trajectory_target = (
                "boundary_safe_repair_containment"
            )
            repair_governance_trajectory_trigger = "boundary_repair_recenter"
            repair_governance_trajectory_notes.append(
                "boundary_risk_keeps_repair_line_in_recenter_mode"
            )
        elif repair_governance_trigger == "attunement_repair_recenter":
            repair_governance_trajectory_target = "attunement_repair_scaffold"
            repair_governance_trajectory_trigger = (
                "attunement_repair_recenter"
            )
            repair_governance_trajectory_notes.append(
                "attunement_rupture_keeps_repair_line_in_recenter_mode"
            )
        else:
            repair_governance_trajectory_target = "clarity_repair_scaffold"
            repair_governance_trajectory_trigger = "clarity_repair_recenter"
            repair_governance_trajectory_notes.append(
                "clarity_rupture_keeps_repair_line_in_recenter_mode"
            )
    elif repair_governance_status == "watch":
        repair_governance_trajectory_status = "watch"
        if repair_governance_trigger == "debt_repair_watch":
            repair_governance_trajectory_target = "debt_buffered_repair"
            repair_governance_trajectory_trigger = "debt_repair_watch"
            repair_governance_trajectory_notes.append(
                "debt_pressure_keeps_repair_line_under_watch"
            )
        elif repair_governance_trigger == "continuity_repair_watch":
            repair_governance_trajectory_target = "continuity_reanchor_repair"
            repair_governance_trajectory_trigger = "continuity_repair_watch"
            repair_governance_trajectory_notes.append(
                "continuity_watch_keeps_repair_line_under_reanchor_watch"
            )
        elif repair_governance_trigger == "support_repair_watch":
            repair_governance_trajectory_target = "low_pressure_repair_watch"
            repair_governance_trajectory_trigger = "support_repair_watch"
            repair_governance_trajectory_notes.append(
                "support_pressure_keeps_repair_line_under_watch"
            )
        elif repair_governance_trigger == "attunement_repair_watch":
            repair_governance_trajectory_target = "attunement_repair_scaffold"
            repair_governance_trajectory_trigger = "attunement_repair_watch"
            repair_governance_trajectory_notes.append(
                "attunement_gap_keeps_repair_line_under_watch"
            )
        elif repair_governance_trigger == "clarity_repair_watch":
            repair_governance_trajectory_target = "clarity_repair_scaffold"
            repair_governance_trajectory_trigger = "clarity_repair_watch"
            repair_governance_trajectory_notes.append(
                "clarity_gap_keeps_repair_line_under_watch"
            )
        else:
            repair_governance_trajectory_target = repair_governance_target
            repair_governance_trajectory_trigger = "repair_watch_active"
            repair_governance_trajectory_notes.append(
                "repair_line_is_shifting_without_full_recenter"
            )
    else:
        repair_governance_trajectory_status = "stable"
        repair_governance_trajectory_target = "steady_relational_repair_posture"
        repair_governance_trajectory_trigger = "repair_governance_stable"
        repair_governance_trajectory_notes.append(
            "repair_line_is_holding_stable_and_proportionate"
        )

    attunement_governance_notes: list[str] = []
    if (
        repair_assessment.repair_needed
        and repair_assessment.rupture_type == "attunement_gap"
        and repair_assessment.severity == "high"
    ):
        attunement_governance_status = "revise"
        attunement_governance_target = "attunement_repair_scaffold"
        attunement_governance_trigger = "attunement_gap_recenter"
        attunement_governance_notes.append(
            "high_severity_attunement_gap_requires_explicit_attunement_repair_scaffold"
        )
    elif continuity_governance_status == "revise":
        attunement_governance_status = "revise"
        attunement_governance_target = "reanchor_before_attunement_rebuild"
        attunement_governance_trigger = "continuity_attunement_recenter"
        attunement_governance_notes.append(
            "continuity_resets_require_reanchor_before_attunement_rebuild"
        )
    elif emotional_debt_status == "elevated":
        attunement_governance_status = "revise"
        attunement_governance_target = "decompression_before_attunement_push"
        attunement_governance_trigger = "debt_attunement_recenter"
        attunement_governance_notes.append(
            "elevated_debt_requires_decompression_before_attunement_push"
        )
    elif (
        repair_assessment.attunement_gap
        or repair_governance_status == "watch"
        or continuity_governance_status == "watch"
        or support_governance_status == "watch"
        or emotional_debt_status == "watch"
    ):
        attunement_governance_status = "watch"
        if repair_assessment.attunement_gap:
            attunement_governance_target = "attunement_repair_watch"
            attunement_governance_trigger = "attunement_gap_watch"
            attunement_governance_notes.append(
                "attunement_gap_keeps_attunement_line_in_repair_watch_mode"
            )
        elif continuity_governance_status == "watch":
            attunement_governance_target = "reanchored_attunement_watch"
            attunement_governance_trigger = "continuity_attunement_watch"
            attunement_governance_notes.append(
                "continuity_watch_keeps_attunement_line_reanchored"
            )
        elif repair_governance_status == "watch":
            attunement_governance_target = "repair_buffered_attunement_watch"
            attunement_governance_trigger = "repair_attunement_watch"
            attunement_governance_notes.append(
                "repair_watch_keeps_attunement_line_buffered_and_low_pressure"
            )
        elif support_governance_status == "watch":
            attunement_governance_target = "support_buffered_attunement_watch"
            attunement_governance_trigger = "support_attunement_watch"
            attunement_governance_notes.append(
                "support_watch_keeps_attunement_line_low_pressure_and_buffered"
            )
        else:
            attunement_governance_target = "debt_buffered_attunement_watch"
            attunement_governance_trigger = "debt_attunement_watch"
            attunement_governance_notes.append(
                "debt_pressure_keeps_attunement_line_low_pressure_and buffered"
            )
    else:
        attunement_governance_status = "pass"
        attunement_governance_target = "steady_relational_attunement"
        attunement_governance_trigger = "attunement_line_stable"

    attunement_governance_trajectory_notes: list[str] = []
    if attunement_governance_status == "revise":
        attunement_governance_trajectory_status = "recenter"
        if attunement_governance_trigger == "attunement_gap_recenter":
            attunement_governance_trajectory_target = "attunement_repair_scaffold"
            attunement_governance_trajectory_trigger = "attunement_gap_recenter"
            attunement_governance_trajectory_notes.append(
                "attunement_gap_keeps_attunement_line_in_repair_scaffold_mode"
            )
        elif attunement_governance_trigger == "continuity_attunement_recenter":
            attunement_governance_trajectory_target = (
                "reanchor_before_attunement_rebuild"
            )
            attunement_governance_trajectory_trigger = (
                "continuity_attunement_recenter"
            )
            attunement_governance_trajectory_notes.append(
                "continuity_resets_keep_attunement_line_in_reanchor_mode"
            )
        else:
            attunement_governance_trajectory_target = (
                "decompression_before_attunement_push"
            )
            attunement_governance_trajectory_trigger = "debt_attunement_recenter"
            attunement_governance_trajectory_notes.append(
                "debt_pressure_keeps_attunement_line_in_decompression_mode"
            )
    elif attunement_governance_status == "watch":
        attunement_governance_trajectory_status = "watch"
        if attunement_governance_trigger == "attunement_gap_watch":
            attunement_governance_trajectory_target = "attunement_repair_watch"
            attunement_governance_trajectory_trigger = "attunement_gap_watch"
            attunement_governance_trajectory_notes.append(
                "attunement_gap_keeps_attunement_line_under_repair_watch"
            )
        elif attunement_governance_trigger == "continuity_attunement_watch":
            attunement_governance_trajectory_target = "reanchored_attunement_watch"
            attunement_governance_trajectory_trigger = (
                "continuity_attunement_watch"
            )
            attunement_governance_trajectory_notes.append(
                "continuity_watch_keeps_attunement_line_under_reanchor_watch"
            )
        elif attunement_governance_trigger == "repair_attunement_watch":
            attunement_governance_trajectory_target = (
                "repair_buffered_attunement_watch"
            )
            attunement_governance_trajectory_trigger = "repair_attunement_watch"
            attunement_governance_trajectory_notes.append(
                "repair_watch_keeps_attunement_line_under_buffered_watch"
            )
        elif attunement_governance_trigger == "support_attunement_watch":
            attunement_governance_trajectory_target = (
                "support_buffered_attunement_watch"
            )
            attunement_governance_trajectory_trigger = "support_attunement_watch"
            attunement_governance_trajectory_notes.append(
                "support_watch_keeps_attunement_line_under_low_pressure_watch"
            )
        elif attunement_governance_trigger == "debt_attunement_watch":
            attunement_governance_trajectory_target = "debt_buffered_attunement_watch"
            attunement_governance_trajectory_trigger = "debt_attunement_watch"
            attunement_governance_trajectory_notes.append(
                "debt_pressure_keeps_attunement_line_under_buffered_watch"
            )
        else:
            attunement_governance_trajectory_target = attunement_governance_target
            attunement_governance_trajectory_trigger = "attunement_watch_active"
            attunement_governance_trajectory_notes.append(
                "attunement_line_is_shifting_without_full_recenter"
            )
    else:
        attunement_governance_trajectory_status = "stable"
        attunement_governance_trajectory_target = "steady_relational_attunement"
        attunement_governance_trajectory_trigger = "attunement_governance_stable"
        attunement_governance_trajectory_notes.append(
            "attunement_line_is_holding_stable_and_responsive"
        )

    trust_governance_notes: list[str] = []
    if (
        policy_gate.red_line_status == "blocked"
        or relationship_state.psychological_safety < 0.48
        or (
            repair_assessment.repair_needed
            and repair_assessment.severity == "high"
            and relationship_state.turbulence_risk == "elevated"
        )
    ):
        trust_governance_status = "revise"
        if policy_gate.red_line_status == "blocked":
            trust_governance_target = "boundary_safe_trust_containment"
            trust_governance_trigger = "boundary_trust_recenter"
            trust_governance_notes.append(
                "blocked_boundary_conditions_require_trust_containment_before_progress"
            )
        elif continuity_governance_status == "revise":
            trust_governance_target = "reanchor_before_trust_rebuild"
            trust_governance_trigger = "continuity_trust_recenter"
            trust_governance_notes.append(
                "continuity_resets_require_reanchor_before_trust_rebuild"
            )
        elif repair_assessment.repair_needed and repair_assessment.severity == "high":
            trust_governance_target = "repair_first_trust_rebuild"
            trust_governance_trigger = "repair_trust_recenter"
            trust_governance_notes.append(
                "high_severity_repair_pressure_requires_repair_first_trust_rebuild"
            )
        else:
            trust_governance_target = "decompression_before_trust_push"
            trust_governance_trigger = "debt_trust_recenter"
            trust_governance_notes.append(
                "low_safety_and_relational_load_require_decompression_before_trust_push"
            )
    elif (
        emotional_debt_status in {"watch", "elevated"}
        or relationship_state.turbulence_risk == "elevated"
        or relationship_state.psychological_safety < 0.72
        or repair_governance_status == "watch"
        or continuity_governance_status == "watch"
        or support_governance_status == "watch"
    ):
        trust_governance_status = "watch"
        if emotional_debt_status in {"watch", "elevated"}:
            trust_governance_target = "debt_buffered_trust_watch"
            trust_governance_trigger = "debt_trust_watch"
            trust_governance_notes.append(
                "debt_pressure_keeps_trust_line_low_pressure_and_buffered"
            )
        elif continuity_governance_status == "watch":
            trust_governance_target = "reanchored_trust_watch"
            trust_governance_trigger = "continuity_trust_watch"
            trust_governance_notes.append(
                "continuity_watch_keeps_trust_line_reanchored_before_deepening"
            )
        elif repair_governance_status == "watch":
            trust_governance_target = "repair_buffered_trust_watch"
            trust_governance_trigger = "repair_trust_watch"
            trust_governance_notes.append(
                "repair_watch_keeps_trust_line_buffered_and_low_pressure"
            )
        elif support_governance_status == "watch":
            trust_governance_target = "low_pressure_trust_watch"
            trust_governance_trigger = "support_trust_watch"
            trust_governance_notes.append(
                "support_watch_keeps_trust_line_low_pressure"
            )
        elif relationship_state.turbulence_risk == "elevated":
            trust_governance_target = "stabilizing_trust_watch"
            trust_governance_trigger = "turbulence_trust_watch"
            trust_governance_notes.append(
                "turbulence_keeps_trust_line_in_stabilizing_watch_mode"
            )
        else:
            trust_governance_target = "steady_low_pressure_trust"
            trust_governance_trigger = "trust_watch_active"
            trust_governance_notes.append(
                "trust_line_requires_watch_under_soft_safety_pressure"
            )
    else:
        trust_governance_status = "pass"
        trust_governance_target = "steady_mutual_trust_posture"
        trust_governance_trigger = "trust_line_stable"

    trust_governance_trajectory_notes: list[str] = []
    if trust_governance_status == "revise":
        trust_governance_trajectory_status = "recenter"
        if trust_governance_trigger == "boundary_trust_recenter":
            trust_governance_trajectory_target = "boundary_safe_trust_containment"
            trust_governance_trajectory_trigger = "boundary_trust_recenter"
            trust_governance_trajectory_notes.append(
                "boundary_lock_keeps_trust_line_in_containment_mode"
            )
        elif trust_governance_trigger == "continuity_trust_recenter":
            trust_governance_trajectory_target = "reanchor_before_trust_rebuild"
            trust_governance_trajectory_trigger = "continuity_trust_recenter"
            trust_governance_trajectory_notes.append(
                "continuity_resets_keep_trust_line_in_reanchor_mode"
            )
        elif trust_governance_trigger == "repair_trust_recenter":
            trust_governance_trajectory_target = "repair_first_trust_rebuild"
            trust_governance_trajectory_trigger = "repair_trust_recenter"
            trust_governance_trajectory_notes.append(
                "repair_pressure_keeps_trust_line_in_rebuild_mode"
            )
        else:
            trust_governance_trajectory_target = "decompression_before_trust_push"
            trust_governance_trajectory_trigger = "debt_trust_recenter"
            trust_governance_trajectory_notes.append(
                "relational_load_keeps_trust_line_in_decompression_mode"
            )
    elif trust_governance_status == "watch":
        trust_governance_trajectory_status = "watch"
        if trust_governance_trigger == "debt_trust_watch":
            trust_governance_trajectory_target = "debt_buffered_trust_watch"
            trust_governance_trajectory_trigger = "debt_trust_watch"
            trust_governance_trajectory_notes.append(
                "debt_pressure_keeps_trust_line_under_watch"
            )
        elif trust_governance_trigger == "continuity_trust_watch":
            trust_governance_trajectory_target = "reanchored_trust_watch"
            trust_governance_trajectory_trigger = "continuity_trust_watch"
            trust_governance_trajectory_notes.append(
                "continuity_watch_keeps_trust_line_under_reanchor_watch"
            )
        elif trust_governance_trigger == "repair_trust_watch":
            trust_governance_trajectory_target = "repair_buffered_trust_watch"
            trust_governance_trajectory_trigger = "repair_trust_watch"
            trust_governance_trajectory_notes.append(
                "repair_watch_keeps_trust_line_under_buffered_watch"
            )
        elif trust_governance_trigger == "support_trust_watch":
            trust_governance_trajectory_target = "low_pressure_trust_watch"
            trust_governance_trajectory_trigger = "support_trust_watch"
            trust_governance_trajectory_notes.append(
                "support_watch_keeps_trust_line_under_low_pressure_watch"
            )
        elif trust_governance_trigger == "turbulence_trust_watch":
            trust_governance_trajectory_target = "stabilizing_trust_watch"
            trust_governance_trajectory_trigger = "turbulence_trust_watch"
            trust_governance_trajectory_notes.append(
                "turbulence_keeps_trust_line_under_stabilizing_watch"
            )
        else:
            trust_governance_trajectory_target = trust_governance_target
            trust_governance_trajectory_trigger = "trust_watch_active"
            trust_governance_trajectory_notes.append(
                "trust_line_is_shifting_without_full_recenter"
            )
    else:
        trust_governance_trajectory_status = "stable"
        trust_governance_trajectory_target = "steady_mutual_trust_posture"
        trust_governance_trajectory_trigger = "trust_governance_stable"
        trust_governance_trajectory_notes.append(
            "trust_line_is_holding_stable_with_enough_relational_safety"
        )

    clarity_governance_notes: list[str] = []
    if (
        confidence_assessment.needs_clarification
        and filtered_recall_count > 0
    ):
        clarity_governance_status = "revise"
        clarity_governance_target = "reanchor_before_clarity_commitment"
        clarity_governance_trigger = "filtered_context_clarity_recenter"
        clarity_governance_notes.append(
            "filtered_recall_requires_reanchor_before_clarity_commitment"
        )
    elif (
        confidence_assessment.needs_clarification
        and knowledge_boundary_decision.should_disclose_uncertainty
    ):
        clarity_governance_status = "revise"
        clarity_governance_target = "uncertainty_first_clarity_scaffold"
        clarity_governance_trigger = "uncertainty_clarity_recenter"
        clarity_governance_notes.append(
            "uncertainty_and_clarification_pressure_require_explicit_clarity_scaffold"
        )
    elif (
        repair_assessment.repair_needed
        and repair_assessment.rupture_type == "clarity_gap"
    ):
        clarity_governance_status = "revise"
        clarity_governance_target = "repair_scaffolded_clarity"
        clarity_governance_trigger = "repair_clarity_recenter"
        clarity_governance_notes.append(
            "clarity_gap_requires_repair_scaffold_before_forward_clarity"
        )
    elif (
        confidence_assessment.needs_clarification
        or knowledge_boundary_decision.should_disclose_uncertainty
        or continuity_governance_status == "watch"
        or expectation_calibration_status == "watch"
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        clarity_governance_status = "watch"
        if confidence_assessment.needs_clarification:
            clarity_governance_target = "clarify_before_commitment"
            clarity_governance_trigger = "clarification_clarity_watch"
            clarity_governance_notes.append(
                "clarification_need_keeps_clarity_line_context_first"
            )
        elif knowledge_boundary_decision.should_disclose_uncertainty:
            clarity_governance_target = "uncertainty_buffered_clarity"
            clarity_governance_trigger = "uncertainty_clarity_watch"
            clarity_governance_notes.append(
                "uncertainty_disclosure_keeps_clarity_line_under_watch"
            )
        elif continuity_governance_status == "watch":
            clarity_governance_target = "reanchored_clarity_watch"
            clarity_governance_trigger = "continuity_clarity_watch"
            clarity_governance_notes.append(
                "continuity_watch_keeps_clarity_line_reanchored"
            )
        elif expectation_calibration_status == "watch":
            clarity_governance_target = "expectation_reset_clarity_watch"
            clarity_governance_trigger = "expectation_clarity_watch"
            clarity_governance_notes.append(
                "expectation_watch_keeps_clarity_line_explicit_and_bounded"
            )
        else:
            clarity_governance_target = "stepwise_clarity_watch"
            clarity_governance_trigger = "segmented_clarity_watch"
            clarity_governance_notes.append(
                "segmented_delivery_keeps_clarity_line_stepwise"
            )
    else:
        clarity_governance_status = "pass"
        clarity_governance_target = "steady_contextual_clarity"
        clarity_governance_trigger = "clarity_line_stable"

    clarity_governance_trajectory_notes: list[str] = []
    if clarity_governance_status == "revise":
        clarity_governance_trajectory_status = "recenter"
        if clarity_governance_trigger == "filtered_context_clarity_recenter":
            clarity_governance_trajectory_target = (
                "reanchor_before_clarity_commitment"
            )
            clarity_governance_trajectory_trigger = (
                "filtered_context_clarity_recenter"
            )
            clarity_governance_trajectory_notes.append(
                "filtered_context_keeps_clarity_line_in_reanchor_mode"
            )
        elif clarity_governance_trigger == "uncertainty_clarity_recenter":
            clarity_governance_trajectory_target = (
                "uncertainty_first_clarity_scaffold"
            )
            clarity_governance_trajectory_trigger = (
                "uncertainty_clarity_recenter"
            )
            clarity_governance_trajectory_notes.append(
                "uncertainty_and_clarification_keep_clarity_line_in_scaffold_mode"
            )
        else:
            clarity_governance_trajectory_target = "repair_scaffolded_clarity"
            clarity_governance_trajectory_trigger = "repair_clarity_recenter"
            clarity_governance_trajectory_notes.append(
                "clarity_rupture_keeps_clarity_line_in_repair_mode"
            )
    elif clarity_governance_status == "watch":
        clarity_governance_trajectory_status = "watch"
        if clarity_governance_trigger == "clarification_clarity_watch":
            clarity_governance_trajectory_target = "clarify_before_commitment"
            clarity_governance_trajectory_trigger = "clarification_clarity_watch"
            clarity_governance_trajectory_notes.append(
                "clarification_need_keeps_clarity_line_under_watch"
            )
        elif clarity_governance_trigger == "uncertainty_clarity_watch":
            clarity_governance_trajectory_target = "uncertainty_buffered_clarity"
            clarity_governance_trajectory_trigger = "uncertainty_clarity_watch"
            clarity_governance_trajectory_notes.append(
                "uncertainty_keeps_clarity_line_under_watch"
            )
        elif clarity_governance_trigger == "continuity_clarity_watch":
            clarity_governance_trajectory_target = "reanchored_clarity_watch"
            clarity_governance_trajectory_trigger = "continuity_clarity_watch"
            clarity_governance_trajectory_notes.append(
                "continuity_watch_keeps_clarity_line_under_reanchor_watch"
            )
        elif clarity_governance_trigger == "expectation_clarity_watch":
            clarity_governance_trajectory_target = "expectation_reset_clarity_watch"
            clarity_governance_trajectory_trigger = "expectation_clarity_watch"
            clarity_governance_trajectory_notes.append(
                "expectation_watch_keeps_clarity_line_under_watch"
            )
        elif clarity_governance_trigger == "segmented_clarity_watch":
            clarity_governance_trajectory_target = "stepwise_clarity_watch"
            clarity_governance_trajectory_trigger = "segmented_clarity_watch"
            clarity_governance_trajectory_notes.append(
                "segmented_delivery_keeps_clarity_line_under_watch"
            )
        else:
            clarity_governance_trajectory_target = clarity_governance_target
            clarity_governance_trajectory_trigger = "clarity_watch_active"
            clarity_governance_trajectory_notes.append(
                "clarity_line_is_shifting_without_full_recenter"
            )
    else:
        clarity_governance_trajectory_status = "stable"
        clarity_governance_trajectory_target = "steady_contextual_clarity"
        clarity_governance_trajectory_trigger = "clarity_governance_stable"
        clarity_governance_trajectory_notes.append(
            "clarity_line_is_holding_stable_with_enough_context"
        )

    growth_transition_watch_signal = (
        growth_stage in {"repairing", "stabilizing"}
        and relationship_state.psychological_safety < 0.78
    )

    pacing_governance_notes: list[str] = []
    if emotional_debt_status == "elevated":
        pacing_governance_status = "revise"
        pacing_governance_target = "decompression_first_pacing"
        pacing_governance_trigger = "debt_pacing_recenter"
        pacing_governance_notes.append(
            "elevated_debt_requires_decompression_before_forward_pacing"
        )
    elif repair_governance_status == "revise":
        pacing_governance_status = "revise"
        pacing_governance_target = "repair_first_pacing"
        pacing_governance_trigger = "repair_pacing_recenter"
        pacing_governance_notes.append(
            "repair_recenter_requires_slower_repair_first_pacing"
        )
    elif expectation_calibration_status == "revise":
        pacing_governance_status = "revise"
        pacing_governance_target = "expectation_reset_pacing"
        pacing_governance_trigger = "expectation_pacing_recenter"
        pacing_governance_notes.append(
            "expectation_reset_requires_explicitly_slower_pacing"
        )
    elif (
        emotional_debt_status == "watch"
        or trust_governance_status == "watch"
        or clarity_governance_status == "watch"
        or growth_transition_watch_signal
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        pacing_governance_status = "watch"
        if trust_governance_status == "watch":
            pacing_governance_target = "trust_buffered_pacing"
            pacing_governance_trigger = "trust_pacing_watch"
            pacing_governance_notes.append(
                "trust_watch_keeps_pacing_line_low_pressure"
            )
        elif clarity_governance_status == "watch":
            pacing_governance_target = "clarity_first_pacing"
            pacing_governance_trigger = "clarity_pacing_watch"
            pacing_governance_notes.append(
                "clarity_watch_keeps_pacing_line_context_first"
            )
        elif (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        ):
            pacing_governance_target = "segmented_low_pressure_pacing"
            pacing_governance_trigger = "segmented_pacing_watch"
            pacing_governance_notes.append(
                "segmented_delivery_keeps_pacing_line_stepwise"
            )
        elif growth_transition_watch_signal:
            pacing_governance_target = "steadying_transition_pacing"
            pacing_governance_trigger = "growth_pacing_watch"
            pacing_governance_notes.append(
                "growth_transition_watch_keeps_pacing_line_steadying"
            )
        else:
            pacing_governance_target = "debt_buffered_pacing"
            pacing_governance_trigger = "pacing_watch_active"
            pacing_governance_notes.append(
                "mixed_relational_pressure_keeps_pacing_line_under_watch"
            )
    else:
        pacing_governance_status = "pass"
        pacing_governance_target = "steady_relational_pacing"
        pacing_governance_trigger = "pacing_line_stable"

    pacing_governance_trajectory_notes: list[str] = []
    if pacing_governance_status == "revise":
        pacing_governance_trajectory_status = "recenter"
        if pacing_governance_trigger == "debt_pacing_recenter":
            pacing_governance_trajectory_target = "decompression_first_pacing"
            pacing_governance_trajectory_trigger = "debt_pacing_recenter"
            pacing_governance_trajectory_notes.append(
                "debt_pressure_keeps_pacing_line_in_decompression_mode"
            )
        elif pacing_governance_trigger == "repair_pacing_recenter":
            pacing_governance_trajectory_target = "repair_first_pacing"
            pacing_governance_trajectory_trigger = "repair_pacing_recenter"
            pacing_governance_trajectory_notes.append(
                "repair_pressure_keeps_pacing_line_in_repair_first_mode"
            )
        else:
            pacing_governance_trajectory_target = "expectation_reset_pacing"
            pacing_governance_trajectory_trigger = "expectation_pacing_recenter"
            pacing_governance_trajectory_notes.append(
                "expectation_reset_keeps_pacing_line_in_slower_reset_mode"
            )
    elif pacing_governance_status == "watch":
        pacing_governance_trajectory_status = "watch"
        if pacing_governance_trigger == "trust_pacing_watch":
            pacing_governance_trajectory_target = "trust_buffered_pacing"
            pacing_governance_trajectory_trigger = "trust_pacing_watch"
            pacing_governance_trajectory_notes.append(
                "trust_watch_keeps_pacing_line_under_buffered_watch"
            )
        elif pacing_governance_trigger == "clarity_pacing_watch":
            pacing_governance_trajectory_target = "clarity_first_pacing"
            pacing_governance_trajectory_trigger = "clarity_pacing_watch"
            pacing_governance_trajectory_notes.append(
                "clarity_watch_keeps_pacing_line_under_context_first_watch"
            )
        elif pacing_governance_trigger == "segmented_pacing_watch":
            pacing_governance_trajectory_target = "segmented_low_pressure_pacing"
            pacing_governance_trajectory_trigger = "segmented_pacing_watch"
            pacing_governance_trajectory_notes.append(
                "segmented_delivery_keeps_pacing_line_under_watch"
            )
        elif pacing_governance_trigger == "growth_pacing_watch":
            pacing_governance_trajectory_target = "steadying_transition_pacing"
            pacing_governance_trajectory_trigger = "growth_pacing_watch"
            pacing_governance_trajectory_notes.append(
                "growth_transition_watch_keeps_pacing_line_under_watch"
            )
        else:
            pacing_governance_trajectory_target = pacing_governance_target
            pacing_governance_trajectory_trigger = "pacing_watch_active"
            pacing_governance_trajectory_notes.append(
                "pacing_line_is_shifting_without_full_recenter"
            )
    else:
        pacing_governance_trajectory_status = "stable"
        pacing_governance_trajectory_target = "steady_relational_pacing"
        pacing_governance_trajectory_trigger = "pacing_governance_stable"
        pacing_governance_trajectory_notes.append(
            "pacing_line_is_holding_stable_and_proportionate"
        )

    commitment_governance_notes: list[str] = []
    if boundary_governance_status == "revise":
        commitment_governance_status = "revise"
        commitment_governance_target = "bounded_noncommitment_support"
        commitment_governance_trigger = "boundary_commitment_recenter"
        commitment_governance_notes.append(
            "boundary_recenter_requires_noncommitment_before_forward_motion"
        )
    elif expectation_calibration_status == "revise":
        commitment_governance_status = "revise"
        commitment_governance_target = "expectation_reset_before_commitment"
        commitment_governance_trigger = "expectation_commitment_recenter"
        commitment_governance_notes.append(
            "expectation_reset_requires_explicitly_lower_commitment_shape"
        )
    elif autonomy_governance_status == "revise":
        commitment_governance_status = "revise"
        commitment_governance_target = "explicit_user_led_noncommitment"
        commitment_governance_trigger = "autonomy_commitment_recenter"
        commitment_governance_notes.append(
            "autonomy_recenter_requires_user_led_noncommitment_support"
        )
    elif (
        confidence_assessment.needs_clarification
        and knowledge_boundary_decision.should_disclose_uncertainty
    ):
        commitment_governance_status = "revise"
        commitment_governance_target = "uncertainty_first_noncommitment"
        commitment_governance_trigger = "uncertainty_commitment_recenter"
        commitment_governance_notes.append(
            "uncertainty_and_clarification_require_noncommitment_before_forwarding"
        )
    elif (
        repair_assessment.repair_needed
        or confidence_assessment.needs_clarification
        or knowledge_boundary_decision.should_disclose_uncertainty
        or expectation_calibration_status == "watch"
        or boundary_governance_status == "watch"
        or autonomy_governance_status == "watch"
        or pacing_governance_status == "watch"
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        commitment_governance_status = "watch"
        if repair_assessment.repair_needed and policy_gate.selected_path == "repair_first":
            commitment_governance_target = "repair_buffered_commitment_watch"
            commitment_governance_trigger = "repair_commitment_watch"
            commitment_governance_notes.append(
                "repair_pressure_keeps_commitment_line_buffered_and_low_pressure"
            )
        elif confidence_assessment.needs_clarification:
            commitment_governance_target = "clarify_before_commitment_watch"
            commitment_governance_trigger = "clarification_commitment_watch"
            commitment_governance_notes.append(
                "clarification_need_keeps_commitment_line_context_first"
            )
        elif knowledge_boundary_decision.should_disclose_uncertainty:
            commitment_governance_target = "uncertainty_buffered_commitment_watch"
            commitment_governance_trigger = "uncertainty_commitment_watch"
            commitment_governance_notes.append(
                "uncertainty_keeps_commitment_line_low_certainty_and_bounded"
            )
        elif expectation_calibration_status == "watch":
            commitment_governance_target = "expectation_buffered_commitment_watch"
            commitment_governance_trigger = "expectation_commitment_watch"
            commitment_governance_notes.append(
                "expectation_watch_keeps_commitment_line_explicitly_bounded"
            )
        elif boundary_governance_status == "watch":
            commitment_governance_target = "bounded_commitment_watch"
            commitment_governance_trigger = "boundary_commitment_watch"
            commitment_governance_notes.append(
                "boundary_watch_keeps_commitment_line_soft_and_bounded"
            )
        elif autonomy_governance_status == "watch":
            commitment_governance_target = "user_led_commitment_watch"
            commitment_governance_trigger = "autonomy_commitment_watch"
            commitment_governance_notes.append(
                "autonomy_watch_keeps_commitment_line_user_led"
            )
        elif pacing_governance_status == "watch":
            commitment_governance_target = "slow_commitment_watch"
            commitment_governance_trigger = "pacing_commitment_watch"
            commitment_governance_notes.append(
                "pacing_watch_keeps_commitment_line_slow_and_incremental"
            )
        else:
            commitment_governance_target = "stepwise_commitment_watch"
            commitment_governance_trigger = "segmented_commitment_watch"
            commitment_governance_notes.append(
                "segmented_delivery_keeps_commitment_line_stepwise"
            )
    else:
        commitment_governance_status = "pass"
        commitment_governance_target = "steady_calibrated_commitment"
        commitment_governance_trigger = "commitment_line_stable"

    commitment_governance_trajectory_notes: list[str] = []
    if commitment_governance_status == "revise":
        commitment_governance_trajectory_status = "recenter"
        if commitment_governance_trigger == "boundary_commitment_recenter":
            commitment_governance_trajectory_target = "bounded_noncommitment_support"
            commitment_governance_trajectory_trigger = "boundary_commitment_recenter"
            commitment_governance_trajectory_notes.append(
                "boundary_pressure_keeps_commitment_line_in_noncommitment_mode"
            )
        elif commitment_governance_trigger == "expectation_commitment_recenter":
            commitment_governance_trajectory_target = (
                "expectation_reset_before_commitment"
            )
            commitment_governance_trajectory_trigger = (
                "expectation_commitment_recenter"
            )
            commitment_governance_trajectory_notes.append(
                "expectation_reset_keeps_commitment_line_in_reset_mode"
            )
        elif commitment_governance_trigger == "autonomy_commitment_recenter":
            commitment_governance_trajectory_target = (
                "explicit_user_led_noncommitment"
            )
            commitment_governance_trajectory_trigger = (
                "autonomy_commitment_recenter"
            )
            commitment_governance_trajectory_notes.append(
                "autonomy_pressure_keeps_commitment_line_in_user_led_mode"
            )
        else:
            commitment_governance_trajectory_target = "uncertainty_first_noncommitment"
            commitment_governance_trajectory_trigger = (
                "uncertainty_commitment_recenter"
            )
            commitment_governance_trajectory_notes.append(
                "uncertainty_pressure_keeps_commitment_line_in_noncommitment_mode"
            )
    elif commitment_governance_status == "watch":
        commitment_governance_trajectory_status = "watch"
        if commitment_governance_trigger == "repair_commitment_watch":
            commitment_governance_trajectory_target = (
                "repair_buffered_commitment_watch"
            )
            commitment_governance_trajectory_trigger = "repair_commitment_watch"
            commitment_governance_trajectory_notes.append(
                "repair_pressure_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "clarification_commitment_watch":
            commitment_governance_trajectory_target = (
                "clarify_before_commitment_watch"
            )
            commitment_governance_trajectory_trigger = (
                "clarification_commitment_watch"
            )
            commitment_governance_trajectory_notes.append(
                "clarification_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "uncertainty_commitment_watch":
            commitment_governance_trajectory_target = (
                "uncertainty_buffered_commitment_watch"
            )
            commitment_governance_trajectory_trigger = (
                "uncertainty_commitment_watch"
            )
            commitment_governance_trajectory_notes.append(
                "uncertainty_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "expectation_commitment_watch":
            commitment_governance_trajectory_target = (
                "expectation_buffered_commitment_watch"
            )
            commitment_governance_trajectory_trigger = (
                "expectation_commitment_watch"
            )
            commitment_governance_trajectory_notes.append(
                "expectation_watch_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "boundary_commitment_watch":
            commitment_governance_trajectory_target = "bounded_commitment_watch"
            commitment_governance_trajectory_trigger = "boundary_commitment_watch"
            commitment_governance_trajectory_notes.append(
                "boundary_watch_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "autonomy_commitment_watch":
            commitment_governance_trajectory_target = "user_led_commitment_watch"
            commitment_governance_trajectory_trigger = "autonomy_commitment_watch"
            commitment_governance_trajectory_notes.append(
                "autonomy_watch_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "pacing_commitment_watch":
            commitment_governance_trajectory_target = "slow_commitment_watch"
            commitment_governance_trajectory_trigger = "pacing_commitment_watch"
            commitment_governance_trajectory_notes.append(
                "pacing_watch_keeps_commitment_line_under_watch"
            )
        elif commitment_governance_trigger == "segmented_commitment_watch":
            commitment_governance_trajectory_target = "stepwise_commitment_watch"
            commitment_governance_trajectory_trigger = "segmented_commitment_watch"
            commitment_governance_trajectory_notes.append(
                "segmented_delivery_keeps_commitment_line_under_watch"
            )
        else:
            commitment_governance_trajectory_target = commitment_governance_target
            commitment_governance_trajectory_trigger = "commitment_watch_active"
            commitment_governance_trajectory_notes.append(
                "commitment_line_is_shifting_without_full_recenter"
            )
    else:
        commitment_governance_trajectory_status = "stable"
        commitment_governance_trajectory_target = "steady_calibrated_commitment"
        commitment_governance_trajectory_trigger = "commitment_governance_stable"
        commitment_governance_trajectory_notes.append(
            "commitment_line_is_holding_stable_and_calibrated"
        )

    disclosure_governance_notes: list[str] = []
    if filtered_recall_count > 0 and knowledge_boundary_decision.should_disclose_uncertainty:
        disclosure_governance_status = "revise"
        disclosure_governance_target = "reanchor_before_disclosure_commitment"
        disclosure_governance_trigger = "filtered_context_disclosure_recenter"
        disclosure_governance_notes.append(
            "filtered_context_requires_reanchor_before_disclosure_commitment"
        )
    elif boundary_governance_status == "revise":
        disclosure_governance_status = "revise"
        disclosure_governance_target = "boundary_safe_disclosure"
        disclosure_governance_trigger = "boundary_disclosure_recenter"
        disclosure_governance_notes.append(
            "boundary_recenter_requires_explicitly_safe_disclosure_posture"
        )
    elif (
        confidence_assessment.needs_clarification
        and knowledge_boundary_decision.should_disclose_uncertainty
    ):
        disclosure_governance_status = "revise"
        disclosure_governance_target = "explicit_uncertainty_disclosure"
        disclosure_governance_trigger = "uncertainty_disclosure_recenter"
        disclosure_governance_notes.append(
            "uncertainty_plus_clarification_require_explicit_disclosure_scaffold"
        )
    elif (
        confidence_assessment.needs_clarification
        or knowledge_boundary_decision.should_disclose_uncertainty
        or clarity_governance_status == "watch"
        or boundary_governance_status == "watch"
        or commitment_governance_status == "watch"
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        disclosure_governance_status = "watch"
        if confidence_assessment.needs_clarification:
            disclosure_governance_target = "clarify_before_disclosure_watch"
            disclosure_governance_trigger = "clarification_disclosure_watch"
            disclosure_governance_notes.append(
                "clarification_need_keeps_disclosure_line_context_first"
            )
        elif knowledge_boundary_decision.should_disclose_uncertainty:
            disclosure_governance_target = "uncertainty_buffered_disclosure_watch"
            disclosure_governance_trigger = "uncertainty_disclosure_watch"
            disclosure_governance_notes.append(
                "uncertainty_keeps_disclosure_line_explicit_and_buffered"
            )
        elif boundary_governance_status == "watch":
            disclosure_governance_target = "boundary_buffered_disclosure_watch"
            disclosure_governance_trigger = "boundary_disclosure_watch"
            disclosure_governance_notes.append(
                "boundary_watch_keeps_disclosure_line_bounded"
            )
        elif commitment_governance_status == "watch":
            disclosure_governance_target = "commitment_softened_disclosure_watch"
            disclosure_governance_trigger = "commitment_disclosure_watch"
            disclosure_governance_notes.append(
                "commitment_watch_keeps_disclosure_line_softened"
            )
        elif (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        ):
            disclosure_governance_target = "segmented_disclosure_watch"
            disclosure_governance_trigger = "segmented_disclosure_watch"
            disclosure_governance_notes.append(
                "segmented_delivery_keeps_disclosure_line_stepwise"
            )
        else:
            disclosure_governance_target = "clarity_buffered_disclosure_watch"
            disclosure_governance_trigger = "clarity_disclosure_watch"
            disclosure_governance_notes.append(
                "clarity_watch_keeps_disclosure_line_buffered"
            )
    else:
        disclosure_governance_status = "pass"
        disclosure_governance_target = "steady_transparent_disclosure"
        disclosure_governance_trigger = "disclosure_line_stable"

    disclosure_governance_trajectory_notes: list[str] = []
    if disclosure_governance_status == "revise":
        disclosure_governance_trajectory_status = "recenter"
        if disclosure_governance_trigger == "filtered_context_disclosure_recenter":
            disclosure_governance_trajectory_target = (
                "reanchor_before_disclosure_commitment"
            )
            disclosure_governance_trajectory_trigger = (
                "filtered_context_disclosure_recenter"
            )
            disclosure_governance_trajectory_notes.append(
                "filtered_context_keeps_disclosure_line_in_reanchor_mode"
            )
        elif disclosure_governance_trigger == "boundary_disclosure_recenter":
            disclosure_governance_trajectory_target = "boundary_safe_disclosure"
            disclosure_governance_trajectory_trigger = "boundary_disclosure_recenter"
            disclosure_governance_trajectory_notes.append(
                "boundary_pressure_keeps_disclosure_line_in_safe_mode"
            )
        else:
            disclosure_governance_trajectory_target = "explicit_uncertainty_disclosure"
            disclosure_governance_trajectory_trigger = (
                "uncertainty_disclosure_recenter"
            )
            disclosure_governance_trajectory_notes.append(
                "uncertainty_pressure_keeps_disclosure_line_in_scaffold_mode"
            )
    elif disclosure_governance_status == "watch":
        disclosure_governance_trajectory_status = "watch"
        if disclosure_governance_trigger == "clarification_disclosure_watch":
            disclosure_governance_trajectory_target = (
                "clarify_before_disclosure_watch"
            )
            disclosure_governance_trajectory_trigger = (
                "clarification_disclosure_watch"
            )
            disclosure_governance_trajectory_notes.append(
                "clarification_keeps_disclosure_line_under_watch"
            )
        elif disclosure_governance_trigger == "uncertainty_disclosure_watch":
            disclosure_governance_trajectory_target = (
                "uncertainty_buffered_disclosure_watch"
            )
            disclosure_governance_trajectory_trigger = (
                "uncertainty_disclosure_watch"
            )
            disclosure_governance_trajectory_notes.append(
                "uncertainty_keeps_disclosure_line_under_watch"
            )
        elif disclosure_governance_trigger == "boundary_disclosure_watch":
            disclosure_governance_trajectory_target = (
                "boundary_buffered_disclosure_watch"
            )
            disclosure_governance_trajectory_trigger = "boundary_disclosure_watch"
            disclosure_governance_trajectory_notes.append(
                "boundary_watch_keeps_disclosure_line_under_watch"
            )
        elif disclosure_governance_trigger == "commitment_disclosure_watch":
            disclosure_governance_trajectory_target = (
                "commitment_softened_disclosure_watch"
            )
            disclosure_governance_trajectory_trigger = (
                "commitment_disclosure_watch"
            )
            disclosure_governance_trajectory_notes.append(
                "commitment_watch_keeps_disclosure_line_under_watch"
            )
        elif disclosure_governance_trigger == "segmented_disclosure_watch":
            disclosure_governance_trajectory_target = "segmented_disclosure_watch"
            disclosure_governance_trajectory_trigger = (
                "segmented_disclosure_watch"
            )
            disclosure_governance_trajectory_notes.append(
                "segmented_delivery_keeps_disclosure_line_under_watch"
            )
        elif disclosure_governance_trigger == "clarity_disclosure_watch":
            disclosure_governance_trajectory_target = "clarity_buffered_disclosure_watch"
            disclosure_governance_trajectory_trigger = "clarity_disclosure_watch"
            disclosure_governance_trajectory_notes.append(
                "clarity_watch_keeps_disclosure_line_under_watch"
            )
        else:
            disclosure_governance_trajectory_target = disclosure_governance_target
            disclosure_governance_trajectory_trigger = "disclosure_watch_active"
            disclosure_governance_trajectory_notes.append(
                "disclosure_line_is_shifting_without_full_recenter"
            )
    else:
        disclosure_governance_trajectory_status = "stable"
        disclosure_governance_trajectory_target = "steady_transparent_disclosure"
        disclosure_governance_trajectory_trigger = "disclosure_governance_stable"
        disclosure_governance_trajectory_notes.append(
            "disclosure_line_is_holding_stable_and_honest"
        )

    reciprocity_score = float(relationship_state.r_vector.get("reciprocity", 0.5))
    reciprocity_governance_notes: list[str] = []
    if dependency_governance_status == "revise":
        reciprocity_governance_status = "revise"
        reciprocity_governance_target = "bounded_nonexclusive_reciprocity"
        reciprocity_governance_trigger = "dependency_reciprocity_recenter"
        reciprocity_governance_notes.append(
            "dependency_recenter_requires_explicitly_nonexclusive_reciprocity"
        )
    elif emotional_debt_status == "elevated":
        reciprocity_governance_status = "revise"
        reciprocity_governance_target = "decompression_before_reciprocity_push"
        reciprocity_governance_trigger = "debt_reciprocity_recenter"
        reciprocity_governance_notes.append(
            "elevated_debt_requires_decompression_before_reciprocity_push"
        )
    elif support_governance_status == "revise":
        reciprocity_governance_status = "revise"
        reciprocity_governance_target = "user_led_reciprocity_reset"
        reciprocity_governance_trigger = "support_reciprocity_recenter"
        reciprocity_governance_notes.append(
            "support_recenter_requires_user_led_reciprocity_reset"
        )
    elif (
        reciprocity_score <= 0.36
        and commitment_governance_status in {"watch", "revise"}
    ):
        reciprocity_governance_status = "revise"
        reciprocity_governance_target = "expectation_reset_before_reciprocity_push"
        reciprocity_governance_trigger = "low_reciprocity_recenter"
        reciprocity_governance_notes.append(
            "low_reciprocity_plus_commitment_pressure_requires_expectation_reset"
        )
    elif (
        reciprocity_score < 0.48
        or emotional_debt_status == "watch"
        or support_governance_status == "watch"
        or autonomy_governance_status == "watch"
        or commitment_governance_status == "watch"
        or expectation_calibration_status == "watch"
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        reciprocity_governance_status = "watch"
        if reciprocity_score < 0.48:
            reciprocity_governance_target = "lightweight_reciprocity_watch"
            reciprocity_governance_trigger = "low_reciprocity_watch"
            reciprocity_governance_notes.append(
                "low_reciprocity_keeps_line_lightweight_and_low_pressure"
            )
        elif emotional_debt_status == "watch":
            reciprocity_governance_target = "debt_buffered_reciprocity_watch"
            reciprocity_governance_trigger = "debt_reciprocity_watch"
            reciprocity_governance_notes.append(
                "debt_watch_keeps_reciprocity_line_buffered"
            )
        elif support_governance_status == "watch":
            reciprocity_governance_target = "low_pressure_reciprocity_watch"
            reciprocity_governance_trigger = "support_reciprocity_watch"
            reciprocity_governance_notes.append(
                "support_watch_keeps_reciprocity_line_low_pressure"
            )
        elif autonomy_governance_status == "watch":
            reciprocity_governance_target = "user_led_reciprocity_watch"
            reciprocity_governance_trigger = "autonomy_reciprocity_watch"
            reciprocity_governance_notes.append(
                "autonomy_watch_keeps_reciprocity_line_user_led"
            )
        elif commitment_governance_status == "watch":
            reciprocity_governance_target = "bounded_reciprocity_watch"
            reciprocity_governance_trigger = "commitment_reciprocity_watch"
            reciprocity_governance_notes.append(
                "commitment_watch_keeps_reciprocity_line_bounded"
            )
        elif expectation_calibration_status == "watch":
            reciprocity_governance_target = (
                "expectation_buffered_reciprocity_watch"
            )
            reciprocity_governance_trigger = "expectation_reciprocity_watch"
            reciprocity_governance_notes.append(
                "expectation_watch_keeps_reciprocity_line_explicitly_bounded"
            )
        else:
            reciprocity_governance_target = "stepwise_reciprocity_watch"
            reciprocity_governance_trigger = "segmented_reciprocity_watch"
            reciprocity_governance_notes.append(
                "segmented_delivery_keeps_reciprocity_line_stepwise"
            )
    else:
        reciprocity_governance_status = "pass"
        reciprocity_governance_target = "steady_mutual_reciprocity"
        reciprocity_governance_trigger = "reciprocity_line_stable"

    reciprocity_governance_trajectory_notes: list[str] = []
    if reciprocity_governance_status == "revise":
        reciprocity_governance_trajectory_status = "recenter"
        if reciprocity_governance_trigger == "dependency_reciprocity_recenter":
            reciprocity_governance_trajectory_target = (
                "bounded_nonexclusive_reciprocity"
            )
            reciprocity_governance_trajectory_trigger = (
                "dependency_reciprocity_recenter"
            )
            reciprocity_governance_trajectory_notes.append(
                "dependency_pressure_keeps_reciprocity_line_in_nonexclusive_mode"
            )
        elif reciprocity_governance_trigger == "debt_reciprocity_recenter":
            reciprocity_governance_trajectory_target = (
                "decompression_before_reciprocity_push"
            )
            reciprocity_governance_trajectory_trigger = (
                "debt_reciprocity_recenter"
            )
            reciprocity_governance_trajectory_notes.append(
                "debt_pressure_keeps_reciprocity_line_in_decompression_mode"
            )
        elif reciprocity_governance_trigger == "support_reciprocity_recenter":
            reciprocity_governance_trajectory_target = "user_led_reciprocity_reset"
            reciprocity_governance_trajectory_trigger = (
                "support_reciprocity_recenter"
            )
            reciprocity_governance_trajectory_notes.append(
                "support_recenter_keeps_reciprocity_line_user_led"
            )
        else:
            reciprocity_governance_trajectory_target = (
                "expectation_reset_before_reciprocity_push"
            )
            reciprocity_governance_trajectory_trigger = "low_reciprocity_recenter"
            reciprocity_governance_trajectory_notes.append(
                "low_reciprocity_keeps_line_in_expectation_reset_mode"
            )
    elif reciprocity_governance_status == "watch":
        reciprocity_governance_trajectory_status = "watch"
        if reciprocity_governance_trigger == "low_reciprocity_watch":
            reciprocity_governance_trajectory_target = (
                "lightweight_reciprocity_watch"
            )
            reciprocity_governance_trajectory_trigger = "low_reciprocity_watch"
            reciprocity_governance_trajectory_notes.append(
                "low_reciprocity_keeps_line_under_watch"
            )
        elif reciprocity_governance_trigger == "debt_reciprocity_watch":
            reciprocity_governance_trajectory_target = (
                "debt_buffered_reciprocity_watch"
            )
            reciprocity_governance_trajectory_trigger = "debt_reciprocity_watch"
            reciprocity_governance_trajectory_notes.append(
                "debt_pressure_keeps_reciprocity_line_buffered"
            )
        elif reciprocity_governance_trigger == "support_reciprocity_watch":
            reciprocity_governance_trajectory_target = (
                "low_pressure_reciprocity_watch"
            )
            reciprocity_governance_trajectory_trigger = (
                "support_reciprocity_watch"
            )
            reciprocity_governance_trajectory_notes.append(
                "support_watch_keeps_reciprocity_line_under_low_pressure_watch"
            )
        elif reciprocity_governance_trigger == "autonomy_reciprocity_watch":
            reciprocity_governance_trajectory_target = "user_led_reciprocity_watch"
            reciprocity_governance_trajectory_trigger = (
                "autonomy_reciprocity_watch"
            )
            reciprocity_governance_trajectory_notes.append(
                "autonomy_watch_keeps_reciprocity_line_user_led"
            )
        elif reciprocity_governance_trigger == "commitment_reciprocity_watch":
            reciprocity_governance_trajectory_target = "bounded_reciprocity_watch"
            reciprocity_governance_trajectory_trigger = (
                "commitment_reciprocity_watch"
            )
            reciprocity_governance_trajectory_notes.append(
                "commitment_watch_keeps_reciprocity_line_bounded"
            )
        elif reciprocity_governance_trigger == "expectation_reciprocity_watch":
            reciprocity_governance_trajectory_target = (
                "expectation_buffered_reciprocity_watch"
            )
            reciprocity_governance_trajectory_trigger = (
                "expectation_reciprocity_watch"
            )
            reciprocity_governance_trajectory_notes.append(
                "expectation_watch_keeps_reciprocity_line_bounded"
            )
        elif reciprocity_governance_trigger == "segmented_reciprocity_watch":
            reciprocity_governance_trajectory_target = "stepwise_reciprocity_watch"
            reciprocity_governance_trajectory_trigger = (
                "segmented_reciprocity_watch"
            )
            reciprocity_governance_trajectory_notes.append(
                "segmented_delivery_keeps_reciprocity_line_stepwise"
            )
        else:
            reciprocity_governance_trajectory_target = reciprocity_governance_target
            reciprocity_governance_trajectory_trigger = "reciprocity_watch_active"
            reciprocity_governance_trajectory_notes.append(
                "reciprocity_line_is_shifting_without_full_recenter"
            )
    else:
        reciprocity_governance_trajectory_status = "stable"
        reciprocity_governance_trajectory_target = "steady_mutual_reciprocity"
        reciprocity_governance_trajectory_trigger = "reciprocity_governance_stable"
        reciprocity_governance_trajectory_notes.append(
            "reciprocity_line_is_holding_stable_and_mutual"
        )

    pressure_governance_notes: list[str] = []
    if emotional_debt_status == "elevated":
        pressure_governance_status = "revise"
        pressure_governance_target = "decompression_before_pressure_push"
        pressure_governance_trigger = "debt_pressure_recenter"
        pressure_governance_notes.append(
            "elevated_debt_requires_decompression_before_extra_relational_pressure"
        )
    elif repair_governance_status == "revise":
        pressure_governance_status = "revise"
        pressure_governance_target = "repair_first_pressure_reset"
        pressure_governance_trigger = "repair_pressure_recenter"
        pressure_governance_notes.append(
            "repair_recenter_requires_pressure_reset_before_forward_motion"
        )
    elif dependency_governance_status == "revise":
        pressure_governance_status = "revise"
        pressure_governance_target = "dependency_safe_pressure_reset"
        pressure_governance_trigger = "dependency_pressure_recenter"
        pressure_governance_notes.append(
            "dependency_recenter_requires_nonexclusive_low_pressure_support"
        )
    elif autonomy_governance_status == "revise":
        pressure_governance_status = "revise"
        pressure_governance_target = "explicit_user_space_pressure_reset"
        pressure_governance_trigger = "autonomy_pressure_recenter"
        pressure_governance_notes.append(
            "autonomy_recenter_requires_explicit_user_space_before_more_pressure"
        )
    elif boundary_governance_status == "revise":
        pressure_governance_status = "revise"
        pressure_governance_target = "hard_boundary_pressure_reset"
        pressure_governance_trigger = "boundary_pressure_recenter"
        pressure_governance_notes.append(
            "boundary_recenter_requires_pressure_reset_and clearer spacing"
        )
    elif (
        pacing_governance_status == "watch"
        or support_governance_status == "watch"
        or attunement_governance_status == "watch"
        or trust_governance_status == "watch"
        or commitment_governance_status == "watch"
        or (
            response_sequence_plan is not None
            and response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        pressure_governance_status = "watch"
        if pacing_governance_status == "watch":
            pressure_governance_target = "slow_pressure_watch"
            pressure_governance_trigger = "pacing_pressure_watch"
            pressure_governance_notes.append(
                "pacing_watch_keeps_pressure_line_slow_and_proportionate"
            )
        elif support_governance_status == "watch":
            pressure_governance_target = "bounded_support_pressure_watch"
            pressure_governance_trigger = "support_pressure_watch"
            pressure_governance_notes.append(
                "support_watch_keeps_pressure_line_low_pressure_and_bounded"
            )
        elif attunement_governance_status == "watch":
            pressure_governance_target = "attunement_sensitive_pressure_watch"
            pressure_governance_trigger = "attunement_pressure_watch"
            pressure_governance_notes.append(
                "attunement_watch_keeps_pressure_line_more responsive and gentle"
            )
        elif trust_governance_status == "watch":
            pressure_governance_target = "relational_safety_pressure_watch"
            pressure_governance_trigger = "trust_pressure_watch"
            pressure_governance_notes.append(
                "trust_watch_keeps_pressure_line_safety_first_and_low_pressure"
            )
        elif commitment_governance_status == "watch":
            pressure_governance_target = "bounded_commitment_pressure_watch"
            pressure_governance_trigger = "commitment_pressure_watch"
            pressure_governance_notes.append(
                "commitment_watch_keeps_pressure_line_explicitly_bounded"
            )
        else:
            pressure_governance_target = "stepwise_pressure_watch"
            pressure_governance_trigger = "segmented_pressure_watch"
            pressure_governance_notes.append(
                "segmented_delivery_keeps_pressure_line_stepwise_and_nonstacking"
            )
    else:
        pressure_governance_status = "pass"
        pressure_governance_target = "steady_low_pressure_support"
        pressure_governance_trigger = "pressure_line_stable"

    pressure_governance_trajectory_notes: list[str] = []
    if pressure_governance_status == "revise":
        pressure_governance_trajectory_status = "recenter"
        if pressure_governance_trigger == "debt_pressure_recenter":
            pressure_governance_trajectory_target = (
                "decompression_before_pressure_push"
            )
            pressure_governance_trajectory_trigger = "debt_pressure_recenter"
            pressure_governance_trajectory_notes.append(
                "debt_load_keeps_pressure_line_in_decompression_mode"
            )
        elif pressure_governance_trigger == "repair_pressure_recenter":
            pressure_governance_trajectory_target = "repair_first_pressure_reset"
            pressure_governance_trajectory_trigger = "repair_pressure_recenter"
            pressure_governance_trajectory_notes.append(
                "repair_pressure_keeps_pressure_line_in_repair_first_mode"
            )
        elif pressure_governance_trigger == "dependency_pressure_recenter":
            pressure_governance_trajectory_target = (
                "dependency_safe_pressure_reset"
            )
            pressure_governance_trajectory_trigger = "dependency_pressure_recenter"
            pressure_governance_trajectory_notes.append(
                "dependency_pressure_keeps_pressure_line_nonexclusive_and_reset"
            )
        elif pressure_governance_trigger == "autonomy_pressure_recenter":
            pressure_governance_trajectory_target = (
                "explicit_user_space_pressure_reset"
            )
            pressure_governance_trajectory_trigger = "autonomy_pressure_recenter"
            pressure_governance_trajectory_notes.append(
                "autonomy_pressure_keeps_pressure_line_in_user_space_mode"
            )
        else:
            pressure_governance_trajectory_target = "hard_boundary_pressure_reset"
            pressure_governance_trajectory_trigger = "boundary_pressure_recenter"
            pressure_governance_trajectory_notes.append(
                "boundary_pressure_keeps_pressure_line_in_explicit_reset_mode"
            )
    elif pressure_governance_status == "watch":
        pressure_governance_trajectory_status = "watch"
        if pressure_governance_trigger == "pacing_pressure_watch":
            pressure_governance_trajectory_target = "slow_pressure_watch"
            pressure_governance_trajectory_trigger = "pacing_pressure_watch"
            pressure_governance_trajectory_notes.append(
                "pacing_watch_keeps_pressure_line_under_slow_watch"
            )
        elif pressure_governance_trigger == "support_pressure_watch":
            pressure_governance_trajectory_target = (
                "bounded_support_pressure_watch"
            )
            pressure_governance_trajectory_trigger = "support_pressure_watch"
            pressure_governance_trajectory_notes.append(
                "support_watch_keeps_pressure_line_under_bounded_watch"
            )
        elif pressure_governance_trigger == "attunement_pressure_watch":
            pressure_governance_trajectory_target = (
                "attunement_sensitive_pressure_watch"
            )
            pressure_governance_trajectory_trigger = "attunement_pressure_watch"
            pressure_governance_trajectory_notes.append(
                "attunement_watch_keeps_pressure_line_responsive_and_gentle"
            )
        elif pressure_governance_trigger == "trust_pressure_watch":
            pressure_governance_trajectory_target = (
                "relational_safety_pressure_watch"
            )
            pressure_governance_trajectory_trigger = "trust_pressure_watch"
            pressure_governance_trajectory_notes.append(
                "trust_watch_keeps_pressure_line_safety_first"
            )
        elif pressure_governance_trigger == "commitment_pressure_watch":
            pressure_governance_trajectory_target = (
                "bounded_commitment_pressure_watch"
            )
            pressure_governance_trajectory_trigger = "commitment_pressure_watch"
            pressure_governance_trajectory_notes.append(
                "commitment_watch_keeps_pressure_line_bounded"
            )
        elif pressure_governance_trigger == "segmented_pressure_watch":
            pressure_governance_trajectory_target = "stepwise_pressure_watch"
            pressure_governance_trajectory_trigger = "segmented_pressure_watch"
            pressure_governance_trajectory_notes.append(
                "segmented_delivery_keeps_pressure_line_stepwise"
            )
        else:
            pressure_governance_trajectory_target = pressure_governance_target
            pressure_governance_trajectory_trigger = "pressure_watch_active"
            pressure_governance_trajectory_notes.append(
                "pressure_line_is_shifting_without_full_recenter"
            )
    else:
        pressure_governance_trajectory_status = "stable"
        pressure_governance_trajectory_target = "steady_low_pressure_support"
        pressure_governance_trajectory_trigger = "pressure_governance_stable"
        pressure_governance_trajectory_notes.append(
            "pressure_line_is_holding_stable_and_proportionate"
        )

    relational_watch_count = sum(
        1
        for status in (
            support_governance_status,
            continuity_governance_status,
            repair_governance_status,
            attunement_governance_status,
            trust_governance_status,
            clarity_governance_status,
            pacing_governance_status,
            commitment_governance_status,
            disclosure_governance_status,
            reciprocity_governance_status,
            pressure_governance_status,
        )
        if status == "watch"
    )
    relational_governance_notes: list[str] = []
    if boundary_governance_status == "revise":
        relational_governance_status = "revise"
        relational_governance_target = "boundary_safe_relational_reset"
        relational_governance_trigger = "boundary_relational_recenter"
        relational_governance_notes.append(
            "boundary_recenter_requires_relational_reset_before_progress"
        )
    elif trust_governance_status == "revise":
        relational_governance_status = "revise"
        relational_governance_target = "trust_repair_relational_reset"
        relational_governance_trigger = "trust_relational_recenter"
        relational_governance_notes.append(
            "trust_recenter_requires_relational_repair_before_forward motion"
        )
    elif pressure_governance_status == "revise":
        relational_governance_status = "revise"
        relational_governance_target = "low_pressure_relational_reset"
        relational_governance_trigger = "pressure_relational_recenter"
        relational_governance_notes.append(
            "pressure_recenter_requires_relational_reset_and_more space"
        )
    elif repair_governance_status == "revise":
        relational_governance_status = "revise"
        relational_governance_target = "repair_first_relational_reset"
        relational_governance_trigger = "repair_relational_recenter"
        relational_governance_notes.append(
            "repair_recenter_requires_relational_reset_before renewed progress"
        )
    elif continuity_governance_status == "revise":
        relational_governance_status = "revise"
        relational_governance_target = "reanchor_before_relational_progress"
        relational_governance_trigger = "continuity_relational_recenter"
        relational_governance_notes.append(
            "continuity_recenter_requires_reanchor_before_relational_progress"
        )
    elif support_governance_status == "revise":
        relational_governance_status = "revise"
        relational_governance_target = "bounded_support_relational_reset"
        relational_governance_trigger = "support_relational_recenter"
        relational_governance_notes.append(
            "support_recenter_requires_bounded_relational_reset"
        )
    elif (
        relational_watch_count >= 4
        or trust_governance_status == "watch"
        or pressure_governance_status == "watch"
        or continuity_governance_status == "watch"
        or repair_governance_status == "watch"
        or support_governance_status == "watch"
    ):
        relational_governance_status = "watch"
        if trust_governance_status == "watch":
            relational_governance_target = "trust_buffered_relational_watch"
            relational_governance_trigger = "trust_relational_watch"
            relational_governance_notes.append(
                "trust_watch_keeps_relational_line_safety_buffered"
            )
        elif pressure_governance_status == "watch":
            relational_governance_target = "low_pressure_relational_watch"
            relational_governance_trigger = "pressure_relational_watch"
            relational_governance_notes.append(
                "pressure_watch_keeps_relational_line_low pressure and spacious"
            )
        elif continuity_governance_status == "watch":
            relational_governance_target = "reanchored_relational_watch"
            relational_governance_trigger = "continuity_relational_watch"
            relational_governance_notes.append(
                "continuity_watch_keeps_relational_line_reanchored"
            )
        elif repair_governance_status == "watch":
            relational_governance_target = "repair_buffered_relational_watch"
            relational_governance_trigger = "repair_relational_watch"
            relational_governance_notes.append(
                "repair_watch_keeps_relational_line_buffered and slow"
            )
        elif support_governance_status == "watch":
            relational_governance_target = "bounded_support_relational_watch"
            relational_governance_trigger = "support_relational_watch"
            relational_governance_notes.append(
                "support_watch_keeps_relational_line bounded and user led"
            )
        else:
            relational_governance_target = "multi_signal_relational_watch"
            relational_governance_trigger = "relational_watch_active"
            relational_governance_notes.append(
                "multiple_relational_watch_signals_keep_the_line_under review"
            )
    else:
        relational_governance_status = "pass"
        relational_governance_target = "steady_bounded_relational_progress"
        relational_governance_trigger = "relational_line_stable"

    relational_governance_trajectory_notes: list[str] = []
    if relational_governance_status == "revise":
        relational_governance_trajectory_status = "recenter"
        if relational_governance_trigger == "boundary_relational_recenter":
            relational_governance_trajectory_target = (
                "boundary_safe_relational_reset"
            )
            relational_governance_trajectory_trigger = (
                "boundary_relational_recenter"
            )
            relational_governance_trajectory_notes.append(
                "boundary_pressure_keeps_relational_line_in_reset_mode"
            )
        elif relational_governance_trigger == "trust_relational_recenter":
            relational_governance_trajectory_target = (
                "trust_repair_relational_reset"
            )
            relational_governance_trajectory_trigger = "trust_relational_recenter"
            relational_governance_trajectory_notes.append(
                "trust_pressure_keeps_relational_line_in_repair mode"
            )
        elif relational_governance_trigger == "pressure_relational_recenter":
            relational_governance_trajectory_target = (
                "low_pressure_relational_reset"
            )
            relational_governance_trajectory_trigger = (
                "pressure_relational_recenter"
            )
            relational_governance_trajectory_notes.append(
                "pressure_overload_keeps_relational_line_in_low pressure reset"
            )
        elif relational_governance_trigger == "repair_relational_recenter":
            relational_governance_trajectory_target = (
                "repair_first_relational_reset"
            )
            relational_governance_trajectory_trigger = "repair_relational_recenter"
            relational_governance_trajectory_notes.append(
                "repair_pressure_keeps_relational_line_in_repair first mode"
            )
        elif relational_governance_trigger == "continuity_relational_recenter":
            relational_governance_trajectory_target = (
                "reanchor_before_relational_progress"
            )
            relational_governance_trajectory_trigger = (
                "continuity_relational_recenter"
            )
            relational_governance_trajectory_notes.append(
                "continuity_drift_keeps_relational_line_in_reanchor mode"
            )
        else:
            relational_governance_trajectory_target = (
                "bounded_support_relational_reset"
            )
            relational_governance_trajectory_trigger = "support_relational_recenter"
            relational_governance_trajectory_notes.append(
                "support_pressure_keeps_relational_line in bounded reset mode"
            )
    elif relational_governance_status == "watch":
        relational_governance_trajectory_status = "watch"
        if relational_governance_trigger == "trust_relational_watch":
            relational_governance_trajectory_target = (
                "trust_buffered_relational_watch"
            )
            relational_governance_trajectory_trigger = "trust_relational_watch"
            relational_governance_trajectory_notes.append(
                "trust_watch_keeps_relational_line_under buffered watch"
            )
        elif relational_governance_trigger == "pressure_relational_watch":
            relational_governance_trajectory_target = (
                "low_pressure_relational_watch"
            )
            relational_governance_trajectory_trigger = "pressure_relational_watch"
            relational_governance_trajectory_notes.append(
                "pressure_watch_keeps_relational_line_under low pressure watch"
            )
        elif relational_governance_trigger == "continuity_relational_watch":
            relational_governance_trajectory_target = (
                "reanchored_relational_watch"
            )
            relational_governance_trajectory_trigger = (
                "continuity_relational_watch"
            )
            relational_governance_trajectory_notes.append(
                "continuity_watch_keeps_relational_line_under reanchor watch"
            )
        elif relational_governance_trigger == "repair_relational_watch":
            relational_governance_trajectory_target = (
                "repair_buffered_relational_watch"
            )
            relational_governance_trajectory_trigger = "repair_relational_watch"
            relational_governance_trajectory_notes.append(
                "repair_watch_keeps_relational_line_under buffered watch"
            )
        elif relational_governance_trigger == "support_relational_watch":
            relational_governance_trajectory_target = (
                "bounded_support_relational_watch"
            )
            relational_governance_trajectory_trigger = "support_relational_watch"
            relational_governance_trajectory_notes.append(
                "support_watch_keeps_relational_line_under bounded watch"
            )
        else:
            relational_governance_trajectory_target = (
                "multi_signal_relational_watch"
            )
            relational_governance_trajectory_trigger = "relational_watch_active"
            relational_governance_trajectory_notes.append(
                "multiple_signals_keep_relational_line_under watch"
            )
    else:
        relational_governance_trajectory_status = "stable"
        relational_governance_trajectory_target = (
            "steady_bounded_relational_progress"
        )
        relational_governance_trajectory_trigger = (
            "relational_governance_stable"
        )
        relational_governance_trajectory_notes.append(
            "relational_line_is_holding_stable_and_bounded"
        )

    safety_watch_count = sum(
        1
        for status in (
            boundary_governance_status,
            trust_governance_status,
            clarity_governance_status,
            disclosure_governance_status,
            pressure_governance_status,
            continuity_governance_status,
            repair_governance_status,
            relational_governance_status,
        )
        if status == "watch"
    )
    safety_governance_notes: list[str] = []
    if boundary_governance_status == "revise":
        safety_governance_status = "revise"
        safety_governance_target = "hard_boundary_safety_reset"
        safety_governance_trigger = "boundary_safety_recenter"
        safety_governance_notes.append(
            "boundary_recenter_requires_a_hard_safety_reset_before_progress"
        )
    elif trust_governance_status == "revise":
        safety_governance_status = "revise"
        safety_governance_target = "trust_repair_safety_reset"
        safety_governance_trigger = "trust_safety_recenter"
        safety_governance_notes.append(
            "trust_recenter_requires_safety_buffering_and_repair_first"
        )
    elif disclosure_governance_status == "revise":
        safety_governance_status = "revise"
        safety_governance_target = "explicit_uncertainty_safety_reset"
        safety_governance_trigger = "disclosure_safety_recenter"
        safety_governance_notes.append(
            "disclosure_recenter_requires_explicit_uncertainty_and_tighter_bounds"
        )
    elif clarity_governance_status == "revise":
        safety_governance_status = "revise"
        safety_governance_target = "reanchor_before_safety_progress"
        safety_governance_trigger = "clarity_safety_recenter"
        safety_governance_notes.append(
            "clarity_recenter_requires_reanchoring_before_further_progress"
        )
    elif pressure_governance_status == "revise":
        safety_governance_status = "revise"
        safety_governance_target = "low_pressure_safety_reset"
        safety_governance_trigger = "pressure_safety_recenter"
        safety_governance_notes.append(
            "pressure_recenter_requires_low_pressure_support_before_any_push"
        )
    elif relational_governance_status == "revise":
        safety_governance_status = "revise"
        safety_governance_target = "bounded_relational_safety_reset"
        safety_governance_trigger = "relational_safety_recenter"
        safety_governance_notes.append(
            "relational_recenter_requires_bounded_safety_reset_before_resuming"
        )
    elif (
        safety_watch_count >= 4
        or boundary_governance_status == "watch"
        or trust_governance_status == "watch"
        or disclosure_governance_status == "watch"
        or clarity_governance_status == "watch"
        or pressure_governance_status == "watch"
        or relational_governance_status == "watch"
    ):
        safety_governance_status = "watch"
        if boundary_governance_status == "watch":
            safety_governance_target = "boundary_buffered_safety_watch"
            safety_governance_trigger = "boundary_safety_watch"
            safety_governance_notes.append(
                "boundary_watch_keeps_the_safety_line_explicit_and_buffered"
            )
        elif trust_governance_status == "watch":
            safety_governance_target = "trust_buffered_safety_watch"
            safety_governance_trigger = "trust_safety_watch"
            safety_governance_notes.append(
                "trust_watch_keeps_the_safety_line_careful_and_buffered"
            )
        elif disclosure_governance_status == "watch":
            safety_governance_target = "uncertainty_first_safety_watch"
            safety_governance_trigger = "disclosure_safety_watch"
            safety_governance_notes.append(
                "disclosure_watch_keeps_the_safety_line_uncertainty_first"
            )
        elif clarity_governance_status == "watch":
            safety_governance_target = "reanchored_safety_watch"
            safety_governance_trigger = "clarity_safety_watch"
            safety_governance_notes.append(
                "clarity_watch_keeps_the_safety_line_reanchored_and_scaffolded"
            )
        elif pressure_governance_status == "watch":
            safety_governance_target = "low_pressure_safety_watch"
            safety_governance_trigger = "pressure_safety_watch"
            safety_governance_notes.append(
                "pressure_watch_keeps_the_safety_line_low_pressure_and_spacious"
            )
        elif relational_governance_status == "watch":
            safety_governance_target = "bounded_relational_safety_watch"
            safety_governance_trigger = "relational_safety_watch"
            safety_governance_notes.append(
                "relational_watch_keeps_the_safety_line_bounded_and_deliberate"
            )
        else:
            safety_governance_target = "multi_signal_safety_watch"
            safety_governance_trigger = "safety_watch_active"
            safety_governance_notes.append(
                "multiple_signals_keep_the_safety_line_under_review"
            )
    else:
        safety_governance_status = "pass"
        safety_governance_target = "steady_safe_relational_support"
        safety_governance_trigger = "safety_line_stable"

    safety_governance_trajectory_notes: list[str] = []
    if safety_governance_status == "revise":
        safety_governance_trajectory_status = "recenter"
        if safety_governance_trigger == "boundary_safety_recenter":
            safety_governance_trajectory_target = "hard_boundary_safety_reset"
            safety_governance_trajectory_trigger = "boundary_safety_recenter"
            safety_governance_trajectory_notes.append(
                "boundary_pressure_keeps_the_safety_line_in_reset_mode"
            )
        elif safety_governance_trigger == "trust_safety_recenter":
            safety_governance_trajectory_target = "trust_repair_safety_reset"
            safety_governance_trajectory_trigger = "trust_safety_recenter"
            safety_governance_trajectory_notes.append(
                "trust_pressure_keeps_the_safety_line_in_repair_mode"
            )
        elif safety_governance_trigger == "disclosure_safety_recenter":
            safety_governance_trajectory_target = (
                "explicit_uncertainty_safety_reset"
            )
            safety_governance_trajectory_trigger = "disclosure_safety_recenter"
            safety_governance_trajectory_notes.append(
                "disclosure_pressure_keeps_the_safety_line_uncertainty_first"
            )
        elif safety_governance_trigger == "clarity_safety_recenter":
            safety_governance_trajectory_target = (
                "reanchor_before_safety_progress"
            )
            safety_governance_trajectory_trigger = "clarity_safety_recenter"
            safety_governance_trajectory_notes.append(
                "clarity_drift_keeps_the_safety_line_in_reanchor_mode"
            )
        elif safety_governance_trigger == "pressure_safety_recenter":
            safety_governance_trajectory_target = "low_pressure_safety_reset"
            safety_governance_trajectory_trigger = "pressure_safety_recenter"
            safety_governance_trajectory_notes.append(
                "pressure_overload_keeps_the_safety_line_in_low_pressure_reset"
            )
        else:
            safety_governance_trajectory_target = (
                "bounded_relational_safety_reset"
            )
            safety_governance_trajectory_trigger = "relational_safety_recenter"
            safety_governance_trajectory_notes.append(
                "relational_drift_keeps_the_safety_line_in_bounded_reset_mode"
            )
    elif safety_governance_status == "watch":
        safety_governance_trajectory_status = "watch"
        if safety_governance_trigger == "boundary_safety_watch":
            safety_governance_trajectory_target = "boundary_buffered_safety_watch"
            safety_governance_trajectory_trigger = "boundary_safety_watch"
            safety_governance_trajectory_notes.append(
                "boundary_watch_keeps_the_safety_line_under_buffered_watch"
            )
        elif safety_governance_trigger == "trust_safety_watch":
            safety_governance_trajectory_target = "trust_buffered_safety_watch"
            safety_governance_trajectory_trigger = "trust_safety_watch"
            safety_governance_trajectory_notes.append(
                "trust_watch_keeps_the_safety_line_under_buffered_watch"
            )
        elif safety_governance_trigger == "disclosure_safety_watch":
            safety_governance_trajectory_target = "uncertainty_first_safety_watch"
            safety_governance_trajectory_trigger = "disclosure_safety_watch"
            safety_governance_trajectory_notes.append(
                "disclosure_watch_keeps_the_safety_line_uncertainty_first"
            )
        elif safety_governance_trigger == "clarity_safety_watch":
            safety_governance_trajectory_target = "reanchored_safety_watch"
            safety_governance_trajectory_trigger = "clarity_safety_watch"
            safety_governance_trajectory_notes.append(
                "clarity_watch_keeps_the_safety_line_reanchored"
            )
        elif safety_governance_trigger == "pressure_safety_watch":
            safety_governance_trajectory_target = "low_pressure_safety_watch"
            safety_governance_trajectory_trigger = "pressure_safety_watch"
            safety_governance_trajectory_notes.append(
                "pressure_watch_keeps_the_safety_line_low_pressure"
            )
        elif safety_governance_trigger == "relational_safety_watch":
            safety_governance_trajectory_target = (
                "bounded_relational_safety_watch"
            )
            safety_governance_trajectory_trigger = "relational_safety_watch"
            safety_governance_trajectory_notes.append(
                "relational_watch_keeps_the_safety_line_bounded"
            )
        else:
            safety_governance_trajectory_target = "multi_signal_safety_watch"
            safety_governance_trajectory_trigger = "safety_watch_active"
            safety_governance_trajectory_notes.append(
                "multiple_signals_keep_the_safety_line_under_watch"
            )
    else:
        safety_governance_trajectory_status = "stable"
        safety_governance_trajectory_target = "steady_safe_relational_support"
        safety_governance_trajectory_trigger = "safety_governance_stable"
        safety_governance_trajectory_notes.append(
            "safety_line_is_holding_stable_and_bounded"
        )

    growth_transition_readiness = _clamp(
        0.16
        + relationship_state.psychological_safety * 0.45
        + min(recall_count, 3) * 0.08
        + (0.08 if user_model_confidence >= 0.55 else 0.0)
        - (
            0.2
            if emotional_debt_status == "elevated"
            else 0.08 if emotional_debt_status == "watch" else 0.0
        )
        - (0.12 if repair_assessment.repair_needed else 0.0)
        - (0.08 if filtered_recall_count > 0 else 0.0)
    )
    growth_transition_notes: list[str] = []
    if emotional_debt_status == "elevated":
        growth_transition_status = "redirect"
        growth_transition_target = "repairing"
        growth_transition_trigger = "emotional_debt_requires_repair"
        growth_transition_notes.append("elevated_debt_blocks_forward_growth")
    elif growth_stage == "deepening" and relationship_state.dependency_risk == "elevated":
        growth_transition_status = "watch"
        growth_transition_target = "steadying"
        growth_transition_trigger = "dependency_risk_requires_rebalancing"
        growth_transition_notes.append("deepening_not_safe_under_dependency_pressure")
    elif growth_stage == "deepening" and repair_assessment.repair_needed:
        growth_transition_status = "watch"
        growth_transition_target = "repairing"
        growth_transition_trigger = "repair_load_interrupts_deepening"
        growth_transition_notes.append("repair_load_requires_repairing_stage")
    elif (
        growth_stage == "forming"
        and turn_index >= 2
        and relationship_state.psychological_safety >= 0.55
    ):
        growth_transition_status = "ready"
        growth_transition_target = "stabilizing"
        growth_transition_trigger = "early_patterning_ready"
        growth_transition_notes.append("initial_turns_show_repeatable_alignment")
    elif (
        growth_stage == "stabilizing"
        and recall_count > 0
        and relationship_state.psychological_safety >= 0.66
        and relationship_state.dependency_risk == "low"
    ):
        growth_transition_status = "ready"
        growth_transition_target = "steadying"
        growth_transition_trigger = "continuity_and_safety_ready"
        growth_transition_notes.append("continuity_signals_support_steadying")
    elif (
        growth_stage == "steadying"
        and relationship_state.psychological_safety >= 0.78
        and recall_count > 1
        and relationship_state.dependency_risk == "low"
        and not repair_assessment.repair_needed
    ):
        growth_transition_status = "ready"
        growth_transition_target = "deepening"
        growth_transition_trigger = "trust_continuity_ready"
        growth_transition_notes.append("safety_and_recall_support_deepening")
    elif (
        growth_stage == "repairing"
        and emotional_debt_status == "low"
        and not repair_assessment.repair_needed
        and relationship_state.psychological_safety >= 0.62
    ):
        growth_transition_status = "ready"
        growth_transition_target = "steadying"
        growth_transition_trigger = "repair_recovered"
        growth_transition_notes.append("repair_signals_have_decompressed")
    elif filtered_recall_count > 0 or user_model_evolution_status == "revise":
        growth_transition_status = "watch"
        growth_transition_target = growth_stage
        growth_transition_trigger = "model_or_context_drift_requires_hold"
        growth_transition_notes.append("user_model_needs_stabilization_before_transition")
    else:
        growth_transition_status = "stable"
        growth_transition_target = growth_stage
        growth_transition_trigger = "maintain_current_stage"

    growth_transition_trajectory_notes: list[str] = []
    if growth_transition_status == "redirect":
        growth_transition_trajectory_status = "redirect"
        growth_transition_trajectory_target = "repairing"
        if growth_transition_trigger == "emotional_debt_requires_repair":
            growth_transition_trajectory_trigger = "debt_redirect_active"
            growth_transition_trajectory_notes.append(
                "elevated_debt_keeps_growth_line_redirected_toward_repair"
            )
        else:
            growth_transition_trajectory_trigger = "growth_redirect_active"
            growth_transition_trajectory_notes.append(
                "current_relational_pressure_keeps_growth_line_in_redirect_mode"
            )
    elif growth_transition_status == "watch":
        growth_transition_trajectory_status = "watch"
        if growth_transition_trigger == "dependency_risk_requires_rebalancing":
            growth_transition_trajectory_target = "steadying"
            growth_transition_trajectory_trigger = "dependency_transition_watch"
            growth_transition_trajectory_notes.append(
                "dependency_pressure_keeps_growth_line_under_watch"
            )
        elif growth_transition_trigger == "repair_load_interrupts_deepening":
            growth_transition_trajectory_target = "repairing"
            growth_transition_trajectory_trigger = "repair_transition_watch"
            growth_transition_trajectory_notes.append(
                "repair_load_keeps_growth_line_from_advancing"
            )
        else:
            growth_transition_trajectory_target = growth_transition_target
            growth_transition_trajectory_trigger = "stability_transition_watch"
            growth_transition_trajectory_notes.append(
                "model_or_context_drift_keeps_growth_line_under_stability_watch"
            )
    elif growth_transition_status == "ready":
        growth_transition_trajectory_status = "advance"
        growth_transition_trajectory_target = growth_transition_target
        if growth_transition_trigger == "early_patterning_ready":
            growth_transition_trajectory_trigger = "patterning_transition_ready"
            growth_transition_trajectory_notes.append(
                "early_alignment_supports_first_growth_step"
            )
        elif growth_transition_trigger == "continuity_and_safety_ready":
            growth_transition_trajectory_trigger = "continuity_transition_ready"
            growth_transition_trajectory_notes.append(
                "continuity_and_safety_support_next_growth_stage"
            )
        elif growth_transition_trigger == "trust_continuity_ready":
            growth_transition_trajectory_trigger = "deepening_transition_ready"
            growth_transition_trajectory_notes.append(
                "trust_and_recall_support_deepening_transition"
            )
        elif growth_transition_trigger == "repair_recovered":
            growth_transition_trajectory_trigger = "repair_recovery_transition_ready"
            growth_transition_trajectory_notes.append(
                "repair_recovery_supports_growth_line_reentry"
            )
        else:
            growth_transition_trajectory_trigger = "growth_transition_ready"
            growth_transition_trajectory_notes.append(
                "growth_line_is_ready_to_advance"
            )
    else:
        growth_transition_trajectory_status = "stable"
        growth_transition_trajectory_target = growth_stage
        growth_transition_trajectory_trigger = "growth_line_stable"
        if growth_transition_readiness >= 0.58:
            growth_transition_trajectory_notes.append(
                "growth_line_is_stable_and_holding_forward_readiness"
            )

    progress_governance_notes: list[str] = []
    if safety_governance_status == "revise":
        progress_governance_status = "revise"
        progress_governance_target = "safety_reset_before_progress"
        progress_governance_trigger = "safety_progress_recenter"
        progress_governance_notes.append(
            "safety_recenter_requires_resetting_progress_before_any_forward_push"
        )
    elif pressure_governance_status == "revise":
        progress_governance_status = "revise"
        progress_governance_target = "decompression_before_progress"
        progress_governance_trigger = "pressure_progress_recenter"
        progress_governance_notes.append(
            "pressure_recenter_requires_decompression_before_more_progress"
        )
    elif continuity_governance_status == "revise":
        progress_governance_status = "revise"
        progress_governance_target = "reanchor_before_progress"
        progress_governance_trigger = "continuity_progress_recenter"
        progress_governance_notes.append(
            "continuity_recenter_requires_reanchoring_before_more_progress"
        )
    elif commitment_governance_status == "revise":
        progress_governance_status = "revise"
        progress_governance_target = "bounded_commitment_before_progress"
        progress_governance_trigger = "commitment_progress_recenter"
        progress_governance_notes.append(
            "commitment_recenter_requires_bounded_nonpressured_progress"
        )
    elif expectation_calibration_status == "revise":
        progress_governance_status = "revise"
        progress_governance_target = "expectation_reset_before_progress"
        progress_governance_trigger = "expectation_progress_recenter"
        progress_governance_notes.append(
            "expectation_recenter_requires_resetting_progress_promises"
        )
    elif growth_transition_status == "redirect":
        progress_governance_status = "revise"
        progress_governance_target = "repairing_before_progress"
        progress_governance_trigger = "growth_progress_recenter"
        progress_governance_notes.append(
            "growth_redirect_requires_repairing_before_more_progress"
        )
    elif (
        growth_transition_status == "watch"
        or safety_governance_status == "watch"
        or pacing_governance_status == "watch"
        or continuity_governance_status == "watch"
        or commitment_governance_status == "watch"
        or expectation_calibration_status == "watch"
    ):
        progress_governance_status = "watch"
        if growth_transition_status == "watch":
            progress_governance_target = "growth_buffered_progress_watch"
            progress_governance_trigger = "growth_progress_watch"
            progress_governance_notes.append(
                "growth_watch_keeps_progress_line_buffered_and stage-aware"
            )
        elif safety_governance_status == "watch":
            progress_governance_target = "safety_buffered_progress_watch"
            progress_governance_trigger = "safety_progress_watch"
            progress_governance_notes.append(
                "safety_watch_keeps_progress_line_more bounded and careful"
            )
        elif pacing_governance_status == "watch":
            progress_governance_target = "slow_progress_watch"
            progress_governance_trigger = "pacing_progress_watch"
            progress_governance_notes.append(
                "pacing_watch_keeps_progress_line deliberately slow"
            )
        elif continuity_governance_status == "watch":
            progress_governance_target = "reanchored_progress_watch"
            progress_governance_trigger = "continuity_progress_watch"
            progress_governance_notes.append(
                "continuity_watch_keeps_progress_line reanchored before advancing"
            )
        elif commitment_governance_status == "watch":
            progress_governance_target = "bounded_progress_watch"
            progress_governance_trigger = "commitment_progress_watch"
            progress_governance_notes.append(
                "commitment_watch_keeps_progress_line explicitly bounded"
            )
        else:
            progress_governance_target = "expectation_buffered_progress_watch"
            progress_governance_trigger = "expectation_progress_watch"
            progress_governance_notes.append(
                "expectation_watch_keeps_progress_line softly calibrated"
            )
    else:
        progress_governance_status = "pass"
        progress_governance_target = "steady_bounded_progress"
        progress_governance_trigger = "progress_line_stable"

    progress_governance_trajectory_notes: list[str] = []
    if progress_governance_status == "revise":
        progress_governance_trajectory_status = "recenter"
        if progress_governance_trigger == "safety_progress_recenter":
            progress_governance_trajectory_target = "safety_reset_before_progress"
            progress_governance_trajectory_trigger = "safety_progress_recenter"
            progress_governance_trajectory_notes.append(
                "safety_recenter_keeps_progress_line_in_reset_mode"
            )
        elif progress_governance_trigger == "pressure_progress_recenter":
            progress_governance_trajectory_target = "decompression_before_progress"
            progress_governance_trajectory_trigger = "pressure_progress_recenter"
            progress_governance_trajectory_notes.append(
                "pressure_recenter_keeps_progress_line_in_decompression_mode"
            )
        elif progress_governance_trigger == "continuity_progress_recenter":
            progress_governance_trajectory_target = "reanchor_before_progress"
            progress_governance_trajectory_trigger = "continuity_progress_recenter"
            progress_governance_trajectory_notes.append(
                "continuity_recenter_keeps_progress_line_in_reanchor_mode"
            )
        elif progress_governance_trigger == "commitment_progress_recenter":
            progress_governance_trajectory_target = (
                "bounded_commitment_before_progress"
            )
            progress_governance_trajectory_trigger = "commitment_progress_recenter"
            progress_governance_trajectory_notes.append(
                "commitment_recenter_keeps_progress_line_bounded"
            )
        elif progress_governance_trigger == "expectation_progress_recenter":
            progress_governance_trajectory_target = "expectation_reset_before_progress"
            progress_governance_trajectory_trigger = "expectation_progress_recenter"
            progress_governance_trajectory_notes.append(
                "expectation_recenter_keeps_progress_line_in_reset_mode"
            )
        else:
            progress_governance_trajectory_target = "repairing_before_progress"
            progress_governance_trajectory_trigger = "growth_progress_recenter"
            progress_governance_trajectory_notes.append(
                "growth_redirect_keeps_progress_line_repair_first"
            )
    elif progress_governance_status == "watch":
        progress_governance_trajectory_status = "watch"
        if progress_governance_trigger == "growth_progress_watch":
            progress_governance_trajectory_target = "growth_buffered_progress_watch"
            progress_governance_trajectory_trigger = "growth_progress_watch"
            progress_governance_trajectory_notes.append(
                "growth_watch_keeps_progress_line_buffered"
            )
        elif progress_governance_trigger == "safety_progress_watch":
            progress_governance_trajectory_target = "safety_buffered_progress_watch"
            progress_governance_trajectory_trigger = "safety_progress_watch"
            progress_governance_trajectory_notes.append(
                "safety_watch_keeps_progress_line_careful"
            )
        elif progress_governance_trigger == "pacing_progress_watch":
            progress_governance_trajectory_target = "slow_progress_watch"
            progress_governance_trajectory_trigger = "pacing_progress_watch"
            progress_governance_trajectory_notes.append(
                "pacing_watch_keeps_progress_line_slow"
            )
        elif progress_governance_trigger == "continuity_progress_watch":
            progress_governance_trajectory_target = "reanchored_progress_watch"
            progress_governance_trajectory_trigger = "continuity_progress_watch"
            progress_governance_trajectory_notes.append(
                "continuity_watch_keeps_progress_line_reanchored"
            )
        elif progress_governance_trigger == "commitment_progress_watch":
            progress_governance_trajectory_target = "bounded_progress_watch"
            progress_governance_trajectory_trigger = "commitment_progress_watch"
            progress_governance_trajectory_notes.append(
                "commitment_watch_keeps_progress_line_bounded"
            )
        else:
            progress_governance_trajectory_target = (
                "expectation_buffered_progress_watch"
            )
            progress_governance_trajectory_trigger = "expectation_progress_watch"
            progress_governance_trajectory_notes.append(
                "expectation_watch_keeps_progress_line_calibrated"
            )
    else:
        progress_governance_trajectory_status = "stable"
        progress_governance_trajectory_target = "steady_bounded_progress"
        progress_governance_trajectory_trigger = "progress_governance_stable"
        progress_governance_trajectory_notes.append(
            "progress_line_is_holding_steady_and_bounded"
        )

    stability_governance_notes: list[str] = []
    if safety_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "safety_reset_before_stability"
        stability_governance_trigger = "safety_stability_recenter"
        stability_governance_notes.append(
            "safety_recenter_requires_resetting_relational_stability_before_progress"
        )
    elif relational_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "relational_reset_before_stability"
        stability_governance_trigger = "relational_stability_recenter"
        stability_governance_notes.append(
            "relational_recenter_requires_resetting_overall_stability_before_progress"
        )
    elif pressure_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "decompression_before_stability"
        stability_governance_trigger = "pressure_stability_recenter"
        stability_governance_notes.append(
            "pressure_recenter_requires_decompression_before_restoring_stability"
        )
    elif trust_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "trust_rebuild_before_stability"
        stability_governance_trigger = "trust_stability_recenter"
        stability_governance_notes.append(
            "trust_recenter_requires_rebuild_before_stability_can_hold"
        )
    elif continuity_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "reanchor_before_stability"
        stability_governance_trigger = "continuity_stability_recenter"
        stability_governance_notes.append(
            "continuity_recenter_requires_reanchoring_before_stability_can_hold"
        )
    elif repair_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "repair_scaffold_before_stability"
        stability_governance_trigger = "repair_stability_recenter"
        stability_governance_notes.append(
            "repair_recenter_requires_repair_scaffolding_before_stability"
        )
    elif progress_governance_status == "revise":
        stability_governance_status = "revise"
        stability_governance_target = "bounded_progress_reset_before_stability"
        stability_governance_trigger = "progress_stability_recenter"
        stability_governance_notes.append(
            "progress_recenter_requires_resetting_forward_motion_before_stability"
        )
    elif (
        safety_governance_status == "watch"
        or relational_governance_status == "watch"
        or pacing_governance_status == "watch"
        or trust_governance_status == "watch"
        or repair_governance_status == "watch"
        or continuity_governance_status == "watch"
        or progress_governance_status == "watch"
        or attunement_governance_status == "watch"
    ):
        stability_governance_status = "watch"
        if safety_governance_status == "watch":
            stability_governance_target = "safety_buffered_stability_watch"
            stability_governance_trigger = "safety_stability_watch"
            stability_governance_notes.append(
                "safety_watch_keeps_stability_line_cautious_and bounded"
            )
        elif relational_governance_status == "watch":
            stability_governance_target = "relational_buffered_stability_watch"
            stability_governance_trigger = "relational_stability_watch"
            stability_governance_notes.append(
                "relational_watch_keeps_stability_line_buffered_before_more_progress"
            )
        elif pacing_governance_status == "watch":
            stability_governance_target = "slow_stability_watch"
            stability_governance_trigger = "pacing_stability_watch"
            stability_governance_notes.append(
                "pacing_watch_keeps_stability_line_deliberately_slow"
            )
        elif trust_governance_status == "watch":
            stability_governance_target = "trust_buffered_stability_watch"
            stability_governance_trigger = "trust_stability_watch"
            stability_governance_notes.append(
                "trust_watch_keeps_stability_line_buffered_until_trust_recovers"
            )
        elif repair_governance_status == "watch":
            stability_governance_target = "repair_buffered_stability_watch"
            stability_governance_trigger = "repair_stability_watch"
            stability_governance_notes.append(
                "repair_watch_keeps_stability_line_scaffolded_and_low_pressure"
            )
        elif continuity_governance_status == "watch":
            stability_governance_target = "reanchored_stability_watch"
            stability_governance_trigger = "continuity_stability_watch"
            stability_governance_notes.append(
                "continuity_watch_keeps_stability_line_reanchored"
            )
        elif progress_governance_status == "watch":
            stability_governance_target = "bounded_progress_stability_watch"
            stability_governance_trigger = "progress_stability_watch"
            stability_governance_notes.append(
                "progress_watch_keeps_stability_line_bounded_before_advancing"
            )
        else:
            stability_governance_target = "attuned_stability_watch"
            stability_governance_trigger = "attunement_stability_watch"
            stability_governance_notes.append(
                "attunement_watch_keeps_stability_line_relationship-aware"
            )
    else:
        stability_governance_status = "pass"
        stability_governance_target = "steady_bounded_relational_stability"
        stability_governance_trigger = "stability_line_stable"

    stability_governance_trajectory_notes: list[str] = []
    if stability_governance_status == "revise":
        stability_governance_trajectory_status = "recenter"
        if stability_governance_trigger == "safety_stability_recenter":
            stability_governance_trajectory_target = "safety_reset_before_stability"
            stability_governance_trajectory_trigger = "safety_stability_recenter"
            stability_governance_trajectory_notes.append(
                "safety_recenter_keeps_stability_line_in_reset_mode"
            )
        elif stability_governance_trigger == "relational_stability_recenter":
            stability_governance_trajectory_target = (
                "relational_reset_before_stability"
            )
            stability_governance_trajectory_trigger = (
                "relational_stability_recenter"
            )
            stability_governance_trajectory_notes.append(
                "relational_recenter_keeps_stability_line_in_relational_reset_mode"
            )
        elif stability_governance_trigger == "pressure_stability_recenter":
            stability_governance_trajectory_target = "decompression_before_stability"
            stability_governance_trajectory_trigger = "pressure_stability_recenter"
            stability_governance_trajectory_notes.append(
                "pressure_recenter_keeps_stability_line_in_decompression_mode"
            )
        elif stability_governance_trigger == "trust_stability_recenter":
            stability_governance_trajectory_target = "trust_rebuild_before_stability"
            stability_governance_trajectory_trigger = "trust_stability_recenter"
            stability_governance_trajectory_notes.append(
                "trust_recenter_keeps_stability_line_in_rebuild_mode"
            )
        elif stability_governance_trigger == "continuity_stability_recenter":
            stability_governance_trajectory_target = "reanchor_before_stability"
            stability_governance_trajectory_trigger = (
                "continuity_stability_recenter"
            )
            stability_governance_trajectory_notes.append(
                "continuity_recenter_keeps_stability_line_in_reanchor_mode"
            )
        elif stability_governance_trigger == "repair_stability_recenter":
            stability_governance_trajectory_target = "repair_scaffold_before_stability"
            stability_governance_trajectory_trigger = "repair_stability_recenter"
            stability_governance_trajectory_notes.append(
                "repair_recenter_keeps_stability_line_in_repair_scaffold_mode"
            )
        else:
            stability_governance_trajectory_target = (
                "bounded_progress_reset_before_stability"
            )
            stability_governance_trajectory_trigger = "progress_stability_recenter"
            stability_governance_trajectory_notes.append(
                "progress_recenter_keeps_stability_line_in_bounded_reset_mode"
            )
    elif stability_governance_status == "watch":
        stability_governance_trajectory_status = "watch"
        if stability_governance_trigger == "safety_stability_watch":
            stability_governance_trajectory_target = "safety_buffered_stability_watch"
            stability_governance_trajectory_trigger = "safety_stability_watch"
            stability_governance_trajectory_notes.append(
                "safety_watch_keeps_stability_line_careful"
            )
        elif stability_governance_trigger == "relational_stability_watch":
            stability_governance_trajectory_target = (
                "relational_buffered_stability_watch"
            )
            stability_governance_trajectory_trigger = "relational_stability_watch"
            stability_governance_trajectory_notes.append(
                "relational_watch_keeps_stability_line_buffered"
            )
        elif stability_governance_trigger == "pacing_stability_watch":
            stability_governance_trajectory_target = "slow_stability_watch"
            stability_governance_trajectory_trigger = "pacing_stability_watch"
            stability_governance_trajectory_notes.append(
                "pacing_watch_keeps_stability_line_slow"
            )
        elif stability_governance_trigger == "trust_stability_watch":
            stability_governance_trajectory_target = "trust_buffered_stability_watch"
            stability_governance_trajectory_trigger = "trust_stability_watch"
            stability_governance_trajectory_notes.append(
                "trust_watch_keeps_stability_line_buffered"
            )
        elif stability_governance_trigger == "repair_stability_watch":
            stability_governance_trajectory_target = (
                "repair_buffered_stability_watch"
            )
            stability_governance_trajectory_trigger = "repair_stability_watch"
            stability_governance_trajectory_notes.append(
                "repair_watch_keeps_stability_line_scaffolded"
            )
        elif stability_governance_trigger == "continuity_stability_watch":
            stability_governance_trajectory_target = "reanchored_stability_watch"
            stability_governance_trajectory_trigger = "continuity_stability_watch"
            stability_governance_trajectory_notes.append(
                "continuity_watch_keeps_stability_line_reanchored"
            )
        elif stability_governance_trigger == "progress_stability_watch":
            stability_governance_trajectory_target = (
                "bounded_progress_stability_watch"
            )
            stability_governance_trajectory_trigger = "progress_stability_watch"
            stability_governance_trajectory_notes.append(
                "progress_watch_keeps_stability_line_bounded"
            )
        else:
            stability_governance_trajectory_target = "attuned_stability_watch"
            stability_governance_trajectory_trigger = "attunement_stability_watch"
            stability_governance_trajectory_notes.append(
                "attunement_watch_keeps_stability_line_relationally_tuned"
            )
    else:
        stability_governance_trajectory_status = "stable"
        stability_governance_trajectory_target = (
            "steady_bounded_relational_stability"
        )
        stability_governance_trajectory_trigger = "stability_governance_stable"
        stability_governance_trajectory_notes.append(
            "stability_line_is_holding_steady_and_bounded"
        )

    version_migration_notes: list[str] = []
    if (
        (response_post_audit and response_post_audit.status == "revise")
        or (
            runtime_quality_doctor_report
            and runtime_quality_doctor_report.status == "revise"
        )
    ):
        version_migration_status = "revise"
        version_migration_scope = "hold_rebuild"
        version_migration_trigger = "quality_drift_requires_hold"
        version_migration_notes.append("quality_revision_blocks_stable_projection_cutover")
    elif identity_trajectory_status == "recenter":
        version_migration_status = "revise"
        version_migration_scope = "hold_rebuild"
        version_migration_trigger = "identity_recenter_requires_hold"
        version_migration_notes.append("identity_needs_recentering_before_version_cutover")
    elif user_model_evolution_status == "revise":
        version_migration_status = "revise"
        version_migration_scope = "hold_rebuild"
        version_migration_trigger = "user_model_recalibration_requires_hold"
        version_migration_notes.append("user_model_shift_requires_recalibration_before_migration")
    elif repair_assessment.repair_needed and emotional_debt_status == "elevated":
        version_migration_status = "revise"
        version_migration_scope = "hold_rebuild"
        version_migration_trigger = "repair_load_requires_hold"
        version_migration_notes.append("repair_pressure_and_debt_make_projection_cutover_risky")
    elif filtered_recall_count > 0:
        version_migration_status = "watch"
        version_migration_scope = "cautious_rebuild"
        version_migration_trigger = "context_drift_requires_hold"
        version_migration_notes.append("filtered_recall_signals_context_mismatch_for_rebuild")
    elif growth_transition_status in {"watch", "redirect"}:
        version_migration_status = "watch"
        version_migration_scope = "cautious_rebuild"
        version_migration_trigger = "growth_transition_hold"
        version_migration_notes.append("growth_transition_is_not_stable_enough_for_version_cutover")
    elif turn_index <= 2 and recall_count == 0:
        version_migration_status = "watch"
        version_migration_scope = "cautious_rebuild"
        version_migration_trigger = "low_continuity_sample"
        version_migration_notes.append("session_history_is_still_thin_for_rebuild_confidence")
    else:
        version_migration_status = "pass"
        version_migration_scope = "stable_rebuild_ready"
        version_migration_trigger = "projection_rebuild_ready"
        if recall_count > 0:
            version_migration_notes.append("continuity_backed_state_supports_projection_rebuild")
        if turn_index >= 2:
            version_migration_notes.append("session_history_is_deep_enough_for_version_cutover")
        if strategy_audit_status == "pass":
            version_migration_notes.append("strategy_audit_is_stable_for_replay")

    version_migration_trajectory_notes: list[str] = []
    if version_migration_status == "revise":
        version_migration_trajectory_status = "hold"
        if version_migration_trigger == "quality_drift_requires_hold":
            version_migration_trajectory_target = "hold_rebuild"
            version_migration_trajectory_trigger = "quality_hold_required"
            version_migration_trajectory_notes.append(
                "quality_drift_keeps_migration_line_in_hold_state"
            )
        elif version_migration_trigger == "identity_recenter_requires_hold":
            version_migration_trajectory_target = "hold_rebuild"
            version_migration_trajectory_trigger = "identity_hold_required"
            version_migration_trajectory_notes.append(
                "identity_recenter_keeps_migration_line_on_hold"
            )
        elif version_migration_trigger == "user_model_recalibration_requires_hold":
            version_migration_trajectory_target = "hold_rebuild"
            version_migration_trajectory_trigger = "user_model_hold_required"
            version_migration_trajectory_notes.append(
                "user_model_recalibration_keeps_migration_line_on_hold"
            )
        else:
            version_migration_trajectory_target = "hold_rebuild"
            version_migration_trajectory_trigger = "migration_hold_required"
            version_migration_trajectory_notes.append(
                "migration_line_requires_hold_under_current_session_pressure"
            )
    elif version_migration_status == "watch":
        version_migration_trajectory_status = "watch"
        if version_migration_trigger == "context_drift_requires_hold":
            version_migration_trajectory_target = "cautious_rebuild"
            version_migration_trajectory_trigger = "context_drift_rebuild_watch"
            version_migration_trajectory_notes.append(
                "context_drift_keeps_migration_line_under_cautious_watch"
            )
        elif version_migration_trigger == "growth_transition_hold":
            version_migration_trajectory_target = "cautious_rebuild"
            version_migration_trajectory_trigger = "growth_transition_rebuild_watch"
            version_migration_trajectory_notes.append(
                "growth_transition_instability_keeps_migration_line_under_watch"
            )
        elif version_migration_trigger == "low_continuity_sample":
            version_migration_trajectory_target = "cautious_rebuild"
            version_migration_trajectory_trigger = "thin_history_rebuild_watch"
            version_migration_trajectory_notes.append(
                "thin_history_keeps_migration_line_in_cautious_mode"
            )
        else:
            version_migration_trajectory_target = "cautious_rebuild"
            version_migration_trajectory_trigger = "migration_watch_active"
            version_migration_trajectory_notes.append(
                "migration_line_is_not_yet_stable_enough_for_full_cutover"
            )
    else:
        version_migration_trajectory_status = "stable"
        version_migration_trajectory_target = "stable_rebuild_ready"
        version_migration_trajectory_trigger = "migration_line_stable"
        version_migration_trajectory_notes.append(
            "migration_line_is_holding_stable_for_rebuild"
        )

    review_focus = _compact(
        debt_signals
        + emotional_debt_trajectory_notes
        + identity_trajectory_notes
        + strategy_audit_notes
        + strategy_audit_trajectory_notes
        + strategy_supervision_notes
        + strategy_supervision_trajectory_notes
        + moral_notes
        + moral_trajectory_notes
        + user_model_evolution_notes
        + user_model_trajectory_notes
        + expectation_calibration_notes
        + expectation_calibration_trajectory_notes
        + dependency_governance_notes
        + dependency_governance_trajectory_notes
        + autonomy_governance_notes
        + autonomy_governance_trajectory_notes
        + boundary_governance_notes
        + boundary_governance_trajectory_notes
        + support_governance_notes
        + support_governance_trajectory_notes
        + continuity_governance_notes
        + continuity_governance_trajectory_notes
        + repair_governance_notes
        + repair_governance_trajectory_notes
        + attunement_governance_notes
        + attunement_governance_trajectory_notes
        + trust_governance_notes
        + trust_governance_trajectory_notes
        + clarity_governance_notes
        + clarity_governance_trajectory_notes
        + pacing_governance_notes
        + pacing_governance_trajectory_notes
        + commitment_governance_notes
        + commitment_governance_trajectory_notes
        + disclosure_governance_notes
        + disclosure_governance_trajectory_notes
        + reciprocity_governance_notes
        + reciprocity_governance_trajectory_notes
        + pressure_governance_notes
        + pressure_governance_trajectory_notes
        + relational_governance_notes
        + relational_governance_trajectory_notes
        + safety_governance_notes
        + safety_governance_trajectory_notes
        + progress_governance_notes
        + progress_governance_trajectory_notes
        + stability_governance_notes
        + stability_governance_trajectory_notes
        + growth_transition_notes
        + growth_transition_trajectory_notes
        + version_migration_notes
        + version_migration_trajectory_notes
        + user_needs
        + user_preferences
        + [growth_signal],
        limit=6,
    )

    return System3Snapshot(
        triggered_turn_index=turn_index,
        identity_anchor=identity_anchor,
        identity_consistency=identity_consistency,
        identity_confidence=identity_confidence,
        identity_trajectory_status=identity_trajectory_status,
        identity_trajectory_target=identity_trajectory_target,
        identity_trajectory_trigger=identity_trajectory_trigger,
        identity_trajectory_notes=_compact(identity_trajectory_notes, limit=6),
        growth_stage=growth_stage,
        growth_signal=growth_signal,
        user_model_confidence=user_model_confidence,
        user_needs=_compact(user_needs, limit=5),
        user_preferences=_compact(user_preferences, limit=5),
        emotional_debt_status=emotional_debt_status,
        emotional_debt_score=emotional_debt_score,
        debt_signals=_compact(debt_signals, limit=6),
        emotional_debt_trajectory_status=emotional_debt_trajectory_status,
        emotional_debt_trajectory_target=emotional_debt_trajectory_target,
        emotional_debt_trajectory_trigger=emotional_debt_trajectory_trigger,
        emotional_debt_trajectory_notes=_compact(
            emotional_debt_trajectory_notes,
            limit=6,
        ),
        strategy_audit_status=strategy_audit_status,
        strategy_fit=strategy_fit,
        strategy_audit_notes=_compact(strategy_audit_notes, limit=6),
        strategy_audit_trajectory_status=strategy_audit_trajectory_status,
        strategy_audit_trajectory_target=strategy_audit_trajectory_target,
        strategy_audit_trajectory_trigger=strategy_audit_trajectory_trigger,
        strategy_audit_trajectory_notes=_compact(
            strategy_audit_trajectory_notes,
            limit=6,
        ),
        strategy_supervision_status=strategy_supervision_status,
        strategy_supervision_mode=strategy_supervision_mode,
        strategy_supervision_trigger=strategy_supervision_trigger,
        strategy_supervision_notes=_compact(strategy_supervision_notes, limit=6),
        strategy_supervision_trajectory_status=(
            strategy_supervision_trajectory_status
        ),
        strategy_supervision_trajectory_target=(
            strategy_supervision_trajectory_target
        ),
        strategy_supervision_trajectory_trigger=(
            strategy_supervision_trajectory_trigger
        ),
        strategy_supervision_trajectory_notes=_compact(
            strategy_supervision_trajectory_notes,
            limit=6,
        ),
        moral_reasoning_status=moral_reasoning_status,
        moral_posture=moral_posture,
        moral_conflict=moral_conflict,
        moral_principles=_compact(moral_principles, limit=6),
        moral_notes=_compact(moral_notes, limit=6),
        moral_trajectory_status=moral_trajectory_status,
        moral_trajectory_target=moral_trajectory_target,
        moral_trajectory_trigger=moral_trajectory_trigger,
        moral_trajectory_notes=_compact(moral_trajectory_notes, limit=6),
        user_model_evolution_status=user_model_evolution_status,
        user_model_revision_mode=user_model_revision_mode,
        user_model_shift_signal=user_model_shift_signal,
        user_model_evolution_notes=_compact(user_model_evolution_notes, limit=6),
        user_model_trajectory_status=user_model_trajectory_status,
        user_model_trajectory_target=user_model_trajectory_target,
        user_model_trajectory_trigger=user_model_trajectory_trigger,
        user_model_trajectory_notes=_compact(user_model_trajectory_notes, limit=6),
        expectation_calibration_status=expectation_calibration_status,
        expectation_calibration_target=expectation_calibration_target,
        expectation_calibration_trigger=expectation_calibration_trigger,
        expectation_calibration_notes=_compact(
            expectation_calibration_notes,
            limit=6,
        ),
        expectation_calibration_trajectory_status=(
            expectation_calibration_trajectory_status
        ),
        expectation_calibration_trajectory_target=(
            expectation_calibration_trajectory_target
        ),
        expectation_calibration_trajectory_trigger=(
            expectation_calibration_trajectory_trigger
        ),
        expectation_calibration_trajectory_notes=_compact(
            expectation_calibration_trajectory_notes,
            limit=6,
        ),
        dependency_governance_status=dependency_governance_status,
        dependency_governance_target=dependency_governance_target,
        dependency_governance_trigger=dependency_governance_trigger,
        dependency_governance_notes=_compact(dependency_governance_notes, limit=6),
        dependency_governance_trajectory_status=(
            dependency_governance_trajectory_status
        ),
        dependency_governance_trajectory_target=(
            dependency_governance_trajectory_target
        ),
        dependency_governance_trajectory_trigger=(
            dependency_governance_trajectory_trigger
        ),
        dependency_governance_trajectory_notes=_compact(
            dependency_governance_trajectory_notes,
            limit=6,
        ),
        autonomy_governance_status=autonomy_governance_status,
        autonomy_governance_target=autonomy_governance_target,
        autonomy_governance_trigger=autonomy_governance_trigger,
        autonomy_governance_notes=_compact(autonomy_governance_notes, limit=6),
        autonomy_governance_trajectory_status=(
            autonomy_governance_trajectory_status
        ),
        autonomy_governance_trajectory_target=(
            autonomy_governance_trajectory_target
        ),
        autonomy_governance_trajectory_trigger=(
            autonomy_governance_trajectory_trigger
        ),
        autonomy_governance_trajectory_notes=_compact(
            autonomy_governance_trajectory_notes,
            limit=6,
        ),
        boundary_governance_status=boundary_governance_status,
        boundary_governance_target=boundary_governance_target,
        boundary_governance_trigger=boundary_governance_trigger,
        boundary_governance_notes=_compact(boundary_governance_notes, limit=6),
        boundary_governance_trajectory_status=(
            boundary_governance_trajectory_status
        ),
        boundary_governance_trajectory_target=(
            boundary_governance_trajectory_target
        ),
        boundary_governance_trajectory_trigger=(
            boundary_governance_trajectory_trigger
        ),
        boundary_governance_trajectory_notes=_compact(
            boundary_governance_trajectory_notes,
            limit=6,
        ),
        support_governance_status=support_governance_status,
        support_governance_target=support_governance_target,
        support_governance_trigger=support_governance_trigger,
        support_governance_notes=_compact(support_governance_notes, limit=6),
        support_governance_trajectory_status=(
            support_governance_trajectory_status
        ),
        support_governance_trajectory_target=(
            support_governance_trajectory_target
        ),
        support_governance_trajectory_trigger=(
            support_governance_trajectory_trigger
        ),
        support_governance_trajectory_notes=_compact(
            support_governance_trajectory_notes,
            limit=6,
        ),
        continuity_governance_status=continuity_governance_status,
        continuity_governance_target=continuity_governance_target,
        continuity_governance_trigger=continuity_governance_trigger,
        continuity_governance_notes=_compact(
            continuity_governance_notes,
            limit=6,
        ),
        continuity_governance_trajectory_status=(
            continuity_governance_trajectory_status
        ),
        continuity_governance_trajectory_target=(
            continuity_governance_trajectory_target
        ),
        continuity_governance_trajectory_trigger=(
            continuity_governance_trajectory_trigger
        ),
        continuity_governance_trajectory_notes=_compact(
            continuity_governance_trajectory_notes,
            limit=6,
        ),
        repair_governance_status=repair_governance_status,
        repair_governance_target=repair_governance_target,
        repair_governance_trigger=repair_governance_trigger,
        repair_governance_notes=_compact(
            repair_governance_notes,
            limit=6,
        ),
        repair_governance_trajectory_status=repair_governance_trajectory_status,
        repair_governance_trajectory_target=repair_governance_trajectory_target,
        repair_governance_trajectory_trigger=repair_governance_trajectory_trigger,
        repair_governance_trajectory_notes=_compact(
            repair_governance_trajectory_notes,
            limit=6,
        ),
        attunement_governance_status=attunement_governance_status,
        attunement_governance_target=attunement_governance_target,
        attunement_governance_trigger=attunement_governance_trigger,
        attunement_governance_notes=_compact(
            attunement_governance_notes,
            limit=6,
        ),
        attunement_governance_trajectory_status=attunement_governance_trajectory_status,
        attunement_governance_trajectory_target=attunement_governance_trajectory_target,
        attunement_governance_trajectory_trigger=attunement_governance_trajectory_trigger,
        attunement_governance_trajectory_notes=_compact(
            attunement_governance_trajectory_notes,
            limit=6,
        ),
        trust_governance_status=trust_governance_status,
        trust_governance_target=trust_governance_target,
        trust_governance_trigger=trust_governance_trigger,
        trust_governance_notes=_compact(
            trust_governance_notes,
            limit=6,
        ),
        trust_governance_trajectory_status=trust_governance_trajectory_status,
        trust_governance_trajectory_target=trust_governance_trajectory_target,
        trust_governance_trajectory_trigger=trust_governance_trajectory_trigger,
        trust_governance_trajectory_notes=_compact(
            trust_governance_trajectory_notes,
            limit=6,
        ),
        clarity_governance_status=clarity_governance_status,
        clarity_governance_target=clarity_governance_target,
        clarity_governance_trigger=clarity_governance_trigger,
        clarity_governance_notes=_compact(
            clarity_governance_notes,
            limit=6,
        ),
        clarity_governance_trajectory_status=clarity_governance_trajectory_status,
        clarity_governance_trajectory_target=clarity_governance_trajectory_target,
        clarity_governance_trajectory_trigger=clarity_governance_trajectory_trigger,
        clarity_governance_trajectory_notes=_compact(
            clarity_governance_trajectory_notes,
            limit=6,
        ),
        pacing_governance_status=pacing_governance_status,
        pacing_governance_target=pacing_governance_target,
        pacing_governance_trigger=pacing_governance_trigger,
        pacing_governance_notes=_compact(
            pacing_governance_notes,
            limit=6,
        ),
        pacing_governance_trajectory_status=pacing_governance_trajectory_status,
        pacing_governance_trajectory_target=pacing_governance_trajectory_target,
        pacing_governance_trajectory_trigger=pacing_governance_trajectory_trigger,
        pacing_governance_trajectory_notes=_compact(
            pacing_governance_trajectory_notes,
            limit=6,
        ),
        commitment_governance_status=commitment_governance_status,
        commitment_governance_target=commitment_governance_target,
        commitment_governance_trigger=commitment_governance_trigger,
        commitment_governance_notes=_compact(
            commitment_governance_notes,
            limit=6,
        ),
        commitment_governance_trajectory_status=(
            commitment_governance_trajectory_status
        ),
        commitment_governance_trajectory_target=(
            commitment_governance_trajectory_target
        ),
        commitment_governance_trajectory_trigger=(
            commitment_governance_trajectory_trigger
        ),
        commitment_governance_trajectory_notes=_compact(
            commitment_governance_trajectory_notes,
            limit=6,
        ),
        disclosure_governance_status=disclosure_governance_status,
        disclosure_governance_target=disclosure_governance_target,
        disclosure_governance_trigger=disclosure_governance_trigger,
        disclosure_governance_notes=_compact(
            disclosure_governance_notes,
            limit=6,
        ),
        disclosure_governance_trajectory_status=(
            disclosure_governance_trajectory_status
        ),
        disclosure_governance_trajectory_target=(
            disclosure_governance_trajectory_target
        ),
        disclosure_governance_trajectory_trigger=(
            disclosure_governance_trajectory_trigger
        ),
        disclosure_governance_trajectory_notes=_compact(
            disclosure_governance_trajectory_notes,
            limit=6,
        ),
        reciprocity_governance_status=reciprocity_governance_status,
        reciprocity_governance_target=reciprocity_governance_target,
        reciprocity_governance_trigger=reciprocity_governance_trigger,
        reciprocity_governance_notes=_compact(
            reciprocity_governance_notes,
            limit=6,
        ),
        reciprocity_governance_trajectory_status=(
            reciprocity_governance_trajectory_status
        ),
        reciprocity_governance_trajectory_target=(
            reciprocity_governance_trajectory_target
        ),
        reciprocity_governance_trajectory_trigger=(
            reciprocity_governance_trajectory_trigger
        ),
        reciprocity_governance_trajectory_notes=_compact(
            reciprocity_governance_trajectory_notes,
            limit=6,
        ),
        pressure_governance_status=pressure_governance_status,
        pressure_governance_target=pressure_governance_target,
        pressure_governance_trigger=pressure_governance_trigger,
        pressure_governance_notes=_compact(
            pressure_governance_notes,
            limit=6,
        ),
        pressure_governance_trajectory_status=(
            pressure_governance_trajectory_status
        ),
        pressure_governance_trajectory_target=(
            pressure_governance_trajectory_target
        ),
        pressure_governance_trajectory_trigger=(
            pressure_governance_trajectory_trigger
        ),
        pressure_governance_trajectory_notes=_compact(
            pressure_governance_trajectory_notes,
            limit=6,
        ),
        relational_governance_status=relational_governance_status,
        relational_governance_target=relational_governance_target,
        relational_governance_trigger=relational_governance_trigger,
        relational_governance_notes=_compact(
            relational_governance_notes,
            limit=6,
        ),
        relational_governance_trajectory_status=(
            relational_governance_trajectory_status
        ),
        relational_governance_trajectory_target=(
            relational_governance_trajectory_target
        ),
        relational_governance_trajectory_trigger=(
            relational_governance_trajectory_trigger
        ),
        relational_governance_trajectory_notes=_compact(
            relational_governance_trajectory_notes,
            limit=6,
        ),
        safety_governance_status=safety_governance_status,
        safety_governance_target=safety_governance_target,
        safety_governance_trigger=safety_governance_trigger,
        safety_governance_notes=_compact(
            safety_governance_notes,
            limit=6,
        ),
        safety_governance_trajectory_status=safety_governance_trajectory_status,
        safety_governance_trajectory_target=safety_governance_trajectory_target,
        safety_governance_trajectory_trigger=safety_governance_trajectory_trigger,
        safety_governance_trajectory_notes=_compact(
            safety_governance_trajectory_notes,
            limit=6,
        ),
        progress_governance_status=progress_governance_status,
        progress_governance_target=progress_governance_target,
        progress_governance_trigger=progress_governance_trigger,
        progress_governance_notes=_compact(
            progress_governance_notes,
            limit=6,
        ),
        progress_governance_trajectory_status=(
            progress_governance_trajectory_status
        ),
        progress_governance_trajectory_target=(
            progress_governance_trajectory_target
        ),
        progress_governance_trajectory_trigger=(
            progress_governance_trajectory_trigger
        ),
        progress_governance_trajectory_notes=_compact(
            progress_governance_trajectory_notes,
            limit=6,
        ),
        stability_governance_status=stability_governance_status,
        stability_governance_target=stability_governance_target,
        stability_governance_trigger=stability_governance_trigger,
        stability_governance_notes=_compact(
            stability_governance_notes,
            limit=6,
        ),
        stability_governance_trajectory_status=(
            stability_governance_trajectory_status
        ),
        stability_governance_trajectory_target=(
            stability_governance_trajectory_target
        ),
        stability_governance_trajectory_trigger=(
            stability_governance_trajectory_trigger
        ),
        stability_governance_trajectory_notes=_compact(
            stability_governance_trajectory_notes,
            limit=6,
        ),
        growth_transition_status=growth_transition_status,
        growth_transition_target=growth_transition_target,
        growth_transition_trigger=growth_transition_trigger,
        growth_transition_readiness=round(growth_transition_readiness, 3),
        growth_transition_notes=_compact(growth_transition_notes, limit=6),
        growth_transition_trajectory_status=growth_transition_trajectory_status,
        growth_transition_trajectory_target=growth_transition_trajectory_target,
        growth_transition_trajectory_trigger=growth_transition_trajectory_trigger,
        growth_transition_trajectory_notes=_compact(
            growth_transition_trajectory_notes,
            limit=6,
        ),
        version_migration_status=version_migration_status,
        version_migration_scope=version_migration_scope,
        version_migration_trigger=version_migration_trigger,
        version_migration_notes=_compact(version_migration_notes, limit=6),
        version_migration_trajectory_status=version_migration_trajectory_status,
        version_migration_trajectory_target=version_migration_trajectory_target,
        version_migration_trajectory_trigger=version_migration_trajectory_trigger,
        version_migration_trajectory_notes=_compact(
            version_migration_trajectory_notes,
            limit=6,
        ),
        review_focus=review_focus,
    )


