from dataclasses import dataclass
from types import SimpleNamespace

from relationship_os.application.runtime.turn_analysis_event_builder import build_turn_events
from relationship_os.domain.contracts.turn_input import Attachment, TurnInput
from relationship_os.domain.event_types import (
    CONTEXT_FRAME_COMPUTED,
    SESSION_DIRECTIVE_UPDATED,
    SESSION_STARTED,
    USER_MESSAGE_RECEIVED,
)


@dataclass
class _Value:
    value: str


def _analysis() -> SimpleNamespace:
    return SimpleNamespace(
        context_frame=_Value("context"),
        relationship_state=_Value("relationship"),
        confidence_assessment=_Value("confidence"),
        repair_assessment=_Value("repair"),
        memory_write_guard={"allowed": True},
        memory_retention_policy={"keep": True},
        memory_bundle=_Value("bundle"),
        memory_forgetting={"forgot": []},
        memory_recall={"items": []},
        knowledge_boundary_decision=_Value("boundary"),
        policy_gate=_Value("policy"),
        rehearsal_result=_Value("rehearsal"),
        repair_plan=_Value("repair-plan"),
        empowerment_audit=_Value("audit"),
        response_draft_plan=_Value("draft"),
        response_rendering_policy=_Value("rendering"),
        runtime_coordination_snapshot=_Value("runtime"),
        guidance_plan=_Value("guidance"),
        conversation_cadence_plan=_Value("cadence"),
        session_ritual_plan=_Value("ritual"),
        somatic_orchestration_plan=_Value("somatic"),
        private_judgment=_Value("private"),
        inner_monologue=[_Value("inner")],
        session_directive=_Value("directive"),
        strategy_decision=_Value("strategy"),
        expression_plan=_Value("expression"),
    )


def test_build_turn_events_preserves_session_start_user_event_and_directive_payload() -> None:
    turn_context = SimpleNamespace(prior_events=[])
    turn_input = TurnInput(
        text="hello",
        attachments=[
            Attachment(
                type="image",
                url="https://example.test/cat.png",
                mime_type="image/png",
                filename="cat.png",
            )
        ],
    )

    events = build_turn_events(
        session_id="session-1",
        user_message="hello",
        metadata={"source": "test"},
        turn_context=turn_context,
        analysis=_analysis(),
        turn_input=turn_input,
    )

    assert [event.event_type for event in events[:3]] == [
        SESSION_STARTED,
        USER_MESSAGE_RECEIVED,
        CONTEXT_FRAME_COMPUTED,
    ]
    assert events[0].payload["session_id"] == "session-1"
    assert events[0].payload["metadata"] == {"source": "test"}
    assert events[1].payload == {
        "content": "hello",
        "attachments": [
            {
                "type": "image",
                "url": "https://example.test/cat.png",
                "mime_type": "image/png",
                "filename": "cat.png",
            }
        ],
    }
    assert events[1].metadata == {"source": "test"}
    assert events[-1].event_type == SESSION_DIRECTIVE_UPDATED
    assert events[-1].payload["directive"] == {"value": "directive"}
    assert events[-1].payload["strategy"] == {"value": "strategy"}
