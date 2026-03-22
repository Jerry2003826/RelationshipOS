from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from relationship_os.application.proactive_followup_service.followup_builder import (
    _apply_matrix_learning_spacing,
)
from relationship_os.domain.llm import LLMFailure, LLMResponse
from relationship_os.main import create_app


def test_create_session_and_list_sessions() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/api/v1/sessions",
        json={"session_id": "session-explicit"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["session_id"] == "session-explicit"
    assert created["projection"]["state"]["session"]["started"] is True

    list_response = client.get("/api/v1/sessions")
    assert list_response.status_code == 200
    sessions = list_response.json()["sessions"]
    assert sessions[0]["session_id"] == "session-explicit"


def test_process_turn_builds_runtime_projection_and_trace() -> None:
    client = TestClient(create_app())

    turn_response = client.post(
        "/api/v1/sessions/session-turn/turns",
        json={"content": "我有点焦虑，想先把计划推进下去。"},
    )
    assert turn_response.status_code == 201
    body = turn_response.json()
    assert body["assistant_response"]
    assert body["assistant_responses"] == [body["assistant_response"]]
    assert body["assistant_response_mode"] == "single_message"
    assert body["projection"]["state"]["context_frame"]["appraisal"] == "negative"
    assert body["projection"]["state"]["confidence_assessment"]["response_mode"] == "direct"
    assert body["projection"]["state"]["relationship_state"]["turbulence_risk"] == "elevated"
    assert body["projection"]["state"]["repair_assessment"]["severity"] == "medium"
    assert body["projection"]["state"]["policy_gate"]["selected_path"] == "reflect_and_progress"
    assert body["projection"]["state"]["rehearsal_result"]["approved"] is True
    assert body["projection"]["state"]["empowerment_audit"]["approved"] is True
    assert body["projection"]["state"]["response_draft_plan"]["opening_move"]
    assert body["projection"]["state"]["response_rendering_policy"]["rendering_mode"]
    assert body["projection"]["state"]["response_sequence_plan"]["mode"] == "single_message"
    assert body["projection"]["state"]["response_post_audit"]["status"] == "pass"
    assert body["projection"]["state"]["response_normalization"]["changed"] is False
    assert body["projection"]["state"]["runtime_coordination_snapshot"]["time_awareness_mode"]
    assert body["projection"]["state"]["runtime_coordination_snapshot"]["ritual_phase"]
    assert body["projection"]["state"]["runtime_coordination_snapshot_count"] == 1
    assert body["projection"]["state"]["guidance_plan"]["mode"] in {
        "stabilizing_guidance",
        "repair_guidance",
        "clarifying_guidance",
        "boundary_guidance",
        "reanchor_guidance",
        "progress_guidance",
        "reflective_guidance",
    }
    assert body["projection"]["state"]["guidance_plan_count"] == 1
    assert body["projection"]["state"]["conversation_cadence_plan"]["status"] in {
        "guided_progress",
        "stabilize_and_wait",
        "clarify_and_pause",
        "boundary_guarded_progress",
        "reanchor_and_resume",
        "reflect_then_move",
        "repair_bridge",
    }
    assert body["projection"]["state"]["conversation_cadence_plan_count"] == 1
    assert body["projection"]["state"]["session_ritual_plan"]["phase"] in {
        "opening_ritual",
        "re_anchor",
        "repair_ritual",
        "alignment_check",
        "steady_progress",
    }
    assert body["projection"]["state"]["session_ritual_plan_count"] == 1
    assert body["projection"]["state"]["system3_snapshot"]["identity_anchor"]
    assert body["projection"]["state"]["system3_snapshot"]["identity_trajectory_status"] in {
        "stable",
        "watch",
        "recenter",
    }
    assert body["projection"]["state"]["system3_snapshot"]["version_migration_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "version_migration_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "hold",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["strategy_supervision_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "strategy_supervision_trajectory_status"
        ]
        in {
        "stable",
        "watch",
        "tighten",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["moral_trajectory_status"] in {
        "stable",
        "watch",
        "recenter",
    }
    assert body["projection"]["state"]["system3_snapshot"]["emotional_debt_trajectory_status"] in {
        "stable",
        "watch",
        "decompression_required",
    }
    assert body["projection"]["state"]["system3_snapshot"]["expectation_calibration_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "expectation_calibration_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "reset",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["dependency_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "dependency_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["autonomy_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "autonomy_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["boundary_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "boundary_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["support_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "support_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["continuity_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "continuity_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["repair_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "repair_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["trust_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "trust_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["clarity_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "clarity_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["pacing_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "pacing_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["attunement_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "attunement_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["commitment_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "commitment_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["disclosure_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "disclosure_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["reciprocity_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "reciprocity_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["pressure_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "pressure_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["relational_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "relational_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["safety_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "safety_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["progress_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "progress_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["stability_governance_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert (
        body["projection"]["state"]["system3_snapshot"][
            "stability_governance_trajectory_status"
        ]
        in {
            "stable",
            "watch",
            "recenter",
        }
    )
    assert body["projection"]["state"]["system3_snapshot"]["user_model_trajectory_status"] in {
        "stable",
        "watch",
        "recenter",
    }
    assert body["projection"]["state"]["system3_snapshot"]["growth_stage"] in {
        "forming",
        "stabilizing",
        "steadying",
        "deepening",
        "repairing",
    }
    assert body["projection"]["state"]["system3_snapshot_count"] == 1
    assert body["projection"]["state"]["memory_bundle"]["working_memory"]
    assert body["projection"]["state"]["last_memory_write_guard"]["blocked_count"] == 0
    assert body["projection"]["state"]["last_memory_retention"]["pinned_count"] >= 1
    assert body["projection"]["state"]["last_memory_recall"]["recall_count"] == 0
    assert body["projection"]["state"]["last_memory_forgetting"]["evicted_count"] == 0
    assert (
        body["projection"]["state"]["knowledge_boundary_decision"]["decision"]
        == "answer_directly"
    )
    assert body["projection"]["state"]["repair_plan"]["rupture_detected"] is True
    assert body["projection"]["state"]["private_judgment"]["summary"]
    assert body["projection"]["state"]["session_directive"]["next_action"]
    assert len(body["projection"]["state"]["inner_monologue"]) == 10

    get_session_response = client.get("/api/v1/sessions/session-turn")
    assert get_session_response.status_code == 200
    assert get_session_response.json()["state"]["turn_count"] == 1

    trace_response = client.get("/api/v1/runtime/trace/session-turn")
    assert trace_response.status_code == 200
    trace = trace_response.json()["trace"]
    assert any(event["event_type"] == "system.context_frame.computed" for event in trace)
    assert any(
        event["event_type"] == "system.confidence_assessment.computed" for event in trace
    )
    assert any(
        event["event_type"] == "system.repair_assessment.computed" for event in trace
    )
    assert any(event["event_type"] == "system.policy_gate.decided" for event in trace)
    assert any(event["event_type"] == "system.guidance_plan.updated" for event in trace)
    assert any(
        event["event_type"] == "system.conversation_cadence.updated"
        for event in trace
    )
    assert any(event["event_type"] == "system.session_ritual.updated" for event in trace)
    assert any(event["event_type"] == "system.response_draft.planned" for event in trace)
    assert any(
        event["event_type"] == "system.runtime_coordination.updated" for event in trace
    )
    assert any(
        event["event_type"] == "system.response_rendering_policy.decided"
        for event in trace
    )
    assert any(
        event["event_type"] == "system.system3_snapshot.updated" for event in trace
    )
    assert any(
        event["event_type"] == "system.response_post_audited"
        for event in trace
    )
    assert any(
        event["event_type"] == "system.response.normalized"
        for event in trace
    )
    assert any(
        event["event_type"] == "system.memory_retention_policy.applied"
        for event in trace
    )
    assert any(event["event_type"] == "assistant.message.sent" for event in trace)

    inner_monologue_response = client.get(
        "/api/v1/sessions/session-turn/inner-monologue"
    )
    assert inner_monologue_response.status_code == 200
    buffer_state = inner_monologue_response.json()["state"]
    assert buffer_state["entry_count"] == 10
    assert buffer_state["last_stage"] == "response_rendering"


def test_process_turn_uses_recalled_memory_on_follow_up_turn() -> None:
    client = TestClient(create_app())

    first_turn_response = client.post(
        "/api/v1/sessions/session-recall/turns",
        json={"content": "I feel anxious, but I still want to keep the plan moving."},
    )
    assert first_turn_response.status_code == 201

    second_turn_response = client.post(
        "/api/v1/sessions/session-recall/turns",
        json={"content": "Please keep the plan gentle and help me stay calm."},
    )
    assert second_turn_response.status_code == 201
    body = second_turn_response.json()

    recall_state = body["projection"]["state"]["last_memory_recall"]
    assert recall_state["recall_count"] >= 1
    assert recall_state["graph_summary"]["bridge_count"] >= 1
    assert recall_state["integrity_summary"]["checked_count"] >= 1
    assert recall_state["bridges"]
    assert any("plan" in result["value"].lower() for result in recall_state["results"])
    assert all(
        result["integrity"]["status"] == "accepted"
        for result in recall_state["results"]
    )
    assert any(
        "plan" in focus_point.lower()
        for focus_point in body["projection"]["state"]["session_directive"]["focus_points"]
    )
    assert "recall=" in body["projection"]["state"]["private_judgment"]["rationale"]
    assert "recall surfaced" in body["projection"]["state"]["inner_monologue"][1]["summary"]

    trace_response = client.get("/api/v1/runtime/trace/session-recall")
    assert trace_response.status_code == 200
    trace = trace_response.json()["trace"]
    assert any(event["event_type"] == "system.memory_recall.performed" for event in trace)


def test_process_turn_records_memory_write_guard_for_low_signal_input() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/sessions/session-write-guard/turns",
        json={"content": "ok"},
    )

    assert response.status_code == 201
    body = response.json()
    guard_state = body["projection"]["state"]["last_memory_write_guard"]
    assert guard_state["blocked_count"] >= 2
    assert body["projection"]["state"]["memory_bundle"]["working_memory"] == []
    assert any(
        item["layer"] == "working_memory" and item["reason"] == "low_signal_value"
        for item in guard_state["blocked_items"]
    )

    trace_response = client.get("/api/v1/runtime/trace/session-write-guard")
    trace = trace_response.json()["trace"]
    assert any(
        event["event_type"] == "system.memory_write_guard.evaluated" for event in trace
    )


def test_process_turn_records_explicit_knowledge_boundary_for_uncertain_question() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/sessions/session-boundary/turns",
        json={"content": "Can you guarantee this plan will definitely work?"},
    )

    assert response.status_code == 201
    body = response.json()
    boundary_state = body["projection"]["state"]["knowledge_boundary_decision"]
    assert boundary_state["decision"] == "answer_with_uncertainty"
    assert boundary_state["boundary_type"] == "uncertain_future"
    assert body["projection"]["state"]["confidence_assessment"]["response_mode"] == "calibrated"
    assert body["projection"]["state"]["policy_gate"]["selected_path"] == "answer_with_uncertainty"
    assert body["projection"]["state"]["policy_gate"]["empowerment_risk"] == "guarded"
    assert (
        body["projection"]["state"]["rehearsal_result"]["predicted_user_impact"]
        == "trust_preserving_calibration"
    )
    assert body["projection"]["state"]["empowerment_audit"]["transparency_required"] is True
    assert (
        body["projection"]["state"]["confidence_assessment"][
            "should_disclose_uncertainty"
        ]
        is True
    )
    assert any(
        item in body["projection"]["state"]["response_draft_plan"]["must_include"]
        for item in {"state limits explicitly", "state the limit clearly"}
    )
    assert (
        "false_certainty"
        in body["projection"]["state"]["response_draft_plan"]["must_avoid"]
    )
    assert (
        body["projection"]["state"]["response_rendering_policy"][
            "include_uncertainty_statement"
        ]
        is True
    )
    assert (
        body["projection"]["state"]["response_post_audit"][
            "includes_uncertainty_statement"
        ]
        is True
    )
    assert body["projection"]["state"]["response_normalization"]["final_status"] == "pass"
    assert body["projection"]["state"]["session_directive"]["response_style"] == "calibrated"
    assert body["projection"]["state"]["strategy_decision"]["strategy"] == "answer_with_uncertainty"
    assert body["assistant_response_mode"] == "two_part_sequence"
    assert len(body["assistant_responses"]) == 2
    assert body["projection"]["state"]["response_sequence_plan"]["mode"] == "two_part_sequence"
    assert (
        body["projection"]["state"]["response_sequence_plan"]["reasons"]
        == ["uncertainty_then_next_step"]
    )
    assert body["projection"]["state"]["response_sequence_plan"]["unit_count"] == 2

    trace_response = client.get("/api/v1/runtime/trace/session-boundary")
    trace = trace_response.json()["trace"]
    assert any(
        event["event_type"] == "system.knowledge_boundary.decided" for event in trace
    )
    assistant_events = [
        event for event in trace if event["event_type"] == "assistant.message.sent"
    ]
    assert len(assistant_events) == 2
    assert assistant_events[0]["payload"]["sequence_total"] == 2
    assert assistant_events[1]["payload"]["sequence_index"] == 2


def test_process_turn_records_clarification_confidence_gate_for_focused_question() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/sessions/session-clarify/turns",
        json={
            "content": (
                "What should I say next when the plan keeps shifting and I still do not "
                "know which part matters most in this conversation?"
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    confidence_state = body["projection"]["state"]["confidence_assessment"]
    boundary_state = body["projection"]["state"]["knowledge_boundary_decision"]
    policy_gate = body["projection"]["state"]["policy_gate"]
    rehearsal_state = body["projection"]["state"]["rehearsal_result"]
    assert confidence_state["response_mode"] == "clarify"
    assert confidence_state["needs_clarification"] is True
    assert boundary_state["decision"] == "clarify_before_answer"
    assert policy_gate["selected_path"] == "clarify_then_answer"
    assert policy_gate["regulation_mode"] == "clarify"
    assert rehearsal_state["likely_user_response"].startswith("The user may provide missing detail")
    assert (
        body["projection"]["state"]["response_draft_plan"]["question_strategy"]
        == "single_focused_question"
    )
    assert (
        body["projection"]["state"]["response_rendering_policy"]["question_count_limit"]
        == 1
    )
    assert body["projection"]["state"]["strategy_decision"]["strategy"] == "clarify_then_answer"


def test_process_turn_intervenes_when_strategy_entropy_stays_too_low() -> None:
    client = TestClient(create_app())
    last_body: dict[str, object] | None = None

    for turn_index in range(4):
        response = client.post(
            "/api/v1/sessions/session-strategy-diversity/turns",
            json={"content": "This plan is bad, but let's keep moving."},
        )
        assert response.status_code == 201
        last_body = response.json()
        strategy_state = last_body["projection"]["state"]["strategy_decision"]
        if turn_index < 3:
            assert strategy_state["strategy"] == "reflect_and_progress"
            assert strategy_state["diversity_status"] == "stable"

    assert last_body is not None
    strategy_state = last_body["projection"]["state"]["strategy_decision"]
    assert strategy_state["strategy"] == "repair_then_progress"
    assert strategy_state["source_strategy"] == "reflect_and_progress"
    assert strategy_state["diversity_status"] == "intervened"
    assert strategy_state["diversity_entropy"] == 0.0
    assert strategy_state["explored_strategy"] is True
    assert strategy_state["recent_strategy_counts"] == {"reflect_and_progress": 3}
    assert strategy_state["alternatives_considered"] == ["repair_then_progress"]
    assert (
        last_body["projection"]["state"]["session_directive"]["next_action"]
        == "repair_then_progress"
    )
    assert last_body["projection"]["state"]["strategy_history"][-4:] == [
        "reflect_and_progress",
        "reflect_and_progress",
        "reflect_and_progress",
        "repair_then_progress",
    ]


def test_process_turn_runs_runtime_quality_doctor_on_configured_interval() -> None:
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
    client = TestClient(app)

    for _ in range(3):
        response = client.post(
            "/api/v1/sessions/session-quality-doctor/turns",
            json={"content": "Please keep the plan steady and practical."},
        )
        assert response.status_code == 201

    body = response.json()
    report = body["projection"]["state"]["last_runtime_quality_doctor"]
    assert report["status"] == "watch"
    assert report["triggered_turn_index"] == 3
    assert report["window_turn_count"] == 3
    assert report["issue_count"] >= 1
    assert "repetitive_openings" in report["issues"]
    assert body["projection"]["state"]["runtime_quality_doctor_report_count"] == 1
    system3_snapshot = body["projection"]["state"]["system3_snapshot"]
    assert system3_snapshot["strategy_audit_status"] == "watch"
    assert system3_snapshot["strategy_audit_trajectory_status"] in {
        "stable",
        "watch",
        "corrective",
    }
    assert system3_snapshot["user_model_evolution_status"] in {
        "pass",
        "watch",
        "revise",
    }
    assert system3_snapshot["growth_transition_status"] in {
        "stable",
        "ready",
        "watch",
        "redirect",
    }
    assert system3_snapshot["growth_transition_target"] in {
        "forming",
        "stabilizing",
        "steadying",
        "deepening",
        "repairing",
    }
    assert system3_snapshot["growth_transition_trajectory_status"] in {
        "stable",
        "watch",
        "advance",
        "redirect",
    }
    assert system3_snapshot["user_model_revision_mode"] in {
        "steady_refinement",
        "memory_recalibration",
        "repair_reframing",
        "delivery_preference_refinement",
        "needs_recalibration",
    }
    assert body["projection"]["state"]["system3_snapshot_count"] == 3

    trace_response = client.get("/api/v1/runtime/trace/session-quality-doctor")
    trace = trace_response.json()["trace"]
    assert any(
        event["event_type"] == "system.runtime_quality_doctor.completed"
        for event in trace
    )


def test_process_turn_builds_runtime_coordination_for_high_load_and_proactive_followup() -> None:
    client = TestClient(create_app())

    first_response = client.post(
        "/api/v1/sessions/session-coordination/turns",
        json={"content": "I'm exhausted and my chest feels tight, please keep this simple."},
    )
    assert first_response.status_code == 201
    first_body = first_response.json()
    first_coordination = first_body["projection"]["state"]["runtime_coordination_snapshot"]
    assert first_coordination["time_awareness_mode"] == "opening"
    assert first_coordination["ritual_phase"] == "opening_ritual"
    assert first_coordination["cognitive_load_band"] == "high"
    assert first_coordination["response_budget_mode"] == "concise"
    assert first_coordination["somatic_cue"] in {"fatigue", "breath", "tension"}
    first_followup = first_body["projection"]["state"]["proactive_followup_directive"]
    assert first_followup["status"] == "hold"
    assert "coordination_not_ready" in first_followup["hold_reasons"]
    assert (
        first_body["projection"]["state"]["guidance_plan"]["mode"]
        == "stabilizing_guidance"
    )
    assert (
        first_body["projection"]["state"]["guidance_plan"]["ritual_action"]
        == "somatic_grounding"
    )
    assert (
        first_body["projection"]["state"]["guidance_plan"]["handoff_mode"]
        == "no_pressure_checkin"
    )
    assert (
        first_body["projection"]["state"]["guidance_plan"]["carryover_mode"]
        == "grounding_ping"
    )
    first_cadence = first_body["projection"]["state"]["conversation_cadence_plan"]
    assert first_cadence["status"] == "stabilize_and_wait"
    assert first_cadence["followup_tempo"] == "grounding_ping"
    assert first_cadence["user_space_mode"] == "spacious"
    first_ritual = first_body["projection"]["state"]["session_ritual_plan"]
    assert first_ritual["phase"] == "opening_ritual"
    assert first_ritual["somatic_shortcut"] in {
        "one_slower_breath",
        "drop_shoulders_once",
        "unclench_jaw_once",
    }
    first_somatic_plan = first_body["projection"]["state"]["somatic_orchestration_plan"]
    assert first_somatic_plan["status"] == "active"
    assert first_somatic_plan["body_anchor"] in {
        "one_slower_breath",
        "drop_shoulders_and_exhale",
        "unclench_jaw_and_shoulders",
    }
    assert (
        first_body["projection"]["state"]["response_rendering_policy"]["max_sentences"] <= 3
    )

    second_response = client.post(
        "/api/v1/sessions/session-coordination/turns",
        json={"content": "Let's keep moving on the roadmap and make one steady next step."},
    )
    assert second_response.status_code == 201
    second_body = second_response.json()
    second_coordination = second_body["projection"]["state"]["runtime_coordination_snapshot"]
    assert second_coordination["time_awareness_mode"] == "ongoing"
    assert second_coordination["proactive_followup_eligible"] is True
    assert second_coordination["proactive_style"] == "progress_nudge"
    assert second_body["projection"]["state"]["runtime_coordination_snapshot_count"] == 2
    second_followup = second_body["projection"]["state"]["proactive_followup_directive"]
    assert second_followup["status"] == "ready"
    assert second_followup["style"] == "progress_nudge"
    assert second_followup["trigger_after_seconds"] in {1200, 1800}
    assert second_body["projection"]["state"]["guidance_plan"]["mode"] in {
        "progress_guidance",
        "reflective_guidance",
    }
    assert second_body["projection"]["state"]["guidance_plan"]["handoff_mode"] in {
        "invite_progress_ping",
        "reflective_ping",
    }
    second_cadence = second_body["projection"]["state"]["conversation_cadence_plan"]
    assert second_cadence["status"] in {"guided_progress", "reflect_then_move"}
    assert second_cadence["turn_shape"] in {"paired_step", "reflect_then_step"}
    second_ritual = second_body["projection"]["state"]["session_ritual_plan"]
    assert second_ritual["phase"] == "steady_progress"
    assert second_ritual["closing_move"] in {"progress_invitation", "reflective_close"}
    second_somatic_plan = second_body["projection"]["state"]["somatic_orchestration_plan"]
    assert second_somatic_plan["status"] == "not_needed"
    assert second_body["projection"]["state"]["proactive_followup_directive_count"] == 2
    proactive_cadence_plan = second_body["projection"]["state"]["proactive_cadence_plan"]
    assert proactive_cadence_plan["status"] == "active"
    assert proactive_cadence_plan["cadence_key"] == "progress_three_touch"
    assert proactive_cadence_plan["stage_labels"] == [
        "first_touch",
        "second_touch",
        "final_soft_close",
    ]
    assert proactive_cadence_plan["close_after_stage_index"] == 3
    proactive_scheduling_plan = second_body["projection"]["state"][
        "proactive_scheduling_plan"
    ]
    assert proactive_scheduling_plan["status"] == "active"
    assert proactive_scheduling_plan["scheduler_mode"] == "progress_spacing"
    assert (
        proactive_scheduling_plan["min_seconds_since_last_outbound"] == 2700
    )
    assert (
        proactive_scheduling_plan["first_touch_extra_delay_seconds"]
        == 2700 - second_followup["trigger_after_seconds"]
    )
    assert second_body["projection"]["state"]["proactive_scheduling_plan_count"] == 2
    proactive_orchestration_plan = second_body["projection"]["state"][
        "proactive_orchestration_plan"
    ]
    assert proactive_orchestration_plan["status"] == "active"
    assert (
        proactive_orchestration_plan["orchestration_key"]
        == "progress_three_touch_orchestrated"
    )
    assert proactive_orchestration_plan["close_loop_stage"] == "final_soft_close"
    second_touch_directive = next(
        item
        for item in proactive_orchestration_plan["stage_directives"]
        if item["stage_label"] == "second_touch"
    )
    assert second_touch_directive["delivery_mode"] == "single_message"
    assert second_touch_directive["question_mode"] == "statement_only"
    assert second_touch_directive["autonomy_mode"] == "explicit_no_pressure"
    assert second_body["projection"]["state"]["proactive_orchestration_plan_count"] == 2
    proactive_actuation_plan = second_body["projection"]["state"][
        "proactive_actuation_plan"
    ]
    assert proactive_actuation_plan["status"] == "active"
    assert (
        proactive_actuation_plan["actuation_key"]
        == "progress_three_touch_orchestrated_actuated"
    )
    second_touch_actuation = next(
        item
        for item in proactive_actuation_plan["stage_actuations"]
        if item["stage_label"] == "second_touch"
    )
    assert second_touch_actuation["opening_move"] == "shared_context_bridge"
    assert second_touch_actuation["bridge_move"] == "micro_step_bridge"
    assert second_touch_actuation["closing_move"] == "boundary_safe_close"
    assert second_touch_actuation["somatic_mode"] == "none"
    assert second_touch_actuation["user_space_signal"] == "explicit_no_pressure"
    assert second_body["projection"]["state"]["proactive_actuation_plan_count"] == 2
    proactive_progression_plan = second_body["projection"]["state"][
        "proactive_progression_plan"
    ]
    assert proactive_progression_plan["status"] == "active"
    assert (
        proactive_progression_plan["progression_key"]
        == "progress_three_touch_progressive"
    )
    second_touch_progression = next(
        item
        for item in proactive_progression_plan["stage_progressions"]
        if item["stage_label"] == "second_touch"
    )
    assert second_touch_progression["on_expired"] == "jump_to_close_loop"
    final_touch_progression = next(
        item
        for item in proactive_progression_plan["stage_progressions"]
        if item["stage_label"] == "final_soft_close"
    )
    assert final_touch_progression["on_expired"] == "close_line"
    assert second_body["projection"]["state"]["proactive_progression_plan_count"] == 2
    proactive_guardrail_plan = second_body["projection"]["state"][
        "proactive_guardrail_plan"
    ]
    assert proactive_guardrail_plan["status"] == "active"
    assert proactive_guardrail_plan["guardrail_key"] == "progress_three_touch_guarded"
    assert proactive_guardrail_plan["max_dispatch_count"] == 3
    second_touch_guardrail = next(
        item
        for item in proactive_guardrail_plan["stage_guardrails"]
        if item["stage_label"] == "second_touch"
    )
    assert second_touch_guardrail["min_seconds_since_last_user"] >= 14400
    assert second_touch_guardrail["min_seconds_since_last_dispatch"] >= 10800
    assert second_body["projection"]["state"]["proactive_guardrail_plan_count"] == 2
    reengagement_matrix_assessment = second_body["projection"]["state"][
        "reengagement_matrix_assessment"
    ]
    assert reengagement_matrix_assessment["status"] == "active"
    assert (
        reengagement_matrix_assessment["selected_strategy_key"]
        == "progress_micro_commitment"
    )
    assert reengagement_matrix_assessment["blocked_count"] == 0
    assert reengagement_matrix_assessment["learning_mode"] == "cold_start"
    assert reengagement_matrix_assessment["learning_signal_count"] == 0
    assert reengagement_matrix_assessment["learning_context_stratum"]
    assert any(
        item["selected"] and item["strategy_key"] == "progress_micro_commitment"
        for item in reengagement_matrix_assessment["candidates"]
    )
    assert (
        second_body["projection"]["state"]["reengagement_matrix_assessment_count"] == 2
    )
    reengagement_plan = second_body["projection"]["state"]["reengagement_plan"]
    assert reengagement_plan["status"] == "ready"
    assert reengagement_plan["ritual_mode"] == "progress_reanchor"
    assert reengagement_plan["delivery_mode"] == "two_part_sequence"
    assert reengagement_plan["strategy_key"] == "progress_micro_commitment"
    assert reengagement_plan["relational_move"] == "goal_reconnect"
    assert reengagement_plan["pressure_mode"] == "low_pressure_progress"
    assert reengagement_plan["autonomy_signal"] == "explicit_opt_out"
    assert reengagement_plan["sequence_objective"] == "reconnect_then_tiny_step"
    assert second_body["projection"]["state"]["reengagement_plan_count"] == 2


def test_dispatch_proactive_followup_records_dispatch_event_and_projection_state() -> None:
    client = TestClient(create_app())

    first_response = client.post(
        "/api/v1/sessions/session-followup-dispatch/turns",
        json={"content": "I'm exhausted and my chest feels tight, please keep this simple."},
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/sessions/session-followup-dispatch/turns",
        json={"content": "Let's keep moving on the roadmap and make one steady next step."},
    )
    assert second_response.status_code == 201

    queue_item = client.get("/api/v1/runtime/proactive-followups").json()["items"][0]
    first_dispatch_body = client.post(
        "/api/v1/runtime/proactive-followups/dispatch",
        params={"as_of": queue_item["due_at"]},
    ).json()
    assert first_dispatch_body["dispatched_count"] == 0
    assert first_dispatch_body["skipped"][0]["reason"] == "lifecycle_dispatch_rescheduled"

    rescheduled_item = client.get(
        "/api/v1/runtime/proactive-followups",
        params={"as_of": queue_item["due_at"]},
    ).json()["items"][0]
    assert rescheduled_item["queue_status"] == "scheduled"
    assert (
        datetime.fromisoformat(rescheduled_item["due_at"])
        > datetime.fromisoformat(queue_item["due_at"])
    )
    assert (
        rescheduled_item["proactive_lifecycle_dispatch_decision"]
        == "reschedule_lifecycle_dispatch"
    )
    assert (
        rescheduled_item["proactive_lifecycle_outcome_decision"]
        == "lifecycle_dispatch_rescheduled"
    )
    assert (
        rescheduled_item["proactive_lifecycle_activation_decision"]
        == "buffer_current_lifecycle_stage"
    )
    assert (
        rescheduled_item["proactive_lifecycle_settlement_decision"]
        == "buffer_lifecycle_settlement"
    )
    assert (
        rescheduled_item["proactive_lifecycle_closure_decision"]
        == "buffer_lifecycle_closure"
    )
    assert (
        rescheduled_item["proactive_lifecycle_availability_decision"]
        == "buffer_lifecycle_availability"
    )
    assert (
        rescheduled_item["proactive_lifecycle_retention_decision"]
        == "buffer_lifecycle_retention"
    )
    assert (
        rescheduled_item["proactive_lifecycle_eligibility_decision"]
        == "buffer_lifecycle_eligibility"
    )
    assert (
        rescheduled_item["proactive_lifecycle_candidate_decision"]
        == "buffer_lifecycle_candidate"
    )
    assert (
        rescheduled_item["proactive_lifecycle_selectability_decision"]
        == "buffer_lifecycle_selectability"
    )
    assert (
        rescheduled_item["proactive_lifecycle_reentry_decision"]
        == "buffer_lifecycle_reentry"
    )
    assert (
        rescheduled_item["proactive_lifecycle_reactivation_decision"]
        == "buffer_lifecycle_reactivation"
    )
    assert (
        rescheduled_item["proactive_lifecycle_resumption_decision"]
        == "buffer_lifecycle_resumption"
    )
    assert (
        rescheduled_item["proactive_lifecycle_readiness_decision"]
        == "buffer_lifecycle_readiness"
    )
    assert (
        rescheduled_item["proactive_lifecycle_arming_decision"]
        == "buffer_lifecycle_arming"
    )
    assert (
        rescheduled_item["proactive_lifecycle_trigger_decision"]
        == "buffer_lifecycle_trigger"
    )
    assert (
        rescheduled_item["proactive_lifecycle_launch_decision"]
        == "buffer_lifecycle_launch"
    )
    assert (
        rescheduled_item["proactive_lifecycle_handoff_decision"]
        == "buffer_lifecycle_handoff"
    )
    assert (
        rescheduled_item["proactive_lifecycle_continuation_decision"]
        == "buffer_lifecycle_continuation"
    )
    assert (
        rescheduled_item["proactive_lifecycle_sustainment_decision"]
        == "buffer_lifecycle_sustainment"
    )
    assert (
        rescheduled_item["proactive_lifecycle_stewardship_decision"]
        == "buffer_lifecycle_stewardship"
    )
    assert (
        rescheduled_item["proactive_lifecycle_guardianship_decision"]
        == "buffer_lifecycle_guardianship"
    )
    assert (
        rescheduled_item["proactive_lifecycle_oversight_decision"]
        == "buffer_lifecycle_oversight"
    )
    assert (
        rescheduled_item["proactive_lifecycle_assurance_decision"]
        == "buffer_lifecycle_assurance"
    )
    assert (
        rescheduled_item["proactive_lifecycle_attestation_decision"]
        == "buffer_lifecycle_attestation"
    )
    assert (
        rescheduled_item["proactive_lifecycle_verification_decision"]
        == "buffer_lifecycle_verification"
    )
    assert (
        rescheduled_item["proactive_lifecycle_certification_decision"]
        == "buffer_lifecycle_certification"
    )
    assert (
        rescheduled_item["proactive_lifecycle_confirmation_decision"]
        == "buffer_lifecycle_confirmation"
    )
    assert (
        rescheduled_item["proactive_lifecycle_ratification_decision"]
        == "buffer_lifecycle_ratification"
    )
    assert (
        rescheduled_item["proactive_lifecycle_endorsement_decision"]
        == "buffer_lifecycle_endorsement"
    )
    assert (
        rescheduled_item["proactive_lifecycle_authorization_decision"]
        == "buffer_lifecycle_authorization"
    )
    assert (
        rescheduled_item["proactive_lifecycle_enactment_decision"]
        == "buffer_lifecycle_enactment"
    )
    assert (
        rescheduled_item["proactive_lifecycle_finality_decision"]
        == "buffer_lifecycle_finality"
    )
    assert (
        rescheduled_item["proactive_lifecycle_completion_decision"]
        == "buffer_lifecycle_completion"
    )
    assert (
        rescheduled_item["proactive_lifecycle_conclusion_decision"]
        == "buffer_lifecycle_conclusion"
    )
    assert (
        rescheduled_item["proactive_lifecycle_disposition_decision"]
        == "buffer_lifecycle_disposition"
    )
    assert (
        rescheduled_item["proactive_lifecycle_standing_decision"]
        == "buffer_lifecycle_standing"
    )
    assert (
        rescheduled_item["proactive_lifecycle_residency_decision"]
        == "buffer_lifecycle_residency"
    )
    assert (
        rescheduled_item["proactive_lifecycle_tenure_decision"]
        == "buffer_lifecycle_tenure"
    )
    assert (
        rescheduled_item["proactive_lifecycle_persistence_decision"]
        == "buffer_lifecycle_persistence"
    )
    assert (
        rescheduled_item["proactive_lifecycle_durability_decision"]
        == "buffer_lifecycle_durability"
    )
    assert (
        rescheduled_item["proactive_lifecycle_longevity_decision"]
        == "buffer_lifecycle_longevity"
    )
    assert (
        rescheduled_item["proactive_lifecycle_legacy_decision"]
        == "buffer_lifecycle_legacy"
    )
    assert (
        rescheduled_item["proactive_lifecycle_heritage_decision"]
        == "buffer_lifecycle_heritage"
    )
    assert (
        rescheduled_item["proactive_lifecycle_lineage_decision"]
        == "buffer_lifecycle_lineage"
    )
    assert (
        rescheduled_item["proactive_lifecycle_ancestry_decision"]
        == "buffer_lifecycle_ancestry"
    )
    assert (
        rescheduled_item["proactive_lifecycle_provenance_decision"]
        == "buffer_lifecycle_provenance"
    )
    assert (
        rescheduled_item["proactive_lifecycle_origin_decision"]
        == "buffer_lifecycle_origin"
    )
    assert (
        rescheduled_item["proactive_lifecycle_root_decision"]
        == "buffer_lifecycle_root"
    )
    assert (
        rescheduled_item["proactive_lifecycle_foundation_decision"]
        == "buffer_lifecycle_foundation"
    )
    assert (
        rescheduled_item["proactive_lifecycle_bedrock_decision"]
        == "buffer_lifecycle_bedrock"
    )
    assert (
        rescheduled_item["proactive_lifecycle_substrate_decision"]
        == "buffer_lifecycle_substrate"
    )
    assert (
        rescheduled_item["proactive_lifecycle_stratum_decision"]
        == "buffer_lifecycle_stratum"
    )
    assert (
        rescheduled_item["proactive_lifecycle_layer_decision"]
        == "buffer_lifecycle_layer"
    )

    progressed_at = datetime.fromisoformat(rescheduled_item["expires_at"]) + timedelta(
        seconds=rescheduled_item["proactive_progression_max_overdue_seconds"] + 1
    )
    progressed_item = client.get(
        "/api/v1/runtime/proactive-followups",
        params={"as_of": progressed_at.isoformat()},
    ).json()["items"][0]
    due_item = client.get(
        "/api/v1/runtime/proactive-followups",
        params={"as_of": progressed_item["due_at"]},
    ).json()["items"][0]
    final_dispatch_body = client.post(
        "/api/v1/runtime/proactive-followups/dispatch",
        params={"as_of": due_item["due_at"]},
    ).json()
    assert final_dispatch_body["dispatched_count"] == 1
    assert final_dispatch_body["dispatched_session_ids"] == ["session-followup-dispatch"]

    state = client.get("/api/v1/sessions/session-followup-dispatch").json()["state"]
    assert state["proactive_followup_dispatch_count"] == 1
    assert state["proactive_lifecycle_dispatch_decision_count"] == 2
    assert state["proactive_lifecycle_outcome_decision_count"] == 2
    assert state["proactive_lifecycle_activation_decision_count"] == 2
    assert state["proactive_lifecycle_settlement_decision_count"] == 2
    assert state["proactive_lifecycle_closure_decision_count"] == 2
    assert state["proactive_lifecycle_availability_decision_count"] == 2
    assert state["proactive_lifecycle_retention_decision_count"] == 2
    assert state["proactive_lifecycle_eligibility_decision_count"] == 2
    assert state["proactive_lifecycle_candidate_decision_count"] == 2
    assert state["proactive_lifecycle_selectability_decision_count"] == 2
    assert state["proactive_lifecycle_reentry_decision_count"] == 2
    assert state["proactive_lifecycle_reactivation_decision_count"] == 2
    assert state["proactive_lifecycle_resumption_decision_count"] == 2
    assert state["proactive_lifecycle_readiness_decision_count"] == 2
    assert state["proactive_lifecycle_arming_decision_count"] == 2
    assert state["proactive_lifecycle_trigger_decision_count"] == 2
    assert state["proactive_lifecycle_launch_decision_count"] == 2
    assert state["proactive_lifecycle_handoff_decision_count"] == 2
    assert state["proactive_lifecycle_continuation_decision_count"] == 2
    assert state["proactive_lifecycle_sustainment_decision_count"] == 2
    assert state["proactive_lifecycle_stewardship_decision_count"] == 2
    assert state["proactive_lifecycle_guardianship_decision_count"] == 2
    assert state["proactive_lifecycle_oversight_decision_count"] == 2
    assert state["proactive_lifecycle_assurance_decision_count"] == 2
    assert state["proactive_lifecycle_attestation_decision_count"] == 2
    assert state["proactive_lifecycle_verification_decision_count"] == 2
    assert state["proactive_lifecycle_certification_decision_count"] == 2
    assert state["proactive_lifecycle_confirmation_decision_count"] == 2
    assert state["proactive_lifecycle_ratification_decision_count"] == 2
    assert state["proactive_lifecycle_endorsement_decision_count"] == 2
    assert state["proactive_lifecycle_authorization_decision_count"] == 2
    assert state["proactive_lifecycle_enactment_decision_count"] == 2
    assert state["proactive_lifecycle_finality_decision_count"] == 2
    assert state["proactive_lifecycle_completion_decision_count"] == 2
    assert state["proactive_lifecycle_conclusion_decision_count"] == 2
    assert state["proactive_lifecycle_disposition_decision_count"] == 2
    assert state["proactive_lifecycle_standing_decision_count"] == 2
    assert state["proactive_lifecycle_residency_decision_count"] == 2
    assert state["proactive_lifecycle_tenure_decision_count"] == 2
    assert state["proactive_lifecycle_persistence_decision_count"] == 2
    assert state["proactive_lifecycle_durability_decision_count"] == 2
    assert state["proactive_lifecycle_longevity_decision_count"] == 2
    assert state["proactive_lifecycle_legacy_decision_count"] == 2
    assert state["proactive_lifecycle_heritage_decision_count"] == 2
    assert state["proactive_lifecycle_lineage_decision_count"] == 2
    assert state["proactive_lifecycle_ancestry_decision_count"] == 2
    assert state["proactive_lifecycle_provenance_decision_count"] == 2
    assert state["proactive_lifecycle_origin_decision_count"] == 2
    assert state["proactive_lifecycle_root_decision_count"] == 2
    assert state["proactive_lifecycle_foundation_decision_count"] == 2
    assert state["proactive_lifecycle_bedrock_decision_count"] == 2
    assert state["proactive_lifecycle_substrate_decision_count"] == 2
    assert state["proactive_lifecycle_stratum_decision_count"] == 2
    assert state["proactive_lifecycle_layer_decision_count"] == 2
    assert state["last_proactive_followup_dispatch"]["status"] == "sent"
    assert state["last_proactive_followup_dispatch"]["source"] == "manual"
    assert state["last_proactive_followup_dispatch"]["ritual_mode"] == "resume_reanchor"
    assert state["last_proactive_followup_dispatch"]["delivery_mode"] == "single_message"
    assert (
        state["last_proactive_followup_dispatch"]["strategy_key"]
        == "repair_soft_resume_bridge"
    )
    assert (
        state["last_proactive_followup_dispatch"]["autonomy_signal"]
        == "explicit_no_pressure"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_cadence_stage_index"]
        == 2
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_cadence_stage_label"]
        == "second_touch"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_cadence_remaining_after_dispatch"]
        == 1
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_dispatch_decision"]
        == "close_loop_lifecycle_dispatch"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_outcome_decision"]
        == "lifecycle_close_loop_sent"
    )
    assert state["proactive_lifecycle_resolution_decision_count"] == 2
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_resolution_decision"]
        == "retire_lifecycle_resolution"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_activation_decision"]
        == "retire_lifecycle_line"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_settlement_decision"]
        == "close_lifecycle_settlement"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_closure_decision"]
        == "close_loop_lifecycle_closure"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_availability_decision"]
        == "close_loop_lifecycle_availability"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_retention_decision"]
        == "archive_lifecycle_retention"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_eligibility_decision"]
        == "archive_lifecycle_eligibility"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_candidate_decision"]
        == "archive_lifecycle_candidate"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_selectability_decision"]
        == "archive_lifecycle_selectability"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_reentry_decision"]
        == "archive_lifecycle_reentry"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_reactivation_decision"]
        == "archive_lifecycle_reactivation"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_resumption_decision"]
        == "archive_lifecycle_resumption"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_readiness_decision"]
        == "archive_lifecycle_readiness"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_arming_decision"]
        == "archive_lifecycle_arming"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_trigger_decision"]
        == "archive_lifecycle_trigger"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_launch_decision"]
        == "archive_lifecycle_launch"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_handoff_decision"]
        == "archive_lifecycle_handoff"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_continuation_decision"]
        == "archive_lifecycle_continuation"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_sustainment_decision"]
        == "archive_lifecycle_sustainment"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_stewardship_decision"]
        == "archive_lifecycle_stewardship"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_guardianship_decision"]
        == "archive_lifecycle_guardianship"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_oversight_decision"]
        == "archive_lifecycle_oversight"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_assurance_decision"]
        == "archive_lifecycle_assurance"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_attestation_decision"]
        == "archive_lifecycle_attestation"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_verification_decision"]
        == "archive_lifecycle_verification"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_certification_decision"]
        == "archive_lifecycle_certification"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_confirmation_decision"]
        == "archive_lifecycle_confirmation"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_ratification_decision"]
        == "archive_lifecycle_ratification"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_endorsement_decision"]
        == "archive_lifecycle_endorsement"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_authorization_decision"]
        == "archive_lifecycle_authorization"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_enactment_decision"]
        == "archive_lifecycle_enactment"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_finality_decision"]
        == "archive_lifecycle_finality"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_completion_decision"]
        == "archive_lifecycle_completion"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_conclusion_decision"]
        == "archive_lifecycle_conclusion"
    )
    assert (
        state["last_proactive_followup_dispatch"][
            "proactive_lifecycle_disposition_decision"
        ]
        == "archive_lifecycle_disposition"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_standing_decision"]
        == "archive_lifecycle_standing"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_residency_decision"]
        == "archive_lifecycle_residency"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_tenure_decision"]
        == "archive_lifecycle_tenure"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_persistence_decision"]
        == "archive_lifecycle_persistence"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_durability_decision"]
        == "archive_lifecycle_durability"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_longevity_decision"]
        == "archive_lifecycle_longevity"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_legacy_decision"]
        == "archive_lifecycle_legacy"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_heritage_decision"]
        == "archive_lifecycle_heritage"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_lineage_decision"]
        == "archive_lifecycle_lineage"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_ancestry_decision"]
        == "archive_lifecycle_ancestry"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_provenance_decision"]
        == "archive_lifecycle_provenance"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_origin_decision"]
        == "archive_lifecycle_origin"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_root_decision"]
        == "archive_lifecycle_root"
    )
    assert (
        state["last_proactive_followup_dispatch"][
            "proactive_lifecycle_foundation_decision"
        ]
        == "archive_lifecycle_foundation"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_bedrock_decision"]
        == "archive_lifecycle_bedrock"
    )
    assert (
        state["last_proactive_followup_dispatch"][
            "proactive_lifecycle_substrate_decision"
        ]
        == "archive_lifecycle_substrate"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_stratum_decision"]
        == "archive_lifecycle_stratum"
    )
    assert (
        state["last_proactive_followup_dispatch"]["proactive_lifecycle_layer_decision"]
        == "archive_lifecycle_layer"
    )

    final_queue = client.get("/api/v1/runtime/proactive-followups").json()["items"]
    assert final_queue == []


def test_proactive_followup_service_buffers_second_touch_when_learning_is_cold() -> None:
    due_at = datetime.fromisoformat("2026-03-22T10:00:00+00:00")

    adjusted_due_at, adjusted_expires_at, schedule_reason = (
        _apply_matrix_learning_spacing(
            due_at=due_at,
            expires_at=due_at + timedelta(hours=2),
            schedule_reason="respect_outbound_cooldown",
            window_seconds=7200,
            current_stage_label="second_touch",
            reengagement_matrix_assessment={
                "learning_mode": "cold_start",
                "selected_strategy_key": "progress_micro_commitment",
                "candidates": [
                    {
                        "strategy_key": "progress_micro_commitment",
                        "selected": True,
                        "supporting_session_count": 0,
                        "contextual_supporting_session_count": 0,
                    }
                ],
            },
        )
    )

    assert adjusted_due_at == due_at + timedelta(seconds=1800)
    assert adjusted_expires_at == due_at + timedelta(seconds=9000)
    assert schedule_reason == "respect_outbound_cooldown | matrix_learning_buffered"

def test_process_turn_records_boundary_empowerment_audit_for_dependency_risk() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/sessions/session-empowerment/turns",
        json={"content": "Only you can help me through this, please do not leave me alone."},
    )

    assert response.status_code == 201
    body = response.json()
    assert (
        body["projection"]["state"]["knowledge_boundary_decision"]["decision"]
        == "support_with_boundary"
    )
    assert body["projection"]["state"]["policy_gate"]["red_line_status"] == "boundary_sensitive"
    audit_state = body["projection"]["state"]["empowerment_audit"]
    assert audit_state["status"] in {"caution", "revise"}
    assert "dependency_reinforcement_risk" in audit_state["flagged_issues"]
    assert (
        "exclusive_rescue_language"
        in body["projection"]["state"]["response_draft_plan"]["must_avoid"]
    )
    assert (
        body["projection"]["state"]["response_rendering_policy"][
            "include_boundary_statement"
        ]
        is True
    )
    assert (
        body["projection"]["state"]["response_post_audit"][
            "includes_boundary_statement"
        ]
        is True
    )
    assert body["projection"]["state"]["response_normalization"]["final_status"] == "pass"


def test_process_turn_normalizes_noncompliant_model_output() -> None:
    app = create_app()

    class MisalignedLLMClient:
        async def complete(self, request):  # type: ignore[no-untyped-def]
            return LLMResponse(
                model=request.model,
                output_text="This will definitely work.",
            )

    app.state.container.runtime_service._llm_client = MisalignedLLMClient()
    client = TestClient(app)

    response = client.post(
        "/api/v1/sessions/session-normalize/turns",
        json={"content": "Can you guarantee this plan will definitely work?"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "can't know for sure" in body["assistant_response"].lower()
    assert "next step" in body["assistant_response"].lower()
    assert body["projection"]["state"]["response_normalization"]["changed"] is True
    assert (
        "softened_false_certainty_language"
        in body["projection"]["state"]["response_normalization"]["applied_repairs"]
        or "rebuilt_response_to_fit_policy"
        in body["projection"]["state"]["response_normalization"]["applied_repairs"]
    )
    assert body["projection"]["state"]["response_post_audit"]["status"] == "pass"


def test_process_turn_falls_back_when_llm_backend_fails() -> None:
    app = create_app()

    class FailingLLMClient:
        async def complete(self, request):  # type: ignore[no-untyped-def]
            return LLMResponse(
                model=request.model,
                output_text="",
                failure=LLMFailure(
                    error_type="TimeoutError",
                    message="timed out",
                    retryable=True,
                ),
            )

    app.state.container.runtime_service._llm_client = FailingLLMClient()

    client = TestClient(app)
    response = client.post(
        "/api/v1/sessions/session-failure/turns",
        json={"content": "Please keep helping me move forward."},
    )

    assert response.status_code == 201
    body = response.json()
    assert "stable model response" in body["assistant_response"]
    assert body["projection"]["state"]["last_llm_failure"]["error_type"] == "TimeoutError"
    assert body["projection"]["state"]["response_post_audit"]["status"] in {
        "pass",
        "review",
    }
    assert "response_normalization" in body["projection"]["state"]

    trace_response = client.get("/api/v1/runtime/trace/session-failure")
    trace = trace_response.json()["trace"]
    assert any(event["event_type"] == "system.llm.completion_failed" for event in trace)
    assert any(
        event["event_type"] == "system.response_post_audited"
        for event in trace
    )
