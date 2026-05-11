from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.edge_memory_text import (
    is_low_signal_fallback_memory_value,
    text_keywords,
)
from relationship_os.application.runtime.friend_chat_digest_helpers import (
    normalize_friend_chat_owner,
)


def _ranked_candidates(
    *,
    recalled_memory: list[dict[str, Any]],
    scopes: set[str],
) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in recalled_memory
        if str(item.get("scope", "")) in scopes
        and not is_low_signal_fallback_memory_value(str(item.get("value", "")))
    ]
    candidates.sort(
        key=lambda item: (
            float(item.get("attribution_confidence", 0.0) or 0.0),
            float(item.get("final_rank_score", 0.0) or 0.0),
        ),
        reverse=True,
    )
    return candidates


def build_friend_chat_memory_values(
    *,
    recalled_memory: list[dict[str, Any]],
    scopes: set[str],
    max_items: int = 6,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in _ranked_candidates(recalled_memory=recalled_memory, scopes=scopes):
        value = str(item.get("value", "") or "").strip()
        if value.casefold().startswith("user:"):
            value = value.split(":", 1)[1].strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
        if len(values) >= max_items:
            break
    return values


def build_friend_chat_memory_items(
    *,
    recalled_memory: list[dict[str, Any]],
    scopes: set[str],
    max_items: int = 4,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in _ranked_candidates(recalled_memory=recalled_memory, scopes=scopes):
        key = (
            str(item.get("scope", "")),
            str(item.get("subject_user_id", "") or item.get("source_user_id", "") or ""),
            str(item.get("value", "") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "value": str(item.get("value", "") or "").strip(),
                "scope": str(item.get("scope", "") or ""),
                "source_user_id": str(item.get("source_user_id", "") or ""),
                "subject_user_id": str(item.get("subject_user_id", "") or ""),
                "subject_hint": str(item.get("subject_hint", "") or ""),
                "subject_display_name": normalize_friend_chat_owner(item),
                "attribution_guard": str(item.get("attribution_guard", "") or ""),
                "attribution_confidence": float(item.get("attribution_confidence", 0.0) or 0.0),
                "final_rank_score": float(item.get("final_rank_score", 0.0) or 0.0),
            }
        )
        if len(items) >= max_items:
            break
    return items


def build_self_memory_values_from_metadata(metadata: dict[str, Any]) -> list[str]:
    precomputed = metadata.get("friend_chat_self_memory_values")
    if isinstance(precomputed, list):
        values = [str(value).strip() for value in precomputed if str(value).strip()]
        if values:
            return values
    values: list[str] = []
    for item in list(metadata.get("fallback_memory_items") or []):
        if not isinstance(item, dict):
            continue
        scope = str(item.get("scope", "") or "")
        if scope not in {"self_user", "session", "user"}:
            continue
        value = str(item.get("value", "") or "").strip()
        if value.casefold().startswith("user:"):
            value = value.split(":", 1)[1].strip()
        if value:
            values.append(value)
    if values:
        return values
    recent_messages = metadata.get("friend_chat_recent_user_messages")
    if isinstance(recent_messages, list):
        values = [str(value).strip() for value in recent_messages if str(value).strip()]
        if values:
            return values
    recent_markers = metadata.get("friend_chat_recent_state_markers")
    if isinstance(recent_markers, list):
        return [str(value).strip() for value in recent_markers if str(value).strip()]
    return values


def build_other_memory_values_from_metadata(metadata: dict[str, Any]) -> list[str]:
    precomputed = metadata.get("friend_chat_other_memory_values")
    if isinstance(precomputed, list):
        values = [str(value).strip() for value in precomputed if str(value).strip()]
        if values:
            return values
    values: list[str] = []
    for item in list(metadata.get("fallback_memory_items") or []):
        if not isinstance(item, dict):
            continue
        if str(item.get("scope", "") or "") != "other_user":
            continue
        value = str(item.get("value", "") or "").strip()
        if value:
            values.append(value)
    if values:
        return values
    detailed = metadata.get("friend_chat_other_memory_items")
    if isinstance(detailed, list):
        return [
            str(item.get("value", "")).strip()
            for item in detailed
            if isinstance(item, dict) and str(item.get("value", "")).strip()
        ]
    return values


def build_friend_chat_other_memory_items_from_metadata(
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    items = metadata.get("friend_chat_other_memory_items")
    if not isinstance(items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value", "") or "").strip()
        if not value:
            continue
        normalized.append(item)
    return normalized


def build_speakable_memory_items(
    *,
    user_message: str,
    recalled_memory: list[dict[str, Any]],
    routing_mode: str,
    edge_runtime_plan: dict[str, Any],
    conscience_assessment: dict[str, Any],
    self_referential_memory_query: bool,
) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in recalled_memory
        if not is_low_signal_fallback_memory_value(str(item.get("value", "")))
    ]
    factual_self_query = bool(
        edge_runtime_plan.get(
            "interpreted_self_referential_memory_query",
            self_referential_memory_query,
        )
    )
    conscience_mode = str(conscience_assessment.get("mode", "withhold") or "withhold")
    allowed_source_user_ids = {
        str(value)
        for value in (conscience_assessment.get("source_user_ids") or [])
        if str(value).strip()
    }
    allowed_fact_count = max(
        0,
        int(conscience_assessment.get("allowed_fact_count", 0) or 0),
    )

    def _is_cross_user_speakable(item: dict[str, Any]) -> bool:
        if str(item.get("scope", "")) != "other_user":
            return False
        source_user_id = str(item.get("source_user_id", "") or "")
        subject_user_id = str(item.get("subject_user_id", "") or "")
        if allowed_source_user_ids and (
            source_user_id not in allowed_source_user_ids
            and subject_user_id not in allowed_source_user_ids
        ):
            return False
        guard = str(item.get("attribution_guard", "hint_only") or "hint_only")
        if guard == "hint_only":
            return False
        return float(item.get("attribution_confidence", 0.0) or 0.0) >= 0.58

    visible: list[dict[str, Any]]
    if routing_mode == "factual_recall":
        if factual_self_query:
            self_candidates = [
                item
                for item in candidates
                if str(item.get("scope", "")) in {"self_user", "session", "user"}
            ]
            visible = self_candidates or [
                item for item in candidates if str(item.get("scope", "")) == "global_entity"
            ]
        elif (
            conscience_mode
            in {
                "partial_reveal",
                "direct_reveal",
                "dramatic_confrontation",
            }
            and allowed_fact_count > 0
        ):
            cross_user_candidates = [item for item in candidates if _is_cross_user_speakable(item)]
            visible = cross_user_candidates[:allowed_fact_count]
        else:
            visible = [
                item for item in candidates if str(item.get("scope", "")) == "global_entity"
            ]
    elif routing_mode == "social_disclosure":
        cross_user_candidates = [item for item in candidates if _is_cross_user_speakable(item)]
        disclosure_cap = allowed_fact_count
        if disclosure_cap <= 0 and conscience_mode == "hint":
            disclosure_cap = 1
        visible = cross_user_candidates[: max(disclosure_cap, 0)]
    else:
        visible = [
            item
            for item in candidates
            if str(item.get("scope", "")) in {"self_user", "session", "user", "global_entity"}
        ]

    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for item in visible:
        key = (
            str(item.get("scope", "")),
            str(item.get("subject_user_id", "") or item.get("source_user_id", "") or ""),
            str(item.get("value", "")),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        normalized_item = dict(item)
        normalized_item["subject_display_name"] = normalize_friend_chat_owner(item)
        deduped.append(normalized_item)
    return deduped


def build_fallback_memory_items(
    *,
    user_message: str,
    candidates: list[dict[str, Any]],
    routing_mode: str,
) -> list[dict[str, Any]]:
    query_keywords = text_keywords(user_message)
    if routing_mode == "factual_recall":
        lowered_message = user_message.casefold()
        asks_pet_name = (
            ("dog" in lowered_message and "name" in lowered_message)
            or ("猫" in user_message and ("叫什么" in user_message or "名字" in user_message))
            or ("狗" in user_message and ("叫什么" in user_message or "名字" in user_message))
        )
        asks_origin = (
            "grew up" in lowered_message
            or "where i grew up" in lowered_message
            or "哪里长大" in user_message
            or "在哪长大" in user_message
            or ("长大" in user_message and "哪里" in user_message)
        )
        candidates.sort(
            key=lambda item: (
                len(text_keywords(str(item.get("value", ""))) & query_keywords),
                1.5
                if asks_pet_name
                and any(
                    token in str(item.get("value", "")).casefold()
                    for token in (
                        "dog",
                        "retriever",
                        "corgi",
                        "cat",
                        "named ",
                        "name is ",
                        "猫",
                        "狗",
                        "宠物",
                        "叫",
                    )
                )
                else 0.0,
                1.5
                if asks_origin
                and any(
                    token in str(item.get("value", "")).casefold()
                    for token in ("grew up", "from ", "长大", "住在")
                )
                else 0.0,
                1 if str(item.get("scope")) == "self_user" else 0,
                float(item.get("attribution_confidence", 0.0) or 0.0),
                float(item.get("final_rank_score", 0.0) or 0.0),
            ),
            reverse=True,
        )
    elif routing_mode == "social_disclosure":
        candidates.sort(
            key=lambda item: (
                1 if str(item.get("scope")) == "other_user" else 0,
                1 if str(item.get("attribution_guard", "hint_only")) != "hint_only" else 0,
                float(item.get("attribution_confidence", 0.0) or 0.0),
                float(item.get("final_rank_score", 0.0) or 0.0),
            ),
            reverse=True,
        )

    items: list[dict[str, Any]] = []
    for item in candidates[:8]:
        value = str(item.get("value", ""))
        if value.casefold().startswith("user:"):
            value = value.split(":", 1)[1].strip()
        items.append(
            {
                "value": value,
                "scope": str(item.get("scope", "")),
                "source_user_id": str(item.get("source_user_id", "") or ""),
                "subject_user_id": str(item.get("subject_user_id", "") or ""),
                "subject_hint": str(item.get("subject_hint", "") or ""),
                "attribution_guard": str(item.get("attribution_guard", "") or ""),
                "attribution_confidence": float(item.get("attribution_confidence", 0.0) or 0.0),
                "memory_kind": str(item.get("memory_kind", "") or ""),
                "final_rank_score": float(item.get("final_rank_score", 0.0) or 0.0),
            }
        )
    return items
