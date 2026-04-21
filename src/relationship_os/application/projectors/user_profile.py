"""UserProfileProjector — cross-session user profile aggregation.

Unlike standard projectors that fold a single event stream, this is a
*second-order* service-level aggregator: it reads the user-index projection
to discover linked sessions, then aggregates their session-memory projections.

It is NOT registered as a standard event-fold projector.  Instead it is
called by UserService as a composed read operation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from relationship_os.application.stream_service import StreamService

_MAX_SEMANTIC_CONCEPTS = 100
_MAX_RELATIONAL_SIGNALS = 50
_MAX_REFLECTIVE_INSIGHTS = 30


def _merge_aggregated_items(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    max_items: int,
) -> list[dict[str, Any]]:
    """Merge incoming aggregated memory items into existing, deduplicating by value."""
    index: dict[str, dict[str, Any]] = {item["value"]: item for item in existing}
    for item in incoming:
        value = item.get("value")
        if not value:
            continue
        if value in index:
            existing_item = index[value]
            index[value] = {
                **existing_item,
                "mention_count": existing_item.get("mention_count", 1)
                + item.get("mention_count", 1),
                "last_seen_at": max(
                    existing_item.get("last_seen_at") or "",
                    item.get("last_seen_at") or "",
                )
                or existing_item.get("last_seen_at"),
            }
        else:
            index[value] = dict(item)

    merged = sorted(
        index.values(),
        key=lambda x: (-(x.get("mention_count") or 1), x.get("last_seen_at") or ""),
    )
    return merged[:max_items]


async def build_user_profile(
    *,
    user_id: str,
    stream_service: StreamService,
) -> dict[str, Any]:
    """Aggregate session-memory projections across all sessions linked to user_id.

    Returns a dict with:
    - identity_facts: high-frequency semantic concepts (name, city, job…)
    - preference_signals: relational signals aggregated across sessions
    - reflective_insights: reflective memory items from all sessions
    - relationship_history: per-session summary (session_id, turn count, last topic)
    - session_ids: list of linked session IDs
    """
    # Step 1: load user index to get linked session IDs
    user_stream_id = f"user:{user_id}"
    index_proj = await stream_service.project_stream(
        stream_id=user_stream_id,
        projector_name="user-index",
        projector_version="v1",
    )
    index_state: dict[str, Any] = index_proj.get("state", {})
    session_ids: list[str] = index_state.get("session_ids") or []

    identity_facts: list[dict[str, Any]] = []
    preference_signals: list[dict[str, Any]] = []
    reflective_insights: list[dict[str, Any]] = []
    relationship_history: list[dict[str, Any]] = []

    # Step 2: for each linked session, load its session-memory projection
    for session_id in session_ids:
        try:
            mem_proj = await stream_service.project_stream(
                stream_id=session_id,
                projector_name="session-memory",
                projector_version="v1",
            )
        except Exception:
            continue

        mem_state: dict[str, Any] = mem_proj.get("state", {})

        # Aggregate semantic concepts → identity facts
        concepts = mem_state.get("semantic_memory", {}).get("concepts") or []
        identity_facts = _merge_aggregated_items(identity_facts, concepts, _MAX_SEMANTIC_CONCEPTS)

        # Aggregate relational signals → preference signals
        signals = mem_state.get("relational_memory", {}).get("signals") or []
        preference_signals = _merge_aggregated_items(
            preference_signals, signals, _MAX_RELATIONAL_SIGNALS
        )

        # Aggregate reflective insights
        insights = mem_state.get("reflective_memory", {}).get("insights") or []
        reflective_insights = _merge_aggregated_items(
            reflective_insights, insights, _MAX_REFLECTIVE_INSIGHTS
        )

        # Build per-session relationship history entry
        turn_count = mem_state.get("memory_turn_count") or 0
        last_updated = mem_state.get("last_updated_at")
        # Try to pull last topic from working memory
        last_topic: str | None = None
        working_hist = mem_state.get("working_memory", {}).get("history") or []
        if working_hist:
            last_entry = working_hist[-1]
            items = last_entry.get("items") or []
            if items:
                last_topic = str(items[0]) if items else None

        relationship_history.append(
            {
                "session_id": session_id,
                "turn_count": turn_count,
                "last_updated_at": last_updated,
                "last_topic": last_topic,
            }
        )

    return {
        "user_id": user_id,
        "display_name": index_state.get("display_name"),
        "session_ids": session_ids,
        "identity_facts": identity_facts,
        "preference_signals": preference_signals,
        "reflective_insights": reflective_insights,
        "relationship_history": relationship_history,
    }
