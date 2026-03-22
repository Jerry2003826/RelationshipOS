"""Proactive controllers: stage controller."""

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
    ProactiveFollowupDirective,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


def build_proactive_stage_controller_decision(
    *,
    directive: ProactiveFollowupDirective,
    proactive_cadence_plan: ProactiveCadencePlan,
    system3_snapshot: System3Snapshot,
    current_stage_label: str,
    current_stage_index: int,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    guidance_plan: GuidancePlan | None = None,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
) -> ProactiveStageControllerDecision:
    if directive.status != "ready" or not directive.eligible:
        return ProactiveStageControllerDecision(
            status="hold",
            controller_key="hold",
            trigger_stage_label=current_stage_label or "unknown",
            target_stage_label=None,
            decision="hold",
            changed=False,
            additional_delay_seconds=0,
            selected_strategy_key="hold",
            selected_pressure_mode="hold",
            selected_autonomy_signal="none",
            selected_delivery_mode="none",
            rationale=directive.rationale,
        )

    stage_labels = list(proactive_cadence_plan.stage_labels or [current_stage_label])
    stage_count = max(
        1,
        proactive_cadence_plan.close_after_stage_index or len(stage_labels) or 1,
    )
    next_stage_label = (
        stage_labels[current_stage_index]
        if current_stage_index < min(stage_count, len(stage_labels))
        else None
    )

    if not next_stage_label:
        return ProactiveStageControllerDecision(
            status="terminal",
            controller_key=f"{current_stage_label}_line_closed",
            trigger_stage_label=current_stage_label,
            target_stage_label=None,
            decision="close_line",
            changed=False,
            additional_delay_seconds=0,
            selected_strategy_key=stage_replan_assessment.selected_strategy_key,
            selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
            selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
            selected_delivery_mode=stage_replan_assessment.selected_delivery_mode,
            rationale=(
                "The current stage already closed the proactive line, so there is no "
                "next stage to schedule."
            ),
        )

    controller_key = f"{next_stage_label}_follow_planned_stage"
    decision = "follow_planned_stage"
    changed = False
    additional_delay_seconds = 0
    selected_strategy_key = stage_replan_assessment.selected_strategy_key
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
        and not commitment_recenter_active
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
        and not commitment_watch_active
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
        and not commitment_recenter_active
        and not commitment_recenter_active
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
        and not commitment_watch_active
        and not commitment_watch_active
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
        and not commitment_recenter_active
        and not commitment_recenter_active
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
        and not commitment_watch_active
        and not commitment_watch_active
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
    guidance_autonomy_signal = (
        "explicit_no_pressure"
        if guidance_plan is not None
        and guidance_plan.handoff_mode
        in {
            "repair_soft_ping",
            "no_pressure_checkin",
            "autonomy_preserving_ping",
            "wait_for_reply",
        }
        else "light_invitation"
    )
    ritual_somatic_gate = _build_proactive_ritual_somatic_gate(
        session_ritual_plan,
        somatic_orchestration_plan,
    )
    ritual_recenter_active = ritual_somatic_gate["status"] == "recenter"
    ritual_watch_active = ritual_somatic_gate["status"] == "watch"
    ritual_summary = str(ritual_somatic_gate["summary"])
    ritual_repair_soft = bool(
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
        )
    )
    ritual_autonomy_signal = (
        "explicit_no_pressure"
        if session_ritual_plan is not None
        and session_ritual_plan.closing_move
        in {
            "repair_soft_close",
            "boundary_safe_close",
            "grounding_close",
            "clarify_pause",
        }
        else "light_invitation"
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

    if next_stage_label == "second_touch":
        if (
            orchestration_controller_decision is not None
            and orchestration_controller_decision.status == "active"
            and orchestration_controller_decision.changed
            and orchestration_controller_decision.next_stage_label == "second_touch"
            and orchestration_controller_decision.stage_additional_delay_seconds > 0
        ):
            controller_key = (
                "second_touch_orchestration_recenter_spacing"
                if orchestration_controller_decision.decision == "recenter_followup_line"
                else "second_touch_orchestration_watch_spacing"
            )
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = (
                orchestration_controller_decision.stage_additional_delay_seconds
            )
            selected_strategy_key = orchestration_controller_decision.selected_strategy_key
            selected_pressure_mode = orchestration_controller_decision.selected_pressure_mode
            selected_autonomy_signal = orchestration_controller_decision.selected_autonomy_signal
            selected_delivery_mode = orchestration_controller_decision.selected_delivery_mode
            controller_notes.extend(list(orchestration_controller_decision.controller_notes))
        elif (
            aggregate_controller_decision is not None
            and aggregate_controller_decision.status == "active"
            and aggregate_controller_decision.changed
            and aggregate_controller_decision.next_stage_label == "second_touch"
            and aggregate_controller_decision.stage_additional_delay_seconds > 0
        ):
            controller_key = (
                "second_touch_aggregate_governance_buffer_spacing"
                if aggregate_controller_decision.decision == "recenter_followup_line"
                else "second_touch_aggregate_governance_watch_spacing"
            )
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = aggregate_controller_decision.stage_additional_delay_seconds
            selected_strategy_key = aggregate_controller_decision.selected_strategy_key
            selected_pressure_mode = aggregate_controller_decision.selected_pressure_mode
            selected_autonomy_signal = aggregate_controller_decision.selected_autonomy_signal
            selected_delivery_mode = aggregate_controller_decision.selected_delivery_mode
            controller_notes.extend(list(aggregate_controller_decision.controller_notes))
        elif aggregate_recenter_active:
            controller_key = "second_touch_aggregate_governance_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 6300
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_recenter:{aggregate_governance_summary}",
                    "space_out_second_touch",
                ]
            )
        elif aggregate_watch_active:
            controller_key = "second_touch_aggregate_governance_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4050
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_watch:{aggregate_governance_summary}",
                    "space_out_second_touch",
                ]
            )
        elif safety_recenter_active:
            controller_key = "second_touch_safety_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 7200
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif safety_watch_active:
            controller_key = "second_touch_safety_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5400
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif autonomy_recenter_active:
            controller_key = "second_touch_autonomy_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 6000
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif autonomy_watch_active:
            controller_key = "second_touch_autonomy_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4200
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif boundary_recenter_active:
            controller_key = "second_touch_boundary_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5700
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif boundary_watch_active:
            controller_key = "second_touch_boundary_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3900
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif support_recenter_active:
            controller_key = "second_touch_support_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5100
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif support_watch_active:
            controller_key = "second_touch_support_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3300
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif clarity_recenter_active:
            controller_key = "second_touch_clarity_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4800
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif clarity_watch_active:
            controller_key = "second_touch_clarity_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3000
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif pacing_recenter_active:
            controller_key = "second_touch_pacing_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4500
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif pacing_watch_active:
            controller_key = "second_touch_pacing_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2700
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif attunement_recenter_active:
            controller_key = "second_touch_attunement_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4950
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif attunement_watch_active:
            controller_key = "second_touch_attunement_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3150
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif commitment_recenter_active:
            controller_key = "second_touch_commitment_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif commitment_watch_active:
            controller_key = "second_touch_commitment_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif disclosure_recenter_active:
            controller_key = "second_touch_disclosure_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif disclosure_watch_active:
            controller_key = "second_touch_disclosure_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif reciprocity_recenter_active:
            controller_key = "second_touch_reciprocity_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif reciprocity_watch_active:
            controller_key = "second_touch_reciprocity_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif progress_recenter_active:
            controller_key = "second_touch_progress_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif progress_watch_active:
            controller_key = "second_touch_progress_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif stability_recenter_active:
            controller_key = "second_touch_stability_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5400
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif stability_watch_active:
            controller_key = "second_touch_stability_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3600
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif pressure_recenter_active:
            controller_key = "second_touch_pressure_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4500
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif pressure_watch_active:
            controller_key = "second_touch_pressure_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2700
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif trust_recenter_active:
            controller_key = "second_touch_trust_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3600
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif trust_watch_active:
            controller_key = "second_touch_trust_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2100
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif continuity_recenter_active:
            controller_key = "second_touch_continuity_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3000
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif continuity_watch_active:
            controller_key = "second_touch_continuity_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1800
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif repair_recenter_active:
            controller_key = "second_touch_repair_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2700
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif repair_watch_active:
            controller_key = "second_touch_repair_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1500
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif relational_recenter_active:
            controller_key = "second_touch_relational_buffer_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2400
            selected_strategy_key = "repair_soft_resume_bridge"
            selected_pressure_mode = "repair_soft"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_recenter",
                    "space_out_second_touch",
                ]
            )
        elif relational_watch_active:
            controller_key = "second_touch_relational_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1200
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_watch",
                    "space_out_second_touch",
                ]
            )
        elif guidance_recenter_active:
            controller_key = "second_touch_guidance_recenter_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2100
            selected_strategy_key = (
                "repair_soft_resume_bridge" if guidance_repair_soft else "resume_context_bridge"
            )
            selected_pressure_mode = "repair_soft" if guidance_repair_soft else "gentle_resume"
            selected_autonomy_signal = guidance_autonomy_signal
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_recenter:{guidance_summary}",
                    "space_out_second_touch",
                ]
            )
        elif guidance_watch_active:
            controller_key = "second_touch_guidance_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1200
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = guidance_autonomy_signal
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_watch:{guidance_summary}",
                    "space_out_second_touch",
                ]
            )
        elif ritual_recenter_active:
            controller_key = "second_touch_ritual_recenter_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1500
            selected_strategy_key = (
                "repair_soft_resume_bridge" if ritual_repair_soft else "resume_context_bridge"
            )
            selected_pressure_mode = "repair_soft" if ritual_repair_soft else "gentle_resume"
            selected_autonomy_signal = ritual_autonomy_signal
            selected_delivery_mode = ritual_delivery_mode
            controller_notes.extend(
                [
                    f"ritual_somatic_recenter:{ritual_summary}",
                    "space_out_second_touch",
                ]
            )
        elif ritual_watch_active:
            controller_key = "second_touch_ritual_watch_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 900
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = ritual_autonomy_signal
            selected_delivery_mode = ritual_delivery_mode
            controller_notes.extend(
                [
                    f"ritual_somatic_watch:{ritual_summary}",
                    "space_out_second_touch",
                ]
            )
        elif (
            dispatch_feedback_assessment.changed
            or stage_replan_assessment.selected_autonomy_signal
            in {
                "explicit_opt_out",
                "explicit_no_pressure",
            }
            or stage_replan_assessment.selected_pressure_mode
            in {"low_pressure_progress", "gentle_resume", "repair_soft"}
        ):
            controller_key = "second_touch_low_pressure_spacing"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = (
                5400
                if stage_replan_assessment.selected_pressure_mode
                in {"gentle_resume", "repair_soft"}
                else 3600
            )
            selected_strategy_key = "resume_context_bridge"
            selected_pressure_mode = "gentle_resume"
            selected_autonomy_signal = "explicit_no_pressure"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "first_touch_already_landed",
                    "space_out_second_touch",
                ]
            )
    elif next_stage_label == "final_soft_close":
        if (
            orchestration_controller_decision is not None
            and orchestration_controller_decision.status == "active"
            and orchestration_controller_decision.changed
            and orchestration_controller_decision.next_stage_label == "final_soft_close"
            and orchestration_controller_decision.stage_additional_delay_seconds > 0
        ):
            controller_key = (
                "final_soft_close_orchestration_recenter_buffer"
                if orchestration_controller_decision.decision == "recenter_followup_line"
                else "final_soft_close_orchestration_watch_buffer"
            )
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = (
                orchestration_controller_decision.stage_additional_delay_seconds
            )
            selected_strategy_key = orchestration_controller_decision.selected_strategy_key
            selected_pressure_mode = orchestration_controller_decision.selected_pressure_mode
            selected_autonomy_signal = orchestration_controller_decision.selected_autonomy_signal
            selected_delivery_mode = orchestration_controller_decision.selected_delivery_mode
            controller_notes.extend(list(orchestration_controller_decision.controller_notes))
        elif (
            aggregate_controller_decision is not None
            and aggregate_controller_decision.status == "active"
            and aggregate_controller_decision.changed
            and aggregate_controller_decision.next_stage_label == "final_soft_close"
            and aggregate_controller_decision.stage_additional_delay_seconds > 0
        ):
            controller_key = (
                "final_soft_close_aggregate_governance_buffer"
                if aggregate_controller_decision.decision == "recenter_followup_line"
                else "final_soft_close_aggregate_governance_watch_buffer"
            )
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = aggregate_controller_decision.stage_additional_delay_seconds
            selected_strategy_key = aggregate_controller_decision.selected_strategy_key
            selected_pressure_mode = aggregate_controller_decision.selected_pressure_mode
            selected_autonomy_signal = aggregate_controller_decision.selected_autonomy_signal
            selected_delivery_mode = aggregate_controller_decision.selected_delivery_mode
            controller_notes.extend(list(aggregate_controller_decision.controller_notes))
        elif aggregate_recenter_active:
            controller_key = "final_soft_close_aggregate_governance_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5700
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_recenter:{aggregate_governance_summary}",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif aggregate_watch_active:
            controller_key = "final_soft_close_aggregate_governance_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3900
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"aggregate_governance_watch:{aggregate_governance_summary}",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif safety_recenter_active:
            controller_key = "final_soft_close_safety_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 7200
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif safety_watch_active:
            controller_key = "final_soft_close_safety_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5400
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "safety_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif autonomy_recenter_active:
            controller_key = "final_soft_close_autonomy_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 6000
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif autonomy_watch_active:
            controller_key = "final_soft_close_autonomy_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4200
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "autonomy_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif boundary_recenter_active:
            controller_key = "final_soft_close_boundary_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5700
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif boundary_watch_active:
            controller_key = "final_soft_close_boundary_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3900
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "boundary_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif support_recenter_active:
            controller_key = "final_soft_close_support_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5100
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif support_watch_active:
            controller_key = "final_soft_close_support_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3300
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "support_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif clarity_recenter_active:
            controller_key = "final_soft_close_clarity_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4800
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif clarity_watch_active:
            controller_key = "final_soft_close_clarity_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3000
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "clarity_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif pacing_recenter_active:
            controller_key = "final_soft_close_pacing_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4500
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif pacing_watch_active:
            controller_key = "final_soft_close_pacing_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2700
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pacing_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif attunement_recenter_active:
            controller_key = "final_soft_close_attunement_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4950
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif attunement_watch_active:
            controller_key = "final_soft_close_attunement_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3150
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "attunement_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif commitment_recenter_active:
            controller_key = "final_soft_close_commitment_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif commitment_watch_active:
            controller_key = "final_soft_close_commitment_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "commitment_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif disclosure_recenter_active:
            controller_key = "final_soft_close_disclosure_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif disclosure_watch_active:
            controller_key = "final_soft_close_disclosure_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "disclosure_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif reciprocity_recenter_active:
            controller_key = "final_soft_close_reciprocity_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif reciprocity_watch_active:
            controller_key = "final_soft_close_reciprocity_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "reciprocity_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif progress_recenter_active:
            controller_key = "final_soft_close_progress_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5250
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif progress_watch_active:
            controller_key = "final_soft_close_progress_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3450
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "progress_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif stability_recenter_active:
            controller_key = "final_soft_close_stability_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 5400
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif stability_watch_active:
            controller_key = "final_soft_close_stability_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3600
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "stability_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif pressure_recenter_active:
            controller_key = "final_soft_close_pressure_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 4500
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif pressure_watch_active:
            controller_key = "final_soft_close_pressure_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2700
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "pressure_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif trust_recenter_active:
            controller_key = "final_soft_close_trust_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3600
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif trust_watch_active:
            controller_key = "final_soft_close_trust_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2100
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "trust_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif continuity_recenter_active:
            controller_key = "final_soft_close_continuity_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 3000
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif continuity_watch_active:
            controller_key = "final_soft_close_continuity_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1800
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "continuity_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif repair_recenter_active:
            controller_key = "final_soft_close_repair_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2700
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif repair_watch_active:
            controller_key = "final_soft_close_repair_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1500
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "repair_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif relational_recenter_active:
            controller_key = "final_soft_close_relational_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 2400
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_recenter",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif relational_watch_active:
            controller_key = "final_soft_close_relational_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1200
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "relational_governance_watch",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif guidance_recenter_active:
            controller_key = "final_soft_close_guidance_recenter_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1800
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_recenter:{guidance_summary}",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif guidance_watch_active:
            controller_key = "final_soft_close_guidance_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 900
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"guidance_watch:{guidance_summary}",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif ritual_recenter_active:
            controller_key = "final_soft_close_ritual_recenter_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 1200
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"ritual_somatic_recenter:{ritual_summary}",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif ritual_watch_active:
            controller_key = "final_soft_close_ritual_watch_buffer"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = 600
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    f"ritual_somatic_watch:{ritual_summary}",
                    "leave_more_breathing_room_before_close",
                ]
            )
        elif (
            dispatch_feedback_assessment.changed
            or stage_replan_assessment.selected_pressure_mode in {"gentle_resume", "repair_soft"}
            or stage_replan_assessment.selected_autonomy_signal
            in {"explicit_no_pressure", "archive_light_thread"}
        ):
            controller_key = "final_soft_close_breathing_room"
            decision = "slow_next_stage"
            changed = True
            additional_delay_seconds = (
                7200 if stage_replan_assessment.selected_pressure_mode == "repair_soft" else 5400
            )
            selected_strategy_key = "continuity_soft_ping"
            selected_pressure_mode = "archive_light_presence"
            selected_autonomy_signal = "archive_light_thread"
            selected_delivery_mode = "single_message"
            controller_notes.extend(
                [
                    "later_touch_should_not_chase",
                    "leave_more_breathing_room_before_close",
                ]
            )

    rationale = (
        "The next proactive stage can keep its planned timing because the current "
        "dispatch did not introduce extra pressure that needs spacing correction."
    )
    if changed:
        rationale = (
            "The next proactive stage should be slowed down so the multi-stage line "
            "keeps shedding pressure instead of escalating just because the next slot exists."
        )

    return ProactiveStageControllerDecision(
        status="active",
        controller_key=controller_key,
        trigger_stage_label=current_stage_label,
        target_stage_label=next_stage_label,
        decision=decision,
        changed=changed,
        additional_delay_seconds=additional_delay_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_delivery_mode=selected_delivery_mode,
        controller_notes=_compact(controller_notes, limit=5),
        rationale=rationale,
    )

