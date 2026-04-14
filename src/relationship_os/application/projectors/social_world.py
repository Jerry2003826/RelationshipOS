"""SocialWorldProjector — projects global relationship drift and disclosure history."""

from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import (
    ENTITY_CONSCIENCE_UPDATED,
    ENTITY_RELATIONSHIP_WORLD_MODEL_UPDATED,
    ENTITY_SEEDED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector

_MAX_DECISIONS = 30
_MAX_DISCLOSURES = 20


class SocialWorldProjector(Projector[dict[str, Any]]):
    name = "entity-social-world"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entity_id": None,
            "entity_name": None,
            "relationships": {},
            "social_edges": [],
            "recent_cross_user_disclosures": [],
            "recent_conscience_decisions": [],
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        event_type = event.event_type
        payload = event.payload

        if event_type == ENTITY_SEEDED:
            return {
                **state,
                "entity_id": payload.get("entity_id"),
                "entity_name": payload.get("entity_name"),
            }

        if event_type == ENTITY_RELATIONSHIP_WORLD_MODEL_UPDATED:
            user_id = str(payload.get("user_id") or "").strip()
            relationships = dict(state.get("relationships") or {})
            if user_id:
                relationships[user_id] = {
                    **dict(relationships.get(user_id) or {}),
                    **dict(payload.get("relationship_drift") or {}),
                    "updated_at": payload.get("occurred_at"),
                    "session_id": payload.get("session_id"),
                }
            social_edges = list(state.get("social_edges") or [])
            for edge in payload.get("social_edges") or []:
                source = str(edge.get("source_user_id") or "").strip()
                target = str(edge.get("target_user_id") or "").strip()
                if not source or not target:
                    continue
                existing_index = next(
                    (
                        index
                        for index, item in enumerate(social_edges)
                        if item.get("source_user_id") == source
                        and item.get("target_user_id") == target
                    ),
                    None,
                )
                merged = {
                    "source_user_id": source,
                    "target_user_id": target,
                    "strength": max(
                        float(edge.get("strength", 0.0)),
                        float(
                            (
                                social_edges[existing_index].get("strength")
                                if existing_index is not None
                                else 0.0
                            )
                            or 0.0
                        ),
                    ),
                    "relation": edge.get("relation", "mentioned"),
                    "last_mentioned_at": payload.get("occurred_at"),
                }
                if existing_index is None:
                    social_edges.append(merged)
                else:
                    social_edges[existing_index] = merged
            return {
                **state,
                "relationships": relationships,
                "social_edges": social_edges,
            }

        if event_type == ENTITY_CONSCIENCE_UPDATED:
            recent_decisions = list(state.get("recent_conscience_decisions") or [])
            decision = {
                "occurred_at": payload.get("occurred_at"),
                "user_id": payload.get("user_id"),
                "session_id": payload.get("session_id"),
                "mode": payload.get("conscience", {}).get("mode"),
                "reason": payload.get("reason"),
                "source_user_ids": list(payload.get("source_user_ids") or []),
            }
            recent_decisions.append(decision)
            disclosures = list(state.get("recent_cross_user_disclosures") or [])
            if payload.get("conscience", {}).get("mode") in {
                "partial_reveal",
                "direct_reveal",
                "dramatic_confrontation",
            }:
                disclosures.append(decision)
            return {
                **state,
                "recent_conscience_decisions": recent_decisions[-_MAX_DECISIONS:],
                "recent_cross_user_disclosures": disclosures[-_MAX_DISCLOSURES:],
            }

        return state
