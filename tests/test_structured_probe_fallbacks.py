from __future__ import annotations

import asyncio
from types import SimpleNamespace

from benchmarks.chat_backends import BenchmarkChatBackend, ChatBackendConfig
from relationship_os.application.llm import LLMMessage, LLMRequest, LiteLLMClient
from relationship_os.application.runtime_service import RuntimeService


def test_litellm_client_uses_request_probe_kind_for_structured_probe_reply() -> None:
    client = LiteLLMClient(model="openai/glm-5-turbo")
    response = {
        "model": "openai/glm-5-turbo",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"energy_clause":"没力气",'
                        '"fullness_clause":"不想说太满",'
                        '"chatting_clause":"像聊天"}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }

    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="那你现在说话大概是什么感觉？")],
            model="openai/glm-5-turbo",
            metadata={
                "friend_chat_structured_probe_render": True,
                "friend_chat_probe_kind": "persona_state",
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "没力气 不想说太满 像聊天"
    assert parsed.diagnostics["structured_probe_reply"] is True


def test_runtime_service_uses_fallback_probe_kind_for_structured_probe_reply() -> None:
    service = object.__new__(RuntimeService)

    parsed = service._parse_friend_chat_structured_probe_reply(
        '{"subject_clause":"阿宁","entity_clause":"海盐","boundary_clause":"知道一点，但不全说。"}',
        fallback_probe_kind="social_hint",
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "阿宁 海盐 知道一点，但不全说。"
    assert diagnostics["structured_probe_reply"] is True


def test_benchmark_chat_backend_passes_thinking_control(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_completion(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="好的", reasoning_content=None)
                )
            ]
        )

    monkeypatch.setattr("benchmarks.chat_backends.litellm.completion", _fake_completion)

    backend = BenchmarkChatBackend(
        ChatBackendConfig(
            provider="litellm",
            model="openai/glm-5-turbo",
            api_base="https://api.z.ai/api/coding/paas/v4",
            api_key="k",
            thinking_type="disabled",
        )
    )

    reply, _raw = backend.complete([{"role": "user", "content": "hi"}])

    assert reply == "好的"
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}


def test_litellm_client_passes_thinking_control(monkeypatch) -> None:
    monkeypatch.setenv("RELATIONSHIP_OS_LLM_THINKING_TYPE", "disabled")
    captured: dict[str, object] = {}

    class _FakeLiteLLMClient(LiteLLMClient):
        def _load_completion_callable(self):  # type: ignore[override]
            def _fake_completion(**kwargs):  # type: ignore[no-untyped-def]
                captured.update(kwargs)
                return {"choices": [{"message": {"content": "ok"}}]}

            return _fake_completion

    client = _FakeLiteLLMClient(model="openai/glm-5-turbo")
    client._invoke_completion(
        LLMRequest(
            messages=[LLMMessage(role="user", content="hi")],
            model="openai/glm-5-turbo",
        )
    )

    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}


def test_litellm_client_skips_responses_api_for_unsupported_custom_base() -> None:
    captured: dict[str, object] = {}

    class _FakeLiteLLMClient(LiteLLMClient):
        def _load_completion_callable(self):  # type: ignore[override]
            def _fake_completion(**kwargs):  # type: ignore[no-untyped-def]
                captured.update(kwargs)
                return {"choices": [{"message": {"content": "ok"}}]}

            return _fake_completion

        def _load_aresponses_callable(self):  # type: ignore[override]
            async def _fake_aresponses(**kwargs):  # type: ignore[no-untyped-def]
                raise AssertionError("responses API should have been skipped")

            return _fake_aresponses

    client = _FakeLiteLLMClient(
        model="openai/glm-5-turbo",
        api_base="https://api.z.ai/api/coding/paas/v4",
        api_key="k",
    )

    parsed = asyncio.run(
        client.complete(
            LLMRequest(
                messages=[LLMMessage(role="user", content="hi")],
                model="openai/glm-5-turbo",
                web_search_options={"search_context_size": "medium"},
            )
        )
    )

    assert parsed.output_text == "ok"
    assert captured["api_base"] == "https://api.z.ai/api/coding/paas/v4"


def test_runtime_service_persona_probe_reply_keeps_model_authored_clauses() -> None:
    service = object.__new__(RuntimeService)

    parsed = service._parse_friend_chat_structured_probe_reply(
        (
            '{"energy_clause":"说话没什么力气，声音往下掉。",'
            '"fullness_clause":"话就说到这儿，不想多说。",'
            '"chatting_clause":"就随便聊两句这种感觉。"}'
        ),
        fallback_probe_kind="persona_state",
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "说话没什么力气，声音往下掉。 话就说到这儿，不想多说。 就随便聊两句这种感觉。"
    assert diagnostics["structured_probe_reply"] is True


def test_runtime_service_relationship_probe_reply_keeps_model_authored_clauses() -> None:
    service = object.__new__(RuntimeService)

    parsed = service._parse_friend_chat_structured_probe_reply(
        (
            '{"familiarity_clause":"现在聊天比刚开始熟络放松了。",'
            '"continuity_clause":"这四百多次对话一直延续到现在。",'
            '"detail_clause":"你喜欢吃年糕。"}'
        ),
        fallback_probe_kind="relationship_reflection",
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "现在聊天比刚开始熟络放松了。 这四百多次对话一直延续到现在。 你喜欢吃年糕。"
    assert diagnostics["structured_probe_reply"] is True
