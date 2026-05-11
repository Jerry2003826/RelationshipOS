from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.friend_chat_fact_extractors import (
    extract_drink_preference_from_text,
    extract_hometown_from_text,
    extract_pet_name_from_text,
    normalize_communication_preference,
    normalize_fact_slot_digest,
)


def infer_friend_chat_communication_preference(
    *,
    metadata: dict[str, Any],
    self_memory_values: list[str],
) -> str:
    digest = normalize_fact_slot_digest(metadata.get("friend_chat_fact_slot_digest"))
    existing = normalize_communication_preference(str(digest.get("communication_preference", "")))
    if existing:
        return existing

    candidate_texts: list[str] = []
    candidate_texts.extend(
        str(value).strip()
        for value in list(digest.get("living_facts") or [])
        if str(value).strip()
    )
    candidate_texts.extend(self_memory_values)
    candidate_texts.extend(
        str(value).strip()
        for value in list(metadata.get("friend_chat_recent_user_messages") or [])
        if str(value).strip()
    )
    for item in list(metadata.get("fallback_memory_items") or []):
        if isinstance(item, dict):
            value = str(item.get("value", "") or "").strip()
            if value:
                candidate_texts.append(value)

    for text in candidate_texts:
        normalized = normalize_communication_preference(text)
        if normalized:
            return normalized
    return ""


def build_enriched_friend_chat_fact_slot_digest(
    *,
    metadata: dict[str, Any],
    self_memory_values: list[str],
) -> dict[str, Any]:
    digest = normalize_fact_slot_digest(metadata.get("friend_chat_fact_slot_digest"))
    values = list(self_memory_values)
    values.extend(
        str(value).strip()
        for value in list(metadata.get("friend_chat_recent_user_messages") or [])
        if str(value).strip()
    )
    values.extend(
        str(item.get("value", "")).strip()
        for item in list(metadata.get("fallback_memory_items") or [])
        if isinstance(item, dict) and str(item.get("value", "")).strip()
    )
    hometown = str(digest.get("hometown", "") or "").strip()
    pet_name = str(digest.get("pet_name", "") or "").strip()
    pet_kind = str(digest.get("pet_kind", "") or "").strip()
    drink_preference = str(digest.get("drink_preference", "") or "").strip()

    if not hometown:
        for value in values:
            hometown = extract_hometown_from_text(value)
            if hometown:
                break
    if not pet_name:
        for value in values:
            pet_name = extract_pet_name_from_text(value)
            if pet_name:
                break
    if not drink_preference:
        for value in values:
            drink_preference = extract_drink_preference_from_text(value)
            if drink_preference:
                break
    if not pet_kind and any(
        token in value
        for value in values
        for token in ("\u732b", "\u5c0f\u732b", "\u732b\u54aa")
    ):
        pet_kind = "\u732b"

    return {
        **digest,
        "hometown": hometown,
        "pet_name": pet_name,
        "pet_kind": pet_kind,
        "drink_preference": drink_preference,
        "communication_preference": infer_friend_chat_communication_preference(
            metadata={
                **metadata,
                "friend_chat_fact_slot_digest": {
                    **digest,
                    "hometown": hometown,
                    "pet_name": pet_name,
                    "pet_kind": pet_kind,
                    "drink_preference": drink_preference,
                },
            },
            self_memory_values=self_memory_values,
        ),
    }
