from dataclasses import dataclass
from types import SimpleNamespace

from relationship_os.application.runtime.assistant_message_event_builder import (
    build_assistant_message_events,
)
from relationship_os.domain.event_types import ASSISTANT_MESSAGE_SENT


@dataclass
class _Usage:
    prompt_tokens: int
    completion_tokens: int


@dataclass
class _Failure:
    error_type: str
    message: str
    retryable: bool


def test_build_assistant_message_events_puts_provider_details_on_first_segment_only() -> None:
    events = build_assistant_message_events(
        assistant_response_units=[
            {"content": "first", "label": "opening"},
            {"content": "second", "label": "followup"},
        ],
        llm_response=SimpleNamespace(
            model="model-a",
            usage=_Usage(prompt_tokens=12, completion_tokens=8),
            latency_ms=123,
            failure=_Failure(error_type="timeout", message="slow", retryable=True),
        ),
        response_sequence_plan=SimpleNamespace(mode="two_part_sequence"),
    )

    assert [event.event_type for event in events] == [
        ASSISTANT_MESSAGE_SENT,
        ASSISTANT_MESSAGE_SENT,
    ]
    assert events[0].payload == {
        "content": "first",
        "model": "model-a",
        "usage": {"prompt_tokens": 12, "completion_tokens": 8},
        "latency_ms": 123,
        "failure": {"error_type": "timeout", "message": "slow", "retryable": True},
        "sequence_index": 1,
        "sequence_total": 2,
        "delivery_mode": "two_part_sequence",
        "segment_label": "opening",
    }
    assert events[1].payload["content"] == "second"
    assert events[1].payload["usage"] is None
    assert events[1].payload["latency_ms"] is None
    assert events[1].payload["failure"] is None
    assert events[1].payload["sequence_index"] == 2
