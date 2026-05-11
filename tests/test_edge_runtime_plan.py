from types import SimpleNamespace

from relationship_os.application.runtime.edge_runtime_plan import build_edge_runtime_plan


def test_build_edge_runtime_plan_routes_factual_recall_with_policy_caps() -> None:
    plan = build_edge_runtime_plan(
        runtime_profile="friend_chat_zh_v1",
        user_message="我家猫叫什么名字？",
        recalled_memory=[{"scope": "self_user"}] * 12,
        conscience_assessment={},
        attachments=[],
        turn_interpretation=SimpleNamespace(
            factual_recall=True,
            social_disclosure=False,
            self_referential_memory=True,
            presence_probe=False,
            edge_fact_deposition=False,
            edge_status_update=False,
            persona_state_probe=False,
            state_reflection_probe=False,
            relationship_reflection_probe=False,
            deliberation_mode="light_recall",
            deliberation_need=0.72,
            intent_label="factual_recall",
            source="rules",
            confidence=1.0,
            appraisal="neutral",
            emotional_load="low",
            user_state_guess="",
            situation_guess="",
            relationship_shift_guess="",
        ),
        routing_policy={
            "factual_memory_item_budget_min": 5,
            "factual_max_completion_tokens": 120,
            "recall_budget_pressure_factor": 2,
        },
        edge_max_completion_tokens=180,
        edge_max_memory_items=3,
        edge_max_prompt_tokens=1200,
        edge_target_latency_seconds=0.8,
        edge_hard_latency_seconds=1.5,
        edge_allow_cloud_escalation=False,
    )

    assert plan["routing_mode"] == "factual_recall"
    assert plan["memory_item_budget"] == 5
    assert plan["max_completion_tokens"] == 120
    assert plan["candidate_cloud_escalation"] is True
    assert plan["interpreted_self_referential_memory_query"] is True


def test_build_edge_runtime_plan_routes_social_disclosure_for_stable_cross_user_hits() -> None:
    plan = build_edge_runtime_plan(
        runtime_profile="friend_chat_zh_v1",
        user_message="阿宁那边你知道一点吧",
        recalled_memory=[
            {"scope": "other_user", "attribution_guard": "attribution_required"},
            {"scope": "other_user", "attribution_guard": "attribution_required"},
            {"scope": "other_user", "attribution_guard": "attribution_required"},
        ],
        conscience_assessment={"mode": "direct_reveal"},
        attachments=[],
        turn_interpretation=SimpleNamespace(
            factual_recall=False,
            social_disclosure=True,
            self_referential_memory=False,
            presence_probe=False,
            edge_fact_deposition=False,
            edge_status_update=False,
            persona_state_probe=False,
            state_reflection_probe=False,
            relationship_reflection_probe=False,
            deliberation_mode="light_recall",
            deliberation_need=0.78,
            intent_label="social_disclosure",
            source="rules",
            confidence=1.0,
            appraisal="neutral",
            emotional_load="low",
            user_state_guess="",
            situation_guess="",
            relationship_shift_guess="",
        ),
        routing_policy={"complex_cross_user_hit_count": 2},
        edge_max_completion_tokens=180,
        edge_max_memory_items=6,
        edge_max_prompt_tokens=1200,
        edge_target_latency_seconds=0.8,
        edge_hard_latency_seconds=1.5,
        edge_allow_cloud_escalation=False,
    )

    assert plan["routing_mode"] == "social_disclosure"
    assert "complex_cross_user_disclosure" in plan["escalation_reason"]
