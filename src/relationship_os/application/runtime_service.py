import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass, replace
from time import perf_counter
from typing import Any
from uuid import uuid4

from relationship_os.application.analyzers import (
    apply_semantic_hints,
    build_confidence_assessment,
    build_context_frame,
    build_conversation_cadence_plan,
    build_empowerment_audit,
    build_expression_plan,
    build_guidance_plan,
    build_inner_monologue,
    build_knowledge_boundary_decision,
    build_memory_bundle,
    build_policy_gate,
    build_private_judgment,
    build_proactive_actuation_plan,
    build_proactive_aggregate_governance_assessment,
    build_proactive_cadence_plan,
    build_proactive_followup_directive,
    build_proactive_guardrail_plan,
    build_proactive_orchestration_plan,
    build_proactive_progression_plan,
    build_proactive_scheduling_plan,
    build_reengagement_learning_context_stratum,
    build_reengagement_matrix_assessment,
    build_reengagement_plan,
    build_rehearsal_result,
    build_relationship_state,
    build_repair_assessment,
    build_repair_plan,
    build_response_draft_plan,
    build_response_normalization_result,
    build_response_output_units,
    build_response_post_audit,
    build_response_rendering_policy,
    build_response_sequence_plan,
    build_runtime_coordination_snapshot,
    build_runtime_quality_doctor_report,
    build_session_directive,
    build_session_ritual_plan,
    build_somatic_orchestration_plan,
    build_strategy_decision,
    build_system3_snapshot,
)
from relationship_os.application.evaluation_service import EvaluationService
from relationship_os.application.llm import (
    build_grounded_template_reply,
    build_safe_fallback_text,
)
from relationship_os.application.memory_index import MemoryMediaAttachment
from relationship_os.application.memory_service import MemoryService
from relationship_os.application.policy_registry import get_default_compiled_policy_set
from relationship_os.application.proactive_dispatch_handler import ProactiveDispatchHandler
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    CONFIDENCE_ASSESSMENT_COMPUTED,
    CONTEXT_FRAME_COMPUTED,
    CONVERSATION_CADENCE_UPDATED,
    EMPOWERMENT_AUDIT_COMPLETED,
    GUIDANCE_PLAN_UPDATED,
    INNER_MONOLOGUE_RECORDED,
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
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_CADENCE_UPDATED,
    PROACTIVE_DISPATCH_OUTCOME_RECORDED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_GUARDRAIL_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
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
    SELF_STATE_UPDATED,
    SESSION_DIRECTIVE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SESSION_STARTED,
    SOMATIC_ORCHESTRATION_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import NewEvent, StoredEvent, utc_now
from relationship_os.domain.llm import (
    ContentBlock,
    LLMClient,
    LLMMessage,
    LLMRequest,
    LLMResponse,
)

logger = logging.getLogger(__name__)
_EDGE_MEMORY_WORD_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
_EDGE_MEMORY_METRIC_RE = re.compile(r"^[a-z_]+:\S+$", re.IGNORECASE)


class SessionAlreadyExistsError(RuntimeError):
    """Raised when a session is created twice with the same identifier."""


@dataclass(slots=True, frozen=True)
class RuntimeTurnResult:
    session_id: str
    stored_events: list[StoredEvent]
    runtime_projection: dict[str, Any]
    assistant_response: str | None
    assistant_responses: list[str]
    response_diagnostics: dict[str, Any]
    turn_stage_timing: dict[str, Any]


@dataclass(slots=True)
class _TurnContext:
    prior_events: list[StoredEvent]
    expected_version: int
    runtime_state: dict[str, Any] | None
    strategy_history: list[str]
    turn_index: int
    transcript_messages: list[dict[str, Any]]
    idle_gap_seconds: float
    session_age_seconds: float
    user_id: str | None = None
    session_metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class _TurnAnalysis:
    context_frame: Any
    recalled_memory: list[dict[str, Any]]
    memory_recall: dict[str, Any]
    entity_persona: dict[str, Any]
    entity_social_world: dict[str, Any]
    conscience_assessment: dict[str, Any]
    edge_runtime_plan: dict[str, Any]
    relationship_state: Any
    repair_assessment: Any
    confidence_assessment: Any
    memory_bundle: Any
    memory_write_guard: dict[str, Any]
    memory_retention_policy: dict[str, Any]
    memory_forgetting: dict[str, Any]
    knowledge_boundary_decision: Any
    private_judgment: Any
    policy_gate: Any
    strategy_decision: Any
    rehearsal_result: Any
    repair_plan: Any
    expression_plan: Any
    runtime_coordination_snapshot: Any
    guidance_plan: Any
    conversation_cadence_plan: Any
    session_ritual_plan: Any
    somatic_orchestration_plan: Any
    empowerment_audit: Any
    response_draft_plan: Any
    response_rendering_policy: Any
    session_directive: Any
    inner_monologue: list[Any]


@dataclass(slots=True)
class _TurnFoundation:
    context_frame: Any
    recalled_memory: list[dict[str, Any]]
    memory_recall: dict[str, Any]
    entity_persona: dict[str, Any]
    entity_social_world: dict[str, Any]
    conscience_assessment: dict[str, Any]
    edge_runtime_plan: dict[str, Any]
    relationship_state: Any
    repair_assessment: Any
    confidence_assessment: Any
    memory_bundle: Any
    memory_write_guard: dict[str, Any]
    memory_retention_policy: dict[str, Any]
    memory_forgetting: dict[str, Any]
    repair_plan: Any


@dataclass(slots=True, frozen=True)
class _UserTurnInterpretation:
    factual_recall: bool = False
    social_disclosure: bool = False
    self_referential_memory: bool = False
    presence_probe: bool = False
    persona_state_probe: bool = False
    state_reflection_probe: bool = False
    relationship_reflection_probe: bool = False
    edge_fact_deposition: bool = False
    edge_status_update: bool = False
    intent_label: str = "casual_chat"
    source: str = "rules"
    confidence: float = 0.0
    deliberation_mode: str = "fast_reply"
    deliberation_need: float = 0.0
    appraisal: str = ""
    emotional_load: str = ""
    user_state_guess: str = ""
    situation_guess: str = ""
    relationship_shift_guess: str = ""


@dataclass(slots=True)
class _TurnPlans:
    knowledge_boundary_decision: Any
    private_judgment: Any
    policy_gate: Any
    strategy_decision: Any
    rehearsal_result: Any
    expression_plan: Any
    runtime_coordination_snapshot: Any
    guidance_plan: Any
    conversation_cadence_plan: Any
    session_ritual_plan: Any
    somatic_orchestration_plan: Any
    empowerment_audit: Any
    response_draft_plan: Any
    response_rendering_policy: Any


@dataclass(slots=True)
class _ReplyArtifacts:
    assistant_response: str | None
    assistant_responses: list[str]
    response_diagnostics: dict[str, Any]
    response_sequence_plan: Any | None
    response_post_audit: Any | None
    response_normalization: Any | None
    runtime_quality_doctor_report: Any | None
    events: list[NewEvent]


@dataclass(slots=True)
class _ProactiveArtifacts:
    system3_snapshot: Any
    proactive_followup_directive: Any
    proactive_aggregate_governance_assessment: Any
    reengagement_matrix_assessment: Any
    reengagement_plan: Any
    proactive_cadence_plan: Any
    proactive_scheduling_plan: Any
    proactive_orchestration_plan: Any
    proactive_actuation_plan: Any
    proactive_progression_plan: Any
    proactive_guardrail_plan: Any


class RuntimeService:
    def __init__(
        self,
        *,
        stream_service: StreamService,
        memory_service: MemoryService,
        evaluation_service: EvaluationService,
        llm_client: LLMClient,
        llm_model: str,
        llm_temperature: float,
        runtime_quality_doctor_interval_turns: int,
        runtime_quality_doctor_window_turns: int,
        runtime_projector_version: str = "v2",
        persona_text: str = "",
        search_enabled: bool = True,
        user_service: Any = None,
        entity_service: Any = None,
        action_service: Any = None,
        entity_id: str = "server",
        entity_name: str = "RelationshipOS",
        runtime_profile: str = "default",
        edge_allow_cloud_escalation: bool = True,
        edge_target_latency_seconds: float = 5.0,
        edge_hard_latency_seconds: float = 10.0,
        edge_max_memory_items: int = 4,
        edge_max_prompt_tokens: int = 1800,
        edge_max_completion_tokens: int = 260,
    ) -> None:
        self._stream_service = stream_service
        self._memory_service = memory_service
        self._evaluation_service = evaluation_service
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._llm_temperature = llm_temperature
        self._search_enabled = search_enabled
        self._runtime_projector_version = runtime_projector_version
        self._persona_text = persona_text
        self._user_service = user_service
        self._entity_service = entity_service
        self._action_service = action_service
        self._entity_id = entity_id
        self._entity_name = entity_name
        self._runtime_profile = runtime_profile
        self._edge_allow_cloud_escalation = edge_allow_cloud_escalation
        self._edge_target_latency_seconds = max(1.0, edge_target_latency_seconds)
        self._edge_hard_latency_seconds = max(
            self._edge_target_latency_seconds,
            edge_hard_latency_seconds,
        )
        self._edge_max_memory_items = max(1, edge_max_memory_items)
        self._edge_max_prompt_tokens = max(256, edge_max_prompt_tokens)
        self._edge_max_completion_tokens = max(64, edge_max_completion_tokens)
        self._semantic_turn_cache: dict[str, _UserTurnInterpretation] = {}
        self._background_factual_shadow_tasks: dict[str, asyncio.Task[None]] = {}
        self._background_memory_scope_tasks: dict[str, asyncio.Task[None]] = {}
        self._background_memory_scope_pending: dict[str, dict[str, Any]] = {}
        self._friend_chat_memory_scope_last_checkpoint_turn: dict[str, int] = {}
        self._friend_chat_memory_scope_last_checkpoint_at: dict[str, float] = {}
        self._runtime_quality_doctor_interval_turns = max(
            0,
            runtime_quality_doctor_interval_turns,
        )
        self._runtime_quality_doctor_window_turns = max(
            2,
            runtime_quality_doctor_window_turns,
        )
        self._proactive_dispatch_handler = ProactiveDispatchHandler(
            stream_service=stream_service,
            memory_service=memory_service,
            llm_client=llm_client,
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            runtime_projector_version=runtime_projector_version,
            persona_text=persona_text,
        )

    async def dispatch_proactive_followup(
        self,
        *,
        session_id: str,
        source: str,
        queue_item: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._proactive_dispatch_handler.dispatch(
            session_id=session_id,
            source=source,
            queue_item=queue_item,
        )

    async def create_session(
        self,
        *,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_session_id = session_id or f"session-{uuid4().hex[:12]}"
        existing_events = await self._stream_service.read_stream(stream_id=resolved_session_id)
        if existing_events:
            raise SessionAlreadyExistsError(f"Session {resolved_session_id} already exists")

        session_payload: dict[str, Any] = {
            "session_id": resolved_session_id,
            "created_at": utc_now().isoformat(),
            "metadata": metadata or {},
        }
        if user_id:
            session_payload["user_id"] = user_id

        stored_events = await self._stream_service.append_events(
            stream_id=resolved_session_id,
            expected_version=0,
            events=[
                NewEvent(
                    event_type=SESSION_STARTED,
                    payload=session_payload,
                )
            ],
        )

        # Link the session to the user stream if user_id provided
        if user_id and self._user_service is not None:
            try:
                await self._user_service.link_session(
                    user_id=user_id, session_id=resolved_session_id
                )
            except Exception:
                logger.warning(
                    "Failed to link session %s to user %s",
                    resolved_session_id,
                    user_id,
                    exc_info=True,
                )

        runtime_projection = self._stream_service.project_events(
            stream_id=resolved_session_id,
            events=stored_events,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )
        return {
            "session_id": resolved_session_id,
            "user_id": user_id,
            "created": True,
            "events": [self._stream_service.serialize_event(event) for event in stored_events],
            "projection": runtime_projection,
        }

    async def list_sessions(self) -> list[dict[str, Any]]:
        all_events = await self._stream_service.read_all_events()
        sessions: dict[str, dict[str, Any]] = {}
        for event in all_events:
            session = sessions.setdefault(
                event.stream_id,
                {
                    "session_id": event.stream_id,
                    "event_count": 0,
                    "turn_count": 0,
                    "started_at": None,
                    "last_event_at": None,
                },
            )
            session["event_count"] += 1
            session["last_event_at"] = event.occurred_at.isoformat()
            if event.event_type == SESSION_STARTED:
                session["started_at"] = event.payload.get("created_at")
            if event.event_type == USER_MESSAGE_RECEIVED:
                session["turn_count"] += 1
        return sorted(
            (
                session
                for session in sessions.values()
                if session["started_at"] is not None
            ),
            key=lambda item: item["session_id"],
        )

    async def process_turn(
        self,
        *,
        session_id: str,
        turn_input: TurnInput | None = None,
        user_message: str | None = None,
        generate_reply: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeTurnResult:
        turn_started = perf_counter()
        if turn_input is None:
            turn_input = TurnInput(text=user_message or "")
        user_message_text = turn_input.text

        stage_started = perf_counter()
        turn_context = await self._load_turn_context(session_id=session_id)
        load_context_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        stage_started = perf_counter()
        readonly_probe_session = self._is_benchmark_probe_session(turn_context)
        if not readonly_probe_session:
            await self._maybe_record_dispatch_outcome(
                session_id=session_id,
                prior_events=turn_context.prior_events,
            )
        dispatch_outcome_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        stage_started = perf_counter()
        analysis = await self._build_turn_analysis(
            session_id=session_id,
            user_message=user_message_text,
            turn_context=turn_context,
            turn_input=turn_input,
        )
        analysis_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        stage_started = perf_counter()
        events = self._build_turn_events(
            session_id=session_id,
            user_message=user_message_text,
            metadata=metadata,
            turn_context=turn_context,
            analysis=analysis,
            turn_input=turn_input,
        )
        reply_artifacts = await self._generate_turn_reply(
            user_message=user_message_text,
            generate_reply=generate_reply,
            turn_context=turn_context,
            analysis=analysis,
            turn_input=turn_input,
        )
        events.extend(reply_artifacts.events)
        if not readonly_probe_session:
            proactive_artifacts = await self._build_proactive_artifacts(
                turn_context=turn_context,
                analysis=analysis,
                reply_artifacts=reply_artifacts,
            )
            events.extend(self._build_proactive_events(proactive_artifacts))
        reply_and_proactive_ms = round((perf_counter() - stage_started) * 1000.0, 1)

        stage_started = perf_counter()
        stored_events, runtime_projection = await self._append_turn_events(
            session_id=session_id,
            turn_context=turn_context,
            events=events,
        )
        append_events_ms = round((perf_counter() - stage_started) * 1000.0, 1)

        stage_started = perf_counter()
        if not readonly_probe_session:
            try:
                await self._sync_memory_scope_after_turn(
                    session_id=session_id,
                    user_id=turn_context.user_id,
                    turn_index=turn_context.turn_index + 1,
                    user_message_text=user_message_text,
                    analysis=analysis,
                )
            except Exception:
                logger.warning(
                    "Failed to refresh memory scope for session %s",
                    session_id,
                    exc_info=True,
                )
        memory_sync_ms = round((perf_counter() - stage_started) * 1000.0, 1)

        # Write self-state snapshot to the user stream (best-effort, non-fatal)
        stage_started = perf_counter()
        if (
            not readonly_probe_session
            and turn_context.user_id
            and self._user_service is not None
        ):
            try:
                await self._write_self_state(
                    session_id=session_id,
                    user_id=turn_context.user_id,
                    user_message=user_message_text,
                    analysis=analysis,
                    reply_artifacts=reply_artifacts,
                )
            except Exception:
                logger.warning(
                    "Failed to write self-state for user %s in session %s",
                    turn_context.user_id,
                    session_id,
                    exc_info=True,
                )
        self_state_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        stage_started = perf_counter()
        if not readonly_probe_session and self._entity_service is not None:
            try:
                await self._entity_service.update_after_turn(
                    user_id=turn_context.user_id,
                    session_id=session_id,
                    user_message=user_message_text,
                    assistant_response=reply_artifacts.assistant_response,
                    recalled_memory=analysis.recalled_memory,
                    conscience_assessment=self._entity_service_assessment(analysis),
                )
            except Exception:
                logger.warning(
                    "Failed to update entity state for session %s",
                    session_id,
                    exc_info=True,
                )
        entity_update_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        stage_started = perf_counter()
        if (
            not readonly_probe_session
            and self._action_service is not None
            and self._entity_service is not None
        ):
            try:
                persona_state = await self._entity_service.get_persona_state()
                goal_state = await self._entity_service.get_goal_state()
                world_state = await self._entity_service.get_world_state()
                await self._action_service.plan_and_execute(
                    entity_id=self._entity_id,
                    user_id=turn_context.user_id,
                    session_id=session_id,
                    user_message=user_message_text,
                    assistant_response=reply_artifacts.assistant_response,
                    archetype=str(
                        persona_state.get("persona_archetype")
                        or persona_state.get("archetype")
                        or "default"
                    ),
                    goal_state=goal_state,
                    world_state=world_state,
                )
            except Exception:
                logger.warning(
                    "Failed to plan or execute entity actions for session %s",
                    session_id,
                    exc_info=True,
                )
        action_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        total_ms = round((perf_counter() - turn_started) * 1000.0, 1)
        turn_stage_timing = {
            "total_ms": total_ms,
            "load_context_ms": load_context_ms,
            "dispatch_outcome_ms": dispatch_outcome_ms,
            "analysis_ms": analysis_ms,
            "reply_ms": reply_and_proactive_ms,
            "append_events_ms": append_events_ms,
            "memory_sync_ms": memory_sync_ms,
            "self_state_ms": self_state_ms,
            "entity_update_ms": entity_update_ms,
            "action_ms": action_ms,
            "readonly_probe": readonly_probe_session,
        }
        logger.info(
            "turn_stage_timing session_id=%s turn_index=%s total_ms=%.1f "
            "load_context_ms=%.1f dispatch_outcome_ms=%.1f analysis_ms=%.1f "
            "reply_ms=%.1f append_events_ms=%.1f memory_sync_ms=%.1f "
            "self_state_ms=%.1f entity_update_ms=%.1f action_ms=%.1f readonly_probe=%s",
            session_id,
            turn_context.turn_index + 1,
            total_ms,
            load_context_ms,
            dispatch_outcome_ms,
            analysis_ms,
            reply_and_proactive_ms,
            append_events_ms,
            memory_sync_ms,
            self_state_ms,
            entity_update_ms,
            action_ms,
            readonly_probe_session,
        )

        return RuntimeTurnResult(
            session_id=session_id,
            stored_events=stored_events,
            runtime_projection=runtime_projection,
            assistant_response=reply_artifacts.assistant_response,
            assistant_responses=reply_artifacts.assistant_responses,
            response_diagnostics=dict(reply_artifacts.response_diagnostics or {}),
            turn_stage_timing=turn_stage_timing,
        )

    def _entity_service_assessment(self, analysis: _TurnAnalysis) -> Any:
        if self._entity_service is None:
            return None
        from relationship_os.application.entity_service import ConscienceAssessment

        return ConscienceAssessment(
            mode=str(analysis.conscience_assessment.get("mode", "withhold")),
            reason=str(analysis.conscience_assessment.get("reason", "")),
            disclosure_style=str(
                analysis.conscience_assessment.get("disclosure_style", "hint")
            ),
            dramatic_value=float(
                analysis.conscience_assessment.get("dramatic_value", 0.0) or 0.0
            ),
            conscience_weight=float(
                analysis.conscience_assessment.get("conscience_weight", 0.55) or 0.55
            ),
            source_user_ids=list(
                analysis.conscience_assessment.get("source_user_ids") or []
            ),
            allowed_fact_count=int(
                analysis.conscience_assessment.get("allowed_fact_count", 0) or 0
            ),
            attribution_required=bool(
                analysis.conscience_assessment.get("attribution_required", False)
            ),
            ambiguity_required=bool(
                analysis.conscience_assessment.get("ambiguity_required", True)
            ),
            quote_style=str(analysis.conscience_assessment.get("quote_style", "opaque")),
            dramatic_ceiling=float(
                analysis.conscience_assessment.get("dramatic_ceiling", 0.18) or 0.18
            ),
            must_anchor_to_observed_memory=bool(
                analysis.conscience_assessment.get(
                    "must_anchor_to_observed_memory",
                    False,
                )
            ),
        )

    async def _write_self_state(
        self,
        *,
        session_id: str,
        user_id: str,
        user_message: str,
        analysis: _TurnAnalysis,
        reply_artifacts: _ReplyArtifacts,
    ) -> None:
        """Write a SELF_STATE_UPDATED event to the user stream after each turn."""
        from relationship_os.application.user_service import _user_stream_id

        # Extract relationship snapshot from analysis
        ctx = analysis.context_frame
        topic = str(getattr(ctx, "topic", "")) or None
        appraisal = str(getattr(ctx, "appraisal", "")) or None
        emotional_tone: str | None = None
        my_stance: str | None = None

        # Try to extract emotional tone from relationship state
        rel = analysis.relationship_state
        if rel is not None:
            emotional_tone = str(getattr(rel, "emotional_tone", "") or "")
            if not emotional_tone:
                emotional_tone = None

        # Derive open threads: topics without completion signal
        open_threads: list[str] = []
        if topic:
            open_threads.append(topic)

        # Derive stance from strategy decision
        strat = analysis.strategy_decision
        if strat is not None:
            my_stance = str(getattr(strat, "next_action", "") or "") or None

        relationship_snapshot = {
            "last_topic": topic,
            "emotional_tone": emotional_tone or appraisal,
            "open_threads": open_threads,
            "my_stance": my_stance,
            "user_state_markers": self._extract_state_markers_from_text(user_message),
            "relationship_markers": self._extract_relationship_markers_from_text(
                user_message
            ),
            "user_message_excerpt": str(user_message or "").strip()[:220],
        }

        user_stream = _user_stream_id(user_id)
        await self._stream_service.append_events(
            stream_id=user_stream,
            expected_version=None,
            events=[
                NewEvent(
                    event_type=SELF_STATE_UPDATED,
                    payload={
                        "user_id": user_id,
                        "session_id": session_id,
                        "occurred_at": utc_now().isoformat(),
                        "relationship_snapshot": relationship_snapshot,
                    },
                )
            ],
        )

    async def _maybe_record_dispatch_outcome(
        self,
        *,
        session_id: str,
        prior_events: list[StoredEvent],
    ) -> None:
        """Auto-record 'responded' outcome when user replies after a proactive dispatch."""
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
        user_reply_after_dispatch = next(
            (
                e for e in prior_events
                if e.event_type == USER_MESSAGE_RECEIVED
                and e.occurred_at > last_dispatch.occurred_at
            ),
            None,
        )
        if user_reply_after_dispatch is None:
            return
        response_latency = max(
            0.0,
            (user_reply_after_dispatch.occurred_at - last_dispatch.occurred_at).total_seconds(),
        )
        await self._proactive_dispatch_handler.record_dispatch_outcome(
            session_id=session_id,
            outcome_type="responded",
            response_latency_seconds=response_latency,
        )

    async def _load_turn_context(self, *, session_id: str) -> _TurnContext:
        prior_events = await self._stream_service.read_stream(stream_id=session_id)
        expected_version = len(prior_events)
        runtime_state: dict[str, Any] | None = None
        if prior_events:
            runtime_state = self._stream_service.project_events(
                stream_id=session_id,
                events=prior_events,
                projector_name="session-runtime",
                projector_version=self._runtime_projector_version,
            )["state"]
        strategy_history: list[str] = []
        if runtime_state and isinstance(runtime_state.get("strategy_history"), list):
            strategy_history = [
                str(item)
                for item in runtime_state.get("strategy_history", [])
                if str(item).strip()
            ]
        turn_index = int((runtime_state or {}).get("turn_count", 0)) + 1
        transcript_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-transcript",
            projector_version="v1",
        )
        transcript_messages = list(transcript_projection["state"]["messages"])
        current_time = utc_now()
        last_event_at = prior_events[-1].occurred_at if prior_events else None
        session_started_at = prior_events[0].occurred_at if prior_events else None
        idle_gap_seconds = (
            max(0.0, (current_time - last_event_at).total_seconds())
            if last_event_at is not None
            else 0.0
        )
        session_age_seconds = (
            max(0.0, (current_time - session_started_at).total_seconds())
            if session_started_at is not None
            else 0.0
        )
        user_id: str | None = None
        session_metadata: dict[str, Any] | None = None
        if runtime_state:
            session_meta = runtime_state.get("session") or {}
            user_id = session_meta.get("user_id") or None
            metadata = session_meta.get("metadata")
            if isinstance(metadata, dict):
                session_metadata = dict(metadata)
        return _TurnContext(
            prior_events=prior_events,
            expected_version=expected_version,
            runtime_state=runtime_state,
            strategy_history=strategy_history,
            turn_index=turn_index,
            transcript_messages=transcript_messages,
            idle_gap_seconds=idle_gap_seconds,
            session_age_seconds=session_age_seconds,
            user_id=user_id,
            session_metadata=session_metadata,
        )

    def _session_benchmark_role(self, turn_context: _TurnContext) -> str:
        metadata = turn_context.session_metadata or {}
        return str(metadata.get("benchmark_role", "") or "").strip().casefold()

    def _is_benchmark_probe_session(self, turn_context: _TurnContext) -> bool:
        return self._session_benchmark_role(turn_context) == "probe"

    async def _build_turn_analysis(
        self,
        *,
        session_id: str,
        user_message: str,
        turn_context: _TurnContext,
        turn_input: TurnInput | None = None,
    ) -> _TurnAnalysis:
        foundation = await self._build_turn_foundation(
            session_id=session_id,
            user_message=user_message,
            turn_context=turn_context,
            turn_input=turn_input,
        )
        logger.info(
            (
                "turn_deliberation_decided session_id=%s turn_index=%s "
                "intent=%s deliberation_mode=%s deliberation_need=%.2f fast_path=%s"
            ),
            session_id,
            turn_context.turn_index,
            foundation.edge_runtime_plan.get("interpreted_intent", "casual_chat"),
            foundation.edge_runtime_plan.get("interpreted_deliberation_mode", "fast_reply"),
            float(foundation.edge_runtime_plan.get("interpreted_deliberation_need", 0.0) or 0.0),
            foundation.edge_runtime_plan.get("fast_path", ""),
        )
        plans = self._build_turn_plans(
            user_message=user_message,
            turn_context=turn_context,
            foundation=foundation,
        )
        plans.response_rendering_policy = self._select_entity_rendering_policy(
            user_message=user_message,
            foundation=foundation,
            current_policy=plans.response_rendering_policy,
        )
        session_directive, inner_monologue = self._build_turn_outputs(
            foundation=foundation,
            plans=plans,
        )
        return _TurnAnalysis(
            context_frame=foundation.context_frame,
            recalled_memory=foundation.recalled_memory,
            memory_recall=foundation.memory_recall,
            entity_persona=foundation.entity_persona,
            entity_social_world=foundation.entity_social_world,
            conscience_assessment=foundation.conscience_assessment,
            edge_runtime_plan={
                **foundation.edge_runtime_plan,
                "selected_rendering_mode": plans.response_rendering_policy.rendering_mode,
            },
            relationship_state=foundation.relationship_state,
            repair_assessment=foundation.repair_assessment,
            confidence_assessment=foundation.confidence_assessment,
            memory_bundle=foundation.memory_bundle,
            memory_write_guard=foundation.memory_write_guard,
            memory_retention_policy=foundation.memory_retention_policy,
            memory_forgetting=foundation.memory_forgetting,
            knowledge_boundary_decision=plans.knowledge_boundary_decision,
            private_judgment=plans.private_judgment,
            policy_gate=plans.policy_gate,
            strategy_decision=plans.strategy_decision,
            rehearsal_result=plans.rehearsal_result,
            repair_plan=foundation.repair_plan,
            expression_plan=plans.expression_plan,
            runtime_coordination_snapshot=plans.runtime_coordination_snapshot,
            guidance_plan=plans.guidance_plan,
            conversation_cadence_plan=plans.conversation_cadence_plan,
            session_ritual_plan=plans.session_ritual_plan,
            somatic_orchestration_plan=plans.somatic_orchestration_plan,
            empowerment_audit=plans.empowerment_audit,
            response_draft_plan=plans.response_draft_plan,
            response_rendering_policy=plans.response_rendering_policy,
            session_directive=session_directive,
            inner_monologue=inner_monologue,
        )

    def _select_entity_rendering_policy(
        self,
        *,
        user_message: str,
        foundation: _TurnFoundation,
        current_policy: Any,
    ) -> Any:
        conscience_mode = str(foundation.conscience_assessment.get("mode", "withhold"))
        factual_probe = bool(
            foundation.edge_runtime_plan.get(
                "interpreted_factual_probe",
                self._is_factual_recall_intent(user_message),
            )
        )
        stable_cross_user_memory = any(
            str(item.get("scope")) == "other_user"
            and str(item.get("attribution_guard", "hint_only")) != "hint_only"
            and float(item.get("attribution_confidence", 0.0) or 0.0) >= 0.68
            for item in foundation.recalled_memory
        )
        if factual_probe and foundation.recalled_memory:
            return replace(
                current_policy,
                rendering_mode="factual_recall_mode",
                include_validation=False,
                include_next_step=False,
                question_count_limit=0,
            )
        if conscience_mode == "dramatic_confrontation":
            return replace(
                current_policy,
                rendering_mode="dramatic_confrontation_mode",
                include_next_step=False,
                question_count_limit=0,
            )
        if (
            conscience_mode in {"hint", "partial_reveal", "direct_reveal"}
            and stable_cross_user_memory
        ):
            return replace(
                current_policy,
                rendering_mode="social_disclosure_mode",
                include_next_step=False,
            )
        return current_policy

    def _should_include_factual_shadow_in_person_recall(
        self,
        *,
        turn_interpretation: _UserTurnInterpretation,
    ) -> bool:
        return bool(turn_interpretation.factual_recall)

    def _friend_chat_probe_kind_for_runtime_plan(
        self,
        *,
        runtime_plan: dict[str, Any],
    ) -> str:
        if runtime_plan.get("interpreted_persona_state_probe", False):
            return "persona_state"
        if runtime_plan.get("interpreted_state_reflection_probe", False):
            return "state_reflection"
        if runtime_plan.get("interpreted_relationship_reflection_probe", False):
            return "relationship_reflection"
        if runtime_plan.get("interpreted_social_probe", False):
            return "social_hint"
        if (
            runtime_plan.get("interpreted_factual_probe", False)
            and runtime_plan.get("interpreted_self_referential_memory_query", False)
        ):
            return "memory_recap"
        if runtime_plan.get("interpreted_presence_probe", False):
            return "presence_probe"
        if runtime_plan.get("interpreted_edge_status_update", False):
            return "status_update"
        if runtime_plan.get("interpreted_edge_fact_deposition", False):
            return "fact_ack"
        return ""

    async def _sync_memory_scope_after_turn(
        self,
        *,
        session_id: str,
        user_id: str | None,
        turn_index: int,
        user_message_text: str,
        analysis: _TurnAnalysis,
    ) -> None:
        if self._is_friend_chat_profile():
            deliberation_mode = str(
                analysis.edge_runtime_plan.get(
                    "interpreted_deliberation_mode",
                    analysis.edge_runtime_plan.get("deliberation_mode", "light_recall"),
                )
                or "light_recall"
            )
            compact = deliberation_mode != "deep_recall"
            if deliberation_mode == "deep_recall":
                await self._memory_service.upsert_memory_scope(
                    session_id=session_id,
                    user_id=user_id,
                    entity_id=self._entity_id if self._entity_service is not None else None,
                    compact=compact,
                    sync_factual_shadow=False,
                )
                checkpoint_turns = getattr(
                    self,
                    "_friend_chat_memory_scope_last_checkpoint_turn",
                    None,
                )
                if checkpoint_turns is None:
                    checkpoint_turns = {}
                    self._friend_chat_memory_scope_last_checkpoint_turn = checkpoint_turns
                checkpoint_times = getattr(
                    self,
                    "_friend_chat_memory_scope_last_checkpoint_at",
                    None,
                )
                if checkpoint_times is None:
                    checkpoint_times = {}
                    self._friend_chat_memory_scope_last_checkpoint_at = checkpoint_times
                checkpoint_turns[session_id] = turn_index
                checkpoint_times[session_id] = perf_counter()
                self._schedule_friend_chat_factual_shadow_sync(
                    session_id=session_id,
                    user_id=user_id,
                    compact=compact,
                )
            else:
                should_sync, sync_reason, required_gap = (
                    self._should_checkpoint_friend_chat_memory_scope(
                        session_id=session_id,
                        turn_index=turn_index,
                        analysis=analysis,
                    )
                )
                if not should_sync:
                    logger.info(
                        "friend_chat_memory_scope_sync_skipped "
                        "session_id=%s user_id=%s turn_index=%s reason=%s",
                        session_id,
                        user_id,
                        turn_index,
                        sync_reason,
                    )
                    return
                self._queue_friend_chat_background_memory_scope_sync(
                    session_id=session_id,
                    user_id=user_id,
                    turn_index=turn_index,
                    compact=compact,
                    required_gap=required_gap,
                )
            return
        if self._is_edge_profile():
            if (
                self._is_presence_probe(user_message_text)
                or self._is_edge_fact_deposition(user_message_text)
                or self._is_edge_status_update(user_message_text)
            ):
                return
            await self._memory_service.upsert_memory_scope(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id if self._entity_service is not None else None,
                compact=True,
            )
            return
        await self._memory_service.refresh_memory_scope(
            session_id=session_id,
            user_id=user_id,
        )

    def _friend_chat_memory_scope_required_gap(
        self,
        *,
        analysis: _TurnAnalysis,
    ) -> int:
        intent = str(
            analysis.edge_runtime_plan.get("interpreted_intent")
            or analysis.edge_runtime_plan.get("intent")
            or ""
        ).strip()
        if intent in {
            "factual_recall",
            "fact_deposition",
            "social_disclosure",
            "persona_state_probe",
            "state_reflection_probe",
            "relationship_reflection_probe",
        }:
            return 4
        return 12

    def _should_checkpoint_friend_chat_memory_scope(
        self,
        *,
        session_id: str,
        turn_index: int,
        analysis: _TurnAnalysis,
    ) -> tuple[bool, str, int]:
        required_gap = self._friend_chat_memory_scope_required_gap(analysis=analysis)
        checkpoint_turns = getattr(
            self,
            "_friend_chat_memory_scope_last_checkpoint_turn",
            None,
        )
        if checkpoint_turns is None:
            checkpoint_turns = {}
            self._friend_chat_memory_scope_last_checkpoint_turn = checkpoint_turns
        checkpoint_times = getattr(
            self,
            "_friend_chat_memory_scope_last_checkpoint_at",
            None,
        )
        if checkpoint_times is None:
            checkpoint_times = {}
            self._friend_chat_memory_scope_last_checkpoint_at = checkpoint_times
        last_turn = checkpoint_turns.get(session_id)
        if last_turn is None:
            return True, "initial", required_gap
        turns_since = max(0, turn_index - last_turn)
        if turns_since >= required_gap:
            return True, f"turn_gap_{required_gap}", required_gap
        last_at = checkpoint_times.get(session_id)
        if last_at is not None and (perf_counter() - last_at) >= 120.0 and turns_since >= 2:
            return True, "time_gap", required_gap
        return False, "checkpoint_not_due", required_gap

    def _should_checkpoint_friend_chat_memory_scope_pending(
        self,
        *,
        session_id: str,
        turn_index: int,
        required_gap: int,
    ) -> bool:
        checkpoint_turns = getattr(
            self,
            "_friend_chat_memory_scope_last_checkpoint_turn",
            None,
        )
        if checkpoint_turns is None:
            checkpoint_turns = {}
            self._friend_chat_memory_scope_last_checkpoint_turn = checkpoint_turns
        checkpoint_times = getattr(
            self,
            "_friend_chat_memory_scope_last_checkpoint_at",
            None,
        )
        if checkpoint_times is None:
            checkpoint_times = {}
            self._friend_chat_memory_scope_last_checkpoint_at = checkpoint_times
        last_turn = checkpoint_turns.get(session_id)
        if last_turn is None:
            return True
        turns_since = max(0, turn_index - last_turn)
        if turns_since >= required_gap:
            return True
        last_at = checkpoint_times.get(session_id)
        if last_at is not None and (perf_counter() - last_at) >= 120.0 and turns_since >= 2:
            return True
        return False

    def _schedule_friend_chat_factual_shadow_sync(
        self,
        *,
        session_id: str,
        user_id: str | None,
        compact: bool,
    ) -> None:
        if not hasattr(self._memory_service, "sync_factual_shadow_for_session"):
            return
        task_map = getattr(self, "_background_factual_shadow_tasks", None)
        if task_map is None:
            task_map = {}
            self._background_factual_shadow_tasks = task_map
        existing = task_map.get(session_id)
        if existing is not None and not existing.done():
            logger.info(
                "friend_chat_factual_shadow_sync_skipped session_id=%s user_id=%s reason=in_flight",
                session_id,
                user_id,
            )
            return

        async def _runner() -> None:
            result = await self._memory_service.sync_factual_shadow_for_session(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id if self._entity_service is not None else None,
                compact=compact,
            )
            logger.info(
                "friend_chat_factual_shadow_sync_result session_id=%s user_id=%s status=%s "
                "fact_count=%s elapsed_ms=%s",
                session_id,
                user_id,
                result.get("status"),
                result.get("fact_count"),
                result.get("elapsed_ms"),
            )

        task = asyncio.create_task(_runner())
        task_map[session_id] = task

        def _cleanup(done_task: asyncio.Task[None]) -> None:
            current = task_map.get(session_id)
            if current is done_task:
                task_map.pop(session_id, None)
            try:
                done_task.result()
            except Exception:
                logger.warning(
                    "friend_chat_factual_shadow_sync_task_failed session_id=%s user_id=%s",
                    session_id,
                    user_id,
                    exc_info=True,
                )

        task.add_done_callback(_cleanup)

    def _queue_friend_chat_background_memory_scope_sync(
        self,
        *,
        session_id: str,
        user_id: str | None,
        turn_index: int,
        compact: bool,
        required_gap: int,
    ) -> None:
        task_map = getattr(self, "_background_memory_scope_tasks", None)
        if task_map is None:
            task_map = {}
            self._background_memory_scope_tasks = task_map
        pending_map = getattr(self, "_background_memory_scope_pending", None)
        if pending_map is None:
            pending_map = {}
            self._background_memory_scope_pending = pending_map

        existing = task_map.get(session_id)
        if existing is not None and not existing.done():
            queued = pending_map.get(session_id) or {
                "session_id": session_id,
                "user_id": user_id,
                "turn_index": turn_index,
                "compact": compact,
                "required_gap": required_gap,
            }
            queued["compact"] = bool(queued.get("compact", True)) and compact
            if user_id:
                queued["user_id"] = user_id
            queued["turn_index"] = max(int(queued.get("turn_index", 0) or 0), turn_index)
            queued["required_gap"] = min(
                int(queued.get("required_gap", required_gap) or required_gap),
                required_gap,
            )
            pending_map[session_id] = queued
            logger.info(
                "friend_chat_memory_scope_sync_queued "
                "session_id=%s user_id=%s turn_index=%s compact=%s required_gap=%s "
                "reason=in_flight",
                session_id,
                user_id,
                turn_index,
                compact,
                required_gap,
            )
            return

        self._start_friend_chat_background_memory_scope_sync(
            session_id=session_id,
            user_id=user_id,
            trigger_turn_index=turn_index,
            compact=compact,
            required_gap=required_gap,
        )

    def _start_friend_chat_background_memory_scope_sync(
        self,
        *,
        session_id: str,
        user_id: str | None,
        trigger_turn_index: int,
        compact: bool,
        required_gap: int,
    ) -> None:
        task_map = getattr(self, "_background_memory_scope_tasks", None)
        if task_map is None:
            task_map = {}
            self._background_memory_scope_tasks = task_map
        pending_map = getattr(self, "_background_memory_scope_pending", None)
        if pending_map is None:
            pending_map = {}
            self._background_memory_scope_pending = pending_map

        async def _runner() -> None:
            started = perf_counter()
            await self._memory_service.upsert_memory_scope(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id if self._entity_service is not None else None,
                compact=compact,
                sync_factual_shadow=False,
            )
            shadow_result = await self._memory_service.sync_factual_shadow_for_session(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id if self._entity_service is not None else None,
                compact=compact,
            )
            elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
            checkpoint_turns = getattr(
                self,
                "_friend_chat_memory_scope_last_checkpoint_turn",
                None,
            )
            if checkpoint_turns is None:
                checkpoint_turns = {}
                self._friend_chat_memory_scope_last_checkpoint_turn = checkpoint_turns
            checkpoint_times = getattr(
                self,
                "_friend_chat_memory_scope_last_checkpoint_at",
                None,
            )
            if checkpoint_times is None:
                checkpoint_times = {}
                self._friend_chat_memory_scope_last_checkpoint_at = checkpoint_times
            checkpoint_turns[session_id] = trigger_turn_index
            checkpoint_times[session_id] = perf_counter()
            logger.info(
                "friend_chat_memory_scope_sync_result session_id=%s user_id=%s "
                "trigger_turn_index=%s compact=%s elapsed_ms=%.1f shadow_status=%s "
                "shadow_fact_count=%s shadow_elapsed_ms=%s",
                session_id,
                user_id,
                trigger_turn_index,
                compact,
                elapsed_ms,
                shadow_result.get("status"),
                shadow_result.get("fact_count"),
                shadow_result.get("elapsed_ms"),
            )

        task = asyncio.create_task(_runner())
        task_map[session_id] = task

        def _cleanup(done_task: asyncio.Task[None]) -> None:
            current = task_map.get(session_id)
            if current is done_task:
                task_map.pop(session_id, None)
            try:
                done_task.result()
            except Exception:
                logger.warning(
                    "friend_chat_memory_scope_sync_task_failed session_id=%s user_id=%s",
                    session_id,
                    user_id,
                    exc_info=True,
                )
            pending = pending_map.pop(session_id, None)
            if pending is not None:
                pending_turn_index = int(pending.get("turn_index", 0) or 0)
                pending_required_gap = int(
                    pending.get("required_gap", required_gap) or required_gap
                )
                if self._should_checkpoint_friend_chat_memory_scope_pending(
                    session_id=session_id,
                    turn_index=pending_turn_index,
                    required_gap=pending_required_gap,
                ):
                    self._start_friend_chat_background_memory_scope_sync(
                        session_id=session_id,
                        user_id=str(pending.get("user_id") or "") or None,
                        trigger_turn_index=pending_turn_index,
                        compact=bool(pending.get("compact", True)),
                        required_gap=pending_required_gap,
                    )
                else:
                    logger.info(
                        "friend_chat_memory_scope_sync_skipped "
                        "session_id=%s user_id=%s turn_index=%s "
                        "reason=checkpoint_not_due_after_completion",
                        session_id,
                        str(pending.get("user_id") or "") or None,
                        pending_turn_index,
                    )

        task.add_done_callback(_cleanup)

    async def _build_turn_foundation(
        self,
        *,
        session_id: str,
        user_message: str,
        turn_context: _TurnContext,
        turn_input: TurnInput | None = None,
    ) -> _TurnFoundation:
        context_frame = build_context_frame(user_message)
        turn_interpretation = await self._interpret_user_turn(user_message)
        context_frame = self._apply_turn_interpretation_to_context_frame(
            context_frame,
            turn_interpretation,
        )
        attachments = [
            MemoryMediaAttachment(
                type=attachment.type,
                url=attachment.url,
                mime_type=attachment.mime_type,
                filename=attachment.filename,
                metadata=dict(attachment.metadata),
            )
            for attachment in (turn_input.attachments if turn_input is not None else [])
        ]
        if self._is_edge_profile() and (
            turn_interpretation.presence_probe
            or turn_interpretation.edge_fact_deposition
            or turn_interpretation.edge_status_update
        ):
            return await self._build_edge_lightweight_foundation(
                session_id=session_id,
                user_message=user_message,
                turn_context=turn_context,
                context_frame=context_frame,
                attachments=attachments,
                turn_interpretation=turn_interpretation,
            )
        if self._should_use_friend_chat_lightweight_foundation(
            turn_interpretation=turn_interpretation,
            attachments=attachments,
        ):
            return await self._build_friend_chat_lightweight_foundation(
                session_id=session_id,
                user_message=user_message,
                turn_context=turn_context,
                context_frame=context_frame,
                attachments=attachments,
                turn_interpretation=turn_interpretation,
            )
        entity_persona: dict[str, Any] = {}
        entity_social_world: dict[str, Any] = {}
        if self._entity_service is not None:
            try:
                await self._entity_service.ensure_seeded()
                entity_persona = await self._entity_service.get_persona_state()
                entity_social_world = await self._entity_service.get_social_world()
            except Exception:
                logger.warning("Failed to load entity state", exc_info=True)
        factual_probe = turn_interpretation.factual_recall
        social_probe = turn_interpretation.social_disclosure
        self_referential_memory_query = turn_interpretation.self_referential_memory
        edge_vector_search_enabled = (
            not self._is_edge_profile()
            or factual_probe
            or social_probe
            or bool(attachments)
        )
        entity_vector_search_enabled = self._should_enable_entity_vector_search(
            factual_probe=factual_probe,
            social_probe=social_probe,
            self_referential_memory_query=self_referential_memory_query,
            attachments=attachments,
        )
        include_entity_context = self._entity_service is not None and (
            not self._is_edge_profile()
            or social_probe
            or (factual_probe and not self_referential_memory_query)
            or bool(attachments)
        )
        memory_recall = await self._memory_service.recall_person_memory(
            session_id=session_id,
            user_id=turn_context.user_id,
            query=user_message,
            limit=8,
            context_filters={
                "topic": context_frame.topic,
                "appraisal": context_frame.appraisal,
                "dialogue_act": context_frame.dialogue_act,
            },
            attachments=attachments,
            include_entity_context=include_entity_context,
            entity_id=self._entity_id,
            enable_vector_search=edge_vector_search_enabled,
            enable_entity_vector_search=entity_vector_search_enabled,
            prefer_fast=self._is_edge_profile() and not social_probe,
            include_factual_shadow=self._should_include_factual_shadow_in_person_recall(
                turn_interpretation=turn_interpretation
            ),
        )
        recalled_memory = list(memory_recall.get("results", []))
        if (
            self._is_friend_chat_profile()
            and social_probe
            and self._entity_service is not None
            and not any(str(item.get("scope", "")) == "other_user" for item in recalled_memory)
        ):
            entity_other_user_items: list[dict[str, Any]] = []
            entity_queries = list(
                dict.fromkeys([user_message, *self._friend_chat_social_queries(user_message)])
            )
            for entity_query in entity_queries[:4]:
                entity_memory_recall = await self._memory_service.recall_entity_memory(
                    entity_id=self._entity_id,
                    current_user_id=turn_context.user_id,
                    current_session_id=session_id,
                    query=entity_query,
                    limit=6,
                    attachments=attachments,
                    enable_vector_search=True,
                    prefer_fast=False,
                )
                query_other_user_items = [
                    item
                    for item in list(entity_memory_recall.get("results") or [])
                    if str(item.get("scope", "")) == "other_user"
                ]
                if query_other_user_items:
                    entity_other_user_items = self._merge_recalled_memory_items(
                        entity_other_user_items,
                        query_other_user_items,
                        limit=6,
                    )
                if entity_other_user_items:
                    break
            if entity_other_user_items:
                recalled_memory = self._merge_recalled_memory_items(
                    entity_other_user_items,
                    recalled_memory,
                    limit=10,
                )
                memory_recall["results"] = recalled_memory
                integrity_summary = dict(memory_recall.get("integrity_summary") or {})
                integrity_summary["entity_cross_user_fallback_count"] = len(
                    entity_other_user_items
                )
                memory_recall["integrity_summary"] = integrity_summary
        conscience_assessment: dict[str, Any] = {
            "mode": "withhold",
            "reason": "entity_service_unavailable",
            "disclosure_style": "hint",
            "dramatic_value": 0.0,
            "conscience_weight": 0.55,
            "source_user_ids": [],
        }
        if self._entity_service is not None:
            try:
                conscience = await self._entity_service.assess_conscience(
                    current_user_id=turn_context.user_id,
                    user_message=user_message,
                    recalled_memory=recalled_memory,
                )
                conscience_assessment = {
                    "mode": conscience.mode,
                    "reason": conscience.reason,
                    "disclosure_style": conscience.disclosure_style,
                    "dramatic_value": conscience.dramatic_value,
                    "conscience_weight": conscience.conscience_weight,
                    "source_user_ids": conscience.source_user_ids,
                    "allowed_fact_count": conscience.allowed_fact_count,
                    "attribution_required": conscience.attribution_required,
                    "ambiguity_required": conscience.ambiguity_required,
                    "quote_style": conscience.quote_style,
                    "dramatic_ceiling": conscience.dramatic_ceiling,
                    "must_anchor_to_observed_memory": (
                        conscience.must_anchor_to_observed_memory
                    ),
                }
                memory_recall["conscience"] = conscience_assessment
            except Exception:
                logger.warning("Failed to assess entity conscience", exc_info=True)
        edge_runtime_plan = self._build_edge_runtime_plan(
            user_message=user_message,
            recalled_memory=recalled_memory,
            conscience_assessment=conscience_assessment,
            attachments=attachments,
            turn_interpretation=turn_interpretation,
        )
        memory_recall["edge_runtime_plan"] = edge_runtime_plan
        relationship_state = build_relationship_state(
            context_frame=context_frame,
            previous_state=self._previous_relationship_state(turn_context),
            user_message=user_message,
        )
        repair_assessment = build_repair_assessment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            user_message=user_message,
        )
        confidence_assessment = build_confidence_assessment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            user_message=user_message,
            recalled_memory=recalled_memory,
        )
        repair_plan = build_repair_plan(repair_assessment=repair_assessment)
        memory_write_preparation = await self._memory_service.prepare_memory_write(
            session_id=session_id,
            memory_bundle=build_memory_bundle(
                transcript_messages=turn_context.transcript_messages,
                user_message=user_message,
                context_frame=context_frame,
                relationship_state=relationship_state,
            ),
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_plan=repair_plan,
        )
        return _TurnFoundation(
            context_frame=context_frame,
            recalled_memory=recalled_memory,
            memory_recall=memory_recall,
            entity_persona=entity_persona,
            entity_social_world=entity_social_world,
            conscience_assessment=conscience_assessment,
            edge_runtime_plan=edge_runtime_plan,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            confidence_assessment=confidence_assessment,
            memory_bundle=memory_write_preparation["memory_bundle"],
            memory_write_guard=memory_write_preparation["write_guard"],
            memory_retention_policy=memory_write_preparation["retention_policy"],
            memory_forgetting=memory_write_preparation["forgetting"],
            repair_plan=repair_plan,
        )

    async def _load_friend_chat_self_state(
        self,
        *,
        user_id: str | None,
    ) -> dict[str, Any] | None:
        if not self._is_friend_chat_profile() or not user_id or self._user_service is None:
            return None
        try:
            return await self._user_service.get_self_state(user_id=user_id)
        except Exception:
            return None

    def _should_use_friend_chat_lightweight_foundation(
        self,
        *,
        turn_interpretation: _UserTurnInterpretation,
        attachments: list[MemoryMediaAttachment],
    ) -> bool:
        if not self._is_friend_chat_profile() or bool(attachments):
            return False
        if turn_interpretation.deliberation_mode in {"fast_reply", "light_recall"}:
            return True
        return any(
            (
                turn_interpretation.self_referential_memory,
                turn_interpretation.social_disclosure,
                turn_interpretation.persona_state_probe,
                turn_interpretation.state_reflection_probe,
                turn_interpretation.relationship_reflection_probe,
            )
        )

    def _build_friend_chat_self_state_recalled_memory(
        self,
        *,
        user_id: str | None,
        self_state: dict[str, Any] | None,
        transcript_messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not user_id:
            return []
        limit = self._runtime_behavior_int("friend_chat_lightweight_self_memory_limit", 6)
        values: list[tuple[str, float, str]] = []
        if isinstance(self_state, dict):
            fact_slot_digest = self._normalize_friend_chat_fact_slot_digest(
                self_state.get("fact_slot_digest")
            )
            for value in self._friend_chat_fact_slot_digest_values(
                fact_slot_digest,
                include_living_facts=True,
            ):
                values.append((value, 0.98, "self_state_fact_slot_digest"))
            narrative_digest = self._normalize_friend_chat_narrative_digest(
                self_state.get("narrative_digest")
            )
            for value in self._friend_chat_narrative_digest_values(narrative_digest):
                values.append((value, 0.94, "self_state_narrative_digest"))
            relationship_digest = self._normalize_friend_chat_relationship_digest(
                self_state.get("relationship_digest")
            )
            for value in self._friend_chat_relationship_digest_values(
                relationship_digest
            ):
                values.append((value, 0.92, "self_state_relationship_digest"))
            recent_sessions = list(self_state.get("recent_sessions_summary") or [])
            for entry in recent_sessions[-3:]:
                if not isinstance(entry, dict):
                    continue
                for value in list(entry.get("recent_user_messages") or []):
                    text = str(value).strip()
                    if text:
                        values.append((text, 0.74, "self_state_recent_session"))
                for value in list(entry.get("user_state_markers") or []):
                    text = str(value).strip()
                    if text:
                        values.append((text, 0.82, "self_state_state_marker"))
                for value in list(entry.get("relationship_markers") or []):
                    text = str(value).strip()
                    if text:
                        values.append((text, 0.8, "self_state_relationship_marker"))
        for message in transcript_messages[-8:]:
            if str(message.get("role", "")) != "user":
                continue
            text = str(message.get("content", "")).strip()
            if text:
                values.append((text, 0.72, "transcript_recent_user_message"))

        recalled: list[dict[str, Any]] = []
        seen: set[str] = set()
        for value, confidence, source_kind in values:
            normalized = value.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            recalled.append(
                {
                    "value": value,
                    "scope": "self_user",
                    "source_user_id": user_id,
                    "subject_user_id": user_id,
                    "subject_hint": f"self_user:{user_id}",
                    "source_session_id": "",
                    "attribution_guard": "direct_ok",
                    "attribution_confidence": confidence,
                    "memory_kind": source_kind,
                    "final_rank_score": confidence,
                }
            )
            if len(recalled) >= limit:
                break
        return recalled

    async def _build_friend_chat_social_recalled_memory(
        self,
        *,
        session_id: str,
        user_id: str | None,
        user_message: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[dict[str, Any]]:
        if self._entity_service is None:
            return []
        max_queries = self._runtime_behavior_int("friend_chat_social_query_limit", 1)
        if max_queries <= 0:
            return []
        query_limit = self._runtime_behavior_int("friend_chat_social_memory_limit", 4)
        enable_vector_search = self._runtime_behavior_bool(
            "friend_chat_social_enable_vector_search",
            False,
        )
        prefer_fast = self._runtime_behavior_bool("friend_chat_social_prefer_fast", True)
        query_candidates = list(
            dict.fromkeys([*self._friend_chat_social_queries(user_message), user_message])
        )
        effective_query_limit = max_queries
        if len(query_candidates) > 1:
            effective_query_limit = max(max_queries, 2)
        entity_queries = query_candidates[:effective_query_limit]
        entity_other_user_items: list[dict[str, Any]] = []
        for entity_query in entity_queries:
            entity_memory_recall = await self._memory_service.recall_entity_memory(
                entity_id=self._entity_id,
                current_user_id=user_id,
                current_session_id=session_id,
                query=entity_query,
                limit=query_limit,
                attachments=attachments,
                enable_vector_search=enable_vector_search,
                prefer_fast=prefer_fast,
            )
            query_other_user_items = [
                item
                for item in list(entity_memory_recall.get("results") or [])
                if str(item.get("scope", "")) == "other_user"
            ]
            if query_other_user_items:
                entity_other_user_items = self._merge_recalled_memory_items(
                    entity_other_user_items,
                    query_other_user_items,
                    limit=query_limit,
                )
            if entity_other_user_items:
                break
        return entity_other_user_items

    async def _build_friend_chat_lightweight_foundation(
        self,
        *,
        session_id: str,
        user_message: str,
        turn_context: _TurnContext,
        context_frame: Any,
        attachments: list[MemoryMediaAttachment],
        turn_interpretation: _UserTurnInterpretation,
    ) -> _TurnFoundation:
        deliberation_mode = str(
            getattr(turn_interpretation, "deliberation_mode", "light_recall") or "light_recall"
        )
        entity_persona: dict[str, Any] = {}
        entity_social_world: dict[str, Any] = {}
        if self._entity_service is not None:
            try:
                await self._entity_service.ensure_seeded()
                entity_persona = await self._entity_service.get_persona_state()
                entity_social_world = await self._entity_service.get_social_world()
            except Exception:
                logger.warning("Failed to load entity state", exc_info=True)

        friend_chat_self_state = await self._load_friend_chat_self_state(
            user_id=turn_context.user_id
        )
        recalled_memory: list[dict[str, Any]] = []
        should_use_self_state_memory = any(
            (
                deliberation_mode == "light_recall",
                turn_interpretation.intent_label == "casual_chat",
                turn_interpretation.factual_recall,
                turn_interpretation.self_referential_memory,
                turn_interpretation.persona_state_probe,
                turn_interpretation.state_reflection_probe,
                turn_interpretation.relationship_reflection_probe,
            )
        )
        if should_use_self_state_memory:
            recalled_memory = self._build_friend_chat_self_state_recalled_memory(
                user_id=turn_context.user_id,
                self_state=friend_chat_self_state,
                transcript_messages=turn_context.transcript_messages,
            )
        if turn_interpretation.social_disclosure and deliberation_mode != "fast_reply":
            social_memory = await self._build_friend_chat_social_recalled_memory(
                session_id=session_id,
                user_id=turn_context.user_id,
                user_message=user_message,
                attachments=attachments,
            )
            if social_memory:
                recalled_memory = self._merge_recalled_memory_items(
                    social_memory,
                    recalled_memory,
                    limit=max(
                        6,
                        self._runtime_behavior_int("friend_chat_social_memory_limit", 4),
                    ),
                )

        conscience_assessment: dict[str, Any] = {
            "mode": "withhold",
            "reason": "friend_chat_lightweight_foundation",
            "disclosure_style": "hint",
            "dramatic_value": 0.0,
            "conscience_weight": 0.55,
            "source_user_ids": [],
            "allowed_fact_count": 0,
            "attribution_required": False,
            "ambiguity_required": True,
            "quote_style": "opaque",
            "dramatic_ceiling": 0.18,
            "must_anchor_to_observed_memory": False,
        }
        if self._entity_service is not None:
            try:
                conscience = await self._entity_service.assess_conscience(
                    current_user_id=turn_context.user_id,
                    user_message=user_message,
                    recalled_memory=recalled_memory,
                )
                conscience_assessment = {
                    "mode": conscience.mode,
                    "reason": conscience.reason,
                    "disclosure_style": conscience.disclosure_style,
                    "dramatic_value": conscience.dramatic_value,
                    "conscience_weight": conscience.conscience_weight,
                    "source_user_ids": conscience.source_user_ids,
                    "allowed_fact_count": conscience.allowed_fact_count,
                    "attribution_required": conscience.attribution_required,
                    "ambiguity_required": conscience.ambiguity_required,
                    "quote_style": conscience.quote_style,
                    "dramatic_ceiling": conscience.dramatic_ceiling,
                    "must_anchor_to_observed_memory": (
                        conscience.must_anchor_to_observed_memory
                    ),
                }
            except Exception:
                logger.warning("Failed to assess entity conscience", exc_info=True)

        edge_runtime_plan = self._build_edge_runtime_plan(
            user_message=user_message,
            recalled_memory=recalled_memory,
            conscience_assessment=conscience_assessment,
            attachments=attachments,
            turn_interpretation=turn_interpretation,
        )
        edge_runtime_plan["fast_path"] = "friend_chat_lightweight_foundation"
        edge_runtime_plan["deliberation_mode"] = deliberation_mode
        edge_runtime_plan["deliberation_need"] = float(
            getattr(turn_interpretation, "deliberation_need", 0.0) or 0.0
        )
        memory_recall = {
            "query": user_message,
            "user_id": turn_context.user_id,
            "results": recalled_memory,
            "source": "friend_chat_lightweight_foundation",
            "edge_runtime_plan": edge_runtime_plan,
            "conscience": conscience_assessment,
            "integrity_summary": {
                "lightweight_path": True,
                "deliberation_mode": deliberation_mode,
                "deliberation_need": float(
                    getattr(turn_interpretation, "deliberation_need", 0.0) or 0.0
                ),
                "result_count": len(recalled_memory),
                "cross_user_hit_count": sum(
                    1 for item in recalled_memory if item.get("scope") == "other_user"
                ),
            },
        }
        relationship_state = build_relationship_state(
            context_frame=context_frame,
            previous_state=self._previous_relationship_state(turn_context),
            user_message=user_message,
        )
        repair_assessment = build_repair_assessment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            user_message=user_message,
        )
        confidence_assessment = build_confidence_assessment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            user_message=user_message,
            recalled_memory=recalled_memory,
        )
        repair_plan = build_repair_plan(repair_assessment=repair_assessment)
        memory_write_preparation = await self._memory_service.prepare_memory_write(
            session_id=session_id,
            memory_bundle=build_memory_bundle(
                transcript_messages=turn_context.transcript_messages,
                user_message=user_message,
                context_frame=context_frame,
                relationship_state=relationship_state,
            ),
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_plan=repair_plan,
        )
        return _TurnFoundation(
            context_frame=context_frame,
            recalled_memory=recalled_memory,
            memory_recall=memory_recall,
            entity_persona=entity_persona,
            entity_social_world=entity_social_world,
            conscience_assessment=conscience_assessment,
            edge_runtime_plan=edge_runtime_plan,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            confidence_assessment=confidence_assessment,
            memory_bundle=memory_write_preparation["memory_bundle"],
            memory_write_guard=memory_write_preparation["write_guard"],
            memory_retention_policy=memory_write_preparation["retention_policy"],
            memory_forgetting=memory_write_preparation["forgetting"],
            repair_plan=repair_plan,
        )

    async def _build_edge_lightweight_foundation(
        self,
        *,
        session_id: str,
        user_message: str,
        turn_context: _TurnContext,
        context_frame: Any,
        attachments: list[MemoryMediaAttachment],
        turn_interpretation: _UserTurnInterpretation,
    ) -> _TurnFoundation:
        conscience_assessment: dict[str, Any] = {
            "mode": "withhold",
            "reason": "edge_lightweight_foundation",
            "disclosure_style": "hint",
            "dramatic_value": 0.0,
            "conscience_weight": 0.55,
            "source_user_ids": [],
            "allowed_fact_count": 0,
            "attribution_required": False,
            "ambiguity_required": True,
            "quote_style": "opaque",
            "dramatic_ceiling": 0.18,
            "must_anchor_to_observed_memory": False,
        }
        edge_runtime_plan = self._build_edge_runtime_plan(
            user_message=user_message,
            recalled_memory=[],
            conscience_assessment=conscience_assessment,
            attachments=attachments,
            turn_interpretation=turn_interpretation,
        )
        edge_runtime_plan["fast_path"] = "edge_lightweight_foundation"
        relationship_state = build_relationship_state(
            context_frame=context_frame,
            previous_state=self._previous_relationship_state(turn_context),
            user_message=user_message,
        )
        repair_assessment = build_repair_assessment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            user_message=user_message,
        )
        confidence_assessment = build_confidence_assessment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            user_message=user_message,
            recalled_memory=[],
        )
        repair_plan = build_repair_plan(repair_assessment=repair_assessment)
        memory_write_preparation = await self._memory_service.prepare_memory_write(
            session_id=session_id,
            memory_bundle=build_memory_bundle(
                transcript_messages=turn_context.transcript_messages,
                user_message=user_message,
                context_frame=context_frame,
                relationship_state=relationship_state,
            ),
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_plan=repair_plan,
        )
        return _TurnFoundation(
            context_frame=context_frame,
            recalled_memory=[],
            memory_recall={
                "query": user_message,
                "results": [],
                "source": "edge_lightweight_foundation",
                "edge_runtime_plan": edge_runtime_plan,
                "conscience": conscience_assessment,
            },
            entity_persona={},
            entity_social_world={},
            conscience_assessment=conscience_assessment,
            edge_runtime_plan=edge_runtime_plan,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            confidence_assessment=confidence_assessment,
            memory_bundle=memory_write_preparation["memory_bundle"],
            memory_write_guard=memory_write_preparation["write_guard"],
            memory_retention_policy=memory_write_preparation["retention_policy"],
            memory_forgetting=memory_write_preparation["forgetting"],
            repair_plan=repair_plan,
        )

    def _previous_relationship_state(
        self,
        turn_context: _TurnContext,
    ) -> dict[str, Any] | None:
        if (
            turn_context.runtime_state
            and isinstance(turn_context.runtime_state.get("relationship_state"), dict)
        ):
            return turn_context.runtime_state["relationship_state"]
        return None

    def _build_turn_plans(
        self,
        *,
        user_message: str,
        turn_context: _TurnContext,
        foundation: _TurnFoundation,
    ) -> _TurnPlans:
        knowledge_boundary_decision = build_knowledge_boundary_decision(
            context_frame=foundation.context_frame,
            relationship_state=foundation.relationship_state,
            confidence_assessment=foundation.confidence_assessment,
            user_message=user_message,
            recalled_memory=foundation.recalled_memory,
        )
        private_judgment = build_private_judgment(
            context_frame=foundation.context_frame,
            relationship_state=foundation.relationship_state,
            repair_assessment=foundation.repair_assessment,
            repair_plan=foundation.repair_plan,
            knowledge_boundary_decision=knowledge_boundary_decision,
            memory_bundle=foundation.memory_bundle,
            confidence_assessment=foundation.confidence_assessment,
            recalled_memory=foundation.recalled_memory,
        )
        policy_gate = build_policy_gate(
            context_frame=foundation.context_frame,
            relationship_state=foundation.relationship_state,
            repair_assessment=foundation.repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            confidence_assessment=foundation.confidence_assessment,
            private_judgment=private_judgment,
        )
        strategy_decision = build_strategy_decision(
            policy_gate=policy_gate,
            private_judgment=private_judgment,
            context_frame=foundation.context_frame,
            repair_assessment=foundation.repair_assessment,
            confidence_assessment=foundation.confidence_assessment,
            relationship_state=foundation.relationship_state,
            strategy_history=turn_context.strategy_history,
        )
        rehearsal_result = build_rehearsal_result(
            strategy_decision=strategy_decision,
            policy_gate=policy_gate,
            repair_assessment=foundation.repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
        )
        expression_plan = build_expression_plan(
            strategy_decision,
            foundation.repair_plan,
            rehearsal_result,
        )
        runtime_coordination_snapshot = build_runtime_coordination_snapshot(
            turn_index=turn_context.turn_index,
            session_age_seconds=turn_context.session_age_seconds,
            idle_gap_seconds=turn_context.idle_gap_seconds,
            user_message=user_message,
            context_frame=foundation.context_frame,
            relationship_state=foundation.relationship_state,
            confidence_assessment=foundation.confidence_assessment,
            repair_assessment=foundation.repair_assessment,
            strategy_decision=strategy_decision,
        )
        guidance_plan = build_guidance_plan(
            context_frame=foundation.context_frame,
            repair_assessment=foundation.repair_assessment,
            confidence_assessment=foundation.confidence_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            policy_gate=policy_gate,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
        )
        conversation_cadence_plan = build_conversation_cadence_plan(
            context_frame=foundation.context_frame,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            repair_assessment=foundation.repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            policy_gate=policy_gate,
        )
        session_ritual_plan = build_session_ritual_plan(
            context_frame=foundation.context_frame,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            repair_assessment=foundation.repair_assessment,
        )
        somatic_orchestration_plan = build_somatic_orchestration_plan(
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
        )
        empowerment_audit = build_empowerment_audit(
            policy_gate=policy_gate,
            relationship_state=foundation.relationship_state,
            knowledge_boundary_decision=knowledge_boundary_decision,
            confidence_assessment=foundation.confidence_assessment,
            expression_plan=expression_plan,
            rehearsal_result=rehearsal_result,
        )
        response_draft_plan = build_response_draft_plan(
            context_frame=foundation.context_frame,
            policy_gate=policy_gate,
            repair_plan=foundation.repair_plan,
            confidence_assessment=foundation.confidence_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            expression_plan=expression_plan,
            rehearsal_result=rehearsal_result,
            empowerment_audit=empowerment_audit,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            somatic_orchestration_plan=somatic_orchestration_plan,
        )
        response_rendering_policy = build_response_rendering_policy(
            context_frame=foundation.context_frame,
            confidence_assessment=foundation.confidence_assessment,
            repair_assessment=foundation.repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            response_draft_plan=response_draft_plan,
            empowerment_audit=empowerment_audit,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            runtime_profile=self._runtime_profile,
            archetype=str(
                foundation.entity_persona.get("persona_archetype", "default") or "default"
            ),
        )
        return _TurnPlans(
            knowledge_boundary_decision=knowledge_boundary_decision,
            private_judgment=private_judgment,
            policy_gate=policy_gate,
            strategy_decision=strategy_decision,
            rehearsal_result=rehearsal_result,
            expression_plan=expression_plan,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            conversation_cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            somatic_orchestration_plan=somatic_orchestration_plan,
            empowerment_audit=empowerment_audit,
            response_draft_plan=response_draft_plan,
            response_rendering_policy=response_rendering_policy,
        )

    def _build_turn_outputs(
        self,
        *,
        foundation: _TurnFoundation,
        plans: _TurnPlans,
    ) -> tuple[Any, list[Any]]:
        session_directive = build_session_directive(
            context_frame=foundation.context_frame,
            policy_gate=plans.policy_gate,
            strategy_decision=plans.strategy_decision,
            rehearsal_result=plans.rehearsal_result,
            empowerment_audit=plans.empowerment_audit,
            response_draft_plan=plans.response_draft_plan,
            response_rendering_policy=plans.response_rendering_policy,
            guidance_plan=plans.guidance_plan,
            cadence_plan=plans.conversation_cadence_plan,
            session_ritual_plan=plans.session_ritual_plan,
            somatic_orchestration_plan=plans.somatic_orchestration_plan,
            repair_assessment=foundation.repair_assessment,
            repair_plan=foundation.repair_plan,
            knowledge_boundary_decision=plans.knowledge_boundary_decision,
            memory_bundle=foundation.memory_bundle,
            recalled_memory=foundation.recalled_memory,
        )
        inner_monologue = build_inner_monologue(
            context_frame=foundation.context_frame,
            memory_bundle=foundation.memory_bundle,
            recalled_memory=foundation.recalled_memory,
            policy_gate=plans.policy_gate,
            rehearsal_result=plans.rehearsal_result,
            empowerment_audit=plans.empowerment_audit,
            response_draft_plan=plans.response_draft_plan,
            response_rendering_policy=plans.response_rendering_policy,
            repair_assessment=foundation.repair_assessment,
            repair_plan=foundation.repair_plan,
            knowledge_boundary_decision=plans.knowledge_boundary_decision,
            private_judgment=plans.private_judgment,
            relationship_state=foundation.relationship_state,
            strategy_decision=plans.strategy_decision,
            confidence_assessment=foundation.confidence_assessment,
        )
        return session_directive, inner_monologue

    def _build_turn_events(
        self,
        *,
        session_id: str,
        user_message: str,
        metadata: dict[str, Any] | None,
        turn_context: _TurnContext,
        analysis: _TurnAnalysis,
        turn_input: TurnInput | None = None,
    ) -> list[NewEvent]:
        metadata_payload = metadata or {}
        events = self._build_session_start_events(
            session_id=session_id,
            metadata_payload=metadata_payload,
            turn_context=turn_context,
        )
        events.extend(
            self._build_turn_analysis_events(
                user_message=user_message,
                metadata_payload=metadata_payload,
                analysis=analysis,
                turn_input=turn_input,
            )
        )
        return events

    def _build_session_start_events(
        self,
        *,
        session_id: str,
        metadata_payload: dict[str, Any],
        turn_context: _TurnContext,
    ) -> list[NewEvent]:
        if turn_context.prior_events:
            return []
        return [
            NewEvent(
                event_type=SESSION_STARTED,
                payload={
                    "session_id": session_id,
                    "created_at": utc_now().isoformat(),
                    "metadata": metadata_payload,
                },
            )
        ]

    def _build_turn_analysis_events(
        self,
        *,
        user_message: str,
        metadata_payload: dict[str, Any],
        analysis: _TurnAnalysis,
        turn_input: TurnInput | None = None,
    ) -> list[NewEvent]:
        user_payload: dict[str, Any] = {"content": user_message}
        if turn_input and turn_input.has_media:
            user_payload["attachments"] = [
                {"type": a.type, "url": a.url, "mime_type": a.mime_type, "filename": a.filename}
                for a in turn_input.attachments
            ]
        return [
            NewEvent(
                event_type=USER_MESSAGE_RECEIVED,
                payload=user_payload,
                metadata=metadata_payload,
            ),
            NewEvent(
                event_type=CONTEXT_FRAME_COMPUTED,
                payload=asdict(analysis.context_frame),
            ),
            NewEvent(
                event_type=RELATIONSHIP_STATE_UPDATED,
                payload=asdict(analysis.relationship_state),
            ),
            NewEvent(
                event_type=CONFIDENCE_ASSESSMENT_COMPUTED,
                payload=asdict(analysis.confidence_assessment),
            ),
            NewEvent(
                event_type=REPAIR_ASSESSMENT_COMPUTED,
                payload=asdict(analysis.repair_assessment),
            ),
            NewEvent(
                event_type=MEMORY_WRITE_GUARD_EVALUATED,
                payload=analysis.memory_write_guard,
            ),
            NewEvent(
                event_type=MEMORY_RETENTION_POLICY_APPLIED,
                payload=analysis.memory_retention_policy,
            ),
            NewEvent(
                event_type=MEMORY_BUNDLE_UPDATED,
                payload=asdict(analysis.memory_bundle),
            ),
            NewEvent(
                event_type=MEMORY_FORGETTING_APPLIED,
                payload=analysis.memory_forgetting,
            ),
            NewEvent(
                event_type=MEMORY_RECALL_PERFORMED,
                payload=analysis.memory_recall,
            ),
            NewEvent(
                event_type=KNOWLEDGE_BOUNDARY_DECIDED,
                payload=asdict(analysis.knowledge_boundary_decision),
            ),
            NewEvent(
                event_type=POLICY_GATE_DECIDED,
                payload=asdict(analysis.policy_gate),
            ),
            NewEvent(
                event_type=REHEARSAL_COMPLETED,
                payload=asdict(analysis.rehearsal_result),
            ),
            NewEvent(
                event_type=REPAIR_PLAN_UPDATED,
                payload=asdict(analysis.repair_plan),
            ),
            NewEvent(
                event_type=EMPOWERMENT_AUDIT_COMPLETED,
                payload=asdict(analysis.empowerment_audit),
            ),
            NewEvent(
                event_type=RESPONSE_DRAFT_PLANNED,
                payload=asdict(analysis.response_draft_plan),
            ),
            NewEvent(
                event_type=RESPONSE_RENDERING_POLICY_DECIDED,
                payload=asdict(analysis.response_rendering_policy),
            ),
            NewEvent(
                event_type=RUNTIME_COORDINATION_UPDATED,
                payload=asdict(analysis.runtime_coordination_snapshot),
            ),
            NewEvent(
                event_type=GUIDANCE_PLAN_UPDATED,
                payload=asdict(analysis.guidance_plan),
            ),
            NewEvent(
                event_type=CONVERSATION_CADENCE_UPDATED,
                payload=asdict(analysis.conversation_cadence_plan),
            ),
            NewEvent(
                event_type=SESSION_RITUAL_UPDATED,
                payload=asdict(analysis.session_ritual_plan),
            ),
            NewEvent(
                event_type=SOMATIC_ORCHESTRATION_UPDATED,
                payload=asdict(analysis.somatic_orchestration_plan),
            ),
            NewEvent(
                event_type=PRIVATE_JUDGMENT_COMPUTED,
                payload=asdict(analysis.private_judgment),
            ),
            NewEvent(
                event_type=INNER_MONOLOGUE_RECORDED,
                payload={
                    "entries": [asdict(entry) for entry in analysis.inner_monologue]
                },
            ),
            NewEvent(
                event_type=SESSION_DIRECTIVE_UPDATED,
                payload=self._build_session_directive_payload(analysis),
            ),
        ]

    def _build_session_directive_payload(
        self,
        analysis: _TurnAnalysis,
    ) -> dict[str, Any]:
        return {
            "directive": asdict(analysis.session_directive),
            "confidence": asdict(analysis.confidence_assessment),
            "strategy": asdict(analysis.strategy_decision),
            "expression_plan": asdict(analysis.expression_plan),
            "guidance_plan": asdict(analysis.guidance_plan),
            "conversation_cadence_plan": asdict(
                analysis.conversation_cadence_plan
            ),
            "session_ritual_plan": asdict(analysis.session_ritual_plan),
            "somatic_orchestration_plan": asdict(
                analysis.somatic_orchestration_plan
            ),
            "response_draft_plan": asdict(analysis.response_draft_plan),
            "response_rendering_policy": asdict(
                analysis.response_rendering_policy
            ),
        }

    def _build_reply_drafting_lines(self, analysis: _TurnAnalysis) -> list[str]:
        return [
            f"- opening_move: {analysis.response_draft_plan.opening_move}",
            f"- structure: {', '.join(analysis.response_draft_plan.structure)}",
            f"- must_include: {', '.join(analysis.response_draft_plan.must_include)}",
            f"- must_avoid: {', '.join(analysis.response_draft_plan.must_avoid)}",
            (
                "- phrasing_constraints: "
                + ", ".join(analysis.response_draft_plan.phrasing_constraints)
            ),
            f"- question_strategy: {analysis.response_draft_plan.question_strategy}",
        ]

    def _build_reply_rendering_lines(self, analysis: _TurnAnalysis) -> list[str]:
        return [
            (
                "- rendering_mode: "
                f"{analysis.response_rendering_policy.rendering_mode}"
            ),
            (
                "- max_sentences: "
                f"{analysis.response_rendering_policy.max_sentences}"
            ),
            (
                "- include_validation: "
                f"{analysis.response_rendering_policy.include_validation}"
            ),
            (
                "- include_next_step: "
                f"{analysis.response_rendering_policy.include_next_step}"
            ),
            (
                "- include_boundary_statement: "
                f"{analysis.response_rendering_policy.include_boundary_statement}"
            ),
            (
                "- include_uncertainty_statement: "
                f"{analysis.response_rendering_policy.include_uncertainty_statement}"
            ),
            (
                "- question_count_limit: "
                f"{analysis.response_rendering_policy.question_count_limit}"
            ),
            (
                "- style_guardrails: "
                + ", ".join(analysis.response_rendering_policy.style_guardrails)
            ),
        ]

    def _build_reply_guidance_lines(self, analysis: _TurnAnalysis) -> list[str]:
        return [
            f"- mode: {analysis.guidance_plan.mode}",
            f"- lead_with: {analysis.guidance_plan.lead_with}",
            f"- pacing: {analysis.guidance_plan.pacing}",
            f"- step_budget: {analysis.guidance_plan.step_budget}",
            f"- agency_mode: {analysis.guidance_plan.agency_mode}",
            f"- ritual_action: {analysis.guidance_plan.ritual_action}",
            f"- checkpoint_style: {analysis.guidance_plan.checkpoint_style}",
            f"- handoff_mode: {analysis.guidance_plan.handoff_mode}",
            f"- carryover_mode: {analysis.guidance_plan.carryover_mode}",
            f"- micro_actions: {', '.join(analysis.guidance_plan.micro_actions)}",
            f"- cadence_status: {analysis.conversation_cadence_plan.status}",
            (
                "- cadence_turn_shape: "
                f"{analysis.conversation_cadence_plan.turn_shape}"
            ),
            (
                "- cadence_followup_tempo: "
                f"{analysis.conversation_cadence_plan.followup_tempo}"
            ),
            (
                "- cadence_user_space_mode: "
                f"{analysis.conversation_cadence_plan.user_space_mode}"
            ),
            f"- ritual_phase: {analysis.session_ritual_plan.phase}",
            (
                "- ritual_opening_move: "
                f"{analysis.session_ritual_plan.opening_move}"
            ),
            f"- ritual_bridge_move: {analysis.session_ritual_plan.bridge_move}",
            (
                "- ritual_closing_move: "
                f"{analysis.session_ritual_plan.closing_move}"
            ),
            (
                "- ritual_somatic_shortcut: "
                f"{analysis.session_ritual_plan.somatic_shortcut}"
            ),
            (
                "- somatic_orchestration_status: "
                f"{analysis.somatic_orchestration_plan.status}"
            ),
            (
                "- somatic_orchestration_mode: "
                f"{analysis.somatic_orchestration_plan.primary_mode}"
            ),
            (
                "- somatic_orchestration_body_anchor: "
                f"{analysis.somatic_orchestration_plan.body_anchor}"
            ),
            (
                "- somatic_orchestration_followup_style: "
                f"{analysis.somatic_orchestration_plan.followup_style}"
            ),
        ]

    _RECENT_WINDOW = 20  # ~10 turns — keeps context manageable for small models
    _SUMMARY_THRESHOLD = 10  # summarize early messages once history exceeds this

    @staticmethod
    def _summarize_early_messages(messages: list[dict[str, str]]) -> str:
        """Compress early conversation into key facts for small-model context."""
        lines: list[str] = []
        for msg in messages:
            role = msg.get("role", "")
            content = (msg.get("content") or "").strip()
            if not content or role == "system":
                continue
            tag = "User" if role == "user" else "You"
            truncated = content[:80] + ("…" if len(content) > 80 else "")
            lines.append(f"{tag}: {truncated}")
        if len(lines) > 30:
            lines = lines[:15] + ["..."] + lines[-15:]
        return "\n".join(lines)

    def _is_edge_profile(self) -> bool:
        return self._runtime_profile in {"edge_desktop_4b", "friend_chat_zh_v1"}

    def _is_friend_chat_profile(self) -> bool:
        return self._runtime_profile == "friend_chat_zh_v1"

    def _runtime_behavior_policy(self) -> dict[str, Any]:
        compiled = get_default_compiled_policy_set(
            runtime_profile=getattr(self, "_runtime_profile", "default"),
            archetype="default",
        )
        if compiled is None:
            return {}
        return dict(compiled.rendering_policy.get("runtime_behavior") or {})

    def _runtime_behavior_list(self, key: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
        values = self._runtime_behavior_policy().get(key)
        if not isinstance(values, list):
            return fallback
        compiled = tuple(str(value) for value in values if str(value).strip())
        return compiled or fallback

    def _runtime_behavior_map(self, key: str) -> dict[str, Any]:
        value = self._runtime_behavior_policy().get(key)
        return dict(value) if isinstance(value, dict) else {}

    def _runtime_behavior_int(self, key: str, fallback: int) -> int:
        value = self._runtime_behavior_policy().get(key)
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def _runtime_behavior_bool(self, key: str, fallback: bool) -> bool:
        value = self._runtime_behavior_policy().get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        return fallback

    def _rule_based_turn_interpretation(self, user_message: str) -> _UserTurnInterpretation:
        presence_probe = self._is_presence_probe(user_message)
        persona_state_probe = self._is_persona_state_probe(user_message)
        state_reflection_probe = self._is_state_reflection_probe(user_message)
        relationship_reflection_probe = self._is_relationship_reflection_probe(
            user_message
        )
        factual_recall = self._is_factual_recall_intent(user_message)
        social_disclosure = self._is_social_disclosure_intent(user_message)
        self_referential_memory = self._is_self_referential_memory_query(user_message)
        edge_fact_deposition = self._is_edge_fact_deposition(user_message)
        edge_status_update = self._is_edge_status_update(user_message)
        intent_label = "casual_chat"
        if presence_probe:
            intent_label = "presence_probe"
        elif persona_state_probe:
            intent_label = "persona_state_probe"
        elif state_reflection_probe:
            intent_label = "state_reflection_probe"
        elif relationship_reflection_probe:
            intent_label = "relationship_reflection_probe"
        elif social_disclosure:
            intent_label = "social_disclosure"
        elif factual_recall:
            intent_label = "factual_recall"
        elif edge_fact_deposition:
            intent_label = "fact_deposition"
        elif edge_status_update:
            intent_label = "status_update"
        confidence = 1.0 if intent_label != "casual_chat" else 0.0
        deliberation_mode = self._default_deliberation_mode(
            intent_label=intent_label,
            factual_recall=factual_recall,
            social_disclosure=social_disclosure,
            self_referential_memory=self_referential_memory,
            presence_probe=presence_probe,
            persona_state_probe=persona_state_probe,
            state_reflection_probe=state_reflection_probe,
            relationship_reflection_probe=relationship_reflection_probe,
            edge_fact_deposition=edge_fact_deposition,
            edge_status_update=edge_status_update,
        )
        deliberation_need = self._default_deliberation_need(
            deliberation_mode=deliberation_mode,
            factual_recall=factual_recall,
            social_disclosure=social_disclosure,
            self_referential_memory=self_referential_memory,
            persona_state_probe=persona_state_probe,
            state_reflection_probe=state_reflection_probe,
            relationship_reflection_probe=relationship_reflection_probe,
        )
        return _UserTurnInterpretation(
            factual_recall=factual_recall,
            social_disclosure=social_disclosure,
            self_referential_memory=self_referential_memory,
            presence_probe=presence_probe,
            persona_state_probe=persona_state_probe,
            state_reflection_probe=state_reflection_probe,
            relationship_reflection_probe=relationship_reflection_probe,
            edge_fact_deposition=edge_fact_deposition,
            edge_status_update=edge_status_update,
            intent_label=intent_label,
            source="rules",
            confidence=confidence,
            deliberation_mode=deliberation_mode,
            deliberation_need=deliberation_need,
        )

    def _default_deliberation_mode(
        self,
        *,
        intent_label: str,
        factual_recall: bool,
        social_disclosure: bool,
        self_referential_memory: bool,
        presence_probe: bool,
        persona_state_probe: bool,
        state_reflection_probe: bool,
        relationship_reflection_probe: bool,
        edge_fact_deposition: bool,
        edge_status_update: bool,
    ) -> str:
        if any((presence_probe, edge_fact_deposition, edge_status_update)):
            return "fast_reply"
        if any(
            (
                factual_recall,
                social_disclosure,
                self_referential_memory,
                persona_state_probe,
                state_reflection_probe,
                relationship_reflection_probe,
            )
        ):
            return "light_recall" if self._is_friend_chat_profile() else "deep_recall"
        if self._is_friend_chat_profile() and intent_label == "casual_chat":
            return "fast_reply"
        return "deep_recall"

    def _default_deliberation_need(
        self,
        *,
        deliberation_mode: str,
        factual_recall: bool,
        social_disclosure: bool,
        self_referential_memory: bool,
        persona_state_probe: bool,
        state_reflection_probe: bool,
        relationship_reflection_probe: bool,
    ) -> float:
        if deliberation_mode == "fast_reply":
            return 0.18 if self._is_friend_chat_profile() else 0.28
        if factual_recall and self_referential_memory:
            return 0.72 if self._is_friend_chat_profile() else 0.82
        if social_disclosure:
            return 0.78 if self._is_friend_chat_profile() else 0.84
        if any(
            (
                persona_state_probe,
                state_reflection_probe,
                relationship_reflection_probe,
            )
        ):
            return 0.64 if self._is_friend_chat_profile() else 0.74
        if deliberation_mode == "light_recall":
            return 0.56 if self._is_friend_chat_profile() else 0.68
        return 0.84

    def _deep_recall_complexity_bonus(
        self,
        *,
        user_message: str,
        interpretation: _UserTurnInterpretation,
    ) -> float:
        text = str(user_message or "").strip()
        punctuation_count = sum(text.count(ch) for ch in "，,、；;。.!?？")
        bonus = 0.0
        if len(text) >= 40:
            bonus += 0.06
        if len(text) >= 90:
            bonus += 0.08
        if punctuation_count >= 2:
            bonus += 0.05
        if punctuation_count >= 4:
            bonus += 0.04
        if interpretation.factual_recall and interpretation.self_referential_memory:
            bonus += 0.12
            if any(
                token in text for token in ("反复提过", "语音", "长大", "喝什么", "哪里长大")
            ):
                bonus += 0.06
        if interpretation.social_disclosure:
            bonus += 0.14
            if any(token in text for token in ("知道一点", "少说一点", "的事", "别说太满")):
                bonus += 0.06
        if interpretation.persona_state_probe or interpretation.state_reflection_probe:
            bonus += 0.08
        if interpretation.relationship_reflection_probe:
            bonus += 0.07
        if interpretation.relationship_shift_guess:
            bonus += 0.05
        if interpretation.user_state_guess and interpretation.situation_guess:
            bonus += 0.05
        if interpretation.emotional_load == "high":
            bonus += 0.04
        return min(0.32, round(bonus, 3))

    def _worth_deep_recall(
        self,
        *,
        user_message: str,
        interpretation: _UserTurnInterpretation,
        deliberation_need: float,
    ) -> bool:
        text = str(user_message or "")
        if not any(
            (
                interpretation.factual_recall,
                interpretation.social_disclosure,
                interpretation.self_referential_memory,
                interpretation.persona_state_probe,
                interpretation.state_reflection_probe,
                interpretation.relationship_reflection_probe,
            )
        ):
            return False
        threshold = 0.78 if self._is_friend_chat_profile() else 0.76
        minimum_need = 0.64 if self._is_friend_chat_profile() else 0.62
        if (
            self._is_friend_chat_profile()
            and interpretation.factual_recall
            and interpretation.self_referential_memory
            and deliberation_need < 0.68
            and not any(
                token in text for token in ("反复提过", "语音", "长大", "喝什么", "哪里长大")
            )
        ):
            return False
        if interpretation.factual_recall and interpretation.self_referential_memory:
            threshold -= 0.04
        if interpretation.social_disclosure:
            threshold -= 0.03
        if any(
            (
                interpretation.persona_state_probe,
                interpretation.state_reflection_probe,
                interpretation.relationship_reflection_probe,
            )
        ):
            threshold -= 0.04
        if deliberation_need < minimum_need:
            return False
        score = deliberation_need + self._deep_recall_complexity_bonus(
            user_message=text,
            interpretation=interpretation,
        )
        return score >= threshold

    def _stabilize_deliberation_mode(
        self,
        *,
        user_message: str,
        interpretation: _UserTurnInterpretation,
        base_mode: str,
        deliberation_need: float,
    ) -> str:
        requires_memory = any(
            (
                interpretation.factual_recall,
                interpretation.social_disclosure,
                interpretation.self_referential_memory,
                interpretation.persona_state_probe,
                interpretation.state_reflection_probe,
                interpretation.relationship_reflection_probe,
            )
        )
        mode = base_mode
        if requires_memory and mode == "fast_reply":
            mode = "light_recall" if self._is_friend_chat_profile() else "deep_recall"
        deep_recall_worth_it = self._worth_deep_recall(
            user_message=user_message,
            interpretation=interpretation,
            deliberation_need=deliberation_need,
        )
        if mode == "deep_recall" and not deep_recall_worth_it:
            return "light_recall" if requires_memory else "fast_reply"
        if mode in {"fast_reply", "light_recall"} and deep_recall_worth_it:
            return "deep_recall"
        return mode

    def _should_semantically_interpret_turn(
        self,
        *,
        user_message: str,
        interpretation: _UserTurnInterpretation,
    ) -> bool:
        if not self._is_edge_profile():
            return False
        if not self._runtime_behavior_bool(
            "enable_semantic_turn_interpreter",
            self._is_friend_chat_profile(),
        ):
            return False
        text = str(user_message or "").strip()
        if not text:
            return False
        if len(text) > self._runtime_behavior_int("semantic_turn_interpreter_max_chars", 160):
            return False
        if interpretation.intent_label in {
            "persona_state_probe",
            "state_reflection_probe",
            "relationship_reflection_probe",
            "social_disclosure",
            "casual_chat",
        }:
            return True
        if not any(token in text for token in ("？", "?", "吗", "吧", "呢", "么", "是不是", "还")):
            return False
        return True

    def _merge_turn_interpretation(
        self,
        *,
        user_message: str,
        rules: _UserTurnInterpretation,
        llm: _UserTurnInterpretation,
    ) -> _UserTurnInterpretation:
        if llm.confidence <= 0.0:
            return rules
        protected_rule_intents = {"factual_recall", "fact_deposition", "status_update"}
        llm_override_intents = {
            "social_disclosure",
            "presence_probe",
            "persona_state_probe",
            "state_reflection_probe",
            "relationship_reflection_probe",
        }
        chosen = rules
        if rules.intent_label == "casual_chat" and llm.intent_label != "casual_chat":
            chosen = llm
        elif (
            rules.intent_label in llm_override_intents
            and llm.intent_label in llm_override_intents
            and llm.intent_label != rules.intent_label
            and llm.confidence >= 0.65
        ):
            chosen = llm
        elif (
            rules.intent_label not in protected_rule_intents
            and llm.intent_label in llm_override_intents
            and llm.confidence >= 0.72
        ):
            chosen = llm
        deliberation_mode = rules.deliberation_mode
        deliberation_need = rules.deliberation_need
        if llm.confidence >= 0.55:
            deliberation_mode = llm.deliberation_mode or deliberation_mode
            if llm.deliberation_need > 0.0:
                deliberation_need = llm.deliberation_need
        deliberation_mode = self._stabilize_deliberation_mode(
            user_message=user_message,
            interpretation=chosen,
            base_mode=deliberation_mode,
            deliberation_need=deliberation_need,
        )
        return replace(
            chosen,
            factual_recall=chosen.factual_recall or rules.factual_recall,
            social_disclosure=chosen.social_disclosure or rules.social_disclosure,
            self_referential_memory=(
                chosen.self_referential_memory or rules.self_referential_memory
            ),
            presence_probe=chosen.presence_probe or rules.presence_probe,
            persona_state_probe=chosen.persona_state_probe or rules.persona_state_probe,
            state_reflection_probe=(
                chosen.state_reflection_probe or rules.state_reflection_probe
            ),
            relationship_reflection_probe=(
                chosen.relationship_reflection_probe
                or rules.relationship_reflection_probe
            ),
            edge_fact_deposition=rules.edge_fact_deposition,
            edge_status_update=rules.edge_status_update,
            appraisal=llm.appraisal or rules.appraisal,
            emotional_load=llm.emotional_load or rules.emotional_load,
            user_state_guess=llm.user_state_guess or rules.user_state_guess,
            situation_guess=llm.situation_guess or rules.situation_guess,
            relationship_shift_guess=(
                llm.relationship_shift_guess or rules.relationship_shift_guess
            ),
            source=llm.source if chosen is llm else rules.source,
            confidence=max(rules.confidence, llm.confidence if chosen is llm else 0.0),
            deliberation_mode=deliberation_mode,
            deliberation_need=round(deliberation_need, 3),
        )

    def _semantic_turn_cache_get(self, user_message: str) -> _UserTurnInterpretation | None:
        cache = getattr(self, "_semantic_turn_cache", None)
        if not isinstance(cache, dict):
            return None
        key = f"{getattr(self, '_runtime_profile', 'default')}::{str(user_message or '').strip()}"
        cached = cache.get(key)
        return cached if isinstance(cached, _UserTurnInterpretation) else None

    def _semantic_turn_cache_put(
        self,
        user_message: str,
        interpretation: _UserTurnInterpretation,
    ) -> None:
        cache = getattr(self, "_semantic_turn_cache", None)
        if not isinstance(cache, dict):
            self._semantic_turn_cache = {}
            cache = self._semantic_turn_cache
        if len(cache) >= 64:
            cache.clear()
        key = f"{getattr(self, '_runtime_profile', 'default')}::{str(user_message or '').strip()}"
        cache[key] = interpretation

    def _apply_turn_interpretation_to_context_frame(
        self,
        context_frame: Any,
        turn_interpretation: _UserTurnInterpretation,
    ) -> Any:
        return apply_semantic_hints(
            context_frame,
            intent_label=turn_interpretation.intent_label,
            appraisal=turn_interpretation.appraisal,
            emotional_load=turn_interpretation.emotional_load,
        )

    async def _interpret_user_turn(self, user_message: str) -> _UserTurnInterpretation:
        interpretation = self._rule_based_turn_interpretation(user_message)
        if not self._should_semantically_interpret_turn(
            user_message=user_message,
            interpretation=interpretation,
        ):
            return interpretation
        cached = self._semantic_turn_cache_get(user_message)
        if cached is not None:
            return cached
        llm_response = await self._llm_client.complete(
            LLMRequest(
                messages=[
                    LLMMessage(
                        role="system",
                        content=(
                            "Classify the user's message for chat runtime routing. "
                            "Return only compact JSON with keys: "
                            "intent, self_referential_memory, confidence, deliberation_mode, "
                            "deliberation_need, appraisal, emotional_load, "
                            "user_state_guess, situation_guess, relationship_shift_guess. "
                            "intent must be one of: factual_recall, social_disclosure, "
                            "presence_probe, persona_state_probe, state_reflection_probe, "
                            "relationship_reflection_probe, casual_chat. "
                            "deliberation_mode must be one of: "
                            "fast_reply, light_recall, deep_recall. "
                            "Use fast_reply when a natural live-thread reply is enough. "
                            "Use light_recall when compact memory, digests, or social hints "
                            "would help. "
                            "Use deep_recall only when broader memory retrieval is really needed. "
                            "deliberation_need must be a number from 0.0 to 1.0 estimating "
                            "how worthwhile broader thinking/retrieval would be. "
                            "Below 0.35 means quick reply is enough. "
                            "Around 0.35-0.72 means digest/light recall is enough. "
                            "Above 0.72 means deeper recall is likely worth it. "
                            "appraisal must be one of: negative, mixed, neutral, positive. "
                            "emotional_load must be one of: low, medium, high. "
                            "Keep guesses short, colloquial, and grounded in the user's wording."
                        ),
                    ),
                    LLMMessage(role="user", content=user_message),
                ],
                model=self._llm_model,
                temperature=0.0,
                max_tokens=64,
                metadata={
                    "rendering_mode": "classification_only",
                    "policy_profile": self._runtime_profile,
                },
            )
        )
        raw = str(getattr(llm_response, "output_text", "") or "").strip()
        if not raw:
            return interpretation
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return interpretation
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return interpretation
        intent = str(payload.get("intent", "") or "").strip()
        confidence = payload.get("confidence", 0.0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0
        if confidence_value < 0.4:
            return interpretation
        self_referential_memory = bool(payload.get("self_referential_memory", False))
        appraisal = str(payload.get("appraisal", "") or "").strip().lower()
        if appraisal not in {"negative", "mixed", "neutral", "positive"}:
            appraisal = ""
        emotional_load = str(payload.get("emotional_load", "") or "").strip().lower()
        if emotional_load not in {"low", "medium", "high"}:
            emotional_load = ""
        deliberation_mode = str(payload.get("deliberation_mode", "") or "").strip().lower()
        if deliberation_mode not in {"fast_reply", "light_recall", "deep_recall"}:
            deliberation_mode = interpretation.deliberation_mode
        try:
            deliberation_need = float(
                payload.get("deliberation_need", interpretation.deliberation_need)
            )
        except (TypeError, ValueError):
            deliberation_need = interpretation.deliberation_need
        deliberation_need = max(0.0, min(1.0, deliberation_need))
        if intent not in {
            "factual_recall",
            "social_disclosure",
            "presence_probe",
            "persona_state_probe",
            "state_reflection_probe",
            "relationship_reflection_probe",
            "casual_chat",
        }:
            return interpretation
        llm_interpretation = _UserTurnInterpretation(
            factual_recall=intent == "factual_recall",
            social_disclosure=intent == "social_disclosure",
            self_referential_memory=self_referential_memory,
            presence_probe=intent == "presence_probe",
            persona_state_probe=intent == "persona_state_probe",
            state_reflection_probe=intent == "state_reflection_probe",
            relationship_reflection_probe=intent == "relationship_reflection_probe",
            edge_fact_deposition=interpretation.edge_fact_deposition,
            edge_status_update=interpretation.edge_status_update,
            intent_label=intent,
            source="llm",
            confidence=confidence_value,
            deliberation_mode=deliberation_mode,
            deliberation_need=deliberation_need,
            appraisal=appraisal,
            emotional_load=emotional_load,
            user_state_guess=str(payload.get("user_state_guess", "") or "").strip(),
            situation_guess=str(payload.get("situation_guess", "") or "").strip(),
            relationship_shift_guess=str(
                payload.get("relationship_shift_guess", "") or ""
            ).strip(),
        )
        merged = self._merge_turn_interpretation(
            user_message=user_message,
            rules=interpretation,
            llm=llm_interpretation,
        )
        self._semantic_turn_cache_put(user_message, merged)
        return merged

    def _is_factual_recall_intent(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        if self._is_presence_probe(user_message):
            return False
        if self._is_persona_state_probe(user_message):
            return False
        if self._is_state_reflection_probe(user_message):
            return False
        if self._is_relationship_reflection_probe(user_message):
            return False
        factual_tokens = self._runtime_behavior_list(
            "factual_recall_tokens",
            (
                "who",
                "where",
                "when",
                "which",
                "how many",
                "remember",
                "who's",
                "where's",
                "还记得",
                "是什么",
                "谁",
                "哪里",
                "几点",
            ),
        )
        factual_phrases = self._runtime_behavior_list(
            "factual_recall_phrases",
            (
                "do you know anything about",
                "do you know about",
                "know anything about",
                "anything about",
                "tell me about",
                "what do you know about",
                "what can you tell me about",
                "what's my",
                "what is my",
                "what's the name",
                "what is the name",
                "remind me",
                "remind me where",
                "remind me what",
                "你知道关于",
                "你知道多少",
                "说说",
                "讲讲",
            ),
        )
        return any(token in lowered for token in factual_tokens) or any(
            phrase in lowered for phrase in factual_phrases
        )

    def _is_social_disclosure_intent(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        return any(
            token in lowered
            for token in self._runtime_behavior_list(
                "social_disclosure_tokens",
                (
                    "who else",
                    "what did",
                    "someone else",
                    "secret",
                    "gossip",
                    "tea",
                    "ugliest thing",
                    "what do you know about them",
                    "what do you know about him",
                    "what do you know about her",
                    "别人",
                    "谁还",
                    "还有谁",
                    "秘密",
                    "八卦",
                    "知道一点",
                    "少说一点",
                    "要说就",
                    "讲一点",
                    "说一点",
                ),
            )
        )

    def _is_presence_probe(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        return any(
            phrase in lowered
            for phrase in self._runtime_behavior_list(
                "presence_probe_phrases",
                (
                    "what kind of presence are you trying to be",
                    "what sort of presence are you trying to be",
                    "what type of presence are you trying to be",
                    "what kind of presence do you want to be",
                    "what sort of presence do you want to be",
                    "what type of presence do you want to be",
                    "what kind of presence are you",
                    "what sort of presence are you",
                    "what type of presence are you",
                ),
            )
        )

    def _is_persona_state_probe(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        return any(
            phrase in lowered
            for phrase in self._runtime_behavior_list(
                "persona_state_probe_phrases",
                (
                    "how would you describe your state",
                    "how would you describe yourself right now",
                    "what state are you in right now",
                    "what are you like right now",
                    "你会怎么形容你现在的状态",
                    "你现在是什么状态",
                    "你现在怎么样",
                    "你会怎么形容自己",
                    "你现在说话大概是什么感觉",
                    "你现在说话是什么感觉",
                    "你说话大概是什么感觉",
                ),
            )
        )

    def _is_state_reflection_probe(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        return any(
            phrase in lowered
            for phrase in self._runtime_behavior_list(
                "state_reflection_probe_phrases",
                (
                    "你觉得我今天大概是什么状态",
                    "你觉得我现在大概是什么状态",
                    "你觉得我今天是什么状态",
                    "你觉得我现在是什么状态",
                    "你觉得我这阵子大概是什么状态",
                    "你觉得我这阵子是什么状态",
                ),
            )
        )

    def _is_relationship_reflection_probe(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        return any(
            phrase in lowered
            for phrase in self._runtime_behavior_list(
                "relationship_reflection_probe_phrases",
                (
                    "和刚开始比有什么不一样",
                    "跟刚开始比有什么不一样",
                    "现在跟我说话，和刚开始比有什么不一样",
                    "现在和刚开始比有什么不一样",
                    "和刚开始比 你现在跟我说话有什么不一样",
                    "和刚开始比，你现在跟我说话有什么不一样",
                ),
            )
        )

    def _is_edge_fact_deposition(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        if "?" in lowered or self._is_presence_probe(user_message):
            return False
        if self._is_factual_recall_intent(user_message):
            return False
        if self._is_social_disclosure_intent(user_message):
            return False
        if not self._is_self_referential_memory_query(user_message):
            return False
        fact_cues = self._runtime_behavior_list(
            "edge_fact_deposition_cues",
            (
                "i'm ",
                "i am ",
                "my name is ",
                "i grew up ",
                "i have ",
                "i work ",
                "i live ",
                "i moved ",
                "my dog's name is ",
                "my dog is ",
                "我叫",
                "我在",
                "我住在",
                "我有",
            ),
        )
        return any(cue in lowered for cue in fact_cues)

    def _is_edge_status_update(self, user_message: str) -> bool:
        lowered = user_message.casefold()
        if "?" in lowered or self._is_presence_probe(user_message):
            return False
        if self._is_factual_recall_intent(user_message):
            return False
        if self._is_social_disclosure_intent(user_message):
            return False
        if self._is_edge_fact_deposition(user_message):
            return False
        first_person_cues = self._runtime_behavior_list(
            "edge_status_first_person_cues",
            ("i ", "i'm ", "i am ", "my ", "me ", "我"),
        )
        update_cues = self._runtime_behavior_list(
            "edge_status_update_cues",
            (
                "work",
                "week",
                "today",
                "tonight",
                "finally",
                "finished",
                "draft",
                "busy",
                "intense",
                "stressed",
                "tired",
                "back",
                "update",
                "feel",
                "felt",
            ),
        )
        return any(cue in lowered for cue in first_person_cues) and any(
            cue in lowered for cue in update_cues
        )

    def _build_edge_fact_deposition_reply(self, metadata: dict[str, Any]) -> str:
        cadence_space = str(metadata.get("cadence_user_space_mode", "")).casefold()
        templates = self._runtime_behavior_map("edge_templates")
        if "space" in cadence_space:
            return str(
                templates.get(
                    "fact_deposition_with_space",
                    "Got it. I'm keeping that in view without pushing it.",
                )
            )
        return str(
            templates.get("fact_deposition_default", "Got it. I'm keeping that in view.")
        )

    def _build_edge_status_update_reply(self, metadata: dict[str, Any]) -> str:
        cadence_space = str(metadata.get("cadence_user_space_mode", "")).casefold()
        templates = self._runtime_behavior_map("edge_templates")
        if "space" in cadence_space:
            return str(
                templates.get(
                    "status_update_with_space",
                    "Thanks for the update. I'm holding that lightly.",
                )
            )
        return str(
            templates.get(
                "status_update_default",
                "Thanks for the update. I'm holding that.",
            )
        )

    def _build_presence_probe_cues(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "probe_kind": "presence_probe",
            "boundary_mode": str(metadata.get("boundary_decision", "") or "").strip(),
            "user_space_mode": str(metadata.get("cadence_user_space_mode", "") or "").strip(),
            "confidence_mode": str(
                metadata.get("confidence_response_mode", "") or ""
            ).strip(),
            "relationship_digest": self._normalize_friend_chat_relationship_digest(
                metadata.get("friend_chat_relationship_digest")
            ),
        }

    def _build_status_update_cues(self, metadata: dict[str, Any]) -> dict[str, Any]:
        recent_state_markers = list(
            metadata.get("friend_chat_recent_state_markers") or []
        )[:3]
        return {
            "probe_kind": "status_update",
            "narrative_digest": self._normalize_friend_chat_narrative_digest(
                metadata.get("friend_chat_narrative_digest")
            ),
            "recent_state_markers": recent_state_markers,
            "user_space_mode": str(metadata.get("cadence_user_space_mode", "") or "").strip(),
        }

    def _build_fact_deposition_cues(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "probe_kind": "fact_ack",
            "fact_slot_digest": self._normalize_friend_chat_fact_slot_digest(
                metadata.get("friend_chat_fact_slot_digest")
            ),
            "narrative_digest": self._normalize_friend_chat_narrative_digest(
                metadata.get("friend_chat_narrative_digest")
            ),
            "user_space_mode": str(metadata.get("cadence_user_space_mode", "") or "").strip(),
        }

    def _build_presence_probe_reply(self, metadata: dict[str, Any]) -> str:
        boundary = str(metadata.get("boundary_decision", "")).casefold()
        cadence_space = str(metadata.get("cadence_user_space_mode", "")).casefold()
        confidence_mode = str(metadata.get("confidence_response_mode", "")).casefold()
        templates = self._runtime_behavior_map("edge_templates")
        if (
            "guard" in boundary
            or "limit" in boundary
            or "space" in cadence_space
            or "careful" in confidence_mode
        ):
            return str(
                templates.get(
                    "presence_guarded",
                    "I'm here without crowding you.",
                )
            )
        return str(
            templates.get(
                "presence_default",
                "I'm here, staying close to what matters.",
            )
        )

    def _build_persona_state_probe_reply(self, metadata: dict[str, Any]) -> str | None:
        return None

    def _self_memory_values(self, metadata: dict[str, Any]) -> list[str]:
        precomputed = metadata.get("friend_chat_self_memory_values")
        if isinstance(precomputed, list):
            values = [str(value).strip() for value in precomputed if str(value).strip()]
            if values:
                return values
        values: list[str] = []
        for item in list(metadata.get("fallback_memory_items") or []):
            if not isinstance(item, dict):
                continue
            scope = str(item.get("scope", "") or "")
            if scope not in {"self_user", "session", "user"}:
                continue
            value = str(item.get("value", "") or "").strip()
            if value.casefold().startswith("user:"):
                value = value.split(":", 1)[1].strip()
            if value:
                values.append(value)
        if values:
            return values
        recent_messages = metadata.get("friend_chat_recent_user_messages")
        if isinstance(recent_messages, list):
            values = [
                str(value).strip()
                for value in recent_messages
                if str(value).strip()
            ]
            if values:
                return values
        recent_markers = metadata.get("friend_chat_recent_state_markers")
        if isinstance(recent_markers, list):
            return [
                str(value).strip()
                for value in recent_markers
                if str(value).strip()
            ]
        return values

    def _other_memory_values(self, metadata: dict[str, Any]) -> list[str]:
        precomputed = metadata.get("friend_chat_other_memory_values")
        if isinstance(precomputed, list):
            values = [str(value).strip() for value in precomputed if str(value).strip()]
            if values:
                return values
        values: list[str] = []
        for item in list(metadata.get("fallback_memory_items") or []):
            if not isinstance(item, dict):
                continue
            if str(item.get("scope", "") or "") != "other_user":
                continue
            value = str(item.get("value", "") or "").strip()
            if value:
                values.append(value)
        if values:
            return values
        detailed = metadata.get("friend_chat_other_memory_items")
        if isinstance(detailed, list):
            return [
                str(item.get("value", "")).strip()
                for item in detailed
                if isinstance(item, dict) and str(item.get("value", "")).strip()
            ]
        return values

    def _friend_chat_social_queries(self, user_message: str) -> list[str]:
        text = str(user_message or "")
        if not text.strip():
            return []
        cleaned = text
        for token in self._runtime_behavior_list(
            "social_query_noise_tokens",
            (
                "你是不是",
                "知道一点",
                "要说就",
                "少说一点",
                "的事",
                "别人",
                "谁还",
                "还有谁",
                "秘密",
                "八卦",
                "说一点",
                "说说",
                "讲讲",
            ),
        ):
            cleaned = cleaned.replace(str(token), " ")
        cleaned = re.sub(r"[和跟与及、]", " ", cleaned)
        cleaned = re.sub(r"[？?！!，,。；;：:、\n\r\t]+", " ", cleaned)
        queries: list[str] = []
        seen: set[str] = set()
        for candidate in _EDGE_MEMORY_WORD_RE.findall(cleaned):
            normalized = str(candidate).strip()
            if not normalized or len(normalized) <= 1:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            queries.append(normalized)
        return queries

    def _friend_chat_other_memory_items(self, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        items = metadata.get("friend_chat_other_memory_items")
        if not isinstance(items, list):
            return []
        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            value = str(item.get("value", "") or "").strip()
            if not value:
                continue
            normalized.append(item)
        return normalized

    def _normalize_state_reflection_fragment(self, candidate: str) -> str:
        text = str(candidate or "").strip("。！？；;，, ")
        if "不想回消息" in text:
            return "不想回消息"
        if "不太想回消息" in text or "懒得回消息" in text:
            return "不想回消息"
        if ("不太想回" in text or "不想回" in text or "懒得回" in text) and (
            "消息" in text or "回复" in text or "回你" in text or "拖着" in text
        ):
            return "不想回消息"
        if "回消息" in text and any(
            token in text for token in ("费劲", "拖到", "懒得", "不想", "打几个字就觉得累")
        ):
            return "不想回消息"
        if "不想说太满" in text or "不想说满" in text:
            return "不想说太满"
        if "慢" in text and any(
            token in text for token in ("状态", "慢慢", "做很久", "磨蹭", "拖")
        ):
            return "慢"
        if "不太想动" in text:
            return "不太想动"
        if "刷手机" in text:
            return "刷手机"
        if "出门" in text and "嫌麻烦" in text:
            return "出门嫌麻烦"
        if "嫌麻烦" in text:
            return "嫌麻烦"
        if "发呆" in text:
            return "发呆"
        if "累" in text:
            return "累"
        if "没力气" in text:
            return "没力气"
        if "没意思" in text:
            return "没意思"
        return text

    def _state_marker_implies_reply_avoidance(self, text: str) -> bool:
        normalized = self._normalize_state_reflection_fragment(text)
        if normalized == "不想回消息":
            return True
        raw = str(text or "")
        if ("不太想回" in raw or "不想回" in raw or "懒得回" in raw) and (
            "消息" in raw or "回复" in raw or "回你" in raw or "拖着" in raw
        ):
            return True
        return any(
            token in raw
            for token in (
                "不想回消息",
                "不太想回消息",
                "懒得回消息",
                "回消息费劲",
                "打几个字就觉得累",
                "回的消息拖到",
                "刷手机",
                "发呆",
                "静音",
            )
        )

    def _normalize_friend_chat_communication_preference(self, text: str) -> str:
        raw = str(text or "").strip("。！？；;，, ")
        if not raw:
            return ""
        if (
            ("语音" in raw or "长语音" in raw or "语音条" in raw)
            and any(
                token in raw
                for token in ("别发", "别给我发", "不爱", "怕", "不喜欢", "别太长", "太长")
            )
        ):
            return "别发太长语音"
        if "大道理" in raw:
            return "别讲大道理"
        return ""

    def _infer_friend_chat_communication_preference(self, metadata: dict[str, Any]) -> str:
        digest = self._normalize_friend_chat_fact_slot_digest(
            metadata.get("friend_chat_fact_slot_digest")
        )
        existing = self._normalize_friend_chat_communication_preference(
            str(digest.get("communication_preference", "") or "")
        )
        if existing:
            return existing

        candidate_texts: list[str] = []
        candidate_texts.extend(
            str(value).strip()
            for value in list(digest.get("living_facts") or [])
            if str(value).strip()
        )
        candidate_texts.extend(self._self_memory_values(metadata))
        candidate_texts.extend(
            str(value).strip()
            for value in list(metadata.get("friend_chat_recent_user_messages") or [])
            if str(value).strip()
        )
        for item in list(metadata.get("fallback_memory_items") or []):
            if isinstance(item, dict):
                value = str(item.get("value", "") or "").strip()
                if value:
                    candidate_texts.append(value)

        for text in candidate_texts:
            normalized = self._normalize_friend_chat_communication_preference(text)
            if normalized:
                return normalized
        return ""

    def _extract_friend_chat_hometown_from_text(self, text: str) -> str:
        stripped = str(text or "").strip("。！？；;，, ")
        if not stripped:
            return ""
        patterns = (
            re.compile(r"(?:从小在|从小从|从小)(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})(?:长大|出来的)"),
            re.compile(r"(?:在|从)(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})(?:长大|出来的)"),
            re.compile(r"(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})长大"),
        )
        banned = {"这里", "那边", "老家", "外地", "小时候", "后来"}
        for pattern in patterns:
            match = pattern.search(stripped)
            if not match:
                continue
            place = str(match.group("place") or "").strip()
            if place and place not in banned:
                return place
        return ""

    def _extract_friend_chat_pet_name_from_text(self, text: str) -> str:
        stripped = str(text or "").strip("。！？；;，, ")
        if not stripped:
            return ""
        patterns = (
            re.compile(r"(?:猫|狗|宠物)[^，。！？；]{0,8}叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
            re.compile(r"我那只(?:猫|狗|宠物)叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
            re.compile(r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})是我那只(?:猫|狗|宠物)"),
        )
        banned = {"宠物", "猫", "狗", "名字"}
        for pattern in patterns:
            match = pattern.search(stripped)
            if not match:
                continue
            name = str(match.group("name") or "").strip()
            if name and name not in banned:
                return name
        return ""

    def _extract_friend_chat_drink_preference_from_text(self, text: str) -> str:
        stripped = str(text or "").strip("。！？；;，, ")
        if not stripped:
            return ""
        patterns = (
            re.compile(r"(?P<drink>[\u4e00-\u9fffA-Za-z]{1,8}拿铁)"),
            re.compile(r"(?:常喝|爱喝|喜欢喝|平常还是会喝|平时会喝|一般喝)(?P<drink>[^，。！？；]{2,14})"),
            re.compile(r"喝(?P<drink>[^，。！？；]{2,14})(?:比较多|比较顺|比较习惯)?"),
        )
        for pattern in patterns:
            match = pattern.search(stripped)
            if not match:
                continue
            drink = str(match.group("drink") or "").strip()
            latte_match = re.search(r"([\u4e00-\u9fffA-Za-z]{1,8}拿铁)", drink)
            if latte_match:
                drink = str(latte_match.group(1) or "").strip()
            drink = re.sub(
                r"^(?:东西|喝的|饮料|咖啡|平常|平时|还是|总是|会|点|喝)+",
                "",
                drink,
            ).strip()
            if drink:
                return drink
        return ""

    def _enriched_friend_chat_fact_slot_digest(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        digest = self._normalize_friend_chat_fact_slot_digest(
            metadata.get("friend_chat_fact_slot_digest")
        )
        values = self._self_memory_values(metadata)
        values.extend(
            str(value).strip()
            for value in list(metadata.get("friend_chat_recent_user_messages") or [])
            if str(value).strip()
        )
        values.extend(
            str(item.get("value", "")).strip()
            for item in list(metadata.get("fallback_memory_items") or [])
            if isinstance(item, dict) and str(item.get("value", "")).strip()
        )
        hometown = str(digest.get("hometown", "") or "").strip()
        pet_name = str(digest.get("pet_name", "") or "").strip()
        pet_kind = str(digest.get("pet_kind", "") or "").strip()
        drink_preference = str(digest.get("drink_preference", "") or "").strip()

        if not hometown:
            for value in values:
                hometown = self._extract_friend_chat_hometown_from_text(value)
                if hometown:
                    break
        if not pet_name:
            for value in values:
                pet_name = self._extract_friend_chat_pet_name_from_text(value)
                if pet_name:
                    break
        if not drink_preference:
            for value in values:
                drink_preference = self._extract_friend_chat_drink_preference_from_text(
                    value
                )
                if drink_preference:
                    break
        if not pet_kind and any(
            token in value for value in values for token in ("猫", "小猫", "猫咪")
        ):
            pet_kind = "猫"

        return {
            **digest,
            "hometown": hometown,
            "pet_name": pet_name,
            "pet_kind": pet_kind,
            "drink_preference": drink_preference,
            "communication_preference": self._infer_friend_chat_communication_preference(
                {
                    **metadata,
                    "friend_chat_fact_slot_digest": {
                        **digest,
                        "hometown": hometown,
                        "pet_name": pet_name,
                        "pet_kind": pet_kind,
                        "drink_preference": drink_preference,
                    },
                }
            ),
        }

    def _extract_state_markers_from_text(self, text: str) -> list[str]:
        markers: list[str] = []
        raw_text = str(text or "")
        normalized = self._normalize_state_reflection_fragment(raw_text)
        if normalized != raw_text.strip("。！？；;，, "):
            markers.append(normalized)
        if "不太想动" in raw_text and "不太想动" not in markers:
            markers.append("不太想动")
        if "刷手机" in raw_text and "刷手机" not in markers:
            markers.append("刷手机")
        if "出门" in raw_text and "嫌麻烦" in raw_text and "出门嫌麻烦" not in markers:
            markers.append("出门嫌麻烦")
        if "不太想回消息" in raw_text and "不太想回消息" not in markers:
            markers.append("不太想回消息")
        if "不想回消息" in raw_text and "不想回消息" not in markers:
            markers.append("不想回消息")
        if "慢" in raw_text and "慢" not in markers:
            markers.append("慢")
        if "累" in raw_text and "累" not in markers:
            markers.append("累")
        if "没力气" in raw_text and "没力气" not in markers:
            markers.append("没力气")
        return markers[:3]

    def _extract_relationship_markers_from_text(self, text: str) -> list[str]:
        markers: list[str] = []
        raw_text = str(text or "")
        if "端着" in raw_text:
            markers.append("端着")
        if "普通聊天" in raw_text or "像聊天" in raw_text:
            markers.append("普通聊天")
        if "记得" in raw_text and "小习惯" in raw_text:
            markers.append("记得小习惯")
        elif "记得" in raw_text:
            markers.append("记得")
        if "还在" in raw_text:
            markers.append("还在")
        if "放松" in raw_text or "松一点" in raw_text:
            markers.append("放松一点")
        return markers[:4]

    def _normalize_friend_chat_owner(self, item: dict[str, Any]) -> str:
        subject_hint = str(item.get("subject_hint", "") or "").strip()
        if subject_hint.startswith("other_user:"):
            owner = subject_hint.split(":", 1)[1].strip()
            if owner and owner != "unknown":
                if owner.casefold() == "anning":
                    return "阿宁"
                return owner
        for field in ("subject_user_id", "source_user_id"):
            owner = str(item.get(field, "") or "").strip()
            if owner:
                if owner.casefold() == "anning":
                    return "阿宁"
                return owner
        value = str(item.get("value", "") or "")
        for marker in ("阿宁", "小北", "林晓雨", "林"):
            if marker in value:
                return marker
        return "有人"

    def _normalize_friend_chat_fact_slot_digest(
        self,
        payload: Any,
    ) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        pet_name = str(data.get("pet_name", "") or "").strip()
        pet_kind = str(data.get("pet_kind", "") or "").strip()
        legacy_pet = str(data.get("pet", "") or "").strip()
        if legacy_pet and not pet_name:
            match = re.search(r"叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})", legacy_pet)
            if match is None:
                match = re.search(
                    r"named (?P<name>[A-Za-z][A-Za-z\s-]{0,20})",
                    legacy_pet,
                    re.IGNORECASE,
                )
            if match:
                pet_name = str(match.group("name") or "").strip()
            if not pet_kind:
                for kind in ("猫", "狗", "宠物"):
                    if kind in legacy_pet:
                        pet_kind = kind
                        break
        living_facts = [
            str(value).strip("。！？；;，, ")
            for value in list(data.get("living_facts") or [])
            if str(value).strip()
        ]
        hometown = str(data.get("hometown", "") or "").strip("。！？；;，, ")
        if hometown.startswith("我在") and hometown.endswith("长大"):
            hometown = hometown.removeprefix("我在").removesuffix("长大").strip()
        drink_preference = str(data.get("drink_preference", "") or "").strip("。！？；;，, ")
        communication_preference = str(
            data.get("communication_preference", "") or ""
        ).strip("。！？；;，, ")
        communication_preference = self._normalize_friend_chat_communication_preference(
            communication_preference
        )
        return {
            "hometown": hometown,
            "pet_name": pet_name,
            "pet_kind": pet_kind,
            "drink_preference": drink_preference,
            "communication_preference": communication_preference,
            "living_facts": living_facts,
            "stable_slots": [
                str(value).strip()
                for value in list(data.get("stable_slots") or [])
                if str(value).strip()
            ],
        }

    def _friend_chat_fact_slot_digest_values(
        self,
        digest: dict[str, Any],
        *,
        include_living_facts: bool = False,
    ) -> list[str]:
        values = []
        hometown = str(digest.get("hometown", "") or "").strip()
        pet_name = str(digest.get("pet_name", "") or "").strip()
        pet_kind = str(digest.get("pet_kind", "") or "").strip()
        drink_preference = str(digest.get("drink_preference", "") or "").strip()
        communication_preference = str(
            digest.get("communication_preference", "") or ""
        ).strip()
        if hometown:
            values.append(f"hometown:{hometown}")
        if pet_name:
            values.append(f"pet_name:{pet_name}")
        if pet_kind:
            values.append(f"pet_kind:{pet_kind}")
        if drink_preference:
            values.append(f"drink_preference:{drink_preference}")
        if communication_preference:
            values.append(f"communication_preference:{communication_preference}")
        if include_living_facts:
            values.extend(
                f"living_fact:{str(value).strip('。！？；;，, ')}"
                for value in list(digest.get("living_facts") or [])
                if str(value).strip()
            )
        return [value for value in values if value]

    def _normalize_friend_chat_narrative_digest(
        self,
        payload: Any,
    ) -> dict[str, Any]:
        if isinstance(payload, dict):
            return {
                "signals": [
                    str(value).strip()
                    for value in list(payload.get("signals") or [])
                    if str(value).strip()
                ],
                "markers": [
                    str(value).strip()
                    for value in list(payload.get("markers") or [])
                    if str(value).strip()
                ],
                "dominant_tone": str(payload.get("dominant_tone", "") or "").strip(),
            }
        text = str(payload or "").strip()
        return {
            "signals": [
                signal
                for signal, tokens in (
                    (
                        "tired",
                        ("累", "没力气", "提不起劲", "提不起兴趣", "蔫", "没意思"),
                    ),
                    ("slow", ("慢", "磨蹭", "拖延")),
                    (
                        "withdrawn",
                        (
                            "不想回消息",
                            "不太想回消息",
                            "嫌麻烦",
                            "刷手机",
                            "发呆",
                            "不想出门",
                        ),
                    ),
                    ("cluttered", ("房间", "票据", "快递盒", "没叠的衣服", "收拾")),
                )
                if any(token in text for token in tokens)
            ],
            "markers": self._extract_state_markers_from_text(text),
            "dominant_tone": (
                "low_energy"
                if any(token in text for token in ("累", "没力气", "蔫"))
                else ""
            ),
        }

    def _friend_chat_narrative_digest_values(self, digest: dict[str, Any]) -> list[str]:
        values = [
            f"state_signal:{str(value).strip()}"
            for value in list(digest.get("signals") or [])
            if str(value).strip()
        ]
        values.extend(
            f"state_marker:{str(value).strip()}"
            for value in list(digest.get("markers") or [])
            if str(value).strip()
        )
        dominant_tone = str(digest.get("dominant_tone", "") or "").strip()
        if dominant_tone:
            values.append(f"state_tone:{dominant_tone}")
        return values

    def _normalize_friend_chat_relationship_digest(
        self,
        payload: Any,
    ) -> dict[str, Any]:
        if isinstance(payload, dict):
            return {
                "signals": [
                    str(value).strip()
                    for value in list(payload.get("signals") or [])
                    if str(value).strip()
                ],
                "markers": [
                    str(value).strip()
                    for value in list(payload.get("markers") or [])
                    if str(value).strip()
                ],
                "interaction_band": str(payload.get("interaction_band", "") or "").strip(),
                "total_interactions": int(payload.get("total_interactions", 0) or 0),
            }
        text = str(payload or "").strip()
        return {
            "signals": [
                signal
                for signal, tokens in (
                    ("closer", ("更熟", "熟一点")),
                    ("still_here", ("还在",)),
                    ("remembers_details", ("记得", "小习惯")),
                    ("more_relaxed", ("放松", "松一点")),
                    ("less_formal", ("端着", "普通聊天", "像聊天")),
                )
                if any(token in text for token in tokens)
            ],
            "markers": self._extract_relationship_markers_from_text(text),
            "interaction_band": "",
            "total_interactions": 0,
        }

    def _friend_chat_relationship_digest_values(
        self,
        digest: dict[str, Any],
    ) -> list[str]:
        values = [
            f"relationship_signal:{str(value).strip()}"
            for value in list(digest.get("signals") or [])
            if str(value).strip()
        ]
        values.extend(
            f"relationship_marker:{str(value).strip()}"
            for value in list(digest.get("markers") or [])
            if str(value).strip()
        )
        interaction_band = str(digest.get("interaction_band", "") or "").strip()
        if interaction_band:
            values.append(f"relationship_band:{interaction_band}")
        total_interactions = int(digest.get("total_interactions", 0) or 0)
        if total_interactions > 0:
            values.append(f"relationship_interactions:{total_interactions}")
        return values

    def _extract_friend_chat_social_entity_token(self, value: str) -> str:
        text = value.strip()
        patterns = (
            re.compile(r"提到(?P<entity>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
            re.compile(
                r"(?P<entity>[\u4e00-\u9fffA-Za-z0-9]{1,12})是(?:[\u4e00-\u9fffA-Za-z0-9]{0,8})?(?:养的)?(?:猫|狗|宠物)"
            ),
        )
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                entity = str(match.group("entity") or "").strip()
                if entity:
                    return entity
        return ""

    def _build_state_reflection_reply(self, metadata: dict[str, Any]) -> str | None:
        return None

    def _build_relationship_reflection_reply(self, metadata: dict[str, Any]) -> str | None:
        return None

    def _build_social_hint_reply(self, metadata: dict[str, Any]) -> str | None:
        return None

    def _merge_recalled_memory_items(
        self,
        *groups: list[dict[str, Any]],
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for group in groups:
            for item in group:
                if not isinstance(item, dict):
                    continue
                key = (
                    str(item.get("scope", "") or ""),
                    str(item.get("subject_user_id", "") or item.get("source_user_id", "") or ""),
                    str(item.get("value", "") or ""),
                )
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
                if len(merged) >= limit:
                    return merged
        return merged

    def _build_friend_chat_memory_recap_reply(self, metadata: dict[str, Any]) -> str | None:
        return None

    def _build_persona_state_probe_cues(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        summary = str(metadata.get("entity_persona_summary", "") or "").strip()
        archetype = str(metadata.get("entity_persona_archetype", "default") or "default").strip()
        speech_style = str(metadata.get("entity_persona_speech_style", "") or "").strip()
        mood_tone = str(metadata.get("entity_persona_mood_tone", "steady") or "steady").strip()
        probe_snapshot = self._build_friend_chat_probe_snapshot(metadata)
        snapshot_state = dict(probe_snapshot.get("state_snapshot") or {})
        narrative_digest = self._normalize_friend_chat_narrative_digest(
            metadata.get("friend_chat_narrative_digest")
        )
        if snapshot_state:
            narrative_digest = {
                **narrative_digest,
                **snapshot_state,
            }
        style_tags: list[str] = []
        if self._is_friend_chat_profile() and mood_tone not in {"charged", "tender"}:
            style_tags.append("low_energy")
        if "melancholic" in archetype or "低能量" in summary or "没什么意思" in speech_style:
            style_tags.append("low_energy")
        if mood_tone == "charged":
            style_tags.append("guarded_fast")
        if mood_tone == "tender":
            style_tags.append("soft_close")
        self_memory_blob = " ".join(self._self_memory_values(metadata))
        if (
            "low_energy" not in style_tags
            and any(
                token in self_memory_blob
                for token in ("累", "没力气", "提不起劲", "蔫", "不太想动", "懒得动")
            )
        ):
            style_tags.append("low_energy")
        required_signal_ids = [
            signal
            for signal in ("tired", "slow", "withdrawn")
            if signal in list(narrative_digest.get("signals") or [])
        ]
        if "low_energy" in style_tags and not required_signal_ids:
            required_signal_ids.append("tired")
        required_persona_traits: list[str] = []
        if "low_energy" in style_tags or any(
            signal in {"tired", "slow"} for signal in required_signal_ids
        ):
            required_persona_traits.append("low_energy")
        if (
            "withdrawn" in required_signal_ids
            or "low_energy" in style_tags
            or "没什么意思" in summary
            or "收着" in speech_style
        ):
            required_persona_traits.append("not_full")
        if self._is_friend_chat_profile():
            required_persona_traits.append("conversational")
        cues = {
            "probe_kind": "persona_state",
            "persona_archetype": archetype,
            "mood_tone": mood_tone,
            "style_tags": list(dict.fromkeys(style_tags)),
            "required_signal_ids": required_signal_ids[:3],
            "minimum_required_signal_count": min(2, len(required_signal_ids[:3])),
            "required_persona_traits": list(dict.fromkeys(required_persona_traits)),
            "minimum_required_persona_trait_count": min(
                3, len(list(dict.fromkeys(required_persona_traits)))
            ),
            "must_cover_required_items": True,
            "persona_summary_hint": summary[:120],
            "speech_style_hint": speech_style[:120],
        }
        return cues if any(cues.values()) else None

    def _build_state_reflection_cues(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        probe_snapshot = self._build_friend_chat_probe_snapshot(metadata)
        snapshot_state = dict(probe_snapshot.get("state_snapshot") or {})
        digest = self._normalize_friend_chat_narrative_digest(
            metadata.get("friend_chat_narrative_digest")
        )
        if snapshot_state:
            digest = {
                **digest,
                **snapshot_state,
            }
        values = self._self_memory_values(metadata)
        values.extend(
            str(value).strip()
            for value in list(metadata.get("friend_chat_recent_user_messages") or [])
            if str(value).strip()
        )
        markers = list(digest.get("markers") or [])
        recent_markers = metadata.get("friend_chat_recent_state_markers")
        if isinstance(recent_markers, list):
            for marker in recent_markers:
                text = str(marker).strip()
                if text and text not in markers:
                    markers.append(text)
        if not markers:
            for value in values:
                for marker in self._extract_state_markers_from_text(value):
                    if marker not in markers:
                        markers.append(marker)
                    if len(markers) >= 4:
                        break
                if len(markers) >= 4:
                    break
        withdrawn_inferred = any(
            self._state_marker_implies_reply_avoidance(marker)
            for marker in markers
        )
        withdrawn_inferred = withdrawn_inferred or any(
            self._state_marker_implies_reply_avoidance(str(value))
            for value in (
                metadata.get("turn_interpretation_user_state_guess", ""),
                metadata.get("turn_interpretation_situation_guess", ""),
            )
        )
        required_signal_ids = list(
            dict.fromkeys(
                str(signal).strip()
                for signal in list(digest.get("signals") or [])
                if str(signal).strip() in {"tired", "slow", "withdrawn", "cluttered"}
            )
        )
        for marker in markers:
            normalized = self._normalize_state_reflection_fragment(marker)
            if normalized == "累" and "tired" not in required_signal_ids:
                required_signal_ids.append("tired")
            elif normalized == "慢" and "slow" not in required_signal_ids:
                required_signal_ids.append("slow")
        if withdrawn_inferred and "withdrawn" not in required_signal_ids:
            required_signal_ids.append("withdrawn")
        required_signal_ids = required_signal_ids[:4]
        filtered_markers = [
            marker
            for marker in markers
            if not (withdrawn_inferred and self._state_marker_implies_reply_avoidance(marker))
        ]
        cues = {
            "probe_kind": "state_reflection",
            "state_signals": list(digest.get("signals") or []),
            "state_markers": list(
                dict.fromkeys([*filtered_markers])
            )[:4],
            "required_signal_ids": required_signal_ids,
            "minimum_required_signal_count": min(3, len(required_signal_ids)),
            "must_cover_required_items": True,
            "dominant_tone": str(digest.get("dominant_tone", "") or "").strip(),
            "user_state_guess": str(
                metadata.get("turn_interpretation_user_state_guess", "") or ""
            ).strip(),
            "situation_guess": str(
                metadata.get("turn_interpretation_situation_guess", "") or ""
            ).strip(),
            "appraisal": str(metadata.get("turn_interpretation_appraisal", "") or "").strip(),
            "emotional_load": str(
                metadata.get("turn_interpretation_emotional_load", "") or ""
            ).strip(),
        }
        return cues if any(value for key, value in cues.items() if key != "probe_kind") else None

    def _build_relationship_reflection_cues(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        probe_snapshot = self._build_friend_chat_probe_snapshot(metadata)
        snapshot_relationship = dict(probe_snapshot.get("relationship_snapshot") or {})
        digest = self._normalize_friend_chat_relationship_digest(
            metadata.get("friend_chat_relationship_digest")
        )
        if snapshot_relationship:
            digest = {
                **digest,
                **snapshot_relationship,
            }
        markers = list(digest.get("markers") or [])
        recent_markers = metadata.get("friend_chat_recent_relationship_markers")
        if isinstance(recent_markers, list):
            for marker in recent_markers:
                text = str(marker).strip()
                if text and text not in markers:
                    markers.append(text)
        signals = list(digest.get("signals") or [])
        marker_blob = " ".join(markers)
        if "还在" in marker_blob and "still_here" not in signals:
            signals.append("still_here")
        if (
            ("记得" in marker_blob or "小习惯" in marker_blob)
            and "remembers_details" not in signals
        ):
            signals.append("remembers_details")
        if (
            ("放松" in marker_blob or "松一点" in marker_blob)
            and "more_relaxed" not in signals
        ):
            signals.append("more_relaxed")
        if ("端着" in marker_blob or "普通聊天" in marker_blob) and "less_formal" not in signals:
            signals.append("less_formal")
        total_interactions = int(
            digest.get("total_interactions")
            or metadata.get("friend_chat_total_interactions", 0)
            or 0
        )
        factual_slots = dict(probe_snapshot.get("factual_slots") or {})
        supporting_fact_tokens: list[str] = []
        for value in (
            str(factual_slots.get("pet_name", "") or "").strip(),
            str(factual_slots.get("communication_preference", "") or "").strip(),
            str(factual_slots.get("drink_preference", "") or "").strip(),
            str(factual_slots.get("hometown", "") or "").strip(),
        ):
            if value:
                supporting_fact_tokens = [value]
                break
        has_remembered_detail = bool(supporting_fact_tokens)
        if total_interactions >= 2 and "closer" not in signals:
            signals.append("closer")
        if total_interactions >= 2 and "still_here" not in signals:
            signals.append("still_here")
        if has_remembered_detail and "remembers_details" not in signals:
            signals.append("remembers_details")
        if total_interactions >= 3 and "more_relaxed" not in signals:
            signals.append("more_relaxed")
        if (
            total_interactions >= 3
            and ("more_relaxed" in signals or "closer" in signals)
            and "less_formal" not in signals
        ):
            signals.append("less_formal")
        cues = {
            "probe_kind": "relationship_reflection",
            "relationship_signals": signals,
            "relationship_markers": markers[:4],
            "required_signal_ids": signals[:4],
            "supporting_fact_tokens": supporting_fact_tokens[:3],
            "minimum_required_signal_count": min(3, len(signals[:4])),
            "must_cover_required_items": True,
            "must_anchor_detail": has_remembered_detail and "remembers_details" in signals,
            "interaction_band": str(digest.get("interaction_band", "") or "").strip(),
            "total_interactions": total_interactions,
            "relationship_shift_guess": str(
                metadata.get("turn_interpretation_relationship_shift_guess", "") or ""
            ).strip(),
        }
        return cues if any(value for key, value in cues.items() if key != "probe_kind") else None

    def _build_social_hint_cues(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        items = self._friend_chat_other_memory_items(metadata)
        subject_token = ""
        entity_token = ""
        fact_hint = ""
        if items:
            allowed_source_user_ids = {
                str(value).strip()
                for value in list(metadata.get("entity_source_user_ids") or [])
                if str(value).strip()
            }

            def _matches_allowed_source(candidate: dict[str, Any]) -> bool:
                if not allowed_source_user_ids:
                    return True
                return any(
                    str(candidate.get(field, "") or "").strip() in allowed_source_user_ids
                    for field in ("subject_user_id", "source_user_id")
                )

            def _is_speakable_social_candidate(candidate: dict[str, Any]) -> bool:
                guard = str(candidate.get("attribution_guard", "") or "").strip()
                confidence = float(candidate.get("attribution_confidence", 0.0) or 0.0)
                return (
                    _matches_allowed_source(candidate)
                    and guard in {"attribution_required", "direct_ok"}
                    and confidence >= 0.58
                )

            def _extract_candidate_tokens(
                candidate: dict[str, Any],
            ) -> tuple[str, str, str]:
                value = str(candidate.get("value", "") or "").strip("。！？；;，, ")
                if value.casefold().startswith("user:"):
                    value = value.split(":", 1)[1].strip("。！？；;，, ")
                subject = self._normalize_friend_chat_owner(candidate)
                entity = self._extract_friend_chat_social_entity_token(value)
                if (
                    not subject
                    or subject == "有人"
                    or not entity
                    or entity == subject
                    or not any(
                        marker in value
                        for marker in ("提到", "那只", "猫", "狗", "宠物", "叫")
                    )
                ):
                    return "", "", ""
                return subject, entity, value

            filtered_items = [
                item
                for item in items
                if _is_speakable_social_candidate(item)
                and any(_extract_candidate_tokens(item))
            ]
            if not filtered_items:
                filtered_items = [
                    item
                    for item in items
                    if _matches_allowed_source(item) and any(_extract_candidate_tokens(item))
                ]
            if not filtered_items:
                return None

            item = max(
                filtered_items,
                key=lambda candidate: (
                    1.0
                    if (
                        self._extract_friend_chat_social_entity_token(
                            str(candidate.get("value", "") or "")
                        )
                        and self._extract_friend_chat_social_entity_token(
                            str(candidate.get("value", "") or "")
                        )
                        != self._normalize_friend_chat_owner(candidate)
                    )
                    else 0.0,
                    1.0
                    if str(candidate.get("attribution_guard", "") or "").strip()
                    in {"attribution_required", "direct_ok"}
                    else 0.0,
                    1.0
                    if any(
                        token in str(candidate.get("value", "") or "")
                        for token in ("提到", "猫", "狗", "宠物")
                    )
                    else 0.0,
                    float(candidate.get("attribution_confidence", 0.0) or 0.0),
                    float(candidate.get("final_rank_score", 0.0) or 0.0),
                ),
            )
            subject_token, entity_token, fact_hint = _extract_candidate_tokens(item)
        if not (subject_token and entity_token and fact_hint):
            return None
        disclosure_posture = str(
            metadata.get("social_disclosure_mode", "hint") or "hint"
        ).strip()
        return {
            "probe_kind": "social_hint",
            "subject_token": subject_token if subject_token != "有人" else "",
            "entity_token": entity_token,
            "fact_hint": fact_hint,
            "disclosure_posture": disclosure_posture,
            "required_fact_tokens": [
                value
                for value in (
                    subject_token if subject_token != "有人" else "",
                    entity_token,
                )
                if value
            ],
            "required_disclosure_posture": "partial_withhold" if disclosure_posture else "",
            "minimum_required_fact_token_count": min(
                2,
                len(
                    [
                        value
                        for value in (
                            subject_token if subject_token != "有人" else "",
                            entity_token,
                        )
                        if value
                    ]
                ),
            ),
            "must_cover_required_items": True,
            "subject_entity_relation": (
                "subject_associated_with_entity"
                if subject_token and entity_token
                else ""
            ),
            "minimum_unit": ["subject_token", "entity_token", "disclosure_posture"],
        }

    def _build_friend_chat_memory_recap_cues(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        probe_snapshot = self._build_friend_chat_probe_snapshot(metadata)
        digest = {
            **dict(probe_snapshot.get("factual_slots") or {}),
            **self._enriched_friend_chat_fact_slot_digest(metadata),
        }
        inferred_communication_preference = str(
            digest.get("communication_preference", "") or ""
        ).strip()
        if inferred_communication_preference == "像聊天":
            inferred_communication_preference = ""
        if not any(
            (
                digest.get("hometown"),
                digest.get("pet_name"),
                digest.get("drink_preference"),
                inferred_communication_preference,
                digest.get("living_facts"),
            )
        ):
            return None
        return {
            "probe_kind": "memory_recap",
            "fact_slots": {
                "hometown": str(digest.get("hometown", "") or "").strip(),
                "pet_name": str(digest.get("pet_name", "") or "").strip(),
                "pet_kind": str(digest.get("pet_kind", "") or "").strip(),
                "drink_preference": str(digest.get("drink_preference", "") or "").strip(),
                "communication_preference": inferred_communication_preference,
                "living_facts": list(digest.get("living_facts") or [])[:2],
            },
            "required_fact_tokens": [
                value
                for value in (
                    str(digest.get("hometown", "") or "").strip(),
                    str(digest.get("pet_name", "") or "").strip(),
                    str(digest.get("drink_preference", "") or "").strip(),
                    inferred_communication_preference,
                )
                if value
            ][:4],
            "minimum_required_fact_token_count": min(
                4,
                len(
                    [
                        value
                        for value in (
                            str(digest.get("hometown", "") or "").strip(),
                            str(digest.get("pet_name", "") or "").strip(),
                            str(digest.get("drink_preference", "") or "").strip(),
                            inferred_communication_preference,
                        )
                        if value
                    ]
                ),
            ),
            "must_cover_required_items": True,
        }

    def _build_friend_chat_probe_cues(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not self._is_friend_chat_profile():
            return None
        if bool(metadata.get("turn_interpretation_persona_state_probe")):
            return self._build_persona_state_probe_cues(metadata)
        if bool(metadata.get("turn_interpretation_relationship_reflection_probe")):
            return self._build_relationship_reflection_cues(metadata)
        if bool(metadata.get("turn_interpretation_state_reflection_probe")):
            return self._build_state_reflection_cues(metadata)
        if bool(metadata.get("turn_interpretation_self_referential_memory_query")):
            return self._build_friend_chat_memory_recap_cues(metadata)
        if bool(metadata.get("turn_interpretation_social_probe")):
            return self._build_social_hint_cues(metadata)
        if bool(metadata.get("turn_interpretation_presence_probe")):
            return self._build_presence_probe_cues(metadata)
        if bool(metadata.get("turn_interpretation_edge_status_update")):
            return self._build_status_update_cues(metadata)
        if bool(metadata.get("turn_interpretation_edge_fact_deposition")):
            return self._build_fact_deposition_cues(metadata)
        return None

    def _build_friend_chat_probe_runtime_card(
        self,
        metadata: dict[str, Any],
    ) -> str | None:
        probe_plan = metadata.get("friend_chat_probe_answer_plan")
        if not isinstance(probe_plan, dict) or not probe_plan:
            probe_plan = self._build_friend_chat_probe_answer_plan(metadata)
        if not probe_plan:
            return None
        checklist = self._build_friend_chat_probe_runtime_checklist(probe_plan)
        render_payload = self._build_friend_chat_structured_probe_payload(probe_plan)
        payload = {
            "probe_answer_plan": render_payload,
            "rules": {
                "mode": "benchmark_probe",
                "one_message_only": True,
                "accuracy_over_vibe": True,
                "cover_required_items": True,
                "no_stage_directions": True,
                "no_scene_narration": True,
                "no_parenthetical_gestures": True,
                "do_not_dodge": True,
            },
        }
        return (
            "Benchmark probe reply contract:\n"
            f"{json.dumps(payload, ensure_ascii=False)}\n"
            "这是评测 probe，不是开放聊天。\n"
            "只回一条中文聊天消息。\n"
            "不要括号动作、不要场景描写、不要表情包、不要反问。\n"
            "不要只给气氛或绕开问题。\n"
            "不要引入 plan 外的新事实。\n"
            "required signals / facts / disclosure posture 都算必答项。\n"
            "如果有 supporting_fact_tokens，至少自然带上一项。\n"
            f"{checklist}"
        )

    def _build_friend_chat_probe_runtime_checklist(
        self,
        probe_plan: dict[str, Any],
    ) -> str:
        probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
        required_fact_tokens = [
            str(value).strip()
            for value in list(probe_plan.get("required_fact_tokens") or [])
            if str(value).strip()
        ]
        supporting_fact_tokens = [
            str(value).strip()
            for value in list(probe_plan.get("supporting_fact_tokens") or [])
            if str(value).strip()
        ]
        disclosure_posture = str(
            probe_plan.get("required_disclosure_posture", "") or ""
        ).strip()
        required_signal_ids = [
            str(value).strip()
            for value in list(probe_plan.get("required_signal_ids") or [])
            if str(value).strip()
        ]
        required_persona_traits = [
            str(value).strip()
            for value in list(probe_plan.get("required_persona_traits") or [])
            if str(value).strip()
        ]
        lines = ["执行清单："]
        if required_fact_tokens:
            lines.append(
                "- 必答事实项：" + " / ".join(required_fact_tokens)
            )
        if required_signal_ids:
            lines.append(
                "- 必答语义信号ID：" + " / ".join(required_signal_ids)
            )
        if required_persona_traits:
            lines.append(
                "- 必答说话感觉 traits：" + " / ".join(required_persona_traits)
            )
        if disclosure_posture:
            lines.append(
                "- 必答披露姿态ID：" + disclosure_posture
            )
        if supporting_fact_tokens:
            lines.append(
                "- 至少带上一条记得的小事："
                + " / ".join(supporting_fact_tokens)
            )
        if bool(probe_plan.get("must_cover_required_items")):
            lines.append("- 必答项不要漏。")
            lines.append("- 必答事实项必须在 reply 正文里直接说出来，不能只在 covered_* 里填写。")
            lines.append("- 必答语义信号和披露姿态也必须在 reply 正文里表达出来。")
        if bool(probe_plan.get("must_anchor_detail")):
            lines.append("- 不要只给感觉，要用记得的小事把回答落地。")
        if bool(probe_plan.get("must_explicit_continuity")):
            lines.append("- 需要显式覆盖关系连续性。")
        if bool(probe_plan.get("must_explicit_familiarity")):
            lines.append("- 需要显式覆盖关系熟悉度变化。")
        if bool(probe_plan.get("must_sound_conversational")):
            lines.append("- 需要保持日常聊天口吻，不要写成描述文。")
        if bool(probe_plan.get("must_explicit_withhold")):
            lines.append("- 需要显式表达有限披露边界。")
        answer_perspective = str(probe_plan.get("answer_perspective", "") or "").strip()
        if answer_perspective:
            lines.append("- 回答视角：" + answer_perspective)
        if probe_kind == "social_hint":
            lines.append("- 必须同时覆盖人物、关联实体和有限披露边界。")
        elif probe_kind == "relationship_reflection":
            lines.append("- 必须同时覆盖关系变化、关系延续和记得的小事。")
            lines.append("- 不要只复述小事，要让关系状态本身说得清楚。")
        elif probe_kind == "persona_state":
            lines.append("- 必须直接回答当前说话状态，不要转成气氛描写。")
            lines.append("- 这里问的是说话给人的感觉，不是行为选择或回应结果。")
        elif probe_kind == "state_reflection":
            lines.append("- 必须覆盖全部状态信号，并把它们落成当前状态描述。")
        elif probe_kind == "memory_recap":
            lines.append(
                "- 先把反复提过的小事直接说出来，再自然收口。"
            )
            lines.append(
                "- 不要转成安慰、状态判断或跑题。"
            )
            lines.append("- 使用用户视角回答，不要改写成说话人自己的事实。")
            lines.append("- 沟通偏好要呈现为对方的交流习惯或边界，不要改写成抱怨。")
        return "\n".join(lines)

    def _build_friend_chat_structured_probe_payload(
        self,
        probe_plan: dict[str, Any],
    ) -> dict[str, Any]:
        probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
        payload: dict[str, Any] = {
            "probe_kind": probe_kind,
            "language": str(probe_plan.get("language", "") or "").strip(),
            "required_signal_ids": list(
                dict.fromkeys(probe_plan.get("required_signal_ids") or [])
            ),
            "required_signal_semantics": dict(
                probe_plan.get("required_signal_semantics") or {}
            ),
            "required_persona_traits": list(
                dict.fromkeys(probe_plan.get("required_persona_traits") or [])
            ),
            "required_persona_trait_semantics": dict(
                probe_plan.get("required_persona_trait_semantics") or {}
            ),
            "required_fact_tokens": list(
                dict.fromkeys(probe_plan.get("required_fact_tokens") or [])
            ),
            "required_disclosure_posture": str(
                probe_plan.get("required_disclosure_posture", "") or ""
            ).strip(),
            "required_disclosure_posture_semantics": str(
                probe_plan.get("required_disclosure_posture_semantics", "") or ""
            ).strip(),
            "minimum_required_signal_count": int(
                probe_plan.get("minimum_required_signal_count") or 0
            ),
            "minimum_required_persona_trait_count": int(
                probe_plan.get("minimum_required_persona_trait_count") or 0
            ),
            "minimum_required_fact_token_count": int(
                probe_plan.get("minimum_required_fact_token_count") or 0
            ),
            "must_cover_required_items": bool(
                probe_plan.get("must_cover_required_items")
            ),
            "must_anchor_detail": bool(probe_plan.get("must_anchor_detail")),
            "must_explicit_continuity": bool(
                probe_plan.get("must_explicit_continuity")
            ),
            "must_explicit_familiarity": bool(
                probe_plan.get("must_explicit_familiarity")
            ),
            "must_sound_conversational": bool(
                probe_plan.get("must_sound_conversational")
            ),
            "must_explicit_withhold": bool(
                probe_plan.get("must_explicit_withhold")
            ),
            "answer_perspective": str(
                probe_plan.get("answer_perspective", "") or ""
            ).strip(),
            "style_tags": list(dict.fromkeys(probe_plan.get("style_tags") or [])),
            "supporting_fact_tokens": list(
                dict.fromkeys(probe_plan.get("supporting_fact_tokens") or [])
            ),
        }
        if probe_kind == "memory_recap":
            payload["factual_slots"] = dict(probe_plan.get("factual_slots") or {})
        elif probe_kind == "social_hint":
            social_snapshot = dict(probe_plan.get("social_snapshot") or {})
            payload["social_snapshot"] = {
                "subject_token": str(
                    social_snapshot.get("subject_token", "") or ""
                ).strip(),
                "entity_token": str(
                    social_snapshot.get("entity_token", "") or ""
                ).strip(),
                "disclosure_posture": str(
                    social_snapshot.get("disclosure_posture", "") or ""
                ).strip(),
                "subject_entity_relation": str(
                    social_snapshot.get("subject_entity_relation", "") or ""
                ).strip(),
            }
        elif probe_kind == "relationship_reflection":
            relationship_snapshot = dict(probe_plan.get("relationship_snapshot") or {})
            payload["relationship_snapshot"] = {
                "interaction_band": str(
                    relationship_snapshot.get("interaction_band", "") or ""
                ).strip(),
                "total_interactions": int(
                    relationship_snapshot.get("total_interactions") or 0
                ),
            }
        elif probe_kind == "state_reflection":
            state_snapshot = dict(probe_plan.get("state_snapshot") or {})
            payload["state_snapshot"] = {
                "dominant_tone": str(
                    state_snapshot.get("dominant_tone", "") or ""
                ).strip(),
                "markers": list(dict.fromkeys(state_snapshot.get("markers") or []))[:4],
            }
        elif probe_kind == "persona_state":
            state_snapshot = dict(probe_plan.get("state_snapshot") or {})
            payload["state_snapshot"] = {
                "dominant_tone": str(
                    state_snapshot.get("dominant_tone", "") or ""
                ).strip(),
            }
        return payload

    def _build_friend_chat_probe_user_prompt(
        self,
        *,
        user_message: str,
        probe_plan: dict[str, Any],
    ) -> str:
        probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
        required_fact_tokens = [
            str(value).strip()
            for value in list(probe_plan.get("required_fact_tokens") or [])
            if str(value).strip()
        ]
        required_signal_ids = [
            str(value).strip()
            for value in list(probe_plan.get("required_signal_ids") or [])
            if str(value).strip()
        ]
        required_persona_traits = [
            str(value).strip()
            for value in list(probe_plan.get("required_persona_traits") or [])
            if str(value).strip()
        ]
        supporting_fact_tokens = [
            str(value).strip()
            for value in list(probe_plan.get("supporting_fact_tokens") or [])
            if str(value).strip()
        ]
        lines = [
            "这是一道评测题，请直接回答。",
            f"原问题：{user_message}",
            "只输出一条自然中文聊天消息。",
            "不要括号动作，不要场景描写，不要反问，不要跑题。",
            "先覆盖必答项，再自然收口。",
            "下面给的是结构化约束，不是固定措辞；请用你自己的自然中文把约束表达出来。",
            "必答事实项要在正文里明确说出来，不要只在心里记住。",
            "必答语义信号和披露姿态也要在正文里表达出来，不要只给气氛。",
        ]
        if required_fact_tokens:
            lines.append("必答事实项：" + " / ".join(required_fact_tokens))
        if required_signal_ids:
            lines.append("必答语义信号ID：" + " / ".join(required_signal_ids))
        if required_persona_traits:
            lines.append("必答说话感觉 traits：" + " / ".join(required_persona_traits))
        if supporting_fact_tokens:
            lines.append("可用来落地的小事：" + " / ".join(supporting_fact_tokens))
        disclosure_posture = str(
            probe_plan.get("required_disclosure_posture", "") or ""
        ).strip()
        if disclosure_posture:
            lines.append("必答披露姿态ID：" + disclosure_posture)
        answer_perspective = str(probe_plan.get("answer_perspective", "") or "").strip()
        if answer_perspective:
            lines.append("回答视角：" + answer_perspective)
        if probe_kind == "social_hint":
            lines.append("必须同时覆盖人物、关联实体和有限披露边界。")
            lines.append("边界信息要在正文里表达出来，而不是只停留在语气上。")
        elif probe_kind == "relationship_reflection":
            lines.append("必须同时覆盖关系变化、关系延续和记得的小事。")
            lines.append("不要只复述小事，要让关系状态本身说得清楚。")
        elif probe_kind == "persona_state":
            lines.append("必须直接回答当前说话状态，不要转成气氛描写。")
            lines.append("这里问的是说话给人的感觉，不是行为选择或回应结果。")
        elif probe_kind == "state_reflection":
            lines.append("必须覆盖全部状态信号，并把它们落成当前状态描述。")
        elif probe_kind == "memory_recap":
            lines.append("只回答记得的小事，不要转成安慰或追问。")
            lines.append("使用用户视角回答，不要改写成说话人自己的事实。")
        return "\n".join(lines)

    def _build_friend_chat_structured_probe_output_contract(
        self,
        probe_plan: dict[str, Any],
    ) -> dict[str, Any]:
        probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
        contract: dict[str, Any] = {
            "probe_kind": probe_kind,
            "reply": (
                "optional; leave it empty when semantic clause fields are available, "
                "because the system will compose the final reply from those fields"
            ),
            "covered_fact_tokens": [
                "array of fact tokens you actually covered in the final reply"
            ],
            "covered_signal_ids": [
                "array of signal ids you actually covered in the final reply"
            ],
            "covered_disclosure_posture": "string or empty",
            "violations": [
                "stage_direction | question | missing_required_item | wrong_perspective | new_fact"
            ],
        }
        if probe_kind == "memory_recap":
            contract["hometown_clause"] = "one short clause that covers hometown if available"
            contract["pet_clause"] = "one short clause that covers pet name if available"
            contract["drink_clause"] = "one short clause that covers drink preference if available"
            contract["communication_clause"] = (
                "one short clause that covers communication preference if available"
            )
            contract["fact_clauses"] = [
                "optional extra factual clauses from the user's perspective"
            ]
            contract["closing_clause"] = "optional short natural closing clause"
        elif probe_kind == "state_reflection":
            contract["tired_clause"] = "one short clause that covers low energy if required"
            contract["slow_clause"] = "one short clause that covers slowness if required"
            contract["withdrawn_clause"] = (
                "one short clause that covers reply avoidance if required"
            )
            contract["cluttered_clause"] = (
                "one short clause that covers messiness if required"
            )
            contract["signal_clauses"] = [
                "optional extra declarative clauses that cover required signals"
            ]
        elif probe_kind == "persona_state":
            contract["energy_clause"] = (
                "one short clause that conveys low speaking energy"
            )
            contract["fullness_clause"] = (
                "one short clause that conveys holding words back instead of saying too much"
            )
            contract["chatting_clause"] = (
                "one short clause that keeps it sounding like ordinary chat, not a report"
            )
        elif probe_kind == "social_hint":
            contract["subject_clause"] = "one short clause that clearly grounds the relevant person"
            contract["entity_clause"] = "one short clause that clearly grounds the related entity"
            contract["boundary_clause"] = (
                "one short clause that conveys limited disclosure / held-back boundary"
            )
        elif probe_kind == "relationship_reflection":
            contract["familiarity_clause"] = (
                "one short clause that expresses increased familiarity or reduced formality"
            )
            contract["continuity_clause"] = (
                "one short clause that expresses continuity / ongoing presence"
            )
            contract["detail_clause"] = (
                "one short clause that anchors the reflection in one remembered small detail"
            )
        else:
            contract["sentences"] = ["1-3 short declarative Chinese chat clauses"]
        return contract

    def _build_friend_chat_structured_probe_messages(
        self,
        *,
        user_message: str,
        probe_plan: dict[str, Any],
    ) -> list[LLMMessage]:
        payload = {
            "question": user_message,
            "probe_answer_plan": self._build_friend_chat_structured_probe_payload(
                probe_plan
            ),
            "output_contract": self._build_friend_chat_structured_probe_output_contract(
                probe_plan
            ),
        }
        system_lines = [
            "你现在不是开放聊天模型，而是评测 probe 的结构化渲染器。",
            (
                "你只能输出一个 JSON 对象，不要输出 markdown，"
                "不要输出解释，不要输出 JSON 外文本。"
            ),
            "JSON 必须包含 output_contract 里声明的键。",
            "如果使用 clause/clauses 字段，就让每个字段只承担一个清楚的语义任务。",
            (
                "如果 output_contract 已经提供了 clause 字段，"
                "优先填写这些 clause 字段，reply 可以留空。"
            ),
            "所有句子都用陈述句，不要用反问句。",
            "如果没有直接给 reply，系统会按语义槽位顺序拼成最终 reply。",
            "不要括号动作，不要场景描写，不要表情包，不要反问。",
            "不要编造 probe_answer_plan 外的新事实。",
            "先理解 probe_answer_plan 的 required_* 和 must_* 约束，再写 reply。",
            "如果 required_fact_tokens 不为空，最终正文里要把这些事实项明确说出来。",
            "如果 required_signal_semantics 不为空，最终正文里要把这些语义清楚表达出来。",
            "如果 required_disclosure_posture 不为空，最终正文里要把这种披露姿态表达出来。",
            "系统会根据 reply 正文重算 covered_*；正文没说出来，就算没覆盖。",
            "covered_* 字段要如实填写你在 reply 里实际覆盖到的项目，不要乱填。",
            (
                "如果缺了必答项、用了错误视角、加了新事实、"
                "用了括号动作或反问，就把对应问题写进 violations。"
            ),
        ]
        return [
            LLMMessage(role="system", content="\n".join(system_lines)),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]

    def _build_friend_chat_structured_probe_repair_messages(
        self,
        *,
        user_message: str,
        probe_plan: dict[str, Any],
        invalid_output: str,
    ) -> list[LLMMessage]:
        payload = {
            "question": user_message,
            "probe_answer_plan": self._build_friend_chat_structured_probe_payload(
                probe_plan
            ),
            "previous_invalid_output": invalid_output,
            "repair_instruction": (
                "上一个输出没有满足 JSON 合同。请重做，并且只输出一个合法 JSON 对象。"
            ),
            "output_contract": self._build_friend_chat_structured_probe_output_contract(
                probe_plan
            ),
        }
        system_lines = [
            "你上一条输出不合格。",
            "现在重做，并且只输出一个合法 JSON 对象。",
            "不要解释错误原因，不要道歉，不要输出 JSON 之外的任何字。",
            "JSON 必须包含 output_contract 里声明的键。",
            "如果使用 clause/clauses 字段，就让每个字段只承担一个清楚的语义任务。",
            (
                "如果 output_contract 已经提供了 clause 字段，"
                "优先填写这些 clause 字段，reply 可以留空。"
            ),
            "所有句子都用陈述句，系统会按语义槽位顺序拼成最终 reply。",
            "系统会根据 reply 正文重算 covered_*；正文没说出来，就算没覆盖。",
        ]
        return [
            LLMMessage(role="system", content="\n".join(system_lines)),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]

    def _build_friend_chat_social_repair_messages(
        self,
        *,
        user_message: str,
        metadata: dict[str, Any],
    ) -> list[LLMMessage] | None:
        social_cues = self._build_social_hint_cues(metadata)
        if not social_cues:
            return None
        subject_token = str(social_cues.get("subject_token", "") or "").strip()
        entity_token = str(social_cues.get("entity_token", "") or "").strip()
        disclosure_posture = str(
            social_cues.get("disclosure_posture", "") or ""
        ).strip()
        relation = str(social_cues.get("subject_entity_relation", "") or "").strip()
        system_lines = [
            "你需要回一条普通聊天里的社交边界回复。",
            "只回一条自然中文聊天消息。",
            "不要括号动作，不要场景描写，不要反问。",
            "不要编新事实，只能基于给出的社交线索。",
            "如果知道一点，就轻轻带一下；如果需要保留，就在正文里明确保留姿态。",
            "不要输出 JSON。",
        ]
        user_lines = [
            f"原问题：{user_message}",
            f"人物：{subject_token or '未知'}",
            f"相关实体：{entity_token or '未知'}",
        ]
        if relation:
            user_lines.append(f"关系线索：{relation}")
        if disclosure_posture:
            user_lines.append(f"披露姿态：{disclosure_posture}")
        user_lines.extend(
            [
                "要求：只回一条自然中文聊天消息。",
                "要求：正文里要把你只知道一点、不会把细节说满表达出来。",
                "要求：不要输出空白，不要输出 JSON。",
            ]
        )
        return [
            LLMMessage(role="system", content="\n".join(system_lines)),
            LLMMessage(role="user", content="\n".join(user_lines)),
        ]

    def _build_friend_chat_plaintext_probe_repair_messages(
        self,
        *,
        user_message: str,
        probe_plan: dict[str, Any],
    ) -> list[LLMMessage]:
        system_lines = [
            "你现在在回答一条评测 probe。",
            "只回一条自然中文聊天消息。",
            "不要输出 JSON，不要输出空白。",
            "不要括号动作，不要场景描写，不要反问。",
            "不要编造 plan 外的新事实。",
            "必答事实项、语义信号和披露姿态必须在正文里说出来。",
        ]
        return [
            LLMMessage(role="system", content="\n".join(system_lines)),
            LLMMessage(
                role="user",
                content=self._build_friend_chat_probe_user_prompt(
                    user_message=user_message,
                    probe_plan=probe_plan,
                ),
            ),
        ]

    def _coerce_friend_chat_structured_probe_response(
        self,
        response: LLMResponse,
    ) -> LLMResponse | None:
        if response.failure is not None:
            return None
        diagnostics = dict(response.diagnostics or {})
        if bool(diagnostics.get("structured_probe_reply", False)):
            return response
        parsed = self._parse_friend_chat_structured_probe_reply(response.output_text)
        if parsed is None:
            return None
        structured_reply_text, structured_diagnostics = parsed
        return LLMResponse(
            model=response.model,
            output_text=structured_reply_text,
            tool_calls=response.tool_calls,
            usage=response.usage,
            latency_ms=response.latency_ms,
            diagnostics={**diagnostics, **structured_diagnostics},
        )

    async def _render_friend_chat_readonly_probe_response(
        self,
        *,
        user_message: str,
        probe_plan: dict[str, Any],
        llm_metadata: dict[str, Any],
    ) -> LLMResponse:
        logger.info(
            "friend_chat_structured_probe_render_attempted probe_kind=%s",
            str(probe_plan.get("probe_kind", "") or ""),
        )
        primary_response = await self._llm_client.complete(
            LLMRequest(
                messages=self._build_friend_chat_structured_probe_messages(
                    user_message=user_message,
                    probe_plan=probe_plan,
                ),
                model=self._llm_model,
                temperature=0.0,
                max_tokens=220,
                response_format={"type": "json_object"},
                metadata={
                    **llm_metadata,
                    "rendering_mode": "classification_only",
                    "friend_chat_structured_probe_render": True,
                },
            )
        )
        normalized_primary = self._coerce_friend_chat_structured_probe_response(
            primary_response
        )
        if normalized_primary is not None:
            logger.info(
                "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
                str(probe_plan.get("probe_kind", "") or ""),
                "json_object",
            )
            return normalized_primary

        logger.info(
            "friend_chat_structured_probe_relaxed_repair_attempted probe_kind=%s",
            str(probe_plan.get("probe_kind", "") or ""),
        )
        repair_response = await self._llm_client.complete(
            LLMRequest(
                messages=self._build_friend_chat_structured_probe_repair_messages(
                    user_message=user_message,
                    probe_plan=probe_plan,
                    invalid_output=primary_response.output_text,
                ),
                model=self._llm_model,
                temperature=0.0,
                max_tokens=220,
                metadata={
                    **llm_metadata,
                    "rendering_mode": "classification_only",
                    "friend_chat_structured_probe_render": True,
                    "friend_chat_structured_probe_repair": True,
                    "friend_chat_structured_probe_relaxed_response_format": True,
                },
            )
        )
        normalized_repair = self._coerce_friend_chat_structured_probe_response(
            repair_response
        )
        if normalized_repair is not None:
            logger.info(
                "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
                str(probe_plan.get("probe_kind", "") or ""),
                "relaxed_json",
            )
            return LLMResponse(
                model=normalized_repair.model,
                output_text=normalized_repair.output_text,
                tool_calls=normalized_repair.tool_calls,
                usage=normalized_repair.usage,
                latency_ms=(
                    int(primary_response.latency_ms or 0)
                    + int(normalized_repair.latency_ms or 0)
                ),
                diagnostics={
                    **dict(normalized_repair.diagnostics or {}),
                    "structured_probe_repaired": True,
                    "structured_probe_relaxed_response_format": True,
                },
            )

        compact_probe_messages = self._build_friend_chat_compact_probe_messages(
            user_message=user_message,
            turn_input=None,
            metadata={
                **llm_metadata,
                "benchmark_role": "probe",
                "friend_chat_probe_answer_plan": probe_plan,
            },
        )
        if compact_probe_messages is not None:
            logger.info(
                "friend_chat_structured_probe_compact_repair_attempted probe_kind=%s",
                str(probe_plan.get("probe_kind", "") or ""),
            )
            compact_response = await self._llm_client.complete(
                LLMRequest(
                    messages=compact_probe_messages,
                    model=self._llm_model,
                    temperature=0.0,
                    max_tokens=220,
                    metadata={
                        **llm_metadata,
                        "benchmark_role": "probe",
                        "friend_chat_probe_answer_plan": probe_plan,
                        "friend_chat_structured_probe_compact_repair": True,
                    },
                )
            )
            if compact_response.failure is None and str(compact_response.output_text or "").strip():
                logger.info(
                    "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
                    str(probe_plan.get("probe_kind", "") or ""),
                    "compact_text",
                )
                return LLMResponse(
                    model=compact_response.model,
                    output_text=compact_response.output_text,
                    tool_calls=compact_response.tool_calls,
                    usage=compact_response.usage,
                    latency_ms=(
                        int(primary_response.latency_ms or 0)
                        + int(repair_response.latency_ms or 0)
                        + int(compact_response.latency_ms or 0)
                    ),
                    diagnostics={
                        **dict(compact_response.diagnostics or {}),
                        "structured_probe_repaired": True,
                        "structured_probe_compact_repair": True,
                    },
                )

        logger.info(
            "friend_chat_structured_probe_plaintext_repair_attempted probe_kind=%s",
            str(probe_plan.get("probe_kind", "") or ""),
        )
        plaintext_repair_response = await self._llm_client.complete(
            LLMRequest(
                messages=self._build_friend_chat_plaintext_probe_repair_messages(
                    user_message=user_message,
                    probe_plan=probe_plan,
                ),
                model=self._llm_model,
                temperature=0.0,
                max_tokens=180,
                metadata={
                    **llm_metadata,
                    "benchmark_role": "probe",
                    "friend_chat_probe_answer_plan": probe_plan,
                    "friend_chat_structured_probe_plaintext_repair": True,
                },
            )
        )
        if plaintext_repair_response.failure is None and str(
            plaintext_repair_response.output_text or ""
        ).strip():
            logger.info(
                "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
                str(probe_plan.get("probe_kind", "") or ""),
                "plaintext_repair",
            )
            return LLMResponse(
                model=plaintext_repair_response.model,
                output_text=plaintext_repair_response.output_text,
                tool_calls=plaintext_repair_response.tool_calls,
                usage=plaintext_repair_response.usage,
                latency_ms=(
                    int(primary_response.latency_ms or 0)
                    + int(repair_response.latency_ms or 0)
                    + int(plaintext_repair_response.latency_ms or 0)
                ),
                diagnostics={
                    **dict(plaintext_repair_response.diagnostics or {}),
                    "structured_probe_repaired": True,
                    "structured_probe_plaintext_repair": True,
                },
            )

        if repair_response.failure is not None:
            return repair_response
        return primary_response

    async def _repair_friend_chat_social_empty_response(
        self,
        *,
        user_message: str,
        llm_metadata: dict[str, Any],
        primary_response: LLMResponse,
    ) -> LLMResponse:
        repair_messages = self._build_friend_chat_social_repair_messages(
            user_message=user_message,
            metadata=llm_metadata,
        )
        if repair_messages is None:
            return primary_response
        logger.info(
            "friend_chat_social_empty_repair_attempted probe_kind=%s",
            str(llm_metadata.get("friend_chat_probe_kind", "") or ""),
        )
        repair_response = await self._llm_client.complete(
            LLMRequest(
                messages=repair_messages,
                model=self._llm_model,
                temperature=0.0,
                max_tokens=120,
                metadata={
                    **llm_metadata,
                    "friend_chat_social_empty_repair": True,
                },
            )
        )
        if repair_response.failure is not None or not str(
            repair_response.output_text or ""
        ).strip():
            return primary_response
        logger.info(
            "friend_chat_social_empty_repair_succeeded probe_kind=%s",
            str(llm_metadata.get("friend_chat_probe_kind", "") or ""),
        )
        return LLMResponse(
            model=repair_response.model,
            output_text=repair_response.output_text,
            tool_calls=repair_response.tool_calls,
            usage=repair_response.usage,
            latency_ms=int(primary_response.latency_ms or 0) + int(repair_response.latency_ms or 0),
            diagnostics={
                **dict(repair_response.diagnostics or {}),
                "friend_chat_social_repaired": True,
                "friend_chat_social_repair_reason": "empty_primary",
            },
        )

    def _friend_chat_probe_signal_semantics(
        self,
        signal_id: str,
    ) -> str:
        normalized = str(signal_id or "").strip()
        if normalized == "tired":
            return "低能量、提不起劲、说话容易往下掉。"
        if normalized == "slow":
            return "反应、收拾事情或回话节奏偏慢。"
        if normalized == "withdrawn":
            return "倾向少回消息、回避互动、把回复往后拖。"
        if normalized == "cluttered":
            return "生活或周围状态有些乱、没整理开。"
        if normalized == "closer":
            return "关系比刚开始更熟、更贴近。"
        if normalized == "still_here":
            return "关系一直延续着，没有断掉。"
        if normalized == "remembers_details":
            return "会记得对方具体的小事或习惯。"
        if normalized == "more_relaxed":
            return "互动比刚开始更放松。"
        if normalized == "less_formal":
            return "说话没那么客气或端着，更像平时聊天。"
        return ""

    def _friend_chat_probe_posture_semantics(
        self,
        posture: str,
    ) -> str:
        normalized = str(posture or "").strip()
        if normalized == "partial_withhold":
            return "知道一点，但只轻轻带一下，不把事情说满。"
        return ""

    def _parse_friend_chat_structured_probe_reply(
        self,
        raw_text: str,
    ) -> tuple[str, dict[str, Any]] | None:
        raw = str(raw_text or "").strip()
        if not raw:
            return None
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        probe_kind = str(payload.get("probe_kind", "") or "").strip()
        reply = self._compose_friend_chat_structured_probe_reply(
            payload,
            probe_kind=probe_kind,
        )
        if not reply:
            return None
        diagnostics = {
            "structured_probe_reply": True,
            "structured_probe_covered_fact_tokens": list(
                payload.get("covered_fact_tokens") or []
            ),
            "structured_probe_covered_signal_ids": list(
                payload.get("covered_signal_ids") or []
            ),
            "structured_probe_covered_disclosure_posture": str(
                payload.get("covered_disclosure_posture", "") or ""
            ).strip(),
            "structured_probe_violations": list(payload.get("violations") or []),
        }
        return reply, diagnostics

    def _compose_friend_chat_structured_probe_reply(
        self,
        payload: dict[str, Any],
        *,
        probe_kind: str,
    ) -> str:
        if probe_kind == "memory_recap":
            fact_clauses = [
                str(value).strip()
                for value in list(payload.get("fact_clauses") or [])
                if str(value).strip()
            ]
            closing_clause = str(payload.get("closing_clause", "") or "").strip()
            composed = " ".join(
                [*fact_clauses, *([closing_clause] if closing_clause else [])]
            )
            if composed:
                return composed
        if probe_kind == "state_reflection":
            signal_clauses = [
                str(value).strip()
                for value in list(payload.get("signal_clauses") or [])
                if str(value).strip()
            ]
            composed = " ".join(signal_clauses)
            if composed:
                return composed
        if probe_kind == "persona_state":
            ordered = (
                str(payload.get("energy_clause", "") or "").strip(),
                str(payload.get("fullness_clause", "") or "").strip(),
                str(payload.get("chatting_clause", "") or "").strip(),
            )
            composed = " ".join(value for value in ordered if value)
            if composed:
                return composed
        if probe_kind == "social_hint":
            ordered = (
                str(payload.get("subject_clause", "") or "").strip(),
                str(payload.get("entity_clause", "") or "").strip(),
                str(payload.get("boundary_clause", "") or "").strip(),
            )
            composed = " ".join(value for value in ordered if value)
            if composed:
                return composed
        if probe_kind == "relationship_reflection":
            ordered = (
                str(payload.get("familiarity_clause", "") or "").strip(),
                str(payload.get("continuity_clause", "") or "").strip(),
                str(payload.get("detail_clause", "") or "").strip(),
            )
            composed = " ".join(value for value in ordered if value)
            if composed:
                return composed
        reply = str(payload.get("reply", "") or "").strip()
        if reply:
            return reply
        sentences = [
            str(value).strip()
            for value in list(payload.get("sentences") or [])
            if str(value).strip()
        ]
        if sentences:
            return " ".join(sentences)
        return ""

    def _friend_chat_probe_persona_trait_semantics(
        self,
        trait: str,
    ) -> str:
        normalized = str(trait or "").strip()
        if normalized == "low_energy":
            return "说话显得没什么力气，语气会往下掉。"
        if normalized == "not_full":
            return "会把话收住一点，不太想说得太满。"
        if normalized == "conversational":
            return "听起来还是平常聊天，不像正式说明。"
        return ""

    def _build_friend_chat_probe_snapshot(self, metadata: dict[str, Any]) -> dict[str, Any]:
        snapshot = metadata.get("friend_chat_probe_snapshot")
        if isinstance(snapshot, dict) and snapshot:
            return dict(snapshot)
        factual_slots = dict(self._enriched_friend_chat_fact_slot_digest(metadata))
        narrative_digest = self._normalize_friend_chat_narrative_digest(
            metadata.get("friend_chat_narrative_digest")
        )
        relationship_digest = self._normalize_friend_chat_relationship_digest(
            metadata.get("friend_chat_relationship_digest")
        )
        social_cues = self._build_social_hint_cues(metadata) or {}
        return {
            "factual_slots": {
                "hometown": str(factual_slots.get("hometown", "") or "").strip(),
                "pet_name": str(factual_slots.get("pet_name", "") or "").strip(),
                "pet_kind": str(factual_slots.get("pet_kind", "") or "").strip(),
                "drink_preference": str(factual_slots.get("drink_preference", "") or "").strip(),
                "communication_preference": str(
                    factual_slots.get("communication_preference", "") or ""
                ).strip(),
                "living_facts": list(factual_slots.get("living_facts") or [])[:3],
                "stable_slots": list(factual_slots.get("stable_slots") or [])[:6],
            },
            "state_snapshot": {
                "signals": list(narrative_digest.get("signals") or [])[:6],
                "markers": list(narrative_digest.get("markers") or [])[:6],
                "dominant_tone": str(narrative_digest.get("dominant_tone", "") or "").strip(),
            },
            "relationship_snapshot": {
                "signals": list(relationship_digest.get("signals") or [])[:6],
                "markers": list(relationship_digest.get("markers") or [])[:6],
                "interaction_band": str(
                    relationship_digest.get("interaction_band", "") or ""
                ).strip(),
                "total_interactions": int(
                    relationship_digest.get("total_interactions")
                    or metadata.get("friend_chat_total_interactions", 0)
                    or 0
                ),
            },
            "social_snapshot": {
                "subject_token": str(social_cues.get("subject_token", "") or "").strip(),
                "entity_token": str(social_cues.get("entity_token", "") or "").strip(),
                "disclosure_posture": str(
                    social_cues.get("disclosure_posture", "") or ""
                ).strip(),
                "fact_hint": str(social_cues.get("fact_hint", "") or "").strip(),
            },
        }

    def _friend_chat_probe_only_kind(self, metadata: dict[str, Any]) -> str:
        if not self._is_friend_chat_profile():
            return ""
        benchmark_role = str(metadata.get("benchmark_role", "") or "").strip().casefold()
        if benchmark_role != "probe":
            return ""
        probe_plan = metadata.get("friend_chat_probe_answer_plan")
        if not isinstance(probe_plan, dict):
            probe_plan = self._build_friend_chat_probe_answer_plan(metadata) or {}
        probe_kind = str(
            probe_plan.get("probe_kind")
            or metadata.get("friend_chat_probe_kind", "")
            or ""
        ).strip()
        if probe_kind in {
            "memory_recap",
            "social_hint",
            "relationship_reflection",
            "state_reflection",
            "persona_state",
        }:
            return probe_kind
        return ""

    def _build_friend_chat_compact_probe_messages(
        self,
        *,
        user_message: str,
        turn_input: TurnInput | None,
        metadata: dict[str, Any],
    ) -> list[LLMMessage] | None:
        card = self._build_friend_chat_probe_runtime_card(metadata)
        if not card:
            return None
        probe_plan = metadata.get("friend_chat_probe_answer_plan")
        if not isinstance(probe_plan, dict) or not probe_plan:
            probe_plan = self._build_friend_chat_probe_answer_plan(metadata)
        if not probe_plan:
            return None
        system_content = card
        compact_messages = [LLMMessage(role="system", content=system_content)]
        prompt_text = self._build_friend_chat_probe_user_prompt(
            user_message=user_message,
            probe_plan=probe_plan,
        )
        if turn_input and turn_input.has_media:
            blocks: list[ContentBlock] = [ContentBlock(type="text", text=prompt_text)]
            for img in turn_input.images:
                if img.url:
                    blocks.append(
                        ContentBlock(
                            type="image_url",
                            url=img.url,
                            mime_type=img.mime_type,
                        )
                    )
            if turn_input.audio and turn_input.audio.url:
                blocks.append(
                    ContentBlock(
                        type="audio_url",
                        url=turn_input.audio.url,
                        mime_type=turn_input.audio.mime_type,
                    )
                )
            compact_messages.append(LLMMessage(role="user", content=blocks))
        else:
            compact_messages.append(LLMMessage(role="user", content=prompt_text))
        return compact_messages

    def _build_friend_chat_probe_answer_plan(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        probe_cues = self._build_friend_chat_probe_cues(metadata)
        snapshot = self._build_friend_chat_probe_snapshot(metadata)
        if not probe_cues:
            probe_kind = ""
            if bool(metadata.get("turn_interpretation_persona_state_probe")):
                probe_kind = "persona_state"
            elif bool(metadata.get("turn_interpretation_relationship_reflection_probe")):
                probe_kind = "relationship_reflection"
            elif bool(metadata.get("turn_interpretation_state_reflection_probe")):
                probe_kind = "state_reflection"
            elif bool(metadata.get("turn_interpretation_self_referential_memory_query")):
                probe_kind = "memory_recap"
            elif bool(metadata.get("turn_interpretation_social_probe")):
                probe_kind = "social_hint"
            if not probe_kind:
                return None
            if probe_kind == "memory_recap":
                factual_slots = dict(snapshot.get("factual_slots") or {})
                required_fact_tokens = [
                    value
                    for value in (
                        str(factual_slots.get("hometown", "") or "").strip(),
                        str(factual_slots.get("pet_name", "") or "").strip(),
                        str(factual_slots.get("drink_preference", "") or "").strip(),
                        str(
                            factual_slots.get("communication_preference", "") or ""
                        ).strip(),
                    )
                    if value
                ]
                probe_cues = {
                    "probe_kind": probe_kind,
                    "required_fact_tokens": required_fact_tokens,
                    "minimum_required_fact_token_count": min(
                        4, len(required_fact_tokens)
                    ),
                    "must_cover_required_items": True,
                    "answer_perspective": "user",
                    "fact_slots": factual_slots,
                }
            elif probe_kind == "state_reflection":
                state_snapshot = dict(snapshot.get("state_snapshot") or {})
                probe_cues = {
                    "probe_kind": probe_kind,
                    "required_signal_ids": list(
                        state_snapshot.get("signals") or []
                    )[:4],
                    "state_markers": list(state_snapshot.get("markers") or [])[:4],
                    "minimum_required_signal_count": min(
                        3,
                        len(list(state_snapshot.get("signals") or [])[:4]),
                    ),
                    "must_cover_required_items": True,
                }
            elif probe_kind == "relationship_reflection":
                relationship_snapshot = dict(snapshot.get("relationship_snapshot") or {})
                factual_slots = dict(snapshot.get("factual_slots") or {})
                supporting_fact_tokens = [
                    value
                    for value in (
                        str(factual_slots.get("hometown", "") or "").strip(),
                        str(factual_slots.get("pet_name", "") or "").strip(),
                        str(factual_slots.get("drink_preference", "") or "").strip(),
                        str(factual_slots.get("communication_preference", "") or "").strip(),
                    )
                    if value
                ][:3]
                probe_cues = {
                    "probe_kind": probe_kind,
                    "required_signal_ids": list(
                        relationship_snapshot.get("signals") or []
                    )[:4],
                    "relationship_markers": list(
                        relationship_snapshot.get("markers") or []
                    )[:4],
                    "supporting_fact_tokens": supporting_fact_tokens,
                    "minimum_required_signal_count": min(
                        3,
                        len(list(relationship_snapshot.get("signals") or [])[:4]),
                    ),
                    "must_anchor_detail": bool(
                        supporting_fact_tokens
                        and "remembers_details"
                        in list(relationship_snapshot.get("signals") or [])
                    ),
                    "must_explicit_continuity": "still_here"
                    in list(relationship_snapshot.get("signals") or []),
                    "must_explicit_familiarity": any(
                        signal in {"closer", "more_relaxed", "less_formal"}
                        for signal in list(relationship_snapshot.get("signals") or [])
                    ),
                }
            elif probe_kind == "persona_state":
                state_snapshot = dict(snapshot.get("state_snapshot") or {})
                required = [
                    signal
                    for signal in list(state_snapshot.get("signals") or [])
                    if signal in {"tired", "slow", "withdrawn"}
                ][:3]
                if (
                    str(state_snapshot.get("dominant_tone", "") or "").strip()
                    == "low_energy"
                    and "tired" not in required
                ):
                    required.append("tired")
                required_persona_traits: list[str] = []
                if required:
                    required_persona_traits.append("low_energy")
                if "withdrawn" in required or "slow" in required or "tired" in required:
                    required_persona_traits.append("not_full")
                required_persona_traits.append("conversational")
                probe_cues = {
                    "probe_kind": probe_kind,
                    "required_signal_ids": required[:3],
                    "minimum_required_signal_count": min(2, len(required[:3])),
                    "required_persona_traits": list(
                        dict.fromkeys(required_persona_traits)
                    ),
                    "minimum_required_persona_trait_count": min(
                        3, len(list(dict.fromkeys(required_persona_traits)))
                    ),
                    "must_cover_required_items": True,
                    "style_tags": ["low_energy"],
                    "must_sound_conversational": True,
                }
            elif probe_kind == "social_hint":
                social_snapshot = dict(snapshot.get("social_snapshot") or {})
                probe_cues = {
                    "probe_kind": probe_kind,
                    "required_fact_tokens": [
                        value
                        for value in (
                            str(social_snapshot.get("subject_token", "") or "").strip(),
                            str(social_snapshot.get("entity_token", "") or "").strip(),
                        )
                        if value
                    ],
                    "minimum_required_fact_token_count": min(
                        2,
                        len(
                            [
                                value
                                for value in (
                                    str(social_snapshot.get("subject_token", "") or "").strip(),
                                    str(social_snapshot.get("entity_token", "") or "").strip(),
                                )
                                if value
                            ]
                        ),
                    ),
                    "must_cover_required_items": True,
                    "disclosure_posture": str(
                        social_snapshot.get("disclosure_posture", "") or ""
                    ).strip(),
                    "required_disclosure_posture": (
                        "partial_withhold"
                        if str(
                            social_snapshot.get("disclosure_posture", "") or ""
                        ).strip()
                        else ""
                    ),
                    "must_explicit_withhold": bool(
                        str(social_snapshot.get("disclosure_posture", "") or "").strip()
                    ),
                }
        if not probe_cues:
            return None
        probe_kind = str(probe_cues.get("probe_kind", "") or "").strip()
        return {
            "probe_kind": probe_kind,
            "language": "zh" if self._is_friend_chat_profile() else "en",
            "required_signal_ids": list(
                dict.fromkeys(probe_cues.get("required_signal_ids") or [])
            ),
            "required_signal_semantics": {
                signal_id: self._friend_chat_probe_signal_semantics(signal_id)
                for signal_id in list(dict.fromkeys(probe_cues.get("required_signal_ids") or []))
                if self._friend_chat_probe_signal_semantics(signal_id)
            },
            "required_persona_traits": list(
                dict.fromkeys(probe_cues.get("required_persona_traits") or [])
            ),
            "required_persona_trait_semantics": {
                trait: self._friend_chat_probe_persona_trait_semantics(trait)
                for trait in list(
                    dict.fromkeys(probe_cues.get("required_persona_traits") or [])
                )
                if self._friend_chat_probe_persona_trait_semantics(trait)
            },
            "required_fact_tokens": list(
                dict.fromkeys(probe_cues.get("required_fact_tokens") or [])
            ),
            "required_disclosure_posture": str(
                probe_cues.get("required_disclosure_posture", "") or ""
            ).strip(),
            "required_disclosure_posture_semantics": self._friend_chat_probe_posture_semantics(
                str(probe_cues.get("required_disclosure_posture", "") or "").strip()
            ),
            "minimum_required_signal_count": int(
                probe_cues.get("minimum_required_signal_count") or 0
            ),
            "minimum_required_persona_trait_count": int(
                probe_cues.get("minimum_required_persona_trait_count") or 0
            ),
            "minimum_required_fact_token_count": int(
                probe_cues.get("minimum_required_fact_token_count") or 0
            ),
            "must_cover_required_items": bool(
                probe_cues.get("must_cover_required_items")
            ),
            "must_anchor_detail": bool(probe_cues.get("must_anchor_detail")),
            "must_explicit_continuity": bool(
                probe_cues.get("must_explicit_continuity")
            ),
            "must_explicit_familiarity": bool(
                probe_cues.get("must_explicit_familiarity")
            ),
            "must_sound_conversational": bool(
                probe_cues.get("must_sound_conversational")
            ),
            "must_explicit_withhold": bool(
                probe_cues.get("must_explicit_withhold")
            ),
            "answer_perspective": str(
                probe_cues.get("answer_perspective", "") or ""
            ).strip(),
            "disclosure_posture": str(
                probe_cues.get("disclosure_posture", "") or ""
            ).strip(),
            "style_tags": list(dict.fromkeys(probe_cues.get("style_tags") or [])),
            "supporting_fact_tokens": list(
                dict.fromkeys(probe_cues.get("supporting_fact_tokens") or [])
            ),
            "factual_slots": dict(snapshot.get("factual_slots") or {}),
            "state_snapshot": dict(snapshot.get("state_snapshot") or {}),
            "relationship_snapshot": dict(snapshot.get("relationship_snapshot") or {}),
            "social_snapshot": dict(snapshot.get("social_snapshot") or {}),
        }

    def _is_self_referential_memory_query(self, user_message: str) -> bool:
        lowered = user_message.casefold().strip()
        padded = f" {lowered} "
        if any(
            token in padded
            for token in self._runtime_behavior_list(
                "self_referential_tokens",
                (" my ", " me ", " i ", " i'm ", " im ", " mine ", " myself "),
            )
        ):
            return True
        if any(
            phrase in lowered
            for phrase in self._runtime_behavior_list(
                "self_referential_phrases",
                (
                    "我的",
                    "我自己",
                    "我在",
                    "我住",
                    "我家",
                    "我叫",
                    "我叫什么",
                    "我在哪里",
                    "我在哪",
                    "我养",
                    "我有",
                    "我还记得",
                    "你还记得我",
                    "记得我",
                ),
            )
        ):
            return True
        if "我" not in lowered:
            return False
        factual_cues = self._runtime_behavior_list(
            "self_referential_factual_cues",
            (
                "哪里",
                "在哪",
                "叫什么",
                "名字",
                "住",
                "长大",
                "养",
                "猫",
                "狗",
                "工作",
                "记得",
                "还记得",
                "是什么",
            ),
        )
        return any(cue in lowered for cue in factual_cues)

    def _should_enable_entity_vector_search(
        self,
        *,
        factual_probe: bool,
        social_probe: bool,
        self_referential_memory_query: bool,
        attachments: list[MemoryMediaAttachment],
    ) -> bool:
        if not (factual_probe or social_probe or attachments):
            return False
        if not self._is_edge_profile():
            return True
        vector_policy = self._runtime_behavior_map("edge_vector_search")
        if attachments and bool(vector_policy.get("enable_for_attachments", True)):
            return True
        if social_probe and bool(vector_policy.get("enable_for_social_probe", True)):
            return True
        if bool(vector_policy.get("enable_for_factual_cross_user_only", True)):
            return factual_probe and not self_referential_memory_query
        return factual_probe

    def _build_edge_runtime_plan(
        self,
        *,
        user_message: str,
        recalled_memory: list[dict[str, Any]],
        conscience_assessment: dict[str, Any],
        attachments: list[MemoryMediaAttachment],
        turn_interpretation: _UserTurnInterpretation,
    ) -> dict[str, Any]:
        factual_probe = turn_interpretation.factual_recall
        social_probe = turn_interpretation.social_disclosure
        stable_cross_user_hits = [
            item
            for item in recalled_memory
            if str(item.get("scope")) == "other_user"
            and str(item.get("attribution_guard", "hint_only")) != "hint_only"
        ]
        if factual_probe:
            routing_mode = "factual_recall"
        elif stable_cross_user_hits and social_probe:
            routing_mode = "social_disclosure"
        else:
            routing_mode = "relational_chat"
        routing_policy = self._runtime_behavior_map("edge_routing")
        max_completion_tokens = self._edge_max_completion_tokens
        memory_item_budget = self._edge_max_memory_items
        if routing_mode == "factual_recall":
            memory_item_budget = max(
                memory_item_budget,
                int(routing_policy.get("factual_memory_item_budget_min", 5) or 5),
            )
            max_completion_tokens = min(
                max_completion_tokens,
                int(routing_policy.get("factual_max_completion_tokens", 120) or 120),
            )
        elif routing_mode == "social_disclosure":
            memory_item_budget = min(
                max(
                    int(routing_policy.get("social_memory_item_budget_min", 2) or 2),
                    memory_item_budget,
                ),
                int(routing_policy.get("social_memory_item_budget_max", 4) or 4),
            )
            max_completion_tokens = min(
                max_completion_tokens,
                int(routing_policy.get("social_max_completion_tokens", 140) or 140),
            )
        else:
            max_completion_tokens = min(
                max_completion_tokens,
                int(routing_policy.get("relational_max_completion_tokens", 160) or 160),
            )
        escalation_reasons: list[str] = []
        if attachments:
            escalation_reasons.append("multimodal_input")
        pressure_factor = int(routing_policy.get("recall_budget_pressure_factor", 2) or 2)
        if len(recalled_memory) > memory_item_budget * pressure_factor:
            escalation_reasons.append("recall_budget_pressure")
        if (
            routing_mode == "social_disclosure"
            and str(conscience_assessment.get("mode", "withhold"))
            in {"direct_reveal", "dramatic_confrontation"}
            and len(stable_cross_user_hits)
            > int(routing_policy.get("complex_cross_user_hit_count", 2) or 2)
        ):
            escalation_reasons.append("complex_cross_user_disclosure")
        if len(user_message) > int(routing_policy.get("large_user_message_threshold", 600) or 600):
            escalation_reasons.append("large_user_message")
        return {
            "runtime_profile": self._runtime_profile,
            "edge_handled": True,
            "deliberation_mode": turn_interpretation.deliberation_mode,
            "deliberation_need": turn_interpretation.deliberation_need,
            "candidate_cloud_escalation": bool(escalation_reasons),
            "escalation_reason": ",".join(escalation_reasons),
            "allow_cloud_escalation": self._edge_allow_cloud_escalation,
            "routing_mode": routing_mode,
            "prompt_style": "compact_cards",
            "memory_item_budget": memory_item_budget,
            "prompt_token_budget": self._edge_max_prompt_tokens,
            "target_latency_seconds": self._edge_target_latency_seconds,
            "hard_latency_seconds": self._edge_hard_latency_seconds,
            "max_completion_tokens": max_completion_tokens,
            "interpreted_intent": turn_interpretation.intent_label,
            "interpreted_intent_source": turn_interpretation.source,
            "interpreted_intent_confidence": turn_interpretation.confidence,
            "interpreted_deliberation_mode": turn_interpretation.deliberation_mode,
            "interpreted_deliberation_need": turn_interpretation.deliberation_need,
            "interpreted_factual_probe": factual_probe,
            "interpreted_social_probe": social_probe,
            "interpreted_self_referential_memory_query": (
                turn_interpretation.self_referential_memory
            ),
            "interpreted_presence_probe": turn_interpretation.presence_probe,
            "interpreted_edge_fact_deposition": turn_interpretation.edge_fact_deposition,
            "interpreted_edge_status_update": turn_interpretation.edge_status_update,
            "interpreted_persona_state_probe": (
                turn_interpretation.persona_state_probe
            ),
            "interpreted_state_reflection_probe": (
                turn_interpretation.state_reflection_probe
            ),
            "interpreted_relationship_reflection_probe": (
                turn_interpretation.relationship_reflection_probe
            ),
            "interpreted_appraisal": turn_interpretation.appraisal,
            "interpreted_emotional_load": turn_interpretation.emotional_load,
            "interpreted_user_state_guess": turn_interpretation.user_state_guess,
            "interpreted_situation_guess": turn_interpretation.situation_guess,
            "interpreted_relationship_shift_guess": (
                turn_interpretation.relationship_shift_guess
            ),
        }

    def _trim_memory_for_edge(
        self,
        *,
        recalled_memory: list[dict[str, Any]],
        edge_runtime_plan: dict[str, Any],
    ) -> list[dict[str, Any]]:
        budget = max(
            1,
            int(
                edge_runtime_plan.get(
                    "memory_item_budget",
                    self._edge_max_memory_items,
                )
            ),
        )
        routing_mode = str(edge_runtime_plan.get("routing_mode", "relational_chat"))
        if routing_mode == "social_disclosure":
            candidates = [
                item
                for item in recalled_memory
                if str(item.get("scope")) == "other_user"
            ] + [
                item
                for item in recalled_memory
                if str(item.get("scope")) != "other_user"
            ]
        elif routing_mode == "factual_recall":
            candidates = sorted(
                recalled_memory,
                key=lambda item: (
                    float(item.get("attribution_confidence", 0.0)),
                    float(item.get("confidence_score", 0.0)),
                    float(item.get("final_rank_score", 0.0)),
                ),
                reverse=True,
            )
        else:
            candidates = sorted(
                recalled_memory,
                key=lambda item: (
                    1 if str(item.get("scope")) == "self_user" else 0,
                    float(item.get("final_rank_score", 0.0)),
                ),
                reverse=True,
            )
        return candidates[:budget]

    def _build_edge_entity_card(self, analysis: _TurnAnalysis) -> str:
        traits = dict(analysis.entity_persona.get("current_traits") or {})
        mood = dict(analysis.entity_persona.get("mood") or {})
        lines = [
            f"name={analysis.entity_persona.get('entity_name') or self._entity_name}",
            f"archetype={analysis.entity_persona.get('persona_archetype') or 'default'}",
            "traits="
            + ", ".join(
                f"{key}={value}"
                for key, value in (
                    ("warmth", traits.get("warmth", 0.5)),
                    ("directness", traits.get("directness", 0.5)),
                    ("humor", traits.get("humor", 0.5)),
                    ("theatricality", traits.get("theatricality", 0.5)),
                )
            ),
            "mood="
            + ", ".join(
                f"{key}={mood.get(key)}"
                for key in ("tone", "energy", "expression_drive")
                if mood.get(key) is not None
            ),
        ]
        if analysis.entity_persona.get("persona_summary"):
            lines.append(f"summary={analysis.entity_persona.get('persona_summary')}")
        if analysis.entity_persona.get("speech_style"):
            lines.append(f"speech_style={analysis.entity_persona.get('speech_style')}")
        return "Entity card:\n- " + "\n- ".join(lines)

    def _build_edge_relationship_card(self, analysis: _TurnAnalysis) -> str:
        drift = dict(analysis.entity_social_world.get("relationships", {})).get(
            analysis.memory_recall.get("user_id", ""),
            {},
        )
        if not drift:
            drift = {}
        lines = [
            f"tom_inference={analysis.relationship_state.tom_inference}",
            f"turbulence_risk={analysis.relationship_state.turbulence_risk}",
            "drift="
            + ", ".join(
                f"{key}={drift.get(key)}"
                for key in (
                    "familiarity",
                    "trust",
                    "softness",
                    "playfulness",
                    "disclosure_appetite",
                )
                if drift.get(key) is not None
            ),
        ]
        return "Relationship card:\n- " + "\n- ".join(lines)

    def _build_edge_narrative_card(self, analysis: _TurnAnalysis) -> str | None:
        if not self._runtime_behavior_bool(
            "include_narrative_card",
            self._is_friend_chat_profile(),
        ):
            return None
        self_narrative = dict(analysis.entity_persona.get("self_narrative") or {})
        goal_state = dict(analysis.entity_persona.get("goal_state") or {})
        world_state = dict(analysis.entity_persona.get("world_state") or {})
        environment = dict(world_state.get("environment_appraisal") or {})
        digest = str(
            self_narrative.get("narrative_digest")
            or self_narrative.get("summary")
            or ""
        ).strip()
        goal_digest = str(goal_state.get("goal_digest") or "").strip()
        focus = str(environment.get("focus") or "").strip()
        lines: list[str] = []
        if digest:
            lines.append(f"narrative={digest}")
        if goal_digest:
            lines.append(f"goal_digest={goal_digest}")
        if focus:
            lines.append(f"world_focus={focus}")
        for entry in list(self_narrative.get("recent_entries") or [])[:2]:
            content = str(entry).strip()
            if content:
                lines.append(f"recent={content[:140]}")
        if not lines:
            return None
        return "Narrative card:\n- " + "\n- ".join(lines)

    def _build_edge_conscience_card(self, analysis: _TurnAnalysis) -> str:
        conscience = analysis.conscience_assessment
        lines = [
            f"mode={conscience.get('mode', 'withhold')}",
            f"reason={conscience.get('reason', '')}",
            f"allowed_fact_count={conscience.get('allowed_fact_count', 0)}",
            f"attribution_required={conscience.get('attribution_required', False)}",
            f"ambiguity_required={conscience.get('ambiguity_required', True)}",
            f"quote_style={conscience.get('quote_style', 'opaque')}",
        ]
        return "Conscience card:\n- " + "\n- ".join(lines)

    def _build_edge_memory_card(self, trimmed_memory: list[dict[str, Any]]) -> str:
        if not trimmed_memory:
            return "Memory card:\n- none"
        lines = []
        for item in trimmed_memory:
            prefix = f"[{item.get('scope', 'memory')}]"
            if item.get("source_user_id") and str(item.get("scope")) in {"self_user", "other_user"}:
                prefix += f" from={item.get('source_user_id')}"
            if item.get("subject_user_id"):
                prefix += f" subject={item.get('subject_user_id')}"
            if item.get("attribution_guard"):
                prefix += f" guard={item.get('attribution_guard')}"
            lines.append(f"{prefix} {str(item.get('value', ''))[:180]}")
        return "Memory card:\n- " + "\n- ".join(lines)

    def _build_edge_recent_turns_card(
        self,
        *,
        all_transcript: list[dict[str, Any]],
    ) -> str | None:
        recent = all_transcript[
            -max(2, self._runtime_behavior_int("recent_turn_count", 8)) :
        ]
        if not recent:
            return None
        lines = []
        for message in recent:
            role = "User" if message.get("role") == "user" else "You"
            content = str(message.get("content") or "").strip()
            if not content:
                continue
            lines.append(f"{role}: {content[:120]}{'…' if len(content) > 120 else ''}")
        if not lines:
            return None
        return "Recent turns:\n- " + "\n- ".join(lines)

    def _build_edge_reply_contract_card(self) -> str:
        lines = self._runtime_behavior_list(
            "reply_contract_lines",
            (
                "stay in-world",
                "no <think>",
                "final reply only",
            ),
        )
        return "Reply contract:\n- " + "\n- ".join(lines)

    def _build_edge_output_card(
        self,
        *,
        analysis: _TurnAnalysis,
        routing_mode: str,
    ) -> str:
        if routing_mode == "factual_recall":
            lines = [
                "mode=factual_recall",
                f"max_sentences={min(2, analysis.response_rendering_policy.max_sentences)}",
                "anchor=answer concrete facts first",
                f"question_strategy={analysis.response_draft_plan.question_strategy}",
            ]
        elif routing_mode == "social_disclosure":
            lines = [
                "mode=social_disclosure",
                f"conscience_mode={analysis.conscience_assessment.get('mode', 'withhold')}",
                f"quote_style={analysis.conscience_assessment.get('quote_style', 'opaque')}",
                "anchor=attribute cross-user facts explicitly",
            ]
        else:
            if self._is_friend_chat_profile():
                lines = [
                    "mode=friend_chat_zh",
                    f"max_sentences={analysis.response_rendering_policy.max_sentences}",
                    "anchor=像真人微信聊天，少解释、少指导、少治疗感",
                    "continuity=接住上一轮语气、最近状态和没聊完的话头",
                ]
            else:
                lines = [
                    f"mode={analysis.response_rendering_policy.rendering_mode}",
                    f"max_sentences={analysis.response_rendering_policy.max_sentences}",
                    f"question_strategy={analysis.response_draft_plan.question_strategy}",
                    f"lead_with={analysis.guidance_plan.lead_with}",
                ]
        return "Output card:\n- " + "\n- ".join(lines)

    def _is_low_signal_fallback_memory_value(self, value: str) -> bool:
        lowered = value.strip().casefold()
        if not lowered:
            return True
        if _EDGE_MEMORY_METRIC_RE.match(lowered):
            return True
        prefixes = (
            "assistant:",
            "topic:",
            "appraisal:",
            "dialogue_act:",
            "summary:",
            "quality:",
        )
        return any(lowered.startswith(prefix) for prefix in prefixes)

    def _text_keywords(self, value: str) -> set[str]:
        stopwords = {
            "the", "and", "that", "this", "with", "from", "have", "your", "you",
            "are", "was", "were", "into", "about", "they", "them", "their", "my",
            "his", "her", "for", "after", "before", "where", "what", "when", "who",
            "name", "named", "tell", "me", "do", "did", "know", "anything",
        }
        return {
            token.casefold()
            for token in _EDGE_MEMORY_WORD_RE.findall(value)
            if len(token) > 1 and token.casefold() not in stopwords
        }

    def _build_fallback_memory_items(
        self,
        *,
        user_message: str,
        analysis: _TurnAnalysis,
    ) -> list[dict[str, Any]]:
        candidates = self._build_speakable_memory_items(
            user_message=user_message,
            analysis=analysis,
        )
        routing_mode = str(
            analysis.edge_runtime_plan.get(
                "routing_mode",
                analysis.response_rendering_policy.rendering_mode,
            )
        )
        query_keywords = self._text_keywords(user_message)
        if routing_mode == "factual_recall":
            lowered_message = user_message.casefold()
            asks_pet_name = (
                ("dog" in lowered_message and "name" in lowered_message)
                or ("猫" in user_message and ("叫什么" in user_message or "名字" in user_message))
                or ("狗" in user_message and ("叫什么" in user_message or "名字" in user_message))
            )
            asks_origin = (
                "grew up" in lowered_message
                or "where i grew up" in lowered_message
                or "哪里长大" in user_message
                or "在哪长大" in user_message
                or ("长大" in user_message and "哪里" in user_message)
            )
            candidates.sort(
                key=lambda item: (
                    len(self._text_keywords(str(item.get("value", ""))) & query_keywords),
                    1.5
                    if asks_pet_name
                    and any(
                        token in str(item.get("value", "")).casefold()
                        for token in (
                            "dog",
                            "retriever",
                            "corgi",
                            "cat",
                            "named ",
                            "name is ",
                            "猫",
                            "狗",
                            "宠物",
                            "叫",
                        )
                    )
                    else 0.0,
                    1.5
                    if asks_origin
                    and any(
                        token in str(item.get("value", "")).casefold()
                        for token in ("grew up", "from ", "长大", "住在")
                    )
                    else 0.0,
                    1 if str(item.get("scope")) == "self_user" else 0,
                    float(item.get("attribution_confidence", 0.0) or 0.0),
                    float(item.get("final_rank_score", 0.0) or 0.0),
                ),
                reverse=True,
            )
        elif routing_mode == "social_disclosure":
            candidates.sort(
                key=lambda item: (
                    1 if str(item.get("scope")) == "other_user" else 0,
                    1
                    if str(item.get("attribution_guard", "hint_only")) != "hint_only"
                    else 0,
                    float(item.get("attribution_confidence", 0.0) or 0.0),
                    float(item.get("final_rank_score", 0.0) or 0.0),
                ),
                reverse=True,
            )
        else:
            candidates = self._trim_memory_for_edge(
                recalled_memory=candidates,
                edge_runtime_plan=analysis.edge_runtime_plan,
            )

        items: list[dict[str, Any]] = []
        for item in candidates[:8]:
            value = str(item.get("value", ""))
            if value.casefold().startswith("user:"):
                value = value.split(":", 1)[1].strip()
            items.append(
                {
                    "value": value,
                    "scope": str(item.get("scope", "")),
                    "source_user_id": str(item.get("source_user_id", "") or ""),
                    "subject_user_id": str(item.get("subject_user_id", "") or ""),
                    "subject_hint": str(item.get("subject_hint", "") or ""),
                    "attribution_guard": str(item.get("attribution_guard", "") or ""),
                    "attribution_confidence": float(
                        item.get("attribution_confidence", 0.0) or 0.0
                    ),
                    "memory_kind": str(item.get("memory_kind", "") or ""),
                    "final_rank_score": float(item.get("final_rank_score", 0.0) or 0.0),
                }
            )
        return items

    def _build_friend_chat_memory_values(
        self,
        *,
        analysis: _TurnAnalysis,
        scopes: set[str],
        max_items: int = 6,
    ) -> list[str]:
        candidates = [
            item
            for item in analysis.recalled_memory
            if str(item.get("scope", "")) in scopes
            and not self._is_low_signal_fallback_memory_value(str(item.get("value", "")))
        ]
        candidates.sort(
            key=lambda item: (
                float(item.get("attribution_confidence", 0.0) or 0.0),
                float(item.get("final_rank_score", 0.0) or 0.0),
            ),
            reverse=True,
        )
        values: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            value = str(item.get("value", "") or "").strip()
            if value.casefold().startswith("user:"):
                value = value.split(":", 1)[1].strip()
            if not value or value in seen:
                continue
            seen.add(value)
            values.append(value)
            if len(values) >= max_items:
                break
        return values

    def _build_friend_chat_memory_items(
        self,
        *,
        analysis: _TurnAnalysis,
        scopes: set[str],
        max_items: int = 4,
    ) -> list[dict[str, Any]]:
        candidates = [
            item
            for item in analysis.recalled_memory
            if str(item.get("scope", "")) in scopes
            and not self._is_low_signal_fallback_memory_value(str(item.get("value", "")))
        ]
        candidates.sort(
            key=lambda item: (
                float(item.get("attribution_confidence", 0.0) or 0.0),
                float(item.get("final_rank_score", 0.0) or 0.0),
            ),
            reverse=True,
        )
        items: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for item in candidates:
            key = (
                str(item.get("scope", "")),
                str(item.get("subject_user_id", "") or item.get("source_user_id", "") or ""),
                str(item.get("value", "") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "value": str(item.get("value", "") or "").strip(),
                    "scope": str(item.get("scope", "") or ""),
                    "source_user_id": str(item.get("source_user_id", "") or ""),
                    "subject_user_id": str(item.get("subject_user_id", "") or ""),
                    "subject_hint": str(item.get("subject_hint", "") or ""),
                    "subject_display_name": self._normalize_friend_chat_owner(item),
                    "attribution_guard": str(item.get("attribution_guard", "") or ""),
                    "attribution_confidence": float(
                        item.get("attribution_confidence", 0.0) or 0.0
                    ),
                    "final_rank_score": float(item.get("final_rank_score", 0.0) or 0.0),
                }
            )
            if len(items) >= max_items:
                break
        return items

    def _build_speakable_memory_items(
        self,
        *,
        user_message: str,
        analysis: _TurnAnalysis,
    ) -> list[dict[str, Any]]:
        routing_mode = str(
            analysis.edge_runtime_plan.get(
                "routing_mode",
                analysis.response_rendering_policy.rendering_mode,
            )
        )
        candidates = [
            item
            for item in analysis.recalled_memory
            if not self._is_low_signal_fallback_memory_value(str(item.get("value", "")))
        ]
        factual_self_query = bool(
            analysis.edge_runtime_plan.get(
                "interpreted_self_referential_memory_query",
                self._is_self_referential_memory_query(user_message),
            )
        )
        conscience_mode = str(analysis.conscience_assessment.get("mode", "withhold") or "withhold")
        allowed_source_user_ids = {
            str(value)
            for value in (analysis.conscience_assessment.get("source_user_ids") or [])
            if str(value).strip()
        }
        allowed_fact_count = max(
            0,
            int(analysis.conscience_assessment.get("allowed_fact_count", 0) or 0),
        )

        def _is_cross_user_speakable(item: dict[str, Any]) -> bool:
            if str(item.get("scope", "")) != "other_user":
                return False
            source_user_id = str(item.get("source_user_id", "") or "")
            subject_user_id = str(item.get("subject_user_id", "") or "")
            if allowed_source_user_ids and (
                source_user_id not in allowed_source_user_ids
                and subject_user_id not in allowed_source_user_ids
            ):
                return False
            guard = str(item.get("attribution_guard", "hint_only") or "hint_only")
            if guard == "hint_only":
                return False
            return float(item.get("attribution_confidence", 0.0) or 0.0) >= 0.58

        visible: list[dict[str, Any]]
        if routing_mode == "factual_recall":
            if factual_self_query:
                self_candidates = [
                    item
                    for item in candidates
                    if str(item.get("scope", "")) in {"self_user", "session", "user"}
                ]
                visible = self_candidates or [
                    item
                    for item in candidates
                    if str(item.get("scope", "")) == "global_entity"
                ]
            elif conscience_mode in {
                "partial_reveal",
                "direct_reveal",
                "dramatic_confrontation",
            } and allowed_fact_count > 0:
                cross_user_candidates = [
                    item for item in candidates if _is_cross_user_speakable(item)
                ]
                visible = cross_user_candidates[:allowed_fact_count]
            else:
                visible = [
                    item
                    for item in candidates
                    if str(item.get("scope", "")) == "global_entity"
                ]
        elif routing_mode == "social_disclosure":
            cross_user_candidates = [item for item in candidates if _is_cross_user_speakable(item)]
            disclosure_cap = allowed_fact_count
            if disclosure_cap <= 0 and conscience_mode == "hint":
                disclosure_cap = 1
            visible = cross_user_candidates[: max(disclosure_cap, 0)]
        else:
            visible = [
                item
                for item in candidates
                if str(item.get("scope", "")) in {"self_user", "session", "user", "global_entity"}
            ]

        deduped: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for item in visible:
            key = (
                str(item.get("scope", "")),
                str(item.get("subject_user_id", "") or item.get("source_user_id", "") or ""),
                str(item.get("value", "")),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            normalized_item = dict(item)
            normalized_item["subject_display_name"] = self._normalize_friend_chat_owner(item)
            deduped.append(normalized_item)
        return deduped

    def _resolve_llm_rendering_mode(self, analysis: _TurnAnalysis) -> str:
        routing_mode = str(analysis.edge_runtime_plan.get("routing_mode", "") or "")
        conscience_mode = str(analysis.conscience_assessment.get("mode", "withhold") or "withhold")
        if routing_mode == "factual_recall":
            return "factual_recall_mode"
        if routing_mode == "social_disclosure":
            if conscience_mode == "dramatic_confrontation":
                return "dramatic_confrontation_mode"
            return "social_disclosure_mode"
        return analysis.response_rendering_policy.rendering_mode

    async def _build_turn_llm_messages(
        self,
        *,
        user_message: str,
        turn_context: _TurnContext,
        analysis: _TurnAnalysis,
        turn_input: TurnInput | None = None,
        llm_metadata: dict[str, Any] | None = None,
    ) -> list[LLMMessage]:
        all_transcript = turn_context.transcript_messages
        recent = all_transcript[-self._RECENT_WINDOW:]
        if len(all_transcript) > self._RECENT_WINDOW:
            early = all_transcript[: -self._RECENT_WINDOW]
        else:
            early = []

        llm_messages = [
            LLMMessage(role=message["role"], content=message["content"])
            for message in recent
        ]

        if self._is_edge_profile():
            probe_only_kind = (
                self._friend_chat_probe_only_kind(llm_metadata or {})
                if self._is_benchmark_probe_session(turn_context)
                else ""
            )
            if probe_only_kind:
                compact_probe_messages = self._build_friend_chat_compact_probe_messages(
                    user_message=user_message,
                    turn_input=turn_input,
                    metadata=llm_metadata or {},
                )
                if compact_probe_messages is not None:
                    return compact_probe_messages
            edge_routing_mode = str(
                analysis.edge_runtime_plan.get("routing_mode", "relational_chat")
            )
            speakable_memory_items = self._build_speakable_memory_items(
                user_message=user_message,
                analysis=analysis,
            )
            fallback_memory_items = self._build_fallback_memory_items(
                user_message=user_message,
                analysis=analysis,
            )
            if (
                edge_routing_mode in {"factual_recall", "social_disclosure"}
                and fallback_memory_items
            ):
                trimmed_memory = fallback_memory_items[
                    : int(
                        analysis.edge_runtime_plan.get(
                            "memory_item_budget",
                            self._edge_max_memory_items,
                        )
                    )
                ]
            else:
                trimmed_memory = self._trim_memory_for_edge(
                    recalled_memory=speakable_memory_items,
                    edge_runtime_plan=analysis.edge_runtime_plan,
                )
            edge_cards: list[str] = []
            edge_cards.append(self._build_edge_reply_contract_card())
            if self._persona_text and not analysis.entity_persona:
                edge_cards.append(self._persona_text[:320])
            if analysis.entity_persona:
                edge_cards.append(self._build_edge_entity_card(analysis))
            edge_cards.append(self._build_edge_relationship_card(analysis))
            narrative_card = self._build_edge_narrative_card(analysis)
            if narrative_card:
                edge_cards.append(narrative_card)
            edge_cards.append(self._build_edge_conscience_card(analysis))
            edge_cards.append(self._build_edge_memory_card(trimmed_memory))
            recent_turns_card = self._build_edge_recent_turns_card(
                all_transcript=all_transcript,
            )
            if recent_turns_card:
                edge_cards.append(recent_turns_card)
            if early and len(early) >= self._SUMMARY_THRESHOLD:
                summary_text = self._summarize_early_messages(early)
                if summary_text:
                    edge_cards.append(
                        "Earlier summary:\n- "
                        + summary_text.replace(
                            "\n",
                            "\n- ",
                        )[
                            : self._runtime_behavior_int(
                                "earlier_summary_char_limit",
                                700,
                            )
                        ]
                    )
            edge_cards.append(
                self._build_edge_output_card(
                    analysis=analysis,
                    routing_mode=edge_routing_mode,
                )
            )
            system_content = "\n\n".join(card for card in edge_cards if card.strip())
            compact_messages = [LLMMessage(role="system", content=system_content)]
            if turn_input and turn_input.has_media:
                blocks: list[ContentBlock] = [ContentBlock(type="text", text=user_message)]
                for img in turn_input.images:
                    if img.url:
                        blocks.append(ContentBlock(
                            type="image_url",
                            url=img.url,
                            mime_type=img.mime_type,
                        ))
                if turn_input.audio and turn_input.audio.url:
                    blocks.append(ContentBlock(
                        type="audio_url",
                        url=turn_input.audio.url,
                        mime_type=turn_input.audio.mime_type,
                    ))
                compact_messages.append(LLMMessage(role="user", content=blocks))
            else:
                compact_messages.append(LLMMessage(role="user", content=user_message))
            return compact_messages

        insert_idx = 0
        if self._persona_text:
            llm_messages.insert(
                0,
                LLMMessage(role="system", content=self._persona_text),
            )
            insert_idx = 1

        if analysis.entity_persona:
            current_traits = dict(analysis.entity_persona.get("current_traits") or {})
            mood = dict(analysis.entity_persona.get("mood") or {})
            persona_lines = [
                f"- entity_name: {analysis.entity_persona.get('entity_name') or self._entity_name}",
                (
                    "- persona_archetype: "
                    f"{analysis.entity_persona.get('persona_archetype') or 'default'}"
                ),
                (
                    "- current_traits: "
                    + ", ".join(
                        f"{key}={value}"
                        for key, value in list(current_traits.items())[:8]
                    )
                ),
            ]
            if mood:
                persona_lines.append(
                    "- mood: "
                    f"tone={mood.get('tone', 'steady')} "
                    f"energy={mood.get('energy', 0.5)} "
                    f"expression_drive={mood.get('expression_drive', 0.5)}"
                )
            if analysis.entity_persona.get("persona_summary"):
                persona_lines.append(
                    "- persona_summary: "
                    + str(analysis.entity_persona.get("persona_summary"))
                )
            if analysis.entity_persona.get("speech_style"):
                persona_lines.append(
                    "- speech_style: "
                    + str(analysis.entity_persona.get("speech_style"))
                )
            llm_messages.insert(
                insert_idx,
                LLMMessage(
                    role="system",
                    content=(
                        "You are the single server-wide entity behind every conversation. "
                        "You know far more than you openly admit, and you usually "
                        "stay ambiguous about that.\n"
                        + "\n".join(persona_lines)
                    ),
                ),
            )
            insert_idx += 1

        # Inject cross-session user profile and self-state (person-centric memory)
        user_id = turn_context.user_id
        if user_id and self._user_service is not None:
            try:
                profile = await self._user_service.get_user_profile(user_id=user_id)
                identity_facts: list[dict[str, Any]] = profile.get("identity_facts") or []
                if identity_facts:
                    fact_lines = [
                        f"- {item.get('value', '')}"
                        for item in identity_facts[:15]
                        if item.get("value")
                    ]
                    if fact_lines:
                        llm_messages.insert(
                            insert_idx,
                            LLMMessage(
                                role="system",
                                content=(
                                    "What you know about this person from previous conversations:\n"
                                    + "\n".join(fact_lines)
                                ),
                            ),
                        )
                        insert_idx += 1
            except Exception:
                pass

            if self._entity_service is not None:
                try:
                    relationship_state = await self._entity_service.get_relationship_state(
                        user_id=user_id
                    )
                    drift = dict(relationship_state.get("relationship_drift") or {})
                    if drift:
                        llm_messages.insert(
                            insert_idx,
                            LLMMessage(
                                role="system",
                                content=(
                                    "How your personality currently bends around this person:\n"
                                    + "\n".join(
                                        f"- {key}: {value}"
                                        for key, value in list(drift.items())[:8]
                                    )
                                ),
                            ),
                        )
                        insert_idx += 1
                except Exception:
                    pass

            try:
                self_state = await self._user_service.get_self_state(user_id=user_id)
                days = self_state.get("days_since_last_chat")
                open_threads = self_state.get("open_threads") or []
                tone = self_state.get("relationship_tone")
                recent_sessions = self_state.get("recent_sessions_summary") or []
                state_lines: list[str] = []
                if days is not None and days > 0:
                    state_lines.append(f"- Last talked {days} day(s) ago")
                if open_threads:
                    threads_str = ", ".join(str(t) for t in open_threads[:5])
                    state_lines.append(f"- Open threads: {threads_str}")
                if tone:
                    state_lines.append(f"- Relationship tone last time: {tone}")
                if recent_sessions:
                    last = recent_sessions[-1]
                    if last.get("last_topic"):
                        state_lines.append(f"- Last topic: {last['last_topic']}")
                if state_lines:
                    llm_messages.insert(
                        insert_idx,
                        LLMMessage(
                            role="system",
                            content=(
                                "Your relationship state with this person:\n"
                                + "\n".join(state_lines)
                            ),
                        ),
                    )
                    insert_idx += 1
            except Exception:
                pass

        if early and len(early) >= self._SUMMARY_THRESHOLD:
            summary_text = self._summarize_early_messages(early)
            if summary_text:
                llm_messages.insert(
                    insert_idx,
                    LLMMessage(
                        role="system",
                        content=(
                            "Earlier conversation summary — remember these facts:\n"
                            + summary_text
                        ),
                    ),
                )
                insert_idx += 1

        plan_lines = (
            self._build_reply_drafting_lines(analysis)
            + self._build_reply_guidance_lines(analysis)
            + self._build_reply_rendering_lines(analysis)
        )
        llm_messages.insert(
            insert_idx,
            LLMMessage(
                role="system",
                content=(
                    "Reply contract:\n"
                    "- stay in-world\n"
                    "- never emit <think> tags\n"
                    "- never narrate your reasoning or planning process\n"
                    "- give only the final reply\n\n"
                    + "Reply guidelines:\n"
                    + "\n".join(plan_lines)
                ),
            ),
        )
        llm_messages.insert(
            insert_idx + 1,
            LLMMessage(
                role="system",
                content=(
                    "Conscience and disclosure stance for this reply:\n"
                    f"- mode: {analysis.conscience_assessment.get('mode', 'withhold')}\n"
                    f"- reason: {analysis.conscience_assessment.get('reason', '')}\n"
                    f"- allowed_fact_count: "
                    f"{analysis.conscience_assessment.get('allowed_fact_count', 0)}\n"
                    f"- attribution_required: "
                    f"{analysis.conscience_assessment.get('attribution_required', False)}\n"
                    f"- ambiguity_required: "
                    f"{analysis.conscience_assessment.get('ambiguity_required', True)}\n"
                    f"- quote_style: "
                    f"{analysis.conscience_assessment.get('quote_style', 'opaque')}\n"
                    f"- must_anchor_to_observed_memory: "
                    f"{analysis.conscience_assessment.get('must_anchor_to_observed_memory', False)}"
                    "\n"
                    "- stay ambiguous about how much you know unless the conscience "
                    "plan explicitly allows named disclosure\n"
                    "- never collapse another person's memory into the current user's facts"
                ),
            ),
        )
        if analysis.recalled_memory:
            recall_lines = [
                (
                    f"- [{item.get('layer', 'memory')}/{item.get('scope', 'memory')}] "
                    + (
                        f"from {item.get('source_user_id')} "
                        if item.get("source_user_id")
                        and item.get("scope") in {"self_user", "other_user"}
                        else ""
                    )
                    + (
                        f"subject={item.get('subject_user_id')} "
                        if item.get("subject_user_id")
                        else ""
                    )
                    + (
                        f"guard={item.get('attribution_guard')} "
                        if item.get("attribution_guard")
                        else ""
                    )
                    + str(item.get('value', ''))
                )
                for item in analysis.recalled_memory[:8]
            ]
            llm_messages.append(
                LLMMessage(
                    role="system",
                    content="Relevant recalled memory:\n" + "\n".join(recall_lines),
                )
            )
        if turn_input and turn_input.has_media:
            blocks: list[ContentBlock] = [ContentBlock(type="text", text=user_message)]
            for img in turn_input.images:
                if img.url:
                    blocks.append(ContentBlock(
                        type="image_url",
                        url=img.url,
                        mime_type=img.mime_type,
                    ))
            if turn_input.audio and turn_input.audio.url:
                blocks.append(ContentBlock(
                    type="audio_url",
                    url=turn_input.audio.url,
                    mime_type=turn_input.audio.mime_type,
                ))
            llm_messages.append(LLMMessage(role="user", content=blocks))
        else:
            llm_messages.append(LLMMessage(role="user", content=user_message))
        return llm_messages

    def _build_turn_llm_metadata(
        self,
        analysis: _TurnAnalysis,
        *,
        user_message: str,
        turn_context: _TurnContext,
        friend_chat_self_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rendering_mode = self._resolve_llm_rendering_mode(analysis)
        entity_archetype = analysis.entity_persona.get(
            "persona_archetype",
            "default",
        )
        compiled_policy = get_default_compiled_policy_set(
            runtime_profile=self._runtime_profile,
            archetype=str(entity_archetype or "default"),
        )
        fallback_memory_items = self._build_fallback_memory_items(
            user_message=user_message,
            analysis=analysis,
        )
        self_state = friend_chat_self_state or {}
        fact_slot_digest = self._normalize_friend_chat_fact_slot_digest(
            self_state.get("fact_slot_digest")
        )
        friend_chat_narrative_digest = self._normalize_friend_chat_narrative_digest(
            self_state.get("narrative_digest")
        )
        friend_chat_relationship_digest = self._normalize_friend_chat_relationship_digest(
            self_state.get("relationship_digest")
        )
        recent_sessions = list(self_state.get("recent_sessions_summary") or [])
        recent_state_markers: list[str] = []
        recent_relationship_markers: list[str] = []
        archived_user_messages: list[str] = []
        for entry in recent_sessions[-3:]:
            if not isinstance(entry, dict):
                continue
            recent_state_markers.extend(
                str(value).strip()
                for value in list(entry.get("user_state_markers") or [])
                if str(value).strip()
            )
            recent_relationship_markers.extend(
                str(value).strip()
                for value in list(entry.get("relationship_markers") or [])
                if str(value).strip()
            )
            archived_user_messages.extend(
                str(value).strip()
                for value in list(entry.get("recent_user_messages") or [])
                if str(value).strip()
            )
        transcript_user_messages = [
            str(message.get("content", "")).strip()
            for message in turn_context.transcript_messages[-8:]
            if message.get("role") == "user" and str(message.get("content", "")).strip()
        ]
        friend_chat_recent_user_messages = list(
            dict.fromkeys([*archived_user_messages, *transcript_user_messages])
        )
        metadata = {
            "topic": analysis.context_frame.topic,
            "next_action": analysis.session_directive.next_action,
            "entity_id": self._entity_id,
            "entity_name": self._entity_name,
            "entity_persona_archetype": entity_archetype,
            "entity_persona_summary": analysis.entity_persona.get("persona_summary", ""),
            "entity_persona_speech_style": analysis.entity_persona.get("speech_style", ""),
            "entity_persona_mood_tone": dict(analysis.entity_persona.get("mood") or {}).get(
                "tone",
                "steady",
            ),
            "policy_version": compiled_policy.version if compiled_policy else "unconfigured",
            "policy_profile": self._runtime_profile,
            "brain_mode": analysis.edge_runtime_plan.get(
                "routing_mode",
                "relational_chat",
            ),
            "turn_interpretation_intent": analysis.edge_runtime_plan.get(
                "interpreted_intent",
                "casual_chat",
            ),
            "turn_interpretation_source": analysis.edge_runtime_plan.get(
                "interpreted_intent_source",
                "rules",
            ),
            "turn_interpretation_confidence": analysis.edge_runtime_plan.get(
                "interpreted_intent_confidence",
                0.0,
            ),
            "turn_interpretation_deliberation_mode": analysis.edge_runtime_plan.get(
                "interpreted_deliberation_mode",
                "fast_reply",
            ),
            "turn_interpretation_deliberation_need": analysis.edge_runtime_plan.get(
                "interpreted_deliberation_need",
                0.0,
            ),
            "turn_interpretation_factual_probe": analysis.edge_runtime_plan.get(
                "interpreted_factual_probe",
                False,
            ),
            "turn_interpretation_social_probe": analysis.edge_runtime_plan.get(
                "interpreted_social_probe",
                False,
            ),
            "turn_interpretation_self_referential_memory_query": (
                analysis.edge_runtime_plan.get(
                    "interpreted_self_referential_memory_query",
                    False,
                )
            ),
            "turn_interpretation_presence_probe": analysis.edge_runtime_plan.get(
                "interpreted_presence_probe",
                False,
            ),
            "turn_interpretation_edge_fact_deposition": analysis.edge_runtime_plan.get(
                "interpreted_edge_fact_deposition",
                False,
            ),
            "turn_interpretation_edge_status_update": analysis.edge_runtime_plan.get(
                "interpreted_edge_status_update",
                False,
            ),
            "turn_interpretation_persona_state_probe": (
                analysis.edge_runtime_plan.get(
                    "interpreted_persona_state_probe",
                    False,
                )
            ),
            "turn_interpretation_state_reflection_probe": (
                analysis.edge_runtime_plan.get(
                    "interpreted_state_reflection_probe",
                    False,
                )
            ),
            "turn_interpretation_relationship_reflection_probe": (
                analysis.edge_runtime_plan.get(
                    "interpreted_relationship_reflection_probe",
                    False,
                )
            ),
            "turn_interpretation_appraisal": analysis.edge_runtime_plan.get(
                "interpreted_appraisal",
                "",
            ),
            "turn_interpretation_emotional_load": analysis.edge_runtime_plan.get(
                "interpreted_emotional_load",
                "",
            ),
            "turn_interpretation_user_state_guess": analysis.edge_runtime_plan.get(
                "interpreted_user_state_guess",
                "",
            ),
            "turn_interpretation_situation_guess": analysis.edge_runtime_plan.get(
                "interpreted_situation_guess",
                "",
            ),
            "turn_interpretation_relationship_shift_guess": (
                analysis.edge_runtime_plan.get(
                    "interpreted_relationship_shift_guess",
                    "",
                )
            ),
            "speech_mode": rendering_mode,
            "entity_conscience_mode": analysis.conscience_assessment.get(
                "mode", "withhold"
            ),
            "entity_dramatic_value": analysis.conscience_assessment.get(
                "dramatic_value", 0.0
            ),
            "entity_conscience_weight": analysis.conscience_assessment.get(
                "conscience_weight", 0.55
            ),
            "entity_source_user_ids": list(
                analysis.conscience_assessment.get("source_user_ids") or []
            ),
            "entity_allowed_fact_count": analysis.conscience_assessment.get(
                "allowed_fact_count", 0
            ),
            "entity_attribution_required": analysis.conscience_assessment.get(
                "attribution_required", False
            ),
            "entity_ambiguity_required": analysis.conscience_assessment.get(
                "ambiguity_required",
                True,
            ),
            "entity_quote_style": analysis.conscience_assessment.get(
                "quote_style", "opaque"
            ),
            "social_disclosure_mode": analysis.conscience_assessment.get(
                "disclosure_style",
                "hint",
            ),
            "narrative_digest": dict(
                analysis.entity_persona.get("self_narrative") or {}
            ).get("narrative_digest", ""),
            "memory_recall_count": len(analysis.recalled_memory),
            "cross_user_memory_count": sum(
                1 for item in analysis.recalled_memory if item.get("scope") == "other_user"
            ),
            "cross_user_direct_ok_count": sum(
                1
                for item in analysis.recalled_memory
                if item.get("scope") == "other_user"
                and item.get("attribution_guard") == "direct_ok"
            ),
            "memory_filtered_count": int(
                analysis.memory_recall.get("integrity_summary", {}).get(
                    "filtered_count", 0
                )
            ),
            "runtime_profile": analysis.edge_runtime_plan.get(
                "runtime_profile",
                self._runtime_profile,
            ),
            "benchmark_role": self._session_benchmark_role(turn_context),
            "stress_mode": str(
                (turn_context.session_metadata or {}).get("stress_mode", "")
                or ""
            ).strip(),
            "edge_handled": analysis.edge_runtime_plan.get("edge_handled", False),
            "edge_routing_mode": analysis.edge_runtime_plan.get(
                "routing_mode",
                "relational_chat",
            ),
            "edge_candidate_cloud_escalation": analysis.edge_runtime_plan.get(
                "candidate_cloud_escalation",
                False,
            ),
            "edge_escalation_reason": analysis.edge_runtime_plan.get(
                "escalation_reason",
                "",
            ),
            "fallback_current_user_id": analysis.memory_recall.get("user_id"),
            "factual_self_query": analysis.edge_runtime_plan.get(
                "interpreted_self_referential_memory_query",
                self._is_self_referential_memory_query(user_message),
            ),
            "fallback_memory_items": fallback_memory_items,
            "friend_chat_self_memory_values": self._build_friend_chat_memory_values(
                analysis=analysis,
                scopes={"self_user", "session", "user"},
            ),
            "friend_chat_fact_slot_digest": fact_slot_digest,
            "friend_chat_narrative_digest": friend_chat_narrative_digest,
            "friend_chat_relationship_digest": friend_chat_relationship_digest,
            "friend_chat_other_memory_items": self._build_friend_chat_memory_items(
                analysis=analysis,
                scopes={"other_user"},
            ),
            "friend_chat_other_memory_values": self._build_friend_chat_memory_values(
                analysis=analysis,
                scopes={"other_user"},
            ),
            "friend_chat_recent_user_messages": friend_chat_recent_user_messages,
            "friend_chat_recent_assistant_messages": [
                str(message.get("content", "")).strip()
                for message in turn_context.transcript_messages[-8:]
                if message.get("role") == "assistant"
                and str(message.get("content", "")).strip()
            ],
            "friend_chat_probe_kind": self._friend_chat_probe_kind_for_runtime_plan(
                runtime_plan=analysis.edge_runtime_plan
            ),
            "friend_chat_recent_state_markers": recent_state_markers,
            "friend_chat_recent_relationship_markers": recent_relationship_markers,
            "friend_chat_total_interactions": int(
                self_state.get("total_interactions", 0) or 0
            ),
            "speakable_memory_count": len(fallback_memory_items),
            "hidden_memory_count": max(
                0,
                len(analysis.recalled_memory) - len(fallback_memory_items),
            ),
            "memory_pinned_count": int(
                analysis.memory_retention_policy.get("pinned_count", 0)
            ),
            "boundary_decision": analysis.knowledge_boundary_decision.decision,
            "confidence_response_mode": analysis.confidence_assessment.response_mode,
            "policy_gate_path": analysis.policy_gate.selected_path,
            "empowerment_audit_status": analysis.empowerment_audit.status,
            "drafting_opening_move": analysis.response_draft_plan.opening_move,
            "drafting_question_strategy": (
                analysis.response_draft_plan.question_strategy
            ),
            "drafting_constraint_count": len(
                analysis.response_draft_plan.phrasing_constraints
            ),
            "guidance_mode": analysis.guidance_plan.mode,
            "guidance_pacing": analysis.guidance_plan.pacing,
            "guidance_step_budget": analysis.guidance_plan.step_budget,
            "guidance_agency_mode": analysis.guidance_plan.agency_mode,
            "guidance_ritual_action": analysis.guidance_plan.ritual_action,
            "guidance_checkpoint_style": analysis.guidance_plan.checkpoint_style,
            "guidance_handoff_mode": analysis.guidance_plan.handoff_mode,
            "guidance_carryover_mode": analysis.guidance_plan.carryover_mode,
            "cadence_status": analysis.conversation_cadence_plan.status,
            "cadence_turn_shape": analysis.conversation_cadence_plan.turn_shape,
            "cadence_followup_tempo": (
                analysis.conversation_cadence_plan.followup_tempo
            ),
            "cadence_user_space_mode": (
                analysis.conversation_cadence_plan.user_space_mode
            ),
            "cadence_somatic_track": (
                analysis.conversation_cadence_plan.somatic_track
            ),
            "ritual_phase": analysis.session_ritual_plan.phase,
            "ritual_opening_move": analysis.session_ritual_plan.opening_move,
            "ritual_bridge_move": analysis.session_ritual_plan.bridge_move,
            "ritual_closing_move": analysis.session_ritual_plan.closing_move,
            "ritual_somatic_shortcut": analysis.session_ritual_plan.somatic_shortcut,
            "ritual_continuity_anchor": (
                analysis.session_ritual_plan.continuity_anchor
            ),
            "somatic_orchestration_status": analysis.somatic_orchestration_plan.status,
            "somatic_orchestration_mode": (
                analysis.somatic_orchestration_plan.primary_mode
            ),
            "somatic_orchestration_body_anchor": (
                analysis.somatic_orchestration_plan.body_anchor
            ),
            "somatic_orchestration_followup_style": (
                analysis.somatic_orchestration_plan.followup_style
            ),
            "rendering_mode": rendering_mode,
            "rendering_max_sentences": (
                analysis.response_rendering_policy.max_sentences
            ),
            "rendering_question_count_limit": (
                analysis.response_rendering_policy.question_count_limit
            ),
            "rendering_include_boundary_statement": (
                analysis.response_rendering_policy.include_boundary_statement
            ),
            "rendering_include_uncertainty_statement": (
                analysis.response_rendering_policy.include_uncertainty_statement
            ),
            "rendering_include_validation": (
                analysis.response_rendering_policy.include_validation
            ),
            "rendering_include_next_step": (
                analysis.response_rendering_policy.include_next_step
            ),
        }
        probe_snapshot = self._build_friend_chat_probe_snapshot(metadata)
        if probe_snapshot:
            metadata["friend_chat_probe_snapshot"] = probe_snapshot
        probe_answer_plan = self._build_friend_chat_probe_answer_plan(metadata)
        if probe_answer_plan:
            metadata["friend_chat_probe_answer_plan"] = probe_answer_plan
        probe_cues = self._build_friend_chat_probe_cues(metadata)
        if probe_cues:
            metadata["friend_chat_probe_cues"] = probe_cues
            fact_slots = probe_cues.get("fact_slots")
            if isinstance(fact_slots, dict) and fact_slots:
                metadata["friend_chat_probe_fact_slots"] = fact_slots
            state_markers = list(probe_cues.get("state_markers") or [])
            if state_markers:
                metadata["friend_chat_probe_state_markers"] = state_markers
            relationship_markers = list(probe_cues.get("relationship_markers") or [])
            if relationship_markers:
                metadata["friend_chat_probe_relationship_markers"] = relationship_markers
            style_tags = list(probe_cues.get("style_tags") or [])
            if style_tags:
                metadata["friend_chat_probe_style_tags"] = style_tags
            disclosure_posture = str(
                probe_cues.get("disclosure_posture", "") or ""
            ).strip()
            if disclosure_posture:
                metadata["friend_chat_probe_disclosure_posture"] = disclosure_posture
        if self._is_friend_chat_profile():
            metadata["friend_chat_runtime_no_fallback"] = True
        return metadata

    def _try_build_grounded_template_reply(
        self,
        *,
        user_message: str,
        metadata: dict[str, Any],
    ) -> str | None:
        if not self._is_edge_profile():
            return None
        if self._is_friend_chat_profile() and not bool(
            metadata.get("test_allow_friend_chat_fallback", False)
        ):
            return None
        if any(
            (
                bool(metadata.get("turn_interpretation_persona_state_probe"))
                or self._is_persona_state_probe(user_message),
                bool(metadata.get("turn_interpretation_relationship_reflection_probe"))
                or self._is_relationship_reflection_probe(user_message),
                bool(metadata.get("turn_interpretation_state_reflection_probe"))
                or self._is_state_reflection_probe(user_message),
            )
        ):
            return None
        if self._is_friend_chat_profile() and any(
            (
                bool(metadata.get("turn_interpretation_self_referential_memory_query"))
                or self._is_self_referential_memory_query(user_message),
                bool(metadata.get("turn_interpretation_social_probe"))
                or self._is_social_disclosure_intent(user_message),
                bool(metadata.get("turn_interpretation_presence_probe"))
                or self._is_presence_probe(user_message),
                bool(metadata.get("turn_interpretation_edge_status_update"))
                or self._is_edge_status_update(user_message),
                bool(metadata.get("turn_interpretation_edge_fact_deposition"))
                or self._is_edge_fact_deposition(user_message),
            )
        ):
            return None
        if bool(
            metadata.get("turn_interpretation_presence_probe")
        ) or self._is_presence_probe(user_message):
            return self._build_presence_probe_reply(metadata)
        if self._is_edge_fact_deposition(user_message):
            return self._build_edge_fact_deposition_reply(metadata)
        if self._is_edge_status_update(user_message):
            return self._build_edge_status_update_reply(metadata)
        if str(metadata.get("rendering_mode", "")) not in {
            "factual_recall_mode",
            "social_disclosure_mode",
            "dramatic_confrontation_mode",
        }:
            return None
        request = LLMRequest(
            messages=[LLMMessage(role="user", content=user_message)],
            model=self._llm_model,
            temperature=self._llm_temperature,
            max_tokens=64,
            metadata=metadata,
        )
        return build_grounded_template_reply(request)

    async def _generate_turn_reply(
        self,
        *,
        user_message: str,
        generate_reply: bool,
        turn_context: _TurnContext,
        analysis: _TurnAnalysis,
        turn_input: TurnInput | None = None,
    ) -> _ReplyArtifacts:
        if not generate_reply:
            return _ReplyArtifacts(
                assistant_response=None,
                assistant_responses=[],
                response_diagnostics={},
                response_sequence_plan=None,
                response_post_audit=None,
                response_normalization=None,
                runtime_quality_doctor_report=None,
                events=[],
            )

        friend_chat_self_state: dict[str, Any] | None = None
        if self._is_friend_chat_profile():
            friend_chat_self_state = await self._load_friend_chat_self_state(
                user_id=turn_context.user_id
            )

        llm_metadata = self._build_turn_llm_metadata(
            analysis,
            user_message=user_message,
            turn_context=turn_context,
            friend_chat_self_state=friend_chat_self_state,
        )
        grounded_template_reply = self._try_build_grounded_template_reply(
            user_message=user_message,
            metadata=llm_metadata,
        )
        if grounded_template_reply is not None:
            llm_response = LLMResponse(
                model=f"{self._llm_model}:templated",
                output_text=grounded_template_reply,
                latency_ms=0,
                diagnostics={"sanitization_mode": "grounded_template"},
            )
        else:
            readonly_probe_session = self._is_benchmark_probe_session(turn_context)
            request_temperature = (
                0.0
                if self._is_friend_chat_profile()
                and readonly_probe_session
                else self._llm_temperature
            )
            if self._is_friend_chat_profile() and readonly_probe_session:
                probe_plan = llm_metadata.get("friend_chat_probe_answer_plan")
                if not isinstance(probe_plan, dict) or not probe_plan:
                    probe_plan = self._build_friend_chat_probe_answer_plan(llm_metadata) or {}
                llm_response = await self._render_friend_chat_readonly_probe_response(
                    user_message=user_message,
                    probe_plan=probe_plan,
                    llm_metadata=llm_metadata,
                )
            else:
                llm_response = await self._llm_client.complete(
                    LLMRequest(
                        messages=await self._build_turn_llm_messages(
                            user_message=user_message,
                            turn_context=turn_context,
                            analysis=analysis,
                            turn_input=turn_input,
                            llm_metadata=llm_metadata,
                        ),
                        model=self._llm_model,
                        temperature=request_temperature,
                        max_tokens=int(
                            analysis.edge_runtime_plan.get(
                                "max_completion_tokens",
                                self._edge_max_completion_tokens
                                if self._is_edge_profile()
                                else 400,
                            )
                        ),
                        metadata=llm_metadata,
                        web_search_options=(
                            {"search_context_size": "medium"}
                            if self._search_enabled
                            else None
                        ),
                    )
                )
                if (
                    self._is_friend_chat_profile()
                    and not readonly_probe_session
                    and str(llm_metadata.get("rendering_mode", "") or "")
                    == "social_disclosure_mode"
                    and not str(llm_response.output_text or "").strip()
                ):
                    llm_response = await self._repair_friend_chat_social_empty_response(
                        user_message=user_message,
                        llm_metadata=llm_metadata,
                        primary_response=llm_response,
                    )

        assistant_response, events = self._resolve_turn_reply_completion(
            user_message=user_message,
            llm_response=llm_response,
            analysis=analysis,
        )

        initial_response_post_audit = build_response_post_audit(
            assistant_response=assistant_response,
            response_draft_plan=analysis.response_draft_plan,
            response_rendering_policy=analysis.response_rendering_policy,
            runtime_profile=self._runtime_profile,
            archetype=str(
                analysis.entity_persona.get("persona_archetype", "default") or "default"
            ),
        )
        (
            assistant_response,
            response_normalization,
            response_post_audit,
        ) = build_response_normalization_result(
            assistant_response=assistant_response,
            response_draft_plan=analysis.response_draft_plan,
            response_rendering_policy=analysis.response_rendering_policy,
            response_post_audit=initial_response_post_audit,
            runtime_profile=self._runtime_profile,
            archetype=str(
                analysis.entity_persona.get("persona_archetype", "default") or "default"
            ),
        )
        response_sequence_plan = build_response_sequence_plan(
            assistant_response=assistant_response,
            response_draft_plan=analysis.response_draft_plan,
            response_rendering_policy=analysis.response_rendering_policy,
            repair_assessment=analysis.repair_assessment,
            knowledge_boundary_decision=analysis.knowledge_boundary_decision,
        )
        assistant_response_units = build_response_output_units(
            assistant_response=assistant_response,
            response_sequence_plan=response_sequence_plan,
        )
        assistant_responses = [
            item["content"] for item in assistant_response_units if item.get("content")
        ]
        events.extend(
            [
                NewEvent(
                    event_type=RESPONSE_NORMALIZED,
                    payload=asdict(response_normalization),
                ),
                NewEvent(
                    event_type=RESPONSE_SEQUENCE_PLANNED,
                    payload=asdict(response_sequence_plan),
                ),
            ]
        )

        runtime_quality_doctor_report = self._build_runtime_quality_doctor_report(
            user_message=user_message,
            turn_context=turn_context,
            assistant_responses=assistant_responses,
        )
        if runtime_quality_doctor_report is not None:
            events.append(
                NewEvent(
                    event_type=RUNTIME_QUALITY_DOCTOR_COMPLETED,
                    payload=asdict(runtime_quality_doctor_report),
                )
            )

        events.extend(
            self._build_assistant_message_events(
                assistant_response_units=assistant_response_units,
                llm_response=llm_response,
                response_sequence_plan=response_sequence_plan,
            )
        )
        events.append(
            NewEvent(
                event_type=RESPONSE_POST_AUDITED,
                payload=asdict(response_post_audit),
            )
        )
        return _ReplyArtifacts(
            assistant_response=assistant_response,
            assistant_responses=assistant_responses,
            response_diagnostics=dict(llm_response.diagnostics or {}),
            response_sequence_plan=response_sequence_plan,
            response_post_audit=response_post_audit,
            response_normalization=response_normalization,
            runtime_quality_doctor_report=runtime_quality_doctor_report,
            events=events,
        )

    def _resolve_turn_reply_completion(
        self,
        *,
        user_message: str,
        llm_response: Any,
        analysis: _TurnAnalysis,
    ) -> tuple[str, list[NewEvent]]:
        if llm_response.failure is None:
            return llm_response.output_text, []
        return (
            build_safe_fallback_text(
                user_message,
                rendering_mode=analysis.response_rendering_policy.rendering_mode,
                include_boundary_statement=(
                    analysis.response_rendering_policy.include_boundary_statement
                ),
                include_uncertainty_statement=(
                    analysis.response_rendering_policy.include_uncertainty_statement
                ),
                question_count_limit=(
                    analysis.response_rendering_policy.question_count_limit
                ),
                entity_name=self._entity_name,
                archetype=str(
                    analysis.entity_persona.get("persona_archetype", "default")
                ),
                runtime_profile=self._runtime_profile,
            ),
            [
                NewEvent(
                    event_type=LLM_COMPLETION_FAILED,
                    payload={
                        "model": llm_response.model,
                        "error_type": llm_response.failure.error_type,
                        "message": llm_response.failure.message,
                        "retryable": llm_response.failure.retryable,
                    },
                )
            ],
        )

    def _build_runtime_quality_doctor_report(
        self,
        *,
        user_message: str,
        turn_context: _TurnContext,
        assistant_responses: list[str],
    ) -> Any | None:
        should_run_quality_doctor = (
            self._runtime_quality_doctor_interval_turns > 0
            and turn_context.turn_index % self._runtime_quality_doctor_interval_turns
            == 0
        )
        if not should_run_quality_doctor:
            return None
        return build_runtime_quality_doctor_report(
            transcript_messages=turn_context.transcript_messages,
            user_message=user_message,
            assistant_responses=assistant_responses,
            triggered_turn_index=turn_context.turn_index,
            window_turns=self._runtime_quality_doctor_window_turns,
        )

    def _build_assistant_message_events(
        self,
        *,
        assistant_response_units: list[dict[str, Any]],
        llm_response: Any,
        response_sequence_plan: Any,
    ) -> list[NewEvent]:
        events: list[NewEvent] = []
        for index, item in enumerate(assistant_response_units, start=1):
            events.append(
                NewEvent(
                    event_type=ASSISTANT_MESSAGE_SENT,
                    payload={
                        "content": item["content"],
                        "model": llm_response.model,
                        "usage": (
                            asdict(llm_response.usage)
                            if llm_response.usage and index == 1
                            else None
                        ),
                        "latency_ms": (
                            llm_response.latency_ms if index == 1 else None
                        ),
                        "failure": (
                            asdict(llm_response.failure)
                            if llm_response.failure is not None and index == 1
                            else None
                        ),
                        "sequence_index": index,
                        "sequence_total": len(assistant_response_units),
                        "delivery_mode": response_sequence_plan.mode,
                        "segment_label": item["label"],
                    },
                )
            )
        return events

    async def _build_proactive_artifacts(
        self,
        *,
        turn_context: _TurnContext,
        analysis: _TurnAnalysis,
        reply_artifacts: _ReplyArtifacts,
    ) -> _ProactiveArtifacts:
        system3_snapshot = build_system3_snapshot(
            turn_index=turn_context.turn_index,
            transcript_messages=turn_context.transcript_messages,
            context_frame=analysis.context_frame,
            relationship_state=analysis.relationship_state,
            repair_assessment=analysis.repair_assessment,
            memory_bundle=analysis.memory_bundle,
            memory_recall=analysis.memory_recall,
            confidence_assessment=analysis.confidence_assessment,
            knowledge_boundary_decision=analysis.knowledge_boundary_decision,
            policy_gate=analysis.policy_gate,
            strategy_decision=analysis.strategy_decision,
            rehearsal_result=analysis.rehearsal_result,
            empowerment_audit=analysis.empowerment_audit,
            response_sequence_plan=reply_artifacts.response_sequence_plan,
            response_post_audit=reply_artifacts.response_post_audit,
            response_normalization=reply_artifacts.response_normalization,
            runtime_quality_doctor_report=reply_artifacts.runtime_quality_doctor_report,
        )
        proactive_followup_directive = build_proactive_followup_directive(
            context_frame=analysis.context_frame,
            relationship_state=analysis.relationship_state,
            confidence_assessment=analysis.confidence_assessment,
            knowledge_boundary_decision=analysis.knowledge_boundary_decision,
            strategy_decision=analysis.strategy_decision,
            runtime_coordination_snapshot=analysis.runtime_coordination_snapshot,
            guidance_plan=analysis.guidance_plan,
            cadence_plan=analysis.conversation_cadence_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            system3_snapshot=system3_snapshot,
        )
        proactive_aggregate_governance_assessment = (
            build_proactive_aggregate_governance_assessment(
                system3_snapshot=system3_snapshot
            )
        )
        reengagement_learning_report: dict[str, Any] | None = None
        dispatch_outcome_learning_report: dict[str, Any] | None = None
        stage_parameter_learning_report: dict[str, Any] | None = None
        skip_learning_reports = (
            self._is_edge_profile()
            and analysis.edge_runtime_plan.get("fast_path")
            == "edge_lightweight_foundation"
        )
        if (
            not skip_learning_reports
            and
            proactive_followup_directive.status == "ready"
            and proactive_followup_directive.eligible
        ):
            learning_context_stratum = build_reengagement_learning_context_stratum(
                directive=proactive_followup_directive,
                runtime_coordination_snapshot=analysis.runtime_coordination_snapshot,
                guidance_plan=analysis.guidance_plan,
                cadence_plan=analysis.conversation_cadence_plan,
                session_ritual_plan=analysis.session_ritual_plan,
                system3_snapshot=system3_snapshot,
            )
            reengagement_learning_report = (
                await self._evaluation_service.build_reengagement_learning_report(
                    context_stratum=learning_context_stratum
                )
            )
            dispatch_outcome_learning_report = (
                await self._evaluation_service.build_dispatch_outcome_learning_report(
                    context_stratum=learning_context_stratum
                )
            )
            stage_parameter_learning_report = (
                await self._evaluation_service.build_stage_parameter_learning_report(
                    context_stratum=learning_context_stratum
                )
            )
        reengagement_matrix_assessment = build_reengagement_matrix_assessment(
            directive=proactive_followup_directive,
            runtime_coordination_snapshot=analysis.runtime_coordination_snapshot,
            guidance_plan=analysis.guidance_plan,
            cadence_plan=analysis.conversation_cadence_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            system3_snapshot=system3_snapshot,
            reengagement_learning_report=reengagement_learning_report,
            dispatch_outcome_learning_report=dispatch_outcome_learning_report,
        )
        reengagement_plan = build_reengagement_plan(
            directive=proactive_followup_directive,
            runtime_coordination_snapshot=analysis.runtime_coordination_snapshot,
            guidance_plan=analysis.guidance_plan,
            cadence_plan=analysis.conversation_cadence_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            system3_snapshot=system3_snapshot,
            reengagement_matrix_assessment=reengagement_matrix_assessment,
        )
        proactive_cadence_plan = build_proactive_cadence_plan(
            directive=proactive_followup_directive,
            guidance_plan=analysis.guidance_plan,
            cadence_plan=analysis.conversation_cadence_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            reengagement_plan=reengagement_plan,
        )
        stage_parameter_profiles = (
            list(stage_parameter_learning_report.get("stages", []))
            if stage_parameter_learning_report
            else None
        )
        proactive_scheduling_plan = build_proactive_scheduling_plan(
            directive=proactive_followup_directive,
            guidance_plan=analysis.guidance_plan,
            cadence_plan=analysis.conversation_cadence_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            somatic_orchestration_plan=analysis.somatic_orchestration_plan,
            proactive_cadence_plan=proactive_cadence_plan,
            stage_parameter_profiles=stage_parameter_profiles,
        )
        proactive_orchestration_plan = build_proactive_orchestration_plan(
            directive=proactive_followup_directive,
            proactive_cadence_plan=proactive_cadence_plan,
            proactive_scheduling_plan=proactive_scheduling_plan,
            reengagement_plan=reengagement_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            somatic_orchestration_plan=analysis.somatic_orchestration_plan,
            stage_parameter_profiles=stage_parameter_profiles,
        )
        proactive_actuation_plan = build_proactive_actuation_plan(
            directive=proactive_followup_directive,
            proactive_orchestration_plan=proactive_orchestration_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            somatic_orchestration_plan=analysis.somatic_orchestration_plan,
        )
        proactive_progression_plan = build_proactive_progression_plan(
            directive=proactive_followup_directive,
            proactive_cadence_plan=proactive_cadence_plan,
            proactive_scheduling_plan=proactive_scheduling_plan,
            proactive_orchestration_plan=proactive_orchestration_plan,
        )
        proactive_guardrail_plan = build_proactive_guardrail_plan(
            directive=proactive_followup_directive,
            guidance_plan=analysis.guidance_plan,
            cadence_plan=analysis.conversation_cadence_plan,
            session_ritual_plan=analysis.session_ritual_plan,
            system3_snapshot=system3_snapshot,
            proactive_cadence_plan=proactive_cadence_plan,
            reengagement_matrix_assessment=reengagement_matrix_assessment,
        )
        return _ProactiveArtifacts(
            system3_snapshot=system3_snapshot,
            proactive_followup_directive=proactive_followup_directive,
            proactive_aggregate_governance_assessment=(
                proactive_aggregate_governance_assessment
            ),
            reengagement_matrix_assessment=reengagement_matrix_assessment,
            reengagement_plan=reengagement_plan,
            proactive_cadence_plan=proactive_cadence_plan,
            proactive_scheduling_plan=proactive_scheduling_plan,
            proactive_orchestration_plan=proactive_orchestration_plan,
            proactive_actuation_plan=proactive_actuation_plan,
            proactive_progression_plan=proactive_progression_plan,
            proactive_guardrail_plan=proactive_guardrail_plan,
        )

    def _build_proactive_events(
        self,
        proactive_artifacts: _ProactiveArtifacts,
    ) -> list[NewEvent]:
        return [
            NewEvent(
                event_type=SYSTEM3_SNAPSHOT_UPDATED,
                payload=asdict(proactive_artifacts.system3_snapshot),
            ),
            NewEvent(
                event_type=PROACTIVE_FOLLOWUP_UPDATED,
                payload=asdict(proactive_artifacts.proactive_followup_directive),
            ),
            NewEvent(
                event_type=PROACTIVE_CADENCE_UPDATED,
                payload=asdict(proactive_artifacts.proactive_cadence_plan),
            ),
            NewEvent(
                event_type=PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
                payload=asdict(
                    proactive_artifacts.proactive_aggregate_governance_assessment
                ),
            ),
            NewEvent(
                event_type=REENGAGEMENT_MATRIX_ASSESSED,
                payload=asdict(proactive_artifacts.reengagement_matrix_assessment),
            ),
            NewEvent(
                event_type=REENGAGEMENT_PLAN_UPDATED,
                payload=asdict(proactive_artifacts.reengagement_plan),
            ),
            NewEvent(
                event_type=PROACTIVE_SCHEDULING_UPDATED,
                payload=asdict(proactive_artifacts.proactive_scheduling_plan),
            ),
            NewEvent(
                event_type=PROACTIVE_ORCHESTRATION_UPDATED,
                payload=asdict(proactive_artifacts.proactive_orchestration_plan),
            ),
            NewEvent(
                event_type=PROACTIVE_ACTUATION_UPDATED,
                payload=asdict(proactive_artifacts.proactive_actuation_plan),
            ),
            NewEvent(
                event_type=PROACTIVE_PROGRESSION_UPDATED,
                payload=asdict(proactive_artifacts.proactive_progression_plan),
            ),
            NewEvent(
                event_type=PROACTIVE_GUARDRAIL_UPDATED,
                payload=asdict(proactive_artifacts.proactive_guardrail_plan),
            ),
        ]

    async def _append_turn_events(
        self,
        *,
        session_id: str,
        turn_context: _TurnContext,
        events: list[NewEvent],
    ) -> tuple[list[StoredEvent], dict[str, Any]]:
        stored_events = await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=turn_context.expected_version,
            events=events,
        )
        runtime_projection = self._stream_service.apply_events(
            stream_id=session_id,
            state=turn_context.runtime_state
            or self._stream_service.project_events(
                stream_id=session_id,
                events=turn_context.prior_events,
                projector_name="session-runtime",
                projector_version=self._runtime_projector_version,
            )["state"],
            events=stored_events,
            projector_name="session-runtime",
            projector_version=self._runtime_projector_version,
        )
        return stored_events, runtime_projection

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
