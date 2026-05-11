from relationship_os.application.runtime.friend_chat_probe_planning import (
    build_friend_chat_probe_answer_plan,
)


def test_build_friend_chat_probe_answer_plan_from_memory_snapshot() -> None:
    plan = build_friend_chat_probe_answer_plan(
        probe_cues=None,
        snapshot={
            "factual_slots": {
                "hometown": "苏州",
                "pet_name": "年糕",
                "drink_preference": "榛子拿铁",
                "communication_preference": "别发太长语音",
            },
            "state_snapshot": {},
            "relationship_snapshot": {},
            "social_snapshot": {},
        },
        metadata={"turn_interpretation_self_referential_memory_query": True},
        is_friend_chat_profile=True,
    )

    assert plan is not None
    assert plan["probe_kind"] == "memory_recap"
    assert plan["language"] == "zh"
    assert plan["minimum_required_fact_token_count"] == 4
    assert "苏州" in plan["required_fact_tokens"]
    assert "别发太长语音" in plan["required_fact_tokens"]
    assert plan["answer_perspective"] == "user"


def test_build_friend_chat_probe_answer_plan_from_relationship_snapshot() -> None:
    plan = build_friend_chat_probe_answer_plan(
        probe_cues=None,
        snapshot={
            "factual_slots": {"pet_name": "年糕"},
            "state_snapshot": {},
            "relationship_snapshot": {
                "signals": ["closer", "still_here", "remembers_details"],
                "markers": ["还在"],
                "interaction_band": "warm",
                "total_interactions": 4,
            },
            "social_snapshot": {},
        },
        metadata={"turn_interpretation_relationship_reflection_probe": True},
        is_friend_chat_profile=True,
    )

    assert plan is not None
    assert plan["probe_kind"] == "relationship_reflection"
    assert plan["minimum_required_signal_count"] == 3
    assert plan["must_anchor_detail"] is True
    assert plan["must_explicit_continuity"] is True
    assert "年糕" in plan["supporting_fact_tokens"]
    assert "closer" in plan["required_signal_semantics"]
