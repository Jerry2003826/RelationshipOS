"""SessionMemoryProjector — multi-layer memory materialization."""

from typing import Any

from relationship_os.application.projectors._helpers import (
    MAX_EPISODIC_HISTORY,
    MAX_WORKING_HISTORY,
    _append_aggregated_items,
    _build_retention_lookup,
    _compact_strings,
    _extract_context_tags,
    _summarize_sequence_retention,
    _trim_retained_sequence,
)
from relationship_os.domain.event_types import (
    MEMORY_BUNDLE_UPDATED,
    MEMORY_FORGETTING_APPLIED,
    MEMORY_RETENTION_POLICY_APPLIED,
    MEMORY_WRITE_GUARD_EVALUATED,
    SESSION_STARTED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class SessionMemoryProjector(Projector[dict[str, Any]]):
    name = "session-memory"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "session_id": None,
            "memory_turn_count": 0,
            "last_updated_at": None,
            "last_bundle_version": None,
            "latest_bundle": None,
            "last_write_guard": None,
            "last_retention_policy": None,
            "last_forgetting": None,
            "write_guard_blocked_total": 0,
            "retention_turn_count": 0,
            "pinned_item_count": 0,
            "forgetting_turn_count": 0,
            "total_evicted_count": 0,
            "working_memory": {
                "current": [],
                "history": [],
                "history_count": 0,
            },
            "episodic_memory": {
                "episodes": [],
                "episode_count": 0,
            },
            "semantic_memory": {
                "concepts": [],
                "concept_count": 0,
            },
            "relational_memory": {
                "signals": [],
                "signal_count": 0,
            },
            "reflective_memory": {
                "insights": [],
                "insight_count": 0,
            },
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            **state,
            "working_memory": {
                "current": list(state["working_memory"]["current"]),
                "history": [dict(item) for item in state["working_memory"]["history"]],
                "history_count": state["working_memory"]["history_count"],
            },
            "episodic_memory": {
                "episodes": [dict(item) for item in state["episodic_memory"]["episodes"]],
                "episode_count": state["episodic_memory"]["episode_count"],
            },
            "semantic_memory": {
                "concepts": [dict(item) for item in state["semantic_memory"]["concepts"]],
                "concept_count": state["semantic_memory"]["concept_count"],
            },
            "last_write_guard": state["last_write_guard"],
            "last_retention_policy": state["last_retention_policy"],
            "last_forgetting": state["last_forgetting"],
            "write_guard_blocked_total": state["write_guard_blocked_total"],
            "retention_turn_count": state["retention_turn_count"],
            "pinned_item_count": state["pinned_item_count"],
            "forgetting_turn_count": state["forgetting_turn_count"],
            "total_evicted_count": state["total_evicted_count"],
            "relational_memory": {
                "signals": [dict(item) for item in state["relational_memory"]["signals"]],
                "signal_count": state["relational_memory"]["signal_count"],
            },
            "reflective_memory": {
                "insights": [dict(item) for item in state["reflective_memory"]["insights"]],
                "insight_count": state["reflective_memory"]["insight_count"],
            },
        }

        if event.event_type == SESSION_STARTED:
            next_state["session_id"] = event.payload.get("session_id", event.stream_id)
            return next_state

        if event.event_type == MEMORY_WRITE_GUARD_EVALUATED:
            next_state["last_write_guard"] = dict(event.payload)
            next_state["write_guard_blocked_total"] += int(
                event.payload.get("blocked_count", 0)
            )
            return next_state

        if event.event_type == MEMORY_RETENTION_POLICY_APPLIED:
            next_state["last_retention_policy"] = dict(event.payload)
            next_state["retention_turn_count"] += 1
            next_state["pinned_item_count"] += int(event.payload.get("pinned_count", 0))
            return next_state

        if event.event_type == MEMORY_FORGETTING_APPLIED:
            evicted_count = int(event.payload.get("evicted_count", 0))
            next_state["last_forgetting"] = dict(event.payload)
            next_state["total_evicted_count"] += evicted_count
            if evicted_count > 0:
                next_state["forgetting_turn_count"] += 1
            return next_state

        if event.event_type != MEMORY_BUNDLE_UPDATED:
            return next_state

        occurred_at = event.occurred_at.isoformat()
        working_items = _compact_strings(
            list(event.payload.get("working_memory", [])),
            limit=4,
        )
        episodic_items = _compact_strings(
            list(event.payload.get("episodic_memory", [])),
            limit=6,
        )
        semantic_items = _compact_strings(
            list(event.payload.get("semantic_memory", [])),
            limit=6,
        )
        relational_items = _compact_strings(
            list(event.payload.get("relational_memory", [])),
            limit=6,
        )
        reflective_items = _compact_strings(
            list(event.payload.get("reflective_memory", [])),
            limit=6,
        )
        context_tags = _extract_context_tags(
            semantic_items=semantic_items,
            relational_items=relational_items,
        )
        retention_policy = dict(next_state.get("last_retention_policy") or {})
        working_retention = _build_retention_lookup(
            retention_policy,
            layer="working_memory",
        )
        episodic_retention = _build_retention_lookup(
            retention_policy,
            layer="episodic_memory",
        )
        semantic_retention = _build_retention_lookup(
            retention_policy,
            layer="semantic_memory",
        )
        relational_retention = _build_retention_lookup(
            retention_policy,
            layer="relational_memory",
        )
        reflective_retention = _build_retention_lookup(
            retention_policy,
            layer="reflective_memory",
        )
        working_retention_summary = _summarize_sequence_retention(
            items=working_items,
            retention_lookup=working_retention,
        )
        episodic_retention_summary = _summarize_sequence_retention(
            items=episodic_items,
            retention_lookup=episodic_retention,
        )

        next_state["session_id"] = next_state["session_id"] or event.stream_id
        next_state["memory_turn_count"] += 1
        next_state["last_updated_at"] = occurred_at
        next_state["last_bundle_version"] = event.version
        next_state["latest_bundle"] = dict(event.payload)

        working_history = list(next_state["working_memory"]["history"])
        working_history.append(
            {
                "source_version": event.version,
                "occurred_at": occurred_at,
                "items": working_items,
                "context_tags": context_tags,
                **working_retention_summary,
            }
        )
        next_state["working_memory"] = {
            "current": working_items,
            "history": _trim_retained_sequence(
                working_history,
                limit=MAX_WORKING_HISTORY,
            ),
            "history_count": len(working_history),
        }

        episodes = list(next_state["episodic_memory"]["episodes"])
        episodes.append(
            {
                "source_version": event.version,
                "occurred_at": occurred_at,
                "items": episodic_items,
                "context_tags": context_tags,
                **episodic_retention_summary,
            }
        )
        next_state["episodic_memory"] = {
            "episodes": _trim_retained_sequence(
                episodes,
                limit=MAX_EPISODIC_HISTORY,
            ),
            "episode_count": len(episodes),
        }

        next_state["semantic_memory"] = {
            "concepts": _append_aggregated_items(
                existing=next_state["semantic_memory"]["concepts"],
                values=semantic_items,
                source_version=event.version,
                occurred_at=occurred_at,
                context_tags=context_tags,
                retention_lookup=semantic_retention,
            ),
            "concept_count": len(next_state["semantic_memory"]["concepts"]) or len(
                semantic_items
            ),
        }
        next_state["semantic_memory"]["concept_count"] = len(
            next_state["semantic_memory"]["concepts"]
        )

        next_state["relational_memory"] = {
            "signals": _append_aggregated_items(
                existing=next_state["relational_memory"]["signals"],
                values=relational_items,
                source_version=event.version,
                occurred_at=occurred_at,
                context_tags=context_tags,
                retention_lookup=relational_retention,
            ),
            "signal_count": len(next_state["relational_memory"]["signals"]) or len(
                relational_items
            ),
        }
        next_state["relational_memory"]["signal_count"] = len(
            next_state["relational_memory"]["signals"]
        )

        next_state["reflective_memory"] = {
            "insights": _append_aggregated_items(
                existing=next_state["reflective_memory"]["insights"],
                values=reflective_items,
                source_version=event.version,
                occurred_at=occurred_at,
                context_tags=context_tags,
                retention_lookup=reflective_retention,
            ),
            "insight_count": len(next_state["reflective_memory"]["insights"]) or len(
                reflective_items
            ),
        }
        next_state["reflective_memory"]["insight_count"] = len(
            next_state["reflective_memory"]["insights"]
        )

        return next_state
