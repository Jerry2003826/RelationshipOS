import re
from typing import Any

from relationship_os.application.stream_service import StreamService
from relationship_os.domain.contracts import (
    ContextFrame,
    MemoryBundle,
    RelationshipState,
    RepairPlan,
)

LAYER_WEIGHTS = {
    "working_memory": 1.25,
    "episodic_memory": 1.0,
    "semantic_memory": 0.85,
    "relational_memory": 0.8,
    "reflective_memory": 0.9,
}

PROVENANCE_BASE = {
    "working_memory": 0.92,
    "episodic_memory": 0.88,
    "semantic_memory": 0.72,
    "relational_memory": 0.76,
    "reflective_memory": 0.7,
}

CONTEXTUAL_KEYS = ("topic", "appraisal", "dialogue_act")
MAX_GRAPH_BRIDGES = 6
MAX_MATCHED_NODES = 6
WORKING_MEMORY_HISTORY_LIMIT = 6
EPISODIC_MEMORY_HISTORY_LIMIT = 12
AGGREGATED_MEMORY_LIMIT = 12
BUNDLE_LAYER_LIMITS = {
    "working_memory": 4,
    "episodic_memory": 6,
    "semantic_memory": 6,
    "relational_memory": 6,
    "reflective_memory": 6,
}
LOW_SIGNAL_MEMORY_VALUES = {
    "k",
    "kk",
    "ok",
    "okay",
    "sure",
    "yes",
    "no",
    "嗯",
    "好的",
    "好",
    "收到",
}
RETENTION_BASE = {
    "working_memory": 0.44,
    "episodic_memory": 0.56,
    "semantic_memory": 0.74,
    "relational_memory": 0.78,
    "reflective_memory": 0.68,
}
PIN_THRESHOLD = 0.78


class MemoryService:
    def __init__(self, *, stream_service: StreamService) -> None:
        self._stream_service = stream_service

    async def get_session_memory(self, *, session_id: str) -> dict[str, object]:
        return await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-memory",
            projector_version="v1",
        )

    async def get_session_temporal_kg(self, *, session_id: str) -> dict[str, object]:
        return await self._stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-temporal-kg",
            projector_version="v1",
        )

    async def recall_session_memory(
        self,
        *,
        session_id: str,
        query: str | None,
        limit: int,
        context_filters: dict[str, str] | None = None,
        include_filtered: bool = False,
    ) -> dict[str, object]:
        projection = await self.get_session_memory(session_id=session_id)
        kg_projection = await self.get_session_temporal_kg(session_id=session_id)
        state = projection["state"]
        kg_state = kg_projection["state"]

        normalized_query = (query or "").strip().lower()
        query_tokens = self._tokenize(normalized_query)
        normalized_context = self._normalize_context_filters(context_filters)
        candidates = self._collect_candidates(state)
        matched_nodes, bridges = self._discover_graph_bridges(
            query=normalized_query,
            query_tokens=query_tokens,
            kg_state=kg_state,
        )
        matched_node_labels = {
            str(node.get("label", "")).lower() for node in matched_nodes if node.get("label")
        }
        bridge_labels = {
            str(label).lower()
            for bridge in bridges
            for label in (bridge.get("source_label"), bridge.get("target_label"))
            if label
        }

        accepted_candidates = []
        filtered_candidates = []
        for candidate in candidates:
            retrieval_score = self._score_candidate(
                query=normalized_query,
                query_tokens=query_tokens,
                candidate=candidate,
                matched_node_labels=matched_node_labels,
                bridge_labels=bridge_labels,
            )
            integrity = self._evaluate_integrity(
                candidate=candidate,
                retrieval_score=retrieval_score,
                context_filters=normalized_context,
                matched_node_labels=matched_node_labels,
                bridge_labels=bridge_labels,
            )
            candidate_payload = {
                **candidate,
                "score": round(retrieval_score, 3),
                "provenance": self._build_provenance(candidate),
                "integrity": integrity,
            }
            if normalized_query and retrieval_score <= 0:
                filtered_candidates.append(
                    {
                        **candidate_payload,
                        "filtered_reason": "query_miss",
                    }
                )
                continue
            if integrity["status"] != "accepted":
                filtered_candidates.append(
                    {
                        **candidate_payload,
                        "filtered_reason": "integrity_guard",
                    }
                )
                continue
            accepted_candidates.append(candidate_payload)

        accepted_candidates.sort(
            key=lambda item: (
                float(item["integrity"]["score"]),
                float(item["score"]),
                int(item.get("mention_count", 0)),
                int(item.get("source_version", 0)),
                str(item.get("occurred_at") or item.get("last_seen_at") or ""),
            ),
            reverse=True,
        )
        filtered_candidates.sort(
            key=lambda item: (
                float(item["score"]),
                float(item["integrity"]["score"]),
                int(item.get("source_version", 0)),
            ),
            reverse=True,
        )

        results = accepted_candidates[: max(1, limit)]
        response = {
            "session_id": session_id,
            "query": query,
            "limit": limit,
            "recall_count": len(results),
            "results": results,
            "memory_turn_count": state.get("memory_turn_count", 0),
            "matched_nodes": matched_nodes,
            "bridges": bridges,
            "graph_summary": {
                "node_count": int(kg_state.get("node_count", 0)),
                "edge_count": int(kg_state.get("edge_count", 0)),
                "matched_node_count": len(matched_nodes),
                "bridge_count": len(bridges),
            },
            "integrity_summary": {
                "checked_count": len(candidates),
                "accepted_count": len(results),
                "filtered_count": len(filtered_candidates),
                "active_filters": normalized_context,
            },
        }
        if include_filtered:
            response["filtered_results"] = filtered_candidates[:limit]
        return response

    async def prepare_memory_write(
        self,
        *,
        session_id: str,
        memory_bundle: MemoryBundle,
        context_frame: ContextFrame | None = None,
        relationship_state: RelationshipState | None = None,
        repair_plan: RepairPlan | None = None,
    ) -> dict[str, object]:
        projection = await self.get_session_memory(session_id=session_id)
        state = projection.get("state", {})
        if not isinstance(state, dict):
            state = {}

        sanitized_bundle, write_guard = self._apply_write_guard(memory_bundle=memory_bundle)
        retention_policy = self._build_retention_policy(
            memory_bundle=sanitized_bundle,
            context_frame=context_frame,
            relationship_state=relationship_state,
            repair_plan=repair_plan,
        )
        forgetting = self._predict_forgetting(
            state=state,
            sanitized_bundle=sanitized_bundle,
            retention_policy=retention_policy,
        )
        write_guard["session_id"] = session_id
        retention_policy["session_id"] = session_id
        forgetting["session_id"] = session_id

        return {
            "memory_bundle": sanitized_bundle,
            "write_guard": write_guard,
            "retention_policy": retention_policy,
            "forgetting": forgetting,
        }

    def _build_provenance(self, candidate: dict[str, Any]) -> dict[str, object]:
        occurred_at = candidate.get("occurred_at") or candidate.get("last_seen_at")
        return {
            "layer": candidate.get("layer"),
            "source_version": candidate.get("source_version"),
            "timestamp": occurred_at,
            "mention_count": candidate.get("mention_count", 1),
            "context_tags": dict(candidate.get("context_tags", {})),
            "pinned": bool(candidate.get("pinned", False)),
            "retention_score": candidate.get("retention_score"),
            "retention_reason": candidate.get("retention_reason"),
        }

    def _collect_candidates(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

        working_memory = state.get("working_memory", {})
        for entry in working_memory.get("history", []):
            for value in entry.get("items", []):
                candidates.append(
                    {
                        "layer": "working_memory",
                        "value": value,
                        "source_version": entry.get("source_version"),
                        "occurred_at": entry.get("occurred_at"),
                        "mention_count": 1,
                        "context_tags": dict(entry.get("context_tags", {})),
                        "pinned": bool(entry.get("pinned", False)),
                        "retention_score": entry.get("retention_score"),
                        "retention_reason": entry.get("retention_reason"),
                    }
                )

        episodic_memory = state.get("episodic_memory", {})
        for episode in episodic_memory.get("episodes", []):
            for value in episode.get("items", []):
                candidates.append(
                    {
                        "layer": "episodic_memory",
                        "value": value,
                        "source_version": episode.get("source_version"),
                        "occurred_at": episode.get("occurred_at"),
                        "mention_count": 1,
                        "context_tags": dict(episode.get("context_tags", {})),
                        "pinned": bool(episode.get("pinned", False)),
                        "retention_score": episode.get("retention_score"),
                        "retention_reason": episode.get("retention_reason"),
                    }
                )

        for concept in state.get("semantic_memory", {}).get("concepts", []):
            candidates.append(
                {
                    "layer": "semantic_memory",
                    "value": concept.get("value", ""),
                    "source_version": concept.get("source_version"),
                    "last_seen_at": concept.get("last_seen_at"),
                    "mention_count": concept.get("mention_count", 1),
                    "context_tags": dict(concept.get("last_context_tags", {})),
                    "pinned": bool(concept.get("pinned", False)),
                    "retention_score": concept.get("retention_score"),
                    "retention_reason": concept.get("retention_reason"),
                }
            )

        for signal in state.get("relational_memory", {}).get("signals", []):
            candidates.append(
                {
                    "layer": "relational_memory",
                    "value": signal.get("value", ""),
                    "source_version": signal.get("source_version"),
                    "last_seen_at": signal.get("last_seen_at"),
                    "mention_count": signal.get("mention_count", 1),
                    "context_tags": dict(signal.get("last_context_tags", {})),
                    "pinned": bool(signal.get("pinned", False)),
                    "retention_score": signal.get("retention_score"),
                    "retention_reason": signal.get("retention_reason"),
                }
            )

        for insight in state.get("reflective_memory", {}).get("insights", []):
            candidates.append(
                {
                    "layer": "reflective_memory",
                    "value": insight.get("value", ""),
                    "source_version": insight.get("source_version"),
                    "last_seen_at": insight.get("last_seen_at"),
                    "mention_count": insight.get("mention_count", 1),
                    "context_tags": dict(insight.get("last_context_tags", {})),
                    "pinned": bool(insight.get("pinned", False)),
                    "retention_score": insight.get("retention_score"),
                    "retention_reason": insight.get("retention_reason"),
                }
            )

        return candidates

    def _discover_graph_bridges(
        self,
        *,
        query: str,
        query_tokens: list[str],
        kg_state: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        nodes = list(kg_state.get("nodes", []))
        edges = list(kg_state.get("edges", []))
        if not nodes or (not query and not query_tokens):
            return [], []

        matched_nodes = []
        matched_node_ids: set[str] = set()
        for node in nodes:
            label = str(node.get("label", "")).lower()
            if not label:
                continue
            token_overlap = sum(1 for token in query_tokens if token and token in label)
            if query and query in label:
                token_overlap += 3
            if token_overlap <= 0:
                continue
            matched_node_ids.add(str(node.get("id", "")))
            matched_nodes.append(
                {
                    **node,
                    "match_score": token_overlap,
                }
            )

        matched_nodes.sort(
            key=lambda item: (
                int(item.get("match_score", 0)),
                int(item.get("mention_count", 0)),
                int(item.get("source_version", 0)),
            ),
            reverse=True,
        )
        matched_nodes = matched_nodes[:MAX_MATCHED_NODES]
        matched_node_ids = {str(node.get("id", "")) for node in matched_nodes}

        bridges = []
        for edge in edges:
            source_id = str(edge.get("source_id", ""))
            target_id = str(edge.get("target_id", ""))
            if source_id not in matched_node_ids and target_id not in matched_node_ids:
                continue
            bridges.append(dict(edge))

        bridges.sort(
            key=lambda item: (
                float(item.get("weight", 0.0)),
                int(item.get("source_version", 0)),
                str(item.get("last_seen_at", "")),
            ),
            reverse=True,
        )
        return matched_nodes, bridges[:MAX_GRAPH_BRIDGES]

    def _evaluate_integrity(
        self,
        *,
        candidate: dict[str, Any],
        retrieval_score: float,
        context_filters: dict[str, str],
        matched_node_labels: set[str],
        bridge_labels: set[str],
    ) -> dict[str, object]:
        layer = str(candidate.get("layer", "episodic_memory"))
        normalized_value = str(candidate.get("value", "")).lower().strip()
        context_tags = {
            str(key): str(value)
            for key, value in dict(candidate.get("context_tags", {})).items()
            if value not in {None, ""}
        }
        flags: list[str] = []

        provenance_score = PROVENANCE_BASE.get(layer, 0.7)
        if candidate.get("source_version") is not None:
            provenance_score += 0.04
        else:
            flags.append("missing_source_version")
        if candidate.get("occurred_at") or candidate.get("last_seen_at"):
            provenance_score += 0.03
        else:
            flags.append("missing_timestamp")

        mention_count = max(1, int(candidate.get("mention_count", 1)))
        provenance_score = min(1.0, provenance_score + min(mention_count, 4) * 0.02)
        if candidate.get("pinned"):
            provenance_score = min(1.0, provenance_score + 0.04)
            flags.append("retention_protected")
        if provenance_score < 0.72:
            flags.append("weak_provenance")

        context_score = 0.72 if context_tags else 0.58
        if not context_tags:
            flags.append("missing_context_tags")
        blocking_mismatch = False
        for key in CONTEXTUAL_KEYS:
            expected = context_filters.get(key)
            actual = context_tags.get(key)
            if not expected or not actual:
                continue
            if actual == expected:
                context_score += 0.08
            else:
                flags.append(f"{key}_mismatch")
                context_score -= 0.2
                if key == "topic":
                    blocking_mismatch = True

        graph_score = 0.0
        if normalized_value in matched_node_labels:
            graph_score += 0.18
        if normalized_value in bridge_labels:
            graph_score += 0.12
        if retrieval_score <= 0 and graph_score <= 0:
            flags.append("query_alignment_low")

        total_score = max(
            0.0,
            min(
                1.0,
                provenance_score * 0.5
                + context_score * 0.35
                + min(1.0, retrieval_score / 4.0) * 0.1
                + graph_score * 0.05,
            ),
        )

        accepted = total_score >= 0.62 and not blocking_mismatch
        if not accepted:
            flags.append("integrity_threshold_not_met")

        return {
            "status": "accepted" if accepted else "filtered",
            "score": round(total_score, 3),
            "provenance_score": round(provenance_score, 3),
            "context_score": round(max(0.0, context_score), 3),
            "flags": sorted(set(flags)),
            "context_tags": context_tags,
        }

    def _normalize_context_filters(
        self,
        context_filters: dict[str, str] | None,
    ) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in (context_filters or {}).items():
            cleaned_key = str(key).strip()
            cleaned_value = str(value).strip().lower()
            if not cleaned_key or not cleaned_value:
                continue
            normalized[cleaned_key] = cleaned_value
        return normalized

    def _score_candidate(
        self,
        *,
        query: str,
        query_tokens: list[str],
        candidate: dict[str, Any],
        matched_node_labels: set[str],
        bridge_labels: set[str],
    ) -> float:
        value = str(candidate.get("value", "")).strip()
        if not value:
            return 0.0

        layer = str(candidate.get("layer", "episodic_memory"))
        base_weight = LAYER_WEIGHTS.get(layer, 1.0)
        mention_count = max(1, int(candidate.get("mention_count", 1)))
        normalized_value = value.lower()

        if not query:
            score = base_weight + min(mention_count, 4) * 0.05
            if normalized_value in bridge_labels:
                score += 0.1
            return score

        score = 0.0
        if query in normalized_value:
            score += 3.0
        for token in query_tokens:
            if token and token in normalized_value:
                score += 1.0

        if score == 0.0:
            candidate_tokens = set(self._tokenize(normalized_value))
            overlap = len(candidate_tokens.intersection(query_tokens))
            score += overlap * 0.6

        if normalized_value in matched_node_labels:
            score += 0.75
        if normalized_value in bridge_labels:
            score += 0.55
        if candidate.get("pinned"):
            score += 0.25

        if score == 0.0:
            return 0.0

        return score * base_weight + min(mention_count, 4) * 0.05

    def _tokenize(self, value: str) -> list[str]:
        return [
            token
            for token in re.findall(r"[\w\u4e00-\u9fff:.-]+", value.lower())
            if token
        ]

    def _apply_write_guard(
        self,
        *,
        memory_bundle: MemoryBundle,
    ) -> tuple[MemoryBundle, dict[str, object]]:
        accepted_bundle: dict[str, list[str]] = {}
        blocked_items: list[dict[str, str]] = []
        layer_summary: dict[str, dict[str, int]] = {}
        rules_triggered: set[str] = set()

        for layer, limit in BUNDLE_LAYER_LIMITS.items():
            raw_items = list(getattr(memory_bundle, layer))
            accepted_items: list[str] = []
            seen: set[str] = set()
            blocked_count = 0
            for raw_item in raw_items:
                cleaned = str(raw_item).strip()
                if not cleaned:
                    blocked_items.append(
                        {
                            "layer": layer,
                            "value": str(raw_item),
                            "reason": "empty_value",
                        }
                    )
                    blocked_count += 1
                    rules_triggered.add("empty_value")
                    continue
                normalized = cleaned.lower()
                if normalized in seen:
                    blocked_items.append(
                        {
                            "layer": layer,
                            "value": cleaned,
                            "reason": "duplicate_value",
                        }
                    )
                    blocked_count += 1
                    rules_triggered.add("duplicate_value")
                    continue
                if self._should_block_low_signal(layer=layer, value=cleaned):
                    blocked_items.append(
                        {
                            "layer": layer,
                            "value": cleaned,
                            "reason": "low_signal_value",
                        }
                    )
                    blocked_count += 1
                    rules_triggered.add("low_signal_value")
                    continue

                accepted_items.append(cleaned)
                seen.add(normalized)
                if len(accepted_items) >= limit:
                    break

            accepted_bundle[layer] = accepted_items
            layer_summary[layer] = {
                "raw_count": len(raw_items),
                "accepted_count": len(accepted_items),
                "blocked_count": blocked_count,
            }

        sanitized_bundle = MemoryBundle(
            working_memory=accepted_bundle["working_memory"],
            episodic_memory=accepted_bundle["episodic_memory"],
            semantic_memory=accepted_bundle["semantic_memory"],
            relational_memory=accepted_bundle["relational_memory"],
            reflective_memory=accepted_bundle["reflective_memory"],
        )
        write_guard = {
            "accepted_bundle": {
                layer: list(values) for layer, values in accepted_bundle.items()
            },
            "accepted_count": sum(
                len(values) for values in accepted_bundle.values()
            ),
            "blocked_count": len(blocked_items),
            "blocked_items": blocked_items,
            "rules_triggered": sorted(rules_triggered),
            "layers": layer_summary,
        }
        return sanitized_bundle, write_guard

    def _should_block_low_signal(self, *, layer: str, value: str) -> bool:
        if layer not in {"working_memory", "episodic_memory"}:
            return False

        normalized = value.lower().strip()
        if ":" in normalized:
            content_candidate = normalized.split(":", 1)[-1].strip()
        else:
            content_candidate = normalized
        if content_candidate in LOW_SIGNAL_MEMORY_VALUES:
            return True

        tokens = self._tokenize(content_candidate)
        if len(tokens) <= 1 and len(content_candidate) <= 3:
            return True
        return False

    def _build_retention_policy(
        self,
        *,
        memory_bundle: MemoryBundle,
        context_frame: ContextFrame | None,
        relationship_state: RelationshipState | None,
        repair_plan: RepairPlan | None,
    ) -> dict[str, object]:
        layers: dict[str, dict[str, object]] = {}
        pinned_total = 0
        accepted_total = 0

        for layer in BUNDLE_LAYER_LIMITS:
            decisions = [
                self._build_retention_decision(
                    layer=layer,
                    value=value,
                    context_frame=context_frame,
                    relationship_state=relationship_state,
                    repair_plan=repair_plan,
                )
                for value in getattr(memory_bundle, layer)
            ]
            pinned_count = sum(1 for item in decisions if item["pinned"])
            pinned_total += pinned_count
            accepted_total += len(decisions)
            layers[layer] = {
                "accepted_count": len(decisions),
                "pinned_count": pinned_count,
                "items": decisions,
            }

        return {
            "policy_version": "v1",
            "accepted_count": accepted_total,
            "pinned_count": pinned_total,
            "layers": layers,
        }

    def _build_retention_decision(
        self,
        *,
        layer: str,
        value: str,
        context_frame: ContextFrame | None,
        relationship_state: RelationshipState | None,
        repair_plan: RepairPlan | None,
    ) -> dict[str, object]:
        cleaned = str(value).strip()
        normalized = cleaned.lower()
        score = RETENTION_BASE.get(layer, 0.55)
        signals: list[str] = []
        reason = "transient_context"

        topic = getattr(context_frame, "topic", None)
        appraisal = getattr(context_frame, "appraisal", None)
        bid_signal = getattr(context_frame, "bid_signal", None)
        dependency_risk = getattr(relationship_state, "dependency_risk", None)
        rupture_detected = bool(getattr(repair_plan, "rupture_detected", False))

        if layer == "semantic_memory" and (
            normalized.startswith("topic:")
            or normalized.startswith("appraisal:")
            or normalized.startswith("dialogue_act:")
        ):
            score += 0.12
            signals.append("semantic_anchor")
            reason = "semantic_anchor"
        if layer == "relational_memory" and (
            normalized.startswith("dependency_risk:")
            or normalized.startswith("psychological_safety:")
            or normalized.startswith("bid_signal:")
            or normalized.startswith("turbulence_risk:")
        ):
            score += 0.12
            signals.append("relational_guardrail")
            reason = "relational_guardrail"
        if layer == "reflective_memory":
            score += 0.04
            signals.append("reflective_summary")
            reason = "reflective_summary"

        if appraisal == "negative" and layer in {
            "working_memory",
            "episodic_memory",
            "reflective_memory",
        }:
            score += 0.12
            signals.append("negative_appraisal")
            reason = "salient_emotional_context"
        if bid_signal == "connection_request" and layer in {
            "working_memory",
            "episodic_memory",
            "relational_memory",
        }:
            score += 0.1
            signals.append("connection_bid")
            reason = "salient_emotional_context"
        if dependency_risk == "elevated" and layer == "relational_memory":
            score += 0.12
            signals.append("dependency_guard")
            reason = "relational_guardrail"
        if rupture_detected and layer in {
            "working_memory",
            "episodic_memory",
            "relational_memory",
            "reflective_memory",
        }:
            score += 0.08
            signals.append("rupture_context")
            reason = "repair_relevant_context"
        if topic and topic in normalized:
            score += 0.05
            signals.append("topic_alignment")
        if any(
            token in normalized
            for token in ["anxious", "alone", "stuck", "worried", "焦虑", "担心", "卡住"]
        ):
            score += 0.1
            signals.append("emotional_salience")
            reason = "salient_emotional_context"

        retention_score = round(max(0.0, min(1.0, score)), 3)
        return {
            "value": cleaned,
            "pinned": retention_score >= PIN_THRESHOLD,
            "retention_score": retention_score,
            "retention_reason": reason,
            "signals": sorted(set(signals)),
        }

    def _layer_retention_lookup(
        self,
        *,
        retention_policy: dict[str, object],
        layer: str,
    ) -> dict[str, dict[str, object]]:
        layers = retention_policy.get("layers", {})
        if not isinstance(layers, dict):
            return {}
        layer_payload = layers.get(layer, {})
        if not isinstance(layer_payload, dict):
            return {}
        items = layer_payload.get("items", [])
        if not isinstance(items, list):
            return {}
        return {
            str(item.get("value", "")): dict(item)
            for item in items
            if isinstance(item, dict) and item.get("value")
        }

    def _predict_forgetting(
        self,
        *,
        state: dict[str, Any],
        sanitized_bundle: MemoryBundle,
        retention_policy: dict[str, object],
    ) -> dict[str, object]:
        working_state = dict(state.get("working_memory", {}))
        episodic_state = dict(state.get("episodic_memory", {}))
        semantic_state = dict(state.get("semantic_memory", {}))
        relational_state = dict(state.get("relational_memory", {}))
        reflective_state = dict(state.get("reflective_memory", {}))

        working_history = [dict(item) for item in working_state.get("history", [])]
        episodic_history = [dict(item) for item in episodic_state.get("episodes", [])]
        working_retention = self._layer_retention_lookup(
            retention_policy=retention_policy,
            layer="working_memory",
        )
        episodic_retention = self._layer_retention_lookup(
            retention_policy=retention_policy,
            layer="episodic_memory",
        )
        semantic_retention = self._layer_retention_lookup(
            retention_policy=retention_policy,
            layer="semantic_memory",
        )
        relational_retention = self._layer_retention_lookup(
            retention_policy=retention_policy,
            layer="relational_memory",
        )
        reflective_retention = self._layer_retention_lookup(
            retention_policy=retention_policy,
            layer="reflective_memory",
        )

        predicted_layers = {
            "working_memory": self._predict_sequence_evictions(
                existing=working_history,
                incoming_values=sanitized_bundle.working_memory,
                retention_lookup=working_retention,
                limit=WORKING_MEMORY_HISTORY_LIMIT,
            ),
            "episodic_memory": self._predict_sequence_evictions(
                existing=episodic_history,
                incoming_values=sanitized_bundle.episodic_memory,
                retention_lookup=episodic_retention,
                limit=EPISODIC_MEMORY_HISTORY_LIMIT,
            ),
            "semantic_memory": self._predict_aggregated_evictions(
                existing=semantic_state.get("concepts", []),
                incoming_values=sanitized_bundle.semantic_memory,
                retention_lookup=semantic_retention,
                limit=AGGREGATED_MEMORY_LIMIT,
            ),
            "relational_memory": self._predict_aggregated_evictions(
                existing=relational_state.get("signals", []),
                incoming_values=sanitized_bundle.relational_memory,
                retention_lookup=relational_retention,
                limit=AGGREGATED_MEMORY_LIMIT,
            ),
            "reflective_memory": self._predict_aggregated_evictions(
                existing=reflective_state.get("insights", []),
                incoming_values=sanitized_bundle.reflective_memory,
                retention_lookup=reflective_retention,
                limit=AGGREGATED_MEMORY_LIMIT,
            ),
        }

        evicted_count = sum(
            int(layer["evicted_count"]) for layer in predicted_layers.values()
        )
        return {
            "evicted_count": evicted_count,
            "layers": predicted_layers,
        }

    def _predict_sequence_evictions(
        self,
        *,
        existing: list[dict[str, Any]],
        incoming_values: list[str],
        retention_lookup: dict[str, dict[str, object]],
        limit: int,
    ) -> dict[str, object]:
        next_entries = [dict(item) for item in existing]
        if incoming_values:
            decisions = [
                retention_lookup.get(value, {"value": value, "pinned": False})
                for value in incoming_values
            ]
            next_entries.append(
                {
                    "items": list(incoming_values),
                    "pinned": any(bool(item.get("pinned", False)) for item in decisions),
                    "retention_score": max(
                        float(item.get("retention_score", 0.0)) for item in decisions
                    ),
                    "retention_reason": next(
                        (
                            str(item.get("retention_reason", "transient_context"))
                            for item in decisions
                            if item.get("pinned")
                        ),
                        str(
                            decisions[0].get("retention_reason", "transient_context")
                        ),
                    ),
                }
            )

        evicted_items: list[dict[str, Any]] = []
        while len(next_entries) > limit:
            pop_index = next(
                (index for index, entry in enumerate(next_entries) if not entry.get("pinned")),
                0,
            )
            evicted_items.append(next_entries.pop(pop_index))

        return {
            "limit": limit,
            "evicted_count": len(evicted_items),
            "evicted_items": evicted_items,
        }

    def _predict_aggregated_evictions(
        self,
        *,
        existing: object,
        incoming_values: list[str],
        retention_lookup: dict[str, dict[str, object]],
        limit: int,
    ) -> dict[str, object]:
        existing_entries = [
            dict(item) for item in existing if isinstance(item, dict)
        ] if isinstance(existing, list) else []
        next_entries = [dict(item) for item in existing_entries]
        index_by_value = {
            str(item.get("value", "")): index
            for index, item in enumerate(next_entries)
            if item.get("value")
        }

        for value in incoming_values:
            cleaned = str(value).strip()
            if not cleaned:
                continue
            retention = retention_lookup.get(cleaned, {})
            entry_index = index_by_value.get(cleaned)
            if entry_index is None:
                next_entries.append(
                    {
                        "value": cleaned,
                        "mention_count": 1,
                        "source_version": None,
                        "last_seen_at": None,
                        "pinned": bool(retention.get("pinned", False)),
                        "retention_score": retention.get("retention_score"),
                        "retention_reason": retention.get("retention_reason"),
                    }
                )
                index_by_value[cleaned] = len(next_entries) - 1
                continue
            updated = dict(next_entries[entry_index])
            updated["mention_count"] = int(updated.get("mention_count", 1)) + 1
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
                int(item.get("source_version", 0) or 0),
                str(item.get("last_seen_at", "")),
            ),
            reverse=True,
        )
        evicted_items = next_entries[limit:]
        return {
            "limit": limit,
            "evicted_count": len(evicted_items),
            "evicted_items": evicted_items,
        }
