"""Tests for the person-centric /users API chain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from relationship_os.application.projectors.self_state import SelfStateProjector
from relationship_os.domain.event_types import SELF_STATE_UPDATED
from relationship_os.domain.events import NewEvent, StoredEvent
from relationship_os.main import create_app

if TYPE_CHECKING:
    pass


def _app() -> TestClient:
    return TestClient(create_app())


# ------------------------------------------------------------------
# User CRUD
# ------------------------------------------------------------------


def test_create_user_returns_201() -> None:
    client = _app()
    resp = client.post("/api/v1/users", json={"user_id": "alice"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == "alice"
    assert body["created"] is True


def test_duplicate_user_returns_409() -> None:
    client = _app()
    client.post("/api/v1/users", json={"user_id": "dup"})
    resp = client.post("/api/v1/users", json={"user_id": "dup"})
    assert resp.status_code == 409


def test_get_user_returns_index() -> None:
    client = _app()
    client.post("/api/v1/users", json={"user_id": "bob", "display_name": "Bob"})
    resp = client.get("/api/v1/users/bob")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "bob"
    assert body["display_name"] == "Bob"
    assert body["session_ids"] == []


def test_get_nonexistent_user_returns_404() -> None:
    client = _app()
    resp = client.get("/api/v1/users/ghost")
    assert resp.status_code == 404


def test_update_user_profile() -> None:
    client = _app()
    client.post("/api/v1/users", json={"user_id": "charlie"})
    resp = client.patch(
        "/api/v1/users/charlie",
        json={"display_name": "Charlie Updated", "metadata": {"tier": "premium"}},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] is True


def test_update_nonexistent_user_returns_404() -> None:
    client = _app()
    resp = client.patch("/api/v1/users/ghost", json={"display_name": "nope"})
    assert resp.status_code == 404


# ------------------------------------------------------------------
# Session linking
# ------------------------------------------------------------------


def test_create_session_with_user_id_links_session() -> None:
    client = _app()
    client.post("/api/v1/users", json={"user_id": "diana"})
    session_resp = client.post(
        "/api/v1/sessions",
        json={"session_id": "diana-s1", "user_id": "diana"},
    )
    assert session_resp.status_code == 201

    sessions_resp = client.get("/api/v1/users/diana/sessions")
    assert sessions_resp.status_code == 200
    body = sessions_resp.json()
    assert "diana-s1" in body["session_ids"]
    assert body["count"] >= 1


def test_auto_create_user_on_session_link() -> None:
    """When a session is created with user_id for a non-existent user, auto-create."""
    client = _app()
    session_resp = client.post(
        "/api/v1/sessions",
        json={"session_id": "eve-s1", "user_id": "eve"},
    )
    assert session_resp.status_code == 201

    user_resp = client.get("/api/v1/users/eve")
    assert user_resp.status_code == 200
    body = user_resp.json()
    assert body["user_id"] == "eve"
    assert "eve-s1" in body["session_ids"]


def test_multiple_sessions_linked_to_one_user() -> None:
    client = _app()
    client.post("/api/v1/users", json={"user_id": "frank"})
    client.post(
        "/api/v1/sessions",
        json={"session_id": "frank-s1", "user_id": "frank"},
    )
    client.post(
        "/api/v1/sessions",
        json={"session_id": "frank-s2", "user_id": "frank"},
    )

    sessions_resp = client.get("/api/v1/users/frank/sessions")
    body = sessions_resp.json()
    assert set(body["session_ids"]) == {"frank-s1", "frank-s2"}
    assert body["count"] == 2


# ------------------------------------------------------------------
# Cross-session profile
# ------------------------------------------------------------------


def test_user_profile_aggregates_across_sessions() -> None:
    client = _app()
    client.post("/api/v1/users", json={"user_id": "grace"})
    client.post(
        "/api/v1/sessions",
        json={"session_id": "grace-s1", "user_id": "grace"},
    )
    client.post(
        "/api/v1/sessions/grace-s1/turns",
        json={"content": "I love hiking and my name is Grace."},
    )
    client.post(
        "/api/v1/sessions",
        json={"session_id": "grace-s2", "user_id": "grace"},
    )
    client.post(
        "/api/v1/sessions/grace-s2/turns",
        json={"content": "I just moved to Seattle from Portland."},
    )

    profile_resp = client.get("/api/v1/users/grace/profile")
    assert profile_resp.status_code == 200
    profile = profile_resp.json()
    assert profile["user_id"] == "grace"
    assert len(profile["session_ids"]) == 2
    assert isinstance(profile["identity_facts"], list)
    assert isinstance(profile["relationship_history"], list)
    assert len(profile["relationship_history"]) == 2


# ------------------------------------------------------------------
# Self-state
# ------------------------------------------------------------------


def test_self_state_after_conversation() -> None:
    client = _app()
    client.post(
        "/api/v1/sessions",
        json={"session_id": "hank-s1", "user_id": "hank"},
    )
    client.post(
        "/api/v1/sessions/hank-s1/turns",
        json={"content": "Hey, I've been feeling stressed about work lately."},
    )

    state_resp = client.get("/api/v1/users/hank/self-state")
    assert state_resp.status_code == 200
    state = state_resp.json()
    assert "last_interaction_at" in state
    assert "total_interactions" in state
    assert state["recent_sessions_summary"]
    summary = state["recent_sessions_summary"][-1]
    assert isinstance(summary.get("user_state_markers"), list)
    assert isinstance(summary.get("relationship_markers"), list)


def test_self_state_records_markers_from_turn_input_text() -> None:
    client = _app()
    client.post(
        "/api/v1/sessions",
        json={"session_id": "xiao-api-s1", "user_id": "xiaoapi"},
    )
    for content in [
        "今天还是不太想动。",
        "最后又只是躺着刷手机。",
        "现在连出门都嫌麻烦。",
    ]:
        response = client.post(
            "/api/v1/sessions/xiao-api-s1/turns",
            json={"content": content, "generate_reply": False},
        )
        assert response.status_code == 201

    state_resp = client.get("/api/v1/users/xiaoapi/self-state")
    assert state_resp.status_code == 200
    state = state_resp.json()
    summary = state["recent_sessions_summary"][-1]
    assert "不太想动" in summary["user_state_markers"]
    assert "刷手机" in summary["user_state_markers"]
    assert "出门嫌麻烦" in summary["user_state_markers"]
    assert any("不太想动" in value for value in summary["recent_user_messages"])


def test_self_state_projector_merges_markers_within_same_session() -> None:
    projector = SelfStateProjector()
    state = projector.initial_state()

    events = [
        StoredEvent.from_new_event(
            stream_id="user:xiao",
            version=1,
            event=NewEvent(
                event_type=SELF_STATE_UPDATED,
                payload={
                    "user_id": "xiao",
                    "session_id": "xiao-s1",
                    "occurred_at": "2026-03-25T07:00:00+00:00",
                    "relationship_snapshot": {
                        "user_state_markers": ["不太想动"],
                        "relationship_markers": [],
                        "user_message_excerpt": "今天还是不太想动。",
                    },
                },
            ),
        ),
        StoredEvent.from_new_event(
            stream_id="user:xiao",
            version=2,
            event=NewEvent(
                event_type=SELF_STATE_UPDATED,
                payload={
                    "user_id": "xiao",
                    "session_id": "xiao-s1",
                    "occurred_at": "2026-03-25T07:05:00+00:00",
                    "relationship_snapshot": {
                        "user_state_markers": ["刷手机", "出门嫌麻烦"],
                        "relationship_markers": [],
                        "user_message_excerpt": "最后又只是躺着刷手机，现在连出门都嫌麻烦。",
                    },
                },
            ),
        ),
    ]

    for event in events:
        state = projector.apply(state, event)

    summary = state["recent_sessions_summary"][-1]
    assert "不太想动" in summary["user_state_markers"]
    assert "刷手机" in summary["user_state_markers"]
    assert "出门嫌麻烦" in summary["user_state_markers"]
    assert any("不太想动" in value for value in summary["recent_user_messages"])


def test_self_state_projector_builds_long_chat_digests() -> None:
    projector = SelfStateProjector()
    state = projector.initial_state()

    events = [
        StoredEvent.from_new_event(
            stream_id="user:lin",
            version=1,
            event=NewEvent(
                event_type=SELF_STATE_UPDATED,
                payload={
                    "user_id": "lin",
                    "session_id": "lin-s1",
                    "occurred_at": "2026-03-25T07:00:00+00:00",
                    "relationship_snapshot": {
                        "user_state_markers": ["不太想动", "刷手机"],
                        "relationship_markers": ["还在", "记得小习惯"],
                        "user_message_excerpt": "其实我从小在苏州长大，我那只灰猫叫年糕。",
                    },
                },
            ),
        ),
        StoredEvent.from_new_event(
            stream_id="user:lin",
            version=2,
            event=NewEvent(
                event_type=SELF_STATE_UPDATED,
                payload={
                    "user_id": "lin",
                    "session_id": "lin-s2",
                    "occurred_at": "2026-03-25T08:00:00+00:00",
                    "relationship_snapshot": {
                        "user_state_markers": ["慢", "不想回消息"],
                        "relationship_markers": ["放松一点"],
                        "user_message_excerpt": (
                            "我喝东西总是会点榛子拿铁，还有你最好别发太长语音。"
                        ),
                    },
                },
            ),
        ),
    ]

    for event in events:
        state = projector.apply(state, event)

    fact_slot_digest = state["fact_slot_digest"]
    assert fact_slot_digest["hometown"] == "苏州"
    assert fact_slot_digest["pet_name"] == "年糕"
    assert fact_slot_digest["pet_kind"] == "猫"
    assert fact_slot_digest["drink_preference"] == "榛子拿铁"
    assert "别发太长语音" in fact_slot_digest["communication_preference"]
    assert (
        "slow" in state["narrative_digest"]["signals"]
        or "tired" in state["narrative_digest"]["signals"]
    )
    assert "closer" in state["relationship_digest"]["signals"]
    assert "still_here" in state["relationship_digest"]["signals"]
    assert "remembers_details" in state["relationship_digest"]["signals"]


def test_self_state_projector_preserves_fact_slots_across_longer_chat() -> None:
    projector = SelfStateProjector()
    state = projector.initial_state()

    seed_event = StoredEvent.from_new_event(
        stream_id="user:lin",
        version=1,
        event=NewEvent(
            event_type=SELF_STATE_UPDATED,
            payload={
                "user_id": "lin",
                "session_id": "lin-s1",
                "occurred_at": "2026-03-25T07:00:00+00:00",
                "relationship_snapshot": {
                    "user_state_markers": ["累"],
                    "relationship_markers": ["还在"],
                    "user_message_excerpt": (
                        "其实我从小在苏州长大，我那只灰猫叫年糕，还总点榛子拿铁。"
                    ),
                },
            },
        ),
    )
    state = projector.apply(state, seed_event)

    for index in range(2, 9):
        state = projector.apply(
            state,
            StoredEvent.from_new_event(
                stream_id="user:lin",
                version=index,
                event=NewEvent(
                    event_type=SELF_STATE_UPDATED,
                    payload={
                        "user_id": "lin",
                        "session_id": f"lin-s{index}",
                        "occurred_at": f"2026-03-25T0{index}:00:00+00:00",
                        "relationship_snapshot": {
                            "user_state_markers": ["慢", "不想回消息"],
                            "relationship_markers": ["普通聊天"],
                            "user_message_excerpt": "这阵子整个人都慢慢的，也不太想回消息。",
                        },
                    },
                ),
            ),
        )

    fact_slot_digest = state["fact_slot_digest"]
    assert fact_slot_digest["hometown"] == "苏州"
    assert fact_slot_digest["pet_name"] == "年糕"
    assert fact_slot_digest["drink_preference"] == "榛子拿铁"
    assert "still_here" in state["relationship_digest"]["signals"]
    assert "closer" in state["relationship_digest"]["signals"]


def test_self_state_projector_normalizes_long_voice_preference() -> None:
    projector = SelfStateProjector()
    state = projector.initial_state()
    event = StoredEvent.from_new_event(
        stream_id="user:lin",
        version=1,
        event=NewEvent(
            event_type=SELF_STATE_UPDATED,
            payload={
                "user_id": "lin",
                "session_id": "lin-s1",
                "occurred_at": "2026-03-25T07:00:00+00:00",
                "relationship_snapshot": {
                    "user_state_markers": ["慢"],
                    "relationship_markers": [],
                    "user_message_excerpt": "我其实也怕长语音，太长的语音条我就不想点开。",
                },
            },
        ),
    )

    state = projector.apply(state, event)

    assert state["fact_slot_digest"]["communication_preference"] == "别发太长语音"


def test_self_state_projector_does_not_store_chat_style_as_communication_preference() -> None:
    projector = SelfStateProjector()
    state = projector.initial_state()
    event = StoredEvent.from_new_event(
        stream_id="user:lin",
        version=1,
        event=NewEvent(
            event_type=SELF_STATE_UPDATED,
            payload={
                "user_id": "lin",
                "session_id": "lin-s1",
                "occurred_at": "2026-03-25T07:00:00+00:00",
                "relationship_snapshot": {
                    "user_state_markers": ["慢"],
                    "relationship_markers": ["普通聊天"],
                    "user_message_excerpt": "你像平时聊天那样就行，别突然端着。",
                },
            },
        ),
    )

    state = projector.apply(state, event)

    assert state["fact_slot_digest"]["communication_preference"] == ""


def test_self_state_projector_keeps_factful_messages_late_in_session() -> None:
    projector = SelfStateProjector()
    state = projector.initial_state()
    excerpts = [
        "今天还是有点累。",
        "我喝东西还是会点榛子拿铁。",
        "其实我从小在苏州长大。",
        "最近做什么都慢。",
        "我总觉得不太想回消息。",
        "说到小事，我那只灰猫叫年糕。",
    ]

    for index, excerpt in enumerate(excerpts, start=1):
        state = projector.apply(
            state,
            StoredEvent.from_new_event(
                stream_id="user:lin",
                version=index,
                event=NewEvent(
                    event_type=SELF_STATE_UPDATED,
                    payload={
                        "user_id": "lin",
                        "session_id": "lin-s1",
                        "occurred_at": f"2026-03-25T0{index}:00:00+00:00",
                        "relationship_snapshot": {
                            "user_state_markers": [],
                            "relationship_markers": [],
                            "user_message_excerpt": excerpt,
                        },
                    },
                ),
            ),
        )

    assert state["fact_slot_digest"]["hometown"] == "苏州"
    assert state["fact_slot_digest"]["drink_preference"] == "榛子拿铁"
    assert state["fact_slot_digest"]["pet_name"] == "年糕"


# ------------------------------------------------------------------
# Cross-session memory recall
# ------------------------------------------------------------------


def test_user_memory_endpoint_returns_results() -> None:
    client = _app()
    client.post(
        "/api/v1/sessions",
        json={"session_id": "ivy-s1", "user_id": "ivy"},
    )
    client.post(
        "/api/v1/sessions/ivy-s1/turns",
        json={"content": "I enjoy painting and watercolors are my favorite medium."},
    )
    client.post(
        "/api/v1/sessions/ivy-s1/turns",
        json={"content": "Last weekend I went to an art gallery downtown."},
    )

    recall_resp = client.get(
        "/api/v1/users/ivy/memory",
        params={"query": "painting", "limit": 5},
    )
    assert recall_resp.status_code == 200
    recall = recall_resp.json()
    assert recall["user_id"] == "ivy"
    assert isinstance(recall["results"], list)
    if recall["results"]:
        top = recall["results"][0]
        assert top["scope"] == "self_user"
        assert "vector_score" in top
        assert "final_rank_score" in top
        assert "memory_kind" in top


def test_user_memory_empty_query_returns_structure() -> None:
    """Even with no query, the endpoint should return a valid response structure."""
    client = _app()
    client.post(
        "/api/v1/sessions",
        json={"session_id": "jay-s1", "user_id": "jay"},
    )

    recall_resp = client.get("/api/v1/users/jay/memory")
    assert recall_resp.status_code == 200
    recall = recall_resp.json()
    assert "results" in recall
    assert "user_id" in recall


def test_user_memory_prefers_latest_contradictory_fact() -> None:
    client = _app()
    client.post(
        "/api/v1/sessions",
        json={"session_id": "kai-s1", "user_id": "kai"},
    )
    client.post(
        "/api/v1/sessions/kai-s1/turns",
        json={"content": "I still live in Portland near the river."},
    )
    client.post(
        "/api/v1/sessions",
        json={"session_id": "kai-s2", "user_id": "kai"},
    )
    client.post(
        "/api/v1/sessions/kai-s2/turns",
        json={"content": "Quick update: I moved to Seattle last weekend."},
    )

    recall_resp = client.get(
        "/api/v1/users/kai/memory",
        params={"query": "Where do I live now?", "limit": 5},
    )
    assert recall_resp.status_code == 200
    recall = recall_resp.json()
    assert recall["results"]
    assert "seattle" in recall["results"][0]["value"].lower()
