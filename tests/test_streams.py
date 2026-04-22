import asyncio
from dataclasses import dataclass

from fastapi.testclient import TestClient

from relationship_os.application.analyzers.proactive.lifecycle_phase_specs import (
    LIFECYCLE_LEGACY_EVENT_TYPES,
)
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LEGACY_LIFECYCLE_STREAM_DETAIL,
    LEGACY_LIFECYCLE_STREAM_ERROR,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.events import NewEvent, StoredEvent
from relationship_os.domain.projectors import VersionedProjectorRegistry
from relationship_os.infrastructure.event_store.memory import InMemoryEventStore
from relationship_os.main import create_app


def test_append_read_and_project_stream() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/streams/session-1/events",
        json={
            "events": [
                {
                    "event_type": "user.message.received",
                    "payload": {"content": "你好"},
                },
                {
                    "event_type": "assistant.message.sent",
                    "payload": {"content": "你好，我们开始吧"},
                },
            ]
        },
    )

    assert response.status_code == 201
    created = response.json()["events"]
    assert [item["version"] for item in created] == [1, 2]

    read_response = client.get("/api/v1/streams/session-1/events")
    assert read_response.status_code == 200
    assert len(read_response.json()["events"]) == 2

    projection_response = client.get("/api/v1/streams/session-1/projection/session-transcript")
    assert projection_response.status_code == 200
    projection = projection_response.json()
    assert projection["projector"] == {"name": "session-transcript", "version": "v1"}
    assert projection["state"]["messages"][0]["role"] == "user"
    assert projection["state"]["messages"][1]["role"] == "assistant"

    replay_response = client.get("/api/v1/streams/session-1/replay")
    assert replay_response.status_code == 200
    replay = replay_response.json()
    assert replay["stream_id"] == "session-1"
    assert replay["consistent"] is True
    assert replay["event_count"] == 2
    assert replay["fingerprint"]


def test_append_detects_optimistic_concurrency_conflict() -> None:
    client = TestClient(create_app())

    first_response = client.post(
        "/api/v1/streams/session-2/events",
        json={
            "expected_version": 0,
            "events": [{"event_type": "user.message.received", "payload": {}}],
        },
    )
    assert first_response.status_code == 201

    conflict_response = client.post(
        "/api/v1/streams/session-2/events",
        json={
            "expected_version": 0,
            "events": [{"event_type": "assistant.message.sent", "payload": {}}],
        },
    )
    assert conflict_response.status_code == 409


def test_rebuild_projection_reports_selected_streams() -> None:
    client = TestClient(create_app())

    client.post(
        "/api/v1/streams/session-a/events",
        json={"events": [{"event_type": "user.message.received", "payload": {"content": "a"}}]},
    )
    client.post(
        "/api/v1/streams/session-b/events",
        json={"events": [{"event_type": "assistant.message.sent", "payload": {"content": "b"}}]},
    )

    response = client.post(
        "/api/v1/projectors/session-transcript/rebuild",
        json={"stream_ids": ["session-a", "session-b"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["projector"] == {"name": "session-transcript", "version": "v1"}
    assert body["stream_count"] == 2
    assert {item["stream_id"] for item in body["streams"]} == {"session-a", "session-b"}


@dataclass
class _ListStreamIdsOnlyEventStore:
    stream_ids: list[str]

    async def append(self, *, stream_id, expected_version, events):  # type: ignore[no-untyped-def]
        raise NotImplementedError

    async def read_stream(self, *, stream_id: str) -> list[StoredEvent]:
        raise NotImplementedError

    async def read_all(self) -> list[StoredEvent]:
        raise AssertionError("StreamService.list_stream_ids should not call read_all")

    async def list_stream_ids(self) -> list[str]:
        return list(self.stream_ids)


def test_stream_service_list_stream_ids_uses_native_event_store_lookup() -> None:
    stream_service = StreamService(
        event_store=_ListStreamIdsOnlyEventStore(["session-b", "session-a"]),
        projector_registry=VersionedProjectorRegistry(),
    )

    stream_ids = asyncio.run(stream_service.list_stream_ids())

    assert stream_ids == ["session-b", "session-a"]


def test_in_memory_event_store_read_all_returns_global_event_order() -> None:
    event_store = InMemoryEventStore()
    asyncio.run(
        event_store.append(
            stream_id="session-a",
            expected_version=None,
            events=[NewEvent(event_type="user.message.received", payload={"step": 1})],
        )
    )
    asyncio.run(
        event_store.append(
            stream_id="session-b",
            expected_version=None,
            events=[NewEvent(event_type="assistant.message.sent", payload={"step": 2})],
        )
    )
    asyncio.run(
        event_store.append(
            stream_id="session-a",
            expected_version=None,
            events=[NewEvent(event_type="assistant.message.sent", payload={"step": 3})],
        )
    )

    events = asyncio.run(event_store.read_all())

    assert [event.payload["step"] for event in events] == [1, 2, 3]


def test_stream_service_apply_events_matches_full_runtime_projection() -> None:
    with TestClient(create_app()) as client:
        turn_response = client.post(
            "/api/v1/sessions/stream-projection/turns",
            json={"content": "Keep this plan practical and low pressure."},
        )
        assert turn_response.status_code == 201

        container = client.app.state.container
        events = asyncio.run(container.stream_service.read_stream(stream_id="stream-projection"))
        assert len(events) > 1

        full_projection = container.stream_service.project_events(
            stream_id="stream-projection",
            events=events,
            projector_name="session-runtime",
            projector_version="v2",
        )
        base_projection = container.stream_service.project_events(
            stream_id="stream-projection",
            events=events[:-1],
            projector_name="session-runtime",
            projector_version="v2",
        )
        incremental_projection = container.stream_service.apply_events(
            stream_id="stream-projection",
            state=base_projection["state"],
            events=events[-1:],
            projector_name="session-runtime",
            projector_version="v2",
        )

    assert incremental_projection["state"] == full_projection["state"]


def test_runtime_v2_projects_lifecycle_snapshot_without_legacy_raw_events() -> None:
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/sessions/stream-lifecycle/turns",
            json={"content": "I'm exhausted and need a calm next step."},
        )
        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/sessions/stream-lifecycle/turns",
            json={"content": "Let's keep going, but make it steady and small."},
        )
        assert second_response.status_code == 201

        queue_item = client.get("/api/v1/runtime/proactive-followups").json()["items"][0]
        dispatch_response = client.post(
            "/api/v1/runtime/proactive-followups/dispatch",
            params={"as_of": queue_item["due_at"]},
        )
        assert dispatch_response.status_code == 200

        container = client.app.state.container
        events = asyncio.run(container.stream_service.read_stream(stream_id="stream-lifecycle"))
        event_types = [event.event_type for event in events]
        projection = asyncio.run(
            container.stream_service.project_stream(
                stream_id="stream-lifecycle",
                projector_name="session-runtime",
                projector_version="v2",
            )
        )

    assert "system.proactive_lifecycle_snapshot.updated" in event_types
    assert not any(event_type in LIFECYCLE_LEGACY_EVENT_TYPES for event_type in event_types)
    assert projection["state"]["proactive_lifecycle_snapshot_count"] >= 1
    assert projection["state"]["proactive_lifecycle_snapshot"] is not None
    assert projection["state"]["proactive_lifecycle_dispatch_decision"] is not None
    assert projection["state"]["proactive_lifecycle_outcome_decision"] is not None


def test_legacy_lifecycle_stream_remains_raw_visible_but_projection_endpoints_return_409() -> None:
    with TestClient(create_app()) as client:
        append_response = client.post(
            "/api/v1/streams/legacy-lifecycle/events",
            json={
                "events": [
                    {
                        "event_type": "session.started",
                        "payload": {
                            "session_id": "legacy-lifecycle",
                            "created_at": "2026-03-22T00:00:00+00:00",
                            "metadata": {},
                        },
                    },
                    {
                        "event_type": "system.proactive_lifecycle_state.updated",
                        "payload": {"status": "active", "state_key": "legacy"},
                    },
                ]
            },
        )
        assert append_response.status_code == 201

        raw_events_response = client.get("/api/v1/streams/legacy-lifecycle/events")
        runtime_trace_response = client.get("/api/v1/runtime/trace/legacy-lifecycle")
        runtime_audit_response = client.get("/api/v1/runtime/audit/legacy-lifecycle")
        projection_response = client.get(
            "/api/v1/streams/legacy-lifecycle/projection/session-runtime",
            params={"version": "v2"},
        )
        replay_response = client.get(
            "/api/v1/streams/legacy-lifecycle/replay",
            params={"projector_name": "session-runtime", "version": "v2"},
        )
        rebuild_response = client.post(
            "/api/v1/projectors/session-runtime/rebuild",
            json={"version": "v2", "stream_ids": ["legacy-lifecycle"]},
        )
        session_response = client.get("/api/v1/sessions/legacy-lifecycle")
        evaluation_response = client.get("/api/v1/evaluations/sessions/legacy-lifecycle")

    assert raw_events_response.status_code == 200
    raw_event_types = [item["event_type"] for item in raw_events_response.json()["events"]]
    assert "system.proactive_lifecycle_state.updated" in raw_event_types
    expected_error = {
        "error": LEGACY_LIFECYCLE_STREAM_ERROR,
        "detail": LEGACY_LIFECYCLE_STREAM_DETAIL,
    }
    assert runtime_trace_response.status_code == 200
    assert any(
        item["event_type"] == "system.proactive_lifecycle_state.updated"
        for item in runtime_trace_response.json()["trace"]
    )
    assert runtime_audit_response.status_code == 200
    runtime_audit = runtime_audit_response.json()
    assert runtime_audit["projection_supported"] is False
    assert runtime_audit["projection_error"] == expected_error
    assert runtime_audit["event_type_counts"]["system.proactive_lifecycle_state.updated"] == 1
    assert projection_response.status_code == 409
    assert projection_response.json() == expected_error
    assert replay_response.status_code == 409
    assert replay_response.json() == expected_error
    assert rebuild_response.status_code == 409
    assert rebuild_response.json() == expected_error
    assert session_response.status_code == 409
    assert session_response.json() == expected_error
    assert evaluation_response.status_code == 409
    assert evaluation_response.json() == expected_error
