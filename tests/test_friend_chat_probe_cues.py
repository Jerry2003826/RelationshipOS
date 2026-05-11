from relationship_os.application.runtime.friend_chat_probe_cues import (
    build_friend_chat_memory_recap_cues,
    build_persona_state_probe_cues,
    build_relationship_reflection_cues,
    build_social_hint_cues,
    build_state_reflection_cues,
)


def test_build_social_hint_cues_filters_to_allowed_speakable_source() -> None:
    cues = build_social_hint_cues(
        metadata={
            "entity_source_user_ids": ["u2"],
            "social_disclosure_mode": "hint",
        },
        items=[
            {
                "value": "\u5c0f\u5317\u63d0\u5230\u82b1\u751f",
                "subject_user_id": "u3",
                "source_user_id": "u3",
                "subject_hint": "other_user:xiaobei",
                "attribution_guard": "direct_ok",
                "attribution_confidence": 0.99,
                "final_rank_score": 0.99,
            },
            {
                "value": "\u963f\u5b81\u63d0\u5230\u56e2\u5b50",
                "subject_user_id": "u2",
                "source_user_id": "u2",
                "subject_hint": "other_user:anning",
                "attribution_guard": "attribution_required",
                "attribution_confidence": 0.7,
                "final_rank_score": 0.4,
            },
        ],
    )

    assert cues is not None
    assert cues["probe_kind"] == "social_hint"
    assert cues["subject_token"] == "\u963f\u5b81"
    assert cues["entity_token"] == "\u56e2\u5b50"
    assert cues["required_disclosure_posture"] == "partial_withhold"
    assert cues["minimum_unit"] == [
        "subject_token",
        "entity_token",
        "disclosure_posture",
    ]


def test_build_persona_state_probe_cues_adds_friend_chat_traits() -> None:
    cues = build_persona_state_probe_cues(
        metadata={"entity_persona_mood_tone": "steady"},
        is_friend_chat_profile=True,
        probe_snapshot={},
        self_memory_values=[],
    )

    assert cues is not None
    assert cues["probe_kind"] == "persona_state"
    assert "low_energy" in cues["style_tags"]
    assert "conversational" in cues["required_persona_traits"]


def test_build_state_reflection_cues_infers_withdrawn_signal() -> None:
    cues = build_state_reflection_cues(
        metadata={
            "friend_chat_recent_state_markers": ["\u4e0d\u60f3\u56de\u6d88\u606f"],
        },
        probe_snapshot={},
        self_memory_values=[],
    )

    assert cues is not None
    assert cues["probe_kind"] == "state_reflection"
    assert "withdrawn" in cues["required_signal_ids"]


def test_build_relationship_reflection_cues_derives_closeness_from_history() -> None:
    cues = build_relationship_reflection_cues(
        metadata={"friend_chat_total_interactions": 3},
        probe_snapshot={
            "factual_slots": {
                "pet_name": "\u56e2\u5b50",
            }
        },
    )

    assert cues is not None
    assert cues["probe_kind"] == "relationship_reflection"
    assert "closer" in cues["relationship_signals"]
    assert "remembers_details" in cues["relationship_signals"]
    assert cues["supporting_fact_tokens"] == ["\u56e2\u5b50"]


def test_build_friend_chat_memory_recap_cues_uses_probe_snapshot_slots() -> None:
    cues = build_friend_chat_memory_recap_cues(
        metadata={},
        probe_snapshot={
            "factual_slots": {
                "pet_name": "\u56e2\u5b50",
                "drink_preference": "\u51b0\u7f8e\u5f0f",
            }
        },
        fact_slot_digest={},
    )

    assert cues is not None
    assert cues["probe_kind"] == "memory_recap"
    assert cues["fact_slots"]["pet_name"] == "\u56e2\u5b50"
    assert "\u51b0\u7f8e\u5f0f" in cues["required_fact_tokens"]
