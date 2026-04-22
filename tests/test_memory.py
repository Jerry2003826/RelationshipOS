import asyncio

import httpx
from fastapi.testclient import TestClient

from relationship_os.application.memory_index import (
    AliyunTextEmbedder,
    FileBackedMemoryIndex,
    MemoryIndexRecord,
)
from relationship_os.application.memory_service import MemoryService
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
        concept["value"] == "topic:planning" for concept in state["semantic_memory"]["concepts"]
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
        "topic_mismatch" in item["integrity"]["flags"] for item in recall["filtered_results"]
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
    assert evaluation["summary"]["memory_forgetting_turn_count"] >= 1
    assert evaluation["summary"]["memory_forgetting_evicted_count"] >= 1


def test_pinned_emotional_memory_survives_when_history_overflows() -> None:
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/sessions/pinned-memory-session/turns",
            json={"content": "I feel anxious and alone, but I still want to keep the plan moving."},
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


def test_person_memory_recall_enters_foundation_across_sessions() -> None:
    with TestClient(create_app()) as client:
        create_first = client.post(
            "/api/v1/sessions",
            json={"session_id": "person-memory-a", "user_id": "memory-user"},
        )
        assert create_first.status_code == 201
        first_turn = client.post(
            "/api/v1/sessions/person-memory-a/turns",
            json={"content": "My dog's name is Maple and I grew up in Austin."},
        )
        assert first_turn.status_code == 201

        create_second = client.post(
            "/api/v1/sessions",
            json={"session_id": "person-memory-b", "user_id": "memory-user"},
        )
        assert create_second.status_code == 201
        second_turn = client.post(
            "/api/v1/sessions/person-memory-b/turns",
            json={"content": "What's my dog's name again?"},
        )
        assert second_turn.status_code == 201
        body = second_turn.json()

    memory_recall_event = next(
        event for event in body["events"] if event["event_type"] == "system.memory_recall.performed"
    )
    recall = memory_recall_event["payload"]
    assert recall["recall_count"] >= 1
    assert any(item["scope"] == "self_user" for item in recall["results"])
    assert any("maple" in item["value"].lower() for item in recall["results"])


def test_aliyun_text_embedder_batches_requests_to_provider_limit(
    monkeypatch,
) -> None:
    requests: list[dict[str, object]] = []

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            texts = list(json["input"]["texts"])  # type: ignore[index]
            requests.append({"url": url, "texts": texts})
            embeddings = [
                {"text_index": index, "embedding": [float(index + 1), float(len(text))]}
                for index, text in enumerate(texts)
            ]
            return httpx.Response(
                200,
                json={"output": {"embeddings": embeddings}},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)

    embedder = AliyunTextEmbedder(
        model="text-embedding-v4",
        api_key="test-key",
        api_base="https://dashscope.aliyuncs.com/api/v1",
        dimensions=0,
    )

    vectors = asyncio.run(embedder.embed_texts([f"memory item {index}" for index in range(23)]))

    assert len(vectors) == 23
    assert [len(request["texts"]) for request in requests] == [10, 10, 3]
    assert requests[0]["url"] == (
        "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    )


def test_file_backed_memory_index_reuses_existing_vectors(tmp_path) -> None:
    class _FakeTextEmbedder:
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            self.calls.append(list(texts))
            return [[float(len(text)), float(index + 1)] for index, text in enumerate(texts)]

    embedder = _FakeTextEmbedder()
    index = FileBackedMemoryIndex(
        root_path=str(tmp_path / "memory-index"),
        text_embedder=embedder,
        multimodal_embedder=None,
        reranker=None,
    )

    first_records = [
        MemoryIndexRecord(
            record_id="r1",
            scope_id="user:test",
            user_id="test",
            session_id="s1",
            layer="semantic_memory",
            memory_kind="persistent",
            text="I grew up in Austin.",
            normalized_key="grew up austin",
        ),
        MemoryIndexRecord(
            record_id="r2",
            scope_id="user:test",
            user_id="test",
            session_id="s1",
            layer="relational_memory",
            memory_kind="persistent",
            text="I have a dog named Maple.",
            normalized_key="dog maple",
        ),
    ]
    second_records = [
        first_records[0],
        MemoryIndexRecord(
            record_id="r2",
            scope_id="user:test",
            user_id="test",
            session_id="s1",
            layer="relational_memory",
            memory_kind="persistent",
            text="I have a golden retriever named Maple.",
            normalized_key="dog maple",
        ),
    ]

    asyncio.run(index.write_many(scope_id="user:test", text_records=first_records))
    asyncio.run(index.write_many(scope_id="user:test", text_records=second_records))

    assert embedder.calls == [
        ["I grew up in Austin.", "I have a dog named Maple."],
        ["I have a golden retriever named Maple."],
    ]
    hits = asyncio.run(
        index.search(scope_id="user:test", query="Austin Maple", limit=4, use_reranker=False)
    )
    assert {hit.record.record_id for hit in hits} == {"r1", "r2"}


def test_file_backed_memory_index_caches_repeated_query_embeddings(tmp_path) -> None:
    class _FakeTextEmbedder:
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            self.calls.append(list(texts))
            return [[float(len(text)), float(index + 1)] for index, text in enumerate(texts)]

    embedder = _FakeTextEmbedder()
    index = FileBackedMemoryIndex(
        root_path=str(tmp_path / "memory-index"),
        text_embedder=embedder,
        multimodal_embedder=None,
        reranker=None,
    )
    record = MemoryIndexRecord(
        record_id="r1",
        scope_id="user:test",
        user_id="test",
        session_id="s1",
        layer="semantic_memory",
        memory_kind="persistent",
        text="I grew up in Austin.",
        normalized_key="grew up austin",
    )

    asyncio.run(index.write_many(scope_id="user:test", text_records=[record]))
    first_hits = asyncio.run(
        index.search(
            scope_id="user:test",
            query="Austin",
            limit=4,
            use_reranker=False,
        )
    )
    second_hits = asyncio.run(
        index.search(
            scope_id="user:test",
            query="Austin",
            limit=4,
            use_reranker=False,
        )
    )

    assert embedder.calls == [["I grew up in Austin."], ["Austin"]]
    assert [hit.record.record_id for hit in first_hits] == ["r1"]
    assert [hit.record.record_id for hit in second_hits] == ["r1"]


def test_file_backed_memory_index_tolerates_empty_scope_file(tmp_path) -> None:
    class _FakeTextEmbedder:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[float(len(text)), 1.0] for text in texts]

    index = FileBackedMemoryIndex(
        root_path=str(tmp_path / "memory-index"),
        text_embedder=_FakeTextEmbedder(),
        multimodal_embedder=None,
        reranker=None,
    )
    scope_path = index._scope_path("user:test")  # type: ignore[attr-defined]
    scope_path.write_text("", "utf-8")

    hits = asyncio.run(
        index.search(scope_id="user:test", query="Austin", limit=4, use_reranker=False)
    )

    assert hits == []


def test_file_backed_memory_index_recovers_from_corrupt_scope_file_on_write(tmp_path) -> None:
    class _FakeTextEmbedder:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[float(len(text)), float(index + 1)] for index, text in enumerate(texts)]

    index = FileBackedMemoryIndex(
        root_path=str(tmp_path / "memory-index"),
        text_embedder=_FakeTextEmbedder(),
        multimodal_embedder=None,
        reranker=None,
    )
    scope_path = index._scope_path("user:test")  # type: ignore[attr-defined]
    scope_path.write_text("{", "utf-8")

    record = MemoryIndexRecord(
        record_id="r1",
        scope_id="user:test",
        user_id="test",
        session_id="s1",
        layer="semantic_memory",
        memory_kind="persistent",
        text="I grew up in Austin.",
        normalized_key="grew up austin",
    )

    asyncio.run(index.write_many(scope_id="user:test", text_records=[record]))
    hits = asyncio.run(
        index.search(scope_id="user:test", query="Austin", limit=4, use_reranker=False)
    )

    assert [hit.record.record_id for hit in hits] == ["r1"]


def test_memory_service_detects_query_echo() -> None:
    service = object.__new__(MemoryService)
    assert service._looks_like_query_echo(
        query="Remind me where I grew up and my dog's name.",
        value="Remind me where I grew up and my dog's name.",
    )
    assert not service._looks_like_query_echo(
        query="Remind me where I grew up and my dog's name.",
        value="I have a golden retriever named Maple.",
    )


def test_person_memory_recall_filters_question_echo_from_results() -> None:
    with TestClient(create_app()) as client:
        assert (
            client.post(
                "/api/v1/sessions",
                json={"session_id": "echo-memory-a", "user_id": "echo-user"},
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/api/v1/sessions/echo-memory-a/turns",
                json={"content": "I grew up in Austin."},
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/api/v1/sessions/echo-memory-a/turns",
                json={"content": "I have a golden retriever named Maple."},
            ).status_code
            == 201
        )

        assert (
            client.post(
                "/api/v1/sessions",
                json={"session_id": "echo-memory-b", "user_id": "echo-user"},
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/api/v1/sessions/echo-memory-b/turns",
                json={"content": "Hey, I'm back after a few days."},
            ).status_code
            == 201
        )
        query = "Remind me where I grew up and my dog's name."
        response = client.post(
            "/api/v1/sessions/echo-memory-b/turns",
            json={"content": query},
        )
        assert response.status_code == 201
        body = response.json()

    memory_recall_event = next(
        event for event in body["events"] if event["event_type"] == "system.memory_recall.performed"
    )
    recall = memory_recall_event["payload"]
    lowered_query = query.casefold()
    assert all(item["value"].casefold() != lowered_query for item in recall["results"])


def test_memory_service_compact_index_prefers_durable_records() -> None:
    service = object.__new__(MemoryService)
    persistent_record = MemoryIndexRecord(
        record_id="persistent",
        scope_id="user:test",
        user_id="test",
        session_id="s1",
        layer="semantic_memory",
        memory_kind="persistent",
        text="I grew up in Austin.",
        normalized_key="grew up austin",
        importance_score=0.65,
        confidence_score=0.7,
    )
    soft_record = MemoryIndexRecord(
        record_id="soft",
        scope_id="user:test",
        user_id="test",
        session_id="s1",
        layer="working_memory",
        memory_kind="soft",
        text="I bought bread yesterday.",
        normalized_key="bought bread yesterday",
        importance_score=0.2,
        confidence_score=0.3,
    )

    assert service._should_keep_compact_index_record(persistent_record)
    assert not service._should_keep_compact_index_record(soft_record)


def test_memory_service_prefers_contentful_entity_candidates_over_guardrail_metadata() -> None:
    service = object.__new__(MemoryService)
    preferred = service._prefer_contentful_entity_candidates(
        candidates=[
            {"value": "psychological_safety:0.72"},
            {"value": "月饼是阿宁养的猫。"},
            {"value": "topic:general"},
        ]
    )
    values = [item["value"] for item in preferred]
    assert values == ["月饼是阿宁养的猫。"]


def test_memory_service_multilingual_tokenization_adds_shared_semantic_aliases() -> None:
    service = object.__new__(MemoryService)
    english_tokens = service._tokenize("I grew up in Austin and my dog's name is Maple.")
    chinese_tokens = service._tokenize("我在Austin长大，我的狗叫Maple。")

    assert "origin_grew_up" in english_tokens
    assert "origin_grew_up" in chinese_tokens
    assert "pet_dog" in english_tokens
    assert "pet_dog" in chinese_tokens
    assert "pet_name" in english_tokens
    assert "pet_name" in chinese_tokens


def test_memory_service_cross_lingual_symbolic_recall_scores_shared_fact_tokens() -> None:
    service = object.__new__(MemoryService)
    query = "你还记得我在哪里长大、我的狗叫什么吗？".lower()
    query_tokens = service._tokenize(query)
    score = service._score_candidate(
        query=query,
        query_tokens=query_tokens,
        candidate={
            "layer": "semantic_memory",
            "value": "I grew up in Austin and my dog's name is Maple.",
            "mention_count": 1,
            "pinned": False,
        },
        matched_node_labels=set(),
        bridge_labels=set(),
    )

    assert score > 0.0


def test_memory_service_extracts_only_stable_factual_candidates() -> None:
    service = object.__new__(MemoryService)
    state = {
        "working_memory": {
            "history": [
                {
                    "items": ["My dog's name is Maple."],
                    "source_version": 1,
                    "occurred_at": "2026-03-27T10:00:00+00:00",
                    "context_tags": {"topic": "pets"},
                    "pinned": False,
                }
            ]
        },
        "episodic_memory": {"episodes": []},
        "semantic_memory": {
            "concepts": [
                {
                    "value": "I grew up in Austin.",
                    "source_version": 2,
                    "last_seen_at": "2026-03-27T10:00:00+00:00",
                    "mention_count": 2,
                    "last_context_tags": {"topic": "home"},
                    "pinned": False,
                },
                {
                    "value": "topic:planning",
                    "source_version": 2,
                    "last_seen_at": "2026-03-27T10:00:00+00:00",
                    "mention_count": 3,
                    "last_context_tags": {"topic": "planning"},
                    "pinned": False,
                },
            ]
        },
        "relational_memory": {
            "signals": [
                {
                    "value": "dependency_risk:elevated",
                    "source_version": 3,
                    "last_seen_at": "2026-03-27T10:00:00+00:00",
                    "mention_count": 2,
                    "last_context_tags": {"topic": "relationship"},
                    "pinned": True,
                }
            ]
        },
        "reflective_memory": {
            "insights": [
                {
                    "value": "I tend to overthink when I'm tired.",
                    "source_version": 4,
                    "last_seen_at": "2026-03-27T10:00:00+00:00",
                    "mention_count": 1,
                    "last_context_tags": {"topic": "reflection"},
                    "pinned": True,
                }
            ]
        },
    }

    facts = service._extract_stable_factual_candidates(
        state=state,
        source_session_id="session-1",
        source_user_id="user-1",
        backend="mem0",
    )

    values = {fact.value for fact in facts}

    assert values == {
        "My dog's name is Maple.",
        "I grew up in Austin.",
    }
    assert all(fact.source_user_id == "user-1" for fact in facts)
    assert all(fact.backend == "mem0" for fact in facts)


def test_memory_service_index_record_marks_factual_candidate_metadata() -> None:
    service = object.__new__(MemoryService)

    factual_record = service._candidate_to_index_record(
        scope_id="user:user-1",
        user_id="user-1",
        session_id="session-1",
        candidate={
            "layer": "semantic_memory",
            "value": "I grew up in Austin.",
            "mention_count": 2,
            "source_version": 3,
            "pinned": False,
        },
    )
    relational_record = service._candidate_to_index_record(
        scope_id="user:user-1",
        user_id="user-1",
        session_id="session-1",
        candidate={
            "layer": "relational_memory",
            "value": "dependency_risk:elevated",
            "mention_count": 2,
            "source_version": 4,
            "pinned": True,
        },
    )

    assert factual_record.metadata["factual_candidate"] is True
    assert factual_record.metadata["fact_id"].startswith("user:user-1:i grew up in austin")
    assert factual_record.metadata["source_version"] == 3
    assert relational_record.metadata["factual_candidate"] is False
    assert relational_record.metadata["fact_id"] is None
