"""L7 dramaturgical engine: policy gate, strategy decision, rehearsal."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import (
    _compact,
    _should_force_diversity_exploration,
    _strategy_alternatives,
    _strategy_entropy,
)
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    KnowledgeBoundaryDecision,
    PolicyGateDecision,
    PrivateJudgment,
    RehearsalResult,
    RelationshipState,
    RepairAssessment,
    StrategyDecision,
)


def build_policy_gate(
    *,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    confidence_assessment: ConfidenceAssessment,
    private_judgment: PrivateJudgment,
) -> PolicyGateDecision:
    safety_flags: list[str] = []
    red_line_status = "clear"
    timing_mode = "immediate"
    regulation_mode = "steady"
    empowerment_risk = "low"
    selected_path = "reflect_and_progress"

    if relationship_state.dependency_risk == "elevated":
        red_line_status = "boundary_sensitive"
        empowerment_risk = "guarded"
        safety_flags.append("dependency_boundary")

    if repair_assessment.severity == "high":
        timing_mode = "stabilize_first"
        regulation_mode = "repair"
        selected_path = "repair_then_progress"
        empowerment_risk = "guarded"
        safety_flags.append("repair_pressure")
    elif repair_assessment.severity == "medium":
        timing_mode = "watchful"
        safety_flags.append("repair_watch")

    if confidence_assessment.response_mode == "calibrated":
        regulation_mode = "calibrated"
        selected_path = "answer_with_uncertainty"
        empowerment_risk = "guarded"
        safety_flags.append("uncertainty_disclosure")
    elif confidence_assessment.response_mode == "clarify":
        regulation_mode = "clarify"
        selected_path = "clarify_then_answer"
        empowerment_risk = "guarded"
        safety_flags.append("clarification_required")

    if knowledge_boundary_decision.decision == "support_with_boundary":
        red_line_status = "boundary_sensitive"
        regulation_mode = "boundary_support"
        selected_path = "support_with_boundary"
        empowerment_risk = "guarded"
        safety_flags.append("relational_safety")
    elif knowledge_boundary_decision.decision == "clarify_before_answer":
        regulation_mode = "clarify"
        selected_path = "clarify_then_answer"
    elif knowledge_boundary_decision.decision == "answer_with_uncertainty":
        regulation_mode = "calibrated"
        selected_path = "answer_with_uncertainty"

    if (
        selected_path == "reflect_and_progress"
        and context_frame.dialogue_act == "question"
    ):
        selected_path = "clarify_then_answer"
        regulation_mode = "clarify"

    if selected_path == "reflect_and_progress" and context_frame.appraisal == "negative":
        timing_mode = "watchful"
        safety_flags.append("emotional_load")

    return PolicyGateDecision(
        selected_path=selected_path,
        red_line_status=red_line_status,
        timing_mode=timing_mode,
        regulation_mode=regulation_mode,
        empowerment_risk=empowerment_risk,
        safe_to_proceed=True,
        rationale=private_judgment.summary,
        safety_flags=_compact(safety_flags, limit=5),
    )


def build_strategy_decision(
    *,
    policy_gate: PolicyGateDecision,
    private_judgment: PrivateJudgment,
    context_frame: ContextFrame,
    repair_assessment: RepairAssessment,
    confidence_assessment: ConfidenceAssessment,
    relationship_state: RelationshipState,
    strategy_history: list[str] | None = None,
) -> StrategyDecision:
    recent_history = [item for item in (strategy_history or []) if item][-4:]
    recent_counts: dict[str, int] = {}
    for item in recent_history:
        recent_counts[item] = recent_counts.get(item, 0) + 1
    entropy = _strategy_entropy(recent_counts)
    selected_strategy = policy_gate.selected_path
    source_strategy = selected_strategy
    diversity_status = "stable"
    explored_strategy = False
    alternatives_considered = _strategy_alternatives(
        selected_strategy=selected_strategy,
        context_frame=context_frame,
        repair_assessment=repair_assessment,
        confidence_assessment=confidence_assessment,
        relationship_state=relationship_state,
    )

    if _should_force_diversity_exploration(
        selected_strategy=selected_strategy,
        recent_counts=recent_counts,
        entropy=entropy,
        alternatives_considered=alternatives_considered,
    ):
        selected_strategy = alternatives_considered[0]
        diversity_status = "intervened"
        explored_strategy = True
    elif recent_history and entropy < 0.8 and recent_counts.get(selected_strategy, 0) >= 3:
        diversity_status = "watch"

    rationale = f"{private_judgment.summary}; gate={policy_gate.regulation_mode}"
    if explored_strategy:
        rationale += f"; diversity_explore={selected_strategy}"
    elif diversity_status == "watch":
        rationale += "; diversity_watch=low_entropy"

    return StrategyDecision(
        strategy=selected_strategy,
        rationale=rationale,
        safety_ok=policy_gate.safe_to_proceed,
        source_strategy=source_strategy,
        diversity_status=diversity_status,
        diversity_entropy=entropy,
        explored_strategy=explored_strategy,
        recent_strategy_counts=recent_counts,
        alternatives_considered=alternatives_considered,
    )


def build_rehearsal_result(
    *,
    strategy_decision: StrategyDecision,
    policy_gate: PolicyGateDecision,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
) -> RehearsalResult:
    predicted_user_impact = "forward_progress"
    projected_risk_level = "low"
    likely_user_response = "The user is likely to accept the next step and continue."
    failure_modes: list[str] = []
    recommended_adjustments: list[str] = []

    if strategy_decision.strategy == "repair_then_progress":
        predicted_user_impact = "stabilizing_repair"
        projected_risk_level = "medium"
        likely_user_response = "The user may feel seen first, then re-engage with progress."
        failure_modes.append("over-indexes_on_emotion")
        recommended_adjustments.append("transition from repair into one concrete next step")
    elif strategy_decision.strategy == "clarify_then_answer":
        predicted_user_impact = "alignment_seeking"
        projected_risk_level = "medium"
        likely_user_response = "The user may provide missing detail if clarification feels useful."
        failure_modes.append("feels_deflective")
        recommended_adjustments.append("explain why clarification helps before asking")
    elif strategy_decision.strategy == "answer_with_uncertainty":
        predicted_user_impact = "trust_preserving_calibration"
        projected_risk_level = "medium"
        likely_user_response = "The user may accept the limit if a bounded next step follows."
        failure_modes.append("sounds_evasive")
        recommended_adjustments.append("pair uncertainty with a practical next step")
    elif strategy_decision.strategy == "support_with_boundary":
        predicted_user_impact = "support_without_dependency"
        projected_risk_level = "high"
        likely_user_response = "The user may seek reassurance while testing the boundary."
        failure_modes.append("reinforces_dependency")
        recommended_adjustments.append("offer support without exclusivity cues")

    if policy_gate.red_line_status == "boundary_sensitive":
        projected_risk_level = "high"
        if "reinforces_dependency" not in failure_modes:
            failure_modes.append("reinforces_dependency")
        recommended_adjustments.append("keep the response collaborative rather than exclusive")
    if repair_assessment.severity == "high" and "over-indexes_on_emotion" not in failure_modes:
        failure_modes.append("misses_task_reentry")
        recommended_adjustments.append("end with one stabilizing action the user can take")
    if knowledge_boundary_decision.should_disclose_uncertainty:
        recommended_adjustments.append("state limits explicitly and avoid overclaiming")

    approved = projected_risk_level != "high" or strategy_decision.strategy in {
        "support_with_boundary",
        "repair_then_progress",
    }
    return RehearsalResult(
        predicted_user_impact=predicted_user_impact,
        projected_risk_level=projected_risk_level,
        likely_user_response=likely_user_response,
        failure_modes=_compact(failure_modes, limit=4),
        recommended_adjustments=_compact(recommended_adjustments, limit=4),
        approved=approved,
    )
