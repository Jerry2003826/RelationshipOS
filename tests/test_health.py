from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from relationship_os.main import create_app


def test_healthz() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runtime_overview_lists_registered_projectors() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/runtime")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "RelationshipOS"
    assert body["event_store_backend"] == "memory"
    assert body["llm_backend"] == "mock"
    assert body["llm_model"] == "openai/gpt-5"
    assert body["job_runtime"]["worker_id"]
    assert body["job_runtime"]["active_job_count"] == 0
    assert body["job_runtime"]["poll_interval_seconds"] == 0.5
    assert body["job_runtime"]["claim_ttl_seconds"] == 5.0
    assert body["job_runtime"]["heartbeat_interval_seconds"] == 1.0
    assert body["job_runtime"]["poller_running"] is True
    assert body["job_runtime"]["last_recovery_report"]["source"] == "startup"
    assert body["job_runtime"]["last_recovery_report"]["candidate_job_count"] == 0
    assert body["job_runtime"]["last_recovery_report"]["scheduled_job_count"] == 0
    assert body["proactive_followups"]["session_count"] == 0
    assert body["proactive_followups"]["actionable_count"] == 0
    assert body["proactive_followups"]["status_counts"] == {
        "hold": 0,
        "waiting": 0,
        "scheduled": 0,
        "due": 0,
        "overdue": 0,
    }
    assert body["proactive_dispatcher"]["worker_id"]
    assert body["proactive_dispatcher"]["poll_interval_seconds"] == 5.0
    assert body["proactive_dispatcher"]["max_dispatch_per_cycle"] == 2
    assert body["proactive_dispatcher"]["active_dispatch_count"] == 0
    assert body["proactive_dispatcher"]["poller_running"] is True
    assert body["proactive_dispatcher"]["last_run_report"]["source"] == "startup"
    assert body["projectors"] == [
        {"name": "inner-monologue-buffer", "version": "v1"},
        {"name": "session-memory", "version": "v1"},
        {"name": "session-runtime", "version": "v1"},
        {"name": "session-snapshots", "version": "v1"},
        {"name": "session-temporal-kg", "version": "v1"},
        {"name": "session-transcript", "version": "v1"},
    ]


def test_runtime_proactive_followups_endpoint_tracks_waiting_due_and_overdue() -> None:
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/sessions/runtime-followup/turns",
            json={"content": "I'm exhausted and my chest feels tight, please keep this simple."},
        )
        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/sessions/runtime-followup/turns",
            json={"content": "Let's keep moving on the roadmap and make one steady next step."},
        )
        assert second_response.status_code == 201

        overview_response = client.get("/api/v1/runtime")
        queue_response = client.get("/api/v1/runtime/proactive-followups")

        assert overview_response.status_code == 200
        overview_body = overview_response.json()
        assert overview_body["proactive_followups"]["session_count"] == 1
        assert overview_body["proactive_followups"]["status_counts"]["waiting"] == 1

        assert queue_response.status_code == 200
        queue_body = queue_response.json()
        assert queue_body["session_count"] == 1
        item = queue_body["items"][0]
        assert item["session_id"] == "runtime-followup"
        assert item["queue_status"] == "waiting"
        assert item["style"] == "progress_nudge"
        assert item["reengagement_strategy_key"] == "progress_micro_commitment"
        assert item["reengagement_pressure_mode"] == "low_pressure_progress"
        assert item["reengagement_autonomy_signal"] == "explicit_opt_out"
        assert item["reengagement_matrix_learning_mode"] == "cold_start"
        assert item["reengagement_matrix_learning_signal_count"] == 0
        assert item["reengagement_matrix_selected_supporting_session_count"] == 0
        assert item["guidance_mode"] in {"progress_guidance", "reflective_guidance"}
        assert item["guidance_handoff_mode"] in {
            "invite_progress_ping",
            "reflective_ping",
        }
        assert item["cadence_status"] in {"guided_progress", "reflect_then_move"}
        assert item["cadence_followup_tempo"] in {"progress_ping", "reflective_ping"}
        assert item["cadence_user_space_mode"] == "balanced_space"
        assert item["ritual_phase"] == "steady_progress"
        assert item["ritual_closing_move"] in {"progress_invitation", "reflective_close"}
        assert item["somatic_orchestration_status"] == "not_needed"
        assert item["somatic_orchestration_mode"] == "none"
        assert item["proactive_cadence_key"] == "progress_three_touch"
        assert item["proactive_cadence_stage_label"] == "first_touch"
        assert item["proactive_cadence_stage_count"] == 3
        assert item["proactive_scheduling_mode"] == "progress_spacing"
        assert (
            item["proactive_scheduling_first_touch_extra_delay_seconds"]
            == 2700 - item["trigger_after_seconds"]
        )
        assert item["proactive_orchestration_key"] == "progress_three_touch_orchestrated"
        assert item["proactive_orchestration_stage_delivery_mode"] == "two_part_sequence"
        assert item["proactive_actuation_key"] == "progress_three_touch_orchestrated_actuated"
        assert item["proactive_progression_key"] == "progress_three_touch_progressive"
        assert item["proactive_progression_stage_action"] == "advance_to_next_stage"
        assert item["proactive_progression_advanced"] is False
        assert item["proactive_actuation_opening_move"] in {
            "soft_open",
            "reflective_restate",
        }
        assert item["proactive_actuation_bridge_move"] == "resume_the_open_loop"
        assert item["proactive_actuation_user_space_signal"] == "explicit_opt_out"
        assert item["base_due_at"] is not None
        assert item["due_at"] is not None
        assert item["expires_at"] is not None

        scheduled_response = client.get(
            "/api/v1/runtime/proactive-followups",
            params={"as_of": item["base_due_at"]},
        )
        assert scheduled_response.status_code == 200
        scheduled_item = scheduled_response.json()["items"][0]
        assert scheduled_item["queue_status"] == "scheduled"
        assert scheduled_item["schedule_reason"] == "respect_outbound_cooldown"

        due_response = client.get(
            "/api/v1/runtime/proactive-followups",
            params={"as_of": item["due_at"]},
        )
        assert due_response.status_code == 200
        assert due_response.json()["items"][0]["queue_status"] == "due"

        dispatch_response = client.post(
            "/api/v1/runtime/proactive-followups/dispatch",
            params={"as_of": item["due_at"]},
        )
        assert dispatch_response.status_code == 200
        dispatch_body = dispatch_response.json()
        assert dispatch_body["dispatched_count"] == 0
        assert dispatch_body["skipped_count"] == 1
        assert dispatch_body["skipped"][0]["reason"] == "lifecycle_dispatch_rescheduled"

        post_dispatch_response = client.get(
            "/api/v1/runtime/proactive-followups",
            params={"as_of": item["due_at"]},
        )
        assert post_dispatch_response.status_code == 200
        post_dispatch_body = post_dispatch_response.json()
        assert post_dispatch_body["session_count"] == 1
        next_item = post_dispatch_body["items"][0]
        assert next_item["queue_status"] == "scheduled"
        assert next_item["proactive_cadence_stage_label"] == "first_touch"
        assert (
            datetime.fromisoformat(next_item["due_at"])
            > datetime.fromisoformat(item["due_at"])
        )
        assert (
            next_item["proactive_lifecycle_dispatch_decision"]
            == "reschedule_lifecycle_dispatch"
        )
        assert (
            next_item["proactive_lifecycle_dispatch_mode"]
            == "rescheduled_lifecycle_dispatch"
        )
        assert (
            next_item["proactive_lifecycle_activation_decision"]
            == "buffer_current_lifecycle_stage"
        )
        assert (
            next_item["proactive_lifecycle_settlement_decision"]
            == "buffer_lifecycle_settlement"
        )
        assert (
            next_item["proactive_lifecycle_closure_decision"]
            == "buffer_lifecycle_closure"
        )
        assert (
            next_item["proactive_lifecycle_availability_decision"]
            == "buffer_lifecycle_availability"
        )
        assert (
            next_item["proactive_lifecycle_retention_decision"]
            == "buffer_lifecycle_retention"
        )
        assert (
            next_item["proactive_lifecycle_eligibility_decision"]
            == "buffer_lifecycle_eligibility"
        )
        assert (
            next_item["proactive_lifecycle_candidate_decision"]
            == "buffer_lifecycle_candidate"
        )
        assert (
            next_item["proactive_lifecycle_selectability_decision"]
            == "buffer_lifecycle_selectability"
        )
        assert (
            next_item["proactive_lifecycle_reentry_decision"]
            == "buffer_lifecycle_reentry"
        )
        assert (
            next_item["proactive_lifecycle_reactivation_decision"]
            == "buffer_lifecycle_reactivation"
        )
        assert (
            next_item["proactive_lifecycle_resumption_decision"]
            == "buffer_lifecycle_resumption"
        )
        assert (
            next_item["proactive_lifecycle_readiness_decision"]
            == "buffer_lifecycle_readiness"
        )
        assert (
            next_item["proactive_lifecycle_arming_decision"]
            == "buffer_lifecycle_arming"
        )
        assert (
            next_item["proactive_lifecycle_trigger_decision"]
            == "buffer_lifecycle_trigger"
        )
        assert (
            next_item["proactive_lifecycle_launch_decision"]
            == "buffer_lifecycle_launch"
        )
        assert (
            next_item["proactive_lifecycle_handoff_decision"]
            == "buffer_lifecycle_handoff"
        )
        assert (
            next_item["proactive_lifecycle_continuation_decision"]
            == "buffer_lifecycle_continuation"
        )
        assert (
            next_item["proactive_lifecycle_sustainment_decision"]
            == "buffer_lifecycle_sustainment"
        )
        assert (
            next_item["proactive_lifecycle_stewardship_decision"]
            == "buffer_lifecycle_stewardship"
        )
        assert (
            next_item["proactive_lifecycle_guardianship_decision"]
            == "buffer_lifecycle_guardianship"
        )
        assert (
            next_item["proactive_lifecycle_oversight_decision"]
            == "buffer_lifecycle_oversight"
        )
        assert (
            next_item["proactive_lifecycle_assurance_decision"]
            == "buffer_lifecycle_assurance"
        )
        assert (
            next_item["proactive_lifecycle_attestation_decision"]
            == "buffer_lifecycle_attestation"
        )
        assert (
            next_item["proactive_lifecycle_verification_decision"]
            == "buffer_lifecycle_verification"
        )
        assert (
            next_item["proactive_lifecycle_certification_decision"]
            == "buffer_lifecycle_certification"
        )
        assert (
            next_item["proactive_lifecycle_confirmation_decision"]
            == "buffer_lifecycle_confirmation"
        )
        assert (
            next_item["proactive_lifecycle_ratification_decision"]
            == "buffer_lifecycle_ratification"
        )
        assert (
            next_item["proactive_lifecycle_endorsement_decision"]
            == "buffer_lifecycle_endorsement"
        )
        assert (
            next_item["proactive_lifecycle_authorization_decision"]
            == "buffer_lifecycle_authorization"
        )
        assert "lifecycle_endorsement_buffered" in str(next_item["schedule_reason"])
        assert (
            next_item["proactive_lifecycle_enactment_decision"]
            == "buffer_lifecycle_enactment"
        )
        assert (
            next_item["proactive_lifecycle_finality_decision"]
            == "buffer_lifecycle_finality"
        )
        assert (
            next_item["proactive_lifecycle_completion_decision"]
            == "buffer_lifecycle_completion"
        )
        assert (
            next_item["proactive_lifecycle_conclusion_decision"]
            == "buffer_lifecycle_conclusion"
        )
        assert (
            next_item["proactive_lifecycle_disposition_decision"]
            == "buffer_lifecycle_disposition"
        )
        assert (
            next_item["proactive_lifecycle_standing_decision"]
            == "buffer_lifecycle_standing"
        )
        assert (
            next_item["proactive_lifecycle_residency_decision"]
            == "buffer_lifecycle_residency"
        )
        assert (
            next_item["proactive_lifecycle_tenure_decision"]
            == "buffer_lifecycle_tenure"
        )
        assert (
            next_item["proactive_lifecycle_persistence_decision"]
            == "buffer_lifecycle_persistence"
        )
        assert (
            next_item["proactive_lifecycle_durability_decision"]
            == "buffer_lifecycle_durability"
        )
        assert (
            next_item["proactive_lifecycle_longevity_decision"]
            == "buffer_lifecycle_longevity"
        )
        assert (
            next_item["proactive_lifecycle_legacy_decision"]
            == "buffer_lifecycle_legacy"
        )
        assert (
            next_item["proactive_lifecycle_heritage_decision"]
            == "buffer_lifecycle_heritage"
        )
        assert (
            next_item["proactive_lifecycle_lineage_decision"]
            == "buffer_lifecycle_lineage"
        )
        assert (
            next_item["proactive_lifecycle_ancestry_decision"]
            == "buffer_lifecycle_ancestry"
        )
        assert (
            next_item["proactive_lifecycle_provenance_decision"]
            == "buffer_lifecycle_provenance"
        )
        assert (
            next_item["proactive_lifecycle_origin_decision"]
            == "buffer_lifecycle_origin"
        )
        assert (
            next_item["proactive_lifecycle_root_decision"]
            == "buffer_lifecycle_root"
        )
        assert (
            next_item["proactive_lifecycle_foundation_decision"]
            == "buffer_lifecycle_foundation"
        )
        assert (
            next_item["proactive_lifecycle_bedrock_decision"]
            == "buffer_lifecycle_bedrock"
        )
        assert (
            next_item["proactive_lifecycle_substrate_decision"]
            == "buffer_lifecycle_substrate"
        )
        assert (
            next_item["proactive_lifecycle_stratum_decision"]
            == "buffer_lifecycle_stratum"
        )
        assert (
            next_item["proactive_lifecycle_layer_decision"]
            == "buffer_lifecycle_layer"
        )
        assert "lifecycle_standing_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_residency_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_tenure_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_persistence_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_durability_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_longevity_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_legacy_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_heritage_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_lineage_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_ancestry_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_provenance_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_origin_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_root_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_foundation_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_bedrock_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_substrate_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_stratum_buffered" not in str(next_item["schedule_reason"])
        assert "lifecycle_layer_buffered" in str(next_item["schedule_reason"])
        assert next_item["proactive_progression_stage_action"] == "advance_to_next_stage"
        assert next_item["proactive_progression_advanced"] is False

        overdue_at = datetime.fromisoformat(next_item["expires_at"]) + timedelta(seconds=1)
        overdue_response = client.get(
            "/api/v1/runtime/proactive-followups",
            params={"as_of": overdue_at.isoformat()},
        )
        assert overdue_response.status_code == 200
        overdue_body = overdue_response.json()
        assert overdue_body["session_count"] == 1
        assert overdue_body["items"][0]["queue_status"] == "overdue"
        assert (
            overdue_body["items"][0]["proactive_lifecycle_activation_decision"]
            == "buffer_current_lifecycle_stage"
        )

        progressed_at = datetime.fromisoformat(next_item["expires_at"]) + timedelta(
            seconds=next_item["proactive_progression_max_overdue_seconds"] + 1
        )
        progressed_response = client.get(
            "/api/v1/runtime/proactive-followups",
            params={"as_of": progressed_at.isoformat()},
        )
        assert progressed_response.status_code == 200
        progressed_item = progressed_response.json()["items"][0]
        assert progressed_item["queue_status"] in {"due", "overdue"}
        assert progressed_item["proactive_cadence_stage_label"] == "final_soft_close"
        assert progressed_item["proactive_cadence_stage_index"] == 3
        assert progressed_item["proactive_progression_advanced"] is True
        assert str(progressed_item["schedule_reason"]) == "progression_advanced"
        assert "first_touch:advance_to_next_stage->second_touch" in str(
            progressed_item["proactive_progression_reason"]
        )
        assert "second_touch:jump_to_close_loop->final_soft_close" in str(
            progressed_item["proactive_progression_reason"]
        )
        guarded_due_response = client.get(
            "/api/v1/runtime/proactive-followups",
            params={"as_of": progressed_item["due_at"]},
        )
        assert guarded_due_response.status_code == 200
        guarded_due_item = guarded_due_response.json()["items"][0]
        assert guarded_due_item["queue_status"] == "overdue"
        assert guarded_due_item["proactive_cadence_stage_label"] == "second_touch"
        assert guarded_due_item["proactive_cadence_stage_index"] == 2
        assert guarded_due_item["proactive_progression_advanced"] is True
        assert (
            "line_controller:remaining_line_orchestration_recentered_after_first_touch"
            in str(guarded_due_item["schedule_reason"])
        )
        assert "first_touch:advance_to_next_stage->second_touch" in str(
            guarded_due_item["proactive_progression_reason"]
        )
        session_response = client.get("/api/v1/sessions/runtime-followup")
        assert session_response.status_code == 200
        gated_state = session_response.json()["state"]
        assert gated_state["proactive_lifecycle_dispatch_decision_count"] == 1
        assert (
            gated_state["proactive_lifecycle_dispatch_decision"]["decision"]
            == "reschedule_lifecycle_dispatch"
        )
