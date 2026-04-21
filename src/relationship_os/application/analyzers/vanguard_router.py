"""Legacy Vanguard Router shim.

Old callers:

    from relationship_os.application.analyzers.vanguard_router import (
        route_user_turn, RouterDecision,
    )

still work unchanged. Internally this now delegates to `router_v2`
(Option D: safety-only rules + distilled LogReg + mini-LLM arbiter).

Deprecated since 2026-04; will be removed in 2026-Q4.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from typing import Any

from relationship_os.domain.llm import LLMClient, LLMMessage, LLMRequest

logger = logging.getLogger(__name__)

# Lazy import so that unit tests that only exercise the legacy two-class
# contract do not need the sklearn / joblib stack at import time.
_V2_ROUTER = None


@dataclass(slots=True, frozen=True)
class RouterDecision:
    """Legacy two-class decision (FAST_PONG / NEED_DEEP_THINK)."""

    route_type: str
    reason: str
    confidence: float


def _get_v2_router() -> Any:
    global _V2_ROUTER
    if _V2_ROUTER is None:
        from router_v2.analyzers.router.vanguard_router_v2 import VanguardRouterV2

        _V2_ROUTER = VanguardRouterV2.from_default()
    return _V2_ROUTER


def _downgrade(route_type: str) -> str:
    """Map the v2 three-class label to the legacy two-class label."""

    if route_type == "FAST_PONG":
        return "FAST_PONG"
    # LIGHT_RECALL and DEEP_THINK both go through the non-fast path.
    return "NEED_DEEP_THINK"


async def route_user_turn(
    llm_client: LLMClient,
    llm_model: str,
    user_message: str,
    transcript_messages: list[dict[str, Any]],
) -> RouterDecision:
    """Drop-in replacement for the old cascade.

    Keeps the old async signature and two-class return shape so that
    `runtime_service` does not change. The v2 router is synchronous —
    we just return its verdict in a coroutine.
    """

    # Short-circuit empty / whitespace-only turns — router v2 treats
    # them as LIGHT_RECALL because the LogReg has no strong short-prior
    # for empty, but the orchestration layer never wants a deep pathway
    # for a blank turn.
    if not (user_message or "").strip():
        return RouterDecision(
            route_type="FAST_PONG", reason="empty_message", confidence=1.0
        )

    try:
        decision = _get_v2_router().decide(user_message)
    except Exception as exc:  # pragma: no cover — only triggered on missing artefacts
        logger.warning(
            "Router v2 failed (%s); falling back to legacy LLM classifier.", exc
        )
        return await _legacy_llm_fallback(
            llm_client=llm_client,
            llm_model=llm_model,
            user_message=user_message,
            transcript_messages=transcript_messages,
        )

    return RouterDecision(
        route_type=_downgrade(decision.route_type),
        reason=f"v2::{decision.decided_by}::{decision.reason}",
        confidence=float(decision.confidence),
    )


async def _legacy_llm_fallback(
    *,
    llm_client: LLMClient,
    llm_model: str,
    user_message: str,
    transcript_messages: list[dict[str, Any]],
) -> RouterDecision:
    """Emergency path when v2 artefacts are not on disk (e.g. fresh
    clone without running the trainer). Kept intentionally minimal."""

    warnings.warn(
        "Router v2 unavailable; using emergency legacy LLM fallback.",
        RuntimeWarning,
        stacklevel=2,
    )

    import json

    recent_context: list[str] = []
    for msg in transcript_messages[-4:]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role and content:
            recent_context.append(f"{role.upper()}: {content}")
    context_str = "\n".join(recent_context)

    system_prompt = (
        "Classify the user message as FAST_PONG (casual) or "
        "NEED_DEEP_THINK (memory / identity / crisis). "
        'Return JSON {"route_type": "...", "reason": "..."}.'
    )
    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(
            role="user",
            content=f"Context:\n{context_str}\n\nLatest: {user_message}",
        ),
    ]
    try:
        response = await llm_client.complete(
            request=LLMRequest(
                model=llm_model,
                messages=messages,
                temperature=0.1,
                max_tokens=64,
                response_format="json_object",
            )
        )
        data = json.loads(response.output_text or "{}")
        route_type = str(data.get("route_type", "NEED_DEEP_THINK")).strip()
        reason = str(data.get("reason", "llm_routed")).strip()
        if route_type not in ("FAST_PONG", "NEED_DEEP_THINK"):
            route_type = "NEED_DEEP_THINK"
        return RouterDecision(route_type=route_type, reason=reason, confidence=0.6)
    except Exception as exc:
        logger.warning("Legacy LLM fallback failed: %s", exc)
        return RouterDecision(
            route_type="NEED_DEEP_THINK", reason="llm_error", confidence=0.0
        )
