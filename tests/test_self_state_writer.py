import asyncio
from types import SimpleNamespace

from relationship_os.application.runtime.self_state_writer import SelfStateWriter
from relationship_os.domain.event_types import SELF_STATE_UPDATED


def test_self_state_writer_appends_relationship_snapshot_to_user_stream() -> None:
    calls = []

    class _StreamService:
        async def append_events(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(kwargs)

    user_message = "今天累，不想回消息，但你还在就放松一点"
    analysis = SimpleNamespace(
        context_frame=SimpleNamespace(topic="deadline", appraisal="tense"),
        relationship_state=SimpleNamespace(emotional_tone="warm"),
        strategy_decision=SimpleNamespace(next_action="stay_close"),
    )

    asyncio.run(
        SelfStateWriter(stream_service=_StreamService()).write(
            session_id="session-1",
            user_id="user-1",
            user_message=user_message,
            analysis=analysis,
            reply_artifacts=SimpleNamespace(assistant_response="ok"),
        )
    )

    assert len(calls) == 1
    call = calls[0]
    assert call["stream_id"] == "user:user-1"
    assert call["expected_version"] is None
    assert len(call["events"]) == 1

    event = call["events"][0]
    assert event.event_type == SELF_STATE_UPDATED
    assert event.payload["user_id"] == "user-1"
    assert event.payload["session_id"] == "session-1"
    assert event.payload["occurred_at"]
    assert event.payload["relationship_snapshot"] == {
        "last_topic": "deadline",
        "emotional_tone": "warm",
        "open_threads": ["deadline"],
        "my_stance": "stay_close",
        "user_state_markers": ["不想回消息", "累"],
        "relationship_markers": ["还在", "放松一点"],
        "user_message_excerpt": user_message,
    }
