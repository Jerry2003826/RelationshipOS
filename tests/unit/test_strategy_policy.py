from relationship_os.application.analyzers.strategy import build_policy_gate
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    KnowledgeBoundaryDecision,
    PrivateJudgment,
    RelationshipState,
    RepairAssessment,
)


def _question_context() -> ContextFrame:
    return ContextFrame(
        dialogue_act="question",
        bid_signal="advice_request",
        common_ground=["study plan"],
        appraisal="neutral",
        topic="study",
        attention="steady",
    )


def _low_risk_relationship() -> RelationshipState:
    return RelationshipState(
        r_vector={"trust": 0.7},
        tom_inference="user wants bounded practical advice",
        psychological_safety=0.75,
        emotional_contagion="steady",
        turbulence_risk="low",
        tipping_point_risk="low",
        dependency_risk="low",
    )


def _no_repair() -> RepairAssessment:
    return RepairAssessment(
        repair_needed=False,
        rupture_type="none",
        severity="low",
        urgency="low",
        attunement_gap=False,
    )


def _private_judgment() -> PrivateJudgment:
    return PrivateJudgment(
        summary="The user asks an answerable practical question.",
        rationale="No safety or knowledge boundary is active.",
        confidence=0.82,
    )


def test_answerable_question_does_not_force_clarify_path() -> None:
    gate = build_policy_gate(
        context_frame=_question_context(),
        relationship_state=_low_risk_relationship(),
        repair_assessment=_no_repair(),
        knowledge_boundary_decision=KnowledgeBoundaryDecision(
            decision="answer_directly",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="high",
            rationale="Current context is sufficient for a bounded response.",
        ),
        confidence_assessment=ConfidenceAssessment(
            level="high",
            score=0.82,
            reason="The question is concrete enough to answer directly.",
            response_mode="direct",
        ),
        private_judgment=_private_judgment(),
    )

    assert gate.selected_path == "reflect_and_progress"
    assert gate.regulation_mode == "steady"


def test_missing_context_question_still_requires_clarification() -> None:
    gate = build_policy_gate(
        context_frame=_question_context(),
        relationship_state=_low_risk_relationship(),
        repair_assessment=_no_repair(),
        knowledge_boundary_decision=KnowledgeBoundaryDecision(
            decision="clarify_before_answer",
            boundary_type="missing_context",
            can_answer=False,
            should_disclose_uncertainty=True,
            confidence_level="medium",
            rationale="Key variables are missing.",
            missing_information=["which deadline matters most"],
        ),
        confidence_assessment=ConfidenceAssessment(
            level="medium",
            score=0.62,
            reason="More context is needed before a reliable answer.",
            response_mode="clarify",
            needs_clarification=True,
        ),
        private_judgment=_private_judgment(),
    )

    assert gate.selected_path == "clarify_then_answer"
    assert gate.regulation_mode == "clarify"
