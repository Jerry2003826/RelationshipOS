from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import LLM_COMPLETION_FAILED
from relationship_os.domain.events import NewEvent


def resolve_turn_reply_completion(
    *,
    llm_response: Any,
    fallback_text: str,
) -> tuple[str, list[NewEvent]]:
    if llm_response.failure is None:
        return llm_response.output_text, []
    return (
        fallback_text,
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
