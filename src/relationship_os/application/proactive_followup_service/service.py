from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from relationship_os.application.proactive_followup_service.followup_builder import (
    build_followup_item,
    sort_key,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.events import utc_now


class ProactiveFollowupService:
    """Thin service that lists followup items by delegating to the builder."""

    def __init__(
        self,
        *,
        stream_service: StreamService,
        runtime_projector_version: str = "v2",
    ) -> None:
        self._stream_service = stream_service
        self._runtime_projector_version = runtime_projector_version

    async def list_followups(
        self,
        *,
        as_of: datetime | None = None,
        include_hold: bool = True,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Return prioritised followup items across all sessions."""
        reference_time = as_of or utc_now()
        stream_ids = await self._stream_service.list_stream_ids()
        items = await asyncio.gather(
            *(
                build_followup_item(
                    stream_service=self._stream_service,
                    session_id=session_id,
                    reference_time=reference_time,
                    runtime_projector_version=self._runtime_projector_version,
                )
                for session_id in stream_ids
            )
        )
        followups = [item for item in items if item is not None]
        if not include_hold:
            followups = [item for item in followups if item.get("queue_status") != "hold"]
        followups.sort(key=sort_key)
        if limit is not None:
            followups = followups[:limit]

        status_counts: dict[str, int] = {
            "hold": 0,
            "waiting": 0,
            "scheduled": 0,
            "due": 0,
            "overdue": 0,
        }
        for item in items:
            if item is None:
                continue
            queue_status = str(item.get("queue_status") or "hold")
            status_counts[queue_status] = status_counts.get(queue_status, 0) + 1

        next_due_item = next(
            (
                item
                for item in followups
                if item.get("queue_status") in {"waiting", "scheduled", "due", "overdue"}
                and item.get("due_at")
            ),
            None,
        )
        return {
            "as_of": reference_time.isoformat(),
            "session_count": len([item for item in items if item is not None]),
            "actionable_count": status_counts["due"] + status_counts["overdue"],
            "status_counts": status_counts,
            "next_due_at": (next_due_item or {}).get("due_at"),
            "items": followups,
        }
