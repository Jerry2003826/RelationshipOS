from dataclasses import replace

from relationship_os.application.analyzers import (
    build_proactive_aggregate_controller_decision,
    build_proactive_aggregate_governance_assessment,
    build_proactive_dispatch_envelope_decision,
    build_proactive_dispatch_gate_decision,
    build_proactive_line_controller_decision,
    build_proactive_line_machine_decision,
    build_proactive_line_state_decision,
    build_proactive_line_transition_decision,
    build_proactive_orchestration_controller_decision,
    build_proactive_stage_controller_decision,
    build_proactive_stage_machine_decision,
    build_proactive_stage_replan_assessment,
    build_proactive_stage_transition_decision,
)
from relationship_os.application.analyzers.proactive.lifecycle import (
    build_proactive_lifecycle_activation_decision,
    build_proactive_lifecycle_ancestry_decision,
    build_proactive_lifecycle_arming_decision,
    build_proactive_lifecycle_assurance_decision,
    build_proactive_lifecycle_attestation_decision,
    build_proactive_lifecycle_authorization_decision,
    build_proactive_lifecycle_availability_decision,
    build_proactive_lifecycle_bedrock_decision,
    build_proactive_lifecycle_candidate_decision,
    build_proactive_lifecycle_certification_decision,
    build_proactive_lifecycle_closure_decision,
    build_proactive_lifecycle_completion_decision,
    build_proactive_lifecycle_conclusion_decision,
    build_proactive_lifecycle_confirmation_decision,
    build_proactive_lifecycle_continuation_decision,
    build_proactive_lifecycle_controller_decision,
    build_proactive_lifecycle_dispatch_decision,
    build_proactive_lifecycle_disposition_decision,
    build_proactive_lifecycle_durability_decision,
    build_proactive_lifecycle_eligibility_decision,
    build_proactive_lifecycle_enactment_decision,
    build_proactive_lifecycle_endorsement_decision,
    build_proactive_lifecycle_envelope_decision,
    build_proactive_lifecycle_finality_decision,
    build_proactive_lifecycle_foundation_decision,
    build_proactive_lifecycle_guardianship_decision,
    build_proactive_lifecycle_handoff_decision,
    build_proactive_lifecycle_heritage_decision,
    build_proactive_lifecycle_launch_decision,
    build_proactive_lifecycle_layer_decision,
    build_proactive_lifecycle_legacy_decision,
    build_proactive_lifecycle_lineage_decision,
    build_proactive_lifecycle_longevity_decision,
    build_proactive_lifecycle_machine_decision,
    build_proactive_lifecycle_origin_decision,
    build_proactive_lifecycle_outcome_decision,
    build_proactive_lifecycle_oversight_decision,
    build_proactive_lifecycle_persistence_decision,
    build_proactive_lifecycle_provenance_decision,
    build_proactive_lifecycle_queue_decision,
    build_proactive_lifecycle_ratification_decision,
    build_proactive_lifecycle_reactivation_decision,
    build_proactive_lifecycle_readiness_decision,
    build_proactive_lifecycle_reentry_decision,
    build_proactive_lifecycle_residency_decision,
    build_proactive_lifecycle_resolution_decision,
    build_proactive_lifecycle_resumption_decision,
    build_proactive_lifecycle_retention_decision,
    build_proactive_lifecycle_root_decision,
    build_proactive_lifecycle_scheduler_decision,
    build_proactive_lifecycle_selectability_decision,
    build_proactive_lifecycle_settlement_decision,
    build_proactive_lifecycle_standing_decision,
    build_proactive_lifecycle_state_decision,
    build_proactive_lifecycle_stewardship_decision,
    build_proactive_lifecycle_stratum_decision,
    build_proactive_lifecycle_substrate_decision,
    build_proactive_lifecycle_sustainment_decision,
    build_proactive_lifecycle_tenure_decision,
    build_proactive_lifecycle_transition_decision,
    build_proactive_lifecycle_trigger_decision,
    build_proactive_lifecycle_verification_decision,
    build_proactive_lifecycle_window_decision,
)
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveCadencePlan,
    ProactiveDispatchFeedbackAssessment,
    ProactiveDispatchGateDecision,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveLineStateDecision,
    ProactiveLineTransitionDecision,
    ProactiveSchedulingPlan,
    ProactiveStageControllerDecision,
    ProactiveStageRefreshPlan,
    ProactiveStageReplanAssessment,
    ProactiveStageStateDecision,
    ReengagementPlan,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)
from relationship_os.domain.contracts.lifecycle import ProactiveLifecycleQueueDecision


def _system3_snapshot(**overrides: object) -> System3Snapshot:
    base = System3Snapshot(
        triggered_turn_index=1,
        identity_anchor="collaborative_reflective_support",
        identity_consistency="aligned",
        identity_confidence=0.92,
        growth_stage="working_alliance",
        growth_signal="steady_progress",
        user_model_confidence=0.84,
    )
    return replace(base, **overrides)


def _directive() -> ProactiveFollowupDirective:
    return ProactiveFollowupDirective(
        eligible=True,
        status="ready",
        style="gentle",
        trigger_after_seconds=1800,
        window_seconds=7200,
        rationale="proactive follow-up is allowed",
        opening_hint="check back in softly",
    )


def _guidance_plan() -> GuidancePlan:
    return GuidancePlan(
        mode="progress_guidance",
        lead_with="reflective_bridge",
        pacing="steady",
        step_budget=1,
        agency_mode="collaborative",
    )


def _session_ritual_plan(**overrides: object) -> SessionRitualPlan:
    base = SessionRitualPlan(
        phase="opening_ritual",
        opening_move="warm_orientation",
        bridge_move="frame_the_session",
        closing_move="light_handoff",
        continuity_anchor="session_frame",
    )
    return replace(base, **overrides)


def _somatic_orchestration_plan(**overrides: object) -> SomaticOrchestrationPlan:
    base = SomaticOrchestrationPlan(
        status="not_needed",
        cue="none",
        primary_mode="none",
        body_anchor="none",
        followup_style="none",
        allow_in_followup=False,
    )
    return replace(base, **overrides)


def _reengagement_plan() -> ReengagementPlan:
    return ReengagementPlan(
        status="active",
        ritual_mode="resume_reanchor",
        delivery_mode="two_part_sequence",
        strategy_key="resume_context_bridge",
        relational_move="context_bridge",
        pressure_mode="gentle_resume",
        autonomy_signal="light_invitation",
        sequence_objective="re_anchor_then_continue",
    )


def _stage_refresh_plan(*, stage_label: str) -> ProactiveStageRefreshPlan:
    return ProactiveStageRefreshPlan(
        status="active",
        refresh_key=f"{stage_label}_refresh",
        stage_label=stage_label,
        dispatch_window_status="on_time_dispatch",
        changed=False,
        refreshed_delivery_mode="single_message",
        refreshed_question_mode="statement_only",
        refreshed_autonomy_mode="light_invitation",
        refreshed_opening_move="shared_context_bridge",
        refreshed_bridge_move="micro_step_bridge",
        refreshed_closing_move="boundary_safe_close",
        refreshed_continuity_anchor="shared_context_anchor",
        refreshed_somatic_mode="none",
        refreshed_user_space_signal="light_invitation",
    )


def _dispatch_feedback(*, stage_label: str) -> ProactiveDispatchFeedbackAssessment:
    prior_stage_label = "first_touch" if stage_label == "second_touch" else "second_touch"
    return ProactiveDispatchFeedbackAssessment(
        status="active",
        feedback_key=f"{stage_label}_baseline_feedback",
        stage_label=stage_label,
        dispatch_count=1,
        prior_stage_label=prior_stage_label,
        gate_defer_count=0,
        changed=False,
        selected_strategy_key="resume_context_bridge",
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="light_invitation",
        selected_delivery_mode="single_message",
        selected_sequence_objective="re_anchor_then_continue",
    )


def _cadence_plan() -> ProactiveCadencePlan:
    return ProactiveCadencePlan(
        status="active",
        cadence_key="progress_three_touch",
        stage_labels=["first_touch", "second_touch", "final_soft_close"],
        stage_intervals_seconds=[0, 3600, 7200],
        window_seconds=10800,
        close_after_stage_index=3,
    )


def _first_touch_replan() -> ProactiveStageReplanAssessment:
    return ProactiveStageReplanAssessment(
        status="active",
        replan_key="first_touch_on_time_dispatch_stable",
        stage_label="first_touch",
        dispatch_window_status="on_time_dispatch",
        changed=False,
        selected_strategy_key="progress_micro_commitment",
        selected_ritual_mode="progress_reanchor",
        selected_delivery_mode="two_part_sequence",
        selected_relational_move="goal_reconnect",
        selected_pressure_mode="low_pressure_progress",
        selected_autonomy_signal="explicit_opt_out",
        selected_sequence_objective="small_progress_reentry",
    )


def _dispatch_gate() -> ProactiveDispatchGateDecision:
    return ProactiveDispatchGateDecision(
        status="active",
        gate_key="second_touch_dispatch_clear",
        stage_label="second_touch",
        dispatch_window_status="on_time_dispatch",
        decision="dispatch",
        changed=False,
        retry_after_seconds=0,
        selected_strategy_key="resume_context_bridge",
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="light_invitation",
    )


def _stage_state_decision(**overrides: object) -> ProactiveStageStateDecision:
    base = ProactiveStageStateDecision(
        status="active",
        state_key="second_touch_dispatch_shaped_resume_context_bridge",
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_shaped",
        changed=True,
        selected_strategy_key="resume_context_bridge",
        selected_stage_delivery_mode="single_message",
        selected_reengagement_delivery_mode="single_message",
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="light_invitation",
        line_state="softened",
        progression_action="advance_to_next_stage",
        progression_advanced=False,
        dispatch_envelope_key="second_touch_dispatch_shaped_resume_context_bridge",
        dispatch_envelope_decision="dispatch_shaped",
        primary_source="dispatch_envelope",
        controller_decision="dispatch_shaped",
    )
    return replace(base, **overrides)


def _lifecycle_queue_decision(**overrides: object) -> ProactiveLifecycleQueueDecision:
    base = ProactiveLifecycleQueueDecision(
        status="active",
        queue_key="second_touch_dispatch_lifecycle_queue_resume_context_bridge",
        current_stage_label="second_touch",
        lifecycle_state="dispatching",
        window_mode="dispatch_lifecycle_window",
        queue_mode="ready_lifecycle_queue",
        decision="dispatch_lifecycle_queue",
        queue_status="due",
        actionability="dispatch",
        changed=True,
        additional_delay_seconds=0,
        selected_strategy_key="resume_context_bridge",
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="light_invitation",
        selected_delivery_mode="single_message",
        primary_source="lifecycle_window",
        controller_decision="continue_lifecycle",
        active_sources=["lifecycle_window"],
        queue_notes=[],
        rationale="queue is dispatch-ready",
    )
    return replace(base, **overrides)


def _line_state_decision(**overrides: object) -> ProactiveLineStateDecision:
    base = ProactiveLineStateDecision(
        status="active",
        line_key="second_touch_softened_active_softened",
        current_stage_label="second_touch",
        current_stage_index=2,
        stage_count=3,
        remaining_stage_count=2,
        line_state="softened",
        lifecycle_mode="active_softened",
        actionability="soften",
        changed=True,
        current_stage_machine_mode="dispatching_stage",
        current_stage_transition_mode="dispatch_stage",
        next_stage_label="final_soft_close",
        close_loop_stage="final_soft_close",
        selected_strategy_key="resume_context_bridge",
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="light_invitation",
        selected_delivery_mode="single_message",
        primary_source="stage_machine",
        controller_decision="follow_remaining_line",
        line_notes=[],
        rationale="line stays active after this stage",
    )
    return replace(base, **overrides)


def _line_transition_decision(**overrides: object) -> ProactiveLineTransitionDecision:
    base = ProactiveLineTransitionDecision(
        status="active",
        transition_key="second_touch_advance_line_softened",
        current_line_key="second_touch_softened_active_softened",
        current_stage_label="second_touch",
        current_stage_index=2,
        stage_count=3,
        line_state="softened",
        lifecycle_mode="active_softened",
        transition_mode="advance_line",
        changed=True,
        next_stage_label="final_soft_close",
        next_stage_index=3,
        next_line_state="softened",
        next_lifecycle_mode="active",
        line_exit_mode="advance",
        selected_strategy_key="resume_context_bridge",
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="light_invitation",
        selected_delivery_mode="single_message",
        primary_source="line_state",
        controller_decision="follow_remaining_line",
        transition_notes=[],
        rationale="advance to the next stage",
    )
    return replace(base, **overrides)


def test_stage_replan_uses_stability_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="watch",
            stability_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_autonomy_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="watch",
            autonomy_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_boundary_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="watch",
            boundary_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_support_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="watch",
            support_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_clarity_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="watch",
            clarity_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_pacing_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="watch",
            pacing_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_attunement_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="watch",
            attunement_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_commitment_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="watch",
            commitment_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_disclosure_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="pass",
            commitment_governance_trajectory_status="stable",
            disclosure_governance_status="watch",
            disclosure_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_reciprocity_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="pass",
            commitment_governance_trajectory_status="stable",
            disclosure_governance_status="pass",
            disclosure_governance_trajectory_status="stable",
            reciprocity_governance_status="watch",
            reciprocity_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_progress_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="pass",
            commitment_governance_trajectory_status="stable",
            disclosure_governance_status="pass",
            disclosure_governance_trajectory_status="stable",
            reciprocity_governance_status="pass",
            reciprocity_governance_trajectory_status="stable",
            progress_governance_status="watch",
            progress_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_trust_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="watch",
            trust_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_continuity_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="pass",
            trust_governance_trajectory_status="stable",
            continuity_governance_status="watch",
            continuity_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_repair_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="pass",
            trust_governance_trajectory_status="stable",
            continuity_governance_status="pass",
            continuity_governance_trajectory_status="stable",
            repair_governance_status="watch",
            repair_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_replan_uses_relational_governance_for_low_pressure_context() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="pass",
            trust_governance_trajectory_status="stable",
            continuity_governance_status="pass",
            continuity_governance_trajectory_status="stable",
            repair_governance_status="pass",
            repair_governance_trajectory_status="stable",
            relational_governance_status="watch",
            relational_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert assessment.selected_strategy_key == "repair_soft_resume_bridge"
    assert assessment.selected_pressure_mode == "repair_soft"
    assert assessment.selected_autonomy_signal == "explicit_no_pressure"


def test_stage_and_line_controller_soften_for_stability_without_safety_trigger() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        stability_governance_status="watch",
        stability_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_stability_watch_spacing"
    assert stage_controller_decision.target_stage_label == "second_touch"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_stability_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_stability_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="revise",
            stability_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_stability_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_autonomy_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="watch",
        autonomy_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_autonomy_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_autonomy_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_autonomy_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="revise",
            autonomy_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_autonomy_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_boundary_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="watch",
        boundary_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_boundary_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_boundary_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_boundary_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="revise",
            boundary_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_boundary_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_support_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="watch",
        support_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_support_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_support_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_support_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="revise",
            support_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_support_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_clarity_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="watch",
        clarity_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_clarity_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_clarity_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_clarity_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="revise",
            clarity_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_clarity_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_pacing_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="pass",
        clarity_governance_trajectory_status="stable",
        pacing_governance_status="watch",
        pacing_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_pacing_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_pacing_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_pacing_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="revise",
            pacing_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_pacing_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_attunement_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="pass",
        clarity_governance_trajectory_status="stable",
        pacing_governance_status="pass",
        pacing_governance_trajectory_status="stable",
        attunement_governance_status="watch",
        attunement_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_attunement_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_attunement_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_attunement_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="revise",
            attunement_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_attunement_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_commitment_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="pass",
        clarity_governance_trajectory_status="stable",
        pacing_governance_status="pass",
        pacing_governance_trajectory_status="stable",
        attunement_governance_status="pass",
        attunement_governance_trajectory_status="stable",
        commitment_governance_status="watch",
        commitment_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_commitment_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_commitment_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_commitment_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="revise",
            commitment_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_commitment_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_disclosure_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="pass",
        clarity_governance_trajectory_status="stable",
        pacing_governance_status="pass",
        pacing_governance_trajectory_status="stable",
        attunement_governance_status="pass",
        attunement_governance_trajectory_status="stable",
        commitment_governance_status="pass",
        commitment_governance_trajectory_status="stable",
        disclosure_governance_status="watch",
        disclosure_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_disclosure_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_disclosure_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_disclosure_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="pass",
            commitment_governance_trajectory_status="stable",
            disclosure_governance_status="revise",
            disclosure_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_disclosure_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_reciprocity_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="pass",
        clarity_governance_trajectory_status="stable",
        pacing_governance_status="pass",
        pacing_governance_trajectory_status="stable",
        attunement_governance_status="pass",
        attunement_governance_trajectory_status="stable",
        commitment_governance_status="pass",
        commitment_governance_trajectory_status="stable",
        disclosure_governance_status="pass",
        disclosure_governance_trajectory_status="stable",
        reciprocity_governance_status="watch",
        reciprocity_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_reciprocity_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_reciprocity_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_reciprocity_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="pass",
            commitment_governance_trajectory_status="stable",
            disclosure_governance_status="pass",
            disclosure_governance_trajectory_status="stable",
            reciprocity_governance_status="revise",
            reciprocity_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_reciprocity_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_progress_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        autonomy_governance_status="pass",
        autonomy_governance_trajectory_status="stable",
        boundary_governance_status="pass",
        boundary_governance_trajectory_status="stable",
        support_governance_status="pass",
        support_governance_trajectory_status="stable",
        clarity_governance_status="pass",
        clarity_governance_trajectory_status="stable",
        pacing_governance_status="pass",
        pacing_governance_trajectory_status="stable",
        attunement_governance_status="pass",
        attunement_governance_trajectory_status="stable",
        commitment_governance_status="pass",
        commitment_governance_trajectory_status="stable",
        disclosure_governance_status="pass",
        disclosure_governance_trajectory_status="stable",
        reciprocity_governance_status="pass",
        reciprocity_governance_trajectory_status="stable",
        progress_governance_status="watch",
        progress_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_progress_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_progress_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_progress_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            autonomy_governance_status="pass",
            autonomy_governance_trajectory_status="stable",
            boundary_governance_status="pass",
            boundary_governance_trajectory_status="stable",
            support_governance_status="pass",
            support_governance_trajectory_status="stable",
            clarity_governance_status="pass",
            clarity_governance_trajectory_status="stable",
            pacing_governance_status="pass",
            pacing_governance_trajectory_status="stable",
            attunement_governance_status="pass",
            attunement_governance_trajectory_status="stable",
            commitment_governance_status="pass",
            commitment_governance_trajectory_status="stable",
            disclosure_governance_status="pass",
            disclosure_governance_trajectory_status="stable",
            reciprocity_governance_status="pass",
            reciprocity_governance_trajectory_status="stable",
            progress_governance_status="revise",
            progress_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_progress_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_pressure_without_safety_or_stability() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        stability_governance_status="pass",
        stability_governance_trajectory_status="stable",
        pressure_governance_status="watch",
        pressure_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_pressure_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_pressure_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_pressure_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="revise",
            pressure_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_pressure_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_trust_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        stability_governance_status="pass",
        stability_governance_trajectory_status="stable",
        pressure_governance_status="pass",
        pressure_governance_trajectory_status="stable",
        trust_governance_status="watch",
        trust_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_trust_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key == "remaining_line_trust_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_trust_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="revise",
            trust_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_trust_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_continuity_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        stability_governance_status="pass",
        stability_governance_trajectory_status="stable",
        pressure_governance_status="pass",
        pressure_governance_trajectory_status="stable",
        trust_governance_status="pass",
        trust_governance_trajectory_status="stable",
        continuity_governance_status="watch",
        continuity_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_continuity_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_continuity_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_continuity_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="pass",
            trust_governance_trajectory_status="stable",
            continuity_governance_status="revise",
            continuity_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_continuity_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_repair_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        stability_governance_status="pass",
        stability_governance_trajectory_status="stable",
        pressure_governance_status="pass",
        pressure_governance_trajectory_status="stable",
        trust_governance_status="pass",
        trust_governance_trajectory_status="stable",
        continuity_governance_status="pass",
        continuity_governance_trajectory_status="stable",
        repair_governance_status="watch",
        repair_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_repair_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_repair_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_repair_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="pass",
            trust_governance_trajectory_status="stable",
            continuity_governance_status="pass",
            continuity_governance_trajectory_status="stable",
            repair_governance_status="revise",
            repair_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_repair_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_and_line_controller_soften_for_relational_without_other_triggers() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        stability_governance_status="pass",
        stability_governance_trajectory_status="stable",
        pressure_governance_status="pass",
        pressure_governance_trajectory_status="stable",
        trust_governance_status="pass",
        trust_governance_trajectory_status="stable",
        continuity_governance_status="pass",
        continuity_governance_trajectory_status="stable",
        repair_governance_status="pass",
        repair_governance_trajectory_status="stable",
        relational_governance_status="watch",
        relational_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert stage_controller_decision.controller_key == "second_touch_relational_watch_spacing"
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_relational_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_defers_final_soft_close_for_relational_recenter() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            stability_governance_status="pass",
            stability_governance_trajectory_status="stable",
            pressure_governance_status="pass",
            pressure_governance_trajectory_status="stable",
            trust_governance_status="pass",
            trust_governance_trajectory_status="stable",
            continuity_governance_status="pass",
            continuity_governance_trajectory_status="stable",
            repair_governance_status="pass",
            repair_governance_trajectory_status="stable",
            relational_governance_status="revise",
            relational_governance_trajectory_status="recenter",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_relational_extra_space"
    assert decision.retry_after_seconds > 0


def test_stage_replan_notes_aggregate_governance_gate_for_multiple_lines() -> None:
    assessment = build_proactive_stage_replan_assessment(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            support_governance_status="watch",
            support_governance_trajectory_status="watch",
            clarity_governance_status="watch",
            clarity_governance_trajectory_status="watch",
        ),
        reengagement_plan=_reengagement_plan(),
        stage_refresh_plan=_stage_refresh_plan(stage_label="second_touch"),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="second_touch"),
    )

    assert assessment.changed is True
    assert any(
        note.startswith("aggregate_governance_gate:watch:support+clarity")
        for note in assessment.replan_notes
    )


def test_build_proactive_aggregate_governance_assessment_for_multiple_lines() -> None:
    assessment = build_proactive_aggregate_governance_assessment(
        system3_snapshot=_system3_snapshot(
            support_governance_status="watch",
            support_governance_trajectory_status="watch",
            clarity_governance_status="watch",
            clarity_governance_trajectory_status="watch",
            trust_governance_status="revise",
            trust_governance_trajectory_status="recenter",
        )
    )

    assert assessment.status == "recenter"
    assert assessment.primary_domain == "trust"
    assert assessment.domain_count == 3
    assert assessment.active_domains == ["trust", "support", "clarity"]
    assert assessment.summary == "trust+support+clarity"


def test_build_proactive_aggregate_controller_decision_softens_second_touch() -> None:
    decision = build_proactive_aggregate_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=_system3_snapshot(emotional_debt_status="watch"),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        aggregate_governance_assessment=build_proactive_aggregate_governance_assessment(
            system3_snapshot=_system3_snapshot(
                support_governance_status="watch",
                support_governance_trajectory_status="watch",
                clarity_governance_status="watch",
                clarity_governance_trajectory_status="watch",
            )
        ),
    )

    assert decision.status == "active"
    assert decision.decision == "soften_followup_line"
    assert decision.next_stage_label == "second_touch"
    assert decision.stage_additional_delay_seconds == 4050
    assert decision.line_additional_delay_seconds == 2700
    assert decision.selected_strategy_key == "resume_context_bridge"


def test_stage_controller_uses_guidance_gate_for_second_touch() -> None:
    decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=replace(
            _guidance_plan(),
            mode="stabilizing_guidance",
            handoff_mode="no_pressure_checkin",
            carryover_mode="grounding_ping",
            checkpoint_style="stability_check",
        ),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
    )

    assert decision.changed is True
    assert decision.controller_key == "second_touch_guidance_recenter_spacing"
    assert decision.selected_autonomy_signal == "explicit_no_pressure"
    assert decision.additional_delay_seconds == 2100


def test_line_controller_uses_guidance_gate_for_remaining_line() -> None:
    guidance_plan = replace(
        _guidance_plan(),
        mode="boundary_guidance",
        handoff_mode="autonomy_preserving_ping",
        carryover_mode="boundary_safe_ping",
        checkpoint_style="boundary_safe_step",
    )
    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=guidance_plan,
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
    )
    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=guidance_plan,
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_guidance_recentered_after_first_touch"
    )
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"
    assert line_controller_decision.additional_delay_seconds == 1200


def test_stage_and_line_controller_use_aggregate_governance_gate() -> None:
    system3_snapshot = _system3_snapshot(
        safety_governance_status="pass",
        safety_governance_trajectory_status="stable",
        support_governance_status="watch",
        support_governance_trajectory_status="watch",
        clarity_governance_status="watch",
        clarity_governance_trajectory_status="watch",
    )
    stage_replan_assessment = _first_touch_replan()
    dispatch_feedback_assessment = _dispatch_feedback(stage_label="first_touch")

    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
    )

    assert stage_controller_decision.changed is True
    assert (
        stage_controller_decision.controller_key
        == "second_touch_aggregate_governance_watch_spacing"
    )
    assert stage_controller_decision.selected_strategy_key == "resume_context_bridge"
    assert stage_controller_decision.selected_autonomy_signal == "explicit_no_pressure"

    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        system3_snapshot=system3_snapshot,
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=stage_replan_assessment,
        dispatch_feedback_assessment=dispatch_feedback_assessment,
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_governance_softened_after_first_touch"
    )
    assert line_controller_decision.line_state == "softened"
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"


def test_dispatch_gate_uses_aggregate_governance_gate_for_multiple_lines() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(
            safety_governance_status="pass",
            safety_governance_trajectory_status="stable",
            support_governance_status="revise",
            support_governance_trajectory_status="recenter",
            trust_governance_status="watch",
            trust_governance_trajectory_status="watch",
        ),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_progressed_dispatch_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="progressed_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason="progression:second_touch->final_soft_close",
        progression_advanced=True,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_governance_extra_space"
    assert decision.retry_after_seconds > 0


def test_dispatch_gate_uses_guidance_gate_for_final_soft_close() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=replace(
            _guidance_plan(),
            mode="repair_guidance",
            handoff_mode="repair_soft_ping",
            carryover_mode="repair_ping",
            checkpoint_style="repair_checkpoint",
        ),
        system3_snapshot=_system3_snapshot(),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_on_time_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="on_time_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason=None,
        progression_advanced=False,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_guidance_extra_space"
    assert decision.retry_after_seconds == 900


def test_stage_controller_uses_ritual_somatic_gate_for_second_touch() -> None:
    decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        session_ritual_plan=replace(
            _session_ritual_plan(),
            phase="repair_ritual",
            closing_move="repair_soft_close",
            continuity_anchor="repair_landing",
            somatic_shortcut="one_slower_breath",
        ),
        somatic_orchestration_plan=replace(
            _somatic_orchestration_plan(),
            status="active",
            cue="breath",
            primary_mode="breath_regulation",
            body_anchor="one_slower_breath",
            followup_style="gentle_body_first_reentry",
            allow_in_followup=True,
        ),
    )

    assert decision.changed is True
    assert decision.controller_key == "second_touch_ritual_recenter_spacing"
    assert decision.selected_autonomy_signal == "explicit_no_pressure"
    assert decision.selected_delivery_mode == "two_part_sequence"
    assert decision.additional_delay_seconds == 1500


def test_line_controller_uses_ritual_somatic_gate_for_remaining_line() -> None:
    session_ritual_plan = replace(
        _session_ritual_plan(),
        phase="repair_ritual",
        closing_move="repair_soft_close",
        continuity_anchor="repair_landing",
        somatic_shortcut="one_slower_breath",
    )
    somatic_orchestration_plan = replace(
        _somatic_orchestration_plan(),
        status="active",
        cue="breath",
        primary_mode="breath_regulation",
        body_anchor="one_slower_breath",
        followup_style="gentle_body_first_reentry",
        allow_in_followup=True,
    )
    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )
    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_ritual_recentered_after_first_touch"
    )
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"
    assert line_controller_decision.selected_delivery_mode == "two_part_sequence"
    assert line_controller_decision.additional_delay_seconds == 900


def test_dispatch_gate_uses_ritual_somatic_gate_for_final_soft_close() -> None:
    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_on_time_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="on_time_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason=None,
        progression_advanced=False,
        session_ritual_plan=replace(
            _session_ritual_plan(),
            phase="repair_ritual",
            closing_move="repair_soft_close",
            continuity_anchor="repair_landing",
            somatic_shortcut="one_slower_breath",
        ),
        somatic_orchestration_plan=replace(
            _somatic_orchestration_plan(),
            status="active",
            cue="breath",
            primary_mode="breath_regulation",
            body_anchor="one_slower_breath",
            followup_style="gentle_body_first_reentry",
            allow_in_followup=True,
        ),
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_ritual_extra_space"
    assert decision.retry_after_seconds == 600


def test_dispatch_envelope_uses_changed_sources_and_selected_fields() -> None:
    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        session_ritual_plan=replace(
            _session_ritual_plan(),
            phase="repair_ritual",
            closing_move="repair_soft_close",
            continuity_anchor="repair_landing",
            somatic_shortcut="one_slower_breath",
        ),
        somatic_orchestration_plan=replace(
            _somatic_orchestration_plan(),
            status="active",
            cue="breath",
            primary_mode="breath_regulation",
            body_anchor="one_slower_breath",
            followup_style="gentle_body_first_reentry",
            allow_in_followup=True,
        ),
    )
    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
        session_ritual_plan=replace(
            _session_ritual_plan(),
            phase="repair_ritual",
            closing_move="repair_soft_close",
            continuity_anchor="repair_landing",
            somatic_shortcut="one_slower_breath",
        ),
        somatic_orchestration_plan=replace(
            _somatic_orchestration_plan(),
            status="active",
            cue="breath",
            primary_mode="breath_regulation",
            body_anchor="one_slower_breath",
            followup_style="gentle_body_first_reentry",
            allow_in_followup=True,
        ),
    )
    envelope = build_proactive_dispatch_envelope_decision(
        stage_label="second_touch",
        current_stage_directive={
            "delivery_mode": "single_message",
            "question_mode": "statement_only",
            "autonomy_mode": "light_invitation",
            "objective": "resume_gently",
            "closing_style": "soft_close",
        },
        current_stage_actuation={
            "opening_move": "soft_open",
            "bridge_move": "micro_step_bridge",
            "closing_move": "boundary_safe_close",
            "continuity_anchor": "shared_context_anchor",
            "somatic_mode": "none",
            "somatic_body_anchor": "none",
            "followup_style": "light_ping",
            "user_space_signal": "light_invitation",
        },
        stage_refresh_plan=replace(
            _stage_refresh_plan(stage_label="second_touch"),
            changed=True,
            refreshed_delivery_mode="two_part_sequence",
            refreshed_question_mode="single_question",
            refreshed_autonomy_mode="explicit_no_pressure",
            refreshed_opening_move="reflective_restate",
            refreshed_bridge_move="resume_the_open_loop",
            refreshed_closing_move="reflective_close",
            refreshed_continuity_anchor="repair_landing",
            refreshed_somatic_mode="breath_regulation",
            refreshed_user_space_signal="explicit_opt_out",
        ),
        stage_replan_assessment=replace(
            _first_touch_replan(),
            stage_label="second_touch",
            changed=True,
            selected_strategy_key="repair_soft_resume_bridge",
            selected_ritual_mode="repair_reentry",
            selected_delivery_mode="two_part_sequence",
            selected_relational_move="repair_bridge",
            selected_pressure_mode="repair_soft",
            selected_autonomy_signal="explicit_no_pressure",
            selected_sequence_objective="repair_then_resume",
            selected_somatic_action="one_slower_breath",
        ),
        dispatch_feedback_assessment=replace(
            _dispatch_feedback(stage_label="second_touch"),
            changed=True,
        ),
        dispatch_gate_decision=replace(
            _dispatch_gate(),
            decision="defer",
            changed=True,
            retry_after_seconds=900,
        ),
        stage_controller_decision=stage_controller_decision,
        line_controller_decision=line_controller_decision,
    )

    assert envelope.status == "scheduled"
    assert envelope.envelope_key.startswith("second_touch_defer_dispatch_")
    assert envelope.decision == "defer_dispatch"
    assert envelope.changed is True
    assert envelope.selected_strategy_key == "repair_soft_resume_bridge"
    assert envelope.selected_stage_delivery_mode == "two_part_sequence"
    assert envelope.selected_stage_question_mode == "single_question"
    assert envelope.selected_opening_move == "reflective_restate"
    assert envelope.selected_followup_style == "light_ping"
    assert envelope.dispatch_retry_after_seconds == 900
    assert set(envelope.active_sources) >= {
        "refresh",
        "replan",
        "feedback",
        "stage_controller",
        "line_controller",
        "gate",
    }


def test_stage_transition_reschedules_close_loop_when_gate_defers() -> None:
    decision = build_proactive_stage_transition_decision(
        stage_state_decision=_stage_state_decision(
            stage_label="final_soft_close",
            stage_index=3,
            queue_status="scheduled",
            state_key="final_soft_close_scheduled_close_loop_repair_soft_resume_bridge",
            state_mode="scheduled_close_loop",
            line_state="close_ready",
            progression_action="close_line",
            dispatch_envelope_decision="defer_dispatch",
            primary_source="gate",
            controller_decision="defer",
        ),
        dispatch_gate_decision=replace(
            _dispatch_gate(),
            stage_label="final_soft_close",
            decision="defer",
            changed=True,
            retry_after_seconds=1800,
        ),
    )

    assert decision.status == "scheduled"
    assert decision.transition_mode == "reschedule_close_loop"
    assert decision.next_queue_status_hint == "scheduled"
    assert decision.stage_exit_mode == "close_loop"
    assert decision.primary_source == "gate"


def test_stage_transition_dispatches_softened_stage_with_next_stage_hint() -> None:
    decision = build_proactive_stage_transition_decision(
        stage_state_decision=_stage_state_decision(),
        next_stage_label="final_soft_close",
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert decision.status == "active"
    assert decision.transition_mode == "dispatch_softened_stage"
    assert decision.next_queue_status_hint == "dispatched"
    assert decision.stage_exit_mode == "advance_line"
    assert decision.next_stage_label == "final_soft_close"
    assert decision.next_stage_index == 3


def test_stage_transition_retires_line_for_terminal_soft_close() -> None:
    decision = build_proactive_stage_transition_decision(
        stage_state_decision=_stage_state_decision(
            stage_label="final_soft_close",
            stage_index=3,
            stage_count=3,
            state_key="final_soft_close_dispatch_close_ready_repair_soft_resume_bridge",
            state_mode="dispatch_close_ready",
            line_state="close_ready",
            progression_action="close_line",
            dispatch_envelope_decision="dispatch_shaped",
            primary_source="progression",
            controller_decision="close_line",
        ),
        dispatch_gate_decision=replace(
            _dispatch_gate(),
            stage_label="final_soft_close",
            decision="dispatch",
        ),
    )

    assert decision.status == "active"
    assert decision.transition_mode == "dispatch_close_loop"
    assert decision.next_queue_status_hint == "terminal"
    assert decision.stage_exit_mode == "retire_line"
    assert decision.next_stage_label is None


def test_build_proactive_orchestration_controller_decision_uses_guidance_and_ritual() -> None:
    decision = build_proactive_orchestration_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        guidance_plan=replace(
            _guidance_plan(),
            mode="repair_guidance",
            handoff_mode="repair_soft_ping",
            carryover_mode="repair_ping",
            checkpoint_style="repair_checkpoint",
        ),
        session_ritual_plan=replace(
            _session_ritual_plan(),
            phase="repair_ritual",
            closing_move="repair_soft_close",
            continuity_anchor="repair_landing",
            somatic_shortcut="one_slower_breath",
        ),
        somatic_orchestration_plan=replace(
            _somatic_orchestration_plan(),
            status="active",
            cue="breath",
            primary_mode="breath_regulation",
            body_anchor="one_slower_breath",
            followup_style="gentle_body_first_reentry",
            allow_in_followup=True,
        ),
    )

    assert decision.status == "active"
    assert decision.decision == "recenter_followup_line"
    assert decision.primary_source == "guidance"
    assert decision.active_sources == ["guidance", "ritual_somatic"]
    assert decision.next_stage_label == "second_touch"
    assert decision.selected_strategy_key == "repair_soft_resume_bridge"


def test_stage_controller_prefers_orchestration_controller_for_second_touch() -> None:
    guidance_plan = replace(
        _guidance_plan(),
        mode="repair_guidance",
        handoff_mode="repair_soft_ping",
        carryover_mode="repair_ping",
        checkpoint_style="repair_checkpoint",
    )
    session_ritual_plan = replace(
        _session_ritual_plan(),
        phase="repair_ritual",
        closing_move="repair_soft_close",
        continuity_anchor="repair_landing",
        somatic_shortcut="one_slower_breath",
    )
    somatic_orchestration_plan = replace(
        _somatic_orchestration_plan(),
        status="active",
        cue="breath",
        primary_mode="breath_regulation",
        body_anchor="one_slower_breath",
        followup_style="gentle_body_first_reentry",
        allow_in_followup=True,
    )
    orchestration_controller_decision = build_proactive_orchestration_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        guidance_plan=guidance_plan,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )

    decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=guidance_plan,
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        orchestration_controller_decision=orchestration_controller_decision,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )

    assert decision.changed is True
    assert decision.controller_key == "second_touch_orchestration_recenter_spacing"
    assert decision.selected_autonomy_signal == "explicit_no_pressure"
    assert decision.selected_delivery_mode == "single_message"
    assert decision.additional_delay_seconds == 2100


def test_line_controller_prefers_orchestration_controller_for_remaining_line() -> None:
    guidance_plan = replace(
        _guidance_plan(),
        mode="repair_guidance",
        handoff_mode="repair_soft_ping",
        carryover_mode="repair_ping",
        checkpoint_style="repair_checkpoint",
    )
    session_ritual_plan = replace(
        _session_ritual_plan(),
        phase="repair_ritual",
        closing_move="repair_soft_close",
        continuity_anchor="repair_landing",
        somatic_shortcut="one_slower_breath",
    )
    somatic_orchestration_plan = replace(
        _somatic_orchestration_plan(),
        status="active",
        cue="breath",
        primary_mode="breath_regulation",
        body_anchor="one_slower_breath",
        followup_style="gentle_body_first_reentry",
        allow_in_followup=True,
    )
    orchestration_controller_decision = build_proactive_orchestration_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        guidance_plan=guidance_plan,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )
    stage_controller_decision = build_proactive_stage_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=guidance_plan,
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        orchestration_controller_decision=orchestration_controller_decision,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )
    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=guidance_plan,
        system3_snapshot=_system3_snapshot(),
        current_stage_label="first_touch",
        current_stage_index=1,
        stage_replan_assessment=_first_touch_replan(),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="first_touch"),
        stage_controller_decision=stage_controller_decision,
        dispatch_gate_decision=_dispatch_gate(),
        orchestration_controller_decision=orchestration_controller_decision,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )

    assert line_controller_decision.changed is True
    assert (
        line_controller_decision.controller_key
        == "remaining_line_orchestration_recentered_after_first_touch"
    )
    assert line_controller_decision.selected_autonomy_signal == "explicit_no_pressure"
    assert line_controller_decision.selected_delivery_mode == "single_message"
    assert line_controller_decision.additional_delay_seconds == 1200


def test_line_controller_keeps_final_stage_close_ready() -> None:
    line_controller_decision = build_proactive_line_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        current_stage_label="final_soft_close",
        current_stage_index=3,
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_on_time_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="on_time_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        dispatch_feedback_assessment=_dispatch_feedback(stage_label="final_soft_close"),
        stage_controller_decision=ProactiveStageControllerDecision(
            status="active",
            controller_key="final_soft_close_follow_stage",
            trigger_stage_label="final_soft_close",
            target_stage_label="final_soft_close",
            decision="follow_stage_replan",
            changed=False,
            additional_delay_seconds=0,
            selected_strategy_key="continuity_soft_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
        ),
        dispatch_gate_decision=_dispatch_gate(),
    )

    assert line_controller_decision.line_state == "close_ready"
    assert line_controller_decision.decision == "retire_after_close_loop"
    assert line_controller_decision.controller_key == "final_soft_close_line_close_ready"


def test_dispatch_gate_prefers_orchestration_controller_for_final_soft_close() -> None:
    orchestration_controller_decision = build_proactive_orchestration_controller_decision(
        directive=_directive(),
        proactive_cadence_plan=_cadence_plan(),
        current_stage_label="second_touch",
        current_stage_index=2,
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_on_time_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="on_time_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        guidance_plan=replace(
            _guidance_plan(),
            mode="repair_guidance",
            handoff_mode="repair_soft_ping",
            carryover_mode="repair_ping",
            checkpoint_style="repair_checkpoint",
        ),
        session_ritual_plan=replace(
            _session_ritual_plan(),
            phase="repair_ritual",
            closing_move="repair_soft_close",
            continuity_anchor="repair_landing",
        ),
        somatic_orchestration_plan=replace(
            _somatic_orchestration_plan(),
            status="active",
            cue="breath",
            primary_mode="breath_regulation",
            body_anchor="one_slower_breath",
            followup_style="gentle_body_first_reentry",
            allow_in_followup=True,
        ),
    )

    decision = build_proactive_dispatch_gate_decision(
        directive=_directive(),
        guidance_plan=_guidance_plan(),
        system3_snapshot=_system3_snapshot(),
        stage_replan_assessment=ProactiveStageReplanAssessment(
            status="active",
            replan_key="final_soft_close_on_time_continuity_soft_ping",
            stage_label="final_soft_close",
            dispatch_window_status="on_time_dispatch",
            changed=True,
            selected_strategy_key="continuity_soft_ping",
            selected_ritual_mode="continuity_nudge",
            selected_delivery_mode="single_message",
            selected_relational_move="continuity_ping",
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_sequence_objective="presence_then_optional_reply",
        ),
        queue_status="due",
        schedule_reason=None,
        progression_advanced=False,
        orchestration_controller_decision=orchestration_controller_decision,
    )

    assert decision.changed is True
    assert decision.decision == "defer"
    assert decision.gate_key == "final_soft_close_orchestration_extra_space"
    assert decision.retry_after_seconds == 900


def test_stage_machine_buffers_close_loop_reschedule() -> None:
    state = _stage_state_decision(
        stage_label="final_soft_close",
        stage_index=3,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_close_loop",
        line_state="close_ready",
        progression_action="close_line",
        changed=True,
    )
    transition = build_proactive_stage_transition_decision(
        stage_state_decision=state,
    )

    decision = build_proactive_stage_machine_decision(
        stage_state_decision=state,
        stage_transition_decision=transition,
    )

    assert decision.machine_key == "final_soft_close_scheduled_close_loop"
    assert decision.machine_mode == "scheduled_close_loop"
    assert decision.lifecycle_mode == "buffered_close_loop"
    assert decision.actionability == "reschedule"
    assert decision.status == "scheduled"


def test_stage_machine_dispatches_softened_stage() -> None:
    state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_shaped",
        line_state="softened",
        changed=True,
    )
    transition = build_proactive_stage_transition_decision(
        stage_state_decision=state,
        next_stage_label="final_soft_close",
    )

    decision = build_proactive_stage_machine_decision(
        stage_state_decision=state,
        stage_transition_decision=transition,
    )

    assert decision.machine_mode == "dispatching_softened_stage"
    assert decision.lifecycle_mode == "dispatching"
    assert decision.actionability == "dispatch"
    assert "line_softened" in decision.machine_notes


def test_stage_machine_retires_terminal_line() -> None:
    state = _stage_state_decision(
        stage_label="final_soft_close",
        stage_index=3,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_close_ready",
        line_state="close_ready",
        progression_action="close_line",
        changed=True,
    )
    transition = build_proactive_stage_transition_decision(
        stage_state_decision=state,
    )

    decision = build_proactive_stage_machine_decision(
        stage_state_decision=state,
        stage_transition_decision=transition,
    )

    assert decision.machine_mode == "retiring_line"
    assert decision.lifecycle_mode == "terminal"
    assert decision.actionability == "retire"
    assert decision.status == "terminal"


def test_line_state_softens_remaining_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_shaped",
        line_state="softened",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_controller = ProactiveLineControllerDecision(
        status="active",
        controller_key="remaining_line_stability_softened_after_first_touch",
        trigger_stage_label="first_touch",
        line_state="softened",
        decision="soften_remaining_line",
        changed=True,
        affected_stage_labels=["second_touch", "final_soft_close"],
        additional_delay_seconds=1800,
        selected_pressure_mode="gentle_resume",
        selected_autonomy_signal="explicit_no_pressure",
        selected_delivery_mode="single_message",
    )

    decision = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=line_controller,
    )

    assert decision.line_state == "softened"
    assert decision.lifecycle_mode in {"active_softened", "buffered"}
    assert decision.actionability == "soften"
    assert decision.remaining_stage_count == 3


def test_line_state_winds_down_close_loop() -> None:
    stage_state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_close_ready",
        line_state="close_ready",
        progression_action="none",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )

    decision = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_close_ready_after_second_touch",
            trigger_stage_label="second_touch",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            affected_stage_labels=["final_soft_close"],
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
        ),
    )

    assert decision.lifecycle_mode == "winding_down"
    assert decision.actionability == "close_loop"
    assert decision.close_loop_stage == "final_soft_close"


def test_line_state_retires_terminal_machine() -> None:
    stage_state = _stage_state_decision(
        stage_label="final_soft_close",
        stage_index=3,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_close_ready",
        line_state="close_ready",
        progression_action="close_line",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )

    decision = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_close_ready_after_second_touch",
            trigger_stage_label="final_soft_close",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            affected_stage_labels=["final_soft_close"],
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
        ),
    )

    assert decision.status == "terminal"
    assert decision.line_state == "retiring"


def test_line_transition_advances_remaining_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_ready",
        line_state="steady",
        progression_action="advance_to_next_stage",
        changed=True,
        selected_pressure_mode="none",
        dispatch_envelope_decision="dispatch",
        primary_source="cadence",
        controller_decision="dispatch",
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_follow_after_first_touch",
            trigger_stage_label="first_touch",
            line_state="steady",
            decision="follow_remaining_line",
            changed=False,
            affected_stage_labels=["second_touch", "final_soft_close"],
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="light_invitation",
            selected_delivery_mode="single_message",
        ),
    )

    decision = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )

    assert decision.transition_mode == "advance_line"
    assert decision.line_exit_mode == "advance"
    assert decision.next_stage_label == "second_touch"


def test_line_transition_buffers_softened_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        progression_action="advance_to_next_stage",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened_after_first_touch",
            trigger_stage_label="first_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
            affected_stage_labels=["second_touch", "final_soft_close"],
            additional_delay_seconds=1800,
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
            selected_delivery_mode="single_message",
        ),
    )

    decision = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )

    assert decision.transition_mode == "buffer_line"
    assert decision.line_exit_mode == "buffer"
    assert decision.next_line_state == "softened"


def test_line_transition_retires_terminal_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="final_soft_close",
        stage_index=3,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_close_ready",
        line_state="close_ready",
        progression_action="close_line",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_close_ready_after_second_touch",
            trigger_stage_label="final_soft_close",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            affected_stage_labels=["final_soft_close"],
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
        ),
    )

    decision = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )

    assert decision.transition_mode == "retire_line"
    assert decision.line_exit_mode == "retire"
    assert decision.next_lifecycle_mode == "terminal"


def test_line_machine_advances_remaining_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_shaped",
        line_state="steady",
        progression_action="advance_to_next_stage",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=build_proactive_stage_machine_decision(
            stage_state_decision=stage_state,
            stage_transition_decision=stage_transition,
        ),
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_follow_after_first_touch",
            trigger_stage_label="first_touch",
            line_state="steady",
            decision="follow_remaining_line",
            changed=False,
            affected_stage_labels=["second_touch", "final_soft_close"],
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="light_invitation",
            selected_delivery_mode="single_message",
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )

    decision = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )

    assert decision.machine_mode == "advancing_line"
    assert decision.actionability == "advance"
    assert decision.lifecycle_mode == "active"


def test_line_machine_buffers_softened_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        progression_action="advance_to_next_stage",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=build_proactive_stage_machine_decision(
            stage_state_decision=stage_state,
            stage_transition_decision=stage_transition,
        ),
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened_after_first_touch",
            trigger_stage_label="first_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
            affected_stage_labels=["second_touch", "final_soft_close"],
            additional_delay_seconds=1800,
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
            selected_delivery_mode="single_message",
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )

    decision = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )

    assert decision.machine_mode == "buffered_line"
    assert decision.actionability == "buffer"
    assert decision.lifecycle_mode == "buffered"


def test_line_machine_retires_terminal_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="final_soft_close",
        stage_index=3,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_close_ready",
        line_state="close_ready",
        progression_action="close_line",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=build_proactive_stage_machine_decision(
            stage_state_decision=stage_state,
            stage_transition_decision=stage_transition,
        ),
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_close_ready_after_second_touch",
            trigger_stage_label="final_soft_close",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            affected_stage_labels=["final_soft_close"],
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )

    decision = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )

    assert decision.machine_mode == "retiring_line"
    assert decision.actionability == "retire"
    assert decision.lifecycle_mode == "terminal"


def test_lifecycle_machine_dispatches_active_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_ready",
        line_state="steady",
        progression_action="advance_to_next_stage",
        changed=True,
        selected_pressure_mode="none",
        dispatch_envelope_decision="dispatch",
        primary_source="cadence",
        controller_decision="dispatch",
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_follow_after_first_touch",
            trigger_stage_label="first_touch",
            line_state="steady",
            decision="follow_remaining_line",
            changed=False,
            affected_stage_labels=["second_touch", "final_soft_close"],
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )

    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    decision = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )

    assert lifecycle_state.state_mode == "lifecycle_dispatching"
    assert lifecycle_transition.transition_mode == "dispatch_lifecycle"
    assert decision.machine_mode == "dispatching_lifecycle"
    assert decision.actionability == "dispatch"
    assert decision.lifecycle_mode == "active"


def test_lifecycle_machine_buffers_softened_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="first_touch",
        stage_index=1,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        progression_action="advance_to_next_stage",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="second_touch",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened_after_first_touch",
            trigger_stage_label="first_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
            affected_stage_labels=["second_touch", "final_soft_close"],
            additional_delay_seconds=1800,
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
            selected_delivery_mode="single_message",
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )

    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    decision = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )

    assert lifecycle_state.state_mode == "lifecycle_buffered"
    assert lifecycle_transition.transition_mode == "buffer_lifecycle"
    assert decision.machine_mode == "buffered_lifecycle"
    assert decision.actionability == "buffer"
    assert decision.lifecycle_mode == "buffered"


def test_lifecycle_machine_retires_terminal_line() -> None:
    stage_state = _stage_state_decision(
        stage_label="final_soft_close",
        stage_index=3,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_close_ready",
        line_state="close_ready",
        progression_action="close_line",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_close_ready_after_second_touch",
            trigger_stage_label="final_soft_close",
            line_state="close_ready",
            decision="retire_after_close_loop",
            changed=True,
            affected_stage_labels=["final_soft_close"],
            selected_pressure_mode="archive_light_presence",
            selected_autonomy_signal="archive_light_thread",
            selected_delivery_mode="single_message",
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )

    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    decision = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )

    assert lifecycle_state.state_mode == "lifecycle_terminal"
    assert lifecycle_transition.transition_mode == "retire_lifecycle"
    assert decision.machine_mode == "terminal_lifecycle"
    assert decision.actionability == "retire"


def test_lifecycle_controller_softens_buffered_lifecycle() -> None:
    stage_state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="final_soft_close",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened",
            trigger_stage_label="second_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    lifecycle_machine = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )

    decision = build_proactive_lifecycle_controller_decision(
        lifecycle_machine_decision=lifecycle_machine,
    )

    assert decision.lifecycle_state == "buffered"
    assert decision.decision == "buffer_lifecycle"
    assert decision.changed is True
    assert decision.controller_key.startswith("second_touch_buffer_lifecycle_")


def test_lifecycle_envelope_shapes_buffered_lifecycle() -> None:
    stage_state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="final_soft_close",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened",
            trigger_stage_label="second_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    lifecycle_machine = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )
    lifecycle_controller = build_proactive_lifecycle_controller_decision(
        lifecycle_machine_decision=lifecycle_machine,
    )

    decision = build_proactive_lifecycle_envelope_decision(
        lifecycle_machine_decision=lifecycle_machine,
        lifecycle_controller_decision=lifecycle_controller,
    )

    assert decision.lifecycle_state == "buffered"
    assert decision.envelope_mode == "buffered_lifecycle_shape"
    assert decision.decision == "buffer_lifecycle_shape"
    assert decision.actionability == "buffer"
    assert decision.changed is True
    assert decision.envelope_key.startswith("second_touch_buffer_lifecycle_shape_")


def test_lifecycle_scheduler_defers_buffered_lifecycle() -> None:
    stage_state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="final_soft_close",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened",
            trigger_stage_label="second_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    lifecycle_machine = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )
    lifecycle_controller = build_proactive_lifecycle_controller_decision(
        lifecycle_machine_decision=lifecycle_machine,
    )
    lifecycle_envelope = build_proactive_lifecycle_envelope_decision(
        lifecycle_machine_decision=lifecycle_machine,
        lifecycle_controller_decision=lifecycle_controller,
    )

    decision = build_proactive_lifecycle_scheduler_decision(
        lifecycle_envelope_decision=lifecycle_envelope,
        proactive_scheduling_plan=ProactiveSchedulingPlan(
            status="active",
            scheduler_mode="progress_spacing",
            min_seconds_since_last_outbound=1800,
            first_touch_extra_delay_seconds=300,
            stage_spacing_mode="expanded",
            low_pressure_guard="balanced_user_space",
        ),
        dispatch_gate_decision=ProactiveDispatchGateDecision(
            status="active",
            gate_key="second_touch_more_space",
            stage_label="second_touch",
            dispatch_window_status="scheduled",
            decision="defer",
            changed=True,
            retry_after_seconds=900,
            selected_strategy_key="continuity_soft_ping",
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
        ),
    )

    assert decision.lifecycle_state == "buffered"
    assert decision.scheduler_mode == "deferred_lifecycle_schedule"
    assert decision.decision == "defer_lifecycle_schedule"
    assert decision.queue_status_hint == "scheduled"
    assert decision.actionability == "buffer"
    assert decision.additional_delay_seconds == 900
    assert decision.scheduler_key.startswith("second_touch_defer_lifecycle_schedule_")


def test_lifecycle_window_keeps_deferred_buffered_lifecycle() -> None:
    stage_state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="scheduled",
        state_mode="scheduled_softened",
        line_state="softened",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="final_soft_close",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_softened",
            trigger_stage_label="second_touch",
            line_state="softened",
            decision="soften_remaining_line",
            changed=True,
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    lifecycle_machine = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )
    lifecycle_controller = build_proactive_lifecycle_controller_decision(
        lifecycle_machine_decision=lifecycle_machine,
    )
    lifecycle_envelope = build_proactive_lifecycle_envelope_decision(
        lifecycle_machine_decision=lifecycle_machine,
        lifecycle_controller_decision=lifecycle_controller,
    )
    lifecycle_scheduler = build_proactive_lifecycle_scheduler_decision(
        lifecycle_envelope_decision=lifecycle_envelope,
        proactive_scheduling_plan=ProactiveSchedulingPlan(
            status="active",
            scheduler_mode="progress_spacing",
            min_seconds_since_last_outbound=1800,
            first_touch_extra_delay_seconds=300,
            stage_spacing_mode="expanded",
            low_pressure_guard="balanced_user_space",
        ),
        dispatch_gate_decision=ProactiveDispatchGateDecision(
            status="active",
            gate_key="second_touch_more_space",
            stage_label="second_touch",
            dispatch_window_status="scheduled",
            decision="defer",
            changed=True,
            retry_after_seconds=900,
            selected_strategy_key="continuity_soft_ping",
            selected_pressure_mode="gentle_resume",
            selected_autonomy_signal="explicit_no_pressure",
        ),
    )

    decision = build_proactive_lifecycle_window_decision(
        lifecycle_scheduler_decision=lifecycle_scheduler,
        current_queue_status="scheduled",
        schedule_reason="guardrail:second_touch_more_space",
        progression_action="advance_to_next_stage",
        progression_advanced=True,
    )

    assert decision.lifecycle_state == "buffered"
    assert decision.window_mode == "deferred_lifecycle_window"
    assert decision.decision == "defer_lifecycle_window"
    assert decision.queue_status == "scheduled"
    assert decision.actionability == "buffer"
    assert decision.additional_delay_seconds == 900
    assert decision.window_key.startswith("second_touch_defer_lifecycle_window_")


def test_lifecycle_queue_keeps_overdue_dispatchable_lifecycle() -> None:
    stage_state = _stage_state_decision(
        stage_label="second_touch",
        stage_index=2,
        stage_count=3,
        queue_status="due",
        state_mode="dispatch_ready",
        line_state="steady",
        changed=True,
    )
    stage_transition = build_proactive_stage_transition_decision(
        stage_state_decision=stage_state,
        next_stage_label="final_soft_close",
    )
    stage_machine = build_proactive_stage_machine_decision(
        stage_state_decision=stage_state,
        stage_transition_decision=stage_transition,
    )
    line_state = build_proactive_line_state_decision(
        proactive_cadence_plan=_cadence_plan(),
        stage_machine_decision=stage_machine,
        line_controller_decision=ProactiveLineControllerDecision(
            status="active",
            controller_key="remaining_line_steady",
            trigger_stage_label="second_touch",
            line_state="steady",
            decision="follow_remaining_line",
            changed=False,
        ),
    )
    line_transition = build_proactive_line_transition_decision(
        line_state_decision=line_state,
        stage_transition_decision=stage_transition,
    )
    line_machine = build_proactive_line_machine_decision(
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    lifecycle_state = build_proactive_lifecycle_state_decision(
        stage_machine_decision=stage_machine,
        line_machine_decision=line_machine,
    )
    lifecycle_transition = build_proactive_lifecycle_transition_decision(
        lifecycle_state_decision=lifecycle_state,
    )
    lifecycle_machine = build_proactive_lifecycle_machine_decision(
        lifecycle_state_decision=lifecycle_state,
        lifecycle_transition_decision=lifecycle_transition,
    )
    lifecycle_controller = build_proactive_lifecycle_controller_decision(
        lifecycle_machine_decision=lifecycle_machine,
    )
    lifecycle_envelope = build_proactive_lifecycle_envelope_decision(
        lifecycle_machine_decision=lifecycle_machine,
        lifecycle_controller_decision=lifecycle_controller,
    )
    lifecycle_scheduler = build_proactive_lifecycle_scheduler_decision(
        lifecycle_envelope_decision=lifecycle_envelope,
    )
    lifecycle_window = build_proactive_lifecycle_window_decision(
        lifecycle_scheduler_decision=lifecycle_scheduler,
        current_queue_status="overdue",
    )
    lifecycle_window = replace(
        lifecycle_window,
        status="active",
        lifecycle_state="dispatching",
        window_mode="dispatch_lifecycle_window",
        decision="dispatch_lifecycle_window",
        queue_status="due",
        actionability="dispatch",
        changed=True,
    )

    decision = build_proactive_lifecycle_queue_decision(
        lifecycle_window_decision=lifecycle_window,
        current_queue_status="overdue",
    )

    assert decision.lifecycle_state in {"dispatching", "softened"}
    assert decision.queue_mode == "overdue_lifecycle_queue"
    assert decision.decision == "overdue_lifecycle_queue"
    assert decision.queue_status == "overdue"
    assert decision.actionability == "dispatch"
    assert decision.queue_key.startswith("second_touch_overdue_lifecycle_queue_")


def test_lifecycle_dispatch_uses_queue_posture_as_authoritative_gate() -> None:
    lifecycle_queue = _lifecycle_queue_decision()

    dispatch = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=lifecycle_queue,
        current_queue_status="due",
        rendered_unit_count=2,
        has_followup_content=True,
    )
    assert dispatch.dispatch_mode == "ready_lifecycle_dispatch"
    assert dispatch.decision == "dispatch_lifecycle_now"

    close_loop = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            lifecycle_state="winding_down",
            queue_mode="close_loop_lifecycle_queue",
            decision="close_loop_lifecycle_queue",
            actionability="close_loop",
        ),
        current_queue_status="due",
        rendered_unit_count=1,
        has_followup_content=True,
    )
    assert close_loop.dispatch_mode == "close_loop_lifecycle_dispatch"
    assert close_loop.decision == "close_loop_lifecycle_dispatch"

    rescheduled = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            status="scheduled",
            queue_mode="buffered_lifecycle_queue",
            decision="buffer_lifecycle_queue",
            queue_status="scheduled",
            actionability="buffer",
        ),
        current_queue_status="scheduled",
        rendered_unit_count=1,
        has_followup_content=True,
    )
    assert rescheduled.dispatch_mode == "rescheduled_lifecycle_dispatch"
    assert rescheduled.decision == "reschedule_lifecycle_dispatch"

    held = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            status="hold",
            queue_mode="hold_lifecycle_queue",
            decision="hold_lifecycle_queue",
            queue_status="hold",
            actionability="hold",
        ),
        current_queue_status="hold",
        rendered_unit_count=1,
        has_followup_content=True,
    )
    assert held.dispatch_mode == "hold_lifecycle_dispatch"
    assert held.decision == "hold_lifecycle_dispatch"

    retired = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            status="terminal",
            lifecycle_state="terminal",
            queue_mode="terminal_lifecycle_queue",
            decision="retire_lifecycle_queue",
            queue_status="terminal",
            actionability="retire",
        ),
        current_queue_status="terminal",
        rendered_unit_count=1,
        has_followup_content=True,
    )
    assert retired.dispatch_mode == "terminal_lifecycle_dispatch"
    assert retired.decision == "retire_lifecycle_dispatch"


def test_lifecycle_dispatch_holds_when_followup_render_is_empty() -> None:
    lifecycle_queue = _lifecycle_queue_decision(
        current_stage_label="first_touch",
        queue_key="first_touch_dispatch_lifecycle_queue_progress_micro_commitment",
        selected_strategy_key="progress_micro_commitment",
        selected_pressure_mode="low_pressure_progress",
        selected_autonomy_signal="explicit_opt_out",
        selected_delivery_mode="two_part_sequence",
    )

    decision = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=lifecycle_queue,
        current_queue_status="due",
        rendered_unit_count=0,
        has_followup_content=False,
    )

    assert decision.dispatch_mode == "hold_lifecycle_dispatch"
    assert decision.decision == "hold_lifecycle_dispatch"
    assert "empty_followup_units" in decision.dispatch_notes


def test_lifecycle_outcome_tracks_dispatch_result() -> None:
    lifecycle_queue = _lifecycle_queue_decision()

    dispatch = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=lifecycle_queue,
        current_queue_status="due",
        rendered_unit_count=2,
        has_followup_content=True,
    )
    sent = build_proactive_lifecycle_outcome_decision(
        lifecycle_dispatch_decision=dispatch,
        dispatched=True,
        message_event_count=2,
    )
    assert sent.outcome_mode == "sent_lifecycle_outcome"
    assert sent.decision == "lifecycle_dispatch_sent"
    assert sent.message_event_count == 2

    close_loop_dispatch = build_proactive_lifecycle_dispatch_decision(
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            lifecycle_state="winding_down",
            queue_mode="close_loop_lifecycle_queue",
            decision="close_loop_lifecycle_queue",
            actionability="close_loop",
        ),
        current_queue_status="due",
        rendered_unit_count=1,
        has_followup_content=True,
    )
    close_loop = build_proactive_lifecycle_outcome_decision(
        lifecycle_dispatch_decision=close_loop_dispatch,
        dispatched=True,
        message_event_count=1,
    )
    assert close_loop.outcome_mode == "close_loop_sent_lifecycle_outcome"
    assert close_loop.decision == "lifecycle_close_loop_sent"

    rescheduled = build_proactive_lifecycle_outcome_decision(
        lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
            lifecycle_queue_decision=replace(
                lifecycle_queue,
                status="scheduled",
                queue_mode="buffered_lifecycle_queue",
                decision="buffer_lifecycle_queue",
                queue_status="scheduled",
                actionability="buffer",
            ),
            current_queue_status="scheduled",
            rendered_unit_count=1,
            has_followup_content=True,
        ),
        dispatched=False,
    )
    assert rescheduled.outcome_mode == "rescheduled_lifecycle_outcome"
    assert rescheduled.decision == "lifecycle_dispatch_rescheduled"

    held = build_proactive_lifecycle_outcome_decision(
        lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
            lifecycle_queue_decision=replace(
                lifecycle_queue,
                status="hold",
                queue_mode="hold_lifecycle_queue",
                decision="hold_lifecycle_queue",
                queue_status="hold",
                actionability="hold",
            ),
            current_queue_status="hold",
            rendered_unit_count=0,
            has_followup_content=False,
        ),
        dispatched=False,
    )
    assert held.outcome_mode == "hold_lifecycle_outcome"
    assert held.decision == "lifecycle_dispatch_held"
    assert "empty_followup_units" in held.outcome_notes

    retired = build_proactive_lifecycle_outcome_decision(
        lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
            lifecycle_queue_decision=replace(
                lifecycle_queue,
                status="terminal",
                lifecycle_state="terminal",
                queue_mode="terminal_lifecycle_queue",
                decision="retire_lifecycle_queue",
                queue_status="terminal",
                actionability="retire",
            ),
            current_queue_status="terminal",
            rendered_unit_count=1,
            has_followup_content=True,
        ),
        dispatched=False,
    )
    assert retired.outcome_mode == "retired_lifecycle_outcome"
    assert retired.decision == "lifecycle_dispatch_retired"


def test_lifecycle_resolution_tracks_post_dispatch_line_result() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    sent_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    assert sent_resolution.resolution_mode == "active_lifecycle_resolution"
    assert sent_resolution.decision == "continue_lifecycle_resolution"
    assert sent_resolution.queue_override_status is None
    assert sent_resolution.remaining_stage_count == 1

    buffered_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=replace(
                    lifecycle_queue,
                    status="scheduled",
                    queue_mode="buffered_lifecycle_queue",
                    decision="buffer_lifecycle_queue",
                    queue_status="scheduled",
                    actionability="buffer",
                    additional_delay_seconds=600,
                ),
                current_queue_status="scheduled",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=False,
        ),
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            status="scheduled",
            queue_mode="buffered_lifecycle_queue",
            decision="buffer_lifecycle_queue",
            queue_status="scheduled",
            actionability="buffer",
            additional_delay_seconds=600,
        ),
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    assert buffered_resolution.resolution_mode == "buffered_lifecycle_resolution"
    assert buffered_resolution.decision == "buffer_lifecycle_resolution"
    assert buffered_resolution.queue_override_status == "scheduled"

    buffered_close_loop_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=replace(
                    lifecycle_queue,
                    lifecycle_state="winding_down",
                    queue_mode="close_loop_lifecycle_queue",
                    decision="close_loop_lifecycle_queue",
                    queue_status="scheduled",
                    actionability="close_loop",
                    additional_delay_seconds=900,
                ),
                current_queue_status="scheduled",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=False,
        ),
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            lifecycle_state="winding_down",
            queue_mode="close_loop_lifecycle_queue",
            decision="close_loop_lifecycle_queue",
            queue_status="scheduled",
            actionability="close_loop",
            additional_delay_seconds=900,
        ),
        line_state_decision=replace(
            line_state,
            remaining_stage_count=1,
            lifecycle_mode="winding_down",
            actionability="close_loop",
        ),
        line_transition_decision=replace(
            line_transition,
            transition_mode="close_loop_line",
            line_exit_mode="close_loop",
            next_stage_label=None,
            next_stage_index=None,
            next_lifecycle_mode="winding_down",
        ),
    )
    assert buffered_close_loop_resolution.resolution_mode == "buffered_lifecycle_resolution"
    assert buffered_close_loop_resolution.decision == "buffer_lifecycle_resolution"
    assert buffered_close_loop_resolution.queue_override_status == "scheduled"

    retired_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=replace(
                    lifecycle_queue,
                    lifecycle_state="winding_down",
                    queue_mode="close_loop_lifecycle_queue",
                    decision="close_loop_lifecycle_queue",
                    actionability="close_loop",
                ),
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=replace(
            lifecycle_queue,
            lifecycle_state="winding_down",
            queue_mode="close_loop_lifecycle_queue",
            decision="close_loop_lifecycle_queue",
            actionability="close_loop",
        ),
        line_state_decision=replace(
            line_state,
            remaining_stage_count=1,
            lifecycle_mode="winding_down",
            actionability="close_loop",
        ),
        line_transition_decision=replace(
            line_transition,
            transition_mode="close_loop_line",
            line_exit_mode="close_loop",
            next_stage_label=None,
            next_stage_index=None,
            next_lifecycle_mode="winding_down",
        ),
    )
    assert retired_resolution.resolution_mode == "terminal_lifecycle_resolution"
    assert retired_resolution.decision == "retire_lifecycle_resolution"
    assert retired_resolution.queue_override_status == "terminal"
    assert retired_resolution.remaining_stage_count == 0


def test_lifecycle_activation_promotes_next_stage_or_retires_line() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    assert continue_activation.activation_mode == "active_lifecycle_activation"
    assert continue_activation.decision == "activate_next_lifecycle_stage"
    assert continue_activation.active_stage_label == "final_soft_close"
    assert continue_activation.queue_override_status is None

    buffered_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=replace(
            continue_resolution,
            status="scheduled",
            resolution_mode="buffered_lifecycle_resolution",
            decision="buffer_lifecycle_resolution",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered_activation.activation_mode == "buffered_lifecycle_activation"
    assert buffered_activation.decision == "buffer_current_lifecycle_stage"
    assert buffered_activation.active_stage_label == "second_touch"
    assert buffered_activation.queue_override_status == "scheduled"

    retired_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=replace(
            continue_resolution,
            status="terminal",
            resolution_mode="terminal_lifecycle_resolution",
            decision="retire_lifecycle_resolution",
            actionability="retire",
            queue_override_status="terminal",
            next_stage_label=None,
            remaining_stage_count=0,
        )
    )
    assert retired_activation.activation_mode == "terminal_lifecycle_activation"
    assert retired_activation.decision == "retire_lifecycle_line"
    assert retired_activation.active_stage_label is None
    assert retired_activation.queue_override_status == "terminal"


def test_lifecycle_settlement_tracks_active_buffer_hold_and_close_loop() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    assert active_settlement.settlement_mode == "active_lifecycle_settlement"
    assert active_settlement.decision == "keep_lifecycle_active"
    assert active_settlement.active_stage_label == "final_soft_close"
    assert active_settlement.queue_override_status is None

    buffered_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=replace(
            continue_activation,
            status="scheduled",
            activation_mode="buffered_lifecycle_activation",
            decision="buffer_current_lifecycle_stage",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered_settlement.settlement_mode == "buffered_lifecycle_settlement"
    assert buffered_settlement.decision == "buffer_lifecycle_settlement"
    assert buffered_settlement.queue_override_status == "scheduled"

    held_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=replace(
            continue_activation,
            status="hold",
            activation_mode="hold_lifecycle_activation",
            decision="hold_current_lifecycle_stage",
            actionability="hold",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert held_settlement.settlement_mode == "hold_lifecycle_settlement"
    assert held_settlement.decision == "hold_lifecycle_settlement"
    assert held_settlement.queue_override_status == "hold"

    closed_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=replace(
            continue_activation,
            status="terminal",
            activation_mode="terminal_lifecycle_activation",
            decision="retire_lifecycle_line",
            actionability="retire",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert closed_settlement.settlement_mode == "close_loop_lifecycle_settlement"
    assert closed_settlement.decision == "close_lifecycle_settlement"
    assert closed_settlement.actionability == "close_loop"


def test_lifecycle_closure_tracks_open_buffer_pause_and_close_loop() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    assert open_closure.closure_mode == "open_lifecycle_closure"
    assert open_closure.decision == "keep_open_lifecycle_closure"
    assert open_closure.active_stage_label == "final_soft_close"
    assert open_closure.queue_override_status is None

    buffered_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=replace(
            active_settlement,
            status="scheduled",
            settlement_mode="buffered_lifecycle_settlement",
            decision="buffer_lifecycle_settlement",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered_closure.closure_mode == "buffered_lifecycle_closure"
    assert buffered_closure.decision == "buffer_lifecycle_closure"
    assert buffered_closure.queue_override_status == "scheduled"

    paused_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=replace(
            active_settlement,
            status="hold",
            settlement_mode="hold_lifecycle_settlement",
            decision="hold_lifecycle_settlement",
            actionability="hold",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_closure.closure_mode == "paused_lifecycle_closure"
    assert paused_closure.decision == "pause_lifecycle_closure"
    assert paused_closure.queue_override_status == "hold"

    closed_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=replace(
            active_settlement,
            status="terminal",
            settlement_mode="close_loop_lifecycle_settlement",
            decision="close_lifecycle_settlement",
            actionability="close_loop",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert closed_closure.closure_mode == "close_loop_lifecycle_closure"
    assert closed_closure.decision == "close_loop_lifecycle_closure"
    assert closed_closure.actionability == "close_loop"


def test_lifecycle_availability_tracks_open_buffer_pause_and_close_loop() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    assert open_availability.availability_mode == "open_lifecycle_availability"
    assert open_availability.decision == "keep_lifecycle_available"
    assert open_availability.active_stage_label == "final_soft_close"
    assert open_availability.queue_override_status is None

    buffered_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=replace(
            open_closure,
            status="scheduled",
            closure_mode="buffered_lifecycle_closure",
            decision="buffer_lifecycle_closure",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered_availability.availability_mode == "buffered_lifecycle_availability"
    assert buffered_availability.decision == "buffer_lifecycle_availability"
    assert buffered_availability.queue_override_status == "scheduled"

    paused_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=replace(
            open_closure,
            status="hold",
            closure_mode="paused_lifecycle_closure",
            decision="pause_lifecycle_closure",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_availability.availability_mode == "paused_lifecycle_availability"
    assert paused_availability.decision == "pause_lifecycle_availability"
    assert paused_availability.queue_override_status == "hold"

    closed_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=replace(
            open_closure,
            status="terminal",
            closure_mode="close_loop_lifecycle_closure",
            decision="close_loop_lifecycle_closure",
            actionability="close_loop",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert closed_availability.availability_mode == "closed_lifecycle_availability"
    assert closed_availability.decision == "close_loop_lifecycle_availability"
    assert closed_availability.actionability == "close_loop"


def test_lifecycle_retention_tracks_retain_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )

    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    assert retained.retention_mode == "retained_lifecycle_retention"
    assert retained.decision == "retain_lifecycle_retention"
    assert retained.queue_override_status is None

    buffered = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=replace(
            open_availability,
            status="scheduled",
            availability_mode="buffered_lifecycle_availability",
            decision="buffer_lifecycle_availability",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.retention_mode == "buffered_lifecycle_retention"
    assert buffered.decision == "buffer_lifecycle_retention"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=replace(
            open_availability,
            status="hold",
            availability_mode="paused_lifecycle_availability",
            decision="pause_lifecycle_availability",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.retention_mode == "paused_lifecycle_retention"
    assert paused.decision == "pause_lifecycle_retention"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=replace(
            open_availability,
            status="terminal",
            availability_mode="closed_lifecycle_availability",
            decision="close_loop_lifecycle_availability",
            actionability="close_loop",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.retention_mode == "archived_lifecycle_retention"
    assert archived.decision == "archive_lifecycle_retention"
    assert archived.actionability == "archive"


def test_lifecycle_eligibility_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )

    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    assert eligible.eligibility_mode == "eligible_lifecycle_eligibility"
    assert eligible.decision == "keep_lifecycle_eligible"
    assert eligible.queue_override_status is None

    buffered = build_proactive_lifecycle_eligibility_decision(
        lifecycle_retention_decision=replace(
            retained,
            status="scheduled",
            retention_mode="buffered_lifecycle_retention",
            decision="buffer_lifecycle_retention",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.eligibility_mode == "buffered_lifecycle_eligibility"
    assert buffered.decision == "buffer_lifecycle_eligibility"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_eligibility_decision(
        lifecycle_retention_decision=replace(
            retained,
            status="hold",
            retention_mode="paused_lifecycle_retention",
            decision="pause_lifecycle_retention",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.eligibility_mode == "paused_lifecycle_eligibility"
    assert paused.decision == "pause_lifecycle_eligibility"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_eligibility_decision(
        lifecycle_retention_decision=replace(
            retained,
            status="terminal",
            retention_mode="archived_lifecycle_retention",
            decision="archive_lifecycle_retention",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.eligibility_mode == "archived_lifecycle_eligibility"
    assert archived.decision == "archive_lifecycle_eligibility"
    assert archived.actionability == "archive"


def test_lifecycle_candidate_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)

    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    assert candidate.candidate_mode == "candidate_lifecycle_candidate"
    assert candidate.decision == "keep_lifecycle_candidate"
    assert candidate.queue_override_status is None

    buffered = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=replace(
            eligible,
            status="scheduled",
            eligibility_mode="buffered_lifecycle_eligibility",
            decision="buffer_lifecycle_eligibility",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.candidate_mode == "buffered_lifecycle_candidate"
    assert buffered.decision == "buffer_lifecycle_candidate"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=replace(
            eligible,
            status="hold",
            eligibility_mode="paused_lifecycle_eligibility",
            decision="pause_lifecycle_eligibility",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.candidate_mode == "paused_lifecycle_candidate"
    assert paused.decision == "pause_lifecycle_candidate"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=replace(
            eligible,
            status="terminal",
            eligibility_mode="archived_lifecycle_eligibility",
            decision="archive_lifecycle_eligibility",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.candidate_mode == "archived_lifecycle_candidate"
    assert archived.decision == "archive_lifecycle_candidate"
    assert archived.actionability == "archive"


def test_lifecycle_selectability_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )

    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    assert selectable.selectability_mode == "selectable_lifecycle_selectability"
    assert selectable.decision == "keep_lifecycle_selectable"
    assert selectable.queue_override_status is None

    buffered = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=replace(
            candidate,
            status="scheduled",
            candidate_mode="buffered_lifecycle_candidate",
            decision="buffer_lifecycle_candidate",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.selectability_mode == "buffered_lifecycle_selectability"
    assert buffered.decision == "buffer_lifecycle_selectability"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=replace(
            candidate,
            status="hold",
            candidate_mode="paused_lifecycle_candidate",
            decision="pause_lifecycle_candidate",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.selectability_mode == "paused_lifecycle_selectability"
    assert paused.decision == "pause_lifecycle_selectability"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=replace(
            candidate,
            status="terminal",
            candidate_mode="archived_lifecycle_candidate",
            decision="archive_lifecycle_candidate",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.selectability_mode == "archived_lifecycle_selectability"
    assert archived.decision == "archive_lifecycle_selectability"
    assert archived.actionability == "archive"


def test_lifecycle_reentry_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )

    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    assert reentry.reentry_mode == "reenterable_lifecycle_reentry"
    assert reentry.decision == "keep_lifecycle_reentry"
    assert reentry.queue_override_status is None

    buffered = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=replace(
            selectable,
            status="scheduled",
            selectability_mode="buffered_lifecycle_selectability",
            decision="buffer_lifecycle_selectability",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.reentry_mode == "buffered_lifecycle_reentry"
    assert buffered.decision == "buffer_lifecycle_reentry"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=replace(
            selectable,
            status="hold",
            selectability_mode="paused_lifecycle_selectability",
            decision="pause_lifecycle_selectability",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.reentry_mode == "paused_lifecycle_reentry"
    assert paused.decision == "pause_lifecycle_reentry"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=replace(
            selectable,
            status="terminal",
            selectability_mode="archived_lifecycle_selectability",
            decision="archive_lifecycle_selectability",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.reentry_mode == "archived_lifecycle_reentry"
    assert archived.decision == "archive_lifecycle_reentry"
    assert archived.actionability == "archive"


def test_lifecycle_reactivation_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )

    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    assert reactivation.reactivation_mode == "reactivatable_lifecycle_reactivation"
    assert reactivation.decision == "keep_lifecycle_reactivation"
    assert reactivation.queue_override_status is None

    buffered = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=replace(
            reentry,
            status="scheduled",
            reentry_mode="buffered_lifecycle_reentry",
            decision="buffer_lifecycle_reentry",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.reactivation_mode == "buffered_lifecycle_reactivation"
    assert buffered.decision == "buffer_lifecycle_reactivation"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=replace(
            reentry,
            status="hold",
            reentry_mode="paused_lifecycle_reentry",
            decision="pause_lifecycle_reentry",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.reactivation_mode == "paused_lifecycle_reactivation"
    assert paused.decision == "pause_lifecycle_reactivation"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=replace(
            reentry,
            status="terminal",
            reentry_mode="archived_lifecycle_reentry",
            decision="archive_lifecycle_reentry",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.reactivation_mode == "archived_lifecycle_reactivation"
    assert archived.decision == "archive_lifecycle_reactivation"
    assert archived.actionability == "archive"


def test_lifecycle_resumption_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )

    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    assert resumption.resumption_mode == "resumable_lifecycle_resumption"
    assert resumption.decision == "keep_lifecycle_resumption"
    assert resumption.queue_override_status is None

    buffered = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=replace(
            reactivation,
            status="scheduled",
            reactivation_mode="buffered_lifecycle_reactivation",
            decision="buffer_lifecycle_reactivation",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.resumption_mode == "buffered_lifecycle_resumption"
    assert buffered.decision == "buffer_lifecycle_resumption"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=replace(
            reactivation,
            status="hold",
            reactivation_mode="paused_lifecycle_reactivation",
            decision="pause_lifecycle_reactivation",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.resumption_mode == "paused_lifecycle_resumption"
    assert paused.decision == "pause_lifecycle_resumption"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=replace(
            reactivation,
            status="terminal",
            reactivation_mode="archived_lifecycle_reactivation",
            decision="archive_lifecycle_reactivation",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.resumption_mode == "archived_lifecycle_resumption"
    assert archived.decision == "archive_lifecycle_resumption"
    assert archived.actionability == "archive"


def test_lifecycle_readiness_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )

    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    assert readiness.readiness_mode == "ready_lifecycle_readiness"
    assert readiness.decision == "keep_lifecycle_readiness"
    assert readiness.queue_override_status is None

    buffered = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=replace(
            resumption,
            status="scheduled",
            resumption_mode="buffered_lifecycle_resumption",
            decision="buffer_lifecycle_resumption",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.readiness_mode == "buffered_lifecycle_readiness"
    assert buffered.decision == "buffer_lifecycle_readiness"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=replace(
            resumption,
            status="hold",
            resumption_mode="paused_lifecycle_resumption",
            decision="pause_lifecycle_resumption",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.readiness_mode == "paused_lifecycle_readiness"
    assert paused.decision == "pause_lifecycle_readiness"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=replace(
            resumption,
            status="terminal",
            resumption_mode="archived_lifecycle_resumption",
            decision="archive_lifecycle_resumption",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.readiness_mode == "archived_lifecycle_readiness"
    assert archived.decision == "archive_lifecycle_readiness"
    assert archived.actionability == "archive"


def test_lifecycle_arming_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )

    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    assert arming.arming_mode == "armed_lifecycle_arming"
    assert arming.decision == "keep_lifecycle_arming"
    assert arming.queue_override_status is None

    buffered = build_proactive_lifecycle_arming_decision(
        lifecycle_readiness_decision=replace(
            readiness,
            status="scheduled",
            readiness_mode="buffered_lifecycle_readiness",
            decision="buffer_lifecycle_readiness",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.arming_mode == "buffered_lifecycle_arming"
    assert buffered.decision == "buffer_lifecycle_arming"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_arming_decision(
        lifecycle_readiness_decision=replace(
            readiness,
            status="hold",
            readiness_mode="paused_lifecycle_readiness",
            decision="pause_lifecycle_readiness",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.arming_mode == "paused_lifecycle_arming"
    assert paused.decision == "pause_lifecycle_arming"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_arming_decision(
        lifecycle_readiness_decision=replace(
            readiness,
            status="terminal",
            readiness_mode="archived_lifecycle_readiness",
            decision="archive_lifecycle_readiness",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.arming_mode == "archived_lifecycle_arming"
    assert archived.decision == "archive_lifecycle_arming"
    assert archived.actionability == "archive"


def test_lifecycle_trigger_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)

    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    assert trigger.trigger_mode == "triggerable_lifecycle_trigger"
    assert trigger.decision == "keep_lifecycle_trigger"
    assert trigger.queue_override_status is None

    buffered = build_proactive_lifecycle_trigger_decision(
        lifecycle_arming_decision=replace(
            arming,
            status="scheduled",
            arming_mode="buffered_lifecycle_arming",
            decision="buffer_lifecycle_arming",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.trigger_mode == "buffered_lifecycle_trigger"
    assert buffered.decision == "buffer_lifecycle_trigger"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_trigger_decision(
        lifecycle_arming_decision=replace(
            arming,
            status="hold",
            arming_mode="paused_lifecycle_arming",
            decision="pause_lifecycle_arming",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.trigger_mode == "paused_lifecycle_trigger"
    assert paused.decision == "pause_lifecycle_trigger"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_trigger_decision(
        lifecycle_arming_decision=replace(
            arming,
            status="terminal",
            arming_mode="archived_lifecycle_arming",
            decision="archive_lifecycle_arming",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.trigger_mode == "archived_lifecycle_trigger"
    assert archived.decision == "archive_lifecycle_trigger"
    assert archived.actionability == "archive"


def test_lifecycle_launch_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)

    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    assert launch.launch_mode == "launchable_lifecycle_launch"
    assert launch.decision == "keep_lifecycle_launch"
    assert launch.queue_override_status is None

    buffered = build_proactive_lifecycle_launch_decision(
        lifecycle_trigger_decision=replace(
            trigger,
            status="scheduled",
            trigger_mode="buffered_lifecycle_trigger",
            decision="buffer_lifecycle_trigger",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.launch_mode == "buffered_lifecycle_launch"
    assert buffered.decision == "buffer_lifecycle_launch"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_launch_decision(
        lifecycle_trigger_decision=replace(
            trigger,
            status="hold",
            trigger_mode="paused_lifecycle_trigger",
            decision="pause_lifecycle_trigger",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.launch_mode == "paused_lifecycle_launch"
    assert paused.decision == "pause_lifecycle_launch"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_launch_decision(
        lifecycle_trigger_decision=replace(
            trigger,
            status="terminal",
            trigger_mode="archived_lifecycle_trigger",
            decision="archive_lifecycle_trigger",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.launch_mode == "archived_lifecycle_launch"
    assert archived.decision == "archive_lifecycle_launch"
    assert archived.actionability == "archive"


def test_lifecycle_handoff_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)

    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    assert handoff.handoff_mode == "handoff_ready_lifecycle_handoff"
    assert handoff.decision == "keep_lifecycle_handoff"
    assert handoff.queue_override_status is None

    buffered = build_proactive_lifecycle_handoff_decision(
        lifecycle_launch_decision=replace(
            launch,
            status="scheduled",
            launch_mode="buffered_lifecycle_launch",
            decision="buffer_lifecycle_launch",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.handoff_mode == "buffered_lifecycle_handoff"
    assert buffered.decision == "buffer_lifecycle_handoff"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_handoff_decision(
        lifecycle_launch_decision=replace(
            launch,
            status="hold",
            launch_mode="paused_lifecycle_launch",
            decision="pause_lifecycle_launch",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.handoff_mode == "paused_lifecycle_handoff"
    assert paused.decision == "pause_lifecycle_handoff"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_handoff_decision(
        lifecycle_launch_decision=replace(
            launch,
            status="terminal",
            launch_mode="archived_lifecycle_launch",
            decision="archive_lifecycle_launch",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.handoff_mode == "archived_lifecycle_handoff"
    assert archived.decision == "archive_lifecycle_handoff"
    assert archived.actionability == "archive"


def test_lifecycle_continuation_tracks_keep_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)

    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    assert continuation.continuation_mode == "continuable_lifecycle_continuation"
    assert continuation.decision == "keep_lifecycle_continuation"
    assert continuation.queue_override_status is None

    buffered = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=replace(
            handoff,
            status="scheduled",
            handoff_mode="buffered_lifecycle_handoff",
            decision="buffer_lifecycle_handoff",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.continuation_mode == "buffered_lifecycle_continuation"
    assert buffered.decision == "buffer_lifecycle_continuation"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=replace(
            handoff,
            status="hold",
            handoff_mode="paused_lifecycle_handoff",
            decision="pause_lifecycle_handoff",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.continuation_mode == "paused_lifecycle_continuation"
    assert paused.decision == "pause_lifecycle_continuation"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=replace(
            handoff,
            status="terminal",
            handoff_mode="archived_lifecycle_handoff",
            decision="archive_lifecycle_handoff",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.continuation_mode == "archived_lifecycle_continuation"
    assert archived.decision == "archive_lifecycle_continuation"
    assert archived.actionability == "archive"


def test_lifecycle_sustainment_tracks_sustain_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )

    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    assert sustainment.sustainment_mode == "sustainable_lifecycle_sustainment"
    assert sustainment.decision == "sustain_lifecycle_sustainment"
    assert sustainment.queue_override_status is None

    buffered = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=replace(
            continuation,
            status="scheduled",
            continuation_mode="buffered_lifecycle_continuation",
            decision="buffer_lifecycle_continuation",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=600,
        )
    )
    assert buffered.sustainment_mode == "buffered_lifecycle_sustainment"
    assert buffered.decision == "buffer_lifecycle_sustainment"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=replace(
            continuation,
            status="hold",
            continuation_mode="paused_lifecycle_continuation",
            decision="pause_lifecycle_continuation",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.sustainment_mode == "paused_lifecycle_sustainment"
    assert paused.decision == "pause_lifecycle_sustainment"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=replace(
            continuation,
            status="terminal",
            continuation_mode="archived_lifecycle_continuation",
            decision="archive_lifecycle_continuation",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.sustainment_mode == "archived_lifecycle_sustainment"
    assert archived.decision == "archive_lifecycle_sustainment"
    assert archived.actionability == "archive"


def test_lifecycle_stewardship_tracks_steward_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )

    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    assert stewardship.stewardship_mode == "stewarded_lifecycle_stewardship"
    assert stewardship.decision == "steward_lifecycle_stewardship"
    assert stewardship.queue_override_status is None

    buffered = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=replace(
            sustainment,
            status="scheduled",
            sustainment_mode="buffered_lifecycle_sustainment",
            decision="buffer_lifecycle_sustainment",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.stewardship_mode == "buffered_lifecycle_stewardship"
    assert buffered.decision == "buffer_lifecycle_stewardship"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=replace(
            sustainment,
            status="hold",
            sustainment_mode="paused_lifecycle_sustainment",
            decision="pause_lifecycle_sustainment",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.stewardship_mode == "paused_lifecycle_stewardship"
    assert paused.decision == "pause_lifecycle_stewardship"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=replace(
            sustainment,
            status="terminal",
            sustainment_mode="archived_lifecycle_sustainment",
            decision="archive_lifecycle_sustainment",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.stewardship_mode == "archived_lifecycle_stewardship"
    assert archived.decision == "archive_lifecycle_stewardship"
    assert archived.actionability == "archive"


def test_lifecycle_guardianship_tracks_guard_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )

    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )
    assert guardianship.guardianship_mode == "guarded_lifecycle_guardianship"
    assert guardianship.decision == "guard_lifecycle_guardianship"
    assert guardianship.queue_override_status is None

    buffered = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=replace(
            stewardship,
            status="scheduled",
            stewardship_mode="buffered_lifecycle_stewardship",
            decision="buffer_lifecycle_stewardship",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.guardianship_mode == "buffered_lifecycle_guardianship"
    assert buffered.decision == "buffer_lifecycle_guardianship"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=replace(
            stewardship,
            status="hold",
            stewardship_mode="paused_lifecycle_stewardship",
            decision="pause_lifecycle_stewardship",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.guardianship_mode == "paused_lifecycle_guardianship"
    assert paused.decision == "pause_lifecycle_guardianship"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=replace(
            stewardship,
            status="terminal",
            stewardship_mode="archived_lifecycle_stewardship",
            decision="archive_lifecycle_stewardship",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.guardianship_mode == "archived_lifecycle_guardianship"
    assert archived.decision == "archive_lifecycle_guardianship"
    assert archived.actionability == "archive"


def test_lifecycle_oversight_tracks_oversee_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )

    oversight = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=guardianship
    )
    assert oversight.oversight_mode == "overseen_lifecycle_oversight"
    assert oversight.decision == "oversee_lifecycle_oversight"
    assert oversight.queue_override_status is None

    buffered = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=replace(
            guardianship,
            status="scheduled",
            guardianship_mode="buffered_lifecycle_guardianship",
            decision="buffer_lifecycle_guardianship",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.oversight_mode == "buffered_lifecycle_oversight"
    assert buffered.decision == "buffer_lifecycle_oversight"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=replace(
            guardianship,
            status="hold",
            guardianship_mode="paused_lifecycle_guardianship",
            decision="pause_lifecycle_guardianship",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.oversight_mode == "paused_lifecycle_oversight"
    assert paused.decision == "pause_lifecycle_oversight"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=replace(
            guardianship,
            status="terminal",
            guardianship_mode="archived_lifecycle_guardianship",
            decision="archive_lifecycle_guardianship",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.oversight_mode == "archived_lifecycle_oversight"
    assert archived.decision == "archive_lifecycle_oversight"
    assert archived.actionability == "archive"


def test_lifecycle_assurance_tracks_assure_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )
    oversight = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=guardianship
    )

    assurance = build_proactive_lifecycle_assurance_decision(lifecycle_oversight_decision=oversight)
    assert assurance.assurance_mode == "assured_lifecycle_assurance"
    assert assurance.decision == "assure_lifecycle_assurance"
    assert assurance.queue_override_status is None

    buffered = build_proactive_lifecycle_assurance_decision(
        lifecycle_oversight_decision=replace(
            oversight,
            status="scheduled",
            oversight_mode="buffered_lifecycle_oversight",
            decision="buffer_lifecycle_oversight",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.assurance_mode == "buffered_lifecycle_assurance"
    assert buffered.decision == "buffer_lifecycle_assurance"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_assurance_decision(
        lifecycle_oversight_decision=replace(
            oversight,
            status="hold",
            oversight_mode="paused_lifecycle_oversight",
            decision="pause_lifecycle_oversight",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.assurance_mode == "paused_lifecycle_assurance"
    assert paused.decision == "pause_lifecycle_assurance"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_assurance_decision(
        lifecycle_oversight_decision=replace(
            oversight,
            status="terminal",
            oversight_mode="archived_lifecycle_oversight",
            decision="archive_lifecycle_oversight",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.assurance_mode == "archived_lifecycle_assurance"
    assert archived.decision == "archive_lifecycle_assurance"
    assert archived.actionability == "archive"


def test_lifecycle_attestation_tracks_attest_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )
    oversight = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=guardianship
    )
    assurance = build_proactive_lifecycle_assurance_decision(lifecycle_oversight_decision=oversight)

    attestation = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=assurance
    )
    assert attestation.attestation_mode == "attested_lifecycle_attestation"
    assert attestation.decision == "attest_lifecycle_attestation"
    assert attestation.queue_override_status is None

    buffered = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=replace(
            assurance,
            status="scheduled",
            assurance_mode="buffered_lifecycle_assurance",
            decision="buffer_lifecycle_assurance",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.attestation_mode == "buffered_lifecycle_attestation"
    assert buffered.decision == "buffer_lifecycle_attestation"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=replace(
            assurance,
            status="hold",
            assurance_mode="paused_lifecycle_assurance",
            decision="pause_lifecycle_assurance",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.attestation_mode == "paused_lifecycle_attestation"
    assert paused.decision == "pause_lifecycle_attestation"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=replace(
            assurance,
            status="terminal",
            assurance_mode="archived_lifecycle_assurance",
            decision="archive_lifecycle_assurance",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.attestation_mode == "archived_lifecycle_attestation"
    assert archived.decision == "archive_lifecycle_attestation"
    assert archived.actionability == "archive"


def test_lifecycle_verification_tracks_verify_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )
    oversight = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=guardianship
    )
    assurance = build_proactive_lifecycle_assurance_decision(lifecycle_oversight_decision=oversight)
    attestation = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=assurance
    )

    verification = build_proactive_lifecycle_verification_decision(
        lifecycle_attestation_decision=attestation
    )
    assert verification.verification_mode == "verified_lifecycle_verification"
    assert verification.decision == "verify_lifecycle_verification"
    assert verification.queue_override_status is None

    buffered = build_proactive_lifecycle_verification_decision(
        lifecycle_attestation_decision=replace(
            attestation,
            status="scheduled",
            attestation_mode="buffered_lifecycle_attestation",
            decision="buffer_lifecycle_attestation",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.verification_mode == "buffered_lifecycle_verification"
    assert buffered.decision == "buffer_lifecycle_verification"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_verification_decision(
        lifecycle_attestation_decision=replace(
            attestation,
            status="hold",
            attestation_mode="paused_lifecycle_attestation",
            decision="pause_lifecycle_attestation",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.verification_mode == "paused_lifecycle_verification"
    assert paused.decision == "pause_lifecycle_verification"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_verification_decision(
        lifecycle_attestation_decision=replace(
            attestation,
            status="terminal",
            attestation_mode="archived_lifecycle_attestation",
            decision="archive_lifecycle_attestation",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.verification_mode == "archived_lifecycle_verification"
    assert archived.decision == "archive_lifecycle_verification"
    assert archived.actionability == "archive"


def test_lifecycle_certification_tracks_certify_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )
    oversight = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=guardianship
    )
    assurance = build_proactive_lifecycle_assurance_decision(lifecycle_oversight_decision=oversight)
    attestation = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=assurance
    )
    verification = build_proactive_lifecycle_verification_decision(
        lifecycle_attestation_decision=attestation
    )

    certification = build_proactive_lifecycle_certification_decision(
        lifecycle_verification_decision=verification
    )
    assert certification.certification_mode == "certified_lifecycle_certification"
    assert certification.decision == "certify_lifecycle_certification"
    assert certification.queue_override_status is None

    buffered = build_proactive_lifecycle_certification_decision(
        lifecycle_verification_decision=replace(
            verification,
            status="scheduled",
            verification_mode="buffered_lifecycle_verification",
            decision="buffer_lifecycle_verification",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.certification_mode == "buffered_lifecycle_certification"
    assert buffered.decision == "buffer_lifecycle_certification"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_certification_decision(
        lifecycle_verification_decision=replace(
            verification,
            status="hold",
            verification_mode="paused_lifecycle_verification",
            decision="pause_lifecycle_verification",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.certification_mode == "paused_lifecycle_certification"
    assert paused.decision == "pause_lifecycle_certification"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_certification_decision(
        lifecycle_verification_decision=replace(
            verification,
            status="terminal",
            verification_mode="archived_lifecycle_verification",
            decision="archive_lifecycle_verification",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.certification_mode == "archived_lifecycle_certification"
    assert archived.decision == "archive_lifecycle_certification"
    assert archived.actionability == "archive"


def test_lifecycle_confirmation_tracks_confirm_buffer_pause_and_archive() -> None:
    lifecycle_queue = _lifecycle_queue_decision()
    line_state = _line_state_decision()
    line_transition = _line_transition_decision()

    continue_resolution = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=build_proactive_lifecycle_outcome_decision(
            lifecycle_dispatch_decision=build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=lifecycle_queue,
                current_queue_status="due",
                rendered_unit_count=1,
                has_followup_content=True,
            ),
            dispatched=True,
            message_event_count=1,
        ),
        lifecycle_queue_decision=lifecycle_queue,
        line_state_decision=line_state,
        line_transition_decision=line_transition,
    )
    continue_activation = build_proactive_lifecycle_activation_decision(
        lifecycle_resolution_decision=continue_resolution
    )
    active_settlement = build_proactive_lifecycle_settlement_decision(
        lifecycle_activation_decision=continue_activation
    )
    open_closure = build_proactive_lifecycle_closure_decision(
        lifecycle_settlement_decision=active_settlement
    )
    open_availability = build_proactive_lifecycle_availability_decision(
        lifecycle_closure_decision=open_closure
    )
    retained = build_proactive_lifecycle_retention_decision(
        lifecycle_availability_decision=open_availability
    )
    eligible = build_proactive_lifecycle_eligibility_decision(lifecycle_retention_decision=retained)
    candidate = build_proactive_lifecycle_candidate_decision(
        lifecycle_eligibility_decision=eligible
    )
    selectable = build_proactive_lifecycle_selectability_decision(
        lifecycle_candidate_decision=candidate
    )
    reentry = build_proactive_lifecycle_reentry_decision(
        lifecycle_selectability_decision=selectable
    )
    reactivation = build_proactive_lifecycle_reactivation_decision(
        lifecycle_reentry_decision=reentry
    )
    resumption = build_proactive_lifecycle_resumption_decision(
        lifecycle_reactivation_decision=reactivation
    )
    readiness = build_proactive_lifecycle_readiness_decision(
        lifecycle_resumption_decision=resumption
    )
    arming = build_proactive_lifecycle_arming_decision(lifecycle_readiness_decision=readiness)
    trigger = build_proactive_lifecycle_trigger_decision(lifecycle_arming_decision=arming)
    launch = build_proactive_lifecycle_launch_decision(lifecycle_trigger_decision=trigger)
    handoff = build_proactive_lifecycle_handoff_decision(lifecycle_launch_decision=launch)
    continuation = build_proactive_lifecycle_continuation_decision(
        lifecycle_handoff_decision=handoff
    )
    sustainment = build_proactive_lifecycle_sustainment_decision(
        lifecycle_continuation_decision=continuation
    )
    stewardship = build_proactive_lifecycle_stewardship_decision(
        lifecycle_sustainment_decision=sustainment
    )
    guardianship = build_proactive_lifecycle_guardianship_decision(
        lifecycle_stewardship_decision=stewardship
    )
    oversight = build_proactive_lifecycle_oversight_decision(
        lifecycle_guardianship_decision=guardianship
    )
    assurance = build_proactive_lifecycle_assurance_decision(lifecycle_oversight_decision=oversight)
    attestation = build_proactive_lifecycle_attestation_decision(
        lifecycle_assurance_decision=assurance
    )
    verification = build_proactive_lifecycle_verification_decision(
        lifecycle_attestation_decision=attestation
    )
    certification = build_proactive_lifecycle_certification_decision(
        lifecycle_verification_decision=verification
    )

    confirmation = build_proactive_lifecycle_confirmation_decision(
        lifecycle_certification_decision=certification
    )
    assert confirmation.confirmation_mode == "confirmed_lifecycle_confirmation"
    assert confirmation.decision == "confirm_lifecycle_confirmation"
    assert confirmation.queue_override_status is None

    buffered = build_proactive_lifecycle_confirmation_decision(
        lifecycle_certification_decision=replace(
            certification,
            status="scheduled",
            certification_mode="buffered_lifecycle_certification",
            decision="buffer_lifecycle_certification",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered.confirmation_mode == "buffered_lifecycle_confirmation"
    assert buffered.decision == "buffer_lifecycle_confirmation"
    assert buffered.queue_override_status == "scheduled"

    paused = build_proactive_lifecycle_confirmation_decision(
        lifecycle_certification_decision=replace(
            certification,
            status="hold",
            certification_mode="paused_lifecycle_certification",
            decision="pause_lifecycle_certification",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused.confirmation_mode == "paused_lifecycle_confirmation"
    assert paused.decision == "pause_lifecycle_confirmation"
    assert paused.queue_override_status == "hold"

    archived = build_proactive_lifecycle_confirmation_decision(
        lifecycle_certification_decision=replace(
            certification,
            status="terminal",
            certification_mode="archived_lifecycle_certification",
            decision="archive_lifecycle_certification",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived.confirmation_mode == "archived_lifecycle_confirmation"
    assert archived.decision == "archive_lifecycle_confirmation"
    assert archived.actionability == "archive"

    ratified = build_proactive_lifecycle_ratification_decision(
        lifecycle_confirmation_decision=confirmation
    )
    assert ratified.ratification_mode == "ratified_lifecycle_ratification"
    assert ratified.decision == "ratify_lifecycle_ratification"
    assert ratified.queue_override_status is None

    buffered_ratification = build_proactive_lifecycle_ratification_decision(
        lifecycle_confirmation_decision=replace(
            confirmation,
            status="scheduled",
            confirmation_mode="buffered_lifecycle_confirmation",
            decision="buffer_lifecycle_confirmation",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered_ratification.ratification_mode == "buffered_lifecycle_ratification"
    assert buffered_ratification.decision == "buffer_lifecycle_ratification"
    assert buffered_ratification.queue_override_status == "scheduled"

    paused_ratification = build_proactive_lifecycle_ratification_decision(
        lifecycle_confirmation_decision=replace(
            confirmation,
            status="hold",
            confirmation_mode="paused_lifecycle_confirmation",
            decision="pause_lifecycle_confirmation",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_ratification.ratification_mode == "paused_lifecycle_ratification"
    assert paused_ratification.decision == "pause_lifecycle_ratification"
    assert paused_ratification.queue_override_status == "hold"

    archived_ratification = build_proactive_lifecycle_ratification_decision(
        lifecycle_confirmation_decision=replace(
            confirmation,
            status="terminal",
            confirmation_mode="archived_lifecycle_confirmation",
            decision="archive_lifecycle_confirmation",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_ratification.ratification_mode == "archived_lifecycle_ratification"
    assert archived_ratification.decision == "archive_lifecycle_ratification"
    assert archived_ratification.actionability == "archive"

    endorsed = build_proactive_lifecycle_endorsement_decision(
        lifecycle_ratification_decision=ratified
    )
    assert endorsed.endorsement_mode == "endorsed_lifecycle_endorsement"
    assert endorsed.decision == "endorse_lifecycle_endorsement"
    assert endorsed.queue_override_status is None

    buffered_endorsement = build_proactive_lifecycle_endorsement_decision(
        lifecycle_ratification_decision=replace(
            ratified,
            status="scheduled",
            ratification_mode="buffered_lifecycle_ratification",
            decision="buffer_lifecycle_ratification",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered_endorsement.endorsement_mode == "buffered_lifecycle_endorsement"
    assert buffered_endorsement.decision == "buffer_lifecycle_endorsement"
    assert buffered_endorsement.queue_override_status == "scheduled"

    paused_endorsement = build_proactive_lifecycle_endorsement_decision(
        lifecycle_ratification_decision=replace(
            ratified,
            status="hold",
            ratification_mode="paused_lifecycle_ratification",
            decision="pause_lifecycle_ratification",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_endorsement.endorsement_mode == "paused_lifecycle_endorsement"
    assert paused_endorsement.decision == "pause_lifecycle_endorsement"
    assert paused_endorsement.queue_override_status == "hold"

    archived_endorsement = build_proactive_lifecycle_endorsement_decision(
        lifecycle_ratification_decision=replace(
            ratified,
            status="terminal",
            ratification_mode="archived_lifecycle_ratification",
            decision="archive_lifecycle_ratification",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_endorsement.endorsement_mode == "archived_lifecycle_endorsement"
    assert archived_endorsement.decision == "archive_lifecycle_endorsement"
    assert archived_endorsement.actionability == "archive"

    authorized = build_proactive_lifecycle_authorization_decision(
        lifecycle_endorsement_decision=endorsed
    )
    assert authorized.authorization_mode == "authorized_lifecycle_authorization"
    assert authorized.decision == "authorize_lifecycle_authorization"
    assert authorized.queue_override_status is None

    buffered_authorization = build_proactive_lifecycle_authorization_decision(
        lifecycle_endorsement_decision=replace(
            endorsed,
            status="scheduled",
            endorsement_mode="buffered_lifecycle_endorsement",
            decision="buffer_lifecycle_endorsement",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered_authorization.authorization_mode == "buffered_lifecycle_authorization"
    assert buffered_authorization.decision == "buffer_lifecycle_authorization"
    assert buffered_authorization.queue_override_status == "scheduled"

    paused_authorization = build_proactive_lifecycle_authorization_decision(
        lifecycle_endorsement_decision=replace(
            endorsed,
            status="hold",
            endorsement_mode="paused_lifecycle_endorsement",
            decision="pause_lifecycle_endorsement",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_authorization.authorization_mode == "paused_lifecycle_authorization"
    assert paused_authorization.decision == "pause_lifecycle_authorization"
    assert paused_authorization.queue_override_status == "hold"

    archived_authorization = build_proactive_lifecycle_authorization_decision(
        lifecycle_endorsement_decision=replace(
            endorsed,
            status="terminal",
            endorsement_mode="archived_lifecycle_endorsement",
            decision="archive_lifecycle_endorsement",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_authorization.authorization_mode == "archived_lifecycle_authorization"
    assert archived_authorization.decision == "archive_lifecycle_authorization"
    assert archived_authorization.actionability == "archive"

    enacted = build_proactive_lifecycle_enactment_decision(
        lifecycle_authorization_decision=authorized
    )
    assert enacted.enactment_mode == "enacted_lifecycle_enactment"
    assert enacted.decision == "enact_lifecycle_enactment"
    assert enacted.queue_override_status is None

    buffered_enactment = build_proactive_lifecycle_enactment_decision(
        lifecycle_authorization_decision=replace(
            authorized,
            status="scheduled",
            authorization_mode="buffered_lifecycle_authorization",
            decision="buffer_lifecycle_authorization",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered_enactment.enactment_mode == "buffered_lifecycle_enactment"
    assert buffered_enactment.decision == "buffer_lifecycle_enactment"
    assert buffered_enactment.queue_override_status == "scheduled"

    paused_enactment = build_proactive_lifecycle_enactment_decision(
        lifecycle_authorization_decision=replace(
            authorized,
            status="hold",
            authorization_mode="paused_lifecycle_authorization",
            decision="pause_lifecycle_authorization",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_enactment.enactment_mode == "paused_lifecycle_enactment"
    assert paused_enactment.decision == "pause_lifecycle_enactment"
    assert paused_enactment.queue_override_status == "hold"

    archived_enactment = build_proactive_lifecycle_enactment_decision(
        lifecycle_authorization_decision=replace(
            authorized,
            status="terminal",
            authorization_mode="archived_lifecycle_authorization",
            decision="archive_lifecycle_authorization",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_enactment.enactment_mode == "archived_lifecycle_enactment"
    assert archived_enactment.decision == "archive_lifecycle_enactment"
    assert archived_enactment.actionability == "archive"

    finalized = build_proactive_lifecycle_finality_decision(lifecycle_enactment_decision=enacted)
    assert finalized.finality_mode == "finalized_lifecycle_finality"
    assert finalized.decision == "finalize_lifecycle_finality"
    assert finalized.queue_override_status is None

    buffered_finality = build_proactive_lifecycle_finality_decision(
        lifecycle_enactment_decision=replace(
            enacted,
            status="scheduled",
            enactment_mode="buffered_lifecycle_enactment",
            decision="buffer_lifecycle_enactment",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered_finality.finality_mode == "buffered_lifecycle_finality"
    assert buffered_finality.decision == "buffer_lifecycle_finality"
    assert buffered_finality.queue_override_status == "scheduled"

    paused_finality = build_proactive_lifecycle_finality_decision(
        lifecycle_enactment_decision=replace(
            enacted,
            status="hold",
            enactment_mode="paused_lifecycle_enactment",
            decision="pause_lifecycle_enactment",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_finality.finality_mode == "paused_lifecycle_finality"
    assert paused_finality.decision == "pause_lifecycle_finality"
    assert paused_finality.queue_override_status == "hold"

    archived_finality = build_proactive_lifecycle_finality_decision(
        lifecycle_enactment_decision=replace(
            enacted,
            status="terminal",
            enactment_mode="archived_lifecycle_enactment",
            decision="archive_lifecycle_enactment",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_finality.finality_mode == "archived_lifecycle_finality"
    assert archived_finality.decision == "archive_lifecycle_finality"
    assert archived_finality.actionability == "archive"

    completed = build_proactive_lifecycle_completion_decision(lifecycle_finality_decision=finalized)
    assert completed.completion_mode == "completed_lifecycle_completion"
    assert completed.decision == "complete_lifecycle_completion"
    assert completed.queue_override_status is None

    buffered_completion = build_proactive_lifecycle_completion_decision(
        lifecycle_finality_decision=replace(
            finalized,
            status="scheduled",
            finality_mode="buffered_lifecycle_finality",
            decision="buffer_lifecycle_finality",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=900,
        )
    )
    assert buffered_completion.completion_mode == "buffered_lifecycle_completion"
    assert buffered_completion.decision == "buffer_lifecycle_completion"
    assert buffered_completion.queue_override_status == "scheduled"

    paused_completion = build_proactive_lifecycle_completion_decision(
        lifecycle_finality_decision=replace(
            finalized,
            status="hold",
            finality_mode="paused_lifecycle_finality",
            decision="pause_lifecycle_finality",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_completion.completion_mode == "paused_lifecycle_completion"
    assert paused_completion.decision == "pause_lifecycle_completion"
    assert paused_completion.queue_override_status == "hold"

    archived_completion = build_proactive_lifecycle_completion_decision(
        lifecycle_finality_decision=replace(
            finalized,
            status="terminal",
            finality_mode="archived_lifecycle_finality",
            decision="archive_lifecycle_finality",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_completion.completion_mode == "archived_lifecycle_completion"
    assert archived_completion.decision == "archive_lifecycle_completion"
    assert archived_completion.actionability == "archive"

    completed_conclusion = build_proactive_lifecycle_conclusion_decision(
        lifecycle_completion_decision=completed
    )
    assert completed_conclusion.conclusion_mode == "completed_lifecycle_conclusion"
    assert completed_conclusion.decision == "complete_lifecycle_conclusion"
    assert completed_conclusion.queue_override_status is None

    buffered_conclusion = build_proactive_lifecycle_conclusion_decision(
        lifecycle_completion_decision=replace(
            buffered_completion,
            status="scheduled",
            completion_mode="buffered_lifecycle_completion",
            decision="buffer_lifecycle_completion",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=1200,
        )
    )
    assert buffered_conclusion.conclusion_mode == "buffered_lifecycle_conclusion"
    assert buffered_conclusion.decision == "buffer_lifecycle_conclusion"
    assert buffered_conclusion.queue_override_status == "scheduled"

    paused_conclusion = build_proactive_lifecycle_conclusion_decision(
        lifecycle_completion_decision=replace(
            paused_completion,
            status="hold",
            completion_mode="paused_lifecycle_completion",
            decision="pause_lifecycle_completion",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_conclusion.conclusion_mode == "paused_lifecycle_conclusion"
    assert paused_conclusion.decision == "pause_lifecycle_conclusion"
    assert paused_conclusion.queue_override_status == "hold"

    archived_conclusion = build_proactive_lifecycle_conclusion_decision(
        lifecycle_completion_decision=replace(
            archived_completion,
            status="terminal",
            completion_mode="archived_lifecycle_completion",
            decision="archive_lifecycle_completion",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_conclusion.conclusion_mode == "archived_lifecycle_conclusion"
    assert archived_conclusion.decision == "archive_lifecycle_conclusion"
    assert archived_conclusion.actionability == "archive"

    completed_disposition = build_proactive_lifecycle_disposition_decision(
        lifecycle_conclusion_decision=completed_conclusion
    )
    assert completed_disposition.disposition_mode == "completed_lifecycle_disposition"
    assert completed_disposition.decision == "complete_lifecycle_disposition"
    assert completed_disposition.queue_override_status is None

    buffered_disposition = build_proactive_lifecycle_disposition_decision(
        lifecycle_conclusion_decision=replace(
            buffered_conclusion,
            status="scheduled",
            conclusion_mode="buffered_lifecycle_conclusion",
            decision="buffer_lifecycle_conclusion",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=1500,
        )
    )
    assert buffered_disposition.disposition_mode == "buffered_lifecycle_disposition"
    assert buffered_disposition.decision == "buffer_lifecycle_disposition"
    assert buffered_disposition.queue_override_status == "scheduled"

    paused_disposition = build_proactive_lifecycle_disposition_decision(
        lifecycle_conclusion_decision=replace(
            paused_conclusion,
            status="hold",
            conclusion_mode="paused_lifecycle_conclusion",
            decision="pause_lifecycle_conclusion",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_disposition.disposition_mode == "paused_lifecycle_disposition"
    assert paused_disposition.decision == "pause_lifecycle_disposition"
    assert paused_disposition.queue_override_status == "hold"

    archived_disposition = build_proactive_lifecycle_disposition_decision(
        lifecycle_conclusion_decision=replace(
            archived_conclusion,
            status="terminal",
            conclusion_mode="archived_lifecycle_conclusion",
            decision="archive_lifecycle_conclusion",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_disposition.disposition_mode == "archived_lifecycle_disposition"
    assert archived_disposition.decision == "archive_lifecycle_disposition"
    assert archived_disposition.actionability == "archive"

    completed_standing = build_proactive_lifecycle_standing_decision(
        lifecycle_disposition_decision=completed_disposition
    )
    assert completed_standing.standing_mode == "standing_lifecycle_standing"
    assert completed_standing.decision == "keep_lifecycle_standing"
    assert completed_standing.queue_override_status is None

    buffered_standing = build_proactive_lifecycle_standing_decision(
        lifecycle_disposition_decision=replace(
            buffered_disposition,
            status="scheduled",
            disposition_mode="buffered_lifecycle_disposition",
            decision="buffer_lifecycle_disposition",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=1800,
        )
    )
    assert buffered_standing.standing_mode == "buffered_lifecycle_standing"
    assert buffered_standing.decision == "buffer_lifecycle_standing"
    assert buffered_standing.queue_override_status == "scheduled"

    paused_standing = build_proactive_lifecycle_standing_decision(
        lifecycle_disposition_decision=replace(
            paused_disposition,
            status="hold",
            disposition_mode="paused_lifecycle_disposition",
            decision="pause_lifecycle_disposition",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_standing.standing_mode == "paused_lifecycle_standing"
    assert paused_standing.decision == "pause_lifecycle_standing"
    assert paused_standing.queue_override_status == "hold"

    archived_standing = build_proactive_lifecycle_standing_decision(
        lifecycle_disposition_decision=replace(
            archived_disposition,
            status="terminal",
            disposition_mode="archived_lifecycle_disposition",
            decision="archive_lifecycle_disposition",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_standing.standing_mode == "archived_lifecycle_standing"
    assert archived_standing.decision == "archive_lifecycle_standing"
    assert archived_standing.actionability == "archive"

    completed_residency = build_proactive_lifecycle_residency_decision(
        lifecycle_standing_decision=completed_standing
    )
    assert completed_residency.residency_mode == "resident_lifecycle_residency"
    assert completed_residency.decision == "keep_lifecycle_residency"
    assert completed_residency.queue_override_status is None

    buffered_residency = build_proactive_lifecycle_residency_decision(
        lifecycle_standing_decision=replace(
            buffered_standing,
            status="scheduled",
            standing_mode="buffered_lifecycle_standing",
            decision="buffer_lifecycle_standing",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=2100,
        )
    )
    assert buffered_residency.residency_mode == "buffered_lifecycle_residency"
    assert buffered_residency.decision == "buffer_lifecycle_residency"
    assert buffered_residency.queue_override_status == "scheduled"

    paused_residency = build_proactive_lifecycle_residency_decision(
        lifecycle_standing_decision=replace(
            paused_standing,
            status="hold",
            standing_mode="paused_lifecycle_standing",
            decision="pause_lifecycle_standing",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_residency.residency_mode == "paused_lifecycle_residency"
    assert paused_residency.decision == "pause_lifecycle_residency"
    assert paused_residency.queue_override_status == "hold"

    archived_residency = build_proactive_lifecycle_residency_decision(
        lifecycle_standing_decision=replace(
            archived_standing,
            status="terminal",
            standing_mode="archived_lifecycle_standing",
            decision="archive_lifecycle_standing",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_residency.residency_mode == "archived_lifecycle_residency"
    assert archived_residency.decision == "archive_lifecycle_residency"
    assert archived_residency.actionability == "archive"

    completed_tenure = build_proactive_lifecycle_tenure_decision(
        lifecycle_residency_decision=completed_residency
    )
    assert completed_tenure.tenure_mode == "tenured_lifecycle_tenure"
    assert completed_tenure.decision == "keep_lifecycle_tenure"
    assert completed_tenure.queue_override_status is None

    buffered_tenure = build_proactive_lifecycle_tenure_decision(
        lifecycle_residency_decision=replace(
            buffered_residency,
            status="scheduled",
            residency_mode="buffered_lifecycle_residency",
            decision="buffer_lifecycle_residency",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=2400,
        )
    )
    assert buffered_tenure.tenure_mode == "buffered_lifecycle_tenure"
    assert buffered_tenure.decision == "buffer_lifecycle_tenure"
    assert buffered_tenure.queue_override_status == "scheduled"

    paused_tenure = build_proactive_lifecycle_tenure_decision(
        lifecycle_residency_decision=replace(
            paused_residency,
            status="hold",
            residency_mode="paused_lifecycle_residency",
            decision="pause_lifecycle_residency",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_tenure.tenure_mode == "paused_lifecycle_tenure"
    assert paused_tenure.decision == "pause_lifecycle_tenure"
    assert paused_tenure.queue_override_status == "hold"

    archived_tenure = build_proactive_lifecycle_tenure_decision(
        lifecycle_residency_decision=replace(
            archived_residency,
            status="terminal",
            residency_mode="archived_lifecycle_residency",
            decision="archive_lifecycle_residency",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_tenure.tenure_mode == "archived_lifecycle_tenure"
    assert archived_tenure.decision == "archive_lifecycle_tenure"
    assert archived_tenure.actionability == "archive"

    completed_persistence = build_proactive_lifecycle_persistence_decision(
        lifecycle_tenure_decision=completed_tenure
    )
    assert completed_persistence.persistence_mode == "persistent_lifecycle_persistence"
    assert completed_persistence.decision == "keep_lifecycle_persistence"
    assert completed_persistence.queue_override_status is None

    buffered_persistence = build_proactive_lifecycle_persistence_decision(
        lifecycle_tenure_decision=replace(
            buffered_tenure,
            status="scheduled",
            tenure_mode="buffered_lifecycle_tenure",
            decision="buffer_lifecycle_tenure",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=2700,
        )
    )
    assert buffered_persistence.persistence_mode == "buffered_lifecycle_persistence"
    assert buffered_persistence.decision == "buffer_lifecycle_persistence"
    assert buffered_persistence.queue_override_status == "scheduled"

    paused_persistence = build_proactive_lifecycle_persistence_decision(
        lifecycle_tenure_decision=replace(
            paused_tenure,
            status="hold",
            tenure_mode="paused_lifecycle_tenure",
            decision="pause_lifecycle_tenure",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_persistence.persistence_mode == "paused_lifecycle_persistence"
    assert paused_persistence.decision == "pause_lifecycle_persistence"
    assert paused_persistence.queue_override_status == "hold"

    archived_persistence = build_proactive_lifecycle_persistence_decision(
        lifecycle_tenure_decision=replace(
            archived_tenure,
            status="terminal",
            tenure_mode="archived_lifecycle_tenure",
            decision="archive_lifecycle_tenure",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_persistence.persistence_mode == "archived_lifecycle_persistence"
    assert archived_persistence.decision == "archive_lifecycle_persistence"
    assert archived_persistence.actionability == "archive"

    completed_durability = build_proactive_lifecycle_durability_decision(
        lifecycle_persistence_decision=completed_persistence
    )
    assert completed_durability.durability_mode == "durable_lifecycle_durability"
    assert completed_durability.decision == "keep_lifecycle_durability"
    assert completed_durability.queue_override_status is None

    buffered_durability = build_proactive_lifecycle_durability_decision(
        lifecycle_persistence_decision=replace(
            buffered_persistence,
            status="scheduled",
            persistence_mode="buffered_lifecycle_persistence",
            decision="buffer_lifecycle_persistence",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=3000,
        )
    )
    assert buffered_durability.durability_mode == "buffered_lifecycle_durability"
    assert buffered_durability.decision == "buffer_lifecycle_durability"
    assert buffered_durability.queue_override_status == "scheduled"

    paused_durability = build_proactive_lifecycle_durability_decision(
        lifecycle_persistence_decision=replace(
            paused_persistence,
            status="hold",
            persistence_mode="paused_lifecycle_persistence",
            decision="pause_lifecycle_persistence",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_durability.durability_mode == "paused_lifecycle_durability"
    assert paused_durability.decision == "pause_lifecycle_durability"
    assert paused_durability.queue_override_status == "hold"

    archived_durability = build_proactive_lifecycle_durability_decision(
        lifecycle_persistence_decision=replace(
            archived_persistence,
            status="terminal",
            persistence_mode="archived_lifecycle_persistence",
            decision="archive_lifecycle_persistence",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_durability.durability_mode == "archived_lifecycle_durability"
    assert archived_durability.decision == "archive_lifecycle_durability"
    assert archived_durability.actionability == "archive"

    completed_longevity = build_proactive_lifecycle_longevity_decision(
        lifecycle_durability_decision=completed_durability
    )
    assert completed_longevity.longevity_mode == "enduring_lifecycle_longevity"
    assert completed_longevity.decision == "keep_lifecycle_longevity"
    assert completed_longevity.queue_override_status is None

    buffered_longevity = build_proactive_lifecycle_longevity_decision(
        lifecycle_durability_decision=replace(
            buffered_durability,
            status="scheduled",
            durability_mode="buffered_lifecycle_durability",
            decision="buffer_lifecycle_durability",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=3300,
        )
    )
    assert buffered_longevity.longevity_mode == "buffered_lifecycle_longevity"
    assert buffered_longevity.decision == "buffer_lifecycle_longevity"
    assert buffered_longevity.queue_override_status == "scheduled"

    paused_longevity = build_proactive_lifecycle_longevity_decision(
        lifecycle_durability_decision=replace(
            paused_durability,
            status="hold",
            durability_mode="paused_lifecycle_durability",
            decision="pause_lifecycle_durability",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_longevity.longevity_mode == "paused_lifecycle_longevity"
    assert paused_longevity.decision == "pause_lifecycle_longevity"
    assert paused_longevity.queue_override_status == "hold"

    archived_longevity = build_proactive_lifecycle_longevity_decision(
        lifecycle_durability_decision=replace(
            archived_durability,
            status="terminal",
            durability_mode="archived_lifecycle_durability",
            decision="archive_lifecycle_durability",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_longevity.longevity_mode == "archived_lifecycle_longevity"
    assert archived_longevity.decision == "archive_lifecycle_longevity"
    assert archived_longevity.actionability == "archive"

    completed_legacy = build_proactive_lifecycle_legacy_decision(
        lifecycle_longevity_decision=completed_longevity
    )
    assert completed_legacy.legacy_mode == "lasting_lifecycle_legacy"
    assert completed_legacy.decision == "keep_lifecycle_legacy"
    assert completed_legacy.queue_override_status is None

    buffered_legacy = build_proactive_lifecycle_legacy_decision(
        lifecycle_longevity_decision=replace(
            buffered_longevity,
            status="scheduled",
            longevity_mode="buffered_lifecycle_longevity",
            decision="buffer_lifecycle_longevity",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=3600,
        )
    )
    assert buffered_legacy.legacy_mode == "buffered_lifecycle_legacy"
    assert buffered_legacy.decision == "buffer_lifecycle_legacy"
    assert buffered_legacy.queue_override_status == "scheduled"

    paused_legacy = build_proactive_lifecycle_legacy_decision(
        lifecycle_longevity_decision=replace(
            paused_longevity,
            status="hold",
            longevity_mode="paused_lifecycle_longevity",
            decision="pause_lifecycle_longevity",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_legacy.legacy_mode == "paused_lifecycle_legacy"
    assert paused_legacy.decision == "pause_lifecycle_legacy"
    assert paused_legacy.queue_override_status == "hold"

    archived_legacy = build_proactive_lifecycle_legacy_decision(
        lifecycle_longevity_decision=replace(
            archived_longevity,
            status="terminal",
            longevity_mode="archived_lifecycle_longevity",
            decision="archive_lifecycle_longevity",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_legacy.legacy_mode == "archived_lifecycle_legacy"
    assert archived_legacy.decision == "archive_lifecycle_legacy"
    assert archived_legacy.actionability == "archive"

    completed_heritage = build_proactive_lifecycle_heritage_decision(
        lifecycle_legacy_decision=completed_legacy
    )
    assert completed_heritage.heritage_mode == "preserved_lifecycle_heritage"
    assert completed_heritage.decision == "keep_lifecycle_heritage"
    assert completed_heritage.queue_override_status is None

    buffered_heritage = build_proactive_lifecycle_heritage_decision(
        lifecycle_legacy_decision=replace(
            buffered_legacy,
            status="scheduled",
            legacy_mode="buffered_lifecycle_legacy",
            decision="buffer_lifecycle_legacy",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=3900,
        )
    )
    assert buffered_heritage.heritage_mode == "buffered_lifecycle_heritage"
    assert buffered_heritage.decision == "buffer_lifecycle_heritage"
    assert buffered_heritage.queue_override_status == "scheduled"

    paused_heritage = build_proactive_lifecycle_heritage_decision(
        lifecycle_legacy_decision=replace(
            paused_legacy,
            status="hold",
            legacy_mode="paused_lifecycle_legacy",
            decision="pause_lifecycle_legacy",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_heritage.heritage_mode == "paused_lifecycle_heritage"
    assert paused_heritage.decision == "pause_lifecycle_heritage"
    assert paused_heritage.queue_override_status == "hold"

    archived_heritage = build_proactive_lifecycle_heritage_decision(
        lifecycle_legacy_decision=replace(
            archived_legacy,
            status="terminal",
            legacy_mode="archived_lifecycle_legacy",
            decision="archive_lifecycle_legacy",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_heritage.heritage_mode == "archived_lifecycle_heritage"
    assert archived_heritage.decision == "archive_lifecycle_heritage"
    assert archived_heritage.actionability == "archive"

    completed_lineage = build_proactive_lifecycle_lineage_decision(
        lifecycle_heritage_decision=completed_heritage
    )
    assert completed_lineage.lineage_mode == "preserved_lifecycle_lineage"
    assert completed_lineage.decision == "keep_lifecycle_lineage"
    assert completed_lineage.queue_override_status is None

    buffered_lineage = build_proactive_lifecycle_lineage_decision(
        lifecycle_heritage_decision=replace(
            buffered_heritage,
            status="scheduled",
            heritage_mode="buffered_lifecycle_heritage",
            decision="buffer_lifecycle_heritage",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=4500,
        )
    )
    assert buffered_lineage.lineage_mode == "buffered_lifecycle_lineage"
    assert buffered_lineage.decision == "buffer_lifecycle_lineage"
    assert buffered_lineage.queue_override_status == "scheduled"

    paused_lineage = build_proactive_lifecycle_lineage_decision(
        lifecycle_heritage_decision=replace(
            paused_heritage,
            status="hold",
            heritage_mode="paused_lifecycle_heritage",
            decision="pause_lifecycle_heritage",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_lineage.lineage_mode == "paused_lifecycle_lineage"
    assert paused_lineage.decision == "pause_lifecycle_lineage"
    assert paused_lineage.queue_override_status == "hold"

    archived_lineage = build_proactive_lifecycle_lineage_decision(
        lifecycle_heritage_decision=replace(
            archived_heritage,
            status="terminal",
            heritage_mode="archived_lifecycle_heritage",
            decision="archive_lifecycle_heritage",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_lineage.lineage_mode == "archived_lifecycle_lineage"
    assert archived_lineage.decision == "archive_lifecycle_lineage"
    assert archived_lineage.actionability == "archive"

    completed_ancestry = build_proactive_lifecycle_ancestry_decision(
        lifecycle_lineage_decision=completed_lineage
    )
    assert completed_ancestry.ancestry_mode == "preserved_lifecycle_ancestry"
    assert completed_ancestry.decision == "keep_lifecycle_ancestry"
    assert completed_ancestry.queue_override_status is None

    buffered_ancestry = build_proactive_lifecycle_ancestry_decision(
        lifecycle_lineage_decision=replace(
            buffered_lineage,
            status="scheduled",
            lineage_mode="buffered_lifecycle_lineage",
            decision="buffer_lifecycle_lineage",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=5100,
        )
    )
    assert buffered_ancestry.ancestry_mode == "buffered_lifecycle_ancestry"
    assert buffered_ancestry.decision == "buffer_lifecycle_ancestry"
    assert buffered_ancestry.queue_override_status == "scheduled"

    paused_ancestry = build_proactive_lifecycle_ancestry_decision(
        lifecycle_lineage_decision=replace(
            paused_lineage,
            status="hold",
            lineage_mode="paused_lifecycle_lineage",
            decision="pause_lifecycle_lineage",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_ancestry.ancestry_mode == "paused_lifecycle_ancestry"
    assert paused_ancestry.decision == "pause_lifecycle_ancestry"
    assert paused_ancestry.queue_override_status == "hold"

    archived_ancestry = build_proactive_lifecycle_ancestry_decision(
        lifecycle_lineage_decision=replace(
            archived_lineage,
            status="terminal",
            lineage_mode="archived_lifecycle_lineage",
            decision="archive_lifecycle_lineage",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_ancestry.ancestry_mode == "archived_lifecycle_ancestry"
    assert archived_ancestry.decision == "archive_lifecycle_ancestry"
    assert archived_ancestry.actionability == "archive"

    completed_provenance = build_proactive_lifecycle_provenance_decision(
        lifecycle_ancestry_decision=completed_ancestry
    )
    assert completed_provenance.provenance_mode == "preserved_lifecycle_provenance"
    assert completed_provenance.decision == "keep_lifecycle_provenance"
    assert completed_provenance.queue_override_status is None

    buffered_provenance = build_proactive_lifecycle_provenance_decision(
        lifecycle_ancestry_decision=replace(
            buffered_ancestry,
            status="scheduled",
            ancestry_mode="buffered_lifecycle_ancestry",
            decision="buffer_lifecycle_ancestry",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=5700,
        )
    )
    assert buffered_provenance.provenance_mode == "buffered_lifecycle_provenance"
    assert buffered_provenance.decision == "buffer_lifecycle_provenance"
    assert buffered_provenance.queue_override_status == "scheduled"

    paused_provenance = build_proactive_lifecycle_provenance_decision(
        lifecycle_ancestry_decision=replace(
            paused_ancestry,
            status="hold",
            ancestry_mode="paused_lifecycle_ancestry",
            decision="pause_lifecycle_ancestry",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_provenance.provenance_mode == "paused_lifecycle_provenance"
    assert paused_provenance.decision == "pause_lifecycle_provenance"
    assert paused_provenance.queue_override_status == "hold"

    archived_provenance = build_proactive_lifecycle_provenance_decision(
        lifecycle_ancestry_decision=replace(
            archived_ancestry,
            status="terminal",
            ancestry_mode="archived_lifecycle_ancestry",
            decision="archive_lifecycle_ancestry",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_provenance.provenance_mode == "archived_lifecycle_provenance"
    assert archived_provenance.decision == "archive_lifecycle_provenance"
    assert archived_provenance.actionability == "archive"

    completed_origin = build_proactive_lifecycle_origin_decision(
        lifecycle_provenance_decision=completed_provenance
    )
    assert completed_origin.origin_mode == "preserved_lifecycle_origin"
    assert completed_origin.decision == "keep_lifecycle_origin"
    assert completed_origin.queue_override_status is None

    buffered_origin = build_proactive_lifecycle_origin_decision(
        lifecycle_provenance_decision=replace(
            buffered_provenance,
            status="scheduled",
            provenance_mode="buffered_lifecycle_provenance",
            decision="buffer_lifecycle_provenance",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=6300,
        )
    )
    assert buffered_origin.origin_mode == "buffered_lifecycle_origin"
    assert buffered_origin.decision == "buffer_lifecycle_origin"
    assert buffered_origin.queue_override_status == "scheduled"

    paused_origin = build_proactive_lifecycle_origin_decision(
        lifecycle_provenance_decision=replace(
            paused_provenance,
            status="hold",
            provenance_mode="paused_lifecycle_provenance",
            decision="pause_lifecycle_provenance",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_origin.origin_mode == "paused_lifecycle_origin"
    assert paused_origin.decision == "pause_lifecycle_origin"
    assert paused_origin.queue_override_status == "hold"

    archived_origin = build_proactive_lifecycle_origin_decision(
        lifecycle_provenance_decision=replace(
            archived_provenance,
            status="terminal",
            provenance_mode="archived_lifecycle_provenance",
            decision="archive_lifecycle_provenance",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_origin.origin_mode == "archived_lifecycle_origin"
    assert archived_origin.decision == "archive_lifecycle_origin"
    assert archived_origin.actionability == "archive"

    completed_root = build_proactive_lifecycle_root_decision(
        lifecycle_origin_decision=completed_origin
    )
    assert completed_root.root_mode == "preserved_lifecycle_root"
    assert completed_root.decision == "keep_lifecycle_root"
    assert completed_root.queue_override_status is None

    buffered_root = build_proactive_lifecycle_root_decision(
        lifecycle_origin_decision=replace(
            buffered_origin,
            status="scheduled",
            origin_mode="buffered_lifecycle_origin",
            decision="buffer_lifecycle_origin",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=6900,
        )
    )
    assert buffered_root.root_mode == "buffered_lifecycle_root"
    assert buffered_root.decision == "buffer_lifecycle_root"
    assert buffered_root.queue_override_status == "scheduled"

    paused_root = build_proactive_lifecycle_root_decision(
        lifecycle_origin_decision=replace(
            paused_origin,
            status="hold",
            origin_mode="paused_lifecycle_origin",
            decision="pause_lifecycle_origin",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_root.root_mode == "paused_lifecycle_root"
    assert paused_root.decision == "pause_lifecycle_root"
    assert paused_root.queue_override_status == "hold"

    archived_root = build_proactive_lifecycle_root_decision(
        lifecycle_origin_decision=replace(
            archived_origin,
            status="terminal",
            origin_mode="archived_lifecycle_origin",
            decision="archive_lifecycle_origin",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_root.root_mode == "archived_lifecycle_root"
    assert archived_root.decision == "archive_lifecycle_root"
    assert archived_root.actionability == "archive"

    completed_foundation = build_proactive_lifecycle_foundation_decision(
        lifecycle_root_decision=completed_root
    )
    assert completed_foundation.foundation_mode == "preserved_lifecycle_foundation"
    assert completed_foundation.decision == "keep_lifecycle_foundation"
    assert completed_foundation.queue_override_status is None

    buffered_foundation = build_proactive_lifecycle_foundation_decision(
        lifecycle_root_decision=replace(
            buffered_root,
            status="scheduled",
            root_mode="buffered_lifecycle_root",
            decision="buffer_lifecycle_root",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=7500,
        )
    )
    assert buffered_foundation.foundation_mode == "buffered_lifecycle_foundation"
    assert buffered_foundation.decision == "buffer_lifecycle_foundation"
    assert buffered_foundation.queue_override_status == "scheduled"

    paused_foundation = build_proactive_lifecycle_foundation_decision(
        lifecycle_root_decision=replace(
            paused_root,
            status="hold",
            root_mode="paused_lifecycle_root",
            decision="pause_lifecycle_root",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_foundation.foundation_mode == "paused_lifecycle_foundation"
    assert paused_foundation.decision == "pause_lifecycle_foundation"
    assert paused_foundation.queue_override_status == "hold"

    archived_foundation = build_proactive_lifecycle_foundation_decision(
        lifecycle_root_decision=replace(
            archived_root,
            status="terminal",
            root_mode="archived_lifecycle_root",
            decision="archive_lifecycle_root",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_foundation.foundation_mode == "archived_lifecycle_foundation"
    assert archived_foundation.decision == "archive_lifecycle_foundation"
    assert archived_foundation.actionability == "archive"

    completed_bedrock = build_proactive_lifecycle_bedrock_decision(
        lifecycle_foundation_decision=completed_foundation
    )
    assert completed_bedrock.bedrock_mode == "preserved_lifecycle_bedrock"
    assert completed_bedrock.decision == "keep_lifecycle_bedrock"
    assert completed_bedrock.queue_override_status is None

    buffered_bedrock = build_proactive_lifecycle_bedrock_decision(
        lifecycle_foundation_decision=replace(
            buffered_foundation,
            status="scheduled",
            foundation_mode="buffered_lifecycle_foundation",
            decision="buffer_lifecycle_foundation",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=8100,
        )
    )
    assert buffered_bedrock.bedrock_mode == "buffered_lifecycle_bedrock"
    assert buffered_bedrock.decision == "buffer_lifecycle_bedrock"
    assert buffered_bedrock.queue_override_status == "scheduled"

    paused_bedrock = build_proactive_lifecycle_bedrock_decision(
        lifecycle_foundation_decision=replace(
            paused_foundation,
            status="hold",
            foundation_mode="paused_lifecycle_foundation",
            decision="pause_lifecycle_foundation",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_bedrock.bedrock_mode == "paused_lifecycle_bedrock"
    assert paused_bedrock.decision == "pause_lifecycle_bedrock"
    assert paused_bedrock.queue_override_status == "hold"

    archived_bedrock = build_proactive_lifecycle_bedrock_decision(
        lifecycle_foundation_decision=replace(
            archived_foundation,
            status="terminal",
            foundation_mode="archived_lifecycle_foundation",
            decision="archive_lifecycle_foundation",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_bedrock.bedrock_mode == "archived_lifecycle_bedrock"
    assert archived_bedrock.decision == "archive_lifecycle_bedrock"
    assert archived_bedrock.actionability == "archive"

    completed_substrate = build_proactive_lifecycle_substrate_decision(
        lifecycle_bedrock_decision=completed_bedrock
    )
    assert completed_substrate.substrate_mode == "preserved_lifecycle_substrate"
    assert completed_substrate.decision == "keep_lifecycle_substrate"
    assert completed_substrate.queue_override_status is None

    buffered_substrate = build_proactive_lifecycle_substrate_decision(
        lifecycle_bedrock_decision=replace(
            buffered_bedrock,
            status="scheduled",
            bedrock_mode="buffered_lifecycle_bedrock",
            decision="buffer_lifecycle_bedrock",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=8700,
        )
    )
    assert buffered_substrate.substrate_mode == "buffered_lifecycle_substrate"
    assert buffered_substrate.decision == "buffer_lifecycle_substrate"
    assert buffered_substrate.queue_override_status == "scheduled"

    paused_substrate = build_proactive_lifecycle_substrate_decision(
        lifecycle_bedrock_decision=replace(
            paused_bedrock,
            status="hold",
            bedrock_mode="paused_lifecycle_bedrock",
            decision="pause_lifecycle_bedrock",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_substrate.substrate_mode == "paused_lifecycle_substrate"
    assert paused_substrate.decision == "pause_lifecycle_substrate"
    assert paused_substrate.queue_override_status == "hold"

    archived_substrate = build_proactive_lifecycle_substrate_decision(
        lifecycle_bedrock_decision=replace(
            archived_bedrock,
            status="terminal",
            bedrock_mode="archived_lifecycle_bedrock",
            decision="archive_lifecycle_bedrock",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_substrate.substrate_mode == "archived_lifecycle_substrate"
    assert archived_substrate.decision == "archive_lifecycle_substrate"
    assert archived_substrate.actionability == "archive"

    completed_stratum = build_proactive_lifecycle_stratum_decision(
        lifecycle_substrate_decision=completed_substrate
    )
    assert completed_stratum.stratum_mode == "preserved_lifecycle_stratum"
    assert completed_stratum.decision == "keep_lifecycle_stratum"
    assert completed_stratum.queue_override_status is None

    buffered_stratum = build_proactive_lifecycle_stratum_decision(
        lifecycle_substrate_decision=replace(
            buffered_substrate,
            status="scheduled",
            substrate_mode="buffered_lifecycle_substrate",
            decision="buffer_lifecycle_substrate",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=9900,
        )
    )
    assert buffered_stratum.stratum_mode == "buffered_lifecycle_stratum"
    assert buffered_stratum.decision == "buffer_lifecycle_stratum"
    assert buffered_stratum.queue_override_status == "scheduled"

    paused_stratum = build_proactive_lifecycle_stratum_decision(
        lifecycle_substrate_decision=replace(
            paused_substrate,
            status="hold",
            substrate_mode="paused_lifecycle_substrate",
            decision="pause_lifecycle_substrate",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_stratum.stratum_mode == "paused_lifecycle_stratum"
    assert paused_stratum.decision == "pause_lifecycle_stratum"
    assert paused_stratum.queue_override_status == "hold"

    archived_stratum = build_proactive_lifecycle_stratum_decision(
        lifecycle_substrate_decision=replace(
            archived_substrate,
            status="terminal",
            substrate_mode="archived_lifecycle_substrate",
            decision="archive_lifecycle_substrate",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_stratum.stratum_mode == "archived_lifecycle_stratum"
    assert archived_stratum.decision == "archive_lifecycle_stratum"
    assert archived_stratum.actionability == "archive"

    completed_layer = build_proactive_lifecycle_layer_decision(
        lifecycle_stratum_decision=completed_stratum
    )
    assert completed_layer.layer_mode == "preserved_lifecycle_layer"
    assert completed_layer.decision == "keep_lifecycle_layer"
    assert completed_layer.queue_override_status is None

    buffered_layer = build_proactive_lifecycle_layer_decision(
        lifecycle_stratum_decision=replace(
            buffered_stratum,
            status="scheduled",
            stratum_mode="buffered_lifecycle_stratum",
            decision="buffer_lifecycle_stratum",
            actionability="buffer",
            queue_override_status="scheduled",
            additional_delay_seconds=11100,
        )
    )
    assert buffered_layer.layer_mode == "buffered_lifecycle_layer"
    assert buffered_layer.decision == "buffer_lifecycle_layer"
    assert buffered_layer.queue_override_status == "scheduled"

    paused_layer = build_proactive_lifecycle_layer_decision(
        lifecycle_stratum_decision=replace(
            paused_stratum,
            status="hold",
            stratum_mode="paused_lifecycle_stratum",
            decision="pause_lifecycle_stratum",
            actionability="pause",
            active_stage_label="second_touch",
            queue_override_status="hold",
        )
    )
    assert paused_layer.layer_mode == "paused_lifecycle_layer"
    assert paused_layer.decision == "pause_lifecycle_layer"
    assert paused_layer.queue_override_status == "hold"

    archived_layer = build_proactive_lifecycle_layer_decision(
        lifecycle_stratum_decision=replace(
            archived_stratum,
            status="terminal",
            stratum_mode="archived_lifecycle_stratum",
            decision="archive_lifecycle_stratum",
            actionability="archive",
            active_stage_label=None,
            next_stage_label=None,
            queue_override_status="terminal",
            remaining_stage_count=0,
            line_exit_mode="close_loop",
        )
    )
    assert archived_layer.layer_mode == "archived_lifecycle_layer"
    assert archived_layer.decision == "archive_lifecycle_layer"
    assert archived_layer.actionability == "archive"
