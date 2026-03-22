from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from relationship_os.domain.event_store import EventStore, OptimisticConcurrencyError
from relationship_os.domain.events import NewEvent, StoredEvent
from relationship_os.infrastructure.db.tables import event_records


def _row_to_stored_event(row: RowMapping) -> StoredEvent:
    return StoredEvent(
        event_id=row["event_id"],
        stream_id=row["stream_id"],
        version=row["version"],
        event_type=row["event_type"],
        payload=dict(row["payload"]),
        metadata=dict(row["metadata"]),
        occurred_at=row["occurred_at"],
    )


def _event_to_record(event: StoredEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "stream_id": event.stream_id,
        "version": event.version,
        "event_type": event.event_type,
        "payload": event.payload,
        "metadata": event.metadata,
        "occurred_at": event.occurred_at,
    }


class PostgresEventStore(EventStore):
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def append(
        self,
        *,
        stream_id: str,
        expected_version: int | None,
        events: Sequence[NewEvent],
    ) -> list[StoredEvent]:
        if not events:
            return []

        async with self._engine.begin() as connection:
            current_version = await self._read_current_version(
                connection=connection,
                stream_id=stream_id,
            )
            if expected_version is not None and expected_version != current_version:
                raise OptimisticConcurrencyError(
                    f"Expected version {expected_version}, got {current_version}"
                )

            stored_events = [
                StoredEvent.from_new_event(
                    stream_id=stream_id,
                    version=current_version + offset,
                    event=event,
                )
                for offset, event in enumerate(events, start=1)
            ]

            try:
                await connection.execute(
                    insert(event_records),
                    [_event_to_record(event) for event in stored_events],
                )
            except IntegrityError as exc:
                raise OptimisticConcurrencyError(
                    f"Concurrent append detected for stream {stream_id}"
                ) from exc

        return stored_events

    async def read_stream(self, *, stream_id: str) -> list[StoredEvent]:
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(event_records)
                .where(event_records.c.stream_id == stream_id)
                .order_by(event_records.c.version.asc())
            )
            return [_row_to_stored_event(row) for row in result.mappings().all()]

    async def read_all(self) -> list[StoredEvent]:
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(event_records).order_by(
                    event_records.c.occurred_at.asc(),
                    event_records.c.stream_id.asc(),
                    event_records.c.version.asc(),
                )
            )
            return [_row_to_stored_event(row) for row in result.mappings().all()]

    async def list_stream_ids(self) -> list[str]:
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(event_records.c.stream_id)
                .distinct()
                .order_by(event_records.c.stream_id.asc())
            )
            return [str(stream_id) for stream_id in result.scalars().all()]

    async def _read_current_version(
        self,
        *,
        connection: AsyncConnection,
        stream_id: str,
    ) -> int:
        statement = select(func.max(event_records.c.version)).where(
            event_records.c.stream_id == stream_id
        )
        current_version = await connection.scalar(statement)
        return int(current_version or 0)
