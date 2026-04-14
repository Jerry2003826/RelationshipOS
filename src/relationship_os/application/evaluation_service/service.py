"""EvaluationService — orchestrates session evaluation, preference reports, and learning."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
    apply_snapshot_to_turn_record,
    is_legacy_lifecycle_event_type,
)
from relationship_os.application.evaluation_service.summary_builder import (
    build_summary,
)
from relationship_os.application.evaluation_service.turn_record import (
    StrategyPreferenceRecord,
    TurnRecord,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    CONFIDENCE_ASSESSMENT_COMPUTED,
    CONTEXT_FRAME_COMPUTED,
    CONVERSATION_CADENCE_UPDATED,
    EMPOWERMENT_AUDIT_COMPLETED,
    GUIDANCE_PLAN_UPDATED,
    KNOWLEDGE_BOUNDARY_DECIDED,
    LLM_COMPLETION_FAILED,
    MEMORY_BUNDLE_UPDATED,
    MEMORY_FORGETTING_APPLIED,
    MEMORY_RECALL_PERFORMED,
    MEMORY_RETENTION_POLICY_APPLIED,
    MEMORY_WRITE_GUARD_EVALUATED,
    POLICY_GATE_DECIDED,
    PRIVATE_JUDGMENT_COMPUTED,
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_CADENCE_UPDATED,
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_DISPATCH_OUTCOME_RECORDED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_GUARDRAIL_UPDATED,
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_LINE_MACHINE_UPDATED,
    PROACTIVE_LINE_STATE_UPDATED,
    PROACTIVE_LINE_TRANSITION_UPDATED,
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_MACHINE_UPDATED,
    PROACTIVE_STAGE_REFRESH_UPDATED,
    PROACTIVE_STAGE_REPLAN_UPDATED,
    PROACTIVE_STAGE_STATE_UPDATED,
    PROACTIVE_STAGE_TRANSITION_UPDATED,
    REENGAGEMENT_MATRIX_ASSESSED,
    REENGAGEMENT_PLAN_UPDATED,
    REHEARSAL_COMPLETED,
    RELATIONSHIP_STATE_UPDATED,
    REPAIR_ASSESSMENT_COMPUTED,
    REPAIR_PLAN_UPDATED,
    RESPONSE_DRAFT_PLANNED,
    RESPONSE_NORMALIZED,
    RESPONSE_POST_AUDITED,
    RESPONSE_RENDERING_POLICY_DECIDED,
    RESPONSE_SEQUENCE_PLANNED,
    RUNTIME_COORDINATION_UPDATED,
    RUNTIME_QUALITY_DOCTOR_COMPLETED,
    SESSION_DIRECTIVE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SESSION_STARTED,
    SOMATIC_ORCHESTRATION_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import StoredEvent

_PREFERENCE_STATUS_RULES: tuple[
    tuple[str, str, tuple[tuple[str, float, str], ...]],
    ...,
] = (
    (
        "output_quality_status",
        "stable",
        (
            ("watch", 0.2, "quality_watch"),
            ("degrading", 0.4, "quality_degrading"),
        ),
    ),
    (
        "latest_runtime_quality_doctor_status",
        "pass",
        (
            ("watch", 0.1, "runtime_quality_doctor_watch"),
            ("revise", 0.2, "runtime_quality_doctor_revise"),
        ),
    ),
    (
        "latest_system3_identity_trajectory_status",
        "stable",
        (
            ("watch", 0.06, "system3_identity_trajectory_watch"),
            ("recenter", 0.14, "system3_identity_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_strategy_audit_status",
        "pass",
        (
            ("watch", 0.1, "system3_strategy_audit_watch"),
            ("revise", 0.2, "system3_strategy_audit_revise"),
        ),
    ),
    (
        "latest_system3_strategy_audit_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_strategy_audit_trajectory_watch"),
            ("corrective", 0.1, "system3_strategy_audit_trajectory_corrective"),
        ),
    ),
    (
        "latest_system3_strategy_supervision_status",
        "pass",
        (
            ("watch", 0.08, "system3_strategy_supervision_watch"),
            ("revise", 0.18, "system3_strategy_supervision_revise"),
        ),
    ),
    (
        "latest_system3_strategy_supervision_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_strategy_supervision_trajectory_watch"),
            ("tighten", 0.1, "system3_strategy_supervision_trajectory_tighten"),
        ),
    ),
    (
        "latest_system3_moral_reasoning_status",
        "pass",
        (
            ("watch", 0.08, "system3_moral_reasoning_watch"),
            ("revise", 0.18, "system3_moral_reasoning_revise"),
        ),
    ),
    (
        "latest_system3_moral_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_moral_trajectory_watch"),
            ("recenter", 0.1, "system3_moral_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_user_model_evolution_status",
        "pass",
        (
            ("watch", 0.06, "system3_user_model_evolution_watch"),
            ("revise", 0.14, "system3_user_model_evolution_revise"),
        ),
    ),
    (
        "latest_system3_user_model_trajectory_status",
        "stable",
        (
            ("watch", 0.05, "system3_user_model_trajectory_watch"),
            ("recenter", 0.12, "system3_user_model_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_expectation_calibration_status",
        "pass",
        (
            ("watch", 0.05, "system3_expectation_calibration_watch"),
            ("revise", 0.12, "system3_expectation_calibration_revise"),
        ),
    ),
    (
        "latest_system3_expectation_calibration_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_expectation_calibration_trajectory_watch"),
            ("reset", 0.1, "system3_expectation_calibration_trajectory_reset"),
        ),
    ),
    (
        "latest_system3_dependency_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_dependency_governance_watch"),
            ("revise", 0.12, "system3_dependency_governance_revise"),
        ),
    ),
    (
        "latest_system3_dependency_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_dependency_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_dependency_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_autonomy_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_autonomy_governance_watch"),
            ("revise", 0.12, "system3_autonomy_governance_revise"),
        ),
    ),
    (
        "latest_system3_autonomy_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_autonomy_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_autonomy_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_boundary_governance_status",
        "pass",
        (
            ("watch", 0.06, "system3_boundary_governance_watch"),
            ("revise", 0.14, "system3_boundary_governance_revise"),
        ),
    ),
    (
        "latest_system3_boundary_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.05, "system3_boundary_governance_trajectory_watch"),
            ("recenter", 0.11, "system3_boundary_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_support_governance_status",
        "pass",
        (
            ("watch", 0.06, "system3_support_governance_watch"),
            ("revise", 0.14, "system3_support_governance_revise"),
        ),
    ),
    (
        "latest_system3_support_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.05, "system3_support_governance_trajectory_watch"),
            ("recenter", 0.11, "system3_support_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_continuity_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_continuity_governance_watch"),
            ("revise", 0.13, "system3_continuity_governance_revise"),
        ),
    ),
    (
        "latest_system3_continuity_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_continuity_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_continuity_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_repair_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_repair_governance_watch"),
            ("revise", 0.13, "system3_repair_governance_revise"),
        ),
    ),
    (
        "latest_system3_repair_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_repair_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_repair_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_attunement_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_attunement_governance_watch"),
            ("revise", 0.13, "system3_attunement_governance_revise"),
        ),
    ),
    (
        "latest_system3_attunement_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_attunement_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_attunement_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_trust_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_trust_governance_watch"),
            ("revise", 0.13, "system3_trust_governance_revise"),
        ),
    ),
    (
        "latest_system3_trust_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_trust_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_trust_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_clarity_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_clarity_governance_watch"),
            ("revise", 0.13, "system3_clarity_governance_revise"),
        ),
    ),
    (
        "latest_system3_clarity_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_clarity_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_clarity_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_pacing_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_pacing_governance_watch"),
            ("revise", 0.13, "system3_pacing_governance_revise"),
        ),
    ),
    (
        "latest_system3_pacing_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_pacing_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_pacing_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_commitment_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_commitment_governance_watch"),
            ("revise", 0.13, "system3_commitment_governance_revise"),
        ),
    ),
    (
        "latest_system3_commitment_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_commitment_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_commitment_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_disclosure_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_disclosure_governance_watch"),
            ("revise", 0.13, "system3_disclosure_governance_revise"),
        ),
    ),
    (
        "latest_system3_disclosure_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_disclosure_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_disclosure_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_reciprocity_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_reciprocity_governance_watch"),
            ("revise", 0.13, "system3_reciprocity_governance_revise"),
        ),
    ),
    (
        "latest_system3_reciprocity_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_reciprocity_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_reciprocity_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_pressure_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_pressure_governance_watch"),
            ("revise", 0.13, "system3_pressure_governance_revise"),
        ),
    ),
    (
        "latest_system3_pressure_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_pressure_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_pressure_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_relational_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_relational_governance_watch"),
            ("revise", 0.13, "system3_relational_governance_revise"),
        ),
    ),
    (
        "latest_system3_relational_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_relational_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_relational_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_safety_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_safety_governance_watch"),
            ("revise", 0.13, "system3_safety_governance_revise"),
        ),
    ),
    (
        "latest_system3_safety_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_safety_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_safety_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_progress_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_progress_governance_watch"),
            ("revise", 0.13, "system3_progress_governance_revise"),
        ),
    ),
    (
        "latest_system3_progress_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_progress_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_progress_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_stability_governance_status",
        "pass",
        (
            ("watch", 0.05, "system3_stability_governance_watch"),
            ("revise", 0.13, "system3_stability_governance_revise"),
        ),
    ),
    (
        "latest_system3_stability_governance_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_stability_governance_trajectory_watch"),
            ("recenter", 0.1, "system3_stability_governance_trajectory_recenter"),
        ),
    ),
    (
        "latest_system3_growth_transition_status",
        "stable",
        (
            ("watch", 0.05, "system3_growth_transition_watch"),
            ("redirect", 0.12, "system3_growth_transition_redirect"),
        ),
    ),
    (
        "latest_system3_growth_transition_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_growth_transition_trajectory_watch"),
            ("redirect", 0.1, "system3_growth_transition_trajectory_redirect"),
        ),
    ),
    (
        "latest_system3_version_migration_status",
        "pass",
        (
            ("watch", 0.06, "system3_version_migration_watch"),
            ("revise", 0.14, "system3_version_migration_revise"),
        ),
    ),
    (
        "latest_system3_version_migration_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_version_migration_trajectory_watch"),
            ("hold", 0.1, "system3_version_migration_trajectory_hold"),
        ),
    ),
    (
        "latest_system3_emotional_debt_status",
        "low",
        (
            ("watch", 0.05, "system3_emotional_debt_watch"),
            ("elevated", 0.15, "system3_emotional_debt_elevated"),
        ),
    ),
    (
        "latest_system3_emotional_debt_trajectory_status",
        "stable",
        (
            ("watch", 0.04, "system3_emotional_debt_trajectory_watch"),
            (
                "decompression_required",
                0.1,
                "system3_emotional_debt_trajectory_decompression",
            ),
        ),
    ),
)

_TURN_RECORD_PAYLOAD_EVENT_FIELDS: dict[str, str] = {
    CONFIDENCE_ASSESSMENT_COMPUTED: "confidence_assessment",
    CONTEXT_FRAME_COMPUTED: "context_frame",
    RELATIONSHIP_STATE_UPDATED: "relationship_state",
    REPAIR_ASSESSMENT_COMPUTED: "repair_assessment",
    MEMORY_BUNDLE_UPDATED: "memory_bundle",
    MEMORY_WRITE_GUARD_EVALUATED: "memory_write_guard",
    MEMORY_RETENTION_POLICY_APPLIED: "memory_retention",
    MEMORY_RECALL_PERFORMED: "memory_recall",
    MEMORY_FORGETTING_APPLIED: "memory_forgetting",
    KNOWLEDGE_BOUNDARY_DECIDED: "knowledge_boundary_decision",
    POLICY_GATE_DECIDED: "policy_gate",
    REHEARSAL_COMPLETED: "rehearsal_result",
    REPAIR_PLAN_UPDATED: "repair_plan",
    EMPOWERMENT_AUDIT_COMPLETED: "empowerment_audit",
    RESPONSE_DRAFT_PLANNED: "response_draft_plan",
    RESPONSE_RENDERING_POLICY_DECIDED: "response_rendering_policy",
    RESPONSE_SEQUENCE_PLANNED: "response_sequence_plan",
    RUNTIME_COORDINATION_UPDATED: "runtime_coordination_snapshot",
    GUIDANCE_PLAN_UPDATED: "guidance_plan",
    CONVERSATION_CADENCE_UPDATED: "conversation_cadence_plan",
    SESSION_RITUAL_UPDATED: "session_ritual_plan",
    SOMATIC_ORCHESTRATION_UPDATED: "somatic_orchestration_plan",
    PROACTIVE_FOLLOWUP_UPDATED: "proactive_followup_directive",
    PROACTIVE_CADENCE_UPDATED: "proactive_cadence_plan",
    PROACTIVE_GUARDRAIL_UPDATED: "proactive_guardrail_plan",
    REENGAGEMENT_MATRIX_ASSESSED: "reengagement_matrix_assessment",
    REENGAGEMENT_PLAN_UPDATED: "reengagement_plan",
    PROACTIVE_SCHEDULING_UPDATED: "proactive_scheduling_plan",
    PROACTIVE_ORCHESTRATION_UPDATED: "proactive_orchestration_plan",
    PROACTIVE_ACTUATION_UPDATED: "proactive_actuation_plan",
    PROACTIVE_PROGRESSION_UPDATED: "proactive_progression_plan",
    PROACTIVE_STAGE_CONTROLLER_UPDATED: "proactive_stage_controller_decision",
    PROACTIVE_LINE_CONTROLLER_UPDATED: "proactive_line_controller_decision",
    PROACTIVE_LINE_STATE_UPDATED: "proactive_line_state_decision",
    PROACTIVE_LINE_TRANSITION_UPDATED: "proactive_line_transition_decision",
    PROACTIVE_LINE_MACHINE_UPDATED: "proactive_line_machine_decision",
    PROACTIVE_STAGE_REFRESH_UPDATED: "proactive_stage_refresh_plan",
    PROACTIVE_STAGE_REPLAN_UPDATED: "proactive_stage_replan_assessment",
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED: "proactive_dispatch_feedback_assessment",
    PROACTIVE_DISPATCH_GATE_UPDATED: "proactive_dispatch_gate_decision",
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED: "proactive_dispatch_envelope_decision",
    PROACTIVE_STAGE_STATE_UPDATED: "proactive_stage_state_decision",
    PROACTIVE_STAGE_TRANSITION_UPDATED: "proactive_stage_transition_decision",
    PROACTIVE_STAGE_MACHINE_UPDATED: "proactive_stage_machine_decision",
    PROACTIVE_FOLLOWUP_DISPATCHED: "proactive_followup_dispatch",
    PROACTIVE_DISPATCH_OUTCOME_RECORDED: "proactive_dispatch_outcome",
    RESPONSE_NORMALIZED: "response_normalization",
    RESPONSE_POST_AUDITED: "response_post_audit",
    RUNTIME_QUALITY_DOCTOR_COMPLETED: "runtime_quality_doctor_report",
    SYSTEM3_SNAPSHOT_UPDATED: "system3_snapshot",
    PRIVATE_JUDGMENT_COMPUTED: "private_judgment",
    LLM_COMPLETION_FAILED: "llm_failure",
}


class EvaluationService:
    def __init__(self, *, stream_service: StreamService) -> None:
        self._stream_service = stream_service

    async def evaluate_session(self, *, session_id: str) -> dict[str, Any]:
        events = await self._stream_service.read_stream(stream_id=session_id)
        if any(is_legacy_lifecycle_event_type(event.event_type) for event in events):
            raise LegacyLifecycleStreamUnsupportedError(stream_id=session_id)
        started_event = next(
            (
                event
                for event in events
                if event.event_type == SESSION_STARTED
            ),
            None,
        )
        turn_records = self._build_turn_records(events)
        started_at = started_event.payload.get("created_at") if started_event else None
        last_event_at = events[-1].occurred_at.isoformat() if events else None
        started_metadata = (
            dict(started_event.payload.get("metadata", {}))
            if started_event is not None
            else {}
        )
        summary = build_summary(
            session_id=session_id,
            turn_records=turn_records,
            event_count=len(events),
            started_at=started_at,
            last_event_at=last_event_at,
            started_metadata=started_metadata,
        )
        return {
            "session_id": session_id,
            "summary": summary,
            "turns": [record.to_dict() for record in turn_records],
        }

    async def list_session_evaluations(self) -> dict[str, Any]:
        session_ids = await self._stream_service.list_stream_ids()
        summaries = []
        for session_id in session_ids:
            events = await self._stream_service.read_stream(stream_id=session_id)
            if not any(event.event_type == SESSION_STARTED for event in events):
                continue
            if any(is_legacy_lifecycle_event_type(event.event_type) for event in events):
                continue
            evaluation = await self.evaluate_session(session_id=session_id)
            summaries.append(evaluation["summary"])
        return {
            "session_count": len(summaries),
            "sessions": summaries,
        }

    async def _list_non_scenario_session_summaries(self) -> list[dict[str, Any]]:
        evaluations_payload = await self.list_session_evaluations()
        return [
            dict(summary)
            for summary in list(evaluations_payload["sessions"])
            if summary.get("session_source") != "scenario_evaluation"
        ]

    async def build_strategy_preference_report(self) -> dict[str, Any]:
        summaries = await self._list_strategy_preference_summaries()
        records = [self._build_strategy_preference_record(summary) for summary in summaries]
        filtered_records = [record for record in records if not record.quality_floor_pass]
        noisy_records = [record for record in records if record.noise_penalty > 0]
        strategy_totals, strata_totals = self._accumulate_strategy_preference_totals(
            records
        )
        strategies = self._build_strategy_preference_strategies(strategy_totals)
        strata = self._build_strategy_preference_strata(strata_totals)

        return {
            "session_count": len(records),
            "strategy_count": len(strategies),
            "filtered_session_count": len(filtered_records),
            "noisy_session_count": len(noisy_records),
            "methodology": {
                "quality_floor_filter": (
                    "Filter out sessions with poor audit quality, low safety, severe "
                    "output degradation, or repeated runtime failures."
                ),
                "main_signal": (
                    "Prefer session duration and relational quality over raw turn count."
                ),
                "noise_control": (
                    "Penalize fast churn sessions where turn count grows without "
                    "real dwell time."
                ),
            },
            "context_strata": strata,
            "strategies": strategies,
            "filtered_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy": record.strategy,
                    "quality_floor_score": record.quality_floor_score,
                    "filtering_reasons": record.filtering_reasons,
                }
                for record in filtered_records[:5]
            ],
            "noisy_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy": record.strategy,
                    "noise_penalty": record.noise_penalty,
                    "turn_count": record.turn_count,
                    "session_duration_seconds": record.session_duration_seconds,
                }
                for record in noisy_records[:5]
            ],
            "reengagement_learning": await self.build_reengagement_learning_report(),
        }

    async def _list_strategy_preference_summaries(self) -> list[dict[str, Any]]:
        return [
            summary
            for summary in await self._list_non_scenario_session_summaries()
            if summary.get("latest_strategy")
        ]

    def _accumulate_strategy_preference_totals(
        self,
        records: list[StrategyPreferenceRecord],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
        strategy_totals: dict[str, dict[str, Any]] = {}
        strata_totals: dict[str, int] = {}
        for record in records:
            strategy_entry = strategy_totals.setdefault(
                record.strategy,
                {
                    "strategy": record.strategy,
                    "session_count": 0,
                    "kept_session_count": 0,
                    "filtered_session_count": 0,
                    "denoised_scores": [],
                    "quality_floor_scores": [],
                    "duration_signals": [],
                    "relational_signals": [],
                    "noise_penalties": [],
                    "strata": {},
                },
            )
            strategy_entry["session_count"] += 1
            if record.quality_floor_pass:
                strategy_entry["kept_session_count"] += 1
                strategy_entry["denoised_scores"].append(
                    record.denoised_preference_score
                )
            else:
                strategy_entry["filtered_session_count"] += 1
            strategy_entry["quality_floor_scores"].append(record.quality_floor_score)
            strategy_entry["duration_signals"].append(record.duration_signal)
            strategy_entry["relational_signals"].append(record.relational_signal)
            strategy_entry["noise_penalties"].append(record.noise_penalty)
            strategy_entry["strata"][record.context_stratum] = (
                strategy_entry["strata"].get(record.context_stratum, 0) + 1
            )
            strata_totals[record.context_stratum] = (
                strata_totals.get(record.context_stratum, 0) + 1
            )
        return strategy_totals, strata_totals

    def _build_strategy_preference_strategies(
        self,
        strategy_totals: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        strategies = []
        for item in strategy_totals.values():
            kept = list(item["denoised_scores"])
            strata = self._build_strategy_preference_strata(item["strata"])
            strategies.append(
                {
                    "strategy": item["strategy"],
                    "session_count": item["session_count"],
                    "kept_session_count": item["kept_session_count"],
                    "filtered_session_count": item["filtered_session_count"],
                    "avg_denoised_preference_score": (
                        round(mean(kept), 3) if kept else None
                    ),
                    "avg_quality_floor_score": round(
                        mean(item["quality_floor_scores"]),
                        3,
                    ),
                    "avg_duration_signal": round(
                        mean(item["duration_signals"]),
                        3,
                    ),
                    "avg_relational_signal": round(
                        mean(item["relational_signals"]),
                        3,
                    ),
                    "avg_noise_penalty": round(mean(item["noise_penalties"]), 3),
                    "dominant_strata": strata[:3],
                }
            )
        strategies.sort(
            key=lambda item: (
                item.get("avg_denoised_preference_score") is not None,
                float(item.get("avg_denoised_preference_score") or 0.0),
                float(item.get("avg_quality_floor_score") or 0.0),
                int(item.get("session_count") or 0),
            ),
            reverse=True,
        )
        return strategies

    def _build_strategy_preference_strata(
        self,
        strata_totals: dict[str, int],
    ) -> list[dict[str, Any]]:
        strata = [
            {"context_stratum": key, "count": value}
            for key, value in strata_totals.items()
        ]
        strata.sort(
            key=lambda item: (
                int(item.get("count") or 0),
                str(item.get("context_stratum") or ""),
            ),
            reverse=True,
        )
        return strata

    async def build_reengagement_learning_report(
        self,
        *,
        context_stratum: str | None = None,
        strategy_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        requested_strategy_keys = {
            str(item)
            for item in list(strategy_keys or [])
            if str(item or "").strip()
        }
        summaries = [
            summary
            for summary in await self._list_non_scenario_session_summaries()
            if summary.get("latest_reengagement_strategy_key")
            and summary.get("latest_reengagement_strategy_key") != "hold"
            and (
                not requested_strategy_keys
                or str(summary.get("latest_reengagement_strategy_key"))
                in requested_strategy_keys
            )
        ]
        records = [
            self._build_reengagement_preference_record(summary) for summary in summaries
        ]
        filtered_records = [record for record in records if not record.quality_floor_pass]
        noisy_records = [record for record in records if record.noise_penalty > 0]
        matching_context_records = [
            record
            for record in records
            if context_stratum and record.context_stratum == context_stratum
        ]
        strategy_totals, strata_totals = self._accumulate_reengagement_learning_totals(
            records,
            context_stratum=context_stratum,
        )
        strategies = self._build_reengagement_learning_strategies(strategy_totals)
        strata = self._build_reengagement_learning_strata(strata_totals)
        learning_mode = self._resolve_reengagement_learning_mode(
            strategies,
            context_stratum=context_stratum,
        )

        return {
            "session_count": len(records),
            "strategy_count": len(strategies),
            "filtered_session_count": len(filtered_records),
            "noisy_session_count": len(noisy_records),
            "matching_context_session_count": len(matching_context_records),
            "context_stratum": context_stratum,
            "learning_mode": learning_mode,
            "methodology": {
                "quality_floor_filter": (
                    "Filter out sessions with poor audit quality, low safety, severe "
                    "output degradation, or repeated runtime failures."
                ),
                "main_signal": (
                    "Prefer session duration and relational quality over raw turn count."
                ),
                "context_bias": (
                    "Prefer matching repair/boundary/dependency context when enough "
                    "history exists, otherwise fall back to global re-engagement signal."
                ),
            },
            "context_strata": strata,
            "strategies": strategies,
            "filtered_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy_key": record.strategy,
                    "quality_floor_score": record.quality_floor_score,
                    "filtering_reasons": record.filtering_reasons,
                }
                for record in filtered_records[:5]
            ],
            "noisy_sessions": [
                {
                    "session_id": record.session_id,
                    "strategy_key": record.strategy,
                    "noise_penalty": record.noise_penalty,
                    "turn_count": record.turn_count,
                    "session_duration_seconds": record.session_duration_seconds,
                }
                for record in noisy_records[:5]
            ],
        }

    def _accumulate_reengagement_learning_totals(
        self,
        records: list[Any],
        *,
        context_stratum: str | None,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
        strategy_totals: dict[str, dict[str, Any]] = {}
        strata_totals: dict[str, int] = {}
        for record in records:
            strategy_entry = strategy_totals.setdefault(
                record.strategy,
                {
                    "strategy_key": record.strategy,
                    "session_count": 0,
                    "kept_session_count": 0,
                    "filtered_session_count": 0,
                    "learning_scores": [],
                    "quality_floor_scores": [],
                    "duration_signals": [],
                    "relational_signals": [],
                    "noise_penalties": [],
                    "strata": {},
                    "contextual_learning_scores": [],
                    "contextual_kept_session_count": 0,
                },
            )
            strategy_entry["session_count"] += 1
            if record.quality_floor_pass:
                strategy_entry["kept_session_count"] += 1
                strategy_entry["learning_scores"].append(
                    record.denoised_preference_score
                )
                if context_stratum and record.context_stratum == context_stratum:
                    strategy_entry["contextual_learning_scores"].append(
                        record.denoised_preference_score
                    )
                    strategy_entry["contextual_kept_session_count"] += 1
            else:
                strategy_entry["filtered_session_count"] += 1
            strategy_entry["quality_floor_scores"].append(record.quality_floor_score)
            strategy_entry["duration_signals"].append(record.duration_signal)
            strategy_entry["relational_signals"].append(record.relational_signal)
            strategy_entry["noise_penalties"].append(record.noise_penalty)
            strategy_entry["strata"][record.context_stratum] = (
                strategy_entry["strata"].get(record.context_stratum, 0) + 1
            )
            strata_totals[record.context_stratum] = (
                strata_totals.get(record.context_stratum, 0) + 1
            )
        return strategy_totals, strata_totals

    def _build_reengagement_learning_strategies(
        self,
        strategy_totals: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        strategies = []
        for item in strategy_totals.values():
            strata = [
                {"context_stratum": key, "count": value}
                for key, value in item["strata"].items()
            ]
            strata.sort(
                key=lambda entry: (
                    int(entry.get("count") or 0),
                    str(entry.get("context_stratum") or ""),
                ),
                reverse=True,
            )
            learning_scores = list(item["learning_scores"])
            contextual_learning_scores = list(item["contextual_learning_scores"])
            strategies.append(
                {
                    "strategy_key": item["strategy_key"],
                    "session_count": item["session_count"],
                    "kept_session_count": item["kept_session_count"],
                    "filtered_session_count": item["filtered_session_count"],
                    "avg_learning_score": (
                        round(mean(learning_scores), 3) if learning_scores else None
                    ),
                    "avg_contextual_learning_score": (
                        round(mean(contextual_learning_scores), 3)
                        if contextual_learning_scores
                        else None
                    ),
                    "contextual_kept_session_count": item[
                        "contextual_kept_session_count"
                    ],
                    "avg_quality_floor_score": round(
                        mean(item["quality_floor_scores"]),
                        3,
                    ),
                    "avg_duration_signal": round(
                        mean(item["duration_signals"]),
                        3,
                    ),
                    "avg_relational_signal": round(
                        mean(item["relational_signals"]),
                        3,
                    ),
                    "avg_noise_penalty": round(mean(item["noise_penalties"]), 3),
                    "dominant_strata": strata[:3],
                }
            )
        strategies.sort(
            key=lambda item: (
                item.get("avg_contextual_learning_score") is not None,
                float(item.get("avg_contextual_learning_score") or 0.0),
                float(item.get("avg_learning_score") or 0.0),
                int(item.get("contextual_kept_session_count") or 0),
                int(item.get("kept_session_count") or 0),
            ),
            reverse=True,
        )
        return strategies

    def _build_reengagement_learning_strata(
        self,
        strata_totals: dict[str, int],
    ) -> list[dict[str, Any]]:
        strata = [
            {"context_stratum": key, "count": value}
            for key, value in strata_totals.items()
        ]
        strata.sort(
            key=lambda item: (
                int(item.get("count") or 0),
                str(item.get("context_stratum") or ""),
            ),
            reverse=True,
        )
        return strata

    def _resolve_reengagement_learning_mode(
        self,
        strategies: list[dict[str, Any]],
        *,
        context_stratum: str | None,
    ) -> str:
        learning_mode = "cold_start"
        if strategies:
            top_strategy = strategies[0]
            if context_stratum and int(
                top_strategy.get("contextual_kept_session_count") or 0
            ) > 0:
                learning_mode = "contextual_reinforcement"
            elif int(top_strategy.get("kept_session_count") or 0) > 0:
                learning_mode = "global_reinforcement"
        return learning_mode

    def _build_turn_records(self, events: list[StoredEvent]) -> list[TurnRecord]:
        turns: list[TurnRecord] = []
        current_turn: TurnRecord | None = None

        for event in events:
            if event.event_type == USER_MESSAGE_RECEIVED:
                current_turn = self._start_turn_record(
                    turns=turns,
                    current_turn=current_turn,
                    event=event,
                )
                continue

            if current_turn is None:
                continue

            if self._apply_turn_message_event(current_turn=current_turn, event=event):
                continue
            self._apply_turn_payload_event(current_turn=current_turn, event=event)

        if current_turn is not None:
            turns.append(current_turn)

        return turns

    def _start_turn_record(
        self,
        *,
        turns: list[TurnRecord],
        current_turn: TurnRecord | None,
        event: StoredEvent,
    ) -> TurnRecord:
        if current_turn is not None:
            turns.append(current_turn)
        return TurnRecord(
            turn_index=len(turns) + 1,
            user_message=str(event.payload.get("content", "")),
        )

    def _apply_turn_message_event(
        self,
        *,
        current_turn: TurnRecord,
        event: StoredEvent,
    ) -> bool:
        if event.event_type != ASSISTANT_MESSAGE_SENT:
            return False
        content = str(event.payload.get("content", ""))
        if str(event.payload.get("delivery_mode", "")) == "proactive_followup":
            current_turn.proactive_followup_message_event_count += 1
            if content:
                current_turn.proactive_followup_messages.append(content)
            return True
        current_turn.assistant_message_event_count += 1
        if content:
            current_turn.assistant_responses.append(content)
            current_turn.assistant_message = (
                f"{current_turn.assistant_message} {content}".strip()
                if current_turn.assistant_message
                else content
            )
        return True

    def _apply_turn_payload_event(
        self,
        *,
        current_turn: TurnRecord,
        event: StoredEvent,
    ) -> None:
        if event.event_type == PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED:
            apply_snapshot_to_turn_record(current_turn, dict(event.payload))
            return
        if event.event_type == PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED:
            current_turn.proactive_aggregate_governance_assessment = dict(event.payload)
            return
        if event.event_type == PROACTIVE_AGGREGATE_CONTROLLER_UPDATED:
            current_turn.proactive_aggregate_controller_decision = dict(event.payload)
            return
        if event.event_type == PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED:
            current_turn.proactive_orchestration_controller_decision = dict(event.payload)
            return
        if event.event_type == SESSION_DIRECTIVE_UPDATED:
            current_turn.session_directive = dict(event.payload.get("directive", {}))
            current_turn.strategy_decision = dict(event.payload.get("strategy", {}))
            return
        field_name = _TURN_RECORD_PAYLOAD_EVENT_FIELDS.get(event.event_type)
        if field_name is not None:
            setattr(current_turn, field_name, dict(event.payload))

    def _build_preference_record(
        self,
        summary: dict[str, Any],
        *,
        strategy: str,
        context_stratum: str,
    ) -> StrategyPreferenceRecord:
        session_duration_seconds = float(summary.get("session_duration_seconds") or 0.0)
        turn_count = int(summary.get("turn_count") or 0)
        bid_rate = float(summary.get("bid_turn_toward_rate") or 0.0)
        safety = float(summary.get("avg_psychological_safety") or 0.0)

        quality_floor_score = 1.0
        filtering_reasons: list[str] = []
        if int(summary.get("response_post_audit_total_violation_count") or 0) > 0:
            quality_floor_score -= 0.35
            filtering_reasons.append("post_audit_violations")
        if int(summary.get("llm_failure_count") or 0) > 0:
            quality_floor_score -= 0.2
            filtering_reasons.append("runtime_failures")
        quality_floor_score = self._apply_preference_status_penalties(
            summary=summary,
            quality_floor_score=quality_floor_score,
            filtering_reasons=filtering_reasons,
        )
        if safety and safety < 0.6:
            quality_floor_score -= 0.15
            filtering_reasons.append("low_psychological_safety")
        quality_floor_score = max(0.0, round(quality_floor_score, 3))
        quality_floor_pass = quality_floor_score >= 0.65

        duration_signal = min(session_duration_seconds / 180.0, 1.0)
        relational_signal = round((bid_rate * 0.5) + (safety * 0.5), 3)
        avg_seconds_per_turn = float(summary.get("avg_seconds_per_turn") or 0.0)
        noise_penalty = 0.0
        if turn_count >= 4 and avg_seconds_per_turn < 0.5:
            noise_penalty = 0.1

        denoised_preference_score = max(
            0.0,
            round(
                (quality_floor_score * 0.6)
                + (duration_signal * 0.25)
                + (relational_signal * 0.15)
                - noise_penalty,
                3,
            ),
        )

        return StrategyPreferenceRecord(
            session_id=str(summary.get("session_id")),
            strategy=strategy,
            source=str(summary.get("session_source") or "session"),
            turn_count=turn_count,
            session_duration_seconds=session_duration_seconds,
            duration_signal=round(duration_signal, 3),
            relational_signal=relational_signal,
            quality_floor_score=quality_floor_score,
            quality_floor_pass=quality_floor_pass,
            noise_penalty=round(noise_penalty, 3),
            denoised_preference_score=denoised_preference_score,
            context_stratum=context_stratum,
            filtering_reasons=filtering_reasons,
        )

    def _apply_preference_status_penalties(
        self,
        *,
        summary: dict[str, Any],
        quality_floor_score: float,
        filtering_reasons: list[str],
    ) -> float:
        for field_name, default_value, rules in _PREFERENCE_STATUS_RULES:
            status = str(summary.get(field_name) or default_value)
            for expected_status, penalty, reason in rules:
                if status == expected_status:
                    quality_floor_score -= penalty
                    filtering_reasons.append(reason)
                    break
        return quality_floor_score

    def _build_strategy_preference_record(
        self,
        summary: dict[str, Any],
    ) -> StrategyPreferenceRecord:
        return self._build_preference_record(
            summary,
            strategy=str(summary.get("latest_strategy") or "unknown"),
            context_stratum=self._build_strategy_context_stratum(summary),
        )

    def _build_reengagement_preference_record(
        self,
        summary: dict[str, Any],
    ) -> StrategyPreferenceRecord:
        return self._build_preference_record(
            summary,
            strategy=str(summary.get("latest_reengagement_strategy_key") or "unknown"),
            context_stratum=self._build_reengagement_context_stratum(summary),
        )

    def _build_strategy_context_stratum(
        self,
        summary: dict[str, Any],
    ) -> str:
        flags: list[str] = []
        if int(summary.get("rupture_detected_count") or 0) > 0:
            flags.append("repair_pressure")
        if int(summary.get("knowledge_boundary_intervention_count") or 0) > 0:
            flags.append("boundary_pressure")
        if int(summary.get("dependency_risk_elevated_count") or 0) > 0:
            flags.append("dependency_pressure")
        quality_status = str(summary.get("output_quality_status") or "stable")
        if quality_status in {"watch", "degrading"}:
            flags.append(f"quality_{quality_status}")
        if not flags:
            flags.append("steady_progress")
        return "+".join(flags[:3])

    def _build_reengagement_context_stratum(
        self,
        summary: dict[str, Any],
    ) -> str:
        flags: list[str] = []
        if (
            int(summary.get("rupture_detected_count") or 0) > 0
            or str(summary.get("latest_system3_repair_governance_status") or "pass")
            in {"watch", "revise"}
            or str(
                summary.get("latest_system3_repair_governance_trajectory_status")
                or "stable"
            )
            == "recenter"
            or str(summary.get("latest_reengagement_pressure_mode") or "")
            == "repair_soft"
        ):
            flags.append("repair_pressure")
        if (
            int(summary.get("knowledge_boundary_intervention_count") or 0) > 0
            or str(summary.get("latest_system3_boundary_governance_status") or "pass")
            in {"watch", "revise"}
            or str(
                summary.get("latest_system3_boundary_governance_trajectory_status")
                or "stable"
            )
            == "recenter"
        ):
            flags.append("boundary_pressure")
        if (
            int(summary.get("dependency_risk_elevated_count") or 0) > 0
            or str(summary.get("latest_system3_dependency_governance_status") or "pass")
            in {"watch", "revise"}
            or str(
                summary.get("latest_system3_dependency_governance_trajectory_status")
                or "stable"
            )
            == "recenter"
        ):
            flags.append("dependency_pressure")
        if (
            str(summary.get("latest_system3_pressure_governance_status") or "pass")
            in {"watch", "revise"}
            or str(summary.get("latest_system3_stability_governance_status") or "pass")
            in {"watch", "revise"}
        ):
            flags.append("quality_watch")
        if not flags:
            flags.append("steady_progress")
        return "+".join(flags[:3])

    async def build_dispatch_outcome_learning_report(
        self,
        *,
        context_stratum: str | None = None,
        strategy_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aggregate dispatch outcomes into a learning report.

        Reads all ``PROACTIVE_DISPATCH_OUTCOME_RECORDED`` events across
        non-scenario sessions and computes response_rate, positive_outcome_rate,
        and outcome_score per ``strategy_key x context_stratum`` combination.
        """
        requested_keys = {
            str(k) for k in (strategy_keys or []) if str(k or "").strip()
        }
        session_ids = await self._stream_service.list_stream_ids()
        outcome_events: list[dict[str, Any]] = []
        for sid in session_ids:
            events = await self._stream_service.read_stream(stream_id=sid)
            started = next(
                (e for e in events if e.event_type == SESSION_STARTED), None
            )
            if started is None:
                continue
            metadata = dict(started.payload.get("metadata", {}))
            if metadata.get("source") == "scenario_evaluation":
                continue
            for event in events:
                if event.event_type != PROACTIVE_DISPATCH_OUTCOME_RECORDED:
                    continue
                payload = dict(event.payload)
                sk = str(payload.get("strategy_key") or "")
                if not sk:
                    continue
                if requested_keys and sk not in requested_keys:
                    continue
                if (
                    context_stratum
                    and str(payload.get("context_stratum") or "") != context_stratum
                ):
                    continue
                outcome_events.append(payload)

        totals: dict[str, dict[str, Any]] = {}
        for payload in outcome_events:
            sk = str(payload["strategy_key"])
            cs = str(payload.get("context_stratum") or "steady_progress")
            key = f"{sk}::{cs}"
            entry = totals.setdefault(
                key,
                {
                    "strategy_key": sk,
                    "context_stratum": cs,
                    "total": 0,
                    "responded": 0,
                    "ignored": 0,
                    "negative_signal": 0,
                    "quality_signals": [],
                    "latencies": [],
                },
            )
            entry["total"] += 1
            otype = str(payload.get("outcome_type") or "ignored")
            if otype in entry:
                entry[otype] += 1
            qs = payload.get("quality_signal")
            if qs is not None:
                entry["quality_signals"].append(float(qs))
            lat = payload.get("response_latency_seconds")
            if lat is not None:
                entry["latencies"].append(float(lat))

        strategies: list[dict[str, Any]] = []
        for entry in totals.values():
            total = entry["total"]
            responded = entry["responded"]
            negative = entry["negative_signal"]
            response_rate = responded / total if total else 0.0
            positive_outcome_rate = (
                (responded - negative) / total if total else 0.0
            )
            avg_quality = (
                round(mean(entry["quality_signals"]), 3)
                if entry["quality_signals"]
                else None
            )
            avg_latency = (
                round(mean(entry["latencies"]), 1)
                if entry["latencies"]
                else None
            )
            outcome_score = round(
                response_rate * 0.5 + max(0.0, positive_outcome_rate) * 0.5,
                3,
            )
            strategies.append(
                {
                    "strategy_key": entry["strategy_key"],
                    "context_stratum": entry["context_stratum"],
                    "total_dispatches": total,
                    "responded_count": responded,
                    "ignored_count": entry["ignored"],
                    "negative_signal_count": negative,
                    "response_rate": round(response_rate, 3),
                    "positive_outcome_rate": round(max(0.0, positive_outcome_rate), 3),
                    "outcome_score": outcome_score,
                    "avg_quality_signal": avg_quality,
                    "avg_response_latency_seconds": avg_latency,
                }
            )
        strategies.sort(
            key=lambda s: (s["outcome_score"], s["total_dispatches"]),
            reverse=True,
        )
        total_dispatches = sum(s["total_dispatches"] for s in strategies)
        total_responded = sum(s["responded_count"] for s in strategies)
        return {
            "total_dispatches": total_dispatches,
            "total_responded": total_responded,
            "overall_response_rate": (
                round(total_responded / total_dispatches, 3) if total_dispatches else 0.0
            ),
            "strategy_count": len(strategies),
            "context_stratum_filter": context_stratum,
            "strategies": strategies,
        }

    async def build_stage_parameter_learning_report(
        self,
        *,
        context_stratum: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate dispatch outcomes by stage_label to learn per-stage parameters.

        Groups ``PROACTIVE_DISPATCH_OUTCOME_RECORDED`` and nearby
        ``PROACTIVE_FOLLOWUP_DISPATCHED`` events by ``stage_label x context_stratum``
        and computes recommended delay, delivery_mode, pressure_mode, and confidence.
        """
        session_ids = await self._stream_service.list_stream_ids()

        GroupKey = tuple[str, str]
        outcome_groups: dict[GroupKey, list[dict[str, Any]]] = defaultdict(list)
        dispatch_events_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for sid in session_ids:
            events = await self._stream_service.read_stream(stream_id=sid)
            started = next(
                (e for e in events if e.event_type == SESSION_STARTED), None
            )
            if started is None:
                continue
            metadata = dict(started.payload.get("metadata", {}))
            if metadata.get("source") == "scenario_evaluation":
                continue

            for event in events:
                if event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED:
                    dispatch_events_by_session[sid].append(dict(event.payload))
                elif event.event_type == PROACTIVE_DISPATCH_OUTCOME_RECORDED:
                    payload = dict(event.payload)
                    sl = str(payload.get("stage_label") or "")
                    if not sl:
                        continue
                    cs = str(payload.get("context_stratum") or "steady_progress")
                    if context_stratum and cs != context_stratum:
                        continue
                    payload["_session_id"] = sid
                    outcome_groups[(sl, cs)].append(payload)

        stages: list[dict[str, Any]] = []
        for (stage_label, cs), outcomes in outcome_groups.items():
            responded_outcomes = [
                o for o in outcomes if str(o.get("outcome_type")) == "responded"
            ]
            responded_count = len(responded_outcomes)
            sample_count = len(outcomes)

            latencies = [
                float(o["response_latency_seconds"])
                for o in responded_outcomes
                if o.get("response_latency_seconds") is not None
            ]
            avg_latency = mean(latencies) if latencies else 0.0
            if avg_latency > 7200:
                learned_extra_delay = 1200
            elif avg_latency > 3600:
                learned_extra_delay = 600
            else:
                learned_extra_delay = 0

            delivery_mode_counts: dict[str, dict[str, int]] = defaultdict(
                lambda: {"total": 0, "responded": 0}
            )
            pressure_mode_counts: dict[str, dict[str, int]] = defaultdict(
                lambda: {"total": 0, "responded": 0}
            )
            responded_dispatch_ids = {
                str(o.get("dispatch_event_id"))
                for o in responded_outcomes
                if o.get("dispatch_event_id")
            }
            for outcome in outcomes:
                sid = outcome.get("_session_id", "")
                dispatch_id = str(outcome.get("dispatch_event_id") or "")
                dispatches = dispatch_events_by_session.get(sid, [])
                matched = next(
                    (
                        d
                        for d in dispatches
                        if str(d.get("dispatch_event_id") or d.get("event_id") or "") == dispatch_id
                    ),
                    None,
                )
                if matched is None:
                    continue
                dm = str(matched.get("delivery_mode") or "none")
                pm = str(matched.get("pressure_mode") or "none")
                delivery_mode_counts[dm]["total"] += 1
                pressure_mode_counts[pm]["total"] += 1
                if dispatch_id in responded_dispatch_ids:
                    delivery_mode_counts[dm]["responded"] += 1
                    pressure_mode_counts[pm]["responded"] += 1

            learned_delivery_mode = "none"
            best_dm_rate = -1.0
            for dm, counts in delivery_mode_counts.items():
                rate = counts["responded"] / counts["total"] if counts["total"] else 0.0
                if rate > best_dm_rate or (rate == best_dm_rate and counts["total"] > 0):
                    best_dm_rate = rate
                    learned_delivery_mode = dm

            learned_pressure_mode = "none"
            best_pm_rate = -1.0
            for pm, counts in pressure_mode_counts.items():
                rate = counts["responded"] / counts["total"] if counts["total"] else 0.0
                if rate > best_pm_rate or (rate == best_pm_rate and counts["total"] > 0):
                    best_pm_rate = rate
                    learned_pressure_mode = pm

            confidence = round(min(1.0, responded_count / 10.0), 3)

            stages.append(
                {
                    "stage_label": stage_label,
                    "context_stratum": cs,
                    "learned_extra_delay_seconds": learned_extra_delay,
                    "learned_delivery_mode": learned_delivery_mode,
                    "learned_pressure_mode": learned_pressure_mode,
                    "confidence": confidence,
                    "sample_count": sample_count,
                }
            )

        stages.sort(
            key=lambda s: (s["confidence"], s["sample_count"]),
            reverse=True,
        )
        return {
            "stage_count": len(stages),
            "context_stratum_filter": context_stratum,
            "stages": stages,
        }
