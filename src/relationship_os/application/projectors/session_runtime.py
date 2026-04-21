"""SessionRuntimeProjector — full session runtime state materialization."""

from typing import Any

from relationship_os.application.analyzers.proactive.lifecycle_phase_specs import (
    LIFECYCLE_PHASE_SPECS,
)
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
    apply_snapshot_to_runtime_state,
    is_legacy_lifecycle_event_type,
)
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_STARTED,
    CONFIDENCE_ASSESSMENT_COMPUTED,
    CONTEXT_FRAME_COMPUTED,
    CONVERSATION_CADENCE_UPDATED,
    EMPOWERMENT_AUDIT_COMPLETED,
    GUIDANCE_PLAN_UPDATED,
    INNER_MONOLOGUE_RECORDED,
    KNOWLEDGE_BOUNDARY_DECIDED,
    LLM_COMPLETION_FAILED,
    MEMORY_BUNDLE_UPDATED,
    MEMORY_FORGETTING_APPLIED,
    MEMORY_RECALL_PERFORMED,
    MEMORY_RETENTION_POLICY_APPLIED,
    MEMORY_WRITE_GUARD_EVALUATED,
    OFFLINE_CONSOLIDATION_COMPLETED,
    POLICY_GATE_DECIDED,
    PRIVATE_JUDGMENT_COMPUTED,
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_CADENCE_UPDATED,
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_GUARDRAIL_UPDATED,
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_LINE_MACHINE_UPDATED,
    PROACTIVE_LINE_STATE_UPDATED,
    PROACTIVE_LINE_TRANSITION_UPDATED,
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_MACHINE_UPDATED,
    PROACTIVE_STAGE_REFRESH_UPDATED,
    PROACTIVE_STAGE_REPLAN_UPDATED,
    PROACTIVE_STAGE_STATE_UPDATED,
    PROACTIVE_STAGE_TRANSITION_UPDATED,
    REENGAGEMENT_MATRIX_ASSESSED,
    REENGAGEMENT_PLAN_UPDATED,
    REHEARSAL_COMPLETED,
    RELATIONSHIP_STATE_UPDATED,
    REPAIR_ASSESSMENT_COMPUTED,
    REPAIR_PLAN_UPDATED,
    RESPONSE_DRAFT_PLANNED,
    RESPONSE_NORMALIZED,
    RESPONSE_POST_AUDITED,
    RESPONSE_RENDERING_POLICY_DECIDED,
    RESPONSE_SEQUENCE_PLANNED,
    RUNTIME_COORDINATION_UPDATED,
    RUNTIME_QUALITY_DOCTOR_COMPLETED,
    SESSION_ARCHIVED,
    SESSION_DIRECTIVE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SESSION_SNAPSHOT_CREATED,
    SESSION_STARTED,
    SOMATIC_ORCHESTRATION_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector

_DIRECT_PAYLOAD_EVENT_FIELDS = {
    CONTEXT_FRAME_COMPUTED: "context_frame",
    RELATIONSHIP_STATE_UPDATED: "relationship_state",
    CONFIDENCE_ASSESSMENT_COMPUTED: "confidence_assessment",
    REPAIR_ASSESSMENT_COMPUTED: "repair_assessment",
    MEMORY_BUNDLE_UPDATED: "memory_bundle",
    MEMORY_WRITE_GUARD_EVALUATED: "last_memory_write_guard",
    MEMORY_RETENTION_POLICY_APPLIED: "last_memory_retention",
    MEMORY_RECALL_PERFORMED: "last_memory_recall",
    MEMORY_FORGETTING_APPLIED: "last_memory_forgetting",
    KNOWLEDGE_BOUNDARY_DECIDED: "knowledge_boundary_decision",
    POLICY_GATE_DECIDED: "policy_gate",
    REHEARSAL_COMPLETED: "rehearsal_result",
    REPAIR_PLAN_UPDATED: "repair_plan",
    EMPOWERMENT_AUDIT_COMPLETED: "empowerment_audit",
    RESPONSE_DRAFT_PLANNED: "response_draft_plan",
    RESPONSE_RENDERING_POLICY_DECIDED: "response_rendering_policy",
    RESPONSE_SEQUENCE_PLANNED: "response_sequence_plan",
    RESPONSE_POST_AUDITED: "response_post_audit",
    RESPONSE_NORMALIZED: "response_normalization",
    PRIVATE_JUDGMENT_COMPUTED: "private_judgment",
    LLM_COMPLETION_FAILED: "last_llm_failure",
    OFFLINE_CONSOLIDATION_COMPLETED: "offline_consolidation",
    SESSION_SNAPSHOT_CREATED: "latest_snapshot",
}

_COUNTED_PAYLOAD_EVENT_FIELDS = {
    RUNTIME_QUALITY_DOCTOR_COMPLETED: (
        "last_runtime_quality_doctor",
        "runtime_quality_doctor_report_count",
    ),
    RUNTIME_COORDINATION_UPDATED: (
        "runtime_coordination_snapshot",
        "runtime_coordination_snapshot_count",
    ),
    GUIDANCE_PLAN_UPDATED: ("guidance_plan", "guidance_plan_count"),
    CONVERSATION_CADENCE_UPDATED: (
        "conversation_cadence_plan",
        "conversation_cadence_plan_count",
    ),
    SESSION_RITUAL_UPDATED: ("session_ritual_plan", "session_ritual_plan_count"),
    SOMATIC_ORCHESTRATION_UPDATED: (
        "somatic_orchestration_plan",
        "somatic_orchestration_plan_count",
    ),
    PROACTIVE_FOLLOWUP_UPDATED: (
        "proactive_followup_directive",
        "proactive_followup_directive_count",
    ),
    PROACTIVE_CADENCE_UPDATED: (
        "proactive_cadence_plan",
        "proactive_cadence_plan_count",
    ),
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED: (
        "proactive_aggregate_governance_assessment",
        "proactive_aggregate_governance_assessment_count",
    ),
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED: (
        "proactive_aggregate_controller_decision",
        "proactive_aggregate_controller_decision_count",
    ),
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED: (
        "proactive_orchestration_controller_decision",
        "proactive_orchestration_controller_decision_count",
    ),
    REENGAGEMENT_MATRIX_ASSESSED: (
        "reengagement_matrix_assessment",
        "reengagement_matrix_assessment_count",
    ),
    REENGAGEMENT_PLAN_UPDATED: ("reengagement_plan", "reengagement_plan_count"),
    PROACTIVE_SCHEDULING_UPDATED: (
        "proactive_scheduling_plan",
        "proactive_scheduling_plan_count",
    ),
    PROACTIVE_GUARDRAIL_UPDATED: (
        "proactive_guardrail_plan",
        "proactive_guardrail_plan_count",
    ),
    PROACTIVE_ORCHESTRATION_UPDATED: (
        "proactive_orchestration_plan",
        "proactive_orchestration_plan_count",
    ),
    PROACTIVE_ACTUATION_UPDATED: (
        "proactive_actuation_plan",
        "proactive_actuation_plan_count",
    ),
    PROACTIVE_PROGRESSION_UPDATED: (
        "proactive_progression_plan",
        "proactive_progression_plan_count",
    ),
    PROACTIVE_STAGE_CONTROLLER_UPDATED: (
        "proactive_stage_controller_decision",
        "proactive_stage_controller_decision_count",
    ),
    PROACTIVE_LINE_CONTROLLER_UPDATED: (
        "proactive_line_controller_decision",
        "proactive_line_controller_decision_count",
    ),
    PROACTIVE_LINE_STATE_UPDATED: (
        "proactive_line_state_decision",
        "proactive_line_state_decision_count",
    ),
    PROACTIVE_LINE_TRANSITION_UPDATED: (
        "proactive_line_transition_decision",
        "proactive_line_transition_decision_count",
    ),
    PROACTIVE_LINE_MACHINE_UPDATED: (
        "proactive_line_machine_decision",
        "proactive_line_machine_decision_count",
    ),
    PROACTIVE_STAGE_REFRESH_UPDATED: (
        "proactive_stage_refresh_plan",
        "proactive_stage_refresh_plan_count",
    ),
    PROACTIVE_STAGE_REPLAN_UPDATED: (
        "proactive_stage_replan_assessment",
        "proactive_stage_replan_assessment_count",
    ),
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED: (
        "proactive_dispatch_feedback_assessment",
        "proactive_dispatch_feedback_assessment_count",
    ),
    PROACTIVE_DISPATCH_GATE_UPDATED: (
        "proactive_dispatch_gate_decision",
        "proactive_dispatch_gate_decision_count",
    ),
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED: (
        "proactive_dispatch_envelope_decision",
        "proactive_dispatch_envelope_decision_count",
    ),
    PROACTIVE_STAGE_STATE_UPDATED: (
        "proactive_stage_state_decision",
        "proactive_stage_state_decision_count",
    ),
    PROACTIVE_STAGE_TRANSITION_UPDATED: (
        "proactive_stage_transition_decision",
        "proactive_stage_transition_decision_count",
    ),
    PROACTIVE_STAGE_MACHINE_UPDATED: (
        "proactive_stage_machine_decision",
        "proactive_stage_machine_decision_count",
    ),
    PROACTIVE_FOLLOWUP_DISPATCHED: (
        "last_proactive_followup_dispatch",
        "proactive_followup_dispatch_count",
    ),
    SYSTEM3_SNAPSHOT_UPDATED: ("system3_snapshot", "system3_snapshot_count"),
}

_BACKGROUND_JOB_EVENT_TYPES = {
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_STARTED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
}


def _build_lifecycle_runtime_defaults() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "proactive_lifecycle_snapshot": None,
        "proactive_lifecycle_snapshot_count": 0,
    }
    for spec in LIFECYCLE_PHASE_SPECS:
        defaults[spec.state_field] = None
        defaults[spec.count_field] = 0
    return defaults


def _build_simple_payload_defaults() -> dict[str, Any]:
    return {field_name: None for field_name in _DIRECT_PAYLOAD_EVENT_FIELDS.values()}


def _build_counted_payload_defaults() -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for field_name, count_field in _COUNTED_PAYLOAD_EVENT_FIELDS.values():
        defaults[field_name] = None
        defaults[count_field] = 0
    return defaults


def _apply_payload_field(
    next_state: dict[str, Any],
    event: StoredEvent,
    *,
    field_name: str,
) -> dict[str, Any]:
    next_state[field_name] = dict(event.payload)
    return next_state


def _apply_counted_payload_field(
    next_state: dict[str, Any],
    event: StoredEvent,
    *,
    field_name: str,
    count_field: str,
) -> dict[str, Any]:
    next_state[field_name] = dict(event.payload)
    next_state[count_field] = int(next_state.get(count_field, 0)) + 1
    return next_state


def _apply_message_event(
    next_state: dict[str, Any],
    event: StoredEvent,
) -> dict[str, Any]:
    role = "user" if event.event_type == USER_MESSAGE_RECEIVED else "assistant"
    next_state["messages"].append(
        {
            "role": role,
            "content": event.payload.get("content", ""),
            "delivery_mode": event.payload.get("delivery_mode"),
            "version": event.version,
            "occurred_at": event.occurred_at.isoformat(),
        }
    )
    next_state["messages"] = next_state["messages"][-500:]
    if event.event_type == USER_MESSAGE_RECEIVED:
        next_state["turn_count"] += 1
    return next_state


def _apply_session_started(
    next_state: dict[str, Any],
    event: StoredEvent,
) -> dict[str, Any]:
    next_state["session"] = {
        "started": True,
        "session_id": event.payload.get("session_id", event.stream_id),
        "created_at": event.payload.get("created_at"),
        "metadata": dict(event.payload.get("metadata", {})),
        "user_id": event.payload.get("user_id"),
    }
    return next_state


def _apply_session_archived(
    next_state: dict[str, Any],
    event: StoredEvent,
) -> dict[str, Any]:
    next_state["archive_status"] = {
        "archived": bool(event.payload.get("archived", True)),
        "archived_at": event.payload.get("archived_at"),
        "reason": event.payload.get("reason"),
        "snapshot_id": event.payload.get("snapshot_id"),
    }
    return next_state


def _apply_inner_monologue_event(
    next_state: dict[str, Any],
    event: StoredEvent,
) -> dict[str, Any]:
    next_state["inner_monologue"].extend(list(event.payload.get("entries", [])))
    next_state["inner_monologue"] = next_state["inner_monologue"][-200:]
    return next_state


def _apply_session_directive_updated(
    next_state: dict[str, Any],
    event: StoredEvent,
) -> dict[str, Any]:
    next_state["session_directive"] = dict(event.payload.get("directive", {}))
    next_state["confidence_assessment"] = dict(event.payload.get("confidence", {}))
    next_state["strategy_decision"] = dict(event.payload.get("strategy", {}))
    strategy_name = str((event.payload.get("strategy", {}) or {}).get("strategy", "")).strip()
    if strategy_name:
        next_state["strategy_history"].append(strategy_name)
        next_state["strategy_history"] = next_state["strategy_history"][-8:]
    next_state["expression_plan"] = dict(event.payload.get("expression_plan", {}))
    next_state["guidance_plan"] = dict(event.payload.get("guidance_plan", {}))
    next_state["conversation_cadence_plan"] = dict(
        event.payload.get("conversation_cadence_plan", {})
    )
    next_state["session_ritual_plan"] = dict(event.payload.get("session_ritual_plan", {}))
    next_state["somatic_orchestration_plan"] = dict(
        event.payload.get("somatic_orchestration_plan", {})
    )
    next_state["proactive_cadence_plan"] = dict(event.payload.get("proactive_cadence_plan", {}))
    next_state["response_draft_plan"] = dict(event.payload.get("response_draft_plan", {}))
    next_state["response_rendering_policy"] = dict(
        event.payload.get("response_rendering_policy", {})
    )
    return next_state


class SessionRuntimeProjector(Projector[dict[str, Any]]):
    name = "session-runtime"
    version = "v2"

    def initial_state(self) -> dict[str, Any]:
        return {
            "session": {
                "started": False,
                "session_id": None,
                "created_at": None,
                "metadata": {},
            },
            "messages": [],
            **_build_simple_payload_defaults(),
            **_build_counted_payload_defaults(),
            **_build_lifecycle_runtime_defaults(),
            "session_directive": None,
            "strategy_decision": None,
            "strategy_history": [],
            "expression_plan": None,
            "inner_monologue": [],
            "last_background_job": None,
            "archive_status": {
                "archived": False,
                "archived_at": None,
                "reason": None,
                "snapshot_id": None,
            },
            "turn_count": 0,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            **state,
            "session": dict(state["session"]),
            "messages": list(state["messages"]),
            "inner_monologue": list(state["inner_monologue"]),
            "strategy_history": list(state.get("strategy_history", [])),
        }
        event_type = event.event_type

        if event_type == SESSION_STARTED:
            return _apply_session_started(next_state, event)

        if event_type in {USER_MESSAGE_RECEIVED, ASSISTANT_MESSAGE_SENT}:
            return _apply_message_event(next_state, event)

        if is_legacy_lifecycle_event_type(event_type):
            raise LegacyLifecycleStreamUnsupportedError(stream_id=event.stream_id)
        if event_type == PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED:
            return apply_snapshot_to_runtime_state(next_state, dict(event.payload))

        simple_field = _DIRECT_PAYLOAD_EVENT_FIELDS.get(event_type)
        if simple_field is not None:
            return _apply_payload_field(next_state, event, field_name=simple_field)

        counted_fields = _COUNTED_PAYLOAD_EVENT_FIELDS.get(event_type)
        if counted_fields is not None:
            field_name, count_field = counted_fields
            return _apply_counted_payload_field(
                next_state,
                event,
                field_name=field_name,
                count_field=count_field,
            )

        if event_type == INNER_MONOLOGUE_RECORDED:
            return _apply_inner_monologue_event(next_state, event)

        if event_type in _BACKGROUND_JOB_EVENT_TYPES:
            next_state["last_background_job"] = dict(event.payload)
            return next_state

        if event_type == SESSION_ARCHIVED:
            return _apply_session_archived(next_state, event)

        if event_type == SESSION_DIRECTIVE_UPDATED:
            return _apply_session_directive_updated(next_state, event)

        return next_state
