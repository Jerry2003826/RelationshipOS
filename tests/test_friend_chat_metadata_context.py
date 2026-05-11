from relationship_os.application.runtime.friend_chat_metadata_context import (
    build_friend_chat_recent_context,
)


def test_build_friend_chat_recent_context_merges_archived_and_transcript_turns() -> None:
    context = build_friend_chat_recent_context(
        self_state={
            "fact_slot_digest": {"pet_name": "\u56e2\u5b50"},
            "narrative_digest": {"signals": ["tired"]},
            "relationship_digest": {"signals": ["closer"]},
            "recent_sessions_summary": [
                {
                    "user_state_markers": ["\u7d2f"],
                    "relationship_markers": ["\u8fd8\u5728"],
                    "recent_user_messages": ["\u65e7\u6d88\u606f"],
                }
            ],
            "total_interactions": 2,
        },
        transcript_messages=[
            {"role": "user", "content": "\u65e7\u6d88\u606f"},
            {"role": "assistant", "content": "\u6211\u5728"},
            {"role": "user", "content": "\u65b0\u6d88\u606f"},
        ],
    )

    assert context["fact_slot_digest"]["pet_name"] == "\u56e2\u5b50"
    assert context["narrative_digest"]["signals"] == ["tired"]
    assert context["relationship_digest"]["signals"] == ["closer"]
    assert context["recent_state_markers"] == ["\u7d2f"]
    assert context["recent_relationship_markers"] == ["\u8fd8\u5728"]
    assert context["recent_user_messages"] == ["\u65e7\u6d88\u606f", "\u65b0\u6d88\u606f"]
    assert context["recent_assistant_messages"] == ["\u6211\u5728"]
    assert context["total_interactions"] == 2
