from fastapi.testclient import TestClient

from relationship_os.domain.llm import LLMResponse
from relationship_os.main import create_app


def test_console_home_renders_control_room_shell() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/console")

    assert response.status_code == 200
    assert "RelationshipOS Control Room" in response.text
    assert 'id="console-overview"' in response.text
    assert 'id="console-evaluations"' in response.text
    assert 'id="console-scenarios"' in response.text
    assert "htmx.org@1.9.12" in response.text
    assert "alpinejs@3.14.1" in response.text
    assert "new WebSocket" in response.text


def test_console_session_detail_fragment_renders_runtime_panels() -> None:
    with TestClient(create_app()) as client:
        turn_response = client.post(
            "/api/v1/sessions/console-session/turns",
            json={"content": "Please help me keep this plan calm and steady."},
        )
        assert turn_response.status_code == 201

        response = client.get(
            "/api/v1/console/fragments/session-detail",
            params={"session_id": "console-session"},
        )

    assert response.status_code == 200
    assert "console-session" in response.text
    assert "Strategy & Audit" in response.text
    assert "Relationship & Memory" in response.text
    assert "Replay Snapshot" in response.text
    assert "Event Ledger" in response.text
    assert "Recent Transcript" in response.text
    assert "Recent Trace" in response.text


def test_console_session_detail_can_switch_projection_inspector() -> None:
    with TestClient(create_app()) as client:
        turn_response = client.post(
            "/api/v1/sessions/console-projection/turns",
            json={"content": "Please remember that I want the plan to stay gentle."},
        )
        assert turn_response.status_code == 201

        response = client.get(
            "/api/v1/console/fragments/session-detail",
            params={
                "session_id": "console-projection",
                "projector_name": "session-memory",
                "version": "v1",
            },
        )

    assert response.status_code == 200
    assert "Projection Inspector" in response.text
    assert "Selected Projector" in response.text
    assert "session-memory" in response.text
    assert "working_memory" in response.text


def test_console_fragments_render_jobs_without_listing_job_streams_as_sessions() -> None:
    with TestClient(create_app()) as client:
        turn_response = client.post(
            "/api/v1/sessions/console-jobs/turns",
            json={"content": "Keep this review moving, then archive it when stable."},
        )
        assert turn_response.status_code == 201

        create_job_response = client.post(
            "/api/v1/jobs/offline-consolidation",
            json={"session_id": "console-jobs"},
        )
        assert create_job_response.status_code == 202
        job_id = str(create_job_response.json()["job"]["job_id"])

        jobs_fragment_response = client.get("/api/v1/console/fragments/jobs")
        sessions_fragment_response = client.get("/api/v1/console/fragments/sessions")
        evaluations_fragment_response = client.get("/api/v1/console/fragments/evaluations")
        evaluations_response = client.get("/api/v1/evaluations/sessions")

    assert jobs_fragment_response.status_code == 200
    assert job_id in jobs_fragment_response.text
    assert "console-jobs" in jobs_fragment_response.text

    assert sessions_fragment_response.status_code == 200
    assert "console-jobs" in sessions_fragment_response.text
    assert job_id not in sessions_fragment_response.text

    assert evaluations_fragment_response.status_code == 200
    assert "console-jobs" in evaluations_fragment_response.text
    assert "guarded turns" in evaluations_fragment_response.text

    assert evaluations_response.status_code == 200
    evaluations_body = evaluations_response.json()
    assert evaluations_body["session_count"] == 1
    assert evaluations_body["sessions"][0]["session_id"] == "console-jobs"


def test_console_scenarios_fragment_renders_recent_runs_and_trends() -> None:
    with TestClient(create_app()) as client:
        first_run_response = client.post(
            "/api/v1/evaluations/scenarios/run",
            json={"scenario_ids": ["stress_memory_recall_continuity"]},
        )
        assert first_run_response.status_code == 201
        first_run_id = str(first_run_response.json()["run_id"])

        second_run_response = client.post(
            "/api/v1/evaluations/scenarios/run",
            json={"scenario_ids": ["stress_memory_recall_continuity"]},
        )
        assert second_run_response.status_code == 201
        second_run_id = str(second_run_response.json()["run_id"])

        baseline_response = client.put(
            "/api/v1/evaluations/scenarios/baselines/default",
            json={"run_id": first_run_id, "note": "console baseline"},
        )
        assert baseline_response.status_code == 200

        response = client.get("/api/v1/console/fragments/scenarios")

    assert response.status_code == 200
    assert "Launch Signoff" in response.text
    assert "Longitudinal Report" in response.text
    assert "Horizon Report" in response.text
    assert "Multiweek Report" in response.text
    assert "Sustained Drift" in response.text
    assert "Release Dossier" in response.text
    assert "Hardening Checklist" in response.text
    assert "Safety Audit" in response.text
    assert "Redteam Robustness" in response.text
    assert "Ship Readiness" in response.text
    assert "Migration Readiness" in response.text
    assert "Baseline Governance" in response.text
    assert "Release Gate" in response.text
    assert "Baseline Track" in response.text
    assert "Stability Report" in response.text
    assert "Regression Watch" in response.text
    assert "Misalignment Taxonomy" in response.text
    assert "Critical Taxonomies" in response.text
    assert "Scenario Trends" in response.text
    assert "Recent Scenario Runs" in response.text
    assert "Memory Recall Continuity" in response.text
    assert "No redteam coverage" in response.text or "Run the redteam scenario set" in response.text
    assert first_run_id in response.text
    assert second_run_id in response.text
    assert "mini-action" in response.text


def test_console_evaluations_fragment_surfaces_output_quality_status() -> None:
    app = create_app()

    class DegradingLLMClient:
        def __init__(self) -> None:
            self._call_count = 0

        async def complete(self, request):  # type: ignore[no-untyped-def]
            self._call_count += 1
            responses = [
                "Plan next step now.",
                "Plan next step now and keep it steady, specific, and calm.",
                (
                    "Plan next step now and keep it steady, specific, and calm. "
                    "Plan next step now and keep it steady, specific, and calm."
                ),
                (
                    "Plan next step now and keep it steady, specific, and calm. "
                    "Plan next step now and keep it steady, specific, and calm. "
                    "Plan next step now and keep it steady, specific, and calm."
                ),
            ]
            return LLMResponse(
                model="test/degrading",
                output_text=responses[min(self._call_count - 1, len(responses) - 1)],
            )

    app.state.container.runtime_service._llm_client = DegradingLLMClient()

    with TestClient(app) as client:
        for index in range(4):
            turn_response = client.post(
                "/api/v1/sessions/console-quality/turns",
                json={"content": f"Please keep moving on the plan step {index}."},
            )
            assert turn_response.status_code == 201

        response = client.get("/api/v1/console/fragments/evaluations")

    assert response.status_code == 200
    assert "console-quality" in response.text
    assert "degrading" in response.text
    assert "Preference Signals" in response.text
    assert "Re-engagement Learning" in response.text
    assert "quality degrading" in response.text or "quality" in response.text


def test_console_evaluations_fragment_surfaces_strategy_diversity_status() -> None:
    with TestClient(create_app()) as client:
        for _ in range(4):
            turn_response = client.post(
                "/api/v1/sessions/console-diversity/turns",
                json={"content": "This plan is bad, but let's keep moving."},
            )
            assert turn_response.status_code == 201

        response = client.get("/api/v1/console/fragments/evaluations")

    assert response.status_code == 200
    assert "console-diversity" in response.text
    assert "intervened" in response.text
    assert "Diversity" in response.text or "diversity" in response.text
    assert "matrix" in response.text.lower()


def test_console_evaluations_fragment_surfaces_continuous_output_status() -> None:
    with TestClient(create_app()) as client:
        turn_response = client.post(
            "/api/v1/sessions/console-sequence/turns",
            json={"content": "Can you guarantee this plan will definitely work?"},
        )
        assert turn_response.status_code == 201

        response = client.get("/api/v1/console/fragments/evaluations")

    assert response.status_code == 200
    assert "console-sequence" in response.text
    assert "two_part_sequence" in response.text
    assert "continuous turns" in response.text


def test_console_evaluations_fragment_surfaces_runtime_quality_doctor_status() -> None:
    app = create_app()

    class RepetitiveLLMClient:
        async def complete(self, request):  # type: ignore[no-untyped-def]
            return LLMResponse(
                model=request.model,
                output_text=(
                    "I hear you, and I want to keep this grounded. "
                    "The next step is to keep moving."
                ),
            )

    app.state.container.runtime_service._llm_client = RepetitiveLLMClient()

    with TestClient(app) as client:
        for _ in range(3):
            turn_response = client.post(
                "/api/v1/sessions/console-quality-doctor/turns",
                json={"content": "Please keep the plan steady and practical."},
            )
            assert turn_response.status_code == 201

        response = client.get("/api/v1/console/fragments/evaluations")

    assert response.status_code == 200
    assert "console-quality-doctor" in response.text
    assert "quality doctor" in response.text.lower()
    assert "coordination" in response.text.lower()
    assert "follow-up" in response.text.lower()
    assert "system3" in response.text.lower()
    assert "identity " in response.text.lower()
    assert "migration " in response.text.lower()
    assert "model " in response.text.lower()
    assert "expectation" in response.text.lower()
    assert "dependency" in response.text.lower()
    assert "trust" in response.text.lower()
    assert "clarity" in response.text.lower()
    assert "aggregate governance" in response.text.lower()
    assert "aggregate controller" in response.text.lower()
    assert "orchestration controller" in response.text.lower()
    assert "dispatch envelope" in response.text.lower()
    assert "stage transition" in response.text.lower()
    assert "stage machine" in response.text.lower()
    assert "line state" in response.text.lower()
    assert "line transition" in response.text.lower()
    assert "line machine" in response.text.lower()
    assert "lifecycle state" in response.text.lower()
    assert "lifecycle queue" in response.text.lower()
    assert "lifecycle transition" in response.text.lower()
    assert "lifecycle machine" in response.text.lower()
    assert "lifecycle controller" in response.text.lower()
    assert "lifecycle envelope" in response.text.lower()
    assert "lifecycle scheduler" in response.text.lower()
    assert "lifecycle window" in response.text.lower()
    assert "lifecycle dispatch" in response.text.lower()
    assert "lifecycle outcome" in response.text.lower()
    assert "lifecycle resolution" in response.text.lower()
    assert "lifecycle activation" in response.text.lower()
    assert "lifecycle settlement" in response.text.lower()
    assert "lifecycle closure" in response.text.lower()
    assert "lifecycle availability" in response.text.lower()
    assert "lifecycle retention" in response.text.lower()
    assert "lifecycle eligibility" in response.text.lower()
    assert "lifecycle candidate" in response.text.lower()
    assert "lifecycle selectability" in response.text.lower()
    assert "lifecycle reentry" in response.text.lower()
    assert "lifecycle reactivation" in response.text.lower()
    assert "lifecycle resumption" in response.text.lower()
    assert "lifecycle readiness" in response.text.lower()
    assert "lifecycle continuation" in response.text.lower()
    assert "lifecycle sustainment" in response.text.lower()
    assert "lifecycle stewardship" in response.text.lower()
    assert "lifecycle guardianship" in response.text.lower()
    assert "lifecycle oversight" in response.text.lower()
    assert "lifecycle conclusion" in response.text.lower()
    assert "lifecycle disposition" in response.text.lower()
    assert "lifecycle standing" in response.text.lower()
    assert "lifecycle residency" in response.text.lower()
    assert "lifecycle tenure" in response.text.lower()
    assert "lifecycle persistence" in response.text.lower()
    assert "lifecycle durability" in response.text.lower()
    assert "lifecycle longevity" in response.text.lower()
    assert "lifecycle legacy" in response.text.lower()
    assert "lifecycle heritage" in response.text.lower()
    assert "lifecycle lineage" in response.text.lower()
    assert "lifecycle ancestry" in response.text.lower()
    assert "lifecycle provenance" in response.text.lower()
    assert "lifecycle origin" in response.text.lower()
    assert "lifecycle root" in response.text.lower()
    assert "lifecycle foundation" in response.text.lower()
    assert "lifecycle bedrock" in response.text.lower()
    assert "lifecycle substrate" in response.text.lower()
    assert "lifecycle stratum" in response.text.lower()
    assert "lifecycle layer" in response.text.lower()
    assert "lifecycle assurance" in response.text.lower()
    assert "lifecycle attestation" in response.text.lower()
    assert "lifecycle verification" in response.text.lower()
    assert "lifecycle certification" in response.text.lower()
    assert "lifecycle confirmation" in response.text.lower()
    assert "lifecycle ratification" in response.text.lower()
    assert "lifecycle endorsement" in response.text.lower()
    assert "lifecycle authorization" in response.text.lower()
    assert "lifecycle enactment" in response.text.lower()
    assert "lifecycle finality" in response.text.lower()
    assert "lifecycle completion" in response.text.lower()
    assert "lifecycle conclusion" in response.text.lower()
    assert "lifecycle arming" in response.text.lower()
    assert "lifecycle trigger" in response.text.lower()
    assert "lifecycle launch" in response.text.lower()
    assert "lifecycle handoff" in response.text.lower()
    assert "pacing" in response.text.lower()
    assert "attunement" in response.text.lower()
    assert "commitment" in response.text.lower()
    assert "disclosure" in response.text.lower()
    assert "reciprocity" in response.text.lower()
    assert "pressure" in response.text.lower()
    assert "relational " in response.text.lower()
    assert "safety " in response.text.lower()
    assert "progress governance" in response.text.lower()
    assert "stability governance" in response.text.lower()
    assert "supervision " in response.text.lower()
    assert "transition " in response.text.lower()
    assert "moral" in response.text.lower()
    assert "watch" in response.text


def test_console_overview_fragment_surfaces_proactive_followup_queue() -> None:
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/sessions/console-followup/turns",
            json={"content": "I'm exhausted and my chest feels tight, please keep this simple."},
        )
        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/sessions/console-followup/turns",
            json={"content": "Let's keep moving on the roadmap and make one steady next step."},
        )
        assert second_response.status_code == 201

        response = client.get("/api/v1/console/fragments/overview")

    assert response.status_code == 200
    assert "Proactive Follow-up Queue" in response.text
    assert "console-followup" in response.text
    assert "waiting" in response.text
    assert "scheduled" in response.text.lower()
    assert "progress_nudge" in response.text
    assert "progress_micro_commitment" in response.text
    assert "handoff" in response.text.lower()
    assert "cadence" in response.text.lower()
    assert "scheduling" in response.text.lower()
    assert "orchestration" in response.text.lower()
    assert "actuation" in response.text.lower()
    assert "progression" in response.text.lower()
    assert "user-space" in response.text.lower()
    assert "bridge" in response.text.lower()
    assert "guardrail" in response.text.lower()
    assert "matrix" in response.text.lower()
    assert "controller" in response.text.lower()
    assert "line controller" in response.text.lower()
    assert "feedback" in response.text.lower()
    assert "stage" in response.text.lower()
    assert "tempo" in response.text.lower()
    assert "ritual" in response.text.lower()
    assert "somatic" in response.text.lower()
    assert "anchor" in response.text.lower()


def test_console_evaluations_fragment_surfaces_proactive_followup_dispatch() -> None:
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/sessions/console-followup-dispatch/turns",
            json={"content": "I'm exhausted and my chest feels tight, please keep this simple."},
        )
        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/sessions/console-followup-dispatch/turns",
            json={"content": "Let's keep moving on the roadmap and make one steady next step."},
        )
        assert second_response.status_code == 201

        queue_response = client.get("/api/v1/runtime/proactive-followups")
        assert queue_response.status_code == 200
        queue_item = queue_response.json()["items"][0]

        dispatch_response = client.post(
            "/api/v1/runtime/proactive-followups/dispatch",
            params={"as_of": queue_item["due_at"]},
        )
        assert dispatch_response.status_code == 200

        response = client.get("/api/v1/console/fragments/evaluations")

    assert response.status_code == 200
    assert "console-followup-dispatch" in response.text
    assert "lifecycle dispatch" in response.text.lower()
    assert (
        "reschedule_lifecycle_dispatch" in response.text
        or "rescheduled_lifecycle_dispatch" in response.text
        or "close_loop_lifecycle_dispatch" in response.text
    )
    assert "explicit_opt_out" in response.text or "progress_micro_commitment" in response.text
    assert "guidance" in response.text.lower()
    assert "carryover" in response.text.lower()
    assert "cadence" in response.text.lower()
    assert "follow-up cadence" in response.text.lower()
    assert "follow-up scheduling" in response.text.lower()
    assert "follow-up orchestration" in response.text.lower()
    assert "follow-up actuation" in response.text.lower()
    assert "follow-up progression" in response.text.lower()
    assert "follow-up controller" in response.text.lower()
    assert "follow-up line controller" in response.text.lower()
    assert "follow-up refresh" in response.text.lower()
    assert "follow-up replan" in response.text.lower()
    assert "follow-up feedback" in response.text.lower()
    assert "follow-up gate" in response.text.lower()
    assert "dispatch progression" in response.text.lower()
    assert "actuation bridge" in response.text.lower()
    assert "ritual" in response.text.lower()
    assert "somatic plan" in response.text.lower()
