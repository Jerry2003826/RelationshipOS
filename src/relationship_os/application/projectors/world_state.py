"""WorldStateProjector — projects the entity's digital world and action surface."""

from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import (
    ENTITY_ENVIRONMENT_APPRAISAL_UPDATED,
    ENTITY_SEEDED,
    SYSTEM_ACTION_SURFACE_UPDATED,
    SYSTEM_WORLD_STATE_UPDATED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class WorldStateProjector(Projector[dict[str, Any]]):
    name = "entity-world-state"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entity_id": None,
            "entity_name": None,
            "time_of_day": "unknown",
            "circadian_phase": "day",
            "sleep_pressure": 0.36,
            "device": {},
            "communication": {},
            "tasks": {},
            "action_surface": {},
            "environment_appraisal": {},
            "updated_at": None,
            "source": "seed",
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        payload = event.payload
        if event.event_type == ENTITY_SEEDED:
            world = dict(payload.get("world_state") or {})
            return {
                **state,
                "entity_id": payload.get("entity_id"),
                "entity_name": payload.get("entity_name"),
                "time_of_day": world.get("time_of_day", state["time_of_day"]),
                "circadian_phase": world.get("circadian_phase", state["circadian_phase"]),
                "sleep_pressure": float(world.get("sleep_pressure", state["sleep_pressure"])),
                "device": dict(world.get("device") or {}),
                "communication": dict(world.get("communication") or {}),
                "tasks": dict(world.get("tasks") or {}),
                "action_surface": dict(world.get("action_surface") or {}),
                "environment_appraisal": dict(
                    world.get("environment_appraisal") or {}
                ),
                "updated_at": payload.get("seeded_at"),
                "source": "seed",
            }
        if event.event_type == SYSTEM_WORLD_STATE_UPDATED:
            return {
                **state,
                **{
                    "time_of_day": payload.get("time_of_day", state["time_of_day"]),
                    "circadian_phase": payload.get(
                        "circadian_phase",
                        state["circadian_phase"],
                    ),
                    "sleep_pressure": float(
                        payload.get("sleep_pressure", state["sleep_pressure"])
                    ),
                    "device": dict(payload.get("device") or state.get("device") or {}),
                    "communication": dict(
                        payload.get("communication")
                        or state.get("communication")
                        or {}
                    ),
                    "tasks": dict(payload.get("tasks") or state.get("tasks") or {}),
                    "updated_at": payload.get("occurred_at"),
                    "source": payload.get("source", "runtime"),
                },
            }
        if event.event_type == SYSTEM_ACTION_SURFACE_UPDATED:
            return {
                **state,
                "action_surface": dict(
                    payload.get("action_surface")
                    or state.get("action_surface")
                    or {}
                ),
                "updated_at": payload.get("occurred_at"),
                "source": payload.get("source", "action"),
            }
        if event.event_type == ENTITY_ENVIRONMENT_APPRAISAL_UPDATED:
            return {
                **state,
                "environment_appraisal": dict(
                    payload.get("environment_appraisal")
                    or state.get("environment_appraisal")
                    or {}
                ),
                "updated_at": payload.get("occurred_at"),
                "source": payload.get("source", "runtime"),
            }
        return state

