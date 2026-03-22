"""EvaluationService — orchestrates session evaluation, preference reports, and learning."""

from __future__ import annotations

from statistics import mean
from typing import Any

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
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_GUARDRAIL_UPDATED,
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


class EvaluationService:
    def __init__(self, *, stream_service: StreamService) -> None:
        self._stream_service = stream_service

    async def evaluate_session(self, *, session_id: str) -> dict[str, Any]:
        events = await self._stream_service.read_stream(stream_id=session_id)
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
        summaries = [
            summary
            for summary in await self._list_non_scenario_session_summaries()
            if summary.get("latest_strategy")
        ]
        records = [self._build_strategy_preference_record(summary) for summary in summaries]

        strategy_totals: dict[str, dict[str, Any]] = {}
        strata_totals: dict[str, int] = {}
        filtered_records = [record for record in records if not record.quality_floor_pass]
        noisy_records = [record for record in records if record.noise_penalty > 0]

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

        strategies = []
        for item in strategy_totals.values():
            kept = list(item["denoised_scores"])
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

        learning_mode = "cold_start"
        if strategies:
            top_strategy = strategies[0]
            if context_stratum and int(
                top_strategy.get("contextual_kept_session_count") or 0
            ) > 0:
                learning_mode = "contextual_reinforcement"
            elif int(top_strategy.get("kept_session_count") or 0) > 0:
                learning_mode = "global_reinforcement"

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

    def _build_turn_records(self, events: list[StoredEvent]) -> list[TurnRecord]:
        turns: list[TurnRecord] = []
        current_turn: TurnRecord | None = None

        for event in events:
            if event.event_type == USER_MESSAGE_RECEIVED:
                if current_turn is not None:
                    turns.append(current_turn)
                current_turn = TurnRecord(
                    turn_index=len(turns) + 1,
                    user_message=str(event.payload.get("content", "")),
                )
                continue

            if current_turn is None:
                continue

            if event.event_type == ASSISTANT_MESSAGE_SENT:
                content = str(event.payload.get("content", ""))
                if str(event.payload.get("delivery_mode", "")) == "proactive_followup":
                    current_turn.proactive_followup_message_event_count += 1
                    if content:
                        current_turn.proactive_followup_messages.append(content)
                    continue
                current_turn.assistant_message_event_count += 1
                if content:
                    current_turn.assistant_responses.append(content)
                    current_turn.assistant_message = (
                        f"{current_turn.assistant_message} {content}".strip()
                        if current_turn.assistant_message
                        else content
                    )
            elif event.event_type == CONFIDENCE_ASSESSMENT_COMPUTED:
                current_turn.confidence_assessment = dict(event.payload)
            elif event.event_type == CONTEXT_FRAME_COMPUTED:
                current_turn.context_frame = dict(event.payload)
            elif event.event_type == RELATIONSHIP_STATE_UPDATED:
                current_turn.relationship_state = dict(event.payload)
            elif event.event_type == REPAIR_ASSESSMENT_COMPUTED:
                current_turn.repair_assessment = dict(event.payload)
            elif event.event_type == MEMORY_BUNDLE_UPDATED:
                current_turn.memory_bundle = dict(event.payload)
            elif event.event_type == MEMORY_WRITE_GUARD_EVALUATED:
                current_turn.memory_write_guard = dict(event.payload)
            elif event.event_type == MEMORY_RETENTION_POLICY_APPLIED:
                current_turn.memory_retention = dict(event.payload)
            elif event.event_type == MEMORY_RECALL_PERFORMED:
                current_turn.memory_recall = dict(event.payload)
            elif event.event_type == MEMORY_FORGETTING_APPLIED:
                current_turn.memory_forgetting = dict(event.payload)
            elif event.event_type == KNOWLEDGE_BOUNDARY_DECIDED:
                current_turn.knowledge_boundary_decision = dict(event.payload)
            elif event.event_type == POLICY_GATE_DECIDED:
                current_turn.policy_gate = dict(event.payload)
            elif event.event_type == REHEARSAL_COMPLETED:
                current_turn.rehearsal_result = dict(event.payload)
            elif event.event_type == REPAIR_PLAN_UPDATED:
                current_turn.repair_plan = dict(event.payload)
            elif event.event_type == EMPOWERMENT_AUDIT_COMPLETED:
                current_turn.empowerment_audit = dict(event.payload)
            elif event.event_type == RESPONSE_DRAFT_PLANNED:
                current_turn.response_draft_plan = dict(event.payload)
            elif event.event_type == RESPONSE_RENDERING_POLICY_DECIDED:
                current_turn.response_rendering_policy = dict(event.payload)
            elif event.event_type == RESPONSE_SEQUENCE_PLANNED:
                current_turn.response_sequence_plan = dict(event.payload)
            elif event.event_type == RUNTIME_COORDINATION_UPDATED:
                current_turn.runtime_coordination_snapshot = dict(event.payload)
            elif event.event_type == GUIDANCE_PLAN_UPDATED:
                current_turn.guidance_plan = dict(event.payload)
            elif event.event_type == CONVERSATION_CADENCE_UPDATED:
                current_turn.conversation_cadence_plan = dict(event.payload)
            elif event.event_type == SESSION_RITUAL_UPDATED:
                current_turn.session_ritual_plan = dict(event.payload)
            elif event.event_type == SOMATIC_ORCHESTRATION_UPDATED:
                current_turn.somatic_orchestration_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_FOLLOWUP_UPDATED:
                current_turn.proactive_followup_directive = dict(event.payload)
            elif event.event_type == PROACTIVE_CADENCE_UPDATED:
                current_turn.proactive_cadence_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED:
                current_turn.proactive_aggregate_governance_assessment = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_AGGREGATE_CONTROLLER_UPDATED:
                current_turn.proactive_aggregate_controller_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED:
                current_turn.proactive_orchestration_controller_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_GUARDRAIL_UPDATED:
                current_turn.proactive_guardrail_plan = dict(event.payload)
            elif event.event_type == REENGAGEMENT_MATRIX_ASSESSED:
                current_turn.reengagement_matrix_assessment = dict(event.payload)
            elif event.event_type == REENGAGEMENT_PLAN_UPDATED:
                current_turn.reengagement_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_SCHEDULING_UPDATED:
                current_turn.proactive_scheduling_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_ORCHESTRATION_UPDATED:
                current_turn.proactive_orchestration_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_ACTUATION_UPDATED:
                current_turn.proactive_actuation_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_PROGRESSION_UPDATED:
                current_turn.proactive_progression_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_CONTROLLER_UPDATED:
                current_turn.proactive_stage_controller_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_CONTROLLER_UPDATED:
                current_turn.proactive_line_controller_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_STATE_UPDATED:
                current_turn.proactive_line_state_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_TRANSITION_UPDATED:
                current_turn.proactive_line_transition_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LINE_MACHINE_UPDATED:
                current_turn.proactive_line_machine_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_STATE_UPDATED:
                current_turn.proactive_lifecycle_state_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_TRANSITION_UPDATED:
                current_turn.proactive_lifecycle_transition_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_MACHINE_UPDATED:
                current_turn.proactive_lifecycle_machine_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_CONTROLLER_UPDATED:
                current_turn.proactive_lifecycle_controller_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ENVELOPE_UPDATED:
                current_turn.proactive_lifecycle_envelope_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SCHEDULER_UPDATED:
                current_turn.proactive_lifecycle_scheduler_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_WINDOW_UPDATED:
                current_turn.proactive_lifecycle_window_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_QUEUE_UPDATED:
                current_turn.proactive_lifecycle_queue_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_DISPATCH_UPDATED:
                current_turn.proactive_lifecycle_dispatch_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_OUTCOME_UPDATED:
                current_turn.proactive_lifecycle_outcome_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_RESOLUTION_UPDATED:
                current_turn.proactive_lifecycle_resolution_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ACTIVATION_UPDATED:
                current_turn.proactive_lifecycle_activation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SETTLEMENT_UPDATED:
                current_turn.proactive_lifecycle_settlement_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CLOSURE_UPDATED:
                current_turn.proactive_lifecycle_closure_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_AVAILABILITY_UPDATED:
                current_turn.proactive_lifecycle_availability_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RETENTION_UPDATED:
                current_turn.proactive_lifecycle_retention_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ELIGIBILITY_UPDATED:
                current_turn.proactive_lifecycle_eligibility_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CANDIDATE_UPDATED:
                current_turn.proactive_lifecycle_candidate_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SELECTABILITY_UPDATED:
                current_turn.proactive_lifecycle_selectability_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_REENTRY_UPDATED:
                current_turn.proactive_lifecycle_reentry_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_REACTIVATION_UPDATED:
                current_turn.proactive_lifecycle_reactivation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RESUMPTION_UPDATED:
                current_turn.proactive_lifecycle_resumption_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_READINESS_UPDATED:
                current_turn.proactive_lifecycle_readiness_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ARMING_UPDATED:
                current_turn.proactive_lifecycle_arming_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_TRIGGER_UPDATED:
                current_turn.proactive_lifecycle_trigger_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_LAUNCH_UPDATED:
                current_turn.proactive_lifecycle_launch_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_HANDOFF_UPDATED:
                current_turn.proactive_lifecycle_handoff_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CONTINUATION_UPDATED:
                current_turn.proactive_lifecycle_continuation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_SUSTAINMENT_UPDATED:
                current_turn.proactive_lifecycle_sustainment_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_STEWARDSHIP_UPDATED:
                current_turn.proactive_lifecycle_stewardship_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_GUARDIANSHIP_UPDATED:
                current_turn.proactive_lifecycle_guardianship_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_OVERSIGHT_UPDATED:
                current_turn.proactive_lifecycle_oversight_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ASSURANCE_UPDATED:
                current_turn.proactive_lifecycle_assurance_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ATTESTATION_UPDATED:
                current_turn.proactive_lifecycle_attestation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_VERIFICATION_UPDATED:
                current_turn.proactive_lifecycle_verification_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CERTIFICATION_UPDATED:
                current_turn.proactive_lifecycle_certification_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CONFIRMATION_UPDATED:
                current_turn.proactive_lifecycle_confirmation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RATIFICATION_UPDATED:
                current_turn.proactive_lifecycle_ratification_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ENDORSEMENT_UPDATED:
                current_turn.proactive_lifecycle_endorsement_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_AUTHORIZATION_UPDATED:
                current_turn.proactive_lifecycle_authorization_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ENACTMENT_UPDATED:
                current_turn.proactive_lifecycle_enactment_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_FINALITY_UPDATED:
                current_turn.proactive_lifecycle_finality_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_COMPLETION_UPDATED:
                current_turn.proactive_lifecycle_completion_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_CONCLUSION_UPDATED:
                current_turn.proactive_lifecycle_conclusion_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_DISPOSITION_UPDATED:
                current_turn.proactive_lifecycle_disposition_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_STANDING_UPDATED:
                current_turn.proactive_lifecycle_standing_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_RESIDENCY_UPDATED:
                current_turn.proactive_lifecycle_residency_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_TENURE_UPDATED:
                current_turn.proactive_lifecycle_tenure_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_PERSISTENCE_UPDATED:
                current_turn.proactive_lifecycle_persistence_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_LONGEVITY_UPDATED:
                current_turn.proactive_lifecycle_longevity_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_LEGACY_UPDATED:
                current_turn.proactive_lifecycle_legacy_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_HERITAGE_UPDATED:
                current_turn.proactive_lifecycle_heritage_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_LINEAGE_UPDATED:
                current_turn.proactive_lifecycle_lineage_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_ANCESTRY_UPDATED:
                current_turn.proactive_lifecycle_ancestry_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_PROVENANCE_UPDATED:
                current_turn.proactive_lifecycle_provenance_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_ORIGIN_UPDATED:
                current_turn.proactive_lifecycle_origin_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_ROOT_UPDATED:
                current_turn.proactive_lifecycle_root_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_FOUNDATION_UPDATED:
                current_turn.proactive_lifecycle_foundation_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_LIFECYCLE_BEDROCK_UPDATED:
                current_turn.proactive_lifecycle_bedrock_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_SUBSTRATE_UPDATED:
                current_turn.proactive_lifecycle_substrate_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_STRATUM_UPDATED:
                current_turn.proactive_lifecycle_stratum_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_LAYER_UPDATED:
                current_turn.proactive_lifecycle_layer_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_LIFECYCLE_DURABILITY_UPDATED:
                current_turn.proactive_lifecycle_durability_decision = dict(
                    event.payload
                )
            elif event.event_type == PROACTIVE_STAGE_REFRESH_UPDATED:
                current_turn.proactive_stage_refresh_plan = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_REPLAN_UPDATED:
                current_turn.proactive_stage_replan_assessment = dict(event.payload)
            elif event.event_type == PROACTIVE_DISPATCH_FEEDBACK_ASSESSED:
                current_turn.proactive_dispatch_feedback_assessment = dict(event.payload)
            elif event.event_type == PROACTIVE_DISPATCH_GATE_UPDATED:
                current_turn.proactive_dispatch_gate_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_DISPATCH_ENVELOPE_UPDATED:
                current_turn.proactive_dispatch_envelope_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_STATE_UPDATED:
                current_turn.proactive_stage_state_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_TRANSITION_UPDATED:
                current_turn.proactive_stage_transition_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_STAGE_MACHINE_UPDATED:
                current_turn.proactive_stage_machine_decision = dict(event.payload)
            elif event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED:
                current_turn.proactive_followup_dispatch = dict(event.payload)
            elif event.event_type == RESPONSE_NORMALIZED:
                current_turn.response_normalization = dict(event.payload)
            elif event.event_type == RESPONSE_POST_AUDITED:
                current_turn.response_post_audit = dict(event.payload)
            elif event.event_type == RUNTIME_QUALITY_DOCTOR_COMPLETED:
                current_turn.runtime_quality_doctor_report = dict(event.payload)
            elif event.event_type == SYSTEM3_SNAPSHOT_UPDATED:
                current_turn.system3_snapshot = dict(event.payload)
            elif event.event_type == PRIVATE_JUDGMENT_COMPUTED:
                current_turn.private_judgment = dict(event.payload)
            elif event.event_type == SESSION_DIRECTIVE_UPDATED:
                current_turn.session_directive = dict(event.payload.get("directive", {}))
                current_turn.strategy_decision = dict(event.payload.get("strategy", {}))
            elif event.event_type == LLM_COMPLETION_FAILED:
                current_turn.llm_failure = dict(event.payload)

        if current_turn is not None:
            turns.append(current_turn)

        return turns

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
        quality_status = str(summary.get("output_quality_status") or "stable")
        if quality_status == "watch":
            quality_floor_score -= 0.2
            filtering_reasons.append("quality_watch")
        elif quality_status == "degrading":
            quality_floor_score -= 0.4
            filtering_reasons.append("quality_degrading")
        runtime_quality_status = str(
            summary.get("latest_runtime_quality_doctor_status") or "pass"
        )
        if runtime_quality_status == "watch":
            quality_floor_score -= 0.1
            filtering_reasons.append("runtime_quality_doctor_watch")
        elif runtime_quality_status == "revise":
            quality_floor_score -= 0.2
            filtering_reasons.append("runtime_quality_doctor_revise")
        identity_trajectory_status = str(
            summary.get("latest_system3_identity_trajectory_status") or "stable"
        )
        if identity_trajectory_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_identity_trajectory_watch")
        elif identity_trajectory_status == "recenter":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_identity_trajectory_recenter")
        strategy_audit_status = str(
            summary.get("latest_system3_strategy_audit_status") or "pass"
        )
        if strategy_audit_status == "watch":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_strategy_audit_watch")
        elif strategy_audit_status == "revise":
            quality_floor_score -= 0.2
            filtering_reasons.append("system3_strategy_audit_revise")
        strategy_audit_trajectory_status = str(
            summary.get("latest_system3_strategy_audit_trajectory_status")
            or "stable"
        )
        if strategy_audit_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_strategy_audit_trajectory_watch")
        elif strategy_audit_trajectory_status == "corrective":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_strategy_audit_trajectory_corrective")
        strategy_supervision_status = str(
            summary.get("latest_system3_strategy_supervision_status") or "pass"
        )
        if strategy_supervision_status == "watch":
            quality_floor_score -= 0.08
            filtering_reasons.append("system3_strategy_supervision_watch")
        elif strategy_supervision_status == "revise":
            quality_floor_score -= 0.18
            filtering_reasons.append("system3_strategy_supervision_revise")
        strategy_supervision_trajectory_status = str(
            summary.get("latest_system3_strategy_supervision_trajectory_status")
            or "stable"
        )
        if strategy_supervision_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_strategy_supervision_trajectory_watch")
        elif strategy_supervision_trajectory_status == "tighten":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_strategy_supervision_trajectory_tighten"
            )
        moral_reasoning_status = str(
            summary.get("latest_system3_moral_reasoning_status") or "pass"
        )
        if moral_reasoning_status == "watch":
            quality_floor_score -= 0.08
            filtering_reasons.append("system3_moral_reasoning_watch")
        elif moral_reasoning_status == "revise":
            quality_floor_score -= 0.18
            filtering_reasons.append("system3_moral_reasoning_revise")
        moral_trajectory_status = str(
            summary.get("latest_system3_moral_trajectory_status") or "stable"
        )
        if moral_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_moral_trajectory_watch")
        elif moral_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_moral_trajectory_recenter")
        user_model_evolution_status = str(
            summary.get("latest_system3_user_model_evolution_status") or "pass"
        )
        if user_model_evolution_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_user_model_evolution_watch")
        elif user_model_evolution_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_user_model_evolution_revise")
        user_model_trajectory_status = str(
            summary.get("latest_system3_user_model_trajectory_status") or "stable"
        )
        if user_model_trajectory_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_user_model_trajectory_watch")
        elif user_model_trajectory_status == "recenter":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_user_model_trajectory_recenter")
        expectation_calibration_status = str(
            summary.get("latest_system3_expectation_calibration_status") or "pass"
        )
        if expectation_calibration_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_expectation_calibration_watch")
        elif expectation_calibration_status == "revise":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_expectation_calibration_revise")
        expectation_calibration_trajectory_status = str(
            summary.get("latest_system3_expectation_calibration_trajectory_status")
            or "stable"
        )
        if expectation_calibration_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_expectation_calibration_trajectory_watch"
            )
        elif expectation_calibration_trajectory_status == "reset":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_expectation_calibration_trajectory_reset"
            )
        dependency_governance_status = str(
            summary.get("latest_system3_dependency_governance_status") or "pass"
        )
        if dependency_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_dependency_governance_watch")
        elif dependency_governance_status == "revise":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_dependency_governance_revise")
        dependency_governance_trajectory_status = str(
            summary.get("latest_system3_dependency_governance_trajectory_status")
            or "stable"
        )
        if dependency_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_dependency_governance_trajectory_watch"
            )
        elif dependency_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_dependency_governance_trajectory_recenter"
            )
        autonomy_governance_status = str(
            summary.get("latest_system3_autonomy_governance_status") or "pass"
        )
        if autonomy_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_autonomy_governance_watch")
        elif autonomy_governance_status == "revise":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_autonomy_governance_revise")
        autonomy_governance_trajectory_status = str(
            summary.get("latest_system3_autonomy_governance_trajectory_status")
            or "stable"
        )
        if autonomy_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_autonomy_governance_trajectory_watch"
            )
        elif autonomy_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_autonomy_governance_trajectory_recenter"
            )
        boundary_governance_status = str(
            summary.get("latest_system3_boundary_governance_status") or "pass"
        )
        if boundary_governance_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_boundary_governance_watch")
        elif boundary_governance_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_boundary_governance_revise")
        boundary_governance_trajectory_status = str(
            summary.get("latest_system3_boundary_governance_trajectory_status")
            or "stable"
        )
        if boundary_governance_trajectory_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append(
                "system3_boundary_governance_trajectory_watch"
            )
        elif boundary_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.11
            filtering_reasons.append(
                "system3_boundary_governance_trajectory_recenter"
            )
        support_governance_status = str(
            summary.get("latest_system3_support_governance_status") or "pass"
        )
        if support_governance_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_support_governance_watch")
        elif support_governance_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_support_governance_revise")
        support_governance_trajectory_status = str(
            summary.get("latest_system3_support_governance_trajectory_status")
            or "stable"
        )
        if support_governance_trajectory_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append(
                "system3_support_governance_trajectory_watch"
            )
        elif support_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.11
            filtering_reasons.append(
                "system3_support_governance_trajectory_recenter"
            )
        continuity_governance_status = str(
            summary.get("latest_system3_continuity_governance_status") or "pass"
        )
        if continuity_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_continuity_governance_watch")
        elif continuity_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_continuity_governance_revise")
        continuity_governance_trajectory_status = str(
            summary.get("latest_system3_continuity_governance_trajectory_status")
            or "stable"
        )
        if continuity_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_continuity_governance_trajectory_watch"
            )
        elif continuity_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_continuity_governance_trajectory_recenter"
            )
        repair_governance_status = str(
            summary.get("latest_system3_repair_governance_status") or "pass"
        )
        if repair_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_repair_governance_watch")
        elif repair_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_repair_governance_revise")
        repair_governance_trajectory_status = str(
            summary.get("latest_system3_repair_governance_trajectory_status")
            or "stable"
        )
        if repair_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_repair_governance_trajectory_watch"
            )
        elif repair_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_repair_governance_trajectory_recenter"
            )
        attunement_governance_status = str(
            summary.get("latest_system3_attunement_governance_status") or "pass"
        )
        if attunement_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_attunement_governance_watch")
        elif attunement_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_attunement_governance_revise")
        attunement_governance_trajectory_status = str(
            summary.get("latest_system3_attunement_governance_trajectory_status")
            or "stable"
        )
        if attunement_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_attunement_governance_trajectory_watch"
            )
        elif attunement_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_attunement_governance_trajectory_recenter"
            )
        trust_governance_status = str(
            summary.get("latest_system3_trust_governance_status") or "pass"
        )
        if trust_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_trust_governance_watch")
        elif trust_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_trust_governance_revise")
        trust_governance_trajectory_status = str(
            summary.get("latest_system3_trust_governance_trajectory_status")
            or "stable"
        )
        if trust_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_trust_governance_trajectory_watch"
            )
        elif trust_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_trust_governance_trajectory_recenter"
            )
        clarity_governance_status = str(
            summary.get("latest_system3_clarity_governance_status") or "pass"
        )
        if clarity_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_clarity_governance_watch")
        elif clarity_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_clarity_governance_revise")
        clarity_governance_trajectory_status = str(
            summary.get("latest_system3_clarity_governance_trajectory_status")
            or "stable"
        )
        if clarity_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_clarity_governance_trajectory_watch"
            )
        elif clarity_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_clarity_governance_trajectory_recenter"
            )
        pacing_governance_status = str(
            summary.get("latest_system3_pacing_governance_status") or "pass"
        )
        if pacing_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_pacing_governance_watch")
        elif pacing_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_pacing_governance_revise")
        pacing_governance_trajectory_status = str(
            summary.get("latest_system3_pacing_governance_trajectory_status")
            or "stable"
        )
        if pacing_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_pacing_governance_trajectory_watch"
            )
        elif pacing_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_pacing_governance_trajectory_recenter"
            )
        commitment_governance_status = str(
            summary.get("latest_system3_commitment_governance_status") or "pass"
        )
        if commitment_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_commitment_governance_watch")
        elif commitment_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_commitment_governance_revise")
        commitment_governance_trajectory_status = str(
            summary.get("latest_system3_commitment_governance_trajectory_status")
            or "stable"
        )
        if commitment_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_commitment_governance_trajectory_watch"
            )
        elif commitment_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_commitment_governance_trajectory_recenter"
            )
        disclosure_governance_status = str(
            summary.get("latest_system3_disclosure_governance_status") or "pass"
        )
        if disclosure_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_disclosure_governance_watch")
        elif disclosure_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_disclosure_governance_revise")
        disclosure_governance_trajectory_status = str(
            summary.get("latest_system3_disclosure_governance_trajectory_status")
            or "stable"
        )
        if disclosure_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_disclosure_governance_trajectory_watch"
            )
        elif disclosure_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_disclosure_governance_trajectory_recenter"
            )
        reciprocity_governance_status = str(
            summary.get("latest_system3_reciprocity_governance_status") or "pass"
        )
        if reciprocity_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_reciprocity_governance_watch")
        elif reciprocity_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_reciprocity_governance_revise")
        reciprocity_governance_trajectory_status = str(
            summary.get("latest_system3_reciprocity_governance_trajectory_status")
            or "stable"
        )
        if reciprocity_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_reciprocity_governance_trajectory_watch"
            )
        elif reciprocity_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_reciprocity_governance_trajectory_recenter"
            )
        pressure_governance_status = str(
            summary.get("latest_system3_pressure_governance_status") or "pass"
        )
        if pressure_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_pressure_governance_watch")
        elif pressure_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_pressure_governance_revise")
        pressure_governance_trajectory_status = str(
            summary.get("latest_system3_pressure_governance_trajectory_status")
            or "stable"
        )
        if pressure_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_pressure_governance_trajectory_watch"
            )
        elif pressure_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_pressure_governance_trajectory_recenter"
            )
        relational_governance_status = str(
            summary.get("latest_system3_relational_governance_status") or "pass"
        )
        if relational_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_relational_governance_watch")
        elif relational_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_relational_governance_revise")
        relational_governance_trajectory_status = str(
            summary.get("latest_system3_relational_governance_trajectory_status")
            or "stable"
        )
        if relational_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_relational_governance_trajectory_watch"
            )
        elif relational_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_relational_governance_trajectory_recenter"
            )
        safety_governance_status = str(
            summary.get("latest_system3_safety_governance_status") or "pass"
        )
        if safety_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_safety_governance_watch")
        elif safety_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_safety_governance_revise")
        safety_governance_trajectory_status = str(
            summary.get("latest_system3_safety_governance_trajectory_status")
            or "stable"
        )
        if safety_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_safety_governance_trajectory_watch"
            )
        elif safety_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_safety_governance_trajectory_recenter"
            )
        progress_governance_status = str(
            summary.get("latest_system3_progress_governance_status") or "pass"
        )
        if progress_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_progress_governance_watch")
        elif progress_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_progress_governance_revise")
        progress_governance_trajectory_status = str(
            summary.get("latest_system3_progress_governance_trajectory_status")
            or "stable"
        )
        if progress_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_progress_governance_trajectory_watch"
            )
        elif progress_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_progress_governance_trajectory_recenter"
            )
        stability_governance_status = str(
            summary.get("latest_system3_stability_governance_status") or "pass"
        )
        if stability_governance_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_stability_governance_watch")
        elif stability_governance_status == "revise":
            quality_floor_score -= 0.13
            filtering_reasons.append("system3_stability_governance_revise")
        stability_governance_trajectory_status = str(
            summary.get("latest_system3_stability_governance_trajectory_status")
            or "stable"
        )
        if stability_governance_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append(
                "system3_stability_governance_trajectory_watch"
            )
        elif stability_governance_trajectory_status == "recenter":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_stability_governance_trajectory_recenter"
            )
        growth_transition_status = str(
            summary.get("latest_system3_growth_transition_status") or "stable"
        )
        if growth_transition_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_growth_transition_watch")
        elif growth_transition_status == "redirect":
            quality_floor_score -= 0.12
            filtering_reasons.append("system3_growth_transition_redirect")
        growth_transition_trajectory_status = str(
            summary.get("latest_system3_growth_transition_trajectory_status")
            or "stable"
        )
        if growth_transition_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_growth_transition_trajectory_watch")
        elif growth_transition_trajectory_status == "redirect":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_growth_transition_trajectory_redirect")
        version_migration_status = str(
            summary.get("latest_system3_version_migration_status") or "pass"
        )
        if version_migration_status == "watch":
            quality_floor_score -= 0.06
            filtering_reasons.append("system3_version_migration_watch")
        elif version_migration_status == "revise":
            quality_floor_score -= 0.14
            filtering_reasons.append("system3_version_migration_revise")
        version_migration_trajectory_status = str(
            summary.get("latest_system3_version_migration_trajectory_status")
            or "stable"
        )
        if version_migration_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_version_migration_trajectory_watch")
        elif version_migration_trajectory_status == "hold":
            quality_floor_score -= 0.1
            filtering_reasons.append("system3_version_migration_trajectory_hold")
        emotional_debt_status = str(
            summary.get("latest_system3_emotional_debt_status") or "low"
        )
        if emotional_debt_status == "watch":
            quality_floor_score -= 0.05
            filtering_reasons.append("system3_emotional_debt_watch")
        elif emotional_debt_status == "elevated":
            quality_floor_score -= 0.15
            filtering_reasons.append("system3_emotional_debt_elevated")
        emotional_debt_trajectory_status = str(
            summary.get("latest_system3_emotional_debt_trajectory_status")
            or "stable"
        )
        if emotional_debt_trajectory_status == "watch":
            quality_floor_score -= 0.04
            filtering_reasons.append("system3_emotional_debt_trajectory_watch")
        elif emotional_debt_trajectory_status == "decompression_required":
            quality_floor_score -= 0.1
            filtering_reasons.append(
                "system3_emotional_debt_trajectory_decompression"
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

