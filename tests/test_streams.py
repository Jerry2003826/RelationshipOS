import asyncio
from dataclasses import dataclass

from fastapi.testclient import TestClient

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

    projection_response = client.get(
        "/api/v1/streams/session-1/projection/session-transcript"
    )
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
        json={
            "events": [{"event_type": "user.message.received", "payload": {"content": "a"}}]
        },
    )
    client.post(
        "/api/v1/streams/session-b/events",
        json={
            "events": [{"event_type": "assistant.message.sent", "payload": {"content": "b"}}]
        },
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
