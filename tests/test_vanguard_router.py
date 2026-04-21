"""Contract tests for the legacy vanguard_router shim.

The shim delegates to router_v2; we only verify the legacy two-class
surface is preserved and that the happy path does not invoke the LLM
client (since router_v2 decides locally via rules + LogReg).
"""

from unittest.mock import AsyncMock

import pytest

from relationship_os.application.analyzers.vanguard_router import (
    RouterDecision,
    route_user_turn,
)
from relationship_os.domain.llm import LLMClient


@pytest.mark.asyncio
async def test_empty_message_returns_fast_pong():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "", [])
    assert isinstance(decision, RouterDecision)
    assert decision.route_type == "FAST_PONG"
    # v2 happy path must not touch the LLM.
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_short_greeting_is_fast_pong():
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(mock_client, "gpt-4", "早上好", [])
    assert decision.route_type == "FAST_PONG"
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_self_harm_signal_routes_to_deep_think():
    """Safety rule must still fire through the shim."""
    mock_client = AsyncMock(spec=LLMClient)
    decision = await route_user_turn(
        mock_client,
        "gpt-4",
        "我不想活了",
        [],
    )
    assert decision.route_type == "NEED_DEEP_THINK"
    assert "v2::" in decision.reason


@pytest.mark.asyncio
async def test_return_shape_is_legacy_two_class():
    """Every decision must be one of the two legacy labels."""
    mock_client = AsyncMock(spec=LLMClient)
    for msg in ("哈哈", "我昨天跟你说什么来着", "你还记得小明吗", "嗯嗯"):
        decision = await route_user_turn(mock_client, "gpt-4", msg, [])
        assert decision.route_type in ("FAST_PONG", "NEED_DEEP_THINK")
        assert 0.0 <= decision.confidence <= 1.0
