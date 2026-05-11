from dataclasses import dataclass
from types import SimpleNamespace

from relationship_os.application.runtime.reply_completion_resolver import (
    resolve_turn_reply_completion,
)
from relationship_os.domain.event_types import LLM_COMPLETION_FAILED


@dataclass
class _Failure:
    error_type: str
    message: str
    retryable: bool


def test_resolve_turn_reply_completion_returns_llm_output_when_successful() -> None:
    assistant_response, events = resolve_turn_reply_completion(
        llm_response=SimpleNamespace(
            failure=None,
            output_text="hello",
            model="model-a",
        ),
        fallback_text="fallback",
    )

    assert assistant_response == "hello"
    assert events == []


def test_resolve_turn_reply_completion_records_failure_and_uses_fallback() -> None:
    assistant_response, events = resolve_turn_reply_completion(
        llm_response=SimpleNamespace(
            failure=_Failure(error_type="timeout", message="slow", retryable=True),
            output_text="",
            model="model-a",
        ),
        fallback_text="fallback",
    )

    assert assistant_response == "fallback"
    assert len(events) == 1
    assert events[0].event_type == LLM_COMPLETION_FAILED
    assert events[0].payload == {
        "model": "model-a",
        "error_type": "timeout",
        "message": "slow",
        "retryable": True,
    }
