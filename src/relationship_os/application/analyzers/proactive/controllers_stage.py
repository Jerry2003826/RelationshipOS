"""Proactive controllers: stage controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch import (
    _build_proactive_aggregate_governance_gate,
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.application.analyzers.proactive.governance_tables import (
    GOVERNANCE_STAGE_DELAY_SPECS,
    build_governance_signal_flags,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateControllerDecision,
    ProactiveAggregateGovernanceAssessment,
    ProactiveCadencePlan,
    ProactiveDispatchFeedbackAssessment,
    ProactiveFollowupDirective,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


@dataclass(frozen=True)
class _StageSpacingOverrideSpec:
    recenter_flag: str
    watch_flag: str
    recenter_key: str
    watch_key: str
    recenter_delay: int
    watch_delay: int
    recenter_strategy_key: str
    watch_strategy_key: str
    recenter_pressure_mode: str
    watch_pressure_mode: str
    recenter_autonomy_signal: str
    watch_autonomy_signal: str
    recenter_delivery_mode: str
    watch_delivery_mode: str
    recenter_note: str
    watch_note: str


@dataclass(frozen=True)
class _StageControllerOverride:
    controller_key: str
    additional_delay_seconds: int
    selected_strategy_key: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_delivery_mode: str
    controller_notes: tuple[str, ...]
    decision: str = "slow_next_stage"
    changed: bool = True


class _FallbackStageOverrideConfig(TypedDict):
    """Parameters for low-pressure / spacing fallback stage overrides."""

    controller_key: str
    default_delay: int
    repair_delay: int
    strategy_key: str
    pressure_mode: str
    autonomy_signal: str
    delivery_mode: str
    notes: list[str]
    trigger_autonomy_signals: frozenset[str]
    trigger_pressure_modes: frozenset[str]
    elevated_delay_pressure_modes: frozenset[str]


@dataclass(frozen=True)
class _StageControllerSignals:
    stage_override_flags: dict[str, bool]
    aggregate_governance_summary: str
    guidance_summary: str
    guidance_repair_soft: bool
    guidance_autonomy_signal: str
    ritual_summary: str
    ritual_repair_soft: bool
    ritual_autonomy_signal: str
    ritual_delivery_mode: str


@dataclass
class _StageControllerState:
    controller_key: str
    decision: str
    changed: bool
    additional_delay_seconds: int
    selected_strategy_key: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_delivery_mode: str
    controller_notes: list[str]


_SECOND_TOUCH_STAGE_GOVERNANCE_SPECS: tuple[tuple[str, str, str, int, int], ...] = tuple(
    (
        domain,
        f"second_touch_{domain}_buffer_spacing",
        f"second_touch_{domain}_watch_spacing",
        recenter_delay,
        watch_delay,
    )
    for domain, recenter_delay, watch_delay in GOVERNANCE_STAGE_DELAY_SPECS
)

_FINAL_SOFT_CLOSE_STAGE_GOVERNANCE_SPECS: tuple[tuple[str, str, str, int, int], ...] = tuple(
    (
        domain,
        f"final_soft_close_{domain}_buffer",
        f"final_soft_close_{domain}_watch_buffer",
        recenter_delay,
        watch_delay,
    )
    for domain, recenter_delay, watch_delay in GOVERNANCE_STAGE_DELAY_SPECS
)


def _build_stage_controller_override(
    *,
    controller_key: str,
    additional_delay_seconds: int,
    selected_strategy_key: str,
    selected_pressure_mode: str,
    selected_autonomy_signal: str,
    selected_delivery_mode: str,
    controller_notes: list[str] | tuple[str, ...],
) -> _StageControllerOverride:
    return _StageControllerOverride(
        controller_key=controller_key,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        controller_notes=tuple(controller_notes),
    )


def _build_stage_hold_decision(
    current_stage_label: str,
    directive: ProactiveFollowupDirective,
) -> ProactiveStageControllerDecision:
    return ProactiveStageControllerDecision(
        status="hold",
        controller_key="hold",
        trigger_stage_label=current_stage_label or "unknown",
        target_stage_label=None,
        decision="hold",
        changed=False,
        additional_delay_seconds=0,
        selected_strategy_key="hold",
        selected_pressure_mode="hold",
        selected_autonomy_signal="none",
        selected_delivery_mode="none",
        rationale=directive.rationale,
    )


def _resolve_next_stage_label(
    *,
    proactive_cadence_plan: ProactiveCadencePlan,
    current_stage_label: str,
    current_stage_index: int,
) -> str | None:
    stage_labels = list(proactive_cadence_plan.stage_labels or [current_stage_label])
    stage_count = max(
        1,
        proactive_cadence_plan.close_after_stage_index or len(stage_labels) or 1,
    )
    return (
        stage_labels[current_stage_index]
        if current_stage_index < min(stage_count, len(stage_labels))
        else None
    )


def _build_exhausted_stage_decision(
    *,
    current_stage_label: str,
    next_stage_label: str | None,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> ProactiveStageControllerDecision | None:
    if next_stage_label is not None:
        return None
    return ProactiveStageControllerDecision(
        status="terminal",
        controller_key=f"{current_stage_label}_line_closed",
        trigger_stage_label=current_stage_label,
        target_stage_label=None,
        decision="close_line",
        changed=False,
        additional_delay_seconds=0,
        selected_strategy_key=stage_replan_assessment.selected_strategy_key,
        selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
        selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
        selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
        rationale=(
            "The current stage already closed the proactive line, so there is no "
            "next stage to schedule."
        ),
    )


def _build_stage_controller_state(
    *,
    next_stage_label: str,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _StageControllerState:
    return _StageControllerState(
        controller_key=f"{next_stage_label}_follow_planned_stage",
        decision="follow_planned_stage",
        changed=False,
        additional_delay_seconds=0,
        selected_strategy_key=stage_replan_assessment.selected_strategy_key,
        selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
        selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
        selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
        controller_notes=[],
    )


def _build_stage_controller_signals(
    *,
    system3_snapshot: System3Snapshot,
    guidance_plan: GuidancePlan | None,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None,
    session_ritual_plan: SessionRitualPlan | None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None,
) -> _StageControllerSignals:
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
    stage_override_flags = dict(governance_flags)
    stage_override_flags.update(
        {
            "aggregate_recenter_active": aggregate_governance_gate["status"] == "recenter",
            "aggregate_watch_active": aggregate_governance_gate["status"] == "watch",
            "guidance_recenter_active": guidance_gate["status"] == "recenter",
            "guidance_watch_active": guidance_gate["status"] == "watch",
            "ritual_recenter_active": ritual_somatic_gate["status"] == "recenter",
            "ritual_watch_active": ritual_somatic_gate["status"] == "watch",
        }
    )
    return _StageControllerSignals(
        stage_override_flags=stage_override_flags,
        aggregate_governance_summary=str(aggregate_governance_gate["summary"]),
        guidance_summary=str(guidance_gate["summary"]),
        guidance_repair_soft=bool(
            guidance_plan is not None
            and (
                guidance_plan.mode in {"repair_guidance", "stabilizing_guidance"}
                or guidance_plan.handoff_mode == "repair_soft_ping"
            )
        ),
        guidance_autonomy_signal=(
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
        ritual_summary=str(ritual_somatic_gate["summary"]),
        ritual_repair_soft=bool(
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
            )
        ),
        ritual_autonomy_signal=(
            "explicit_no_pressure"
            if session_ritual_plan is not None
            and session_ritual_plan.closing_move
            in {
                "repair_soft_close",
                "boundary_safe_close",
                "grounding_close",
                "clarify_pause",
            }
            else "light_invitation"
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


def _resolve_stage_controller_override(
    *,
    next_stage_label: str,
    signals: _StageControllerSignals,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _StageControllerOverride | None:
    if next_stage_label == "second_touch":
        return _resolve_second_touch_stage_override(
            stage_override_flags=signals.stage_override_flags,
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_controller_decision=aggregate_controller_decision,
            aggregate_governance_summary=signals.aggregate_governance_summary,
            guidance_summary=signals.guidance_summary,
            guidance_repair_soft=signals.guidance_repair_soft,
            guidance_autonomy_signal=signals.guidance_autonomy_signal,
            ritual_summary=signals.ritual_summary,
            ritual_repair_soft=signals.ritual_repair_soft,
            ritual_autonomy_signal=signals.ritual_autonomy_signal,
            ritual_delivery_mode=signals.ritual_delivery_mode,
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
        )
    if next_stage_label == "final_soft_close":
        return _resolve_final_soft_close_stage_override(
            stage_override_flags=signals.stage_override_flags,
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_controller_decision=aggregate_controller_decision,
            aggregate_governance_summary=signals.aggregate_governance_summary,
            guidance_summary=signals.guidance_summary,
            ritual_summary=signals.ritual_summary,
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
        )
    return None


def _apply_stage_controller_override(
    state: _StageControllerState,
    stage_override: _StageControllerOverride | None,
) -> None:
    if stage_override is None:
        return
    state.controller_key = stage_override.controller_key
    state.decision = stage_override.decision
    state.changed = stage_override.changed
    state.additional_delay_seconds = stage_override.additional_delay_seconds
    state.selected_strategy_key = stage_override.selected_strategy_key
    state.selected_pressure_mode = stage_override.selected_pressure_mode
    state.selected_autonomy_signal = stage_override.selected_autonomy_signal
    state.selected_delivery_mode = stage_override.selected_delivery_mode
    state.controller_notes.extend(stage_override.controller_notes)


def _build_stage_controller_rationale(changed: bool) -> str:
    if changed:
        return (
            "The next proactive stage should be slowed down so the multi-stage line "
            "keeps shedding pressure instead of escalating just because the next slot exists."
        )
    return (
        "The next proactive stage can keep its planned timing because the current "
        "dispatch did not introduce extra pressure that needs spacing correction."
    )


def _resolve_stage_spacing_spec_override(
    *,
    active_flags: dict[str, bool],
    specs: tuple[_StageSpacingOverrideSpec, ...],
    spacing_note: str,
) -> _StageControllerOverride | None:
    for spec in specs:
        if active_flags.get(spec.recenter_flag, False):
            return _build_stage_controller_override(
                controller_key=spec.recenter_key,
                additional_delay_seconds=spec.recenter_delay,
                selected_strategy_key=spec.recenter_strategy_key,
                selected_pressure_mode=spec.recenter_pressure_mode,
                selected_autonomy_signal=spec.recenter_autonomy_signal,
                selected_delivery_mode=spec.recenter_delivery_mode,
                controller_notes=[spec.recenter_note, spacing_note],
            )
        if active_flags.get(spec.watch_flag, False):
            return _build_stage_controller_override(
                controller_key=spec.watch_key,
                additional_delay_seconds=spec.watch_delay,
                selected_strategy_key=spec.watch_strategy_key,
                selected_pressure_mode=spec.watch_pressure_mode,
                selected_autonomy_signal=spec.watch_autonomy_signal,
                selected_delivery_mode=spec.watch_delivery_mode,
                controller_notes=[spec.watch_note, spacing_note],
            )
    return None


def _build_second_touch_stage_spacing_specs(
    *,
    aggregate_governance_summary: str,
    guidance_summary: str,
    guidance_repair_soft: bool,
    guidance_autonomy_signal: str,
    ritual_summary: str,
    ritual_repair_soft: bool,
    ritual_autonomy_signal: str,
    ritual_delivery_mode: str,
) -> tuple[_StageSpacingOverrideSpec, ...]:
    specs = [
        _StageSpacingOverrideSpec(
            recenter_flag="aggregate_recenter_active",
            watch_flag="aggregate_watch_active",
            recenter_key="second_touch_aggregate_governance_buffer_spacing",
            watch_key="second_touch_aggregate_governance_watch_spacing",
            recenter_delay=6300,
            watch_delay=4050,
            recenter_strategy_key="repair_soft_resume_bridge",
            watch_strategy_key="resume_context_bridge",
            recenter_pressure_mode="repair_soft",
            watch_pressure_mode="gentle_resume",
            recenter_autonomy_signal="explicit_no_pressure",
            watch_autonomy_signal="explicit_no_pressure",
            recenter_delivery_mode="single_message",
            watch_delivery_mode="single_message",
            recenter_note=f"aggregate_governance_recenter:{aggregate_governance_summary}",
            watch_note=f"aggregate_governance_watch:{aggregate_governance_summary}",
        )
    ]
    for (
        domain,
        recenter_key,
        watch_key,
        recenter_delay,
        watch_delay,
    ) in _SECOND_TOUCH_STAGE_GOVERNANCE_SPECS:
        specs.append(
            _StageSpacingOverrideSpec(
                recenter_flag=f"{domain}_recenter_active",
                watch_flag=f"{domain}_watch_active",
                recenter_key=recenter_key,
                watch_key=watch_key,
                recenter_delay=recenter_delay,
                watch_delay=watch_delay,
                recenter_strategy_key="repair_soft_resume_bridge",
                watch_strategy_key="resume_context_bridge",
                recenter_pressure_mode="repair_soft",
                watch_pressure_mode="gentle_resume",
                recenter_autonomy_signal="explicit_no_pressure",
                watch_autonomy_signal="explicit_no_pressure",
                recenter_delivery_mode="single_message",
                watch_delivery_mode="single_message",
                recenter_note=f"{domain}_governance_recenter",
                watch_note=f"{domain}_governance_watch",
            )
        )
    specs.extend(
        [
            _StageSpacingOverrideSpec(
                recenter_flag="guidance_recenter_active",
                watch_flag="guidance_watch_active",
                recenter_key="second_touch_guidance_recenter_spacing",
                watch_key="second_touch_guidance_watch_spacing",
                recenter_delay=2100,
                watch_delay=1200,
                recenter_strategy_key=(
                    "repair_soft_resume_bridge" if guidance_repair_soft else "resume_context_bridge"
                ),
                watch_strategy_key="resume_context_bridge",
                recenter_pressure_mode=("repair_soft" if guidance_repair_soft else "gentle_resume"),
                watch_pressure_mode="gentle_resume",
                recenter_autonomy_signal=guidance_autonomy_signal,
                watch_autonomy_signal=guidance_autonomy_signal,
                recenter_delivery_mode="single_message",
                watch_delivery_mode="single_message",
                recenter_note=f"guidance_recenter:{guidance_summary}",
                watch_note=f"guidance_watch:{guidance_summary}",
            ),
            _StageSpacingOverrideSpec(
                recenter_flag="ritual_recenter_active",
                watch_flag="ritual_watch_active",
                recenter_key="second_touch_ritual_recenter_spacing",
                watch_key="second_touch_ritual_watch_spacing",
                recenter_delay=1500,
                watch_delay=900,
                recenter_strategy_key=(
                    "repair_soft_resume_bridge" if ritual_repair_soft else "resume_context_bridge"
                ),
                watch_strategy_key="resume_context_bridge",
                recenter_pressure_mode=("repair_soft" if ritual_repair_soft else "gentle_resume"),
                watch_pressure_mode="gentle_resume",
                recenter_autonomy_signal=ritual_autonomy_signal,
                watch_autonomy_signal=ritual_autonomy_signal,
                recenter_delivery_mode=ritual_delivery_mode,
                watch_delivery_mode=ritual_delivery_mode,
                recenter_note=f"ritual_somatic_recenter:{ritual_summary}",
                watch_note=f"ritual_somatic_watch:{ritual_summary}",
            ),
        ]
    )
    return tuple(specs)


def _build_final_soft_close_stage_spacing_specs(
    *,
    aggregate_governance_summary: str,
    guidance_summary: str,
    ritual_summary: str,
) -> tuple[_StageSpacingOverrideSpec, ...]:
    specs = [
        _StageSpacingOverrideSpec(
            recenter_flag="aggregate_recenter_active",
            watch_flag="aggregate_watch_active",
            recenter_key="final_soft_close_aggregate_governance_buffer",
            watch_key="final_soft_close_aggregate_governance_watch_buffer",
            recenter_delay=5700,
            watch_delay=3900,
            recenter_strategy_key="continuity_soft_ping",
            watch_strategy_key="continuity_soft_ping",
            recenter_pressure_mode="archive_light_presence",
            watch_pressure_mode="archive_light_presence",
            recenter_autonomy_signal="archive_light_thread",
            watch_autonomy_signal="archive_light_thread",
            recenter_delivery_mode="single_message",
            watch_delivery_mode="single_message",
            recenter_note=f"aggregate_governance_recenter:{aggregate_governance_summary}",
            watch_note=f"aggregate_governance_watch:{aggregate_governance_summary}",
        )
    ]
    for (
        domain,
        recenter_key,
        watch_key,
        recenter_delay,
        watch_delay,
    ) in _FINAL_SOFT_CLOSE_STAGE_GOVERNANCE_SPECS:
        specs.append(
            _StageSpacingOverrideSpec(
                recenter_flag=f"{domain}_recenter_active",
                watch_flag=f"{domain}_watch_active",
                recenter_key=recenter_key,
                watch_key=watch_key,
                recenter_delay=recenter_delay,
                watch_delay=watch_delay,
                recenter_strategy_key="continuity_soft_ping",
                watch_strategy_key="continuity_soft_ping",
                recenter_pressure_mode="archive_light_presence",
                watch_pressure_mode="archive_light_presence",
                recenter_autonomy_signal="archive_light_thread",
                watch_autonomy_signal="archive_light_thread",
                recenter_delivery_mode="single_message",
                watch_delivery_mode="single_message",
                recenter_note=f"{domain}_governance_recenter",
                watch_note=f"{domain}_governance_watch",
            )
        )
    specs.extend(
        [
            _StageSpacingOverrideSpec(
                recenter_flag="guidance_recenter_active",
                watch_flag="guidance_watch_active",
                recenter_key="final_soft_close_guidance_recenter_buffer",
                watch_key="final_soft_close_guidance_watch_buffer",
                recenter_delay=1800,
                watch_delay=900,
                recenter_strategy_key="continuity_soft_ping",
                watch_strategy_key="continuity_soft_ping",
                recenter_pressure_mode="archive_light_presence",
                watch_pressure_mode="archive_light_presence",
                recenter_autonomy_signal="archive_light_thread",
                watch_autonomy_signal="archive_light_thread",
                recenter_delivery_mode="single_message",
                watch_delivery_mode="single_message",
                recenter_note=f"guidance_recenter:{guidance_summary}",
                watch_note=f"guidance_watch:{guidance_summary}",
            ),
            _StageSpacingOverrideSpec(
                recenter_flag="ritual_recenter_active",
                watch_flag="ritual_watch_active",
                recenter_key="final_soft_close_ritual_recenter_buffer",
                watch_key="final_soft_close_ritual_watch_buffer",
                recenter_delay=1200,
                watch_delay=600,
                recenter_strategy_key="continuity_soft_ping",
                watch_strategy_key="continuity_soft_ping",
                recenter_pressure_mode="archive_light_presence",
                watch_pressure_mode="archive_light_presence",
                recenter_autonomy_signal="archive_light_thread",
                watch_autonomy_signal="archive_light_thread",
                recenter_delivery_mode="single_message",
                watch_delivery_mode="single_message",
                recenter_note=f"ritual_somatic_recenter:{ritual_summary}",
                watch_note=f"ritual_somatic_watch:{ritual_summary}",
            ),
        ]
    )
    return tuple(specs)


_ACTIVE_STAGE_CONTROLLER_KEYS: dict[str, tuple[str, str, str, str]] = {
    "second_touch": (
        "second_touch_orchestration_recenter_spacing",
        "second_touch_orchestration_watch_spacing",
        "second_touch_aggregate_governance_buffer_spacing",
        "second_touch_aggregate_governance_watch_spacing",
    ),
    "final_soft_close": (
        "final_soft_close_orchestration_recenter_buffer",
        "final_soft_close_orchestration_watch_buffer",
        "final_soft_close_aggregate_governance_buffer",
        "final_soft_close_aggregate_governance_watch_buffer",
    ),
}

_SECOND_TOUCH_FALLBACK_STAGE_OVERRIDE_CONFIG: _FallbackStageOverrideConfig = {
    "controller_key": "second_touch_low_pressure_spacing",
    "default_delay": 3600,
    "repair_delay": 5400,
    "strategy_key": "resume_context_bridge",
    "pressure_mode": "gentle_resume",
    "autonomy_signal": "explicit_no_pressure",
    "delivery_mode": "single_message",
    "notes": ["first_touch_already_landed", "space_out_second_touch"],
    "trigger_autonomy_signals": frozenset({"explicit_opt_out", "explicit_no_pressure"}),
    "trigger_pressure_modes": frozenset(
        {"low_pressure_progress", "gentle_resume", "repair_soft"}
    ),
    "elevated_delay_pressure_modes": frozenset({"gentle_resume", "repair_soft"}),
}

_FINAL_SOFT_CLOSE_FALLBACK_STAGE_OVERRIDE_CONFIG: _FallbackStageOverrideConfig = {
    "controller_key": "final_soft_close_breathing_room",
    "default_delay": 5400,
    "repair_delay": 7200,
    "strategy_key": "continuity_soft_ping",
    "pressure_mode": "archive_light_presence",
    "autonomy_signal": "archive_light_thread",
    "delivery_mode": "single_message",
    "notes": [
        "later_touch_should_not_chase",
        "leave_more_breathing_room_before_close",
    ],
    "trigger_autonomy_signals": frozenset({"explicit_no_pressure", "archive_light_thread"}),
    "trigger_pressure_modes": frozenset({"gentle_resume", "repair_soft"}),
    "elevated_delay_pressure_modes": frozenset({"repair_soft"}),
}


def _resolve_active_controller_stage_override(
    *,
    next_stage_label: str,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    key_prefix: str,
) -> _StageControllerOverride | None:
    """Apply orchestration or aggregate controller spacing when active for the target stage."""
    keys = _ACTIVE_STAGE_CONTROLLER_KEYS.get(key_prefix)
    if keys is None:
        return None
    orch_recenter_key, orch_watch_key, aggregate_recenter_key, aggregate_watch_key = keys
    if (
        orchestration_controller_decision is not None
        and orchestration_controller_decision.status == "active"
        and orchestration_controller_decision.changed
        and orchestration_controller_decision.next_stage_label == next_stage_label
        and orchestration_controller_decision.stage_additional_delay_seconds > 0
    ):
        return _build_stage_controller_override(
            controller_key=(
                orch_recenter_key
                if orchestration_controller_decision.decision == "recenter_followup_line"
                else orch_watch_key
            ),
            additional_delay_seconds=orchestration_controller_decision.stage_additional_delay_seconds,
            selected_strategy_key=orchestration_controller_decision.selected_strategy_key,
            selected_pressure_mode=orchestration_controller_decision.selected_pressure_mode,
            selected_autonomy_signal=orchestration_controller_decision.selected_autonomy_signal,
            selected_delivery_mode=orchestration_controller_decision.selected_delivery_mode,
            controller_notes=list(orchestration_controller_decision.controller_notes),
        )
    if (
        aggregate_controller_decision is not None
        and aggregate_controller_decision.status == "active"
        and aggregate_controller_decision.changed
        and aggregate_controller_decision.next_stage_label == next_stage_label
        and aggregate_controller_decision.stage_additional_delay_seconds > 0
    ):
        return _build_stage_controller_override(
            controller_key=(
                aggregate_recenter_key
                if aggregate_controller_decision.decision == "recenter_followup_line"
                else aggregate_watch_key
            ),
            additional_delay_seconds=aggregate_controller_decision.stage_additional_delay_seconds,
            selected_strategy_key=aggregate_controller_decision.selected_strategy_key,
            selected_pressure_mode=aggregate_controller_decision.selected_pressure_mode,
            selected_autonomy_signal=aggregate_controller_decision.selected_autonomy_signal,
            selected_delivery_mode=aggregate_controller_decision.selected_delivery_mode,
            controller_notes=list(aggregate_controller_decision.controller_notes),
        )
    return None


def _resolve_fallback_stage_override(
    *,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    stage_label: str,
    config: _FallbackStageOverrideConfig,
) -> _StageControllerOverride | None:
    """Build a low-pressure spacing override when dispatch or replan signals warrant it."""
    assert stage_label in {"second_touch", "final_soft_close"}
    if not (
        dispatch_feedback_assessment.changed
        or stage_replan_assessment.selected_autonomy_signal in config["trigger_autonomy_signals"]
        or stage_replan_assessment.selected_pressure_mode in config["trigger_pressure_modes"]
    ):
        return None
    additional_delay_seconds = (
        config["repair_delay"]
        if stage_replan_assessment.selected_pressure_mode
        in config["elevated_delay_pressure_modes"]
        else config["default_delay"]
    )
    return _build_stage_controller_override(
        controller_key=config["controller_key"],
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=config["strategy_key"],
        selected_pressure_mode=config["pressure_mode"],
        selected_autonomy_signal=config["autonomy_signal"],
        selected_delivery_mode=config["delivery_mode"],
        controller_notes=list(config["notes"]),
    )


def _resolve_second_touch_stage_override(
    *,
    stage_override_flags: dict[str, bool],
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    aggregate_governance_summary: str,
    guidance_summary: str,
    guidance_repair_soft: bool,
    guidance_autonomy_signal: str,
    ritual_summary: str,
    ritual_repair_soft: bool,
    ritual_autonomy_signal: str,
    ritual_delivery_mode: str,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _StageControllerOverride | None:
    return (
        _resolve_active_controller_stage_override(
            next_stage_label="second_touch",
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_controller_decision=aggregate_controller_decision,
            key_prefix="second_touch",
        )
        or _resolve_stage_spacing_spec_override(
            active_flags=stage_override_flags,
            specs=_build_second_touch_stage_spacing_specs(
                aggregate_governance_summary=aggregate_governance_summary,
                guidance_summary=guidance_summary,
                guidance_repair_soft=guidance_repair_soft,
                guidance_autonomy_signal=guidance_autonomy_signal,
                ritual_summary=ritual_summary,
                ritual_repair_soft=ritual_repair_soft,
                ritual_autonomy_signal=ritual_autonomy_signal,
                ritual_delivery_mode=ritual_delivery_mode,
            ),
            spacing_note="space_out_second_touch",
        )
        or _resolve_fallback_stage_override(
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
            stage_label="second_touch",
            config=_SECOND_TOUCH_FALLBACK_STAGE_OVERRIDE_CONFIG,
        )
    )


def _resolve_final_soft_close_stage_override(
    *,
    stage_override_flags: dict[str, bool],
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None,
    aggregate_governance_summary: str,
    guidance_summary: str,
    ritual_summary: str,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_replan_assessment: ProactiveStageReplanAssessment,
) -> _StageControllerOverride | None:
    return (
        _resolve_active_controller_stage_override(
            next_stage_label="final_soft_close",
            orchestration_controller_decision=orchestration_controller_decision,
            aggregate_controller_decision=aggregate_controller_decision,
            key_prefix="final_soft_close",
        )
        or _resolve_stage_spacing_spec_override(
            active_flags=stage_override_flags,
            specs=_build_final_soft_close_stage_spacing_specs(
                aggregate_governance_summary=aggregate_governance_summary,
                guidance_summary=guidance_summary,
                ritual_summary=ritual_summary,
            ),
            spacing_note="leave_more_breathing_room_before_close",
        )
        or _resolve_fallback_stage_override(
            dispatch_feedback_assessment=dispatch_feedback_assessment,
            stage_replan_assessment=stage_replan_assessment,
            stage_label="final_soft_close",
            config=_FINAL_SOFT_CLOSE_FALLBACK_STAGE_OVERRIDE_CONFIG,
        )
    )


def build_proactive_stage_controller_decision(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    system3_snapshot: System3Snapshot,
    current_stage_label: str,
    current_stage_index: int,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    guidance_plan: GuidancePlan | None = None,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
) -> ProactiveStageControllerDecision:
    if directive.status != "ready" or not directive.eligible:
        return _build_stage_hold_decision(current_stage_label, directive)

    next_stage_label = _resolve_next_stage_label(
        proactive_cadence_plan=proactive_cadence_plan,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
    )
    exhausted_stage_decision = _build_exhausted_stage_decision(
        current_stage_label=current_stage_label,
        next_stage_label=next_stage_label,
        stage_replan_assessment=stage_replan_assessment,
    )
    if exhausted_stage_decision is not None:
        return exhausted_stage_decision

    controller_state = _build_stage_controller_state(
        next_stage_label=next_stage_label,
        stage_replan_assessment=stage_replan_assessment,
    )
    signals = _build_stage_controller_signals(
        system3_snapshot=system3_snapshot,
        guidance_plan=guidance_plan,
        aggregate_governance_assessment=aggregate_governance_assessment,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )
    stage_override = _resolve_stage_controller_override(
        next_stage_label=next_stage_label,
        signals=signals,
        orchestration_controller_decision=orchestration_controller_decision,
        aggregate_controller_decision=aggregate_controller_decision,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_replan_assessment=stage_replan_assessment,
    )
    _apply_stage_controller_override(controller_state, stage_override)

    return ProactiveStageControllerDecision(
        status="active",
        controller_key=controller_state.controller_key,
        trigger_stage_label=current_stage_label,
        target_stage_label=next_stage_label,
        decision=controller_state.decision,
        changed=controller_state.changed,
        additional_delay_seconds=controller_state.additional_delay_seconds,
        selected_strategy_key=controller_state.selected_strategy_key,
        selected_pressure_mode=controller_state.selected_pressure_mode,
        selected_autonomy_signal=controller_state.selected_autonomy_signal,
        selected_delivery_mode=controller_state.selected_delivery_mode,
        controller_notes=_compact(controller_state.controller_notes, limit=5),
        rationale=_build_stage_controller_rationale(controller_state.changed),
    )
