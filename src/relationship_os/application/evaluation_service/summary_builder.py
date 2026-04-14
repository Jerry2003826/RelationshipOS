"""Session summary builder."""

from __future__ import annotations

from typing import Any

from relationship_os.application.evaluation_service.summary_reducers import (
    SessionSummaryAccumulator,
)
from relationship_os.application.evaluation_service.turn_record import (
    TurnRecord,
    _parse_datetime,
)


def compute_session_duration_seconds(
    *,
    started_at: str | None,
    last_event_at: str | None,
) -> float:
    started = _parse_datetime(started_at)
    ended = _parse_datetime(last_event_at)
    if started is None or ended is None:
        return 0.0
    return round(max(0.0, (ended - started).total_seconds()), 3)


def build_summary(
    *,
    session_id: str,
    turn_records: list[TurnRecord],
    event_count: int,
    started_at: str | None,
    last_event_at: str | None,
    started_metadata: dict[str, Any],
) -> dict[str, Any]:
    accumulator = SessionSummaryAccumulator()
    for turn in turn_records:
        accumulator.consume(turn)

    session_duration_seconds = compute_session_duration_seconds(
        started_at=started_at,
        last_event_at=last_event_at,
    )
    return accumulator.to_summary(
        session_id=session_id,
        event_count=event_count,
        started_at=started_at,
        last_event_at=last_event_at,
        started_metadata=started_metadata,
        session_duration_seconds=session_duration_seconds,
    )
