import asyncio
from typing import Any
from uuid import uuid4

from relationship_os.application.proactive_followup_service import (
    ProactiveFollowupService,
)
from relationship_os.application.runtime_service import RuntimeService
from relationship_os.core.logging import get_logger
from relationship_os.domain.events import utc_now


class ProactiveFollowupDispatcher:
    def __init__(
        self,
        *,
        proactive_followup_service: ProactiveFollowupService,
        runtime_service: RuntimeService,
        worker_id: str | None = None,
        poll_interval_seconds: float = 5.0,
        max_dispatch_per_cycle: int = 2,
    ) -> None:
        self._proactive_followup_service = proactive_followup_service
        self._runtime_service = runtime_service
        self._worker_id = worker_id or f"followup-{uuid4().hex[:8]}"
        self._poll_interval_seconds = max(0.2, poll_interval_seconds)
        self._max_dispatch_per_cycle = max(1, max_dispatch_per_cycle)
        self._active_dispatches: set[str] = set()
        self._lock = asyncio.Lock()
        self._poller_task: asyncio.Task[None] | None = None
        self._last_run_report: dict[str, Any] = {
            "source": "startup",
            "candidate_count": 0,
            "dispatched_count": 0,
            "skipped_count": 0,
            "dispatched_session_ids": [],
            "last_run_at": None,
        }
        self._logger = get_logger("relationship_os.proactive_followups.dispatcher")

    async def start(self) -> None:
        async with self._lock:
            if self._poller_task is not None and not self._poller_task.done():
                return
            self._poller_task = asyncio.create_task(
                self._poll_loop(),
                name=f"proactive-followup-poller:{self._worker_id}",
            )

    async def shutdown(self) -> None:
        async with self._lock:
            poller_task = self._poller_task
            if poller_task is not None:
                poller_task.cancel()
            self._active_dispatches.clear()
        if poller_task is not None:
            await asyncio.gather(poller_task, return_exceptions=True)
        async with self._lock:
            self._poller_task = None

    async def dispatch_due_followups(
        self,
        *,
        source: str,
        as_of=None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        payload = await self._proactive_followup_service.list_followups(
            as_of=as_of,
            include_hold=False,
            limit=max(limit or self._max_dispatch_per_cycle, self._max_dispatch_per_cycle),
        )
        candidates = [
            item
            for item in list(payload.get("items", []))
            if item.get("queue_status") in {"due", "overdue"}
        ]
        if limit is not None:
            candidates = candidates[: max(1, limit)]
        else:
            candidates = candidates[: self._max_dispatch_per_cycle]

        dispatched_session_ids: list[str] = []
        skipped: list[dict[str, Any]] = []
        for item in candidates:
            session_id = str(item.get("session_id") or "")
            if not session_id:
                continue
            if not await self._begin_dispatch(session_id):
                skipped.append(
                    {
                        "session_id": session_id,
                        "reason": "dispatch_already_in_progress",
                    }
                )
                continue
            try:
                result = await self._runtime_service.dispatch_proactive_followup(
                    session_id=session_id,
                    source=source,
                    queue_item=item,
                )
            finally:
                await self._end_dispatch(session_id)
            if bool(result.get("dispatched")):
                dispatched_session_ids.append(session_id)
            else:
                skipped.append(
                    {
                        "session_id": session_id,
                        "reason": str(result.get("reason") or "skipped"),
                    }
                )

        report = {
            "source": source,
            "worker_id": self._worker_id,
            "candidate_count": len(candidates),
            "dispatched_count": len(dispatched_session_ids),
            "skipped_count": len(skipped),
            "dispatched_session_ids": dispatched_session_ids,
            "skipped": skipped[:8],
            "last_run_at": utc_now().isoformat(),
        }
        self._last_run_report = report
        if dispatched_session_ids or skipped:
            self._logger.info(
                "proactive_followup_dispatch_cycle",
                worker_id=self._worker_id,
                source=source,
                candidate_count=report["candidate_count"],
                dispatched_count=report["dispatched_count"],
                skipped_count=report["skipped_count"],
                dispatched_session_ids=dispatched_session_ids,
            )
        return report

    async def get_runtime_state(self) -> dict[str, Any]:
        async with self._lock:
            active_dispatches = sorted(self._active_dispatches)
            poller_running = self._poller_task is not None and not self._poller_task.done()
        return {
            "worker_id": self._worker_id,
            "poll_interval_seconds": self._poll_interval_seconds,
            "max_dispatch_per_cycle": self._max_dispatch_per_cycle,
            "active_dispatch_count": len(active_dispatches),
            "active_dispatch_session_ids": active_dispatches,
            "poller_running": poller_running,
            "last_run_report": dict(self._last_run_report),
        }

    async def _begin_dispatch(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._active_dispatches:
                return False
            self._active_dispatches.add(session_id)
            return True

    async def _end_dispatch(self, session_id: str) -> None:
        async with self._lock:
            self._active_dispatches.discard(session_id)

    async def _poll_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._poll_interval_seconds)
                await self.dispatch_due_followups(source="poll")
        except asyncio.CancelledError:
            return
