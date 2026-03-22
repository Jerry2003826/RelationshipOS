"""Proactive state machines: stage and line state/transition/machine decisions."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ProactiveAggregateControllerDecision,
    ProactiveCadencePlan,
    ProactiveDispatchEnvelopeDecision,
    ProactiveDispatchGateDecision,
    ProactiveLineControllerDecision,
    ProactiveLineMachineDecision,
    ProactiveLineStateDecision,
    ProactiveLineTransitionDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageMachineDecision,
    ProactiveStageStateDecision,
    ProactiveStageTransitionDecision,
)


def build_proactive_stage_state_decision(
    *,
    stage_label: str,
    stage_index: int,
    stage_count: int,
    queue_status: str,
    schedule_reason: str | None = None,
    progression_action: str | None = None,
    progression_advanced: bool = False,
    line_state: str | None = None,
    current_stage_delivery_mode: str | None = None,
    current_stage_autonomy_mode: str | None = None,
    current_reengagement_delivery_mode: str | None = None,
    selected_strategy_key: str | None = None,
    selected_pressure_mode: str | None = None,
    selected_autonomy_signal: str | None = None,
    dispatch_envelope_key: str | None = None,
    dispatch_envelope_decision: str | None = None,
    dispatch_gate_decision: str | None = None,
    aggregate_controller_decision: str | None = None,
    orchestration_controller_decision: str | None = None,
    stage_controller_decision: str | None = None,
    line_controller_decision: str | None = None,
) -> ProactiveStageStateDecision:
    stage_label = stage_label or "unknown"
    queue_status = queue_status or "hold"
    stage_index = max(1, int(stage_index or 1))
    stage_count = max(stage_index, int(stage_count or stage_index or 1))
    line_state = line_state or "steady"
    progression_action = progression_action or "none"

    selected_strategy_key = selected_strategy_key or "none"
    selected_stage_delivery_mode = current_stage_delivery_mode or "single_message"
    selected_reengagement_delivery_mode = (
        current_reengagement_delivery_mode or selected_stage_delivery_mode
    )
    selected_pressure_mode = selected_pressure_mode or "none"
    selected_autonomy_signal = selected_autonomy_signal or current_stage_autonomy_mode or "none"

    primary_source = "cadence"
    controller_decision = None
    if dispatch_gate_decision in {"hold", "defer"}:
        primary_source = "gate"
        controller_decision = dispatch_gate_decision
    elif orchestration_controller_decision not in {None, "follow_local_controllers"}:
        primary_source = "orchestration_controller"
        controller_decision = orchestration_controller_decision
    elif aggregate_controller_decision not in {None, "follow_local_controllers"}:
        primary_source = "aggregate_controller"
        controller_decision = aggregate_controller_decision
    elif stage_controller_decision not in {None, "follow_local_controllers"}:
        primary_source = "stage_controller"
        controller_decision = stage_controller_decision
    elif line_controller_decision not in {None, "follow_local_controllers"}:
        primary_source = "line_controller"
        controller_decision = line_controller_decision
    elif dispatch_envelope_decision in {"dispatch_shaped", "defer_dispatch", "hold_dispatch"}:
        primary_source = "dispatch_envelope"
        controller_decision = dispatch_envelope_decision
    elif progression_advanced:
        primary_source = "progression"
        controller_decision = progression_action

    if queue_status == "hold" or dispatch_gate_decision == "hold":
        status = "hold"
        state_mode = "held"
    elif dispatch_gate_decision == "defer" or dispatch_envelope_decision == "defer_dispatch":
        status = "scheduled"
        state_mode = "deferred_dispatch"
    elif queue_status == "scheduled":
        status = "scheduled"
        if line_state == "close_ready" or progression_action == "close_line":
            state_mode = "scheduled_close_loop"
        elif line_state == "softened":
            state_mode = "scheduled_softened"
        else:
            state_mode = "scheduled_wait"
    elif queue_status == "waiting":
        status = "active"
        state_mode = "waiting_softened" if line_state == "softened" else "waiting_turn"
    elif queue_status == "overdue":
        status = "active"
        if progression_advanced:
            state_mode = "overdue_progressed"
        elif dispatch_envelope_decision == "dispatch_shaped":
            state_mode = "overdue_shaped"
        else:
            state_mode = "overdue_ready"
    else:
        status = "active"
        if dispatch_envelope_decision == "dispatch_shaped":
            state_mode = "dispatch_shaped"
        elif line_state == "close_ready" or progression_action == "close_line":
            state_mode = "dispatch_close_ready"
        elif line_state == "softened":
            state_mode = "dispatch_softened"
        else:
            state_mode = "dispatch_ready"

    changed = bool(
        primary_source != "cadence"
        or progression_advanced
        or dispatch_envelope_decision in {"dispatch_shaped", "defer_dispatch", "hold_dispatch"}
        or line_state != "steady"
    )
    state_key = f"{stage_label}_{state_mode}_{selected_strategy_key}"

    state_notes: list[str] = [f"queue:{queue_status}"]
    if schedule_reason:
        state_notes.append(f"schedule:{schedule_reason}")
    if line_state and line_state != "steady":
        state_notes.append(f"line:{line_state}")
    if progression_action and progression_action != "none":
        state_notes.append(f"progression:{progression_action}")
    if primary_source:
        state_notes.append(f"source:{primary_source}")

    rationale = (
        "The current proactive stage is following its expected cadence state without "
        "additional controller or gate shaping."
    )
    if state_mode == "deferred_dispatch":
        rationale = (
            "The current proactive stage has a shaped envelope, but the dispatch gate "
            "is still leaving more space before it can be sent."
        )
    elif state_mode in {"scheduled_softened", "dispatch_softened", "waiting_softened"}:
        rationale = (
            "The current proactive stage is softened by the controller stack, so it "
            "keeps a lower-pressure posture even before dispatch."
        )
    elif state_mode in {"dispatch_shaped", "overdue_shaped"}:
        rationale = (
            "The current proactive stage is ready to move with a shaped low-pressure "
            "envelope instead of its original local defaults."
        )
    elif state_mode in {"scheduled_close_loop", "dispatch_close_ready"}:
        rationale = (
            "The current proactive stage is already in a close-loop posture, so the "
            "remaining line is being wound down carefully."
        )
    elif state_mode == "held":
        rationale = (
            "The current proactive stage should stay on hold because the line is not "
            "ready to move at all."
        )

    return ProactiveStageStateDecision(
        status=status,
        state_key=state_key,
        stage_label=stage_label,
        stage_index=stage_index,
        stage_count=stage_count,
        queue_status=queue_status,
        state_mode=state_mode,
        changed=changed,
        selected_strategy_key=selected_strategy_key,
        selected_stage_delivery_mode=selected_stage_delivery_mode,
        selected_reengagement_delivery_mode=selected_reengagement_delivery_mode,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        line_state=line_state,
        progression_action=progression_action,
        progression_advanced=progression_advanced,
        dispatch_envelope_key=dispatch_envelope_key,
        dispatch_envelope_decision=dispatch_envelope_decision,
        primary_source=primary_source,
        controller_decision=controller_decision,
        state_notes=_compact(state_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_stage_transition_decision(
    *,
    stage_state_decision: ProactiveStageStateDecision,
    next_stage_label: str | None = None,
    dispatch_gate_decision: ProactiveDispatchGateDecision | None = None,
    dispatch_envelope_decision: ProactiveDispatchEnvelopeDecision | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    stage_controller_decision: ProactiveStageControllerDecision | None = None,
    line_controller_decision: ProactiveLineControllerDecision | None = None,
) -> ProactiveStageTransitionDecision:
    stage_label = stage_state_decision.stage_label or "unknown"
    stage_index = max(1, int(stage_state_decision.stage_index or 1))
    stage_count = max(stage_index, int(stage_state_decision.stage_count or stage_index))
    current_state_key = stage_state_decision.state_key or f"{stage_label}_unknown"
    current_state_mode = stage_state_decision.state_mode or "held"
    queue_status = stage_state_decision.queue_status or "hold"
    line_state = stage_state_decision.line_state or "steady"
    progression_action = stage_state_decision.progression_action or "none"
    progression_advanced = bool(stage_state_decision.progression_advanced)

    gate_decision = (
        dispatch_gate_decision.decision
        if dispatch_gate_decision is not None
        else stage_state_decision.controller_decision
        if stage_state_decision.primary_source == "gate"
        else None
    )
    envelope_decision = (
        dispatch_envelope_decision.decision
        if dispatch_envelope_decision is not None
        else stage_state_decision.dispatch_envelope_decision
    )
    primary_source = stage_state_decision.primary_source or "cadence"
    controller_decision = stage_state_decision.controller_decision
    if controller_decision in {None, ""}:
        for decision in (
            orchestration_controller_decision.decision
            if orchestration_controller_decision is not None
            else None,
            aggregate_controller_decision.decision
            if aggregate_controller_decision is not None
            else None,
            stage_controller_decision.decision if stage_controller_decision is not None else None,
            line_controller_decision.decision if line_controller_decision is not None else None,
            envelope_decision,
            gate_decision,
        ):
            if decision and decision not in {"follow_local_controllers", "dispatch"}:
                controller_decision = decision
                break

    transition_mode = "hold_stage"
    status = "hold"
    next_queue_status_hint = "hold"
    stage_exit_mode = "stay"
    next_stage_index: int | None = None

    is_close_loop_stage = bool(
        line_state == "close_ready"
        or progression_action == "close_line"
        or stage_label == "final_soft_close"
    )
    if queue_status == "hold" or gate_decision == "hold":
        transition_mode = "hold_stage"
        status = "hold"
        next_queue_status_hint = "hold"
    elif queue_status == "scheduled" or gate_decision == "defer":
        status = "scheduled"
        next_queue_status_hint = "scheduled"
        if is_close_loop_stage:
            transition_mode = "reschedule_close_loop"
            stage_exit_mode = "close_loop"
        else:
            transition_mode = "reschedule_stage"
    elif queue_status == "waiting":
        status = "waiting"
        next_queue_status_hint = "waiting"
        if line_state == "softened":
            transition_mode = "wait_softened_stage"
        else:
            transition_mode = "wait_stage"
    else:
        status = "active"
        next_queue_status_hint = "dispatched"
        if is_close_loop_stage:
            transition_mode = "dispatch_close_loop"
            if stage_label == "final_soft_close" or progression_action == "close_line":
                stage_exit_mode = "retire_line"
                next_queue_status_hint = "terminal"
                next_stage_label = None
            else:
                stage_exit_mode = "close_loop"
        elif envelope_decision == "dispatch_shaped" or line_state == "softened":
            transition_mode = "dispatch_softened_stage"
            stage_exit_mode = "advance_line"
        else:
            transition_mode = "dispatch_stage"
            stage_exit_mode = "advance_line"

        if stage_exit_mode == "advance_line":
            if next_stage_label:
                next_stage_index = min(stage_count, stage_index + 1)
            elif stage_index < stage_count:
                next_stage_index = stage_index + 1

    changed = bool(
        stage_state_decision.changed
        or transition_mode not in {"hold_stage", "wait_stage", "dispatch_stage"}
        or stage_exit_mode != "stay"
    )
    selected_strategy_key = stage_state_decision.selected_strategy_key or "none"
    transition_key = f"{stage_label}_{transition_mode}_{selected_strategy_key}"

    transition_notes: list[str] = [
        f"state:{current_state_mode}",
        f"queue:{queue_status}",
        f"source:{primary_source}",
    ]
    if line_state != "steady":
        transition_notes.append(f"line:{line_state}")
    if progression_action != "none":
        transition_notes.append(f"progression:{progression_action}")
    if controller_decision:
        transition_notes.append(f"controller:{controller_decision}")
    if next_stage_label:
        transition_notes.append(f"next:{next_stage_label}")
    elif next_stage_index is not None:
        transition_notes.append(f"next_index:{next_stage_index}")

    rationale = (
        "The current proactive stage is staying on its default lifecycle path "
        "without needing a controller-led transition."
    )
    if transition_mode == "hold_stage":
        rationale = (
            "The current proactive stage should remain on hold because the proactive "
            "line is not ready to move at all."
        )
    elif transition_mode in {"reschedule_stage", "reschedule_close_loop"}:
        rationale = (
            "The current proactive stage should be rescheduled so the line keeps its "
            "low-pressure timing instead of firing on the first due moment."
        )
    elif transition_mode == "wait_softened_stage":
        rationale = (
            "The current proactive stage is still waiting, but the controller stack "
            "has already softened its posture before dispatch."
        )
    elif transition_mode == "dispatch_softened_stage":
        rationale = (
            "The current proactive stage can dispatch now, but it should do so with "
            "a softened low-pressure envelope."
        )
    elif transition_mode == "dispatch_close_loop":
        rationale = (
            "The current proactive stage can dispatch now, and the line is already in "
            "a close-loop posture so the remaining proactive path should wind down."
        )

    return ProactiveStageTransitionDecision(
        status=status,
        transition_key=transition_key,
        stage_label=stage_label,
        stage_index=stage_index,
        stage_count=stage_count,
        current_state_key=current_state_key,
        current_state_mode=current_state_mode,
        transition_mode=transition_mode,
        changed=changed,
        next_stage_label=next_stage_label,
        next_stage_index=next_stage_index,
        next_queue_status_hint=next_queue_status_hint,
        stage_exit_mode=stage_exit_mode,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=stage_state_decision.selected_pressure_mode,
        selected_autonomy_signal=stage_state_decision.selected_autonomy_signal,
        line_state=line_state,
        progression_action=progression_action,
        progression_advanced=progression_advanced,
        dispatch_gate_decision=gate_decision,
        dispatch_envelope_decision=envelope_decision,
        primary_source=primary_source,
        controller_decision=controller_decision,
        transition_notes=_compact(transition_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_stage_machine_decision(
    *,
    stage_state_decision: ProactiveStageStateDecision,
    stage_transition_decision: ProactiveStageTransitionDecision,
    dispatch_envelope_decision: ProactiveDispatchEnvelopeDecision | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    stage_controller_decision: ProactiveStageControllerDecision | None = None,
    line_controller_decision: ProactiveLineControllerDecision | None = None,
) -> ProactiveStageMachineDecision:
    stage_label = (
        stage_transition_decision.stage_label or stage_state_decision.stage_label or "unknown"
    )
    stage_index = max(1, int(stage_transition_decision.stage_index or 1))
    stage_count = max(stage_index, int(stage_transition_decision.stage_count or stage_index))
    current_state_key = (
        stage_state_decision.state_key
        or stage_transition_decision.current_state_key
        or f"{stage_label}_unknown"
    )
    current_state_mode = (
        stage_state_decision.state_mode or stage_transition_decision.current_state_mode or "held"
    )
    transition_key = stage_transition_decision.transition_key or f"{stage_label}_hold_stage"
    transition_mode = stage_transition_decision.transition_mode or "hold_stage"
    queue_status = stage_state_decision.queue_status or "hold"
    next_stage_label = stage_transition_decision.next_stage_label
    next_stage_index = stage_transition_decision.next_stage_index
    next_queue_status_hint = stage_transition_decision.next_queue_status_hint or "hold"
    stage_exit_mode = stage_transition_decision.stage_exit_mode or "stay"
    selected_strategy_key = (
        stage_transition_decision.selected_strategy_key
        or stage_state_decision.selected_strategy_key
        or "none"
    )
    selected_pressure_mode = (
        stage_transition_decision.selected_pressure_mode
        or stage_state_decision.selected_pressure_mode
        or "none"
    )
    selected_autonomy_signal = (
        stage_transition_decision.selected_autonomy_signal
        or stage_state_decision.selected_autonomy_signal
        or "none"
    )
    selected_delivery_mode = (
        dispatch_envelope_decision.selected_reengagement_delivery_mode
        if dispatch_envelope_decision is not None
        else stage_state_decision.selected_reengagement_delivery_mode
        or stage_state_decision.selected_stage_delivery_mode
        or "none"
    )
    line_state = stage_transition_decision.line_state or stage_state_decision.line_state
    primary_source = (
        stage_transition_decision.primary_source or stage_state_decision.primary_source or "cadence"
    )
    controller_decision = (
        stage_transition_decision.controller_decision or stage_state_decision.controller_decision
    )
    if controller_decision in {None, ""}:
        for decision in (
            orchestration_controller_decision.decision
            if orchestration_controller_decision is not None
            else None,
            aggregate_controller_decision.decision
            if aggregate_controller_decision is not None
            else None,
            stage_controller_decision.decision if stage_controller_decision is not None else None,
            line_controller_decision.decision if line_controller_decision is not None else None,
        ):
            if decision and decision not in {"follow_local_controllers", "dispatch"}:
                controller_decision = decision
                break

    machine_mode = "held"
    lifecycle_mode = "dormant"
    actionability = "hold"
    status = "hold"
    machine_notes: list[str] = []

    if stage_exit_mode == "retire_line" or next_queue_status_hint == "terminal":
        machine_mode = "retiring_line"
        lifecycle_mode = "terminal"
        actionability = "retire"
        status = "terminal"
        machine_notes.append("terminal_stage_exit")
    elif transition_mode.startswith("reschedule_") or queue_status == "scheduled":
        status = "scheduled"
        actionability = "reschedule"
        if stage_exit_mode == "close_loop" or "close_loop" in transition_mode:
            machine_mode = "scheduled_close_loop"
            lifecycle_mode = "buffered_close_loop"
            machine_notes.append("close_loop_buffer")
        else:
            machine_mode = "scheduled_stage"
            lifecycle_mode = "buffered"
    elif transition_mode.startswith("wait_") or queue_status == "waiting":
        status = "waiting"
        machine_mode = "waiting_stage"
        lifecycle_mode = "waiting"
        actionability = "wait"
    elif transition_mode == "dispatch_close_loop":
        status = "active"
        machine_mode = "dispatching_close_loop"
        lifecycle_mode = "winding_down"
        actionability = "dispatch"
        machine_notes.append("close_loop_dispatch")
    elif transition_mode in {"dispatch_stage", "dispatch_softened_stage"}:
        status = "active"
        actionability = "dispatch"
        machine_mode = (
            "dispatching_softened_stage"
            if transition_mode == "dispatch_softened_stage"
            else "dispatching_stage"
        )
        lifecycle_mode = "dispatching"

    if line_state == "softened":
        machine_notes.append("line_softened")
    if current_state_mode.endswith("close_loop"):
        machine_notes.append("state_close_loop")
    if controller_decision and controller_decision not in {
        "dispatch",
        "follow_local_controllers",
    }:
        machine_notes.append(f"controller:{controller_decision}")
    if primary_source not in {"cadence", "dispatch_envelope"}:
        machine_notes.append(f"source:{primary_source}")

    machine_key = f"{stage_label}_{machine_mode}"
    changed = bool(
        stage_state_decision.changed
        or stage_transition_decision.changed
        or machine_mode not in {"held", "dispatching_stage"}
        or actionability != "hold"
    )
    rationale = (
        "The proactive stage machine now has a unified lifecycle view for this stage, "
        "combining the current state, the latest transition, and the controller stack "
        "into one dispatch posture."
    )
    if lifecycle_mode == "terminal":
        rationale = (
            "The proactive stage machine has moved into a terminal posture, so this "
            "line should retire instead of continuing to push contact."
        )
    elif lifecycle_mode in {"buffered", "buffered_close_loop", "waiting"}:
        rationale = (
            "The proactive stage machine is intentionally buffered, so this stage keeps "
            "space open before any further proactive movement."
        )
    elif lifecycle_mode == "winding_down":
        rationale = (
            "The proactive stage machine is dispatching a close-loop stage, so the "
            "line is being wound down carefully."
        )

    return ProactiveStageMachineDecision(
        status=status,
        machine_key=machine_key,
        stage_label=stage_label,
        stage_index=stage_index,
        stage_count=stage_count,
        current_state_key=current_state_key,
        current_state_mode=current_state_mode,
        transition_key=transition_key,
        transition_mode=transition_mode,
        queue_status=queue_status,
        machine_mode=machine_mode,
        lifecycle_mode=lifecycle_mode,
        actionability=actionability,
        changed=changed,
        next_stage_label=next_stage_label,
        next_stage_index=next_stage_index,
        next_queue_status_hint=next_queue_status_hint,
        stage_exit_mode=stage_exit_mode,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        line_state=line_state,
        primary_source=primary_source,
        controller_decision=controller_decision,
        machine_notes=_compact(machine_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_line_state_decision(
    *,
    proactive_cadence_plan: ProactiveCadencePlan,
    stage_machine_decision: ProactiveStageMachineDecision,
    line_controller_decision: ProactiveLineControllerDecision,
) -> ProactiveLineStateDecision:
    current_stage_label = stage_machine_decision.stage_label or "unknown"
    current_stage_index = max(1, int(stage_machine_decision.stage_index or 1))
    stage_count = max(
        current_stage_index,
        int(
            proactive_cadence_plan.close_after_stage_index
            or stage_machine_decision.stage_count
            or len(proactive_cadence_plan.stage_labels)
            or current_stage_index
        ),
    )
    close_loop_stage = None
    if proactive_cadence_plan.stage_labels:
        close_loop_index = min(
            stage_count - 1,
            len(proactive_cadence_plan.stage_labels) - 1,
        )
        close_loop_stage = proactive_cadence_plan.stage_labels[close_loop_index]
    next_stage_label = stage_machine_decision.next_stage_label
    remaining_stage_count = max(0, stage_count - current_stage_index + 1)
    line_state = line_controller_decision.line_state or "steady"
    lifecycle_mode = "active"
    actionability = "continue"
    status = "active"
    line_notes: list[str] = []

    if line_state in {"hold", "line_complete"}:
        status = "hold" if line_state == "hold" else "terminal"
        lifecycle_mode = "dormant" if line_state == "hold" else "terminal"
        actionability = "hold" if line_state == "hold" else "retire_line"
        if line_state == "line_complete":
            remaining_stage_count = 0
            next_stage_label = None
            line_notes.append("line_complete")
    elif stage_machine_decision.lifecycle_mode == "terminal":
        status = "terminal"
        lifecycle_mode = "terminal"
        actionability = "retire_line"
        line_state = "retiring"
        remaining_stage_count = 0
        next_stage_label = None
        line_notes.append("terminal_machine")
    elif line_state == "close_ready" or stage_machine_decision.lifecycle_mode == "winding_down":
        status = "active"
        lifecycle_mode = "winding_down"
        actionability = "close_loop"
        line_notes.append("close_loop_line")
    elif line_state == "softened":
        is_buffered = stage_machine_decision.actionability in {
            "reschedule",
            "wait",
        }
        status = "scheduled" if is_buffered else "active"
        lifecycle_mode = "buffered" if is_buffered else "active_softened"
        actionability = "soften"
        line_notes.append("softened_line")
    elif stage_machine_decision.actionability == "hold":
        status = "hold"
        lifecycle_mode = "dormant"
        actionability = "hold"
    elif stage_machine_decision.actionability in {"reschedule", "wait"}:
        status = "scheduled"
        lifecycle_mode = "buffered"
        actionability = "buffer"

    if next_stage_label:
        line_notes.append(f"next:{next_stage_label}")
    if line_controller_decision.decision not in {
        "hold",
        "follow_remaining_line",
        "close_line",
    }:
        line_notes.append(f"controller:{line_controller_decision.decision}")
    if stage_machine_decision.current_state_mode.endswith("close_loop"):
        line_notes.append("stage_close_loop")

    line_key = f"{current_stage_label}_{line_state}_{lifecycle_mode}"
    changed = bool(
        stage_machine_decision.changed
        or line_controller_decision.changed
        or line_state not in {"steady"}
        or lifecycle_mode not in {"active"}
    )
    rationale = (
        "The proactive line now has a unified lifecycle view that combines the "
        "current stage machine with the line controller posture."
    )
    if lifecycle_mode == "terminal":
        rationale = (
            "The proactive line is effectively complete or retiring, so future "
            "contact should stop instead of continuing through another stage."
        )
    elif lifecycle_mode == "winding_down":
        rationale = (
            "The proactive line is already winding down, so any remaining touch "
            "should behave like a close-loop instead of a fresh nudge."
        )
    elif lifecycle_mode in {"buffered", "active_softened"}:
        rationale = (
            "The proactive line is softened, so the remaining stages should keep "
            "extra user space instead of following the default cadence."
        )

    return ProactiveLineStateDecision(
        status=status,
        line_key=line_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        remaining_stage_count=remaining_stage_count,
        line_state=line_state,
        lifecycle_mode=lifecycle_mode,
        actionability=actionability,
        changed=changed,
        current_stage_machine_mode=stage_machine_decision.machine_mode,
        current_stage_transition_mode=stage_machine_decision.transition_mode,
        next_stage_label=next_stage_label,
        close_loop_stage=close_loop_stage,
        selected_strategy_key=stage_machine_decision.selected_strategy_key,
        selected_pressure_mode=stage_machine_decision.selected_pressure_mode,
        selected_autonomy_signal=stage_machine_decision.selected_autonomy_signal,
        selected_delivery_mode=stage_machine_decision.selected_delivery_mode,
        primary_source=stage_machine_decision.primary_source,
        controller_decision=line_controller_decision.decision,
        line_notes=_compact(line_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_line_transition_decision(
    *,
    line_state_decision: ProactiveLineStateDecision,
    stage_transition_decision: ProactiveStageTransitionDecision,
) -> ProactiveLineTransitionDecision:
    current_line_key = line_state_decision.line_key or "unknown_line"
    current_stage_label = line_state_decision.current_stage_label or "unknown"
    current_stage_index = max(1, int(line_state_decision.current_stage_index or 1))
    stage_count = max(
        current_stage_index,
        int(line_state_decision.stage_count or current_stage_index),
    )
    line_state = line_state_decision.line_state or "steady"
    lifecycle_mode = line_state_decision.lifecycle_mode or "active"
    next_stage_label = (
        line_state_decision.next_stage_label or stage_transition_decision.next_stage_label
    )
    next_stage_index = stage_transition_decision.next_stage_index
    if next_stage_index is None and next_stage_label and current_stage_index < stage_count:
        next_stage_index = current_stage_index + 1

    status = line_state_decision.status or "active"
    transition_mode = "continue_line"
    next_line_state = line_state
    next_lifecycle_mode = lifecycle_mode
    line_exit_mode = "stay"
    transition_notes: list[str] = [
        f"line:{line_state}",
        f"lifecycle:{lifecycle_mode}",
        f"stage_transition:{stage_transition_decision.transition_mode}",
    ]

    if (
        line_state_decision.actionability == "retire_line"
        or lifecycle_mode == "terminal"
        or stage_transition_decision.stage_exit_mode == "retire_line"
    ):
        status = "terminal"
        transition_mode = "retire_line"
        next_line_state = "retiring"
        next_lifecycle_mode = "terminal"
        line_exit_mode = "retire"
        next_stage_label = None
        next_stage_index = None
        transition_notes.append("retire_line")
    elif (
        line_state_decision.actionability == "close_loop"
        or lifecycle_mode == "winding_down"
        or stage_transition_decision.stage_exit_mode == "close_loop"
    ):
        transition_mode = "close_loop_line"
        next_line_state = "close_ready"
        next_lifecycle_mode = "winding_down"
        line_exit_mode = "close_loop"
        transition_notes.append("close_loop_line")
    elif line_state_decision.actionability == "hold":
        status = "hold"
        transition_mode = "hold_line"
        next_line_state = "hold"
        next_lifecycle_mode = "dormant"
        line_exit_mode = "stay"
        transition_notes.append("hold_line")
    elif (
        line_state_decision.actionability == "buffer"
        or lifecycle_mode == "buffered"
        or stage_transition_decision.transition_mode.startswith("reschedule_")
        or stage_transition_decision.transition_mode.startswith("wait_")
    ):
        status = "scheduled"
        transition_mode = "buffer_line"
        next_line_state = "softened"
        next_lifecycle_mode = "buffered"
        line_exit_mode = "buffer"
        transition_notes.append("buffer_line")
    elif line_state_decision.actionability == "soften" or lifecycle_mode == "active_softened":
        transition_mode = "soften_line"
        next_line_state = "softened"
        next_lifecycle_mode = "active_softened"
        line_exit_mode = "soften"
        transition_notes.append("soften_line")
    elif next_stage_label:
        transition_mode = "advance_line"
        next_lifecycle_mode = "active"
        line_exit_mode = "advance"
        transition_notes.append(f"next:{next_stage_label}")

    if line_state_decision.controller_decision not in {None, "", "follow_remaining_line"}:
        transition_notes.append(f"controller:{line_state_decision.controller_decision}")

    transition_key = f"{current_stage_label}_{transition_mode}_{next_line_state}"
    changed = bool(
        line_state_decision.changed
        or stage_transition_decision.changed
        or transition_mode not in {"continue_line", "hold_line"}
        or next_line_state != line_state
        or next_lifecycle_mode != lifecycle_mode
    )
    rationale = (
        "The proactive line now has an explicit transition layer that describes "
        "how the remaining line should move after the current stage outcome."
    )
    if transition_mode == "retire_line":
        rationale = (
            "The proactive line is effectively done, so it should retire instead "
            "of keeping another proactive stage alive."
        )
    elif transition_mode == "close_loop_line":
        rationale = (
            "The proactive line is already winding down, so the remaining movement "
            "should stay in a close-loop posture instead of reopening momentum."
        )
    elif transition_mode in {"buffer_line", "soften_line"}:
        rationale = (
            "The proactive line should keep a softened low-pressure posture before "
            "it tries to move through any remaining stage."
        )

    return ProactiveLineTransitionDecision(
        status=status,
        transition_key=transition_key,
        current_line_key=current_line_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        line_state=line_state,
        lifecycle_mode=lifecycle_mode,
        transition_mode=transition_mode,
        changed=changed,
        next_stage_label=next_stage_label,
        next_stage_index=next_stage_index,
        next_line_state=next_line_state,
        next_lifecycle_mode=next_lifecycle_mode,
        line_exit_mode=line_exit_mode,
        selected_strategy_key=line_state_decision.selected_strategy_key,
        selected_pressure_mode=line_state_decision.selected_pressure_mode,
        selected_autonomy_signal=line_state_decision.selected_autonomy_signal,
        selected_delivery_mode=line_state_decision.selected_delivery_mode,
        primary_source=line_state_decision.primary_source,
        controller_decision=line_state_decision.controller_decision,
        transition_notes=_compact(transition_notes, limit=6),
        rationale=rationale,
    )


def build_proactive_line_machine_decision(
    *,
    line_state_decision: ProactiveLineStateDecision,
    line_transition_decision: ProactiveLineTransitionDecision,
) -> ProactiveLineMachineDecision:
    current_line_key = line_transition_decision.current_line_key or "unknown_line"
    current_stage_label = line_transition_decision.current_stage_label or "unknown"
    current_stage_index = max(1, int(line_transition_decision.current_stage_index or 1))
    stage_count = max(
        current_stage_index,
        int(line_transition_decision.stage_count or current_stage_index),
    )
    transition_key = line_transition_decision.transition_key or "line_transition"
    transition_mode = line_transition_decision.transition_mode or "continue_line"
    line_state = line_transition_decision.line_state or line_state_decision.line_state
    lifecycle_mode = line_transition_decision.lifecycle_mode or line_state_decision.lifecycle_mode

    status = line_transition_decision.status or "active"
    machine_mode = "active_line"
    actionability = "continue"
    machine_lifecycle_mode = lifecycle_mode or "active"
    machine_notes: list[str] = [
        f"line:{line_state}",
        f"transition:{transition_mode}",
    ]

    if (
        line_transition_decision.line_exit_mode == "retire"
        or line_transition_decision.next_lifecycle_mode == "terminal"
    ):
        status = "terminal"
        machine_mode = "retiring_line"
        actionability = "retire"
        machine_lifecycle_mode = "terminal"
        machine_notes.append("retire_line")
    elif (
        line_transition_decision.line_exit_mode == "close_loop"
        or line_transition_decision.next_lifecycle_mode == "winding_down"
    ):
        machine_mode = "winding_down_line"
        actionability = "close_loop"
        machine_lifecycle_mode = "winding_down"
        machine_notes.append("close_loop_line")
    elif (
        line_transition_decision.line_exit_mode == "buffer"
        or line_transition_decision.next_lifecycle_mode == "buffered"
    ):
        status = "scheduled"
        machine_mode = "buffered_line"
        actionability = "buffer"
        machine_lifecycle_mode = "buffered"
        machine_notes.append("buffer_line")
    elif (
        line_transition_decision.line_exit_mode == "soften"
        or line_transition_decision.next_lifecycle_mode == "active_softened"
    ):
        machine_mode = "softened_line"
        actionability = "soften"
        machine_lifecycle_mode = "active_softened"
        machine_notes.append("soften_line")
    elif line_transition_decision.line_exit_mode == "stay" and status == "hold":
        machine_mode = "dormant_line"
        actionability = "hold"
        machine_lifecycle_mode = "dormant"
        machine_notes.append("hold_line")
    elif line_transition_decision.line_exit_mode == "advance":
        machine_mode = "advancing_line"
        actionability = "advance"
        machine_lifecycle_mode = "active"
        if line_transition_decision.next_stage_label:
            machine_notes.append(f"next:{line_transition_decision.next_stage_label}")

    if line_transition_decision.controller_decision not in {
        None,
        "",
        "follow_remaining_line",
    }:
        machine_notes.append(f"controller:{line_transition_decision.controller_decision}")
    if line_transition_decision.next_line_state not in {None, "", line_state}:
        machine_notes.append(f"next_line:{line_transition_decision.next_line_state}")

    machine_key = f"{current_stage_label}_{machine_mode}"
    changed = bool(
        line_state_decision.changed
        or line_transition_decision.changed
        or machine_mode not in {"active_line", "dormant_line"}
        or actionability != "continue"
    )
    rationale = (
        "The proactive line machine now has a unified lifecycle view that combines "
        "the current line state with its next transition."
    )
    if machine_lifecycle_mode == "terminal":
        rationale = (
            "The proactive line has reached a terminal lifecycle, so no further "
            "proactive movement should remain active."
        )
    elif machine_lifecycle_mode == "winding_down":
        rationale = (
            "The proactive line is winding down, so remaining movement should stay "
            "in a close-loop posture rather than reopen momentum."
        )
    elif machine_lifecycle_mode in {"buffered", "active_softened"}:
        rationale = (
            "The proactive line remains softened, so the line machine should keep "
            "extra user space before any further dispatch."
        )

    return ProactiveLineMachineDecision(
        status=status,
        machine_key=machine_key,
        current_line_key=current_line_key,
        current_stage_label=current_stage_label,
        current_stage_index=current_stage_index,
        stage_count=stage_count,
        transition_key=transition_key,
        transition_mode=transition_mode,
        line_state=line_state,
        lifecycle_mode=machine_lifecycle_mode,
        machine_mode=machine_mode,
        actionability=actionability,
        changed=changed,
        next_stage_label=line_transition_decision.next_stage_label,
        next_stage_index=line_transition_decision.next_stage_index,
        next_line_state=line_transition_decision.next_line_state,
        next_lifecycle_mode=line_transition_decision.next_lifecycle_mode,
        line_exit_mode=line_transition_decision.line_exit_mode,
        selected_strategy_key=line_transition_decision.selected_strategy_key,
        selected_pressure_mode=line_transition_decision.selected_pressure_mode,
        selected_autonomy_signal=line_transition_decision.selected_autonomy_signal,
        selected_delivery_mode=line_transition_decision.selected_delivery_mode,
        primary_source=line_transition_decision.primary_source,
        controller_decision=line_transition_decision.controller_decision,
        machine_notes=_compact(machine_notes, limit=6),
        rationale=rationale,
    )
