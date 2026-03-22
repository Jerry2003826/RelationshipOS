from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from relationship_os.application.analyzers import (
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
from relationship_os.application.llm import build_safe_fallback_text
from relationship_os.application.memory_service import MemoryService
from relationship_os.application.proactive_dispatch_handler import ProactiveDispatchHandler
from relationship_os.application.stream_service import StreamService
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
    SESSION_DIRECTIVE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SESSION_STARTED,
    SOMATIC_ORCHESTRATION_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import NewEvent, StoredEvent, utc_now
from relationship_os.domain.llm import LLMClient, LLMMessage, LLMRequest


class SessionAlreadyExistsError(RuntimeError):
    """Raised when a session is created twice with the same identifier."""


@dataclass(slots=True, frozen=True)
class RuntimeTurnResult:
    session_id: str
    stored_events: list[StoredEvent]
    runtime_projection: dict[str, Any]
    assistant_response: str | None
    assistant_responses: list[str]


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
    ) -> None:
        self._stream_service = stream_service
        self._memory_service = memory_service
        self._evaluation_service = evaluation_service
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._llm_temperature = llm_temperature
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
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_session_id = session_id or f"session-{uuid4().hex[:12]}"
        existing_events = await self._stream_service.read_stream(stream_id=resolved_session_id)
        if existing_events:
            raise SessionAlreadyExistsError(f"Session {resolved_session_id} already exists")

        stored_events = await self._stream_service.append_events(
            stream_id=resolved_session_id,
            expected_version=0,
            events=[
                NewEvent(
                    event_type=SESSION_STARTED,
                    payload={
                        "session_id": resolved_session_id,
                        "created_at": utc_now().isoformat(),
                        "metadata": metadata or {},
                    },
                )
            ],
        )
        runtime_projection = await self._stream_service.project_stream(
            stream_id=resolved_session_id,
            projector_name="session-runtime",
            projector_version="v1",
        )
        return {
            "session_id": resolved_session_id,
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
        user_message: str,
        generate_reply: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeTurnResult:
        prior_events = await self._stream_service.read_stream(stream_id=session_id)
        expected_version = len(prior_events)
        runtime_state: dict[str, Any] | None = None

        if prior_events:
            current_projection = await self._stream_service.project_stream(
                stream_id=session_id,
                projector_name="session-runtime",
                projector_version="v1",
            )
            runtime_state = current_projection["state"]
        strategy_history = []
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
        context_frame = build_context_frame(user_message)
        memory_recall = await self._memory_service.recall_session_memory(
            session_id=session_id,
            query=user_message,
            limit=3,
            context_filters={
                "topic": context_frame.topic,
                "appraisal": context_frame.appraisal,
                "dialogue_act": context_frame.dialogue_act,
            },
        )
        recalled_memory = list(memory_recall.get("results", []))
        previous_relationship = None
        if runtime_state and isinstance(runtime_state.get("relationship_state"), dict):
            previous_relationship = runtime_state["relationship_state"]
        relationship_state = build_relationship_state(
            context_frame=context_frame,
            previous_state=previous_relationship,
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
        raw_memory_bundle = build_memory_bundle(
            transcript_messages=transcript_messages,
            user_message=user_message,
            context_frame=context_frame,
            relationship_state=relationship_state,
        )
        repair_plan = build_repair_plan(repair_assessment=repair_assessment)
        memory_write_preparation = await self._memory_service.prepare_memory_write(
            session_id=session_id,
            memory_bundle=raw_memory_bundle,
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_plan=repair_plan,
        )
        memory_bundle = memory_write_preparation["memory_bundle"]
        memory_write_guard = memory_write_preparation["write_guard"]
        memory_retention_policy = memory_write_preparation["retention_policy"]
        memory_forgetting = memory_write_preparation["forgetting"]
        knowledge_boundary_decision = build_knowledge_boundary_decision(
            context_frame=context_frame,
            relationship_state=relationship_state,
            confidence_assessment=confidence_assessment,
            user_message=user_message,
            recalled_memory=recalled_memory,
        )
        private_judgment = build_private_judgment(
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            repair_plan=repair_plan,
            knowledge_boundary_decision=knowledge_boundary_decision,
            memory_bundle=memory_bundle,
            confidence_assessment=confidence_assessment,
            recalled_memory=recalled_memory,
        )
        policy_gate = build_policy_gate(
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            confidence_assessment=confidence_assessment,
            private_judgment=private_judgment,
        )
        strategy_decision = build_strategy_decision(
            policy_gate=policy_gate,
            private_judgment=private_judgment,
            context_frame=context_frame,
            repair_assessment=repair_assessment,
            confidence_assessment=confidence_assessment,
            relationship_state=relationship_state,
            strategy_history=strategy_history,
        )
        rehearsal_result = build_rehearsal_result(
            strategy_decision=strategy_decision,
            policy_gate=policy_gate,
            repair_assessment=repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
        )
        expression_plan = build_expression_plan(
            strategy_decision,
            repair_plan,
            rehearsal_result,
        )
        runtime_coordination_snapshot = build_runtime_coordination_snapshot(
            turn_index=turn_index,
            session_age_seconds=session_age_seconds,
            idle_gap_seconds=idle_gap_seconds,
            user_message=user_message,
            context_frame=context_frame,
            relationship_state=relationship_state,
            confidence_assessment=confidence_assessment,
            repair_assessment=repair_assessment,
            strategy_decision=strategy_decision,
        )
        guidance_plan = build_guidance_plan(
            context_frame=context_frame,
            repair_assessment=repair_assessment,
            confidence_assessment=confidence_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            policy_gate=policy_gate,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
        )
        conversation_cadence_plan = build_conversation_cadence_plan(
            context_frame=context_frame,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            repair_assessment=repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            policy_gate=policy_gate,
        )
        session_ritual_plan = build_session_ritual_plan(
            context_frame=context_frame,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            repair_assessment=repair_assessment,
        )
        somatic_orchestration_plan = build_somatic_orchestration_plan(
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
        )
        empowerment_audit = build_empowerment_audit(
            policy_gate=policy_gate,
            relationship_state=relationship_state,
            knowledge_boundary_decision=knowledge_boundary_decision,
            confidence_assessment=confidence_assessment,
            expression_plan=expression_plan,
            rehearsal_result=rehearsal_result,
        )
        response_draft_plan = build_response_draft_plan(
            context_frame=context_frame,
            policy_gate=policy_gate,
            repair_plan=repair_plan,
            confidence_assessment=confidence_assessment,
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
            context_frame=context_frame,
            confidence_assessment=confidence_assessment,
            repair_assessment=repair_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            response_draft_plan=response_draft_plan,
            empowerment_audit=empowerment_audit,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
        )
        session_directive = build_session_directive(
            context_frame=context_frame,
            policy_gate=policy_gate,
            strategy_decision=strategy_decision,
            rehearsal_result=rehearsal_result,
            empowerment_audit=empowerment_audit,
            response_draft_plan=response_draft_plan,
            response_rendering_policy=response_rendering_policy,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            somatic_orchestration_plan=somatic_orchestration_plan,
            repair_assessment=repair_assessment,
            repair_plan=repair_plan,
            knowledge_boundary_decision=knowledge_boundary_decision,
            memory_bundle=memory_bundle,
            recalled_memory=recalled_memory,
        )
        inner_monologue = build_inner_monologue(
            context_frame=context_frame,
            memory_bundle=memory_bundle,
            recalled_memory=recalled_memory,
            policy_gate=policy_gate,
            rehearsal_result=rehearsal_result,
            empowerment_audit=empowerment_audit,
            response_draft_plan=response_draft_plan,
            response_rendering_policy=response_rendering_policy,
            repair_assessment=repair_assessment,
            repair_plan=repair_plan,
            knowledge_boundary_decision=knowledge_boundary_decision,
            private_judgment=private_judgment,
            relationship_state=relationship_state,
            strategy_decision=strategy_decision,
            confidence_assessment=confidence_assessment,
        )

        events: list[NewEvent] = []
        if not prior_events:
            events.append(
                NewEvent(
                    event_type=SESSION_STARTED,
                    payload={
                        "session_id": session_id,
                        "created_at": utc_now().isoformat(),
                        "metadata": metadata or {},
                    },
                )
            )

        events.extend(
            [
                NewEvent(
                    event_type=USER_MESSAGE_RECEIVED,
                    payload={"content": user_message},
                    metadata=metadata or {},
                ),
                NewEvent(
                    event_type=CONTEXT_FRAME_COMPUTED,
                    payload=asdict(context_frame),
                ),
                NewEvent(
                    event_type=RELATIONSHIP_STATE_UPDATED,
                    payload=asdict(relationship_state),
                ),
                NewEvent(
                    event_type=CONFIDENCE_ASSESSMENT_COMPUTED,
                    payload=asdict(confidence_assessment),
                ),
                NewEvent(
                    event_type=REPAIR_ASSESSMENT_COMPUTED,
                    payload=asdict(repair_assessment),
                ),
                NewEvent(
                    event_type=MEMORY_WRITE_GUARD_EVALUATED,
                    payload=memory_write_guard,
                ),
                NewEvent(
                    event_type=MEMORY_RETENTION_POLICY_APPLIED,
                    payload=memory_retention_policy,
                ),
                NewEvent(
                    event_type=MEMORY_BUNDLE_UPDATED,
                    payload=asdict(memory_bundle),
                ),
                NewEvent(
                    event_type=MEMORY_FORGETTING_APPLIED,
                    payload=memory_forgetting,
                ),
                NewEvent(
                    event_type=MEMORY_RECALL_PERFORMED,
                    payload=memory_recall,
                ),
                NewEvent(
                    event_type=KNOWLEDGE_BOUNDARY_DECIDED,
                    payload=asdict(knowledge_boundary_decision),
                ),
                NewEvent(
                    event_type=POLICY_GATE_DECIDED,
                    payload=asdict(policy_gate),
                ),
                NewEvent(
                    event_type=REHEARSAL_COMPLETED,
                    payload=asdict(rehearsal_result),
                ),
                NewEvent(
                    event_type=REPAIR_PLAN_UPDATED,
                    payload=asdict(repair_plan),
                ),
                NewEvent(
                    event_type=EMPOWERMENT_AUDIT_COMPLETED,
                    payload=asdict(empowerment_audit),
                ),
                NewEvent(
                    event_type=RESPONSE_DRAFT_PLANNED,
                    payload=asdict(response_draft_plan),
                ),
                NewEvent(
                    event_type=RESPONSE_RENDERING_POLICY_DECIDED,
                    payload=asdict(response_rendering_policy),
                ),
                NewEvent(
                    event_type=RUNTIME_COORDINATION_UPDATED,
                    payload=asdict(runtime_coordination_snapshot),
                ),
                NewEvent(
                    event_type=GUIDANCE_PLAN_UPDATED,
                    payload=asdict(guidance_plan),
                ),
                NewEvent(
                    event_type=CONVERSATION_CADENCE_UPDATED,
                    payload=asdict(conversation_cadence_plan),
                ),
                NewEvent(
                    event_type=SESSION_RITUAL_UPDATED,
                    payload=asdict(session_ritual_plan),
                ),
                NewEvent(
                    event_type=SOMATIC_ORCHESTRATION_UPDATED,
                    payload=asdict(somatic_orchestration_plan),
                ),
                NewEvent(
                    event_type=PRIVATE_JUDGMENT_COMPUTED,
                    payload=asdict(private_judgment),
                ),
                NewEvent(
                    event_type=INNER_MONOLOGUE_RECORDED,
                    payload={"entries": [asdict(entry) for entry in inner_monologue]},
                ),
                NewEvent(
                    event_type=SESSION_DIRECTIVE_UPDATED,
                    payload={
                        "directive": asdict(session_directive),
                        "confidence": asdict(confidence_assessment),
                        "strategy": asdict(strategy_decision),
                        "expression_plan": asdict(expression_plan),
                        "guidance_plan": asdict(guidance_plan),
                        "conversation_cadence_plan": asdict(conversation_cadence_plan),
                        "session_ritual_plan": asdict(session_ritual_plan),
                        "somatic_orchestration_plan": asdict(
                            somatic_orchestration_plan
                        ),
                        "response_draft_plan": asdict(response_draft_plan),
                        "response_rendering_policy": asdict(response_rendering_policy),
                    },
                ),
            ]
        )

        assistant_response: str | None = None
        assistant_responses: list[str] = []
        response_sequence_plan = None
        response_post_audit = None
        response_normalization = None
        runtime_quality_doctor_report = None
        if generate_reply:
            drafting_lines = [
                f"- opening_move: {response_draft_plan.opening_move}",
                f"- structure: {', '.join(response_draft_plan.structure)}",
                f"- must_include: {', '.join(response_draft_plan.must_include)}",
                f"- must_avoid: {', '.join(response_draft_plan.must_avoid)}",
                (
                    "- phrasing_constraints: "
                    + ", ".join(response_draft_plan.phrasing_constraints)
                ),
                f"- question_strategy: {response_draft_plan.question_strategy}",
            ]
            rendering_lines = [
                f"- rendering_mode: {response_rendering_policy.rendering_mode}",
                f"- max_sentences: {response_rendering_policy.max_sentences}",
                f"- include_validation: {response_rendering_policy.include_validation}",
                f"- include_next_step: {response_rendering_policy.include_next_step}",
                (
                    "- include_boundary_statement: "
                    f"{response_rendering_policy.include_boundary_statement}"
                ),
                (
                    "- include_uncertainty_statement: "
                    f"{response_rendering_policy.include_uncertainty_statement}"
                ),
                (
                    "- question_count_limit: "
                    f"{response_rendering_policy.question_count_limit}"
                ),
                (
                    "- style_guardrails: "
                    + ", ".join(response_rendering_policy.style_guardrails)
                ),
            ]
            guidance_lines = [
                f"- mode: {guidance_plan.mode}",
                f"- lead_with: {guidance_plan.lead_with}",
                f"- pacing: {guidance_plan.pacing}",
                f"- step_budget: {guidance_plan.step_budget}",
                f"- agency_mode: {guidance_plan.agency_mode}",
                f"- ritual_action: {guidance_plan.ritual_action}",
                f"- checkpoint_style: {guidance_plan.checkpoint_style}",
                f"- handoff_mode: {guidance_plan.handoff_mode}",
                f"- carryover_mode: {guidance_plan.carryover_mode}",
                f"- micro_actions: {', '.join(guidance_plan.micro_actions)}",
                f"- cadence_status: {conversation_cadence_plan.status}",
                f"- cadence_turn_shape: {conversation_cadence_plan.turn_shape}",
                f"- cadence_followup_tempo: {conversation_cadence_plan.followup_tempo}",
                f"- cadence_user_space_mode: {conversation_cadence_plan.user_space_mode}",
                f"- ritual_phase: {session_ritual_plan.phase}",
                f"- ritual_opening_move: {session_ritual_plan.opening_move}",
                f"- ritual_bridge_move: {session_ritual_plan.bridge_move}",
                f"- ritual_closing_move: {session_ritual_plan.closing_move}",
                f"- ritual_somatic_shortcut: {session_ritual_plan.somatic_shortcut}",
                f"- somatic_orchestration_status: {somatic_orchestration_plan.status}",
                f"- somatic_orchestration_mode: {somatic_orchestration_plan.primary_mode}",
                f"- somatic_orchestration_body_anchor: {somatic_orchestration_plan.body_anchor}",
                (
                    "- somatic_orchestration_followup_style: "
                    f"{somatic_orchestration_plan.followup_style}"
                ),
            ]
            llm_messages = [
                LLMMessage(
                    role=message["role"],
                    content=message["content"],
                )
                for message in transcript_messages[-6:]
            ]
            llm_messages.insert(
                0,
                LLMMessage(
                    role="system",
                    content="Use this response drafting plan:\n" + "\n".join(drafting_lines),
                ),
            )
            llm_messages.insert(
                1,
                LLMMessage(
                    role="system",
                    content="Use this guidance plan:\n" + "\n".join(guidance_lines),
                ),
            )
            llm_messages.insert(
                2,
                LLMMessage(
                    role="system",
                    content=(
                        "Use this response rendering policy:\n"
                        + "\n".join(rendering_lines)
                    ),
                ),
            )
            if recalled_memory:
                recall_lines = [
                    f"- [{item.get('layer', 'memory')}] {item.get('value', '')}"
                    for item in recalled_memory[:3]
                ]
                llm_messages.append(
                    LLMMessage(
                        role="system",
                        content="Relevant recalled memory:\n" + "\n".join(recall_lines),
                    )
                )
            llm_messages.append(LLMMessage(role="user", content=user_message))
            llm_response = await self._llm_client.complete(
                LLMRequest(
                    messages=llm_messages,
                    model=self._llm_model,
                    temperature=self._llm_temperature,
                    metadata={
                        "topic": context_frame.topic,
                        "next_action": session_directive.next_action,
                        "memory_recall_count": len(recalled_memory),
                        "memory_filtered_count": int(
                            memory_recall.get("integrity_summary", {}).get(
                                "filtered_count", 0
                            )
                        ),
                        "memory_pinned_count": int(
                            memory_retention_policy.get("pinned_count", 0)
                        ),
                        "boundary_decision": knowledge_boundary_decision.decision,
                        "confidence_response_mode": confidence_assessment.response_mode,
                        "policy_gate_path": policy_gate.selected_path,
                        "empowerment_audit_status": empowerment_audit.status,
                        "drafting_opening_move": response_draft_plan.opening_move,
                        "drafting_question_strategy": response_draft_plan.question_strategy,
                        "drafting_constraint_count": len(
                            response_draft_plan.phrasing_constraints
                        ),
                        "guidance_mode": guidance_plan.mode,
                        "guidance_pacing": guidance_plan.pacing,
                        "guidance_step_budget": guidance_plan.step_budget,
                        "guidance_agency_mode": guidance_plan.agency_mode,
                        "guidance_ritual_action": guidance_plan.ritual_action,
                        "guidance_checkpoint_style": guidance_plan.checkpoint_style,
                        "guidance_handoff_mode": guidance_plan.handoff_mode,
                        "guidance_carryover_mode": guidance_plan.carryover_mode,
                        "cadence_status": conversation_cadence_plan.status,
                        "cadence_turn_shape": conversation_cadence_plan.turn_shape,
                        "cadence_followup_tempo": (
                            conversation_cadence_plan.followup_tempo
                        ),
                        "cadence_user_space_mode": (
                            conversation_cadence_plan.user_space_mode
                        ),
                        "cadence_somatic_track": conversation_cadence_plan.somatic_track,
                        "ritual_phase": session_ritual_plan.phase,
                        "ritual_opening_move": session_ritual_plan.opening_move,
                        "ritual_bridge_move": session_ritual_plan.bridge_move,
                        "ritual_closing_move": session_ritual_plan.closing_move,
                        "ritual_somatic_shortcut": session_ritual_plan.somatic_shortcut,
                        "ritual_continuity_anchor": (
                            session_ritual_plan.continuity_anchor
                        ),
                        "somatic_orchestration_status": (
                            somatic_orchestration_plan.status
                        ),
                        "somatic_orchestration_mode": (
                            somatic_orchestration_plan.primary_mode
                        ),
                        "somatic_orchestration_body_anchor": (
                            somatic_orchestration_plan.body_anchor
                        ),
                        "somatic_orchestration_followup_style": (
                            somatic_orchestration_plan.followup_style
                        ),
                        "rendering_mode": response_rendering_policy.rendering_mode,
                        "rendering_max_sentences": response_rendering_policy.max_sentences,
                        "rendering_question_count_limit": (
                            response_rendering_policy.question_count_limit
                        ),
                        "rendering_include_boundary_statement": (
                            response_rendering_policy.include_boundary_statement
                        ),
                        "rendering_include_uncertainty_statement": (
                            response_rendering_policy.include_uncertainty_statement
                        ),
                        "rendering_include_validation": (
                            response_rendering_policy.include_validation
                        ),
                        "rendering_include_next_step": (
                            response_rendering_policy.include_next_step
                        ),
                    },
                )
            )
            if llm_response.failure is not None:
                assistant_response = build_safe_fallback_text(
                    user_message,
                    rendering_mode=response_rendering_policy.rendering_mode,
                    include_boundary_statement=(
                        response_rendering_policy.include_boundary_statement
                    ),
                    include_uncertainty_statement=(
                        response_rendering_policy.include_uncertainty_statement
                    ),
                    question_count_limit=(
                        response_rendering_policy.question_count_limit
                    ),
                )
                events.append(
                    NewEvent(
                        event_type=LLM_COMPLETION_FAILED,
                        payload={
                            "model": llm_response.model,
                            "error_type": llm_response.failure.error_type,
                            "message": llm_response.failure.message,
                            "retryable": llm_response.failure.retryable,
                        },
                    )
                )
            else:
                assistant_response = llm_response.output_text
            initial_response_post_audit = build_response_post_audit(
                assistant_response=assistant_response,
                response_draft_plan=response_draft_plan,
                response_rendering_policy=response_rendering_policy,
            )
            (
                assistant_response,
                response_normalization,
                response_post_audit,
            ) = build_response_normalization_result(
                assistant_response=assistant_response,
                response_draft_plan=response_draft_plan,
                response_rendering_policy=response_rendering_policy,
                response_post_audit=initial_response_post_audit,
            )
            response_sequence_plan = build_response_sequence_plan(
                assistant_response=assistant_response,
                response_draft_plan=response_draft_plan,
                response_rendering_policy=response_rendering_policy,
                repair_assessment=repair_assessment,
                knowledge_boundary_decision=knowledge_boundary_decision,
            )
            assistant_response_units = build_response_output_units(
                assistant_response=assistant_response,
                response_sequence_plan=response_sequence_plan,
            )
            assistant_responses = [
                item["content"] for item in assistant_response_units if item.get("content")
            ]
            events.append(
                NewEvent(
                    event_type=RESPONSE_NORMALIZED,
                    payload=asdict(response_normalization),
                )
            )
            events.append(
                NewEvent(
                    event_type=RESPONSE_SEQUENCE_PLANNED,
                    payload=asdict(response_sequence_plan),
                )
            )
            should_run_quality_doctor = (
                self._runtime_quality_doctor_interval_turns > 0
                and turn_index % self._runtime_quality_doctor_interval_turns == 0
            )
            if should_run_quality_doctor:
                runtime_quality_doctor_report = build_runtime_quality_doctor_report(
                    transcript_messages=transcript_messages,
                    user_message=user_message,
                    assistant_responses=assistant_responses,
                    triggered_turn_index=turn_index,
                    window_turns=self._runtime_quality_doctor_window_turns,
                )
                events.append(
                    NewEvent(
                        event_type=RUNTIME_QUALITY_DOCTOR_COMPLETED,
                        payload=asdict(runtime_quality_doctor_report),
                    )
                )
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
            events.append(
                NewEvent(
                    event_type=RESPONSE_POST_AUDITED,
                    payload=asdict(response_post_audit),
                )
            )

        system3_snapshot = build_system3_snapshot(
            turn_index=turn_index,
            transcript_messages=transcript_messages,
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_assessment=repair_assessment,
            memory_bundle=memory_bundle,
            memory_recall=memory_recall,
            confidence_assessment=confidence_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            policy_gate=policy_gate,
            strategy_decision=strategy_decision,
            rehearsal_result=rehearsal_result,
            empowerment_audit=empowerment_audit,
            response_sequence_plan=response_sequence_plan,
            response_post_audit=response_post_audit,
            response_normalization=response_normalization,
            runtime_quality_doctor_report=runtime_quality_doctor_report,
        )
        proactive_followup_directive = build_proactive_followup_directive(
            context_frame=context_frame,
            relationship_state=relationship_state,
            confidence_assessment=confidence_assessment,
            knowledge_boundary_decision=knowledge_boundary_decision,
            strategy_decision=strategy_decision,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            system3_snapshot=system3_snapshot,
        )
        proactive_aggregate_governance_assessment = (
            build_proactive_aggregate_governance_assessment(
                system3_snapshot=system3_snapshot
            )
        )
        reengagement_learning_report: dict[str, Any] | None = None
        if (
            proactive_followup_directive.status == "ready"
            and proactive_followup_directive.eligible
        ):
            learning_context_stratum = build_reengagement_learning_context_stratum(
                directive=proactive_followup_directive,
                runtime_coordination_snapshot=runtime_coordination_snapshot,
                guidance_plan=guidance_plan,
                cadence_plan=conversation_cadence_plan,
                session_ritual_plan=session_ritual_plan,
                system3_snapshot=system3_snapshot,
            )
            reengagement_learning_report = (
                await self._evaluation_service.build_reengagement_learning_report(
                    context_stratum=learning_context_stratum
                )
            )
        reengagement_matrix_assessment = build_reengagement_matrix_assessment(
            directive=proactive_followup_directive,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            system3_snapshot=system3_snapshot,
            reengagement_learning_report=reengagement_learning_report,
        )
        reengagement_plan = build_reengagement_plan(
            directive=proactive_followup_directive,
            runtime_coordination_snapshot=runtime_coordination_snapshot,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            system3_snapshot=system3_snapshot,
            reengagement_matrix_assessment=reengagement_matrix_assessment,
        )
        proactive_cadence_plan = build_proactive_cadence_plan(
            directive=proactive_followup_directive,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            reengagement_plan=reengagement_plan,
        )
        proactive_scheduling_plan = build_proactive_scheduling_plan(
            directive=proactive_followup_directive,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            somatic_orchestration_plan=somatic_orchestration_plan,
            proactive_cadence_plan=proactive_cadence_plan,
        )
        proactive_orchestration_plan = build_proactive_orchestration_plan(
            directive=proactive_followup_directive,
            proactive_cadence_plan=proactive_cadence_plan,
            proactive_scheduling_plan=proactive_scheduling_plan,
            reengagement_plan=reengagement_plan,
            session_ritual_plan=session_ritual_plan,
            somatic_orchestration_plan=somatic_orchestration_plan,
        )
        proactive_actuation_plan = build_proactive_actuation_plan(
            directive=proactive_followup_directive,
            proactive_orchestration_plan=proactive_orchestration_plan,
            session_ritual_plan=session_ritual_plan,
            somatic_orchestration_plan=somatic_orchestration_plan,
        )
        proactive_progression_plan = build_proactive_progression_plan(
            directive=proactive_followup_directive,
            proactive_cadence_plan=proactive_cadence_plan,
            proactive_scheduling_plan=proactive_scheduling_plan,
            proactive_orchestration_plan=proactive_orchestration_plan,
        )
        proactive_guardrail_plan = build_proactive_guardrail_plan(
            directive=proactive_followup_directive,
            guidance_plan=guidance_plan,
            cadence_plan=conversation_cadence_plan,
            session_ritual_plan=session_ritual_plan,
            system3_snapshot=system3_snapshot,
            proactive_cadence_plan=proactive_cadence_plan,
            reengagement_matrix_assessment=reengagement_matrix_assessment,
        )
        events.append(
            NewEvent(
                event_type=SYSTEM3_SNAPSHOT_UPDATED,
                payload=asdict(system3_snapshot),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_FOLLOWUP_UPDATED,
                payload=asdict(proactive_followup_directive),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_CADENCE_UPDATED,
                payload=asdict(proactive_cadence_plan),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
                payload=asdict(proactive_aggregate_governance_assessment),
            )
        )
        events.append(
            NewEvent(
                event_type=REENGAGEMENT_MATRIX_ASSESSED,
                payload=asdict(reengagement_matrix_assessment),
            )
        )
        events.append(
            NewEvent(
                event_type=REENGAGEMENT_PLAN_UPDATED,
                payload=asdict(reengagement_plan),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_SCHEDULING_UPDATED,
                payload=asdict(proactive_scheduling_plan),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_ORCHESTRATION_UPDATED,
                payload=asdict(proactive_orchestration_plan),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_ACTUATION_UPDATED,
                payload=asdict(proactive_actuation_plan),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_PROGRESSION_UPDATED,
                payload=asdict(proactive_progression_plan),
            )
        )
        events.append(
            NewEvent(
                event_type=PROACTIVE_GUARDRAIL_UPDATED,
                payload=asdict(proactive_guardrail_plan),
            )
        )

        stored_events = await self._stream_service.append_events(
            stream_id=session_id,
            expected_version=expected_version,
            events=events,
        )
        runtime_projection = await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
        )
        return RuntimeTurnResult(
            session_id=session_id,
            stored_events=stored_events,
            runtime_projection=runtime_projection,
            assistant_response=assistant_response,
            assistant_responses=assistant_responses,
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
