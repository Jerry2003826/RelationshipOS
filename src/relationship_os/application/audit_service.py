from collections import Counter
from typing import Any

from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_types import TRACE_EVENT_TYPES


class AuditService:
    def __init__(self, *, stream_service: StreamService) -> None:
        self._stream_service = stream_service

    async def get_session_audit(self, *, session_id: str) -> dict[str, Any]:
        events = await self._stream_service.read_stream(stream_id=session_id)
        runtime_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
        )
        replay = await self._stream_service.replay_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
        )

        event_type_counts = Counter(event.event_type for event in events)
        state = runtime_projection["state"]
        return {
            "session_id": session_id,
            "event_count": len(events),
            "trace_event_count": sum(
                1 for event in events if event.event_type in TRACE_EVENT_TYPES
            ),
            "fingerprint": replay["fingerprint"],
            "consistent": replay["consistent"],
            "event_type_counts": dict(sorted(event_type_counts.items())),
            "last_llm_failure": state.get("last_llm_failure"),
            "last_background_job": state.get("last_background_job"),
            "latest_snapshot": state.get("latest_snapshot"),
            "archive_status": state.get("archive_status"),
            "offline_consolidation": state.get("offline_consolidation"),
            "runtime_coordination_snapshot": state.get("runtime_coordination_snapshot"),
            "guidance_plan": state.get("guidance_plan"),
            "conversation_cadence_plan": state.get("conversation_cadence_plan"),
            "session_ritual_plan": state.get("session_ritual_plan"),
            "somatic_orchestration_plan": state.get("somatic_orchestration_plan"),
            "proactive_followup_directive": state.get("proactive_followup_directive"),
            "proactive_cadence_plan": state.get("proactive_cadence_plan"),
            "proactive_aggregate_governance_assessment": state.get(
                "proactive_aggregate_governance_assessment"
            ),
            "proactive_aggregate_controller_decision": state.get(
                "proactive_aggregate_controller_decision"
            ),
            "proactive_orchestration_controller_decision": state.get(
                "proactive_orchestration_controller_decision"
            ),
            "reengagement_matrix_assessment": state.get(
                "reengagement_matrix_assessment"
            ),
            "reengagement_plan": state.get("reengagement_plan"),
            "proactive_scheduling_plan": state.get("proactive_scheduling_plan"),
            "proactive_guardrail_plan": state.get("proactive_guardrail_plan"),
            "proactive_orchestration_plan": state.get("proactive_orchestration_plan"),
            "proactive_actuation_plan": state.get("proactive_actuation_plan"),
            "proactive_progression_plan": state.get("proactive_progression_plan"),
            "proactive_stage_controller_decision": state.get(
                "proactive_stage_controller_decision"
            ),
            "proactive_line_controller_decision": state.get(
                "proactive_line_controller_decision"
            ),
            "proactive_line_state_decision": state.get("proactive_line_state_decision"),
            "proactive_line_transition_decision": state.get(
                "proactive_line_transition_decision"
            ),
            "proactive_line_machine_decision": state.get(
                "proactive_line_machine_decision"
            ),
            "proactive_lifecycle_state_decision": state.get(
                "proactive_lifecycle_state_decision"
            ),
            "proactive_lifecycle_transition_decision": state.get(
                "proactive_lifecycle_transition_decision"
            ),
            "proactive_lifecycle_machine_decision": state.get(
                "proactive_lifecycle_machine_decision"
            ),
            "proactive_lifecycle_controller_decision": state.get(
                "proactive_lifecycle_controller_decision"
            ),
            "proactive_lifecycle_envelope_decision": state.get(
                "proactive_lifecycle_envelope_decision"
            ),
            "proactive_lifecycle_scheduler_decision": state.get(
                "proactive_lifecycle_scheduler_decision"
            ),
            "proactive_lifecycle_window_decision": state.get(
                "proactive_lifecycle_window_decision"
            ),
            "proactive_lifecycle_queue_decision": state.get(
                "proactive_lifecycle_queue_decision"
            ),
            "proactive_lifecycle_dispatch_decision": state.get(
                "proactive_lifecycle_dispatch_decision"
            ),
            "proactive_lifecycle_outcome_decision": state.get(
                "proactive_lifecycle_outcome_decision"
            ),
            "proactive_lifecycle_resolution_decision": state.get(
                "proactive_lifecycle_resolution_decision"
            ),
            "proactive_lifecycle_activation_decision": state.get(
                "proactive_lifecycle_activation_decision"
            ),
            "proactive_lifecycle_settlement_decision": state.get(
                "proactive_lifecycle_settlement_decision"
            ),
            "proactive_lifecycle_closure_decision": state.get(
                "proactive_lifecycle_closure_decision"
            ),
            "proactive_lifecycle_availability_decision": state.get(
                "proactive_lifecycle_availability_decision"
            ),
            "proactive_lifecycle_retention_decision": state.get(
                "proactive_lifecycle_retention_decision"
            ),
            "proactive_lifecycle_eligibility_decision": state.get(
                "proactive_lifecycle_eligibility_decision"
            ),
            "proactive_lifecycle_candidate_decision": state.get(
                "proactive_lifecycle_candidate_decision"
            ),
            "proactive_lifecycle_selectability_decision": state.get(
                "proactive_lifecycle_selectability_decision"
            ),
            "proactive_lifecycle_reentry_decision": state.get(
                "proactive_lifecycle_reentry_decision"
            ),
            "proactive_lifecycle_reactivation_decision": state.get(
                "proactive_lifecycle_reactivation_decision"
            ),
            "proactive_lifecycle_resumption_decision": state.get(
                "proactive_lifecycle_resumption_decision"
            ),
            "proactive_lifecycle_readiness_decision": state.get(
                "proactive_lifecycle_readiness_decision"
            ),
            "proactive_lifecycle_arming_decision": state.get(
                "proactive_lifecycle_arming_decision"
            ),
            "proactive_lifecycle_trigger_decision": state.get(
                "proactive_lifecycle_trigger_decision"
            ),
            "proactive_lifecycle_launch_decision": state.get(
                "proactive_lifecycle_launch_decision"
            ),
            "proactive_lifecycle_handoff_decision": state.get(
                "proactive_lifecycle_handoff_decision"
            ),
            "proactive_lifecycle_continuation_decision": state.get(
                "proactive_lifecycle_continuation_decision"
            ),
            "proactive_lifecycle_sustainment_decision": state.get(
                "proactive_lifecycle_sustainment_decision"
            ),
            "proactive_lifecycle_stewardship_decision": state.get(
                "proactive_lifecycle_stewardship_decision"
            ),
            "proactive_lifecycle_guardianship_decision": state.get(
                "proactive_lifecycle_guardianship_decision"
            ),
            "proactive_lifecycle_oversight_decision": state.get(
                "proactive_lifecycle_oversight_decision"
            ),
            "proactive_lifecycle_assurance_decision": state.get(
                "proactive_lifecycle_assurance_decision"
            ),
            "proactive_lifecycle_attestation_decision": state.get(
            "proactive_lifecycle_attestation_decision"
        ),
        "proactive_lifecycle_verification_decision": state.get(
            "proactive_lifecycle_verification_decision"
        ),
        "proactive_lifecycle_certification_decision": state.get(
            "proactive_lifecycle_certification_decision"
        ),
        "proactive_lifecycle_confirmation_decision": state.get(
            "proactive_lifecycle_confirmation_decision"
        ),
        "proactive_lifecycle_ratification_decision": state.get(
            "proactive_lifecycle_ratification_decision"
        ),
        "proactive_lifecycle_endorsement_decision": state.get(
            "proactive_lifecycle_endorsement_decision"
        ),
        "proactive_lifecycle_authorization_decision": state.get(
            "proactive_lifecycle_authorization_decision"
        ),
        "proactive_lifecycle_enactment_decision": state.get(
            "proactive_lifecycle_enactment_decision"
        ),
        "proactive_lifecycle_finality_decision": state.get(
            "proactive_lifecycle_finality_decision"
        ),
        "proactive_lifecycle_completion_decision": state.get(
            "proactive_lifecycle_completion_decision"
        ),
        "proactive_lifecycle_conclusion_decision": state.get(
            "proactive_lifecycle_conclusion_decision"
        ),
        "proactive_lifecycle_disposition_decision": state.get(
            "proactive_lifecycle_disposition_decision"
        ),
        "proactive_lifecycle_standing_decision": state.get(
            "proactive_lifecycle_standing_decision"
        ),
        "proactive_lifecycle_residency_decision": state.get(
            "proactive_lifecycle_residency_decision"
        ),
        "proactive_lifecycle_tenure_decision": state.get(
            "proactive_lifecycle_tenure_decision"
        ),
        "proactive_lifecycle_persistence_decision": state.get(
            "proactive_lifecycle_persistence_decision"
        ),
        "proactive_lifecycle_durability_decision": state.get(
            "proactive_lifecycle_durability_decision"
        ),
        "proactive_lifecycle_longevity_decision": state.get(
            "proactive_lifecycle_longevity_decision"
        ),
        "proactive_lifecycle_legacy_decision": state.get(
            "proactive_lifecycle_legacy_decision"
        ),
        "proactive_lifecycle_heritage_decision": state.get(
            "proactive_lifecycle_heritage_decision"
        ),
        "proactive_lifecycle_lineage_decision": state.get(
            "proactive_lifecycle_lineage_decision"
        ),
        "proactive_lifecycle_ancestry_decision": state.get(
            "proactive_lifecycle_ancestry_decision"
        ),
        "proactive_lifecycle_provenance_decision": state.get(
            "proactive_lifecycle_provenance_decision"
        ),
        "proactive_lifecycle_origin_decision": state.get(
            "proactive_lifecycle_origin_decision"
        ),
        "proactive_lifecycle_root_decision": state.get(
            "proactive_lifecycle_root_decision"
        ),
        "proactive_lifecycle_foundation_decision": state.get(
            "proactive_lifecycle_foundation_decision"
        ),
        "proactive_lifecycle_bedrock_decision": state.get(
            "proactive_lifecycle_bedrock_decision"
        ),
        "proactive_lifecycle_substrate_decision": state.get(
            "proactive_lifecycle_substrate_decision"
        ),
        "proactive_lifecycle_stratum_decision": state.get(
            "proactive_lifecycle_stratum_decision"
        ),
        "proactive_lifecycle_layer_decision": state.get(
            "proactive_lifecycle_layer_decision"
        ),
        "proactive_stage_refresh_plan": state.get("proactive_stage_refresh_plan"),
            "proactive_stage_replan_assessment": state.get(
                "proactive_stage_replan_assessment"
            ),
            "proactive_dispatch_feedback_assessment": state.get(
                "proactive_dispatch_feedback_assessment"
            ),
            "proactive_dispatch_gate_decision": state.get(
                "proactive_dispatch_gate_decision"
            ),
            "proactive_dispatch_envelope_decision": state.get(
                "proactive_dispatch_envelope_decision"
            ),
            "proactive_stage_state_decision": state.get(
                "proactive_stage_state_decision"
            ),
            "proactive_stage_transition_decision": state.get(
                "proactive_stage_transition_decision"
            ),
            "proactive_stage_machine_decision": state.get(
                "proactive_stage_machine_decision"
            ),
            "last_proactive_followup_dispatch": state.get(
                "last_proactive_followup_dispatch"
            ),
            "last_runtime_quality_doctor": state.get("last_runtime_quality_doctor"),
            "system3_snapshot": state.get("system3_snapshot"),
        }

    async def list_archived_sessions(self) -> dict[str, Any]:
        archived_sessions: list[dict[str, Any]] = []
        session_ids = await self._stream_service.list_stream_ids()
        for session_id in session_ids:
            projection = await self._stream_service.project_stream(
                stream_id=session_id,
                projector_name="session-runtime",
                projector_version="v1",
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
