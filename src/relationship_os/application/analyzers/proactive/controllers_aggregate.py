"""Proactive controllers: aggregate + orchestration."""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch import (
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.application.analyzers.proactive.governance_tables import (
    GOVERNANCE_AGGREGATE_DELAY_TABLE,
    GOVERNANCE_AGGREGATE_RETRY_TABLE,
    GOVERNANCE_AGGREGATE_STRATEGY_TABLE,
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

    kind = "recenter" if recenter_active else "default"
    if next_stage_label in {"second_touch", "final_soft_close"}:
        stage_additional_delay_seconds, line_additional_delay_seconds = (
            GOVERNANCE_AGGREGATE_DELAY_TABLE.get((next_stage_label, kind), (3900, 0))
        )
        strategy_row = GOVERNANCE_AGGREGATE_STRATEGY_TABLE.get((next_stage_label, kind))
        if strategy_row:
            (
                selected_strategy_key,
                selected_pressure_mode,
                selected_autonomy_signal,
                selected_delivery_mode,
                stage_note,
            ) = strategy_row
            controller_notes.append(stage_note)

    if current_stage_label == "first_touch":
        _, line_additional_delay_seconds = GOVERNANCE_AGGREGATE_DELAY_TABLE.get(
            ("first_touch", kind), (0, 2700)
        )
        controller_notes.append("keep_remaining_line_soft")

    if (
        stage_replan_assessment.stage_label == "final_soft_close"
        and stage_replan_assessment.selected_strategy_key
        in {"continuity_soft_ping", "repair_soft_reentry"}
    ):
        is_elevated = (
            system3_snapshot.emotional_debt_status == "elevated"
            or stage_replan_assessment.selected_pressure_mode == "repair_soft"
        )
        dispatch_retry_after_seconds = GOVERNANCE_AGGREGATE_RETRY_TABLE.get(
            (recenter_active, is_elevated), 1500
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


def _build_orchestration_source_state(
    *,
    guidance_plan: GuidancePlan | None,
    session_ritual_plan: SessionRitualPlan | None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    guidance_gate: dict[str, Any],
    ritual_somatic_gate: dict[str, Any],
) -> dict[str, Any]:
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
    return {
        "guidance_recenter_active": guidance_recenter_active,
        "guidance_watch_active": guidance_watch_active,
        "ritual_recenter_active": ritual_recenter_active,
        "ritual_watch_active": ritual_watch_active,
        "aggregate_active": aggregate_active,
        "aggregate_recenter_active": aggregate_recenter_active,
        "aggregate_watch_active": aggregate_watch_active,
        "active_sources": active_sources,
        "guidance_repair_soft": bool(
            guidance_plan is not None
            and (
                guidance_plan.mode in {"repair_guidance", "stabilizing_guidance"}
                or guidance_plan.handoff_mode == "repair_soft_ping"
            )
        ),
        "guidance_autonomy_signal": (
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
        ),
        "ritual_low_pressure": bool(
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
        ),
        "ritual_delivery_mode": (
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
        ),
    }


def _build_orchestration_control_state(
    *,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> dict[str, Any]:
    return {
        "selected_strategy_key": stage_replan_assessment.selected_strategy_key,
        "selected_pressure_mode": stage_replan_assessment.selected_pressure_mode,
        "selected_autonomy_signal": stage_replan_assessment.selected_autonomy_signal,
        "selected_delivery_mode": stage_replan_assessment.selected_delivery_mode,
        "stage_additional_delay_seconds": 0,
        "line_additional_delay_seconds": 0,
        "dispatch_retry_after_seconds": 0,
        "controller_notes": [],
    }


def _apply_aggregate_orchestration_override(
    state: dict[str, Any],
    *,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
) -> None:
    if aggregate_controller_decision is None:
        return
    state["stage_additional_delay_seconds"] = max(
        int(state["stage_additional_delay_seconds"]),
        aggregate_controller_decision.stage_additional_delay_seconds,
    )
    state["line_additional_delay_seconds"] = max(
        int(state["line_additional_delay_seconds"]),
        aggregate_controller_decision.line_additional_delay_seconds,
    )
    state["dispatch_retry_after_seconds"] = max(
        int(state["dispatch_retry_after_seconds"]),
        aggregate_controller_decision.dispatch_retry_after_seconds,
    )
    state["controller_notes"].extend(list(aggregate_controller_decision.controller_notes))


def _apply_second_touch_orchestration_override(
    state: dict[str, Any],
    *,
    current_stage_label: str,
    primary_source: str,
    source_state: dict[str, Any],
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    guidance_gate: dict[str, Any],
    ritual_somatic_gate: dict[str, Any],
) -> None:
    if source_state["guidance_recenter_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 2100
        )
        if current_stage_label == "first_touch":
            state["line_additional_delay_seconds"] = max(
                int(state["line_additional_delay_seconds"]), 1200
            )
    elif source_state["guidance_watch_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 1200
        )
        if current_stage_label == "first_touch":
            state["line_additional_delay_seconds"] = max(
                int(state["line_additional_delay_seconds"]), 600
            )

    if source_state["ritual_recenter_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 1500
        )
        if current_stage_label == "first_touch":
            state["line_additional_delay_seconds"] = max(
                int(state["line_additional_delay_seconds"]), 900
            )
    elif source_state["ritual_watch_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 900
        )
        if current_stage_label == "first_touch":
            state["line_additional_delay_seconds"] = max(
                int(state["line_additional_delay_seconds"]), 450
            )

    if primary_source == "aggregate" and aggregate_controller_decision is not None:
        state["selected_strategy_key"] = aggregate_controller_decision.selected_strategy_key
        state["selected_pressure_mode"] = (
            aggregate_controller_decision.selected_pressure_mode
        )
        state["selected_autonomy_signal"] = (
            aggregate_controller_decision.selected_autonomy_signal
        )
        state["selected_delivery_mode"] = (
            aggregate_controller_decision.selected_delivery_mode
        )
    elif primary_source == "guidance":
        state["selected_strategy_key"] = (
            "repair_soft_resume_bridge"
            if source_state["guidance_repair_soft"]
            else "resume_context_bridge"
        )
        state["selected_pressure_mode"] = (
            "repair_soft" if source_state["guidance_repair_soft"] else "gentle_resume"
        )
        state["selected_autonomy_signal"] = source_state["guidance_autonomy_signal"]
        state["selected_delivery_mode"] = "single_message"
        state["controller_notes"].append(f"guidance:{guidance_gate['summary']}")
    else:
        state["selected_strategy_key"] = (
            "repair_soft_resume_bridge"
            if source_state["ritual_low_pressure"]
            else "resume_context_bridge"
        )
        state["selected_pressure_mode"] = (
            "repair_soft" if source_state["ritual_low_pressure"] else "gentle_resume"
        )
        state["selected_autonomy_signal"] = (
            "explicit_no_pressure"
            if source_state["ritual_low_pressure"]
            else "light_invitation"
        )
        state["selected_delivery_mode"] = source_state["ritual_delivery_mode"]
        state["controller_notes"].append(
            f"ritual_somatic:{ritual_somatic_gate['summary']}"
        )


def _apply_late_stage_orchestration_override(
    state: dict[str, Any],
    *,
    primary_source: str,
    source_state: dict[str, Any],
    guidance_gate: dict[str, Any],
    ritual_somatic_gate: dict[str, Any],
) -> None:
    if source_state["guidance_recenter_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 1800
        )
        state["line_additional_delay_seconds"] = max(
            int(state["line_additional_delay_seconds"]), 600
        )
        state["dispatch_retry_after_seconds"] = max(
            int(state["dispatch_retry_after_seconds"]), 900
        )
    elif source_state["guidance_watch_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 900
        )
        state["line_additional_delay_seconds"] = max(
            int(state["line_additional_delay_seconds"]), 450
        )
        state["dispatch_retry_after_seconds"] = max(
            int(state["dispatch_retry_after_seconds"]), 450
        )

    if source_state["ritual_recenter_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 1200
        )
        state["line_additional_delay_seconds"] = max(
            int(state["line_additional_delay_seconds"]), 600
        )
        state["dispatch_retry_after_seconds"] = max(
            int(state["dispatch_retry_after_seconds"]), 600
        )
    elif source_state["ritual_watch_active"]:
        state["stage_additional_delay_seconds"] = max(
            int(state["stage_additional_delay_seconds"]), 600
        )
        state["line_additional_delay_seconds"] = max(
            int(state["line_additional_delay_seconds"]), 300
        )
        state["dispatch_retry_after_seconds"] = max(
            int(state["dispatch_retry_after_seconds"]), 300
        )

    state["selected_strategy_key"] = "continuity_soft_ping"
    state["selected_pressure_mode"] = "archive_light_presence"
    state["selected_autonomy_signal"] = "archive_light_thread"
    state["selected_delivery_mode"] = "single_message"
    if primary_source == "guidance":
        state["controller_notes"].append(f"guidance:{guidance_gate['summary']}")
    elif primary_source == "ritual_somatic":
        state["controller_notes"].append(
            f"ritual_somatic:{ritual_somatic_gate['summary']}"
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
    source_state = _build_orchestration_source_state(
        guidance_plan=guidance_plan,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
        aggregate_controller_decision=aggregate_controller_decision,
        guidance_gate=guidance_gate,
        ritual_somatic_gate=ritual_somatic_gate,
    )

    if not source_state["active_sources"]:
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
        source_state["aggregate_recenter_active"]
        or source_state["guidance_recenter_active"]
        or source_state["ritual_recenter_active"]
    )
    primary_source = (
        "aggregate"
        if source_state["aggregate_recenter_active"]
        or source_state["aggregate_watch_active"]
        else "guidance"
        if source_state["guidance_recenter_active"]
        or source_state["guidance_watch_active"]
        else "ritual_somatic"
    )
    controller_key = (
        "orchestration_recenter_followup_line"
        if recenter_active
        else "orchestration_watch_followup_line"
    )
    decision = "recenter_followup_line" if recenter_active else "soften_followup_line"
    state = _build_orchestration_control_state(
        stage_replan_assessment=stage_replan_assessment,
    )
    if source_state["aggregate_active"]:
        _apply_aggregate_orchestration_override(
            state,
            aggregate_controller_decision=aggregate_controller_decision,
        )

    if next_stage_label == "second_touch":
        _apply_second_touch_orchestration_override(
            state,
            current_stage_label=current_stage_label,
            primary_source=primary_source,
            source_state=source_state,
            aggregate_controller_decision=aggregate_controller_decision,
            guidance_gate=guidance_gate,
            ritual_somatic_gate=ritual_somatic_gate,
        )
    else:
        _apply_late_stage_orchestration_override(
            state,
            primary_source=primary_source,
            source_state=source_state,
            guidance_gate=guidance_gate,
            ritual_somatic_gate=ritual_somatic_gate,
        )

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
        stage_additional_delay_seconds=int(state["stage_additional_delay_seconds"]),
        line_additional_delay_seconds=int(state["line_additional_delay_seconds"]),
        dispatch_retry_after_seconds=int(state["dispatch_retry_after_seconds"]),
        selected_strategy_key=str(state["selected_strategy_key"]),
        selected_pressure_mode=str(state["selected_pressure_mode"]),
        selected_autonomy_signal=str(state["selected_autonomy_signal"]),
        selected_delivery_mode=str(state["selected_delivery_mode"]),
        primary_source=primary_source,
        active_sources=list(source_state["active_sources"]),
        controller_notes=_compact(list(state["controller_notes"]), limit=5),
        rationale=rationale,
    )
