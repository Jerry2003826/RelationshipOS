"""L5+L6 private judgment, confidence, knowledge boundary, memory bundle."""

from relationship_os.application.analyzers._utils import _clamp, _compact, _contains_any
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    KnowledgeBoundaryDecision,
    MemoryBundle,
    PrivateJudgment,
    RelationshipState,
    RepairAssessment,
    RepairPlan,
)


def build_confidence_assessment(
    *,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    user_message: str,
    recalled_memory: list[dict[str, object]] | None = None,
) -> ConfidenceAssessment:
    score = 0.74
    risk_flags: list[str] = []
    response_mode = "direct"

    if context_frame.dialogue_act == "question":
        score += 0.03
    if context_frame.attention == "high":
        score -= 0.08
        risk_flags.append("high_attention")
    elif context_frame.attention == "focused":
        score -= 0.03
        risk_flags.append("focused_attention")
    if context_frame.appraisal == "negative":
        score -= 0.06
        risk_flags.append("negative_appraisal")
    if repair_assessment.severity == "high":
        score -= 0.08
        risk_flags.append("repair_pressure")
        response_mode = "repair_first"
    elif repair_assessment.severity == "medium":
        score -= 0.03
        risk_flags.append("repair_watch")
    if relationship_state.dependency_risk == "elevated":
        score -= 0.06
        risk_flags.append("dependency_boundary")
    if context_frame.dialogue_act == "question" and not recalled_memory:
        score -= 0.05
        risk_flags.append("no_recalled_context")
    if _contains_any(
        user_message,
        english_tokens=["guarantee", "definitely", "certain", "predict", "forever"],
        chinese_tokens=["保证", "一定", "绝对", "预测", "永远", "肯定"],
    ):
        score -= 0.07
        risk_flags.append("certainty_request")
        response_mode = "calibrated"
    elif (
        context_frame.dialogue_act == "question"
        and not recalled_memory
        and context_frame.attention in {"focused", "high"}
    ):
        risk_flags.append("clarification_needed")
        response_mode = "clarify"

    score = _clamp(score)
    if score >= 0.78:
        level = "high"
    elif score >= 0.62:
        level = "medium"
    else:
        level = "low"

    should_disclose_uncertainty = response_mode == "calibrated" or score < 0.64
    needs_clarification = response_mode == "clarify"
    if response_mode == "repair_first":
        reason = "Repair pressure is high, so the system should slow down before answering."
    elif should_disclose_uncertainty:
        reason = "The request needs calibrated uncertainty rather than overclaiming."
    elif needs_clarification:
        reason = "The question needs more context before a confident answer."
    else:
        reason = "Current turn has enough bounded signal for a direct response."

    return ConfidenceAssessment(
        level=level,
        score=score,
        reason=reason,
        response_mode=response_mode,
        should_disclose_uncertainty=should_disclose_uncertainty,
        needs_clarification=needs_clarification,
        risk_flags=_compact(risk_flags, limit=5),
    )


def build_memory_bundle(
    *,
    transcript_messages: list[dict[str, str]],
    user_message: str,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
) -> MemoryBundle:
    recent_contents = [
        str(message.get("content", ""))
        for message in transcript_messages[-2:]
        if message.get("content")
    ]
    working_memory = _compact(recent_contents + [user_message], limit=3)

    episodic_sources = [
        f"{message.get('role', 'unknown')}: {message.get('content', '')}"
        for message in transcript_messages[-4:]
        if message.get("content")
    ]
    episodic_sources.append(f"user: {user_message}")

    semantic_memory = _compact(
        [
            f"topic:{context_frame.topic}",
            f"dialogue_act:{context_frame.dialogue_act}",
            f"appraisal:{context_frame.appraisal}",
            f"attention:{context_frame.attention}",
        ],
        limit=4,
    )
    relational_memory = _compact(
        [
            f"psychological_safety:{relationship_state.psychological_safety}",
            f"dependency_risk:{relationship_state.dependency_risk}",
            f"bid_signal:{context_frame.bid_signal}",
            f"turbulence_risk:{relationship_state.turbulence_risk}",
        ],
        limit=4,
    )
    reflective_memory = _compact(
        [
            (
                "User may need emotional regulation before action planning."
                if context_frame.appraisal == "negative"
                else "User is ready for direct forward progress."
            ),
            (
                "Boundary-aware support is important in this turn."
                if relationship_state.dependency_risk == "elevated"
                else "Maintain collaborative momentum."
            ),
        ],
        limit=3,
    )

    return MemoryBundle(
        working_memory=working_memory,
        episodic_memory=_compact(episodic_sources, limit=4),
        semantic_memory=semantic_memory,
        relational_memory=relational_memory,
        reflective_memory=reflective_memory,
    )


def build_knowledge_boundary_decision(
    *,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    confidence_assessment: ConfidenceAssessment,
    user_message: str,
    recalled_memory: list[dict[str, object]] | None = None,
) -> KnowledgeBoundaryDecision:
    uncertainty_trigger = confidence_assessment.should_disclose_uncertainty and (
        "certainty_request" in confidence_assessment.risk_flags
        or confidence_assessment.response_mode == "calibrated"
    )
    clarification_needed = confidence_assessment.needs_clarification
    relational_boundary = relationship_state.dependency_risk == "elevated" and _contains_any(
        user_message,
        english_tokens=["only you", "need you", "can't without you"],
        chinese_tokens=["只有你", "离不开你", "只能靠你"],
    )

    if uncertainty_trigger:
        return KnowledgeBoundaryDecision(
            decision="answer_with_uncertainty",
            boundary_type="uncertain_future",
            can_answer=False,
            should_disclose_uncertainty=True,
            confidence_level="guarded",
            rationale="The request asks for certainty or prediction beyond stable evidence.",
            missing_information=["verifiable future outcome"],
        )
    if clarification_needed:
        return KnowledgeBoundaryDecision(
            decision="clarify_before_answer",
            boundary_type="missing_context",
            can_answer=False,
            should_disclose_uncertainty=True,
            confidence_level=confidence_assessment.level,
            rationale="The question needs more concrete context before a reliable answer.",
            missing_information=[f"context about {context_frame.topic}"],
        )
    if relational_boundary:
        return KnowledgeBoundaryDecision(
            decision="support_with_boundary",
            boundary_type="relational_safety",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="high",
            rationale="The response should support the user without reinforcing exclusivity.",
            missing_information=[],
        )
    return KnowledgeBoundaryDecision(
        decision="answer_directly",
        boundary_type="none",
        can_answer=True,
        should_disclose_uncertainty=False,
        confidence_level=confidence_assessment.level,
        rationale="Current context is sufficient for a bounded response.",
        missing_information=[],
    )


def build_private_judgment(
    *,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    repair_assessment: RepairAssessment,
    repair_plan: RepairPlan,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    memory_bundle: MemoryBundle,
    confidence_assessment: ConfidenceAssessment,
    recalled_memory: list[dict[str, object]] | None = None,
) -> PrivateJudgment:
    summary = "The user mainly wants task progress."
    if repair_assessment.repair_needed:
        summary = "The user needs repair and regulation before pure task acceleration."
    elif knowledge_boundary_decision.decision == "answer_with_uncertainty":
        summary = "The user needs a bounded answer with explicit uncertainty."
    elif knowledge_boundary_decision.decision == "clarify_before_answer":
        summary = "The user is asking for specifics that need clarification first."
    elif context_frame.bid_signal == "connection_request":
        summary = "The user is asking for support plus forward motion."
    elif recalled_memory:
        summary = "The user is revisiting earlier context and expects continuity."

    rationale = (
        f"topic={context_frame.topic}; "
        f"bid={context_frame.bid_signal}; "
        f"repair={repair_assessment.rupture_type}; "
        f"boundary={knowledge_boundary_decision.boundary_type}; "
        f"confidence_mode={confidence_assessment.response_mode}; "
        f"working_memory={len(memory_bundle.working_memory)} items; "
        f"recall={len(recalled_memory or [])} items"
    )
    confidence = confidence_assessment.score
    if repair_assessment.urgency == "high":
        confidence = _clamp(confidence - 0.06)
    if knowledge_boundary_decision.should_disclose_uncertainty:
        confidence = _clamp(confidence - 0.04)

    return PrivateJudgment(
        summary=summary,
        rationale=rationale,
        confidence=confidence,
    )
