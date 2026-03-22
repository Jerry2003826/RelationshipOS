"""Runtime coordination, guidance, cadence, ritual, and somatic orchestration."""

from __future__ import annotations

import re

from relationship_os.application.analyzers._utils import (
    _compact,
    _contains_chinese,
)
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    ConversationCadencePlan,
    GuidancePlan,
    KnowledgeBoundaryDecision,
    PolicyGateDecision,
    RelationshipState,
    RepairAssessment,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    StrategyDecision,
)


def _has_mixed_language(text: str) -> bool:
    if not text:
        return False
    has_chinese = _contains_chinese(text)
    english_word_count = len(re.findall(r"\b[a-zA-Z]{2,}\b", text))
    return has_chinese and english_word_count >= 3


def _detect_somatic_cue(text: str) -> str | None:
    lowered = text.lower()
    cue_map = [
        (
            "fatigue",
            ["tired", "exhausted", "drained", "sleep-deprived"],
            ["累", "疲惫", "精疲力尽", "困"],
        ),
        (
            "breath",
            ["can't breathe", "breathing", "short of breath", "heart racing"],
            ["呼吸", "喘不过气", "心慌", "胸口"],
        ),
        (
            "tension",
            ["tense", "shaky", "frozen", "numb", "headache"],
            ["紧绷", "发抖", "僵住", "麻木", "头疼", "头痛"],
        ),
    ]
    for cue_name, english_tokens, chinese_tokens in cue_map:
        if any(token in lowered for token in english_tokens) or any(
            token in text for token in chinese_tokens
        ):
            return cue_name
    return None


def build_runtime_coordination_snapshot(
    *,
    turn_index: int,
    session_age_seconds: float,
    idle_gap_seconds: float,
    user_message: str,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    confidence_assessment: ConfidenceAssessment,
    repair_assessment: RepairAssessment,
    strategy_decision: StrategyDecision,
) -> RuntimeCoordinationSnapshot:
    somatic_cue = _detect_somatic_cue(user_message)

    if turn_index <= 1:
        time_awareness_mode = "opening"
    elif idle_gap_seconds >= 1800:
        time_awareness_mode = "reengagement"
    elif idle_gap_seconds >= 300:
        time_awareness_mode = "resume"
    elif context_frame.attention == "high":
        time_awareness_mode = "high_intensity"
    else:
        time_awareness_mode = "ongoing"

    if turn_index <= 1:
        ritual_phase = "opening_ritual"
    elif time_awareness_mode in {"reengagement", "resume"}:
        ritual_phase = "re_anchor"
    elif repair_assessment.repair_needed and repair_assessment.severity == "high":
        ritual_phase = "repair_ritual"
    elif strategy_decision.strategy == "clarify_then_answer":
        ritual_phase = "alignment_check"
    else:
        ritual_phase = "steady_progress"

    cognitive_load_band = "low"
    if (
        context_frame.attention == "high"
        or len(user_message) >= 180
        or confidence_assessment.needs_clarification
        or repair_assessment.severity == "high"
        or somatic_cue is not None
        or time_awareness_mode == "high_intensity"
    ):
        cognitive_load_band = "high"
    elif (
        context_frame.attention == "focused"
        or context_frame.appraisal == "negative"
        or repair_assessment.repair_needed
    ):
        cognitive_load_band = "medium"

    if cognitive_load_band == "high":
        response_budget_mode = "concise"
    elif cognitive_load_band == "medium":
        response_budget_mode = "structured"
    else:
        response_budget_mode = "expansive"

    proactive_followup_eligible = bool(
        turn_index >= 2
        and relationship_state.psychological_safety >= 0.72
        and relationship_state.dependency_risk == "low"
        and not repair_assessment.repair_needed
        and confidence_assessment.level != "low"
        and cognitive_load_band != "high"
    )
    proactive_style = "none"
    if proactive_followup_eligible:
        if context_frame.topic in {"planning", "work", "technical"}:
            proactive_style = "progress_nudge"
        elif context_frame.appraisal == "negative":
            proactive_style = "grounded_check_in"
        else:
            proactive_style = "light_check_in"

    coordination_notes = [
        f"time_mode={time_awareness_mode}",
        f"ritual={ritual_phase}",
        f"cognitive_load={cognitive_load_band}",
        f"response_budget={response_budget_mode}",
    ]
    if session_age_seconds > 0:
        coordination_notes.append(f"session_age_seconds={round(session_age_seconds, 1)}")
    if idle_gap_seconds > 0:
        coordination_notes.append(f"idle_gap_seconds={round(idle_gap_seconds, 1)}")
    if somatic_cue is not None:
        coordination_notes.append(f"somatic_cue={somatic_cue}")

    return RuntimeCoordinationSnapshot(
        triggered_turn_index=turn_index,
        time_awareness_mode=time_awareness_mode,
        idle_gap_seconds=round(max(0.0, idle_gap_seconds), 3),
        session_age_seconds=round(max(0.0, session_age_seconds), 3),
        ritual_phase=ritual_phase,
        cognitive_load_band=cognitive_load_band,
        response_budget_mode=response_budget_mode,
        proactive_followup_eligible=proactive_followup_eligible,
        proactive_style=proactive_style,
        somatic_cue=somatic_cue,
        coordination_notes=_compact(coordination_notes, limit=6),
    )


def build_guidance_plan(
    *,
    context_frame: ContextFrame,
    repair_assessment: RepairAssessment,
    confidence_assessment: ConfidenceAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
) -> GuidancePlan:
    mode = "progress_guidance"
    lead_with = "micro_commitment"
    pacing = "forward"
    step_budget = 2
    agency_mode = "collaborative_choice"
    ritual_action = "goal_restate"
    checkpoint_style = "micro_checkpoint"
    handoff_mode = "invite_progress_ping"
    carryover_mode = "progress_ping"
    micro_actions = [
        "restate the smallest active goal",
        "offer one or two manageable next steps",
    ]
    rationale = "The interaction is stable enough to guide progress in a concrete way."

    if repair_assessment.repair_needed and repair_assessment.severity == "high":
        mode = "repair_guidance"
        lead_with = "attunement_repair"
        pacing = "slow"
        step_budget = 1
        agency_mode = "consent_check"
        ritual_action = "attunement_repair"
        checkpoint_style = "repair_checkpoint"
        handoff_mode = "repair_soft_ping"
        carryover_mode = "repair_ping"
        micro_actions = [
            "acknowledge the rupture first",
            "repair understanding before new direction",
            "offer one safe next step only after repair lands",
        ]
        rationale = "Repair needs to lead before any directional guidance."
    elif runtime_coordination_snapshot.cognitive_load_band == "high":
        mode = "stabilizing_guidance"
        lead_with = "regulate_first"
        pacing = "slow"
        step_budget = 1
        agency_mode = "low_pressure_invitation"
        ritual_action = "somatic_grounding"
        checkpoint_style = "stability_check"
        handoff_mode = "no_pressure_checkin"
        carryover_mode = "grounding_ping"
        micro_actions = [
            "lower the tempo before asking for movement",
            "offer one grounding move",
            "keep the next step optional",
        ]
        rationale = "High cognitive load means guidance should reduce pressure first."
    elif (
        knowledge_boundary_decision.decision == "clarify_before_answer"
        or confidence_assessment.response_mode == "clarify"
    ):
        mode = "clarifying_guidance"
        lead_with = "clarify_gap"
        pacing = "steady"
        step_budget = 1
        agency_mode = "focused_question"
        ritual_action = "focus_the_unknown"
        checkpoint_style = "clarity_checkpoint"
        handoff_mode = "wait_for_reply"
        carryover_mode = "clarify_hold"
        micro_actions = [
            "name the missing detail",
            "ask one focused question",
            "pause new advice until the gap is closed",
        ]
        rationale = "The system should guide the user toward one missing detail first."
    elif knowledge_boundary_decision.decision == "support_with_boundary":
        mode = "boundary_guidance"
        lead_with = "boundary_frame"
        pacing = "steady"
        step_budget = 1
        agency_mode = "explicit_autonomy"
        ritual_action = "boundary_frame"
        checkpoint_style = "boundary_safe_step"
        handoff_mode = "autonomy_preserving_ping"
        carryover_mode = "boundary_safe_ping"
        micro_actions = [
            "name the support boundary",
            "keep the user's agency explicit",
            "offer one collaborative next step",
        ]
        rationale = "Guidance should stay supportive without taking over the user's agency."
    elif runtime_coordination_snapshot.time_awareness_mode in {"resume", "reengagement"}:
        mode = "reanchor_guidance"
        lead_with = "shared_context_reanchor"
        pacing = "gentle"
        step_budget = 1
        agency_mode = "light_reentry"
        ritual_action = "shared_context_reanchor"
        checkpoint_style = "resume_checkpoint"
        handoff_mode = "resume_bridge"
        carryover_mode = "resume_ping"
        micro_actions = [
            "briefly reconnect shared context",
            "resume from the easiest open loop",
        ]
        rationale = "After a gap, guidance should re-anchor context before asking for progress."
    elif policy_gate.selected_path == "reflect_and_progress":
        mode = "reflective_guidance"
        lead_with = "reflect_then_step"
        pacing = "steady"
        step_budget = 1
        agency_mode = "collaborative_choice"
        ritual_action = "reflective_restate"
        checkpoint_style = "steady_checkpoint"
        handoff_mode = "reflective_ping"
        carryover_mode = "reflective_ping"
        micro_actions = [
            "briefly reflect the user's state",
            "offer one grounded next step",
        ]
        rationale = "The path calls for reflective guidance before forward motion."

    if runtime_coordination_snapshot.somatic_cue is not None:
        micro_actions.insert(0, "guide one brief somatic reset before progress")
    if policy_gate.red_line_status == "boundary_sensitive":
        agency_mode = "explicit_autonomy"
        handoff_mode = "autonomy_preserving_ping"
        carryover_mode = "boundary_safe_ping"

    return GuidancePlan(
        mode=mode,
        lead_with=lead_with,
        pacing=pacing,
        step_budget=step_budget,
        agency_mode=agency_mode,
        ritual_action=ritual_action,
        checkpoint_style=checkpoint_style,
        handoff_mode=handoff_mode,
        carryover_mode=carryover_mode,
        micro_actions=_compact(micro_actions, limit=4),
        rationale=rationale,
    )


def build_conversation_cadence_plan(
    *,
    context_frame: ContextFrame,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    repair_assessment: RepairAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    policy_gate: PolicyGateDecision,
) -> ConversationCadencePlan:
    status = "guided_progress"
    turn_shape = "paired_step"
    ritual_depth = "structured"
    somatic_track = "none"
    followup_tempo = "progress_ping"
    user_space_mode = "balanced_space"
    transition_intent = "close_with_optional_progress_ping"
    next_checkpoint = "micro_progress_check"
    cadence_actions = [
        "name the smallest useful next move",
        "close with a low-pressure progress handoff",
    ]
    rationale = "The current turn can move forward while still leaving space."

    if repair_assessment.repair_needed and repair_assessment.severity == "high":
        status = "repair_bridge"
        turn_shape = "single_step"
        ritual_depth = "restorative"
        followup_tempo = "repair_soft_ping"
        user_space_mode = "consent_space"
        transition_intent = "pause_after_repair_landing"
        next_checkpoint = "repair_landing_check"
        cadence_actions = [
            "repair attunement before directional guidance",
            "leave explicit room for the user not to respond immediately",
        ]
        rationale = "The cadence should privilege repair landing over forward motion."
    elif runtime_coordination_snapshot.cognitive_load_band == "high":
        status = "stabilize_and_wait"
        turn_shape = "single_step"
        ritual_depth = "restorative"
        followup_tempo = "grounding_ping"
        user_space_mode = "spacious"
        transition_intent = "decompress_before_any_next_step"
        next_checkpoint = "regulation_check"
        cadence_actions = [
            "slow the cadence before asking for movement",
            "offer one grounding action and stop there",
        ]
        rationale = "High load calls for a wider, lower-pressure conversational rhythm."
    elif (
        knowledge_boundary_decision.decision == "clarify_before_answer"
        or guidance_plan.mode == "clarifying_guidance"
    ):
        status = "clarify_and_pause"
        turn_shape = "question_then_pause"
        ritual_depth = "light"
        followup_tempo = "hold_for_user_reply"
        user_space_mode = "reply_required_space"
        transition_intent = "pause_for_missing_detail"
        next_checkpoint = "missing_detail_reply"
        cadence_actions = [
            "ask one focused question and then stop",
            "do not reopen the thread before the user replies",
        ]
        rationale = "Clarification works best when the cadence pauses after one precise ask."
    elif knowledge_boundary_decision.decision == "support_with_boundary":
        status = "boundary_guarded_progress"
        turn_shape = "single_step"
        ritual_depth = "structured"
        followup_tempo = "boundary_safe_ping"
        user_space_mode = "explicit_autonomy_space"
        transition_intent = "keep_agency_visible"
        next_checkpoint = "boundary_safe_recheck"
        cadence_actions = [
            "state the boundary and keep choice explicit",
            "offer one collaborative next step without taking over",
        ]
        rationale = "Boundary-sensitive turns need a slower handoff with visible autonomy."
    elif runtime_coordination_snapshot.time_awareness_mode in {"resume", "reengagement"}:
        status = "reanchor_and_resume"
        turn_shape = "reanchor_then_step"
        ritual_depth = "bridge"
        followup_tempo = "resume_ping"
        user_space_mode = "light_reentry_space"
        transition_intent = "reopen_with_shared_context"
        next_checkpoint = "resume_bridge_check"
        cadence_actions = [
            "briefly bridge back to shared context",
            "resume from the easiest open loop",
        ]
        rationale = "After a gap, the cadence should bridge first and only then re-enter."
    elif guidance_plan.mode == "reflective_guidance":
        status = "reflect_then_move"
        turn_shape = "reflect_then_step"
        ritual_depth = "light"
        followup_tempo = "reflective_ping"
        user_space_mode = "balanced_space"
        transition_intent = "reflect_then_reopen"
        next_checkpoint = "reflective_followup"
        cadence_actions = [
            "reflect briefly before reopening progress",
            "keep the next step grounded and optional",
        ]
        rationale = "Reflective turns work best with a slower bridge into progress."

    if runtime_coordination_snapshot.somatic_cue == "breath":
        somatic_track = "breath_reset"
    elif runtime_coordination_snapshot.somatic_cue == "fatigue":
        somatic_track = "fatigue_release"
    elif runtime_coordination_snapshot.somatic_cue == "tension":
        somatic_track = "tension_release"

    if somatic_track != "none":
        cadence_actions.insert(0, "start with one brief somatic reset")

    if policy_gate.red_line_status == "boundary_sensitive":
        user_space_mode = "explicit_autonomy_space"
        if followup_tempo not in {"hold_for_user_reply", "boundary_safe_ping"}:
            followup_tempo = "boundary_safe_ping"
        cadence_actions.append("avoid turning the handoff into relational pressure")

    return ConversationCadencePlan(
        status=status,
        turn_shape=turn_shape,
        ritual_depth=ritual_depth,
        somatic_track=somatic_track,
        followup_tempo=followup_tempo,
        user_space_mode=user_space_mode,
        transition_intent=transition_intent,
        next_checkpoint=next_checkpoint,
        cadence_actions=_compact(cadence_actions, limit=4),
        rationale=rationale,
    )


def build_session_ritual_plan(
    *,
    context_frame: ContextFrame,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    repair_assessment: RepairAssessment,
) -> SessionRitualPlan:
    phase = runtime_coordination_snapshot.ritual_phase
    opening_move = "soft_open"
    bridge_move = "micro_step_bridge"
    closing_move = "light_handoff"
    continuity_anchor = "smallest_next_step"
    somatic_shortcut = "none"
    micro_rituals = ["set a gentle frame", "close with a low-pressure handoff"]
    rationale = "The ritual should make the interaction easier to enter and easier to resume."

    if phase == "opening_ritual":
        opening_move = "warm_orientation"
        bridge_move = "frame_the_session"
        closing_move = "progress_invitation"
        continuity_anchor = "session_frame"
        micro_rituals = [
            "name the frame before solving",
            "set one simple expectation for this turn",
        ]
    elif phase == "re_anchor":
        opening_move = "shared_context_bridge"
        bridge_move = "resume_the_open_loop"
        closing_move = "resume_ping"
        continuity_anchor = "shared_context_resume"
        micro_rituals = [
            "briefly restate where we left off",
            "reopen the easiest live thread",
        ]
    elif phase == "repair_ritual":
        opening_move = "attunement_repair"
        bridge_move = "repair_before_progress"
        closing_move = "repair_soft_close"
        continuity_anchor = "repair_landing"
        micro_rituals = [
            "repair the connection before movement",
            "close with explicit non-pressure",
        ]
    elif phase == "alignment_check":
        opening_move = "clarity_frame"
        bridge_move = "single_question_pause"
        closing_move = "clarify_pause"
        continuity_anchor = "missing_detail"
        micro_rituals = [
            "say why the missing detail matters",
            "stop after one focused question",
        ]

    if guidance_plan.mode == "boundary_guidance":
        closing_move = "boundary_safe_close"
        continuity_anchor = "boundary_safe_step"
        micro_rituals.append("keep the user's choice explicit at the close")
    elif guidance_plan.mode == "stabilizing_guidance":
        opening_move = "regulate_first"
        bridge_move = "ground_then_step"
        closing_move = "grounding_close"
        continuity_anchor = "grounding_first"
    elif guidance_plan.mode == "reflective_guidance":
        opening_move = "reflective_restate"
        bridge_move = "reflect_then_step"
        closing_move = "reflective_close"
        continuity_anchor = "reflective_step"

    if cadence_plan.turn_shape == "question_then_pause":
        bridge_move = "single_question_pause"
        closing_move = "clarify_pause"
    elif cadence_plan.turn_shape == "reanchor_then_step":
        bridge_move = "resume_the_open_loop"
    elif cadence_plan.turn_shape == "reflect_then_step":
        bridge_move = "reflect_then_step"

    if runtime_coordination_snapshot.somatic_cue == "breath":
        somatic_shortcut = "one_slower_breath"
    elif runtime_coordination_snapshot.somatic_cue == "fatigue":
        somatic_shortcut = "drop_shoulders_once"
    elif runtime_coordination_snapshot.somatic_cue == "tension":
        somatic_shortcut = "unclench_jaw_once"

    if repair_assessment.repair_needed and repair_assessment.severity == "high":
        continuity_anchor = "repair_landing"

    return SessionRitualPlan(
        phase=phase,
        opening_move=opening_move,
        bridge_move=bridge_move,
        closing_move=closing_move,
        continuity_anchor=continuity_anchor,
        somatic_shortcut=somatic_shortcut,
        micro_rituals=_compact(micro_rituals, limit=4),
        rationale=rationale,
    )


def build_somatic_orchestration_plan(
    *,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
) -> SomaticOrchestrationPlan:
    cue = str(runtime_coordination_snapshot.somatic_cue or "none")
    active = cue != "none"
    if cadence_plan.somatic_track != "none":
        active = True
    if session_ritual_plan.somatic_shortcut != "none":
        active = True
    if guidance_plan.ritual_action == "somatic_grounding":
        active = True

    if not active:
        return SomaticOrchestrationPlan(
            status="not_needed",
            cue="none",
            primary_mode="none",
            body_anchor="none",
            followup_style="none",
            allow_in_followup=False,
            rationale="No body-based orchestration is needed for this turn.",
        )

    primary_mode = "settle_pace"
    body_anchor = "breath_and_posture"
    followup_style = "light_grounding_checkin"
    micro_actions = ["slow the pace before asking for movement"]
    phrasing_guardrails = ["keep the body cue optional, brief, and non-prescriptive"]
    rationale = "A light body-based reset can lower friction before the next move."

    if cue == "breath":
        primary_mode = "breath_regulation"
        body_anchor = "one_slower_breath"
        followup_style = "one_breath_then_choice"
        micro_actions = [
            "invite one slower breath",
            "resume only after the breath settles",
        ]
    elif cue == "fatigue":
        primary_mode = "fatigue_release"
        body_anchor = "drop_shoulders_and_exhale"
        followup_style = "reduce_effort_then_micro_step"
        micro_actions = [
            "drop the shoulders once before choosing the next move",
            "shrink the next step so it costs less energy",
        ]
    elif cue == "tension":
        primary_mode = "tension_release"
        body_anchor = "unclench_jaw_and_shoulders"
        followup_style = "soften_then_resume"
        micro_actions = [
            "unclench the jaw and shoulders once",
            "resume only after the body softens a notch",
        ]

    if cadence_plan.user_space_mode in {
        "spacious",
        "explicit_autonomy_space",
        "consent_space",
    }:
        phrasing_guardrails.append("do not turn the body cue into an obligation")
    if guidance_plan.mode == "stabilizing_guidance":
        phrasing_guardrails.append("ground first, then stop after one steadying action")
    if guidance_plan.mode == "repair_guidance":
        phrasing_guardrails.append("use the body cue to lower friction before repair")
    if session_ritual_plan.somatic_shortcut != "none":
        micro_actions.insert(
            0,
            f"reuse the ritual shortcut {session_ritual_plan.somatic_shortcut}",
        )

    allow_in_followup = cadence_plan.followup_tempo != "hold_for_user_reply"
    if guidance_plan.handoff_mode in {"no_pressure_checkin", "repair_soft_ping"}:
        followup_style = "gentle_body_first_reentry"
    elif guidance_plan.handoff_mode == "reflective_ping":
        followup_style = "reflect_then_ground_then_resume"

    return SomaticOrchestrationPlan(
        status="active",
        cue=cue,
        primary_mode=primary_mode,
        body_anchor=body_anchor,
        followup_style=followup_style,
        allow_in_followup=allow_in_followup,
        micro_actions=_compact(micro_actions, limit=4),
        phrasing_guardrails=_compact(phrasing_guardrails, limit=4),
        rationale=rationale,
    )
