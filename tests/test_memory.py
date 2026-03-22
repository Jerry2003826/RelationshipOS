from fastapi.testclient import TestClient

from relationship_os.main import create_app


def test_session_memory_projection_tracks_layered_memory_across_turns() -> None:
    with TestClient(create_app()) as client:
        first_turn = client.post(
            "/api/v1/sessions/memory-session/turns",
            json={"content": "I feel anxious, but I still want to keep the plan moving."},
        )
        assert first_turn.status_code == 201
        second_turn = client.post(
            "/api/v1/sessions/memory-session/turns",
            json={"content": "Please give me the next planning step in a calmer tone."},
        )
        assert second_turn.status_code == 201

        memory_response = client.get("/api/v1/sessions/memory-session/memory")
        assert memory_response.status_code == 200
        memory_projection = memory_response.json()
        graph_response = client.get("/api/v1/sessions/memory-session/memory/graph")
        assert graph_response.status_code == 200
        graph_projection = graph_response.json()

    assert memory_projection["projector"] == {"name": "session-memory", "version": "v1"}
    state = memory_projection["state"]
    assert state["memory_turn_count"] == 2
    assert state["working_memory"]["history_count"] == 2
    assert state["working_memory"]["current"]
    assert state["episodic_memory"]["episode_count"] == 2
    assert any(
        concept["value"] == "topic:planning"
        for concept in state["semantic_memory"]["concepts"]
    )
    assert state["relational_memory"]["signal_count"] >= 1
    assert state["reflective_memory"]["insight_count"] >= 1
    assert graph_projection["projector"] == {
        "name": "session-temporal-kg",
        "version": "v1",
    }
    graph_state = graph_projection["state"]
    assert graph_state["node_count"] >= 4
    assert graph_state["edge_count"] >= 3
    assert any(node["label"] == "topic:planning" for node in graph_state["nodes"])
    assert any(edge["relation"] == "focuses_on" for edge in graph_state["edges"])


def test_session_memory_recall_returns_ranked_matches() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/v1/sessions/recall-session/turns",
            json={"content": "I feel anxious, but I want to keep the plan moving."},
        )
        client.post(
            "/api/v1/sessions/recall-session/turns",
            json={"content": "Please help me keep the next step gentle and structured."},
        )

        recall_response = client.get(
            "/api/v1/sessions/recall-session/memory/recall",
            params={"query": "anxious", "limit": 4},
        )
        assert recall_response.status_code == 200
        recall = recall_response.json()

    assert recall["session_id"] == "recall-session"
    assert recall["memory_turn_count"] == 2
    assert recall["recall_count"] >= 1
    assert recall["graph_summary"]["node_count"] >= 1
    assert recall["graph_summary"]["edge_count"] >= 1
    assert recall["graph_summary"]["matched_node_count"] >= 1
    assert recall["graph_summary"]["bridge_count"] >= 1
    assert recall["integrity_summary"]["checked_count"] >= recall["recall_count"]
    assert recall["matched_nodes"]
    assert recall["bridges"]
    top_result = recall["results"][0]
    assert top_result["layer"] in {"working_memory", "episodic_memory"}
    assert "anxious" in top_result["value"].lower()
    assert top_result["score"] > 0
    assert top_result["provenance"]["source_version"] is not None
    assert "pinned" in top_result["provenance"]
    assert top_result["integrity"]["status"] == "accepted"
    assert top_result["integrity"]["score"] > 0.6


def test_session_memory_recall_filters_context_mismatches_when_requested() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/v1/sessions/integrity-session/turns",
            json={"content": "I want to keep the plan moving even though I feel anxious."},
        )
        client.post(
            "/api/v1/sessions/integrity-session/turns",
            json={"content": "Please keep the planning step calm and explicit."},
        )

        recall_response = client.get(
            "/api/v1/sessions/integrity-session/memory/recall",
            params={
                "query": "plan",
                "topic": "relationship",
                "include_filtered": True,
                "limit": 5,
            },
        )
        assert recall_response.status_code == 200
        recall = recall_response.json()

    assert recall["integrity_summary"]["filtered_count"] >= 1
    assert recall["filtered_results"]
    assert any(
        "topic_mismatch" in item["integrity"]["flags"]
        for item in recall["filtered_results"]
    )


def test_session_memory_projection_tracks_controlled_forgetting_after_history_limit() -> None:
    with TestClient(create_app()) as client:
        for turn_index in range(7):
            response = client.post(
                "/api/v1/sessions/forgetting-session/turns",
                json={
                    "content": (
                        f"Please keep plan step {turn_index} calm, explicit, and moving "
                        "forward with a stable next action."
                    )
                },
            )
            assert response.status_code == 201

        memory_response = client.get("/api/v1/sessions/forgetting-session/memory")
        assert memory_response.status_code == 200
        memory_projection = memory_response.json()
        evaluation_response = client.get("/api/v1/evaluations/sessions/forgetting-session")
        assert evaluation_response.status_code == 200
        evaluation = evaluation_response.json()

    state = memory_projection["state"]
    assert state["memory_turn_count"] == 7
    assert state["working_memory"]["history_count"] == 7
    assert len(state["working_memory"]["history"]) == 6
    assert state["forgetting_turn_count"] >= 1
    assert state["total_evicted_count"] >= 1
    assert state["last_forgetting"]["layers"]["working_memory"]["evicted_count"] >= 1
    assert (
        evaluation["summary"]["memory_forgetting_turn_count"] >= 1
    )
    assert (
        evaluation["summary"]["memory_forgetting_evicted_count"] >= 1
    )


def test_pinned_emotional_memory_survives_when_history_overflows() -> None:
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/sessions/pinned-memory-session/turns",
            json={
                "content": "I feel anxious and alone, but I still want to keep the plan moving."
            },
        )
        assert first_response.status_code == 201

        for turn_index in range(6):
            response = client.post(
                "/api/v1/sessions/pinned-memory-session/turns",
                json={
                    "content": (
                        f"Please continue with plan step {turn_index} in a calm, direct way."
                    )
                },
            )
            assert response.status_code == 201

        memory_response = client.get("/api/v1/sessions/pinned-memory-session/memory")
        assert memory_response.status_code == 200
        state = memory_response.json()["state"]

    working_history = state["working_memory"]["history"]
    assert len(working_history) == 6
    assert any(entry["pinned"] for entry in working_history)
    assert any(
        any("anxious and alone" in item.lower() for item in entry["items"])
        for entry in working_history
    )
    assert state["last_retention_policy"]["pinned_count"] >= 1
    assert state["pinned_item_count"] >= 1
