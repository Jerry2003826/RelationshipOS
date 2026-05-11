from relationship_os.application.runtime.friend_chat_probe_cues import (
    build_social_hint_cues,
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
