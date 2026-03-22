"""SessionTranscriptProjector — append-only message log."""

from typing import Any

from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class SessionTranscriptProjector(Projector[dict[str, Any]]):
    name = "session-transcript"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {"messages": []}

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {"messages": list(state["messages"])}

        if event.event_type not in {USER_MESSAGE_RECEIVED, ASSISTANT_MESSAGE_SENT}:
            return next_state

        role = "user" if event.event_type == USER_MESSAGE_RECEIVED else "assistant"
        next_state["messages"].append(
            {
                "event_id": str(event.event_id),
                "role": role,
                "content": event.payload.get("content", ""),
                "delivery_mode": event.payload.get("delivery_mode"),
                "version": event.version,
                "occurred_at": event.occurred_at.isoformat(),
            }
        )
        return next_state
