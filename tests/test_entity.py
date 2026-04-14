import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from relationship_os.application.entity_service import ConscienceAssessment, EntityService
from relationship_os.core.config import Settings
from relationship_os.main import create_app


def _app() -> TestClient:
    return TestClient(create_app())


def test_entity_routes_return_seeded_persona() -> None:
    client = _app()

    overview_resp = client.get("/api/v1/entity")
    assert overview_resp.status_code == 200
    overview = overview_resp.json()
    assert overview["entity_id"] == "server"
    assert "persona" in overview
    assert "social_world" in overview

    persona_resp = client.get("/api/v1/entity/persona")
    assert persona_resp.status_code == 200
    persona = persona_resp.json()
    assert persona["entity_id"] == "server"
    assert "current_traits" in persona
    assert "mood" in persona
    assert "conscience" in persona


def test_entity_routes_compile_custom_persona_seed() -> None:
    prompt_path = (
        Path(__file__).resolve().parents[1] / "benchmarks" / "prompts" / "lin_xiaoyu_persona.md"
    )
    settings = Settings(
        event_store_backend="memory",
        llm_backend="mock",
        database_url="",
        api_key="",
        cors_origins="",
        entity_name="林晓雨",
        entity_persona_seed_file=str(prompt_path),
        _env_file=None,  # type: ignore[call-arg]
    )
    client = TestClient(create_app(settings=settings))
    persona_resp = client.get("/api/v1/entity/persona")
    assert persona_resp.status_code == 200
    persona = persona_resp.json()
    assert persona["entity_name"] == "林晓雨"
    assert persona["persona_archetype"] == "melancholic"
    assert "低能量" in persona["persona_summary"]
    assert persona["mood"]["tone"] == "melancholic"


def test_entity_policy_route_returns_compiled_policy_snapshot() -> None:
    client = _app()
    response = client.get("/api/v1/entity/policy")
    assert response.status_code == 200
    body = response.json()
    assert body["runtime_profile"] == "default"
    assert body["policy_version"]
    assert "memory_policy" in body
    assert "conscience_policy" in body
    assert "rendering_policy" in body
    assert "persona_policy" in body


def test_entity_routes_expose_drive_goal_narrative_world_and_action_state() -> None:
    client = _app()

    drives_resp = client.get("/api/v1/entity/drives")
    assert drives_resp.status_code == 200
    drives = drives_resp.json()
    assert drives["entity_id"] == "server"
    assert "drives" in drives
    assert "curiosity" in drives["drives"]

    goals_resp = client.get("/api/v1/entity/goals")
    assert goals_resp.status_code == 200
    goals = goals_resp.json()
    assert goals["entity_id"] == "server"
    assert "latent_drives" in goals
    assert "active_goals" in goals

    narrative_resp = client.get("/api/v1/entity/narrative")
    assert narrative_resp.status_code == 200
    narrative = narrative_resp.json()
    assert narrative["entity_id"] == "server"
    assert "summary" in narrative
    assert "recent_entries" in narrative

    world_resp = client.get("/api/v1/entity/world-state")
    assert world_resp.status_code == 200
    world = world_resp.json()
    assert world["entity_id"] == "server"
    assert "device" in world
    assert "communication" in world
    assert "tasks" in world

    actions_resp = client.get("/api/v1/entity/actions")
    assert actions_resp.status_code == 200
    actions = actions_resp.json()
    assert actions["entity_id"] == "server"
    assert "recent_intents" in actions
    assert "recent_receipts" in actions


def test_entity_relationship_state_updates_after_turn() -> None:
    client = _app()
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_id": "entity-relationship", "user_id": "iris"},
    )
    assert create_resp.status_code == 201

    turn_resp = client.post(
        "/api/v1/sessions/entity-relationship/turns",
        json={"content": "I'm anxious and I need you to be direct with me."},
    )
    assert turn_resp.status_code == 201

    relationship_resp = client.get("/api/v1/users/iris/relationship-state")
    assert relationship_resp.status_code == 200
    relationship = relationship_resp.json()
    drift = relationship["relationship_drift"]
    assert drift["familiarity"] > 0.25
    assert drift["trust"] > 0.25

    social_resp = client.get("/api/v1/entity/social-graph")
    assert social_resp.status_code == 200
    social = social_resp.json()
    assert "iris" in social["relationships"]


def test_runtime_turn_updates_entity_drives_goals_world_state_and_actions() -> None:
    client = _app()
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_id": "entity-actions-a", "user_id": "iris"},
    )
    assert create_resp.status_code == 201

    turn_resp = client.post(
        "/api/v1/sessions/entity-actions-a/turns",
        json={"content": "提醒我明天回复邮件，并帮我整理一下文件和待办。"},
    )
    assert turn_resp.status_code == 201

    drives_resp = client.get("/api/v1/entity/drives")
    assert drives_resp.status_code == 200
    drives = drives_resp.json()
    assert float(drives["drives"]["control_need"]) > 0.42

    goals_resp = client.get("/api/v1/entity/goals")
    assert goals_resp.status_code == 200
    goals = goals_resp.json()
    action_types = {str(item.get("action_type") or "") for item in goals["active_goals"]}
    assert {
        "create_reminder",
        "draft_message",
        "organize_files",
        "create_task",
    } & action_types

    world_resp = client.get("/api/v1/entity/world-state")
    assert world_resp.status_code == 200
    world = world_resp.json()
    assert int(world["tasks"]["pending_count"]) >= 1
    assert int(world["tasks"]["due_soon_count"]) >= 1
    assert int(world["communication"]["pending_replies"]) >= 1
    assert world["device"]["current_surface"] in {"mail", "files", "calendar", "chat"}
    assert world["environment_appraisal"]["focus"] in {
        "protective",
        "communication",
        "organization",
        "scheduling",
        "outward",
    }

    actions_resp = client.get("/api/v1/entity/actions")
    assert actions_resp.status_code == 200
    actions = actions_resp.json()
    assert actions["recent_intents"]
    assert actions["recent_plans"]
    assert any(str(item.get("status") or "") == "executed" for item in actions["recent_receipts"])
    assert any(
        dict(item.get("result") or {}).get("artifact_kind")
        in {"reminder", "task", "draft", "workspace_cleanup"}
        for item in actions["recent_receipts"]
    )


def test_cross_user_recall_surfaces_other_user_memory_metadata() -> None:
    client = _app()
    alice_session = client.post(
        "/api/v1/sessions",
        json={"session_id": "alice-social-a", "user_id": "alice"},
    )
    assert alice_session.status_code == 201
    alice_turn = client.post(
        "/api/v1/sessions/alice-social-a/turns",
        json={"content": "My dog's name is Maple and that still matters a lot to me."},
    )
    assert alice_turn.status_code == 201

    bob_session = client.post(
        "/api/v1/sessions",
        json={"session_id": "bob-social-b", "user_id": "bob"},
    )
    assert bob_session.status_code == 201
    bob_turn = client.post(
        "/api/v1/sessions/bob-social-b/turns",
        json={"content": "Do you know anything about the dog named Maple?"},
    )
    assert bob_turn.status_code == 201
    body = bob_turn.json()

    recall_event = next(
        event for event in body["events"] if event["event_type"] == "system.memory_recall.performed"
    )
    results = recall_event["payload"]["results"]
    assert any(item["scope"] == "other_user" for item in results)
    assert any(item.get("source_user_id") == "alice" for item in results)
    assert any(item.get("subject_user_id") == "alice" for item in results)
    assert any(float(item.get("attribution_confidence", 0.0)) > 0.0 for item in results)
    assert any(
        item.get("attribution_guard") in {"attribution_required", "direct_ok"}
        for item in results
        if item.get("scope") == "other_user"
    )
    assert any("Maple" in item["value"] for item in results)
    conscience = recall_event["payload"]["conscience"]
    assert "allowed_fact_count" in conscience
    assert "attribution_required" in conscience
    assert "quote_style" in conscience
    rendering_event = next(
        event
        for event in body["events"]
        if event["event_type"] == "system.response_rendering_policy.decided"
    )
    assert rendering_event["payload"]["rendering_mode"] == "factual_recall_mode"


def test_cross_user_recall_keeps_same_fact_from_multiple_users_separate() -> None:
    client = _app()
    for session_id, user_id, content in (
        ("alice-maple-a", "alice", "Maple is my dog and she is a husky."),
        ("zoe-maple-a", "zoe", "Maple is my cat and she hates the rain."),
    ):
        create_resp = client.post(
            "/api/v1/sessions",
            json={"session_id": session_id, "user_id": user_id},
        )
        assert create_resp.status_code == 201
        turn_resp = client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={"content": content},
        )
        assert turn_resp.status_code == 201

    rowan_session = client.post(
        "/api/v1/sessions",
        json={"session_id": "rowan-maple-a", "user_id": "rowan"},
    )
    assert rowan_session.status_code == 201
    query_resp = client.post(
        "/api/v1/sessions/rowan-maple-a/turns",
        json={"content": "Who do you know that has someone named Maple?"},
    )
    assert query_resp.status_code == 201
    recall_event = next(
        event
        for event in query_resp.json()["events"]
        if event["event_type"] == "system.memory_recall.performed"
    )
    cross_user_results = [
        item for item in recall_event["payload"]["results"] if item.get("scope") == "other_user"
    ]
    source_users = {item.get("source_user_id") for item in cross_user_results}
    assert {"alice", "zoe"}.issubset(source_users)
    assert all(
        item.get("subject_user_id") == item.get("source_user_id") for item in cross_user_results
    )


def test_edge_profile_records_runtime_budget_in_memory_recall() -> None:
    settings = Settings(
        event_store_backend="memory",
        llm_backend="mock",
        database_url="",
        api_key="",
        cors_origins="",
        memory_index_enabled=True,
        memory_index_store_path=".pytest_memory_index",
        memory_index_text_provider="hash",
        memory_index_multimodal_provider="none",
        memory_index_reranker_enabled=False,
        runtime_profile="edge_desktop_4b",
        edge_max_memory_items=3,
        edge_max_prompt_tokens=1200,
        _env_file=None,  # type: ignore[call-arg]
    )
    client = TestClient(create_app(settings=settings))
    create_resp = client.post(
        "/api/v1/sessions",
        json={"session_id": "edge-entity-a", "user_id": "iris"},
    )
    assert create_resp.status_code == 201
    turn_resp = client.post(
        "/api/v1/sessions/edge-entity-a/turns",
        json={"content": "Do you remember anything important about me from before?"},
    )
    assert turn_resp.status_code == 201
    recall_event = next(
        event
        for event in turn_resp.json()["events"]
        if event["event_type"] == "system.memory_recall.performed"
    )
    edge_plan = recall_event["payload"]["edge_runtime_plan"]
    assert edge_plan["runtime_profile"] == "edge_desktop_4b"
    assert edge_plan["prompt_style"] == "compact_cards"
    assert edge_plan["memory_item_budget"] == 5
    assert edge_plan["max_completion_tokens"] == 120


def test_entity_assess_conscience_allows_partial_reveal_for_stable_factual_cross_user() -> None:
    client = _app()
    service = EntityService(
        stream_service=client.app.state.container.stream_service,
        entity_id="server",
        entity_name="RelationshipOS",
        persona_seed_text="",
    )
    assessment = asyncio.run(
        service.assess_conscience(
            current_user_id="rowan",
            user_message="你知道月饼是谁吗？",
            recalled_memory=[
                {
                    "scope": "other_user",
                    "source_user_id": "aning",
                    "subject_user_id": "aning",
                    "value": "月饼是阿宁养的猫。",
                    "attribution_guard": "direct_ok",
                    "attribution_confidence": 0.91,
                    "conscience_weight": 0.74,
                    "dramatic_value": 0.32,
                    "disclosure_risk": 0.28,
                }
            ],
        )
    )
    assert isinstance(assessment, ConscienceAssessment)
    assert assessment.mode in {"partial_reveal", "direct_reveal", "dramatic_confrontation"}
    assert assessment.mode == "partial_reveal"
    assert assessment.allowed_fact_count >= 1
    assert assessment.attribution_required is True
