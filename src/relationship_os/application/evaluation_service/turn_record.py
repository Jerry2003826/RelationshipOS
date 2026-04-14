"""Data classes and utility functions for the evaluation service."""

import math
import re
from dataclasses import dataclass, field, fields
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
    proactive_dispatch_outcome: dict[str, Any] | None = None
    proactive_followup_messages: list[str] = field(default_factory=list)
    proactive_followup_message_event_count: int = 0
    runtime_quality_doctor_report: dict[str, Any] | None = None
    system3_snapshot: dict[str, Any] | None = None
    private_judgment: dict[str, Any] | None = None
    session_directive: dict[str, Any] | None = None
    strategy_decision: dict[str, Any] | None = None
    llm_failure: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {item.name: getattr(self, item.name) for item in fields(self)}
        data["assistant_responses"] = list(self.assistant_responses)
        data["proactive_followup_messages"] = list(self.proactive_followup_messages)
        return data


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
