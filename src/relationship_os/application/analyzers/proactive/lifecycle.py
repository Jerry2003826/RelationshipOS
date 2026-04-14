"""Proactive lifecycle decision chain.

state → transition → machine → controller → envelope → scheduler →
window → queue → dispatch → outcome → resolution → activation →
settlement → ... → stratum → layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ProactiveAggregateControllerDecision,
    ProactiveDispatchEnvelopeDecision,
    ProactiveDispatchGateDecision,
    ProactiveLineMachineDecision,
    ProactiveLineStateDecision,
    ProactiveLineTransitionDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveSchedulingPlan,
    ProactiveStageMachineDecision,
)
from relationship_os.domain.contracts.lifecycle import (
    ProactiveLifecycleActivationDecision,
    ProactiveLifecycleAncestryDecision,
    ProactiveLifecycleArmingDecision,
    ProactiveLifecycleAssuranceDecision,
    ProactiveLifecycleAttestationDecision,
    ProactiveLifecycleAuthorizationDecision,
    ProactiveLifecycleAvailabilityDecision,
    ProactiveLifecycleBedrockDecision,
    ProactiveLifecycleCandidateDecision,
    ProactiveLifecycleCertificationDecision,
    ProactiveLifecycleClosureDecision,
    ProactiveLifecycleCompletionDecision,
    ProactiveLifecycleConclusionDecision,
    ProactiveLifecycleConfirmationDecision,
    ProactiveLifecycleContinuationDecision,
    ProactiveLifecycleControllerDecision,
    ProactiveLifecycleDispatchDecision,
    ProactiveLifecycleDispositionDecision,
    ProactiveLifecycleDurabilityDecision,
    ProactiveLifecycleEligibilityDecision,
    ProactiveLifecycleEnactmentDecision,
    ProactiveLifecycleEndorsementDecision,
    ProactiveLifecycleEnvelopeDecision,
    ProactiveLifecycleFinalityDecision,
    ProactiveLifecycleFoundationDecision,
    ProactiveLifecycleGuardianshipDecision,
    ProactiveLifecycleHandoffDecision,
    ProactiveLifecycleHeritageDecision,
    ProactiveLifecycleLaunchDecision,
    ProactiveLifecycleLayerDecision,
    ProactiveLifecycleLegacyDecision,
    ProactiveLifecycleLineageDecision,
    ProactiveLifecycleLongevityDecision,
    ProactiveLifecycleMachineDecision,
    ProactiveLifecycleOriginDecision,
    ProactiveLifecycleOutcomeDecision,
    ProactiveLifecycleOversightDecision,
    ProactiveLifecyclePersistenceDecision,
    ProactiveLifecycleProvenanceDecision,
    ProactiveLifecycleQueueDecision,
    ProactiveLifecycleRatificationDecision,
    ProactiveLifecycleReactivationDecision,
    ProactiveLifecycleReadinessDecision,
    ProactiveLifecycleReentryDecision,
    ProactiveLifecycleResidencyDecision,
    ProactiveLifecycleResolutionDecision,
    ProactiveLifecycleResumptionDecision,
    ProactiveLifecycleRetentionDecision,
    ProactiveLifecycleRootDecision,
    ProactiveLifecycleSchedulerDecision,
    ProactiveLifecycleSelectabilityDecision,
    ProactiveLifecycleSettlementDecision,
    ProactiveLifecycleStandingDecision,
    ProactiveLifecycleStateDecision,
    ProactiveLifecycleStewardshipDecision,
    ProactiveLifecycleStratumDecision,
    ProactiveLifecycleSubstrateDecision,
    ProactiveLifecycleSustainmentDecision,
    ProactiveLifecycleTenureDecision,
    ProactiveLifecycleTransitionDecision,
    ProactiveLifecycleTriggerDecision,
    ProactiveLifecycleVerificationDecision,
    ProactiveLifecycleWindowDecision,
)


@dataclass(frozen=True)
class _LifecycleStateShape:
    status: str
    state_mode: str
    lifecycle_mode: str
    actionability: str
    note: str | None


@dataclass(frozen=True)
class _LifecycleEnvelopeShape:
    status: str
    lifecycle_state: str
    decision: str
    envelope_mode: str
    actionability: str
    changed: bool


@dataclass(frozen=True)
class _LifecycleDispatchShape:
    status: str
    decision: str
    dispatch_mode: str
    actionability: str
    changed: bool
    primary_source: str
    note: str | None


def _resolve_lifecycle_state_shape(
    *,
    line_machine_decision: ProactiveLineMachineDecision,
    stage_machine_decision: ProactiveStageMachineDecision,
) -> _LifecycleStateShape:
    if (
        line_machine_decision.lifecycle_mode == "terminal"
        or stage_machine_decision.lifecycle_mode == "terminal"
    ):
        return _LifecycleStateShape(
            status="terminal",
            state_mode="lifecycle_terminal",
            lifecycle_mode="terminal",
            actionability="retire",
            note="terminal_line",
        )
    if (
        line_machine_decision.lifecycle_mode == "winding_down"
        or stage_machine_decision.lifecycle_mode == "winding_down"
    ):
        return _LifecycleStateShape(
            status="active",
            state_mode="lifecycle_winding_down",
            lifecycle_mode="winding_down",
            actionability="close_loop",
            note="winding_down_line",
        )
    if (
        line_machine_decision.lifecycle_mode == "buffered"
        or stage_machine_decision.lifecycle_mode in {"buffered", "waiting"}
    ):
        return _LifecycleStateShape(
            status="scheduled",
            state_mode="lifecycle_buffered",
            lifecycle_mode="buffered",
            actionability="buffer",
            note="buffered_line",
        )
    if (
        line_machine_decision.lifecycle_mode == "active_softened"
        or stage_machine_decision.machine_mode == "dispatching_softened_stage"
    ):
        return _LifecycleStateShape(
            status="active",
            state_mode="lifecycle_softened",
            lifecycle_mode="active_softened",
            actionability="soften",
            note="softened_line",
        )
    if (
        line_machine_decision.lifecycle_mode == "dormant"
        or stage_machine_decision.lifecycle_mode == "dormant"
    ):
        return _LifecycleStateShape(
            status="hold",
            state_mode="lifecycle_dormant",
            lifecycle_mode="dormant",
            actionability="hold",
            note="dormant_line",
        )
    if stage_machine_decision.lifecycle_mode == "dispatching":
        return _LifecycleStateShape(
            status="active",
            state_mode="lifecycle_dispatching",
            lifecycle_mode="active",
            actionability="dispatch",
            note="dispatching_stage",
        )
    return _LifecycleStateShape(
        status=line_machine_decision.status or stage_machine_decision.status or "active",
        state_mode="lifecycle_active",
        lifecycle_mode="active",
        actionability="advance",
        note=None,
    )


def _resolve_lifecycle_state_rationale(lifecycle_mode: str) -> str:
    if lifecycle_mode == "terminal":
        return (
            "The proactive lifecycle is already terminal, so the line should retire "
            "instead of leaving more proactive motion alive."
        )
    if lifecycle_mode == "winding_down":
        return (
            "The proactive lifecycle is winding down, so remaining movement should "
            "stay close-loop and low-pressure."
        )
    if lifecycle_mode in {"buffered", "active_softened"}:
        return (
            "The proactive lifecycle is softened, so the whole line should leave "
            "extra user space before any further dispatch."
        )
    return (
        "The proactive lifecycle state now combines the current stage machine, "
        "the line machine, and the orchestration layer into one observable posture."
    )


def _resolve_lifecycle_envelope_shape(
    *,
    lifecycle_controller_decision: ProactiveLifecycleControllerDecision,
    lifecycle_machine_decision: ProactiveLifecycleMachineDecision,
    changed: bool,
) -> _LifecycleEnvelopeShape:
    if lifecycle_controller_decision.decision == "retire_lifecycle":
        return _LifecycleEnvelopeShape(
            status="terminal",
            lifecycle_state="terminal",
            decision="retire_lifecycle_shape",
            envelope_mode="terminal_lifecycle_shape",
            actionability="retire",
            changed=True,
        )
    if lifecycle_controller_decision.decision == "close_loop_lifecycle":
        return _LifecycleEnvelopeShape(
            status="active",
            lifecycle_state="winding_down",
            decision="close_loop_lifecycle_shape",
            envelope_mode="winding_down_lifecycle_shape",
            actionability="close_loop",
            changed=True,
        )
    if lifecycle_controller_decision.decision == "buffer_lifecycle":
        return _LifecycleEnvelopeShape(
            status="scheduled",
            lifecycle_state="buffered",
            decision="buffer_lifecycle_shape",
            envelope_mode="buffered_lifecycle_shape",
            actionability="buffer",
            changed=True,
        )
    if lifecycle_controller_decision.decision == "soften_lifecycle":
        return _LifecycleEnvelopeShape(
            status="active",
            lifecycle_state="softened",
            decision="soften_lifecycle_shape",
            envelope_mode="softened_lifecycle_shape",
            actionability="soften",
            changed=True,
        )
    if lifecycle_controller_decision.decision == "hold_lifecycle":
        return _LifecycleEnvelopeShape(
            status="hold",
            lifecycle_state="dormant",
            decision="hold_lifecycle_shape",
            envelope_mode="dormant_lifecycle_shape",
            actionability="hold",
            changed=True,
        )
    if lifecycle_controller_decision.decision == "dispatch_lifecycle":
        return _LifecycleEnvelopeShape(
            status="active",
            lifecycle_state="dispatching",
            decision="dispatch_lifecycle_shape",
            envelope_mode="dispatching_lifecycle_shape",
            actionability="dispatch",
            changed=True,
        )
    return _LifecycleEnvelopeShape(
        status=(
            lifecycle_controller_decision.status
            or lifecycle_machine_decision.status
            or "active"
        ),
        lifecycle_state=(
            lifecycle_controller_decision.lifecycle_state
            or lifecycle_machine_decision.lifecycle_mode
            or "active"
        ),
        decision="continue_lifecycle_shape",
        envelope_mode="active_lifecycle_shape",
        actionability="continue",
        changed=changed,
    )


def _resolve_lifecycle_envelope_rationale(actionability: str) -> str:
    if actionability == "retire":
        return (
            "The proactive lifecycle envelope retires the line because the lifecycle stack "
            "has already moved into a terminal posture."
        )
    if actionability == "close_loop":
        return (
            "The proactive lifecycle envelope keeps the line in a winding-down shape so "
            "the remaining touch stays close-loop and low-pressure."
        )
    if actionability in {"buffer", "soften"}:
        return (
            "The proactive lifecycle envelope keeps a softened buffered execution shape so "
            "later touches inherit more user space and lower pressure."
        )
    if actionability == "dispatch":
        return (
            "The proactive lifecycle envelope can still dispatch, but it now does so as "
            "an explicit lifecycle-level execution posture."
        )
    return (
        "The proactive lifecycle envelope keeps the line on its current lifecycle posture "
        "because the higher-order lifecycle stack did not need to reshape execution."
    )


def _resolve_lifecycle_dispatch_shape(
    *,
    lifecycle_queue_decision: ProactiveLifecycleQueueDecision,
    gate_decision: str,
    queue_decision: str,
    lifecycle_state: str,
    queue_status: str,
    rendered_unit_count: int,
    has_followup_content: bool,
    primary_source: str,
) -> _LifecycleDispatchShape:
    if rendered_unit_count <= 0 or not has_followup_content:
        return _LifecycleDispatchShape(
            status="hold",
            decision="hold_lifecycle_dispatch",
            dispatch_mode="hold_lifecycle_dispatch",
            actionability="hold",
            changed=True,
            primary_source=(
                "rendering" if primary_source in {"cadence", "queue", "gate"} else primary_source
            ),
            note="empty_followup_units",
        )
    if (
        queue_decision == "retire_lifecycle_queue"
        or lifecycle_state == "terminal"
        or queue_status == "terminal"
    ):
        return _LifecycleDispatchShape(
            status="terminal",
            decision="retire_lifecycle_dispatch",
            dispatch_mode="terminal_lifecycle_dispatch",
            actionability="retire",
            changed=True,
            primary_source=primary_source,
            note=None,
        )
    if gate_decision == "hold":
        return _LifecycleDispatchShape(
            status="hold",
            decision="hold_lifecycle_dispatch",
            dispatch_mode="hold_lifecycle_dispatch",
            actionability="hold",
            changed=True,
            primary_source=primary_source,
            note=None,
        )
    if (
        gate_decision == "defer"
        or queue_decision in {"buffer_lifecycle_queue", "defer_lifecycle_queue"}
        or queue_status in {"waiting", "scheduled"}
    ):
        return _LifecycleDispatchShape(
            status="scheduled",
            decision="reschedule_lifecycle_dispatch",
            dispatch_mode="rescheduled_lifecycle_dispatch",
            actionability="buffer",
            changed=True,
            primary_source=primary_source,
            note=None,
        )
    if (
        queue_decision in {"close_loop_lifecycle_queue", "overdue_close_loop_lifecycle_queue"}
        or lifecycle_state == "winding_down"
    ):
        return _LifecycleDispatchShape(
            status="active",
            decision="close_loop_lifecycle_dispatch",
            dispatch_mode="close_loop_lifecycle_dispatch",
            actionability="close_loop",
            changed=True,
            primary_source=primary_source,
            note=None,
        )
    if (
        queue_decision in {"dispatch_lifecycle_queue", "overdue_lifecycle_queue"}
        or queue_status in {"due", "overdue"}
    ):
        return _LifecycleDispatchShape(
            status="active",
            decision="dispatch_lifecycle_now",
            dispatch_mode="ready_lifecycle_dispatch",
            actionability="dispatch",
            changed=True,
            primary_source=primary_source,
            note=None,
        )
    return _LifecycleDispatchShape(
        status="hold",
        decision="hold_lifecycle_dispatch",
        dispatch_mode="hold_lifecycle_dispatch",
        actionability="hold",
        changed=True,
        primary_source=primary_source,
        note="fallback_hold",
    )


def _resolve_lifecycle_dispatch_rationale(
    decision: str,
    dispatch_notes: list[str],
) -> str:
    if decision == "dispatch_lifecycle_now":
        return (
            "The proactive lifecycle dispatch authorizes an immediate send because the "
            "lifecycle queue is dispatch-ready and the rendered follow-up content exists."
        )
    if decision == "close_loop_lifecycle_dispatch":
        return (
            "The proactive lifecycle dispatch authorizes a final low-pressure close-loop "
            "send because the lifecycle queue is winding down but still dispatchable."
        )
    if decision == "reschedule_lifecycle_dispatch":
        return (
            "The proactive lifecycle dispatch keeps the line scheduled so the proactive "
            "touch inherits more user space before it can be sent."
        )
    if decision == "retire_lifecycle_dispatch":
        return (
            "The proactive lifecycle dispatch retires the line because the lifecycle "
            "queue is already terminal and should not emit any further contact."
        )
    if "empty_followup_units" in dispatch_notes:
        return (
            "The proactive lifecycle dispatch holds the line because the current "
            "follow-up render did not produce any sendable content."
        )
    return (
        "The proactive lifecycle dispatch keeps the line on hold because the current "
        "lifecycle posture should not force contact yet."
    )


def build_proactive_lifecycle_state_decision(
    *,
    stage_machine_decision: ProactiveStageMachineDecision,
    line_machine_decision: ProactiveLineMachineDecision,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
) -> ProactiveLifecycleStateDecision:
    current_stage_label = (
        line_machine_decision.current_stage_label or stage_machine_decision.stage_label or "unknown"
    )
    current_stage_index = max(
        1,
        int(line_machine_decision.current_stage_index or stage_machine_decision.stage_index or 1),
    )
    stage_count = max(
        current_stage_index,
        int(line_machine_decision.stage_count or stage_machine_decision.stage_count or 1),
    )
    stage_machine_key = stage_machine_decision.machine_key or f"{current_stage_label}_stage"
    stage_machine_mode = stage_machine_decision.machine_mode or "held"
    line_machine_key = line_machine_decision.machine_key or f"{current_stage_label}_line"
    line_machine_mode = line_machine_decision.machine_mode or "active_line"
    line_state = line_machine_decision.line_state or stage_machine_decision.line_state

    active_sources = _compact(
        [
            str(source)
            for source in (
                stage_machine_decision.primary_source,
                line_machine_decision.primary_source,
                orchestration_controller_decision.primary_source
                if orchestration_controller_decision is not None
                else None,
            )
            if source not in {None, ""}
        ],
        limit=4,
    )
    primary_source = (
        "orchestration_controller"
        if orchestration_controller_decision is not None
        and orchestration_controller_decision.status == "active"
        and orchestration_controller_decision.changed
        and orchestration_controller_decision.primary_source not in {None, "", "cadence"}
        else line_machine_decision.primary_source
        or stage_machine_decision.primary_source
        or "cadence"
    )
    controller_decision = (
        orchestration_controller_decision.decision
        if orchestration_controller_decision is not None
        and orchestration_controller_decision.decision
        not in {"dispatch", "follow_local_controllers", "follow_remaining_line"}
        else line_machine_decision.controller_decision or stage_machine_decision.controller_decision
    )
    shape = _resolve_lifecycle_state_shape(
        line_machine_decision=line_machine_decision,
        stage_machine_decision=stage_machine_decision,
    )
    state_notes: list[str] = [
        f"stage:{stage_machine_mode}",
        f"line:{line_machine_mode}",
    ]
    if shape.note:
        state_notes.append(shape.note)

    if controller_decision:
        state_notes.append(f"controller:{controller_decision}")
    if line_machine_decision.next_line_state not in {None, "", line_state}:
        state_notes.append(f"next_line:{line_machine_decision.next_line_state}")
    if line_machine_decision.next_stage_label:
        state_notes.append(f"next_stage:{line_machine_decision.next_stage_label}")

    selected_strategy_key = (
        line_machine_decision.selected_strategy_key
        or stage_machine_decision.selected_strategy_key
        or "none"
    )
    state_key = f"{current_stage_label}_{shape.state_mode}_{selected_strategy_key}"
    changed = bool(
        stage_machine_decision.changed
        or line_machine_decision.changed
        or shape.state_mode not in {"lifecycle_active", "lifecycle_dormant"}
        or shape.actionability != "advance"
    )

    return ProactiveLifecycleStateDecision(
        status=shape.status,
        state_key=state_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        stage_machine_key=stage_machine_key,
        stage_machine_mode=stage_machine_mode,
        line_machine_key=line_machine_key,
        line_machine_mode=line_machine_mode,
        line_state=line_state,
        state_mode=shape.state_mode,
        lifecycle_mode=shape.lifecycle_mode,
        actionability=shape.actionability,
        changed=changed,
        next_stage_label=line_machine_decision.next_stage_label,
        next_stage_index=line_machine_decision.next_stage_index,
        next_line_state=line_machine_decision.next_line_state,
        next_line_lifecycle_mode=line_machine_decision.next_lifecycle_mode,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=(
            line_machine_decision.selected_pressure_mode
            or stage_machine_decision.selected_pressure_mode
        ),
        selected_autonomy_signal=(
            line_machine_decision.selected_autonomy_signal
            or stage_machine_decision.selected_autonomy_signal
        ),
        selected_delivery_mode=(
            line_machine_decision.selected_delivery_mode
            or stage_machine_decision.selected_delivery_mode
        ),
        primary_source=primary_source,
        controller_decision=controller_decision,
        active_sources=active_sources,
        state_notes=_compact(state_notes, limit=6),
        rationale=_resolve_lifecycle_state_rationale(shape.lifecycle_mode),
    )


def build_proactive_lifecycle_transition_decision(
    *,
    lifecycle_state_decision: ProactiveLifecycleStateDecision,
) -> ProactiveLifecycleTransitionDecision:
    current_stage_label = lifecycle_state_decision.current_stage_label or "unknown"
    current_stage_index = max(1, int(lifecycle_state_decision.current_stage_index or 1))
    stage_count = max(
        current_stage_index,
        int(lifecycle_state_decision.stage_count or current_stage_index),
    )
    current_state_key = lifecycle_state_decision.state_key or f"{current_stage_label}_lifecycle"
    state_mode = lifecycle_state_decision.state_mode or "lifecycle_active"
    lifecycle_mode = lifecycle_state_decision.lifecycle_mode or "active"
    actionability = lifecycle_state_decision.actionability or "advance"

    transition_mode = "advance_lifecycle"
    status = lifecycle_state_decision.status or "active"
    lifecycle_exit_mode = "advance"
    if actionability == "retire" or lifecycle_mode == "terminal":
        transition_mode = "retire_lifecycle"
        status = "terminal"
        lifecycle_exit_mode = "retire"
    elif actionability == "close_loop" or lifecycle_mode == "winding_down":
        transition_mode = "close_loop_lifecycle"
        status = "active"
        lifecycle_exit_mode = "close_loop"
    elif actionability == "buffer" or lifecycle_mode == "buffered":
        transition_mode = "buffer_lifecycle"
        status = "scheduled"
        lifecycle_exit_mode = "buffer"
    elif actionability == "soften" or lifecycle_mode == "active_softened":
        transition_mode = "soften_lifecycle"
        status = "active"
        lifecycle_exit_mode = "soften"
    elif actionability == "hold" or lifecycle_mode == "dormant":
        transition_mode = "hold_lifecycle"
        status = "hold"
        lifecycle_exit_mode = "hold"
    elif actionability == "dispatch":
        transition_mode = "dispatch_lifecycle"
        status = "active"
        lifecycle_exit_mode = "dispatch"

    transition_key = (
        f"{current_stage_label}_{transition_mode}_"
        f"{lifecycle_state_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_state_decision.changed
        or transition_mode not in {"advance_lifecycle", "hold_lifecycle"}
        or lifecycle_exit_mode != "advance"
    )
    transition_notes: list[str] = [
        f"state:{state_mode}",
        f"lifecycle:{lifecycle_mode}",
        f"source:{lifecycle_state_decision.primary_source or 'cadence'}",
    ]
    if lifecycle_state_decision.controller_decision:
        transition_notes.append(f"controller:{lifecycle_state_decision.controller_decision}")
    if lifecycle_state_decision.next_line_state:
        transition_notes.append(f"next_line:{lifecycle_state_decision.next_line_state}")
    if lifecycle_state_decision.next_stage_label:
        transition_notes.append(f"next_stage:{lifecycle_state_decision.next_stage_label}")

    rationale = (
        "The proactive lifecycle transition keeps the overall line posture moving "
        "through the expected active path."
    )
    if transition_mode == "retire_lifecycle":
        rationale = (
            "The proactive lifecycle should retire because the line has reached a terminal posture."
        )
    elif transition_mode == "close_loop_lifecycle":
        rationale = (
            "The proactive lifecycle should stay in a close-loop posture because the "
            "line is already winding down."
        )
    elif transition_mode in {"buffer_lifecycle", "soften_lifecycle"}:
        rationale = (
            "The proactive lifecycle should keep extra user space before any further "
            "dispatch because the line is still softened."
        )
    elif transition_mode == "dispatch_lifecycle":
        rationale = (
            "The proactive lifecycle can dispatch now because both the stage and line "
            "machines remain in an active sending posture."
        )

    return ProactiveLifecycleTransitionDecision(
        status=status,
        transition_key=transition_key,
        current_state_key=current_state_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        state_mode=state_mode,
        lifecycle_mode=lifecycle_mode,
        transition_mode=transition_mode,
        changed=changed,
        next_stage_label=lifecycle_state_decision.next_stage_label,
        next_stage_index=lifecycle_state_decision.next_stage_index,
        next_line_state=lifecycle_state_decision.next_line_state,
        next_line_lifecycle_mode=lifecycle_state_decision.next_line_lifecycle_mode,
        lifecycle_exit_mode=lifecycle_exit_mode,
        selected_strategy_key=lifecycle_state_decision.selected_strategy_key,
        selected_pressure_mode=lifecycle_state_decision.selected_pressure_mode,
        selected_autonomy_signal=lifecycle_state_decision.selected_autonomy_signal,
        selected_delivery_mode=lifecycle_state_decision.selected_delivery_mode,
        primary_source=lifecycle_state_decision.primary_source,
        controller_decision=lifecycle_state_decision.controller_decision,
        active_sources=list(lifecycle_state_decision.active_sources),
        transition_notes=_compact(transition_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_lifecycle_machine_decision(
    *,
    lifecycle_state_decision: ProactiveLifecycleStateDecision,
    lifecycle_transition_decision: ProactiveLifecycleTransitionDecision,
) -> ProactiveLifecycleMachineDecision:
    current_stage_label = lifecycle_state_decision.current_stage_label or "unknown"
    current_stage_index = max(1, int(lifecycle_state_decision.current_stage_index or 1))
    stage_count = max(
        current_stage_index,
        int(lifecycle_state_decision.stage_count or current_stage_index),
    )
    current_state_key = lifecycle_state_decision.state_key or f"{current_stage_label}_lifecycle"
    state_mode = lifecycle_state_decision.state_mode or "lifecycle_active"
    transition_key = (
        lifecycle_transition_decision.transition_key or f"{current_stage_label}_advance_lifecycle"
    )
    transition_mode = lifecycle_transition_decision.transition_mode or "advance_lifecycle"
    lifecycle_mode = (
        lifecycle_transition_decision.lifecycle_mode
        or lifecycle_state_decision.lifecycle_mode
        or "active"
    )
    status = lifecycle_transition_decision.status or lifecycle_state_decision.status or "active"
    machine_mode = "active_lifecycle"
    machine_lifecycle_mode = lifecycle_mode
    machine_actionability = "advance"
    machine_notes: list[str] = [
        f"state:{state_mode}",
        f"transition:{transition_mode}",
    ]

    if transition_mode == "retire_lifecycle" or lifecycle_mode == "terminal":
        status = "terminal"
        machine_mode = "terminal_lifecycle"
        machine_lifecycle_mode = "terminal"
        machine_actionability = "retire"
        machine_notes.append("retire_lifecycle")
    elif transition_mode == "close_loop_lifecycle" or lifecycle_mode == "winding_down":
        machine_mode = "winding_down_lifecycle"
        machine_lifecycle_mode = "winding_down"
        machine_actionability = "close_loop"
        machine_notes.append("close_loop_lifecycle")
    elif transition_mode == "buffer_lifecycle" or lifecycle_mode == "buffered":
        status = "scheduled"
        machine_mode = "buffered_lifecycle"
        machine_lifecycle_mode = "buffered"
        machine_actionability = "buffer"
        machine_notes.append("buffer_lifecycle")
    elif transition_mode == "soften_lifecycle" or lifecycle_mode == "active_softened":
        machine_mode = "softened_lifecycle"
        machine_lifecycle_mode = "active_softened"
        machine_actionability = "soften"
        machine_notes.append("soften_lifecycle")
    elif transition_mode == "hold_lifecycle" or lifecycle_mode == "dormant":
        status = "hold"
        machine_mode = "dormant_lifecycle"
        machine_lifecycle_mode = "dormant"
        machine_actionability = "hold"
        machine_notes.append("hold_lifecycle")
    elif transition_mode == "dispatch_lifecycle":
        machine_mode = "dispatching_lifecycle"
        machine_lifecycle_mode = "active"
        machine_actionability = "dispatch"
        machine_notes.append("dispatch_lifecycle")

    if lifecycle_transition_decision.controller_decision:
        machine_notes.append(f"controller:{lifecycle_transition_decision.controller_decision}")
    if lifecycle_transition_decision.next_line_state not in {
        None,
        "",
        lifecycle_state_decision.line_state,
    }:
        machine_notes.append(f"next_line:{lifecycle_transition_decision.next_line_state}")
    if lifecycle_transition_decision.next_stage_label:
        machine_notes.append(f"next_stage:{lifecycle_transition_decision.next_stage_label}")

    machine_key = f"{current_stage_label}_{machine_mode}"
    changed = bool(
        lifecycle_state_decision.changed
        or lifecycle_transition_decision.changed
        or machine_mode not in {"active_lifecycle", "dormant_lifecycle"}
        or machine_actionability != "advance"
    )
    rationale = (
        "The proactive lifecycle machine now turns the lifecycle state and "
        "transition into one observable machine posture."
    )
    if machine_lifecycle_mode == "terminal":
        rationale = (
            "The proactive lifecycle has reached a terminal posture, so the line "
            "should retire instead of leaving residual follow-up motion alive."
        )
    elif machine_lifecycle_mode == "winding_down":
        rationale = (
            "The proactive lifecycle is already winding down, so remaining movement "
            "should stay close-loop and low-pressure."
        )
    elif machine_lifecycle_mode in {"buffered", "active_softened"}:
        rationale = (
            "The proactive lifecycle remains softened, so the whole line should keep "
            "extra user space before any further dispatch."
        )

    return ProactiveLifecycleMachineDecision(
        status=status,
        machine_key=machine_key,
        current_state_key=current_state_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        transition_key=transition_key,
        transition_mode=transition_mode,
        stage_machine_key=lifecycle_state_decision.stage_machine_key,
        stage_machine_mode=lifecycle_state_decision.stage_machine_mode,
        line_machine_key=lifecycle_state_decision.line_machine_key,
        line_machine_mode=lifecycle_state_decision.line_machine_mode,
        line_state=lifecycle_state_decision.line_state,
        state_mode=state_mode,
        lifecycle_mode=machine_lifecycle_mode,
        machine_mode=machine_mode,
        actionability=machine_actionability,
        changed=changed,
        next_stage_label=lifecycle_transition_decision.next_stage_label,
        next_stage_index=lifecycle_transition_decision.next_stage_index,
        next_line_state=lifecycle_transition_decision.next_line_state,
        next_line_lifecycle_mode=lifecycle_transition_decision.next_line_lifecycle_mode,
        selected_strategy_key=lifecycle_transition_decision.selected_strategy_key,
        selected_pressure_mode=lifecycle_transition_decision.selected_pressure_mode,
        selected_autonomy_signal=lifecycle_transition_decision.selected_autonomy_signal,
        selected_delivery_mode=lifecycle_transition_decision.selected_delivery_mode,
        primary_source=lifecycle_transition_decision.primary_source,
        controller_decision=lifecycle_transition_decision.controller_decision,
        active_sources=list(lifecycle_transition_decision.active_sources),
        machine_notes=_compact(machine_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_lifecycle_controller_decision(
    *,
    lifecycle_machine_decision: ProactiveLifecycleMachineDecision,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
) -> ProactiveLifecycleControllerDecision:
    current_stage_label = lifecycle_machine_decision.current_stage_label or "unknown"
    lifecycle_mode = lifecycle_machine_decision.lifecycle_mode or "active"
    lifecycle_state = lifecycle_mode
    decision = "continue_lifecycle"
    status = lifecycle_machine_decision.status or "active"
    changed = False
    additional_delay_seconds = 0
    primary_source = lifecycle_machine_decision.primary_source or "cadence"
    controller_decision = lifecycle_machine_decision.controller_decision
    active_sources = list(lifecycle_machine_decision.active_sources)
    controller_notes: list[str] = list(lifecycle_machine_decision.machine_notes)

    if (
        orchestration_controller_decision is not None
        and orchestration_controller_decision.status == "active"
        and orchestration_controller_decision.changed
    ):
        additional_delay_seconds = max(
            additional_delay_seconds,
            orchestration_controller_decision.line_additional_delay_seconds,
        )
        if primary_source == "cadence":
            primary_source = "orchestration_controller"
        if controller_decision in {None, "", "dispatch", "follow_local_controllers"}:
            controller_decision = orchestration_controller_decision.decision
        active_sources.append("orchestration_controller")
        controller_notes.extend(list(orchestration_controller_decision.controller_notes))

    if (
        aggregate_controller_decision is not None
        and aggregate_controller_decision.status == "active"
        and aggregate_controller_decision.changed
    ):
        additional_delay_seconds = max(
            additional_delay_seconds,
            aggregate_controller_decision.line_additional_delay_seconds,
        )
        if primary_source == "cadence":
            primary_source = "aggregate_controller"
        if controller_decision in {None, "", "dispatch", "follow_local_controllers"}:
            controller_decision = aggregate_controller_decision.decision
        active_sources.append("aggregate_controller")
        controller_notes.extend(list(aggregate_controller_decision.controller_notes))

    if lifecycle_machine_decision.actionability == "retire" or lifecycle_mode == "terminal":
        status = "terminal"
        lifecycle_state = "terminal"
        decision = "retire_lifecycle"
        changed = True
    elif (
        lifecycle_machine_decision.actionability == "close_loop" or lifecycle_mode == "winding_down"
    ):
        status = "active"
        lifecycle_state = "winding_down"
        decision = "close_loop_lifecycle"
        changed = True
    elif lifecycle_machine_decision.actionability == "buffer" or lifecycle_mode == "buffered":
        status = "scheduled"
        lifecycle_state = "buffered"
        decision = "buffer_lifecycle"
        changed = True
    elif (
        lifecycle_machine_decision.actionability == "soften" or lifecycle_mode == "active_softened"
    ):
        status = "active"
        lifecycle_state = "softened"
        decision = "soften_lifecycle"
        changed = True
    elif lifecycle_machine_decision.actionability == "hold" or lifecycle_mode == "dormant":
        status = "hold"
        lifecycle_state = "dormant"
        decision = "hold_lifecycle"
        changed = bool(lifecycle_machine_decision.changed)
    elif lifecycle_machine_decision.actionability == "dispatch":
        status = "active"
        lifecycle_state = "dispatching"
        decision = "dispatch_lifecycle"
        changed = True

    if additional_delay_seconds > 0:
        changed = True
        controller_notes.append(f"delay:{additional_delay_seconds}")
    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        controller_notes.append(f"controller:{controller_decision}")

    controller_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_machine_decision.selected_strategy_key or 'none'}"
    )
    if not changed and decision == "continue_lifecycle":
        controller_key = f"{current_stage_label}_continue_lifecycle"

    rationale = (
        "The proactive lifecycle controller keeps the lifecycle machine on its current "
        "path because the higher-order controller stack did not need to reshape the line."
    )
    if decision == "retire_lifecycle":
        rationale = (
            "The proactive lifecycle should retire the line because the lifecycle machine "
            "has already reached a terminal posture."
        )
    elif decision == "close_loop_lifecycle":
        rationale = (
            "The proactive lifecycle should stay in a close-loop posture so the remaining "
            "line winds down instead of reopening momentum."
        )
    elif decision in {"buffer_lifecycle", "soften_lifecycle"}:
        rationale = (
            "The proactive lifecycle should keep a softened buffered posture so later "
            "touches inherit lower pressure and more user space."
        )
    elif decision == "dispatch_lifecycle":
        rationale = (
            "The proactive lifecycle can still dispatch, but it is doing so as an "
            "explicit lifecycle-level action instead of a passive default."
        )

    return ProactiveLifecycleControllerDecision(
        status=status,
        controller_key=controller_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        decision=decision,
        changed=changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=lifecycle_machine_decision.selected_strategy_key,
        selected_pressure_mode=lifecycle_machine_decision.selected_pressure_mode,
        selected_autonomy_signal=lifecycle_machine_decision.selected_autonomy_signal,
        selected_delivery_mode=lifecycle_machine_decision.selected_delivery_mode,
        primary_source=primary_source,
        controller_decision=controller_decision,
        active_sources=_compact(active_sources, limit=6),
        controller_notes=_compact(controller_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_lifecycle_envelope_decision(
    *,
    lifecycle_machine_decision: ProactiveLifecycleMachineDecision,
    lifecycle_controller_decision: ProactiveLifecycleControllerDecision,
    dispatch_envelope_decision: ProactiveDispatchEnvelopeDecision | None = None,
) -> ProactiveLifecycleEnvelopeDecision:
    current_stage_label = (
        lifecycle_controller_decision.current_stage_label
        or lifecycle_machine_decision.current_stage_label
        or "unknown"
    )
    changed = bool(lifecycle_controller_decision.changed)
    additional_delay_seconds = max(
        0,
        int(lifecycle_controller_decision.additional_delay_seconds or 0),
    )
    selected_strategy_key = (
        lifecycle_controller_decision.selected_strategy_key
        or lifecycle_machine_decision.selected_strategy_key
        or "none"
    )
    selected_pressure_mode = (
        lifecycle_controller_decision.selected_pressure_mode
        or lifecycle_machine_decision.selected_pressure_mode
        or "none"
    )
    selected_autonomy_signal = (
        lifecycle_controller_decision.selected_autonomy_signal
        or lifecycle_machine_decision.selected_autonomy_signal
        or "none"
    )
    selected_delivery_mode = (
        lifecycle_controller_decision.selected_delivery_mode
        or lifecycle_machine_decision.selected_delivery_mode
        or "none"
    )
    primary_source = (
        lifecycle_controller_decision.primary_source
        or lifecycle_machine_decision.primary_source
        or "cadence"
    )
    controller_decision = (
        lifecycle_controller_decision.controller_decision
        or lifecycle_machine_decision.controller_decision
    )
    active_sources = list(lifecycle_machine_decision.active_sources) + list(
        lifecycle_controller_decision.active_sources
    )
    envelope_notes: list[str] = list(lifecycle_machine_decision.machine_notes) + list(
        lifecycle_controller_decision.controller_notes
    )

    if dispatch_envelope_decision is not None:
        selected_strategy_key = (
            dispatch_envelope_decision.selected_strategy_key or selected_strategy_key
        )
        selected_pressure_mode = (
            dispatch_envelope_decision.selected_pressure_mode or selected_pressure_mode
        )
        selected_autonomy_signal = (
            dispatch_envelope_decision.selected_autonomy_signal or selected_autonomy_signal
        )
        selected_delivery_mode = (
            dispatch_envelope_decision.selected_reengagement_delivery_mode
            or dispatch_envelope_decision.selected_stage_delivery_mode
            or selected_delivery_mode
        )
        changed = bool(changed or dispatch_envelope_decision.changed)
        if dispatch_envelope_decision.active_sources:
            active_sources.extend(list(dispatch_envelope_decision.active_sources))
        if dispatch_envelope_decision.envelope_notes:
            envelope_notes.extend(list(dispatch_envelope_decision.envelope_notes))
        if primary_source in {"cadence", "lifecycle_controller"}:
            primary_source = "dispatch_envelope"
        envelope_notes.append(f"dispatch:{dispatch_envelope_decision.decision}")

    if additional_delay_seconds > 0:
        changed = True
    shape = _resolve_lifecycle_envelope_shape(
        lifecycle_controller_decision=lifecycle_controller_decision,
        lifecycle_machine_decision=lifecycle_machine_decision,
        changed=changed,
    )

    if additional_delay_seconds > 0:
        envelope_notes.append(f"delay:{additional_delay_seconds}")
    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        envelope_notes.append(f"controller:{controller_decision}")

    envelope_key = (
        f"{current_stage_label}_{shape.decision}_{selected_strategy_key or 'none'}"
    )
    if not shape.changed and shape.decision == "continue_lifecycle_shape":
        envelope_key = f"{current_stage_label}_continue_lifecycle_shape"

    return ProactiveLifecycleEnvelopeDecision(
        status=shape.status,
        envelope_key=envelope_key,
        current_stage_label=current_stage_label,
        lifecycle_state=shape.lifecycle_state,
        envelope_mode=shape.envelope_mode,
        decision=shape.decision,
        actionability=shape.actionability,
        changed=shape.changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_source=primary_source,
        controller_decision=controller_decision,
        active_sources=_compact(active_sources, limit=8),
        envelope_notes=_compact(envelope_notes, limit=8),
        rationale=_resolve_lifecycle_envelope_rationale(shape.actionability),
    )


def build_proactive_lifecycle_scheduler_decision(
    *,
    lifecycle_envelope_decision: ProactiveLifecycleEnvelopeDecision,
    proactive_scheduling_plan: ProactiveSchedulingPlan | None = None,
    dispatch_gate_decision: ProactiveDispatchGateDecision | None = None,
) -> ProactiveLifecycleSchedulerDecision:
    current_stage_label = lifecycle_envelope_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_envelope_decision.lifecycle_state or "active"
    lifecycle_envelope_mode = lifecycle_envelope_decision.envelope_mode or "active_lifecycle_shape"
    status = lifecycle_envelope_decision.status or "active"
    scheduler_mode = "active_lifecycle_schedule"
    decision = "continue_lifecycle_schedule"
    queue_status_hint = "ready"
    actionability = lifecycle_envelope_decision.actionability or "continue"
    changed = bool(lifecycle_envelope_decision.changed)
    additional_delay_seconds = max(
        0,
        int(lifecycle_envelope_decision.additional_delay_seconds or 0),
    )
    selected_strategy_key = lifecycle_envelope_decision.selected_strategy_key or "none"
    selected_pressure_mode = lifecycle_envelope_decision.selected_pressure_mode or "none"
    selected_autonomy_signal = lifecycle_envelope_decision.selected_autonomy_signal or "none"
    selected_delivery_mode = lifecycle_envelope_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_envelope_decision.primary_source or "cadence"
    controller_decision = lifecycle_envelope_decision.controller_decision
    active_sources = list(lifecycle_envelope_decision.active_sources)
    scheduler_notes: list[str] = list(lifecycle_envelope_decision.envelope_notes)
    scheduler_state = _build_lifecycle_scheduler_state(
        lifecycle_state=lifecycle_state,
        actionability=actionability,
        changed=changed,
        status=status,
    )
    status = str(scheduler_state["status"])
    scheduler_mode = str(scheduler_state["scheduler_mode"])
    decision = str(scheduler_state["decision"])
    queue_status_hint = str(scheduler_state["queue_status_hint"])
    actionability = str(scheduler_state["actionability"])
    changed = bool(scheduler_state["changed"])
    scheduling_status = "inactive"
    scheduling_mode = "none"
    scheduling_extra_delay = 0
    if isinstance(proactive_scheduling_plan, ProactiveSchedulingPlan):
        scheduling_status = proactive_scheduling_plan.status
        scheduling_mode = proactive_scheduling_plan.scheduler_mode
        scheduling_extra_delay = int(proactive_scheduling_plan.first_touch_extra_delay_seconds or 0)
    elif proactive_scheduling_plan is not None:
        scheduling_payload = dict(proactive_scheduling_plan or {})
        scheduling_status = str(scheduling_payload.get("status") or "inactive")
        scheduling_mode = str(scheduling_payload.get("scheduler_mode") or "none")
        scheduling_extra_delay = int(scheduling_payload.get("first_touch_extra_delay_seconds") or 0)

    primary_source = _apply_lifecycle_scheduler_scheduling_plan(
        scheduler_state=scheduler_state,
        proactive_scheduling_plan=proactive_scheduling_plan,
        scheduling_status=scheduling_status,
        scheduling_mode=scheduling_mode,
        scheduling_extra_delay=scheduling_extra_delay,
        additional_delay_seconds=additional_delay_seconds,
        active_sources=active_sources,
        scheduler_notes=scheduler_notes,
        primary_source=primary_source,
    )
    primary_source = _apply_lifecycle_scheduler_dispatch_gate(
        scheduler_state=scheduler_state,
        dispatch_gate_decision=dispatch_gate_decision,
        active_sources=active_sources,
        scheduler_notes=scheduler_notes,
        primary_source=primary_source,
    )
    status = str(scheduler_state["status"])
    scheduler_mode = str(scheduler_state["scheduler_mode"])
    decision = str(scheduler_state["decision"])
    queue_status_hint = str(scheduler_state["queue_status_hint"])
    actionability = str(scheduler_state["actionability"])
    changed = bool(scheduler_state["changed"])
    additional_delay_seconds = int(scheduler_state["additional_delay_seconds"])

    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        scheduler_notes.append(f"controller:{controller_decision}")

    scheduler_key = f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"
    if not changed and decision == "continue_lifecycle_schedule":
        scheduler_key = f"{current_stage_label}_continue_lifecycle_schedule"

    rationale = _build_lifecycle_scheduler_rationale(decision=decision)

    return ProactiveLifecycleSchedulerDecision(
        status=status,
        scheduler_key=scheduler_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        lifecycle_envelope_mode=lifecycle_envelope_mode,
        scheduler_mode=scheduler_mode,
        decision=decision,
        queue_status_hint=queue_status_hint,
        actionability=actionability,
        changed=changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_source=primary_source,
        controller_decision=controller_decision,
        active_sources=_compact(active_sources, limit=8),
        scheduler_notes=_compact(scheduler_notes, limit=8),
        rationale=rationale,
    )


def _build_lifecycle_scheduler_state(
    *,
    lifecycle_state: str,
    actionability: str,
    changed: bool,
    status: str,
) -> dict[str, object]:
    scheduler_state: dict[str, object] = {
        "status": status,
        "scheduler_mode": "active_lifecycle_schedule",
        "decision": "continue_lifecycle_schedule",
        "queue_status_hint": "ready",
        "actionability": actionability,
        "changed": changed,
        "additional_delay_seconds": 0,
    }
    if actionability == "retire" or lifecycle_state == "terminal":
        scheduler_state.update(
            status="terminal",
            decision="retire_lifecycle_schedule",
            scheduler_mode="terminal_lifecycle_schedule",
            queue_status_hint="terminal",
            changed=True,
        )
    elif actionability == "close_loop" or lifecycle_state == "winding_down":
        scheduler_state.update(
            status="active",
            decision="close_loop_lifecycle_schedule",
            scheduler_mode="winding_down_lifecycle_schedule",
            queue_status_hint="due",
            changed=True,
        )
    elif actionability in {"buffer", "soften"} or lifecycle_state in {
        "buffered",
        "softened",
    }:
        scheduler_state.update(
            status="scheduled",
            decision="buffer_lifecycle_schedule",
            scheduler_mode="buffered_lifecycle_schedule",
            queue_status_hint="scheduled",
            actionability="buffer",
            changed=True,
        )
    elif actionability == "hold" or lifecycle_state == "dormant":
        scheduler_state.update(
            status="hold",
            decision="hold_lifecycle_schedule",
            scheduler_mode="dormant_lifecycle_schedule",
            queue_status_hint="hold",
            changed=True,
        )
    elif actionability == "dispatch" or lifecycle_state == "dispatching":
        scheduler_state.update(
            status="active",
            decision="dispatch_lifecycle_schedule",
            scheduler_mode="dispatching_lifecycle_schedule",
            queue_status_hint="due",
            changed=True,
        )
    return scheduler_state


def _apply_lifecycle_scheduler_scheduling_plan(
    *,
    scheduler_state: dict[str, object],
    proactive_scheduling_plan: ProactiveSchedulingPlan | None,
    scheduling_status: str,
    scheduling_mode: str,
    scheduling_extra_delay: int,
    additional_delay_seconds: int,
    active_sources: list[str],
    scheduler_notes: list[str],
    primary_source: str,
) -> str:
    scheduler_state["additional_delay_seconds"] = additional_delay_seconds
    if proactive_scheduling_plan is None or scheduling_status != "active":
        return primary_source
    if scheduling_extra_delay > 0:
        scheduler_state["additional_delay_seconds"] = max(
            int(scheduler_state["additional_delay_seconds"]),
            scheduling_extra_delay,
        )
        scheduler_state["changed"] = True
        scheduler_notes.append(f"scheduling_delay:{scheduling_extra_delay}")
        if primary_source in {"cadence", "lifecycle_envelope"}:
            primary_source = "scheduling_plan"
    active_sources.append("scheduling_plan")
    scheduler_notes.append(f"scheduler:{scheduling_mode}")
    return primary_source


def _apply_lifecycle_scheduler_dispatch_gate(
    *,
    scheduler_state: dict[str, object],
    dispatch_gate_decision: ProactiveDispatchGateDecision | None,
    active_sources: list[str],
    scheduler_notes: list[str],
    primary_source: str,
) -> str:
    if dispatch_gate_decision is None:
        return primary_source
    active_sources.append("dispatch_gate")
    if dispatch_gate_decision.decision == "defer":
        retry_after_seconds = int(dispatch_gate_decision.retry_after_seconds or 0)
        scheduler_state.update(
            status="scheduled",
            decision="defer_lifecycle_schedule",
            scheduler_mode="deferred_lifecycle_schedule",
            queue_status_hint="scheduled",
            actionability="buffer",
            additional_delay_seconds=max(
                int(scheduler_state["additional_delay_seconds"]),
                retry_after_seconds,
            ),
            changed=True,
        )
        scheduler_notes.append(f"gate_defer:{retry_after_seconds}")
        return "dispatch_gate"
    if dispatch_gate_decision.decision == "hold":
        scheduler_state.update(
            status="hold",
            decision="hold_lifecycle_schedule",
            scheduler_mode="hold_lifecycle_schedule",
            queue_status_hint="hold",
            actionability="hold",
            changed=True,
        )
        scheduler_notes.append("gate_hold")
        return "dispatch_gate"
    return primary_source


def _build_lifecycle_scheduler_rationale(*, decision: str) -> str:
    rationale = (
        "The proactive lifecycle scheduler keeps the lifecycle envelope on its current "
        "execution path because no higher-order scheduling force needs to reshape timing."
    )
    if decision == "retire_lifecycle_schedule":
        return (
            "The proactive lifecycle scheduler retires the line because the lifecycle "
            "stack has already reached a terminal execution posture."
        )
    if decision == "close_loop_lifecycle_schedule":
        return (
            "The proactive lifecycle scheduler keeps the line on a winding-down path so "
            "the final touch stays close-loop and low-pressure."
        )
    if decision in {"buffer_lifecycle_schedule", "defer_lifecycle_schedule"}:
        return (
            "The proactive lifecycle scheduler buffers the line so later touches inherit "
            "more user space and a softer dispatch window."
        )
    if decision == "dispatch_lifecycle_schedule":
        return (
            "The proactive lifecycle scheduler keeps the line dispatchable, but now as "
            "an explicit lifecycle-level scheduling posture."
        )
    return rationale


def build_proactive_lifecycle_window_decision(
    *,
    lifecycle_scheduler_decision: ProactiveLifecycleSchedulerDecision,
    current_queue_status: str = "due",
    schedule_reason: str = "",
    progression_action: str = "none",
    progression_advanced: bool = False,
) -> ProactiveLifecycleWindowDecision:
    current_stage_label = lifecycle_scheduler_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_scheduler_decision.lifecycle_state or "active"
    scheduler_mode = lifecycle_scheduler_decision.scheduler_mode or "active_lifecycle_schedule"
    status = lifecycle_scheduler_decision.status or "active"
    decision = "continue_lifecycle_window"
    window_mode = "active_lifecycle_window"
    queue_status = str(
        current_queue_status or lifecycle_scheduler_decision.queue_status_hint or "ready"
    )
    actionability = lifecycle_scheduler_decision.actionability or "continue"
    changed = bool(lifecycle_scheduler_decision.changed)
    additional_delay_seconds = max(
        0,
        int(lifecycle_scheduler_decision.additional_delay_seconds or 0),
    )
    selected_strategy_key = lifecycle_scheduler_decision.selected_strategy_key or "none"
    selected_pressure_mode = lifecycle_scheduler_decision.selected_pressure_mode or "none"
    selected_autonomy_signal = lifecycle_scheduler_decision.selected_autonomy_signal or "none"
    selected_delivery_mode = lifecycle_scheduler_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_scheduler_decision.primary_source or "cadence"
    controller_decision = lifecycle_scheduler_decision.controller_decision
    active_sources = list(lifecycle_scheduler_decision.active_sources)
    window_notes: list[str] = list(lifecycle_scheduler_decision.scheduler_notes)
    schedule_reason_value = str(schedule_reason or "")
    window_state = _build_lifecycle_window_state(
        lifecycle_scheduler_decision=lifecycle_scheduler_decision,
        lifecycle_state=lifecycle_state,
        queue_status=queue_status,
        actionability=actionability,
        status=status,
        changed=changed,
        current_stage_label=current_stage_label,
        progression_advanced=progression_advanced,
    )
    status = str(window_state["status"])
    decision = str(window_state["decision"])
    window_mode = str(window_state["window_mode"])
    queue_status = str(window_state["queue_status"])
    actionability = str(window_state["actionability"])
    changed = bool(window_state["changed"])
    if progression_advanced:
        changed = True
        window_notes.append("progression_advanced")
        if primary_source in {"cadence", "lifecycle_scheduler"}:
            primary_source = "progression"
    if progression_action not in {"", "none"}:
        window_notes.append(f"progression:{progression_action}")
    if schedule_reason_value:
        window_notes.append(f"schedule_reason:{schedule_reason_value}")
        if primary_source in {"cadence", "lifecycle_scheduler"} and queue_status in {
            "scheduled",
            "hold",
        }:
            primary_source = "queue"
    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        window_notes.append(f"controller:{controller_decision}")

    window_key = f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"
    if not changed and decision == "continue_lifecycle_window":
        window_key = f"{current_stage_label}_continue_lifecycle_window"
    rationale = _build_lifecycle_window_rationale(decision=decision)

    return ProactiveLifecycleWindowDecision(
        status=status,
        window_key=window_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        scheduler_mode=scheduler_mode,
        window_mode=window_mode,
        decision=decision,
        queue_status=queue_status,
        schedule_reason=schedule_reason_value,
        actionability=actionability,
        changed=changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_source=primary_source,
        controller_decision=controller_decision,
        active_sources=_compact(active_sources, limit=8),
        window_notes=_compact(window_notes, limit=8),
        rationale=rationale,
    )


def _build_lifecycle_window_state(
    *,
    lifecycle_scheduler_decision: ProactiveLifecycleSchedulerDecision,
    lifecycle_state: str,
    queue_status: str,
    actionability: str,
    status: str,
    changed: bool,
    current_stage_label: str,
    progression_advanced: bool,
) -> dict[str, object]:
    window_state: dict[str, object] = {
        "status": status,
        "decision": "continue_lifecycle_window",
        "window_mode": "active_lifecycle_window",
        "queue_status": queue_status,
        "actionability": actionability,
        "changed": changed,
    }
    if (
        lifecycle_scheduler_decision.decision == "retire_lifecycle_schedule"
        or lifecycle_state == "terminal"
    ):
        window_state.update(
            status="terminal",
            decision="retire_lifecycle_window",
            window_mode="terminal_lifecycle_window",
            queue_status="terminal",
            actionability="retire",
            changed=True,
        )
    elif (
        lifecycle_scheduler_decision.decision == "close_loop_lifecycle_schedule"
        or lifecycle_state == "winding_down"
    ):
        window_state.update(
            status="active",
            decision="close_loop_lifecycle_window",
            window_mode="close_loop_lifecycle_window",
            queue_status=queue_status if queue_status in {"due", "overdue", "scheduled"} else "due",
            actionability="close_loop",
            changed=True,
        )
    elif progression_advanced and current_stage_label == "final_soft_close":
        window_state.update(
            status="active",
            decision="close_loop_lifecycle_window",
            window_mode="close_loop_lifecycle_window",
            queue_status=queue_status if queue_status in {"due", "overdue"} else "due",
            actionability="close_loop",
            changed=True,
        )
    elif lifecycle_scheduler_decision.decision == "defer_lifecycle_schedule":
        window_state.update(
            status="scheduled",
            decision="defer_lifecycle_window",
            window_mode="deferred_lifecycle_window",
            queue_status="scheduled",
            actionability="buffer",
            changed=True,
        )
    elif (
        lifecycle_scheduler_decision.decision == "buffer_lifecycle_schedule"
        or lifecycle_state in {"buffered", "softened"}
    ):
        window_state.update(
            status="scheduled",
            decision="buffer_lifecycle_window",
            window_mode="buffered_lifecycle_window",
            queue_status="scheduled",
            actionability="buffer",
            changed=True,
        )
    elif (
        lifecycle_scheduler_decision.decision == "hold_lifecycle_schedule"
        or lifecycle_state == "dormant"
    ):
        window_state.update(
            status="hold",
            decision="hold_lifecycle_window",
            window_mode="hold_lifecycle_window",
            queue_status="hold",
            actionability="hold",
            changed=True,
        )
    elif (
        lifecycle_scheduler_decision.decision == "dispatch_lifecycle_schedule"
        or lifecycle_state == "dispatching"
    ):
        window_state.update(
            status="active",
            decision="dispatch_lifecycle_window",
            window_mode="dispatch_lifecycle_window",
            queue_status=queue_status if queue_status in {"due", "overdue"} else "due",
            actionability="dispatch",
            changed=True,
        )
    return window_state


def _build_lifecycle_window_rationale(*, decision: str) -> str:
    rationale = (
        "The proactive lifecycle window keeps the current scheduling posture because "
        "the lifecycle scheduler did not need to reshape the timing window any further."
    )
    if decision == "retire_lifecycle_window":
        return (
            "The proactive lifecycle window is terminal because the scheduler has already "
            "moved the line into a retire-ready posture."
        )
    if decision == "close_loop_lifecycle_window":
        return (
            "The proactive lifecycle window keeps the line in a close-loop window so the "
            "remaining touch stays low-pressure and winding down."
        )
    if decision in {"buffer_lifecycle_window", "defer_lifecycle_window"}:
        return (
            "The proactive lifecycle window keeps the line scheduled so later touches "
            "inherit more user space and a softer dispatch window."
        )
    if decision == "dispatch_lifecycle_window":
        return (
            "The proactive lifecycle window keeps the line dispatchable as an explicit "
            "lifecycle-level time window rather than an implicit queue default."
        )
    return rationale


def build_proactive_lifecycle_queue_decision(
    *,
    lifecycle_window_decision: ProactiveLifecycleWindowDecision,
    current_queue_status: str = "due",
) -> ProactiveLifecycleQueueDecision:
    current_stage_label = lifecycle_window_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_window_decision.lifecycle_state or "active"
    window_mode = lifecycle_window_decision.window_mode or "active_lifecycle_window"
    lifecycle_window_queue_status = str(lifecycle_window_decision.queue_status or "due")
    queue_status = str(current_queue_status or lifecycle_window_queue_status or "due")
    status = lifecycle_window_decision.status or "active"
    decision = "continue_lifecycle_queue"
    queue_mode = "active_lifecycle_queue"
    actionability = lifecycle_window_decision.actionability or "continue"
    changed = bool(lifecycle_window_decision.changed)
    additional_delay_seconds = max(
        0,
        int(lifecycle_window_decision.additional_delay_seconds or 0),
    )
    selected_strategy_key = lifecycle_window_decision.selected_strategy_key or "none"
    selected_pressure_mode = lifecycle_window_decision.selected_pressure_mode or "none"
    selected_autonomy_signal = lifecycle_window_decision.selected_autonomy_signal or "none"
    selected_delivery_mode = lifecycle_window_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_window_decision.primary_source or "cadence"
    controller_decision = lifecycle_window_decision.controller_decision
    active_sources = list(lifecycle_window_decision.active_sources)
    queue_notes: list[str] = list(lifecycle_window_decision.window_notes)

    if queue_status != lifecycle_window_queue_status:
        queue_notes.append(f"queue_override:{queue_status}")
        if primary_source in {"cadence", "lifecycle_window"}:
            primary_source = "queue"

    queue_state = _build_lifecycle_queue_state(
        lifecycle_window_decision=lifecycle_window_decision,
        lifecycle_state=lifecycle_state,
        queue_status=queue_status,
        actionability=actionability,
        status=status,
        changed=changed,
    )
    status = str(queue_state["status"])
    decision = str(queue_state["decision"])
    queue_mode = str(queue_state["queue_mode"])
    queue_status = str(queue_state["queue_status"])
    actionability = str(queue_state["actionability"])
    changed = bool(queue_state["changed"])

    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        queue_notes.append(f"controller:{controller_decision}")

    queue_key = f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"
    if not changed and decision == "continue_lifecycle_queue":
        queue_key = f"{current_stage_label}_continue_lifecycle_queue"

    rationale = _build_lifecycle_queue_rationale(decision=decision)

    return ProactiveLifecycleQueueDecision(
        status=status,
        queue_key=queue_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        window_mode=window_mode,
        queue_mode=queue_mode,
        decision=decision,
        queue_status=queue_status,
        actionability=actionability,
        changed=changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_source=primary_source,
        controller_decision=controller_decision,
        active_sources=_compact(active_sources, limit=8),
        queue_notes=_compact(queue_notes, limit=8),
        rationale=rationale,
    )


def _build_lifecycle_queue_state(
    *,
    lifecycle_window_decision: ProactiveLifecycleWindowDecision,
    lifecycle_state: str,
    queue_status: str,
    actionability: str,
    status: str,
    changed: bool,
) -> dict[str, object]:
    queue_state: dict[str, object] = {
        "status": status,
        "decision": "continue_lifecycle_queue",
        "queue_mode": "active_lifecycle_queue",
        "queue_status": queue_status,
        "actionability": actionability,
        "changed": changed,
    }
    if (
        lifecycle_window_decision.decision == "retire_lifecycle_window"
        or lifecycle_state == "terminal"
        or queue_status == "terminal"
    ):
        queue_state.update(
            status="terminal",
            decision="retire_lifecycle_queue",
            queue_mode="terminal_lifecycle_queue",
            queue_status="terminal",
            actionability="retire",
            changed=True,
        )
    elif lifecycle_window_decision.decision == "hold_lifecycle_window" or queue_status == "hold":
        queue_state.update(
            status="hold",
            decision="hold_lifecycle_queue",
            queue_mode="hold_lifecycle_queue",
            queue_status="hold",
            actionability="hold",
            changed=True,
        )
    elif queue_status == "waiting":
        queue_state.update(
            status="waiting",
            decision="wait_lifecycle_queue",
            queue_mode="waiting_lifecycle_queue",
            queue_status="waiting",
            actionability="wait",
            changed=True,
        )
    elif (
        lifecycle_window_decision.decision in {"buffer_lifecycle_window", "defer_lifecycle_window"}
        or queue_status == "scheduled"
    ):
        queue_state.update(
            status="scheduled",
            decision=(
                "defer_lifecycle_queue"
                if lifecycle_window_decision.decision == "defer_lifecycle_window"
                else "buffer_lifecycle_queue"
            ),
            queue_mode=(
                "deferred_lifecycle_queue"
                if lifecycle_window_decision.decision == "defer_lifecycle_window"
                else "buffered_lifecycle_queue"
            ),
            queue_status="scheduled",
            actionability="buffer",
            changed=True,
        )
    elif queue_status == "overdue":
        queue_state.update(
            status="active",
            decision=(
                "overdue_close_loop_lifecycle_queue"
                if lifecycle_window_decision.decision == "close_loop_lifecycle_window"
                else "overdue_lifecycle_queue"
            ),
            queue_mode=(
                "overdue_close_loop_lifecycle_queue"
                if lifecycle_window_decision.decision == "close_loop_lifecycle_window"
                else "overdue_lifecycle_queue"
            ),
            queue_status="overdue",
            actionability=(
                "close_loop"
                if lifecycle_window_decision.decision == "close_loop_lifecycle_window"
                else "dispatch"
            ),
            changed=True,
        )
    elif (
        lifecycle_window_decision.decision == "close_loop_lifecycle_window"
        or lifecycle_state == "winding_down"
    ):
        queue_state.update(
            status="active",
            decision="close_loop_lifecycle_queue",
            queue_mode="close_loop_lifecycle_queue",
            queue_status="due",
            actionability="close_loop",
            changed=True,
        )
    elif lifecycle_window_decision.decision == "dispatch_lifecycle_window" or queue_status == "due":
        queue_state.update(
            status="active",
            decision="dispatch_lifecycle_queue",
            queue_mode="ready_lifecycle_queue",
            queue_status="due",
            actionability="dispatch",
            changed=True,
        )
    return queue_state


def _build_lifecycle_queue_rationale(*, decision: str) -> str:
    rationale = (
        "The proactive lifecycle queue keeps the current lifecycle window posture because "
        "the queue layer does not need to reinterpret that window any further."
    )
    if decision == "retire_lifecycle_queue":
        return (
            "The proactive lifecycle queue is terminal because the lifecycle window has "
            "already moved the line into a retire-ready posture."
        )
    if decision in {"hold_lifecycle_queue", "wait_lifecycle_queue"}:
        return (
            "The proactive lifecycle queue keeps the line out of dispatch so the current "
            "lifecycle posture preserves user space instead of forcing contact."
        )
    if decision in {"buffer_lifecycle_queue", "defer_lifecycle_queue"}:
        return (
            "The proactive lifecycle queue keeps the line scheduled so later touches "
            "inherit a softer lifecycle-level queue posture."
        )
    if decision in {
        "close_loop_lifecycle_queue",
        "overdue_close_loop_lifecycle_queue",
    }:
        return (
            "The proactive lifecycle queue keeps the line in a close-loop queue posture "
            "so any remaining touch stays winding-down and low-pressure."
        )
    if decision in {"dispatch_lifecycle_queue", "overdue_lifecycle_queue"}:
        return (
            "The proactive lifecycle queue keeps the line explicitly dispatchable rather "
            "than relying on an implicit queue default."
        )
    return rationale


def build_proactive_lifecycle_dispatch_decision(
    *,
    lifecycle_queue_decision: ProactiveLifecycleQueueDecision,
    dispatch_gate_decision: ProactiveDispatchGateDecision | None = None,
    current_queue_status: str = "due",
    schedule_reason: str = "",
    rendered_unit_count: int = 0,
    has_followup_content: bool = False,
) -> ProactiveLifecycleDispatchDecision:
    current_stage_label = lifecycle_queue_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_queue_decision.lifecycle_state or "active"
    queue_mode = lifecycle_queue_decision.queue_mode or "active_lifecycle_queue"
    queue_decision = lifecycle_queue_decision.decision or "dispatch_lifecycle_queue"
    queue_status = str(current_queue_status or lifecycle_queue_decision.queue_status or "due")
    additional_delay_seconds = max(
        0,
        int(lifecycle_queue_decision.additional_delay_seconds or 0),
    )
    selected_strategy_key = lifecycle_queue_decision.selected_strategy_key or "none"
    selected_pressure_mode = lifecycle_queue_decision.selected_pressure_mode or "none"
    selected_autonomy_signal = lifecycle_queue_decision.selected_autonomy_signal or "none"
    selected_delivery_mode = lifecycle_queue_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_queue_decision.primary_source or "cadence"
    controller_decision = lifecycle_queue_decision.controller_decision
    active_sources = list(lifecycle_queue_decision.active_sources)
    dispatch_notes: list[str] = list(lifecycle_queue_decision.queue_notes)

    gate_payload = dispatch_gate_decision
    gate_decision = (
        gate_payload.decision if gate_payload is not None and gate_payload.decision else "dispatch"
    )
    gate_retry_after_seconds = max(
        0,
        int(gate_payload.retry_after_seconds if gate_payload is not None else 0),
    )
    if gate_decision not in {"dispatch", "follow_local_controllers"}:
        dispatch_notes.append(f"gate:{gate_decision}")
        if primary_source in {"cadence", "queue"}:
            primary_source = "gate"
    if gate_retry_after_seconds > 0:
        additional_delay_seconds = max(additional_delay_seconds, gate_retry_after_seconds)

    if queue_status != str(lifecycle_queue_decision.queue_status or "due"):
        dispatch_notes.append(f"queue_override:{queue_status}")
        if primary_source in {"cadence", "lifecycle_queue"}:
            primary_source = "queue"
    if schedule_reason:
        dispatch_notes.append(f"schedule_reason:{schedule_reason}")
    if rendered_unit_count > 0:
        dispatch_notes.append(f"units:{rendered_unit_count}")
    shape = _resolve_lifecycle_dispatch_shape(
        lifecycle_queue_decision=lifecycle_queue_decision,
        gate_decision=gate_decision,
        queue_decision=queue_decision,
        lifecycle_state=lifecycle_state,
        queue_status=queue_status,
        rendered_unit_count=rendered_unit_count,
        has_followup_content=has_followup_content,
        primary_source=primary_source,
    )
    if shape.note:
        dispatch_notes.append(shape.note)

    dispatch_key = (
        f"{current_stage_label}_{shape.decision}_{selected_strategy_key or 'none'}"
    )

    return ProactiveLifecycleDispatchDecision(
        status=shape.status,
        dispatch_key=dispatch_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        queue_mode=queue_mode,
        dispatch_mode=shape.dispatch_mode,
        decision=shape.decision,
        actionability=shape.actionability,
        changed=shape.changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        primary_source=shape.primary_source,
        controller_decision=controller_decision,
        active_sources=_compact(active_sources, limit=8),
        dispatch_notes=_compact(dispatch_notes, limit=8),
        rationale=_resolve_lifecycle_dispatch_rationale(shape.decision, dispatch_notes),
    )


def build_proactive_lifecycle_outcome_decision(
    *,
    lifecycle_dispatch_decision: ProactiveLifecycleDispatchDecision,
    dispatched: bool,
    message_event_count: int = 0,
) -> ProactiveLifecycleOutcomeDecision:
    current_stage_label = lifecycle_dispatch_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_dispatch_decision.lifecycle_state or "active"
    dispatch_mode = lifecycle_dispatch_decision.dispatch_mode or "hold_lifecycle_dispatch"
    dispatch_decision = lifecycle_dispatch_decision.decision or "hold_lifecycle_dispatch"
    status = lifecycle_dispatch_decision.status or "hold"
    outcome_mode = "hold_lifecycle_outcome"
    decision = "lifecycle_dispatch_held"
    actionability = "hold"
    primary_source = lifecycle_dispatch_decision.primary_source or "dispatch"
    outcome_notes: list[str] = list(lifecycle_dispatch_decision.dispatch_notes)

    if dispatched and dispatch_decision == "dispatch_lifecycle_now":
        status = "sent"
        outcome_mode = "sent_lifecycle_outcome"
        decision = "lifecycle_dispatch_sent"
        actionability = "dispatch"
        outcome_notes.append(f"messages:{max(1, int(message_event_count or 0))}")
    elif dispatched and dispatch_decision == "close_loop_lifecycle_dispatch":
        status = "sent"
        outcome_mode = "close_loop_sent_lifecycle_outcome"
        decision = "lifecycle_close_loop_sent"
        actionability = "close_loop"
        outcome_notes.append(f"messages:{max(1, int(message_event_count or 0))}")
    elif dispatch_decision == "reschedule_lifecycle_dispatch":
        status = "scheduled"
        outcome_mode = "rescheduled_lifecycle_outcome"
        decision = "lifecycle_dispatch_rescheduled"
        actionability = "buffer"
    elif dispatch_decision == "retire_lifecycle_dispatch":
        status = "terminal"
        outcome_mode = "retired_lifecycle_outcome"
        decision = "lifecycle_dispatch_retired"
        actionability = "retire"
    else:
        status = "hold"
        outcome_mode = "hold_lifecycle_outcome"
        decision = "lifecycle_dispatch_held"
        actionability = "hold"

    outcome_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_dispatch_decision.selected_strategy_key or 'none'}"
    )

    rationale = (
        "The proactive lifecycle outcome records the final execution result after the "
        "authoritative lifecycle dispatch gate resolves the current proactive touch."
    )
    if decision == "lifecycle_dispatch_sent":
        rationale = (
            "The proactive lifecycle outcome records a successful send because the "
            "authoritative lifecycle dispatch gate allowed the current stage to fire now."
        )
    elif decision == "lifecycle_close_loop_sent":
        rationale = (
            "The proactive lifecycle outcome records a successful close-loop send because "
            "the authoritative lifecycle dispatch gate allowed the winding-down stage to fire."
        )
    elif decision == "lifecycle_dispatch_rescheduled":
        rationale = (
            "The proactive lifecycle outcome records a reschedule because the authoritative "
            "lifecycle dispatch gate preserved more user space before contact."
        )
    elif decision == "lifecycle_dispatch_retired":
        rationale = (
            "The proactive lifecycle outcome records a retirement because the authoritative "
            "lifecycle dispatch gate determined the proactive line should stop emitting contact."
        )
    elif "empty_followup_units" in outcome_notes:
        rationale = (
            "The proactive lifecycle outcome records a hold because the current lifecycle "
            "dispatch did not have any sendable follow-up content."
        )

    return ProactiveLifecycleOutcomeDecision(
        status=status,
        outcome_key=outcome_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        dispatch_mode=dispatch_mode,
        outcome_mode=outcome_mode,
        decision=decision,
        actionability=actionability,
        dispatched=dispatched,
        message_event_count=max(0, int(message_event_count or 0)),
        changed=True,
        additional_delay_seconds=max(
            0,
            int(lifecycle_dispatch_decision.additional_delay_seconds or 0),
        ),
        selected_strategy_key=(lifecycle_dispatch_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_dispatch_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(lifecycle_dispatch_decision.selected_autonomy_signal or "none"),
        selected_delivery_mode=(lifecycle_dispatch_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        dispatch_decision=dispatch_decision,
        active_sources=_compact(lifecycle_dispatch_decision.active_sources, limit=8),
        outcome_notes=_compact(outcome_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_resolution_decision(
    *,
    lifecycle_outcome_decision: ProactiveLifecycleOutcomeDecision,
    lifecycle_queue_decision: ProactiveLifecycleQueueDecision,
    line_state_decision: ProactiveLineStateDecision,
    line_transition_decision: ProactiveLineTransitionDecision,
) -> ProactiveLifecycleResolutionDecision:
    current_stage_label = lifecycle_outcome_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_outcome_decision.lifecycle_state or "active"
    outcome_mode = lifecycle_outcome_decision.outcome_mode or "hold_lifecycle_outcome"
    outcome_decision = lifecycle_outcome_decision.decision or "lifecycle_dispatch_held"
    remaining_stage_count = max(0, int(line_state_decision.remaining_stage_count or 0))
    next_stage_label = line_transition_decision.next_stage_label
    line_state = line_state_decision.line_state or "steady"
    line_exit_mode = line_transition_decision.line_exit_mode or "stay"
    status = lifecycle_outcome_decision.status or "hold"
    resolution_mode = "hold_lifecycle_resolution"
    decision = "hold_lifecycle_resolution"
    actionability = "hold"
    queue_override_status: str | None = "hold"
    additional_delay_seconds = max(
        int(lifecycle_outcome_decision.additional_delay_seconds or 0),
        int(lifecycle_queue_decision.additional_delay_seconds or 0),
        0,
    )
    primary_source = lifecycle_outcome_decision.primary_source or "outcome"
    resolution_notes: list[str] = list(lifecycle_outcome_decision.outcome_notes)
    if line_state:
        resolution_notes.append(f"line:{line_state}")
    if line_exit_mode:
        resolution_notes.append(f"exit:{line_exit_mode}")
    if next_stage_label:
        resolution_notes.append(f"next:{next_stage_label}")

    remaining_after_dispatch = remaining_stage_count
    if lifecycle_outcome_decision.dispatched:
        remaining_after_dispatch = max(0, remaining_stage_count - 1)

    if (
        outcome_decision
        in {
            "lifecycle_dispatch_retired",
            "lifecycle_close_loop_sent",
        }
        or line_exit_mode == "retire"
    ):
        status = "terminal"
        resolution_mode = "terminal_lifecycle_resolution"
        decision = "retire_lifecycle_resolution"
        actionability = "retire"
        queue_override_status = "terminal"
        remaining_after_dispatch = 0
        next_stage_label = None
    elif outcome_decision == "lifecycle_dispatch_rescheduled":
        status = "scheduled"
        resolution_mode = "buffered_lifecycle_resolution"
        decision = "buffer_lifecycle_resolution"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif outcome_decision == "lifecycle_dispatch_held":
        status = "hold"
        resolution_mode = "hold_lifecycle_resolution"
        decision = "hold_lifecycle_resolution"
        actionability = "hold"
        queue_override_status = "hold"
    elif outcome_decision == "lifecycle_dispatch_sent":
        if remaining_after_dispatch <= 0 and not next_stage_label:
            status = "terminal"
            resolution_mode = "terminal_lifecycle_resolution"
            decision = "retire_lifecycle_resolution"
            actionability = "retire"
            queue_override_status = "terminal"
        else:
            status = "active"
            resolution_mode = "active_lifecycle_resolution"
            decision = "continue_lifecycle_resolution"
            actionability = "continue"
            queue_override_status = None
    else:
        resolution_notes.append("fallback_hold")

    resolution_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_outcome_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_outcome_decision.changed
        or line_state_decision.changed
        or line_transition_decision.changed
        or decision != "hold_lifecycle_resolution"
    )
    rationale = (
        "The proactive lifecycle resolution converts the post-dispatch outcome into "
        "the final lifecycle posture that future queueing should respect."
    )
    if decision == "continue_lifecycle_resolution":
        rationale = (
            "The proactive lifecycle resolution keeps the proactive line alive because "
            "the current touch was sent successfully and there is still a future stage "
            "to inherit the line."
        )
    elif decision == "buffer_lifecycle_resolution":
        rationale = (
            "The proactive lifecycle resolution keeps the line buffered because the "
            "current touch stayed scheduled instead of becoming an actual send."
        )
    elif decision == "retire_lifecycle_resolution":
        rationale = (
            "The proactive lifecycle resolution retires the line because the proactive "
            "touch has either closed the loop or reached a terminal stop condition."
        )
    elif decision == "hold_lifecycle_resolution":
        rationale = (
            "The proactive lifecycle resolution keeps the line on hold because the "
            "current proactive attempt should preserve user space instead of pushing forward."
        )

    return ProactiveLifecycleResolutionDecision(
        status=status,
        resolution_key=resolution_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        outcome_mode=outcome_mode,
        resolution_mode=resolution_mode,
        decision=decision,
        actionability=actionability,
        changed=changed,
        queue_override_status=queue_override_status,
        remaining_stage_count=remaining_after_dispatch,
        next_stage_label=next_stage_label,
        line_state=line_state,
        line_exit_mode=line_exit_mode,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=(lifecycle_outcome_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_outcome_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(lifecycle_outcome_decision.selected_autonomy_signal or "none"),
        selected_delivery_mode=(lifecycle_outcome_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        outcome_decision=outcome_decision,
        active_sources=_compact(lifecycle_outcome_decision.active_sources, limit=8),
        resolution_notes=_compact(resolution_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_activation_decision(
    *,
    lifecycle_resolution_decision: ProactiveLifecycleResolutionDecision,
) -> ProactiveLifecycleActivationDecision:
    current_stage_label = lifecycle_resolution_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_resolution_decision.lifecycle_state or "active"
    resolution_mode = lifecycle_resolution_decision.resolution_mode or "hold_lifecycle_resolution"
    resolution_decision = lifecycle_resolution_decision.decision or "hold_lifecycle_resolution"
    line_state = lifecycle_resolution_decision.line_state or "steady"
    line_exit_mode = lifecycle_resolution_decision.line_exit_mode or "stay"
    remaining_stage_count = max(
        0,
        int(lifecycle_resolution_decision.remaining_stage_count or 0),
    )
    next_stage_label = lifecycle_resolution_decision.next_stage_label
    active_stage_label = current_stage_label
    status = lifecycle_resolution_decision.status or "hold"
    activation_mode = "hold_lifecycle_activation"
    decision = "hold_current_lifecycle_stage"
    actionability = "hold"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0,
        int(lifecycle_resolution_decision.additional_delay_seconds or 0),
    )
    primary_source = lifecycle_resolution_decision.primary_source or "resolution"
    activation_notes: list[str] = list(lifecycle_resolution_decision.resolution_notes)
    if line_state:
        activation_notes.append(f"line:{line_state}")
    if line_exit_mode:
        activation_notes.append(f"exit:{line_exit_mode}")
    if next_stage_label:
        activation_notes.append(f"next:{next_stage_label}")

    if resolution_decision == "retire_lifecycle_resolution":
        status = "terminal"
        activation_mode = "terminal_lifecycle_activation"
        decision = "retire_lifecycle_line"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        queue_override_status = "terminal"
        remaining_stage_count = 0
    elif resolution_decision == "buffer_lifecycle_resolution":
        status = "scheduled"
        activation_mode = "buffered_lifecycle_activation"
        decision = "buffer_current_lifecycle_stage"
        actionability = "buffer"
        active_stage_label = current_stage_label
        queue_override_status = "scheduled"
    elif resolution_decision == "hold_lifecycle_resolution":
        status = "hold"
        activation_mode = "hold_lifecycle_activation"
        decision = "hold_current_lifecycle_stage"
        actionability = "hold"
        active_stage_label = current_stage_label
        queue_override_status = "hold"
    elif resolution_decision == "continue_lifecycle_resolution":
        if next_stage_label:
            status = "active"
            activation_mode = "active_lifecycle_activation"
            decision = "activate_next_lifecycle_stage"
            actionability = "activate"
            active_stage_label = next_stage_label
            queue_override_status = None
        else:
            status = "terminal"
            activation_mode = "terminal_lifecycle_activation"
            decision = "retire_lifecycle_line"
            actionability = "retire"
            active_stage_label = None
            next_stage_label = None
            queue_override_status = "terminal"
            remaining_stage_count = 0
    else:
        activation_notes.append("fallback_hold")

    activation_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_resolution_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_resolution_decision.changed
        or active_stage_label != current_stage_label
        or decision != "hold_current_lifecycle_stage"
    )
    rationale = (
        "The proactive lifecycle activation converts the post-dispatch lifecycle "
        "resolution into the stage that should stay active for future proactive work."
    )
    if decision == "activate_next_lifecycle_stage":
        rationale = (
            "The proactive lifecycle activation moves the proactive line forward because "
            "the previous touch resolved cleanly and the next stage should inherit control."
        )
    elif decision == "buffer_current_lifecycle_stage":
        rationale = (
            "The proactive lifecycle activation keeps the current stage active but "
            "buffered because the line was rescheduled instead of actually sent."
        )
    elif decision == "hold_current_lifecycle_stage":
        rationale = (
            "The proactive lifecycle activation keeps the current stage on hold because "
            "the line should preserve user space instead of advancing."
        )
    elif decision == "retire_lifecycle_line":
        rationale = (
            "The proactive lifecycle activation retires the proactive line because the "
            "lifecycle has closed cleanly or reached a terminal stop condition."
        )

    return ProactiveLifecycleActivationDecision(
        status=status,
        activation_key=activation_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        resolution_mode=resolution_mode,
        activation_mode=activation_mode,
        decision=decision,
        actionability=actionability,
        changed=changed,
        active_stage_label=active_stage_label,
        next_stage_label=next_stage_label,
        queue_override_status=queue_override_status,
        remaining_stage_count=remaining_stage_count,
        line_state=line_state,
        line_exit_mode=line_exit_mode,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=(lifecycle_resolution_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_resolution_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(lifecycle_resolution_decision.selected_autonomy_signal or "none"),
        selected_delivery_mode=(lifecycle_resolution_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        resolution_decision=resolution_decision,
        active_sources=_compact(lifecycle_resolution_decision.active_sources, limit=8),
        activation_notes=_compact(activation_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_settlement_decision(
    *,
    lifecycle_activation_decision: ProactiveLifecycleActivationDecision,
) -> ProactiveLifecycleSettlementDecision:
    current_stage_label = lifecycle_activation_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_activation_decision.lifecycle_state or "active"
    activation_mode = lifecycle_activation_decision.activation_mode or "hold_lifecycle_activation"
    activation_decision = lifecycle_activation_decision.decision or "hold_current_lifecycle_stage"
    active_stage_label = lifecycle_activation_decision.active_stage_label
    next_stage_label = lifecycle_activation_decision.next_stage_label
    remaining_stage_count = max(
        0,
        int(lifecycle_activation_decision.remaining_stage_count or 0),
    )
    line_state = lifecycle_activation_decision.line_state or "steady"
    line_exit_mode = lifecycle_activation_decision.line_exit_mode or "stay"
    status = lifecycle_activation_decision.status or "hold"
    settlement_mode = "hold_lifecycle_settlement"
    decision = "hold_lifecycle_settlement"
    actionability = "hold"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0,
        int(lifecycle_activation_decision.additional_delay_seconds or 0),
    )
    primary_source = lifecycle_activation_decision.primary_source or "activation"
    settlement_notes: list[str] = list(lifecycle_activation_decision.activation_notes)
    if line_state:
        settlement_notes.append(f"line:{line_state}")
    if line_exit_mode:
        settlement_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        settlement_notes.append(f"active:{active_stage_label}")

    if activation_decision == "activate_next_lifecycle_stage":
        status = "active"
        settlement_mode = "active_lifecycle_settlement"
        decision = "keep_lifecycle_active"
        actionability = "activate"
        queue_override_status = None
    elif activation_decision == "buffer_current_lifecycle_stage":
        status = "scheduled"
        settlement_mode = "buffered_lifecycle_settlement"
        decision = "buffer_lifecycle_settlement"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif activation_decision == "hold_current_lifecycle_stage":
        status = "hold"
        settlement_mode = "hold_lifecycle_settlement"
        decision = "hold_lifecycle_settlement"
        actionability = "hold"
        queue_override_status = "hold"
    elif activation_decision == "retire_lifecycle_line":
        status = "terminal"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
        if line_exit_mode == "close_loop":
            settlement_mode = "close_loop_lifecycle_settlement"
            decision = "close_lifecycle_settlement"
            actionability = "close_loop"
        else:
            settlement_mode = "terminal_lifecycle_settlement"
            decision = "retire_lifecycle_settlement"
            actionability = "retire"
    else:
        settlement_notes.append("fallback_hold")

    settlement_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_activation_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_activation_decision.changed
        or decision != "hold_lifecycle_settlement"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle settlement converts the post-activation lifecycle "
        "shape into the final line posture that future queue and dispatch logic should honor."
    )
    if decision == "keep_lifecycle_active":
        rationale = (
            "The proactive lifecycle settlement keeps the lifecycle active because "
            "the next stage should now inherit the proactive line."
        )
    elif decision == "buffer_lifecycle_settlement":
        rationale = (
            "The proactive lifecycle settlement keeps the lifecycle buffered because "
            "the current stage is still active but should wait before the next touch."
        )
    elif decision == "hold_lifecycle_settlement":
        rationale = (
            "The proactive lifecycle settlement holds the lifecycle because the line "
            "should preserve user space instead of pushing forward."
        )
    elif decision == "close_lifecycle_settlement":
        rationale = (
            "The proactive lifecycle settlement closes the lifecycle because the line "
            "reached a clean close-loop ending after the current touch."
        )
    elif decision == "retire_lifecycle_settlement":
        rationale = (
            "The proactive lifecycle settlement retires the lifecycle because the line "
            "has reached a terminal stop condition."
        )

    return ProactiveLifecycleSettlementDecision(
        status=status,
        settlement_key=settlement_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        activation_mode=activation_mode,
        settlement_mode=settlement_mode,
        decision=decision,
        actionability=actionability,
        changed=changed,
        active_stage_label=active_stage_label,
        next_stage_label=next_stage_label,
        queue_override_status=queue_override_status,
        remaining_stage_count=remaining_stage_count,
        line_state=line_state,
        line_exit_mode=line_exit_mode,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=(lifecycle_activation_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_activation_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(lifecycle_activation_decision.selected_autonomy_signal or "none"),
        selected_delivery_mode=(lifecycle_activation_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        activation_decision=activation_decision,
        active_sources=_compact(lifecycle_activation_decision.active_sources, limit=8),
        settlement_notes=_compact(settlement_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_closure_decision(
    *,
    lifecycle_settlement_decision: ProactiveLifecycleSettlementDecision,
) -> ProactiveLifecycleClosureDecision:
    current_stage_label = lifecycle_settlement_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_settlement_decision.lifecycle_state or "active"
    settlement_mode = lifecycle_settlement_decision.settlement_mode or "hold_lifecycle_settlement"
    settlement_decision = lifecycle_settlement_decision.decision or "hold_lifecycle_settlement"
    active_stage_label = lifecycle_settlement_decision.active_stage_label
    next_stage_label = lifecycle_settlement_decision.next_stage_label
    remaining_stage_count = max(
        0,
        int(lifecycle_settlement_decision.remaining_stage_count or 0),
    )
    line_state = lifecycle_settlement_decision.line_state or "steady"
    line_exit_mode = lifecycle_settlement_decision.line_exit_mode or "stay"
    status = lifecycle_settlement_decision.status or "hold"
    closure_mode = "paused_lifecycle_closure"
    decision = "pause_lifecycle_closure"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0,
        int(lifecycle_settlement_decision.additional_delay_seconds or 0),
    )
    primary_source = lifecycle_settlement_decision.primary_source or "settlement"
    closure_notes: list[str] = list(lifecycle_settlement_decision.settlement_notes)
    if line_state:
        closure_notes.append(f"line:{line_state}")
    if line_exit_mode:
        closure_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        closure_notes.append(f"active:{active_stage_label}")

    if settlement_decision == "keep_lifecycle_active":
        status = "active"
        closure_mode = "open_lifecycle_closure"
        decision = "keep_open_lifecycle_closure"
        actionability = "continue"
        queue_override_status = None
    elif settlement_decision == "buffer_lifecycle_settlement":
        status = "scheduled"
        closure_mode = "buffered_lifecycle_closure"
        decision = "buffer_lifecycle_closure"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif settlement_decision == "hold_lifecycle_settlement":
        status = "hold"
        closure_mode = "paused_lifecycle_closure"
        decision = "pause_lifecycle_closure"
        actionability = "pause"
        queue_override_status = "hold"
    elif settlement_decision == "close_lifecycle_settlement":
        status = "terminal"
        closure_mode = "close_loop_lifecycle_closure"
        decision = "close_loop_lifecycle_closure"
        actionability = "close_loop"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif settlement_decision == "retire_lifecycle_settlement":
        status = "terminal"
        closure_mode = "terminal_lifecycle_closure"
        decision = "retire_lifecycle_closure"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        closure_notes.append("fallback_pause")

    closure_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_settlement_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_settlement_decision.changed
        or decision != "pause_lifecycle_closure"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle closure converts the post-settlement lifecycle "
        "shape into the final close posture that downstream queue and "
        "inspection layers should honor."
    )
    if decision == "keep_open_lifecycle_closure":
        rationale = (
            "The proactive lifecycle closure keeps the lifecycle open because the line "
            "should stay active for the next proactive stage."
        )
    elif decision == "buffer_lifecycle_closure":
        rationale = (
            "The proactive lifecycle closure keeps the lifecycle buffered because the "
            "line should stay open but wait before the next touch."
        )
    elif decision == "pause_lifecycle_closure":
        rationale = (
            "The proactive lifecycle closure pauses the lifecycle because the line "
            "should preserve user space instead of pushing forward."
        )
    elif decision == "close_loop_lifecycle_closure":
        rationale = (
            "The proactive lifecycle closure closes the lifecycle because the line "
            "has reached a clean close-loop ending."
        )
    elif decision == "retire_lifecycle_closure":
        rationale = (
            "The proactive lifecycle closure retires the lifecycle because the line "
            "has reached a terminal stop condition."
        )

    return ProactiveLifecycleClosureDecision(
        status=status,
        closure_key=closure_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        settlement_mode=settlement_mode,
        closure_mode=closure_mode,
        decision=decision,
        actionability=actionability,
        changed=changed,
        active_stage_label=active_stage_label,
        next_stage_label=next_stage_label,
        queue_override_status=queue_override_status,
        remaining_stage_count=remaining_stage_count,
        line_state=line_state,
        line_exit_mode=line_exit_mode,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=(lifecycle_settlement_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_settlement_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(lifecycle_settlement_decision.selected_autonomy_signal or "none"),
        selected_delivery_mode=(lifecycle_settlement_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        settlement_decision=settlement_decision,
        active_sources=_compact(lifecycle_settlement_decision.active_sources, limit=8),
        closure_notes=_compact(closure_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_availability_decision(
    *,
    lifecycle_closure_decision: ProactiveLifecycleClosureDecision,
) -> ProactiveLifecycleAvailabilityDecision:
    current_stage_label = lifecycle_closure_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_closure_decision.lifecycle_state or "active"
    closure_mode = lifecycle_closure_decision.closure_mode or "paused_lifecycle_closure"
    closure_decision = lifecycle_closure_decision.decision or "pause_lifecycle_closure"
    active_stage_label = lifecycle_closure_decision.active_stage_label
    next_stage_label = lifecycle_closure_decision.next_stage_label
    remaining_stage_count = max(
        0,
        int(lifecycle_closure_decision.remaining_stage_count or 0),
    )
    line_state = lifecycle_closure_decision.line_state or "steady"
    line_exit_mode = lifecycle_closure_decision.line_exit_mode or "stay"
    status = lifecycle_closure_decision.status or "hold"
    availability_mode = "paused_lifecycle_availability"
    decision = "pause_lifecycle_availability"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0,
        int(lifecycle_closure_decision.additional_delay_seconds or 0),
    )
    primary_source = lifecycle_closure_decision.primary_source or "closure"
    availability_notes: list[str] = list(lifecycle_closure_decision.closure_notes)
    if line_state:
        availability_notes.append(f"line:{line_state}")
    if line_exit_mode:
        availability_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        availability_notes.append(f"active:{active_stage_label}")

    if closure_decision == "keep_open_lifecycle_closure":
        status = "active"
        availability_mode = "open_lifecycle_availability"
        decision = "keep_lifecycle_available"
        actionability = "continue"
        queue_override_status = None
    elif closure_decision == "buffer_lifecycle_closure":
        status = "scheduled"
        availability_mode = "buffered_lifecycle_availability"
        decision = "buffer_lifecycle_availability"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif closure_decision == "pause_lifecycle_closure":
        status = "hold"
        availability_mode = "paused_lifecycle_availability"
        decision = "pause_lifecycle_availability"
        actionability = "pause"
        queue_override_status = "hold"
    elif closure_decision == "close_loop_lifecycle_closure":
        status = "terminal"
        availability_mode = "closed_lifecycle_availability"
        decision = "close_loop_lifecycle_availability"
        actionability = "close_loop"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif closure_decision == "retire_lifecycle_closure":
        status = "terminal"
        availability_mode = "retired_lifecycle_availability"
        decision = "retire_lifecycle_availability"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        availability_notes.append("fallback_pause")

    availability_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_closure_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_closure_decision.changed
        or decision != "pause_lifecycle_availability"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle availability converts the post-closure lifecycle "
        "shape into the final availability posture that future queue surfaces should honor."
    )
    if decision == "keep_lifecycle_available":
        rationale = (
            "The proactive lifecycle availability keeps the lifecycle available because "
            "the line should remain open for the next proactive touch."
        )
    elif decision == "buffer_lifecycle_availability":
        rationale = (
            "The proactive lifecycle availability keeps the lifecycle buffered because "
            "the line is still available but should wait before the next touch."
        )
    elif decision == "pause_lifecycle_availability":
        rationale = (
            "The proactive lifecycle availability pauses the lifecycle because the line "
            "should preserve user space instead of remaining actively available."
        )
    elif decision == "close_loop_lifecycle_availability":
        rationale = (
            "The proactive lifecycle availability closes the lifecycle because the line "
            "has reached a clean close-loop ending."
        )
    elif decision == "retire_lifecycle_availability":
        rationale = (
            "The proactive lifecycle availability retires the lifecycle because the line "
            "has reached a terminal stop condition."
        )

    return ProactiveLifecycleAvailabilityDecision(
        status=status,
        availability_key=availability_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        closure_mode=closure_mode,
        availability_mode=availability_mode,
        decision=decision,
        actionability=actionability,
        changed=changed,
        active_stage_label=active_stage_label,
        next_stage_label=next_stage_label,
        queue_override_status=queue_override_status,
        remaining_stage_count=remaining_stage_count,
        line_state=line_state,
        line_exit_mode=line_exit_mode,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=(lifecycle_closure_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_closure_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(lifecycle_closure_decision.selected_autonomy_signal or "none"),
        selected_delivery_mode=(lifecycle_closure_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        closure_decision=closure_decision,
        active_sources=_compact(lifecycle_closure_decision.active_sources, limit=8),
        availability_notes=_compact(availability_notes, limit=10),
        rationale=rationale,
    )


@dataclass(slots=True, frozen=True)
class _LifecycleChainSpec:
    phase: str
    previous_phase: str
    decision_cls: type[object]
    primary_source: str
    active_previous_decision: str
    active_mode: str
    active_decision: str
    active_actionability: str
    base_rationale: str
    active_rationale: str
    buffered_previous_decision: str
    buffered_mode: str
    buffered_decision: str
    buffered_rationale: str
    paused_previous_decision: str
    paused_mode: str
    paused_decision: str
    paused_rationale: str
    archived_previous_decision: str
    archived_mode: str
    archived_decision: str
    archived_rationale: str
    retired_previous_decision: str
    retired_mode: str
    retired_decision: str
    retired_rationale: str

    @property
    def key_field(self) -> str:
        return f"{self.phase}_key"

    @property
    def mode_field(self) -> str:
        return f"{self.phase}_mode"

    @property
    def notes_field(self) -> str:
        return f"{self.phase}_notes"

    @property
    def previous_mode_field(self) -> str:
        return f"{self.previous_phase}_mode"

    @property
    def previous_notes_field(self) -> str:
        return f"{self.previous_phase}_notes"

    @property
    def previous_decision_field(self) -> str:
        return f"{self.previous_phase}_decision"


def _build_lifecycle_chain_decision(
    *,
    previous_decision: object,
    spec: _LifecycleChainSpec,
) -> object:
    current_stage_label = getattr(previous_decision, "current_stage_label", None) or "unknown"
    lifecycle_state = getattr(previous_decision, "lifecycle_state", None) or "active"
    previous_mode = getattr(previous_decision, spec.previous_mode_field, None) or (
        f"paused_lifecycle_{spec.previous_phase}"
    )
    previous_decision_value = (
        getattr(previous_decision, "decision", None) or spec.paused_previous_decision
    )
    active_stage_label = getattr(previous_decision, "active_stage_label", None)
    next_stage_label = getattr(previous_decision, "next_stage_label", None)
    remaining_stage_count = max(
        0,
        int(getattr(previous_decision, "remaining_stage_count", 0) or 0),
    )
    line_state = getattr(previous_decision, "line_state", None) or "steady"
    line_exit_mode = getattr(previous_decision, "line_exit_mode", None) or "stay"
    status = getattr(previous_decision, "status", None) or "hold"
    current_mode = spec.paused_mode
    current_decision = spec.paused_decision
    actionability = "pause"
    queue_override_status: str | None = "hold"
    additional_delay_seconds = max(
        0,
        int(getattr(previous_decision, "additional_delay_seconds", 0) or 0),
    )
    primary_source = getattr(previous_decision, "primary_source", None) or spec.primary_source
    notes = list(getattr(previous_decision, spec.previous_notes_field, None) or [])
    if line_state:
        notes.append(f"line:{line_state}")
    if line_exit_mode:
        notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        notes.append(f"active:{active_stage_label}")

    rationale = spec.base_rationale
    if previous_decision_value == spec.active_previous_decision:
        status = "active"
        current_mode = spec.active_mode
        current_decision = spec.active_decision
        actionability = spec.active_actionability
        queue_override_status = None
        rationale = spec.active_rationale
    elif previous_decision_value == spec.buffered_previous_decision:
        status = "scheduled"
        current_mode = spec.buffered_mode
        current_decision = spec.buffered_decision
        actionability = "buffer"
        queue_override_status = "scheduled"
        rationale = spec.buffered_rationale
    elif previous_decision_value == spec.paused_previous_decision:
        status = "hold"
        current_mode = spec.paused_mode
        current_decision = spec.paused_decision
        actionability = "pause"
        queue_override_status = "hold"
        rationale = spec.paused_rationale
    elif previous_decision_value == spec.archived_previous_decision:
        status = "terminal"
        current_mode = spec.archived_mode
        current_decision = spec.archived_decision
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
        rationale = spec.archived_rationale
    elif previous_decision_value == spec.retired_previous_decision:
        status = "terminal"
        current_mode = spec.retired_mode
        current_decision = spec.retired_decision
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
        rationale = spec.retired_rationale
    else:
        notes.append("fallback_pause")

    decision_key = (
        f"{current_stage_label}_{current_decision}_"
        f"{getattr(previous_decision, 'selected_strategy_key', None) or 'none'}"
    )
    changed = bool(
        getattr(previous_decision, "changed", False)
        or current_decision != spec.paused_decision
        or active_stage_label != current_stage_label
    )

    payload = {
        "status": status,
        spec.key_field: decision_key,
        "current_stage_label": current_stage_label,
        "lifecycle_state": lifecycle_state,
        spec.previous_mode_field: previous_mode,
        spec.mode_field: current_mode,
        "decision": current_decision,
        "actionability": actionability,
        "changed": changed,
        "active_stage_label": active_stage_label,
        "next_stage_label": next_stage_label,
        "queue_override_status": queue_override_status,
        "remaining_stage_count": remaining_stage_count,
        "line_state": line_state,
        "line_exit_mode": line_exit_mode,
        "additional_delay_seconds": additional_delay_seconds,
        "selected_strategy_key": getattr(previous_decision, "selected_strategy_key", None)
        or "none",
        "selected_pressure_mode": getattr(previous_decision, "selected_pressure_mode", None)
        or "none",
        "selected_autonomy_signal": getattr(previous_decision, "selected_autonomy_signal", None)
        or "none",
        "selected_delivery_mode": getattr(previous_decision, "selected_delivery_mode", None)
        or "none",
        "primary_source": primary_source,
        spec.previous_decision_field: previous_decision_value,
        "active_sources": _compact(
            getattr(previous_decision, "active_sources", None) or [],
            limit=8,
        ),
        spec.notes_field: _compact(notes, limit=10),
        "rationale": rationale,
    }
    return spec.decision_cls(**payload)


_LIFECYCLE_CHAIN_SPECS: dict[str, _LifecycleChainSpec] = {
    "retention": _LifecycleChainSpec(
        phase="retention",
        previous_phase="availability",
        decision_cls=ProactiveLifecycleRetentionDecision,
        primary_source="availability",
        active_previous_decision="keep_lifecycle_available",
        active_mode="retained_lifecycle_retention",
        active_decision="retain_lifecycle_retention",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle retention converts the post-availability "
            "lifecycle shape into the final retained posture that queue and "
            "inspection layers should honor."
        ),
        active_rationale=(
            "The proactive lifecycle retention keeps the lifecycle retained because "
            "the line should remain present for the next proactive touch."
        ),
        buffered_previous_decision="buffer_lifecycle_availability",
        buffered_mode="buffered_lifecycle_retention",
        buffered_decision="buffer_lifecycle_retention",
        buffered_rationale=(
            "The proactive lifecycle retention keeps the lifecycle buffered because "
            "the line stays retained but should wait before the next touch."
        ),
        paused_previous_decision="pause_lifecycle_availability",
        paused_mode="paused_lifecycle_retention",
        paused_decision="pause_lifecycle_retention",
        paused_rationale=(
            "The proactive lifecycle retention pauses the lifecycle because the line "
            "should remain retained without actively pushing forward."
        ),
        archived_previous_decision="close_loop_lifecycle_availability",
        archived_mode="archived_lifecycle_retention",
        archived_decision="archive_lifecycle_retention",
        archived_rationale=(
            "The proactive lifecycle retention archives the lifecycle because the "
            "line reached a clean close-loop ending."
        ),
        retired_previous_decision="retire_lifecycle_availability",
        retired_mode="retired_lifecycle_retention",
        retired_decision="retire_lifecycle_retention",
        retired_rationale=(
            "The proactive lifecycle retention retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "eligibility": _LifecycleChainSpec(
        phase="eligibility",
        previous_phase="retention",
        decision_cls=ProactiveLifecycleEligibilityDecision,
        primary_source="retention",
        active_previous_decision="retain_lifecycle_retention",
        active_mode="eligible_lifecycle_eligibility",
        active_decision="keep_lifecycle_eligible",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle eligibility converts the post-retention "
            "lifecycle shape into the final eligible posture that downstream queue "
            "and dispatch selection should honor."
        ),
        active_rationale=(
            "The proactive lifecycle eligibility keeps the lifecycle eligible because "
            "the retained line should remain a valid candidate for the next proactive "
            "touch."
        ),
        buffered_previous_decision="buffer_lifecycle_retention",
        buffered_mode="buffered_lifecycle_eligibility",
        buffered_decision="buffer_lifecycle_eligibility",
        buffered_rationale=(
            "The proactive lifecycle eligibility keeps the lifecycle buffered because "
            "the retained line stays eligible but should wait before being "
            "considered."
        ),
        paused_previous_decision="pause_lifecycle_retention",
        paused_mode="paused_lifecycle_eligibility",
        paused_decision="pause_lifecycle_eligibility",
        paused_rationale=(
            "The proactive lifecycle eligibility pauses the lifecycle because the "
            "line should remain retained without actively re-entering the queue."
        ),
        archived_previous_decision="archive_lifecycle_retention",
        archived_mode="archived_lifecycle_eligibility",
        archived_decision="archive_lifecycle_eligibility",
        archived_rationale=(
            "The proactive lifecycle eligibility archives the lifecycle because the "
            "line reached a clean close-loop ending and should no longer be "
            "considered active."
        ),
        retired_previous_decision="retire_lifecycle_retention",
        retired_mode="retired_lifecycle_eligibility",
        retired_decision="retire_lifecycle_eligibility",
        retired_rationale=(
            "The proactive lifecycle eligibility retires the lifecycle because the "
            "line has reached a terminal stop condition and should no longer be "
            "considered."
        ),
    ),
    "candidate": _LifecycleChainSpec(
        phase="candidate",
        previous_phase="eligibility",
        decision_cls=ProactiveLifecycleCandidateDecision,
        primary_source="eligibility",
        active_previous_decision="keep_lifecycle_eligible",
        active_mode="candidate_lifecycle_candidate",
        active_decision="keep_lifecycle_candidate",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle candidate converts the final eligibility posture "
            "into the downstream candidate state that queue selection should honor."
        ),
        active_rationale=(
            "The proactive lifecycle candidate keeps the lifecycle selectable because "
            "the eligible line should remain a valid proactive candidate."
        ),
        buffered_previous_decision="buffer_lifecycle_eligibility",
        buffered_mode="buffered_lifecycle_candidate",
        buffered_decision="buffer_lifecycle_candidate",
        buffered_rationale=(
            "The proactive lifecycle candidate keeps the lifecycle buffered because "
            "the line remains a candidate but should wait before re-entering "
            "selection."
        ),
        paused_previous_decision="pause_lifecycle_eligibility",
        paused_mode="paused_lifecycle_candidate",
        paused_decision="pause_lifecycle_candidate",
        paused_rationale=(
            "The proactive lifecycle candidate pauses the lifecycle because the line "
            "should remain retained without active reselection."
        ),
        archived_previous_decision="archive_lifecycle_eligibility",
        archived_mode="archived_lifecycle_candidate",
        archived_decision="archive_lifecycle_candidate",
        archived_rationale=(
            "The proactive lifecycle candidate archives the lifecycle because the "
            "line reached a clean ending and should no longer be selected."
        ),
        retired_previous_decision="retire_lifecycle_eligibility",
        retired_mode="retired_lifecycle_candidate",
        retired_decision="retire_lifecycle_candidate",
        retired_rationale=(
            "The proactive lifecycle candidate retires the lifecycle because the line "
            "has reached a terminal stop condition and should no longer be selected."
        ),
    ),
    "selectability": _LifecycleChainSpec(
        phase="selectability",
        previous_phase="candidate",
        decision_cls=ProactiveLifecycleSelectabilityDecision,
        primary_source="candidate",
        active_previous_decision="keep_lifecycle_candidate",
        active_mode="selectable_lifecycle_selectability",
        active_decision="keep_lifecycle_selectable",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle selectability converts the candidate posture "
            "into the final selectable state that downstream queue selection should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle selectability keeps the lifecycle selectable "
            "because the candidate line should remain available for reselection."
        ),
        buffered_previous_decision="buffer_lifecycle_candidate",
        buffered_mode="buffered_lifecycle_selectability",
        buffered_decision="buffer_lifecycle_selectability",
        buffered_rationale=(
            "The proactive lifecycle selectability keeps the lifecycle buffered "
            "because the line remains selectable later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_candidate",
        paused_mode="paused_lifecycle_selectability",
        paused_decision="pause_lifecycle_selectability",
        paused_rationale=(
            "The proactive lifecycle selectability pauses the lifecycle because the "
            "line should remain present without active reselection."
        ),
        archived_previous_decision="archive_lifecycle_candidate",
        archived_mode="archived_lifecycle_selectability",
        archived_decision="archive_lifecycle_selectability",
        archived_rationale=(
            "The proactive lifecycle selectability archives the lifecycle because the "
            "line reached a clean ending and should leave active selection."
        ),
        retired_previous_decision="retire_lifecycle_candidate",
        retired_mode="retired_lifecycle_selectability",
        retired_decision="retire_lifecycle_selectability",
        retired_rationale=(
            "The proactive lifecycle selectability retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "reentry": _LifecycleChainSpec(
        phase="reentry",
        previous_phase="selectability",
        decision_cls=ProactiveLifecycleReentryDecision,
        primary_source="selectability",
        active_previous_decision="keep_lifecycle_selectable",
        active_mode="reenterable_lifecycle_reentry",
        active_decision="keep_lifecycle_reentry",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle reentry converts the selectability posture into "
            "the final reentry state that future proactive scheduling should honor."
        ),
        active_rationale=(
            "The proactive lifecycle reentry keeps the lifecycle reenterable because "
            "the line should remain available for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_selectability",
        buffered_mode="buffered_lifecycle_reentry",
        buffered_decision="buffer_lifecycle_reentry",
        buffered_rationale=(
            "The proactive lifecycle reentry keeps the lifecycle buffered because the "
            "line can return later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_selectability",
        paused_mode="paused_lifecycle_reentry",
        paused_decision="pause_lifecycle_reentry",
        paused_rationale=(
            "The proactive lifecycle reentry pauses the lifecycle because the line "
            "should remain present without immediate return."
        ),
        archived_previous_decision="archive_lifecycle_selectability",
        archived_mode="archived_lifecycle_reentry",
        archived_decision="archive_lifecycle_reentry",
        archived_rationale=(
            "The proactive lifecycle reentry archives the lifecycle because the line "
            "reached a clean ending and should leave reentry."
        ),
        retired_previous_decision="retire_lifecycle_selectability",
        retired_mode="retired_lifecycle_reentry",
        retired_decision="retire_lifecycle_reentry",
        retired_rationale=(
            "The proactive lifecycle reentry retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "reactivation": _LifecycleChainSpec(
        phase="reactivation",
        previous_phase="reentry",
        decision_cls=ProactiveLifecycleReactivationDecision,
        primary_source="reentry",
        active_previous_decision="keep_lifecycle_reentry",
        active_mode="reactivatable_lifecycle_reactivation",
        active_decision="keep_lifecycle_reactivation",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle reactivation converts the reentry posture into "
            "the final reactivation state that future proactive resumption should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle reactivation keeps the lifecycle reactivatable "
            "because the line should remain ready for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_reentry",
        buffered_mode="buffered_lifecycle_reactivation",
        buffered_decision="buffer_lifecycle_reactivation",
        buffered_rationale=(
            "The proactive lifecycle reactivation keeps the lifecycle buffered "
            "because the line can reactivate later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_reentry",
        paused_mode="paused_lifecycle_reactivation",
        paused_decision="pause_lifecycle_reactivation",
        paused_rationale=(
            "The proactive lifecycle reactivation pauses the lifecycle because the "
            "line should remain present without immediate reactivation."
        ),
        archived_previous_decision="archive_lifecycle_reentry",
        archived_mode="archived_lifecycle_reactivation",
        archived_decision="archive_lifecycle_reactivation",
        archived_rationale=(
            "The proactive lifecycle reactivation archives the lifecycle because the "
            "line reached a clean ending and should leave reactivation."
        ),
        retired_previous_decision="retire_lifecycle_reentry",
        retired_mode="retired_lifecycle_reactivation",
        retired_decision="retire_lifecycle_reactivation",
        retired_rationale=(
            "The proactive lifecycle reactivation retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "resumption": _LifecycleChainSpec(
        phase="resumption",
        previous_phase="reactivation",
        decision_cls=ProactiveLifecycleResumptionDecision,
        primary_source="reactivation",
        active_previous_decision="keep_lifecycle_reactivation",
        active_mode="resumable_lifecycle_resumption",
        active_decision="keep_lifecycle_resumption",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle resumption converts the reactivation posture "
            "into the final resumption state that future proactive resumption should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle resumption keeps the lifecycle resumable because "
            "the line should remain ready for future proactive resumption."
        ),
        buffered_previous_decision="buffer_lifecycle_reactivation",
        buffered_mode="buffered_lifecycle_resumption",
        buffered_decision="buffer_lifecycle_resumption",
        buffered_rationale=(
            "The proactive lifecycle resumption keeps the lifecycle buffered because "
            "the line can resume later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_reactivation",
        paused_mode="paused_lifecycle_resumption",
        paused_decision="pause_lifecycle_resumption",
        paused_rationale=(
            "The proactive lifecycle resumption pauses the lifecycle because the line "
            "should remain present without immediate resumption."
        ),
        archived_previous_decision="archive_lifecycle_reactivation",
        archived_mode="archived_lifecycle_resumption",
        archived_decision="archive_lifecycle_resumption",
        archived_rationale=(
            "The proactive lifecycle resumption archives the lifecycle because the "
            "line reached a clean ending and should leave resumption."
        ),
        retired_previous_decision="retire_lifecycle_reactivation",
        retired_mode="retired_lifecycle_resumption",
        retired_decision="retire_lifecycle_resumption",
        retired_rationale=(
            "The proactive lifecycle resumption retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "readiness": _LifecycleChainSpec(
        phase="readiness",
        previous_phase="resumption",
        decision_cls=ProactiveLifecycleReadinessDecision,
        primary_source="resumption",
        active_previous_decision="keep_lifecycle_resumption",
        active_mode="ready_lifecycle_readiness",
        active_decision="keep_lifecycle_readiness",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle readiness converts the resumption posture into "
            "the final readiness state that future proactive return should honor."
        ),
        active_rationale=(
            "The proactive lifecycle readiness keeps the lifecycle ready because the "
            "line should remain ready for future proactive resumption."
        ),
        buffered_previous_decision="buffer_lifecycle_resumption",
        buffered_mode="buffered_lifecycle_readiness",
        buffered_decision="buffer_lifecycle_readiness",
        buffered_rationale=(
            "The proactive lifecycle readiness keeps the lifecycle buffered because "
            "the line can become ready later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_resumption",
        paused_mode="paused_lifecycle_readiness",
        paused_decision="pause_lifecycle_readiness",
        paused_rationale=(
            "The proactive lifecycle readiness pauses the lifecycle because the line "
            "should remain present without immediate readiness."
        ),
        archived_previous_decision="archive_lifecycle_resumption",
        archived_mode="archived_lifecycle_readiness",
        archived_decision="archive_lifecycle_readiness",
        archived_rationale=(
            "The proactive lifecycle readiness archives the lifecycle because the "
            "line reached a clean ending and should leave readiness."
        ),
        retired_previous_decision="retire_lifecycle_resumption",
        retired_mode="retired_lifecycle_readiness",
        retired_decision="retire_lifecycle_readiness",
        retired_rationale=(
            "The proactive lifecycle readiness retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "arming": _LifecycleChainSpec(
        phase="arming",
        previous_phase="readiness",
        decision_cls=ProactiveLifecycleArmingDecision,
        primary_source="readiness",
        active_previous_decision="keep_lifecycle_readiness",
        active_mode="armed_lifecycle_arming",
        active_decision="keep_lifecycle_arming",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle arming converts the readiness posture into the "
            "final armed state that future proactive return should honor."
        ),
        active_rationale=(
            "The proactive lifecycle arming keeps the lifecycle armed because the "
            "line should remain ready for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_readiness",
        buffered_mode="buffered_lifecycle_arming",
        buffered_decision="buffer_lifecycle_arming",
        buffered_rationale=(
            "The proactive lifecycle arming keeps the lifecycle buffered because the "
            "line can become armed later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_readiness",
        paused_mode="paused_lifecycle_arming",
        paused_decision="pause_lifecycle_arming",
        paused_rationale=(
            "The proactive lifecycle arming pauses the lifecycle because the line "
            "should remain present without immediate arming."
        ),
        archived_previous_decision="archive_lifecycle_readiness",
        archived_mode="archived_lifecycle_arming",
        archived_decision="archive_lifecycle_arming",
        archived_rationale=(
            "The proactive lifecycle arming archives the lifecycle because the line "
            "reached a clean ending and should leave arming."
        ),
        retired_previous_decision="retire_lifecycle_readiness",
        retired_mode="retired_lifecycle_arming",
        retired_decision="retire_lifecycle_arming",
        retired_rationale=(
            "The proactive lifecycle arming retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "trigger": _LifecycleChainSpec(
        phase="trigger",
        previous_phase="arming",
        decision_cls=ProactiveLifecycleTriggerDecision,
        primary_source="arming",
        active_previous_decision="keep_lifecycle_arming",
        active_mode="triggerable_lifecycle_trigger",
        active_decision="keep_lifecycle_trigger",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle trigger converts the arming posture into the "
            "final triggerable state that future proactive return should honor."
        ),
        active_rationale=(
            "The proactive lifecycle trigger keeps the lifecycle triggerable because "
            "the line should remain armed for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_arming",
        buffered_mode="buffered_lifecycle_trigger",
        buffered_decision="buffer_lifecycle_trigger",
        buffered_rationale=(
            "The proactive lifecycle trigger keeps the lifecycle buffered because the "
            "line can become triggerable later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_arming",
        paused_mode="paused_lifecycle_trigger",
        paused_decision="pause_lifecycle_trigger",
        paused_rationale=(
            "The proactive lifecycle trigger pauses the lifecycle because the line "
            "should remain present without immediate triggering."
        ),
        archived_previous_decision="archive_lifecycle_arming",
        archived_mode="archived_lifecycle_trigger",
        archived_decision="archive_lifecycle_trigger",
        archived_rationale=(
            "The proactive lifecycle trigger archives the lifecycle because the line "
            "reached a clean ending and should leave triggering."
        ),
        retired_previous_decision="retire_lifecycle_arming",
        retired_mode="retired_lifecycle_trigger",
        retired_decision="retire_lifecycle_trigger",
        retired_rationale=(
            "The proactive lifecycle trigger retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "launch": _LifecycleChainSpec(
        phase="launch",
        previous_phase="trigger",
        decision_cls=ProactiveLifecycleLaunchDecision,
        primary_source="trigger",
        active_previous_decision="keep_lifecycle_trigger",
        active_mode="launchable_lifecycle_launch",
        active_decision="keep_lifecycle_launch",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle launch converts the trigger posture into the "
            "final launchable state that future proactive return should honor."
        ),
        active_rationale=(
            "The proactive lifecycle launch keeps the lifecycle launchable because "
            "the line should remain trigger-ready for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_trigger",
        buffered_mode="buffered_lifecycle_launch",
        buffered_decision="buffer_lifecycle_launch",
        buffered_rationale=(
            "The proactive lifecycle launch keeps the lifecycle buffered because the "
            "line can become launchable later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_trigger",
        paused_mode="paused_lifecycle_launch",
        paused_decision="pause_lifecycle_launch",
        paused_rationale=(
            "The proactive lifecycle launch pauses the lifecycle because the line "
            "should remain present without immediate launch."
        ),
        archived_previous_decision="archive_lifecycle_trigger",
        archived_mode="archived_lifecycle_launch",
        archived_decision="archive_lifecycle_launch",
        archived_rationale=(
            "The proactive lifecycle launch archives the lifecycle because the line "
            "reached a clean ending and should leave launch."
        ),
        retired_previous_decision="retire_lifecycle_trigger",
        retired_mode="retired_lifecycle_launch",
        retired_decision="retire_lifecycle_launch",
        retired_rationale=(
            "The proactive lifecycle launch retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "handoff": _LifecycleChainSpec(
        phase="handoff",
        previous_phase="launch",
        decision_cls=ProactiveLifecycleHandoffDecision,
        primary_source="launch",
        active_previous_decision="keep_lifecycle_launch",
        active_mode="handoff_ready_lifecycle_handoff",
        active_decision="keep_lifecycle_handoff",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle handoff converts the launch posture into the "
            "final handoff-ready state that future proactive continuation should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle handoff keeps the lifecycle handoff-ready "
            "because the line should remain ready for future proactive continuation."
        ),
        buffered_previous_decision="buffer_lifecycle_launch",
        buffered_mode="buffered_lifecycle_handoff",
        buffered_decision="buffer_lifecycle_handoff",
        buffered_rationale=(
            "The proactive lifecycle handoff keeps the lifecycle buffered because the "
            "line can become handoff-ready later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_launch",
        paused_mode="paused_lifecycle_handoff",
        paused_decision="pause_lifecycle_handoff",
        paused_rationale=(
            "The proactive lifecycle handoff pauses the lifecycle because the line "
            "should remain present without immediate handoff."
        ),
        archived_previous_decision="archive_lifecycle_launch",
        archived_mode="archived_lifecycle_handoff",
        archived_decision="archive_lifecycle_handoff",
        archived_rationale=(
            "The proactive lifecycle handoff archives the lifecycle because the line "
            "reached a clean ending and should leave handoff."
        ),
        retired_previous_decision="retire_lifecycle_launch",
        retired_mode="retired_lifecycle_handoff",
        retired_decision="retire_lifecycle_handoff",
        retired_rationale=(
            "The proactive lifecycle handoff retires the lifecycle because the line "
            "has reached a terminal stop condition."
        ),
    ),
    "continuation": _LifecycleChainSpec(
        phase="continuation",
        previous_phase="handoff",
        decision_cls=ProactiveLifecycleContinuationDecision,
        primary_source="handoff",
        active_previous_decision="keep_lifecycle_handoff",
        active_mode="continuable_lifecycle_continuation",
        active_decision="keep_lifecycle_continuation",
        active_actionability="continue",
        base_rationale=(
            "The proactive lifecycle continuation converts the handoff posture into "
            "the final continuable state that future proactive continuation should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle continuation keeps the lifecycle continuable "
            "because the line should remain ready for future proactive continuation."
        ),
        buffered_previous_decision="buffer_lifecycle_handoff",
        buffered_mode="buffered_lifecycle_continuation",
        buffered_decision="buffer_lifecycle_continuation",
        buffered_rationale=(
            "The proactive lifecycle continuation keeps the lifecycle buffered "
            "because the line can become continuable later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_handoff",
        paused_mode="paused_lifecycle_continuation",
        paused_decision="pause_lifecycle_continuation",
        paused_rationale=(
            "The proactive lifecycle continuation pauses the lifecycle because the "
            "line should remain present without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_handoff",
        archived_mode="archived_lifecycle_continuation",
        archived_decision="archive_lifecycle_continuation",
        archived_rationale=(
            "The proactive lifecycle continuation archives the lifecycle because the "
            "line reached a clean ending and should leave continuation."
        ),
        retired_previous_decision="retire_lifecycle_handoff",
        retired_mode="retired_lifecycle_continuation",
        retired_decision="retire_lifecycle_continuation",
        retired_rationale=(
            "The proactive lifecycle continuation retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "sustainment": _LifecycleChainSpec(
        phase="sustainment",
        previous_phase="continuation",
        decision_cls=ProactiveLifecycleSustainmentDecision,
        primary_source="continuation",
        active_previous_decision="keep_lifecycle_continuation",
        active_mode="sustainable_lifecycle_sustainment",
        active_decision="sustain_lifecycle_sustainment",
        active_actionability="sustain",
        base_rationale=(
            "The proactive lifecycle sustainment converts the continuation posture "
            "into the final sustainable state that future proactive sustainment "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle sustainment keeps the lifecycle sustainable "
            "because the line should remain durably available for future proactive "
            "continuation."
        ),
        buffered_previous_decision="buffer_lifecycle_continuation",
        buffered_mode="buffered_lifecycle_sustainment",
        buffered_decision="buffer_lifecycle_sustainment",
        buffered_rationale=(
            "The proactive lifecycle sustainment keeps the lifecycle buffered because "
            "the line can become sustainably continuable later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_continuation",
        paused_mode="paused_lifecycle_sustainment",
        paused_decision="pause_lifecycle_sustainment",
        paused_rationale=(
            "The proactive lifecycle sustainment pauses the lifecycle because the "
            "line should remain present without immediate sustainment."
        ),
        archived_previous_decision="archive_lifecycle_continuation",
        archived_mode="archived_lifecycle_sustainment",
        archived_decision="archive_lifecycle_sustainment",
        archived_rationale=(
            "The proactive lifecycle sustainment archives the lifecycle because the "
            "line reached a clean ending and should leave sustainment."
        ),
        retired_previous_decision="retire_lifecycle_continuation",
        retired_mode="retired_lifecycle_sustainment",
        retired_decision="retire_lifecycle_sustainment",
        retired_rationale=(
            "The proactive lifecycle sustainment retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "stewardship": _LifecycleChainSpec(
        phase="stewardship",
        previous_phase="sustainment",
        decision_cls=ProactiveLifecycleStewardshipDecision,
        primary_source="sustainment",
        active_previous_decision="sustain_lifecycle_sustainment",
        active_mode="stewarded_lifecycle_stewardship",
        active_decision="steward_lifecycle_stewardship",
        active_actionability="steward",
        base_rationale=(
            "The proactive lifecycle stewardship converts the sustainment posture "
            "into the final stewarded state that future proactive stewardship "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle stewardship keeps the lifecycle stewarded "
            "because the line should remain responsibly available for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_sustainment",
        buffered_mode="buffered_lifecycle_stewardship",
        buffered_decision="buffer_lifecycle_stewardship",
        buffered_rationale=(
            "The proactive lifecycle stewardship keeps the lifecycle buffered "
            "because the line can become stewarded later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_sustainment",
        paused_mode="paused_lifecycle_stewardship",
        paused_decision="pause_lifecycle_stewardship",
        paused_rationale=(
            "The proactive lifecycle stewardship pauses the lifecycle because the "
            "line should remain present without immediate stewardship."
        ),
        archived_previous_decision="archive_lifecycle_sustainment",
        archived_mode="archived_lifecycle_stewardship",
        archived_decision="archive_lifecycle_stewardship",
        archived_rationale=(
            "The proactive lifecycle stewardship archives the lifecycle because the "
            "line reached a clean ending and should leave stewardship."
        ),
        retired_previous_decision="retire_lifecycle_sustainment",
        retired_mode="retired_lifecycle_stewardship",
        retired_decision="retire_lifecycle_stewardship",
        retired_rationale=(
            "The proactive lifecycle stewardship retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "guardianship": _LifecycleChainSpec(
        phase="guardianship",
        previous_phase="stewardship",
        decision_cls=ProactiveLifecycleGuardianshipDecision,
        primary_source="stewardship",
        active_previous_decision="steward_lifecycle_stewardship",
        active_mode="guarded_lifecycle_guardianship",
        active_decision="guard_lifecycle_guardianship",
        active_actionability="guard",
        base_rationale=(
            "The proactive lifecycle guardianship converts the stewardship posture "
            "into the final guarded state that future proactive guardianship should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle guardianship keeps the lifecycle guarded "
            "because the line should remain safely protected for future proactive "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_stewardship",
        buffered_mode="buffered_lifecycle_guardianship",
        buffered_decision="buffer_lifecycle_guardianship",
        buffered_rationale=(
            "The proactive lifecycle guardianship keeps the lifecycle buffered "
            "because the line can become guarded later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_stewardship",
        paused_mode="paused_lifecycle_guardianship",
        paused_decision="pause_lifecycle_guardianship",
        paused_rationale=(
            "The proactive lifecycle guardianship pauses the lifecycle because the "
            "line should remain present without immediate guardianship."
        ),
        archived_previous_decision="archive_lifecycle_stewardship",
        archived_mode="archived_lifecycle_guardianship",
        archived_decision="archive_lifecycle_guardianship",
        archived_rationale=(
            "The proactive lifecycle guardianship archives the lifecycle because "
            "the line reached a clean ending and should leave guardianship."
        ),
        retired_previous_decision="retire_lifecycle_stewardship",
        retired_mode="retired_lifecycle_guardianship",
        retired_decision="retire_lifecycle_guardianship",
        retired_rationale=(
            "The proactive lifecycle guardianship retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "oversight": _LifecycleChainSpec(
        phase="oversight",
        previous_phase="guardianship",
        decision_cls=ProactiveLifecycleOversightDecision,
        primary_source="guardianship",
        active_previous_decision="guard_lifecycle_guardianship",
        active_mode="overseen_lifecycle_oversight",
        active_decision="oversee_lifecycle_oversight",
        active_actionability="oversee",
        base_rationale=(
            "The proactive lifecycle oversight converts the guardianship posture "
            "into the final overseen state that future proactive oversight should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle oversight keeps the lifecycle overseen because "
            "the line should remain actively watched over for future proactive "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_guardianship",
        buffered_mode="buffered_lifecycle_oversight",
        buffered_decision="buffer_lifecycle_oversight",
        buffered_rationale=(
            "The proactive lifecycle oversight keeps the lifecycle buffered because "
            "the line can become overseen later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_guardianship",
        paused_mode="paused_lifecycle_oversight",
        paused_decision="pause_lifecycle_oversight",
        paused_rationale=(
            "The proactive lifecycle oversight pauses the lifecycle because the "
            "line should remain present without immediate oversight."
        ),
        archived_previous_decision="archive_lifecycle_guardianship",
        archived_mode="archived_lifecycle_oversight",
        archived_decision="archive_lifecycle_oversight",
        archived_rationale=(
            "The proactive lifecycle oversight archives the lifecycle because the "
            "line reached a clean ending and should leave oversight."
        ),
        retired_previous_decision="retire_lifecycle_guardianship",
        retired_mode="retired_lifecycle_oversight",
        retired_decision="retire_lifecycle_oversight",
        retired_rationale=(
            "The proactive lifecycle oversight retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "assurance": _LifecycleChainSpec(
        phase="assurance",
        previous_phase="oversight",
        decision_cls=ProactiveLifecycleAssuranceDecision,
        primary_source="oversight",
        active_previous_decision="oversee_lifecycle_oversight",
        active_mode="assured_lifecycle_assurance",
        active_decision="assure_lifecycle_assurance",
        active_actionability="assure",
        base_rationale=(
            "The proactive lifecycle assurance converts the oversight posture into "
            "the final assured state that future proactive assurance should honor."
        ),
        active_rationale=(
            "The proactive lifecycle assurance keeps the lifecycle assured because "
            "the line should remain confidently protected for future proactive "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_oversight",
        buffered_mode="buffered_lifecycle_assurance",
        buffered_decision="buffer_lifecycle_assurance",
        buffered_rationale=(
            "The proactive lifecycle assurance keeps the lifecycle buffered because "
            "the line can become assured later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_oversight",
        paused_mode="paused_lifecycle_assurance",
        paused_decision="pause_lifecycle_assurance",
        paused_rationale=(
            "The proactive lifecycle assurance pauses the lifecycle because the "
            "line should remain present without immediate assurance."
        ),
        archived_previous_decision="archive_lifecycle_oversight",
        archived_mode="archived_lifecycle_assurance",
        archived_decision="archive_lifecycle_assurance",
        archived_rationale=(
            "The proactive lifecycle assurance archives the lifecycle because the "
            "line reached a clean ending and should leave assurance."
        ),
        retired_previous_decision="retire_lifecycle_oversight",
        retired_mode="retired_lifecycle_assurance",
        retired_decision="retire_lifecycle_assurance",
        retired_rationale=(
            "The proactive lifecycle assurance retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "attestation": _LifecycleChainSpec(
        phase="attestation",
        previous_phase="assurance",
        decision_cls=ProactiveLifecycleAttestationDecision,
        primary_source="assurance",
        active_previous_decision="assure_lifecycle_assurance",
        active_mode="attested_lifecycle_attestation",
        active_decision="attest_lifecycle_attestation",
        active_actionability="attest",
        base_rationale=(
            "The proactive lifecycle attestation converts the assurance posture "
            "into the final attested state that future proactive attestation should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle attestation keeps the lifecycle attested "
            "because the line should remain explicitly affirmed for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_assurance",
        buffered_mode="buffered_lifecycle_attestation",
        buffered_decision="buffer_lifecycle_attestation",
        buffered_rationale=(
            "The proactive lifecycle attestation keeps the lifecycle buffered "
            "because the line can become attested later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_assurance",
        paused_mode="paused_lifecycle_attestation",
        paused_decision="pause_lifecycle_attestation",
        paused_rationale=(
            "The proactive lifecycle attestation pauses the lifecycle because the "
            "line should remain present without immediate attestation."
        ),
        archived_previous_decision="archive_lifecycle_assurance",
        archived_mode="archived_lifecycle_attestation",
        archived_decision="archive_lifecycle_attestation",
        archived_rationale=(
            "The proactive lifecycle attestation archives the lifecycle because the "
            "line reached a clean ending and should leave attestation."
        ),
        retired_previous_decision="retire_lifecycle_assurance",
        retired_mode="retired_lifecycle_attestation",
        retired_decision="retire_lifecycle_attestation",
        retired_rationale=(
            "The proactive lifecycle attestation retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "verification": _LifecycleChainSpec(
        phase="verification",
        previous_phase="attestation",
        decision_cls=ProactiveLifecycleVerificationDecision,
        primary_source="attestation",
        active_previous_decision="attest_lifecycle_attestation",
        active_mode="verified_lifecycle_verification",
        active_decision="verify_lifecycle_verification",
        active_actionability="verify",
        base_rationale=(
            "The proactive lifecycle verification converts the attestation posture "
            "into the final verified state that future proactive verification "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle verification keeps the lifecycle verified "
            "because the line should remain explicitly confirmed for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_attestation",
        buffered_mode="buffered_lifecycle_verification",
        buffered_decision="buffer_lifecycle_verification",
        buffered_rationale=(
            "The proactive lifecycle verification keeps the lifecycle buffered "
            "because the line can become verified later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_attestation",
        paused_mode="paused_lifecycle_verification",
        paused_decision="pause_lifecycle_verification",
        paused_rationale=(
            "The proactive lifecycle verification pauses the lifecycle because the "
            "line should remain present without immediate verification."
        ),
        archived_previous_decision="archive_lifecycle_attestation",
        archived_mode="archived_lifecycle_verification",
        archived_decision="archive_lifecycle_verification",
        archived_rationale=(
            "The proactive lifecycle verification archives the lifecycle because "
            "the line reached a clean ending and should leave verification."
        ),
        retired_previous_decision="retire_lifecycle_attestation",
        retired_mode="retired_lifecycle_verification",
        retired_decision="retire_lifecycle_verification",
        retired_rationale=(
            "The proactive lifecycle verification retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "certification": _LifecycleChainSpec(
        phase="certification",
        previous_phase="verification",
        decision_cls=ProactiveLifecycleCertificationDecision,
        primary_source="verification",
        active_previous_decision="verify_lifecycle_verification",
        active_mode="certified_lifecycle_certification",
        active_decision="certify_lifecycle_certification",
        active_actionability="certify",
        base_rationale=(
            "The proactive lifecycle certification converts the verification "
            "posture into the final certified state that future proactive "
            "certification should honor."
        ),
        active_rationale=(
            "The proactive lifecycle certification keeps the lifecycle certified "
            "because the line should remain explicitly certified for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_verification",
        buffered_mode="buffered_lifecycle_certification",
        buffered_decision="buffer_lifecycle_certification",
        buffered_rationale=(
            "The proactive lifecycle certification keeps the lifecycle buffered "
            "because the line can become certified later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_verification",
        paused_mode="paused_lifecycle_certification",
        paused_decision="pause_lifecycle_certification",
        paused_rationale=(
            "The proactive lifecycle certification pauses the lifecycle because the "
            "line should remain present without immediate certification."
        ),
        archived_previous_decision="archive_lifecycle_verification",
        archived_mode="archived_lifecycle_certification",
        archived_decision="archive_lifecycle_certification",
        archived_rationale=(
            "The proactive lifecycle certification archives the lifecycle because "
            "the line reached a clean ending and should leave certification."
        ),
        retired_previous_decision="retire_lifecycle_verification",
        retired_mode="retired_lifecycle_certification",
        retired_decision="retire_lifecycle_certification",
        retired_rationale=(
            "The proactive lifecycle certification retires the lifecycle because "
            "the line has reached a terminal stop condition."
        ),
    ),
    "confirmation": _LifecycleChainSpec(
        phase="confirmation",
        previous_phase="certification",
        decision_cls=ProactiveLifecycleConfirmationDecision,
        primary_source="certification",
        active_previous_decision="certify_lifecycle_certification",
        active_mode="confirmed_lifecycle_confirmation",
        active_decision="confirm_lifecycle_confirmation",
        active_actionability="confirm",
        base_rationale=(
            "The proactive lifecycle confirmation converts the certification "
            "posture into the final confirmed state that future proactive "
            "confirmation should honor."
        ),
        active_rationale=(
            "The proactive lifecycle confirmation keeps the lifecycle confirmed "
            "because the line should remain explicitly confirmed for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_certification",
        buffered_mode="buffered_lifecycle_confirmation",
        buffered_decision="buffer_lifecycle_confirmation",
        buffered_rationale=(
            "The proactive lifecycle confirmation keeps the lifecycle buffered "
            "because the line can become confirmed later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_certification",
        paused_mode="paused_lifecycle_confirmation",
        paused_decision="pause_lifecycle_confirmation",
        paused_rationale=(
            "The proactive lifecycle confirmation pauses the lifecycle because the "
            "line should remain present without immediate confirmation."
        ),
        archived_previous_decision="archive_lifecycle_certification",
        archived_mode="archived_lifecycle_confirmation",
        archived_decision="archive_lifecycle_confirmation",
        archived_rationale=(
            "The proactive lifecycle confirmation archives the lifecycle because "
            "the line reached a clean ending and should leave confirmation."
        ),
        retired_previous_decision="retire_lifecycle_certification",
        retired_mode="retired_lifecycle_confirmation",
        retired_decision="retire_lifecycle_confirmation",
        retired_rationale=(
            "The proactive lifecycle confirmation retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "ratification": _LifecycleChainSpec(
        phase="ratification",
        previous_phase="confirmation",
        decision_cls=ProactiveLifecycleRatificationDecision,
        primary_source="confirmation",
        active_previous_decision="confirm_lifecycle_confirmation",
        active_mode="ratified_lifecycle_ratification",
        active_decision="ratify_lifecycle_ratification",
        active_actionability="ratify",
        base_rationale=(
            "The proactive lifecycle ratification converts the confirmation posture "
            "into the final ratified state that future proactive ratification "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle ratification keeps the lifecycle ratified "
            "because the line should remain explicitly ratified for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_confirmation",
        buffered_mode="buffered_lifecycle_ratification",
        buffered_decision="buffer_lifecycle_ratification",
        buffered_rationale=(
            "The proactive lifecycle ratification keeps the lifecycle buffered "
            "because the line can become ratified later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_confirmation",
        paused_mode="paused_lifecycle_ratification",
        paused_decision="pause_lifecycle_ratification",
        paused_rationale=(
            "The proactive lifecycle ratification pauses the lifecycle because the "
            "line should remain present without immediate ratification."
        ),
        archived_previous_decision="archive_lifecycle_confirmation",
        archived_mode="archived_lifecycle_ratification",
        archived_decision="archive_lifecycle_ratification",
        archived_rationale=(
            "The proactive lifecycle ratification archives the lifecycle because "
            "the line reached a clean ending and should leave ratification."
        ),
        retired_previous_decision="retire_lifecycle_confirmation",
        retired_mode="retired_lifecycle_ratification",
        retired_decision="retire_lifecycle_ratification",
        retired_rationale=(
            "The proactive lifecycle ratification retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "endorsement": _LifecycleChainSpec(
        phase="endorsement",
        previous_phase="ratification",
        decision_cls=ProactiveLifecycleEndorsementDecision,
        primary_source="ratification",
        active_previous_decision="ratify_lifecycle_ratification",
        active_mode="endorsed_lifecycle_endorsement",
        active_decision="endorse_lifecycle_endorsement",
        active_actionability="endorse",
        base_rationale=(
            "The proactive lifecycle endorsement converts the ratification posture "
            "into the final endorsed state that future proactive endorsement should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle endorsement keeps the lifecycle endorsed "
            "because the line should remain explicitly endorsed for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_ratification",
        buffered_mode="buffered_lifecycle_endorsement",
        buffered_decision="buffer_lifecycle_endorsement",
        buffered_rationale=(
            "The proactive lifecycle endorsement keeps the lifecycle buffered "
            "because the line can become endorsed later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_ratification",
        paused_mode="paused_lifecycle_endorsement",
        paused_decision="pause_lifecycle_endorsement",
        paused_rationale=(
            "The proactive lifecycle endorsement pauses the lifecycle because the "
            "line should remain present without immediate endorsement."
        ),
        archived_previous_decision="archive_lifecycle_ratification",
        archived_mode="archived_lifecycle_endorsement",
        archived_decision="archive_lifecycle_endorsement",
        archived_rationale=(
            "The proactive lifecycle endorsement archives the lifecycle because the "
            "line reached a clean ending and should leave endorsement."
        ),
        retired_previous_decision="retire_lifecycle_ratification",
        retired_mode="retired_lifecycle_endorsement",
        retired_decision="retire_lifecycle_endorsement",
        retired_rationale=(
            "The proactive lifecycle endorsement retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "authorization": _LifecycleChainSpec(
        phase="authorization",
        previous_phase="endorsement",
        decision_cls=ProactiveLifecycleAuthorizationDecision,
        primary_source="endorsement",
        active_previous_decision="endorse_lifecycle_endorsement",
        active_mode="authorized_lifecycle_authorization",
        active_decision="authorize_lifecycle_authorization",
        active_actionability="authorize",
        base_rationale=(
            "The proactive lifecycle authorization converts the endorsement posture "
            "into the final authorized state that future proactive authorization "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle authorization keeps the lifecycle authorized "
            "because the line should remain explicitly authorized for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_endorsement",
        buffered_mode="buffered_lifecycle_authorization",
        buffered_decision="buffer_lifecycle_authorization",
        buffered_rationale=(
            "The proactive lifecycle authorization keeps the lifecycle buffered "
            "because the line can become authorized later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_endorsement",
        paused_mode="paused_lifecycle_authorization",
        paused_decision="pause_lifecycle_authorization",
        paused_rationale=(
            "The proactive lifecycle authorization pauses the lifecycle because the "
            "line should remain present without immediate authorization."
        ),
        archived_previous_decision="archive_lifecycle_endorsement",
        archived_mode="archived_lifecycle_authorization",
        archived_decision="archive_lifecycle_authorization",
        archived_rationale=(
            "The proactive lifecycle authorization archives the lifecycle because "
            "the line reached a clean ending and should leave authorization."
        ),
        retired_previous_decision="retire_lifecycle_endorsement",
        retired_mode="retired_lifecycle_authorization",
        retired_decision="retire_lifecycle_authorization",
        retired_rationale=(
            "The proactive lifecycle authorization retires the lifecycle because "
            "the line has reached a terminal stop condition."
        ),
    ),
    "enactment": _LifecycleChainSpec(
        phase="enactment",
        previous_phase="authorization",
        decision_cls=ProactiveLifecycleEnactmentDecision,
        primary_source="authorization",
        active_previous_decision="authorize_lifecycle_authorization",
        active_mode="enacted_lifecycle_enactment",
        active_decision="enact_lifecycle_enactment",
        active_actionability="enact",
        base_rationale=(
            "The proactive lifecycle enactment converts the authorization posture "
            "into the final enacted state that future proactive enactment should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle enactment keeps the lifecycle enacted because "
            "the line should remain explicitly enacted for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_authorization",
        buffered_mode="buffered_lifecycle_enactment",
        buffered_decision="buffer_lifecycle_enactment",
        buffered_rationale=(
            "The proactive lifecycle enactment keeps the lifecycle buffered because "
            "the line can become enacted later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_authorization",
        paused_mode="paused_lifecycle_enactment",
        paused_decision="pause_lifecycle_enactment",
        paused_rationale=(
            "The proactive lifecycle enactment pauses the lifecycle because the "
            "line should remain present without immediate enactment."
        ),
        archived_previous_decision="archive_lifecycle_authorization",
        archived_mode="archived_lifecycle_enactment",
        archived_decision="archive_lifecycle_enactment",
        archived_rationale=(
            "The proactive lifecycle enactment archives the lifecycle because the "
            "line reached a clean ending and should leave enactment."
        ),
        retired_previous_decision="retire_lifecycle_authorization",
        retired_mode="retired_lifecycle_enactment",
        retired_decision="retire_lifecycle_enactment",
        retired_rationale=(
            "The proactive lifecycle enactment retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "finality": _LifecycleChainSpec(
        phase="finality",
        previous_phase="enactment",
        decision_cls=ProactiveLifecycleFinalityDecision,
        primary_source="enactment",
        active_previous_decision="enact_lifecycle_enactment",
        active_mode="finalized_lifecycle_finality",
        active_decision="finalize_lifecycle_finality",
        active_actionability="finalize",
        base_rationale=(
            "The proactive lifecycle finality converts the enactment posture into "
            "the final finality state that future proactive execution should honor."
        ),
        active_rationale=(
            "The proactive lifecycle finality keeps the lifecycle finalized because "
            "the line should remain explicitly finalized for future proactive "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_enactment",
        buffered_mode="buffered_lifecycle_finality",
        buffered_decision="buffer_lifecycle_finality",
        buffered_rationale=(
            "The proactive lifecycle finality keeps the lifecycle buffered because "
            "the line can become finalized later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_enactment",
        paused_mode="paused_lifecycle_finality",
        paused_decision="pause_lifecycle_finality",
        paused_rationale=(
            "The proactive lifecycle finality pauses the lifecycle because the line "
            "should remain present without immediate finalization."
        ),
        archived_previous_decision="archive_lifecycle_enactment",
        archived_mode="archived_lifecycle_finality",
        archived_decision="archive_lifecycle_finality",
        archived_rationale=(
            "The proactive lifecycle finality archives the lifecycle because the "
            "line reached a clean ending and should leave finality."
        ),
        retired_previous_decision="retire_lifecycle_enactment",
        retired_mode="retired_lifecycle_finality",
        retired_decision="retire_lifecycle_finality",
        retired_rationale=(
            "The proactive lifecycle finality retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "completion": _LifecycleChainSpec(
        phase="completion",
        previous_phase="finality",
        decision_cls=ProactiveLifecycleCompletionDecision,
        primary_source="finality",
        active_previous_decision="finalize_lifecycle_finality",
        active_mode="completed_lifecycle_completion",
        active_decision="complete_lifecycle_completion",
        active_actionability="complete",
        base_rationale=(
            "The proactive lifecycle completion converts the finality posture into "
            "the final completion state that future proactive completion should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle completion keeps the lifecycle completed "
            "because the line should remain explicitly completed for future "
            "proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_finality",
        buffered_mode="buffered_lifecycle_completion",
        buffered_decision="buffer_lifecycle_completion",
        buffered_rationale=(
            "The proactive lifecycle completion keeps the lifecycle buffered "
            "because the line can become completed later, but not yet."
        ),
        paused_previous_decision="pause_lifecycle_finality",
        paused_mode="paused_lifecycle_completion",
        paused_decision="pause_lifecycle_completion",
        paused_rationale=(
            "The proactive lifecycle completion pauses the lifecycle because the "
            "line should remain present without immediate completion."
        ),
        archived_previous_decision="archive_lifecycle_finality",
        archived_mode="archived_lifecycle_completion",
        archived_decision="archive_lifecycle_completion",
        archived_rationale=(
            "The proactive lifecycle completion archives the lifecycle because the "
            "line reached a clean ending and should leave completion."
        ),
        retired_previous_decision="retire_lifecycle_finality",
        retired_mode="retired_lifecycle_completion",
        retired_decision="retire_lifecycle_completion",
        retired_rationale=(
            "The proactive lifecycle completion retires the lifecycle because the "
            "line has reached a terminal stop condition."
        ),
    ),
    "conclusion": _LifecycleChainSpec(
        phase="conclusion",
        previous_phase="completion",
        decision_cls=ProactiveLifecycleConclusionDecision,
        primary_source="completion",
        active_previous_decision="complete_lifecycle_completion",
        active_mode="completed_lifecycle_conclusion",
        active_decision="complete_lifecycle_conclusion",
        active_actionability="complete",
        base_rationale=(
            "The proactive lifecycle conclusion converts the completion posture "
            "into the final conclusion state that future proactive scheduling "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle conclusion keeps the lifecycle completed "
            "because the line can remain present without extra queue suppression."
        ),
        buffered_previous_decision="buffer_lifecycle_completion",
        buffered_mode="buffered_lifecycle_conclusion",
        buffered_decision="buffer_lifecycle_conclusion",
        buffered_rationale=(
            "The proactive lifecycle conclusion buffers the lifecycle because the "
            "line should stay present but not immediately active."
        ),
        paused_previous_decision="pause_lifecycle_completion",
        paused_mode="paused_lifecycle_conclusion",
        paused_decision="pause_lifecycle_conclusion",
        paused_rationale=(
            "The proactive lifecycle conclusion pauses the lifecycle because the "
            "line should remain open without immediate proactive continuation."
        ),
        archived_previous_decision="archive_lifecycle_completion",
        archived_mode="archived_lifecycle_conclusion",
        archived_decision="archive_lifecycle_conclusion",
        archived_rationale=(
            "The proactive lifecycle conclusion archives the lifecycle because the "
            "line reached a clean ending and should leave the active queue."
        ),
        retired_previous_decision="retire_lifecycle_completion",
        retired_mode="retired_lifecycle_conclusion",
        retired_decision="retire_lifecycle_conclusion",
        retired_rationale=(
            "The proactive lifecycle conclusion retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "disposition": _LifecycleChainSpec(
        phase="disposition",
        previous_phase="conclusion",
        decision_cls=ProactiveLifecycleDispositionDecision,
        primary_source="conclusion",
        active_previous_decision="complete_lifecycle_conclusion",
        active_mode="completed_lifecycle_disposition",
        active_decision="complete_lifecycle_disposition",
        active_actionability="complete",
        base_rationale=(
            "The proactive lifecycle disposition converts the conclusion posture "
            "into the final disposition state that future proactive scheduling "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle disposition keeps the lifecycle complete "
            "because the line can remain present without extra queue suppression."
        ),
        buffered_previous_decision="buffer_lifecycle_conclusion",
        buffered_mode="buffered_lifecycle_disposition",
        buffered_decision="buffer_lifecycle_disposition",
        buffered_rationale=(
            "The proactive lifecycle disposition buffers the lifecycle because the "
            "line should stay present but not immediately active."
        ),
        paused_previous_decision="pause_lifecycle_conclusion",
        paused_mode="paused_lifecycle_disposition",
        paused_decision="pause_lifecycle_disposition",
        paused_rationale=(
            "The proactive lifecycle disposition pauses the lifecycle because the "
            "line should remain open without immediate proactive continuation."
        ),
        archived_previous_decision="archive_lifecycle_conclusion",
        archived_mode="archived_lifecycle_disposition",
        archived_decision="archive_lifecycle_disposition",
        archived_rationale=(
            "The proactive lifecycle disposition archives the lifecycle because the "
            "line reached a clean ending and should leave the active queue."
        ),
        retired_previous_decision="retire_lifecycle_conclusion",
        retired_mode="retired_lifecycle_disposition",
        retired_decision="retire_lifecycle_disposition",
        retired_rationale=(
            "The proactive lifecycle disposition retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "standing": _LifecycleChainSpec(
        phase="standing",
        previous_phase="disposition",
        decision_cls=ProactiveLifecycleStandingDecision,
        primary_source="disposition",
        active_previous_decision="complete_lifecycle_disposition",
        active_mode="standing_lifecycle_standing",
        active_decision="keep_lifecycle_standing",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle standing converts the disposition posture into "
            "the final standing state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle standing keeps the lifecycle standing because "
            "the line can remain present without extra queue suppression."
        ),
        buffered_previous_decision="buffer_lifecycle_disposition",
        buffered_mode="buffered_lifecycle_standing",
        buffered_decision="buffer_lifecycle_standing",
        buffered_rationale=(
            "The proactive lifecycle standing buffers the lifecycle because the "
            "line should stay present but not immediately active."
        ),
        paused_previous_decision="pause_lifecycle_disposition",
        paused_mode="paused_lifecycle_standing",
        paused_decision="pause_lifecycle_standing",
        paused_rationale=(
            "The proactive lifecycle standing pauses the lifecycle because the line "
            "should remain open without immediate proactive continuation."
        ),
        archived_previous_decision="archive_lifecycle_disposition",
        archived_mode="archived_lifecycle_standing",
        archived_decision="archive_lifecycle_standing",
        archived_rationale=(
            "The proactive lifecycle standing archives the lifecycle because the "
            "line reached a clean ending and should leave the active queue."
        ),
        retired_previous_decision="retire_lifecycle_disposition",
        retired_mode="retired_lifecycle_standing",
        retired_decision="retire_lifecycle_standing",
        retired_rationale=(
            "The proactive lifecycle standing retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "residency": _LifecycleChainSpec(
        phase="residency",
        previous_phase="standing",
        decision_cls=ProactiveLifecycleResidencyDecision,
        primary_source="standing",
        active_previous_decision="keep_lifecycle_standing",
        active_mode="resident_lifecycle_residency",
        active_decision="keep_lifecycle_residency",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle residency converts the standing posture into "
            "the final residency state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle residency keeps the lifecycle resident because "
            "the line should remain present for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_standing",
        buffered_mode="buffered_lifecycle_residency",
        buffered_decision="buffer_lifecycle_residency",
        buffered_rationale=(
            "The proactive lifecycle residency buffers the lifecycle because the "
            "line should stay present but not immediately active."
        ),
        paused_previous_decision="pause_lifecycle_standing",
        paused_mode="paused_lifecycle_residency",
        paused_decision="pause_lifecycle_residency",
        paused_rationale=(
            "The proactive lifecycle residency pauses the lifecycle because the "
            "line should preserve user space without immediate proactive "
            "continuation."
        ),
        archived_previous_decision="archive_lifecycle_standing",
        archived_mode="archived_lifecycle_residency",
        archived_decision="archive_lifecycle_residency",
        archived_rationale=(
            "The proactive lifecycle residency archives the lifecycle because the "
            "line reached a clean ending and should leave active residency."
        ),
        retired_previous_decision="retire_lifecycle_standing",
        retired_mode="retired_lifecycle_residency",
        retired_decision="retire_lifecycle_residency",
        retired_rationale=(
            "The proactive lifecycle residency retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "tenure": _LifecycleChainSpec(
        phase="tenure",
        previous_phase="residency",
        decision_cls=ProactiveLifecycleTenureDecision,
        primary_source="residency",
        active_previous_decision="keep_lifecycle_residency",
        active_mode="tenured_lifecycle_tenure",
        active_decision="keep_lifecycle_tenure",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle tenure converts the residency posture into the "
            "final tenure state that future proactive scheduling should honor."
        ),
        active_rationale=(
            "The proactive lifecycle tenure keeps the lifecycle tenured because the "
            "line should remain durably available for future proactive return."
        ),
        buffered_previous_decision="buffer_lifecycle_residency",
        buffered_mode="buffered_lifecycle_tenure",
        buffered_decision="buffer_lifecycle_tenure",
        buffered_rationale=(
            "The proactive lifecycle tenure buffers the lifecycle because the line "
            "should stay durably present without immediate activity."
        ),
        paused_previous_decision="pause_lifecycle_residency",
        paused_mode="paused_lifecycle_tenure",
        paused_decision="pause_lifecycle_tenure",
        paused_rationale=(
            "The proactive lifecycle tenure pauses the lifecycle because the line "
            "should preserve durable user space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_residency",
        archived_mode="archived_lifecycle_tenure",
        archived_decision="archive_lifecycle_tenure",
        archived_rationale=(
            "The proactive lifecycle tenure archives the lifecycle because the line "
            "reached a clean ending and should leave durable availability."
        ),
        retired_previous_decision="retire_lifecycle_residency",
        retired_mode="retired_lifecycle_tenure",
        retired_decision="retire_lifecycle_tenure",
        retired_rationale=(
            "The proactive lifecycle tenure retires the lifecycle because the line "
            "reached a terminal stop condition."
        ),
    ),
    "persistence": _LifecycleChainSpec(
        phase="persistence",
        previous_phase="tenure",
        decision_cls=ProactiveLifecyclePersistenceDecision,
        primary_source="tenure",
        active_previous_decision="keep_lifecycle_tenure",
        active_mode="persistent_lifecycle_persistence",
        active_decision="keep_lifecycle_persistence",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle persistence converts the tenure posture into "
            "the final persistence state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle persistence keeps the lifecycle persistent "
            "because the line should remain reliably present for future proactive "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_tenure",
        buffered_mode="buffered_lifecycle_persistence",
        buffered_decision="buffer_lifecycle_persistence",
        buffered_rationale=(
            "The proactive lifecycle persistence buffers the lifecycle because the "
            "line should stay reliably present without immediate activity."
        ),
        paused_previous_decision="pause_lifecycle_tenure",
        paused_mode="paused_lifecycle_persistence",
        paused_decision="pause_lifecycle_persistence",
        paused_rationale=(
            "The proactive lifecycle persistence pauses the lifecycle because the "
            "line should preserve long-lived user space without immediate "
            "continuation."
        ),
        archived_previous_decision="archive_lifecycle_tenure",
        archived_mode="archived_lifecycle_persistence",
        archived_decision="archive_lifecycle_persistence",
        archived_rationale=(
            "The proactive lifecycle persistence archives the lifecycle because the "
            "line reached a clean ending and should leave persistent availability."
        ),
        retired_previous_decision="retire_lifecycle_tenure",
        retired_mode="retired_lifecycle_persistence",
        retired_decision="retire_lifecycle_persistence",
        retired_rationale=(
            "The proactive lifecycle persistence retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "durability": _LifecycleChainSpec(
        phase="durability",
        previous_phase="persistence",
        decision_cls=ProactiveLifecycleDurabilityDecision,
        primary_source="persistence",
        active_previous_decision="keep_lifecycle_persistence",
        active_mode="durable_lifecycle_durability",
        active_decision="keep_lifecycle_durability",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle durability converts the persistence posture "
            "into the final durable state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle durability keeps the lifecycle durable because "
            "the line should remain long-lived and steadily available for future "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_persistence",
        buffered_mode="buffered_lifecycle_durability",
        buffered_decision="buffer_lifecycle_durability",
        buffered_rationale=(
            "The proactive lifecycle durability buffers the lifecycle because the "
            "line should remain durable while staying out of immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_persistence",
        paused_mode="paused_lifecycle_durability",
        paused_decision="pause_lifecycle_durability",
        paused_rationale=(
            "The proactive lifecycle durability pauses the lifecycle because the "
            "line should preserve durable space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_persistence",
        archived_mode="archived_lifecycle_durability",
        archived_decision="archive_lifecycle_durability",
        archived_rationale=(
            "The proactive lifecycle durability archives the lifecycle because the "
            "line reached a clean durable ending."
        ),
        retired_previous_decision="retire_lifecycle_persistence",
        retired_mode="retired_lifecycle_durability",
        retired_decision="retire_lifecycle_durability",
        retired_rationale=(
            "The proactive lifecycle durability retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "longevity": _LifecycleChainSpec(
        phase="longevity",
        previous_phase="durability",
        decision_cls=ProactiveLifecycleLongevityDecision,
        primary_source="durability",
        active_previous_decision="keep_lifecycle_durability",
        active_mode="enduring_lifecycle_longevity",
        active_decision="keep_lifecycle_longevity",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle longevity converts the durability posture into "
            "the final long-lived state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle longevity keeps the lifecycle enduring because "
            "the line should stay available over a longer horizon for future "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_durability",
        buffered_mode="buffered_lifecycle_longevity",
        buffered_decision="buffer_lifecycle_longevity",
        buffered_rationale=(
            "The proactive lifecycle longevity buffers the lifecycle because the "
            "line should remain long-lived without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_durability",
        paused_mode="paused_lifecycle_longevity",
        paused_decision="pause_lifecycle_longevity",
        paused_rationale=(
            "The proactive lifecycle longevity pauses the lifecycle because the "
            "line should preserve long-horizon space without immediate "
            "continuation."
        ),
        archived_previous_decision="archive_lifecycle_durability",
        archived_mode="archived_lifecycle_longevity",
        archived_decision="archive_lifecycle_longevity",
        archived_rationale=(
            "The proactive lifecycle longevity archives the lifecycle because the "
            "line reached a clean long-horizon ending."
        ),
        retired_previous_decision="retire_lifecycle_durability",
        retired_mode="retired_lifecycle_longevity",
        retired_decision="retire_lifecycle_longevity",
        retired_rationale=(
            "The proactive lifecycle longevity retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "legacy": _LifecycleChainSpec(
        phase="legacy",
        previous_phase="longevity",
        decision_cls=ProactiveLifecycleLegacyDecision,
        primary_source="longevity",
        active_previous_decision="keep_lifecycle_longevity",
        active_mode="lasting_lifecycle_legacy",
        active_decision="keep_lifecycle_legacy",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle legacy converts the longevity posture into the "
            "final long-tail legacy state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle legacy keeps the lifecycle lasting because the "
            "line should remain as an enduring long-tail return path."
        ),
        buffered_previous_decision="buffer_lifecycle_longevity",
        buffered_mode="buffered_lifecycle_legacy",
        buffered_decision="buffer_lifecycle_legacy",
        buffered_rationale=(
            "The proactive lifecycle legacy buffers the lifecycle because the line "
            "should keep its legacy value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_longevity",
        paused_mode="paused_lifecycle_legacy",
        paused_decision="pause_lifecycle_legacy",
        paused_rationale=(
            "The proactive lifecycle legacy pauses the lifecycle because the line "
            "should preserve legacy space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_longevity",
        archived_mode="archived_lifecycle_legacy",
        archived_decision="archive_lifecycle_legacy",
        archived_rationale=(
            "The proactive lifecycle legacy archives the lifecycle because the line "
            "reached a clean long-tail ending."
        ),
        retired_previous_decision="retire_lifecycle_longevity",
        retired_mode="retired_lifecycle_legacy",
        retired_decision="retire_lifecycle_legacy",
        retired_rationale=(
            "The proactive lifecycle legacy retires the lifecycle because the line "
            "reached a terminal stop condition."
        ),
    ),
    "heritage": _LifecycleChainSpec(
        phase="heritage",
        previous_phase="legacy",
        decision_cls=ProactiveLifecycleHeritageDecision,
        primary_source="legacy",
        active_previous_decision="keep_lifecycle_legacy",
        active_mode="preserved_lifecycle_heritage",
        active_decision="keep_lifecycle_heritage",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle heritage converts the legacy posture into the "
            "final preserved heritage state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle heritage keeps the lifecycle preserved because "
            "the line should remain as a durable heritage path for future return."
        ),
        buffered_previous_decision="buffer_lifecycle_legacy",
        buffered_mode="buffered_lifecycle_heritage",
        buffered_decision="buffer_lifecycle_heritage",
        buffered_rationale=(
            "The proactive lifecycle heritage buffers the lifecycle because the "
            "line should preserve its heritage value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_legacy",
        paused_mode="paused_lifecycle_heritage",
        paused_decision="pause_lifecycle_heritage",
        paused_rationale=(
            "The proactive lifecycle heritage pauses the lifecycle because the line "
            "should preserve heritage space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_legacy",
        archived_mode="archived_lifecycle_heritage",
        archived_decision="archive_lifecycle_heritage",
        archived_rationale=(
            "The proactive lifecycle heritage archives the lifecycle because the "
            "line reached a clean preserved ending."
        ),
        retired_previous_decision="retire_lifecycle_legacy",
        retired_mode="retired_lifecycle_heritage",
        retired_decision="retire_lifecycle_heritage",
        retired_rationale=(
            "The proactive lifecycle heritage retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "lineage": _LifecycleChainSpec(
        phase="lineage",
        previous_phase="heritage",
        decision_cls=ProactiveLifecycleLineageDecision,
        primary_source="heritage",
        active_previous_decision="keep_lifecycle_heritage",
        active_mode="preserved_lifecycle_lineage",
        active_decision="keep_lifecycle_lineage",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle lineage converts the heritage posture into the "
            "final preserved lineage state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle lineage keeps the lifecycle preserved because "
            "the line should remain as a durable lineage path for future return."
        ),
        buffered_previous_decision="buffer_lifecycle_heritage",
        buffered_mode="buffered_lifecycle_lineage",
        buffered_decision="buffer_lifecycle_lineage",
        buffered_rationale=(
            "The proactive lifecycle lineage buffers the lifecycle because the line "
            "should preserve its lineage value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_heritage",
        paused_mode="paused_lifecycle_lineage",
        paused_decision="pause_lifecycle_lineage",
        paused_rationale=(
            "The proactive lifecycle lineage pauses the lifecycle because the line "
            "should preserve lineage space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_heritage",
        archived_mode="archived_lifecycle_lineage",
        archived_decision="archive_lifecycle_lineage",
        archived_rationale=(
            "The proactive lifecycle lineage archives the lifecycle because the "
            "line reached a clean preserved ending."
        ),
        retired_previous_decision="retire_lifecycle_heritage",
        retired_mode="retired_lifecycle_lineage",
        retired_decision="retire_lifecycle_lineage",
        retired_rationale=(
            "The proactive lifecycle lineage retires the lifecycle because the line "
            "reached a terminal stop condition."
        ),
    ),
    "ancestry": _LifecycleChainSpec(
        phase="ancestry",
        previous_phase="lineage",
        decision_cls=ProactiveLifecycleAncestryDecision,
        primary_source="lineage",
        active_previous_decision="keep_lifecycle_lineage",
        active_mode="preserved_lifecycle_ancestry",
        active_decision="keep_lifecycle_ancestry",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle ancestry converts the lineage posture into the "
            "final preserved ancestry state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle ancestry keeps the lifecycle preserved because "
            "the line should remain as a durable ancestry path for future return."
        ),
        buffered_previous_decision="buffer_lifecycle_lineage",
        buffered_mode="buffered_lifecycle_ancestry",
        buffered_decision="buffer_lifecycle_ancestry",
        buffered_rationale=(
            "The proactive lifecycle ancestry buffers the lifecycle because the "
            "line should preserve its ancestry value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_lineage",
        paused_mode="paused_lifecycle_ancestry",
        paused_decision="pause_lifecycle_ancestry",
        paused_rationale=(
            "The proactive lifecycle ancestry pauses the lifecycle because the line "
            "should preserve ancestry space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_lineage",
        archived_mode="archived_lifecycle_ancestry",
        archived_decision="archive_lifecycle_ancestry",
        archived_rationale=(
            "The proactive lifecycle ancestry archives the lifecycle because the "
            "line reached a clean preserved ending."
        ),
        retired_previous_decision="retire_lifecycle_lineage",
        retired_mode="retired_lifecycle_ancestry",
        retired_decision="retire_lifecycle_ancestry",
        retired_rationale=(
            "The proactive lifecycle ancestry retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "provenance": _LifecycleChainSpec(
        phase="provenance",
        previous_phase="ancestry",
        decision_cls=ProactiveLifecycleProvenanceDecision,
        primary_source="ancestry",
        active_previous_decision="keep_lifecycle_ancestry",
        active_mode="preserved_lifecycle_provenance",
        active_decision="keep_lifecycle_provenance",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle provenance converts the ancestry posture into "
            "the final preserved provenance state that future proactive scheduling "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle provenance keeps the lifecycle preserved "
            "because the line should remain as a durable provenance path for future "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_ancestry",
        buffered_mode="buffered_lifecycle_provenance",
        buffered_decision="buffer_lifecycle_provenance",
        buffered_rationale=(
            "The proactive lifecycle provenance buffers the lifecycle because the "
            "line should preserve its provenance value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_ancestry",
        paused_mode="paused_lifecycle_provenance",
        paused_decision="pause_lifecycle_provenance",
        paused_rationale=(
            "The proactive lifecycle provenance pauses the lifecycle because the "
            "line should preserve provenance space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_ancestry",
        archived_mode="archived_lifecycle_provenance",
        archived_decision="archive_lifecycle_provenance",
        archived_rationale=(
            "The proactive lifecycle provenance archives the lifecycle because the "
            "line reached a clean preserved ending."
        ),
        retired_previous_decision="retire_lifecycle_ancestry",
        retired_mode="retired_lifecycle_provenance",
        retired_decision="retire_lifecycle_provenance",
        retired_rationale=(
            "The proactive lifecycle provenance retires the lifecycle because the "
            "line reached a terminal stop condition."
        ),
    ),
    "origin": _LifecycleChainSpec(
        phase="origin",
        previous_phase="provenance",
        decision_cls=ProactiveLifecycleOriginDecision,
        primary_source="provenance",
        active_previous_decision="keep_lifecycle_provenance",
        active_mode="preserved_lifecycle_origin",
        active_decision="keep_lifecycle_origin",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle origin converts the provenance posture into "
            "the final preserved origin state that future proactive scheduling "
            "should honor."
        ),
        active_rationale=(
            "The proactive lifecycle origin keeps the lifecycle preserved because "
            "the line should remain available as a stable origin point for future "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_provenance",
        buffered_mode="buffered_lifecycle_origin",
        buffered_decision="buffer_lifecycle_origin",
        buffered_rationale=(
            "The proactive lifecycle origin buffers the lifecycle because the line "
            "should preserve its origin value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_provenance",
        paused_mode="paused_lifecycle_origin",
        paused_decision="pause_lifecycle_origin",
        paused_rationale=(
            "The proactive lifecycle origin pauses the lifecycle because the line "
            "should preserve origin space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_provenance",
        archived_mode="archived_lifecycle_origin",
        archived_decision="archive_lifecycle_origin",
        archived_rationale=(
            "The proactive lifecycle origin archives the lifecycle because the line "
            "reached a clean preserved ending."
        ),
        retired_previous_decision="retire_lifecycle_provenance",
        retired_mode="retired_lifecycle_origin",
        retired_decision="retire_lifecycle_origin",
        retired_rationale=(
            "The proactive lifecycle origin retires the lifecycle because the line "
            "reached a terminal stop condition."
        ),
    ),
    "root": _LifecycleChainSpec(
        phase="root",
        previous_phase="origin",
        decision_cls=ProactiveLifecycleRootDecision,
        primary_source="origin",
        active_previous_decision="keep_lifecycle_origin",
        active_mode="preserved_lifecycle_root",
        active_decision="keep_lifecycle_root",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle root converts the origin posture into the "
            "final preserved root state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle root keeps the lifecycle preserved because the "
            "line should remain available as a stable root point for future return."
        ),
        buffered_previous_decision="buffer_lifecycle_origin",
        buffered_mode="buffered_lifecycle_root",
        buffered_decision="buffer_lifecycle_root",
        buffered_rationale=(
            "The proactive lifecycle root buffers the lifecycle because the line "
            "should preserve its root value without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_origin",
        paused_mode="paused_lifecycle_root",
        paused_decision="pause_lifecycle_root",
        paused_rationale=(
            "The proactive lifecycle root pauses the lifecycle because the line "
            "should preserve root space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_origin",
        archived_mode="archived_lifecycle_root",
        archived_decision="archive_lifecycle_root",
        archived_rationale=(
            "The proactive lifecycle root archives the lifecycle because the line "
            "reached a clean preserved ending."
        ),
        retired_previous_decision="retire_lifecycle_origin",
        retired_mode="retired_lifecycle_root",
        retired_decision="retire_lifecycle_root",
        retired_rationale=(
            "The proactive lifecycle root retires the lifecycle because the line "
            "reached a terminal stop condition."
        ),
    ),
    "foundation": _LifecycleChainSpec(
        phase="foundation",
        previous_phase="root",
        decision_cls=ProactiveLifecycleFoundationDecision,
        primary_source="root",
        active_previous_decision="keep_lifecycle_root",
        active_mode="preserved_lifecycle_foundation",
        active_decision="keep_lifecycle_foundation",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle foundation converts the root posture into the "
            "final foundational state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle foundation keeps the lifecycle preserved "
            "because the line should remain available as a stable foundation for "
            "future return."
        ),
        buffered_previous_decision="buffer_lifecycle_root",
        buffered_mode="buffered_lifecycle_foundation",
        buffered_decision="buffer_lifecycle_foundation",
        buffered_rationale=(
            "The proactive lifecycle foundation buffers the lifecycle because the "
            "line should preserve its foundation without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_root",
        paused_mode="paused_lifecycle_foundation",
        paused_decision="pause_lifecycle_foundation",
        paused_rationale=(
            "The proactive lifecycle foundation pauses the lifecycle because the "
            "line should preserve foundational space without immediate "
            "continuation."
        ),
        archived_previous_decision="archive_lifecycle_root",
        archived_mode="archived_lifecycle_foundation",
        archived_decision="archive_lifecycle_foundation",
        archived_rationale=(
            "The proactive lifecycle foundation archives the lifecycle because the "
            "line reached a clean foundational ending."
        ),
        retired_previous_decision="retire_lifecycle_root",
        retired_mode="retired_lifecycle_foundation",
        retired_decision="retire_lifecycle_foundation",
        retired_rationale=(
            "The proactive lifecycle foundation retires the lifecycle because the "
            "line reached a terminal foundational stop condition."
        ),
    ),
    "bedrock": _LifecycleChainSpec(
        phase="bedrock",
        previous_phase="foundation",
        decision_cls=ProactiveLifecycleBedrockDecision,
        primary_source="foundation",
        active_previous_decision="keep_lifecycle_foundation",
        active_mode="preserved_lifecycle_bedrock",
        active_decision="keep_lifecycle_bedrock",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle bedrock converts the foundation posture into "
            "the final bedrock state that future proactive scheduling should honor."
        ),
        active_rationale=(
            "The proactive lifecycle bedrock keeps the lifecycle preserved because "
            "the line should remain available as a stable bedrock for future "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_foundation",
        buffered_mode="buffered_lifecycle_bedrock",
        buffered_decision="buffer_lifecycle_bedrock",
        buffered_rationale=(
            "The proactive lifecycle bedrock buffers the lifecycle because the line "
            "should preserve its bedrock without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_foundation",
        paused_mode="paused_lifecycle_bedrock",
        paused_decision="pause_lifecycle_bedrock",
        paused_rationale=(
            "The proactive lifecycle bedrock pauses the lifecycle because the line "
            "should preserve bedrock space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_foundation",
        archived_mode="archived_lifecycle_bedrock",
        archived_decision="archive_lifecycle_bedrock",
        archived_rationale=(
            "The proactive lifecycle bedrock archives the lifecycle because the "
            "line reached a clean bedrock ending."
        ),
        retired_previous_decision="retire_lifecycle_foundation",
        retired_mode="retired_lifecycle_bedrock",
        retired_decision="retire_lifecycle_bedrock",
        retired_rationale=(
            "The proactive lifecycle bedrock retires the lifecycle because the line "
            "reached a terminal bedrock stop condition."
        ),
    ),
    "substrate": _LifecycleChainSpec(
        phase="substrate",
        previous_phase="bedrock",
        decision_cls=ProactiveLifecycleSubstrateDecision,
        primary_source="bedrock",
        active_previous_decision="keep_lifecycle_bedrock",
        active_mode="preserved_lifecycle_substrate",
        active_decision="keep_lifecycle_substrate",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle substrate converts the bedrock posture into "
            "the final substrate state that future proactive scheduling should "
            "honor."
        ),
        active_rationale=(
            "The proactive lifecycle substrate keeps the lifecycle preserved "
            "because the line should remain available as a stable substrate for "
            "future return."
        ),
        buffered_previous_decision="buffer_lifecycle_bedrock",
        buffered_mode="buffered_lifecycle_substrate",
        buffered_decision="buffer_lifecycle_substrate",
        buffered_rationale=(
            "The proactive lifecycle substrate buffers the lifecycle because the "
            "line should preserve its substrate without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_bedrock",
        paused_mode="paused_lifecycle_substrate",
        paused_decision="pause_lifecycle_substrate",
        paused_rationale=(
            "The proactive lifecycle substrate pauses the lifecycle because the "
            "line should preserve substrate space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_bedrock",
        archived_mode="archived_lifecycle_substrate",
        archived_decision="archive_lifecycle_substrate",
        archived_rationale=(
            "The proactive lifecycle substrate archives the lifecycle because the "
            "line reached a clean substrate ending."
        ),
        retired_previous_decision="retire_lifecycle_bedrock",
        retired_mode="retired_lifecycle_substrate",
        retired_decision="retire_lifecycle_substrate",
        retired_rationale=(
            "The proactive lifecycle substrate retires the lifecycle because the "
            "line reached a terminal substrate stop condition."
        ),
    ),
    "stratum": _LifecycleChainSpec(
        phase="stratum",
        previous_phase="substrate",
        decision_cls=ProactiveLifecycleStratumDecision,
        primary_source="substrate",
        active_previous_decision="keep_lifecycle_substrate",
        active_mode="preserved_lifecycle_stratum",
        active_decision="keep_lifecycle_stratum",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle stratum converts the substrate posture into "
            "the final stratum state that future proactive scheduling should honor."
        ),
        active_rationale=(
            "The proactive lifecycle stratum keeps the lifecycle preserved because "
            "the line should remain available as a stable stratum for future "
            "return."
        ),
        buffered_previous_decision="buffer_lifecycle_substrate",
        buffered_mode="buffered_lifecycle_stratum",
        buffered_decision="buffer_lifecycle_stratum",
        buffered_rationale=(
            "The proactive lifecycle stratum buffers the lifecycle because the line "
            "should preserve its stratum without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_substrate",
        paused_mode="paused_lifecycle_stratum",
        paused_decision="pause_lifecycle_stratum",
        paused_rationale=(
            "The proactive lifecycle stratum pauses the lifecycle because the line "
            "should preserve stratum space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_substrate",
        archived_mode="archived_lifecycle_stratum",
        archived_decision="archive_lifecycle_stratum",
        archived_rationale=(
            "The proactive lifecycle stratum archives the lifecycle because the "
            "line reached a clean stratum ending."
        ),
        retired_previous_decision="retire_lifecycle_substrate",
        retired_mode="retired_lifecycle_stratum",
        retired_decision="retire_lifecycle_stratum",
        retired_rationale=(
            "The proactive lifecycle stratum retires the lifecycle because the line "
            "reached a terminal stratum stop condition."
        ),
    ),
    "layer": _LifecycleChainSpec(
        phase="layer",
        previous_phase="stratum",
        decision_cls=ProactiveLifecycleLayerDecision,
        primary_source="stratum",
        active_previous_decision="keep_lifecycle_stratum",
        active_mode="preserved_lifecycle_layer",
        active_decision="keep_lifecycle_layer",
        active_actionability="keep",
        base_rationale=(
            "The proactive lifecycle layer converts the stratum posture into the "
            "final layer state that future proactive scheduling should honor."
        ),
        active_rationale=(
            "The proactive lifecycle layer keeps the lifecycle preserved because "
            "the line should remain available as a stable layer for future return."
        ),
        buffered_previous_decision="buffer_lifecycle_stratum",
        buffered_mode="buffered_lifecycle_layer",
        buffered_decision="buffer_lifecycle_layer",
        buffered_rationale=(
            "The proactive lifecycle layer buffers the lifecycle because the line "
            "should preserve its layer without immediate motion."
        ),
        paused_previous_decision="pause_lifecycle_stratum",
        paused_mode="paused_lifecycle_layer",
        paused_decision="pause_lifecycle_layer",
        paused_rationale=(
            "The proactive lifecycle layer pauses the lifecycle because the line "
            "should preserve layer space without immediate continuation."
        ),
        archived_previous_decision="archive_lifecycle_stratum",
        archived_mode="archived_lifecycle_layer",
        archived_decision="archive_lifecycle_layer",
        archived_rationale=(
            "The proactive lifecycle layer archives the lifecycle because the line "
            "reached a clean layer ending."
        ),
        retired_previous_decision="retire_lifecycle_stratum",
        retired_mode="retired_lifecycle_layer",
        retired_decision="retire_lifecycle_layer",
        retired_rationale=(
            "The proactive lifecycle layer retires the lifecycle because the line "
            "reached a terminal layer stop condition."
        ),
    ),
}


def build_proactive_lifecycle_retention_decision(
    *,
    lifecycle_availability_decision: ProactiveLifecycleAvailabilityDecision,
) -> ProactiveLifecycleRetentionDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_availability_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["retention"],
    )


def build_proactive_lifecycle_eligibility_decision(
    *,
    lifecycle_retention_decision: ProactiveLifecycleRetentionDecision,
) -> ProactiveLifecycleEligibilityDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_retention_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["eligibility"],
    )


def build_proactive_lifecycle_candidate_decision(
    *,
    lifecycle_eligibility_decision: ProactiveLifecycleEligibilityDecision,
) -> ProactiveLifecycleCandidateDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_eligibility_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["candidate"],
    )


def build_proactive_lifecycle_selectability_decision(
    *,
    lifecycle_candidate_decision: ProactiveLifecycleCandidateDecision,
) -> ProactiveLifecycleSelectabilityDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_candidate_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["selectability"],
    )


def build_proactive_lifecycle_reentry_decision(
    *,
    lifecycle_selectability_decision: ProactiveLifecycleSelectabilityDecision,
) -> ProactiveLifecycleReentryDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_selectability_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["reentry"],
    )


def build_proactive_lifecycle_reactivation_decision(
    *,
    lifecycle_reentry_decision: ProactiveLifecycleReentryDecision,
) -> ProactiveLifecycleReactivationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_reentry_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["reactivation"],
    )


def build_proactive_lifecycle_resumption_decision(
    *,
    lifecycle_reactivation_decision: ProactiveLifecycleReactivationDecision,
) -> ProactiveLifecycleResumptionDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_reactivation_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["resumption"],
    )


def build_proactive_lifecycle_readiness_decision(
    *,
    lifecycle_resumption_decision: ProactiveLifecycleResumptionDecision,
) -> ProactiveLifecycleReadinessDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_resumption_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["readiness"],
    )


def build_proactive_lifecycle_arming_decision(
    *,
    lifecycle_readiness_decision: ProactiveLifecycleReadinessDecision,
) -> ProactiveLifecycleArmingDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_readiness_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["arming"],
    )


def build_proactive_lifecycle_trigger_decision(
    *,
    lifecycle_arming_decision: ProactiveLifecycleArmingDecision,
) -> ProactiveLifecycleTriggerDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_arming_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["trigger"],
    )


def build_proactive_lifecycle_launch_decision(
    *,
    lifecycle_trigger_decision: ProactiveLifecycleTriggerDecision,
) -> ProactiveLifecycleLaunchDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_trigger_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["launch"],
    )


def build_proactive_lifecycle_handoff_decision(
    *,
    lifecycle_launch_decision: ProactiveLifecycleLaunchDecision,
) -> ProactiveLifecycleHandoffDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_launch_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["handoff"],
    )


def build_proactive_lifecycle_continuation_decision(
    *,
    lifecycle_handoff_decision: ProactiveLifecycleHandoffDecision,
) -> ProactiveLifecycleContinuationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_handoff_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["continuation"],
    )


def build_proactive_lifecycle_sustainment_decision(
    *,
    lifecycle_continuation_decision: ProactiveLifecycleContinuationDecision,
) -> ProactiveLifecycleSustainmentDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_continuation_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["sustainment"],
    )


def build_proactive_lifecycle_stewardship_decision(
    *,
    lifecycle_sustainment_decision: ProactiveLifecycleSustainmentDecision,
) -> ProactiveLifecycleStewardshipDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_sustainment_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["stewardship"],
    )


def build_proactive_lifecycle_guardianship_decision(
    *,
    lifecycle_stewardship_decision: ProactiveLifecycleStewardshipDecision,
) -> ProactiveLifecycleGuardianshipDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_stewardship_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["guardianship"],
    )


def build_proactive_lifecycle_oversight_decision(
    *,
    lifecycle_guardianship_decision: ProactiveLifecycleGuardianshipDecision,
) -> ProactiveLifecycleOversightDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_guardianship_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["oversight"],
    )


def build_proactive_lifecycle_assurance_decision(
    *,
    lifecycle_oversight_decision: ProactiveLifecycleOversightDecision,
) -> ProactiveLifecycleAssuranceDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_oversight_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["assurance"],
    )


def build_proactive_lifecycle_attestation_decision(
    *,
    lifecycle_assurance_decision: ProactiveLifecycleAssuranceDecision,
) -> ProactiveLifecycleAttestationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_assurance_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["attestation"],
    )


def build_proactive_lifecycle_verification_decision(
    *,
    lifecycle_attestation_decision: ProactiveLifecycleAttestationDecision,
) -> ProactiveLifecycleVerificationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_attestation_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["verification"],
    )


def build_proactive_lifecycle_certification_decision(
    *,
    lifecycle_verification_decision: ProactiveLifecycleVerificationDecision,
) -> ProactiveLifecycleCertificationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_verification_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["certification"],
    )


def build_proactive_lifecycle_confirmation_decision(
    *,
    lifecycle_certification_decision: ProactiveLifecycleCertificationDecision,
) -> ProactiveLifecycleConfirmationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_certification_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["confirmation"],
    )


def build_proactive_lifecycle_ratification_decision(
    *,
    lifecycle_confirmation_decision: ProactiveLifecycleConfirmationDecision,
) -> ProactiveLifecycleRatificationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_confirmation_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["ratification"],
    )


def build_proactive_lifecycle_endorsement_decision(
    *,
    lifecycle_ratification_decision: ProactiveLifecycleRatificationDecision,
) -> ProactiveLifecycleEndorsementDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_ratification_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["endorsement"],
    )


def build_proactive_lifecycle_authorization_decision(
    *,
    lifecycle_endorsement_decision: ProactiveLifecycleEndorsementDecision,
) -> ProactiveLifecycleAuthorizationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_endorsement_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["authorization"],
    )


def build_proactive_lifecycle_enactment_decision(
    *,
    lifecycle_authorization_decision: ProactiveLifecycleAuthorizationDecision,
) -> ProactiveLifecycleEnactmentDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_authorization_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["enactment"],
    )


def build_proactive_lifecycle_finality_decision(
    *,
    lifecycle_enactment_decision: ProactiveLifecycleEnactmentDecision,
) -> ProactiveLifecycleFinalityDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_enactment_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["finality"],
    )


def build_proactive_lifecycle_completion_decision(
    *,
    lifecycle_finality_decision: ProactiveLifecycleFinalityDecision,
) -> ProactiveLifecycleCompletionDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_finality_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["completion"],
    )


def build_proactive_lifecycle_conclusion_decision(
    *,
    lifecycle_completion_decision: ProactiveLifecycleCompletionDecision,
) -> ProactiveLifecycleConclusionDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_completion_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["conclusion"],
    )


def build_proactive_lifecycle_disposition_decision(
    *,
    lifecycle_conclusion_decision: ProactiveLifecycleConclusionDecision,
) -> ProactiveLifecycleDispositionDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_conclusion_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["disposition"],
    )


def build_proactive_lifecycle_standing_decision(
    *,
    lifecycle_disposition_decision: ProactiveLifecycleDispositionDecision,
) -> ProactiveLifecycleStandingDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_disposition_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["standing"],
    )


def build_proactive_lifecycle_residency_decision(
    *,
    lifecycle_standing_decision: ProactiveLifecycleStandingDecision,
) -> ProactiveLifecycleResidencyDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_standing_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["residency"],
    )


def build_proactive_lifecycle_tenure_decision(
    *,
    lifecycle_residency_decision: ProactiveLifecycleResidencyDecision,
) -> ProactiveLifecycleTenureDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_residency_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["tenure"],
    )


def build_proactive_lifecycle_persistence_decision(
    *,
    lifecycle_tenure_decision: ProactiveLifecycleTenureDecision,
) -> ProactiveLifecyclePersistenceDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_tenure_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["persistence"],
    )


def build_proactive_lifecycle_durability_decision(
    *,
    lifecycle_persistence_decision: ProactiveLifecyclePersistenceDecision,
) -> ProactiveLifecycleDurabilityDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_persistence_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["durability"],
    )


def build_proactive_lifecycle_longevity_decision(
    *,
    lifecycle_durability_decision: ProactiveLifecycleDurabilityDecision,
) -> ProactiveLifecycleLongevityDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_durability_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["longevity"],
    )


def build_proactive_lifecycle_legacy_decision(
    *,
    lifecycle_longevity_decision: ProactiveLifecycleLongevityDecision,
) -> ProactiveLifecycleLegacyDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_longevity_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["legacy"],
    )


def build_proactive_lifecycle_heritage_decision(
    *,
    lifecycle_legacy_decision: ProactiveLifecycleLegacyDecision,
) -> ProactiveLifecycleHeritageDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_legacy_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["heritage"],
    )


def build_proactive_lifecycle_lineage_decision(
    *,
    lifecycle_heritage_decision: ProactiveLifecycleHeritageDecision,
) -> ProactiveLifecycleLineageDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_heritage_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["lineage"],
    )


def build_proactive_lifecycle_ancestry_decision(
    *,
    lifecycle_lineage_decision: ProactiveLifecycleLineageDecision,
) -> ProactiveLifecycleAncestryDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_lineage_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["ancestry"],
    )


def build_proactive_lifecycle_provenance_decision(
    *,
    lifecycle_ancestry_decision: ProactiveLifecycleAncestryDecision,
) -> ProactiveLifecycleProvenanceDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_ancestry_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["provenance"],
    )


def build_proactive_lifecycle_origin_decision(
    *,
    lifecycle_provenance_decision: ProactiveLifecycleProvenanceDecision,
) -> ProactiveLifecycleOriginDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_provenance_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["origin"],
    )


def build_proactive_lifecycle_root_decision(
    *,
    lifecycle_origin_decision: ProactiveLifecycleOriginDecision,
) -> ProactiveLifecycleRootDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_origin_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["root"],
    )


def build_proactive_lifecycle_foundation_decision(
    *,
    lifecycle_root_decision: ProactiveLifecycleRootDecision,
) -> ProactiveLifecycleFoundationDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_root_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["foundation"],
    )


def build_proactive_lifecycle_bedrock_decision(
    *,
    lifecycle_foundation_decision: ProactiveLifecycleFoundationDecision,
) -> ProactiveLifecycleBedrockDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_foundation_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["bedrock"],
    )


def build_proactive_lifecycle_substrate_decision(
    *,
    lifecycle_bedrock_decision: ProactiveLifecycleBedrockDecision,
) -> ProactiveLifecycleSubstrateDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_bedrock_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["substrate"],
    )


def build_proactive_lifecycle_stratum_decision(
    *,
    lifecycle_substrate_decision: ProactiveLifecycleSubstrateDecision,
) -> ProactiveLifecycleStratumDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_substrate_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["stratum"],
    )


def build_proactive_lifecycle_layer_decision(
    *,
    lifecycle_stratum_decision: ProactiveLifecycleStratumDecision,
) -> ProactiveLifecycleLayerDecision:
    return _build_lifecycle_chain_decision(
        previous_decision=lifecycle_stratum_decision,
        spec=_LIFECYCLE_CHAIN_SPECS["layer"],
    )
