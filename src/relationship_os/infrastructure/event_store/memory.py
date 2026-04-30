import asyncio
from itertools import chain

from relationship_os.domain.event_store import EventStore, OptimisticConcurrencyError
from relationship_os.domain.events import NewEvent, StoredEvent


class InMemoryEventStore(EventStore):
    def __init__(self) -> None:
        self._streams: dict[str, list[StoredEvent]] = {}
        self._lock = asyncio.Lock()

    async def append(
        self,
        *,
        stream_id: str,
        expected_version: int | None,
        events: list[NewEvent],
    ) -> list[StoredEvent]:
        async with self._lock:
            stream = self._streams.setdefault(stream_id, [])
            current_version = stream[-1].version if stream else 0

            if expected_version is not None and expected_version != current_version:
                raise OptimisticConcurrencyError(
                    f"Expected version {expected_version}, got {current_version}"
                )

            stored_events: list[StoredEvent] = []
            for offset, event in enumerate(events, start=1):
                stored_event = StoredEvent.from_new_event(
                    stream_id=stream_id,
                    version=current_version + offset,
                    event=event,
                )
                stream.append(stored_event)
                stored_events.append(stored_event)
            return stored_events

    async def read_stream(
        self,
        *,
        stream_id: str,
        after_version: int = 0,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        async with self._lock:
            events = [
                event
                for event in self._streams.get(stream_id, [])
                if event.version > max(0, after_version)
            ]
            if limit is not None:
                events = events[: max(0, limit)]
            return list(events)

    async def read_all(self, *, offset: int = 0, limit: int | None = None) -> list[StoredEvent]:
        async with self._lock:
            events = list(chain.from_iterable(self._streams.values()))
        ordered = sorted(
            events,
            key=lambda event: (
                event.occurred_at,
                event.stream_id,
                event.version,
            ),
        )
        start = max(0, offset)
        if limit is None:
            return ordered[start:]
        return ordered[start : start + max(0, limit)]

    async def list_stream_ids(self) -> list[str]:
        async with self._lock:
            return sorted(self._streams)
