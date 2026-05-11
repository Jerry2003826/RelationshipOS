from types import SimpleNamespace

import pytest

from relationship_os.application.runtime.friend_chat_readonly_probe_renderer import (
    render_friend_chat_readonly_probe_response,
)


class _StubLLMClient:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = responses
        self.requests = []

    async def complete(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_render_friend_chat_readonly_probe_response_returns_primary_json_success() -> None:
    client = _StubLLMClient(
        [
            SimpleNamespace(
                model="m",
                output_text=(
                    '{"probe_kind":"persona_state",'
                    '"energy_clause":"说话会有点没力气。",'
                    '"fullness_clause":"也不太想把话说太满。",'
                    '"chatting_clause":"但还是像平时聊天。"}'
                ),
                tool_calls=[],
                usage=None,
                latency_ms=3,
                diagnostics={},
                failure=None,
            )
        ]
    )

    response = await render_friend_chat_readonly_probe_response(
        llm_client=client,
        llm_model="m",
        user_message="你现在说话是什么状态？",
        probe_plan={"probe_kind": "persona_state"},
        llm_metadata={"policy_profile": "friend_chat_zh_v1"},
    )

    assert "没力气" in response.output_text
    assert response.diagnostics["structured_probe_reply"] is True
    assert len(client.requests) == 1
    assert client.requests[0].response_format == {"type": "json_object"}
