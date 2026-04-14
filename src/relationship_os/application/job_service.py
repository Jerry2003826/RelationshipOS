from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from relationship_os.application.analyzers import (
    build_archive_status,
    build_offline_consolidation_report,
    build_session_snapshot,
)
from relationship_os.application.evaluation_service import EvaluationService
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_store import OptimisticConcurrencyError
from relationship_os.domain.event_types import (
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_STARTED,
    OFFLINE_CONSOLIDATION_COMPLETED,
    SESSION_ARCHIVED,
    SESSION_SNAPSHOT_CREATED,
)
from relationship_os.domain.events import NewEvent, StoredEvent, utc_now

JOB_EVENT_TYPES = {
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_STARTED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
}
LEASED_JOB_STATUSES = {"claimed", "running"}


class JobNotFoundError(LookupError):
    """Raised when a job cannot be found by identifier."""


class SessionNotFoundError(LookupError):
    """Raised when a background job targets an unknown session."""


class JobRetryNotAllowedError(RuntimeError):
    """Raised when a job cannot be retried from its current status."""


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _build_lease_expiry(*, ttl_seconds: float) -> str:
    ttl = max(0.1, ttl_seconds)
    return (utc_now() + timedelta(seconds=ttl)).isoformat()


@dataclass(slots=True)
class JobRecord:
    job_id: str
    job_type: str
    session_id: str
    status: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    attempt_count: int = 0
    max_attempts: int = 1
    last_worker_id: str | None = None
    claim_owner: str | None = None
    claim_token: str | None = None
    claimed_at: str | None = None
    last_heartbeat_at: str | None = None
    lease_expires_at: str | None = None

    @property
    def can_retry(self) -> bool:
        return self.status == "failed" and self.attempt_count < self.max_attempts

    def lease_is_expired(self, *, now: datetime | None = None) -> bool:
        if self.status not in LEASED_JOB_STATUSES:
            return False
        expiry = _parse_datetime(self.lease_expires_at)
        if expiry is None:
            return True
        return expiry <= (now or utc_now())

    def can_be_claimed(self, *, now: datetime | None = None) -> bool:
        return self.status == "queued" or self.lease_is_expired(now=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata),
            "result": self.result,
            "error": self.error,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "last_worker_id": self.last_worker_id,
            "claim_owner": self.claim_owner,
            "claim_token": self.claim_token,
            "claimed_at": self.claimed_at,
            "last_heartbeat_at": self.last_heartbeat_at,
            "lease_expires_at": self.lease_expires_at,
            "lease_is_expired": self.lease_is_expired(),
            "can_retry": self.can_retry,
        }


@dataclass(slots=True)
class _OfflineConsolidationResult:
    completed_at: str
    evaluation: dict[str, Any]
    report: Any
    snapshot: Any
    result: dict[str, Any]
    archive_status: Any


class JobService:
    def __init__(
        self,
        *,
        stream_service: StreamService,
        evaluation_service: EvaluationService,
        default_max_attempts: int,
        runtime_projector_version: str = "v2",
        entity_service: Any | None = None,
    ) -> None:
        self._stream_service = stream_service
        self._evaluation_service = evaluation_service
        self._default_max_attempts = max(1, default_max_attempts)
        self._runtime_projector_version = runtime_projector_version
        self._entity_service = entity_service

    async def create_offline_consolidation_job(
        self,
        *,
        session_id: str,
        metadata: dict[str, Any] | None = None,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        session_events = await self._stream_service.read_stream(stream_id=session_id)
        if not session_events:
            raise SessionNotFoundError(f"Session {session_id} does not exist")

        created_at = utc_now().isoformat()
        job_id = f"job-{uuid4().hex[:12]}"
        scheduled_payload = {
            "job_id": job_id,
            "job_type": "offline_consolidation",
            "session_id": session_id,
            "status": "queued",
            "created_at": created_at,
            "metadata": dict(metadata or {}),
            "attempt_count": 0,
            "max_attempts": max(1, max_attempts or self._default_max_attempts),
        }
        await self._append_session_events(
            session_id=session_id,
            events=[
                NewEvent(
                    event_type=BACKGROUND_JOB_SCHEDULED,
                    payload=scheduled_payload,
                )
            ],
        )
        return await self.get_job(job_id=job_id)

    async def retry_job(self, *, job_id: str) -> dict[str, Any]:
        return await self._requeue_job(job_id=job_id, reason="manual_retry")

    async def retry_job_for_recovery(self, *, job_id: str) -> dict[str, Any]:
        return await self._requeue_job(job_id=job_id, reason="startup_recovery")

    async def claim_job(
        self,
        *,
        job_id: str,
        worker_id: str,
        lease_ttl_seconds: float,
    ) -> dict[str, Any] | None:
        now = utc_now()
        record = await self._get_job_record(job_id)
        if not record.can_be_claimed(now=now):
            return None

        current_record, current_version = await self._get_job_record_for_session(
            session_id=record.session_id,
            job_id=job_id,
        )
        if current_record is None or not current_record.can_be_claimed(now=now):
            return None

        claim_token = uuid4().hex
        lease_expires_at = _build_lease_expiry(ttl_seconds=lease_ttl_seconds)
        events: list[NewEvent] = []
        if current_record.status in LEASED_JOB_STATUSES:
            events.append(
                NewEvent(
                    event_type=BACKGROUND_JOB_LEASE_EXPIRED,
                    payload={
                        "job_id": current_record.job_id,
                        "job_type": current_record.job_type,
                        "session_id": current_record.session_id,
                        "status": "queued",
                        "created_at": current_record.created_at,
                        "metadata": dict(current_record.metadata),
                        "attempt_count": current_record.attempt_count,
                        "max_attempts": current_record.max_attempts,
                        "expired_at": now.isoformat(),
                        "previous_status": current_record.status,
                        "previous_worker_id": current_record.claim_owner,
                        "previous_claim_token": current_record.claim_token,
                        "lease_expires_at": current_record.lease_expires_at,
                    },
                )
            )
        events.append(
            NewEvent(
                event_type=BACKGROUND_JOB_CLAIMED,
                payload={
                    "job_id": current_record.job_id,
                    "job_type": current_record.job_type,
                    "session_id": current_record.session_id,
                    "status": "claimed",
                    "created_at": current_record.created_at,
                    "metadata": dict(current_record.metadata),
                    "attempt_count": current_record.attempt_count,
                    "max_attempts": current_record.max_attempts,
                    "claim_owner": worker_id,
                    "claim_token": claim_token,
                    "claimed_at": now.isoformat(),
                    "lease_expires_at": lease_expires_at,
                    "previous_status": current_record.status,
                },
            )
        )
        try:
            await self._append_session_events(
                session_id=current_record.session_id,
                events=events,
                expected_version=current_version,
            )
        except OptimisticConcurrencyError:
            return None
        return await self.get_job(job_id=job_id)

    async def renew_job_lease(
        self,
        *,
        job_id: str,
        worker_id: str,
        claim_token: str,
        lease_ttl_seconds: float,
    ) -> bool:
        record = await self._get_job_record(job_id)
        if (
            record.status not in LEASED_JOB_STATUSES
            or record.claim_owner != worker_id
            or record.claim_token != claim_token
        ):
            return False

        current_record, current_version = await self._get_job_record_for_session(
            session_id=record.session_id,
            job_id=job_id,
        )
        if (
            current_record is None
            or current_record.status not in LEASED_JOB_STATUSES
            or current_record.claim_owner != worker_id
            or current_record.claim_token != claim_token
        ):
            return False

        now = utc_now()
        try:
            await self._append_session_events(
                session_id=current_record.session_id,
                expected_version=current_version,
                events=[
                    NewEvent(
                        event_type=BACKGROUND_JOB_HEARTBEAT,
                        payload={
                            "job_id": current_record.job_id,
                            "job_type": current_record.job_type,
                            "session_id": current_record.session_id,
                            "status": current_record.status,
                            "created_at": current_record.created_at,
                            "metadata": dict(current_record.metadata),
                            "attempt_count": current_record.attempt_count,
                            "max_attempts": current_record.max_attempts,
                            "worker_id": worker_id,
                            "claim_owner": worker_id,
                            "claim_token": claim_token,
                            "heartbeat_at": now.isoformat(),
                            "lease_expires_at": _build_lease_expiry(
                                ttl_seconds=lease_ttl_seconds
                            ),
                        },
                    )
                ],
            )
        except OptimisticConcurrencyError:
            return False
        return True

    async def run_job(
        self,
        *,
        job_id: str,
        worker_id: str | None = None,
        claim_token: str | None = None,
    ) -> dict[str, Any]:
        record = await self._get_job_record(job_id)
        if record.status not in {"queued", "claimed"}:
            return record.to_dict()
        if claim_token is not None and (
            record.claim_owner != worker_id or record.claim_token != claim_token
        ):
            return record.to_dict()

        attempt_count = record.attempt_count + 1
        started_at = utc_now().isoformat()
        await self._append_session_events(
            session_id=record.session_id,
            events=[
                self._build_job_started_event(
                    record=record,
                    attempt_count=attempt_count,
                    started_at=started_at,
                    worker_id=worker_id,
                )
            ],
        )

        try:
            consolidation = await self._run_offline_consolidation(record=record)
            await self._append_session_events(
                session_id=record.session_id,
                events=self._build_job_completion_events(
                    record=record,
                    attempt_count=attempt_count,
                    worker_id=worker_id,
                    consolidation=consolidation,
                ),
            )
        except Exception as exc:
            completed_at = utc_now().isoformat()
            await self._append_session_events(
                session_id=record.session_id,
                events=[
                    self._build_job_failed_event(
                        record=record,
                        attempt_count=attempt_count,
                        worker_id=worker_id,
                        completed_at=completed_at,
                        exc=exc,
                    )
                ],
            )

        return await self.get_job(job_id=job_id)

    def _build_job_started_event(
        self,
        *,
        record: JobRecord,
        attempt_count: int,
        started_at: str,
        worker_id: str | None,
    ) -> NewEvent:
        return NewEvent(
            event_type=BACKGROUND_JOB_STARTED,
            payload={
                "job_id": record.job_id,
                "job_type": record.job_type,
                "session_id": record.session_id,
                "status": "running",
                "started_at": started_at,
                "created_at": record.created_at,
                "metadata": dict(record.metadata),
                "attempt_count": attempt_count,
                "max_attempts": record.max_attempts,
                "worker_id": worker_id,
                "claim_owner": record.claim_owner,
                "claim_token": record.claim_token,
                "claimed_at": record.claimed_at,
                "lease_expires_at": record.lease_expires_at,
            },
        )

    async def _run_offline_consolidation(
        self,
        *,
        record: JobRecord,
    ) -> _OfflineConsolidationResult:
        runtime_projection = await self._stream_service.project_stream(
            stream_id=record.session_id,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )
        evaluation = await self._evaluation_service.evaluate_session(
            session_id=record.session_id
        )
        report = build_offline_consolidation_report(
            session_id=record.session_id,
            runtime_projection=runtime_projection,
            evaluation=evaluation,
        )
        completed_at = utc_now().isoformat()
        snapshot = build_session_snapshot(
            snapshot_id=f"snapshot-{uuid4().hex[:12]}",
            created_at=completed_at,
            source_job_id=record.job_id,
            evaluation_summary=evaluation["summary"],
            report=report,
            fingerprint=self._stream_service.fingerprint_value(
                {
                    "runtime_state": runtime_projection["state"],
                    "evaluation_summary": evaluation["summary"],
                    "report": asdict(report),
                }
            ),
        )
        result = {
            "job_id": record.job_id,
            "job_type": record.job_type,
            "session_id": record.session_id,
            "completed_at": completed_at,
            "report": asdict(report),
            "snapshot": asdict(snapshot),
            "evaluation_summary": evaluation["summary"],
        }
        archive_status = build_archive_status(
            created_at=completed_at,
            snapshot=snapshot,
            report=report,
        )
        entity_consolidation: dict[str, Any] | None = None
        if self._entity_service is not None:
            entity_consolidation = await self._entity_service.consolidate_offline_state(
                session_id=record.session_id,
                report_summary=report.summary,
                recommended_actions=list(report.recommended_actions),
                evaluation_summary=evaluation["summary"],
            )
            result["entity_consolidation"] = entity_consolidation
        return _OfflineConsolidationResult(
            completed_at=completed_at,
            evaluation=evaluation,
            report=report,
            snapshot=snapshot,
            result=result,
            archive_status=archive_status,
        )

    def _build_job_completion_events(
        self,
        *,
        record: JobRecord,
        attempt_count: int,
        worker_id: str | None,
        consolidation: _OfflineConsolidationResult,
    ) -> list[NewEvent]:
        session_events = [
            NewEvent(
                event_type=OFFLINE_CONSOLIDATION_COMPLETED,
                payload=consolidation.result,
            ),
            NewEvent(
                event_type=SESSION_SNAPSHOT_CREATED,
                payload=asdict(consolidation.snapshot),
            ),
        ]
        if consolidation.archive_status.archived:
            session_events.append(
                NewEvent(
                    event_type=SESSION_ARCHIVED,
                    payload=asdict(consolidation.archive_status),
                )
            )
        session_events.append(
            NewEvent(
                event_type=BACKGROUND_JOB_COMPLETED,
                payload={
                    "job_id": record.job_id,
                    "job_type": record.job_type,
                    "session_id": record.session_id,
                    "status": "completed",
                    "created_at": record.created_at,
                    "metadata": dict(record.metadata),
                    "attempt_count": attempt_count,
                    "max_attempts": record.max_attempts,
                    "completed_at": consolidation.completed_at,
                    "worker_id": worker_id,
                    "claim_owner": record.claim_owner,
                    "claim_token": record.claim_token,
                    "result": consolidation.result,
                },
            )
        )
        return session_events

    def _build_job_failed_event(
        self,
        *,
        record: JobRecord,
        attempt_count: int,
        worker_id: str | None,
        completed_at: str,
        exc: Exception,
    ) -> NewEvent:
        return NewEvent(
            event_type=BACKGROUND_JOB_FAILED,
            payload={
                "job_id": record.job_id,
                "job_type": record.job_type,
                "session_id": record.session_id,
                "status": "failed",
                "created_at": record.created_at,
                "metadata": dict(record.metadata),
                "attempt_count": attempt_count,
                "max_attempts": record.max_attempts,
                "completed_at": completed_at,
                "worker_id": worker_id,
                "claim_owner": record.claim_owner,
                "claim_token": record.claim_token,
                "error": {
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
            },
        )

    async def get_job(self, *, job_id: str) -> dict[str, Any]:
        return (await self._get_job_record(job_id)).to_dict()

    async def list_jobs(
        self,
        *,
        status: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        records = await self._list_job_records()
        filtered = [
            record.to_dict()
            for record in records
            if (status is None or record.status == status)
            and (session_id is None or record.session_id == session_id)
        ]
        filtered.sort(key=lambda item: str(item["created_at"]), reverse=True)
        return {
            "job_count": len(filtered),
            "jobs": filtered,
        }

    async def _requeue_job(
        self,
        *,
        job_id: str,
        reason: str,
    ) -> dict[str, Any]:
        record = await self._get_job_record(job_id)
        if record.status != "failed":
            raise JobRetryNotAllowedError(
                f"Job {job_id} is {record.status} and cannot be retried"
            )
        if not record.can_retry:
            raise JobRetryNotAllowedError(
                "Job "
                f"{job_id} exhausted retry budget "
                f"({record.attempt_count}/{record.max_attempts})"
            )

        requeued_at = utc_now().isoformat()
        await self._append_session_events(
            session_id=record.session_id,
            events=[
                NewEvent(
                    event_type=BACKGROUND_JOB_REQUEUED,
                    payload={
                        "job_id": record.job_id,
                        "job_type": record.job_type,
                        "session_id": record.session_id,
                        "status": "queued",
                        "created_at": record.created_at,
                        "metadata": dict(record.metadata),
                        "attempt_count": record.attempt_count,
                        "max_attempts": record.max_attempts,
                        "requeued_at": requeued_at,
                        "next_attempt": record.attempt_count + 1,
                        "requeue_reason": reason,
                    },
                )
            ],
        )
        return await self.get_job(job_id=job_id)

    async def _get_job_record(self, job_id: str) -> JobRecord:
        records = await self._list_job_records()
        for record in records:
            if record.job_id == job_id:
                return record
        raise JobNotFoundError(f"Job {job_id} does not exist")

    async def _get_job_record_for_session(
        self,
        *,
        session_id: str,
        job_id: str,
    ) -> tuple[JobRecord | None, int]:
        session_events = await self._stream_service.read_stream(stream_id=session_id)
        records = self._rebuild_job_records(session_events)
        return records.get(job_id), len(session_events)

    async def _list_job_records(self) -> list[JobRecord]:
        events = await self._stream_service.read_all_events()
        records = self._rebuild_job_records(events)
        return sorted(records.values(), key=lambda item: item.created_at, reverse=True)

    def _rebuild_job_records(
        self,
        events: list[StoredEvent],
    ) -> dict[str, JobRecord]:
        jobs: dict[str, JobRecord] = {}
        for event in events:
            if event.event_type not in JOB_EVENT_TYPES:
                continue
            job_id = str(event.payload.get("job_id", "")).strip()
            if not job_id:
                continue

            existing = jobs.get(job_id)
            if existing is None:
                existing = JobRecord(
                    job_id=job_id,
                    job_type=str(event.payload.get("job_type", "unknown")),
                    session_id=str(event.payload.get("session_id", event.stream_id)),
                    status=str(event.payload.get("status", "unknown")),
                    created_at=str(
                        event.payload.get("created_at", event.occurred_at.isoformat())
                    ),
                    metadata=dict(event.payload.get("metadata", {})),
                    max_attempts=int(
                        event.payload.get("max_attempts", self._default_max_attempts)
                    ),
                )
                jobs[job_id] = existing

            self._apply_job_event(existing, event)
        return jobs

    def _apply_job_event(self, record: JobRecord, event: StoredEvent) -> None:
        payload = event.payload
        if "job_type" in payload:
            record.job_type = str(payload["job_type"])
        if "session_id" in payload:
            record.session_id = str(payload["session_id"])
        if "created_at" in payload:
            record.created_at = str(payload["created_at"])
        if "metadata" in payload and isinstance(payload["metadata"], dict):
            record.metadata = dict(payload["metadata"])
        if "max_attempts" in payload:
            record.max_attempts = max(1, int(payload["max_attempts"]))
        if "worker_id" in payload and payload["worker_id"] is not None:
            record.last_worker_id = str(payload["worker_id"])
        if "claim_owner" in payload and payload["claim_owner"] is not None:
            record.claim_owner = str(payload["claim_owner"])
        if "claim_token" in payload and payload["claim_token"] is not None:
            record.claim_token = str(payload["claim_token"])
        if "lease_expires_at" in payload:
            record.lease_expires_at = payload["lease_expires_at"]

        if event.event_type in {BACKGROUND_JOB_SCHEDULED, BACKGROUND_JOB_REQUEUED}:
            record.status = "queued"
            record.started_at = None
            record.completed_at = None
            record.error = None
            record.result = None
            record.claim_owner = None
            record.claim_token = None
            record.claimed_at = None
            record.last_heartbeat_at = None
            record.lease_expires_at = None
            return

        if event.event_type == BACKGROUND_JOB_CLAIMED:
            record.status = "claimed"
            record.claim_owner = payload.get("claim_owner")
            record.claim_token = payload.get("claim_token")
            record.claimed_at = payload.get("claimed_at")
            record.last_heartbeat_at = None
            record.lease_expires_at = payload.get("lease_expires_at")
            return

        if event.event_type == BACKGROUND_JOB_HEARTBEAT:
            record.claim_owner = payload.get("claim_owner") or record.claim_owner
            record.claim_token = payload.get("claim_token") or record.claim_token
            record.last_heartbeat_at = payload.get("heartbeat_at")
            record.lease_expires_at = payload.get("lease_expires_at")
            return

        if event.event_type == BACKGROUND_JOB_LEASE_EXPIRED:
            record.status = "queued"
            record.claim_owner = None
            record.claim_token = None
            record.claimed_at = None
            record.last_heartbeat_at = None
            record.lease_expires_at = None
            return

        if event.event_type == BACKGROUND_JOB_STARTED:
            record.status = "running"
            record.started_at = str(payload.get("started_at", event.occurred_at.isoformat()))
            record.attempt_count = int(
                payload.get("attempt_count", record.attempt_count + 1)
            )
            record.error = None
            record.claimed_at = payload.get("claimed_at", record.claimed_at)
            record.lease_expires_at = payload.get(
                "lease_expires_at",
                record.lease_expires_at,
            )
            return

        if event.event_type == BACKGROUND_JOB_COMPLETED:
            record.status = "completed"
            record.completed_at = str(payload.get("completed_at", event.occurred_at.isoformat()))
            record.attempt_count = int(payload.get("attempt_count", record.attempt_count))
            record.result = payload.get("result")
            record.error = None
            record.claim_owner = None
            record.claim_token = None
            record.claimed_at = None
            record.last_heartbeat_at = None
            record.lease_expires_at = None
            return

        if event.event_type == BACKGROUND_JOB_FAILED:
            record.status = "failed"
            record.completed_at = str(payload.get("completed_at", event.occurred_at.isoformat()))
            record.attempt_count = int(payload.get("attempt_count", record.attempt_count))
            record.error = payload.get("error")
            record.result = None
            record.claim_owner = None
            record.claim_token = None
            record.claimed_at = None
            record.last_heartbeat_at = None
            record.lease_expires_at = None

    async def _append_session_events(
        self,
        *,
        session_id: str,
        events: list[NewEvent],
        expected_version: int | None = None,
    ) -> None:
        await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=expected_version,
            events=events,
        )
