from relationship_os.application.runtime.friend_chat_memory_selection import (
    build_fallback_memory_items,
    build_friend_chat_memory_items,
    build_friend_chat_memory_values,
    build_speakable_memory_items,
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


def test_build_speakable_memory_items_limits_cross_user_by_conscience() -> None:
    items = build_speakable_memory_items(
        user_message="阿宁那边你知道一点吧",
        recalled_memory=[
            {
                "scope": "other_user",
                "value": "阿宁提过海盐",
                "source_user_id": "anning",
                "attribution_guard": "attribution_required",
                "attribution_confidence": 0.8,
            },
            {
                "scope": "other_user",
                "value": "小北提过风铃",
                "source_user_id": "xiaobei",
                "attribution_guard": "attribution_required",
                "attribution_confidence": 0.9,
            },
            {"scope": "self_user", "value": "我喜欢榛子拿铁"},
        ],
        routing_mode="social_disclosure",
        edge_runtime_plan={},
        conscience_assessment={
            "mode": "partial_reveal",
            "source_user_ids": ["anning"],
            "allowed_fact_count": 1,
        },
        self_referential_memory_query=False,
    )

    assert len(items) == 1
    assert items[0]["value"] == "阿宁提过海盐"
    assert items[0]["subject_display_name"] == "阿宁"


def test_build_speakable_memory_items_prefers_self_memory_for_self_factual_query() -> None:
    items = build_speakable_memory_items(
        user_message="我喜欢喝什么？",
        recalled_memory=[
            {"scope": "global_entity", "value": "榛子拿铁是饮品"},
            {"scope": "self_user", "value": "我喜欢榛子拿铁"},
        ],
        routing_mode="factual_recall",
        edge_runtime_plan={},
        conscience_assessment={},
        self_referential_memory_query=True,
    )

    assert [item["value"] for item in items] == ["我喜欢榛子拿铁"]


def test_build_fallback_memory_items_prioritizes_pet_name_matches() -> None:
    items = build_fallback_memory_items(
        user_message="我的猫叫什么名字？",
        candidates=[
            {
                "scope": "self_user",
                "value": "我在苏州长大",
                "final_rank_score": 0.9,
            },
            {
                "scope": "self_user",
                "value": "user: 我那只猫叫月饼",
                "final_rank_score": 0.5,
            },
        ],
        routing_mode="factual_recall",
    )

    assert items[0]["value"] == "我那只猫叫月饼"
    assert items[0]["scope"] == "self_user"
