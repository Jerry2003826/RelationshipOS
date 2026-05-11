from dataclasses import dataclass
from typing import Any

from relationship_os.domain.events import StoredEvent, utc_now


@dataclass(slots=True)
class _TurnContext:
    prior_events: list[StoredEvent]
    expected_version: int
    runtime_state: dict[str, Any] | None
    strategy_history: list[str]
    turn_index: int
    transcript_messages: list[dict[str, Any]]
    idle_gap_seconds: float
    session_age_seconds: float
    user_id: str | None = None
    session_metadata: dict[str, Any] | None = None


class TurnContextLoader:
    """Loads projections and timing context needed to process one user turn."""

    def __init__(
        self,
        *,
        stream_service: Any,
        runtime_projector_version: str,
    ) -> None:
        self._stream_service = stream_service
        self._runtime_projector_version = runtime_projector_version

    async def load(self, *, session_id: str) -> _TurnContext:
        prior_events = await self._stream_service.read_stream(stream_id=session_id)
        expected_version = len(prior_events)
        runtime_state: dict[str, Any] | None = None
        if prior_events:
            runtime_state = self._stream_service.project_events(
                stream_id=session_id,
                events=prior_events,
                projector_name="session-runtime",
                projector_version=self._runtime_projector_version,
            )["state"]
        strategy_history: list[str] = []
        if runtime_state and isinstance(runtime_state.get("strategy_history"), list):
            strategy_history = [
                str(item) for item in runtime_state.get("strategy_history", []) if str(item).strip()
            ]
        turn_index = int((runtime_state or {}).get("turn_count", 0)) + 1
        transcript_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-transcript",
            projector_version="v1",
        )
        transcript_messages = list(transcript_projection["state"]["messages"])
        current_time = utc_now()
        last_event_at = prior_events[-1].occurred_at if prior_events else None
        session_started_at = prior_events[0].occurred_at if prior_events else None
        idle_gap_seconds = (
            max(0.0, (current_time - last_event_at).total_seconds())
            if last_event_at is not None
            else 0.0
        )
        session_age_seconds = (
            max(0.0, (current_time - session_started_at).total_seconds())
            if session_started_at is not None
            else 0.0
        )
        user_id: str | None = None
        session_metadata: dict[str, Any] | None = None
        if runtime_state:
            session_meta = runtime_state.get("session") or {}
            user_id = session_meta.get("user_id") or None
            metadata = session_meta.get("metadata")
            if isinstance(metadata, dict):
                session_metadata = dict(metadata)
        return _TurnContext(
            prior_events=prior_events,
            expected_version=expected_version,
            runtime_state=runtime_state,
            strategy_history=strategy_history,
            turn_index=turn_index,
            transcript_messages=transcript_messages,
            idle_gap_seconds=idle_gap_seconds,
            session_age_seconds=session_age_seconds,
            user_id=user_id,
            session_metadata=session_metadata,
        )

