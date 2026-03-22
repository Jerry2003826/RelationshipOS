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

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            **state,
            "nodes": [dict(item) for item in state["nodes"]],
            "edges": [dict(item) for item in state["edges"]],
        }

        if event.event_type == SESSION_STARTED:
            next_state["session_id"] = event.payload.get("session_id", event.stream_id)
            return next_state

        if event.event_type != MEMORY_BUNDLE_UPDATED:
            return next_state

        occurred_at = event.occurred_at.isoformat()
        next_state["session_id"] = next_state["session_id"] or event.stream_id
        next_state["last_updated_at"] = occurred_at

        working_items = _compact_strings(list(event.payload.get("working_memory", [])), limit=4)
        episodic_items = _compact_strings(list(event.payload.get("episodic_memory", [])), limit=4)
        semantic_items = _compact_strings(list(event.payload.get("semantic_memory", [])), limit=6)
        relational_items = _compact_strings(
            list(event.payload.get("relational_memory", [])),
            limit=6,
        )
        reflective_items = _compact_strings(
            list(event.payload.get("reflective_memory", [])),
            limit=6,
        )

        nodes = list(next_state["nodes"])
        nodes = _append_graph_nodes(
            existing=nodes,
            values=working_items,
            node_type="working_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=episodic_items,
            node_type="episodic_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=semantic_items,
            node_type="semantic_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=relational_items,
            node_type="relational_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        nodes = _append_graph_nodes(
            existing=nodes,
            values=reflective_items,
            node_type="reflective_memory",
            source_version=event.version,
            occurred_at=occurred_at,
        )
        next_state["nodes"] = nodes

        relations: list[tuple[str, str, str, str, str]] = []
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

        next_state["edges"] = _append_graph_edges(
            existing=next_state["edges"],
            relations=relations,
            source_version=event.version,
            occurred_at=occurred_at,
        )
        next_state["node_count"] = len(next_state["nodes"])
        next_state["edge_count"] = len(next_state["edges"])
        return next_state
