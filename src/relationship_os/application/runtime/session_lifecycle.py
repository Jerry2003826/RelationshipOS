from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from relationship_os.domain.event_types import SESSION_STARTED, USER_MESSAGE_RECEIVED
from relationship_os.domain.events import NewEvent, utc_now

logger = logging.getLogger(__name__)


class SessionAlreadyExistsError(RuntimeError):
    """Raised when a session is created twice with the same identifier."""


class SessionLifecycleService:
    def __init__(
        self,
        *,
        stream_service: Any,
        user_service: Any,
        runtime_projector_version: str,
    ) -> None:
        self._stream_service = stream_service
        self._user_service = user_service
        self._runtime_projector_version = runtime_projector_version

    async def create_session(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_session_id = session_id or f"session-{uuid4().hex[:12]}"
        existing_events = await self._stream_service.read_stream(stream_id=resolved_session_id)
        if existing_events:
            raise SessionAlreadyExistsError(f"Session {resolved_session_id} already exists")

        session_payload: dict[str, Any] = {
            "session_id": resolved_session_id,
            "created_at": utc_now().isoformat(),
            "metadata": metadata or {},
        }
        if user_id:
            session_payload["user_id"] = user_id

        stored_events = await self._stream_service.append_events(
            stream_id=resolved_session_id,
            expected_version=0,
            events=[
                NewEvent(
                    event_type=SESSION_STARTED,
                    payload=session_payload,
                )
            ],
        )

        if user_id and self._user_service is not None:
            try:
                await self._user_service.link_session(
                    user_id=user_id, session_id=resolved_session_id
                )
            except Exception:
                logger.warning(
                    "Failed to link session %s to user %s",
                    resolved_session_id,
                    user_id,
                    exc_info=True,
                )

        runtime_projection = self._stream_service.project_events(
            stream_id=resolved_session_id,
            events=stored_events,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )
        return {
            "session_id": resolved_session_id,
            "user_id": user_id,
            "created": True,
            "events": [self._stream_service.serialize_event(event) for event in stored_events],
            "projection": runtime_projection,
        }

    async def list_sessions(self) -> list[dict[str, Any]]:
        stream_ids = await self._stream_service.list_stream_ids()
        sessions: list[dict[str, Any]] = []
        for stream_id in sorted(stream_ids):
            events = await self._stream_service.read_stream(stream_id=stream_id)
            session = {
                "session_id": stream_id,
                "user_id": None,
                "event_count": 0,
                "turn_count": 0,
                "started_at": None,
                "last_event_at": None,
            }
            for event in events:
                session["event_count"] += 1
                session["last_event_at"] = event.occurred_at.isoformat()
                if event.event_type == SESSION_STARTED:
                    session["started_at"] = event.payload.get("created_at")
                    session["user_id"] = event.payload.get("user_id")
                if event.event_type == USER_MESSAGE_RECEIVED:
                    session["turn_count"] += 1
            if session["started_at"] is not None:
                sessions.append(session)
        return sorted(
            sessions,
            key=lambda item: item["session_id"],
        )
