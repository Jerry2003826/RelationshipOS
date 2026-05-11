from typing import Any

from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import (
    CONTEXT_FRAME_COMPUTED,
    RELATIONSHIP_STATE_UPDATED,
    SESSION_STARTED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import NewEvent, utc_now


def build_lightweight_turn_events(
    *,
    session_id: str,
    user_message: str,
    metadata_payload: dict[str, Any],
    turn_context: Any,
    turn_input: TurnInput | None = None,
) -> list[NewEvent]:
    """Build shared FAST_PONG/LIGHT_RECALL events without deep analysis output."""
    events: list[NewEvent] = []
    if not turn_context.prior_events:
        events.append(
            NewEvent(
                event_type=SESSION_STARTED,
                payload={
                    "session_id": session_id,
                    "created_at": utc_now().isoformat(),
                    "metadata": metadata_payload,
                },
            )
        )

    user_payload: dict[str, Any] = {"content": user_message}
    if turn_input and turn_input.has_media:
        user_payload["attachments"] = [
            {
                "type": attachment.type,
                "url": attachment.url,
                "mime_type": attachment.mime_type,
                "filename": attachment.filename,
            }
            for attachment in turn_input.attachments
        ]
    events.append(
        NewEvent(
            event_type=USER_MESSAGE_RECEIVED,
            payload=user_payload,
            metadata=metadata_payload,
        )
    )

    if not turn_context.runtime_state:
        return events

    prev_relationship = turn_context.runtime_state.get("relationship_state", {})
    if prev_relationship:
        events.append(
            NewEvent(
                event_type=RELATIONSHIP_STATE_UPDATED,
                payload=prev_relationship,
            )
        )
    prev_context = turn_context.runtime_state.get("context_frame", {})
    if prev_context:
        events.append(
            NewEvent(
                event_type=CONTEXT_FRAME_COMPUTED,
                payload=prev_context,
            )
        )
    return events
