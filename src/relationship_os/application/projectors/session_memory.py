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

    _EVENT_APPLIERS = {
        SESSION_STARTED: "_apply_session_started",
        MEMORY_WRITE_GUARD_EVALUATED: "_apply_write_guard_evaluated",
        MEMORY_RETENTION_POLICY_APPLIED: "_apply_retention_policy",
        MEMORY_FORGETTING_APPLIED: "_apply_forgetting",
        MEMORY_BUNDLE_UPDATED: "_apply_memory_bundle",
    }

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

    def _clone_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
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

    def _apply_session_started(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        next_state["session_id"] = event.payload.get("session_id", event.stream_id)
        return next_state

    def _apply_write_guard_evaluated(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        next_state["last_write_guard"] = dict(event.payload)
        next_state["write_guard_blocked_total"] += int(
            event.payload.get("blocked_count", 0)
        )
        return next_state

    def _apply_retention_policy(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        next_state["last_retention_policy"] = dict(event.payload)
        next_state["retention_turn_count"] += 1
        next_state["pinned_item_count"] += int(event.payload.get("pinned_count", 0))
        return next_state

    def _apply_forgetting(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        evicted_count = int(event.payload.get("evicted_count", 0))
        next_state["last_forgetting"] = dict(event.payload)
        next_state["total_evicted_count"] += evicted_count
        if evicted_count > 0:
            next_state["forgetting_turn_count"] += 1
        return next_state

    def _apply_memory_bundle(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        occurred_at = event.occurred_at.isoformat()
        layer_items = self._build_memory_bundle_items(event=event)
        context_tags = _extract_context_tags(
            semantic_items=layer_items["semantic_memory"],
            relational_items=layer_items["relational_memory"],
        )
        retention_lookups = self._build_memory_bundle_retention_lookups(
            next_state=next_state
        )
        working_retention_summary = _summarize_sequence_retention(
            items=layer_items["working_memory"],
            retention_lookup=retention_lookups["working_memory"],
        )
        episodic_retention_summary = _summarize_sequence_retention(
            items=layer_items["episodic_memory"],
            retention_lookup=retention_lookups["episodic_memory"],
        )

        next_state["session_id"] = next_state["session_id"] or event.stream_id
        next_state["memory_turn_count"] += 1
        next_state["last_updated_at"] = occurred_at
        next_state["last_bundle_version"] = event.version
        next_state["latest_bundle"] = dict(event.payload)

        next_state["working_memory"] = self._build_working_memory_state(
            current_state=next_state["working_memory"],
            items=layer_items["working_memory"],
            context_tags=context_tags,
            source_version=event.version,
            occurred_at=occurred_at,
            retention_summary=working_retention_summary,
        )

        next_state["episodic_memory"] = self._build_episodic_memory_state(
            current_state=next_state["episodic_memory"],
            items=layer_items["episodic_memory"],
            context_tags=context_tags,
            source_version=event.version,
            occurred_at=occurred_at,
            retention_summary=episodic_retention_summary,
        )

        next_state["semantic_memory"] = self._build_aggregated_memory_state(
            items=layer_items["semantic_memory"],
            entry_key="concepts",
            count_key="concept_count",
            existing=next_state["semantic_memory"]["concepts"],
            source_version=event.version,
            occurred_at=occurred_at,
            context_tags=context_tags,
            retention_lookup=retention_lookups["semantic_memory"],
        )

        next_state["relational_memory"] = self._build_aggregated_memory_state(
            items=layer_items["relational_memory"],
            entry_key="signals",
            count_key="signal_count",
            existing=next_state["relational_memory"]["signals"],
            source_version=event.version,
            occurred_at=occurred_at,
            context_tags=context_tags,
            retention_lookup=retention_lookups["relational_memory"],
        )

        next_state["reflective_memory"] = self._build_aggregated_memory_state(
            items=layer_items["reflective_memory"],
            entry_key="insights",
            count_key="insight_count",
            existing=next_state["reflective_memory"]["insights"],
            source_version=event.version,
            occurred_at=occurred_at,
            context_tags=context_tags,
            retention_lookup=retention_lookups["reflective_memory"],
        )
        return next_state

    def _build_memory_bundle_items(
        self,
        *,
        event: StoredEvent,
    ) -> dict[str, list[str]]:
        return {
            "working_memory": _compact_strings(
                list(event.payload.get("working_memory", [])),
                limit=4,
            ),
            "episodic_memory": _compact_strings(
                list(event.payload.get("episodic_memory", [])),
                limit=6,
            ),
            "semantic_memory": _compact_strings(
                list(event.payload.get("semantic_memory", [])),
                limit=6,
            ),
            "relational_memory": _compact_strings(
                list(event.payload.get("relational_memory", [])),
                limit=6,
            ),
            "reflective_memory": _compact_strings(
                list(event.payload.get("reflective_memory", [])),
                limit=6,
            ),
        }

    def _build_memory_bundle_retention_lookups(
        self,
        *,
        next_state: dict[str, Any],
    ) -> dict[str, dict[str, dict[str, Any]]]:
        retention_policy = dict(next_state.get("last_retention_policy") or {})
        return {
            layer: _build_retention_lookup(retention_policy, layer=layer)
            for layer in (
                "working_memory",
                "episodic_memory",
                "semantic_memory",
                "relational_memory",
                "reflective_memory",
            )
        }

    def _build_working_memory_state(
        self,
        *,
        current_state: dict[str, Any],
        items: list[str],
        context_tags: list[str],
        source_version: int,
        occurred_at: str,
        retention_summary: dict[str, Any],
    ) -> dict[str, Any]:
        working_history = list(current_state["history"])
        working_history.append(
            {
                "source_version": source_version,
                "occurred_at": occurred_at,
                "items": items,
                "context_tags": context_tags,
                **retention_summary,
            }
        )
        return {
            "current": items,
            "history": _trim_retained_sequence(
                working_history,
                limit=MAX_WORKING_HISTORY,
            ),
            "history_count": len(working_history),
        }

    def _build_episodic_memory_state(
        self,
        *,
        current_state: dict[str, Any],
        items: list[str],
        context_tags: list[str],
        source_version: int,
        occurred_at: str,
        retention_summary: dict[str, Any],
    ) -> dict[str, Any]:
        episodes = list(current_state["episodes"])
        episodes.append(
            {
                "source_version": source_version,
                "occurred_at": occurred_at,
                "items": items,
                "context_tags": context_tags,
                **retention_summary,
            }
        )
        return {
            "episodes": _trim_retained_sequence(
                episodes,
                limit=MAX_EPISODIC_HISTORY,
            ),
            "episode_count": len(episodes),
        }

    def _build_aggregated_memory_state(
        self,
        *,
        items: list[str],
        entry_key: str,
        count_key: str,
        existing: list[dict[str, Any]],
        source_version: int,
        occurred_at: str,
        context_tags: list[str],
        retention_lookup: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        aggregated_items = _append_aggregated_items(
            existing=existing,
            values=items,
            source_version=source_version,
            occurred_at=occurred_at,
            context_tags=context_tags,
            retention_lookup=retention_lookup,
        )
        return {
            entry_key: aggregated_items,
            count_key: len(aggregated_items),
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = self._clone_state(state)
        applier_name = self._EVENT_APPLIERS.get(event.event_type)
        if applier_name is None:
            return next_state
        applier = getattr(self, applier_name)
        return applier(next_state, event)
