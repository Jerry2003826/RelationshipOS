"""Lightweight HTTP client that talks to the RelationshipOS API."""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class TurnResult:
    session_id: str
    user_message: str
    assistant_response: str
    latency_ms: float
    raw: dict[str, Any] = field(default_factory=dict)


class RelationshipOSClient:
    """Synchronous wrapper around the sessions / turns REST API."""

    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 300.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._http = self._make_client()

    def _make_client(self) -> httpx.Client:
        api_key = (
            os.getenv("BENCHMARK_RELATIONSHIP_OS_API_KEY", "").strip()
            or os.getenv("RELATIONSHIP_OS_API_KEY", "").strip()
        )
        headers = {"X-API-Key": api_key} if api_key else None
        return httpx.Client(base_url=self._base, timeout=self._timeout, headers=headers)

    def _retry(self, fn: Any, check_status: bool = False) -> Any:
        for attempt in range(self.MAX_RETRIES):
            try:
                result = fn()
                if check_status and hasattr(result, "status_code") and result.status_code >= 500:
                    raise httpx.ReadError(f"Server error {result.status_code}")
                return result
            except (
                httpx.ReadError,
                httpx.ConnectError,
                httpx.RemoteProtocolError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ) as exc:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                wait = self.RETRY_DELAY * (attempt + 1)
                print(
                    f"    ⚠ 错误, {wait:.0f}s 后重试 ({attempt + 1}/{self.MAX_RETRIES}): {exc}",
                    flush=True,
                )
                time.sleep(wait)
                self._http.close()
                self._http = self._make_client()

    def create_session(
        self,
        session_id: str | None = None,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        tag = uuid.uuid4().hex[:6]
        sid = f"{session_id}-{tag}" if session_id else f"bench-{tag}"

        def _do() -> None:
            payload: dict[str, Any] = {"session_id": sid}
            if user_id:
                payload["user_id"] = user_id
            if metadata:
                payload["metadata"] = dict(metadata)
            r = self._http.post("/api/v1/sessions", json=payload)
            r.raise_for_status()

        self._retry(_do)
        return sid

    def send_turn(self, session_id: str, content: str) -> TurnResult:
        t0 = time.perf_counter()

        # Turn submission is not safely retryable: if the server keeps processing
        # after a client-side timeout, retrying the same POST can corrupt the
        # benchmark run with optimistic-concurrency collisions on the same stream.
        r = self._http.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={"content": content},
        )
        latency = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        data = r.json()
        return TurnResult(
            session_id=session_id,
            user_message=content,
            assistant_response=data.get("assistant_response", ""),
            latency_ms=latency,
            raw=data,
        )

    def list_sessions(self) -> list[str]:
        r = self._http.get("/api/v1/sessions")
        r.raise_for_status()
        return [s["session_id"] for s in r.json().get("sessions", [])]

    def idle(self, seconds: float) -> None:
        delay = max(0.0, float(seconds))
        if delay > 0:
            time.sleep(delay)

    def create_offline_consolidation_job(
        self,
        session_id: str,
        *,
        metadata: dict[str, Any] | None = None,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "session_id": session_id,
            "metadata": dict(metadata or {}),
        }
        if max_attempts is not None:
            payload["max_attempts"] = max_attempts
        response = self._http.post("/api/v1/jobs/offline-consolidation", json=payload)
        response.raise_for_status()
        return dict(response.json().get("job") or {})

    def get_job(self, job_id: str) -> dict[str, Any]:
        response = self._http.get(f"/api/v1/jobs/{job_id}")
        response.raise_for_status()
        return dict(response.json().get("job") or {})

    def wait_for_job(
        self,
        job_id: str,
        *,
        timeout_seconds: float = 120.0,
        poll_interval: float = 0.5,
    ) -> dict[str, Any]:
        deadline = time.time() + max(1.0, float(timeout_seconds))
        delay = max(0.05, float(poll_interval))
        last_job: dict[str, Any] | None = None
        while time.time() < deadline:
            job = self.get_job(job_id)
            last_job = job
            status = str(job.get("status") or "").strip()
            if status in {"completed", "failed"}:
                return job
            time.sleep(delay)
        raise TimeoutError(
            f"Job {job_id} did not finish within {timeout_seconds:.1f}s; last state was {last_job}"
        )

    def consolidate_session(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 120.0,
        poll_interval: float = 0.5,
        metadata: dict[str, Any] | None = None,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        job = self.create_offline_consolidation_job(
            session_id,
            metadata=metadata,
            max_attempts=max_attempts,
        )
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return job
        return self.wait_for_job(
            job_id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )

    def close(self) -> None:
        self._http.close()
