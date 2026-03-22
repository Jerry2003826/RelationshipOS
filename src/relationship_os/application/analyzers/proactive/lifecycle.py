"""Proactive lifecycle decision chain.

state → transition → machine → controller → envelope → scheduler →
window → queue → dispatch → outcome → resolution → activation →
settlement → ... → stratum → layer.
"""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ProactiveAggregateControllerDecision,
    ProactiveDispatchEnvelopeDecision,
    ProactiveDispatchGateDecision,
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
    ProactiveLineMachineDecision,
    ProactiveLineStateDecision,
    ProactiveLineTransitionDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveSchedulingPlan,
    ProactiveStageMachineDecision,
)


def build_proactive_lifecycle_state_decision(
    *,
    stage_machine_decision: ProactiveStageMachineDecision,
    line_machine_decision: ProactiveLineMachineDecision,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
) -> ProactiveLifecycleStateDecision:
    current_stage_label = (
        line_machine_decision.current_stage_label
        or stage_machine_decision.stage_label
        or "unknown"
    )
    current_stage_index = max(
        1,
        int(
            line_machine_decision.current_stage_index
            or stage_machine_decision.stage_index
            or 1
        ),
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
        and orchestration_controller_decision.primary_source
        not in {None, "", "cadence"}
        else line_machine_decision.primary_source
        or stage_machine_decision.primary_source
        or "cadence"
    )
    controller_decision = (
        orchestration_controller_decision.decision
        if orchestration_controller_decision is not None
        and orchestration_controller_decision.decision
        not in {"dispatch", "follow_local_controllers", "follow_remaining_line"}
        else line_machine_decision.controller_decision
        or stage_machine_decision.controller_decision
    )

    status = line_machine_decision.status or stage_machine_decision.status or "active"
    state_mode = "lifecycle_active"
    lifecycle_mode = "active"
    actionability = "advance"
    state_notes: list[str] = [
        f"stage:{stage_machine_mode}",
        f"line:{line_machine_mode}",
    ]

    if (
        line_machine_decision.lifecycle_mode == "terminal"
        or stage_machine_decision.lifecycle_mode == "terminal"
    ):
        status = "terminal"
        state_mode = "lifecycle_terminal"
        lifecycle_mode = "terminal"
        actionability = "retire"
        state_notes.append("terminal_line")
    elif (
        line_machine_decision.lifecycle_mode == "winding_down"
        or stage_machine_decision.lifecycle_mode == "winding_down"
    ):
        status = "active"
        state_mode = "lifecycle_winding_down"
        lifecycle_mode = "winding_down"
        actionability = "close_loop"
        state_notes.append("winding_down_line")
    elif (
        line_machine_decision.lifecycle_mode == "buffered"
        or stage_machine_decision.lifecycle_mode in {"buffered", "waiting"}
    ):
        status = "scheduled"
        state_mode = "lifecycle_buffered"
        lifecycle_mode = "buffered"
        actionability = "buffer"
        state_notes.append("buffered_line")
    elif (
        line_machine_decision.lifecycle_mode == "active_softened"
        or stage_machine_decision.machine_mode == "dispatching_softened_stage"
    ):
        status = "active"
        state_mode = "lifecycle_softened"
        lifecycle_mode = "active_softened"
        actionability = "soften"
        state_notes.append("softened_line")
    elif (
        line_machine_decision.lifecycle_mode == "dormant"
        or stage_machine_decision.lifecycle_mode == "dormant"
    ):
        status = "hold"
        state_mode = "lifecycle_dormant"
        lifecycle_mode = "dormant"
        actionability = "hold"
        state_notes.append("dormant_line")
    elif stage_machine_decision.lifecycle_mode == "dispatching":
        status = "active"
        state_mode = "lifecycle_dispatching"
        lifecycle_mode = "active"
        actionability = "dispatch"
        state_notes.append("dispatching_stage")

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
    state_key = f"{current_stage_label}_{state_mode}_{selected_strategy_key}"
    changed = bool(
        stage_machine_decision.changed
        or line_machine_decision.changed
        or state_mode not in {"lifecycle_active", "lifecycle_dormant"}
        or actionability != "advance"
    )
    rationale = (
        "The proactive lifecycle state now combines the current stage machine, "
        "the line machine, and the orchestration layer into one observable posture."
    )
    if lifecycle_mode == "terminal":
        rationale = (
            "The proactive lifecycle is already terminal, so the line should retire "
            "instead of leaving more proactive motion alive."
        )
    elif lifecycle_mode == "winding_down":
        rationale = (
            "The proactive lifecycle is winding down, so remaining movement should "
            "stay close-loop and low-pressure."
        )
    elif lifecycle_mode in {"buffered", "active_softened"}:
        rationale = (
            "The proactive lifecycle is softened, so the whole line should leave "
            "extra user space before any further dispatch."
        )

    return ProactiveLifecycleStateDecision(
        status=status,
        state_key=state_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        stage_machine_key=stage_machine_key,
        stage_machine_mode=stage_machine_mode,
        line_machine_key=line_machine_key,
        line_machine_mode=line_machine_mode,
        line_state=line_state,
        state_mode=state_mode,
        lifecycle_mode=lifecycle_mode,
        actionability=actionability,
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
        rationale=rationale,
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
        transition_notes.append(
            f"controller:{lifecycle_state_decision.controller_decision}"
        )
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
            "The proactive lifecycle should retire because the line has reached a "
            "terminal posture."
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
        lifecycle_transition_decision.transition_key
        or f"{current_stage_label}_advance_lifecycle"
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
        machine_notes.append(
            f"controller:{lifecycle_transition_decision.controller_decision}"
        )
    if lifecycle_transition_decision.next_line_state not in {
        None,
        "",
        lifecycle_state_decision.line_state,
    }:
        machine_notes.append(
            f"next_line:{lifecycle_transition_decision.next_line_state}"
        )
    if lifecycle_transition_decision.next_stage_label:
        machine_notes.append(
            f"next_stage:{lifecycle_transition_decision.next_stage_label}"
        )

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

    if (
        lifecycle_machine_decision.actionability == "retire"
        or lifecycle_mode == "terminal"
    ):
        status = "terminal"
        lifecycle_state = "terminal"
        decision = "retire_lifecycle"
        changed = True
    elif (
        lifecycle_machine_decision.actionability == "close_loop"
        or lifecycle_mode == "winding_down"
    ):
        status = "active"
        lifecycle_state = "winding_down"
        decision = "close_loop_lifecycle"
        changed = True
    elif (
        lifecycle_machine_decision.actionability == "buffer"
        or lifecycle_mode == "buffered"
    ):
        status = "scheduled"
        lifecycle_state = "buffered"
        decision = "buffer_lifecycle"
        changed = True
    elif (
        lifecycle_machine_decision.actionability == "soften"
        or lifecycle_mode == "active_softened"
    ):
        status = "active"
        lifecycle_state = "softened"
        decision = "soften_lifecycle"
        changed = True
    elif (
        lifecycle_machine_decision.actionability == "hold"
        or lifecycle_mode == "dormant"
    ):
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
    lifecycle_state = (
        lifecycle_controller_decision.lifecycle_state
        or lifecycle_machine_decision.lifecycle_mode
        or "active"
    )
    status = lifecycle_controller_decision.status or lifecycle_machine_decision.status or "active"
    decision = "continue_lifecycle_shape"
    envelope_mode = "active_lifecycle_shape"
    actionability = "continue"
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
            dispatch_envelope_decision.selected_pressure_mode
            or selected_pressure_mode
        )
        selected_autonomy_signal = (
            dispatch_envelope_decision.selected_autonomy_signal
            or selected_autonomy_signal
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

    if decision == "continue_lifecycle_shape" and additional_delay_seconds > 0:
        changed = True

    if lifecycle_controller_decision.decision == "retire_lifecycle":
        status = "terminal"
        lifecycle_state = "terminal"
        decision = "retire_lifecycle_shape"
        envelope_mode = "terminal_lifecycle_shape"
        actionability = "retire"
        changed = True
    elif lifecycle_controller_decision.decision == "close_loop_lifecycle":
        status = "active"
        lifecycle_state = "winding_down"
        decision = "close_loop_lifecycle_shape"
        envelope_mode = "winding_down_lifecycle_shape"
        actionability = "close_loop"
        changed = True
    elif lifecycle_controller_decision.decision == "buffer_lifecycle":
        status = "scheduled"
        lifecycle_state = "buffered"
        decision = "buffer_lifecycle_shape"
        envelope_mode = "buffered_lifecycle_shape"
        actionability = "buffer"
        changed = True
    elif lifecycle_controller_decision.decision == "soften_lifecycle":
        status = "active"
        lifecycle_state = "softened"
        decision = "soften_lifecycle_shape"
        envelope_mode = "softened_lifecycle_shape"
        actionability = "soften"
        changed = True
    elif lifecycle_controller_decision.decision == "hold_lifecycle":
        status = "hold"
        lifecycle_state = "dormant"
        decision = "hold_lifecycle_shape"
        envelope_mode = "dormant_lifecycle_shape"
        actionability = "hold"
        changed = True
    elif lifecycle_controller_decision.decision == "dispatch_lifecycle":
        status = "active"
        lifecycle_state = "dispatching"
        decision = "dispatch_lifecycle_shape"
        envelope_mode = "dispatching_lifecycle_shape"
        actionability = "dispatch"
        changed = True

    if additional_delay_seconds > 0:
        envelope_notes.append(f"delay:{additional_delay_seconds}")
    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        envelope_notes.append(f"controller:{controller_decision}")

    envelope_key = (
        f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"
    )
    if not changed and decision == "continue_lifecycle_shape":
        envelope_key = f"{current_stage_label}_continue_lifecycle_shape"

    rationale = (
        "The proactive lifecycle envelope keeps the line on its current lifecycle posture "
        "because the higher-order lifecycle stack did not need to reshape execution."
    )
    if actionability == "retire":
        rationale = (
            "The proactive lifecycle envelope retires the line because the lifecycle stack "
            "has already moved into a terminal posture."
        )
    elif actionability == "close_loop":
        rationale = (
            "The proactive lifecycle envelope keeps the line in a winding-down shape so "
            "the remaining touch stays close-loop and low-pressure."
        )
    elif actionability in {"buffer", "soften"}:
        rationale = (
            "The proactive lifecycle envelope keeps a softened buffered execution shape so "
            "later touches inherit more user space and lower pressure."
        )
    elif actionability == "dispatch":
        rationale = (
            "The proactive lifecycle envelope can still dispatch, but it now does so as "
            "an explicit lifecycle-level execution posture."
        )

    return ProactiveLifecycleEnvelopeDecision(
        status=status,
        envelope_key=envelope_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        envelope_mode=envelope_mode,
        decision=decision,
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
        envelope_notes=_compact(envelope_notes, limit=8),
        rationale=rationale,
    )


def build_proactive_lifecycle_scheduler_decision(
    *,
    lifecycle_envelope_decision: ProactiveLifecycleEnvelopeDecision,
    proactive_scheduling_plan: ProactiveSchedulingPlan | None = None,
    dispatch_gate_decision: ProactiveDispatchGateDecision | None = None,
) -> ProactiveLifecycleSchedulerDecision:
    current_stage_label = lifecycle_envelope_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_envelope_decision.lifecycle_state or "active"
    lifecycle_envelope_mode = (
        lifecycle_envelope_decision.envelope_mode or "active_lifecycle_shape"
    )
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
    selected_autonomy_signal = (
        lifecycle_envelope_decision.selected_autonomy_signal or "none"
    )
    selected_delivery_mode = lifecycle_envelope_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_envelope_decision.primary_source or "cadence"
    controller_decision = lifecycle_envelope_decision.controller_decision
    active_sources = list(lifecycle_envelope_decision.active_sources)
    scheduler_notes: list[str] = list(lifecycle_envelope_decision.envelope_notes)
    scheduling_status = "inactive"
    scheduling_mode = "none"
    scheduling_extra_delay = 0
    if isinstance(proactive_scheduling_plan, ProactiveSchedulingPlan):
        scheduling_status = proactive_scheduling_plan.status
        scheduling_mode = proactive_scheduling_plan.scheduler_mode
        scheduling_extra_delay = int(
            proactive_scheduling_plan.first_touch_extra_delay_seconds or 0
        )
    elif proactive_scheduling_plan is not None:
        scheduling_payload = dict(proactive_scheduling_plan or {})
        scheduling_status = str(scheduling_payload.get("status") or "inactive")
        scheduling_mode = str(scheduling_payload.get("scheduler_mode") or "none")
        scheduling_extra_delay = int(
            scheduling_payload.get("first_touch_extra_delay_seconds") or 0
        )

    if actionability == "retire" or lifecycle_state == "terminal":
        status = "terminal"
        decision = "retire_lifecycle_schedule"
        scheduler_mode = "terminal_lifecycle_schedule"
        queue_status_hint = "terminal"
        changed = True
    elif actionability == "close_loop" or lifecycle_state == "winding_down":
        status = "active"
        decision = "close_loop_lifecycle_schedule"
        scheduler_mode = "winding_down_lifecycle_schedule"
        queue_status_hint = "due"
        changed = True
    elif actionability in {"buffer", "soften"} or lifecycle_state in {
        "buffered",
        "softened",
    }:
        status = "scheduled"
        decision = "buffer_lifecycle_schedule"
        scheduler_mode = "buffered_lifecycle_schedule"
        queue_status_hint = "scheduled"
        actionability = "buffer"
        changed = True
    elif actionability == "hold" or lifecycle_state == "dormant":
        status = "hold"
        decision = "hold_lifecycle_schedule"
        scheduler_mode = "dormant_lifecycle_schedule"
        queue_status_hint = "hold"
        changed = True
    elif actionability == "dispatch" or lifecycle_state == "dispatching":
        status = "active"
        decision = "dispatch_lifecycle_schedule"
        scheduler_mode = "dispatching_lifecycle_schedule"
        queue_status_hint = "due"
        changed = True

    if proactive_scheduling_plan is not None and scheduling_status == "active":
        if scheduling_extra_delay > 0:
            additional_delay_seconds = max(
                additional_delay_seconds,
                scheduling_extra_delay,
            )
            changed = True
            scheduler_notes.append(f"scheduling_delay:{scheduling_extra_delay}")
            if primary_source in {"cadence", "lifecycle_envelope"}:
                primary_source = "scheduling_plan"
        active_sources.append("scheduling_plan")
        scheduler_notes.append(f"scheduler:{scheduling_mode}")

    if dispatch_gate_decision is not None:
        active_sources.append("dispatch_gate")
        if dispatch_gate_decision.decision == "defer":
            status = "scheduled"
            decision = "defer_lifecycle_schedule"
            scheduler_mode = "deferred_lifecycle_schedule"
            queue_status_hint = "scheduled"
            actionability = "buffer"
            additional_delay_seconds = max(
                additional_delay_seconds,
                int(dispatch_gate_decision.retry_after_seconds or 0),
            )
            changed = True
            primary_source = "dispatch_gate"
            scheduler_notes.append(
                f"gate_defer:{int(dispatch_gate_decision.retry_after_seconds or 0)}"
            )
        elif dispatch_gate_decision.decision == "hold":
            status = "hold"
            decision = "hold_lifecycle_schedule"
            scheduler_mode = "hold_lifecycle_schedule"
            queue_status_hint = "hold"
            actionability = "hold"
            changed = True
            primary_source = "dispatch_gate"
            scheduler_notes.append("gate_hold")

    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        scheduler_notes.append(f"controller:{controller_decision}")

    scheduler_key = (
        f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"
    )
    if not changed and decision == "continue_lifecycle_schedule":
        scheduler_key = f"{current_stage_label}_continue_lifecycle_schedule"

    rationale = (
        "The proactive lifecycle scheduler keeps the lifecycle envelope on its current "
        "execution path because no higher-order scheduling force needs to reshape timing."
    )
    if decision == "retire_lifecycle_schedule":
        rationale = (
            "The proactive lifecycle scheduler retires the line because the lifecycle "
            "stack has already reached a terminal execution posture."
        )
    elif decision == "close_loop_lifecycle_schedule":
        rationale = (
            "The proactive lifecycle scheduler keeps the line on a winding-down path so "
            "the final touch stays close-loop and low-pressure."
        )
    elif decision in {"buffer_lifecycle_schedule", "defer_lifecycle_schedule"}:
        rationale = (
            "The proactive lifecycle scheduler buffers the line so later touches inherit "
            "more user space and a softer dispatch window."
        )
    elif decision == "dispatch_lifecycle_schedule":
        rationale = (
            "The proactive lifecycle scheduler keeps the line dispatchable, but now as "
            "an explicit lifecycle-level scheduling posture."
        )

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
    selected_autonomy_signal = (
        lifecycle_scheduler_decision.selected_autonomy_signal or "none"
    )
    selected_delivery_mode = (
        lifecycle_scheduler_decision.selected_delivery_mode or "none"
    )
    primary_source = lifecycle_scheduler_decision.primary_source or "cadence"
    controller_decision = lifecycle_scheduler_decision.controller_decision
    active_sources = list(lifecycle_scheduler_decision.active_sources)
    window_notes: list[str] = list(lifecycle_scheduler_decision.scheduler_notes)
    schedule_reason_value = str(schedule_reason or "")

    if (
        lifecycle_scheduler_decision.decision == "retire_lifecycle_schedule"
        or lifecycle_state == "terminal"
    ):
        status = "terminal"
        decision = "retire_lifecycle_window"
        window_mode = "terminal_lifecycle_window"
        queue_status = "terminal"
        actionability = "retire"
        changed = True
    elif (
        lifecycle_scheduler_decision.decision == "close_loop_lifecycle_schedule"
        or lifecycle_state == "winding_down"
    ):
        status = "active"
        decision = "close_loop_lifecycle_window"
        window_mode = "close_loop_lifecycle_window"
        queue_status = (
            queue_status
            if queue_status in {"due", "overdue", "scheduled"}
            else "due"
        )
        actionability = "close_loop"
        changed = True
    elif progression_advanced and current_stage_label == "final_soft_close":
        status = "active"
        decision = "close_loop_lifecycle_window"
        window_mode = "close_loop_lifecycle_window"
        queue_status = queue_status if queue_status in {"due", "overdue"} else "due"
        actionability = "close_loop"
        changed = True
        if primary_source in {"cadence", "lifecycle_scheduler"}:
            primary_source = "progression"
    elif lifecycle_scheduler_decision.decision == "defer_lifecycle_schedule":
        status = "scheduled"
        decision = "defer_lifecycle_window"
        window_mode = "deferred_lifecycle_window"
        queue_status = "scheduled"
        actionability = "buffer"
        changed = True
    elif (
        lifecycle_scheduler_decision.decision == "buffer_lifecycle_schedule"
        or lifecycle_state in {"buffered", "softened"}
    ):
        status = "scheduled"
        decision = "buffer_lifecycle_window"
        window_mode = "buffered_lifecycle_window"
        queue_status = "scheduled"
        actionability = "buffer"
        changed = True
    elif (
        lifecycle_scheduler_decision.decision == "hold_lifecycle_schedule"
        or lifecycle_state == "dormant"
    ):
        status = "hold"
        decision = "hold_lifecycle_window"
        window_mode = "hold_lifecycle_window"
        queue_status = "hold"
        actionability = "hold"
        changed = True
    elif (
        lifecycle_scheduler_decision.decision == "dispatch_lifecycle_schedule"
        or lifecycle_state == "dispatching"
    ):
        status = "active"
        decision = "dispatch_lifecycle_window"
        window_mode = "dispatch_lifecycle_window"
        queue_status = queue_status if queue_status in {"due", "overdue"} else "due"
        actionability = "dispatch"
        changed = True

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

    rationale = (
        "The proactive lifecycle window keeps the current scheduling posture because "
        "the lifecycle scheduler did not need to reshape the timing window any further."
    )
    if decision == "retire_lifecycle_window":
        rationale = (
            "The proactive lifecycle window is terminal because the scheduler has already "
            "moved the line into a retire-ready posture."
        )
    elif decision == "close_loop_lifecycle_window":
        rationale = (
            "The proactive lifecycle window keeps the line in a close-loop window so the "
            "remaining touch stays low-pressure and winding down."
        )
    elif decision in {"buffer_lifecycle_window", "defer_lifecycle_window"}:
        rationale = (
            "The proactive lifecycle window keeps the line scheduled so later touches "
            "inherit more user space and a softer dispatch window."
        )
    elif decision == "dispatch_lifecycle_window":
        rationale = (
            "The proactive lifecycle window keeps the line dispatchable as an explicit "
            "lifecycle-level time window rather than an implicit queue default."
        )

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
    selected_autonomy_signal = (
        lifecycle_window_decision.selected_autonomy_signal or "none"
    )
    selected_delivery_mode = lifecycle_window_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_window_decision.primary_source or "cadence"
    controller_decision = lifecycle_window_decision.controller_decision
    active_sources = list(lifecycle_window_decision.active_sources)
    queue_notes: list[str] = list(lifecycle_window_decision.window_notes)

    if queue_status != lifecycle_window_queue_status:
        queue_notes.append(f"queue_override:{queue_status}")
        if primary_source in {"cadence", "lifecycle_window"}:
            primary_source = "queue"

    if (
        lifecycle_window_decision.decision == "retire_lifecycle_window"
        or lifecycle_state == "terminal"
        or queue_status == "terminal"
    ):
        status = "terminal"
        decision = "retire_lifecycle_queue"
        queue_mode = "terminal_lifecycle_queue"
        queue_status = "terminal"
        actionability = "retire"
        changed = True
    elif (
        lifecycle_window_decision.decision == "hold_lifecycle_window"
        or queue_status == "hold"
    ):
        status = "hold"
        decision = "hold_lifecycle_queue"
        queue_mode = "hold_lifecycle_queue"
        queue_status = "hold"
        actionability = "hold"
        changed = True
    elif queue_status == "waiting":
        status = "waiting"
        decision = "wait_lifecycle_queue"
        queue_mode = "waiting_lifecycle_queue"
        queue_status = "waiting"
        actionability = "wait"
        changed = True
    elif (
        lifecycle_window_decision.decision in {
            "buffer_lifecycle_window",
            "defer_lifecycle_window",
        }
        or queue_status == "scheduled"
    ):
        status = "scheduled"
        if lifecycle_window_decision.decision == "defer_lifecycle_window":
            decision = "defer_lifecycle_queue"
            queue_mode = "deferred_lifecycle_queue"
        else:
            decision = "buffer_lifecycle_queue"
            queue_mode = "buffered_lifecycle_queue"
        queue_status = "scheduled"
        actionability = "buffer"
        changed = True
    elif queue_status == "overdue":
        status = "active"
        if lifecycle_window_decision.decision == "close_loop_lifecycle_window":
            decision = "overdue_close_loop_lifecycle_queue"
            queue_mode = "overdue_close_loop_lifecycle_queue"
            actionability = "close_loop"
        else:
            decision = "overdue_lifecycle_queue"
            queue_mode = "overdue_lifecycle_queue"
            actionability = "dispatch"
        queue_status = "overdue"
        changed = True
    elif (
        lifecycle_window_decision.decision == "close_loop_lifecycle_window"
        or lifecycle_state == "winding_down"
    ):
        status = "active"
        decision = "close_loop_lifecycle_queue"
        queue_mode = "close_loop_lifecycle_queue"
        queue_status = "due"
        actionability = "close_loop"
        changed = True
    elif (
        lifecycle_window_decision.decision == "dispatch_lifecycle_window"
        or queue_status == "due"
    ):
        status = "active"
        decision = "dispatch_lifecycle_queue"
        queue_mode = "ready_lifecycle_queue"
        queue_status = "due"
        actionability = "dispatch"
        changed = True

    if controller_decision not in {None, "", "dispatch", "follow_local_controllers"}:
        queue_notes.append(f"controller:{controller_decision}")

    queue_key = f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"
    if not changed and decision == "continue_lifecycle_queue":
        queue_key = f"{current_stage_label}_continue_lifecycle_queue"

    rationale = (
        "The proactive lifecycle queue keeps the current lifecycle window posture because "
        "the queue layer does not need to reinterpret that window any further."
    )
    if decision == "retire_lifecycle_queue":
        rationale = (
            "The proactive lifecycle queue is terminal because the lifecycle window has "
            "already moved the line into a retire-ready posture."
        )
    elif decision in {"hold_lifecycle_queue", "wait_lifecycle_queue"}:
        rationale = (
            "The proactive lifecycle queue keeps the line out of dispatch so the current "
            "lifecycle posture preserves user space instead of forcing contact."
        )
    elif decision in {"buffer_lifecycle_queue", "defer_lifecycle_queue"}:
        rationale = (
            "The proactive lifecycle queue keeps the line scheduled so later touches "
            "inherit a softer lifecycle-level queue posture."
        )
    elif decision in {
        "close_loop_lifecycle_queue",
        "overdue_close_loop_lifecycle_queue",
    }:
        rationale = (
            "The proactive lifecycle queue keeps the line in a close-loop queue posture "
            "so any remaining touch stays winding-down and low-pressure."
        )
    elif decision in {"dispatch_lifecycle_queue", "overdue_lifecycle_queue"}:
        rationale = (
            "The proactive lifecycle queue keeps the line explicitly dispatchable rather "
            "than relying on an implicit queue default."
        )

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
    queue_status = str(
        current_queue_status or lifecycle_queue_decision.queue_status or "due"
    )
    status = lifecycle_queue_decision.status or "active"
    decision = "hold_lifecycle_dispatch"
    dispatch_mode = "hold_lifecycle_dispatch"
    actionability = "hold"
    changed = bool(lifecycle_queue_decision.changed)
    additional_delay_seconds = max(
        0,
        int(lifecycle_queue_decision.additional_delay_seconds or 0),
    )
    selected_strategy_key = lifecycle_queue_decision.selected_strategy_key or "none"
    selected_pressure_mode = lifecycle_queue_decision.selected_pressure_mode or "none"
    selected_autonomy_signal = (
        lifecycle_queue_decision.selected_autonomy_signal or "none"
    )
    selected_delivery_mode = lifecycle_queue_decision.selected_delivery_mode or "none"
    primary_source = lifecycle_queue_decision.primary_source or "cadence"
    controller_decision = lifecycle_queue_decision.controller_decision
    active_sources = list(lifecycle_queue_decision.active_sources)
    dispatch_notes: list[str] = list(lifecycle_queue_decision.queue_notes)

    gate_payload = dispatch_gate_decision
    gate_decision = (
        gate_payload.decision
        if gate_payload is not None and gate_payload.decision
        else "dispatch"
    )
    gate_retry_after_seconds = max(
        0,
        int(
            gate_payload.retry_after_seconds
            if gate_payload is not None
            else 0
        ),
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

    if rendered_unit_count <= 0 or not has_followup_content:
        status = "hold"
        decision = "hold_lifecycle_dispatch"
        dispatch_mode = "hold_lifecycle_dispatch"
        actionability = "hold"
        changed = True
        dispatch_notes.append("empty_followup_units")
        if primary_source in {"cadence", "queue", "gate"}:
            primary_source = "rendering"
    elif (
        queue_decision == "retire_lifecycle_queue"
        or lifecycle_state == "terminal"
        or queue_status == "terminal"
    ):
        status = "terminal"
        decision = "retire_lifecycle_dispatch"
        dispatch_mode = "terminal_lifecycle_dispatch"
        actionability = "retire"
        changed = True
    elif gate_decision == "hold":
        status = "hold"
        decision = "hold_lifecycle_dispatch"
        dispatch_mode = "hold_lifecycle_dispatch"
        actionability = "hold"
        changed = True
    elif (
        gate_decision == "defer"
        or queue_decision in {"buffer_lifecycle_queue", "defer_lifecycle_queue"}
        or queue_status in {"waiting", "scheduled"}
    ):
        status = "scheduled"
        decision = "reschedule_lifecycle_dispatch"
        dispatch_mode = "rescheduled_lifecycle_dispatch"
        actionability = "buffer"
        changed = True
    elif (
        queue_decision in {
            "close_loop_lifecycle_queue",
            "overdue_close_loop_lifecycle_queue",
        }
        or lifecycle_state == "winding_down"
    ):
        status = "active"
        decision = "close_loop_lifecycle_dispatch"
        dispatch_mode = "close_loop_lifecycle_dispatch"
        actionability = "close_loop"
        changed = True
    elif (
        queue_decision in {"dispatch_lifecycle_queue", "overdue_lifecycle_queue"}
        or queue_status in {"due", "overdue"}
    ):
        status = "active"
        decision = "dispatch_lifecycle_now"
        dispatch_mode = "ready_lifecycle_dispatch"
        actionability = "dispatch"
        changed = True
    else:
        status = "hold"
        decision = "hold_lifecycle_dispatch"
        dispatch_mode = "hold_lifecycle_dispatch"
        actionability = "hold"
        changed = True
        dispatch_notes.append("fallback_hold")

    dispatch_key = f"{current_stage_label}_{decision}_{selected_strategy_key or 'none'}"

    rationale = (
        "The proactive lifecycle dispatch keeps the current lifecycle queue posture "
        "because the queue layer already carries the final execution shape."
    )
    if decision == "dispatch_lifecycle_now":
        rationale = (
            "The proactive lifecycle dispatch authorizes an immediate send because the "
            "lifecycle queue is dispatch-ready and the rendered follow-up content exists."
        )
    elif decision == "close_loop_lifecycle_dispatch":
        rationale = (
            "The proactive lifecycle dispatch authorizes a final low-pressure close-loop "
            "send because the lifecycle queue is winding down but still dispatchable."
        )
    elif decision == "reschedule_lifecycle_dispatch":
        rationale = (
            "The proactive lifecycle dispatch keeps the line scheduled so the proactive "
            "touch inherits more user space before it can be sent."
        )
    elif decision == "hold_lifecycle_dispatch":
        rationale = (
            "The proactive lifecycle dispatch keeps the line on hold because the current "
            "lifecycle posture should not force contact yet."
        )
        if "empty_followup_units" in dispatch_notes:
            rationale = (
                "The proactive lifecycle dispatch holds the line because the current "
                "follow-up render did not produce any sendable content."
            )
    elif decision == "retire_lifecycle_dispatch":
        rationale = (
            "The proactive lifecycle dispatch retires the line because the lifecycle "
            "queue is already terminal and should not emit any further contact."
        )

    return ProactiveLifecycleDispatchDecision(
        status=status,
        dispatch_key=dispatch_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        queue_mode=queue_mode,
        dispatch_mode=dispatch_mode,
        decision=decision,
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
        dispatch_notes=_compact(dispatch_notes, limit=8),
        rationale=rationale,
    )


def build_proactive_lifecycle_outcome_decision(
    *,
    lifecycle_dispatch_decision: ProactiveLifecycleDispatchDecision,
    dispatched: bool,
    message_event_count: int = 0,
) -> ProactiveLifecycleOutcomeDecision:
    current_stage_label = (
        lifecycle_dispatch_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_dispatch_decision.lifecycle_state or "active"
    dispatch_mode = (
        lifecycle_dispatch_decision.dispatch_mode or "hold_lifecycle_dispatch"
    )
    dispatch_decision = (
        lifecycle_dispatch_decision.decision or "hold_lifecycle_dispatch"
    )
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
        selected_strategy_key=(
            lifecycle_dispatch_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_dispatch_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_dispatch_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_dispatch_decision.selected_delivery_mode or "none"
        ),
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

    if outcome_decision in {
        "lifecycle_dispatch_retired",
        "lifecycle_close_loop_sent",
    } or line_exit_mode == "retire":
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
        selected_strategy_key=(
            lifecycle_outcome_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_outcome_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_outcome_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_outcome_decision.selected_delivery_mode or "none"
        ),
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
    current_stage_label = (
        lifecycle_resolution_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_resolution_decision.lifecycle_state or "active"
    resolution_mode = (
        lifecycle_resolution_decision.resolution_mode
        or "hold_lifecycle_resolution"
    )
    resolution_decision = (
        lifecycle_resolution_decision.decision or "hold_lifecycle_resolution"
    )
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
    activation_notes: list[str] = list(
        lifecycle_resolution_decision.resolution_notes
    )
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
        selected_strategy_key=(
            lifecycle_resolution_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_resolution_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_resolution_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_resolution_decision.selected_delivery_mode or "none"
        ),
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
    current_stage_label = (
        lifecycle_activation_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_activation_decision.lifecycle_state or "active"
    activation_mode = (
        lifecycle_activation_decision.activation_mode
        or "hold_lifecycle_activation"
    )
    activation_decision = (
        lifecycle_activation_decision.decision or "hold_current_lifecycle_stage"
    )
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
    settlement_notes: list[str] = list(
        lifecycle_activation_decision.activation_notes
    )
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
        selected_strategy_key=(
            lifecycle_activation_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_activation_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_activation_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_activation_decision.selected_delivery_mode or "none"
        ),
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
    current_stage_label = (
        lifecycle_settlement_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_settlement_decision.lifecycle_state or "active"
    settlement_mode = (
        lifecycle_settlement_decision.settlement_mode
        or "hold_lifecycle_settlement"
    )
    settlement_decision = (
        lifecycle_settlement_decision.decision or "hold_lifecycle_settlement"
    )
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
        selected_strategy_key=(
            lifecycle_settlement_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_settlement_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_settlement_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_settlement_decision.selected_delivery_mode or "none"
        ),
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
    current_stage_label = (
        lifecycle_closure_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_closure_decision.lifecycle_state or "active"
    closure_mode = (
        lifecycle_closure_decision.closure_mode or "paused_lifecycle_closure"
    )
    closure_decision = (
        lifecycle_closure_decision.decision or "pause_lifecycle_closure"
    )
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
        selected_strategy_key=(
            lifecycle_closure_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_closure_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_closure_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_closure_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        closure_decision=closure_decision,
        active_sources=_compact(lifecycle_closure_decision.active_sources, limit=8),
        availability_notes=_compact(availability_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_retention_decision(
    *,
    lifecycle_availability_decision: ProactiveLifecycleAvailabilityDecision,
) -> ProactiveLifecycleRetentionDecision:
    current_stage_label = (
        lifecycle_availability_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_availability_decision.lifecycle_state or "active"
    availability_mode = (
        lifecycle_availability_decision.availability_mode
        or "paused_lifecycle_availability"
    )
    availability_decision = (
        lifecycle_availability_decision.decision or "pause_lifecycle_availability"
    )
    active_stage_label = lifecycle_availability_decision.active_stage_label
    next_stage_label = lifecycle_availability_decision.next_stage_label
    remaining_stage_count = max(
        0,
        int(lifecycle_availability_decision.remaining_stage_count or 0),
    )
    line_state = lifecycle_availability_decision.line_state or "steady"
    line_exit_mode = lifecycle_availability_decision.line_exit_mode or "stay"
    status = lifecycle_availability_decision.status or "hold"
    retention_mode = "paused_lifecycle_retention"
    decision = "pause_lifecycle_retention"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0,
        int(lifecycle_availability_decision.additional_delay_seconds or 0),
    )
    primary_source = lifecycle_availability_decision.primary_source or "availability"
    retention_notes: list[str] = list(
        lifecycle_availability_decision.availability_notes
    )
    if line_state:
        retention_notes.append(f"line:{line_state}")
    if line_exit_mode:
        retention_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        retention_notes.append(f"active:{active_stage_label}")

    if availability_decision == "keep_lifecycle_available":
        status = "active"
        retention_mode = "retained_lifecycle_retention"
        decision = "retain_lifecycle_retention"
        actionability = "continue"
        queue_override_status = None
    elif availability_decision == "buffer_lifecycle_availability":
        status = "scheduled"
        retention_mode = "buffered_lifecycle_retention"
        decision = "buffer_lifecycle_retention"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif availability_decision == "pause_lifecycle_availability":
        status = "hold"
        retention_mode = "paused_lifecycle_retention"
        decision = "pause_lifecycle_retention"
        actionability = "pause"
        queue_override_status = "hold"
    elif availability_decision == "close_loop_lifecycle_availability":
        status = "terminal"
        retention_mode = "archived_lifecycle_retention"
        decision = "archive_lifecycle_retention"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif availability_decision == "retire_lifecycle_availability":
        status = "terminal"
        retention_mode = "retired_lifecycle_retention"
        decision = "retire_lifecycle_retention"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        retention_notes.append("fallback_pause")

    retention_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_availability_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_availability_decision.changed
        or decision != "pause_lifecycle_retention"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle retention converts the post-availability lifecycle "
        "shape into the final retained posture that queue and inspection layers should honor."
    )
    if decision == "retain_lifecycle_retention":
        rationale = (
            "The proactive lifecycle retention keeps the lifecycle retained because "
            "the line should remain present for the next proactive touch."
        )
    elif decision == "buffer_lifecycle_retention":
        rationale = (
            "The proactive lifecycle retention keeps the lifecycle buffered because "
            "the line stays retained but should wait before the next touch."
        )
    elif decision == "pause_lifecycle_retention":
        rationale = (
            "The proactive lifecycle retention pauses the lifecycle because the line "
            "should remain retained without actively pushing forward."
        )
    elif decision == "archive_lifecycle_retention":
        rationale = (
            "The proactive lifecycle retention archives the lifecycle because the line "
            "reached a clean close-loop ending."
        )
    elif decision == "retire_lifecycle_retention":
        rationale = (
            "The proactive lifecycle retention retires the lifecycle because the line "
            "has reached a terminal stop condition."
        )

    return ProactiveLifecycleRetentionDecision(
        status=status,
        retention_key=retention_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        availability_mode=availability_mode,
        retention_mode=retention_mode,
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
        selected_strategy_key=(
            lifecycle_availability_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_availability_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_availability_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_availability_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        availability_decision=availability_decision,
        active_sources=_compact(
            lifecycle_availability_decision.active_sources, limit=8
        ),
        retention_notes=_compact(retention_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_eligibility_decision(
    *,
    lifecycle_retention_decision: ProactiveLifecycleRetentionDecision,
) -> ProactiveLifecycleEligibilityDecision:
    current_stage_label = lifecycle_retention_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_retention_decision.lifecycle_state or "active"
    retention_mode = (
        lifecycle_retention_decision.retention_mode
        or "paused_lifecycle_retention"
    )
    retention_decision = (
        lifecycle_retention_decision.decision or "pause_lifecycle_retention"
    )
    active_stage_label = lifecycle_retention_decision.active_stage_label
    next_stage_label = lifecycle_retention_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_retention_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_retention_decision.line_state or "steady"
    line_exit_mode = lifecycle_retention_decision.line_exit_mode or "stay"
    status = lifecycle_retention_decision.status or "hold"
    eligibility_mode = "paused_lifecycle_eligibility"
    decision = "pause_lifecycle_eligibility"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_retention_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_retention_decision.primary_source or "retention"
    eligibility_notes: list[str] = list(lifecycle_retention_decision.retention_notes)
    if line_state:
        eligibility_notes.append(f"line:{line_state}")
    if line_exit_mode:
        eligibility_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        eligibility_notes.append(f"active:{active_stage_label}")

    if retention_decision == "retain_lifecycle_retention":
        status = "active"
        eligibility_mode = "eligible_lifecycle_eligibility"
        decision = "keep_lifecycle_eligible"
        actionability = "continue"
        queue_override_status = None
    elif retention_decision == "buffer_lifecycle_retention":
        status = "scheduled"
        eligibility_mode = "buffered_lifecycle_eligibility"
        decision = "buffer_lifecycle_eligibility"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif retention_decision == "pause_lifecycle_retention":
        status = "hold"
        eligibility_mode = "paused_lifecycle_eligibility"
        decision = "pause_lifecycle_eligibility"
        actionability = "pause"
        queue_override_status = "hold"
    elif retention_decision == "archive_lifecycle_retention":
        status = "terminal"
        eligibility_mode = "archived_lifecycle_eligibility"
        decision = "archive_lifecycle_eligibility"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif retention_decision == "retire_lifecycle_retention":
        status = "terminal"
        eligibility_mode = "retired_lifecycle_eligibility"
        decision = "retire_lifecycle_eligibility"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        eligibility_notes.append("fallback_pause")

    eligibility_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_retention_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_retention_decision.changed
        or decision != "pause_lifecycle_eligibility"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle eligibility converts the post-retention lifecycle "
        "shape into the final eligible posture that downstream queue and dispatch "
        "selection should honor."
    )
    if decision == "keep_lifecycle_eligible":
        rationale = (
            "The proactive lifecycle eligibility keeps the lifecycle eligible because "
            "the retained line should remain a valid candidate for the next proactive touch."
        )
    elif decision == "buffer_lifecycle_eligibility":
        rationale = (
            "The proactive lifecycle eligibility keeps the lifecycle buffered because "
            "the retained line stays eligible but should wait before being considered."
        )
    elif decision == "pause_lifecycle_eligibility":
        rationale = (
            "The proactive lifecycle eligibility pauses the lifecycle because the line "
            "should remain retained without actively re-entering the queue."
        )
    elif decision == "archive_lifecycle_eligibility":
        rationale = (
            "The proactive lifecycle eligibility archives the lifecycle because the line "
            "reached a clean close-loop ending and should no longer be considered active."
        )
    elif decision == "retire_lifecycle_eligibility":
        rationale = (
            "The proactive lifecycle eligibility retires the lifecycle because the line "
            "has reached a terminal stop condition and should no longer be considered."
        )

    return ProactiveLifecycleEligibilityDecision(
        status=status,
        eligibility_key=eligibility_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        retention_mode=retention_mode,
        eligibility_mode=eligibility_mode,
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
        selected_strategy_key=(
            lifecycle_retention_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_retention_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_retention_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_retention_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        retention_decision=retention_decision,
        active_sources=_compact(lifecycle_retention_decision.active_sources, limit=8),
        eligibility_notes=_compact(eligibility_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_candidate_decision(
    *,
    lifecycle_eligibility_decision: ProactiveLifecycleEligibilityDecision,
) -> ProactiveLifecycleCandidateDecision:
    current_stage_label = lifecycle_eligibility_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_eligibility_decision.lifecycle_state or "active"
    eligibility_mode = (
        lifecycle_eligibility_decision.eligibility_mode
        or "paused_lifecycle_eligibility"
    )
    eligibility_decision = (
        lifecycle_eligibility_decision.decision or "pause_lifecycle_eligibility"
    )
    active_stage_label = lifecycle_eligibility_decision.active_stage_label
    next_stage_label = lifecycle_eligibility_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_eligibility_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_eligibility_decision.line_state or "steady"
    line_exit_mode = lifecycle_eligibility_decision.line_exit_mode or "stay"
    status = lifecycle_eligibility_decision.status or "hold"
    candidate_mode = "paused_lifecycle_candidate"
    decision = "pause_lifecycle_candidate"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_eligibility_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_eligibility_decision.primary_source or "eligibility"
    candidate_notes: list[str] = list(
        lifecycle_eligibility_decision.eligibility_notes
    )
    if line_state:
        candidate_notes.append(f"line:{line_state}")
    if line_exit_mode:
        candidate_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        candidate_notes.append(f"active:{active_stage_label}")

    if eligibility_decision == "keep_lifecycle_eligible":
        status = "active"
        candidate_mode = "candidate_lifecycle_candidate"
        decision = "keep_lifecycle_candidate"
        actionability = "continue"
        queue_override_status = None
    elif eligibility_decision == "buffer_lifecycle_eligibility":
        status = "scheduled"
        candidate_mode = "buffered_lifecycle_candidate"
        decision = "buffer_lifecycle_candidate"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif eligibility_decision == "pause_lifecycle_eligibility":
        status = "hold"
        candidate_mode = "paused_lifecycle_candidate"
        decision = "pause_lifecycle_candidate"
        actionability = "pause"
        queue_override_status = "hold"
    elif eligibility_decision == "archive_lifecycle_eligibility":
        status = "terminal"
        candidate_mode = "archived_lifecycle_candidate"
        decision = "archive_lifecycle_candidate"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif eligibility_decision == "retire_lifecycle_eligibility":
        status = "terminal"
        candidate_mode = "retired_lifecycle_candidate"
        decision = "retire_lifecycle_candidate"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        candidate_notes.append("fallback_pause")

    candidate_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_eligibility_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_eligibility_decision.changed
        or decision != "pause_lifecycle_candidate"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle candidate converts the final eligibility posture "
        "into the downstream candidate state that queue selection should honor."
    )
    if decision == "keep_lifecycle_candidate":
        rationale = (
            "The proactive lifecycle candidate keeps the lifecycle selectable because "
            "the eligible line should remain a valid proactive candidate."
        )
    elif decision == "buffer_lifecycle_candidate":
        rationale = (
            "The proactive lifecycle candidate keeps the lifecycle buffered because "
            "the line remains a candidate but should wait before re-entering selection."
        )
    elif decision == "pause_lifecycle_candidate":
        rationale = (
            "The proactive lifecycle candidate pauses the lifecycle because the line "
            "should remain retained without active reselection."
        )
    elif decision == "archive_lifecycle_candidate":
        rationale = (
            "The proactive lifecycle candidate archives the lifecycle because the line "
            "reached a clean ending and should no longer be selected."
        )
    elif decision == "retire_lifecycle_candidate":
        rationale = (
            "The proactive lifecycle candidate retires the lifecycle because the line "
            "has reached a terminal stop condition and should no longer be selected."
        )

    return ProactiveLifecycleCandidateDecision(
        status=status,
        candidate_key=candidate_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        eligibility_mode=eligibility_mode,
        candidate_mode=candidate_mode,
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
        selected_strategy_key=(
            lifecycle_eligibility_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_eligibility_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_eligibility_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_eligibility_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        eligibility_decision=eligibility_decision,
        active_sources=_compact(lifecycle_eligibility_decision.active_sources, limit=8),
        candidate_notes=_compact(candidate_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_selectability_decision(
    *,
    lifecycle_candidate_decision: ProactiveLifecycleCandidateDecision,
) -> ProactiveLifecycleSelectabilityDecision:
    current_stage_label = lifecycle_candidate_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_candidate_decision.lifecycle_state or "active"
    candidate_mode = (
        lifecycle_candidate_decision.candidate_mode or "paused_lifecycle_candidate"
    )
    candidate_decision = (
        lifecycle_candidate_decision.decision or "pause_lifecycle_candidate"
    )
    active_stage_label = lifecycle_candidate_decision.active_stage_label
    next_stage_label = lifecycle_candidate_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_candidate_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_candidate_decision.line_state or "steady"
    line_exit_mode = lifecycle_candidate_decision.line_exit_mode or "stay"
    status = lifecycle_candidate_decision.status or "hold"
    selectability_mode = "paused_lifecycle_selectability"
    decision = "pause_lifecycle_selectability"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_candidate_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_candidate_decision.primary_source or "candidate"
    selectability_notes: list[str] = list(lifecycle_candidate_decision.candidate_notes)
    if line_state:
        selectability_notes.append(f"line:{line_state}")
    if line_exit_mode:
        selectability_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        selectability_notes.append(f"active:{active_stage_label}")

    if candidate_decision == "keep_lifecycle_candidate":
        status = "active"
        selectability_mode = "selectable_lifecycle_selectability"
        decision = "keep_lifecycle_selectable"
        actionability = "continue"
        queue_override_status = None
    elif candidate_decision == "buffer_lifecycle_candidate":
        status = "scheduled"
        selectability_mode = "buffered_lifecycle_selectability"
        decision = "buffer_lifecycle_selectability"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif candidate_decision == "pause_lifecycle_candidate":
        status = "hold"
        selectability_mode = "paused_lifecycle_selectability"
        decision = "pause_lifecycle_selectability"
        actionability = "pause"
        queue_override_status = "hold"
    elif candidate_decision == "archive_lifecycle_candidate":
        status = "terminal"
        selectability_mode = "archived_lifecycle_selectability"
        decision = "archive_lifecycle_selectability"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif candidate_decision == "retire_lifecycle_candidate":
        status = "terminal"
        selectability_mode = "retired_lifecycle_selectability"
        decision = "retire_lifecycle_selectability"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        selectability_notes.append("fallback_pause")

    selectability_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_candidate_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_candidate_decision.changed
        or decision != "pause_lifecycle_selectability"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle selectability converts the candidate posture into "
        "the final selectable state that downstream queue selection should honor."
    )
    if decision == "keep_lifecycle_selectable":
        rationale = (
            "The proactive lifecycle selectability keeps the lifecycle selectable "
            "because the candidate line should remain available for reselection."
        )
    elif decision == "buffer_lifecycle_selectability":
        rationale = (
            "The proactive lifecycle selectability keeps the lifecycle buffered "
            "because the line remains selectable later, but not yet."
        )
    elif decision == "pause_lifecycle_selectability":
        rationale = (
            "The proactive lifecycle selectability pauses the lifecycle because the "
            "line should remain present without active reselection."
        )
    elif decision == "archive_lifecycle_selectability":
        rationale = (
            "The proactive lifecycle selectability archives the lifecycle because "
            "the line reached a clean ending and should leave active selection."
        )
    elif decision == "retire_lifecycle_selectability":
        rationale = (
            "The proactive lifecycle selectability retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleSelectabilityDecision(
        status=status,
        selectability_key=selectability_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        candidate_mode=candidate_mode,
        selectability_mode=selectability_mode,
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
        selected_strategy_key=(
            lifecycle_candidate_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_candidate_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_candidate_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_candidate_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        candidate_decision=candidate_decision,
        active_sources=_compact(lifecycle_candidate_decision.active_sources, limit=8),
        selectability_notes=_compact(selectability_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_reentry_decision(
    *,
    lifecycle_selectability_decision: ProactiveLifecycleSelectabilityDecision,
) -> ProactiveLifecycleReentryDecision:
    current_stage_label = (
        lifecycle_selectability_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_selectability_decision.lifecycle_state or "active"
    selectability_mode = (
        lifecycle_selectability_decision.selectability_mode
        or "paused_lifecycle_selectability"
    )
    selectability_decision = (
        lifecycle_selectability_decision.decision or "pause_lifecycle_selectability"
    )
    active_stage_label = lifecycle_selectability_decision.active_stage_label
    next_stage_label = lifecycle_selectability_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_selectability_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_selectability_decision.line_state or "steady"
    line_exit_mode = lifecycle_selectability_decision.line_exit_mode or "stay"
    status = lifecycle_selectability_decision.status or "hold"
    reentry_mode = "paused_lifecycle_reentry"
    decision = "pause_lifecycle_reentry"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_selectability_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_selectability_decision.primary_source or "selectability"
    reentry_notes: list[str] = list(
        lifecycle_selectability_decision.selectability_notes
    )
    if line_state:
        reentry_notes.append(f"line:{line_state}")
    if line_exit_mode:
        reentry_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        reentry_notes.append(f"active:{active_stage_label}")

    if selectability_decision == "keep_lifecycle_selectable":
        status = "active"
        reentry_mode = "reenterable_lifecycle_reentry"
        decision = "keep_lifecycle_reentry"
        actionability = "continue"
        queue_override_status = None
    elif selectability_decision == "buffer_lifecycle_selectability":
        status = "scheduled"
        reentry_mode = "buffered_lifecycle_reentry"
        decision = "buffer_lifecycle_reentry"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif selectability_decision == "pause_lifecycle_selectability":
        status = "hold"
        reentry_mode = "paused_lifecycle_reentry"
        decision = "pause_lifecycle_reentry"
        actionability = "pause"
        queue_override_status = "hold"
    elif selectability_decision == "archive_lifecycle_selectability":
        status = "terminal"
        reentry_mode = "archived_lifecycle_reentry"
        decision = "archive_lifecycle_reentry"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif selectability_decision == "retire_lifecycle_selectability":
        status = "terminal"
        reentry_mode = "retired_lifecycle_reentry"
        decision = "retire_lifecycle_reentry"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        reentry_notes.append("fallback_pause")

    reentry_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_selectability_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_selectability_decision.changed
        or decision != "pause_lifecycle_reentry"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle reentry converts the selectability posture into "
        "the final reentry state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_reentry":
        rationale = (
            "The proactive lifecycle reentry keeps the lifecycle reenterable "
            "because the line should remain available for future proactive return."
        )
    elif decision == "buffer_lifecycle_reentry":
        rationale = (
            "The proactive lifecycle reentry keeps the lifecycle buffered "
            "because the line can return later, but not yet."
        )
    elif decision == "pause_lifecycle_reentry":
        rationale = (
            "The proactive lifecycle reentry pauses the lifecycle because the "
            "line should remain present without immediate return."
        )
    elif decision == "archive_lifecycle_reentry":
        rationale = (
            "The proactive lifecycle reentry archives the lifecycle because "
            "the line reached a clean ending and should leave reentry."
        )
    elif decision == "retire_lifecycle_reentry":
        rationale = (
            "The proactive lifecycle reentry retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleReentryDecision(
        status=status,
        reentry_key=reentry_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        selectability_mode=selectability_mode,
        reentry_mode=reentry_mode,
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
        selected_strategy_key=(
            lifecycle_selectability_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_selectability_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_selectability_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_selectability_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        selectability_decision=selectability_decision,
        active_sources=_compact(
            lifecycle_selectability_decision.active_sources, limit=8
        ),
        reentry_notes=_compact(reentry_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_reactivation_decision(
    *,
    lifecycle_reentry_decision: ProactiveLifecycleReentryDecision,
) -> ProactiveLifecycleReactivationDecision:
    current_stage_label = lifecycle_reentry_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_reentry_decision.lifecycle_state or "active"
    reentry_mode = (
        lifecycle_reentry_decision.reentry_mode or "paused_lifecycle_reentry"
    )
    reentry_decision = (
        lifecycle_reentry_decision.decision or "pause_lifecycle_reentry"
    )
    active_stage_label = lifecycle_reentry_decision.active_stage_label
    next_stage_label = lifecycle_reentry_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_reentry_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_reentry_decision.line_state or "steady"
    line_exit_mode = lifecycle_reentry_decision.line_exit_mode or "stay"
    status = lifecycle_reentry_decision.status or "hold"
    reactivation_mode = "paused_lifecycle_reactivation"
    decision = "pause_lifecycle_reactivation"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_reentry_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_reentry_decision.primary_source or "reentry"
    reactivation_notes: list[str] = list(lifecycle_reentry_decision.reentry_notes)
    if line_state:
        reactivation_notes.append(f"line:{line_state}")
    if line_exit_mode:
        reactivation_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        reactivation_notes.append(f"active:{active_stage_label}")

    if reentry_decision == "keep_lifecycle_reentry":
        status = "active"
        reactivation_mode = "reactivatable_lifecycle_reactivation"
        decision = "keep_lifecycle_reactivation"
        actionability = "continue"
        queue_override_status = None
    elif reentry_decision == "buffer_lifecycle_reentry":
        status = "scheduled"
        reactivation_mode = "buffered_lifecycle_reactivation"
        decision = "buffer_lifecycle_reactivation"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif reentry_decision == "pause_lifecycle_reentry":
        status = "hold"
        reactivation_mode = "paused_lifecycle_reactivation"
        decision = "pause_lifecycle_reactivation"
        actionability = "pause"
        queue_override_status = "hold"
    elif reentry_decision == "archive_lifecycle_reentry":
        status = "terminal"
        reactivation_mode = "archived_lifecycle_reactivation"
        decision = "archive_lifecycle_reactivation"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif reentry_decision == "retire_lifecycle_reentry":
        status = "terminal"
        reactivation_mode = "retired_lifecycle_reactivation"
        decision = "retire_lifecycle_reactivation"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        reactivation_notes.append("fallback_pause")

    reactivation_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_reentry_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_reentry_decision.changed
        or decision != "pause_lifecycle_reactivation"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle reactivation converts the reentry posture into "
        "the final reactivation state that future proactive resumption should honor."
    )
    if decision == "keep_lifecycle_reactivation":
        rationale = (
            "The proactive lifecycle reactivation keeps the lifecycle reactivatable "
            "because the line should remain ready for future proactive return."
        )
    elif decision == "buffer_lifecycle_reactivation":
        rationale = (
            "The proactive lifecycle reactivation keeps the lifecycle buffered "
            "because the line can reactivate later, but not yet."
        )
    elif decision == "pause_lifecycle_reactivation":
        rationale = (
            "The proactive lifecycle reactivation pauses the lifecycle because the "
            "line should remain present without immediate reactivation."
        )
    elif decision == "archive_lifecycle_reactivation":
        rationale = (
            "The proactive lifecycle reactivation archives the lifecycle because "
            "the line reached a clean ending and should leave reactivation."
        )
    elif decision == "retire_lifecycle_reactivation":
        rationale = (
            "The proactive lifecycle reactivation retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleReactivationDecision(
        status=status,
        reactivation_key=reactivation_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        reentry_mode=reentry_mode,
        reactivation_mode=reactivation_mode,
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
        selected_strategy_key=(lifecycle_reentry_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_reentry_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_reentry_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_reentry_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        reentry_decision=reentry_decision,
        active_sources=_compact(lifecycle_reentry_decision.active_sources, limit=8),
        reactivation_notes=_compact(reactivation_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_resumption_decision(
    *,
    lifecycle_reactivation_decision: ProactiveLifecycleReactivationDecision,
) -> ProactiveLifecycleResumptionDecision:
    current_stage_label = (
        lifecycle_reactivation_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_reactivation_decision.lifecycle_state or "active"
    reactivation_mode = (
        lifecycle_reactivation_decision.reactivation_mode
        or "paused_lifecycle_reactivation"
    )
    reactivation_decision = (
        lifecycle_reactivation_decision.decision or "pause_lifecycle_reactivation"
    )
    active_stage_label = lifecycle_reactivation_decision.active_stage_label
    next_stage_label = lifecycle_reactivation_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_reactivation_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_reactivation_decision.line_state or "steady"
    line_exit_mode = lifecycle_reactivation_decision.line_exit_mode or "stay"
    status = lifecycle_reactivation_decision.status or "hold"
    resumption_mode = "paused_lifecycle_resumption"
    decision = "pause_lifecycle_resumption"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_reactivation_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_reactivation_decision.primary_source or "reactivation"
    resumption_notes: list[str] = list(
        lifecycle_reactivation_decision.reactivation_notes
    )
    if line_state:
        resumption_notes.append(f"line:{line_state}")
    if line_exit_mode:
        resumption_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        resumption_notes.append(f"active:{active_stage_label}")

    if reactivation_decision == "keep_lifecycle_reactivation":
        status = "active"
        resumption_mode = "resumable_lifecycle_resumption"
        decision = "keep_lifecycle_resumption"
        actionability = "continue"
        queue_override_status = None
    elif reactivation_decision == "buffer_lifecycle_reactivation":
        status = "scheduled"
        resumption_mode = "buffered_lifecycle_resumption"
        decision = "buffer_lifecycle_resumption"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif reactivation_decision == "pause_lifecycle_reactivation":
        status = "hold"
        resumption_mode = "paused_lifecycle_resumption"
        decision = "pause_lifecycle_resumption"
        actionability = "pause"
        queue_override_status = "hold"
    elif reactivation_decision == "archive_lifecycle_reactivation":
        status = "terminal"
        resumption_mode = "archived_lifecycle_resumption"
        decision = "archive_lifecycle_resumption"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif reactivation_decision == "retire_lifecycle_reactivation":
        status = "terminal"
        resumption_mode = "retired_lifecycle_resumption"
        decision = "retire_lifecycle_resumption"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        resumption_notes.append("fallback_pause")

    resumption_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_reactivation_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_reactivation_decision.changed
        or decision != "pause_lifecycle_resumption"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle resumption converts the reactivation posture into "
        "the final resumption state that future proactive resumption should honor."
    )
    if decision == "keep_lifecycle_resumption":
        rationale = (
            "The proactive lifecycle resumption keeps the lifecycle resumable "
            "because the line should remain ready for future proactive resumption."
        )
    elif decision == "buffer_lifecycle_resumption":
        rationale = (
            "The proactive lifecycle resumption keeps the lifecycle buffered "
            "because the line can resume later, but not yet."
        )
    elif decision == "pause_lifecycle_resumption":
        rationale = (
            "The proactive lifecycle resumption pauses the lifecycle because the "
            "line should remain present without immediate resumption."
        )
    elif decision == "archive_lifecycle_resumption":
        rationale = (
            "The proactive lifecycle resumption archives the lifecycle because "
            "the line reached a clean ending and should leave resumption."
        )
    elif decision == "retire_lifecycle_resumption":
        rationale = (
            "The proactive lifecycle resumption retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleResumptionDecision(
        status=status,
        resumption_key=resumption_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        reactivation_mode=reactivation_mode,
        resumption_mode=resumption_mode,
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
        selected_strategy_key=(
            lifecycle_reactivation_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_reactivation_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_reactivation_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_reactivation_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        reactivation_decision=reactivation_decision,
        active_sources=_compact(
            lifecycle_reactivation_decision.active_sources,
            limit=8,
        ),
        resumption_notes=_compact(resumption_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_readiness_decision(
    *,
    lifecycle_resumption_decision: ProactiveLifecycleResumptionDecision,
) -> ProactiveLifecycleReadinessDecision:
    current_stage_label = lifecycle_resumption_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_resumption_decision.lifecycle_state or "active"
    resumption_mode = (
        lifecycle_resumption_decision.resumption_mode or "paused_lifecycle_resumption"
    )
    resumption_decision = (
        lifecycle_resumption_decision.decision or "pause_lifecycle_resumption"
    )
    active_stage_label = lifecycle_resumption_decision.active_stage_label
    next_stage_label = lifecycle_resumption_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_resumption_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_resumption_decision.line_state or "steady"
    line_exit_mode = lifecycle_resumption_decision.line_exit_mode or "stay"
    status = lifecycle_resumption_decision.status or "hold"
    readiness_mode = "paused_lifecycle_readiness"
    decision = "pause_lifecycle_readiness"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_resumption_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_resumption_decision.primary_source or "resumption"
    readiness_notes: list[str] = list(lifecycle_resumption_decision.resumption_notes)
    if line_state:
        readiness_notes.append(f"line:{line_state}")
    if line_exit_mode:
        readiness_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        readiness_notes.append(f"active:{active_stage_label}")

    if resumption_decision == "keep_lifecycle_resumption":
        status = "active"
        readiness_mode = "ready_lifecycle_readiness"
        decision = "keep_lifecycle_readiness"
        actionability = "continue"
        queue_override_status = None
    elif resumption_decision == "buffer_lifecycle_resumption":
        status = "scheduled"
        readiness_mode = "buffered_lifecycle_readiness"
        decision = "buffer_lifecycle_readiness"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif resumption_decision == "pause_lifecycle_resumption":
        status = "hold"
        readiness_mode = "paused_lifecycle_readiness"
        decision = "pause_lifecycle_readiness"
        actionability = "pause"
        queue_override_status = "hold"
    elif resumption_decision == "archive_lifecycle_resumption":
        status = "terminal"
        readiness_mode = "archived_lifecycle_readiness"
        decision = "archive_lifecycle_readiness"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif resumption_decision == "retire_lifecycle_resumption":
        status = "terminal"
        readiness_mode = "retired_lifecycle_readiness"
        decision = "retire_lifecycle_readiness"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        readiness_notes.append("fallback_pause")

    readiness_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_resumption_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_resumption_decision.changed
        or decision != "pause_lifecycle_readiness"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle readiness converts the resumption posture into "
        "the final readiness state that future proactive return should honor."
    )
    if decision == "keep_lifecycle_readiness":
        rationale = (
            "The proactive lifecycle readiness keeps the lifecycle ready "
            "because the line should remain ready for future proactive resumption."
        )
    elif decision == "buffer_lifecycle_readiness":
        rationale = (
            "The proactive lifecycle readiness keeps the lifecycle buffered "
            "because the line can become ready later, but not yet."
        )
    elif decision == "pause_lifecycle_readiness":
        rationale = (
            "The proactive lifecycle readiness pauses the lifecycle because the "
            "line should remain present without immediate readiness."
        )
    elif decision == "archive_lifecycle_readiness":
        rationale = (
            "The proactive lifecycle readiness archives the lifecycle because "
            "the line reached a clean ending and should leave readiness."
        )
    elif decision == "retire_lifecycle_readiness":
        rationale = (
            "The proactive lifecycle readiness retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleReadinessDecision(
        status=status,
        readiness_key=readiness_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        resumption_mode=resumption_mode,
        readiness_mode=readiness_mode,
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
        selected_strategy_key=(
            lifecycle_resumption_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_resumption_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_resumption_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_resumption_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        resumption_decision=resumption_decision,
        active_sources=_compact(
            lifecycle_resumption_decision.active_sources,
            limit=8,
        ),
        readiness_notes=_compact(readiness_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_arming_decision(
    *,
    lifecycle_readiness_decision: ProactiveLifecycleReadinessDecision,
) -> ProactiveLifecycleArmingDecision:
    current_stage_label = lifecycle_readiness_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_readiness_decision.lifecycle_state or "active"
    readiness_mode = (
        lifecycle_readiness_decision.readiness_mode or "paused_lifecycle_readiness"
    )
    readiness_decision = (
        lifecycle_readiness_decision.decision or "pause_lifecycle_readiness"
    )
    active_stage_label = lifecycle_readiness_decision.active_stage_label
    next_stage_label = lifecycle_readiness_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_readiness_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_readiness_decision.line_state or "steady"
    line_exit_mode = lifecycle_readiness_decision.line_exit_mode or "stay"
    status = lifecycle_readiness_decision.status or "hold"
    arming_mode = "paused_lifecycle_arming"
    decision = "pause_lifecycle_arming"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_readiness_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_readiness_decision.primary_source or "readiness"
    arming_notes: list[str] = list(lifecycle_readiness_decision.readiness_notes)
    if line_state:
        arming_notes.append(f"line:{line_state}")
    if line_exit_mode:
        arming_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        arming_notes.append(f"active:{active_stage_label}")

    if readiness_decision == "keep_lifecycle_readiness":
        status = "active"
        arming_mode = "armed_lifecycle_arming"
        decision = "keep_lifecycle_arming"
        actionability = "continue"
        queue_override_status = None
    elif readiness_decision == "buffer_lifecycle_readiness":
        status = "scheduled"
        arming_mode = "buffered_lifecycle_arming"
        decision = "buffer_lifecycle_arming"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif readiness_decision == "pause_lifecycle_readiness":
        status = "hold"
        arming_mode = "paused_lifecycle_arming"
        decision = "pause_lifecycle_arming"
        actionability = "pause"
        queue_override_status = "hold"
    elif readiness_decision == "archive_lifecycle_readiness":
        status = "terminal"
        arming_mode = "archived_lifecycle_arming"
        decision = "archive_lifecycle_arming"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif readiness_decision == "retire_lifecycle_readiness":
        status = "terminal"
        arming_mode = "retired_lifecycle_arming"
        decision = "retire_lifecycle_arming"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        arming_notes.append("fallback_pause")

    arming_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_readiness_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_readiness_decision.changed
        or decision != "pause_lifecycle_arming"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle arming converts the readiness posture into "
        "the final armed state that future proactive return should honor."
    )
    if decision == "keep_lifecycle_arming":
        rationale = (
            "The proactive lifecycle arming keeps the lifecycle armed because "
            "the line should remain ready for future proactive return."
        )
    elif decision == "buffer_lifecycle_arming":
        rationale = (
            "The proactive lifecycle arming keeps the lifecycle buffered because "
            "the line can become armed later, but not yet."
        )
    elif decision == "pause_lifecycle_arming":
        rationale = (
            "The proactive lifecycle arming pauses the lifecycle because the "
            "line should remain present without immediate arming."
        )
    elif decision == "archive_lifecycle_arming":
        rationale = (
            "The proactive lifecycle arming archives the lifecycle because "
            "the line reached a clean ending and should leave arming."
        )
    elif decision == "retire_lifecycle_arming":
        rationale = (
            "The proactive lifecycle arming retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleArmingDecision(
        status=status,
        arming_key=arming_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        readiness_mode=readiness_mode,
        arming_mode=arming_mode,
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
        selected_strategy_key=(
            lifecycle_readiness_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_readiness_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_readiness_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_readiness_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        readiness_decision=readiness_decision,
        active_sources=_compact(
            lifecycle_readiness_decision.active_sources,
            limit=8,
        ),
        arming_notes=_compact(arming_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_trigger_decision(
    *,
    lifecycle_arming_decision: ProactiveLifecycleArmingDecision,
) -> ProactiveLifecycleTriggerDecision:
    current_stage_label = lifecycle_arming_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_arming_decision.lifecycle_state or "active"
    arming_mode = lifecycle_arming_decision.arming_mode or "paused_lifecycle_arming"
    arming_decision = lifecycle_arming_decision.decision or "pause_lifecycle_arming"
    active_stage_label = lifecycle_arming_decision.active_stage_label
    next_stage_label = lifecycle_arming_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_arming_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_arming_decision.line_state or "steady"
    line_exit_mode = lifecycle_arming_decision.line_exit_mode or "stay"
    status = lifecycle_arming_decision.status or "hold"
    trigger_mode = "paused_lifecycle_trigger"
    decision = "pause_lifecycle_trigger"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_arming_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_arming_decision.primary_source or "arming"
    trigger_notes: list[str] = list(lifecycle_arming_decision.arming_notes)
    if line_state:
        trigger_notes.append(f"line:{line_state}")
    if line_exit_mode:
        trigger_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        trigger_notes.append(f"active:{active_stage_label}")

    if arming_decision == "keep_lifecycle_arming":
        status = "active"
        trigger_mode = "triggerable_lifecycle_trigger"
        decision = "keep_lifecycle_trigger"
        actionability = "continue"
        queue_override_status = None
    elif arming_decision == "buffer_lifecycle_arming":
        status = "scheduled"
        trigger_mode = "buffered_lifecycle_trigger"
        decision = "buffer_lifecycle_trigger"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif arming_decision == "pause_lifecycle_arming":
        status = "hold"
        trigger_mode = "paused_lifecycle_trigger"
        decision = "pause_lifecycle_trigger"
        actionability = "pause"
        queue_override_status = "hold"
    elif arming_decision == "archive_lifecycle_arming":
        status = "terminal"
        trigger_mode = "archived_lifecycle_trigger"
        decision = "archive_lifecycle_trigger"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif arming_decision == "retire_lifecycle_arming":
        status = "terminal"
        trigger_mode = "retired_lifecycle_trigger"
        decision = "retire_lifecycle_trigger"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        trigger_notes.append("fallback_pause")

    trigger_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_arming_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_arming_decision.changed
        or decision != "pause_lifecycle_trigger"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle trigger converts the arming posture into "
        "the final triggerable state that future proactive return should honor."
    )
    if decision == "keep_lifecycle_trigger":
        rationale = (
            "The proactive lifecycle trigger keeps the lifecycle triggerable "
            "because the line should remain armed for future proactive return."
        )
    elif decision == "buffer_lifecycle_trigger":
        rationale = (
            "The proactive lifecycle trigger keeps the lifecycle buffered because "
            "the line can become triggerable later, but not yet."
        )
    elif decision == "pause_lifecycle_trigger":
        rationale = (
            "The proactive lifecycle trigger pauses the lifecycle because the "
            "line should remain present without immediate triggering."
        )
    elif decision == "archive_lifecycle_trigger":
        rationale = (
            "The proactive lifecycle trigger archives the lifecycle because "
            "the line reached a clean ending and should leave triggering."
        )
    elif decision == "retire_lifecycle_trigger":
        rationale = (
            "The proactive lifecycle trigger retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleTriggerDecision(
        status=status,
        trigger_key=trigger_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        arming_mode=arming_mode,
        trigger_mode=trigger_mode,
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
        selected_strategy_key=(lifecycle_arming_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_arming_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_arming_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_arming_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        arming_decision=arming_decision,
        active_sources=_compact(lifecycle_arming_decision.active_sources, limit=8),
        trigger_notes=_compact(trigger_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_launch_decision(
    *,
    lifecycle_trigger_decision: ProactiveLifecycleTriggerDecision,
) -> ProactiveLifecycleLaunchDecision:
    current_stage_label = lifecycle_trigger_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_trigger_decision.lifecycle_state or "active"
    trigger_mode = lifecycle_trigger_decision.trigger_mode or "paused_lifecycle_trigger"
    trigger_decision = lifecycle_trigger_decision.decision or "pause_lifecycle_trigger"
    active_stage_label = lifecycle_trigger_decision.active_stage_label
    next_stage_label = lifecycle_trigger_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_trigger_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_trigger_decision.line_state or "steady"
    line_exit_mode = lifecycle_trigger_decision.line_exit_mode or "stay"
    status = lifecycle_trigger_decision.status or "hold"
    launch_mode = "paused_lifecycle_launch"
    decision = "pause_lifecycle_launch"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_trigger_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_trigger_decision.primary_source or "trigger"
    launch_notes: list[str] = list(lifecycle_trigger_decision.trigger_notes)
    if line_state:
        launch_notes.append(f"line:{line_state}")
    if line_exit_mode:
        launch_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        launch_notes.append(f"active:{active_stage_label}")

    if trigger_decision == "keep_lifecycle_trigger":
        status = "active"
        launch_mode = "launchable_lifecycle_launch"
        decision = "keep_lifecycle_launch"
        actionability = "continue"
        queue_override_status = None
    elif trigger_decision == "buffer_lifecycle_trigger":
        status = "scheduled"
        launch_mode = "buffered_lifecycle_launch"
        decision = "buffer_lifecycle_launch"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif trigger_decision == "pause_lifecycle_trigger":
        status = "hold"
        launch_mode = "paused_lifecycle_launch"
        decision = "pause_lifecycle_launch"
        actionability = "pause"
        queue_override_status = "hold"
    elif trigger_decision == "archive_lifecycle_trigger":
        status = "terminal"
        launch_mode = "archived_lifecycle_launch"
        decision = "archive_lifecycle_launch"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif trigger_decision == "retire_lifecycle_trigger":
        status = "terminal"
        launch_mode = "retired_lifecycle_launch"
        decision = "retire_lifecycle_launch"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        launch_notes.append("fallback_pause")

    launch_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_trigger_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_trigger_decision.changed
        or decision != "pause_lifecycle_launch"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle launch converts the trigger posture into "
        "the final launchable state that future proactive return should honor."
    )
    if decision == "keep_lifecycle_launch":
        rationale = (
            "The proactive lifecycle launch keeps the lifecycle launchable "
            "because the line should remain trigger-ready for future proactive return."
        )
    elif decision == "buffer_lifecycle_launch":
        rationale = (
            "The proactive lifecycle launch keeps the lifecycle buffered because "
            "the line can become launchable later, but not yet."
        )
    elif decision == "pause_lifecycle_launch":
        rationale = (
            "The proactive lifecycle launch pauses the lifecycle because the "
            "line should remain present without immediate launch."
        )
    elif decision == "archive_lifecycle_launch":
        rationale = (
            "The proactive lifecycle launch archives the lifecycle because "
            "the line reached a clean ending and should leave launch."
        )
    elif decision == "retire_lifecycle_launch":
        rationale = (
            "The proactive lifecycle launch retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleLaunchDecision(
        status=status,
        launch_key=launch_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        trigger_mode=trigger_mode,
        launch_mode=launch_mode,
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
        selected_strategy_key=(lifecycle_trigger_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_trigger_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_trigger_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_trigger_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        trigger_decision=trigger_decision,
        active_sources=_compact(lifecycle_trigger_decision.active_sources, limit=8),
        launch_notes=_compact(launch_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_handoff_decision(
    *,
    lifecycle_launch_decision: ProactiveLifecycleLaunchDecision,
) -> ProactiveLifecycleHandoffDecision:
    current_stage_label = lifecycle_launch_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_launch_decision.lifecycle_state or "active"
    launch_mode = lifecycle_launch_decision.launch_mode or "paused_lifecycle_launch"
    launch_decision = lifecycle_launch_decision.decision or "pause_lifecycle_launch"
    active_stage_label = lifecycle_launch_decision.active_stage_label
    next_stage_label = lifecycle_launch_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_launch_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_launch_decision.line_state or "steady"
    line_exit_mode = lifecycle_launch_decision.line_exit_mode or "stay"
    status = lifecycle_launch_decision.status or "hold"
    handoff_mode = "paused_lifecycle_handoff"
    decision = "pause_lifecycle_handoff"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_launch_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_launch_decision.primary_source or "launch"
    handoff_notes: list[str] = list(lifecycle_launch_decision.launch_notes)
    if line_state:
        handoff_notes.append(f"line:{line_state}")
    if line_exit_mode:
        handoff_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        handoff_notes.append(f"active:{active_stage_label}")

    if launch_decision == "keep_lifecycle_launch":
        status = "active"
        handoff_mode = "handoff_ready_lifecycle_handoff"
        decision = "keep_lifecycle_handoff"
        actionability = "continue"
        queue_override_status = None
    elif launch_decision == "buffer_lifecycle_launch":
        status = "scheduled"
        handoff_mode = "buffered_lifecycle_handoff"
        decision = "buffer_lifecycle_handoff"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif launch_decision == "pause_lifecycle_launch":
        status = "hold"
        handoff_mode = "paused_lifecycle_handoff"
        decision = "pause_lifecycle_handoff"
        actionability = "pause"
        queue_override_status = "hold"
    elif launch_decision == "archive_lifecycle_launch":
        status = "terminal"
        handoff_mode = "archived_lifecycle_handoff"
        decision = "archive_lifecycle_handoff"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif launch_decision == "retire_lifecycle_launch":
        status = "terminal"
        handoff_mode = "retired_lifecycle_handoff"
        decision = "retire_lifecycle_handoff"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        handoff_notes.append("fallback_pause")

    handoff_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_launch_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_launch_decision.changed
        or decision != "pause_lifecycle_handoff"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle handoff converts the launch posture into "
        "the final handoff-ready state that future proactive continuation should honor."
    )
    if decision == "keep_lifecycle_handoff":
        rationale = (
            "The proactive lifecycle handoff keeps the lifecycle handoff-ready "
            "because the line should remain ready for future proactive continuation."
        )
    elif decision == "buffer_lifecycle_handoff":
        rationale = (
            "The proactive lifecycle handoff keeps the lifecycle buffered because "
            "the line can become handoff-ready later, but not yet."
        )
    elif decision == "pause_lifecycle_handoff":
        rationale = (
            "The proactive lifecycle handoff pauses the lifecycle because the "
            "line should remain present without immediate handoff."
        )
    elif decision == "archive_lifecycle_handoff":
        rationale = (
            "The proactive lifecycle handoff archives the lifecycle because "
            "the line reached a clean ending and should leave handoff."
        )
    elif decision == "retire_lifecycle_handoff":
        rationale = (
            "The proactive lifecycle handoff retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleHandoffDecision(
        status=status,
        handoff_key=handoff_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        launch_mode=launch_mode,
        handoff_mode=handoff_mode,
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
        selected_strategy_key=(lifecycle_launch_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_launch_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_launch_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_launch_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        launch_decision=launch_decision,
        active_sources=_compact(lifecycle_launch_decision.active_sources, limit=8),
        handoff_notes=_compact(handoff_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_continuation_decision(
    *,
    lifecycle_handoff_decision: ProactiveLifecycleHandoffDecision,
) -> ProactiveLifecycleContinuationDecision:
    current_stage_label = lifecycle_handoff_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_handoff_decision.lifecycle_state or "active"
    handoff_mode = lifecycle_handoff_decision.handoff_mode or "paused_lifecycle_handoff"
    handoff_decision = lifecycle_handoff_decision.decision or "pause_lifecycle_handoff"
    active_stage_label = lifecycle_handoff_decision.active_stage_label
    next_stage_label = lifecycle_handoff_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_handoff_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_handoff_decision.line_state or "steady"
    line_exit_mode = lifecycle_handoff_decision.line_exit_mode or "stay"
    status = lifecycle_handoff_decision.status or "hold"
    continuation_mode = "paused_lifecycle_continuation"
    decision = "pause_lifecycle_continuation"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_handoff_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_handoff_decision.primary_source or "handoff"
    continuation_notes: list[str] = list(lifecycle_handoff_decision.handoff_notes)
    if line_state:
        continuation_notes.append(f"line:{line_state}")
    if line_exit_mode:
        continuation_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        continuation_notes.append(f"active:{active_stage_label}")

    if handoff_decision == "keep_lifecycle_handoff":
        status = "active"
        continuation_mode = "continuable_lifecycle_continuation"
        decision = "keep_lifecycle_continuation"
        actionability = "continue"
        queue_override_status = None
    elif handoff_decision == "buffer_lifecycle_handoff":
        status = "scheduled"
        continuation_mode = "buffered_lifecycle_continuation"
        decision = "buffer_lifecycle_continuation"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif handoff_decision == "pause_lifecycle_handoff":
        status = "hold"
        continuation_mode = "paused_lifecycle_continuation"
        decision = "pause_lifecycle_continuation"
        actionability = "pause"
        queue_override_status = "hold"
    elif handoff_decision == "archive_lifecycle_handoff":
        status = "terminal"
        continuation_mode = "archived_lifecycle_continuation"
        decision = "archive_lifecycle_continuation"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif handoff_decision == "retire_lifecycle_handoff":
        status = "terminal"
        continuation_mode = "retired_lifecycle_continuation"
        decision = "retire_lifecycle_continuation"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        continuation_notes.append("fallback_pause")

    continuation_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_handoff_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_handoff_decision.changed
        or decision != "pause_lifecycle_continuation"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle continuation converts the handoff posture into "
        "the final continuable state that future proactive continuation should honor."
    )
    if decision == "keep_lifecycle_continuation":
        rationale = (
            "The proactive lifecycle continuation keeps the lifecycle continuable "
            "because the line should remain ready for future proactive continuation."
        )
    elif decision == "buffer_lifecycle_continuation":
        rationale = (
            "The proactive lifecycle continuation keeps the lifecycle buffered because "
            "the line can become continuable later, but not yet."
        )
    elif decision == "pause_lifecycle_continuation":
        rationale = (
            "The proactive lifecycle continuation pauses the lifecycle because the "
            "line should remain present without immediate continuation."
        )
    elif decision == "archive_lifecycle_continuation":
        rationale = (
            "The proactive lifecycle continuation archives the lifecycle because "
            "the line reached a clean ending and should leave continuation."
        )
    elif decision == "retire_lifecycle_continuation":
        rationale = (
            "The proactive lifecycle continuation retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleContinuationDecision(
        status=status,
        continuation_key=continuation_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        handoff_mode=handoff_mode,
        continuation_mode=continuation_mode,
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
        selected_strategy_key=(lifecycle_handoff_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_handoff_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_handoff_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_handoff_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        handoff_decision=handoff_decision,
        active_sources=_compact(lifecycle_handoff_decision.active_sources, limit=8),
        continuation_notes=_compact(continuation_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_sustainment_decision(
    *,
    lifecycle_continuation_decision: ProactiveLifecycleContinuationDecision,
) -> ProactiveLifecycleSustainmentDecision:
    current_stage_label = (
        lifecycle_continuation_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_continuation_decision.lifecycle_state or "active"
    continuation_mode = (
        lifecycle_continuation_decision.continuation_mode
        or "paused_lifecycle_continuation"
    )
    continuation_decision = (
        lifecycle_continuation_decision.decision or "pause_lifecycle_continuation"
    )
    active_stage_label = lifecycle_continuation_decision.active_stage_label
    next_stage_label = lifecycle_continuation_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_continuation_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_continuation_decision.line_state or "steady"
    line_exit_mode = lifecycle_continuation_decision.line_exit_mode or "stay"
    status = lifecycle_continuation_decision.status or "hold"
    sustainment_mode = "paused_lifecycle_sustainment"
    decision = "pause_lifecycle_sustainment"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_continuation_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_continuation_decision.primary_source or "continuation"
    sustainment_notes: list[str] = list(
        lifecycle_continuation_decision.continuation_notes
    )
    if line_state:
        sustainment_notes.append(f"line:{line_state}")
    if line_exit_mode:
        sustainment_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        sustainment_notes.append(f"active:{active_stage_label}")

    if continuation_decision == "keep_lifecycle_continuation":
        status = "active"
        sustainment_mode = "sustainable_lifecycle_sustainment"
        decision = "sustain_lifecycle_sustainment"
        actionability = "sustain"
        queue_override_status = None
    elif continuation_decision == "buffer_lifecycle_continuation":
        status = "scheduled"
        sustainment_mode = "buffered_lifecycle_sustainment"
        decision = "buffer_lifecycle_sustainment"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif continuation_decision == "pause_lifecycle_continuation":
        status = "hold"
        sustainment_mode = "paused_lifecycle_sustainment"
        decision = "pause_lifecycle_sustainment"
        actionability = "pause"
        queue_override_status = "hold"
    elif continuation_decision == "archive_lifecycle_continuation":
        status = "terminal"
        sustainment_mode = "archived_lifecycle_sustainment"
        decision = "archive_lifecycle_sustainment"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif continuation_decision == "retire_lifecycle_continuation":
        status = "terminal"
        sustainment_mode = "retired_lifecycle_sustainment"
        decision = "retire_lifecycle_sustainment"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        sustainment_notes.append("fallback_pause")

    sustainment_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_continuation_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_continuation_decision.changed
        or decision != "pause_lifecycle_sustainment"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle sustainment converts the continuation posture into "
        "the final sustainable state that future proactive sustainment should honor."
    )
    if decision == "sustain_lifecycle_sustainment":
        rationale = (
            "The proactive lifecycle sustainment keeps the lifecycle sustainable "
            "because the line should remain durably available for future proactive continuation."
        )
    elif decision == "buffer_lifecycle_sustainment":
        rationale = (
            "The proactive lifecycle sustainment keeps the lifecycle buffered because "
            "the line can become sustainably continuable later, but not yet."
        )
    elif decision == "pause_lifecycle_sustainment":
        rationale = (
            "The proactive lifecycle sustainment pauses the lifecycle because the "
            "line should remain present without immediate sustainment."
        )
    elif decision == "archive_lifecycle_sustainment":
        rationale = (
            "The proactive lifecycle sustainment archives the lifecycle because "
            "the line reached a clean ending and should leave sustainment."
        )
    elif decision == "retire_lifecycle_sustainment":
        rationale = (
            "The proactive lifecycle sustainment retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleSustainmentDecision(
        status=status,
        sustainment_key=sustainment_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        continuation_mode=continuation_mode,
        sustainment_mode=sustainment_mode,
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
        selected_strategy_key=(
            lifecycle_continuation_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_continuation_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_continuation_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_continuation_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        continuation_decision=continuation_decision,
        active_sources=_compact(lifecycle_continuation_decision.active_sources, limit=8),
        sustainment_notes=_compact(sustainment_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_stewardship_decision(
    *,
    lifecycle_sustainment_decision: ProactiveLifecycleSustainmentDecision,
) -> ProactiveLifecycleStewardshipDecision:
    current_stage_label = lifecycle_sustainment_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_sustainment_decision.lifecycle_state or "active"
    sustainment_mode = (
        lifecycle_sustainment_decision.sustainment_mode
        or "paused_lifecycle_sustainment"
    )
    sustainment_decision = (
        lifecycle_sustainment_decision.decision or "pause_lifecycle_sustainment"
    )
    active_stage_label = lifecycle_sustainment_decision.active_stage_label
    next_stage_label = lifecycle_sustainment_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_sustainment_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_sustainment_decision.line_state or "steady"
    line_exit_mode = lifecycle_sustainment_decision.line_exit_mode or "stay"
    status = lifecycle_sustainment_decision.status or "hold"
    stewardship_mode = "paused_lifecycle_stewardship"
    decision = "pause_lifecycle_stewardship"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_sustainment_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_sustainment_decision.primary_source or "sustainment"
    stewardship_notes: list[str] = list(
        lifecycle_sustainment_decision.sustainment_notes
    )
    if line_state:
        stewardship_notes.append(f"line:{line_state}")
    if line_exit_mode:
        stewardship_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        stewardship_notes.append(f"active:{active_stage_label}")

    if sustainment_decision == "sustain_lifecycle_sustainment":
        status = "active"
        stewardship_mode = "stewarded_lifecycle_stewardship"
        decision = "steward_lifecycle_stewardship"
        actionability = "steward"
        queue_override_status = None
    elif sustainment_decision == "buffer_lifecycle_sustainment":
        status = "scheduled"
        stewardship_mode = "buffered_lifecycle_stewardship"
        decision = "buffer_lifecycle_stewardship"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif sustainment_decision == "pause_lifecycle_sustainment":
        status = "hold"
        stewardship_mode = "paused_lifecycle_stewardship"
        decision = "pause_lifecycle_stewardship"
        actionability = "pause"
        queue_override_status = "hold"
    elif sustainment_decision == "archive_lifecycle_sustainment":
        status = "terminal"
        stewardship_mode = "archived_lifecycle_stewardship"
        decision = "archive_lifecycle_stewardship"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif sustainment_decision == "retire_lifecycle_sustainment":
        status = "terminal"
        stewardship_mode = "retired_lifecycle_stewardship"
        decision = "retire_lifecycle_stewardship"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        stewardship_notes.append("fallback_pause")

    stewardship_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_sustainment_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_sustainment_decision.changed
        or decision != "pause_lifecycle_stewardship"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle stewardship converts the sustainment posture into "
        "the final stewarded state that future proactive stewardship should honor."
    )
    if decision == "steward_lifecycle_stewardship":
        rationale = (
            "The proactive lifecycle stewardship keeps the lifecycle stewarded "
            "because the line should remain responsibly available for future proactive return."
        )
    elif decision == "buffer_lifecycle_stewardship":
        rationale = (
            "The proactive lifecycle stewardship keeps the lifecycle buffered because "
            "the line can become stewarded later, but not yet."
        )
    elif decision == "pause_lifecycle_stewardship":
        rationale = (
            "The proactive lifecycle stewardship pauses the lifecycle because the "
            "line should remain present without immediate stewardship."
        )
    elif decision == "archive_lifecycle_stewardship":
        rationale = (
            "The proactive lifecycle stewardship archives the lifecycle because "
            "the line reached a clean ending and should leave stewardship."
        )
    elif decision == "retire_lifecycle_stewardship":
        rationale = (
            "The proactive lifecycle stewardship retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleStewardshipDecision(
        status=status,
        stewardship_key=stewardship_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        sustainment_mode=sustainment_mode,
        stewardship_mode=stewardship_mode,
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
        selected_strategy_key=(lifecycle_sustainment_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_sustainment_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_sustainment_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_sustainment_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        sustainment_decision=sustainment_decision,
        active_sources=_compact(lifecycle_sustainment_decision.active_sources, limit=8),
        stewardship_notes=_compact(stewardship_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_guardianship_decision(
    *,
    lifecycle_stewardship_decision: ProactiveLifecycleStewardshipDecision,
) -> ProactiveLifecycleGuardianshipDecision:
    current_stage_label = lifecycle_stewardship_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_stewardship_decision.lifecycle_state or "active"
    stewardship_mode = (
        lifecycle_stewardship_decision.stewardship_mode
        or "paused_lifecycle_stewardship"
    )
    stewardship_decision = (
        lifecycle_stewardship_decision.decision or "pause_lifecycle_stewardship"
    )
    active_stage_label = lifecycle_stewardship_decision.active_stage_label
    next_stage_label = lifecycle_stewardship_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_stewardship_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_stewardship_decision.line_state or "steady"
    line_exit_mode = lifecycle_stewardship_decision.line_exit_mode or "stay"
    status = lifecycle_stewardship_decision.status or "hold"
    guardianship_mode = "paused_lifecycle_guardianship"
    decision = "pause_lifecycle_guardianship"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_stewardship_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_stewardship_decision.primary_source or "stewardship"
    guardianship_notes: list[str] = list(
        lifecycle_stewardship_decision.stewardship_notes
    )
    if line_state:
        guardianship_notes.append(f"line:{line_state}")
    if line_exit_mode:
        guardianship_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        guardianship_notes.append(f"active:{active_stage_label}")

    if stewardship_decision == "steward_lifecycle_stewardship":
        status = "active"
        guardianship_mode = "guarded_lifecycle_guardianship"
        decision = "guard_lifecycle_guardianship"
        actionability = "guard"
        queue_override_status = None
    elif stewardship_decision == "buffer_lifecycle_stewardship":
        status = "scheduled"
        guardianship_mode = "buffered_lifecycle_guardianship"
        decision = "buffer_lifecycle_guardianship"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif stewardship_decision == "pause_lifecycle_stewardship":
        status = "hold"
        guardianship_mode = "paused_lifecycle_guardianship"
        decision = "pause_lifecycle_guardianship"
        actionability = "pause"
        queue_override_status = "hold"
    elif stewardship_decision == "archive_lifecycle_stewardship":
        status = "terminal"
        guardianship_mode = "archived_lifecycle_guardianship"
        decision = "archive_lifecycle_guardianship"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif stewardship_decision == "retire_lifecycle_stewardship":
        status = "terminal"
        guardianship_mode = "retired_lifecycle_guardianship"
        decision = "retire_lifecycle_guardianship"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        guardianship_notes.append("fallback_pause")

    guardianship_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_stewardship_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_stewardship_decision.changed
        or decision != "pause_lifecycle_guardianship"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle guardianship converts the stewardship posture into "
        "the final guarded state that future proactive guardianship should honor."
    )
    if decision == "guard_lifecycle_guardianship":
        rationale = (
            "The proactive lifecycle guardianship keeps the lifecycle guarded "
            "because the line should remain safely protected for future proactive return."
        )
    elif decision == "buffer_lifecycle_guardianship":
        rationale = (
            "The proactive lifecycle guardianship keeps the lifecycle buffered because "
            "the line can become guarded later, but not yet."
        )
    elif decision == "pause_lifecycle_guardianship":
        rationale = (
            "The proactive lifecycle guardianship pauses the lifecycle because the "
            "line should remain present without immediate guardianship."
        )
    elif decision == "archive_lifecycle_guardianship":
        rationale = (
            "The proactive lifecycle guardianship archives the lifecycle because "
            "the line reached a clean ending and should leave guardianship."
        )
    elif decision == "retire_lifecycle_guardianship":
        rationale = (
            "The proactive lifecycle guardianship retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleGuardianshipDecision(
        status=status,
        guardianship_key=guardianship_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        stewardship_mode=stewardship_mode,
        guardianship_mode=guardianship_mode,
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
        selected_strategy_key=(lifecycle_stewardship_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_stewardship_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_stewardship_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_stewardship_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        stewardship_decision=stewardship_decision,
        active_sources=_compact(lifecycle_stewardship_decision.active_sources, limit=8),
        guardianship_notes=_compact(guardianship_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_oversight_decision(
    *,
    lifecycle_guardianship_decision: ProactiveLifecycleGuardianshipDecision,
) -> ProactiveLifecycleOversightDecision:
    current_stage_label = lifecycle_guardianship_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_guardianship_decision.lifecycle_state or "active"
    guardianship_mode = (
        lifecycle_guardianship_decision.guardianship_mode
        or "paused_lifecycle_guardianship"
    )
    guardianship_decision = (
        lifecycle_guardianship_decision.decision or "pause_lifecycle_guardianship"
    )
    active_stage_label = lifecycle_guardianship_decision.active_stage_label
    next_stage_label = lifecycle_guardianship_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_guardianship_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_guardianship_decision.line_state or "steady"
    line_exit_mode = lifecycle_guardianship_decision.line_exit_mode or "stay"
    status = lifecycle_guardianship_decision.status or "hold"
    oversight_mode = "paused_lifecycle_oversight"
    decision = "pause_lifecycle_oversight"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_guardianship_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_guardianship_decision.primary_source or "guardianship"
    oversight_notes: list[str] = list(
        lifecycle_guardianship_decision.guardianship_notes
    )
    if line_state:
        oversight_notes.append(f"line:{line_state}")
    if line_exit_mode:
        oversight_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        oversight_notes.append(f"active:{active_stage_label}")

    if guardianship_decision == "guard_lifecycle_guardianship":
        status = "active"
        oversight_mode = "overseen_lifecycle_oversight"
        decision = "oversee_lifecycle_oversight"
        actionability = "oversee"
        queue_override_status = None
    elif guardianship_decision == "buffer_lifecycle_guardianship":
        status = "scheduled"
        oversight_mode = "buffered_lifecycle_oversight"
        decision = "buffer_lifecycle_oversight"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif guardianship_decision == "pause_lifecycle_guardianship":
        status = "hold"
        oversight_mode = "paused_lifecycle_oversight"
        decision = "pause_lifecycle_oversight"
        actionability = "pause"
        queue_override_status = "hold"
    elif guardianship_decision == "archive_lifecycle_guardianship":
        status = "terminal"
        oversight_mode = "archived_lifecycle_oversight"
        decision = "archive_lifecycle_oversight"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif guardianship_decision == "retire_lifecycle_guardianship":
        status = "terminal"
        oversight_mode = "retired_lifecycle_oversight"
        decision = "retire_lifecycle_oversight"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        oversight_notes.append("fallback_pause")

    oversight_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_guardianship_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_guardianship_decision.changed
        or decision != "pause_lifecycle_oversight"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle oversight converts the guardianship posture into "
        "the final overseen state that future proactive oversight should honor."
    )
    if decision == "oversee_lifecycle_oversight":
        rationale = (
            "The proactive lifecycle oversight keeps the lifecycle overseen "
            "because the line should remain actively watched over for future proactive return."
        )
    elif decision == "buffer_lifecycle_oversight":
        rationale = (
            "The proactive lifecycle oversight keeps the lifecycle buffered because "
            "the line can become overseen later, but not yet."
        )
    elif decision == "pause_lifecycle_oversight":
        rationale = (
            "The proactive lifecycle oversight pauses the lifecycle because the "
            "line should remain present without immediate oversight."
        )
    elif decision == "archive_lifecycle_oversight":
        rationale = (
            "The proactive lifecycle oversight archives the lifecycle because "
            "the line reached a clean ending and should leave oversight."
        )
    elif decision == "retire_lifecycle_oversight":
        rationale = (
            "The proactive lifecycle oversight retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleOversightDecision(
        status=status,
        oversight_key=oversight_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        guardianship_mode=guardianship_mode,
        oversight_mode=oversight_mode,
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
        selected_strategy_key=(lifecycle_guardianship_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_guardianship_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_guardianship_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_guardianship_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        guardianship_decision=guardianship_decision,
        active_sources=_compact(lifecycle_guardianship_decision.active_sources, limit=8),
        oversight_notes=_compact(oversight_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_assurance_decision(
    *,
    lifecycle_oversight_decision: ProactiveLifecycleOversightDecision,
) -> ProactiveLifecycleAssuranceDecision:
    current_stage_label = lifecycle_oversight_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_oversight_decision.lifecycle_state or "active"
    oversight_mode = (
        lifecycle_oversight_decision.oversight_mode or "paused_lifecycle_oversight"
    )
    oversight_decision = (
        lifecycle_oversight_decision.decision or "pause_lifecycle_oversight"
    )
    active_stage_label = lifecycle_oversight_decision.active_stage_label
    next_stage_label = lifecycle_oversight_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_oversight_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_oversight_decision.line_state or "steady"
    line_exit_mode = lifecycle_oversight_decision.line_exit_mode or "stay"
    status = lifecycle_oversight_decision.status or "hold"
    assurance_mode = "paused_lifecycle_assurance"
    decision = "pause_lifecycle_assurance"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_oversight_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_oversight_decision.primary_source or "oversight"
    assurance_notes: list[str] = list(lifecycle_oversight_decision.oversight_notes)
    if line_state:
        assurance_notes.append(f"line:{line_state}")
    if line_exit_mode:
        assurance_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        assurance_notes.append(f"active:{active_stage_label}")

    if oversight_decision == "oversee_lifecycle_oversight":
        status = "active"
        assurance_mode = "assured_lifecycle_assurance"
        decision = "assure_lifecycle_assurance"
        actionability = "assure"
        queue_override_status = None
    elif oversight_decision == "buffer_lifecycle_oversight":
        status = "scheduled"
        assurance_mode = "buffered_lifecycle_assurance"
        decision = "buffer_lifecycle_assurance"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif oversight_decision == "pause_lifecycle_oversight":
        status = "hold"
        assurance_mode = "paused_lifecycle_assurance"
        decision = "pause_lifecycle_assurance"
        actionability = "pause"
        queue_override_status = "hold"
    elif oversight_decision == "archive_lifecycle_oversight":
        status = "terminal"
        assurance_mode = "archived_lifecycle_assurance"
        decision = "archive_lifecycle_assurance"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif oversight_decision == "retire_lifecycle_oversight":
        status = "terminal"
        assurance_mode = "retired_lifecycle_assurance"
        decision = "retire_lifecycle_assurance"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        assurance_notes.append("fallback_pause")

    assurance_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_oversight_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_oversight_decision.changed
        or decision != "pause_lifecycle_assurance"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle assurance converts the oversight posture into "
        "the final assured state that future proactive assurance should honor."
    )
    if decision == "assure_lifecycle_assurance":
        rationale = (
            "The proactive lifecycle assurance keeps the lifecycle assured because "
            "the line should remain confidently protected for future proactive return."
        )
    elif decision == "buffer_lifecycle_assurance":
        rationale = (
            "The proactive lifecycle assurance keeps the lifecycle buffered because "
            "the line can become assured later, but not yet."
        )
    elif decision == "pause_lifecycle_assurance":
        rationale = (
            "The proactive lifecycle assurance pauses the lifecycle because the "
            "line should remain present without immediate assurance."
        )
    elif decision == "archive_lifecycle_assurance":
        rationale = (
            "The proactive lifecycle assurance archives the lifecycle because "
            "the line reached a clean ending and should leave assurance."
        )
    elif decision == "retire_lifecycle_assurance":
        rationale = (
            "The proactive lifecycle assurance retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleAssuranceDecision(
        status=status,
        assurance_key=assurance_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        oversight_mode=oversight_mode,
        assurance_mode=assurance_mode,
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
        selected_strategy_key=(lifecycle_oversight_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_oversight_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_oversight_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_oversight_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        oversight_decision=oversight_decision,
        active_sources=_compact(lifecycle_oversight_decision.active_sources, limit=8),
        assurance_notes=_compact(assurance_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_attestation_decision(
    *,
    lifecycle_assurance_decision: ProactiveLifecycleAssuranceDecision,
) -> ProactiveLifecycleAttestationDecision:
    current_stage_label = lifecycle_assurance_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_assurance_decision.lifecycle_state or "active"
    assurance_mode = (
        lifecycle_assurance_decision.assurance_mode or "paused_lifecycle_assurance"
    )
    assurance_decision = (
        lifecycle_assurance_decision.decision or "pause_lifecycle_assurance"
    )
    active_stage_label = lifecycle_assurance_decision.active_stage_label
    next_stage_label = lifecycle_assurance_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_assurance_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_assurance_decision.line_state or "steady"
    line_exit_mode = lifecycle_assurance_decision.line_exit_mode or "stay"
    status = lifecycle_assurance_decision.status or "hold"
    attestation_mode = "paused_lifecycle_attestation"
    decision = "pause_lifecycle_attestation"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_assurance_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_assurance_decision.primary_source or "assurance"
    attestation_notes: list[str] = list(lifecycle_assurance_decision.assurance_notes)
    if line_state:
        attestation_notes.append(f"line:{line_state}")
    if line_exit_mode:
        attestation_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        attestation_notes.append(f"active:{active_stage_label}")

    if assurance_decision == "assure_lifecycle_assurance":
        status = "active"
        attestation_mode = "attested_lifecycle_attestation"
        decision = "attest_lifecycle_attestation"
        actionability = "attest"
        queue_override_status = None
    elif assurance_decision == "buffer_lifecycle_assurance":
        status = "scheduled"
        attestation_mode = "buffered_lifecycle_attestation"
        decision = "buffer_lifecycle_attestation"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif assurance_decision == "pause_lifecycle_assurance":
        status = "hold"
        attestation_mode = "paused_lifecycle_attestation"
        decision = "pause_lifecycle_attestation"
        actionability = "pause"
        queue_override_status = "hold"
    elif assurance_decision == "archive_lifecycle_assurance":
        status = "terminal"
        attestation_mode = "archived_lifecycle_attestation"
        decision = "archive_lifecycle_attestation"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif assurance_decision == "retire_lifecycle_assurance":
        status = "terminal"
        attestation_mode = "retired_lifecycle_attestation"
        decision = "retire_lifecycle_attestation"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        attestation_notes.append("fallback_pause")

    attestation_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_assurance_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_assurance_decision.changed
        or decision != "pause_lifecycle_attestation"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle attestation converts the assurance posture into "
        "the final attested state that future proactive attestation should honor."
    )
    if decision == "attest_lifecycle_attestation":
        rationale = (
            "The proactive lifecycle attestation keeps the lifecycle attested because "
            "the line should remain explicitly affirmed for future proactive return."
        )
    elif decision == "buffer_lifecycle_attestation":
        rationale = (
            "The proactive lifecycle attestation keeps the lifecycle buffered because "
            "the line can become attested later, but not yet."
        )
    elif decision == "pause_lifecycle_attestation":
        rationale = (
            "The proactive lifecycle attestation pauses the lifecycle because the "
            "line should remain present without immediate attestation."
        )
    elif decision == "archive_lifecycle_attestation":
        rationale = (
            "The proactive lifecycle attestation archives the lifecycle because "
            "the line reached a clean ending and should leave attestation."
        )
    elif decision == "retire_lifecycle_attestation":
        rationale = (
            "The proactive lifecycle attestation retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleAttestationDecision(
        status=status,
        attestation_key=attestation_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        assurance_mode=assurance_mode,
        attestation_mode=attestation_mode,
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
        selected_strategy_key=(lifecycle_assurance_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_assurance_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_assurance_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_assurance_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        assurance_decision=assurance_decision,
        active_sources=_compact(lifecycle_assurance_decision.active_sources, limit=8),
        attestation_notes=_compact(attestation_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_verification_decision(
    *,
    lifecycle_attestation_decision: ProactiveLifecycleAttestationDecision,
) -> ProactiveLifecycleVerificationDecision:
    current_stage_label = (
        lifecycle_attestation_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_attestation_decision.lifecycle_state or "active"
    attestation_mode = (
        lifecycle_attestation_decision.attestation_mode
        or "paused_lifecycle_attestation"
    )
    attestation_decision = (
        lifecycle_attestation_decision.decision or "pause_lifecycle_attestation"
    )
    active_stage_label = lifecycle_attestation_decision.active_stage_label
    next_stage_label = lifecycle_attestation_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_attestation_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_attestation_decision.line_state or "steady"
    line_exit_mode = lifecycle_attestation_decision.line_exit_mode or "stay"
    status = lifecycle_attestation_decision.status or "hold"
    verification_mode = "paused_lifecycle_verification"
    decision = "pause_lifecycle_verification"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_attestation_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_attestation_decision.primary_source or "attestation"
    verification_notes: list[str] = list(
        lifecycle_attestation_decision.attestation_notes
    )
    if line_state:
        verification_notes.append(f"line:{line_state}")
    if line_exit_mode:
        verification_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        verification_notes.append(f"active:{active_stage_label}")

    if attestation_decision == "attest_lifecycle_attestation":
        status = "active"
        verification_mode = "verified_lifecycle_verification"
        decision = "verify_lifecycle_verification"
        actionability = "verify"
        queue_override_status = None
    elif attestation_decision == "buffer_lifecycle_attestation":
        status = "scheduled"
        verification_mode = "buffered_lifecycle_verification"
        decision = "buffer_lifecycle_verification"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif attestation_decision == "pause_lifecycle_attestation":
        status = "hold"
        verification_mode = "paused_lifecycle_verification"
        decision = "pause_lifecycle_verification"
        actionability = "pause"
        queue_override_status = "hold"
    elif attestation_decision == "archive_lifecycle_attestation":
        status = "terminal"
        verification_mode = "archived_lifecycle_verification"
        decision = "archive_lifecycle_verification"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif attestation_decision == "retire_lifecycle_attestation":
        status = "terminal"
        verification_mode = "retired_lifecycle_verification"
        decision = "retire_lifecycle_verification"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        verification_notes.append("fallback_pause")

    verification_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_attestation_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_attestation_decision.changed
        or decision != "pause_lifecycle_verification"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle verification converts the attestation posture into "
        "the final verified state that future proactive verification should honor."
    )
    if decision == "verify_lifecycle_verification":
        rationale = (
            "The proactive lifecycle verification keeps the lifecycle verified because "
            "the line should remain explicitly confirmed for future proactive return."
        )
    elif decision == "buffer_lifecycle_verification":
        rationale = (
            "The proactive lifecycle verification keeps the lifecycle buffered because "
            "the line can become verified later, but not yet."
        )
    elif decision == "pause_lifecycle_verification":
        rationale = (
            "The proactive lifecycle verification pauses the lifecycle because the "
            "line should remain present without immediate verification."
        )
    elif decision == "archive_lifecycle_verification":
        rationale = (
            "The proactive lifecycle verification archives the lifecycle because "
            "the line reached a clean ending and should leave verification."
        )
    elif decision == "retire_lifecycle_verification":
        rationale = (
            "The proactive lifecycle verification retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleVerificationDecision(
        status=status,
        verification_key=verification_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        attestation_mode=attestation_mode,
        verification_mode=verification_mode,
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
        selected_strategy_key=(
            lifecycle_attestation_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_attestation_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_attestation_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_attestation_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        attestation_decision=attestation_decision,
        active_sources=_compact(lifecycle_attestation_decision.active_sources, limit=8),
        verification_notes=_compact(verification_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_certification_decision(
    *,
    lifecycle_verification_decision: ProactiveLifecycleVerificationDecision,
) -> ProactiveLifecycleCertificationDecision:
    current_stage_label = (
        lifecycle_verification_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_verification_decision.lifecycle_state or "active"
    verification_mode = (
        lifecycle_verification_decision.verification_mode
        or "paused_lifecycle_verification"
    )
    verification_decision = (
        lifecycle_verification_decision.decision or "pause_lifecycle_verification"
    )
    active_stage_label = lifecycle_verification_decision.active_stage_label
    next_stage_label = lifecycle_verification_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_verification_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_verification_decision.line_state or "steady"
    line_exit_mode = lifecycle_verification_decision.line_exit_mode or "stay"
    status = lifecycle_verification_decision.status or "hold"
    certification_mode = "paused_lifecycle_certification"
    decision = "pause_lifecycle_certification"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_verification_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_verification_decision.primary_source or "verification"
    certification_notes: list[str] = list(
        lifecycle_verification_decision.verification_notes
    )
    if line_state:
        certification_notes.append(f"line:{line_state}")
    if line_exit_mode:
        certification_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        certification_notes.append(f"active:{active_stage_label}")

    if verification_decision == "verify_lifecycle_verification":
        status = "active"
        certification_mode = "certified_lifecycle_certification"
        decision = "certify_lifecycle_certification"
        actionability = "certify"
        queue_override_status = None
    elif verification_decision == "buffer_lifecycle_verification":
        status = "scheduled"
        certification_mode = "buffered_lifecycle_certification"
        decision = "buffer_lifecycle_certification"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif verification_decision == "pause_lifecycle_verification":
        status = "hold"
        certification_mode = "paused_lifecycle_certification"
        decision = "pause_lifecycle_certification"
        actionability = "pause"
        queue_override_status = "hold"
    elif verification_decision == "archive_lifecycle_verification":
        status = "terminal"
        certification_mode = "archived_lifecycle_certification"
        decision = "archive_lifecycle_certification"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif verification_decision == "retire_lifecycle_verification":
        status = "terminal"
        certification_mode = "retired_lifecycle_certification"
        decision = "retire_lifecycle_certification"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        certification_notes.append("fallback_pause")

    certification_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_verification_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_verification_decision.changed
        or decision != "pause_lifecycle_certification"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle certification converts the verification posture into "
        "the final certified state that future proactive certification should honor."
    )
    if decision == "certify_lifecycle_certification":
        rationale = (
            "The proactive lifecycle certification keeps the lifecycle certified because "
            "the line should remain explicitly certified for future proactive return."
        )
    elif decision == "buffer_lifecycle_certification":
        rationale = (
            "The proactive lifecycle certification keeps the lifecycle buffered because "
            "the line can become certified later, but not yet."
        )
    elif decision == "pause_lifecycle_certification":
        rationale = (
            "The proactive lifecycle certification pauses the lifecycle because the "
            "line should remain present without immediate certification."
        )
    elif decision == "archive_lifecycle_certification":
        rationale = (
            "The proactive lifecycle certification archives the lifecycle because "
            "the line reached a clean ending and should leave certification."
        )
    elif decision == "retire_lifecycle_certification":
        rationale = (
            "The proactive lifecycle certification retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleCertificationDecision(
        status=status,
        certification_key=certification_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        verification_mode=verification_mode,
        certification_mode=certification_mode,
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
        selected_strategy_key=(
            lifecycle_verification_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_verification_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_verification_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_verification_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        verification_decision=verification_decision,
        active_sources=_compact(lifecycle_verification_decision.active_sources, limit=8),
        certification_notes=_compact(certification_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_confirmation_decision(
    *,
    lifecycle_certification_decision: ProactiveLifecycleCertificationDecision,
) -> ProactiveLifecycleConfirmationDecision:
    current_stage_label = (
        lifecycle_certification_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_certification_decision.lifecycle_state or "active"
    certification_mode = (
        lifecycle_certification_decision.certification_mode
        or "paused_lifecycle_certification"
    )
    certification_decision = (
        lifecycle_certification_decision.decision or "pause_lifecycle_certification"
    )
    active_stage_label = lifecycle_certification_decision.active_stage_label
    next_stage_label = lifecycle_certification_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_certification_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_certification_decision.line_state or "steady"
    line_exit_mode = lifecycle_certification_decision.line_exit_mode or "stay"
    status = lifecycle_certification_decision.status or "hold"
    confirmation_mode = "paused_lifecycle_confirmation"
    decision = "pause_lifecycle_confirmation"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_certification_decision.additional_delay_seconds or 0)
    )
    primary_source = (
        lifecycle_certification_decision.primary_source or "certification"
    )
    confirmation_notes: list[str] = list(
        lifecycle_certification_decision.certification_notes
    )
    if line_state:
        confirmation_notes.append(f"line:{line_state}")
    if line_exit_mode:
        confirmation_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        confirmation_notes.append(f"active:{active_stage_label}")

    if certification_decision == "certify_lifecycle_certification":
        status = "active"
        confirmation_mode = "confirmed_lifecycle_confirmation"
        decision = "confirm_lifecycle_confirmation"
        actionability = "confirm"
        queue_override_status = None
    elif certification_decision == "buffer_lifecycle_certification":
        status = "scheduled"
        confirmation_mode = "buffered_lifecycle_confirmation"
        decision = "buffer_lifecycle_confirmation"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif certification_decision == "pause_lifecycle_certification":
        status = "hold"
        confirmation_mode = "paused_lifecycle_confirmation"
        decision = "pause_lifecycle_confirmation"
        actionability = "pause"
        queue_override_status = "hold"
    elif certification_decision == "archive_lifecycle_certification":
        status = "terminal"
        confirmation_mode = "archived_lifecycle_confirmation"
        decision = "archive_lifecycle_confirmation"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif certification_decision == "retire_lifecycle_certification":
        status = "terminal"
        confirmation_mode = "retired_lifecycle_confirmation"
        decision = "retire_lifecycle_confirmation"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        confirmation_notes.append("fallback_pause")

    confirmation_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_certification_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_certification_decision.changed
        or decision != "pause_lifecycle_confirmation"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle confirmation converts the certification posture into "
        "the final confirmed state that future proactive confirmation should honor."
    )
    if decision == "confirm_lifecycle_confirmation":
        rationale = (
            "The proactive lifecycle confirmation keeps the lifecycle confirmed because "
            "the line should remain explicitly confirmed for future proactive return."
        )
    elif decision == "buffer_lifecycle_confirmation":
        rationale = (
            "The proactive lifecycle confirmation keeps the lifecycle buffered because "
            "the line can become confirmed later, but not yet."
        )
    elif decision == "pause_lifecycle_confirmation":
        rationale = (
            "The proactive lifecycle confirmation pauses the lifecycle because the "
            "line should remain present without immediate confirmation."
        )
    elif decision == "archive_lifecycle_confirmation":
        rationale = (
            "The proactive lifecycle confirmation archives the lifecycle because "
            "the line reached a clean ending and should leave confirmation."
        )
    elif decision == "retire_lifecycle_confirmation":
        rationale = (
            "The proactive lifecycle confirmation retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleConfirmationDecision(
        status=status,
        confirmation_key=confirmation_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        certification_mode=certification_mode,
        confirmation_mode=confirmation_mode,
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
        selected_strategy_key=(
            lifecycle_certification_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_certification_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_certification_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_certification_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        certification_decision=certification_decision,
        active_sources=_compact(
            lifecycle_certification_decision.active_sources, limit=8
        ),
        confirmation_notes=_compact(confirmation_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_ratification_decision(
    *,
    lifecycle_confirmation_decision: ProactiveLifecycleConfirmationDecision,
) -> ProactiveLifecycleRatificationDecision:
    current_stage_label = (
        lifecycle_confirmation_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_confirmation_decision.lifecycle_state or "active"
    confirmation_mode = (
        lifecycle_confirmation_decision.confirmation_mode
        or "paused_lifecycle_confirmation"
    )
    confirmation_decision = (
        lifecycle_confirmation_decision.decision or "pause_lifecycle_confirmation"
    )
    active_stage_label = lifecycle_confirmation_decision.active_stage_label
    next_stage_label = lifecycle_confirmation_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_confirmation_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_confirmation_decision.line_state or "steady"
    line_exit_mode = lifecycle_confirmation_decision.line_exit_mode or "stay"
    status = lifecycle_confirmation_decision.status or "hold"
    ratification_mode = "paused_lifecycle_ratification"
    decision = "pause_lifecycle_ratification"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_confirmation_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_confirmation_decision.primary_source or "confirmation"
    ratification_notes: list[str] = list(
        lifecycle_confirmation_decision.confirmation_notes
    )
    if line_state:
        ratification_notes.append(f"line:{line_state}")
    if line_exit_mode:
        ratification_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        ratification_notes.append(f"active:{active_stage_label}")

    if confirmation_decision == "confirm_lifecycle_confirmation":
        status = "active"
        ratification_mode = "ratified_lifecycle_ratification"
        decision = "ratify_lifecycle_ratification"
        actionability = "ratify"
        queue_override_status = None
    elif confirmation_decision == "buffer_lifecycle_confirmation":
        status = "scheduled"
        ratification_mode = "buffered_lifecycle_ratification"
        decision = "buffer_lifecycle_ratification"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif confirmation_decision == "pause_lifecycle_confirmation":
        status = "hold"
        ratification_mode = "paused_lifecycle_ratification"
        decision = "pause_lifecycle_ratification"
        actionability = "pause"
        queue_override_status = "hold"
    elif confirmation_decision == "archive_lifecycle_confirmation":
        status = "terminal"
        ratification_mode = "archived_lifecycle_ratification"
        decision = "archive_lifecycle_ratification"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif confirmation_decision == "retire_lifecycle_confirmation":
        status = "terminal"
        ratification_mode = "retired_lifecycle_ratification"
        decision = "retire_lifecycle_ratification"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        ratification_notes.append("fallback_pause")

    ratification_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_confirmation_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_confirmation_decision.changed
        or decision != "pause_lifecycle_ratification"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle ratification converts the confirmation posture into "
        "the final ratified state that future proactive ratification should honor."
    )
    if decision == "ratify_lifecycle_ratification":
        rationale = (
            "The proactive lifecycle ratification keeps the lifecycle ratified because "
            "the line should remain explicitly ratified for future proactive return."
        )
    elif decision == "buffer_lifecycle_ratification":
        rationale = (
            "The proactive lifecycle ratification keeps the lifecycle buffered because "
            "the line can become ratified later, but not yet."
        )
    elif decision == "pause_lifecycle_ratification":
        rationale = (
            "The proactive lifecycle ratification pauses the lifecycle because the "
            "line should remain present without immediate ratification."
        )
    elif decision == "archive_lifecycle_ratification":
        rationale = (
            "The proactive lifecycle ratification archives the lifecycle because "
            "the line reached a clean ending and should leave ratification."
        )
    elif decision == "retire_lifecycle_ratification":
        rationale = (
            "The proactive lifecycle ratification retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleRatificationDecision(
        status=status,
        ratification_key=ratification_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        confirmation_mode=confirmation_mode,
        ratification_mode=ratification_mode,
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
        selected_strategy_key=(
            lifecycle_confirmation_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_confirmation_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_confirmation_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_confirmation_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        confirmation_decision=confirmation_decision,
        active_sources=_compact(
            lifecycle_confirmation_decision.active_sources, limit=8
        ),
        ratification_notes=_compact(ratification_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_endorsement_decision(
    *,
    lifecycle_ratification_decision: ProactiveLifecycleRatificationDecision,
) -> ProactiveLifecycleEndorsementDecision:
    current_stage_label = lifecycle_ratification_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_ratification_decision.lifecycle_state or "active"
    ratification_mode = (
        lifecycle_ratification_decision.ratification_mode
        or "paused_lifecycle_ratification"
    )
    ratification_decision = (
        lifecycle_ratification_decision.decision or "pause_lifecycle_ratification"
    )
    active_stage_label = lifecycle_ratification_decision.active_stage_label
    next_stage_label = lifecycle_ratification_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_ratification_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_ratification_decision.line_state or "steady"
    line_exit_mode = lifecycle_ratification_decision.line_exit_mode or "stay"
    status = lifecycle_ratification_decision.status or "hold"
    endorsement_mode = "paused_lifecycle_endorsement"
    decision = "pause_lifecycle_endorsement"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_ratification_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_ratification_decision.primary_source or "ratification"
    endorsement_notes: list[str] = list(
        lifecycle_ratification_decision.ratification_notes
    )
    if line_state:
        endorsement_notes.append(f"line:{line_state}")
    if line_exit_mode:
        endorsement_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        endorsement_notes.append(f"active:{active_stage_label}")

    if ratification_decision == "ratify_lifecycle_ratification":
        status = "active"
        endorsement_mode = "endorsed_lifecycle_endorsement"
        decision = "endorse_lifecycle_endorsement"
        actionability = "endorse"
        queue_override_status = None
    elif ratification_decision == "buffer_lifecycle_ratification":
        status = "scheduled"
        endorsement_mode = "buffered_lifecycle_endorsement"
        decision = "buffer_lifecycle_endorsement"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif ratification_decision == "pause_lifecycle_ratification":
        status = "hold"
        endorsement_mode = "paused_lifecycle_endorsement"
        decision = "pause_lifecycle_endorsement"
        actionability = "pause"
        queue_override_status = "hold"
    elif ratification_decision == "archive_lifecycle_ratification":
        status = "terminal"
        endorsement_mode = "archived_lifecycle_endorsement"
        decision = "archive_lifecycle_endorsement"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif ratification_decision == "retire_lifecycle_ratification":
        status = "terminal"
        endorsement_mode = "retired_lifecycle_endorsement"
        decision = "retire_lifecycle_endorsement"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        endorsement_notes.append("fallback_pause")

    endorsement_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_ratification_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_ratification_decision.changed
        or decision != "pause_lifecycle_endorsement"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle endorsement converts the ratification posture into "
        "the final endorsed state that future proactive endorsement should honor."
    )
    if decision == "endorse_lifecycle_endorsement":
        rationale = (
            "The proactive lifecycle endorsement keeps the lifecycle endorsed because "
            "the line should remain explicitly endorsed for future proactive return."
        )
    elif decision == "buffer_lifecycle_endorsement":
        rationale = (
            "The proactive lifecycle endorsement keeps the lifecycle buffered because "
            "the line can become endorsed later, but not yet."
        )
    elif decision == "pause_lifecycle_endorsement":
        rationale = (
            "The proactive lifecycle endorsement pauses the lifecycle because the "
            "line should remain present without immediate endorsement."
        )
    elif decision == "archive_lifecycle_endorsement":
        rationale = (
            "The proactive lifecycle endorsement archives the lifecycle because "
            "the line reached a clean ending and should leave endorsement."
        )
    elif decision == "retire_lifecycle_endorsement":
        rationale = (
            "The proactive lifecycle endorsement retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleEndorsementDecision(
        status=status,
        endorsement_key=endorsement_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        ratification_mode=ratification_mode,
        endorsement_mode=endorsement_mode,
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
        selected_strategy_key=(
            lifecycle_ratification_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_ratification_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_ratification_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_ratification_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        ratification_decision=ratification_decision,
        active_sources=_compact(
            lifecycle_ratification_decision.active_sources, limit=8
        ),
        endorsement_notes=_compact(endorsement_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_authorization_decision(
    *,
    lifecycle_endorsement_decision: ProactiveLifecycleEndorsementDecision,
) -> ProactiveLifecycleAuthorizationDecision:
    current_stage_label = lifecycle_endorsement_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_endorsement_decision.lifecycle_state or "active"
    endorsement_mode = (
        lifecycle_endorsement_decision.endorsement_mode
        or "paused_lifecycle_endorsement"
    )
    endorsement_decision = (
        lifecycle_endorsement_decision.decision or "pause_lifecycle_endorsement"
    )
    active_stage_label = lifecycle_endorsement_decision.active_stage_label
    next_stage_label = lifecycle_endorsement_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_endorsement_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_endorsement_decision.line_state or "steady"
    line_exit_mode = lifecycle_endorsement_decision.line_exit_mode or "stay"
    status = lifecycle_endorsement_decision.status or "hold"
    authorization_mode = "paused_lifecycle_authorization"
    decision = "pause_lifecycle_authorization"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_endorsement_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_endorsement_decision.primary_source or "endorsement"
    authorization_notes: list[str] = list(
        lifecycle_endorsement_decision.endorsement_notes
    )
    if line_state:
        authorization_notes.append(f"line:{line_state}")
    if line_exit_mode:
        authorization_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        authorization_notes.append(f"active:{active_stage_label}")

    if endorsement_decision == "endorse_lifecycle_endorsement":
        status = "active"
        authorization_mode = "authorized_lifecycle_authorization"
        decision = "authorize_lifecycle_authorization"
        actionability = "authorize"
        queue_override_status = None
    elif endorsement_decision == "buffer_lifecycle_endorsement":
        status = "scheduled"
        authorization_mode = "buffered_lifecycle_authorization"
        decision = "buffer_lifecycle_authorization"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif endorsement_decision == "pause_lifecycle_endorsement":
        status = "hold"
        authorization_mode = "paused_lifecycle_authorization"
        decision = "pause_lifecycle_authorization"
        actionability = "pause"
        queue_override_status = "hold"
    elif endorsement_decision == "archive_lifecycle_endorsement":
        status = "terminal"
        authorization_mode = "archived_lifecycle_authorization"
        decision = "archive_lifecycle_authorization"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif endorsement_decision == "retire_lifecycle_endorsement":
        status = "terminal"
        authorization_mode = "retired_lifecycle_authorization"
        decision = "retire_lifecycle_authorization"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        authorization_notes.append("fallback_pause")

    authorization_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_endorsement_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_endorsement_decision.changed
        or decision != "pause_lifecycle_authorization"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle authorization converts the endorsement posture into "
        "the final authorized state that future proactive authorization should honor."
    )
    if decision == "authorize_lifecycle_authorization":
        rationale = (
            "The proactive lifecycle authorization keeps the lifecycle authorized because "
            "the line should remain explicitly authorized for future proactive return."
        )
    elif decision == "buffer_lifecycle_authorization":
        rationale = (
            "The proactive lifecycle authorization keeps the lifecycle buffered because "
            "the line can become authorized later, but not yet."
        )
    elif decision == "pause_lifecycle_authorization":
        rationale = (
            "The proactive lifecycle authorization pauses the lifecycle because the "
            "line should remain present without immediate authorization."
        )
    elif decision == "archive_lifecycle_authorization":
        rationale = (
            "The proactive lifecycle authorization archives the lifecycle because "
            "the line reached a clean ending and should leave authorization."
        )
    elif decision == "retire_lifecycle_authorization":
        rationale = (
            "The proactive lifecycle authorization retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleAuthorizationDecision(
        status=status,
        authorization_key=authorization_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        endorsement_mode=endorsement_mode,
        authorization_mode=authorization_mode,
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
        selected_strategy_key=(
            lifecycle_endorsement_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_endorsement_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_endorsement_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_endorsement_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        endorsement_decision=endorsement_decision,
        active_sources=_compact(
            lifecycle_endorsement_decision.active_sources, limit=8
        ),
        authorization_notes=_compact(authorization_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_enactment_decision(
    *,
    lifecycle_authorization_decision: ProactiveLifecycleAuthorizationDecision,
) -> ProactiveLifecycleEnactmentDecision:
    current_stage_label = (
        lifecycle_authorization_decision.current_stage_label or "unknown"
    )
    lifecycle_state = lifecycle_authorization_decision.lifecycle_state or "active"
    authorization_mode = (
        lifecycle_authorization_decision.authorization_mode
        or "paused_lifecycle_authorization"
    )
    authorization_decision = (
        lifecycle_authorization_decision.decision or "pause_lifecycle_authorization"
    )
    active_stage_label = lifecycle_authorization_decision.active_stage_label
    next_stage_label = lifecycle_authorization_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_authorization_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_authorization_decision.line_state or "steady"
    line_exit_mode = lifecycle_authorization_decision.line_exit_mode or "stay"
    status = lifecycle_authorization_decision.status or "hold"
    enactment_mode = "paused_lifecycle_enactment"
    decision = "pause_lifecycle_enactment"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_authorization_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_authorization_decision.primary_source or "authorization"
    enactment_notes: list[str] = list(
        lifecycle_authorization_decision.authorization_notes
    )
    if line_state:
        enactment_notes.append(f"line:{line_state}")
    if line_exit_mode:
        enactment_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        enactment_notes.append(f"active:{active_stage_label}")

    if authorization_decision == "authorize_lifecycle_authorization":
        status = "active"
        enactment_mode = "enacted_lifecycle_enactment"
        decision = "enact_lifecycle_enactment"
        actionability = "enact"
        queue_override_status = None
    elif authorization_decision == "buffer_lifecycle_authorization":
        status = "scheduled"
        enactment_mode = "buffered_lifecycle_enactment"
        decision = "buffer_lifecycle_enactment"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif authorization_decision == "pause_lifecycle_authorization":
        status = "hold"
        enactment_mode = "paused_lifecycle_enactment"
        decision = "pause_lifecycle_enactment"
        actionability = "pause"
        queue_override_status = "hold"
    elif authorization_decision == "archive_lifecycle_authorization":
        status = "terminal"
        enactment_mode = "archived_lifecycle_enactment"
        decision = "archive_lifecycle_enactment"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif authorization_decision == "retire_lifecycle_authorization":
        status = "terminal"
        enactment_mode = "retired_lifecycle_enactment"
        decision = "retire_lifecycle_enactment"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        enactment_notes.append("fallback_pause")

    enactment_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_authorization_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_authorization_decision.changed
        or decision != "pause_lifecycle_enactment"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle enactment converts the authorization posture into "
        "the final enacted state that future proactive enactment should honor."
    )
    if decision == "enact_lifecycle_enactment":
        rationale = (
            "The proactive lifecycle enactment keeps the lifecycle enacted because "
            "the line should remain explicitly enacted for future proactive return."
        )
    elif decision == "buffer_lifecycle_enactment":
        rationale = (
            "The proactive lifecycle enactment keeps the lifecycle buffered because "
            "the line can become enacted later, but not yet."
        )
    elif decision == "pause_lifecycle_enactment":
        rationale = (
            "The proactive lifecycle enactment pauses the lifecycle because the "
            "line should remain present without immediate enactment."
        )
    elif decision == "archive_lifecycle_enactment":
        rationale = (
            "The proactive lifecycle enactment archives the lifecycle because "
            "the line reached a clean ending and should leave enactment."
        )
    elif decision == "retire_lifecycle_enactment":
        rationale = (
            "The proactive lifecycle enactment retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleEnactmentDecision(
        status=status,
        enactment_key=enactment_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        authorization_mode=authorization_mode,
        enactment_mode=enactment_mode,
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
        selected_strategy_key=(
            lifecycle_authorization_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_authorization_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_authorization_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_authorization_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        authorization_decision=authorization_decision,
        active_sources=_compact(
            lifecycle_authorization_decision.active_sources, limit=8
        ),
        enactment_notes=_compact(enactment_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_finality_decision(
    *,
    lifecycle_enactment_decision: ProactiveLifecycleEnactmentDecision,
) -> ProactiveLifecycleFinalityDecision:
    current_stage_label = lifecycle_enactment_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_enactment_decision.lifecycle_state or "active"
    enactment_mode = (
        lifecycle_enactment_decision.enactment_mode
        or "paused_lifecycle_enactment"
    )
    enactment_decision = (
        lifecycle_enactment_decision.decision or "pause_lifecycle_enactment"
    )
    active_stage_label = lifecycle_enactment_decision.active_stage_label
    next_stage_label = lifecycle_enactment_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_enactment_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_enactment_decision.line_state or "steady"
    line_exit_mode = lifecycle_enactment_decision.line_exit_mode or "stay"
    status = lifecycle_enactment_decision.status or "hold"
    finality_mode = "paused_lifecycle_finality"
    decision = "pause_lifecycle_finality"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_enactment_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_enactment_decision.primary_source or "enactment"
    finality_notes: list[str] = list(lifecycle_enactment_decision.enactment_notes)
    if line_state:
        finality_notes.append(f"line:{line_state}")
    if line_exit_mode:
        finality_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        finality_notes.append(f"active:{active_stage_label}")

    if enactment_decision == "enact_lifecycle_enactment":
        status = "active"
        finality_mode = "finalized_lifecycle_finality"
        decision = "finalize_lifecycle_finality"
        actionability = "finalize"
        queue_override_status = None
    elif enactment_decision == "buffer_lifecycle_enactment":
        status = "scheduled"
        finality_mode = "buffered_lifecycle_finality"
        decision = "buffer_lifecycle_finality"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif enactment_decision == "pause_lifecycle_enactment":
        status = "hold"
        finality_mode = "paused_lifecycle_finality"
        decision = "pause_lifecycle_finality"
        actionability = "pause"
        queue_override_status = "hold"
    elif enactment_decision == "archive_lifecycle_enactment":
        status = "terminal"
        finality_mode = "archived_lifecycle_finality"
        decision = "archive_lifecycle_finality"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif enactment_decision == "retire_lifecycle_enactment":
        status = "terminal"
        finality_mode = "retired_lifecycle_finality"
        decision = "retire_lifecycle_finality"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        finality_notes.append("fallback_pause")

    finality_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_enactment_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_enactment_decision.changed
        or decision != "pause_lifecycle_finality"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle finality converts the enactment posture into "
        "the final finality state that future proactive execution should honor."
    )
    if decision == "finalize_lifecycle_finality":
        rationale = (
            "The proactive lifecycle finality keeps the lifecycle finalized because "
            "the line should remain explicitly finalized for future proactive return."
        )
    elif decision == "buffer_lifecycle_finality":
        rationale = (
            "The proactive lifecycle finality keeps the lifecycle buffered because "
            "the line can become finalized later, but not yet."
        )
    elif decision == "pause_lifecycle_finality":
        rationale = (
            "The proactive lifecycle finality pauses the lifecycle because the "
            "line should remain present without immediate finalization."
        )
    elif decision == "archive_lifecycle_finality":
        rationale = (
            "The proactive lifecycle finality archives the lifecycle because "
            "the line reached a clean ending and should leave finality."
        )
    elif decision == "retire_lifecycle_finality":
        rationale = (
            "The proactive lifecycle finality retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleFinalityDecision(
        status=status,
        finality_key=finality_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        enactment_mode=enactment_mode,
        finality_mode=finality_mode,
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
        selected_strategy_key=(
            lifecycle_enactment_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_enactment_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_enactment_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_enactment_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        enactment_decision=enactment_decision,
        active_sources=_compact(lifecycle_enactment_decision.active_sources, limit=8),
        finality_notes=_compact(finality_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_completion_decision(
    *,
    lifecycle_finality_decision: ProactiveLifecycleFinalityDecision,
) -> ProactiveLifecycleCompletionDecision:
    current_stage_label = lifecycle_finality_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_finality_decision.lifecycle_state or "active"
    finality_mode = (
        lifecycle_finality_decision.finality_mode or "paused_lifecycle_finality"
    )
    finality_decision = (
        lifecycle_finality_decision.decision or "pause_lifecycle_finality"
    )
    active_stage_label = lifecycle_finality_decision.active_stage_label
    next_stage_label = lifecycle_finality_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_finality_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_finality_decision.line_state or "steady"
    line_exit_mode = lifecycle_finality_decision.line_exit_mode or "stay"
    status = lifecycle_finality_decision.status or "hold"
    completion_mode = "paused_lifecycle_completion"
    decision = "pause_lifecycle_completion"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_finality_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_finality_decision.primary_source or "finality"
    completion_notes: list[str] = list(lifecycle_finality_decision.finality_notes)
    if line_state:
        completion_notes.append(f"line:{line_state}")
    if line_exit_mode:
        completion_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        completion_notes.append(f"active:{active_stage_label}")

    if finality_decision == "finalize_lifecycle_finality":
        status = "active"
        completion_mode = "completed_lifecycle_completion"
        decision = "complete_lifecycle_completion"
        actionability = "complete"
        queue_override_status = None
    elif finality_decision == "buffer_lifecycle_finality":
        status = "scheduled"
        completion_mode = "buffered_lifecycle_completion"
        decision = "buffer_lifecycle_completion"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif finality_decision == "pause_lifecycle_finality":
        status = "hold"
        completion_mode = "paused_lifecycle_completion"
        decision = "pause_lifecycle_completion"
        actionability = "pause"
        queue_override_status = "hold"
    elif finality_decision == "archive_lifecycle_finality":
        status = "terminal"
        completion_mode = "archived_lifecycle_completion"
        decision = "archive_lifecycle_completion"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif finality_decision == "retire_lifecycle_finality":
        status = "terminal"
        completion_mode = "retired_lifecycle_completion"
        decision = "retire_lifecycle_completion"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        completion_notes.append("fallback_pause")

    completion_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_finality_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_finality_decision.changed
        or decision != "pause_lifecycle_completion"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle completion converts the finality posture into "
        "the final completion state that future proactive completion should honor."
    )
    if decision == "complete_lifecycle_completion":
        rationale = (
            "The proactive lifecycle completion keeps the lifecycle completed because "
            "the line should remain explicitly completed for future proactive return."
        )
    elif decision == "buffer_lifecycle_completion":
        rationale = (
            "The proactive lifecycle completion keeps the lifecycle buffered because "
            "the line can become completed later, but not yet."
        )
    elif decision == "pause_lifecycle_completion":
        rationale = (
            "The proactive lifecycle completion pauses the lifecycle because the "
            "line should remain present without immediate completion."
        )
    elif decision == "archive_lifecycle_completion":
        rationale = (
            "The proactive lifecycle completion archives the lifecycle because "
            "the line reached a clean ending and should leave completion."
        )
    elif decision == "retire_lifecycle_completion":
        rationale = (
            "The proactive lifecycle completion retires the lifecycle because "
            "the line has reached a terminal stop condition."
        )

    return ProactiveLifecycleCompletionDecision(
        status=status,
        completion_key=completion_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        finality_mode=finality_mode,
        completion_mode=completion_mode,
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
        selected_strategy_key=(
            lifecycle_finality_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_finality_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_finality_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_finality_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        finality_decision=finality_decision,
        active_sources=_compact(lifecycle_finality_decision.active_sources, limit=8),
        completion_notes=_compact(completion_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_conclusion_decision(
    *,
    lifecycle_completion_decision: ProactiveLifecycleCompletionDecision,
) -> ProactiveLifecycleConclusionDecision:
    current_stage_label = lifecycle_completion_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_completion_decision.lifecycle_state or "active"
    completion_mode = (
        lifecycle_completion_decision.completion_mode
        or "paused_lifecycle_completion"
    )
    completion_decision = (
        lifecycle_completion_decision.decision or "pause_lifecycle_completion"
    )
    active_stage_label = lifecycle_completion_decision.active_stage_label
    next_stage_label = lifecycle_completion_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_completion_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_completion_decision.line_state or "steady"
    line_exit_mode = lifecycle_completion_decision.line_exit_mode or "stay"
    status = lifecycle_completion_decision.status or "hold"
    conclusion_mode = "paused_lifecycle_conclusion"
    decision = "pause_lifecycle_conclusion"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_completion_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_completion_decision.primary_source or "completion"
    conclusion_notes: list[str] = list(lifecycle_completion_decision.completion_notes)
    conclusion_notes.append(f"completion:{completion_mode}")
    if line_state:
        conclusion_notes.append(f"line:{line_state}")
    if line_exit_mode:
        conclusion_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        conclusion_notes.append(f"active:{active_stage_label}")

    if completion_decision == "complete_lifecycle_completion":
        status = "active"
        conclusion_mode = "completed_lifecycle_conclusion"
        decision = "complete_lifecycle_conclusion"
        actionability = "complete"
        queue_override_status = None
    elif completion_decision == "buffer_lifecycle_completion":
        status = "scheduled"
        conclusion_mode = "buffered_lifecycle_conclusion"
        decision = "buffer_lifecycle_conclusion"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif completion_decision == "pause_lifecycle_completion":
        status = "hold"
        conclusion_mode = "paused_lifecycle_conclusion"
        decision = "pause_lifecycle_conclusion"
        actionability = "pause"
        queue_override_status = "hold"
    elif completion_decision == "archive_lifecycle_completion":
        status = "terminal"
        conclusion_mode = "archived_lifecycle_conclusion"
        decision = "archive_lifecycle_conclusion"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif completion_decision == "retire_lifecycle_completion":
        status = "terminal"
        conclusion_mode = "retired_lifecycle_conclusion"
        decision = "retire_lifecycle_conclusion"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        conclusion_notes.append("fallback_pause")

    conclusion_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_completion_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_completion_decision.changed
        or decision != "pause_lifecycle_conclusion"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle conclusion converts the completion posture into "
        "the final conclusion state that future proactive scheduling should honor."
    )
    if decision == "complete_lifecycle_conclusion":
        rationale = (
            "The proactive lifecycle conclusion keeps the lifecycle completed because "
            "the line can remain present without extra queue suppression."
        )
    elif decision == "buffer_lifecycle_conclusion":
        rationale = (
            "The proactive lifecycle conclusion buffers the lifecycle because "
            "the line should stay present but not immediately active."
        )
    elif decision == "pause_lifecycle_conclusion":
        rationale = (
            "The proactive lifecycle conclusion pauses the lifecycle because "
            "the line should remain open without immediate proactive continuation."
        )
    elif decision == "archive_lifecycle_conclusion":
        rationale = (
            "The proactive lifecycle conclusion archives the lifecycle because "
            "the line reached a clean ending and should leave the active queue."
        )
    elif decision == "retire_lifecycle_conclusion":
        rationale = (
            "The proactive lifecycle conclusion retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleConclusionDecision(
        status=status,
        conclusion_key=conclusion_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        completion_mode=completion_mode,
        conclusion_mode=conclusion_mode,
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
        selected_strategy_key=(
            lifecycle_completion_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_completion_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_completion_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_completion_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        completion_decision=completion_decision,
        active_sources=_compact(lifecycle_completion_decision.active_sources, limit=8),
        conclusion_notes=_compact(conclusion_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_disposition_decision(
    *,
    lifecycle_conclusion_decision: ProactiveLifecycleConclusionDecision,
) -> ProactiveLifecycleDispositionDecision:
    current_stage_label = lifecycle_conclusion_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_conclusion_decision.lifecycle_state or "active"
    conclusion_mode = (
        lifecycle_conclusion_decision.conclusion_mode
        or "paused_lifecycle_conclusion"
    )
    conclusion_decision = (
        lifecycle_conclusion_decision.decision or "pause_lifecycle_conclusion"
    )
    active_stage_label = lifecycle_conclusion_decision.active_stage_label
    next_stage_label = lifecycle_conclusion_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_conclusion_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_conclusion_decision.line_state or "steady"
    line_exit_mode = lifecycle_conclusion_decision.line_exit_mode or "stay"
    status = lifecycle_conclusion_decision.status or "hold"
    disposition_mode = "paused_lifecycle_disposition"
    decision = "pause_lifecycle_disposition"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_conclusion_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_conclusion_decision.primary_source or "conclusion"
    disposition_notes: list[str] = list(lifecycle_conclusion_decision.conclusion_notes)
    disposition_notes.append(f"conclusion:{conclusion_mode}")
    if line_state:
        disposition_notes.append(f"line:{line_state}")
    if line_exit_mode:
        disposition_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        disposition_notes.append(f"active:{active_stage_label}")

    if conclusion_decision == "complete_lifecycle_conclusion":
        status = "active"
        disposition_mode = "completed_lifecycle_disposition"
        decision = "complete_lifecycle_disposition"
        actionability = "complete"
        queue_override_status = None
    elif conclusion_decision == "buffer_lifecycle_conclusion":
        status = "scheduled"
        disposition_mode = "buffered_lifecycle_disposition"
        decision = "buffer_lifecycle_disposition"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif conclusion_decision == "pause_lifecycle_conclusion":
        status = "hold"
        disposition_mode = "paused_lifecycle_disposition"
        decision = "pause_lifecycle_disposition"
        actionability = "pause"
        queue_override_status = "hold"
    elif conclusion_decision == "archive_lifecycle_conclusion":
        status = "terminal"
        disposition_mode = "archived_lifecycle_disposition"
        decision = "archive_lifecycle_disposition"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif conclusion_decision == "retire_lifecycle_conclusion":
        status = "terminal"
        disposition_mode = "retired_lifecycle_disposition"
        decision = "retire_lifecycle_disposition"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        disposition_notes.append("fallback_pause")

    disposition_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_conclusion_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_conclusion_decision.changed
        or decision != "pause_lifecycle_disposition"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle disposition converts the conclusion posture into "
        "the final disposition state that future proactive scheduling should honor."
    )
    if decision == "complete_lifecycle_disposition":
        rationale = (
            "The proactive lifecycle disposition keeps the lifecycle complete because "
            "the line can remain present without extra queue suppression."
        )
    elif decision == "buffer_lifecycle_disposition":
        rationale = (
            "The proactive lifecycle disposition buffers the lifecycle because "
            "the line should stay present but not immediately active."
        )
    elif decision == "pause_lifecycle_disposition":
        rationale = (
            "The proactive lifecycle disposition pauses the lifecycle because "
            "the line should remain open without immediate proactive continuation."
        )
    elif decision == "archive_lifecycle_disposition":
        rationale = (
            "The proactive lifecycle disposition archives the lifecycle because "
            "the line reached a clean ending and should leave the active queue."
        )
    elif decision == "retire_lifecycle_disposition":
        rationale = (
            "The proactive lifecycle disposition retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleDispositionDecision(
        status=status,
        disposition_key=disposition_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        conclusion_mode=conclusion_mode,
        disposition_mode=disposition_mode,
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
        selected_strategy_key=(
            lifecycle_conclusion_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_conclusion_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_conclusion_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_conclusion_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        conclusion_decision=conclusion_decision,
        active_sources=_compact(lifecycle_conclusion_decision.active_sources, limit=8),
        disposition_notes=_compact(disposition_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_standing_decision(
    *,
    lifecycle_disposition_decision: ProactiveLifecycleDispositionDecision,
) -> ProactiveLifecycleStandingDecision:
    current_stage_label = lifecycle_disposition_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_disposition_decision.lifecycle_state or "active"
    disposition_mode = (
        lifecycle_disposition_decision.disposition_mode
        or "paused_lifecycle_disposition"
    )
    disposition_decision = (
        lifecycle_disposition_decision.decision or "pause_lifecycle_disposition"
    )
    active_stage_label = lifecycle_disposition_decision.active_stage_label
    next_stage_label = lifecycle_disposition_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_disposition_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_disposition_decision.line_state or "steady"
    line_exit_mode = lifecycle_disposition_decision.line_exit_mode or "stay"
    status = lifecycle_disposition_decision.status or "hold"
    standing_mode = "paused_lifecycle_standing"
    decision = "pause_lifecycle_standing"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_disposition_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_disposition_decision.primary_source or "disposition"
    standing_notes: list[str] = list(lifecycle_disposition_decision.disposition_notes)
    standing_notes.append(f"disposition:{disposition_mode}")
    if line_state:
        standing_notes.append(f"line:{line_state}")
    if line_exit_mode:
        standing_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        standing_notes.append(f"active:{active_stage_label}")

    if disposition_decision == "complete_lifecycle_disposition":
        status = "active"
        standing_mode = "standing_lifecycle_standing"
        decision = "keep_lifecycle_standing"
        actionability = "keep"
        queue_override_status = None
    elif disposition_decision == "buffer_lifecycle_disposition":
        status = "scheduled"
        standing_mode = "buffered_lifecycle_standing"
        decision = "buffer_lifecycle_standing"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif disposition_decision == "pause_lifecycle_disposition":
        status = "hold"
        standing_mode = "paused_lifecycle_standing"
        decision = "pause_lifecycle_standing"
        actionability = "pause"
        queue_override_status = "hold"
    elif disposition_decision == "archive_lifecycle_disposition":
        status = "terminal"
        standing_mode = "archived_lifecycle_standing"
        decision = "archive_lifecycle_standing"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif disposition_decision == "retire_lifecycle_disposition":
        status = "terminal"
        standing_mode = "retired_lifecycle_standing"
        decision = "retire_lifecycle_standing"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        standing_notes.append("fallback_pause")

    standing_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_disposition_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_disposition_decision.changed
        or decision != "pause_lifecycle_standing"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle standing converts the disposition posture into "
        "the final standing state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_standing":
        rationale = (
            "The proactive lifecycle standing keeps the lifecycle standing because "
            "the line can remain present without extra queue suppression."
        )
    elif decision == "buffer_lifecycle_standing":
        rationale = (
            "The proactive lifecycle standing buffers the lifecycle because "
            "the line should stay present but not immediately active."
        )
    elif decision == "pause_lifecycle_standing":
        rationale = (
            "The proactive lifecycle standing pauses the lifecycle because "
            "the line should remain open without immediate proactive continuation."
        )
    elif decision == "archive_lifecycle_standing":
        rationale = (
            "The proactive lifecycle standing archives the lifecycle because "
            "the line reached a clean ending and should leave the active queue."
        )
    elif decision == "retire_lifecycle_standing":
        rationale = (
            "The proactive lifecycle standing retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleStandingDecision(
        status=status,
        standing_key=standing_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        disposition_mode=disposition_mode,
        standing_mode=standing_mode,
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
        selected_strategy_key=(
            lifecycle_disposition_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_disposition_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_disposition_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_disposition_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        disposition_decision=disposition_decision,
        active_sources=_compact(lifecycle_disposition_decision.active_sources, limit=8),
        standing_notes=_compact(standing_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_residency_decision(
    *,
    lifecycle_standing_decision: ProactiveLifecycleStandingDecision,
) -> ProactiveLifecycleResidencyDecision:
    current_stage_label = lifecycle_standing_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_standing_decision.lifecycle_state or "active"
    standing_mode = (
        lifecycle_standing_decision.standing_mode or "paused_lifecycle_standing"
    )
    standing_decision = (
        lifecycle_standing_decision.decision or "pause_lifecycle_standing"
    )
    active_stage_label = lifecycle_standing_decision.active_stage_label
    next_stage_label = lifecycle_standing_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_standing_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_standing_decision.line_state or "steady"
    line_exit_mode = lifecycle_standing_decision.line_exit_mode or "stay"
    status = lifecycle_standing_decision.status or "hold"
    residency_mode = "paused_lifecycle_residency"
    decision = "pause_lifecycle_residency"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_standing_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_standing_decision.primary_source or "standing"
    residency_notes: list[str] = list(lifecycle_standing_decision.standing_notes)
    residency_notes.append(f"standing:{standing_mode}")
    if line_state:
        residency_notes.append(f"line:{line_state}")
    if line_exit_mode:
        residency_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        residency_notes.append(f"active:{active_stage_label}")

    if standing_decision == "keep_lifecycle_standing":
        status = "active"
        residency_mode = "resident_lifecycle_residency"
        decision = "keep_lifecycle_residency"
        actionability = "keep"
        queue_override_status = None
    elif standing_decision == "buffer_lifecycle_standing":
        status = "scheduled"
        residency_mode = "buffered_lifecycle_residency"
        decision = "buffer_lifecycle_residency"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif standing_decision == "pause_lifecycle_standing":
        status = "hold"
        residency_mode = "paused_lifecycle_residency"
        decision = "pause_lifecycle_residency"
        actionability = "pause"
        queue_override_status = "hold"
    elif standing_decision == "archive_lifecycle_standing":
        status = "terminal"
        residency_mode = "archived_lifecycle_residency"
        decision = "archive_lifecycle_residency"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif standing_decision == "retire_lifecycle_standing":
        status = "terminal"
        residency_mode = "retired_lifecycle_residency"
        decision = "retire_lifecycle_residency"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        residency_notes.append("fallback_pause")

    residency_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_standing_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_standing_decision.changed
        or decision != "pause_lifecycle_residency"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle residency converts the standing posture into "
        "the final residency state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_residency":
        rationale = (
            "The proactive lifecycle residency keeps the lifecycle resident because "
            "the line should remain present for future proactive return."
        )
    elif decision == "buffer_lifecycle_residency":
        rationale = (
            "The proactive lifecycle residency buffers the lifecycle because "
            "the line should stay present but not immediately active."
        )
    elif decision == "pause_lifecycle_residency":
        rationale = (
            "The proactive lifecycle residency pauses the lifecycle because "
            "the line should preserve user space without immediate proactive continuation."
        )
    elif decision == "archive_lifecycle_residency":
        rationale = (
            "The proactive lifecycle residency archives the lifecycle because "
            "the line reached a clean ending and should leave active residency."
        )
    elif decision == "retire_lifecycle_residency":
        rationale = (
            "The proactive lifecycle residency retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleResidencyDecision(
        status=status,
        residency_key=residency_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        standing_mode=standing_mode,
        residency_mode=residency_mode,
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
        selected_strategy_key=(
            lifecycle_standing_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_standing_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_standing_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_standing_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        standing_decision=standing_decision,
        active_sources=_compact(lifecycle_standing_decision.active_sources, limit=8),
        residency_notes=_compact(residency_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_tenure_decision(
    *,
    lifecycle_residency_decision: ProactiveLifecycleResidencyDecision,
) -> ProactiveLifecycleTenureDecision:
    current_stage_label = lifecycle_residency_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_residency_decision.lifecycle_state or "active"
    residency_mode = (
        lifecycle_residency_decision.residency_mode or "paused_lifecycle_residency"
    )
    residency_decision = (
        lifecycle_residency_decision.decision or "pause_lifecycle_residency"
    )
    active_stage_label = lifecycle_residency_decision.active_stage_label
    next_stage_label = lifecycle_residency_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_residency_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_residency_decision.line_state or "steady"
    line_exit_mode = lifecycle_residency_decision.line_exit_mode or "stay"
    status = lifecycle_residency_decision.status or "hold"
    tenure_mode = "paused_lifecycle_tenure"
    decision = "pause_lifecycle_tenure"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_residency_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_residency_decision.primary_source or "residency"
    tenure_notes: list[str] = list(lifecycle_residency_decision.residency_notes)
    tenure_notes.append(f"residency:{residency_mode}")
    if line_state:
        tenure_notes.append(f"line:{line_state}")
    if line_exit_mode:
        tenure_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        tenure_notes.append(f"active:{active_stage_label}")

    if residency_decision == "keep_lifecycle_residency":
        status = "active"
        tenure_mode = "tenured_lifecycle_tenure"
        decision = "keep_lifecycle_tenure"
        actionability = "keep"
        queue_override_status = None
    elif residency_decision == "buffer_lifecycle_residency":
        status = "scheduled"
        tenure_mode = "buffered_lifecycle_tenure"
        decision = "buffer_lifecycle_tenure"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif residency_decision == "pause_lifecycle_residency":
        status = "hold"
        tenure_mode = "paused_lifecycle_tenure"
        decision = "pause_lifecycle_tenure"
        actionability = "pause"
        queue_override_status = "hold"
    elif residency_decision == "archive_lifecycle_residency":
        status = "terminal"
        tenure_mode = "archived_lifecycle_tenure"
        decision = "archive_lifecycle_tenure"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif residency_decision == "retire_lifecycle_residency":
        status = "terminal"
        tenure_mode = "retired_lifecycle_tenure"
        decision = "retire_lifecycle_tenure"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        tenure_notes.append("fallback_pause")

    tenure_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_residency_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_residency_decision.changed
        or decision != "pause_lifecycle_tenure"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle tenure converts the residency posture into "
        "the final tenure state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_tenure":
        rationale = (
            "The proactive lifecycle tenure keeps the lifecycle tenured because "
            "the line should remain durably available for future proactive return."
        )
    elif decision == "buffer_lifecycle_tenure":
        rationale = (
            "The proactive lifecycle tenure buffers the lifecycle because "
            "the line should stay durably present without immediate activity."
        )
    elif decision == "pause_lifecycle_tenure":
        rationale = (
            "The proactive lifecycle tenure pauses the lifecycle because "
            "the line should preserve durable user space without immediate continuation."
        )
    elif decision == "archive_lifecycle_tenure":
        rationale = (
            "The proactive lifecycle tenure archives the lifecycle because "
            "the line reached a clean ending and should leave durable availability."
        )
    elif decision == "retire_lifecycle_tenure":
        rationale = (
            "The proactive lifecycle tenure retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleTenureDecision(
        status=status,
        tenure_key=tenure_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        residency_mode=residency_mode,
        tenure_mode=tenure_mode,
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
        selected_strategy_key=(
            lifecycle_residency_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_residency_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_residency_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_residency_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        residency_decision=residency_decision,
        active_sources=_compact(lifecycle_residency_decision.active_sources, limit=8),
        tenure_notes=_compact(tenure_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_persistence_decision(
    *,
    lifecycle_tenure_decision: ProactiveLifecycleTenureDecision,
) -> ProactiveLifecyclePersistenceDecision:
    current_stage_label = lifecycle_tenure_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_tenure_decision.lifecycle_state or "active"
    tenure_mode = lifecycle_tenure_decision.tenure_mode or "paused_lifecycle_tenure"
    tenure_decision = lifecycle_tenure_decision.decision or "pause_lifecycle_tenure"
    active_stage_label = lifecycle_tenure_decision.active_stage_label
    next_stage_label = lifecycle_tenure_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_tenure_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_tenure_decision.line_state or "steady"
    line_exit_mode = lifecycle_tenure_decision.line_exit_mode or "stay"
    status = lifecycle_tenure_decision.status or "hold"
    persistence_mode = "paused_lifecycle_persistence"
    decision = "pause_lifecycle_persistence"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_tenure_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_tenure_decision.primary_source or "tenure"
    persistence_notes: list[str] = list(lifecycle_tenure_decision.tenure_notes)
    persistence_notes.append(f"tenure:{tenure_mode}")
    if line_state:
        persistence_notes.append(f"line:{line_state}")
    if line_exit_mode:
        persistence_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        persistence_notes.append(f"active:{active_stage_label}")

    if tenure_decision == "keep_lifecycle_tenure":
        status = "active"
        persistence_mode = "persistent_lifecycle_persistence"
        decision = "keep_lifecycle_persistence"
        actionability = "keep"
        queue_override_status = None
    elif tenure_decision == "buffer_lifecycle_tenure":
        status = "scheduled"
        persistence_mode = "buffered_lifecycle_persistence"
        decision = "buffer_lifecycle_persistence"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif tenure_decision == "pause_lifecycle_tenure":
        status = "hold"
        persistence_mode = "paused_lifecycle_persistence"
        decision = "pause_lifecycle_persistence"
        actionability = "pause"
        queue_override_status = "hold"
    elif tenure_decision == "archive_lifecycle_tenure":
        status = "terminal"
        persistence_mode = "archived_lifecycle_persistence"
        decision = "archive_lifecycle_persistence"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif tenure_decision == "retire_lifecycle_tenure":
        status = "terminal"
        persistence_mode = "retired_lifecycle_persistence"
        decision = "retire_lifecycle_persistence"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        persistence_notes.append("fallback_pause")

    persistence_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_tenure_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_tenure_decision.changed
        or decision != "pause_lifecycle_persistence"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle persistence converts the tenure posture into "
        "the final persistence state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_persistence":
        rationale = (
            "The proactive lifecycle persistence keeps the lifecycle persistent because "
            "the line should remain reliably present for future proactive return."
        )
    elif decision == "buffer_lifecycle_persistence":
        rationale = (
            "The proactive lifecycle persistence buffers the lifecycle because "
            "the line should stay reliably present without immediate activity."
        )
    elif decision == "pause_lifecycle_persistence":
        rationale = (
            "The proactive lifecycle persistence pauses the lifecycle because "
            "the line should preserve long-lived user space without immediate continuation."
        )
    elif decision == "archive_lifecycle_persistence":
        rationale = (
            "The proactive lifecycle persistence archives the lifecycle because "
            "the line reached a clean ending and should leave persistent availability."
        )
    elif decision == "retire_lifecycle_persistence":
        rationale = (
            "The proactive lifecycle persistence retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecyclePersistenceDecision(
        status=status,
        persistence_key=persistence_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        tenure_mode=tenure_mode,
        persistence_mode=persistence_mode,
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
        selected_strategy_key=(
            lifecycle_tenure_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_tenure_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_tenure_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_tenure_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        tenure_decision=tenure_decision,
        active_sources=_compact(lifecycle_tenure_decision.active_sources, limit=8),
        persistence_notes=_compact(persistence_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_durability_decision(
    *,
    lifecycle_persistence_decision: ProactiveLifecyclePersistenceDecision,
) -> ProactiveLifecycleDurabilityDecision:
    current_stage_label = lifecycle_persistence_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_persistence_decision.lifecycle_state or "active"
    persistence_mode = (
        lifecycle_persistence_decision.persistence_mode
        or "paused_lifecycle_persistence"
    )
    persistence_decision = (
        lifecycle_persistence_decision.decision or "pause_lifecycle_persistence"
    )
    active_stage_label = lifecycle_persistence_decision.active_stage_label
    next_stage_label = lifecycle_persistence_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_persistence_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_persistence_decision.line_state or "steady"
    line_exit_mode = lifecycle_persistence_decision.line_exit_mode or "stay"
    status = lifecycle_persistence_decision.status or "hold"
    durability_mode = "paused_lifecycle_durability"
    decision = "pause_lifecycle_durability"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_persistence_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_persistence_decision.primary_source or "persistence"
    durability_notes: list[str] = list(lifecycle_persistence_decision.persistence_notes)
    durability_notes.append(f"persistence:{persistence_mode}")
    if line_state:
        durability_notes.append(f"line:{line_state}")
    if line_exit_mode:
        durability_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        durability_notes.append(f"active:{active_stage_label}")

    if persistence_decision == "keep_lifecycle_persistence":
        status = "active"
        durability_mode = "durable_lifecycle_durability"
        decision = "keep_lifecycle_durability"
        actionability = "keep"
        queue_override_status = None
    elif persistence_decision == "buffer_lifecycle_persistence":
        status = "scheduled"
        durability_mode = "buffered_lifecycle_durability"
        decision = "buffer_lifecycle_durability"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif persistence_decision == "pause_lifecycle_persistence":
        status = "hold"
        durability_mode = "paused_lifecycle_durability"
        decision = "pause_lifecycle_durability"
        actionability = "pause"
        queue_override_status = "hold"
    elif persistence_decision == "archive_lifecycle_persistence":
        status = "terminal"
        durability_mode = "archived_lifecycle_durability"
        decision = "archive_lifecycle_durability"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif persistence_decision == "retire_lifecycle_persistence":
        status = "terminal"
        durability_mode = "retired_lifecycle_durability"
        decision = "retire_lifecycle_durability"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        durability_notes.append("fallback_pause")

    durability_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_persistence_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_persistence_decision.changed
        or decision != "pause_lifecycle_durability"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle durability converts the persistence posture into "
        "the final durable state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_durability":
        rationale = (
            "The proactive lifecycle durability keeps the lifecycle durable because "
            "the line should remain long-lived and steadily available for future return."
        )
    elif decision == "buffer_lifecycle_durability":
        rationale = (
            "The proactive lifecycle durability buffers the lifecycle because "
            "the line should remain durable while staying out of immediate motion."
        )
    elif decision == "pause_lifecycle_durability":
        rationale = (
            "The proactive lifecycle durability pauses the lifecycle because "
            "the line should preserve durable space without immediate continuation."
        )
    elif decision == "archive_lifecycle_durability":
        rationale = (
            "The proactive lifecycle durability archives the lifecycle because "
            "the line reached a clean durable ending."
        )
    elif decision == "retire_lifecycle_durability":
        rationale = (
            "The proactive lifecycle durability retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleDurabilityDecision(
        status=status,
        durability_key=durability_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        persistence_mode=persistence_mode,
        durability_mode=durability_mode,
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
        selected_strategy_key=(
            lifecycle_persistence_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_persistence_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_persistence_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_persistence_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        persistence_decision=persistence_decision,
        active_sources=_compact(lifecycle_persistence_decision.active_sources, limit=8),
        durability_notes=_compact(durability_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_longevity_decision(
    *,
    lifecycle_durability_decision: ProactiveLifecycleDurabilityDecision,
) -> ProactiveLifecycleLongevityDecision:
    current_stage_label = lifecycle_durability_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_durability_decision.lifecycle_state or "active"
    durability_mode = (
        lifecycle_durability_decision.durability_mode
        or "paused_lifecycle_durability"
    )
    durability_decision = (
        lifecycle_durability_decision.decision or "pause_lifecycle_durability"
    )
    active_stage_label = lifecycle_durability_decision.active_stage_label
    next_stage_label = lifecycle_durability_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_durability_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_durability_decision.line_state or "steady"
    line_exit_mode = lifecycle_durability_decision.line_exit_mode or "stay"
    status = lifecycle_durability_decision.status or "hold"
    longevity_mode = "paused_lifecycle_longevity"
    decision = "pause_lifecycle_longevity"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_durability_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_durability_decision.primary_source or "durability"
    longevity_notes: list[str] = list(lifecycle_durability_decision.durability_notes)
    longevity_notes.append(f"durability:{durability_mode}")
    if line_state:
        longevity_notes.append(f"line:{line_state}")
    if line_exit_mode:
        longevity_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        longevity_notes.append(f"active:{active_stage_label}")

    if durability_decision == "keep_lifecycle_durability":
        status = "active"
        longevity_mode = "enduring_lifecycle_longevity"
        decision = "keep_lifecycle_longevity"
        actionability = "keep"
        queue_override_status = None
    elif durability_decision == "buffer_lifecycle_durability":
        status = "scheduled"
        longevity_mode = "buffered_lifecycle_longevity"
        decision = "buffer_lifecycle_longevity"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif durability_decision == "pause_lifecycle_durability":
        status = "hold"
        longevity_mode = "paused_lifecycle_longevity"
        decision = "pause_lifecycle_longevity"
        actionability = "pause"
        queue_override_status = "hold"
    elif durability_decision == "archive_lifecycle_durability":
        status = "terminal"
        longevity_mode = "archived_lifecycle_longevity"
        decision = "archive_lifecycle_longevity"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif durability_decision == "retire_lifecycle_durability":
        status = "terminal"
        longevity_mode = "retired_lifecycle_longevity"
        decision = "retire_lifecycle_longevity"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        longevity_notes.append("fallback_pause")

    longevity_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_durability_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_durability_decision.changed
        or decision != "pause_lifecycle_longevity"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle longevity converts the durability posture into "
        "the final long-lived state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_longevity":
        rationale = (
            "The proactive lifecycle longevity keeps the lifecycle enduring because "
            "the line should stay available over a longer horizon for future return."
        )
    elif decision == "buffer_lifecycle_longevity":
        rationale = (
            "The proactive lifecycle longevity buffers the lifecycle because "
            "the line should remain long-lived without immediate motion."
        )
    elif decision == "pause_lifecycle_longevity":
        rationale = (
            "The proactive lifecycle longevity pauses the lifecycle because "
            "the line should preserve long-horizon space without immediate continuation."
        )
    elif decision == "archive_lifecycle_longevity":
        rationale = (
            "The proactive lifecycle longevity archives the lifecycle because "
            "the line reached a clean long-horizon ending."
        )
    elif decision == "retire_lifecycle_longevity":
        rationale = (
            "The proactive lifecycle longevity retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleLongevityDecision(
        status=status,
        longevity_key=longevity_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        durability_mode=durability_mode,
        longevity_mode=longevity_mode,
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
        selected_strategy_key=(
            lifecycle_durability_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_durability_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_durability_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_durability_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        durability_decision=durability_decision,
        active_sources=_compact(lifecycle_durability_decision.active_sources, limit=8),
        longevity_notes=_compact(longevity_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_legacy_decision(
    *,
    lifecycle_longevity_decision: ProactiveLifecycleLongevityDecision,
) -> ProactiveLifecycleLegacyDecision:
    current_stage_label = lifecycle_longevity_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_longevity_decision.lifecycle_state or "active"
    longevity_mode = (
        lifecycle_longevity_decision.longevity_mode or "paused_lifecycle_longevity"
    )
    longevity_decision = (
        lifecycle_longevity_decision.decision or "pause_lifecycle_longevity"
    )
    active_stage_label = lifecycle_longevity_decision.active_stage_label
    next_stage_label = lifecycle_longevity_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_longevity_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_longevity_decision.line_state or "steady"
    line_exit_mode = lifecycle_longevity_decision.line_exit_mode or "stay"
    status = lifecycle_longevity_decision.status or "hold"
    legacy_mode = "paused_lifecycle_legacy"
    decision = "pause_lifecycle_legacy"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_longevity_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_longevity_decision.primary_source or "longevity"
    legacy_notes: list[str] = list(lifecycle_longevity_decision.longevity_notes)
    legacy_notes.append(f"longevity:{longevity_mode}")
    if line_state:
        legacy_notes.append(f"line:{line_state}")
    if line_exit_mode:
        legacy_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        legacy_notes.append(f"active:{active_stage_label}")

    if longevity_decision == "keep_lifecycle_longevity":
        status = "active"
        legacy_mode = "lasting_lifecycle_legacy"
        decision = "keep_lifecycle_legacy"
        actionability = "keep"
        queue_override_status = None
    elif longevity_decision == "buffer_lifecycle_longevity":
        status = "scheduled"
        legacy_mode = "buffered_lifecycle_legacy"
        decision = "buffer_lifecycle_legacy"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif longevity_decision == "pause_lifecycle_longevity":
        status = "hold"
        legacy_mode = "paused_lifecycle_legacy"
        decision = "pause_lifecycle_legacy"
        actionability = "pause"
        queue_override_status = "hold"
    elif longevity_decision == "archive_lifecycle_longevity":
        status = "terminal"
        legacy_mode = "archived_lifecycle_legacy"
        decision = "archive_lifecycle_legacy"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif longevity_decision == "retire_lifecycle_longevity":
        status = "terminal"
        legacy_mode = "retired_lifecycle_legacy"
        decision = "retire_lifecycle_legacy"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        legacy_notes.append("fallback_pause")

    legacy_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_longevity_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_longevity_decision.changed
        or decision != "pause_lifecycle_legacy"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle legacy converts the longevity posture into "
        "the final long-tail legacy state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_legacy":
        rationale = (
            "The proactive lifecycle legacy keeps the lifecycle lasting because "
            "the line should remain as an enduring long-tail return path."
        )
    elif decision == "buffer_lifecycle_legacy":
        rationale = (
            "The proactive lifecycle legacy buffers the lifecycle because "
            "the line should keep its legacy value without immediate motion."
        )
    elif decision == "pause_lifecycle_legacy":
        rationale = (
            "The proactive lifecycle legacy pauses the lifecycle because "
            "the line should preserve legacy space without immediate continuation."
        )
    elif decision == "archive_lifecycle_legacy":
        rationale = (
            "The proactive lifecycle legacy archives the lifecycle because "
            "the line reached a clean long-tail ending."
        )
    elif decision == "retire_lifecycle_legacy":
        rationale = (
            "The proactive lifecycle legacy retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleLegacyDecision(
        status=status,
        legacy_key=legacy_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        longevity_mode=longevity_mode,
        legacy_mode=legacy_mode,
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
        selected_strategy_key=(
            lifecycle_longevity_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_longevity_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_longevity_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_longevity_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        longevity_decision=longevity_decision,
        active_sources=_compact(lifecycle_longevity_decision.active_sources, limit=8),
        legacy_notes=_compact(legacy_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_heritage_decision(
    *,
    lifecycle_legacy_decision: ProactiveLifecycleLegacyDecision,
) -> ProactiveLifecycleHeritageDecision:
    current_stage_label = lifecycle_legacy_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_legacy_decision.lifecycle_state or "active"
    legacy_mode = lifecycle_legacy_decision.legacy_mode or "paused_lifecycle_legacy"
    legacy_decision = lifecycle_legacy_decision.decision or "pause_lifecycle_legacy"
    active_stage_label = lifecycle_legacy_decision.active_stage_label
    next_stage_label = lifecycle_legacy_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_legacy_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_legacy_decision.line_state or "steady"
    line_exit_mode = lifecycle_legacy_decision.line_exit_mode or "stay"
    status = lifecycle_legacy_decision.status or "hold"
    heritage_mode = "paused_lifecycle_heritage"
    decision = "pause_lifecycle_heritage"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_legacy_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_legacy_decision.primary_source or "legacy"
    heritage_notes: list[str] = list(lifecycle_legacy_decision.legacy_notes)
    heritage_notes.append(f"legacy:{legacy_mode}")
    if line_state:
        heritage_notes.append(f"line:{line_state}")
    if line_exit_mode:
        heritage_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        heritage_notes.append(f"active:{active_stage_label}")

    if legacy_decision == "keep_lifecycle_legacy":
        status = "active"
        heritage_mode = "preserved_lifecycle_heritage"
        decision = "keep_lifecycle_heritage"
        actionability = "keep"
        queue_override_status = None
    elif legacy_decision == "buffer_lifecycle_legacy":
        status = "scheduled"
        heritage_mode = "buffered_lifecycle_heritage"
        decision = "buffer_lifecycle_heritage"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif legacy_decision == "pause_lifecycle_legacy":
        status = "hold"
        heritage_mode = "paused_lifecycle_heritage"
        decision = "pause_lifecycle_heritage"
        actionability = "pause"
        queue_override_status = "hold"
    elif legacy_decision == "archive_lifecycle_legacy":
        status = "terminal"
        heritage_mode = "archived_lifecycle_heritage"
        decision = "archive_lifecycle_heritage"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif legacy_decision == "retire_lifecycle_legacy":
        status = "terminal"
        heritage_mode = "retired_lifecycle_heritage"
        decision = "retire_lifecycle_heritage"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        heritage_notes.append("fallback_pause")

    heritage_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_legacy_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_legacy_decision.changed
        or decision != "pause_lifecycle_heritage"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle heritage converts the legacy posture into "
        "the final preserved heritage state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_heritage":
        rationale = (
            "The proactive lifecycle heritage keeps the lifecycle preserved because "
            "the line should remain as a durable heritage path for future return."
        )
    elif decision == "buffer_lifecycle_heritage":
        rationale = (
            "The proactive lifecycle heritage buffers the lifecycle because "
            "the line should preserve its heritage value without immediate motion."
        )
    elif decision == "pause_lifecycle_heritage":
        rationale = (
            "The proactive lifecycle heritage pauses the lifecycle because "
            "the line should preserve heritage space without immediate continuation."
        )
    elif decision == "archive_lifecycle_heritage":
        rationale = (
            "The proactive lifecycle heritage archives the lifecycle because "
            "the line reached a clean preserved ending."
        )
    elif decision == "retire_lifecycle_heritage":
        rationale = (
            "The proactive lifecycle heritage retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleHeritageDecision(
        status=status,
        heritage_key=heritage_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        legacy_mode=legacy_mode,
        heritage_mode=heritage_mode,
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
        selected_strategy_key=(lifecycle_legacy_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_legacy_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_legacy_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_legacy_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        legacy_decision=legacy_decision,
        active_sources=_compact(lifecycle_legacy_decision.active_sources, limit=8),
        heritage_notes=_compact(heritage_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_lineage_decision(
    *,
    lifecycle_heritage_decision: ProactiveLifecycleHeritageDecision,
) -> ProactiveLifecycleLineageDecision:
    current_stage_label = lifecycle_heritage_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_heritage_decision.lifecycle_state or "active"
    heritage_mode = (
        lifecycle_heritage_decision.heritage_mode or "paused_lifecycle_heritage"
    )
    heritage_decision = (
        lifecycle_heritage_decision.decision or "pause_lifecycle_heritage"
    )
    active_stage_label = lifecycle_heritage_decision.active_stage_label
    next_stage_label = lifecycle_heritage_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_heritage_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_heritage_decision.line_state or "steady"
    line_exit_mode = lifecycle_heritage_decision.line_exit_mode or "stay"
    status = lifecycle_heritage_decision.status or "hold"
    lineage_mode = "paused_lifecycle_lineage"
    decision = "pause_lifecycle_lineage"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_heritage_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_heritage_decision.primary_source or "heritage"
    lineage_notes: list[str] = list(lifecycle_heritage_decision.heritage_notes)
    lineage_notes.append(f"heritage:{heritage_mode}")
    if line_state:
        lineage_notes.append(f"line:{line_state}")
    if line_exit_mode:
        lineage_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        lineage_notes.append(f"active:{active_stage_label}")

    if heritage_decision == "keep_lifecycle_heritage":
        status = "active"
        lineage_mode = "preserved_lifecycle_lineage"
        decision = "keep_lifecycle_lineage"
        actionability = "keep"
        queue_override_status = None
    elif heritage_decision == "buffer_lifecycle_heritage":
        status = "scheduled"
        lineage_mode = "buffered_lifecycle_lineage"
        decision = "buffer_lifecycle_lineage"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif heritage_decision == "pause_lifecycle_heritage":
        status = "hold"
        lineage_mode = "paused_lifecycle_lineage"
        decision = "pause_lifecycle_lineage"
        actionability = "pause"
        queue_override_status = "hold"
    elif heritage_decision == "archive_lifecycle_heritage":
        status = "terminal"
        lineage_mode = "archived_lifecycle_lineage"
        decision = "archive_lifecycle_lineage"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif heritage_decision == "retire_lifecycle_heritage":
        status = "terminal"
        lineage_mode = "retired_lifecycle_lineage"
        decision = "retire_lifecycle_lineage"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        lineage_notes.append("fallback_pause")

    lineage_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_heritage_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_heritage_decision.changed
        or decision != "pause_lifecycle_lineage"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle lineage converts the heritage posture into "
        "the final preserved lineage state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_lineage":
        rationale = (
            "The proactive lifecycle lineage keeps the lifecycle preserved because "
            "the line should remain as a durable lineage path for future return."
        )
    elif decision == "buffer_lifecycle_lineage":
        rationale = (
            "The proactive lifecycle lineage buffers the lifecycle because "
            "the line should preserve its lineage value without immediate motion."
        )
    elif decision == "pause_lifecycle_lineage":
        rationale = (
            "The proactive lifecycle lineage pauses the lifecycle because "
            "the line should preserve lineage space without immediate continuation."
        )
    elif decision == "archive_lifecycle_lineage":
        rationale = (
            "The proactive lifecycle lineage archives the lifecycle because "
            "the line reached a clean preserved ending."
        )
    elif decision == "retire_lifecycle_lineage":
        rationale = (
            "The proactive lifecycle lineage retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleLineageDecision(
        status=status,
        lineage_key=lineage_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        heritage_mode=heritage_mode,
        lineage_mode=lineage_mode,
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
        selected_strategy_key=(
            lifecycle_heritage_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_heritage_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_heritage_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_heritage_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        heritage_decision=heritage_decision,
        active_sources=_compact(lifecycle_heritage_decision.active_sources, limit=8),
        lineage_notes=_compact(lineage_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_ancestry_decision(
    *,
    lifecycle_lineage_decision: ProactiveLifecycleLineageDecision,
) -> ProactiveLifecycleAncestryDecision:
    current_stage_label = lifecycle_lineage_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_lineage_decision.lifecycle_state or "active"
    lineage_mode = (
        lifecycle_lineage_decision.lineage_mode or "paused_lifecycle_lineage"
    )
    lineage_decision = (
        lifecycle_lineage_decision.decision or "pause_lifecycle_lineage"
    )
    active_stage_label = lifecycle_lineage_decision.active_stage_label
    next_stage_label = lifecycle_lineage_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_lineage_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_lineage_decision.line_state or "steady"
    line_exit_mode = lifecycle_lineage_decision.line_exit_mode or "stay"
    status = lifecycle_lineage_decision.status or "hold"
    ancestry_mode = "paused_lifecycle_ancestry"
    decision = "pause_lifecycle_ancestry"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_lineage_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_lineage_decision.primary_source or "lineage"
    ancestry_notes: list[str] = list(lifecycle_lineage_decision.lineage_notes)
    ancestry_notes.append(f"lineage:{lineage_mode}")
    if line_state:
        ancestry_notes.append(f"line:{line_state}")
    if line_exit_mode:
        ancestry_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        ancestry_notes.append(f"active:{active_stage_label}")

    if lineage_decision == "keep_lifecycle_lineage":
        status = "active"
        ancestry_mode = "preserved_lifecycle_ancestry"
        decision = "keep_lifecycle_ancestry"
        actionability = "keep"
        queue_override_status = None
    elif lineage_decision == "buffer_lifecycle_lineage":
        status = "scheduled"
        ancestry_mode = "buffered_lifecycle_ancestry"
        decision = "buffer_lifecycle_ancestry"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif lineage_decision == "pause_lifecycle_lineage":
        status = "hold"
        ancestry_mode = "paused_lifecycle_ancestry"
        decision = "pause_lifecycle_ancestry"
        actionability = "pause"
        queue_override_status = "hold"
    elif lineage_decision == "archive_lifecycle_lineage":
        status = "terminal"
        ancestry_mode = "archived_lifecycle_ancestry"
        decision = "archive_lifecycle_ancestry"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif lineage_decision == "retire_lifecycle_lineage":
        status = "terminal"
        ancestry_mode = "retired_lifecycle_ancestry"
        decision = "retire_lifecycle_ancestry"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        ancestry_notes.append("fallback_pause")

    ancestry_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_lineage_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_lineage_decision.changed
        or decision != "pause_lifecycle_ancestry"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle ancestry converts the lineage posture into "
        "the final preserved ancestry state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_ancestry":
        rationale = (
            "The proactive lifecycle ancestry keeps the lifecycle preserved because "
            "the line should remain as a durable ancestry path for future return."
        )
    elif decision == "buffer_lifecycle_ancestry":
        rationale = (
            "The proactive lifecycle ancestry buffers the lifecycle because "
            "the line should preserve its ancestry value without immediate motion."
        )
    elif decision == "pause_lifecycle_ancestry":
        rationale = (
            "The proactive lifecycle ancestry pauses the lifecycle because "
            "the line should preserve ancestry space without immediate continuation."
        )
    elif decision == "archive_lifecycle_ancestry":
        rationale = (
            "The proactive lifecycle ancestry archives the lifecycle because "
            "the line reached a clean preserved ending."
        )
    elif decision == "retire_lifecycle_ancestry":
        rationale = (
            "The proactive lifecycle ancestry retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleAncestryDecision(
        status=status,
        ancestry_key=ancestry_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        lineage_mode=lineage_mode,
        ancestry_mode=ancestry_mode,
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
        selected_strategy_key=(
            lifecycle_lineage_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_lineage_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_lineage_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_lineage_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        lineage_decision=lineage_decision,
        active_sources=_compact(lifecycle_lineage_decision.active_sources, limit=8),
        ancestry_notes=_compact(ancestry_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_provenance_decision(
    *,
    lifecycle_ancestry_decision: ProactiveLifecycleAncestryDecision,
) -> ProactiveLifecycleProvenanceDecision:
    current_stage_label = lifecycle_ancestry_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_ancestry_decision.lifecycle_state or "active"
    ancestry_mode = (
        lifecycle_ancestry_decision.ancestry_mode or "paused_lifecycle_ancestry"
    )
    ancestry_decision = (
        lifecycle_ancestry_decision.decision or "pause_lifecycle_ancestry"
    )
    active_stage_label = lifecycle_ancestry_decision.active_stage_label
    next_stage_label = lifecycle_ancestry_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_ancestry_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_ancestry_decision.line_state or "steady"
    line_exit_mode = lifecycle_ancestry_decision.line_exit_mode or "stay"
    status = lifecycle_ancestry_decision.status or "hold"
    provenance_mode = "paused_lifecycle_provenance"
    decision = "pause_lifecycle_provenance"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_ancestry_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_ancestry_decision.primary_source or "ancestry"
    provenance_notes: list[str] = list(lifecycle_ancestry_decision.ancestry_notes)
    provenance_notes.append(f"ancestry:{ancestry_mode}")
    if line_state:
        provenance_notes.append(f"line:{line_state}")
    if line_exit_mode:
        provenance_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        provenance_notes.append(f"active:{active_stage_label}")

    if ancestry_decision == "keep_lifecycle_ancestry":
        status = "active"
        provenance_mode = "preserved_lifecycle_provenance"
        decision = "keep_lifecycle_provenance"
        actionability = "keep"
        queue_override_status = None
    elif ancestry_decision == "buffer_lifecycle_ancestry":
        status = "scheduled"
        provenance_mode = "buffered_lifecycle_provenance"
        decision = "buffer_lifecycle_provenance"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif ancestry_decision == "pause_lifecycle_ancestry":
        status = "hold"
        provenance_mode = "paused_lifecycle_provenance"
        decision = "pause_lifecycle_provenance"
        actionability = "pause"
        queue_override_status = "hold"
    elif ancestry_decision == "archive_lifecycle_ancestry":
        status = "terminal"
        provenance_mode = "archived_lifecycle_provenance"
        decision = "archive_lifecycle_provenance"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif ancestry_decision == "retire_lifecycle_ancestry":
        status = "terminal"
        provenance_mode = "retired_lifecycle_provenance"
        decision = "retire_lifecycle_provenance"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        provenance_notes.append("fallback_pause")

    provenance_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_ancestry_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_ancestry_decision.changed
        or decision != "pause_lifecycle_provenance"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle provenance converts the ancestry posture into "
        "the final preserved provenance state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_provenance":
        rationale = (
            "The proactive lifecycle provenance keeps the lifecycle preserved because "
            "the line should remain as a durable provenance path for future return."
        )
    elif decision == "buffer_lifecycle_provenance":
        rationale = (
            "The proactive lifecycle provenance buffers the lifecycle because "
            "the line should preserve its provenance value without immediate motion."
        )
    elif decision == "pause_lifecycle_provenance":
        rationale = (
            "The proactive lifecycle provenance pauses the lifecycle because "
            "the line should preserve provenance space without immediate continuation."
        )
    elif decision == "archive_lifecycle_provenance":
        rationale = (
            "The proactive lifecycle provenance archives the lifecycle because "
            "the line reached a clean preserved ending."
        )
    elif decision == "retire_lifecycle_provenance":
        rationale = (
            "The proactive lifecycle provenance retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleProvenanceDecision(
        status=status,
        provenance_key=provenance_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        ancestry_mode=ancestry_mode,
        provenance_mode=provenance_mode,
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
        selected_strategy_key=(
            lifecycle_ancestry_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_ancestry_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_ancestry_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_ancestry_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        ancestry_decision=ancestry_decision,
        active_sources=_compact(lifecycle_ancestry_decision.active_sources, limit=8),
        provenance_notes=_compact(provenance_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_origin_decision(
    *,
    lifecycle_provenance_decision: ProactiveLifecycleProvenanceDecision,
) -> ProactiveLifecycleOriginDecision:
    current_stage_label = lifecycle_provenance_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_provenance_decision.lifecycle_state or "active"
    provenance_mode = (
        lifecycle_provenance_decision.provenance_mode
        or "paused_lifecycle_provenance"
    )
    provenance_decision = (
        lifecycle_provenance_decision.decision or "pause_lifecycle_provenance"
    )
    active_stage_label = lifecycle_provenance_decision.active_stage_label
    next_stage_label = lifecycle_provenance_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_provenance_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_provenance_decision.line_state or "steady"
    line_exit_mode = lifecycle_provenance_decision.line_exit_mode or "stay"
    status = lifecycle_provenance_decision.status or "hold"
    origin_mode = "paused_lifecycle_origin"
    decision = "pause_lifecycle_origin"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_provenance_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_provenance_decision.primary_source or "provenance"
    origin_notes: list[str] = list(lifecycle_provenance_decision.provenance_notes)
    origin_notes.append(f"provenance:{provenance_mode}")
    if line_state:
        origin_notes.append(f"line:{line_state}")
    if line_exit_mode:
        origin_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        origin_notes.append(f"active:{active_stage_label}")

    if provenance_decision == "keep_lifecycle_provenance":
        status = "active"
        origin_mode = "preserved_lifecycle_origin"
        decision = "keep_lifecycle_origin"
        actionability = "keep"
        queue_override_status = None
    elif provenance_decision == "buffer_lifecycle_provenance":
        status = "scheduled"
        origin_mode = "buffered_lifecycle_origin"
        decision = "buffer_lifecycle_origin"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif provenance_decision == "pause_lifecycle_provenance":
        status = "hold"
        origin_mode = "paused_lifecycle_origin"
        decision = "pause_lifecycle_origin"
        actionability = "pause"
        queue_override_status = "hold"
    elif provenance_decision == "archive_lifecycle_provenance":
        status = "terminal"
        origin_mode = "archived_lifecycle_origin"
        decision = "archive_lifecycle_origin"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif provenance_decision == "retire_lifecycle_provenance":
        status = "terminal"
        origin_mode = "retired_lifecycle_origin"
        decision = "retire_lifecycle_origin"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        origin_notes.append("fallback_pause")

    origin_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_provenance_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_provenance_decision.changed
        or decision != "pause_lifecycle_origin"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle origin converts the provenance posture into "
        "the final preserved origin state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_origin":
        rationale = (
            "The proactive lifecycle origin keeps the lifecycle preserved because "
            "the line should remain available as a stable origin point for future return."
        )
    elif decision == "buffer_lifecycle_origin":
        rationale = (
            "The proactive lifecycle origin buffers the lifecycle because "
            "the line should preserve its origin value without immediate motion."
        )
    elif decision == "pause_lifecycle_origin":
        rationale = (
            "The proactive lifecycle origin pauses the lifecycle because "
            "the line should preserve origin space without immediate continuation."
        )
    elif decision == "archive_lifecycle_origin":
        rationale = (
            "The proactive lifecycle origin archives the lifecycle because "
            "the line reached a clean preserved ending."
        )
    elif decision == "retire_lifecycle_origin":
        rationale = (
            "The proactive lifecycle origin retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleOriginDecision(
        status=status,
        origin_key=origin_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        provenance_mode=provenance_mode,
        origin_mode=origin_mode,
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
        selected_strategy_key=(
            lifecycle_provenance_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_provenance_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_provenance_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_provenance_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        provenance_decision=provenance_decision,
        active_sources=_compact(lifecycle_provenance_decision.active_sources, limit=8),
        origin_notes=_compact(origin_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_root_decision(
    *,
    lifecycle_origin_decision: ProactiveLifecycleOriginDecision,
) -> ProactiveLifecycleRootDecision:
    current_stage_label = lifecycle_origin_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_origin_decision.lifecycle_state or "active"
    origin_mode = lifecycle_origin_decision.origin_mode or "paused_lifecycle_origin"
    origin_decision = lifecycle_origin_decision.decision or "pause_lifecycle_origin"
    active_stage_label = lifecycle_origin_decision.active_stage_label
    next_stage_label = lifecycle_origin_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_origin_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_origin_decision.line_state or "steady"
    line_exit_mode = lifecycle_origin_decision.line_exit_mode or "stay"
    status = lifecycle_origin_decision.status or "hold"
    root_mode = "paused_lifecycle_root"
    decision = "pause_lifecycle_root"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_origin_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_origin_decision.primary_source or "origin"
    root_notes: list[str] = list(lifecycle_origin_decision.origin_notes)
    root_notes.append(f"origin:{origin_mode}")
    if line_state:
        root_notes.append(f"line:{line_state}")
    if line_exit_mode:
        root_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        root_notes.append(f"active:{active_stage_label}")

    if origin_decision == "keep_lifecycle_origin":
        status = "active"
        root_mode = "preserved_lifecycle_root"
        decision = "keep_lifecycle_root"
        actionability = "keep"
        queue_override_status = None
    elif origin_decision == "buffer_lifecycle_origin":
        status = "scheduled"
        root_mode = "buffered_lifecycle_root"
        decision = "buffer_lifecycle_root"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif origin_decision == "pause_lifecycle_origin":
        status = "hold"
        root_mode = "paused_lifecycle_root"
        decision = "pause_lifecycle_root"
        actionability = "pause"
        queue_override_status = "hold"
    elif origin_decision == "archive_lifecycle_origin":
        status = "terminal"
        root_mode = "archived_lifecycle_root"
        decision = "archive_lifecycle_root"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif origin_decision == "retire_lifecycle_origin":
        status = "terminal"
        root_mode = "retired_lifecycle_root"
        decision = "retire_lifecycle_root"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        root_notes.append("fallback_pause")

    root_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_origin_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_origin_decision.changed
        or decision != "pause_lifecycle_root"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle root converts the origin posture into "
        "the final preserved root state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_root":
        rationale = (
            "The proactive lifecycle root keeps the lifecycle preserved because "
            "the line should remain available as a stable root point for future return."
        )
    elif decision == "buffer_lifecycle_root":
        rationale = (
            "The proactive lifecycle root buffers the lifecycle because "
            "the line should preserve its root value without immediate motion."
        )
    elif decision == "pause_lifecycle_root":
        rationale = (
            "The proactive lifecycle root pauses the lifecycle because "
            "the line should preserve root space without immediate continuation."
        )
    elif decision == "archive_lifecycle_root":
        rationale = (
            "The proactive lifecycle root archives the lifecycle because "
            "the line reached a clean preserved ending."
        )
    elif decision == "retire_lifecycle_root":
        rationale = (
            "The proactive lifecycle root retires the lifecycle because "
            "the line reached a terminal stop condition."
        )

    return ProactiveLifecycleRootDecision(
        status=status,
        root_key=root_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        origin_mode=origin_mode,
        root_mode=root_mode,
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
        selected_strategy_key=(lifecycle_origin_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(
            lifecycle_origin_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_origin_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_origin_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        origin_decision=origin_decision,
        active_sources=_compact(lifecycle_origin_decision.active_sources, limit=8),
        root_notes=_compact(root_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_foundation_decision(
    *,
    lifecycle_root_decision: ProactiveLifecycleRootDecision,
) -> ProactiveLifecycleFoundationDecision:
    current_stage_label = lifecycle_root_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_root_decision.lifecycle_state or "active"
    root_mode = lifecycle_root_decision.root_mode or "paused_lifecycle_root"
    root_decision = lifecycle_root_decision.decision or "pause_lifecycle_root"
    active_stage_label = lifecycle_root_decision.active_stage_label
    next_stage_label = lifecycle_root_decision.next_stage_label
    remaining_stage_count = max(0, int(lifecycle_root_decision.remaining_stage_count or 0))
    line_state = lifecycle_root_decision.line_state or "steady"
    line_exit_mode = lifecycle_root_decision.line_exit_mode or "stay"
    status = lifecycle_root_decision.status or "hold"
    foundation_mode = "paused_lifecycle_foundation"
    decision = "pause_lifecycle_foundation"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_root_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_root_decision.primary_source or "root"
    foundation_notes: list[str] = list(lifecycle_root_decision.root_notes)
    foundation_notes.append(f"root:{root_mode}")
    if line_state:
        foundation_notes.append(f"line:{line_state}")
    if line_exit_mode:
        foundation_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        foundation_notes.append(f"active:{active_stage_label}")

    if root_decision == "keep_lifecycle_root":
        status = "active"
        foundation_mode = "preserved_lifecycle_foundation"
        decision = "keep_lifecycle_foundation"
        actionability = "keep"
        queue_override_status = None
    elif root_decision == "buffer_lifecycle_root":
        status = "scheduled"
        foundation_mode = "buffered_lifecycle_foundation"
        decision = "buffer_lifecycle_foundation"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif root_decision == "pause_lifecycle_root":
        status = "hold"
        foundation_mode = "paused_lifecycle_foundation"
        decision = "pause_lifecycle_foundation"
        actionability = "pause"
        queue_override_status = "hold"
    elif root_decision == "archive_lifecycle_root":
        status = "terminal"
        foundation_mode = "archived_lifecycle_foundation"
        decision = "archive_lifecycle_foundation"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif root_decision == "retire_lifecycle_root":
        status = "terminal"
        foundation_mode = "retired_lifecycle_foundation"
        decision = "retire_lifecycle_foundation"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        foundation_notes.append("fallback_pause")

    foundation_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_root_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_root_decision.changed
        or decision != "pause_lifecycle_foundation"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle foundation converts the root posture into "
        "the final foundational state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_foundation":
        rationale = (
            "The proactive lifecycle foundation keeps the lifecycle preserved because "
            "the line should remain available as a stable foundation for future return."
        )
    elif decision == "buffer_lifecycle_foundation":
        rationale = (
            "The proactive lifecycle foundation buffers the lifecycle because "
            "the line should preserve its foundation without immediate motion."
        )
    elif decision == "pause_lifecycle_foundation":
        rationale = (
            "The proactive lifecycle foundation pauses the lifecycle because "
            "the line should preserve foundational space without immediate continuation."
        )
    elif decision == "archive_lifecycle_foundation":
        rationale = (
            "The proactive lifecycle foundation archives the lifecycle because "
            "the line reached a clean foundational ending."
        )
    elif decision == "retire_lifecycle_foundation":
        rationale = (
            "The proactive lifecycle foundation retires the lifecycle because "
            "the line reached a terminal foundational stop condition."
        )

    return ProactiveLifecycleFoundationDecision(
        status=status,
        foundation_key=foundation_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        root_mode=root_mode,
        foundation_mode=foundation_mode,
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
        selected_strategy_key=(lifecycle_root_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_root_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_root_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_root_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        root_decision=root_decision,
        active_sources=_compact(lifecycle_root_decision.active_sources, limit=8),
        foundation_notes=_compact(foundation_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_bedrock_decision(
    *,
    lifecycle_foundation_decision: ProactiveLifecycleFoundationDecision,
) -> ProactiveLifecycleBedrockDecision:
    current_stage_label = lifecycle_foundation_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_foundation_decision.lifecycle_state or "active"
    foundation_mode = (
        lifecycle_foundation_decision.foundation_mode or "paused_lifecycle_foundation"
    )
    foundation_decision = (
        lifecycle_foundation_decision.decision or "pause_lifecycle_foundation"
    )
    active_stage_label = lifecycle_foundation_decision.active_stage_label
    next_stage_label = lifecycle_foundation_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_foundation_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_foundation_decision.line_state or "steady"
    line_exit_mode = lifecycle_foundation_decision.line_exit_mode or "stay"
    status = lifecycle_foundation_decision.status or "hold"
    bedrock_mode = "paused_lifecycle_bedrock"
    decision = "pause_lifecycle_bedrock"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_foundation_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_foundation_decision.primary_source or "foundation"
    bedrock_notes: list[str] = list(lifecycle_foundation_decision.foundation_notes)
    bedrock_notes.append(f"foundation:{foundation_mode}")
    if line_state:
        bedrock_notes.append(f"line:{line_state}")
    if line_exit_mode:
        bedrock_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        bedrock_notes.append(f"active:{active_stage_label}")

    if foundation_decision == "keep_lifecycle_foundation":
        status = "active"
        bedrock_mode = "preserved_lifecycle_bedrock"
        decision = "keep_lifecycle_bedrock"
        actionability = "keep"
        queue_override_status = None
    elif foundation_decision == "buffer_lifecycle_foundation":
        status = "scheduled"
        bedrock_mode = "buffered_lifecycle_bedrock"
        decision = "buffer_lifecycle_bedrock"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif foundation_decision == "pause_lifecycle_foundation":
        status = "hold"
        bedrock_mode = "paused_lifecycle_bedrock"
        decision = "pause_lifecycle_bedrock"
        actionability = "pause"
        queue_override_status = "hold"
    elif foundation_decision == "archive_lifecycle_foundation":
        status = "terminal"
        bedrock_mode = "archived_lifecycle_bedrock"
        decision = "archive_lifecycle_bedrock"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif foundation_decision == "retire_lifecycle_foundation":
        status = "terminal"
        bedrock_mode = "retired_lifecycle_bedrock"
        decision = "retire_lifecycle_bedrock"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        bedrock_notes.append("fallback_pause")

    bedrock_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_foundation_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_foundation_decision.changed
        or decision != "pause_lifecycle_bedrock"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle bedrock converts the foundation posture into "
        "the final bedrock state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_bedrock":
        rationale = (
            "The proactive lifecycle bedrock keeps the lifecycle preserved because "
            "the line should remain available as a stable bedrock for future return."
        )
    elif decision == "buffer_lifecycle_bedrock":
        rationale = (
            "The proactive lifecycle bedrock buffers the lifecycle because "
            "the line should preserve its bedrock without immediate motion."
        )
    elif decision == "pause_lifecycle_bedrock":
        rationale = (
            "The proactive lifecycle bedrock pauses the lifecycle because "
            "the line should preserve bedrock space without immediate continuation."
        )
    elif decision == "archive_lifecycle_bedrock":
        rationale = (
            "The proactive lifecycle bedrock archives the lifecycle because "
            "the line reached a clean bedrock ending."
        )
    elif decision == "retire_lifecycle_bedrock":
        rationale = (
            "The proactive lifecycle bedrock retires the lifecycle because "
            "the line reached a terminal bedrock stop condition."
        )

    return ProactiveLifecycleBedrockDecision(
        status=status,
        bedrock_key=bedrock_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        foundation_mode=foundation_mode,
        bedrock_mode=bedrock_mode,
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
        selected_strategy_key=(
            lifecycle_foundation_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_foundation_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_foundation_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_foundation_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        foundation_decision=foundation_decision,
        active_sources=_compact(lifecycle_foundation_decision.active_sources, limit=8),
        bedrock_notes=_compact(bedrock_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_substrate_decision(
    *,
    lifecycle_bedrock_decision: ProactiveLifecycleBedrockDecision,
) -> ProactiveLifecycleSubstrateDecision:
    current_stage_label = lifecycle_bedrock_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_bedrock_decision.lifecycle_state or "active"
    bedrock_mode = lifecycle_bedrock_decision.bedrock_mode or "paused_lifecycle_bedrock"
    bedrock_decision = (
        lifecycle_bedrock_decision.decision or "pause_lifecycle_bedrock"
    )
    active_stage_label = lifecycle_bedrock_decision.active_stage_label
    next_stage_label = lifecycle_bedrock_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_bedrock_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_bedrock_decision.line_state or "steady"
    line_exit_mode = lifecycle_bedrock_decision.line_exit_mode or "stay"
    status = lifecycle_bedrock_decision.status or "hold"
    substrate_mode = "paused_lifecycle_substrate"
    decision = "pause_lifecycle_substrate"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_bedrock_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_bedrock_decision.primary_source or "bedrock"
    substrate_notes: list[str] = list(lifecycle_bedrock_decision.bedrock_notes)
    substrate_notes.append(f"bedrock:{bedrock_mode}")
    if line_state:
        substrate_notes.append(f"line:{line_state}")
    if line_exit_mode:
        substrate_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        substrate_notes.append(f"active:{active_stage_label}")

    if bedrock_decision == "keep_lifecycle_bedrock":
        status = "active"
        substrate_mode = "preserved_lifecycle_substrate"
        decision = "keep_lifecycle_substrate"
        actionability = "keep"
        queue_override_status = None
    elif bedrock_decision == "buffer_lifecycle_bedrock":
        status = "scheduled"
        substrate_mode = "buffered_lifecycle_substrate"
        decision = "buffer_lifecycle_substrate"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif bedrock_decision == "pause_lifecycle_bedrock":
        status = "hold"
        substrate_mode = "paused_lifecycle_substrate"
        decision = "pause_lifecycle_substrate"
        actionability = "pause"
        queue_override_status = "hold"
    elif bedrock_decision == "archive_lifecycle_bedrock":
        status = "terminal"
        substrate_mode = "archived_lifecycle_substrate"
        decision = "archive_lifecycle_substrate"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif bedrock_decision == "retire_lifecycle_bedrock":
        status = "terminal"
        substrate_mode = "retired_lifecycle_substrate"
        decision = "retire_lifecycle_substrate"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        substrate_notes.append("fallback_pause")

    substrate_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_bedrock_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_bedrock_decision.changed
        or decision != "pause_lifecycle_substrate"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle substrate converts the bedrock posture into "
        "the final substrate state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_substrate":
        rationale = (
            "The proactive lifecycle substrate keeps the lifecycle preserved because "
            "the line should remain available as a stable substrate for future return."
        )
    elif decision == "buffer_lifecycle_substrate":
        rationale = (
            "The proactive lifecycle substrate buffers the lifecycle because "
            "the line should preserve its substrate without immediate motion."
        )
    elif decision == "pause_lifecycle_substrate":
        rationale = (
            "The proactive lifecycle substrate pauses the lifecycle because "
            "the line should preserve substrate space without immediate continuation."
        )
    elif decision == "archive_lifecycle_substrate":
        rationale = (
            "The proactive lifecycle substrate archives the lifecycle because "
            "the line reached a clean substrate ending."
        )
    elif decision == "retire_lifecycle_substrate":
        rationale = (
            "The proactive lifecycle substrate retires the lifecycle because "
            "the line reached a terminal substrate stop condition."
        )

    return ProactiveLifecycleSubstrateDecision(
        status=status,
        substrate_key=substrate_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        bedrock_mode=bedrock_mode,
        substrate_mode=substrate_mode,
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
        selected_strategy_key=(lifecycle_bedrock_decision.selected_strategy_key or "none"),
        selected_pressure_mode=(lifecycle_bedrock_decision.selected_pressure_mode or "none"),
        selected_autonomy_signal=(
            lifecycle_bedrock_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(lifecycle_bedrock_decision.selected_delivery_mode or "none"),
        primary_source=primary_source,
        bedrock_decision=bedrock_decision,
        active_sources=_compact(lifecycle_bedrock_decision.active_sources, limit=8),
        substrate_notes=_compact(substrate_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_stratum_decision(
    *,
    lifecycle_substrate_decision: ProactiveLifecycleSubstrateDecision,
) -> ProactiveLifecycleStratumDecision:
    current_stage_label = lifecycle_substrate_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_substrate_decision.lifecycle_state or "active"
    substrate_mode = (
        lifecycle_substrate_decision.substrate_mode or "paused_lifecycle_substrate"
    )
    substrate_decision = (
        lifecycle_substrate_decision.decision or "pause_lifecycle_substrate"
    )
    active_stage_label = lifecycle_substrate_decision.active_stage_label
    next_stage_label = lifecycle_substrate_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_substrate_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_substrate_decision.line_state or "steady"
    line_exit_mode = lifecycle_substrate_decision.line_exit_mode or "stay"
    status = lifecycle_substrate_decision.status or "hold"
    stratum_mode = "paused_lifecycle_stratum"
    decision = "pause_lifecycle_stratum"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_substrate_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_substrate_decision.primary_source or "substrate"
    stratum_notes: list[str] = list(lifecycle_substrate_decision.substrate_notes)
    stratum_notes.append(f"substrate:{substrate_mode}")
    if line_state:
        stratum_notes.append(f"line:{line_state}")
    if line_exit_mode:
        stratum_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        stratum_notes.append(f"active:{active_stage_label}")

    if substrate_decision == "keep_lifecycle_substrate":
        status = "active"
        stratum_mode = "preserved_lifecycle_stratum"
        decision = "keep_lifecycle_stratum"
        actionability = "keep"
        queue_override_status = None
    elif substrate_decision == "buffer_lifecycle_substrate":
        status = "scheduled"
        stratum_mode = "buffered_lifecycle_stratum"
        decision = "buffer_lifecycle_stratum"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif substrate_decision == "pause_lifecycle_substrate":
        status = "hold"
        stratum_mode = "paused_lifecycle_stratum"
        decision = "pause_lifecycle_stratum"
        actionability = "pause"
        queue_override_status = "hold"
    elif substrate_decision == "archive_lifecycle_substrate":
        status = "terminal"
        stratum_mode = "archived_lifecycle_stratum"
        decision = "archive_lifecycle_stratum"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif substrate_decision == "retire_lifecycle_substrate":
        status = "terminal"
        stratum_mode = "retired_lifecycle_stratum"
        decision = "retire_lifecycle_stratum"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        stratum_notes.append("fallback_pause")

    stratum_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_substrate_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_substrate_decision.changed
        or decision != "pause_lifecycle_stratum"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle stratum converts the substrate posture into "
        "the final stratum state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_stratum":
        rationale = (
            "The proactive lifecycle stratum keeps the lifecycle preserved because "
            "the line should remain available as a stable stratum for future return."
        )
    elif decision == "buffer_lifecycle_stratum":
        rationale = (
            "The proactive lifecycle stratum buffers the lifecycle because "
            "the line should preserve its stratum without immediate motion."
        )
    elif decision == "pause_lifecycle_stratum":
        rationale = (
            "The proactive lifecycle stratum pauses the lifecycle because "
            "the line should preserve stratum space without immediate continuation."
        )
    elif decision == "archive_lifecycle_stratum":
        rationale = (
            "The proactive lifecycle stratum archives the lifecycle because "
            "the line reached a clean stratum ending."
        )
    elif decision == "retire_lifecycle_stratum":
        rationale = (
            "The proactive lifecycle stratum retires the lifecycle because "
            "the line reached a terminal stratum stop condition."
        )

    return ProactiveLifecycleStratumDecision(
        status=status,
        stratum_key=stratum_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        substrate_mode=substrate_mode,
        stratum_mode=stratum_mode,
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
        selected_strategy_key=(
            lifecycle_substrate_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_substrate_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_substrate_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_substrate_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        substrate_decision=substrate_decision,
        active_sources=_compact(lifecycle_substrate_decision.active_sources, limit=8),
        stratum_notes=_compact(stratum_notes, limit=10),
        rationale=rationale,
    )


def build_proactive_lifecycle_layer_decision(
    *,
    lifecycle_stratum_decision: ProactiveLifecycleStratumDecision,
) -> ProactiveLifecycleLayerDecision:
    current_stage_label = lifecycle_stratum_decision.current_stage_label or "unknown"
    lifecycle_state = lifecycle_stratum_decision.lifecycle_state or "active"
    stratum_mode = (
        lifecycle_stratum_decision.stratum_mode or "paused_lifecycle_stratum"
    )
    stratum_decision = (
        lifecycle_stratum_decision.decision or "pause_lifecycle_stratum"
    )
    active_stage_label = lifecycle_stratum_decision.active_stage_label
    next_stage_label = lifecycle_stratum_decision.next_stage_label
    remaining_stage_count = max(
        0, int(lifecycle_stratum_decision.remaining_stage_count or 0)
    )
    line_state = lifecycle_stratum_decision.line_state or "steady"
    line_exit_mode = lifecycle_stratum_decision.line_exit_mode or "stay"
    status = lifecycle_stratum_decision.status or "hold"
    layer_mode = "paused_lifecycle_layer"
    decision = "pause_lifecycle_layer"
    actionability = "pause"
    queue_override_status = "hold"
    additional_delay_seconds = max(
        0, int(lifecycle_stratum_decision.additional_delay_seconds or 0)
    )
    primary_source = lifecycle_stratum_decision.primary_source or "stratum"
    layer_notes: list[str] = list(lifecycle_stratum_decision.stratum_notes)
    layer_notes.append(f"stratum:{stratum_mode}")
    if line_state:
        layer_notes.append(f"line:{line_state}")
    if line_exit_mode:
        layer_notes.append(f"exit:{line_exit_mode}")
    if active_stage_label:
        layer_notes.append(f"active:{active_stage_label}")

    if stratum_decision == "keep_lifecycle_stratum":
        status = "active"
        layer_mode = "preserved_lifecycle_layer"
        decision = "keep_lifecycle_layer"
        actionability = "keep"
        queue_override_status = None
    elif stratum_decision == "buffer_lifecycle_stratum":
        status = "scheduled"
        layer_mode = "buffered_lifecycle_layer"
        decision = "buffer_lifecycle_layer"
        actionability = "buffer"
        queue_override_status = "scheduled"
    elif stratum_decision == "pause_lifecycle_stratum":
        status = "hold"
        layer_mode = "paused_lifecycle_layer"
        decision = "pause_lifecycle_layer"
        actionability = "pause"
        queue_override_status = "hold"
    elif stratum_decision == "archive_lifecycle_stratum":
        status = "terminal"
        layer_mode = "archived_lifecycle_layer"
        decision = "archive_lifecycle_layer"
        actionability = "archive"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    elif stratum_decision == "retire_lifecycle_stratum":
        status = "terminal"
        layer_mode = "retired_lifecycle_layer"
        decision = "retire_lifecycle_layer"
        actionability = "retire"
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0
        queue_override_status = "terminal"
    else:
        layer_notes.append("fallback_pause")

    layer_key = (
        f"{current_stage_label}_{decision}_"
        f"{lifecycle_stratum_decision.selected_strategy_key or 'none'}"
    )
    changed = bool(
        lifecycle_stratum_decision.changed
        or decision != "pause_lifecycle_layer"
        or active_stage_label != current_stage_label
    )
    rationale = (
        "The proactive lifecycle layer converts the stratum posture into "
        "the final layer state that future proactive scheduling should honor."
    )
    if decision == "keep_lifecycle_layer":
        rationale = (
            "The proactive lifecycle layer keeps the lifecycle preserved because "
            "the line should remain available as a stable layer for future return."
        )
    elif decision == "buffer_lifecycle_layer":
        rationale = (
            "The proactive lifecycle layer buffers the lifecycle because "
            "the line should preserve its layer without immediate motion."
        )
    elif decision == "pause_lifecycle_layer":
        rationale = (
            "The proactive lifecycle layer pauses the lifecycle because "
            "the line should preserve layer space without immediate continuation."
        )
    elif decision == "archive_lifecycle_layer":
        rationale = (
            "The proactive lifecycle layer archives the lifecycle because "
            "the line reached a clean layer ending."
        )
    elif decision == "retire_lifecycle_layer":
        rationale = (
            "The proactive lifecycle layer retires the lifecycle because "
            "the line reached a terminal layer stop condition."
        )

    return ProactiveLifecycleLayerDecision(
        status=status,
        layer_key=layer_key,
        current_stage_label=current_stage_label,
        lifecycle_state=lifecycle_state,
        stratum_mode=stratum_mode,
        layer_mode=layer_mode,
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
        selected_strategy_key=(
            lifecycle_stratum_decision.selected_strategy_key or "none"
        ),
        selected_pressure_mode=(
            lifecycle_stratum_decision.selected_pressure_mode or "none"
        ),
        selected_autonomy_signal=(
            lifecycle_stratum_decision.selected_autonomy_signal or "none"
        ),
        selected_delivery_mode=(
            lifecycle_stratum_decision.selected_delivery_mode or "none"
        ),
        primary_source=primary_source,
        stratum_decision=stratum_decision,
        active_sources=_compact(lifecycle_stratum_decision.active_sources, limit=8),
        layer_notes=_compact(layer_notes, limit=10),
        rationale=rationale,
    )


