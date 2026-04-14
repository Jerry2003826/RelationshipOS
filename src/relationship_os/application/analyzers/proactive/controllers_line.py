"""Proactive controllers: line controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch import (
    _build_proactive_aggregate_governance_gate,
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.application.analyzers.proactive.governance_tables import (
    build_governance_signal_flags,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateControllerDecision,
    ProactiveAggregateGovernanceAssessment,
    ProactiveCadencePlan,
    ProactiveDispatchFeedbackAssessment,
    ProactiveDispatchGateDecision,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


@dataclass(frozen=True)
class _LineControllerOverride:
    controller_key: str
    line_state: str
    decision: str
    changed: bool
    additional_delay_seconds: int
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_delivery_mode: str
    controller_notes: tuple[str, ...]


@dataclass(frozen=True)
class _RemainingLinePlan:
    final_stage_label: str
    remaining_stage_labels: tuple[str, ...]


@dataclass(frozen=True)
class _LineControllerSignals:
    governance_flags: dict[str, bool]
    aggregate_recenter_active: bool
    aggregate_watch_active: bool
    aggregate_governance_summary: str
    guidance_recenter_active: bool
    guidance_watch_active: bool
    guidance_summary: str
    guidance_repair_soft: bool
    guidance_low_pressure: bool
    ritual_recenter_active: bool
    ritual_watch_active: bool
    ritual_summary: str
    ritual_low_pressure: bool
    ritual_delivery_mode: str


@dataclass
class _LineControllerState:
    controller_key: str
    line_state: str
    decision: str
    changed: bool
    additional_delay_seconds: int
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_delivery_mode: str
    controller_notes: list[str]


_FIRST_TOUCH_GOVERNANCE_LINE_OVERRIDE_SPECS: tuple[tuple[str, int, int], ...] = (
    ("safety", 3600, 2700),
    ("autonomy", 3150, 2250),
    ("boundary", 3000, 2100),
    ("support", 2700, 1800),
    ("clarity", 2400, 1500),
    ("pacing", 2100, 1200),
    ("attunement", 2400, 1500),
    ("commitment", 2550, 1650),
    ("disclosure", 2550, 1650),
    ("reciprocity", 2550, 1650),
    ("progress", 2550, 1650),
    ("stability", 2700, 1800),
    ("pressure", 2400, 1500),
    ("trust", 1800, 1200),
    ("continuity", 1500, 900),
    ("repair", 1200, 750),
    ("relational", 900, 600),
)


_SECOND_TOUCH_GOVERNANCE_LINE_OVERRIDE_SPECS: tuple[tuple[str, int, int, int, int], ...] = (
    ("safety", 5400, 3600, 3600, 2700),
    ("autonomy", 4500, 3150, 3150, 2250),
    ("boundary", 4200, 3000, 3000, 2100),
    ("support", 3600, 2700, 2700, 1800),
    ("clarity", 3300, 2400, 2400, 1500),
    ("pacing", 3000, 2100, 2100, 1200),
    ("attunement", 3300, 2400, 2400, 1500),
    ("commitment", 3450, 2550, 2550, 1650),
    ("disclosure", 3450, 2550, 2550, 1650),
    ("reciprocity", 3450, 2550, 2550, 1650),
    ("progress", 3450, 2550, 2550, 1650),
    ("stability", 3600, 2700, 2700, 1800),
    ("pressure", 2400, 1800, 1800, 1200),
    ("trust", 1800, 1200, 1200, 900),
    ("continuity", 1200, 900, 900, 600),
    ("repair", 900, 600, 600, 450),
    ("relational", 750, 450, 450, 300),
)


def _build_line_controller_override(
    *,
    controller_key: str,
    line_state: str,
    decision: str,
    changed: bool,
    additional_delay_seconds: int,
    selected_pressure_mode: str,
    selected_autonomy_signal: str,
    selected_delivery_mode: str,
    controller_notes: list[str] | tuple[str, ...],
) -> _LineControllerOverride:
    return _LineControllerOverride(
        controller_key=controller_key,
        line_state=line_state,
        decision=decision,
        changed=changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        controller_notes=tuple(controller_notes),
    )


def _resolve_signal_gate_line_override(
    *,
    recenter_active: bool,
    watch_active: bool,
    summary: str,
    recenter_config: dict[str, Any],
    watch_config: dict[str, Any],
    defer: bool = False,
) -> _LineControllerOverride | None:
    """Resolve recenter/watch gate signals into a line override from config dicts.

    Each config dict supports:
        controller_key, line_state, decision, changed (optional, default True),
        delay: int, or tuple[int, int] as (seconds_when_defer, seconds_when_not_defer),
        pressure_mode, autonomy_signal, delivery_mode,
        summary_note_prefix: builds the first note as ``f"{prefix}:{summary}"``,
        notes: iterable of trailing controller note strings.
    """
    cfg: dict[str, Any] | None = None
    if recenter_active:
        cfg = recenter_config
    elif watch_active:
        cfg = watch_config
    if cfg is None:
        return None

    delay_raw = cfg["delay"]
    if isinstance(delay_raw, tuple):
        defer_secs, ready_secs = delay_raw
        additional_delay_seconds = int(defer_secs if defer else ready_secs)
    else:
        additional_delay_seconds = int(delay_raw)

    note_prefix = str(cfg["summary_note_prefix"])
    tail_notes = tuple(str(n) for n in cfg["notes"])
    controller_notes: tuple[str, ...] = (f"{note_prefix}:{summary}", *tail_notes)

    return _build_line_controller_override(
        controller_key=str(cfg["controller_key"]),
        line_state=str(cfg["line_state"]),
        decision=str(cfg["decision"]),
        changed=bool(cfg.get("changed", True)),
        additional_delay_seconds=additional_delay_seconds,
        selected_pressure_mode=str(cfg["pressure_mode"]),
        selected_autonomy_signal=str(cfg["autonomy_signal"]),
        selected_delivery_mode=str(cfg["delivery_mode"]),
        controller_notes=controller_notes,
    )


def _build_line_hold_decision(
    current_stage_label: str,
    directive: ProactiveFollowupDirective,
) -> ProactiveLineControllerDecision:
    return ProactiveLineControllerDecision(
        status="hold",
        controller_key="hold",
        trigger_stage_label=current_stage_label or "unknown",
        line_state="hold",
        decision="hold",
        changed=False,
        rationale=directive.rationale,
    )


def _build_remaining_line_plan(
    *,
    proactive_cadence_plan: ProactiveCadencePlan,
    current_stage_label: str,
    current_stage_index: int,
) -> _RemainingLinePlan:
    stage_labels = list(proactive_cadence_plan.stage_labels or [current_stage_label])
    stage_count = max(
        1,
        proactive_cadence_plan.close_after_stage_index or len(stage_labels) or 1,
    )
    final_stage_label = (
        stage_labels[min(stage_count, len(stage_labels)) - 1]
        if stage_labels
        else current_stage_label
    )
    remaining_stage_labels = tuple(
        label
        for label in stage_labels[current_stage_index : min(stage_count, len(stage_labels))]
        if str(label).strip()
    )
    return _RemainingLinePlan(
        final_stage_label=final_stage_label,
        remaining_stage_labels=remaining_stage_labels,
    )


def _build_exhausted_line_decision(
    *,
    current_stage_label: str,
    remaining_line_plan: _RemainingLinePlan,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> ProactiveLineControllerDecision | None:
    if remaining_line_plan.remaining_stage_labels:
        return None
    if current_stage_label == remaining_line_plan.final_stage_label:
        return ProactiveLineControllerDecision(
            status="active",
            controller_key=f"{current_stage_label}_line_close_ready",
            trigger_stage_label=current_stage_label,
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
            selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
            selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
            controller_notes=["current_stage_is_final_close_loop"],
            rationale=(
                "The current stage is already the last proactive touch, so the "
                "line should stay close-ready until this close-loop finishes."
            ),
        )
    return ProactiveLineControllerDecision(
        status="terminal",
        controller_key=f"{current_stage_label}_line_complete",
        trigger_stage_label=current_stage_label,
        line_state="line_complete",
        decision="close_line",
        changed=False,
        selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
        selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
        selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
        rationale=(
            "The current stage already exhausted the remaining proactive line, so "
            "there is nothing left to soften or retire."
        ),
    )


def _build_line_controller_state(
    *,
    current_stage_label: str,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _LineControllerState:
    return _LineControllerState(
        controller_key=f"{current_stage_label}_follow_remaining_line",
        line_state="steady",
        decision="follow_remaining_line",
        changed=False,
        additional_delay_seconds=0,
        selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
        selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
        selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
        controller_notes=[],
    )


def _build_line_controller_signals(
    *,
    system3_snapshot: System3Snapshot,
    guidance_plan: GuidancePlan | None,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None,
    session_ritual_plan: SessionRitualPlan | None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None,
) -> _LineControllerSignals:
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
    guidance_gate = _build_proactive_guidance_gate(guidance_plan)
    ritual_somatic_gate = _build_proactive_ritual_somatic_gate(
        session_ritual_plan,
        somatic_orchestration_plan,
    )
    return _LineControllerSignals(
        governance_flags=governance_flags,
        aggregate_recenter_active=aggregate_governance_gate["status"] == "recenter",
        aggregate_watch_active=aggregate_governance_gate["status"] == "watch",
        aggregate_governance_summary=str(aggregate_governance_gate["summary"]),
        guidance_recenter_active=guidance_gate["status"] == "recenter",
        guidance_watch_active=guidance_gate["status"] == "watch",
        guidance_summary=str(guidance_gate["summary"]),
        guidance_repair_soft=bool(
            guidance_plan is not None
            and (
                guidance_plan.mode in {"repair_guidance", "stabilizing_guidance"}
                or guidance_plan.handoff_mode == "repair_soft_ping"
            )
        ),
        guidance_low_pressure=bool(
            guidance_plan is not None
            and guidance_plan.handoff_mode
            in {
                "repair_soft_ping",
                "no_pressure_checkin",
                "autonomy_preserving_ping",
                "wait_for_reply",
            }
        ),
        ritual_recenter_active=ritual_somatic_gate["status"] == "recenter",
        ritual_watch_active=ritual_somatic_gate["status"] == "watch",
        ritual_summary=str(ritual_somatic_gate["summary"]),
        ritual_low_pressure=bool(
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
        ritual_delivery_mode=(
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
    )


def _resolve_line_controller_override(
    *,
    current_stage_label: str,
    signals: _LineControllerSignals,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
) -> _LineControllerOverride | None:
    if current_stage_label == "first_touch":
        return _resolve_first_touch_line_override(
            governance_flags=signals.governance_flags,
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_controller_decision=aggregate_controller_decision,
            aggregate_recenter_active=signals.aggregate_recenter_active,
            aggregate_watch_active=signals.aggregate_watch_active,
            aggregate_governance_summary=signals.aggregate_governance_summary,
            guidance_recenter_active=signals.guidance_recenter_active,
            guidance_watch_active=signals.guidance_watch_active,
            guidance_summary=signals.guidance_summary,
            guidance_repair_soft=signals.guidance_repair_soft,
            guidance_low_pressure=signals.guidance_low_pressure,
            ritual_recenter_active=signals.ritual_recenter_active,
            ritual_watch_active=signals.ritual_watch_active,
            ritual_summary=signals.ritual_summary,
            ritual_low_pressure=signals.ritual_low_pressure,
            ritual_delivery_mode=signals.ritual_delivery_mode,
            stage_controller_decision=stage_controller_decision,
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
        )
    if current_stage_label == "second_touch":
        return _resolve_second_touch_line_override(
            governance_flags=signals.governance_flags,
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_recenter_active=signals.aggregate_recenter_active,
            aggregate_watch_active=signals.aggregate_watch_active,
            aggregate_governance_summary=signals.aggregate_governance_summary,
            guidance_recenter_active=signals.guidance_recenter_active,
            guidance_watch_active=signals.guidance_watch_active,
            guidance_summary=signals.guidance_summary,
            ritual_recenter_active=signals.ritual_recenter_active,
            ritual_watch_active=signals.ritual_watch_active,
            ritual_summary=signals.ritual_summary,
            stage_controller_decision=stage_controller_decision,
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
            dispatch_gate_decision=dispatch_gate_decision,
        )
    return None


def _apply_line_controller_override(
    state: _LineControllerState,
    line_override: _LineControllerOverride | None,
) -> None:
    if line_override is None:
        return
    state.controller_key = line_override.controller_key
    state.line_state = line_override.line_state
    state.decision = line_override.decision
    state.changed = line_override.changed
    state.additional_delay_seconds = line_override.additional_delay_seconds
    state.selected_pressure_mode = line_override.selected_pressure_mode
    state.selected_autonomy_signal = line_override.selected_autonomy_signal
    state.selected_delivery_mode = line_override.selected_delivery_mode
    state.controller_notes.extend(line_override.controller_notes)


def _build_line_controller_rationale(changed: bool) -> str:
    if changed:
        return (
            "The remaining proactive line should now shift as a whole toward a lower-"
            "pressure posture so later touches inherit softer delivery and autonomy "
            "without each stage rediscovering that from scratch."
        )
    return (
        "The remaining proactive line can keep its planned posture because the current "
        "stage did not create enough pressure to reshape everything that follows."
    )


def _build_first_touch_active_controller_override(
    *,
    controller_decision: ProactiveOrchestrationControllerDecision
    | ProactiveAggregateControllerDecision
    | None,
    recentered_key: str,
    softened_key: str,
) -> _LineControllerOverride | None:
    if (
        controller_decision is None
        or controller_decision.status != "active"
        or not controller_decision.changed
        or controller_decision.current_stage_label != "first_touch"
        or controller_decision.line_additional_delay_seconds <= 0
    ):
        return None
    return _build_line_controller_override(
        controller_key=(
            recentered_key
            if controller_decision.decision == "recenter_followup_line"
            else softened_key
        ),
        line_state="softened",
        decision="soften_remaining_line",
        changed=True,
        additional_delay_seconds=controller_decision.line_additional_delay_seconds,
        selected_pressure_mode=controller_decision.selected_pressure_mode,
        selected_autonomy_signal=controller_decision.selected_autonomy_signal,
        selected_delivery_mode=controller_decision.selected_delivery_mode,
        controller_notes=list(controller_decision.controller_notes),
    )


def _build_first_touch_aggregate_gate_override(
    *,
    aggregate_recenter_active: bool,
    aggregate_watch_active: bool,
    aggregate_governance_summary: str,
) -> _LineControllerOverride | None:
    if aggregate_recenter_active:
        return _build_line_controller_override(
            controller_key="remaining_line_governance_recentered_after_first_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
            additional_delay_seconds=3900,
            selected_pressure_mode="repair_soft",
            selected_autonomy_signal="explicit_no_pressure",
            selected_delivery_mode="single_message",
            controller_notes=[
                f"aggregate_governance_recenter:{aggregate_governance_summary}",
                "keep_remaining_line_soft",
            ],
        )
    if aggregate_watch_active:
        return _build_line_controller_override(
            controller_key="remaining_line_governance_softened_after_first_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
            additional_delay_seconds=2700,
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
            selected_delivery_mode="single_message",
            controller_notes=[
                f"aggregate_governance_watch:{aggregate_governance_summary}",
                "keep_remaining_line_soft",
            ],
        )
    return None


def _build_first_touch_governance_family_override(
    *,
    governance_flags: dict[str, bool],
) -> _LineControllerOverride | None:
    for domain, recenter_delay, watch_delay in _FIRST_TOUCH_GOVERNANCE_LINE_OVERRIDE_SPECS:
        if governance_flags[f"{domain}_recenter_active"]:
            return _build_line_controller_override(
                controller_key=f"remaining_line_{domain}_recentered_after_first_touch",
                line_state="softened",
                decision="soften_remaining_line",
                changed=True,
                additional_delay_seconds=recenter_delay,
                selected_pressure_mode="repair_soft",
                selected_autonomy_signal="explicit_no_pressure",
                selected_delivery_mode="single_message",
                controller_notes=[
                    f"{domain}_governance_recenter",
                    "keep_remaining_line_soft",
                ],
            )
        if governance_flags[f"{domain}_watch_active"]:
            return _build_line_controller_override(
                controller_key=f"remaining_line_{domain}_softened_after_first_touch",
                line_state="softened",
                decision="soften_remaining_line",
                changed=True,
                additional_delay_seconds=watch_delay,
                selected_pressure_mode="gentle_resume",
                selected_autonomy_signal="explicit_no_pressure",
                selected_delivery_mode="single_message",
                controller_notes=[
                    f"{domain}_governance_watch",
                    "keep_remaining_line_soft",
                ],
            )
    return None


def _build_first_touch_guidance_override(
    *,
    guidance_recenter_active: bool,
    guidance_watch_active: bool,
    guidance_summary: str,
    guidance_repair_soft: bool,
    guidance_low_pressure: bool,
) -> _LineControllerOverride | None:
    recenter_pressure = "repair_soft" if guidance_repair_soft else "gentle_resume"
    autonomy_signal = (
        "explicit_no_pressure" if guidance_low_pressure else "light_invitation"
    )
    return _resolve_signal_gate_line_override(
        recenter_active=guidance_recenter_active,
        watch_active=guidance_watch_active,
        summary=guidance_summary,
        recenter_config={
            "controller_key": "remaining_line_guidance_recentered_after_first_touch",
            "line_state": "softened",
            "decision": "soften_remaining_line",
            "delay": 1200,
            "pressure_mode": recenter_pressure,
            "autonomy_signal": autonomy_signal,
            "delivery_mode": "single_message",
            "summary_note_prefix": "guidance_recenter",
            "notes": ("keep_remaining_line_soft",),
        },
        watch_config={
            "controller_key": "remaining_line_guidance_softened_after_first_touch",
            "line_state": "softened",
            "decision": "soften_remaining_line",
            "delay": 600,
            "pressure_mode": "gentle_resume",
            "autonomy_signal": autonomy_signal,
            "delivery_mode": "single_message",
            "summary_note_prefix": "guidance_watch",
            "notes": ("keep_remaining_line_soft",),
        },
    )


def _build_first_touch_ritual_override(
    *,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    ritual_summary: str,
    ritual_low_pressure: bool,
    ritual_delivery_mode: str,
) -> _LineControllerOverride | None:
    recenter_pressure = "repair_soft" if ritual_low_pressure else "gentle_resume"
    autonomy_signal = (
        "explicit_no_pressure" if ritual_low_pressure else "light_invitation"
    )
    return _resolve_signal_gate_line_override(
        recenter_active=ritual_recenter_active,
        watch_active=ritual_watch_active,
        summary=ritual_summary,
        recenter_config={
            "controller_key": "remaining_line_ritual_recentered_after_first_touch",
            "line_state": "softened",
            "decision": "soften_remaining_line",
            "delay": 900,
            "pressure_mode": recenter_pressure,
            "autonomy_signal": autonomy_signal,
            "delivery_mode": ritual_delivery_mode,
            "summary_note_prefix": "ritual_somatic_recenter",
            "notes": ("keep_remaining_line_soft",),
        },
        watch_config={
            "controller_key": "remaining_line_ritual_softened_after_first_touch",
            "line_state": "softened",
            "decision": "soften_remaining_line",
            "delay": 450,
            "pressure_mode": "gentle_resume",
            "autonomy_signal": autonomy_signal,
            "delivery_mode": ritual_delivery_mode,
            "summary_note_prefix": "ritual_somatic_watch",
            "notes": ("keep_remaining_line_soft",),
        },
    )


def _build_first_touch_low_pressure_override(
    *,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _LineControllerOverride | None:
    if (
        stage_controller_decision.changed
        or dispatch_feedback_assessment.changed
        or stage_replan_assessment.selected_autonomy_signal
        in {"explicit_opt_out", "explicit_no_pressure"}
        or stage_replan_assessment.selected_pressure_mode
        in {"low_pressure_progress", "gentle_resume", "repair_soft"}
    ):
        return _build_line_controller_override(
            controller_key="remaining_line_softened_after_first_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
            additional_delay_seconds=1800,
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
            selected_delivery_mode="single_message",
            controller_notes=[
                "first_touch_already_set_low_pressure",
                "keep_remaining_line_soft",
            ],
        )
    return None


def _resolve_first_touch_line_override(
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
    guidance_repair_soft: bool,
    guidance_low_pressure: bool,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    ritual_summary: str,
    ritual_low_pressure: bool,
    ritual_delivery_mode: str,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _LineControllerOverride | None:
    return (
        _build_first_touch_active_controller_override(
            controller_decision=orchestration_controller_decision,
            recentered_key="remaining_line_orchestration_recentered_after_first_touch",
            softened_key="remaining_line_orchestration_softened_after_first_touch",
        )
        or _build_first_touch_active_controller_override(
            controller_decision=aggregate_controller_decision,
            recentered_key="remaining_line_governance_recentered_after_first_touch",
            softened_key="remaining_line_governance_softened_after_first_touch",
        )
        or _build_first_touch_aggregate_gate_override(
            aggregate_recenter_active=aggregate_recenter_active,
            aggregate_watch_active=aggregate_watch_active,
            aggregate_governance_summary=aggregate_governance_summary,
        )
        or _build_first_touch_governance_family_override(
            governance_flags=governance_flags,
        )
        or _build_first_touch_guidance_override(
            guidance_recenter_active=guidance_recenter_active,
            guidance_watch_active=guidance_watch_active,
            guidance_summary=guidance_summary,
            guidance_repair_soft=guidance_repair_soft,
            guidance_low_pressure=guidance_low_pressure,
        )
        or _build_first_touch_ritual_override(
            ritual_recenter_active=ritual_recenter_active,
            ritual_watch_active=ritual_watch_active,
            ritual_summary=ritual_summary,
            ritual_low_pressure=ritual_low_pressure,
            ritual_delivery_mode=ritual_delivery_mode,
        )
        or _build_first_touch_low_pressure_override(
            stage_controller_decision=stage_controller_decision,
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
        )
    )


def _resolve_second_touch_line_override(
    *,
    governance_flags: dict[str, bool],
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_recenter_active: bool,
    aggregate_watch_active: bool,
    aggregate_governance_summary: str,
    guidance_recenter_active: bool,
    guidance_watch_active: bool,
    guidance_summary: str,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    ritual_summary: str,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
) -> _LineControllerOverride | None:
    defer = dispatch_gate_decision.decision == "defer"
    return (
        _build_second_touch_active_controller_override(
            controller_decision=orchestration_controller_decision,
        )
        or _build_second_touch_aggregate_override(
            aggregate_recenter_active=aggregate_recenter_active,
            aggregate_watch_active=aggregate_watch_active,
            aggregate_governance_summary=aggregate_governance_summary,
            defer=defer,
        )
        or _build_second_touch_governance_family_override(
            governance_flags=governance_flags,
            defer=defer,
        )
        or _build_second_touch_guidance_override(
            guidance_recenter_active=guidance_recenter_active,
            guidance_watch_active=guidance_watch_active,
            guidance_summary=guidance_summary,
            defer=defer,
        )
        or _build_second_touch_ritual_override(
            ritual_recenter_active=ritual_recenter_active,
            ritual_watch_active=ritual_watch_active,
            ritual_summary=ritual_summary,
            defer=defer,
        )
        or _build_second_touch_close_ready_override(
            stage_controller_decision=stage_controller_decision,
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
            dispatch_gate_decision=dispatch_gate_decision,
            defer=defer,
        )
    )


def _build_second_touch_active_controller_override(
    *,
    controller_decision: ProactiveOrchestrationControllerDecision | None,
) -> _LineControllerOverride | None:
    if (
        controller_decision is None
        or controller_decision.status != "active"
        or not controller_decision.changed
        or controller_decision.current_stage_label != "second_touch"
        or controller_decision.line_additional_delay_seconds <= 0
    ):
        return None
    return _build_line_controller_override(
        controller_key=(
            "remaining_line_orchestration_close_ready"
            if controller_decision.decision == "recenter_followup_line"
            else "remaining_line_orchestration_watch_close_ready"
        ),
        line_state="close_ready",
        decision="retire_after_close_loop",
        changed=True,
        additional_delay_seconds=controller_decision.line_additional_delay_seconds,
        selected_pressure_mode=controller_decision.selected_pressure_mode,
        selected_autonomy_signal=controller_decision.selected_autonomy_signal,
        selected_delivery_mode=controller_decision.selected_delivery_mode,
        controller_notes=list(controller_decision.controller_notes),
    )


def _build_second_touch_aggregate_override(
    *,
    aggregate_recenter_active: bool,
    aggregate_watch_active: bool,
    aggregate_governance_summary: str,
    defer: bool,
) -> _LineControllerOverride | None:
    if aggregate_recenter_active:
        return _build_line_controller_override(
            controller_key="remaining_line_governance_close_ready",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            additional_delay_seconds=3900 if defer else 3000,
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
            controller_notes=[
                f"aggregate_governance_recenter:{aggregate_governance_summary}",
                "favor_close_ready_shape",
            ],
        )
    if aggregate_watch_active:
        return _build_line_controller_override(
            controller_key="remaining_line_governance_watch_close_ready",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            additional_delay_seconds=3000 if defer else 2100,
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
            controller_notes=[
                f"aggregate_governance_watch:{aggregate_governance_summary}",
                "favor_close_ready_shape",
            ],
        )
    return None


def _build_second_touch_governance_family_override(
    *,
    governance_flags: dict[str, bool],
    defer: bool,
) -> _LineControllerOverride | None:
    for (
        domain,
        recenter_defer,
        recenter_ready,
        watch_defer,
        watch_ready,
    ) in _SECOND_TOUCH_GOVERNANCE_LINE_OVERRIDE_SPECS:
        if governance_flags[f"{domain}_recenter_active"]:
            return _build_line_controller_override(
                controller_key=f"remaining_line_{domain}_close_ready",
                line_state="close_ready",
                decision="retire_after_close_loop",
                changed=True,
                additional_delay_seconds=recenter_defer if defer else recenter_ready,
                selected_pressure_mode="archive_light_presence",
                selected_autonomy_signal="archive_light_thread",
                selected_delivery_mode="single_message",
                controller_notes=[
                    f"{domain}_governance_recenter",
                    "favor_close_ready_shape",
                ],
            )
        if governance_flags[f"{domain}_watch_active"]:
            return _build_line_controller_override(
                controller_key=f"remaining_line_{domain}_watch_close_ready",
                line_state="close_ready",
                decision="retire_after_close_loop",
                changed=True,
                additional_delay_seconds=watch_defer if defer else watch_ready,
                selected_pressure_mode="archive_light_presence",
                selected_autonomy_signal="archive_light_thread",
                selected_delivery_mode="single_message",
                controller_notes=[
                    f"{domain}_governance_watch",
                    "favor_close_ready_shape",
                ],
            )
    return None


def _build_second_touch_guidance_override(
    *,
    guidance_recenter_active: bool,
    guidance_watch_active: bool,
    guidance_summary: str,
    defer: bool,
) -> _LineControllerOverride | None:
    return _resolve_signal_gate_line_override(
        recenter_active=guidance_recenter_active,
        watch_active=guidance_watch_active,
        summary=guidance_summary,
        defer=defer,
        recenter_config={
            "controller_key": "remaining_line_guidance_close_ready",
            "line_state": "close_ready",
            "decision": "retire_after_close_loop",
            "delay": (900, 600),
            "pressure_mode": "archive_light_presence",
            "autonomy_signal": "archive_light_thread",
            "delivery_mode": "single_message",
            "summary_note_prefix": "guidance_recenter",
            "notes": ("favor_close_ready_shape",),
        },
        watch_config={
            "controller_key": "remaining_line_guidance_watch_close_ready",
            "line_state": "close_ready",
            "decision": "retire_after_close_loop",
            "delay": (600, 450),
            "pressure_mode": "archive_light_presence",
            "autonomy_signal": "archive_light_thread",
            "delivery_mode": "single_message",
            "summary_note_prefix": "guidance_watch",
            "notes": ("favor_close_ready_shape",),
        },
    )


def _build_second_touch_ritual_override(
    *,
    ritual_recenter_active: bool,
    ritual_watch_active: bool,
    ritual_summary: str,
    defer: bool,
) -> _LineControllerOverride | None:
    return _resolve_signal_gate_line_override(
        recenter_active=ritual_recenter_active,
        watch_active=ritual_watch_active,
        summary=ritual_summary,
        defer=defer,
        recenter_config={
            "controller_key": "remaining_line_ritual_close_ready",
            "line_state": "close_ready",
            "decision": "retire_after_close_loop",
            "delay": (750, 600),
            "pressure_mode": "archive_light_presence",
            "autonomy_signal": "archive_light_thread",
            "delivery_mode": "single_message",
            "summary_note_prefix": "ritual_somatic_recenter",
            "notes": ("favor_close_ready_shape",),
        },
        watch_config={
            "controller_key": "remaining_line_ritual_watch_close_ready",
            "line_state": "close_ready",
            "decision": "retire_after_close_loop",
            "delay": (450, 300),
            "pressure_mode": "archive_light_presence",
            "autonomy_signal": "archive_light_thread",
            "delivery_mode": "single_message",
            "summary_note_prefix": "ritual_somatic_watch",
            "notes": ("favor_close_ready_shape",),
        },
    )


def _build_second_touch_close_ready_override(
    *,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    defer: bool,
) -> _LineControllerOverride | None:
    if not (
        dispatch_feedback_assessment.changed
        or stage_controller_decision.changed
        or dispatch_gate_decision.decision == "defer"
        or stage_replan_assessment.selected_pressure_mode
        in {"gentle_resume", "repair_soft"}
        or stage_replan_assessment.selected_autonomy_signal
        in {"explicit_no_pressure", "archive_light_thread"}
    ):
        return None
    return _build_line_controller_override(
        controller_key="remaining_line_close_ready",
        line_state="close_ready",
        decision="retire_after_close_loop",
        changed=True,
        additional_delay_seconds=3600 if defer else 1800,
        selected_pressure_mode="archive_light_presence",
        selected_autonomy_signal="archive_light_thread",
        selected_delivery_mode="single_message",
        controller_notes=[
            "remaining_line_should_finish_lightly",
            "favor_close_ready_shape",
        ],
    )


def build_proactive_line_controller_decision(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    system3_snapshot: System3Snapshot,
    current_stage_label: str,
    current_stage_index: int,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    guidance_plan: GuidancePlan | None = None,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
) -> ProactiveLineControllerDecision:
    if directive.status != "ready" or not directive.eligible:
        return _build_line_hold_decision(current_stage_label, directive)

    remaining_line_plan = _build_remaining_line_plan(
        proactive_cadence_plan=proactive_cadence_plan,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
    )
    exhausted_line_decision = _build_exhausted_line_decision(
        current_stage_label=current_stage_label,
        remaining_line_plan=remaining_line_plan,
        stage_replan_assessment=stage_replan_assessment,
    )
    if exhausted_line_decision is not None:
        return exhausted_line_decision

    controller_state = _build_line_controller_state(
        current_stage_label=current_stage_label,
        stage_replan_assessment=stage_replan_assessment,
    )
    signals = _build_line_controller_signals(
        system3_snapshot=system3_snapshot,
        guidance_plan=guidance_plan,
        aggregate_governance_assessment=aggregate_governance_assessment,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )
    line_override = _resolve_line_controller_override(
        current_stage_label=current_stage_label,
        signals=signals,
        orchestration_controller_decision=orchestration_controller_decision,
        aggregate_controller_decision=aggregate_controller_decision,
        stage_controller_decision=stage_controller_decision,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_gate_decision=dispatch_gate_decision,
    )
    _apply_line_controller_override(controller_state, line_override)

    return ProactiveLineControllerDecision(
        status="active",
        controller_key=controller_state.controller_key,
        trigger_stage_label=current_stage_label,
        line_state=controller_state.line_state,
        decision=controller_state.decision,
        changed=controller_state.changed,
        affected_stage_labels=list(remaining_line_plan.remaining_stage_labels),
        additional_delay_seconds=controller_state.additional_delay_seconds,
        selected_pressure_mode=controller_state.selected_pressure_mode,
        selected_autonomy_signal=controller_state.selected_autonomy_signal,
        selected_delivery_mode=controller_state.selected_delivery_mode,
        controller_notes=_compact(controller_state.controller_notes, limit=5),
        rationale=_build_line_controller_rationale(controller_state.changed),
    )
