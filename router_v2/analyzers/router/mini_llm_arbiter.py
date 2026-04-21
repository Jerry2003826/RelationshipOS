"""Tier 3 mini-LLM arbiter.

Only called when Tier 1 produces no short-circuit AND Tier 2's max
probability is below the abstention threshold (default 0.6). Uses a
6-shot, deterministic prompt that asks the model to output JSON with
`route_type` + `confidence` + `why`.

This module is intentionally decoupled from any concrete model client;
the caller injects a `call_llm` callable matching
``(prompt: str, timeout: float) -> str``. In production this wraps the
host's existing fast-lane LLM (e.g. Qwen2.5-1.5B at int4). For tests
we inject a stub.

Safety contract:
    * Hard timeout enforced in the caller (default 1.5s).
    * Any error / timeout → CircuitBreaker.on_failure() + health_degraded.
    * JSON parse failure → fallback to Tier 2 top-1 + health_degraded.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

from .circuit_breaker import BreakerOpenError, CircuitBreaker
from .contracts import ALL_ROUTES, RouteType

logger = logging.getLogger(__name__)

LLMCallable = Callable[[str, float], str]


_SYSTEM_PROMPT = """你是一个对话路由仲裁器。给定用户一句话, 在以下 3 类中选 1:

- FAST_PONG: 无需调用记忆/情感/推理的闲聊或致意; 回一句话即可。
- LIGHT_RECALL: 需要浅层记忆 (比如引用上次提到的事) 或情感着色, 但不需要多专家推理。
- DEEP_THINK: 身份探询、复杂情感事件、多步任务、明确的回忆请求+情感, 需要完整 pipeline。

只输出 JSON, 不要解释:
{"route_type": "FAST_PONG|LIGHT_RECALL|DEEP_THINK", "confidence": 0~1, "why": "<=20 字"}"""


_FEWSHOTS: list[tuple[str, dict[str, Any]]] = [
    ("在吗", {"route_type": "FAST_PONG", "confidence": 0.95, "why": "招呼"}),
    ("哈哈哈哈哈", {"route_type": "FAST_PONG", "confidence": 0.9, "why": "笑声"}),
    (
        "还记得我上次说我男朋友的事吗",
        {"route_type": "LIGHT_RECALL", "confidence": 0.9, "why": "明确回忆"},
    ),
    (
        "我一个人在宿舍哭了半天",
        {"route_type": "DEEP_THINK", "confidence": 0.9, "why": "情感事件"},
    ),
    (
        "你是谁啊 你把我当成什么",
        {"route_type": "DEEP_THINK", "confidence": 0.95, "why": "身份+关系"},
    ),
    (
        "帮我把这段翻译成英文",
        {"route_type": "DEEP_THINK", "confidence": 0.9, "why": "翻译任务"},
    ),
]


def _build_prompt(text: str) -> str:
    lines = [_SYSTEM_PROMPT, "", "示例:"]
    for user, out in _FEWSHOTS:
        lines.append(f"Q: {user}")
        lines.append(f"A: {json.dumps(out, ensure_ascii=False)}")
    lines.append("")
    lines.append(f"Q: {text}")
    lines.append("A: ")
    return "\n".join(lines)


@dataclass(slots=True, frozen=True)
class ArbiterOutput:
    route_type: RouteType
    confidence: float
    why: str


class ArbiterError(RuntimeError):
    """Raised on unrecoverable parse / timeout / breaker errors."""


@dataclass(slots=True)
class MiniLLMArbiter:
    call_llm: LLMCallable
    breaker: CircuitBreaker
    timeout_sec: float = 1.5

    def arbitrate(self, text: str) -> ArbiterOutput:
        """Call the mini-LLM. Raises ArbiterError on any failure path.

        Callers are expected to catch ArbiterError and fall back to the
        Tier 2 top-1 class while marking the decision as health_degraded.
        """
        if not self.breaker.allow():
            raise BreakerOpenError("mini-llm breaker open")

        prompt = _build_prompt(text)
        try:
            raw = self.call_llm(prompt, self.timeout_sec)
        except Exception as exc:  # noqa: BLE001
            self.breaker.on_failure()
            logger.warning("mini-llm call failed: %s", exc)
            raise ArbiterError(f"call_llm failed: {exc}") from exc

        parsed = _parse_json(raw)
        if parsed is None:
            self.breaker.on_failure()
            logger.warning("mini-llm returned non-JSON: %r", raw[:200])
            raise ArbiterError("non-json response")

        route = parsed.get("route_type")
        if route not in ALL_ROUTES:
            self.breaker.on_failure()
            raise ArbiterError(f"invalid route_type {route!r}")

        try:
            confidence = float(parsed.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        why = str(parsed.get("why", ""))[:40]

        self.breaker.on_success()
        return ArbiterOutput(route_type=route, confidence=confidence, why=why)  # type: ignore[arg-type]


def _parse_json(raw: str) -> dict[str, Any] | None:
    raw = raw.strip()
    # Sometimes mini LLMs prepend/append junk; grab outermost {...}.
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
