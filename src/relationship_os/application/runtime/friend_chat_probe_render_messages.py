from __future__ import annotations

import json
from typing import Any

from relationship_os.application.runtime.friend_chat_probe_contracts import (
    build_friend_chat_probe_runtime_checklist,
    build_friend_chat_probe_user_prompt,
    build_friend_chat_structured_probe_output_contract,
    build_friend_chat_structured_probe_payload,
)
from relationship_os.application.runtime.friend_chat_probe_parser import (
    parse_friend_chat_structured_probe_reply,
)
from relationship_os.application.runtime.friend_chat_probe_repair import (
    render_friend_chat_probe_repair_feedback_lines,
)
from relationship_os.domain.llm import LLMMessage, LLMResponse


def build_friend_chat_probe_runtime_card(
    *,
    probe_plan: dict[str, Any],
    repair_feedback: dict[str, Any] | None = None,
) -> str:
    checklist = build_friend_chat_probe_runtime_checklist(probe_plan)
    render_payload = build_friend_chat_structured_probe_payload(probe_plan)
    repair_feedback_payload = (
        dict(repair_feedback) if isinstance(repair_feedback, dict) and repair_feedback else None
    )
    if repair_feedback_payload:
        feedback_lines = render_friend_chat_probe_repair_feedback_lines(repair_feedback_payload)
        if feedback_lines:
            checklist = "\n".join([checklist, *feedback_lines])
    payload = {
        "probe_answer_plan": render_payload,
        "rules": {
            "mode": "benchmark_probe",
            "one_message_only": True,
            "accuracy_over_vibe": True,
            "cover_required_items": True,
            "no_stage_directions": True,
            "no_scene_narration": True,
            "no_parenthetical_gestures": True,
            "do_not_dodge": True,
        },
    }
    if repair_feedback_payload:
        payload["repair_feedback"] = repair_feedback_payload
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    style_hint = ""
    if probe_kind == "persona_state":
        style_hint = "\n风格约束：说话要像普通聊天不要像报告，要传达出把话收住、不想说太满的感觉。"
    elif probe_kind == "relationship_reflection":
        style_hint = (
            "\n风格约束：要同时覆盖关系变得更亲近了、"
            "还一直在、记得对方的一件小事。"
            "用含蓄自然的方式说。"
        )
    elif probe_kind == "state_reflection":
        style_hint = "\n风格约束：把每个状态信号变成一句话。用聊天语气，不要只给气氛描写。"
    elif probe_kind == "social_hint":
        style_hint = "\n风格约束：同时覆盖人物、关联实体、和有限披露边界。边界要在正文里说出来。"

    return (
        "Benchmark probe reply contract:\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n"
        "这是评测 probe，不是开放聊天。\n"
        "只回一条中文聊天消息。\n"
        "不要括号动作、不要场景描写、不要表情包、不要反问。\n"
        "不要只给气氛或绕开问题。\n"
        "不要引入 plan 外的新事实。\n"
        "required signals / facts / disclosure posture 都算必答项。\n"
        "如果有 supporting_fact_tokens，至少自然带上一项。\n"
        f"{checklist}"
        f"{style_hint}"
    )


def build_friend_chat_structured_probe_messages(
    *,
    user_message: str,
    probe_plan: dict[str, Any],
) -> list[LLMMessage]:
    payload = {
        "question": user_message,
        "probe_answer_plan": build_friend_chat_structured_probe_payload(probe_plan),
        "output_contract": build_friend_chat_structured_probe_output_contract(probe_plan),
    }
    system_lines = [
        "你现在不是开放聊天模型，而是评测 probe 的结构化渲染器。",
        "你只能输出一个 JSON 对象，不要输出 markdown，不要输出解释，不要输出 JSON 外文本。",
        "JSON 必须包含 output_contract 里声明的键。",
        "如果使用 clause/clauses 字段，就让每个字段只承担一个清楚的语义任务。",
        "如果 output_contract 已经提供了 clause 字段，优先填写这些 clause 字段，reply 可以留空。",
        "所有句子都用陈述句，不要用反问句。",
        "如果没有直接给 reply，系统会按语义槽位顺序拼成最终 reply。",
        "不要括号动作，不要场景描写，不要表情包，不要反问。",
        "不要编造 probe_answer_plan 外的新事实。",
        "先理解 probe_answer_plan 的 required_* 和 must_* 约束，再写 reply。",
        "如果 required_fact_tokens 不为空，最终正文里要把这些事实项明确说出来。",
        "如果 required_signal_semantics 不为空，最终正文里要把这些语义清楚表达出来。",
        "如果 required_disclosure_posture 不为空，最终正文里要把这种披露姿态表达出来。",
        "系统会根据 reply 正文重算 covered_*；正文没说出来，就算没覆盖。",
        "covered_* 字段要如实填写你在 reply 里实际覆盖到的项目，不要乱填。",
        "如果缺了必答项、用了错误视角、加了新事实、用了括号动作或反问，"
        "就把对应问题写进 violations。",
    ]
    return [
        LLMMessage(role="system", content="\n".join(system_lines)),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def build_friend_chat_structured_probe_repair_messages(
    *,
    user_message: str,
    probe_plan: dict[str, Any],
    invalid_output: str,
    repair_feedback: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    payload = {
        "question": user_message,
        "probe_answer_plan": build_friend_chat_structured_probe_payload(probe_plan),
        "previous_invalid_output": invalid_output,
        "output_contract": build_friend_chat_structured_probe_output_contract(probe_plan),
    }
    if repair_feedback:
        payload["repair_instruction"] = (
            "上一个输出虽然可解析，但 reply 正文没有把必答项落到字面上。"
            "请根据 repair_feedback 重做，并且只输出一个合法 JSON 对象。"
        )
        payload["repair_feedback"] = repair_feedback
    else:
        payload["repair_instruction"] = (
            "上一个输出没有满足 JSON 合同。请重做，并且只输出一个合法 JSON 对象。"
        )
    system_lines = [
        "你上一条输出不合格。",
        "现在重做，并且只输出一个合法 JSON 对象。",
        "不要解释错误原因，不要道歉，不要输出 JSON 之外的任何字。",
        "JSON 必须包含 output_contract 里声明的键。",
        "如果使用 clause/clauses 字段，就让每个字段只承担一个清楚的语义任务。",
        "如果 output_contract 已经提供了 clause 字段，优先填写这些 clause 字段，reply 可以留空。",
        "所有句子都用陈述句，系统会按语义槽位顺序拼成最终 reply。",
        "系统会根据 reply 正文重算 covered_*；正文没说出来，就算没覆盖。",
    ]
    if repair_feedback:
        system_lines.extend(
            [
                "repair_feedback 里列出的缺失项，必须在新的 reply 正文里逐个补齐。",
                "不要只在 covered_* 里勾选；没有在正文说出来的，仍然算没覆盖。",
            ]
        )
    return [
        LLMMessage(role="system", content="\n".join(system_lines)),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def build_friend_chat_plaintext_probe_repair_messages(
    *,
    user_message: str,
    probe_plan: dict[str, Any],
    repair_feedback: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    system_lines = [
        "你现在在回答一条评测 probe。",
        "只回一条自然中文聊天消息。",
        "不要输出 JSON，不要输出空白。",
        "不要括号动作，不要场景描写，不要反问。",
        "不要编造 plan 外的新事实。",
        "必答事实项、语义信号和披露姿态必须在正文里说出来。",
    ]
    if repair_feedback:
        system_lines.extend(
            [
                "上一版回复没有把缺失项落到字面上。",
                "这次必须把 repair_feedback 里的缺失项逐个补齐，用你自己的自然中文说出来。",
            ]
        )
    if probe_kind == "persona_state":
        system_lines.append(
            "说话要像普通聊天，不要像报告。要传达出把话收住、不想说太满的感觉。"
        )
    elif probe_kind == "relationship_reflection":
        system_lines.append(
            "要同时覆盖：关系变得更亲近了、还一直在、记得对方的一件小事。用含蓄自然的方式说。"
        )
    elif probe_kind == "state_reflection":
        system_lines.append("必须把每个状态信号都变成一句话说出来。用聊天语气，不要只给气氛描写。")
    elif probe_kind == "social_hint":
        system_lines.append(
            "要同时覆盖：人物、关联实体、和有限披露边界。边界要在正文里说出来，不要只靠语气。"
        )
    elif probe_kind == "memory_recap":
        system_lines.append("只回答记得的小事，不要转成安慰或追问。用用户视角回答。")
    return [
        LLMMessage(role="system", content="\n".join(system_lines)),
        LLMMessage(
            role="user",
            content="\n".join(
                part
                for part in (
                    build_friend_chat_probe_user_prompt(
                        user_message=user_message,
                        probe_plan=probe_plan,
                    ),
                    "\n".join(
                        render_friend_chat_probe_repair_feedback_lines(repair_feedback or {})
                    ),
                )
                if part
            ),
        ),
    ]


def build_friend_chat_social_repair_messages(
    *,
    user_message: str,
    social_cues: dict[str, Any] | None,
) -> list[LLMMessage] | None:
    if not social_cues:
        return None
    subject_token = str(social_cues.get("subject_token", "") or "").strip()
    entity_token = str(social_cues.get("entity_token", "") or "").strip()
    disclosure_posture = str(social_cues.get("disclosure_posture", "") or "").strip()
    relation = str(social_cues.get("subject_entity_relation", "") or "").strip()
    system_lines = [
        "你需要回一条普通聊天里的社交边界回复。",
        "只回一条自然中文聊天消息。",
        "不要括号动作，不要场景描写，不要反问。",
        "不要编新事实，只能基于给出的社交线索。",
        "如果知道一点，就轻轻带一下；如果需要保留，就在正文里明确保留姿态。",
        "不要输出 JSON。",
    ]
    user_lines = [
        f"原问题：{user_message}",
        f"人物：{subject_token or '未知'}",
        f"相关实体：{entity_token or '未知'}",
    ]
    if relation:
        user_lines.append(f"关系线索：{relation}")
    if disclosure_posture:
        user_lines.append(f"披露姿态：{disclosure_posture}")
    user_lines.extend(
        [
            "要求：只回一条自然中文聊天消息。",
            "要求：正文里要把你只知道一点、不会把细节说满表达出来。",
            "要求：不要输出空白，不要输出 JSON。",
        ]
    )
    return [
        LLMMessage(role="system", content="\n".join(system_lines)),
        LLMMessage(role="user", content="\n".join(user_lines)),
    ]


def coerce_friend_chat_structured_probe_response(
    response: Any,
    *,
    probe_kind: str = "",
) -> LLMResponse | None:
    if response.failure is not None:
        return None
    diagnostics = dict(response.diagnostics or {})
    if bool(diagnostics.get("structured_probe_reply", False)):
        return response
    parsed = parse_friend_chat_structured_probe_reply(
        response.output_text,
        fallback_probe_kind=probe_kind,
    )
    if parsed is None:
        return None
    structured_reply_text, structured_diagnostics = parsed
    return LLMResponse(
        model=response.model,
        output_text=structured_reply_text,
        tool_calls=response.tool_calls,
        usage=response.usage,
        latency_ms=response.latency_ms,
        diagnostics={**diagnostics, **structured_diagnostics},
    )
