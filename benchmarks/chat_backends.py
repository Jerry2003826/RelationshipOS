"""Shared chat backends for benchmark arms."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import httpx
import litellm

_THINK_CLOSED = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
_THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL)

litellm.suppress_debug_info = True


def strip_reasoning(text: str) -> str:
    if "<think>" not in text:
        return text.strip()
    reply = _THINK_CLOSED.sub("", text)
    reply = _THINK_UNCLOSED.sub("", reply).strip()
    return reply or text.strip()


def resolve_benchmark_api_key(
    *,
    provider: str | None = None,
    default_api_key: str = "",
) -> str:
    provider_name = (
        provider or os.getenv("BENCHMARK_CHAT_PROVIDER", "") or "litellm"
    ).strip().casefold()
    benchmark_key = os.getenv("BENCHMARK_CHAT_API_KEY", "").strip()
    minimax_key = os.getenv("MINIMAX_API_KEY", "").strip()
    relationship_key = os.getenv("RELATIONSHIP_OS_LLM_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if provider_name == "minimax":
        return (
            benchmark_key
            or minimax_key
            or relationship_key
            or openai_key
            or default_api_key
        )
    return (
        benchmark_key
        or relationship_key
        or openai_key
        or minimax_key
        or default_api_key
    )


def resolve_benchmark_api_base(
    *,
    provider: str | None = None,
    default_api_base: str = "",
) -> str:
    provider_name = (
        provider or os.getenv("BENCHMARK_CHAT_PROVIDER", "") or "litellm"
    ).strip().casefold()
    benchmark_base = os.getenv("BENCHMARK_CHAT_API_BASE", "").strip()
    relationship_base = os.getenv("RELATIONSHIP_OS_LLM_API_BASE", "").strip()
    openai_base = os.getenv("OPENAI_API_BASE", "").strip()
    minimax_base = os.getenv("MINIMAX_API_BASE", "").strip()
    if provider_name == "minimax":
        return (
            benchmark_base
            or minimax_base
            or relationship_base
            or openai_base
            or default_api_base
        )
    return benchmark_base or relationship_base or openai_base or minimax_base or default_api_base


@dataclass(slots=True)
class ChatBackendConfig:
    provider: str
    model: str
    api_base: str
    api_key: str
    timeout: float = 180.0
    temperature: float = 0.7
    max_tokens: int = 512

    @classmethod
    def from_env(
        cls,
        *,
        default_model: str = "",
        default_api_base: str = "",
        default_api_key: str = "",
        default_provider: str = "litellm",
        timeout: float = 180.0,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> ChatBackendConfig:
        provider = (
            os.getenv("BENCHMARK_CHAT_PROVIDER", default_provider).strip()
            or default_provider
        )
        model = os.getenv("BENCHMARK_CHAT_MODEL", default_model).strip() or default_model
        api_base = resolve_benchmark_api_base(
            provider=provider,
            default_api_base=default_api_base,
        )
        api_key = resolve_benchmark_api_key(
            provider=provider,
            default_api_key=default_api_key,
        )
        return cls(
            provider=provider,
            model=model,
            api_base=api_base,
            api_key=api_key,
            timeout=float(os.getenv("BENCHMARK_CHAT_TIMEOUT", str(timeout))),
            temperature=float(os.getenv("BENCHMARK_CHAT_TEMPERATURE", str(temperature))),
            max_tokens=int(os.getenv("BENCHMARK_CHAT_MAX_TOKENS", str(max_tokens))),
        )


class BenchmarkChatBackend:
    def __init__(self, config: ChatBackendConfig) -> None:
        self._config = config

    def complete(self, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        provider = self._config.provider.casefold()
        if provider == "minimax":
            return self._complete_minimax(messages)
        return self._complete_litellm(messages)

    def _complete_litellm(self, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "timeout": self._config.timeout,
        }
        if self._config.api_base:
            kwargs["api_base"] = self._config.api_base
        if self._config.api_key:
            kwargs["api_key"] = self._config.api_key
        response = litellm.completion(**kwargs)
        raw_reply = response.choices[0].message.content.strip()
        reply = strip_reasoning(raw_reply)
        return reply, {"provider": "litellm", "raw": response}

    def _complete_minimax(self, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
        endpoint = self._normalize_minimax_endpoint(self._config.api_base)
        payload = {
            "model": self._config.model or "M2-her",
            "messages": [self._serialize_minimax_message(message) for message in messages],
            "temperature": max(0.01, min(1.0, self._config.temperature)),
            "top_p": 0.95,
            "stream": False,
            "max_completion_tokens": self._config.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self._config.timeout) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not isinstance(choices, list) or not choices:
            base_resp = data.get("base_resp") or {}
            status_msg = base_resp.get("status_msg") or data.get("message") or "missing_choices"
            raise RuntimeError(f"MiniMax response missing choices: {status_msg}")
        message = choices[0].get("message") or {}
        raw_reply = str(message.get("content") or "").strip()
        if not raw_reply:
            base_resp = data.get("base_resp") or {}
            status_msg = base_resp.get("status_msg") or "empty_content"
            raise RuntimeError(f"MiniMax response missing content: {status_msg}")
        return strip_reasoning(raw_reply), {
            "provider": "minimax",
            "endpoint": endpoint,
            "raw": data,
        }

    def _normalize_minimax_endpoint(self, api_base: str) -> str:
        base = (api_base or "https://api.minimax.io").rstrip("/")
        if base.endswith("/v1/text/chatcompletion_v2"):
            return base
        if base.endswith("/v1"):
            return f"{base}/text/chatcompletion_v2"
        return f"{base}/v1/text/chatcompletion_v2"

    def _serialize_minimax_message(self, message: dict[str, str]) -> dict[str, str]:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            return {"role": "system", "name": "MiniMax AI", "content": content}
        if role == "assistant":
            return {"role": "assistant", "name": "MiniMax AI", "content": content}
        return {"role": "user", "name": "User", "content": content}
