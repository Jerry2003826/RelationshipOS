import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from relationship_os.application.runtime.turn_context import TurnContextLoader


def test_turn_context_loader_projects_runtime_and_transcript_state() -> None:
    now = datetime.now(UTC)
    events = [
        SimpleNamespace(occurred_at=now - timedelta(minutes=5)),
        SimpleNamespace(occurred_at=now - timedelta(minutes=2)),
    ]
    runtime_state = {
        "strategy_history": ["reflect", "", 42],
        "turn_count": 4,
        "session": {
            "user_id": "user-1",
            "metadata": {"benchmark_role": "probe"},
        },
    }
    transcript_messages = [{"role": "user", "content": "hello"}]

    class _StreamService:
        async def read_stream(self, *, stream_id: str):  # type: ignore[no-untyped-def]
            assert stream_id == "session-1"
            return events

        def project_events(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["stream_id"] == "session-1"
            assert kwargs["events"] == events
            assert kwargs["projector_name"] == "session-runtime"
            assert kwargs["projector_version"] == "v2"
            return {"state": runtime_state}

        async def project_stream(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["stream_id"] == "session-1"
            assert kwargs["projector_name"] == "session-transcript"
            assert kwargs["projector_version"] == "v1"
            return {"state": {"messages": transcript_messages}}

    context = asyncio.run(
        TurnContextLoader(
            stream_service=_StreamService(),
            runtime_projector_version="v2",
        ).load(session_id="session-1")
    )

    assert context.prior_events == events
    assert context.expected_version == 2
    assert context.runtime_state == runtime_state
    assert context.strategy_history == ["reflect", "42"]
    assert context.turn_index == 5
    assert context.transcript_messages == transcript_messages
    assert context.idle_gap_seconds >= 0
    assert context.session_age_seconds >= context.idle_gap_seconds
    assert context.user_id == "user-1"
    assert context.session_metadata == {"benchmark_role": "probe"}
    assert context.session_metadata is not runtime_state["session"]["metadata"]

