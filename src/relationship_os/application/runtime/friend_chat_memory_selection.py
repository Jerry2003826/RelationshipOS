from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.edge_memory_text import (
    is_low_signal_fallback_memory_value,
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
