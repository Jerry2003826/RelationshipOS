from unittest.mock import AsyncMock, MagicMock

import pytest

from relationship_os.application.analyzers.vanguard_router import route_user_turn
from relationship_os.domain.llm import LLMClient, LLMResponse


@pytest.mark.asyncio
async def test_vanguard_router_level_1_intercept():
    mock_client = AsyncMock(spec=LLMClient)

    # Test blank message
    decision = await route_user_turn(mock_client, "gpt-4", "", [])
    assert decision.route_type == "FAST_PONG"
    assert decision.reason == "empty_message"

    # Test strict exact matches
    decision = await route_user_turn(mock_client, "gpt-4", "早上好", [])
    assert decision.route_type == "FAST_PONG"
    assert decision.reason == "rule_exact_match"

    # Test pattern match
    decision = await route_user_turn(mock_client, "gpt-4", "嘿嘿", [])
    assert decision.route_type == "FAST_PONG"
    assert decision.reason == "rule_pattern_match"

    # Rule engine intercepts should not invoke the LLM
    mock_client.complete.assert_not_called()


@pytest.mark.asyncio
async def test_vanguard_router_level_2_llm_fast_pong():
    mock_client = AsyncMock(spec=LLMClient)

    # Mock the LLM JSON response for a casual non-rule intent
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.output_text = '{"route_type": "FAST_PONG", "reason": "venting"}'
    mock_client.complete.return_value = mock_response

    decision = await route_user_turn(
        llm_client=mock_client,
        llm_model="gpt-4",
        user_message="我今天上班好累啊，哎",
        transcript_messages=[{"role": "assistant", "content": "怎么啦？"}],
    )

    assert decision.route_type == "FAST_PONG"
    assert decision.reason == "venting"
    assert mock_client.complete.call_count == 1


@pytest.mark.asyncio
async def test_vanguard_router_level_2_llm_deep_think():
    mock_client = AsyncMock(spec=LLMClient)

    # Mock the LLM JSON response for a deep think intent
    mock_response = MagicMock(spec=LLMResponse)
    mock_response.output_text = '{"route_type": "NEED_DEEP_THINK", "reason": "factual_question"}'
    mock_client.complete.return_value = mock_response

    decision = await route_user_turn(
        llm_client=mock_client,
        llm_model="gpt-4",
        user_message="我昨天跟你说什么来着？",
        transcript_messages=[],
    )

    assert decision.route_type == "NEED_DEEP_THINK"
    assert decision.reason == "factual_question"
    assert mock_client.complete.call_count == 1
