"""ActionStateProjector — projects action intents, plans, and execution receipts."""

from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import (
    ENTITY_ACTION_EXECUTION_DECIDED,
    ENTITY_ACTION_EXECUTION_RECORDED,
    ENTITY_ACTION_INTENT_UPDATED,
    ENTITY_ACTION_PLANNED,
    ENTITY_SEEDED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector

_MAX_RECENT_ITEMS = 40


class ActionStateProjector(Projector[dict[str, Any]]):
    name = "entity-actions"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "entity_id": None,
            "entity_name": None,
            "recent_intents": [],
            "recent_plans": [],
            "recent_gate_decisions": [],
            "recent_receipts": [],
            "pending_confirmations": [],
            "last_action_at": None,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        payload = event.payload
        if event.event_type == ENTITY_SEEDED:
            return {
                **state,
                "entity_id": payload.get("entity_id"),
                "entity_name": payload.get("entity_name"),
            }

        if event.event_type == ENTITY_ACTION_INTENT_UPDATED:
            intents = list(state.get("recent_intents") or [])
            intents.append(dict(payload.get("intent") or {}))
            return {**state, "recent_intents": intents[-_MAX_RECENT_ITEMS:]}

        if event.event_type == ENTITY_ACTION_PLANNED:
            plans = list(state.get("recent_plans") or [])
            plans.append(dict(payload.get("plan") or {}))
            return {**state, "recent_plans": plans[-_MAX_RECENT_ITEMS:]}

        if event.event_type == ENTITY_ACTION_EXECUTION_DECIDED:
            decisions = list(state.get("recent_gate_decisions") or [])
            gate = dict(payload.get("gate") or {})
            decisions.append(gate)
            pending = list(state.get("pending_confirmations") or [])
            if bool(gate.get("confirmation_required")):
                pending.append(gate)
            return {
                **state,
                "recent_gate_decisions": decisions[-_MAX_RECENT_ITEMS:],
                "pending_confirmations": pending[-_MAX_RECENT_ITEMS:],
            }

        if event.event_type == ENTITY_ACTION_EXECUTION_RECORDED:
            receipts = list(state.get("recent_receipts") or [])
            receipt = dict(payload.get("receipt") or {})
            receipts.append(receipt)
            pending = [
                item
                for item in list(state.get("pending_confirmations") or [])
                if item.get("action_id") != receipt.get("action_id")
            ]
            return {
                **state,
                "recent_receipts": receipts[-_MAX_RECENT_ITEMS:],
                "pending_confirmations": pending[-_MAX_RECENT_ITEMS:],
                "last_action_at": payload.get("occurred_at"),
            }

        return state
