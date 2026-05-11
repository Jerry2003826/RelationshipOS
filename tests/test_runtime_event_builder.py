from types import SimpleNamespace

from relationship_os.application.runtime.event_builder import build_lightweight_turn_events
from relationship_os.domain.contracts.turn_input import Attachment, TurnInput
from relationship_os.domain.event_types import (
    CONTEXT_FRAME_COMPUTED,
    RELATIONSHIP_STATE_UPDATED,
    SESSION_STARTED,
    USER_MESSAGE_RECEIVED,
)


def test_build_lightweight_turn_events_preserves_start_user_and_previous_state() -> None:
    turn_context = SimpleNamespace(
        prior_events=[],
        runtime_state={
            "relationship_state": {"emotional_tone": "steady"},
            "context_frame": {"topic": "check-in"},
        },
    )
    turn_input = TurnInput(
        text="hi",
        attachments=[
            Attachment(
                type="image",
                url="https://example.test/cat.png",
                mime_type="image/png",
                filename="cat.png",
            )
        ],
    )

    events = build_lightweight_turn_events(
        session_id="session-1",
        user_message="hi",
        metadata_payload={"source": "test"},
        turn_context=turn_context,
        turn_input=turn_input,
    )

    assert [event.event_type for event in events] == [
        SESSION_STARTED,
        USER_MESSAGE_RECEIVED,
        RELATIONSHIP_STATE_UPDATED,
        CONTEXT_FRAME_COMPUTED,
    ]
    assert events[0].payload["session_id"] == "session-1"
    assert events[1].payload["attachments"] == [
        {
            "type": "image",
            "url": "https://example.test/cat.png",
            "mime_type": "image/png",
            "filename": "cat.png",
        }
    ]
    assert events[1].metadata == {"source": "test"}
    assert events[2].payload == {"emotional_tone": "steady"}
    assert events[3].payload == {"topic": "check-in"}

