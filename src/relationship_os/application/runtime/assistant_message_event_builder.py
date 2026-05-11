from __future__ import annotations

from dataclasses import asdict
from typing import Any

from relationship_os.domain.event_types import ASSISTANT_MESSAGE_SENT
from relationship_os.domain.events import NewEvent


def build_assistant_message_events(
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
                        asdict(llm_response.usage) if llm_response.usage and index == 1 else None
                    ),
                    "latency_ms": (llm_response.latency_ms if index == 1 else None),
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
