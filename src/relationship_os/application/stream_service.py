import hashlib
import json
from datetime import datetime
from uuid import UUID

from relationship_os.application.runtime_events import RuntimeEventBroker, RuntimeEventSubscription
from relationship_os.domain.event_store import EventStore
from relationship_os.domain.events import NewEvent, StoredEvent
from relationship_os.domain.projectors import VersionedProjectorRegistry


class StreamService:
    def __init__(
        self,
        *,
        event_store: EventStore,
        projector_registry: VersionedProjectorRegistry,
        runtime_event_broker: RuntimeEventBroker | None = None,
    ) -> None:
        self._event_store = event_store
        self._projector_registry = projector_registry
        self._runtime_event_broker = runtime_event_broker

    async def append_events(
        self,
        *,
        stream_id: str,
        expected_version: int | None,
        events: list[NewEvent],
    ) -> list[StoredEvent]:
        stored_events = await self._event_store.append(
            stream_id=stream_id,
            expected_version=expected_version,
            events=events,
        )
        if self._runtime_event_broker is not None:
            await self._runtime_event_broker.publish(
                stream_id=stream_id,
                events=stored_events,
            )
        return stored_events

    async def read_stream(self, *, stream_id: str) -> list[StoredEvent]:
        return await self._event_store.read_stream(stream_id=stream_id)

    async def read_all_events(self) -> list[StoredEvent]:
        return await self._event_store.read_all()

    async def list_stream_ids(self) -> list[str]:
        return sorted({event.stream_id for event in await self._event_store.read_all()})

    async def subscribe_runtime_events(self) -> RuntimeEventSubscription | None:
        if self._runtime_event_broker is None:
            return None
        return await self._runtime_event_broker.subscribe()

    async def project_stream(
        self,
        *,
        stream_id: str,
        projector_name: str,
        projector_version: str,
    ) -> dict[str, object]:
        projector = self._projector_registry.resolve(
            name=projector_name,
            version=projector_version,
        )
        state = projector.initial_state()
        events = await self._event_store.read_stream(stream_id=stream_id)
        for event in events:
            state = projector.apply(state, event)
        return {
            "projector": {
                "name": projector_name,
                "version": projector_version,
            },
            "stream_id": stream_id,
            "state": state,
        }

    def serialize_event(self, event: StoredEvent) -> dict[str, object]:
        return {
            "event_id": str(event.event_id),
            "stream_id": event.stream_id,
            "version": event.version,
            "event_type": event.event_type,
            "payload": event.payload,
            "metadata": event.metadata,
            "occurred_at": event.occurred_at.isoformat(),
        }

    def fingerprint_value(self, value: object) -> str:
        return self._fingerprint(value)

    async def replay_stream(
        self,
        *,
        stream_id: str,
        projector_name: str,
        projector_version: str,
    ) -> dict[str, object]:
        events = await self._event_store.read_stream(stream_id=stream_id)
        serialized_events = [self.serialize_event(event) for event in events]
        projection = await self.project_stream(
            stream_id=stream_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )
        replay_check = await self.project_stream(
            stream_id=stream_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )
        fingerprint = self._fingerprint(
            {
                "events": serialized_events,
                "projection": projection["state"],
            }
        )
        return {
            "stream_id": stream_id,
            "projector": projection["projector"],
            "event_count": len(serialized_events),
            "events": serialized_events,
            "projection": projection["state"],
            "fingerprint": fingerprint,
            "consistent": projection["state"] == replay_check["state"],
        }

    async def rebuild_projection(
        self,
        *,
        projector_name: str,
        projector_version: str,
        stream_ids: list[str] | None = None,
    ) -> dict[str, object]:
        target_stream_ids = stream_ids or await self.list_stream_ids()
        rebuild_results = []
        for stream_id in target_stream_ids:
            replay = await self.replay_stream(
                stream_id=stream_id,
                projector_name=projector_name,
                projector_version=projector_version,
            )
            rebuild_results.append(
                {
                    "stream_id": stream_id,
                    "event_count": replay["event_count"],
                    "fingerprint": replay["fingerprint"],
                    "consistent": replay["consistent"],
                }
            )
        return {
            "projector": {
                "name": projector_name,
                "version": projector_version,
            },
            "stream_count": len(rebuild_results),
            "streams": rebuild_results,
        }

    def _fingerprint(self, value: object) -> str:
        normalized = self._normalize(value)
        encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _normalize(self, value: object) -> object:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): self._normalize(item)
                for key, item in sorted(value.items(), key=lambda item: str(item[0]))
            }
        return value
