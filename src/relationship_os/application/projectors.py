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

MAX_WORKING_HISTORY = 6
MAX_EPISODIC_HISTORY = 12
MAX_AGGREGATED_MEMORY_ITEMS = 12
MAX_GRAPH_NODES = 48
MAX_GRAPH_EDGES = 96


def _compact_strings(items: list[object], *, limit: int) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = str(item).strip()
        if not cleaned or cleaned in seen:
            continue
        values.append(cleaned)
        seen.add(cleaned)
        if len(values) >= limit:
            break
    return values


def _append_aggregated_items(
    *,
    existing: list[dict[str, Any]],
    values: list[object],
    source_version: int,
    occurred_at: str,
    context_tags: dict[str, str] | None = None,
    retention_lookup: dict[str, dict[str, object]] | None = None,
    limit: int = MAX_AGGREGATED_MEMORY_ITEMS,
) -> list[dict[str, Any]]:
    next_entries = [dict(item) for item in existing]
    index_by_value = {
        str(item.get("value", "")): index
        for index, item in enumerate(next_entries)
        if item.get("value")
    }
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        retention = dict((retention_lookup or {}).get(cleaned, {}))
        entry_index = index_by_value.get(cleaned)
        if entry_index is None:
            next_entries.append(
                {
                    "value": cleaned,
                    "mention_count": 1,
                    "last_seen_at": occurred_at,
                    "source_version": source_version,
                    "last_context_tags": dict(context_tags or {}),
                    "pinned": bool(retention.get("pinned", False)),
                    "retention_score": retention.get("retention_score"),
                    "retention_reason": retention.get("retention_reason"),
                }
            )
            index_by_value[cleaned] = len(next_entries) - 1
            continue
        updated = dict(next_entries[entry_index])
        updated["mention_count"] = int(updated.get("mention_count", 1)) + 1
        updated["last_seen_at"] = occurred_at
        updated["source_version"] = source_version
        updated["last_context_tags"] = dict(context_tags or {})
        updated["pinned"] = bool(updated.get("pinned", False)) or bool(
            retention.get("pinned", False)
        )
        if retention.get("retention_score") is not None:
            updated["retention_score"] = max(
                float(updated.get("retention_score", 0.0) or 0.0),
                float(retention["retention_score"]),
            )
        if retention.get("retention_reason"):
            updated["retention_reason"] = retention["retention_reason"]
        next_entries[entry_index] = updated

    next_entries.sort(
        key=lambda item: (
            bool(item.get("pinned", False)),
            int(item.get("mention_count", 0)),
            int(item.get("source_version", 0)),
            str(item.get("last_seen_at", "")),
        ),
        reverse=True,
    )
    return next_entries[:limit]


def _extract_context_tags(
    *,
    semantic_items: list[str],
    relational_items: list[str],
) -> dict[str, str]:
    context_tags: dict[str, str] = {}
    for value in semantic_items + relational_items:
        if ":" not in value:
            continue
        key, raw_value = value.split(":", 1)
        cleaned_key = key.strip()
        cleaned_value = raw_value.strip()
        if not cleaned_key or not cleaned_value:
            continue
        context_tags[cleaned_key] = cleaned_value
    return context_tags


def _build_retention_lookup(
    policy: dict[str, Any] | None,
    *,
    layer: str,
) -> dict[str, dict[str, Any]]:
    layers = dict((policy or {}).get("layers", {}))
    layer_payload = dict(layers.get(layer, {}))
    items = layer_payload.get("items", [])
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("value", "")): dict(item)
        for item in items
        if isinstance(item, dict) and item.get("value")
    }


def _summarize_sequence_retention(
    *,
    items: list[str],
    retention_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    decisions = [
        dict(retention_lookup.get(item, {}))
        for item in items
        if retention_lookup.get(item) is not None
    ]
    if not decisions:
        return {
            "pinned": False,
            "retention_score": 0.0,
            "retention_reason": "transient_context",
        }
    pinned_items = [item for item in decisions if item.get("pinned")]
    return {
        "pinned": bool(pinned_items),
        "retention_score": max(
            float(item.get("retention_score", 0.0) or 0.0) for item in decisions
        ),
        "retention_reason": str(
            (pinned_items[0] if pinned_items else decisions[0]).get(
                "retention_reason",
                "transient_context",
            )
        ),
    }


def _trim_retained_sequence(
    entries: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    next_entries = [dict(entry) for entry in entries]
    while len(next_entries) > limit:
        pop_index = next(
            (index for index, entry in enumerate(next_entries) if not entry.get("pinned")),
            0,
        )
        next_entries.pop(pop_index)
    return next_entries


def _graph_node_id(*, node_type: str, label: str) -> str:
    return f"{node_type}:{label}"


def _append_graph_nodes(
    *,
    existing: list[dict[str, Any]],
    values: list[object],
    node_type: str,
    source_version: int,
    occurred_at: str,
    limit: int = MAX_GRAPH_NODES,
) -> list[dict[str, Any]]:
    next_nodes = [dict(item) for item in existing]
    index_by_id = {
        str(item.get("id", "")): index
        for index, item in enumerate(next_nodes)
        if item.get("id")
    }
    for value in values:
        label = str(value).strip()
        if not label:
            continue
        node_id = _graph_node_id(node_type=node_type, label=label)
        node_index = index_by_id.get(node_id)
        if node_index is None:
            next_nodes.append(
                {
                    "id": node_id,
                    "label": label,
                    "node_type": node_type,
                    "mention_count": 1,
                    "last_seen_at": occurred_at,
                    "source_version": source_version,
                }
            )
            index_by_id[node_id] = len(next_nodes) - 1
            continue
        updated = dict(next_nodes[node_index])
        updated["mention_count"] = int(updated.get("mention_count", 1)) + 1
        updated["last_seen_at"] = occurred_at
        updated["source_version"] = source_version
        next_nodes[node_index] = updated

    next_nodes.sort(
        key=lambda item: (
            int(item.get("mention_count", 0)),
            int(item.get("source_version", 0)),
            str(item.get("last_seen_at", "")),
        ),
        reverse=True,
    )
    return next_nodes[:limit]


def _append_graph_edges(
    *,
    existing: list[dict[str, Any]],
    relations: list[tuple[str, str, str, str, str]],
    source_version: int,
    occurred_at: str,
    limit: int = MAX_GRAPH_EDGES,
) -> list[dict[str, Any]]:
    next_edges = [dict(item) for item in existing]
    index_by_key = {
        (
            str(item.get("source_id", "")),
            str(item.get("target_id", "")),
            str(item.get("relation", "")),
        ): index
        for index, item in enumerate(next_edges)
        if item.get("source_id") and item.get("target_id") and item.get("relation")
    }
    for source_type, source_label, target_type, target_label, relation in relations:
        cleaned_source_label = str(source_label).strip()
        cleaned_target_label = str(target_label).strip()
        if not cleaned_source_label or not cleaned_target_label:
            continue
        source_id = _graph_node_id(node_type=source_type, label=cleaned_source_label)
        target_id = _graph_node_id(node_type=target_type, label=cleaned_target_label)
        edge_key = (source_id, target_id, relation)
        edge_index = index_by_key.get(edge_key)
        if edge_index is None:
            next_edges.append(
                {
                    "source_id": source_id,
                    "source_label": cleaned_source_label,
                    "source_type": source_type,
                    "target_id": target_id,
                    "target_label": cleaned_target_label,
                    "target_type": target_type,
                    "relation": relation,
                    "weight": 1.0,
                    "last_seen_at": occurred_at,
                    "source_version": source_version,
                }
            )
            index_by_key[edge_key] = len(next_edges) - 1
            continue
        updated = dict(next_edges[edge_index])
        updated["weight"] = round(float(updated.get("weight", 1.0)) + 1.0, 3)
        updated["last_seen_at"] = occurred_at
        updated["source_version"] = source_version
        next_edges[edge_index] = updated

    next_edges.sort(
        key=lambda item: (
            float(item.get("weight", 0.0)),
            int(item.get("source_version", 0)),
            str(item.get("last_seen_at", "")),
        ),
        reverse=True,
    )
    return next_edges[:limit]


class SessionTranscriptProjector(Projector[dict[str, Any]]):
    name = "session-transcript"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {"messages": []}

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {"messages": list(state["messages"])}

        if event.event_type not in {"user.message.received", "assistant.message.sent"}:
            return next_state

        role = "user" if event.event_type == "user.message.received" else "assistant"
        next_state["messages"].append(
            {
                "event_id": str(event.event_id),
                "role": role,
                "content": event.payload.get("content", ""),
                "delivery_mode": event.payload.get("delivery_mode"),
                "version": event.version,
                "occurred_at": event.occurred_at.isoformat(),
            }
        )
        return next_state


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


class SessionMemoryProjector(Projector[dict[str, Any]]):
    name = "session-memory"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "session_id": None,
            "memory_turn_count": 0,
            "last_updated_at": None,
            "last_bundle_version": None,
            "latest_bundle": None,
            "last_write_guard": None,
            "last_retention_policy": None,
            "last_forgetting": None,
            "write_guard_blocked_total": 0,
            "retention_turn_count": 0,
            "pinned_item_count": 0,
            "forgetting_turn_count": 0,
            "total_evicted_count": 0,
            "working_memory": {
                "current": [],
                "history": [],
                "history_count": 0,
            },
            "episodic_memory": {
                "episodes": [],
                "episode_count": 0,
            },
            "semantic_memory": {
                "concepts": [],
                "concept_count": 0,
            },
            "relational_memory": {
                "signals": [],
                "signal_count": 0,
            },
            "reflective_memory": {
                "insights": [],
                "insight_count": 0,
            },
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            **state,
            "working_memory": {
                "current": list(state["working_memory"]["current"]),
                "history": [dict(item) for item in state["working_memory"]["history"]],
                "history_count": state["working_memory"]["history_count"],
            },
            "episodic_memory": {
                "episodes": [dict(item) for item in state["episodic_memory"]["episodes"]],
                "episode_count": state["episodic_memory"]["episode_count"],
            },
            "semantic_memory": {
                "concepts": [dict(item) for item in state["semantic_memory"]["concepts"]],
                "concept_count": state["semantic_memory"]["concept_count"],
            },
            "last_write_guard": state["last_write_guard"],
            "last_retention_policy": state["last_retention_policy"],
            "last_forgetting": state["last_forgetting"],
            "write_guard_blocked_total": state["write_guard_blocked_total"],
            "retention_turn_count": state["retention_turn_count"],
            "pinned_item_count": state["pinned_item_count"],
            "forgetting_turn_count": state["forgetting_turn_count"],
            "total_evicted_count": state["total_evicted_count"],
            "relational_memory": {
                "signals": [dict(item) for item in state["relational_memory"]["signals"]],
                "signal_count": state["relational_memory"]["signal_count"],
            },
            "reflective_memory": {
                "insights": [dict(item) for item in state["reflective_memory"]["insights"]],
                "insight_count": state["reflective_memory"]["insight_count"],
            },
        }

        if event.event_type == SESSION_STARTED:
            next_state["session_id"] = event.payload.get("session_id", event.stream_id)
            return next_state

        if event.event_type == MEMORY_WRITE_GUARD_EVALUATED:
            next_state["last_write_guard"] = dict(event.payload)
            next_state["write_guard_blocked_total"] += int(
                event.payload.get("blocked_count", 0)
            )
            return next_state

        if event.event_type == MEMORY_RETENTION_POLICY_APPLIED:
            next_state["last_retention_policy"] = dict(event.payload)
            next_state["retention_turn_count"] += 1
            next_state["pinned_item_count"] += int(event.payload.get("pinned_count", 0))
            return next_state

        if event.event_type == MEMORY_FORGETTING_APPLIED:
            evicted_count = int(event.payload.get("evicted_count", 0))
            next_state["last_forgetting"] = dict(event.payload)
            next_state["total_evicted_count"] += evicted_count
            if evicted_count > 0:
                next_state["forgetting_turn_count"] += 1
            return next_state

        if event.event_type != MEMORY_BUNDLE_UPDATED:
            return next_state

        occurred_at = event.occurred_at.isoformat()
        working_items = _compact_strings(
            list(event.payload.get("working_memory", [])),
            limit=4,
        )
        episodic_items = _compact_strings(
            list(event.payload.get("episodic_memory", [])),
            limit=6,
        )
        semantic_items = _compact_strings(
            list(event.payload.get("semantic_memory", [])),
            limit=6,
        )
        relational_items = _compact_strings(
            list(event.payload.get("relational_memory", [])),
            limit=6,
        )
        reflective_items = _compact_strings(
            list(event.payload.get("reflective_memory", [])),
            limit=6,
        )
        context_tags = _extract_context_tags(
            semantic_items=semantic_items,
            relational_items=relational_items,
        )
        retention_policy = dict(next_state.get("last_retention_policy") or {})
        working_retention = _build_retention_lookup(
            retention_policy,
            layer="working_memory",
        )
        episodic_retention = _build_retention_lookup(
            retention_policy,
            layer="episodic_memory",
        )
        semantic_retention = _build_retention_lookup(
            retention_policy,
            layer="semantic_memory",
        )
        relational_retention = _build_retention_lookup(
            retention_policy,
            layer="relational_memory",
        )
        reflective_retention = _build_retention_lookup(
            retention_policy,
            layer="reflective_memory",
        )
        working_retention_summary = _summarize_sequence_retention(
            items=working_items,
            retention_lookup=working_retention,
        )
        episodic_retention_summary = _summarize_sequence_retention(
            items=episodic_items,
            retention_lookup=episodic_retention,
        )

        next_state["session_id"] = next_state["session_id"] or event.stream_id
        next_state["memory_turn_count"] += 1
        next_state["last_updated_at"] = occurred_at
        next_state["last_bundle_version"] = event.version
        next_state["latest_bundle"] = dict(event.payload)

        working_history = list(next_state["working_memory"]["history"])
        working_history.append(
            {
                "source_version": event.version,
                "occurred_at": occurred_at,
                "items": working_items,
                "context_tags": context_tags,
                **working_retention_summary,
            }
        )
        next_state["working_memory"] = {
            "current": working_items,
            "history": _trim_retained_sequence(
                working_history,
                limit=MAX_WORKING_HISTORY,
            ),
            "history_count": len(working_history),
        }

        episodes = list(next_state["episodic_memory"]["episodes"])
        episodes.append(
            {
                "source_version": event.version,
                "occurred_at": occurred_at,
                "items": episodic_items,
                "context_tags": context_tags,
                **episodic_retention_summary,
            }
        )
        next_state["episodic_memory"] = {
            "episodes": _trim_retained_sequence(
                episodes,
                limit=MAX_EPISODIC_HISTORY,
            ),
            "episode_count": len(episodes),
        }

        next_state["semantic_memory"] = {
            "concepts": _append_aggregated_items(
                existing=next_state["semantic_memory"]["concepts"],
                values=semantic_items,
                source_version=event.version,
                occurred_at=occurred_at,
                context_tags=context_tags,
                retention_lookup=semantic_retention,
            ),
            "concept_count": len(next_state["semantic_memory"]["concepts"]) or len(
                semantic_items
            ),
        }
        next_state["semantic_memory"]["concept_count"] = len(
            next_state["semantic_memory"]["concepts"]
        )

        next_state["relational_memory"] = {
            "signals": _append_aggregated_items(
                existing=next_state["relational_memory"]["signals"],
                values=relational_items,
                source_version=event.version,
                occurred_at=occurred_at,
                context_tags=context_tags,
                retention_lookup=relational_retention,
            ),
            "signal_count": len(next_state["relational_memory"]["signals"]) or len(
                relational_items
            ),
        }
        next_state["relational_memory"]["signal_count"] = len(
            next_state["relational_memory"]["signals"]
        )

        next_state["reflective_memory"] = {
            "insights": _append_aggregated_items(
                existing=next_state["reflective_memory"]["insights"],
                values=reflective_items,
                source_version=event.version,
                occurred_at=occurred_at,
                context_tags=context_tags,
                retention_lookup=reflective_retention,
            ),
            "insight_count": len(next_state["reflective_memory"]["insights"]) or len(
                reflective_items
            ),
        }
        next_state["reflective_memory"]["insight_count"] = len(
            next_state["reflective_memory"]["insights"]
        )

        return next_state


class SessionTemporalKGProjector(Projector[dict[str, Any]]):
    name = "session-temporal-kg"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "session_id": None,
            "last_updated_at": None,
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            **state,
            "nodes": [dict(item) for item in state["nodes"]],
            "edges": [dict(item) for item in state["edges"]],
        }

        if event.event_type == SESSION_STARTED:
            next_state["session_id"] = event.payload.get("session_id", event.stream_id)
            return next_state

        if event.event_type != MEMORY_BUNDLE_UPDATED:
            return next_state

        occurred_at = event.occurred_at.isoformat()
        next_state["session_id"] = next_state["session_id"] or event.stream_id
        next_state["last_updated_at"] = occurred_at

        working_items = _compact_strings(list(event.payload.get("working_memory", [])), limit=4)
        episodic_items = _compact_strings(list(event.payload.get("episodic_memory", [])), limit=4)
        semantic_items = _compact_strings(list(event.payload.get("semantic_memory", [])), limit=6)
        relational_items = _compact_strings(
            list(event.payload.get("relational_memory", [])),
            limit=6,
        )
        reflective_items = _compact_strings(
            list(event.payload.get("reflective_memory", [])),
            limit=6,
        )

        nodes = list(next_state["nodes"])
        nodes = _append_graph_nodes(
            existing=nodes,
            values=working_items,
            node_type="working_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=episodic_items,
            node_type="episodic_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=semantic_items,
            node_type="semantic_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=relational_items,
            node_type="relational_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=reflective_items,
            node_type="reflective_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        next_state["nodes"] = nodes

        relations: list[tuple[str, str, str, str, str]] = []
        for episodic_item in episodic_items:
            for semantic_item in semantic_items:
                relations.append(
                    (
                        "episodic_memory",
                        episodic_item,
                        "semantic_memory",
                        semantic_item,
                        "mentions",
                    )
                )
            for relational_item in relational_items:
                relations.append(
                    (
                        "episodic_memory",
                        episodic_item,
                        "relational_memory",
                        relational_item,
                        "observes",
                    )
                )
        for working_item in working_items:
            for semantic_item in semantic_items:
                relations.append(
                    (
                        "working_memory",
                        working_item,
                        "semantic_memory",
                        semantic_item,
                        "focuses_on",
                    )
                )
            for relational_item in relational_items:
                relations.append(
                    (
                        "working_memory",
                        working_item,
                        "relational_memory",
                        relational_item,
                        "grounds",
                    )
                )
        for semantic_item in semantic_items:
            for relational_item in relational_items:
                relations.append(
                    (
                        "semantic_memory",
                        semantic_item,
                        "relational_memory",
                        relational_item,
                        "signals",
                    )
                )
            for reflective_item in reflective_items:
                relations.append(
                    (
                        "semantic_memory",
                        semantic_item,
                        "reflective_memory",
                        reflective_item,
                        "supports",
                    )
                )
        for relational_item in relational_items:
            for reflective_item in reflective_items:
                relations.append(
                    (
                        "relational_memory",
                        relational_item,
                        "reflective_memory",
                        reflective_item,
                        "informs",
                    )
                )

        next_state["edges"] = _append_graph_edges(
            existing=next_state["edges"],
            relations=relations,
            source_version=event.version,
            occurred_at=occurred_at,
        )
        next_state["node_count"] = len(next_state["nodes"])
        next_state["edge_count"] = len(next_state["edges"])
        return next_state


class InnerMonologueBufferProjector(Projector[dict[str, Any]]):
    name = "inner-monologue-buffer"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entries": [],
            "entry_count": 0,
            "last_stage": None,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            "entries": list(state["entries"]),
            "entry_count": state["entry_count"],
            "last_stage": state["last_stage"],
        }
        if event.event_type != INNER_MONOLOGUE_RECORDED:
            return next_state

        entries = list(event.payload.get("entries", []))
        next_state["entries"].extend(entries)
        next_state["entry_count"] += len(entries)
        if entries:
            next_state["last_stage"] = entries[-1].get("stage")
        return next_state


class SessionSnapshotProjector(Projector[dict[str, Any]]):
    name = "session-snapshots"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "snapshots": [],
            "snapshot_count": 0,
            "latest_snapshot_id": None,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            "snapshots": list(state["snapshots"]),
            "snapshot_count": state["snapshot_count"],
            "latest_snapshot_id": state["latest_snapshot_id"],
        }
        if event.event_type != SESSION_SNAPSHOT_CREATED:
            return next_state

        snapshot = dict(event.payload)
        next_state["snapshots"].append(snapshot)
        next_state["snapshot_count"] += 1
        next_state["latest_snapshot_id"] = snapshot.get("snapshot_id")
        return next_state
