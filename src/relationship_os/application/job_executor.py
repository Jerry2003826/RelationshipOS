import asyncio
from typing import Any
from uuid import uuid4

from relationship_os.application.job_service import JobService
from relationship_os.core.logging import get_logger
from relationship_os.domain.events import utc_now

RECOVERY_STATUSES = ("queued", "claimed", "running")


class JobExecutor:
    def __init__(
        self,
        *,
        job_service: JobService,
        auto_retry_failed_jobs: bool = True,
        worker_id: str | None = None,
        poll_interval_seconds: float = 0.5,
        claim_ttl_seconds: float = 5.0,
        heartbeat_interval_seconds: float = 1.0,
    ) -> None:
        self._job_service = job_service
        self._auto_retry_failed_jobs = auto_retry_failed_jobs
        self._worker_id = worker_id or f"worker-{uuid4().hex[:8]}"
        self._poll_interval_seconds = max(0.1, poll_interval_seconds)
        self._claim_ttl_seconds = max(0.5, claim_ttl_seconds)
        self._heartbeat_interval_seconds = max(0.1, heartbeat_interval_seconds)
        self._active_tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._poller_task: asyncio.Task[None] | None = None
        self._last_recovery_report: dict[str, Any] = {
            "source": "startup",
            "candidate_job_count": 0,
            "expired_lease_job_count": 0,
            "retried_job_count": 0,
            "scheduled_job_count": 0,
            "scheduled_job_ids": [],
            "last_run_at": None,
        }
        self._logger = get_logger("relationship_os.jobs.executor")

    async def start(self) -> None:
        async with self._lock:
            if self._poller_task is not None and not self._poller_task.done():
                return
            self._poller_task = asyncio.create_task(
                self._poll_loop(),
                name=f"job-poller:{self._worker_id}",
            )

    async def schedule_job(self, *, job_id: str) -> bool:
        async with self._lock:
            existing = self._active_tasks.get(job_id)
            if existing is not None and not existing.done():
                return False

        claimed = await self._job_service.claim_job(
            job_id=job_id,
            worker_id=self._worker_id,
            lease_ttl_seconds=self._claim_ttl_seconds,
        )
        if claimed is None:
            return False
        claim_token = claimed.get("claim_token")
        if not isinstance(claim_token, str) or not claim_token:
            return False

        async with self._lock:
            existing = self._active_tasks.get(job_id)
            if existing is not None and not existing.done():
                return False
            task = asyncio.create_task(
                self._run_job(job_id=job_id, claim_token=claim_token),
                name=f"job:{job_id}",
            )
            self._active_tasks[job_id] = task
            return True

    async def recover_jobs(
        self,
        *,
        source: str,
        include_failed_retries: bool,
    ) -> dict[str, Any]:
        candidate_jobs: list[dict[str, Any]] = []
        expired_lease_job_count = 0
        for status in RECOVERY_STATUSES:
            response = await self._job_service.list_jobs(status=status)
            for job in response["jobs"]:
                candidate_jobs.append(job)
                if bool(job.get("lease_is_expired")):
                    expired_lease_job_count += 1

        scheduled_job_ids: list[str] = []
        retried_job_ids: list[str] = []

        if include_failed_retries and self._auto_retry_failed_jobs:
            failed = await self._job_service.list_jobs(status="failed")
            for job in failed["jobs"]:
                if not bool(job.get("can_retry")):
                    continue
                retried = await self._job_service.retry_job_for_recovery(
                    job_id=str(job["job_id"])
                )
                retried_job_ids.append(str(retried["job_id"]))

        refreshed_candidates: list[dict[str, Any]] = []
        for status in RECOVERY_STATUSES:
            refreshed_candidates.extend(
                (await self._job_service.list_jobs(status=status))["jobs"]
            )
        for job in refreshed_candidates:
            job_id = str(job["job_id"])
            if await self.schedule_job(job_id=job_id):
                scheduled_job_ids.append(job_id)

        report = {
            "source": source,
            "candidate_job_count": len(candidate_jobs),
            "expired_lease_job_count": expired_lease_job_count,
            "retried_job_count": len(retried_job_ids),
            "scheduled_job_count": len(scheduled_job_ids),
            "scheduled_job_ids": scheduled_job_ids,
            "last_run_at": utc_now().isoformat(),
        }
        self._last_recovery_report = report
        if scheduled_job_ids or retried_job_ids or expired_lease_job_count:
            self._logger.info(
                "job_recovery_scheduled",
                worker_id=self._worker_id,
                source=source,
                candidate_job_count=report["candidate_job_count"],
                expired_lease_job_count=report["expired_lease_job_count"],
                retried_job_count=report["retried_job_count"],
                scheduled_job_count=report["scheduled_job_count"],
                scheduled_job_ids=scheduled_job_ids,
            )
        return report

    async def shutdown(self) -> None:
        async with self._lock:
            poller_task = self._poller_task
            if poller_task is not None:
                poller_task.cancel()

        if poller_task is not None:
            await asyncio.gather(poller_task, return_exceptions=True)

        async with self._lock:
            tasks = list(self._active_tasks.values())
            for task in tasks:
                task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        async with self._lock:
            self._active_tasks.clear()
            self._poller_task = None

    @property
    def is_running(self) -> bool:
        return self._poller_task is not None and not self._poller_task.done()

    async def get_runtime_state(self) -> dict[str, Any]:
        async with self._lock:
            active_job_ids = [
                job_id
                for job_id, task in self._active_tasks.items()
                if not task.done()
            ]
            poller_running = self._poller_task is not None and not self._poller_task.done()
        return {
            "worker_id": self._worker_id,
            "active_job_count": len(active_job_ids),
            "active_job_ids": sorted(active_job_ids),
            "auto_retry_failed_jobs": self._auto_retry_failed_jobs,
            "poll_interval_seconds": self._poll_interval_seconds,
            "claim_ttl_seconds": self._claim_ttl_seconds,
            "heartbeat_interval_seconds": self._heartbeat_interval_seconds,
            "poller_running": poller_running,
            "last_recovery_report": dict(self._last_recovery_report),
        }

    async def _run_job(self, *, job_id: str, claim_token: str) -> None:
        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(job_id=job_id, claim_token=claim_token),
            name=f"job-heartbeat:{job_id}",
        )
        try:
            await self._job_service.run_job(
                job_id=job_id,
                worker_id=self._worker_id,
                claim_token=claim_token,
            )
        except Exception as exc:
            self._logger.exception(
                "job_execution_failed",
                job_id=job_id,
                worker_id=self._worker_id,
                error=str(exc),
            )
        finally:
            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)
            async with self._lock:
                self._active_tasks.pop(job_id, None)

    async def _heartbeat_loop(self, *, job_id: str, claim_token: str) -> None:
        try:
            while True:
                renewed = await self._job_service.renew_job_lease(
                    job_id=job_id,
                    worker_id=self._worker_id,
                    claim_token=claim_token,
                    lease_ttl_seconds=self._claim_ttl_seconds,
                )
                if not renewed:
                    return
                await asyncio.sleep(self._heartbeat_interval_seconds)
        except asyncio.CancelledError:
            return

    async def _poll_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._poll_interval_seconds)
                await self.recover_jobs(source="poll", include_failed_retries=False)
        except asyncio.CancelledError:
            return
