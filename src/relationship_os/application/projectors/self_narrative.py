"""SelfNarrativeProjector — projects the entity's evolving self narrative."""

from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import ENTITY_SEEDED, ENTITY_SELF_NARRATIVE_UPDATED
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class SelfNarrativeProjector(Projector[dict[str, Any]]):
    name = "entity-self-narrative"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entity_id": None,
            "entity_name": None,
            "summary": "",
            "recent_entries": [],
            "narrative_digest": "",
            "updated_at": None,
            "source": "seed",
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        payload = event.payload
        if event.event_type == ENTITY_SEEDED:
            return {
                **state,
                "entity_id": payload.get("entity_id"),
                "entity_name": payload.get("entity_name"),
                "summary": str((payload.get("self_narrative") or {}).get("summary") or ""),
                "recent_entries": list(
                    (payload.get("self_narrative") or {}).get("recent_entries") or []
                ),
                "narrative_digest": str(
                    (payload.get("self_narrative") or {}).get("narrative_digest") or ""
                ),
                "updated_at": payload.get("seeded_at"),
                "source": "seed",
            }
        if event.event_type == ENTITY_SELF_NARRATIVE_UPDATED:
            return {
                **state,
                "summary": str(payload.get("summary") or state["summary"]),
                "recent_entries": list(payload.get("recent_entries") or []),
                "narrative_digest": str(payload.get("narrative_digest") or ""),
                "updated_at": payload.get("occurred_at"),
                "source": payload.get("source", "runtime"),
            }
        return state
