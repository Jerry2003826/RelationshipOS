import asyncio
import time

from fastapi.testclient import TestClient

from relationship_os.application.job_service import JobService
from relationship_os.core.config import Settings
from relationship_os.main import create_app


def _wait_for_job_status(
    client: TestClient,
    job_id: str,
    *,
    expected_status: str,
    attempts: int = 50,
    delay_seconds: float = 0.02,
) -> dict[str, object]:
    last_job: dict[str, object] | None = None
    for _ in range(attempts):
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        last_job = response.json()["job"]
        if last_job["status"] == expected_status:
            return last_job
        time.sleep(delay_seconds)
    raise AssertionError(
        f"Job {job_id} did not reach status {expected_status}; last state was {last_job}"
    )


def test_offline_consolidation_job_completes_and_updates_session_projection() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/v1/sessions/job-session/turns",
            json={"content": "我有点担心节奏，但还是想继续推进。"},
        )
        client.post(
            "/api/v1/sessions/job-session/turns",
            json={"content": "请继续给我一个更稳一点的下一步。"},
        )

        create_response = client.post(
            "/api/v1/jobs/offline-consolidation",
            json={"session_id": "job-session"},
        )
        assert create_response.status_code == 202
        queued_job = create_response.json()["job"]
        assert queued_job["job_type"] == "offline_consolidation"
        assert queued_job["status"] == "queued"
        assert queued_job["attempt_count"] == 0
        assert queued_job["max_attempts"] == 2

        completed_job = _wait_for_job_status(
            client,
            str(queued_job["job_id"]),
            expected_status="completed",
        )

        list_response = client.get("/api/v1/jobs?session_id=job-session")
        assert list_response.status_code == 200
        body = list_response.json()
        assert body["job_count"] == 1
        assert body["jobs"][0]["job_id"] == queued_job["job_id"]

        session_response = client.get("/api/v1/sessions/job-session")
        assert session_response.status_code == 200
        session_state = session_response.json()["state"]
        assert session_state["last_background_job"]["status"] == "completed"
        assert session_state["offline_consolidation"]["report"]["summary"]
        assert session_state["latest_snapshot"]["snapshot_id"]
        assert session_state["archive_status"]["archived"] is True

        snapshot_response = client.get("/api/v1/sessions/job-session/snapshots")
        assert snapshot_response.status_code == 200
        snapshots_state = snapshot_response.json()["state"]
        assert snapshots_state["snapshot_count"] == 1
        assert snapshots_state["snapshots"][0]["archive_candidate"] is True

        archive_response = client.get("/api/v1/runtime/archives")
        assert archive_response.status_code == 200
        archive_body = archive_response.json()
        assert archive_body["archive_count"] >= 1
        assert archive_body["sessions"][0]["session_id"] == "job-session"

        audit_response = client.get("/api/v1/runtime/audit/job-session")
        assert audit_response.status_code == 200
        audit_body = audit_response.json()
        assert audit_body["fingerprint"]
        assert audit_body["event_type_counts"]["system.session_snapshot.created"] == 1
        assert audit_body["archive_status"]["archived"] is True

        trace_response = client.get("/api/v1/runtime/trace/job-session")
        assert trace_response.status_code == 200
        trace_event_types = {event["event_type"] for event in trace_response.json()["trace"]}
        assert "system.background_job.claimed" in trace_event_types
        assert "system.background_job.started" in trace_event_types
        assert "system.offline_consolidation.completed" in trace_event_types
        assert "system.session_snapshot.created" in trace_event_types
        assert "system.session.archived" in trace_event_types

        drives_response = client.get("/api/v1/entity/drives")
        assert drives_response.status_code == 200
        drives_state = drives_response.json()
        assert drives_state["source"] in {"turn_runtime", "offline_consolidation"}

        goals_response = client.get("/api/v1/entity/goals")
        assert goals_response.status_code == 200
        goals_state = goals_response.json()
        assert "goal_digest" in goals_state
        assert goals_state["goal_digest"]

        narrative_response = client.get("/api/v1/entity/narrative")
        assert narrative_response.status_code == 200
        narrative_state = narrative_response.json()
        assert "离线整理后" in narrative_state["summary"]
        assert any(
            entry.get("source") == "offline_consolidation"
            for entry in narrative_state["recent_entries"]
        )

        world_response = client.get("/api/v1/entity/world-state")
        assert world_response.status_code == 200
        world_state = world_response.json()
        assert world_state["environment_appraisal"]["focus"] in {"rest", "organizational"}
        assert int(world_state["tasks"]["pending_count"]) >= 1

    assert completed_job["status"] == "completed"
    assert completed_job["attempt_count"] == 1
    assert completed_job["can_retry"] is False
    assert completed_job["last_worker_id"]
    assert completed_job["claim_owner"] is None
    assert completed_job["claim_token"] is None
    assert completed_job["result"]["session_id"] == "job-session"
    assert completed_job["result"]["report"]["source_turn_count"] == 2
    assert completed_job["result"]["report"]["recommended_actions"]
    assert completed_job["result"]["entity_consolidation"]["narrative_summary"]
    assert completed_job["result"]["entity_consolidation"]["top_goal_titles"]
    assert completed_job["result"]["entity_consolidation"]["world_focus"] in {
        "rest",
        "organizational",
    }


def test_offline_consolidation_job_returns_404_for_missing_session() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/jobs/offline-consolidation",
            json={"session_id": "missing-session"},
        )

        assert response.status_code == 404


def test_failed_job_can_be_retried_after_recovery() -> None:
    app = create_app()

    class FailingEvaluationService:
        async def evaluate_session(self, *, session_id: str):  # type: ignore[no-untyped-def]
            raise RuntimeError(f"evaluation unavailable for {session_id}")

    original_evaluation_service = app.state.container.job_service._evaluation_service
    app.state.container.job_service._evaluation_service = FailingEvaluationService()

    with TestClient(app) as client:
        client.post(
            "/api/v1/sessions/retry-session/turns",
            json={"content": "Please keep the session alive while systems recover."},
        )

        create_response = client.post(
            "/api/v1/jobs/offline-consolidation",
            json={"session_id": "retry-session", "max_attempts": 2},
        )
        assert create_response.status_code == 202
        job_id = create_response.json()["job"]["job_id"]

        failed_job = _wait_for_job_status(
            client,
            str(job_id),
            expected_status="failed",
        )
        assert failed_job["attempt_count"] == 1
        assert failed_job["can_retry"] is True

        app.state.container.job_service._evaluation_service = original_evaluation_service

        retry_response = client.post(f"/api/v1/jobs/{job_id}/retry")
        assert retry_response.status_code == 202
        retried_job = retry_response.json()["job"]
        assert retried_job["status"] == "queued"

        completed_job = _wait_for_job_status(
            client,
            str(job_id),
            expected_status="completed",
        )

        trace_response = client.get("/api/v1/runtime/trace/retry-session")
        trace_event_types = [event["event_type"] for event in trace_response.json()["trace"]]
        assert "system.background_job.failed" in trace_event_types
        assert "system.background_job.requeued" in trace_event_types
        assert trace_event_types.count("system.background_job.started") == 2

    assert completed_job["status"] == "completed"
    assert completed_job["attempt_count"] == 2
    assert completed_job["last_worker_id"]
    assert completed_job["claim_owner"] is None
    assert completed_job["can_retry"] is False


def test_job_state_can_be_rebuilt_from_event_stream() -> None:
    app = create_app()
    with TestClient(app) as client:
        client.post(
            "/api/v1/sessions/persisted-job/turns",
            json={"content": "Archive this when the review is complete."},
        )
        create_response = client.post(
            "/api/v1/jobs/offline-consolidation",
            json={"session_id": "persisted-job"},
        )
        job_id = create_response.json()["job"]["job_id"]
        _wait_for_job_status(client, str(job_id), expected_status="completed")

    rebuilt_job_service = JobService(
        stream_service=app.state.container.stream_service,
        evaluation_service=app.state.container.evaluation_service,
        default_max_attempts=app.state.container.settings.job_max_attempts,
    )
    rebuilt_job = asyncio.run(rebuilt_job_service.get_job(job_id=job_id))

    assert rebuilt_job["job_id"] == job_id
    assert rebuilt_job["status"] == "completed"
    assert rebuilt_job["last_worker_id"]
    assert rebuilt_job["claim_owner"] is None
    assert rebuilt_job["result"]["snapshot"]["snapshot_id"]


def test_job_executor_recovers_queued_job_on_startup() -> None:
    app = create_app()
    asyncio.run(
        app.state.container.runtime_service.process_turn(
            session_id="recover-queued-session",
            user_message="Please resume the queued consolidation after startup.",
        )
    )
    queued_job = asyncio.run(
        app.state.container.job_service.create_offline_consolidation_job(
            session_id="recover-queued-session"
        )
    )

    with TestClient(app) as client:
        completed_job = _wait_for_job_status(
            client,
            str(queued_job["job_id"]),
            expected_status="completed",
        )
        overview = client.get("/api/v1/runtime").json()

    assert completed_job["status"] == "completed"
    assert overview["job_runtime"]["last_recovery_report"]["candidate_job_count"] >= 1
    assert (
        str(queued_job["job_id"])
        in overview["job_runtime"]["last_recovery_report"]["scheduled_job_ids"]
    )


def test_job_executor_retries_failed_job_on_startup() -> None:
    app = create_app()
    asyncio.run(
        app.state.container.runtime_service.process_turn(
            session_id="recover-failed-session",
            user_message="Please recover the failed consolidation automatically.",
        )
    )
    queued_job = asyncio.run(
        app.state.container.job_service.create_offline_consolidation_job(
            session_id="recover-failed-session",
            max_attempts=2,
        )
    )

    class FailingEvaluationService:
        async def evaluate_session(self, *, session_id: str):  # type: ignore[no-untyped-def]
            raise RuntimeError(f"temporary failure for {session_id}")

    original_evaluation_service = app.state.container.job_service._evaluation_service
    app.state.container.job_service._evaluation_service = FailingEvaluationService()
    asyncio.run(app.state.container.job_service.run_job(job_id=str(queued_job["job_id"])))
    app.state.container.job_service._evaluation_service = original_evaluation_service

    with TestClient(app) as client:
        completed_job = _wait_for_job_status(
            client,
            str(queued_job["job_id"]),
            expected_status="completed",
        )
        overview = client.get("/api/v1/runtime").json()

    assert completed_job["attempt_count"] == 2
    assert overview["job_runtime"]["last_recovery_report"]["retried_job_count"] >= 1


def test_job_executor_poll_loop_picks_up_jobs_created_outside_request_flow() -> None:
    app = create_app()
    with TestClient(app) as client:
        client.post(
            "/api/v1/sessions/poll-loop-session/turns",
            json={"content": "Please let the background worker notice this queued task."},
        )
        queued_job = asyncio.run(
            app.state.container.job_service.create_offline_consolidation_job(
                session_id="poll-loop-session"
            )
        )
        completed_job = _wait_for_job_status(
            client,
            str(queued_job["job_id"]),
            expected_status="completed",
            attempts=100,
        )
        overview = client.get("/api/v1/runtime").json()

    assert completed_job["status"] == "completed"
    assert completed_job["last_worker_id"] == overview["job_runtime"]["worker_id"]


def test_job_executor_emits_heartbeat_for_slow_job() -> None:
    app = create_app(
        Settings(
            job_claim_ttl_seconds=0.2,
            job_heartbeat_interval_seconds=0.02,
            job_poll_interval_seconds=0.05,
        )
    )

    class SlowEvaluationService:
        async def evaluate_session(self, *, session_id: str):  # type: ignore[no-untyped-def]
            await asyncio.sleep(0.08)
            return await original_evaluation_service.evaluate_session(session_id=session_id)

    original_evaluation_service = app.state.container.job_service._evaluation_service
    slow_service = SlowEvaluationService()
    app.state.container.job_service._evaluation_service = slow_service

    with TestClient(app) as client:
        client.post(
            "/api/v1/sessions/heartbeat-session/turns",
            json={"content": "Please keep this job alive long enough to heartbeat."},
        )
        create_response = client.post(
            "/api/v1/jobs/offline-consolidation",
            json={"session_id": "heartbeat-session"},
        )
        job_id = create_response.json()["job"]["job_id"]
        completed_job = _wait_for_job_status(
            client,
            str(job_id),
            expected_status="completed",
            attempts=120,
        )
        trace_response = client.get("/api/v1/runtime/trace/heartbeat-session")
        trace_event_types = [event["event_type"] for event in trace_response.json()["trace"]]

    assert completed_job["status"] == "completed"
    assert "system.background_job.heartbeat" in trace_event_types


def test_job_executor_reclaims_expired_claim_on_startup() -> None:
    settings = Settings(
        job_claim_ttl_seconds=0.05,
        job_heartbeat_interval_seconds=0.02,
        job_poll_interval_seconds=0.05,
    )
    app = create_app(settings)
    asyncio.run(
        app.state.container.runtime_service.process_turn(
            session_id="expired-claim-session",
            user_message="Please reclaim this stalled job after startup.",
        )
    )
    queued_job = asyncio.run(
        app.state.container.job_service.create_offline_consolidation_job(
            session_id="expired-claim-session"
        )
    )
    claimed_job = asyncio.run(
        app.state.container.job_service.claim_job(
            job_id=str(queued_job["job_id"]),
            worker_id="stale-worker",
            lease_ttl_seconds=settings.job_claim_ttl_seconds,
        )
    )
    assert claimed_job is not None
    time.sleep(0.06)

    with TestClient(app) as client:
        completed_job = _wait_for_job_status(
            client,
            str(queued_job["job_id"]),
            expected_status="completed",
        )
        trace_response = client.get("/api/v1/runtime/trace/expired-claim-session")
        trace_event_types = [event["event_type"] for event in trace_response.json()["trace"]]
        overview = client.get("/api/v1/runtime").json()

    assert completed_job["status"] == "completed"
    assert completed_job["last_worker_id"] == overview["job_runtime"]["worker_id"]
    assert "system.background_job.lease_expired" in trace_event_types
    assert "system.background_job.claimed" in trace_event_types
