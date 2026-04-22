from collections.abc import Sequence
from typing import Protocol

from relationship_os.domain.events import NewEvent, StoredEvent


class EventStoreError(RuntimeError):
    """Base error for event store operations."""


class OptimisticConcurrencyError(EventStoreError):
    """Raised when the expected stream version does not match the current version."""


class EventStore(Protocol):
    async def append(
        self,
        *,
        stream_id: str,
        expected_version: int | None,
        events: Sequence[NewEvent],
    ) -> list[StoredEvent]: ...

    async def read_stream(self, *, stream_id: str) -> list[StoredEvent]: ...

    async def read_all(self) -> list[StoredEvent]: ...

    async def list_stream_ids(self) -> list[str]: ...
