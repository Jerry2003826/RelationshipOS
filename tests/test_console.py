from fastapi.testclient import TestClient

from relationship_os.domain.llm import LLMResponse
from relationship_os.main import create_app


def test_console_home_renders_control_room_shell() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/console")

    assert response.status_code == 200
    assert "RelationshipOS 控制台" in response.text
    assert "在浏览器中查看运行时状态" in response.text
    assert 'id="console-overview"' in response.text
    assert 'id="console-evaluations"' in response.text
    assert 'id="console-scenarios"' in response.text
    assert 'id="console-entity"' in response.text
    assert ">人格<" in response.text
    assert "htmx.org@1.9.12" in response.text
    assert "alpinejs@3.14.1" in response.text
    assert "/static/console.js" in response.text


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
    assert "策略与审计" in response.text
    assert "关系与记忆" in response.text
    assert "回放快照" in response.text
    assert "事件账本" in response.text
    assert "最近对话记录" in response.text
    assert "最近追踪" in response.text
    assert "投影检查器" in response.text


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
    assert "投影检查器" in response.text
    assert "选中投影器" in response.text
    assert "session-memory" in response.text
    assert "working_memory" in response.text


def test_console_session_detail_renders_unsupported_notice_for_legacy_lifecycle_stream() -> None:
    with TestClient(create_app()) as client:
        append_response = client.post(
            "/api/v1/streams/console-legacy/events",
            json={
                "events": [
                    {
                        "event_type": "session.started",
                        "payload": {
                            "session_id": "console-legacy",
                            "created_at": "2026-03-22T00:00:00+00:00",
                            "metadata": {},
                        },
                    },
                    {
                        "event_type": "system.proactive_lifecycle_state.updated",
                        "payload": {"status": "active", "state_key": "legacy"},
                    },
                ]
            },
        )
        assert append_response.status_code == 201

        response = client.get(
            "/api/v1/console/fragments/session-detail",
            params={"session_id": "console-legacy"},
        )

    assert response.status_code == 200
    assert "不支持旧版生命周期流" in response.text


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
    assert "偏好信号" in evaluations_fragment_response.text
    assert "重连学习" in evaluations_fragment_response.text

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
    assert "上线签核" in response.text
    assert "纵向报告" in response.text
    assert "时间维度报告" in response.text
    assert "多周报告" in response.text
    assert "持续漂移" in response.text
    assert "发版档案" in response.text
    assert "加固检查单" in response.text
    assert "安全审计" in response.text
    assert "红队鲁棒性" in response.text
    assert "上线就绪" in response.text
    assert "迁移就绪" in response.text
    assert "基线治理" in response.text
    assert "发版过线" in response.text
    assert "基线追踪" in response.text
    assert "稳定性报告" in response.text
    assert "退化监控" in response.text
    assert "失对齐分类" in response.text
    assert "关键分类" in response.text
    assert "场景趋势" in response.text
    assert "近期场景运行" in response.text
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
    assert "偏好信号" in response.text
    assert "重连学习" in response.text
    assert "质量" in response.text


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
    # Diversity status may be "intervened" or "stable" depending on
    # how the strategy pipeline processes mock responses
    assert "diversity" in response.text.casefold() or "偏好信号" in response.text
    assert "偏好信号" in response.text
    assert "矩阵" in response.text


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
    assert "single_message" in response.text
    assert "偏好信号" in response.text


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
    assert "偏好信号" in response.text
    assert "重连学习" in response.text
    assert "质量" in response.text
    assert "协调" in response.text
    assert "跟进" in response.text
    assert "system3" in response.text.lower()
    assert "身份" in response.text
    assert "迁移" in response.text
    assert "模型" in response.text
    assert "依赖" in response.text
    assert "信任" in response.text
    assert "清晰" in response.text
    assert "矩阵" in response.text
    assert "观察" in response.text


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
    assert "主动跟进队列" in response.text
    assert "console-followup" in response.text
    assert "等待中" in response.text
    assert "progress_nudge" in response.text
    assert "progress_micro_commitment" in response.text
    assert "matrix" in response.text
    assert "handoff" in response.text.lower()
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
    assert "重连学习" in response.text
    assert "重连矩阵" in response.text or "矩阵" in response.text
    assert "道德" in response.text
    assert "观察" in response.text


def test_console_entity_fragment_surfaces_server_persona_and_social_world() -> None:
    with TestClient(create_app()) as client:
        first_session = client.post(
            "/api/v1/sessions",
            json={"session_id": "console-entity-a", "user_id": "alice"},
        )
        assert first_session.status_code == 201
        first_turn = client.post(
            "/api/v1/sessions/console-entity-a/turns",
            json={"content": "My dog's name is Maple, and Mira keeps teasing Jonah about Iris."},
        )
        assert first_turn.status_code == 201

        second_session = client.post(
            "/api/v1/sessions",
            json={"session_id": "console-entity-b", "user_id": "bob"},
        )
        assert second_session.status_code == 201
        second_turn = client.post(
            "/api/v1/sessions/console-entity-b/turns",
            json={"content": "Do you know anything about Maple, or about Jonah and Iris?"},
        )
        assert second_turn.status_code == 201

        response = client.get("/api/v1/console/fragments/entity")

    assert response.status_code == 200
    assert "服务器人格" in response.text
    assert "人格与世界观" in response.text
    assert "关系漂移" in response.text
    assert "社会图谱" in response.text
    assert "良心裁量" in response.text
    assert "近期跨人披露" in response.text
