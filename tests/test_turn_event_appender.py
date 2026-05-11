import asyncio
from types import SimpleNamespace

from relationship_os.application.runtime.turn_event_appender import TurnEventAppender
from relationship_os.domain.events import NewEvent


def test_turn_event_appender_appends_and_applies_against_loaded_runtime_state() -> None:
    event = NewEvent(event_type="USER_MESSAGE_RECEIVED", payload={"content": "hello"})
    stored_events = [SimpleNamespace(event_type="USER_MESSAGE_RECEIVED")]
    runtime_state = {"turn_count": 3}
    projection = {"state": {"turn_count": 4}}
    calls = []

    class _StreamService:
        async def append_events(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("append", kwargs))
            return stored_events

        def apply_events(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("apply", kwargs))
            return projection

    turn_context = SimpleNamespace(
        expected_version=7,
        runtime_state=runtime_state,
        prior_events=[],
    )

    result = asyncio.run(
        TurnEventAppender(
            stream_service=_StreamService(),
            runtime_projector_version="v2",
        ).append(
            session_id="session-1",
            turn_context=turn_context,
            events=[event],
        )
    )

    assert result == (stored_events, projection)
    assert calls[0] == (
        "append",
        {
            "stream_id": "session-1",
            "expected_version": 7,
            "events": [event],
        },
    )
    assert calls[1] == (
        "apply",
        {
            "stream_id": "session-1",
            "state": runtime_state,
            "events": stored_events,
            "projector_name": "session-runtime",
            "projector_version": "v2",
        },
    )
