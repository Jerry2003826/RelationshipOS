import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

from relationship_os.domain.events import StoredEvent


@dataclass(slots=True, frozen=True)
class RuntimeEventBatch:
    stream_id: str
    events: tuple[StoredEvent, ...]


_SHUTDOWN_SENTINEL = RuntimeEventBatch(stream_id="__shutdown__", events=())


class RuntimeEventSubscription:
    def __init__(
        self,
        *,
        broker: "RuntimeEventBroker",
        queue: asyncio.Queue[RuntimeEventBatch],
    ) -> None:
        self._broker = broker
        self._queue = queue

    async def get(self) -> RuntimeEventBatch:
        batch = await self._queue.get()
        if batch.stream_id == "__shutdown__":
            raise asyncio.CancelledError("broker shut down")
        return batch

    async def close(self) -> None:
        await self._broker.unsubscribe(self._queue)


class RuntimeEventBroker:
    def __init__(self) -> None:
        self._subscriptions: set[asyncio.Queue[RuntimeEventBatch]] = set()
        self._lock = asyncio.Lock()

    async def publish(
        self,
        *,
        stream_id: str,
        events: Iterable[StoredEvent],
    ) -> None:
        batch = RuntimeEventBatch(stream_id=stream_id, events=tuple(events))
        if not batch.events:
            return

        async with self._lock:
            subscriptions = list(self._subscriptions)

        for queue in subscriptions:
            while True:
                try:
                    queue.put_nowait(batch)
                    break
                except asyncio.QueueFull:
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

    async def unsubscribe(
        self,
        queue: asyncio.Queue[RuntimeEventBatch],
    ) -> None:
        async with self._lock:
            self._subscriptions.discard(queue)

    async def shutdown(self) -> None:
        async with self._lock:
            queues = list(self._subscriptions)
            self._subscriptions.clear()
        for queue in queues:
            try:
                queue.put_nowait(_SHUTDOWN_SENTINEL)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(_SHUTDOWN_SENTINEL)
                except asyncio.QueueFull:
                    pass

    async def subscribe(
        self,
        *,
        max_queue_size: int = 100,
    ) -> RuntimeEventSubscription:
        queue: asyncio.Queue[RuntimeEventBatch] = asyncio.Queue(maxsize=max_queue_size)
        async with self._lock:
            self._subscriptions.add(queue)
        return RuntimeEventSubscription(broker=self, queue=queue)
