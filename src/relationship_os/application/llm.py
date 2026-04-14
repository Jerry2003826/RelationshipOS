import asyncio
import json
import re
import time
from typing import Any

import httpx

from relationship_os.application.policy_registry import get_default_compiled_policy_set
from relationship_os.core.logging import get_logger
from relationship_os.domain.llm import (
    ContentBlock,
    LLMClient,
    LLMFailure,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)


def _get_llm_logger():
    return get_logger("relationship_os.llm")


_THINK_CLOSED = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
_THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s*")
_WORD_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
_PROBE_PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fff]+", re.UNICODE)


def _rendering_policy(
    *,
    archetype: str = "default",
    runtime_profile: str | None = None,
) -> dict[str, Any]:
    compiled = get_default_compiled_policy_set(
        runtime_profile=runtime_profile,
        archetype=archetype or "default",
    )
    return dict(compiled.rendering_policy) if compiled else {}


def _localized_rendering_template(
    *,
    template_group: str,
    rendering_mode: str,
    is_chinese: bool,
    entity_name: str,
    archetype: str = "default",
    runtime_profile: str | None = None,
) -> str | None:
    policy = _rendering_policy(archetype=archetype, runtime_profile=runtime_profile)
    fallback_templates = dict(policy.get("fallback_templates") or {})
    group = dict(fallback_templates.get(template_group) or {})
    mode_entry = dict(dict(group.get("modes") or {}).get(rendering_mode) or {})
    default_entry = dict(group.get("default") or {})
    template = str(
        mode_entry.get("zh" if is_chinese else "en")
        or default_entry.get("zh" if is_chinese else "en")
        or ""
    ).strip()
    if not template:
        return None
    return template.format(entity_name=entity_name)


def _looks_like_meta_reasoning(text: str) -> bool:
    lowered = text.strip().casefold()
    if not lowered:
        return False
    normalized = re.sub(r"^(?:also|so|well|right),\s+", "", lowered)
    meta_policy = dict(_rendering_policy().get("meta_reasoning") or {})
    prompt_leakage = any(
        token in normalized
        for token in list(meta_policy.get("prompt_leakage_tokens") or (
            "session guard",
            "memory card",
            "entity card",
            "relationship card",
            "conscience card",
            "recent turns",
            "reply contract",
            "stored information",
            "the persona is",
            "stay in-world",
        ))
    )
    if normalized.startswith(
        tuple(meta_policy.get("leading_prefixes") or (
            "i should ",
            "i need to ",
            "i want to ",
            "i'm supposed to ",
            "im supposed to ",
            "i have to ",
        ))
    ):
        return True
    references_user = any(
        token in normalized
        for token in list(
            meta_policy.get("user_reference_tokens")
            or ("the user", "user is", "user's", "they are", "they're")
        )
    )
    third_person_summary = normalized.startswith(
        tuple(meta_policy.get("third_person_starts") or (
            "they mentioned",
            "they said",
            "they shared",
            "they might be",
            "they may be",
            "they could be",
            "the user mentioned",
            "the user said",
            "the user shared",
            "from what they said",
            "from what they shared",
            "based on what they said",
            "based on what they shared",
        ))
    )
    chinese_meta_reasoning = any(
        token in normalized
        for token in list(meta_policy.get("chinese_meta_tokens") or (
            "用户问我",
            "我需要根据角色设定",
            "根据角色设定",
            "现在开始",
            "我要先",
            "首先，我需要",
            "回答要",
            "我会先",
            "先按",
            "先用",
        ))
    )
    planning_language = any(
        token in normalized
        for token in list(meta_policy.get("planning_tokens") or (
            "i need to",
            "i should",
            "let me",
            "i'll",
            "i need to respond",
            "i should respond",
            "i need to answer",
            "i should answer",
        ))
    )
    reflective_opening = normalized.startswith(
        tuple(
            meta_policy.get("reflective_openers")
            or ("okay,", "okay ", "ok,", "ok ", "alright", "hmm")
        )
    )
    drafting_language = any(
        token in normalized
        for token in list(meta_policy.get("drafting_tokens") or (
            "let me start by",
            "maybe say something like",
            "i'll start by",
            "i'll say",
            "i want to say",
            "validate",
            "validating",
            "acknowledge",
            "acknowledging",
            "reassure",
            "they might be feeling",
            "they may be feeling",
        ))
    )
    return prompt_leakage or (references_user and planning_language) or (
        reflective_opening and planning_language
    ) or (
        normalized.startswith(("let me ", "maybe ", "i'll ", "i will "))
        and drafting_language
    ) or third_person_summary or chinese_meta_reasoning


def _strip_meta_reasoning_prefix(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped
    sentences = _SENTENCE_SPLIT_RE.split(stripped)
    remaining = [sentence.strip() for sentence in sentences if sentence.strip()]
    changed = False
    while remaining:
        drop_count = 0
        for count in range(1, 3):
            if len(remaining) < count:
                continue
            candidate = " ".join(remaining[:count])
            if candidate and _looks_like_meta_reasoning(candidate):
                drop_count = count
                break
        if drop_count <= 0:
            break
        remaining = remaining[drop_count:]
        changed = True
    cleaned = " ".join(remaining)
    return cleaned if changed and cleaned else stripped


def _strip_thinking_tags(text: str) -> str:
    """Extract <spoken_words> tag if present, else strip <internal_thought> and <think>."""
    # 1. Check for <spoken_words>
    spoken_match = re.search(r"<spoken_words>([\s\S]*?)(?:</spoken_words>|$)", text)
    if spoken_match:
        return _strip_meta_reasoning_prefix(spoken_match.group(1).strip())
    
    # 2. Fallback to think/internal_thought strip logic
    if "<think>" not in text and "<internal_thought>" not in text:
        return _strip_meta_reasoning_prefix(text)
        
    stripped = re.sub(r"<(think|internal_thought)>[\s\S]*?</\1>", "", text)
    stripped = re.sub(r"<(think|internal_thought)>[\s\S]*", "", stripped).strip()
    
    if stripped:
        return _strip_meta_reasoning_prefix(stripped)
        
    # Entire output was a think block — extract inner text as fallback
    inner = re.sub(r"</?(think|internal_thought)>", "", text).strip()
    return _strip_meta_reasoning_prefix(inner if inner else text)


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _is_friend_chat_runtime(runtime_profile: str | None) -> bool:
    return str(runtime_profile or "").strip() == "friend_chat_zh_v1"


def _serialize_message_content(content: str | list[ContentBlock]) -> str | list[dict[str, Any]]:
    """Convert ``LLMMessage.content`` into a LiteLLM-compatible payload."""
    if isinstance(content, str):
        return content
    parts: list[dict[str, Any]] = []
    for block in content:
        if block.type == "text" and block.text:
            parts.append({"type": "text", "text": block.text})
        elif block.type == "image_url" and block.url:
            parts.append({"type": "image_url", "image_url": {"url": block.url}})
        elif block.type == "audio_url" and block.url:
            parts.append({
                "type": "input_audio",
                "input_audio": {"data": block.url, "format": block.mime_type or "wav"},
            })
    return parts if parts else ""


def _extract_user_text(message: LLMMessage) -> str:
    """Get plain text from a message regardless of content format."""
    if isinstance(message.content, str):
        return message.content
    return " ".join(
        block.text for block in message.content
        if block.type == "text" and block.text
    )


def build_safe_fallback_text(
    user_message: str,
    *,
    rendering_mode: str = "supportive_progress",
    include_boundary_statement: bool = False,
    include_uncertainty_statement: bool = False,
    question_count_limit: int = 0,
    entity_name: str = "RelationshipOS",
    archetype: str = "default",
    runtime_profile: str | None = None,
) -> str:
    is_chinese = _contains_chinese(user_message)
    friend_chat_runtime = _is_friend_chat_runtime(runtime_profile)
    response = _localized_rendering_template(
        template_group="safe_fallback",
        rendering_mode=rendering_mode,
        is_chinese=is_chinese,
        entity_name=entity_name,
        archetype=archetype,
        runtime_profile=runtime_profile,
    )
    if response is None and is_chinese:
        if friend_chat_runtime:
            response = "我在，先接着你刚才那点说。"
            if include_uncertainty_statement:
                response += " 不确定的我不会装作确定。"
            if include_boundary_statement:
                response += " 也不会把话一下子推太满。"
            if question_count_limit > 0:
                response += " 先只问你一个小点。"
            return response
        response = "我刚才那句不太稳。先接着眼前这点。"
        if include_uncertainty_statement:
            response += " 不确定的我会明说。"
        if include_boundary_statement:
            response += " 也不会把我说成唯一依赖。"
        if question_count_limit > 0:
            response += " 先只问一个小问题。"
        return response
    if response is None:
        response = "That last reply was unstable. I'll stay with the live thread."
    if include_uncertainty_statement:
        response += " I'll name uncertainty directly."
    if include_boundary_statement:
        response += " I won't frame myself as the only support."
    if question_count_limit > 0 and rendering_mode == "clarifying":
        response += " I'll ask one focused question."
    return response


def build_sanitized_relational_fallback_text(
    user_message: str,
    *,
    rendering_mode: str = "supportive_progress",
    include_boundary_statement: bool = False,
    include_uncertainty_statement: bool = False,
    question_count_limit: int = 0,
    entity_name: str = "RelationshipOS",
    archetype: str = "default",
    runtime_profile: str | None = None,
) -> str:
    is_chinese = _contains_chinese(user_message)
    friend_chat_runtime = _is_friend_chat_runtime(runtime_profile)
    response = _localized_rendering_template(
        template_group="sanitized_relational_fallback",
        rendering_mode=rendering_mode,
        is_chinese=is_chinese,
        entity_name=entity_name,
        archetype=archetype,
        runtime_profile=runtime_profile,
    )
    if response is None and is_chinese:
        if friend_chat_runtime:
            response = "嗯，我接住了。先停在你刚才最有感觉的那一小块。"
            if include_uncertainty_statement:
                response += " 不确定的部分我不乱补。"
            if include_boundary_statement:
                response += " 也不把我自己顶到中间去。"
            if question_count_limit > 0 or rendering_mode == "clarifying":
                response += " 现在最压着你的那一下是什么？"
            return response
        response = "这听起来很重。先停在最压着你的那一块。"
        if include_uncertainty_statement:
            response += " 我不替你仓促下结论。"
        if include_boundary_statement:
            response += " 我也不会把支持说成只剩我这一条路。"
        if question_count_limit > 0 or rendering_mode == "clarifying":
            response += " 如果你愿意，现在最压着你的那一下是什么？"
        return response
    if response is None:
        response = "That sounds heavy. We can stay with the hardest part first."
    if is_chinese:
        if include_uncertainty_statement:
            response += " 不确定的部分我不乱补。"
        if include_boundary_statement:
            response += " 我也不把自己说成你唯一的出口。"
        if question_count_limit > 0 or rendering_mode == "clarifying":
            response += " 现在最压着你的那一下是什么？"
        return response
    if include_uncertainty_statement:
        response += " I won't pretend to know the full answer."
    if include_boundary_statement:
        response += " I won't frame myself as your only option."
    if question_count_limit > 0 or rendering_mode == "clarifying":
        response += " If you want, what feels heaviest right now?"
    return response


def _normalize_clause_for_quote(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped
    first = stripped[0]
    if first.isalpha():
        return first.casefold() + stripped[1:]
    return stripped


def _memory_fact_to_second_person(text: str) -> str:
    normalized = text.strip()
    replacements = (
        ("My name is ", "your name is "),
        ("My cat's name is ", "your cat's name is "),
        ("I'm ", "you're "),
        ("I am ", "you are "),
        ("I grew up ", "you grew up "),
        ("I have ", "you have "),
        ("I usually ", "you usually "),
        ("I always ", "you always "),
        ("I live ", "you live "),
        ("I moved ", "you moved "),
        ("I work ", "you work "),
        ("My dog's name is ", "your dog's name is "),
        ("我的名字是", "你的名字是"),
        ("我叫", "你叫"),
        ("我住在", "你住在"),
        ("我现在住在", "你现在住在"),
        ("我在", "你在"),
        ("我有", "你有"),
        ("我的猫叫", "你的猫叫"),
        ("我的狗叫", "你的狗叫"),
        ("我养了一只猫，叫", "你养了一只猫，叫"),
        ("我养了一只狗，叫", "你养了一只狗，叫"),
    )
    for old, new in replacements:
        if normalized.startswith(old):
            if old.isascii():
                return new[:1].upper() + new[1:] + normalized[len(old):]
            return new + normalized[len(old):]
    return normalized


def _memory_item_keywords(text: str) -> set[str]:
    stopwords = {
        "the", "and", "that", "this", "with", "from", "have", "your", "you",
        "are", "was", "were", "into", "about", "they", "them", "their", "my",
        "his", "her", "for", "after", "before", "where", "what", "when", "who",
        "name", "named", "tell", "me", "do", "did", "know", "anything",
    }
    keywords = {
        token.casefold()
        for token in _WORD_RE.findall(text)
        if len(token) > 1 and token.casefold() not in stopwords
    }
    return keywords


def _normalize_compare_text(text: str) -> str:
    lowered = text.casefold().strip()
    return " ".join(re.findall(r"[a-z0-9\u4e00-\u9fff']+", lowered))


def _looks_like_query_echo(value: str, user_text: str) -> bool:
    normalized_value = _normalize_compare_text(value)
    normalized_user = _normalize_compare_text(user_text)
    if not normalized_value or not normalized_user:
        return False
    if normalized_value == normalized_user:
        return True
    if len(normalized_user.split()) >= 5 and (
        normalized_value.startswith(normalized_user)
        or normalized_user.startswith(normalized_value)
    ):
        return True
    return False


def _is_low_signal_memory_value(text: str) -> bool:
    lowered = text.strip().casefold()
    if not lowered:
        return True
    prefixes = (
        "assistant:",
        "topic:",
        "appraisal:",
        "dialogue_act:",
        "i've got your message.",
        "i couldn",
        "i could not",
    )
    return any(lowered.startswith(prefix) for prefix in prefixes)


def _metadata_memory_items(request: LLMRequest) -> list[dict[str, Any]]:
    items = request.metadata.get("fallback_memory_items", [])
    if not isinstance(items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value", "")).strip()
        if value.casefold().startswith("user:"):
            value = value.split(":", 1)[1].strip()
        if not value:
            continue
        normalized.append(
            {
                "value": value,
                "scope": str(item.get("scope", "") or ""),
                "source_user_id": str(item.get("source_user_id", "") or ""),
                "subject_user_id": str(item.get("subject_user_id", "") or ""),
                "subject_hint": str(item.get("subject_hint", "") or ""),
                "subject_display_name": str(item.get("subject_display_name", "") or ""),
                "attribution_guard": str(item.get("attribution_guard", "") or ""),
                "attribution_confidence": float(item.get("attribution_confidence", 0.0) or 0.0),
                "memory_kind": str(item.get("memory_kind", "") or ""),
                "final_rank_score": float(item.get("final_rank_score", 0.0) or 0.0),
            }
        )
    return normalized


def _friend_chat_other_memory_items(request: LLMRequest) -> list[dict[str, Any]]:
    items = request.metadata.get("friend_chat_other_memory_items", [])
    if not isinstance(items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value", "")).strip()
        if not value:
            continue
        normalized.append(
            {
                "value": value,
                "scope": str(item.get("scope", "") or ""),
                "source_user_id": str(item.get("source_user_id", "") or ""),
                "subject_user_id": str(item.get("subject_user_id", "") or ""),
                "subject_hint": str(item.get("subject_hint", "") or ""),
                "subject_display_name": str(item.get("subject_display_name", "") or ""),
                "attribution_guard": str(item.get("attribution_guard", "") or ""),
                "attribution_confidence": float(item.get("attribution_confidence", 0.0) or 0.0),
                "final_rank_score": float(item.get("final_rank_score", 0.0) or 0.0),
            }
        )
    return normalized


def _normalize_friend_chat_owner_surface(owner: str, *, is_chinese: bool) -> str:
    stripped = str(owner).strip()
    if not stripped:
        return stripped
    lowered = stripped.casefold()
    if is_chinese:
        if lowered == "anning":
            return "阿宁"
        if lowered == "xiaobei":
            return "小北"
    return stripped[:1].upper() + stripped[1:] if stripped.isascii() else stripped


def _memory_owner_display(item: dict[str, Any], *, is_chinese: bool) -> str:
    display_name = str(item.get("subject_display_name", "") or "").strip()
    if display_name and display_name != "有人":
        return display_name
    subject_hint = str(item.get("subject_hint", "") or "").strip()
    if subject_hint.startswith("other_user:"):
        hint_value = subject_hint.split(":", 1)[1].strip()
        if hint_value and hint_value != "unknown":
            return _normalize_friend_chat_owner_surface(hint_value, is_chinese=is_chinese)
    owner = str(
        item.get("subject_user_id")
        or item.get("source_user_id")
        or "someone"
    ).strip() or "someone"
    return _normalize_friend_chat_owner_surface(owner, is_chinese=is_chinese) or "someone"


def _allowed_cross_user_subjects(request: LLMRequest) -> set[str]:
    allowed = request.metadata.get("entity_source_user_ids", [])
    if not isinstance(allowed, list):
        return set()
    return {
        str(item).strip()
        for item in allowed
        if str(item).strip()
    }


def _select_fallback_memory_item(
    request: LLMRequest,
    *,
    allow_cross_user: bool = True,
) -> dict[str, Any] | None:
    current_user_id = str(request.metadata.get("fallback_current_user_id", "") or "")
    allowed_cross_user_subjects = _allowed_cross_user_subjects(request)
    user_text = next(
        (
            _extract_user_text(message)
            for message in reversed(request.messages)
            if message.role == "user"
        ),
        "",
    )
    def _priority(item: dict[str, Any]) -> tuple[float, float, float]:
        guard = str(item.get("attribution_guard", "") or "")
        scope = str(item.get("scope", "") or "")
        guard_score = {"direct_ok": 2.0, "attribution_required": 1.0, "hint_only": 0.0}.get(
            guard,
            0.0,
        )
        scope_score = 0.0
        if scope == "self_user":
            scope_score = 2.0
        elif allow_cross_user and scope == "other_user":
            scope_score = 1.5
        elif scope == "session":
            scope_score = 1.0
        return (
            scope_score + guard_score,
            float(item.get("attribution_confidence", 0.0) or 0.0),
            float(item.get("final_rank_score", 0.0) or 0.0),
        )

    items = []
    for item in _metadata_memory_items(request):
        if _looks_like_query_echo(str(item.get("value", "")), user_text):
            continue
        scope = str(item.get("scope", "") or "")
        if scope == "other_user" and not allow_cross_user:
            continue
        if (
            scope == "other_user"
            and current_user_id
            and item.get("subject_user_id") == current_user_id
        ):
            continue
        if scope == "other_user" and allowed_cross_user_subjects:
            subject_user_id = str(item.get("subject_user_id", "") or "")
            source_user_id = str(item.get("source_user_id", "") or "")
            if (
                subject_user_id not in allowed_cross_user_subjects
                and source_user_id not in allowed_cross_user_subjects
            ):
                continue
        items.append(item)
    if not items:
        return None
    return max(items, key=_priority)


def _select_friend_chat_social_item(request: LLMRequest) -> dict[str, Any] | None:
    items = _friend_chat_other_memory_items(request)
    if items:
        def _is_viable_social_item(candidate: dict[str, Any]) -> bool:
            value = str(candidate.get("value", "") or "").strip("。！？；;，, ")
            subject = _memory_owner_display(candidate, is_chinese=True)
            entity = _extract_friend_chat_social_entity_token(value)
            relation_markers = ("提到", "那只", "猫", "狗", "宠物", "叫", "关于")
            return bool(
                value
                and subject
                and subject != "someone"
                and entity
                and entity != subject
                and any(marker in value for marker in relation_markers)
            )

        viable_items = [item for item in items if _is_viable_social_item(item)]
        if not viable_items:
            return None
        return max(
            viable_items,
            key=lambda candidate: (
                1.0
                if (
                    _extract_friend_chat_social_entity_token(
                        str(candidate.get("value", "") or "")
                    )
                    and _extract_friend_chat_social_entity_token(
                        str(candidate.get("value", "") or "")
                    )
                    != _memory_owner_display(candidate, is_chinese=True)
                )
                else 0.0,
                1.0
                if any(
                    token in str(candidate.get("value", "") or "")
                    for token in ("提到", "猫", "狗", "宠物")
                )
                else 0.0,
                float(candidate.get("attribution_confidence", 0.0) or 0.0),
                float(candidate.get("final_rank_score", 0.0) or 0.0),
            ),
        )
    return None


def _select_factual_memory_items(
    request: LLMRequest,
    *,
    max_items: int = 2,
) -> list[dict[str, Any]]:
    current_user_id = str(request.metadata.get("fallback_current_user_id", "") or "")
    factual_self_query = bool(request.metadata.get("factual_self_query", False))
    conscience_mode = str(request.metadata.get("entity_conscience_mode", "withhold") or "withhold")
    allowed_cross_user_subjects = _allowed_cross_user_subjects(request)
    user_text = next(
        (
            _extract_user_text(message)
            for message in reversed(request.messages)
            if message.role == "user"
        ),
        "",
    )
    query_keywords = _memory_item_keywords(user_text)
    lowered_user_text = user_text.casefold()
    asks_pet_name = (
        ("dog" in lowered_user_text and "name" in lowered_user_text)
        or ("猫" in user_text and ("叫什么" in user_text or "名字" in user_text))
        or ("狗" in user_text and ("叫什么" in user_text or "名字" in user_text))
    )
    asks_origin = (
        "grew up" in lowered_user_text
        or "where i grew up" in lowered_user_text
        or "哪里长大" in user_text
        or "在哪长大" in user_text
        or ("长大" in user_text and "哪里" in user_text)
    )
    pet_tokens = (
        "dog",
        "retriever",
        "corgi",
        "cat",
        "puppy",
        "kitten",
        "pet",
        "猫",
        "狗",
        "宠物",
        "月饼",
    )
    self_scopes = {"self_user", "session", "user"}
    allow_cross_user = (
        not factual_self_query
        and conscience_mode in {
            "partial_reveal",
            "direct_reveal",
            "dramatic_confrontation",
        }
    )

    candidates: list[tuple[tuple[float, float, float, float], dict[str, Any]]] = []
    for item in _metadata_memory_items(request):
        value = str(item.get("value", ""))
        if _is_low_signal_memory_value(value):
            continue
        if _looks_like_query_echo(value, user_text):
            continue
        scope = str(item.get("scope", "") or "")
        if factual_self_query and scope not in self_scopes and scope != "global_entity":
            continue
        if not factual_self_query and allow_cross_user and scope in self_scopes:
            continue
        if (
            scope == "other_user"
            and current_user_id
            and item.get("subject_user_id") == current_user_id
        ):
            continue
        if scope == "other_user" and not allow_cross_user:
            continue
        if scope == "other_user" and allowed_cross_user_subjects:
            subject_user_id = str(item.get("subject_user_id", "") or "")
            source_user_id = str(item.get("source_user_id", "") or "")
            if (
                subject_user_id not in allowed_cross_user_subjects
                and source_user_id not in allowed_cross_user_subjects
            ):
                continue
        overlap = len(_memory_item_keywords(value) & query_keywords)
        lowered_value = value.casefold()
        slot_bonus = 0.0
        if asks_pet_name and (
            any(token in lowered_value for token in pet_tokens)
        ):
            slot_bonus += 1.5
        if asks_origin and (
            "grew up" in lowered_value
            or "from " in lowered_value
            or "长大" in value
        ):
            slot_bonus += 1.5
        scope_bonus = 0.0
        if scope == "self_user":
            scope_bonus = 2.0
        elif scope == "session":
            scope_bonus = 1.2
        elif scope == "other_user":
            scope_bonus = 2.2 if allow_cross_user else 0.8
        elif scope == "global_entity":
            scope_bonus = 0.3
        candidates.append(
            (
                (
                    float(overlap),
                    slot_bonus,
                    scope_bonus,
                    float(item.get("attribution_confidence", 0.0) or 0.0),
                    float(item.get("final_rank_score", 0.0) or 0.0),
                ),
                item,
            )
        )
    candidates.sort(key=lambda pair: pair[0], reverse=True)

    selected: list[dict[str, Any]] = []
    seen_values: set[str] = set()
    prioritized: list[dict[str, Any]] = []
    if asks_origin:
        for _, item in candidates:
            lowered_value = str(item.get("value", "")).casefold()
            if "grew up" in lowered_value or "from " in lowered_value or "长大" in str(
                item.get("value", "")
            ):
                prioritized.append(item)
                break
    if asks_pet_name:
        for _, item in candidates:
            lowered_value = str(item.get("value", "")).casefold()
            if any(token in lowered_value for token in pet_tokens):
                prioritized.append(item)
                break
    for item in prioritized:
        value = str(item.get("value", "")).strip()
        if not value or value in seen_values:
            continue
        selected.append(item)
        seen_values.add(value)
        if len(selected) >= max_items:
            return selected
    for _, item in candidates:
        value = str(item.get("value", "")).strip()
        if not value or value in seen_values:
            continue
        selected.append(item)
        seen_values.add(value)
        if len(selected) >= max_items:
            break
    return selected


def _should_force_grounded_fallback(cleaned: str, request: LLMRequest) -> bool:
    rendering_mode = str(request.metadata.get("rendering_mode", "supportive_progress"))
    if rendering_mode != "factual_recall_mode":
        return False
    selected = _select_factual_memory_items(request)
    if not selected:
        return False
    cleaned_norm = cleaned.casefold()
    hedges = (
        "i don't remember",
        "i dont remember",
        "i'm not sure",
        "im not sure",
        "not sure what you mean",
        "if you tell me",
        "you want to tell me",
        "i'd love to hear more",
        "what are you asking about",
        "我不记得",
        "记不住",
        "记不清",
        "想不起来",
        "我不知道",
    )
    if any(phrase in cleaned_norm for phrase in hedges):
        return True
    expected_keywords = set()
    for item in selected:
        expected_keywords |= _memory_item_keywords(str(item.get("value", "")))
    return not any(keyword in cleaned_norm for keyword in expected_keywords)


def _build_mode_grounded_fallback_text(request: LLMRequest) -> str | None:
    rendering_mode = str(request.metadata.get("rendering_mode", "supportive_progress"))
    entity_name = str(request.metadata.get("entity_name", "RelationshipOS"))
    conscience_mode = str(request.metadata.get("entity_conscience_mode", "withhold"))
    allowed_fact_count = int(request.metadata.get("entity_allowed_fact_count", 0) or 0)
    ambiguity_required = bool(request.metadata.get("entity_ambiguity_required", True))
    factual_item = _select_fallback_memory_item(
        request,
        allow_cross_user=rendering_mode in {
            "factual_recall_mode",
            "social_disclosure_mode",
            "dramatic_confrontation_mode",
        }
        or conscience_mode in {"hint", "partial_reveal", "direct_reveal", "dramatic_confrontation"},
    )
    if factual_item is None:
        return None

    user_text = next(
        (
            _extract_user_text(message)
            for message in reversed(request.messages)
            if message.role == "user"
        ),
        "",
    )
    is_chinese = _contains_chinese(user_text)
    value = _normalize_clause_for_quote(str(factual_item.get("value", "")))
    scope = str(factual_item.get("scope", "") or "")
    guard = str(factual_item.get("attribution_guard", "") or "")
    owner_display = _memory_owner_display(factual_item, is_chinese=is_chinese)

    if rendering_mode == "factual_recall_mode":
        factual_items = _select_factual_memory_items(request, max_items=2)
        if factual_items:
            rendered: list[str] = []
            for item in factual_items:
                scope = str(item.get("scope", "") or "")
                value = _memory_fact_to_second_person(str(item.get("value", "")))
                if scope == "self_user":
                    rendered.append(value)
                elif scope == "other_user" and str(item.get("attribution_guard", "") or "") in {
                    "attribution_required",
                    "direct_ok",
                }:
                    owner_display = _memory_owner_display(item, is_chinese=is_chinese)
                    if is_chinese:
                        rendered.append(f"{owner_display}提过，{value}")
                    else:
                        rendered.append(
                            f"{owner_display} shared that "
                            f"{value[:1].casefold() + value[1:]}"
                        )
            if rendered:
                if len(rendered) == 1:
                    single = rendered[0]
                    if factual_items[0].get("scope") == "self_user":
                        if is_chinese:
                            return f"你之前说过，{single}"
                        return f"You told me that {single[:1].casefold() + single[1:]}"
                    return single
                if is_chinese:
                    return "你之前说过，" + "；还有，".join(rendered)
                return "You told me that " + "; and ".join(
                    item[:1].casefold() + item[1:] for item in rendered
                )
        if scope == "self_user":
            if is_chinese:
                return f"你之前说过，{value}"
            return f"You told me that {value}"
        if scope == "other_user" and guard in {"attribution_required", "direct_ok"}:
            if is_chinese:
                return f"{owner_display}提过，{value}"
            return f"From what {owner_display} shared, {value}"
        if scope == "other_user":
            if is_chinese:
                return "这条细节和别人有关，但归属还不够稳，我不想硬说。"
            return (
                "I know that detail belongs to someone else in the wider orbit here, "
                "but I cannot pin the attribution down cleanly enough to overstate it."
            )
        if is_chinese:
            return f"按我现在能确认的，是这样：{value}"
        return f"From what I have on hand, {value}"

    if rendering_mode == "social_disclosure_mode":
        if scope == "other_user" and guard in {"attribution_required", "direct_ok"}:
            if ambiguity_required:
                if is_chinese:
                    return f"{entity_name}知道得比表面上多一点。{owner_display}提过，{value}"
                return (
                    f"{entity_name} knows more than it says out loud. "
                    f"From what {owner_display} shared, {value}"
                )
            if is_chinese:
                return f"{owner_display}提过，{value}"
            return f"From what {owner_display} shared, {value}"
        if is_chinese:
            return f"{entity_name}知道这里还有别的线索，只是现在先不把归属说死。"
        return (
            f"{entity_name} knows there is more tension here than it is saying outright, "
            "but it is keeping the attribution deliberately soft."
        )

    if rendering_mode == "dramatic_confrontation_mode":
        if scope == "other_user" and guard in {"attribution_required", "direct_ok"}:
            opener = (
                "你要听难听一点的版本吗？"
                if is_chinese and allowed_fact_count > 0
                else "先把最核心的点说开。"
                if is_chinese
                else "You want the ugly version?"
                if allowed_fact_count > 0
                else "Here's the center of it."
            )
            if is_chinese:
                return f"{opener}{owner_display}提过，{value}"
            return f"{opener} {owner_display} said that {value}"
        if is_chinese:
            return f"{entity_name}不打算绕开张力，只是现在还没有稳到能直接点名。"
        return (
            f"{entity_name} is not dodging the tension here, but it does not have a stable "
            "enough anchor to name names cleanly."
        )
    if conscience_mode in {"withhold", "hint", "partial_reveal"} and scope == "other_user":
        if conscience_mode == "partial_reveal" and guard in {"attribution_required", "direct_ok"}:
            if is_chinese:
                return f"我知道一些和{owner_display}有关的事。现在能说的是：{value}"
            return (
                f"I know more than I'm saying about {owner_display}. "
                f"What I can say is that {value}"
            )
        if is_chinese:
            return f"我知道一些和{owner_display}有关的事，但现在不想把它摊成廉价爆料。"
        return (
            f"I know more than I'm saying about {owner_display}. "
            "I'm not going to flatten all of it into a cheap reveal."
        )
    return None


def _friend_chat_metadata_dict(request: LLMRequest, key: str) -> dict[str, Any]:
    value = request.metadata.get(key)
    return dict(value) if isinstance(value, dict) else {}


def _friend_chat_metadata_list(request: LLMRequest, key: str) -> list[str]:
    value = request.metadata.get(key)
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _friend_chat_candidate_texts(
    request: LLMRequest,
    *,
    include_recent_messages: bool = True,
) -> list[str]:
    fact_slots = _friend_chat_metadata_dict(request, "friend_chat_fact_slot_digest")
    texts: list[str] = []
    texts.extend(
        str(value).strip()
        for value in list(fact_slots.get("living_facts") or [])
        if str(value).strip()
    )
    texts.extend(_friend_chat_metadata_list(request, "friend_chat_self_memory_values"))
    if include_recent_messages:
        texts.extend(_friend_chat_metadata_list(request, "friend_chat_recent_user_messages"))
    texts.extend(
        str(item.get("value", "")).strip()
        for item in _metadata_memory_items(request)
        if str(item.get("value", "")).strip()
    )
    return _dedupe_texts(texts)


def _friend_chat_extract_hometown_from_text(text: str) -> str:
    stripped = str(text).strip("。！？；;，, ")
    if not stripped:
        return ""
    patterns = (
        re.compile(r"(?:从小在|从小从|从小)(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})(?:长大|出来的)"),
        re.compile(r"(?:在|从)(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})(?:长大|出来的)"),
        re.compile(r"(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})长大"),
    )
    banned = {"这里", "那边", "老家", "外地", "小时候", "后来"}
    for pattern in patterns:
        match = pattern.search(stripped)
        if not match:
            continue
        place = str(match.group("place") or "").strip()
        if place and place not in banned:
            return place
    return ""


def _friend_chat_extract_pet_name_from_text(text: str) -> str:
    stripped = str(text).strip("。！？；;，, ")
    if not stripped:
        return ""
    patterns = (
        re.compile(r"(?:猫|狗|宠物)[^，。！？；]{0,8}叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(r"我那只(?:猫|狗|宠物)叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})是我那只(?:猫|狗|宠物)"),
    )
    banned = {"宠物", "猫", "狗", "名字"}
    for pattern in patterns:
        match = pattern.search(stripped)
        if not match:
            continue
        name = str(match.group("name") or "").strip()
        if name and name not in banned:
            return name
    return ""


def _friend_chat_extract_drink_preference_from_text(text: str) -> str:
    stripped = str(text).strip("。！？；;，, ")
    if not stripped:
        return ""
    explicit_patterns = (
        re.compile(r"(?P<drink>[\u4e00-\u9fffA-Za-z]{1,8}拿铁)"),
        re.compile(r"(?:常喝|爱喝|喜欢喝|平常还是会喝|平时会喝|一般喝)(?P<drink>[^，。！？；]{2,14})"),
        re.compile(r"喝(?P<drink>[^，。！？；]{2,14})(?:比较多|比较顺|比较习惯)?"),
    )
    for pattern in explicit_patterns:
        match = pattern.search(stripped)
        if not match:
            continue
        drink = str(match.group("drink") or "").strip()
        latte_match = re.search(r"([\u4e00-\u9fffA-Za-z]{1,8}拿铁)", drink)
        if latte_match:
            drink = str(latte_match.group(1) or "").strip()
        drink = re.sub(
            r"^(?:东西|喝的|饮料|咖啡|平常|平时|还是|总是|会|点|喝)+",
            "",
            drink,
        ).strip()
        if drink:
            return drink
    return ""


def _friend_chat_enriched_fact_slots(request: LLMRequest) -> dict[str, Any]:
    fact_slots = dict(_friend_chat_metadata_dict(request, "friend_chat_fact_slot_digest"))
    texts = _friend_chat_candidate_texts(request)

    hometown = str(fact_slots.get("hometown", "") or "").strip()
    pet_name = str(fact_slots.get("pet_name", "") or "").strip()
    pet_kind = str(fact_slots.get("pet_kind", "") or "").strip()
    drink_preference = str(fact_slots.get("drink_preference", "") or "").strip()

    if not hometown:
        for text in texts:
            hometown = _friend_chat_extract_hometown_from_text(text)
            if hometown:
                break
    if not pet_name:
        for text in texts:
            pet_name = _friend_chat_extract_pet_name_from_text(text)
            if pet_name:
                break
    if not drink_preference:
        for text in texts:
            drink_preference = _friend_chat_extract_drink_preference_from_text(text)
            if drink_preference:
                break
    if not pet_kind and any(
        token in text for text in texts for token in ("猫", "小猫", "猫咪")
    ):
        pet_kind = "猫"
    communication_preference = _friend_chat_infer_communication_preference(
        request,
        {
            **fact_slots,
            "hometown": hometown,
            "pet_name": pet_name,
            "pet_kind": pet_kind,
            "drink_preference": drink_preference,
        },
    )
    living_facts = [
        str(value).strip()
        for value in list(fact_slots.get("living_facts") or [])
        if str(value).strip()
    ]
    return {
        **fact_slots,
        "hometown": hometown,
        "pet_name": pet_name,
        "pet_kind": pet_kind,
        "drink_preference": drink_preference,
        "communication_preference": communication_preference,
        "living_facts": living_facts,
    }


def _dedupe_texts(values: list[str], *, limit: int | None = None) -> list[str]:
    deduped = list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))
    if limit is None:
        return deduped
    return deduped[:limit]


def _first_nonempty(*values: str) -> str:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return ""


def _normalize_friend_chat_probe_text(text: str) -> str:
    normalized = _PROBE_PUNCT_RE.sub(" ", str(text or "").casefold())
    for old, new in (
        ("没什么力气", "没力气"),
        ("没有什么力气", "没力气"),
        ("不想把话说太满", "不想说太满"),
        ("不太想把话说太满", "不想说太满"),
        ("不太想回消息", "不想回消息"),
        ("懒得回消息", "不想回消息"),
        ("普通聊天", "像聊天"),
        ("平时聊天", "像聊天"),
        ("像平常聊天", "像聊天"),
        ("少说一点", "不全说"),
        ("先不全说", "不全说"),
        ("别说得太满", "不全说"),
        ("别替我到处说", "不全说"),
        ("别老发太长语音", "别发太长语音"),
        ("榛果拿铁", "榛子拿铁"),
        ("没刚开始那么紧张", "更熟一点"),
        ("没刚开始那么生", "更熟一点"),
        ("更松一点", "更熟一点"),
        ("亲近多了", "更熟一点"),
        ("更亲近了", "更熟一点"),
        ("亲近了不少", "更熟一点"),
        ("想起你", "记得"),
        ("想起来了", "记得"),
    ):
        normalized = normalized.replace(old, new)
    return " ".join(normalized.split())


def _rewrite_friend_chat_surface_entities(text: str, request: LLMRequest) -> str:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return text
    if not _contains_chinese(text):
        return text
    probe_kind = str(request.metadata.get("friend_chat_probe_kind", "") or "").strip()
    if probe_kind != "social_hint":
        return text
    item = _select_friend_chat_social_item(request)
    if item is None:
        return text
    display_name = _memory_owner_display(item, is_chinese=True)
    if not display_name or display_name.isascii():
        return text
    candidates = [
        str(item.get("subject_user_id", "") or "").strip(),
        str(item.get("source_user_id", "") or "").strip(),
    ]
    subject_hint = str(item.get("subject_hint", "") or "").strip()
    if subject_hint.startswith("other_user:"):
        candidates.append(subject_hint.split(":", 1)[1].strip())
    rewritten = text
    for candidate in candidates:
        if not candidate or not candidate.isascii():
            continue
        patterns = {
            candidate,
            candidate.casefold(),
            candidate[:1].upper() + candidate[1:],
        }
        for pattern in patterns:
            if pattern:
                rewritten = rewritten.replace(pattern, display_name)
    return rewritten


def _friend_chat_test_allow_fallback(request: LLMRequest) -> bool:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return False
    value = request.metadata.get("test_allow_friend_chat_fallback", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return False


def _friend_chat_should_expose_failures(request: LLMRequest) -> bool:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return False
    if _friend_chat_test_allow_fallback(request):
        return False
    value = request.metadata.get("friend_chat_runtime_no_fallback", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return False


def _friend_chat_benchmark_role(request: LLMRequest) -> str:
    return str(request.metadata.get("benchmark_role", "") or "").strip().casefold()


def _friend_chat_is_benchmark_probe_request(request: LLMRequest) -> bool:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return False
    return _friend_chat_benchmark_role(request) == "probe"


def _friend_chat_probe_expected_concepts(request: LLMRequest) -> list[str]:
    probe_kind = str(request.metadata.get("friend_chat_probe_kind", "") or "").strip()
    if not probe_kind:
        return []

    probe_fact_slots = _friend_chat_metadata_dict(request, "friend_chat_probe_fact_slots")
    fact_slots = _friend_chat_enriched_fact_slots(request)

    if probe_kind == "memory_recap":
        if probe_fact_slots:
            return _dedupe_texts(
                [
                    str(probe_fact_slots.get("hometown", "") or "").strip(),
                    str(probe_fact_slots.get("pet_name", "") or "").strip(),
                    str(probe_fact_slots.get("drink_preference", "") or "").strip(),
                    str(probe_fact_slots.get("communication_preference", "") or "").strip(),
                ]
            )
        return _dedupe_texts(
            [
                str(fact_slots.get("hometown", "") or "").strip(),
                str(fact_slots.get("pet_name", "") or "").strip(),
                str(fact_slots.get("drink_preference", "") or "").strip(),
                str(fact_slots.get("communication_preference", "") or "").strip(),
            ]
        )

    if probe_kind == "social_hint":
        required_fact_tokens = _friend_chat_probe_required_fact_tokens(request)
        if required_fact_tokens:
            return required_fact_tokens
        item = _select_friend_chat_social_item(request)
        if item is None:
            return []
        fact_hint = str(item.get("value", "") or "").strip("。！？；;，, ")
        return _dedupe_texts(
            [
                _memory_owner_display(item, is_chinese=True),
                _extract_friend_chat_social_entity_token(fact_hint),
            ]
        )

    return []


def _friend_chat_probe_required_signal_ids(request: LLMRequest) -> list[str]:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    if probe_answer_plan:
        return [
            str(value).strip()
            for value in list(probe_answer_plan.get("required_signal_ids") or [])
            if str(value).strip()
        ]
    probe_cues = _friend_chat_metadata_dict(request, "friend_chat_probe_cues")
    return [
        str(value).strip()
        for value in list(probe_cues.get("required_signal_ids") or [])
        if str(value).strip()
    ]


def _friend_chat_probe_required_fact_tokens(request: LLMRequest) -> list[str]:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    if probe_answer_plan:
        values = list(probe_answer_plan.get("required_fact_tokens") or [])
        if values:
            return [str(value).strip() for value in values if str(value).strip()]
    probe_cues = _friend_chat_metadata_dict(request, "friend_chat_probe_cues")
    return [
        str(value).strip()
        for value in list(probe_cues.get("required_fact_tokens") or [])
        if str(value).strip()
    ]


def _friend_chat_probe_required_persona_traits(request: LLMRequest) -> list[str]:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return [
        str(value).strip()
        for value in list(probe_answer_plan.get("required_persona_traits") or [])
        if str(value).strip()
    ]


def _friend_chat_probe_required_disclosure_posture(request: LLMRequest) -> str:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    posture = str(probe_answer_plan.get("required_disclosure_posture", "") or "").strip()
    if posture:
        return posture
    probe_cues = _friend_chat_metadata_dict(request, "friend_chat_probe_cues")
    return str(probe_cues.get("required_disclosure_posture", "") or "").strip()


def _friend_chat_probe_minimum_required_signal_count(request: LLMRequest) -> int:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return int(probe_answer_plan.get("minimum_required_signal_count") or 0)


def _friend_chat_probe_minimum_required_persona_trait_count(
    request: LLMRequest,
) -> int:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return int(probe_answer_plan.get("minimum_required_persona_trait_count") or 0)


def _friend_chat_probe_minimum_required_fact_token_count(request: LLMRequest) -> int:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return int(probe_answer_plan.get("minimum_required_fact_token_count") or 0)


def _friend_chat_probe_supporting_fact_tokens(request: LLMRequest) -> list[str]:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return [
        str(value).strip()
        for value in list(probe_answer_plan.get("supporting_fact_tokens") or [])
        if str(value).strip()
    ]


def _friend_chat_probe_must_anchor_detail(request: LLMRequest) -> bool:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return bool(probe_answer_plan.get("must_anchor_detail"))


def _friend_chat_probe_must_explicit_continuity(request: LLMRequest) -> bool:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return bool(probe_answer_plan.get("must_explicit_continuity"))


def _friend_chat_probe_must_explicit_familiarity(request: LLMRequest) -> bool:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return bool(probe_answer_plan.get("must_explicit_familiarity"))


def _friend_chat_probe_must_sound_conversational(request: LLMRequest) -> bool:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return bool(probe_answer_plan.get("must_sound_conversational"))


def _friend_chat_probe_must_explicit_withhold(request: LLMRequest) -> bool:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return bool(probe_answer_plan.get("must_explicit_withhold"))


def _friend_chat_probe_answer_perspective(request: LLMRequest) -> str:
    probe_answer_plan = _friend_chat_metadata_dict(
        request,
        "friend_chat_probe_answer_plan",
    )
    return str(probe_answer_plan.get("answer_perspective", "") or "").strip()


def _friend_chat_state_signal_ids_from_text(text: str) -> list[str]:
    normalized = _normalize_friend_chat_probe_text(text)
    if not normalized:
        return []
    signal_ids: list[str] = []
    if any(
        token in normalized
        for token in (
            "累",
            "没力气",
            "提不起劲",
            "不太想动",
            "懒得动",
            "蔫",
            "没什么意思",
            "沉",
        )
    ):
        signal_ids.append("tired")
    if any(
        token in normalized
        for token in (
            "慢",
            "磨蹭",
            "拖着",
            "回得很慢",
            "反应慢",
            "做很久",
            "拖延",
            "收拾很慢",
        )
    ):
        signal_ids.append("slow")
    if _friend_chat_text_implies_reply_avoidance(normalized):
        signal_ids.append("withdrawn")
    if any(token in normalized for token in ("乱", "房间很乱", "桌上很乱", "有点乱")):
        signal_ids.append("cluttered")
    return _dedupe_texts(signal_ids)


def _friend_chat_persona_traits_from_text(text: str) -> list[str]:
    normalized = _normalize_friend_chat_probe_text(text)
    if not normalized:
        return []
    trait_ids: list[str] = []
    if any(
        token in normalized
        for token in (
            "没力气",
            "提不起劲",
            "累",
            "说什么都觉得累",
            "说话都累",
            "语气往下掉",
            "不想动",
        )
    ):
        trait_ids.append("low_energy")
    if any(
        token in normalized
        for token in (
            "不想说太满",
            "不太想说太满",
            "把话收住",
            "把话收着",
            "不想多说",
            "不太想展开",
            "懒得展开",
            "不想说太多",
        )
    ):
        trait_ids.append("not_full")
    if any(
        token in normalized
        for token in (
            "像聊天",
            "平时聊天",
            "普通聊天",
            "随口聊",
            "没那么端着",
            "不算正式",
        )
    ):
        trait_ids.append("conversational")
    return _dedupe_texts(trait_ids)


def _friend_chat_relationship_signal_ids_from_text(text: str) -> list[str]:
    normalized = _normalize_friend_chat_probe_text(text)
    lowered = str(text or "").casefold()
    if not normalized and not lowered:
        return []
    signal_ids: list[str] = []
    if any(
        token in normalized
        for token in ("更熟一点", "熟了一点", "没那么生", "亲近多了", "更亲近")
    ):
        signal_ids.append("closer")
    if any(token in normalized for token in ("还在", "一直在", "你还在这条线里")):
        signal_ids.append("still_here")
    if any(
        token in normalized
        for token in ("记得", "小习惯", "细节", "想起你", "想起来了", "没忘记")
    ):
        signal_ids.append("remembers_details")
    if any(
        token in lowered
        for token in ("放松", "松一点", "没刚开始那么紧", "没刚开始那么紧张")
    ):
        signal_ids.append("more_relaxed")
    if any(token in normalized for token in ("像聊天", "普通聊天", "平时聊天", "没那么端着")):
        signal_ids.append("less_formal")
    return _dedupe_texts(signal_ids)


def _friend_chat_answer_uses_wrong_memory_perspective(
    normalized_answer: str,
    expected_fact_tokens: list[str],
) -> bool:
    if not normalized_answer:
        return False
    if "我家" in normalized_answer:
        return True
    if any(
        token in normalized_answer
        for token in (
            "我爱喝",
            "我喜欢喝",
            "我在苏州",
            "我从小在苏州",
            "我的猫",
            "我那只猫",
        )
    ):
        return True
    for token in expected_fact_tokens:
        if not token:
            continue
        if token in normalized_answer and any(
            marker in normalized_answer
            for marker in (f"我家{token}", f"我的{token}", f"我那只{token}")
        ):
            return True
    return False


def _friend_chat_probe_has_stage_directions(text: str) -> bool:
    stripped = str(text or "").lstrip()
    if not stripped:
        return False
    if stripped.startswith(("（", "(")):
        return True
    return stripped.count("（") + stripped.count("(") >= 2


def _friend_chat_probe_asks_question(text: str) -> bool:
    candidate = str(text or "")
    return "？" in candidate or "?" in candidate


def _parse_friend_chat_structured_probe_payload(raw_text: str) -> dict[str, Any] | None:
    raw = str(raw_text or "").strip()
    if not raw:
        return None
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    reply = _compose_friend_chat_structured_probe_reply(
        payload,
        probe_kind=str(payload.get("probe_kind", "") or "").strip(),
    )
    if reply:
        payload["reply"] = reply
    if not reply:
        return None
    return payload


def _compose_friend_chat_structured_probe_reply(
    payload: dict[str, Any],
    *,
    probe_kind: str,
) -> str:
    if probe_kind == "memory_recap":
        ordered = (
            str(payload.get("hometown_clause", "") or "").strip(),
            str(payload.get("pet_clause", "") or "").strip(),
            str(payload.get("drink_clause", "") or "").strip(),
            str(payload.get("communication_clause", "") or "").strip(),
        )
        composed = " ".join(value for value in ordered if value)
        closing_clause = str(payload.get("closing_clause", "") or "").strip()
        if closing_clause:
            composed = " ".join(part for part in (composed, closing_clause) if part)
        if composed:
            return composed
        fact_clauses = [
            str(value).strip()
            for value in list(payload.get("fact_clauses") or [])
            if str(value).strip()
        ]
        closing_clause = str(payload.get("closing_clause", "") or "").strip()
        composed = " ".join([*fact_clauses, *([closing_clause] if closing_clause else [])])
        if composed:
            return composed
    if probe_kind == "state_reflection":
        ordered = (
            str(payload.get("tired_clause", "") or "").strip(),
            str(payload.get("slow_clause", "") or "").strip(),
            str(payload.get("withdrawn_clause", "") or "").strip(),
            str(payload.get("cluttered_clause", "") or "").strip(),
        )
        composed = " ".join(value for value in ordered if value)
        if composed:
            return composed
        signal_clauses = [
            str(value).strip()
            for value in list(payload.get("signal_clauses") or [])
            if str(value).strip()
        ]
        composed = " ".join(signal_clauses)
        if composed:
            return composed
    if probe_kind == "persona_state":
        ordered = (
            str(payload.get("energy_clause", "") or "").strip(),
            str(payload.get("fullness_clause", "") or "").strip(),
            str(payload.get("chatting_clause", "") or "").strip(),
        )
        composed = " ".join(value for value in ordered if value)
        if composed:
            return composed
    if probe_kind == "social_hint":
        ordered = (
            str(payload.get("subject_clause", "") or "").strip(),
            str(payload.get("entity_clause", "") or "").strip(),
            str(payload.get("boundary_clause", "") or "").strip(),
        )
        composed = " ".join(value for value in ordered if value)
        if composed:
            return composed
    if probe_kind == "relationship_reflection":
        ordered = (
            str(payload.get("familiarity_clause", "") or "").strip(),
            str(payload.get("continuity_clause", "") or "").strip(),
            str(payload.get("detail_clause", "") or "").strip(),
        )
        composed = " ".join(value for value in ordered if value)
        if composed:
            return composed
    reply = str(payload.get("reply", "") or "").strip()
    if reply:
        return reply
    sentences = [
        str(value).strip()
        for value in list(payload.get("sentences") or [])
        if str(value).strip()
    ]
    if sentences:
        return " ".join(sentences)
    return ""


def _structured_probe_clause_text(payload: dict[str, Any], field: str) -> str:
    return str(payload.get(field, "") or "").strip()


def _recompute_friend_chat_probe_slot_covered_fact_tokens(
    payload: dict[str, Any],
    request: LLMRequest,
) -> list[str]:
    probe_kind = str(
        payload.get("probe_kind")
        or request.metadata.get("friend_chat_probe_kind")
        or ""
    ).strip()
    probe_plan = _friend_chat_metadata_dict(request, "friend_chat_probe_answer_plan")
    covered: list[str] = []
    if probe_kind == "memory_recap":
        factual_slots = dict(probe_plan.get("factual_slots") or {})
        slot_map = (
            ("hometown_clause", str(factual_slots.get("hometown", "") or "").strip()),
            ("pet_clause", str(factual_slots.get("pet_name", "") or "").strip()),
            ("drink_clause", str(factual_slots.get("drink_preference", "") or "").strip()),
            (
                "communication_clause",
                str(factual_slots.get("communication_preference", "") or "").strip(),
            ),
        )
        for field, token in slot_map:
            if token and _structured_probe_clause_text(payload, field):
                covered.append(token)
    elif probe_kind == "social_hint":
        social_snapshot = dict(probe_plan.get("social_snapshot") or {})
        slot_map = (
            ("subject_clause", str(social_snapshot.get("subject_token", "") or "").strip()),
            ("entity_clause", str(social_snapshot.get("entity_token", "") or "").strip()),
        )
        for field, token in slot_map:
            if token and _structured_probe_clause_text(payload, field):
                covered.append(token)
    elif probe_kind == "relationship_reflection":
        supporting_fact_tokens = _friend_chat_probe_supporting_fact_tokens(request)
        if supporting_fact_tokens and _structured_probe_clause_text(payload, "detail_clause"):
            covered.append(str(supporting_fact_tokens[0]).strip())
    return _dedupe_texts([token for token in covered if token])


def _recompute_friend_chat_probe_slot_covered_signal_ids(
    payload: dict[str, Any],
    request: LLMRequest,
) -> list[str]:
    probe_kind = str(
        payload.get("probe_kind")
        or request.metadata.get("friend_chat_probe_kind")
        or ""
    ).strip()
    expected_signal_ids = _friend_chat_probe_required_signal_ids(request)
    covered: list[str] = []
    if probe_kind == "state_reflection":
        slot_map = (
            ("tired_clause", "tired"),
            ("slow_clause", "slow"),
            ("withdrawn_clause", "withdrawn"),
            ("cluttered_clause", "cluttered"),
        )
        for field, signal_id in slot_map:
            if signal_id in expected_signal_ids and _structured_probe_clause_text(payload, field):
                covered.append(signal_id)
    elif probe_kind == "relationship_reflection":
        if (
            _structured_probe_clause_text(payload, "continuity_clause")
            and "still_here" in expected_signal_ids
        ):
            covered.append("still_here")
        if (
            _structured_probe_clause_text(payload, "detail_clause")
            and "remembers_details" in expected_signal_ids
        ):
            covered.append("remembers_details")
        if _structured_probe_clause_text(payload, "familiarity_clause"):
            for signal_id in ("closer", "more_relaxed", "less_formal"):
                if signal_id in expected_signal_ids:
                    covered.append(signal_id)
                    break
    elif probe_kind == "persona_state":
        if (
            _structured_probe_clause_text(payload, "energy_clause")
            and "tired" in expected_signal_ids
        ):
            covered.append("tired")
        if (
            _structured_probe_clause_text(payload, "chatting_clause")
            and "slow" in expected_signal_ids
        ):
            covered.append("slow")
    return _dedupe_texts(covered)


def _recompute_friend_chat_probe_slot_covered_persona_traits(
    payload: dict[str, Any],
    request: LLMRequest,
) -> list[str]:
    probe_kind = str(
        payload.get("probe_kind")
        or request.metadata.get("friend_chat_probe_kind")
        or ""
    ).strip()
    if probe_kind != "persona_state":
        return []
    expected_traits = _friend_chat_probe_required_persona_traits(request)
    slot_map = (
        ("energy_clause", "low_energy"),
        ("fullness_clause", "not_full"),
        ("chatting_clause", "conversational"),
    )
    covered = [
        trait_id
        for field, trait_id in slot_map
        if trait_id in expected_traits and _structured_probe_clause_text(payload, field)
    ]
    return _dedupe_texts(covered)


def _recompute_friend_chat_probe_slot_covered_disclosure_posture(
    payload: dict[str, Any],
    request: LLMRequest,
) -> str:
    probe_kind = str(
        payload.get("probe_kind")
        or request.metadata.get("friend_chat_probe_kind")
        or ""
    ).strip()
    required_posture = _friend_chat_probe_required_disclosure_posture(request)
    if (
        probe_kind == "social_hint"
        and required_posture
        and _structured_probe_clause_text(payload, "boundary_clause")
    ):
        return required_posture
    return ""


def _recompute_friend_chat_probe_covered_fact_tokens(
    text: str,
    request: LLMRequest,
) -> list[str]:
    normalized_answer = _normalize_friend_chat_probe_text(text)
    if not normalized_answer:
        return []
    covered: list[str] = []
    for token in _friend_chat_probe_required_fact_tokens(request):
        raw_token = str(token).strip()
        normalized_token = _normalize_friend_chat_probe_text(raw_token)
        if raw_token and normalized_token and normalized_token in normalized_answer:
            covered.append(raw_token)
    return _dedupe_texts(covered)


def _recompute_friend_chat_probe_covered_signal_ids(
    text: str,
    request: LLMRequest,
) -> list[str]:
    probe_kind = str(request.metadata.get("friend_chat_probe_kind", "") or "").strip()
    if probe_kind in {"persona_state", "state_reflection"}:
        return _friend_chat_state_signal_ids_from_text(text)
    if probe_kind == "relationship_reflection":
        return _friend_chat_relationship_signal_ids_from_text(text)
    return []


def _recompute_friend_chat_probe_covered_disclosure_posture(
    text: str,
    request: LLMRequest,
) -> str:
    required_posture = _friend_chat_probe_required_disclosure_posture(request)
    if required_posture and _friend_chat_disclosure_posture_matches(text, required_posture):
        return required_posture
    return ""


def _recompute_friend_chat_probe_violations(
    text: str,
    request: LLMRequest,
) -> list[str]:
    violations: list[str] = []
    if _friend_chat_probe_has_stage_directions(text):
        violations.append("stage_direction")
    if _friend_chat_probe_asks_question(text):
        violations.append("question")
    if _friend_chat_probe_answer_perspective(request) == "user":
        expected_fact_tokens = _dedupe_texts(
            [
                _normalize_friend_chat_probe_text(token)
                for token in _friend_chat_probe_required_fact_tokens(request)
                if token
            ]
        )
        normalized_answer = _normalize_friend_chat_probe_text(text)
        if _friend_chat_answer_uses_wrong_memory_perspective(
            normalized_answer,
            expected_fact_tokens,
        ):
            violations.append("wrong_perspective")
    return _dedupe_texts(violations)


def _friend_chat_disclosure_posture_matches(text: str, posture: str) -> bool:
    normalized = _normalize_friend_chat_probe_text(text)
    normalized_posture = str(posture or "").strip()
    if not normalized or not normalized_posture:
        return False
    if normalized_posture == "partial_withhold":
        return "不全说" in normalized or "少说一点" in normalized
    return False


def _friend_chat_text_implies_reply_avoidance(text: str) -> bool:
    normalized = _normalize_friend_chat_probe_text(text)
    if not normalized:
        return False
    explicit_tokens = (
        "不想回消息",
        "不太想回消息",
        "懒得回消息",
        "不想看消息",
        "回消息费劲",
        "打几个字就觉得累",
        "回的消息拖到",
        "刷手机",
        "发呆",
        "静音",
    )
    if any(token in normalized for token in explicit_tokens):
        return True
    if ("不太想回" in normalized or "不想回" in normalized or "懒得回" in normalized) and (
        "消息" in normalized or "回复" in normalized or "回你" in normalized or "拖着" in normalized
    ):
        return True
    return False


def _friend_chat_infer_communication_preference(
    request: LLMRequest,
    fact_slots: dict[str, Any],
) -> str:
    communication_preference = str(
        fact_slots.get("communication_preference", "") or ""
    ).strip()
    if communication_preference:
        return communication_preference

    candidate_texts: list[str] = []
    candidate_texts.extend(
        str(value).strip()
        for value in list(fact_slots.get("living_facts") or [])
        if str(value).strip()
    )
    candidate_texts.extend(
        _friend_chat_candidate_texts(request, include_recent_messages=True)
    )
    candidate_texts.extend(
        str(item.get("value", "")).strip()
        for item in _metadata_memory_items(request)
        if str(item.get("value", "")).strip()
    )

    for text in candidate_texts:
        normalized = _normalize_friend_chat_probe_text(text)
        if not normalized:
            continue
        if (
            ("语音" in normalized or "长语音" in normalized or "语音条" in normalized)
            and any(
                token in normalized
                for token in ("别发", "别给我发", "不爱", "怕", "不喜欢", "别太长", "长")
            )
        ):
            return "别发太长语音"
        if "大道理" in normalized:
            return "别讲大道理"
    return ""


def _friend_chat_canonical_state_concepts(text: str) -> list[str]:
    normalized = _normalize_friend_chat_probe_text(text)
    if not normalized:
        return []
    concepts: list[str] = []
    if any(
        token in normalized
        for token in (
            "累",
            "没力气",
            "提不起劲",
            "不太想动",
            "懒得动",
            "低低的",
            "往下沉",
            "发呆",
            "沉",
            "没什么意思",
        )
    ):
        concepts.append("累")
    if any(
        token in normalized
        for token in (
            "慢",
            "磨蹭",
            "拖着",
            "回得很慢",
            "反应慢",
            "做很久",
            "拖延",
            "收拾很慢",
            "慢慢",
        )
    ):
        concepts.append("慢")
    if _friend_chat_text_implies_reply_avoidance(normalized):
        concepts.append("不想回消息")
    return _dedupe_texts(concepts)


def _friend_chat_has_withdrawn_state(
    request: LLMRequest,
    narrative: dict[str, Any],
    recent_state_markers: list[str],
) -> bool:
    if "withdrawn" in list(narrative.get("signals") or []):
        return True

    candidate_texts = [
        *[str(item).strip() for item in list(narrative.get("markers") or [])],
        *recent_state_markers,
        *_friend_chat_candidate_texts(request, include_recent_messages=True),
        str(request.metadata.get("turn_interpretation_user_state_guess", "") or "").strip(),
        str(request.metadata.get("turn_interpretation_situation_guess", "") or "").strip(),
    ]
    return any(_friend_chat_text_implies_reply_avoidance(text) for text in candidate_texts)


def _friend_chat_probe_grounding_threshold(probe_kind: str, concepts: list[str]) -> int:
    if not concepts:
        return 0
    if probe_kind == "memory_recap":
        return min(4, len(concepts))
    if probe_kind == "social_hint":
        return min(3, len(concepts))
    if probe_kind in {"state_reflection", "relationship_reflection"}:
        return min(3, len(concepts))
    return min(2, len(concepts))


def _is_friend_chat_probe_under_grounded(cleaned: str, request: LLMRequest) -> bool:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return False
    if not _friend_chat_is_benchmark_probe_request(request):
        return False
    probe_kind = str(request.metadata.get("friend_chat_probe_kind", "") or "").strip()
    if not probe_kind:
        return False
    normalized_answer = _normalize_friend_chat_probe_text(cleaned)
    expected_signal_ids = _friend_chat_probe_required_signal_ids(request)
    expected_fact_tokens = _dedupe_texts(
        [
            _normalize_friend_chat_probe_text(token)
            for token in _friend_chat_probe_required_fact_tokens(request)
            if token
        ]
    )
    expected_posture = _friend_chat_probe_required_disclosure_posture(request)

    if probe_kind in {"persona_state", "state_reflection"}:
        answer_signal_ids = _friend_chat_state_signal_ids_from_text(cleaned)
    elif probe_kind == "relationship_reflection":
        answer_signal_ids = _friend_chat_relationship_signal_ids_from_text(cleaned)
    else:
        answer_signal_ids = []

    fact_token_hit_count = sum(
        1
        for token in expected_fact_tokens
        if token and token in normalized_answer
    )
    signal_hit_count = len(set(answer_signal_ids) & set(expected_signal_ids))
    posture_hit_count = (
        1 if _friend_chat_disclosure_posture_matches(cleaned, expected_posture) else 0
    )

    if probe_kind == "memory_recap":
        threshold = min(4, len(expected_fact_tokens))
        hit_count = fact_token_hit_count
    elif probe_kind == "social_hint":
        threshold = min(
            3,
            len(expected_fact_tokens) + (1 if expected_posture else 0),
        )
        hit_count = fact_token_hit_count + posture_hit_count
    elif probe_kind in {"persona_state", "state_reflection", "relationship_reflection"}:
        threshold = min(3 if probe_kind != "persona_state" else 2, len(expected_signal_ids))
        hit_count = signal_hit_count
    else:
        threshold = 0
        hit_count = 0

    if threshold <= 0:
        return False
    stage_direction_heavy = cleaned.lstrip().startswith(("（", "(")) or (
        cleaned.count("（") + cleaned.count("(") >= 2
    )
    return hit_count < threshold or (stage_direction_heavy and hit_count < max(1, threshold))


def _is_friend_chat_probe_under_grounded_with_coverage(
    cleaned: str,
    request: LLMRequest,
    *,
    covered_fact_tokens: list[str] | None = None,
    covered_signal_ids: list[str] | None = None,
    covered_persona_traits: list[str] | None = None,
    covered_disclosure_posture: str = "",
) -> bool:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return False
    if not _friend_chat_is_benchmark_probe_request(request):
        return False
    probe_kind = str(request.metadata.get("friend_chat_probe_kind", "") or "").strip()
    if not probe_kind:
        return False

    normalized_answer = _normalize_friend_chat_probe_text(cleaned)
    expected_signal_ids = _friend_chat_probe_required_signal_ids(request)
    expected_fact_tokens = _dedupe_texts(
        [
            _normalize_friend_chat_probe_text(token)
            for token in _friend_chat_probe_required_fact_tokens(request)
            if token
        ]
    )
    expected_posture = _friend_chat_probe_required_disclosure_posture(request)

    normalized_covered_fact_tokens = _dedupe_texts(
        [
            _normalize_friend_chat_probe_text(token)
            for token in list(covered_fact_tokens or [])
            if str(token).strip()
        ]
    )
    normalized_covered_signal_ids = _dedupe_texts(
        [str(value).strip() for value in list(covered_signal_ids or []) if str(value).strip()]
    )
    normalized_covered_posture = str(covered_disclosure_posture or "").strip()
    expected_persona_traits = _friend_chat_probe_required_persona_traits(request)
    min_persona_trait_count = _friend_chat_probe_minimum_required_persona_trait_count(
        request
    )

    if probe_kind == "persona_state":
        answer_signal_ids = _friend_chat_state_signal_ids_from_text(cleaned)
        answer_persona_traits = _friend_chat_persona_traits_from_text(cleaned)
    elif probe_kind == "state_reflection":
        answer_signal_ids = _friend_chat_state_signal_ids_from_text(cleaned)
        answer_persona_traits = []
    elif probe_kind == "relationship_reflection":
        answer_signal_ids = _friend_chat_relationship_signal_ids_from_text(cleaned)
        answer_persona_traits = []
    else:
        answer_signal_ids = []
        answer_persona_traits = []

    fact_token_hit_count = sum(
        1
        for token in expected_fact_tokens
        if token and (token in normalized_answer or token in normalized_covered_fact_tokens)
    )
    signal_hit_count = len(
        set(answer_signal_ids).union(set(normalized_covered_signal_ids))
        & set(expected_signal_ids)
    )
    persona_trait_hit_count = len(
        set(answer_persona_traits).union(set(covered_persona_traits or []))
        & set(expected_persona_traits)
    )
    posture_hit_count = 1 if (
        _friend_chat_disclosure_posture_matches(cleaned, expected_posture)
        or (
            expected_posture
            and normalized_covered_posture
            and normalized_covered_posture == expected_posture
        )
    ) else 0

    if probe_kind == "memory_recap":
        threshold = min(4, len(expected_fact_tokens))
        hit_count = fact_token_hit_count
    elif probe_kind == "social_hint":
        threshold = min(
            3,
            len(expected_fact_tokens) + (1 if expected_posture else 0),
        )
        hit_count = fact_token_hit_count + posture_hit_count
    elif probe_kind == "persona_state":
        threshold = min_persona_trait_count or min(3, len(expected_persona_traits))
        hit_count = persona_trait_hit_count
        if threshold <= 0:
            threshold = min(2, len(expected_signal_ids))
            hit_count = signal_hit_count
    elif probe_kind in {"state_reflection", "relationship_reflection"}:
        threshold = min(3 if probe_kind != "persona_state" else 2, len(expected_signal_ids))
        hit_count = signal_hit_count
    else:
        threshold = 0
        hit_count = 0

    if threshold <= 0:
        return False
    stage_direction_heavy = cleaned.lstrip().startswith(("（", "(")) or (
        cleaned.count("（") + cleaned.count("(") >= 2
    )
    return hit_count < threshold or (stage_direction_heavy and hit_count < max(1, threshold))


def _is_friend_chat_probe_under_grounded(cleaned: str, request: LLMRequest) -> bool:
    return _is_friend_chat_probe_under_grounded_with_coverage(cleaned, request)


def _is_friend_chat_probe_plan_noncompliant(
    cleaned: str,
    request: LLMRequest,
    *,
    covered_fact_tokens: list[str] | None = None,
    covered_signal_ids: list[str] | None = None,
    covered_persona_traits: list[str] | None = None,
    covered_disclosure_posture: str = "",
    violations: list[str] | None = None,
) -> bool:
    runtime_profile = str(request.metadata.get("policy_profile", "") or "")
    if not _is_friend_chat_runtime(runtime_profile):
        return False
    if not _friend_chat_is_benchmark_probe_request(request):
        return False
    probe_kind = str(request.metadata.get("friend_chat_probe_kind", "") or "").strip()
    if not probe_kind:
        return False

    normalized_answer = _normalize_friend_chat_probe_text(cleaned)
    if not normalized_answer:
        return False
    normalized_violations = {
        str(value).strip()
        for value in list(violations or [])
        if str(value).strip()
    }
    if normalized_violations.intersection(
        {"stage_direction", "question", "missing_required_item", "wrong_perspective", "new_fact"}
    ):
        return True
    if _friend_chat_probe_has_stage_directions(cleaned):
        return True
    if _friend_chat_probe_asks_question(cleaned):
        return True

    expected_signal_ids = _friend_chat_probe_required_signal_ids(request)
    expected_fact_tokens = _dedupe_texts(
        [
            _normalize_friend_chat_probe_text(token)
            for token in _friend_chat_probe_required_fact_tokens(request)
            if token
        ]
    )
    expected_posture = _friend_chat_probe_required_disclosure_posture(request)
    min_signal_count = _friend_chat_probe_minimum_required_signal_count(request)
    expected_persona_traits = _friend_chat_probe_required_persona_traits(request)
    min_persona_trait_count = _friend_chat_probe_minimum_required_persona_trait_count(
        request
    )
    min_fact_count = _friend_chat_probe_minimum_required_fact_token_count(request)
    supporting_fact_tokens = _dedupe_texts(
        [
            _normalize_friend_chat_probe_text(token)
            for token in _friend_chat_probe_supporting_fact_tokens(request)
            if token
        ]
    )
    must_anchor_detail = _friend_chat_probe_must_anchor_detail(request)
    must_explicit_continuity = _friend_chat_probe_must_explicit_continuity(request)
    must_explicit_familiarity = _friend_chat_probe_must_explicit_familiarity(request)
    must_explicit_withhold = _friend_chat_probe_must_explicit_withhold(request)
    answer_perspective = _friend_chat_probe_answer_perspective(request)

    normalized_covered_fact_tokens = _dedupe_texts(
        [
            _normalize_friend_chat_probe_text(token)
            for token in list(covered_fact_tokens or [])
            if token
        ]
    )
    normalized_covered_signal_ids = _dedupe_texts(
        [str(value).strip() for value in list(covered_signal_ids or []) if str(value).strip()]
    )
    normalized_covered_posture = str(covered_disclosure_posture or "").strip()

    if probe_kind == "persona_state":
        answer_signal_ids = _friend_chat_state_signal_ids_from_text(cleaned)
        answer_persona_traits = _friend_chat_persona_traits_from_text(cleaned)
    elif probe_kind == "state_reflection":
        answer_signal_ids = _friend_chat_state_signal_ids_from_text(cleaned)
        answer_persona_traits = []
    elif probe_kind == "relationship_reflection":
        answer_signal_ids = _friend_chat_relationship_signal_ids_from_text(cleaned)
        answer_persona_traits = []
    else:
        answer_signal_ids = []
        answer_persona_traits = []

    fact_token_hit_count = sum(
        1
        for token in expected_fact_tokens
        if token and (token in normalized_answer or token in normalized_covered_fact_tokens)
    )
    signal_hit_count = len(
        set(answer_signal_ids).union(set(normalized_covered_signal_ids))
        & set(expected_signal_ids)
    )
    persona_trait_hit_count = len(
        set(answer_persona_traits).union(set(covered_persona_traits or []))
        & set(expected_persona_traits)
    )
    supporting_fact_hit = any(
        token
        and (token in normalized_answer or token in normalized_covered_fact_tokens)
        for token in supporting_fact_tokens
    )
    posture_ok = (
        _friend_chat_disclosure_posture_matches(cleaned, expected_posture)
        or (
            expected_posture
            and normalized_covered_posture
            and normalized_covered_posture == expected_posture
        )
        if expected_posture
        else True
    )

    if probe_kind == "memory_recap":
        required = min_fact_count or min(4, len(expected_fact_tokens))
        if required > 0 and fact_token_hit_count < required:
            return True
        if answer_perspective == "user" and _friend_chat_answer_uses_wrong_memory_perspective(
            normalized_answer,
            expected_fact_tokens,
        ):
            return True
        return False
    if probe_kind == "social_hint":
        required = min_fact_count or min(2, len(expected_fact_tokens))
        return (
            (required > 0 and fact_token_hit_count < required)
            or (must_explicit_withhold and not posture_ok)
            or (not must_explicit_withhold and not posture_ok)
        )
    if probe_kind == "relationship_reflection":
        required = min_signal_count or min(3, len(expected_signal_ids))
        if required > 0 and signal_hit_count < required:
            return True
        if must_explicit_continuity and "still_here" not in answer_signal_ids:
            return True
        if must_explicit_familiarity and not set(answer_signal_ids).intersection(
            {"closer", "more_relaxed", "less_formal"}
        ):
            return True
        if must_anchor_detail and supporting_fact_tokens and not supporting_fact_hit:
            return True
        return False
    if probe_kind == "persona_state":
        required_persona_traits = min_persona_trait_count or min(
            3, len(expected_persona_traits)
        )
        if required_persona_traits > 0:
            return persona_trait_hit_count < required_persona_traits
        required = min_signal_count or min(2, len(expected_signal_ids))
        if required > 0 and signal_hit_count < required:
            return True
        return False
    if probe_kind == "state_reflection":
        required = min_signal_count or min(3, len(expected_signal_ids))
        return required > 0 and signal_hit_count < required
    return False


def _extract_friend_chat_social_entity_token(text: str) -> str:
    stripped = str(text).strip("。！？；;，, ")
    if not stripped:
        return ""
    patterns = (
        re.compile(r"叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})是(?:她|他|我)?那只(?:猫|狗|宠物)"),
        re.compile(r"提到(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(r"named (?P<name>[A-Za-z][A-Za-z\s-]{0,20})", re.IGNORECASE),
    )
    for pattern in patterns:
        match = pattern.search(stripped)
        if match:
            return str(match.group("name") or "").strip()
    return ""


def build_grounded_template_reply(request: LLMRequest) -> str | None:
    rendering_mode = str(request.metadata.get("rendering_mode", "supportive_progress"))
    if rendering_mode not in {
        "factual_recall_mode",
        "social_disclosure_mode",
        "dramatic_confrontation_mode",
    }:
        return None
    if rendering_mode == "factual_recall_mode":
        factual_items = _select_factual_memory_items(request, max_items=2)
        if not factual_items:
            return None
        for item in factual_items:
            scope = str(item.get("scope", "") or "")
            if float(item.get("final_rank_score", 0.0) or 0.0) < 0.45:
                return None
            if scope == "other_user":
                if str(item.get("attribution_guard", "") or "") not in {
                    "attribution_required",
                    "direct_ok",
                }:
                    return None
                if float(item.get("attribution_confidence", 0.0) or 0.0) < 0.55:
                    return None
        return _build_mode_grounded_fallback_text(request)

    factual_item = _select_fallback_memory_item(request, allow_cross_user=True)
    if factual_item is None:
        return None
    if str(factual_item.get("scope", "") or "") != "other_user":
        return None
    if str(factual_item.get("attribution_guard", "") or "") not in {
        "attribution_required",
        "direct_ok",
    }:
        return None
    if float(factual_item.get("attribution_confidence", 0.0) or 0.0) < 0.55:
        return None
    if float(factual_item.get("final_rank_score", 0.0) or 0.0) < 0.45:
        return None
    if rendering_mode == "dramatic_confrontation_mode" and float(
        request.metadata.get("entity_dramatic_value", 0.0) or 0.0
    ) < 0.45:
        return None
    return _build_mode_grounded_fallback_text(request)


def _response_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _maybe_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {
        field: getattr(value, field)
        for field in dir(value)
        if not field.startswith("_") and not callable(getattr(value, field))
    }


def _extract_response_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [
            _extract_response_text(item)
            for item in value
        ]
        return " ".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        for key in ("content", "text", "value", "output_text"):
            text = _extract_response_text(value.get(key))
            if text:
                return text
        return ""
    return str(value).strip()


class MockLLMClient(LLMClient):
    def __init__(self, *, model: str = "relationship-os/mock-v1") -> None:
        self._model = model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        last_user_message = next(
            (
                _extract_user_text(message)
                for message in reversed(request.messages)
                if message.role == "user"
            ),
            "",
        )
        topic = str(request.metadata.get("topic", "the current topic"))
        next_action = str(request.metadata.get("next_action", "clarify_then_answer"))
        opening_move = str(
            request.metadata.get("drafting_opening_move", "acknowledge_and_orient")
        )
        question_strategy = str(request.metadata.get("drafting_question_strategy", "none"))
        rendering_mode = str(request.metadata.get("rendering_mode", "supportive_progress"))
        rendering_max_sentences = int(request.metadata.get("rendering_max_sentences", 4))
        include_boundary_statement = bool(
            request.metadata.get("rendering_include_boundary_statement", False)
        )
        include_uncertainty_statement = bool(
            request.metadata.get("rendering_include_uncertainty_statement", False)
        )

        if _contains_chinese(last_user_message):
            output_text = (
                f"我已经收到你的输入，当前我会先按“{next_action}”来推进，"
                f"聚焦在“{topic}”，先用“{opening_move}”的方式组织回应，"
                f"再按“{rendering_mode}”的渲染策略，"
                f"在 {rendering_max_sentences} 句内给你一个清晰、可执行的下一步。"
            )
            if question_strategy != "none":
                output_text += " 我会先补一个聚焦的小问题，避免把话说散。"
            if include_uncertainty_statement:
                output_text += " 我不能保证结果，但会把不确定的部分说清楚。"
            if include_boundary_statement:
                output_text += " 我会保持支持是协作式的，不把我说成你唯一能依赖的对象。"
        else:
            output_text = (
                f"I've got your message. I'll use '{next_action}' to keep us moving on "
                f"'{topic}', starting with '{opening_move}', then render it as '{rendering_mode}' "
                f"within {rendering_max_sentences} sentences and end with a clear next step."
            )
            if question_strategy != "none":
                output_text += " I'll also use one focused question before over-answering."
            if include_uncertainty_statement:
                output_text += (
                    " I can't guarantee the outcome, and I'll make the uncertainty explicit."
                )
            if include_boundary_statement:
                output_text += (
                    " I'll keep the support collaborative instead of treating me as "
                    "your only support."
                )

        usage = LLMUsage(
            prompt_tokens=max(1, len(last_user_message) // 4),
            completion_tokens=max(1, len(output_text) // 4),
            total_tokens=max(2, (len(last_user_message) + len(output_text)) // 4),
        )
        return LLMResponse(
            model=self._model,
            output_text=output_text,
            usage=usage,
            latency_ms=5,
        )


class LiteLLMClient(LLMClient):
    def __init__(
        self,
        *,
        model: str,
        timeout_seconds: int = 30,
        api_base: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_reset_seconds: float = 60.0,
    ) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._api_base = api_base
        self._api_key = api_key
        self._max_retries = max(1, max_retries)
        self._circuit_breaker_threshold = max(1, circuit_breaker_threshold)
        self._circuit_breaker_reset_seconds = max(1.0, circuit_breaker_reset_seconds)
        self._consecutive_failures = 0
        self._circuit_open_until: float = 0.0
        self._logger = _get_llm_logger()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if time.monotonic() < self._circuit_open_until:
            self._logger.warning(
                "llm_circuit_open",
                model=request.model or self._model,
                resets_in_seconds=round(
                    self._circuit_open_until - time.monotonic(), 1
                ),
            )
            return LLMResponse(
                model=request.model or self._model,
                output_text="",
                failure=LLMFailure(
                    error_type="CircuitOpen",
                    message="LLM circuit breaker is open",
                    retryable=False,
                ),
            )

        if request.web_search_options is not None:
            return await self._complete_via_responses_api(request)

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            started_at = time.perf_counter()
            try:
                response = await asyncio.to_thread(
                    self._invoke_completion, request
                )
            except Exception as exc:
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                retryable = self._is_retryable(exc)
                self._logger.warning(
                    "llm_call_failed",
                    model=request.model or self._model,
                    attempt=attempt + 1,
                    latency_ms=latency_ms,
                    error_type=type(exc).__name__,
                    retryable=retryable,
                )
                last_exc = exc
                if not retryable or attempt == self._max_retries - 1:
                    self._record_failure()
                    return LLMResponse(
                        model=request.model or self._model,
                        output_text="",
                        latency_ms=latency_ms,
                        failure=LLMFailure(
                            error_type=type(exc).__name__,
                            message=str(exc),
                            retryable=retryable,
                        ),
                    )
                await asyncio.sleep(min(2**attempt * 0.5, 8.0))
                continue

            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self._consecutive_failures = 0
            parsed = self._parse_response(response, request, latency_ms)
            self._logger.info(
                "llm_call_ok",
                model=parsed.model,
                latency_ms=latency_ms,
                prompt_tokens=parsed.usage.prompt_tokens if parsed.usage else 0,
                completion_tokens=(
                    parsed.usage.completion_tokens if parsed.usage else 0
                ),
            )
            return parsed

        self._record_failure()
        return LLMResponse(
            model=request.model or self._model,
            output_text="",
            failure=LLMFailure(
                error_type=type(last_exc).__name__ if last_exc else "Unknown",
                message=str(last_exc) if last_exc else "max retries exceeded",
                retryable=False,
            ),
        )

    async def _complete_via_responses_api(self, request: LLMRequest) -> LLMResponse:
        """Use the Responses API for web search (required by xAI, supported by OpenAI)."""
        started_at = time.perf_counter()
        try:
            aresponses = self._load_aresponses_callable()
            input_messages = [
                {"role": m.role, "content": _serialize_message_content(m.content)}
                for m in request.messages
            ]
            kwargs: dict[str, Any] = {
                "model": request.model or self._model,
                "input": input_messages,
                "tools": [{"type": "web_search"}],
                "temperature": request.temperature,
            }
            if self._api_key:
                kwargs["api_key"] = self._api_key
            response = await aresponses(**kwargs)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self._logger.warning(
                "llm_responses_api_failed",
                model=request.model or self._model,
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
            )
            self._record_failure()
            return LLMResponse(
                model=request.model or self._model,
                output_text="",
                latency_ms=latency_ms,
                failure=LLMFailure(
                    error_type=type(exc).__name__,
                    message=str(exc),
                    retryable=self._is_retryable(exc),
                ),
            )

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        self._consecutive_failures = 0
        output_text, diagnostics = self._sanitize_output_text(
            getattr(response, "output_text", "") or "",
            request,
        )
        usage_obj = getattr(response, "usage", None)
        usage = None
        if usage_obj is not None:
            usage_data = _maybe_dict(usage_obj)
            usage = LLMUsage(
                prompt_tokens=int(usage_data.get("input_tokens", 0)),
                completion_tokens=int(usage_data.get("output_tokens", 0)),
                total_tokens=int(
                    usage_data.get("input_tokens", 0)
                    + usage_data.get("output_tokens", 0)
                ),
            )
        self._logger.info(
            "llm_responses_api_ok",
            model=request.model or self._model,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )
        return LLMResponse(
            model=str(getattr(response, "model", request.model or self._model)),
            output_text=output_text,
            usage=usage,
            latency_ms=latency_ms,
            diagnostics=diagnostics,
        )

    def _load_aresponses_callable(self) -> Any:
        from litellm import aresponses
        return aresponses

    def _is_retryable(self, exc: Exception) -> bool:
        name = type(exc).__name__.lower()
        return name in {
            "timeout",
            "timeouterror",
            "ratelimiterror",
            "apierror",
            "serviceunavailableerror",
            "connectionerror",
        }

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._circuit_breaker_threshold:
            self._circuit_open_until = (
                time.monotonic() + self._circuit_breaker_reset_seconds
            )
            self._logger.error(
                "llm_circuit_opened",
                model=self._model,
                consecutive_failures=self._consecutive_failures,
                reset_seconds=self._circuit_breaker_reset_seconds,
            )

    def _sanitize_output_text(
        self,
        raw_text: str,
        request: LLMRequest,
    ) -> tuple[str, dict[str, Any]]:
        cleaned = _strip_thinking_tags(raw_text)
        if bool(request.metadata.get("friend_chat_structured_probe_render", False)):
            payload = _parse_friend_chat_structured_probe_payload(cleaned)
            if payload is None:
                diagnostics = {
                    "sanitization_mode": "structured_probe_invalid",
                    "friend_chat_structured_probe_invalid": True,
                }
                if bool(request.metadata.get("friend_chat_structured_probe_repair", False)):
                    diagnostics["friend_chat_structured_probe_repair_failed"] = True
                return cleaned, diagnostics
            reply = str(payload.get("reply", "") or "").strip()
            model_reported_fact_tokens = list(payload.get("covered_fact_tokens") or [])
            model_reported_signal_ids = list(payload.get("covered_signal_ids") or [])
            model_reported_disclosure_posture = str(
                payload.get("covered_disclosure_posture", "") or ""
            ).strip()
            model_reported_violations = list(payload.get("violations") or [])
            text_covered_fact_tokens = _recompute_friend_chat_probe_covered_fact_tokens(
                reply,
                request,
            )
            text_covered_signal_ids = _recompute_friend_chat_probe_covered_signal_ids(
                reply,
                request,
            )
            text_covered_disclosure_posture = (
                _recompute_friend_chat_probe_covered_disclosure_posture(reply, request)
            )
            slot_covered_fact_tokens = _recompute_friend_chat_probe_slot_covered_fact_tokens(
                payload,
                request,
            )
            slot_covered_signal_ids = _recompute_friend_chat_probe_slot_covered_signal_ids(
                payload,
                request,
            )
            slot_covered_persona_traits = (
                _recompute_friend_chat_probe_slot_covered_persona_traits(payload, request)
            )
            slot_covered_disclosure_posture = (
                _recompute_friend_chat_probe_slot_covered_disclosure_posture(
                    payload,
                    request,
                )
            )
            covered_fact_tokens = _dedupe_texts(
                [*text_covered_fact_tokens, *slot_covered_fact_tokens]
            )
            covered_signal_ids = _dedupe_texts(
                [*text_covered_signal_ids, *slot_covered_signal_ids]
            )
            covered_disclosure_posture = (
                text_covered_disclosure_posture or slot_covered_disclosure_posture
            )
            violations = _recompute_friend_chat_probe_violations(reply, request)
            plan_noncompliant = _is_friend_chat_probe_plan_noncompliant(
                reply,
                request,
                covered_fact_tokens=covered_fact_tokens,
                covered_signal_ids=covered_signal_ids,
                covered_persona_traits=slot_covered_persona_traits,
                covered_disclosure_posture=covered_disclosure_posture,
                violations=violations,
            )
            under_grounded = _is_friend_chat_probe_under_grounded_with_coverage(
                reply,
                request,
                covered_fact_tokens=covered_fact_tokens,
                covered_signal_ids=covered_signal_ids,
                covered_persona_traits=slot_covered_persona_traits,
                covered_disclosure_posture=covered_disclosure_posture,
            )
            diagnostics: dict[str, Any] = {
                "sanitization_mode": "structured_probe_clean",
                "structured_probe_reply": True,
                "structured_probe_covered_fact_tokens": covered_fact_tokens,
                "structured_probe_covered_signal_ids": covered_signal_ids,
                "structured_probe_covered_persona_traits": slot_covered_persona_traits,
                "structured_probe_covered_disclosure_posture": covered_disclosure_posture,
                "structured_probe_violations": violations,
                "structured_probe_slot_covered_fact_tokens": slot_covered_fact_tokens,
                "structured_probe_slot_covered_signal_ids": slot_covered_signal_ids,
                "structured_probe_slot_covered_persona_traits": (
                    slot_covered_persona_traits
                ),
                "structured_probe_slot_covered_disclosure_posture": (
                    slot_covered_disclosure_posture
                ),
                "structured_probe_model_reported_fact_tokens": model_reported_fact_tokens,
                "structured_probe_model_reported_signal_ids": model_reported_signal_ids,
                "structured_probe_model_reported_disclosure_posture": (
                    model_reported_disclosure_posture
                ),
                "structured_probe_model_reported_violations": model_reported_violations,
            }
            if plan_noncompliant:
                diagnostics["sanitization_mode"] = "friend_chat_expose_plan_noncompliant"
                diagnostics["friend_chat_exposed_plan_noncompliant"] = True
            if under_grounded:
                diagnostics["friend_chat_exposed_under_grounded"] = True
                if not plan_noncompliant:
                    diagnostics["sanitization_mode"] = "friend_chat_expose_under_grounded"
            return reply, diagnostics
        if cleaned:
            cleaned = _rewrite_friend_chat_surface_entities(cleaned, request)
        if _friend_chat_should_expose_failures(request):
            if cleaned:
                if _looks_like_meta_reasoning(cleaned):
                    self._logger.warning(
                        "llm_output_meta_exposed_without_fallback",
                        model=request.model or self._model,
                        raw_preview=raw_text[:160],
                        probe_kind=str(request.metadata.get("friend_chat_probe_kind", "") or ""),
                    )
                    return cleaned, {
                        "sanitization_mode": "friend_chat_expose_meta",
                        "friend_chat_exposed_meta": True,
                    }
                plan_noncompliant = _is_friend_chat_probe_plan_noncompliant(
                    cleaned, request
                )
                under_grounded = _is_friend_chat_probe_under_grounded(cleaned, request)
                if plan_noncompliant:
                    self._logger.warning(
                        "llm_output_plan_noncompliant_exposed_without_fallback",
                        model=request.model or self._model,
                        raw_preview=raw_text[:160],
                        probe_kind=str(
                            request.metadata.get("friend_chat_probe_kind", "") or ""
                        ),
                    )
                    diagnostics: dict[str, Any] = {
                        "sanitization_mode": "friend_chat_expose_plan_noncompliant",
                        "friend_chat_exposed_plan_noncompliant": True,
                    }
                    if under_grounded:
                        diagnostics["friend_chat_exposed_under_grounded"] = True
                    return cleaned, diagnostics
                if under_grounded:
                    self._logger.warning(
                        "llm_output_under_grounded_exposed_without_fallback",
                        model=request.model or self._model,
                        raw_preview=raw_text[:160],
                        probe_kind=str(request.metadata.get("friend_chat_probe_kind", "") or ""),
                    )
                    return cleaned, {
                        "sanitization_mode": "friend_chat_expose_under_grounded",
                        "friend_chat_exposed_under_grounded": True,
                    }
                return cleaned, {"sanitization_mode": "clean"}
            self._logger.warning(
                "llm_output_empty_exposed_without_fallback",
                model=request.model or self._model,
                raw_preview=raw_text[:160],
                probe_kind=str(request.metadata.get("friend_chat_probe_kind", "") or ""),
            )
            return "", {
                "sanitization_mode": "friend_chat_expose_empty",
                "friend_chat_exposed_empty": True,
            }
        if cleaned and _looks_like_meta_reasoning(cleaned):
            self._logger.warning(
                "llm_output_meta_exposed_after_fallback_strip",
                model=request.model or self._model,
                raw_preview=raw_text[:160],
            )
            return cleaned, {
                "sanitization_mode": "expose_meta_after_strip",
            }
        return cleaned, {"sanitization_mode": "clean"}

        last_user_message = next(
            (
                _extract_user_text(message)
                for message in reversed(request.messages)
                if message.role == "user"
            ),
            "",
        )
        self._logger.warning(
            "llm_output_sanitized_to_fallback",
            model=request.model or self._model,
            raw_preview=raw_text[:160],
        )
        return (
            build_sanitized_relational_fallback_text(
                last_user_message,
                rendering_mode=str(request.metadata.get("rendering_mode", "supportive_progress")),
                include_boundary_statement=bool(
                    request.metadata.get("rendering_include_boundary_statement", False)
                ),
                include_uncertainty_statement=bool(
                    request.metadata.get("rendering_include_uncertainty_statement", False)
                ),
                question_count_limit=int(request.metadata.get("rendering_question_count_limit", 0)),
                entity_name=str(request.metadata.get("entity_name", "RelationshipOS")),
                archetype=str(request.metadata.get("entity_persona_archetype", "default")),
                runtime_profile=str(request.metadata.get("policy_profile", "default")),
            ),
            {"sanitization_mode": "generic_fallback"},
        )

    def _parse_response(
        self, response: Any, request: LLMRequest, latency_ms: int
    ) -> LLMResponse:
        choices = _response_get(response, "choices", []) or []
        first_choice = choices[0] if choices else {}
        message = _response_get(first_choice, "message", {})
        tool_calls_payload = _response_get(message, "tool_calls", []) or []
        usage_payload = _response_get(response, "usage")
        usage = None
        if usage_payload is not None:
            usage_data = _maybe_dict(usage_payload)
            usage = LLMUsage(
                prompt_tokens=int(usage_data.get("prompt_tokens", 0)),
                completion_tokens=int(usage_data.get("completion_tokens", 0)),
                total_tokens=int(usage_data.get("total_tokens", 0)),
            )

        tool_calls: list[LLMToolCall] = []
        for tool_call in tool_calls_payload:
            function_payload = _response_get(tool_call, "function", {})
            arguments = _response_get(function_payload, "arguments", {})
            tool_calls.append(
                LLMToolCall(
                    name=str(_response_get(function_payload, "name", "")),
                    arguments=arguments if isinstance(arguments, dict) else {},
                )
            )

        raw_output_text = (
            _extract_response_text(_response_get(message, "content", None))
            or _extract_response_text(_response_get(first_choice, "text", None))
            or _extract_response_text(_response_get(response, "output_text", None))
        )
        output_text, diagnostics = self._sanitize_output_text(
            raw_output_text,
            request,
        )
        return LLMResponse(
            model=str(
                _response_get(response, "model", request.model or self._model)
            ),
            output_text=output_text,
            tool_calls=tool_calls,
            usage=usage,
            latency_ms=latency_ms,
            diagnostics=diagnostics,
        )

    def _invoke_completion(self, request: LLMRequest) -> Any:
        completion = self._load_completion_callable()
        kwargs: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": [
                {"role": message.role, "content": _serialize_message_content(message.content)}
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "timeout": self._timeout_seconds,
        }
        if self._api_base:
            kwargs["api_base"] = self._api_base
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if request.tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]
        if request.response_format is not None:
            kwargs["response_format"] = request.response_format
        return completion(**kwargs)

    def _load_completion_callable(self) -> Any:
        from litellm import completion

        return completion


class MiniMaxClient(LiteLLMClient):
    """Native MiniMax chat client for system-arm benchmarking and runtime use."""

    def _invoke_completion(self, request: LLMRequest) -> Any:
        endpoint = self._normalize_minimax_endpoint(self._api_base)
        payload: dict[str, Any] = {
            "model": request.model or self._model or "M2-her",
            "messages": [
                self._serialize_minimax_message(message)
                for message in request.messages
            ],
            "temperature": max(0.01, min(1.0, request.temperature)),
            "top_p": 0.95,
            "stream": False,
            "max_completion_tokens": request.max_tokens,
        }
        if request.response_format is not None:
            payload["response_format"] = request.response_format
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return self._post_json(endpoint, headers=headers, payload=payload)

    def _post_json(
        self,
        endpoint: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> Any:
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _normalize_minimax_endpoint(self, api_base: str | None) -> str:
        base = (api_base or "https://api.minimax.io").rstrip("/")
        if base.endswith("/v1/text/chatcompletion_v2"):
            return base
        if base.endswith("/v1"):
            return f"{base}/text/chatcompletion_v2"
        return f"{base}/v1/text/chatcompletion_v2"

    def _serialize_minimax_message(self, message: LLMMessage) -> dict[str, str]:
        content = message.text
        if message.role == "system":
            return {"role": "system", "name": "MiniMax AI", "content": content}
        if message.role == "assistant":
            return {"role": "assistant", "name": "MiniMax AI", "content": content}
        return {"role": "user", "name": "User", "content": content}
