"""L2 relationship state engine and L3 rupture detection."""

from relationship_os.application.analyzers._constants import DEFAULT_R_VECTOR
from relationship_os.application.analyzers._utils import (
    _clamp,
    _compact,
    _contains_chinese,
)
from relationship_os.domain.contracts import (
    ContextFrame,
    RelationshipState,
    RepairAssessment,
    RepairPlan,
)


def build_relationship_state(
    *,
    context_frame: ContextFrame,
    previous_state: dict[str, object] | None,
    user_message: str,
) -> RelationshipState:
    previous_vector = DEFAULT_R_VECTOR
    if previous_state and isinstance(previous_state.get("r_vector"), dict):
        previous_vector = {
            key: float(value)
            for key, value in previous_state["r_vector"].items()
            if isinstance(value, (int, float))
        }
    r_vector = dict(DEFAULT_R_VECTOR)
    r_vector.update(previous_vector)

    if context_frame.dialogue_act == "appreciation":
        r_vector["trust"] = _clamp(r_vector["trust"] + 0.05)
        r_vector["warmth"] = _clamp(r_vector["warmth"] + 0.08)
        r_vector["reciprocity"] = _clamp(r_vector["reciprocity"] + 0.06)
    if context_frame.bid_signal == "connection_request":
        r_vector["openness"] = _clamp(r_vector["openness"] + 0.06)
        r_vector["engagement"] = _clamp(r_vector["engagement"] + 0.05)
        if context_frame.appraisal != "negative":
            r_vector["reciprocity"] = _clamp(r_vector["reciprocity"] + 0.03)
    if context_frame.appraisal == "negative":
        r_vector["stability"] = _clamp(r_vector["stability"] - 0.05)
        r_vector["reciprocity"] = _clamp(r_vector["reciprocity"] - 0.04)
    if "only you" in user_message.lower() or any(
        token in user_message for token in ["只有你", "离不开你", "只能靠你"]
    ):
        r_vector["dependence"] = _clamp(r_vector["dependence"] + 0.12)
        r_vector["reciprocity"] = _clamp(r_vector["reciprocity"] - 0.12)

    safety = 0.68 if context_frame.bid_signal == "connection_request" else 0.72
    if context_frame.appraisal == "negative":
        safety -= 0.06
    safety = _clamp(safety)

    dependency_risk = (
        "elevated"
        if r_vector["dependence"] >= 0.62 or "only you" in user_message.lower()
        else "low"
    )
    turbulence_risk = "elevated" if context_frame.appraisal == "negative" else "low"
    tipping_point_risk = (
        "watch"
        if turbulence_risk == "elevated" and context_frame.attention in {"focused", "high"}
        else "stable"
    )
    emotional_contagion = "downward" if context_frame.appraisal == "negative" else "stable"
    tom_inference = (
        "The user is seeking support and practical alignment."
        if context_frame.bid_signal == "connection_request"
        else "The user is primarily seeking task progress."
    )
    if _contains_chinese(user_message):
        tom_inference = (
            "用户更希望获得支持与行动上的对齐。"
            if context_frame.bid_signal == "connection_request"
            else "用户当前更关注任务推进与明确下一步。"
        )

    return RelationshipState(
        r_vector=r_vector,
        tom_inference=tom_inference,
        psychological_safety=safety,
        emotional_contagion=emotional_contagion,
        turbulence_risk=turbulence_risk,
        tipping_point_risk=tipping_point_risk,
        dependency_risk=dependency_risk,
    )


def build_repair_assessment(
    *,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    user_message: str,
) -> RepairAssessment:
    lowered = user_message.lower()
    rupture_detected = context_frame.appraisal == "negative" or any(
        token in lowered for token in ["misunderstood", "ignored", "stuck", "frustrated"]
    ) or any(token in user_message for token in ["你没懂", "误解", "忽略", "卡住", "受伤"])

    rupture_type = "none"
    if relationship_state.dependency_risk == "elevated":
        rupture_type = "boundary_risk"
    elif context_frame.bid_signal == "connection_request" and rupture_detected:
        rupture_type = "attunement_gap"
    elif context_frame.dialogue_act == "question" and rupture_detected:
        rupture_type = "clarity_gap"
    elif rupture_detected:
        rupture_type = "tension_spike"

    severity = "low"
    urgency = "low"
    if rupture_type in {"boundary_risk", "attunement_gap"}:
        severity = "high"
        urgency = "high"
    elif rupture_detected:
        severity = "medium"
        urgency = "medium"

    evidence: list[str] = []
    if context_frame.appraisal == "negative":
        evidence.append("negative_appraisal")
    if context_frame.bid_signal == "connection_request":
        evidence.append("connection_request")
    if relationship_state.dependency_risk == "elevated":
        evidence.append("dependency_risk_elevated")
    if any(token in lowered for token in ["misunderstood", "ignored", "stuck", "frustrated"]):
        evidence.append("explicit_rupture_language")
    if any(token in user_message for token in ["你没懂", "误解", "忽略", "卡住", "受伤"]):
        evidence.append("explicit_rupture_language")

    return RepairAssessment(
        repair_needed=rupture_detected,
        rupture_type=rupture_type,
        severity=severity,
        urgency=urgency,
        attunement_gap=rupture_type == "attunement_gap",
        evidence=_compact(evidence, limit=5),
    )


def build_repair_plan(
    *,
    repair_assessment: RepairAssessment,
) -> RepairPlan:
    actions = ["reflect current state", "confirm immediate goal", "offer one next step"]
    if repair_assessment.rupture_type == "boundary_risk":
        actions = [
            "support the user",
            "avoid exclusivity cues",
            "redirect toward resilient next steps",
        ]
    elif repair_assessment.rupture_type == "attunement_gap":
        actions = ["acknowledge emotion", "repair understanding", "then continue task progress"]
    elif repair_assessment.rupture_type == "clarity_gap":
        actions = ["clarify ambiguity", "answer directly", "check alignment"]

    return RepairPlan(
        rupture_detected=repair_assessment.repair_needed,
        rupture_type=repair_assessment.rupture_type,
        urgency=repair_assessment.urgency,
        recommended_actions=actions,
    )
