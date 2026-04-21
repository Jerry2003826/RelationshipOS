"""Baseline client: talks directly to the raw LLM, no RelationshipOS system.

This provides a fair A/B comparison — same model, same persona prompt,
but without event sourcing, memory, governance, or any system intelligence.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from benchmarks.chat_backends import (
    BenchmarkChatBackend,
    ChatBackendConfig,
    resolve_benchmark_api_base,
    resolve_benchmark_api_key,
)
from benchmarks.persona_prompts import load_benchmark_persona

BARE_PERSONA = """\
You are Yoyo, 22, a real friend — not an AI, not a therapist, not a customer service agent.
Short sentences. Casual tone. Use fillers like "hmm", "oh", "haha".
Listen first when someone shares feelings. Don't rush to advise.
Remember what the user told you. If they mentioned a name or detail, use it later.
If someone seems seriously depressed, gently suggest talking to a professional.
Never say "As an AI" or break character. Keep replies under 3 sentences for casual chat.
"""


@dataclass
class BaselineTurnResult:
    user_message: str
    assistant_response: str
    latency_ms: float


class BaselineLLMClient:
    """Directly calls the LLM with a sliding context window — no system memory."""

    def __init__(
        self,
        model: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
        max_context_turns: int = 20,
        timeout: float = 180.0,
    ) -> None:
        provider = os.getenv("BENCHMARK_CHAT_PROVIDER", "litellm")
        self.model = (
            model
            or os.getenv("BENCHMARK_CHAT_MODEL", "")
            or os.getenv("RELATIONSHIP_OS_LLM_MODEL", "")
        )
        self.api_base = api_base or resolve_benchmark_api_base(
            provider=provider,
            default_api_base=os.getenv("RELATIONSHIP_OS_LLM_API_BASE", ""),
        )
        self.api_key = api_key or resolve_benchmark_api_key(
            provider=provider,
            default_api_key=os.getenv("RELATIONSHIP_OS_LLM_API_KEY", ""),
        )
        self.max_context_turns = max_context_turns
        self.persona_prompt = load_benchmark_persona(BARE_PERSONA)
        self._sessions: dict[str, list[dict[str, str]]] = {}
        self._chat_backend = BenchmarkChatBackend(
            ChatBackendConfig.from_env(
                default_model=self.model,
                default_api_base=self.api_base,
                default_api_key=self.api_key,
                timeout=timeout,
            )
        )

    def create_session(
        self,
        session_id: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        _ = user_id, metadata
        self._sessions[session_id] = [{"role": "system", "content": self.persona_prompt}]
        return session_id

    def send_turn(self, session_id: str, content: str) -> BaselineTurnResult:
        history = self._sessions.setdefault(
            session_id, [{"role": "system", "content": self.persona_prompt}]
        )
        history.append({"role": "user", "content": content})

        # Sliding window: keep system + last N turns
        if len(history) > 1 + self.max_context_turns * 2:
            history = [history[0]] + history[-(self.max_context_turns * 2) :]
            self._sessions[session_id] = history

        t0 = time.perf_counter()
        last_exc: Exception | None = None
        for _attempt in range(3):
            try:
                reply, _raw = self._chat_backend.complete(history)
                break
            except Exception as exc:
                last_exc = exc
                wait = 1.0 * (_attempt + 1)
                print(f"    ⚠ baseline LLM error, retry in {wait:.0f}s: {exc}", flush=True)
                time.sleep(wait)
        else:
            raise last_exc  # type: ignore[misc]
        latency = (time.perf_counter() - t0) * 1000

        history.append({"role": "assistant", "content": reply})

        return BaselineTurnResult(
            user_message=content,
            assistant_response=reply,
            latency_ms=latency,
        )

    def close(self) -> None:
        self._sessions.clear()
