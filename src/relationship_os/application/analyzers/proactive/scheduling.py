"""Proactive scheduling, orchestration, actuation, progression, guardrail."""

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ConversationCadencePlan,
    GuidancePlan,
    ProactiveActuationPlan,
    ProactiveCadencePlan,
    ProactiveFollowupDirective,
    ProactiveGuardrailPlan,
    ProactiveOrchestrationPlan,
    ProactiveProgressionPlan,
    ProactiveSchedulingPlan,
    ProactiveStageActuation,
    ProactiveStageDirective,
    ProactiveStageGuardrail,
    ProactiveStageProgressionDirective,
    ReengagementMatrixAssessment,
    ReengagementPlan,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


def build_proactive_scheduling_plan(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    proactive_cadence_plan: ProactiveCadencePlan,
) -> ProactiveSchedulingPlan:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveSchedulingPlan(
            status="hold",
            scheduler_mode="hold",
            min_seconds_since_last_outbound=0,
            rationale=directive.rationale,
        )

    min_seconds_since_last_outbound = max(0, directive.trigger_after_seconds)
    scheduler_mode = "baseline_spacing"
    stage_spacing_mode = "single_touch"
    low_pressure_guard = "steady_guard"
    scheduling_notes = [
        "respect_recent_outbound_spacing",
        f"directive_style:{directive.style}",
    ]

    if directive.style == "progress_nudge":
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            45 * 60,
        )
        scheduler_mode = "progress_spacing"
    elif directive.style == "grounded_check_in":
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            30 * 60,
        )
        scheduler_mode = "grounding_spacing"
    else:
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            90 * 60,
        )
        scheduler_mode = "light_presence_spacing"

    if cadence_plan.user_space_mode in {
        "spacious",
        "explicit_autonomy_space",
        "consent_space",
    }:
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            4 * 3600,
        )
        scheduler_mode = "spacious_user_window"
        low_pressure_guard = "spacious_user_space"
        scheduling_notes.append("preserve_explicit_user_space")
    elif cadence_plan.user_space_mode == "balanced_space":
        low_pressure_guard = "balanced_user_space"

    if guidance_plan.handoff_mode in {
        "no_pressure_checkin",
        "repair_soft_ping",
        "autonomy_preserving_ping",
    }:
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            3 * 3600,
        )
        scheduler_mode = "no_pressure_cooldown"
        scheduling_notes.append(f"handoff:{guidance_plan.handoff_mode}")

    if session_ritual_plan.closing_move in {
        "repair_soft_close",
        "grounding_close",
        "boundary_safe_close",
    }:
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            2 * 3600,
        )
        scheduling_notes.append(f"closing:{session_ritual_plan.closing_move}")

    if somatic_orchestration_plan.status == "active":
        min_seconds_since_last_outbound = max(
            min_seconds_since_last_outbound,
            30 * 60,
        )
        scheduling_notes.append(
            f"somatic_followup:{somatic_orchestration_plan.followup_style}"
        )

    if proactive_cadence_plan.close_after_stage_index > 1:
        stage_spacing_mode = "multi_touch_low_pressure"
        scheduling_notes.append(
            f"cadence:{proactive_cadence_plan.cadence_key}"
        )

    first_touch_extra_delay_seconds = max(
        0,
        min_seconds_since_last_outbound - directive.trigger_after_seconds,
    )
    rationale = (
        "The proactive line should respect user space by adding a visible outbound "
        "cooldown before the first touch becomes dispatchable."
    )
    if first_touch_extra_delay_seconds == 0:
        rationale = (
            "The proactive line can use its normal trigger timing because the current "
            "guidance and cadence do not require extra cooldown."
        )

    return ProactiveSchedulingPlan(
        status="active",
        scheduler_mode=scheduler_mode,
        min_seconds_since_last_outbound=min_seconds_since_last_outbound,
        first_touch_extra_delay_seconds=first_touch_extra_delay_seconds,
        stage_spacing_mode=stage_spacing_mode,
        low_pressure_guard=low_pressure_guard,
        scheduling_notes=_compact(scheduling_notes, limit=5),
        rationale=rationale,
    )


def build_proactive_orchestration_plan(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    proactive_scheduling_plan: ProactiveSchedulingPlan,
    reengagement_plan: ReengagementPlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
) -> ProactiveOrchestrationPlan:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveOrchestrationPlan(
            status="hold",
            orchestration_key="hold",
            close_loop_stage="none",
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or ["first_touch"])
    stage_directives: list[ProactiveStageDirective] = []
    orchestration_key = f"{proactive_cadence_plan.cadence_key}_orchestrated"
    close_loop_stage = stage_labels[-1]

    for index, stage_label in enumerate(stage_labels, start=1):
        is_first_touch = index == 1
        is_final_touch = stage_label == close_loop_stage
        is_second_touch = stage_label == "second_touch"

        objective = reengagement_plan.sequence_objective or "presence_then_optional_reply"
        delivery_mode = reengagement_plan.delivery_mode
        question_mode = "optional_question"
        autonomy_mode = reengagement_plan.autonomy_signal or "open_loop_without_demand"
        closing_style = "keep_thread_open"
        allow_somatic_carryover = bool(
            somatic_orchestration_plan.allow_in_followup
            and somatic_orchestration_plan.status == "active"
        )
        rationale = reengagement_plan.rationale or directive.rationale

        if is_first_touch:
            objective = reengagement_plan.sequence_objective or "initial_reconnect"
            question_mode = "optional_question"
            closing_style = "invite_reentry"
            if proactive_scheduling_plan.first_touch_extra_delay_seconds > 0:
                rationale = (
                    "The first touch stays gentle because scheduling already inserted "
                    "an outbound cooldown."
                )
        elif is_second_touch:
            objective = "restage_low_pressure_reconnect"
            delivery_mode = (
                "two_part_sequence"
                if reengagement_plan.ritual_mode == "grounding_reentry"
                and somatic_orchestration_plan.status == "active"
                else "single_message"
            )
            question_mode = "statement_only"
            autonomy_mode = "explicit_no_pressure"
            closing_style = "steady_reopen"
            allow_somatic_carryover = allow_somatic_carryover and (
                reengagement_plan.ritual_mode == "grounding_reentry"
            )
            rationale = (
                "The second touch should lower pressure further by compressing the "
                "message shape unless grounding still needs a two-part re-entry."
            )
        if is_final_touch:
            objective = "soft_close_loop"
            delivery_mode = "single_message"
            question_mode = "statement_only"
            autonomy_mode = "archive_light_thread"
            closing_style = "soft_close"
            allow_somatic_carryover = False
            rationale = (
                "The final touch should stop escalating the line and leave the thread "
                "open without demanding a reply."
            )

        if session_ritual_plan.closing_move in {"repair_soft_close", "boundary_safe_close"}:
            autonomy_mode = "explicit_no_pressure"
        if somatic_orchestration_plan.status != "active":
            allow_somatic_carryover = False

        stage_directives.append(
            ProactiveStageDirective(
                stage_label=stage_label,
                objective=objective,
                delivery_mode=delivery_mode,
                question_mode=question_mode,
                autonomy_mode=autonomy_mode,
                closing_style=closing_style,
                allow_somatic_carryover=allow_somatic_carryover,
                rationale=rationale,
            )
        )

    return ProactiveOrchestrationPlan(
        status="active",
        orchestration_key=orchestration_key,
        close_loop_stage=close_loop_stage,
        stage_directives=stage_directives,
        rationale=directive.rationale,
    )


def build_proactive_actuation_plan(
    *,
    directive: ProactiveFollowupDirective,
    proactive_orchestration_plan: ProactiveOrchestrationPlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
) -> ProactiveActuationPlan:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveActuationPlan(
            status="hold",
            actuation_key="hold",
            rationale=directive.rationale,
        )

    stage_actuations: list[ProactiveStageActuation] = []
    actuation_key = (
        f"{proactive_orchestration_plan.orchestration_key}_actuated"
        if proactive_orchestration_plan.orchestration_key
        else "default_actuation"
    )

    for stage_directive in proactive_orchestration_plan.stage_directives:
        opening_move = session_ritual_plan.opening_move
        bridge_move = session_ritual_plan.bridge_move
        closing_move = session_ritual_plan.closing_move
        continuity_anchor = session_ritual_plan.continuity_anchor
        somatic_mode = (
            somatic_orchestration_plan.primary_mode
            if (
                somatic_orchestration_plan.status == "active"
                and stage_directive.allow_somatic_carryover
            )
            else "none"
        )
        somatic_body_anchor = (
            somatic_orchestration_plan.body_anchor if somatic_mode != "none" else "none"
        )
        followup_style = (
            somatic_orchestration_plan.followup_style
            if somatic_mode != "none"
            else "none"
        )
        user_space_signal = stage_directive.autonomy_mode
        rationale = stage_directive.rationale or directive.rationale

        if stage_directive.stage_label == "first_touch":
            if stage_directive.objective == "initial_reconnect":
                continuity_anchor = "shared_context_resume"
            if stage_directive.delivery_mode == "two_part_sequence":
                bridge_move = "resume_the_open_loop"
        elif stage_directive.stage_label == "second_touch":
            opening_move = (
                "attunement_repair"
                if session_ritual_plan.closing_move == "repair_soft_close"
                else "shared_context_bridge"
            )
            bridge_move = "micro_step_bridge"
            closing_move = (
                "boundary_safe_close"
                if stage_directive.autonomy_mode == "explicit_no_pressure"
                else "light_handoff"
            )
            continuity_anchor = (
                "repair_landing"
                if session_ritual_plan.closing_move == "repair_soft_close"
                else "shared_context_resume"
            )
            if not stage_directive.allow_somatic_carryover:
                somatic_mode = "none"
                somatic_body_anchor = "none"
                followup_style = "none"
        elif stage_directive.stage_label == proactive_orchestration_plan.close_loop_stage:
            opening_move = (
                "attunement_repair"
                if session_ritual_plan.closing_move == "repair_soft_close"
                else "shared_context_bridge"
            )
            bridge_move = "reflect_then_step"
            closing_move = (
                "repair_soft_close"
                if session_ritual_plan.closing_move == "repair_soft_close"
                else "boundary_safe_close"
            )
            continuity_anchor = "thread_left_open"
            somatic_mode = "none"
            somatic_body_anchor = "none"
            followup_style = "none"

        stage_actuations.append(
            ProactiveStageActuation(
                stage_label=stage_directive.stage_label,
                opening_move=opening_move,
                bridge_move=bridge_move,
                closing_move=closing_move,
                continuity_anchor=continuity_anchor,
                somatic_mode=somatic_mode,
                somatic_body_anchor=somatic_body_anchor,
                followup_style=followup_style,
                user_space_signal=user_space_signal,
                rationale=rationale,
            )
        )

    return ProactiveActuationPlan(
        status="active",
        actuation_key=actuation_key,
        stage_actuations=stage_actuations,
        rationale=directive.rationale,
    )


def build_proactive_progression_plan(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    proactive_scheduling_plan: ProactiveSchedulingPlan,
    proactive_orchestration_plan: ProactiveOrchestrationPlan,
) -> ProactiveProgressionPlan:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveProgressionPlan(
            status="hold",
            progression_key="hold",
            close_loop_stage="none",
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or ["first_touch"])
    stage_intervals = list(proactive_cadence_plan.stage_intervals_seconds or [0])
    close_loop_stage = (
        proactive_orchestration_plan.close_loop_stage
        if proactive_orchestration_plan.close_loop_stage
        else stage_labels[-1]
    )
    progression_key = f"{proactive_cadence_plan.cadence_key}_progressive"
    stage_progressions: list[ProactiveStageProgressionDirective] = []
    extra_delay = max(
        0,
        int(proactive_scheduling_plan.first_touch_extra_delay_seconds or 0),
    )

    for index, stage_label in enumerate(stage_labels):
        stage_interval = (
            stage_intervals[min(index, len(stage_intervals) - 1)] if stage_intervals else 0
        )
        max_overdue_seconds = max(stage_interval, 4 * 3600)
        on_expired = "advance_to_next_stage"
        rationale = "If this stage goes stale, advance the line instead of nagging in place."

        if stage_label == "first_touch":
            max_overdue_seconds = max(
                stage_interval + extra_delay,
                4 * 3600,
            )
            if directive.style == "grounded_check_in":
                max_overdue_seconds = max(max_overdue_seconds, 6 * 3600)
        elif stage_label == "second_touch":
            max_overdue_seconds = max(stage_interval, 8 * 3600)
            on_expired = "jump_to_close_loop"
            rationale = (
                "If the second touch also goes stale, skip forward to a gentle close loop."
            )

        if stage_label == close_loop_stage:
            max_overdue_seconds = max(stage_interval, 12 * 3600)
            on_expired = "close_line"
            rationale = (
                "If the final soft close goes stale too, retire the line "
                "instead of keeping it overdue."
            )

        stage_progressions.append(
            ProactiveStageProgressionDirective(
                stage_label=stage_label,
                max_overdue_seconds=max_overdue_seconds,
                on_expired=on_expired,
                rationale=rationale,
            )
        )

    return ProactiveProgressionPlan(
        status="active",
        progression_key=progression_key,
        close_loop_stage=close_loop_stage,
        stage_progressions=stage_progressions,
        rationale=directive.rationale,
    )


def build_proactive_guardrail_plan(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    system3_snapshot: System3Snapshot,
    proactive_cadence_plan: ProactiveCadencePlan,
    reengagement_matrix_assessment: ReengagementMatrixAssessment | None = None,
) -> ProactiveGuardrailPlan:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveGuardrailPlan(
            status="hold",
            guardrail_key="hold",
            max_dispatch_count=0,
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or ["first_touch"])
    stage_intervals = list(proactive_cadence_plan.stage_intervals_seconds or [0])
    max_dispatch_count = max(
        1,
        int(
            proactive_cadence_plan.close_after_stage_index
            or len(stage_labels)
            or 1
        ),
    )
    hard_stop_conditions: list[str] = []
    guidance_low_pressure = guidance_plan.handoff_mode in {
        "no_pressure_checkin",
        "repair_soft_ping",
        "autonomy_preserving_ping",
    }
    selected_strategy_key = (
        reengagement_matrix_assessment.selected_strategy_key
        if reengagement_matrix_assessment is not None
        else ""
    )

    if system3_snapshot.strategy_audit_status == "revise":
        max_dispatch_count = 1
        hard_stop_conditions.append("strategy_audit_revise")
    elif system3_snapshot.emotional_debt_status == "elevated":
        max_dispatch_count = min(max_dispatch_count, 2)
        hard_stop_conditions.append("emotional_debt_elevated")

    if guidance_plan.mode in {"boundary_guidance", "repair_guidance"}:
        max_dispatch_count = min(max_dispatch_count, 2)
        hard_stop_conditions.append(f"guidance:{guidance_plan.mode}")
    if guidance_low_pressure:
        hard_stop_conditions.append(f"handoff:{guidance_plan.handoff_mode}")
    if session_ritual_plan.closing_move in {"repair_soft_close", "boundary_safe_close"}:
        hard_stop_conditions.append(f"closing:{session_ritual_plan.closing_move}")
    if selected_strategy_key.startswith("repair_soft"):
        hard_stop_conditions.append(f"strategy:{selected_strategy_key}")

    stage_guardrails: list[ProactiveStageGuardrail] = []
    for index, stage_label in enumerate(stage_labels, start=1):
        stage_interval = stage_intervals[min(index - 1, len(stage_intervals) - 1)]
        min_seconds_since_last_user = 0
        min_seconds_since_last_dispatch = 0
        on_guardrail_hit = "defer"
        rationale = (
            "Each proactive stage should leave enough user space to keep the line "
            "low-pressure instead of piling touches too tightly."
        )

        if stage_label == "second_touch":
            min_seconds_since_last_user = 4 * 3600
            min_seconds_since_last_dispatch = max(stage_interval, 3 * 3600)
            on_guardrail_hit = "defer"
        elif stage_label == "final_soft_close":
            min_seconds_since_last_user = 8 * 3600
            min_seconds_since_last_dispatch = max(stage_interval, 6 * 3600)
            on_guardrail_hit = "close_line"

        if guidance_low_pressure or cadence_plan.user_space_mode in {
            "spacious",
            "explicit_autonomy_space",
            "consent_space",
        }:
            min_seconds_since_last_user = max(min_seconds_since_last_user, 6 * 3600)
        if system3_snapshot.emotional_debt_status in {"watch", "elevated"}:
            min_seconds_since_last_user = max(min_seconds_since_last_user, 8 * 3600)
        if selected_strategy_key.startswith("repair_soft") and index > 1:
            min_seconds_since_last_user = max(min_seconds_since_last_user, 10 * 3600)
            min_seconds_since_last_dispatch = max(
                min_seconds_since_last_dispatch,
                6 * 3600,
            )
        if stage_label == "final_soft_close" and guidance_plan.mode == "reanchor_guidance":
            min_seconds_since_last_dispatch = max(
                min_seconds_since_last_dispatch,
                8 * 3600,
            )

        stage_guardrails.append(
            ProactiveStageGuardrail(
                stage_label=stage_label,
                min_seconds_since_last_user=min_seconds_since_last_user,
                min_seconds_since_last_dispatch=min_seconds_since_last_dispatch,
                on_guardrail_hit=on_guardrail_hit,
                rationale=rationale,
            )
        )

    guardrail_key = f"{proactive_cadence_plan.cadence_key}_guarded"
    if max_dispatch_count == 1:
        guardrail_key = f"{guardrail_key}_single_touch"
    elif max_dispatch_count == 2:
        guardrail_key = f"{guardrail_key}_capped_two_touch"

    rationale = (
        "The proactive line should honor explicit user space guardrails before any "
        "stage becomes dispatchable."
    )
    if not hard_stop_conditions:
        rationale = (
            "The proactive line can keep its full staged cadence, but each stage still "
            "inherits explicit user-space spacing rules."
        )

    return ProactiveGuardrailPlan(
        status="active",
        guardrail_key=guardrail_key,
        max_dispatch_count=max_dispatch_count,
        stage_guardrails=stage_guardrails,
        hard_stop_conditions=_compact(hard_stop_conditions, limit=5),
        rationale=rationale,
    )
