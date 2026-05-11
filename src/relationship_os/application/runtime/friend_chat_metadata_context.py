from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.friend_chat_digest_helpers import (
    normalize_friend_chat_narrative_digest,
    normalize_friend_chat_relationship_digest,
)
from relationship_os.application.runtime.friend_chat_fact_extractors import (
    normalize_fact_slot_digest,
)


def build_friend_chat_recent_context(
    *,
    self_state: dict[str, Any],
    transcript_messages: list[dict[str, Any]],
) -> dict[str, Any]:
    recent_sessions = list(self_state.get("recent_sessions_summary") or [])
    recent_state_markers: list[str] = []
    recent_relationship_markers: list[str] = []
    archived_user_messages: list[str] = []
    for entry in recent_sessions[-3:]:
        if not isinstance(entry, dict):
            continue
        recent_state_markers.extend(
            str(value).strip()
            for value in list(entry.get("user_state_markers") or [])
            if str(value).strip()
        )
        recent_relationship_markers.extend(
            str(value).strip()
            for value in list(entry.get("relationship_markers") or [])
            if str(value).strip()
        )
        archived_user_messages.extend(
            str(value).strip()
            for value in list(entry.get("recent_user_messages") or [])
            if str(value).strip()
        )
    transcript_user_messages = [
        str(message.get("content", "")).strip()
        for message in transcript_messages[-8:]
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]
    recent_user_messages = list(
        dict.fromkeys([*archived_user_messages, *transcript_user_messages])
    )
    recent_assistant_messages = [
        str(message.get("content", "")).strip()
        for message in transcript_messages[-8:]
        if message.get("role") == "assistant" and str(message.get("content", "")).strip()
    ]
    return {
        "fact_slot_digest": normalize_fact_slot_digest(self_state.get("fact_slot_digest")),
        "narrative_digest": normalize_friend_chat_narrative_digest(
            self_state.get("narrative_digest")
        ),
        "relationship_digest": normalize_friend_chat_relationship_digest(
            self_state.get("relationship_digest")
        ),
        "recent_state_markers": recent_state_markers,
        "recent_relationship_markers": recent_relationship_markers,
        "recent_user_messages": recent_user_messages,
        "recent_assistant_messages": recent_assistant_messages,
        "total_interactions": int(self_state.get("total_interactions", 0) or 0),
    }
