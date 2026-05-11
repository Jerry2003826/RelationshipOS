from relationship_os.application.runtime.friend_chat_fact_slots import (
    build_enriched_friend_chat_fact_slot_digest,
    infer_friend_chat_communication_preference,
)


def test_infer_friend_chat_communication_preference_from_memory_values() -> None:
    preference = infer_friend_chat_communication_preference(
        metadata={},
        self_memory_values=["\u522b\u53d1\u592a\u957f\u8bed\u97f3"],
    )

    assert preference == "\u522b\u53d1\u592a\u957f\u8bed\u97f3"


def test_build_enriched_friend_chat_fact_slot_digest_fills_missing_slots() -> None:
    digest = build_enriched_friend_chat_fact_slot_digest(
        metadata={
            "friend_chat_recent_user_messages": [
                "\u6211\u5728\u6210\u90fd\u957f\u5927",
                "\u6211\u5bb6\u732b\u53eb\u56e2\u5b50",
                "\u5e73\u65f6\u4f1a\u559d\u51b0\u7f8e\u5f0f",
            ],
        },
        self_memory_values=[],
    )

    assert digest["hometown"] == "\u6210\u90fd"
    assert digest["pet_name"] == "\u56e2\u5b50"
    assert digest["pet_kind"] == "\u732b"
    assert digest["drink_preference"] == "\u51b0\u7f8e\u5f0f"
