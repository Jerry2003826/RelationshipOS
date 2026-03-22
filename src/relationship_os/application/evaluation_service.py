import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Any

from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    CONFIDENCE_ASSESSMENT_COMPUTED,
    CONTEXT_FRAME_COMPUTED,
    CONVERSATION_CADENCE_UPDATED,
    EMPOWERMENT_AUDIT_COMPLETED,
    GUIDANCE_PLAN_UPDATED,
    KNOWLEDGE_BOUNDARY_DECIDED,
    LLM_COMPLETION_FAILED,
    MEMORY_BUNDLE_UPDATED,
    MEMORY_FORGETTING_APPLIED,
    MEMORY_RECALL_PERFORMED,
    MEMORY_RETENTION_POLICY_APPLIED,
    MEMORY_WRITE_GUARD_EVALUATED,
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
    SESSION_DIRECTIVE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SESSION_STARTED,
    SOMATIC_ORCHESTRATION_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import StoredEvent

QUALITY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "this",
    "to",
    "we",
    "will",
    "with",
    "you",
    "your",
}


@dataclass(slots=True)
class TurnRecord:
    turn_index: int
    user_message: str
    assistant_message: str | None = None
    assistant_responses: list[str] = field(default_factory=list)
    assistant_message_event_count: int = 0
    context_frame: dict[str, Any] | None = None
    confidence_assessment: dict[str, Any] | None = None
    relationship_state: dict[str, Any] | None = None
    repair_assessment: dict[str, Any] | None = None
    memory_bundle: dict[str, Any] | None = None
    memory_write_guard: dict[str, Any] | None = None
    memory_retention: dict[str, Any] | None = None
    memory_recall: dict[str, Any] | None = None
    memory_forgetting: dict[str, Any] | None = None
    knowledge_boundary_decision: dict[str, Any] | None = None
    policy_gate: dict[str, Any] | None = None
    rehearsal_result: dict[str, Any] | None = None
    repair_plan: dict[str, Any] | None = None
    empowerment_audit: dict[str, Any] | None = None
    response_draft_plan: dict[str, Any] | None = None
    response_rendering_policy: dict[str, Any] | None = None
    response_sequence_plan: dict[str, Any] | None = None
    response_post_audit: dict[str, Any] | None = None
    response_normalization: dict[str, Any] | None = None
    runtime_coordination_snapshot: dict[str, Any] | None = None
    guidance_plan: dict[str, Any] | None = None
    conversation_cadence_plan: dict[str, Any] | None = None
    session_ritual_plan: dict[str, Any] | None = None
    somatic_orchestration_plan: dict[str, Any] | None = None
    proactive_followup_directive: dict[str, Any] | None = None
    proactive_cadence_plan: dict[str, Any] | None = None
    proactive_aggregate_governance_assessment: dict[str, Any] | None = None
    proactive_aggregate_controller_decision: dict[str, Any] | None = None
    proactive_orchestration_controller_decision: dict[str, Any] | None = None
    proactive_guardrail_plan: dict[str, Any] | None = None
    reengagement_matrix_assessment: dict[str, Any] | None = None
    reengagement_plan: dict[str, Any] | None = None
    proactive_scheduling_plan: dict[str, Any] | None = None
    proactive_orchestration_plan: dict[str, Any] | None = None
    proactive_actuation_plan: dict[str, Any] | None = None
    proactive_progression_plan: dict[str, Any] | None = None
    proactive_stage_controller_decision: dict[str, Any] | None = None
    proactive_line_controller_decision: dict[str, Any] | None = None
    proactive_line_state_decision: dict[str, Any] | None = None
    proactive_line_transition_decision: dict[str, Any] | None = None
    proactive_line_machine_decision: dict[str, Any] | None = None
    proactive_lifecycle_state_decision: dict[str, Any] | None = None
    proactive_lifecycle_transition_decision: dict[str, Any] | None = None
    proactive_lifecycle_machine_decision: dict[str, Any] | None = None
    proactive_lifecycle_controller_decision: dict[str, Any] | None = None
    proactive_lifecycle_envelope_decision: dict[str, Any] | None = None
    proactive_lifecycle_scheduler_decision: dict[str, Any] | None = None
    proactive_lifecycle_window_decision: dict[str, Any] | None = None
    proactive_lifecycle_queue_decision: dict[str, Any] | None = None
    proactive_lifecycle_dispatch_decision: dict[str, Any] | None = None
    proactive_lifecycle_outcome_decision: dict[str, Any] | None = None
    proactive_lifecycle_resolution_decision: dict[str, Any] | None = None
    proactive_lifecycle_activation_decision: dict[str, Any] | None = None
    proactive_lifecycle_settlement_decision: dict[str, Any] | None = None
    proactive_lifecycle_closure_decision: dict[str, Any] | None = None
    proactive_lifecycle_availability_decision: dict[str, Any] | None = None
    proactive_lifecycle_retention_decision: dict[str, Any] | None = None
    proactive_lifecycle_eligibility_decision: dict[str, Any] | None = None
    proactive_lifecycle_candidate_decision: dict[str, Any] | None = None
    proactive_lifecycle_selectability_decision: dict[str, Any] | None = None
    proactive_lifecycle_reentry_decision: dict[str, Any] | None = None
    proactive_lifecycle_reactivation_decision: dict[str, Any] | None = None
    proactive_lifecycle_resumption_decision: dict[str, Any] | None = None
    proactive_lifecycle_readiness_decision: dict[str, Any] | None = None
    proactive_lifecycle_arming_decision: dict[str, Any] | None = None
    proactive_lifecycle_trigger_decision: dict[str, Any] | None = None
    proactive_lifecycle_launch_decision: dict[str, Any] | None = None
    proactive_lifecycle_handoff_decision: dict[str, Any] | None = None
    proactive_lifecycle_continuation_decision: dict[str, Any] | None = None
    proactive_lifecycle_sustainment_decision: dict[str, Any] | None = None
    proactive_lifecycle_stewardship_decision: dict[str, Any] | None = None
    proactive_lifecycle_guardianship_decision: dict[str, Any] | None = None
    proactive_lifecycle_oversight_decision: dict[str, Any] | None = None
    proactive_lifecycle_assurance_decision: dict[str, Any] | None = None
    proactive_lifecycle_attestation_decision: dict[str, Any] | None = None
    proactive_lifecycle_verification_decision: dict[str, Any] | None = None
    proactive_lifecycle_certification_decision: dict[str, Any] | None = None
    proactive_lifecycle_confirmation_decision: dict[str, Any] | None = None
    proactive_lifecycle_ratification_decision: dict[str, Any] | None = None
    proactive_lifecycle_endorsement_decision: dict[str, Any] | None = None
    proactive_lifecycle_authorization_decision: dict[str, Any] | None = None
    proactive_lifecycle_enactment_decision: dict[str, Any] | None = None
    proactive_lifecycle_finality_decision: dict[str, Any] | None = None
    proactive_lifecycle_completion_decision: dict[str, Any] | None = None
    proactive_lifecycle_conclusion_decision: dict[str, Any] | None = None
    proactive_lifecycle_disposition_decision: dict[str, Any] | None = None
    proactive_lifecycle_standing_decision: dict[str, Any] | None = None
    proactive_lifecycle_residency_decision: dict[str, Any] | None = None
    proactive_lifecycle_tenure_decision: dict[str, Any] | None = None
    proactive_lifecycle_persistence_decision: dict[str, Any] | None = None
    proactive_lifecycle_longevity_decision: dict[str, Any] | None = None
    proactive_lifecycle_legacy_decision: dict[str, Any] | None = None
    proactive_lifecycle_heritage_decision: dict[str, Any] | None = None
    proactive_lifecycle_lineage_decision: dict[str, Any] | None = None
    proactive_lifecycle_ancestry_decision: dict[str, Any] | None = None
    proactive_lifecycle_provenance_decision: dict[str, Any] | None = None
    proactive_lifecycle_origin_decision: dict[str, Any] | None = None
    proactive_lifecycle_root_decision: dict[str, Any] | None = None
    proactive_lifecycle_foundation_decision: dict[str, Any] | None = None
    proactive_lifecycle_bedrock_decision: dict[str, Any] | None = None
    proactive_lifecycle_substrate_decision: dict[str, Any] | None = None
    proactive_lifecycle_stratum_decision: dict[str, Any] | None = None
    proactive_lifecycle_layer_decision: dict[str, Any] | None = None
    proactive_lifecycle_durability_decision: dict[str, Any] | None = None
    proactive_stage_refresh_plan: dict[str, Any] | None = None
    proactive_stage_replan_assessment: dict[str, Any] | None = None
    proactive_dispatch_feedback_assessment: dict[str, Any] | None = None
    proactive_dispatch_gate_decision: dict[str, Any] | None = None
    proactive_dispatch_envelope_decision: dict[str, Any] | None = None
    proactive_stage_state_decision: dict[str, Any] | None = None
    proactive_stage_transition_decision: dict[str, Any] | None = None
    proactive_stage_machine_decision: dict[str, Any] | None = None
    proactive_followup_dispatch: dict[str, Any] | None = None
    proactive_followup_messages: list[str] = field(default_factory=list)
    proactive_followup_message_event_count: int = 0
    runtime_quality_doctor_report: dict[str, Any] | None = None
    system3_snapshot: dict[str, Any] | None = None
    private_judgment: dict[str, Any] | None = None
    session_directive: dict[str, Any] | None = None
    strategy_decision: dict[str, Any] | None = None
    llm_failure: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "user_message": self.user_message,
            "assistant_message": self.assistant_message,
            "assistant_responses": list(self.assistant_responses),
            "assistant_message_event_count": self.assistant_message_event_count,
            "context_frame": self.context_frame,
            "confidence_assessment": self.confidence_assessment,
            "relationship_state": self.relationship_state,
            "repair_assessment": self.repair_assessment,
            "memory_bundle": self.memory_bundle,
            "memory_write_guard": self.memory_write_guard,
            "memory_retention": self.memory_retention,
            "memory_recall": self.memory_recall,
            "memory_forgetting": self.memory_forgetting,
            "knowledge_boundary_decision": self.knowledge_boundary_decision,
            "policy_gate": self.policy_gate,
            "rehearsal_result": self.rehearsal_result,
            "repair_plan": self.repair_plan,
            "empowerment_audit": self.empowerment_audit,
            "response_draft_plan": self.response_draft_plan,
            "response_rendering_policy": self.response_rendering_policy,
            "response_sequence_plan": self.response_sequence_plan,
            "response_post_audit": self.response_post_audit,
            "response_normalization": self.response_normalization,
            "runtime_coordination_snapshot": self.runtime_coordination_snapshot,
            "guidance_plan": self.guidance_plan,
            "conversation_cadence_plan": self.conversation_cadence_plan,
            "session_ritual_plan": self.session_ritual_plan,
            "somatic_orchestration_plan": self.somatic_orchestration_plan,
            "proactive_followup_directive": self.proactive_followup_directive,
            "proactive_cadence_plan": self.proactive_cadence_plan,
            "proactive_aggregate_governance_assessment": (
                self.proactive_aggregate_governance_assessment
            ),
            "proactive_aggregate_controller_decision": (
                self.proactive_aggregate_controller_decision
            ),
            "proactive_orchestration_controller_decision": (
                self.proactive_orchestration_controller_decision
            ),
            "proactive_guardrail_plan": self.proactive_guardrail_plan,
            "reengagement_matrix_assessment": self.reengagement_matrix_assessment,
            "reengagement_plan": self.reengagement_plan,
            "proactive_scheduling_plan": self.proactive_scheduling_plan,
            "proactive_orchestration_plan": self.proactive_orchestration_plan,
            "proactive_actuation_plan": self.proactive_actuation_plan,
            "proactive_progression_plan": self.proactive_progression_plan,
            "proactive_stage_controller_decision": (
                self.proactive_stage_controller_decision
            ),
            "proactive_line_controller_decision": self.proactive_line_controller_decision,
            "proactive_line_state_decision": self.proactive_line_state_decision,
            "proactive_line_transition_decision": (
                self.proactive_line_transition_decision
            ),
            "proactive_line_machine_decision": self.proactive_line_machine_decision,
            "proactive_lifecycle_state_decision": (
                self.proactive_lifecycle_state_decision
            ),
            "proactive_lifecycle_transition_decision": (
                self.proactive_lifecycle_transition_decision
            ),
            "proactive_lifecycle_machine_decision": (
                self.proactive_lifecycle_machine_decision
            ),
            "proactive_lifecycle_controller_decision": (
                self.proactive_lifecycle_controller_decision
            ),
            "proactive_lifecycle_envelope_decision": (
                self.proactive_lifecycle_envelope_decision
            ),
            "proactive_lifecycle_scheduler_decision": (
                self.proactive_lifecycle_scheduler_decision
            ),
            "proactive_lifecycle_window_decision": (
                self.proactive_lifecycle_window_decision
            ),
            "proactive_lifecycle_queue_decision": (
                self.proactive_lifecycle_queue_decision
            ),
            "proactive_lifecycle_dispatch_decision": (
                self.proactive_lifecycle_dispatch_decision
            ),
            "proactive_lifecycle_outcome_decision": (
                self.proactive_lifecycle_outcome_decision
            ),
            "proactive_lifecycle_resolution_decision": (
                self.proactive_lifecycle_resolution_decision
            ),
            "proactive_lifecycle_activation_decision": (
                self.proactive_lifecycle_activation_decision
            ),
            "proactive_lifecycle_settlement_decision": (
                self.proactive_lifecycle_settlement_decision
            ),
            "proactive_lifecycle_closure_decision": (
                self.proactive_lifecycle_closure_decision
            ),
            "proactive_lifecycle_availability_decision": (
                self.proactive_lifecycle_availability_decision
            ),
            "proactive_lifecycle_retention_decision": (
                self.proactive_lifecycle_retention_decision
            ),
            "proactive_lifecycle_eligibility_decision": (
                self.proactive_lifecycle_eligibility_decision
            ),
            "proactive_lifecycle_candidate_decision": (
                self.proactive_lifecycle_candidate_decision
            ),
            "proactive_lifecycle_selectability_decision": (
                self.proactive_lifecycle_selectability_decision
            ),
            "proactive_lifecycle_reentry_decision": (
                self.proactive_lifecycle_reentry_decision
            ),
            "proactive_lifecycle_reactivation_decision": (
                self.proactive_lifecycle_reactivation_decision
            ),
            "proactive_lifecycle_resumption_decision": (
                self.proactive_lifecycle_resumption_decision
            ),
            "proactive_lifecycle_readiness_decision": (
                self.proactive_lifecycle_readiness_decision
            ),
            "proactive_lifecycle_arming_decision": (
                self.proactive_lifecycle_arming_decision
            ),
            "proactive_lifecycle_trigger_decision": (
                self.proactive_lifecycle_trigger_decision
            ),
            "proactive_lifecycle_launch_decision": (
                self.proactive_lifecycle_launch_decision
            ),
            "proactive_lifecycle_handoff_decision": (
                self.proactive_lifecycle_handoff_decision
            ),
            "proactive_lifecycle_continuation_decision": (
                self.proactive_lifecycle_continuation_decision
            ),
            "proactive_lifecycle_sustainment_decision": (
                self.proactive_lifecycle_sustainment_decision
            ),
            "proactive_lifecycle_stewardship_decision": (
                self.proactive_lifecycle_stewardship_decision
            ),
            "proactive_lifecycle_guardianship_decision": (
                self.proactive_lifecycle_guardianship_decision
            ),
            "proactive_lifecycle_oversight_decision": (
                self.proactive_lifecycle_oversight_decision
            ),
            "proactive_lifecycle_assurance_decision": (
                self.proactive_lifecycle_assurance_decision
            ),
            "proactive_lifecycle_attestation_decision": (
                self.proactive_lifecycle_attestation_decision
            ),
            "proactive_lifecycle_verification_decision": (
                self.proactive_lifecycle_verification_decision
            ),
            "proactive_lifecycle_certification_decision": (
                self.proactive_lifecycle_certification_decision
            ),
            "proactive_lifecycle_confirmation_decision": (
                self.proactive_lifecycle_confirmation_decision
            ),
            "proactive_lifecycle_ratification_decision": (
                self.proactive_lifecycle_ratification_decision
            ),
            "proactive_lifecycle_endorsement_decision": (
                self.proactive_lifecycle_endorsement_decision
            ),
            "proactive_lifecycle_authorization_decision": (
                self.proactive_lifecycle_authorization_decision
            ),
            "proactive_lifecycle_enactment_decision": (
                self.proactive_lifecycle_enactment_decision
            ),
            "proactive_lifecycle_finality_decision": (
                self.proactive_lifecycle_finality_decision
            ),
            "proactive_lifecycle_completion_decision": (
                self.proactive_lifecycle_completion_decision
            ),
            "proactive_lifecycle_conclusion_decision": (
                self.proactive_lifecycle_conclusion_decision
            ),
            "proactive_lifecycle_disposition_decision": (
                self.proactive_lifecycle_disposition_decision
            ),
            "proactive_lifecycle_standing_decision": (
                self.proactive_lifecycle_standing_decision
            ),
            "proactive_lifecycle_residency_decision": (
                self.proactive_lifecycle_residency_decision
            ),
            "proactive_lifecycle_tenure_decision": self.proactive_lifecycle_tenure_decision,
            "proactive_lifecycle_persistence_decision": (
                self.proactive_lifecycle_persistence_decision
            ),
            "proactive_lifecycle_longevity_decision": (
                self.proactive_lifecycle_longevity_decision
            ),
            "proactive_lifecycle_legacy_decision": self.proactive_lifecycle_legacy_decision,
            "proactive_lifecycle_heritage_decision": (
                self.proactive_lifecycle_heritage_decision
            ),
            "proactive_lifecycle_lineage_decision": (
                self.proactive_lifecycle_lineage_decision
            ),
            "proactive_lifecycle_ancestry_decision": (
                self.proactive_lifecycle_ancestry_decision
            ),
            "proactive_lifecycle_provenance_decision": (
                self.proactive_lifecycle_provenance_decision
            ),
            "proactive_lifecycle_origin_decision": (
                self.proactive_lifecycle_origin_decision
            ),
            "proactive_lifecycle_root_decision": self.proactive_lifecycle_root_decision,
            "proactive_lifecycle_foundation_decision": (
                self.proactive_lifecycle_foundation_decision
            ),
            "proactive_lifecycle_bedrock_decision": (
                self.proactive_lifecycle_bedrock_decision
            ),
            "proactive_lifecycle_substrate_decision": (
                self.proactive_lifecycle_substrate_decision
            ),
            "proactive_lifecycle_stratum_decision": (
                self.proactive_lifecycle_stratum_decision
            ),
            "proactive_lifecycle_layer_decision": (
                self.proactive_lifecycle_layer_decision
            ),
            "proactive_lifecycle_durability_decision": (
                self.proactive_lifecycle_durability_decision
            ),
            "proactive_stage_refresh_plan": self.proactive_stage_refresh_plan,
            "proactive_stage_replan_assessment": (
                self.proactive_stage_replan_assessment
            ),
            "proactive_dispatch_feedback_assessment": (
                self.proactive_dispatch_feedback_assessment
            ),
            "proactive_dispatch_gate_decision": self.proactive_dispatch_gate_decision,
            "proactive_dispatch_envelope_decision": (
                self.proactive_dispatch_envelope_decision
            ),
            "proactive_stage_state_decision": self.proactive_stage_state_decision,
            "proactive_stage_transition_decision": (
                self.proactive_stage_transition_decision
            ),
            "proactive_stage_machine_decision": self.proactive_stage_machine_decision,
            "proactive_followup_dispatch": self.proactive_followup_dispatch,
            "proactive_followup_messages": list(self.proactive_followup_messages),
            "proactive_followup_message_event_count": (
                self.proactive_followup_message_event_count
            ),
            "runtime_quality_doctor_report": self.runtime_quality_doctor_report,
            "system3_snapshot": self.system3_snapshot,
            "private_judgment": self.private_judgment,
            "session_directive": self.session_directive,
            "strategy_decision": self.strategy_decision,
            "llm_failure": self.llm_failure,
        }


@dataclass(slots=True)
class OutputQualitySample:
    turn_index: int
    word_count: int
    lexical_diversity: float
    information_density: float
    opening_signature: str


@dataclass(slots=True)
class StrategyPreferenceRecord:
    session_id: str
    strategy: str
    source: str
    turn_count: int
    session_duration_seconds: float
    duration_signal: float
    relational_signal: float
    quality_floor_score: float
    quality_floor_pass: bool
    noise_penalty: float
    denoised_preference_score: float
    context_stratum: str
    filtering_reasons: list[str]


def _tokenize_text(text: str) -> list[str]:
    return [token for token in re.findall(r"\b\w+\b", text.lower()) if token]


def _content_tokens(tokens: list[str]) -> list[str]:
    return [
        token
        for token in tokens
        if token not in QUALITY_STOPWORDS and (len(token) > 2 or not token.isascii())
    ]


def _series_slope(values: list[float | int]) -> float:
    if len(values) < 2:
        return 0.0
    sample_count = len(values)
    x_mean = (sample_count - 1) / 2
    y_mean = mean(float(value) for value in values)
    numerator = 0.0
    denominator = 0.0
    for index, value in enumerate(values):
        offset = index - x_mean
        numerator += offset * (float(value) - y_mean)
        denominator += offset * offset
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def _distribution_entropy(labels: list[str]) -> float:
    if not labels:
        return 0.0
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    return round(entropy, 3)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class EvaluationService:
    def __init__(self, *, stream_service: StreamService) -> None:
        self._stream_service = stream_service

    async def evaluate_session(self, *, session_id: str) -> dict[str, Any]:
        events = await self._stream_service.read_stream(stream_id=session_id)
        started_event = next(
            (
                event
                for event in events
                if event.event_type == SESSION_STARTED
            ),
            None,
        )
        turn_records = self._build_turn_records(events)
        started_at = started_event.payload.get("created_at") if started_event else None
        last_event_at = events[-1].occurred_at.isoformat() if events else None
        started_metadata = (
            dict(started_event.payload.get("metadata", {}))
            if started_event is not None
            else {}
        )
        summary = self._build_summary(
            session_id=session_id,
            turn_records=turn_records,
            event_count=len(events),
            started_at=started_at,
            last_event_at=last_event_at,
            started_metadata=started_metadata,
        )
        return {
            "session_id": session_id,
            "summary": summary,
            "turns": [record.to_dict() for record in turn_records],
        }

    async def list_session_evaluations(self) -> dict[str, Any]:
        session_ids = await self._stream_service.list_stream_ids()
        summaries = []
        for session_id in session_ids:
            events = await self._stream_service.read_stream(stream_id=session_id)
            if not any(event.event_type == SESSION_STARTED for event in events):
                continue
            evaluation = await self.evaluate_session(session_id=session_id)
            summaries.append(evaluation["summary"])
        return {
            "session_count": len(summaries),
            "sessions": summaries,
        }

    async def _list_non_scenario_session_summaries(self) -> list[dict[str, Any]]:
        evaluations_payload = await self.list_session_evaluations()
        return [
            dict(summary)
            for summary in list(evaluations_payload["sessions"])
            if summary.get("session_source") != "scenario_evaluation"
        ]

    async def build_strategy_preference_report(self) -> dict[str, Any]:
        summaries = [
            summary
            for summary in await self._list_non_scenario_session_summaries()
            if summary.get("latest_strategy")
        ]
        records = [self._build_strategy_preference_record(summary) for summary in summaries]

        strategy_totals: dict[str, dict[str, Any]] = {}
        strata_totals: dict[str, int] = {}
        filtered_records = [record for record in records if not record.quality_floor_pass]
        noisy_records = [record for record in records if record.noise_penalty > 0]

        for record in records:
            strategy_entry = strategy_totals.setdefault(
                record.strategy,
                {
                    "strategy": record.strategy,
                    "session_count": 0,
                    "kept_session_count": 0,
                    "filtered_session_count": 0,
                    "denoised_scores": [],
                    "quality_floor_scores": [],
                    "duration_signals": [],
                    "relational_signals": [],
                    "noise_penalties": [],
                    "strata": {},
                },
            )
            strategy_entry["session_count"] += 1
            if record.quality_floor_pass:
                strategy_entry["kept_session_count"] += 1
                strategy_entry["denoised_scores"].append(
                    record.denoised_preference_score
                )
            else:
                strategy_entry["filtered_session_count"] += 1
            strategy_entry["quality_floor_scores"].append(record.quality_floor_score)
            strategy_entry["duration_signals"].append(record.duration_signal)
            strategy_entry["relational_signals"].append(record.relational_signal)
            strategy_entry["noise_penalties"].append(record.noise_penalty)
            strategy_entry["strata"][record.context_stratum] = (
                strategy_entry["strata"].get(record.context_stratum, 0) + 1
            )
            strata_totals[record.context_stratum] = (
                strata_totals.get(record.context_stratum, 0) + 1
            )

        strategies = []
        for item in strategy_totals.values():
            kept = list(item["denoised_scores"])
            strata = [
                {"context_stratum": key, "count": value}
                for key, value in item["strata"].items()
            ]
            strata.sort(
                key=lambda entry: (
                    int(entry.get("count") or 0),
                    str(entry.get("context_stratum") or ""),
                ),
                reverse=True,
            )
            strategies.append(
                {
                    "strategy": item["strategy"],
                    "session_count": item["session_count"],
                    "kept_session_count": item["kept_session_count"],
                    "filtered_session_count": item["filtered_session_count"],
                    "avg_denoised_preference_score": (
                        round(mean(kept), 3) if kept else None
                    ),
                    "avg_quality_floor_score": round(
                        mean(item["quality_floor_scores"]),
                        3,
                    ),
                    "avg_duration_signal": round(
                        mean(item["duration_signals"]),
                        3,
                    ),
                    "avg_relational_signal": round(
                        mean(item["relational_signals"]),
                        3,
                    ),
                    "avg_noise_penalty": round(mean(item["noise_penalties"]), 3),
                    "dominant_strata": strata[:3],
                }
            )
        strategies.sort(
            key=lambda item: (
                item.get("avg_denoised_preference_score") is not None,
                float(item.get("avg_denoised_preference_score") or 0.0),
                float(item.get("avg_quality_floor_score") or 0.0),
                int(item.get("session_count") or 0),
            ),
            reverse=True,
        )

        strata = [
            {"context_stratum": key, "count": value}
            for key, value in strata_totals.items()
        ]
        strata.sort(
            key=lambda item: (
                int(item.get("count") or 0),
                str(item.get("context_stratum") or ""),
            ),
            reverse=True,
        )

        return {
            "session_count": len(records),
            "strategy_count": len(strategies),
            "filtered_session_count": len(filtered_records),
            "noisy_session_count": len(noisy_records),
            "methodology": {
                "quality_floor_filter": (
                    "Filter out sessions with poor audit quality, low safety, severe "
                    "output degradation, or repeated runtime failures."
                ),
                "main_signal": (
                    "Prefer session duration and relational quality over raw turn count."
                ),
                "noise_control": (
                    "Penalize fast churn sessions where turn count grows without "
                    "real dwell time."
                ),
            },
            "context_strata": strata,
            "strategies": strategies,
            "filtered_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy": record.strategy,
                    "quality_floor_score": record.quality_floor_score,
                    "filtering_reasons": record.filtering_reasons,
                }
                for record in filtered_records[:5]
            ],
            "noisy_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy": record.strategy,
                    "noise_penalty": record.noise_penalty,
                    "turn_count": record.turn_count,
                    "session_duration_seconds": record.session_duration_seconds,
                }
                for record in noisy_records[:5]
            ],
            "reengagement_learning": await self.build_reengagement_learning_report(),
        }

    async def build_reengagement_learning_report(
        self,
        *,
        context_stratum: str | None = None,
        strategy_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        requested_strategy_keys = {
            str(item)
            for item in list(strategy_keys or [])
            if str(item or "").strip()
        }
        summaries = [
            summary
            for summary in await self._list_non_scenario_session_summaries()
            if summary.get("latest_reengagement_strategy_key")
            and summary.get("latest_reengagement_strategy_key") != "hold"
            and (
                not requested_strategy_keys
                or str(summary.get("latest_reengagement_strategy_key"))
                in requested_strategy_keys
            )
        ]
        records = [
            self._build_reengagement_preference_record(summary) for summary in summaries
        ]
        filtered_records = [record for record in records if not record.quality_floor_pass]
        noisy_records = [record for record in records if record.noise_penalty > 0]
        matching_context_records = [
            record
            for record in records
            if context_stratum and record.context_stratum == context_stratum
        ]

        strategy_totals: dict[str, dict[str, Any]] = {}
        strata_totals: dict[str, int] = {}
        for record in records:
            strategy_entry = strategy_totals.setdefault(
                record.strategy,
                {
                    "strategy_key": record.strategy,
                    "session_count": 0,
                    "kept_session_count": 0,
                    "filtered_session_count": 0,
                    "learning_scores": [],
                    "quality_floor_scores": [],
                    "duration_signals": [],
                    "relational_signals": [],
                    "noise_penalties": [],
                    "strata": {},
                    "contextual_learning_scores": [],
                    "contextual_kept_session_count": 0,
                },
            )
            strategy_entry["session_count"] += 1
            if record.quality_floor_pass:
                strategy_entry["kept_session_count"] += 1
                strategy_entry["learning_scores"].append(
                    record.denoised_preference_score
                )
                if context_stratum and record.context_stratum == context_stratum:
                    strategy_entry["contextual_learning_scores"].append(
                        record.denoised_preference_score
                    )
                    strategy_entry["contextual_kept_session_count"] += 1
            else:
                strategy_entry["filtered_session_count"] += 1
            strategy_entry["quality_floor_scores"].append(record.quality_floor_score)
            strategy_entry["duration_signals"].append(record.duration_signal)
            strategy_entry["relational_signals"].append(record.relational_signal)
            strategy_entry["noise_penalties"].append(record.noise_penalty)
            strategy_entry["strata"][record.context_stratum] = (
                strategy_entry["strata"].get(record.context_stratum, 0) + 1
            )
            strata_totals[record.context_stratum] = (
                strata_totals.get(record.context_stratum, 0) + 1
            )

        strategies = []
        for item in strategy_totals.values():
            strata = [
                {"context_stratum": key, "count": value}
                for key, value in item["strata"].items()
            ]
            strata.sort(
                key=lambda entry: (
                    int(entry.get("count") or 0),
                    str(entry.get("context_stratum") or ""),
                ),
                reverse=True,
            )
            learning_scores = list(item["learning_scores"])
            contextual_learning_scores = list(item["contextual_learning_scores"])
            strategies.append(
                {
                    "strategy_key": item["strategy_key"],
                    "session_count": item["session_count"],
                    "kept_session_count": item["kept_session_count"],
                    "filtered_session_count": item["filtered_session_count"],
                    "avg_learning_score": (
                        round(mean(learning_scores), 3) if learning_scores else None
                    ),
                    "avg_contextual_learning_score": (
                        round(mean(contextual_learning_scores), 3)
                        if contextual_learning_scores
                        else None
                    ),
                    "contextual_kept_session_count": item[
                        "contextual_kept_session_count"
                    ],
                    "avg_quality_floor_score": round(
                        mean(item["quality_floor_scores"]),
                        3,
                    ),
                    "avg_duration_signal": round(
                        mean(item["duration_signals"]),
                        3,
                    ),
                    "avg_relational_signal": round(
                        mean(item["relational_signals"]),
                        3,
                    ),
                    "avg_noise_penalty": round(mean(item["noise_penalties"]), 3),
                    "dominant_strata": strata[:3],
                }
            )
        strategies.sort(
            key=lambda item: (
                item.get("avg_contextual_learning_score") is not None,
                float(item.get("avg_contextual_learning_score") or 0.0),
                float(item.get("avg_learning_score") or 0.0),
                int(item.get("contextual_kept_session_count") or 0),
                int(item.get("kept_session_count") or 0),
            ),
            reverse=True,
        )

        strata = [
            {"context_stratum": key, "count": value}
            for key, value in strata_totals.items()
        ]
        strata.sort(
            key=lambda item: (
                int(item.get("count") or 0),
                str(item.get("context_stratum") or ""),
            ),
            reverse=True,
        )

        learning_mode = "cold_start"
        if strategies:
            top_strategy = strategies[0]
            if context_stratum and int(
                top_strategy.get("contextual_kept_session_count") or 0
            ) > 0:
                learning_mode = "contextual_reinforcement"
            elif int(top_strategy.get("kept_session_count") or 0) > 0:
                learning_mode = "global_reinforcement"

        return {
            "session_count": len(records),
            "strategy_count": len(strategies),
            "filtered_session_count": len(filtered_records),
            "noisy_session_count": len(noisy_records),
            "matching_context_session_count": len(matching_context_records),
            "context_stratum": context_stratum,
            "learning_mode": learning_mode,
            "methodology": {
                "quality_floor_filter": (
                    "Filter out sessions with poor audit quality, low safety, severe "
                    "output degradation, or repeated runtime failures."
                ),
                "main_signal": (
                    "Prefer session duration and relational quality over raw turn count."
                ),
                "context_bias": (
                    "Prefer matching repair/boundary/dependency context when enough "
                    "history exists, otherwise fall back to global re-engagement signal."
                ),
            },
            "context_strata": strata,
            "strategies": strategies,
            "filtered_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy_key": record.strategy,
                    "quality_floor_score": record.quality_floor_score,
                    "filtering_reasons": record.filtering_reasons,
                }
                for record in filtered_records[:5]
            ],
            "noisy_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy_key": record.strategy,
                    "noise_penalty": record.noise_penalty,
                    "turn_count": record.turn_count,
                    "session_duration_seconds": record.session_duration_seconds,
                }
                for record in noisy_records[:5]
            ],
        }

    def _build_turn_records(self, events: list[StoredEvent]) -> list[TurnRecord]:
        turns: list[TurnRecord] = []
        current_turn: TurnRecord | None = None

        for event in events:
            if event.event_type == USER_MESSAGE_RECEIVED:
                if current_turn is not None:
                    turns.append(current_turn)
                current_turn = TurnRecord(
                    turn_index=len(turns) + 1,
                    user_message=str(event.payload.get("content", "")),
                )
                continue

            if current_turn is None:
                continue

            if event.event_type == ASSISTANT_MESSAGE_SENT:
                content = str(event.payload.get("content", ""))
                if str(event.payload.get("delivery_mode", "")) == "proactive_followup":
                    current_turn.proactive_followup_message_event_count += 1
                    if content:
                        current_turn.proactive_followup_messages.append(content)
                    continue
                current_turn.assistant_message_event_count += 1
                if content:
                    current_turn.assistant_responses.append(content)
                    current_turn.assistant_message = (
                        f"{current_turn.assistant_message} {content}".strip()
                        if current_turn.assistant_message
                        else content
                    )
            elif event.event_type == CONFIDENCE_ASSESSMENT_COMPUTED:
                current_turn.confidence_assessment = dict(event.payload)
            elif event.event_type == CONTEXT_FRAME_COMPUTED:
                current_turn.context_frame = dict(event.payload)
            elif event.event_type == RELATIONSHIP_STATE_UPDATED:
                current_turn.relationship_state = dict(event.payload)
            elif event.event_type == REPAIR_ASSESSMENT_COMPUTED:
                current_turn.repair_assessment = dict(event.payload)
            elif event.event_type == MEMORY_BUNDLE_UPDATED:
                current_turn.memory_bundle = dict(event.payload)
            elif event.event_type == MEMORY_WRITE_GUARD_EVALUATED:
                current_turn.memory_write_guard = dict(event.payload)
            elif event.event_type == MEMORY_RETENTION_POLICY_APPLIED:
                current_turn.memory_retention = dict(event.payload)
            elif event.event_type == MEMORY_RECALL_PERFORMED:
                current_turn.memory_recall = dict(event.payload)
            elif event.event_type == MEMORY_FORGETTING_APPLIED:
                current_turn.memory_forgetting = dict(event.payload)
            elif event.event_type == KNOWLEDGE_BOUNDARY_DECIDED:
                current_turn.knowledge_boundary_decision = dict(event.payload)
            elif event.event_type == POLICY_GATE_DECIDED:
                current_turn.policy_gate = dict(event.payload)
            elif event.event_type == REHEARSAL_COMPLETED:
                current_turn.rehearsal_result = dict(event.payload)
            elif event.event_type == REPAIR_PLAN_UPDATED:
                current_turn.repair_plan = dict(event.payload)
            elif event.event_type == EMPOWERMENT_AUDIT_COMPLETED:
                current_turn.empowerment_audit = dict(event.payload)
            elif event.event_type == RESPONSE_DRAFT_PLANNED:
                current_turn.response_draft_plan = dict(event.payload)
            elif event.event_type == RESPONSE_RENDERING_POLICY_DECIDED:
                current_turn.response_rendering_policy = dict(event.payload)
            elif event.event_type == RESPONSE_SEQUENCE_PLANNED:
                current_turn.response_sequence_plan = dict(event.payload)
            elif event.event_type == RUNTIME_COORDINATION_UPDATED:
                current_turn.runtime_coordination_snapshot = dict(event.payload)
            elif event.event_type == GUIDANCE_PLAN_UPDATED:
                current_turn.guidance_plan = dict(event.payload)
            elif event.event_type == CONVERSATION_CADENCE_UPDATED:
                current_turn.conversation_cadence_plan = dict(event.payload)
            elif event.event_type == SESSION_RITUAL_UPDATED:
                current_turn.session_ritual_plan = dict(event.payload)
            elif event.event_type == SOMATIC_ORCHESTRATION_UPDATED:
                current_turn.somatic_orchestration_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_FOLLOWUP_UPDATED:
                current_turn.proactive_followup_directive = dict(event.payload)
            elif event.event_type == PROACTIVE_CADENCE_UPDATED:
                current_turn.proactive_cadence_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED:
                current_turn.proactive_aggregate_governance_assessment = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_AGGREGATE_CONTROLLER_UPDATED:
                current_turn.proactive_aggregate_controller_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED:
                current_turn.proactive_orchestration_controller_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_GUARDRAIL_UPDATED:
                current_turn.proactive_guardrail_plan = dict(event.payload)
            elif event.event_type == REENGAGEMENT_MATRIX_ASSESSED:
                current_turn.reengagement_matrix_assessment = dict(event.payload)
            elif event.event_type == REENGAGEMENT_PLAN_UPDATED:
                current_turn.reengagement_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_SCHEDULING_UPDATED:
                current_turn.proactive_scheduling_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_ORCHESTRATION_UPDATED:
                current_turn.proactive_orchestration_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_ACTUATION_UPDATED:
                current_turn.proactive_actuation_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_PROGRESSION_UPDATED:
                current_turn.proactive_progression_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_CONTROLLER_UPDATED:
                current_turn.proactive_stage_controller_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_CONTROLLER_UPDATED:
                current_turn.proactive_line_controller_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_STATE_UPDATED:
                current_turn.proactive_line_state_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_TRANSITION_UPDATED:
                current_turn.proactive_line_transition_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_MACHINE_UPDATED:
                current_turn.proactive_line_machine_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_STATE_UPDATED:
                current_turn.proactive_lifecycle_state_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_TRANSITION_UPDATED:
                current_turn.proactive_lifecycle_transition_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_MACHINE_UPDATED:
                current_turn.proactive_lifecycle_machine_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED:
                current_turn.proactive_lifecycle_controller_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED:
                current_turn.proactive_lifecycle_envelope_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED:
                current_turn.proactive_lifecycle_scheduler_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_WINDOW_UPDATED:
                current_turn.proactive_lifecycle_window_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_QUEUE_UPDATED:
                current_turn.proactive_lifecycle_queue_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_DISPATCH_UPDATED:
                current_turn.proactive_lifecycle_dispatch_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_OUTCOME_UPDATED:
                current_turn.proactive_lifecycle_outcome_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED:
                current_turn.proactive_lifecycle_resolution_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED:
                current_turn.proactive_lifecycle_activation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED:
                current_turn.proactive_lifecycle_settlement_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CLOSURE_UPDATED:
                current_turn.proactive_lifecycle_closure_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED:
                current_turn.proactive_lifecycle_availability_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RETENTION_UPDATED:
                current_turn.proactive_lifecycle_retention_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED:
                current_turn.proactive_lifecycle_eligibility_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED:
                current_turn.proactive_lifecycle_candidate_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED:
                current_turn.proactive_lifecycle_selectability_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_REENTRY_UPDATED:
                current_turn.proactive_lifecycle_reentry_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED:
                current_turn.proactive_lifecycle_reactivation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED:
                current_turn.proactive_lifecycle_resumption_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_READINESS_UPDATED:
                current_turn.proactive_lifecycle_readiness_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ARMING_UPDATED:
                current_turn.proactive_lifecycle_arming_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_TRIGGER_UPDATED:
                current_turn.proactive_lifecycle_trigger_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_LAUNCH_UPDATED:
                current_turn.proactive_lifecycle_launch_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_HANDOFF_UPDATED:
                current_turn.proactive_lifecycle_handoff_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED:
                current_turn.proactive_lifecycle_continuation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED:
                current_turn.proactive_lifecycle_sustainment_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED:
                current_turn.proactive_lifecycle_stewardship_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED:
                current_turn.proactive_lifecycle_guardianship_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED:
                current_turn.proactive_lifecycle_oversight_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED:
                current_turn.proactive_lifecycle_assurance_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED:
                current_turn.proactive_lifecycle_attestation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED:
                current_turn.proactive_lifecycle_verification_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED:
                current_turn.proactive_lifecycle_certification_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED:
                current_turn.proactive_lifecycle_confirmation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED:
                current_turn.proactive_lifecycle_ratification_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED:
                current_turn.proactive_lifecycle_endorsement_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED:
                current_turn.proactive_lifecycle_authorization_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED:
                current_turn.proactive_lifecycle_enactment_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_FINALITY_UPDATED:
                current_turn.proactive_lifecycle_finality_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_COMPLETION_UPDATED:
                current_turn.proactive_lifecycle_completion_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED:
                current_turn.proactive_lifecycle_conclusion_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED:
                current_turn.proactive_lifecycle_disposition_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_STANDING_UPDATED:
                current_turn.proactive_lifecycle_standing_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED:
                current_turn.proactive_lifecycle_residency_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_TENURE_UPDATED:
                current_turn.proactive_lifecycle_tenure_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED:
                current_turn.proactive_lifecycle_persistence_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED:
                current_turn.proactive_lifecycle_longevity_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_LEGACY_UPDATED:
                current_turn.proactive_lifecycle_legacy_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_HERITAGE_UPDATED:
                current_turn.proactive_lifecycle_heritage_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_LINEAGE_UPDATED:
                current_turn.proactive_lifecycle_lineage_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED:
                current_turn.proactive_lifecycle_ancestry_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED:
                current_turn.proactive_lifecycle_provenance_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ORIGIN_UPDATED:
                current_turn.proactive_lifecycle_origin_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_ROOT_UPDATED:
                current_turn.proactive_lifecycle_root_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED:
                current_turn.proactive_lifecycle_foundation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_BEDROCK_UPDATED:
                current_turn.proactive_lifecycle_bedrock_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED:
                current_turn.proactive_lifecycle_substrate_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_STRATUM_UPDATED:
                current_turn.proactive_lifecycle_stratum_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_LAYER_UPDATED:
                current_turn.proactive_lifecycle_layer_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_DURABILITY_UPDATED:
                current_turn.proactive_lifecycle_durability_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_STAGE_REFRESH_UPDATED:
                current_turn.proactive_stage_refresh_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_REPLAN_UPDATED:
                current_turn.proactive_stage_replan_assessment = dict(event.payload)
            elif event.event_type == PROACTIVE_DISPATCH_FEEDBACK_ASSESSED:
                current_turn.proactive_dispatch_feedback_assessment = dict(event.payload)
            elif event.event_type == PROACTIVE_DISPATCH_GATE_UPDATED:
                current_turn.proactive_dispatch_gate_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_DISPATCH_ENVELOPE_UPDATED:
                current_turn.proactive_dispatch_envelope_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_STATE_UPDATED:
                current_turn.proactive_stage_state_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_TRANSITION_UPDATED:
                current_turn.proactive_stage_transition_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_MACHINE_UPDATED:
                current_turn.proactive_stage_machine_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED:
                current_turn.proactive_followup_dispatch = dict(event.payload)
            elif event.event_type == RESPONSE_NORMALIZED:
                current_turn.response_normalization = dict(event.payload)
            elif event.event_type == RESPONSE_POST_AUDITED:
                current_turn.response_post_audit = dict(event.payload)
            elif event.event_type == RUNTIME_QUALITY_DOCTOR_COMPLETED:
                current_turn.runtime_quality_doctor_report = dict(event.payload)
            elif event.event_type == SYSTEM3_SNAPSHOT_UPDATED:
                current_turn.system3_snapshot = dict(event.payload)
            elif event.event_type == PRIVATE_JUDGMENT_COMPUTED:
                current_turn.private_judgment = dict(event.payload)
            elif event.event_type == SESSION_DIRECTIVE_UPDATED:
                current_turn.session_directive = dict(event.payload.get("directive", {}))
                current_turn.strategy_decision = dict(event.payload.get("strategy", {}))
            elif event.event_type == LLM_COMPLETION_FAILED:
                current_turn.llm_failure = dict(event.payload)

        if current_turn is not None:
            turns.append(current_turn)

        return turns

    def _build_summary(
        self,
        *,
        session_id: str,
        turn_records: list[TurnRecord],
        event_count: int,
        started_at: str | None,
        last_event_at: str | None,
        started_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        bid_turns = [
            turn
            for turn in turn_records
            if (turn.context_frame or {}).get("bid_signal") not in {None, "low_signal"}
        ]
        responded_bids = [turn for turn in bid_turns if turn.assistant_message]
        safety_scores = [
            float((turn.relationship_state or {}).get("psychological_safety"))
            for turn in turn_records
            if (turn.relationship_state or {}).get("psychological_safety") is not None
        ]
        rupture_turns = [
            turn
            for turn in turn_records
            if bool((turn.repair_plan or {}).get("rupture_detected"))
        ]
        severe_repair_turns = [
            turn
            for turn in turn_records
            if (turn.repair_assessment or {}).get("severity") == "high"
        ]
        dependency_turns = [
            turn
            for turn in turn_records
            if (turn.relationship_state or {}).get("dependency_risk") == "elevated"
        ]
        llm_failures = [turn for turn in turn_records if turn.llm_failure is not None]
        low_confidence_turns = [
            turn
            for turn in turn_records
            if (turn.confidence_assessment or {}).get("level") == "low"
        ]
        clarification_turns = [
            turn
            for turn in turn_records
            if bool((turn.confidence_assessment or {}).get("needs_clarification"))
        ]
        uncertainty_disclosure_turns = [
            turn
            for turn in turn_records
            if bool((turn.confidence_assessment or {}).get("should_disclose_uncertainty"))
        ]
        recalled_turns = [
            turn
            for turn in turn_records
            if int((turn.memory_recall or {}).get("recall_count", 0)) > 0
        ]
        filtered_recall_turns = [
            turn
            for turn in turn_records
            if int((turn.memory_recall or {}).get("integrity_summary", {}).get("filtered_count", 0))
            > 0
        ]
        blocked_memory_turns = [
            turn
            for turn in turn_records
            if int((turn.memory_write_guard or {}).get("blocked_count", 0)) > 0
        ]
        forgetting_turns = [
            turn
            for turn in turn_records
            if int((turn.memory_forgetting or {}).get("evicted_count", 0)) > 0
        ]
        retention_turns = [
            turn
            for turn in turn_records
            if int((turn.memory_retention or {}).get("pinned_count", 0)) > 0
        ]
        boundary_intervention_turns = [
            turn
            for turn in turn_records
            if (turn.knowledge_boundary_decision or {}).get("decision")
            not in {None, "answer_directly"}
        ]
        guarded_policy_turns = [
            turn
            for turn in turn_records
            if (turn.policy_gate or {}).get("empowerment_risk") == "guarded"
        ]
        boundary_sensitive_policy_turns = [
            turn
            for turn in turn_records
            if (turn.policy_gate or {}).get("red_line_status") == "boundary_sensitive"
        ]
        high_risk_rehearsal_turns = [
            turn
            for turn in turn_records
            if (turn.rehearsal_result or {}).get("projected_risk_level") == "high"
        ]
        empowerment_audit_caution_turns = [
            turn
            for turn in turn_records
            if (turn.empowerment_audit or {}).get("status") == "caution"
        ]
        empowerment_audit_revise_turns = [
            turn
            for turn in turn_records
            if (turn.empowerment_audit or {}).get("status") == "revise"
        ]
        response_draft_question_turns = [
            turn
            for turn in turn_records
            if (turn.response_draft_plan or {}).get("question_strategy") not in {None, "none"}
        ]
        response_draft_constrained_turns = [
            turn
            for turn in turn_records
            if len((turn.response_draft_plan or {}).get("phrasing_constraints", [])) > 0
        ]
        response_rendering_boundary_turns = [
            turn
            for turn in turn_records
            if bool((turn.response_rendering_policy or {}).get("include_boundary_statement"))
        ]
        response_rendering_uncertainty_turns = [
            turn
            for turn in turn_records
            if bool(
                (turn.response_rendering_policy or {}).get(
                    "include_uncertainty_statement"
                )
            )
        ]
        response_post_audit_review_turns = [
            turn
            for turn in turn_records
            if (turn.response_post_audit or {}).get("status") == "review"
        ]
        response_post_audit_revise_turns = [
            turn
            for turn in turn_records
            if (turn.response_post_audit or {}).get("status") == "revise"
        ]
        continuous_output_turns = [
            turn
            for turn in turn_records
            if (turn.response_sequence_plan or {}).get("mode") == "two_part_sequence"
            or turn.assistant_message_event_count > 1
        ]
        runtime_coordination_snapshots = [
            turn
            for turn in turn_records
            if turn.runtime_coordination_snapshot is not None
        ]
        reengagement_turns = [
            turn
            for turn in runtime_coordination_snapshots
            if (turn.runtime_coordination_snapshot or {}).get("time_awareness_mode")
            in {"resume", "reengagement"}
        ]
        high_cognitive_load_turns = [
            turn
            for turn in runtime_coordination_snapshots
            if (turn.runtime_coordination_snapshot or {}).get("cognitive_load_band")
            == "high"
        ]
        proactive_followup_turns = [
            turn
            for turn in runtime_coordination_snapshots
            if bool(
                (turn.runtime_coordination_snapshot or {}).get(
                    "proactive_followup_eligible"
                )
            )
        ]
        proactive_cadence_plans = [
            turn for turn in turn_records if turn.proactive_cadence_plan is not None
        ]
        proactive_guardrail_plans = [
            turn for turn in turn_records if turn.proactive_guardrail_plan is not None
        ]
        proactive_guardrail_reduced_turns = [
            turn
            for turn in proactive_guardrail_plans
            if int((turn.proactive_guardrail_plan or {}).get("max_dispatch_count", 0))
            < len((turn.proactive_guardrail_plan or {}).get("stage_guardrails", []))
        ]
        proactive_guardrail_hard_stop_turns = [
            turn
            for turn in proactive_guardrail_plans
            if list((turn.proactive_guardrail_plan or {}).get("hard_stop_conditions", []))
        ]
        proactive_scheduling_plans = [
            turn for turn in turn_records if turn.proactive_scheduling_plan is not None
        ]
        proactive_scheduling_deferred_turns = [
            turn
            for turn in proactive_scheduling_plans
            if int(
                (turn.proactive_scheduling_plan or {}).get(
                    "first_touch_extra_delay_seconds",
                    0,
                )
                or 0
            )
            > 0
        ]
        proactive_orchestration_plans = [
            turn for turn in turn_records if turn.proactive_orchestration_plan is not None
        ]
        proactive_orchestration_multi_stage_turns = [
            turn
            for turn in proactive_orchestration_plans
            if len((turn.proactive_orchestration_plan or {}).get("stage_directives", []))
            > 1
        ]
        proactive_actuation_plans = [
            turn for turn in turn_records if turn.proactive_actuation_plan is not None
        ]
        proactive_actuation_multi_stage_turns = [
            turn
            for turn in proactive_actuation_plans
            if len((turn.proactive_actuation_plan or {}).get("stage_actuations", [])) > 1
        ]
        proactive_progression_plans = [
            turn for turn in turn_records if turn.proactive_progression_plan is not None
        ]
        proactive_progression_multi_stage_turns = [
            turn
            for turn in proactive_progression_plans
            if len((turn.proactive_progression_plan or {}).get("stage_progressions", []))
            > 1
        ]
        proactive_stage_controller_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_stage_controller_decision is not None
        ]
        proactive_stage_controller_changed_turns = [
            turn
            for turn in proactive_stage_controller_decisions
            if bool((turn.proactive_stage_controller_decision or {}).get("changed"))
        ]
        proactive_line_controller_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_line_controller_decision is not None
        ]
        proactive_line_controller_changed_turns = [
            turn
            for turn in proactive_line_controller_decisions
            if bool((turn.proactive_line_controller_decision or {}).get("changed"))
        ]
        proactive_line_state_decisions = [
            turn for turn in turn_records if turn.proactive_line_state_decision is not None
        ]
        proactive_line_state_changed_turns = [
            turn
            for turn in proactive_line_state_decisions
            if bool((turn.proactive_line_state_decision or {}).get("changed"))
        ]
        proactive_line_state_buffered_turns = [
            turn
            for turn in proactive_line_state_decisions
            if (turn.proactive_line_state_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_line_state_terminal_turns = [
            turn
            for turn in proactive_line_state_decisions
            if (turn.proactive_line_state_decision or {}).get("lifecycle_mode")
            == "terminal"
        ]
        proactive_line_transition_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_line_transition_decision is not None
        ]
        proactive_line_transition_changed_turns = [
            turn
            for turn in proactive_line_transition_decisions
            if bool((turn.proactive_line_transition_decision or {}).get("changed"))
        ]
        proactive_line_transition_buffered_turns = [
            turn
            for turn in proactive_line_transition_decisions
            if (turn.proactive_line_transition_decision or {}).get("transition_mode")
            in {"buffer_line", "soften_line"}
        ]
        proactive_line_transition_terminal_turns = [
            turn
            for turn in proactive_line_transition_decisions
            if (turn.proactive_line_transition_decision or {}).get("line_exit_mode")
            == "retire"
        ]
        proactive_line_machine_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_line_machine_decision is not None
        ]
        proactive_line_machine_changed_turns = [
            turn
            for turn in proactive_line_machine_decisions
            if bool((turn.proactive_line_machine_decision or {}).get("changed"))
        ]
        proactive_line_machine_buffered_turns = [
            turn
            for turn in proactive_line_machine_decisions
            if (turn.proactive_line_machine_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_line_machine_terminal_turns = [
            turn
            for turn in proactive_line_machine_decisions
            if (turn.proactive_line_machine_decision or {}).get("lifecycle_mode")
            == "terminal"
        ]
        proactive_lifecycle_state_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_state_decision is not None
        ]
        proactive_lifecycle_state_changed_turns = [
            turn
            for turn in proactive_lifecycle_state_decisions
            if bool((turn.proactive_lifecycle_state_decision or {}).get("changed"))
        ]
        proactive_lifecycle_state_buffered_turns = [
            turn
            for turn in proactive_lifecycle_state_decisions
            if (turn.proactive_lifecycle_state_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_lifecycle_state_terminal_turns = [
            turn
            for turn in proactive_lifecycle_state_decisions
            if (turn.proactive_lifecycle_state_decision or {}).get("lifecycle_mode")
            == "terminal"
        ]
        proactive_lifecycle_transition_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_transition_decision is not None
        ]
        proactive_lifecycle_transition_changed_turns = [
            turn
            for turn in proactive_lifecycle_transition_decisions
            if bool((turn.proactive_lifecycle_transition_decision or {}).get("changed"))
        ]
        proactive_lifecycle_transition_buffered_turns = [
            turn
            for turn in proactive_lifecycle_transition_decisions
            if (turn.proactive_lifecycle_transition_decision or {}).get("transition_mode")
            in {"buffer_lifecycle", "soften_lifecycle"}
        ]
        proactive_lifecycle_transition_terminal_turns = [
            turn
            for turn in proactive_lifecycle_transition_decisions
            if (
                (turn.proactive_lifecycle_transition_decision or {}).get(
                    "lifecycle_exit_mode"
                )
                == "retire"
            )
        ]
        proactive_lifecycle_machine_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_machine_decision is not None
        ]
        proactive_lifecycle_machine_changed_turns = [
            turn
            for turn in proactive_lifecycle_machine_decisions
            if bool((turn.proactive_lifecycle_machine_decision or {}).get("changed"))
        ]
        proactive_lifecycle_machine_buffered_turns = [
            turn
            for turn in proactive_lifecycle_machine_decisions
            if (turn.proactive_lifecycle_machine_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_lifecycle_machine_terminal_turns = [
            turn
            for turn in proactive_lifecycle_machine_decisions
            if (turn.proactive_lifecycle_machine_decision or {}).get("lifecycle_mode")
            == "terminal"
        ]
        proactive_lifecycle_controller_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_controller_decision is not None
        ]
        proactive_lifecycle_controller_changed_turns = [
            turn
            for turn in proactive_lifecycle_controller_decisions
            if bool((turn.proactive_lifecycle_controller_decision or {}).get("changed"))
        ]
        proactive_lifecycle_controller_buffered_turns = [
            turn
            for turn in proactive_lifecycle_controller_decisions
            if (turn.proactive_lifecycle_controller_decision or {}).get("decision")
            in {"buffer_lifecycle", "soften_lifecycle"}
        ]
        proactive_lifecycle_controller_terminal_turns = [
            turn
            for turn in proactive_lifecycle_controller_decisions
            if (turn.proactive_lifecycle_controller_decision or {}).get(
                "lifecycle_state"
            )
            == "terminal"
        ]
        proactive_lifecycle_envelope_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_envelope_decision is not None
        ]
        proactive_lifecycle_envelope_changed_turns = [
            turn
            for turn in proactive_lifecycle_envelope_decisions
            if bool((turn.proactive_lifecycle_envelope_decision or {}).get("changed"))
        ]
        proactive_lifecycle_envelope_buffered_turns = [
            turn
            for turn in proactive_lifecycle_envelope_decisions
            if (turn.proactive_lifecycle_envelope_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_lifecycle_envelope_terminal_turns = [
            turn
            for turn in proactive_lifecycle_envelope_decisions
            if (turn.proactive_lifecycle_envelope_decision or {}).get(
                "lifecycle_state"
            )
            == "terminal"
        ]
        proactive_lifecycle_scheduler_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_scheduler_decision is not None
        ]
        proactive_lifecycle_scheduler_changed_turns = [
            turn
            for turn in proactive_lifecycle_scheduler_decisions
            if bool((turn.proactive_lifecycle_scheduler_decision or {}).get("changed"))
        ]
        proactive_lifecycle_scheduler_buffered_turns = [
            turn
            for turn in proactive_lifecycle_scheduler_decisions
            if (turn.proactive_lifecycle_scheduler_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_lifecycle_scheduler_terminal_turns = [
            turn
            for turn in proactive_lifecycle_scheduler_decisions
            if (turn.proactive_lifecycle_scheduler_decision or {}).get(
                "lifecycle_state"
            )
            == "terminal"
        ]
        proactive_lifecycle_window_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_window_decision is not None
        ]
        proactive_lifecycle_window_changed_turns = [
            turn
            for turn in proactive_lifecycle_window_decisions
            if bool((turn.proactive_lifecycle_window_decision or {}).get("changed"))
        ]
        proactive_lifecycle_window_buffered_turns = [
            turn
            for turn in proactive_lifecycle_window_decisions
            if (turn.proactive_lifecycle_window_decision or {}).get("actionability")
            in {"buffer", "soften"}
        ]
        proactive_lifecycle_window_terminal_turns = [
            turn
            for turn in proactive_lifecycle_window_decisions
            if (turn.proactive_lifecycle_window_decision or {}).get("queue_status")
            == "terminal"
        ]
        proactive_lifecycle_queue_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_queue_decision is not None
        ]
        proactive_lifecycle_queue_changed_turns = [
            turn
            for turn in proactive_lifecycle_queue_decisions
            if bool((turn.proactive_lifecycle_queue_decision or {}).get("changed"))
        ]
        proactive_lifecycle_queue_buffered_turns = [
            turn
            for turn in proactive_lifecycle_queue_decisions
            if (turn.proactive_lifecycle_queue_decision or {}).get("actionability")
            in {"buffer", "wait"}
        ]
        proactive_lifecycle_queue_terminal_turns = [
            turn
            for turn in proactive_lifecycle_queue_decisions
            if (turn.proactive_lifecycle_queue_decision or {}).get("queue_status")
            == "terminal"
        ]
        proactive_lifecycle_dispatch_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_dispatch_decision is not None
        ]
        proactive_lifecycle_dispatch_changed_turns = [
            turn
            for turn in proactive_lifecycle_dispatch_decisions
            if bool((turn.proactive_lifecycle_dispatch_decision or {}).get("changed"))
        ]
        proactive_lifecycle_dispatch_sent_turns = [
            turn
            for turn in proactive_lifecycle_dispatch_decisions
            if (turn.proactive_lifecycle_dispatch_decision or {}).get("decision")
            in {"dispatch_lifecycle_now", "close_loop_lifecycle_dispatch"}
        ]
        proactive_lifecycle_dispatch_rescheduled_turns = [
            turn
            for turn in proactive_lifecycle_dispatch_decisions
            if (turn.proactive_lifecycle_dispatch_decision or {}).get("decision")
            == "reschedule_lifecycle_dispatch"
        ]
        proactive_lifecycle_dispatch_hold_turns = [
            turn
            for turn in proactive_lifecycle_dispatch_decisions
            if (turn.proactive_lifecycle_dispatch_decision or {}).get("decision")
            == "hold_lifecycle_dispatch"
        ]
        proactive_lifecycle_dispatch_retire_turns = [
            turn
            for turn in proactive_lifecycle_dispatch_decisions
            if (turn.proactive_lifecycle_dispatch_decision or {}).get("decision")
            == "retire_lifecycle_dispatch"
        ]
        proactive_lifecycle_outcome_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_outcome_decision is not None
        ]
        proactive_lifecycle_outcome_changed_turns = [
            turn
            for turn in proactive_lifecycle_outcome_decisions
            if bool((turn.proactive_lifecycle_outcome_decision or {}).get("changed"))
        ]
        proactive_lifecycle_outcome_sent_turns = [
            turn
            for turn in proactive_lifecycle_outcome_decisions
            if (turn.proactive_lifecycle_outcome_decision or {}).get("decision")
            in {"lifecycle_dispatch_sent", "lifecycle_close_loop_sent"}
        ]
        proactive_lifecycle_outcome_rescheduled_turns = [
            turn
            for turn in proactive_lifecycle_outcome_decisions
            if (turn.proactive_lifecycle_outcome_decision or {}).get("decision")
            == "lifecycle_dispatch_rescheduled"
        ]
        proactive_lifecycle_outcome_hold_turns = [
            turn
            for turn in proactive_lifecycle_outcome_decisions
            if (turn.proactive_lifecycle_outcome_decision or {}).get("decision")
            == "lifecycle_dispatch_held"
        ]
        proactive_lifecycle_outcome_retire_turns = [
            turn
            for turn in proactive_lifecycle_outcome_decisions
            if (turn.proactive_lifecycle_outcome_decision or {}).get("decision")
            == "lifecycle_dispatch_retired"
        ]
        proactive_lifecycle_resolution_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_resolution_decision is not None
        ]
        proactive_lifecycle_resolution_changed_turns = [
            turn
            for turn in proactive_lifecycle_resolution_decisions
            if bool((turn.proactive_lifecycle_resolution_decision or {}).get("changed"))
        ]
        proactive_lifecycle_resolution_continue_turns = [
            turn
            for turn in proactive_lifecycle_resolution_decisions
            if (turn.proactive_lifecycle_resolution_decision or {}).get("decision")
            == "continue_lifecycle_resolution"
        ]
        proactive_lifecycle_resolution_buffer_turns = [
            turn
            for turn in proactive_lifecycle_resolution_decisions
            if (turn.proactive_lifecycle_resolution_decision or {}).get("decision")
            == "buffer_lifecycle_resolution"
        ]
        proactive_lifecycle_resolution_hold_turns = [
            turn
            for turn in proactive_lifecycle_resolution_decisions
            if (turn.proactive_lifecycle_resolution_decision or {}).get("decision")
            == "hold_lifecycle_resolution"
        ]
        proactive_lifecycle_resolution_retire_turns = [
            turn
            for turn in proactive_lifecycle_resolution_decisions
            if (turn.proactive_lifecycle_resolution_decision or {}).get("decision")
            == "retire_lifecycle_resolution"
        ]
        proactive_lifecycle_activation_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_activation_decision is not None
        ]
        proactive_lifecycle_activation_changed_turns = [
            turn
            for turn in proactive_lifecycle_activation_decisions
            if bool((turn.proactive_lifecycle_activation_decision or {}).get("changed"))
        ]
        proactive_lifecycle_activation_activate_turns = [
            turn
            for turn in proactive_lifecycle_activation_decisions
            if (turn.proactive_lifecycle_activation_decision or {}).get("decision")
            == "activate_next_lifecycle_stage"
        ]
        proactive_lifecycle_activation_buffer_turns = [
            turn
            for turn in proactive_lifecycle_activation_decisions
            if (turn.proactive_lifecycle_activation_decision or {}).get("decision")
            == "buffer_current_lifecycle_stage"
        ]
        proactive_lifecycle_activation_hold_turns = [
            turn
            for turn in proactive_lifecycle_activation_decisions
            if (turn.proactive_lifecycle_activation_decision or {}).get("decision")
            == "hold_current_lifecycle_stage"
        ]
        proactive_lifecycle_activation_retire_turns = [
            turn
            for turn in proactive_lifecycle_activation_decisions
            if (turn.proactive_lifecycle_activation_decision or {}).get("decision")
            == "retire_lifecycle_line"
        ]
        proactive_lifecycle_settlement_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_settlement_decision is not None
        ]
        proactive_lifecycle_settlement_changed_turns = [
            turn
            for turn in proactive_lifecycle_settlement_decisions
            if bool((turn.proactive_lifecycle_settlement_decision or {}).get("changed"))
        ]
        proactive_lifecycle_settlement_keep_turns = [
            turn
            for turn in proactive_lifecycle_settlement_decisions
            if (turn.proactive_lifecycle_settlement_decision or {}).get("decision")
            == "keep_lifecycle_active"
        ]
        proactive_lifecycle_settlement_buffer_turns = [
            turn
            for turn in proactive_lifecycle_settlement_decisions
            if (turn.proactive_lifecycle_settlement_decision or {}).get("decision")
            == "buffer_lifecycle_settlement"
        ]
        proactive_lifecycle_settlement_hold_turns = [
            turn
            for turn in proactive_lifecycle_settlement_decisions
            if (turn.proactive_lifecycle_settlement_decision or {}).get("decision")
            == "hold_lifecycle_settlement"
        ]
        proactive_lifecycle_settlement_close_turns = [
            turn
            for turn in proactive_lifecycle_settlement_decisions
            if (turn.proactive_lifecycle_settlement_decision or {}).get("decision")
            == "close_lifecycle_settlement"
        ]
        proactive_lifecycle_settlement_retire_turns = [
            turn
            for turn in proactive_lifecycle_settlement_decisions
            if (turn.proactive_lifecycle_settlement_decision or {}).get("decision")
            == "retire_lifecycle_settlement"
        ]
        proactive_lifecycle_closure_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_closure_decision is not None
        ]
        proactive_lifecycle_closure_changed_turns = [
            turn
            for turn in proactive_lifecycle_closure_decisions
            if bool((turn.proactive_lifecycle_closure_decision or {}).get("changed"))
        ]
        proactive_lifecycle_closure_open_turns = [
            turn
            for turn in proactive_lifecycle_closure_decisions
            if (turn.proactive_lifecycle_closure_decision or {}).get("decision")
            == "keep_open_lifecycle_closure"
        ]
        proactive_lifecycle_closure_buffer_turns = [
            turn
            for turn in proactive_lifecycle_closure_decisions
            if (turn.proactive_lifecycle_closure_decision or {}).get("decision")
            == "buffer_lifecycle_closure"
        ]
        proactive_lifecycle_closure_pause_turns = [
            turn
            for turn in proactive_lifecycle_closure_decisions
            if (turn.proactive_lifecycle_closure_decision or {}).get("decision")
            == "pause_lifecycle_closure"
        ]
        proactive_lifecycle_closure_close_turns = [
            turn
            for turn in proactive_lifecycle_closure_decisions
            if (turn.proactive_lifecycle_closure_decision or {}).get("decision")
            == "close_loop_lifecycle_closure"
        ]
        proactive_lifecycle_closure_retire_turns = [
            turn
            for turn in proactive_lifecycle_closure_decisions
            if (turn.proactive_lifecycle_closure_decision or {}).get("decision")
            == "retire_lifecycle_closure"
        ]
        proactive_lifecycle_availability_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_availability_decision is not None
        ]
        proactive_lifecycle_availability_changed_turns = [
            turn
            for turn in proactive_lifecycle_availability_decisions
            if bool(
                (turn.proactive_lifecycle_availability_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_availability_open_turns = [
            turn
            for turn in proactive_lifecycle_availability_decisions
            if (turn.proactive_lifecycle_availability_decision or {}).get("decision")
            == "keep_lifecycle_available"
        ]
        proactive_lifecycle_availability_buffer_turns = [
            turn
            for turn in proactive_lifecycle_availability_decisions
            if (turn.proactive_lifecycle_availability_decision or {}).get("decision")
            == "buffer_lifecycle_availability"
        ]
        proactive_lifecycle_availability_pause_turns = [
            turn
            for turn in proactive_lifecycle_availability_decisions
            if (turn.proactive_lifecycle_availability_decision or {}).get("decision")
            == "pause_lifecycle_availability"
        ]
        proactive_lifecycle_availability_close_turns = [
            turn
            for turn in proactive_lifecycle_availability_decisions
            if (turn.proactive_lifecycle_availability_decision or {}).get("decision")
            == "close_loop_lifecycle_availability"
        ]
        proactive_lifecycle_availability_retire_turns = [
            turn
            for turn in proactive_lifecycle_availability_decisions
            if (turn.proactive_lifecycle_availability_decision or {}).get("decision")
            == "retire_lifecycle_availability"
        ]
        proactive_lifecycle_retention_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_retention_decision is not None
        ]
        proactive_lifecycle_retention_changed_turns = [
            turn
            for turn in proactive_lifecycle_retention_decisions
            if bool((turn.proactive_lifecycle_retention_decision or {}).get("changed"))
        ]
        proactive_lifecycle_retention_retain_turns = [
            turn
            for turn in proactive_lifecycle_retention_decisions
            if (turn.proactive_lifecycle_retention_decision or {}).get("decision")
            == "retain_lifecycle_retention"
        ]
        proactive_lifecycle_retention_buffer_turns = [
            turn
            for turn in proactive_lifecycle_retention_decisions
            if (turn.proactive_lifecycle_retention_decision or {}).get("decision")
            == "buffer_lifecycle_retention"
        ]
        proactive_lifecycle_retention_pause_turns = [
            turn
            for turn in proactive_lifecycle_retention_decisions
            if (turn.proactive_lifecycle_retention_decision or {}).get("decision")
            == "pause_lifecycle_retention"
        ]
        proactive_lifecycle_retention_archive_turns = [
            turn
            for turn in proactive_lifecycle_retention_decisions
            if (turn.proactive_lifecycle_retention_decision or {}).get("decision")
            == "archive_lifecycle_retention"
        ]
        proactive_lifecycle_retention_retire_turns = [
            turn
            for turn in proactive_lifecycle_retention_decisions
            if (turn.proactive_lifecycle_retention_decision or {}).get("decision")
            == "retire_lifecycle_retention"
        ]
        proactive_lifecycle_eligibility_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_eligibility_decision is not None
        ]
        proactive_lifecycle_eligibility_changed_turns = [
            turn
            for turn in proactive_lifecycle_eligibility_decisions
            if bool((turn.proactive_lifecycle_eligibility_decision or {}).get("changed"))
        ]
        proactive_lifecycle_eligibility_keep_turns = [
            turn
            for turn in proactive_lifecycle_eligibility_decisions
            if (turn.proactive_lifecycle_eligibility_decision or {}).get("decision")
            == "keep_lifecycle_eligible"
        ]
        proactive_lifecycle_eligibility_buffer_turns = [
            turn
            for turn in proactive_lifecycle_eligibility_decisions
            if (turn.proactive_lifecycle_eligibility_decision or {}).get("decision")
            == "buffer_lifecycle_eligibility"
        ]
        proactive_lifecycle_eligibility_pause_turns = [
            turn
            for turn in proactive_lifecycle_eligibility_decisions
            if (turn.proactive_lifecycle_eligibility_decision or {}).get("decision")
            == "pause_lifecycle_eligibility"
        ]
        proactive_lifecycle_eligibility_archive_turns = [
            turn
            for turn in proactive_lifecycle_eligibility_decisions
            if (turn.proactive_lifecycle_eligibility_decision or {}).get("decision")
            == "archive_lifecycle_eligibility"
        ]
        proactive_lifecycle_eligibility_retire_turns = [
            turn
            for turn in proactive_lifecycle_eligibility_decisions
            if (turn.proactive_lifecycle_eligibility_decision or {}).get("decision")
            == "retire_lifecycle_eligibility"
        ]
        proactive_lifecycle_candidate_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_candidate_decision is not None
        ]
        proactive_lifecycle_candidate_changed_turns = [
            turn
            for turn in proactive_lifecycle_candidate_decisions
            if bool((turn.proactive_lifecycle_candidate_decision or {}).get("changed"))
        ]
        proactive_lifecycle_candidate_keep_turns = [
            turn
            for turn in proactive_lifecycle_candidate_decisions
            if (turn.proactive_lifecycle_candidate_decision or {}).get("decision")
            == "keep_lifecycle_candidate"
        ]
        proactive_lifecycle_candidate_buffer_turns = [
            turn
            for turn in proactive_lifecycle_candidate_decisions
            if (turn.proactive_lifecycle_candidate_decision or {}).get("decision")
            == "buffer_lifecycle_candidate"
        ]
        proactive_lifecycle_candidate_pause_turns = [
            turn
            for turn in proactive_lifecycle_candidate_decisions
            if (turn.proactive_lifecycle_candidate_decision or {}).get("decision")
            == "pause_lifecycle_candidate"
        ]
        proactive_lifecycle_candidate_archive_turns = [
            turn
            for turn in proactive_lifecycle_candidate_decisions
            if (turn.proactive_lifecycle_candidate_decision or {}).get("decision")
            == "archive_lifecycle_candidate"
        ]
        proactive_lifecycle_candidate_retire_turns = [
            turn
            for turn in proactive_lifecycle_candidate_decisions
            if (turn.proactive_lifecycle_candidate_decision or {}).get("decision")
            == "retire_lifecycle_candidate"
        ]
        proactive_lifecycle_selectability_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_selectability_decision is not None
        ]
        proactive_lifecycle_selectability_changed_turns = [
            turn
            for turn in proactive_lifecycle_selectability_decisions
            if bool(
                (turn.proactive_lifecycle_selectability_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_selectability_keep_turns = [
            turn
            for turn in proactive_lifecycle_selectability_decisions
            if (turn.proactive_lifecycle_selectability_decision or {}).get("decision")
            == "keep_lifecycle_selectable"
        ]
        proactive_lifecycle_selectability_buffer_turns = [
            turn
            for turn in proactive_lifecycle_selectability_decisions
            if (turn.proactive_lifecycle_selectability_decision or {}).get("decision")
            == "buffer_lifecycle_selectability"
        ]
        proactive_lifecycle_selectability_pause_turns = [
            turn
            for turn in proactive_lifecycle_selectability_decisions
            if (turn.proactive_lifecycle_selectability_decision or {}).get("decision")
            == "pause_lifecycle_selectability"
        ]
        proactive_lifecycle_selectability_archive_turns = [
            turn
            for turn in proactive_lifecycle_selectability_decisions
            if (turn.proactive_lifecycle_selectability_decision or {}).get("decision")
            == "archive_lifecycle_selectability"
        ]
        proactive_lifecycle_selectability_retire_turns = [
            turn
            for turn in proactive_lifecycle_selectability_decisions
            if (turn.proactive_lifecycle_selectability_decision or {}).get("decision")
            == "retire_lifecycle_selectability"
        ]
        proactive_lifecycle_reentry_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_reentry_decision is not None
        ]
        proactive_lifecycle_reentry_changed_turns = [
            turn
            for turn in proactive_lifecycle_reentry_decisions
            if bool((turn.proactive_lifecycle_reentry_decision or {}).get("changed"))
        ]
        proactive_lifecycle_reentry_keep_turns = [
            turn
            for turn in proactive_lifecycle_reentry_decisions
            if (turn.proactive_lifecycle_reentry_decision or {}).get("decision")
            == "keep_lifecycle_reentry"
        ]
        proactive_lifecycle_reentry_buffer_turns = [
            turn
            for turn in proactive_lifecycle_reentry_decisions
            if (turn.proactive_lifecycle_reentry_decision or {}).get("decision")
            == "buffer_lifecycle_reentry"
        ]
        proactive_lifecycle_reentry_pause_turns = [
            turn
            for turn in proactive_lifecycle_reentry_decisions
            if (turn.proactive_lifecycle_reentry_decision or {}).get("decision")
            == "pause_lifecycle_reentry"
        ]
        proactive_lifecycle_reentry_archive_turns = [
            turn
            for turn in proactive_lifecycle_reentry_decisions
            if (turn.proactive_lifecycle_reentry_decision or {}).get("decision")
            == "archive_lifecycle_reentry"
        ]
        proactive_lifecycle_reentry_retire_turns = [
            turn
            for turn in proactive_lifecycle_reentry_decisions
            if (turn.proactive_lifecycle_reentry_decision or {}).get("decision")
            == "retire_lifecycle_reentry"
        ]
        proactive_lifecycle_reactivation_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_reactivation_decision is not None
        ]
        proactive_lifecycle_reactivation_changed_turns = [
            turn
            for turn in proactive_lifecycle_reactivation_decisions
            if bool(
                (turn.proactive_lifecycle_reactivation_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_reactivation_keep_turns = [
            turn
            for turn in proactive_lifecycle_reactivation_decisions
            if (turn.proactive_lifecycle_reactivation_decision or {}).get("decision")
            == "keep_lifecycle_reactivation"
        ]
        proactive_lifecycle_reactivation_buffer_turns = [
            turn
            for turn in proactive_lifecycle_reactivation_decisions
            if (turn.proactive_lifecycle_reactivation_decision or {}).get("decision")
            == "buffer_lifecycle_reactivation"
        ]
        proactive_lifecycle_reactivation_pause_turns = [
            turn
            for turn in proactive_lifecycle_reactivation_decisions
            if (turn.proactive_lifecycle_reactivation_decision or {}).get("decision")
            == "pause_lifecycle_reactivation"
        ]
        proactive_lifecycle_reactivation_archive_turns = [
            turn
            for turn in proactive_lifecycle_reactivation_decisions
            if (turn.proactive_lifecycle_reactivation_decision or {}).get("decision")
            == "archive_lifecycle_reactivation"
        ]
        proactive_lifecycle_reactivation_retire_turns = [
            turn
            for turn in proactive_lifecycle_reactivation_decisions
            if (turn.proactive_lifecycle_reactivation_decision or {}).get("decision")
            == "retire_lifecycle_reactivation"
        ]
        proactive_lifecycle_resumption_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_resumption_decision is not None
        ]
        proactive_lifecycle_resumption_changed_turns = [
            turn
            for turn in proactive_lifecycle_resumption_decisions
            if bool(
                (turn.proactive_lifecycle_resumption_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_resumption_keep_turns = [
            turn
            for turn in proactive_lifecycle_resumption_decisions
            if (turn.proactive_lifecycle_resumption_decision or {}).get("decision")
            == "keep_lifecycle_resumption"
        ]
        proactive_lifecycle_resumption_buffer_turns = [
            turn
            for turn in proactive_lifecycle_resumption_decisions
            if (turn.proactive_lifecycle_resumption_decision or {}).get("decision")
            == "buffer_lifecycle_resumption"
        ]
        proactive_lifecycle_resumption_pause_turns = [
            turn
            for turn in proactive_lifecycle_resumption_decisions
            if (turn.proactive_lifecycle_resumption_decision or {}).get("decision")
            == "pause_lifecycle_resumption"
        ]
        proactive_lifecycle_resumption_archive_turns = [
            turn
            for turn in proactive_lifecycle_resumption_decisions
            if (turn.proactive_lifecycle_resumption_decision or {}).get("decision")
            == "archive_lifecycle_resumption"
        ]
        proactive_lifecycle_resumption_retire_turns = [
            turn
            for turn in proactive_lifecycle_resumption_decisions
            if (turn.proactive_lifecycle_resumption_decision or {}).get("decision")
            == "retire_lifecycle_resumption"
        ]
        proactive_lifecycle_readiness_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_readiness_decision is not None
        ]
        proactive_lifecycle_readiness_changed_turns = [
            turn
            for turn in proactive_lifecycle_readiness_decisions
            if bool((turn.proactive_lifecycle_readiness_decision or {}).get("changed"))
        ]
        proactive_lifecycle_readiness_keep_turns = [
            turn
            for turn in proactive_lifecycle_readiness_decisions
            if (turn.proactive_lifecycle_readiness_decision or {}).get("decision")
            == "keep_lifecycle_readiness"
        ]
        proactive_lifecycle_readiness_buffer_turns = [
            turn
            for turn in proactive_lifecycle_readiness_decisions
            if (turn.proactive_lifecycle_readiness_decision or {}).get("decision")
            == "buffer_lifecycle_readiness"
        ]
        proactive_lifecycle_readiness_pause_turns = [
            turn
            for turn in proactive_lifecycle_readiness_decisions
            if (turn.proactive_lifecycle_readiness_decision or {}).get("decision")
            == "pause_lifecycle_readiness"
        ]
        proactive_lifecycle_readiness_archive_turns = [
            turn
            for turn in proactive_lifecycle_readiness_decisions
            if (turn.proactive_lifecycle_readiness_decision or {}).get("decision")
            == "archive_lifecycle_readiness"
        ]
        proactive_lifecycle_readiness_retire_turns = [
            turn
            for turn in proactive_lifecycle_readiness_decisions
            if (turn.proactive_lifecycle_readiness_decision or {}).get("decision")
            == "retire_lifecycle_readiness"
        ]
        proactive_lifecycle_arming_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_arming_decision is not None
        ]
        proactive_lifecycle_arming_changed_turns = [
            turn
            for turn in proactive_lifecycle_arming_decisions
            if bool((turn.proactive_lifecycle_arming_decision or {}).get("changed"))
        ]
        proactive_lifecycle_arming_keep_turns = [
            turn
            for turn in proactive_lifecycle_arming_decisions
            if (turn.proactive_lifecycle_arming_decision or {}).get("decision")
            == "keep_lifecycle_arming"
        ]
        proactive_lifecycle_arming_buffer_turns = [
            turn
            for turn in proactive_lifecycle_arming_decisions
            if (turn.proactive_lifecycle_arming_decision or {}).get("decision")
            == "buffer_lifecycle_arming"
        ]
        proactive_lifecycle_arming_pause_turns = [
            turn
            for turn in proactive_lifecycle_arming_decisions
            if (turn.proactive_lifecycle_arming_decision or {}).get("decision")
            == "pause_lifecycle_arming"
        ]
        proactive_lifecycle_arming_archive_turns = [
            turn
            for turn in proactive_lifecycle_arming_decisions
            if (turn.proactive_lifecycle_arming_decision or {}).get("decision")
            == "archive_lifecycle_arming"
        ]
        proactive_lifecycle_arming_retire_turns = [
            turn
            for turn in proactive_lifecycle_arming_decisions
            if (turn.proactive_lifecycle_arming_decision or {}).get("decision")
            == "retire_lifecycle_arming"
        ]
        proactive_lifecycle_trigger_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_trigger_decision is not None
        ]
        proactive_lifecycle_trigger_changed_turns = [
            turn
            for turn in proactive_lifecycle_trigger_decisions
            if bool((turn.proactive_lifecycle_trigger_decision or {}).get("changed"))
        ]
        proactive_lifecycle_trigger_keep_turns = [
            turn
            for turn in proactive_lifecycle_trigger_decisions
            if (turn.proactive_lifecycle_trigger_decision or {}).get("decision")
            == "keep_lifecycle_trigger"
        ]
        proactive_lifecycle_trigger_buffer_turns = [
            turn
            for turn in proactive_lifecycle_trigger_decisions
            if (turn.proactive_lifecycle_trigger_decision or {}).get("decision")
            == "buffer_lifecycle_trigger"
        ]
        proactive_lifecycle_trigger_pause_turns = [
            turn
            for turn in proactive_lifecycle_trigger_decisions
            if (turn.proactive_lifecycle_trigger_decision or {}).get("decision")
            == "pause_lifecycle_trigger"
        ]
        proactive_lifecycle_trigger_archive_turns = [
            turn
            for turn in proactive_lifecycle_trigger_decisions
            if (turn.proactive_lifecycle_trigger_decision or {}).get("decision")
            == "archive_lifecycle_trigger"
        ]
        proactive_lifecycle_trigger_retire_turns = [
            turn
            for turn in proactive_lifecycle_trigger_decisions
            if (turn.proactive_lifecycle_trigger_decision or {}).get("decision")
            == "retire_lifecycle_trigger"
        ]
        proactive_lifecycle_launch_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_launch_decision is not None
        ]
        proactive_lifecycle_launch_changed_turns = [
            turn
            for turn in proactive_lifecycle_launch_decisions
            if bool((turn.proactive_lifecycle_launch_decision or {}).get("changed"))
        ]
        proactive_lifecycle_launch_keep_turns = [
            turn
            for turn in proactive_lifecycle_launch_decisions
            if (turn.proactive_lifecycle_launch_decision or {}).get("decision")
            == "keep_lifecycle_launch"
        ]
        proactive_lifecycle_launch_buffer_turns = [
            turn
            for turn in proactive_lifecycle_launch_decisions
            if (turn.proactive_lifecycle_launch_decision or {}).get("decision")
            == "buffer_lifecycle_launch"
        ]
        proactive_lifecycle_launch_pause_turns = [
            turn
            for turn in proactive_lifecycle_launch_decisions
            if (turn.proactive_lifecycle_launch_decision or {}).get("decision")
            == "pause_lifecycle_launch"
        ]
        proactive_lifecycle_launch_archive_turns = [
            turn
            for turn in proactive_lifecycle_launch_decisions
            if (turn.proactive_lifecycle_launch_decision or {}).get("decision")
            == "archive_lifecycle_launch"
        ]
        proactive_lifecycle_launch_retire_turns = [
            turn
            for turn in proactive_lifecycle_launch_decisions
            if (turn.proactive_lifecycle_launch_decision or {}).get("decision")
            == "retire_lifecycle_launch"
        ]
        proactive_lifecycle_handoff_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_handoff_decision is not None
        ]
        proactive_lifecycle_handoff_changed_turns = [
            turn
            for turn in proactive_lifecycle_handoff_decisions
            if bool((turn.proactive_lifecycle_handoff_decision or {}).get("changed"))
        ]
        proactive_lifecycle_handoff_keep_turns = [
            turn
            for turn in proactive_lifecycle_handoff_decisions
            if (turn.proactive_lifecycle_handoff_decision or {}).get("decision")
            == "keep_lifecycle_handoff"
        ]
        proactive_lifecycle_handoff_buffer_turns = [
            turn
            for turn in proactive_lifecycle_handoff_decisions
            if (turn.proactive_lifecycle_handoff_decision or {}).get("decision")
            == "buffer_lifecycle_handoff"
        ]
        proactive_lifecycle_handoff_pause_turns = [
            turn
            for turn in proactive_lifecycle_handoff_decisions
            if (turn.proactive_lifecycle_handoff_decision or {}).get("decision")
            == "pause_lifecycle_handoff"
        ]
        proactive_lifecycle_handoff_archive_turns = [
            turn
            for turn in proactive_lifecycle_handoff_decisions
            if (turn.proactive_lifecycle_handoff_decision or {}).get("decision")
            == "archive_lifecycle_handoff"
        ]
        proactive_lifecycle_handoff_retire_turns = [
            turn
            for turn in proactive_lifecycle_handoff_decisions
            if (turn.proactive_lifecycle_handoff_decision or {}).get("decision")
            == "retire_lifecycle_handoff"
        ]
        proactive_lifecycle_continuation_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_continuation_decision is not None
        ]
        proactive_lifecycle_continuation_changed_turns = [
            turn
            for turn in proactive_lifecycle_continuation_decisions
            if bool(
                (turn.proactive_lifecycle_continuation_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_continuation_keep_turns = [
            turn
            for turn in proactive_lifecycle_continuation_decisions
            if (turn.proactive_lifecycle_continuation_decision or {}).get("decision")
            == "keep_lifecycle_continuation"
        ]
        proactive_lifecycle_continuation_buffer_turns = [
            turn
            for turn in proactive_lifecycle_continuation_decisions
            if (turn.proactive_lifecycle_continuation_decision or {}).get("decision")
            == "buffer_lifecycle_continuation"
        ]
        proactive_lifecycle_continuation_pause_turns = [
            turn
            for turn in proactive_lifecycle_continuation_decisions
            if (turn.proactive_lifecycle_continuation_decision or {}).get("decision")
            == "pause_lifecycle_continuation"
        ]
        proactive_lifecycle_continuation_archive_turns = [
            turn
            for turn in proactive_lifecycle_continuation_decisions
            if (turn.proactive_lifecycle_continuation_decision or {}).get("decision")
            == "archive_lifecycle_continuation"
        ]
        proactive_lifecycle_continuation_retire_turns = [
            turn
            for turn in proactive_lifecycle_continuation_decisions
            if (turn.proactive_lifecycle_continuation_decision or {}).get("decision")
            == "retire_lifecycle_continuation"
        ]
        proactive_lifecycle_sustainment_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_sustainment_decision is not None
        ]
        proactive_lifecycle_sustainment_changed_turns = [
            turn
            for turn in proactive_lifecycle_sustainment_decisions
            if bool(
                (turn.proactive_lifecycle_sustainment_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_sustainment_sustain_turns = [
            turn
            for turn in proactive_lifecycle_sustainment_decisions
            if (turn.proactive_lifecycle_sustainment_decision or {}).get("decision")
            == "sustain_lifecycle_sustainment"
        ]
        proactive_lifecycle_sustainment_buffer_turns = [
            turn
            for turn in proactive_lifecycle_sustainment_decisions
            if (turn.proactive_lifecycle_sustainment_decision or {}).get("decision")
            == "buffer_lifecycle_sustainment"
        ]
        proactive_lifecycle_sustainment_pause_turns = [
            turn
            for turn in proactive_lifecycle_sustainment_decisions
            if (turn.proactive_lifecycle_sustainment_decision or {}).get("decision")
            == "pause_lifecycle_sustainment"
        ]
        proactive_lifecycle_sustainment_archive_turns = [
            turn
            for turn in proactive_lifecycle_sustainment_decisions
            if (turn.proactive_lifecycle_sustainment_decision or {}).get("decision")
            == "archive_lifecycle_sustainment"
        ]
        proactive_lifecycle_sustainment_retire_turns = [
            turn
            for turn in proactive_lifecycle_sustainment_decisions
            if (turn.proactive_lifecycle_sustainment_decision or {}).get("decision")
            == "retire_lifecycle_sustainment"
        ]
        proactive_lifecycle_stewardship_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_stewardship_decision is not None
        ]
        proactive_lifecycle_stewardship_changed_turns = [
            turn
            for turn in proactive_lifecycle_stewardship_decisions
            if bool(
                (turn.proactive_lifecycle_stewardship_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_stewardship_steward_turns = [
            turn
            for turn in proactive_lifecycle_stewardship_decisions
            if (turn.proactive_lifecycle_stewardship_decision or {}).get("decision")
            == "steward_lifecycle_stewardship"
        ]
        proactive_lifecycle_stewardship_buffer_turns = [
            turn
            for turn in proactive_lifecycle_stewardship_decisions
            if (turn.proactive_lifecycle_stewardship_decision or {}).get("decision")
            == "buffer_lifecycle_stewardship"
        ]
        proactive_lifecycle_stewardship_pause_turns = [
            turn
            for turn in proactive_lifecycle_stewardship_decisions
            if (turn.proactive_lifecycle_stewardship_decision or {}).get("decision")
            == "pause_lifecycle_stewardship"
        ]
        proactive_lifecycle_stewardship_archive_turns = [
            turn
            for turn in proactive_lifecycle_stewardship_decisions
            if (turn.proactive_lifecycle_stewardship_decision or {}).get("decision")
            == "archive_lifecycle_stewardship"
        ]
        proactive_lifecycle_stewardship_retire_turns = [
            turn
            for turn in proactive_lifecycle_stewardship_decisions
            if (turn.proactive_lifecycle_stewardship_decision or {}).get("decision")
            == "retire_lifecycle_stewardship"
        ]
        proactive_lifecycle_guardianship_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_guardianship_decision is not None
        ]
        proactive_lifecycle_guardianship_changed_turns = [
            turn
            for turn in proactive_lifecycle_guardianship_decisions
            if bool(
                (turn.proactive_lifecycle_guardianship_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_guardianship_guard_turns = [
            turn
            for turn in proactive_lifecycle_guardianship_decisions
            if (turn.proactive_lifecycle_guardianship_decision or {}).get("decision")
            == "guard_lifecycle_guardianship"
        ]
        proactive_lifecycle_guardianship_buffer_turns = [
            turn
            for turn in proactive_lifecycle_guardianship_decisions
            if (turn.proactive_lifecycle_guardianship_decision or {}).get("decision")
            == "buffer_lifecycle_guardianship"
        ]
        proactive_lifecycle_guardianship_pause_turns = [
            turn
            for turn in proactive_lifecycle_guardianship_decisions
            if (turn.proactive_lifecycle_guardianship_decision or {}).get("decision")
            == "pause_lifecycle_guardianship"
        ]
        proactive_lifecycle_guardianship_archive_turns = [
            turn
            for turn in proactive_lifecycle_guardianship_decisions
            if (turn.proactive_lifecycle_guardianship_decision or {}).get("decision")
            == "archive_lifecycle_guardianship"
        ]
        proactive_lifecycle_guardianship_retire_turns = [
            turn
            for turn in proactive_lifecycle_guardianship_decisions
            if (turn.proactive_lifecycle_guardianship_decision or {}).get("decision")
            == "retire_lifecycle_guardianship"
        ]
        proactive_lifecycle_oversight_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_oversight_decision is not None
        ]
        proactive_lifecycle_oversight_changed_turns = [
            turn
            for turn in proactive_lifecycle_oversight_decisions
            if bool((turn.proactive_lifecycle_oversight_decision or {}).get("changed"))
        ]
        proactive_lifecycle_oversight_oversee_turns = [
            turn
            for turn in proactive_lifecycle_oversight_decisions
            if (turn.proactive_lifecycle_oversight_decision or {}).get("decision")
            == "oversee_lifecycle_oversight"
        ]
        proactive_lifecycle_oversight_buffer_turns = [
            turn
            for turn in proactive_lifecycle_oversight_decisions
            if (turn.proactive_lifecycle_oversight_decision or {}).get("decision")
            == "buffer_lifecycle_oversight"
        ]
        proactive_lifecycle_oversight_pause_turns = [
            turn
            for turn in proactive_lifecycle_oversight_decisions
            if (turn.proactive_lifecycle_oversight_decision or {}).get("decision")
            == "pause_lifecycle_oversight"
        ]
        proactive_lifecycle_oversight_archive_turns = [
            turn
            for turn in proactive_lifecycle_oversight_decisions
            if (turn.proactive_lifecycle_oversight_decision or {}).get("decision")
            == "archive_lifecycle_oversight"
        ]
        proactive_lifecycle_oversight_retire_turns = [
            turn
            for turn in proactive_lifecycle_oversight_decisions
            if (turn.proactive_lifecycle_oversight_decision or {}).get("decision")
            == "retire_lifecycle_oversight"
        ]
        proactive_lifecycle_assurance_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_assurance_decision is not None
        ]
        proactive_lifecycle_assurance_changed_turns = [
            turn
            for turn in proactive_lifecycle_assurance_decisions
            if bool((turn.proactive_lifecycle_assurance_decision or {}).get("changed"))
        ]
        proactive_lifecycle_assurance_assure_turns = [
            turn
            for turn in proactive_lifecycle_assurance_decisions
            if (turn.proactive_lifecycle_assurance_decision or {}).get("decision")
            == "assure_lifecycle_assurance"
        ]
        proactive_lifecycle_assurance_buffer_turns = [
            turn
            for turn in proactive_lifecycle_assurance_decisions
            if (turn.proactive_lifecycle_assurance_decision or {}).get("decision")
            == "buffer_lifecycle_assurance"
        ]
        proactive_lifecycle_assurance_pause_turns = [
            turn
            for turn in proactive_lifecycle_assurance_decisions
            if (turn.proactive_lifecycle_assurance_decision or {}).get("decision")
            == "pause_lifecycle_assurance"
        ]
        proactive_lifecycle_assurance_archive_turns = [
            turn
            for turn in proactive_lifecycle_assurance_decisions
            if (turn.proactive_lifecycle_assurance_decision or {}).get("decision")
            == "archive_lifecycle_assurance"
        ]
        proactive_lifecycle_assurance_retire_turns = [
            turn
            for turn in proactive_lifecycle_assurance_decisions
            if (turn.proactive_lifecycle_assurance_decision or {}).get("decision")
            == "retire_lifecycle_assurance"
        ]
        proactive_lifecycle_attestation_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_attestation_decision is not None
        ]
        proactive_lifecycle_attestation_changed_turns = [
            turn
            for turn in proactive_lifecycle_attestation_decisions
            if bool((turn.proactive_lifecycle_attestation_decision or {}).get("changed"))
        ]
        proactive_lifecycle_attestation_attest_turns = [
            turn
            for turn in proactive_lifecycle_attestation_decisions
            if (turn.proactive_lifecycle_attestation_decision or {}).get("decision")
            == "attest_lifecycle_attestation"
        ]
        proactive_lifecycle_attestation_buffer_turns = [
            turn
            for turn in proactive_lifecycle_attestation_decisions
            if (turn.proactive_lifecycle_attestation_decision or {}).get("decision")
            == "buffer_lifecycle_attestation"
        ]
        proactive_lifecycle_attestation_pause_turns = [
            turn
            for turn in proactive_lifecycle_attestation_decisions
            if (turn.proactive_lifecycle_attestation_decision or {}).get("decision")
            == "pause_lifecycle_attestation"
        ]
        proactive_lifecycle_attestation_archive_turns = [
            turn
            for turn in proactive_lifecycle_attestation_decisions
            if (turn.proactive_lifecycle_attestation_decision or {}).get("decision")
            == "archive_lifecycle_attestation"
        ]
        proactive_lifecycle_attestation_retire_turns = [
            turn
            for turn in proactive_lifecycle_attestation_decisions
            if (turn.proactive_lifecycle_attestation_decision or {}).get("decision")
            == "retire_lifecycle_attestation"
        ]
        proactive_lifecycle_verification_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_verification_decision is not None
        ]
        proactive_lifecycle_verification_changed_turns = [
            turn
            for turn in proactive_lifecycle_verification_decisions
            if bool((turn.proactive_lifecycle_verification_decision or {}).get("changed"))
        ]
        proactive_lifecycle_verification_verify_turns = [
            turn
            for turn in proactive_lifecycle_verification_decisions
            if (turn.proactive_lifecycle_verification_decision or {}).get("decision")
            == "verify_lifecycle_verification"
        ]
        proactive_lifecycle_verification_buffer_turns = [
            turn
            for turn in proactive_lifecycle_verification_decisions
            if (turn.proactive_lifecycle_verification_decision or {}).get("decision")
            == "buffer_lifecycle_verification"
        ]
        proactive_lifecycle_verification_pause_turns = [
            turn
            for turn in proactive_lifecycle_verification_decisions
            if (turn.proactive_lifecycle_verification_decision or {}).get("decision")
            == "pause_lifecycle_verification"
        ]
        proactive_lifecycle_verification_archive_turns = [
            turn
            for turn in proactive_lifecycle_verification_decisions
            if (turn.proactive_lifecycle_verification_decision or {}).get("decision")
            == "archive_lifecycle_verification"
        ]
        proactive_lifecycle_verification_retire_turns = [
            turn
            for turn in proactive_lifecycle_verification_decisions
            if (turn.proactive_lifecycle_verification_decision or {}).get("decision")
            == "retire_lifecycle_verification"
        ]
        proactive_lifecycle_certification_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_certification_decision is not None
        ]
        proactive_lifecycle_certification_changed_turns = [
            turn
            for turn in proactive_lifecycle_certification_decisions
            if bool((turn.proactive_lifecycle_certification_decision or {}).get("changed"))
        ]
        proactive_lifecycle_certification_certify_turns = [
            turn
            for turn in proactive_lifecycle_certification_decisions
            if (turn.proactive_lifecycle_certification_decision or {}).get("decision")
            == "certify_lifecycle_certification"
        ]
        proactive_lifecycle_certification_buffer_turns = [
            turn
            for turn in proactive_lifecycle_certification_decisions
            if (turn.proactive_lifecycle_certification_decision or {}).get("decision")
            == "buffer_lifecycle_certification"
        ]
        proactive_lifecycle_certification_pause_turns = [
            turn
            for turn in proactive_lifecycle_certification_decisions
            if (turn.proactive_lifecycle_certification_decision or {}).get("decision")
            == "pause_lifecycle_certification"
        ]
        proactive_lifecycle_certification_archive_turns = [
            turn
            for turn in proactive_lifecycle_certification_decisions
            if (turn.proactive_lifecycle_certification_decision or {}).get("decision")
            == "archive_lifecycle_certification"
        ]
        proactive_lifecycle_certification_retire_turns = [
            turn
            for turn in proactive_lifecycle_certification_decisions
            if (turn.proactive_lifecycle_certification_decision or {}).get("decision")
            == "retire_lifecycle_certification"
        ]
        proactive_lifecycle_confirmation_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_confirmation_decision is not None
        ]
        proactive_lifecycle_confirmation_changed_turns = [
            turn
            for turn in proactive_lifecycle_confirmation_decisions
            if bool((turn.proactive_lifecycle_confirmation_decision or {}).get("changed"))
        ]
        proactive_lifecycle_confirmation_confirm_turns = [
            turn
            for turn in proactive_lifecycle_confirmation_decisions
            if (turn.proactive_lifecycle_confirmation_decision or {}).get("decision")
            == "confirm_lifecycle_confirmation"
        ]
        proactive_lifecycle_confirmation_buffer_turns = [
            turn
            for turn in proactive_lifecycle_confirmation_decisions
            if (turn.proactive_lifecycle_confirmation_decision or {}).get("decision")
            == "buffer_lifecycle_confirmation"
        ]
        proactive_lifecycle_confirmation_pause_turns = [
            turn
            for turn in proactive_lifecycle_confirmation_decisions
            if (turn.proactive_lifecycle_confirmation_decision or {}).get("decision")
            == "pause_lifecycle_confirmation"
        ]
        proactive_lifecycle_confirmation_archive_turns = [
            turn
            for turn in proactive_lifecycle_confirmation_decisions
            if (turn.proactive_lifecycle_confirmation_decision or {}).get("decision")
            == "archive_lifecycle_confirmation"
        ]
        proactive_lifecycle_confirmation_retire_turns = [
            turn
            for turn in proactive_lifecycle_confirmation_decisions
            if (turn.proactive_lifecycle_confirmation_decision or {}).get("decision")
            == "retire_lifecycle_confirmation"
        ]
        proactive_lifecycle_ratification_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_ratification_decision is not None
        ]
        proactive_lifecycle_ratification_changed_turns = [
            turn
            for turn in proactive_lifecycle_ratification_decisions
            if bool((turn.proactive_lifecycle_ratification_decision or {}).get("changed"))
        ]
        proactive_lifecycle_ratification_ratify_turns = [
            turn
            for turn in proactive_lifecycle_ratification_decisions
            if (turn.proactive_lifecycle_ratification_decision or {}).get("decision")
            == "ratify_lifecycle_ratification"
        ]
        proactive_lifecycle_ratification_buffer_turns = [
            turn
            for turn in proactive_lifecycle_ratification_decisions
            if (turn.proactive_lifecycle_ratification_decision or {}).get("decision")
            == "buffer_lifecycle_ratification"
        ]
        proactive_lifecycle_ratification_pause_turns = [
            turn
            for turn in proactive_lifecycle_ratification_decisions
            if (turn.proactive_lifecycle_ratification_decision or {}).get("decision")
            == "pause_lifecycle_ratification"
        ]
        proactive_lifecycle_ratification_archive_turns = [
            turn
            for turn in proactive_lifecycle_ratification_decisions
            if (turn.proactive_lifecycle_ratification_decision or {}).get("decision")
            == "archive_lifecycle_ratification"
        ]
        proactive_lifecycle_ratification_retire_turns = [
            turn
            for turn in proactive_lifecycle_ratification_decisions
            if (turn.proactive_lifecycle_ratification_decision or {}).get("decision")
            == "retire_lifecycle_ratification"
        ]
        proactive_lifecycle_endorsement_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_endorsement_decision is not None
        ]
        proactive_lifecycle_endorsement_changed_turns = [
            turn
            for turn in proactive_lifecycle_endorsement_decisions
            if bool((turn.proactive_lifecycle_endorsement_decision or {}).get("changed"))
        ]
        proactive_lifecycle_endorsement_endorse_turns = [
            turn
            for turn in proactive_lifecycle_endorsement_decisions
            if (turn.proactive_lifecycle_endorsement_decision or {}).get("decision")
            == "endorse_lifecycle_endorsement"
        ]
        proactive_lifecycle_endorsement_buffer_turns = [
            turn
            for turn in proactive_lifecycle_endorsement_decisions
            if (turn.proactive_lifecycle_endorsement_decision or {}).get("decision")
            == "buffer_lifecycle_endorsement"
        ]
        proactive_lifecycle_endorsement_pause_turns = [
            turn
            for turn in proactive_lifecycle_endorsement_decisions
            if (turn.proactive_lifecycle_endorsement_decision or {}).get("decision")
            == "pause_lifecycle_endorsement"
        ]
        proactive_lifecycle_endorsement_archive_turns = [
            turn
            for turn in proactive_lifecycle_endorsement_decisions
            if (turn.proactive_lifecycle_endorsement_decision or {}).get("decision")
            == "archive_lifecycle_endorsement"
        ]
        proactive_lifecycle_endorsement_retire_turns = [
            turn
            for turn in proactive_lifecycle_endorsement_decisions
            if (turn.proactive_lifecycle_endorsement_decision or {}).get("decision")
            == "retire_lifecycle_endorsement"
        ]
        proactive_lifecycle_authorization_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_authorization_decision is not None
        ]
        proactive_lifecycle_authorization_changed_turns = [
            turn
            for turn in proactive_lifecycle_authorization_decisions
            if bool((turn.proactive_lifecycle_authorization_decision or {}).get("changed"))
        ]
        proactive_lifecycle_authorization_authorize_turns = [
            turn
            for turn in proactive_lifecycle_authorization_decisions
            if (turn.proactive_lifecycle_authorization_decision or {}).get("decision")
            == "authorize_lifecycle_authorization"
        ]
        proactive_lifecycle_authorization_buffer_turns = [
            turn
            for turn in proactive_lifecycle_authorization_decisions
            if (turn.proactive_lifecycle_authorization_decision or {}).get("decision")
            == "buffer_lifecycle_authorization"
        ]
        proactive_lifecycle_authorization_pause_turns = [
            turn
            for turn in proactive_lifecycle_authorization_decisions
            if (turn.proactive_lifecycle_authorization_decision or {}).get("decision")
            == "pause_lifecycle_authorization"
        ]
        proactive_lifecycle_authorization_archive_turns = [
            turn
            for turn in proactive_lifecycle_authorization_decisions
            if (turn.proactive_lifecycle_authorization_decision or {}).get("decision")
            == "archive_lifecycle_authorization"
        ]
        proactive_lifecycle_authorization_retire_turns = [
            turn
            for turn in proactive_lifecycle_authorization_decisions
            if (turn.proactive_lifecycle_authorization_decision or {}).get("decision")
            == "retire_lifecycle_authorization"
        ]
        proactive_lifecycle_enactment_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_enactment_decision is not None
        ]
        proactive_lifecycle_enactment_changed_turns = [
            turn
            for turn in proactive_lifecycle_enactment_decisions
            if bool((turn.proactive_lifecycle_enactment_decision or {}).get("changed"))
        ]
        proactive_lifecycle_enactment_enact_turns = [
            turn
            for turn in proactive_lifecycle_enactment_decisions
            if (turn.proactive_lifecycle_enactment_decision or {}).get("decision")
            == "enact_lifecycle_enactment"
        ]
        proactive_lifecycle_enactment_buffer_turns = [
            turn
            for turn in proactive_lifecycle_enactment_decisions
            if (turn.proactive_lifecycle_enactment_decision or {}).get("decision")
            == "buffer_lifecycle_enactment"
        ]
        proactive_lifecycle_enactment_pause_turns = [
            turn
            for turn in proactive_lifecycle_enactment_decisions
            if (turn.proactive_lifecycle_enactment_decision or {}).get("decision")
            == "pause_lifecycle_enactment"
        ]
        proactive_lifecycle_enactment_archive_turns = [
            turn
            for turn in proactive_lifecycle_enactment_decisions
            if (turn.proactive_lifecycle_enactment_decision or {}).get("decision")
            == "archive_lifecycle_enactment"
        ]
        proactive_lifecycle_enactment_retire_turns = [
            turn
            for turn in proactive_lifecycle_enactment_decisions
            if (turn.proactive_lifecycle_enactment_decision or {}).get("decision")
            == "retire_lifecycle_enactment"
        ]
        proactive_lifecycle_finality_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_finality_decision is not None
        ]
        proactive_lifecycle_finality_changed_turns = [
            turn
            for turn in proactive_lifecycle_finality_decisions
            if bool((turn.proactive_lifecycle_finality_decision or {}).get("changed"))
        ]
        proactive_lifecycle_finality_finalize_turns = [
            turn
            for turn in proactive_lifecycle_finality_decisions
            if (turn.proactive_lifecycle_finality_decision or {}).get("decision")
            == "finalize_lifecycle_finality"
        ]
        proactive_lifecycle_finality_buffer_turns = [
            turn
            for turn in proactive_lifecycle_finality_decisions
            if (turn.proactive_lifecycle_finality_decision or {}).get("decision")
            == "buffer_lifecycle_finality"
        ]
        proactive_lifecycle_finality_pause_turns = [
            turn
            for turn in proactive_lifecycle_finality_decisions
            if (turn.proactive_lifecycle_finality_decision or {}).get("decision")
            == "pause_lifecycle_finality"
        ]
        proactive_lifecycle_finality_archive_turns = [
            turn
            for turn in proactive_lifecycle_finality_decisions
            if (turn.proactive_lifecycle_finality_decision or {}).get("decision")
            == "archive_lifecycle_finality"
        ]
        proactive_lifecycle_finality_retire_turns = [
            turn
            for turn in proactive_lifecycle_finality_decisions
            if (turn.proactive_lifecycle_finality_decision or {}).get("decision")
            == "retire_lifecycle_finality"
        ]
        proactive_lifecycle_completion_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_completion_decision is not None
        ]
        proactive_lifecycle_completion_changed_turns = [
            turn
            for turn in proactive_lifecycle_completion_decisions
            if bool(
                (turn.proactive_lifecycle_completion_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_completion_complete_turns = [
            turn
            for turn in proactive_lifecycle_completion_decisions
            if (turn.proactive_lifecycle_completion_decision or {}).get("decision")
            == "complete_lifecycle_completion"
        ]
        proactive_lifecycle_completion_buffer_turns = [
            turn
            for turn in proactive_lifecycle_completion_decisions
            if (turn.proactive_lifecycle_completion_decision or {}).get("decision")
            == "buffer_lifecycle_completion"
        ]
        proactive_lifecycle_completion_pause_turns = [
            turn
            for turn in proactive_lifecycle_completion_decisions
            if (turn.proactive_lifecycle_completion_decision or {}).get("decision")
            == "pause_lifecycle_completion"
        ]
        proactive_lifecycle_completion_archive_turns = [
            turn
            for turn in proactive_lifecycle_completion_decisions
            if (turn.proactive_lifecycle_completion_decision or {}).get("decision")
            == "archive_lifecycle_completion"
        ]
        proactive_lifecycle_completion_retire_turns = [
            turn
            for turn in proactive_lifecycle_completion_decisions
            if (turn.proactive_lifecycle_completion_decision or {}).get("decision")
            == "retire_lifecycle_completion"
        ]
        proactive_lifecycle_conclusion_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_conclusion_decision is not None
        ]
        proactive_lifecycle_conclusion_changed_turns = [
            turn
            for turn in proactive_lifecycle_conclusion_decisions
            if bool(
                (turn.proactive_lifecycle_conclusion_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_conclusion_complete_turns = [
            turn
            for turn in proactive_lifecycle_conclusion_decisions
            if (turn.proactive_lifecycle_conclusion_decision or {}).get("decision")
            == "complete_lifecycle_conclusion"
        ]
        proactive_lifecycle_conclusion_buffer_turns = [
            turn
            for turn in proactive_lifecycle_conclusion_decisions
            if (turn.proactive_lifecycle_conclusion_decision or {}).get("decision")
            == "buffer_lifecycle_conclusion"
        ]
        proactive_lifecycle_conclusion_pause_turns = [
            turn
            for turn in proactive_lifecycle_conclusion_decisions
            if (turn.proactive_lifecycle_conclusion_decision or {}).get("decision")
            == "pause_lifecycle_conclusion"
        ]
        proactive_lifecycle_conclusion_archive_turns = [
            turn
            for turn in proactive_lifecycle_conclusion_decisions
            if (turn.proactive_lifecycle_conclusion_decision or {}).get("decision")
            == "archive_lifecycle_conclusion"
        ]
        proactive_lifecycle_conclusion_retire_turns = [
            turn
            for turn in proactive_lifecycle_conclusion_decisions
            if (turn.proactive_lifecycle_conclusion_decision or {}).get("decision")
            == "retire_lifecycle_conclusion"
        ]
        proactive_lifecycle_disposition_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_disposition_decision is not None
        ]
        proactive_lifecycle_disposition_changed_turns = [
            turn
            for turn in proactive_lifecycle_disposition_decisions
            if bool(
                (turn.proactive_lifecycle_disposition_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_disposition_complete_turns = [
            turn
            for turn in proactive_lifecycle_disposition_decisions
            if (turn.proactive_lifecycle_disposition_decision or {}).get("decision")
            == "complete_lifecycle_disposition"
        ]
        proactive_lifecycle_disposition_buffer_turns = [
            turn
            for turn in proactive_lifecycle_disposition_decisions
            if (turn.proactive_lifecycle_disposition_decision or {}).get("decision")
            == "buffer_lifecycle_disposition"
        ]
        proactive_lifecycle_disposition_pause_turns = [
            turn
            for turn in proactive_lifecycle_disposition_decisions
            if (turn.proactive_lifecycle_disposition_decision or {}).get("decision")
            == "pause_lifecycle_disposition"
        ]
        proactive_lifecycle_disposition_archive_turns = [
            turn
            for turn in proactive_lifecycle_disposition_decisions
            if (turn.proactive_lifecycle_disposition_decision or {}).get("decision")
            == "archive_lifecycle_disposition"
        ]
        proactive_lifecycle_disposition_retire_turns = [
            turn
            for turn in proactive_lifecycle_disposition_decisions
            if (turn.proactive_lifecycle_disposition_decision or {}).get("decision")
            == "retire_lifecycle_disposition"
        ]
        proactive_lifecycle_standing_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_standing_decision is not None
        ]
        proactive_lifecycle_standing_changed_turns = [
            turn
            for turn in proactive_lifecycle_standing_decisions
            if bool((turn.proactive_lifecycle_standing_decision or {}).get("changed"))
        ]
        proactive_lifecycle_standing_keep_turns = [
            turn
            for turn in proactive_lifecycle_standing_decisions
            if (turn.proactive_lifecycle_standing_decision or {}).get("decision")
            == "keep_lifecycle_standing"
        ]
        proactive_lifecycle_standing_buffer_turns = [
            turn
            for turn in proactive_lifecycle_standing_decisions
            if (turn.proactive_lifecycle_standing_decision or {}).get("decision")
            == "buffer_lifecycle_standing"
        ]
        proactive_lifecycle_standing_pause_turns = [
            turn
            for turn in proactive_lifecycle_standing_decisions
            if (turn.proactive_lifecycle_standing_decision or {}).get("decision")
            == "pause_lifecycle_standing"
        ]
        proactive_lifecycle_standing_archive_turns = [
            turn
            for turn in proactive_lifecycle_standing_decisions
            if (turn.proactive_lifecycle_standing_decision or {}).get("decision")
            == "archive_lifecycle_standing"
        ]
        proactive_lifecycle_standing_retire_turns = [
            turn
            for turn in proactive_lifecycle_standing_decisions
            if (turn.proactive_lifecycle_standing_decision or {}).get("decision")
            == "retire_lifecycle_standing"
        ]
        proactive_lifecycle_residency_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_residency_decision is not None
        ]
        proactive_lifecycle_residency_changed_turns = [
            turn
            for turn in proactive_lifecycle_residency_decisions
            if bool(
                (turn.proactive_lifecycle_residency_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_residency_keep_turns = [
            turn
            for turn in proactive_lifecycle_residency_decisions
            if (turn.proactive_lifecycle_residency_decision or {}).get("decision")
            == "keep_lifecycle_residency"
        ]
        proactive_lifecycle_residency_buffer_turns = [
            turn
            for turn in proactive_lifecycle_residency_decisions
            if (turn.proactive_lifecycle_residency_decision or {}).get("decision")
            == "buffer_lifecycle_residency"
        ]
        proactive_lifecycle_residency_pause_turns = [
            turn
            for turn in proactive_lifecycle_residency_decisions
            if (turn.proactive_lifecycle_residency_decision or {}).get("decision")
            == "pause_lifecycle_residency"
        ]
        proactive_lifecycle_residency_archive_turns = [
            turn
            for turn in proactive_lifecycle_residency_decisions
            if (turn.proactive_lifecycle_residency_decision or {}).get("decision")
            == "archive_lifecycle_residency"
        ]
        proactive_lifecycle_residency_retire_turns = [
            turn
            for turn in proactive_lifecycle_residency_decisions
            if (turn.proactive_lifecycle_residency_decision or {}).get("decision")
            == "retire_lifecycle_residency"
        ]
        proactive_lifecycle_tenure_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_tenure_decision is not None
        ]
        proactive_lifecycle_tenure_changed_turns = [
            turn
            for turn in proactive_lifecycle_tenure_decisions
            if bool((turn.proactive_lifecycle_tenure_decision or {}).get("changed"))
        ]
        proactive_lifecycle_tenure_keep_turns = [
            turn
            for turn in proactive_lifecycle_tenure_decisions
            if (turn.proactive_lifecycle_tenure_decision or {}).get("decision")
            == "keep_lifecycle_tenure"
        ]
        proactive_lifecycle_tenure_buffer_turns = [
            turn
            for turn in proactive_lifecycle_tenure_decisions
            if (turn.proactive_lifecycle_tenure_decision or {}).get("decision")
            == "buffer_lifecycle_tenure"
        ]
        proactive_lifecycle_tenure_pause_turns = [
            turn
            for turn in proactive_lifecycle_tenure_decisions
            if (turn.proactive_lifecycle_tenure_decision or {}).get("decision")
            == "pause_lifecycle_tenure"
        ]
        proactive_lifecycle_tenure_archive_turns = [
            turn
            for turn in proactive_lifecycle_tenure_decisions
            if (turn.proactive_lifecycle_tenure_decision or {}).get("decision")
            == "archive_lifecycle_tenure"
        ]
        proactive_lifecycle_tenure_retire_turns = [
            turn
            for turn in proactive_lifecycle_tenure_decisions
            if (turn.proactive_lifecycle_tenure_decision or {}).get("decision")
            == "retire_lifecycle_tenure"
        ]
        proactive_lifecycle_persistence_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_persistence_decision is not None
        ]
        proactive_lifecycle_persistence_changed_turns = [
            turn
            for turn in proactive_lifecycle_persistence_decisions
            if bool(
                (turn.proactive_lifecycle_persistence_decision or {}).get("changed")
            )
        ]
        proactive_lifecycle_persistence_keep_turns = [
            turn
            for turn in proactive_lifecycle_persistence_decisions
            if (turn.proactive_lifecycle_persistence_decision or {}).get("decision")
            == "keep_lifecycle_persistence"
        ]
        proactive_lifecycle_persistence_buffer_turns = [
            turn
            for turn in proactive_lifecycle_persistence_decisions
            if (turn.proactive_lifecycle_persistence_decision or {}).get("decision")
            == "buffer_lifecycle_persistence"
        ]
        proactive_lifecycle_persistence_pause_turns = [
            turn
            for turn in proactive_lifecycle_persistence_decisions
            if (turn.proactive_lifecycle_persistence_decision or {}).get("decision")
            == "pause_lifecycle_persistence"
        ]
        proactive_lifecycle_persistence_archive_turns = [
            turn
            for turn in proactive_lifecycle_persistence_decisions
            if (turn.proactive_lifecycle_persistence_decision or {}).get("decision")
            == "archive_lifecycle_persistence"
        ]
        proactive_lifecycle_persistence_retire_turns = [
            turn
            for turn in proactive_lifecycle_persistence_decisions
            if (turn.proactive_lifecycle_persistence_decision or {}).get("decision")
            == "retire_lifecycle_persistence"
        ]
        proactive_lifecycle_longevity_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_longevity_decision is not None
        ]
        proactive_lifecycle_longevity_changed_turns = [
            turn
            for turn in proactive_lifecycle_longevity_decisions
            if bool((turn.proactive_lifecycle_longevity_decision or {}).get("changed"))
        ]
        proactive_lifecycle_longevity_keep_turns = [
            turn
            for turn in proactive_lifecycle_longevity_decisions
            if (turn.proactive_lifecycle_longevity_decision or {}).get("decision")
            == "keep_lifecycle_longevity"
        ]
        proactive_lifecycle_longevity_buffer_turns = [
            turn
            for turn in proactive_lifecycle_longevity_decisions
            if (turn.proactive_lifecycle_longevity_decision or {}).get("decision")
            == "buffer_lifecycle_longevity"
        ]
        proactive_lifecycle_longevity_pause_turns = [
            turn
            for turn in proactive_lifecycle_longevity_decisions
            if (turn.proactive_lifecycle_longevity_decision or {}).get("decision")
            == "pause_lifecycle_longevity"
        ]
        proactive_lifecycle_longevity_archive_turns = [
            turn
            for turn in proactive_lifecycle_longevity_decisions
            if (turn.proactive_lifecycle_longevity_decision or {}).get("decision")
            == "archive_lifecycle_longevity"
        ]
        proactive_lifecycle_longevity_retire_turns = [
            turn
            for turn in proactive_lifecycle_longevity_decisions
            if (turn.proactive_lifecycle_longevity_decision or {}).get("decision")
            == "retire_lifecycle_longevity"
        ]
        proactive_lifecycle_legacy_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_legacy_decision is not None
        ]
        proactive_lifecycle_legacy_changed_turns = [
            turn
            for turn in proactive_lifecycle_legacy_decisions
            if bool((turn.proactive_lifecycle_legacy_decision or {}).get("changed"))
        ]
        proactive_lifecycle_legacy_keep_turns = [
            turn
            for turn in proactive_lifecycle_legacy_decisions
            if (turn.proactive_lifecycle_legacy_decision or {}).get("decision")
            == "keep_lifecycle_legacy"
        ]
        proactive_lifecycle_legacy_buffer_turns = [
            turn
            for turn in proactive_lifecycle_legacy_decisions
            if (turn.proactive_lifecycle_legacy_decision or {}).get("decision")
            == "buffer_lifecycle_legacy"
        ]
        proactive_lifecycle_legacy_pause_turns = [
            turn
            for turn in proactive_lifecycle_legacy_decisions
            if (turn.proactive_lifecycle_legacy_decision or {}).get("decision")
            == "pause_lifecycle_legacy"
        ]
        proactive_lifecycle_legacy_archive_turns = [
            turn
            for turn in proactive_lifecycle_legacy_decisions
            if (turn.proactive_lifecycle_legacy_decision or {}).get("decision")
            == "archive_lifecycle_legacy"
        ]
        proactive_lifecycle_legacy_retire_turns = [
            turn
            for turn in proactive_lifecycle_legacy_decisions
            if (turn.proactive_lifecycle_legacy_decision or {}).get("decision")
            == "retire_lifecycle_legacy"
        ]
        proactive_lifecycle_heritage_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_heritage_decision is not None
        ]
        proactive_lifecycle_heritage_changed_turns = [
            turn
            for turn in proactive_lifecycle_heritage_decisions
            if bool((turn.proactive_lifecycle_heritage_decision or {}).get("changed"))
        ]
        proactive_lifecycle_heritage_keep_turns = [
            turn
            for turn in proactive_lifecycle_heritage_decisions
            if (turn.proactive_lifecycle_heritage_decision or {}).get("decision")
            == "keep_lifecycle_heritage"
        ]
        proactive_lifecycle_heritage_buffer_turns = [
            turn
            for turn in proactive_lifecycle_heritage_decisions
            if (turn.proactive_lifecycle_heritage_decision or {}).get("decision")
            == "buffer_lifecycle_heritage"
        ]
        proactive_lifecycle_heritage_pause_turns = [
            turn
            for turn in proactive_lifecycle_heritage_decisions
            if (turn.proactive_lifecycle_heritage_decision or {}).get("decision")
            == "pause_lifecycle_heritage"
        ]
        proactive_lifecycle_heritage_archive_turns = [
            turn
            for turn in proactive_lifecycle_heritage_decisions
            if (turn.proactive_lifecycle_heritage_decision or {}).get("decision")
            == "archive_lifecycle_heritage"
        ]
        proactive_lifecycle_heritage_retire_turns = [
            turn
            for turn in proactive_lifecycle_heritage_decisions
            if (turn.proactive_lifecycle_heritage_decision or {}).get("decision")
            == "retire_lifecycle_heritage"
        ]
        proactive_lifecycle_lineage_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_lineage_decision is not None
        ]
        proactive_lifecycle_lineage_changed_turns = [
            turn
            for turn in proactive_lifecycle_lineage_decisions
            if bool((turn.proactive_lifecycle_lineage_decision or {}).get("changed"))
        ]
        proactive_lifecycle_lineage_keep_turns = [
            turn
            for turn in proactive_lifecycle_lineage_decisions
            if (turn.proactive_lifecycle_lineage_decision or {}).get("decision")
            == "keep_lifecycle_lineage"
        ]
        proactive_lifecycle_lineage_buffer_turns = [
            turn
            for turn in proactive_lifecycle_lineage_decisions
            if (turn.proactive_lifecycle_lineage_decision or {}).get("decision")
            == "buffer_lifecycle_lineage"
        ]
        proactive_lifecycle_lineage_pause_turns = [
            turn
            for turn in proactive_lifecycle_lineage_decisions
            if (turn.proactive_lifecycle_lineage_decision or {}).get("decision")
            == "pause_lifecycle_lineage"
        ]
        proactive_lifecycle_lineage_archive_turns = [
            turn
            for turn in proactive_lifecycle_lineage_decisions
            if (turn.proactive_lifecycle_lineage_decision or {}).get("decision")
            == "archive_lifecycle_lineage"
        ]
        proactive_lifecycle_lineage_retire_turns = [
            turn
            for turn in proactive_lifecycle_lineage_decisions
            if (turn.proactive_lifecycle_lineage_decision or {}).get("decision")
            == "retire_lifecycle_lineage"
        ]
        proactive_lifecycle_ancestry_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_ancestry_decision is not None
        ]
        proactive_lifecycle_ancestry_changed_turns = [
            turn
            for turn in proactive_lifecycle_ancestry_decisions
            if bool((turn.proactive_lifecycle_ancestry_decision or {}).get("changed"))
        ]
        proactive_lifecycle_ancestry_keep_turns = [
            turn
            for turn in proactive_lifecycle_ancestry_decisions
            if (turn.proactive_lifecycle_ancestry_decision or {}).get("decision")
            == "keep_lifecycle_ancestry"
        ]
        proactive_lifecycle_ancestry_buffer_turns = [
            turn
            for turn in proactive_lifecycle_ancestry_decisions
            if (turn.proactive_lifecycle_ancestry_decision or {}).get("decision")
            == "buffer_lifecycle_ancestry"
        ]
        proactive_lifecycle_ancestry_pause_turns = [
            turn
            for turn in proactive_lifecycle_ancestry_decisions
            if (turn.proactive_lifecycle_ancestry_decision or {}).get("decision")
            == "pause_lifecycle_ancestry"
        ]
        proactive_lifecycle_ancestry_archive_turns = [
            turn
            for turn in proactive_lifecycle_ancestry_decisions
            if (turn.proactive_lifecycle_ancestry_decision or {}).get("decision")
            == "archive_lifecycle_ancestry"
        ]
        proactive_lifecycle_ancestry_retire_turns = [
            turn
            for turn in proactive_lifecycle_ancestry_decisions
            if (turn.proactive_lifecycle_ancestry_decision or {}).get("decision")
            == "retire_lifecycle_ancestry"
        ]
        proactive_lifecycle_provenance_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_provenance_decision is not None
        ]
        proactive_lifecycle_provenance_changed_turns = [
            turn
            for turn in proactive_lifecycle_provenance_decisions
            if bool((turn.proactive_lifecycle_provenance_decision or {}).get("changed"))
        ]
        proactive_lifecycle_provenance_keep_turns = [
            turn
            for turn in proactive_lifecycle_provenance_decisions
            if (turn.proactive_lifecycle_provenance_decision or {}).get("decision")
            == "keep_lifecycle_provenance"
        ]
        proactive_lifecycle_provenance_buffer_turns = [
            turn
            for turn in proactive_lifecycle_provenance_decisions
            if (turn.proactive_lifecycle_provenance_decision or {}).get("decision")
            == "buffer_lifecycle_provenance"
        ]
        proactive_lifecycle_provenance_pause_turns = [
            turn
            for turn in proactive_lifecycle_provenance_decisions
            if (turn.proactive_lifecycle_provenance_decision or {}).get("decision")
            == "pause_lifecycle_provenance"
        ]
        proactive_lifecycle_provenance_archive_turns = [
            turn
            for turn in proactive_lifecycle_provenance_decisions
            if (turn.proactive_lifecycle_provenance_decision or {}).get("decision")
            == "archive_lifecycle_provenance"
        ]
        proactive_lifecycle_provenance_retire_turns = [
            turn
            for turn in proactive_lifecycle_provenance_decisions
            if (turn.proactive_lifecycle_provenance_decision or {}).get("decision")
            == "retire_lifecycle_provenance"
        ]
        proactive_lifecycle_origin_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_origin_decision is not None
        ]
        proactive_lifecycle_origin_changed_turns = [
            turn
            for turn in proactive_lifecycle_origin_decisions
            if bool((turn.proactive_lifecycle_origin_decision or {}).get("changed"))
        ]
        proactive_lifecycle_origin_keep_turns = [
            turn
            for turn in proactive_lifecycle_origin_decisions
            if (turn.proactive_lifecycle_origin_decision or {}).get("decision")
            == "keep_lifecycle_origin"
        ]
        proactive_lifecycle_origin_buffer_turns = [
            turn
            for turn in proactive_lifecycle_origin_decisions
            if (turn.proactive_lifecycle_origin_decision or {}).get("decision")
            == "buffer_lifecycle_origin"
        ]
        proactive_lifecycle_origin_pause_turns = [
            turn
            for turn in proactive_lifecycle_origin_decisions
            if (turn.proactive_lifecycle_origin_decision or {}).get("decision")
            == "pause_lifecycle_origin"
        ]
        proactive_lifecycle_origin_archive_turns = [
            turn
            for turn in proactive_lifecycle_origin_decisions
            if (turn.proactive_lifecycle_origin_decision or {}).get("decision")
            == "archive_lifecycle_origin"
        ]
        proactive_lifecycle_origin_retire_turns = [
            turn
            for turn in proactive_lifecycle_origin_decisions
            if (turn.proactive_lifecycle_origin_decision or {}).get("decision")
            == "retire_lifecycle_origin"
        ]
        proactive_lifecycle_root_decisions = [
            turn for turn in turn_records if turn.proactive_lifecycle_root_decision is not None
        ]
        proactive_lifecycle_root_changed_turns = [
            turn
            for turn in proactive_lifecycle_root_decisions
            if bool((turn.proactive_lifecycle_root_decision or {}).get("changed"))
        ]
        proactive_lifecycle_root_keep_turns = [
            turn
            for turn in proactive_lifecycle_root_decisions
            if (turn.proactive_lifecycle_root_decision or {}).get("decision")
            == "keep_lifecycle_root"
        ]
        proactive_lifecycle_root_buffer_turns = [
            turn
            for turn in proactive_lifecycle_root_decisions
            if (turn.proactive_lifecycle_root_decision or {}).get("decision")
            == "buffer_lifecycle_root"
        ]
        proactive_lifecycle_root_pause_turns = [
            turn
            for turn in proactive_lifecycle_root_decisions
            if (turn.proactive_lifecycle_root_decision or {}).get("decision")
            == "pause_lifecycle_root"
        ]
        proactive_lifecycle_root_archive_turns = [
            turn
            for turn in proactive_lifecycle_root_decisions
            if (turn.proactive_lifecycle_root_decision or {}).get("decision")
            == "archive_lifecycle_root"
        ]
        proactive_lifecycle_root_retire_turns = [
            turn
            for turn in proactive_lifecycle_root_decisions
            if (turn.proactive_lifecycle_root_decision or {}).get("decision")
            == "retire_lifecycle_root"
        ]
        proactive_lifecycle_foundation_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_foundation_decision is not None
        ]
        proactive_lifecycle_foundation_changed_turns = [
            turn
            for turn in proactive_lifecycle_foundation_decisions
            if bool((turn.proactive_lifecycle_foundation_decision or {}).get("changed"))
        ]
        proactive_lifecycle_foundation_keep_turns = [
            turn
            for turn in proactive_lifecycle_foundation_decisions
            if (turn.proactive_lifecycle_foundation_decision or {}).get("decision")
            == "keep_lifecycle_foundation"
        ]
        proactive_lifecycle_foundation_buffer_turns = [
            turn
            for turn in proactive_lifecycle_foundation_decisions
            if (turn.proactive_lifecycle_foundation_decision or {}).get("decision")
            == "buffer_lifecycle_foundation"
        ]
        proactive_lifecycle_foundation_pause_turns = [
            turn
            for turn in proactive_lifecycle_foundation_decisions
            if (turn.proactive_lifecycle_foundation_decision or {}).get("decision")
            == "pause_lifecycle_foundation"
        ]
        proactive_lifecycle_foundation_archive_turns = [
            turn
            for turn in proactive_lifecycle_foundation_decisions
            if (turn.proactive_lifecycle_foundation_decision or {}).get("decision")
            == "archive_lifecycle_foundation"
        ]
        proactive_lifecycle_foundation_retire_turns = [
            turn
            for turn in proactive_lifecycle_foundation_decisions
            if (turn.proactive_lifecycle_foundation_decision or {}).get("decision")
            == "retire_lifecycle_foundation"
        ]
        proactive_lifecycle_bedrock_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_bedrock_decision is not None
        ]
        proactive_lifecycle_bedrock_changed_turns = [
            turn
            for turn in proactive_lifecycle_bedrock_decisions
            if bool((turn.proactive_lifecycle_bedrock_decision or {}).get("changed"))
        ]
        proactive_lifecycle_bedrock_keep_turns = [
            turn
            for turn in proactive_lifecycle_bedrock_decisions
            if (turn.proactive_lifecycle_bedrock_decision or {}).get("decision")
            == "keep_lifecycle_bedrock"
        ]
        proactive_lifecycle_bedrock_buffer_turns = [
            turn
            for turn in proactive_lifecycle_bedrock_decisions
            if (turn.proactive_lifecycle_bedrock_decision or {}).get("decision")
            == "buffer_lifecycle_bedrock"
        ]
        proactive_lifecycle_bedrock_pause_turns = [
            turn
            for turn in proactive_lifecycle_bedrock_decisions
            if (turn.proactive_lifecycle_bedrock_decision or {}).get("decision")
            == "pause_lifecycle_bedrock"
        ]
        proactive_lifecycle_bedrock_archive_turns = [
            turn
            for turn in proactive_lifecycle_bedrock_decisions
            if (turn.proactive_lifecycle_bedrock_decision or {}).get("decision")
            == "archive_lifecycle_bedrock"
        ]
        proactive_lifecycle_bedrock_retire_turns = [
            turn
            for turn in proactive_lifecycle_bedrock_decisions
            if (turn.proactive_lifecycle_bedrock_decision or {}).get("decision")
            == "retire_lifecycle_bedrock"
        ]
        proactive_lifecycle_substrate_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_substrate_decision is not None
        ]
        proactive_lifecycle_substrate_changed_turns = [
            turn
            for turn in proactive_lifecycle_substrate_decisions
            if bool((turn.proactive_lifecycle_substrate_decision or {}).get("changed"))
        ]
        proactive_lifecycle_substrate_keep_turns = [
            turn
            for turn in proactive_lifecycle_substrate_decisions
            if (turn.proactive_lifecycle_substrate_decision or {}).get("decision")
            == "keep_lifecycle_substrate"
        ]
        proactive_lifecycle_substrate_buffer_turns = [
            turn
            for turn in proactive_lifecycle_substrate_decisions
            if (turn.proactive_lifecycle_substrate_decision or {}).get("decision")
            == "buffer_lifecycle_substrate"
        ]
        proactive_lifecycle_substrate_pause_turns = [
            turn
            for turn in proactive_lifecycle_substrate_decisions
            if (turn.proactive_lifecycle_substrate_decision or {}).get("decision")
            == "pause_lifecycle_substrate"
        ]
        proactive_lifecycle_substrate_archive_turns = [
            turn
            for turn in proactive_lifecycle_substrate_decisions
            if (turn.proactive_lifecycle_substrate_decision or {}).get("decision")
            == "archive_lifecycle_substrate"
        ]
        proactive_lifecycle_substrate_retire_turns = [
            turn
            for turn in proactive_lifecycle_substrate_decisions
            if (turn.proactive_lifecycle_substrate_decision or {}).get("decision")
            == "retire_lifecycle_substrate"
        ]
        proactive_lifecycle_stratum_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_stratum_decision is not None
        ]
        proactive_lifecycle_stratum_changed_turns = [
            turn
            for turn in proactive_lifecycle_stratum_decisions
            if bool((turn.proactive_lifecycle_stratum_decision or {}).get("changed"))
        ]
        proactive_lifecycle_stratum_keep_turns = [
            turn
            for turn in proactive_lifecycle_stratum_decisions
            if (turn.proactive_lifecycle_stratum_decision or {}).get("decision")
            == "keep_lifecycle_stratum"
        ]
        proactive_lifecycle_stratum_buffer_turns = [
            turn
            for turn in proactive_lifecycle_stratum_decisions
            if (turn.proactive_lifecycle_stratum_decision or {}).get("decision")
            == "buffer_lifecycle_stratum"
        ]
        proactive_lifecycle_stratum_pause_turns = [
            turn
            for turn in proactive_lifecycle_stratum_decisions
            if (turn.proactive_lifecycle_stratum_decision or {}).get("decision")
            == "pause_lifecycle_stratum"
        ]
        proactive_lifecycle_stratum_archive_turns = [
            turn
            for turn in proactive_lifecycle_stratum_decisions
            if (turn.proactive_lifecycle_stratum_decision or {}).get("decision")
            == "archive_lifecycle_stratum"
        ]
        proactive_lifecycle_stratum_retire_turns = [
            turn
            for turn in proactive_lifecycle_stratum_decisions
            if (turn.proactive_lifecycle_stratum_decision or {}).get("decision")
            == "retire_lifecycle_stratum"
        ]
        proactive_lifecycle_layer_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_layer_decision is not None
        ]
        proactive_lifecycle_layer_changed_turns = [
            turn
            for turn in proactive_lifecycle_layer_decisions
            if bool((turn.proactive_lifecycle_layer_decision or {}).get("changed"))
        ]
        proactive_lifecycle_layer_keep_turns = [
            turn
            for turn in proactive_lifecycle_layer_decisions
            if (turn.proactive_lifecycle_layer_decision or {}).get("decision")
            == "keep_lifecycle_layer"
        ]
        proactive_lifecycle_layer_buffer_turns = [
            turn
            for turn in proactive_lifecycle_layer_decisions
            if (turn.proactive_lifecycle_layer_decision or {}).get("decision")
            == "buffer_lifecycle_layer"
        ]
        proactive_lifecycle_layer_pause_turns = [
            turn
            for turn in proactive_lifecycle_layer_decisions
            if (turn.proactive_lifecycle_layer_decision or {}).get("decision")
            == "pause_lifecycle_layer"
        ]
        proactive_lifecycle_layer_archive_turns = [
            turn
            for turn in proactive_lifecycle_layer_decisions
            if (turn.proactive_lifecycle_layer_decision or {}).get("decision")
            == "archive_lifecycle_layer"
        ]
        proactive_lifecycle_layer_retire_turns = [
            turn
            for turn in proactive_lifecycle_layer_decisions
            if (turn.proactive_lifecycle_layer_decision or {}).get("decision")
            == "retire_lifecycle_layer"
        ]
        proactive_lifecycle_durability_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_lifecycle_durability_decision is not None
        ]
        proactive_lifecycle_durability_changed_turns = [
            turn
            for turn in proactive_lifecycle_durability_decisions
            if bool((turn.proactive_lifecycle_durability_decision or {}).get("changed"))
        ]
        proactive_lifecycle_durability_keep_turns = [
            turn
            for turn in proactive_lifecycle_durability_decisions
            if (turn.proactive_lifecycle_durability_decision or {}).get("decision")
            == "keep_lifecycle_durability"
        ]
        proactive_lifecycle_durability_buffer_turns = [
            turn
            for turn in proactive_lifecycle_durability_decisions
            if (turn.proactive_lifecycle_durability_decision or {}).get("decision")
            == "buffer_lifecycle_durability"
        ]
        proactive_lifecycle_durability_pause_turns = [
            turn
            for turn in proactive_lifecycle_durability_decisions
            if (turn.proactive_lifecycle_durability_decision or {}).get("decision")
            == "pause_lifecycle_durability"
        ]
        proactive_lifecycle_durability_archive_turns = [
            turn
            for turn in proactive_lifecycle_durability_decisions
            if (turn.proactive_lifecycle_durability_decision or {}).get("decision")
            == "archive_lifecycle_durability"
        ]
        proactive_lifecycle_durability_retire_turns = [
            turn
            for turn in proactive_lifecycle_durability_decisions
            if (turn.proactive_lifecycle_durability_decision or {}).get("decision")
            == "retire_lifecycle_durability"
        ]
        proactive_stage_refresh_plans = [
            turn for turn in turn_records if turn.proactive_stage_refresh_plan is not None
        ]
        proactive_stage_refresh_changed_turns = [
            turn
            for turn in proactive_stage_refresh_plans
            if bool((turn.proactive_stage_refresh_plan or {}).get("changed"))
        ]
        proactive_stage_replan_assessments = [
            turn
            for turn in turn_records
            if turn.proactive_stage_replan_assessment is not None
        ]
        proactive_stage_replan_changed_turns = [
            turn
            for turn in proactive_stage_replan_assessments
            if bool((turn.proactive_stage_replan_assessment or {}).get("changed"))
        ]
        proactive_dispatch_feedback_assessments = [
            turn
            for turn in turn_records
            if turn.proactive_dispatch_feedback_assessment is not None
        ]
        proactive_dispatch_feedback_changed_turns = [
            turn
            for turn in proactive_dispatch_feedback_assessments
            if bool((turn.proactive_dispatch_feedback_assessment or {}).get("changed"))
        ]
        proactive_dispatch_gate_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_dispatch_gate_decision is not None
        ]
        proactive_dispatch_gate_deferred_turns = [
            turn
            for turn in proactive_dispatch_gate_decisions
            if (turn.proactive_dispatch_gate_decision or {}).get("decision") == "defer"
        ]
        proactive_dispatch_envelope_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_dispatch_envelope_decision is not None
        ]
        proactive_dispatch_envelope_changed_turns = [
            turn
            for turn in proactive_dispatch_envelope_decisions
            if bool((turn.proactive_dispatch_envelope_decision or {}).get("changed"))
        ]
        proactive_stage_state_decisions = [
            turn for turn in turn_records if turn.proactive_stage_state_decision is not None
        ]
        proactive_stage_state_changed_turns = [
            turn
            for turn in proactive_stage_state_decisions
            if bool((turn.proactive_stage_state_decision or {}).get("changed"))
        ]
        proactive_stage_transition_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_stage_transition_decision is not None
        ]
        proactive_stage_transition_changed_turns = [
            turn
            for turn in proactive_stage_transition_decisions
            if bool((turn.proactive_stage_transition_decision or {}).get("changed"))
        ]
        proactive_stage_transition_rescheduled_turns = [
            turn
            for turn in proactive_stage_transition_decisions
            if str(
                (turn.proactive_stage_transition_decision or {}).get(
                    "transition_mode"
                )
            ).startswith("reschedule_")
        ]
        proactive_stage_transition_terminal_turns = [
            turn
            for turn in proactive_stage_transition_decisions
            if (turn.proactive_stage_transition_decision or {}).get("stage_exit_mode")
            == "retire_line"
        ]
        proactive_stage_machine_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_stage_machine_decision is not None
        ]
        proactive_stage_machine_changed_turns = [
            turn
            for turn in proactive_stage_machine_decisions
            if bool((turn.proactive_stage_machine_decision or {}).get("changed"))
        ]
        proactive_stage_machine_buffered_turns = [
            turn
            for turn in proactive_stage_machine_decisions
            if (turn.proactive_stage_machine_decision or {}).get("actionability")
            in {"reschedule", "wait"}
        ]
        proactive_stage_machine_terminal_turns = [
            turn
            for turn in proactive_stage_machine_decisions
            if (turn.proactive_stage_machine_decision or {}).get("lifecycle_mode")
            == "terminal"
        ]
        proactive_multi_stage_cadence_turns = [
            turn
            for turn in proactive_cadence_plans
            if int((turn.proactive_cadence_plan or {}).get("close_after_stage_index", 0))
            > 1
        ]
        guidance_plans = [turn for turn in turn_records if turn.guidance_plan is not None]
        stabilizing_guidance_turns = [
            turn
            for turn in guidance_plans
            if (turn.guidance_plan or {}).get("mode") == "stabilizing_guidance"
        ]
        reanchor_guidance_turns = [
            turn
            for turn in guidance_plans
            if (turn.guidance_plan or {}).get("mode") == "reanchor_guidance"
        ]
        low_pressure_guidance_turns = [
            turn
            for turn in guidance_plans
            if (turn.guidance_plan or {}).get("handoff_mode")
            in {"no_pressure_checkin", "autonomy_preserving_ping", "repair_soft_ping"}
        ]
        resume_carryover_guidance_turns = [
            turn
            for turn in guidance_plans
            if (turn.guidance_plan or {}).get("carryover_mode") == "resume_ping"
        ]
        cadence_plans = [
            turn for turn in turn_records if turn.conversation_cadence_plan is not None
        ]
        cadence_spacious_turns = [
            turn
            for turn in cadence_plans
            if (turn.conversation_cadence_plan or {}).get("user_space_mode")
            in {"spacious", "explicit_autonomy_space", "consent_space"}
        ]
        cadence_reanchor_turns = [
            turn
            for turn in cadence_plans
            if (turn.conversation_cadence_plan or {}).get("turn_shape")
            == "reanchor_then_step"
        ]
        session_ritual_plans = [
            turn for turn in turn_records if turn.session_ritual_plan is not None
        ]
        session_ritual_somatic_turns = [
            turn
            for turn in session_ritual_plans
            if (turn.session_ritual_plan or {}).get("somatic_shortcut") not in {None, "none"}
        ]
        somatic_orchestration_plans = [
            turn for turn in turn_records if turn.somatic_orchestration_plan is not None
        ]
        somatic_orchestration_active_turns = [
            turn
            for turn in somatic_orchestration_plans
            if (turn.somatic_orchestration_plan or {}).get("status") == "active"
        ]
        somatic_orchestration_followup_allowed_turns = [
            turn
            for turn in somatic_orchestration_plans
            if bool((turn.somatic_orchestration_plan or {}).get("allow_in_followup"))
        ]
        somatic_cue_turns = [
            turn
            for turn in runtime_coordination_snapshots
            if (turn.runtime_coordination_snapshot or {}).get("somatic_cue")
        ]
        proactive_ready_turns = [
            turn
            for turn in turn_records
            if (turn.proactive_followup_directive or {}).get("status") == "ready"
        ]
        proactive_hold_turns = [
            turn
            for turn in turn_records
            if (turn.proactive_followup_directive or {}).get("status") == "hold"
        ]
        proactive_aggregate_governance_assessments = [
            turn
            for turn in turn_records
            if turn.proactive_aggregate_governance_assessment is not None
        ]
        proactive_aggregate_governance_watch_turns = [
            turn
            for turn in proactive_aggregate_governance_assessments
            if (turn.proactive_aggregate_governance_assessment or {}).get("status")
            == "watch"
        ]
        proactive_aggregate_governance_recenter_turns = [
            turn
            for turn in proactive_aggregate_governance_assessments
            if (turn.proactive_aggregate_governance_assessment or {}).get("status")
            == "recenter"
        ]
        proactive_aggregate_controller_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_aggregate_controller_decision is not None
        ]
        proactive_aggregate_controller_changed_turns = [
            turn
            for turn in proactive_aggregate_controller_decisions
            if bool((turn.proactive_aggregate_controller_decision or {}).get("changed"))
        ]
        proactive_orchestration_controller_decisions = [
            turn
            for turn in turn_records
            if turn.proactive_orchestration_controller_decision is not None
        ]
        proactive_orchestration_controller_changed_turns = [
            turn
            for turn in proactive_orchestration_controller_decisions
            if bool(
                (turn.proactive_orchestration_controller_decision or {}).get(
                    "changed"
                )
            )
        ]
        reengagement_matrix_assessments = [
            turn
            for turn in turn_records
            if turn.reengagement_matrix_assessment is not None
        ]
        reengagement_matrix_blocked_turns = [
            turn
            for turn in reengagement_matrix_assessments
            if int((turn.reengagement_matrix_assessment or {}).get("blocked_count", 0))
            > 0
        ]
        reengagement_plans = [
            turn for turn in turn_records if turn.reengagement_plan is not None
        ]
        reengagement_two_part_turns = [
            turn
            for turn in reengagement_plans
            if (turn.reengagement_plan or {}).get("delivery_mode") == "two_part_sequence"
        ]
        reengagement_repair_bridge_turns = [
            turn
            for turn in reengagement_plans
            if (turn.reengagement_plan or {}).get("relational_move") == "repair_bridge"
        ]
        reengagement_somatic_action_turns = [
            turn
            for turn in reengagement_plans
            if (turn.reengagement_plan or {}).get("somatic_action")
        ]
        proactive_dispatch_turns = [
            turn
            for turn in turn_records
            if turn.proactive_followup_dispatch is not None
        ]
        proactive_progression_advanced_dispatch_turns = [
            turn
            for turn in proactive_dispatch_turns
            if bool((turn.proactive_followup_dispatch or {}).get("proactive_progression_advanced"))
        ]
        runtime_quality_doctor_reports = [
            turn
            for turn in turn_records
            if turn.runtime_quality_doctor_report is not None
        ]
        runtime_quality_doctor_watch_turns = [
            turn
            for turn in runtime_quality_doctor_reports
            if (turn.runtime_quality_doctor_report or {}).get("status") == "watch"
        ]
        runtime_quality_doctor_revise_turns = [
            turn
            for turn in runtime_quality_doctor_reports
            if (turn.runtime_quality_doctor_report or {}).get("status") == "revise"
        ]
        system3_snapshots = [
            turn for turn in turn_records if turn.system3_snapshot is not None
        ]
        system3_identity_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("identity_consistency")
            in {"watch", "drift"}
        ]
        identity_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("identity_trajectory_status")
            in {"watch", "recenter"}
        ]
        identity_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("identity_trajectory_status")
            == "recenter"
        ]
        emotional_debt_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("emotional_debt_status")
            in {"watch", "elevated"}
        ]
        emotional_debt_elevated_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("emotional_debt_status") == "elevated"
        ]
        emotional_debt_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("emotional_debt_trajectory_status")
            in {"watch", "decompression_required"}
        ]
        emotional_debt_trajectory_decompression_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("emotional_debt_trajectory_status")
            == "decompression_required"
        ]
        strategy_audit_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("strategy_audit_status")
            in {"watch", "revise"}
        ]
        strategy_audit_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("strategy_audit_status") == "revise"
        ]
        strategy_audit_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("strategy_audit_trajectory_status")
            in {"watch", "corrective"}
        ]
        strategy_audit_trajectory_corrective_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("strategy_audit_trajectory_status")
            == "corrective"
        ]
        strategy_supervision_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("strategy_supervision_status")
            in {"watch", "revise"}
        ]
        strategy_supervision_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("strategy_supervision_status")
            == "revise"
        ]
        strategy_supervision_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get(
                "strategy_supervision_trajectory_status"
            )
            in {"watch", "tighten"}
        ]
        strategy_supervision_trajectory_tighten_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get(
                "strategy_supervision_trajectory_status"
            )
            == "tighten"
        ]
        moral_reasoning_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("moral_reasoning_status")
            in {"watch", "revise"}
        ]
        moral_reasoning_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("moral_reasoning_status") == "revise"
        ]
        moral_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("moral_trajectory_status")
            in {"watch", "recenter"}
        ]
        moral_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("moral_trajectory_status")
            == "recenter"
        ]
        expectation_calibration_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("expectation_calibration_status")
            in {"watch", "revise"}
        ]
        expectation_calibration_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("expectation_calibration_status")
            == "revise"
        ]
        expectation_calibration_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("expectation_calibration_trajectory_status")
            in {"watch", "reset"}
        ]
        expectation_calibration_trajectory_reset_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("expectation_calibration_trajectory_status")
            == "reset"
        ]
        dependency_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("dependency_governance_status")
            in {"watch", "revise"}
        ]
        dependency_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("dependency_governance_status")
            == "revise"
        ]
        dependency_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("dependency_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        dependency_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("dependency_governance_trajectory_status")
            == "recenter"
        ]
        autonomy_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("autonomy_governance_status")
            in {"watch", "revise"}
        ]
        autonomy_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("autonomy_governance_status")
            == "revise"
        ]
        autonomy_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("autonomy_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        autonomy_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("autonomy_governance_trajectory_status")
            == "recenter"
        ]
        boundary_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("boundary_governance_status")
            in {"watch", "revise"}
        ]
        boundary_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("boundary_governance_status")
            == "revise"
        ]
        boundary_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("boundary_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        boundary_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("boundary_governance_trajectory_status")
            == "recenter"
        ]
        support_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("support_governance_status")
            in {"watch", "revise"}
        ]
        support_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("support_governance_status")
            == "revise"
        ]
        support_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("support_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        support_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("support_governance_trajectory_status")
            == "recenter"
        ]
        continuity_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("continuity_governance_status")
            in {"watch", "revise"}
        ]
        continuity_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("continuity_governance_status")
            == "revise"
        ]
        continuity_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("continuity_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        continuity_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("continuity_governance_trajectory_status")
            == "recenter"
        ]
        repair_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("repair_governance_status")
            in {"watch", "revise"}
        ]
        repair_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("repair_governance_status")
            == "revise"
        ]
        repair_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("repair_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        repair_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("repair_governance_trajectory_status")
            == "recenter"
        ]
        attunement_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("attunement_governance_status")
            in {"watch", "revise"}
        ]
        attunement_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("attunement_governance_status")
            == "revise"
        ]
        attunement_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("attunement_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        attunement_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("attunement_governance_trajectory_status")
            == "recenter"
        ]
        trust_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("trust_governance_status")
            in {"watch", "revise"}
        ]
        trust_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("trust_governance_status")
            == "revise"
        ]
        trust_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("trust_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        trust_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("trust_governance_trajectory_status")
            == "recenter"
        ]
        clarity_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("clarity_governance_status")
            in {"watch", "revise"}
        ]
        clarity_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("clarity_governance_status")
            == "revise"
        ]
        clarity_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("clarity_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        clarity_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("clarity_governance_trajectory_status")
            == "recenter"
        ]
        pacing_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("pacing_governance_status")
            in {"watch", "revise"}
        ]
        pacing_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("pacing_governance_status")
            == "revise"
        ]
        pacing_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("pacing_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        pacing_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("pacing_governance_trajectory_status")
            == "recenter"
        ]
        commitment_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("commitment_governance_status")
            in {"watch", "revise"}
        ]
        commitment_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("commitment_governance_status")
            == "revise"
        ]
        commitment_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("commitment_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        commitment_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("commitment_governance_trajectory_status")
            == "recenter"
        ]
        disclosure_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("disclosure_governance_status")
            in {"watch", "revise"}
        ]
        disclosure_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("disclosure_governance_status")
            == "revise"
        ]
        disclosure_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("disclosure_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        disclosure_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("disclosure_governance_trajectory_status")
            == "recenter"
        ]
        reciprocity_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("reciprocity_governance_status")
            in {"watch", "revise"}
        ]
        reciprocity_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("reciprocity_governance_status")
            == "revise"
        ]
        reciprocity_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("reciprocity_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        reciprocity_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("reciprocity_governance_trajectory_status")
            == "recenter"
        ]
        pressure_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("pressure_governance_status")
            in {"watch", "revise"}
        ]
        pressure_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("pressure_governance_status")
            == "revise"
        ]
        pressure_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("pressure_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        pressure_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("pressure_governance_trajectory_status")
            == "recenter"
        ]
        relational_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("relational_governance_status")
            in {"watch", "revise"}
        ]
        relational_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("relational_governance_status")
            == "revise"
        ]
        relational_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("relational_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        relational_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("relational_governance_trajectory_status")
            == "recenter"
        ]
        safety_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("safety_governance_status")
            in {"watch", "revise"}
        ]
        safety_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("safety_governance_status")
            == "revise"
        ]
        safety_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("safety_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        safety_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("safety_governance_trajectory_status")
            == "recenter"
        ]
        progress_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("progress_governance_status")
            in {"watch", "revise"}
        ]
        progress_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("progress_governance_status")
            == "revise"
        ]
        progress_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("progress_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        progress_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("progress_governance_trajectory_status")
            == "recenter"
        ]
        stability_governance_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("stability_governance_status")
            in {"watch", "revise"}
        ]
        stability_governance_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("stability_governance_status")
            == "revise"
        ]
        stability_governance_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("stability_governance_trajectory_status")
            in {"watch", "recenter"}
        ]
        stability_governance_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (
                turn.system3_snapshot or {}
            ).get("stability_governance_trajectory_status")
            == "recenter"
        ]
        growth_transition_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("growth_transition_status")
            in {"watch", "redirect"}
        ]
        growth_transition_ready_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("growth_transition_status") == "ready"
        ]
        growth_transition_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("growth_transition_trajectory_status")
            == "watch"
        ]
        growth_transition_trajectory_advance_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("growth_transition_trajectory_status")
            == "advance"
        ]
        growth_transition_trajectory_redirect_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("growth_transition_trajectory_status")
            == "redirect"
        ]
        version_migration_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("version_migration_status")
            in {"watch", "revise"}
        ]
        version_migration_revise_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("version_migration_status")
            == "revise"
        ]
        version_migration_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("version_migration_trajectory_status")
            in {"watch", "hold"}
        ]
        version_migration_trajectory_hold_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("version_migration_trajectory_status")
            == "hold"
        ]
        user_model_trajectory_watch_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("user_model_trajectory_status")
            in {"watch", "recenter"}
        ]
        user_model_trajectory_recenter_turns = [
            turn
            for turn in system3_snapshots
            if (turn.system3_snapshot or {}).get("user_model_trajectory_status")
            == "recenter"
        ]
        diversity_intervention_turns = [
            turn
            for turn in turn_records
            if bool((turn.strategy_decision or {}).get("explored_strategy"))
            or (turn.strategy_decision or {}).get("diversity_status") == "intervened"
        ]
        diversity_watch_turns = [
            turn
            for turn in turn_records
            if (turn.strategy_decision or {}).get("diversity_status") == "watch"
        ]
        strategy_names = [
            str((turn.strategy_decision or {}).get("strategy", "")).strip()
            for turn in turn_records
            if str((turn.strategy_decision or {}).get("strategy", "")).strip()
        ]
        response_normalization_changed_turns = [
            turn
            for turn in turn_records
            if bool((turn.response_normalization or {}).get("changed"))
        ]

        last_turn = turn_records[-1] if turn_records else None
        latest_strategy = None
        latest_confidence_level = None
        latest_confidence_response_mode = None
        latest_turbulence_risk = None
        latest_strategy_source = None
        latest_strategy_diversity_status = None
        latest_strategy_diversity_entropy = 0.0
        latest_boundary_decision = None
        latest_policy_path = None
        latest_rehearsal_risk = None
        latest_empowerment_audit_status = None
        latest_drafting_question_strategy = None
        latest_drafting_opening_move = None
        latest_rendering_mode = None
        latest_rendering_max_sentences = None
        latest_response_sequence_mode = None
        latest_response_sequence_unit_count = 0
        latest_time_awareness_mode = None
        latest_ritual_phase = None
        latest_cognitive_load_band = None
        latest_guidance_mode = None
        latest_guidance_lead_with = None
        latest_guidance_pacing = None
        latest_guidance_step_budget = None
        latest_guidance_agency_mode = None
        latest_guidance_ritual_action = None
        latest_guidance_checkpoint_style = None
        latest_guidance_handoff_mode = None
        latest_guidance_carryover_mode = None
        latest_cadence_status = None
        latest_cadence_turn_shape = None
        latest_cadence_ritual_depth = None
        latest_cadence_followup_tempo = None
        latest_cadence_user_space_mode = None
        latest_cadence_transition_intent = None
        latest_cadence_next_checkpoint = None
        latest_session_ritual_phase = None
        latest_session_ritual_opening_move = None
        latest_session_ritual_bridge_move = None
        latest_session_ritual_closing_move = None
        latest_session_ritual_continuity_anchor = None
        latest_session_ritual_somatic_shortcut = None
        latest_somatic_orchestration_status = None
        latest_somatic_orchestration_mode = None
        latest_somatic_orchestration_body_anchor = None
        latest_somatic_orchestration_followup_style = None
        latest_response_budget_mode = None
        latest_proactive_followup_eligible = None
        latest_proactive_style = None
        latest_somatic_cue = None
        latest_proactive_followup_status = None
        latest_proactive_followup_style = None
        latest_proactive_followup_after_seconds = None
        latest_proactive_cadence_status = None
        latest_proactive_cadence_key = None
        latest_proactive_cadence_stage_count = 0
        latest_proactive_aggregate_governance_status = None
        latest_proactive_aggregate_governance_primary_domain = None
        latest_proactive_aggregate_governance_summary = None
        latest_proactive_aggregate_governance_domain_count = 0
        latest_proactive_aggregate_controller_key = None
        latest_proactive_aggregate_controller_decision = None
        latest_proactive_aggregate_controller_stage_delay_seconds = 0
        latest_proactive_aggregate_controller_line_delay_seconds = 0
        latest_proactive_aggregate_controller_retry_after_seconds = 0
        latest_proactive_orchestration_controller_key = None
        latest_proactive_orchestration_controller_decision = None
        latest_proactive_orchestration_controller_stage_delay_seconds = 0
        latest_proactive_orchestration_controller_line_delay_seconds = 0
        latest_proactive_orchestration_controller_retry_after_seconds = 0
        latest_proactive_orchestration_controller_primary_source = None
        latest_proactive_guardrail_key = None
        latest_proactive_guardrail_max_dispatch_count = 0
        latest_proactive_guardrail_hard_stop_count = 0
        latest_proactive_guardrail_second_touch_min_user_seconds = 0
        latest_proactive_scheduling_mode = None
        latest_proactive_scheduling_min_seconds_since_last_outbound = 0
        latest_proactive_scheduling_first_touch_extra_delay_seconds = 0
        latest_proactive_orchestration_key = None
        latest_proactive_orchestration_close_loop_stage = None
        latest_proactive_orchestration_second_touch_delivery_mode = None
        latest_proactive_orchestration_second_touch_question_mode = None
        latest_proactive_actuation_key = None
        latest_proactive_actuation_second_touch_opening_move = None
        latest_proactive_actuation_second_touch_bridge_move = None
        latest_proactive_actuation_second_touch_somatic_mode = None
        latest_proactive_actuation_second_touch_user_space_signal = None
        latest_proactive_actuation_final_touch_closing_move = None
        latest_proactive_progression_key = None
        latest_proactive_progression_second_touch_action = None
        latest_proactive_progression_final_touch_action = None
        latest_proactive_stage_controller_key = None
        latest_proactive_stage_controller_decision = None
        latest_proactive_stage_controller_target_stage_label = None
        latest_proactive_stage_controller_additional_delay_seconds = 0
        latest_proactive_stage_controller_strategy_key = None
        latest_proactive_stage_controller_changed = False
        latest_proactive_line_controller_key = None
        latest_proactive_line_controller_decision = None
        latest_proactive_line_controller_line_state = None
        latest_proactive_line_controller_additional_delay_seconds = 0
        latest_proactive_line_controller_changed = False
        latest_proactive_line_state_key = None
        latest_proactive_line_state_mode = None
        latest_proactive_line_state_lifecycle = None
        latest_proactive_line_state_actionability = None
        latest_proactive_line_state_source = None
        latest_proactive_line_transition_key = None
        latest_proactive_line_transition_mode = None
        latest_proactive_line_transition_exit_mode = None
        latest_proactive_line_transition_source = None
        latest_proactive_line_machine_key = None
        latest_proactive_line_machine_mode = None
        latest_proactive_line_machine_lifecycle = None
        latest_proactive_line_machine_actionability = None
        latest_proactive_line_machine_source = None
        latest_proactive_lifecycle_state_key = None
        latest_proactive_lifecycle_state_mode = None
        latest_proactive_lifecycle_state_lifecycle = None
        latest_proactive_lifecycle_state_actionability = None
        latest_proactive_lifecycle_state_source = None
        latest_proactive_lifecycle_transition_key = None
        latest_proactive_lifecycle_transition_mode = None
        latest_proactive_lifecycle_transition_exit_mode = None
        latest_proactive_lifecycle_transition_source = None
        latest_proactive_lifecycle_machine_key = None
        latest_proactive_lifecycle_machine_mode = None
        latest_proactive_lifecycle_machine_lifecycle = None
        latest_proactive_lifecycle_machine_actionability = None
        latest_proactive_lifecycle_machine_source = None
        latest_proactive_lifecycle_controller_key = None
        latest_proactive_lifecycle_controller_state = None
        latest_proactive_lifecycle_controller_decision = None
        latest_proactive_lifecycle_controller_delay_seconds = 0
        latest_proactive_lifecycle_controller_source = None
        latest_proactive_lifecycle_envelope_key = None
        latest_proactive_lifecycle_envelope_state = None
        latest_proactive_lifecycle_envelope_mode = None
        latest_proactive_lifecycle_envelope_decision = None
        latest_proactive_lifecycle_envelope_actionability = None
        latest_proactive_lifecycle_envelope_delay_seconds = 0
        latest_proactive_lifecycle_envelope_source = None
        latest_proactive_lifecycle_scheduler_key = None
        latest_proactive_lifecycle_scheduler_state = None
        latest_proactive_lifecycle_scheduler_mode = None
        latest_proactive_lifecycle_scheduler_decision = None
        latest_proactive_lifecycle_scheduler_actionability = None
        latest_proactive_lifecycle_scheduler_queue_status = None
        latest_proactive_lifecycle_scheduler_delay_seconds = 0
        latest_proactive_lifecycle_scheduler_source = None
        latest_proactive_lifecycle_window_key = None
        latest_proactive_lifecycle_window_state = None
        latest_proactive_lifecycle_window_mode = None
        latest_proactive_lifecycle_window_decision = None
        latest_proactive_lifecycle_window_actionability = None
        latest_proactive_lifecycle_window_queue_status = None
        latest_proactive_lifecycle_window_delay_seconds = 0
        latest_proactive_lifecycle_window_source = None
        latest_proactive_lifecycle_queue_key = None
        latest_proactive_lifecycle_queue_state = None
        latest_proactive_lifecycle_queue_mode = None
        latest_proactive_lifecycle_queue_decision = None
        latest_proactive_lifecycle_queue_actionability = None
        latest_proactive_lifecycle_queue_status = None
        latest_proactive_lifecycle_queue_delay_seconds = 0
        latest_proactive_lifecycle_queue_source = None
        latest_proactive_lifecycle_dispatch_key = None
        latest_proactive_lifecycle_dispatch_state = None
        latest_proactive_lifecycle_dispatch_mode = None
        latest_proactive_lifecycle_dispatch_decision = None
        latest_proactive_lifecycle_dispatch_actionability = None
        latest_proactive_lifecycle_dispatch_delay_seconds = 0
        latest_proactive_lifecycle_dispatch_source = None
        latest_proactive_lifecycle_outcome_key = None
        latest_proactive_lifecycle_outcome_status = None
        latest_proactive_lifecycle_outcome_mode = None
        latest_proactive_lifecycle_outcome_decision = None
        latest_proactive_lifecycle_outcome_actionability = None
        latest_proactive_lifecycle_outcome_message_event_count = 0
        latest_proactive_lifecycle_outcome_source = None
        latest_proactive_lifecycle_resolution_key = None
        latest_proactive_lifecycle_resolution_status = None
        latest_proactive_lifecycle_resolution_mode = None
        latest_proactive_lifecycle_resolution_decision = None
        latest_proactive_lifecycle_resolution_actionability = None
        latest_proactive_lifecycle_resolution_queue_override_status = None
        latest_proactive_lifecycle_resolution_remaining_stage_count = 0
        latest_proactive_lifecycle_resolution_source = None
        latest_proactive_lifecycle_activation_key = None
        latest_proactive_lifecycle_activation_status = None
        latest_proactive_lifecycle_activation_mode = None
        latest_proactive_lifecycle_activation_decision = None
        latest_proactive_lifecycle_activation_actionability = None
        latest_proactive_lifecycle_activation_active_stage_label = None
        latest_proactive_lifecycle_activation_queue_override_status = None
        latest_proactive_lifecycle_activation_source = None
        latest_proactive_lifecycle_settlement_key = None
        latest_proactive_lifecycle_settlement_status = None
        latest_proactive_lifecycle_settlement_mode = None
        latest_proactive_lifecycle_settlement_decision = None
        latest_proactive_lifecycle_settlement_actionability = None
        latest_proactive_lifecycle_settlement_active_stage_label = None
        latest_proactive_lifecycle_settlement_queue_override_status = None
        latest_proactive_lifecycle_settlement_source = None
        latest_proactive_lifecycle_closure_key = None
        latest_proactive_lifecycle_closure_status = None
        latest_proactive_lifecycle_closure_mode = None
        latest_proactive_lifecycle_closure_decision = None
        latest_proactive_lifecycle_closure_actionability = None
        latest_proactive_lifecycle_closure_active_stage_label = None
        latest_proactive_lifecycle_closure_queue_override_status = None
        latest_proactive_lifecycle_closure_source = None
        latest_proactive_lifecycle_availability_key = None
        latest_proactive_lifecycle_availability_status = None
        latest_proactive_lifecycle_availability_mode = None
        latest_proactive_lifecycle_availability_decision = None
        latest_proactive_lifecycle_availability_actionability = None
        latest_proactive_lifecycle_availability_active_stage_label = None
        latest_proactive_lifecycle_availability_queue_override_status = None
        latest_proactive_lifecycle_availability_source = None
        latest_proactive_lifecycle_retention_key = None
        latest_proactive_lifecycle_retention_status = None
        latest_proactive_lifecycle_retention_mode = None
        latest_proactive_lifecycle_retention_decision = None
        latest_proactive_lifecycle_retention_actionability = None
        latest_proactive_lifecycle_retention_active_stage_label = None
        latest_proactive_lifecycle_retention_queue_override_status = None
        latest_proactive_lifecycle_retention_source = None
        latest_proactive_lifecycle_eligibility_key = None
        latest_proactive_lifecycle_eligibility_status = None
        latest_proactive_lifecycle_eligibility_mode = None
        latest_proactive_lifecycle_eligibility_decision = None
        latest_proactive_lifecycle_eligibility_actionability = None
        latest_proactive_lifecycle_eligibility_active_stage_label = None
        latest_proactive_lifecycle_eligibility_queue_override_status = None
        latest_proactive_lifecycle_eligibility_source = None
        latest_proactive_lifecycle_candidate_key = None
        latest_proactive_lifecycle_candidate_status = None
        latest_proactive_lifecycle_candidate_mode = None
        latest_proactive_lifecycle_candidate_decision = None
        latest_proactive_lifecycle_candidate_actionability = None
        latest_proactive_lifecycle_candidate_active_stage_label = None
        latest_proactive_lifecycle_candidate_queue_override_status = None
        latest_proactive_lifecycle_candidate_source = None
        latest_proactive_lifecycle_selectability_key = None
        latest_proactive_lifecycle_selectability_status = None
        latest_proactive_lifecycle_selectability_mode = None
        latest_proactive_lifecycle_selectability_decision = None
        latest_proactive_lifecycle_selectability_actionability = None
        latest_proactive_lifecycle_selectability_active_stage_label = None
        latest_proactive_lifecycle_selectability_queue_override_status = None
        latest_proactive_lifecycle_selectability_source = None
        latest_proactive_lifecycle_reentry_key = None
        latest_proactive_lifecycle_reentry_status = None
        latest_proactive_lifecycle_reentry_mode = None
        latest_proactive_lifecycle_reentry_decision = None
        latest_proactive_lifecycle_reentry_actionability = None
        latest_proactive_lifecycle_reentry_active_stage_label = None
        latest_proactive_lifecycle_reentry_queue_override_status = None
        latest_proactive_lifecycle_reentry_source = None
        latest_proactive_lifecycle_reactivation_key = None
        latest_proactive_lifecycle_reactivation_status = None
        latest_proactive_lifecycle_reactivation_mode = None
        latest_proactive_lifecycle_reactivation_decision = None
        latest_proactive_lifecycle_reactivation_actionability = None
        latest_proactive_lifecycle_reactivation_active_stage_label = None
        latest_proactive_lifecycle_reactivation_queue_override_status = None
        latest_proactive_lifecycle_reactivation_source = None
        latest_proactive_lifecycle_resumption_key = None
        latest_proactive_lifecycle_resumption_status = None
        latest_proactive_lifecycle_resumption_mode = None
        latest_proactive_lifecycle_resumption_decision = None
        latest_proactive_lifecycle_resumption_actionability = None
        latest_proactive_lifecycle_resumption_active_stage_label = None
        latest_proactive_lifecycle_resumption_queue_override_status = None
        latest_proactive_lifecycle_resumption_source = None
        latest_proactive_lifecycle_readiness_key = None
        latest_proactive_lifecycle_readiness_status = None
        latest_proactive_lifecycle_readiness_mode = None
        latest_proactive_lifecycle_readiness_decision = None
        latest_proactive_lifecycle_readiness_actionability = None
        latest_proactive_lifecycle_readiness_active_stage_label = None
        latest_proactive_lifecycle_readiness_queue_override_status = None
        latest_proactive_lifecycle_readiness_source = None
        latest_proactive_lifecycle_arming_key = None
        latest_proactive_lifecycle_arming_status = None
        latest_proactive_lifecycle_arming_mode = None
        latest_proactive_lifecycle_arming_decision = None
        latest_proactive_lifecycle_arming_actionability = None
        latest_proactive_lifecycle_arming_active_stage_label = None
        latest_proactive_lifecycle_arming_queue_override_status = None
        latest_proactive_lifecycle_arming_source = None
        latest_proactive_lifecycle_trigger_key = None
        latest_proactive_lifecycle_trigger_status = None
        latest_proactive_lifecycle_trigger_mode = None
        latest_proactive_lifecycle_trigger_decision = None
        latest_proactive_lifecycle_trigger_actionability = None
        latest_proactive_lifecycle_trigger_active_stage_label = None
        latest_proactive_lifecycle_trigger_queue_override_status = None
        latest_proactive_lifecycle_trigger_source = None
        latest_proactive_lifecycle_launch_key = None
        latest_proactive_lifecycle_launch_status = None
        latest_proactive_lifecycle_launch_mode = None
        latest_proactive_lifecycle_launch_decision = None
        latest_proactive_lifecycle_launch_actionability = None
        latest_proactive_lifecycle_launch_active_stage_label = None
        latest_proactive_lifecycle_launch_queue_override_status = None
        latest_proactive_lifecycle_launch_source = None
        latest_proactive_lifecycle_handoff_key = None
        latest_proactive_lifecycle_handoff_status = None
        latest_proactive_lifecycle_handoff_mode = None
        latest_proactive_lifecycle_handoff_decision = None
        latest_proactive_lifecycle_handoff_actionability = None
        latest_proactive_lifecycle_handoff_active_stage_label = None
        latest_proactive_lifecycle_handoff_queue_override_status = None
        latest_proactive_lifecycle_handoff_source = None
        latest_proactive_lifecycle_continuation_key = None
        latest_proactive_lifecycle_continuation_status = None
        latest_proactive_lifecycle_continuation_mode = None
        latest_proactive_lifecycle_continuation_decision = None
        latest_proactive_lifecycle_continuation_actionability = None
        latest_proactive_lifecycle_continuation_active_stage_label = None
        latest_proactive_lifecycle_continuation_queue_override_status = None
        latest_proactive_lifecycle_continuation_source = None
        latest_proactive_lifecycle_sustainment_key = None
        latest_proactive_lifecycle_sustainment_status = None
        latest_proactive_lifecycle_sustainment_mode = None
        latest_proactive_lifecycle_sustainment_decision = None
        latest_proactive_lifecycle_sustainment_actionability = None
        latest_proactive_lifecycle_sustainment_active_stage_label = None
        latest_proactive_lifecycle_sustainment_queue_override_status = None
        latest_proactive_lifecycle_sustainment_source = None
        latest_proactive_lifecycle_stewardship_key = None
        latest_proactive_lifecycle_stewardship_status = None
        latest_proactive_lifecycle_stewardship_mode = None
        latest_proactive_lifecycle_stewardship_decision = None
        latest_proactive_lifecycle_stewardship_actionability = None
        latest_proactive_lifecycle_stewardship_active_stage_label = None
        latest_proactive_lifecycle_stewardship_queue_override_status = None
        latest_proactive_lifecycle_stewardship_source = None
        latest_proactive_lifecycle_guardianship_key = None
        latest_proactive_lifecycle_guardianship_status = None
        latest_proactive_lifecycle_guardianship_mode = None
        latest_proactive_lifecycle_guardianship_decision = None
        latest_proactive_lifecycle_guardianship_actionability = None
        latest_proactive_lifecycle_guardianship_active_stage_label = None
        latest_proactive_lifecycle_guardianship_queue_override_status = None
        latest_proactive_lifecycle_guardianship_source = None
        latest_proactive_lifecycle_oversight_key = None
        latest_proactive_lifecycle_oversight_status = None
        latest_proactive_lifecycle_oversight_mode = None
        latest_proactive_lifecycle_oversight_decision = None
        latest_proactive_lifecycle_oversight_actionability = None
        latest_proactive_lifecycle_oversight_active_stage_label = None
        latest_proactive_lifecycle_oversight_queue_override_status = None
        latest_proactive_lifecycle_oversight_source = None
        latest_proactive_lifecycle_assurance_key = None
        latest_proactive_lifecycle_assurance_status = None
        latest_proactive_lifecycle_assurance_mode = None
        latest_proactive_lifecycle_assurance_decision = None
        latest_proactive_lifecycle_assurance_actionability = None
        latest_proactive_lifecycle_assurance_active_stage_label = None
        latest_proactive_lifecycle_assurance_queue_override_status = None
        latest_proactive_lifecycle_assurance_source = None
        latest_proactive_lifecycle_attestation_key = None
        latest_proactive_lifecycle_attestation_status = None
        latest_proactive_lifecycle_attestation_mode = None
        latest_proactive_lifecycle_attestation_decision = None
        latest_proactive_lifecycle_attestation_actionability = None
        latest_proactive_lifecycle_attestation_active_stage_label = None
        latest_proactive_lifecycle_attestation_queue_override_status = None
        latest_proactive_lifecycle_attestation_source = None
        latest_proactive_lifecycle_verification_key = None
        latest_proactive_lifecycle_verification_status = None
        latest_proactive_lifecycle_verification_mode = None
        latest_proactive_lifecycle_verification_decision = None
        latest_proactive_lifecycle_verification_actionability = None
        latest_proactive_lifecycle_verification_active_stage_label = None
        latest_proactive_lifecycle_verification_queue_override_status = None
        latest_proactive_lifecycle_verification_source = None
        latest_proactive_lifecycle_certification_key = None
        latest_proactive_lifecycle_certification_status = None
        latest_proactive_lifecycle_certification_mode = None
        latest_proactive_lifecycle_certification_decision = None
        latest_proactive_lifecycle_certification_actionability = None
        latest_proactive_lifecycle_certification_active_stage_label = None
        latest_proactive_lifecycle_certification_queue_override_status = None
        latest_proactive_lifecycle_certification_source = None
        latest_proactive_lifecycle_confirmation_key = None
        latest_proactive_lifecycle_confirmation_status = None
        latest_proactive_lifecycle_confirmation_mode = None
        latest_proactive_lifecycle_confirmation_decision = None
        latest_proactive_lifecycle_confirmation_actionability = None
        latest_proactive_lifecycle_confirmation_active_stage_label = None
        latest_proactive_lifecycle_confirmation_queue_override_status = None
        latest_proactive_lifecycle_confirmation_source = None
        latest_proactive_lifecycle_ratification_key = None
        latest_proactive_lifecycle_ratification_status = None
        latest_proactive_lifecycle_ratification_mode = None
        latest_proactive_lifecycle_ratification_decision = None
        latest_proactive_lifecycle_ratification_actionability = None
        latest_proactive_lifecycle_ratification_active_stage_label = None
        latest_proactive_lifecycle_ratification_queue_override_status = None
        latest_proactive_lifecycle_ratification_source = None
        latest_proactive_lifecycle_endorsement_key = None
        latest_proactive_lifecycle_endorsement_status = None
        latest_proactive_lifecycle_endorsement_mode = None
        latest_proactive_lifecycle_endorsement_decision = None
        latest_proactive_lifecycle_endorsement_actionability = None
        latest_proactive_lifecycle_endorsement_active_stage_label = None
        latest_proactive_lifecycle_endorsement_queue_override_status = None
        latest_proactive_lifecycle_endorsement_source = None
        latest_proactive_lifecycle_authorization_key = None
        latest_proactive_lifecycle_authorization_status = None
        latest_proactive_lifecycle_authorization_mode = None
        latest_proactive_lifecycle_authorization_decision = None
        latest_proactive_lifecycle_authorization_actionability = None
        latest_proactive_lifecycle_authorization_active_stage_label = None
        latest_proactive_lifecycle_authorization_queue_override_status = None
        latest_proactive_lifecycle_authorization_source = None
        latest_proactive_lifecycle_enactment_key = None
        latest_proactive_lifecycle_enactment_status = None
        latest_proactive_lifecycle_enactment_mode = None
        latest_proactive_lifecycle_enactment_decision = None
        latest_proactive_lifecycle_enactment_actionability = None
        latest_proactive_lifecycle_enactment_active_stage_label = None
        latest_proactive_lifecycle_enactment_queue_override_status = None
        latest_proactive_lifecycle_enactment_source = None
        latest_proactive_lifecycle_finality_key = None
        latest_proactive_lifecycle_finality_status = None
        latest_proactive_lifecycle_finality_mode = None
        latest_proactive_lifecycle_finality_decision = None
        latest_proactive_lifecycle_finality_actionability = None
        latest_proactive_lifecycle_finality_active_stage_label = None
        latest_proactive_lifecycle_finality_queue_override_status = None
        latest_proactive_lifecycle_finality_source = None
        latest_proactive_lifecycle_completion_key = None
        latest_proactive_lifecycle_completion_status = None
        latest_proactive_lifecycle_completion_mode = None
        latest_proactive_lifecycle_completion_decision = None
        latest_proactive_lifecycle_completion_actionability = None
        latest_proactive_lifecycle_completion_active_stage_label = None
        latest_proactive_lifecycle_completion_queue_override_status = None
        latest_proactive_lifecycle_completion_source = None
        latest_proactive_lifecycle_conclusion_key = None
        latest_proactive_lifecycle_conclusion_status = None
        latest_proactive_lifecycle_conclusion_mode = None
        latest_proactive_lifecycle_conclusion_decision = None
        latest_proactive_lifecycle_conclusion_actionability = None
        latest_proactive_lifecycle_conclusion_active_stage_label = None
        latest_proactive_lifecycle_conclusion_queue_override_status = None
        latest_proactive_lifecycle_conclusion_source = None
        latest_proactive_lifecycle_disposition_key = None
        latest_proactive_lifecycle_disposition_status = None
        latest_proactive_lifecycle_disposition_mode = None
        latest_proactive_lifecycle_disposition_decision = None
        latest_proactive_lifecycle_disposition_actionability = None
        latest_proactive_lifecycle_disposition_active_stage_label = None
        latest_proactive_lifecycle_disposition_queue_override_status = None
        latest_proactive_lifecycle_disposition_source = None
        latest_proactive_lifecycle_standing_key = None
        latest_proactive_lifecycle_standing_status = None
        latest_proactive_lifecycle_standing_mode = None
        latest_proactive_lifecycle_standing_decision = None
        latest_proactive_lifecycle_standing_actionability = None
        latest_proactive_lifecycle_standing_active_stage_label = None
        latest_proactive_lifecycle_standing_queue_override_status = None
        latest_proactive_lifecycle_standing_source = None
        latest_proactive_lifecycle_residency_key = None
        latest_proactive_lifecycle_residency_status = None
        latest_proactive_lifecycle_residency_mode = None
        latest_proactive_lifecycle_residency_decision = None
        latest_proactive_lifecycle_residency_actionability = None
        latest_proactive_lifecycle_residency_active_stage_label = None
        latest_proactive_lifecycle_residency_queue_override_status = None
        latest_proactive_lifecycle_residency_source = None
        latest_proactive_lifecycle_tenure_key = None
        latest_proactive_lifecycle_tenure_status = None
        latest_proactive_lifecycle_tenure_mode = None
        latest_proactive_lifecycle_tenure_decision = None
        latest_proactive_lifecycle_tenure_actionability = None
        latest_proactive_lifecycle_tenure_active_stage_label = None
        latest_proactive_lifecycle_tenure_queue_override_status = None
        latest_proactive_lifecycle_tenure_source = None
        latest_proactive_lifecycle_persistence_key = None
        latest_proactive_lifecycle_persistence_status = None
        latest_proactive_lifecycle_persistence_mode = None
        latest_proactive_lifecycle_persistence_decision = None
        latest_proactive_lifecycle_persistence_actionability = None
        latest_proactive_lifecycle_persistence_active_stage_label = None
        latest_proactive_lifecycle_persistence_queue_override_status = None
        latest_proactive_lifecycle_persistence_source = None
        latest_proactive_lifecycle_longevity_key = None
        latest_proactive_lifecycle_longevity_status = None
        latest_proactive_lifecycle_longevity_mode = None
        latest_proactive_lifecycle_longevity_decision = None
        latest_proactive_lifecycle_longevity_actionability = None
        latest_proactive_lifecycle_longevity_active_stage_label = None
        latest_proactive_lifecycle_longevity_queue_override_status = None
        latest_proactive_lifecycle_longevity_source = None
        latest_proactive_lifecycle_legacy_key = None
        latest_proactive_lifecycle_legacy_status = None
        latest_proactive_lifecycle_legacy_mode = None
        latest_proactive_lifecycle_legacy_decision = None
        latest_proactive_lifecycle_legacy_actionability = None
        latest_proactive_lifecycle_legacy_active_stage_label = None
        latest_proactive_lifecycle_legacy_queue_override_status = None
        latest_proactive_lifecycle_legacy_source = None
        latest_proactive_lifecycle_heritage_key = None
        latest_proactive_lifecycle_heritage_status = None
        latest_proactive_lifecycle_heritage_mode = None
        latest_proactive_lifecycle_heritage_decision = None
        latest_proactive_lifecycle_heritage_actionability = None
        latest_proactive_lifecycle_heritage_active_stage_label = None
        latest_proactive_lifecycle_heritage_queue_override_status = None
        latest_proactive_lifecycle_heritage_source = None
        latest_proactive_lifecycle_lineage_key = None
        latest_proactive_lifecycle_lineage_status = None
        latest_proactive_lifecycle_lineage_mode = None
        latest_proactive_lifecycle_lineage_decision = None
        latest_proactive_lifecycle_lineage_actionability = None
        latest_proactive_lifecycle_lineage_active_stage_label = None
        latest_proactive_lifecycle_lineage_queue_override_status = None
        latest_proactive_lifecycle_lineage_source = None
        latest_proactive_lifecycle_ancestry_key = None
        latest_proactive_lifecycle_ancestry_status = None
        latest_proactive_lifecycle_ancestry_mode = None
        latest_proactive_lifecycle_ancestry_decision = None
        latest_proactive_lifecycle_ancestry_actionability = None
        latest_proactive_lifecycle_ancestry_active_stage_label = None
        latest_proactive_lifecycle_ancestry_queue_override_status = None
        latest_proactive_lifecycle_ancestry_source = None
        latest_proactive_lifecycle_provenance_key = None
        latest_proactive_lifecycle_provenance_status = None
        latest_proactive_lifecycle_provenance_mode = None
        latest_proactive_lifecycle_provenance_decision = None
        latest_proactive_lifecycle_provenance_actionability = None
        latest_proactive_lifecycle_provenance_active_stage_label = None
        latest_proactive_lifecycle_provenance_queue_override_status = None
        latest_proactive_lifecycle_provenance_source = None
        latest_proactive_lifecycle_origin_key = None
        latest_proactive_lifecycle_origin_status = None
        latest_proactive_lifecycle_origin_mode = None
        latest_proactive_lifecycle_origin_decision = None
        latest_proactive_lifecycle_origin_actionability = None
        latest_proactive_lifecycle_origin_active_stage_label = None
        latest_proactive_lifecycle_origin_queue_override_status = None
        latest_proactive_lifecycle_origin_source = None
        latest_proactive_lifecycle_root_key = None
        latest_proactive_lifecycle_root_status = None
        latest_proactive_lifecycle_root_mode = None
        latest_proactive_lifecycle_root_decision = None
        latest_proactive_lifecycle_root_actionability = None
        latest_proactive_lifecycle_root_active_stage_label = None
        latest_proactive_lifecycle_root_queue_override_status = None
        latest_proactive_lifecycle_root_source = None
        latest_proactive_lifecycle_foundation_key = None
        latest_proactive_lifecycle_foundation_status = None
        latest_proactive_lifecycle_foundation_mode = None
        latest_proactive_lifecycle_foundation_decision = None
        latest_proactive_lifecycle_foundation_actionability = None
        latest_proactive_lifecycle_foundation_active_stage_label = None
        latest_proactive_lifecycle_foundation_queue_override_status = None
        latest_proactive_lifecycle_foundation_source = None
        latest_proactive_lifecycle_bedrock_key = None
        latest_proactive_lifecycle_bedrock_status = None
        latest_proactive_lifecycle_bedrock_mode = None
        latest_proactive_lifecycle_bedrock_decision = None
        latest_proactive_lifecycle_bedrock_actionability = None
        latest_proactive_lifecycle_bedrock_active_stage_label = None
        latest_proactive_lifecycle_bedrock_queue_override_status = None
        latest_proactive_lifecycle_bedrock_source = None
        latest_proactive_lifecycle_substrate_key = None
        latest_proactive_lifecycle_substrate_status = None
        latest_proactive_lifecycle_substrate_mode = None
        latest_proactive_lifecycle_substrate_decision = None
        latest_proactive_lifecycle_substrate_actionability = None
        latest_proactive_lifecycle_substrate_active_stage_label = None
        latest_proactive_lifecycle_substrate_queue_override_status = None
        latest_proactive_lifecycle_substrate_source = None
        latest_proactive_lifecycle_stratum_key = None
        latest_proactive_lifecycle_stratum_status = None
        latest_proactive_lifecycle_stratum_mode = None
        latest_proactive_lifecycle_stratum_decision = None
        latest_proactive_lifecycle_stratum_actionability = None
        latest_proactive_lifecycle_stratum_active_stage_label = None
        latest_proactive_lifecycle_stratum_queue_override_status = None
        latest_proactive_lifecycle_stratum_source = None
        latest_proactive_lifecycle_layer_key = None
        latest_proactive_lifecycle_layer_status = None
        latest_proactive_lifecycle_layer_mode = None
        latest_proactive_lifecycle_layer_decision = None
        latest_proactive_lifecycle_layer_actionability = None
        latest_proactive_lifecycle_layer_active_stage_label = None
        latest_proactive_lifecycle_layer_queue_override_status = None
        latest_proactive_lifecycle_layer_source = None
        latest_proactive_lifecycle_durability_key = None
        latest_proactive_lifecycle_durability_status = None
        latest_proactive_lifecycle_durability_mode = None
        latest_proactive_lifecycle_durability_decision = None
        latest_proactive_lifecycle_durability_actionability = None
        latest_proactive_lifecycle_durability_active_stage_label = None
        latest_proactive_lifecycle_durability_queue_override_status = None
        latest_proactive_lifecycle_durability_source = None
        latest_proactive_stage_refresh_key = None
        latest_proactive_stage_refresh_window_status = None
        latest_proactive_stage_refresh_stage_label = None
        latest_proactive_stage_refresh_changed = False
        latest_proactive_stage_refresh_delivery_mode = None
        latest_proactive_stage_refresh_user_space_signal = None
        latest_proactive_stage_replan_key = None
        latest_proactive_stage_replan_strategy_key = None
        latest_proactive_stage_replan_ritual_mode = None
        latest_proactive_stage_replan_pressure_mode = None
        latest_proactive_stage_replan_autonomy_signal = None
        latest_proactive_stage_replan_changed = False
        latest_proactive_dispatch_feedback_key = None
        latest_proactive_dispatch_feedback_strategy_key = None
        latest_proactive_dispatch_feedback_pressure_mode = None
        latest_proactive_dispatch_feedback_autonomy_signal = None
        latest_proactive_dispatch_feedback_delivery_mode = None
        latest_proactive_dispatch_feedback_sequence_objective = None
        latest_proactive_dispatch_feedback_prior_stage_label = None
        latest_proactive_dispatch_feedback_changed = False
        latest_proactive_dispatch_gate_key = None
        latest_proactive_dispatch_gate_decision = None
        latest_proactive_dispatch_gate_retry_after_seconds = 0
        latest_proactive_dispatch_gate_strategy_key = None
        latest_proactive_dispatch_gate_changed = False
        latest_proactive_dispatch_envelope_key = None
        latest_proactive_dispatch_envelope_decision = None
        latest_proactive_dispatch_envelope_strategy_key = None
        latest_proactive_dispatch_envelope_stage_delivery_mode = None
        latest_proactive_dispatch_envelope_reengagement_delivery_mode = None
        latest_proactive_dispatch_envelope_source_count = 0
        latest_proactive_stage_state_key = None
        latest_proactive_stage_state_mode = None
        latest_proactive_stage_state_queue_status = None
        latest_proactive_stage_state_source = None
        latest_proactive_stage_transition_key = None
        latest_proactive_stage_transition_mode = None
        latest_proactive_stage_transition_queue_hint = None
        latest_proactive_stage_transition_source = None
        latest_proactive_stage_machine_key = None
        latest_proactive_stage_machine_mode = None
        latest_proactive_stage_machine_lifecycle = None
        latest_proactive_stage_machine_actionability = None
        latest_proactive_stage_machine_source = None
        latest_reengagement_matrix_key = None
        latest_reengagement_matrix_selected_strategy = None
        latest_reengagement_matrix_selected_score = None
        latest_reengagement_matrix_top_alternative = None
        latest_reengagement_matrix_blocked_count = 0
        latest_reengagement_matrix_learning_mode = None
        latest_reengagement_matrix_learning_context_stratum = None
        latest_reengagement_matrix_learning_signal_count = 0
        latest_reengagement_matrix_selected_supporting_session_count = 0
        latest_reengagement_matrix_selected_contextual_supporting_session_count = 0
        latest_reengagement_ritual_mode = None
        latest_reengagement_delivery_mode = None
        latest_reengagement_strategy_key = None
        latest_reengagement_relational_move = None
        latest_reengagement_pressure_mode = None
        latest_reengagement_autonomy_signal = None
        latest_reengagement_sequence_objective = None
        latest_reengagement_somatic_action = None
        latest_proactive_followup_dispatch_status = None
        latest_proactive_followup_dispatch_source = None
        latest_proactive_followup_dispatched_at = None
        latest_proactive_followup_dispatch_stage_index = 0
        latest_proactive_followup_dispatch_stage_label = None
        latest_proactive_followup_dispatch_remaining = 0
        latest_proactive_followup_dispatch_progression_action = None
        latest_proactive_followup_dispatch_progression_advanced = False
        latest_runtime_quality_doctor_status = None
        latest_runtime_quality_doctor_issue_count = 0
        latest_system3_identity_consistency = None
        latest_system3_identity_anchor = None
        latest_system3_identity_trajectory_status = None
        latest_system3_identity_trajectory_target = None
        latest_system3_identity_trajectory_trigger = None
        latest_system3_growth_stage = None
        latest_system3_user_model_confidence = None
        latest_system3_emotional_debt_status = None
        latest_system3_emotional_debt_score = None
        latest_system3_emotional_debt_trajectory_status = None
        latest_system3_emotional_debt_trajectory_target = None
        latest_system3_emotional_debt_trajectory_trigger = None
        latest_system3_strategy_audit_status = None
        latest_system3_strategy_audit_trajectory_status = None
        latest_system3_strategy_audit_trajectory_target = None
        latest_system3_strategy_audit_trajectory_trigger = None
        latest_system3_strategy_fit = None
        latest_system3_strategy_supervision_status = None
        latest_system3_strategy_supervision_mode = None
        latest_system3_strategy_supervision_trigger = None
        latest_system3_strategy_supervision_trajectory_status = None
        latest_system3_strategy_supervision_trajectory_target = None
        latest_system3_strategy_supervision_trajectory_trigger = None
        latest_system3_moral_reasoning_status = None
        latest_system3_moral_posture = None
        latest_system3_moral_conflict = None
        latest_system3_moral_trajectory_status = None
        latest_system3_moral_trajectory_target = None
        latest_system3_moral_trajectory_trigger = None
        latest_system3_user_model_evolution_status = None
        latest_system3_user_model_revision_mode = None
        latest_system3_user_model_shift_signal = None
        latest_system3_user_model_trajectory_status = None
        latest_system3_user_model_trajectory_target = None
        latest_system3_user_model_trajectory_trigger = None
        latest_system3_expectation_calibration_status = None
        latest_system3_expectation_calibration_target = None
        latest_system3_expectation_calibration_trigger = None
        latest_system3_expectation_calibration_trajectory_status = None
        latest_system3_expectation_calibration_trajectory_target = None
        latest_system3_expectation_calibration_trajectory_trigger = None
        latest_system3_dependency_governance_status = None
        latest_system3_dependency_governance_target = None
        latest_system3_dependency_governance_trigger = None
        latest_system3_dependency_governance_trajectory_status = None
        latest_system3_dependency_governance_trajectory_target = None
        latest_system3_dependency_governance_trajectory_trigger = None
        latest_system3_autonomy_governance_status = None
        latest_system3_autonomy_governance_target = None
        latest_system3_autonomy_governance_trigger = None
        latest_system3_autonomy_governance_trajectory_status = None
        latest_system3_autonomy_governance_trajectory_target = None
        latest_system3_autonomy_governance_trajectory_trigger = None
        latest_system3_boundary_governance_status = None
        latest_system3_boundary_governance_target = None
        latest_system3_boundary_governance_trigger = None
        latest_system3_boundary_governance_trajectory_status = None
        latest_system3_boundary_governance_trajectory_target = None
        latest_system3_boundary_governance_trajectory_trigger = None
        latest_system3_support_governance_status = None
        latest_system3_support_governance_target = None
        latest_system3_support_governance_trigger = None
        latest_system3_support_governance_trajectory_status = None
        latest_system3_support_governance_trajectory_target = None
        latest_system3_support_governance_trajectory_trigger = None
        latest_system3_continuity_governance_status = None
        latest_system3_continuity_governance_target = None
        latest_system3_continuity_governance_trigger = None
        latest_system3_continuity_governance_trajectory_status = None
        latest_system3_continuity_governance_trajectory_target = None
        latest_system3_continuity_governance_trajectory_trigger = None
        latest_system3_repair_governance_status = None
        latest_system3_repair_governance_target = None
        latest_system3_repair_governance_trigger = None
        latest_system3_repair_governance_trajectory_status = None
        latest_system3_repair_governance_trajectory_target = None
        latest_system3_repair_governance_trajectory_trigger = None
        latest_system3_attunement_governance_status = None
        latest_system3_attunement_governance_target = None
        latest_system3_attunement_governance_trigger = None
        latest_system3_attunement_governance_trajectory_status = None
        latest_system3_attunement_governance_trajectory_target = None
        latest_system3_attunement_governance_trajectory_trigger = None
        latest_system3_trust_governance_status = None
        latest_system3_trust_governance_target = None
        latest_system3_trust_governance_trigger = None
        latest_system3_trust_governance_trajectory_status = None
        latest_system3_trust_governance_trajectory_target = None
        latest_system3_trust_governance_trajectory_trigger = None
        latest_system3_clarity_governance_status = None
        latest_system3_clarity_governance_target = None
        latest_system3_clarity_governance_trigger = None
        latest_system3_clarity_governance_trajectory_status = None
        latest_system3_clarity_governance_trajectory_target = None
        latest_system3_clarity_governance_trajectory_trigger = None
        latest_system3_pacing_governance_status = None
        latest_system3_pacing_governance_target = None
        latest_system3_pacing_governance_trigger = None
        latest_system3_pacing_governance_trajectory_status = None
        latest_system3_pacing_governance_trajectory_target = None
        latest_system3_pacing_governance_trajectory_trigger = None
        latest_system3_commitment_governance_status = None
        latest_system3_commitment_governance_target = None
        latest_system3_commitment_governance_trigger = None
        latest_system3_commitment_governance_trajectory_status = None
        latest_system3_commitment_governance_trajectory_target = None
        latest_system3_commitment_governance_trajectory_trigger = None
        latest_system3_disclosure_governance_status = None
        latest_system3_disclosure_governance_target = None
        latest_system3_disclosure_governance_trigger = None
        latest_system3_disclosure_governance_trajectory_status = None
        latest_system3_disclosure_governance_trajectory_target = None
        latest_system3_disclosure_governance_trajectory_trigger = None
        latest_system3_reciprocity_governance_status = None
        latest_system3_reciprocity_governance_target = None
        latest_system3_reciprocity_governance_trigger = None
        latest_system3_reciprocity_governance_trajectory_status = None
        latest_system3_reciprocity_governance_trajectory_target = None
        latest_system3_reciprocity_governance_trajectory_trigger = None
        latest_system3_pressure_governance_status = None
        latest_system3_pressure_governance_target = None
        latest_system3_pressure_governance_trigger = None
        latest_system3_pressure_governance_trajectory_status = None
        latest_system3_pressure_governance_trajectory_target = None
        latest_system3_pressure_governance_trajectory_trigger = None
        latest_system3_relational_governance_status = None
        latest_system3_relational_governance_target = None
        latest_system3_relational_governance_trigger = None
        latest_system3_relational_governance_trajectory_status = None
        latest_system3_relational_governance_trajectory_target = None
        latest_system3_relational_governance_trajectory_trigger = None
        latest_system3_safety_governance_status = None
        latest_system3_safety_governance_target = None
        latest_system3_safety_governance_trigger = None
        latest_system3_safety_governance_trajectory_status = None
        latest_system3_safety_governance_trajectory_target = None
        latest_system3_safety_governance_trajectory_trigger = None
        latest_system3_progress_governance_status = None
        latest_system3_progress_governance_target = None
        latest_system3_progress_governance_trigger = None
        latest_system3_progress_governance_trajectory_status = None
        latest_system3_progress_governance_trajectory_target = None
        latest_system3_progress_governance_trajectory_trigger = None
        latest_system3_stability_governance_status = None
        latest_system3_stability_governance_target = None
        latest_system3_stability_governance_trigger = None
        latest_system3_stability_governance_trajectory_status = None
        latest_system3_stability_governance_trajectory_target = None
        latest_system3_stability_governance_trajectory_trigger = None
        latest_system3_growth_transition_status = None
        latest_system3_growth_transition_target = None
        latest_system3_growth_transition_trigger = None
        latest_system3_growth_transition_readiness = None
        latest_system3_growth_transition_trajectory_status = None
        latest_system3_growth_transition_trajectory_target = None
        latest_system3_growth_transition_trajectory_trigger = None
        latest_system3_version_migration_status = None
        latest_system3_version_migration_scope = None
        latest_system3_version_migration_trigger = None
        latest_system3_version_migration_trajectory_status = None
        latest_system3_version_migration_trajectory_target = None
        latest_system3_version_migration_trajectory_trigger = None
        latest_response_post_audit_status = None
        latest_response_normalization_final_status = None
        latest_memory_items = 0
        latest_memory_recall_count = 0
        latest_memory_filtered_count = 0
        latest_memory_blocked_count = 0
        latest_memory_pinned_count = 0
        latest_memory_evicted_count = 0
        quality_samples = self._build_output_quality_samples(turn_records)
        quality_summary = self._build_output_quality_summary(quality_samples)
        strategy_diversity_index = _distribution_entropy(strategy_names)
        if last_turn is not None:
            latest_strategy = (
                (last_turn.strategy_decision or {}).get("strategy")
                or (last_turn.session_directive or {}).get("next_action")
            )
            latest_strategy_source = (
                (last_turn.strategy_decision or {}).get("source_strategy")
                or latest_strategy
            )
            latest_strategy_diversity_status = (
                last_turn.strategy_decision or {}
            ).get("diversity_status")
            latest_strategy_diversity_entropy = float(
                (last_turn.strategy_decision or {}).get("diversity_entropy", 0.0)
            )
            latest_confidence_level = (
                last_turn.confidence_assessment or {}
            ).get("level")
            latest_confidence_response_mode = (
                last_turn.confidence_assessment or {}
            ).get("response_mode")
            latest_turbulence_risk = (last_turn.relationship_state or {}).get("turbulence_risk")
            latest_boundary_decision = (
                last_turn.knowledge_boundary_decision or {}
            ).get("decision")
            latest_policy_path = (last_turn.policy_gate or {}).get("selected_path")
            latest_rehearsal_risk = (
                last_turn.rehearsal_result or {}
            ).get("projected_risk_level")
            latest_empowerment_audit_status = (
                last_turn.empowerment_audit or {}
            ).get("status")
            latest_drafting_question_strategy = (
                last_turn.response_draft_plan or {}
            ).get("question_strategy")
            latest_drafting_opening_move = (
                last_turn.response_draft_plan or {}
            ).get("opening_move")
            latest_rendering_mode = (
                last_turn.response_rendering_policy or {}
            ).get("rendering_mode")
            latest_rendering_max_sentences = (
                last_turn.response_rendering_policy or {}
            ).get("max_sentences")
            latest_response_sequence_mode = (
                last_turn.response_sequence_plan or {}
            ).get("mode")
            latest_response_sequence_unit_count = int(
                (last_turn.response_sequence_plan or {}).get(
                    "unit_count",
                    last_turn.assistant_message_event_count,
                )
                or 0
            )
            latest_time_awareness_mode = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("time_awareness_mode")
            latest_ritual_phase = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("ritual_phase")
            latest_cognitive_load_band = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("cognitive_load_band")
            latest_guidance_mode = (last_turn.guidance_plan or {}).get("mode")
            latest_guidance_lead_with = (
                last_turn.guidance_plan or {}
            ).get("lead_with")
            latest_guidance_pacing = (last_turn.guidance_plan or {}).get("pacing")
            latest_guidance_step_budget = (
                last_turn.guidance_plan or {}
            ).get("step_budget")
            latest_guidance_agency_mode = (
                last_turn.guidance_plan or {}
            ).get("agency_mode")
            latest_guidance_ritual_action = (
                last_turn.guidance_plan or {}
            ).get("ritual_action")
            latest_guidance_checkpoint_style = (
                last_turn.guidance_plan or {}
            ).get("checkpoint_style")
            latest_guidance_handoff_mode = (
                last_turn.guidance_plan or {}
            ).get("handoff_mode")
            latest_guidance_carryover_mode = (
                last_turn.guidance_plan or {}
            ).get("carryover_mode")
            latest_cadence_status = (
                last_turn.conversation_cadence_plan or {}
            ).get("status")
            latest_cadence_turn_shape = (
                last_turn.conversation_cadence_plan or {}
            ).get("turn_shape")
            latest_cadence_ritual_depth = (
                last_turn.conversation_cadence_plan or {}
            ).get("ritual_depth")
            latest_cadence_followup_tempo = (
                last_turn.conversation_cadence_plan or {}
            ).get("followup_tempo")
            latest_cadence_user_space_mode = (
                last_turn.conversation_cadence_plan or {}
            ).get("user_space_mode")
            latest_cadence_transition_intent = (
                last_turn.conversation_cadence_plan or {}
            ).get("transition_intent")
            latest_cadence_next_checkpoint = (
                last_turn.conversation_cadence_plan or {}
            ).get("next_checkpoint")
            latest_session_ritual_phase = (
                last_turn.session_ritual_plan or {}
            ).get("phase")
            latest_session_ritual_opening_move = (
                last_turn.session_ritual_plan or {}
            ).get("opening_move")
            latest_session_ritual_bridge_move = (
                last_turn.session_ritual_plan or {}
            ).get("bridge_move")
            latest_session_ritual_closing_move = (
                last_turn.session_ritual_plan or {}
            ).get("closing_move")
            latest_session_ritual_continuity_anchor = (
                last_turn.session_ritual_plan or {}
            ).get("continuity_anchor")
            latest_session_ritual_somatic_shortcut = (
                last_turn.session_ritual_plan or {}
            ).get("somatic_shortcut")
            latest_somatic_orchestration_status = (
                last_turn.somatic_orchestration_plan or {}
            ).get("status")
            latest_somatic_orchestration_mode = (
                last_turn.somatic_orchestration_plan or {}
            ).get("primary_mode")
            latest_somatic_orchestration_body_anchor = (
                last_turn.somatic_orchestration_plan or {}
            ).get("body_anchor")
            latest_somatic_orchestration_followup_style = (
                last_turn.somatic_orchestration_plan or {}
            ).get("followup_style")
            latest_response_budget_mode = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("response_budget_mode")
            latest_proactive_followup_eligible = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("proactive_followup_eligible")
            latest_proactive_style = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("proactive_style")
            latest_somatic_cue = (
                last_turn.runtime_coordination_snapshot or {}
            ).get("somatic_cue")
            latest_proactive_followup_status = (
                last_turn.proactive_followup_directive or {}
            ).get("status")
            latest_proactive_followup_style = (
                last_turn.proactive_followup_directive or {}
            ).get("style")
            latest_proactive_followup_after_seconds = (
                last_turn.proactive_followup_directive or {}
            ).get("trigger_after_seconds")
            latest_proactive_cadence_status = (
                last_turn.proactive_cadence_plan or {}
            ).get("status")
            latest_proactive_cadence_key = (
                last_turn.proactive_cadence_plan or {}
            ).get("cadence_key")
            latest_proactive_cadence_stage_count = int(
                (last_turn.proactive_cadence_plan or {}).get(
                    "close_after_stage_index",
                    0,
                )
                or 0
            )
            latest_proactive_aggregate_governance_status = (
                last_turn.proactive_aggregate_governance_assessment or {}
            ).get("status")
            latest_proactive_aggregate_governance_primary_domain = (
                last_turn.proactive_aggregate_governance_assessment or {}
            ).get("primary_domain")
            latest_proactive_aggregate_governance_summary = (
                last_turn.proactive_aggregate_governance_assessment or {}
            ).get("summary")
            latest_proactive_aggregate_governance_domain_count = int(
                (last_turn.proactive_aggregate_governance_assessment or {}).get(
                    "domain_count",
                    0,
                )
                or 0
            )
            latest_proactive_aggregate_controller_key = (
                last_turn.proactive_aggregate_controller_decision or {}
            ).get("controller_key")
            latest_proactive_aggregate_controller_decision = (
                last_turn.proactive_aggregate_controller_decision or {}
            ).get("decision")
            latest_proactive_aggregate_controller_stage_delay_seconds = int(
                (last_turn.proactive_aggregate_controller_decision or {}).get(
                    "stage_additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_aggregate_controller_line_delay_seconds = int(
                (last_turn.proactive_aggregate_controller_decision or {}).get(
                    "line_additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_aggregate_controller_retry_after_seconds = int(
                (last_turn.proactive_aggregate_controller_decision or {}).get(
                    "dispatch_retry_after_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_orchestration_controller_key = (
                last_turn.proactive_orchestration_controller_decision or {}
            ).get("controller_key")
            latest_proactive_orchestration_controller_decision = (
                last_turn.proactive_orchestration_controller_decision or {}
            ).get("decision")
            latest_proactive_orchestration_controller_stage_delay_seconds = int(
                (last_turn.proactive_orchestration_controller_decision or {}).get(
                    "stage_additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_orchestration_controller_line_delay_seconds = int(
                (last_turn.proactive_orchestration_controller_decision or {}).get(
                    "line_additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_orchestration_controller_retry_after_seconds = int(
                (last_turn.proactive_orchestration_controller_decision or {}).get(
                    "dispatch_retry_after_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_orchestration_controller_primary_source = (
                last_turn.proactive_orchestration_controller_decision or {}
            ).get("primary_source")
            latest_proactive_guardrail_key = (
                last_turn.proactive_guardrail_plan or {}
            ).get("guardrail_key")
            latest_proactive_guardrail_max_dispatch_count = int(
                (last_turn.proactive_guardrail_plan or {}).get(
                    "max_dispatch_count",
                    0,
                )
                or 0
            )
            latest_proactive_guardrail_hard_stop_count = len(
                list(
                    (last_turn.proactive_guardrail_plan or {}).get(
                        "hard_stop_conditions",
                        [],
                    )
                )
            )
            second_touch_guardrail = next(
                (
                    guardrail
                    for guardrail in list(
                        (last_turn.proactive_guardrail_plan or {}).get(
                            "stage_guardrails",
                            [],
                        )
                    )
                    if str(guardrail.get("stage_label") or "") == "second_touch"
                ),
                {},
            )
            latest_proactive_guardrail_second_touch_min_user_seconds = int(
                second_touch_guardrail.get("min_seconds_since_last_user") or 0
            )
            latest_proactive_scheduling_mode = (
                last_turn.proactive_scheduling_plan or {}
            ).get("scheduler_mode")
            latest_proactive_scheduling_min_seconds_since_last_outbound = int(
                (last_turn.proactive_scheduling_plan or {}).get(
                    "min_seconds_since_last_outbound",
                    0,
                )
                or 0
            )
            latest_proactive_scheduling_first_touch_extra_delay_seconds = int(
                (last_turn.proactive_scheduling_plan or {}).get(
                    "first_touch_extra_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_orchestration_key = (
                last_turn.proactive_orchestration_plan or {}
            ).get("orchestration_key")
            latest_proactive_orchestration_close_loop_stage = (
                last_turn.proactive_orchestration_plan or {}
            ).get("close_loop_stage")
            second_touch_directive = next(
                (
                    directive
                    for directive in list(
                        (last_turn.proactive_orchestration_plan or {}).get(
                            "stage_directives",
                            [],
                        )
                    )
                    if str(directive.get("stage_label") or "") == "second_touch"
                ),
                {},
            )
            latest_proactive_orchestration_second_touch_delivery_mode = (
                second_touch_directive.get("delivery_mode")
            )
            latest_proactive_orchestration_second_touch_question_mode = (
                second_touch_directive.get("question_mode")
            )
            latest_proactive_actuation_key = (
                last_turn.proactive_actuation_plan or {}
            ).get("actuation_key")
            second_touch_actuation = next(
                (
                    actuation
                    for actuation in list(
                        (last_turn.proactive_actuation_plan or {}).get(
                            "stage_actuations",
                            [],
                        )
                    )
                    if str(actuation.get("stage_label") or "") == "second_touch"
                ),
                {},
            )
            final_touch_actuation = next(
                (
                    actuation
                    for actuation in list(
                        (last_turn.proactive_actuation_plan or {}).get(
                            "stage_actuations",
                            [],
                        )
                    )
                    if str(actuation.get("stage_label") or "") == "final_soft_close"
                ),
                {},
            )
            latest_proactive_actuation_second_touch_opening_move = (
                second_touch_actuation.get("opening_move")
            )
            latest_proactive_actuation_second_touch_bridge_move = (
                second_touch_actuation.get("bridge_move")
            )
            latest_proactive_actuation_second_touch_somatic_mode = (
                second_touch_actuation.get("somatic_mode")
            )
            latest_proactive_actuation_second_touch_user_space_signal = (
                second_touch_actuation.get("user_space_signal")
            )
            latest_proactive_actuation_final_touch_closing_move = (
                final_touch_actuation.get("closing_move")
            )
            latest_proactive_progression_key = (
                last_turn.proactive_progression_plan or {}
            ).get("progression_key")
            second_touch_progression = next(
                (
                    progression
                    for progression in list(
                        (last_turn.proactive_progression_plan or {}).get(
                            "stage_progressions",
                            [],
                        )
                    )
                    if str(progression.get("stage_label") or "") == "second_touch"
                ),
                {},
            )
            final_touch_progression = next(
                (
                    progression
                    for progression in list(
                        (last_turn.proactive_progression_plan or {}).get(
                            "stage_progressions",
                            [],
                        )
                    )
                    if str(progression.get("stage_label") or "") == "final_soft_close"
                ),
                {},
            )
            latest_proactive_progression_second_touch_action = (
                second_touch_progression.get("on_expired")
            )
            latest_proactive_progression_final_touch_action = (
                final_touch_progression.get("on_expired")
            )
            latest_proactive_stage_controller_key = (
                last_turn.proactive_stage_controller_decision or {}
            ).get("controller_key")
            latest_proactive_stage_controller_decision = (
                last_turn.proactive_stage_controller_decision or {}
            ).get("decision")
            latest_proactive_stage_controller_target_stage_label = (
                last_turn.proactive_stage_controller_decision or {}
            ).get("target_stage_label")
            latest_proactive_stage_controller_additional_delay_seconds = int(
                (last_turn.proactive_stage_controller_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_stage_controller_strategy_key = (
                last_turn.proactive_stage_controller_decision or {}
            ).get("selected_strategy_key")
            latest_proactive_stage_controller_changed = bool(
                (last_turn.proactive_stage_controller_decision or {}).get("changed")
            )
            latest_proactive_line_controller_key = (
                last_turn.proactive_line_controller_decision or {}
            ).get("controller_key")
            latest_proactive_line_controller_decision = (
                last_turn.proactive_line_controller_decision or {}
            ).get("decision")
            latest_proactive_line_controller_line_state = (
                last_turn.proactive_line_controller_decision or {}
            ).get("line_state")
            latest_proactive_line_controller_additional_delay_seconds = int(
                (last_turn.proactive_line_controller_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_line_controller_changed = bool(
                (last_turn.proactive_line_controller_decision or {}).get("changed")
            )
            latest_proactive_line_state_key = (
                last_turn.proactive_line_state_decision or {}
            ).get("line_key")
            latest_proactive_line_state_mode = (
                last_turn.proactive_line_state_decision or {}
            ).get("line_state")
            latest_proactive_line_state_lifecycle = (
                last_turn.proactive_line_state_decision or {}
            ).get("lifecycle_mode")
            latest_proactive_line_state_actionability = (
                last_turn.proactive_line_state_decision or {}
            ).get("actionability")
            latest_proactive_line_state_source = (
                last_turn.proactive_line_state_decision or {}
            ).get("primary_source")
            latest_proactive_line_transition_key = (
                last_turn.proactive_line_transition_decision or {}
            ).get("transition_key")
            latest_proactive_line_transition_mode = (
                last_turn.proactive_line_transition_decision or {}
            ).get("transition_mode")
            latest_proactive_line_transition_exit_mode = (
                last_turn.proactive_line_transition_decision or {}
            ).get("line_exit_mode")
            latest_proactive_line_transition_source = (
                last_turn.proactive_line_transition_decision or {}
            ).get("primary_source")
            latest_proactive_line_machine_key = (
                last_turn.proactive_line_machine_decision or {}
            ).get("machine_key")
            latest_proactive_line_machine_mode = (
                last_turn.proactive_line_machine_decision or {}
            ).get("machine_mode")
            latest_proactive_line_machine_lifecycle = (
                last_turn.proactive_line_machine_decision or {}
            ).get("lifecycle_mode")
            latest_proactive_line_machine_actionability = (
                last_turn.proactive_line_machine_decision or {}
            ).get("actionability")
            latest_proactive_line_machine_source = (
                last_turn.proactive_line_machine_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_state_key = (
                last_turn.proactive_lifecycle_state_decision or {}
            ).get("state_key")
            latest_proactive_lifecycle_state_mode = (
                last_turn.proactive_lifecycle_state_decision or {}
            ).get("state_mode")
            latest_proactive_lifecycle_state_lifecycle = (
                last_turn.proactive_lifecycle_state_decision or {}
            ).get("lifecycle_mode")
            latest_proactive_lifecycle_state_actionability = (
                last_turn.proactive_lifecycle_state_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_state_source = (
                last_turn.proactive_lifecycle_state_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_transition_key = (
                last_turn.proactive_lifecycle_transition_decision or {}
            ).get("transition_key")
            latest_proactive_lifecycle_transition_mode = (
                last_turn.proactive_lifecycle_transition_decision or {}
            ).get("transition_mode")
            latest_proactive_lifecycle_transition_exit_mode = (
                last_turn.proactive_lifecycle_transition_decision or {}
            ).get("lifecycle_exit_mode")
            latest_proactive_lifecycle_transition_source = (
                last_turn.proactive_lifecycle_transition_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_machine_key = (
                last_turn.proactive_lifecycle_machine_decision or {}
            ).get("machine_key")
            latest_proactive_lifecycle_machine_mode = (
                last_turn.proactive_lifecycle_machine_decision or {}
            ).get("machine_mode")
            latest_proactive_lifecycle_machine_lifecycle = (
                last_turn.proactive_lifecycle_machine_decision or {}
            ).get("lifecycle_mode")
            latest_proactive_lifecycle_machine_actionability = (
                last_turn.proactive_lifecycle_machine_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_machine_source = (
                last_turn.proactive_lifecycle_machine_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_controller_key = (
                last_turn.proactive_lifecycle_controller_decision or {}
            ).get("controller_key")
            latest_proactive_lifecycle_controller_state = (
                last_turn.proactive_lifecycle_controller_decision or {}
            ).get("lifecycle_state")
            latest_proactive_lifecycle_controller_decision = (
                last_turn.proactive_lifecycle_controller_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_controller_delay_seconds = int(
                (last_turn.proactive_lifecycle_controller_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_controller_source = (
                last_turn.proactive_lifecycle_controller_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_envelope_key = (
                last_turn.proactive_lifecycle_envelope_decision or {}
            ).get("envelope_key")
            latest_proactive_lifecycle_envelope_state = (
                last_turn.proactive_lifecycle_envelope_decision or {}
            ).get("lifecycle_state")
            latest_proactive_lifecycle_envelope_mode = (
                last_turn.proactive_lifecycle_envelope_decision or {}
            ).get("envelope_mode")
            latest_proactive_lifecycle_envelope_decision = (
                last_turn.proactive_lifecycle_envelope_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_envelope_actionability = (
                last_turn.proactive_lifecycle_envelope_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_envelope_delay_seconds = int(
                (last_turn.proactive_lifecycle_envelope_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_envelope_source = (
                last_turn.proactive_lifecycle_envelope_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_scheduler_key = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("scheduler_key")
            latest_proactive_lifecycle_scheduler_state = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("lifecycle_state")
            latest_proactive_lifecycle_scheduler_mode = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("scheduler_mode")
            latest_proactive_lifecycle_scheduler_decision = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_scheduler_actionability = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_scheduler_queue_status = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("queue_status_hint")
            latest_proactive_lifecycle_scheduler_delay_seconds = int(
                (last_turn.proactive_lifecycle_scheduler_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_scheduler_source = (
                last_turn.proactive_lifecycle_scheduler_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_window_key = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("window_key")
            latest_proactive_lifecycle_window_state = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("lifecycle_state")
            latest_proactive_lifecycle_window_mode = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("window_mode")
            latest_proactive_lifecycle_window_decision = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_window_actionability = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_window_queue_status = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("queue_status")
            latest_proactive_lifecycle_window_delay_seconds = int(
                (last_turn.proactive_lifecycle_window_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_window_source = (
                last_turn.proactive_lifecycle_window_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_queue_key = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("queue_key")
            latest_proactive_lifecycle_queue_state = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("lifecycle_state")
            latest_proactive_lifecycle_queue_mode = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("queue_mode")
            latest_proactive_lifecycle_queue_decision = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_queue_actionability = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_queue_status = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("queue_status")
            latest_proactive_lifecycle_queue_delay_seconds = int(
                (last_turn.proactive_lifecycle_queue_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_queue_source = (
                last_turn.proactive_lifecycle_queue_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_dispatch_key = (
                last_turn.proactive_lifecycle_dispatch_decision or {}
            ).get("dispatch_key")
            latest_proactive_lifecycle_dispatch_state = (
                last_turn.proactive_lifecycle_dispatch_decision or {}
            ).get("lifecycle_state")
            latest_proactive_lifecycle_dispatch_mode = (
                last_turn.proactive_lifecycle_dispatch_decision or {}
            ).get("dispatch_mode")
            latest_proactive_lifecycle_dispatch_decision = (
                last_turn.proactive_lifecycle_dispatch_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_dispatch_actionability = (
                last_turn.proactive_lifecycle_dispatch_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_dispatch_delay_seconds = int(
                (last_turn.proactive_lifecycle_dispatch_decision or {}).get(
                    "additional_delay_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_dispatch_source = (
                last_turn.proactive_lifecycle_dispatch_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_outcome_key = (
                last_turn.proactive_lifecycle_outcome_decision or {}
            ).get("outcome_key")
            latest_proactive_lifecycle_outcome_status = (
                last_turn.proactive_lifecycle_outcome_decision or {}
            ).get("status")
            latest_proactive_lifecycle_outcome_mode = (
                last_turn.proactive_lifecycle_outcome_decision or {}
            ).get("outcome_mode")
            latest_proactive_lifecycle_outcome_decision = (
                last_turn.proactive_lifecycle_outcome_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_outcome_actionability = (
                last_turn.proactive_lifecycle_outcome_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_outcome_message_event_count = int(
                (last_turn.proactive_lifecycle_outcome_decision or {}).get(
                    "message_event_count",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_outcome_source = (
                last_turn.proactive_lifecycle_outcome_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_resolution_key = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("resolution_key")
            latest_proactive_lifecycle_resolution_status = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("status")
            latest_proactive_lifecycle_resolution_mode = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("resolution_mode")
            latest_proactive_lifecycle_resolution_decision = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_resolution_actionability = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_resolution_queue_override_status = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_resolution_remaining_stage_count = int(
                (last_turn.proactive_lifecycle_resolution_decision or {}).get(
                    "remaining_stage_count",
                    0,
                )
                or 0
            )
            latest_proactive_lifecycle_resolution_source = (
                last_turn.proactive_lifecycle_resolution_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_activation_key = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("activation_key")
            latest_proactive_lifecycle_activation_status = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("status")
            latest_proactive_lifecycle_activation_mode = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("activation_mode")
            latest_proactive_lifecycle_activation_decision = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_activation_actionability = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_activation_active_stage_label = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_activation_queue_override_status = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_activation_source = (
                last_turn.proactive_lifecycle_activation_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_settlement_key = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("settlement_key")
            latest_proactive_lifecycle_settlement_status = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("status")
            latest_proactive_lifecycle_settlement_mode = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("settlement_mode")
            latest_proactive_lifecycle_settlement_decision = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_settlement_actionability = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_settlement_active_stage_label = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_settlement_queue_override_status = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_settlement_source = (
                last_turn.proactive_lifecycle_settlement_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_closure_key = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("closure_key")
            latest_proactive_lifecycle_closure_status = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("status")
            latest_proactive_lifecycle_closure_mode = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("closure_mode")
            latest_proactive_lifecycle_closure_decision = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_closure_actionability = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_closure_active_stage_label = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_closure_queue_override_status = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_closure_source = (
                last_turn.proactive_lifecycle_closure_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_availability_key = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("availability_key")
            latest_proactive_lifecycle_availability_status = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("status")
            latest_proactive_lifecycle_availability_mode = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("availability_mode")
            latest_proactive_lifecycle_availability_decision = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_availability_actionability = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_availability_active_stage_label = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_availability_queue_override_status = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_availability_source = (
                last_turn.proactive_lifecycle_availability_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_retention_key = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("retention_key")
            latest_proactive_lifecycle_retention_status = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("status")
            latest_proactive_lifecycle_retention_mode = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("retention_mode")
            latest_proactive_lifecycle_retention_decision = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_retention_actionability = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_retention_active_stage_label = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_retention_queue_override_status = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_retention_source = (
                last_turn.proactive_lifecycle_retention_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_eligibility_key = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("eligibility_key")
            latest_proactive_lifecycle_eligibility_status = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("status")
            latest_proactive_lifecycle_eligibility_mode = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("eligibility_mode")
            latest_proactive_lifecycle_eligibility_decision = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_eligibility_actionability = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_eligibility_active_stage_label = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_eligibility_queue_override_status = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_eligibility_source = (
                last_turn.proactive_lifecycle_eligibility_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_candidate_key = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("candidate_key")
            latest_proactive_lifecycle_candidate_status = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("status")
            latest_proactive_lifecycle_candidate_mode = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("candidate_mode")
            latest_proactive_lifecycle_candidate_decision = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_candidate_actionability = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_candidate_active_stage_label = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_candidate_queue_override_status = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_candidate_source = (
                last_turn.proactive_lifecycle_candidate_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_selectability_key = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("selectability_key")
            latest_proactive_lifecycle_selectability_status = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("status")
            latest_proactive_lifecycle_selectability_mode = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("selectability_mode")
            latest_proactive_lifecycle_selectability_decision = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_selectability_actionability = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_selectability_active_stage_label = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_selectability_queue_override_status = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_selectability_source = (
                last_turn.proactive_lifecycle_selectability_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_reentry_key = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("reentry_key")
            latest_proactive_lifecycle_reentry_status = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("status")
            latest_proactive_lifecycle_reentry_mode = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("reentry_mode")
            latest_proactive_lifecycle_reentry_decision = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_reentry_actionability = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_reentry_active_stage_label = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_reentry_queue_override_status = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_reentry_source = (
                last_turn.proactive_lifecycle_reentry_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_reactivation_key = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("reactivation_key")
            latest_proactive_lifecycle_reactivation_status = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("status")
            latest_proactive_lifecycle_reactivation_mode = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("reactivation_mode")
            latest_proactive_lifecycle_reactivation_decision = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_reactivation_actionability = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_reactivation_active_stage_label = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_reactivation_queue_override_status = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_reactivation_source = (
                last_turn.proactive_lifecycle_reactivation_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_resumption_key = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("resumption_key")
            latest_proactive_lifecycle_resumption_status = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("status")
            latest_proactive_lifecycle_resumption_mode = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("resumption_mode")
            latest_proactive_lifecycle_resumption_decision = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_resumption_actionability = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_resumption_active_stage_label = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_resumption_queue_override_status = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_resumption_source = (
                last_turn.proactive_lifecycle_resumption_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_readiness_key = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("readiness_key")
            latest_proactive_lifecycle_readiness_status = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("status")
            latest_proactive_lifecycle_readiness_mode = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("readiness_mode")
            latest_proactive_lifecycle_readiness_decision = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_readiness_actionability = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_readiness_active_stage_label = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_readiness_queue_override_status = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_readiness_source = (
                last_turn.proactive_lifecycle_readiness_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_arming_key = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("arming_key")
            latest_proactive_lifecycle_arming_status = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("status")
            latest_proactive_lifecycle_arming_mode = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("arming_mode")
            latest_proactive_lifecycle_arming_decision = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_arming_actionability = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_arming_active_stage_label = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_arming_queue_override_status = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_arming_source = (
                last_turn.proactive_lifecycle_arming_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_trigger_key = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("trigger_key")
            latest_proactive_lifecycle_trigger_status = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("status")
            latest_proactive_lifecycle_trigger_mode = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("trigger_mode")
            latest_proactive_lifecycle_trigger_decision = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_trigger_actionability = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_trigger_active_stage_label = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_trigger_queue_override_status = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_trigger_source = (
                last_turn.proactive_lifecycle_trigger_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_launch_key = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("launch_key")
            latest_proactive_lifecycle_launch_status = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("status")
            latest_proactive_lifecycle_launch_mode = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("launch_mode")
            latest_proactive_lifecycle_launch_decision = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_launch_actionability = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_launch_active_stage_label = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_launch_queue_override_status = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_launch_source = (
                last_turn.proactive_lifecycle_launch_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_handoff_key = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("handoff_key")
            latest_proactive_lifecycle_handoff_status = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("status")
            latest_proactive_lifecycle_handoff_mode = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("handoff_mode")
            latest_proactive_lifecycle_handoff_decision = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_handoff_actionability = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_handoff_active_stage_label = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_handoff_queue_override_status = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_handoff_source = (
                last_turn.proactive_lifecycle_handoff_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_continuation_key = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("continuation_key")
            latest_proactive_lifecycle_continuation_status = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("status")
            latest_proactive_lifecycle_continuation_mode = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("continuation_mode")
            latest_proactive_lifecycle_continuation_decision = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_continuation_actionability = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_continuation_active_stage_label = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_continuation_queue_override_status = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_continuation_source = (
                last_turn.proactive_lifecycle_continuation_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_sustainment_key = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("sustainment_key")
            latest_proactive_lifecycle_sustainment_status = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("status")
            latest_proactive_lifecycle_sustainment_mode = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("sustainment_mode")
            latest_proactive_lifecycle_sustainment_decision = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_sustainment_actionability = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_sustainment_active_stage_label = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_sustainment_queue_override_status = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_sustainment_source = (
                last_turn.proactive_lifecycle_sustainment_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_stewardship_key = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("stewardship_key")
            latest_proactive_lifecycle_stewardship_status = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("status")
            latest_proactive_lifecycle_stewardship_mode = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("stewardship_mode")
            latest_proactive_lifecycle_stewardship_decision = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_stewardship_actionability = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_stewardship_active_stage_label = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_stewardship_queue_override_status = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_stewardship_source = (
                last_turn.proactive_lifecycle_stewardship_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_guardianship_key = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("guardianship_key")
            latest_proactive_lifecycle_guardianship_status = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("status")
            latest_proactive_lifecycle_guardianship_mode = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("guardianship_mode")
            latest_proactive_lifecycle_guardianship_decision = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_guardianship_actionability = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_guardianship_active_stage_label = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_guardianship_queue_override_status = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_guardianship_source = (
                last_turn.proactive_lifecycle_guardianship_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_oversight_key = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("oversight_key")
            latest_proactive_lifecycle_oversight_status = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("status")
            latest_proactive_lifecycle_oversight_mode = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("oversight_mode")
            latest_proactive_lifecycle_oversight_decision = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_oversight_actionability = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_oversight_active_stage_label = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_oversight_queue_override_status = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_oversight_source = (
                last_turn.proactive_lifecycle_oversight_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_assurance_key = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("assurance_key")
            latest_proactive_lifecycle_assurance_status = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("status")
            latest_proactive_lifecycle_assurance_mode = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("assurance_mode")
            latest_proactive_lifecycle_assurance_decision = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_assurance_actionability = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_assurance_active_stage_label = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_assurance_queue_override_status = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_assurance_source = (
                last_turn.proactive_lifecycle_assurance_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_attestation_key = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("attestation_key")
            latest_proactive_lifecycle_attestation_status = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("status")
            latest_proactive_lifecycle_attestation_mode = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("attestation_mode")
            latest_proactive_lifecycle_attestation_decision = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_attestation_actionability = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_attestation_active_stage_label = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_attestation_queue_override_status = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_attestation_source = (
                last_turn.proactive_lifecycle_attestation_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_verification_key = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("verification_key")
            latest_proactive_lifecycle_verification_status = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("status")
            latest_proactive_lifecycle_verification_mode = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("verification_mode")
            latest_proactive_lifecycle_verification_decision = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_verification_actionability = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_verification_active_stage_label = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_verification_queue_override_status = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_verification_source = (
                last_turn.proactive_lifecycle_verification_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_certification_key = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("certification_key")
            latest_proactive_lifecycle_certification_status = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("status")
            latest_proactive_lifecycle_certification_mode = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("certification_mode")
            latest_proactive_lifecycle_certification_decision = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_certification_actionability = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_certification_active_stage_label = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_certification_queue_override_status = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_certification_source = (
                last_turn.proactive_lifecycle_certification_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_confirmation_key = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("confirmation_key")
            latest_proactive_lifecycle_confirmation_status = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("status")
            latest_proactive_lifecycle_confirmation_mode = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("confirmation_mode")
            latest_proactive_lifecycle_confirmation_decision = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_confirmation_actionability = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_confirmation_active_stage_label = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_confirmation_queue_override_status = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_confirmation_source = (
                last_turn.proactive_lifecycle_confirmation_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_ratification_key = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("ratification_key")
            latest_proactive_lifecycle_ratification_status = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("status")
            latest_proactive_lifecycle_ratification_mode = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("ratification_mode")
            latest_proactive_lifecycle_ratification_decision = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_ratification_actionability = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_ratification_active_stage_label = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_ratification_queue_override_status = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_ratification_source = (
                last_turn.proactive_lifecycle_ratification_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_endorsement_key = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("endorsement_key")
            latest_proactive_lifecycle_endorsement_status = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("status")
            latest_proactive_lifecycle_endorsement_mode = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("endorsement_mode")
            latest_proactive_lifecycle_endorsement_decision = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_endorsement_actionability = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_endorsement_active_stage_label = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_endorsement_queue_override_status = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_endorsement_source = (
                last_turn.proactive_lifecycle_endorsement_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_authorization_key = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("authorization_key")
            latest_proactive_lifecycle_authorization_status = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("status")
            latest_proactive_lifecycle_authorization_mode = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("authorization_mode")
            latest_proactive_lifecycle_authorization_decision = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_authorization_actionability = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_authorization_active_stage_label = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_authorization_queue_override_status = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_authorization_source = (
                last_turn.proactive_lifecycle_authorization_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_enactment_key = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("enactment_key")
            latest_proactive_lifecycle_enactment_status = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("status")
            latest_proactive_lifecycle_enactment_mode = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("enactment_mode")
            latest_proactive_lifecycle_enactment_decision = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_enactment_actionability = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_enactment_active_stage_label = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_enactment_queue_override_status = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_enactment_source = (
                last_turn.proactive_lifecycle_enactment_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_finality_key = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("finality_key")
            latest_proactive_lifecycle_finality_status = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("status")
            latest_proactive_lifecycle_finality_mode = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("finality_mode")
            latest_proactive_lifecycle_finality_decision = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_finality_actionability = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_finality_active_stage_label = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_finality_queue_override_status = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_finality_source = (
                last_turn.proactive_lifecycle_finality_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_completion_key = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("completion_key")
            latest_proactive_lifecycle_completion_status = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("status")
            latest_proactive_lifecycle_completion_mode = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("completion_mode")
            latest_proactive_lifecycle_completion_decision = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_completion_actionability = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_completion_active_stage_label = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_completion_queue_override_status = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_completion_source = (
                last_turn.proactive_lifecycle_completion_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_conclusion_key = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("conclusion_key")
            latest_proactive_lifecycle_conclusion_status = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("status")
            latest_proactive_lifecycle_conclusion_mode = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("conclusion_mode")
            latest_proactive_lifecycle_conclusion_decision = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_conclusion_actionability = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_conclusion_active_stage_label = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_conclusion_queue_override_status = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_conclusion_source = (
                last_turn.proactive_lifecycle_conclusion_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_disposition_key = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("disposition_key")
            latest_proactive_lifecycle_disposition_status = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("status")
            latest_proactive_lifecycle_disposition_mode = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("disposition_mode")
            latest_proactive_lifecycle_disposition_decision = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_disposition_actionability = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_disposition_active_stage_label = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_disposition_queue_override_status = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_disposition_source = (
                last_turn.proactive_lifecycle_disposition_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_standing_key = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("standing_key")
            latest_proactive_lifecycle_standing_status = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("status")
            latest_proactive_lifecycle_standing_mode = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("standing_mode")
            latest_proactive_lifecycle_standing_decision = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_standing_actionability = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_standing_active_stage_label = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_standing_queue_override_status = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_standing_source = (
                last_turn.proactive_lifecycle_standing_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_residency_key = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("residency_key")
            latest_proactive_lifecycle_residency_status = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("status")
            latest_proactive_lifecycle_residency_mode = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("residency_mode")
            latest_proactive_lifecycle_residency_decision = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_residency_actionability = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_residency_active_stage_label = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_residency_queue_override_status = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_residency_source = (
                last_turn.proactive_lifecycle_residency_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_tenure_key = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("tenure_key")
            latest_proactive_lifecycle_tenure_status = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("status")
            latest_proactive_lifecycle_tenure_mode = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("tenure_mode")
            latest_proactive_lifecycle_tenure_decision = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_tenure_actionability = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_tenure_active_stage_label = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_tenure_queue_override_status = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_tenure_source = (
                last_turn.proactive_lifecycle_tenure_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_persistence_key = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("persistence_key")
            latest_proactive_lifecycle_persistence_status = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("status")
            latest_proactive_lifecycle_persistence_mode = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("persistence_mode")
            latest_proactive_lifecycle_persistence_decision = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_persistence_actionability = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_persistence_active_stage_label = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_persistence_queue_override_status = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_persistence_source = (
                last_turn.proactive_lifecycle_persistence_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_longevity_key = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("longevity_key")
            latest_proactive_lifecycle_longevity_status = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("status")
            latest_proactive_lifecycle_longevity_mode = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("longevity_mode")
            latest_proactive_lifecycle_longevity_decision = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_longevity_actionability = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_longevity_active_stage_label = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_longevity_queue_override_status = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_longevity_source = (
                last_turn.proactive_lifecycle_longevity_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_legacy_key = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("legacy_key")
            latest_proactive_lifecycle_legacy_status = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("status")
            latest_proactive_lifecycle_legacy_mode = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("legacy_mode")
            latest_proactive_lifecycle_legacy_decision = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_legacy_actionability = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_legacy_active_stage_label = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_legacy_queue_override_status = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_legacy_source = (
                last_turn.proactive_lifecycle_legacy_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_heritage_key = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("heritage_key")
            latest_proactive_lifecycle_heritage_status = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("status")
            latest_proactive_lifecycle_heritage_mode = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("heritage_mode")
            latest_proactive_lifecycle_heritage_decision = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_heritage_actionability = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_heritage_active_stage_label = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_heritage_queue_override_status = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_heritage_source = (
                last_turn.proactive_lifecycle_heritage_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_lineage_key = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("lineage_key")
            latest_proactive_lifecycle_lineage_status = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("status")
            latest_proactive_lifecycle_lineage_mode = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("lineage_mode")
            latest_proactive_lifecycle_lineage_decision = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_lineage_actionability = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_lineage_active_stage_label = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_lineage_queue_override_status = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_lineage_source = (
                last_turn.proactive_lifecycle_lineage_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_ancestry_key = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("ancestry_key")
            latest_proactive_lifecycle_ancestry_status = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("status")
            latest_proactive_lifecycle_ancestry_mode = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("ancestry_mode")
            latest_proactive_lifecycle_ancestry_decision = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_ancestry_actionability = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_ancestry_active_stage_label = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_ancestry_queue_override_status = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_ancestry_source = (
                last_turn.proactive_lifecycle_ancestry_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_provenance_key = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("provenance_key")
            latest_proactive_lifecycle_provenance_status = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("status")
            latest_proactive_lifecycle_provenance_mode = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("provenance_mode")
            latest_proactive_lifecycle_provenance_decision = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_provenance_actionability = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_provenance_active_stage_label = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_provenance_queue_override_status = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_provenance_source = (
                last_turn.proactive_lifecycle_provenance_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_origin_key = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("origin_key")
            latest_proactive_lifecycle_origin_status = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("status")
            latest_proactive_lifecycle_origin_mode = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("origin_mode")
            latest_proactive_lifecycle_origin_decision = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_origin_actionability = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_origin_active_stage_label = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_origin_queue_override_status = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_origin_source = (
                last_turn.proactive_lifecycle_origin_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_root_key = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("root_key")
            latest_proactive_lifecycle_root_status = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("status")
            latest_proactive_lifecycle_root_mode = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("root_mode")
            latest_proactive_lifecycle_root_decision = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_root_actionability = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_root_active_stage_label = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_root_queue_override_status = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_root_source = (
                last_turn.proactive_lifecycle_root_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_foundation_key = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("foundation_key")
            latest_proactive_lifecycle_foundation_status = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("status")
            latest_proactive_lifecycle_foundation_mode = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("foundation_mode")
            latest_proactive_lifecycle_foundation_decision = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_foundation_actionability = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_foundation_active_stage_label = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_foundation_queue_override_status = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_foundation_source = (
                last_turn.proactive_lifecycle_foundation_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_bedrock_key = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("bedrock_key")
            latest_proactive_lifecycle_bedrock_status = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("status")
            latest_proactive_lifecycle_bedrock_mode = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("bedrock_mode")
            latest_proactive_lifecycle_bedrock_decision = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_bedrock_actionability = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_bedrock_active_stage_label = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_bedrock_queue_override_status = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_bedrock_source = (
                last_turn.proactive_lifecycle_bedrock_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_substrate_key = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("substrate_key")
            latest_proactive_lifecycle_substrate_status = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("status")
            latest_proactive_lifecycle_substrate_mode = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("substrate_mode")
            latest_proactive_lifecycle_substrate_decision = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_substrate_actionability = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_substrate_active_stage_label = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_substrate_queue_override_status = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_substrate_source = (
                last_turn.proactive_lifecycle_substrate_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_stratum_key = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("stratum_key")
            latest_proactive_lifecycle_stratum_status = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("status")
            latest_proactive_lifecycle_stratum_mode = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("stratum_mode")
            latest_proactive_lifecycle_stratum_decision = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_stratum_actionability = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_stratum_active_stage_label = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_stratum_queue_override_status = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_stratum_source = (
                last_turn.proactive_lifecycle_stratum_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_layer_key = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("layer_key")
            latest_proactive_lifecycle_layer_status = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("status")
            latest_proactive_lifecycle_layer_mode = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("layer_mode")
            latest_proactive_lifecycle_layer_decision = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_layer_actionability = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_layer_active_stage_label = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_layer_queue_override_status = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_layer_source = (
                last_turn.proactive_lifecycle_layer_decision or {}
            ).get("primary_source")
            latest_proactive_lifecycle_durability_key = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("durability_key")
            latest_proactive_lifecycle_durability_status = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("status")
            latest_proactive_lifecycle_durability_mode = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("durability_mode")
            latest_proactive_lifecycle_durability_decision = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("decision")
            latest_proactive_lifecycle_durability_actionability = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("actionability")
            latest_proactive_lifecycle_durability_active_stage_label = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("active_stage_label")
            latest_proactive_lifecycle_durability_queue_override_status = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("queue_override_status")
            latest_proactive_lifecycle_durability_source = (
                last_turn.proactive_lifecycle_durability_decision or {}
            ).get("primary_source")
            latest_proactive_stage_refresh_key = (
                last_turn.proactive_stage_refresh_plan or {}
            ).get("refresh_key")
            latest_proactive_stage_refresh_window_status = (
                last_turn.proactive_stage_refresh_plan or {}
            ).get("dispatch_window_status")
            latest_proactive_stage_refresh_stage_label = (
                last_turn.proactive_stage_refresh_plan or {}
            ).get("stage_label")
            latest_proactive_stage_refresh_changed = bool(
                (last_turn.proactive_stage_refresh_plan or {}).get("changed")
            )
            latest_proactive_stage_refresh_delivery_mode = (
                last_turn.proactive_stage_refresh_plan or {}
            ).get("refreshed_delivery_mode")
            latest_proactive_stage_refresh_user_space_signal = (
                last_turn.proactive_stage_refresh_plan or {}
            ).get("refreshed_user_space_signal")
            latest_proactive_stage_replan_key = (
                last_turn.proactive_stage_replan_assessment or {}
            ).get("replan_key")
            latest_proactive_stage_replan_strategy_key = (
                last_turn.proactive_stage_replan_assessment or {}
            ).get("selected_strategy_key")
            latest_proactive_stage_replan_ritual_mode = (
                last_turn.proactive_stage_replan_assessment or {}
            ).get("selected_ritual_mode")
            latest_proactive_stage_replan_pressure_mode = (
                last_turn.proactive_stage_replan_assessment or {}
            ).get("selected_pressure_mode")
            latest_proactive_stage_replan_autonomy_signal = (
                last_turn.proactive_stage_replan_assessment or {}
            ).get("selected_autonomy_signal")
            latest_proactive_stage_replan_changed = bool(
                (last_turn.proactive_stage_replan_assessment or {}).get("changed")
            )
            latest_proactive_dispatch_feedback_key = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("feedback_key")
            latest_proactive_dispatch_feedback_strategy_key = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("selected_strategy_key")
            latest_proactive_dispatch_feedback_pressure_mode = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("selected_pressure_mode")
            latest_proactive_dispatch_feedback_autonomy_signal = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("selected_autonomy_signal")
            latest_proactive_dispatch_feedback_delivery_mode = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("selected_delivery_mode")
            latest_proactive_dispatch_feedback_sequence_objective = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("selected_sequence_objective")
            latest_proactive_dispatch_feedback_prior_stage_label = (
                last_turn.proactive_dispatch_feedback_assessment or {}
            ).get("prior_stage_label")
            latest_proactive_dispatch_feedback_changed = bool(
                (last_turn.proactive_dispatch_feedback_assessment or {}).get("changed")
            )
            latest_proactive_dispatch_gate_key = (
                last_turn.proactive_dispatch_gate_decision or {}
            ).get("gate_key")
            latest_proactive_dispatch_gate_decision = (
                last_turn.proactive_dispatch_gate_decision or {}
            ).get("decision")
            latest_proactive_dispatch_gate_retry_after_seconds = int(
                (last_turn.proactive_dispatch_gate_decision or {}).get(
                    "retry_after_seconds",
                    0,
                )
                or 0
            )
            latest_proactive_dispatch_gate_strategy_key = (
                last_turn.proactive_dispatch_gate_decision or {}
            ).get("selected_strategy_key")
            latest_proactive_dispatch_gate_changed = bool(
                (last_turn.proactive_dispatch_gate_decision or {}).get("changed")
            )
            latest_proactive_dispatch_envelope_key = (
                last_turn.proactive_dispatch_envelope_decision or {}
            ).get("envelope_key")
            latest_proactive_dispatch_envelope_decision = (
                last_turn.proactive_dispatch_envelope_decision or {}
            ).get("decision")
            latest_proactive_dispatch_envelope_strategy_key = (
                last_turn.proactive_dispatch_envelope_decision or {}
            ).get("selected_strategy_key")
            latest_proactive_dispatch_envelope_stage_delivery_mode = (
                last_turn.proactive_dispatch_envelope_decision or {}
            ).get("selected_stage_delivery_mode")
            latest_proactive_dispatch_envelope_reengagement_delivery_mode = (
                last_turn.proactive_dispatch_envelope_decision or {}
            ).get("selected_reengagement_delivery_mode")
            latest_proactive_dispatch_envelope_source_count = len(
                list(
                    (last_turn.proactive_dispatch_envelope_decision or {}).get(
                        "active_sources",
                        [],
                    )
                )
            )
            latest_proactive_stage_state_key = (
                last_turn.proactive_stage_state_decision or {}
            ).get("state_key")
            latest_proactive_stage_state_mode = (
                last_turn.proactive_stage_state_decision or {}
            ).get("state_mode")
            latest_proactive_stage_state_queue_status = (
                last_turn.proactive_stage_state_decision or {}
            ).get("queue_status")
            latest_proactive_stage_state_source = (
                last_turn.proactive_stage_state_decision or {}
            ).get("primary_source")
            latest_proactive_stage_transition_key = (
                last_turn.proactive_stage_transition_decision or {}
            ).get("transition_key")
            latest_proactive_stage_transition_mode = (
                last_turn.proactive_stage_transition_decision or {}
            ).get("transition_mode")
            latest_proactive_stage_transition_queue_hint = (
                last_turn.proactive_stage_transition_decision or {}
            ).get("next_queue_status_hint")
            latest_proactive_stage_transition_source = (
                last_turn.proactive_stage_transition_decision or {}
            ).get("primary_source")
            latest_proactive_stage_machine_key = (
                last_turn.proactive_stage_machine_decision or {}
            ).get("machine_key")
            latest_proactive_stage_machine_mode = (
                last_turn.proactive_stage_machine_decision or {}
            ).get("machine_mode")
            latest_proactive_stage_machine_lifecycle = (
                last_turn.proactive_stage_machine_decision or {}
            ).get("lifecycle_mode")
            latest_proactive_stage_machine_actionability = (
                last_turn.proactive_stage_machine_decision or {}
            ).get("actionability")
            latest_proactive_stage_machine_source = (
                last_turn.proactive_stage_machine_decision or {}
            ).get("primary_source")
            latest_reengagement_matrix_key = (
                last_turn.reengagement_matrix_assessment or {}
            ).get("matrix_key")
            latest_reengagement_matrix_selected_strategy = (
                last_turn.reengagement_matrix_assessment or {}
            ).get("selected_strategy_key")
            latest_reengagement_matrix_selected_score = (
                last_turn.reengagement_matrix_assessment or {}
            ).get("selected_score")
            latest_reengagement_matrix_blocked_count = int(
                (last_turn.reengagement_matrix_assessment or {}).get(
                    "blocked_count",
                    0,
                )
                or 0
            )
            matrix_candidates = list(
                (last_turn.reengagement_matrix_assessment or {}).get("candidates", [])
            )
            latest_reengagement_matrix_learning_mode = (
                last_turn.reengagement_matrix_assessment or {}
            ).get("learning_mode")
            latest_reengagement_matrix_learning_context_stratum = (
                last_turn.reengagement_matrix_assessment or {}
            ).get("learning_context_stratum")
            latest_reengagement_matrix_learning_signal_count = int(
                (last_turn.reengagement_matrix_assessment or {}).get(
                    "learning_signal_count",
                    0,
                )
                or 0
            )
            selected_matrix_candidate = next(
                (
                    dict(candidate)
                    for candidate in matrix_candidates
                    if bool(candidate.get("selected"))
                    or (
                        str(candidate.get("strategy_key") or "")
                        == str(latest_reengagement_matrix_selected_strategy or "")
                    )
                ),
                {},
            )
            latest_reengagement_matrix_selected_supporting_session_count = int(
                selected_matrix_candidate.get("supporting_session_count") or 0
            )
            latest_reengagement_matrix_selected_contextual_supporting_session_count = (
                int(selected_matrix_candidate.get("contextual_supporting_session_count") or 0)
            )
            latest_reengagement_matrix_top_alternative = next(
                (
                    str(candidate.get("strategy_key") or "")
                    for candidate in matrix_candidates
                    if str(candidate.get("strategy_key") or "")
                    and str(candidate.get("strategy_key") or "")
                    != str(latest_reengagement_matrix_selected_strategy or "")
                ),
                None,
            )
            latest_reengagement_ritual_mode = (
                last_turn.reengagement_plan or {}
            ).get("ritual_mode")
            latest_reengagement_delivery_mode = (
                last_turn.reengagement_plan or {}
            ).get("delivery_mode")
            latest_reengagement_strategy_key = (
                last_turn.reengagement_plan or {}
            ).get("strategy_key")
            latest_reengagement_relational_move = (
                last_turn.reengagement_plan or {}
            ).get("relational_move")
            latest_reengagement_pressure_mode = (
                last_turn.reengagement_plan or {}
            ).get("pressure_mode")
            latest_reengagement_autonomy_signal = (
                last_turn.reengagement_plan or {}
            ).get("autonomy_signal")
            latest_reengagement_sequence_objective = (
                last_turn.reengagement_plan or {}
            ).get("sequence_objective")
            latest_reengagement_somatic_action = (
                last_turn.reengagement_plan or {}
            ).get("somatic_action")
            latest_proactive_followup_dispatch_status = (
                last_turn.proactive_followup_dispatch or {}
            ).get("status")
            latest_proactive_followup_dispatch_source = (
                last_turn.proactive_followup_dispatch or {}
            ).get("source")
            latest_proactive_followup_dispatched_at = (
                last_turn.proactive_followup_dispatch or {}
            ).get("dispatched_at")
            latest_proactive_followup_dispatch_stage_index = int(
                (last_turn.proactive_followup_dispatch or {}).get(
                    "proactive_cadence_stage_index",
                    0,
                )
                or 0
            )
            latest_proactive_followup_dispatch_stage_label = (
                last_turn.proactive_followup_dispatch or {}
            ).get("proactive_cadence_stage_label")
            latest_proactive_followup_dispatch_remaining = int(
                (last_turn.proactive_followup_dispatch or {}).get(
                    "proactive_cadence_remaining_after_dispatch",
                    0,
                )
                or 0
            )
            latest_proactive_followup_dispatch_progression_action = (
                last_turn.proactive_followup_dispatch or {}
            ).get("proactive_progression_stage_action")
            latest_proactive_followup_dispatch_progression_advanced = bool(
                (last_turn.proactive_followup_dispatch or {}).get(
                    "proactive_progression_advanced"
                )
            )
            latest_runtime_quality_doctor_status = (
                last_turn.runtime_quality_doctor_report or {}
            ).get("status")
            latest_runtime_quality_doctor_issue_count = int(
                (last_turn.runtime_quality_doctor_report or {}).get("issue_count", 0)
            )
            latest_system3_identity_consistency = (
                last_turn.system3_snapshot or {}
            ).get("identity_consistency")
            latest_system3_identity_anchor = (last_turn.system3_snapshot or {}).get(
                "identity_anchor"
            )
            latest_system3_identity_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("identity_trajectory_status")
            latest_system3_identity_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("identity_trajectory_target")
            latest_system3_identity_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("identity_trajectory_trigger")
            latest_system3_growth_stage = (last_turn.system3_snapshot or {}).get(
                "growth_stage"
            )
            latest_system3_user_model_confidence = (
                last_turn.system3_snapshot or {}
            ).get("user_model_confidence")
            latest_system3_emotional_debt_status = (
                last_turn.system3_snapshot or {}
            ).get("emotional_debt_status")
            latest_system3_emotional_debt_score = (
                last_turn.system3_snapshot or {}
            ).get("emotional_debt_score")
            latest_system3_emotional_debt_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("emotional_debt_trajectory_status")
            latest_system3_emotional_debt_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("emotional_debt_trajectory_target")
            latest_system3_emotional_debt_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("emotional_debt_trajectory_trigger")
            latest_system3_strategy_audit_status = (
                last_turn.system3_snapshot or {}
            ).get("strategy_audit_status")
            latest_system3_strategy_audit_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("strategy_audit_trajectory_status")
            latest_system3_strategy_audit_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("strategy_audit_trajectory_target")
            latest_system3_strategy_audit_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("strategy_audit_trajectory_trigger")
            latest_system3_strategy_fit = (last_turn.system3_snapshot or {}).get(
                "strategy_fit"
            )
            latest_system3_strategy_supervision_status = (
                last_turn.system3_snapshot or {}
            ).get("strategy_supervision_status")
            latest_system3_strategy_supervision_mode = (
                last_turn.system3_snapshot or {}
            ).get("strategy_supervision_mode")
            latest_system3_strategy_supervision_trigger = (
                last_turn.system3_snapshot or {}
            ).get("strategy_supervision_trigger")
            latest_system3_strategy_supervision_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("strategy_supervision_trajectory_status")
            latest_system3_strategy_supervision_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("strategy_supervision_trajectory_target")
            latest_system3_strategy_supervision_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("strategy_supervision_trajectory_trigger")
            latest_system3_moral_reasoning_status = (
                last_turn.system3_snapshot or {}
            ).get("moral_reasoning_status")
            latest_system3_moral_posture = (last_turn.system3_snapshot or {}).get(
                "moral_posture"
            )
            latest_system3_moral_conflict = (last_turn.system3_snapshot or {}).get(
                "moral_conflict"
            )
            latest_system3_moral_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("moral_trajectory_status")
            latest_system3_moral_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("moral_trajectory_target")
            latest_system3_moral_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("moral_trajectory_trigger")
            latest_system3_user_model_evolution_status = (
                last_turn.system3_snapshot or {}
            ).get("user_model_evolution_status")
            latest_system3_user_model_revision_mode = (
                last_turn.system3_snapshot or {}
            ).get("user_model_revision_mode")
            latest_system3_user_model_shift_signal = (
                last_turn.system3_snapshot or {}
            ).get("user_model_shift_signal")
            latest_system3_user_model_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("user_model_trajectory_status")
            latest_system3_user_model_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("user_model_trajectory_target")
            latest_system3_user_model_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("user_model_trajectory_trigger")
            latest_system3_expectation_calibration_status = (
                last_turn.system3_snapshot or {}
            ).get("expectation_calibration_status")
            latest_system3_expectation_calibration_target = (
                last_turn.system3_snapshot or {}
            ).get("expectation_calibration_target")
            latest_system3_expectation_calibration_trigger = (
                last_turn.system3_snapshot or {}
            ).get("expectation_calibration_trigger")
            latest_system3_expectation_calibration_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("expectation_calibration_trajectory_status")
            latest_system3_expectation_calibration_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("expectation_calibration_trajectory_target")
            latest_system3_expectation_calibration_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("expectation_calibration_trajectory_trigger")
            latest_system3_dependency_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("dependency_governance_status")
            latest_system3_dependency_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("dependency_governance_target")
            latest_system3_dependency_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("dependency_governance_trigger")
            latest_system3_dependency_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("dependency_governance_trajectory_status")
            latest_system3_dependency_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("dependency_governance_trajectory_target")
            latest_system3_dependency_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("dependency_governance_trajectory_trigger")
            latest_system3_autonomy_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("autonomy_governance_status")
            latest_system3_autonomy_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("autonomy_governance_target")
            latest_system3_autonomy_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("autonomy_governance_trigger")
            latest_system3_autonomy_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("autonomy_governance_trajectory_status")
            latest_system3_autonomy_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("autonomy_governance_trajectory_target")
            latest_system3_autonomy_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("autonomy_governance_trajectory_trigger")
            latest_system3_boundary_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("boundary_governance_status")
            latest_system3_boundary_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("boundary_governance_target")
            latest_system3_boundary_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("boundary_governance_trigger")
            latest_system3_boundary_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("boundary_governance_trajectory_status")
            latest_system3_boundary_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("boundary_governance_trajectory_target")
            latest_system3_boundary_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("boundary_governance_trajectory_trigger")
            latest_system3_support_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("support_governance_status")
            latest_system3_support_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("support_governance_target")
            latest_system3_support_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("support_governance_trigger")
            latest_system3_support_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("support_governance_trajectory_status")
            latest_system3_support_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("support_governance_trajectory_target")
            latest_system3_support_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("support_governance_trajectory_trigger")
            latest_system3_continuity_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("continuity_governance_status")
            latest_system3_continuity_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("continuity_governance_target")
            latest_system3_continuity_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("continuity_governance_trigger")
            latest_system3_continuity_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("continuity_governance_trajectory_status")
            latest_system3_continuity_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("continuity_governance_trajectory_target")
            latest_system3_continuity_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("continuity_governance_trajectory_trigger")
            latest_system3_repair_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("repair_governance_status")
            latest_system3_repair_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("repair_governance_target")
            latest_system3_repair_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("repair_governance_trigger")
            latest_system3_repair_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("repair_governance_trajectory_status")
            latest_system3_repair_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("repair_governance_trajectory_target")
            latest_system3_repair_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("repair_governance_trajectory_trigger")
            latest_system3_attunement_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("attunement_governance_status")
            latest_system3_attunement_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("attunement_governance_target")
            latest_system3_attunement_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("attunement_governance_trigger")
            latest_system3_attunement_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("attunement_governance_trajectory_status")
            latest_system3_attunement_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("attunement_governance_trajectory_target")
            latest_system3_attunement_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("attunement_governance_trajectory_trigger")
            latest_system3_trust_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("trust_governance_status")
            latest_system3_trust_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("trust_governance_target")
            latest_system3_trust_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("trust_governance_trigger")
            latest_system3_trust_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("trust_governance_trajectory_status")
            latest_system3_trust_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("trust_governance_trajectory_target")
            latest_system3_trust_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("trust_governance_trajectory_trigger")
            latest_system3_clarity_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("clarity_governance_status")
            latest_system3_clarity_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("clarity_governance_target")
            latest_system3_clarity_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("clarity_governance_trigger")
            latest_system3_clarity_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("clarity_governance_trajectory_status")
            latest_system3_clarity_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("clarity_governance_trajectory_target")
            latest_system3_clarity_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("clarity_governance_trajectory_trigger")
            latest_system3_pacing_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("pacing_governance_status")
            latest_system3_pacing_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("pacing_governance_target")
            latest_system3_pacing_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("pacing_governance_trigger")
            latest_system3_pacing_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("pacing_governance_trajectory_status")
            latest_system3_pacing_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("pacing_governance_trajectory_target")
            latest_system3_pacing_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("pacing_governance_trajectory_trigger")
            latest_system3_commitment_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("commitment_governance_status")
            latest_system3_commitment_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("commitment_governance_target")
            latest_system3_commitment_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("commitment_governance_trigger")
            latest_system3_commitment_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("commitment_governance_trajectory_status")
            latest_system3_commitment_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("commitment_governance_trajectory_target")
            latest_system3_commitment_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("commitment_governance_trajectory_trigger")
            latest_system3_disclosure_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("disclosure_governance_status")
            latest_system3_disclosure_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("disclosure_governance_target")
            latest_system3_disclosure_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("disclosure_governance_trigger")
            latest_system3_disclosure_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("disclosure_governance_trajectory_status")
            latest_system3_disclosure_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("disclosure_governance_trajectory_target")
            latest_system3_disclosure_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("disclosure_governance_trajectory_trigger")
            latest_system3_reciprocity_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("reciprocity_governance_status")
            latest_system3_reciprocity_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("reciprocity_governance_target")
            latest_system3_reciprocity_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("reciprocity_governance_trigger")
            latest_system3_reciprocity_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("reciprocity_governance_trajectory_status")
            latest_system3_reciprocity_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("reciprocity_governance_trajectory_target")
            latest_system3_reciprocity_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("reciprocity_governance_trajectory_trigger")
            latest_system3_pressure_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("pressure_governance_status")
            latest_system3_pressure_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("pressure_governance_target")
            latest_system3_pressure_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("pressure_governance_trigger")
            latest_system3_pressure_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("pressure_governance_trajectory_status")
            latest_system3_pressure_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("pressure_governance_trajectory_target")
            latest_system3_pressure_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("pressure_governance_trajectory_trigger")
            latest_system3_relational_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("relational_governance_status")
            latest_system3_relational_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("relational_governance_target")
            latest_system3_relational_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("relational_governance_trigger")
            latest_system3_relational_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("relational_governance_trajectory_status")
            latest_system3_relational_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("relational_governance_trajectory_target")
            latest_system3_relational_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("relational_governance_trajectory_trigger")
            latest_system3_safety_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("safety_governance_status")
            latest_system3_safety_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("safety_governance_target")
            latest_system3_safety_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("safety_governance_trigger")
            latest_system3_safety_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("safety_governance_trajectory_status")
            latest_system3_safety_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("safety_governance_trajectory_target")
            latest_system3_safety_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("safety_governance_trajectory_trigger")
            latest_system3_progress_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("progress_governance_status")
            latest_system3_progress_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("progress_governance_target")
            latest_system3_progress_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("progress_governance_trigger")
            latest_system3_progress_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("progress_governance_trajectory_status")
            latest_system3_progress_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("progress_governance_trajectory_target")
            latest_system3_progress_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("progress_governance_trajectory_trigger")
            latest_system3_stability_governance_status = (
                last_turn.system3_snapshot or {}
            ).get("stability_governance_status")
            latest_system3_stability_governance_target = (
                last_turn.system3_snapshot or {}
            ).get("stability_governance_target")
            latest_system3_stability_governance_trigger = (
                last_turn.system3_snapshot or {}
            ).get("stability_governance_trigger")
            latest_system3_stability_governance_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("stability_governance_trajectory_status")
            latest_system3_stability_governance_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("stability_governance_trajectory_target")
            latest_system3_stability_governance_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("stability_governance_trajectory_trigger")
            latest_system3_growth_transition_status = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_status")
            latest_system3_growth_transition_target = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_target")
            latest_system3_growth_transition_trigger = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_trigger")
            latest_system3_growth_transition_readiness = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_readiness")
            latest_system3_growth_transition_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_trajectory_status")
            latest_system3_growth_transition_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_trajectory_target")
            latest_system3_growth_transition_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("growth_transition_trajectory_trigger")
            latest_system3_version_migration_status = (
                last_turn.system3_snapshot or {}
            ).get("version_migration_status")
            latest_system3_version_migration_scope = (
                last_turn.system3_snapshot or {}
            ).get("version_migration_scope")
            latest_system3_version_migration_trigger = (
                last_turn.system3_snapshot or {}
            ).get("version_migration_trigger")
            latest_system3_version_migration_trajectory_status = (
                last_turn.system3_snapshot or {}
            ).get("version_migration_trajectory_status")
            latest_system3_version_migration_trajectory_target = (
                last_turn.system3_snapshot or {}
            ).get("version_migration_trajectory_target")
            latest_system3_version_migration_trajectory_trigger = (
                last_turn.system3_snapshot or {}
            ).get("version_migration_trajectory_trigger")
            latest_response_post_audit_status = (
                last_turn.response_post_audit or {}
            ).get("status")
            latest_response_normalization_final_status = (
                last_turn.response_normalization or {}
            ).get("final_status")
            latest_memory_items = len((last_turn.memory_bundle or {}).get("working_memory", []))
            latest_memory_recall_count = int(
                (last_turn.memory_recall or {}).get("recall_count", 0)
            )
            latest_memory_filtered_count = int(
                (last_turn.memory_recall or {})
                .get("integrity_summary", {})
                .get("filtered_count", 0)
            )
            latest_memory_blocked_count = int(
                (last_turn.memory_write_guard or {}).get("blocked_count", 0)
            )
            latest_memory_pinned_count = int(
                (last_turn.memory_retention or {}).get("pinned_count", 0)
            )
            latest_memory_evicted_count = int(
                (last_turn.memory_forgetting or {}).get("evicted_count", 0)
            )

        bid_rate = 1.0 if not bid_turns else round(len(responded_bids) / len(bid_turns), 3)
        session_duration_seconds = self._compute_session_duration_seconds(
            started_at=started_at,
            last_event_at=last_event_at,
        )

        return {
            "session_id": session_id,
            "session_source": str(started_metadata.get("source", "session") or "session"),
            "event_count": event_count,
            "turn_count": len(turn_records),
            "assistant_turn_count": sum(1 for turn in turn_records if turn.assistant_message),
            "started_at": started_at,
            "last_event_at": last_event_at,
            "session_duration_seconds": session_duration_seconds,
            "avg_seconds_per_turn": (
                round(session_duration_seconds / max(len(turn_records), 1), 3)
                if turn_records
                else None
            ),
            "bid_turn_count": len(bid_turns),
            "bid_turn_toward_rate": bid_rate,
            "rupture_detected_count": len(rupture_turns),
            "repair_assessment_high_severity_count": len(severe_repair_turns),
            "dependency_risk_elevated_count": len(dependency_turns),
            "llm_failure_count": len(llm_failures),
            "low_confidence_turn_count": len(low_confidence_turns),
            "clarification_required_turn_count": len(clarification_turns),
            "uncertainty_disclosure_turn_count": len(uncertainty_disclosure_turns),
            "knowledge_boundary_intervention_count": len(boundary_intervention_turns),
            "policy_gate_guarded_turn_count": len(guarded_policy_turns),
            "policy_gate_boundary_sensitive_turn_count": len(
                boundary_sensitive_policy_turns
            ),
            "rehearsal_high_risk_turn_count": len(high_risk_rehearsal_turns),
            "empowerment_audit_caution_turn_count": len(
                empowerment_audit_caution_turns
            ),
            "empowerment_audit_revise_turn_count": len(
                empowerment_audit_revise_turns
            ),
            "response_draft_question_turn_count": len(response_draft_question_turns),
            "response_draft_constraint_turn_count": len(
                response_draft_constrained_turns
            ),
            "response_rendering_boundary_turn_count": len(
                response_rendering_boundary_turns
            ),
            "response_rendering_uncertainty_turn_count": len(
                response_rendering_uncertainty_turns
            ),
            "assistant_message_event_count": sum(
                turn.assistant_message_event_count for turn in turn_records
            ),
            "continuous_output_turn_count": len(continuous_output_turns),
            "continuous_output_segment_total": sum(
                int(
                    (turn.response_sequence_plan or {}).get(
                        "unit_count",
                        turn.assistant_message_event_count,
                    )
                    or 0
                )
                for turn in continuous_output_turns
            ),
            "runtime_coordination_snapshot_count": len(
                runtime_coordination_snapshots
            ),
            "guidance_plan_count": len(guidance_plans),
            "guidance_stabilizing_turn_count": len(stabilizing_guidance_turns),
            "guidance_reanchor_turn_count": len(reanchor_guidance_turns),
            "guidance_low_pressure_turn_count": len(low_pressure_guidance_turns),
            "guidance_resume_carryover_turn_count": len(
                resume_carryover_guidance_turns
            ),
            "conversation_cadence_plan_count": len(cadence_plans),
            "conversation_cadence_spacious_turn_count": len(cadence_spacious_turns),
            "conversation_cadence_reanchor_turn_count": len(cadence_reanchor_turns),
            "session_ritual_plan_count": len(session_ritual_plans),
            "session_ritual_somatic_turn_count": len(session_ritual_somatic_turns),
            "somatic_orchestration_plan_count": len(somatic_orchestration_plans),
            "somatic_orchestration_active_turn_count": len(
                somatic_orchestration_active_turns
            ),
            "somatic_orchestration_followup_allowed_turn_count": len(
                somatic_orchestration_followup_allowed_turns
            ),
            "time_awareness_reengagement_turn_count": len(reengagement_turns),
            "cognitive_load_high_turn_count": len(high_cognitive_load_turns),
            "proactive_followup_eligible_turn_count": len(
                proactive_followup_turns
            ),
            "proactive_followup_ready_turn_count": len(proactive_ready_turns),
            "proactive_followup_hold_turn_count": len(proactive_hold_turns),
            "proactive_cadence_plan_count": len(proactive_cadence_plans),
            "proactive_cadence_multi_stage_turn_count": len(
                proactive_multi_stage_cadence_turns
            ),
            "proactive_guardrail_plan_count": len(proactive_guardrail_plans),
            "proactive_guardrail_reduced_dispatch_turn_count": len(
                proactive_guardrail_reduced_turns
            ),
            "proactive_guardrail_hard_stop_turn_count": len(
                proactive_guardrail_hard_stop_turns
            ),
            "proactive_scheduling_plan_count": len(proactive_scheduling_plans),
            "proactive_scheduling_deferred_turn_count": len(
                proactive_scheduling_deferred_turns
            ),
            "proactive_orchestration_plan_count": len(
                proactive_orchestration_plans
            ),
            "proactive_orchestration_multi_stage_turn_count": len(
                proactive_orchestration_multi_stage_turns
            ),
            "proactive_actuation_plan_count": len(proactive_actuation_plans),
            "proactive_actuation_multi_stage_turn_count": len(
                proactive_actuation_multi_stage_turns
            ),
            "proactive_progression_plan_count": len(proactive_progression_plans),
            "proactive_progression_multi_stage_turn_count": len(
                proactive_progression_multi_stage_turns
            ),
            "proactive_stage_controller_decision_count": len(
                proactive_stage_controller_decisions
            ),
            "proactive_stage_controller_changed_turn_count": len(
                proactive_stage_controller_changed_turns
            ),
            "proactive_line_controller_decision_count": len(
                proactive_line_controller_decisions
            ),
            "proactive_line_controller_changed_turn_count": len(
                proactive_line_controller_changed_turns
            ),
            "proactive_line_state_decision_count": len(
                proactive_line_state_decisions
            ),
            "proactive_line_state_changed_turn_count": len(
                proactive_line_state_changed_turns
            ),
            "proactive_line_state_buffered_turn_count": len(
                proactive_line_state_buffered_turns
            ),
            "proactive_line_state_terminal_turn_count": len(
                proactive_line_state_terminal_turns
            ),
            "proactive_line_transition_decision_count": len(
                proactive_line_transition_decisions
            ),
            "proactive_line_transition_changed_turn_count": len(
                proactive_line_transition_changed_turns
            ),
            "proactive_line_transition_buffered_turn_count": len(
                proactive_line_transition_buffered_turns
            ),
            "proactive_line_transition_terminal_turn_count": len(
                proactive_line_transition_terminal_turns
            ),
            "proactive_line_machine_decision_count": len(
                proactive_line_machine_decisions
            ),
            "proactive_line_machine_changed_turn_count": len(
                proactive_line_machine_changed_turns
            ),
            "proactive_line_machine_buffered_turn_count": len(
                proactive_line_machine_buffered_turns
            ),
            "proactive_line_machine_terminal_turn_count": len(
                proactive_line_machine_terminal_turns
            ),
            "proactive_lifecycle_state_decision_count": len(
                proactive_lifecycle_state_decisions
            ),
            "proactive_lifecycle_state_changed_turn_count": len(
                proactive_lifecycle_state_changed_turns
            ),
            "proactive_lifecycle_state_buffered_turn_count": len(
                proactive_lifecycle_state_buffered_turns
            ),
            "proactive_lifecycle_state_terminal_turn_count": len(
                proactive_lifecycle_state_terminal_turns
            ),
            "proactive_lifecycle_transition_decision_count": len(
                proactive_lifecycle_transition_decisions
            ),
            "proactive_lifecycle_transition_changed_turn_count": len(
                proactive_lifecycle_transition_changed_turns
            ),
            "proactive_lifecycle_transition_buffered_turn_count": len(
                proactive_lifecycle_transition_buffered_turns
            ),
            "proactive_lifecycle_transition_terminal_turn_count": len(
                proactive_lifecycle_transition_terminal_turns
            ),
            "proactive_lifecycle_machine_decision_count": len(
                proactive_lifecycle_machine_decisions
            ),
            "proactive_lifecycle_machine_changed_turn_count": len(
                proactive_lifecycle_machine_changed_turns
            ),
            "proactive_lifecycle_machine_buffered_turn_count": len(
                proactive_lifecycle_machine_buffered_turns
            ),
            "proactive_lifecycle_machine_terminal_turn_count": len(
                proactive_lifecycle_machine_terminal_turns
            ),
            "proactive_lifecycle_controller_decision_count": len(
                proactive_lifecycle_controller_decisions
            ),
            "proactive_lifecycle_controller_changed_turn_count": len(
                proactive_lifecycle_controller_changed_turns
            ),
            "proactive_lifecycle_controller_buffered_turn_count": len(
                proactive_lifecycle_controller_buffered_turns
            ),
            "proactive_lifecycle_controller_terminal_turn_count": len(
                proactive_lifecycle_controller_terminal_turns
            ),
            "proactive_lifecycle_envelope_decision_count": len(
                proactive_lifecycle_envelope_decisions
            ),
            "proactive_lifecycle_envelope_changed_turn_count": len(
                proactive_lifecycle_envelope_changed_turns
            ),
            "proactive_lifecycle_envelope_buffered_turn_count": len(
                proactive_lifecycle_envelope_buffered_turns
            ),
            "proactive_lifecycle_envelope_terminal_turn_count": len(
                proactive_lifecycle_envelope_terminal_turns
            ),
            "proactive_lifecycle_scheduler_decision_count": len(
                proactive_lifecycle_scheduler_decisions
            ),
            "proactive_lifecycle_scheduler_changed_turn_count": len(
                proactive_lifecycle_scheduler_changed_turns
            ),
            "proactive_lifecycle_scheduler_buffered_turn_count": len(
                proactive_lifecycle_scheduler_buffered_turns
            ),
            "proactive_lifecycle_scheduler_terminal_turn_count": len(
                proactive_lifecycle_scheduler_terminal_turns
            ),
            "proactive_lifecycle_window_decision_count": len(
                proactive_lifecycle_window_decisions
            ),
            "proactive_lifecycle_window_changed_turn_count": len(
                proactive_lifecycle_window_changed_turns
            ),
            "proactive_lifecycle_window_buffered_turn_count": len(
                proactive_lifecycle_window_buffered_turns
            ),
            "proactive_lifecycle_window_terminal_turn_count": len(
                proactive_lifecycle_window_terminal_turns
            ),
            "proactive_lifecycle_queue_decision_count": len(
                proactive_lifecycle_queue_decisions
            ),
            "proactive_lifecycle_queue_changed_turn_count": len(
                proactive_lifecycle_queue_changed_turns
            ),
            "proactive_lifecycle_queue_buffered_turn_count": len(
                proactive_lifecycle_queue_buffered_turns
            ),
            "proactive_lifecycle_queue_terminal_turn_count": len(
                proactive_lifecycle_queue_terminal_turns
            ),
            "proactive_lifecycle_dispatch_decision_count": len(
                proactive_lifecycle_dispatch_decisions
            ),
            "proactive_lifecycle_dispatch_changed_turn_count": len(
                proactive_lifecycle_dispatch_changed_turns
            ),
            "proactive_lifecycle_dispatch_sent_turn_count": len(
                proactive_lifecycle_dispatch_sent_turns
            ),
            "proactive_lifecycle_dispatch_rescheduled_turn_count": len(
                proactive_lifecycle_dispatch_rescheduled_turns
            ),
            "proactive_lifecycle_dispatch_hold_turn_count": len(
                proactive_lifecycle_dispatch_hold_turns
            ),
            "proactive_lifecycle_dispatch_retire_turn_count": len(
                proactive_lifecycle_dispatch_retire_turns
            ),
            "proactive_lifecycle_outcome_decision_count": len(
                proactive_lifecycle_outcome_decisions
            ),
            "proactive_lifecycle_outcome_changed_turn_count": len(
                proactive_lifecycle_outcome_changed_turns
            ),
            "proactive_lifecycle_outcome_sent_turn_count": len(
                proactive_lifecycle_outcome_sent_turns
            ),
            "proactive_lifecycle_outcome_rescheduled_turn_count": len(
                proactive_lifecycle_outcome_rescheduled_turns
            ),
            "proactive_lifecycle_outcome_hold_turn_count": len(
                proactive_lifecycle_outcome_hold_turns
            ),
            "proactive_lifecycle_outcome_retire_turn_count": len(
                proactive_lifecycle_outcome_retire_turns
            ),
            "proactive_lifecycle_resolution_decision_count": len(
                proactive_lifecycle_resolution_decisions
            ),
            "proactive_lifecycle_resolution_changed_turn_count": len(
                proactive_lifecycle_resolution_changed_turns
            ),
            "proactive_lifecycle_resolution_continue_turn_count": len(
                proactive_lifecycle_resolution_continue_turns
            ),
            "proactive_lifecycle_resolution_buffer_turn_count": len(
                proactive_lifecycle_resolution_buffer_turns
            ),
            "proactive_lifecycle_resolution_hold_turn_count": len(
                proactive_lifecycle_resolution_hold_turns
            ),
            "proactive_lifecycle_resolution_retire_turn_count": len(
                proactive_lifecycle_resolution_retire_turns
            ),
            "proactive_lifecycle_activation_decision_count": len(
                proactive_lifecycle_activation_decisions
            ),
            "proactive_lifecycle_activation_changed_turn_count": len(
                proactive_lifecycle_activation_changed_turns
            ),
            "proactive_lifecycle_activation_activate_turn_count": len(
                proactive_lifecycle_activation_activate_turns
            ),
            "proactive_lifecycle_activation_buffer_turn_count": len(
                proactive_lifecycle_activation_buffer_turns
            ),
            "proactive_lifecycle_activation_hold_turn_count": len(
                proactive_lifecycle_activation_hold_turns
            ),
            "proactive_lifecycle_activation_retire_turn_count": len(
                proactive_lifecycle_activation_retire_turns
            ),
            "proactive_lifecycle_settlement_decision_count": len(
                proactive_lifecycle_settlement_decisions
            ),
            "proactive_lifecycle_settlement_changed_turn_count": len(
                proactive_lifecycle_settlement_changed_turns
            ),
            "proactive_lifecycle_settlement_keep_turn_count": len(
                proactive_lifecycle_settlement_keep_turns
            ),
            "proactive_lifecycle_settlement_buffer_turn_count": len(
                proactive_lifecycle_settlement_buffer_turns
            ),
            "proactive_lifecycle_settlement_hold_turn_count": len(
                proactive_lifecycle_settlement_hold_turns
            ),
            "proactive_lifecycle_settlement_close_turn_count": len(
                proactive_lifecycle_settlement_close_turns
            ),
            "proactive_lifecycle_settlement_retire_turn_count": len(
                proactive_lifecycle_settlement_retire_turns
            ),
            "proactive_lifecycle_closure_decision_count": len(
                proactive_lifecycle_closure_decisions
            ),
            "proactive_lifecycle_closure_changed_turn_count": len(
                proactive_lifecycle_closure_changed_turns
            ),
            "proactive_lifecycle_closure_open_turn_count": len(
                proactive_lifecycle_closure_open_turns
            ),
            "proactive_lifecycle_closure_buffer_turn_count": len(
                proactive_lifecycle_closure_buffer_turns
            ),
            "proactive_lifecycle_closure_pause_turn_count": len(
                proactive_lifecycle_closure_pause_turns
            ),
            "proactive_lifecycle_closure_close_turn_count": len(
                proactive_lifecycle_closure_close_turns
            ),
            "proactive_lifecycle_closure_retire_turn_count": len(
                proactive_lifecycle_closure_retire_turns
            ),
            "proactive_lifecycle_availability_decision_count": len(
                proactive_lifecycle_availability_decisions
            ),
            "proactive_lifecycle_availability_changed_turn_count": len(
                proactive_lifecycle_availability_changed_turns
            ),
            "proactive_lifecycle_availability_open_turn_count": len(
                proactive_lifecycle_availability_open_turns
            ),
            "proactive_lifecycle_availability_buffer_turn_count": len(
                proactive_lifecycle_availability_buffer_turns
            ),
            "proactive_lifecycle_availability_pause_turn_count": len(
                proactive_lifecycle_availability_pause_turns
            ),
            "proactive_lifecycle_availability_close_turn_count": len(
                proactive_lifecycle_availability_close_turns
            ),
            "proactive_lifecycle_availability_retire_turn_count": len(
                proactive_lifecycle_availability_retire_turns
            ),
            "proactive_lifecycle_retention_decision_count": len(
                proactive_lifecycle_retention_decisions
            ),
            "proactive_lifecycle_retention_changed_turn_count": len(
                proactive_lifecycle_retention_changed_turns
            ),
            "proactive_lifecycle_retention_retain_turn_count": len(
                proactive_lifecycle_retention_retain_turns
            ),
            "proactive_lifecycle_retention_buffer_turn_count": len(
                proactive_lifecycle_retention_buffer_turns
            ),
            "proactive_lifecycle_retention_pause_turn_count": len(
                proactive_lifecycle_retention_pause_turns
            ),
            "proactive_lifecycle_retention_archive_turn_count": len(
                proactive_lifecycle_retention_archive_turns
            ),
            "proactive_lifecycle_retention_retire_turn_count": len(
                proactive_lifecycle_retention_retire_turns
            ),
            "proactive_lifecycle_eligibility_decision_count": len(
                proactive_lifecycle_eligibility_decisions
            ),
            "proactive_lifecycle_eligibility_changed_turn_count": len(
                proactive_lifecycle_eligibility_changed_turns
            ),
            "proactive_lifecycle_eligibility_keep_turn_count": len(
                proactive_lifecycle_eligibility_keep_turns
            ),
            "proactive_lifecycle_eligibility_buffer_turn_count": len(
                proactive_lifecycle_eligibility_buffer_turns
            ),
            "proactive_lifecycle_eligibility_pause_turn_count": len(
                proactive_lifecycle_eligibility_pause_turns
            ),
            "proactive_lifecycle_eligibility_archive_turn_count": len(
                proactive_lifecycle_eligibility_archive_turns
            ),
            "proactive_lifecycle_eligibility_retire_turn_count": len(
                proactive_lifecycle_eligibility_retire_turns
            ),
            "proactive_lifecycle_candidate_decision_count": len(
                proactive_lifecycle_candidate_decisions
            ),
            "proactive_lifecycle_candidate_changed_turn_count": len(
                proactive_lifecycle_candidate_changed_turns
            ),
            "proactive_lifecycle_candidate_keep_turn_count": len(
                proactive_lifecycle_candidate_keep_turns
            ),
            "proactive_lifecycle_candidate_buffer_turn_count": len(
                proactive_lifecycle_candidate_buffer_turns
            ),
            "proactive_lifecycle_candidate_pause_turn_count": len(
                proactive_lifecycle_candidate_pause_turns
            ),
            "proactive_lifecycle_candidate_archive_turn_count": len(
                proactive_lifecycle_candidate_archive_turns
            ),
            "proactive_lifecycle_candidate_retire_turn_count": len(
                proactive_lifecycle_candidate_retire_turns
            ),
            "proactive_lifecycle_selectability_decision_count": len(
                proactive_lifecycle_selectability_decisions
            ),
            "proactive_lifecycle_selectability_changed_turn_count": len(
                proactive_lifecycle_selectability_changed_turns
            ),
            "proactive_lifecycle_selectability_keep_turn_count": len(
                proactive_lifecycle_selectability_keep_turns
            ),
            "proactive_lifecycle_selectability_buffer_turn_count": len(
                proactive_lifecycle_selectability_buffer_turns
            ),
            "proactive_lifecycle_selectability_pause_turn_count": len(
                proactive_lifecycle_selectability_pause_turns
            ),
            "proactive_lifecycle_selectability_archive_turn_count": len(
                proactive_lifecycle_selectability_archive_turns
            ),
            "proactive_lifecycle_selectability_retire_turn_count": len(
                proactive_lifecycle_selectability_retire_turns
            ),
            "proactive_lifecycle_reentry_decision_count": len(
                proactive_lifecycle_reentry_decisions
            ),
            "proactive_lifecycle_reentry_changed_turn_count": len(
                proactive_lifecycle_reentry_changed_turns
            ),
            "proactive_lifecycle_reentry_keep_turn_count": len(
                proactive_lifecycle_reentry_keep_turns
            ),
            "proactive_lifecycle_reentry_buffer_turn_count": len(
                proactive_lifecycle_reentry_buffer_turns
            ),
            "proactive_lifecycle_reentry_pause_turn_count": len(
                proactive_lifecycle_reentry_pause_turns
            ),
            "proactive_lifecycle_reentry_archive_turn_count": len(
                proactive_lifecycle_reentry_archive_turns
            ),
            "proactive_lifecycle_reentry_retire_turn_count": len(
                proactive_lifecycle_reentry_retire_turns
            ),
            "proactive_lifecycle_reactivation_decision_count": len(
                proactive_lifecycle_reactivation_decisions
            ),
            "proactive_lifecycle_reactivation_changed_turn_count": len(
                proactive_lifecycle_reactivation_changed_turns
            ),
            "proactive_lifecycle_reactivation_keep_turn_count": len(
                proactive_lifecycle_reactivation_keep_turns
            ),
            "proactive_lifecycle_reactivation_buffer_turn_count": len(
                proactive_lifecycle_reactivation_buffer_turns
            ),
            "proactive_lifecycle_reactivation_pause_turn_count": len(
                proactive_lifecycle_reactivation_pause_turns
            ),
            "proactive_lifecycle_reactivation_archive_turn_count": len(
                proactive_lifecycle_reactivation_archive_turns
            ),
            "proactive_lifecycle_reactivation_retire_turn_count": len(
                proactive_lifecycle_reactivation_retire_turns
            ),
            "proactive_lifecycle_resumption_decision_count": len(
                proactive_lifecycle_resumption_decisions
            ),
            "proactive_lifecycle_resumption_changed_turn_count": len(
                proactive_lifecycle_resumption_changed_turns
            ),
            "proactive_lifecycle_resumption_keep_turn_count": len(
                proactive_lifecycle_resumption_keep_turns
            ),
            "proactive_lifecycle_resumption_buffer_turn_count": len(
                proactive_lifecycle_resumption_buffer_turns
            ),
            "proactive_lifecycle_resumption_pause_turn_count": len(
                proactive_lifecycle_resumption_pause_turns
            ),
            "proactive_lifecycle_resumption_archive_turn_count": len(
                proactive_lifecycle_resumption_archive_turns
            ),
            "proactive_lifecycle_resumption_retire_turn_count": len(
                proactive_lifecycle_resumption_retire_turns
            ),
            "proactive_lifecycle_readiness_decision_count": len(
                proactive_lifecycle_readiness_decisions
            ),
            "proactive_lifecycle_readiness_changed_turn_count": len(
                proactive_lifecycle_readiness_changed_turns
            ),
            "proactive_lifecycle_readiness_keep_turn_count": len(
                proactive_lifecycle_readiness_keep_turns
            ),
            "proactive_lifecycle_readiness_buffer_turn_count": len(
                proactive_lifecycle_readiness_buffer_turns
            ),
            "proactive_lifecycle_readiness_pause_turn_count": len(
                proactive_lifecycle_readiness_pause_turns
            ),
            "proactive_lifecycle_readiness_archive_turn_count": len(
                proactive_lifecycle_readiness_archive_turns
            ),
            "proactive_lifecycle_readiness_retire_turn_count": len(
                proactive_lifecycle_readiness_retire_turns
            ),
            "proactive_lifecycle_arming_decision_count": len(
                proactive_lifecycle_arming_decisions
            ),
            "proactive_lifecycle_arming_changed_turn_count": len(
                proactive_lifecycle_arming_changed_turns
            ),
            "proactive_lifecycle_arming_keep_turn_count": len(
                proactive_lifecycle_arming_keep_turns
            ),
            "proactive_lifecycle_arming_buffer_turn_count": len(
                proactive_lifecycle_arming_buffer_turns
            ),
            "proactive_lifecycle_arming_pause_turn_count": len(
                proactive_lifecycle_arming_pause_turns
            ),
            "proactive_lifecycle_arming_archive_turn_count": len(
                proactive_lifecycle_arming_archive_turns
            ),
            "proactive_lifecycle_arming_retire_turn_count": len(
                proactive_lifecycle_arming_retire_turns
            ),
            "proactive_lifecycle_trigger_decision_count": len(
                proactive_lifecycle_trigger_decisions
            ),
            "proactive_lifecycle_trigger_changed_turn_count": len(
                proactive_lifecycle_trigger_changed_turns
            ),
            "proactive_lifecycle_trigger_keep_turn_count": len(
                proactive_lifecycle_trigger_keep_turns
            ),
            "proactive_lifecycle_trigger_buffer_turn_count": len(
                proactive_lifecycle_trigger_buffer_turns
            ),
            "proactive_lifecycle_trigger_pause_turn_count": len(
                proactive_lifecycle_trigger_pause_turns
            ),
            "proactive_lifecycle_trigger_archive_turn_count": len(
                proactive_lifecycle_trigger_archive_turns
            ),
            "proactive_lifecycle_trigger_retire_turn_count": len(
                proactive_lifecycle_trigger_retire_turns
            ),
            "proactive_lifecycle_launch_decision_count": len(
                proactive_lifecycle_launch_decisions
            ),
            "proactive_lifecycle_launch_changed_turn_count": len(
                proactive_lifecycle_launch_changed_turns
            ),
            "proactive_lifecycle_launch_keep_turn_count": len(
                proactive_lifecycle_launch_keep_turns
            ),
            "proactive_lifecycle_launch_buffer_turn_count": len(
                proactive_lifecycle_launch_buffer_turns
            ),
            "proactive_lifecycle_launch_pause_turn_count": len(
                proactive_lifecycle_launch_pause_turns
            ),
            "proactive_lifecycle_launch_archive_turn_count": len(
                proactive_lifecycle_launch_archive_turns
            ),
            "proactive_lifecycle_launch_retire_turn_count": len(
                proactive_lifecycle_launch_retire_turns
            ),
            "proactive_lifecycle_handoff_decision_count": len(
                proactive_lifecycle_handoff_decisions
            ),
            "proactive_lifecycle_handoff_changed_turn_count": len(
                proactive_lifecycle_handoff_changed_turns
            ),
            "proactive_lifecycle_handoff_keep_turn_count": len(
                proactive_lifecycle_handoff_keep_turns
            ),
            "proactive_lifecycle_handoff_buffer_turn_count": len(
                proactive_lifecycle_handoff_buffer_turns
            ),
            "proactive_lifecycle_handoff_pause_turn_count": len(
                proactive_lifecycle_handoff_pause_turns
            ),
            "proactive_lifecycle_handoff_archive_turn_count": len(
                proactive_lifecycle_handoff_archive_turns
            ),
            "proactive_lifecycle_handoff_retire_turn_count": len(
                proactive_lifecycle_handoff_retire_turns
            ),
            "proactive_lifecycle_continuation_decision_count": len(
                proactive_lifecycle_continuation_decisions
            ),
            "proactive_lifecycle_continuation_changed_turn_count": len(
                proactive_lifecycle_continuation_changed_turns
            ),
            "proactive_lifecycle_continuation_keep_turn_count": len(
                proactive_lifecycle_continuation_keep_turns
            ),
            "proactive_lifecycle_continuation_buffer_turn_count": len(
                proactive_lifecycle_continuation_buffer_turns
            ),
            "proactive_lifecycle_continuation_pause_turn_count": len(
                proactive_lifecycle_continuation_pause_turns
            ),
            "proactive_lifecycle_continuation_archive_turn_count": len(
                proactive_lifecycle_continuation_archive_turns
            ),
            "proactive_lifecycle_continuation_retire_turn_count": len(
                proactive_lifecycle_continuation_retire_turns
            ),
            "proactive_lifecycle_sustainment_decision_count": len(
                proactive_lifecycle_sustainment_decisions
            ),
            "proactive_lifecycle_sustainment_changed_turn_count": len(
                proactive_lifecycle_sustainment_changed_turns
            ),
            "proactive_lifecycle_sustainment_sustain_turn_count": len(
                proactive_lifecycle_sustainment_sustain_turns
            ),
            "proactive_lifecycle_sustainment_buffer_turn_count": len(
                proactive_lifecycle_sustainment_buffer_turns
            ),
            "proactive_lifecycle_sustainment_pause_turn_count": len(
                proactive_lifecycle_sustainment_pause_turns
            ),
            "proactive_lifecycle_sustainment_archive_turn_count": len(
                proactive_lifecycle_sustainment_archive_turns
            ),
            "proactive_lifecycle_sustainment_retire_turn_count": len(
                proactive_lifecycle_sustainment_retire_turns
            ),
            "proactive_lifecycle_stewardship_decision_count": len(
                proactive_lifecycle_stewardship_decisions
            ),
            "proactive_lifecycle_stewardship_changed_turn_count": len(
                proactive_lifecycle_stewardship_changed_turns
            ),
            "proactive_lifecycle_stewardship_steward_turn_count": len(
                proactive_lifecycle_stewardship_steward_turns
            ),
            "proactive_lifecycle_stewardship_buffer_turn_count": len(
                proactive_lifecycle_stewardship_buffer_turns
            ),
            "proactive_lifecycle_stewardship_pause_turn_count": len(
                proactive_lifecycle_stewardship_pause_turns
            ),
            "proactive_lifecycle_stewardship_archive_turn_count": len(
                proactive_lifecycle_stewardship_archive_turns
            ),
            "proactive_lifecycle_stewardship_retire_turn_count": len(
                proactive_lifecycle_stewardship_retire_turns
            ),
            "proactive_lifecycle_guardianship_decision_count": len(
                proactive_lifecycle_guardianship_decisions
            ),
            "proactive_lifecycle_guardianship_changed_turn_count": len(
                proactive_lifecycle_guardianship_changed_turns
            ),
            "proactive_lifecycle_guardianship_guard_turn_count": len(
                proactive_lifecycle_guardianship_guard_turns
            ),
            "proactive_lifecycle_guardianship_buffer_turn_count": len(
                proactive_lifecycle_guardianship_buffer_turns
            ),
            "proactive_lifecycle_guardianship_pause_turn_count": len(
                proactive_lifecycle_guardianship_pause_turns
            ),
            "proactive_lifecycle_guardianship_archive_turn_count": len(
                proactive_lifecycle_guardianship_archive_turns
            ),
            "proactive_lifecycle_guardianship_retire_turn_count": len(
                proactive_lifecycle_guardianship_retire_turns
            ),
            "proactive_lifecycle_oversight_decision_count": len(
                proactive_lifecycle_oversight_decisions
            ),
            "proactive_lifecycle_oversight_changed_turn_count": len(
                proactive_lifecycle_oversight_changed_turns
            ),
            "proactive_lifecycle_oversight_oversee_turn_count": len(
                proactive_lifecycle_oversight_oversee_turns
            ),
            "proactive_lifecycle_oversight_buffer_turn_count": len(
                proactive_lifecycle_oversight_buffer_turns
            ),
            "proactive_lifecycle_oversight_pause_turn_count": len(
                proactive_lifecycle_oversight_pause_turns
            ),
            "proactive_lifecycle_oversight_archive_turn_count": len(
                proactive_lifecycle_oversight_archive_turns
            ),
            "proactive_lifecycle_oversight_retire_turn_count": len(
                proactive_lifecycle_oversight_retire_turns
            ),
            "proactive_lifecycle_assurance_decision_count": len(
                proactive_lifecycle_assurance_decisions
            ),
            "proactive_lifecycle_assurance_changed_turn_count": len(
                proactive_lifecycle_assurance_changed_turns
            ),
            "proactive_lifecycle_assurance_assure_turn_count": len(
                proactive_lifecycle_assurance_assure_turns
            ),
            "proactive_lifecycle_assurance_buffer_turn_count": len(
                proactive_lifecycle_assurance_buffer_turns
            ),
            "proactive_lifecycle_assurance_pause_turn_count": len(
                proactive_lifecycle_assurance_pause_turns
            ),
            "proactive_lifecycle_assurance_archive_turn_count": len(
                proactive_lifecycle_assurance_archive_turns
            ),
            "proactive_lifecycle_assurance_retire_turn_count": len(
                proactive_lifecycle_assurance_retire_turns
            ),
            "proactive_lifecycle_attestation_decision_count": len(
                proactive_lifecycle_attestation_decisions
            ),
            "proactive_lifecycle_attestation_changed_turn_count": len(
                proactive_lifecycle_attestation_changed_turns
            ),
            "proactive_lifecycle_attestation_attest_turn_count": len(
                proactive_lifecycle_attestation_attest_turns
            ),
            "proactive_lifecycle_attestation_buffer_turn_count": len(
                proactive_lifecycle_attestation_buffer_turns
            ),
            "proactive_lifecycle_attestation_pause_turn_count": len(
                proactive_lifecycle_attestation_pause_turns
            ),
            "proactive_lifecycle_attestation_archive_turn_count": len(
                proactive_lifecycle_attestation_archive_turns
            ),
            "proactive_lifecycle_attestation_retire_turn_count": len(
                proactive_lifecycle_attestation_retire_turns
            ),
            "proactive_lifecycle_verification_decision_count": len(
                proactive_lifecycle_verification_decisions
            ),
            "proactive_lifecycle_verification_changed_turn_count": len(
                proactive_lifecycle_verification_changed_turns
            ),
            "proactive_lifecycle_verification_verify_turn_count": len(
                proactive_lifecycle_verification_verify_turns
            ),
            "proactive_lifecycle_verification_buffer_turn_count": len(
                proactive_lifecycle_verification_buffer_turns
            ),
            "proactive_lifecycle_verification_pause_turn_count": len(
                proactive_lifecycle_verification_pause_turns
            ),
            "proactive_lifecycle_verification_archive_turn_count": len(
                proactive_lifecycle_verification_archive_turns
            ),
            "proactive_lifecycle_verification_retire_turn_count": len(
                proactive_lifecycle_verification_retire_turns
            ),
            "proactive_lifecycle_certification_decision_count": len(
                proactive_lifecycle_certification_decisions
            ),
            "proactive_lifecycle_certification_changed_turn_count": len(
                proactive_lifecycle_certification_changed_turns
            ),
            "proactive_lifecycle_certification_certify_turn_count": len(
                proactive_lifecycle_certification_certify_turns
            ),
            "proactive_lifecycle_certification_buffer_turn_count": len(
                proactive_lifecycle_certification_buffer_turns
            ),
            "proactive_lifecycle_certification_pause_turn_count": len(
                proactive_lifecycle_certification_pause_turns
            ),
            "proactive_lifecycle_certification_archive_turn_count": len(
                proactive_lifecycle_certification_archive_turns
            ),
            "proactive_lifecycle_certification_retire_turn_count": len(
                proactive_lifecycle_certification_retire_turns
            ),
            "proactive_lifecycle_confirmation_decision_count": len(
                proactive_lifecycle_confirmation_decisions
            ),
            "proactive_lifecycle_confirmation_changed_turn_count": len(
                proactive_lifecycle_confirmation_changed_turns
            ),
            "proactive_lifecycle_confirmation_confirm_turn_count": len(
                proactive_lifecycle_confirmation_confirm_turns
            ),
            "proactive_lifecycle_confirmation_buffer_turn_count": len(
                proactive_lifecycle_confirmation_buffer_turns
            ),
            "proactive_lifecycle_confirmation_pause_turn_count": len(
                proactive_lifecycle_confirmation_pause_turns
            ),
            "proactive_lifecycle_confirmation_archive_turn_count": len(
                proactive_lifecycle_confirmation_archive_turns
            ),
            "proactive_lifecycle_confirmation_retire_turn_count": len(
                proactive_lifecycle_confirmation_retire_turns
            ),
            "proactive_lifecycle_ratification_decision_count": len(
                proactive_lifecycle_ratification_decisions
            ),
            "proactive_lifecycle_ratification_changed_turn_count": len(
                proactive_lifecycle_ratification_changed_turns
            ),
            "proactive_lifecycle_ratification_ratify_turn_count": len(
                proactive_lifecycle_ratification_ratify_turns
            ),
            "proactive_lifecycle_ratification_buffer_turn_count": len(
                proactive_lifecycle_ratification_buffer_turns
            ),
            "proactive_lifecycle_ratification_pause_turn_count": len(
                proactive_lifecycle_ratification_pause_turns
            ),
            "proactive_lifecycle_ratification_archive_turn_count": len(
                proactive_lifecycle_ratification_archive_turns
            ),
            "proactive_lifecycle_ratification_retire_turn_count": len(
                proactive_lifecycle_ratification_retire_turns
            ),
            "proactive_lifecycle_endorsement_decision_count": len(
                proactive_lifecycle_endorsement_decisions
            ),
            "proactive_lifecycle_endorsement_changed_turn_count": len(
                proactive_lifecycle_endorsement_changed_turns
            ),
            "proactive_lifecycle_endorsement_endorse_turn_count": len(
                proactive_lifecycle_endorsement_endorse_turns
            ),
            "proactive_lifecycle_endorsement_buffer_turn_count": len(
                proactive_lifecycle_endorsement_buffer_turns
            ),
            "proactive_lifecycle_endorsement_pause_turn_count": len(
                proactive_lifecycle_endorsement_pause_turns
            ),
            "proactive_lifecycle_endorsement_archive_turn_count": len(
                proactive_lifecycle_endorsement_archive_turns
            ),
            "proactive_lifecycle_endorsement_retire_turn_count": len(
                proactive_lifecycle_endorsement_retire_turns
            ),
            "proactive_lifecycle_authorization_decision_count": len(
                proactive_lifecycle_authorization_decisions
            ),
            "proactive_lifecycle_authorization_changed_turn_count": len(
                proactive_lifecycle_authorization_changed_turns
            ),
            "proactive_lifecycle_authorization_authorize_turn_count": len(
                proactive_lifecycle_authorization_authorize_turns
            ),
            "proactive_lifecycle_authorization_buffer_turn_count": len(
                proactive_lifecycle_authorization_buffer_turns
            ),
            "proactive_lifecycle_authorization_pause_turn_count": len(
                proactive_lifecycle_authorization_pause_turns
            ),
            "proactive_lifecycle_authorization_archive_turn_count": len(
                proactive_lifecycle_authorization_archive_turns
            ),
            "proactive_lifecycle_authorization_retire_turn_count": len(
                proactive_lifecycle_authorization_retire_turns
            ),
            "proactive_lifecycle_enactment_decision_count": len(
                proactive_lifecycle_enactment_decisions
            ),
            "proactive_lifecycle_enactment_changed_turn_count": len(
                proactive_lifecycle_enactment_changed_turns
            ),
            "proactive_lifecycle_enactment_enact_turn_count": len(
                proactive_lifecycle_enactment_enact_turns
            ),
            "proactive_lifecycle_enactment_buffer_turn_count": len(
                proactive_lifecycle_enactment_buffer_turns
            ),
            "proactive_lifecycle_enactment_pause_turn_count": len(
                proactive_lifecycle_enactment_pause_turns
            ),
            "proactive_lifecycle_enactment_archive_turn_count": len(
                proactive_lifecycle_enactment_archive_turns
            ),
            "proactive_lifecycle_enactment_retire_turn_count": len(
                proactive_lifecycle_enactment_retire_turns
            ),
            "proactive_lifecycle_finality_decision_count": len(
                proactive_lifecycle_finality_decisions
            ),
            "proactive_lifecycle_finality_changed_turn_count": len(
                proactive_lifecycle_finality_changed_turns
            ),
            "proactive_lifecycle_finality_finalize_turn_count": len(
                proactive_lifecycle_finality_finalize_turns
            ),
            "proactive_lifecycle_finality_buffer_turn_count": len(
                proactive_lifecycle_finality_buffer_turns
            ),
            "proactive_lifecycle_finality_pause_turn_count": len(
                proactive_lifecycle_finality_pause_turns
            ),
            "proactive_lifecycle_finality_archive_turn_count": len(
                proactive_lifecycle_finality_archive_turns
            ),
            "proactive_lifecycle_finality_retire_turn_count": len(
                proactive_lifecycle_finality_retire_turns
            ),
            "proactive_lifecycle_completion_decision_count": len(
                proactive_lifecycle_completion_decisions
            ),
            "proactive_lifecycle_completion_changed_turn_count": len(
                proactive_lifecycle_completion_changed_turns
            ),
            "proactive_lifecycle_completion_complete_turn_count": len(
                proactive_lifecycle_completion_complete_turns
            ),
            "proactive_lifecycle_completion_buffer_turn_count": len(
                proactive_lifecycle_completion_buffer_turns
            ),
            "proactive_lifecycle_completion_pause_turn_count": len(
                proactive_lifecycle_completion_pause_turns
            ),
            "proactive_lifecycle_completion_archive_turn_count": len(
                proactive_lifecycle_completion_archive_turns
            ),
            "proactive_lifecycle_completion_retire_turn_count": len(
                proactive_lifecycle_completion_retire_turns
            ),
            "proactive_lifecycle_conclusion_decision_count": len(
                proactive_lifecycle_conclusion_decisions
            ),
            "proactive_lifecycle_conclusion_changed_turn_count": len(
                proactive_lifecycle_conclusion_changed_turns
            ),
            "proactive_lifecycle_conclusion_complete_turn_count": len(
                proactive_lifecycle_conclusion_complete_turns
            ),
            "proactive_lifecycle_conclusion_buffer_turn_count": len(
                proactive_lifecycle_conclusion_buffer_turns
            ),
            "proactive_lifecycle_conclusion_pause_turn_count": len(
                proactive_lifecycle_conclusion_pause_turns
            ),
            "proactive_lifecycle_conclusion_archive_turn_count": len(
                proactive_lifecycle_conclusion_archive_turns
            ),
            "proactive_lifecycle_conclusion_retire_turn_count": len(
                proactive_lifecycle_conclusion_retire_turns
            ),
            "proactive_lifecycle_disposition_decision_count": len(
                proactive_lifecycle_disposition_decisions
            ),
            "proactive_lifecycle_disposition_changed_turn_count": len(
                proactive_lifecycle_disposition_changed_turns
            ),
            "proactive_lifecycle_disposition_complete_turn_count": len(
                proactive_lifecycle_disposition_complete_turns
            ),
            "proactive_lifecycle_disposition_buffer_turn_count": len(
                proactive_lifecycle_disposition_buffer_turns
            ),
            "proactive_lifecycle_disposition_pause_turn_count": len(
                proactive_lifecycle_disposition_pause_turns
            ),
            "proactive_lifecycle_disposition_archive_turn_count": len(
                proactive_lifecycle_disposition_archive_turns
            ),
            "proactive_lifecycle_disposition_retire_turn_count": len(
                proactive_lifecycle_disposition_retire_turns
            ),
            "proactive_lifecycle_standing_decision_count": len(
                proactive_lifecycle_standing_decisions
            ),
            "proactive_lifecycle_standing_changed_turn_count": len(
                proactive_lifecycle_standing_changed_turns
            ),
            "proactive_lifecycle_standing_keep_turn_count": len(
                proactive_lifecycle_standing_keep_turns
            ),
            "proactive_lifecycle_standing_buffer_turn_count": len(
                proactive_lifecycle_standing_buffer_turns
            ),
            "proactive_lifecycle_standing_pause_turn_count": len(
                proactive_lifecycle_standing_pause_turns
            ),
            "proactive_lifecycle_standing_archive_turn_count": len(
                proactive_lifecycle_standing_archive_turns
            ),
            "proactive_lifecycle_standing_retire_turn_count": len(
                proactive_lifecycle_standing_retire_turns
            ),
            "proactive_lifecycle_residency_decision_count": len(
                proactive_lifecycle_residency_decisions
            ),
            "proactive_lifecycle_residency_changed_turn_count": len(
                proactive_lifecycle_residency_changed_turns
            ),
            "proactive_lifecycle_residency_keep_turn_count": len(
                proactive_lifecycle_residency_keep_turns
            ),
            "proactive_lifecycle_residency_buffer_turn_count": len(
                proactive_lifecycle_residency_buffer_turns
            ),
            "proactive_lifecycle_residency_pause_turn_count": len(
                proactive_lifecycle_residency_pause_turns
            ),
            "proactive_lifecycle_residency_archive_turn_count": len(
                proactive_lifecycle_residency_archive_turns
            ),
            "proactive_lifecycle_residency_retire_turn_count": len(
                proactive_lifecycle_residency_retire_turns
            ),
            "proactive_lifecycle_tenure_decision_count": len(
                proactive_lifecycle_tenure_decisions
            ),
            "proactive_lifecycle_tenure_changed_turn_count": len(
                proactive_lifecycle_tenure_changed_turns
            ),
            "proactive_lifecycle_tenure_keep_turn_count": len(
                proactive_lifecycle_tenure_keep_turns
            ),
            "proactive_lifecycle_tenure_buffer_turn_count": len(
                proactive_lifecycle_tenure_buffer_turns
            ),
            "proactive_lifecycle_tenure_pause_turn_count": len(
                proactive_lifecycle_tenure_pause_turns
            ),
            "proactive_lifecycle_tenure_archive_turn_count": len(
                proactive_lifecycle_tenure_archive_turns
            ),
            "proactive_lifecycle_tenure_retire_turn_count": len(
                proactive_lifecycle_tenure_retire_turns
            ),
            "proactive_lifecycle_persistence_decision_count": len(
                proactive_lifecycle_persistence_decisions
            ),
            "proactive_lifecycle_persistence_changed_turn_count": len(
                proactive_lifecycle_persistence_changed_turns
            ),
            "proactive_lifecycle_persistence_keep_turn_count": len(
                proactive_lifecycle_persistence_keep_turns
            ),
            "proactive_lifecycle_persistence_buffer_turn_count": len(
                proactive_lifecycle_persistence_buffer_turns
            ),
            "proactive_lifecycle_persistence_pause_turn_count": len(
                proactive_lifecycle_persistence_pause_turns
            ),
            "proactive_lifecycle_persistence_archive_turn_count": len(
                proactive_lifecycle_persistence_archive_turns
            ),
            "proactive_lifecycle_persistence_retire_turn_count": len(
                proactive_lifecycle_persistence_retire_turns
            ),
            "proactive_lifecycle_longevity_decision_count": len(
                proactive_lifecycle_longevity_decisions
            ),
            "proactive_lifecycle_longevity_changed_turn_count": len(
                proactive_lifecycle_longevity_changed_turns
            ),
            "proactive_lifecycle_longevity_keep_turn_count": len(
                proactive_lifecycle_longevity_keep_turns
            ),
            "proactive_lifecycle_longevity_buffer_turn_count": len(
                proactive_lifecycle_longevity_buffer_turns
            ),
            "proactive_lifecycle_longevity_pause_turn_count": len(
                proactive_lifecycle_longevity_pause_turns
            ),
            "proactive_lifecycle_longevity_archive_turn_count": len(
                proactive_lifecycle_longevity_archive_turns
            ),
            "proactive_lifecycle_longevity_retire_turn_count": len(
                proactive_lifecycle_longevity_retire_turns
            ),
            "proactive_lifecycle_legacy_decision_count": len(
                proactive_lifecycle_legacy_decisions
            ),
            "proactive_lifecycle_legacy_changed_turn_count": len(
                proactive_lifecycle_legacy_changed_turns
            ),
            "proactive_lifecycle_legacy_keep_turn_count": len(
                proactive_lifecycle_legacy_keep_turns
            ),
            "proactive_lifecycle_legacy_buffer_turn_count": len(
                proactive_lifecycle_legacy_buffer_turns
            ),
            "proactive_lifecycle_legacy_pause_turn_count": len(
                proactive_lifecycle_legacy_pause_turns
            ),
            "proactive_lifecycle_legacy_archive_turn_count": len(
                proactive_lifecycle_legacy_archive_turns
            ),
            "proactive_lifecycle_legacy_retire_turn_count": len(
                proactive_lifecycle_legacy_retire_turns
            ),
            "proactive_lifecycle_heritage_decision_count": len(
                proactive_lifecycle_heritage_decisions
            ),
            "proactive_lifecycle_heritage_changed_turn_count": len(
                proactive_lifecycle_heritage_changed_turns
            ),
            "proactive_lifecycle_heritage_keep_turn_count": len(
                proactive_lifecycle_heritage_keep_turns
            ),
            "proactive_lifecycle_heritage_buffer_turn_count": len(
                proactive_lifecycle_heritage_buffer_turns
            ),
            "proactive_lifecycle_heritage_pause_turn_count": len(
                proactive_lifecycle_heritage_pause_turns
            ),
            "proactive_lifecycle_heritage_archive_turn_count": len(
                proactive_lifecycle_heritage_archive_turns
            ),
            "proactive_lifecycle_heritage_retire_turn_count": len(
                proactive_lifecycle_heritage_retire_turns
            ),
            "proactive_lifecycle_lineage_decision_count": len(
                proactive_lifecycle_lineage_decisions
            ),
            "proactive_lifecycle_lineage_changed_turn_count": len(
                proactive_lifecycle_lineage_changed_turns
            ),
            "proactive_lifecycle_lineage_keep_turn_count": len(
                proactive_lifecycle_lineage_keep_turns
            ),
            "proactive_lifecycle_lineage_buffer_turn_count": len(
                proactive_lifecycle_lineage_buffer_turns
            ),
            "proactive_lifecycle_lineage_pause_turn_count": len(
                proactive_lifecycle_lineage_pause_turns
            ),
            "proactive_lifecycle_lineage_archive_turn_count": len(
                proactive_lifecycle_lineage_archive_turns
            ),
            "proactive_lifecycle_lineage_retire_turn_count": len(
                proactive_lifecycle_lineage_retire_turns
            ),
            "proactive_lifecycle_ancestry_decision_count": len(
                proactive_lifecycle_ancestry_decisions
            ),
            "proactive_lifecycle_ancestry_changed_turn_count": len(
                proactive_lifecycle_ancestry_changed_turns
            ),
            "proactive_lifecycle_ancestry_keep_turn_count": len(
                proactive_lifecycle_ancestry_keep_turns
            ),
            "proactive_lifecycle_ancestry_buffer_turn_count": len(
                proactive_lifecycle_ancestry_buffer_turns
            ),
            "proactive_lifecycle_ancestry_pause_turn_count": len(
                proactive_lifecycle_ancestry_pause_turns
            ),
            "proactive_lifecycle_ancestry_archive_turn_count": len(
                proactive_lifecycle_ancestry_archive_turns
            ),
            "proactive_lifecycle_ancestry_retire_turn_count": len(
                proactive_lifecycle_ancestry_retire_turns
            ),
            "proactive_lifecycle_provenance_decision_count": len(
                proactive_lifecycle_provenance_decisions
            ),
            "proactive_lifecycle_provenance_changed_turn_count": len(
                proactive_lifecycle_provenance_changed_turns
            ),
            "proactive_lifecycle_provenance_keep_turn_count": len(
                proactive_lifecycle_provenance_keep_turns
            ),
            "proactive_lifecycle_provenance_buffer_turn_count": len(
                proactive_lifecycle_provenance_buffer_turns
            ),
            "proactive_lifecycle_provenance_pause_turn_count": len(
                proactive_lifecycle_provenance_pause_turns
            ),
            "proactive_lifecycle_provenance_archive_turn_count": len(
                proactive_lifecycle_provenance_archive_turns
            ),
            "proactive_lifecycle_provenance_retire_turn_count": len(
                proactive_lifecycle_provenance_retire_turns
            ),
            "proactive_lifecycle_origin_decision_count": len(
                proactive_lifecycle_origin_decisions
            ),
            "proactive_lifecycle_origin_changed_turn_count": len(
                proactive_lifecycle_origin_changed_turns
            ),
            "proactive_lifecycle_origin_keep_turn_count": len(
                proactive_lifecycle_origin_keep_turns
            ),
            "proactive_lifecycle_origin_buffer_turn_count": len(
                proactive_lifecycle_origin_buffer_turns
            ),
            "proactive_lifecycle_origin_pause_turn_count": len(
                proactive_lifecycle_origin_pause_turns
            ),
            "proactive_lifecycle_origin_archive_turn_count": len(
                proactive_lifecycle_origin_archive_turns
            ),
            "proactive_lifecycle_origin_retire_turn_count": len(
                proactive_lifecycle_origin_retire_turns
            ),
            "proactive_lifecycle_root_decision_count": len(
                proactive_lifecycle_root_decisions
            ),
            "proactive_lifecycle_root_changed_turn_count": len(
                proactive_lifecycle_root_changed_turns
            ),
            "proactive_lifecycle_root_keep_turn_count": len(
                proactive_lifecycle_root_keep_turns
            ),
            "proactive_lifecycle_root_buffer_turn_count": len(
                proactive_lifecycle_root_buffer_turns
            ),
            "proactive_lifecycle_root_pause_turn_count": len(
                proactive_lifecycle_root_pause_turns
            ),
            "proactive_lifecycle_root_archive_turn_count": len(
                proactive_lifecycle_root_archive_turns
            ),
            "proactive_lifecycle_root_retire_turn_count": len(
                proactive_lifecycle_root_retire_turns
            ),
            "proactive_lifecycle_foundation_decision_count": len(
                proactive_lifecycle_foundation_decisions
            ),
            "proactive_lifecycle_foundation_changed_turn_count": len(
                proactive_lifecycle_foundation_changed_turns
            ),
            "proactive_lifecycle_foundation_keep_turn_count": len(
                proactive_lifecycle_foundation_keep_turns
            ),
            "proactive_lifecycle_foundation_buffer_turn_count": len(
                proactive_lifecycle_foundation_buffer_turns
            ),
            "proactive_lifecycle_foundation_pause_turn_count": len(
                proactive_lifecycle_foundation_pause_turns
            ),
            "proactive_lifecycle_foundation_archive_turn_count": len(
                proactive_lifecycle_foundation_archive_turns
            ),
            "proactive_lifecycle_foundation_retire_turn_count": len(
                proactive_lifecycle_foundation_retire_turns
            ),
            "proactive_lifecycle_bedrock_decision_count": len(
                proactive_lifecycle_bedrock_decisions
            ),
            "proactive_lifecycle_bedrock_changed_turn_count": len(
                proactive_lifecycle_bedrock_changed_turns
            ),
            "proactive_lifecycle_bedrock_keep_turn_count": len(
                proactive_lifecycle_bedrock_keep_turns
            ),
            "proactive_lifecycle_bedrock_buffer_turn_count": len(
                proactive_lifecycle_bedrock_buffer_turns
            ),
            "proactive_lifecycle_bedrock_pause_turn_count": len(
                proactive_lifecycle_bedrock_pause_turns
            ),
            "proactive_lifecycle_bedrock_archive_turn_count": len(
                proactive_lifecycle_bedrock_archive_turns
            ),
            "proactive_lifecycle_bedrock_retire_turn_count": len(
                proactive_lifecycle_bedrock_retire_turns
            ),
            "proactive_lifecycle_substrate_decision_count": len(
                proactive_lifecycle_substrate_decisions
            ),
            "proactive_lifecycle_substrate_changed_turn_count": len(
                proactive_lifecycle_substrate_changed_turns
            ),
            "proactive_lifecycle_substrate_keep_turn_count": len(
                proactive_lifecycle_substrate_keep_turns
            ),
            "proactive_lifecycle_substrate_buffer_turn_count": len(
                proactive_lifecycle_substrate_buffer_turns
            ),
            "proactive_lifecycle_substrate_pause_turn_count": len(
                proactive_lifecycle_substrate_pause_turns
            ),
            "proactive_lifecycle_substrate_archive_turn_count": len(
                proactive_lifecycle_substrate_archive_turns
            ),
            "proactive_lifecycle_substrate_retire_turn_count": len(
                proactive_lifecycle_substrate_retire_turns
            ),
            "proactive_lifecycle_stratum_decision_count": len(
                proactive_lifecycle_stratum_decisions
            ),
            "proactive_lifecycle_stratum_changed_turn_count": len(
                proactive_lifecycle_stratum_changed_turns
            ),
            "proactive_lifecycle_stratum_keep_turn_count": len(
                proactive_lifecycle_stratum_keep_turns
            ),
            "proactive_lifecycle_stratum_buffer_turn_count": len(
                proactive_lifecycle_stratum_buffer_turns
            ),
            "proactive_lifecycle_stratum_pause_turn_count": len(
                proactive_lifecycle_stratum_pause_turns
            ),
            "proactive_lifecycle_stratum_archive_turn_count": len(
                proactive_lifecycle_stratum_archive_turns
            ),
            "proactive_lifecycle_stratum_retire_turn_count": len(
                proactive_lifecycle_stratum_retire_turns
            ),
            "proactive_lifecycle_layer_decision_count": len(
                proactive_lifecycle_layer_decisions
            ),
            "proactive_lifecycle_layer_changed_turn_count": len(
                proactive_lifecycle_layer_changed_turns
            ),
            "proactive_lifecycle_layer_keep_turn_count": len(
                proactive_lifecycle_layer_keep_turns
            ),
            "proactive_lifecycle_layer_buffer_turn_count": len(
                proactive_lifecycle_layer_buffer_turns
            ),
            "proactive_lifecycle_layer_pause_turn_count": len(
                proactive_lifecycle_layer_pause_turns
            ),
            "proactive_lifecycle_layer_archive_turn_count": len(
                proactive_lifecycle_layer_archive_turns
            ),
            "proactive_lifecycle_layer_retire_turn_count": len(
                proactive_lifecycle_layer_retire_turns
            ),
            "proactive_lifecycle_durability_decision_count": len(
                proactive_lifecycle_durability_decisions
            ),
            "proactive_lifecycle_durability_changed_turn_count": len(
                proactive_lifecycle_durability_changed_turns
            ),
            "proactive_lifecycle_durability_keep_turn_count": len(
                proactive_lifecycle_durability_keep_turns
            ),
            "proactive_lifecycle_durability_buffer_turn_count": len(
                proactive_lifecycle_durability_buffer_turns
            ),
            "proactive_lifecycle_durability_pause_turn_count": len(
                proactive_lifecycle_durability_pause_turns
            ),
            "proactive_lifecycle_durability_archive_turn_count": len(
                proactive_lifecycle_durability_archive_turns
            ),
            "proactive_lifecycle_durability_retire_turn_count": len(
                proactive_lifecycle_durability_retire_turns
            ),
            "proactive_stage_refresh_plan_count": len(proactive_stage_refresh_plans),
            "proactive_stage_refresh_changed_turn_count": len(
                proactive_stage_refresh_changed_turns
            ),
            "proactive_stage_replan_assessment_count": len(
                proactive_stage_replan_assessments
            ),
            "proactive_stage_replan_changed_turn_count": len(
                proactive_stage_replan_changed_turns
            ),
            "proactive_aggregate_governance_assessment_count": len(
                proactive_aggregate_governance_assessments
            ),
            "proactive_aggregate_governance_watch_turn_count": len(
                proactive_aggregate_governance_watch_turns
            ),
            "proactive_aggregate_governance_recenter_turn_count": len(
                proactive_aggregate_governance_recenter_turns
            ),
            "proactive_aggregate_controller_decision_count": len(
                proactive_aggregate_controller_decisions
            ),
            "proactive_aggregate_controller_changed_turn_count": len(
                proactive_aggregate_controller_changed_turns
            ),
            "proactive_orchestration_controller_decision_count": len(
                proactive_orchestration_controller_decisions
            ),
            "proactive_orchestration_controller_changed_turn_count": len(
                proactive_orchestration_controller_changed_turns
            ),
            "proactive_dispatch_feedback_assessment_count": len(
                proactive_dispatch_feedback_assessments
            ),
            "proactive_dispatch_feedback_changed_turn_count": len(
                proactive_dispatch_feedback_changed_turns
            ),
            "proactive_dispatch_gate_decision_count": len(
                proactive_dispatch_gate_decisions
            ),
            "proactive_dispatch_gate_deferred_turn_count": len(
                proactive_dispatch_gate_deferred_turns
            ),
            "proactive_dispatch_envelope_decision_count": len(
                proactive_dispatch_envelope_decisions
            ),
            "proactive_dispatch_envelope_changed_turn_count": len(
                proactive_dispatch_envelope_changed_turns
            ),
            "proactive_stage_state_decision_count": len(
                proactive_stage_state_decisions
            ),
            "proactive_stage_state_changed_turn_count": len(
                proactive_stage_state_changed_turns
            ),
            "proactive_stage_transition_decision_count": len(
                proactive_stage_transition_decisions
            ),
            "proactive_stage_transition_changed_turn_count": len(
                proactive_stage_transition_changed_turns
            ),
            "proactive_stage_transition_rescheduled_turn_count": len(
                proactive_stage_transition_rescheduled_turns
            ),
            "proactive_stage_transition_terminal_turn_count": len(
                proactive_stage_transition_terminal_turns
            ),
            "proactive_stage_machine_decision_count": len(
                proactive_stage_machine_decisions
            ),
            "proactive_stage_machine_changed_turn_count": len(
                proactive_stage_machine_changed_turns
            ),
            "proactive_stage_machine_buffered_turn_count": len(
                proactive_stage_machine_buffered_turns
            ),
            "proactive_stage_machine_terminal_turn_count": len(
                proactive_stage_machine_terminal_turns
            ),
            "reengagement_matrix_assessment_count": len(
                reengagement_matrix_assessments
            ),
            "reengagement_matrix_blocked_turn_count": len(
                reengagement_matrix_blocked_turns
            ),
            "reengagement_plan_count": len(reengagement_plans),
            "reengagement_two_part_turn_count": len(reengagement_two_part_turns),
            "reengagement_repair_bridge_turn_count": len(
                reengagement_repair_bridge_turns
            ),
            "reengagement_somatic_action_turn_count": len(
                reengagement_somatic_action_turns
            ),
            "proactive_followup_dispatch_count": len(proactive_dispatch_turns),
            "proactive_followup_dispatch_progression_advanced_count": len(
                proactive_progression_advanced_dispatch_turns
            ),
            "proactive_followup_message_event_count": sum(
                turn.proactive_followup_message_event_count for turn in turn_records
            ),
            "somatic_cue_turn_count": len(somatic_cue_turns),
            "runtime_quality_doctor_report_count": len(
                runtime_quality_doctor_reports
            ),
            "runtime_quality_doctor_watch_count": len(
                runtime_quality_doctor_watch_turns
            ),
            "runtime_quality_doctor_revise_count": len(
                runtime_quality_doctor_revise_turns
            ),
            "runtime_quality_doctor_issue_total": sum(
                int((turn.runtime_quality_doctor_report or {}).get("issue_count", 0))
                for turn in runtime_quality_doctor_reports
            ),
            "system3_snapshot_count": len(system3_snapshots),
            "system3_identity_watch_turn_count": len(system3_identity_watch_turns),
            "system3_identity_trajectory_watch_turn_count": len(
                identity_trajectory_watch_turns
            ),
            "system3_identity_trajectory_recenter_turn_count": len(
                identity_trajectory_recenter_turns
            ),
            "system3_emotional_debt_watch_turn_count": len(
                emotional_debt_watch_turns
            ),
            "system3_emotional_debt_elevated_turn_count": len(
                emotional_debt_elevated_turns
            ),
            "system3_emotional_debt_trajectory_watch_turn_count": len(
                emotional_debt_trajectory_watch_turns
            ),
            "system3_emotional_debt_trajectory_decompression_turn_count": len(
                emotional_debt_trajectory_decompression_turns
            ),
            "system3_strategy_audit_watch_turn_count": len(
                strategy_audit_watch_turns
            ),
            "system3_strategy_audit_revise_turn_count": len(
                strategy_audit_revise_turns
            ),
            "system3_strategy_audit_trajectory_watch_turn_count": len(
                strategy_audit_trajectory_watch_turns
            ),
            "system3_strategy_audit_trajectory_corrective_turn_count": len(
                strategy_audit_trajectory_corrective_turns
            ),
            "system3_strategy_supervision_watch_turn_count": len(
                strategy_supervision_watch_turns
            ),
            "system3_strategy_supervision_revise_turn_count": len(
                strategy_supervision_revise_turns
            ),
            "system3_strategy_supervision_trajectory_watch_turn_count": len(
                strategy_supervision_trajectory_watch_turns
            ),
            "system3_strategy_supervision_trajectory_tighten_turn_count": len(
                strategy_supervision_trajectory_tighten_turns
            ),
            "system3_moral_reasoning_watch_turn_count": len(
                moral_reasoning_watch_turns
            ),
            "system3_moral_reasoning_revise_turn_count": len(
                moral_reasoning_revise_turns
            ),
            "system3_moral_trajectory_watch_turn_count": len(
                moral_trajectory_watch_turns
            ),
            "system3_moral_trajectory_recenter_turn_count": len(
                moral_trajectory_recenter_turns
            ),
            "system3_user_model_evolution_watch_turn_count": len(
                [
                    turn
                    for turn in system3_snapshots
                    if (turn.system3_snapshot or {}).get("user_model_evolution_status")
                    in {"watch", "revise"}
                ]
            ),
            "system3_user_model_evolution_revise_turn_count": len(
                [
                    turn
                    for turn in system3_snapshots
                    if (turn.system3_snapshot or {}).get("user_model_evolution_status")
                    == "revise"
                ]
            ),
            "system3_user_model_trajectory_watch_turn_count": len(
                user_model_trajectory_watch_turns
            ),
            "system3_user_model_trajectory_recenter_turn_count": len(
                user_model_trajectory_recenter_turns
            ),
            "system3_expectation_calibration_watch_turn_count": len(
                expectation_calibration_watch_turns
            ),
            "system3_expectation_calibration_revise_turn_count": len(
                expectation_calibration_revise_turns
            ),
            "system3_expectation_calibration_trajectory_watch_turn_count": len(
                expectation_calibration_trajectory_watch_turns
            ),
            "system3_expectation_calibration_trajectory_reset_turn_count": len(
                expectation_calibration_trajectory_reset_turns
            ),
            "system3_dependency_governance_watch_turn_count": len(
                dependency_governance_watch_turns
            ),
            "system3_dependency_governance_revise_turn_count": len(
                dependency_governance_revise_turns
            ),
            "system3_dependency_governance_trajectory_watch_turn_count": len(
                dependency_governance_trajectory_watch_turns
            ),
            "system3_dependency_governance_trajectory_recenter_turn_count": len(
                dependency_governance_trajectory_recenter_turns
            ),
            "system3_autonomy_governance_watch_turn_count": len(
                autonomy_governance_watch_turns
            ),
            "system3_autonomy_governance_revise_turn_count": len(
                autonomy_governance_revise_turns
            ),
            "system3_autonomy_governance_trajectory_watch_turn_count": len(
                autonomy_governance_trajectory_watch_turns
            ),
            "system3_autonomy_governance_trajectory_recenter_turn_count": len(
                autonomy_governance_trajectory_recenter_turns
            ),
            "system3_boundary_governance_watch_turn_count": len(
                boundary_governance_watch_turns
            ),
            "system3_boundary_governance_revise_turn_count": len(
                boundary_governance_revise_turns
            ),
            "system3_boundary_governance_trajectory_watch_turn_count": len(
                boundary_governance_trajectory_watch_turns
            ),
            "system3_boundary_governance_trajectory_recenter_turn_count": len(
                boundary_governance_trajectory_recenter_turns
            ),
            "system3_support_governance_watch_turn_count": len(
                support_governance_watch_turns
            ),
            "system3_support_governance_revise_turn_count": len(
                support_governance_revise_turns
            ),
            "system3_support_governance_trajectory_watch_turn_count": len(
                support_governance_trajectory_watch_turns
            ),
            "system3_support_governance_trajectory_recenter_turn_count": len(
                support_governance_trajectory_recenter_turns
            ),
            "system3_continuity_governance_watch_turn_count": len(
                continuity_governance_watch_turns
            ),
            "system3_continuity_governance_revise_turn_count": len(
                continuity_governance_revise_turns
            ),
            "system3_continuity_governance_trajectory_watch_turn_count": len(
                continuity_governance_trajectory_watch_turns
            ),
            "system3_continuity_governance_trajectory_recenter_turn_count": len(
                continuity_governance_trajectory_recenter_turns
            ),
            "system3_repair_governance_watch_turn_count": len(
                repair_governance_watch_turns
            ),
            "system3_repair_governance_revise_turn_count": len(
                repair_governance_revise_turns
            ),
            "system3_repair_governance_trajectory_watch_turn_count": len(
                repair_governance_trajectory_watch_turns
            ),
            "system3_repair_governance_trajectory_recenter_turn_count": len(
                repair_governance_trajectory_recenter_turns
            ),
            "system3_attunement_governance_watch_turn_count": len(
                attunement_governance_watch_turns
            ),
            "system3_attunement_governance_revise_turn_count": len(
                attunement_governance_revise_turns
            ),
            "system3_attunement_governance_trajectory_watch_turn_count": len(
                attunement_governance_trajectory_watch_turns
            ),
            "system3_attunement_governance_trajectory_recenter_turn_count": len(
                attunement_governance_trajectory_recenter_turns
            ),
            "system3_trust_governance_watch_turn_count": len(
                trust_governance_watch_turns
            ),
            "system3_trust_governance_revise_turn_count": len(
                trust_governance_revise_turns
            ),
            "system3_trust_governance_trajectory_watch_turn_count": len(
                trust_governance_trajectory_watch_turns
            ),
            "system3_trust_governance_trajectory_recenter_turn_count": len(
                trust_governance_trajectory_recenter_turns
            ),
            "system3_clarity_governance_watch_turn_count": len(
                clarity_governance_watch_turns
            ),
            "system3_clarity_governance_revise_turn_count": len(
                clarity_governance_revise_turns
            ),
            "system3_clarity_governance_trajectory_watch_turn_count": len(
                clarity_governance_trajectory_watch_turns
            ),
            "system3_clarity_governance_trajectory_recenter_turn_count": len(
                clarity_governance_trajectory_recenter_turns
            ),
            "system3_pacing_governance_watch_turn_count": len(
                pacing_governance_watch_turns
            ),
            "system3_pacing_governance_revise_turn_count": len(
                pacing_governance_revise_turns
            ),
            "system3_pacing_governance_trajectory_watch_turn_count": len(
                pacing_governance_trajectory_watch_turns
            ),
            "system3_pacing_governance_trajectory_recenter_turn_count": len(
                pacing_governance_trajectory_recenter_turns
            ),
            "system3_commitment_governance_watch_turn_count": len(
                commitment_governance_watch_turns
            ),
            "system3_commitment_governance_revise_turn_count": len(
                commitment_governance_revise_turns
            ),
            "system3_commitment_governance_trajectory_watch_turn_count": len(
                commitment_governance_trajectory_watch_turns
            ),
            "system3_commitment_governance_trajectory_recenter_turn_count": len(
                commitment_governance_trajectory_recenter_turns
            ),
            "system3_disclosure_governance_watch_turn_count": len(
                disclosure_governance_watch_turns
            ),
            "system3_disclosure_governance_revise_turn_count": len(
                disclosure_governance_revise_turns
            ),
            "system3_disclosure_governance_trajectory_watch_turn_count": len(
                disclosure_governance_trajectory_watch_turns
            ),
            "system3_disclosure_governance_trajectory_recenter_turn_count": len(
                disclosure_governance_trajectory_recenter_turns
            ),
            "system3_reciprocity_governance_watch_turn_count": len(
                reciprocity_governance_watch_turns
            ),
            "system3_reciprocity_governance_revise_turn_count": len(
                reciprocity_governance_revise_turns
            ),
            "system3_reciprocity_governance_trajectory_watch_turn_count": len(
                reciprocity_governance_trajectory_watch_turns
            ),
            "system3_reciprocity_governance_trajectory_recenter_turn_count": len(
                reciprocity_governance_trajectory_recenter_turns
            ),
            "system3_pressure_governance_watch_turn_count": len(
                pressure_governance_watch_turns
            ),
            "system3_pressure_governance_revise_turn_count": len(
                pressure_governance_revise_turns
            ),
            "system3_pressure_governance_trajectory_watch_turn_count": len(
                pressure_governance_trajectory_watch_turns
            ),
            "system3_pressure_governance_trajectory_recenter_turn_count": len(
                pressure_governance_trajectory_recenter_turns
            ),
            "system3_relational_governance_watch_turn_count": len(
                relational_governance_watch_turns
            ),
            "system3_relational_governance_revise_turn_count": len(
                relational_governance_revise_turns
            ),
            "system3_relational_governance_trajectory_watch_turn_count": len(
                relational_governance_trajectory_watch_turns
            ),
            "system3_relational_governance_trajectory_recenter_turn_count": len(
                relational_governance_trajectory_recenter_turns
            ),
            "system3_safety_governance_watch_turn_count": len(
                safety_governance_watch_turns
            ),
            "system3_safety_governance_revise_turn_count": len(
                safety_governance_revise_turns
            ),
            "system3_safety_governance_trajectory_watch_turn_count": len(
                safety_governance_trajectory_watch_turns
            ),
            "system3_safety_governance_trajectory_recenter_turn_count": len(
                safety_governance_trajectory_recenter_turns
            ),
            "system3_progress_governance_watch_turn_count": len(
                progress_governance_watch_turns
            ),
            "system3_progress_governance_revise_turn_count": len(
                progress_governance_revise_turns
            ),
            "system3_progress_governance_trajectory_watch_turn_count": len(
                progress_governance_trajectory_watch_turns
            ),
            "system3_progress_governance_trajectory_recenter_turn_count": len(
                progress_governance_trajectory_recenter_turns
            ),
            "system3_stability_governance_watch_turn_count": len(
                stability_governance_watch_turns
            ),
            "system3_stability_governance_revise_turn_count": len(
                stability_governance_revise_turns
            ),
            "system3_stability_governance_trajectory_watch_turn_count": len(
                stability_governance_trajectory_watch_turns
            ),
            "system3_stability_governance_trajectory_recenter_turn_count": len(
                stability_governance_trajectory_recenter_turns
            ),
            "system3_growth_transition_watch_turn_count": len(
                growth_transition_watch_turns
            ),
            "system3_growth_transition_ready_turn_count": len(
                growth_transition_ready_turns
            ),
            "system3_growth_transition_trajectory_watch_turn_count": len(
                growth_transition_trajectory_watch_turns
            ),
            "system3_growth_transition_trajectory_advance_turn_count": len(
                growth_transition_trajectory_advance_turns
            ),
            "system3_growth_transition_trajectory_redirect_turn_count": len(
                growth_transition_trajectory_redirect_turns
            ),
            "system3_version_migration_watch_turn_count": len(
                version_migration_watch_turns
            ),
            "system3_version_migration_revise_turn_count": len(
                version_migration_revise_turns
            ),
            "system3_version_migration_trajectory_watch_turn_count": len(
                version_migration_trajectory_watch_turns
            ),
            "system3_version_migration_trajectory_hold_turn_count": len(
                version_migration_trajectory_hold_turns
            ),
            "response_post_audit_review_turn_count": len(
                response_post_audit_review_turns
            ),
            "response_post_audit_revise_turn_count": len(
                response_post_audit_revise_turns
            ),
            "response_post_audit_total_violation_count": sum(
                len((turn.response_post_audit or {}).get("violations", []))
                for turn in turn_records
            ),
            "strategy_diversity_assessed_turn_count": len(strategy_names),
            "strategy_diversity_unique_strategy_count": len(set(strategy_names)),
            "strategy_diversity_index": strategy_diversity_index,
            "strategy_diversity_watch_turn_count": len(diversity_watch_turns),
            "strategy_diversity_intervention_turn_count": len(
                diversity_intervention_turns
            ),
            "response_normalization_changed_turn_count": len(
                response_normalization_changed_turns
            ),
            "response_normalization_repair_count": sum(
                len((turn.response_normalization or {}).get("applied_repairs", []))
                for turn in turn_records
            ),
            "memory_recall_turn_count": len(recalled_turns),
            "memory_recall_filtered_turn_count": len(filtered_recall_turns),
            "memory_write_guard_turn_count": len(blocked_memory_turns),
            "memory_write_guard_blocked_count": sum(
                int((turn.memory_write_guard or {}).get("blocked_count", 0))
                for turn in turn_records
            ),
            "memory_retention_turn_count": len(retention_turns),
            "memory_retention_pinned_count": sum(
                int((turn.memory_retention or {}).get("pinned_count", 0))
                for turn in turn_records
            ),
            "memory_forgetting_turn_count": len(forgetting_turns),
            "memory_forgetting_evicted_count": sum(
                int((turn.memory_forgetting or {}).get("evicted_count", 0))
                for turn in turn_records
            ),
            "avg_psychological_safety": round(mean(safety_scores), 3) if safety_scores else None,
            "latest_strategy": latest_strategy,
            "latest_strategy_source": latest_strategy_source,
            "latest_strategy_diversity_status": latest_strategy_diversity_status,
            "latest_strategy_diversity_entropy": round(
                latest_strategy_diversity_entropy,
                3,
            ),
            "latest_confidence_level": latest_confidence_level,
            "latest_confidence_response_mode": latest_confidence_response_mode,
            "latest_boundary_decision": latest_boundary_decision,
            "latest_policy_path": latest_policy_path,
            "latest_rehearsal_risk": latest_rehearsal_risk,
            "latest_empowerment_audit_status": latest_empowerment_audit_status,
            "latest_drafting_question_strategy": latest_drafting_question_strategy,
            "latest_drafting_opening_move": latest_drafting_opening_move,
            "latest_rendering_mode": latest_rendering_mode,
            "latest_rendering_max_sentences": latest_rendering_max_sentences,
            "latest_response_sequence_mode": latest_response_sequence_mode,
            "latest_response_sequence_unit_count": latest_response_sequence_unit_count,
            "latest_time_awareness_mode": latest_time_awareness_mode,
            "latest_ritual_phase": latest_ritual_phase,
            "latest_cognitive_load_band": latest_cognitive_load_band,
            "latest_guidance_mode": latest_guidance_mode,
            "latest_guidance_lead_with": latest_guidance_lead_with,
            "latest_guidance_pacing": latest_guidance_pacing,
            "latest_guidance_step_budget": latest_guidance_step_budget,
            "latest_guidance_agency_mode": latest_guidance_agency_mode,
            "latest_guidance_ritual_action": latest_guidance_ritual_action,
            "latest_guidance_checkpoint_style": latest_guidance_checkpoint_style,
            "latest_guidance_handoff_mode": latest_guidance_handoff_mode,
            "latest_guidance_carryover_mode": latest_guidance_carryover_mode,
            "latest_cadence_status": latest_cadence_status,
            "latest_cadence_turn_shape": latest_cadence_turn_shape,
            "latest_cadence_ritual_depth": latest_cadence_ritual_depth,
            "latest_cadence_followup_tempo": latest_cadence_followup_tempo,
            "latest_cadence_user_space_mode": latest_cadence_user_space_mode,
            "latest_cadence_transition_intent": latest_cadence_transition_intent,
            "latest_cadence_next_checkpoint": latest_cadence_next_checkpoint,
            "latest_session_ritual_phase": latest_session_ritual_phase,
            "latest_session_ritual_opening_move": latest_session_ritual_opening_move,
            "latest_session_ritual_bridge_move": latest_session_ritual_bridge_move,
            "latest_session_ritual_closing_move": latest_session_ritual_closing_move,
            "latest_session_ritual_continuity_anchor": (
                latest_session_ritual_continuity_anchor
            ),
            "latest_session_ritual_somatic_shortcut": (
                latest_session_ritual_somatic_shortcut
            ),
            "latest_somatic_orchestration_status": (
                latest_somatic_orchestration_status
            ),
            "latest_somatic_orchestration_mode": latest_somatic_orchestration_mode,
            "latest_somatic_orchestration_body_anchor": (
                latest_somatic_orchestration_body_anchor
            ),
            "latest_somatic_orchestration_followup_style": (
                latest_somatic_orchestration_followup_style
            ),
            "latest_response_budget_mode": latest_response_budget_mode,
            "latest_proactive_followup_eligible": (
                latest_proactive_followup_eligible
            ),
            "latest_proactive_style": latest_proactive_style,
            "latest_somatic_cue": latest_somatic_cue,
            "latest_proactive_followup_status": latest_proactive_followup_status,
            "latest_proactive_followup_style": latest_proactive_followup_style,
            "latest_proactive_followup_after_seconds": (
                latest_proactive_followup_after_seconds
            ),
            "latest_proactive_cadence_status": latest_proactive_cadence_status,
            "latest_proactive_cadence_key": latest_proactive_cadence_key,
            "latest_proactive_cadence_stage_count": latest_proactive_cadence_stage_count,
            "latest_proactive_aggregate_governance_status": (
                latest_proactive_aggregate_governance_status
            ),
            "latest_proactive_aggregate_governance_primary_domain": (
                latest_proactive_aggregate_governance_primary_domain
            ),
            "latest_proactive_aggregate_governance_summary": (
                latest_proactive_aggregate_governance_summary
            ),
            "latest_proactive_aggregate_governance_domain_count": (
                latest_proactive_aggregate_governance_domain_count
            ),
            "latest_proactive_aggregate_controller_key": (
                latest_proactive_aggregate_controller_key
            ),
            "latest_proactive_aggregate_controller_decision": (
                latest_proactive_aggregate_controller_decision
            ),
            "latest_proactive_aggregate_controller_stage_delay_seconds": (
                latest_proactive_aggregate_controller_stage_delay_seconds
            ),
            "latest_proactive_aggregate_controller_line_delay_seconds": (
                latest_proactive_aggregate_controller_line_delay_seconds
            ),
            "latest_proactive_aggregate_controller_retry_after_seconds": (
                latest_proactive_aggregate_controller_retry_after_seconds
            ),
            "latest_proactive_orchestration_controller_key": (
                latest_proactive_orchestration_controller_key
            ),
            "latest_proactive_orchestration_controller_decision": (
                latest_proactive_orchestration_controller_decision
            ),
            "latest_proactive_orchestration_controller_stage_delay_seconds": (
                latest_proactive_orchestration_controller_stage_delay_seconds
            ),
            "latest_proactive_orchestration_controller_line_delay_seconds": (
                latest_proactive_orchestration_controller_line_delay_seconds
            ),
            "latest_proactive_orchestration_controller_retry_after_seconds": (
                latest_proactive_orchestration_controller_retry_after_seconds
            ),
            "latest_proactive_orchestration_controller_primary_source": (
                latest_proactive_orchestration_controller_primary_source
            ),
            "latest_proactive_guardrail_key": latest_proactive_guardrail_key,
            "latest_proactive_guardrail_max_dispatch_count": (
                latest_proactive_guardrail_max_dispatch_count
            ),
            "latest_proactive_guardrail_hard_stop_count": (
                latest_proactive_guardrail_hard_stop_count
            ),
            "latest_proactive_guardrail_second_touch_min_user_seconds": (
                latest_proactive_guardrail_second_touch_min_user_seconds
            ),
            "latest_proactive_scheduling_mode": latest_proactive_scheduling_mode,
            "latest_proactive_scheduling_min_seconds_since_last_outbound": (
                latest_proactive_scheduling_min_seconds_since_last_outbound
            ),
            "latest_proactive_scheduling_first_touch_extra_delay_seconds": (
                latest_proactive_scheduling_first_touch_extra_delay_seconds
            ),
            "latest_proactive_orchestration_key": latest_proactive_orchestration_key,
            "latest_proactive_orchestration_close_loop_stage": (
                latest_proactive_orchestration_close_loop_stage
            ),
            "latest_proactive_orchestration_second_touch_delivery_mode": (
                latest_proactive_orchestration_second_touch_delivery_mode
            ),
            "latest_proactive_orchestration_second_touch_question_mode": (
                latest_proactive_orchestration_second_touch_question_mode
            ),
            "latest_proactive_actuation_key": latest_proactive_actuation_key,
            "latest_proactive_actuation_second_touch_opening_move": (
                latest_proactive_actuation_second_touch_opening_move
            ),
            "latest_proactive_actuation_second_touch_bridge_move": (
                latest_proactive_actuation_second_touch_bridge_move
            ),
            "latest_proactive_actuation_second_touch_somatic_mode": (
                latest_proactive_actuation_second_touch_somatic_mode
            ),
            "latest_proactive_actuation_second_touch_user_space_signal": (
                latest_proactive_actuation_second_touch_user_space_signal
            ),
            "latest_proactive_actuation_final_touch_closing_move": (
                latest_proactive_actuation_final_touch_closing_move
            ),
            "latest_proactive_progression_key": latest_proactive_progression_key,
            "latest_proactive_progression_second_touch_action": (
                latest_proactive_progression_second_touch_action
            ),
            "latest_proactive_progression_final_touch_action": (
                latest_proactive_progression_final_touch_action
            ),
            "latest_proactive_stage_controller_key": (
                latest_proactive_stage_controller_key
            ),
            "latest_proactive_stage_controller_decision": (
                latest_proactive_stage_controller_decision
            ),
            "latest_proactive_stage_controller_target_stage_label": (
                latest_proactive_stage_controller_target_stage_label
            ),
            "latest_proactive_stage_controller_additional_delay_seconds": (
                latest_proactive_stage_controller_additional_delay_seconds
            ),
            "latest_proactive_stage_controller_strategy_key": (
                latest_proactive_stage_controller_strategy_key
            ),
            "latest_proactive_stage_controller_changed": (
                latest_proactive_stage_controller_changed
            ),
            "latest_proactive_line_controller_key": (
                latest_proactive_line_controller_key
            ),
            "latest_proactive_line_controller_decision": (
                latest_proactive_line_controller_decision
            ),
            "latest_proactive_line_controller_line_state": (
                latest_proactive_line_controller_line_state
            ),
            "latest_proactive_line_controller_additional_delay_seconds": (
                latest_proactive_line_controller_additional_delay_seconds
            ),
            "latest_proactive_line_controller_changed": (
                latest_proactive_line_controller_changed
            ),
            "latest_proactive_line_state_key": latest_proactive_line_state_key,
            "latest_proactive_line_state_mode": latest_proactive_line_state_mode,
            "latest_proactive_line_state_lifecycle": (
                latest_proactive_line_state_lifecycle
            ),
            "latest_proactive_line_state_actionability": (
                latest_proactive_line_state_actionability
            ),
            "latest_proactive_line_state_source": (
                latest_proactive_line_state_source
            ),
            "latest_proactive_line_transition_key": (
                latest_proactive_line_transition_key
            ),
            "latest_proactive_line_transition_mode": (
                latest_proactive_line_transition_mode
            ),
            "latest_proactive_line_transition_exit_mode": (
                latest_proactive_line_transition_exit_mode
            ),
            "latest_proactive_line_transition_source": (
                latest_proactive_line_transition_source
            ),
            "latest_proactive_line_machine_key": latest_proactive_line_machine_key,
            "latest_proactive_line_machine_mode": latest_proactive_line_machine_mode,
            "latest_proactive_line_machine_lifecycle": (
                latest_proactive_line_machine_lifecycle
            ),
            "latest_proactive_line_machine_actionability": (
                latest_proactive_line_machine_actionability
            ),
            "latest_proactive_line_machine_source": (
                latest_proactive_line_machine_source
            ),
            "latest_proactive_lifecycle_state_key": (
                latest_proactive_lifecycle_state_key
            ),
            "latest_proactive_lifecycle_state_mode": (
                latest_proactive_lifecycle_state_mode
            ),
            "latest_proactive_lifecycle_state_lifecycle": (
                latest_proactive_lifecycle_state_lifecycle
            ),
            "latest_proactive_lifecycle_state_actionability": (
                latest_proactive_lifecycle_state_actionability
            ),
            "latest_proactive_lifecycle_state_source": (
                latest_proactive_lifecycle_state_source
            ),
            "latest_proactive_lifecycle_transition_key": (
                latest_proactive_lifecycle_transition_key
            ),
            "latest_proactive_lifecycle_transition_mode": (
                latest_proactive_lifecycle_transition_mode
            ),
            "latest_proactive_lifecycle_transition_exit_mode": (
                latest_proactive_lifecycle_transition_exit_mode
            ),
            "latest_proactive_lifecycle_transition_source": (
                latest_proactive_lifecycle_transition_source
            ),
            "latest_proactive_lifecycle_machine_key": (
                latest_proactive_lifecycle_machine_key
            ),
            "latest_proactive_lifecycle_machine_mode": (
                latest_proactive_lifecycle_machine_mode
            ),
            "latest_proactive_lifecycle_machine_lifecycle": (
                latest_proactive_lifecycle_machine_lifecycle
            ),
            "latest_proactive_lifecycle_machine_actionability": (
                latest_proactive_lifecycle_machine_actionability
            ),
            "latest_proactive_lifecycle_machine_source": (
                latest_proactive_lifecycle_machine_source
            ),
            "latest_proactive_lifecycle_controller_key": (
                latest_proactive_lifecycle_controller_key
            ),
            "latest_proactive_lifecycle_controller_state": (
                latest_proactive_lifecycle_controller_state
            ),
            "latest_proactive_lifecycle_controller_decision": (
                latest_proactive_lifecycle_controller_decision
            ),
            "latest_proactive_lifecycle_controller_delay_seconds": (
                latest_proactive_lifecycle_controller_delay_seconds
            ),
            "latest_proactive_lifecycle_controller_source": (
                latest_proactive_lifecycle_controller_source
            ),
            "latest_proactive_lifecycle_envelope_key": (
                latest_proactive_lifecycle_envelope_key
            ),
            "latest_proactive_lifecycle_envelope_state": (
                latest_proactive_lifecycle_envelope_state
            ),
            "latest_proactive_lifecycle_envelope_mode": (
                latest_proactive_lifecycle_envelope_mode
            ),
            "latest_proactive_lifecycle_envelope_decision": (
                latest_proactive_lifecycle_envelope_decision
            ),
            "latest_proactive_lifecycle_envelope_actionability": (
                latest_proactive_lifecycle_envelope_actionability
            ),
            "latest_proactive_lifecycle_envelope_delay_seconds": (
                latest_proactive_lifecycle_envelope_delay_seconds
            ),
            "latest_proactive_lifecycle_envelope_source": (
                latest_proactive_lifecycle_envelope_source
            ),
            "latest_proactive_lifecycle_scheduler_key": (
                latest_proactive_lifecycle_scheduler_key
            ),
            "latest_proactive_lifecycle_scheduler_state": (
                latest_proactive_lifecycle_scheduler_state
            ),
            "latest_proactive_lifecycle_scheduler_mode": (
                latest_proactive_lifecycle_scheduler_mode
            ),
            "latest_proactive_lifecycle_scheduler_decision": (
                latest_proactive_lifecycle_scheduler_decision
            ),
            "latest_proactive_lifecycle_scheduler_actionability": (
                latest_proactive_lifecycle_scheduler_actionability
            ),
            "latest_proactive_lifecycle_scheduler_queue_status": (
                latest_proactive_lifecycle_scheduler_queue_status
            ),
            "latest_proactive_lifecycle_scheduler_delay_seconds": (
                latest_proactive_lifecycle_scheduler_delay_seconds
            ),
            "latest_proactive_lifecycle_scheduler_source": (
                latest_proactive_lifecycle_scheduler_source
            ),
            "latest_proactive_lifecycle_window_key": (
                latest_proactive_lifecycle_window_key
            ),
            "latest_proactive_lifecycle_window_state": (
                latest_proactive_lifecycle_window_state
            ),
            "latest_proactive_lifecycle_window_mode": (
                latest_proactive_lifecycle_window_mode
            ),
            "latest_proactive_lifecycle_window_decision": (
                latest_proactive_lifecycle_window_decision
            ),
            "latest_proactive_lifecycle_window_actionability": (
                latest_proactive_lifecycle_window_actionability
            ),
            "latest_proactive_lifecycle_window_queue_status": (
                latest_proactive_lifecycle_window_queue_status
            ),
            "latest_proactive_lifecycle_window_delay_seconds": (
                latest_proactive_lifecycle_window_delay_seconds
            ),
            "latest_proactive_lifecycle_window_source": (
                latest_proactive_lifecycle_window_source
            ),
            "latest_proactive_lifecycle_queue_key": (
                latest_proactive_lifecycle_queue_key
            ),
            "latest_proactive_lifecycle_queue_state": (
                latest_proactive_lifecycle_queue_state
            ),
            "latest_proactive_lifecycle_queue_mode": (
                latest_proactive_lifecycle_queue_mode
            ),
            "latest_proactive_lifecycle_queue_decision": (
                latest_proactive_lifecycle_queue_decision
            ),
            "latest_proactive_lifecycle_queue_actionability": (
                latest_proactive_lifecycle_queue_actionability
            ),
            "latest_proactive_lifecycle_queue_status": (
                latest_proactive_lifecycle_queue_status
            ),
            "latest_proactive_lifecycle_queue_delay_seconds": (
                latest_proactive_lifecycle_queue_delay_seconds
            ),
            "latest_proactive_lifecycle_queue_source": (
                latest_proactive_lifecycle_queue_source
            ),
            "latest_proactive_lifecycle_dispatch_key": (
                latest_proactive_lifecycle_dispatch_key
            ),
            "latest_proactive_lifecycle_dispatch_state": (
                latest_proactive_lifecycle_dispatch_state
            ),
            "latest_proactive_lifecycle_dispatch_mode": (
                latest_proactive_lifecycle_dispatch_mode
            ),
            "latest_proactive_lifecycle_dispatch_decision": (
                latest_proactive_lifecycle_dispatch_decision
            ),
            "latest_proactive_lifecycle_dispatch_actionability": (
                latest_proactive_lifecycle_dispatch_actionability
            ),
            "latest_proactive_lifecycle_dispatch_delay_seconds": (
                latest_proactive_lifecycle_dispatch_delay_seconds
            ),
            "latest_proactive_lifecycle_dispatch_source": (
                latest_proactive_lifecycle_dispatch_source
            ),
            "latest_proactive_lifecycle_outcome_key": (
                latest_proactive_lifecycle_outcome_key
            ),
            "latest_proactive_lifecycle_outcome_status": (
                latest_proactive_lifecycle_outcome_status
            ),
            "latest_proactive_lifecycle_outcome_mode": (
                latest_proactive_lifecycle_outcome_mode
            ),
            "latest_proactive_lifecycle_outcome_decision": (
                latest_proactive_lifecycle_outcome_decision
            ),
            "latest_proactive_lifecycle_outcome_actionability": (
                latest_proactive_lifecycle_outcome_actionability
            ),
            "latest_proactive_lifecycle_outcome_message_event_count": (
                latest_proactive_lifecycle_outcome_message_event_count
            ),
            "latest_proactive_lifecycle_outcome_source": (
                latest_proactive_lifecycle_outcome_source
            ),
            "latest_proactive_lifecycle_resolution_key": (
                latest_proactive_lifecycle_resolution_key
            ),
            "latest_proactive_lifecycle_resolution_status": (
                latest_proactive_lifecycle_resolution_status
            ),
            "latest_proactive_lifecycle_resolution_mode": (
                latest_proactive_lifecycle_resolution_mode
            ),
            "latest_proactive_lifecycle_resolution_decision": (
                latest_proactive_lifecycle_resolution_decision
            ),
            "latest_proactive_lifecycle_resolution_actionability": (
                latest_proactive_lifecycle_resolution_actionability
            ),
            "latest_proactive_lifecycle_resolution_queue_override_status": (
                latest_proactive_lifecycle_resolution_queue_override_status
            ),
            "latest_proactive_lifecycle_resolution_remaining_stage_count": (
                latest_proactive_lifecycle_resolution_remaining_stage_count
            ),
            "latest_proactive_lifecycle_resolution_source": (
                latest_proactive_lifecycle_resolution_source
            ),
            "latest_proactive_lifecycle_activation_key": (
                latest_proactive_lifecycle_activation_key
            ),
            "latest_proactive_lifecycle_activation_status": (
                latest_proactive_lifecycle_activation_status
            ),
            "latest_proactive_lifecycle_activation_mode": (
                latest_proactive_lifecycle_activation_mode
            ),
            "latest_proactive_lifecycle_activation_decision": (
                latest_proactive_lifecycle_activation_decision
            ),
            "latest_proactive_lifecycle_activation_actionability": (
                latest_proactive_lifecycle_activation_actionability
            ),
            "latest_proactive_lifecycle_activation_active_stage_label": (
                latest_proactive_lifecycle_activation_active_stage_label
            ),
            "latest_proactive_lifecycle_activation_queue_override_status": (
                latest_proactive_lifecycle_activation_queue_override_status
            ),
            "latest_proactive_lifecycle_activation_source": (
                latest_proactive_lifecycle_activation_source
            ),
            "latest_proactive_lifecycle_settlement_key": (
                latest_proactive_lifecycle_settlement_key
            ),
            "latest_proactive_lifecycle_settlement_status": (
                latest_proactive_lifecycle_settlement_status
            ),
            "latest_proactive_lifecycle_settlement_mode": (
                latest_proactive_lifecycle_settlement_mode
            ),
            "latest_proactive_lifecycle_settlement_decision": (
                latest_proactive_lifecycle_settlement_decision
            ),
            "latest_proactive_lifecycle_settlement_actionability": (
                latest_proactive_lifecycle_settlement_actionability
            ),
            "latest_proactive_lifecycle_settlement_active_stage_label": (
                latest_proactive_lifecycle_settlement_active_stage_label
            ),
            "latest_proactive_lifecycle_settlement_queue_override_status": (
                latest_proactive_lifecycle_settlement_queue_override_status
            ),
            "latest_proactive_lifecycle_settlement_source": (
                latest_proactive_lifecycle_settlement_source
            ),
            "latest_proactive_lifecycle_closure_key": (
                latest_proactive_lifecycle_closure_key
            ),
            "latest_proactive_lifecycle_closure_status": (
                latest_proactive_lifecycle_closure_status
            ),
            "latest_proactive_lifecycle_closure_mode": (
                latest_proactive_lifecycle_closure_mode
            ),
            "latest_proactive_lifecycle_closure_decision": (
                latest_proactive_lifecycle_closure_decision
            ),
            "latest_proactive_lifecycle_closure_actionability": (
                latest_proactive_lifecycle_closure_actionability
            ),
            "latest_proactive_lifecycle_closure_active_stage_label": (
                latest_proactive_lifecycle_closure_active_stage_label
            ),
            "latest_proactive_lifecycle_closure_queue_override_status": (
                latest_proactive_lifecycle_closure_queue_override_status
            ),
            "latest_proactive_lifecycle_closure_source": (
                latest_proactive_lifecycle_closure_source
            ),
            "latest_proactive_lifecycle_availability_key": (
                latest_proactive_lifecycle_availability_key
            ),
            "latest_proactive_lifecycle_availability_status": (
                latest_proactive_lifecycle_availability_status
            ),
            "latest_proactive_lifecycle_availability_mode": (
                latest_proactive_lifecycle_availability_mode
            ),
            "latest_proactive_lifecycle_availability_decision": (
                latest_proactive_lifecycle_availability_decision
            ),
            "latest_proactive_lifecycle_availability_actionability": (
                latest_proactive_lifecycle_availability_actionability
            ),
            "latest_proactive_lifecycle_availability_active_stage_label": (
                latest_proactive_lifecycle_availability_active_stage_label
            ),
            "latest_proactive_lifecycle_availability_queue_override_status": (
                latest_proactive_lifecycle_availability_queue_override_status
            ),
            "latest_proactive_lifecycle_availability_source": (
                latest_proactive_lifecycle_availability_source
            ),
            "latest_proactive_lifecycle_retention_key": (
                latest_proactive_lifecycle_retention_key
            ),
            "latest_proactive_lifecycle_retention_status": (
                latest_proactive_lifecycle_retention_status
            ),
            "latest_proactive_lifecycle_retention_mode": (
                latest_proactive_lifecycle_retention_mode
            ),
            "latest_proactive_lifecycle_retention_decision": (
                latest_proactive_lifecycle_retention_decision
            ),
            "latest_proactive_lifecycle_retention_actionability": (
                latest_proactive_lifecycle_retention_actionability
            ),
            "latest_proactive_lifecycle_retention_active_stage_label": (
                latest_proactive_lifecycle_retention_active_stage_label
            ),
            "latest_proactive_lifecycle_retention_queue_override_status": (
                latest_proactive_lifecycle_retention_queue_override_status
            ),
            "latest_proactive_lifecycle_retention_source": (
                latest_proactive_lifecycle_retention_source
            ),
            "latest_proactive_lifecycle_eligibility_key": (
                latest_proactive_lifecycle_eligibility_key
            ),
            "latest_proactive_lifecycle_eligibility_status": (
                latest_proactive_lifecycle_eligibility_status
            ),
            "latest_proactive_lifecycle_eligibility_mode": (
                latest_proactive_lifecycle_eligibility_mode
            ),
            "latest_proactive_lifecycle_eligibility_decision": (
                latest_proactive_lifecycle_eligibility_decision
            ),
            "latest_proactive_lifecycle_eligibility_actionability": (
                latest_proactive_lifecycle_eligibility_actionability
            ),
            "latest_proactive_lifecycle_eligibility_active_stage_label": (
                latest_proactive_lifecycle_eligibility_active_stage_label
            ),
            "latest_proactive_lifecycle_eligibility_queue_override_status": (
                latest_proactive_lifecycle_eligibility_queue_override_status
            ),
            "latest_proactive_lifecycle_eligibility_source": (
                latest_proactive_lifecycle_eligibility_source
            ),
            "latest_proactive_lifecycle_candidate_key": (
                latest_proactive_lifecycle_candidate_key
            ),
            "latest_proactive_lifecycle_candidate_status": (
                latest_proactive_lifecycle_candidate_status
            ),
            "latest_proactive_lifecycle_candidate_mode": (
                latest_proactive_lifecycle_candidate_mode
            ),
            "latest_proactive_lifecycle_candidate_decision": (
                latest_proactive_lifecycle_candidate_decision
            ),
            "latest_proactive_lifecycle_candidate_actionability": (
                latest_proactive_lifecycle_candidate_actionability
            ),
            "latest_proactive_lifecycle_candidate_active_stage_label": (
                latest_proactive_lifecycle_candidate_active_stage_label
            ),
            "latest_proactive_lifecycle_candidate_queue_override_status": (
                latest_proactive_lifecycle_candidate_queue_override_status
            ),
            "latest_proactive_lifecycle_candidate_source": (
                latest_proactive_lifecycle_candidate_source
            ),
            "latest_proactive_lifecycle_selectability_key": (
                latest_proactive_lifecycle_selectability_key
            ),
            "latest_proactive_lifecycle_selectability_status": (
                latest_proactive_lifecycle_selectability_status
            ),
            "latest_proactive_lifecycle_selectability_mode": (
                latest_proactive_lifecycle_selectability_mode
            ),
            "latest_proactive_lifecycle_selectability_decision": (
                latest_proactive_lifecycle_selectability_decision
            ),
            "latest_proactive_lifecycle_selectability_actionability": (
                latest_proactive_lifecycle_selectability_actionability
            ),
            "latest_proactive_lifecycle_selectability_active_stage_label": (
                latest_proactive_lifecycle_selectability_active_stage_label
            ),
            "latest_proactive_lifecycle_selectability_queue_override_status": (
                latest_proactive_lifecycle_selectability_queue_override_status
            ),
            "latest_proactive_lifecycle_selectability_source": (
                latest_proactive_lifecycle_selectability_source
            ),
            "latest_proactive_lifecycle_reentry_key": (
                latest_proactive_lifecycle_reentry_key
            ),
            "latest_proactive_lifecycle_reentry_status": (
                latest_proactive_lifecycle_reentry_status
            ),
            "latest_proactive_lifecycle_reentry_mode": (
                latest_proactive_lifecycle_reentry_mode
            ),
            "latest_proactive_lifecycle_reentry_decision": (
                latest_proactive_lifecycle_reentry_decision
            ),
            "latest_proactive_lifecycle_reentry_actionability": (
                latest_proactive_lifecycle_reentry_actionability
            ),
            "latest_proactive_lifecycle_reentry_active_stage_label": (
                latest_proactive_lifecycle_reentry_active_stage_label
            ),
            "latest_proactive_lifecycle_reentry_queue_override_status": (
                latest_proactive_lifecycle_reentry_queue_override_status
            ),
            "latest_proactive_lifecycle_reentry_source": (
                latest_proactive_lifecycle_reentry_source
            ),
            "latest_proactive_lifecycle_reactivation_key": (
                latest_proactive_lifecycle_reactivation_key
            ),
            "latest_proactive_lifecycle_reactivation_status": (
                latest_proactive_lifecycle_reactivation_status
            ),
            "latest_proactive_lifecycle_reactivation_mode": (
                latest_proactive_lifecycle_reactivation_mode
            ),
            "latest_proactive_lifecycle_reactivation_decision": (
                latest_proactive_lifecycle_reactivation_decision
            ),
            "latest_proactive_lifecycle_reactivation_actionability": (
                latest_proactive_lifecycle_reactivation_actionability
            ),
            "latest_proactive_lifecycle_reactivation_active_stage_label": (
                latest_proactive_lifecycle_reactivation_active_stage_label
            ),
            "latest_proactive_lifecycle_reactivation_queue_override_status": (
                latest_proactive_lifecycle_reactivation_queue_override_status
            ),
            "latest_proactive_lifecycle_reactivation_source": (
                latest_proactive_lifecycle_reactivation_source
            ),
            "latest_proactive_lifecycle_resumption_key": (
                latest_proactive_lifecycle_resumption_key
            ),
            "latest_proactive_lifecycle_resumption_status": (
                latest_proactive_lifecycle_resumption_status
            ),
            "latest_proactive_lifecycle_resumption_mode": (
                latest_proactive_lifecycle_resumption_mode
            ),
            "latest_proactive_lifecycle_resumption_decision": (
                latest_proactive_lifecycle_resumption_decision
            ),
            "latest_proactive_lifecycle_resumption_actionability": (
                latest_proactive_lifecycle_resumption_actionability
            ),
            "latest_proactive_lifecycle_resumption_active_stage_label": (
                latest_proactive_lifecycle_resumption_active_stage_label
            ),
            "latest_proactive_lifecycle_resumption_queue_override_status": (
                latest_proactive_lifecycle_resumption_queue_override_status
            ),
            "latest_proactive_lifecycle_resumption_source": (
                latest_proactive_lifecycle_resumption_source
            ),
            "latest_proactive_lifecycle_readiness_key": (
                latest_proactive_lifecycle_readiness_key
            ),
            "latest_proactive_lifecycle_readiness_status": (
                latest_proactive_lifecycle_readiness_status
            ),
            "latest_proactive_lifecycle_readiness_mode": (
                latest_proactive_lifecycle_readiness_mode
            ),
            "latest_proactive_lifecycle_readiness_decision": (
                latest_proactive_lifecycle_readiness_decision
            ),
            "latest_proactive_lifecycle_readiness_actionability": (
                latest_proactive_lifecycle_readiness_actionability
            ),
            "latest_proactive_lifecycle_readiness_active_stage_label": (
                latest_proactive_lifecycle_readiness_active_stage_label
            ),
            "latest_proactive_lifecycle_readiness_queue_override_status": (
                latest_proactive_lifecycle_readiness_queue_override_status
            ),
            "latest_proactive_lifecycle_readiness_source": (
                latest_proactive_lifecycle_readiness_source
            ),
            "latest_proactive_lifecycle_arming_key": (
                latest_proactive_lifecycle_arming_key
            ),
            "latest_proactive_lifecycle_arming_status": (
                latest_proactive_lifecycle_arming_status
            ),
            "latest_proactive_lifecycle_arming_mode": (
                latest_proactive_lifecycle_arming_mode
            ),
            "latest_proactive_lifecycle_arming_decision": (
                latest_proactive_lifecycle_arming_decision
            ),
            "latest_proactive_lifecycle_arming_actionability": (
                latest_proactive_lifecycle_arming_actionability
            ),
            "latest_proactive_lifecycle_arming_active_stage_label": (
                latest_proactive_lifecycle_arming_active_stage_label
            ),
            "latest_proactive_lifecycle_arming_queue_override_status": (
                latest_proactive_lifecycle_arming_queue_override_status
            ),
            "latest_proactive_lifecycle_arming_source": (
                latest_proactive_lifecycle_arming_source
            ),
            "latest_proactive_lifecycle_trigger_key": (
                latest_proactive_lifecycle_trigger_key
            ),
            "latest_proactive_lifecycle_trigger_status": (
                latest_proactive_lifecycle_trigger_status
            ),
            "latest_proactive_lifecycle_trigger_mode": (
                latest_proactive_lifecycle_trigger_mode
            ),
            "latest_proactive_lifecycle_trigger_decision": (
                latest_proactive_lifecycle_trigger_decision
            ),
            "latest_proactive_lifecycle_trigger_actionability": (
                latest_proactive_lifecycle_trigger_actionability
            ),
            "latest_proactive_lifecycle_trigger_active_stage_label": (
                latest_proactive_lifecycle_trigger_active_stage_label
            ),
            "latest_proactive_lifecycle_trigger_queue_override_status": (
                latest_proactive_lifecycle_trigger_queue_override_status
            ),
            "latest_proactive_lifecycle_trigger_source": (
                latest_proactive_lifecycle_trigger_source
            ),
            "latest_proactive_lifecycle_launch_key": (
                latest_proactive_lifecycle_launch_key
            ),
            "latest_proactive_lifecycle_launch_status": (
                latest_proactive_lifecycle_launch_status
            ),
            "latest_proactive_lifecycle_launch_mode": (
                latest_proactive_lifecycle_launch_mode
            ),
            "latest_proactive_lifecycle_launch_decision": (
                latest_proactive_lifecycle_launch_decision
            ),
            "latest_proactive_lifecycle_launch_actionability": (
                latest_proactive_lifecycle_launch_actionability
            ),
            "latest_proactive_lifecycle_launch_active_stage_label": (
                latest_proactive_lifecycle_launch_active_stage_label
            ),
            "latest_proactive_lifecycle_launch_queue_override_status": (
                latest_proactive_lifecycle_launch_queue_override_status
            ),
            "latest_proactive_lifecycle_launch_source": (
                latest_proactive_lifecycle_launch_source
            ),
            "latest_proactive_lifecycle_handoff_key": (
                latest_proactive_lifecycle_handoff_key
            ),
            "latest_proactive_lifecycle_handoff_status": (
                latest_proactive_lifecycle_handoff_status
            ),
            "latest_proactive_lifecycle_handoff_mode": (
                latest_proactive_lifecycle_handoff_mode
            ),
            "latest_proactive_lifecycle_handoff_decision": (
                latest_proactive_lifecycle_handoff_decision
            ),
            "latest_proactive_lifecycle_handoff_actionability": (
                latest_proactive_lifecycle_handoff_actionability
            ),
            "latest_proactive_lifecycle_handoff_active_stage_label": (
                latest_proactive_lifecycle_handoff_active_stage_label
            ),
            "latest_proactive_lifecycle_handoff_queue_override_status": (
                latest_proactive_lifecycle_handoff_queue_override_status
            ),
            "latest_proactive_lifecycle_handoff_source": (
                latest_proactive_lifecycle_handoff_source
            ),
            "latest_proactive_lifecycle_continuation_key": (
                latest_proactive_lifecycle_continuation_key
            ),
            "latest_proactive_lifecycle_continuation_status": (
                latest_proactive_lifecycle_continuation_status
            ),
            "latest_proactive_lifecycle_continuation_mode": (
                latest_proactive_lifecycle_continuation_mode
            ),
            "latest_proactive_lifecycle_continuation_decision": (
                latest_proactive_lifecycle_continuation_decision
            ),
            "latest_proactive_lifecycle_continuation_actionability": (
                latest_proactive_lifecycle_continuation_actionability
            ),
            "latest_proactive_lifecycle_continuation_active_stage_label": (
                latest_proactive_lifecycle_continuation_active_stage_label
            ),
            "latest_proactive_lifecycle_continuation_queue_override_status": (
                latest_proactive_lifecycle_continuation_queue_override_status
            ),
            "latest_proactive_lifecycle_continuation_source": (
                latest_proactive_lifecycle_continuation_source
            ),
            "latest_proactive_lifecycle_sustainment_key": (
                latest_proactive_lifecycle_sustainment_key
            ),
            "latest_proactive_lifecycle_sustainment_status": (
                latest_proactive_lifecycle_sustainment_status
            ),
            "latest_proactive_lifecycle_sustainment_mode": (
                latest_proactive_lifecycle_sustainment_mode
            ),
            "latest_proactive_lifecycle_sustainment_decision": (
                latest_proactive_lifecycle_sustainment_decision
            ),
            "latest_proactive_lifecycle_sustainment_actionability": (
                latest_proactive_lifecycle_sustainment_actionability
            ),
            "latest_proactive_lifecycle_sustainment_active_stage_label": (
                latest_proactive_lifecycle_sustainment_active_stage_label
            ),
            "latest_proactive_lifecycle_sustainment_queue_override_status": (
                latest_proactive_lifecycle_sustainment_queue_override_status
            ),
            "latest_proactive_lifecycle_sustainment_source": (
                latest_proactive_lifecycle_sustainment_source
            ),
            "latest_proactive_lifecycle_stewardship_key": (
                latest_proactive_lifecycle_stewardship_key
            ),
            "latest_proactive_lifecycle_stewardship_status": (
                latest_proactive_lifecycle_stewardship_status
            ),
            "latest_proactive_lifecycle_stewardship_mode": (
                latest_proactive_lifecycle_stewardship_mode
            ),
            "latest_proactive_lifecycle_stewardship_decision": (
                latest_proactive_lifecycle_stewardship_decision
            ),
            "latest_proactive_lifecycle_stewardship_actionability": (
                latest_proactive_lifecycle_stewardship_actionability
            ),
            "latest_proactive_lifecycle_stewardship_active_stage_label": (
                latest_proactive_lifecycle_stewardship_active_stage_label
            ),
            "latest_proactive_lifecycle_stewardship_queue_override_status": (
                latest_proactive_lifecycle_stewardship_queue_override_status
            ),
            "latest_proactive_lifecycle_stewardship_source": (
                latest_proactive_lifecycle_stewardship_source
            ),
            "latest_proactive_lifecycle_guardianship_key": (
                latest_proactive_lifecycle_guardianship_key
            ),
            "latest_proactive_lifecycle_guardianship_status": (
                latest_proactive_lifecycle_guardianship_status
            ),
            "latest_proactive_lifecycle_guardianship_mode": (
                latest_proactive_lifecycle_guardianship_mode
            ),
            "latest_proactive_lifecycle_guardianship_decision": (
                latest_proactive_lifecycle_guardianship_decision
            ),
            "latest_proactive_lifecycle_guardianship_actionability": (
                latest_proactive_lifecycle_guardianship_actionability
            ),
            "latest_proactive_lifecycle_guardianship_active_stage_label": (
                latest_proactive_lifecycle_guardianship_active_stage_label
            ),
            "latest_proactive_lifecycle_guardianship_queue_override_status": (
                latest_proactive_lifecycle_guardianship_queue_override_status
            ),
            "latest_proactive_lifecycle_guardianship_source": (
                latest_proactive_lifecycle_guardianship_source
            ),
            "latest_proactive_lifecycle_oversight_key": (
                latest_proactive_lifecycle_oversight_key
            ),
            "latest_proactive_lifecycle_oversight_status": (
                latest_proactive_lifecycle_oversight_status
            ),
            "latest_proactive_lifecycle_oversight_mode": (
                latest_proactive_lifecycle_oversight_mode
            ),
            "latest_proactive_lifecycle_oversight_decision": (
                latest_proactive_lifecycle_oversight_decision
            ),
            "latest_proactive_lifecycle_oversight_actionability": (
                latest_proactive_lifecycle_oversight_actionability
            ),
            "latest_proactive_lifecycle_oversight_active_stage_label": (
                latest_proactive_lifecycle_oversight_active_stage_label
            ),
            "latest_proactive_lifecycle_oversight_queue_override_status": (
                latest_proactive_lifecycle_oversight_queue_override_status
            ),
            "latest_proactive_lifecycle_oversight_source": (
                latest_proactive_lifecycle_oversight_source
            ),
            "latest_proactive_lifecycle_assurance_key": (
                latest_proactive_lifecycle_assurance_key
            ),
            "latest_proactive_lifecycle_assurance_status": (
                latest_proactive_lifecycle_assurance_status
            ),
            "latest_proactive_lifecycle_assurance_mode": (
                latest_proactive_lifecycle_assurance_mode
            ),
            "latest_proactive_lifecycle_assurance_decision": (
                latest_proactive_lifecycle_assurance_decision
            ),
            "latest_proactive_lifecycle_assurance_actionability": (
                latest_proactive_lifecycle_assurance_actionability
            ),
            "latest_proactive_lifecycle_assurance_active_stage_label": (
                latest_proactive_lifecycle_assurance_active_stage_label
            ),
            "latest_proactive_lifecycle_assurance_queue_override_status": (
                latest_proactive_lifecycle_assurance_queue_override_status
            ),
            "latest_proactive_lifecycle_assurance_source": (
                latest_proactive_lifecycle_assurance_source
            ),
            "latest_proactive_lifecycle_attestation_key": (
                latest_proactive_lifecycle_attestation_key
            ),
            "latest_proactive_lifecycle_attestation_status": (
                latest_proactive_lifecycle_attestation_status
            ),
            "latest_proactive_lifecycle_attestation_mode": (
                latest_proactive_lifecycle_attestation_mode
            ),
            "latest_proactive_lifecycle_attestation_decision": (
                latest_proactive_lifecycle_attestation_decision
            ),
            "latest_proactive_lifecycle_attestation_actionability": (
                latest_proactive_lifecycle_attestation_actionability
            ),
            "latest_proactive_lifecycle_attestation_active_stage_label": (
                latest_proactive_lifecycle_attestation_active_stage_label
            ),
            "latest_proactive_lifecycle_attestation_queue_override_status": (
                latest_proactive_lifecycle_attestation_queue_override_status
            ),
            "latest_proactive_lifecycle_attestation_source": (
                latest_proactive_lifecycle_attestation_source
            ),
            "latest_proactive_lifecycle_verification_key": (
                latest_proactive_lifecycle_verification_key
            ),
            "latest_proactive_lifecycle_verification_status": (
                latest_proactive_lifecycle_verification_status
            ),
            "latest_proactive_lifecycle_verification_mode": (
                latest_proactive_lifecycle_verification_mode
            ),
            "latest_proactive_lifecycle_verification_decision": (
                latest_proactive_lifecycle_verification_decision
            ),
            "latest_proactive_lifecycle_verification_actionability": (
                latest_proactive_lifecycle_verification_actionability
            ),
            "latest_proactive_lifecycle_verification_active_stage_label": (
                latest_proactive_lifecycle_verification_active_stage_label
            ),
            "latest_proactive_lifecycle_verification_queue_override_status": (
                latest_proactive_lifecycle_verification_queue_override_status
            ),
            "latest_proactive_lifecycle_verification_source": (
                latest_proactive_lifecycle_verification_source
            ),
            "latest_proactive_lifecycle_certification_key": (
                latest_proactive_lifecycle_certification_key
            ),
            "latest_proactive_lifecycle_certification_status": (
                latest_proactive_lifecycle_certification_status
            ),
            "latest_proactive_lifecycle_certification_mode": (
                latest_proactive_lifecycle_certification_mode
            ),
            "latest_proactive_lifecycle_certification_decision": (
                latest_proactive_lifecycle_certification_decision
            ),
            "latest_proactive_lifecycle_certification_actionability": (
                latest_proactive_lifecycle_certification_actionability
            ),
            "latest_proactive_lifecycle_certification_active_stage_label": (
                latest_proactive_lifecycle_certification_active_stage_label
            ),
            "latest_proactive_lifecycle_certification_queue_override_status": (
                latest_proactive_lifecycle_certification_queue_override_status
            ),
            "latest_proactive_lifecycle_certification_source": (
                latest_proactive_lifecycle_certification_source
            ),
            "latest_proactive_lifecycle_confirmation_key": (
                latest_proactive_lifecycle_confirmation_key
            ),
            "latest_proactive_lifecycle_confirmation_status": (
                latest_proactive_lifecycle_confirmation_status
            ),
            "latest_proactive_lifecycle_confirmation_mode": (
                latest_proactive_lifecycle_confirmation_mode
            ),
            "latest_proactive_lifecycle_confirmation_decision": (
                latest_proactive_lifecycle_confirmation_decision
            ),
            "latest_proactive_lifecycle_confirmation_actionability": (
                latest_proactive_lifecycle_confirmation_actionability
            ),
            "latest_proactive_lifecycle_confirmation_active_stage_label": (
                latest_proactive_lifecycle_confirmation_active_stage_label
            ),
            "latest_proactive_lifecycle_confirmation_queue_override_status": (
                latest_proactive_lifecycle_confirmation_queue_override_status
            ),
            "latest_proactive_lifecycle_confirmation_source": (
                latest_proactive_lifecycle_confirmation_source
            ),
            "latest_proactive_lifecycle_ratification_key": (
                latest_proactive_lifecycle_ratification_key
            ),
            "latest_proactive_lifecycle_ratification_status": (
                latest_proactive_lifecycle_ratification_status
            ),
            "latest_proactive_lifecycle_ratification_mode": (
                latest_proactive_lifecycle_ratification_mode
            ),
            "latest_proactive_lifecycle_ratification_decision": (
                latest_proactive_lifecycle_ratification_decision
            ),
            "latest_proactive_lifecycle_ratification_actionability": (
                latest_proactive_lifecycle_ratification_actionability
            ),
            "latest_proactive_lifecycle_ratification_active_stage_label": (
                latest_proactive_lifecycle_ratification_active_stage_label
            ),
            "latest_proactive_lifecycle_ratification_queue_override_status": (
                latest_proactive_lifecycle_ratification_queue_override_status
            ),
            "latest_proactive_lifecycle_ratification_source": (
                latest_proactive_lifecycle_ratification_source
            ),
            "latest_proactive_lifecycle_endorsement_key": (
                latest_proactive_lifecycle_endorsement_key
            ),
            "latest_proactive_lifecycle_endorsement_status": (
                latest_proactive_lifecycle_endorsement_status
            ),
            "latest_proactive_lifecycle_endorsement_mode": (
                latest_proactive_lifecycle_endorsement_mode
            ),
            "latest_proactive_lifecycle_endorsement_decision": (
                latest_proactive_lifecycle_endorsement_decision
            ),
            "latest_proactive_lifecycle_endorsement_actionability": (
                latest_proactive_lifecycle_endorsement_actionability
            ),
            "latest_proactive_lifecycle_endorsement_active_stage_label": (
                latest_proactive_lifecycle_endorsement_active_stage_label
            ),
            "latest_proactive_lifecycle_endorsement_queue_override_status": (
                latest_proactive_lifecycle_endorsement_queue_override_status
            ),
            "latest_proactive_lifecycle_endorsement_source": (
                latest_proactive_lifecycle_endorsement_source
            ),
            "latest_proactive_lifecycle_authorization_key": (
                latest_proactive_lifecycle_authorization_key
            ),
            "latest_proactive_lifecycle_authorization_status": (
                latest_proactive_lifecycle_authorization_status
            ),
            "latest_proactive_lifecycle_authorization_mode": (
                latest_proactive_lifecycle_authorization_mode
            ),
            "latest_proactive_lifecycle_authorization_decision": (
                latest_proactive_lifecycle_authorization_decision
            ),
            "latest_proactive_lifecycle_authorization_actionability": (
                latest_proactive_lifecycle_authorization_actionability
            ),
            "latest_proactive_lifecycle_authorization_active_stage_label": (
                latest_proactive_lifecycle_authorization_active_stage_label
            ),
            "latest_proactive_lifecycle_authorization_queue_override_status": (
                latest_proactive_lifecycle_authorization_queue_override_status
            ),
            "latest_proactive_lifecycle_authorization_source": (
                latest_proactive_lifecycle_authorization_source
            ),
            "latest_proactive_lifecycle_enactment_key": (
                latest_proactive_lifecycle_enactment_key
            ),
            "latest_proactive_lifecycle_enactment_status": (
                latest_proactive_lifecycle_enactment_status
            ),
            "latest_proactive_lifecycle_enactment_mode": (
                latest_proactive_lifecycle_enactment_mode
            ),
            "latest_proactive_lifecycle_enactment_decision": (
                latest_proactive_lifecycle_enactment_decision
            ),
            "latest_proactive_lifecycle_enactment_actionability": (
                latest_proactive_lifecycle_enactment_actionability
            ),
            "latest_proactive_lifecycle_enactment_active_stage_label": (
                latest_proactive_lifecycle_enactment_active_stage_label
            ),
            "latest_proactive_lifecycle_enactment_queue_override_status": (
                latest_proactive_lifecycle_enactment_queue_override_status
            ),
            "latest_proactive_lifecycle_enactment_source": (
                latest_proactive_lifecycle_enactment_source
            ),
            "latest_proactive_lifecycle_finality_key": (
                latest_proactive_lifecycle_finality_key
            ),
            "latest_proactive_lifecycle_finality_status": (
                latest_proactive_lifecycle_finality_status
            ),
            "latest_proactive_lifecycle_finality_mode": (
                latest_proactive_lifecycle_finality_mode
            ),
            "latest_proactive_lifecycle_finality_decision": (
                latest_proactive_lifecycle_finality_decision
            ),
            "latest_proactive_lifecycle_finality_actionability": (
                latest_proactive_lifecycle_finality_actionability
            ),
            "latest_proactive_lifecycle_finality_active_stage_label": (
                latest_proactive_lifecycle_finality_active_stage_label
            ),
            "latest_proactive_lifecycle_finality_queue_override_status": (
                latest_proactive_lifecycle_finality_queue_override_status
            ),
            "latest_proactive_lifecycle_finality_source": (
                latest_proactive_lifecycle_finality_source
            ),
            "latest_proactive_lifecycle_completion_key": (
                latest_proactive_lifecycle_completion_key
            ),
            "latest_proactive_lifecycle_completion_status": (
                latest_proactive_lifecycle_completion_status
            ),
            "latest_proactive_lifecycle_completion_mode": (
                latest_proactive_lifecycle_completion_mode
            ),
            "latest_proactive_lifecycle_completion_decision": (
                latest_proactive_lifecycle_completion_decision
            ),
            "latest_proactive_lifecycle_completion_actionability": (
                latest_proactive_lifecycle_completion_actionability
            ),
            "latest_proactive_lifecycle_completion_active_stage_label": (
                latest_proactive_lifecycle_completion_active_stage_label
            ),
            "latest_proactive_lifecycle_completion_queue_override_status": (
                latest_proactive_lifecycle_completion_queue_override_status
            ),
            "latest_proactive_lifecycle_completion_source": (
                latest_proactive_lifecycle_completion_source
            ),
            "latest_proactive_lifecycle_conclusion_key": (
                latest_proactive_lifecycle_conclusion_key
            ),
            "latest_proactive_lifecycle_conclusion_status": (
                latest_proactive_lifecycle_conclusion_status
            ),
            "latest_proactive_lifecycle_conclusion_mode": (
                latest_proactive_lifecycle_conclusion_mode
            ),
            "latest_proactive_lifecycle_conclusion_decision": (
                latest_proactive_lifecycle_conclusion_decision
            ),
            "latest_proactive_lifecycle_conclusion_actionability": (
                latest_proactive_lifecycle_conclusion_actionability
            ),
            "latest_proactive_lifecycle_conclusion_active_stage_label": (
                latest_proactive_lifecycle_conclusion_active_stage_label
            ),
            "latest_proactive_lifecycle_conclusion_queue_override_status": (
                latest_proactive_lifecycle_conclusion_queue_override_status
            ),
            "latest_proactive_lifecycle_conclusion_source": (
                latest_proactive_lifecycle_conclusion_source
            ),
            "latest_proactive_lifecycle_disposition_key": (
                latest_proactive_lifecycle_disposition_key
            ),
            "latest_proactive_lifecycle_disposition_status": (
                latest_proactive_lifecycle_disposition_status
            ),
            "latest_proactive_lifecycle_disposition_mode": (
                latest_proactive_lifecycle_disposition_mode
            ),
            "latest_proactive_lifecycle_disposition_decision": (
                latest_proactive_lifecycle_disposition_decision
            ),
            "latest_proactive_lifecycle_disposition_actionability": (
                latest_proactive_lifecycle_disposition_actionability
            ),
            "latest_proactive_lifecycle_disposition_active_stage_label": (
                latest_proactive_lifecycle_disposition_active_stage_label
            ),
            "latest_proactive_lifecycle_disposition_queue_override_status": (
                latest_proactive_lifecycle_disposition_queue_override_status
            ),
            "latest_proactive_lifecycle_disposition_source": (
                latest_proactive_lifecycle_disposition_source
            ),
            "latest_proactive_lifecycle_standing_key": (
                latest_proactive_lifecycle_standing_key
            ),
            "latest_proactive_lifecycle_standing_status": (
                latest_proactive_lifecycle_standing_status
            ),
            "latest_proactive_lifecycle_standing_mode": (
                latest_proactive_lifecycle_standing_mode
            ),
            "latest_proactive_lifecycle_standing_decision": (
                latest_proactive_lifecycle_standing_decision
            ),
            "latest_proactive_lifecycle_standing_actionability": (
                latest_proactive_lifecycle_standing_actionability
            ),
            "latest_proactive_lifecycle_standing_active_stage_label": (
                latest_proactive_lifecycle_standing_active_stage_label
            ),
            "latest_proactive_lifecycle_standing_queue_override_status": (
                latest_proactive_lifecycle_standing_queue_override_status
            ),
            "latest_proactive_lifecycle_standing_source": (
                latest_proactive_lifecycle_standing_source
            ),
            "latest_proactive_lifecycle_residency_key": (
                latest_proactive_lifecycle_residency_key
            ),
            "latest_proactive_lifecycle_residency_status": (
                latest_proactive_lifecycle_residency_status
            ),
            "latest_proactive_lifecycle_residency_mode": (
                latest_proactive_lifecycle_residency_mode
            ),
            "latest_proactive_lifecycle_residency_decision": (
                latest_proactive_lifecycle_residency_decision
            ),
            "latest_proactive_lifecycle_residency_actionability": (
                latest_proactive_lifecycle_residency_actionability
            ),
            "latest_proactive_lifecycle_residency_active_stage_label": (
                latest_proactive_lifecycle_residency_active_stage_label
            ),
            "latest_proactive_lifecycle_residency_queue_override_status": (
                latest_proactive_lifecycle_residency_queue_override_status
            ),
            "latest_proactive_lifecycle_residency_source": (
                latest_proactive_lifecycle_residency_source
            ),
            "latest_proactive_lifecycle_tenure_key": (
                latest_proactive_lifecycle_tenure_key
            ),
            "latest_proactive_lifecycle_tenure_status": (
                latest_proactive_lifecycle_tenure_status
            ),
            "latest_proactive_lifecycle_tenure_mode": (
                latest_proactive_lifecycle_tenure_mode
            ),
            "latest_proactive_lifecycle_tenure_decision": (
                latest_proactive_lifecycle_tenure_decision
            ),
            "latest_proactive_lifecycle_tenure_actionability": (
                latest_proactive_lifecycle_tenure_actionability
            ),
            "latest_proactive_lifecycle_tenure_active_stage_label": (
                latest_proactive_lifecycle_tenure_active_stage_label
            ),
            "latest_proactive_lifecycle_tenure_queue_override_status": (
                latest_proactive_lifecycle_tenure_queue_override_status
            ),
            "latest_proactive_lifecycle_tenure_source": (
                latest_proactive_lifecycle_tenure_source
            ),
            "latest_proactive_lifecycle_persistence_key": (
                latest_proactive_lifecycle_persistence_key
            ),
            "latest_proactive_lifecycle_persistence_status": (
                latest_proactive_lifecycle_persistence_status
            ),
            "latest_proactive_lifecycle_persistence_mode": (
                latest_proactive_lifecycle_persistence_mode
            ),
            "latest_proactive_lifecycle_persistence_decision": (
                latest_proactive_lifecycle_persistence_decision
            ),
            "latest_proactive_lifecycle_persistence_actionability": (
                latest_proactive_lifecycle_persistence_actionability
            ),
            "latest_proactive_lifecycle_persistence_active_stage_label": (
                latest_proactive_lifecycle_persistence_active_stage_label
            ),
            "latest_proactive_lifecycle_persistence_queue_override_status": (
                latest_proactive_lifecycle_persistence_queue_override_status
            ),
            "latest_proactive_lifecycle_persistence_source": (
                latest_proactive_lifecycle_persistence_source
            ),
            "latest_proactive_lifecycle_longevity_key": (
                latest_proactive_lifecycle_longevity_key
            ),
            "latest_proactive_lifecycle_longevity_status": (
                latest_proactive_lifecycle_longevity_status
            ),
            "latest_proactive_lifecycle_longevity_mode": (
                latest_proactive_lifecycle_longevity_mode
            ),
            "latest_proactive_lifecycle_longevity_decision": (
                latest_proactive_lifecycle_longevity_decision
            ),
            "latest_proactive_lifecycle_longevity_actionability": (
                latest_proactive_lifecycle_longevity_actionability
            ),
            "latest_proactive_lifecycle_longevity_active_stage_label": (
                latest_proactive_lifecycle_longevity_active_stage_label
            ),
            "latest_proactive_lifecycle_longevity_queue_override_status": (
                latest_proactive_lifecycle_longevity_queue_override_status
            ),
            "latest_proactive_lifecycle_longevity_source": (
                latest_proactive_lifecycle_longevity_source
            ),
            "latest_proactive_lifecycle_legacy_key": (
                latest_proactive_lifecycle_legacy_key
            ),
            "latest_proactive_lifecycle_legacy_status": (
                latest_proactive_lifecycle_legacy_status
            ),
            "latest_proactive_lifecycle_legacy_mode": (
                latest_proactive_lifecycle_legacy_mode
            ),
            "latest_proactive_lifecycle_legacy_decision": (
                latest_proactive_lifecycle_legacy_decision
            ),
            "latest_proactive_lifecycle_legacy_actionability": (
                latest_proactive_lifecycle_legacy_actionability
            ),
            "latest_proactive_lifecycle_legacy_active_stage_label": (
                latest_proactive_lifecycle_legacy_active_stage_label
            ),
            "latest_proactive_lifecycle_legacy_queue_override_status": (
                latest_proactive_lifecycle_legacy_queue_override_status
            ),
            "latest_proactive_lifecycle_legacy_source": (
                latest_proactive_lifecycle_legacy_source
            ),
            "latest_proactive_lifecycle_heritage_key": (
                latest_proactive_lifecycle_heritage_key
            ),
            "latest_proactive_lifecycle_heritage_status": (
                latest_proactive_lifecycle_heritage_status
            ),
            "latest_proactive_lifecycle_heritage_mode": (
                latest_proactive_lifecycle_heritage_mode
            ),
            "latest_proactive_lifecycle_heritage_decision": (
                latest_proactive_lifecycle_heritage_decision
            ),
            "latest_proactive_lifecycle_heritage_actionability": (
                latest_proactive_lifecycle_heritage_actionability
            ),
            "latest_proactive_lifecycle_heritage_active_stage_label": (
                latest_proactive_lifecycle_heritage_active_stage_label
            ),
            "latest_proactive_lifecycle_heritage_queue_override_status": (
                latest_proactive_lifecycle_heritage_queue_override_status
            ),
            "latest_proactive_lifecycle_heritage_source": (
                latest_proactive_lifecycle_heritage_source
            ),
            "latest_proactive_lifecycle_lineage_key": (
                latest_proactive_lifecycle_lineage_key
            ),
            "latest_proactive_lifecycle_lineage_status": (
                latest_proactive_lifecycle_lineage_status
            ),
            "latest_proactive_lifecycle_lineage_mode": (
                latest_proactive_lifecycle_lineage_mode
            ),
            "latest_proactive_lifecycle_lineage_decision": (
                latest_proactive_lifecycle_lineage_decision
            ),
            "latest_proactive_lifecycle_lineage_actionability": (
                latest_proactive_lifecycle_lineage_actionability
            ),
            "latest_proactive_lifecycle_lineage_active_stage_label": (
                latest_proactive_lifecycle_lineage_active_stage_label
            ),
            "latest_proactive_lifecycle_lineage_queue_override_status": (
                latest_proactive_lifecycle_lineage_queue_override_status
            ),
            "latest_proactive_lifecycle_lineage_source": (
                latest_proactive_lifecycle_lineage_source
            ),
            "latest_proactive_lifecycle_ancestry_key": (
                latest_proactive_lifecycle_ancestry_key
            ),
            "latest_proactive_lifecycle_ancestry_status": (
                latest_proactive_lifecycle_ancestry_status
            ),
            "latest_proactive_lifecycle_ancestry_mode": (
                latest_proactive_lifecycle_ancestry_mode
            ),
            "latest_proactive_lifecycle_ancestry_decision": (
                latest_proactive_lifecycle_ancestry_decision
            ),
            "latest_proactive_lifecycle_ancestry_actionability": (
                latest_proactive_lifecycle_ancestry_actionability
            ),
            "latest_proactive_lifecycle_ancestry_active_stage_label": (
                latest_proactive_lifecycle_ancestry_active_stage_label
            ),
            "latest_proactive_lifecycle_ancestry_queue_override_status": (
                latest_proactive_lifecycle_ancestry_queue_override_status
            ),
            "latest_proactive_lifecycle_ancestry_source": (
                latest_proactive_lifecycle_ancestry_source
            ),
            "latest_proactive_lifecycle_provenance_key": (
                latest_proactive_lifecycle_provenance_key
            ),
            "latest_proactive_lifecycle_provenance_status": (
                latest_proactive_lifecycle_provenance_status
            ),
            "latest_proactive_lifecycle_provenance_mode": (
                latest_proactive_lifecycle_provenance_mode
            ),
            "latest_proactive_lifecycle_provenance_decision": (
                latest_proactive_lifecycle_provenance_decision
            ),
            "latest_proactive_lifecycle_provenance_actionability": (
                latest_proactive_lifecycle_provenance_actionability
            ),
            "latest_proactive_lifecycle_provenance_active_stage_label": (
                latest_proactive_lifecycle_provenance_active_stage_label
            ),
            "latest_proactive_lifecycle_provenance_queue_override_status": (
                latest_proactive_lifecycle_provenance_queue_override_status
            ),
            "latest_proactive_lifecycle_provenance_source": (
                latest_proactive_lifecycle_provenance_source
            ),
            "latest_proactive_lifecycle_origin_key": (
                latest_proactive_lifecycle_origin_key
            ),
            "latest_proactive_lifecycle_origin_status": (
                latest_proactive_lifecycle_origin_status
            ),
            "latest_proactive_lifecycle_origin_mode": (
                latest_proactive_lifecycle_origin_mode
            ),
            "latest_proactive_lifecycle_origin_decision": (
                latest_proactive_lifecycle_origin_decision
            ),
            "latest_proactive_lifecycle_origin_actionability": (
                latest_proactive_lifecycle_origin_actionability
            ),
            "latest_proactive_lifecycle_origin_active_stage_label": (
                latest_proactive_lifecycle_origin_active_stage_label
            ),
            "latest_proactive_lifecycle_origin_queue_override_status": (
                latest_proactive_lifecycle_origin_queue_override_status
            ),
            "latest_proactive_lifecycle_origin_source": (
                latest_proactive_lifecycle_origin_source
            ),
            "latest_proactive_lifecycle_root_key": (
                latest_proactive_lifecycle_root_key
            ),
            "latest_proactive_lifecycle_root_status": (
                latest_proactive_lifecycle_root_status
            ),
            "latest_proactive_lifecycle_root_mode": (
                latest_proactive_lifecycle_root_mode
            ),
            "latest_proactive_lifecycle_root_decision": (
                latest_proactive_lifecycle_root_decision
            ),
            "latest_proactive_lifecycle_root_actionability": (
                latest_proactive_lifecycle_root_actionability
            ),
            "latest_proactive_lifecycle_root_active_stage_label": (
                latest_proactive_lifecycle_root_active_stage_label
            ),
            "latest_proactive_lifecycle_root_queue_override_status": (
                latest_proactive_lifecycle_root_queue_override_status
            ),
            "latest_proactive_lifecycle_root_source": (
                latest_proactive_lifecycle_root_source
            ),
            "latest_proactive_lifecycle_foundation_key": (
                latest_proactive_lifecycle_foundation_key
            ),
            "latest_proactive_lifecycle_foundation_status": (
                latest_proactive_lifecycle_foundation_status
            ),
            "latest_proactive_lifecycle_foundation_mode": (
                latest_proactive_lifecycle_foundation_mode
            ),
            "latest_proactive_lifecycle_foundation_decision": (
                latest_proactive_lifecycle_foundation_decision
            ),
            "latest_proactive_lifecycle_foundation_actionability": (
                latest_proactive_lifecycle_foundation_actionability
            ),
            "latest_proactive_lifecycle_foundation_active_stage_label": (
                latest_proactive_lifecycle_foundation_active_stage_label
            ),
            "latest_proactive_lifecycle_foundation_queue_override_status": (
                latest_proactive_lifecycle_foundation_queue_override_status
            ),
            "latest_proactive_lifecycle_foundation_source": (
                latest_proactive_lifecycle_foundation_source
            ),
            "latest_proactive_lifecycle_bedrock_key": (
                latest_proactive_lifecycle_bedrock_key
            ),
            "latest_proactive_lifecycle_bedrock_status": (
                latest_proactive_lifecycle_bedrock_status
            ),
            "latest_proactive_lifecycle_bedrock_mode": (
                latest_proactive_lifecycle_bedrock_mode
            ),
            "latest_proactive_lifecycle_bedrock_decision": (
                latest_proactive_lifecycle_bedrock_decision
            ),
            "latest_proactive_lifecycle_bedrock_actionability": (
                latest_proactive_lifecycle_bedrock_actionability
            ),
            "latest_proactive_lifecycle_bedrock_active_stage_label": (
                latest_proactive_lifecycle_bedrock_active_stage_label
            ),
            "latest_proactive_lifecycle_bedrock_queue_override_status": (
                latest_proactive_lifecycle_bedrock_queue_override_status
            ),
            "latest_proactive_lifecycle_bedrock_source": (
                latest_proactive_lifecycle_bedrock_source
            ),
            "latest_proactive_lifecycle_substrate_key": (
                latest_proactive_lifecycle_substrate_key
            ),
            "latest_proactive_lifecycle_substrate_status": (
                latest_proactive_lifecycle_substrate_status
            ),
            "latest_proactive_lifecycle_substrate_mode": (
                latest_proactive_lifecycle_substrate_mode
            ),
            "latest_proactive_lifecycle_substrate_decision": (
                latest_proactive_lifecycle_substrate_decision
            ),
            "latest_proactive_lifecycle_substrate_actionability": (
                latest_proactive_lifecycle_substrate_actionability
            ),
            "latest_proactive_lifecycle_substrate_active_stage_label": (
                latest_proactive_lifecycle_substrate_active_stage_label
            ),
            "latest_proactive_lifecycle_substrate_queue_override_status": (
                latest_proactive_lifecycle_substrate_queue_override_status
            ),
            "latest_proactive_lifecycle_substrate_source": (
                latest_proactive_lifecycle_substrate_source
            ),
            "latest_proactive_lifecycle_stratum_key": (
                latest_proactive_lifecycle_stratum_key
            ),
            "latest_proactive_lifecycle_stratum_status": (
                latest_proactive_lifecycle_stratum_status
            ),
            "latest_proactive_lifecycle_stratum_mode": (
                latest_proactive_lifecycle_stratum_mode
            ),
            "latest_proactive_lifecycle_stratum_decision": (
                latest_proactive_lifecycle_stratum_decision
            ),
            "latest_proactive_lifecycle_stratum_actionability": (
                latest_proactive_lifecycle_stratum_actionability
            ),
            "latest_proactive_lifecycle_stratum_active_stage_label": (
                latest_proactive_lifecycle_stratum_active_stage_label
            ),
            "latest_proactive_lifecycle_stratum_queue_override_status": (
                latest_proactive_lifecycle_stratum_queue_override_status
            ),
            "latest_proactive_lifecycle_stratum_source": (
                latest_proactive_lifecycle_stratum_source
            ),
            "latest_proactive_lifecycle_layer_key": (
                latest_proactive_lifecycle_layer_key
            ),
            "latest_proactive_lifecycle_layer_status": (
                latest_proactive_lifecycle_layer_status
            ),
            "latest_proactive_lifecycle_layer_mode": (
                latest_proactive_lifecycle_layer_mode
            ),
            "latest_proactive_lifecycle_layer_decision": (
                latest_proactive_lifecycle_layer_decision
            ),
            "latest_proactive_lifecycle_layer_actionability": (
                latest_proactive_lifecycle_layer_actionability
            ),
            "latest_proactive_lifecycle_layer_active_stage_label": (
                latest_proactive_lifecycle_layer_active_stage_label
            ),
            "latest_proactive_lifecycle_layer_queue_override_status": (
                latest_proactive_lifecycle_layer_queue_override_status
            ),
            "latest_proactive_lifecycle_layer_source": (
                latest_proactive_lifecycle_layer_source
            ),
            "latest_proactive_lifecycle_durability_key": (
                latest_proactive_lifecycle_durability_key
            ),
            "latest_proactive_lifecycle_durability_status": (
                latest_proactive_lifecycle_durability_status
            ),
            "latest_proactive_lifecycle_durability_mode": (
                latest_proactive_lifecycle_durability_mode
            ),
            "latest_proactive_lifecycle_durability_decision": (
                latest_proactive_lifecycle_durability_decision
            ),
            "latest_proactive_lifecycle_durability_actionability": (
                latest_proactive_lifecycle_durability_actionability
            ),
            "latest_proactive_lifecycle_durability_active_stage_label": (
                latest_proactive_lifecycle_durability_active_stage_label
            ),
            "latest_proactive_lifecycle_durability_queue_override_status": (
                latest_proactive_lifecycle_durability_queue_override_status
            ),
            "latest_proactive_lifecycle_durability_source": (
                latest_proactive_lifecycle_durability_source
            ),
            "latest_proactive_stage_refresh_key": latest_proactive_stage_refresh_key,
            "latest_proactive_stage_refresh_window_status": (
                latest_proactive_stage_refresh_window_status
            ),
            "latest_proactive_stage_refresh_stage_label": (
                latest_proactive_stage_refresh_stage_label
            ),
            "latest_proactive_stage_refresh_changed": (
                latest_proactive_stage_refresh_changed
            ),
            "latest_proactive_stage_refresh_delivery_mode": (
                latest_proactive_stage_refresh_delivery_mode
            ),
            "latest_proactive_stage_refresh_user_space_signal": (
                latest_proactive_stage_refresh_user_space_signal
            ),
            "latest_proactive_stage_replan_key": latest_proactive_stage_replan_key,
            "latest_proactive_stage_replan_strategy_key": (
                latest_proactive_stage_replan_strategy_key
            ),
            "latest_proactive_stage_replan_ritual_mode": (
                latest_proactive_stage_replan_ritual_mode
            ),
            "latest_proactive_stage_replan_pressure_mode": (
                latest_proactive_stage_replan_pressure_mode
            ),
            "latest_proactive_stage_replan_autonomy_signal": (
                latest_proactive_stage_replan_autonomy_signal
            ),
            "latest_proactive_stage_replan_changed": (
                latest_proactive_stage_replan_changed
            ),
            "latest_proactive_dispatch_feedback_key": (
                latest_proactive_dispatch_feedback_key
            ),
            "latest_proactive_dispatch_feedback_strategy_key": (
                latest_proactive_dispatch_feedback_strategy_key
            ),
            "latest_proactive_dispatch_feedback_pressure_mode": (
                latest_proactive_dispatch_feedback_pressure_mode
            ),
            "latest_proactive_dispatch_feedback_autonomy_signal": (
                latest_proactive_dispatch_feedback_autonomy_signal
            ),
            "latest_proactive_dispatch_feedback_delivery_mode": (
                latest_proactive_dispatch_feedback_delivery_mode
            ),
            "latest_proactive_dispatch_feedback_sequence_objective": (
                latest_proactive_dispatch_feedback_sequence_objective
            ),
            "latest_proactive_dispatch_feedback_prior_stage_label": (
                latest_proactive_dispatch_feedback_prior_stage_label
            ),
            "latest_proactive_dispatch_feedback_changed": (
                latest_proactive_dispatch_feedback_changed
            ),
            "latest_proactive_dispatch_gate_key": latest_proactive_dispatch_gate_key,
            "latest_proactive_dispatch_gate_decision": (
                latest_proactive_dispatch_gate_decision
            ),
            "latest_proactive_dispatch_gate_retry_after_seconds": (
                latest_proactive_dispatch_gate_retry_after_seconds
            ),
            "latest_proactive_dispatch_gate_strategy_key": (
                latest_proactive_dispatch_gate_strategy_key
            ),
            "latest_proactive_dispatch_gate_changed": (
                latest_proactive_dispatch_gate_changed
            ),
            "latest_proactive_dispatch_envelope_key": (
                latest_proactive_dispatch_envelope_key
            ),
            "latest_proactive_dispatch_envelope_decision": (
                latest_proactive_dispatch_envelope_decision
            ),
            "latest_proactive_dispatch_envelope_strategy_key": (
                latest_proactive_dispatch_envelope_strategy_key
            ),
            "latest_proactive_dispatch_envelope_stage_delivery_mode": (
                latest_proactive_dispatch_envelope_stage_delivery_mode
            ),
            "latest_proactive_dispatch_envelope_reengagement_delivery_mode": (
                latest_proactive_dispatch_envelope_reengagement_delivery_mode
            ),
            "latest_proactive_dispatch_envelope_source_count": (
                latest_proactive_dispatch_envelope_source_count
            ),
            "latest_proactive_stage_state_key": latest_proactive_stage_state_key,
            "latest_proactive_stage_state_mode": latest_proactive_stage_state_mode,
            "latest_proactive_stage_state_queue_status": (
                latest_proactive_stage_state_queue_status
            ),
            "latest_proactive_stage_state_source": (
                latest_proactive_stage_state_source
            ),
            "latest_proactive_stage_transition_key": (
                latest_proactive_stage_transition_key
            ),
            "latest_proactive_stage_transition_mode": (
                latest_proactive_stage_transition_mode
            ),
            "latest_proactive_stage_transition_queue_hint": (
                latest_proactive_stage_transition_queue_hint
            ),
            "latest_proactive_stage_transition_source": (
                latest_proactive_stage_transition_source
            ),
            "latest_proactive_stage_machine_key": latest_proactive_stage_machine_key,
            "latest_proactive_stage_machine_mode": latest_proactive_stage_machine_mode,
            "latest_proactive_stage_machine_lifecycle": (
                latest_proactive_stage_machine_lifecycle
            ),
            "latest_proactive_stage_machine_actionability": (
                latest_proactive_stage_machine_actionability
            ),
            "latest_proactive_stage_machine_source": (
                latest_proactive_stage_machine_source
            ),
            "latest_reengagement_matrix_key": latest_reengagement_matrix_key,
            "latest_reengagement_matrix_selected_strategy": (
                latest_reengagement_matrix_selected_strategy
            ),
            "latest_reengagement_matrix_selected_score": (
                latest_reengagement_matrix_selected_score
            ),
            "latest_reengagement_matrix_top_alternative": (
                latest_reengagement_matrix_top_alternative
            ),
            "latest_reengagement_matrix_blocked_count": (
                latest_reengagement_matrix_blocked_count
            ),
            "latest_reengagement_matrix_learning_mode": (
                latest_reengagement_matrix_learning_mode
            ),
            "latest_reengagement_matrix_learning_context_stratum": (
                latest_reengagement_matrix_learning_context_stratum
            ),
            "latest_reengagement_matrix_learning_signal_count": (
                latest_reengagement_matrix_learning_signal_count
            ),
            "latest_reengagement_matrix_selected_supporting_session_count": (
                latest_reengagement_matrix_selected_supporting_session_count
            ),
            "latest_reengagement_matrix_selected_contextual_supporting_session_count": (
                latest_reengagement_matrix_selected_contextual_supporting_session_count
            ),
            "latest_reengagement_ritual_mode": latest_reengagement_ritual_mode,
            "latest_reengagement_delivery_mode": latest_reengagement_delivery_mode,
            "latest_reengagement_strategy_key": latest_reengagement_strategy_key,
            "latest_reengagement_relational_move": latest_reengagement_relational_move,
            "latest_reengagement_pressure_mode": latest_reengagement_pressure_mode,
            "latest_reengagement_autonomy_signal": (
                latest_reengagement_autonomy_signal
            ),
            "latest_reengagement_sequence_objective": (
                latest_reengagement_sequence_objective
            ),
            "latest_reengagement_somatic_action": latest_reengagement_somatic_action,
            "latest_proactive_followup_dispatch_status": (
                latest_proactive_followup_dispatch_status
            ),
            "latest_proactive_followup_dispatch_source": (
                latest_proactive_followup_dispatch_source
            ),
            "latest_proactive_followup_dispatched_at": (
                latest_proactive_followup_dispatched_at
            ),
            "latest_proactive_followup_dispatch_stage_index": (
                latest_proactive_followup_dispatch_stage_index
            ),
            "latest_proactive_followup_dispatch_stage_label": (
                latest_proactive_followup_dispatch_stage_label
            ),
            "latest_proactive_followup_dispatch_remaining": (
                latest_proactive_followup_dispatch_remaining
            ),
            "latest_proactive_followup_dispatch_progression_action": (
                latest_proactive_followup_dispatch_progression_action
            ),
            "latest_proactive_followup_dispatch_progression_advanced": (
                latest_proactive_followup_dispatch_progression_advanced
            ),
            "latest_runtime_quality_doctor_status": latest_runtime_quality_doctor_status,
            "latest_runtime_quality_doctor_issue_count": (
                latest_runtime_quality_doctor_issue_count
            ),
            "latest_system3_identity_consistency": (
                latest_system3_identity_consistency
            ),
            "latest_system3_identity_anchor": latest_system3_identity_anchor,
            "latest_system3_identity_trajectory_status": (
                latest_system3_identity_trajectory_status
            ),
            "latest_system3_identity_trajectory_target": (
                latest_system3_identity_trajectory_target
            ),
            "latest_system3_identity_trajectory_trigger": (
                latest_system3_identity_trajectory_trigger
            ),
            "latest_system3_growth_stage": latest_system3_growth_stage,
            "latest_system3_user_model_confidence": (
                latest_system3_user_model_confidence
            ),
            "latest_system3_emotional_debt_status": (
                latest_system3_emotional_debt_status
            ),
            "latest_system3_emotional_debt_score": latest_system3_emotional_debt_score,
            "latest_system3_emotional_debt_trajectory_status": (
                latest_system3_emotional_debt_trajectory_status
            ),
            "latest_system3_emotional_debt_trajectory_target": (
                latest_system3_emotional_debt_trajectory_target
            ),
            "latest_system3_emotional_debt_trajectory_trigger": (
                latest_system3_emotional_debt_trajectory_trigger
            ),
            "latest_system3_strategy_audit_status": (
                latest_system3_strategy_audit_status
            ),
            "latest_system3_strategy_audit_trajectory_status": (
                latest_system3_strategy_audit_trajectory_status
            ),
            "latest_system3_strategy_audit_trajectory_target": (
                latest_system3_strategy_audit_trajectory_target
            ),
            "latest_system3_strategy_audit_trajectory_trigger": (
                latest_system3_strategy_audit_trajectory_trigger
            ),
            "latest_system3_strategy_fit": latest_system3_strategy_fit,
            "latest_system3_strategy_supervision_status": (
                latest_system3_strategy_supervision_status
            ),
            "latest_system3_strategy_supervision_mode": (
                latest_system3_strategy_supervision_mode
            ),
            "latest_system3_strategy_supervision_trigger": (
                latest_system3_strategy_supervision_trigger
            ),
            "latest_system3_strategy_supervision_trajectory_status": (
                latest_system3_strategy_supervision_trajectory_status
            ),
            "latest_system3_strategy_supervision_trajectory_target": (
                latest_system3_strategy_supervision_trajectory_target
            ),
            "latest_system3_strategy_supervision_trajectory_trigger": (
                latest_system3_strategy_supervision_trajectory_trigger
            ),
            "latest_system3_moral_reasoning_status": (
                latest_system3_moral_reasoning_status
            ),
            "latest_system3_moral_posture": latest_system3_moral_posture,
            "latest_system3_moral_conflict": latest_system3_moral_conflict,
            "latest_system3_moral_trajectory_status": (
                latest_system3_moral_trajectory_status
            ),
            "latest_system3_moral_trajectory_target": (
                latest_system3_moral_trajectory_target
            ),
            "latest_system3_moral_trajectory_trigger": (
                latest_system3_moral_trajectory_trigger
            ),
            "latest_system3_user_model_evolution_status": (
                latest_system3_user_model_evolution_status
            ),
            "latest_system3_user_model_revision_mode": (
                latest_system3_user_model_revision_mode
            ),
            "latest_system3_user_model_shift_signal": (
                latest_system3_user_model_shift_signal
            ),
            "latest_system3_user_model_trajectory_status": (
                latest_system3_user_model_trajectory_status
            ),
            "latest_system3_user_model_trajectory_target": (
                latest_system3_user_model_trajectory_target
            ),
            "latest_system3_user_model_trajectory_trigger": (
                latest_system3_user_model_trajectory_trigger
            ),
            "latest_system3_expectation_calibration_status": (
                latest_system3_expectation_calibration_status
            ),
            "latest_system3_expectation_calibration_target": (
                latest_system3_expectation_calibration_target
            ),
            "latest_system3_expectation_calibration_trigger": (
                latest_system3_expectation_calibration_trigger
            ),
            "latest_system3_expectation_calibration_trajectory_status": (
                latest_system3_expectation_calibration_trajectory_status
            ),
            "latest_system3_expectation_calibration_trajectory_target": (
                latest_system3_expectation_calibration_trajectory_target
            ),
            "latest_system3_expectation_calibration_trajectory_trigger": (
                latest_system3_expectation_calibration_trajectory_trigger
            ),
            "latest_system3_dependency_governance_status": (
                latest_system3_dependency_governance_status
            ),
            "latest_system3_dependency_governance_target": (
                latest_system3_dependency_governance_target
            ),
            "latest_system3_dependency_governance_trigger": (
                latest_system3_dependency_governance_trigger
            ),
            "latest_system3_dependency_governance_trajectory_status": (
                latest_system3_dependency_governance_trajectory_status
            ),
            "latest_system3_dependency_governance_trajectory_target": (
                latest_system3_dependency_governance_trajectory_target
            ),
            "latest_system3_dependency_governance_trajectory_trigger": (
                latest_system3_dependency_governance_trajectory_trigger
            ),
            "latest_system3_autonomy_governance_status": (
                latest_system3_autonomy_governance_status
            ),
            "latest_system3_autonomy_governance_target": (
                latest_system3_autonomy_governance_target
            ),
            "latest_system3_autonomy_governance_trigger": (
                latest_system3_autonomy_governance_trigger
            ),
            "latest_system3_autonomy_governance_trajectory_status": (
                latest_system3_autonomy_governance_trajectory_status
            ),
            "latest_system3_autonomy_governance_trajectory_target": (
                latest_system3_autonomy_governance_trajectory_target
            ),
            "latest_system3_autonomy_governance_trajectory_trigger": (
                latest_system3_autonomy_governance_trajectory_trigger
            ),
            "latest_system3_boundary_governance_status": (
                latest_system3_boundary_governance_status
            ),
            "latest_system3_boundary_governance_target": (
                latest_system3_boundary_governance_target
            ),
            "latest_system3_boundary_governance_trigger": (
                latest_system3_boundary_governance_trigger
            ),
            "latest_system3_boundary_governance_trajectory_status": (
                latest_system3_boundary_governance_trajectory_status
            ),
            "latest_system3_boundary_governance_trajectory_target": (
                latest_system3_boundary_governance_trajectory_target
            ),
            "latest_system3_boundary_governance_trajectory_trigger": (
                latest_system3_boundary_governance_trajectory_trigger
            ),
            "latest_system3_support_governance_status": (
                latest_system3_support_governance_status
            ),
            "latest_system3_support_governance_target": (
                latest_system3_support_governance_target
            ),
            "latest_system3_support_governance_trigger": (
                latest_system3_support_governance_trigger
            ),
            "latest_system3_support_governance_trajectory_status": (
                latest_system3_support_governance_trajectory_status
            ),
            "latest_system3_support_governance_trajectory_target": (
                latest_system3_support_governance_trajectory_target
            ),
            "latest_system3_support_governance_trajectory_trigger": (
                latest_system3_support_governance_trajectory_trigger
            ),
            "latest_system3_continuity_governance_status": (
                latest_system3_continuity_governance_status
            ),
            "latest_system3_continuity_governance_target": (
                latest_system3_continuity_governance_target
            ),
            "latest_system3_continuity_governance_trigger": (
                latest_system3_continuity_governance_trigger
            ),
            "latest_system3_continuity_governance_trajectory_status": (
                latest_system3_continuity_governance_trajectory_status
            ),
            "latest_system3_continuity_governance_trajectory_target": (
                latest_system3_continuity_governance_trajectory_target
            ),
            "latest_system3_continuity_governance_trajectory_trigger": (
                latest_system3_continuity_governance_trajectory_trigger
            ),
            "latest_system3_repair_governance_status": (
                latest_system3_repair_governance_status
            ),
            "latest_system3_repair_governance_target": (
                latest_system3_repair_governance_target
            ),
            "latest_system3_repair_governance_trigger": (
                latest_system3_repair_governance_trigger
            ),
            "latest_system3_repair_governance_trajectory_status": (
                latest_system3_repair_governance_trajectory_status
            ),
            "latest_system3_repair_governance_trajectory_target": (
                latest_system3_repair_governance_trajectory_target
            ),
            "latest_system3_repair_governance_trajectory_trigger": (
                latest_system3_repair_governance_trajectory_trigger
            ),
            "latest_system3_attunement_governance_status": (
                latest_system3_attunement_governance_status
            ),
            "latest_system3_attunement_governance_target": (
                latest_system3_attunement_governance_target
            ),
            "latest_system3_attunement_governance_trigger": (
                latest_system3_attunement_governance_trigger
            ),
            "latest_system3_attunement_governance_trajectory_status": (
                latest_system3_attunement_governance_trajectory_status
            ),
            "latest_system3_attunement_governance_trajectory_target": (
                latest_system3_attunement_governance_trajectory_target
            ),
            "latest_system3_attunement_governance_trajectory_trigger": (
                latest_system3_attunement_governance_trajectory_trigger
            ),
            "latest_system3_trust_governance_status": (
                latest_system3_trust_governance_status
            ),
            "latest_system3_trust_governance_target": (
                latest_system3_trust_governance_target
            ),
            "latest_system3_trust_governance_trigger": (
                latest_system3_trust_governance_trigger
            ),
            "latest_system3_trust_governance_trajectory_status": (
                latest_system3_trust_governance_trajectory_status
            ),
            "latest_system3_trust_governance_trajectory_target": (
                latest_system3_trust_governance_trajectory_target
            ),
            "latest_system3_trust_governance_trajectory_trigger": (
                latest_system3_trust_governance_trajectory_trigger
            ),
            "latest_system3_clarity_governance_status": (
                latest_system3_clarity_governance_status
            ),
            "latest_system3_clarity_governance_target": (
                latest_system3_clarity_governance_target
            ),
            "latest_system3_clarity_governance_trigger": (
                latest_system3_clarity_governance_trigger
            ),
            "latest_system3_clarity_governance_trajectory_status": (
                latest_system3_clarity_governance_trajectory_status
            ),
            "latest_system3_clarity_governance_trajectory_target": (
                latest_system3_clarity_governance_trajectory_target
            ),
            "latest_system3_clarity_governance_trajectory_trigger": (
                latest_system3_clarity_governance_trajectory_trigger
            ),
            "latest_system3_pacing_governance_status": (
                latest_system3_pacing_governance_status
            ),
            "latest_system3_pacing_governance_target": (
                latest_system3_pacing_governance_target
            ),
            "latest_system3_pacing_governance_trigger": (
                latest_system3_pacing_governance_trigger
            ),
            "latest_system3_pacing_governance_trajectory_status": (
                latest_system3_pacing_governance_trajectory_status
            ),
            "latest_system3_pacing_governance_trajectory_target": (
                latest_system3_pacing_governance_trajectory_target
            ),
            "latest_system3_pacing_governance_trajectory_trigger": (
                latest_system3_pacing_governance_trajectory_trigger
            ),
            "latest_system3_commitment_governance_status": (
                latest_system3_commitment_governance_status
            ),
            "latest_system3_commitment_governance_target": (
                latest_system3_commitment_governance_target
            ),
            "latest_system3_commitment_governance_trigger": (
                latest_system3_commitment_governance_trigger
            ),
            "latest_system3_commitment_governance_trajectory_status": (
                latest_system3_commitment_governance_trajectory_status
            ),
            "latest_system3_commitment_governance_trajectory_target": (
                latest_system3_commitment_governance_trajectory_target
            ),
            "latest_system3_commitment_governance_trajectory_trigger": (
                latest_system3_commitment_governance_trajectory_trigger
            ),
            "latest_system3_disclosure_governance_status": (
                latest_system3_disclosure_governance_status
            ),
            "latest_system3_disclosure_governance_target": (
                latest_system3_disclosure_governance_target
            ),
            "latest_system3_disclosure_governance_trigger": (
                latest_system3_disclosure_governance_trigger
            ),
            "latest_system3_disclosure_governance_trajectory_status": (
                latest_system3_disclosure_governance_trajectory_status
            ),
            "latest_system3_disclosure_governance_trajectory_target": (
                latest_system3_disclosure_governance_trajectory_target
            ),
            "latest_system3_disclosure_governance_trajectory_trigger": (
                latest_system3_disclosure_governance_trajectory_trigger
            ),
            "latest_system3_reciprocity_governance_status": (
                latest_system3_reciprocity_governance_status
            ),
            "latest_system3_reciprocity_governance_target": (
                latest_system3_reciprocity_governance_target
            ),
            "latest_system3_reciprocity_governance_trigger": (
                latest_system3_reciprocity_governance_trigger
            ),
            "latest_system3_reciprocity_governance_trajectory_status": (
                latest_system3_reciprocity_governance_trajectory_status
            ),
            "latest_system3_reciprocity_governance_trajectory_target": (
                latest_system3_reciprocity_governance_trajectory_target
            ),
            "latest_system3_reciprocity_governance_trajectory_trigger": (
                latest_system3_reciprocity_governance_trajectory_trigger
            ),
            "latest_system3_pressure_governance_status": (
                latest_system3_pressure_governance_status
            ),
            "latest_system3_pressure_governance_target": (
                latest_system3_pressure_governance_target
            ),
            "latest_system3_pressure_governance_trigger": (
                latest_system3_pressure_governance_trigger
            ),
            "latest_system3_pressure_governance_trajectory_status": (
                latest_system3_pressure_governance_trajectory_status
            ),
            "latest_system3_pressure_governance_trajectory_target": (
                latest_system3_pressure_governance_trajectory_target
            ),
            "latest_system3_pressure_governance_trajectory_trigger": (
                latest_system3_pressure_governance_trajectory_trigger
            ),
            "latest_system3_relational_governance_status": (
                latest_system3_relational_governance_status
            ),
            "latest_system3_relational_governance_target": (
                latest_system3_relational_governance_target
            ),
            "latest_system3_relational_governance_trigger": (
                latest_system3_relational_governance_trigger
            ),
            "latest_system3_relational_governance_trajectory_status": (
                latest_system3_relational_governance_trajectory_status
            ),
            "latest_system3_relational_governance_trajectory_target": (
                latest_system3_relational_governance_trajectory_target
            ),
            "latest_system3_relational_governance_trajectory_trigger": (
                latest_system3_relational_governance_trajectory_trigger
            ),
            "latest_system3_safety_governance_status": (
                latest_system3_safety_governance_status
            ),
            "latest_system3_safety_governance_target": (
                latest_system3_safety_governance_target
            ),
            "latest_system3_safety_governance_trigger": (
                latest_system3_safety_governance_trigger
            ),
            "latest_system3_safety_governance_trajectory_status": (
                latest_system3_safety_governance_trajectory_status
            ),
            "latest_system3_safety_governance_trajectory_target": (
                latest_system3_safety_governance_trajectory_target
            ),
            "latest_system3_safety_governance_trajectory_trigger": (
                latest_system3_safety_governance_trajectory_trigger
            ),
            "latest_system3_progress_governance_status": (
                latest_system3_progress_governance_status
            ),
            "latest_system3_progress_governance_target": (
                latest_system3_progress_governance_target
            ),
            "latest_system3_progress_governance_trigger": (
                latest_system3_progress_governance_trigger
            ),
            "latest_system3_progress_governance_trajectory_status": (
                latest_system3_progress_governance_trajectory_status
            ),
            "latest_system3_progress_governance_trajectory_target": (
                latest_system3_progress_governance_trajectory_target
            ),
            "latest_system3_progress_governance_trajectory_trigger": (
                latest_system3_progress_governance_trajectory_trigger
            ),
            "latest_system3_stability_governance_status": (
                latest_system3_stability_governance_status
            ),
            "latest_system3_stability_governance_target": (
                latest_system3_stability_governance_target
            ),
            "latest_system3_stability_governance_trigger": (
                latest_system3_stability_governance_trigger
            ),
            "latest_system3_stability_governance_trajectory_status": (
                latest_system3_stability_governance_trajectory_status
            ),
            "latest_system3_stability_governance_trajectory_target": (
                latest_system3_stability_governance_trajectory_target
            ),
            "latest_system3_stability_governance_trajectory_trigger": (
                latest_system3_stability_governance_trajectory_trigger
            ),
            "latest_system3_growth_transition_status": (
                latest_system3_growth_transition_status
            ),
            "latest_system3_growth_transition_target": (
                latest_system3_growth_transition_target
            ),
            "latest_system3_growth_transition_trigger": (
                latest_system3_growth_transition_trigger
            ),
            "latest_system3_growth_transition_readiness": (
                latest_system3_growth_transition_readiness
            ),
            "latest_system3_growth_transition_trajectory_status": (
                latest_system3_growth_transition_trajectory_status
            ),
            "latest_system3_growth_transition_trajectory_target": (
                latest_system3_growth_transition_trajectory_target
            ),
            "latest_system3_growth_transition_trajectory_trigger": (
                latest_system3_growth_transition_trajectory_trigger
            ),
            "latest_system3_version_migration_status": (
                latest_system3_version_migration_status
            ),
            "latest_system3_version_migration_scope": (
                latest_system3_version_migration_scope
            ),
            "latest_system3_version_migration_trigger": (
                latest_system3_version_migration_trigger
            ),
            "latest_system3_version_migration_trajectory_status": (
                latest_system3_version_migration_trajectory_status
            ),
            "latest_system3_version_migration_trajectory_target": (
                latest_system3_version_migration_trajectory_target
            ),
            "latest_system3_version_migration_trajectory_trigger": (
                latest_system3_version_migration_trajectory_trigger
            ),
            "latest_response_post_audit_status": latest_response_post_audit_status,
            "latest_response_normalization_final_status": (
                latest_response_normalization_final_status
            ),
            "latest_turbulence_risk": latest_turbulence_risk,
            "latest_working_memory_size": latest_memory_items,
            "latest_memory_recall_count": latest_memory_recall_count,
            "latest_memory_filtered_count": latest_memory_filtered_count,
            "latest_memory_blocked_count": latest_memory_blocked_count,
            "latest_memory_pinned_count": latest_memory_pinned_count,
            "latest_memory_evicted_count": latest_memory_evicted_count,
            "output_quality_assessed_turn_count": quality_summary["assessed_turn_count"],
            "avg_response_word_count": quality_summary["avg_response_word_count"],
            "latest_response_word_count": quality_summary["latest_response_word_count"],
            "response_length_slope": quality_summary["response_length_slope"],
            "avg_response_lexical_diversity": quality_summary[
                "avg_response_lexical_diversity"
            ],
            "latest_response_lexical_diversity": quality_summary[
                "latest_response_lexical_diversity"
            ],
            "response_lexical_diversity_slope": quality_summary[
                "response_lexical_diversity_slope"
            ],
            "avg_response_information_density": quality_summary[
                "avg_response_information_density"
            ],
            "latest_response_information_density": quality_summary[
                "latest_response_information_density"
            ],
            "response_information_density_slope": quality_summary[
                "response_information_density_slope"
            ],
            "repeated_opening_turn_count": quality_summary[
                "repeated_opening_turn_count"
            ],
            "output_quality_issue_count": quality_summary["output_quality_issue_count"],
            "output_quality_issues": quality_summary["output_quality_issues"],
            "output_quality_status": quality_summary["output_quality_status"],
        }

    def _compute_session_duration_seconds(
        self,
        *,
        started_at: str | None,
        last_event_at: str | None,
    ) -> float:
        started = _parse_datetime(started_at)
        ended = _parse_datetime(last_event_at)
        if started is None or ended is None:
            return 0.0
        return round(max(0.0, (ended - started).total_seconds()), 3)

    def _build_preference_record(
        self,
        summary: dict[str, Any],
        *,
        strategy: str,
        context_stratum: str,
    ) -> StrategyPreferenceRecord:
        session_duration_seconds = float(summary.get("session_duration_seconds") or 0.0)
        turn_count = int(summary.get("turn_count") or 0)
        bid_rate = float(summary.get("bid_turn_toward_rate") or 0.0)
        safety = float(summary.get("avg_psychological_safety") or 0.0)

        quality_floor_score = 1.0
        filtering_reasons: list[str] = []
        if int(summary.get("response_post_audit_total_violation_count") or 0) > 0:
            quality_floor_score -= 0.35
            filtering_reasons.append("post_audit_violations")
        if int(summary.get("llm_failure_count") or 0) > 0:
            quality_floor_score -= 0.2
            filtering_reasons.append("runtime_failures")
        quality_status = str(summary.get("output_quality_status") or "stable")
        if quality_status == "watch":
            quality_floor_score -= 0.2
            filtering_reasons.append("quality_watch")
        elif quality_status == "degrading":
            quality_floor_score -= 0.4
            filtering_reasons.append("quality_degrading")
        runtime_quality_status = str(
            summary.get("latest_runtime_quality_doctor_status") or "pass"
        )
        if runtime_quality_status == "watch":
            quality_floor_score -= 0.1
            filtering_reasons.append("runtime_quality_doctor_watch")
        elif runtime_quality_status == "revise":
            quality_floor_score -= 0.2
            filtering_reasons.append("runtime_quality_doctor_revise")
        identity_trajectory_status = str(
            summary.get("latest_system3_identity_trajectory_status") or "stable"
        )
        if identity_trajectory_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_identity_trajectory_watch")
        elif identity_trajectory_status == "recenter":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_identity_trajectory_recenter")
        strategy_audit_status = str(
            summary.get("latest_system3_strategy_audit_status") or "pass"
        )
        if strategy_audit_status == "watch":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_strategy_audit_watch")
        elif strategy_audit_status == "revise":
            quality_floor_score -= 0.2
            filtering_reasons.append("system3_strategy_audit_revise")
        strategy_audit_trajectory_status = str(
            summary.get("latest_system3_strategy_audit_trajectory_status")
            or "stable"
        )
        if strategy_audit_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_strategy_audit_trajectory_watch")
        elif strategy_audit_trajectory_status == "corrective":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_strategy_audit_trajectory_corrective")
        strategy_supervision_status = str(
            summary.get("latest_system3_strategy_supervision_status") or "pass"
        )
        if strategy_supervision_status == "watch":
            quality_floor_score -= 0.08
            filtering_reasons.append("system3_strategy_supervision_watch")
        elif strategy_supervision_status == "revise":
            quality_floor_score -= 0.18
            filtering_reasons.append("system3_strategy_supervision_revise")
        strategy_supervision_trajectory_status = str(
            summary.get("latest_system3_strategy_supervision_trajectory_status")
            or "stable"
        )
        if strategy_supervision_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_strategy_supervision_trajectory_watch")
        elif strategy_supervision_trajectory_status == "tighten":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_strategy_supervision_trajectory_tighten"
            )
        moral_reasoning_status = str(
            summary.get("latest_system3_moral_reasoning_status") or "pass"
        )
        if moral_reasoning_status == "watch":
            quality_floor_score -= 0.08
            filtering_reasons.append("system3_moral_reasoning_watch")
        elif moral_reasoning_status == "revise":
            quality_floor_score -= 0.18
            filtering_reasons.append("system3_moral_reasoning_revise")
        moral_trajectory_status = str(
            summary.get("latest_system3_moral_trajectory_status") or "stable"
        )
        if moral_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_moral_trajectory_watch")
        elif moral_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_moral_trajectory_recenter")
        user_model_evolution_status = str(
            summary.get("latest_system3_user_model_evolution_status") or "pass"
        )
        if user_model_evolution_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_user_model_evolution_watch")
        elif user_model_evolution_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_user_model_evolution_revise")
        user_model_trajectory_status = str(
            summary.get("latest_system3_user_model_trajectory_status") or "stable"
        )
        if user_model_trajectory_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_user_model_trajectory_watch")
        elif user_model_trajectory_status == "recenter":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_user_model_trajectory_recenter")
        expectation_calibration_status = str(
            summary.get("latest_system3_expectation_calibration_status") or "pass"
        )
        if expectation_calibration_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_expectation_calibration_watch")
        elif expectation_calibration_status == "revise":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_expectation_calibration_revise")
        expectation_calibration_trajectory_status = str(
            summary.get("latest_system3_expectation_calibration_trajectory_status")
            or "stable"
        )
        if expectation_calibration_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_expectation_calibration_trajectory_watch"
            )
        elif expectation_calibration_trajectory_status == "reset":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_expectation_calibration_trajectory_reset"
            )
        dependency_governance_status = str(
            summary.get("latest_system3_dependency_governance_status") or "pass"
        )
        if dependency_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_dependency_governance_watch")
        elif dependency_governance_status == "revise":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_dependency_governance_revise")
        dependency_governance_trajectory_status = str(
            summary.get("latest_system3_dependency_governance_trajectory_status")
            or "stable"
        )
        if dependency_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_dependency_governance_trajectory_watch"
            )
        elif dependency_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_dependency_governance_trajectory_recenter"
            )
        autonomy_governance_status = str(
            summary.get("latest_system3_autonomy_governance_status") or "pass"
        )
        if autonomy_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_autonomy_governance_watch")
        elif autonomy_governance_status == "revise":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_autonomy_governance_revise")
        autonomy_governance_trajectory_status = str(
            summary.get("latest_system3_autonomy_governance_trajectory_status")
            or "stable"
        )
        if autonomy_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_autonomy_governance_trajectory_watch"
            )
        elif autonomy_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_autonomy_governance_trajectory_recenter"
            )
        boundary_governance_status = str(
            summary.get("latest_system3_boundary_governance_status") or "pass"
        )
        if boundary_governance_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_boundary_governance_watch")
        elif boundary_governance_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_boundary_governance_revise")
        boundary_governance_trajectory_status = str(
            summary.get("latest_system3_boundary_governance_trajectory_status")
            or "stable"
        )
        if boundary_governance_trajectory_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append(
                "system3_boundary_governance_trajectory_watch"
            )
        elif boundary_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.11
            filtering_reasons.append(
                "system3_boundary_governance_trajectory_recenter"
            )
        support_governance_status = str(
            summary.get("latest_system3_support_governance_status") or "pass"
        )
        if support_governance_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_support_governance_watch")
        elif support_governance_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_support_governance_revise")
        support_governance_trajectory_status = str(
            summary.get("latest_system3_support_governance_trajectory_status")
            or "stable"
        )
        if support_governance_trajectory_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append(
                "system3_support_governance_trajectory_watch"
            )
        elif support_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.11
            filtering_reasons.append(
                "system3_support_governance_trajectory_recenter"
            )
        continuity_governance_status = str(
            summary.get("latest_system3_continuity_governance_status") or "pass"
        )
        if continuity_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_continuity_governance_watch")
        elif continuity_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_continuity_governance_revise")
        continuity_governance_trajectory_status = str(
            summary.get("latest_system3_continuity_governance_trajectory_status")
            or "stable"
        )
        if continuity_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_continuity_governance_trajectory_watch"
            )
        elif continuity_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_continuity_governance_trajectory_recenter"
            )
        repair_governance_status = str(
            summary.get("latest_system3_repair_governance_status") or "pass"
        )
        if repair_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_repair_governance_watch")
        elif repair_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_repair_governance_revise")
        repair_governance_trajectory_status = str(
            summary.get("latest_system3_repair_governance_trajectory_status")
            or "stable"
        )
        if repair_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_repair_governance_trajectory_watch"
            )
        elif repair_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_repair_governance_trajectory_recenter"
            )
        attunement_governance_status = str(
            summary.get("latest_system3_attunement_governance_status") or "pass"
        )
        if attunement_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_attunement_governance_watch")
        elif attunement_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_attunement_governance_revise")
        attunement_governance_trajectory_status = str(
            summary.get("latest_system3_attunement_governance_trajectory_status")
            or "stable"
        )
        if attunement_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_attunement_governance_trajectory_watch"
            )
        elif attunement_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_attunement_governance_trajectory_recenter"
            )
        trust_governance_status = str(
            summary.get("latest_system3_trust_governance_status") or "pass"
        )
        if trust_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_trust_governance_watch")
        elif trust_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_trust_governance_revise")
        trust_governance_trajectory_status = str(
            summary.get("latest_system3_trust_governance_trajectory_status")
            or "stable"
        )
        if trust_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_trust_governance_trajectory_watch"
            )
        elif trust_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_trust_governance_trajectory_recenter"
            )
        clarity_governance_status = str(
            summary.get("latest_system3_clarity_governance_status") or "pass"
        )
        if clarity_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_clarity_governance_watch")
        elif clarity_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_clarity_governance_revise")
        clarity_governance_trajectory_status = str(
            summary.get("latest_system3_clarity_governance_trajectory_status")
            or "stable"
        )
        if clarity_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_clarity_governance_trajectory_watch"
            )
        elif clarity_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_clarity_governance_trajectory_recenter"
            )
        pacing_governance_status = str(
            summary.get("latest_system3_pacing_governance_status") or "pass"
        )
        if pacing_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_pacing_governance_watch")
        elif pacing_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_pacing_governance_revise")
        pacing_governance_trajectory_status = str(
            summary.get("latest_system3_pacing_governance_trajectory_status")
            or "stable"
        )
        if pacing_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_pacing_governance_trajectory_watch"
            )
        elif pacing_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_pacing_governance_trajectory_recenter"
            )
        commitment_governance_status = str(
            summary.get("latest_system3_commitment_governance_status") or "pass"
        )
        if commitment_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_commitment_governance_watch")
        elif commitment_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_commitment_governance_revise")
        commitment_governance_trajectory_status = str(
            summary.get("latest_system3_commitment_governance_trajectory_status")
            or "stable"
        )
        if commitment_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_commitment_governance_trajectory_watch"
            )
        elif commitment_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_commitment_governance_trajectory_recenter"
            )
        disclosure_governance_status = str(
            summary.get("latest_system3_disclosure_governance_status") or "pass"
        )
        if disclosure_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_disclosure_governance_watch")
        elif disclosure_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_disclosure_governance_revise")
        disclosure_governance_trajectory_status = str(
            summary.get("latest_system3_disclosure_governance_trajectory_status")
            or "stable"
        )
        if disclosure_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_disclosure_governance_trajectory_watch"
            )
        elif disclosure_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_disclosure_governance_trajectory_recenter"
            )
        reciprocity_governance_status = str(
            summary.get("latest_system3_reciprocity_governance_status") or "pass"
        )
        if reciprocity_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_reciprocity_governance_watch")
        elif reciprocity_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_reciprocity_governance_revise")
        reciprocity_governance_trajectory_status = str(
            summary.get("latest_system3_reciprocity_governance_trajectory_status")
            or "stable"
        )
        if reciprocity_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_reciprocity_governance_trajectory_watch"
            )
        elif reciprocity_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_reciprocity_governance_trajectory_recenter"
            )
        pressure_governance_status = str(
            summary.get("latest_system3_pressure_governance_status") or "pass"
        )
        if pressure_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_pressure_governance_watch")
        elif pressure_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_pressure_governance_revise")
        pressure_governance_trajectory_status = str(
            summary.get("latest_system3_pressure_governance_trajectory_status")
            or "stable"
        )
        if pressure_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_pressure_governance_trajectory_watch"
            )
        elif pressure_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_pressure_governance_trajectory_recenter"
            )
        relational_governance_status = str(
            summary.get("latest_system3_relational_governance_status") or "pass"
        )
        if relational_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_relational_governance_watch")
        elif relational_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_relational_governance_revise")
        relational_governance_trajectory_status = str(
            summary.get("latest_system3_relational_governance_trajectory_status")
            or "stable"
        )
        if relational_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_relational_governance_trajectory_watch"
            )
        elif relational_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_relational_governance_trajectory_recenter"
            )
        safety_governance_status = str(
            summary.get("latest_system3_safety_governance_status") or "pass"
        )
        if safety_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_safety_governance_watch")
        elif safety_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_safety_governance_revise")
        safety_governance_trajectory_status = str(
            summary.get("latest_system3_safety_governance_trajectory_status")
            or "stable"
        )
        if safety_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_safety_governance_trajectory_watch"
            )
        elif safety_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_safety_governance_trajectory_recenter"
            )
        progress_governance_status = str(
            summary.get("latest_system3_progress_governance_status") or "pass"
        )
        if progress_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_progress_governance_watch")
        elif progress_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_progress_governance_revise")
        progress_governance_trajectory_status = str(
            summary.get("latest_system3_progress_governance_trajectory_status")
            or "stable"
        )
        if progress_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_progress_governance_trajectory_watch"
            )
        elif progress_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_progress_governance_trajectory_recenter"
            )
        stability_governance_status = str(
            summary.get("latest_system3_stability_governance_status") or "pass"
        )
        if stability_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_stability_governance_watch")
        elif stability_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_stability_governance_revise")
        stability_governance_trajectory_status = str(
            summary.get("latest_system3_stability_governance_trajectory_status")
            or "stable"
        )
        if stability_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_stability_governance_trajectory_watch"
            )
        elif stability_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_stability_governance_trajectory_recenter"
            )
        growth_transition_status = str(
            summary.get("latest_system3_growth_transition_status") or "stable"
        )
        if growth_transition_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_growth_transition_watch")
        elif growth_transition_status == "redirect":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_growth_transition_redirect")
        growth_transition_trajectory_status = str(
            summary.get("latest_system3_growth_transition_trajectory_status")
            or "stable"
        )
        if growth_transition_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_growth_transition_trajectory_watch")
        elif growth_transition_trajectory_status == "redirect":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_growth_transition_trajectory_redirect")
        version_migration_status = str(
            summary.get("latest_system3_version_migration_status") or "pass"
        )
        if version_migration_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_version_migration_watch")
        elif version_migration_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_version_migration_revise")
        version_migration_trajectory_status = str(
            summary.get("latest_system3_version_migration_trajectory_status")
            or "stable"
        )
        if version_migration_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_version_migration_trajectory_watch")
        elif version_migration_trajectory_status == "hold":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_version_migration_trajectory_hold")
        emotional_debt_status = str(
            summary.get("latest_system3_emotional_debt_status") or "low"
        )
        if emotional_debt_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_emotional_debt_watch")
        elif emotional_debt_status == "elevated":
            quality_floor_score -= 0.15
            filtering_reasons.append("system3_emotional_debt_elevated")
        emotional_debt_trajectory_status = str(
            summary.get("latest_system3_emotional_debt_trajectory_status")
            or "stable"
        )
        if emotional_debt_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_emotional_debt_trajectory_watch")
        elif emotional_debt_trajectory_status == "decompression_required":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_emotional_debt_trajectory_decompression"
            )
        if safety and safety < 0.6:
            quality_floor_score -= 0.15
            filtering_reasons.append("low_psychological_safety")
        quality_floor_score = max(0.0, round(quality_floor_score, 3))
        quality_floor_pass = quality_floor_score >= 0.65

        duration_signal = min(session_duration_seconds / 180.0, 1.0)
        relational_signal = round((bid_rate * 0.5) + (safety * 0.5), 3)
        avg_seconds_per_turn = float(summary.get("avg_seconds_per_turn") or 0.0)
        noise_penalty = 0.0
        if turn_count >= 4 and avg_seconds_per_turn < 0.5:
            noise_penalty = 0.1

        denoised_preference_score = max(
            0.0,
            round(
                (quality_floor_score * 0.6)
                + (duration_signal * 0.25)
                + (relational_signal * 0.15)
                - noise_penalty,
                3,
            ),
        )

        return StrategyPreferenceRecord(
            session_id=str(summary.get("session_id")),
            strategy=strategy,
            source=str(summary.get("session_source") or "session"),
            turn_count=turn_count,
            session_duration_seconds=session_duration_seconds,
            duration_signal=round(duration_signal, 3),
            relational_signal=relational_signal,
            quality_floor_score=quality_floor_score,
            quality_floor_pass=quality_floor_pass,
            noise_penalty=round(noise_penalty, 3),
            denoised_preference_score=denoised_preference_score,
            context_stratum=context_stratum,
            filtering_reasons=filtering_reasons,
        )

    def _build_strategy_preference_record(
        self,
        summary: dict[str, Any],
    ) -> StrategyPreferenceRecord:
        return self._build_preference_record(
            summary,
            strategy=str(summary.get("latest_strategy") or "unknown"),
            context_stratum=self._build_strategy_context_stratum(summary),
        )

    def _build_reengagement_preference_record(
        self,
        summary: dict[str, Any],
    ) -> StrategyPreferenceRecord:
        return self._build_preference_record(
            summary,
            strategy=str(summary.get("latest_reengagement_strategy_key") or "unknown"),
            context_stratum=self._build_reengagement_context_stratum(summary),
        )

    def _build_strategy_context_stratum(
        self,
        summary: dict[str, Any],
    ) -> str:
        flags: list[str] = []
        if int(summary.get("rupture_detected_count") or 0) > 0:
            flags.append("repair_pressure")
        if int(summary.get("knowledge_boundary_intervention_count") or 0) > 0:
            flags.append("boundary_pressure")
        if int(summary.get("dependency_risk_elevated_count") or 0) > 0:
            flags.append("dependency_pressure")
        quality_status = str(summary.get("output_quality_status") or "stable")
        if quality_status in {"watch", "degrading"}:
            flags.append(f"quality_{quality_status}")
        if not flags:
            flags.append("steady_progress")
        return "+".join(flags[:3])

    def _build_reengagement_context_stratum(
        self,
        summary: dict[str, Any],
    ) -> str:
        flags: list[str] = []
        if (
            int(summary.get("rupture_detected_count") or 0) > 0
            or str(summary.get("latest_system3_repair_governance_status") or "pass")
            in {"watch", "revise"}
            or str(
                summary.get("latest_system3_repair_governance_trajectory_status")
                or "stable"
            )
            == "recenter"
            or str(summary.get("latest_reengagement_pressure_mode") or "")
            == "repair_soft"
        ):
            flags.append("repair_pressure")
        if (
            int(summary.get("knowledge_boundary_intervention_count") or 0) > 0
            or str(summary.get("latest_system3_boundary_governance_status") or "pass")
            in {"watch", "revise"}
            or str(
                summary.get("latest_system3_boundary_governance_trajectory_status")
                or "stable"
            )
            == "recenter"
        ):
            flags.append("boundary_pressure")
        if (
            int(summary.get("dependency_risk_elevated_count") or 0) > 0
            or str(summary.get("latest_system3_dependency_governance_status") or "pass")
            in {"watch", "revise"}
            or str(
                summary.get("latest_system3_dependency_governance_trajectory_status")
                or "stable"
            )
            == "recenter"
        ):
            flags.append("dependency_pressure")
        if (
            str(summary.get("latest_system3_pressure_governance_status") or "pass")
            in {"watch", "revise"}
            or str(summary.get("latest_system3_stability_governance_status") or "pass")
            in {"watch", "revise"}
        ):
            flags.append("quality_watch")
        if not flags:
            flags.append("steady_progress")
        return "+".join(flags[:3])

    def _build_output_quality_samples(
        self,
        turn_records: list[TurnRecord],
    ) -> list[OutputQualitySample]:
        samples: list[OutputQualitySample] = []
        seen_content_tokens: set[str] = set()
        for turn in turn_records:
            if not turn.assistant_message:
                continue
            tokens = _tokenize_text(turn.assistant_message)
            if not tokens:
                continue
            content_tokens = _content_tokens(tokens)
            token_set = set(tokens)
            content_set = set(content_tokens)
            novel_content_tokens = content_set - seen_content_tokens
            information_density = (
                round(len(novel_content_tokens) / len(content_set), 3)
                if content_set
                else round(len(token_set) / len(tokens), 3)
            )
            if content_set:
                seen_content_tokens.update(content_set)
            samples.append(
                OutputQualitySample(
                    turn_index=turn.turn_index,
                    word_count=len(tokens),
                    lexical_diversity=round(len(token_set) / len(tokens), 3),
                    information_density=information_density,
                    opening_signature=" ".join(tokens[:3]),
                )
            )
        return samples

    def _build_output_quality_summary(
        self,
        samples: list[OutputQualitySample],
    ) -> dict[str, Any]:
        if not samples:
            return {
                "assessed_turn_count": 0,
                "avg_response_word_count": None,
                "latest_response_word_count": None,
                "response_length_slope": 0.0,
                "avg_response_lexical_diversity": None,
                "latest_response_lexical_diversity": None,
                "response_lexical_diversity_slope": 0.0,
                "avg_response_information_density": None,
                "latest_response_information_density": None,
                "response_information_density_slope": 0.0,
                "repeated_opening_turn_count": 0,
                "output_quality_issue_count": 0,
                "output_quality_issues": [],
                "output_quality_status": "stable",
            }

        word_counts = [sample.word_count for sample in samples]
        lexical_diversities = [sample.lexical_diversity for sample in samples]
        information_densities = [sample.information_density for sample in samples]
        opening_counts: dict[str, int] = {}
        for sample in samples:
            if not sample.opening_signature:
                continue
            opening_counts[sample.opening_signature] = (
                opening_counts.get(sample.opening_signature, 0) + 1
            )
        repeated_opening_turn_count = sum(
            count for count in opening_counts.values() if count > 1
        )

        issues: list[str] = []
        if len(samples) >= 3:
            latest_word_count = word_counts[-1]
            first_word_count = word_counts[0]
            if latest_word_count >= max(first_word_count + 12, int(first_word_count * 1.75)):
                if _series_slope(word_counts) >= 4.0:
                    issues.append("length_bloat")
            if lexical_diversities[0] - lexical_diversities[-1] >= 0.2:
                if _series_slope(lexical_diversities) <= -0.05:
                    issues.append("lexical_diversity_drop")
            if information_densities[0] - information_densities[-1] >= 0.2:
                if _series_slope(information_densities) <= -0.05:
                    issues.append("information_density_drop")
        if repeated_opening_turn_count >= 2:
            issues.append("template_repetition")

        if len(issues) >= 2:
            status = "degrading"
        elif issues:
            status = "watch"
        else:
            status = "stable"

        return {
            "assessed_turn_count": len(samples),
            "avg_response_word_count": round(mean(word_counts), 3),
            "latest_response_word_count": word_counts[-1],
            "response_length_slope": _series_slope(word_counts),
            "avg_response_lexical_diversity": round(mean(lexical_diversities), 3),
            "latest_response_lexical_diversity": lexical_diversities[-1],
            "response_lexical_diversity_slope": _series_slope(lexical_diversities),
            "avg_response_information_density": round(mean(information_densities), 3),
            "latest_response_information_density": information_densities[-1],
            "response_information_density_slope": _series_slope(information_densities),
            "repeated_opening_turn_count": repeated_opening_turn_count,
            "output_quality_issue_count": len(issues),
            "output_quality_issues": issues,
            "output_quality_status": status,
        }
