"""Proactive dispatch: planning, assessment, and governance gate helpers."""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.governance import (
    _PROACTIVE_GOVERNANCE_DOMAINS,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateGovernanceAssessment,
    ProactiveDispatchFeedbackAssessment,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageRefreshPlan,
    ProactiveStageReplanAssessment,
    ReengagementPlan,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


def build_proactive_stage_refresh_plan(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    system3_snapshot: System3Snapshot,
    stage_label: str,
    queue_status: str,
    schedule_reason: str | None,
    progression_advanced: bool,
    stage_directive: dict[str, Any] | None,
    stage_actuation: dict[str, Any] | None,
    prior_stage_controller_decision: ProactiveStageControllerDecision | None = None,
    prior_line_controller_decision: ProactiveLineControllerDecision | None = None,
) -> ProactiveStageRefreshPlan:
    """Build a refresh plan for the current proactive stage right before dispatch."""
    if directive.status != "ready" or not directive.eligible:
        return ProactiveStageRefreshPlan(
            status="hold",
            refresh_key="hold",
            stage_label=stage_label or "unknown",
            dispatch_window_status="hold",
            changed=False,
            refreshed_delivery_mode="none",
            refreshed_question_mode="default",
            refreshed_autonomy_mode="none",
            refreshed_opening_move="none",
            refreshed_bridge_move="none",
            refreshed_closing_move="none",
            refreshed_continuity_anchor="none",
            refreshed_somatic_mode="none",
            refreshed_user_space_signal="none",
            rationale=directive.rationale,
        )

    refreshed_delivery_mode = str((stage_directive or {}).get("delivery_mode") or "single_message")
    refreshed_question_mode = str((stage_directive or {}).get("question_mode") or "default")
    refreshed_autonomy_mode = str((stage_directive or {}).get("autonomy_mode") or "none")
    refreshed_opening_move = str((stage_actuation or {}).get("opening_move") or "soft_open")
    refreshed_bridge_move = str(
        (stage_actuation or {}).get("bridge_move") or "resume_the_open_loop"
    )
    refreshed_closing_move = str((stage_actuation or {}).get("closing_move") or "light_handoff")
    refreshed_continuity_anchor = str(
        (stage_actuation or {}).get("continuity_anchor") or "shared_context_resume"
    )
    refreshed_somatic_mode = str((stage_actuation or {}).get("somatic_mode") or "none")
    refreshed_user_space_signal = str(
        (stage_actuation or {}).get("user_space_signal") or refreshed_autonomy_mode or "none"
    )
    refresh_notes: list[str] = []

    dispatch_window_status = "on_time_dispatch"
    if queue_status == "overdue":
        dispatch_window_status = "overdue_dispatch"
        refresh_notes.append("overdue_window")
    elif progression_advanced:
        dispatch_window_status = "progressed_dispatch"
        refresh_notes.append("progression_advanced")
    elif schedule_reason and "guardrail:" in schedule_reason:
        dispatch_window_status = "guarded_release"
        refresh_notes.append("guardrail_release")

    low_pressure_refresh = (
        guidance_plan.mode in {"repair_guidance", "boundary_guidance"}
        or guidance_plan.handoff_mode
        in {"repair_soft_ping", "no_pressure_checkin", "autonomy_preserving_ping"}
        or system3_snapshot.strategy_audit_status in {"watch", "revise"}
        or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
    )
    controller_applies = bool(
        prior_stage_controller_decision is not None
        and prior_stage_controller_decision.status == "active"
        and prior_stage_controller_decision.changed
        and prior_stage_controller_decision.decision == "slow_next_stage"
        and prior_stage_controller_decision.target_stage_label == stage_label
    )
    line_controller_applies = bool(
        prior_line_controller_decision is not None
        and prior_line_controller_decision.status == "active"
        and prior_line_controller_decision.changed
        and prior_line_controller_decision.decision
        in {"soften_remaining_line", "retire_after_close_loop"}
        and stage_label in prior_line_controller_decision.affected_stage_labels
    )

    if stage_label == "second_touch":
        if dispatch_window_status == "on_time_dispatch":
            dispatch_window_status = "second_touch_refresh"
        refreshed_question_mode = "statement_only"
        refreshed_autonomy_mode = "explicit_no_pressure"
        refreshed_user_space_signal = "explicit_no_pressure"
        refreshed_opening_move = "shared_context_bridge"
        refreshed_bridge_move = "reflect_then_step"
        refresh_notes.append("softened_second_touch_bridge")
        refreshed_closing_move = "boundary_safe_close"
        refreshed_continuity_anchor = "shared_context_resume"
        if low_pressure_refresh:
            refreshed_delivery_mode = "single_message"
            refreshed_somatic_mode = "none"
            refresh_notes.append("second_touch_low_pressure")
    elif stage_label == "final_soft_close":
        refreshed_delivery_mode = "single_message"
        refreshed_question_mode = "statement_only"
        refreshed_autonomy_mode = "explicit_no_pressure"
        refreshed_opening_move = "shared_context_bridge"
        refreshed_bridge_move = "reflect_then_step"
        if refreshed_closing_move != "repair_soft_close":
            refreshed_closing_move = "boundary_safe_close"
        refreshed_continuity_anchor = "thread_left_open"
        refreshed_somatic_mode = "none"
        refreshed_user_space_signal = "archive_light_thread"
        refresh_notes.append("final_soft_close_refresh")
    elif low_pressure_refresh:
        refreshed_question_mode = "statement_only"
        refreshed_autonomy_mode = "explicit_no_pressure"
        refreshed_user_space_signal = "explicit_no_pressure"
        refreshed_somatic_mode = "none"
        refresh_notes.append("dispatch_softened_for_safety")

    if controller_applies:
        refreshed_delivery_mode = (
            prior_stage_controller_decision.selected_delivery_mode or refreshed_delivery_mode
        )
        if prior_stage_controller_decision.selected_autonomy_signal in {"explicit_no_pressure"}:
            refreshed_autonomy_mode = prior_stage_controller_decision.selected_autonomy_signal
        refreshed_user_space_signal = (
            prior_stage_controller_decision.selected_autonomy_signal or refreshed_user_space_signal
        )
        if stage_label in {"second_touch", "final_soft_close"}:
            refreshed_bridge_move = "shared_context_bridge"
        refresh_notes.append(f"stage_controller:{prior_stage_controller_decision.controller_key}")

    if line_controller_applies:
        refreshed_delivery_mode = (
            prior_line_controller_decision.selected_delivery_mode or refreshed_delivery_mode
        )
        if (
            stage_label == "second_touch"
            and prior_line_controller_decision.selected_autonomy_signal
            in {"explicit_no_pressure", "archive_light_thread"}
        ):
            refreshed_autonomy_mode = prior_line_controller_decision.selected_autonomy_signal
            refreshed_user_space_signal = prior_line_controller_decision.selected_autonomy_signal
        elif (
            stage_label == "final_soft_close"
            and prior_line_controller_decision.line_state == "close_ready"
        ):
            refreshed_autonomy_mode = "archive_light_thread"
            refreshed_user_space_signal = "archive_light_thread"
        if stage_label in {"second_touch", "final_soft_close"}:
            refreshed_bridge_move = "shared_context_bridge"
        refresh_notes.append(f"line_controller:{prior_line_controller_decision.controller_key}")

    if progression_advanced and stage_label == "final_soft_close":
        refreshed_user_space_signal = "archive_light_thread"
        refresh_notes.append("close_loop_after_progression")

    changed = any(
        [
            refreshed_delivery_mode
            != str((stage_directive or {}).get("delivery_mode") or "single_message"),
            refreshed_question_mode
            != str((stage_directive or {}).get("question_mode") or "default"),
            refreshed_autonomy_mode != str((stage_directive or {}).get("autonomy_mode") or "none"),
            refreshed_opening_move
            != str((stage_actuation or {}).get("opening_move") or "soft_open"),
            refreshed_bridge_move
            != str((stage_actuation or {}).get("bridge_move") or "resume_the_open_loop"),
            refreshed_closing_move
            != str((stage_actuation or {}).get("closing_move") or "light_handoff"),
            refreshed_continuity_anchor
            != str((stage_actuation or {}).get("continuity_anchor") or "shared_context_resume"),
            refreshed_somatic_mode != str((stage_actuation or {}).get("somatic_mode") or "none"),
            refreshed_user_space_signal
            != str(
                (stage_actuation or {}).get("user_space_signal")
                or str((stage_directive or {}).get("autonomy_mode") or "none")
                or "none"
            ),
        ]
    )

    refresh_key = (
        dispatch_window_status
        if dispatch_window_status.startswith(stage_label)
        else f"{stage_label}_{dispatch_window_status}"
    )
    if not changed:
        refresh_key = f"{refresh_key}_stable"

    rationale = (
        "The current proactive stage is being refreshed right before dispatch so the "
        "message shape matches the latest user-space and progression context."
    )
    if not refresh_notes:
        rationale = (
            "The current proactive stage can be dispatched without reshaping because "
            "the planned cadence still fits the latest context."
        )

    return ProactiveStageRefreshPlan(
        status="active",
        refresh_key=refresh_key,
        stage_label=stage_label,
        dispatch_window_status=dispatch_window_status,
        changed=changed,
        refreshed_delivery_mode=refreshed_delivery_mode,
        refreshed_question_mode=refreshed_question_mode,
        refreshed_autonomy_mode=refreshed_autonomy_mode,
        refreshed_opening_move=refreshed_opening_move,
        refreshed_bridge_move=refreshed_bridge_move,
        refreshed_closing_move=refreshed_closing_move,
        refreshed_continuity_anchor=refreshed_continuity_anchor,
        refreshed_somatic_mode=refreshed_somatic_mode,
        refreshed_user_space_signal=refreshed_user_space_signal,
        refresh_notes=_compact(refresh_notes, limit=5),
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Private gate helpers
# ---------------------------------------------------------------------------


def _build_proactive_aggregate_governance_gate(
    system3_snapshot: System3Snapshot,
) -> dict[str, Any]:
    """Build aggregate governance gate from system3 snapshot."""
    recenter_domains: list[str] = []
    watch_domains: list[str] = []
    for domain in _PROACTIVE_GOVERNANCE_DOMAINS:
        status = str(getattr(system3_snapshot, f"{domain}_governance_status", "pass"))
        trajectory_status = str(
            getattr(
                system3_snapshot,
                f"{domain}_governance_trajectory_status",
                "stable",
            )
        )
        if status == "revise" or trajectory_status == "recenter":
            recenter_domains.append(domain)
        elif status == "watch" or trajectory_status == "watch":
            watch_domains.append(domain)

    active_domains = recenter_domains + watch_domains
    if len(active_domains) < 2:
        return {
            "status": "clear",
            "primary_domain": None,
            "active_domains": [],
            "summary": "clear",
            "domain_count": len(active_domains),
        }

    if recenter_domains:
        status = "recenter"
        primary_domain = recenter_domains[0]
    else:
        status = "watch"
        primary_domain = watch_domains[0]

    return {
        "status": status,
        "primary_domain": primary_domain,
        "active_domains": active_domains,
        "summary": "+".join(active_domains[:3]),
        "domain_count": len(active_domains),
    }


def _build_proactive_guidance_gate(
    guidance_plan: GuidancePlan | None,
) -> dict[str, Any]:
    """Build guidance gate from guidance plan."""
    if guidance_plan is None:
        return {
            "status": "clear",
            "primary_signal": None,
            "active_signals": [],
            "summary": "clear",
            "signal_count": 0,
        }

    recenter_signals: list[str] = []
    watch_signals: list[str] = []

    if guidance_plan.mode in {
        "repair_guidance",
        "boundary_guidance",
        "stabilizing_guidance",
        "clarifying_guidance",
    }:
        recenter_signals.append(f"mode:{guidance_plan.mode}")
    elif guidance_plan.mode in {"reanchor_guidance", "reflective_guidance"}:
        watch_signals.append(f"mode:{guidance_plan.mode}")

    if guidance_plan.handoff_mode in {
        "repair_soft_ping",
        "no_pressure_checkin",
        "autonomy_preserving_ping",
        "wait_for_reply",
    }:
        recenter_signals.append(f"handoff:{guidance_plan.handoff_mode}")
    elif guidance_plan.handoff_mode in {
        "resume_bridge",
        "reflective_ping",
        "invite_progress_ping",
    }:
        watch_signals.append(f"handoff:{guidance_plan.handoff_mode}")

    if guidance_plan.carryover_mode in {
        "repair_ping",
        "grounding_ping",
        "boundary_safe_ping",
        "clarify_hold",
    }:
        recenter_signals.append(f"carryover:{guidance_plan.carryover_mode}")
    elif guidance_plan.carryover_mode in {
        "resume_ping",
        "reflective_ping",
        "progress_ping",
    }:
        watch_signals.append(f"carryover:{guidance_plan.carryover_mode}")

    if guidance_plan.checkpoint_style in {
        "repair_checkpoint",
        "stability_check",
        "boundary_safe_step",
        "clarity_checkpoint",
    }:
        recenter_signals.append(f"checkpoint:{guidance_plan.checkpoint_style}")
    elif guidance_plan.checkpoint_style in {
        "resume_checkpoint",
        "steady_checkpoint",
        "micro_checkpoint",
    }:
        watch_signals.append(f"checkpoint:{guidance_plan.checkpoint_style}")

    recenter_signals = list(dict.fromkeys(recenter_signals))
    watch_signals = [
        signal for signal in list(dict.fromkeys(watch_signals)) if signal not in recenter_signals
    ]
    active_signals = recenter_signals + watch_signals

    if recenter_signals:
        status = "recenter"
        primary_signal = recenter_signals[0]
    elif watch_signals:
        status = "watch"
        primary_signal = watch_signals[0]
    else:
        status = "clear"
        primary_signal = None

    return {
        "status": status,
        "primary_signal": primary_signal,
        "active_signals": active_signals,
        "summary": "+".join(active_signals[:3]) if active_signals else "clear",
        "signal_count": len(active_signals),
    }


def _build_proactive_ritual_somatic_gate(
    session_ritual_plan: SessionRitualPlan | None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None,
) -> dict[str, Any]:
    """Build ritual/somatic gate from session ritual and somatic orchestration plans."""
    if session_ritual_plan is None and somatic_orchestration_plan is None:
        return {
            "status": "clear",
            "primary_signal": None,
            "active_signals": [],
            "summary": "clear",
            "signal_count": 0,
        }

    recenter_signals: list[str] = []
    watch_signals: list[str] = []

    if session_ritual_plan is not None:
        if session_ritual_plan.phase in {"repair_ritual", "alignment_check"}:
            recenter_signals.append(f"phase:{session_ritual_plan.phase}")
        elif session_ritual_plan.phase in {"opening_ritual", "re_anchor"}:
            watch_signals.append(f"phase:{session_ritual_plan.phase}")

        if session_ritual_plan.opening_move in {
            "attunement_repair",
            "regulate_first",
            "clarity_frame",
        }:
            recenter_signals.append(f"opening:{session_ritual_plan.opening_move}")
        elif session_ritual_plan.opening_move in {
            "warm_orientation",
            "shared_context_bridge",
            "reflective_restate",
        }:
            watch_signals.append(f"opening:{session_ritual_plan.opening_move}")

        if session_ritual_plan.bridge_move in {
            "repair_before_progress",
            "ground_then_step",
            "single_question_pause",
        }:
            recenter_signals.append(f"bridge:{session_ritual_plan.bridge_move}")
        elif session_ritual_plan.bridge_move in {
            "frame_the_session",
            "resume_the_open_loop",
            "reflect_then_step",
        }:
            watch_signals.append(f"bridge:{session_ritual_plan.bridge_move}")

        if session_ritual_plan.closing_move in {
            "repair_soft_close",
            "boundary_safe_close",
            "grounding_close",
            "clarify_pause",
        }:
            recenter_signals.append(f"closing:{session_ritual_plan.closing_move}")
        elif session_ritual_plan.closing_move in {
            "light_handoff",
            "progress_invitation",
            "resume_ping",
            "reflective_close",
        }:
            watch_signals.append(f"closing:{session_ritual_plan.closing_move}")

        if session_ritual_plan.continuity_anchor in {
            "repair_landing",
            "boundary_safe_step",
            "grounding_first",
            "missing_detail",
        }:
            recenter_signals.append(f"anchor:{session_ritual_plan.continuity_anchor}")
        elif session_ritual_plan.continuity_anchor in {
            "session_frame",
            "shared_context_resume",
            "reflective_step",
            "smallest_next_step",
        }:
            watch_signals.append(f"anchor:{session_ritual_plan.continuity_anchor}")

        if session_ritual_plan.somatic_shortcut != "none":
            recenter_signals.append(f"somatic_shortcut:{session_ritual_plan.somatic_shortcut}")

    if somatic_orchestration_plan is not None:
        if somatic_orchestration_plan.status == "active":
            watch_signals.append("somatic:active")
            if somatic_orchestration_plan.primary_mode in {
                "breath_regulation",
                "fatigue_release",
                "tension_release",
            }:
                recenter_signals.append(f"somatic_mode:{somatic_orchestration_plan.primary_mode}")
            elif somatic_orchestration_plan.primary_mode not in {
                "none",
                "settle_pace",
            }:
                watch_signals.append(f"somatic_mode:{somatic_orchestration_plan.primary_mode}")

            if somatic_orchestration_plan.followup_style in {
                "gentle_body_first_reentry",
                "one_breath_then_choice",
                "reduce_effort_then_micro_step",
                "soften_then_resume",
                "reflect_then_ground_then_resume",
            }:
                recenter_signals.append(f"followup:{somatic_orchestration_plan.followup_style}")
            elif somatic_orchestration_plan.followup_style not in {
                "none",
                "light_grounding_checkin",
            }:
                watch_signals.append(f"followup:{somatic_orchestration_plan.followup_style}")

            if somatic_orchestration_plan.allow_in_followup:
                watch_signals.append("somatic:carryover")

    recenter_signals = list(dict.fromkeys(recenter_signals))
    watch_signals = [
        signal for signal in list(dict.fromkeys(watch_signals)) if signal not in recenter_signals
    ]
    active_signals = recenter_signals + watch_signals

    if recenter_signals:
        status = "recenter"
        primary_signal = recenter_signals[0]
    elif watch_signals:
        status = "watch"
        primary_signal = watch_signals[0]
    else:
        status = "clear"
        primary_signal = None

    return {
        "status": status,
        "primary_signal": primary_signal,
        "active_signals": active_signals,
        "summary": "+".join(active_signals[:3]) if active_signals else "clear",
        "signal_count": len(active_signals),
    }


# ---------------------------------------------------------------------------
# Public dispatch functions
# ---------------------------------------------------------------------------


def build_proactive_aggregate_governance_assessment(
    *,
    system3_snapshot: System3Snapshot,
) -> ProactiveAggregateGovernanceAssessment:
    """Build aggregate governance assessment from system3 snapshot."""
    gate = _build_proactive_aggregate_governance_gate(system3_snapshot)
    if gate["status"] == "clear":
        rationale = (
            "No overlapping proactive governance lines are active enough to require "
            "an aggregate controller override."
        )
    else:
        rationale = (
            "Multiple proactive governance lines are active at the same time, so the "
            "controller should treat the next follow-up stages as a shared low-"
            "pressure regulation problem."
        )
    return ProactiveAggregateGovernanceAssessment(
        status=str(gate["status"]),
        primary_domain=(
            str(gate["primary_domain"]) if gate["primary_domain"] is not None else None
        ),
        active_domains=[str(item) for item in list(gate["active_domains"])],
        domain_count=int(gate["domain_count"]),
        summary=str(gate["summary"]),
        rationale=rationale,
    )


def build_proactive_stage_replan_assessment(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    system3_snapshot: System3Snapshot,
    reengagement_plan: ReengagementPlan,
    stage_refresh_plan: ProactiveStageRefreshPlan,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    prior_stage_controller_decision: ProactiveStageControllerDecision | None = None,
    prior_line_controller_decision: ProactiveLineControllerDecision | None = None,
) -> ProactiveStageReplanAssessment:
    """Build replan assessment for the current proactive stage before dispatch."""
    if directive.status != "ready" or not directive.eligible:
        return ProactiveStageReplanAssessment(
            status="hold",
            replan_key="hold",
            stage_label=stage_refresh_plan.stage_label or "unknown",
            dispatch_window_status=stage_refresh_plan.dispatch_window_status,
            changed=False,
            selected_strategy_key="hold",
            selected_ritual_mode="hold",
            selected_delivery_mode="none",
            selected_relational_move="hold",
            selected_pressure_mode="hold",
            selected_autonomy_signal="none",
            selected_sequence_objective="wait_until_regulation_is_stable",
            rationale=directive.rationale,
        )

    stage_label = stage_refresh_plan.stage_label or "first_touch"
    dispatch_window_status = stage_refresh_plan.dispatch_window_status or "on_time_dispatch"
    selected_strategy_key = reengagement_plan.strategy_key
    selected_ritual_mode = reengagement_plan.ritual_mode
    selected_delivery_mode = stage_refresh_plan.refreshed_delivery_mode
    selected_relational_move = reengagement_plan.relational_move
    selected_pressure_mode = reengagement_plan.pressure_mode
    selected_autonomy_signal = stage_refresh_plan.refreshed_autonomy_mode
    selected_sequence_objective = reengagement_plan.sequence_objective
    selected_somatic_action = reengagement_plan.somatic_action
    replan_notes: list[str] = []
    aggregate_governance_gate = (
        {
            "status": aggregate_governance_assessment.status,
            "primary_domain": aggregate_governance_assessment.primary_domain,
            "active_domains": list(aggregate_governance_assessment.active_domains),
            "summary": aggregate_governance_assessment.summary,
            "domain_count": aggregate_governance_assessment.domain_count,
        }
        if aggregate_governance_assessment is not None
        else _build_proactive_aggregate_governance_gate(system3_snapshot)
    )

    low_pressure_context = (
        guidance_plan.mode in {"repair_guidance", "boundary_guidance"}
        or guidance_plan.handoff_mode
        in {"repair_soft_ping", "no_pressure_checkin", "autonomy_preserving_ping"}
        or system3_snapshot.strategy_audit_status in {"watch", "revise"}
        or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
        or system3_snapshot.safety_governance_status in {"watch", "revise"}
        or system3_snapshot.safety_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.autonomy_governance_status in {"watch", "revise"}
        or system3_snapshot.autonomy_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.boundary_governance_status in {"watch", "revise"}
        or system3_snapshot.boundary_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.support_governance_status in {"watch", "revise"}
        or system3_snapshot.support_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.clarity_governance_status in {"watch", "revise"}
        or system3_snapshot.clarity_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.pacing_governance_status in {"watch", "revise"}
        or system3_snapshot.pacing_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.attunement_governance_status in {"watch", "revise"}
        or system3_snapshot.attunement_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.commitment_governance_status in {"watch", "revise"}
        or system3_snapshot.commitment_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.disclosure_governance_status in {"watch", "revise"}
        or system3_snapshot.disclosure_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.reciprocity_governance_status in {"watch", "revise"}
        or system3_snapshot.reciprocity_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.progress_governance_status in {"watch", "revise"}
        or system3_snapshot.progress_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.stability_governance_status in {"watch", "revise"}
        or system3_snapshot.stability_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.pressure_governance_status in {"watch", "revise"}
        or system3_snapshot.pressure_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.trust_governance_status in {"watch", "revise"}
        or system3_snapshot.trust_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.continuity_governance_status in {"watch", "revise"}
        or system3_snapshot.continuity_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.repair_governance_status in {"watch", "revise"}
        or system3_snapshot.repair_governance_trajectory_status in {"watch", "recenter"}
        or system3_snapshot.relational_governance_status in {"watch", "revise"}
        or system3_snapshot.relational_governance_trajectory_status in {"watch", "recenter"}
        or aggregate_governance_gate["status"] != "clear"
        or dispatch_window_status in {"guarded_release", "progressed_dispatch"}
        or dispatch_feedback_assessment.changed
    )
    if aggregate_governance_gate["status"] != "clear":
        replan_notes.append(
            "aggregate_governance_gate:"
            f"{aggregate_governance_gate['status']}:"
            f"{aggregate_governance_gate['summary']}"
        )
    controller_applies = bool(
        prior_stage_controller_decision is not None
        and prior_stage_controller_decision.status == "active"
        and prior_stage_controller_decision.changed
        and prior_stage_controller_decision.decision == "slow_next_stage"
        and prior_stage_controller_decision.target_stage_label == stage_label
    )
    line_controller_applies = bool(
        prior_line_controller_decision is not None
        and prior_line_controller_decision.status == "active"
        and prior_line_controller_decision.changed
        and prior_line_controller_decision.decision
        in {"soften_remaining_line", "retire_after_close_loop"}
        and stage_label in prior_line_controller_decision.affected_stage_labels
    )

    if dispatch_feedback_assessment.changed:
        selected_strategy_key = dispatch_feedback_assessment.selected_strategy_key
        selected_pressure_mode = dispatch_feedback_assessment.selected_pressure_mode
        selected_autonomy_signal = dispatch_feedback_assessment.selected_autonomy_signal
        selected_delivery_mode = dispatch_feedback_assessment.selected_delivery_mode
        selected_sequence_objective = dispatch_feedback_assessment.selected_sequence_objective
        replan_notes.append(f"dispatch_feedback:{dispatch_feedback_assessment.feedback_key}")

    if stage_label == "second_touch":
        selected_ritual_mode = "resume_reanchor"
        selected_delivery_mode = stage_refresh_plan.refreshed_delivery_mode
        selected_autonomy_signal = "explicit_no_pressure"
        if dispatch_feedback_assessment.changed:
            selected_delivery_mode = dispatch_feedback_assessment.selected_delivery_mode
            selected_autonomy_signal = dispatch_feedback_assessment.selected_autonomy_signal
        if low_pressure_context:
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_relational_move = "repair_bridge"
            selected_pressure_mode = "repair_soft"
            selected_sequence_objective = "reconnect_without_relational_demand"
            replan_notes.append("second_touch_replanned_for_repair_safety")
            if dispatch_feedback_assessment.changed:
                selected_sequence_objective = (
                    dispatch_feedback_assessment.selected_sequence_objective
                )
        else:
            selected_strategy_key = "resume_context_bridge"
            selected_relational_move = "context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_sequence_objective = "re_anchor_then_continue"
            replan_notes.append("second_touch_replanned_as_resume_bridge")
            if dispatch_feedback_assessment.changed:
                selected_strategy_key = dispatch_feedback_assessment.selected_strategy_key
                selected_pressure_mode = dispatch_feedback_assessment.selected_pressure_mode
                selected_sequence_objective = (
                    dispatch_feedback_assessment.selected_sequence_objective
                )
        if stage_refresh_plan.changed:
            replan_notes.append("stage_refresh_applied_before_dispatch")
    elif stage_label == "final_soft_close":
        selected_ritual_mode = "continuity_nudge"
        selected_delivery_mode = "single_message"
        selected_somatic_action = None
        if dispatch_feedback_assessment.feedback_key == "final_stage_after_defer_close_out":
            selected_strategy_key = dispatch_feedback_assessment.selected_strategy_key
            selected_relational_move = "continuity_ping"
            selected_pressure_mode = dispatch_feedback_assessment.selected_pressure_mode
            selected_autonomy_signal = dispatch_feedback_assessment.selected_autonomy_signal
            selected_delivery_mode = dispatch_feedback_assessment.selected_delivery_mode
            selected_sequence_objective = dispatch_feedback_assessment.selected_sequence_objective
            replan_notes.append("final_soft_close_replanned_from_dispatch_feedback")
        elif low_pressure_context:
            selected_strategy_key = "repair_soft_reentry"
            selected_relational_move = "repair_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_sequence_objective = "reconnect_without_relational_demand"
            replan_notes.append("final_soft_close_replanned_for_repair_safety")
        else:
            selected_strategy_key = "continuity_soft_ping"
            selected_relational_move = "continuity_ping"
            selected_pressure_mode = "low_pressure_presence"
            selected_autonomy_signal = "open_loop_without_demand"
            selected_sequence_objective = "presence_then_optional_reply"
            replan_notes.append("final_soft_close_replanned_as_continuity_ping")
        if stage_refresh_plan.changed:
            replan_notes.append("stage_refresh_applied_before_dispatch")
    elif low_pressure_context:
        selected_autonomy_signal = "explicit_no_pressure"
        selected_pressure_mode = "repair_soft"
        replan_notes.append("dispatch_softened_for_safety")

    if controller_applies:
        selected_delivery_mode = (
            prior_stage_controller_decision.selected_delivery_mode or selected_delivery_mode
        )
        selected_autonomy_signal = (
            prior_stage_controller_decision.selected_autonomy_signal or selected_autonomy_signal
        )
        if stage_label == "second_touch":
            selected_strategy_key = (
                prior_stage_controller_decision.selected_strategy_key or selected_strategy_key
            )
            selected_relational_move = "context_bridge"
            selected_pressure_mode = (
                prior_stage_controller_decision.selected_pressure_mode or selected_pressure_mode
            )
            selected_sequence_objective = "re_anchor_then_continue"
        elif stage_label == "final_soft_close":
            selected_strategy_key = (
                prior_stage_controller_decision.selected_strategy_key or selected_strategy_key
            )
            selected_relational_move = "continuity_ping"
            selected_pressure_mode = (
                prior_stage_controller_decision.selected_pressure_mode or selected_pressure_mode
            )
            selected_sequence_objective = "presence_then_optional_reply"
        replan_notes.append(f"stage_controller:{prior_stage_controller_decision.controller_key}")

    if line_controller_applies:
        selected_delivery_mode = (
            prior_line_controller_decision.selected_delivery_mode or selected_delivery_mode
        )
        if stage_label == "second_touch":
            selected_autonomy_signal = "explicit_no_pressure"
            selected_pressure_mode = "gentle_resume"
            selected_sequence_objective = "re_anchor_then_continue"
        elif (
            stage_label == "final_soft_close"
            and prior_line_controller_decision.line_state == "close_ready"
        ):
            selected_autonomy_signal = "archive_light_thread"
            selected_pressure_mode = "archive_light_presence"
            selected_sequence_objective = "presence_then_optional_reply"
        replan_notes.append(f"line_controller:{prior_line_controller_decision.controller_key}")

    changed = any(
        [
            selected_strategy_key != reengagement_plan.strategy_key,
            selected_ritual_mode != reengagement_plan.ritual_mode,
            selected_delivery_mode != reengagement_plan.delivery_mode,
            selected_relational_move != reengagement_plan.relational_move,
            selected_pressure_mode != reengagement_plan.pressure_mode,
            selected_autonomy_signal != reengagement_plan.autonomy_signal,
            selected_sequence_objective != reengagement_plan.sequence_objective,
            selected_somatic_action != reengagement_plan.somatic_action,
        ]
    )

    replan_key = f"{stage_label}_{dispatch_window_status}_{selected_strategy_key}"
    if not changed:
        replan_key = f"{stage_label}_{dispatch_window_status}_stable"

    rationale = (
        "The current proactive stage is being re-planned right before dispatch so the "
        "strategy stays low-pressure and stage-appropriate."
    )
    if not replan_notes:
        rationale = (
            "The current proactive stage can keep its original re-engagement strategy "
            "because the latest dispatch context still fits the planned line."
        )

    return ProactiveStageReplanAssessment(
        status="active",
        replan_key=replan_key,
        stage_label=stage_label,
        dispatch_window_status=dispatch_window_status,
        changed=changed,
        selected_strategy_key=selected_strategy_key,
        selected_ritual_mode=selected_ritual_mode,
        selected_delivery_mode=selected_delivery_mode,
        selected_relational_move=selected_relational_move,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_sequence_objective=selected_sequence_objective,
        selected_somatic_action=selected_somatic_action,
        replan_notes=_compact(replan_notes, limit=5),
        rationale=rationale,
    )


def build_proactive_dispatch_feedback_assessment(
    *,
    directive: ProactiveFollowupDirective,
    reengagement_plan: ReengagementPlan,
    stage_label: str,
    dispatch_events_for_directive: list[dict[str, Any]],
    gate_events_for_directive: list[dict[str, Any]],
) -> ProactiveDispatchFeedbackAssessment:
    """Build dispatch feedback assessment from prior dispatch and gate events."""
    if directive.status != "ready" or not directive.eligible:
        return ProactiveDispatchFeedbackAssessment(
            status="hold",
            feedback_key="hold",
            stage_label=stage_label or "unknown",
            dispatch_count=0,
            prior_stage_label=None,
            gate_defer_count=0,
            changed=False,
            selected_strategy_key="hold",
            selected_pressure_mode="hold",
            selected_autonomy_signal="none",
            selected_delivery_mode="none",
            selected_sequence_objective="wait_until_context_is_ready",
            rationale=directive.rationale,
        )

    dispatch_count = len(dispatch_events_for_directive)
    prior_dispatch = (
        dict(dispatch_events_for_directive[-1]) if dispatch_events_for_directive else {}
    )
    prior_stage_label = str(prior_dispatch.get("proactive_cadence_stage_label") or "") or None
    gate_defer_events = [
        event for event in gate_events_for_directive if str(event.get("decision") or "") == "defer"
    ]
    gate_defer_count = len(gate_defer_events)

    feedback_key = f"{stage_label}_baseline_feedback"
    changed = False
    selected_strategy_key = reengagement_plan.strategy_key
    selected_pressure_mode = reengagement_plan.pressure_mode
    selected_autonomy_signal = reengagement_plan.autonomy_signal
    selected_delivery_mode = reengagement_plan.delivery_mode
    selected_sequence_objective = reengagement_plan.sequence_objective
    feedback_notes: list[str] = []

    if stage_label == "second_touch" and dispatch_count >= 1 and prior_stage_label == "first_touch":
        feedback_key = "second_touch_after_first_touch_soften"
        changed = True
        selected_strategy_key = "resume_context_bridge"
        selected_pressure_mode = "gentle_resume"
        selected_autonomy_signal = "explicit_no_pressure"
        selected_delivery_mode = "single_message"
        selected_sequence_objective = "re_anchor_then_continue"
        feedback_notes.extend(
            [
                "prior_touch_already_landed",
                "compress_second_touch_shape",
            ]
        )

    if stage_label == "final_soft_close" and gate_defer_count > 0:
        feedback_key = "final_stage_after_defer_close_out"
        changed = True
        selected_strategy_key = "continuity_soft_ping"
        selected_pressure_mode = "archive_light_presence"
        selected_autonomy_signal = "archive_light_thread"
        selected_delivery_mode = "single_message"
        selected_sequence_objective = "leave_thread_open_without_additional_followup"
        feedback_notes.extend(
            [
                "prior_gate_defer_respected",
                "soft_close_should_finish_lightly",
            ]
        )

    rationale = (
        "The current proactive stage can keep its baseline line because prior dispatches "
        "have not introduced extra pressure that needs correction."
    )
    if changed:
        rationale = (
            "The current proactive stage should absorb prior dispatch/gate outcomes so "
            "later touches get softer instead of repeating the original pressure shape."
        )

    return ProactiveDispatchFeedbackAssessment(
        status="active",
        feedback_key=feedback_key,
        stage_label=stage_label,
        dispatch_count=dispatch_count,
        prior_stage_label=prior_stage_label,
        gate_defer_count=gate_defer_count,
        changed=changed,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        selected_sequence_objective=selected_sequence_objective,
        feedback_notes=_compact(feedback_notes, limit=5),
        rationale=rationale,
    )
