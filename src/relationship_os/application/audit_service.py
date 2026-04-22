from collections import Counter
from typing import Any

from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
    has_legacy_lifecycle_events,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_types import (
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
    is_trace_event_type,
)

_AUDIT_STATE_FIELDS = (
    "last_llm_failure",
    "last_background_job",
    "latest_snapshot",
    "archive_status",
    "offline_consolidation",
    "runtime_coordination_snapshot",
    "guidance_plan",
    "conversation_cadence_plan",
    "session_ritual_plan",
    "somatic_orchestration_plan",
    "proactive_followup_directive",
    "proactive_cadence_plan",
    "proactive_aggregate_governance_assessment",
    "proactive_aggregate_controller_decision",
    "proactive_orchestration_controller_decision",
    "reengagement_matrix_assessment",
    "reengagement_plan",
    "proactive_scheduling_plan",
    "proactive_guardrail_plan",
    "proactive_orchestration_plan",
    "proactive_actuation_plan",
    "proactive_progression_plan",
    "proactive_stage_controller_decision",
    "proactive_line_controller_decision",
    "proactive_line_state_decision",
    "proactive_line_transition_decision",
    "proactive_line_machine_decision",
    "proactive_lifecycle_state_decision",
    "proactive_lifecycle_transition_decision",
    "proactive_lifecycle_machine_decision",
    "proactive_lifecycle_controller_decision",
    "proactive_lifecycle_envelope_decision",
    "proactive_lifecycle_scheduler_decision",
    "proactive_lifecycle_window_decision",
    "proactive_lifecycle_queue_decision",
    "proactive_lifecycle_dispatch_decision",
    "proactive_lifecycle_outcome_decision",
    "proactive_lifecycle_resolution_decision",
    "proactive_lifecycle_activation_decision",
    "proactive_lifecycle_settlement_decision",
    "proactive_lifecycle_closure_decision",
    "proactive_lifecycle_availability_decision",
    "proactive_lifecycle_retention_decision",
    "proactive_lifecycle_eligibility_decision",
    "proactive_lifecycle_candidate_decision",
    "proactive_lifecycle_selectability_decision",
    "proactive_lifecycle_reentry_decision",
    "proactive_lifecycle_reactivation_decision",
    "proactive_lifecycle_resumption_decision",
    "proactive_lifecycle_readiness_decision",
    "proactive_lifecycle_arming_decision",
    "proactive_lifecycle_trigger_decision",
    "proactive_lifecycle_launch_decision",
    "proactive_lifecycle_handoff_decision",
    "proactive_lifecycle_continuation_decision",
    "proactive_lifecycle_sustainment_decision",
    "proactive_lifecycle_stewardship_decision",
    "proactive_lifecycle_guardianship_decision",
    "proactive_lifecycle_oversight_decision",
    "proactive_lifecycle_assurance_decision",
    "proactive_lifecycle_attestation_decision",
    "proactive_lifecycle_verification_decision",
    "proactive_lifecycle_certification_decision",
    "proactive_lifecycle_confirmation_decision",
    "proactive_lifecycle_ratification_decision",
    "proactive_lifecycle_endorsement_decision",
    "proactive_lifecycle_authorization_decision",
    "proactive_lifecycle_enactment_decision",
    "proactive_lifecycle_finality_decision",
    "proactive_lifecycle_completion_decision",
    "proactive_lifecycle_conclusion_decision",
    "proactive_lifecycle_disposition_decision",
    "proactive_lifecycle_standing_decision",
    "proactive_lifecycle_residency_decision",
    "proactive_lifecycle_tenure_decision",
    "proactive_lifecycle_persistence_decision",
    "proactive_lifecycle_durability_decision",
    "proactive_lifecycle_longevity_decision",
    "proactive_lifecycle_legacy_decision",
    "proactive_lifecycle_heritage_decision",
    "proactive_lifecycle_lineage_decision",
    "proactive_lifecycle_ancestry_decision",
    "proactive_lifecycle_provenance_decision",
    "proactive_lifecycle_origin_decision",
    "proactive_lifecycle_root_decision",
    "proactive_lifecycle_foundation_decision",
    "proactive_lifecycle_bedrock_decision",
    "proactive_lifecycle_substrate_decision",
    "proactive_lifecycle_stratum_decision",
    "proactive_lifecycle_layer_decision",
    "proactive_stage_refresh_plan",
    "proactive_stage_replan_assessment",
    "proactive_dispatch_feedback_assessment",
    "proactive_dispatch_gate_decision",
    "proactive_dispatch_envelope_decision",
    "proactive_stage_state_decision",
    "proactive_stage_transition_decision",
    "proactive_stage_machine_decision",
    "last_proactive_followup_dispatch",
    "last_runtime_quality_doctor",
    "system3_snapshot",
    "proactive_lifecycle_snapshot",
)


class AuditService:
    def __init__(
        self,
        *,
        stream_service: StreamService,
        runtime_projector_version: str = "v2",
    ) -> None:
        self._stream_service = stream_service
        self._runtime_projector_version = runtime_projector_version

    async def get_session_audit(
        self,
        *,
        session_id: str,
        projector_version: str | None = None,
    ) -> dict[str, Any]:
        events = await self._stream_service.read_stream(stream_id=session_id)
        resolved_version = projector_version or self._runtime_projector_version
        event_type_counts = Counter(event.event_type for event in events)
        lifecycle_snapshot_count = sum(
            1 for event in events if event.event_type == PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED
        )
        payload: dict[str, Any] = {
            "session_id": session_id,
            "projector_version": resolved_version,
            "event_count": len(events),
            "trace_event_count": sum(
                1 for event in events if is_trace_event_type(event.event_type)
            ),
            "lifecycle_snapshot_count": lifecycle_snapshot_count,
            "event_type_counts": dict(sorted(event_type_counts.items())),
        }
        if has_legacy_lifecycle_events(events):
            payload.update(
                {
                    "projection_supported": False,
                    "projection_error": LegacyLifecycleStreamUnsupportedError(
                        stream_id=session_id
                    ).response_detail(),
                    "fingerprint": None,
                    "consistent": None,
                }
            )
            payload.update({field: None for field in _AUDIT_STATE_FIELDS})
            return payload

        runtime_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version=resolved_version,
        )
        replay = await self._stream_service.replay_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version=resolved_version,
        )
        state = runtime_projection["state"]
        payload.update(
            {
                "projection_supported": True,
                "projection_error": None,
                "fingerprint": replay["fingerprint"],
                "consistent": replay["consistent"],
            }
        )
        payload.update({field: state.get(field) for field in _AUDIT_STATE_FIELDS})
        return payload

    async def list_archived_sessions(self) -> dict[str, Any]:
        archived_sessions: list[dict[str, Any]] = []
        session_ids = await self._stream_service.list_stream_ids()
        for session_id in session_ids:
            events = await self._stream_service.read_stream(stream_id=session_id)
            if has_legacy_lifecycle_events(events):
                continue
            projection = await self._stream_service.project_stream(
                stream_id=session_id,
                projector_name="session-runtime",
                projector_version=self._runtime_projector_version,
            )
            state = projection["state"]
            archive_status = state.get("archive_status", {})
            if not isinstance(archive_status, dict) or not archive_status.get("archived"):
                continue
            archived_sessions.append(
                {
                    "session_id": session_id,
                    "archived_at": archive_status.get("archived_at"),
                    "reason": archive_status.get("reason"),
                    "snapshot_id": archive_status.get("snapshot_id"),
                    "latest_snapshot": state.get("latest_snapshot"),
                }
            )

        archived_sessions.sort(
            key=lambda item: str(item.get("archived_at") or ""),
            reverse=True,
        )
        return {
            "archive_count": len(archived_sessions),
            "sessions": archived_sessions,
        }
