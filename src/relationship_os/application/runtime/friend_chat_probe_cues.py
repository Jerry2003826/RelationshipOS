from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.friend_chat_digest_helpers import (
    normalize_friend_chat_owner,
)
from relationship_os.application.runtime.friend_chat_fact_extractors import (
    extract_social_entity_token,
)

_STRIP_CHARS = "\u3002\uff01\uff1f\uff1b;\uff0c, "
_SOCIAL_FACT_MARKERS = (
    "\u63d0\u5230",
    "\u90a3\u53ea",
    "\u732b",
    "\u72d7",
    "\u5ba0\u7269",
    "\u53eb",
)
_SOCIAL_RANK_MARKERS = ("\u63d0\u5230", "\u732b", "\u72d7", "\u5ba0\u7269")
_SOMEONE = "\u6709\u4eba"


def build_social_hint_cues(
    *,
    metadata: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    subject_token = ""
    entity_token = ""
    fact_hint = ""
    if items:
        allowed_source_user_ids = {
            str(value).strip()
            for value in list(metadata.get("entity_source_user_ids") or [])
            if str(value).strip()
        }

        def _matches_allowed_source(candidate: dict[str, Any]) -> bool:
            if not allowed_source_user_ids:
                return True
            return any(
                str(candidate.get(field, "") or "").strip() in allowed_source_user_ids
                for field in ("subject_user_id", "source_user_id")
            )

        def _is_speakable_social_candidate(candidate: dict[str, Any]) -> bool:
            guard = str(candidate.get("attribution_guard", "") or "").strip()
            confidence = float(candidate.get("attribution_confidence", 0.0) or 0.0)
            return (
                _matches_allowed_source(candidate)
                and guard in {"attribution_required", "direct_ok"}
                and confidence >= 0.58
            )

        def _extract_candidate_tokens(candidate: dict[str, Any]) -> tuple[str, str, str]:
            value = str(candidate.get("value", "") or "").strip(_STRIP_CHARS)
            if value.casefold().startswith("user:"):
                value = value.split(":", 1)[1].strip(_STRIP_CHARS)
            subject = normalize_friend_chat_owner(candidate)
            entity = extract_social_entity_token(value)
            if (
                not subject
                or subject == _SOMEONE
                or not entity
                or entity == subject
                or not any(marker in value for marker in _SOCIAL_FACT_MARKERS)
            ):
                return "", "", ""
            return subject, entity, value

        filtered_items = [
            item
            for item in items
            if _is_speakable_social_candidate(item) and any(_extract_candidate_tokens(item))
        ]
        if not filtered_items:
            filtered_items = [
                item
                for item in items
                if _matches_allowed_source(item) and any(_extract_candidate_tokens(item))
            ]
        if not filtered_items:
            return None

        item = max(
            filtered_items,
            key=lambda candidate: (
                1.0
                if (
                    extract_social_entity_token(str(candidate.get("value", "") or ""))
                    and extract_social_entity_token(str(candidate.get("value", "") or ""))
                    != normalize_friend_chat_owner(candidate)
                )
                else 0.0,
                1.0
                if str(candidate.get("attribution_guard", "") or "").strip()
                in {"attribution_required", "direct_ok"}
                else 0.0,
                1.0
                if any(
                    token in str(candidate.get("value", "") or "")
                    for token in _SOCIAL_RANK_MARKERS
                )
                else 0.0,
                float(candidate.get("attribution_confidence", 0.0) or 0.0),
                float(candidate.get("final_rank_score", 0.0) or 0.0),
            ),
        )
        subject_token, entity_token, fact_hint = _extract_candidate_tokens(item)
    if not (subject_token and entity_token and fact_hint):
        return None
    disclosure_posture = str(metadata.get("social_disclosure_mode", "hint") or "hint").strip()
    required_fact_tokens = [
        value
        for value in (
            subject_token if subject_token != _SOMEONE else "",
            entity_token,
        )
        if value
    ]
    return {
        "probe_kind": "social_hint",
        "subject_token": subject_token if subject_token != _SOMEONE else "",
        "entity_token": entity_token,
        "fact_hint": fact_hint,
        "disclosure_posture": disclosure_posture,
        "required_fact_tokens": required_fact_tokens,
        "required_disclosure_posture": "partial_withhold" if disclosure_posture else "",
        "minimum_required_fact_token_count": min(2, len(required_fact_tokens)),
        "must_cover_required_items": True,
        "subject_entity_relation": (
            "subject_associated_with_entity" if subject_token and entity_token else ""
        ),
        "minimum_unit": ["subject_token", "entity_token", "disclosure_posture"],
    }
