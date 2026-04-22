"""Legacy Vanguard Router shim.

Old callers::

    from relationship_os.application.analyzers.vanguard_router import (
        route_user_turn, RouterDecision,
    )

still work unchanged. Internally this now delegates to ``router_v2``
(Option D: safety-only rules + distilled LogReg + mini-LLM arbiter).

Deprecated since 2026-04; the legacy LLM fallback remains only for
cases where the v2 artefacts (lexicons / model) fail to load.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from relationship_os.domain.llm import LLMClient, LLMMessage, LLMRequest

logger = logging.getLogger(__name__)

# Lazy so that tests which only exercise the legacy two-class contract
# do not pull in the sklearn / joblib stack at import time.
_V2_ROUTER: Any | None = None


@dataclass(slots=True, frozen=True)
class RouterDecision:
    """Legacy two-class routing decision (FAST_PONG / NEED_DEEP_THINK)."""

    route_type: str
    reason: str
    confidence: float


def _get_v2_router() -> Any:
    """Build (or return cached) VanguardRouterV2 instance."""
    global _V2_ROUTER
    if _V2_ROUTER is None:
        from router_v2.analyzers.router.vanguard_router_v2 import VanguardRouterV2

        _V2_ROUTER = VanguardRouterV2.from_default()
    return _V2_ROUTER


def _downgrade(route_type: str) -> str:
    """Map v2 three-class label to legacy two-class label."""
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
    """Drop-in replacement for the old LLM-based cascade.

    Signature is preserved so ``runtime_service`` keeps working. The v2
    router is synchronous; we return its verdict inside a coroutine.
    """
    # Short-circuit blank turns — keep the exact legacy semantics.
    if not (user_message or "").strip():
        return RouterDecision(
            route_type="FAST_PONG",
            reason="empty_message",
            confidence=1.0,
        )

    try:
        decision = _get_v2_router().decide(user_message)
    except Exception as exc:  # pragma: no cover - artefact-load failure path
        logger.warning(
            "Router v2 failed (%s); falling back to legacy LLM classifier.",
            exc,
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
    """Last-resort LLM classifier used only if router_v2 cannot load."""
    recent_context: list[str] = []
    for msg in transcript_messages[-4:]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role and content:
            recent_context.append(f"{role.upper()}: {content}")
    context_str = "\n".join(recent_context)

    system_prompt = (
        "You are an intent classifier for a chat AI. "
        "Classify if the user's latest message requires deep memory "
        "recall / complex reflection (NEED_DEEP_THINK) or if it's "
        "just casual conversation/venting (FAST_PONG).\n"
        '\nRespond ONLY with a valid JSON: {"route_type": '
        '"FAST_PONG" | "NEED_DEEP_THINK", "reason": "short explanation"}'
    )
    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(
            role="user",
            content=(
                f"Recent Context:\n{context_str}\n\n"
                f"Latest User Message: {user_message}"
            ),
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
        if not response.output_text:
            return RouterDecision(
                route_type="NEED_DEEP_THINK",
                reason="llm_no_response",
                confidence=0.0,
            )
        data = json.loads(response.output_text)
        route_type = str(data.get("route_type", "NEED_DEEP_THINK")).strip()
        reason = str(data.get("reason", "llm_routed")).strip()
        if route_type not in ("FAST_PONG", "NEED_DEEP_THINK"):
            route_type = "NEED_DEEP_THINK"
        return RouterDecision(
            route_type=route_type, reason=reason, confidence=0.85
        )
    except Exception as e:
        logger.warning(
            "Vanguard router fallback failed: %s. Defaulting to NEED_DEEP_THINK.",
            e,
        )
        return RouterDecision(
            route_type="NEED_DEEP_THINK",
            reason="llm_error",
            confidence=0.0,
        )
