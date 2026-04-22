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
PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED = "system.proactive_aggregate_governance.assessed"
PROACTIVE_AGGREGATE_CONTROLLER_UPDATED = "system.proactive_aggregate_controller.updated"
PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED = "system.proactive_orchestration_controller.updated"
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
PROACTIVE_LIFECYCLE_EVENT_PREFIX = "system.proactive_lifecycle_"
PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED = "system.proactive_lifecycle_snapshot.updated"
PROACTIVE_FOLLOWUP_DISPATCHED = "system.proactive_followup.dispatched"
PROACTIVE_DISPATCH_OUTCOME_RECORDED = "system.proactive_dispatch_outcome.recorded"
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

# User identity and person-centric events
USER_CREATED = "user.created"
USER_SESSION_LINKED = "user.session_linked"
USER_PROFILE_UPDATED = "user.profile_updated"
SELF_STATE_UPDATED = "user.self_state.updated"

# Single-entity persona and social-world events
ENTITY_SEEDED = "entity.seeded"
ENTITY_PERSONA_UPDATED = "entity.persona.updated"
ENTITY_MOOD_UPDATED = "entity.mood.updated"
ENTITY_RELATIONSHIP_WORLD_MODEL_UPDATED = "entity.relationship_world_model.updated"
ENTITY_CONSCIENCE_UPDATED = "entity.conscience.updated"
ENTITY_DRIVE_UPDATED = "entity.drive.updated"
ENTITY_GOAL_UPDATED = "entity.goal.updated"
ENTITY_SELF_NARRATIVE_UPDATED = "entity.self_narrative.updated"
ENTITY_ENVIRONMENT_APPRAISAL_UPDATED = "entity.environment_appraisal.updated"
SYSTEM_WORLD_STATE_UPDATED = "system.world_state.updated"
SYSTEM_ACTION_SURFACE_UPDATED = "system.action_surface.updated"
ENTITY_ACTION_INTENT_UPDATED = "entity.action_intent.updated"
ENTITY_ACTION_PLANNED = "entity.action_planned"
ENTITY_ACTION_EXECUTION_DECIDED = "entity.action_execution_decided"
ENTITY_ACTION_EXECUTION_RECORDED = "entity.action_execution_recorded"

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
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_DISPATCH_OUTCOME_RECORDED,
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
    USER_CREATED,
    USER_SESSION_LINKED,
    USER_PROFILE_UPDATED,
    SELF_STATE_UPDATED,
    ENTITY_SEEDED,
    ENTITY_PERSONA_UPDATED,
    ENTITY_MOOD_UPDATED,
    ENTITY_RELATIONSHIP_WORLD_MODEL_UPDATED,
    ENTITY_CONSCIENCE_UPDATED,
    ENTITY_DRIVE_UPDATED,
    ENTITY_GOAL_UPDATED,
    ENTITY_SELF_NARRATIVE_UPDATED,
    ENTITY_ENVIRONMENT_APPRAISAL_UPDATED,
    SYSTEM_WORLD_STATE_UPDATED,
    SYSTEM_ACTION_SURFACE_UPDATED,
    ENTITY_ACTION_INTENT_UPDATED,
    ENTITY_ACTION_PLANNED,
    ENTITY_ACTION_EXECUTION_DECIDED,
    ENTITY_ACTION_EXECUTION_RECORDED,
}


def is_trace_event_type(event_type: str) -> bool:
    return event_type in TRACE_EVENT_TYPES or event_type.startswith(
        PROACTIVE_LIFECYCLE_EVENT_PREFIX
    )
