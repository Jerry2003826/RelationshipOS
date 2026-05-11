from __future__ import annotations

from dataclasses import asdict
from typing import Any

from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import (
    CONFIDENCE_ASSESSMENT_COMPUTED,
    CONTEXT_FRAME_COMPUTED,
    CONVERSATION_CADENCE_UPDATED,
    EMPOWERMENT_AUDIT_COMPLETED,
    GUIDANCE_PLAN_UPDATED,
    INNER_MONOLOGUE_RECORDED,
    KNOWLEDGE_BOUNDARY_DECIDED,
    MEMORY_BUNDLE_UPDATED,
    MEMORY_FORGETTING_APPLIED,
    MEMORY_RECALL_PERFORMED,
    MEMORY_RETENTION_POLICY_APPLIED,
    MEMORY_WRITE_GUARD_EVALUATED,
    POLICY_GATE_DECIDED,
    PRIVATE_JUDGMENT_COMPUTED,
    REHEARSAL_COMPLETED,
    RELATIONSHIP_STATE_UPDATED,
    REPAIR_ASSESSMENT_COMPUTED,
    REPAIR_PLAN_UPDATED,
    RESPONSE_DRAFT_PLANNED,
    RESPONSE_RENDERING_POLICY_DECIDED,
    RUNTIME_COORDINATION_UPDATED,
    SESSION_DIRECTIVE_UPDATED,
    SESSION_RITUAL_UPDATED,
    SESSION_STARTED,
    SOMATIC_ORCHESTRATION_UPDATED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import NewEvent, utc_now


def build_turn_events(
    *,
    session_id: str,
    user_message: str,
    metadata: dict[str, Any] | None,
    turn_context: Any,
    analysis: Any,
    turn_input: TurnInput | None = None,
) -> list[NewEvent]:
    metadata_payload = metadata or {}
    events = build_session_start_events(
        session_id=session_id,
        metadata_payload=metadata_payload,
        turn_context=turn_context,
    )
    events.extend(
        build_turn_analysis_events(
            user_message=user_message,
            metadata_payload=metadata_payload,
            analysis=analysis,
            turn_input=turn_input,
        )
    )
    return events


def build_session_start_events(
    *,
    session_id: str,
    metadata_payload: dict[str, Any],
    turn_context: Any,
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


def build_turn_analysis_events(
    *,
    user_message: str,
    metadata_payload: dict[str, Any],
    analysis: Any,
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
            payload={"entries": [asdict(entry) for entry in analysis.inner_monologue]},
        ),
        NewEvent(
            event_type=SESSION_DIRECTIVE_UPDATED,
            payload=build_session_directive_payload(analysis),
        ),
    ]


def build_session_directive_payload(analysis: Any) -> dict[str, Any]:
    return {
        "directive": asdict(analysis.session_directive),
        "confidence": asdict(analysis.confidence_assessment),
        "strategy": asdict(analysis.strategy_decision),
        "expression_plan": asdict(analysis.expression_plan),
        "guidance_plan": asdict(analysis.guidance_plan),
        "conversation_cadence_plan": asdict(analysis.conversation_cadence_plan),
        "session_ritual_plan": asdict(analysis.session_ritual_plan),
        "somatic_orchestration_plan": asdict(analysis.somatic_orchestration_plan),
        "response_draft_plan": asdict(analysis.response_draft_plan),
        "response_rendering_policy": asdict(analysis.response_rendering_policy),
    }
