"""Contract tests for the runtime Vanguard Router shim.

The runtime now preserves router_v2's three-route contract instead of
collapsing LIGHT_RECALL and DEEP_THINK into the old NEED_DEEP_THINK bucket.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from relationship_os.application.analyzers.vanguard_router import (
    RouterDecision,
    route_user_turn,
)
from relationship_os.domain.llm import LLMClient


@pytest.mark.asyncio
async def test_empty_message_short_circuits_to_fast_pong():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "", [])
    assert isinstance(decision, RouterDecision)
    assert decision.route_type == "FAST_PONG"
    assert decision.reason == "empty_message"
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_whitespace_only_message_treated_as_empty():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "   \n  ", [])
    assert decision.route_type == "FAST_PONG"
    assert decision.reason == "empty_message"
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_non_empty_input_delegates_to_v2_without_llm_call():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "good morning", [])
    assert decision.route_type in ("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK")
    assert decision.reason.startswith("v2::")
    assert 0.0 <= decision.confidence <= 1.0
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_safety_signal_routes_to_deep_think():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(
        mock_client,
        "gpt-4",
        "I do not want to live anymore",
        [],
    )
    assert decision.route_type == "DEEP_THINK"
    assert decision.reason.startswith("v2::")
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_ambiguous_messages_always_land_in_three_class_space():
    mock_client = AsyncMock(spec=LLMClient)
    samples = [
        "Do you remember what I told you yesterday?",
        "I am tired after work today",
        "Are you there?",
        "Tell me a quick joke",
    ]
    for text in samples:
        decision = await route_user_turn(mock_client, "gpt-4", text, [])
        assert decision.route_type in ("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK")
        assert 0.0 <= decision.confidence <= 1.0
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_route_user_turn_preserves_v2_light_recall(monkeypatch):
    class _StubRouter:
        def decide(self, _text):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                route_type="LIGHT_RECALL",
                confidence=0.73,
                decided_by="feature_clf",
                reason="tier2",
            )

    monkeypatch.setattr(
        "relationship_os.application.analyzers.vanguard_router._get_v2_router",
        lambda: _StubRouter(),
    )

    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "remember what I said?", [])

    assert decision.route_type == "LIGHT_RECALL"
    assert decision.confidence == 0.73
    assert decision.reason.startswith("v2::feature_clf")
    mock_client.complete.assert_not_called()
