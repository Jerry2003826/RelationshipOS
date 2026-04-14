"""SessionTemporalKGProjector — temporal knowledge graph materialization."""

from typing import Any

from relationship_os.application.projectors._helpers import (
    _append_graph_edges,
    _append_graph_nodes,
    _compact_strings,
)
from relationship_os.domain.event_types import (
    MEMORY_BUNDLE_UPDATED,
    SESSION_STARTED,
)
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class SessionTemporalKGProjector(Projector[dict[str, Any]]):
    name = "session-temporal-kg"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "session_id": None,
            "last_updated_at": None,
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
        }

    def _clone_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            **state,
            "nodes": [dict(item) for item in state["nodes"]],
            "edges": [dict(item) for item in state["edges"]],
        }

    def _apply_session_started(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        next_state["session_id"] = event.payload.get("session_id", event.stream_id)
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
                limit=4,
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

    def _build_memory_nodes(
        self,
        *,
        existing: list[dict[str, Any]],
        layer_items: dict[str, list[str]],
        source_version: int,
        occurred_at: str,
    ) -> list[dict[str, Any]]:
        nodes = list(existing)
        for layer, limit_items in layer_items.items():
            nodes = _append_graph_nodes(
                existing=nodes,
                values=limit_items,
                node_type=layer,
                source_version=source_version,
                occurred_at=occurred_at,
            )
        return nodes

    def _build_memory_relations(
        self,
        *,
        layer_items: dict[str, list[str]],
    ) -> list[tuple[str, str, str, str, str]]:
        relations: list[tuple[str, str, str, str, str]] = []
        episodic_items = layer_items["episodic_memory"]
        semantic_items = layer_items["semantic_memory"]
        relational_items = layer_items["relational_memory"]
        working_items = layer_items["working_memory"]
        reflective_items = layer_items["reflective_memory"]
        for episodic_item in episodic_items:
            for semantic_item in semantic_items:
                relations.append(
                    (
                        "episodic_memory",
                        episodic_item,
                        "semantic_memory",
                        semantic_item,
                        "mentions",
                    )
                )
            for relational_item in relational_items:
                relations.append(
                    (
                        "episodic_memory",
                        episodic_item,
                        "relational_memory",
                        relational_item,
                        "observes",
                    )
                )
        for working_item in working_items:
            for semantic_item in semantic_items:
                relations.append(
                    (
                        "working_memory",
                        working_item,
                        "semantic_memory",
                        semantic_item,
                        "focuses_on",
                    )
                )
            for relational_item in relational_items:
                relations.append(
                    (
                        "working_memory",
                        working_item,
                        "relational_memory",
                        relational_item,
                        "grounds",
                    )
                )
        for semantic_item in semantic_items:
            for relational_item in relational_items:
                relations.append(
                    (
                        "semantic_memory",
                        semantic_item,
                        "relational_memory",
                        relational_item,
                        "signals",
                    )
                )
            for reflective_item in reflective_items:
                relations.append(
                    (
                        "semantic_memory",
                        semantic_item,
                        "reflective_memory",
                        reflective_item,
                        "supports",
                    )
                )
        for relational_item in relational_items:
            for reflective_item in reflective_items:
                relations.append(
                    (
                        "relational_memory",
                        relational_item,
                        "reflective_memory",
                        reflective_item,
                        "informs",
                    )
                )
        return relations

    def _apply_memory_bundle(
        self,
        next_state: dict[str, Any],
        event: StoredEvent,
    ) -> dict[str, Any]:
        occurred_at = event.occurred_at.isoformat()
        layer_items = self._build_memory_bundle_items(event=event)
        next_state["session_id"] = next_state["session_id"] or event.stream_id
        next_state["last_updated_at"] = occurred_at
        next_state["nodes"] = self._build_memory_nodes(
            existing=next_state["nodes"],
            layer_items=layer_items,
            source_version=event.version,
            occurred_at=occurred_at,
        )
        relations = self._build_memory_relations(layer_items=layer_items)
        next_state["edges"] = _append_graph_edges(
            existing=next_state["edges"],
            relations=relations,
            source_version=event.version,
            occurred_at=occurred_at,
        )
        next_state["node_count"] = len(next_state["nodes"])
        next_state["edge_count"] = len(next_state["edges"])
        return next_state

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = self._clone_state(state)
        if event.event_type == SESSION_STARTED:
            return self._apply_session_started(next_state, event)
        if event.event_type != MEMORY_BUNDLE_UPDATED:
            return next_state
        return self._apply_memory_bundle(next_state, event)
