import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from relationship_os.application.runtime.session_lifecycle import SessionLifecycleService
from relationship_os.domain.event_types import SESSION_STARTED, USER_MESSAGE_RECEIVED


def test_session_lifecycle_creates_session_links_user_and_projects_runtime_state() -> None:
    calls = []
    stored_event = SimpleNamespace(
        event_type=SESSION_STARTED,
        payload={"session_id": "session-1"},
    )

    class _StreamService:
        async def read_stream(self, *, stream_id: str):  # type: ignore[no-untyped-def]
            calls.append(("read", stream_id))
            return []

        async def append_events(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("append", kwargs))
            return [stored_event]

        def project_events(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("project", kwargs))
            return {"state": {"turn_count": 0}}

        def serialize_event(self, event):  # type: ignore[no-untyped-def]
            return {"event_type": event.event_type, "payload": event.payload}

    class _UserService:
        async def link_session(self, *, user_id: str, session_id: str):  # type: ignore[no-untyped-def]
            calls.append(("link", user_id, session_id))

    result = asyncio.run(
        SessionLifecycleService(
            stream_service=_StreamService(),
            user_service=_UserService(),
            runtime_projector_version="v2",
        ).create_session(
            session_id="session-1",
            user_id="user-1",
            metadata={"source": "test"},
        )
    )

    assert calls[0] == ("read", "session-1")
    assert calls[1][0] == "append"
    append_kwargs = calls[1][1]
    assert append_kwargs["stream_id"] == "session-1"
    assert append_kwargs["expected_version"] == 0
    assert append_kwargs["events"][0].event_type == SESSION_STARTED
    assert append_kwargs["events"][0].payload["user_id"] == "user-1"
    assert append_kwargs["events"][0].payload["metadata"] == {"source": "test"}
    assert calls[2] == ("link", "user-1", "session-1")
    assert calls[3][0] == "project"
    assert result["session_id"] == "session-1"
    assert result["user_id"] == "user-1"
    assert result["created"] is True
    assert result["events"] == [
        {"event_type": SESSION_STARTED, "payload": {"session_id": "session-1"}}
    ]
    assert result["projection"] == {"state": {"turn_count": 0}}


def test_session_lifecycle_lists_started_sessions_with_turn_counts() -> None:
    now = datetime.now(UTC)

    class _StreamService:
        async def list_stream_ids(self):  # type: ignore[no-untyped-def]
            return ["z-session", "a-session", "internal-empty"]

        async def read_stream(self, *, stream_id: str):  # type: ignore[no-untyped-def]
            if stream_id == "internal-empty":
                return []
            return [
                SimpleNamespace(
                    event_type=SESSION_STARTED,
                    payload={"created_at": f"{stream_id}-created", "user_id": f"{stream_id}-user"},
                    occurred_at=now,
                ),
                SimpleNamespace(
                    event_type=USER_MESSAGE_RECEIVED,
                    payload={},
                    occurred_at=now,
                ),
            ]

    sessions = asyncio.run(
        SessionLifecycleService(
            stream_service=_StreamService(),
            user_service=None,
            runtime_projector_version="v2",
        ).list_sessions()
    )

    assert [session["session_id"] for session in sessions] == ["a-session", "z-session"]
    assert sessions[0]["user_id"] == "a-session-user"
    assert sessions[0]["event_count"] == 2
    assert sessions[0]["turn_count"] == 1
    assert sessions[0]["started_at"] == "a-session-created"
    assert sessions[0]["last_event_at"] == now.isoformat()
