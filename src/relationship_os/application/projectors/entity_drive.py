"""EntityDriveProjector — projects server-wide drives, goals, and tensions."""

from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import (
    ENTITY_DRIVE_UPDATED,
    ENTITY_GOAL_UPDATED,
    ENTITY_SEEDED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class EntityDriveProjector(Projector[dict[str, Any]]):
    name = "entity-drive"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entity_id": None,
            "entity_name": None,
            "drives": {},
            "latent_drives": [],
            "active_goals": [],
            "unresolved_tensions": [],
            "goal_digest": "",
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
                "drives": dict(payload.get("drive_state") or state["drives"]),
                "latent_drives": list((payload.get("goal_state") or {}).get("latent_drives") or []),
                "active_goals": list((payload.get("goal_state") or {}).get("active_goals") or []),
                "unresolved_tensions": list(
                    (payload.get("goal_state") or {}).get("unresolved_tensions") or []
                ),
                "goal_digest": str((payload.get("goal_state") or {}).get("goal_digest") or ""),
                "updated_at": payload.get("seeded_at"),
                "source": "seed",
            }

        if event.event_type == ENTITY_DRIVE_UPDATED:
            return {
                **state,
                "drives": dict(payload.get("drives") or state["drives"]),
                "updated_at": payload.get("occurred_at"),
                "source": payload.get("source", "runtime"),
            }

        if event.event_type == ENTITY_GOAL_UPDATED:
            return {
                **state,
                "latent_drives": list(payload.get("latent_drives") or []),
                "active_goals": list(payload.get("active_goals") or []),
                "unresolved_tensions": list(payload.get("unresolved_tensions") or []),
                "goal_digest": str(payload.get("goal_digest") or ""),
                "updated_at": payload.get("occurred_at"),
                "source": payload.get("source", "runtime"),
            }

        return state
