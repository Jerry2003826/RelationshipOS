"""Shared helper functions for projector implementations."""

from typing import Any

MAX_WORKING_HISTORY = 6
MAX_EPISODIC_HISTORY = 12
MAX_AGGREGATED_MEMORY_ITEMS = 12
MAX_GRAPH_NODES = 48
MAX_GRAPH_EDGES = 96


def _compact_strings(items: list[object], *, limit: int) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = str(item).strip()
        if not cleaned or cleaned in seen:
            continue
        values.append(cleaned)
        seen.add(cleaned)
        if len(values) >= limit:
            break
    return values


def _append_aggregated_items(
    *,
    existing: list[dict[str, Any]],
    values: list[object],
    source_version: int,
    occurred_at: str,
    context_tags: dict[str, str] | None = None,
    retention_lookup: dict[str, dict[str, object]] | None = None,
    limit: int = MAX_AGGREGATED_MEMORY_ITEMS,
) -> list[dict[str, Any]]:
    next_entries = [dict(item) for item in existing]
    index_by_value = {
        str(item.get("value", "")): index
        for index, item in enumerate(next_entries)
        if item.get("value")
    }
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        retention = dict((retention_lookup or {}).get(cleaned, {}))
        entry_index = index_by_value.get(cleaned)
        if entry_index is None:
            next_entries.append(
                {
                    "value": cleaned,
                    "mention_count": 1,
                    "last_seen_at": occurred_at,
                    "source_version": source_version,
                    "last_context_tags": dict(context_tags or {}),
                    "pinned": bool(retention.get("pinned", False)),
                    "retention_score": retention.get("retention_score"),
                    "retention_reason": retention.get("retention_reason"),
                }
            )
            index_by_value[cleaned] = len(next_entries) - 1
            continue
        updated = dict(next_entries[entry_index])
        updated["mention_count"] = int(updated.get("mention_count", 1)) + 1
        updated["last_seen_at"] = occurred_at
        updated["source_version"] = source_version
        updated["last_context_tags"] = dict(context_tags or {})
        updated["pinned"] = bool(updated.get("pinned", False)) or bool(
            retention.get("pinned", False)
        )
        if retention.get("retention_score") is not None:
            updated["retention_score"] = max(
                float(updated.get("retention_score", 0.0) or 0.0),
                float(retention["retention_score"]),
            )
        if retention.get("retention_reason"):
            updated["retention_reason"] = retention["retention_reason"]
        next_entries[entry_index] = updated

    next_entries.sort(
        key=lambda item: (
            bool(item.get("pinned", False)),
            int(item.get("mention_count", 0)),
            int(item.get("source_version", 0)),
            str(item.get("last_seen_at", "")),
        ),
        reverse=True,
    )
    return next_entries[:limit]


def _extract_context_tags(
    *,
    semantic_items: list[str],
    relational_items: list[str],
) -> dict[str, str]:
    context_tags: dict[str, str] = {}
    for value in semantic_items + relational_items:
        if ":" not in value:
            continue
        key, raw_value = value.split(":", 1)
        cleaned_key = key.strip()
        cleaned_value = raw_value.strip()
        if not cleaned_key or not cleaned_value:
            continue
        context_tags[cleaned_key] = cleaned_value
    return context_tags


def _build_retention_lookup(
    policy: dict[str, Any] | None,
    *,
    layer: str,
) -> dict[str, dict[str, Any]]:
    layers = dict((policy or {}).get("layers", {}))
    layer_payload = dict(layers.get(layer, {}))
    items = layer_payload.get("items", [])
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("value", "")): dict(item)
        for item in items
        if isinstance(item, dict) and item.get("value")
    }


def _summarize_sequence_retention(
    *,
    items: list[str],
    retention_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    decisions = [
        dict(retention_lookup.get(item, {}))
        for item in items
        if retention_lookup.get(item) is not None
    ]
    if not decisions:
        return {
            "pinned": False,
            "retention_score": 0.0,
            "retention_reason": "transient_context",
        }
    pinned_items = [item for item in decisions if item.get("pinned")]
    return {
        "pinned": bool(pinned_items),
        "retention_score": max(
            float(item.get("retention_score", 0.0) or 0.0) for item in decisions
        ),
        "retention_reason": str(
            (pinned_items[0] if pinned_items else decisions[0]).get(
                "retention_reason",
                "transient_context",
            )
        ),
    }


def _trim_retained_sequence(
    entries: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    next_entries = [dict(entry) for entry in entries]
    while len(next_entries) > limit:
        pop_index = next(
            (index for index, entry in enumerate(next_entries) if not entry.get("pinned")),
            0,
        )
        next_entries.pop(pop_index)
    return next_entries


def _graph_node_id(*, node_type: str, label: str) -> str:
    return f"{node_type}:{label}"


def _append_graph_nodes(
    *,
    existing: list[dict[str, Any]],
    values: list[object],
    node_type: str,
    source_version: int,
    occurred_at: str,
    limit: int = MAX_GRAPH_NODES,
) -> list[dict[str, Any]]:
    next_nodes = [dict(item) for item in existing]
    index_by_id = {
        str(item.get("id", "")): index
        for index, item in enumerate(next_nodes)
        if item.get("id")
    }
    for value in values:
        label = str(value).strip()
        if not label:
            continue
        node_id = _graph_node_id(node_type=node_type, label=label)
        node_index = index_by_id.get(node_id)
        if node_index is None:
            next_nodes.append(
                {
                    "id": node_id,
                    "label": label,
                    "node_type": node_type,
                    "mention_count": 1,
                    "last_seen_at": occurred_at,
                    "source_version": source_version,
                }
            )
            index_by_id[node_id] = len(next_nodes) - 1
            continue
        updated = dict(next_nodes[node_index])
        updated["mention_count"] = int(updated.get("mention_count", 1)) + 1
        updated["last_seen_at"] = occurred_at
        updated["source_version"] = source_version
        next_nodes[node_index] = updated

    next_nodes.sort(
        key=lambda item: (
            int(item.get("mention_count", 0)),
            int(item.get("source_version", 0)),
            str(item.get("last_seen_at", "")),
        ),
        reverse=True,
    )
    return next_nodes[:limit]


def _append_graph_edges(
    *,
    existing: list[dict[str, Any]],
    relations: list[tuple[str, str, str, str, str]],
    source_version: int,
    occurred_at: str,
    limit: int = MAX_GRAPH_EDGES,
) -> list[dict[str, Any]]:
    next_edges = [dict(item) for item in existing]
    index_by_key = {
        (
            str(item.get("source_id", "")),
            str(item.get("target_id", "")),
            str(item.get("relation", "")),
        ): index
        for index, item in enumerate(next_edges)
        if item.get("source_id") and item.get("target_id") and item.get("relation")
    }
    for source_type, source_label, target_type, target_label, relation in relations:
        cleaned_source_label = str(source_label).strip()
        cleaned_target_label = str(target_label).strip()
        if not cleaned_source_label or not cleaned_target_label:
            continue
        source_id = _graph_node_id(node_type=source_type, label=cleaned_source_label)
        target_id = _graph_node_id(node_type=target_type, label=cleaned_target_label)
        edge_key = (source_id, target_id, relation)
        edge_index = index_by_key.get(edge_key)
        if edge_index is None:
            next_edges.append(
                {
                    "source_id": source_id,
                    "source_label": cleaned_source_label,
                    "source_type": source_type,
                    "target_id": target_id,
                    "target_label": cleaned_target_label,
                    "target_type": target_type,
                    "relation": relation,
                    "weight": 1.0,
                    "last_seen_at": occurred_at,
                    "source_version": source_version,
                }
            )
            index_by_key[edge_key] = len(next_edges) - 1
            continue
        updated = dict(next_edges[edge_index])
        updated["weight"] = round(float(updated.get("weight", 1.0)) + 1.0, 3)
        updated["last_seen_at"] = occurred_at
        updated["source_version"] = source_version
        next_edges[edge_index] = updated

    next_edges.sort(
        key=lambda item: (
            float(item.get("weight", 0.0)),
            int(item.get("source_version", 0)),
            str(item.get("last_seen_at", "")),
        ),
        reverse=True,
    )
    return next_edges[:limit]
