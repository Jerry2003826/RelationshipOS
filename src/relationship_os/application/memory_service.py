import logging
import re
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from relationship_os.application.factual_memory_backends import (
    FactualMemoryBackend,
    FactualMemoryCandidate,
)
from relationship_os.application.memory_index import (
    MemoryIndex,
    MemoryIndexHit,
    MemoryIndexRecord,
    MemoryMediaAttachment,
    NullMemoryIndex,
)
from relationship_os.application.policy_registry import (
    PolicyRegistry,
    get_default_compiled_policy_set,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.contracts import (
    ContextFrame,
    MemoryBundle,
    RelationshipState,
    RepairPlan,
)

logger = logging.getLogger(__name__)

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
SEMANTIC_ALIAS_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "identity_name",
        (
            "my name is",
            "i am ",
            "i'm ",
            "im ",
            "我叫",
            "我的名字",
            "名字叫",
            "叫什么",
        ),
    ),
    (
        "origin_grew_up",
        (
            "grew up",
            "raised in",
            "from childhood in",
            "长大",
            "从小在",
            "老家",
            "在哪里长大",
        ),
    ),
    (
        "current_residence",
        (
            "live in",
            "living in",
            "moved to",
            "住在",
            "现在住",
            "搬到",
            "在哪里住",
            "住哪",
        ),
    ),
    (
        "occupation",
        (
            "i work",
            "work as",
            "job",
            "职业",
            "工作",
            "上班",
            "做什么工作",
        ),
    ),
    (
        "pet_dog",
        (
            " dog",
            "dog ",
            "puppy",
            "狗",
            "狗狗",
            "小狗",
        ),
    ),
    (
        "pet_cat",
        (
            " cat",
            "cat ",
            "kitty",
            "kitten",
            "猫",
            "猫咪",
            "小猫",
            "橘猫",
        ),
    ),
    (
        "pet_name",
        (
            "dog's name",
            "cat's name",
            "named ",
            "名字叫",
            "叫什么",
            "狗叫",
            "猫叫",
            "狗的名字",
            "猫的名字",
        ),
    ),
    (
        "memory_query",
        (
            "remember",
            "remind me",
            "do you know",
            "记得",
            "还记得",
            "你知道",
            "提醒我",
        ),
    ),
    (
        "question_where",
        (
            "where",
            "哪里",
            "哪儿",
            "在哪",
        ),
    ),
    (
        "question_who",
        (
            "who",
            "谁",
        ),
    ),
    (
        "question_what",
        (
            "what",
            "什么",
        ),
    ),
    (
        "preference_like",
        (
            "like ",
            "love ",
            "prefer ",
            "喜欢",
            "爱",
            "偏爱",
        ),
    ),
)
RETENTION_BASE = {
    "working_memory": 0.44,
    "episodic_memory": 0.56,
    "semantic_memory": 0.74,
    "relational_memory": 0.78,
    "reflective_memory": 0.68,
}
PIN_THRESHOLD = 0.78
IMPORTANCE_BASE = {
    "working_memory": 0.58,
    "episodic_memory": 0.66,
    "semantic_memory": 0.82,
    "relational_memory": 0.84,
    "reflective_memory": 0.76,
    "temporal_kg": 0.7,
}
PERSISTENT_LAYERS = {"semantic_memory", "relational_memory", "reflective_memory"}
USER_SCOPE_BONUS = 0.04
SESSION_SCOPE_BONUS = 0.08
SELF_USER_SCOPE_BONUS = 0.06
OTHER_USER_SCOPE_BONUS = 0.0
GLOBAL_ENTITY_SCOPE_BONUS = 0.02
FACTUAL_ALIAS_KEYS = {
    "identity_name",
    "origin_grew_up",
    "current_residence",
    "occupation",
    "pet_dog",
    "pet_cat",
    "pet_name",
    "preference_like",
}
FACTUAL_MEMORY_LAYERS = {"working_memory", "episodic_memory", "semantic_memory"}


class MemoryService:
    def __init__(
        self,
        *,
        stream_service: StreamService,
        memory_index: MemoryIndex | None = None,
        memory_index_enabled: bool = True,
        policy_registry: PolicyRegistry | None = None,
        runtime_profile: str = "default",
        factual_backend_mode: str = "mem0_shadow",
        native_factual_backend: FactualMemoryBackend | None = None,
        mem0_factual_backend: FactualMemoryBackend | None = None,
    ) -> None:
        self._stream_service = stream_service
        self._memory_index = memory_index or NullMemoryIndex()
        self._memory_index_enabled = memory_index_enabled
        self._policy_registry = policy_registry
        self._runtime_profile = runtime_profile or "default"
        self._factual_backend_mode = (factual_backend_mode or "native").strip()
        self._native_factual_backend = native_factual_backend
        self._mem0_factual_backend = mem0_factual_backend

    def _compiled_policy_set(self) -> Any | None:
        registry = getattr(self, "_policy_registry", None)
        runtime_profile = getattr(self, "_runtime_profile", "default")
        if registry is not None:
            return registry.compile_policy_set(runtime_profile=runtime_profile)
        return get_default_compiled_policy_set(runtime_profile=runtime_profile)

    def _memory_policy(self) -> dict[str, Any]:
        compiled = self._compiled_policy_set()
        return dict(compiled.memory_policy) if compiled else {}

    def _memory_threshold(self, key: str, *, default: float) -> float:
        thresholds = dict(self._memory_policy().get("thresholds") or {})
        try:
            return float(thresholds.get(key, default))
        except (TypeError, ValueError):
            return default

    def _memory_weight_map(
        self,
        weight_key: str,
        fallback: dict[str, float],
    ) -> dict[str, float]:
        weights = dict(self._memory_policy().get("weights") or {})
        payload = weights.get(weight_key)
        if not isinstance(payload, dict):
            return fallback
        merged = dict(fallback)
        for key, value in payload.items():
            try:
                merged[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return merged

    def _semantic_alias_patterns(self) -> list[tuple[str, tuple[str, ...]]]:
        alias_sets = list(self._memory_policy().get("semantic_alias_sets") or [])
        if not alias_sets:
            return list(SEMANTIC_ALIAS_PATTERNS)
        compiled: list[tuple[str, tuple[str, ...]]] = []
        for item in alias_sets:
            if not isinstance(item, dict):
                continue
            alias = str(item.get("alias") or "").strip()
            patterns = tuple(
                str(pattern)
                for pattern in list(item.get("patterns") or [])
                if str(pattern).strip()
            )
            if alias and patterns:
                compiled.append((alias, patterns))
        return compiled or list(SEMANTIC_ALIAS_PATTERNS)

    def _contradiction_patterns(self) -> list[tuple[str, str]]:
        entries = list(self._memory_policy().get("contradiction_patterns") or [])
        if not entries:
            return [
                (r"\b(?:i|i'm|im)\s+(?:still\s+)?live in\b", "location.current_residence"),
                (r"\bmoved to\b", "location.current_residence"),
                (r"\bmy name is\b", "identity.name"),
                (r"\bi work (?:in|as|at)\b", "identity.work"),
                (r"我住在", "location.current_residence"),
                (r"我搬到", "location.current_residence"),
                (r"我叫", "identity.name"),
            ]
        compiled: list[tuple[str, str]] = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            pattern = str(item.get("pattern") or "").strip()
            key = str(item.get("key") or "").strip()
            if pattern and key:
                compiled.append((pattern, key))
        return compiled

    def _low_signal_values(self) -> set[str]:
        values = self._memory_policy().get("low_signal_values")
        if not isinstance(values, list):
            return LOW_SIGNAL_MEMORY_VALUES
        return {str(value) for value in values if str(value).strip()} or LOW_SIGNAL_MEMORY_VALUES

    def _low_signal_entity_prefixes(self) -> tuple[str, ...]:
        values = self._memory_policy().get("low_signal_entity_prefixes")
        if not isinstance(values, list):
            return (
                "topic:",
                "appraisal:",
                "dialogue_act:",
                "attention:",
                "psychological_safety:",
                "dependency_risk:",
                "bid_signal:",
                "turbulence_risk:",
            )
        compiled = tuple(str(value) for value in values if str(value).strip())
        return compiled or (
            "topic:",
            "appraisal:",
            "dialogue_act:",
            "attention:",
            "psychological_safety:",
            "dependency_risk:",
            "bid_signal:",
            "turbulence_risk:",
        )

    def _semantic_anchor_prefixes(self) -> tuple[str, ...]:
        values = self._memory_policy().get("semantic_anchor_prefixes")
        if not isinstance(values, list):
            return ("topic:", "appraisal:", "dialogue_act:")
        compiled = tuple(str(value) for value in values if str(value).strip())
        return compiled or ("topic:", "appraisal:", "dialogue_act:")

    def _relational_guardrail_prefixes(self) -> tuple[str, ...]:
        values = self._memory_policy().get("relational_guardrail_prefixes")
        if not isinstance(values, list):
            return (
                "dependency_risk:",
                "psychological_safety:",
                "bid_signal:",
                "turbulence_risk:",
            )
        compiled = tuple(str(value) for value in values if str(value).strip())
        return compiled or (
            "dependency_risk:",
            "psychological_safety:",
            "bid_signal:",
            "turbulence_risk:",
        )

    def _salient_emotion_tokens(self) -> tuple[str, ...]:
        values = self._memory_policy().get("salient_emotion_tokens")
        if not isinstance(values, list):
            return ("anxious", "alone", "stuck", "worried", "焦虑", "担心", "卡住")
        compiled = tuple(str(value) for value in values if str(value).strip())
        return compiled or ("anxious", "alone", "stuck", "worried", "焦虑", "担心", "卡住")

    def _mem0_shadow_enabled(self) -> bool:
        return self._factual_backend_mode in {"mem0_shadow", "mem0_primary"}

    def factual_shadow_enabled(self) -> bool:
        return self._mem0_shadow_enabled() and self._mem0_factual_backend is not None

    def _prefer_mem0_factual_backend(self) -> bool:
        return self._factual_backend_mode == "mem0_primary"

    def _build_fact_id(
        self,
        *,
        normalized_key: str,
        source_session_id: str,
        source_user_id: str | None,
    ) -> str:
        if source_user_id:
            return f"user:{source_user_id}:{normalized_key}"
        return f"session:{source_session_id}:{normalized_key}"

    def _is_stable_factual_candidate(self, candidate: dict[str, Any]) -> bool:
        layer = str(candidate.get("layer", "episodic_memory"))
        if layer not in FACTUAL_MEMORY_LAYERS:
            return False
        value = str(candidate.get("value", "")).strip()
        if not value or value.casefold().strip() in self._low_signal_values():
            return False
        lowered = value.casefold()
        if any(lowered.startswith(prefix) for prefix in self._semantic_anchor_prefixes()):
            return False
        if any(lowered.startswith(prefix) for prefix in self._relational_guardrail_prefixes()):
            return False

        aliases = set(self._extract_semantic_aliases(value))
        if aliases.intersection(FACTUAL_ALIAS_KEYS):
            return True

        if any(token in lowered for token in self._salient_emotion_tokens()):
            return False

        if self._classify_memory_kind(candidate) != "persistent":
            return False

        if layer == "semantic_memory":
            return True
        return bool(candidate.get("pinned"))

    def _to_factual_candidate(
        self,
        *,
        candidate: dict[str, Any],
        source_session_id: str,
        source_user_id: str | None,
        backend: str,
    ) -> FactualMemoryCandidate:
        normalized_key = str(
            candidate.get("normalized_key")
            or self._normalize_memory_key(str(candidate.get("value", "")))
        )
        source_version_raw = candidate.get("source_version")
        source_version: int | None = None
        if source_version_raw is not None:
            try:
                source_version = int(source_version_raw)
            except (TypeError, ValueError):
                source_version = None
        return FactualMemoryCandidate(
            value=str(candidate.get("value", "")).strip(),
            normalized_key=normalized_key,
            layer=str(candidate.get("layer", "semantic_memory")),
            memory_kind=self._classify_memory_kind(candidate),
            source_session_id=source_session_id,
            source_user_id=source_user_id,
            source_version=source_version,
            occurred_at=str(candidate.get("occurred_at") or "").strip() or None,
            last_seen_at=str(candidate.get("last_seen_at") or "").strip() or None,
            mention_count=max(1, int(candidate.get("mention_count", 1) or 1)),
            confidence_score=self._compute_confidence_score(candidate),
            importance_score=self._compute_importance_score(candidate),
            retention_score=float(candidate.get("retention_score") or 0.0),
            retention_reason=str(candidate.get("retention_reason") or "").strip() or None,
            context_tags={
                str(key): str(value)
                for key, value in dict(candidate.get("context_tags", {})).items()
                if value not in {None, ""}
            },
            pinned=bool(candidate.get("pinned", False)),
            backend=backend,
            fact_id=self._build_fact_id(
                normalized_key=normalized_key,
                source_session_id=source_session_id,
                source_user_id=source_user_id,
            ),
        )

    def _extract_stable_factual_candidates(
        self,
        *,
        state: dict[str, Any],
        source_session_id: str,
        source_user_id: str | None,
        backend: str,
    ) -> list[FactualMemoryCandidate]:
        results: list[FactualMemoryCandidate] = []
        seen: set[str] = set()
        for candidate in self._collect_candidates(state):
            if not self._is_stable_factual_candidate(candidate):
                continue
            fact = self._to_factual_candidate(
                candidate=candidate,
                source_session_id=source_session_id,
                source_user_id=source_user_id,
                backend=backend,
            )
            if fact.fact_id in seen:
                continue
            seen.add(fact.fact_id)
            results.append(fact)
        return results

    def _decorate_factual_backend_result(
        self,
        *,
        fact: FactualMemoryCandidate,
        scope: str,
        current_session_id: str | None,
        current_user_id: str | None,
        vector_score: float,
    ) -> dict[str, Any]:
        return self._decorate_recall_result(
            candidate=fact.to_candidate_dict(),
            scope=scope,
            source_session_id=fact.source_session_id,
            source_user_id=fact.source_user_id,
            symbolic_score=0.0,
            vector_score=vector_score,
            current_session_id=current_session_id,
            current_user_id=current_user_id,
        )

    def _resolve_selected_factual_backend(
        self,
        *,
        native_count: int,
        mem0_count: int,
    ) -> str:
        if mem0_count and native_count:
            return "merged"
        if mem0_count:
            return "mem0"
        if native_count:
            return "native"
        return "none"

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

    def _scope_id(self, *, session_id: str, user_id: str | None = None) -> str:
        if user_id:
            return f"user:{user_id}"
        return f"session:{session_id}"

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    def _compute_recency_score(self, candidate: dict[str, Any]) -> float:
        timestamp = self._parse_timestamp(
            str(candidate.get("occurred_at") or candidate.get("last_seen_at") or "")
        )
        if timestamp is None:
            return 0.3
        now = datetime.now(tz=UTC)
        age_days = max(0.0, (now - timestamp).total_seconds() / 86400.0)
        return round(max(0.15, 1.0 / (1.0 + age_days / 7.0)), 3)

    def _compute_confidence_score(self, candidate: dict[str, Any]) -> float:
        layer = str(candidate.get("layer", "episodic_memory"))
        provenance_base = self._memory_weight_map("provenance_base", PROVENANCE_BASE)
        score = provenance_base.get(layer, 0.7)
        if candidate.get("source_version") is not None:
            score += 0.05
        if candidate.get("occurred_at") or candidate.get("last_seen_at"):
            score += 0.04
        if candidate.get("pinned"):
            score += 0.05
        mention_count = max(1, int(candidate.get("mention_count", 1)))
        score += min(0.08, mention_count * 0.02)
        return round(min(1.0, score), 3)

    def _compute_importance_score(self, candidate: dict[str, Any]) -> float:
        layer = str(candidate.get("layer", "episodic_memory"))
        importance_base = self._memory_weight_map("importance_base", IMPORTANCE_BASE)
        score = importance_base.get(layer, 0.6)
        mention_count = max(1, int(candidate.get("mention_count", 1)))
        score += min(0.12, mention_count * 0.03)
        if candidate.get("pinned"):
            score += 0.08
        retention_score = candidate.get("retention_score")
        if retention_score is not None:
            score += min(0.1, float(retention_score) * 0.12)
        return round(min(1.0, score), 3)

    def _classify_memory_kind(self, candidate: dict[str, Any]) -> str:
        layer = str(candidate.get("layer", "episodic_memory"))
        if layer in PERSISTENT_LAYERS:
            return "persistent"
        mention_count = max(1, int(candidate.get("mention_count", 1)))
        confidence_score = self._compute_confidence_score(candidate)
        if (
            candidate.get("pinned")
            or mention_count
            >= int(self._memory_threshold("persistent_mention_count", default=2))
            or confidence_score
            >= self._memory_threshold("persistent_confidence", default=0.82)
        ):
            return "persistent"
        return "soft"

    def _extract_contradiction_key(self, value: str) -> str | None:
        normalized = value.casefold()
        for pattern, key in self._contradiction_patterns():
            if re.search(pattern, normalized):
                return key
        return None

    def _normalize_memory_key(self, value: str) -> str:
        tokens = self._tokenize(value)
        if not tokens:
            return value.casefold().strip()
        return " ".join(tokens[:12])

    def _extract_semantic_aliases(self, value: str) -> list[str]:
        normalized = value.casefold()
        aliases: list[str] = []
        for alias, patterns in self._semantic_alias_patterns():
            if any(pattern in normalized for pattern in patterns):
                aliases.append(alias)
        return aliases

    def _detect_language_hint(self, value: str) -> str:
        has_chinese = any("\u4e00" <= char <= "\u9fff" for char in value)
        has_latin = bool(re.search(r"[a-zA-Z]", value))
        if has_chinese and has_latin:
            return "mixed"
        if has_chinese:
            return "zh"
        if has_latin:
            return "en"
        return "unknown"

    def _normalize_compare_text(self, value: str) -> str:
        return " ".join(
            token
            for token in re.findall(r"[a-z0-9\u4e00-\u9fff']+", value.casefold())
            if token
        )

    def _looks_like_query_echo(self, *, query: str | None, value: str) -> bool:
        normalized_query = self._normalize_compare_text(query or "")
        normalized_value = self._normalize_compare_text(value)
        if not normalized_query or not normalized_value:
            return False
        if normalized_query == normalized_value:
            return True
        query_tokens = normalized_query.split()
        if len(query_tokens) < 5:
            return False
        return (
            normalized_value.startswith(normalized_query)
            or normalized_query.startswith(normalized_value)
        )

    def _filter_query_echo_candidates(
        self,
        *,
        candidates: list[dict[str, Any]],
        query: str | None,
    ) -> list[dict[str, Any]]:
        if not (query or "").strip():
            return candidates
        return [
            candidate
            for candidate in candidates
            if not self._looks_like_query_echo(
                query=query,
                value=str(candidate.get("value", "")),
            )
        ]

    def _is_low_signal_entity_memory_value(self, value: str) -> bool:
        normalized = value.casefold().strip()
        return any(
            normalized.startswith(prefix)
            for prefix in self._low_signal_entity_prefixes()
        )

    def _prefer_contentful_entity_candidates(
        self,
        *,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        contentful = [
            candidate
            for candidate in candidates
            if not self._is_low_signal_entity_memory_value(
                str(candidate.get("value", ""))
            )
        ]
        return contentful or candidates

    def _build_final_rank_score(
        self,
        *,
        symbolic_score: float,
        vector_score: float,
        recency_score: float,
        importance_score: float,
        confidence_score: float,
        memory_kind: str,
        scope: str,
        source_session_id: str | None,
        current_session_id: str | None = None,
        conscience_weight: float = 0.5,
    ) -> float:
        base = (
            min(1.0, symbolic_score / 4.0) * 0.34
            + vector_score * 0.32
            + recency_score * 0.12
            + importance_score * 0.14
            + confidence_score * 0.08
        )
        if memory_kind == "persistent":
            base += 0.08
        scope_bonuses = self._memory_weight_map(
            "scope_bonuses",
            {
                "user": USER_SCOPE_BONUS,
                "session": SESSION_SCOPE_BONUS,
                "self_user": SELF_USER_SCOPE_BONUS,
                "other_user": OTHER_USER_SCOPE_BONUS,
                "global_entity": GLOBAL_ENTITY_SCOPE_BONUS,
            },
        )
        base += scope_bonuses.get(scope, scope_bonuses.get("user", USER_SCOPE_BONUS))
        if current_session_id and source_session_id and source_session_id == current_session_id:
            base += 0.04
        base += max(-0.05, min(0.08, (conscience_weight - 0.5) * 0.16))
        return round(min(1.2, base), 3)

    def _compute_disclosure_risk(
        self,
        *,
        candidate: dict[str, Any],
        scope: str,
        source_user_id: str | None,
        current_user_id: str | None,
    ) -> float:
        if scope in {"session", "user", "self_user"} or (
            source_user_id and current_user_id and source_user_id == current_user_id
        ):
            return 0.08
        memory_kind = self._classify_memory_kind(candidate)
        layer = str(candidate.get("layer", "episodic_memory"))
        risk = 0.58
        if memory_kind == "soft":
            risk += 0.12
        if layer in {"working_memory", "episodic_memory", "reflective_memory"}:
            risk += 0.08
        if candidate.get("pinned"):
            risk -= 0.05
        return round(max(0.0, min(1.0, risk)), 3)

    def _compute_dramatic_value(
        self,
        *,
        candidate: dict[str, Any],
        scope: str,
    ) -> float:
        importance = self._compute_importance_score(candidate)
        confidence = self._compute_confidence_score(candidate)
        layer = str(candidate.get("layer", "episodic_memory"))
        bonus = 0.0
        if scope == "other_user":
            bonus += 0.22
        if layer in {"relational_memory", "reflective_memory"}:
            bonus += 0.08
        if candidate.get("pinned"):
            bonus += 0.04
        return round(max(0.0, min(1.0, importance * 0.55 + confidence * 0.25 + bonus)), 3)

    def _compute_conscience_weight(
        self,
        *,
        disclosure_risk: float,
        dramatic_value: float,
        scope: str,
    ) -> float:
        if scope in {"session", "user", "self_user"}:
            return 0.82
        return round(max(0.0, min(1.0, 0.48 + dramatic_value * 0.32 - disclosure_risk * 0.18)), 3)

    def _resolve_subject_user_id(
        self,
        *,
        scope: str,
        source_user_id: str | None,
        current_user_id: str | None,
    ) -> str | None:
        if scope == "self_user":
            return current_user_id or source_user_id
        if scope == "other_user":
            return source_user_id
        return source_user_id if scope == "user" else None

    def _compute_attribution_confidence(
        self,
        *,
        candidate: dict[str, Any],
        scope: str,
        source_user_id: str | None,
        subject_user_id: str | None,
        integrity: dict[str, Any] | None,
    ) -> float:
        if scope in {"session", "global_entity"}:
            return 0.98
        if not source_user_id or not subject_user_id:
            return 0.32 if scope == "other_user" else 0.7
        confidence = self._compute_confidence_score(candidate)
        integrity_score = float((integrity or {}).get("score", confidence) or confidence)
        mention_count = max(1, int(candidate.get("mention_count", 1)))
        score = confidence * 0.45 + integrity_score * 0.35 + min(0.2, mention_count * 0.03)
        if scope == "other_user":
            if subject_user_id == source_user_id:
                score += 0.06
            else:
                score -= 0.08
        if candidate.get("source_version") is not None:
            score += 0.03
        if candidate.get("occurred_at") or candidate.get("last_seen_at"):
            score += 0.02
        if subject_user_id != source_user_id:
            score -= 0.12
        return round(max(0.0, min(1.0, score)), 3)

    def _build_subject_hint(
        self,
        *,
        scope: str,
        source_user_id: str | None,
        subject_user_id: str | None,
        current_user_id: str | None,
    ) -> str:
        if scope == "session":
            return "current_session"
        if scope == "self_user":
            return "current_user"
        if scope == "global_entity":
            return "global_entity"
        if scope == "other_user":
            if subject_user_id and current_user_id and subject_user_id == current_user_id:
                return "ambiguous_cross_user"
            if subject_user_id:
                return f"other_user:{subject_user_id}"
            if source_user_id:
                return f"other_user:{source_user_id}"
            return "other_user:unknown"
        if source_user_id:
            return f"user:{source_user_id}"
        return "user:unknown"

    def _build_attribution_guard(
        self,
        *,
        scope: str,
        attribution_confidence: float,
        disclosure_risk: float,
    ) -> str:
        if scope in {"session", "self_user", "global_entity"}:
            return "direct_ok"
        if (
            attribution_confidence
            < self._memory_threshold(
                "attribution_hint_only_confidence",
                default=0.58,
            )
            or disclosure_risk
            >= self._memory_threshold(
                "attribution_hint_only_disclosure_risk",
                default=0.82,
            )
        ):
            return "hint_only"
        if (
            attribution_confidence
            < self._memory_threshold(
                "attribution_attribution_required_confidence",
                default=0.74,
            )
            or disclosure_risk
            >= self._memory_threshold(
                "attribution_attribution_required_disclosure_risk",
                default=0.68,
            )
        ):
            return "attribution_required"
        return "direct_ok"

    def _decorate_recall_result(
        self,
        *,
        candidate: dict[str, Any],
        scope: str,
        source_session_id: str,
        source_user_id: str | None = None,
        subject_user_id: str | None = None,
        symbolic_score: float,
        vector_score: float,
        current_session_id: str | None = None,
        current_user_id: str | None = None,
        integrity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        memory_kind = self._classify_memory_kind(candidate)
        recency_score = self._compute_recency_score(candidate)
        importance_score = self._compute_importance_score(candidate)
        confidence_score = self._compute_confidence_score(candidate)
        disclosure_risk = self._compute_disclosure_risk(
            candidate=candidate,
            scope=scope,
            source_user_id=source_user_id,
            current_user_id=current_user_id,
        )
        resolved_subject_user_id = self._resolve_subject_user_id(
            scope=scope,
            source_user_id=source_user_id,
            current_user_id=current_user_id,
        )
        if subject_user_id:
            resolved_subject_user_id = subject_user_id
        dramatic_value = self._compute_dramatic_value(candidate=candidate, scope=scope)
        conscience_weight = self._compute_conscience_weight(
            disclosure_risk=disclosure_risk,
            dramatic_value=dramatic_value,
            scope=scope,
        )
        attribution_confidence = self._compute_attribution_confidence(
            candidate=candidate,
            scope=scope,
            source_user_id=source_user_id,
            subject_user_id=resolved_subject_user_id,
            integrity=integrity,
        )
        attribution_guard = self._build_attribution_guard(
            scope=scope,
            attribution_confidence=attribution_confidence,
            disclosure_risk=disclosure_risk,
        )
        final_rank_score = self._build_final_rank_score(
            symbolic_score=symbolic_score,
            vector_score=vector_score,
            recency_score=recency_score,
            importance_score=importance_score,
            confidence_score=confidence_score,
            memory_kind=memory_kind,
            scope=scope,
            source_session_id=source_session_id,
            current_session_id=current_session_id,
            conscience_weight=conscience_weight,
        )
        return {
            **candidate,
            "scope": scope,
            "source_session_id": source_session_id,
            "source_user_id": source_user_id,
            "subject_user_id": resolved_subject_user_id,
            "subject_hint": self._build_subject_hint(
                scope=scope,
                source_user_id=source_user_id,
                subject_user_id=resolved_subject_user_id,
                current_user_id=current_user_id,
            ),
            "memory_kind": memory_kind,
            "contradiction_key": self._extract_contradiction_key(
                str(candidate.get("value", ""))
            ),
            "symbolic_score": round(symbolic_score, 3),
            "vector_score": round(vector_score, 3),
            "recency_score": recency_score,
            "importance_score": importance_score,
            "confidence_score": confidence_score,
            "disclosure_risk": disclosure_risk,
            "dramatic_value": dramatic_value,
            "conscience_weight": conscience_weight,
            "attribution_confidence": attribution_confidence,
            "attribution_guard": attribution_guard,
            "final_rank_score": final_rank_score,
            "score": round(max(symbolic_score, final_rank_score), 3),
            "provenance": self._build_provenance(candidate),
            "integrity": integrity or {
                "status": "accepted",
                "score": confidence_score,
                "flags": [],
                "context_tags": dict(candidate.get("context_tags", {})),
            },
        }

    def _merge_recall_candidates(
        self,
        *,
        candidates: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        merged: dict[tuple[str, str, str], dict[str, Any]] = {}
        for candidate in candidates:
            normalized_key = str(
                candidate.get("normalized_key")
                or self._normalize_memory_key(str(candidate.get("value", "")))
            )
            key = (
                normalized_key,
                str(candidate.get("scope", "session")),
                str(candidate.get("source_session_id", "")),
                str(candidate.get("source_user_id", "")),
                str(candidate.get("subject_user_id", "")),
            )
            existing = merged.get(key)
            if existing is None:
                merged[key] = candidate
                continue
            existing["vector_score"] = max(
                float(existing.get("vector_score", 0.0)),
                float(candidate.get("vector_score", 0.0)),
            )
            existing["symbolic_score"] = max(
                float(existing.get("symbolic_score", 0.0)),
                float(candidate.get("symbolic_score", 0.0)),
            )
            existing["importance_score"] = max(
                float(existing.get("importance_score", 0.0)),
                float(candidate.get("importance_score", 0.0)),
            )
            existing["confidence_score"] = max(
                float(existing.get("confidence_score", 0.0)),
                float(candidate.get("confidence_score", 0.0)),
            )
            existing["final_rank_score"] = max(
                float(existing.get("final_rank_score", 0.0)),
                float(candidate.get("final_rank_score", 0.0)),
            )
            existing["score"] = max(
                float(existing.get("score", 0.0)),
                float(candidate.get("score", 0.0)),
            )
            existing["attribution_confidence"] = max(
                float(existing.get("attribution_confidence", 0.0)),
                float(candidate.get("attribution_confidence", 0.0)),
            )
            guard_levels = {"hint_only": 0, "attribution_required": 1, "direct_ok": 2}
            existing_guard = str(existing.get("attribution_guard", "hint_only"))
            candidate_guard = str(candidate.get("attribution_guard", "hint_only"))
            existing["attribution_guard"] = (
                existing_guard
                if guard_levels.get(existing_guard, 0) >= guard_levels.get(candidate_guard, 0)
                else candidate_guard
            )
        ranked = sorted(
            merged.values(),
            key=lambda item: (
                float(item.get("final_rank_score", 0.0)),
                float(item.get("vector_score", 0.0)),
                float(item.get("symbolic_score", 0.0)),
                float(item.get("importance_score", 0.0)),
                int(item.get("mention_count", 0)),
                str(item.get("occurred_at") or item.get("last_seen_at") or ""),
            ),
            reverse=True,
        )
        contradiction_groups: dict[str, list[dict[str, Any]]] = {}
        for item in ranked:
            contradiction_key = str(item.get("contradiction_key") or "").strip()
            if not contradiction_key:
                continue
            contradiction_groups.setdefault(contradiction_key, []).append(item)
        for items in contradiction_groups.values():
            items.sort(
                key=lambda item: (
                    self._parse_timestamp(
                        str(item.get("occurred_at") or item.get("last_seen_at") or "")
                    )
                    or datetime.min.replace(tzinfo=UTC),
                    float(item.get("confidence_score", 0.0)),
                ),
                reverse=True,
            )
            for offset, item in enumerate(items):
                adjustment = 0.08 if offset == 0 else -min(0.12, offset * 0.06)
                item["final_rank_score"] = round(
                    float(item.get("final_rank_score", 0.0)) + adjustment,
                    3,
                )
        ranked.sort(
            key=lambda item: (
                float(item.get("final_rank_score", 0.0)),
                float(item.get("vector_score", 0.0)),
                float(item.get("symbolic_score", 0.0)),
                float(item.get("importance_score", 0.0)),
                int(item.get("mention_count", 0)),
                str(item.get("occurred_at") or item.get("last_seen_at") or ""),
            ),
            reverse=True,
        )
        return ranked[: max(1, limit)]

    def _candidate_record_id(
        self,
        *,
        scope_id: str,
        session_id: str,
        layer: str,
        normalized_key: str,
    ) -> str:
        return f"{scope_id}:{session_id}:{layer}:{normalized_key}"

    def _candidate_to_index_record(
        self,
        *,
        scope_id: str,
        user_id: str | None,
        session_id: str,
        candidate: dict[str, Any],
    ) -> MemoryIndexRecord:
        value = str(candidate.get("value", "")).strip()
        normalized_key = self._normalize_memory_key(value)
        semantic_aliases = self._extract_semantic_aliases(value)
        factual_candidate = self._is_stable_factual_candidate(
            {
                **candidate,
                "value": value,
                "normalized_key": normalized_key,
            }
        )
        return MemoryIndexRecord(
            record_id=self._candidate_record_id(
                scope_id=scope_id,
                session_id=session_id,
                layer=str(candidate.get("layer", "episodic_memory")),
                normalized_key=normalized_key,
            ),
            scope_id=scope_id,
            user_id=user_id,
            session_id=session_id,
            layer=str(candidate.get("layer", "episodic_memory")),
            memory_kind=self._classify_memory_kind(candidate),
            text=value,
            normalized_key=normalized_key,
            occurred_at=candidate.get("occurred_at"),
            last_seen_at=candidate.get("last_seen_at"),
            mention_count=max(1, int(candidate.get("mention_count", 1))),
            importance_score=self._compute_importance_score(candidate),
            confidence_score=self._compute_confidence_score(candidate),
            retention_score=float(candidate.get("retention_score") or 0.0),
            metadata={
                "context_tags": dict(candidate.get("context_tags", {})),
                "pinned": bool(candidate.get("pinned", False)),
                "retention_reason": candidate.get("retention_reason"),
                "language_hint": self._detect_language_hint(value),
                "semantic_aliases": semantic_aliases,
                "source_version": candidate.get("source_version"),
                "factual_candidate": factual_candidate,
                "fact_id": (
                    self._build_fact_id(
                        normalized_key=normalized_key,
                        source_session_id=session_id,
                        source_user_id=user_id,
                    )
                    if factual_candidate
                    else None
                ),
            },
        )

    def _event_to_multimodal_record(
        self,
        *,
        scope_id: str,
        user_id: str | None,
        session_id: str,
        event: Any,
    ) -> MemoryIndexRecord | None:
        payload = getattr(event, "payload", {})
        attachments = list(payload.get("attachments") or [])
        if not attachments:
            return None
        media = [
            MemoryMediaAttachment(
                type=str(attachment.get("type") or ""),
                url=str(attachment.get("url") or ""),
                mime_type=str(attachment.get("mime_type") or ""),
                filename=str(attachment.get("filename") or ""),
                metadata=dict(attachment.get("metadata") or {}),
            )
            for attachment in attachments
            if attachment.get("url")
        ]
        if not media:
            return None
        text = str(payload.get("content") or payload.get("text") or "").strip()
        descriptors = [
            " ".join(
                part
                for part in [
                    attachment.filename,
                    attachment.mime_type,
                    attachment.metadata.get("caption", ""),
                    attachment.metadata.get("summary", ""),
                ]
                if part
            ).strip()
            for attachment in media
        ]
        combined_text = " ".join(part for part in [text, *descriptors] if part).strip()
        normalized_key = self._normalize_memory_key(combined_text or session_id)
        occurred_at = getattr(event, "occurred_at", None)
        return MemoryIndexRecord(
            record_id=self._candidate_record_id(
                scope_id=scope_id,
                session_id=session_id,
                layer="multimodal_attachment",
                normalized_key=normalized_key,
            ),
            scope_id=scope_id,
            user_id=user_id,
            session_id=session_id,
            layer="multimodal_attachment",
            memory_kind="soft",
            text=combined_text or "multimodal attachment",
            normalized_key=normalized_key,
            occurred_at=occurred_at.isoformat() if occurred_at is not None else None,
            last_seen_at=occurred_at.isoformat() if occurred_at is not None else None,
            mention_count=1,
            importance_score=0.62,
            confidence_score=0.7,
            retention_score=0.45,
            metadata={"event_type": getattr(event, "event_type", "")},
            attachments=media,
        )

    async def _build_scope_index_records(
        self,
        *,
        session_ids: list[str],
        scope_id: str,
        user_id: str | None,
        compact: bool = False,
    ) -> tuple[list[MemoryIndexRecord], list[MemoryIndexRecord]]:
        sources = [(user_id, session_id) for session_id in session_ids]
        return await self._build_scope_index_records_for_sources(
            sources=sources,
            scope_id=scope_id,
            compact=compact,
        )

    async def _list_user_session_sources(self) -> list[tuple[str | None, str]]:
        stream_ids = await self._stream_service.list_stream_ids()
        user_stream_ids = sorted(
            stream_id for stream_id in stream_ids if stream_id.startswith("user:")
        )
        sources: list[tuple[str | None, str]] = []
        for user_stream_id in user_stream_ids:
            user_id = user_stream_id.split(":", 1)[1]
            try:
                projection = await self._stream_service.project_stream(
                    stream_id=user_stream_id,
                    projector_name="user-index",
                    projector_version="v1",
                )
            except Exception:
                continue
            for session_id in projection.get("state", {}).get("session_ids") or []:
                sources.append((user_id, str(session_id)))
        return sources

    async def _build_scope_index_records_for_sources(
        self,
        *,
        sources: list[tuple[str | None, str]],
        scope_id: str,
        compact: bool = False,
    ) -> tuple[list[MemoryIndexRecord], list[MemoryIndexRecord]]:
        text_records: list[MemoryIndexRecord] = []
        multimodal_records: list[MemoryIndexRecord] = []
        for source_user_id, session_id in sources:
            try:
                projection = await self.get_session_memory(session_id=session_id)
            except Exception:
                continue
            state = projection.get("state", {})
            candidates = self._collect_candidates(state)
            for candidate in candidates:
                if not candidate.get("value"):
                    continue
                record = self._candidate_to_index_record(
                    scope_id=scope_id,
                    user_id=source_user_id,
                    session_id=session_id,
                    candidate=candidate,
                )
                if compact and not self._should_keep_compact_index_record(record):
                    continue
                text_records.append(record)
            try:
                stream_events = await self._stream_service.read_stream(stream_id=session_id)
            except Exception:
                stream_events = []
            for event in stream_events:
                record = self._event_to_multimodal_record(
                    scope_id=scope_id,
                    user_id=source_user_id,
                    session_id=session_id,
                    event=event,
                )
                if record is not None:
                    multimodal_records.append(record)
        deduped_text = {record.record_id: record for record in text_records}
        deduped_multi = {record.record_id: record for record in multimodal_records}
        return list(deduped_text.values()), list(deduped_multi.values())

    def _should_keep_compact_index_record(self, record: MemoryIndexRecord) -> bool:
        if record.memory_kind == "persistent":
            return True
        if record.layer in {"semantic_memory", "relational_memory"}:
            return True
        if bool(record.metadata.get("pinned")):
            return True
        if record.importance_score >= 0.72:
            return True
        if record.confidence_score >= 0.8:
            return True
        return False

    async def refresh_memory_scope(
        self,
        *,
        session_id: str,
        user_id: str | None = None,
    ) -> None:
        if not self._memory_index_enabled:
            return
        scope_id = self._scope_id(session_id=session_id, user_id=user_id)
        if user_id:
            from relationship_os.application.projectors.user_profile import build_user_profile

            profile = await build_user_profile(
                user_id=user_id,
                stream_service=self._stream_service,
            )
            session_ids = list(profile.get("session_ids") or [])
            if session_id not in session_ids:
                session_ids.append(session_id)
        else:
            session_ids = [session_id]
        text_records, multimodal_records = await self._build_scope_index_records(
            session_ids=session_ids,
            scope_id=scope_id,
            user_id=user_id,
            compact=False,
        )
        await self._memory_index.rebuild_user(
            scope_id=scope_id,
            text_records=text_records,
            multimodal_records=multimodal_records,
        )
        mem0_backend = self._mem0_factual_backend
        if self._mem0_shadow_enabled() and mem0_backend is not None:
            try:
                session_facts: dict[str, list[FactualMemoryCandidate]] = {}
                for candidate_session_id in session_ids:
                    try:
                        projection = await self.get_session_memory(
                            session_id=candidate_session_id
                        )
                    except Exception:
                        continue
                    session_facts[candidate_session_id] = (
                        self._extract_stable_factual_candidates(
                            state=dict(projection.get("state") or {}),
                            source_session_id=candidate_session_id,
                            source_user_id=user_id,
                            backend="mem0",
                        )
                    )
                if user_id and session_facts:
                    await mem0_backend.refresh_user_facts(
                        user_id=user_id,
                        session_facts=session_facts,
                    )
                elif session_facts.get(session_id):
                    await mem0_backend.upsert_session_facts(
                        session_id=session_id,
                        user_id=user_id,
                        entity_id=None,
                        compact=False,
                        facts=session_facts[session_id],
                    )
            except Exception:
                logger.warning(
                    "mem0_shadow_refresh_failed session_id=%s user_id=%s",
                    session_id,
                    user_id,
                    exc_info=True,
                )

    async def upsert_memory_scope(
        self,
        *,
        session_id: str,
        user_id: str | None = None,
        entity_id: str | None = None,
        compact: bool = False,
        sync_factual_shadow: bool = True,
    ) -> None:
        if not self._memory_index_enabled:
            return
        started = perf_counter()
        scope_id = self._scope_id(session_id=session_id, user_id=user_id)
        text_records, multimodal_records = await self._build_scope_index_records(
            session_ids=[session_id],
            scope_id=scope_id,
            user_id=user_id,
            compact=compact,
        )
        await self._memory_index.write_many(
            scope_id=scope_id,
            text_records=text_records,
            multimodal_records=multimodal_records,
        )
        if entity_id:
            entity_text_records, entity_multimodal_records = (
                await self._build_scope_index_records_for_sources(
                    sources=[(user_id, session_id)],
                    scope_id=f"entity:{entity_id}",
                    compact=compact,
                )
            )
            await self._memory_index.write_many(
                scope_id=f"entity:{entity_id}",
                text_records=entity_text_records,
                multimodal_records=entity_multimodal_records,
            )
        mem0_shadow_elapsed_ms = 0.0
        mem0_backend = self._mem0_factual_backend
        if sync_factual_shadow and self._mem0_shadow_enabled() and mem0_backend is not None:
            mem0_started = perf_counter()
            try:
                try:
                    projection = await self.get_session_memory(session_id=session_id)
                except Exception:
                    projection = {}
                factual_candidates = self._extract_stable_factual_candidates(
                    state=dict(projection.get("state") or {}),
                    source_session_id=session_id,
                    source_user_id=user_id,
                    backend="mem0",
                )
                if factual_candidates:
                    await mem0_backend.upsert_session_facts(
                        session_id=session_id,
                        user_id=user_id,
                        entity_id=entity_id,
                        compact=compact,
                        facts=factual_candidates,
                    )
            except Exception:
                logger.warning(
                    "mem0_shadow_upsert_failed session_id=%s user_id=%s",
                    session_id,
                    user_id,
                    exc_info=True,
                )
            mem0_shadow_elapsed_ms = round((perf_counter() - mem0_started) * 1000.0, 1)
        total_elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
        logger.info(
            "memory_scope_upsert_timing session_id=%s user_id=%s compact=%s "
            "sync_factual_shadow=%s text_records=%s multimodal_records=%s total_ms=%.1f "
            "mem0_shadow_ms=%.1f",
            session_id,
            user_id,
            compact,
            sync_factual_shadow,
            len(text_records),
            len(multimodal_records),
            total_elapsed_ms,
            mem0_shadow_elapsed_ms,
        )

    async def sync_factual_shadow_for_session(
        self,
        *,
        session_id: str,
        user_id: str | None = None,
        entity_id: str | None = None,
        compact: bool = False,
    ) -> dict[str, Any]:
        started = perf_counter()
        if not self.factual_shadow_enabled():
            return {
                "status": "disabled",
                "fact_count": 0,
                "elapsed_ms": round((perf_counter() - started) * 1000.0, 1),
            }
        mem0_backend = self._mem0_factual_backend
        assert mem0_backend is not None
        try:
            try:
                projection = await self.get_session_memory(session_id=session_id)
            except Exception:
                projection = {}
            factual_candidates = self._extract_stable_factual_candidates(
                state=dict(projection.get("state") or {}),
                source_session_id=session_id,
                source_user_id=user_id,
                backend="mem0",
            )
            if factual_candidates:
                await mem0_backend.upsert_session_facts(
                    session_id=session_id,
                    user_id=user_id,
                    entity_id=entity_id,
                    compact=compact,
                    facts=factual_candidates,
                )
            elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
            logger.info(
                "mem0_shadow_session_sync session_id=%s user_id=%s compact=%s "
                "fact_count=%s elapsed_ms=%.1f",
                session_id,
                user_id,
                compact,
                len(factual_candidates),
                elapsed_ms,
            )
            return {
                "status": "ok",
                "fact_count": len(factual_candidates),
                "elapsed_ms": elapsed_ms,
            }
        except Exception as exc:
            elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
            logger.warning(
                "mem0_shadow_session_sync_failed session_id=%s user_id=%s elapsed_ms=%.1f",
                session_id,
                user_id,
                elapsed_ms,
                exc_info=True,
            )
            return {
                "status": "failed",
                "fact_count": 0,
                "elapsed_ms": elapsed_ms,
                "error": str(exc),
            }

    async def refresh_entity_scope(self, *, entity_id: str) -> None:
        if not self._memory_index_enabled:
            return
        sources = await self._list_user_session_sources()
        text_records, multimodal_records = await self._build_scope_index_records_for_sources(
            sources=sources,
            scope_id=f"entity:{entity_id}",
        )
        await self._memory_index.rebuild_user(
            scope_id=f"entity:{entity_id}",
            text_records=text_records,
            multimodal_records=multimodal_records,
        )

    async def recall_session_memory(
        self,
        *,
        session_id: str,
        query: str | None,
        limit: int,
        context_filters: dict[str, str] | None = None,
        include_filtered: bool = False,
        attachments: list[MemoryMediaAttachment] | None = None,
        enable_vector_search: bool = True,
        prefer_fast: bool = False,
        include_factual_shadow: bool = True,
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

        filtered_candidates.sort(
            key=lambda item: (
                float(item["score"]),
                float(item["integrity"]["score"]),
                int(item.get("source_version", 0)),
            ),
            reverse=True,
        )

        decorated_results = [
            self._decorate_recall_result(
                candidate={
                    **candidate_payload,
                    "normalized_key": self._normalize_memory_key(
                        str(candidate_payload.get("value", ""))
                    ),
                },
                scope="session",
                source_session_id=session_id,
                symbolic_score=float(candidate_payload.get("score", 0.0)),
                vector_score=0.0,
                current_session_id=session_id,
                current_user_id=None,
                integrity=dict(candidate_payload.get("integrity", {})),
            )
            for candidate_payload in accepted_candidates
        ]

        vector_hits: list[MemoryIndexHit] = []
        native_factual_results: list[dict[str, Any]] = []
        mem0_factual_results: list[dict[str, Any]] = []
        mem0_fallback_reason: str | None = None
        if (
            self._memory_index_enabled
            and enable_vector_search
            and ((query or "").strip() or attachments)
        ):
            if not prefer_fast:
                await self.refresh_memory_scope(session_id=session_id)
            if attachments:
                vector_hits = await self._memory_index.search(
                    scope_id=self._scope_id(session_id=session_id),
                    query=query or "",
                    limit=max(limit * 3, 8),
                    attachments=attachments,
                    use_reranker=not prefer_fast,
                )
                native_factual_results = [
                    self._decorate_recall_result(
                        candidate={
                            "layer": hit.record.layer,
                            "value": hit.record.text,
                            "source_version": hit.record.metadata.get("source_version"),
                            "occurred_at": hit.record.occurred_at,
                            "last_seen_at": hit.record.last_seen_at,
                            "mention_count": hit.record.mention_count,
                            "context_tags": dict(hit.record.metadata.get("context_tags", {})),
                            "pinned": bool(hit.record.metadata.get("pinned", False)),
                            "retention_score": hit.record.retention_score,
                            "retention_reason": hit.record.metadata.get("retention_reason"),
                            "normalized_key": hit.record.normalized_key,
                        },
                        scope="session",
                        source_session_id=hit.record.session_id or session_id,
                        source_user_id=hit.record.user_id,
                        symbolic_score=0.0,
                        vector_score=hit.vector_score,
                        current_session_id=session_id,
                        current_user_id=None,
                    )
                    for hit in vector_hits
                ]
            else:
                mem0_enabled = (
                    include_factual_shadow
                    and self._mem0_shadow_enabled()
                    and self._mem0_factual_backend is not None
                )
                native_enabled = self._native_factual_backend is not None
                if mem0_enabled and self._prefer_mem0_factual_backend():
                    try:
                        mem0_facts = await self._mem0_factual_backend.recall_session_facts(
                            session_id=session_id,
                            query=query,
                            limit=limit,
                            prefer_fast=prefer_fast,
                        )
                        mem0_factual_results = [
                            self._decorate_factual_backend_result(
                                fact=fact,
                                scope="session",
                                current_session_id=session_id,
                                current_user_id=None,
                                vector_score=max(
                                    0.5,
                                    float(fact.confidence_score) or 0.0,
                                ),
                            )
                            for fact in mem0_facts
                        ]
                    except Exception as exc:
                        mem0_fallback_reason = f"{type(exc).__name__}:{exc}"
                    if not mem0_factual_results and native_enabled:
                        native_facts = await self._native_factual_backend.recall_session_facts(
                            session_id=session_id,
                            query=query,
                            limit=limit,
                            prefer_fast=prefer_fast,
                        )
                        native_factual_results = [
                            self._decorate_factual_backend_result(
                                fact=fact,
                                scope="session",
                                current_session_id=session_id,
                                current_user_id=None,
                                vector_score=max(
                                    0.52,
                                    float(fact.confidence_score) or 0.0,
                                ),
                            )
                            for fact in native_facts
                        ]
                else:
                    if native_enabled:
                        native_facts = await self._native_factual_backend.recall_session_facts(
                            session_id=session_id,
                            query=query,
                            limit=limit,
                            prefer_fast=prefer_fast,
                        )
                        native_factual_results = [
                            self._decorate_factual_backend_result(
                                fact=fact,
                                scope="session",
                                current_session_id=session_id,
                                current_user_id=None,
                                vector_score=max(
                                    0.52,
                                    float(fact.confidence_score) or 0.0,
                                ),
                            )
                            for fact in native_facts
                        ]
                    if mem0_enabled:
                        try:
                            mem0_facts = await self._mem0_factual_backend.recall_session_facts(
                                session_id=session_id,
                                query=query,
                                limit=limit,
                                prefer_fast=prefer_fast,
                            )
                            mem0_factual_results = [
                                self._decorate_factual_backend_result(
                                    fact=fact,
                                    scope="session",
                                    current_session_id=session_id,
                                    current_user_id=None,
                                    vector_score=max(
                                        0.5,
                                        float(fact.confidence_score) or 0.0,
                                    ),
                                )
                                for fact in mem0_facts
                            ]
                        except Exception as exc:
                            mem0_fallback_reason = f"{type(exc).__name__}:{exc}"

        decorated_results = self._filter_query_echo_candidates(
            candidates=decorated_results,
            query=query,
        )
        native_factual_results = self._filter_query_echo_candidates(
            candidates=native_factual_results,
            query=query,
        )
        mem0_factual_results = self._filter_query_echo_candidates(
            candidates=mem0_factual_results,
            query=query,
        )
        results = self._merge_recall_candidates(
            candidates=[*decorated_results, *native_factual_results, *mem0_factual_results],
            limit=limit,
        )
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
                "vector_hit_count": max(len(vector_hits), len(native_factual_results)),
            },
            "factual_backend_mode": self._factual_backend_mode,
            "native_factual_hit_count": len(native_factual_results),
            "mem0_factual_hit_count": len(mem0_factual_results),
            "selected_factual_backend": self._resolve_selected_factual_backend(
                native_count=len(native_factual_results),
                mem0_count=len(mem0_factual_results),
            ),
            "mem0_fallback_reason": mem0_fallback_reason,
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

        provenance_base = self._memory_weight_map("provenance_base", PROVENANCE_BASE)
        provenance_score = provenance_base.get(layer, 0.7)
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

        accepted = (
            total_score
            >= self._memory_threshold("integrity_acceptance", default=0.62)
            and not blocking_mismatch
        )
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
        layer_weights = self._memory_weight_map("layer_weights", LAYER_WEIGHTS)
        base_weight = layer_weights.get(layer, 1.0)
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
        surface_tokens = [
            token
            for token in re.findall(r"[\w\u4e00-\u9fff:.-]+", value.lower())
            if token
        ]
        semantic_aliases = self._extract_semantic_aliases(value)
        merged = [*surface_tokens, *semantic_aliases]
        return list(dict.fromkeys(merged))

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
        if content_candidate in self._low_signal_values():
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
            "policy_version": (
                self._compiled_policy_set().version if self._compiled_policy_set() else "v1"
            ),
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
        retention_base = self._memory_weight_map("retention_base", RETENTION_BASE)
        score = retention_base.get(layer, 0.55)
        signals: list[str] = []
        reason = "transient_context"

        topic = getattr(context_frame, "topic", None)
        appraisal = getattr(context_frame, "appraisal", None)
        bid_signal = getattr(context_frame, "bid_signal", None)
        dependency_risk = getattr(relationship_state, "dependency_risk", None)
        rupture_detected = bool(getattr(repair_plan, "rupture_detected", False))

        if layer == "semantic_memory" and any(
            normalized.startswith(prefix) for prefix in self._semantic_anchor_prefixes()
        ):
            score += 0.12
            signals.append("semantic_anchor")
            reason = "semantic_anchor"
        if layer == "relational_memory" and any(
            normalized.startswith(prefix) for prefix in self._relational_guardrail_prefixes()
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
        if any(token in normalized for token in self._salient_emotion_tokens()):
            score += 0.1
            signals.append("emotional_salience")
            reason = "salient_emotional_context"

        retention_score = round(max(0.0, min(1.0, score)), 3)
        return {
            "value": cleaned,
            "pinned": retention_score
            >= self._memory_threshold("pin", default=PIN_THRESHOLD),
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

    async def recall_user_memory(
        self,
        *,
        user_id: str,
        query: str | None,
        limit: int = 10,
        current_session_id: str | None = None,
        attachments: list[MemoryMediaAttachment] | None = None,
        enable_vector_search: bool = True,
        prefer_fast: bool = False,
        include_factual_shadow: bool = True,
    ) -> dict[str, Any]:
        """Recall cross-session memory for a user.

        Loads all linked sessions, merges symbolic + vector recall, and returns
        richer ranking metadata for debugging and runtime use.
        """
        from relationship_os.application.projectors.user_profile import build_user_profile

        profile = await build_user_profile(
            user_id=user_id, stream_service=self._stream_service
        )
        session_ids: list[str] = profile.get("session_ids") or []
        if not session_ids:
            return {
                "results": [],
                "matched_nodes": [],
                "bridges": [],
                "graph_summary": {},
                "integrity_summary": {},
                "user_id": user_id,
                "session_count": 0,
            }

        normalized_query = (query or "").strip().lower()
        query_tokens = self._tokenize(normalized_query)

        all_candidates: list[dict[str, Any]] = []
        all_matched_nodes: list[dict[str, Any]] = []
        all_bridges: list[dict[str, Any]] = []

        for session_id in session_ids:
            try:
                projection = await self.get_session_memory(session_id=session_id)
                kg_projection = await self.get_session_temporal_kg(session_id=session_id)
            except Exception:
                continue

            state = projection["state"]
            kg_state = kg_projection["state"]

            candidates = self._collect_candidates(state)
            tagged = [
                {
                    **candidate,
                    "_user_level": True,
                    "source_user_id": user_id,
                    "source_session_id": session_id,
                    "normalized_key": self._normalize_memory_key(
                        str(candidate.get("value", ""))
                    ),
                }
                for candidate in candidates
            ]
            all_candidates.extend(tagged)

            matched_nodes, bridges = self._discover_graph_bridges(
                query=normalized_query,
                kg_state=kg_state,
                query_tokens=query_tokens,
            )
            all_matched_nodes.extend(matched_nodes)
            all_bridges.extend(bridges)

        # Score and rank
        matched_labels: set[str] = {
            str(n.get("label", "")).lower() for n in all_matched_nodes
        }
        bridge_lbls: set[str] = {
            str(b.get("source_label", "")).lower() for b in all_bridges
        } | {str(b.get("target_label", "")).lower() for b in all_bridges}
        all_candidates = self._filter_query_echo_candidates(
            candidates=all_candidates,
            query=query,
        )
        scored_results: list[dict[str, Any]] = []
        for candidate in all_candidates:
            score = self._score_candidate(
                query=normalized_query,
                query_tokens=query_tokens,
                candidate=candidate,
                matched_node_labels=matched_labels,
                bridge_labels=bridge_lbls,
            )
            integrity = self._evaluate_integrity(
                candidate=candidate,
                retrieval_score=score,
                context_filters={},
                matched_node_labels=matched_labels,
                bridge_labels=bridge_lbls,
            )
            if integrity["status"] != "accepted":
                continue
            scored_results.append(
                self._decorate_recall_result(
                    candidate=candidate,
                    scope="self_user",
                    source_session_id=str(candidate.get("source_session_id") or ""),
                    source_user_id=str(candidate.get("source_user_id") or user_id),
                    symbolic_score=score,
                    vector_score=0.0,
                    current_session_id=current_session_id,
                    current_user_id=user_id,
                    integrity=integrity,
                )
            )

        vector_hits: list[MemoryIndexHit] = []
        native_factual_results: list[dict[str, Any]] = []
        mem0_factual_results: list[dict[str, Any]] = []
        mem0_fallback_reason: str | None = None
        if (
            self._memory_index_enabled
            and enable_vector_search
            and ((query or "").strip() or attachments)
        ):
            scope_id = self._scope_id(
                session_id=current_session_id or session_ids[-1],
                user_id=user_id,
            )
            text_records, multimodal_records = await self._build_scope_index_records(
                session_ids=session_ids,
                scope_id=scope_id,
                user_id=user_id,
            )
            await self._memory_index.rebuild_user(
                scope_id=scope_id,
                text_records=text_records,
                multimodal_records=multimodal_records,
            )
            if attachments:
                vector_hits = await self._memory_index.search(
                    scope_id=scope_id,
                    query=query or "",
                    limit=max(limit * 3, 10),
                    attachments=attachments,
                    use_reranker=not prefer_fast,
                )
                native_factual_results = [
                    self._decorate_recall_result(
                        candidate={
                            "layer": hit.record.layer,
                            "value": hit.record.text,
                            "source_version": hit.record.metadata.get("source_version"),
                            "occurred_at": hit.record.occurred_at,
                            "last_seen_at": hit.record.last_seen_at,
                            "mention_count": hit.record.mention_count,
                            "context_tags": dict(hit.record.metadata.get("context_tags", {})),
                            "pinned": bool(hit.record.metadata.get("pinned", False)),
                            "retention_score": hit.record.retention_score,
                            "retention_reason": hit.record.metadata.get("retention_reason"),
                            "normalized_key": hit.record.normalized_key,
                        },
                        scope="self_user",
                        source_session_id=hit.record.session_id or current_session_id or "",
                        source_user_id=hit.record.user_id or user_id,
                        symbolic_score=0.0,
                        vector_score=hit.vector_score,
                        current_session_id=current_session_id,
                        current_user_id=user_id,
                    )
                    for hit in vector_hits
                ]
            else:
                mem0_enabled = (
                    include_factual_shadow
                    and self._mem0_shadow_enabled()
                    and self._mem0_factual_backend is not None
                )
                native_enabled = self._native_factual_backend is not None
                if mem0_enabled and self._prefer_mem0_factual_backend():
                    try:
                        mem0_facts = await self._mem0_factual_backend.recall_user_facts(
                            user_id=user_id,
                            current_session_id=current_session_id,
                            query=query,
                            limit=limit,
                            prefer_fast=prefer_fast,
                        )
                        mem0_factual_results = [
                            self._decorate_factual_backend_result(
                                fact=fact,
                                scope="self_user",
                                current_session_id=current_session_id,
                                current_user_id=user_id,
                                vector_score=max(
                                    0.5,
                                    float(fact.confidence_score) or 0.0,
                                ),
                            )
                            for fact in mem0_facts
                        ]
                    except Exception as exc:
                        mem0_fallback_reason = f"{type(exc).__name__}:{exc}"
                    if not mem0_factual_results and native_enabled:
                        native_facts = await self._native_factual_backend.recall_user_facts(
                            user_id=user_id,
                            current_session_id=current_session_id,
                            query=query,
                            limit=limit,
                            prefer_fast=prefer_fast,
                        )
                        native_factual_results = [
                            self._decorate_factual_backend_result(
                                fact=fact,
                                scope="self_user",
                                current_session_id=current_session_id,
                                current_user_id=user_id,
                                vector_score=max(
                                    0.52,
                                    float(fact.confidence_score) or 0.0,
                                ),
                            )
                            for fact in native_facts
                        ]
                else:
                    if native_enabled:
                        native_facts = await self._native_factual_backend.recall_user_facts(
                            user_id=user_id,
                            current_session_id=current_session_id,
                            query=query,
                            limit=limit,
                            prefer_fast=prefer_fast,
                        )
                        native_factual_results = [
                            self._decorate_factual_backend_result(
                                fact=fact,
                                scope="self_user",
                                current_session_id=current_session_id,
                                current_user_id=user_id,
                                vector_score=max(
                                    0.52,
                                    float(fact.confidence_score) or 0.0,
                                ),
                            )
                            for fact in native_facts
                        ]
                    if mem0_enabled:
                        try:
                            mem0_facts = await self._mem0_factual_backend.recall_user_facts(
                                user_id=user_id,
                                current_session_id=current_session_id,
                                query=query,
                                limit=limit,
                                prefer_fast=prefer_fast,
                            )
                            mem0_factual_results = [
                                self._decorate_factual_backend_result(
                                    fact=fact,
                                    scope="self_user",
                                    current_session_id=current_session_id,
                                    current_user_id=user_id,
                                    vector_score=max(
                                        0.5,
                                        float(fact.confidence_score) or 0.0,
                                    ),
                                )
                                for fact in mem0_facts
                            ]
                        except Exception as exc:
                            mem0_fallback_reason = f"{type(exc).__name__}:{exc}"

        native_factual_results = self._filter_query_echo_candidates(
            candidates=native_factual_results,
            query=query,
        )
        mem0_factual_results = self._filter_query_echo_candidates(
            candidates=mem0_factual_results,
            query=query,
        )
        results = self._merge_recall_candidates(
            candidates=[*scored_results, *native_factual_results, *mem0_factual_results],
            limit=limit,
        )

        return {
            "results": results,
            "matched_nodes": all_matched_nodes[:6],
            "bridges": all_bridges[:6],
            "graph_summary": {
                "user_id": user_id,
                "session_count": len(session_ids),
                "matched_node_count": len(all_matched_nodes[:6]),
                "bridge_count": len(all_bridges[:6]),
            },
            "integrity_summary": {
                "total_candidates": len(all_candidates),
                "symbolic_hit_count": len(scored_results),
                "vector_hit_count": max(len(vector_hits), len(native_factual_results)),
            },
            "user_id": user_id,
            "session_count": len(session_ids),
            "factual_backend_mode": self._factual_backend_mode,
            "native_factual_hit_count": len(native_factual_results),
            "mem0_factual_hit_count": len(mem0_factual_results),
            "selected_factual_backend": self._resolve_selected_factual_backend(
                native_count=len(native_factual_results),
                mem0_count=len(mem0_factual_results),
            ),
            "mem0_fallback_reason": mem0_fallback_reason,
        }

    async def recall_entity_memory(
        self,
        *,
        entity_id: str,
        current_user_id: str | None,
        current_session_id: str | None,
        query: str | None,
        limit: int = 10,
        attachments: list[MemoryMediaAttachment] | None = None,
        enable_vector_search: bool = True,
        prefer_fast: bool = False,
    ) -> dict[str, Any]:
        sources = await self._list_user_session_sources()
        if not sources:
            return {
                "results": [],
                "entity_id": entity_id,
                "source_user_count": 0,
                "session_count": 0,
            }

        normalized_query = (query or "").strip().lower()
        query_tokens = self._tokenize(normalized_query)
        all_candidates: list[dict[str, Any]] = []
        for source_user_id, session_id in sources:
            try:
                projection = await self.get_session_memory(session_id=session_id)
            except Exception:
                continue
            for candidate in self._collect_candidates(projection["state"]):
                all_candidates.append(
                    {
                        **candidate,
                        "source_user_id": source_user_id,
                        "source_session_id": session_id,
                        "normalized_key": self._normalize_memory_key(
                            str(candidate.get("value", ""))
                        ),
                    }
                )

        all_candidates = self._filter_query_echo_candidates(
            candidates=all_candidates,
            query=query,
        )
        if query_tokens:
            all_candidates = self._prefer_contentful_entity_candidates(
                candidates=all_candidates,
            )
        symbolic_results: list[dict[str, Any]] = []
        for candidate in all_candidates:
            score = self._score_candidate(
                query=normalized_query,
                query_tokens=query_tokens,
                candidate=candidate,
                matched_node_labels=set(),
                bridge_labels=set(),
            )
            integrity = self._evaluate_integrity(
                candidate=candidate,
                retrieval_score=score,
                context_filters={},
                matched_node_labels=set(),
                bridge_labels=set(),
            )
            if integrity["status"] != "accepted":
                continue
            source_user_id = str(candidate.get("source_user_id") or "")
            scope = (
                "self_user"
                if current_user_id and source_user_id == current_user_id
                else "other_user"
            )
            symbolic_results.append(
                self._decorate_recall_result(
                    candidate=candidate,
                    scope=scope,
                    source_session_id=str(candidate.get("source_session_id") or ""),
                    source_user_id=source_user_id or None,
                    symbolic_score=score,
                    vector_score=0.0,
                    current_session_id=current_session_id,
                    current_user_id=current_user_id,
                    integrity=integrity,
                )
            )

        vector_hits: list[MemoryIndexHit] = []
        if (
            self._memory_index_enabled
            and enable_vector_search
            and ((query or "").strip() or attachments)
        ):
            if not prefer_fast:
                await self.refresh_entity_scope(entity_id=entity_id)
            vector_hits = await self._memory_index.search(
                scope_id=f"entity:{entity_id}",
                query=query or "",
                limit=max(limit * 4, 12),
                attachments=attachments,
                use_reranker=not prefer_fast,
            )
            if prefer_fast and not vector_hits:
                await self.refresh_entity_scope(entity_id=entity_id)
                vector_hits = await self._memory_index.search(
                    scope_id=f"entity:{entity_id}",
                    query=query or "",
                    limit=max(limit * 4, 12),
                    attachments=attachments,
                    use_reranker=False,
                )
        vector_results = []
        for hit in vector_hits:
            source_user_id = hit.record.user_id
            scope = (
                "self_user"
                if current_user_id and source_user_id == current_user_id
                else "other_user"
            )
            vector_results.append(
                self._decorate_recall_result(
                    candidate={
                        "layer": hit.record.layer,
                        "value": hit.record.text,
                        "source_version": hit.record.metadata.get("source_version"),
                        "occurred_at": hit.record.occurred_at,
                        "last_seen_at": hit.record.last_seen_at,
                        "mention_count": hit.record.mention_count,
                        "context_tags": dict(hit.record.metadata.get("context_tags", {})),
                        "pinned": bool(hit.record.metadata.get("pinned", False)),
                        "retention_score": hit.record.retention_score,
                        "retention_reason": hit.record.metadata.get("retention_reason"),
                        "normalized_key": hit.record.normalized_key,
                    },
                    scope=scope,
                    source_session_id=hit.record.session_id or current_session_id or "",
                    source_user_id=source_user_id,
                    symbolic_score=0.0,
                    vector_score=hit.vector_score,
                    current_session_id=current_session_id,
                    current_user_id=current_user_id,
                )
            )
        vector_results = self._filter_query_echo_candidates(
            candidates=vector_results,
            query=query,
        )
        results = self._merge_recall_candidates(
            candidates=[*symbolic_results, *vector_results],
            limit=limit,
        )
        return {
            "entity_id": entity_id,
            "results": results,
            "source_user_count": len({source_user_id for source_user_id, _ in sources}),
            "session_count": len(sources),
            "integrity_summary": {
                "symbolic_hit_count": len(symbolic_results),
                "vector_hit_count": len(vector_hits),
                "cross_user_hit_count": sum(
                    1 for item in results if item.get("scope") == "other_user"
                ),
            },
        }

    async def recall_person_memory(
        self,
        *,
        session_id: str,
        user_id: str | None,
        query: str | None,
        limit: int,
        context_filters: dict[str, str] | None = None,
        attachments: list[MemoryMediaAttachment] | None = None,
        include_entity_context: bool = False,
        entity_id: str | None = None,
        enable_vector_search: bool = True,
        enable_entity_vector_search: bool = True,
        prefer_fast: bool = False,
        include_factual_shadow: bool = False,
    ) -> dict[str, Any]:
        if not user_id:
            return await self.recall_session_memory(
                session_id=session_id,
                query=query,
                limit=limit,
                context_filters=context_filters,
                attachments=attachments,
                enable_vector_search=enable_vector_search,
                prefer_fast=prefer_fast,
                include_factual_shadow=include_factual_shadow,
            )

        user_recall = await self.recall_user_memory(
            user_id=user_id,
            query=query,
            limit=limit,
            current_session_id=session_id,
            attachments=attachments,
            enable_vector_search=enable_vector_search,
            prefer_fast=prefer_fast,
            include_factual_shadow=include_factual_shadow,
        )
        entity_recall: dict[str, Any] = {"results": [], "integrity_summary": {}}
        if include_entity_context and entity_id:
            entity_recall = await self.recall_entity_memory(
                entity_id=entity_id,
                current_user_id=user_id,
                current_session_id=session_id,
                query=query,
                limit=limit,
                attachments=attachments,
                enable_vector_search=enable_entity_vector_search,
                prefer_fast=prefer_fast,
            )
        session_recall = await self.recall_session_memory(
            session_id=session_id,
            query=query,
            limit=limit,
            context_filters=context_filters,
            attachments=attachments,
            enable_vector_search=enable_vector_search,
            prefer_fast=prefer_fast,
            include_factual_shadow=include_factual_shadow,
        )
        merged_results = self._merge_recall_candidates(
            candidates=[
                *list(session_recall.get("results", [])),
                *list(user_recall.get("results", [])),
                *list(entity_recall.get("results", [])),
            ],
            limit=limit,
        )
        return {
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "recall_count": len(merged_results),
            "results": merged_results,
            "matched_nodes": session_recall.get("matched_nodes", []),
            "bridges": session_recall.get("bridges", []),
            "graph_summary": {
                **dict(session_recall.get("graph_summary", {})),
                "user_session_count": int(user_recall.get("session_count", 0) or 0),
                "entity_session_count": int(entity_recall.get("session_count", 0) or 0),
            },
            "integrity_summary": {
                **dict(session_recall.get("integrity_summary", {})),
                "user_symbolic_hit_count": int(
                    user_recall.get("integrity_summary", {}).get("symbolic_hit_count", 0)
                    or 0
                ),
                "user_vector_hit_count": int(
                    user_recall.get("integrity_summary", {}).get("vector_hit_count", 0)
                    or 0
                ),
                "entity_symbolic_hit_count": int(
                    entity_recall.get("integrity_summary", {}).get("symbolic_hit_count", 0)
                    or 0
                ),
                "entity_vector_hit_count": int(
                    entity_recall.get("integrity_summary", {}).get("vector_hit_count", 0)
                    or 0
                ),
                "entity_cross_user_hit_count": int(
                    entity_recall.get("integrity_summary", {}).get("cross_user_hit_count", 0)
                    or 0
                ),
            },
            "memory_turn_count": session_recall.get("memory_turn_count", 0),
            "entity_recall_summary": {
                "entity_id": entity_recall.get("entity_id"),
                "source_user_count": int(entity_recall.get("source_user_count", 0) or 0),
            },
            "factual_backend_mode": self._factual_backend_mode,
            "native_factual_hit_count": int(
                session_recall.get("native_factual_hit_count", 0) or 0
            )
            + int(user_recall.get("native_factual_hit_count", 0) or 0),
            "mem0_factual_hit_count": int(
                session_recall.get("mem0_factual_hit_count", 0) or 0
            )
            + int(user_recall.get("mem0_factual_hit_count", 0) or 0),
            "selected_factual_backend": self._resolve_selected_factual_backend(
                native_count=int(session_recall.get("native_factual_hit_count", 0) or 0)
                + int(user_recall.get("native_factual_hit_count", 0) or 0),
                mem0_count=int(session_recall.get("mem0_factual_hit_count", 0) or 0)
                + int(user_recall.get("mem0_factual_hit_count", 0) or 0),
            ),
            "mem0_fallback_reason": (
                session_recall.get("mem0_fallback_reason")
                or user_recall.get("mem0_fallback_reason")
            ),
        }
