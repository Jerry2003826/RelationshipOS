from sqlalchemy import DateTime, Index, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text
from sqlalchemy.sql.schema import Column, Table, UniqueConstraint

from relationship_os.infrastructure.db.metadata import metadata

event_records = Table(
    "event_records",
    metadata,
    Column("event_id", Uuid(as_uuid=True), primary_key=True),
    Column("stream_id", String(length=255), nullable=False),
    Column("version", Integer, nullable=False),
    Column("event_type", String(length=255), nullable=False),
    Column("payload", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("occurred_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("stream_id", "version"),
    Index("ix_event_records_stream_id_occurred_at", "stream_id", "occurred_at"),
)

