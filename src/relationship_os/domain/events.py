from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, frozen=True)
class NewEvent:
    event_type: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class StoredEvent:
    event_id: UUID
    stream_id: str
    version: int
    event_type: str
    payload: dict[str, Any]
    metadata: dict[str, Any]
    occurred_at: datetime

    @classmethod
    def from_new_event(
        cls,
        *,
        stream_id: str,
        version: int,
        event: NewEvent,
    ) -> "StoredEvent":
        return cls(
            event_id=uuid4(),
            stream_id=stream_id,
            version=version,
            event_type=event.event_type,
            payload=dict(event.payload),
            metadata=dict(event.metadata),
            occurred_at=utc_now(),
        )
