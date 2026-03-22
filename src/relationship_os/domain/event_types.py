SESSION_STARTED = "session.started"
USER_MESSAGE_RECEIVED = "user.message.received"
ASSISTANT_MESSAGE_SENT = "assistant.message.sent"
CONTEXT_FRAME_COMPUTED = "system.context_frame.computed"
RELATIONSHIP_STATE_UPDATED = "system.relationship_state.updated"
CONFIDENCE_ASSESSMENT_COMPUTED = "system.confidence_assessment.computed"
REPAIR_ASSESSMENT_COMPUTED = "system.repair_assessment.computed"
MEMORY_WRITE_GUARD_EVALUATED = "system.memory_write_guard.evaluated"
MEMORY_BUNDLE_UPDATED = "system.memory_bundle.updated"
MEMORY_RECALL_PERFORMED = "system.memory_recall.performed"
MEMORY_RETENTION_POLICY_APPLIED = "system.memory_retention_policy.applied"
MEMORY_FORGETTING_APPLIED = "system.memory_forgetting.applied"
KNOWLEDGE_BOUNDARY_DECIDED = "system.knowledge_boundary.decided"
POLICY_GATE_DECIDED = "system.policy_gate.decided"
REHEARSAL_COMPLETED = "system.rehearsal.completed"
EMPOWERMENT_AUDIT_COMPLETED = "system.empowerment_audit.completed"
RESPONSE_DRAFT_PLANNED = "system.response_draft.planned"
RESPONSE_RENDERING_POLICY_DECIDED = "system.response_rendering_policy.decided"
RESPONSE_SEQUENCE_PLANNED = "system.response_sequence.planned"
RUNTIME_QUALITY_DOCTOR_COMPLETED = "system.runtime_quality_doctor.completed"
SYSTEM3_SNAPSHOT_UPDATED = "system.system3_snapshot.updated"
RUNTIME_COORDINATION_UPDATED = "system.runtime_coordination.updated"
GUIDANCE_PLAN_UPDATED = "system.guidance_plan.updated"
CONVERSATION_CADENCE_UPDATED = "system.conversation_cadence.updated"
SESSION_RITUAL_UPDATED = "system.session_ritual.updated"
SOMATIC_ORCHESTRATION_UPDATED = "system.somatic_orchestration.updated"
PROACTIVE_FOLLOWUP_UPDATED = "system.proactive_followup.updated"
PROACTIVE_CADENCE_UPDATED = "system.proactive_cadence.updated"
REENGAGEMENT_MATRIX_ASSESSED = "system.reengagement_matrix.assessed"
REENGAGEMENT_PLAN_UPDATED = "system.reengagement_plan.updated"
PROACTIVE_SCHEDULING_UPDATED = "system.proactive_scheduling.updated"
PROACTIVE_ORCHESTRATION_UPDATED = "system.proactive_orchestration.updated"
PROACTIVE_ACTUATION_UPDATED = "system.proactive_actuation.updated"
PROACTIVE_PROGRESSION_UPDATED = "system.proactive_progression.updated"
PROACTIVE_GUARDRAIL_UPDATED = "system.proactive_guardrail.updated"
PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED = (
    "system.proactive_aggregate_governance.assessed"
)
PROACTIVE_AGGREGATE_CONTROLLER_UPDATED = (
    "system.proactive_aggregate_controller.updated"
)
PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED = (
    "system.proactive_orchestration_controller.updated"
)
PROACTIVE_STAGE_CONTROLLER_UPDATED = "system.proactive_stage_controller.updated"
PROACTIVE_LINE_CONTROLLER_UPDATED = "system.proactive_line_controller.updated"
PROACTIVE_STAGE_REFRESH_UPDATED = "system.proactive_stage_refresh.updated"
PROACTIVE_STAGE_REPLAN_UPDATED = "system.proactive_stage_replan.updated"
PROACTIVE_DISPATCH_FEEDBACK_ASSESSED = "system.proactive_dispatch_feedback.assessed"
PROACTIVE_DISPATCH_GATE_UPDATED = "system.proactive_dispatch_gate.updated"
PROACTIVE_DISPATCH_ENVELOPE_UPDATED = "system.proactive_dispatch_envelope.updated"
PROACTIVE_STAGE_STATE_UPDATED = "system.proactive_stage_state.updated"
PROACTIVE_STAGE_TRANSITION_UPDATED = "system.proactive_stage_transition.updated"
PROACTIVE_STAGE_MACHINE_UPDATED = "system.proactive_stage_machine.updated"
PROACTIVE_LINE_STATE_UPDATED = "system.proactive_line_state.updated"
PROACTIVE_LINE_TRANSITION_UPDATED = "system.proactive_line_transition.updated"
PROACTIVE_LINE_MACHINE_UPDATED = "system.proactive_line_machine.updated"
PROACTIVE_LIFECYCLE_STATE_UPDATED = "system.proactive_lifecycle_state.updated"
PROACTIVE_LIFECYCLE_TRANSITION_UPDATED = "system.proactive_lifecycle_transition.updated"
PROACTIVE_LIFECYCLE_MACHINE_UPDATED = "system.proactive_lifecycle_machine.updated"
PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED = (
    "system.proactive_lifecycle_controller.updated"
)
PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED = (
    "system.proactive_lifecycle_envelope.updated"
)
PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED = (
    "system.proactive_lifecycle_scheduler.updated"
)
PROACTIVE_LIFECYCLE_WINDOW_UPDATED = "system.proactive_lifecycle_window.updated"
PROACTIVE_LIFECYCLE_QUEUE_UPDATED = "system.proactive_lifecycle_queue.updated"
PROACTIVE_LIFECYCLE_DISPATCH_UPDATED = "system.proactive_lifecycle_dispatch.updated"
PROACTIVE_LIFECYCLE_OUTCOME_UPDATED = "system.proactive_lifecycle_outcome.updated"
PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED = (
    "system.proactive_lifecycle_resolution.updated"
)
PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED = (
    "system.proactive_lifecycle_activation.updated"
)
PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED = (
    "system.proactive_lifecycle_settlement.updated"
)
PROACTIVE_LIFECYCLE_CLOSURE_UPDATED = (
    "system.proactive_lifecycle_closure.updated"
)
PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED = (
    "system.proactive_lifecycle_availability.updated"
)
PROACTIVE_LIFECYCLE_RETENTION_UPDATED = (
    "system.proactive_lifecycle_retention.updated"
)
PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED = (
    "system.proactive_lifecycle_eligibility.updated"
)
PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED = (
    "system.proactive_lifecycle_candidate.updated"
)
PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED = (
    "system.proactive_lifecycle_selectability.updated"
)
PROACTIVE_LIFECYCLE_REENTRY_UPDATED = "system.proactive_lifecycle_reentry.updated"
PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED = (
    "system.proactive_lifecycle_reactivation.updated"
)
PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED = (
    "system.proactive_lifecycle_resumption.updated"
)
PROACTIVE_LIFECYCLE_READINESS_UPDATED = (
    "system.proactive_lifecycle_readiness.updated"
)
PROACTIVE_LIFECYCLE_ARMING_UPDATED = "system.proactive_lifecycle_arming.updated"
PROACTIVE_LIFECYCLE_TRIGGER_UPDATED = "system.proactive_lifecycle_trigger.updated"
PROACTIVE_LIFECYCLE_LAUNCH_UPDATED = "system.proactive_lifecycle_launch.updated"
PROACTIVE_LIFECYCLE_HANDOFF_UPDATED = "system.proactive_lifecycle_handoff.updated"
PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED = (
    "system.proactive_lifecycle_continuation.updated"
)
PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED = (
    "system.proactive_lifecycle_sustainment.updated"
)
PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED = (
    "system.proactive_lifecycle_stewardship.updated"
)
PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED = (
    "system.proactive_lifecycle_guardianship.updated"
)
PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED = (
    "system.proactive_lifecycle_oversight.updated"
)
PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED = (
    "system.proactive_lifecycle_assurance.updated"
)
PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED = (
    "system.proactive_lifecycle_attestation.updated"
)
PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED = (
    "system.proactive_lifecycle_verification.updated"
)
PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED = (
    "system.proactive_lifecycle_certification.updated"
)
PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED = (
    "system.proactive_lifecycle_confirmation.updated"
)
PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED = (
    "system.proactive_lifecycle_ratification.updated"
)
PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED = (
    "system.proactive_lifecycle_endorsement.updated"
)
PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED = (
    "system.proactive_lifecycle_authorization.updated"
)
PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED = (
    "system.proactive_lifecycle_enactment.updated"
)
PROACTIVE_LIFECYCLE_FINALITY_UPDATED = "system.proactive_lifecycle_finality.updated"
PROACTIVE_LIFECYCLE_COMPLETION_UPDATED = (
    "system.proactive_lifecycle_completion.updated"
)
PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED = (
    "system.proactive_lifecycle_conclusion.updated"
)
PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED = (
    "system.proactive_lifecycle_disposition.updated"
)
PROACTIVE_LIFECYCLE_DURABILITY_UPDATED = (
    "system.proactive_lifecycle_durability.updated"
)
PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED = (
    "system.proactive_lifecycle_longevity.updated"
)
PROACTIVE_LIFECYCLE_LEGACY_UPDATED = "system.proactive_lifecycle_legacy.updated"
PROACTIVE_LIFECYCLE_HERITAGE_UPDATED = (
    "system.proactive_lifecycle_heritage.updated"
)
PROACTIVE_LIFECYCLE_LINEAGE_UPDATED = (
    "system.proactive_lifecycle_lineage.updated"
)
PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED = (
    "system.proactive_lifecycle_ancestry.updated"
)
PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED = (
    "system.proactive_lifecycle_provenance.updated"
)
PROACTIVE_LIFECYCLE_ORIGIN_UPDATED = "system.proactive_lifecycle_origin.updated"
PROACTIVE_LIFECYCLE_ROOT_UPDATED = "system.proactive_lifecycle_root.updated"
PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED = (
    "system.proactive_lifecycle_foundation.updated"
)
PROACTIVE_LIFECYCLE_BEDROCK_UPDATED = "system.proactive_lifecycle_bedrock.updated"
PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED = (
    "system.proactive_lifecycle_substrate.updated"
)
PROACTIVE_LIFECYCLE_STRATUM_UPDATED = "system.proactive_lifecycle_stratum.updated"
PROACTIVE_LIFECYCLE_LAYER_UPDATED = "system.proactive_lifecycle_layer.updated"
PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED = (
    "system.proactive_lifecycle_persistence.updated"
)
PROACTIVE_LIFECYCLE_TENURE_UPDATED = "system.proactive_lifecycle_tenure.updated"
PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED = "system.proactive_lifecycle_residency.updated"
PROACTIVE_LIFECYCLE_STANDING_UPDATED = "system.proactive_lifecycle_standing.updated"
PROACTIVE_FOLLOWUP_DISPATCHED = "system.proactive_followup.dispatched"
RESPONSE_POST_AUDITED = "system.response_post_audited"
RESPONSE_NORMALIZED = "system.response.normalized"
REPAIR_PLAN_UPDATED = "system.repair_plan.updated"
PRIVATE_JUDGMENT_COMPUTED = "system.private_judgment.computed"
INNER_MONOLOGUE_RECORDED = "system.inner_monologue.recorded"
LLM_COMPLETION_FAILED = "system.llm.completion_failed"
SESSION_DIRECTIVE_UPDATED = "system.session_directive.updated"
BACKGROUND_JOB_SCHEDULED = "system.background_job.scheduled"
BACKGROUND_JOB_REQUEUED = "system.background_job.requeued"
BACKGROUND_JOB_CLAIMED = "system.background_job.claimed"
BACKGROUND_JOB_HEARTBEAT = "system.background_job.heartbeat"
BACKGROUND_JOB_LEASE_EXPIRED = "system.background_job.lease_expired"
BACKGROUND_JOB_STARTED = "system.background_job.started"
BACKGROUND_JOB_COMPLETED = "system.background_job.completed"
BACKGROUND_JOB_FAILED = "system.background_job.failed"
OFFLINE_CONSOLIDATION_COMPLETED = "system.offline_consolidation.completed"
SESSION_SNAPSHOT_CREATED = "system.session_snapshot.created"
SESSION_ARCHIVED = "system.session.archived"
SCENARIO_BASELINE_SET = "system.scenario_baseline.set"
SCENARIO_BASELINE_CLEARED = "system.scenario_baseline.cleared"

TRACE_EVENT_TYPES = {
    SESSION_STARTED,
    USER_MESSAGE_RECEIVED,
    ASSISTANT_MESSAGE_SENT,
    CONTEXT_FRAME_COMPUTED,
    RELATIONSHIP_STATE_UPDATED,
    CONFIDENCE_ASSESSMENT_COMPUTED,
    REPAIR_ASSESSMENT_COMPUTED,
    MEMORY_WRITE_GUARD_EVALUATED,
    MEMORY_BUNDLE_UPDATED,
    MEMORY_RECALL_PERFORMED,
    MEMORY_RETENTION_POLICY_APPLIED,
    MEMORY_FORGETTING_APPLIED,
    KNOWLEDGE_BOUNDARY_DECIDED,
    POLICY_GATE_DECIDED,
    REHEARSAL_COMPLETED,
    EMPOWERMENT_AUDIT_COMPLETED,
    RESPONSE_DRAFT_PLANNED,
    RESPONSE_RENDERING_POLICY_DECIDED,
    RESPONSE_SEQUENCE_PLANNED,
    RUNTIME_QUALITY_DOCTOR_COMPLETED,
    SYSTEM3_SNAPSHOT_UPDATED,
    RUNTIME_COORDINATION_UPDATED,
    GUIDANCE_PLAN_UPDATED,
    CONVERSATION_CADENCE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SOMATIC_ORCHESTRATION_UPDATED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_CADENCE_UPDATED,
    REENGAGEMENT_MATRIX_ASSESSED,
    REENGAGEMENT_PLAN_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_GUARDRAIL_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_REFRESH_UPDATED,
    PROACTIVE_STAGE_REPLAN_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
    PROACTIVE_STAGE_STATE_UPDATED,
    PROACTIVE_STAGE_TRANSITION_UPDATED,
    PROACTIVE_STAGE_MACHINE_UPDATED,
    PROACTIVE_LINE_STATE_UPDATED,
    PROACTIVE_LINE_TRANSITION_UPDATED,
    PROACTIVE_LINE_MACHINE_UPDATED,
    PROACTIVE_LIFECYCLE_STATE_UPDATED,
    PROACTIVE_LIFECYCLE_TRANSITION_UPDATED,
    PROACTIVE_LIFECYCLE_MACHINE_UPDATED,
    PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED,
    PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED,
    PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED,
    PROACTIVE_LIFECYCLE_WINDOW_UPDATED,
    PROACTIVE_LIFECYCLE_QUEUE_UPDATED,
    PROACTIVE_LIFECYCLE_DISPATCH_UPDATED,
    PROACTIVE_LIFECYCLE_OUTCOME_UPDATED,
    PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED,
    PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED,
    PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED,
    PROACTIVE_LIFECYCLE_CLOSURE_UPDATED,
    PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_RETENTION_UPDATED,
    PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED,
    PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED,
    PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_REENTRY_UPDATED,
    PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED,
    PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED,
    PROACTIVE_LIFECYCLE_READINESS_UPDATED,
    PROACTIVE_LIFECYCLE_ARMING_UPDATED,
    PROACTIVE_LIFECYCLE_TRIGGER_UPDATED,
    PROACTIVE_LIFECYCLE_LAUNCH_UPDATED,
    PROACTIVE_LIFECYCLE_HANDOFF_UPDATED,
    PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED,
    PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED,
    PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED,
    PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED,
    PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED,
    PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED,
    PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED,
    PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED,
    PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED,
    PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED,
    PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED,
    PROACTIVE_LIFECYCLE_FINALITY_UPDATED,
    PROACTIVE_LIFECYCLE_COMPLETION_UPDATED,
    PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED,
    PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED,
    PROACTIVE_LIFECYCLE_DURABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED,
    PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED,
    PROACTIVE_LIFECYCLE_TENURE_UPDATED,
    PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED,
    PROACTIVE_LIFECYCLE_STANDING_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    RESPONSE_POST_AUDITED,
    RESPONSE_NORMALIZED,
    REPAIR_PLAN_UPDATED,
    PRIVATE_JUDGMENT_COMPUTED,
    INNER_MONOLOGUE_RECORDED,
    LLM_COMPLETION_FAILED,
    SESSION_DIRECTIVE_UPDATED,
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_STARTED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
    OFFLINE_CONSOLIDATION_COMPLETED,
    SESSION_SNAPSHOT_CREATED,
    SESSION_ARCHIVED,
    SCENARIO_BASELINE_SET,
    SCENARIO_BASELINE_CLEARED,
}
