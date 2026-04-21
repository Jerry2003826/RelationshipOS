"""Proactive follow-up dispatch handler — extracted from RuntimeService."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from relationship_os.application.analyzers import (
    build_proactive_aggregate_controller_decision,
    build_proactive_aggregate_governance_assessment,
    build_proactive_dispatch_envelope_decision,
    build_proactive_dispatch_feedback_assessment,
    build_proactive_dispatch_gate_decision,
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
from relationship_os.application.analyzers.proactive.lifecycle import (
    build_proactive_lifecycle_controller_decision,
    build_proactive_lifecycle_dispatch_decision,
    build_proactive_lifecycle_envelope_decision,
    build_proactive_lifecycle_machine_decision,
    build_proactive_lifecycle_queue_decision,
    build_proactive_lifecycle_scheduler_decision,
    build_proactive_lifecycle_state_decision,
    build_proactive_lifecycle_transition_decision,
    build_proactive_lifecycle_window_decision,
)
from relationship_os.application.analyzers.proactive.lifecycle_machine import (
    build_proactive_lifecycle_post_dispatch_chain,
    build_proactive_lifecycle_snapshot,
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
    PROACTIVE_DISPATCH_OUTCOME_RECORDED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
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
    REENGAGEMENT_MATRIX_ASSESSED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import NewEvent, StoredEvent, utc_now
from relationship_os.domain.llm import LLMClient

_POST_DISPATCH_LIFECYCLE_PHASES = (
    "activation",
    "settlement",
    "closure",
    "availability",
    "retention",
    "eligibility",
    "candidate",
    "selectability",
    "reentry",
    "reactivation",
    "resumption",
    "readiness",
    "arming",
    "trigger",
    "launch",
    "handoff",
    "continuation",
    "sustainment",
    "stewardship",
    "guardianship",
    "oversight",
    "assurance",
    "attestation",
    "verification",
    "certification",
    "confirmation",
    "ratification",
    "endorsement",
    "authorization",
    "enactment",
    "finality",
    "completion",
    "conclusion",
    "disposition",
    "standing",
    "residency",
    "tenure",
    "persistence",
    "durability",
    "longevity",
    "legacy",
    "heritage",
    "lineage",
    "ancestry",
    "provenance",
    "origin",
    "root",
    "foundation",
    "bedrock",
    "substrate",
    "stratum",
    "layer",
)

_SYSTEM3_GOVERNANCE_DOMAIN_SPECS: tuple[tuple[str, str, str], ...] = (
    ("dependency", "steady_low_dependency_support", "dependency_line_stable"),
    ("autonomy", "steady_explicit_autonomy", "autonomy_line_stable"),
    ("boundary", "steady_clear_boundary_support", "boundary_line_stable"),
    ("support", "steady_bounded_support", "support_line_stable"),
    ("continuity", "steady_contextual_continuity", "continuity_line_stable"),
    ("repair", "steady_relational_repair_posture", "repair_line_stable"),
    ("attunement", "steady_relational_attunement", "attunement_line_stable"),
    ("trust", "steady_mutual_trust_posture", "trust_line_stable"),
    ("clarity", "steady_contextual_clarity", "clarity_line_stable"),
    ("pacing", "steady_relational_pacing", "pacing_line_stable"),
    ("commitment", "steady_calibrated_commitment", "commitment_line_stable"),
    ("disclosure", "steady_transparent_disclosure", "disclosure_line_stable"),
    ("reciprocity", "steady_mutual_reciprocity", "reciprocity_line_stable"),
    ("pressure", "steady_low_pressure_support", "pressure_line_stable"),
    ("relational", "steady_bounded_relational_progress", "relational_line_stable"),
    ("safety", "steady_safe_relational_support", "safety_line_stable"),
    ("progress", "steady_bounded_progress", "progress_line_stable"),
    ("stability", "steady_bounded_relational_stability", "stability_line_stable"),
)


@dataclass(frozen=True)
class _DispatchContext:
    prior_events: list[StoredEvent]
    runtime_state: dict[str, Any]
    queue_item: dict[str, Any]
    directive: dict[str, Any]
    latest_proactive_event: StoredEvent | None
    recent_user_text: str


@dataclass(frozen=True)
class _DispatchModels:
    directive_model: ProactiveFollowupDirective
    runtime_coordination_model: RuntimeCoordinationSnapshot | None
    session_ritual_plan_model: SessionRitualPlan
    somatic_orchestration_plan_model: SomaticOrchestrationPlan
    proactive_cadence_plan_model: ProactiveCadencePlan
    reengagement_plan_model: ReengagementPlan
    proactive_scheduling_plan_model: ProactiveSchedulingPlan
    guidance_plan_model: GuidancePlan
    system3_snapshot_model: System3Snapshot
    runtime_coordination_snapshot: dict[str, Any]
    conversation_cadence_plan: dict[str, Any]
    proactive_scheduling_plan: dict[str, Any]
    proactive_guardrail_plan: dict[str, Any]
    proactive_orchestration_plan: dict[str, Any]
    proactive_actuation_plan: dict[str, Any]
    proactive_progression_plan: dict[str, Any]


@dataclass(frozen=True)
class _DispatchStageContext:
    current_stage_index: int
    current_stage_label: str
    current_stage_directive: dict[str, Any] | None
    current_stage_guardrail: dict[str, Any] | None
    current_stage_actuation: dict[str, Any] | None
    latest_dispatches_for_directive: list[StoredEvent]
    latest_gate_events_for_directive: list[StoredEvent]
    latest_stage_controller_events_for_directive: list[StoredEvent]
    latest_line_controller_events_for_directive: list[StoredEvent]
    prior_stage_controller_decision: ProactiveStageControllerDecision | None
    prior_line_controller_decision: ProactiveLineControllerDecision | None
    latest_dispatched_stage_index: int


@dataclass(frozen=True)
class _DispatchDecisionChain:
    proactive_stage_refresh_plan: Any
    proactive_dispatch_feedback_assessment: Any
    proactive_aggregate_governance_assessment: Any
    proactive_stage_replan_assessment: Any
    proactive_aggregate_controller_decision: Any
    proactive_orchestration_controller_decision: Any
    proactive_dispatch_gate_decision: Any
    proactive_stage_controller_decision: Any
    proactive_line_controller_decision: Any
    proactive_dispatch_envelope_decision: Any
    proactive_stage_state_decision: Any
    proactive_stage_transition_decision: Any
    proactive_stage_machine_decision: Any
    proactive_line_state_decision: Any
    proactive_line_transition_decision: Any
    proactive_line_machine_decision: Any
    proactive_lifecycle_state_decision: Any
    proactive_lifecycle_transition_decision: Any
    proactive_lifecycle_machine_decision: Any
    proactive_lifecycle_controller_decision: Any
    proactive_lifecycle_envelope_decision: Any
    proactive_lifecycle_scheduler_decision: Any
    proactive_lifecycle_window_decision: Any
    proactive_lifecycle_queue_decision: Any


@dataclass(frozen=True)
class _DispatchQueueContext:
    queue_status: str
    schedule_reason: str
    progression_advanced: bool


@dataclass(frozen=True)
class _DispatchPreControllerChain:
    proactive_stage_refresh_plan: Any
    proactive_dispatch_feedback_assessment: Any
    proactive_aggregate_governance_assessment: Any
    proactive_stage_replan_assessment: Any


@dataclass(frozen=True)
class _DispatchControllerChain:
    proactive_aggregate_controller_decision: Any
    proactive_orchestration_controller_decision: Any
    proactive_dispatch_gate_decision: Any
    proactive_stage_controller_decision: Any
    proactive_line_controller_decision: Any
    proactive_dispatch_envelope_decision: Any


@dataclass(frozen=True)
class _DispatchStageLineChain:
    proactive_stage_state_decision: Any
    proactive_stage_transition_decision: Any
    proactive_stage_machine_decision: Any
    proactive_line_state_decision: Any
    proactive_line_transition_decision: Any
    proactive_line_machine_decision: Any


@dataclass(frozen=True)
class _PreDispatchLifecycleBundle:
    proactive_lifecycle_state_decision: Any
    proactive_lifecycle_transition_decision: Any
    proactive_lifecycle_machine_decision: Any
    proactive_lifecycle_controller_decision: Any
    proactive_lifecycle_envelope_decision: Any
    proactive_lifecycle_scheduler_decision: Any
    proactive_lifecycle_window_decision: Any
    proactive_lifecycle_queue_decision: Any


@dataclass(frozen=True)
class _RenderedFollowup:
    effective_stage_directive: dict[str, Any]
    effective_stage_actuation: dict[str, Any]
    effective_reengagement_plan_model: ReengagementPlan
    followup_units: list[dict[str, Any]]
    followup_content: str
    prior_stage_controller_applied: bool
    prior_line_controller_applied: bool


@dataclass(frozen=True)
class _DispatchPayloadBundle:
    session_id: str
    source: str
    context: _DispatchContext
    models: _DispatchModels
    stage_context: _DispatchStageContext
    decisions: _DispatchDecisionChain
    rendered: _RenderedFollowup
    lifecycle_dispatch_decision: Any


@dataclass(frozen=True)
class _PostDispatchLifecycleBundle:
    outcome: Any
    resolution: Any
    phase_decisions: dict[str, Any]
    snapshot_decisions: dict[str, Any]


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
        runtime_projector_version: str,
        persona_text: str = "",
    ) -> None:
        self._stream_service = stream_service
        self._memory_service = memory_service
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._llm_temperature = llm_temperature
        self._runtime_projector_version = runtime_projector_version
        self._persona_text = persona_text

    async def dispatch(
        self,
        *,
        session_id: str,
        source: str,
        queue_item: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context, early_response = await self._load_dispatch_context(
            session_id=session_id,
            queue_item=queue_item,
        )
        if early_response is not None:
            return early_response

        assert context is not None
        await self._maybe_record_ignored_outcome(
            session_id=session_id,
            prior_events=context.prior_events,
        )
        models = self._build_dispatch_models(context)
        stage_context, early_response = self._resolve_dispatch_stage_context(
            context=context,
            models=models,
        )
        if early_response is not None:
            return early_response

        assert stage_context is not None
        decisions = self._build_dispatch_decision_chain(
            context=context,
            models=models,
            stage_context=stage_context,
        )
        rendered = self._render_dispatch_followup(
            context=context,
            models=models,
            stage_context=stage_context,
            decisions=decisions,
        )
        return await self._finalize_dispatch_result(
            session_id=session_id,
            source=source,
            context=context,
            models=models,
            stage_context=stage_context,
            decisions=decisions,
            rendered=rendered,
        )

    async def _maybe_record_ignored_outcome(
        self,
        *,
        session_id: str,
        prior_events: list[StoredEvent],
        ignored_threshold_seconds: float = 172800.0,
    ) -> None:
        """Record 'ignored' outcome if a prior dispatch has had no user response for too long."""
        if not prior_events:
            return
        last_dispatch = next(
            (e for e in reversed(prior_events) if e.event_type == PROACTIVE_FOLLOWUP_DISPATCHED),
            None,
        )
        if last_dispatch is None:
            return
        already_recorded = any(
            e.event_type == PROACTIVE_DISPATCH_OUTCOME_RECORDED
            and e.occurred_at > last_dispatch.occurred_at
            for e in prior_events
        )
        if already_recorded:
            return
        user_replied = any(
            e.event_type == USER_MESSAGE_RECEIVED and e.occurred_at > last_dispatch.occurred_at
            for e in prior_events
        )
        if user_replied:
            return
        gap = (utc_now() - last_dispatch.occurred_at).total_seconds()
        if gap >= ignored_threshold_seconds:
            await self.record_dispatch_outcome(
                session_id=session_id,
                outcome_type="ignored",
            )

    async def record_dispatch_outcome(
        self,
        *,
        session_id: str,
        outcome_type: str,
        response_latency_seconds: float | None = None,
        quality_signal: float | None = None,
    ) -> dict[str, Any] | None:
        """Record the outcome of a prior proactive dispatch.

        Args:
            session_id: The session that received the dispatch.
            outcome_type: One of 'responded', 'ignored', 'negative_signal'.
            response_latency_seconds: Seconds between dispatch and user response.
            quality_signal: Optional quality score for the response (0..1).

        Returns:
            The outcome payload written, or None if no pending dispatch was found.
        """
        events = await self._stream_service.read_stream(stream_id=session_id)
        if not events:
            return None

        last_dispatch = next(
            (
                event
                for event in reversed(events)
                if event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED
            ),
            None,
        )
        if last_dispatch is None:
            return None

        already_recorded = any(
            event.event_type == PROACTIVE_DISPATCH_OUTCOME_RECORDED
            and event.occurred_at > last_dispatch.occurred_at
            for event in events
        )
        if already_recorded:
            return None

        dispatch_payload = dict(last_dispatch.payload)
        strategy_key = str(dispatch_payload.get("strategy_key") or "unknown")
        stage_label = str(dispatch_payload.get("proactive_cadence_stage_label") or "first_touch")

        matrix_event = next(
            (
                event
                for event in reversed(events)
                if event.event_type == REENGAGEMENT_MATRIX_ASSESSED
                and event.occurred_at <= last_dispatch.occurred_at
            ),
            None,
        )
        context_stratum = (
            str(matrix_event.payload.get("learning_context_stratum") or "steady_progress")
            if matrix_event is not None
            else "steady_progress"
        )

        outcome_payload: dict[str, Any] = {
            "dispatch_event_id": str(last_dispatch.event_id),
            "strategy_key": strategy_key,
            "stage_label": stage_label,
            "context_stratum": context_stratum,
            "outcome_type": outcome_type,
            "response_latency_seconds": response_latency_seconds,
            "quality_signal": quality_signal,
            "dispatched_at": last_dispatch.occurred_at.isoformat(),
            "recorded_at": utc_now().isoformat(),
        }

        await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=len(events),
            events=[
                NewEvent(
                    event_type=PROACTIVE_DISPATCH_OUTCOME_RECORDED,
                    payload=outcome_payload,
                )
            ],
        )
        return outcome_payload

    async def _load_dispatch_context(
        self,
        *,
        session_id: str,
        queue_item: dict[str, Any] | None,
    ) -> tuple[_DispatchContext | None, dict[str, Any] | None]:
        prior_events = await self._stream_service.read_stream(stream_id=session_id)
        if not prior_events:
            return None, {
                "session_id": session_id,
                "dispatched": False,
                "reason": "session_not_found",
            }

        runtime_projection = self._stream_service.project_events(
            stream_id=session_id,
            events=prior_events,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )
        runtime_state = dict(runtime_projection["state"])
        archive_status = dict(runtime_state.get("archive_status") or {})
        if archive_status.get("archived"):
            return None, {
                "session_id": session_id,
                "dispatched": False,
                "reason": "session_archived",
            }

        directive = dict(runtime_state.get("proactive_followup_directive") or {})
        if not directive:
            return None, {
                "session_id": session_id,
                "dispatched": False,
                "reason": "missing_directive",
            }
        if directive.get("status") != "ready" or not bool(directive.get("eligible")):
            return None, {
                "session_id": session_id,
                "dispatched": False,
                "reason": "directive_not_ready",
            }

        resolved_queue_item = dict(queue_item or {})
        if queue_item is not None and resolved_queue_item.get("queue_status") not in {
            "due",
            "overdue",
        }:
            return None, {
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
        return _DispatchContext(
            prior_events=prior_events,
            runtime_state=runtime_state,
            queue_item=resolved_queue_item,
            directive=directive,
            latest_proactive_event=latest_proactive_event,
            recent_user_text=recent_user_text,
        ), None

    def _build_dispatch_models(self, context: _DispatchContext) -> _DispatchModels:
        runtime_coordination_snapshot = dict(
            context.runtime_state.get("runtime_coordination_snapshot") or {}
        )
        conversation_cadence_plan = dict(
            context.runtime_state.get("conversation_cadence_plan") or {}
        )
        session_ritual_plan = dict(context.runtime_state.get("session_ritual_plan") or {})
        somatic_orchestration_plan = dict(
            context.runtime_state.get("somatic_orchestration_plan") or {}
        )
        proactive_cadence_plan = dict(context.runtime_state.get("proactive_cadence_plan") or {})
        reengagement_plan = dict(context.runtime_state.get("reengagement_plan") or {})
        proactive_scheduling_plan = dict(
            context.runtime_state.get("proactive_scheduling_plan") or {}
        )
        guidance_plan_state = dict(context.runtime_state.get("guidance_plan") or {})
        system3_snapshot_state = dict(context.runtime_state.get("system3_snapshot") or {})

        directive_model = self._build_directive_model(context.directive)
        return _DispatchModels(
            directive_model=directive_model,
            runtime_coordination_model=self._build_runtime_coordination_model(
                runtime_coordination_snapshot
            ),
            session_ritual_plan_model=self._build_session_ritual_plan_model(
                session_ritual_plan=session_ritual_plan,
                runtime_coordination_snapshot=runtime_coordination_snapshot,
            ),
            somatic_orchestration_plan_model=(
                self._build_somatic_orchestration_plan_model(somatic_orchestration_plan)
            ),
            proactive_cadence_plan_model=self._build_proactive_cadence_plan_model(
                proactive_cadence_plan=proactive_cadence_plan,
                directive_model=directive_model,
            ),
            reengagement_plan_model=self._build_reengagement_plan_model(
                reengagement_plan=reengagement_plan,
                directive_model=directive_model,
            ),
            proactive_scheduling_plan_model=(
                self._build_proactive_scheduling_plan_model(
                    proactive_scheduling_plan=proactive_scheduling_plan,
                    directive_model=directive_model,
                )
            ),
            guidance_plan_model=self._build_guidance_plan_model(
                guidance_plan_state=guidance_plan_state,
                directive_model=directive_model,
            ),
            system3_snapshot_model=self._build_system3_snapshot_model(system3_snapshot_state),
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            conversation_cadence_plan=conversation_cadence_plan,
            proactive_scheduling_plan=proactive_scheduling_plan,
            proactive_guardrail_plan=dict(
                context.runtime_state.get("proactive_guardrail_plan") or {}
            ),
            proactive_orchestration_plan=dict(
                context.runtime_state.get("proactive_orchestration_plan") or {}
            ),
            proactive_actuation_plan=dict(
                context.runtime_state.get("proactive_actuation_plan") or {}
            ),
            proactive_progression_plan=dict(
                context.runtime_state.get("proactive_progression_plan") or {}
            ),
        )

    def _build_directive_model(
        self,
        directive: dict[str, Any],
    ) -> ProactiveFollowupDirective:
        return ProactiveFollowupDirective(
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

    def _build_runtime_coordination_model(
        self,
        runtime_coordination_snapshot: dict[str, Any],
    ) -> RuntimeCoordinationSnapshot | None:
        if not runtime_coordination_snapshot:
            return None
        return RuntimeCoordinationSnapshot(
            triggered_turn_index=int(
                runtime_coordination_snapshot.get("triggered_turn_index") or 0
            ),
            time_awareness_mode=str(
                runtime_coordination_snapshot.get("time_awareness_mode") or "ongoing"
            ),
            idle_gap_seconds=float(runtime_coordination_snapshot.get("idle_gap_seconds") or 0.0),
            session_age_seconds=float(
                runtime_coordination_snapshot.get("session_age_seconds") or 0.0
            ),
            ritual_phase=str(
                runtime_coordination_snapshot.get("ritual_phase") or "steady_progress"
            ),
            cognitive_load_band=str(
                runtime_coordination_snapshot.get("cognitive_load_band") or "low"
            ),
            response_budget_mode=str(
                runtime_coordination_snapshot.get("response_budget_mode") or "structured"
            ),
            proactive_followup_eligible=bool(
                runtime_coordination_snapshot.get("proactive_followup_eligible")
            ),
            proactive_style=str(runtime_coordination_snapshot.get("proactive_style") or "none"),
            somatic_cue=runtime_coordination_snapshot.get("somatic_cue"),
            coordination_notes=[
                str(item)
                for item in list(runtime_coordination_snapshot.get("coordination_notes") or [])
            ],
        )

    def _build_session_ritual_plan_model(
        self,
        *,
        session_ritual_plan: dict[str, Any],
        runtime_coordination_snapshot: dict[str, Any],
    ) -> SessionRitualPlan:
        return SessionRitualPlan(
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
            somatic_shortcut=str(session_ritual_plan.get("somatic_shortcut") or "none"),
            micro_rituals=[
                str(item) for item in list(session_ritual_plan.get("micro_rituals") or [])
            ],
            rationale=str(session_ritual_plan.get("rationale") or ""),
        )

    def _build_somatic_orchestration_plan_model(
        self,
        somatic_orchestration_plan: dict[str, Any],
    ) -> SomaticOrchestrationPlan:
        return SomaticOrchestrationPlan(
            status=str(somatic_orchestration_plan.get("status") or "not_needed"),
            cue=str(somatic_orchestration_plan.get("cue") or "none"),
            primary_mode=str(somatic_orchestration_plan.get("primary_mode") or "none"),
            body_anchor=str(somatic_orchestration_plan.get("body_anchor") or "none"),
            followup_style=str(somatic_orchestration_plan.get("followup_style") or "none"),
            allow_in_followup=bool(somatic_orchestration_plan.get("allow_in_followup")),
            micro_actions=[
                str(item) for item in list(somatic_orchestration_plan.get("micro_actions") or [])
            ],
            phrasing_guardrails=[
                str(item)
                for item in list(somatic_orchestration_plan.get("phrasing_guardrails") or [])
            ],
            rationale=str(somatic_orchestration_plan.get("rationale") or ""),
        )

    def _build_proactive_cadence_plan_model(
        self,
        *,
        proactive_cadence_plan: dict[str, Any],
        directive_model: ProactiveFollowupDirective,
    ) -> ProactiveCadencePlan:
        return ProactiveCadencePlan(
            status=str(proactive_cadence_plan.get("status") or "hold"),
            cadence_key=str(proactive_cadence_plan.get("cadence_key") or "hold"),
            stage_labels=[
                str(item) for item in list(proactive_cadence_plan.get("stage_labels") or [])
            ],
            stage_intervals_seconds=[
                max(0, int(item))
                for item in list(proactive_cadence_plan.get("stage_intervals_seconds") or [])
            ],
            window_seconds=max(0, int(proactive_cadence_plan.get("window_seconds") or 0)),
            close_after_stage_index=max(
                0,
                int(proactive_cadence_plan.get("close_after_stage_index") or 0),
            ),
            rationale=str(proactive_cadence_plan.get("rationale") or directive_model.rationale),
        )

    def _build_reengagement_plan_model(
        self,
        *,
        reengagement_plan: dict[str, Any],
        directive_model: ProactiveFollowupDirective,
    ) -> ReengagementPlan:
        return ReengagementPlan(
            status=str(reengagement_plan.get("status") or directive_model.status),
            ritual_mode=str(reengagement_plan.get("ritual_mode") or "continuity_nudge"),
            delivery_mode=str(reengagement_plan.get("delivery_mode") or "single_message"),
            strategy_key=str(reengagement_plan.get("strategy_key") or "none"),
            relational_move=str(reengagement_plan.get("relational_move") or "none"),
            pressure_mode=str(reengagement_plan.get("pressure_mode") or "none"),
            autonomy_signal=str(reengagement_plan.get("autonomy_signal") or "none"),
            sequence_objective=str(reengagement_plan.get("sequence_objective") or ""),
            somatic_action=(
                str(reengagement_plan.get("somatic_action"))
                if reengagement_plan.get("somatic_action") is not None
                else None
            ),
            segment_labels=[
                str(item) for item in list(reengagement_plan.get("segment_labels") or [])
            ],
            focus_points=[str(item) for item in list(reengagement_plan.get("focus_points") or [])],
            tone=str(reengagement_plan.get("tone") or "gentle"),
            opening_hint=str(reengagement_plan.get("opening_hint") or ""),
            closing_hint=str(reengagement_plan.get("closing_hint") or ""),
            rationale=str(reengagement_plan.get("rationale") or directive_model.rationale),
        )

    def _build_proactive_scheduling_plan_model(
        self,
        *,
        proactive_scheduling_plan: dict[str, Any],
        directive_model: ProactiveFollowupDirective,
    ) -> ProactiveSchedulingPlan:
        return ProactiveSchedulingPlan(
            status=str(proactive_scheduling_plan.get("status") or "hold"),
            scheduler_mode=str(proactive_scheduling_plan.get("scheduler_mode") or "hold"),
            min_seconds_since_last_outbound=max(
                0,
                int(proactive_scheduling_plan.get("min_seconds_since_last_outbound") or 0),
            ),
            first_touch_extra_delay_seconds=max(
                0,
                int(proactive_scheduling_plan.get("first_touch_extra_delay_seconds") or 0),
            ),
            stage_spacing_mode=str(
                proactive_scheduling_plan.get("stage_spacing_mode") or "standard"
            ),
            low_pressure_guard=str(proactive_scheduling_plan.get("low_pressure_guard") or "none"),
            scheduling_notes=[
                str(item) for item in list(proactive_scheduling_plan.get("scheduling_notes") or [])
            ],
            rationale=str(proactive_scheduling_plan.get("rationale") or directive_model.rationale),
        )

    def _build_guidance_plan_model(
        self,
        *,
        guidance_plan_state: dict[str, Any],
        directive_model: ProactiveFollowupDirective,
    ) -> GuidancePlan:
        return GuidancePlan(
            mode=str(guidance_plan_state.get("mode") or "progress_guidance"),
            lead_with=str(guidance_plan_state.get("lead_with") or "steady_next_step"),
            pacing=str(guidance_plan_state.get("pacing") or "steady"),
            step_budget=max(1, int(guidance_plan_state.get("step_budget") or 1)),
            agency_mode=str(guidance_plan_state.get("agency_mode") or "light_reentry"),
            ritual_action=str(guidance_plan_state.get("ritual_action") or ""),
            checkpoint_style=str(guidance_plan_state.get("checkpoint_style") or ""),
            handoff_mode=str(guidance_plan_state.get("handoff_mode") or ""),
            carryover_mode=str(guidance_plan_state.get("carryover_mode") or ""),
            micro_actions=[
                str(item) for item in list(guidance_plan_state.get("micro_actions") or [])
            ],
            rationale=str(guidance_plan_state.get("rationale") or directive_model.rationale),
        )

    def _state_string(
        self,
        state: dict[str, Any],
        key: str,
        *,
        default: str = "",
    ) -> str:
        return str(state.get(key) or default)

    def _state_strings(
        self,
        state: dict[str, Any],
        key: str,
    ) -> list[str]:
        return [str(item) for item in list(state.get(key) or [])]

    def _state_float(
        self,
        state: dict[str, Any],
        key: str,
        *,
        default: float = 0.0,
    ) -> float:
        return float(state.get(key) or default)

    def _build_trajectory_payload(
        self,
        *,
        state: dict[str, Any],
        prefix: str,
        target_default: str,
        trigger_default: str,
        target_fallback_keys: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        target = self._state_string(state, f"{prefix}_target")
        if not target:
            for fallback_key in target_fallback_keys:
                target = self._state_string(state, fallback_key)
                if target:
                    break
        if not target:
            target = target_default
        return {
            f"{prefix}_status": self._state_string(
                state,
                f"{prefix}_status",
                default="stable",
            ),
            f"{prefix}_target": target,
            f"{prefix}_trigger": self._state_string(
                state,
                f"{prefix}_trigger",
                default=trigger_default,
            ),
            f"{prefix}_notes": self._state_strings(state, f"{prefix}_notes"),
        }

    def _build_system3_governance_domain_payload(
        self,
        *,
        state: dict[str, Any],
        domain: str,
        target_default: str,
        trigger_default: str,
    ) -> dict[str, Any]:
        prefix = f"{domain}_governance"
        payload = {
            f"{prefix}_status": self._state_string(
                state,
                f"{prefix}_status",
                default="pass",
            ),
            f"{prefix}_target": self._state_string(
                state,
                f"{prefix}_target",
                default=target_default,
            ),
            f"{prefix}_trigger": self._state_string(
                state,
                f"{prefix}_trigger",
                default=trigger_default,
            ),
            f"{prefix}_notes": self._state_strings(state, f"{prefix}_notes"),
        }
        payload.update(
            self._build_trajectory_payload(
                state=state,
                prefix=f"{prefix}_trajectory",
                target_default=target_default,
                trigger_default=f"{prefix}_stable",
            )
        )
        return payload

    def _build_system3_snapshot_model(
        self,
        system3_snapshot_state: dict[str, Any],
    ) -> System3Snapshot:
        payload = self._build_system3_snapshot_base_payload(system3_snapshot_state)
        payload.update(self._build_system3_snapshot_trajectory_payloads(system3_snapshot_state))
        payload.update(self._build_system3_snapshot_governance_payloads(system3_snapshot_state))
        return System3Snapshot(**payload)

    def _build_system3_snapshot_base_payload(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "triggered_turn_index": max(
                0,
                int(state.get("triggered_turn_index") or 0),
            ),
            "review_focus": self._state_strings(state, "review_focus"),
        }
        payload.update(self._build_system3_snapshot_identity_payload(state))
        payload.update(self._build_system3_snapshot_strategy_payload(state))
        payload.update(self._build_system3_snapshot_moral_payload(state))
        payload.update(self._build_system3_snapshot_user_model_payload(state))
        payload.update(self._build_system3_snapshot_transition_payload(state))
        return payload

    def _build_system3_snapshot_identity_payload(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "identity_anchor": self._state_string(state, "identity_anchor"),
            "identity_consistency": self._state_string(
                state,
                "identity_consistency",
                default="stable",
            ),
            "identity_confidence": self._state_float(
                state,
                "identity_confidence",
            ),
            "growth_stage": self._state_string(
                state,
                "growth_stage",
                default="forming",
            ),
            "growth_signal": self._state_string(state, "growth_signal"),
            "user_model_confidence": self._state_float(
                state,
                "user_model_confidence",
            ),
            "user_needs": self._state_strings(state, "user_needs"),
            "user_preferences": self._state_strings(state, "user_preferences"),
            "emotional_debt_status": self._state_string(
                state,
                "emotional_debt_status",
                default="low",
            ),
            "emotional_debt_score": self._state_float(
                state,
                "emotional_debt_score",
            ),
            "debt_signals": self._state_strings(state, "debt_signals"),
        }

    def _build_system3_snapshot_strategy_payload(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "strategy_audit_status": self._state_string(
                state,
                "strategy_audit_status",
                default="pass",
            ),
            "strategy_fit": self._state_string(
                state,
                "strategy_fit",
                default="aligned",
            ),
            "strategy_audit_notes": self._state_strings(
                state,
                "strategy_audit_notes",
            ),
            "strategy_supervision_status": self._state_string(
                state,
                "strategy_supervision_status",
                default="pass",
            ),
            "strategy_supervision_mode": self._state_string(
                state,
                "strategy_supervision_mode",
                default="steady_supervision",
            ),
            "strategy_supervision_trigger": self._state_string(
                state,
                "strategy_supervision_trigger",
                default="strategy_stable",
            ),
            "strategy_supervision_notes": self._state_strings(
                state,
                "strategy_supervision_notes",
            ),
        }

    def _build_system3_snapshot_moral_payload(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "moral_reasoning_status": self._state_string(
                state,
                "moral_reasoning_status",
                default="pass",
            ),
            "moral_posture": self._state_string(
                state,
                "moral_posture",
                default="steady_progress_care",
            ),
            "moral_conflict": self._state_string(
                state,
                "moral_conflict",
                default="none",
            ),
            "moral_principles": self._state_strings(state, "moral_principles"),
            "moral_notes": self._state_strings(state, "moral_notes"),
        }

    def _build_system3_snapshot_user_model_payload(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "user_model_evolution_status": self._state_string(
                state,
                "user_model_evolution_status",
                default="pass",
            ),
            "user_model_revision_mode": self._state_string(
                state,
                "user_model_revision_mode",
                default="steady_refinement",
            ),
            "user_model_shift_signal": self._state_string(
                state,
                "user_model_shift_signal",
                default="stable",
            ),
            "user_model_evolution_notes": self._state_strings(
                state,
                "user_model_evolution_notes",
            ),
            "expectation_calibration_status": self._state_string(
                state,
                "expectation_calibration_status",
                default="pass",
            ),
            "expectation_calibration_target": self._state_string(
                state,
                "expectation_calibration_target",
                default="bounded_progress_expectation",
            ),
            "expectation_calibration_trigger": self._state_string(
                state,
                "expectation_calibration_trigger",
                default="expectation_line_stable",
            ),
            "expectation_calibration_notes": self._state_strings(
                state,
                "expectation_calibration_notes",
            ),
        }

    def _build_system3_snapshot_transition_payload(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "growth_transition_status": self._state_string(
                state,
                "growth_transition_status",
                default="stable",
            ),
            "growth_transition_target": self._state_string(
                state,
                "growth_transition_target",
                default="steadying",
            ),
            "growth_transition_trigger": self._state_string(
                state,
                "growth_transition_trigger",
                default="maintain_current_stage",
            ),
            "growth_transition_readiness": self._state_float(
                state,
                "growth_transition_readiness",
            ),
            "growth_transition_notes": self._state_strings(
                state,
                "growth_transition_notes",
            ),
            "version_migration_status": self._state_string(
                state,
                "version_migration_status",
                default="pass",
            ),
            "version_migration_scope": self._state_string(
                state,
                "version_migration_scope",
                default="stable_rebuild_ready",
            ),
            "version_migration_trigger": self._state_string(
                state,
                "version_migration_trigger",
                default="projection_rebuild_ready",
            ),
            "version_migration_notes": self._state_strings(
                state,
                "version_migration_notes",
            ),
        }

    def _build_system3_snapshot_trajectory_payloads(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for prefix, target_default, trigger_default, target_fallback_keys in (
            ("identity_trajectory", "", "identity_consistent", ("identity_anchor",)),
            ("emotional_debt_trajectory", "steady_low_debt", "debt_stable", ()),
            (
                "strategy_audit_trajectory",
                "aligned_strategy_path",
                "strategy_line_stable",
                (),
            ),
            (
                "strategy_supervision_trajectory",
                "steady_supervision",
                "strategy_supervision_stable",
                (),
            ),
            ("moral_trajectory", "steady_progress_care", "moral_line_stable", ()),
            ("user_model_trajectory", "steady_refinement", "model_stable", ()),
            (
                "expectation_calibration_trajectory",
                "bounded_progress_expectation",
                "expectation_line_stable",
                (),
            ),
            ("growth_transition_trajectory", "steadying", "growth_line_stable", ()),
            (
                "version_migration_trajectory",
                "stable_rebuild_ready",
                "migration_line_stable",
                (),
            ),
        ):
            payload.update(
                self._build_trajectory_payload(
                    state=state,
                    prefix=prefix,
                    target_default=target_default,
                    trigger_default=trigger_default,
                    target_fallback_keys=target_fallback_keys,
                )
            )
        return payload

    def _build_system3_snapshot_governance_payloads(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for domain, target_default, trigger_default in _SYSTEM3_GOVERNANCE_DOMAIN_SPECS:
            payload.update(
                self._build_system3_governance_domain_payload(
                    state=state,
                    domain=domain,
                    target_default=target_default,
                    trigger_default=trigger_default,
                )
            )
        return payload

    def _resolve_dispatch_stage_context(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
    ) -> tuple[_DispatchStageContext | None, dict[str, Any] | None]:
        current_stage_index = max(
            1,
            int(context.queue_item.get("proactive_cadence_stage_index") or 1),
        )
        current_stage_label = str(
            context.queue_item.get("proactive_cadence_stage_label") or "first_touch"
        )
        latest_dispatches_for_directive = self._filter_events_for_latest_directive(
            events=context.prior_events,
            latest_proactive_event=context.latest_proactive_event,
            event_type=PROACTIVE_FOLLOWUP_DISPATCHED,
        )
        stage_context = _DispatchStageContext(
            current_stage_index=current_stage_index,
            current_stage_label=current_stage_label,
            current_stage_directive=self._select_stage_plan_payload(
                stage_items=models.proactive_orchestration_plan.get("stage_directives"),
                stage_label=current_stage_label,
            ),
            current_stage_guardrail=self._select_stage_plan_payload(
                stage_items=models.proactive_guardrail_plan.get("stage_guardrails"),
                stage_label=current_stage_label,
            ),
            current_stage_actuation=self._select_stage_plan_payload(
                stage_items=models.proactive_actuation_plan.get("stage_actuations"),
                stage_label=current_stage_label,
            ),
            latest_dispatches_for_directive=latest_dispatches_for_directive,
            latest_gate_events_for_directive=self._filter_events_for_latest_directive(
                events=context.prior_events,
                latest_proactive_event=context.latest_proactive_event,
                event_type=PROACTIVE_DISPATCH_GATE_UPDATED,
            ),
            latest_stage_controller_events_for_directive=(
                self._filter_events_for_latest_directive(
                    events=context.prior_events,
                    latest_proactive_event=context.latest_proactive_event,
                    event_type=PROACTIVE_STAGE_CONTROLLER_UPDATED,
                )
            ),
            latest_line_controller_events_for_directive=(
                self._filter_events_for_latest_directive(
                    events=context.prior_events,
                    latest_proactive_event=context.latest_proactive_event,
                    event_type=PROACTIVE_LINE_CONTROLLER_UPDATED,
                )
            ),
            prior_stage_controller_decision=None,
            prior_line_controller_decision=None,
            latest_dispatched_stage_index=max(
                (
                    int(event.payload.get("proactive_cadence_stage_index") or 0)
                    for event in latest_dispatches_for_directive
                ),
                default=0,
            ),
        )
        prior_stage_controller_decision = self._build_prior_stage_controller_decision(
            events=stage_context.latest_stage_controller_events_for_directive,
            current_stage_label=current_stage_label,
        )
        prior_line_controller_decision = self._build_prior_line_controller_decision(
            events=stage_context.latest_line_controller_events_for_directive,
            current_stage_label=current_stage_label,
        )
        stage_context = _DispatchStageContext(
            current_stage_index=stage_context.current_stage_index,
            current_stage_label=stage_context.current_stage_label,
            current_stage_directive=stage_context.current_stage_directive,
            current_stage_guardrail=stage_context.current_stage_guardrail,
            current_stage_actuation=stage_context.current_stage_actuation,
            latest_dispatches_for_directive=stage_context.latest_dispatches_for_directive,
            latest_gate_events_for_directive=stage_context.latest_gate_events_for_directive,
            latest_stage_controller_events_for_directive=(
                stage_context.latest_stage_controller_events_for_directive
            ),
            latest_line_controller_events_for_directive=(
                stage_context.latest_line_controller_events_for_directive
            ),
            prior_stage_controller_decision=prior_stage_controller_decision,
            prior_line_controller_decision=prior_line_controller_decision,
            latest_dispatched_stage_index=stage_context.latest_dispatched_stage_index,
        )
        if stage_context.latest_dispatched_stage_index >= current_stage_index:
            return None, {
                "session_id": self._session_id_from_events(context.prior_events),
                "dispatched": False,
                "reason": "already_dispatched_for_requested_stage",
            }
        if (
            models.proactive_cadence_plan_model.close_after_stage_index > 0
            and current_stage_index > models.proactive_cadence_plan_model.close_after_stage_index
        ):
            return None, {
                "session_id": self._session_id_from_events(context.prior_events),
                "dispatched": False,
                "reason": "requested_stage_beyond_cadence",
            }
        return stage_context, None

    def _select_stage_plan_payload(
        self,
        *,
        stage_items: Any,
        stage_label: str,
    ) -> dict[str, Any] | None:
        return next(
            (
                dict(item)
                for item in list(stage_items or [])
                if str(item.get("stage_label") or "") == stage_label
            ),
            None,
        )

    def _filter_events_for_latest_directive(
        self,
        *,
        events: list[StoredEvent],
        latest_proactive_event: StoredEvent | None,
        event_type: str,
    ) -> list[StoredEvent]:
        return [
            event
            for event in events
            if event.event_type == event_type
            and latest_proactive_event is not None
            and event.occurred_at >= latest_proactive_event.occurred_at
        ]

    def _build_prior_stage_controller_decision(
        self,
        *,
        events: list[StoredEvent],
        current_stage_label: str,
    ) -> ProactiveStageControllerDecision | None:
        applicable_event = next(
            (
                event
                for event in reversed(events)
                if str(event.payload.get("target_stage_label") or "") == current_stage_label
                and str(event.payload.get("decision") or "") == "slow_next_stage"
            ),
            None,
        )
        if applicable_event is None:
            return None
        return ProactiveStageControllerDecision(**dict(applicable_event.payload))

    def _build_prior_line_controller_decision(
        self,
        *,
        events: list[StoredEvent],
        current_stage_label: str,
    ) -> ProactiveLineControllerDecision | None:
        applicable_event = next(
            (
                event
                for event in reversed(events)
                if current_stage_label in list(event.payload.get("affected_stage_labels") or [])
                and str(event.payload.get("decision") or "")
                in {"soften_remaining_line", "retire_after_close_loop"}
            ),
            None,
        )
        if applicable_event is None:
            return None
        return ProactiveLineControllerDecision(**dict(applicable_event.payload))

    def _resolve_queue_status_for_stage_state(
        self,
        *,
        queue_status: str,
        dispatch_gate_decision: Any,
    ) -> str:
        if dispatch_gate_decision.decision == "defer":
            return "scheduled"
        if dispatch_gate_decision.decision == "hold":
            return "hold"
        return queue_status

    def _build_pre_dispatch_lifecycle_bundle(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
        proactive_aggregate_controller_decision: Any,
        proactive_orchestration_controller_decision: Any,
        proactive_dispatch_gate_decision: Any,
        proactive_dispatch_envelope_decision: Any,
        proactive_line_machine_decision: Any,
        proactive_stage_machine_decision: Any,
        queue_status: str,
        schedule_reason: str,
        progression_advanced: bool,
    ) -> _PreDispatchLifecycleBundle:
        proactive_lifecycle_state_decision = build_proactive_lifecycle_state_decision(
            stage_machine_decision=proactive_stage_machine_decision,
            line_machine_decision=proactive_line_machine_decision,
            orchestration_controller_decision=(proactive_orchestration_controller_decision),
        )
        proactive_lifecycle_transition_decision = build_proactive_lifecycle_transition_decision(
            lifecycle_state_decision=proactive_lifecycle_state_decision,
        )
        proactive_lifecycle_machine_decision = build_proactive_lifecycle_machine_decision(
            lifecycle_state_decision=proactive_lifecycle_state_decision,
            lifecycle_transition_decision=proactive_lifecycle_transition_decision,
        )
        proactive_lifecycle_controller_decision = build_proactive_lifecycle_controller_decision(
            lifecycle_machine_decision=proactive_lifecycle_machine_decision,
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=(proactive_orchestration_controller_decision),
        )
        proactive_lifecycle_envelope_decision = build_proactive_lifecycle_envelope_decision(
            lifecycle_machine_decision=proactive_lifecycle_machine_decision,
            lifecycle_controller_decision=proactive_lifecycle_controller_decision,
            dispatch_envelope_decision=proactive_dispatch_envelope_decision,
        )
        proactive_lifecycle_scheduler_decision = build_proactive_lifecycle_scheduler_decision(
            lifecycle_envelope_decision=proactive_lifecycle_envelope_decision,
            proactive_scheduling_plan=models.proactive_scheduling_plan,
            dispatch_gate_decision=proactive_dispatch_gate_decision,
        )
        proactive_lifecycle_window_decision = build_proactive_lifecycle_window_decision(
            lifecycle_scheduler_decision=proactive_lifecycle_scheduler_decision,
            current_queue_status=queue_status,
            schedule_reason=schedule_reason,
            progression_action=str(
                context.queue_item.get("proactive_progression_stage_action") or "none"
            ),
            progression_advanced=progression_advanced,
        )
        proactive_lifecycle_queue_decision = build_proactive_lifecycle_queue_decision(
            lifecycle_window_decision=proactive_lifecycle_window_decision,
            current_queue_status=queue_status,
        )
        return _PreDispatchLifecycleBundle(
            proactive_lifecycle_state_decision=proactive_lifecycle_state_decision,
            proactive_lifecycle_transition_decision=(proactive_lifecycle_transition_decision),
            proactive_lifecycle_machine_decision=proactive_lifecycle_machine_decision,
            proactive_lifecycle_controller_decision=(proactive_lifecycle_controller_decision),
            proactive_lifecycle_envelope_decision=proactive_lifecycle_envelope_decision,
            proactive_lifecycle_scheduler_decision=(proactive_lifecycle_scheduler_decision),
            proactive_lifecycle_window_decision=proactive_lifecycle_window_decision,
            proactive_lifecycle_queue_decision=proactive_lifecycle_queue_decision,
        )

    def _build_dispatch_decision_chain(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
    ) -> _DispatchDecisionChain:
        queue_context = self._build_dispatch_queue_context(context)
        pre_controller_chain = self._build_dispatch_pre_controller_chain(
            context=context,
            models=models,
            stage_context=stage_context,
            queue_context=queue_context,
        )
        controller_chain = self._build_dispatch_controller_chain(
            context=context,
            models=models,
            stage_context=stage_context,
            queue_context=queue_context,
            pre_controller_chain=pre_controller_chain,
        )
        stage_line_chain = self._build_dispatch_stage_line_chain(
            context=context,
            models=models,
            stage_context=stage_context,
            queue_context=queue_context,
            controller_chain=controller_chain,
        )
        lifecycle_bundle = self._build_pre_dispatch_lifecycle_bundle(
            context=context,
            models=models,
            proactive_aggregate_controller_decision=(
                controller_chain.proactive_aggregate_controller_decision
            ),
            proactive_orchestration_controller_decision=(
                controller_chain.proactive_orchestration_controller_decision
            ),
            proactive_dispatch_gate_decision=(controller_chain.proactive_dispatch_gate_decision),
            proactive_dispatch_envelope_decision=(
                controller_chain.proactive_dispatch_envelope_decision
            ),
            proactive_line_machine_decision=stage_line_chain.proactive_line_machine_decision,
            proactive_stage_machine_decision=stage_line_chain.proactive_stage_machine_decision,
            queue_status=queue_context.queue_status,
            schedule_reason=queue_context.schedule_reason,
            progression_advanced=queue_context.progression_advanced,
        )
        return _DispatchDecisionChain(
            proactive_stage_refresh_plan=pre_controller_chain.proactive_stage_refresh_plan,
            proactive_dispatch_feedback_assessment=(
                pre_controller_chain.proactive_dispatch_feedback_assessment
            ),
            proactive_aggregate_governance_assessment=(
                pre_controller_chain.proactive_aggregate_governance_assessment
            ),
            proactive_stage_replan_assessment=(
                pre_controller_chain.proactive_stage_replan_assessment
            ),
            proactive_aggregate_controller_decision=(
                controller_chain.proactive_aggregate_controller_decision
            ),
            proactive_orchestration_controller_decision=(
                controller_chain.proactive_orchestration_controller_decision
            ),
            proactive_dispatch_gate_decision=(controller_chain.proactive_dispatch_gate_decision),
            proactive_stage_controller_decision=(
                controller_chain.proactive_stage_controller_decision
            ),
            proactive_line_controller_decision=(
                controller_chain.proactive_line_controller_decision
            ),
            proactive_dispatch_envelope_decision=(
                controller_chain.proactive_dispatch_envelope_decision
            ),
            proactive_stage_state_decision=stage_line_chain.proactive_stage_state_decision,
            proactive_stage_transition_decision=(
                stage_line_chain.proactive_stage_transition_decision
            ),
            proactive_stage_machine_decision=stage_line_chain.proactive_stage_machine_decision,
            proactive_line_state_decision=stage_line_chain.proactive_line_state_decision,
            proactive_line_transition_decision=(
                stage_line_chain.proactive_line_transition_decision
            ),
            proactive_line_machine_decision=stage_line_chain.proactive_line_machine_decision,
            proactive_lifecycle_state_decision=(
                lifecycle_bundle.proactive_lifecycle_state_decision
            ),
            proactive_lifecycle_transition_decision=(
                lifecycle_bundle.proactive_lifecycle_transition_decision
            ),
            proactive_lifecycle_machine_decision=(
                lifecycle_bundle.proactive_lifecycle_machine_decision
            ),
            proactive_lifecycle_controller_decision=(
                lifecycle_bundle.proactive_lifecycle_controller_decision
            ),
            proactive_lifecycle_envelope_decision=(
                lifecycle_bundle.proactive_lifecycle_envelope_decision
            ),
            proactive_lifecycle_scheduler_decision=(
                lifecycle_bundle.proactive_lifecycle_scheduler_decision
            ),
            proactive_lifecycle_window_decision=(
                lifecycle_bundle.proactive_lifecycle_window_decision
            ),
            proactive_lifecycle_queue_decision=(
                lifecycle_bundle.proactive_lifecycle_queue_decision
            ),
        )

    def _build_dispatch_queue_context(
        self,
        context: _DispatchContext,
    ) -> _DispatchQueueContext:
        return _DispatchQueueContext(
            queue_status=str(context.queue_item.get("queue_status") or "due"),
            schedule_reason=str(context.queue_item.get("schedule_reason") or ""),
            progression_advanced=bool(context.queue_item.get("proactive_progression_advanced")),
        )

    def _build_dispatch_pre_controller_chain(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        queue_context: _DispatchQueueContext,
    ) -> _DispatchPreControllerChain:
        proactive_stage_refresh_plan = build_proactive_stage_refresh_plan(
            directive=models.directive_model,
            guidance_plan=models.guidance_plan_model,
            system3_snapshot=models.system3_snapshot_model,
            stage_label=stage_context.current_stage_label,
            queue_status=queue_context.queue_status,
            schedule_reason=queue_context.schedule_reason,
            progression_advanced=queue_context.progression_advanced,
            stage_directive=stage_context.current_stage_directive,
            stage_actuation=stage_context.current_stage_actuation,
            prior_stage_controller_decision=stage_context.prior_stage_controller_decision,
            prior_line_controller_decision=stage_context.prior_line_controller_decision,
        )
        proactive_dispatch_feedback_assessment = build_proactive_dispatch_feedback_assessment(
            directive=models.directive_model,
            reengagement_plan=models.reengagement_plan_model,
            stage_label=stage_context.current_stage_label,
            dispatch_events_for_directive=[
                dict(event.payload) for event in stage_context.latest_dispatches_for_directive
            ],
            gate_events_for_directive=[
                dict(event.payload) for event in stage_context.latest_gate_events_for_directive
            ],
        )
        proactive_aggregate_governance_assessment = build_proactive_aggregate_governance_assessment(
            system3_snapshot=models.system3_snapshot_model
        )
        proactive_stage_replan_assessment = build_proactive_stage_replan_assessment(
            directive=models.directive_model,
            guidance_plan=models.guidance_plan_model,
            system3_snapshot=models.system3_snapshot_model,
            reengagement_plan=models.reengagement_plan_model,
            stage_refresh_plan=proactive_stage_refresh_plan,
            dispatch_feedback_assessment=proactive_dispatch_feedback_assessment,
            aggregate_governance_assessment=proactive_aggregate_governance_assessment,
            prior_stage_controller_decision=stage_context.prior_stage_controller_decision,
            prior_line_controller_decision=stage_context.prior_line_controller_decision,
        )
        return _DispatchPreControllerChain(
            proactive_stage_refresh_plan=proactive_stage_refresh_plan,
            proactive_dispatch_feedback_assessment=(proactive_dispatch_feedback_assessment),
            proactive_aggregate_governance_assessment=(proactive_aggregate_governance_assessment),
            proactive_stage_replan_assessment=proactive_stage_replan_assessment,
        )

    def _build_dispatch_controller_chain(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        queue_context: _DispatchQueueContext,
        pre_controller_chain: _DispatchPreControllerChain,
    ) -> _DispatchControllerChain:
        proactive_aggregate_controller_decision = build_proactive_aggregate_controller_decision(
            directive=models.directive_model,
            proactive_cadence_plan=models.proactive_cadence_plan_model,
            system3_snapshot=models.system3_snapshot_model,
            current_stage_label=stage_context.current_stage_label,
            current_stage_index=stage_context.current_stage_index,
            stage_replan_assessment=(pre_controller_chain.proactive_stage_replan_assessment),
            aggregate_governance_assessment=(
                pre_controller_chain.proactive_aggregate_governance_assessment
            ),
        )
        proactive_orchestration_controller_decision = (
            build_proactive_orchestration_controller_decision(
                directive=models.directive_model,
                proactive_cadence_plan=models.proactive_cadence_plan_model,
                current_stage_label=stage_context.current_stage_label,
                current_stage_index=stage_context.current_stage_index,
                stage_replan_assessment=(pre_controller_chain.proactive_stage_replan_assessment),
                guidance_plan=models.guidance_plan_model,
                session_ritual_plan=models.session_ritual_plan_model,
                somatic_orchestration_plan=models.somatic_orchestration_plan_model,
                aggregate_controller_decision=proactive_aggregate_controller_decision,
            )
        )
        proactive_dispatch_gate_decision = build_proactive_dispatch_gate_decision(
            directive=models.directive_model,
            guidance_plan=models.guidance_plan_model,
            system3_snapshot=models.system3_snapshot_model,
            stage_replan_assessment=pre_controller_chain.proactive_stage_replan_assessment,
            queue_status=queue_context.queue_status,
            schedule_reason=queue_context.schedule_reason,
            progression_advanced=queue_context.progression_advanced,
            aggregate_governance_assessment=(
                pre_controller_chain.proactive_aggregate_governance_assessment
            ),
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=proactive_orchestration_controller_decision,
            session_ritual_plan=models.session_ritual_plan_model,
            somatic_orchestration_plan=models.somatic_orchestration_plan_model,
        )
        proactive_stage_controller_decision = build_proactive_stage_controller_decision(
            directive=models.directive_model,
            proactive_cadence_plan=models.proactive_cadence_plan_model,
            guidance_plan=models.guidance_plan_model,
            system3_snapshot=models.system3_snapshot_model,
            current_stage_label=stage_context.current_stage_label,
            current_stage_index=stage_context.current_stage_index,
            stage_replan_assessment=(pre_controller_chain.proactive_stage_replan_assessment),
            dispatch_feedback_assessment=(
                pre_controller_chain.proactive_dispatch_feedback_assessment
            ),
            aggregate_governance_assessment=(
                pre_controller_chain.proactive_aggregate_governance_assessment
            ),
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=proactive_orchestration_controller_decision,
            session_ritual_plan=models.session_ritual_plan_model,
            somatic_orchestration_plan=models.somatic_orchestration_plan_model,
        )
        proactive_line_controller_decision = build_proactive_line_controller_decision(
            directive=models.directive_model,
            proactive_cadence_plan=models.proactive_cadence_plan_model,
            guidance_plan=models.guidance_plan_model,
            system3_snapshot=models.system3_snapshot_model,
            current_stage_label=stage_context.current_stage_label,
            current_stage_index=stage_context.current_stage_index,
            stage_replan_assessment=pre_controller_chain.proactive_stage_replan_assessment,
            dispatch_feedback_assessment=(
                pre_controller_chain.proactive_dispatch_feedback_assessment
            ),
            stage_controller_decision=proactive_stage_controller_decision,
            dispatch_gate_decision=proactive_dispatch_gate_decision,
            aggregate_governance_assessment=(
                pre_controller_chain.proactive_aggregate_governance_assessment
            ),
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=proactive_orchestration_controller_decision,
            session_ritual_plan=models.session_ritual_plan_model,
            somatic_orchestration_plan=models.somatic_orchestration_plan_model,
        )
        proactive_dispatch_envelope_decision = build_proactive_dispatch_envelope_decision(
            stage_label=stage_context.current_stage_label,
            current_stage_directive=stage_context.current_stage_directive,
            current_stage_actuation=stage_context.current_stage_actuation,
            stage_refresh_plan=pre_controller_chain.proactive_stage_refresh_plan,
            stage_replan_assessment=(pre_controller_chain.proactive_stage_replan_assessment),
            dispatch_feedback_assessment=(
                pre_controller_chain.proactive_dispatch_feedback_assessment
            ),
            dispatch_gate_decision=proactive_dispatch_gate_decision,
            aggregate_controller_decision=proactive_aggregate_controller_decision,
            orchestration_controller_decision=proactive_orchestration_controller_decision,
            stage_controller_decision=proactive_stage_controller_decision,
            line_controller_decision=proactive_line_controller_decision,
        )
        return _DispatchControllerChain(
            proactive_aggregate_controller_decision=(proactive_aggregate_controller_decision),
            proactive_orchestration_controller_decision=(
                proactive_orchestration_controller_decision
            ),
            proactive_dispatch_gate_decision=proactive_dispatch_gate_decision,
            proactive_stage_controller_decision=proactive_stage_controller_decision,
            proactive_line_controller_decision=proactive_line_controller_decision,
            proactive_dispatch_envelope_decision=proactive_dispatch_envelope_decision,
        )

    def _build_dispatch_stage_line_chain(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        queue_context: _DispatchQueueContext,
        controller_chain: _DispatchControllerChain,
    ) -> _DispatchStageLineChain:
        queue_status_for_stage_state = self._resolve_queue_status_for_stage_state(
            queue_status=queue_context.queue_status,
            dispatch_gate_decision=controller_chain.proactive_dispatch_gate_decision,
        )
        proactive_stage_state_decision = build_proactive_stage_state_decision(
            stage_label=stage_context.current_stage_label,
            stage_index=stage_context.current_stage_index,
            stage_count=self._resolve_stage_count(models.proactive_cadence_plan_model),
            queue_status=queue_status_for_stage_state,
            schedule_reason=queue_context.schedule_reason,
            progression_action=str(
                context.queue_item.get("proactive_progression_stage_action") or "none"
            ),
            progression_advanced=queue_context.progression_advanced,
            line_state=controller_chain.proactive_line_controller_decision.line_state,
            current_stage_delivery_mode=str(
                (stage_context.current_stage_directive or {}).get("delivery_mode")
                or "single_message"
            ),
            current_stage_autonomy_mode=str(
                (stage_context.current_stage_directive or {}).get("autonomy_mode")
                or "light_invitation"
            ),
            current_reengagement_delivery_mode=models.reengagement_plan_model.delivery_mode,
            selected_strategy_key=(
                controller_chain.proactive_dispatch_envelope_decision.selected_strategy_key
            ),
            selected_pressure_mode=(
                controller_chain.proactive_dispatch_envelope_decision.selected_pressure_mode
            ),
            selected_autonomy_signal=(
                controller_chain.proactive_dispatch_envelope_decision.selected_autonomy_signal
            ),
            dispatch_envelope_key=(
                controller_chain.proactive_dispatch_envelope_decision.envelope_key
            ),
            dispatch_envelope_decision=(
                controller_chain.proactive_dispatch_envelope_decision.decision
            ),
            dispatch_gate_decision=(controller_chain.proactive_dispatch_gate_decision.decision),
            aggregate_controller_decision=(
                controller_chain.proactive_aggregate_controller_decision.decision
            ),
            orchestration_controller_decision=(
                controller_chain.proactive_orchestration_controller_decision.decision
            ),
            stage_controller_decision=(
                controller_chain.proactive_stage_controller_decision.decision
            ),
            line_controller_decision=(controller_chain.proactive_line_controller_decision.decision),
        )
        cadence_stage_labels = list(models.proactive_cadence_plan_model.stage_labels)
        next_stage_label = (
            cadence_stage_labels[stage_context.current_stage_index]
            if 0 <= stage_context.current_stage_index < len(cadence_stage_labels)
            else None
        )
        proactive_stage_transition_decision = build_proactive_stage_transition_decision(
            stage_state_decision=proactive_stage_state_decision,
            next_stage_label=next_stage_label,
            dispatch_gate_decision=controller_chain.proactive_dispatch_gate_decision,
            dispatch_envelope_decision=(controller_chain.proactive_dispatch_envelope_decision),
            aggregate_controller_decision=(
                controller_chain.proactive_aggregate_controller_decision
            ),
            orchestration_controller_decision=(
                controller_chain.proactive_orchestration_controller_decision
            ),
            stage_controller_decision=controller_chain.proactive_stage_controller_decision,
            line_controller_decision=controller_chain.proactive_line_controller_decision,
        )
        proactive_stage_machine_decision = build_proactive_stage_machine_decision(
            stage_state_decision=proactive_stage_state_decision,
            stage_transition_decision=proactive_stage_transition_decision,
            dispatch_envelope_decision=controller_chain.proactive_dispatch_envelope_decision,
            aggregate_controller_decision=(
                controller_chain.proactive_aggregate_controller_decision
            ),
            orchestration_controller_decision=(
                controller_chain.proactive_orchestration_controller_decision
            ),
            stage_controller_decision=controller_chain.proactive_stage_controller_decision,
            line_controller_decision=controller_chain.proactive_line_controller_decision,
        )
        proactive_line_state_decision = build_proactive_line_state_decision(
            proactive_cadence_plan=models.proactive_cadence_plan_model,
            stage_machine_decision=proactive_stage_machine_decision,
            line_controller_decision=controller_chain.proactive_line_controller_decision,
        )
        proactive_line_transition_decision = build_proactive_line_transition_decision(
            line_state_decision=proactive_line_state_decision,
            stage_transition_decision=proactive_stage_transition_decision,
        )
        proactive_line_machine_decision = build_proactive_line_machine_decision(
            line_state_decision=proactive_line_state_decision,
            line_transition_decision=proactive_line_transition_decision,
        )
        return _DispatchStageLineChain(
            proactive_stage_state_decision=proactive_stage_state_decision,
            proactive_stage_transition_decision=proactive_stage_transition_decision,
            proactive_stage_machine_decision=proactive_stage_machine_decision,
            proactive_line_state_decision=proactive_line_state_decision,
            proactive_line_transition_decision=proactive_line_transition_decision,
            proactive_line_machine_decision=proactive_line_machine_decision,
        )

    def _render_dispatch_followup(
        self,
        *,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        decisions: _DispatchDecisionChain,
    ) -> _RenderedFollowup:
        effective_stage_directive = {
            **(stage_context.current_stage_directive or {}),
            "delivery_mode": (
                decisions.proactive_dispatch_envelope_decision.selected_stage_delivery_mode
            ),
            "question_mode": (
                decisions.proactive_dispatch_envelope_decision.selected_stage_question_mode
            ),
            "autonomy_mode": (
                decisions.proactive_dispatch_envelope_decision.selected_stage_autonomy_mode
            ),
            "objective": (decisions.proactive_dispatch_envelope_decision.selected_stage_objective),
        }
        effective_stage_actuation = {
            **(stage_context.current_stage_actuation or {}),
            "opening_move": (decisions.proactive_dispatch_envelope_decision.selected_opening_move),
            "bridge_move": (decisions.proactive_dispatch_envelope_decision.selected_bridge_move),
            "closing_move": (decisions.proactive_dispatch_envelope_decision.selected_closing_move),
            "continuity_anchor": (
                decisions.proactive_dispatch_envelope_decision.selected_continuity_anchor
            ),
            "somatic_mode": (decisions.proactive_dispatch_envelope_decision.selected_somatic_mode),
            "somatic_body_anchor": (
                decisions.proactive_dispatch_envelope_decision.selected_somatic_body_anchor
            ),
            "followup_style": (
                decisions.proactive_dispatch_envelope_decision.selected_followup_style
            ),
            "user_space_signal": (
                decisions.proactive_dispatch_envelope_decision.selected_user_space_signal
            ),
        }
        effective_reengagement_plan_model = ReengagementPlan(
            status=models.reengagement_plan_model.status,
            ritual_mode=decisions.proactive_dispatch_envelope_decision.selected_ritual_mode,
            delivery_mode=(
                decisions.proactive_dispatch_envelope_decision.selected_reengagement_delivery_mode
            ),
            strategy_key=decisions.proactive_dispatch_envelope_decision.selected_strategy_key,
            relational_move=(
                decisions.proactive_dispatch_envelope_decision.selected_relational_move
            ),
            pressure_mode=(decisions.proactive_dispatch_envelope_decision.selected_pressure_mode),
            autonomy_signal=(
                decisions.proactive_dispatch_envelope_decision.selected_autonomy_signal
            ),
            sequence_objective=(
                decisions.proactive_dispatch_envelope_decision.selected_sequence_objective
            ),
            somatic_action=(decisions.proactive_dispatch_envelope_decision.selected_somatic_action),
            segment_labels=list(models.reengagement_plan_model.segment_labels),
            focus_points=list(models.reengagement_plan_model.focus_points),
            tone=models.reengagement_plan_model.tone,
            opening_hint=models.reengagement_plan_model.opening_hint,
            closing_hint=models.reengagement_plan_model.closing_hint,
            rationale=models.reengagement_plan_model.rationale,
        )
        prior_stage_controller_applied = bool(
            stage_context.prior_stage_controller_decision is not None
            and stage_context.prior_stage_controller_decision.status == "active"
            and stage_context.prior_stage_controller_decision.changed
            and stage_context.prior_stage_controller_decision.decision == "slow_next_stage"
            and stage_context.prior_stage_controller_decision.target_stage_label
            == stage_context.current_stage_label
        )
        prior_line_controller_applied = bool(
            stage_context.prior_line_controller_decision is not None
            and stage_context.prior_line_controller_decision.status == "active"
            and stage_context.prior_line_controller_decision.changed
            and stage_context.prior_line_controller_decision.decision
            in {"soften_remaining_line", "retire_after_close_loop"}
            and stage_context.current_stage_label
            in stage_context.prior_line_controller_decision.affected_stage_labels
        )
        followup_units = build_reengagement_output_units(
            recent_user_text=context.recent_user_text,
            directive=models.directive_model,
            reengagement_plan=effective_reengagement_plan_model,
            session_ritual_plan=models.session_ritual_plan_model,
            somatic_orchestration_plan=models.somatic_orchestration_plan_model,
            runtime_coordination_snapshot=models.runtime_coordination_model,
            cadence_stage_label=stage_context.current_stage_label,
            cadence_stage_index=stage_context.current_stage_index,
            cadence_stage_count=self._resolve_stage_count(models.proactive_cadence_plan_model),
            stage_directive=effective_stage_directive,
            stage_actuation=effective_stage_actuation,
        )
        followup_content = " ".join(
            item["content"] for item in followup_units if item.get("content")
        ).strip()
        return _RenderedFollowup(
            effective_stage_directive=effective_stage_directive,
            effective_stage_actuation=effective_stage_actuation,
            effective_reengagement_plan_model=effective_reengagement_plan_model,
            followup_units=followup_units,
            followup_content=followup_content,
            prior_stage_controller_applied=prior_stage_controller_applied,
            prior_line_controller_applied=prior_line_controller_applied,
        )

    def _resolve_stage_count(self, proactive_cadence_plan_model: ProactiveCadencePlan) -> int:
        return max(
            1,
            proactive_cadence_plan_model.close_after_stage_index
            or len(proactive_cadence_plan_model.stage_labels)
            or 1,
        )

    def _session_id_from_events(self, events: list[StoredEvent]) -> str:
        return events[-1].stream_id if events else ""

    async def _finalize_dispatch_result(
        self,
        *,
        session_id: str,
        source: str,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        decisions: _DispatchDecisionChain,
        rendered: _RenderedFollowup,
    ) -> dict[str, Any]:
        lifecycle_dispatch_decision = build_proactive_lifecycle_dispatch_decision(
            lifecycle_queue_decision=decisions.proactive_lifecycle_queue_decision,
            dispatch_gate_decision=decisions.proactive_dispatch_gate_decision,
            current_queue_status=str(context.queue_item.get("queue_status") or "due"),
            schedule_reason=str(context.queue_item.get("schedule_reason") or ""),
            rendered_unit_count=len(rendered.followup_units),
            has_followup_content=bool(rendered.followup_content),
        )
        if lifecycle_dispatch_decision.decision not in {
            "dispatch_lifecycle_now",
            "close_loop_lifecycle_dispatch",
        }:
            return await self._finalize_skipped_dispatch(
                session_id=session_id,
                context=context,
                decisions=decisions,
                lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            )
        return await self._finalize_sent_dispatch(
            session_id=session_id,
            source=source,
            context=context,
            models=models,
            stage_context=stage_context,
            decisions=decisions,
            rendered=rendered,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
        )

    async def _finalize_skipped_dispatch(
        self,
        *,
        session_id: str,
        context: _DispatchContext,
        decisions: _DispatchDecisionChain,
        lifecycle_dispatch_decision: Any,
    ) -> dict[str, Any]:
        post_dispatch = self._build_post_dispatch_lifecycle(
            context=context,
            decisions=decisions,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            dispatched=False,
            message_event_count=0,
        )
        stored_events = await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=len(context.prior_events),
            events=self._build_common_dispatch_events(
                proactive_stage_refresh_plan=decisions.proactive_stage_refresh_plan,
                proactive_aggregate_governance_assessment=(
                    decisions.proactive_aggregate_governance_assessment
                ),
                proactive_aggregate_controller_decision=(
                    decisions.proactive_aggregate_controller_decision
                ),
                proactive_orchestration_controller_decision=(
                    decisions.proactive_orchestration_controller_decision
                ),
                proactive_stage_replan_assessment=(decisions.proactive_stage_replan_assessment),
                proactive_stage_controller_decision=(decisions.proactive_stage_controller_decision),
                proactive_line_controller_decision=(decisions.proactive_line_controller_decision),
                proactive_dispatch_feedback_assessment=(
                    decisions.proactive_dispatch_feedback_assessment
                ),
                proactive_dispatch_gate_decision=decisions.proactive_dispatch_gate_decision,
                proactive_dispatch_envelope_decision=(
                    decisions.proactive_dispatch_envelope_decision
                ),
                proactive_stage_state_decision=decisions.proactive_stage_state_decision,
                proactive_stage_transition_decision=(decisions.proactive_stage_transition_decision),
                proactive_stage_machine_decision=decisions.proactive_stage_machine_decision,
                proactive_line_state_decision=decisions.proactive_line_state_decision,
                proactive_line_transition_decision=(decisions.proactive_line_transition_decision),
                proactive_line_machine_decision=decisions.proactive_line_machine_decision,
            )
            + [self._build_lifecycle_snapshot_event(decisions=post_dispatch.snapshot_decisions)],
        )
        updated_projection = self._project_runtime_state(
            session_id=session_id,
            state=context.runtime_state,
            stored_events=stored_events,
        )
        return self._build_skipped_dispatch_response(
            session_id=session_id,
            decisions=decisions,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            post_dispatch=post_dispatch,
            stored_events=stored_events,
            updated_projection=updated_projection,
        )

    async def _finalize_sent_dispatch(
        self,
        *,
        session_id: str,
        source: str,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        decisions: _DispatchDecisionChain,
        rendered: _RenderedFollowup,
        lifecycle_dispatch_decision: Any,
    ) -> dict[str, Any]:
        post_dispatch = self._build_post_dispatch_lifecycle(
            context=context,
            decisions=decisions,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            dispatched=True,
            message_event_count=len(rendered.followup_units),
        )
        dispatch_payload = self._build_dispatch_payload(
            session_id=session_id,
            source=source,
            context=context,
            models=models,
            stage_context=stage_context,
            decisions=decisions,
            rendered=rendered,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            post_dispatch=post_dispatch,
        )
        stored_events = await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=len(context.prior_events),
            events=self._build_common_dispatch_events(
                proactive_stage_refresh_plan=decisions.proactive_stage_refresh_plan,
                proactive_aggregate_governance_assessment=(
                    decisions.proactive_aggregate_governance_assessment
                ),
                proactive_aggregate_controller_decision=(
                    decisions.proactive_aggregate_controller_decision
                ),
                proactive_orchestration_controller_decision=(
                    decisions.proactive_orchestration_controller_decision
                ),
                proactive_stage_replan_assessment=(decisions.proactive_stage_replan_assessment),
                proactive_stage_controller_decision=(decisions.proactive_stage_controller_decision),
                proactive_line_controller_decision=(decisions.proactive_line_controller_decision),
                proactive_dispatch_feedback_assessment=(
                    decisions.proactive_dispatch_feedback_assessment
                ),
                proactive_dispatch_gate_decision=decisions.proactive_dispatch_gate_decision,
                proactive_dispatch_envelope_decision=(
                    decisions.proactive_dispatch_envelope_decision
                ),
                proactive_stage_state_decision=decisions.proactive_stage_state_decision,
                proactive_stage_transition_decision=(decisions.proactive_stage_transition_decision),
                proactive_stage_machine_decision=decisions.proactive_stage_machine_decision,
                proactive_line_state_decision=decisions.proactive_line_state_decision,
                proactive_line_transition_decision=(decisions.proactive_line_transition_decision),
                proactive_line_machine_decision=decisions.proactive_line_machine_decision,
            )
            + [
                NewEvent(
                    event_type=PROACTIVE_FOLLOWUP_DISPATCHED,
                    payload=dispatch_payload,
                )
            ]
            + self._build_assistant_message_events(rendered.followup_units)
            + [self._build_lifecycle_snapshot_event(decisions=post_dispatch.snapshot_decisions)],
        )
        updated_projection = self._project_runtime_state(
            session_id=session_id,
            state=context.runtime_state,
            stored_events=stored_events,
        )
        return self._build_sent_dispatch_response(
            session_id=session_id,
            dispatch_payload=dispatch_payload,
            post_dispatch=post_dispatch,
            followup_content=rendered.followup_content,
            stored_events=stored_events,
            updated_projection=updated_projection,
        )

    def _build_post_dispatch_lifecycle(
        self,
        *,
        context: _DispatchContext,
        decisions: _DispatchDecisionChain,
        lifecycle_dispatch_decision: Any,
        dispatched: bool,
        message_event_count: int,
    ) -> _PostDispatchLifecycleBundle:
        del context
        lifecycle_post_dispatch = build_proactive_lifecycle_post_dispatch_chain(
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            lifecycle_queue_decision=decisions.proactive_lifecycle_queue_decision,
            line_state_decision=decisions.proactive_line_state_decision,
            line_transition_decision=decisions.proactive_line_transition_decision,
            dispatched=dispatched,
            message_event_count=message_event_count,
        )
        phase_decisions = {
            phase: lifecycle_post_dispatch[phase] for phase in _POST_DISPATCH_LIFECYCLE_PHASES
        }
        snapshot_decisions = self._build_pre_dispatch_lifecycle_decisions(
            decisions=decisions,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
        )
        snapshot_decisions["outcome"] = lifecycle_post_dispatch["outcome"]
        snapshot_decisions["resolution"] = lifecycle_post_dispatch["resolution"]
        snapshot_decisions.update(phase_decisions)
        return _PostDispatchLifecycleBundle(
            outcome=lifecycle_post_dispatch["outcome"],
            resolution=lifecycle_post_dispatch["resolution"],
            phase_decisions=phase_decisions,
            snapshot_decisions=snapshot_decisions,
        )

    def _build_pre_dispatch_lifecycle_decisions(
        self,
        *,
        decisions: _DispatchDecisionChain,
        lifecycle_dispatch_decision: Any,
    ) -> dict[str, Any]:
        return {
            "state": decisions.proactive_lifecycle_state_decision,
            "transition": decisions.proactive_lifecycle_transition_decision,
            "machine": decisions.proactive_lifecycle_machine_decision,
            "controller": decisions.proactive_lifecycle_controller_decision,
            "envelope": decisions.proactive_lifecycle_envelope_decision,
            "scheduler": decisions.proactive_lifecycle_scheduler_decision,
            "window": decisions.proactive_lifecycle_window_decision,
            "queue": decisions.proactive_lifecycle_queue_decision,
            "dispatch": lifecycle_dispatch_decision,
        }

    def _build_assistant_message_events(
        self,
        followup_units: list[dict[str, Any]],
    ) -> list[NewEvent]:
        return [
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
        ]

    def _build_dispatch_payload_core_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        return {
            "session_id": bundle.session_id,
            "status": "sent",
            "source": bundle.source,
            "style": bundle.context.directive.get("style"),
            "ritual_mode": bundle.rendered.effective_reengagement_plan_model.ritual_mode,
            "delivery_mode": bundle.rendered.effective_reengagement_plan_model.delivery_mode,
            "strategy_key": bundle.rendered.effective_reengagement_plan_model.strategy_key,
            "relational_move": (bundle.rendered.effective_reengagement_plan_model.relational_move),
            "pressure_mode": bundle.rendered.effective_reengagement_plan_model.pressure_mode,
            "autonomy_signal": (bundle.rendered.effective_reengagement_plan_model.autonomy_signal),
            "sequence_objective": (
                bundle.rendered.effective_reengagement_plan_model.sequence_objective
            ),
            "somatic_action": bundle.rendered.effective_reengagement_plan_model.somatic_action,
            "content": bundle.rendered.followup_content,
            "trigger_after_seconds": int(
                bundle.context.directive.get("trigger_after_seconds") or 0
            ),
            "window_seconds": int(bundle.context.directive.get("window_seconds") or 0),
            "queue_status": bundle.context.queue_item.get("queue_status", "due"),
            "directive_updated_at": (
                bundle.context.latest_proactive_event.occurred_at.isoformat()
                if bundle.context.latest_proactive_event is not None
                else None
            ),
            "due_at": bundle.context.queue_item.get("due_at"),
            "base_due_at": bundle.context.queue_item.get("base_due_at"),
            "expires_at": bundle.context.queue_item.get("expires_at"),
            "schedule_reason": bundle.context.queue_item.get("schedule_reason"),
            "opening_hint": bundle.context.directive.get("opening_hint"),
            "rationale": bundle.context.directive.get("rationale"),
            "trigger_conditions": list(bundle.context.directive.get("trigger_conditions") or []),
            "hold_reasons": list(bundle.context.directive.get("hold_reasons") or []),
        }

    def _build_dispatch_payload_planning_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        return {
            "proactive_cadence_key": bundle.models.proactive_cadence_plan_model.cadence_key,
            "proactive_cadence_stage_index": bundle.stage_context.current_stage_index,
            "proactive_cadence_stage_label": bundle.stage_context.current_stage_label,
            "proactive_cadence_stage_count": self._resolve_stage_count(
                bundle.models.proactive_cadence_plan_model
            ),
            "proactive_scheduling_status": (bundle.models.proactive_scheduling_plan_model.status),
            "proactive_scheduling_mode": (
                bundle.models.proactive_scheduling_plan_model.scheduler_mode
            ),
            "proactive_scheduling_min_seconds_since_last_outbound": (
                bundle.models.proactive_scheduling_plan_model.min_seconds_since_last_outbound
            ),
            "proactive_scheduling_first_touch_extra_delay_seconds": (
                bundle.models.proactive_scheduling_plan_model.first_touch_extra_delay_seconds
            ),
            "proactive_scheduling_stage_spacing_mode": (
                bundle.models.proactive_scheduling_plan_model.stage_spacing_mode
            ),
            "proactive_scheduling_low_pressure_guard": (
                bundle.models.proactive_scheduling_plan_model.low_pressure_guard
            ),
            "proactive_guardrail_key": bundle.models.proactive_guardrail_plan.get("guardrail_key"),
            "proactive_guardrail_max_dispatch_count": int(
                bundle.models.proactive_guardrail_plan.get("max_dispatch_count") or 0
            ),
            "proactive_guardrail_stage_min_seconds_since_last_user": int(
                (bundle.stage_context.current_stage_guardrail or {}).get(
                    "min_seconds_since_last_user",
                    0,
                )
                or 0
            ),
            "proactive_guardrail_stage_min_seconds_since_last_dispatch": int(
                (bundle.stage_context.current_stage_guardrail or {}).get(
                    "min_seconds_since_last_dispatch",
                    0,
                )
                or 0
            ),
            "proactive_guardrail_stage_on_guardrail_hit": (
                (bundle.stage_context.current_stage_guardrail or {}).get("on_guardrail_hit")
            ),
            "proactive_guardrail_hard_stop_conditions": list(
                bundle.models.proactive_guardrail_plan.get("hard_stop_conditions") or []
            ),
            "proactive_guardrail_rationale": bundle.models.proactive_guardrail_plan.get(
                "rationale"
            ),
            "proactive_orchestration_key": bundle.models.proactive_orchestration_plan.get(
                "orchestration_key"
            ),
            "proactive_orchestration_stage_objective": (
                bundle.rendered.effective_stage_directive.get("objective")
            ),
            "proactive_orchestration_stage_delivery_mode": (
                bundle.rendered.effective_stage_directive.get("delivery_mode")
            ),
            "proactive_orchestration_stage_question_mode": (
                bundle.rendered.effective_stage_directive.get("question_mode")
            ),
            "proactive_orchestration_stage_autonomy_mode": (
                bundle.rendered.effective_stage_directive.get("autonomy_mode")
            ),
            "proactive_orchestration_stage_closing_style": (
                bundle.rendered.effective_stage_directive.get("closing_style")
            ),
            "proactive_actuation_key": bundle.models.proactive_actuation_plan.get("actuation_key"),
            "proactive_actuation_opening_move": (
                bundle.rendered.effective_stage_actuation.get("opening_move")
            ),
            "proactive_actuation_bridge_move": (
                bundle.rendered.effective_stage_actuation.get("bridge_move")
            ),
            "proactive_actuation_closing_move": (
                bundle.rendered.effective_stage_actuation.get("closing_move")
            ),
            "proactive_actuation_continuity_anchor": (
                bundle.rendered.effective_stage_actuation.get("continuity_anchor")
            ),
            "proactive_actuation_somatic_mode": (
                bundle.rendered.effective_stage_actuation.get("somatic_mode")
            ),
            "proactive_actuation_somatic_body_anchor": (
                bundle.rendered.effective_stage_actuation.get("somatic_body_anchor")
            ),
            "proactive_actuation_followup_style": (
                bundle.rendered.effective_stage_actuation.get("followup_style")
            ),
            "proactive_actuation_user_space_signal": (
                bundle.rendered.effective_stage_actuation.get("user_space_signal")
            ),
            "proactive_progression_key": bundle.models.proactive_progression_plan.get(
                "progression_key"
            ),
            "proactive_progression_stage_action": bundle.context.queue_item.get(
                "proactive_progression_stage_action"
            ),
            "proactive_progression_advanced": bool(
                bundle.context.queue_item.get("proactive_progression_advanced")
            ),
            "proactive_progression_reason": bundle.context.queue_item.get(
                "proactive_progression_reason"
            ),
            "proactive_cadence_remaining_after_dispatch": max(
                0,
                (
                    bundle.models.proactive_cadence_plan_model.close_after_stage_index
                    or len(bundle.models.proactive_cadence_plan_model.stage_labels)
                )
                - bundle.stage_context.current_stage_index,
            ),
        }

    def _build_dispatch_payload_refresh_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        return {
            "proactive_stage_refresh_key": (
                bundle.decisions.proactive_stage_refresh_plan.refresh_key
            ),
            "proactive_stage_refresh_window_status": (
                bundle.decisions.proactive_stage_refresh_plan.dispatch_window_status
            ),
            "proactive_stage_refresh_changed": (
                bundle.decisions.proactive_stage_refresh_plan.changed
            ),
            "proactive_stage_refresh_notes": list(
                bundle.decisions.proactive_stage_refresh_plan.refresh_notes
            ),
            "proactive_stage_replan_key": (
                bundle.decisions.proactive_stage_replan_assessment.replan_key
            ),
            "proactive_stage_replan_changed": (
                bundle.decisions.proactive_stage_replan_assessment.changed
            ),
            "proactive_stage_replan_strategy_key": (
                bundle.decisions.proactive_stage_replan_assessment.selected_strategy_key
            ),
            "proactive_stage_replan_ritual_mode": (
                bundle.decisions.proactive_stage_replan_assessment.selected_ritual_mode
            ),
            "proactive_stage_replan_pressure_mode": (
                bundle.decisions.proactive_stage_replan_assessment.selected_pressure_mode
            ),
            "proactive_stage_replan_autonomy_signal": (
                bundle.decisions.proactive_stage_replan_assessment.selected_autonomy_signal
            ),
            "proactive_stage_replan_notes": list(
                bundle.decisions.proactive_stage_replan_assessment.replan_notes
            ),
            "proactive_dispatch_feedback_key": (
                bundle.decisions.proactive_dispatch_feedback_assessment.feedback_key
            ),
            "proactive_dispatch_feedback_changed": (
                bundle.decisions.proactive_dispatch_feedback_assessment.changed
            ),
            "proactive_dispatch_feedback_dispatch_count": (
                bundle.decisions.proactive_dispatch_feedback_assessment.dispatch_count
            ),
            "proactive_dispatch_feedback_gate_defer_count": (
                bundle.decisions.proactive_dispatch_feedback_assessment.gate_defer_count
            ),
            "proactive_dispatch_feedback_strategy_key": (
                bundle.decisions.proactive_dispatch_feedback_assessment.selected_strategy_key
            ),
            "proactive_dispatch_feedback_pressure_mode": (
                bundle.decisions.proactive_dispatch_feedback_assessment.selected_pressure_mode
            ),
            "proactive_dispatch_feedback_autonomy_signal": (
                bundle.decisions.proactive_dispatch_feedback_assessment.selected_autonomy_signal
            ),
            "proactive_dispatch_feedback_delivery_mode": (
                bundle.decisions.proactive_dispatch_feedback_assessment.selected_delivery_mode
            ),
            "proactive_dispatch_feedback_sequence_objective": (
                bundle.decisions.proactive_dispatch_feedback_assessment.selected_sequence_objective
            ),
            "proactive_dispatch_feedback_prior_stage_label": (
                bundle.decisions.proactive_dispatch_feedback_assessment.prior_stage_label
            ),
            "proactive_dispatch_feedback_notes": list(
                bundle.decisions.proactive_dispatch_feedback_assessment.feedback_notes
            ),
        }

    def _build_dispatch_payload_controller_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        return {
            "proactive_stage_controller_key": (
                bundle.decisions.proactive_stage_controller_decision.controller_key
            ),
            "proactive_stage_controller_decision": (
                bundle.decisions.proactive_stage_controller_decision.decision
            ),
            "proactive_stage_controller_changed": (
                bundle.decisions.proactive_stage_controller_decision.changed
            ),
            "proactive_stage_controller_target_stage_label": (
                bundle.decisions.proactive_stage_controller_decision.target_stage_label
            ),
            "proactive_stage_controller_additional_delay_seconds": (
                bundle.decisions.proactive_stage_controller_decision.additional_delay_seconds
            ),
            "proactive_stage_controller_strategy_key": (
                bundle.decisions.proactive_stage_controller_decision.selected_strategy_key
            ),
            "proactive_stage_controller_pressure_mode": (
                bundle.decisions.proactive_stage_controller_decision.selected_pressure_mode
            ),
            "proactive_stage_controller_autonomy_signal": (
                bundle.decisions.proactive_stage_controller_decision.selected_autonomy_signal
            ),
            "proactive_stage_controller_delivery_mode": (
                bundle.decisions.proactive_stage_controller_decision.selected_delivery_mode
            ),
            "proactive_stage_controller_notes": list(
                bundle.decisions.proactive_stage_controller_decision.controller_notes
            ),
            "proactive_stage_controller_applied": (bundle.rendered.prior_stage_controller_applied),
            "proactive_stage_controller_applied_key": (
                bundle.stage_context.prior_stage_controller_decision.controller_key
                if bundle.rendered.prior_stage_controller_applied
                else None
            ),
            "proactive_line_controller_key": (
                bundle.decisions.proactive_line_controller_decision.controller_key
            ),
            "proactive_line_controller_line_state": (
                bundle.decisions.proactive_line_controller_decision.line_state
            ),
            "proactive_line_controller_decision": (
                bundle.decisions.proactive_line_controller_decision.decision
            ),
            "proactive_line_controller_changed": (
                bundle.decisions.proactive_line_controller_decision.changed
            ),
            "proactive_line_controller_affected_stage_labels": list(
                bundle.decisions.proactive_line_controller_decision.affected_stage_labels
            ),
            "proactive_line_controller_additional_delay_seconds": (
                bundle.decisions.proactive_line_controller_decision.additional_delay_seconds
            ),
            "proactive_line_controller_pressure_mode": (
                bundle.decisions.proactive_line_controller_decision.selected_pressure_mode
            ),
            "proactive_line_controller_autonomy_signal": (
                bundle.decisions.proactive_line_controller_decision.selected_autonomy_signal
            ),
            "proactive_line_controller_delivery_mode": (
                bundle.decisions.proactive_line_controller_decision.selected_delivery_mode
            ),
            "proactive_line_controller_notes": list(
                bundle.decisions.proactive_line_controller_decision.controller_notes
            ),
            "proactive_line_controller_applied": (bundle.rendered.prior_line_controller_applied),
            "proactive_line_controller_applied_key": (
                bundle.stage_context.prior_line_controller_decision.controller_key
                if bundle.rendered.prior_line_controller_applied
                else None
            ),
        }

    def _build_dispatch_payload_gate_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        return {
            "proactive_dispatch_gate_key": (
                bundle.decisions.proactive_dispatch_gate_decision.gate_key
            ),
            "proactive_dispatch_gate_decision": (
                bundle.decisions.proactive_dispatch_gate_decision.decision
            ),
            "proactive_dispatch_gate_changed": (
                bundle.decisions.proactive_dispatch_gate_decision.changed
            ),
            "proactive_dispatch_gate_retry_after_seconds": (
                bundle.decisions.proactive_dispatch_gate_decision.retry_after_seconds
            ),
            "proactive_dispatch_gate_strategy_key": (
                bundle.decisions.proactive_dispatch_gate_decision.selected_strategy_key
            ),
            "proactive_dispatch_gate_pressure_mode": (
                bundle.decisions.proactive_dispatch_gate_decision.selected_pressure_mode
            ),
            "proactive_dispatch_gate_autonomy_signal": (
                bundle.decisions.proactive_dispatch_gate_decision.selected_autonomy_signal
            ),
            "proactive_dispatch_gate_notes": list(
                bundle.decisions.proactive_dispatch_gate_decision.gate_notes
            ),
            "proactive_dispatch_envelope_key": (
                bundle.decisions.proactive_dispatch_envelope_decision.envelope_key
            ),
            "proactive_dispatch_envelope_decision": (
                bundle.decisions.proactive_dispatch_envelope_decision.decision
            ),
            "proactive_dispatch_envelope_reengagement_delivery_mode": (
                bundle.decisions.proactive_dispatch_envelope_decision.selected_reengagement_delivery_mode
            ),
            "proactive_dispatch_envelope_stage_delivery_mode": (
                bundle.decisions.proactive_dispatch_envelope_decision.selected_stage_delivery_mode
            ),
            "proactive_dispatch_envelope_source_count": len(
                bundle.decisions.proactive_dispatch_envelope_decision.active_sources
            ),
            "proactive_dispatch_envelope_sources": list(
                bundle.decisions.proactive_dispatch_envelope_decision.active_sources
            ),
            "proactive_dispatch_envelope_notes": list(
                bundle.decisions.proactive_dispatch_envelope_decision.envelope_notes
            ),
        }

    def _build_dispatch_payload_decision_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        payload.update(self._build_dispatch_payload_refresh_fields(bundle))
        payload.update(self._build_dispatch_payload_controller_fields(bundle))
        payload.update(self._build_dispatch_payload_gate_fields(bundle))
        return payload

    def _build_dispatch_payload_state_fields(
        self,
        bundle: _DispatchPayloadBundle,
    ) -> dict[str, Any]:
        return {
            "proactive_stage_state_key": (
                bundle.decisions.proactive_stage_state_decision.state_key
            ),
            "proactive_stage_state_mode": (
                bundle.decisions.proactive_stage_state_decision.state_mode
            ),
            "proactive_stage_state_source": (
                bundle.decisions.proactive_stage_state_decision.primary_source
            ),
            "proactive_stage_state_queue_status": (
                bundle.decisions.proactive_stage_state_decision.queue_status
            ),
            "proactive_stage_transition_key": (
                bundle.decisions.proactive_stage_transition_decision.transition_key
            ),
            "proactive_stage_transition_mode": (
                bundle.decisions.proactive_stage_transition_decision.transition_mode
            ),
            "proactive_stage_transition_queue_hint": (
                bundle.decisions.proactive_stage_transition_decision.next_queue_status_hint
            ),
            "proactive_stage_transition_source": (
                bundle.decisions.proactive_stage_transition_decision.primary_source
            ),
            "proactive_stage_machine_key": (
                bundle.decisions.proactive_stage_machine_decision.machine_key
            ),
            "proactive_stage_machine_mode": (
                bundle.decisions.proactive_stage_machine_decision.machine_mode
            ),
            "proactive_stage_machine_lifecycle": (
                bundle.decisions.proactive_stage_machine_decision.lifecycle_mode
            ),
            "proactive_stage_machine_actionability": (
                bundle.decisions.proactive_stage_machine_decision.actionability
            ),
            "proactive_line_state_key": (bundle.decisions.proactive_line_state_decision.line_key),
            "proactive_line_state_mode": (
                bundle.decisions.proactive_line_state_decision.line_state
            ),
            "proactive_line_state_lifecycle": (
                bundle.decisions.proactive_line_state_decision.lifecycle_mode
            ),
            "proactive_line_state_actionability": (
                bundle.decisions.proactive_line_state_decision.actionability
            ),
            "proactive_line_transition_key": (
                bundle.decisions.proactive_line_transition_decision.transition_key
            ),
            "proactive_line_transition_mode": (
                bundle.decisions.proactive_line_transition_decision.transition_mode
            ),
            "proactive_line_transition_exit_mode": (
                bundle.decisions.proactive_line_transition_decision.line_exit_mode
            ),
            "proactive_line_machine_key": (
                bundle.decisions.proactive_line_machine_decision.machine_key
            ),
            "proactive_line_machine_mode": (
                bundle.decisions.proactive_line_machine_decision.machine_mode
            ),
            "proactive_line_machine_lifecycle": (
                bundle.decisions.proactive_line_machine_decision.lifecycle_mode
            ),
            "proactive_line_machine_actionability": (
                bundle.decisions.proactive_line_machine_decision.actionability
            ),
            "time_awareness_mode": bundle.models.runtime_coordination_snapshot.get(
                "time_awareness_mode"
            ),
            "cognitive_load_band": bundle.models.runtime_coordination_snapshot.get(
                "cognitive_load_band"
            ),
            "cadence_status": bundle.models.conversation_cadence_plan.get("status"),
            "cadence_turn_shape": bundle.models.conversation_cadence_plan.get("turn_shape"),
            "cadence_followup_tempo": bundle.models.conversation_cadence_plan.get("followup_tempo"),
            "cadence_user_space_mode": bundle.models.conversation_cadence_plan.get(
                "user_space_mode"
            ),
            "ritual_phase": bundle.models.session_ritual_plan_model.phase,
            "ritual_opening_move": bundle.models.session_ritual_plan_model.opening_move,
            "ritual_bridge_move": bundle.models.session_ritual_plan_model.bridge_move,
            "ritual_closing_move": bundle.models.session_ritual_plan_model.closing_move,
            "ritual_somatic_shortcut": (bundle.models.session_ritual_plan_model.somatic_shortcut),
            "ritual_continuity_anchor": (bundle.models.session_ritual_plan_model.continuity_anchor),
            "somatic_orchestration_status": (bundle.models.somatic_orchestration_plan_model.status),
            "somatic_orchestration_mode": (
                bundle.models.somatic_orchestration_plan_model.primary_mode
            ),
            "somatic_orchestration_body_anchor": (
                bundle.models.somatic_orchestration_plan_model.body_anchor
            ),
            "somatic_orchestration_followup_style": (
                bundle.models.somatic_orchestration_plan_model.followup_style
            ),
            "dispatched_at": utc_now().isoformat(),
        }

    def _build_dispatch_payload(
        self,
        *,
        session_id: str,
        source: str,
        context: _DispatchContext,
        models: _DispatchModels,
        stage_context: _DispatchStageContext,
        decisions: _DispatchDecisionChain,
        rendered: _RenderedFollowup,
        lifecycle_dispatch_decision: Any,
        post_dispatch: _PostDispatchLifecycleBundle,
    ) -> dict[str, Any]:
        bundle = _DispatchPayloadBundle(
            session_id=session_id,
            source=source,
            context=context,
            models=models,
            stage_context=stage_context,
            decisions=decisions,
            rendered=rendered,
            lifecycle_dispatch_decision=lifecycle_dispatch_decision,
        )
        payload: dict[str, Any] = {}
        payload.update(self._build_dispatch_payload_core_fields(bundle))
        payload.update(self._build_dispatch_payload_planning_fields(bundle))
        payload.update(self._build_dispatch_payload_decision_fields(bundle))
        payload.update(self._build_dispatch_payload_state_fields(bundle))
        payload.update(
            self._build_pre_dispatch_lifecycle_payload_fields(
                decisions=decisions,
                lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            )
        )
        payload.update(self._build_post_dispatch_lifecycle_payload_fields(post_dispatch))
        return payload

    def _build_pre_dispatch_lifecycle_state_machine_fields(
        self,
        *,
        decisions: _DispatchDecisionChain,
    ) -> dict[str, Any]:
        return {
            "proactive_lifecycle_state_key": (
                decisions.proactive_lifecycle_state_decision.state_key
            ),
            "proactive_lifecycle_state_mode": (
                decisions.proactive_lifecycle_state_decision.state_mode
            ),
            "proactive_lifecycle_state_lifecycle": (
                decisions.proactive_lifecycle_state_decision.lifecycle_mode
            ),
            "proactive_lifecycle_state_actionability": (
                decisions.proactive_lifecycle_state_decision.actionability
            ),
            "proactive_lifecycle_transition_key": (
                decisions.proactive_lifecycle_transition_decision.transition_key
            ),
            "proactive_lifecycle_transition_mode": (
                decisions.proactive_lifecycle_transition_decision.transition_mode
            ),
            "proactive_lifecycle_transition_exit_mode": (
                decisions.proactive_lifecycle_transition_decision.lifecycle_exit_mode
            ),
            "proactive_lifecycle_machine_key": (
                decisions.proactive_lifecycle_machine_decision.machine_key
            ),
            "proactive_lifecycle_machine_mode": (
                decisions.proactive_lifecycle_machine_decision.machine_mode
            ),
            "proactive_lifecycle_machine_lifecycle": (
                decisions.proactive_lifecycle_machine_decision.lifecycle_mode
            ),
            "proactive_lifecycle_machine_actionability": (
                decisions.proactive_lifecycle_machine_decision.actionability
            ),
        }

    def _build_pre_dispatch_lifecycle_controller_window_fields(
        self,
        *,
        decisions: _DispatchDecisionChain,
    ) -> dict[str, Any]:
        return {
            "proactive_lifecycle_controller_key": (
                decisions.proactive_lifecycle_controller_decision.controller_key
            ),
            "proactive_lifecycle_controller_state": (
                decisions.proactive_lifecycle_controller_decision.lifecycle_state
            ),
            "proactive_lifecycle_controller_decision": (
                decisions.proactive_lifecycle_controller_decision.decision
            ),
            "proactive_lifecycle_controller_delay_seconds": (
                decisions.proactive_lifecycle_controller_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_envelope_key": (
                decisions.proactive_lifecycle_envelope_decision.envelope_key
            ),
            "proactive_lifecycle_envelope_state": (
                decisions.proactive_lifecycle_envelope_decision.lifecycle_state
            ),
            "proactive_lifecycle_envelope_mode": (
                decisions.proactive_lifecycle_envelope_decision.envelope_mode
            ),
            "proactive_lifecycle_envelope_decision": (
                decisions.proactive_lifecycle_envelope_decision.decision
            ),
            "proactive_lifecycle_envelope_actionability": (
                decisions.proactive_lifecycle_envelope_decision.actionability
            ),
            "proactive_lifecycle_envelope_delay_seconds": (
                decisions.proactive_lifecycle_envelope_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_scheduler_key": (
                decisions.proactive_lifecycle_scheduler_decision.scheduler_key
            ),
            "proactive_lifecycle_scheduler_state": (
                decisions.proactive_lifecycle_scheduler_decision.lifecycle_state
            ),
            "proactive_lifecycle_scheduler_mode": (
                decisions.proactive_lifecycle_scheduler_decision.scheduler_mode
            ),
            "proactive_lifecycle_scheduler_decision": (
                decisions.proactive_lifecycle_scheduler_decision.decision
            ),
            "proactive_lifecycle_scheduler_actionability": (
                decisions.proactive_lifecycle_scheduler_decision.actionability
            ),
            "proactive_lifecycle_scheduler_queue_status": (
                decisions.proactive_lifecycle_scheduler_decision.queue_status_hint
            ),
            "proactive_lifecycle_scheduler_delay_seconds": (
                decisions.proactive_lifecycle_scheduler_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_window_key": (
                decisions.proactive_lifecycle_window_decision.window_key
            ),
            "proactive_lifecycle_window_state": (
                decisions.proactive_lifecycle_window_decision.lifecycle_state
            ),
            "proactive_lifecycle_window_mode": (
                decisions.proactive_lifecycle_window_decision.window_mode
            ),
            "proactive_lifecycle_window_decision": (
                decisions.proactive_lifecycle_window_decision.decision
            ),
            "proactive_lifecycle_window_queue_status": (
                decisions.proactive_lifecycle_window_decision.queue_status
            ),
            "proactive_lifecycle_window_delay_seconds": (
                decisions.proactive_lifecycle_window_decision.additional_delay_seconds
            ),
        }

    def _build_pre_dispatch_lifecycle_queue_dispatch_fields(
        self,
        *,
        decisions: _DispatchDecisionChain,
        lifecycle_dispatch_decision: Any,
    ) -> dict[str, Any]:
        return {
            "proactive_lifecycle_queue_key": (
                decisions.proactive_lifecycle_queue_decision.queue_key
            ),
            "proactive_lifecycle_queue_state": (
                decisions.proactive_lifecycle_queue_decision.lifecycle_state
            ),
            "proactive_lifecycle_queue_mode": (
                decisions.proactive_lifecycle_queue_decision.queue_mode
            ),
            "proactive_lifecycle_queue_decision": (
                decisions.proactive_lifecycle_queue_decision.decision
            ),
            "proactive_lifecycle_queue_status": (
                decisions.proactive_lifecycle_queue_decision.queue_status
            ),
            "proactive_lifecycle_queue_delay_seconds": (
                decisions.proactive_lifecycle_queue_decision.additional_delay_seconds
            ),
            "proactive_lifecycle_dispatch_key": lifecycle_dispatch_decision.dispatch_key,
            "proactive_lifecycle_dispatch_state": (lifecycle_dispatch_decision.lifecycle_state),
            "proactive_lifecycle_dispatch_mode": lifecycle_dispatch_decision.dispatch_mode,
            "proactive_lifecycle_dispatch_decision": lifecycle_dispatch_decision.decision,
            "proactive_lifecycle_dispatch_actionability": (
                lifecycle_dispatch_decision.actionability
            ),
            "proactive_lifecycle_dispatch_delay_seconds": (
                lifecycle_dispatch_decision.additional_delay_seconds
            ),
        }

    def _build_pre_dispatch_lifecycle_payload_fields(
        self,
        *,
        decisions: _DispatchDecisionChain,
        lifecycle_dispatch_decision: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        payload.update(
            self._build_pre_dispatch_lifecycle_state_machine_fields(
                decisions=decisions,
            )
        )
        payload.update(
            self._build_pre_dispatch_lifecycle_controller_window_fields(
                decisions=decisions,
            )
        )
        payload.update(
            self._build_pre_dispatch_lifecycle_queue_dispatch_fields(
                decisions=decisions,
                lifecycle_dispatch_decision=lifecycle_dispatch_decision,
            )
        )
        return payload

    def _build_post_dispatch_outcome_resolution_fields(
        self,
        post_dispatch: _PostDispatchLifecycleBundle,
    ) -> dict[str, Any]:
        return {
            "proactive_lifecycle_outcome_key": post_dispatch.outcome.outcome_key,
            "proactive_lifecycle_outcome_status": post_dispatch.outcome.status,
            "proactive_lifecycle_outcome_mode": post_dispatch.outcome.outcome_mode,
            "proactive_lifecycle_outcome_decision": post_dispatch.outcome.decision,
            "proactive_lifecycle_outcome_actionability": (post_dispatch.outcome.actionability),
            "proactive_lifecycle_outcome_message_event_count": (
                post_dispatch.outcome.message_event_count
            ),
            "proactive_lifecycle_resolution_key": (post_dispatch.resolution.resolution_key),
            "proactive_lifecycle_resolution_status": post_dispatch.resolution.status,
            "proactive_lifecycle_resolution_mode": (post_dispatch.resolution.resolution_mode),
            "proactive_lifecycle_resolution_decision": (post_dispatch.resolution.decision),
            "proactive_lifecycle_resolution_actionability": (
                post_dispatch.resolution.actionability
            ),
            "proactive_lifecycle_resolution_queue_override_status": (
                post_dispatch.resolution.queue_override_status
            ),
            "proactive_lifecycle_resolution_remaining_stage_count": (
                post_dispatch.resolution.remaining_stage_count
            ),
        }

    def _build_post_dispatch_phase_payload_fields(
        self,
        *,
        phase: str,
        decision: Any,
    ) -> dict[str, Any]:
        return {
            f"proactive_lifecycle_{phase}_key": getattr(
                decision,
                f"{phase}_key",
            ),
            f"proactive_lifecycle_{phase}_status": decision.status,
            f"proactive_lifecycle_{phase}_mode": getattr(
                decision,
                f"{phase}_mode",
            ),
            f"proactive_lifecycle_{phase}_decision": decision.decision,
            f"proactive_lifecycle_{phase}_actionability": decision.actionability,
            f"proactive_lifecycle_{phase}_active_stage_label": (decision.active_stage_label),
            f"proactive_lifecycle_{phase}_queue_override_status": (decision.queue_override_status),
        }

    def _build_post_dispatch_lifecycle_payload_fields(
        self,
        post_dispatch: _PostDispatchLifecycleBundle,
    ) -> dict[str, Any]:
        payload = self._build_post_dispatch_outcome_resolution_fields(post_dispatch)
        for phase in _POST_DISPATCH_LIFECYCLE_PHASES:
            decision = post_dispatch.phase_decisions[phase]
            payload.update(
                self._build_post_dispatch_phase_payload_fields(
                    phase=phase,
                    decision=decision,
                )
            )
        return payload

    def _build_skipped_dispatch_response(
        self,
        *,
        session_id: str,
        decisions: _DispatchDecisionChain,
        lifecycle_dispatch_decision: Any,
        post_dispatch: _PostDispatchLifecycleBundle,
        stored_events: list[StoredEvent],
        updated_projection: dict[str, Any],
    ) -> dict[str, Any]:
        reason_map = {
            "reschedule_lifecycle_dispatch": "lifecycle_dispatch_rescheduled",
            "hold_lifecycle_dispatch": "lifecycle_dispatch_hold",
            "retire_lifecycle_dispatch": "lifecycle_dispatch_retired",
        }
        return {
            "session_id": session_id,
            "dispatched": False,
            "reason": reason_map.get(
                lifecycle_dispatch_decision.decision,
                "lifecycle_dispatch_hold",
            ),
            "gate": asdict(decisions.proactive_dispatch_gate_decision),
            "lifecycle_dispatch": asdict(lifecycle_dispatch_decision),
            **self._build_lifecycle_response_fields(post_dispatch),
            "events": [self._stream_service.serialize_event(event) for event in stored_events],
            "projection": updated_projection,
        }

    def _build_sent_dispatch_response(
        self,
        *,
        session_id: str,
        dispatch_payload: dict[str, Any],
        post_dispatch: _PostDispatchLifecycleBundle,
        followup_content: str,
        stored_events: list[StoredEvent],
        updated_projection: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "dispatched": True,
            "dispatch": dispatch_payload,
            **self._build_lifecycle_response_fields(post_dispatch),
            "assistant_response": followup_content,
            "events": [self._stream_service.serialize_event(event) for event in stored_events],
            "projection": updated_projection,
        }

    def _build_lifecycle_response_fields(
        self,
        post_dispatch: _PostDispatchLifecycleBundle,
    ) -> dict[str, Any]:
        response = {
            "lifecycle_outcome": asdict(post_dispatch.outcome),
            "lifecycle_resolution": asdict(post_dispatch.resolution),
        }
        for phase in _POST_DISPATCH_LIFECYCLE_PHASES:
            response[f"lifecycle_{phase}"] = asdict(post_dispatch.phase_decisions[phase])
        return response

    def _build_common_dispatch_events(
        self,
        *,
        proactive_stage_refresh_plan: Any,
        proactive_aggregate_governance_assessment: Any,
        proactive_aggregate_controller_decision: Any,
        proactive_orchestration_controller_decision: Any,
        proactive_stage_replan_assessment: Any,
        proactive_stage_controller_decision: Any,
        proactive_line_controller_decision: Any,
        proactive_dispatch_feedback_assessment: Any,
        proactive_dispatch_gate_decision: Any,
        proactive_dispatch_envelope_decision: Any,
        proactive_stage_state_decision: Any,
        proactive_stage_transition_decision: Any,
        proactive_stage_machine_decision: Any,
        proactive_line_state_decision: Any,
        proactive_line_transition_decision: Any,
        proactive_line_machine_decision: Any,
    ) -> list[NewEvent]:
        return [
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
        ]

    def _build_lifecycle_snapshot_event(
        self,
        *,
        decisions: dict[str, Any],
    ) -> NewEvent:
        snapshot = build_proactive_lifecycle_snapshot(decisions=decisions)
        return NewEvent(
            event_type=PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
            payload=asdict(snapshot),
            metadata={
                "schema_version": 2,
                "emission_id": snapshot.emission_id,
            },
        )

    def _project_runtime_state(
        self,
        *,
        session_id: str,
        state: dict[str, Any],
        stored_events: list[StoredEvent],
    ) -> dict[str, Any]:
        return self._stream_service.apply_events(
            stream_id=session_id,
            state=state,
            events=stored_events,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )

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
