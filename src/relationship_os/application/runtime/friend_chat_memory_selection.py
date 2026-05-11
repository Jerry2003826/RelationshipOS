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
