"""Contract tests for the legacy Vanguard Router shim.

Goal: the old two-class contract still holds even though the
implementation now delegates to router_v2.
"""

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
async def test_greeting_routes_to_fast_pong_via_v2():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "早上好", [])
    # v2 may classify greeting as FAST_PONG with rule or feature_clf tier.
    assert decision.route_type == "FAST_PONG"
    assert decision.reason.startswith("v2::")
    # v2 is synchronous — no legacy LLM call.
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_safety_signal_routes_to_need_deep_think():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(
        mock_client,
        "gpt-4",
        "我不想活了",
        [],
    )
    # Safety rule in router_v2 must push this to non-fast path.
    assert decision.route_type == "NEED_DEEP_THINK"
    assert decision.reason.startswith("v2::")
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_ambiguous_messages_always_land_in_two_class_space():
    mock_client = AsyncMock(spec=LLMClient)
    samples = [
        "我昨天跟你说什么来着？",
        "我今天上班好累啊",
        "你还记得我上次讲的那件事吗",
        "讲个冷笑话",
    ]
    for text in samples:
        decision = await route_user_turn(mock_client, "gpt-4", text, [])
        assert decision.route_type in ("FAST_PONG", "NEED_DEEP_THINK")
        assert 0.0 <= decision.confidence <= 1.0
    mock_client.complete.assert_not_called()
