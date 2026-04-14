"""UserIndexProjector — maps a user to their linked sessions."""

from typing import Any

from relationship_os.domain.event_types import (
    USER_CREATED,
    USER_PROFILE_UPDATED,
    USER_SESSION_LINKED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class UserIndexProjector(Projector[dict[str, Any]]):
    """Projects a user stream into a lightweight index of linked sessions.

    Stream ID convention: ``user:{user_id}``
    """

    name = "user-index"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "user_id": None,
            "display_name": None,
            "session_ids": [],
            "created_at": None,
            "metadata": {},
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        et = event.event_type
        p = event.payload

        if et == USER_CREATED:
            return {
                **state,
                "user_id": p.get("user_id"),
                "display_name": p.get("display_name"),
                "created_at": p.get("created_at"),
                "metadata": p.get("metadata", {}),
            }

        if et == USER_SESSION_LINKED:
            session_id = p.get("session_id")
            existing = state.get("session_ids") or []
            if session_id and session_id not in existing:
                return {**state, "session_ids": [*existing, session_id]}
            return state

        if et == USER_PROFILE_UPDATED:
            updates: dict[str, Any] = {}
            if "display_name" in p:
                updates["display_name"] = p["display_name"]
            if "metadata" in p:
                updates["metadata"] = {**(state.get("metadata") or {}), **p["metadata"]}
            return {**state, **updates}

        return state
