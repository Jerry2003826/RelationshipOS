from __future__ import annotations

from typing import Any


def build_edge_entity_card(analysis: Any, *, entity_name: str) -> str:
    traits = dict(analysis.entity_persona.get("current_traits") or {})
    mood = dict(analysis.entity_persona.get("mood") or {})
    lines = [
        f"name={analysis.entity_persona.get('entity_name') or entity_name}",
        f"archetype={analysis.entity_persona.get('persona_archetype') or 'default'}",
        "traits="
        + ", ".join(
            f"{key}={value}"
            for key, value in (
                ("warmth", traits.get("warmth", 0.5)),
                ("directness", traits.get("directness", 0.5)),
                ("humor", traits.get("humor", 0.5)),
                ("theatricality", traits.get("theatricality", 0.5)),
            )
        ),
        "mood="
        + ", ".join(
            f"{key}={mood.get(key)}"
            for key in ("tone", "energy", "expression_drive")
            if mood.get(key) is not None
        ),
    ]
    if analysis.entity_persona.get("persona_summary"):
        lines.append(f"summary={analysis.entity_persona.get('persona_summary')}")
    if analysis.entity_persona.get("speech_style"):
        lines.append(f"speech_style={analysis.entity_persona.get('speech_style')}")
    return "Entity card:\n- " + "\n- ".join(lines)


def build_edge_relationship_card(analysis: Any) -> str:
    drift = dict(analysis.entity_social_world.get("relationships", {})).get(
        analysis.memory_recall.get("user_id", ""),
        {},
    )
    if not drift:
        drift = {}
    lines = [
        f"tom_inference={analysis.relationship_state.tom_inference}",
        f"turbulence_risk={analysis.relationship_state.turbulence_risk}",
        "drift="
        + ", ".join(
            f"{key}={drift.get(key)}"
            for key in (
                "familiarity",
                "trust",
                "softness",
                "playfulness",
                "disclosure_appetite",
            )
            if drift.get(key) is not None
        ),
    ]
    return "Relationship card:\n- " + "\n- ".join(lines)


def build_edge_narrative_card(analysis: Any, *, include_narrative_card: bool) -> str | None:
    if not include_narrative_card:
        return None
    self_narrative = dict(analysis.entity_persona.get("self_narrative") or {})
    goal_state = dict(analysis.entity_persona.get("goal_state") or {})
    world_state = dict(analysis.entity_persona.get("world_state") or {})
    environment = dict(world_state.get("environment_appraisal") or {})
    digest = str(
        self_narrative.get("narrative_digest") or self_narrative.get("summary") or ""
    ).strip()
    goal_digest = str(goal_state.get("goal_digest") or "").strip()
    focus = str(environment.get("focus") or "").strip()
    lines: list[str] = []
    if digest:
        lines.append(f"narrative={digest}")
    if goal_digest:
        lines.append(f"goal_digest={goal_digest}")
    if focus:
        lines.append(f"world_focus={focus}")
    for entry in list(self_narrative.get("recent_entries") or [])[:2]:
        content = str(entry).strip()
        if content:
            lines.append(f"recent={content[:140]}")
    if not lines:
        return None
    return "Narrative card:\n- " + "\n- ".join(lines)


def build_edge_conscience_card(analysis: Any) -> str:
    conscience = analysis.conscience_assessment
    lines = [
        f"mode={conscience.get('mode', 'withhold')}",
        f"reason={conscience.get('reason', '')}",
        f"allowed_fact_count={conscience.get('allowed_fact_count', 0)}",
        f"attribution_required={conscience.get('attribution_required', False)}",
        f"ambiguity_required={conscience.get('ambiguity_required', True)}",
        f"quote_style={conscience.get('quote_style', 'opaque')}",
    ]
    return "Conscience card:\n- " + "\n- ".join(lines)


def build_edge_memory_card(trimmed_memory: list[dict[str, Any]]) -> str:
    if not trimmed_memory:
        return "Memory card:\n- none"
    lines = []
    for item in trimmed_memory:
        prefix = f"[{item.get('scope', 'memory')}]"
        if item.get("source_user_id") and str(item.get("scope")) in {"self_user", "other_user"}:
            prefix += f" from={item.get('source_user_id')}"
        if item.get("subject_user_id"):
            prefix += f" subject={item.get('subject_user_id')}"
        if item.get("attribution_guard"):
            prefix += f" guard={item.get('attribution_guard')}"
        lines.append(f"{prefix} {str(item.get('value', ''))[:180]}")
    return "Memory card:\n- " + "\n- ".join(lines)


def build_edge_recent_turns_card(
    *,
    all_transcript: list[dict[str, Any]],
    recent_turn_count: int,
) -> str | None:
    recent = all_transcript[-max(2, recent_turn_count) :]
    if not recent:
        return None
    lines = []
    for message in recent:
        role = "User" if message.get("role") == "user" else "You"
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"{role}: {content[:120]}{'…' if len(content) > 120 else ''}")
    if not lines:
        return None
    return "Recent turns:\n- " + "\n- ".join(lines)


def build_edge_reply_contract_card(lines: tuple[str, ...]) -> str:
    return "Reply contract:\n- " + "\n- ".join(lines)


def build_edge_output_card(
    analysis: Any,
    *,
    routing_mode: str,
    is_friend_chat_profile: bool,
) -> str:
    if routing_mode == "factual_recall":
        lines = [
            "mode=factual_recall",
            f"max_sentences={min(2, analysis.response_rendering_policy.max_sentences)}",
            "anchor=answer concrete facts first",
            f"question_strategy={analysis.response_draft_plan.question_strategy}",
        ]
    elif routing_mode == "social_disclosure":
        lines = [
            "mode=social_disclosure",
            f"conscience_mode={analysis.conscience_assessment.get('mode', 'withhold')}",
            f"quote_style={analysis.conscience_assessment.get('quote_style', 'opaque')}",
            "anchor=attribute cross-user facts explicitly",
        ]
    else:
        if is_friend_chat_profile:
            lines = [
                "mode=friend_chat_zh",
                f"max_sentences={analysis.response_rendering_policy.max_sentences}",
                "anchor=像真人微信聊天，少解释、少指导、少治疗感",
                "continuity=接住上一轮语气、最近状态和没聊完的话头",
            ]
        else:
            lines = [
                f"mode={analysis.response_rendering_policy.rendering_mode}",
                f"max_sentences={analysis.response_rendering_policy.max_sentences}",
                f"question_strategy={analysis.response_draft_plan.question_strategy}",
                f"lead_with={analysis.guidance_plan.lead_with}",
            ]
    return "Output card:\n- " + "\n- ".join(lines)
