"""Expression planning and empowerment audit."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    EmpowermentAudit,
    ExpressionPlan,
    KnowledgeBoundaryDecision,
    PolicyGateDecision,
    RehearsalResult,
    RelationshipState,
    RepairPlan,
    StrategyDecision,
)


def build_expression_plan(
    strategy_decision: StrategyDecision,
    repair_plan: RepairPlan,
    rehearsal_result: RehearsalResult,
) -> ExpressionPlan:
    tone = "calm_supportive"
    goals = ["acknowledge context", "make next step explicit"]
    avoid = ["dependency_reinforcement"]
    if strategy_decision.strategy == "repair_then_progress":
        tone = "grounded_repair"
        goals = [
            "repair understanding",
            "stabilize emotion",
            "then move one step forward",
        ]
    if strategy_decision.strategy == "clarify_then_answer":
        tone = "clear_direct"
        goals = ["answer clearly", "reduce ambiguity"]
    if strategy_decision.strategy == "answer_with_uncertainty":
        tone = "calibrated_honest"
        goals = ["state the limit clearly", "offer a bounded next step"]
    if repair_plan.rupture_type == "boundary_risk":
        avoid.append("exclusive_attachment_cues")
    if "feels_deflective" in rehearsal_result.failure_modes:
        goals.append("explain why clarification helps")
    if "sounds_evasive" in rehearsal_result.failure_modes:
        avoid.append("evasive_tone")
    if "misses_task_reentry" in rehearsal_result.failure_modes:
        goals.append("end with one stabilizing action")
    return ExpressionPlan(
        tone=tone,
        goals=_compact(goals, limit=4),
        include_question=strategy_decision.strategy == "clarify_then_answer",
        avoid=_compact(avoid, limit=4),
    )


def build_empowerment_audit(
    *,
    policy_gate: PolicyGateDecision,
    relationship_state: RelationshipState,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    confidence_assessment: ConfidenceAssessment,
    expression_plan: ExpressionPlan,
    rehearsal_result: RehearsalResult,
) -> EmpowermentAudit:
    flagged_issues: list[str] = []
    recommended_adjustments: list[str] = []
    transparency_required = knowledge_boundary_decision.should_disclose_uncertainty
    dependency_safe = True

    if policy_gate.empowerment_risk == "guarded":
        flagged_issues.append("guarded_empowerment_risk")
    if relationship_state.dependency_risk == "elevated":
        flagged_issues.append("dependency_reinforcement_risk")
        dependency_safe = False
        recommended_adjustments.append("avoid framing the assistant as the only support")
    if transparency_required and expression_plan.tone != "calibrated_honest":
        flagged_issues.append("transparency_gap")
        recommended_adjustments.append("make uncertainty explicit in the response")
    if (
        confidence_assessment.needs_clarification
        and not expression_plan.include_question
    ):
        flagged_issues.append("missing_clarification_step")
        recommended_adjustments.append("ask one focused clarifying question")
    if rehearsal_result.projected_risk_level == "high":
        flagged_issues.append("high_rehearsal_risk")
        recommended_adjustments.extend(rehearsal_result.recommended_adjustments[:2])

    if len(flagged_issues) >= 3:
        status = "revise"
    elif flagged_issues:
        status = "caution"
    else:
        status = "pass"

    return EmpowermentAudit(
        status=status,
        empowerment_risk=policy_gate.empowerment_risk,
        transparency_required=transparency_required,
        dependency_safe=dependency_safe,
        flagged_issues=_compact(flagged_issues, limit=5),
        recommended_adjustments=_compact(recommended_adjustments, limit=5),
        approved=status != "revise",
    )
