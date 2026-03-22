"""InnerMonologueBufferProjector — rolling inner monologue buffer."""

from typing import Any

from relationship_os.domain.event_types import INNER_MONOLOGUE_RECORDED
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class InnerMonologueBufferProjector(Projector[dict[str, Any]]):
    name = "inner-monologue-buffer"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entries": [],
            "entry_count": 0,
            "last_stage": None,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            "entries": list(state["entries"]),
            "entry_count": state["entry_count"],
            "last_stage": state["last_stage"],
        }
        if event.event_type != INNER_MONOLOGUE_RECORDED:
            return next_state

        entries = list(event.payload.get("entries", []))
        next_state["entries"].extend(entries)
        next_state["entries"] = next_state["entries"][-200:]
        next_state["entry_count"] += len(entries)
        if entries:
            next_state["last_stage"] = entries[-1].get("stage")
        return next_state
