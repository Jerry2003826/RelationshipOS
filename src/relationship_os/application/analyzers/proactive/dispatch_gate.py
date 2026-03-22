"""Proactive dispatch: gate decision and envelope decision."""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.dispatch_planning import (
    _build_proactive_aggregate_governance_gate,
    _build_proactive_guidance_gate,
    _build_proactive_ritual_somatic_gate,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveAggregateControllerDecision,
    ProactiveAggregateGovernanceAssessment,
    ProactiveDispatchEnvelopeDecision,
    ProactiveDispatchFeedbackAssessment,
    ProactiveDispatchGateDecision,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveOrchestrationControllerDecision,
    ProactiveStageControllerDecision,
    ProactiveStageRefreshPlan,
    ProactiveStageReplanAssessment,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)


def build_proactive_dispatch_gate_decision(
    *,
    directive: ProactiveFollowupDirective,
    guidance_plan: GuidancePlan,
    system3_snapshot: System3Snapshot,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    queue_status: str,
    schedule_reason: str | None,
    progression_advanced: bool,
    aggregate_governance_assessment: ProactiveAggregateGovernanceAssessment | None = None,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    session_ritual_plan: SessionRitualPlan | None = None,
    somatic_orchestration_plan: SomaticOrchestrationPlan | None = None,
) -> ProactiveDispatchGateDecision:
    """Build gate decision controlling whether the current proactive stage dispatches."""
    if directive.status != "ready" or not directive.eligible:
        return ProactiveDispatchGateDecision(
            status="hold",
            gate_key="hold",
            stage_label=stage_replan_assessment.stage_label or "unknown",
            dispatch_window_status=stage_replan_assessment.dispatch_window_status,
            decision="hold",
            changed=False,
            retry_after_seconds=0,
            selected_strategy_key=stage_replan_assessment.selected_strategy_key,
            selected_pressure_mode=stage_replan_assessment.selected_pressure_mode,
            selected_autonomy_signal=stage_replan_assessment.selected_autonomy_signal,
            rationale=directive.rationale,
        )

    stage_label = stage_replan_assessment.stage_label or "first_touch"
    dispatch_window_status = stage_replan_assessment.dispatch_window_status or "on_time_dispatch"
    selected_strategy_key = stage_replan_assessment.selected_strategy_key
    selected_pressure_mode = stage_replan_assessment.selected_pressure_mode
    selected_autonomy_signal = stage_replan_assessment.selected_autonomy_signal
    schedule_reason_text = str(schedule_reason or "")
    gate_notes: list[str] = []
    decision = "dispatch"
    changed = False
    retry_after_seconds = 0
    gate_key = f"{stage_label}_dispatch_clear"

    low_pressure_handoff = guidance_plan.handoff_mode in {
        "no_pressure_checkin",
        "repair_soft_ping",
        "autonomy_preserving_ping",
    }
    guidance_gate = _build_proactive_guidance_gate(guidance_plan)
    guidance_recenter_active = guidance_gate["status"] == "recenter"
    guidance_watch_active = guidance_gate["status"] == "watch"
    guidance_summary = str(guidance_gate["summary"])
    ritual_somatic_gate = _build_proactive_ritual_somatic_gate(
        session_ritual_plan,
        somatic_orchestration_plan,
    )
    ritual_recenter_active = ritual_somatic_gate["status"] == "recenter"
    ritual_watch_active = ritual_somatic_gate["status"] == "watch"
    ritual_summary = str(ritual_somatic_gate["summary"])
    already_gate_deferred = "dispatch_gate:" in schedule_reason_text
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

    if (
        stage_label == "final_soft_close"
        and not already_gate_deferred
        and selected_strategy_key in {"continuity_soft_ping", "repair_soft_reentry"}
        and (
            safety_recenter_active
            or safety_watch_active
            or autonomy_recenter_active
            or autonomy_watch_active
            or boundary_recenter_active
            or boundary_watch_active
            or support_recenter_active
            or support_watch_active
            or clarity_recenter_active
            or clarity_watch_active
            or pacing_recenter_active
            or pacing_watch_active
            or attunement_recenter_active
            or attunement_watch_active
            or commitment_recenter_active
            or commitment_watch_active
            or disclosure_recenter_active
            or disclosure_watch_active
            or reciprocity_recenter_active
            or reciprocity_watch_active
            or progress_recenter_active
            or progress_watch_active
            or stability_recenter_active
            or stability_watch_active
            or pressure_recenter_active
            or pressure_watch_active
            or trust_recenter_active
            or trust_watch_active
            or continuity_recenter_active
            or continuity_watch_active
            or repair_recenter_active
            or repair_watch_active
            or relational_recenter_active
            or relational_watch_active
            or guidance_recenter_active
            or guidance_watch_active
            or ritual_recenter_active
            or ritual_watch_active
            or (
                orchestration_controller_decision is not None
                and orchestration_controller_decision.status == "active"
                and orchestration_controller_decision.changed
                and orchestration_controller_decision.dispatch_retry_after_seconds > 0
            )
            or aggregate_recenter_active
            or aggregate_watch_active
            or progression_advanced
            or "guardrail:" in schedule_reason_text
            or dispatch_window_status in {"progressed_dispatch", "guarded_release"}
        )
    ):
        decision = "defer"
        changed = True
        if (
            orchestration_controller_decision is not None
            and orchestration_controller_decision.status == "active"
            and orchestration_controller_decision.changed
            and orchestration_controller_decision.dispatch_retry_after_seconds > 0
        ):
            retry_after_seconds = orchestration_controller_decision.dispatch_retry_after_seconds
            gate_key = (
                "final_soft_close_orchestration_extra_space"
                if orchestration_controller_decision.decision == "recenter_followup_line"
                else "final_soft_close_orchestration_watch_space"
            )
            gate_notes.extend(list(orchestration_controller_decision.controller_notes))
        elif (
            aggregate_controller_decision is not None
            and aggregate_controller_decision.status == "active"
            and aggregate_controller_decision.changed
            and aggregate_controller_decision.dispatch_retry_after_seconds > 0
        ):
            retry_after_seconds = aggregate_controller_decision.dispatch_retry_after_seconds
            gate_key = (
                "final_soft_close_governance_extra_space"
                if aggregate_controller_decision.decision == "recenter_followup_line"
                else "final_soft_close_governance_watch_space"
            )
            gate_notes.extend(list(aggregate_controller_decision.controller_notes))
        elif aggregate_recenter_active:
            retry_after_seconds = (
                3000
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 2100
            )
            gate_key = "final_soft_close_governance_extra_space"
            gate_notes.extend(
                [
                    f"aggregate_governance_recenter:{aggregate_governance_summary}",
                    "one_more_space_before_soft_close",
                ]
            )
        elif aggregate_watch_active:
            retry_after_seconds = (
                2100
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1500
            )
            gate_key = "final_soft_close_governance_watch_space"
            gate_notes.extend(
                [
                    f"aggregate_governance_watch:{aggregate_governance_summary}",
                    "one_more_space_before_soft_close",
                ]
            )
        elif safety_recenter_active:
            retry_after_seconds = (
                3600
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 2700
            )
            gate_key = "final_soft_close_safety_extra_space"
            gate_notes.extend(["final_stage_safety_delay", "one_more_space_before_soft_close"])
        elif safety_watch_active:
            retry_after_seconds = (
                2700
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_safety_watch_space"
            gate_notes.extend(
                ["final_stage_safety_watch_delay", "one_more_space_before_soft_close"]
            )
        elif autonomy_recenter_active:
            retry_after_seconds = (
                3000
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 2100
            )
            gate_key = "final_soft_close_autonomy_extra_space"
            gate_notes.extend(["final_stage_autonomy_delay", "one_more_space_before_soft_close"])
        elif autonomy_watch_active:
            retry_after_seconds = 2100
            gate_key = "final_soft_close_autonomy_watch_space"
            gate_notes.extend(
                ["final_stage_autonomy_watch_delay", "one_more_space_before_soft_close"]
            )
        elif boundary_recenter_active:
            retry_after_seconds = (
                2700
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_boundary_extra_space"
            gate_notes.extend(["final_stage_boundary_delay", "one_more_space_before_soft_close"])
        elif boundary_watch_active:
            retry_after_seconds = 1800
            gate_key = "final_soft_close_boundary_watch_space"
            gate_notes.extend(
                ["final_stage_boundary_watch_delay", "one_more_space_before_soft_close"]
            )
        elif support_recenter_active:
            retry_after_seconds = (
                2400
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1500
            )
            gate_key = "final_soft_close_support_extra_space"
            gate_notes.extend(["final_stage_support_delay", "one_more_space_before_soft_close"])
        elif support_watch_active:
            retry_after_seconds = 1500
            gate_key = "final_soft_close_support_watch_space"
            gate_notes.extend(
                ["final_stage_support_watch_delay", "one_more_space_before_soft_close"]
            )
        elif clarity_recenter_active:
            retry_after_seconds = (
                2100
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1200
            )
            gate_key = "final_soft_close_clarity_extra_space"
            gate_notes.extend(["final_stage_clarity_delay", "one_more_space_before_soft_close"])
        elif clarity_watch_active:
            retry_after_seconds = 1200
            gate_key = "final_soft_close_clarity_watch_space"
            gate_notes.extend(
                ["final_stage_clarity_watch_delay", "one_more_space_before_soft_close"]
            )
        elif pacing_recenter_active:
            retry_after_seconds = (
                1800
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1200
            )
            gate_key = "final_soft_close_pacing_extra_space"
            gate_notes.extend(["final_stage_pacing_delay", "one_more_space_before_soft_close"])
        elif pacing_watch_active:
            retry_after_seconds = 1200
            gate_key = "final_soft_close_pacing_watch_space"
            gate_notes.extend(
                ["final_stage_pacing_watch_delay", "one_more_space_before_soft_close"]
            )
        elif attunement_recenter_active:
            retry_after_seconds = (
                2100
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1500
            )
            gate_key = "final_soft_close_attunement_extra_space"
            gate_notes.extend(["final_stage_attunement_delay", "one_more_space_before_soft_close"])
        elif attunement_watch_active:
            retry_after_seconds = 1500
            gate_key = "final_soft_close_attunement_watch_space"
            gate_notes.extend(
                ["final_stage_attunement_watch_delay", "one_more_space_before_soft_close"]
            )
        elif commitment_recenter_active:
            retry_after_seconds = (
                2400
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_commitment_extra_space"
            gate_notes.extend(["final_stage_commitment_delay", "one_more_space_before_soft_close"])
        elif commitment_watch_active:
            retry_after_seconds = 1800
            gate_key = "final_soft_close_commitment_watch_space"
            gate_notes.extend(
                ["final_stage_commitment_watch_delay", "one_more_space_before_soft_close"]
            )
        elif disclosure_recenter_active:
            retry_after_seconds = (
                2400
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_disclosure_extra_space"
            gate_notes.extend(["final_stage_disclosure_delay", "one_more_space_before_soft_close"])
        elif disclosure_watch_active:
            retry_after_seconds = 1800
            gate_key = "final_soft_close_disclosure_watch_space"
            gate_notes.extend(
                ["final_stage_disclosure_watch_delay", "one_more_space_before_soft_close"]
            )
        elif reciprocity_recenter_active:
            retry_after_seconds = (
                2400
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_reciprocity_extra_space"
            gate_notes.extend(["final_stage_reciprocity_delay", "one_more_space_before_soft_close"])
        elif reciprocity_watch_active:
            retry_after_seconds = 1800
            gate_key = "final_soft_close_reciprocity_watch_space"
            gate_notes.extend(
                ["final_stage_reciprocity_watch_delay", "one_more_space_before_soft_close"]
            )
        elif progress_recenter_active:
            retry_after_seconds = (
                2400
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_progress_extra_space"
            gate_notes.extend(["final_stage_progress_delay", "one_more_space_before_soft_close"])
        elif progress_watch_active:
            retry_after_seconds = 1800
            gate_key = "final_soft_close_progress_watch_space"
            gate_notes.extend(
                ["final_stage_progress_watch_delay", "one_more_space_before_soft_close"]
            )
        elif stability_recenter_active:
            retry_after_seconds = (
                2700
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_stability_extra_space"
            gate_notes.extend(["final_stage_stability_delay", "one_more_space_before_soft_close"])
        elif stability_watch_active:
            retry_after_seconds = 1800
            gate_key = "final_soft_close_stability_watch_space"
            gate_notes.extend(
                ["final_stage_stability_watch_delay", "one_more_space_before_soft_close"]
            )
        elif pressure_recenter_active:
            retry_after_seconds = (
                1800
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1200
            )
            gate_key = "final_soft_close_pressure_extra_space"
            gate_notes.extend(["final_stage_pressure_delay", "one_more_space_before_soft_close"])
        elif pressure_watch_active:
            retry_after_seconds = 1200
            gate_key = "final_soft_close_pressure_watch_space"
            gate_notes.extend(
                ["final_stage_pressure_watch_delay", "one_more_space_before_soft_close"]
            )
        elif trust_recenter_active:
            retry_after_seconds = (
                1500
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 900
            )
            gate_key = "final_soft_close_trust_extra_space"
            gate_notes.extend(["final_stage_trust_delay", "one_more_space_before_soft_close"])
        elif trust_watch_active:
            retry_after_seconds = 900
            gate_key = "final_soft_close_trust_watch_space"
            gate_notes.extend(["final_stage_trust_watch_delay", "one_more_space_before_soft_close"])
        elif continuity_recenter_active:
            retry_after_seconds = (
                1200
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 600
            )
            gate_key = "final_soft_close_continuity_extra_space"
            gate_notes.extend(["final_stage_continuity_delay", "one_more_space_before_soft_close"])
        elif continuity_watch_active:
            retry_after_seconds = 600
            gate_key = "final_soft_close_continuity_watch_space"
            gate_notes.extend(
                ["final_stage_continuity_watch_delay", "one_more_space_before_soft_close"]
            )
        elif repair_recenter_active:
            retry_after_seconds = (
                900
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 450
            )
            gate_key = "final_soft_close_repair_extra_space"
            gate_notes.extend(["final_stage_repair_delay", "one_more_space_before_soft_close"])
        elif repair_watch_active:
            retry_after_seconds = 450
            gate_key = "final_soft_close_repair_watch_space"
            gate_notes.extend(
                ["final_stage_repair_watch_delay", "one_more_space_before_soft_close"]
            )
        elif relational_recenter_active:
            retry_after_seconds = (
                750
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 300
            )
            gate_key = "final_soft_close_relational_extra_space"
            gate_notes.extend(["final_stage_relational_delay", "one_more_space_before_soft_close"])
        elif relational_watch_active:
            retry_after_seconds = 300
            gate_key = "final_soft_close_relational_watch_space"
            gate_notes.extend(
                ["final_stage_relational_watch_delay", "one_more_space_before_soft_close"]
            )
        elif guidance_recenter_active:
            retry_after_seconds = 900
            gate_key = "final_soft_close_guidance_extra_space"
            gate_notes.extend(
                [f"guidance_recenter:{guidance_summary}", "one_more_space_before_soft_close"]
            )
        elif guidance_watch_active:
            retry_after_seconds = 450
            gate_key = "final_soft_close_guidance_watch_space"
            gate_notes.extend(
                [f"guidance_watch:{guidance_summary}", "one_more_space_before_soft_close"]
            )
        elif ritual_recenter_active:
            retry_after_seconds = 600
            gate_key = "final_soft_close_ritual_extra_space"
            gate_notes.extend(
                [f"ritual_somatic_recenter:{ritual_summary}", "one_more_space_before_soft_close"]
            )
        elif ritual_watch_active:
            retry_after_seconds = 300
            gate_key = "final_soft_close_ritual_watch_space"
            gate_notes.extend(
                [f"ritual_somatic_watch:{ritual_summary}", "one_more_space_before_soft_close"]
            )
        else:
            retry_after_seconds = (
                2700
                if system3_snapshot.emotional_debt_status == "elevated"
                or selected_pressure_mode == "repair_soft"
                else 1800
            )
            gate_key = "final_soft_close_extra_space"
            gate_notes.extend(
                ["final_stage_low_pressure_delay", "one_more_space_before_soft_close"]
            )
    elif (
        stage_label == "second_touch"
        and not already_gate_deferred
        and selected_strategy_key == "repair_soft_resume_bridge"
        and queue_status in {"due", "overdue"}
        and (
            low_pressure_handoff or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
        )
    ):
        decision = "defer"
        changed = True
        retry_after_seconds = 1200
        gate_key = "second_touch_repair_space"
        gate_notes.append("repair_bridge_needs_more_user_space")

    rationale = (
        "The proactive dispatch can proceed because the current stage still fits the "
        "latest low-pressure envelope."
    )
    if decision == "defer":
        rationale = (
            "The proactive dispatch should pause once more so the current stage keeps "
            "its low-pressure shape instead of firing as soon as it becomes due."
        )

    return ProactiveDispatchGateDecision(
        status="active",
        gate_key=gate_key,
        stage_label=stage_label,
        dispatch_window_status=dispatch_window_status,
        decision=decision,
        changed=changed,
        retry_after_seconds=retry_after_seconds,
        selected_strategy_key=selected_strategy_key,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        gate_notes=_compact(gate_notes, limit=5),
        rationale=rationale,
    )


def build_proactive_dispatch_envelope_decision(
    *,
    stage_label: str,
    current_stage_directive: dict[str, Any] | None,
    current_stage_actuation: dict[str, Any] | None,
    stage_refresh_plan: ProactiveStageRefreshPlan,
    stage_replan_assessment: ProactiveStageReplanAssessment,
    dispatch_feedback_assessment: ProactiveDispatchFeedbackAssessment,
    dispatch_gate_decision: ProactiveDispatchGateDecision,
    aggregate_controller_decision: ProactiveAggregateControllerDecision | None = None,
    orchestration_controller_decision: ProactiveOrchestrationControllerDecision | None = None,
    stage_controller_decision: ProactiveStageControllerDecision | None = None,
    line_controller_decision: ProactiveLineControllerDecision | None = None,
) -> ProactiveDispatchEnvelopeDecision:
    """Build the final dispatch envelope merging all controller and gate outputs."""
    stage_label = (
        stage_label
        or stage_refresh_plan.stage_label
        or stage_replan_assessment.stage_label
        or "unknown"
    )
    current_stage_directive = current_stage_directive or {}
    current_stage_actuation = current_stage_actuation or {}

    selected_strategy_key = stage_replan_assessment.selected_strategy_key
    selected_ritual_mode = stage_replan_assessment.selected_ritual_mode
    selected_reengagement_delivery_mode = stage_replan_assessment.selected_delivery_mode
    selected_relational_move = stage_replan_assessment.selected_relational_move
    selected_pressure_mode = stage_replan_assessment.selected_pressure_mode
    selected_autonomy_signal = stage_replan_assessment.selected_autonomy_signal
    selected_sequence_objective = stage_replan_assessment.selected_sequence_objective
    selected_somatic_action = stage_replan_assessment.selected_somatic_action
    selected_stage_delivery_mode = stage_refresh_plan.refreshed_delivery_mode or str(
        current_stage_directive.get("delivery_mode") or "single_message"
    )
    selected_stage_question_mode = stage_refresh_plan.refreshed_question_mode or str(
        current_stage_directive.get("question_mode") or "statement_only"
    )
    selected_stage_autonomy_mode = stage_refresh_plan.refreshed_autonomy_mode or str(
        current_stage_directive.get("autonomy_mode") or "light_invitation"
    )
    selected_stage_objective = stage_replan_assessment.selected_sequence_objective or str(
        current_stage_directive.get("objective") or ""
    )
    selected_stage_closing_style = str(current_stage_directive.get("closing_style") or "none")
    selected_opening_move = stage_refresh_plan.refreshed_opening_move or str(
        current_stage_actuation.get("opening_move") or "none"
    )
    selected_bridge_move = stage_refresh_plan.refreshed_bridge_move or str(
        current_stage_actuation.get("bridge_move") or "none"
    )
    selected_closing_move = stage_refresh_plan.refreshed_closing_move or str(
        current_stage_actuation.get("closing_move") or "none"
    )
    selected_continuity_anchor = stage_refresh_plan.refreshed_continuity_anchor or str(
        current_stage_actuation.get("continuity_anchor") or "none"
    )
    selected_somatic_mode = stage_refresh_plan.refreshed_somatic_mode or str(
        current_stage_actuation.get("somatic_mode") or "none"
    )
    selected_somatic_body_anchor = str(
        current_stage_actuation.get("somatic_body_anchor")
        or current_stage_actuation.get("body_anchor")
        or "none"
    )
    selected_followup_style = str(current_stage_actuation.get("followup_style") or "none")
    selected_user_space_signal = stage_refresh_plan.refreshed_user_space_signal or str(
        current_stage_actuation.get("user_space_signal") or "none"
    )

    active_sources: list[str] = []
    envelope_notes: list[str] = []

    if stage_refresh_plan.changed:
        active_sources.append("refresh")
    if stage_replan_assessment.changed:
        active_sources.append("replan")
    if dispatch_feedback_assessment.changed:
        active_sources.append("feedback")
    if (
        aggregate_controller_decision is not None
        and aggregate_controller_decision.status == "active"
        and aggregate_controller_decision.changed
    ):
        active_sources.append("aggregate_controller")
    if (
        orchestration_controller_decision is not None
        and orchestration_controller_decision.status == "active"
        and orchestration_controller_decision.changed
    ):
        active_sources.append("orchestration_controller")
    if (
        stage_controller_decision is not None
        and stage_controller_decision.status == "active"
        and stage_controller_decision.changed
    ):
        active_sources.append("stage_controller")
    if (
        line_controller_decision is not None
        and line_controller_decision.status == "active"
        and line_controller_decision.changed
    ):
        active_sources.append("line_controller")
    if dispatch_gate_decision.changed or dispatch_gate_decision.decision != "dispatch":
        active_sources.append("gate")

    envelope_notes.extend(list(stage_refresh_plan.refresh_notes))
    envelope_notes.extend(list(stage_replan_assessment.replan_notes))
    envelope_notes.extend(list(dispatch_feedback_assessment.feedback_notes))
    envelope_notes.extend(list(dispatch_gate_decision.gate_notes))

    if (
        dispatch_gate_decision.selected_pressure_mode
        and dispatch_gate_decision.selected_pressure_mode != "none"
    ):
        selected_pressure_mode = dispatch_gate_decision.selected_pressure_mode
    if (
        dispatch_gate_decision.selected_autonomy_signal
        and dispatch_gate_decision.selected_autonomy_signal != "none"
    ):
        selected_autonomy_signal = dispatch_gate_decision.selected_autonomy_signal
        selected_stage_autonomy_mode = dispatch_gate_decision.selected_autonomy_signal

    if dispatch_gate_decision.decision == "hold":
        status = "hold"
        decision = "hold_dispatch"
    elif dispatch_gate_decision.decision == "defer":
        status = "scheduled"
        decision = "defer_dispatch"
    elif active_sources:
        status = "active"
        decision = "dispatch_shaped"
    else:
        status = "active"
        decision = "dispatch_as_planned"

    changed = bool(active_sources) or dispatch_gate_decision.decision != "dispatch"
    envelope_key = f"{stage_label}_{decision}_{selected_strategy_key}"
    if not changed:
        envelope_key = f"{stage_label}_dispatch_stable"

    rationale = (
        "The current proactive stage can dispatch with its current shape because the "
        "latest refresh, replan, and gate did not materially alter the envelope."
    )
    if decision == "dispatch_shaped":
        rationale = (
            "The current proactive stage should dispatch using the latest refreshed "
            "low-pressure envelope rather than the original stage defaults."
        )
    elif decision == "defer_dispatch":
        rationale = (
            "The current proactive stage should keep its final softened envelope, but "
            "the gate is deferring dispatch to leave more user space first."
        )
    elif decision == "hold_dispatch":
        rationale = (
            "The current proactive stage should not dispatch because the gate is "
            "holding the line entirely."
        )

    return ProactiveDispatchEnvelopeDecision(
        status=status,
        envelope_key=envelope_key,
        stage_label=stage_label,
        decision=decision,
        changed=changed,
        selected_strategy_key=selected_strategy_key,
        selected_ritual_mode=selected_ritual_mode,
        selected_reengagement_delivery_mode=selected_reengagement_delivery_mode,
        selected_relational_move=selected_relational_move,
        selected_pressure_mode=selected_pressure_mode,
        selected_autonomy_signal=selected_autonomy_signal,
        selected_sequence_objective=selected_sequence_objective,
        selected_somatic_action=selected_somatic_action,
        selected_stage_delivery_mode=selected_stage_delivery_mode,
        selected_stage_question_mode=selected_stage_question_mode,
        selected_stage_autonomy_mode=selected_stage_autonomy_mode,
        selected_stage_objective=selected_stage_objective,
        selected_stage_closing_style=selected_stage_closing_style,
        selected_opening_move=selected_opening_move,
        selected_bridge_move=selected_bridge_move,
        selected_closing_move=selected_closing_move,
        selected_continuity_anchor=selected_continuity_anchor,
        selected_somatic_mode=selected_somatic_mode,
        selected_somatic_body_anchor=selected_somatic_body_anchor,
        selected_followup_style=selected_followup_style,
        selected_user_space_signal=selected_user_space_signal,
        dispatch_retry_after_seconds=dispatch_gate_decision.retry_after_seconds,
        active_sources=_compact(active_sources, limit=6),
        envelope_notes=_compact(envelope_notes, limit=6),
        rationale=rationale,
    )
