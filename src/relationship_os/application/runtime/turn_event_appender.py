from __future__ import annotations

from typing import Any

from relationship_os.domain.events import NewEvent, StoredEvent


class TurnEventAppender:
    def __init__(self, *, stream_service: Any, runtime_projector_version: str) -> None:
        self._stream_service = stream_service
        self._runtime_projector_version = runtime_projector_version

    async def append(
        self,
        *,
        session_id: str,
        turn_context: Any,
        events: list[NewEvent],
    ) -> tuple[list[StoredEvent], dict[str, Any]]:
        stored_events = await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=turn_context.expected_version,
            events=events,
        )
        runtime_projection = self._stream_service.apply_events(
            stream_id=session_id,
            state=turn_context.runtime_state
            or self._stream_service.project_events(
                stream_id=session_id,
                events=turn_context.prior_events,
                projector_name="session-runtime",
                projector_version=self._runtime_projector_version,
            )["state"],
            events=stored_events,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )
        return stored_events, runtime_projection
