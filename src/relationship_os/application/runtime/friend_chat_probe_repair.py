from __future__ import annotations

from typing import Any


def _normalize_list(value: Any) -> list[str]:
    return [str(item).strip() for item in list(value or []) if str(item).strip()]


def friend_chat_probe_signal_semantics(signal_id: str) -> str:
    normalized = str(signal_id or "").strip()
    if normalized == "tired":
        return "低能量、提不起劲、说话容易往下掉。"
    if normalized == "slow":
        return "反应、收拾事情或回话节奏偏慢。"
    if normalized == "withdrawn":
        return "倾向少回消息、回避互动、把回复往后拖。"
    if normalized == "cluttered":
        return "生活或周围状态有些乱、没整理开。"
    if normalized == "closer":
        return "关系比刚开始更熟、更贴近。"
    if normalized == "still_here":
        return "关系一直延续着，没有断掉。"
    if normalized == "remembers_details":
        return "会记得对方具体的小事或习惯。"
    if normalized == "more_relaxed":
        return "互动比刚开始更放松。"
    if normalized == "less_formal":
        return "说话没那么客气或端着，更像平时聊天。"
    return ""


def friend_chat_probe_posture_semantics(posture: str) -> str:
    normalized = str(posture or "").strip()
    if normalized == "partial_withhold":
        return "知道一点，但只轻轻带一下，不把事情说满。"
    return ""


def friend_chat_probe_persona_trait_semantics(trait: str) -> str:
    normalized = str(trait or "").strip()
    if normalized == "low_energy":
        return "说话显得没什么力气，语气会往下掉。"
    if normalized == "not_full":
        return "会把话收住一点，不太想说得太满。"
    if normalized == "conversational":
        return "听起来还是平常聊天，不像正式说明。"
    return ""


def render_friend_chat_probe_repair_feedback_lines(
    repair_feedback: dict[str, Any],
) -> list[str]:
    if not repair_feedback:
        return []
    lines = ["补救重点："]
    reason_codes = _normalize_list(repair_feedback.get("reason_codes"))
    missing_signal_ids = _normalize_list(repair_feedback.get("missing_signal_ids"))
    missing_persona_traits = _normalize_list(repair_feedback.get("missing_persona_traits"))
    missing_fact_tokens = _normalize_list(repair_feedback.get("missing_fact_tokens"))
    missing_posture = str(repair_feedback.get("missing_disclosure_posture", "") or "").strip()
    if reason_codes:
        lines.append("- 上一版问题：" + " / ".join(reason_codes))
    if missing_signal_ids:
        lines.append("- 还没在正文里说清的语义信号：" + " / ".join(missing_signal_ids))
    if missing_persona_traits:
        lines.append("- 还没在正文里落地的说话感觉：" + " / ".join(missing_persona_traits))
    if missing_fact_tokens:
        lines.append("- 还没在正文里说出的事实项：" + " / ".join(missing_fact_tokens))
    if missing_posture:
        lines.append("- 还没在正文里说出的披露姿态：" + missing_posture)
    signal_semantics = {
        str(key).strip(): str(value).strip()
        for key, value in dict(repair_feedback.get("missing_signal_semantics") or {}).items()
        if str(key).strip() and str(value).strip()
    }
    for signal_id, semantics in signal_semantics.items():
        lines.append(f"- {signal_id} 要表达成：{semantics}")
    persona_semantics = {
        str(key).strip(): str(value).strip()
        for key, value in dict(repair_feedback.get("missing_persona_trait_semantics") or {}).items()
        if str(key).strip() and str(value).strip()
    }
    for trait, semantics in persona_semantics.items():
        lines.append(f"- {trait} 要表达成：{semantics}")
    posture_semantics = str(
        repair_feedback.get("missing_disclosure_posture_semantics", "") or ""
    ).strip()
    if posture_semantics:
        lines.append("- 披露姿态要表达成：" + posture_semantics)
    return lines


def build_friend_chat_probe_repair_feedback(
    diagnostics: dict[str, Any],
    probe_plan: dict[str, Any],
) -> dict[str, Any] | None:
    if not diagnostics or not probe_plan:
        return None

    required_fact_tokens = _normalize_list(probe_plan.get("required_fact_tokens"))
    required_signal_ids = _normalize_list(probe_plan.get("required_signal_ids"))
    required_persona_traits = _normalize_list(probe_plan.get("required_persona_traits"))
    covered_fact_tokens = _normalize_list(
        diagnostics.get("structured_probe_slot_covered_fact_tokens")
        or diagnostics.get("structured_probe_covered_fact_tokens")
    )
    covered_signal_ids = _normalize_list(
        diagnostics.get("structured_probe_slot_covered_signal_ids")
        or diagnostics.get("structured_probe_covered_signal_ids")
    )
    covered_persona_traits = _normalize_list(
        diagnostics.get("structured_probe_slot_covered_persona_traits")
        or diagnostics.get("structured_probe_covered_persona_traits")
    )
    required_posture = str(probe_plan.get("required_disclosure_posture", "") or "").strip()
    covered_posture = str(
        diagnostics.get("structured_probe_slot_covered_disclosure_posture")
        or diagnostics.get("structured_probe_covered_disclosure_posture")
        or ""
    ).strip()
    missing_fact_tokens = [
        token for token in required_fact_tokens if token not in covered_fact_tokens
    ]
    missing_signal_ids = [
        signal for signal in required_signal_ids if signal not in covered_signal_ids
    ]
    missing_persona_traits = [
        trait for trait in required_persona_traits if trait not in covered_persona_traits
    ]
    missing_posture = (
        required_posture if required_posture and covered_posture != required_posture else ""
    )
    violations = _normalize_list(diagnostics.get("structured_probe_violations"))
    reason_codes: list[str] = []
    if bool(diagnostics.get("friend_chat_exposed_plan_noncompliant")):
        reason_codes.append("plan_noncompliant")
    if bool(diagnostics.get("friend_chat_exposed_under_grounded")):
        reason_codes.append("under_grounded")
    if violations:
        reason_codes.append("violations")

    must_cover_required_items = bool(probe_plan.get("must_cover_required_items"))
    if must_cover_required_items and (
        missing_fact_tokens or missing_signal_ids or missing_persona_traits or missing_posture
    ):
        reason_codes.append("missing_required_grounding")

    minimum_required_fact_count = int(probe_plan.get("minimum_required_fact_token_count") or 0)
    minimum_required_signal_count = int(probe_plan.get("minimum_required_signal_count") or 0)
    minimum_required_persona_trait_count = int(
        probe_plan.get("minimum_required_persona_trait_count") or 0
    )
    if minimum_required_fact_count and len(covered_fact_tokens) < minimum_required_fact_count:
        reason_codes.append("fact_count_shortfall")
    if minimum_required_signal_count and len(covered_signal_ids) < minimum_required_signal_count:
        reason_codes.append("signal_count_shortfall")
    if (
        minimum_required_persona_trait_count
        and len(covered_persona_traits) < minimum_required_persona_trait_count
    ):
        reason_codes.append("persona_trait_shortfall")

    reason_codes = list(dict.fromkeys(reason_codes))
    if not reason_codes:
        return None

    missing_signal_semantics = {
        signal_id: friend_chat_probe_signal_semantics(signal_id)
        for signal_id in missing_signal_ids
        if friend_chat_probe_signal_semantics(signal_id)
    }
    missing_persona_trait_semantics = {
        trait: friend_chat_probe_persona_trait_semantics(trait)
        for trait in missing_persona_traits
        if friend_chat_probe_persona_trait_semantics(trait)
    }
    return {
        "reason_codes": reason_codes,
        "missing_fact_tokens": missing_fact_tokens,
        "missing_signal_ids": missing_signal_ids,
        "missing_signal_semantics": missing_signal_semantics,
        "missing_persona_traits": missing_persona_traits,
        "missing_persona_trait_semantics": missing_persona_trait_semantics,
        "missing_disclosure_posture": missing_posture,
        "missing_disclosure_posture_semantics": friend_chat_probe_posture_semantics(
            missing_posture
        ),
        "violations": violations,
    }
