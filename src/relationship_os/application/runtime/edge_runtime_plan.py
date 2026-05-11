from __future__ import annotations

from typing import Any


def build_edge_runtime_plan(
    *,
    runtime_profile: str,
    user_message: str,
    recalled_memory: list[dict[str, Any]],
    conscience_assessment: dict[str, Any],
    attachments: list[Any],
    turn_interpretation: Any,
    routing_policy: dict[str, Any],
    edge_max_completion_tokens: int,
    edge_max_memory_items: int,
    edge_max_prompt_tokens: int,
    edge_target_latency_seconds: float,
    edge_hard_latency_seconds: float,
    edge_allow_cloud_escalation: bool,
) -> dict[str, Any]:
    factual_probe = turn_interpretation.factual_recall
    social_probe = turn_interpretation.social_disclosure
    stable_cross_user_hits = [
        item
        for item in recalled_memory
        if str(item.get("scope")) == "other_user"
        and str(item.get("attribution_guard", "hint_only")) != "hint_only"
    ]
    if factual_probe:
        routing_mode = "factual_recall"
    elif stable_cross_user_hits and social_probe:
        routing_mode = "social_disclosure"
    else:
        routing_mode = "relational_chat"

    max_completion_tokens = edge_max_completion_tokens
    memory_item_budget = edge_max_memory_items
    if routing_mode == "factual_recall":
        memory_item_budget = max(
            memory_item_budget,
            int(routing_policy.get("factual_memory_item_budget_min", 5) or 5),
        )
        max_completion_tokens = min(
            max_completion_tokens,
            int(routing_policy.get("factual_max_completion_tokens", 120) or 120),
        )
    elif routing_mode == "social_disclosure":
        memory_item_budget = min(
            max(
                int(routing_policy.get("social_memory_item_budget_min", 2) or 2),
                memory_item_budget,
            ),
            int(routing_policy.get("social_memory_item_budget_max", 4) or 4),
        )
        max_completion_tokens = min(
            max_completion_tokens,
            int(routing_policy.get("social_max_completion_tokens", 140) or 140),
        )
    else:
        max_completion_tokens = min(
            max_completion_tokens,
            int(routing_policy.get("relational_max_completion_tokens", 160) or 160),
        )

    escalation_reasons: list[str] = []
    if attachments:
        escalation_reasons.append("multimodal_input")
    pressure_factor = int(routing_policy.get("recall_budget_pressure_factor", 2) or 2)
    if len(recalled_memory) > memory_item_budget * pressure_factor:
        escalation_reasons.append("recall_budget_pressure")
    if (
        routing_mode == "social_disclosure"
        and str(conscience_assessment.get("mode", "withhold"))
        in {"direct_reveal", "dramatic_confrontation"}
        and len(stable_cross_user_hits)
        > int(routing_policy.get("complex_cross_user_hit_count", 2) or 2)
    ):
        escalation_reasons.append("complex_cross_user_disclosure")
    if len(user_message) > int(routing_policy.get("large_user_message_threshold", 600) or 600):
        escalation_reasons.append("large_user_message")

    return {
        "runtime_profile": runtime_profile,
        "edge_handled": True,
        "deliberation_mode": turn_interpretation.deliberation_mode,
        "deliberation_need": turn_interpretation.deliberation_need,
        "candidate_cloud_escalation": bool(escalation_reasons),
        "escalation_reason": ",".join(escalation_reasons),
        "allow_cloud_escalation": edge_allow_cloud_escalation,
        "routing_mode": routing_mode,
        "prompt_style": "compact_cards",
        "memory_item_budget": memory_item_budget,
        "prompt_token_budget": edge_max_prompt_tokens,
        "target_latency_seconds": edge_target_latency_seconds,
        "hard_latency_seconds": edge_hard_latency_seconds,
        "max_completion_tokens": max_completion_tokens,
        "interpreted_intent": turn_interpretation.intent_label,
        "interpreted_intent_source": turn_interpretation.source,
        "interpreted_intent_confidence": turn_interpretation.confidence,
        "interpreted_deliberation_mode": turn_interpretation.deliberation_mode,
        "interpreted_deliberation_need": turn_interpretation.deliberation_need,
        "interpreted_factual_probe": factual_probe,
        "interpreted_social_probe": social_probe,
        "interpreted_self_referential_memory_query": (
            turn_interpretation.self_referential_memory
        ),
        "interpreted_presence_probe": turn_interpretation.presence_probe,
        "interpreted_edge_fact_deposition": turn_interpretation.edge_fact_deposition,
        "interpreted_edge_status_update": turn_interpretation.edge_status_update,
        "interpreted_persona_state_probe": turn_interpretation.persona_state_probe,
        "interpreted_state_reflection_probe": turn_interpretation.state_reflection_probe,
        "interpreted_relationship_reflection_probe": (
            turn_interpretation.relationship_reflection_probe
        ),
        "interpreted_appraisal": turn_interpretation.appraisal,
        "interpreted_emotional_load": turn_interpretation.emotional_load,
        "interpreted_user_state_guess": turn_interpretation.user_state_guess,
        "interpreted_situation_guess": turn_interpretation.situation_guess,
        "interpreted_relationship_shift_guess": turn_interpretation.relationship_shift_guess,
    }
