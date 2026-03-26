"""Direct LLM chat backends for benchmark preflight and tooling."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@dataclass(frozen=True, slots=True)
class ChatBackendConfig:
    provider: str
    model: str
    api_base: str | None
    api_key: str | None
    timeout: float
    temperature: float
    max_tokens: int

    @classmethod
    def from_env(
        cls,
        *,
        default_provider: str = "minimax",
        default_model: str = "M2-her",
        default_api_base: str = "https://api.minimax.io",
        timeout: float = 60.0,
        temperature: float = 0.3,
        max_tokens: int = 256,
    ) -> ChatBackendConfig:
        api_key = (
            os.environ.get("BENCHMARK_CHAT_API_KEY")
            or os.environ.get("MINIMAX_API_KEY")
            or ""
        ).strip() or None
        api_base = (os.environ.get("BENCHMARK_CHAT_API_BASE") or default_api_base).strip()
        return cls(
            provider=(os.environ.get("BENCHMARK_CHAT_PROVIDER") or default_provider).strip(),
            model=(os.environ.get("BENCHMARK_CHAT_MODEL") or default_model).strip(),
            api_base=api_base or None,
            api_key=api_key,
            timeout=_env_float("BENCHMARK_CHAT_TIMEOUT", timeout),
            temperature=_env_float("BENCHMARK_CHAT_TEMPERATURE", temperature),
            max_tokens=_env_int("BENCHMARK_CHAT_MAX_TOKENS", max_tokens),
        )

    def litellm_model(self) -> str:
        """Map env provider + model to a LiteLLM model id."""
        p = self.provider.lower()
        if p == "minimax" and "/" not in self.model:
            return f"minimax/{self.model}"
        return self.model


class BenchmarkChatBackend:
    def __init__(self, config: ChatBackendConfig) -> None:
        self._cfg = config

    def complete(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, dict[str, Any]]:
        from litellm import completion

        kwargs: dict[str, Any] = {
            "model": self._cfg.litellm_model(),
            "messages": messages,
            "temperature": self._cfg.temperature,
            "max_tokens": self._cfg.max_tokens,
            "timeout": self._cfg.timeout,
        }
        if self._cfg.api_base:
            kwargs["api_base"] = self._cfg.api_base
        if self._cfg.api_key:
            kwargs["api_key"] = self._cfg.api_key

        response = completion(**kwargs)
        meta: dict[str, Any] = {"provider": self._cfg.provider, "model": kwargs["model"]}
        choices = getattr(response, "choices", None) or []
        if not choices:
            return "", meta
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None) if message is not None else None
        if content is None and isinstance(choices[0], dict):
            message = choices[0].get("message") or {}
            content = message.get("content")
        text = (content or "").strip() if isinstance(content, str) else str(content or "")
        return text, meta
