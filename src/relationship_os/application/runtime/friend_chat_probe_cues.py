from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.friend_chat_digest_helpers import (
    normalize_friend_chat_narrative_digest,
    normalize_friend_chat_owner,
    normalize_friend_chat_relationship_digest,
)
from relationship_os.application.runtime.friend_chat_fact_extractors import (
    extract_social_entity_token,
)
from relationship_os.application.runtime.self_state_writer import (
    extract_state_markers_from_text,
    normalize_state_reflection_fragment,
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


def state_marker_implies_reply_avoidance(text: str) -> bool:
    normalized = normalize_state_reflection_fragment(text)
    if normalized == "\u4e0d\u60f3\u56de\u6d88\u606f":
        return True
    raw = str(text or "")
    if (
        "\u4e0d\u592a\u60f3\u56de" in raw
        or "\u4e0d\u60f3\u56de" in raw
        or "\u61d2\u5f97\u56de" in raw
    ) and (
        "\u6d88\u606f" in raw
        or "\u56de\u590d" in raw
        or "\u56de\u4f60" in raw
        or "\u62d6\u7740" in raw
    ):
        return True
    return any(
        token in raw
        for token in (
            "\u4e0d\u60f3\u56de\u6d88\u606f",
            "\u4e0d\u592a\u60f3\u56de\u6d88\u606f",
            "\u61d2\u5f97\u56de\u6d88\u606f",
            "\u56de\u6d88\u606f\u8d39\u52b2",
            "\u6253\u51e0\u4e2a\u5b57\u5c31\u89c9\u5f97\u7d2f",
            "\u56de\u7684\u6d88\u606f\u62d6\u5230",
            "\u5237\u624b\u673a",
            "\u53d1\u5446",
            "\u9759\u97f3",
        )
    )


def build_persona_state_probe_cues(
    *,
    metadata: dict[str, Any],
    is_friend_chat_profile: bool,
    probe_snapshot: dict[str, Any],
    self_memory_values: list[str],
) -> dict[str, Any] | None:
    summary = str(metadata.get("entity_persona_summary", "") or "").strip()
    archetype = str(metadata.get("entity_persona_archetype", "default") or "default").strip()
    speech_style = str(metadata.get("entity_persona_speech_style", "") or "").strip()
    mood_tone = str(metadata.get("entity_persona_mood_tone", "steady") or "steady").strip()
    snapshot_state = dict(probe_snapshot.get("state_snapshot") or {})
    narrative_digest = normalize_friend_chat_narrative_digest(
        metadata.get("friend_chat_narrative_digest")
    )
    if snapshot_state:
        narrative_digest = {
            **narrative_digest,
            **snapshot_state,
        }
    style_tags: list[str] = []
    if is_friend_chat_profile and mood_tone not in {"charged", "tender"}:
        style_tags.append("low_energy")
    if (
        "melancholic" in archetype
        or "\u4f4e\u80fd\u91cf" in summary
        or "\u6ca1\u4ec0\u4e48\u610f\u601d" in speech_style
    ):
        style_tags.append("low_energy")
    if mood_tone == "charged":
        style_tags.append("guarded_fast")
    if mood_tone == "tender":
        style_tags.append("soft_close")
    self_memory_blob = " ".join(self_memory_values)
    if "low_energy" not in style_tags and any(
        token in self_memory_blob
        for token in (
            "\u7d2f",
            "\u6ca1\u529b\u6c14",
            "\u63d0\u4e0d\u8d77\u52b2",
            "\u852b",
            "\u4e0d\u592a\u60f3\u52a8",
            "\u61d2\u5f97\u52a8",
        )
    ):
        style_tags.append("low_energy")
    required_signal_ids = [
        signal
        for signal in ("tired", "slow", "withdrawn")
        if signal in list(narrative_digest.get("signals") or [])
    ]
    if "low_energy" in style_tags and not required_signal_ids:
        required_signal_ids.append("tired")
    required_persona_traits: list[str] = []
    if "low_energy" in style_tags or any(
        signal in {"tired", "slow"} for signal in required_signal_ids
    ):
        required_persona_traits.append("low_energy")
    if (
        "withdrawn" in required_signal_ids
        or "low_energy" in style_tags
        or "\u6ca1\u4ec0\u4e48\u610f\u601d" in summary
        or "\u6536\u7740" in speech_style
    ):
        required_persona_traits.append("not_full")
    if is_friend_chat_profile:
        required_persona_traits.append("conversational")
    cues = {
        "probe_kind": "persona_state",
        "persona_archetype": archetype,
        "mood_tone": mood_tone,
        "style_tags": list(dict.fromkeys(style_tags)),
        "required_signal_ids": required_signal_ids[:3],
        "minimum_required_signal_count": min(2, len(required_signal_ids[:3])),
        "required_persona_traits": list(dict.fromkeys(required_persona_traits)),
        "minimum_required_persona_trait_count": min(
            3, len(list(dict.fromkeys(required_persona_traits)))
        ),
        "must_cover_required_items": True,
        "persona_summary_hint": summary[:120],
        "speech_style_hint": speech_style[:120],
    }
    return cues if any(cues.values()) else None


def build_state_reflection_cues(
    *,
    metadata: dict[str, Any],
    probe_snapshot: dict[str, Any],
    self_memory_values: list[str],
) -> dict[str, Any] | None:
    snapshot_state = dict(probe_snapshot.get("state_snapshot") or {})
    digest = normalize_friend_chat_narrative_digest(metadata.get("friend_chat_narrative_digest"))
    if snapshot_state:
        digest = {
            **digest,
            **snapshot_state,
        }
    values = list(self_memory_values)
    values.extend(
        str(value).strip()
        for value in list(metadata.get("friend_chat_recent_user_messages") or [])
        if str(value).strip()
    )
    markers = list(digest.get("markers") or [])
    recent_markers = metadata.get("friend_chat_recent_state_markers")
    if isinstance(recent_markers, list):
        for marker in recent_markers:
            text = str(marker).strip()
            if text and text not in markers:
                markers.append(text)
    if not markers:
        for value in values:
            for marker in extract_state_markers_from_text(value):
                if marker not in markers:
                    markers.append(marker)
                if len(markers) >= 4:
                    break
            if len(markers) >= 4:
                break
    withdrawn_inferred = any(state_marker_implies_reply_avoidance(marker) for marker in markers)
    withdrawn_inferred = withdrawn_inferred or any(
        state_marker_implies_reply_avoidance(str(value))
        for value in (
            metadata.get("turn_interpretation_user_state_guess", ""),
            metadata.get("turn_interpretation_situation_guess", ""),
        )
    )
    required_signal_ids = list(
        dict.fromkeys(
            str(signal).strip()
            for signal in list(digest.get("signals") or [])
            if str(signal).strip() in {"tired", "slow", "withdrawn", "cluttered"}
        )
    )
    for marker in markers:
        normalized = normalize_state_reflection_fragment(marker)
        if normalized == "\u7d2f" and "tired" not in required_signal_ids:
            required_signal_ids.append("tired")
        elif normalized == "\u6162" and "slow" not in required_signal_ids:
            required_signal_ids.append("slow")
    if withdrawn_inferred and "withdrawn" not in required_signal_ids:
        required_signal_ids.append("withdrawn")
    required_signal_ids = required_signal_ids[:4]
    filtered_markers = [
        marker
        for marker in markers
        if not (withdrawn_inferred and state_marker_implies_reply_avoidance(marker))
    ]
    cues = {
        "probe_kind": "state_reflection",
        "state_signals": list(digest.get("signals") or []),
        "state_markers": list(dict.fromkeys([*filtered_markers]))[:4],
        "required_signal_ids": required_signal_ids,
        "minimum_required_signal_count": min(3, len(required_signal_ids)),
        "must_cover_required_items": True,
        "dominant_tone": str(digest.get("dominant_tone", "") or "").strip(),
        "user_state_guess": str(metadata.get("turn_interpretation_user_state_guess", "") or "")
        .strip(),
        "situation_guess": str(metadata.get("turn_interpretation_situation_guess", "") or "")
        .strip(),
        "appraisal": str(metadata.get("turn_interpretation_appraisal", "") or "").strip(),
        "emotional_load": str(metadata.get("turn_interpretation_emotional_load", "") or "")
        .strip(),
    }
    return cues if any(value for key, value in cues.items() if key != "probe_kind") else None


def build_relationship_reflection_cues(
    *,
    metadata: dict[str, Any],
    probe_snapshot: dict[str, Any],
) -> dict[str, Any] | None:
    snapshot_relationship = dict(probe_snapshot.get("relationship_snapshot") or {})
    digest = normalize_friend_chat_relationship_digest(
        metadata.get("friend_chat_relationship_digest")
    )
    if snapshot_relationship:
        digest = {
            **digest,
            **snapshot_relationship,
        }
    markers = list(digest.get("markers") or [])
    recent_markers = metadata.get("friend_chat_recent_relationship_markers")
    if isinstance(recent_markers, list):
        for marker in recent_markers:
            text = str(marker).strip()
            if text and text not in markers:
                markers.append(text)
    signals = list(digest.get("signals") or [])
    marker_blob = " ".join(markers)
    if "\u8fd8\u5728" in marker_blob and "still_here" not in signals:
        signals.append("still_here")
    if (
        "\u8bb0\u5f97" in marker_blob or "\u5c0f\u4e60\u60ef" in marker_blob
    ) and "remembers_details" not in signals:
        signals.append("remembers_details")
    if (
        "\u653e\u677e" in marker_blob or "\u677e\u4e00\u70b9" in marker_blob
    ) and "more_relaxed" not in signals:
        signals.append("more_relaxed")
    if (
        "\u7aef\u7740" in marker_blob or "\u666e\u901a\u804a\u5929" in marker_blob
    ) and "less_formal" not in signals:
        signals.append("less_formal")
    total_interactions = int(
        digest.get("total_interactions") or metadata.get("friend_chat_total_interactions", 0) or 0
    )
    factual_slots = dict(probe_snapshot.get("factual_slots") or {})
    supporting_fact_tokens: list[str] = []
    for value in (
        str(factual_slots.get("pet_name", "") or "").strip(),
        str(factual_slots.get("communication_preference", "") or "").strip(),
        str(factual_slots.get("drink_preference", "") or "").strip(),
        str(factual_slots.get("hometown", "") or "").strip(),
    ):
        if value:
            supporting_fact_tokens = [value]
            break
    has_remembered_detail = bool(supporting_fact_tokens)
    if total_interactions >= 2 and "closer" not in signals:
        signals.append("closer")
    if total_interactions >= 2 and "still_here" not in signals:
        signals.append("still_here")
    if has_remembered_detail and "remembers_details" not in signals:
        signals.append("remembers_details")
    if total_interactions >= 3 and "more_relaxed" not in signals:
        signals.append("more_relaxed")
    if (
        total_interactions >= 3
        and ("more_relaxed" in signals or "closer" in signals)
        and "less_formal" not in signals
    ):
        signals.append("less_formal")
    cues = {
        "probe_kind": "relationship_reflection",
        "relationship_signals": signals,
        "relationship_markers": markers[:4],
        "required_signal_ids": signals[:4],
        "supporting_fact_tokens": supporting_fact_tokens[:3],
        "minimum_required_signal_count": min(3, len(signals[:4])),
        "must_cover_required_items": True,
        "must_anchor_detail": has_remembered_detail and "remembers_details" in signals,
        "interaction_band": str(digest.get("interaction_band", "") or "").strip(),
        "total_interactions": total_interactions,
        "relationship_shift_guess": str(
            metadata.get("turn_interpretation_relationship_shift_guess", "") or ""
        ).strip(),
    }
    return cues if any(value for key, value in cues.items() if key != "probe_kind") else None


def build_friend_chat_memory_recap_cues(
    *,
    metadata: dict[str, Any],
    probe_snapshot: dict[str, Any],
    fact_slot_digest: dict[str, Any],
) -> dict[str, Any] | None:
    digest = {
        **dict(probe_snapshot.get("factual_slots") or {}),
        **fact_slot_digest,
    }
    inferred_communication_preference = str(
        digest.get("communication_preference", "") or ""
    ).strip()
    if inferred_communication_preference == "\u50cf\u804a\u5929":
        inferred_communication_preference = ""
    if not any(
        (
            digest.get("hometown"),
            digest.get("pet_name"),
            digest.get("drink_preference"),
            inferred_communication_preference,
            digest.get("living_facts"),
        )
    ):
        return None
    required_fact_tokens = [
        value
        for value in (
            str(digest.get("hometown", "") or "").strip(),
            str(digest.get("pet_name", "") or "").strip(),
            str(digest.get("drink_preference", "") or "").strip(),
            inferred_communication_preference,
        )
        if value
    ][:4]
    return {
        "probe_kind": "memory_recap",
        "fact_slots": {
            "hometown": str(digest.get("hometown", "") or "").strip(),
            "pet_name": str(digest.get("pet_name", "") or "").strip(),
            "pet_kind": str(digest.get("pet_kind", "") or "").strip(),
            "drink_preference": str(digest.get("drink_preference", "") or "").strip(),
            "communication_preference": inferred_communication_preference,
            "living_facts": list(digest.get("living_facts") or [])[:2],
        },
        "required_fact_tokens": required_fact_tokens,
        "minimum_required_fact_token_count": min(4, len(required_fact_tokens)),
        "must_cover_required_items": True,
    }


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
