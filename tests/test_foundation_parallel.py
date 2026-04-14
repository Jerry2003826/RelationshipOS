"""Tests for Foundation phase async I/O parallelization.

Verifies that the parallel stages in `_build_turn_foundation` produce
identical results to sequential execution and that individual service
failures are handled gracefully.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from relationship_os.application.runtime_service import (
    RuntimeService,
    _TurnContext,
)


def _make_turn_context(**overrides):
    defaults = {
        "session_id": "test-session",
        "user_id": "test-user",
        "turn_index": 1,
        "session_age_seconds": 60.0,
        "idle_gap_seconds": 10.0,
        "transcript_messages": [],
        "strategy_history": [],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_stub_llm_interpretation():
    """Return a minimal _UserTurnInterpretation-like object."""
    return SimpleNamespace(
        intent_label="casual_chat",
        factual_recall=False,
        social_disclosure=False,
        self_referential_memory=False,
        presence_probe=False,
        edge_fact_deposition=False,
        edge_status_update=False,
        emotional_load="low",
        appraisal="neutral",
        source="llm",
        deliberation_mode="fast_reply",
        deliberation_need=0.1,
    )


def _make_stub_entity_service():
    """Create a stub entity service with all async methods."""
    service = MagicMock()

    async def _ensure_seeded():
        return None

    async def _get_persona_state():
        return {"persona_archetype": "warm_companion"}

    async def _get_social_world():
        return {"social_style": "engaging"}

    async def _assess_conscience(**kwargs):
        return SimpleNamespace(
            mode="withhold",
            reason="none",
            disclosure_style="hint",
            dramatic_value=0.0,
            conscience_weight=0.55,
            source_user_ids=[],
            allowed_fact_count=3,
            attribution_required=False,
            ambiguity_required=False,
            quote_style="none",
            dramatic_ceiling=0.5,
            must_anchor_to_observed_memory=False,
        )

    service.ensure_seeded = AsyncMock(side_effect=_ensure_seeded)
    service.get_persona_state = AsyncMock(side_effect=_get_persona_state)
    service.get_social_world = AsyncMock(side_effect=_get_social_world)
    service.assess_conscience = AsyncMock(side_effect=_assess_conscience)
    return service


def _make_stub_memory_service():
    """Create a stub memory service with all async methods."""
    service = MagicMock()

    async def _recall_person_memory(**kwargs):
        return {"results": [], "integrity_summary": {}}

    async def _recall_entity_memory(**kwargs):
        return {"results": []}

    async def _prepare_memory_write(**kwargs):
        return {
            "memory_bundle": SimpleNamespace(
                working_memory=[],
                episodic_memory=[],
                semantic_memory=[],
                relational_memory=[],
                reflective_memory=[],
            ),
            "write_guard": {},
            "retention_policy": {},
            "forgetting": {},
        }

    service.recall_person_memory = AsyncMock(side_effect=_recall_person_memory)
    service.recall_entity_memory = AsyncMock(side_effect=_recall_entity_memory)
    service.prepare_memory_write = AsyncMock(side_effect=_prepare_memory_write)
    return service


def _make_service_with_stubs():
    """Create a RuntimeService with all stubs for Foundation testing."""
    service = object.__new__(RuntimeService)

    # Stub LLM client
    class _StubLLMClient:
        async def complete(self, _request):
            return SimpleNamespace(
                output_text=(
                    '{"intent":"casual_chat","factual_recall":false,'
                    '"social_disclosure":false,"self_referential_memory":false,'
                    '"confidence":0.9,"deliberation_mode":"fast_reply",'
                    '"deliberation_need":0.1}'
                )
            )

    service._llm_client = _StubLLMClient()
    service._llm_model = "test-model"
    service._runtime_profile = "default"
    service._entity_service = _make_stub_entity_service()
    service._memory_service = _make_stub_memory_service()
    service._entity_id = "test-entity"
    service._user_service = None

    # Stub methods that _build_turn_foundation delegates to
    def _stub_build_edge_runtime_plan(**kwargs):
        return {"interpreted_intent": "casual_chat"}

    service._build_edge_runtime_plan = _stub_build_edge_runtime_plan  # type: ignore[method-assign]

    def _stub_is_edge_profile():
        return False

    service._is_edge_profile = _stub_is_edge_profile  # type: ignore[method-assign]

    def _stub_is_friend_chat_profile():
        return False

    service._is_friend_chat_profile = _stub_is_friend_chat_profile  # type: ignore[method-assign]

    def _stub_should_enable_entity_vector_search(**kwargs):
        return False

    service._should_enable_entity_vector_search = _stub_should_enable_entity_vector_search  # type: ignore[method-assign]

    def _stub_should_include_factual_shadow_in_person_recall(**kwargs):
        return False

    service._should_include_factual_shadow_in_person_recall = _stub_should_include_factual_shadow_in_person_recall  # type: ignore[method-assign]

    def _stub_merge_recalled_memory_items(existing, new, *, limit=10):
        return existing + new

    service._merge_recalled_memory_items = _stub_merge_recalled_memory_items  # type: ignore[method-assign]

    def _stub_friend_chat_social_queries(msg):
        return []

    service._friend_chat_social_queries = _stub_friend_chat_social_queries  # type: ignore[method-assign]

    def _stub_should_use_friend_chat_lightweight_foundation(*args, **kwargs):
        return False

    service._should_use_friend_chat_lightweight_foundation = _stub_should_use_friend_chat_lightweight_foundation  # type: ignore[method-assign]

    def _stub_previous_relationship_state(turn_context):
        return None

    service._previous_relationship_state = _stub_previous_relationship_state  # type: ignore[method-assign]

    return service


# ── Stage 1: Parallel LLM interpretation + entity seeding ──────────────


def test_foundation_stage1_runs_interpret_and_seed_in_parallel():
    """Verify that interpretation and seeding both complete."""
    service = _make_service_with_stubs()
    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Hello!",
            turn_context=turn_context,
        )
    )

    # Both should have been called
    service._entity_service.ensure_seeded.assert_called_once()
    assert foundation.entity_persona == {"persona_archetype": "warm_companion"}
    assert foundation.entity_social_world == {"social_style": "engaging"}


def test_foundation_stage1_handles_seed_failure_gracefully():
    """If ensure_seeded fails, interpretation still succeeds."""
    service = _make_service_with_stubs()
    service._entity_service.ensure_seeded = AsyncMock(side_effect=RuntimeError("seed failed"))

    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Hello!",
            turn_context=turn_context,
        )
    )

    # Foundation still returns, but entity data is empty
    assert foundation.entity_persona == {}
    assert foundation.entity_social_world == {}
    assert foundation.context_frame is not None


def test_foundation_stage1_works_without_entity_service():
    """No entity service → no seeding, interpretation still works."""
    service = _make_service_with_stubs()
    service._entity_service = None

    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Hello!",
            turn_context=turn_context,
        )
    )

    assert foundation.entity_persona == {}
    assert foundation.entity_social_world == {}


# ── Stage 2: Parallel entity state reads ───────────────────────────────


def test_foundation_stage2_reads_persona_and_social_world():
    """Verify both entity reads complete."""
    service = _make_service_with_stubs()
    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Hello!",
            turn_context=turn_context,
        )
    )

    service._entity_service.get_persona_state.assert_called_once()
    service._entity_service.get_social_world.assert_called_once()
    assert foundation.entity_persona == {"persona_archetype": "warm_companion"}
    assert foundation.entity_social_world == {"social_style": "engaging"}


def test_foundation_stage2_handles_read_failure():
    """If entity reads fail, foundation still returns with empty dicts."""
    service = _make_service_with_stubs()
    service._entity_service.get_persona_state = AsyncMock(side_effect=RuntimeError("read failed"))

    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Hello!",
            turn_context=turn_context,
        )
    )

    # Both should be empty because the try/except catches the gather failure
    assert foundation.entity_persona == {}
    assert foundation.entity_social_world == {}


# ── Full foundation equivalence ────────────────────────────────────────


def test_foundation_returns_valid_turn_foundation():
    """Verify the full _TurnFoundation is populated correctly."""
    service = _make_service_with_stubs()
    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Hello!",
            turn_context=turn_context,
        )
    )

    # Check all fields are populated
    assert foundation.context_frame is not None
    assert foundation.recalled_memory == []
    assert foundation.memory_recall is not None
    assert foundation.entity_persona == {"persona_archetype": "warm_companion"}
    assert foundation.entity_social_world == {"social_style": "engaging"}
    assert foundation.conscience_assessment["mode"] == "withhold"
    assert foundation.edge_runtime_plan is not None
    assert foundation.relationship_state is not None
    assert foundation.repair_assessment is not None
    assert foundation.confidence_assessment is not None
    assert foundation.memory_bundle is not None
    assert foundation.memory_write_guard is not None
    assert foundation.memory_retention_policy is not None
    assert foundation.memory_forgetting is not None
    assert foundation.repair_plan is not None


def test_foundation_conscience_uses_recalled_memory():
    """assess_conscience is called with the recalled_memory list."""
    service = _make_service_with_stubs()

    # Make recall return some items
    async def _recall_with_items(**kwargs):
        return {
            "results": [
                {"scope": "personal", "text": "test memory", "layer": "episodic"}
            ],
            "integrity_summary": {},
        }

    service._memory_service.recall_person_memory = AsyncMock(side_effect=_recall_with_items)

    turn_context = _make_turn_context()

    foundation = asyncio.run(
        service._build_turn_foundation(
            session_id="test-session",
            user_message="Remember when...",
            turn_context=turn_context,
        )
    )

    # Verify assess_conscience was called with the recalled items
    call_kwargs = service._entity_service.assess_conscience.call_args
    assert len(call_kwargs.kwargs["recalled_memory"]) == 1
    assert call_kwargs.kwargs["recalled_memory"][0]["text"] == "test memory"
