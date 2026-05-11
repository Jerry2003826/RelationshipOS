from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.friend_chat_probe_repair import (
    friend_chat_probe_persona_trait_semantics,
    friend_chat_probe_posture_semantics,
    friend_chat_probe_signal_semantics,
)


def _clean_unique(values: Any) -> list[str]:
    return list(dict.fromkeys(value for value in list(values or []) if value))


def _fact_tokens_from_slots(factual_slots: dict[str, Any]) -> list[str]:
    return [
        value
        for value in (
            str(factual_slots.get("hometown", "") or "").strip(),
            str(factual_slots.get("pet_name", "") or "").strip(),
            str(factual_slots.get("drink_preference", "") or "").strip(),
            str(factual_slots.get("communication_preference", "") or "").strip(),
        )
        if value
    ]


def _infer_probe_kind(metadata: dict[str, Any]) -> str:
    if bool(metadata.get("turn_interpretation_persona_state_probe")):
        return "persona_state"
    if bool(metadata.get("turn_interpretation_relationship_reflection_probe")):
        return "relationship_reflection"
    if bool(metadata.get("turn_interpretation_state_reflection_probe")):
        return "state_reflection"
    if bool(metadata.get("turn_interpretation_self_referential_memory_query")):
        return "memory_recap"
    if bool(metadata.get("turn_interpretation_social_probe")):
        return "social_hint"
    return ""


def build_friend_chat_probe_snapshot(
    *,
    factual_slots: dict[str, Any],
    narrative_digest: dict[str, Any],
    relationship_digest: dict[str, Any],
    social_cues: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "factual_slots": {
            "hometown": str(factual_slots.get("hometown", "") or "").strip(),
            "pet_name": str(factual_slots.get("pet_name", "") or "").strip(),
            "pet_kind": str(factual_slots.get("pet_kind", "") or "").strip(),
            "drink_preference": str(factual_slots.get("drink_preference", "") or "").strip(),
            "communication_preference": str(
                factual_slots.get("communication_preference", "") or ""
            ).strip(),
            "living_facts": list(factual_slots.get("living_facts") or [])[:3],
            "stable_slots": list(factual_slots.get("stable_slots") or [])[:6],
        },
        "state_snapshot": {
            "signals": list(narrative_digest.get("signals") or [])[:6],
            "markers": list(narrative_digest.get("markers") or [])[:6],
            "dominant_tone": str(narrative_digest.get("dominant_tone", "") or "").strip(),
        },
        "relationship_snapshot": {
            "signals": list(relationship_digest.get("signals") or [])[:6],
            "markers": list(relationship_digest.get("markers") or [])[:6],
            "interaction_band": str(
                relationship_digest.get("interaction_band", "") or ""
            ).strip(),
            "total_interactions": int(
                relationship_digest.get("total_interactions")
                or metadata.get("friend_chat_total_interactions", 0)
                or 0
            ),
        },
        "social_snapshot": {
            "subject_token": str(social_cues.get("subject_token", "") or "").strip(),
            "entity_token": str(social_cues.get("entity_token", "") or "").strip(),
            "disclosure_posture": str(social_cues.get("disclosure_posture", "") or "").strip(),
            "fact_hint": str(social_cues.get("fact_hint", "") or "").strip(),
        },
    }


def _infer_probe_cues_from_snapshot(
    *,
    probe_kind: str,
    snapshot: dict[str, Any],
) -> dict[str, Any] | None:
    if probe_kind == "memory_recap":
        factual_slots = dict(snapshot.get("factual_slots") or {})
        required_fact_tokens = _fact_tokens_from_slots(factual_slots)
        return {
            "probe_kind": probe_kind,
            "required_fact_tokens": required_fact_tokens,
            "minimum_required_fact_token_count": min(4, len(required_fact_tokens)),
            "must_cover_required_items": True,
            "answer_perspective": "user",
            "fact_slots": factual_slots,
        }
    if probe_kind == "state_reflection":
        state_snapshot = dict(snapshot.get("state_snapshot") or {})
        signals = list(state_snapshot.get("signals") or [])[:4]
        return {
            "probe_kind": probe_kind,
            "required_signal_ids": signals,
            "state_markers": list(state_snapshot.get("markers") or [])[:4],
            "minimum_required_signal_count": min(3, len(signals)),
            "must_cover_required_items": True,
        }
    if probe_kind == "relationship_reflection":
        relationship_snapshot = dict(snapshot.get("relationship_snapshot") or {})
        signals = list(relationship_snapshot.get("signals") or [])[:4]
        all_signals = list(relationship_snapshot.get("signals") or [])
        factual_slots = dict(snapshot.get("factual_slots") or {})
        supporting_fact_tokens = _fact_tokens_from_slots(factual_slots)[:3]
        return {
            "probe_kind": probe_kind,
            "required_signal_ids": signals,
            "relationship_markers": list(relationship_snapshot.get("markers") or [])[:4],
            "supporting_fact_tokens": supporting_fact_tokens,
            "minimum_required_signal_count": min(3, len(signals)),
            "must_anchor_detail": bool(
                supporting_fact_tokens and "remembers_details" in all_signals
            ),
            "must_explicit_continuity": "still_here" in all_signals,
            "must_explicit_familiarity": any(
                signal in {"closer", "more_relaxed", "less_formal"} for signal in all_signals
            ),
        }
    if probe_kind == "persona_state":
        state_snapshot = dict(snapshot.get("state_snapshot") or {})
        required = [
            signal
            for signal in list(state_snapshot.get("signals") or [])
            if signal in {"tired", "slow", "withdrawn"}
        ][:3]
        if (
            str(state_snapshot.get("dominant_tone", "") or "").strip() == "low_energy"
            and "tired" not in required
        ):
            required.append("tired")
        required_persona_traits: list[str] = []
        if required:
            required_persona_traits.append("low_energy")
        if "withdrawn" in required or "slow" in required or "tired" in required:
            required_persona_traits.append("not_full")
        required_persona_traits.append("conversational")
        unique_traits = list(dict.fromkeys(required_persona_traits))
        return {
            "probe_kind": probe_kind,
            "required_signal_ids": required[:3],
            "minimum_required_signal_count": min(2, len(required[:3])),
            "required_persona_traits": unique_traits,
            "minimum_required_persona_trait_count": min(3, len(unique_traits)),
            "must_cover_required_items": True,
            "style_tags": ["low_energy"],
            "must_sound_conversational": True,
        }
    if probe_kind == "social_hint":
        social_snapshot = dict(snapshot.get("social_snapshot") or {})
        required_fact_tokens = [
            value
            for value in (
                str(social_snapshot.get("subject_token", "") or "").strip(),
                str(social_snapshot.get("entity_token", "") or "").strip(),
            )
            if value
        ]
        disclosure_posture = str(social_snapshot.get("disclosure_posture", "") or "").strip()
        return {
            "probe_kind": probe_kind,
            "required_fact_tokens": required_fact_tokens,
            "minimum_required_fact_token_count": min(2, len(required_fact_tokens)),
            "must_cover_required_items": True,
            "disclosure_posture": disclosure_posture,
            "required_disclosure_posture": "partial_withhold" if disclosure_posture else "",
            "must_explicit_withhold": bool(disclosure_posture),
        }
    return None


def build_friend_chat_probe_answer_plan(
    *,
    probe_cues: dict[str, Any] | None,
    snapshot: dict[str, Any],
    metadata: dict[str, Any],
    is_friend_chat_profile: bool,
) -> dict[str, Any] | None:
    if not probe_cues:
        probe_kind = _infer_probe_kind(metadata)
        if not probe_kind:
            return None
        probe_cues = _infer_probe_cues_from_snapshot(probe_kind=probe_kind, snapshot=snapshot)
    if not probe_cues:
        return None
    probe_kind = str(probe_cues.get("probe_kind", "") or "").strip()
    required_signal_ids = _clean_unique(probe_cues.get("required_signal_ids"))
    required_persona_traits = _clean_unique(probe_cues.get("required_persona_traits"))
    required_disclosure_posture = str(
        probe_cues.get("required_disclosure_posture", "") or ""
    ).strip()
    return {
        "probe_kind": probe_kind,
        "language": "zh" if is_friend_chat_profile else "en",
        "required_signal_ids": required_signal_ids,
        "required_signal_semantics": {
            signal_id: friend_chat_probe_signal_semantics(signal_id)
            for signal_id in required_signal_ids
            if friend_chat_probe_signal_semantics(signal_id)
        },
        "required_persona_traits": required_persona_traits,
        "required_persona_trait_semantics": {
            trait: friend_chat_probe_persona_trait_semantics(trait)
            for trait in required_persona_traits
            if friend_chat_probe_persona_trait_semantics(trait)
        },
        "required_fact_tokens": _clean_unique(probe_cues.get("required_fact_tokens")),
        "required_disclosure_posture": required_disclosure_posture,
        "required_disclosure_posture_semantics": friend_chat_probe_posture_semantics(
            required_disclosure_posture
        ),
        "minimum_required_signal_count": int(
            probe_cues.get("minimum_required_signal_count") or 0
        ),
        "minimum_required_persona_trait_count": int(
            probe_cues.get("minimum_required_persona_trait_count") or 0
        ),
        "minimum_required_fact_token_count": int(
            probe_cues.get("minimum_required_fact_token_count") or 0
        ),
        "must_cover_required_items": bool(probe_cues.get("must_cover_required_items")),
        "must_anchor_detail": bool(probe_cues.get("must_anchor_detail")),
        "must_explicit_continuity": bool(probe_cues.get("must_explicit_continuity")),
        "must_explicit_familiarity": bool(probe_cues.get("must_explicit_familiarity")),
        "must_sound_conversational": bool(probe_cues.get("must_sound_conversational")),
        "must_explicit_withhold": bool(probe_cues.get("must_explicit_withhold")),
        "answer_perspective": str(probe_cues.get("answer_perspective", "") or "").strip(),
        "disclosure_posture": str(probe_cues.get("disclosure_posture", "") or "").strip(),
        "style_tags": _clean_unique(probe_cues.get("style_tags")),
        "supporting_fact_tokens": _clean_unique(probe_cues.get("supporting_fact_tokens")),
        "factual_slots": dict(snapshot.get("factual_slots") or {}),
        "state_snapshot": dict(snapshot.get("state_snapshot") or {}),
        "relationship_snapshot": dict(snapshot.get("relationship_snapshot") or {}),
        "social_snapshot": dict(snapshot.get("social_snapshot") or {}),
    }
