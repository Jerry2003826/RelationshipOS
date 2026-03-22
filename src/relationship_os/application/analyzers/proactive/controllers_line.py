"""Proactive controllers: line controller."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch import (
    _build_proactive_aggregate_governance_gate,
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateControllerDecision,
    ProactiveAggregateGovernanceAssessment,
    ProactiveCadencePlan,
    ProactiveDispatchFeedbackAssessment,
    ProactiveDispatchGateDecision,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


def build_proactive_line_controller_decision(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    system3_snapshot: System3Snapshot,
    current_stage_label: str,
    current_stage_index: int,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    stage_controller_decision: ProactiveStageControllerDecision,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    guidance_plan: GuidancePlan | None = None,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
) -> ProactiveLineControllerDecision:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveLineControllerDecision(
            status="hold",
            controller_key="hold",
            trigger_stage_label=current_stage_label or "unknown",
            line_state="hold",
            decision="hold",
            changed=False,
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or [current_stage_label])
    stage_count = max(
        1,
        proactive_cadence_plan.close_after_stage_index or len(stage_labels) or 1,
    )
    final_stage_label = (
        stage_labels[min(stage_count, len(stage_labels)) - 1]
        if stage_labels
        else current_stage_label
    )
    remaining_stage_labels = [
        label
        for label in stage_labels[current_stage_index : min(stage_count, len(stage_labels))]
        if str(label).strip()
    ]

    if not remaining_stage_labels:
        if current_stage_label == final_stage_label:
            return ProactiveLineControllerDecision(
                status="active",
                controller_key=f"{current_stage_label}_line_close_ready",
                trigger_stage_label=current_stage_label,
                line_state="close_ready",
                decision="retire_after_close_loop",
                changed=True,
                selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
                selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
                selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
                controller_notes=["current_stage_is_final_close_loop"],
                rationale=(
                    "The current stage is already the last proactive touch, so the "
                    "line should stay close-ready until this close-loop finishes."
                ),
            )
        return ProactiveLineControllerDecision(
            status="terminal",
            controller_key=f"{current_stage_label}_line_complete",
            trigger_stage_label=current_stage_label,
            line_state="line_complete",
            decision="close_line",
            changed=False,
            selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
            selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
            selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
            rationale=(
                "The current stage already exhausted the remaining proactive line, so "
                "there is nothing left to soften or retire."
            ),
        )

    controller_key = f"{current_stage_label}_follow_remaining_line"
    line_state = "steady"
    decision = "follow_remaining_line"
    changed = False
    additional_delay_seconds = 0
    selected_pressure_mode = stage_replan_assessment.selected_pressure_mode
    selected_autonomy_signal = stage_replan_assessment.selected_autonomy_signal
    selected_delivery_mode = stage_replan_assessment.selected_delivery_mode
    controller_notes: list[str] = []
    safety_recenter_active = (
        system3_snapshot.safety_governance_status == "revise"
        or system3_snapshot.safety_governance_trajectory_status == "recenter"
    )
    safety_watch_active = not safety_recenter_active and (
        system3_snapshot.safety_governance_status == "watch"
        or system3_snapshot.safety_governance_trajectory_status == "watch"
    )
    autonomy_recenter_active = not safety_recenter_active and (
        system3_snapshot.autonomy_governance_status == "revise"
        or system3_snapshot.autonomy_governance_trajectory_status == "recenter"
    )
    autonomy_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and (
            system3_snapshot.autonomy_governance_status == "watch"
            or system3_snapshot.autonomy_governance_trajectory_status == "watch"
        )
    )
    boundary_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and (
            system3_snapshot.boundary_governance_status == "revise"
            or system3_snapshot.boundary_governance_trajectory_status == "recenter"
        )
    )
    boundary_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and (
            system3_snapshot.boundary_governance_status == "watch"
            or system3_snapshot.boundary_governance_trajectory_status == "watch"
        )
    )
    support_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and (
            system3_snapshot.support_governance_status == "revise"
            or system3_snapshot.support_governance_trajectory_status == "recenter"
        )
    )
    support_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and (
            system3_snapshot.support_governance_status == "watch"
            or system3_snapshot.support_governance_trajectory_status == "watch"
        )
    )
    clarity_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and (
            system3_snapshot.clarity_governance_status == "revise"
            or system3_snapshot.clarity_governance_trajectory_status == "recenter"
        )
    )
    clarity_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and (
            system3_snapshot.clarity_governance_status == "watch"
            or system3_snapshot.clarity_governance_trajectory_status == "watch"
        )
    )
    pacing_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and (
            system3_snapshot.pacing_governance_status == "revise"
            or system3_snapshot.pacing_governance_trajectory_status == "recenter"
        )
    )
    pacing_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and (
            system3_snapshot.pacing_governance_status == "watch"
            or system3_snapshot.pacing_governance_trajectory_status == "watch"
        )
    )
    attunement_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and (
            system3_snapshot.attunement_governance_status == "revise"
            or system3_snapshot.attunement_governance_trajectory_status == "recenter"
        )
    )
    attunement_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and (
            system3_snapshot.attunement_governance_status == "watch"
            or system3_snapshot.attunement_governance_trajectory_status == "watch"
        )
    )
    commitment_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and (
            system3_snapshot.commitment_governance_status == "revise"
            or system3_snapshot.commitment_governance_trajectory_status == "recenter"
        )
    )
    commitment_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and (
            system3_snapshot.commitment_governance_status == "watch"
            or system3_snapshot.commitment_governance_trajectory_status == "watch"
        )
    )
    disclosure_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and (
            system3_snapshot.disclosure_governance_status == "revise"
            or system3_snapshot.disclosure_governance_trajectory_status == "recenter"
        )
    )
    disclosure_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and not disclosure_recenter_active
        and (
            system3_snapshot.disclosure_governance_status == "watch"
            or system3_snapshot.disclosure_governance_trajectory_status == "watch"
        )
    )
    reciprocity_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and not disclosure_recenter_active
        and (
            system3_snapshot.reciprocity_governance_status == "revise"
            or system3_snapshot.reciprocity_governance_trajectory_status == "recenter"
        )
    )
    reciprocity_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and not disclosure_recenter_active
        and not reciprocity_recenter_active
        and (
            system3_snapshot.reciprocity_governance_status == "watch"
            or system3_snapshot.reciprocity_governance_trajectory_status == "watch"
        )
    )
    progress_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and not disclosure_recenter_active
        and not reciprocity_recenter_active
        and (
            system3_snapshot.progress_governance_status == "revise"
            or system3_snapshot.progress_governance_trajectory_status == "recenter"
        )
    )
    progress_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and not disclosure_recenter_active
        and not reciprocity_recenter_active
        and not progress_recenter_active
        and (
            system3_snapshot.progress_governance_status == "watch"
            or system3_snapshot.progress_governance_trajectory_status == "watch"
        )
    )
    stability_recenter_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not commitment_recenter_active
        and not disclosure_recenter_active
        and not reciprocity_recenter_active
        and not progress_recenter_active
        and (
            system3_snapshot.stability_governance_status == "revise"
            or system3_snapshot.stability_governance_trajectory_status == "recenter"
        )
    )
    stability_watch_active = (
        not safety_recenter_active
        and not autonomy_recenter_active
        and not autonomy_watch_active
        and not boundary_watch_active
        and not support_watch_active
        and not clarity_watch_active
        and not pacing_watch_active
        and not attunement_watch_active
        and not commitment_watch_active
        and not disclosure_watch_active
        and not reciprocity_watch_active
        and not progress_watch_active
        and not stability_recenter_active
        and (
            system3_snapshot.stability_governance_status == "watch"
            or system3_snapshot.stability_governance_trajectory_status == "watch"
        )
    )
    pressure_recenter_active = (
        not safety_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not stability_recenter_active
        and (
            system3_snapshot.pressure_governance_status == "revise"
            or system3_snapshot.pressure_governance_trajectory_status == "recenter"
        )
    )
    pressure_watch_active = (
        not safety_recenter_active
        and not boundary_watch_active
        and not support_watch_active
        and not clarity_watch_active
        and not pacing_watch_active
        and not attunement_watch_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and (
            system3_snapshot.pressure_governance_status == "watch"
            or system3_snapshot.pressure_governance_trajectory_status == "watch"
        )
    )
    trust_recenter_active = (
        not safety_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and (
            system3_snapshot.trust_governance_status == "revise"
            or system3_snapshot.trust_governance_trajectory_status == "recenter"
        )
    )
    trust_watch_active = (
        not safety_recenter_active
        and not boundary_watch_active
        and not support_watch_active
        and not clarity_watch_active
        and not pacing_watch_active
        and not attunement_watch_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and (
            system3_snapshot.trust_governance_status == "watch"
            or system3_snapshot.trust_governance_trajectory_status == "watch"
        )
    )
    continuity_recenter_active = (
        not safety_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and (
            system3_snapshot.continuity_governance_status == "revise"
            or system3_snapshot.continuity_governance_trajectory_status == "recenter"
        )
    )
    continuity_watch_active = (
        not safety_recenter_active
        and not boundary_watch_active
        and not support_watch_active
        and not clarity_watch_active
        and not pacing_watch_active
        and not attunement_watch_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and not continuity_recenter_active
        and (
            system3_snapshot.continuity_governance_status == "watch"
            or system3_snapshot.continuity_governance_trajectory_status == "watch"
        )
    )
    repair_recenter_active = (
        not safety_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and not continuity_recenter_active
        and (
            system3_snapshot.repair_governance_status == "revise"
            or system3_snapshot.repair_governance_trajectory_status == "recenter"
        )
    )
    repair_watch_active = (
        not safety_recenter_active
        and not boundary_watch_active
        and not support_watch_active
        and not clarity_watch_active
        and not pacing_watch_active
        and not attunement_watch_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and not continuity_recenter_active
        and not repair_recenter_active
        and (
            system3_snapshot.repair_governance_status == "watch"
            or system3_snapshot.repair_governance_trajectory_status == "watch"
        )
    )
    relational_recenter_active = (
        not safety_recenter_active
        and not boundary_recenter_active
        and not support_recenter_active
        and not clarity_recenter_active
        and not pacing_recenter_active
        and not attunement_recenter_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and not continuity_recenter_active
        and not repair_recenter_active
        and (
            system3_snapshot.relational_governance_status == "revise"
            or system3_snapshot.relational_governance_trajectory_status == "recenter"
        )
    )
    relational_watch_active = (
        not safety_recenter_active
        and not boundary_watch_active
        and not support_watch_active
        and not clarity_watch_active
        and not pacing_watch_active
        and not attunement_watch_active
        and not stability_recenter_active
        and not pressure_recenter_active
        and not trust_recenter_active
        and not continuity_recenter_active
        and not repair_recenter_active
        and not relational_recenter_active
        and (
            system3_snapshot.relational_governance_status == "watch"
            or system3_snapshot.relational_governance_trajectory_status == "watch"
        )
    )

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
    aggregate_recenter_active = aggregate_governance_gate["status"] == "recenter"
    aggregate_watch_active = aggregate_governance_gate["status"] == "watch"
    aggregate_governance_summary = str(aggregate_governance_gate["summary"])
    guidance_gate = _build_proactive_guidance_gate(guidance_plan)
    guidance_recenter_active = guidance_gate["status"] == "recenter"
    guidance_watch_active = guidance_gate["status"] == "watch"
    guidance_summary = str(guidance_gate["summary"])
    guidance_repair_soft = bool(
        guidance_plan is not None
        and (
            guidance_plan.mode in {"repair_guidance", "stabilizing_guidance"}
            or guidance_plan.handoff_mode == "repair_soft_ping"
        )
    )
    guidance_low_pressure = bool(
        guidance_plan is not None
        and guidance_plan.handoff_mode
        in {
            "repair_soft_ping",
            "no_pressure_checkin",
            "autonomy_preserving_ping",
            "wait_for_reply",
        }
    )
    ritual_somatic_gate = _build_proactive_ritual_somatic_gate(
        session_ritual_plan,
        somatic_orchestration_plan,
    )
    ritual_recenter_active = ritual_somatic_gate["status"] == "recenter"
    ritual_watch_active = ritual_somatic_gate["status"] == "watch"
    ritual_summary = str(ritual_somatic_gate["summary"])
    ritual_low_pressure = bool(
        session_ritual_plan is not None
        and (
            session_ritual_plan.phase in {"repair_ritual", "alignment_check"}
            or session_ritual_plan.closing_move
            in {
                "repair_soft_close",
                "boundary_safe_close",
                "grounding_close",
                "clarify_pause",
            }
            or session_ritual_plan.somatic_shortcut != "none"
        )
    )
    ritual_delivery_mode = (
        "two_part_sequence"
        if somatic_orchestration_plan is not None
        and somatic_orchestration_plan.status == "active"
        and somatic_orchestration_plan.allow_in_followup
        and somatic_orchestration_plan.followup_style
        in {
            "gentle_body_first_reentry",
            "one_breath_then_choice",
            "reduce_effort_then_micro_step",
            "soften_then_resume",
            "reflect_then_ground_then_resume",
        }
        else "single_message"
    )

    if current_stage_label == "first_touch":
        if (
            orchestration_controller_decision is not None
            and orchestration_controller_decision.status == "active"
            and orchestration_controller_decision.changed
            and orchestration_controller_decision.current_stage_label == "first_touch"
            and orchestration_controller_decision.line_additional_delay_seconds > 0
        ):
            controller_key = (
                "remaining_line_orchestration_recentered_after_first_touch"
                if orchestration_controller_decision.decision == "recenter_followup_line"
                else "remaining_line_orchestration_softened_after_first_touch"
            )
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = (
                orchestration_controller_decision.line_additional_delay_seconds
            )
            selected_pressure_mode = orchestration_controller_decision.selected_pressure_mode
            selected_autonomy_signal = orchestration_controller_decision.selected_autonomy_signal
            selected_delivery_mode = orchestration_controller_decision.selected_delivery_mode
            controller_notes.extend(list(orchestration_controller_decision.controller_notes))
        elif (
            aggregate_controller_decision is not None
            and aggregate_controller_decision.status == "active"
            and aggregate_controller_decision.changed
            and aggregate_controller_decision.current_stage_label == "first_touch"
            and aggregate_controller_decision.line_additional_delay_seconds > 0
        ):
            controller_key = (
                "remaining_line_governance_recentered_after_first_touch"
                if aggregate_controller_decision.decision == "recenter_followup_line"
                else "remaining_line_governance_softened_after_first_touch"
            )
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = aggregate_controller_decision.line_additional_delay_seconds
            selected_pressure_mode = aggregate_controller_decision.selected_pressure_mode
            selected_autonomy_signal = aggregate_controller_decision.selected_autonomy_signal
            selected_delivery_mode = aggregate_controller_decision.selected_delivery_mode
            controller_notes.extend(list(aggregate_controller_decision.controller_notes))
        elif aggregate_recenter_active:
            controller_key = "remaining_line_governance_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 3900
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_recenter:{aggregate_governance_summary}",
                    "keep_remaining_line_soft",
                ]
            )
        elif aggregate_watch_active:
            controller_key = "remaining_line_governance_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2700
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_watch:{aggregate_governance_summary}",
                    "keep_remaining_line_soft",
                ]
            )
        elif safety_recenter_active:
            controller_key = "remaining_line_safety_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 3600
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif safety_watch_active:
            controller_key = "remaining_line_safety_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2700
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif autonomy_recenter_active:
            controller_key = "remaining_line_autonomy_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 3150
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif autonomy_watch_active:
            controller_key = "remaining_line_autonomy_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2250
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif boundary_recenter_active:
            controller_key = "remaining_line_boundary_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 3000
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif boundary_watch_active:
            controller_key = "remaining_line_boundary_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2100
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif support_recenter_active:
            controller_key = "remaining_line_support_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2700
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif support_watch_active:
            controller_key = "remaining_line_support_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1800
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif clarity_recenter_active:
            controller_key = "remaining_line_clarity_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2400
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif clarity_watch_active:
            controller_key = "remaining_line_clarity_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1500
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif pacing_recenter_active:
            controller_key = "remaining_line_pacing_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2100
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif pacing_watch_active:
            controller_key = "remaining_line_pacing_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1200
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif attunement_recenter_active:
            controller_key = "remaining_line_attunement_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2400
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif attunement_watch_active:
            controller_key = "remaining_line_attunement_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1500
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif commitment_recenter_active:
            controller_key = "remaining_line_commitment_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2550
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif commitment_watch_active:
            controller_key = "remaining_line_commitment_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1650
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif disclosure_recenter_active:
            controller_key = "remaining_line_disclosure_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2550
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif disclosure_watch_active:
            controller_key = "remaining_line_disclosure_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1650
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif reciprocity_recenter_active:
            controller_key = "remaining_line_reciprocity_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2550
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif reciprocity_watch_active:
            controller_key = "remaining_line_reciprocity_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1650
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif progress_recenter_active:
            controller_key = "remaining_line_progress_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2550
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif progress_watch_active:
            controller_key = "remaining_line_progress_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1650
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif stability_recenter_active:
            controller_key = "remaining_line_stability_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2700
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif stability_watch_active:
            controller_key = "remaining_line_stability_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1800
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif pressure_recenter_active:
            controller_key = "remaining_line_pressure_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 2400
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif pressure_watch_active:
            controller_key = "remaining_line_pressure_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1500
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif trust_recenter_active:
            controller_key = "remaining_line_trust_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1800
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif trust_watch_active:
            controller_key = "remaining_line_trust_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1200
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif continuity_recenter_active:
            controller_key = "remaining_line_continuity_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1500
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif continuity_watch_active:
            controller_key = "remaining_line_continuity_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 900
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif repair_recenter_active:
            controller_key = "remaining_line_repair_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1200
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif repair_watch_active:
            controller_key = "remaining_line_repair_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 750
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif relational_recenter_active:
            controller_key = "remaining_line_relational_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 900
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_recenter",
                    "keep_remaining_line_soft",
                ]
            )
        elif relational_watch_active:
            controller_key = "remaining_line_relational_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 600
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_watch",
                    "keep_remaining_line_soft",
                ]
            )
        elif guidance_recenter_active:
            controller_key = "remaining_line_guidance_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1200
            selected_pressure_mode = "repair_soft" if guidance_repair_soft else "gentle_resume"
            selected_autonomy_signal = (
                "explicit_no_pressure" if guidance_low_pressure else "light_invitation"
            )
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_recenter:{guidance_summary}",
                    "keep_remaining_line_soft",
                ]
            )
        elif guidance_watch_active:
            controller_key = "remaining_line_guidance_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 600
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = (
                "explicit_no_pressure" if guidance_low_pressure else "light_invitation"
            )
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_watch:{guidance_summary}",
                    "keep_remaining_line_soft",
                ]
            )
        elif ritual_recenter_active:
            controller_key = "remaining_line_ritual_recentered_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 900
            selected_pressure_mode = "repair_soft" if ritual_low_pressure else "gentle_resume"
            selected_autonomy_signal = (
                "explicit_no_pressure" if ritual_low_pressure else "light_invitation"
            )
            selected_delivery_mode = ritual_delivery_mode
            controller_notes.extend(
                [
                    f"ritual_somatic_recenter:{ritual_summary}",
                    "keep_remaining_line_soft",
                ]
            )
        elif ritual_watch_active:
            controller_key = "remaining_line_ritual_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 450
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = (
                "explicit_no_pressure" if ritual_low_pressure else "light_invitation"
            )
            selected_delivery_mode = ritual_delivery_mode
            controller_notes.extend(
                [
                    f"ritual_somatic_watch:{ritual_summary}",
                    "keep_remaining_line_soft",
                ]
            )
        elif (
            stage_controller_decision.changed
            or dispatch_feedback_assessment.changed
            or stage_replan_assessment.selected_autonomy_signal
            in {"explicit_opt_out", "explicit_no_pressure"}
            or stage_replan_assessment.selected_pressure_mode
            in {"low_pressure_progress", "gentle_resume", "repair_soft"}
        ):
            controller_key = "remaining_line_softened_after_first_touch"
            line_state = "softened"
            decision = "soften_remaining_line"
            changed = True
            additional_delay_seconds = 1800
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "first_touch_already_set_low_pressure",
                    "keep_remaining_line_soft",
                ]
            )
    elif current_stage_label == "second_touch":
        if (
            orchestration_controller_decision is not None
            and orchestration_controller_decision.status == "active"
            and orchestration_controller_decision.changed
            and orchestration_controller_decision.current_stage_label == "second_touch"
            and orchestration_controller_decision.line_additional_delay_seconds > 0
        ):
            controller_key = (
                "remaining_line_orchestration_close_ready"
                if orchestration_controller_decision.decision == "recenter_followup_line"
                else "remaining_line_orchestration_watch_close_ready"
            )
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = (
                orchestration_controller_decision.line_additional_delay_seconds
            )
            selected_pressure_mode = orchestration_controller_decision.selected_pressure_mode
            selected_autonomy_signal = orchestration_controller_decision.selected_autonomy_signal
            selected_delivery_mode = orchestration_controller_decision.selected_delivery_mode
            controller_notes.extend(list(orchestration_controller_decision.controller_notes))
        elif aggregate_recenter_active:
            controller_key = "remaining_line_governance_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3900 if dispatch_gate_decision.decision == "defer" else 3000
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_recenter:{aggregate_governance_summary}",
                    "favor_close_ready_shape",
                ]
            )
        elif aggregate_watch_active:
            controller_key = "remaining_line_governance_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3000 if dispatch_gate_decision.decision == "defer" else 2100
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_watch:{aggregate_governance_summary}",
                    "favor_close_ready_shape",
                ]
            )
        elif safety_recenter_active:
            controller_key = "remaining_line_safety_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 5400 if dispatch_gate_decision.decision == "defer" else 3600
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif safety_watch_active:
            controller_key = "remaining_line_safety_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3600 if dispatch_gate_decision.decision == "defer" else 2700
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif autonomy_recenter_active:
            controller_key = "remaining_line_autonomy_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 4500 if dispatch_gate_decision.decision == "defer" else 3150
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif autonomy_watch_active:
            controller_key = "remaining_line_autonomy_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3150 if dispatch_gate_decision.decision == "defer" else 2250
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif boundary_recenter_active:
            controller_key = "remaining_line_boundary_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 4200 if dispatch_gate_decision.decision == "defer" else 3000
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif boundary_watch_active:
            controller_key = "remaining_line_boundary_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3000 if dispatch_gate_decision.decision == "defer" else 2100
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif support_recenter_active:
            controller_key = "remaining_line_support_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3600 if dispatch_gate_decision.decision == "defer" else 2700
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif support_watch_active:
            controller_key = "remaining_line_support_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2700 if dispatch_gate_decision.decision == "defer" else 1800
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif clarity_recenter_active:
            controller_key = "remaining_line_clarity_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3300 if dispatch_gate_decision.decision == "defer" else 2400
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif clarity_watch_active:
            controller_key = "remaining_line_clarity_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2400 if dispatch_gate_decision.decision == "defer" else 1500
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif pacing_recenter_active:
            controller_key = "remaining_line_pacing_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3000 if dispatch_gate_decision.decision == "defer" else 2100
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif pacing_watch_active:
            controller_key = "remaining_line_pacing_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2100 if dispatch_gate_decision.decision == "defer" else 1200
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif attunement_recenter_active:
            controller_key = "remaining_line_attunement_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3300 if dispatch_gate_decision.decision == "defer" else 2400
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif attunement_watch_active:
            controller_key = "remaining_line_attunement_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2400 if dispatch_gate_decision.decision == "defer" else 1500
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif commitment_recenter_active:
            controller_key = "remaining_line_commitment_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3450 if dispatch_gate_decision.decision == "defer" else 2550
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif commitment_watch_active:
            controller_key = "remaining_line_commitment_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2550 if dispatch_gate_decision.decision == "defer" else 1650
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif disclosure_recenter_active:
            controller_key = "remaining_line_disclosure_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3450 if dispatch_gate_decision.decision == "defer" else 2550
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif disclosure_watch_active:
            controller_key = "remaining_line_disclosure_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2550 if dispatch_gate_decision.decision == "defer" else 1650
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif reciprocity_recenter_active:
            controller_key = "remaining_line_reciprocity_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3450 if dispatch_gate_decision.decision == "defer" else 2550
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif reciprocity_watch_active:
            controller_key = "remaining_line_reciprocity_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2550 if dispatch_gate_decision.decision == "defer" else 1650
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif progress_recenter_active:
            controller_key = "remaining_line_progress_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3450 if dispatch_gate_decision.decision == "defer" else 2550
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif progress_watch_active:
            controller_key = "remaining_line_progress_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2550 if dispatch_gate_decision.decision == "defer" else 1650
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif stability_recenter_active:
            controller_key = "remaining_line_stability_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3600 if dispatch_gate_decision.decision == "defer" else 2700
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif stability_watch_active:
            controller_key = "remaining_line_stability_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2700 if dispatch_gate_decision.decision == "defer" else 1800
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif pressure_recenter_active:
            controller_key = "remaining_line_pressure_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 2400 if dispatch_gate_decision.decision == "defer" else 1800
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif pressure_watch_active:
            controller_key = "remaining_line_pressure_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 1800 if dispatch_gate_decision.decision == "defer" else 1200
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif trust_recenter_active:
            controller_key = "remaining_line_trust_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 1800 if dispatch_gate_decision.decision == "defer" else 1200
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif trust_watch_active:
            controller_key = "remaining_line_trust_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 1200 if dispatch_gate_decision.decision == "defer" else 900
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif continuity_recenter_active:
            controller_key = "remaining_line_continuity_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 1200 if dispatch_gate_decision.decision == "defer" else 900
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif continuity_watch_active:
            controller_key = "remaining_line_continuity_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 900 if dispatch_gate_decision.decision == "defer" else 600
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif repair_recenter_active:
            controller_key = "remaining_line_repair_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 900 if dispatch_gate_decision.decision == "defer" else 600
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif repair_watch_active:
            controller_key = "remaining_line_repair_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 600 if dispatch_gate_decision.decision == "defer" else 450
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif relational_recenter_active:
            controller_key = "remaining_line_relational_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 750 if dispatch_gate_decision.decision == "defer" else 450
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_recenter",
                    "favor_close_ready_shape",
                ]
            )
        elif relational_watch_active:
            controller_key = "remaining_line_relational_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 450 if dispatch_gate_decision.decision == "defer" else 300
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_watch",
                    "favor_close_ready_shape",
                ]
            )
        elif guidance_recenter_active:
            controller_key = "remaining_line_guidance_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 900 if dispatch_gate_decision.decision == "defer" else 600
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_recenter:{guidance_summary}",
                    "favor_close_ready_shape",
                ]
            )
        elif guidance_watch_active:
            controller_key = "remaining_line_guidance_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 600 if dispatch_gate_decision.decision == "defer" else 450
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_watch:{guidance_summary}",
                    "favor_close_ready_shape",
                ]
            )
        elif ritual_recenter_active:
            controller_key = "remaining_line_ritual_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 750 if dispatch_gate_decision.decision == "defer" else 600
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"ritual_somatic_recenter:{ritual_summary}",
                    "favor_close_ready_shape",
                ]
            )
        elif ritual_watch_active:
            controller_key = "remaining_line_ritual_watch_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 450 if dispatch_gate_decision.decision == "defer" else 300
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"ritual_somatic_watch:{ritual_summary}",
                    "favor_close_ready_shape",
                ]
            )
        elif (
            dispatch_feedback_assessment.changed
            or stage_controller_decision.changed
            or dispatch_gate_decision.decision == "defer"
            or stage_replan_assessment.selected_pressure_mode in {"gentle_resume", "repair_soft"}
            or stage_replan_assessment.selected_autonomy_signal
            in {"explicit_no_pressure", "archive_light_thread"}
        ):
            controller_key = "remaining_line_close_ready"
            line_state = "close_ready"
            decision = "retire_after_close_loop"
            changed = True
            additional_delay_seconds = 3600 if dispatch_gate_decision.decision == "defer" else 1800
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "remaining_line_should_finish_lightly",
                    "favor_close_ready_shape",
                ]
            )

    rationale = (
        "The remaining proactive line can keep its planned posture because the current "
        "stage did not create enough pressure to reshape everything that follows."
    )
    if changed:
        rationale = (
            "The remaining proactive line should now shift as a whole toward a lower-"
            "pressure posture so later touches inherit softer delivery and autonomy "
            "without each stage rediscovering that from scratch."
        )

    return ProactiveLineControllerDecision(
        status="active",
        controller_key=controller_key,
        trigger_stage_label=current_stage_label,
        line_state=line_state,
        decision=decision,
        changed=changed,
        affected_stage_labels=list(remaining_stage_labels),
        additional_delay_seconds=additional_delay_seconds,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        controller_notes=_compact(controller_notes, limit=5),
        rationale=rationale,
    )
