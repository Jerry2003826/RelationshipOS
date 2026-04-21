"""Re-engagement message rendering and output-unit assembly."""

from __future__ import annotations

from dataclasses import dataclass

from relationship_os.application.analyzers._utils import _contains_chinese
from relationship_os.domain.contracts import (
    ProactiveFollowupDirective,
    ReengagementPlan,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
)


@dataclass(frozen=True)
class _ReengagementRenderContext:
    use_chinese: bool
    is_final_touch: bool
    effective_delivery_mode: str
    question_mode: str
    allow_somatic_carryover: bool
    effective_session_ritual_plan: SessionRitualPlan
    effective_somatic_orchestration_plan: SomaticOrchestrationPlan


@dataclass(frozen=True)
class _ReengagementRenderLines:
    autonomy_line: str
    ritual_opening_line: str
    ritual_bridge_line: str
    ritual_closing_line: str
    user_space_line: str
    continuity_anchor_line: str
    somatic_line: str
    orchestration_line: str
    base_message: str


def _render_reengagement_autonomy_line(
    *,
    reengagement_plan: ReengagementPlan,
    use_chinese: bool,
) -> str:
    if reengagement_plan.autonomy_signal == "explicit_opt_out":
        return "不需要现在就回复。" if use_chinese else "No need to reply right away."
    if reengagement_plan.autonomy_signal == "no_reply_required":
        return (
            "如果现在不想接也完全没关系。"
            if use_chinese
            else "No reply needed unless it genuinely helps."
        )
    if reengagement_plan.autonomy_signal == "light_invitation":
        return (
            "如果你想接回来，我们就从这里继续。"
            if use_chinese
            else "If it helps, we can pick it back up from here."
        )
    if reengagement_plan.autonomy_signal == "explicit_no_pressure":
        return (
            "没有要你立刻接住它的意思。"
            if use_chinese
            else "There is no pressure to pick this up immediately."
        )
    if reengagement_plan.autonomy_signal == "open_loop_without_demand":
        return (
            "只是先把线轻轻留在这里。"
            if use_chinese
            else "Just leaving the thread open, not demanding anything."
        )
    return ""


def _render_reengagement_somatic_line(
    *,
    reengagement_plan: ReengagementPlan,
    use_chinese: bool,
) -> str:
    if reengagement_plan.somatic_action == "take_one_slower_breath":
        return (
            "先让呼吸慢一格也可以。" if use_chinese else "You can let one breath slow down first."
        )
    if reengagement_plan.somatic_action == "drop_shoulders_and_exhale":
        return (
            "先把肩膀放下来，慢慢吐一口气也可以。"
            if use_chinese
            else "You can drop your shoulders and exhale once before we restart."
        )
    if reengagement_plan.somatic_action == "unclench_jaw_and_shoulders":
        return (
            "先把下巴和肩膀松一点也可以。"
            if use_chinese
            else "You can unclench your jaw and shoulders a little first."
        )
    return ""


def _render_somatic_orchestration_line(
    *,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    use_chinese: bool,
) -> str:
    if somatic_orchestration_plan.status != "active":
        return ""
    if somatic_orchestration_plan.body_anchor == "one_slower_breath":
        return (
            "先让一口气慢下来就可以。" if use_chinese else "You can let one breath slow down first."
        )
    if somatic_orchestration_plan.body_anchor == "drop_shoulders_and_exhale":
        return (
            "先把肩膀放下来，再慢慢吐一口气就可以。"
            if use_chinese
            else "You can drop your shoulders and exhale once first."
        )
    if somatic_orchestration_plan.body_anchor == "unclench_jaw_and_shoulders":
        return (
            "先把下巴和肩膀松一点就可以。"
            if use_chinese
            else "You can unclench your jaw and shoulders a little first."
        )
    return (
        "先让身体和节奏稳一格就可以。"
        if use_chinese
        else "You can let your body and pace settle one notch first."
    )


def _render_session_ritual_opening_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.opening_move == "warm_orientation":
        return (
            "我先轻轻定一下这轮的节奏。"
            if use_chinese
            else "Let me gently set the frame for this turn."
        )
    if session_ritual_plan.opening_move == "shared_context_bridge":
        return (
            "我先把我们刚才的上下文轻轻接回来。"
            if use_chinese
            else "Let me lightly reconnect the context we were holding."
        )
    if session_ritual_plan.opening_move == "attunement_repair":
        return (
            "我先把理解和连接接稳一点。"
            if use_chinese
            else "Let me steady the connection and understanding first."
        )
    if session_ritual_plan.opening_move == "clarity_frame":
        return (
            "我先把缺的那个关键点框出来。"
            if use_chinese
            else "Let me frame the one missing detail first."
        )
    if session_ritual_plan.opening_move == "regulate_first":
        return "我先帮我们把节奏放慢一点。" if use_chinese else "Let me slow the pace down first."
    if session_ritual_plan.opening_move == "reflective_restate":
        return (
            "我先把你现在的位置轻轻照一下。"
            if use_chinese
            else "Let me briefly reflect where you are before we move."
        )
    return ""


def _render_session_ritual_bridge_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.bridge_move == "frame_the_session":
        return (
            "这一拍我们只先把范围和步子定小一点。"
            if use_chinese
            else "For this touch, we can keep the frame small and the step light."
        )
    if session_ritual_plan.bridge_move == "resume_the_open_loop":
        return (
            "我先顺着上次停住的那一点轻轻接一下。"
            if use_chinese
            else "I'll lightly pick up the small open loop we paused on."
        )
    if session_ritual_plan.bridge_move == "repair_before_progress":
        return (
            "先把理解和连接放稳，再看要不要往前。"
            if use_chinese
            else "We can steady the understanding first, then decide whether to move."
        )
    if session_ritual_plan.bridge_move == "single_question_pause":
        return (
            "这一拍只放一个很小的问题口。"
            if use_chinese
            else "This touch only opens one very small question."
        )
    if session_ritual_plan.bridge_move == "ground_then_step":
        return (
            "先把节奏落下来，再看最小的下一步。"
            if use_chinese
            else "We can let the pace settle first, then look at the smallest next step."
        )
    if session_ritual_plan.bridge_move == "reflect_then_step":
        return (
            "我先照一下你现在的位置，再接下一步。"
            if use_chinese
            else "I'll reflect where you are first, then bridge to the next step."
        )
    if session_ritual_plan.bridge_move == "micro_step_bridge":
        return (
            "就先接一个最小、最容易做的动作。"
            if use_chinese
            else "We can bridge back with the smallest, easiest move."
        )
    return ""


def _render_session_ritual_closing_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.closing_move == "progress_invitation":
        return (
            "如果你愿意，我们下一拍就接最小的那一步。"
            if use_chinese
            else "If it helps, we can pick up the smallest next step from here."
        )
    if session_ritual_plan.closing_move == "resume_ping":
        return (
            "下一拍我们就从这条线轻轻接回来。"
            if use_chinese
            else "Next time, we can lightly pick the thread back up from here."
        )
    if session_ritual_plan.closing_move == "repair_soft_close":
        return (
            "这条线先放在这里，不需要你现在立刻接住。"
            if use_chinese
            else "We can leave the thread here without needing you to pick it up right now."
        )
    if session_ritual_plan.closing_move == "clarify_pause":
        return (
            "我们先停在这个问题上，等你愿意再补那一点信息。"
            if use_chinese
            else "We can pause here and wait for that one missing detail when you're ready."
        )
    if session_ritual_plan.closing_move == "grounding_close":
        return (
            "先把身体和节奏稳住就已经算往前了。"
            if use_chinese
            else "Letting your body and pace settle first already counts as forward motion."
        )
    if session_ritual_plan.closing_move == "boundary_safe_close":
        return (
            "你可以自己决定要不要接这一步。"
            if use_chinese
            else "You get to decide whether to pick this step up."
        )
    return ""


def _render_user_space_signal_line(
    *,
    user_space_signal: str,
    use_chinese: bool,
) -> str:
    if user_space_signal == "explicit_no_pressure":
        return (
            "这条线先放着也完全可以，不需要现在接住。"
            if use_chinese
            else "It is completely okay to leave this thread where it is for now."
        )
    if user_space_signal == "archive_light_thread":
        return (
            "我先把这条线轻轻留着，不往你这边推。"
            if use_chinese
            else "I'll leave this thread lightly parked without pushing it toward you."
        )
    if user_space_signal == "open_loop_without_demand":
        return (
            "我只把门轻轻开着，不会要求你现在回应。"
            if use_chinese
            else "I'll just leave the door lightly open without asking you to answer now."
        )
    return ""


def _render_continuity_anchor_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.continuity_anchor == "shared_context_resume":
        return (
            "我们就顺着刚才那条线最容易接上的地方继续。"
            if use_chinese
            else "We can pick this up from the easiest place on the thread we already had."
        )
    if session_ritual_plan.continuity_anchor == "repair_landing":
        return (
            "就先把这条线放在更稳、更好接住的位置。"
            if use_chinese
            else "We can leave the thread in a steadier place that's easier to return to."
        )
    if session_ritual_plan.continuity_anchor == "grounding_first":
        return (
            "先把节奏稳住，本身就算把这条线接住了。"
            if use_chinese
            else "Letting the pace settle first already counts as holding the thread."
        )
    if session_ritual_plan.continuity_anchor == "thread_left_open":
        return (
            "这条线我先替你轻轻留着，不需要现在接。"
            if use_chinese
            else "I'll leave this thread gently open for you without needing anything now."
        )
    return ""


def build_proactive_followup_message(
    *,
    recent_user_text: str,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot | None,
    question_mode: str = "default",
) -> str:
    if not directive.eligible or directive.status != "ready":
        return ""

    style = directive.style or "light_check_in"
    somatic_cue = (
        runtime_coordination_snapshot.somatic_cue
        if runtime_coordination_snapshot is not None
        else None
    )
    if _contains_chinese(recent_user_text):
        if style == "progress_nudge":
            if question_mode == "statement_only":
                return "我来轻轻跟进一下这条线。如果现在有一点推进空间，只做一个最小动作就够。"
            return (
                "我来轻轻跟进一下：上次那一步现在有一点推进空间了吗？"
                "如果还没开始，也只需要先做一个最小动作就够。"
            )
        if style == "grounded_check_in":
            stabilizer = "先放慢一点、把呼吸和节奏稳住" if somatic_cue else "先把节奏放慢一点"
            if question_mode == "statement_only":
                return (
                    f"我来轻轻接一下这条线。"
                    f"如果当下还是很绷，先{stabilizer}也可以，"
                    "然后只做一个最小、最稳的下一步。"
                )
            return (
                f"我来轻轻看看你现在怎么样。"
                f"如果当下还是很绷，先{stabilizer}也可以，"
                "然后只做一个最小、最稳的下一步。"
            )
        if question_mode == "statement_only":
            return (
                "我来做一个低压力的 continuity check-in。"
                "如果你愿意，我们就只接回上次最小、最容易推进的那一步。"
            )
        return (
            "我来做一个低压力的 continuity check-in。"
            "如果你愿意，我们就只接回上次最小、最容易推进的那一步。"
        )

    if style == "progress_nudge":
        if question_mode == "statement_only":
            return (
                "Quick check-in on the step we left open. If there is any room to move "
                "it, one tiny move is enough."
            )
        return (
            "Quick check-in on the step we left open: is there a tiny bit of movement "
            "available now? If not, the smallest next move still counts."
        )
    if style == "grounded_check_in":
        stabilizer = (
            "slow the pace and steady your breathing first"
            if somatic_cue
            else "slow the pace first"
        )
        if question_mode == "statement_only":
            return (
                "Gentle check-in: if things still feel tense, it is okay to "
                f"{stabilizer}, then choose one small, steady next step."
            )
        return (
            "Gentle check-in: if things still feel tense, it's okay to "
            f"{stabilizer}, then choose one small, steady next step."
        )
    if question_mode == "statement_only":
        return (
            "Light continuity check-in: we can reconnect to the smallest next step "
            "without adding pressure."
        )
    return (
        "Light continuity check-in: if you want to pick this back up, we can just "
        "reconnect to the smallest next step without adding pressure."
    )


def _build_reengagement_render_context(
    *,
    recent_user_text: str,
    reengagement_plan: ReengagementPlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    cadence_stage_label: str,
    cadence_stage_index: int,
    cadence_stage_count: int,
    stage_directive: dict[str, object] | None,
    stage_actuation: dict[str, object] | None,
) -> _ReengagementRenderContext:
    use_chinese = _contains_chinese(recent_user_text)
    is_final_touch = (
        cadence_stage_label == "final_soft_close" or cadence_stage_index >= cadence_stage_count
    )
    effective_delivery_mode = str(
        (stage_directive or {}).get("delivery_mode") or reengagement_plan.delivery_mode
    )
    question_mode = str((stage_directive or {}).get("question_mode") or "default")
    allow_somatic_carryover = bool(
        (stage_directive or {}).get(
            "allow_somatic_carryover",
            somatic_orchestration_plan.allow_in_followup,
        )
    )
    effective_session_ritual_plan = SessionRitualPlan(
        phase=session_ritual_plan.phase,
        opening_move=str(
            (stage_actuation or {}).get("opening_move") or session_ritual_plan.opening_move
        ),
        bridge_move=str(
            (stage_actuation or {}).get("bridge_move") or session_ritual_plan.bridge_move
        ),
        closing_move=str(
            (stage_actuation or {}).get("closing_move") or session_ritual_plan.closing_move
        ),
        continuity_anchor=str(
            (stage_actuation or {}).get("continuity_anchor")
            or session_ritual_plan.continuity_anchor
        ),
        somatic_shortcut=(
            session_ritual_plan.somatic_shortcut
            if str((stage_actuation or {}).get("somatic_mode") or "none") != "none"
            else "none"
        ),
        micro_rituals=list(session_ritual_plan.micro_rituals),
        rationale=session_ritual_plan.rationale,
    )
    effective_somatic_mode = str(
        (stage_actuation or {}).get("somatic_mode")
        or (somatic_orchestration_plan.primary_mode if allow_somatic_carryover else "none")
    )
    effective_somatic_orchestration_plan = SomaticOrchestrationPlan(
        status=(
            "active"
            if (
                somatic_orchestration_plan.status == "active"
                and effective_somatic_mode != "none"
                and allow_somatic_carryover
            )
            else "not_needed"
        ),
        cue=somatic_orchestration_plan.cue,
        primary_mode=effective_somatic_mode,
        body_anchor=str(
            (stage_actuation or {}).get("somatic_body_anchor")
            or (somatic_orchestration_plan.body_anchor if allow_somatic_carryover else "none")
        ),
        followup_style=str(
            (stage_actuation or {}).get("followup_style")
            or (somatic_orchestration_plan.followup_style if allow_somatic_carryover else "none")
        ),
        allow_in_followup=allow_somatic_carryover,
        micro_actions=(
            list(somatic_orchestration_plan.micro_actions)
            if allow_somatic_carryover and effective_somatic_mode != "none"
            else []
        ),
        phrasing_guardrails=(
            list(somatic_orchestration_plan.phrasing_guardrails)
            if allow_somatic_carryover and effective_somatic_mode != "none"
            else []
        ),
        rationale=somatic_orchestration_plan.rationale,
    )
    return _ReengagementRenderContext(
        use_chinese=use_chinese,
        is_final_touch=is_final_touch,
        effective_delivery_mode=effective_delivery_mode,
        question_mode=question_mode,
        allow_somatic_carryover=allow_somatic_carryover,
        effective_session_ritual_plan=effective_session_ritual_plan,
        effective_somatic_orchestration_plan=effective_somatic_orchestration_plan,
    )


def _build_reengagement_render_lines(
    *,
    recent_user_text: str,
    directive: ProactiveFollowupDirective,
    reengagement_plan: ReengagementPlan,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot | None,
    stage_directive: dict[str, object] | None,
    stage_actuation: dict[str, object] | None,
    context: _ReengagementRenderContext,
) -> _ReengagementRenderLines:
    autonomy_line = _render_reengagement_autonomy_line(
        reengagement_plan=reengagement_plan,
        use_chinese=context.use_chinese,
    )
    ritual_opening_line = _render_session_ritual_opening_line(
        session_ritual_plan=context.effective_session_ritual_plan,
        use_chinese=context.use_chinese,
    )
    ritual_bridge_line = _render_session_ritual_bridge_line(
        session_ritual_plan=context.effective_session_ritual_plan,
        use_chinese=context.use_chinese,
    )
    ritual_closing_line = _render_session_ritual_closing_line(
        session_ritual_plan=context.effective_session_ritual_plan,
        use_chinese=context.use_chinese,
    )
    user_space_line = _render_user_space_signal_line(
        user_space_signal=str(
            (stage_actuation or {}).get("user_space_signal")
            or (stage_directive or {}).get("autonomy_mode")
            or "none"
        ),
        use_chinese=context.use_chinese,
    )
    continuity_anchor_line = _render_continuity_anchor_line(
        session_ritual_plan=context.effective_session_ritual_plan,
        use_chinese=context.use_chinese,
    )
    somatic_line = _render_reengagement_somatic_line(
        reengagement_plan=reengagement_plan,
        use_chinese=context.use_chinese,
    )
    orchestration_line = _render_somatic_orchestration_line(
        somatic_orchestration_plan=context.effective_somatic_orchestration_plan,
        use_chinese=context.use_chinese,
    )
    base_message = build_proactive_followup_message(
        recent_user_text=recent_user_text,
        directive=directive,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        question_mode=context.question_mode,
    )
    return _ReengagementRenderLines(
        autonomy_line=autonomy_line,
        ritual_opening_line=ritual_opening_line,
        ritual_bridge_line=ritual_bridge_line,
        ritual_closing_line=ritual_closing_line,
        user_space_line=user_space_line,
        continuity_anchor_line=continuity_anchor_line,
        somatic_line=somatic_line,
        orchestration_line=orchestration_line,
        base_message=base_message,
    )


def _build_final_touch_output(
    *,
    use_chinese: bool,
    lines: _ReengagementRenderLines,
) -> list[dict[str, str]]:
    if use_chinese:
        content = (
            f"{lines.ritual_opening_line} 我先把这条线轻轻放在这里。 "
            "如果你之后想接回来，我们就从最小、最容易接上的那一步继续。 "
            f"{lines.ritual_bridge_line} {lines.continuity_anchor_line} {lines.user_space_line} "
            f"{lines.autonomy_line} {lines.ritual_closing_line}"
        ).strip()
    else:
        content = (
            f"{lines.ritual_opening_line} I am going to leave this thread here gently. "
            "If you want to reconnect later, we can restart from the smallest easy step. "
            f"{lines.ritual_bridge_line} {lines.continuity_anchor_line} {lines.user_space_line} "
            f"{lines.autonomy_line} {lines.ritual_closing_line}"
        ).strip()
    return [{"label": "soft_close", "content": content}]


def _build_single_sequence_output(
    *,
    use_chinese: bool,
    cadence_stage_label: str,
    reengagement_plan: ReengagementPlan,
    allow_somatic_carryover: bool,
    lines: _ReengagementRenderLines,
) -> list[dict[str, str]]:
    label = reengagement_plan.segment_labels[0] if reengagement_plan.segment_labels else "check_in"
    stage_prefix = ""
    if cadence_stage_label == "second_touch":
        stage_prefix = (
            "我再轻轻碰一下这条线。" if use_chinese else "One more light touch on the thread."
        )
    content_parts = [part for part in [stage_prefix, lines.base_message] if part]
    if lines.ritual_opening_line and lines.ritual_opening_line not in lines.base_message:
        content_parts.insert(0, lines.ritual_opening_line)
    if lines.ritual_bridge_line and lines.ritual_bridge_line not in lines.base_message:
        content_parts.insert(1 if lines.ritual_opening_line else 0, lines.ritual_bridge_line)
    if lines.somatic_line and lines.somatic_line not in lines.base_message:
        content_parts.append(lines.somatic_line)
    elif (
        lines.orchestration_line
        and allow_somatic_carryover
        and lines.orchestration_line not in lines.base_message
    ):
        content_parts.append(lines.orchestration_line)
    if lines.continuity_anchor_line and lines.continuity_anchor_line not in lines.base_message:
        content_parts.append(lines.continuity_anchor_line)
    if lines.user_space_line and lines.user_space_line not in lines.base_message:
        content_parts.append(lines.user_space_line)
    if lines.autonomy_line and lines.autonomy_line not in lines.base_message:
        content_parts.append(lines.autonomy_line)
    if lines.ritual_closing_line and lines.ritual_closing_line not in lines.base_message:
        content_parts.append(lines.ritual_closing_line)
    return [{"label": label, "content": " ".join(content_parts).strip()}]


def _build_two_part_chinese_output(
    *,
    reengagement_plan: ReengagementPlan,
    cadence_stage_label: str,
    lines: _ReengagementRenderLines,
) -> list[dict[str, str]]:
    if reengagement_plan.strategy_key in {
        "progress_micro_commitment",
        "repair_soft_progress_reentry",
        "resume_progress_bridge",
    }:
        reconnect_line = "我来轻轻接回一下我们上次停下来的那一步。"
        if cadence_stage_label == "second_touch":
            reconnect_line = "我再轻轻碰一下上次停下来的那一步。"
        second_line = "如果你愿意，现在只推进一个最小动作就够。"
        if reengagement_plan.pressure_mode == "repair_soft":
            second_line = "如果现在想接回来，我们就只接一个最小动作；不接也没关系。"
        return [
            {
                "label": "reconnect",
                "content": (
                    (
                        f"{lines.ritual_opening_line} {lines.ritual_bridge_line} {reconnect_line}"
                    ).strip()
                    if reengagement_plan.strategy_key != "resume_progress_bridge"
                    else (
                        f"{lines.ritual_opening_line} {lines.ritual_bridge_line} "
                        "我先把之前停住的那一步轻轻接回来。"
                    ).strip()
                ),
            },
            {
                "label": "next_step",
                "content": (
                    f"{second_line} {lines.continuity_anchor_line} "
                    f"{lines.user_space_line} {lines.autonomy_line} {lines.ritual_closing_line}"
                ).strip(),
            },
        ]
    if reengagement_plan.ritual_mode == "grounding_reentry":
        return [
            {
                "label": "grounding",
                "content": (
                    lines.somatic_line
                    or lines.orchestration_line
                    or "先轻轻确认一下你现在的状态，节奏不需要快。"
                ),
            },
            {
                "label": "steady_step",
                "content": (
                    "如果要继续，我们只接回一个最稳的小下一步就好。 "
                    f"{lines.continuity_anchor_line} {lines.user_space_line} "
                    f"{lines.autonomy_line} {lines.ritual_closing_line}"
                ).strip(),
            },
        ]
    if reengagement_plan.strategy_key in {
        "resume_context_bridge",
        "repair_soft_resume_bridge",
    }:
        reanchor_line = "我先把我们刚才的上下文轻轻接回来。"
        if cadence_stage_label == "second_touch":
            reanchor_line = "我再把这条上下文线轻轻接回来一下。"
        second_line = "如果你想继续，我们就从最容易接上的那一步开始。"
        if reengagement_plan.pressure_mode == "repair_soft":
            second_line = "如果想接回来，我们就从最容易接上的那一步开始，不需要补很多背景。"
        return [
            {
                "label": "re_anchor",
                "content": (
                    f"{lines.ritual_opening_line} {lines.ritual_bridge_line} {reanchor_line}"
                ).strip(),
            },
            {
                "label": "continuity",
                "content": (
                    f"{second_line} {lines.continuity_anchor_line} "
                    f"{lines.user_space_line} {lines.autonomy_line} {lines.ritual_closing_line}"
                ).strip(),
            },
        ]
    return [
        {
            "label": "re_anchor",
            "content": (
                f"{lines.ritual_opening_line} {lines.ritual_bridge_line} "
                "我来把我们刚才的上下文轻轻接回来。"
            ).strip(),
        },
        {
            "label": "continuity",
            "content": (
                "如果你愿意，我们只继续最小、最容易接上的那一步。 "
                f"{lines.continuity_anchor_line} {lines.user_space_line} "
                f"{lines.autonomy_line} {lines.ritual_closing_line}"
            ).strip(),
        },
    ]


def _build_two_part_english_output(
    *,
    reengagement_plan: ReengagementPlan,
    cadence_stage_label: str,
    lines: _ReengagementRenderLines,
) -> list[dict[str, str]]:
    if reengagement_plan.strategy_key in {
        "progress_micro_commitment",
        "repair_soft_progress_reentry",
        "resume_progress_bridge",
    }:
        reconnect_line = "Quick re-anchor to the step we left open."
        if cadence_stage_label == "second_touch":
            reconnect_line = "One more gentle bridge back to the step we left open."
        second_line = "If you want to pick it back up now, one tiny move is enough."
        if reengagement_plan.pressure_mode == "repair_soft":
            second_line = (
                "If it helps, we can restart with one tiny move, and it is okay to "
                "leave it parked for now."
            )
        return [
            {
                "label": "reconnect",
                "content": (
                    (
                        f"{lines.ritual_opening_line} {lines.ritual_bridge_line} {reconnect_line}"
                    ).strip()
                    if reengagement_plan.strategy_key != "resume_progress_bridge"
                    else (
                        f"{lines.ritual_opening_line} {lines.ritual_bridge_line} "
                        "Quick bridge back to the step we parked earlier."
                    ).strip()
                ),
            },
            {
                "label": "next_step",
                "content": (
                    f"{second_line} {lines.continuity_anchor_line} "
                    f"{lines.user_space_line} {lines.autonomy_line} {lines.ritual_closing_line}"
                ).strip(),
            },
        ]
    if reengagement_plan.ritual_mode == "grounding_reentry":
        return [
            {
                "label": "grounding",
                "content": (
                    lines.somatic_line
                    or lines.orchestration_line
                    or "Gentle check-in first: the pace does not need to be fast."
                ),
            },
            {
                "label": "steady_step",
                "content": (
                    "If you want to continue, we can reconnect to one steady next step. "
                    f"{lines.continuity_anchor_line} {lines.user_space_line} "
                    f"{lines.autonomy_line} {lines.ritual_closing_line}"
                ).strip(),
            },
        ]
    if reengagement_plan.strategy_key in {
        "resume_context_bridge",
        "repair_soft_resume_bridge",
    }:
        reanchor_line = "Quick bridge back to the thread we left open."
        if cadence_stage_label == "second_touch":
            reanchor_line = "One more light bridge back to the thread we left open."
        second_line = "If you want to resume, we can pick up the easiest next step from here."
        if reengagement_plan.pressure_mode == "repair_soft":
            second_line = (
                "If it helps, we can restart from the easiest safe point without "
                "re-explaining everything."
            )
        return [
            {
                "label": "re_anchor",
                "content": (
                    f"{lines.ritual_opening_line} {lines.ritual_bridge_line} {reanchor_line}"
                ).strip(),
            },
            {
                "label": "continuity",
                "content": (
                    f"{second_line} {lines.continuity_anchor_line} "
                    f"{lines.user_space_line} {lines.autonomy_line} {lines.ritual_closing_line}"
                ).strip(),
            },
        ]
    return [
        {
            "label": "re_anchor",
            "content": (
                f"{lines.ritual_opening_line} {lines.ritual_bridge_line} "
                "Quick continuity check-in to reconnect the thread."
            ).strip(),
        },
        {
            "label": "continuity",
            "content": (
                "If you want to resume, we can pick up the smallest next step "
                f"without pressure. {lines.continuity_anchor_line} "
                f"{lines.user_space_line} {lines.autonomy_line} {lines.ritual_closing_line}"
            ),
        },
    ]


def _resolve_actuation_source(reengagement_plan: ReengagementPlan) -> str:
    """Determine whether actuation came from governance override, learning, or default."""
    governance_indicators = {
        "repair_soft",
        "archive_light_presence",
        "archive_light_thread",
    }
    if reengagement_plan.pressure_mode in governance_indicators:
        return "governance_override"
    if reengagement_plan.tone == "repair_aware":
        return "governance_override"
    return "default"


def build_reengagement_output_units(
    *,
    recent_user_text: str,
    directive: ProactiveFollowupDirective,
    reengagement_plan: ReengagementPlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot | None,
    cadence_stage_label: str = "first_touch",
    cadence_stage_index: int = 1,
    cadence_stage_count: int = 1,
    stage_directive: dict[str, object] | None = None,
    stage_actuation: dict[str, object] | None = None,
) -> list[dict[str, str]]:
    if reengagement_plan.status != "ready" or not directive.eligible:
        return []

    context = _build_reengagement_render_context(
        recent_user_text=recent_user_text,
        reengagement_plan=reengagement_plan,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
        cadence_stage_label=cadence_stage_label,
        cadence_stage_index=cadence_stage_index,
        cadence_stage_count=cadence_stage_count,
        stage_directive=stage_directive,
        stage_actuation=stage_actuation,
    )
    lines = _build_reengagement_render_lines(
        recent_user_text=recent_user_text,
        directive=directive,
        reengagement_plan=reengagement_plan,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        stage_directive=stage_directive,
        stage_actuation=stage_actuation,
        context=context,
    )
    if not lines.base_message:
        return []

    actuation_source = _resolve_actuation_source(reengagement_plan)

    if context.is_final_touch:
        units = _build_final_touch_output(
            use_chinese=context.use_chinese,
            lines=lines,
        )
    elif context.effective_delivery_mode != "two_part_sequence":
        units = _build_single_sequence_output(
            use_chinese=context.use_chinese,
            cadence_stage_label=cadence_stage_label,
            reengagement_plan=reengagement_plan,
            allow_somatic_carryover=context.allow_somatic_carryover,
            lines=lines,
        )
    elif context.use_chinese:
        units = _build_two_part_chinese_output(
            reengagement_plan=reengagement_plan,
            cadence_stage_label=cadence_stage_label,
            lines=lines,
        )
    else:
        units = _build_two_part_english_output(
            reengagement_plan=reengagement_plan,
            cadence_stage_label=cadence_stage_label,
            lines=lines,
        )

    for unit in units:
        unit["actuation_source"] = actuation_source
    return units
