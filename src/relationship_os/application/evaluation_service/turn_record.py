"""Data classes and utility functions for the evaluation service."""

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Any

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
