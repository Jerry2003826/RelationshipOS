"""UserService — manages user identity and cross-session relationships."""

from __future__ import annotations

from typing import Any

from relationship_os.application.projectors.user_profile import build_user_profile
from relationship_os.application.stream_service import StreamService
from relationship_os.core.logging import get_logger
from relationship_os.domain.event_types import (
    USER_CREATED,
    USER_PROFILE_UPDATED,
    USER_SESSION_LINKED,
)
from relationship_os.domain.events import NewEvent, utc_now


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user that already exists."""


class UserNotFoundError(Exception):
    """Raised when a user does not exist."""


def _user_stream_id(user_id: str) -> str:
    return f"user:{user_id}"


class UserService:
    """Manages person-centric identity: user creation, session linking, and profile reads."""

    def __init__(self, *, stream_service: StreamService) -> None:
        self._stream = stream_service
        self._logger = get_logger("relationship_os.user_service")

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create_user(
        self,
        *,
        user_id: str,
        display_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new user identity stream.

        Raises UserAlreadyExistsError if the user stream already exists.
        """
        stream_id = _user_stream_id(user_id)
        existing = await self._stream.read_stream(stream_id=stream_id)
        if existing:
            raise UserAlreadyExistsError(f"User {user_id!r} already exists")

        await self._stream.append_events(
            stream_id=stream_id,
            expected_version=0,
            events=[
                NewEvent(
                    event_type=USER_CREATED,
                    payload={
                        "user_id": user_id,
                        "display_name": display_name,
                        "created_at": utc_now().isoformat(),
                        "metadata": metadata or {},
                    },
                )
            ],
        )
        self._logger.info("user_created", user_id=user_id)
        return {"user_id": user_id, "created": True}

    async def link_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> None:
        """Link a session to this user, auto-creating the user if needed."""
        stream_id = _user_stream_id(user_id)
        existing = await self._stream.read_stream(stream_id=stream_id)

        events: list[NewEvent] = []
        expected_version: int | None

        if not existing:
            # Auto-create the user stream on first session link
            events.append(
                NewEvent(
                    event_type=USER_CREATED,
                    payload={
                        "user_id": user_id,
                        "display_name": None,
                        "created_at": utc_now().isoformat(),
                        "metadata": {},
                    },
                )
            )
            expected_version = 0
        else:
            expected_version = None  # append without version check

        events.append(
            NewEvent(
                event_type=USER_SESSION_LINKED,
                payload={
                    "user_id": user_id,
                    "session_id": session_id,
                    "linked_at": utc_now().isoformat(),
                },
            )
        )

        await self._stream.append_events(
            stream_id=stream_id,
            expected_version=expected_version,
            events=events,
        )
        self._logger.info("session_linked", user_id=user_id, session_id=session_id)

    async def update_profile(
        self,
        *,
        user_id: str,
        display_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update user profile fields."""
        stream_id = _user_stream_id(user_id)
        payload: dict[str, Any] = {"user_id": user_id, "updated_at": utc_now().isoformat()}
        if display_name is not None:
            payload["display_name"] = display_name
        if metadata is not None:
            payload["metadata"] = metadata

        await self._stream.append_events(
            stream_id=stream_id,
            expected_version=None,
            events=[NewEvent(event_type=USER_PROFILE_UPDATED, payload=payload)],
        )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_user_index(self, *, user_id: str) -> dict[str, Any]:
        """Return the user-index projection (lightweight: user_id, session_ids, metadata)."""
        proj = await self._stream.project_stream(
            stream_id=_user_stream_id(user_id),
            projector_name="user-index",
            projector_version="v1",
        )
        return proj.get("state", {})

    async def get_user_sessions(self, *, user_id: str) -> list[str]:
        """Return list of session IDs linked to this user."""
        index = await self.get_user_index(user_id=user_id)
        return index.get("session_ids") or []

    async def get_user_profile(self, *, user_id: str) -> dict[str, Any]:
        """Return cross-session aggregated user profile."""
        return await build_user_profile(user_id=user_id, stream_service=self._stream)

    async def get_self_state(self, *, user_id: str) -> dict[str, Any]:
        """Return the AI's self-state for this user (relationship memory)."""
        proj = await self._stream.project_stream(
            stream_id=_user_stream_id(user_id),
            projector_name="self-state",
            projector_version="v1",
        )
        return proj.get("state", {})

    async def user_exists(self, *, user_id: str) -> bool:
        """Return True if the user stream exists."""
        events = await self._stream.read_stream(stream_id=_user_stream_id(user_id))
        return bool(events)
