import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from relationship_os.application.runtime.dispatch_outcome_recorder import (
    DispatchOutcomeRecorder,
)
from relationship_os.domain.event_types import (
    PROACTIVE_DISPATCH_OUTCOME_RECORDED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    USER_MESSAGE_RECEIVED,
)


def test_dispatch_outcome_recorder_records_user_reply_after_dispatch() -> None:
    now = datetime.now(UTC)
    calls = []

    class _Handler:
        async def record_dispatch_outcome(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(kwargs)

    prior_events = [
        SimpleNamespace(
            event_type=PROACTIVE_FOLLOWUP_DISPATCHED,
            occurred_at=now,
        ),
        SimpleNamespace(
            event_type=USER_MESSAGE_RECEIVED,
            occurred_at=now + timedelta(seconds=42),
        ),
    ]

    asyncio.run(
        DispatchOutcomeRecorder(proactive_dispatch_handler=_Handler()).maybe_record(
            session_id="session-1",
            prior_events=prior_events,
        )
    )

    assert calls == [
        {
            "session_id": "session-1",
            "outcome_type": "responded",
            "response_latency_seconds": 42.0,
        }
    ]


def test_dispatch_outcome_recorder_skips_already_recorded_dispatch() -> None:
    now = datetime.now(UTC)
    calls = []

    class _Handler:
        async def record_dispatch_outcome(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(kwargs)

    prior_events = [
        SimpleNamespace(
            event_type=PROACTIVE_FOLLOWUP_DISPATCHED,
            occurred_at=now,
        ),
        SimpleNamespace(
            event_type=PROACTIVE_DISPATCH_OUTCOME_RECORDED,
            occurred_at=now + timedelta(seconds=5),
        ),
        SimpleNamespace(
            event_type=USER_MESSAGE_RECEIVED,
            occurred_at=now + timedelta(seconds=42),
        ),
    ]

    asyncio.run(
        DispatchOutcomeRecorder(proactive_dispatch_handler=_Handler()).maybe_record(
            session_id="session-1",
            prior_events=prior_events,
        )
    )

    assert calls == []
