from relationship_os.application.runtime.friend_chat_probe_planning import (
    build_friend_chat_probe_answer_plan,
    build_friend_chat_probe_snapshot,
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


def test_build_friend_chat_probe_snapshot_limits_nested_values() -> None:
    snapshot = build_friend_chat_probe_snapshot(
        factual_slots={
            "hometown": "苏州",
            "pet_name": "年糕",
            "pet_kind": "猫",
            "drink_preference": "榛子拿铁",
            "communication_preference": "别发太长语音",
            "living_facts": ["a", "b", "c", "d"],
            "stable_slots": ["1", "2", "3", "4", "5", "6", "7"],
        },
        narrative_digest={
            "signals": ["tired", "slow", "withdrawn", "cluttered", "extra", "x", "y"],
            "markers": ["m1", "m2", "m3", "m4", "m5", "m6", "m7"],
            "dominant_tone": "low_energy",
        },
        relationship_digest={
            "signals": ["closer"],
            "markers": ["还在"],
            "interaction_band": "warm",
        },
        social_cues={"subject_token": "阿宁", "entity_token": "海盐", "fact_hint": "一点"},
        metadata={"friend_chat_total_interactions": 9},
    )

    assert snapshot["factual_slots"]["living_facts"] == ["a", "b", "c"]
    assert snapshot["factual_slots"]["stable_slots"] == ["1", "2", "3", "4", "5", "6"]
    assert snapshot["state_snapshot"]["signals"] == [
        "tired",
        "slow",
        "withdrawn",
        "cluttered",
        "extra",
        "x",
    ]
    assert snapshot["relationship_snapshot"]["total_interactions"] == 9
    assert snapshot["social_snapshot"]["subject_token"] == "阿宁"


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
