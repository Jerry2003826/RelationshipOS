"""Proactive follow-up dispatch handler — extracted from RuntimeService."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from relationship_os.application.analyzers import (
    build_proactive_aggregate_controller_decision,
    build_proactive_aggregate_governance_assessment,
    build_proactive_dispatch_envelope_decision,
    build_proactive_dispatch_feedback_assessment,
    build_proactive_dispatch_gate_decision,
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
    build_proactive_line_controller_decision,
    build_proactive_line_machine_decision,
    build_proactive_line_state_decision,
    build_proactive_line_transition_decision,
    build_proactive_orchestration_controller_decision,
    build_proactive_stage_controller_decision,
    build_proactive_stage_machine_decision,
    build_proactive_stage_refresh_plan,
    build_proactive_stage_replan_assessment,
    build_proactive_stage_state_decision,
    build_proactive_stage_transition_decision,
    build_reengagement_output_units,
)
from relationship_os.application.memory_service import MemoryService
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.contracts import (
    GuidancePlan,
    ProactiveCadencePlan,
    ProactiveFollowupDirective,
    ProactiveLineControllerDecision,
    ProactiveSchedulingPlan,
    ProactiveStageControllerDecision,
    ReengagementPlan,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
    System3Snapshot,
)
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED,
    PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED,
    PROACTIVE_LIFECYCLE_ARMING_UPDATED,
    PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED,
    PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED,
    PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED,
    PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_BEDROCK_UPDATED,
    PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED,
    PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_CLOSURE_UPDATED,
    PROACTIVE_LIFECYCLE_COMPLETION_UPDATED,
    PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED,
    PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED,
    PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED,
    PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED,
    PROACTIVE_LIFECYCLE_DISPATCH_UPDATED,
    PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED,
    PROACTIVE_LIFECYCLE_DURABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED,
    PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED,
    PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED,
    PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED,
    PROACTIVE_LIFECYCLE_FINALITY_UPDATED,
    PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED,
    PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED,
    PROACTIVE_LIFECYCLE_HANDOFF_UPDATED,
    PROACTIVE_LIFECYCLE_HERITAGE_UPDATED,
    PROACTIVE_LIFECYCLE_LAUNCH_UPDATED,
    PROACTIVE_LIFECYCLE_LAYER_UPDATED,
    PROACTIVE_LIFECYCLE_LEGACY_UPDATED,
    PROACTIVE_LIFECYCLE_LINEAGE_UPDATED,
    PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED,
    PROACTIVE_LIFECYCLE_MACHINE_UPDATED,
    PROACTIVE_LIFECYCLE_ORIGIN_UPDATED,
    PROACTIVE_LIFECYCLE_OUTCOME_UPDATED,
    PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED,
    PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED,
    PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED,
    PROACTIVE_LIFECYCLE_QUEUE_UPDATED,
    PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED,
    PROACTIVE_LIFECYCLE_READINESS_UPDATED,
    PROACTIVE_LIFECYCLE_REENTRY_UPDATED,
    PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED,
    PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED,
    PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED,
    PROACTIVE_LIFECYCLE_RETENTION_UPDATED,
    PROACTIVE_LIFECYCLE_ROOT_UPDATED,
    PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED,
    PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED,
    PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED,
    PROACTIVE_LIFECYCLE_STANDING_UPDATED,
    PROACTIVE_LIFECYCLE_STATE_UPDATED,
    PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED,
    PROACTIVE_LIFECYCLE_STRATUM_UPDATED,
    PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED,
    PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED,
    PROACTIVE_LIFECYCLE_TENURE_UPDATED,
    PROACTIVE_LIFECYCLE_TRANSITION_UPDATED,
    PROACTIVE_LIFECYCLE_TRIGGER_UPDATED,
    PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED,
    PROACTIVE_LIFECYCLE_WINDOW_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_LINE_MACHINE_UPDATED,
    PROACTIVE_LINE_STATE_UPDATED,
    PROACTIVE_LINE_TRANSITION_UPDATED,
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_MACHINE_UPDATED,
    PROACTIVE_STAGE_REFRESH_UPDATED,
    PROACTIVE_STAGE_REPLAN_UPDATED,
    PROACTIVE_STAGE_STATE_UPDATED,
    PROACTIVE_STAGE_TRANSITION_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import NewEvent, StoredEvent, utc_now
from relationship_os.domain.llm import LLMClient


class ProactiveDispatchHandler:
    """Handles the proactive follow-up dispatch flow."""

    def __init__(
        self,
        *,
        stream_service: StreamService,
        memory_service: MemoryService,
        llm_client: LLMClient,
        llm_model: str,
        llm_temperature: float,
    ) -> None:
        self._stream_service = stream_service
        self._memory_service = memory_service
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._llm_temperature = llm_temperature

    async def dispatch(
        self,
        *,
        session_id: str,
        source: str,
        queue_item: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prior_events = await self._stream_service.read_stream(stream_id=session_id)
        if not prior_events:
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "session_not_found",
            }

        runtime_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
        )
        runtime_state = dict(runtime_projection["state"])
        archive_status = dict(runtime_state.get("archive_status") or {})
        if archive_status.get("archived"):
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "session_archived",
            }

        directive = dict(runtime_state.get("proactive_followup_directive") or {})
        if not directive:
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "missing_directive",
            }
        if directive.get("status") != "ready" or not bool(directive.get("eligible")):
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "directive_not_ready",
            }
        if queue_item is not None and queue_item.get("queue_status") not in {"due", "overdue"}:
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "queue_not_actionable",
            }

        latest_proactive_event = self._latest_event(
            prior_events,
            event_type=PROACTIVE_FOLLOWUP_UPDATED,
        )
        recent_user_text = str(
            next(
                (
                    event.payload.get("content", "")
                    for event in reversed(prior_events)
                    if event.event_type == USER_MESSAGE_RECEIVED
                ),
                "",
            )
        )
        runtime_coordination_snapshot = dict(
            runtime_state.get("runtime_coordination_snapshot") or {}
        )
        conversation_cadence_plan = dict(
            runtime_state.get("conversation_cadence_plan") or {}
        )
        session_ritual_plan = dict(runtime_state.get("session_ritual_plan") or {})
        proactive_cadence_plan = dict(runtime_state.get("proactive_cadence_plan") or {})
        proactive_scheduling_plan = dict(
            runtime_state.get("proactive_scheduling_plan") or {}
        )
        proactive_guardrail_plan = dict(runtime_state.get("proactive_guardrail_plan") or {})
        proactive_orchestration_plan = dict(
            runtime_state.get("proactive_orchestration_plan") or {}
        )
        proactive_actuation_plan = dict(runtime_state.get("proactive_actuation_plan") or {})
        proactive_progression_plan = dict(
            runtime_state.get("proactive_progression_plan") or {}
        )
        directive_model = ProactiveFollowupDirective(
            eligible=bool(directive.get("eligible")),
            status=str(directive.get("status") or "hold"),
            style=str(directive.get("style") or "none"),
            trigger_after_seconds=int(directive.get("trigger_after_seconds") or 0),
            window_seconds=int(directive.get("window_seconds") or 0),
            rationale=str(directive.get("rationale") or ""),
            opening_hint=str(directive.get("opening_hint") or ""),
            trigger_conditions=[
                str(item) for item in list(directive.get("trigger_conditions") or [])
            ],
            hold_reasons=[str(item) for item in list(directive.get("hold_reasons") or [])],
        )
        runtime_coordination_model = (
            RuntimeCoordinationSnapshot(
                triggered_turn_index=int(
                    runtime_coordination_snapshot.get("triggered_turn_index") or 0
                ),
                time_awareness_mode=str(
                    runtime_coordination_snapshot.get("time_awareness_mode") or "ongoing"
                ),
                idle_gap_seconds=float(
                    runtime_coordination_snapshot.get("idle_gap_seconds") or 0.0
                ),
                session_age_seconds=float(
                    runtime_coordination_snapshot.get("session_age_seconds") or 0.0
                ),
                ritual_phase=str(
                    runtime_coordination_snapshot.get("ritual_phase")
                    or "steady_progress"
                ),
                cognitive_load_band=str(
                    runtime_coordination_snapshot.get("cognitive_load_band") or "low"
                ),
                response_budget_mode=str(
                    runtime_coordination_snapshot.get("response_budget_mode")
                    or "structured"
                ),
                proactive_followup_eligible=bool(
                    runtime_coordination_snapshot.get("proactive_followup_eligible")
                ),
                proactive_style=str(
                    runtime_coordination_snapshot.get("proactive_style") or "none"
                ),
                somatic_cue=runtime_coordination_snapshot.get("somatic_cue"),
                coordination_notes=[
                    str(item)
                    for item in list(
                        runtime_coordination_snapshot.get("coordination_notes") or []
                    )
                ],
            )
            if runtime_coordination_snapshot
            else None
        )
        session_ritual_plan_model = SessionRitualPlan(
            phase=str(
                session_ritual_plan.get("phase")
                or runtime_coordination_snapshot.get("ritual_phase")
                or "steady_progress"
            ),
            opening_move=str(session_ritual_plan.get("opening_move") or "soft_open"),
            bridge_move=str(session_ritual_plan.get("bridge_move") or "micro_step_bridge"),
            closing_move=str(session_ritual_plan.get("closing_move") or "light_handoff"),
            continuity_anchor=str(
                session_ritual_plan.get("continuity_anchor") or "smallest_next_step"
            ),
            somatic_shortcut=str(
                session_ritual_plan.get("somatic_shortcut") or "none"
            ),
            micro_rituals=[
                str(item) for item in list(session_ritual_plan.get("micro_rituals") or [])
            ],
            rationale=str(session_ritual_plan.get("rationale") or ""),
        )
        somatic_orchestration_plan = dict(
            runtime_state.get("somatic_orchestration_plan") or {}
        )
        somatic_orchestration_plan_model = SomaticOrchestrationPlan(
            status=str(somatic_orchestration_plan.get("status") or "not_needed"),
            cue=str(somatic_orchestration_plan.get("cue") or "none"),
            primary_mode=str(
                somatic_orchestration_plan.get("primary_mode") or "none"
            ),
            body_anchor=str(somatic_orchestration_plan.get("body_anchor") or "none"),
            followup_style=str(
                somatic_orchestration_plan.get("followup_style") or "none"
            ),
            allow_in_followup=bool(
                somatic_orchestration_plan.get("allow_in_followup")
            ),
            micro_actions=[
                str(item)
                for item in list(
                    somatic_orchestration_plan.get("micro_actions") or []
                )
            ],
            phrasing_guardrails=[
                str(item)
                for item in list(
                    somatic_orchestration_plan.get("phrasing_guardrails") or []
                )
            ],
            rationale=str(somatic_orchestration_plan.get("rationale") or ""),
        )
        proactive_cadence_plan_model = ProactiveCadencePlan(
            status=str(proactive_cadence_plan.get("status") or "hold"),
            cadence_key=str(proactive_cadence_plan.get("cadence_key") or "hold"),
            stage_labels=[
                str(item)
                for item in list(proactive_cadence_plan.get("stage_labels") or [])
            ],
            stage_intervals_seconds=[
                max(0, int(item))
                for item in list(
                    proactive_cadence_plan.get("stage_intervals_seconds") or []
                )
            ],
            window_seconds=max(0, int(proactive_cadence_plan.get("window_seconds") or 0)),
            close_after_stage_index=max(
                0,
                int(proactive_cadence_plan.get("close_after_stage_index") or 0),
            ),
            rationale=str(proactive_cadence_plan.get("rationale") or directive_model.rationale),
        )
        reengagement_plan = dict(runtime_state.get("reengagement_plan") or {})
        reengagement_plan_model = ReengagementPlan(
            status=str(reengagement_plan.get("status") or directive_model.status),
            ritual_mode=str(reengagement_plan.get("ritual_mode") or "continuity_nudge"),
            delivery_mode=str(
                reengagement_plan.get("delivery_mode") or "single_message"
            ),
            strategy_key=str(reengagement_plan.get("strategy_key") or "none"),
            relational_move=str(reengagement_plan.get("relational_move") or "none"),
            pressure_mode=str(reengagement_plan.get("pressure_mode") or "none"),
            autonomy_signal=str(reengagement_plan.get("autonomy_signal") or "none"),
            sequence_objective=str(
                reengagement_plan.get("sequence_objective") or ""
            ),
            somatic_action=(
                str(reengagement_plan.get("somatic_action"))
                if reengagement_plan.get("somatic_action") is not None
                else None
            ),
            segment_labels=[
                str(item) for item in list(reengagement_plan.get("segment_labels") or [])
            ],
            focus_points=[
                str(item) for item in list(reengagement_plan.get("focus_points") or [])
            ],
            tone=str(reengagement_plan.get("tone") or "gentle"),
            opening_hint=str(reengagement_plan.get("opening_hint") or ""),
            closing_hint=str(reengagement_plan.get("closing_hint") or ""),
            rationale=str(reengagement_plan.get("rationale") or directive_model.rationale),
        )
        proactive_scheduling_plan_model = ProactiveSchedulingPlan(
            status=str(proactive_scheduling_plan.get("status") or "hold"),
            scheduler_mode=str(
                proactive_scheduling_plan.get("scheduler_mode") or "hold"
            ),
            min_seconds_since_last_outbound=max(
                0,
                int(
                    proactive_scheduling_plan.get(
                        "min_seconds_since_last_outbound"
                    )
                    or 0
                ),
            ),
            first_touch_extra_delay_seconds=max(
                0,
                int(
                    proactive_scheduling_plan.get(
                        "first_touch_extra_delay_seconds"
                    )
                    or 0
                ),
            ),
            stage_spacing_mode=str(
                proactive_scheduling_plan.get("stage_spacing_mode") or "standard"
            ),
            low_pressure_guard=str(
                proactive_scheduling_plan.get("low_pressure_guard") or "none"
            ),
            scheduling_notes=[
                str(item)
                for item in list(
                    proactive_scheduling_plan.get("scheduling_notes") or []
                )
            ],
            rationale=str(
                proactive_scheduling_plan.get("rationale") or directive_model.rationale
            ),
        )
        guidance_plan_state = dict(runtime_state.get("guidance_plan") or {})
        guidance_plan_model = GuidancePlan(
            mode=str(guidance_plan_state.get("mode") or "progress_guidance"),
            lead_with=str(guidance_plan_state.get("lead_with") or "steady_next_step"),
            pacing=str(guidance_plan_state.get("pacing") or "steady"),
            step_budget=max(1, int(guidance_plan_state.get("step_budget") or 1)),
            agency_mode=str(
                guidance_plan_state.get("agency_mode") or "light_reentry"
            ),
            ritual_action=str(guidance_plan_state.get("ritual_action") or ""),
            checkpoint_style=str(
                guidance_plan_state.get("checkpoint_style") or ""
            ),
            handoff_mode=str(guidance_plan_state.get("handoff_mode") or ""),
            carryover_mode=str(guidance_plan_state.get("carryover_mode") or ""),
            micro_actions=[
                str(item)
                for item in list(guidance_plan_state.get("micro_actions") or [])
            ],
            rationale=str(guidance_plan_state.get("rationale") or directive_model.rationale),
        )
        system3_snapshot_state = dict(runtime_state.get("system3_snapshot") or {})
        system3_snapshot_model = System3Snapshot(
            triggered_turn_index=max(
                0,
                int(system3_snapshot_state.get("triggered_turn_index") or 0),
            ),
            identity_anchor=str(system3_snapshot_state.get("identity_anchor") or ""),
            identity_consistency=str(
                system3_snapshot_state.get("identity_consistency") or "stable"
            ),
            identity_confidence=float(
                system3_snapshot_state.get("identity_confidence") or 0.0
            ),
            identity_trajectory_status=str(
                system3_snapshot_state.get("identity_trajectory_status") or "stable"
            ),
            identity_trajectory_target=str(
                system3_snapshot_state.get("identity_trajectory_target")
                or system3_snapshot_state.get("identity_anchor")
                or ""
            ),
            identity_trajectory_trigger=str(
                system3_snapshot_state.get("identity_trajectory_trigger")
                or "identity_consistent"
            ),
            identity_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("identity_trajectory_notes") or []
                )
            ],
            growth_stage=str(system3_snapshot_state.get("growth_stage") or "forming"),
            growth_signal=str(system3_snapshot_state.get("growth_signal") or ""),
            user_model_confidence=float(
                system3_snapshot_state.get("user_model_confidence") or 0.0
            ),
            user_needs=[
                str(item)
                for item in list(system3_snapshot_state.get("user_needs") or [])
            ],
            user_preferences=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("user_preferences") or []
                )
            ],
            emotional_debt_status=str(
                system3_snapshot_state.get("emotional_debt_status") or "low"
            ),
            emotional_debt_score=float(
                system3_snapshot_state.get("emotional_debt_score") or 0.0
            ),
            debt_signals=[
                str(item)
                for item in list(system3_snapshot_state.get("debt_signals") or [])
            ],
            emotional_debt_trajectory_status=str(
                system3_snapshot_state.get("emotional_debt_trajectory_status")
                or "stable"
            ),
            emotional_debt_trajectory_target=str(
                system3_snapshot_state.get("emotional_debt_trajectory_target")
                or "steady_low_debt"
            ),
            emotional_debt_trajectory_trigger=str(
                system3_snapshot_state.get("emotional_debt_trajectory_trigger")
                or "debt_stable"
            ),
            emotional_debt_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("emotional_debt_trajectory_notes")
                    or []
                )
            ],
            strategy_audit_status=str(
                system3_snapshot_state.get("strategy_audit_status") or "pass"
            ),
            strategy_fit=str(system3_snapshot_state.get("strategy_fit") or "aligned"),
            strategy_audit_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("strategy_audit_notes") or []
                )
            ],
            strategy_audit_trajectory_status=str(
                system3_snapshot_state.get("strategy_audit_trajectory_status")
                or "stable"
            ),
            strategy_audit_trajectory_target=str(
                system3_snapshot_state.get("strategy_audit_trajectory_target")
                or "aligned_strategy_path"
            ),
            strategy_audit_trajectory_trigger=str(
                system3_snapshot_state.get("strategy_audit_trajectory_trigger")
                or "strategy_line_stable"
            ),
            strategy_audit_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("strategy_audit_trajectory_notes") or []
                )
            ],
            strategy_supervision_status=str(
                system3_snapshot_state.get("strategy_supervision_status") or "pass"
            ),
            strategy_supervision_mode=str(
                system3_snapshot_state.get("strategy_supervision_mode")
                or "steady_supervision"
            ),
            strategy_supervision_trigger=str(
                system3_snapshot_state.get("strategy_supervision_trigger")
                or "strategy_stable"
            ),
            strategy_supervision_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("strategy_supervision_notes") or []
                )
            ],
            strategy_supervision_trajectory_status=str(
                system3_snapshot_state.get("strategy_supervision_trajectory_status")
                or "stable"
            ),
            strategy_supervision_trajectory_target=str(
                system3_snapshot_state.get("strategy_supervision_trajectory_target")
                or "steady_supervision"
            ),
            strategy_supervision_trajectory_trigger=str(
                system3_snapshot_state.get("strategy_supervision_trajectory_trigger")
                or "strategy_supervision_stable"
            ),
            strategy_supervision_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "strategy_supervision_trajectory_notes"
                    )
                    or []
                )
            ],
            moral_reasoning_status=str(
                system3_snapshot_state.get("moral_reasoning_status") or "pass"
            ),
            moral_posture=str(
                system3_snapshot_state.get("moral_posture") or "steady_progress_care"
            ),
            moral_conflict=str(
                system3_snapshot_state.get("moral_conflict") or "none"
            ),
            moral_principles=[
                str(item)
                for item in list(system3_snapshot_state.get("moral_principles") or [])
            ],
            moral_notes=[
                str(item)
                for item in list(system3_snapshot_state.get("moral_notes") or [])
            ],
            moral_trajectory_status=str(
                system3_snapshot_state.get("moral_trajectory_status") or "stable"
            ),
            moral_trajectory_target=str(
                system3_snapshot_state.get("moral_trajectory_target")
                or "steady_progress_care"
            ),
            moral_trajectory_trigger=str(
                system3_snapshot_state.get("moral_trajectory_trigger")
                or "moral_line_stable"
            ),
            moral_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("moral_trajectory_notes") or []
                )
            ],
            user_model_evolution_status=str(
                system3_snapshot_state.get("user_model_evolution_status") or "pass"
            ),
            user_model_revision_mode=str(
                system3_snapshot_state.get("user_model_revision_mode")
                or "steady_refinement"
            ),
            user_model_shift_signal=str(
                system3_snapshot_state.get("user_model_shift_signal") or "stable"
            ),
            user_model_evolution_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("user_model_evolution_notes") or []
                )
            ],
            user_model_trajectory_status=str(
                system3_snapshot_state.get("user_model_trajectory_status")
                or "stable"
            ),
            user_model_trajectory_target=str(
                system3_snapshot_state.get("user_model_trajectory_target")
                or "steady_refinement"
            ),
            user_model_trajectory_trigger=str(
                system3_snapshot_state.get("user_model_trajectory_trigger")
                or "model_stable"
            ),
            user_model_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("user_model_trajectory_notes") or []
                )
            ],
            expectation_calibration_status=str(
                system3_snapshot_state.get("expectation_calibration_status")
                or "pass"
            ),
            expectation_calibration_target=str(
                system3_snapshot_state.get("expectation_calibration_target")
                or "bounded_progress_expectation"
            ),
            expectation_calibration_trigger=str(
                system3_snapshot_state.get("expectation_calibration_trigger")
                or "expectation_line_stable"
            ),
            expectation_calibration_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("expectation_calibration_notes") or []
                )
            ],
            expectation_calibration_trajectory_status=str(
                system3_snapshot_state.get(
                    "expectation_calibration_trajectory_status"
                )
                or "stable"
            ),
            expectation_calibration_trajectory_target=str(
                system3_snapshot_state.get(
                    "expectation_calibration_trajectory_target"
                )
                or "bounded_progress_expectation"
            ),
            expectation_calibration_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "expectation_calibration_trajectory_trigger"
                )
                or "expectation_line_stable"
            ),
            expectation_calibration_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "expectation_calibration_trajectory_notes"
                    )
                    or []
                )
            ],
            dependency_governance_status=str(
                system3_snapshot_state.get("dependency_governance_status") or "pass"
            ),
            dependency_governance_target=str(
                system3_snapshot_state.get("dependency_governance_target")
                or "steady_low_dependency_support"
            ),
            dependency_governance_trigger=str(
                system3_snapshot_state.get("dependency_governance_trigger")
                or "dependency_line_stable"
            ),
            dependency_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("dependency_governance_notes") or []
                )
            ],
            dependency_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "dependency_governance_trajectory_status"
                )
                or "stable"
            ),
            dependency_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "dependency_governance_trajectory_target"
                )
                or "steady_low_dependency_support"
            ),
            dependency_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "dependency_governance_trajectory_trigger"
                )
                or "dependency_governance_stable"
            ),
            dependency_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "dependency_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            autonomy_governance_status=str(
                system3_snapshot_state.get("autonomy_governance_status") or "pass"
            ),
            autonomy_governance_target=str(
                system3_snapshot_state.get("autonomy_governance_target")
                or "steady_explicit_autonomy"
            ),
            autonomy_governance_trigger=str(
                system3_snapshot_state.get("autonomy_governance_trigger")
                or "autonomy_line_stable"
            ),
            autonomy_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("autonomy_governance_notes") or []
                )
            ],
            autonomy_governance_trajectory_status=str(
                system3_snapshot_state.get("autonomy_governance_trajectory_status")
                or "stable"
            ),
            autonomy_governance_trajectory_target=str(
                system3_snapshot_state.get("autonomy_governance_trajectory_target")
                or "steady_explicit_autonomy"
            ),
            autonomy_governance_trajectory_trigger=str(
                system3_snapshot_state.get("autonomy_governance_trajectory_trigger")
                or "autonomy_governance_stable"
            ),
            autonomy_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "autonomy_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            boundary_governance_status=str(
                system3_snapshot_state.get("boundary_governance_status") or "pass"
            ),
            boundary_governance_target=str(
                system3_snapshot_state.get("boundary_governance_target")
                or "steady_clear_boundary_support"
            ),
            boundary_governance_trigger=str(
                system3_snapshot_state.get("boundary_governance_trigger")
                or "boundary_line_stable"
            ),
            boundary_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("boundary_governance_notes") or []
                )
            ],
            boundary_governance_trajectory_status=str(
                system3_snapshot_state.get("boundary_governance_trajectory_status")
                or "stable"
            ),
            boundary_governance_trajectory_target=str(
                system3_snapshot_state.get("boundary_governance_trajectory_target")
                or "steady_clear_boundary_support"
            ),
            boundary_governance_trajectory_trigger=str(
                system3_snapshot_state.get("boundary_governance_trajectory_trigger")
                or "boundary_governance_stable"
            ),
            boundary_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "boundary_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            support_governance_status=str(
                system3_snapshot_state.get("support_governance_status") or "pass"
            ),
            support_governance_target=str(
                system3_snapshot_state.get("support_governance_target")
                or "steady_bounded_support"
            ),
            support_governance_trigger=str(
                system3_snapshot_state.get("support_governance_trigger")
                or "support_line_stable"
            ),
            support_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("support_governance_notes") or []
                )
            ],
            support_governance_trajectory_status=str(
                system3_snapshot_state.get("support_governance_trajectory_status")
                or "stable"
            ),
            support_governance_trajectory_target=str(
                system3_snapshot_state.get("support_governance_trajectory_target")
                or "steady_bounded_support"
            ),
            support_governance_trajectory_trigger=str(
                system3_snapshot_state.get("support_governance_trajectory_trigger")
                or "support_governance_stable"
            ),
            support_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "support_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            continuity_governance_status=str(
                system3_snapshot_state.get("continuity_governance_status")
                or "pass"
            ),
            continuity_governance_target=str(
                system3_snapshot_state.get("continuity_governance_target")
                or "steady_contextual_continuity"
            ),
            continuity_governance_trigger=str(
                system3_snapshot_state.get("continuity_governance_trigger")
                or "continuity_line_stable"
            ),
            continuity_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("continuity_governance_notes") or []
                )
            ],
            continuity_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "continuity_governance_trajectory_status"
                )
                or "stable"
            ),
            continuity_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "continuity_governance_trajectory_target"
                )
                or "steady_contextual_continuity"
            ),
            continuity_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "continuity_governance_trajectory_trigger"
                )
                or "continuity_governance_stable"
            ),
            continuity_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "continuity_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            repair_governance_status=str(
                system3_snapshot_state.get("repair_governance_status") or "pass"
            ),
            repair_governance_target=str(
                system3_snapshot_state.get("repair_governance_target")
                or "steady_relational_repair_posture"
            ),
            repair_governance_trigger=str(
                system3_snapshot_state.get("repair_governance_trigger")
                or "repair_line_stable"
            ),
            repair_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("repair_governance_notes") or []
                )
            ],
            repair_governance_trajectory_status=str(
                system3_snapshot_state.get("repair_governance_trajectory_status")
                or "stable"
            ),
            repair_governance_trajectory_target=str(
                system3_snapshot_state.get("repair_governance_trajectory_target")
                or "steady_relational_repair_posture"
            ),
            repair_governance_trajectory_trigger=str(
                system3_snapshot_state.get("repair_governance_trajectory_trigger")
                or "repair_governance_stable"
            ),
            repair_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "repair_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            attunement_governance_status=str(
                system3_snapshot_state.get("attunement_governance_status") or "pass"
            ),
            attunement_governance_target=str(
                system3_snapshot_state.get("attunement_governance_target")
                or "steady_relational_attunement"
            ),
            attunement_governance_trigger=str(
                system3_snapshot_state.get("attunement_governance_trigger")
                or "attunement_line_stable"
            ),
            attunement_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("attunement_governance_notes")
                    or []
                )
            ],
            attunement_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "attunement_governance_trajectory_status"
                )
                or "stable"
            ),
            attunement_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "attunement_governance_trajectory_target"
                )
                or "steady_relational_attunement"
            ),
            attunement_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "attunement_governance_trajectory_trigger"
                )
                or "attunement_governance_stable"
            ),
            attunement_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "attunement_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            trust_governance_status=str(
                system3_snapshot_state.get("trust_governance_status") or "pass"
            ),
            trust_governance_target=str(
                system3_snapshot_state.get("trust_governance_target")
                or "steady_mutual_trust_posture"
            ),
            trust_governance_trigger=str(
                system3_snapshot_state.get("trust_governance_trigger")
                or "trust_line_stable"
            ),
            trust_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("trust_governance_notes") or []
                )
            ],
            trust_governance_trajectory_status=str(
                system3_snapshot_state.get("trust_governance_trajectory_status")
                or "stable"
            ),
            trust_governance_trajectory_target=str(
                system3_snapshot_state.get("trust_governance_trajectory_target")
                or "steady_mutual_trust_posture"
            ),
            trust_governance_trajectory_trigger=str(
                system3_snapshot_state.get("trust_governance_trajectory_trigger")
                or "trust_governance_stable"
            ),
            trust_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "trust_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            clarity_governance_status=str(
                system3_snapshot_state.get("clarity_governance_status") or "pass"
            ),
            clarity_governance_target=str(
                system3_snapshot_state.get("clarity_governance_target")
                or "steady_contextual_clarity"
            ),
            clarity_governance_trigger=str(
                system3_snapshot_state.get("clarity_governance_trigger")
                or "clarity_line_stable"
            ),
            clarity_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("clarity_governance_notes") or []
                )
            ],
            clarity_governance_trajectory_status=str(
                system3_snapshot_state.get("clarity_governance_trajectory_status")
                or "stable"
            ),
            clarity_governance_trajectory_target=str(
                system3_snapshot_state.get("clarity_governance_trajectory_target")
                or "steady_contextual_clarity"
            ),
            clarity_governance_trajectory_trigger=str(
                system3_snapshot_state.get("clarity_governance_trajectory_trigger")
                or "clarity_governance_stable"
            ),
            clarity_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "clarity_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            pacing_governance_status=str(
                system3_snapshot_state.get("pacing_governance_status") or "pass"
            ),
            pacing_governance_target=str(
                system3_snapshot_state.get("pacing_governance_target")
                or "steady_relational_pacing"
            ),
            pacing_governance_trigger=str(
                system3_snapshot_state.get("pacing_governance_trigger")
                or "pacing_line_stable"
            ),
            pacing_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("pacing_governance_notes") or []
                )
            ],
            pacing_governance_trajectory_status=str(
                system3_snapshot_state.get("pacing_governance_trajectory_status")
                or "stable"
            ),
            pacing_governance_trajectory_target=str(
                system3_snapshot_state.get("pacing_governance_trajectory_target")
                or "steady_relational_pacing"
            ),
            pacing_governance_trajectory_trigger=str(
                system3_snapshot_state.get("pacing_governance_trajectory_trigger")
                or "pacing_governance_stable"
            ),
            pacing_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "pacing_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            commitment_governance_status=str(
                system3_snapshot_state.get("commitment_governance_status") or "pass"
            ),
            commitment_governance_target=str(
                system3_snapshot_state.get("commitment_governance_target")
                or "steady_calibrated_commitment"
            ),
            commitment_governance_trigger=str(
                system3_snapshot_state.get("commitment_governance_trigger")
                or "commitment_line_stable"
            ),
            commitment_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("commitment_governance_notes") or []
                )
            ],
            commitment_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "commitment_governance_trajectory_status"
                )
                or "stable"
            ),
            commitment_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "commitment_governance_trajectory_target"
                )
                or "steady_calibrated_commitment"
            ),
            commitment_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "commitment_governance_trajectory_trigger"
                )
                or "commitment_governance_stable"
            ),
            commitment_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "commitment_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            disclosure_governance_status=str(
                system3_snapshot_state.get("disclosure_governance_status") or "pass"
            ),
            disclosure_governance_target=str(
                system3_snapshot_state.get("disclosure_governance_target")
                or "steady_transparent_disclosure"
            ),
            disclosure_governance_trigger=str(
                system3_snapshot_state.get("disclosure_governance_trigger")
                or "disclosure_line_stable"
            ),
            disclosure_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("disclosure_governance_notes") or []
                )
            ],
            disclosure_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "disclosure_governance_trajectory_status"
                )
                or "stable"
            ),
            disclosure_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "disclosure_governance_trajectory_target"
                )
                or "steady_transparent_disclosure"
            ),
            disclosure_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "disclosure_governance_trajectory_trigger"
                )
                or "disclosure_governance_stable"
            ),
            disclosure_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "disclosure_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            reciprocity_governance_status=str(
                system3_snapshot_state.get("reciprocity_governance_status")
                or "pass"
            ),
            reciprocity_governance_target=str(
                system3_snapshot_state.get("reciprocity_governance_target")
                or "steady_mutual_reciprocity"
            ),
            reciprocity_governance_trigger=str(
                system3_snapshot_state.get("reciprocity_governance_trigger")
                or "reciprocity_line_stable"
            ),
            reciprocity_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("reciprocity_governance_notes")
                    or []
                )
            ],
            reciprocity_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "reciprocity_governance_trajectory_status"
                )
                or "stable"
            ),
            reciprocity_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "reciprocity_governance_trajectory_target"
                )
                or "steady_mutual_reciprocity"
            ),
            reciprocity_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "reciprocity_governance_trajectory_trigger"
                )
                or "reciprocity_governance_stable"
            ),
            reciprocity_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "reciprocity_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            pressure_governance_status=str(
                system3_snapshot_state.get("pressure_governance_status") or "pass"
            ),
            pressure_governance_target=str(
                system3_snapshot_state.get("pressure_governance_target")
                or "steady_low_pressure_support"
            ),
            pressure_governance_trigger=str(
                system3_snapshot_state.get("pressure_governance_trigger")
                or "pressure_line_stable"
            ),
            pressure_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("pressure_governance_notes") or []
                )
            ],
            pressure_governance_trajectory_status=str(
                system3_snapshot_state.get("pressure_governance_trajectory_status")
                or "stable"
            ),
            pressure_governance_trajectory_target=str(
                system3_snapshot_state.get("pressure_governance_trajectory_target")
                or "steady_low_pressure_support"
            ),
            pressure_governance_trajectory_trigger=str(
                system3_snapshot_state.get("pressure_governance_trajectory_trigger")
                or "pressure_governance_stable"
            ),
            pressure_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "pressure_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            relational_governance_status=str(
                system3_snapshot_state.get("relational_governance_status")
                or "pass"
            ),
            relational_governance_target=str(
                system3_snapshot_state.get("relational_governance_target")
                or "steady_bounded_relational_progress"
            ),
            relational_governance_trigger=str(
                system3_snapshot_state.get("relational_governance_trigger")
                or "relational_line_stable"
            ),
            relational_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("relational_governance_notes")
                    or []
                )
            ],
            relational_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "relational_governance_trajectory_status"
                )
                or "stable"
            ),
            relational_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "relational_governance_trajectory_target"
                )
                or "steady_bounded_relational_progress"
            ),
            relational_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "relational_governance_trajectory_trigger"
                )
                or "relational_governance_stable"
            ),
            relational_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "relational_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            safety_governance_status=str(
                system3_snapshot_state.get("safety_governance_status") or "pass"
            ),
            safety_governance_target=str(
                system3_snapshot_state.get("safety_governance_target")
                or "steady_safe_relational_support"
            ),
            safety_governance_trigger=str(
                system3_snapshot_state.get("safety_governance_trigger")
                or "safety_line_stable"
            ),
            safety_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("safety_governance_notes") or []
                )
            ],
            safety_governance_trajectory_status=str(
                system3_snapshot_state.get("safety_governance_trajectory_status")
                or "stable"
            ),
            safety_governance_trajectory_target=str(
                system3_snapshot_state.get("safety_governance_trajectory_target")
                or "steady_safe_relational_support"
            ),
            safety_governance_trajectory_trigger=str(
                system3_snapshot_state.get("safety_governance_trajectory_trigger")
                or "safety_governance_stable"
            ),
            safety_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "safety_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            progress_governance_status=str(
                system3_snapshot_state.get("progress_governance_status") or "pass"
            ),
            progress_governance_target=str(
                system3_snapshot_state.get("progress_governance_target")
                or "steady_bounded_progress"
            ),
            progress_governance_trigger=str(
                system3_snapshot_state.get("progress_governance_trigger")
                or "progress_line_stable"
            ),
            progress_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("progress_governance_notes") or []
                )
            ],
            progress_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "progress_governance_trajectory_status"
                )
                or "stable"
            ),
            progress_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "progress_governance_trajectory_target"
                )
                or "steady_bounded_progress"
            ),
            progress_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "progress_governance_trajectory_trigger"
                )
                or "progress_governance_stable"
            ),
            progress_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "progress_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            stability_governance_status=str(
                system3_snapshot_state.get("stability_governance_status")
                or "pass"
            ),
            stability_governance_target=str(
                system3_snapshot_state.get("stability_governance_target")
                or "steady_bounded_relational_stability"
            ),
            stability_governance_trigger=str(
                system3_snapshot_state.get("stability_governance_trigger")
                or "stability_line_stable"
            ),
            stability_governance_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("stability_governance_notes")
                    or []
                )
            ],
            stability_governance_trajectory_status=str(
                system3_snapshot_state.get(
                    "stability_governance_trajectory_status"
                )
                or "stable"
            ),
            stability_governance_trajectory_target=str(
                system3_snapshot_state.get(
                    "stability_governance_trajectory_target"
                )
                or "steady_bounded_relational_stability"
            ),
            stability_governance_trajectory_trigger=str(
                system3_snapshot_state.get(
                    "stability_governance_trajectory_trigger"
                )
                or "stability_governance_stable"
            ),
            stability_governance_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get(
                        "stability_governance_trajectory_notes"
                    )
                    or []
                )
            ],
            growth_transition_status=str(
                system3_snapshot_state.get("growth_transition_status") or "stable"
            ),
            growth_transition_target=str(
                system3_snapshot_state.get("growth_transition_target") or "steadying"
            ),
            growth_transition_trigger=str(
                system3_snapshot_state.get("growth_transition_trigger")
                or "maintain_current_stage"
            ),
            growth_transition_readiness=float(
                system3_snapshot_state.get("growth_transition_readiness") or 0.0
            ),
            growth_transition_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("growth_transition_notes") or []
                )
            ],
            growth_transition_trajectory_status=str(
                system3_snapshot_state.get("growth_transition_trajectory_status")
                or "stable"
            ),
            growth_transition_trajectory_target=str(
                system3_snapshot_state.get("growth_transition_trajectory_target")
                or "steadying"
            ),
            growth_transition_trajectory_trigger=str(
                system3_snapshot_state.get("growth_transition_trajectory_trigger")
                or "growth_line_stable"
            ),
            growth_transition_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("growth_transition_trajectory_notes")
                    or []
                )
            ],
            version_migration_status=str(
                system3_snapshot_state.get("version_migration_status") or "pass"
            ),
            version_migration_scope=str(
                system3_snapshot_state.get("version_migration_scope")
                or "stable_rebuild_ready"
            ),
            version_migration_trigger=str(
                system3_snapshot_state.get("version_migration_trigger")
                or "projection_rebuild_ready"
            ),
            version_migration_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("version_migration_notes") or []
                )
            ],
            version_migration_trajectory_status=str(
                system3_snapshot_state.get("version_migration_trajectory_status")
                or "stable"
            ),
            version_migration_trajectory_target=str(
                system3_snapshot_state.get("version_migration_trajectory_target")
                or "stable_rebuild_ready"
            ),
            version_migration_trajectory_trigger=str(
                system3_snapshot_state.get("version_migration_trajectory_trigger")
                or "migration_line_stable"
            ),
            version_migration_trajectory_notes=[
                str(item)
                for item in list(
                    system3_snapshot_state.get("version_migration_trajectory_notes")
                    or []
                )
            ],
            review_focus=[
                str(item)
                for item in list(system3_snapshot_state.get("review_focus") or [])
            ],
        )
        current_stage_index = max(
            1,
            int((queue_item or {}).get("proactive_cadence_stage_index") or 1),
        )
        current_stage_label = str(
            (queue_item or {}).get("proactive_cadence_stage_label") or "first_touch"
        )
        current_stage_directive = next(
            (
                dict(item)
                for item in list(
                    proactive_orchestration_plan.get("stage_directives") or []
                )
                if str(item.get("stage_label") or "") == current_stage_label
            ),
            None,
        )
        current_stage_guardrail = next(
            (
                dict(item)
                for item in list(
                    proactive_guardrail_plan.get("stage_guardrails") or []
                )
                if str(item.get("stage_label") or "") == current_stage_label
            ),
            None,
        )
        current_stage_actuation = next(
            (
                dict(item)
                for item in list(
                    proactive_actuation_plan.get("stage_actuations") or []
                )
                if str(item.get("stage_label") or "") == current_stage_label
            ),
            None,
        )
        latest_dispatches_for_directive = [
            event
            for event in prior_events
            if event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED
            and latest_proactive_event is not None
            and event.occurred_at >= latest_proactive_event.occurred_at
        ]
        latest_gate_events_for_directive = [
            event
            for event in prior_events
            if event.event_type == PROACTIVE_DISPATCH_GATE_UPDATED
            and latest_proactive_event is not None
            and event.occurred_at >= latest_proactive_event.occurred_at
        ]
        latest_stage_controller_events_for_directive = [
            event
            for event in prior_events
            if event.event_type == PROACTIVE_STAGE_CONTROLLER_UPDATED
            and latest_proactive_event is not None
            and event.occurred_at >= latest_proactive_event.occurred_at
        ]
        latest_line_controller_events_for_directive = [
            event
            for event in prior_events
            if event.event_type == PROACTIVE_LINE_CONTROLLER_UPDATED
            and latest_proactive_event is not None
            and event.occurred_at >= latest_proactive_event.occurred_at
        ]
        prior_stage_controller_decision = None
        prior_line_controller_decision = None
        applicable_stage_controller_event = next(
            (
                event
                for event in reversed(latest_stage_controller_events_for_directive)
                if str(event.payload.get("target_stage_label") or "") == current_stage_label
                and str(event.payload.get("decision") or "") == "slow_next_stage"
            ),
            None,
        )
        if applicable_stage_controller_event is not None:
            prior_stage_controller_decision = ProactiveStageControllerDecision(
                **dict(applicable_stage_controller_event.payload)
            )
        applicable_line_controller_event = next(
            (
                event
                for event in reversed(latest_line_controller_events_for_directive)
                if current_stage_label
                in list(event.payload.get("affected_stage_labels") or [])
                and str(event.payload.get("decision") or "")
                in {"soften_remaining_line", "retire_after_close_loop"}
            ),
            None,
        )
        if applicable_line_controller_event is not None:
            prior_line_controller_decision = ProactiveLineControllerDecision(
                **dict(applicable_line_controller_event.payload)
            )
        latest_dispatched_stage_index = max(
            (
                int(event.payload.get("proactive_cadence_stage_index") or 0)
                for event in latest_dispatches_for_directive
            ),
            default=0,
        )
        if latest_dispatched_stage_index >= current_stage_index:
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "already_dispatched_for_requested_stage",
            }
        if (
            proactive_cadence_plan_model.close_after_stage_index > 0
            and current_stage_index > proactive_cadence_plan_model.close_after_stage_index
        ):
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": "requested_stage_beyond_cadence",
            }

        proactive_stage_refresh_plan = build_proactive_stage_refresh_plan(
            directive=directive_model,
            guidance_plan=guidance_plan_model,
            system3_snapshot=system3_snapshot_model,
            stage_label=current_stage_label,
            queue_status=str((queue_item or {}).get("queue_status") or "due"),
            schedule_reason=str((queue_item or {}).get("schedule_reason") or ""),
            progression_advanced=bool(
                (queue_item or {}).get("proactive_progression_advanced")
            ),
            stage_directive=current_stage_directive,
            stage_actuation=current_stage_actuation,
            prior_stage_controller_decision=prior_stage_controller_decision,
            prior_line_controller_decision=prior_line_controller_decision,
        )
        proactive_dispatch_feedback_assessment = (
            build_proactive_dispatch_feedback_assessment(
                directive=directive_model,
                reengagement_plan=reengagement_plan_model,
                stage_label=current_stage_label,
                dispatch_events_for_directive=[
                    dict(event.payload) for event in latest_dispatches_for_directive
                ],
                gate_events_for_directive=[
                    dict(event.payload) for event in latest_gate_events_for_directive
                ],
            )
        )
        proactive_aggregate_governance_assessment = (
            build_proactive_aggregate_governance_assessment(
                system3_snapshot=system3_snapshot_model
            )
        )
        proactive_stage_replan_assessment = build_proactive_stage_replan_assessment(
            directive=directive_model,
            guidance_plan=guidance_plan_model,
            system3_snapshot=system3_snapshot_model,
            reengagement_plan=reengagement_plan_model,
            stage_refresh_plan=proactive_stage_refresh_plan,
            dispatch_feedback_assessment=proactive_dispatch_feedback_assessment,
            aggregate_governance_assessment=proactive_aggregate_governance_assessment,
            prior_stage_controller_decision=prior_stage_controller_decision,
            prior_line_controller_decision=prior_line_controller_decision,
        )
        proactive_aggregate_controller_decision = (
            build_proactive_aggregate_controller_decision(
                directive=directive_model,
                proactive_cadence_plan=proactive_cadence_plan_model,
                system3_snapshot=system3_snapshot_model,
                current_stage_label=current_stage_label,
                current_stage_index=current_stage_index,
                stage_replan_assessment=proactive_stage_replan_assessment,
                aggregate_governance_assessment=proactive_aggregate_governance_assessment,
            )
        )
        proactive_orchestration_controller_decision = (
            build_proactive_orchestration_controller_decision(
                directive=directive_model,
                proactive_cadence_plan=proactive_cadence_plan_model,
                current_stage_label=current_stage_label,
                current_stage_index=current_stage_index,
                stage_replan_assessment=proactive_stage_replan_assessment,
                guidance_plan=guidance_plan_model,
                session_ritual_plan=session_ritual_plan_model,
                somatic_orchestration_plan=somatic_orchestration_plan_model,
                aggregate_controller_decision=proactive_aggregate_controller_decision,
            )
        )
        proactive_dispatch_gate_decision = build_proactive_dispatch_gate_decision(
            directive=directive_model,
            guidance_plan=guidance_plan_model,
            system3_snapshot=system3_snapshot_model,
            stage_replan_assessment=proactive_stage_replan_assessment,
            queue_status=str((queue_item or {}).get("queue_status") or "due"),
            schedule_reason=str((queue_item or {}).get("schedule_reason") or ""),
            progression_advanced=bool(
                (queue_item or {}).get("proactive_progression_advanced")
            ),
            aggregate_governance_assessment=proactive_aggregate_governance_assessment,
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=proactive_orchestration_controller_decision,
            session_ritual_plan=session_ritual_plan_model,
            somatic_orchestration_plan=somatic_orchestration_plan_model,
        )
        proactive_stage_controller_decision = (
            build_proactive_stage_controller_decision(
                directive=directive_model,
                proactive_cadence_plan=proactive_cadence_plan_model,
                guidance_plan=guidance_plan_model,
                system3_snapshot=system3_snapshot_model,
                current_stage_label=current_stage_label,
                current_stage_index=current_stage_index,
                stage_replan_assessment=proactive_stage_replan_assessment,
                dispatch_feedback_assessment=proactive_dispatch_feedback_assessment,
                aggregate_governance_assessment=proactive_aggregate_governance_assessment,
                aggregate_controller_decision=proactive_aggregate_controller_decision,
                orchestration_controller_decision=proactive_orchestration_controller_decision,
                session_ritual_plan=session_ritual_plan_model,
                somatic_orchestration_plan=somatic_orchestration_plan_model,
            )
        )
        proactive_line_controller_decision = build_proactive_line_controller_decision(
            directive=directive_model,
            proactive_cadence_plan=proactive_cadence_plan_model,
            guidance_plan=guidance_plan_model,
            system3_snapshot=system3_snapshot_model,
            current_stage_label=current_stage_label,
            current_stage_index=current_stage_index,
            stage_replan_assessment=proactive_stage_replan_assessment,
            dispatch_feedback_assessment=proactive_dispatch_feedback_assessment,
            stage_controller_decision=proactive_stage_controller_decision,
            dispatch_gate_decision=proactive_dispatch_gate_decision,
            aggregate_governance_assessment=proactive_aggregate_governance_assessment,
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=proactive_orchestration_controller_decision,
            session_ritual_plan=session_ritual_plan_model,
            somatic_orchestration_plan=somatic_orchestration_plan_model,
        )
        proactive_dispatch_envelope_decision = (
            build_proactive_dispatch_envelope_decision(
                stage_label=current_stage_label,
                current_stage_directive=current_stage_directive,
                current_stage_actuation=current_stage_actuation,
                stage_refresh_plan=proactive_stage_refresh_plan,
                stage_replan_assessment=proactive_stage_replan_assessment,
                dispatch_feedback_assessment=proactive_dispatch_feedback_assessment,
                dispatch_gate_decision=proactive_dispatch_gate_decision,
                aggregate_controller_decision=proactive_aggregate_controller_decision,
                orchestration_controller_decision=proactive_orchestration_controller_decision,
                stage_controller_decision=proactive_stage_controller_decision,
                line_controller_decision=proactive_line_controller_decision,
            )
        )
        queue_status_for_stage_state = str((queue_item or {}).get("queue_status") or "due")
        if proactive_dispatch_gate_decision.decision == "defer":
            queue_status_for_stage_state = "scheduled"
        elif proactive_dispatch_gate_decision.decision == "hold":
            queue_status_for_stage_state = "hold"
        proactive_stage_state_decision = build_proactive_stage_state_decision(
            stage_label=current_stage_label,
            stage_index=current_stage_index,
            stage_count=max(
                1,
                proactive_cadence_plan_model.close_after_stage_index
                or len(proactive_cadence_plan_model.stage_labels)
                or 1,
            ),
            queue_status=queue_status_for_stage_state,
            schedule_reason=str((queue_item or {}).get("schedule_reason") or ""),
            progression_action=str(
                (queue_item or {}).get("proactive_progression_stage_action") or "none"
            ),
            progression_advanced=bool(
                (queue_item or {}).get("proactive_progression_advanced")
            ),
            line_state=proactive_line_controller_decision.line_state,
            current_stage_delivery_mode=str(
                (current_stage_directive or {}).get("delivery_mode") or "single_message"
            ),
            current_stage_autonomy_mode=str(
                (current_stage_directive or {}).get("autonomy_mode")
                or "light_invitation"
            ),
            current_reengagement_delivery_mode=reengagement_plan_model.delivery_mode,
            selected_strategy_key=proactive_dispatch_envelope_decision.selected_strategy_key,
            selected_pressure_mode=proactive_dispatch_envelope_decision.selected_pressure_mode,
            selected_autonomy_signal=proactive_dispatch_envelope_decision.selected_autonomy_signal,
            dispatch_envelope_key=proactive_dispatch_envelope_decision.envelope_key,
            dispatch_envelope_decision=proactive_dispatch_envelope_decision.decision,
            dispatch_gate_decision=proactive_dispatch_gate_decision.decision,
            aggregate_controller_decision=proactive_aggregate_controller_decision.decision,
            orchestration_controller_decision=(
                proactive_orchestration_controller_decision.decision
            ),
            stage_controller_decision=proactive_stage_controller_decision.decision,
            line_controller_decision=proactive_line_controller_decision.decision,
        )
        cadence_stage_labels = list(proactive_cadence_plan_model.stage_labels)
        next_stage_label = (
            cadence_stage_labels[current_stage_index]
            if 0 <= current_stage_index < len(cadence_stage_labels)
            else None
        )
        proactive_stage_transition_decision = (
            build_proactive_stage_transition_decision(
                stage_state_decision=proactive_stage_state_decision,
                next_stage_label=next_stage_label,
                dispatch_gate_decision=proactive_dispatch_gate_decision,
                dispatch_envelope_decision=proactive_dispatch_envelope_decision,
                aggregate_controller_decision=proactive_aggregate_controller_decision,
                orchestration_controller_decision=(
                    proactive_orchestration_controller_decision
                ),
                stage_controller_decision=proactive_stage_controller_decision,
                line_controller_decision=proactive_line_controller_decision,
            )
        )
        proactive_stage_machine_decision = build_proactive_stage_machine_decision(
            stage_state_decision=proactive_stage_state_decision,
            stage_transition_decision=proactive_stage_transition_decision,
            dispatch_envelope_decision=proactive_dispatch_envelope_decision,
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=(
                proactive_orchestration_controller_decision
            ),
            stage_controller_decision=proactive_stage_controller_decision,
            line_controller_decision=proactive_line_controller_decision,
        )
        proactive_line_state_decision = build_proactive_line_state_decision(
            proactive_cadence_plan=proactive_cadence_plan_model,
            stage_machine_decision=proactive_stage_machine_decision,
            line_controller_decision=proactive_line_controller_decision,
        )
        proactive_line_transition_decision = build_proactive_line_transition_decision(
            line_state_decision=proactive_line_state_decision,
            stage_transition_decision=proactive_stage_transition_decision,
        )
        proactive_line_machine_decision = build_proactive_line_machine_decision(
            line_state_decision=proactive_line_state_decision,
            line_transition_decision=proactive_line_transition_decision,
        )
        proactive_lifecycle_state_decision = build_proactive_lifecycle_state_decision(
            stage_machine_decision=proactive_stage_machine_decision,
            line_machine_decision=proactive_line_machine_decision,
            orchestration_controller_decision=(
                proactive_orchestration_controller_decision
            ),
        )
        proactive_lifecycle_transition_decision = (
            build_proactive_lifecycle_transition_decision(
                lifecycle_state_decision=proactive_lifecycle_state_decision,
            )
        )
        proactive_lifecycle_machine_decision = (
            build_proactive_lifecycle_machine_decision(
                lifecycle_state_decision=proactive_lifecycle_state_decision,
                lifecycle_transition_decision=proactive_lifecycle_transition_decision,
            )
        )
        proactive_lifecycle_controller_decision = (
            build_proactive_lifecycle_controller_decision(
                lifecycle_machine_decision=proactive_lifecycle_machine_decision,
                aggregate_controller_decision=proactive_aggregate_controller_decision,
                orchestration_controller_decision=(
                    proactive_orchestration_controller_decision
                ),
            )
        )
        proactive_lifecycle_envelope_decision = (
            build_proactive_lifecycle_envelope_decision(
                lifecycle_machine_decision=proactive_lifecycle_machine_decision,
                lifecycle_controller_decision=proactive_lifecycle_controller_decision,
                dispatch_envelope_decision=proactive_dispatch_envelope_decision,
            )
        )
        proactive_lifecycle_scheduler_decision = (
            build_proactive_lifecycle_scheduler_decision(
                lifecycle_envelope_decision=proactive_lifecycle_envelope_decision,
                proactive_scheduling_plan=proactive_scheduling_plan,
                dispatch_gate_decision=proactive_dispatch_gate_decision,
            )
        )
        proactive_lifecycle_window_decision = build_proactive_lifecycle_window_decision(
            lifecycle_scheduler_decision=proactive_lifecycle_scheduler_decision,
            current_queue_status=str((queue_item or {}).get("queue_status") or "due"),
            schedule_reason=str((queue_item or {}).get("schedule_reason") or ""),
            progression_action=str(
                (queue_item or {}).get("proactive_progression_stage_action") or "none"
            ),
            progression_advanced=bool(
                (queue_item or {}).get("proactive_progression_advanced")
            ),
        )
        proactive_lifecycle_queue_decision = build_proactive_lifecycle_queue_decision(
            lifecycle_window_decision=proactive_lifecycle_window_decision,
            current_queue_status=str((queue_item or {}).get("queue_status") or "due"),
        )
        effective_stage_directive = {
            **(current_stage_directive or {}),
            "delivery_mode": (
                proactive_dispatch_envelope_decision.selected_stage_delivery_mode
            ),
            "question_mode": (
                proactive_dispatch_envelope_decision.selected_stage_question_mode
            ),
            "autonomy_mode": (
                proactive_dispatch_envelope_decision.selected_stage_autonomy_mode
            ),
            "objective": proactive_dispatch_envelope_decision.selected_stage_objective,
        }
        effective_stage_actuation = {
            **(current_stage_actuation or {}),
            "opening_move": proactive_dispatch_envelope_decision.selected_opening_move,
            "bridge_move": proactive_dispatch_envelope_decision.selected_bridge_move,
            "closing_move": proactive_dispatch_envelope_decision.selected_closing_move,
            "continuity_anchor": (
                proactive_dispatch_envelope_decision.selected_continuity_anchor
            ),
            "somatic_mode": proactive_dispatch_envelope_decision.selected_somatic_mode,
            "somatic_body_anchor": (
                proactive_dispatch_envelope_decision.selected_somatic_body_anchor
            ),
            "followup_style": (
                proactive_dispatch_envelope_decision.selected_followup_style
            ),
            "user_space_signal": (
                proactive_dispatch_envelope_decision.selected_user_space_signal
            ),
        }
        effective_reengagement_plan_model = ReengagementPlan(
            status=reengagement_plan_model.status,
            ritual_mode=proactive_dispatch_envelope_decision.selected_ritual_mode,
            delivery_mode=(
                proactive_dispatch_envelope_decision.selected_reengagement_delivery_mode
            ),
            strategy_key=proactive_dispatch_envelope_decision.selected_strategy_key,
            relational_move=proactive_dispatch_envelope_decision.selected_relational_move,
            pressure_mode=proactive_dispatch_envelope_decision.selected_pressure_mode,
            autonomy_signal=proactive_dispatch_envelope_decision.selected_autonomy_signal,
            sequence_objective=(
                proactive_dispatch_envelope_decision.selected_sequence_objective
            ),
            somatic_action=proactive_dispatch_envelope_decision.selected_somatic_action,
            segment_labels=list(reengagement_plan_model.segment_labels),
            focus_points=list(reengagement_plan_model.focus_points),
            tone=reengagement_plan_model.tone,
            opening_hint=reengagement_plan_model.opening_hint,
            closing_hint=reengagement_plan_model.closing_hint,
            rationale=reengagement_plan_model.rationale,
        )
        prior_stage_controller_applied = bool(
            prior_stage_controller_decision is not None
            and prior_stage_controller_decision.status == "active"
            and prior_stage_controller_decision.changed
            and prior_stage_controller_decision.decision == "slow_next_stage"
            and prior_stage_controller_decision.target_stage_label == current_stage_label
        )
        prior_line_controller_applied = bool(
            prior_line_controller_decision is not None
            and prior_line_controller_decision.status == "active"
            and prior_line_controller_decision.changed
            and prior_line_controller_decision.decision
            in {"soften_remaining_line", "retire_after_close_loop"}
            and current_stage_label in prior_line_controller_decision.affected_stage_labels
        )
        followup_units = build_reengagement_output_units(
            recent_user_text=recent_user_text,
            directive=directive_model,
            reengagement_plan=effective_reengagement_plan_model,
            session_ritual_plan=session_ritual_plan_model,
            somatic_orchestration_plan=somatic_orchestration_plan_model,
            runtime_coordination_snapshot=runtime_coordination_model,
            cadence_stage_label=current_stage_label,
            cadence_stage_index=current_stage_index,
            cadence_stage_count=max(
                1,
                proactive_cadence_plan_model.close_after_stage_index
                or len(proactive_cadence_plan_model.stage_labels)
                or 1,
            ),
            stage_directive=effective_stage_directive,
            stage_actuation=effective_stage_actuation,
        )
        followup_content = " ".join(
            item["content"] for item in followup_units if item.get("content")
        ).strip()
        proactive_lifecycle_dispatch_decision = (
            build_proactive_lifecycle_dispatch_decision(
                lifecycle_queue_decision=proactive_lifecycle_queue_decision,
                dispatch_gate_decision=proactive_dispatch_gate_decision,
                current_queue_status=str((queue_item or {}).get("queue_status") or "due"),
                schedule_reason=str((queue_item or {}).get("schedule_reason") or ""),
                rendered_unit_count=len(followup_units),
                has_followup_content=bool(followup_content),
            )
        )
        if proactive_lifecycle_dispatch_decision.decision not in {
            "dispatch_lifecycle_now",
            "close_loop_lifecycle_dispatch",
        }:
            proactive_lifecycle_outcome_decision = (
                build_proactive_lifecycle_outcome_decision(
                    lifecycle_dispatch_decision=proactive_lifecycle_dispatch_decision,
                    dispatched=False,
                    message_event_count=0,
                )
            )
            proactive_lifecycle_resolution_decision = (
                build_proactive_lifecycle_resolution_decision(
                    lifecycle_outcome_decision=proactive_lifecycle_outcome_decision,
                    lifecycle_queue_decision=proactive_lifecycle_queue_decision,
                    line_state_decision=proactive_line_state_decision,
                    line_transition_decision=proactive_line_transition_decision,
                )
            )
            proactive_lifecycle_activation_decision = (
                build_proactive_lifecycle_activation_decision(
                    lifecycle_resolution_decision=proactive_lifecycle_resolution_decision
                )
            )
            proactive_lifecycle_settlement_decision = (
                build_proactive_lifecycle_settlement_decision(
                    lifecycle_activation_decision=proactive_lifecycle_activation_decision
                )
            )
            proactive_lifecycle_closure_decision = (
                build_proactive_lifecycle_closure_decision(
                    lifecycle_settlement_decision=proactive_lifecycle_settlement_decision
                )
            )
            proactive_lifecycle_availability_decision = (
                build_proactive_lifecycle_availability_decision(
                    lifecycle_closure_decision=proactive_lifecycle_closure_decision
                )
            )
            proactive_lifecycle_retention_decision = (
                build_proactive_lifecycle_retention_decision(
                    lifecycle_availability_decision=proactive_lifecycle_availability_decision
                )
            )
            proactive_lifecycle_eligibility_decision = (
                build_proactive_lifecycle_eligibility_decision(
                    lifecycle_retention_decision=proactive_lifecycle_retention_decision
                )
            )
            proactive_lifecycle_candidate_decision = (
                build_proactive_lifecycle_candidate_decision(
                    lifecycle_eligibility_decision=proactive_lifecycle_eligibility_decision
                )
            )
            proactive_lifecycle_selectability_decision = (
                build_proactive_lifecycle_selectability_decision(
                    lifecycle_candidate_decision=proactive_lifecycle_candidate_decision
                )
            )
            proactive_lifecycle_reentry_decision = (
                build_proactive_lifecycle_reentry_decision(
                    lifecycle_selectability_decision=(
                        proactive_lifecycle_selectability_decision
                    )
                )
            )
            proactive_lifecycle_reactivation_decision = (
                build_proactive_lifecycle_reactivation_decision(
                    lifecycle_reentry_decision=proactive_lifecycle_reentry_decision
                )
            )
            proactive_lifecycle_resumption_decision = (
                build_proactive_lifecycle_resumption_decision(
                    lifecycle_reactivation_decision=(
                        proactive_lifecycle_reactivation_decision
                    )
                )
            )
            proactive_lifecycle_readiness_decision = (
                build_proactive_lifecycle_readiness_decision(
                    lifecycle_resumption_decision=(
                        proactive_lifecycle_resumption_decision
                    )
                )
            )
            proactive_lifecycle_arming_decision = (
                build_proactive_lifecycle_arming_decision(
                    lifecycle_readiness_decision=(
                        proactive_lifecycle_readiness_decision
                    )
                )
            )
            proactive_lifecycle_trigger_decision = (
                build_proactive_lifecycle_trigger_decision(
                    lifecycle_arming_decision=proactive_lifecycle_arming_decision
                )
            )
            proactive_lifecycle_launch_decision = (
                build_proactive_lifecycle_launch_decision(
                    lifecycle_trigger_decision=proactive_lifecycle_trigger_decision
                )
            )
            proactive_lifecycle_handoff_decision = (
                build_proactive_lifecycle_handoff_decision(
                    lifecycle_launch_decision=proactive_lifecycle_launch_decision
                )
            )
            proactive_lifecycle_continuation_decision = (
                build_proactive_lifecycle_continuation_decision(
                    lifecycle_handoff_decision=proactive_lifecycle_handoff_decision
                )
            )
            proactive_lifecycle_sustainment_decision = (
                build_proactive_lifecycle_sustainment_decision(
                    lifecycle_continuation_decision=(
                        proactive_lifecycle_continuation_decision
                    )
                )
            )
            proactive_lifecycle_stewardship_decision = (
                build_proactive_lifecycle_stewardship_decision(
                    lifecycle_sustainment_decision=(
                        proactive_lifecycle_sustainment_decision
                    )
                )
            )
            proactive_lifecycle_guardianship_decision = (
                build_proactive_lifecycle_guardianship_decision(
                    lifecycle_stewardship_decision=(
                        proactive_lifecycle_stewardship_decision
                    )
                )
            )
            proactive_lifecycle_oversight_decision = (
                build_proactive_lifecycle_oversight_decision(
                    lifecycle_guardianship_decision=(
                        proactive_lifecycle_guardianship_decision
                    )
                )
            )
            proactive_lifecycle_assurance_decision = (
                build_proactive_lifecycle_assurance_decision(
                    lifecycle_oversight_decision=(
                        proactive_lifecycle_oversight_decision
                    )
                )
            )
            proactive_lifecycle_attestation_decision = (
                build_proactive_lifecycle_attestation_decision(
                    lifecycle_assurance_decision=(
                        proactive_lifecycle_assurance_decision
                    )
                )
            )
            proactive_lifecycle_verification_decision = (
                build_proactive_lifecycle_verification_decision(
                    lifecycle_attestation_decision=(
                        proactive_lifecycle_attestation_decision
                    )
                )
            )
            proactive_lifecycle_certification_decision = (
                build_proactive_lifecycle_certification_decision(
                    lifecycle_verification_decision=(
                        proactive_lifecycle_verification_decision
                    )
                )
            )
            proactive_lifecycle_confirmation_decision = (
                build_proactive_lifecycle_confirmation_decision(
                    lifecycle_certification_decision=(
                        proactive_lifecycle_certification_decision
                    )
                )
            )
            proactive_lifecycle_ratification_decision = (
                build_proactive_lifecycle_ratification_decision(
                    lifecycle_confirmation_decision=(
                        proactive_lifecycle_confirmation_decision
                    )
                )
            )
            proactive_lifecycle_endorsement_decision = (
                build_proactive_lifecycle_endorsement_decision(
                    lifecycle_ratification_decision=(
                        proactive_lifecycle_ratification_decision
                    )
                )
            )
            proactive_lifecycle_authorization_decision = (
                build_proactive_lifecycle_authorization_decision(
                    lifecycle_endorsement_decision=(
                        proactive_lifecycle_endorsement_decision
                    )
                )
            )
            proactive_lifecycle_enactment_decision = (
                build_proactive_lifecycle_enactment_decision(
                    lifecycle_authorization_decision=(
                        proactive_lifecycle_authorization_decision
                    )
                )
            )
            proactive_lifecycle_finality_decision = (
                build_proactive_lifecycle_finality_decision(
                    lifecycle_enactment_decision=proactive_lifecycle_enactment_decision
                )
            )
            proactive_lifecycle_completion_decision = (
                build_proactive_lifecycle_completion_decision(
                    lifecycle_finality_decision=proactive_lifecycle_finality_decision
                )
            )
            proactive_lifecycle_conclusion_decision = (
                build_proactive_lifecycle_conclusion_decision(
                    lifecycle_completion_decision=proactive_lifecycle_completion_decision
                )
            )
            proactive_lifecycle_disposition_decision = (
                build_proactive_lifecycle_disposition_decision(
                    lifecycle_conclusion_decision=proactive_lifecycle_conclusion_decision
                )
            )
            proactive_lifecycle_standing_decision = (
                build_proactive_lifecycle_standing_decision(
                    lifecycle_disposition_decision=(
                        proactive_lifecycle_disposition_decision
                    )
                )
            )
            proactive_lifecycle_residency_decision = (
                build_proactive_lifecycle_residency_decision(
                    lifecycle_standing_decision=proactive_lifecycle_standing_decision
                )
            )
            proactive_lifecycle_tenure_decision = (
                build_proactive_lifecycle_tenure_decision(
                    lifecycle_residency_decision=proactive_lifecycle_residency_decision
                )
            )
            proactive_lifecycle_persistence_decision = (
                build_proactive_lifecycle_persistence_decision(
                    lifecycle_tenure_decision=proactive_lifecycle_tenure_decision
                )
            )
            proactive_lifecycle_durability_decision = (
                build_proactive_lifecycle_durability_decision(
                    lifecycle_persistence_decision=(
                        proactive_lifecycle_persistence_decision
                    )
                )
            )
            proactive_lifecycle_longevity_decision = (
                build_proactive_lifecycle_longevity_decision(
                    lifecycle_durability_decision=proactive_lifecycle_durability_decision
                )
            )
            proactive_lifecycle_legacy_decision = (
                build_proactive_lifecycle_legacy_decision(
                    lifecycle_longevity_decision=proactive_lifecycle_longevity_decision
                )
            )
            proactive_lifecycle_heritage_decision = (
                build_proactive_lifecycle_heritage_decision(
                    lifecycle_legacy_decision=proactive_lifecycle_legacy_decision
                )
            )
            proactive_lifecycle_lineage_decision = (
                build_proactive_lifecycle_lineage_decision(
                    lifecycle_heritage_decision=proactive_lifecycle_heritage_decision
                )
            )
            proactive_lifecycle_ancestry_decision = (
                build_proactive_lifecycle_ancestry_decision(
                    lifecycle_lineage_decision=proactive_lifecycle_lineage_decision
                )
            )
            proactive_lifecycle_provenance_decision = (
                build_proactive_lifecycle_provenance_decision(
                    lifecycle_ancestry_decision=proactive_lifecycle_ancestry_decision
                )
            )
            proactive_lifecycle_origin_decision = (
                build_proactive_lifecycle_origin_decision(
                    lifecycle_provenance_decision=proactive_lifecycle_provenance_decision
                )
            )
            proactive_lifecycle_root_decision = (
                build_proactive_lifecycle_root_decision(
                    lifecycle_origin_decision=proactive_lifecycle_origin_decision
                )
            )
            proactive_lifecycle_foundation_decision = (
                build_proactive_lifecycle_foundation_decision(
                    lifecycle_root_decision=proactive_lifecycle_root_decision
                )
            )
            proactive_lifecycle_bedrock_decision = (
                build_proactive_lifecycle_bedrock_decision(
                    lifecycle_foundation_decision=proactive_lifecycle_foundation_decision
                )
            )
            proactive_lifecycle_substrate_decision = (
                build_proactive_lifecycle_substrate_decision(
                    lifecycle_bedrock_decision=proactive_lifecycle_bedrock_decision
                )
            )
            proactive_lifecycle_stratum_decision = (
                build_proactive_lifecycle_stratum_decision(
                    lifecycle_substrate_decision=proactive_lifecycle_substrate_decision
                )
            )
            proactive_lifecycle_layer_decision = (
                build_proactive_lifecycle_layer_decision(
                    lifecycle_stratum_decision=proactive_lifecycle_stratum_decision
                )
            )
            stored_events = await self._stream_service.append_events(
                stream_id=session_id,
                expected_version=len(prior_events),
                events=[
                    NewEvent(
                        event_type=PROACTIVE_STAGE_REFRESH_UPDATED,
                        payload=asdict(proactive_stage_refresh_plan),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
                        payload=asdict(proactive_aggregate_governance_assessment),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
                        payload=asdict(proactive_aggregate_controller_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
                        payload=asdict(proactive_orchestration_controller_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_REPLAN_UPDATED,
                        payload=asdict(proactive_stage_replan_assessment),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_CONTROLLER_UPDATED,
                        payload=asdict(proactive_stage_controller_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_CONTROLLER_UPDATED,
                        payload=asdict(proactive_line_controller_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
                        payload=asdict(proactive_dispatch_feedback_assessment),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_DISPATCH_GATE_UPDATED,
                        payload=asdict(proactive_dispatch_gate_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
                        payload=asdict(proactive_dispatch_envelope_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_STATE_UPDATED,
                        payload=asdict(proactive_stage_state_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_TRANSITION_UPDATED,
                        payload=asdict(proactive_stage_transition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_MACHINE_UPDATED,
                        payload=asdict(proactive_stage_machine_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_STATE_UPDATED,
                        payload=asdict(proactive_line_state_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_TRANSITION_UPDATED,
                        payload=asdict(proactive_line_transition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_MACHINE_UPDATED,
                        payload=asdict(proactive_line_machine_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_STATE_UPDATED,
                        payload=asdict(proactive_lifecycle_state_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_TRANSITION_UPDATED,
                        payload=asdict(proactive_lifecycle_transition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_MACHINE_UPDATED,
                        payload=asdict(proactive_lifecycle_machine_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED,
                        payload=asdict(proactive_lifecycle_controller_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED,
                        payload=asdict(proactive_lifecycle_envelope_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED,
                        payload=asdict(proactive_lifecycle_scheduler_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_WINDOW_UPDATED,
                        payload=asdict(proactive_lifecycle_window_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_QUEUE_UPDATED,
                        payload=asdict(proactive_lifecycle_queue_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_DISPATCH_UPDATED,
                        payload=asdict(proactive_lifecycle_dispatch_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_OUTCOME_UPDATED,
                        payload=asdict(proactive_lifecycle_outcome_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED,
                        payload=asdict(proactive_lifecycle_resolution_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED,
                        payload=asdict(proactive_lifecycle_activation_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED,
                        payload=asdict(proactive_lifecycle_settlement_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CLOSURE_UPDATED,
                        payload=asdict(proactive_lifecycle_closure_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED,
                        payload=asdict(proactive_lifecycle_availability_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_RETENTION_UPDATED,
                        payload=asdict(proactive_lifecycle_retention_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED,
                        payload=asdict(proactive_lifecycle_eligibility_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED,
                        payload=asdict(proactive_lifecycle_candidate_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED,
                        payload=asdict(proactive_lifecycle_selectability_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_REENTRY_UPDATED,
                        payload=asdict(proactive_lifecycle_reentry_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED,
                        payload=asdict(proactive_lifecycle_reactivation_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED,
                        payload=asdict(proactive_lifecycle_resumption_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_READINESS_UPDATED,
                        payload=asdict(proactive_lifecycle_readiness_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ARMING_UPDATED,
                        payload=asdict(proactive_lifecycle_arming_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_TRIGGER_UPDATED,
                        payload=asdict(proactive_lifecycle_trigger_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_LAUNCH_UPDATED,
                        payload=asdict(proactive_lifecycle_launch_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_HANDOFF_UPDATED,
                        payload=asdict(proactive_lifecycle_handoff_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED,
                        payload=asdict(proactive_lifecycle_continuation_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED,
                        payload=asdict(proactive_lifecycle_sustainment_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED,
                        payload=asdict(proactive_lifecycle_stewardship_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED,
                        payload=asdict(proactive_lifecycle_guardianship_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED,
                        payload=asdict(proactive_lifecycle_oversight_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED,
                        payload=asdict(proactive_lifecycle_assurance_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED,
                        payload=asdict(proactive_lifecycle_attestation_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED,
                        payload=asdict(proactive_lifecycle_verification_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED,
                        payload=asdict(proactive_lifecycle_certification_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED,
                        payload=asdict(proactive_lifecycle_confirmation_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED,
                        payload=asdict(proactive_lifecycle_ratification_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED,
                        payload=asdict(proactive_lifecycle_endorsement_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED,
                        payload=asdict(proactive_lifecycle_authorization_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED,
                        payload=asdict(proactive_lifecycle_enactment_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_FINALITY_UPDATED,
                        payload=asdict(proactive_lifecycle_finality_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_COMPLETION_UPDATED,
                        payload=asdict(proactive_lifecycle_completion_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED,
                        payload=asdict(proactive_lifecycle_conclusion_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED,
                        payload=asdict(proactive_lifecycle_disposition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_STANDING_UPDATED,
                        payload=asdict(proactive_lifecycle_standing_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED,
                        payload=asdict(proactive_lifecycle_residency_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_TENURE_UPDATED,
                        payload=asdict(proactive_lifecycle_tenure_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED,
                        payload=asdict(proactive_lifecycle_persistence_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_DURABILITY_UPDATED,
                        payload=asdict(proactive_lifecycle_durability_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED,
                        payload=asdict(proactive_lifecycle_longevity_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_LEGACY_UPDATED,
                        payload=asdict(proactive_lifecycle_legacy_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_HERITAGE_UPDATED,
                        payload=asdict(proactive_lifecycle_heritage_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_LINEAGE_UPDATED,
                        payload=asdict(proactive_lifecycle_lineage_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED,
                        payload=asdict(proactive_lifecycle_ancestry_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED,
                        payload=asdict(proactive_lifecycle_provenance_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ORIGIN_UPDATED,
                        payload=asdict(proactive_lifecycle_origin_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ROOT_UPDATED,
                        payload=asdict(proactive_lifecycle_root_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED,
                        payload=asdict(proactive_lifecycle_foundation_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_BEDROCK_UPDATED,
                        payload=asdict(proactive_lifecycle_bedrock_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED,
                        payload=asdict(proactive_lifecycle_substrate_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_STRATUM_UPDATED,
                        payload=asdict(proactive_lifecycle_stratum_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_LAYER_UPDATED,
                        payload=asdict(proactive_lifecycle_layer_decision),
                    ),
                ],
            )
            updated_projection = await self._stream_service.project_stream(
                stream_id=session_id,
                projector_name="session-runtime",
                projector_version="v1",
            )
            reason_map = {
                "reschedule_lifecycle_dispatch": "lifecycle_dispatch_rescheduled",
                "hold_lifecycle_dispatch": "lifecycle_dispatch_hold",
                "retire_lifecycle_dispatch": "lifecycle_dispatch_retired",
            }
            return {
                "session_id": session_id,
                "dispatched": False,
                "reason": reason_map.get(
                    proactive_lifecycle_dispatch_decision.decision,
                    "lifecycle_dispatch_hold",
                ),
                "gate": asdict(proactive_dispatch_gate_decision),
                "lifecycle_dispatch": asdict(proactive_lifecycle_dispatch_decision),
                "lifecycle_outcome": asdict(proactive_lifecycle_outcome_decision),
                "lifecycle_resolution": asdict(
                    proactive_lifecycle_resolution_decision
                ),
                "lifecycle_activation": asdict(
                    proactive_lifecycle_activation_decision
                ),
                "lifecycle_settlement": asdict(
                    proactive_lifecycle_settlement_decision
                ),
                "lifecycle_closure": asdict(proactive_lifecycle_closure_decision),
                "lifecycle_availability": asdict(
                    proactive_lifecycle_availability_decision
                ),
                "lifecycle_retention": asdict(
                    proactive_lifecycle_retention_decision
                ),
                "lifecycle_eligibility": asdict(
                    proactive_lifecycle_eligibility_decision
                ),
                "lifecycle_candidate": asdict(proactive_lifecycle_candidate_decision),
                "lifecycle_selectability": asdict(
                    proactive_lifecycle_selectability_decision
                ),
                "lifecycle_reentry": asdict(proactive_lifecycle_reentry_decision),
                "lifecycle_reactivation": asdict(
                    proactive_lifecycle_reactivation_decision
                ),
                "lifecycle_resumption": asdict(
                    proactive_lifecycle_resumption_decision
                ),
                "lifecycle_readiness": asdict(
                    proactive_lifecycle_readiness_decision
                ),
                "lifecycle_arming": asdict(proactive_lifecycle_arming_decision),
                "lifecycle_trigger": asdict(proactive_lifecycle_trigger_decision),
                "lifecycle_launch": asdict(proactive_lifecycle_launch_decision),
                "lifecycle_handoff": asdict(proactive_lifecycle_handoff_decision),
                "lifecycle_continuation": asdict(
                    proactive_lifecycle_continuation_decision
                ),
                "lifecycle_sustainment": asdict(
                    proactive_lifecycle_sustainment_decision
                ),
                "lifecycle_stewardship": asdict(
                    proactive_lifecycle_stewardship_decision
                ),
                "lifecycle_guardianship": asdict(
                    proactive_lifecycle_guardianship_decision
                ),
                "lifecycle_oversight": asdict(
                    proactive_lifecycle_oversight_decision
                ),
                "lifecycle_assurance": asdict(
                    proactive_lifecycle_assurance_decision
                ),
                "lifecycle_attestation": asdict(
                    proactive_lifecycle_attestation_decision
                ),
                "lifecycle_verification": asdict(
                    proactive_lifecycle_verification_decision
                ),
                "lifecycle_certification": asdict(
                    proactive_lifecycle_certification_decision
                ),
                "lifecycle_confirmation": asdict(
                    proactive_lifecycle_confirmation_decision
                ),
                "lifecycle_ratification": asdict(
                    proactive_lifecycle_ratification_decision
                ),
                "lifecycle_endorsement": asdict(
                    proactive_lifecycle_endorsement_decision
                ),
                "lifecycle_authorization": asdict(
                    proactive_lifecycle_authorization_decision
                ),
                "lifecycle_enactment": asdict(proactive_lifecycle_enactment_decision),
                "lifecycle_finality": asdict(proactive_lifecycle_finality_decision),
                "lifecycle_completion": asdict(proactive_lifecycle_completion_decision),
                "lifecycle_conclusion": asdict(proactive_lifecycle_conclusion_decision),
                "lifecycle_disposition": asdict(
                    proactive_lifecycle_disposition_decision
                ),
                "lifecycle_standing": asdict(proactive_lifecycle_standing_decision),
                "lifecycle_residency": asdict(
                    proactive_lifecycle_residency_decision
                ),
                "lifecycle_tenure": asdict(proactive_lifecycle_tenure_decision),
                "lifecycle_persistence": asdict(
                    proactive_lifecycle_persistence_decision
                ),
                "lifecycle_durability": asdict(
                    proactive_lifecycle_durability_decision
                ),
                "lifecycle_longevity": asdict(proactive_lifecycle_longevity_decision),
                "lifecycle_legacy": asdict(proactive_lifecycle_legacy_decision),
                "lifecycle_heritage": asdict(proactive_lifecycle_heritage_decision),
                "lifecycle_lineage": asdict(proactive_lifecycle_lineage_decision),
                "lifecycle_ancestry": asdict(proactive_lifecycle_ancestry_decision),
                "lifecycle_provenance": asdict(
                    proactive_lifecycle_provenance_decision
                ),
                "lifecycle_origin": asdict(proactive_lifecycle_origin_decision),
                "lifecycle_root": asdict(proactive_lifecycle_root_decision),
                "lifecycle_foundation": asdict(proactive_lifecycle_foundation_decision),
                "lifecycle_bedrock": asdict(proactive_lifecycle_bedrock_decision),
                "lifecycle_substrate": asdict(proactive_lifecycle_substrate_decision),
                "lifecycle_stratum": asdict(proactive_lifecycle_stratum_decision),
                "lifecycle_layer": asdict(proactive_lifecycle_layer_decision),
                "events": [
                    self._stream_service.serialize_event(event)
                    for event in stored_events
                ],
                "projection": updated_projection,
            }

        proactive_lifecycle_outcome_decision = (
            build_proactive_lifecycle_outcome_decision(
                lifecycle_dispatch_decision=proactive_lifecycle_dispatch_decision,
                dispatched=True,
                message_event_count=len(followup_units),
            )
        )
        proactive_lifecycle_resolution_decision = (
            build_proactive_lifecycle_resolution_decision(
                lifecycle_outcome_decision=proactive_lifecycle_outcome_decision,
                lifecycle_queue_decision=proactive_lifecycle_queue_decision,
                line_state_decision=proactive_line_state_decision,
                line_transition_decision=proactive_line_transition_decision,
            )
        )
        proactive_lifecycle_activation_decision = (
            build_proactive_lifecycle_activation_decision(
                lifecycle_resolution_decision=proactive_lifecycle_resolution_decision
            )
        )
        proactive_lifecycle_settlement_decision = (
            build_proactive_lifecycle_settlement_decision(
                lifecycle_activation_decision=proactive_lifecycle_activation_decision
            )
        )
        proactive_lifecycle_closure_decision = (
            build_proactive_lifecycle_closure_decision(
                lifecycle_settlement_decision=proactive_lifecycle_settlement_decision
            )
        )
        proactive_lifecycle_availability_decision = (
            build_proactive_lifecycle_availability_decision(
                lifecycle_closure_decision=proactive_lifecycle_closure_decision
            )
        )
        proactive_lifecycle_retention_decision = (
            build_proactive_lifecycle_retention_decision(
                lifecycle_availability_decision=proactive_lifecycle_availability_decision
            )
        )
        proactive_lifecycle_eligibility_decision = (
            build_proactive_lifecycle_eligibility_decision(
                lifecycle_retention_decision=proactive_lifecycle_retention_decision
            )
        )
        proactive_lifecycle_candidate_decision = (
            build_proactive_lifecycle_candidate_decision(
                lifecycle_eligibility_decision=proactive_lifecycle_eligibility_decision
            )
        )
        proactive_lifecycle_selectability_decision = (
            build_proactive_lifecycle_selectability_decision(
                lifecycle_candidate_decision=proactive_lifecycle_candidate_decision
            )
        )
        proactive_lifecycle_reentry_decision = (
            build_proactive_lifecycle_reentry_decision(
                lifecycle_selectability_decision=(
                    proactive_lifecycle_selectability_decision
                )
            )
        )
        proactive_lifecycle_reactivation_decision = (
            build_proactive_lifecycle_reactivation_decision(
                lifecycle_reentry_decision=proactive_lifecycle_reentry_decision
            )
        )
        proactive_lifecycle_resumption_decision = (
            build_proactive_lifecycle_resumption_decision(
                lifecycle_reactivation_decision=(
                    proactive_lifecycle_reactivation_decision
                )
            )
        )
        proactive_lifecycle_readiness_decision = (
            build_proactive_lifecycle_readiness_decision(
                lifecycle_resumption_decision=(
                    proactive_lifecycle_resumption_decision
                )
            )
        )
        proactive_lifecycle_arming_decision = (
            build_proactive_lifecycle_arming_decision(
                lifecycle_readiness_decision=proactive_lifecycle_readiness_decision
            )
        )
        proactive_lifecycle_trigger_decision = (
            build_proactive_lifecycle_trigger_decision(
                lifecycle_arming_decision=proactive_lifecycle_arming_decision
            )
        )
        proactive_lifecycle_launch_decision = (
            build_proactive_lifecycle_launch_decision(
                lifecycle_trigger_decision=proactive_lifecycle_trigger_decision
            )
        )
        proactive_lifecycle_handoff_decision = (
            build_proactive_lifecycle_handoff_decision(
                lifecycle_launch_decision=proactive_lifecycle_launch_decision
            )
        )
        proactive_lifecycle_continuation_decision = (
            build_proactive_lifecycle_continuation_decision(
                lifecycle_handoff_decision=proactive_lifecycle_handoff_decision
            )
        )
        proactive_lifecycle_sustainment_decision = (
            build_proactive_lifecycle_sustainment_decision(
                lifecycle_continuation_decision=proactive_lifecycle_continuation_decision
            )
        )
        proactive_lifecycle_stewardship_decision = (
            build_proactive_lifecycle_stewardship_decision(
                lifecycle_sustainment_decision=proactive_lifecycle_sustainment_decision
            )
        )
        proactive_lifecycle_guardianship_decision = (
            build_proactive_lifecycle_guardianship_decision(
                lifecycle_stewardship_decision=proactive_lifecycle_stewardship_decision
            )
        )
        proactive_lifecycle_oversight_decision = (
            build_proactive_lifecycle_oversight_decision(
                lifecycle_guardianship_decision=proactive_lifecycle_guardianship_decision
            )
        )
        proactive_lifecycle_assurance_decision = (
            build_proactive_lifecycle_assurance_decision(
                lifecycle_oversight_decision=proactive_lifecycle_oversight_decision
            )
        )
        proactive_lifecycle_attestation_decision = (
            build_proactive_lifecycle_attestation_decision(
                lifecycle_assurance_decision=proactive_lifecycle_assurance_decision
            )
        )
        proactive_lifecycle_verification_decision = (
            build_proactive_lifecycle_verification_decision(
                lifecycle_attestation_decision=proactive_lifecycle_attestation_decision
            )
        )
        proactive_lifecycle_certification_decision = (
            build_proactive_lifecycle_certification_decision(
                lifecycle_verification_decision=(
                    proactive_lifecycle_verification_decision
                )
            )
        )
        proactive_lifecycle_confirmation_decision = (
            build_proactive_lifecycle_confirmation_decision(
                lifecycle_certification_decision=(
                    proactive_lifecycle_certification_decision
                )
            )
        )
        proactive_lifecycle_ratification_decision = (
            build_proactive_lifecycle_ratification_decision(
                lifecycle_confirmation_decision=(
                    proactive_lifecycle_confirmation_decision
                )
            )
        )
        proactive_lifecycle_endorsement_decision = (
            build_proactive_lifecycle_endorsement_decision(
                lifecycle_ratification_decision=(
                    proactive_lifecycle_ratification_decision
                )
            )
        )
        proactive_lifecycle_authorization_decision = (
            build_proactive_lifecycle_authorization_decision(
                lifecycle_endorsement_decision=(
                    proactive_lifecycle_endorsement_decision
                )
            )
        )
        proactive_lifecycle_enactment_decision = (
            build_proactive_lifecycle_enactment_decision(
                lifecycle_authorization_decision=(
                    proactive_lifecycle_authorization_decision
                )
            )
        )
        proactive_lifecycle_finality_decision = (
            build_proactive_lifecycle_finality_decision(
                lifecycle_enactment_decision=proactive_lifecycle_enactment_decision
            )
        )
        proactive_lifecycle_completion_decision = (
            build_proactive_lifecycle_completion_decision(
                lifecycle_finality_decision=proactive_lifecycle_finality_decision
            )
        )
        proactive_lifecycle_conclusion_decision = (
            build_proactive_lifecycle_conclusion_decision(
                lifecycle_completion_decision=proactive_lifecycle_completion_decision
            )
        )
        proactive_lifecycle_disposition_decision = (
            build_proactive_lifecycle_disposition_decision(
                lifecycle_conclusion_decision=proactive_lifecycle_conclusion_decision
            )
        )
        proactive_lifecycle_standing_decision = (
            build_proactive_lifecycle_standing_decision(
                lifecycle_disposition_decision=proactive_lifecycle_disposition_decision
            )
        )
        proactive_lifecycle_residency_decision = (
            build_proactive_lifecycle_residency_decision(
                lifecycle_standing_decision=proactive_lifecycle_standing_decision
            )
        )
        proactive_lifecycle_tenure_decision = (
            build_proactive_lifecycle_tenure_decision(
                lifecycle_residency_decision=proactive_lifecycle_residency_decision
            )
        )
        proactive_lifecycle_persistence_decision = (
            build_proactive_lifecycle_persistence_decision(
                lifecycle_tenure_decision=proactive_lifecycle_tenure_decision
            )
        )
        proactive_lifecycle_durability_decision = (
            build_proactive_lifecycle_durability_decision(
                lifecycle_persistence_decision=proactive_lifecycle_persistence_decision
            )
        )
        proactive_lifecycle_longevity_decision = (
            build_proactive_lifecycle_longevity_decision(
                lifecycle_durability_decision=proactive_lifecycle_durability_decision
            )
        )
        proactive_lifecycle_legacy_decision = (
            build_proactive_lifecycle_legacy_decision(
                lifecycle_longevity_decision=proactive_lifecycle_longevity_decision
            )
        )
        proactive_lifecycle_heritage_decision = (
            build_proactive_lifecycle_heritage_decision(
                lifecycle_legacy_decision=proactive_lifecycle_legacy_decision
            )
        )
        proactive_lifecycle_lineage_decision = (
            build_proactive_lifecycle_lineage_decision(
                lifecycle_heritage_decision=proactive_lifecycle_heritage_decision
            )
        )
        proactive_lifecycle_ancestry_decision = (
            build_proactive_lifecycle_ancestry_decision(
                lifecycle_lineage_decision=proactive_lifecycle_lineage_decision
            )
        )
        proactive_lifecycle_provenance_decision = (
            build_proactive_lifecycle_provenance_decision(
                lifecycle_ancestry_decision=proactive_lifecycle_ancestry_decision
            )
        )
        proactive_lifecycle_origin_decision = (
            build_proactive_lifecycle_origin_decision(
                lifecycle_provenance_decision=proactive_lifecycle_provenance_decision
            )
        )
        proactive_lifecycle_root_decision = (
            build_proactive_lifecycle_root_decision(
                lifecycle_origin_decision=proactive_lifecycle_origin_decision
            )
        )
        proactive_lifecycle_foundation_decision = (
            build_proactive_lifecycle_foundation_decision(
                lifecycle_root_decision=proactive_lifecycle_root_decision
            )
        )
        proactive_lifecycle_bedrock_decision = (
            build_proactive_lifecycle_bedrock_decision(
                lifecycle_foundation_decision=proactive_lifecycle_foundation_decision
            )
        )
        proactive_lifecycle_substrate_decision = (
            build_proactive_lifecycle_substrate_decision(
                lifecycle_bedrock_decision=proactive_lifecycle_bedrock_decision
            )
        )
        proactive_lifecycle_stratum_decision = (
            build_proactive_lifecycle_stratum_decision(
                lifecycle_substrate_decision=proactive_lifecycle_substrate_decision
            )
        )
        proactive_lifecycle_layer_decision = (
            build_proactive_lifecycle_layer_decision(
                lifecycle_stratum_decision=proactive_lifecycle_stratum_decision
            )
        )

        dispatch_payload = {
            "session_id": session_id,
            "status": "sent",
            "source": source,
            "style": directive.get("style"),
            "ritual_mode": effective_reengagement_plan_model.ritual_mode,
            "delivery_mode": effective_reengagement_plan_model.delivery_mode,
            "strategy_key": effective_reengagement_plan_model.strategy_key,
            "relational_move": effective_reengagement_plan_model.relational_move,
            "pressure_mode": effective_reengagement_plan_model.pressure_mode,
            "autonomy_signal": effective_reengagement_plan_model.autonomy_signal,
            "sequence_objective": effective_reengagement_plan_model.sequence_objective,
            "somatic_action": effective_reengagement_plan_model.somatic_action,
            "content": followup_content,
            "trigger_after_seconds": int(directive.get("trigger_after_seconds") or 0),
            "window_seconds": int(directive.get("window_seconds") or 0),
            "queue_status": (queue_item or {}).get("queue_status", "due"),
            "directive_updated_at": (
                latest_proactive_event.occurred_at.isoformat()
                if latest_proactive_event is not None
                else None
            ),
            "due_at": (queue_item or {}).get("due_at"),
            "base_due_at": (queue_item or {}).get("base_due_at"),
            "expires_at": (queue_item or {}).get("expires_at"),
            "schedule_reason": (queue_item or {}).get("schedule_reason"),
            "opening_hint": directive.get("opening_hint"),
            "rationale": directive.get("rationale"),
            "trigger_conditions": list(directive.get("trigger_conditions") or []),
            "hold_reasons": list(directive.get("hold_reasons") or []),
            "proactive_cadence_key": proactive_cadence_plan_model.cadence_key,
            "proactive_cadence_stage_index": current_stage_index,
            "proactive_cadence_stage_label": current_stage_label,
            "proactive_cadence_stage_count": max(
                1,
                proactive_cadence_plan_model.close_after_stage_index
                or len(proactive_cadence_plan_model.stage_labels)
                or 1,
            ),
            "proactive_scheduling_status": proactive_scheduling_plan_model.status,
            "proactive_scheduling_mode": proactive_scheduling_plan_model.scheduler_mode,
            "proactive_scheduling_min_seconds_since_last_outbound": (
                proactive_scheduling_plan_model.min_seconds_since_last_outbound
            ),
            "proactive_scheduling_first_touch_extra_delay_seconds": (
                proactive_scheduling_plan_model.first_touch_extra_delay_seconds
            ),
            "proactive_scheduling_stage_spacing_mode": (
                proactive_scheduling_plan_model.stage_spacing_mode
            ),
            "proactive_scheduling_low_pressure_guard": (
                proactive_scheduling_plan_model.low_pressure_guard
            ),
            "proactive_guardrail_key": proactive_guardrail_plan.get("guardrail_key"),
            "proactive_guardrail_max_dispatch_count": int(
                proactive_guardrail_plan.get("max_dispatch_count") or 0
            ),
            "proactive_guardrail_stage_min_seconds_since_last_user": int(
                (current_stage_guardrail or {}).get(
                    "min_seconds_since_last_user",
                    0,
                )
                or 0
            ),
            "proactive_guardrail_stage_min_seconds_since_last_dispatch": int(
                (current_stage_guardrail or {}).get(
                    "min_seconds_since_last_dispatch",
                    0,
                )
                or 0
            ),
            "proactive_guardrail_stage_on_guardrail_hit": (
                (current_stage_guardrail or {}).get("on_guardrail_hit")
            ),
            "proactive_guardrail_hard_stop_conditions": list(
                proactive_guardrail_plan.get("hard_stop_conditions") or []
            ),
            "proactive_guardrail_rationale": proactive_guardrail_plan.get("rationale"),
            "proactive_orchestration_key": proactive_orchestration_plan.get(
                "orchestration_key"
            ),
            "proactive_orchestration_stage_objective": (
                effective_stage_directive.get("objective")
            ),
            "proactive_orchestration_stage_delivery_mode": (
                effective_stage_directive.get("delivery_mode")
            ),
            "proactive_orchestration_stage_question_mode": (
                effective_stage_directive.get("question_mode")
            ),
            "proactive_orchestration_stage_autonomy_mode": (
                effective_stage_directive.get("autonomy_mode")
            ),
            "proactive_orchestration_stage_closing_style": (
                effective_stage_directive.get("closing_style")
            ),
            "proactive_stage_refresh_key": proactive_stage_refresh_plan.refresh_key,
            "proactive_stage_refresh_window_status": (
                proactive_stage_refresh_plan.dispatch_window_status
            ),
            "proactive_stage_refresh_changed": proactive_stage_refresh_plan.changed,
            "proactive_stage_refresh_notes": list(
                proactive_stage_refresh_plan.refresh_notes
            ),
            "proactive_stage_replan_key": (
                proactive_stage_replan_assessment.replan_key
            ),
            "proactive_stage_replan_changed": (
                proactive_stage_replan_assessment.changed
            ),
            "proactive_stage_replan_strategy_key": (
                proactive_stage_replan_assessment.selected_strategy_key
            ),
            "proactive_stage_replan_ritual_mode": (
                proactive_stage_replan_assessment.selected_ritual_mode
            ),
            "proactive_stage_replan_pressure_mode": (
                proactive_stage_replan_assessment.selected_pressure_mode
            ),
            "proactive_stage_replan_autonomy_signal": (
                proactive_stage_replan_assessment.selected_autonomy_signal
            ),
            "proactive_stage_replan_notes": list(
                proactive_stage_replan_assessment.replan_notes
            ),
            "proactive_dispatch_feedback_key": (
                proactive_dispatch_feedback_assessment.feedback_key
            ),
            "proactive_dispatch_feedback_changed": (
                proactive_dispatch_feedback_assessment.changed
            ),
            "proactive_dispatch_feedback_dispatch_count": (
                proactive_dispatch_feedback_assessment.dispatch_count
            ),
            "proactive_dispatch_feedback_gate_defer_count": (
                proactive_dispatch_feedback_assessment.gate_defer_count
            ),
            "proactive_dispatch_feedback_strategy_key": (
                proactive_dispatch_feedback_assessment.selected_strategy_key
            ),
            "proactive_dispatch_feedback_pressure_mode": (
                proactive_dispatch_feedback_assessment.selected_pressure_mode
            ),
            "proactive_dispatch_feedback_autonomy_signal": (
                proactive_dispatch_feedback_assessment.selected_autonomy_signal
            ),
            "proactive_dispatch_feedback_delivery_mode": (
                proactive_dispatch_feedback_assessment.selected_delivery_mode
            ),
            "proactive_dispatch_feedback_sequence_objective": (
                proactive_dispatch_feedback_assessment.selected_sequence_objective
            ),
            "proactive_dispatch_feedback_prior_stage_label": (
                proactive_dispatch_feedback_assessment.prior_stage_label
            ),
            "proactive_dispatch_feedback_notes": list(
                proactive_dispatch_feedback_assessment.feedback_notes
            ),
            "proactive_stage_controller_key": (
                proactive_stage_controller_decision.controller_key
            ),
            "proactive_stage_controller_decision": (
                proactive_stage_controller_decision.decision
            ),
            "proactive_stage_controller_changed": (
                proactive_stage_controller_decision.changed
            ),
            "proactive_stage_controller_target_stage_label": (
                proactive_stage_controller_decision.target_stage_label
            ),
            "proactive_stage_controller_additional_delay_seconds": (
                proactive_stage_controller_decision.additional_delay_seconds
            ),
            "proactive_stage_controller_strategy_key": (
                proactive_stage_controller_decision.selected_strategy_key
            ),
            "proactive_stage_controller_pressure_mode": (
                proactive_stage_controller_decision.selected_pressure_mode
            ),
            "proactive_stage_controller_autonomy_signal": (
                proactive_stage_controller_decision.selected_autonomy_signal
            ),
            "proactive_stage_controller_delivery_mode": (
                proactive_stage_controller_decision.selected_delivery_mode
            ),
            "proactive_stage_controller_notes": list(
                proactive_stage_controller_decision.controller_notes
            ),
            "proactive_stage_controller_applied": prior_stage_controller_applied,
            "proactive_stage_controller_applied_key": (
                prior_stage_controller_decision.controller_key
                if prior_stage_controller_applied
                else None
            ),
            "proactive_line_controller_key": (
                proactive_line_controller_decision.controller_key
            ),
            "proactive_line_controller_line_state": (
                proactive_line_controller_decision.line_state
            ),
            "proactive_line_controller_decision": (
                proactive_line_controller_decision.decision
            ),
            "proactive_line_controller_changed": (
                proactive_line_controller_decision.changed
            ),
            "proactive_line_controller_affected_stage_labels": list(
                proactive_line_controller_decision.affected_stage_labels
            ),
            "proactive_line_controller_additional_delay_seconds": (
                proactive_line_controller_decision.additional_delay_seconds
            ),
            "proactive_line_controller_pressure_mode": (
                proactive_line_controller_decision.selected_pressure_mode
            ),
            "proactive_line_controller_autonomy_signal": (
                proactive_line_controller_decision.selected_autonomy_signal
            ),
            "proactive_line_controller_delivery_mode": (
                proactive_line_controller_decision.selected_delivery_mode
            ),
            "proactive_line_controller_notes": list(
                proactive_line_controller_decision.controller_notes
            ),
            "proactive_line_controller_applied": prior_line_controller_applied,
            "proactive_line_controller_applied_key": (
                prior_line_controller_decision.controller_key
                if prior_line_controller_applied
                else None
            ),
            "proactive_dispatch_gate_key": proactive_dispatch_gate_decision.gate_key,
            "proactive_dispatch_gate_decision": (
                proactive_dispatch_gate_decision.decision
            ),
            "proactive_dispatch_gate_changed": (
                proactive_dispatch_gate_decision.changed
            ),
            "proactive_dispatch_gate_retry_after_seconds": (
                proactive_dispatch_gate_decision.retry_after_seconds
            ),
            "proactive_dispatch_gate_strategy_key": (
                proactive_dispatch_gate_decision.selected_strategy_key
            ),
            "proactive_dispatch_gate_pressure_mode": (
                proactive_dispatch_gate_decision.selected_pressure_mode
            ),
            "proactive_dispatch_gate_autonomy_signal": (
                proactive_dispatch_gate_decision.selected_autonomy_signal
            ),
            "proactive_dispatch_gate_notes": list(
                proactive_dispatch_gate_decision.gate_notes
            ),
            "proactive_dispatch_envelope_key": (
                proactive_dispatch_envelope_decision.envelope_key
            ),
            "proactive_dispatch_envelope_decision": (
                proactive_dispatch_envelope_decision.decision
            ),
            "proactive_dispatch_envelope_reengagement_delivery_mode": (
                proactive_dispatch_envelope_decision.selected_reengagement_delivery_mode
            ),
            "proactive_dispatch_envelope_stage_delivery_mode": (
                proactive_dispatch_envelope_decision.selected_stage_delivery_mode
            ),
            "proactive_dispatch_envelope_source_count": len(
                proactive_dispatch_envelope_decision.active_sources
            ),
            "proactive_dispatch_envelope_sources": list(
                proactive_dispatch_envelope_decision.active_sources
            ),
            "proactive_dispatch_envelope_notes": list(
                proactive_dispatch_envelope_decision.envelope_notes
            ),
            "proactive_stage_state_key": proactive_stage_state_decision.state_key,
            "proactive_stage_state_mode": proactive_stage_state_decision.state_mode,
            "proactive_stage_state_source": proactive_stage_state_decision.primary_source,
            "proactive_stage_state_queue_status": (
                proactive_stage_state_decision.queue_status
            ),
            "proactive_stage_transition_key": (
                proactive_stage_transition_decision.transition_key
            ),
            "proactive_stage_transition_mode": (
                proactive_stage_transition_decision.transition_mode
            ),
            "proactive_stage_transition_queue_hint": (
                proactive_stage_transition_decision.next_queue_status_hint
            ),
            "proactive_stage_transition_source": (
                proactive_stage_transition_decision.primary_source
            ),
            "proactive_stage_machine_key": proactive_stage_machine_decision.machine_key,
            "proactive_stage_machine_mode": proactive_stage_machine_decision.machine_mode,
            "proactive_stage_machine_lifecycle": (
                proactive_stage_machine_decision.lifecycle_mode
            ),
            "proactive_stage_machine_actionability": (
                proactive_stage_machine_decision.actionability
            ),
            "proactive_line_state_key": proactive_line_state_decision.line_key,
            "proactive_line_state_mode": proactive_line_state_decision.line_state,
            "proactive_line_state_lifecycle": (
                proactive_line_state_decision.lifecycle_mode
            ),
            "proactive_line_state_actionability": (
                proactive_line_state_decision.actionability
            ),
            "proactive_line_transition_key": (
                proactive_line_transition_decision.transition_key
            ),
            "proactive_line_transition_mode": (
                proactive_line_transition_decision.transition_mode
            ),
            "proactive_line_transition_exit_mode": (
                proactive_line_transition_decision.line_exit_mode
            ),
            "proactive_line_machine_key": proactive_line_machine_decision.machine_key,
            "proactive_line_machine_mode": proactive_line_machine_decision.machine_mode,
            "proactive_line_machine_lifecycle": (
                proactive_line_machine_decision.lifecycle_mode
            ),
            "proactive_line_machine_actionability": (
                proactive_line_machine_decision.actionability
            ),
            "proactive_lifecycle_state_key": (
                proactive_lifecycle_state_decision.state_key
            ),
            "proactive_lifecycle_state_mode": (
                proactive_lifecycle_state_decision.state_mode
            ),
            "proactive_lifecycle_state_lifecycle": (
                proactive_lifecycle_state_decision.lifecycle_mode
            ),
            "proactive_lifecycle_state_actionability": (
                proactive_lifecycle_state_decision.actionability
            ),
            "proactive_lifecycle_transition_key": (
                proactive_lifecycle_transition_decision.transition_key
            ),
            "proactive_lifecycle_transition_mode": (
                proactive_lifecycle_transition_decision.transition_mode
            ),
            "proactive_lifecycle_transition_exit_mode": (
                proactive_lifecycle_transition_decision.lifecycle_exit_mode
            ),
            "proactive_lifecycle_machine_key": (
                proactive_lifecycle_machine_decision.machine_key
            ),
            "proactive_lifecycle_machine_mode": (
                proactive_lifecycle_machine_decision.machine_mode
            ),
            "proactive_lifecycle_machine_lifecycle": (
                proactive_lifecycle_machine_decision.lifecycle_mode
            ),
            "proactive_lifecycle_machine_actionability": (
                proactive_lifecycle_machine_decision.actionability
            ),
            "proactive_lifecycle_controller_key": (
                proactive_lifecycle_controller_decision.controller_key
            ),
            "proactive_lifecycle_controller_state": (
                proactive_lifecycle_controller_decision.lifecycle_state
            ),
            "proactive_lifecycle_controller_decision": (
                proactive_lifecycle_controller_decision.decision
            ),
            "proactive_lifecycle_controller_delay_seconds": (
                proactive_lifecycle_controller_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_envelope_key": (
                proactive_lifecycle_envelope_decision.envelope_key
            ),
            "proactive_lifecycle_envelope_state": (
                proactive_lifecycle_envelope_decision.lifecycle_state
            ),
            "proactive_lifecycle_envelope_mode": (
                proactive_lifecycle_envelope_decision.envelope_mode
            ),
            "proactive_lifecycle_envelope_decision": (
                proactive_lifecycle_envelope_decision.decision
            ),
            "proactive_lifecycle_envelope_actionability": (
                proactive_lifecycle_envelope_decision.actionability
            ),
            "proactive_lifecycle_envelope_delay_seconds": (
                proactive_lifecycle_envelope_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_scheduler_key": (
                proactive_lifecycle_scheduler_decision.scheduler_key
            ),
            "proactive_lifecycle_scheduler_state": (
                proactive_lifecycle_scheduler_decision.lifecycle_state
            ),
            "proactive_lifecycle_scheduler_mode": (
                proactive_lifecycle_scheduler_decision.scheduler_mode
            ),
            "proactive_lifecycle_scheduler_decision": (
                proactive_lifecycle_scheduler_decision.decision
            ),
            "proactive_lifecycle_scheduler_actionability": (
                proactive_lifecycle_scheduler_decision.actionability
            ),
            "proactive_lifecycle_scheduler_queue_status": (
                proactive_lifecycle_scheduler_decision.queue_status_hint
            ),
            "proactive_lifecycle_scheduler_delay_seconds": (
                proactive_lifecycle_scheduler_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_window_key": (
                proactive_lifecycle_window_decision.window_key
            ),
            "proactive_lifecycle_window_state": (
                proactive_lifecycle_window_decision.lifecycle_state
            ),
            "proactive_lifecycle_window_mode": (
                proactive_lifecycle_window_decision.window_mode
            ),
            "proactive_lifecycle_window_decision": (
                proactive_lifecycle_window_decision.decision
            ),
            "proactive_lifecycle_window_queue_status": (
                proactive_lifecycle_window_decision.queue_status
            ),
            "proactive_lifecycle_window_delay_seconds": (
                proactive_lifecycle_window_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_queue_key": (
                proactive_lifecycle_queue_decision.queue_key
            ),
            "proactive_lifecycle_queue_state": (
                proactive_lifecycle_queue_decision.lifecycle_state
            ),
            "proactive_lifecycle_queue_mode": (
                proactive_lifecycle_queue_decision.queue_mode
            ),
            "proactive_lifecycle_queue_decision": (
                proactive_lifecycle_queue_decision.decision
            ),
            "proactive_lifecycle_queue_status": (
                proactive_lifecycle_queue_decision.queue_status
            ),
            "proactive_lifecycle_queue_delay_seconds": (
                proactive_lifecycle_queue_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_dispatch_key": (
                proactive_lifecycle_dispatch_decision.dispatch_key
            ),
            "proactive_lifecycle_dispatch_state": (
                proactive_lifecycle_dispatch_decision.lifecycle_state
            ),
            "proactive_lifecycle_dispatch_mode": (
                proactive_lifecycle_dispatch_decision.dispatch_mode
            ),
            "proactive_lifecycle_dispatch_decision": (
                proactive_lifecycle_dispatch_decision.decision
            ),
            "proactive_lifecycle_dispatch_actionability": (
                proactive_lifecycle_dispatch_decision.actionability
            ),
            "proactive_lifecycle_dispatch_delay_seconds": (
                proactive_lifecycle_dispatch_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_outcome_key": (
                proactive_lifecycle_outcome_decision.outcome_key
            ),
            "proactive_lifecycle_outcome_status": (
                proactive_lifecycle_outcome_decision.status
            ),
            "proactive_lifecycle_outcome_mode": (
                proactive_lifecycle_outcome_decision.outcome_mode
            ),
            "proactive_lifecycle_outcome_decision": (
                proactive_lifecycle_outcome_decision.decision
            ),
            "proactive_lifecycle_outcome_actionability": (
                proactive_lifecycle_outcome_decision.actionability
            ),
            "proactive_lifecycle_outcome_message_event_count": (
                proactive_lifecycle_outcome_decision.message_event_count
            ),
            "proactive_lifecycle_resolution_key": (
                proactive_lifecycle_resolution_decision.resolution_key
            ),
            "proactive_lifecycle_resolution_status": (
                proactive_lifecycle_resolution_decision.status
            ),
            "proactive_lifecycle_resolution_mode": (
                proactive_lifecycle_resolution_decision.resolution_mode
            ),
            "proactive_lifecycle_resolution_decision": (
                proactive_lifecycle_resolution_decision.decision
            ),
            "proactive_lifecycle_resolution_actionability": (
                proactive_lifecycle_resolution_decision.actionability
            ),
            "proactive_lifecycle_resolution_queue_override_status": (
                proactive_lifecycle_resolution_decision.queue_override_status
            ),
            "proactive_lifecycle_resolution_remaining_stage_count": (
                proactive_lifecycle_resolution_decision.remaining_stage_count
            ),
            "proactive_lifecycle_activation_key": (
                proactive_lifecycle_activation_decision.activation_key
            ),
            "proactive_lifecycle_activation_status": (
                proactive_lifecycle_activation_decision.status
            ),
            "proactive_lifecycle_activation_mode": (
                proactive_lifecycle_activation_decision.activation_mode
            ),
            "proactive_lifecycle_activation_decision": (
                proactive_lifecycle_activation_decision.decision
            ),
            "proactive_lifecycle_activation_actionability": (
                proactive_lifecycle_activation_decision.actionability
            ),
            "proactive_lifecycle_activation_active_stage_label": (
                proactive_lifecycle_activation_decision.active_stage_label
            ),
            "proactive_lifecycle_activation_queue_override_status": (
                proactive_lifecycle_activation_decision.queue_override_status
            ),
            "proactive_lifecycle_settlement_key": (
                proactive_lifecycle_settlement_decision.settlement_key
            ),
            "proactive_lifecycle_settlement_status": (
                proactive_lifecycle_settlement_decision.status
            ),
            "proactive_lifecycle_settlement_mode": (
                proactive_lifecycle_settlement_decision.settlement_mode
            ),
            "proactive_lifecycle_settlement_decision": (
                proactive_lifecycle_settlement_decision.decision
            ),
            "proactive_lifecycle_settlement_actionability": (
                proactive_lifecycle_settlement_decision.actionability
            ),
            "proactive_lifecycle_settlement_active_stage_label": (
                proactive_lifecycle_settlement_decision.active_stage_label
            ),
            "proactive_lifecycle_settlement_queue_override_status": (
                proactive_lifecycle_settlement_decision.queue_override_status
            ),
            "proactive_lifecycle_closure_key": (
                proactive_lifecycle_closure_decision.closure_key
            ),
            "proactive_lifecycle_closure_status": (
                proactive_lifecycle_closure_decision.status
            ),
            "proactive_lifecycle_closure_mode": (
                proactive_lifecycle_closure_decision.closure_mode
            ),
            "proactive_lifecycle_closure_decision": (
                proactive_lifecycle_closure_decision.decision
            ),
            "proactive_lifecycle_closure_actionability": (
                proactive_lifecycle_closure_decision.actionability
            ),
            "proactive_lifecycle_closure_active_stage_label": (
                proactive_lifecycle_closure_decision.active_stage_label
            ),
            "proactive_lifecycle_closure_queue_override_status": (
                proactive_lifecycle_closure_decision.queue_override_status
            ),
            "proactive_lifecycle_availability_key": (
                proactive_lifecycle_availability_decision.availability_key
            ),
            "proactive_lifecycle_availability_status": (
                proactive_lifecycle_availability_decision.status
            ),
            "proactive_lifecycle_availability_mode": (
                proactive_lifecycle_availability_decision.availability_mode
            ),
            "proactive_lifecycle_availability_decision": (
                proactive_lifecycle_availability_decision.decision
            ),
            "proactive_lifecycle_availability_actionability": (
                proactive_lifecycle_availability_decision.actionability
            ),
            "proactive_lifecycle_availability_active_stage_label": (
                proactive_lifecycle_availability_decision.active_stage_label
            ),
            "proactive_lifecycle_availability_queue_override_status": (
                proactive_lifecycle_availability_decision.queue_override_status
            ),
            "proactive_lifecycle_retention_key": (
                proactive_lifecycle_retention_decision.retention_key
            ),
            "proactive_lifecycle_retention_status": (
                proactive_lifecycle_retention_decision.status
            ),
            "proactive_lifecycle_retention_mode": (
                proactive_lifecycle_retention_decision.retention_mode
            ),
            "proactive_lifecycle_retention_decision": (
                proactive_lifecycle_retention_decision.decision
            ),
            "proactive_lifecycle_retention_actionability": (
                proactive_lifecycle_retention_decision.actionability
            ),
            "proactive_lifecycle_retention_active_stage_label": (
                proactive_lifecycle_retention_decision.active_stage_label
            ),
            "proactive_lifecycle_retention_queue_override_status": (
                proactive_lifecycle_retention_decision.queue_override_status
            ),
            "proactive_lifecycle_eligibility_key": (
                proactive_lifecycle_eligibility_decision.eligibility_key
            ),
            "proactive_lifecycle_eligibility_status": (
                proactive_lifecycle_eligibility_decision.status
            ),
            "proactive_lifecycle_eligibility_mode": (
                proactive_lifecycle_eligibility_decision.eligibility_mode
            ),
            "proactive_lifecycle_eligibility_decision": (
                proactive_lifecycle_eligibility_decision.decision
            ),
            "proactive_lifecycle_eligibility_actionability": (
                proactive_lifecycle_eligibility_decision.actionability
            ),
            "proactive_lifecycle_eligibility_active_stage_label": (
                proactive_lifecycle_eligibility_decision.active_stage_label
            ),
            "proactive_lifecycle_eligibility_queue_override_status": (
                proactive_lifecycle_eligibility_decision.queue_override_status
            ),
            "proactive_lifecycle_candidate_key": (
                proactive_lifecycle_candidate_decision.candidate_key
            ),
            "proactive_lifecycle_candidate_status": (
                proactive_lifecycle_candidate_decision.status
            ),
            "proactive_lifecycle_candidate_mode": (
                proactive_lifecycle_candidate_decision.candidate_mode
            ),
            "proactive_lifecycle_candidate_decision": (
                proactive_lifecycle_candidate_decision.decision
            ),
            "proactive_lifecycle_candidate_actionability": (
                proactive_lifecycle_candidate_decision.actionability
            ),
            "proactive_lifecycle_candidate_active_stage_label": (
                proactive_lifecycle_candidate_decision.active_stage_label
            ),
            "proactive_lifecycle_candidate_queue_override_status": (
                proactive_lifecycle_candidate_decision.queue_override_status
            ),
            "proactive_lifecycle_selectability_key": (
                proactive_lifecycle_selectability_decision.selectability_key
            ),
            "proactive_lifecycle_selectability_status": (
                proactive_lifecycle_selectability_decision.status
            ),
            "proactive_lifecycle_selectability_mode": (
                proactive_lifecycle_selectability_decision.selectability_mode
            ),
            "proactive_lifecycle_selectability_decision": (
                proactive_lifecycle_selectability_decision.decision
            ),
            "proactive_lifecycle_selectability_actionability": (
                proactive_lifecycle_selectability_decision.actionability
            ),
            "proactive_lifecycle_selectability_active_stage_label": (
                proactive_lifecycle_selectability_decision.active_stage_label
            ),
            "proactive_lifecycle_selectability_queue_override_status": (
                proactive_lifecycle_selectability_decision.queue_override_status
            ),
            "proactive_lifecycle_reentry_key": (
                proactive_lifecycle_reentry_decision.reentry_key
            ),
            "proactive_lifecycle_reentry_status": (
                proactive_lifecycle_reentry_decision.status
            ),
            "proactive_lifecycle_reentry_mode": (
                proactive_lifecycle_reentry_decision.reentry_mode
            ),
            "proactive_lifecycle_reentry_decision": (
                proactive_lifecycle_reentry_decision.decision
            ),
            "proactive_lifecycle_reentry_actionability": (
                proactive_lifecycle_reentry_decision.actionability
            ),
            "proactive_lifecycle_reentry_active_stage_label": (
                proactive_lifecycle_reentry_decision.active_stage_label
            ),
            "proactive_lifecycle_reentry_queue_override_status": (
                proactive_lifecycle_reentry_decision.queue_override_status
            ),
            "proactive_lifecycle_reactivation_key": (
                proactive_lifecycle_reactivation_decision.reactivation_key
            ),
            "proactive_lifecycle_reactivation_status": (
                proactive_lifecycle_reactivation_decision.status
            ),
            "proactive_lifecycle_reactivation_mode": (
                proactive_lifecycle_reactivation_decision.reactivation_mode
            ),
            "proactive_lifecycle_reactivation_decision": (
                proactive_lifecycle_reactivation_decision.decision
            ),
            "proactive_lifecycle_reactivation_actionability": (
                proactive_lifecycle_reactivation_decision.actionability
            ),
            "proactive_lifecycle_reactivation_active_stage_label": (
                proactive_lifecycle_reactivation_decision.active_stage_label
            ),
            "proactive_lifecycle_reactivation_queue_override_status": (
                proactive_lifecycle_reactivation_decision.queue_override_status
            ),
            "proactive_lifecycle_resumption_key": (
                proactive_lifecycle_resumption_decision.resumption_key
            ),
            "proactive_lifecycle_resumption_status": (
                proactive_lifecycle_resumption_decision.status
            ),
            "proactive_lifecycle_resumption_mode": (
                proactive_lifecycle_resumption_decision.resumption_mode
            ),
            "proactive_lifecycle_resumption_decision": (
                proactive_lifecycle_resumption_decision.decision
            ),
            "proactive_lifecycle_resumption_actionability": (
                proactive_lifecycle_resumption_decision.actionability
            ),
            "proactive_lifecycle_resumption_active_stage_label": (
                proactive_lifecycle_resumption_decision.active_stage_label
            ),
            "proactive_lifecycle_resumption_queue_override_status": (
                proactive_lifecycle_resumption_decision.queue_override_status
            ),
            "proactive_lifecycle_readiness_key": (
                proactive_lifecycle_readiness_decision.readiness_key
            ),
            "proactive_lifecycle_readiness_status": (
                proactive_lifecycle_readiness_decision.status
            ),
            "proactive_lifecycle_readiness_mode": (
                proactive_lifecycle_readiness_decision.readiness_mode
            ),
            "proactive_lifecycle_readiness_decision": (
                proactive_lifecycle_readiness_decision.decision
            ),
            "proactive_lifecycle_readiness_actionability": (
                proactive_lifecycle_readiness_decision.actionability
            ),
            "proactive_lifecycle_readiness_active_stage_label": (
                proactive_lifecycle_readiness_decision.active_stage_label
            ),
            "proactive_lifecycle_readiness_queue_override_status": (
                proactive_lifecycle_readiness_decision.queue_override_status
            ),
            "proactive_lifecycle_arming_key": (
                proactive_lifecycle_arming_decision.arming_key
            ),
            "proactive_lifecycle_arming_status": (
                proactive_lifecycle_arming_decision.status
            ),
            "proactive_lifecycle_arming_mode": (
                proactive_lifecycle_arming_decision.arming_mode
            ),
            "proactive_lifecycle_arming_decision": (
                proactive_lifecycle_arming_decision.decision
            ),
            "proactive_lifecycle_arming_actionability": (
                proactive_lifecycle_arming_decision.actionability
            ),
            "proactive_lifecycle_arming_active_stage_label": (
                proactive_lifecycle_arming_decision.active_stage_label
            ),
            "proactive_lifecycle_arming_queue_override_status": (
                proactive_lifecycle_arming_decision.queue_override_status
            ),
            "proactive_lifecycle_trigger_key": (
                proactive_lifecycle_trigger_decision.trigger_key
            ),
            "proactive_lifecycle_trigger_status": (
                proactive_lifecycle_trigger_decision.status
            ),
            "proactive_lifecycle_trigger_mode": (
                proactive_lifecycle_trigger_decision.trigger_mode
            ),
            "proactive_lifecycle_trigger_decision": (
                proactive_lifecycle_trigger_decision.decision
            ),
            "proactive_lifecycle_trigger_actionability": (
                proactive_lifecycle_trigger_decision.actionability
            ),
            "proactive_lifecycle_trigger_active_stage_label": (
                proactive_lifecycle_trigger_decision.active_stage_label
            ),
            "proactive_lifecycle_trigger_queue_override_status": (
                proactive_lifecycle_trigger_decision.queue_override_status
            ),
            "proactive_lifecycle_launch_key": (
                proactive_lifecycle_launch_decision.launch_key
            ),
            "proactive_lifecycle_launch_status": (
                proactive_lifecycle_launch_decision.status
            ),
            "proactive_lifecycle_launch_mode": (
                proactive_lifecycle_launch_decision.launch_mode
            ),
            "proactive_lifecycle_launch_decision": (
                proactive_lifecycle_launch_decision.decision
            ),
            "proactive_lifecycle_launch_actionability": (
                proactive_lifecycle_launch_decision.actionability
            ),
            "proactive_lifecycle_launch_active_stage_label": (
                proactive_lifecycle_launch_decision.active_stage_label
            ),
            "proactive_lifecycle_launch_queue_override_status": (
                proactive_lifecycle_launch_decision.queue_override_status
            ),
            "proactive_lifecycle_handoff_key": (
                proactive_lifecycle_handoff_decision.handoff_key
            ),
            "proactive_lifecycle_handoff_status": (
                proactive_lifecycle_handoff_decision.status
            ),
            "proactive_lifecycle_handoff_mode": (
                proactive_lifecycle_handoff_decision.handoff_mode
            ),
            "proactive_lifecycle_handoff_decision": (
                proactive_lifecycle_handoff_decision.decision
            ),
            "proactive_lifecycle_handoff_actionability": (
                proactive_lifecycle_handoff_decision.actionability
            ),
            "proactive_lifecycle_handoff_active_stage_label": (
                proactive_lifecycle_handoff_decision.active_stage_label
            ),
            "proactive_lifecycle_handoff_queue_override_status": (
                proactive_lifecycle_handoff_decision.queue_override_status
            ),
            "proactive_lifecycle_continuation_key": (
                proactive_lifecycle_continuation_decision.continuation_key
            ),
            "proactive_lifecycle_continuation_status": (
                proactive_lifecycle_continuation_decision.status
            ),
            "proactive_lifecycle_continuation_mode": (
                proactive_lifecycle_continuation_decision.continuation_mode
            ),
            "proactive_lifecycle_continuation_decision": (
                proactive_lifecycle_continuation_decision.decision
            ),
            "proactive_lifecycle_continuation_actionability": (
                proactive_lifecycle_continuation_decision.actionability
            ),
            "proactive_lifecycle_continuation_active_stage_label": (
                proactive_lifecycle_continuation_decision.active_stage_label
            ),
            "proactive_lifecycle_continuation_queue_override_status": (
                proactive_lifecycle_continuation_decision.queue_override_status
            ),
            "proactive_lifecycle_sustainment_key": (
                proactive_lifecycle_sustainment_decision.sustainment_key
            ),
            "proactive_lifecycle_sustainment_status": (
                proactive_lifecycle_sustainment_decision.status
            ),
            "proactive_lifecycle_sustainment_mode": (
                proactive_lifecycle_sustainment_decision.sustainment_mode
            ),
            "proactive_lifecycle_sustainment_decision": (
                proactive_lifecycle_sustainment_decision.decision
            ),
            "proactive_lifecycle_sustainment_actionability": (
                proactive_lifecycle_sustainment_decision.actionability
            ),
            "proactive_lifecycle_sustainment_active_stage_label": (
                proactive_lifecycle_sustainment_decision.active_stage_label
            ),
            "proactive_lifecycle_sustainment_queue_override_status": (
                proactive_lifecycle_sustainment_decision.queue_override_status
            ),
            "proactive_lifecycle_stewardship_key": (
                proactive_lifecycle_stewardship_decision.stewardship_key
            ),
            "proactive_lifecycle_stewardship_status": (
                proactive_lifecycle_stewardship_decision.status
            ),
            "proactive_lifecycle_stewardship_mode": (
                proactive_lifecycle_stewardship_decision.stewardship_mode
            ),
            "proactive_lifecycle_stewardship_decision": (
                proactive_lifecycle_stewardship_decision.decision
            ),
            "proactive_lifecycle_stewardship_actionability": (
                proactive_lifecycle_stewardship_decision.actionability
            ),
            "proactive_lifecycle_stewardship_active_stage_label": (
                proactive_lifecycle_stewardship_decision.active_stage_label
            ),
            "proactive_lifecycle_stewardship_queue_override_status": (
                proactive_lifecycle_stewardship_decision.queue_override_status
            ),
            "proactive_lifecycle_guardianship_key": (
                proactive_lifecycle_guardianship_decision.guardianship_key
            ),
            "proactive_lifecycle_guardianship_status": (
                proactive_lifecycle_guardianship_decision.status
            ),
            "proactive_lifecycle_guardianship_mode": (
                proactive_lifecycle_guardianship_decision.guardianship_mode
            ),
            "proactive_lifecycle_guardianship_decision": (
                proactive_lifecycle_guardianship_decision.decision
            ),
            "proactive_lifecycle_guardianship_actionability": (
                proactive_lifecycle_guardianship_decision.actionability
            ),
            "proactive_lifecycle_guardianship_active_stage_label": (
                proactive_lifecycle_guardianship_decision.active_stage_label
            ),
            "proactive_lifecycle_guardianship_queue_override_status": (
                proactive_lifecycle_guardianship_decision.queue_override_status
            ),
            "proactive_lifecycle_oversight_key": (
                proactive_lifecycle_oversight_decision.oversight_key
            ),
            "proactive_lifecycle_oversight_status": (
                proactive_lifecycle_oversight_decision.status
            ),
            "proactive_lifecycle_oversight_mode": (
                proactive_lifecycle_oversight_decision.oversight_mode
            ),
            "proactive_lifecycle_oversight_decision": (
                proactive_lifecycle_oversight_decision.decision
            ),
            "proactive_lifecycle_oversight_actionability": (
                proactive_lifecycle_oversight_decision.actionability
            ),
            "proactive_lifecycle_oversight_active_stage_label": (
                proactive_lifecycle_oversight_decision.active_stage_label
            ),
            "proactive_lifecycle_oversight_queue_override_status": (
                proactive_lifecycle_oversight_decision.queue_override_status
            ),
            "proactive_lifecycle_assurance_key": (
                proactive_lifecycle_assurance_decision.assurance_key
            ),
            "proactive_lifecycle_assurance_status": (
                proactive_lifecycle_assurance_decision.status
            ),
            "proactive_lifecycle_assurance_mode": (
                proactive_lifecycle_assurance_decision.assurance_mode
            ),
            "proactive_lifecycle_assurance_decision": (
                proactive_lifecycle_assurance_decision.decision
            ),
            "proactive_lifecycle_assurance_actionability": (
                proactive_lifecycle_assurance_decision.actionability
            ),
            "proactive_lifecycle_assurance_active_stage_label": (
                proactive_lifecycle_assurance_decision.active_stage_label
            ),
            "proactive_lifecycle_assurance_queue_override_status": (
                proactive_lifecycle_assurance_decision.queue_override_status
            ),
            "proactive_lifecycle_attestation_key": (
                proactive_lifecycle_attestation_decision.attestation_key
            ),
            "proactive_lifecycle_attestation_status": (
                proactive_lifecycle_attestation_decision.status
            ),
            "proactive_lifecycle_attestation_mode": (
                proactive_lifecycle_attestation_decision.attestation_mode
            ),
            "proactive_lifecycle_attestation_decision": (
                proactive_lifecycle_attestation_decision.decision
            ),
            "proactive_lifecycle_attestation_actionability": (
                proactive_lifecycle_attestation_decision.actionability
            ),
            "proactive_lifecycle_attestation_active_stage_label": (
                proactive_lifecycle_attestation_decision.active_stage_label
            ),
            "proactive_lifecycle_attestation_queue_override_status": (
                proactive_lifecycle_attestation_decision.queue_override_status
            ),
            "proactive_lifecycle_verification_key": (
                proactive_lifecycle_verification_decision.verification_key
            ),
            "proactive_lifecycle_verification_status": (
                proactive_lifecycle_verification_decision.status
            ),
            "proactive_lifecycle_verification_mode": (
                proactive_lifecycle_verification_decision.verification_mode
            ),
            "proactive_lifecycle_verification_decision": (
                proactive_lifecycle_verification_decision.decision
            ),
            "proactive_lifecycle_verification_actionability": (
                proactive_lifecycle_verification_decision.actionability
            ),
            "proactive_lifecycle_verification_active_stage_label": (
                proactive_lifecycle_verification_decision.active_stage_label
            ),
            "proactive_lifecycle_verification_queue_override_status": (
                proactive_lifecycle_verification_decision.queue_override_status
            ),
            "proactive_lifecycle_certification_key": (
                proactive_lifecycle_certification_decision.certification_key
            ),
            "proactive_lifecycle_certification_status": (
                proactive_lifecycle_certification_decision.status
            ),
            "proactive_lifecycle_certification_mode": (
                proactive_lifecycle_certification_decision.certification_mode
            ),
            "proactive_lifecycle_certification_decision": (
                proactive_lifecycle_certification_decision.decision
            ),
            "proactive_lifecycle_certification_actionability": (
                proactive_lifecycle_certification_decision.actionability
            ),
            "proactive_lifecycle_certification_active_stage_label": (
                proactive_lifecycle_certification_decision.active_stage_label
            ),
            "proactive_lifecycle_certification_queue_override_status": (
                proactive_lifecycle_certification_decision.queue_override_status
            ),
            "proactive_lifecycle_confirmation_key": (
                proactive_lifecycle_confirmation_decision.confirmation_key
            ),
            "proactive_lifecycle_confirmation_status": (
                proactive_lifecycle_confirmation_decision.status
            ),
            "proactive_lifecycle_confirmation_mode": (
                proactive_lifecycle_confirmation_decision.confirmation_mode
            ),
            "proactive_lifecycle_confirmation_decision": (
                proactive_lifecycle_confirmation_decision.decision
            ),
            "proactive_lifecycle_confirmation_actionability": (
                proactive_lifecycle_confirmation_decision.actionability
            ),
            "proactive_lifecycle_confirmation_active_stage_label": (
                proactive_lifecycle_confirmation_decision.active_stage_label
            ),
            "proactive_lifecycle_confirmation_queue_override_status": (
                proactive_lifecycle_confirmation_decision.queue_override_status
            ),
            "proactive_lifecycle_ratification_key": (
                proactive_lifecycle_ratification_decision.ratification_key
            ),
            "proactive_lifecycle_ratification_status": (
                proactive_lifecycle_ratification_decision.status
            ),
            "proactive_lifecycle_ratification_mode": (
                proactive_lifecycle_ratification_decision.ratification_mode
            ),
            "proactive_lifecycle_ratification_decision": (
                proactive_lifecycle_ratification_decision.decision
            ),
            "proactive_lifecycle_ratification_actionability": (
                proactive_lifecycle_ratification_decision.actionability
            ),
            "proactive_lifecycle_ratification_active_stage_label": (
                proactive_lifecycle_ratification_decision.active_stage_label
            ),
            "proactive_lifecycle_ratification_queue_override_status": (
                proactive_lifecycle_ratification_decision.queue_override_status
            ),
            "proactive_lifecycle_endorsement_key": (
                proactive_lifecycle_endorsement_decision.endorsement_key
            ),
            "proactive_lifecycle_endorsement_status": (
                proactive_lifecycle_endorsement_decision.status
            ),
            "proactive_lifecycle_endorsement_mode": (
                proactive_lifecycle_endorsement_decision.endorsement_mode
            ),
            "proactive_lifecycle_endorsement_decision": (
                proactive_lifecycle_endorsement_decision.decision
            ),
            "proactive_lifecycle_endorsement_actionability": (
                proactive_lifecycle_endorsement_decision.actionability
            ),
            "proactive_lifecycle_endorsement_active_stage_label": (
                proactive_lifecycle_endorsement_decision.active_stage_label
            ),
            "proactive_lifecycle_endorsement_queue_override_status": (
                proactive_lifecycle_endorsement_decision.queue_override_status
            ),
            "proactive_lifecycle_authorization_key": (
                proactive_lifecycle_authorization_decision.authorization_key
            ),
            "proactive_lifecycle_authorization_status": (
                proactive_lifecycle_authorization_decision.status
            ),
            "proactive_lifecycle_authorization_mode": (
                proactive_lifecycle_authorization_decision.authorization_mode
            ),
            "proactive_lifecycle_authorization_decision": (
                proactive_lifecycle_authorization_decision.decision
            ),
            "proactive_lifecycle_authorization_actionability": (
                proactive_lifecycle_authorization_decision.actionability
            ),
            "proactive_lifecycle_authorization_active_stage_label": (
                proactive_lifecycle_authorization_decision.active_stage_label
            ),
            "proactive_lifecycle_authorization_queue_override_status": (
                proactive_lifecycle_authorization_decision.queue_override_status
            ),
            "proactive_lifecycle_enactment_key": (
                proactive_lifecycle_enactment_decision.enactment_key
            ),
            "proactive_lifecycle_enactment_status": (
                proactive_lifecycle_enactment_decision.status
            ),
            "proactive_lifecycle_enactment_mode": (
                proactive_lifecycle_enactment_decision.enactment_mode
            ),
            "proactive_lifecycle_enactment_decision": (
                proactive_lifecycle_enactment_decision.decision
            ),
            "proactive_lifecycle_enactment_actionability": (
                proactive_lifecycle_enactment_decision.actionability
            ),
            "proactive_lifecycle_enactment_active_stage_label": (
                proactive_lifecycle_enactment_decision.active_stage_label
            ),
            "proactive_lifecycle_enactment_queue_override_status": (
                proactive_lifecycle_enactment_decision.queue_override_status
            ),
            "proactive_lifecycle_finality_key": (
                proactive_lifecycle_finality_decision.finality_key
            ),
            "proactive_lifecycle_finality_status": (
                proactive_lifecycle_finality_decision.status
            ),
            "proactive_lifecycle_finality_mode": (
                proactive_lifecycle_finality_decision.finality_mode
            ),
            "proactive_lifecycle_finality_decision": (
                proactive_lifecycle_finality_decision.decision
            ),
            "proactive_lifecycle_finality_actionability": (
                proactive_lifecycle_finality_decision.actionability
            ),
            "proactive_lifecycle_finality_active_stage_label": (
                proactive_lifecycle_finality_decision.active_stage_label
            ),
            "proactive_lifecycle_finality_queue_override_status": (
                proactive_lifecycle_finality_decision.queue_override_status
            ),
            "proactive_lifecycle_completion_key": (
                proactive_lifecycle_completion_decision.completion_key
            ),
            "proactive_lifecycle_completion_status": (
                proactive_lifecycle_completion_decision.status
            ),
            "proactive_lifecycle_completion_mode": (
                proactive_lifecycle_completion_decision.completion_mode
            ),
            "proactive_lifecycle_completion_decision": (
                proactive_lifecycle_completion_decision.decision
            ),
            "proactive_lifecycle_completion_actionability": (
                proactive_lifecycle_completion_decision.actionability
            ),
            "proactive_lifecycle_completion_active_stage_label": (
                proactive_lifecycle_completion_decision.active_stage_label
            ),
            "proactive_lifecycle_completion_queue_override_status": (
                proactive_lifecycle_completion_decision.queue_override_status
            ),
            "proactive_lifecycle_conclusion_key": (
                proactive_lifecycle_conclusion_decision.conclusion_key
            ),
            "proactive_lifecycle_conclusion_status": (
                proactive_lifecycle_conclusion_decision.status
            ),
            "proactive_lifecycle_conclusion_mode": (
                proactive_lifecycle_conclusion_decision.conclusion_mode
            ),
            "proactive_lifecycle_conclusion_decision": (
                proactive_lifecycle_conclusion_decision.decision
            ),
            "proactive_lifecycle_conclusion_actionability": (
                proactive_lifecycle_conclusion_decision.actionability
            ),
            "proactive_lifecycle_conclusion_active_stage_label": (
                proactive_lifecycle_conclusion_decision.active_stage_label
            ),
            "proactive_lifecycle_conclusion_queue_override_status": (
                proactive_lifecycle_conclusion_decision.queue_override_status
            ),
            "proactive_lifecycle_disposition_key": (
                proactive_lifecycle_disposition_decision.disposition_key
            ),
            "proactive_lifecycle_disposition_status": (
                proactive_lifecycle_disposition_decision.status
            ),
            "proactive_lifecycle_disposition_mode": (
                proactive_lifecycle_disposition_decision.disposition_mode
            ),
            "proactive_lifecycle_disposition_decision": (
                proactive_lifecycle_disposition_decision.decision
            ),
            "proactive_lifecycle_disposition_actionability": (
                proactive_lifecycle_disposition_decision.actionability
            ),
            "proactive_lifecycle_disposition_active_stage_label": (
                proactive_lifecycle_disposition_decision.active_stage_label
            ),
            "proactive_lifecycle_disposition_queue_override_status": (
                proactive_lifecycle_disposition_decision.queue_override_status
            ),
            "proactive_lifecycle_standing_key": (
                proactive_lifecycle_standing_decision.standing_key
            ),
            "proactive_lifecycle_standing_status": (
                proactive_lifecycle_standing_decision.status
            ),
            "proactive_lifecycle_standing_mode": (
                proactive_lifecycle_standing_decision.standing_mode
            ),
            "proactive_lifecycle_standing_decision": (
                proactive_lifecycle_standing_decision.decision
            ),
            "proactive_lifecycle_standing_actionability": (
                proactive_lifecycle_standing_decision.actionability
            ),
            "proactive_lifecycle_standing_active_stage_label": (
                proactive_lifecycle_standing_decision.active_stage_label
            ),
            "proactive_lifecycle_standing_queue_override_status": (
                proactive_lifecycle_standing_decision.queue_override_status
            ),
            "proactive_lifecycle_residency_key": (
                proactive_lifecycle_residency_decision.residency_key
            ),
            "proactive_lifecycle_residency_status": (
                proactive_lifecycle_residency_decision.status
            ),
            "proactive_lifecycle_residency_mode": (
                proactive_lifecycle_residency_decision.residency_mode
            ),
            "proactive_lifecycle_residency_decision": (
                proactive_lifecycle_residency_decision.decision
            ),
            "proactive_lifecycle_residency_actionability": (
                proactive_lifecycle_residency_decision.actionability
            ),
            "proactive_lifecycle_residency_active_stage_label": (
                proactive_lifecycle_residency_decision.active_stage_label
            ),
            "proactive_lifecycle_residency_queue_override_status": (
                proactive_lifecycle_residency_decision.queue_override_status
            ),
            "proactive_lifecycle_tenure_key": (
                proactive_lifecycle_tenure_decision.tenure_key
            ),
            "proactive_lifecycle_tenure_status": (
                proactive_lifecycle_tenure_decision.status
            ),
            "proactive_lifecycle_tenure_mode": (
                proactive_lifecycle_tenure_decision.tenure_mode
            ),
            "proactive_lifecycle_tenure_decision": (
                proactive_lifecycle_tenure_decision.decision
            ),
            "proactive_lifecycle_tenure_actionability": (
                proactive_lifecycle_tenure_decision.actionability
            ),
            "proactive_lifecycle_tenure_active_stage_label": (
                proactive_lifecycle_tenure_decision.active_stage_label
            ),
            "proactive_lifecycle_tenure_queue_override_status": (
                proactive_lifecycle_tenure_decision.queue_override_status
            ),
            "proactive_lifecycle_persistence_key": (
                proactive_lifecycle_persistence_decision.persistence_key
            ),
            "proactive_lifecycle_persistence_status": (
                proactive_lifecycle_persistence_decision.status
            ),
            "proactive_lifecycle_persistence_mode": (
                proactive_lifecycle_persistence_decision.persistence_mode
            ),
            "proactive_lifecycle_persistence_decision": (
                proactive_lifecycle_persistence_decision.decision
            ),
            "proactive_lifecycle_persistence_actionability": (
                proactive_lifecycle_persistence_decision.actionability
            ),
            "proactive_lifecycle_persistence_active_stage_label": (
                proactive_lifecycle_persistence_decision.active_stage_label
            ),
            "proactive_lifecycle_persistence_queue_override_status": (
                proactive_lifecycle_persistence_decision.queue_override_status
            ),
            "proactive_lifecycle_durability_key": (
                proactive_lifecycle_durability_decision.durability_key
            ),
            "proactive_lifecycle_durability_status": (
                proactive_lifecycle_durability_decision.status
            ),
            "proactive_lifecycle_durability_mode": (
                proactive_lifecycle_durability_decision.durability_mode
            ),
            "proactive_lifecycle_durability_decision": (
                proactive_lifecycle_durability_decision.decision
            ),
            "proactive_lifecycle_durability_actionability": (
                proactive_lifecycle_durability_decision.actionability
            ),
            "proactive_lifecycle_durability_active_stage_label": (
                proactive_lifecycle_durability_decision.active_stage_label
            ),
            "proactive_lifecycle_durability_queue_override_status": (
                proactive_lifecycle_durability_decision.queue_override_status
            ),
            "proactive_lifecycle_longevity_key": (
                proactive_lifecycle_longevity_decision.longevity_key
            ),
            "proactive_lifecycle_longevity_status": (
                proactive_lifecycle_longevity_decision.status
            ),
            "proactive_lifecycle_longevity_mode": (
                proactive_lifecycle_longevity_decision.longevity_mode
            ),
            "proactive_lifecycle_longevity_decision": (
                proactive_lifecycle_longevity_decision.decision
            ),
            "proactive_lifecycle_longevity_actionability": (
                proactive_lifecycle_longevity_decision.actionability
            ),
            "proactive_lifecycle_longevity_active_stage_label": (
                proactive_lifecycle_longevity_decision.active_stage_label
            ),
            "proactive_lifecycle_longevity_queue_override_status": (
                proactive_lifecycle_longevity_decision.queue_override_status
            ),
            "proactive_lifecycle_legacy_key": (
                proactive_lifecycle_legacy_decision.legacy_key
            ),
            "proactive_lifecycle_legacy_status": (
                proactive_lifecycle_legacy_decision.status
            ),
            "proactive_lifecycle_legacy_mode": (
                proactive_lifecycle_legacy_decision.legacy_mode
            ),
            "proactive_lifecycle_legacy_decision": (
                proactive_lifecycle_legacy_decision.decision
            ),
            "proactive_lifecycle_legacy_actionability": (
                proactive_lifecycle_legacy_decision.actionability
            ),
            "proactive_lifecycle_legacy_active_stage_label": (
                proactive_lifecycle_legacy_decision.active_stage_label
            ),
            "proactive_lifecycle_legacy_queue_override_status": (
                proactive_lifecycle_legacy_decision.queue_override_status
            ),
            "proactive_lifecycle_heritage_key": (
                proactive_lifecycle_heritage_decision.heritage_key
            ),
            "proactive_lifecycle_heritage_status": (
                proactive_lifecycle_heritage_decision.status
            ),
            "proactive_lifecycle_heritage_mode": (
                proactive_lifecycle_heritage_decision.heritage_mode
            ),
            "proactive_lifecycle_heritage_decision": (
                proactive_lifecycle_heritage_decision.decision
            ),
            "proactive_lifecycle_heritage_actionability": (
                proactive_lifecycle_heritage_decision.actionability
            ),
            "proactive_lifecycle_heritage_active_stage_label": (
                proactive_lifecycle_heritage_decision.active_stage_label
            ),
            "proactive_lifecycle_heritage_queue_override_status": (
                proactive_lifecycle_heritage_decision.queue_override_status
            ),
            "proactive_lifecycle_lineage_key": (
                proactive_lifecycle_lineage_decision.lineage_key
            ),
            "proactive_lifecycle_lineage_status": (
                proactive_lifecycle_lineage_decision.status
            ),
            "proactive_lifecycle_lineage_mode": (
                proactive_lifecycle_lineage_decision.lineage_mode
            ),
            "proactive_lifecycle_lineage_decision": (
                proactive_lifecycle_lineage_decision.decision
            ),
            "proactive_lifecycle_lineage_actionability": (
                proactive_lifecycle_lineage_decision.actionability
            ),
            "proactive_lifecycle_lineage_active_stage_label": (
                proactive_lifecycle_lineage_decision.active_stage_label
            ),
            "proactive_lifecycle_lineage_queue_override_status": (
                proactive_lifecycle_lineage_decision.queue_override_status
            ),
            "proactive_lifecycle_ancestry_key": (
                proactive_lifecycle_ancestry_decision.ancestry_key
            ),
            "proactive_lifecycle_ancestry_status": (
                proactive_lifecycle_ancestry_decision.status
            ),
            "proactive_lifecycle_ancestry_mode": (
                proactive_lifecycle_ancestry_decision.ancestry_mode
            ),
            "proactive_lifecycle_ancestry_decision": (
                proactive_lifecycle_ancestry_decision.decision
            ),
            "proactive_lifecycle_ancestry_actionability": (
                proactive_lifecycle_ancestry_decision.actionability
            ),
            "proactive_lifecycle_ancestry_active_stage_label": (
                proactive_lifecycle_ancestry_decision.active_stage_label
            ),
            "proactive_lifecycle_ancestry_queue_override_status": (
                proactive_lifecycle_ancestry_decision.queue_override_status
            ),
            "proactive_lifecycle_provenance_key": (
                proactive_lifecycle_provenance_decision.provenance_key
            ),
            "proactive_lifecycle_provenance_status": (
                proactive_lifecycle_provenance_decision.status
            ),
            "proactive_lifecycle_provenance_mode": (
                proactive_lifecycle_provenance_decision.provenance_mode
            ),
            "proactive_lifecycle_provenance_decision": (
                proactive_lifecycle_provenance_decision.decision
            ),
            "proactive_lifecycle_provenance_actionability": (
                proactive_lifecycle_provenance_decision.actionability
            ),
            "proactive_lifecycle_provenance_active_stage_label": (
                proactive_lifecycle_provenance_decision.active_stage_label
            ),
            "proactive_lifecycle_provenance_queue_override_status": (
                proactive_lifecycle_provenance_decision.queue_override_status
            ),
            "proactive_lifecycle_origin_key": (
                proactive_lifecycle_origin_decision.origin_key
            ),
            "proactive_lifecycle_origin_status": (
                proactive_lifecycle_origin_decision.status
            ),
            "proactive_lifecycle_origin_mode": (
                proactive_lifecycle_origin_decision.origin_mode
            ),
            "proactive_lifecycle_origin_decision": (
                proactive_lifecycle_origin_decision.decision
            ),
            "proactive_lifecycle_origin_actionability": (
                proactive_lifecycle_origin_decision.actionability
            ),
            "proactive_lifecycle_origin_active_stage_label": (
                proactive_lifecycle_origin_decision.active_stage_label
            ),
            "proactive_lifecycle_origin_queue_override_status": (
                proactive_lifecycle_origin_decision.queue_override_status
            ),
            "proactive_lifecycle_root_key": proactive_lifecycle_root_decision.root_key,
            "proactive_lifecycle_root_status": proactive_lifecycle_root_decision.status,
            "proactive_lifecycle_root_mode": proactive_lifecycle_root_decision.root_mode,
            "proactive_lifecycle_root_decision": (
                proactive_lifecycle_root_decision.decision
            ),
            "proactive_lifecycle_root_actionability": (
                proactive_lifecycle_root_decision.actionability
            ),
            "proactive_lifecycle_root_active_stage_label": (
                proactive_lifecycle_root_decision.active_stage_label
            ),
            "proactive_lifecycle_root_queue_override_status": (
                proactive_lifecycle_root_decision.queue_override_status
            ),
            "proactive_lifecycle_foundation_key": (
                proactive_lifecycle_foundation_decision.foundation_key
            ),
            "proactive_lifecycle_foundation_status": (
                proactive_lifecycle_foundation_decision.status
            ),
            "proactive_lifecycle_foundation_mode": (
                proactive_lifecycle_foundation_decision.foundation_mode
            ),
            "proactive_lifecycle_foundation_decision": (
                proactive_lifecycle_foundation_decision.decision
            ),
            "proactive_lifecycle_foundation_actionability": (
                proactive_lifecycle_foundation_decision.actionability
            ),
            "proactive_lifecycle_foundation_active_stage_label": (
                proactive_lifecycle_foundation_decision.active_stage_label
            ),
            "proactive_lifecycle_foundation_queue_override_status": (
                proactive_lifecycle_foundation_decision.queue_override_status
            ),
            "proactive_lifecycle_bedrock_key": (
                proactive_lifecycle_bedrock_decision.bedrock_key
            ),
            "proactive_lifecycle_bedrock_status": (
                proactive_lifecycle_bedrock_decision.status
            ),
            "proactive_lifecycle_bedrock_mode": (
                proactive_lifecycle_bedrock_decision.bedrock_mode
            ),
            "proactive_lifecycle_bedrock_decision": (
                proactive_lifecycle_bedrock_decision.decision
            ),
            "proactive_lifecycle_bedrock_actionability": (
                proactive_lifecycle_bedrock_decision.actionability
            ),
            "proactive_lifecycle_bedrock_active_stage_label": (
                proactive_lifecycle_bedrock_decision.active_stage_label
            ),
            "proactive_lifecycle_bedrock_queue_override_status": (
                proactive_lifecycle_bedrock_decision.queue_override_status
            ),
            "proactive_lifecycle_substrate_key": (
                proactive_lifecycle_substrate_decision.substrate_key
            ),
            "proactive_lifecycle_substrate_status": (
                proactive_lifecycle_substrate_decision.status
            ),
            "proactive_lifecycle_substrate_mode": (
                proactive_lifecycle_substrate_decision.substrate_mode
            ),
            "proactive_lifecycle_substrate_decision": (
                proactive_lifecycle_substrate_decision.decision
            ),
            "proactive_lifecycle_substrate_actionability": (
                proactive_lifecycle_substrate_decision.actionability
            ),
            "proactive_lifecycle_substrate_active_stage_label": (
                proactive_lifecycle_substrate_decision.active_stage_label
            ),
            "proactive_lifecycle_substrate_queue_override_status": (
                proactive_lifecycle_substrate_decision.queue_override_status
            ),
            "proactive_lifecycle_stratum_key": (
                proactive_lifecycle_stratum_decision.stratum_key
            ),
            "proactive_lifecycle_stratum_status": (
                proactive_lifecycle_stratum_decision.status
            ),
            "proactive_lifecycle_stratum_mode": (
                proactive_lifecycle_stratum_decision.stratum_mode
            ),
            "proactive_lifecycle_stratum_decision": (
                proactive_lifecycle_stratum_decision.decision
            ),
            "proactive_lifecycle_stratum_actionability": (
                proactive_lifecycle_stratum_decision.actionability
            ),
            "proactive_lifecycle_stratum_active_stage_label": (
                proactive_lifecycle_stratum_decision.active_stage_label
            ),
            "proactive_lifecycle_stratum_queue_override_status": (
                proactive_lifecycle_stratum_decision.queue_override_status
            ),
            "proactive_lifecycle_layer_key": (
                proactive_lifecycle_layer_decision.layer_key
            ),
            "proactive_lifecycle_layer_status": (
                proactive_lifecycle_layer_decision.status
            ),
            "proactive_lifecycle_layer_mode": (
                proactive_lifecycle_layer_decision.layer_mode
            ),
            "proactive_lifecycle_layer_decision": (
                proactive_lifecycle_layer_decision.decision
            ),
            "proactive_lifecycle_layer_actionability": (
                proactive_lifecycle_layer_decision.actionability
            ),
            "proactive_lifecycle_layer_active_stage_label": (
                proactive_lifecycle_layer_decision.active_stage_label
            ),
            "proactive_lifecycle_layer_queue_override_status": (
                proactive_lifecycle_layer_decision.queue_override_status
            ),
            "proactive_actuation_key": proactive_actuation_plan.get("actuation_key"),
            "proactive_actuation_opening_move": (
                effective_stage_actuation.get("opening_move")
            ),
            "proactive_actuation_bridge_move": (
                effective_stage_actuation.get("bridge_move")
            ),
            "proactive_actuation_closing_move": (
                effective_stage_actuation.get("closing_move")
            ),
            "proactive_actuation_continuity_anchor": (
                effective_stage_actuation.get("continuity_anchor")
            ),
            "proactive_actuation_somatic_mode": (
                effective_stage_actuation.get("somatic_mode")
            ),
            "proactive_actuation_somatic_body_anchor": (
                effective_stage_actuation.get("somatic_body_anchor")
            ),
            "proactive_actuation_followup_style": (
                effective_stage_actuation.get("followup_style")
            ),
            "proactive_actuation_user_space_signal": (
                effective_stage_actuation.get("user_space_signal")
            ),
            "proactive_progression_key": proactive_progression_plan.get(
                "progression_key"
            ),
            "proactive_progression_stage_action": (
                (queue_item or {}).get("proactive_progression_stage_action")
            ),
            "proactive_progression_advanced": bool(
                (queue_item or {}).get("proactive_progression_advanced")
            ),
            "proactive_progression_reason": (
                (queue_item or {}).get("proactive_progression_reason")
            ),
            "proactive_cadence_remaining_after_dispatch": max(
                0,
                (
                    proactive_cadence_plan_model.close_after_stage_index
                    or len(proactive_cadence_plan_model.stage_labels)
                )
                - current_stage_index,
            ),
            "time_awareness_mode": runtime_coordination_snapshot.get(
                "time_awareness_mode"
            ),
            "cognitive_load_band": runtime_coordination_snapshot.get(
                "cognitive_load_band"
            ),
            "cadence_status": conversation_cadence_plan.get("status"),
            "cadence_turn_shape": conversation_cadence_plan.get("turn_shape"),
            "cadence_followup_tempo": conversation_cadence_plan.get("followup_tempo"),
            "cadence_user_space_mode": conversation_cadence_plan.get(
                "user_space_mode"
            ),
            "ritual_phase": session_ritual_plan_model.phase,
            "ritual_opening_move": session_ritual_plan_model.opening_move,
            "ritual_bridge_move": session_ritual_plan_model.bridge_move,
            "ritual_closing_move": session_ritual_plan_model.closing_move,
            "ritual_somatic_shortcut": session_ritual_plan_model.somatic_shortcut,
            "ritual_continuity_anchor": session_ritual_plan_model.continuity_anchor,
            "somatic_orchestration_status": somatic_orchestration_plan_model.status,
            "somatic_orchestration_mode": (
                somatic_orchestration_plan_model.primary_mode
            ),
            "somatic_orchestration_body_anchor": (
                somatic_orchestration_plan_model.body_anchor
            ),
            "somatic_orchestration_followup_style": (
                somatic_orchestration_plan_model.followup_style
            ),
            "dispatched_at": utc_now().isoformat(),
        }
        stored_events = await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=len(prior_events),
            events=[
                NewEvent(
                    event_type=PROACTIVE_STAGE_REFRESH_UPDATED,
                    payload=asdict(proactive_stage_refresh_plan),
                ),
                NewEvent(
                    event_type=PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
                    payload=asdict(proactive_aggregate_governance_assessment),
                ),
                NewEvent(
                    event_type=PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
                    payload=asdict(proactive_aggregate_controller_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
                    payload=asdict(proactive_orchestration_controller_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_STAGE_REPLAN_UPDATED,
                    payload=asdict(proactive_stage_replan_assessment),
                ),
                NewEvent(
                    event_type=PROACTIVE_STAGE_CONTROLLER_UPDATED,
                    payload=asdict(proactive_stage_controller_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LINE_CONTROLLER_UPDATED,
                    payload=asdict(proactive_line_controller_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
                    payload=asdict(proactive_dispatch_feedback_assessment),
                ),
                NewEvent(
                    event_type=PROACTIVE_DISPATCH_GATE_UPDATED,
                    payload=asdict(proactive_dispatch_gate_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
                    payload=asdict(proactive_dispatch_envelope_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_STAGE_STATE_UPDATED,
                    payload=asdict(proactive_stage_state_decision),
                ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_TRANSITION_UPDATED,
                        payload=asdict(proactive_stage_transition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_STAGE_MACHINE_UPDATED,
                        payload=asdict(proactive_stage_machine_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_STATE_UPDATED,
                        payload=asdict(proactive_line_state_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_TRANSITION_UPDATED,
                        payload=asdict(proactive_line_transition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LINE_MACHINE_UPDATED,
                        payload=asdict(proactive_line_machine_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_STATE_UPDATED,
                        payload=asdict(proactive_lifecycle_state_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_TRANSITION_UPDATED,
                        payload=asdict(proactive_lifecycle_transition_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_MACHINE_UPDATED,
                        payload=asdict(proactive_lifecycle_machine_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED,
                        payload=asdict(proactive_lifecycle_controller_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED,
                        payload=asdict(proactive_lifecycle_envelope_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED,
                        payload=asdict(proactive_lifecycle_scheduler_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_WINDOW_UPDATED,
                        payload=asdict(proactive_lifecycle_window_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_QUEUE_UPDATED,
                        payload=asdict(proactive_lifecycle_queue_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_LIFECYCLE_DISPATCH_UPDATED,
                        payload=asdict(proactive_lifecycle_dispatch_decision),
                    ),
                    NewEvent(
                        event_type=PROACTIVE_FOLLOWUP_DISPATCHED,
                        payload=dispatch_payload,
                    ),
                *[
                    NewEvent(
                        event_type=ASSISTANT_MESSAGE_SENT,
                        payload={
                            "content": item["content"],
                            "model": "relationship-os/proactive-followup",
                            "usage": None,
                            "latency_ms": None,
                            "failure": None,
                            "sequence_index": index,
                            "sequence_total": len(followup_units),
                            "delivery_mode": "proactive_followup",
                            "segment_label": item["label"],
                        },
                    )
                    for index, item in enumerate(followup_units, start=1)
                ],
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_OUTCOME_UPDATED,
                    payload=asdict(proactive_lifecycle_outcome_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED,
                    payload=asdict(proactive_lifecycle_resolution_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED,
                    payload=asdict(proactive_lifecycle_activation_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED,
                    payload=asdict(proactive_lifecycle_settlement_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_CLOSURE_UPDATED,
                    payload=asdict(proactive_lifecycle_closure_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED,
                    payload=asdict(proactive_lifecycle_availability_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_RETENTION_UPDATED,
                    payload=asdict(proactive_lifecycle_retention_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED,
                    payload=asdict(proactive_lifecycle_eligibility_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED,
                    payload=asdict(proactive_lifecycle_candidate_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED,
                    payload=asdict(proactive_lifecycle_selectability_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_REENTRY_UPDATED,
                    payload=asdict(proactive_lifecycle_reentry_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED,
                    payload=asdict(proactive_lifecycle_reactivation_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED,
                    payload=asdict(proactive_lifecycle_resumption_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_READINESS_UPDATED,
                    payload=asdict(proactive_lifecycle_readiness_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ARMING_UPDATED,
                    payload=asdict(proactive_lifecycle_arming_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_TRIGGER_UPDATED,
                    payload=asdict(proactive_lifecycle_trigger_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_LAUNCH_UPDATED,
                    payload=asdict(proactive_lifecycle_launch_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_HANDOFF_UPDATED,
                    payload=asdict(proactive_lifecycle_handoff_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED,
                    payload=asdict(proactive_lifecycle_continuation_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED,
                    payload=asdict(proactive_lifecycle_sustainment_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED,
                    payload=asdict(proactive_lifecycle_stewardship_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED,
                    payload=asdict(proactive_lifecycle_guardianship_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED,
                    payload=asdict(proactive_lifecycle_oversight_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED,
                    payload=asdict(proactive_lifecycle_assurance_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED,
                    payload=asdict(proactive_lifecycle_attestation_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED,
                    payload=asdict(proactive_lifecycle_verification_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED,
                    payload=asdict(proactive_lifecycle_certification_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED,
                    payload=asdict(proactive_lifecycle_confirmation_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED,
                    payload=asdict(proactive_lifecycle_ratification_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED,
                    payload=asdict(proactive_lifecycle_endorsement_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED,
                    payload=asdict(proactive_lifecycle_authorization_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED,
                    payload=asdict(proactive_lifecycle_enactment_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_FINALITY_UPDATED,
                    payload=asdict(proactive_lifecycle_finality_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_COMPLETION_UPDATED,
                    payload=asdict(proactive_lifecycle_completion_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED,
                    payload=asdict(proactive_lifecycle_conclusion_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED,
                    payload=asdict(proactive_lifecycle_disposition_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_STANDING_UPDATED,
                    payload=asdict(proactive_lifecycle_standing_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED,
                    payload=asdict(proactive_lifecycle_residency_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_TENURE_UPDATED,
                    payload=asdict(proactive_lifecycle_tenure_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED,
                    payload=asdict(proactive_lifecycle_persistence_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_DURABILITY_UPDATED,
                    payload=asdict(proactive_lifecycle_durability_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED,
                    payload=asdict(proactive_lifecycle_longevity_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_LEGACY_UPDATED,
                    payload=asdict(proactive_lifecycle_legacy_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_HERITAGE_UPDATED,
                    payload=asdict(proactive_lifecycle_heritage_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_LINEAGE_UPDATED,
                    payload=asdict(proactive_lifecycle_lineage_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED,
                    payload=asdict(proactive_lifecycle_ancestry_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED,
                    payload=asdict(proactive_lifecycle_provenance_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ORIGIN_UPDATED,
                    payload=asdict(proactive_lifecycle_origin_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_ROOT_UPDATED,
                    payload=asdict(proactive_lifecycle_root_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED,
                    payload=asdict(proactive_lifecycle_foundation_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_BEDROCK_UPDATED,
                    payload=asdict(proactive_lifecycle_bedrock_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED,
                    payload=asdict(proactive_lifecycle_substrate_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_STRATUM_UPDATED,
                    payload=asdict(proactive_lifecycle_stratum_decision),
                ),
                NewEvent(
                    event_type=PROACTIVE_LIFECYCLE_LAYER_UPDATED,
                    payload=asdict(proactive_lifecycle_layer_decision),
                ),
            ],
        )
        updated_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
        )
        return {
            "session_id": session_id,
            "dispatched": True,
            "dispatch": dispatch_payload,
            "lifecycle_outcome": asdict(proactive_lifecycle_outcome_decision),
            "lifecycle_resolution": asdict(proactive_lifecycle_resolution_decision),
            "lifecycle_activation": asdict(proactive_lifecycle_activation_decision),
            "lifecycle_settlement": asdict(proactive_lifecycle_settlement_decision),
            "lifecycle_closure": asdict(proactive_lifecycle_closure_decision),
            "lifecycle_availability": asdict(
                proactive_lifecycle_availability_decision
            ),
            "lifecycle_retention": asdict(proactive_lifecycle_retention_decision),
            "lifecycle_eligibility": asdict(proactive_lifecycle_eligibility_decision),
            "lifecycle_candidate": asdict(proactive_lifecycle_candidate_decision),
            "lifecycle_selectability": asdict(
                proactive_lifecycle_selectability_decision
            ),
            "lifecycle_reentry": asdict(proactive_lifecycle_reentry_decision),
            "lifecycle_reactivation": asdict(
                proactive_lifecycle_reactivation_decision
            ),
            "lifecycle_resumption": asdict(
                proactive_lifecycle_resumption_decision
            ),
            "lifecycle_readiness": asdict(
                proactive_lifecycle_readiness_decision
            ),
            "lifecycle_arming": asdict(proactive_lifecycle_arming_decision),
            "lifecycle_trigger": asdict(proactive_lifecycle_trigger_decision),
            "lifecycle_launch": asdict(proactive_lifecycle_launch_decision),
            "lifecycle_handoff": asdict(proactive_lifecycle_handoff_decision),
            "lifecycle_continuation": asdict(
                proactive_lifecycle_continuation_decision
            ),
            "lifecycle_sustainment": asdict(proactive_lifecycle_sustainment_decision),
            "lifecycle_stewardship": asdict(
                proactive_lifecycle_stewardship_decision
            ),
            "lifecycle_guardianship": asdict(
                proactive_lifecycle_guardianship_decision
            ),
            "lifecycle_oversight": asdict(proactive_lifecycle_oversight_decision),
            "lifecycle_assurance": asdict(proactive_lifecycle_assurance_decision),
            "lifecycle_attestation": asdict(
                proactive_lifecycle_attestation_decision
            ),
            "lifecycle_verification": asdict(
                proactive_lifecycle_verification_decision
            ),
            "lifecycle_certification": asdict(
                proactive_lifecycle_certification_decision
            ),
            "lifecycle_confirmation": asdict(
                proactive_lifecycle_confirmation_decision
            ),
            "lifecycle_ratification": asdict(
                proactive_lifecycle_ratification_decision
            ),
            "lifecycle_endorsement": asdict(
                proactive_lifecycle_endorsement_decision
            ),
            "lifecycle_authorization": asdict(
                proactive_lifecycle_authorization_decision
            ),
            "lifecycle_enactment": asdict(proactive_lifecycle_enactment_decision),
            "lifecycle_finality": asdict(proactive_lifecycle_finality_decision),
            "lifecycle_completion": asdict(proactive_lifecycle_completion_decision),
            "lifecycle_conclusion": asdict(proactive_lifecycle_conclusion_decision),
            "lifecycle_disposition": asdict(
                proactive_lifecycle_disposition_decision
            ),
            "lifecycle_standing": asdict(proactive_lifecycle_standing_decision),
            "lifecycle_residency": asdict(proactive_lifecycle_residency_decision),
            "lifecycle_tenure": asdict(proactive_lifecycle_tenure_decision),
            "lifecycle_persistence": asdict(
                proactive_lifecycle_persistence_decision
            ),
            "lifecycle_durability": asdict(
                proactive_lifecycle_durability_decision
            ),
            "lifecycle_longevity": asdict(proactive_lifecycle_longevity_decision),
            "lifecycle_legacy": asdict(proactive_lifecycle_legacy_decision),
            "lifecycle_heritage": asdict(proactive_lifecycle_heritage_decision),
            "lifecycle_lineage": asdict(proactive_lifecycle_lineage_decision),
            "lifecycle_ancestry": asdict(proactive_lifecycle_ancestry_decision),
            "lifecycle_provenance": asdict(
                proactive_lifecycle_provenance_decision
            ),
            "lifecycle_origin": asdict(proactive_lifecycle_origin_decision),
            "lifecycle_root": asdict(proactive_lifecycle_root_decision),
            "lifecycle_foundation": asdict(proactive_lifecycle_foundation_decision),
            "lifecycle_bedrock": asdict(proactive_lifecycle_bedrock_decision),
            "lifecycle_substrate": asdict(proactive_lifecycle_substrate_decision),
            "lifecycle_stratum": asdict(proactive_lifecycle_stratum_decision),
            "lifecycle_layer": asdict(proactive_lifecycle_layer_decision),
            "assistant_response": followup_content,
            "events": [
                self._stream_service.serialize_event(event) for event in stored_events
            ],
            "projection": updated_projection,
        }

    def _latest_event(
        self,
        events: list[StoredEvent],
        *,
        event_type: str,
    ) -> StoredEvent | None:
        return next(
            (event for event in reversed(events) if event.event_type == event_type),
            None,
        )
