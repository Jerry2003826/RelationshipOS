"""SessionRuntimeProjector — full session runtime state materialization."""

from typing import Any

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
    PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED,
    PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED,
    PROACTIVE_LIFECYCLE_ARMING_UPDATED,
    PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED,
    PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED,
    PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED,
    PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_BEDROCK_UPDATED,
    PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED,
    PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_CLOSURE_UPDATED,
    PROACTIVE_LIFECYCLE_COMPLETION_UPDATED,
    PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED,
    PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED,
    PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED,
    PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED,
    PROACTIVE_LIFECYCLE_DISPATCH_UPDATED,
    PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED,
    PROACTIVE_LIFECYCLE_DURABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED,
    PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED,
    PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED,
    PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED,
    PROACTIVE_LIFECYCLE_FINALITY_UPDATED,
    PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED,
    PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED,
    PROACTIVE_LIFECYCLE_HANDOFF_UPDATED,
    PROACTIVE_LIFECYCLE_HERITAGE_UPDATED,
    PROACTIVE_LIFECYCLE_LAUNCH_UPDATED,
    PROACTIVE_LIFECYCLE_LAYER_UPDATED,
    PROACTIVE_LIFECYCLE_LEGACY_UPDATED,
    PROACTIVE_LIFECYCLE_LINEAGE_UPDATED,
    PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED,
    PROACTIVE_LIFECYCLE_MACHINE_UPDATED,
    PROACTIVE_LIFECYCLE_ORIGIN_UPDATED,
    PROACTIVE_LIFECYCLE_OUTCOME_UPDATED,
    PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED,
    PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED,
    PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED,
    PROACTIVE_LIFECYCLE_QUEUE_UPDATED,
    PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED,
    PROACTIVE_LIFECYCLE_READINESS_UPDATED,
    PROACTIVE_LIFECYCLE_REENTRY_UPDATED,
    PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED,
    PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED,
    PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED,
    PROACTIVE_LIFECYCLE_RETENTION_UPDATED,
    PROACTIVE_LIFECYCLE_ROOT_UPDATED,
    PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED,
    PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED,
    PROACTIVE_LIFECYCLE_STANDING_UPDATED,
    PROACTIVE_LIFECYCLE_STATE_UPDATED,
    PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED,
    PROACTIVE_LIFECYCLE_STRATUM_UPDATED,
    PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED,
    PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED,
    PROACTIVE_LIFECYCLE_TENURE_UPDATED,
    PROACTIVE_LIFECYCLE_TRANSITION_UPDATED,
    PROACTIVE_LIFECYCLE_TRIGGER_UPDATED,
    PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_WINDOW_UPDATED,
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


class SessionRuntimeProjector(Projector[dict[str, Any]]):
    name = "session-runtime"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "session": {
                "started": False,
                "session_id": None,
                "created_at": None,
                "metadata": {},
            },
            "messages": [],
            "context_frame": None,
            "relationship_state": None,
            "repair_assessment": None,
            "memory_bundle": None,
            "last_memory_write_guard": None,
            "last_memory_retention": None,
            "last_memory_recall": None,
            "last_memory_forgetting": None,
            "knowledge_boundary_decision": None,
            "policy_gate": None,
            "rehearsal_result": None,
            "repair_plan": None,
            "empowerment_audit": None,
            "response_draft_plan": None,
            "response_rendering_policy": None,
            "response_sequence_plan": None,
            "response_post_audit": None,
            "response_normalization": None,
            "runtime_coordination_snapshot": None,
            "runtime_coordination_snapshot_count": 0,
            "guidance_plan": None,
            "guidance_plan_count": 0,
            "conversation_cadence_plan": None,
            "conversation_cadence_plan_count": 0,
            "session_ritual_plan": None,
            "session_ritual_plan_count": 0,
            "somatic_orchestration_plan": None,
            "somatic_orchestration_plan_count": 0,
            "proactive_followup_directive": None,
            "proactive_followup_directive_count": 0,
            "proactive_cadence_plan": None,
            "proactive_cadence_plan_count": 0,
            "proactive_aggregate_governance_assessment": None,
            "proactive_aggregate_governance_assessment_count": 0,
            "proactive_aggregate_controller_decision": None,
            "proactive_aggregate_controller_decision_count": 0,
            "proactive_orchestration_controller_decision": None,
            "proactive_orchestration_controller_decision_count": 0,
            "reengagement_matrix_assessment": None,
            "reengagement_matrix_assessment_count": 0,
            "reengagement_plan": None,
            "reengagement_plan_count": 0,
            "proactive_scheduling_plan": None,
            "proactive_scheduling_plan_count": 0,
            "proactive_guardrail_plan": None,
            "proactive_guardrail_plan_count": 0,
            "proactive_orchestration_plan": None,
            "proactive_orchestration_plan_count": 0,
            "proactive_actuation_plan": None,
            "proactive_actuation_plan_count": 0,
            "proactive_progression_plan": None,
            "proactive_progression_plan_count": 0,
            "proactive_stage_controller_decision": None,
            "proactive_stage_controller_decision_count": 0,
            "proactive_line_controller_decision": None,
            "proactive_line_controller_decision_count": 0,
            "proactive_line_state_decision": None,
            "proactive_line_state_decision_count": 0,
            "proactive_line_transition_decision": None,
            "proactive_line_transition_decision_count": 0,
            "proactive_line_machine_decision": None,
            "proactive_line_machine_decision_count": 0,
            "proactive_lifecycle_state_decision": None,
            "proactive_lifecycle_state_decision_count": 0,
            "proactive_lifecycle_transition_decision": None,
            "proactive_lifecycle_transition_decision_count": 0,
            "proactive_lifecycle_machine_decision": None,
            "proactive_lifecycle_machine_decision_count": 0,
            "proactive_lifecycle_controller_decision": None,
            "proactive_lifecycle_controller_decision_count": 0,
            "proactive_lifecycle_envelope_decision": None,
            "proactive_lifecycle_envelope_decision_count": 0,
            "proactive_lifecycle_scheduler_decision": None,
            "proactive_lifecycle_scheduler_decision_count": 0,
            "proactive_lifecycle_window_decision": None,
            "proactive_lifecycle_window_decision_count": 0,
            "proactive_lifecycle_queue_decision": None,
            "proactive_lifecycle_queue_decision_count": 0,
            "proactive_lifecycle_dispatch_decision": None,
            "proactive_lifecycle_dispatch_decision_count": 0,
            "proactive_lifecycle_outcome_decision": None,
            "proactive_lifecycle_outcome_decision_count": 0,
            "proactive_lifecycle_resolution_decision": None,
            "proactive_lifecycle_resolution_decision_count": 0,
            "proactive_lifecycle_activation_decision": None,
            "proactive_lifecycle_activation_decision_count": 0,
            "proactive_lifecycle_settlement_decision": None,
            "proactive_lifecycle_settlement_decision_count": 0,
            "proactive_lifecycle_closure_decision": None,
            "proactive_lifecycle_closure_decision_count": 0,
            "proactive_lifecycle_availability_decision": None,
            "proactive_lifecycle_availability_decision_count": 0,
            "proactive_lifecycle_retention_decision": None,
            "proactive_lifecycle_retention_decision_count": 0,
            "proactive_lifecycle_eligibility_decision": None,
            "proactive_lifecycle_eligibility_decision_count": 0,
            "proactive_lifecycle_candidate_decision": None,
            "proactive_lifecycle_candidate_decision_count": 0,
            "proactive_lifecycle_selectability_decision": None,
            "proactive_lifecycle_selectability_decision_count": 0,
            "proactive_lifecycle_reentry_decision": None,
            "proactive_lifecycle_reentry_decision_count": 0,
            "proactive_lifecycle_reactivation_decision": None,
            "proactive_lifecycle_reactivation_decision_count": 0,
            "proactive_lifecycle_resumption_decision": None,
            "proactive_lifecycle_resumption_decision_count": 0,
            "proactive_lifecycle_readiness_decision": None,
            "proactive_lifecycle_readiness_decision_count": 0,
            "proactive_lifecycle_arming_decision": None,
            "proactive_lifecycle_arming_decision_count": 0,
            "proactive_lifecycle_trigger_decision": None,
            "proactive_lifecycle_trigger_decision_count": 0,
            "proactive_lifecycle_launch_decision": None,
            "proactive_lifecycle_launch_decision_count": 0,
            "proactive_lifecycle_handoff_decision": None,
            "proactive_lifecycle_handoff_decision_count": 0,
            "proactive_lifecycle_continuation_decision": None,
            "proactive_lifecycle_continuation_decision_count": 0,
            "proactive_lifecycle_sustainment_decision": None,
            "proactive_lifecycle_sustainment_decision_count": 0,
            "proactive_lifecycle_stewardship_decision": None,
            "proactive_lifecycle_stewardship_decision_count": 0,
            "proactive_lifecycle_guardianship_decision": None,
            "proactive_lifecycle_guardianship_decision_count": 0,
            "proactive_lifecycle_oversight_decision": None,
            "proactive_lifecycle_oversight_decision_count": 0,
            "proactive_lifecycle_assurance_decision": None,
            "proactive_lifecycle_assurance_decision_count": 0,
            "proactive_lifecycle_attestation_decision": None,
            "proactive_lifecycle_attestation_decision_count": 0,
            "proactive_lifecycle_verification_decision": None,
            "proactive_lifecycle_verification_decision_count": 0,
            "proactive_lifecycle_certification_decision": None,
            "proactive_lifecycle_certification_decision_count": 0,
            "proactive_lifecycle_confirmation_decision": None,
            "proactive_lifecycle_confirmation_decision_count": 0,
            "proactive_lifecycle_ratification_decision": None,
            "proactive_lifecycle_ratification_decision_count": 0,
            "proactive_lifecycle_endorsement_decision": None,
            "proactive_lifecycle_endorsement_decision_count": 0,
            "proactive_lifecycle_authorization_decision": None,
            "proactive_lifecycle_authorization_decision_count": 0,
            "proactive_lifecycle_enactment_decision": None,
            "proactive_lifecycle_enactment_decision_count": 0,
            "proactive_lifecycle_finality_decision": None,
            "proactive_lifecycle_finality_decision_count": 0,
            "proactive_lifecycle_completion_decision": None,
            "proactive_lifecycle_completion_decision_count": 0,
            "proactive_lifecycle_conclusion_decision": None,
            "proactive_lifecycle_conclusion_decision_count": 0,
            "proactive_lifecycle_disposition_decision": None,
            "proactive_lifecycle_disposition_decision_count": 0,
            "proactive_lifecycle_standing_decision": None,
            "proactive_lifecycle_standing_decision_count": 0,
            "proactive_lifecycle_residency_decision": None,
            "proactive_lifecycle_residency_decision_count": 0,
            "proactive_lifecycle_tenure_decision": None,
            "proactive_lifecycle_tenure_decision_count": 0,
            "proactive_lifecycle_persistence_decision": None,
            "proactive_lifecycle_persistence_decision_count": 0,
            "proactive_lifecycle_durability_decision": None,
            "proactive_lifecycle_durability_decision_count": 0,
            "proactive_lifecycle_longevity_decision": None,
            "proactive_lifecycle_longevity_decision_count": 0,
            "proactive_lifecycle_legacy_decision": None,
            "proactive_lifecycle_legacy_decision_count": 0,
            "proactive_lifecycle_heritage_decision": None,
            "proactive_lifecycle_heritage_decision_count": 0,
            "proactive_lifecycle_lineage_decision": None,
            "proactive_lifecycle_lineage_decision_count": 0,
            "proactive_lifecycle_ancestry_decision": None,
            "proactive_lifecycle_ancestry_decision_count": 0,
            "proactive_lifecycle_provenance_decision": None,
            "proactive_lifecycle_provenance_decision_count": 0,
            "proactive_lifecycle_origin_decision": None,
            "proactive_lifecycle_origin_decision_count": 0,
            "proactive_lifecycle_root_decision": None,
            "proactive_lifecycle_root_decision_count": 0,
            "proactive_lifecycle_foundation_decision": None,
            "proactive_lifecycle_foundation_decision_count": 0,
            "proactive_lifecycle_bedrock_decision": None,
            "proactive_lifecycle_bedrock_decision_count": 0,
            "proactive_lifecycle_substrate_decision": None,
            "proactive_lifecycle_substrate_decision_count": 0,
            "proactive_lifecycle_stratum_decision": None,
            "proactive_lifecycle_stratum_decision_count": 0,
            "proactive_lifecycle_layer_decision": None,
            "proactive_lifecycle_layer_decision_count": 0,
            "proactive_stage_refresh_plan": None,
            "proactive_stage_refresh_plan_count": 0,
            "proactive_stage_replan_assessment": None,
            "proactive_stage_replan_assessment_count": 0,
            "proactive_dispatch_feedback_assessment": None,
            "proactive_dispatch_feedback_assessment_count": 0,
            "proactive_dispatch_gate_decision": None,
            "proactive_dispatch_gate_decision_count": 0,
            "proactive_dispatch_envelope_decision": None,
            "proactive_dispatch_envelope_decision_count": 0,
            "proactive_stage_state_decision": None,
            "proactive_stage_state_decision_count": 0,
            "proactive_stage_transition_decision": None,
            "proactive_stage_transition_decision_count": 0,
            "proactive_stage_machine_decision": None,
            "proactive_stage_machine_decision_count": 0,
            "last_proactive_followup_dispatch": None,
            "proactive_followup_dispatch_count": 0,
            "last_runtime_quality_doctor": None,
            "runtime_quality_doctor_report_count": 0,
            "system3_snapshot": None,
            "system3_snapshot_count": 0,
            "private_judgment": None,
            "session_directive": None,
            "confidence_assessment": None,
            "strategy_decision": None,
            "strategy_history": [],
            "expression_plan": None,
            "inner_monologue": [],
            "last_llm_failure": None,
            "last_background_job": None,
            "offline_consolidation": None,
            "latest_snapshot": None,
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

        if event.event_type == SESSION_STARTED:
            next_state["session"] = {
                "started": True,
                "session_id": event.payload.get("session_id", event.stream_id),
                "created_at": event.payload.get("created_at"),
                "metadata": dict(event.payload.get("metadata", {})),
            }
            return next_state

        if event.event_type in {USER_MESSAGE_RECEIVED, ASSISTANT_MESSAGE_SENT}:
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

        if event.event_type == CONTEXT_FRAME_COMPUTED:
            next_state["context_frame"] = dict(event.payload)
            return next_state

        if event.event_type == RELATIONSHIP_STATE_UPDATED:
            next_state["relationship_state"] = dict(event.payload)
            return next_state

        if event.event_type == CONFIDENCE_ASSESSMENT_COMPUTED:
            next_state["confidence_assessment"] = dict(event.payload)
            return next_state

        if event.event_type == REPAIR_ASSESSMENT_COMPUTED:
            next_state["repair_assessment"] = dict(event.payload)
            return next_state

        if event.event_type == MEMORY_BUNDLE_UPDATED:
            next_state["memory_bundle"] = dict(event.payload)
            return next_state

        if event.event_type == MEMORY_WRITE_GUARD_EVALUATED:
            next_state["last_memory_write_guard"] = dict(event.payload)
            return next_state

        if event.event_type == MEMORY_RETENTION_POLICY_APPLIED:
            next_state["last_memory_retention"] = dict(event.payload)
            return next_state

        if event.event_type == MEMORY_RECALL_PERFORMED:
            next_state["last_memory_recall"] = dict(event.payload)
            return next_state

        if event.event_type == MEMORY_FORGETTING_APPLIED:
            next_state["last_memory_forgetting"] = dict(event.payload)
            return next_state

        if event.event_type == KNOWLEDGE_BOUNDARY_DECIDED:
            next_state["knowledge_boundary_decision"] = dict(event.payload)
            return next_state

        if event.event_type == POLICY_GATE_DECIDED:
            next_state["policy_gate"] = dict(event.payload)
            return next_state

        if event.event_type == REHEARSAL_COMPLETED:
            next_state["rehearsal_result"] = dict(event.payload)
            return next_state

        if event.event_type == REPAIR_PLAN_UPDATED:
            next_state["repair_plan"] = dict(event.payload)
            return next_state

        if event.event_type == EMPOWERMENT_AUDIT_COMPLETED:
            next_state["empowerment_audit"] = dict(event.payload)
            return next_state

        if event.event_type == RESPONSE_DRAFT_PLANNED:
            next_state["response_draft_plan"] = dict(event.payload)
            return next_state

        if event.event_type == RESPONSE_RENDERING_POLICY_DECIDED:
            next_state["response_rendering_policy"] = dict(event.payload)
            return next_state

        if event.event_type == RESPONSE_SEQUENCE_PLANNED:
            next_state["response_sequence_plan"] = dict(event.payload)
            return next_state

        if event.event_type == RUNTIME_QUALITY_DOCTOR_COMPLETED:
            next_state["last_runtime_quality_doctor"] = dict(event.payload)
            next_state["runtime_quality_doctor_report_count"] = int(
                next_state.get("runtime_quality_doctor_report_count", 0)
            ) + 1
            return next_state

        if event.event_type == RUNTIME_COORDINATION_UPDATED:
            next_state["runtime_coordination_snapshot"] = dict(event.payload)
            next_state["runtime_coordination_snapshot_count"] = int(
                next_state.get("runtime_coordination_snapshot_count", 0)
            ) + 1
            return next_state

        if event.event_type == GUIDANCE_PLAN_UPDATED:
            next_state["guidance_plan"] = dict(event.payload)
            next_state["guidance_plan_count"] = int(
                next_state.get("guidance_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == CONVERSATION_CADENCE_UPDATED:
            next_state["conversation_cadence_plan"] = dict(event.payload)
            next_state["conversation_cadence_plan_count"] = int(
                next_state.get("conversation_cadence_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == SESSION_RITUAL_UPDATED:
            next_state["session_ritual_plan"] = dict(event.payload)
            next_state["session_ritual_plan_count"] = int(
                next_state.get("session_ritual_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == SOMATIC_ORCHESTRATION_UPDATED:
            next_state["somatic_orchestration_plan"] = dict(event.payload)
            next_state["somatic_orchestration_plan_count"] = int(
                next_state.get("somatic_orchestration_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_FOLLOWUP_UPDATED:
            next_state["proactive_followup_directive"] = dict(event.payload)
            next_state["proactive_followup_directive_count"] = int(
                next_state.get("proactive_followup_directive_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_CADENCE_UPDATED:
            next_state["proactive_cadence_plan"] = dict(event.payload)
            next_state["proactive_cadence_plan_count"] = int(
                next_state.get("proactive_cadence_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED:
            next_state["proactive_aggregate_governance_assessment"] = dict(
                event.payload
            )
            next_state["proactive_aggregate_governance_assessment_count"] = int(
                next_state.get("proactive_aggregate_governance_assessment_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_AGGREGATE_CONTROLLER_UPDATED:
            next_state["proactive_aggregate_controller_decision"] = dict(
                event.payload
            )
            next_state["proactive_aggregate_controller_decision_count"] = int(
                next_state.get("proactive_aggregate_controller_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED:
            next_state["proactive_orchestration_controller_decision"] = dict(
                event.payload
            )
            next_state["proactive_orchestration_controller_decision_count"] = int(
                next_state.get("proactive_orchestration_controller_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == REENGAGEMENT_MATRIX_ASSESSED:
            next_state["reengagement_matrix_assessment"] = dict(event.payload)
            next_state["reengagement_matrix_assessment_count"] = int(
                next_state.get("reengagement_matrix_assessment_count", 0)
            ) + 1
            return next_state

        if event.event_type == REENGAGEMENT_PLAN_UPDATED:
            next_state["reengagement_plan"] = dict(event.payload)
            next_state["reengagement_plan_count"] = int(
                next_state.get("reengagement_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_SCHEDULING_UPDATED:
            next_state["proactive_scheduling_plan"] = dict(event.payload)
            next_state["proactive_scheduling_plan_count"] = int(
                next_state.get("proactive_scheduling_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_GUARDRAIL_UPDATED:
            next_state["proactive_guardrail_plan"] = dict(event.payload)
            next_state["proactive_guardrail_plan_count"] = int(
                next_state.get("proactive_guardrail_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_ORCHESTRATION_UPDATED:
            next_state["proactive_orchestration_plan"] = dict(event.payload)
            next_state["proactive_orchestration_plan_count"] = int(
                next_state.get("proactive_orchestration_plan_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_ACTUATION_UPDATED:
            next_state["proactive_actuation_plan"] = dict(event.payload)
            next_state["proactive_actuation_plan_count"] = int(
                next_state.get("proactive_actuation_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_PROGRESSION_UPDATED:
            next_state["proactive_progression_plan"] = dict(event.payload)
            next_state["proactive_progression_plan_count"] = int(
                next_state.get("proactive_progression_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_STAGE_CONTROLLER_UPDATED:
            next_state["proactive_stage_controller_decision"] = dict(event.payload)
            next_state["proactive_stage_controller_decision_count"] = int(
                next_state.get("proactive_stage_controller_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_LINE_CONTROLLER_UPDATED:
            next_state["proactive_line_controller_decision"] = dict(event.payload)
            next_state["proactive_line_controller_decision_count"] = int(
                next_state.get("proactive_line_controller_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_LINE_STATE_UPDATED:
            next_state["proactive_line_state_decision"] = dict(event.payload)
            next_state["proactive_line_state_decision_count"] = int(
                next_state.get("proactive_line_state_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_LINE_TRANSITION_UPDATED:
            next_state["proactive_line_transition_decision"] = dict(event.payload)
            next_state["proactive_line_transition_decision_count"] = int(
                next_state.get("proactive_line_transition_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_LINE_MACHINE_UPDATED:
            next_state["proactive_line_machine_decision"] = dict(event.payload)
            next_state["proactive_line_machine_decision_count"] = int(
                next_state.get("proactive_line_machine_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_STATE_UPDATED:
            next_state["proactive_lifecycle_state_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_state_decision_count"] = int(
                next_state.get("proactive_lifecycle_state_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_TRANSITION_UPDATED:
            next_state["proactive_lifecycle_transition_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_transition_decision_count"] = int(
                next_state.get("proactive_lifecycle_transition_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_MACHINE_UPDATED:
            next_state["proactive_lifecycle_machine_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_machine_decision_count"] = int(
                next_state.get("proactive_lifecycle_machine_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED:
            next_state["proactive_lifecycle_controller_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_controller_decision_count"] = int(
                next_state.get("proactive_lifecycle_controller_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED:
            next_state["proactive_lifecycle_envelope_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_envelope_decision_count"] = int(
                next_state.get("proactive_lifecycle_envelope_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED:
            next_state["proactive_lifecycle_scheduler_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_scheduler_decision_count"] = int(
                next_state.get("proactive_lifecycle_scheduler_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_WINDOW_UPDATED:
            next_state["proactive_lifecycle_window_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_window_decision_count"] = int(
                next_state.get("proactive_lifecycle_window_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_QUEUE_UPDATED:
            next_state["proactive_lifecycle_queue_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_queue_decision_count"] = int(
                next_state.get("proactive_lifecycle_queue_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_DISPATCH_UPDATED:
            next_state["proactive_lifecycle_dispatch_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_dispatch_decision_count"] = int(
                next_state.get("proactive_lifecycle_dispatch_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_OUTCOME_UPDATED:
            next_state["proactive_lifecycle_outcome_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_outcome_decision_count"] = int(
                next_state.get("proactive_lifecycle_outcome_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED:
            next_state["proactive_lifecycle_resolution_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_resolution_decision_count"] = int(
                next_state.get("proactive_lifecycle_resolution_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED:
            next_state["proactive_lifecycle_activation_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_activation_decision_count"] = int(
                next_state.get("proactive_lifecycle_activation_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED:
            next_state["proactive_lifecycle_settlement_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_settlement_decision_count"] = int(
                next_state.get("proactive_lifecycle_settlement_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CLOSURE_UPDATED:
            next_state["proactive_lifecycle_closure_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_closure_decision_count"] = int(
                next_state.get("proactive_lifecycle_closure_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED:
            next_state["proactive_lifecycle_availability_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_availability_decision_count"] = int(
                next_state.get("proactive_lifecycle_availability_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_RETENTION_UPDATED:
            next_state["proactive_lifecycle_retention_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_retention_decision_count"] = int(
                next_state.get("proactive_lifecycle_retention_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED:
            next_state["proactive_lifecycle_eligibility_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_eligibility_decision_count"] = int(
                next_state.get("proactive_lifecycle_eligibility_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED:
            next_state["proactive_lifecycle_candidate_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_candidate_decision_count"] = int(
                next_state.get("proactive_lifecycle_candidate_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED:
            next_state["proactive_lifecycle_selectability_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_selectability_decision_count"] = int(
                next_state.get("proactive_lifecycle_selectability_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_REENTRY_UPDATED:
            next_state["proactive_lifecycle_reentry_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_reentry_decision_count"] = int(
                next_state.get("proactive_lifecycle_reentry_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED:
            next_state["proactive_lifecycle_reactivation_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_reactivation_decision_count"] = int(
                next_state.get("proactive_lifecycle_reactivation_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED:
            next_state["proactive_lifecycle_resumption_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_resumption_decision_count"] = int(
                next_state.get("proactive_lifecycle_resumption_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_READINESS_UPDATED:
            next_state["proactive_lifecycle_readiness_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_readiness_decision_count"] = int(
                next_state.get("proactive_lifecycle_readiness_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ARMING_UPDATED:
            next_state["proactive_lifecycle_arming_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_arming_decision_count"] = int(
                next_state.get("proactive_lifecycle_arming_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_TRIGGER_UPDATED:
            next_state["proactive_lifecycle_trigger_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_trigger_decision_count"] = int(
                next_state.get("proactive_lifecycle_trigger_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_LAUNCH_UPDATED:
            next_state["proactive_lifecycle_launch_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_launch_decision_count"] = int(
                next_state.get("proactive_lifecycle_launch_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_HANDOFF_UPDATED:
            next_state["proactive_lifecycle_handoff_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_handoff_decision_count"] = int(
                next_state.get("proactive_lifecycle_handoff_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED:
            next_state["proactive_lifecycle_continuation_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_continuation_decision_count"] = int(
                next_state.get("proactive_lifecycle_continuation_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED:
            next_state["proactive_lifecycle_sustainment_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_sustainment_decision_count"] = int(
                next_state.get("proactive_lifecycle_sustainment_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED:
            next_state["proactive_lifecycle_stewardship_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_stewardship_decision_count"] = int(
                next_state.get("proactive_lifecycle_stewardship_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED:
            next_state["proactive_lifecycle_guardianship_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_guardianship_decision_count"] = int(
                next_state.get("proactive_lifecycle_guardianship_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED:
            next_state["proactive_lifecycle_oversight_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_oversight_decision_count"] = int(
                next_state.get("proactive_lifecycle_oversight_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED:
            next_state["proactive_lifecycle_assurance_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_assurance_decision_count"] = int(
                next_state.get("proactive_lifecycle_assurance_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED:
            next_state["proactive_lifecycle_attestation_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_attestation_decision_count"] = int(
                next_state.get("proactive_lifecycle_attestation_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED:
            next_state["proactive_lifecycle_verification_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_verification_decision_count"] = int(
                next_state.get("proactive_lifecycle_verification_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED:
            next_state["proactive_lifecycle_certification_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_certification_decision_count"] = int(
                next_state.get("proactive_lifecycle_certification_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED:
            next_state["proactive_lifecycle_confirmation_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_confirmation_decision_count"] = int(
                next_state.get("proactive_lifecycle_confirmation_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED:
            next_state["proactive_lifecycle_ratification_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_ratification_decision_count"] = int(
                next_state.get("proactive_lifecycle_ratification_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED:
            next_state["proactive_lifecycle_endorsement_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_endorsement_decision_count"] = int(
                next_state.get("proactive_lifecycle_endorsement_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED:
            next_state["proactive_lifecycle_authorization_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_authorization_decision_count"] = int(
                next_state.get("proactive_lifecycle_authorization_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED:
            next_state["proactive_lifecycle_enactment_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_enactment_decision_count"] = int(
                next_state.get("proactive_lifecycle_enactment_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_FINALITY_UPDATED:
            next_state["proactive_lifecycle_finality_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_finality_decision_count"] = int(
                next_state.get("proactive_lifecycle_finality_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_COMPLETION_UPDATED:
            next_state["proactive_lifecycle_completion_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_completion_decision_count"] = int(
                next_state.get("proactive_lifecycle_completion_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED:
            next_state["proactive_lifecycle_conclusion_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_conclusion_decision_count"] = int(
                next_state.get("proactive_lifecycle_conclusion_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED:
            next_state["proactive_lifecycle_disposition_decision"] = dict(
                event.payload
            )
            next_state["proactive_lifecycle_disposition_decision_count"] = int(
                next_state.get("proactive_lifecycle_disposition_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_STANDING_UPDATED:
            next_state["proactive_lifecycle_standing_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_standing_decision_count"] = int(
                next_state.get("proactive_lifecycle_standing_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED:
            next_state["proactive_lifecycle_residency_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_residency_decision_count"] = int(
                next_state.get("proactive_lifecycle_residency_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_TENURE_UPDATED:
            next_state["proactive_lifecycle_tenure_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_tenure_decision_count"] = int(
                next_state.get("proactive_lifecycle_tenure_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED:
            next_state["proactive_lifecycle_persistence_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_persistence_decision_count"] = int(
                next_state.get("proactive_lifecycle_persistence_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_DURABILITY_UPDATED:
            next_state["proactive_lifecycle_durability_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_durability_decision_count"] = int(
                next_state.get("proactive_lifecycle_durability_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED:
            next_state["proactive_lifecycle_longevity_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_longevity_decision_count"] = int(
                next_state.get("proactive_lifecycle_longevity_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_LEGACY_UPDATED:
            next_state["proactive_lifecycle_legacy_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_legacy_decision_count"] = int(
                next_state.get("proactive_lifecycle_legacy_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_HERITAGE_UPDATED:
            next_state["proactive_lifecycle_heritage_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_heritage_decision_count"] = int(
                next_state.get("proactive_lifecycle_heritage_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_LINEAGE_UPDATED:
            next_state["proactive_lifecycle_lineage_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_lineage_decision_count"] = int(
                next_state.get("proactive_lifecycle_lineage_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED:
            next_state["proactive_lifecycle_ancestry_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_ancestry_decision_count"] = int(
                next_state.get("proactive_lifecycle_ancestry_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED:
            next_state["proactive_lifecycle_provenance_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_provenance_decision_count"] = int(
                next_state.get("proactive_lifecycle_provenance_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ORIGIN_UPDATED:
            next_state["proactive_lifecycle_origin_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_origin_decision_count"] = int(
                next_state.get("proactive_lifecycle_origin_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_ROOT_UPDATED:
            next_state["proactive_lifecycle_root_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_root_decision_count"] = int(
                next_state.get("proactive_lifecycle_root_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED:
            next_state["proactive_lifecycle_foundation_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_foundation_decision_count"] = int(
                next_state.get("proactive_lifecycle_foundation_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_BEDROCK_UPDATED:
            next_state["proactive_lifecycle_bedrock_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_bedrock_decision_count"] = int(
                next_state.get("proactive_lifecycle_bedrock_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED:
            next_state["proactive_lifecycle_substrate_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_substrate_decision_count"] = int(
                next_state.get("proactive_lifecycle_substrate_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_STRATUM_UPDATED:
            next_state["proactive_lifecycle_stratum_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_stratum_decision_count"] = int(
                next_state.get("proactive_lifecycle_stratum_decision_count", 0)
            ) + 1
            return next_state
        if event.event_type == PROACTIVE_LIFECYCLE_LAYER_UPDATED:
            next_state["proactive_lifecycle_layer_decision"] = dict(event.payload)
            next_state["proactive_lifecycle_layer_decision_count"] = int(
                next_state.get("proactive_lifecycle_layer_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_STAGE_REFRESH_UPDATED:
            next_state["proactive_stage_refresh_plan"] = dict(event.payload)
            next_state["proactive_stage_refresh_plan_count"] = int(
                next_state.get("proactive_stage_refresh_plan_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_STAGE_REPLAN_UPDATED:
            next_state["proactive_stage_replan_assessment"] = dict(event.payload)
            next_state["proactive_stage_replan_assessment_count"] = int(
                next_state.get("proactive_stage_replan_assessment_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_DISPATCH_FEEDBACK_ASSESSED:
            next_state["proactive_dispatch_feedback_assessment"] = dict(event.payload)
            next_state["proactive_dispatch_feedback_assessment_count"] = int(
                next_state.get("proactive_dispatch_feedback_assessment_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_DISPATCH_GATE_UPDATED:
            next_state["proactive_dispatch_gate_decision"] = dict(event.payload)
            next_state["proactive_dispatch_gate_decision_count"] = int(
                next_state.get("proactive_dispatch_gate_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_DISPATCH_ENVELOPE_UPDATED:
            next_state["proactive_dispatch_envelope_decision"] = dict(event.payload)
            next_state["proactive_dispatch_envelope_decision_count"] = int(
                next_state.get("proactive_dispatch_envelope_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_STAGE_STATE_UPDATED:
            next_state["proactive_stage_state_decision"] = dict(event.payload)
            next_state["proactive_stage_state_decision_count"] = int(
                next_state.get("proactive_stage_state_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_STAGE_TRANSITION_UPDATED:
            next_state["proactive_stage_transition_decision"] = dict(event.payload)
            next_state["proactive_stage_transition_decision_count"] = int(
                next_state.get("proactive_stage_transition_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_STAGE_MACHINE_UPDATED:
            next_state["proactive_stage_machine_decision"] = dict(event.payload)
            next_state["proactive_stage_machine_decision_count"] = int(
                next_state.get("proactive_stage_machine_decision_count", 0)
            ) + 1
            return next_state

        if event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED:
            next_state["last_proactive_followup_dispatch"] = dict(event.payload)
            next_state["proactive_followup_dispatch_count"] = int(
                next_state.get("proactive_followup_dispatch_count", 0)
            ) + 1
            return next_state

        if event.event_type == SYSTEM3_SNAPSHOT_UPDATED:
            next_state["system3_snapshot"] = dict(event.payload)
            next_state["system3_snapshot_count"] = int(
                next_state.get("system3_snapshot_count", 0)
            ) + 1
            return next_state

        if event.event_type == RESPONSE_POST_AUDITED:
            next_state["response_post_audit"] = dict(event.payload)
            return next_state

        if event.event_type == RESPONSE_NORMALIZED:
            next_state["response_normalization"] = dict(event.payload)
            return next_state

        if event.event_type == PRIVATE_JUDGMENT_COMPUTED:
            next_state["private_judgment"] = dict(event.payload)
            return next_state

        if event.event_type == INNER_MONOLOGUE_RECORDED:
            next_state["inner_monologue"].extend(
                list(event.payload.get("entries", []))
            )
            next_state["inner_monologue"] = next_state["inner_monologue"][-200:]
            return next_state

        if event.event_type == LLM_COMPLETION_FAILED:
            next_state["last_llm_failure"] = dict(event.payload)
            return next_state

        if event.event_type in {
            BACKGROUND_JOB_SCHEDULED,
            BACKGROUND_JOB_REQUEUED,
            BACKGROUND_JOB_CLAIMED,
            BACKGROUND_JOB_HEARTBEAT,
            BACKGROUND_JOB_LEASE_EXPIRED,
            BACKGROUND_JOB_STARTED,
            BACKGROUND_JOB_COMPLETED,
            BACKGROUND_JOB_FAILED,
        }:
            next_state["last_background_job"] = dict(event.payload)
            return next_state

        if event.event_type == OFFLINE_CONSOLIDATION_COMPLETED:
            next_state["offline_consolidation"] = dict(event.payload)
            return next_state

        if event.event_type == SESSION_SNAPSHOT_CREATED:
            next_state["latest_snapshot"] = dict(event.payload)
            return next_state

        if event.event_type == SESSION_ARCHIVED:
            next_state["archive_status"] = {
                "archived": bool(event.payload.get("archived", True)),
                "archived_at": event.payload.get("archived_at"),
                "reason": event.payload.get("reason"),
                "snapshot_id": event.payload.get("snapshot_id"),
            }
            return next_state

        if event.event_type == SESSION_DIRECTIVE_UPDATED:
            next_state["session_directive"] = dict(event.payload.get("directive", {}))
            next_state["confidence_assessment"] = dict(
                event.payload.get("confidence", {})
            )
            next_state["strategy_decision"] = dict(event.payload.get("strategy", {}))
            strategy_name = str(
                (event.payload.get("strategy", {}) or {}).get("strategy", "")
            ).strip()
            if strategy_name:
                next_state["strategy_history"].append(strategy_name)
                next_state["strategy_history"] = next_state["strategy_history"][-8:]
            next_state["expression_plan"] = dict(
                event.payload.get("expression_plan", {})
            )
            next_state["guidance_plan"] = dict(event.payload.get("guidance_plan", {}))
            next_state["conversation_cadence_plan"] = dict(
                event.payload.get("conversation_cadence_plan", {})
            )
            next_state["session_ritual_plan"] = dict(
                event.payload.get("session_ritual_plan", {})
            )
            next_state["somatic_orchestration_plan"] = dict(
                event.payload.get("somatic_orchestration_plan", {})
            )
            next_state["proactive_cadence_plan"] = dict(
                event.payload.get("proactive_cadence_plan", {})
            )
            next_state["response_draft_plan"] = dict(
                event.payload.get("response_draft_plan", {})
            )
            next_state["response_rendering_policy"] = dict(
                event.payload.get("response_rendering_policy", {})
            )
            return next_state

        return next_state
