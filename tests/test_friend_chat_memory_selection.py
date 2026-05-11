from relationship_os.application.runtime.friend_chat_memory_selection import (
    build_friend_chat_memory_items,
    build_friend_chat_memory_values,
)


def test_build_friend_chat_memory_values_filters_low_signal_and_dedupes() -> None:
    values = build_friend_chat_memory_values(
        recalled_memory=[
            {"scope": "self_user", "value": "topic:work", "final_rank_score": 9},
            {"scope": "self_user", "value": "user: 我喜欢榛子拿铁", "final_rank_score": 0.6},
            {"scope": "self_user", "value": "我喜欢榛子拿铁", "final_rank_score": 0.5},
            {"scope": "other_user", "value": "阿宁提过海盐", "final_rank_score": 1.0},
        ],
        scopes={"self_user"},
        max_items=3,
    )

    assert values == ["我喜欢榛子拿铁"]


def test_build_friend_chat_memory_items_normalizes_owner_and_limits() -> None:
    items = build_friend_chat_memory_items(
        recalled_memory=[
            {
                "scope": "other_user",
                "value": "阿宁提过海盐",
                "subject_hint": "other_user:anning",
                "attribution_confidence": 0.9,
                "final_rank_score": 0.8,
            },
            {"scope": "other_user", "value": "quality:low", "final_rank_score": 1.0},
        ],
        scopes={"other_user"},
        max_items=2,
    )

    assert len(items) == 1
    assert items[0]["subject_display_name"] == "阿宁"
    assert items[0]["value"] == "阿宁提过海盐"
