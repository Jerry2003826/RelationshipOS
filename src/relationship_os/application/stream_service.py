import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from relationship_os.application.runtime_events import RuntimeEventBroker, RuntimeEventSubscription
from relationship_os.domain.event_store import EventStore
from relationship_os.domain.events import NewEvent, StoredEvent
from relationship_os.domain.projectors import VersionedProjectorRegistry

_PROJECTION_SNAPSHOT_EVENT_TYPE = "system.projection_snapshot.saved"
_PROJECTION_SNAPSHOT_PREFIX = "__projection_snapshot__:"


@dataclass(slots=True)
class _ProjectionSnapshot:
    version: int
    state: dict[str, object]


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
        self._projection_snapshots: dict[tuple[str, str, str], _ProjectionSnapshot] = {}

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

    async def read_stream(
        self,
        *,
        stream_id: str,
        after_version: int = 0,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        return await self._event_store.read_stream(
            stream_id=stream_id,
            after_version=after_version,
            limit=limit,
        )

    async def read_all_events(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        events = await self._event_store.read_all(offset=offset, limit=limit)
        return [event for event in events if not _is_internal_stream_id(event.stream_id)]

    async def list_stream_ids(self) -> list[str]:
        stream_ids = await self._event_store.list_stream_ids()
        return [
            stream_id
            for stream_id in stream_ids
            if not _is_internal_stream_id(stream_id)
        ]

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
        self._projector_registry.resolve(
            name=projector_name,
            version=projector_version,
        )
        snapshot_key = (stream_id, projector_name, projector_version)
        snapshot = self._projection_snapshots.get(snapshot_key)
        if snapshot is None:
            snapshot = await self._load_projection_snapshot(
                stream_id=stream_id,
                projector_name=projector_name,
                projector_version=projector_version,
            )
        if snapshot is not None:
            events = await self._event_store.read_stream(
                stream_id=stream_id,
                after_version=snapshot.version,
            )
            if not events:
                return {
                    "projector": {
                        "name": projector_name,
                        "version": projector_version,
                    },
                    "stream_id": stream_id,
                    "state": deepcopy(snapshot.state),
                }
            projection = self.apply_events(
                stream_id=stream_id,
                state=deepcopy(snapshot.state),
                events=events,
                projector_name=projector_name,
                projector_version=projector_version,
            )
        else:
            events = await self._event_store.read_stream(stream_id=stream_id)
            projection = self.project_events(
                stream_id=stream_id,
                events=events,
                projector_name=projector_name,
                projector_version=projector_version,
            )

        latest_version = events[-1].version if events else 0
        self._projection_snapshots[snapshot_key] = _ProjectionSnapshot(
            version=latest_version,
            state=deepcopy(projection["state"]),
        )
        if latest_version > 0:
            await self._save_projection_snapshot(
                stream_id=stream_id,
                projector_name=projector_name,
                projector_version=projector_version,
                version=latest_version,
                state=projection["state"],
            )
        return projection

    def project_events(
        self,
        *,
        stream_id: str,
        events: list[StoredEvent],
        projector_name: str,
        projector_version: str,
    ) -> dict[str, object]:
        projector = self._projector_registry.resolve(
            name=projector_name,
            version=projector_version,
        )
        state = projector.initial_state()
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

    def apply_events(
        self,
        *,
        stream_id: str,
        state: dict[str, object],
        events: list[StoredEvent],
        projector_name: str,
        projector_version: str,
    ) -> dict[str, object]:
        projector = self._projector_registry.resolve(
            name=projector_name,
            version=projector_version,
        )
        next_state = state
        for event in events:
            next_state = projector.apply(next_state, event)
        return {
            "projector": {
                "name": projector_name,
                "version": projector_version,
            },
            "stream_id": stream_id,
            "state": next_state,
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
        projection = self.project_events(
            stream_id=stream_id,
            events=events,
            projector_name=projector_name,
            projector_version=projector_version,
        )
        replay_check = self.project_events(
            stream_id=stream_id,
            events=events,
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

    async def _load_projection_snapshot(
        self,
        *,
        stream_id: str,
        projector_name: str,
        projector_version: str,
    ) -> _ProjectionSnapshot | None:
        snapshot_stream_id = _projection_snapshot_stream_id(
            stream_id=stream_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )
        events = await self._event_store.read_stream(stream_id=snapshot_stream_id)
        for event in reversed(events):
            if event.event_type != _PROJECTION_SNAPSHOT_EVENT_TYPE:
                continue
            payload = event.payload
            if (
                payload.get("stream_id") != stream_id
                or payload.get("projector_name") != projector_name
                or payload.get("projector_version") != projector_version
            ):
                continue
            version = payload.get("version")
            state = payload.get("state")
            if isinstance(version, int) and isinstance(state, dict):
                snapshot = _ProjectionSnapshot(version=version, state=deepcopy(state))
                self._projection_snapshots[
                    (stream_id, projector_name, projector_version)
                ] = snapshot
                return snapshot
        return None

    async def _save_projection_snapshot(
        self,
        *,
        stream_id: str,
        projector_name: str,
        projector_version: str,
        version: int,
        state: object,
    ) -> None:
        snapshot_stream_id = _projection_snapshot_stream_id(
            stream_id=stream_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )
        await self._event_store.append(
            stream_id=snapshot_stream_id,
            expected_version=None,
            events=[
                NewEvent(
                    event_type=_PROJECTION_SNAPSHOT_EVENT_TYPE,
                    payload={
                        "stream_id": stream_id,
                        "projector_name": projector_name,
                        "projector_version": projector_version,
                        "version": version,
                        "state": deepcopy(state),
                    },
                )
            ],
        )

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


def _is_internal_stream_id(stream_id: str) -> bool:
    return stream_id.startswith(_PROJECTION_SNAPSHOT_PREFIX)


def _projection_snapshot_stream_id(
    *,
    stream_id: str,
    projector_name: str,
    projector_version: str,
) -> str:
    key = f"{stream_id}\0{projector_name}\0{projector_version}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return f"{_PROJECTION_SNAPSHOT_PREFIX}{digest}"
