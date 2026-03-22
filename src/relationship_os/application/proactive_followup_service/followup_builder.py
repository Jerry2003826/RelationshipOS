from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from relationship_os.application.analyzers import build_proactive_stage_state_decision
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    SESSION_STARTED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import StoredEvent

if TYPE_CHECKING:
    from relationship_os.application.stream_service import StreamService

_QUEUE_PRIORITY = {
    "overdue": 0,
    "due": 1,
    "scheduled": 2,
    "waiting": 3,
    "hold": 4,
}


def _parse_datetime(value: object | None) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def build_followup_item(
    *,
    stream_service: StreamService,
    session_id: str,
    reference_time: datetime,
) -> dict[str, Any] | None:
    """Build a single followup item for a session.

    Extracted from ProactiveFollowupService._build_followup_item to keep
    the service class thin while preserving all original logic.
    """
    projection, events = await asyncio.gather(
        stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
        ),
        stream_service.read_stream(stream_id=session_id),
    )
    state = dict(projection["state"])
    session = dict(state.get("session") or {})
    if not session.get("started"):
        return None
    session_source = str((session.get("metadata") or {}).get("source") or "session")
    if session_source == "scenario_evaluation":
        return None
    archive_status = dict(state.get("archive_status") or {})
    if archive_status.get("archived"):
        return None

    directive = dict(state.get("proactive_followup_directive") or {})
    if not directive:
        return None
    guidance_plan = dict(state.get("guidance_plan") or {})
    conversation_cadence_plan = dict(state.get("conversation_cadence_plan") or {})
    session_ritual_plan = dict(state.get("session_ritual_plan") or {})
    somatic_orchestration_plan = dict(state.get("somatic_orchestration_plan") or {})
    proactive_cadence_plan = dict(state.get("proactive_cadence_plan") or {})
    reengagement_matrix_assessment = dict(
        state.get("reengagement_matrix_assessment") or {}
    )
    selected_matrix_candidate = _selected_matrix_candidate(
        reengagement_matrix_assessment
    )
    reengagement_plan = dict(state.get("reengagement_plan") or {})
    proactive_scheduling_plan = dict(state.get("proactive_scheduling_plan") or {})
    proactive_guardrail_plan = dict(state.get("proactive_guardrail_plan") or {})
    proactive_orchestration_plan = dict(
        state.get("proactive_orchestration_plan") or {}
    )
    proactive_actuation_plan = dict(state.get("proactive_actuation_plan") or {})
    proactive_progression_plan = dict(state.get("proactive_progression_plan") or {})

    latest_proactive_event = _latest_event(
        events,
        event_type=PROACTIVE_FOLLOWUP_UPDATED,
    )
    latest_proactive_scheduling_event = _latest_event(
        events,
        event_type=PROACTIVE_SCHEDULING_UPDATED,
    )
    latest_proactive_orchestration_event = _latest_event(
        events,
        event_type=PROACTIVE_ORCHESTRATION_UPDATED,
    )
    latest_proactive_actuation_event = _latest_event(
        events,
        event_type=PROACTIVE_ACTUATION_UPDATED,
    )
    latest_proactive_progression_event = _latest_event(
        events,
        event_type=PROACTIVE_PROGRESSION_UPDATED,
    )
    latest_proactive_dispatch_gate_event = _latest_event(
        events,
        event_type=PROACTIVE_DISPATCH_GATE_UPDATED,
    )
    latest_proactive_dispatch_feedback_event = _latest_event(
        events,
        event_type=PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    )
    latest_proactive_stage_controller_event = _latest_event(
        events,
        event_type=PROACTIVE_STAGE_CONTROLLER_UPDATED,
    )
    latest_proactive_line_controller_event = _latest_event(
        events,
        event_type=PROACTIVE_LINE_CONTROLLER_UPDATED,
    )
    latest_session_event = _latest_event(
        events,
        event_type=SESSION_STARTED,
    )
    latest_user_event = _latest_event(events, event_type=USER_MESSAGE_RECEIVED)
    latest_assistant_event = _latest_event(
        events,
        event_type=ASSISTANT_MESSAGE_SENT,
    )

    directive_time = (
        latest_proactive_event.occurred_at
        if latest_proactive_event is not None
        else (events[-1].occurred_at if events else reference_time)
    )
    dispatch_events_for_directive = [
        event
        for event in events
        if event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED
        and latest_proactive_event is not None
        and event.occurred_at >= latest_proactive_event.occurred_at
    ]
    if dispatch_events_for_directive:
        latest_dispatch_payload = dict(dispatch_events_for_directive[-1].payload)
        if int(
            latest_dispatch_payload.get(
                "proactive_cadence_remaining_after_dispatch",
                1,
            )
            or 0
        ) <= 0:
            return None
    dispatched_stage_count = len(dispatch_events_for_directive)
    stage_labels = [
        str(item)
        for item in list(proactive_cadence_plan.get("stage_labels") or [])
        if str(item).strip()
    ]
    stage_intervals_seconds = [
        max(0, int(item))
        for item in list(proactive_cadence_plan.get("stage_intervals_seconds") or [])
    ]
    close_after_stage_index = max(
        0,
        int(proactive_cadence_plan.get("close_after_stage_index") or 0),
    )
    if not stage_labels:
        stage_labels = ["first_touch"]
        stage_intervals_seconds = [max(0, int(directive.get("trigger_after_seconds") or 0))]
        close_after_stage_index = 1
    max_dispatch_count = max(
        1,
        int(proactive_guardrail_plan.get("max_dispatch_count") or close_after_stage_index),
    )
    if close_after_stage_index > 0:
        max_dispatch_count = min(max_dispatch_count, close_after_stage_index)
    if dispatched_stage_count >= max_dispatch_count:
        return None
    stage_index_by_label = {
        label: index + 1 for index, label in enumerate(stage_labels)
    }
    close_loop_stage = str(
        proactive_progression_plan.get("close_loop_stage")
        or proactive_orchestration_plan.get("close_loop_stage")
        or stage_labels[-1]
    )
    current_stage_index = dispatched_stage_count + 1
    current_stage_label = stage_labels[min(current_stage_index - 1, len(stage_labels) - 1)]
    current_stage_directive = None
    current_stage_actuation = None
    current_stage_progression = None
    current_stage_guardrail = None

    due_at: datetime | None = None
    base_due_at: datetime | None = None
    expires_at: datetime | None = None
    seconds_until_due: int | None = None
    seconds_overdue: int | None = None
    window_remaining_seconds: int | None = None
    schedule_reason: str | None = None
    scheduling_deferred_until: datetime | None = None
    progression_anchor_at: datetime | None = None
    progression_advanced = False
    progression_reason: str | None = None
    progression_applied_actions: list[str] = []

    window_seconds = 0
    directive_status = str(directive.get("status") or "hold")
    queue_status = "hold"
    if directive_status == "ready" and bool(directive.get("eligible")):
        window_seconds = max(
            0,
            int(
                proactive_cadence_plan.get("window_seconds")
                or directive.get("window_seconds")
                or 0
            ),
        )
        while current_stage_index <= max_dispatch_count:
            current_stage_label = stage_labels[
                min(current_stage_index - 1, len(stage_labels) - 1)
            ]
            current_stage_directive = _stage_entry(
                proactive_orchestration_plan.get("stage_directives"),
                current_stage_label,
            )
            current_stage_actuation = _stage_entry(
                proactive_actuation_plan.get("stage_actuations"),
                current_stage_label,
            )
            current_stage_progression = _stage_entry(
                proactive_progression_plan.get("stage_progressions"),
                current_stage_label,
            )
            current_stage_guardrail = _stage_entry(
                proactive_guardrail_plan.get("stage_guardrails"),
                current_stage_label,
            )
            trigger_after_seconds = stage_intervals_seconds[
                min(current_stage_index - 1, len(stage_intervals_seconds) - 1)
            ]
            (
                base_due_at,
                due_at,
                expires_at,
                seconds_until_due,
                seconds_overdue,
                window_remaining_seconds,
                schedule_reason,
                scheduling_deferred_until,
            ) = _compute_stage_schedule(
                reference_time=reference_time,
                directive_time=directive_time,
                dispatch_events_for_directive=dispatch_events_for_directive,
                latest_assistant_event=latest_assistant_event,
                proactive_scheduling_plan=proactive_scheduling_plan,
                trigger_after_seconds=trigger_after_seconds,
                window_seconds=window_seconds,
                progression_anchor_at=progression_anchor_at,
            )
            due_at, expires_at, schedule_reason = _apply_matrix_learning_spacing(
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
                current_stage_label=current_stage_label,
                reengagement_matrix_assessment=reengagement_matrix_assessment,
            )
            due_at, expires_at, schedule_reason = _apply_stage_guardrail(
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                latest_user_event=latest_user_event,
                dispatch_events_for_directive=dispatch_events_for_directive,
                current_stage_guardrail=current_stage_guardrail,
            )
            due_at, expires_at, schedule_reason = _apply_stage_controller(
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
                current_stage_label=current_stage_label,
                latest_stage_controller_event=latest_proactive_stage_controller_event,
            )
            due_at, expires_at, schedule_reason = _apply_line_controller(
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
                current_stage_label=current_stage_label,
                latest_line_controller_event=latest_proactive_line_controller_event,
            )
            due_at, expires_at, schedule_reason = _apply_dispatch_gate(
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
                current_stage_label=current_stage_label,
                dispatch_events_for_directive=dispatch_events_for_directive,
                latest_dispatch_gate_event=latest_proactive_dispatch_gate_event,
            )
            (
                queue_status,
                seconds_until_due,
                seconds_overdue,
                window_remaining_seconds,
            ) = _resolve_queue_status(
                reference_time=reference_time,
                base_due_at=base_due_at,
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
            )

            if queue_status != "overdue":
                break

            max_overdue_seconds = max(
                0,
                int((current_stage_progression or {}).get("max_overdue_seconds") or 0),
            )
            if (
                expires_at is None
                or reference_time
                <= expires_at + timedelta(seconds=max_overdue_seconds)
            ):
                break

            expired_action = str(
                (current_stage_progression or {}).get("on_expired")
                or "close_line"
            )
            progression_advanced = True
            if expired_action == "close_line":
                return None

            if expired_action == "jump_to_close_loop":
                next_stage_index = stage_index_by_label.get(
                    close_loop_stage,
                    close_after_stage_index,
                )
            else:
                next_stage_index = min(
                    current_stage_index + 1,
                    close_after_stage_index,
                )

            if next_stage_index <= current_stage_index:
                return None
            if next_stage_index > max_dispatch_count:
                return None

            next_stage_label = stage_labels[
                min(next_stage_index - 1, len(stage_labels) - 1)
            ]
            progression_applied_actions.append(
                f"{current_stage_label}:{expired_action}->{next_stage_label}"
            )
            progression_reason = " | ".join(progression_applied_actions)
            current_stage_index = next_stage_index
            progression_anchor_at = expires_at + timedelta(
                seconds=max_overdue_seconds
            )

        if current_stage_index > max_dispatch_count:
            return None

        current_stage_label = stage_labels[
            min(current_stage_index - 1, len(stage_labels) - 1)
        ]
        current_stage_directive = _stage_entry(
            proactive_orchestration_plan.get("stage_directives"),
            current_stage_label,
        )
        current_stage_actuation = _stage_entry(
            proactive_actuation_plan.get("stage_actuations"),
            current_stage_label,
        )
        current_stage_progression = _stage_entry(
            proactive_progression_plan.get("stage_progressions"),
            current_stage_label,
        )
        current_stage_guardrail = _stage_entry(
            proactive_guardrail_plan.get("stage_guardrails"),
            current_stage_label,
        )

    projected_stage_state = dict(state.get("proactive_stage_state_decision") or {})
    projected_line_state = dict(state.get("proactive_line_state_decision") or {})
    projected_line_transition = dict(
        state.get("proactive_line_transition_decision") or {}
    )
    projected_line_machine = dict(state.get("proactive_line_machine_decision") or {})
    projected_lifecycle_state = dict(
        state.get("proactive_lifecycle_state_decision") or {}
    )
    projected_lifecycle_transition = dict(
        state.get("proactive_lifecycle_transition_decision") or {}
    )
    projected_lifecycle_machine = dict(
        state.get("proactive_lifecycle_machine_decision") or {}
    )
    projected_lifecycle_envelope = dict(
        state.get("proactive_lifecycle_envelope_decision") or {}
    )
    projected_lifecycle_scheduler = dict(
        state.get("proactive_lifecycle_scheduler_decision") or {}
    )
    projected_lifecycle_window = dict(
        state.get("proactive_lifecycle_window_decision") or {}
    )
    projected_lifecycle_queue = dict(
        state.get("proactive_lifecycle_queue_decision") or {}
    )
    projected_lifecycle_dispatch = dict(
        state.get("proactive_lifecycle_dispatch_decision") or {}
    )
    projected_lifecycle_outcome = dict(
        state.get("proactive_lifecycle_outcome_decision") or {}
    )
    projected_lifecycle_resolution = dict(
        state.get("proactive_lifecycle_resolution_decision") or {}
    )
    projected_lifecycle_activation = dict(
        state.get("proactive_lifecycle_activation_decision") or {}
    )
    projected_lifecycle_settlement = dict(
        state.get("proactive_lifecycle_settlement_decision") or {}
    )
    projected_lifecycle_closure = dict(
        state.get("proactive_lifecycle_closure_decision") or {}
    )
    projected_lifecycle_availability = dict(
        state.get("proactive_lifecycle_availability_decision") or {}
    )
    projected_lifecycle_retention = dict(
        state.get("proactive_lifecycle_retention_decision") or {}
    )
    projected_lifecycle_eligibility = dict(
        state.get("proactive_lifecycle_eligibility_decision") or {}
    )
    projected_lifecycle_candidate = dict(
        state.get("proactive_lifecycle_candidate_decision") or {}
    )
    projected_lifecycle_selectability = dict(
        state.get("proactive_lifecycle_selectability_decision") or {}
    )
    projected_lifecycle_reentry = dict(
        state.get("proactive_lifecycle_reentry_decision") or {}
    )
    projected_lifecycle_reactivation = dict(
        state.get("proactive_lifecycle_reactivation_decision") or {}
    )
    projected_lifecycle_resumption = dict(
        state.get("proactive_lifecycle_resumption_decision") or {}
    )
    projected_lifecycle_readiness = dict(
        state.get("proactive_lifecycle_readiness_decision") or {}
    )
    projected_lifecycle_arming = dict(
        state.get("proactive_lifecycle_arming_decision") or {}
    )
    projected_lifecycle_trigger = dict(
        state.get("proactive_lifecycle_trigger_decision") or {}
    )
    projected_lifecycle_launch = dict(
        state.get("proactive_lifecycle_launch_decision") or {}
    )
    projected_lifecycle_handoff = dict(
        state.get("proactive_lifecycle_handoff_decision") or {}
    )
    projected_lifecycle_continuation = dict(
        state.get("proactive_lifecycle_continuation_decision") or {}
    )
    projected_lifecycle_sustainment = dict(
        state.get("proactive_lifecycle_sustainment_decision") or {}
    )
    projected_lifecycle_stewardship = dict(
        state.get("proactive_lifecycle_stewardship_decision") or {}
    )
    projected_lifecycle_guardianship = dict(
        state.get("proactive_lifecycle_guardianship_decision") or {}
    )
    projected_lifecycle_oversight = dict(
        state.get("proactive_lifecycle_oversight_decision") or {}
    )
    projected_lifecycle_assurance = dict(
        state.get("proactive_lifecycle_assurance_decision") or {}
    )
    projected_lifecycle_attestation = dict(
        state.get("proactive_lifecycle_attestation_decision") or {}
    )
    projected_lifecycle_verification = dict(
        state.get("proactive_lifecycle_verification_decision") or {}
    )
    projected_lifecycle_certification = dict(
        state.get("proactive_lifecycle_certification_decision") or {}
    )
    projected_lifecycle_confirmation = dict(
        state.get("proactive_lifecycle_confirmation_decision") or {}
    )
    projected_lifecycle_ratification = dict(
        state.get("proactive_lifecycle_ratification_decision") or {}
    )
    projected_lifecycle_endorsement = dict(
        state.get("proactive_lifecycle_endorsement_decision") or {}
    )
    projected_lifecycle_authorization = dict(
        state.get("proactive_lifecycle_authorization_decision") or {}
    )
    projected_lifecycle_enactment = dict(
        state.get("proactive_lifecycle_enactment_decision") or {}
    )
    projected_lifecycle_finality = dict(
        state.get("proactive_lifecycle_finality_decision") or {}
    )
    projected_lifecycle_completion = dict(
        state.get("proactive_lifecycle_completion_decision") or {}
    )
    projected_lifecycle_conclusion = dict(
        state.get("proactive_lifecycle_conclusion_decision") or {}
    )
    projected_lifecycle_disposition = dict(
        state.get("proactive_lifecycle_disposition_decision") or {}
    )
    projected_lifecycle_standing = dict(
        state.get("proactive_lifecycle_standing_decision") or {}
    )
    projected_lifecycle_residency = dict(
        state.get("proactive_lifecycle_residency_decision") or {}
    )
    projected_lifecycle_tenure = dict(
        state.get("proactive_lifecycle_tenure_decision") or {}
    )
    projected_lifecycle_persistence = dict(
        state.get("proactive_lifecycle_persistence_decision") or {}
    )
    projected_lifecycle_durability = dict(
        state.get("proactive_lifecycle_durability_decision") or {}
    )
    projected_lifecycle_longevity = dict(
        state.get("proactive_lifecycle_longevity_decision") or {}
    )
    projected_lifecycle_legacy = dict(
        state.get("proactive_lifecycle_legacy_decision") or {}
    )
    projected_lifecycle_heritage = dict(
        state.get("proactive_lifecycle_heritage_decision") or {}
    )
    projected_lifecycle_lineage = dict(
        state.get("proactive_lifecycle_lineage_decision") or {}
    )
    projected_lifecycle_ancestry = dict(
        state.get("proactive_lifecycle_ancestry_decision") or {}
    )
    projected_lifecycle_provenance = dict(
        state.get("proactive_lifecycle_provenance_decision") or {}
    )
    projected_lifecycle_origin = dict(
        state.get("proactive_lifecycle_origin_decision") or {}
    )
    projected_lifecycle_root = dict(
        state.get("proactive_lifecycle_root_decision") or {}
    )
    projected_lifecycle_foundation = dict(
        state.get("proactive_lifecycle_foundation_decision") or {}
    )
    projected_lifecycle_bedrock = dict(
        state.get("proactive_lifecycle_bedrock_decision") or {}
    )
    projected_lifecycle_substrate = dict(
        state.get("proactive_lifecycle_substrate_decision") or {}
    )
    projected_lifecycle_stratum = dict(
        state.get("proactive_lifecycle_stratum_decision") or {}
    )
    projected_lifecycle_layer = dict(
        state.get("proactive_lifecycle_layer_decision") or {}
    )
    lifecycle_resolution_decision = str(
        projected_lifecycle_resolution.get("decision") or ""
    )
    lifecycle_resolution_stage_label = str(
        projected_lifecycle_resolution.get("current_stage_label") or ""
    )
    lifecycle_resolution_delay_seconds = max(
        0,
        int(projected_lifecycle_resolution.get("additional_delay_seconds") or 0),
    )
    lifecycle_activation_decision = str(
        projected_lifecycle_activation.get("decision") or ""
    )
    lifecycle_activation_stage_label = str(
        projected_lifecycle_activation.get("active_stage_label") or ""
    )
    lifecycle_activation_delay_seconds = max(
        0,
        int(projected_lifecycle_activation.get("additional_delay_seconds") or 0),
    )
    lifecycle_settlement_decision = str(
        projected_lifecycle_settlement.get("decision") or ""
    )
    lifecycle_settlement_stage_label = str(
        projected_lifecycle_settlement.get("active_stage_label") or ""
    )
    lifecycle_settlement_delay_seconds = max(
        0,
        int(projected_lifecycle_settlement.get("additional_delay_seconds") or 0),
    )
    lifecycle_closure_decision = str(
        projected_lifecycle_closure.get("decision") or ""
    )
    lifecycle_closure_stage_label = str(
        projected_lifecycle_closure.get("active_stage_label") or ""
    )
    lifecycle_closure_delay_seconds = max(
        0,
        int(projected_lifecycle_closure.get("additional_delay_seconds") or 0),
    )
    lifecycle_availability_decision = str(
        projected_lifecycle_availability.get("decision") or ""
    )
    lifecycle_availability_stage_label = str(
        projected_lifecycle_availability.get("active_stage_label") or ""
    )
    lifecycle_availability_delay_seconds = max(
        0,
        int(
            projected_lifecycle_availability.get("additional_delay_seconds") or 0
        ),
    )
    lifecycle_retention_decision = str(
        projected_lifecycle_retention.get("decision") or ""
    )
    lifecycle_retention_stage_label = str(
        projected_lifecycle_retention.get("active_stage_label") or ""
    )
    lifecycle_retention_delay_seconds = max(
        0,
        int(projected_lifecycle_retention.get("additional_delay_seconds") or 0),
    )
    lifecycle_eligibility_decision = str(
        projected_lifecycle_eligibility.get("decision") or ""
    )
    lifecycle_eligibility_stage_label = str(
        projected_lifecycle_eligibility.get("active_stage_label") or ""
    )
    lifecycle_eligibility_delay_seconds = max(
        0,
        int(projected_lifecycle_eligibility.get("additional_delay_seconds") or 0),
    )
    lifecycle_candidate_decision = str(
        projected_lifecycle_candidate.get("decision") or ""
    )
    lifecycle_candidate_stage_label = str(
        projected_lifecycle_candidate.get("active_stage_label") or ""
    )
    lifecycle_candidate_delay_seconds = max(
        0,
        int(projected_lifecycle_candidate.get("additional_delay_seconds") or 0),
    )
    lifecycle_selectability_decision = str(
        projected_lifecycle_selectability.get("decision") or ""
    )
    lifecycle_selectability_stage_label = str(
        projected_lifecycle_selectability.get("active_stage_label") or ""
    )
    lifecycle_selectability_delay_seconds = max(
        0,
        int(
            projected_lifecycle_selectability.get("additional_delay_seconds") or 0
        ),
    )
    lifecycle_reentry_decision = str(
        projected_lifecycle_reentry.get("decision") or ""
    )
    lifecycle_reentry_stage_label = str(
        projected_lifecycle_reentry.get("active_stage_label") or ""
    )
    lifecycle_reentry_delay_seconds = max(
        0,
        int(projected_lifecycle_reentry.get("additional_delay_seconds") or 0),
    )
    lifecycle_reactivation_decision = str(
        projected_lifecycle_reactivation.get("decision") or ""
    )
    lifecycle_reactivation_stage_label = str(
        projected_lifecycle_reactivation.get("active_stage_label") or ""
    )
    lifecycle_reactivation_delay_seconds = max(
        0,
        int(projected_lifecycle_reactivation.get("additional_delay_seconds") or 0),
    )
    lifecycle_resumption_decision = str(
        projected_lifecycle_resumption.get("decision") or ""
    )
    lifecycle_resumption_stage_label = str(
        projected_lifecycle_resumption.get("active_stage_label") or ""
    )
    lifecycle_resumption_delay_seconds = max(
        0,
        int(projected_lifecycle_resumption.get("additional_delay_seconds") or 0),
    )
    lifecycle_readiness_decision = str(
        projected_lifecycle_readiness.get("decision") or ""
    )
    lifecycle_readiness_stage_label = str(
        projected_lifecycle_readiness.get("active_stage_label") or ""
    )
    lifecycle_readiness_delay_seconds = max(
        0,
        int(projected_lifecycle_readiness.get("additional_delay_seconds") or 0),
    )
    lifecycle_arming_decision = str(
        projected_lifecycle_arming.get("decision") or ""
    )
    lifecycle_arming_stage_label = str(
        projected_lifecycle_arming.get("active_stage_label") or ""
    )
    lifecycle_arming_delay_seconds = max(
        0,
        int(projected_lifecycle_arming.get("additional_delay_seconds") or 0),
    )
    lifecycle_trigger_decision = str(
        projected_lifecycle_trigger.get("decision") or ""
    )
    lifecycle_trigger_stage_label = str(
        projected_lifecycle_trigger.get("active_stage_label") or ""
    )
    lifecycle_trigger_delay_seconds = max(
        0,
        int(projected_lifecycle_trigger.get("additional_delay_seconds") or 0),
    )
    lifecycle_launch_decision = str(
        projected_lifecycle_launch.get("decision") or ""
    )
    lifecycle_launch_stage_label = str(
        projected_lifecycle_launch.get("active_stage_label") or ""
    )
    lifecycle_launch_delay_seconds = max(
        0,
        int(projected_lifecycle_launch.get("additional_delay_seconds") or 0),
    )
    lifecycle_handoff_decision = str(
        projected_lifecycle_handoff.get("decision") or ""
    )
    lifecycle_handoff_stage_label = str(
        projected_lifecycle_handoff.get("active_stage_label") or ""
    )
    lifecycle_handoff_delay_seconds = max(
        0,
        int(projected_lifecycle_handoff.get("additional_delay_seconds") or 0),
    )
    lifecycle_continuation_decision = str(
        projected_lifecycle_continuation.get("decision") or ""
    )
    lifecycle_continuation_stage_label = str(
        projected_lifecycle_continuation.get("active_stage_label") or ""
    )
    lifecycle_continuation_delay_seconds = max(
        0,
        int(projected_lifecycle_continuation.get("additional_delay_seconds") or 0),
    )
    lifecycle_sustainment_decision = str(
        projected_lifecycle_sustainment.get("decision") or ""
    )
    lifecycle_sustainment_stage_label = str(
        projected_lifecycle_sustainment.get("active_stage_label") or ""
    )
    lifecycle_sustainment_delay_seconds = max(
        0,
        int(projected_lifecycle_sustainment.get("additional_delay_seconds") or 0),
    )
    lifecycle_stewardship_decision = str(
        projected_lifecycle_stewardship.get("decision") or ""
    )
    lifecycle_stewardship_stage_label = str(
        projected_lifecycle_stewardship.get("active_stage_label") or ""
    )
    lifecycle_stewardship_delay_seconds = max(
        0,
        int(projected_lifecycle_stewardship.get("additional_delay_seconds") or 0),
    )
    lifecycle_guardianship_decision = str(
        projected_lifecycle_guardianship.get("decision") or ""
    )
    lifecycle_guardianship_stage_label = str(
        projected_lifecycle_guardianship.get("active_stage_label") or ""
    )
    lifecycle_guardianship_delay_seconds = max(
        0,
        int(projected_lifecycle_guardianship.get("additional_delay_seconds") or 0),
    )
    lifecycle_oversight_decision = str(
        projected_lifecycle_oversight.get("decision") or ""
    )
    lifecycle_oversight_stage_label = str(
        projected_lifecycle_oversight.get("active_stage_label") or ""
    )
    lifecycle_oversight_delay_seconds = max(
        0,
        int(projected_lifecycle_oversight.get("additional_delay_seconds") or 0),
    )
    lifecycle_assurance_decision = str(
        projected_lifecycle_assurance.get("decision") or ""
    )
    lifecycle_assurance_stage_label = str(
        projected_lifecycle_assurance.get("active_stage_label") or ""
    )
    lifecycle_assurance_delay_seconds = max(
        0,
        int(projected_lifecycle_assurance.get("additional_delay_seconds") or 0),
    )
    lifecycle_attestation_decision = str(
        projected_lifecycle_attestation.get("decision") or ""
    )
    lifecycle_attestation_stage_label = str(
        projected_lifecycle_attestation.get("active_stage_label") or ""
    )
    lifecycle_attestation_delay_seconds = max(
        0,
        int(projected_lifecycle_attestation.get("additional_delay_seconds") or 0),
    )
    lifecycle_verification_decision = str(
        projected_lifecycle_verification.get("decision") or ""
    )
    lifecycle_verification_stage_label = str(
        projected_lifecycle_verification.get("active_stage_label") or ""
    )
    lifecycle_verification_delay_seconds = max(
        0,
        int(projected_lifecycle_verification.get("additional_delay_seconds") or 0),
    )
    lifecycle_certification_decision = str(
        projected_lifecycle_certification.get("decision") or ""
    )
    lifecycle_certification_stage_label = str(
        projected_lifecycle_certification.get("active_stage_label") or ""
    )
    lifecycle_certification_delay_seconds = max(
        0,
        int(projected_lifecycle_certification.get("additional_delay_seconds") or 0),
    )
    lifecycle_confirmation_decision = str(
        projected_lifecycle_confirmation.get("decision") or ""
    )
    lifecycle_confirmation_stage_label = str(
        projected_lifecycle_confirmation.get("active_stage_label") or ""
    )
    lifecycle_confirmation_delay_seconds = max(
        0,
        int(projected_lifecycle_confirmation.get("additional_delay_seconds") or 0),
    )
    lifecycle_ratification_decision = str(
        projected_lifecycle_ratification.get("decision") or ""
    )
    lifecycle_ratification_stage_label = str(
        projected_lifecycle_ratification.get("active_stage_label") or ""
    )
    lifecycle_ratification_delay_seconds = max(
        0,
        int(projected_lifecycle_ratification.get("additional_delay_seconds") or 0),
    )
    lifecycle_endorsement_decision = str(
        projected_lifecycle_endorsement.get("decision") or ""
    )
    lifecycle_endorsement_stage_label = str(
        projected_lifecycle_endorsement.get("active_stage_label") or ""
    )
    lifecycle_endorsement_delay_seconds = max(
        0,
        int(projected_lifecycle_endorsement.get("additional_delay_seconds") or 0),
    )
    lifecycle_authorization_decision = str(
        projected_lifecycle_authorization.get("decision") or ""
    )
    lifecycle_enactment_decision = str(
        projected_lifecycle_enactment.get("decision") or ""
    )
    lifecycle_enactment_stage_label = str(
        projected_lifecycle_enactment.get("active_stage_label") or ""
    )
    lifecycle_enactment_delay_seconds = max(
        0,
        int(projected_lifecycle_enactment.get("additional_delay_seconds") or 0),
    )
    lifecycle_finality_decision = str(
        projected_lifecycle_finality.get("decision") or ""
    )
    lifecycle_finality_stage_label = str(
        projected_lifecycle_finality.get("active_stage_label") or ""
    )
    lifecycle_finality_delay_seconds = max(
        0,
        int(projected_lifecycle_finality.get("additional_delay_seconds") or 0),
    )
    lifecycle_completion_decision = str(
        projected_lifecycle_completion.get("decision") or ""
    )
    lifecycle_completion_stage_label = str(
        projected_lifecycle_completion.get("active_stage_label") or ""
    )
    lifecycle_completion_delay_seconds = max(
        0,
        int(projected_lifecycle_completion.get("additional_delay_seconds") or 0),
    )
    lifecycle_conclusion_decision = str(
        projected_lifecycle_conclusion.get("decision") or ""
    )
    lifecycle_conclusion_stage_label = str(
        projected_lifecycle_conclusion.get("active_stage_label") or ""
    )
    lifecycle_conclusion_delay_seconds = max(
        0,
        int(projected_lifecycle_conclusion.get("additional_delay_seconds") or 0),
    )
    lifecycle_disposition_decision = str(
        projected_lifecycle_disposition.get("decision") or ""
    )
    lifecycle_disposition_stage_label = str(
        projected_lifecycle_disposition.get("active_stage_label") or ""
    )
    lifecycle_disposition_delay_seconds = max(
        0,
        int(projected_lifecycle_disposition.get("additional_delay_seconds") or 0),
    )
    lifecycle_standing_decision = str(
        projected_lifecycle_standing.get("decision") or ""
    )
    lifecycle_standing_stage_label = str(
        projected_lifecycle_standing.get("active_stage_label") or ""
    )
    lifecycle_standing_delay_seconds = max(
        0,
        int(projected_lifecycle_standing.get("additional_delay_seconds") or 0),
    )
    lifecycle_residency_decision = str(
        projected_lifecycle_residency.get("decision") or ""
    )
    lifecycle_residency_stage_label = str(
        projected_lifecycle_residency.get("active_stage_label") or ""
    )
    lifecycle_residency_delay_seconds = max(
        0,
        int(projected_lifecycle_residency.get("additional_delay_seconds") or 0),
    )
    lifecycle_tenure_decision = str(projected_lifecycle_tenure.get("decision") or "")
    lifecycle_tenure_stage_label = str(
        projected_lifecycle_tenure.get("active_stage_label") or ""
    )
    lifecycle_tenure_delay_seconds = max(
        0,
        int(projected_lifecycle_tenure.get("additional_delay_seconds") or 0),
    )
    lifecycle_persistence_decision = str(
        projected_lifecycle_persistence.get("decision") or ""
    )
    lifecycle_persistence_stage_label = str(
        projected_lifecycle_persistence.get("active_stage_label") or ""
    )
    lifecycle_persistence_delay_seconds = max(
        0,
        int(projected_lifecycle_persistence.get("additional_delay_seconds") or 0),
    )
    lifecycle_durability_decision = str(
        projected_lifecycle_durability.get("decision") or ""
    )
    lifecycle_durability_stage_label = str(
        projected_lifecycle_durability.get("active_stage_label") or ""
    )
    lifecycle_durability_delay_seconds = max(
        0,
        int(projected_lifecycle_durability.get("additional_delay_seconds") or 0),
    )
    lifecycle_longevity_decision = str(
        projected_lifecycle_longevity.get("decision") or ""
    )
    lifecycle_longevity_stage_label = str(
        projected_lifecycle_longevity.get("active_stage_label") or ""
    )
    lifecycle_longevity_delay_seconds = max(
        0,
        int(projected_lifecycle_longevity.get("additional_delay_seconds") or 0),
    )
    lifecycle_legacy_decision = str(projected_lifecycle_legacy.get("decision") or "")
    lifecycle_legacy_stage_label = str(
        projected_lifecycle_legacy.get("active_stage_label") or ""
    )
    lifecycle_legacy_delay_seconds = max(
        0, int(projected_lifecycle_legacy.get("additional_delay_seconds") or 0)
    )
    lifecycle_heritage_decision = str(
        projected_lifecycle_heritage.get("decision") or ""
    )
    lifecycle_heritage_stage_label = str(
        projected_lifecycle_heritage.get("active_stage_label") or ""
    )
    lifecycle_heritage_delay_seconds = max(
        0, int(projected_lifecycle_heritage.get("additional_delay_seconds") or 0)
    )
    lifecycle_lineage_decision = str(
        projected_lifecycle_lineage.get("decision") or ""
    )
    lifecycle_lineage_stage_label = str(
        projected_lifecycle_lineage.get("active_stage_label") or ""
    )
    lifecycle_lineage_delay_seconds = max(
        0, int(projected_lifecycle_lineage.get("additional_delay_seconds") or 0)
    )
    lifecycle_ancestry_decision = str(
        projected_lifecycle_ancestry.get("decision") or ""
    )
    lifecycle_ancestry_stage_label = str(
        projected_lifecycle_ancestry.get("active_stage_label") or ""
    )
    lifecycle_ancestry_delay_seconds = max(
        0, int(projected_lifecycle_ancestry.get("additional_delay_seconds") or 0)
    )
    lifecycle_provenance_decision = str(
        projected_lifecycle_provenance.get("decision") or ""
    )
    lifecycle_provenance_stage_label = str(
        projected_lifecycle_provenance.get("active_stage_label") or ""
    )
    lifecycle_provenance_delay_seconds = max(
        0, int(projected_lifecycle_provenance.get("additional_delay_seconds") or 0)
    )
    lifecycle_origin_decision = str(projected_lifecycle_origin.get("decision") or "")
    lifecycle_origin_stage_label = str(
        projected_lifecycle_origin.get("active_stage_label") or ""
    )
    lifecycle_origin_delay_seconds = max(
        0, int(projected_lifecycle_origin.get("additional_delay_seconds") or 0)
    )
    lifecycle_root_decision = str(projected_lifecycle_root.get("decision") or "")
    lifecycle_root_stage_label = str(
        projected_lifecycle_root.get("active_stage_label") or ""
    )
    lifecycle_root_delay_seconds = max(
        0, int(projected_lifecycle_root.get("additional_delay_seconds") or 0)
    )
    lifecycle_foundation_decision = str(
        projected_lifecycle_foundation.get("decision") or ""
    )
    lifecycle_foundation_stage_label = str(
        projected_lifecycle_foundation.get("active_stage_label") or ""
    )
    lifecycle_foundation_delay_seconds = max(
        0, int(projected_lifecycle_foundation.get("additional_delay_seconds") or 0)
    )
    lifecycle_bedrock_decision = str(
        projected_lifecycle_bedrock.get("decision") or ""
    )
    lifecycle_bedrock_stage_label = str(
        projected_lifecycle_bedrock.get("active_stage_label") or ""
    )
    lifecycle_bedrock_delay_seconds = max(
        0, int(projected_lifecycle_bedrock.get("additional_delay_seconds") or 0)
    )
    lifecycle_substrate_decision = str(
        projected_lifecycle_substrate.get("decision") or ""
    )
    lifecycle_substrate_stage_label = str(
        projected_lifecycle_substrate.get("active_stage_label") or ""
    )
    lifecycle_substrate_delay_seconds = max(
        0, int(projected_lifecycle_substrate.get("additional_delay_seconds") or 0)
    )
    lifecycle_stratum_decision = str(
        projected_lifecycle_stratum.get("decision") or ""
    )
    lifecycle_stratum_stage_label = str(
        projected_lifecycle_stratum.get("active_stage_label") or ""
    )
    lifecycle_stratum_delay_seconds = max(
        0, int(projected_lifecycle_stratum.get("additional_delay_seconds") or 0)
    )
    lifecycle_layer_decision = str(
        projected_lifecycle_layer.get("decision") or ""
    )
    lifecycle_layer_stage_label = str(
        projected_lifecycle_layer.get("active_stage_label") or ""
    )
    lifecycle_layer_delay_seconds = max(
        0, int(projected_lifecycle_layer.get("additional_delay_seconds") or 0)
    )
    projected_dispatch_envelope = dict(
        state.get("proactive_dispatch_envelope_decision") or {}
    )
    skip_lifecycle_dispatch_override = False
    layer_applies = (
        lifecycle_layer_decision in {
            "archive_lifecycle_layer",
            "retire_lifecycle_layer",
        }
        or lifecycle_layer_stage_label == current_stage_label
    )
    if layer_applies and lifecycle_layer_decision in {
        "archive_lifecycle_layer",
        "retire_lifecycle_layer",
    }:
        return None
    if layer_applies and lifecycle_layer_decision == "pause_lifecycle_layer":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif layer_applies and lifecycle_layer_decision == "buffer_lifecycle_layer":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_layer_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            schedule_reason = " | ".join(
                part
                for part in str(schedule_reason).split(" | ")
                if part != "lifecycle_stratum_buffered"
            )
            if "lifecycle_layer_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_layer_buffered"
        else:
            schedule_reason = "lifecycle_layer_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif layer_applies and lifecycle_layer_decision == "keep_lifecycle_layer":
        skip_lifecycle_dispatch_override = True
    stratum_applies = layer_applies or (
        lifecycle_stratum_decision in {
            "archive_lifecycle_stratum",
            "retire_lifecycle_stratum",
        }
        or lifecycle_stratum_stage_label == current_stage_label
    )
    if (
        not layer_applies
        and stratum_applies
        and lifecycle_stratum_decision in {
        "archive_lifecycle_stratum",
        "retire_lifecycle_stratum",
        }
    ):
        return None
    if (
        not layer_applies
        and stratum_applies
        and lifecycle_stratum_decision == "pause_lifecycle_stratum"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        stratum_applies
        and lifecycle_stratum_decision == "buffer_lifecycle_stratum"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_stratum_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            schedule_reason = " | ".join(
                part
                for part in str(schedule_reason).split(" | ")
                if part != "lifecycle_substrate_buffered"
            )
            if "lifecycle_stratum_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_stratum_buffered"
                )
        else:
            schedule_reason = "lifecycle_stratum_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        stratum_applies and lifecycle_stratum_decision == "keep_lifecycle_stratum"
    ):
        skip_lifecycle_dispatch_override = True
    substrate_applies = layer_applies or stratum_applies or (
        lifecycle_substrate_decision in {
            "archive_lifecycle_substrate",
            "retire_lifecycle_substrate",
        }
        or lifecycle_substrate_stage_label == current_stage_label
    )
    if (
        not layer_applies
        and
        not stratum_applies
        and substrate_applies
        and lifecycle_substrate_decision in {
        "archive_lifecycle_substrate",
        "retire_lifecycle_substrate",
        }
    ):
        return None
    if (
        not layer_applies
        and
        not stratum_applies
        and
        substrate_applies
        and lifecycle_substrate_decision == "pause_lifecycle_substrate"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        not stratum_applies
        and
        substrate_applies
        and lifecycle_substrate_decision == "buffer_lifecycle_substrate"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_substrate_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_substrate_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_substrate_buffered"
                )
        else:
            schedule_reason = "lifecycle_substrate_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        not stratum_applies
        and
        substrate_applies
        and lifecycle_substrate_decision == "keep_lifecycle_substrate"
    ):
        skip_lifecycle_dispatch_override = True
    bedrock_applies = layer_applies or stratum_applies or substrate_applies or (
        lifecycle_bedrock_decision in {
            "archive_lifecycle_bedrock",
            "retire_lifecycle_bedrock",
        }
        or lifecycle_bedrock_stage_label == current_stage_label
    )
    if (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and bedrock_applies
        and lifecycle_bedrock_decision in {
        "archive_lifecycle_bedrock",
        "retire_lifecycle_bedrock",
        }
    ):
        return None
    if (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and bedrock_applies
        and lifecycle_bedrock_decision == "pause_lifecycle_bedrock"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and bedrock_applies
        and lifecycle_bedrock_decision == "buffer_lifecycle_bedrock"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_bedrock_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_bedrock_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_bedrock_buffered"
                )
        else:
            schedule_reason = "lifecycle_bedrock_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and bedrock_applies
        and lifecycle_bedrock_decision == "keep_lifecycle_bedrock"
    ):
        skip_lifecycle_dispatch_override = True
    foundation_applies = (
        layer_applies
        or stratum_applies
        or substrate_applies
        or bedrock_applies
        or (
        lifecycle_foundation_decision in {
            "archive_lifecycle_foundation",
            "retire_lifecycle_foundation",
        }
        or lifecycle_foundation_stage_label == current_stage_label
        )
    )
    if (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and
        not bedrock_applies
        and foundation_applies
        and lifecycle_foundation_decision in {
        "archive_lifecycle_foundation",
        "retire_lifecycle_foundation",
        }
    ):
        return None
    if (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and
        not bedrock_applies
        and foundation_applies
        and lifecycle_foundation_decision == "pause_lifecycle_foundation"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and
        not bedrock_applies
        and foundation_applies
        and lifecycle_foundation_decision == "buffer_lifecycle_foundation"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_foundation_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_foundation_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_foundation_buffered"
                )
        else:
            schedule_reason = "lifecycle_foundation_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not layer_applies
        and
        not stratum_applies
        and
        not substrate_applies
        and
        not bedrock_applies
        and foundation_applies
        and lifecycle_foundation_decision == "keep_lifecycle_foundation"
    ):
        skip_lifecycle_dispatch_override = True
    root_applies = (
        not foundation_applies
        and (
            lifecycle_root_decision in {
                "archive_lifecycle_root",
                "retire_lifecycle_root",
            }
            or lifecycle_root_stage_label == current_stage_label
        )
    )
    if root_applies and lifecycle_root_decision in {
        "archive_lifecycle_root",
        "retire_lifecycle_root",
    }:
        return None
    if root_applies and lifecycle_root_decision == "pause_lifecycle_root":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif root_applies and lifecycle_root_decision == "buffer_lifecycle_root":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_root_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_root_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_root_buffered"
        else:
            schedule_reason = "lifecycle_root_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif root_applies and lifecycle_root_decision == "keep_lifecycle_root":
        skip_lifecycle_dispatch_override = True
    origin_applies = (
        not foundation_applies
        and not root_applies
        and (
            lifecycle_origin_decision in {
                "archive_lifecycle_origin",
                "retire_lifecycle_origin",
            }
            or lifecycle_origin_stage_label == current_stage_label
        )
    )
    if origin_applies and lifecycle_origin_decision in {
        "archive_lifecycle_origin",
        "retire_lifecycle_origin",
    }:
        return None
    if origin_applies and lifecycle_origin_decision == "pause_lifecycle_origin":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif origin_applies and lifecycle_origin_decision == "buffer_lifecycle_origin":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_origin_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_origin_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_origin_buffered"
        else:
            schedule_reason = "lifecycle_origin_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif origin_applies and lifecycle_origin_decision == "keep_lifecycle_origin":
        skip_lifecycle_dispatch_override = True
    provenance_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and (
            lifecycle_provenance_decision in {
                "archive_lifecycle_provenance",
                "retire_lifecycle_provenance",
            }
            or lifecycle_provenance_stage_label == current_stage_label
        )
    )
    if provenance_applies and lifecycle_provenance_decision in {
        "archive_lifecycle_provenance",
        "retire_lifecycle_provenance",
    }:
        return None
    if (
        provenance_applies
        and lifecycle_provenance_decision == "pause_lifecycle_provenance"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        provenance_applies
        and lifecycle_provenance_decision == "buffer_lifecycle_provenance"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_provenance_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_provenance_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_provenance_buffered"
                )
        else:
            schedule_reason = "lifecycle_provenance_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif provenance_applies and (
        lifecycle_provenance_decision == "keep_lifecycle_provenance"
    ):
        skip_lifecycle_dispatch_override = True
    ancestry_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and (
            lifecycle_ancestry_decision in {
                "archive_lifecycle_ancestry",
                "retire_lifecycle_ancestry",
            }
            or lifecycle_ancestry_stage_label == current_stage_label
        )
    )
    if ancestry_applies and lifecycle_ancestry_decision in {
        "archive_lifecycle_ancestry",
        "retire_lifecycle_ancestry",
    }:
        return None
    if ancestry_applies and lifecycle_ancestry_decision == "pause_lifecycle_ancestry":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        ancestry_applies
        and lifecycle_ancestry_decision == "buffer_lifecycle_ancestry"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_ancestry_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_ancestry_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_ancestry_buffered"
                )
        else:
            schedule_reason = "lifecycle_ancestry_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif ancestry_applies and lifecycle_ancestry_decision == "keep_lifecycle_ancestry":
        skip_lifecycle_dispatch_override = True
    lineage_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and (
            lifecycle_lineage_decision in {
                "archive_lifecycle_lineage",
                "retire_lifecycle_lineage",
            }
            or lifecycle_lineage_stage_label == current_stage_label
        )
    )
    if lineage_applies and lifecycle_lineage_decision in {
        "archive_lifecycle_lineage",
        "retire_lifecycle_lineage",
    }:
        return None
    if lineage_applies and lifecycle_lineage_decision == "pause_lifecycle_lineage":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif lineage_applies and lifecycle_lineage_decision == "buffer_lifecycle_lineage":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_lineage_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_lineage_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_lineage_buffered"
        else:
            schedule_reason = "lifecycle_lineage_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif lineage_applies and lifecycle_lineage_decision == "keep_lifecycle_lineage":
        skip_lifecycle_dispatch_override = True
    heritage_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and (
            lifecycle_heritage_decision in {
                "archive_lifecycle_heritage",
                "retire_lifecycle_heritage",
            }
            or lifecycle_heritage_stage_label == current_stage_label
        )
    )
    if heritage_applies and lifecycle_heritage_decision in {
        "archive_lifecycle_heritage",
        "retire_lifecycle_heritage",
    }:
        return None
    if heritage_applies and lifecycle_heritage_decision == "pause_lifecycle_heritage":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        heritage_applies
        and lifecycle_heritage_decision == "buffer_lifecycle_heritage"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_heritage_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_heritage_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_heritage_buffered"
                )
        else:
            schedule_reason = "lifecycle_heritage_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif heritage_applies and lifecycle_heritage_decision == "keep_lifecycle_heritage":
        skip_lifecycle_dispatch_override = True
    legacy_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and (
            lifecycle_legacy_decision in {
                "archive_lifecycle_legacy",
                "retire_lifecycle_legacy",
            }
            or lifecycle_legacy_stage_label == current_stage_label
        )
    )
    if legacy_applies and lifecycle_legacy_decision in {
        "archive_lifecycle_legacy",
        "retire_lifecycle_legacy",
    }:
        return None
    if legacy_applies and lifecycle_legacy_decision == "pause_lifecycle_legacy":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif legacy_applies and lifecycle_legacy_decision == "buffer_lifecycle_legacy":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_legacy_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_legacy_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_legacy_buffered"
        else:
            schedule_reason = "lifecycle_legacy_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif legacy_applies and lifecycle_legacy_decision == "keep_lifecycle_legacy":
        skip_lifecycle_dispatch_override = True
    longevity_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and (
            lifecycle_longevity_decision in {
                "archive_lifecycle_longevity",
                "retire_lifecycle_longevity",
            }
            or lifecycle_longevity_stage_label == current_stage_label
        )
    )
    if longevity_applies and lifecycle_longevity_decision in {
        "archive_lifecycle_longevity",
        "retire_lifecycle_longevity",
    }:
        return None
    if longevity_applies and lifecycle_longevity_decision == "pause_lifecycle_longevity":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        longevity_applies
        and lifecycle_longevity_decision == "buffer_lifecycle_longevity"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_longevity_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_longevity_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_longevity_buffered"
                )
        else:
            schedule_reason = "lifecycle_longevity_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif longevity_applies and lifecycle_longevity_decision == "keep_lifecycle_longevity":
        skip_lifecycle_dispatch_override = True
    durability_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and not longevity_applies
        and (
            lifecycle_durability_decision in {
                "archive_lifecycle_durability",
                "retire_lifecycle_durability",
            }
            or lifecycle_durability_stage_label == current_stage_label
        )
    )
    if durability_applies and lifecycle_durability_decision in {
        "archive_lifecycle_durability",
        "retire_lifecycle_durability",
    }:
        return None
    if durability_applies and lifecycle_durability_decision == "pause_lifecycle_durability":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        durability_applies
        and lifecycle_durability_decision == "buffer_lifecycle_durability"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_durability_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_durability_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_durability_buffered"
                )
        else:
            schedule_reason = "lifecycle_durability_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif durability_applies and lifecycle_durability_decision == "keep_lifecycle_durability":
        skip_lifecycle_dispatch_override = True
    persistence_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and not longevity_applies
        and not durability_applies
        and (
            lifecycle_persistence_decision in {
                "archive_lifecycle_persistence",
                "retire_lifecycle_persistence",
            }
            or lifecycle_persistence_stage_label == current_stage_label
        )
    )
    if persistence_applies and lifecycle_persistence_decision in {
        "archive_lifecycle_persistence",
        "retire_lifecycle_persistence",
    }:
        return None
    if (
        persistence_applies
        and lifecycle_persistence_decision == "pause_lifecycle_persistence"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        persistence_applies
        and lifecycle_persistence_decision == "buffer_lifecycle_persistence"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_persistence_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_persistence_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_persistence_buffered"
                )
        else:
            schedule_reason = "lifecycle_persistence_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        persistence_applies
        and lifecycle_persistence_decision == "keep_lifecycle_persistence"
    ):
        skip_lifecycle_dispatch_override = True
    tenure_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and not longevity_applies
        and not durability_applies
        and not persistence_applies
        and (
            lifecycle_tenure_decision in {
                "archive_lifecycle_tenure",
                "retire_lifecycle_tenure",
            }
            or lifecycle_tenure_stage_label == current_stage_label
        )
    )
    if tenure_applies and lifecycle_tenure_decision in {
        "archive_lifecycle_tenure",
        "retire_lifecycle_tenure",
    }:
        return None
    if tenure_applies and lifecycle_tenure_decision == "pause_lifecycle_tenure":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif tenure_applies and lifecycle_tenure_decision == "buffer_lifecycle_tenure":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_tenure_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_tenure_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_tenure_buffered"
        else:
            schedule_reason = "lifecycle_tenure_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif tenure_applies and lifecycle_tenure_decision == "keep_lifecycle_tenure":
        skip_lifecycle_dispatch_override = True
    residency_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and not longevity_applies
        and not durability_applies
        and not persistence_applies
        and not tenure_applies
        and (
            lifecycle_residency_decision in {
                "archive_lifecycle_residency",
                "retire_lifecycle_residency",
            }
            or lifecycle_residency_stage_label == current_stage_label
        )
    )
    if residency_applies and lifecycle_residency_decision in {
        "archive_lifecycle_residency",
        "retire_lifecycle_residency",
    }:
        return None
    if (
        residency_applies
        and lifecycle_residency_decision == "pause_lifecycle_residency"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        residency_applies
        and lifecycle_residency_decision == "buffer_lifecycle_residency"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_residency_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_residency_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_residency_buffered"
                )
        else:
            schedule_reason = "lifecycle_residency_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        residency_applies
        and lifecycle_residency_decision == "keep_lifecycle_residency"
    ):
        skip_lifecycle_dispatch_override = True
    standing_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and not longevity_applies
        and not durability_applies
        and not persistence_applies
        and not tenure_applies
        and not residency_applies
        and (
            lifecycle_standing_decision in {
                "archive_lifecycle_standing",
                "retire_lifecycle_standing",
            }
            or lifecycle_standing_stage_label == current_stage_label
        )
    )
    if standing_applies and lifecycle_standing_decision in {
        "archive_lifecycle_standing",
        "retire_lifecycle_standing",
    }:
        return None
    if standing_applies and lifecycle_standing_decision == "pause_lifecycle_standing":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif standing_applies and lifecycle_standing_decision == "buffer_lifecycle_standing":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_standing_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_standing_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_standing_buffered"
        else:
            schedule_reason = "lifecycle_standing_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif standing_applies and lifecycle_standing_decision == "keep_lifecycle_standing":
        skip_lifecycle_dispatch_override = True
    disposition_applies = (
        not foundation_applies
        and
        not root_applies
        and not origin_applies
        and not provenance_applies
        and not ancestry_applies
        and not lineage_applies
        and not heritage_applies
        and not legacy_applies
        and not longevity_applies
        and not durability_applies
        and not persistence_applies
        and not tenure_applies
        and not residency_applies
        and not standing_applies
        and (
            lifecycle_disposition_decision in {
                "archive_lifecycle_disposition",
                "retire_lifecycle_disposition",
            }
            or lifecycle_disposition_stage_label == current_stage_label
        )
    )
    if disposition_applies and lifecycle_disposition_decision in {
        "archive_lifecycle_disposition",
        "retire_lifecycle_disposition",
    }:
        return None
    if (
        disposition_applies
        and lifecycle_disposition_decision == "pause_lifecycle_disposition"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        disposition_applies
        and lifecycle_disposition_decision == "buffer_lifecycle_disposition"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_disposition_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_disposition_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_disposition_buffered"
                )
        else:
            schedule_reason = "lifecycle_disposition_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        disposition_applies
        and lifecycle_disposition_decision == "complete_lifecycle_disposition"
    ):
        skip_lifecycle_dispatch_override = True
    conclusion_applies = (
        not disposition_applies
        and (
            lifecycle_conclusion_decision in {
                "archive_lifecycle_conclusion",
                "retire_lifecycle_conclusion",
            }
            or lifecycle_conclusion_stage_label == current_stage_label
        )
    )
    if conclusion_applies and lifecycle_conclusion_decision in {
        "archive_lifecycle_conclusion",
        "retire_lifecycle_conclusion",
    }:
        return None
    if (
        conclusion_applies
        and lifecycle_conclusion_decision == "pause_lifecycle_conclusion"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        conclusion_applies
        and lifecycle_conclusion_decision == "buffer_lifecycle_conclusion"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_conclusion_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_conclusion_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_conclusion_buffered"
                )
        else:
            schedule_reason = "lifecycle_conclusion_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        conclusion_applies
        and lifecycle_conclusion_decision == "complete_lifecycle_conclusion"
    ):
        skip_lifecycle_dispatch_override = True
    completion_applies = (
        not conclusion_applies
        and (
            lifecycle_completion_decision in {
                "archive_lifecycle_completion",
                "retire_lifecycle_completion",
            }
            or lifecycle_completion_stage_label == current_stage_label
        )
    )
    if completion_applies and lifecycle_completion_decision in {
        "archive_lifecycle_completion",
        "retire_lifecycle_completion",
    }:
        return None
    if (
        completion_applies
        and lifecycle_completion_decision == "pause_lifecycle_completion"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        completion_applies
        and lifecycle_completion_decision == "buffer_lifecycle_completion"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_completion_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_completion_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_completion_buffered"
                )
        else:
            schedule_reason = "lifecycle_completion_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        completion_applies
        and lifecycle_completion_decision == "complete_lifecycle_completion"
    ):
        skip_lifecycle_dispatch_override = True
    finality_applies = (
        not completion_applies
        and (
        lifecycle_finality_decision in {
            "archive_lifecycle_finality",
            "retire_lifecycle_finality",
        }
        or lifecycle_finality_stage_label == current_stage_label
        )
    )
    if finality_applies and lifecycle_finality_decision in {
        "archive_lifecycle_finality",
        "retire_lifecycle_finality",
    }:
        return None
    if (
        finality_applies
        and lifecycle_finality_decision == "pause_lifecycle_finality"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        finality_applies
        and lifecycle_finality_decision == "buffer_lifecycle_finality"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_finality_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_finality_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_finality_buffered"
                )
        else:
            schedule_reason = "lifecycle_finality_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        finality_applies
        and lifecycle_finality_decision == "finalize_lifecycle_finality"
    ):
        skip_lifecycle_dispatch_override = True
    enactment_applies = (
        (not finality_applies)
        and (
        lifecycle_enactment_decision in {
            "archive_lifecycle_enactment",
            "retire_lifecycle_enactment",
        }
        or lifecycle_enactment_stage_label == current_stage_label
        )
    )
    if enactment_applies and lifecycle_enactment_decision in {
        "archive_lifecycle_enactment",
        "retire_lifecycle_enactment",
    }:
        return None
    if (
        enactment_applies
        and lifecycle_enactment_decision == "pause_lifecycle_enactment"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        enactment_applies
        and lifecycle_enactment_decision == "buffer_lifecycle_enactment"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_enactment_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_enactment_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_enactment_buffered"
                )
        else:
            schedule_reason = "lifecycle_enactment_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        enactment_applies
        and lifecycle_enactment_decision == "enact_lifecycle_enactment"
    ):
        skip_lifecycle_dispatch_override = True
    # Authorization is observable across the lifecycle stack, but it does
    # not become a non-terminal queue override until we have stronger
    # semantics than the existing endorsement/progression flow.
    authorization_applies = (
        not enactment_applies
        and lifecycle_authorization_decision in {
            "archive_lifecycle_authorization",
            "retire_lifecycle_authorization",
        }
    )
    if authorization_applies and lifecycle_authorization_decision in {
        "archive_lifecycle_authorization",
        "retire_lifecycle_authorization",
    }:
        return None
    endorsement_applies = (
        not authorization_applies
        and (
            lifecycle_endorsement_decision in {
                "archive_lifecycle_endorsement",
                "retire_lifecycle_endorsement",
            }
            or lifecycle_endorsement_stage_label == current_stage_label
        )
    )
    if endorsement_applies and lifecycle_endorsement_decision in {
        "archive_lifecycle_endorsement",
        "retire_lifecycle_endorsement",
    }:
        return None
    if (
        endorsement_applies
        and lifecycle_endorsement_decision == "pause_lifecycle_endorsement"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        endorsement_applies
        and lifecycle_endorsement_decision == "buffer_lifecycle_endorsement"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_endorsement_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_endorsement_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_endorsement_buffered"
                )
        else:
            schedule_reason = "lifecycle_endorsement_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        endorsement_applies
        and lifecycle_endorsement_decision == "endorse_lifecycle_endorsement"
    ):
        skip_lifecycle_dispatch_override = True
    ratification_applies = (
        not endorsement_applies
        and (
            lifecycle_ratification_decision in {
                "archive_lifecycle_ratification",
                "retire_lifecycle_ratification",
            }
            or lifecycle_ratification_stage_label == current_stage_label
        )
    )
    if ratification_applies and lifecycle_ratification_decision in {
        "archive_lifecycle_ratification",
        "retire_lifecycle_ratification",
    }:
        return None
    if (
        ratification_applies
        and lifecycle_ratification_decision == "pause_lifecycle_ratification"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        ratification_applies
        and lifecycle_ratification_decision == "buffer_lifecycle_ratification"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_ratification_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_ratification_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_ratification_buffered"
                )
        else:
            schedule_reason = "lifecycle_ratification_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        ratification_applies
        and lifecycle_ratification_decision == "ratify_lifecycle_ratification"
    ):
        skip_lifecycle_dispatch_override = True
    confirmation_applies = (
        not ratification_applies
        and (
            lifecycle_confirmation_decision in {
                "archive_lifecycle_confirmation",
                "retire_lifecycle_confirmation",
            }
            or lifecycle_confirmation_stage_label == current_stage_label
        )
    )
    if confirmation_applies and lifecycle_confirmation_decision in {
        "archive_lifecycle_confirmation",
        "retire_lifecycle_confirmation",
    }:
        return None
    if (
        confirmation_applies
        and lifecycle_confirmation_decision == "pause_lifecycle_confirmation"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        confirmation_applies
        and lifecycle_confirmation_decision == "buffer_lifecycle_confirmation"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_confirmation_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_confirmation_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_confirmation_buffered"
                )
        else:
            schedule_reason = "lifecycle_confirmation_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        confirmation_applies
        and lifecycle_confirmation_decision == "confirm_lifecycle_confirmation"
    ):
        skip_lifecycle_dispatch_override = True
    certification_applies = (
        not confirmation_applies
        and (
            lifecycle_certification_decision in {
                "archive_lifecycle_certification",
                "retire_lifecycle_certification",
            }
            or lifecycle_certification_stage_label == current_stage_label
        )
    )
    if certification_applies and lifecycle_certification_decision in {
        "archive_lifecycle_certification",
        "retire_lifecycle_certification",
    }:
        return None
    if (
        certification_applies
        and lifecycle_certification_decision == "pause_lifecycle_certification"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        certification_applies
        and lifecycle_certification_decision == "buffer_lifecycle_certification"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_certification_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_certification_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_certification_buffered"
                )
        else:
            schedule_reason = "lifecycle_certification_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        certification_applies
        and lifecycle_certification_decision == "certify_lifecycle_certification"
    ):
        skip_lifecycle_dispatch_override = True
    verification_applies = (
        not certification_applies
        and (
            lifecycle_verification_decision in {
                "archive_lifecycle_verification",
                "retire_lifecycle_verification",
            }
            or lifecycle_verification_stage_label == current_stage_label
        )
    )
    if verification_applies and lifecycle_verification_decision in {
        "archive_lifecycle_verification",
        "retire_lifecycle_verification",
    }:
        return None
    if (
        verification_applies
        and lifecycle_verification_decision == "pause_lifecycle_verification"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        verification_applies
        and lifecycle_verification_decision == "buffer_lifecycle_verification"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_verification_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_verification_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_verification_buffered"
                )
        else:
            schedule_reason = "lifecycle_verification_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        verification_applies
        and lifecycle_verification_decision == "verify_lifecycle_verification"
    ):
        skip_lifecycle_dispatch_override = True
    attestation_applies = (
        lifecycle_attestation_decision in {
            "archive_lifecycle_attestation",
            "retire_lifecycle_attestation",
        }
        or lifecycle_attestation_stage_label == current_stage_label
    )
    if attestation_applies and lifecycle_attestation_decision in {
        "archive_lifecycle_attestation",
        "retire_lifecycle_attestation",
    }:
        return None
    if (
        not verification_applies
        and attestation_applies
        and lifecycle_attestation_decision == "pause_lifecycle_attestation"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not verification_applies
        and attestation_applies
        and lifecycle_attestation_decision == "buffer_lifecycle_attestation"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_attestation_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_attestation_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_attestation_buffered"
                )
        else:
            schedule_reason = "lifecycle_attestation_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not verification_applies
        and attestation_applies
        and lifecycle_attestation_decision == "attest_lifecycle_attestation"
    ):
        skip_lifecycle_dispatch_override = True
    assurance_applies = (
        lifecycle_assurance_decision in {
            "archive_lifecycle_assurance",
            "retire_lifecycle_assurance",
        }
        or lifecycle_assurance_stage_label == current_stage_label
    )
    if assurance_applies and lifecycle_assurance_decision in {
        "archive_lifecycle_assurance",
        "retire_lifecycle_assurance",
    }:
        return None
    if (
        not attestation_applies
        and assurance_applies
        and lifecycle_assurance_decision == "pause_lifecycle_assurance"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not attestation_applies
        and assurance_applies
        and lifecycle_assurance_decision == "buffer_lifecycle_assurance"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_assurance_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_assurance_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_assurance_buffered"
                )
        else:
            schedule_reason = "lifecycle_assurance_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not attestation_applies
        and assurance_applies
        and lifecycle_assurance_decision == "assure_lifecycle_assurance"
    ):
        skip_lifecycle_dispatch_override = True
    oversight_applies = (
        lifecycle_oversight_decision in {
            "archive_lifecycle_oversight",
            "retire_lifecycle_oversight",
        }
        or lifecycle_oversight_stage_label == current_stage_label
    )
    if (
        not attestation_applies
        and not assurance_applies
        and oversight_applies
        and lifecycle_oversight_decision in {
        "archive_lifecycle_oversight",
        "retire_lifecycle_oversight",
    }
    ):
        return None
    if (
        not attestation_applies
        and not assurance_applies
        and
        oversight_applies
        and lifecycle_oversight_decision == "pause_lifecycle_oversight"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not attestation_applies
        and not assurance_applies
        and
        oversight_applies
        and lifecycle_oversight_decision == "buffer_lifecycle_oversight"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_oversight_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_oversight_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_oversight_buffered"
                )
        else:
            schedule_reason = "lifecycle_oversight_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not attestation_applies
        and not assurance_applies
        and
        oversight_applies
        and lifecycle_oversight_decision == "oversee_lifecycle_oversight"
    ):
        skip_lifecycle_dispatch_override = True
    guardianship_applies = (
        lifecycle_guardianship_decision in {
            "archive_lifecycle_guardianship",
            "retire_lifecycle_guardianship",
        }
        or lifecycle_guardianship_stage_label == current_stage_label
    )
    if (
        not assurance_applies
        and not oversight_applies
        and guardianship_applies
        and lifecycle_guardianship_decision in {
            "archive_lifecycle_guardianship",
            "retire_lifecycle_guardianship",
        }
    ):
        return None
    if (
        not assurance_applies
        and not oversight_applies
        and
        guardianship_applies
        and lifecycle_guardianship_decision == "pause_lifecycle_guardianship"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not assurance_applies
        and not oversight_applies
        and
        guardianship_applies
        and lifecycle_guardianship_decision == "buffer_lifecycle_guardianship"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_guardianship_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_guardianship_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_guardianship_buffered"
                )
        else:
            schedule_reason = "lifecycle_guardianship_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not assurance_applies
        and not oversight_applies
        and
        guardianship_applies
        and lifecycle_guardianship_decision == "guard_lifecycle_guardianship"
    ):
        skip_lifecycle_dispatch_override = True
    stewardship_applies = (
        lifecycle_stewardship_decision in {
            "archive_lifecycle_stewardship",
            "retire_lifecycle_stewardship",
        }
        or lifecycle_stewardship_stage_label == current_stage_label
    )
    if (
        not assurance_applies
        and not oversight_applies
        and not guardianship_applies
        and stewardship_applies
        and lifecycle_stewardship_decision in {
        "archive_lifecycle_stewardship",
        "retire_lifecycle_stewardship",
    }):
        return None
    if (
        not assurance_applies
        and not oversight_applies
        and not guardianship_applies
        and
        stewardship_applies
        and lifecycle_stewardship_decision == "pause_lifecycle_stewardship"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not assurance_applies
        and not oversight_applies
        and not guardianship_applies
        and
        stewardship_applies
        and lifecycle_stewardship_decision == "buffer_lifecycle_stewardship"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_stewardship_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_stewardship_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_stewardship_buffered"
                )
        else:
            schedule_reason = "lifecycle_stewardship_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not assurance_applies
        and not oversight_applies
        and not guardianship_applies
        and
        stewardship_applies
        and lifecycle_stewardship_decision == "steward_lifecycle_stewardship"
    ):
        skip_lifecycle_dispatch_override = True
    sustainment_applies = (
        lifecycle_sustainment_decision in {
            "archive_lifecycle_sustainment",
            "retire_lifecycle_sustainment",
        }
        or lifecycle_sustainment_stage_label == current_stage_label
    )
    if (
        not guardianship_applies
        and not stewardship_applies
        and sustainment_applies
        and lifecycle_sustainment_decision in {
            "archive_lifecycle_sustainment",
            "retire_lifecycle_sustainment",
        }
    ):
        return None
    if (
        not guardianship_applies
        and not stewardship_applies
        and
        sustainment_applies
        and lifecycle_sustainment_decision == "pause_lifecycle_sustainment"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not guardianship_applies
        and not stewardship_applies
        and
        sustainment_applies
        and lifecycle_sustainment_decision == "buffer_lifecycle_sustainment"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_sustainment_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_sustainment_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_sustainment_buffered"
                )
        else:
            schedule_reason = "lifecycle_sustainment_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not guardianship_applies
        and not stewardship_applies
        and
        sustainment_applies
        and lifecycle_sustainment_decision == "sustain_lifecycle_sustainment"
    ):
        skip_lifecycle_dispatch_override = True
    continuation_applies = (
        lifecycle_continuation_decision in {
            "archive_lifecycle_continuation",
            "retire_lifecycle_continuation",
        }
        or lifecycle_continuation_stage_label == current_stage_label
    )
    if (
        not sustainment_applies
        and continuation_applies
        and lifecycle_continuation_decision in {
            "archive_lifecycle_continuation",
            "retire_lifecycle_continuation",
        }
    ):
        return None
    if (
        not sustainment_applies
        and continuation_applies
        and lifecycle_continuation_decision == "pause_lifecycle_continuation"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not sustainment_applies
        and
        continuation_applies
        and lifecycle_continuation_decision == "buffer_lifecycle_continuation"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_continuation_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_continuation_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_continuation_buffered"
                )
        else:
            schedule_reason = "lifecycle_continuation_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not sustainment_applies
        and
        continuation_applies
        and lifecycle_continuation_decision == "keep_lifecycle_continuation"
    ):
        skip_lifecycle_dispatch_override = True
    handoff_applies = (
        not continuation_applies
        and (
            lifecycle_handoff_decision in {
            "archive_lifecycle_handoff",
            "retire_lifecycle_handoff",
        }
            or lifecycle_handoff_stage_label == current_stage_label
        )
    )
    if handoff_applies and lifecycle_handoff_decision in {
        "archive_lifecycle_handoff",
        "retire_lifecycle_handoff",
    }:
        return None
    if handoff_applies and lifecycle_handoff_decision == "pause_lifecycle_handoff":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        handoff_applies
        and lifecycle_handoff_decision == "buffer_lifecycle_handoff"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_handoff_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_handoff_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_handoff_buffered"
                )
        else:
            schedule_reason = "lifecycle_handoff_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif handoff_applies and lifecycle_handoff_decision == "keep_lifecycle_handoff":
        skip_lifecycle_dispatch_override = True
    launch_applies = (
        not handoff_applies
        and (
            lifecycle_launch_decision in {
            "archive_lifecycle_launch",
            "retire_lifecycle_launch",
        }
            or lifecycle_launch_stage_label == current_stage_label
        )
    )
    if launch_applies and lifecycle_launch_decision in {
        "archive_lifecycle_launch",
        "retire_lifecycle_launch",
    }:
        return None
    if launch_applies and lifecycle_launch_decision == "pause_lifecycle_launch":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif launch_applies and lifecycle_launch_decision == "buffer_lifecycle_launch":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_launch_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_launch_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_launch_buffered"
        else:
            schedule_reason = "lifecycle_launch_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif launch_applies and lifecycle_launch_decision == "keep_lifecycle_launch":
        skip_lifecycle_dispatch_override = True
    trigger_applies = (
        not launch_applies
        and (
            lifecycle_trigger_decision in {
                "archive_lifecycle_trigger",
                "retire_lifecycle_trigger",
            }
            or lifecycle_trigger_stage_label == current_stage_label
        )
    )
    if trigger_applies and lifecycle_trigger_decision in {
        "archive_lifecycle_trigger",
        "retire_lifecycle_trigger",
    }:
        return None
    if trigger_applies and lifecycle_trigger_decision == "pause_lifecycle_trigger":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif trigger_applies and lifecycle_trigger_decision == "buffer_lifecycle_trigger":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_trigger_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_trigger_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_trigger_buffered"
                )
        else:
            schedule_reason = "lifecycle_trigger_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif trigger_applies and lifecycle_trigger_decision == "keep_lifecycle_trigger":
        skip_lifecycle_dispatch_override = True
    arming_applies = (
        not trigger_applies
        and (
            lifecycle_arming_decision in {
                "archive_lifecycle_arming",
                "retire_lifecycle_arming",
            }
            or lifecycle_arming_stage_label == current_stage_label
        )
    )
    if arming_applies and lifecycle_arming_decision in {
        "archive_lifecycle_arming",
        "retire_lifecycle_arming",
    }:
        return None
    if arming_applies and lifecycle_arming_decision == "pause_lifecycle_arming":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif arming_applies and lifecycle_arming_decision == "buffer_lifecycle_arming":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_arming_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_arming_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_arming_buffered"
        else:
            schedule_reason = "lifecycle_arming_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif arming_applies and lifecycle_arming_decision == "keep_lifecycle_arming":
        skip_lifecycle_dispatch_override = True
    readiness_applies = (
        not arming_applies
        and (
            lifecycle_readiness_decision in {
                "archive_lifecycle_readiness",
                "retire_lifecycle_readiness",
            }
            or lifecycle_readiness_stage_label == current_stage_label
        )
    )
    if readiness_applies and lifecycle_readiness_decision in {
        "archive_lifecycle_readiness",
        "retire_lifecycle_readiness",
    }:
        return None
    if (
        readiness_applies
        and lifecycle_readiness_decision == "pause_lifecycle_readiness"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        readiness_applies
        and lifecycle_readiness_decision == "buffer_lifecycle_readiness"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_readiness_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_readiness_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_readiness_buffered"
                )
        else:
            schedule_reason = "lifecycle_readiness_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        readiness_applies
        and lifecycle_readiness_decision == "keep_lifecycle_readiness"
    ):
        skip_lifecycle_dispatch_override = True
    resumption_applies = (
        not readiness_applies
        and (
        lifecycle_resumption_decision in {
            "archive_lifecycle_resumption",
            "retire_lifecycle_resumption",
        }
        or lifecycle_resumption_stage_label == current_stage_label
        )
    )
    if resumption_applies and lifecycle_resumption_decision in {
        "archive_lifecycle_resumption",
        "retire_lifecycle_resumption",
    }:
        return None
    if (
        resumption_applies
        and lifecycle_resumption_decision == "pause_lifecycle_resumption"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        resumption_applies
        and lifecycle_resumption_decision == "buffer_lifecycle_resumption"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_resumption_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_resumption_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_resumption_buffered"
                )
        else:
            schedule_reason = "lifecycle_resumption_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        resumption_applies
        and lifecycle_resumption_decision == "keep_lifecycle_resumption"
    ):
        skip_lifecycle_dispatch_override = True
    reactivation_applies = (
        not resumption_applies
        and (
        lifecycle_reactivation_decision in {
            "archive_lifecycle_reactivation",
            "retire_lifecycle_reactivation",
        }
        or lifecycle_reactivation_stage_label == current_stage_label
        )
    )
    if reactivation_applies and lifecycle_reactivation_decision in {
        "archive_lifecycle_reactivation",
        "retire_lifecycle_reactivation",
    }:
        return None
    if (
        reactivation_applies
        and lifecycle_reactivation_decision == "pause_lifecycle_reactivation"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        reactivation_applies
        and lifecycle_reactivation_decision == "buffer_lifecycle_reactivation"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_reactivation_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_reactivation_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_reactivation_buffered"
                )
        else:
            schedule_reason = "lifecycle_reactivation_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        reactivation_applies
        and lifecycle_reactivation_decision == "keep_lifecycle_reactivation"
    ):
        skip_lifecycle_dispatch_override = True
    reentry_applies = (
        not reactivation_applies
        and (
            lifecycle_reentry_decision in {
                "archive_lifecycle_reentry",
                "retire_lifecycle_reentry",
            }
            or lifecycle_reentry_stage_label == current_stage_label
        )
    )
    if reentry_applies and lifecycle_reentry_decision in {
        "archive_lifecycle_reentry",
        "retire_lifecycle_reentry",
    }:
        return None
    if reentry_applies and lifecycle_reentry_decision == "pause_lifecycle_reentry":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif reentry_applies and lifecycle_reentry_decision == "buffer_lifecycle_reentry":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_reentry_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_reentry_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_reentry_buffered"
                )
        else:
            schedule_reason = "lifecycle_reentry_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif reentry_applies and lifecycle_reentry_decision == "keep_lifecycle_reentry":
        skip_lifecycle_dispatch_override = True
    selectability_applies = (
        not reentry_applies
        and (
            lifecycle_selectability_decision in {
                "archive_lifecycle_selectability",
                "retire_lifecycle_selectability",
            }
            or lifecycle_selectability_stage_label == current_stage_label
        )
    )
    if selectability_applies and lifecycle_selectability_decision in {
        "archive_lifecycle_selectability",
        "retire_lifecycle_selectability",
    }:
        return None
    if (
        selectability_applies
        and lifecycle_selectability_decision == "pause_lifecycle_selectability"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        selectability_applies
        and lifecycle_selectability_decision == "buffer_lifecycle_selectability"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(
                seconds=lifecycle_selectability_delay_seconds
            )
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_selectability_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_selectability_buffered"
                )
        else:
            schedule_reason = "lifecycle_selectability_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        selectability_applies
        and lifecycle_selectability_decision == "keep_lifecycle_selectable"
    ):
        skip_lifecycle_dispatch_override = True
    candidate_applies = (
        not selectability_applies
        and (
        lifecycle_candidate_decision in {
            "archive_lifecycle_candidate",
            "retire_lifecycle_candidate",
        }
        or lifecycle_candidate_stage_label == current_stage_label
        )
    )
    if candidate_applies and lifecycle_candidate_decision in {
        "archive_lifecycle_candidate",
        "retire_lifecycle_candidate",
    }:
        return None
    if candidate_applies and lifecycle_candidate_decision == "pause_lifecycle_candidate":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        candidate_applies
        and lifecycle_candidate_decision == "buffer_lifecycle_candidate"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_candidate_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_candidate_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_candidate_buffered"
                )
        else:
            schedule_reason = "lifecycle_candidate_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        candidate_applies
        and lifecycle_candidate_decision == "keep_lifecycle_candidate"
    ):
        skip_lifecycle_dispatch_override = True
    eligibility_applies = (
        not candidate_applies
        and (
        lifecycle_eligibility_decision in {
            "archive_lifecycle_eligibility",
            "retire_lifecycle_eligibility",
        }
        or lifecycle_eligibility_stage_label == current_stage_label
        )
    )
    if eligibility_applies and lifecycle_eligibility_decision in {
        "archive_lifecycle_eligibility",
        "retire_lifecycle_eligibility",
    }:
        return None
    if (
        eligibility_applies
        and lifecycle_eligibility_decision == "pause_lifecycle_eligibility"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        eligibility_applies
        and lifecycle_eligibility_decision == "buffer_lifecycle_eligibility"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_eligibility_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_eligibility_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_eligibility_buffered"
                )
        else:
            schedule_reason = "lifecycle_eligibility_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        eligibility_applies
        and lifecycle_eligibility_decision == "keep_lifecycle_eligible"
    ):
        skip_lifecycle_dispatch_override = True
    retention_applies = (
        not eligibility_applies
        and (
        lifecycle_retention_decision in {
            "archive_lifecycle_retention",
            "retire_lifecycle_retention",
        }
        or lifecycle_retention_stage_label == current_stage_label
        )
    )
    if retention_applies and lifecycle_retention_decision in {
        "archive_lifecycle_retention",
        "retire_lifecycle_retention",
    }:
        return None
    if (
        retention_applies
        and lifecycle_retention_decision == "pause_lifecycle_retention"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        retention_applies
        and lifecycle_retention_decision == "buffer_lifecycle_retention"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_retention_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_retention_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_retention_buffered"
                )
        else:
            schedule_reason = "lifecycle_retention_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        retention_applies
        and lifecycle_retention_decision == "retain_lifecycle_retention"
    ):
        skip_lifecycle_dispatch_override = True
    availability_applies = (
        not retention_applies
        and (
        lifecycle_availability_decision in {
            "close_loop_lifecycle_availability",
            "retire_lifecycle_availability",
        }
        or lifecycle_availability_stage_label == current_stage_label
        )
    )
    if availability_applies and lifecycle_availability_decision in {
        "close_loop_lifecycle_availability",
        "retire_lifecycle_availability",
    }:
        return None
    if (
        availability_applies
        and lifecycle_availability_decision == "pause_lifecycle_availability"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        availability_applies
        and lifecycle_availability_decision == "buffer_lifecycle_availability"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_availability_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_availability_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_availability_buffered"
                )
        else:
            schedule_reason = "lifecycle_availability_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        availability_applies
        and lifecycle_availability_decision == "keep_lifecycle_available"
    ):
        skip_lifecycle_dispatch_override = True
    closure_applies = (
        not availability_applies
        and (
        lifecycle_closure_decision in {
            "close_loop_lifecycle_closure",
            "retire_lifecycle_closure",
        }
        or lifecycle_closure_stage_label == current_stage_label
        )
    )
    if closure_applies and lifecycle_closure_decision in {
        "close_loop_lifecycle_closure",
        "retire_lifecycle_closure",
    }:
        return None
    if closure_applies and lifecycle_closure_decision == "pause_lifecycle_closure":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif closure_applies and lifecycle_closure_decision == "buffer_lifecycle_closure":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_closure_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_closure_buffered" not in schedule_reason:
                schedule_reason = f"{schedule_reason} | lifecycle_closure_buffered"
        else:
            schedule_reason = "lifecycle_closure_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif closure_applies and lifecycle_closure_decision == "keep_open_lifecycle_closure":
        skip_lifecycle_dispatch_override = True
    settlement_applies = (
        not closure_applies
        and (
        lifecycle_settlement_decision in {
            "close_lifecycle_settlement",
            "retire_lifecycle_settlement",
        }
        or lifecycle_settlement_stage_label == current_stage_label
        )
    )
    if settlement_applies and lifecycle_settlement_decision in {
        "close_lifecycle_settlement",
        "retire_lifecycle_settlement",
    }:
        return None
    if settlement_applies and lifecycle_settlement_decision == "hold_lifecycle_settlement":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        settlement_applies
        and lifecycle_settlement_decision == "buffer_lifecycle_settlement"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_settlement_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_settlement_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_settlement_buffered"
                )
        else:
            schedule_reason = "lifecycle_settlement_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        settlement_applies
        and lifecycle_settlement_decision == "keep_lifecycle_active"
    ):
        skip_lifecycle_dispatch_override = True
    activation_applies = (
        not settlement_applies
        and (
            lifecycle_activation_decision == "retire_lifecycle_line"
            or lifecycle_activation_stage_label == current_stage_label
        )
    )
    if activation_applies and lifecycle_activation_decision == "retire_lifecycle_line":
        return None
    if activation_applies and lifecycle_activation_decision == "hold_current_lifecycle_stage":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        activation_applies
        and lifecycle_activation_decision == "buffer_current_lifecycle_stage"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_activation_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_activation_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_activation_buffered"
                )
        else:
            schedule_reason = "lifecycle_activation_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        activation_applies
        and lifecycle_activation_decision == "activate_next_lifecycle_stage"
    ):
        skip_lifecycle_dispatch_override = True
    resolution_applies = (
        not settlement_applies
        and (
            lifecycle_resolution_decision == "retire_lifecycle_resolution"
            or lifecycle_resolution_stage_label == current_stage_label
        )
    )
    if (
        not activation_applies
        and resolution_applies
        and lifecycle_resolution_decision == "retire_lifecycle_resolution"
    ):
        return None
    if (
        not activation_applies
        and resolution_applies
        and lifecycle_resolution_decision == "hold_lifecycle_resolution"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
        skip_lifecycle_dispatch_override = True
    elif (
        not activation_applies
        and resolution_applies
        and lifecycle_resolution_decision == "buffer_lifecycle_resolution"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_resolution_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
        if schedule_reason:
            if "lifecycle_resolution_buffered" not in schedule_reason:
                schedule_reason = (
                    f"{schedule_reason} | lifecycle_resolution_buffered"
                )
        else:
            schedule_reason = "lifecycle_resolution_buffered"
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"scheduled", "waiting"}:
            queue_status = "scheduled"
        skip_lifecycle_dispatch_override = True
    elif (
        not activation_applies
        and resolution_applies
        and lifecycle_resolution_decision == "continue_lifecycle_resolution"
    ):
        skip_lifecycle_dispatch_override = True
    lifecycle_dispatch_decision = str(
        projected_lifecycle_dispatch.get("decision") or ""
    )
    lifecycle_dispatch_stage_label = str(
        projected_lifecycle_dispatch.get("current_stage_label") or ""
    )
    lifecycle_dispatch_delay_seconds = max(
        0,
        int(projected_lifecycle_dispatch.get("additional_delay_seconds") or 0),
    )
    dispatch_applies = (
        not skip_lifecycle_dispatch_override
        and lifecycle_dispatch_stage_label == current_stage_label
    )
    if (
        dispatch_applies
        and lifecycle_dispatch_decision == "retire_lifecycle_dispatch"
    ):
        return None
    if (
        dispatch_applies
        and lifecycle_dispatch_decision == "hold_lifecycle_dispatch"
    ):
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
    elif (
        dispatch_applies
        and lifecycle_dispatch_decision == "reschedule_lifecycle_dispatch"
    ):
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_dispatch_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
            if schedule_reason:
                if "lifecycle_dispatch_rescheduled" not in schedule_reason:
                    schedule_reason = (
                        f"{schedule_reason} | lifecycle_dispatch_rescheduled"
                    )
            else:
                schedule_reason = "lifecycle_dispatch_rescheduled"
            (
                queue_status,
                seconds_until_due,
                seconds_overdue,
                window_remaining_seconds,
            ) = _resolve_queue_status(
                reference_time=reference_time,
                base_due_at=base_due_at,
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
            )
        else:
            queue_status = "scheduled"
    elif dispatch_applies and lifecycle_dispatch_decision in {
        "dispatch_lifecycle_now",
        "close_loop_lifecycle_dispatch",
    }:
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"due", "overdue"}:
            queue_status = (
                "overdue"
                if str(projected_lifecycle_queue.get("queue_status") or "") == "overdue"
                else "due"
            )
    if (
        projected_stage_state.get("stage_label") == current_stage_label
        and projected_stage_state.get("queue_status") == queue_status
    ):
        proactive_stage_state = projected_stage_state
    else:
        matching_envelope = (
            projected_dispatch_envelope
            if projected_dispatch_envelope.get("stage_label") == current_stage_label
            else {}
        )
        proactive_stage_state = asdict(
            build_proactive_stage_state_decision(
                stage_label=current_stage_label,
                stage_index=current_stage_index,
                stage_count=max_dispatch_count,
                queue_status=queue_status,
                schedule_reason=schedule_reason,
                progression_action=str(
                    (current_stage_progression or {}).get("on_expired") or "none"
                ),
                progression_advanced=progression_advanced,
                line_state=str(
                    dict(
                        latest_proactive_line_controller_event.payload
                        if latest_proactive_line_controller_event is not None
                        else {}
                    ).get("line_state")
                    or "steady"
                ),
                current_stage_delivery_mode=str(
                    (current_stage_directive or {}).get("delivery_mode")
                    or "single_message"
                ),
                current_stage_autonomy_mode=str(
                    (current_stage_directive or {}).get("autonomy_mode")
                    or "light_invitation"
                ),
                current_reengagement_delivery_mode=str(
                    reengagement_plan.get("delivery_mode") or "single_message"
                ),
                selected_strategy_key=str(
                    matching_envelope.get("selected_strategy_key")
                    or reengagement_plan.get("strategy_key")
                    or "none"
                ),
                selected_pressure_mode=str(
                    matching_envelope.get("selected_pressure_mode")
                    or reengagement_plan.get("pressure_mode")
                    or "none"
                ),
                selected_autonomy_signal=str(
                    matching_envelope.get("selected_autonomy_signal")
                    or reengagement_plan.get("autonomy_signal")
                    or "none"
                ),
                dispatch_envelope_key=matching_envelope.get("envelope_key"),
                dispatch_envelope_decision=matching_envelope.get("decision"),
                dispatch_gate_decision=str(
                    dict(
                        latest_proactive_dispatch_gate_event.payload
                        if latest_proactive_dispatch_gate_event is not None
                        else {}
                    ).get("decision")
                    or ""
                ),
                aggregate_controller_decision=str(
                    dict(state.get("proactive_aggregate_controller_decision") or {}).get(
                        "decision"
                    )
                    or ""
                ),
                orchestration_controller_decision=str(
                    dict(
                        state.get("proactive_orchestration_controller_decision") or {}
                    ).get("decision")
                    or ""
                ),
                stage_controller_decision=str(
                    dict(
                        latest_proactive_stage_controller_event.payload
                        if latest_proactive_stage_controller_event is not None
                        else {}
                    ).get("decision")
                    or ""
                ),
                line_controller_decision=str(
                    dict(
                        latest_proactive_line_controller_event.payload
                        if latest_proactive_line_controller_event is not None
                        else {}
                    ).get("decision")
                    or ""
                ),
            )
        )

    return {
        "session_id": session_id,
        "session_source": session_source,
        "queue_status": queue_status,
        "directive_status": directive_status,
        "style": directive.get("style"),
        "eligible": bool(directive.get("eligible")),
        "guidance_mode": guidance_plan.get("mode"),
        "guidance_pacing": guidance_plan.get("pacing"),
        "guidance_agency_mode": guidance_plan.get("agency_mode"),
        "guidance_ritual_action": guidance_plan.get("ritual_action"),
        "guidance_handoff_mode": guidance_plan.get("handoff_mode"),
        "guidance_carryover_mode": guidance_plan.get("carryover_mode"),
        "cadence_status": conversation_cadence_plan.get("status"),
        "cadence_turn_shape": conversation_cadence_plan.get("turn_shape"),
        "cadence_followup_tempo": conversation_cadence_plan.get("followup_tempo"),
        "cadence_user_space_mode": conversation_cadence_plan.get(
            "user_space_mode"
        ),
        "cadence_transition_intent": conversation_cadence_plan.get(
            "transition_intent"
        ),
        "cadence_next_checkpoint": conversation_cadence_plan.get(
            "next_checkpoint"
        ),
        "ritual_phase": session_ritual_plan.get("phase"),
        "ritual_opening_move": session_ritual_plan.get("opening_move"),
        "ritual_bridge_move": session_ritual_plan.get("bridge_move"),
        "ritual_closing_move": session_ritual_plan.get("closing_move"),
        "ritual_continuity_anchor": session_ritual_plan.get("continuity_anchor"),
        "ritual_somatic_shortcut": session_ritual_plan.get("somatic_shortcut"),
        "somatic_orchestration_status": somatic_orchestration_plan.get("status"),
        "somatic_orchestration_mode": somatic_orchestration_plan.get("primary_mode"),
        "somatic_orchestration_body_anchor": somatic_orchestration_plan.get(
            "body_anchor"
        ),
        "somatic_orchestration_followup_style": somatic_orchestration_plan.get(
            "followup_style"
        ),
        "somatic_orchestration_allow_in_followup": (
            somatic_orchestration_plan.get("allow_in_followup")
        ),
        "reengagement_matrix_key": reengagement_matrix_assessment.get("matrix_key"),
        "reengagement_matrix_selected_strategy": reengagement_matrix_assessment.get(
            "selected_strategy_key"
        ),
        "reengagement_matrix_selected_score": reengagement_matrix_assessment.get(
            "selected_score"
        ),
        "reengagement_matrix_blocked_count": int(
            reengagement_matrix_assessment.get("blocked_count") or 0
        ),
        "reengagement_matrix_learning_mode": reengagement_matrix_assessment.get(
            "learning_mode"
        ),
        "reengagement_matrix_learning_context_stratum": (
            reengagement_matrix_assessment.get("learning_context_stratum")
        ),
        "reengagement_matrix_learning_signal_count": int(
            reengagement_matrix_assessment.get("learning_signal_count") or 0
        ),
        "reengagement_matrix_selected_supporting_session_count": int(
            selected_matrix_candidate.get("supporting_session_count") or 0
        ),
        "reengagement_matrix_selected_contextual_supporting_session_count": int(
            selected_matrix_candidate.get("contextual_supporting_session_count") or 0
        ),
        "reengagement_ritual_mode": reengagement_plan.get("ritual_mode"),
        "reengagement_delivery_mode": reengagement_plan.get("delivery_mode"),
        "reengagement_strategy_key": reengagement_plan.get("strategy_key"),
        "reengagement_relational_move": reengagement_plan.get("relational_move"),
        "reengagement_pressure_mode": reengagement_plan.get("pressure_mode"),
        "reengagement_autonomy_signal": reengagement_plan.get("autonomy_signal"),
        "reengagement_sequence_objective": reengagement_plan.get(
            "sequence_objective"
        ),
        "reengagement_somatic_action": reengagement_plan.get("somatic_action"),
        "proactive_dispatch_gate_key": (
            dict(
                latest_proactive_dispatch_gate_event.payload
                if latest_proactive_dispatch_gate_event is not None
                else {}
            ).get("gate_key")
        ),
        "proactive_dispatch_gate_decision": (
            dict(
                latest_proactive_dispatch_gate_event.payload
                if latest_proactive_dispatch_gate_event is not None
                else {}
            ).get("decision")
        ),
        "proactive_dispatch_gate_retry_after_seconds": int(
            dict(
                latest_proactive_dispatch_gate_event.payload
                if latest_proactive_dispatch_gate_event is not None
                else {}
            ).get("retry_after_seconds")
            or 0
        ),
        "proactive_dispatch_gate_strategy_key": (
            dict(
                latest_proactive_dispatch_gate_event.payload
                if latest_proactive_dispatch_gate_event is not None
                else {}
            ).get("selected_strategy_key")
        ),
        "proactive_dispatch_feedback_key": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("feedback_key")
        ),
        "proactive_dispatch_feedback_changed": bool(
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("changed")
        ),
        "proactive_dispatch_feedback_dispatch_count": int(
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("dispatch_count")
            or 0
        ),
        "proactive_dispatch_feedback_gate_defer_count": int(
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("gate_defer_count")
            or 0
        ),
        "proactive_dispatch_feedback_strategy_key": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("selected_strategy_key")
        ),
        "proactive_dispatch_feedback_pressure_mode": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("selected_pressure_mode")
        ),
        "proactive_dispatch_feedback_autonomy_signal": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("selected_autonomy_signal")
        ),
        "proactive_dispatch_feedback_delivery_mode": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("selected_delivery_mode")
        ),
        "proactive_dispatch_feedback_sequence_objective": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("selected_sequence_objective")
        ),
        "proactive_dispatch_feedback_prior_stage_label": (
            dict(
                latest_proactive_dispatch_feedback_event.payload
                if latest_proactive_dispatch_feedback_event is not None
                else {}
            ).get("prior_stage_label")
        ),
        "proactive_stage_state_key": proactive_stage_state.get("state_key"),
        "proactive_stage_state_mode": proactive_stage_state.get("state_mode"),
        "proactive_stage_state_source": proactive_stage_state.get("primary_source"),
        "proactive_stage_state_queue_status": proactive_stage_state.get(
            "queue_status"
        ),
        "proactive_stage_state_changed": bool(
            proactive_stage_state.get("changed")
        ),
        "proactive_stage_controller_key": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("controller_key")
        ),
        "proactive_stage_controller_decision": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("decision")
        ),
        "proactive_stage_controller_changed": bool(
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("changed")
        ),
        "proactive_stage_controller_target_stage_label": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("target_stage_label")
        ),
        "proactive_stage_controller_additional_delay_seconds": int(
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("additional_delay_seconds")
            or 0
        ),
        "proactive_stage_controller_strategy_key": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("selected_strategy_key")
        ),
        "proactive_stage_controller_pressure_mode": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("selected_pressure_mode")
        ),
        "proactive_stage_controller_autonomy_signal": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("selected_autonomy_signal")
        ),
        "proactive_stage_controller_delivery_mode": (
            dict(
                latest_proactive_stage_controller_event.payload
                if latest_proactive_stage_controller_event is not None
                else {}
            ).get("selected_delivery_mode")
        ),
        "proactive_line_controller_key": (
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("controller_key")
        ),
        "proactive_line_controller_line_state": (
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("line_state")
        ),
        "proactive_line_controller_decision": (
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("decision")
        ),
        "proactive_line_controller_changed": bool(
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("changed")
        ),
        "proactive_line_controller_affected_stage_labels": list(
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("affected_stage_labels")
            or []
        ),
        "proactive_line_controller_additional_delay_seconds": int(
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("additional_delay_seconds")
            or 0
        ),
        "proactive_line_controller_pressure_mode": (
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("selected_pressure_mode")
        ),
        "proactive_line_controller_autonomy_signal": (
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("selected_autonomy_signal")
        ),
        "proactive_line_controller_delivery_mode": (
            dict(
                latest_proactive_line_controller_event.payload
                if latest_proactive_line_controller_event is not None
                else {}
            ).get("selected_delivery_mode")
        ),
        "proactive_line_state_key": projected_line_state.get("line_key"),
        "proactive_line_state_mode": projected_line_state.get("line_state"),
        "proactive_line_state_lifecycle": projected_line_state.get(
            "lifecycle_mode"
        ),
        "proactive_line_state_actionability": projected_line_state.get(
            "actionability"
        ),
        "proactive_line_transition_key": projected_line_transition.get(
            "transition_key"
        ),
        "proactive_line_transition_mode": projected_line_transition.get(
            "transition_mode"
        ),
        "proactive_line_transition_exit_mode": projected_line_transition.get(
            "line_exit_mode"
        ),
        "proactive_line_machine_key": projected_line_machine.get("machine_key"),
        "proactive_line_machine_mode": projected_line_machine.get("machine_mode"),
        "proactive_line_machine_lifecycle": projected_line_machine.get(
            "lifecycle_mode"
        ),
        "proactive_line_machine_actionability": projected_line_machine.get(
            "actionability"
        ),
        "proactive_lifecycle_state_key": projected_lifecycle_state.get("state_key"),
        "proactive_lifecycle_state_mode": projected_lifecycle_state.get("state_mode"),
        "proactive_lifecycle_state_lifecycle": projected_lifecycle_state.get(
            "lifecycle_mode"
        ),
        "proactive_lifecycle_state_actionability": projected_lifecycle_state.get(
            "actionability"
        ),
        "proactive_lifecycle_transition_key": projected_lifecycle_transition.get(
            "transition_key"
        ),
        "proactive_lifecycle_transition_mode": projected_lifecycle_transition.get(
            "transition_mode"
        ),
        "proactive_lifecycle_transition_exit_mode": projected_lifecycle_transition.get(
            "lifecycle_exit_mode"
        ),
        "proactive_lifecycle_machine_key": projected_lifecycle_machine.get(
            "machine_key"
        ),
        "proactive_lifecycle_machine_mode": projected_lifecycle_machine.get(
            "machine_mode"
        ),
        "proactive_lifecycle_machine_lifecycle": projected_lifecycle_machine.get(
            "lifecycle_mode"
        ),
        "proactive_lifecycle_machine_actionability": projected_lifecycle_machine.get(
            "actionability"
        ),
        "proactive_lifecycle_controller_key": (
            dict(state.get("proactive_lifecycle_controller_decision") or {}).get(
                "controller_key"
            )
        ),
        "proactive_lifecycle_controller_state": (
            dict(state.get("proactive_lifecycle_controller_decision") or {}).get(
                "lifecycle_state"
            )
        ),
        "proactive_lifecycle_controller_decision": (
            dict(state.get("proactive_lifecycle_controller_decision") or {}).get(
                "decision"
            )
        ),
        "proactive_lifecycle_controller_delay_seconds": int(
            dict(state.get("proactive_lifecycle_controller_decision") or {}).get(
                "additional_delay_seconds"
            )
            or 0
        ),
        "proactive_lifecycle_envelope_key": projected_lifecycle_envelope.get(
            "envelope_key"
        ),
        "proactive_lifecycle_envelope_state": projected_lifecycle_envelope.get(
            "lifecycle_state"
        ),
        "proactive_lifecycle_envelope_mode": projected_lifecycle_envelope.get(
            "envelope_mode"
        ),
        "proactive_lifecycle_envelope_decision": projected_lifecycle_envelope.get(
            "decision"
        ),
        "proactive_lifecycle_envelope_actionability": projected_lifecycle_envelope.get(
            "actionability"
        ),
        "proactive_lifecycle_envelope_delay_seconds": int(
            projected_lifecycle_envelope.get("additional_delay_seconds") or 0
        ),
        "proactive_lifecycle_scheduler_key": projected_lifecycle_scheduler.get(
            "scheduler_key"
        ),
        "proactive_lifecycle_scheduler_state": projected_lifecycle_scheduler.get(
            "lifecycle_state"
        ),
        "proactive_lifecycle_scheduler_mode": projected_lifecycle_scheduler.get(
            "scheduler_mode"
        ),
        "proactive_lifecycle_scheduler_decision": projected_lifecycle_scheduler.get(
            "decision"
        ),
        "proactive_lifecycle_scheduler_actionability": projected_lifecycle_scheduler.get(
            "actionability"
        ),
        "proactive_lifecycle_scheduler_queue_status": projected_lifecycle_scheduler.get(
            "queue_status_hint"
        ),
        "proactive_lifecycle_scheduler_delay_seconds": int(
            projected_lifecycle_scheduler.get("additional_delay_seconds") or 0
        ),
        "proactive_lifecycle_window_key": projected_lifecycle_window.get(
            "window_key"
        ),
        "proactive_lifecycle_window_state": projected_lifecycle_window.get(
            "lifecycle_state"
        ),
        "proactive_lifecycle_window_mode": projected_lifecycle_window.get(
            "window_mode"
        ),
        "proactive_lifecycle_window_decision": projected_lifecycle_window.get(
            "decision"
        ),
        "proactive_lifecycle_window_queue_status": projected_lifecycle_window.get(
            "queue_status"
        ),
        "proactive_lifecycle_window_delay_seconds": int(
            projected_lifecycle_window.get("additional_delay_seconds") or 0
        ),
        "proactive_lifecycle_queue_key": projected_lifecycle_queue.get("queue_key"),
        "proactive_lifecycle_queue_state": projected_lifecycle_queue.get(
            "lifecycle_state"
        ),
        "proactive_lifecycle_queue_mode": projected_lifecycle_queue.get(
            "queue_mode"
        ),
        "proactive_lifecycle_queue_decision": projected_lifecycle_queue.get(
            "decision"
        ),
        "proactive_lifecycle_queue_status": projected_lifecycle_queue.get(
            "queue_status"
        ),
        "proactive_lifecycle_queue_delay_seconds": int(
            projected_lifecycle_queue.get("additional_delay_seconds") or 0
        ),
        "proactive_lifecycle_dispatch_key": projected_lifecycle_dispatch.get(
            "dispatch_key"
        ),
        "proactive_lifecycle_dispatch_state": projected_lifecycle_dispatch.get(
            "lifecycle_state"
        ),
        "proactive_lifecycle_dispatch_mode": projected_lifecycle_dispatch.get(
            "dispatch_mode"
        ),
        "proactive_lifecycle_dispatch_decision": projected_lifecycle_dispatch.get(
            "decision"
        ),
        "proactive_lifecycle_dispatch_actionability": projected_lifecycle_dispatch.get(
            "actionability"
        ),
        "proactive_lifecycle_dispatch_delay_seconds": int(
            projected_lifecycle_dispatch.get("additional_delay_seconds") or 0
        ),
        "proactive_lifecycle_outcome_key": projected_lifecycle_outcome.get(
            "outcome_key"
        ),
        "proactive_lifecycle_outcome_status": projected_lifecycle_outcome.get(
            "status"
        ),
        "proactive_lifecycle_outcome_mode": projected_lifecycle_outcome.get(
            "outcome_mode"
        ),
        "proactive_lifecycle_outcome_decision": projected_lifecycle_outcome.get(
            "decision"
        ),
        "proactive_lifecycle_outcome_actionability": projected_lifecycle_outcome.get(
            "actionability"
        ),
        "proactive_lifecycle_outcome_message_event_count": int(
            projected_lifecycle_outcome.get("message_event_count") or 0
        ),
        "proactive_lifecycle_resolution_key": projected_lifecycle_resolution.get(
            "resolution_key"
        ),
        "proactive_lifecycle_resolution_status": projected_lifecycle_resolution.get(
            "status"
        ),
        "proactive_lifecycle_resolution_mode": projected_lifecycle_resolution.get(
            "resolution_mode"
        ),
        "proactive_lifecycle_resolution_decision": projected_lifecycle_resolution.get(
            "decision"
        ),
        "proactive_lifecycle_resolution_actionability": projected_lifecycle_resolution.get(
            "actionability"
        ),
        "proactive_lifecycle_resolution_queue_override_status": (
            projected_lifecycle_resolution.get("queue_override_status")
        ),
        "proactive_lifecycle_resolution_remaining_stage_count": int(
            projected_lifecycle_resolution.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_activation_key": projected_lifecycle_activation.get(
            "activation_key"
        ),
        "proactive_lifecycle_activation_status": projected_lifecycle_activation.get(
            "status"
        ),
        "proactive_lifecycle_activation_mode": projected_lifecycle_activation.get(
            "activation_mode"
        ),
        "proactive_lifecycle_activation_decision": projected_lifecycle_activation.get(
            "decision"
        ),
        "proactive_lifecycle_activation_actionability": projected_lifecycle_activation.get(
            "actionability"
        ),
        "proactive_lifecycle_activation_active_stage_label": projected_lifecycle_activation.get(
            "active_stage_label"
        ),
        "proactive_lifecycle_activation_queue_override_status": (
            projected_lifecycle_activation.get("queue_override_status")
        ),
        "proactive_lifecycle_activation_remaining_stage_count": int(
            projected_lifecycle_activation.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_settlement_key": projected_lifecycle_settlement.get(
            "settlement_key"
        ),
        "proactive_lifecycle_settlement_status": projected_lifecycle_settlement.get(
            "status"
        ),
        "proactive_lifecycle_settlement_mode": projected_lifecycle_settlement.get(
            "settlement_mode"
        ),
        "proactive_lifecycle_settlement_decision": projected_lifecycle_settlement.get(
            "decision"
        ),
        "proactive_lifecycle_settlement_actionability": projected_lifecycle_settlement.get(
            "actionability"
        ),
        "proactive_lifecycle_settlement_active_stage_label": projected_lifecycle_settlement.get(
            "active_stage_label"
        ),
        "proactive_lifecycle_settlement_queue_override_status": (
            projected_lifecycle_settlement.get("queue_override_status")
        ),
        "proactive_lifecycle_settlement_remaining_stage_count": int(
            projected_lifecycle_settlement.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_closure_key": projected_lifecycle_closure.get(
            "closure_key"
        ),
        "proactive_lifecycle_closure_status": projected_lifecycle_closure.get(
            "status"
        ),
        "proactive_lifecycle_closure_mode": projected_lifecycle_closure.get(
            "closure_mode"
        ),
        "proactive_lifecycle_closure_decision": projected_lifecycle_closure.get(
            "decision"
        ),
        "proactive_lifecycle_closure_actionability": (
            projected_lifecycle_closure.get("actionability")
        ),
        "proactive_lifecycle_closure_active_stage_label": (
            projected_lifecycle_closure.get("active_stage_label")
        ),
        "proactive_lifecycle_closure_queue_override_status": (
            projected_lifecycle_closure.get("queue_override_status")
        ),
        "proactive_lifecycle_closure_remaining_stage_count": int(
            projected_lifecycle_closure.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_availability_key": projected_lifecycle_availability.get(
            "availability_key"
        ),
        "proactive_lifecycle_availability_status": projected_lifecycle_availability.get(
            "status"
        ),
        "proactive_lifecycle_availability_mode": projected_lifecycle_availability.get(
            "availability_mode"
        ),
        "proactive_lifecycle_availability_decision": projected_lifecycle_availability.get(
            "decision"
        ),
        "proactive_lifecycle_availability_actionability": (
            projected_lifecycle_availability.get("actionability")
        ),
        "proactive_lifecycle_availability_active_stage_label": (
            projected_lifecycle_availability.get("active_stage_label")
        ),
        "proactive_lifecycle_availability_queue_override_status": (
            projected_lifecycle_availability.get("queue_override_status")
        ),
        "proactive_lifecycle_availability_remaining_stage_count": int(
            projected_lifecycle_availability.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_retention_key": projected_lifecycle_retention.get(
            "retention_key"
        ),
        "proactive_lifecycle_retention_status": projected_lifecycle_retention.get(
            "status"
        ),
        "proactive_lifecycle_retention_mode": projected_lifecycle_retention.get(
            "retention_mode"
        ),
        "proactive_lifecycle_retention_decision": projected_lifecycle_retention.get(
            "decision"
        ),
        "proactive_lifecycle_retention_actionability": (
            projected_lifecycle_retention.get("actionability")
        ),
        "proactive_lifecycle_retention_active_stage_label": (
            projected_lifecycle_retention.get("active_stage_label")
        ),
        "proactive_lifecycle_retention_queue_override_status": (
            projected_lifecycle_retention.get("queue_override_status")
        ),
        "proactive_lifecycle_retention_remaining_stage_count": int(
            projected_lifecycle_retention.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_eligibility_key": projected_lifecycle_eligibility.get(
            "eligibility_key"
        ),
        "proactive_lifecycle_eligibility_status": projected_lifecycle_eligibility.get(
            "status"
        ),
        "proactive_lifecycle_eligibility_mode": projected_lifecycle_eligibility.get(
            "eligibility_mode"
        ),
        "proactive_lifecycle_eligibility_decision": projected_lifecycle_eligibility.get(
            "decision"
        ),
        "proactive_lifecycle_eligibility_actionability": (
            projected_lifecycle_eligibility.get("actionability")
        ),
        "proactive_lifecycle_eligibility_active_stage_label": (
            projected_lifecycle_eligibility.get("active_stage_label")
        ),
        "proactive_lifecycle_eligibility_queue_override_status": (
            projected_lifecycle_eligibility.get("queue_override_status")
        ),
        "proactive_lifecycle_eligibility_remaining_stage_count": int(
            projected_lifecycle_eligibility.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_candidate_key": projected_lifecycle_candidate.get(
            "candidate_key"
        ),
        "proactive_lifecycle_candidate_status": projected_lifecycle_candidate.get(
            "status"
        ),
        "proactive_lifecycle_candidate_mode": projected_lifecycle_candidate.get(
            "candidate_mode"
        ),
        "proactive_lifecycle_candidate_decision": projected_lifecycle_candidate.get(
            "decision"
        ),
        "proactive_lifecycle_candidate_actionability": (
            projected_lifecycle_candidate.get("actionability")
        ),
        "proactive_lifecycle_candidate_active_stage_label": (
            projected_lifecycle_candidate.get("active_stage_label")
        ),
        "proactive_lifecycle_candidate_queue_override_status": (
            projected_lifecycle_candidate.get("queue_override_status")
        ),
        "proactive_lifecycle_candidate_remaining_stage_count": int(
            projected_lifecycle_candidate.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_selectability_key": (
            projected_lifecycle_selectability.get("selectability_key")
        ),
        "proactive_lifecycle_selectability_status": (
            projected_lifecycle_selectability.get("status")
        ),
        "proactive_lifecycle_selectability_mode": (
            projected_lifecycle_selectability.get("selectability_mode")
        ),
        "proactive_lifecycle_selectability_decision": (
            projected_lifecycle_selectability.get("decision")
        ),
        "proactive_lifecycle_selectability_actionability": (
            projected_lifecycle_selectability.get("actionability")
        ),
        "proactive_lifecycle_selectability_active_stage_label": (
            projected_lifecycle_selectability.get("active_stage_label")
        ),
        "proactive_lifecycle_selectability_queue_override_status": (
            projected_lifecycle_selectability.get("queue_override_status")
        ),
        "proactive_lifecycle_selectability_remaining_stage_count": int(
            projected_lifecycle_selectability.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_reentry_key": (
            projected_lifecycle_reentry.get("reentry_key")
        ),
        "proactive_lifecycle_reentry_status": (
            projected_lifecycle_reentry.get("status")
        ),
        "proactive_lifecycle_reentry_mode": (
            projected_lifecycle_reentry.get("reentry_mode")
        ),
        "proactive_lifecycle_reentry_decision": (
            projected_lifecycle_reentry.get("decision")
        ),
        "proactive_lifecycle_reentry_actionability": (
            projected_lifecycle_reentry.get("actionability")
        ),
        "proactive_lifecycle_reentry_active_stage_label": (
            projected_lifecycle_reentry.get("active_stage_label")
        ),
        "proactive_lifecycle_reentry_queue_override_status": (
            projected_lifecycle_reentry.get("queue_override_status")
        ),
        "proactive_lifecycle_reentry_remaining_stage_count": int(
            projected_lifecycle_reentry.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_reactivation_key": (
            projected_lifecycle_reactivation.get("reactivation_key")
        ),
        "proactive_lifecycle_reactivation_status": (
            projected_lifecycle_reactivation.get("status")
        ),
        "proactive_lifecycle_reactivation_mode": (
            projected_lifecycle_reactivation.get("reactivation_mode")
        ),
        "proactive_lifecycle_reactivation_decision": (
            projected_lifecycle_reactivation.get("decision")
        ),
        "proactive_lifecycle_reactivation_actionability": (
            projected_lifecycle_reactivation.get("actionability")
        ),
        "proactive_lifecycle_reactivation_active_stage_label": (
            projected_lifecycle_reactivation.get("active_stage_label")
        ),
        "proactive_lifecycle_reactivation_queue_override_status": (
            projected_lifecycle_reactivation.get("queue_override_status")
        ),
        "proactive_lifecycle_reactivation_remaining_stage_count": int(
            projected_lifecycle_reactivation.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_resumption_key": (
            projected_lifecycle_resumption.get("resumption_key")
        ),
        "proactive_lifecycle_resumption_status": (
            projected_lifecycle_resumption.get("status")
        ),
        "proactive_lifecycle_resumption_mode": (
            projected_lifecycle_resumption.get("resumption_mode")
        ),
        "proactive_lifecycle_resumption_decision": (
            projected_lifecycle_resumption.get("decision")
        ),
        "proactive_lifecycle_resumption_actionability": (
            projected_lifecycle_resumption.get("actionability")
        ),
        "proactive_lifecycle_resumption_active_stage_label": (
            projected_lifecycle_resumption.get("active_stage_label")
        ),
        "proactive_lifecycle_resumption_queue_override_status": (
            projected_lifecycle_resumption.get("queue_override_status")
        ),
        "proactive_lifecycle_resumption_remaining_stage_count": int(
            projected_lifecycle_resumption.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_readiness_key": (
            projected_lifecycle_readiness.get("readiness_key")
        ),
        "proactive_lifecycle_readiness_status": (
            projected_lifecycle_readiness.get("status")
        ),
        "proactive_lifecycle_readiness_mode": (
            projected_lifecycle_readiness.get("readiness_mode")
        ),
        "proactive_lifecycle_readiness_decision": (
            projected_lifecycle_readiness.get("decision")
        ),
        "proactive_lifecycle_readiness_actionability": (
            projected_lifecycle_readiness.get("actionability")
        ),
        "proactive_lifecycle_readiness_active_stage_label": (
            projected_lifecycle_readiness.get("active_stage_label")
        ),
        "proactive_lifecycle_readiness_queue_override_status": (
            projected_lifecycle_readiness.get("queue_override_status")
        ),
        "proactive_lifecycle_readiness_remaining_stage_count": int(
            projected_lifecycle_readiness.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_arming_key": (
            projected_lifecycle_arming.get("arming_key")
        ),
        "proactive_lifecycle_arming_status": (
            projected_lifecycle_arming.get("status")
        ),
        "proactive_lifecycle_arming_mode": (
            projected_lifecycle_arming.get("arming_mode")
        ),
        "proactive_lifecycle_arming_decision": (
            projected_lifecycle_arming.get("decision")
        ),
        "proactive_lifecycle_arming_actionability": (
            projected_lifecycle_arming.get("actionability")
        ),
        "proactive_lifecycle_arming_active_stage_label": (
            projected_lifecycle_arming.get("active_stage_label")
        ),
        "proactive_lifecycle_arming_queue_override_status": (
            projected_lifecycle_arming.get("queue_override_status")
        ),
        "proactive_lifecycle_arming_remaining_stage_count": int(
            projected_lifecycle_arming.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_trigger_key": (
            projected_lifecycle_trigger.get("trigger_key")
        ),
        "proactive_lifecycle_trigger_status": (
            projected_lifecycle_trigger.get("status")
        ),
        "proactive_lifecycle_trigger_mode": (
            projected_lifecycle_trigger.get("trigger_mode")
        ),
        "proactive_lifecycle_trigger_decision": (
            projected_lifecycle_trigger.get("decision")
        ),
        "proactive_lifecycle_trigger_actionability": (
            projected_lifecycle_trigger.get("actionability")
        ),
        "proactive_lifecycle_trigger_active_stage_label": (
            projected_lifecycle_trigger.get("active_stage_label")
        ),
        "proactive_lifecycle_trigger_queue_override_status": (
            projected_lifecycle_trigger.get("queue_override_status")
        ),
        "proactive_lifecycle_trigger_remaining_stage_count": int(
            projected_lifecycle_trigger.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_launch_key": (
            projected_lifecycle_launch.get("launch_key")
        ),
        "proactive_lifecycle_launch_status": (
            projected_lifecycle_launch.get("status")
        ),
        "proactive_lifecycle_launch_mode": (
            projected_lifecycle_launch.get("launch_mode")
        ),
        "proactive_lifecycle_launch_decision": (
            projected_lifecycle_launch.get("decision")
        ),
        "proactive_lifecycle_launch_actionability": (
            projected_lifecycle_launch.get("actionability")
        ),
        "proactive_lifecycle_launch_active_stage_label": (
            projected_lifecycle_launch.get("active_stage_label")
        ),
        "proactive_lifecycle_launch_queue_override_status": (
            projected_lifecycle_launch.get("queue_override_status")
        ),
        "proactive_lifecycle_launch_remaining_stage_count": int(
            projected_lifecycle_launch.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_handoff_key": (
            projected_lifecycle_handoff.get("handoff_key")
        ),
        "proactive_lifecycle_handoff_status": (
            projected_lifecycle_handoff.get("status")
        ),
        "proactive_lifecycle_handoff_mode": (
            projected_lifecycle_handoff.get("handoff_mode")
        ),
        "proactive_lifecycle_handoff_decision": (
            projected_lifecycle_handoff.get("decision")
        ),
        "proactive_lifecycle_handoff_actionability": (
            projected_lifecycle_handoff.get("actionability")
        ),
        "proactive_lifecycle_handoff_active_stage_label": (
            projected_lifecycle_handoff.get("active_stage_label")
        ),
        "proactive_lifecycle_handoff_queue_override_status": (
            projected_lifecycle_handoff.get("queue_override_status")
        ),
        "proactive_lifecycle_handoff_remaining_stage_count": int(
            projected_lifecycle_handoff.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_continuation_key": (
            projected_lifecycle_continuation.get("continuation_key")
        ),
        "proactive_lifecycle_continuation_status": (
            projected_lifecycle_continuation.get("status")
        ),
        "proactive_lifecycle_continuation_mode": (
            projected_lifecycle_continuation.get("continuation_mode")
        ),
        "proactive_lifecycle_continuation_decision": (
            projected_lifecycle_continuation.get("decision")
        ),
        "proactive_lifecycle_continuation_actionability": (
            projected_lifecycle_continuation.get("actionability")
        ),
        "proactive_lifecycle_continuation_active_stage_label": (
            projected_lifecycle_continuation.get("active_stage_label")
        ),
        "proactive_lifecycle_continuation_queue_override_status": (
            projected_lifecycle_continuation.get("queue_override_status")
        ),
        "proactive_lifecycle_continuation_remaining_stage_count": int(
            projected_lifecycle_continuation.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_sustainment_key": (
            projected_lifecycle_sustainment.get("sustainment_key")
        ),
        "proactive_lifecycle_sustainment_status": (
            projected_lifecycle_sustainment.get("status")
        ),
        "proactive_lifecycle_sustainment_mode": (
            projected_lifecycle_sustainment.get("sustainment_mode")
        ),
        "proactive_lifecycle_sustainment_decision": (
            projected_lifecycle_sustainment.get("decision")
        ),
        "proactive_lifecycle_sustainment_actionability": (
            projected_lifecycle_sustainment.get("actionability")
        ),
        "proactive_lifecycle_sustainment_active_stage_label": (
            projected_lifecycle_sustainment.get("active_stage_label")
        ),
        "proactive_lifecycle_sustainment_queue_override_status": (
            projected_lifecycle_sustainment.get("queue_override_status")
        ),
        "proactive_lifecycle_sustainment_remaining_stage_count": int(
            projected_lifecycle_sustainment.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_stewardship_key": (
            projected_lifecycle_stewardship.get("stewardship_key")
        ),
        "proactive_lifecycle_stewardship_status": (
            projected_lifecycle_stewardship.get("status")
        ),
        "proactive_lifecycle_stewardship_mode": (
            projected_lifecycle_stewardship.get("stewardship_mode")
        ),
        "proactive_lifecycle_stewardship_decision": (
            projected_lifecycle_stewardship.get("decision")
        ),
        "proactive_lifecycle_stewardship_actionability": (
            projected_lifecycle_stewardship.get("actionability")
        ),
        "proactive_lifecycle_stewardship_active_stage_label": (
            projected_lifecycle_stewardship.get("active_stage_label")
        ),
        "proactive_lifecycle_stewardship_queue_override_status": (
            projected_lifecycle_stewardship.get("queue_override_status")
        ),
        "proactive_lifecycle_stewardship_remaining_stage_count": int(
            projected_lifecycle_stewardship.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_guardianship_key": (
            projected_lifecycle_guardianship.get("guardianship_key")
        ),
        "proactive_lifecycle_guardianship_status": (
            projected_lifecycle_guardianship.get("status")
        ),
        "proactive_lifecycle_guardianship_mode": (
            projected_lifecycle_guardianship.get("guardianship_mode")
        ),
        "proactive_lifecycle_guardianship_decision": (
            projected_lifecycle_guardianship.get("decision")
        ),
        "proactive_lifecycle_guardianship_actionability": (
            projected_lifecycle_guardianship.get("actionability")
        ),
        "proactive_lifecycle_guardianship_active_stage_label": (
            projected_lifecycle_guardianship.get("active_stage_label")
        ),
        "proactive_lifecycle_guardianship_queue_override_status": (
            projected_lifecycle_guardianship.get("queue_override_status")
        ),
        "proactive_lifecycle_guardianship_remaining_stage_count": int(
            projected_lifecycle_guardianship.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_oversight_key": (
            projected_lifecycle_oversight.get("oversight_key")
        ),
        "proactive_lifecycle_oversight_status": (
            projected_lifecycle_oversight.get("status")
        ),
        "proactive_lifecycle_oversight_mode": (
            projected_lifecycle_oversight.get("oversight_mode")
        ),
        "proactive_lifecycle_oversight_decision": (
            projected_lifecycle_oversight.get("decision")
        ),
        "proactive_lifecycle_oversight_actionability": (
            projected_lifecycle_oversight.get("actionability")
        ),
        "proactive_lifecycle_oversight_active_stage_label": (
            projected_lifecycle_oversight.get("active_stage_label")
        ),
        "proactive_lifecycle_oversight_queue_override_status": (
            projected_lifecycle_oversight.get("queue_override_status")
        ),
        "proactive_lifecycle_oversight_remaining_stage_count": int(
            projected_lifecycle_oversight.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_assurance_key": (
            projected_lifecycle_assurance.get("assurance_key")
        ),
        "proactive_lifecycle_assurance_status": (
            projected_lifecycle_assurance.get("status")
        ),
        "proactive_lifecycle_assurance_mode": (
            projected_lifecycle_assurance.get("assurance_mode")
        ),
        "proactive_lifecycle_assurance_decision": (
            projected_lifecycle_assurance.get("decision")
        ),
        "proactive_lifecycle_assurance_actionability": (
            projected_lifecycle_assurance.get("actionability")
        ),
        "proactive_lifecycle_assurance_active_stage_label": (
            projected_lifecycle_assurance.get("active_stage_label")
        ),
        "proactive_lifecycle_assurance_queue_override_status": (
            projected_lifecycle_assurance.get("queue_override_status")
        ),
        "proactive_lifecycle_assurance_remaining_stage_count": int(
            projected_lifecycle_assurance.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_attestation_key": (
            projected_lifecycle_attestation.get("attestation_key")
        ),
        "proactive_lifecycle_attestation_status": (
            projected_lifecycle_attestation.get("status")
        ),
        "proactive_lifecycle_attestation_mode": (
            projected_lifecycle_attestation.get("attestation_mode")
        ),
        "proactive_lifecycle_attestation_decision": (
            projected_lifecycle_attestation.get("decision")
        ),
        "proactive_lifecycle_attestation_actionability": (
            projected_lifecycle_attestation.get("actionability")
        ),
        "proactive_lifecycle_attestation_active_stage_label": (
            projected_lifecycle_attestation.get("active_stage_label")
        ),
        "proactive_lifecycle_attestation_queue_override_status": (
            projected_lifecycle_attestation.get("queue_override_status")
        ),
        "proactive_lifecycle_attestation_remaining_stage_count": int(
            projected_lifecycle_attestation.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_verification_key": (
            projected_lifecycle_verification.get("verification_key")
        ),
        "proactive_lifecycle_verification_status": (
            projected_lifecycle_verification.get("status")
        ),
        "proactive_lifecycle_verification_mode": (
            projected_lifecycle_verification.get("verification_mode")
        ),
        "proactive_lifecycle_verification_decision": (
            projected_lifecycle_verification.get("decision")
        ),
        "proactive_lifecycle_verification_actionability": (
            projected_lifecycle_verification.get("actionability")
        ),
        "proactive_lifecycle_verification_active_stage_label": (
            projected_lifecycle_verification.get("active_stage_label")
        ),
        "proactive_lifecycle_verification_queue_override_status": (
            projected_lifecycle_verification.get("queue_override_status")
        ),
        "proactive_lifecycle_verification_remaining_stage_count": int(
            projected_lifecycle_verification.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_certification_key": (
            projected_lifecycle_certification.get("certification_key")
        ),
        "proactive_lifecycle_certification_status": (
            projected_lifecycle_certification.get("status")
        ),
        "proactive_lifecycle_certification_mode": (
            projected_lifecycle_certification.get("certification_mode")
        ),
        "proactive_lifecycle_certification_decision": (
            projected_lifecycle_certification.get("decision")
        ),
        "proactive_lifecycle_certification_actionability": (
            projected_lifecycle_certification.get("actionability")
        ),
        "proactive_lifecycle_certification_active_stage_label": (
            projected_lifecycle_certification.get("active_stage_label")
        ),
        "proactive_lifecycle_certification_queue_override_status": (
            projected_lifecycle_certification.get("queue_override_status")
        ),
        "proactive_lifecycle_certification_remaining_stage_count": int(
            projected_lifecycle_certification.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_confirmation_key": (
            projected_lifecycle_confirmation.get("confirmation_key")
        ),
        "proactive_lifecycle_confirmation_status": (
            projected_lifecycle_confirmation.get("status")
        ),
        "proactive_lifecycle_confirmation_mode": (
            projected_lifecycle_confirmation.get("confirmation_mode")
        ),
        "proactive_lifecycle_confirmation_decision": (
            projected_lifecycle_confirmation.get("decision")
        ),
        "proactive_lifecycle_confirmation_actionability": (
            projected_lifecycle_confirmation.get("actionability")
        ),
        "proactive_lifecycle_confirmation_active_stage_label": (
            projected_lifecycle_confirmation.get("active_stage_label")
        ),
        "proactive_lifecycle_confirmation_queue_override_status": (
            projected_lifecycle_confirmation.get("queue_override_status")
        ),
        "proactive_lifecycle_confirmation_remaining_stage_count": int(
            projected_lifecycle_confirmation.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_ratification_key": (
            projected_lifecycle_ratification.get("ratification_key")
        ),
        "proactive_lifecycle_ratification_status": (
            projected_lifecycle_ratification.get("status")
        ),
        "proactive_lifecycle_ratification_mode": (
            projected_lifecycle_ratification.get("ratification_mode")
        ),
        "proactive_lifecycle_ratification_decision": (
            projected_lifecycle_ratification.get("decision")
        ),
        "proactive_lifecycle_ratification_actionability": (
            projected_lifecycle_ratification.get("actionability")
        ),
        "proactive_lifecycle_ratification_active_stage_label": (
            projected_lifecycle_ratification.get("active_stage_label")
        ),
        "proactive_lifecycle_ratification_queue_override_status": (
            projected_lifecycle_ratification.get("queue_override_status")
        ),
        "proactive_lifecycle_ratification_remaining_stage_count": int(
            projected_lifecycle_ratification.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_endorsement_key": (
            projected_lifecycle_endorsement.get("endorsement_key")
        ),
        "proactive_lifecycle_endorsement_status": (
            projected_lifecycle_endorsement.get("status")
        ),
        "proactive_lifecycle_endorsement_mode": (
            projected_lifecycle_endorsement.get("endorsement_mode")
        ),
        "proactive_lifecycle_endorsement_decision": (
            projected_lifecycle_endorsement.get("decision")
        ),
        "proactive_lifecycle_endorsement_actionability": (
            projected_lifecycle_endorsement.get("actionability")
        ),
        "proactive_lifecycle_endorsement_active_stage_label": (
            projected_lifecycle_endorsement.get("active_stage_label")
        ),
        "proactive_lifecycle_endorsement_queue_override_status": (
            projected_lifecycle_endorsement.get("queue_override_status")
        ),
        "proactive_lifecycle_endorsement_remaining_stage_count": int(
            projected_lifecycle_endorsement.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_authorization_key": (
            projected_lifecycle_authorization.get("authorization_key")
        ),
        "proactive_lifecycle_authorization_status": (
            projected_lifecycle_authorization.get("status")
        ),
        "proactive_lifecycle_authorization_mode": (
            projected_lifecycle_authorization.get("authorization_mode")
        ),
        "proactive_lifecycle_authorization_decision": (
            projected_lifecycle_authorization.get("decision")
        ),
        "proactive_lifecycle_authorization_actionability": (
            projected_lifecycle_authorization.get("actionability")
        ),
        "proactive_lifecycle_authorization_active_stage_label": (
            projected_lifecycle_authorization.get("active_stage_label")
        ),
        "proactive_lifecycle_authorization_queue_override_status": (
            projected_lifecycle_authorization.get("queue_override_status")
        ),
        "proactive_lifecycle_authorization_remaining_stage_count": int(
            projected_lifecycle_authorization.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_enactment_key": (
            projected_lifecycle_enactment.get("enactment_key")
        ),
        "proactive_lifecycle_enactment_status": (
            projected_lifecycle_enactment.get("status")
        ),
        "proactive_lifecycle_enactment_mode": (
            projected_lifecycle_enactment.get("enactment_mode")
        ),
        "proactive_lifecycle_enactment_decision": (
            projected_lifecycle_enactment.get("decision")
        ),
        "proactive_lifecycle_enactment_actionability": (
            projected_lifecycle_enactment.get("actionability")
        ),
        "proactive_lifecycle_enactment_active_stage_label": (
            projected_lifecycle_enactment.get("active_stage_label")
        ),
        "proactive_lifecycle_enactment_queue_override_status": (
            projected_lifecycle_enactment.get("queue_override_status")
        ),
        "proactive_lifecycle_enactment_remaining_stage_count": int(
            projected_lifecycle_enactment.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_finality_key": (
            projected_lifecycle_finality.get("finality_key")
        ),
        "proactive_lifecycle_finality_status": (
            projected_lifecycle_finality.get("status")
        ),
        "proactive_lifecycle_finality_mode": (
            projected_lifecycle_finality.get("finality_mode")
        ),
        "proactive_lifecycle_finality_decision": (
            projected_lifecycle_finality.get("decision")
        ),
        "proactive_lifecycle_finality_actionability": (
            projected_lifecycle_finality.get("actionability")
        ),
        "proactive_lifecycle_finality_active_stage_label": (
            projected_lifecycle_finality.get("active_stage_label")
        ),
        "proactive_lifecycle_finality_queue_override_status": (
            projected_lifecycle_finality.get("queue_override_status")
        ),
        "proactive_lifecycle_finality_remaining_stage_count": int(
            projected_lifecycle_finality.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_completion_key": (
            projected_lifecycle_completion.get("completion_key")
        ),
        "proactive_lifecycle_completion_status": (
            projected_lifecycle_completion.get("status")
        ),
        "proactive_lifecycle_completion_mode": (
            projected_lifecycle_completion.get("completion_mode")
        ),
        "proactive_lifecycle_completion_decision": (
            projected_lifecycle_completion.get("decision")
        ),
        "proactive_lifecycle_completion_actionability": (
            projected_lifecycle_completion.get("actionability")
        ),
        "proactive_lifecycle_completion_active_stage_label": (
            projected_lifecycle_completion.get("active_stage_label")
        ),
        "proactive_lifecycle_completion_queue_override_status": (
            projected_lifecycle_completion.get("queue_override_status")
        ),
        "proactive_lifecycle_completion_remaining_stage_count": int(
            projected_lifecycle_completion.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_conclusion_key": (
            projected_lifecycle_conclusion.get("conclusion_key")
        ),
        "proactive_lifecycle_conclusion_status": (
            projected_lifecycle_conclusion.get("status")
        ),
        "proactive_lifecycle_conclusion_mode": (
            projected_lifecycle_conclusion.get("conclusion_mode")
        ),
        "proactive_lifecycle_conclusion_decision": (
            projected_lifecycle_conclusion.get("decision")
        ),
        "proactive_lifecycle_conclusion_actionability": (
            projected_lifecycle_conclusion.get("actionability")
        ),
        "proactive_lifecycle_conclusion_active_stage_label": (
            projected_lifecycle_conclusion.get("active_stage_label")
        ),
        "proactive_lifecycle_conclusion_queue_override_status": (
            projected_lifecycle_conclusion.get("queue_override_status")
        ),
        "proactive_lifecycle_conclusion_remaining_stage_count": int(
            projected_lifecycle_conclusion.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_disposition_key": (
            projected_lifecycle_disposition.get("disposition_key")
        ),
        "proactive_lifecycle_disposition_status": (
            projected_lifecycle_disposition.get("status")
        ),
        "proactive_lifecycle_disposition_mode": (
            projected_lifecycle_disposition.get("disposition_mode")
        ),
        "proactive_lifecycle_disposition_decision": (
            projected_lifecycle_disposition.get("decision")
        ),
        "proactive_lifecycle_disposition_actionability": (
            projected_lifecycle_disposition.get("actionability")
        ),
        "proactive_lifecycle_disposition_active_stage_label": (
            projected_lifecycle_disposition.get("active_stage_label")
        ),
        "proactive_lifecycle_disposition_queue_override_status": (
            projected_lifecycle_disposition.get("queue_override_status")
        ),
        "proactive_lifecycle_disposition_remaining_stage_count": int(
            projected_lifecycle_disposition.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_standing_key": (
            projected_lifecycle_standing.get("standing_key")
        ),
        "proactive_lifecycle_standing_status": (
            projected_lifecycle_standing.get("status")
        ),
        "proactive_lifecycle_standing_mode": (
            projected_lifecycle_standing.get("standing_mode")
        ),
        "proactive_lifecycle_standing_decision": (
            projected_lifecycle_standing.get("decision")
        ),
        "proactive_lifecycle_standing_actionability": (
            projected_lifecycle_standing.get("actionability")
        ),
        "proactive_lifecycle_standing_active_stage_label": (
            projected_lifecycle_standing.get("active_stage_label")
        ),
        "proactive_lifecycle_standing_queue_override_status": (
            projected_lifecycle_standing.get("queue_override_status")
        ),
        "proactive_lifecycle_standing_remaining_stage_count": int(
            projected_lifecycle_standing.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_residency_key": (
            projected_lifecycle_residency.get("residency_key")
        ),
        "proactive_lifecycle_residency_status": (
            projected_lifecycle_residency.get("status")
        ),
        "proactive_lifecycle_residency_mode": (
            projected_lifecycle_residency.get("residency_mode")
        ),
        "proactive_lifecycle_residency_decision": (
            projected_lifecycle_residency.get("decision")
        ),
        "proactive_lifecycle_residency_actionability": (
            projected_lifecycle_residency.get("actionability")
        ),
        "proactive_lifecycle_residency_active_stage_label": (
            projected_lifecycle_residency.get("active_stage_label")
        ),
        "proactive_lifecycle_residency_queue_override_status": (
            projected_lifecycle_residency.get("queue_override_status")
        ),
        "proactive_lifecycle_residency_remaining_stage_count": int(
            projected_lifecycle_residency.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_tenure_key": (
            projected_lifecycle_tenure.get("tenure_key")
        ),
        "proactive_lifecycle_tenure_status": (
            projected_lifecycle_tenure.get("status")
        ),
        "proactive_lifecycle_tenure_mode": (
            projected_lifecycle_tenure.get("tenure_mode")
        ),
        "proactive_lifecycle_tenure_decision": (
            projected_lifecycle_tenure.get("decision")
        ),
        "proactive_lifecycle_tenure_actionability": (
            projected_lifecycle_tenure.get("actionability")
        ),
        "proactive_lifecycle_tenure_active_stage_label": (
            projected_lifecycle_tenure.get("active_stage_label")
        ),
        "proactive_lifecycle_tenure_queue_override_status": (
            projected_lifecycle_tenure.get("queue_override_status")
        ),
        "proactive_lifecycle_tenure_remaining_stage_count": int(
            projected_lifecycle_tenure.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_persistence_key": (
            projected_lifecycle_persistence.get("persistence_key")
        ),
        "proactive_lifecycle_persistence_status": (
            projected_lifecycle_persistence.get("status")
        ),
        "proactive_lifecycle_persistence_mode": (
            projected_lifecycle_persistence.get("persistence_mode")
        ),
        "proactive_lifecycle_persistence_decision": (
            projected_lifecycle_persistence.get("decision")
        ),
        "proactive_lifecycle_persistence_actionability": (
            projected_lifecycle_persistence.get("actionability")
        ),
        "proactive_lifecycle_persistence_active_stage_label": (
            projected_lifecycle_persistence.get("active_stage_label")
        ),
        "proactive_lifecycle_persistence_queue_override_status": (
            projected_lifecycle_persistence.get("queue_override_status")
        ),
        "proactive_lifecycle_persistence_remaining_stage_count": int(
            projected_lifecycle_persistence.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_durability_key": (
            projected_lifecycle_durability.get("durability_key")
        ),
        "proactive_lifecycle_durability_status": (
            projected_lifecycle_durability.get("status")
        ),
        "proactive_lifecycle_durability_mode": (
            projected_lifecycle_durability.get("durability_mode")
        ),
        "proactive_lifecycle_durability_decision": (
            projected_lifecycle_durability.get("decision")
        ),
        "proactive_lifecycle_durability_actionability": (
            projected_lifecycle_durability.get("actionability")
        ),
        "proactive_lifecycle_durability_active_stage_label": (
            projected_lifecycle_durability.get("active_stage_label")
        ),
        "proactive_lifecycle_durability_queue_override_status": (
            projected_lifecycle_durability.get("queue_override_status")
        ),
        "proactive_lifecycle_durability_remaining_stage_count": int(
            projected_lifecycle_durability.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_longevity_key": (
            projected_lifecycle_longevity.get("longevity_key")
        ),
        "proactive_lifecycle_longevity_status": (
            projected_lifecycle_longevity.get("status")
        ),
        "proactive_lifecycle_longevity_mode": (
            projected_lifecycle_longevity.get("longevity_mode")
        ),
        "proactive_lifecycle_longevity_decision": (
            projected_lifecycle_longevity.get("decision")
        ),
        "proactive_lifecycle_longevity_actionability": (
            projected_lifecycle_longevity.get("actionability")
        ),
        "proactive_lifecycle_longevity_active_stage_label": (
            projected_lifecycle_longevity.get("active_stage_label")
        ),
        "proactive_lifecycle_longevity_queue_override_status": (
            projected_lifecycle_longevity.get("queue_override_status")
        ),
        "proactive_lifecycle_longevity_remaining_stage_count": int(
            projected_lifecycle_longevity.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_legacy_key": (
            projected_lifecycle_legacy.get("legacy_key")
        ),
        "proactive_lifecycle_legacy_status": (
            projected_lifecycle_legacy.get("status")
        ),
        "proactive_lifecycle_legacy_mode": (
            projected_lifecycle_legacy.get("legacy_mode")
        ),
        "proactive_lifecycle_legacy_decision": (
            projected_lifecycle_legacy.get("decision")
        ),
        "proactive_lifecycle_legacy_actionability": (
            projected_lifecycle_legacy.get("actionability")
        ),
        "proactive_lifecycle_legacy_active_stage_label": (
            projected_lifecycle_legacy.get("active_stage_label")
        ),
        "proactive_lifecycle_legacy_queue_override_status": (
            projected_lifecycle_legacy.get("queue_override_status")
        ),
        "proactive_lifecycle_legacy_remaining_stage_count": int(
            projected_lifecycle_legacy.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_heritage_key": (
            projected_lifecycle_heritage.get("heritage_key")
        ),
        "proactive_lifecycle_heritage_status": (
            projected_lifecycle_heritage.get("status")
        ),
        "proactive_lifecycle_heritage_mode": (
            projected_lifecycle_heritage.get("heritage_mode")
        ),
        "proactive_lifecycle_heritage_decision": (
            projected_lifecycle_heritage.get("decision")
        ),
        "proactive_lifecycle_heritage_actionability": (
            projected_lifecycle_heritage.get("actionability")
        ),
        "proactive_lifecycle_heritage_active_stage_label": (
            projected_lifecycle_heritage.get("active_stage_label")
        ),
        "proactive_lifecycle_heritage_queue_override_status": (
            projected_lifecycle_heritage.get("queue_override_status")
        ),
        "proactive_lifecycle_heritage_remaining_stage_count": int(
            projected_lifecycle_heritage.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_lineage_key": (
            projected_lifecycle_lineage.get("lineage_key")
        ),
        "proactive_lifecycle_lineage_status": (
            projected_lifecycle_lineage.get("status")
        ),
        "proactive_lifecycle_lineage_mode": (
            projected_lifecycle_lineage.get("lineage_mode")
        ),
        "proactive_lifecycle_lineage_decision": (
            projected_lifecycle_lineage.get("decision")
        ),
        "proactive_lifecycle_lineage_actionability": (
            projected_lifecycle_lineage.get("actionability")
        ),
        "proactive_lifecycle_lineage_active_stage_label": (
            projected_lifecycle_lineage.get("active_stage_label")
        ),
        "proactive_lifecycle_lineage_queue_override_status": (
            projected_lifecycle_lineage.get("queue_override_status")
        ),
        "proactive_lifecycle_lineage_remaining_stage_count": int(
            projected_lifecycle_lineage.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_ancestry_key": (
            projected_lifecycle_ancestry.get("ancestry_key")
        ),
        "proactive_lifecycle_ancestry_status": (
            projected_lifecycle_ancestry.get("status")
        ),
        "proactive_lifecycle_ancestry_mode": (
            projected_lifecycle_ancestry.get("ancestry_mode")
        ),
        "proactive_lifecycle_ancestry_decision": (
            projected_lifecycle_ancestry.get("decision")
        ),
        "proactive_lifecycle_ancestry_actionability": (
            projected_lifecycle_ancestry.get("actionability")
        ),
        "proactive_lifecycle_ancestry_active_stage_label": (
            projected_lifecycle_ancestry.get("active_stage_label")
        ),
        "proactive_lifecycle_ancestry_queue_override_status": (
            projected_lifecycle_ancestry.get("queue_override_status")
        ),
        "proactive_lifecycle_ancestry_remaining_stage_count": int(
            projected_lifecycle_ancestry.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_provenance_key": (
            projected_lifecycle_provenance.get("provenance_key")
        ),
        "proactive_lifecycle_provenance_status": (
            projected_lifecycle_provenance.get("status")
        ),
        "proactive_lifecycle_provenance_mode": (
            projected_lifecycle_provenance.get("provenance_mode")
        ),
        "proactive_lifecycle_provenance_decision": (
            projected_lifecycle_provenance.get("decision")
        ),
        "proactive_lifecycle_provenance_actionability": (
            projected_lifecycle_provenance.get("actionability")
        ),
        "proactive_lifecycle_provenance_active_stage_label": (
            projected_lifecycle_provenance.get("active_stage_label")
        ),
        "proactive_lifecycle_provenance_queue_override_status": (
            projected_lifecycle_provenance.get("queue_override_status")
        ),
        "proactive_lifecycle_provenance_remaining_stage_count": int(
            projected_lifecycle_provenance.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_origin_key": projected_lifecycle_origin.get(
            "origin_key"
        ),
        "proactive_lifecycle_origin_status": projected_lifecycle_origin.get(
            "status"
        ),
        "proactive_lifecycle_origin_mode": projected_lifecycle_origin.get(
            "origin_mode"
        ),
        "proactive_lifecycle_origin_decision": projected_lifecycle_origin.get(
            "decision"
        ),
        "proactive_lifecycle_origin_actionability": projected_lifecycle_origin.get(
            "actionability"
        ),
        "proactive_lifecycle_origin_active_stage_label": (
            projected_lifecycle_origin.get("active_stage_label")
        ),
        "proactive_lifecycle_origin_queue_override_status": (
            projected_lifecycle_origin.get("queue_override_status")
        ),
        "proactive_lifecycle_origin_remaining_stage_count": int(
            projected_lifecycle_origin.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_root_key": projected_lifecycle_root.get("root_key"),
        "proactive_lifecycle_root_status": projected_lifecycle_root.get("status"),
        "proactive_lifecycle_root_mode": projected_lifecycle_root.get("root_mode"),
        "proactive_lifecycle_root_decision": projected_lifecycle_root.get(
            "decision"
        ),
        "proactive_lifecycle_root_actionability": projected_lifecycle_root.get(
            "actionability"
        ),
        "proactive_lifecycle_root_active_stage_label": (
            projected_lifecycle_root.get("active_stage_label")
        ),
        "proactive_lifecycle_root_queue_override_status": (
            projected_lifecycle_root.get("queue_override_status")
        ),
        "proactive_lifecycle_root_remaining_stage_count": int(
            projected_lifecycle_root.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_foundation_key": projected_lifecycle_foundation.get(
            "foundation_key"
        ),
        "proactive_lifecycle_foundation_status": projected_lifecycle_foundation.get(
            "status"
        ),
        "proactive_lifecycle_foundation_mode": projected_lifecycle_foundation.get(
            "foundation_mode"
        ),
        "proactive_lifecycle_foundation_decision": (
            projected_lifecycle_foundation.get("decision")
        ),
        "proactive_lifecycle_foundation_actionability": (
            projected_lifecycle_foundation.get("actionability")
        ),
        "proactive_lifecycle_foundation_active_stage_label": (
            projected_lifecycle_foundation.get("active_stage_label")
        ),
        "proactive_lifecycle_foundation_queue_override_status": (
            projected_lifecycle_foundation.get("queue_override_status")
        ),
        "proactive_lifecycle_foundation_remaining_stage_count": int(
            projected_lifecycle_foundation.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_bedrock_key": projected_lifecycle_bedrock.get(
            "bedrock_key"
        ),
        "proactive_lifecycle_bedrock_status": projected_lifecycle_bedrock.get(
            "status"
        ),
        "proactive_lifecycle_bedrock_mode": projected_lifecycle_bedrock.get(
            "bedrock_mode"
        ),
        "proactive_lifecycle_bedrock_decision": (
            projected_lifecycle_bedrock.get("decision")
        ),
        "proactive_lifecycle_bedrock_actionability": (
            projected_lifecycle_bedrock.get("actionability")
        ),
        "proactive_lifecycle_bedrock_active_stage_label": (
            projected_lifecycle_bedrock.get("active_stage_label")
        ),
        "proactive_lifecycle_bedrock_queue_override_status": (
            projected_lifecycle_bedrock.get("queue_override_status")
        ),
        "proactive_lifecycle_bedrock_remaining_stage_count": int(
            projected_lifecycle_bedrock.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_substrate_key": projected_lifecycle_substrate.get(
            "substrate_key"
        ),
        "proactive_lifecycle_substrate_status": projected_lifecycle_substrate.get(
            "status"
        ),
        "proactive_lifecycle_substrate_mode": projected_lifecycle_substrate.get(
            "substrate_mode"
        ),
        "proactive_lifecycle_substrate_decision": (
            projected_lifecycle_substrate.get("decision")
        ),
        "proactive_lifecycle_substrate_actionability": (
            projected_lifecycle_substrate.get("actionability")
        ),
        "proactive_lifecycle_substrate_active_stage_label": (
            projected_lifecycle_substrate.get("active_stage_label")
        ),
        "proactive_lifecycle_substrate_queue_override_status": (
            projected_lifecycle_substrate.get("queue_override_status")
        ),
        "proactive_lifecycle_substrate_remaining_stage_count": int(
            projected_lifecycle_substrate.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_stratum_key": projected_lifecycle_stratum.get(
            "stratum_key"
        ),
        "proactive_lifecycle_stratum_status": projected_lifecycle_stratum.get(
            "status"
        ),
        "proactive_lifecycle_stratum_mode": projected_lifecycle_stratum.get(
            "stratum_mode"
        ),
        "proactive_lifecycle_stratum_decision": (
            projected_lifecycle_stratum.get("decision")
        ),
        "proactive_lifecycle_stratum_actionability": (
            projected_lifecycle_stratum.get("actionability")
        ),
        "proactive_lifecycle_stratum_active_stage_label": (
            projected_lifecycle_stratum.get("active_stage_label")
        ),
        "proactive_lifecycle_stratum_queue_override_status": (
            projected_lifecycle_stratum.get("queue_override_status")
        ),
        "proactive_lifecycle_stratum_remaining_stage_count": int(
            projected_lifecycle_stratum.get("remaining_stage_count") or 0
        ),
        "proactive_lifecycle_layer_key": projected_lifecycle_layer.get("layer_key"),
        "proactive_lifecycle_layer_status": projected_lifecycle_layer.get(
            "status"
        ),
        "proactive_lifecycle_layer_mode": projected_lifecycle_layer.get(
            "layer_mode"
        ),
        "proactive_lifecycle_layer_decision": (
            projected_lifecycle_layer.get("decision")
        ),
        "proactive_lifecycle_layer_actionability": (
            projected_lifecycle_layer.get("actionability")
        ),
        "proactive_lifecycle_layer_active_stage_label": (
            projected_lifecycle_layer.get("active_stage_label")
        ),
        "proactive_lifecycle_layer_queue_override_status": (
            projected_lifecycle_layer.get("queue_override_status")
        ),
        "proactive_lifecycle_layer_remaining_stage_count": int(
            projected_lifecycle_layer.get("remaining_stage_count") or 0
        ),
        "proactive_scheduling_status": proactive_scheduling_plan.get("status"),
        "proactive_scheduling_mode": proactive_scheduling_plan.get(
            "scheduler_mode"
        ),
        "proactive_scheduling_min_seconds_since_last_outbound": int(
            proactive_scheduling_plan.get("min_seconds_since_last_outbound") or 0
        ),
        "proactive_scheduling_first_touch_extra_delay_seconds": int(
            proactive_scheduling_plan.get("first_touch_extra_delay_seconds") or 0
        ),
        "proactive_scheduling_stage_spacing_mode": proactive_scheduling_plan.get(
            "stage_spacing_mode"
        ),
        "proactive_scheduling_low_pressure_guard": proactive_scheduling_plan.get(
            "low_pressure_guard"
        ),
        "proactive_guardrail_key": proactive_guardrail_plan.get("guardrail_key"),
        "proactive_guardrail_max_dispatch_count": max_dispatch_count,
        "proactive_guardrail_stage_min_seconds_since_last_user": int(
            (current_stage_guardrail or {}).get("min_seconds_since_last_user") or 0
        ),
        "proactive_guardrail_stage_min_seconds_since_last_dispatch": int(
            (current_stage_guardrail or {}).get(
                "min_seconds_since_last_dispatch"
            )
            or 0
        ),
        "proactive_guardrail_stage_on_guardrail_hit": (
            (current_stage_guardrail or {}).get("on_guardrail_hit")
        ),
        "proactive_guardrail_hard_stop_conditions": list(
            proactive_guardrail_plan.get("hard_stop_conditions") or []
        ),
        "proactive_orchestration_key": proactive_orchestration_plan.get(
            "orchestration_key"
        ),
        "proactive_orchestration_stage_objective": (
            (current_stage_directive or {}).get("objective")
        ),
        "proactive_orchestration_stage_delivery_mode": (
            (current_stage_directive or {}).get("delivery_mode")
        ),
        "proactive_orchestration_stage_question_mode": (
            (current_stage_directive or {}).get("question_mode")
        ),
        "proactive_orchestration_stage_autonomy_mode": (
            (current_stage_directive or {}).get("autonomy_mode")
        ),
        "proactive_orchestration_stage_closing_style": (
            (current_stage_directive or {}).get("closing_style")
        ),
        "proactive_actuation_key": proactive_actuation_plan.get("actuation_key"),
        "proactive_actuation_opening_move": (
            (current_stage_actuation or {}).get("opening_move")
        ),
        "proactive_actuation_bridge_move": (
            (current_stage_actuation or {}).get("bridge_move")
        ),
        "proactive_actuation_closing_move": (
            (current_stage_actuation or {}).get("closing_move")
        ),
        "proactive_actuation_continuity_anchor": (
            (current_stage_actuation or {}).get("continuity_anchor")
        ),
        "proactive_actuation_somatic_mode": (
            (current_stage_actuation or {}).get("somatic_mode")
        ),
        "proactive_actuation_somatic_body_anchor": (
            (current_stage_actuation or {}).get("somatic_body_anchor")
        ),
        "proactive_actuation_followup_style": (
            (current_stage_actuation or {}).get("followup_style")
        ),
        "proactive_actuation_user_space_signal": (
            (current_stage_actuation or {}).get("user_space_signal")
        ),
        "proactive_progression_key": proactive_progression_plan.get(
            "progression_key"
        ),
        "proactive_progression_close_loop_stage": close_loop_stage,
        "proactive_progression_stage_action": (
            (current_stage_progression or {}).get("on_expired")
        ),
        "proactive_progression_max_overdue_seconds": int(
            (current_stage_progression or {}).get("max_overdue_seconds") or 0
        ),
        "proactive_progression_advanced": progression_advanced,
        "proactive_progression_reason": progression_reason,
        "trigger_after_seconds": int(directive.get("trigger_after_seconds") or 0),
        "window_seconds": int(directive.get("window_seconds") or 0),
        "proactive_cadence_key": proactive_cadence_plan.get("cadence_key"),
        "proactive_cadence_status": proactive_cadence_plan.get("status"),
        "proactive_cadence_stage_index": current_stage_index,
        "proactive_cadence_stage_label": current_stage_label,
        "proactive_cadence_stage_count": max_dispatch_count,
        "proactive_cadence_remaining_dispatches": max(
            0,
            max_dispatch_count - (current_stage_index - 1),
        ),
        "proactive_cadence_next_interval_seconds": (
            stage_intervals_seconds[
                min(current_stage_index - 1, len(stage_intervals_seconds) - 1)
            ]
            if stage_intervals_seconds
            else 0
        ),
        "proactive_cadence_dispatched_stage_count": dispatched_stage_count,
        "due_at": due_at.isoformat() if due_at is not None else None,
        "base_due_at": base_due_at.isoformat() if base_due_at is not None else None,
        "expires_at": expires_at.isoformat() if expires_at is not None else None,
        "seconds_until_due": seconds_until_due,
        "seconds_overdue": seconds_overdue,
        "window_remaining_seconds": window_remaining_seconds,
        "schedule_reason": schedule_reason,
        "scheduling_deferred_until": (
            scheduling_deferred_until.isoformat()
            if scheduling_deferred_until is not None
            else None
        ),
        "opening_hint": directive.get("opening_hint"),
        "rationale": directive.get("rationale"),
        "trigger_conditions": list(directive.get("trigger_conditions") or []),
        "hold_reasons": list(directive.get("hold_reasons") or []),
        "scheduling_notes": list(
            proactive_scheduling_plan.get("scheduling_notes") or []
        ),
        "time_awareness_mode": (
            dict(state.get("runtime_coordination_snapshot") or {}).get(
                "time_awareness_mode"
            )
        ),
        "cognitive_load_band": (
            dict(state.get("runtime_coordination_snapshot") or {}).get(
                "cognitive_load_band"
            )
        ),
        "proactive_style": (
            dict(state.get("runtime_coordination_snapshot") or {}).get(
                "proactive_style"
            )
        ),
        "somatic_cue": (
            dict(state.get("runtime_coordination_snapshot") or {}).get(
                "somatic_cue"
            )
        ),
        "turn_count": int(state.get("turn_count") or 0),
        "started_at": (
            latest_session_event.occurred_at.isoformat()
            if latest_session_event is not None
            else session.get("created_at")
        ),
        "last_user_message_at": (
            latest_user_event.occurred_at.isoformat()
            if latest_user_event is not None
            else None
        ),
        "last_assistant_message_at": (
            latest_assistant_event.occurred_at.isoformat()
            if latest_assistant_event is not None
            else None
        ),
        "directive_updated_at": directive_time.isoformat(),
        "scheduling_updated_at": (
            latest_proactive_scheduling_event.occurred_at.isoformat()
            if latest_proactive_scheduling_event is not None
            else None
        ),
        "orchestration_updated_at": (
            latest_proactive_orchestration_event.occurred_at.isoformat()
            if latest_proactive_orchestration_event is not None
            else None
        ),
        "actuation_updated_at": (
            latest_proactive_actuation_event.occurred_at.isoformat()
            if latest_proactive_actuation_event is not None
            else None
        ),
        "progression_updated_at": (
            latest_proactive_progression_event.occurred_at.isoformat()
            if latest_proactive_progression_event is not None
            else None
        ),
        "dispatch_gate_updated_at": (
            latest_proactive_dispatch_gate_event.occurred_at.isoformat()
            if latest_proactive_dispatch_gate_event is not None
            else None
        ),
        "dispatch_feedback_updated_at": (
            latest_proactive_dispatch_feedback_event.occurred_at.isoformat()
            if latest_proactive_dispatch_feedback_event is not None
            else None
        ),
        "stage_controller_updated_at": (
            latest_proactive_stage_controller_event.occurred_at.isoformat()
            if latest_proactive_stage_controller_event is not None
            else None
        ),
        "line_controller_updated_at": (
            latest_proactive_line_controller_event.occurred_at.isoformat()
            if latest_proactive_line_controller_event is not None
            else None
        ),
        "last_event_at": events[-1].occurred_at.isoformat() if events else None,
    }

def _latest_event(
    events: list[StoredEvent],
    *,
    event_type: str,
) -> StoredEvent | None:
    return next(
        (event for event in reversed(events) if event.event_type == event_type),
        None,
    )


def sort_key(item: dict[str, Any]) -> tuple[object, ...]:
    """Sort key for followup items — used by the service layer."""
    queue_status = str(item.get("queue_status") or "hold")
    due_at = _parse_datetime(item.get("due_at"))
    last_event_at = _parse_datetime(item.get("last_event_at"))
    return (
        _QUEUE_PRIORITY.get(queue_status, 99),
        due_at.timestamp() if due_at is not None else float("inf"),
        -int(item.get("turn_count") or 0),
        -(last_event_at.timestamp() if last_event_at is not None else 0.0),
        str(item.get("session_id") or ""),
    )


def _stage_entry(
    items: object,
    stage_label: str,
) -> dict[str, Any] | None:
    for item in list(items or []):
        candidate = dict(item)
        if str(candidate.get("stage_label") or "") == stage_label:
            return candidate
    return None


def _selected_matrix_candidate(
    reengagement_matrix_assessment: dict[str, Any],
) -> dict[str, Any]:
    selected_strategy_key = str(
        reengagement_matrix_assessment.get("selected_strategy_key") or ""
    )
    for item in list(reengagement_matrix_assessment.get("candidates") or []):
        candidate = dict(item)
        if bool(candidate.get("selected")):
            return candidate
        if (
            selected_strategy_key
            and str(candidate.get("strategy_key") or "") == selected_strategy_key
        ):
            return candidate
    return {}


def _compute_stage_schedule(
    *,
    reference_time: datetime,
    directive_time: datetime,
    dispatch_events_for_directive: list[StoredEvent],
    latest_assistant_event: StoredEvent | None,
    proactive_scheduling_plan: dict[str, Any],
    trigger_after_seconds: int,
    window_seconds: int,
    progression_anchor_at: datetime | None,
) -> tuple[
    datetime | None,
    datetime | None,
    datetime | None,
    int | None,
    int | None,
    int | None,
    str | None,
    datetime | None,
]:
    seconds_until_due: int | None = None
    seconds_overdue: int | None = None
    window_remaining_seconds: int | None = None
    schedule_reason: str | None = None
    scheduling_deferred_until: datetime | None = None

    if progression_anchor_at is not None:
        base_due_at = progression_anchor_at
        due_at = progression_anchor_at
        expires_at = due_at + timedelta(seconds=window_seconds)
        if window_seconds == 0 or reference_time <= expires_at:
            window_remaining_seconds = max(
                0,
                int((expires_at - reference_time).total_seconds()),
            )
            schedule_reason = "progression_advanced"
        else:
            seconds_overdue = max(
                0,
                int((reference_time - expires_at).total_seconds()),
            )
            schedule_reason = "progression_advanced"
        return (
            base_due_at,
            due_at,
            expires_at,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
            schedule_reason,
            scheduling_deferred_until,
        )

    base_time = (
        dispatch_events_for_directive[-1].occurred_at
        if dispatch_events_for_directive
        else directive_time
    )
    base_due_at = base_time + timedelta(seconds=trigger_after_seconds)
    due_at = base_due_at
    min_seconds_since_last_outbound = max(
        0,
        int(
            proactive_scheduling_plan.get("min_seconds_since_last_outbound")
            or 0
        ),
    )
    outbound_reference_time = (
        dispatch_events_for_directive[-1].occurred_at
        if dispatch_events_for_directive
        else (
            latest_assistant_event.occurred_at
            if latest_assistant_event is not None
            else directive_time
        )
    )
    if min_seconds_since_last_outbound > 0:
        scheduling_deferred_until = outbound_reference_time + timedelta(
            seconds=min_seconds_since_last_outbound
        )
        if scheduling_deferred_until > due_at:
            due_at = scheduling_deferred_until
            schedule_reason = "respect_outbound_cooldown"
    expires_at = due_at + timedelta(seconds=window_seconds)
    return (
        base_due_at,
        due_at,
        expires_at,
        seconds_until_due,
        seconds_overdue,
        window_remaining_seconds,
        schedule_reason,
        scheduling_deferred_until,
    )


def _apply_matrix_learning_spacing(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    reengagement_matrix_assessment: dict[str, Any],
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or current_stage_label == "first_touch":
        return due_at, expires_at, schedule_reason
    if "progression_advanced" in str(schedule_reason or ""):
        return due_at, expires_at, schedule_reason

    learning_mode = str(
        reengagement_matrix_assessment.get("learning_mode") or "cold_start"
    )
    if learning_mode == "contextual_reinforcement":
        return due_at, expires_at, schedule_reason

    selected_candidate = _selected_matrix_candidate(reengagement_matrix_assessment)
    contextual_supporting_session_count = max(
        0,
        int(selected_candidate.get("contextual_supporting_session_count") or 0),
    )
    if contextual_supporting_session_count > 0:
        return due_at, expires_at, schedule_reason

    supporting_session_count = max(
        0,
        int(selected_candidate.get("supporting_session_count") or 0),
    )
    buffer_seconds = 0
    if supporting_session_count <= 0:
        buffer_seconds = 1800 if current_stage_label == "second_touch" else 3600
    elif supporting_session_count == 1:
        buffer_seconds = 900 if current_stage_label == "second_touch" else 1800
    elif learning_mode == "safe_exploration":
        buffer_seconds = 600 if current_stage_label == "second_touch" else 1200

    if buffer_seconds <= 0:
        return due_at, expires_at, schedule_reason

    adjusted_due_at = due_at + timedelta(seconds=buffer_seconds)
    adjusted_expires_at = adjusted_due_at + timedelta(seconds=window_seconds)
    adjusted_reason = (
        f"{schedule_reason} | matrix_learning_buffered"
        if schedule_reason
        else "matrix_learning_buffered"
    )
    return adjusted_due_at, adjusted_expires_at, adjusted_reason


def _apply_stage_guardrail(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    latest_user_event: StoredEvent | None,
    dispatch_events_for_directive: list[StoredEvent],
    current_stage_guardrail: dict[str, Any] | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or not current_stage_guardrail:
        return due_at, expires_at, schedule_reason

    guardrail_due_at = due_at
    reasons: list[str] = []
    min_seconds_since_last_user = max(
        0,
        int(current_stage_guardrail.get("min_seconds_since_last_user") or 0),
    )
    if latest_user_event is not None and min_seconds_since_last_user > 0:
        user_ready_at = latest_user_event.occurred_at + timedelta(
            seconds=min_seconds_since_last_user
        )
        if user_ready_at > guardrail_due_at:
            guardrail_due_at = user_ready_at
            reasons.append("user_space")

    min_seconds_since_last_dispatch = max(
        0,
        int(current_stage_guardrail.get("min_seconds_since_last_dispatch") or 0),
    )
    if dispatch_events_for_directive and min_seconds_since_last_dispatch > 0:
        dispatch_ready_at = dispatch_events_for_directive[-1].occurred_at + timedelta(
            seconds=min_seconds_since_last_dispatch
        )
        if dispatch_ready_at > guardrail_due_at:
            guardrail_due_at = dispatch_ready_at
            reasons.append("dispatch_spacing")

    if guardrail_due_at <= due_at:
        return due_at, expires_at, schedule_reason

    delay_extension = guardrail_due_at - due_at
    adjusted_expires_at = (
        expires_at + delay_extension if expires_at is not None else None
    )
    guardrail_reason = f"guardrail:{'+'.join(reasons) or 'defer'}"
    adjusted_reason = (
        f"{schedule_reason}|{guardrail_reason}"
        if schedule_reason
        else guardrail_reason
    )
    return guardrail_due_at, adjusted_expires_at, adjusted_reason


def _apply_dispatch_gate(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    dispatch_events_for_directive: list[StoredEvent],
    latest_dispatch_gate_event: StoredEvent | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or latest_dispatch_gate_event is None:
        return due_at, expires_at, schedule_reason

    if (
        dispatch_events_for_directive
        and latest_dispatch_gate_event.occurred_at
        <= dispatch_events_for_directive[-1].occurred_at
    ):
        return due_at, expires_at, schedule_reason

    payload = dict(latest_dispatch_gate_event.payload)
    if str(payload.get("stage_label") or "") != current_stage_label:
        return due_at, expires_at, schedule_reason
    if str(payload.get("decision") or "dispatch") != "defer":
        return due_at, expires_at, schedule_reason

    retry_after_seconds = max(0, int(payload.get("retry_after_seconds") or 0))
    if retry_after_seconds <= 0:
        return due_at, expires_at, schedule_reason

    gate_anchor_at = max(latest_dispatch_gate_event.occurred_at, due_at)
    gate_due_at = gate_anchor_at + timedelta(seconds=retry_after_seconds)
    adjusted_expires_at = gate_due_at + timedelta(seconds=window_seconds)
    gate_reason = f"dispatch_gate:{payload.get('gate_key') or 'defer'}"
    adjusted_reason = (
        f"{schedule_reason}|{gate_reason}" if schedule_reason else gate_reason
    )
    return gate_due_at, adjusted_expires_at, adjusted_reason


def _apply_stage_controller(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    latest_stage_controller_event: StoredEvent | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or latest_stage_controller_event is None:
        return due_at, expires_at, schedule_reason

    payload = dict(latest_stage_controller_event.payload)
    if str(payload.get("status") or "") not in {"active", "terminal"}:
        return due_at, expires_at, schedule_reason
    if str(payload.get("target_stage_label") or "") != current_stage_label:
        return due_at, expires_at, schedule_reason
    if str(payload.get("decision") or "") != "slow_next_stage":
        return due_at, expires_at, schedule_reason

    additional_delay_seconds = max(
        0,
        int(payload.get("additional_delay_seconds") or 0),
    )
    if additional_delay_seconds <= 0:
        return due_at, expires_at, schedule_reason

    adjusted_due_at = due_at + timedelta(seconds=additional_delay_seconds)
    adjusted_expires_at = adjusted_due_at + timedelta(seconds=window_seconds)
    controller_reason = (
        f"controller:{payload.get('controller_key') or 'slow_next_stage'}"
    )
    reasons = [reason for reason in [schedule_reason, controller_reason] if reason]
    return adjusted_due_at, adjusted_expires_at, " | ".join(reasons) or None


def _apply_line_controller(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    latest_line_controller_event: StoredEvent | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or latest_line_controller_event is None:
        return due_at, expires_at, schedule_reason

    if (
        current_stage_label == "final_soft_close"
        and "progression_advanced" in str(schedule_reason or "")
    ):
        return due_at, expires_at, schedule_reason

    payload = dict(latest_line_controller_event.payload)
    if str(payload.get("status") or "") not in {"active", "terminal"}:
        return due_at, expires_at, schedule_reason
    if current_stage_label not in list(payload.get("affected_stage_labels") or []):
        return due_at, expires_at, schedule_reason
    if str(payload.get("decision") or "") not in {
        "soften_remaining_line",
        "retire_after_close_loop",
    }:
        return due_at, expires_at, schedule_reason

    additional_delay_seconds = max(
        0,
        int(payload.get("additional_delay_seconds") or 0),
    )
    if additional_delay_seconds <= 0:
        return due_at, expires_at, schedule_reason

    adjusted_due_at = due_at + timedelta(seconds=additional_delay_seconds)
    adjusted_expires_at = adjusted_due_at + timedelta(seconds=window_seconds)
    controller_reason = (
        f"line_controller:{payload.get('controller_key') or 'soften_remaining_line'}"
    )
    reasons = [reason for reason in [schedule_reason, controller_reason] if reason]
    return adjusted_due_at, adjusted_expires_at, " | ".join(reasons) or None


def _resolve_queue_status(
    *,
    reference_time: datetime,
    base_due_at: datetime | None,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
) -> tuple[str, int | None, int | None, int | None]:
    seconds_until_due: int | None = None
    seconds_overdue: int | None = None
    window_remaining_seconds: int | None = None

    if base_due_at is not None and reference_time < base_due_at:
        seconds_until_due = max(
            0,
            int((base_due_at - reference_time).total_seconds()),
        )
        window_remaining_seconds = window_seconds
        return ("waiting", seconds_until_due, seconds_overdue, window_remaining_seconds)

    if (
        base_due_at is not None
        and due_at is not None
        and base_due_at < due_at
        and reference_time < due_at
    ):
        seconds_until_due = max(
            0,
            int((due_at - reference_time).total_seconds()),
        )
        window_remaining_seconds = window_seconds
        return (
            "scheduled",
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        )

    if window_seconds == 0 or (
        expires_at is not None and reference_time <= expires_at
    ):
        window_remaining_seconds = (
            max(
                0,
                int((expires_at - reference_time).total_seconds()),
            )
            if expires_at is not None
            else window_seconds
        )
        return ("due", seconds_until_due, seconds_overdue, window_remaining_seconds)

    if expires_at is None:
        return ("hold", seconds_until_due, seconds_overdue, window_remaining_seconds)

    seconds_overdue = max(
        0,
        int((reference_time - expires_at).total_seconds()),
    )
    return ("overdue", seconds_until_due, seconds_overdue, window_remaining_seconds)
