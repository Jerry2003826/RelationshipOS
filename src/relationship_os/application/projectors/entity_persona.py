"""EntityPersonaProjector — projects the server-wide persona stream."""

from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import (
    ENTITY_CONSCIENCE_UPDATED,
    ENTITY_MOOD_UPDATED,
    ENTITY_PERSONA_UPDATED,
    ENTITY_SEEDED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector

_MAX_GROWTH_HISTORY = 30


class EntityPersonaProjector(Projector[dict[str, Any]]):
    name = "entity-persona"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entity_id": None,
            "entity_name": None,
            "seeded_at": None,
            "seed_excerpt": "",
            "persona_archetype": "default",
            "persona_summary": "",
            "speech_style": "",
            "base_traits": {},
            "current_traits": {},
            "mood": {
                "tone": "steady",
                "energy": 0.5,
                "expression_drive": 0.5,
                "updated_at": None,
                "reason": "uninitialized",
            },
            "conscience": {
                "mode": "withhold",
                "ambiguity_style": "keep_ambiguous",
                "disclosure_style": "hint",
                "dramatic_appetite": 0.5,
                "protectiveness": 0.5,
                "secrecy_tendency": 0.5,
                "updated_at": None,
                "reason": "seed_defaults",
            },
            "growth_history": [],
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        event_type = event.event_type
        payload = event.payload

        if event_type == ENTITY_SEEDED:
            return {
                **state,
                "entity_id": payload.get("entity_id"),
                "entity_name": payload.get("entity_name"),
                "seeded_at": payload.get("seeded_at"),
                "seed_excerpt": payload.get("seed_excerpt", ""),
                "persona_archetype": payload.get("persona_archetype", "default"),
                "persona_summary": payload.get("persona_summary", ""),
                "speech_style": payload.get("speech_style", ""),
                "base_traits": dict(payload.get("base_traits") or {}),
                "current_traits": dict(payload.get("current_traits") or {}),
                "mood": dict(payload.get("mood") or state["mood"]),
                "conscience": dict(payload.get("conscience") or state["conscience"]),
            }

        if event_type == ENTITY_PERSONA_UPDATED:
            history = list(state.get("growth_history") or [])
            history.append(
                {
                    "occurred_at": payload.get("occurred_at"),
                    "reason": payload.get("reason"),
                    "deltas": dict(payload.get("deltas") or {}),
                    "current_traits": dict(payload.get("current_traits") or {}),
                    "user_id": payload.get("user_id"),
                    "session_id": payload.get("session_id"),
                }
            )
            return {
                **state,
                "current_traits": dict(payload.get("current_traits") or {}),
                "growth_history": history[-_MAX_GROWTH_HISTORY:],
            }

        if event_type == ENTITY_MOOD_UPDATED:
            return {
                **state,
                "mood": {
                    **dict(state.get("mood") or {}),
                    **dict(payload.get("mood") or {}),
                    "updated_at": payload.get("occurred_at"),
                    "reason": payload.get("reason"),
                },
            }

        if event_type == ENTITY_CONSCIENCE_UPDATED:
            return {
                **state,
                "conscience": {
                    **dict(state.get("conscience") or {}),
                    **dict(payload.get("conscience") or {}),
                    "updated_at": payload.get("occurred_at"),
                    "reason": payload.get("reason"),
                },
            }

        return state
