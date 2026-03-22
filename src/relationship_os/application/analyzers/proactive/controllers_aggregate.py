"""Proactive controllers: aggregate + orchestration."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch import (
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateControllerDecision,
    ProactiveAggregateGovernanceAssessment,
    ProactiveCadencePlan,
    ProactiveFollowupDirective,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


def build_proactive_aggregate_controller_decision(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    system3_snapshot: System3Snapshot,
    current_stage_label: str,
    current_stage_index: int,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment,
) -> ProactiveAggregateControllerDecision:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveAggregateControllerDecision(
            status="hold",
            controller_key="hold",
            current_stage_label=current_stage_label or "unknown",
            next_stage_label=None,
            decision="hold",
            changed=False,
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or [current_stage_label])
    stage_count = max(
        1,
        proactive_cadence_plan.close_after_stage_index or len(stage_labels) or 1,
    )
    next_stage_label = (
        stage_labels[current_stage_index]
        if current_stage_index < min(stage_count, len(stage_labels))
        else None
    )

    if aggregate_governance_assessment.status == "clear":
        return ProactiveAggregateControllerDecision(
            status="clear",
            controller_key="aggregate_governance_clear",
            current_stage_label=current_stage_label,
            next_stage_label=next_stage_label,
            decision="follow_local_controllers",
            changed=False,
            primary_domain=aggregate_governance_assessment.primary_domain,
            active_domains=list(aggregate_governance_assessment.active_domains),
            rationale=aggregate_governance_assessment.rationale,
        )

    recenter_active = aggregate_governance_assessment.status == "recenter"
    controller_key = (
        "aggregate_governance_recenter_followup_line"
        if recenter_active
        else "aggregate_governance_watch_followup_line"
    )
    selected_strategy_key = stage_replan_assessment.selected_strategy_key
    selected_pressure_mode = stage_replan_assessment.selected_pressure_mode
    selected_autonomy_signal = stage_replan_assessment.selected_autonomy_signal
    selected_delivery_mode = stage_replan_assessment.selected_delivery_mode
    stage_additional_delay_seconds = 0
    line_additional_delay_seconds = 0
    dispatch_retry_after_seconds = 0
    controller_notes = [
        f"aggregate_governance_{aggregate_governance_assessment.status}:"
        f"{aggregate_governance_assessment.summary}"
    ]

    if next_stage_label == "second_touch":
        stage_additional_delay_seconds = 6300 if recenter_active else 4050
        line_additional_delay_seconds = 3900 if recenter_active else 2700
        selected_strategy_key = (
            "repair_soft_resume_bridge" if recenter_active else "resume_context_bridge"
        )
        selected_pressure_mode = "repair_soft" if recenter_active else "gentle_resume"
        selected_autonomy_signal = "explicit_no_pressure"
        selected_delivery_mode = "single_message"
        controller_notes.append("space_out_second_touch")
    elif next_stage_label == "final_soft_close":
        stage_additional_delay_seconds = 5700 if recenter_active else 3900
        selected_strategy_key = "continuity_soft_ping"
        selected_pressure_mode = "archive_light_presence"
        selected_autonomy_signal = "archive_light_thread"
        selected_delivery_mode = "single_message"
        controller_notes.append("leave_more_breathing_room_before_close")

    if current_stage_label == "first_touch":
        line_additional_delay_seconds = 3900 if recenter_active else 2700
        controller_notes.append("keep_remaining_line_soft")

    if (
        stage_replan_assessment.stage_label == "final_soft_close"
        and stage_replan_assessment.selected_strategy_key
        in {"continuity_soft_ping", "repair_soft_reentry"}
    ):
        if recenter_active:
            dispatch_retry_after_seconds = (
                3000
                if system3_snapshot.emotional_debt_status == "elevated"
                or stage_replan_assessment.selected_pressure_mode == "repair_soft"
                else 2100
            )
        else:
            dispatch_retry_after_seconds = (
                2100
                if system3_snapshot.emotional_debt_status == "elevated"
                or stage_replan_assessment.selected_pressure_mode == "repair_soft"
                else 1500
            )
        controller_notes.append("one_more_space_before_soft_close")

    return ProactiveAggregateControllerDecision(
        status="active",
        controller_key=controller_key,
        current_stage_label=current_stage_label,
        next_stage_label=next_stage_label,
        decision=("recenter_followup_line" if recenter_active else "soften_followup_line"),
        changed=True,
        stage_additional_delay_seconds=stage_additional_delay_seconds,
        line_additional_delay_seconds=line_additional_delay_seconds,
        dispatch_retry_after_seconds=dispatch_retry_after_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_domain=aggregate_governance_assessment.primary_domain,
        active_domains=list(aggregate_governance_assessment.active_domains),
        controller_notes=_compact(controller_notes, limit=5),
        rationale=(
            "Multiple governance lines are active together, so the proactive "
            "controller should soften the remaining line before dispatching the next "
            "stage."
        ),
    )

def build_proactive_orchestration_controller_decision(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    current_stage_label: str,
    current_stage_index: int,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    guidance_plan: GuidancePlan | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
) -> ProactiveOrchestrationControllerDecision:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveOrchestrationControllerDecision(
            status="hold",
            controller_key="hold",
            current_stage_label=current_stage_label or "unknown",
            next_stage_label=None,
            decision="hold",
            changed=False,
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or [current_stage_label])
    stage_count = max(
        1,
        proactive_cadence_plan.close_after_stage_index or len(stage_labels) or 1,
    )
    next_stage_label = (
        stage_labels[current_stage_index]
        if current_stage_index < min(stage_count, len(stage_labels))
        else None
    )

    if not next_stage_label:
        return ProactiveOrchestrationControllerDecision(
            status="terminal",
            controller_key="orchestration_line_closed",
            current_stage_label=current_stage_label,
            next_stage_label=None,
            decision="close_line",
            changed=False,
            rationale=(
                "There is no remaining proactive stage to orchestrate after the current stage."
            ),
        )

    guidance_gate = _build_proactive_guidance_gate(guidance_plan)
    ritual_somatic_gate = _build_proactive_ritual_somatic_gate(
        session_ritual_plan,
        somatic_orchestration_plan,
    )
    guidance_recenter_active = guidance_gate["status"] == "recenter"
    guidance_watch_active = guidance_gate["status"] == "watch"
    ritual_recenter_active = ritual_somatic_gate["status"] == "recenter"
    ritual_watch_active = ritual_somatic_gate["status"] == "watch"

    aggregate_active = bool(
        aggregate_controller_decision is not None
        and aggregate_controller_decision.status == "active"
        and aggregate_controller_decision.changed
    )
    aggregate_recenter_active = bool(
        aggregate_active
        and aggregate_controller_decision is not None
        and aggregate_controller_decision.decision == "recenter_followup_line"
    )
    aggregate_watch_active = aggregate_active and not aggregate_recenter_active

    active_sources: list[str] = []
    if aggregate_active:
        active_sources.append("aggregate")
    if guidance_recenter_active or guidance_watch_active:
        active_sources.append("guidance")
    if ritual_recenter_active or ritual_watch_active:
        active_sources.append("ritual_somatic")

    if not active_sources:
        return ProactiveOrchestrationControllerDecision(
            status="clear",
            controller_key="orchestration_clear",
            current_stage_label=current_stage_label,
            next_stage_label=next_stage_label,
            decision="follow_local_controllers",
            changed=False,
            rationale=(
                "The local proactive controllers can operate normally because neither "
                "aggregate governance, guidance, nor ritual/somatic orchestration is "
                "requesting a stronger low-pressure override."
            ),
        )

    recenter_active = (
        aggregate_recenter_active or guidance_recenter_active or ritual_recenter_active
    )
    primary_source = (
        "aggregate"
        if aggregate_recenter_active or aggregate_watch_active
        else "guidance"
        if guidance_recenter_active or guidance_watch_active
        else "ritual_somatic"
    )
    controller_key = (
        "orchestration_recenter_followup_line"
        if recenter_active
        else "orchestration_watch_followup_line"
    )
    decision = "recenter_followup_line" if recenter_active else "soften_followup_line"

    guidance_repair_soft = bool(
        guidance_plan is not None
        and (
            guidance_plan.mode in {"repair_guidance", "stabilizing_guidance"}
            or guidance_plan.handoff_mode == "repair_soft_ping"
        )
    )
    guidance_autonomy_signal = (
        "explicit_no_pressure"
        if guidance_plan is not None
        and guidance_plan.handoff_mode
        in {
            "repair_soft_ping",
            "no_pressure_checkin",
            "autonomy_preserving_ping",
            "wait_for_reply",
        }
        else "light_invitation"
    )
    ritual_low_pressure = bool(
        session_ritual_plan is not None
        and (
            session_ritual_plan.phase in {"repair_ritual", "alignment_check"}
            or session_ritual_plan.closing_move
            in {
                "repair_soft_close",
                "boundary_safe_close",
                "grounding_close",
                "clarify_pause",
            }
            or session_ritual_plan.somatic_shortcut != "none"
        )
    )
    ritual_delivery_mode = (
        "two_part_sequence"
        if somatic_orchestration_plan is not None
        and somatic_orchestration_plan.status == "active"
        and somatic_orchestration_plan.allow_in_followup
        and somatic_orchestration_plan.followup_style
        in {
            "gentle_body_first_reentry",
            "one_breath_then_choice",
            "reduce_effort_then_micro_step",
            "soften_then_resume",
            "reflect_then_ground_then_resume",
        }
        else "single_message"
    )

    selected_strategy_key = stage_replan_assessment.selected_strategy_key
    selected_pressure_mode = stage_replan_assessment.selected_pressure_mode
    selected_autonomy_signal = stage_replan_assessment.selected_autonomy_signal
    selected_delivery_mode = stage_replan_assessment.selected_delivery_mode

    stage_additional_delay_seconds = 0
    line_additional_delay_seconds = 0
    dispatch_retry_after_seconds = 0
    controller_notes: list[str] = []

    if aggregate_active and aggregate_controller_decision is not None:
        stage_additional_delay_seconds = max(
            stage_additional_delay_seconds,
            aggregate_controller_decision.stage_additional_delay_seconds,
        )
        line_additional_delay_seconds = max(
            line_additional_delay_seconds,
            aggregate_controller_decision.line_additional_delay_seconds,
        )
        dispatch_retry_after_seconds = max(
            dispatch_retry_after_seconds,
            aggregate_controller_decision.dispatch_retry_after_seconds,
        )
        controller_notes.extend(list(aggregate_controller_decision.controller_notes))

    if next_stage_label == "second_touch":
        if guidance_recenter_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 2100)
            if current_stage_label == "first_touch":
                line_additional_delay_seconds = max(line_additional_delay_seconds, 1200)
        elif guidance_watch_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 1200)
            if current_stage_label == "first_touch":
                line_additional_delay_seconds = max(line_additional_delay_seconds, 600)

        if ritual_recenter_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 1500)
            if current_stage_label == "first_touch":
                line_additional_delay_seconds = max(line_additional_delay_seconds, 900)
        elif ritual_watch_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 900)
            if current_stage_label == "first_touch":
                line_additional_delay_seconds = max(line_additional_delay_seconds, 450)

        if primary_source == "aggregate" and aggregate_controller_decision is not None:
            selected_strategy_key = aggregate_controller_decision.selected_strategy_key
            selected_pressure_mode = aggregate_controller_decision.selected_pressure_mode
            selected_autonomy_signal = aggregate_controller_decision.selected_autonomy_signal
            selected_delivery_mode = aggregate_controller_decision.selected_delivery_mode
        elif primary_source == "guidance":
            selected_strategy_key = (
                "repair_soft_resume_bridge" if guidance_repair_soft else "resume_context_bridge"
            )
            selected_pressure_mode = "repair_soft" if guidance_repair_soft else "gentle_resume"
            selected_autonomy_signal = guidance_autonomy_signal
            selected_delivery_mode = "single_message"
            controller_notes.append(f"guidance:{guidance_gate['summary']}")
        else:
            selected_strategy_key = (
                "repair_soft_resume_bridge" if ritual_low_pressure else "resume_context_bridge"
            )
            selected_pressure_mode = "repair_soft" if ritual_low_pressure else "gentle_resume"
            selected_autonomy_signal = (
                "explicit_no_pressure" if ritual_low_pressure else "light_invitation"
            )
            selected_delivery_mode = ritual_delivery_mode
            controller_notes.append(f"ritual_somatic:{ritual_somatic_gate['summary']}")
    else:
        if guidance_recenter_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 1800)
            line_additional_delay_seconds = max(line_additional_delay_seconds, 600)
            dispatch_retry_after_seconds = max(dispatch_retry_after_seconds, 900)
        elif guidance_watch_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 900)
            line_additional_delay_seconds = max(line_additional_delay_seconds, 450)
            dispatch_retry_after_seconds = max(dispatch_retry_after_seconds, 450)

        if ritual_recenter_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 1200)
            line_additional_delay_seconds = max(line_additional_delay_seconds, 600)
            dispatch_retry_after_seconds = max(dispatch_retry_after_seconds, 600)
        elif ritual_watch_active:
            stage_additional_delay_seconds = max(stage_additional_delay_seconds, 600)
            line_additional_delay_seconds = max(line_additional_delay_seconds, 300)
            dispatch_retry_after_seconds = max(dispatch_retry_after_seconds, 300)

        selected_strategy_key = "continuity_soft_ping"
        selected_pressure_mode = "archive_light_presence"
        selected_autonomy_signal = "archive_light_thread"
        selected_delivery_mode = "single_message"
        if primary_source == "guidance":
            controller_notes.append(f"guidance:{guidance_gate['summary']}")
        elif primary_source == "ritual_somatic":
            controller_notes.append(f"ritual_somatic:{ritual_somatic_gate['summary']}")

    rationale = (
        "The proactive controller should treat aggregate governance, guidance, and "
        "ritual/somatic orchestration as one low-pressure envelope before the local "
        "stage/line/gate logic adds its own stage-specific refinements."
    )
    return ProactiveOrchestrationControllerDecision(
        status="active",
        controller_key=controller_key,
        current_stage_label=current_stage_label,
        next_stage_label=next_stage_label,
        decision=decision,
        changed=True,
        stage_additional_delay_seconds=stage_additional_delay_seconds,
        line_additional_delay_seconds=line_additional_delay_seconds,
        dispatch_retry_after_seconds=dispatch_retry_after_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_source=primary_source,
        active_sources=active_sources,
        controller_notes=_compact(controller_notes, limit=5),
        rationale=rationale,
    )

