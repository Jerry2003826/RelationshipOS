"""Proactive dispatch: gate decision and envelope decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch_planning import (
    _build_proactive_aggregate_governance_gate,
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.application.analyzers.proactive.governance_tables import (
    GOVERNANCE_GATE_DELAY_SPECS_BY_STAGE,
    build_governance_signal_flags,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateControllerDecision,
    ProactiveAggregateGovernanceAssessment,
    ProactiveDispatchEnvelopeDecision,
    ProactiveDispatchFeedbackAssessment,
    ProactiveDispatchGateDecision,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageRefreshPlan,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


@dataclass(frozen=True)
class _DispatchGateOverride:
    retry_after_seconds: int
    gate_key: str
    gate_notes: tuple[str, ...]


@dataclass(frozen=True)
class _DispatchEnvelopeSelections:
    stage_label: str
    selected_strategy_key: str
    selected_ritual_mode: str
    selected_reengagement_delivery_mode: str
    selected_relational_move: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_sequence_objective: str
    selected_somatic_action: str
    selected_stage_delivery_mode: str
    selected_stage_question_mode: str
    selected_stage_autonomy_mode: str
    selected_stage_objective: str
    selected_stage_closing_style: str
    selected_opening_move: str
    selected_bridge_move: str
    selected_closing_move: str
    selected_continuity_anchor: str
    selected_somatic_mode: str
    selected_somatic_body_anchor: str
    selected_followup_style: str
    selected_user_space_signal: str


@dataclass(frozen=True)
class _DispatchEnvelopeState:
    status: str
    decision: str
    changed: bool
    envelope_key: str
    rationale: str
    active_sources: list[str]
    envelope_notes: list[str]


def _build_dispatch_gate_override(
    *, retry_after_seconds: int, gate_key: str, gate_notes: list[str] | tuple[str, ...]
) -> _DispatchGateOverride:
    return _DispatchGateOverride(
        retry_after_seconds=retry_after_seconds,
        gate_key=gate_key,
        gate_notes=tuple(gate_notes),
    )


def _governance_gate_defer_notes(
    stage_label: str,
    domain: str,
    kind: Literal["recenter", "watch"],
) -> tuple[str, ...]:
    """Build gate notes for a governance-driven dispatch deferral."""
    if stage_label == "final_soft_close":
        if kind == "recenter":
            return (
                f"final_stage_{domain}_delay",
                "one_more_space_before_soft_close",
            )
        return (
            f"final_stage_{domain}_watch_delay",
            "one_more_space_before_soft_close",
        )
    if kind == "recenter":
        return (
            f"{stage_label}_{domain}_recenter_delay",
            "governance_dispatch_pause",
        )
    return (
        f"{stage_label}_{domain}_watch_delay",
        "governance_dispatch_pause",
    )


def _resolve_governance_gate_override(
    *,
    stage_label: str,
    governance_flags: dict[str, bool],
    elevated_or_repair_soft: bool,
) -> _DispatchGateOverride | None:
    """Return a deferral override when a governance domain in the stage spec table is active."""
    specs = GOVERNANCE_GATE_DELAY_SPECS_BY_STAGE.get(stage_label)
    if specs is None:
        return None
    for (
        domain,
        recenter_high,
        recenter_low,
        watch_high,
        watch_low,
    ) in specs:
        if governance_flags.get(f"{domain}_recenter_active"):
            return _build_dispatch_gate_override(
                retry_after_seconds=recenter_high
                if elevated_or_repair_soft
                else recenter_low,
                gate_key=f"{stage_label}_{domain}_extra_space",
                gate_notes=_governance_gate_defer_notes(stage_label, domain, "recenter"),
            )
        if governance_flags.get(f"{domain}_watch_active"):
            return _build_dispatch_gate_override(
                retry_after_seconds=watch_high if elevated_or_repair_soft else watch_low,
                gate_key=f"{stage_label}_{domain}_watch_space",
                gate_notes=_governance_gate_defer_notes(stage_label, domain, "watch"),
            )
    return None


def _resolve_final_soft_close_gate_override(
    *,
    governance_flags: dict[str, bool],
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    aggregate_recenter_active: bool,
    aggregate_watch_active: bool,
    aggregate_governance_summary: str,
    guidance_recenter_active: bool,
    guidance_watch_active: bool,
    guidance_summary: str,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    ritual_summary: str,
    system3_snapshot: System3Snapshot,
    selected_pressure_mode: str,
    progression_advanced: bool,
    schedule_reason_text: str,
    dispatch_window_status: str,
) -> _DispatchGateOverride | None:
    has_governance_signal = any(governance_flags.values())
    has_controller_retry = _has_final_soft_close_controller_retry(
        orchestration_controller_decision=orchestration_controller_decision
    )
    if not _has_final_soft_close_gate_signal(
        has_governance_signal=has_governance_signal,
        guidance_recenter_active=guidance_recenter_active,
        guidance_watch_active=guidance_watch_active,
        ritual_recenter_active=ritual_recenter_active,
        ritual_watch_active=ritual_watch_active,
        has_controller_retry=has_controller_retry,
        aggregate_recenter_active=aggregate_recenter_active,
        aggregate_watch_active=aggregate_watch_active,
        progression_advanced=progression_advanced,
        schedule_reason_text=schedule_reason_text,
        dispatch_window_status=dispatch_window_status,
    ):
        return None

    elevated_or_repair_soft = (
        system3_snapshot.emotional_debt_status == "elevated"
        or selected_pressure_mode == "repair_soft"
    )
    return (
        _build_final_soft_close_controller_retry_override(
            orchestration_controller_decision=orchestration_controller_decision,
        )
        or _build_final_soft_close_aggregate_override(
            aggregate_controller_decision=aggregate_controller_decision,
            aggregate_recenter_active=aggregate_recenter_active,
            aggregate_watch_active=aggregate_watch_active,
            aggregate_governance_summary=aggregate_governance_summary,
            elevated_or_repair_soft=elevated_or_repair_soft,
        )
        or _resolve_governance_gate_override(
            stage_label="final_soft_close",
            governance_flags=governance_flags,
            elevated_or_repair_soft=elevated_or_repair_soft,
        )
        or _build_final_soft_close_guidance_ritual_override(
            guidance_recenter_active=guidance_recenter_active,
            guidance_watch_active=guidance_watch_active,
            guidance_summary=guidance_summary,
            ritual_recenter_active=ritual_recenter_active,
            ritual_watch_active=ritual_watch_active,
            ritual_summary=ritual_summary,
        )
        or _build_dispatch_gate_override(
            retry_after_seconds=2700 if elevated_or_repair_soft else 1800,
            gate_key="final_soft_close_extra_space",
            gate_notes=[
                "final_stage_low_pressure_delay",
                "one_more_space_before_soft_close",
            ],
        )
    )


def _has_final_soft_close_controller_retry(
    *,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
) -> bool:
    return bool(
        orchestration_controller_decision is not None
        and orchestration_controller_decision.status == "active"
        and orchestration_controller_decision.changed
        and orchestration_controller_decision.dispatch_retry_after_seconds > 0
    )


def _has_final_soft_close_gate_signal(
    *,
    has_governance_signal: bool,
    guidance_recenter_active: bool,
    guidance_watch_active: bool,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    has_controller_retry: bool,
    aggregate_recenter_active: bool,
    aggregate_watch_active: bool,
    progression_advanced: bool,
    schedule_reason_text: str,
    dispatch_window_status: str,
) -> bool:
    return bool(
        has_governance_signal
        or guidance_recenter_active
        or guidance_watch_active
        or ritual_recenter_active
        or ritual_watch_active
        or has_controller_retry
        or aggregate_recenter_active
        or aggregate_watch_active
        or progression_advanced
        or "guardrail:" in schedule_reason_text
        or dispatch_window_status in {"progressed_dispatch", "guarded_release"}
    )


def _build_final_soft_close_controller_retry_override(
    *,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
) -> _DispatchGateOverride | None:
    if not _has_final_soft_close_controller_retry(
        orchestration_controller_decision=orchestration_controller_decision
    ):
        return None
    assert orchestration_controller_decision is not None
    return _build_dispatch_gate_override(
        retry_after_seconds=orchestration_controller_decision.dispatch_retry_after_seconds,
        gate_key=(
            "final_soft_close_orchestration_extra_space"
            if orchestration_controller_decision.decision == "recenter_followup_line"
            else "final_soft_close_orchestration_watch_space"
        ),
        gate_notes=list(orchestration_controller_decision.controller_notes),
    )


def _build_final_soft_close_aggregate_override(
    *,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    aggregate_recenter_active: bool,
    aggregate_watch_active: bool,
    aggregate_governance_summary: str,
    elevated_or_repair_soft: bool,
) -> _DispatchGateOverride | None:
    if (
        aggregate_controller_decision is not None
        and aggregate_controller_decision.status == "active"
        and aggregate_controller_decision.changed
        and aggregate_controller_decision.dispatch_retry_after_seconds > 0
    ):
        return _build_dispatch_gate_override(
            retry_after_seconds=aggregate_controller_decision.dispatch_retry_after_seconds,
            gate_key=(
                "final_soft_close_governance_extra_space"
                if aggregate_controller_decision.decision == "recenter_followup_line"
                else "final_soft_close_governance_watch_space"
            ),
            gate_notes=list(aggregate_controller_decision.controller_notes),
        )
    if aggregate_recenter_active:
        return _build_dispatch_gate_override(
            retry_after_seconds=3000 if elevated_or_repair_soft else 2100,
            gate_key="final_soft_close_governance_extra_space",
            gate_notes=[
                f"aggregate_governance_recenter:{aggregate_governance_summary}",
                "one_more_space_before_soft_close",
            ],
        )
    if aggregate_watch_active:
        return _build_dispatch_gate_override(
            retry_after_seconds=2100 if elevated_or_repair_soft else 1500,
            gate_key="final_soft_close_governance_watch_space",
            gate_notes=[
                f"aggregate_governance_watch:{aggregate_governance_summary}",
                "one_more_space_before_soft_close",
            ],
        )
    return None


def _build_final_soft_close_guidance_ritual_override(
    *,
    guidance_recenter_active: bool,
    guidance_watch_active: bool,
    guidance_summary: str,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    ritual_summary: str,
) -> _DispatchGateOverride | None:
    if guidance_recenter_active:
        return _build_dispatch_gate_override(
            retry_after_seconds=900,
            gate_key="final_soft_close_guidance_extra_space",
            gate_notes=[
                f"guidance_recenter:{guidance_summary}",
                "one_more_space_before_soft_close",
            ],
        )
    if guidance_watch_active:
        return _build_dispatch_gate_override(
            retry_after_seconds=450,
            gate_key="final_soft_close_guidance_watch_space",
            gate_notes=[
                f"guidance_watch:{guidance_summary}",
                "one_more_space_before_soft_close",
            ],
        )
    if ritual_recenter_active:
        return _build_dispatch_gate_override(
            retry_after_seconds=600,
            gate_key="final_soft_close_ritual_extra_space",
            gate_notes=[
                f"ritual_somatic_recenter:{ritual_summary}",
                "one_more_space_before_soft_close",
            ],
        )
    if ritual_watch_active:
        return _build_dispatch_gate_override(
            retry_after_seconds=300,
            gate_key="final_soft_close_ritual_watch_space",
            gate_notes=[
                f"ritual_somatic_watch:{ritual_summary}",
                "one_more_space_before_soft_close",
            ],
        )
    return None


def build_proactive_dispatch_gate_decision(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    system3_snapshot: System3Snapshot,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    queue_status: str,
    schedule_reason: str | None,
    progression_advanced: bool,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
) -> ProactiveDispatchGateDecision:
    """Build gate decision controlling whether the current proactive stage dispatches."""
    if directive.status != "ready" or not directive.eligible:
        return ProactiveDispatchGateDecision(
            status="hold",
            gate_key="hold",
            stage_label=stage_replan_assessment.stage_label or "unknown",
            dispatch_window_status=stage_replan_assessment.dispatch_window_status,
            decision="hold",
            changed=False,
            retry_after_seconds=0,
            selected_strategy_key=stage_replan_assessment.selected_strategy_key,
            selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
            selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
            rationale=directive.rationale,
        )

    stage_label = stage_replan_assessment.stage_label or "first_touch"
    dispatch_window_status = stage_replan_assessment.dispatch_window_status or "on_time_dispatch"
    selected_strategy_key = stage_replan_assessment.selected_strategy_key
    selected_pressure_mode = stage_replan_assessment.selected_pressure_mode
    selected_autonomy_signal = stage_replan_assessment.selected_autonomy_signal
    schedule_reason_text = str(schedule_reason or "")
    gate_notes: list[str] = []
    decision = "dispatch"
    changed = False
    retry_after_seconds = 0
    gate_key = f"{stage_label}_dispatch_clear"

    low_pressure_handoff = guidance_plan.handoff_mode in {
        "no_pressure_checkin",
        "repair_soft_ping",
        "autonomy_preserving_ping",
    }
    guidance_gate = _build_proactive_guidance_gate(guidance_plan)
    guidance_recenter_active = guidance_gate["status"] == "recenter"
    guidance_watch_active = guidance_gate["status"] == "watch"
    guidance_summary = str(guidance_gate["summary"])
    ritual_somatic_gate = _build_proactive_ritual_somatic_gate(
        session_ritual_plan,
        somatic_orchestration_plan,
    )
    ritual_recenter_active = ritual_somatic_gate["status"] == "recenter"
    ritual_watch_active = ritual_somatic_gate["status"] == "watch"
    ritual_summary = str(ritual_somatic_gate["summary"])
    already_gate_deferred = "dispatch_gate:" in schedule_reason_text
    governance_flags = build_governance_signal_flags(system3_snapshot)
    aggregate_governance_gate = (
        {
            "status": aggregate_governance_assessment.status,
            "primary_domain": aggregate_governance_assessment.primary_domain,
            "active_domains": list(aggregate_governance_assessment.active_domains),
            "summary": aggregate_governance_assessment.summary,
            "domain_count": aggregate_governance_assessment.domain_count,
        }
        if aggregate_governance_assessment is not None
        else _build_proactive_aggregate_governance_gate(system3_snapshot)
    )
    aggregate_recenter_active = aggregate_governance_gate["status"] == "recenter"
    aggregate_watch_active = aggregate_governance_gate["status"] == "watch"
    aggregate_governance_summary = str(aggregate_governance_gate["summary"])

    gate_override: _DispatchGateOverride | None = None
    if (
        stage_label == "final_soft_close"
        and not already_gate_deferred
        and selected_strategy_key in {"continuity_soft_ping", "repair_soft_reentry"}
    ):
        gate_override = _resolve_final_soft_close_gate_override(
            governance_flags=governance_flags,
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_controller_decision=aggregate_controller_decision,
            aggregate_recenter_active=aggregate_recenter_active,
            aggregate_watch_active=aggregate_watch_active,
            aggregate_governance_summary=aggregate_governance_summary,
            guidance_recenter_active=guidance_recenter_active,
            guidance_watch_active=guidance_watch_active,
            guidance_summary=guidance_summary,
            ritual_recenter_active=ritual_recenter_active,
            ritual_watch_active=ritual_watch_active,
            ritual_summary=ritual_summary,
            system3_snapshot=system3_snapshot,
            selected_pressure_mode=selected_pressure_mode,
            progression_advanced=progression_advanced,
            schedule_reason_text=schedule_reason_text,
            dispatch_window_status=dispatch_window_status,
        )
    elif (
        stage_label in {"first_touch", "second_touch"}
        and not already_gate_deferred
        and queue_status in {"due", "overdue"}
        and any(governance_flags.values())
        # Guardrail-tightened windows only; plain progression_advanced would defer
        # too many routine due/overdue first/second dispatches.
        and (
            dispatch_window_status == "guarded_release"
            or "guardrail:" in schedule_reason_text
        )
    ):
        elevated_or_repair_soft = (
            system3_snapshot.emotional_debt_status == "elevated"
            or selected_pressure_mode == "repair_soft"
        )
        gate_override = _resolve_governance_gate_override(
            stage_label=stage_label,
            governance_flags=governance_flags,
            elevated_or_repair_soft=elevated_or_repair_soft,
        )

    # version_migration hold overrides everything
    if getattr(system3_snapshot, "version_migration_status", None) == "hold_rebuild":
        return ProactiveDispatchGateDecision(
            status="active",
            gate_key=f"{stage_label}_version_migration_hold",
            stage_label=stage_label,
            dispatch_window_status=dispatch_window_status,
            decision="hold",
            changed=True,
            retry_after_seconds=0,
            selected_strategy_key=selected_strategy_key,
            selected_pressure_mode=selected_pressure_mode,
            selected_autonomy_signal=selected_autonomy_signal,
            gate_notes=_compact(["version_migration_hold_rebuild", "all_dispatch_held"], limit=5),
            rationale=(
                "All proactive dispatches are held because the version migration "
                "status is hold_rebuild — the system model is being rebuilt."
            ),
        )

    # moral trajectory: defer final_soft_close
    if (
        gate_override is None
        and getattr(system3_snapshot, "moral_trajectory_status", None) == "recenter"
        and stage_label == "final_soft_close"
    ):
        gate_override = _build_dispatch_gate_override(
            retry_after_seconds=600,
            gate_key="final_soft_close_moral_recenter_space",
            gate_notes=[
                "moral_recenter_defer_final_close",
                "one_more_space_before_soft_close",
            ],
        )

    # growth transition: defer non-first_touch, block progress_micro_commitment
    if getattr(system3_snapshot, "growth_transition_status", None) == "redirect":
        if gate_override is None and stage_label != "first_touch":
            gate_override = _build_dispatch_gate_override(
                retry_after_seconds=3600,
                gate_key=f"{stage_label}_growth_redirect_space",
                gate_notes=[
                    "growth_redirect_defer_non_first_touch",
                    "governance_dispatch_pause",
                ],
            )
        if selected_strategy_key == "progress_micro_commitment":
            selected_strategy_key = "continuity_soft_ping"
            gate_notes.append("growth_redirect_blocked_progress_micro_commitment")

    if gate_override is not None:
        decision = "defer"
        changed = True
        retry_after_seconds = gate_override.retry_after_seconds
        gate_key = gate_override.gate_key
        gate_notes.extend(gate_override.gate_notes)
    elif (
        stage_label == "second_touch"
        and not already_gate_deferred
        and selected_strategy_key == "repair_soft_resume_bridge"
        and queue_status in {"due", "overdue"}
        and (
            low_pressure_handoff or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
        )
    ):
        decision = "defer"
        changed = True
        retry_after_seconds = 1200
        gate_key = "second_touch_repair_space"
        gate_notes.append("repair_bridge_needs_more_user_space")

    rationale = (
        "The proactive dispatch can proceed because the current stage still fits the "
        "latest low-pressure envelope."
    )
    if decision == "defer":
        rationale = (
            "The proactive dispatch should pause once more so the current stage keeps "
            "its low-pressure shape instead of firing as soon as it becomes due."
        )

    return ProactiveDispatchGateDecision(
        status="active",
        gate_key=gate_key,
        stage_label=stage_label,
        dispatch_window_status=dispatch_window_status,
        decision=decision,
        changed=changed,
        retry_after_seconds=retry_after_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        gate_notes=_compact(gate_notes, limit=5),
        rationale=rationale,
    )


def build_proactive_dispatch_envelope_decision(
    *,
    stage_label: str,
    current_stage_directive: dict[str, Any] | None,
    current_stage_actuation: dict[str, Any] | None,
    stage_refresh_plan: ProactiveStageRefreshPlan,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    stage_controller_decision: ProactiveStageControllerDecision | None = None,
    line_controller_decision: ProactiveLineControllerDecision | None = None,
) -> ProactiveDispatchEnvelopeDecision:
    """Build the final dispatch envelope merging all controller and gate outputs."""
    selections = _build_dispatch_envelope_selections(
        stage_label=stage_label,
        current_stage_directive=current_stage_directive,
        current_stage_actuation=current_stage_actuation,
        stage_refresh_plan=stage_refresh_plan,
        stage_replan_assessment=stage_replan_assessment,
    )
    selections = _apply_dispatch_envelope_gate_overrides(
        selections=selections,
        dispatch_gate_decision=dispatch_gate_decision,
    )
    active_sources = _build_dispatch_envelope_active_sources(
        stage_refresh_plan=stage_refresh_plan,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        dispatch_gate_decision=dispatch_gate_decision,
        aggregate_controller_decision=aggregate_controller_decision,
        orchestration_controller_decision=orchestration_controller_decision,
        stage_controller_decision=stage_controller_decision,
        line_controller_decision=line_controller_decision,
    )
    envelope_notes = _build_dispatch_envelope_notes(
        stage_refresh_plan=stage_refresh_plan,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        dispatch_gate_decision=dispatch_gate_decision,
    )
    envelope_state = _build_dispatch_envelope_state(
        stage_label=selections.stage_label,
        selected_strategy_key=selections.selected_strategy_key,
        active_sources=active_sources,
        dispatch_gate_decision=dispatch_gate_decision,
        envelope_notes=envelope_notes,
    )

    return ProactiveDispatchEnvelopeDecision(
        status=envelope_state.status,
        envelope_key=envelope_state.envelope_key,
        stage_label=selections.stage_label,
        decision=envelope_state.decision,
        changed=envelope_state.changed,
        selected_strategy_key=selections.selected_strategy_key,
        selected_ritual_mode=selections.selected_ritual_mode,
        selected_reengagement_delivery_mode=selections.selected_reengagement_delivery_mode,
        selected_relational_move=selections.selected_relational_move,
        selected_pressure_mode=selections.selected_pressure_mode,
        selected_autonomy_signal=selections.selected_autonomy_signal,
        selected_sequence_objective=selections.selected_sequence_objective,
        selected_somatic_action=selections.selected_somatic_action,
        selected_stage_delivery_mode=selections.selected_stage_delivery_mode,
        selected_stage_question_mode=selections.selected_stage_question_mode,
        selected_stage_autonomy_mode=selections.selected_stage_autonomy_mode,
        selected_stage_objective=selections.selected_stage_objective,
        selected_stage_closing_style=selections.selected_stage_closing_style,
        selected_opening_move=selections.selected_opening_move,
        selected_bridge_move=selections.selected_bridge_move,
        selected_closing_move=selections.selected_closing_move,
        selected_continuity_anchor=selections.selected_continuity_anchor,
        selected_somatic_mode=selections.selected_somatic_mode,
        selected_somatic_body_anchor=selections.selected_somatic_body_anchor,
        selected_followup_style=selections.selected_followup_style,
        selected_user_space_signal=selections.selected_user_space_signal,
        dispatch_retry_after_seconds=dispatch_gate_decision.retry_after_seconds,
        active_sources=_compact(envelope_state.active_sources, limit=6),
        envelope_notes=_compact(envelope_state.envelope_notes, limit=6),
        rationale=envelope_state.rationale,
    )


def _build_dispatch_envelope_selections(
    *,
    stage_label: str,
    current_stage_directive: dict[str, Any] | None,
    current_stage_actuation: dict[str, Any] | None,
    stage_refresh_plan: ProactiveStageRefreshPlan,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _DispatchEnvelopeSelections:
    current_stage_directive = current_stage_directive or {}
    current_stage_actuation = current_stage_actuation or {}
    resolved_stage_label = (
        stage_label
        or stage_refresh_plan.stage_label
        or stage_replan_assessment.stage_label
        or "unknown"
    )
    return _DispatchEnvelopeSelections(
        stage_label=resolved_stage_label,
        selected_strategy_key=stage_replan_assessment.selected_strategy_key,
        selected_ritual_mode=stage_replan_assessment.selected_ritual_mode,
        selected_reengagement_delivery_mode=stage_replan_assessment.selected_delivery_mode,
        selected_relational_move=stage_replan_assessment.selected_relational_move,
        selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
        selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
        selected_sequence_objective=stage_replan_assessment.selected_sequence_objective,
        selected_somatic_action=stage_replan_assessment.selected_somatic_action,
        selected_stage_delivery_mode=stage_refresh_plan.refreshed_delivery_mode
        or str(current_stage_directive.get("delivery_mode") or "single_message"),
        selected_stage_question_mode=stage_refresh_plan.refreshed_question_mode
        or str(current_stage_directive.get("question_mode") or "statement_only"),
        selected_stage_autonomy_mode=stage_refresh_plan.refreshed_autonomy_mode
        or str(current_stage_directive.get("autonomy_mode") or "light_invitation"),
        selected_stage_objective=stage_replan_assessment.selected_sequence_objective
        or str(current_stage_directive.get("objective") or ""),
        selected_stage_closing_style=str(
            current_stage_directive.get("closing_style") or "none"
        ),
        selected_opening_move=stage_refresh_plan.refreshed_opening_move
        or str(current_stage_actuation.get("opening_move") or "none"),
        selected_bridge_move=stage_refresh_plan.refreshed_bridge_move
        or str(current_stage_actuation.get("bridge_move") or "none"),
        selected_closing_move=stage_refresh_plan.refreshed_closing_move
        or str(current_stage_actuation.get("closing_move") or "none"),
        selected_continuity_anchor=stage_refresh_plan.refreshed_continuity_anchor
        or str(current_stage_actuation.get("continuity_anchor") or "none"),
        selected_somatic_mode=stage_refresh_plan.refreshed_somatic_mode
        or str(current_stage_actuation.get("somatic_mode") or "none"),
        selected_somatic_body_anchor=str(
            current_stage_actuation.get("somatic_body_anchor")
            or current_stage_actuation.get("body_anchor")
            or "none"
        ),
        selected_followup_style=str(current_stage_actuation.get("followup_style") or "none"),
        selected_user_space_signal=stage_refresh_plan.refreshed_user_space_signal
        or str(current_stage_actuation.get("user_space_signal") or "none"),
    )


def _apply_dispatch_envelope_gate_overrides(
    *,
    selections: _DispatchEnvelopeSelections,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
) -> _DispatchEnvelopeSelections:
    selected_pressure_mode = selections.selected_pressure_mode
    selected_autonomy_signal = selections.selected_autonomy_signal
    selected_stage_autonomy_mode = selections.selected_stage_autonomy_mode
    if (
        dispatch_gate_decision.selected_pressure_mode
        and dispatch_gate_decision.selected_pressure_mode != "none"
    ):
        selected_pressure_mode = dispatch_gate_decision.selected_pressure_mode
    if (
        dispatch_gate_decision.selected_autonomy_signal
        and dispatch_gate_decision.selected_autonomy_signal != "none"
    ):
        selected_autonomy_signal = dispatch_gate_decision.selected_autonomy_signal
        selected_stage_autonomy_mode = dispatch_gate_decision.selected_autonomy_signal
    return _DispatchEnvelopeSelections(
        **{
            **selections.__dict__,
            "selected_pressure_mode": selected_pressure_mode,
            "selected_autonomy_signal": selected_autonomy_signal,
            "selected_stage_autonomy_mode": selected_stage_autonomy_mode,
        }
    )


def _is_changed_active_controller(controller_decision: Any | None) -> bool:
    return bool(
        controller_decision is not None
        and getattr(controller_decision, "status", None) == "active"
        and getattr(controller_decision, "changed", False)
    )


def _build_dispatch_envelope_active_sources(
    *,
    stage_refresh_plan: ProactiveStageRefreshPlan,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    stage_controller_decision: ProactiveStageControllerDecision | None,
    line_controller_decision: ProactiveLineControllerDecision | None,
) -> list[str]:
    active_sources: list[str] = []
    if stage_refresh_plan.changed:
        active_sources.append("refresh")
    if stage_replan_assessment.changed:
        active_sources.append("replan")
    if dispatch_feedback_assessment.changed:
        active_sources.append("feedback")
    if _is_changed_active_controller(aggregate_controller_decision):
        active_sources.append("aggregate_controller")
    if _is_changed_active_controller(orchestration_controller_decision):
        active_sources.append("orchestration_controller")
    if _is_changed_active_controller(stage_controller_decision):
        active_sources.append("stage_controller")
    if _is_changed_active_controller(line_controller_decision):
        active_sources.append("line_controller")
    if dispatch_gate_decision.changed or dispatch_gate_decision.decision != "dispatch":
        active_sources.append("gate")
    return active_sources


def _build_dispatch_envelope_notes(
    *,
    stage_refresh_plan: ProactiveStageRefreshPlan,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
) -> list[str]:
    envelope_notes: list[str] = []
    envelope_notes.extend(list(stage_refresh_plan.refresh_notes))
    envelope_notes.extend(list(stage_replan_assessment.replan_notes))
    envelope_notes.extend(list(dispatch_feedback_assessment.feedback_notes))
    envelope_notes.extend(list(dispatch_gate_decision.gate_notes))
    return envelope_notes


def _build_dispatch_envelope_state(
    *,
    stage_label: str,
    selected_strategy_key: str,
    active_sources: list[str],
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    envelope_notes: list[str],
) -> _DispatchEnvelopeState:
    if dispatch_gate_decision.decision == "hold":
        status = "hold"
        decision = "hold_dispatch"
    elif dispatch_gate_decision.decision == "defer":
        status = "scheduled"
        decision = "defer_dispatch"
    elif active_sources:
        status = "active"
        decision = "dispatch_shaped"
    else:
        status = "active"
        decision = "dispatch_as_planned"
    changed = bool(active_sources) or dispatch_gate_decision.decision != "dispatch"
    envelope_key = (
        f"{stage_label}_{decision}_{selected_strategy_key}"
        if changed
        else f"{stage_label}_dispatch_stable"
    )
    rationale = (
        "The current proactive stage can dispatch with its current shape because the "
        "latest refresh, replan, and gate did not materially alter the envelope."
    )
    if decision == "dispatch_shaped":
        rationale = (
            "The current proactive stage should dispatch using the latest refreshed "
            "low-pressure envelope rather than the original stage defaults."
        )
    elif decision == "defer_dispatch":
        rationale = (
            "The current proactive stage should keep its final softened envelope, but "
            "the gate is deferring dispatch to leave more user space first."
        )
    elif decision == "hold_dispatch":
        rationale = (
            "The current proactive stage should not dispatch because the gate is "
            "holding the line entirely."
        )
    return _DispatchEnvelopeState(
        status=status,
        decision=decision,
        changed=changed,
        envelope_key=envelope_key,
        rationale=rationale,
        active_sources=active_sources,
        envelope_notes=envelope_notes,
    )
