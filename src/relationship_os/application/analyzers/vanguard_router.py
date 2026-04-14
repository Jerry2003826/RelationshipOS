import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from relationship_os.domain.llm import LLMClient, LLMMessage, LLMRequest

logger = logging.getLogger(__name__)

@dataclass(slots=True, frozen=True)
class RouterDecision:
    route_type: str  # "FAST_PONG" or "NEED_DEEP_THINK"
    reason: str
    confidence: float

_FAST_PONG_EXACT_MATCHES = {
    "哈哈", "哈哈哈", "哈哈哈哈", "嗯", "嗯嗯", "哦", "哦哦", "好的", "好", "好滴", "行",
    "早", "早上好", "晚安", "拜拜", "再见", "收到", "知道了", "卧槽", "牛逼", "牛",
    "hahaha", "haha", "ok", "okay", "gm", "gn", "bye", "hi", "hello"
}
_FAST_PONG_PATTERN = re.compile(r"^(哈哈+|嗯+|哦+|哈+|呵+|嘿+|呜+|啊+)$")

def _level_1_rule_intercept(user_message: str) -> RouterDecision | None:
    text = str(user_message).strip()
    if not text:
        return RouterDecision(route_type="FAST_PONG", reason="empty_message", confidence=1.0)
    
    # Very short messages
    if len(text) <= 8:
        # Check exact matches
        if text.casefold() in _FAST_PONG_EXACT_MATCHES:
            return RouterDecision(route_type="FAST_PONG", reason="rule_exact_match", confidence=1.0)
        
        # Check patterns like "哈哈哈哈" or "嗯嗯嗯"
        if _FAST_PONG_PATTERN.match(text):
            return RouterDecision(route_type="FAST_PONG", reason="rule_pattern_match", confidence=1.0)
            
    return None

async def route_user_turn(
    llm_client: LLMClient,
    llm_model: str,
    user_message: str,
    transcript_messages: list[dict[str, Any]],
) -> RouterDecision:
    """Hybrid cascade routing to determine if we can fast-track this turn."""
    # LEVEL 1: Quick Rules
    rule_decision = _level_1_rule_intercept(user_message)
    if rule_decision is not None:
        return rule_decision

    # LEVEL 2: Mini-LLM Routing
    recent_context = []
    # Pick last 3 user/assistant turns to give just enough context for intent
    for msg in transcript_messages[-4:]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role and content:
            recent_context.append(f"{role.upper()}: {content}")
            
    context_str = "\n".join(recent_context)
    
    system_prompt = """You are an intent classifier for a chat AI. You must classify if the user's latest message requires deep memory recall / complex reflection (NEED_DEEP_THINK) or if it's just casual conversation/venting that can be replied to instantly (FAST_PONG).

RULES for FAST_PONG:
- Simple greetings, agreements, or short reactions.
- Casual venting ("I'm so tired today") that just needs empathy, not facts.
- Memes, jokes, or teasing that doesn't reference historical facts or other people's secrets.

RULES for NEED_DEEP_THINK:
- Asking factual questions ("What did I say yesterday?", "Who is Alex?").
- Asking the AI about its own identity, persona, or current state.
- Deep, complex emotional crises that require careful step-by-step psychological repair.
- Direct continuations of a deep analytical discussion.

Respond ONLY with a valid JSON in exactly this format:
{
  "route_type": "FAST_PONG" | "NEED_DEEP_THINK",
  "reason": "short explanation"
}"""
    
    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(
            role="user", 
            content=f"Recent Context:\n{context_str}\n\nLatest User Message: {user_message}"
        )
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
            return RouterDecision(route_type="NEED_DEEP_THINK", reason="llm_no_response", confidence=0.0)
            
        content = response.output_text
        data = json.loads(content)
        route_type = str(data.get("route_type", "NEED_DEEP_THINK")).strip()
        reason = str(data.get("reason", "llm_routed")).strip()
        
        if route_type not in ("FAST_PONG", "NEED_DEEP_THINK"):
            route_type = "NEED_DEEP_THINK"
            
        return RouterDecision(route_type=route_type, reason=reason, confidence=0.85)

    except Exception as e:
        logger.warning(f"Vanguard router failed: {e}. Defaulting to NEED_DEEP_THINK.")
        return RouterDecision(route_type="NEED_DEEP_THINK", reason="llm_error", confidence=0.0)
