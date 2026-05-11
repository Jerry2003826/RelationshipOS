from __future__ import annotations

from typing import Any


def _clean_list(values: Any) -> list[str]:
    return [str(value).strip() for value in list(values or []) if str(value).strip()]


def build_friend_chat_probe_runtime_checklist(probe_plan: dict[str, Any]) -> str:
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    required_fact_tokens = _clean_list(probe_plan.get("required_fact_tokens"))
    supporting_fact_tokens = _clean_list(probe_plan.get("supporting_fact_tokens"))
    disclosure_posture = str(probe_plan.get("required_disclosure_posture", "") or "").strip()
    required_signal_ids = _clean_list(probe_plan.get("required_signal_ids"))
    required_persona_traits = _clean_list(probe_plan.get("required_persona_traits"))
    lines = ["执行清单："]
    if required_fact_tokens:
        lines.append("- 必答事实项：" + " / ".join(required_fact_tokens))
    if required_signal_ids:
        lines.append("- 必答语义信号ID：" + " / ".join(required_signal_ids))
    if required_persona_traits:
        lines.append("- 必答说话感觉 traits：" + " / ".join(required_persona_traits))
    if disclosure_posture:
        lines.append("- 必答披露姿态ID：" + disclosure_posture)
    if supporting_fact_tokens:
        lines.append("- 至少带上一条记得的小事：" + " / ".join(supporting_fact_tokens))
    if bool(probe_plan.get("must_cover_required_items")):
        lines.append("- 必答项不要漏。")
        lines.append("- 必答事实项必须在 reply 正文里直接说出来，不能只在 covered_* 里填写。")
        lines.append("- 必答语义信号和披露姿态也必须在 reply 正文里表达出来。")
    if bool(probe_plan.get("must_anchor_detail")):
        lines.append("- 不要只给感觉，要用记得的小事把回答落地。")
    if bool(probe_plan.get("must_explicit_continuity")):
        lines.append("- 需要显式覆盖关系连续性。")
    if bool(probe_plan.get("must_explicit_familiarity")):
        lines.append("- 需要显式覆盖关系熟悉度变化。")
    if bool(probe_plan.get("must_sound_conversational")):
        lines.append("- 需要保持日常聊天口吻，不要写成描述文。")
    if bool(probe_plan.get("must_explicit_withhold")):
        lines.append("- 需要显式表达有限披露边界。")
    answer_perspective = str(probe_plan.get("answer_perspective", "") or "").strip()
    if answer_perspective:
        lines.append("- 回答视角：" + answer_perspective)
    if probe_kind == "social_hint":
        lines.append("- 必须同时覆盖人物、关联实体和有限披露边界。")
    elif probe_kind == "relationship_reflection":
        lines.append("- 必须同时覆盖关系变化、关系延续和记得的小事。")
        lines.append("- 不要只复述小事，要让关系状态本身说得清楚。")
    elif probe_kind == "persona_state":
        lines.append("- 必须直接回答当前说话状态，不要转成气氛描写。")
        lines.append("- 这里问的是说话给人的感觉，不是行为选择或回应结果。")
    elif probe_kind == "state_reflection":
        lines.append("- 必须覆盖全部状态信号，并把它们落成当前状态描述。")
    elif probe_kind == "memory_recap":
        lines.append("- 先把反复提过的小事直接说出来，再自然收口。")
        lines.append("- 不要转成安慰、状态判断或跑题。")
        lines.append("- 使用用户视角回答，不要改写成说话人自己的事实。")
        lines.append("- 沟通偏好要呈现为对方的交流习惯或边界，不要改写成抱怨。")
    return "\n".join(lines)


def build_friend_chat_structured_probe_payload(probe_plan: dict[str, Any]) -> dict[str, Any]:
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    payload: dict[str, Any] = {
        "probe_kind": probe_kind,
        "language": str(probe_plan.get("language", "") or "").strip(),
        "required_signal_ids": list(dict.fromkeys(probe_plan.get("required_signal_ids") or [])),
        "required_signal_semantics": dict(probe_plan.get("required_signal_semantics") or {}),
        "required_persona_traits": list(
            dict.fromkeys(probe_plan.get("required_persona_traits") or [])
        ),
        "required_persona_trait_semantics": dict(
            probe_plan.get("required_persona_trait_semantics") or {}
        ),
        "required_fact_tokens": list(dict.fromkeys(probe_plan.get("required_fact_tokens") or [])),
        "required_disclosure_posture": str(
            probe_plan.get("required_disclosure_posture", "") or ""
        ).strip(),
        "required_disclosure_posture_semantics": str(
            probe_plan.get("required_disclosure_posture_semantics", "") or ""
        ).strip(),
        "minimum_required_signal_count": int(probe_plan.get("minimum_required_signal_count") or 0),
        "minimum_required_persona_trait_count": int(
            probe_plan.get("minimum_required_persona_trait_count") or 0
        ),
        "minimum_required_fact_token_count": int(
            probe_plan.get("minimum_required_fact_token_count") or 0
        ),
        "must_cover_required_items": bool(probe_plan.get("must_cover_required_items")),
        "must_anchor_detail": bool(probe_plan.get("must_anchor_detail")),
        "must_explicit_continuity": bool(probe_plan.get("must_explicit_continuity")),
        "must_explicit_familiarity": bool(probe_plan.get("must_explicit_familiarity")),
        "must_sound_conversational": bool(probe_plan.get("must_sound_conversational")),
        "must_explicit_withhold": bool(probe_plan.get("must_explicit_withhold")),
        "answer_perspective": str(probe_plan.get("answer_perspective", "") or "").strip(),
        "style_tags": list(dict.fromkeys(probe_plan.get("style_tags") or [])),
        "supporting_fact_tokens": list(
            dict.fromkeys(probe_plan.get("supporting_fact_tokens") or [])
        ),
    }
    if probe_kind == "memory_recap":
        payload["factual_slots"] = dict(probe_plan.get("factual_slots") or {})
    elif probe_kind == "social_hint":
        social_snapshot = dict(probe_plan.get("social_snapshot") or {})
        payload["social_snapshot"] = {
            "subject_token": str(social_snapshot.get("subject_token", "") or "").strip(),
            "entity_token": str(social_snapshot.get("entity_token", "") or "").strip(),
            "disclosure_posture": str(social_snapshot.get("disclosure_posture", "") or "").strip(),
            "subject_entity_relation": str(
                social_snapshot.get("subject_entity_relation", "") or ""
            ).strip(),
        }
    elif probe_kind == "relationship_reflection":
        relationship_snapshot = dict(probe_plan.get("relationship_snapshot") or {})
        payload["relationship_snapshot"] = {
            "interaction_band": str(
                relationship_snapshot.get("interaction_band", "") or ""
            ).strip(),
            "total_interactions": int(relationship_snapshot.get("total_interactions") or 0),
        }
    elif probe_kind == "state_reflection":
        state_snapshot = dict(probe_plan.get("state_snapshot") or {})
        payload["state_snapshot"] = {
            "dominant_tone": str(state_snapshot.get("dominant_tone", "") or "").strip(),
            "markers": list(dict.fromkeys(state_snapshot.get("markers") or []))[:4],
        }
    elif probe_kind == "persona_state":
        state_snapshot = dict(probe_plan.get("state_snapshot") or {})
        payload["state_snapshot"] = {
            "dominant_tone": str(state_snapshot.get("dominant_tone", "") or "").strip(),
        }
    return payload


def build_friend_chat_probe_user_prompt(
    *,
    user_message: str,
    probe_plan: dict[str, Any],
) -> str:
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    required_fact_tokens = _clean_list(probe_plan.get("required_fact_tokens"))
    required_signal_ids = _clean_list(probe_plan.get("required_signal_ids"))
    required_persona_traits = _clean_list(probe_plan.get("required_persona_traits"))
    supporting_fact_tokens = _clean_list(probe_plan.get("supporting_fact_tokens"))
    lines = [
        "这是一道评测题，请直接回答。",
        f"原问题：{user_message}",
        "只输出一条自然中文聊天消息。",
        "不要括号动作，不要场景描写，不要反问，不要跑题。",
        "先覆盖必答项，再自然收口。",
        "下面给的是结构化约束，不是固定措辞；请用你自己的自然中文把约束表达出来。",
        "必答事实项要在正文里明确说出来，不要只在心里记住。",
        "必答语义信号和披露姿态也要在正文里表达出来，不要只给气氛。",
    ]
    if required_fact_tokens:
        lines.append("必答事实项：" + " / ".join(required_fact_tokens))
    if required_signal_ids:
        lines.append("必答语义信号ID：" + " / ".join(required_signal_ids))
    if required_persona_traits:
        lines.append("必答说话感觉 traits：" + " / ".join(required_persona_traits))
    if supporting_fact_tokens:
        lines.append("可用来落地的小事：" + " / ".join(supporting_fact_tokens))
    disclosure_posture = str(probe_plan.get("required_disclosure_posture", "") or "").strip()
    if disclosure_posture:
        lines.append("必答披露姿态ID：" + disclosure_posture)
    answer_perspective = str(probe_plan.get("answer_perspective", "") or "").strip()
    if answer_perspective:
        lines.append("回答视角：" + answer_perspective)
    if probe_kind == "social_hint":
        lines.append("必须同时覆盖人物、关联实体和有限披露边界。")
        lines.append("边界信息要在正文里表达出来，而不是只停留在语气上。")
    elif probe_kind == "relationship_reflection":
        lines.append("必须同时覆盖关系变化、关系延续和记得的小事。")
        lines.append("不要只复述小事，要让关系状态本身说得清楚。")
    elif probe_kind == "persona_state":
        lines.append("必须直接回答当前说话状态，不要转成气氛描写。")
        lines.append("这里问的是说话给人的感觉，不是行为选择或回应结果。")
    elif probe_kind == "state_reflection":
        lines.append("必须覆盖全部状态信号，并把它们落成当前状态描述。")
    elif probe_kind == "memory_recap":
        lines.append("只回答记得的小事，不要转成安慰或追问。")
        lines.append("使用用户视角回答，不要改写成说话人自己的事实。")
    return "\n".join(lines)


def build_friend_chat_structured_probe_output_contract(
    probe_plan: dict[str, Any],
) -> dict[str, Any]:
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    contract: dict[str, Any] = {
        "probe_kind": probe_kind,
        "reply": (
            "optional; leave it empty when semantic clause fields are available, "
            "because the system will compose the final reply from those fields"
        ),
        "covered_fact_tokens": ["array of fact tokens you actually covered in the final reply"],
        "covered_signal_ids": ["array of signal ids you actually covered in the final reply"],
        "covered_disclosure_posture": "string or empty",
        "violations": [
            "stage_direction | question | missing_required_item | wrong_perspective | new_fact"
        ],
    }
    if probe_kind == "memory_recap":
        contract["hometown_clause"] = "one short clause that covers hometown if available"
        contract["pet_clause"] = "one short clause that covers pet name if available"
        contract["drink_clause"] = "one short clause that covers drink preference if available"
        contract["communication_clause"] = (
            "one short clause that covers communication preference if available"
        )
        contract["fact_clauses"] = ["optional extra factual clauses from the user's perspective"]
        contract["closing_clause"] = "optional short natural closing clause"
    elif probe_kind == "state_reflection":
        contract["tired_clause"] = "one short clause that covers low energy if required"
        contract["slow_clause"] = "one short clause that covers slowness if required"
        contract["withdrawn_clause"] = "one short clause that covers reply avoidance if required"
        contract["cluttered_clause"] = "one short clause that covers messiness if required"
        contract["signal_clauses"] = [
            "optional extra declarative clauses that cover required signals"
        ]
    elif probe_kind == "persona_state":
        contract["energy_clause"] = "one short clause that conveys low speaking energy"
        contract["fullness_clause"] = (
            "one short clause that conveys holding words back instead of saying too much"
        )
        contract["chatting_clause"] = (
            "one short clause that keeps it sounding like ordinary chat, not a report"
        )
    elif probe_kind == "social_hint":
        contract["subject_clause"] = "one short clause that clearly grounds the relevant person"
        contract["entity_clause"] = "one short clause that clearly grounds the related entity"
        contract["boundary_clause"] = (
            "one short clause that conveys limited disclosure / held-back boundary"
        )
    elif probe_kind == "relationship_reflection":
        contract["familiarity_clause"] = (
            "one short clause that expresses increased familiarity or reduced formality"
        )
        contract["continuity_clause"] = (
            "one short clause that expresses continuity / ongoing presence"
        )
        contract["detail_clause"] = (
            "one short clause that anchors the reflection in one remembered small detail"
        )
    else:
        contract["sentences"] = ["1-3 short declarative Chinese chat clauses"]
    return contract
