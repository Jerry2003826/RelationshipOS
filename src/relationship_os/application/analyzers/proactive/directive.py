"""Proactive follow-up directive and cadence planning."""

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    ConversationCadencePlan,
    GuidancePlan,
    KnowledgeBoundaryDecision,
    ProactiveCadencePlan,
    ProactiveFollowupDirective,
    ReengagementPlan,
    RelationshipState,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    StrategyDecision,
    System3Snapshot,
)


def build_proactive_followup_directive(
    *,
    context_frame: ContextFrame,
    relationship_state: RelationshipState,
    confidence_assessment: ConfidenceAssessment,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    strategy_decision: StrategyDecision,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    system3_snapshot: System3Snapshot,
) -> ProactiveFollowupDirective:
    hold_reasons: list[str] = []
    trigger_conditions: list[str] = []
    style = runtime_coordination_snapshot.proactive_style

    if not runtime_coordination_snapshot.proactive_followup_eligible:
        hold_reasons.append("coordination_not_ready")
    if relationship_state.dependency_risk == "elevated":
        hold_reasons.append("dependency_boundary_risk")
    if knowledge_boundary_decision.decision == "support_with_boundary":
        hold_reasons.append("boundary_sensitive_turn")
    if confidence_assessment.level == "low":
        hold_reasons.append("low_confidence_turn")
    if system3_snapshot.strategy_audit_status in {"watch", "revise"}:
        hold_reasons.append(f"strategy_audit_{system3_snapshot.strategy_audit_status}")
    if system3_snapshot.emotional_debt_status == "elevated":
        hold_reasons.append("emotional_debt_elevated")
    if cadence_plan.followup_tempo == "hold_for_user_reply":
        hold_reasons.append("cadence_wait_for_user_reply")

    eligible = len(hold_reasons) == 0
    if not style or style == "none":
        if context_frame.topic in {"planning", "work", "technical"}:
            style = "progress_nudge"
        elif context_frame.appraisal == "negative":
            style = "grounded_check_in"
        else:
            style = "light_check_in"

    trigger_after_seconds = 0
    window_seconds = 0
    opening_hint = "check in with one concrete next step."
    if eligible:
        if style == "progress_nudge":
            trigger_after_seconds = 1800
            window_seconds = 7200
            opening_hint = "check whether the next step moved and offer one tiny unblock."
        elif style == "grounded_check_in":
            trigger_after_seconds = 900
            window_seconds = 3600
            opening_hint = "reconnect gently, validate pressure, then offer one stabilizing action."
        else:
            trigger_after_seconds = 3600
            window_seconds = 14400
            opening_hint = "send a light continuity check-in without adding pressure."

        if runtime_coordination_snapshot.time_awareness_mode in {"resume", "reengagement"}:
            trigger_after_seconds = min(trigger_after_seconds, 600)
            trigger_conditions.append("user_has_been_idle")
        else:
            trigger_conditions.append("no_new_user_turn")

        trigger_conditions.append(f"carryover:{guidance_plan.carryover_mode}")
        trigger_conditions.append(f"handoff:{guidance_plan.handoff_mode}")
        trigger_conditions.append(f"ritual:{session_ritual_plan.closing_move}")

        if style == "progress_nudge":
            trigger_conditions.append("current_goal_still_open")
        if context_frame.appraisal == "negative":
            trigger_conditions.append("preserve_low_pressure_tone")
        if runtime_coordination_snapshot.somatic_cue is not None:
            trigger_conditions.append("keep_followup_brief_and_grounding")
        if guidance_plan.carryover_mode == "clarify_hold":
            trigger_conditions.append("wait_for_user_reply_before_reengaging")
        if guidance_plan.handoff_mode == "no_pressure_checkin":
            opening_hint = "reconnect softly, keep the pace low, and make the next step optional."
        elif guidance_plan.handoff_mode == "resume_bridge":
            opening_hint = "re-anchor shared context first, then reopen the easiest next step."
        elif guidance_plan.handoff_mode == "repair_soft_ping":
            opening_hint = (
                "reconnect gently, keep pressure low, and leave room for the user "
                "not to reply."
            )
        elif guidance_plan.handoff_mode == "autonomy_preserving_ping":
            opening_hint = "check in without taking over, and keep the user's choice explicit."
        elif guidance_plan.handoff_mode == "reflective_ping":
            opening_hint = "reflect the state briefly, then reopen one grounded next step."
        if session_ritual_plan.closing_move == "grounding_close":
            opening_hint = (
                "reconnect softly, offer one grounding cue, then reopen "
                "the smallest safe step."
            )
        elif session_ritual_plan.closing_move == "repair_soft_close":
            opening_hint = (
                "reconnect with attunement first and keep the follow-up "
                "explicitly non-demanding."
            )
        elif session_ritual_plan.closing_move == "boundary_safe_close":
            opening_hint = "check in without taking over, and keep the user's choice visible."

        if cadence_plan.followup_tempo == "grounding_ping":
            trigger_after_seconds = min(trigger_after_seconds, 900)
            window_seconds = min(window_seconds, 3600)
        elif cadence_plan.followup_tempo == "resume_ping":
            trigger_after_seconds = min(trigger_after_seconds, 600)
        elif cadence_plan.followup_tempo == "boundary_safe_ping":
            trigger_after_seconds = max(trigger_after_seconds, 1800)
        elif cadence_plan.followup_tempo == "reflective_ping":
            trigger_after_seconds = min(trigger_after_seconds, 1200)

        trigger_conditions.append(f"cadence:{cadence_plan.status}")
        trigger_conditions.append(f"tempo:{cadence_plan.followup_tempo}")

        status = "ready"
        rationale = (
            "The session is stable enough for a lightweight follow-up without "
            "raising dependency or cognitive load."
        )
    else:
        status = "hold"
        rationale = (
            "A proactive follow-up would be premature because the current turn "
            "still needs regulation, repair, or stronger boundaries."
        )
        style = "none"

    if strategy_decision.strategy == "clarify_then_answer" and eligible:
        trigger_conditions.append("wait_for_missing_detail_before_followup")

    return ProactiveFollowupDirective(
        eligible=eligible,
        status=status,
        style=style,
        trigger_after_seconds=trigger_after_seconds,
        window_seconds=window_seconds,
        rationale=rationale,
        opening_hint=opening_hint if eligible else "",
        trigger_conditions=_compact(trigger_conditions, limit=5),
        hold_reasons=_compact(hold_reasons, limit=5),
    )


def build_proactive_cadence_plan(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    reengagement_plan: ReengagementPlan,
) -> ProactiveCadencePlan:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveCadencePlan(
            status="hold",
            cadence_key="hold",
            rationale=directive.rationale,
        )

    first_interval = max(0, directive.trigger_after_seconds)
    window_seconds = max(1800, directive.window_seconds)
    stage_labels = ["first_touch", "second_touch", "final_soft_close"]
    cadence_key = "steady_three_touch"
    second_interval = 4 * 3600
    final_interval = 18 * 3600

    if directive.style == "grounded_check_in":
        cadence_key = "grounding_three_touch"
        second_interval = 6 * 3600
        final_interval = 24 * 3600
        window_seconds = max(window_seconds, 2 * 3600)
    elif reengagement_plan.strategy_key == "progress_micro_commitment":
        cadence_key = "progress_three_touch"
        second_interval = 3 * 3600
        final_interval = 12 * 3600
    elif reengagement_plan.strategy_key == "repair_soft_progress_reentry":
        cadence_key = "repair_progress_three_touch"
        second_interval = 6 * 3600
        final_interval = 24 * 3600
    elif reengagement_plan.strategy_key in {
        "resume_context_bridge",
        "repair_soft_resume_bridge",
    }:
        cadence_key = "resume_bridge_three_touch"
        second_interval = 4 * 3600
        final_interval = 16 * 3600

    if cadence_plan.followup_tempo == "grounding_ping":
        second_interval = max(second_interval, 6 * 3600)
        final_interval = max(final_interval, 24 * 3600)
    elif cadence_plan.followup_tempo == "reflective_ping":
        second_interval = max(second_interval, 5 * 3600)
        final_interval = max(final_interval, 18 * 3600)

    if cadence_plan.user_space_mode in {
        "spacious",
        "explicit_autonomy_space",
        "consent_space",
    }:
        second_interval = max(second_interval, 6 * 3600)
        final_interval = max(final_interval, 24 * 3600)

    if guidance_plan.handoff_mode in {
        "no_pressure_checkin",
        "repair_soft_ping",
        "autonomy_preserving_ping",
    }:
        second_interval = max(second_interval, 6 * 3600)
        final_interval = max(final_interval, 24 * 3600)

    if session_ritual_plan.closing_move in {
        "repair_soft_close",
        "grounding_close",
        "boundary_safe_close",
    }:
        final_interval = max(final_interval, 24 * 3600)

    return ProactiveCadencePlan(
        status="active",
        cadence_key=cadence_key,
        stage_labels=stage_labels,
        stage_intervals_seconds=[first_interval, second_interval, final_interval][
            : len(stage_labels)
        ],
        window_seconds=window_seconds,
        close_after_stage_index=len(stage_labels),
        rationale=directive.rationale,
    )
