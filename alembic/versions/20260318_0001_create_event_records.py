"""create event records

Revision ID: 20260318_0001
Revises:
Create Date: 2026-03-18 22:25:00

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_records",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("stream_id", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk_event_records")),
        sa.UniqueConstraint(
            "stream_id",
            "version",
            name=op.f("uq_event_records_stream_id_version"),
        ),
    )
    op.create_index(
        "ix_event_records_stream_id_occurred_at",
        "event_records",
        ["stream_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_event_records_stream_id_occurred_at", table_name="event_records")
    op.drop_table("event_records")
