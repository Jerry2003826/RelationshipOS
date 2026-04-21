from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from relationship_os.application.memory_index import (
    MemoryIndex,
    MemoryIndexHit,
    MemoryIndexRecord,
    NullMemoryIndex,
)
from relationship_os.core.logging import get_logger

_LOGGER = get_logger("relationship_os.factual_memory")
_FACTUAL_ALIAS_KEYS = {
    "identity_name",
    "origin_grew_up",
    "current_residence",
    "occupation",
    "pet_dog",
    "pet_cat",
    "pet_name",
    "preference_like",
}


@dataclass(slots=True, frozen=True)
class FactualMemoryCandidate:
    value: str
    normalized_key: str
    layer: str
    memory_kind: str
    source_session_id: str
    source_user_id: str | None = None
    source_version: int | None = None
    occurred_at: str | None = None
    last_seen_at: str | None = None
    mention_count: int = 1
    confidence_score: float = 0.0
    importance_score: float = 0.0
    retention_score: float = 0.0
    retention_reason: str | None = None
    context_tags: dict[str, str] = field(default_factory=dict)
    pinned: bool = False
    backend: str = "native"
    fact_id: str = ""

    def to_candidate_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "value": self.value,
            "source_version": self.source_version,
            "occurred_at": self.occurred_at,
            "last_seen_at": self.last_seen_at,
            "mention_count": self.mention_count,
            "context_tags": dict(self.context_tags),
            "pinned": self.pinned,
            "retention_score": self.retention_score,
            "retention_reason": self.retention_reason,
            "normalized_key": self.normalized_key,
            "source_user_id": self.source_user_id,
            "source_session_id": self.source_session_id,
            "backend": self.backend,
            "fact_id": self.fact_id,
        }


class FactualMemoryBackend(Protocol):
    backend_name: str

    async def upsert_session_facts(
        self,
        *,
        session_id: str,
        user_id: str | None,
        entity_id: str | None,
        compact: bool,
        facts: list[FactualMemoryCandidate],
    ) -> None: ...

    async def refresh_user_facts(
        self,
        *,
        user_id: str,
        session_facts: dict[str, list[FactualMemoryCandidate]],
    ) -> None: ...

    async def recall_session_facts(
        self,
        *,
        session_id: str,
        query: str | None,
        limit: int,
        prefer_fast: bool,
    ) -> list[FactualMemoryCandidate]: ...

    async def recall_user_facts(
        self,
        *,
        user_id: str,
        current_session_id: str | None,
        query: str | None,
        limit: int,
        prefer_fast: bool,
    ) -> list[FactualMemoryCandidate]: ...


def _memory_index_record_from_fact(
    *,
    scope_id: str,
    fact: FactualMemoryCandidate,
) -> MemoryIndexRecord:
    return MemoryIndexRecord(
        record_id=f"{scope_id}:fact:{fact.fact_id or fact.normalized_key}",
        scope_id=scope_id,
        user_id=fact.source_user_id,
        session_id=fact.source_session_id,
        layer=fact.layer,
        memory_kind=fact.memory_kind,
        text=fact.value,
        normalized_key=fact.normalized_key,
        occurred_at=fact.occurred_at,
        last_seen_at=fact.last_seen_at,
        mention_count=max(1, int(fact.mention_count)),
        importance_score=float(fact.importance_score),
        confidence_score=float(fact.confidence_score),
        retention_score=float(fact.retention_score),
        metadata={
            "context_tags": dict(fact.context_tags),
            "pinned": bool(fact.pinned),
            "retention_reason": fact.retention_reason,
            "source_version": fact.source_version,
            "fact_id": fact.fact_id,
            "backend": fact.backend,
        },
    )


def _fact_from_memory_index_hit(hit: MemoryIndexHit, *, backend: str) -> FactualMemoryCandidate:
    metadata = dict(hit.record.metadata or {})
    source_version_raw = metadata.get("source_version")
    source_version: int | None = None
    if source_version_raw is not None:
        try:
            source_version = int(source_version_raw)
        except (TypeError, ValueError):
            source_version = None
    return FactualMemoryCandidate(
        value=hit.record.text,
        normalized_key=hit.record.normalized_key,
        layer=hit.record.layer,
        memory_kind=hit.record.memory_kind,
        source_session_id=hit.record.session_id or "",
        source_user_id=hit.record.user_id,
        source_version=source_version,
        occurred_at=hit.record.occurred_at,
        last_seen_at=hit.record.last_seen_at,
        mention_count=max(1, int(hit.record.mention_count)),
        confidence_score=float(hit.record.confidence_score),
        importance_score=float(hit.record.importance_score),
        retention_score=float(hit.record.retention_score),
        retention_reason=str(metadata.get("retention_reason") or "").strip() or None,
        context_tags={
            str(key): str(value)
            for key, value in dict(metadata.get("context_tags") or {}).items()
            if value not in {None, ""}
        },
        pinned=bool(metadata.get("pinned", False)),
        backend=backend,
        fact_id=str(metadata.get("fact_id") or hit.record.normalized_key),
    )


def _is_factual_index_hit(hit: MemoryIndexHit) -> bool:
    metadata = dict(hit.record.metadata or {})
    if bool(metadata.get("factual_candidate", False)):
        return True
    semantic_aliases = {
        str(alias) for alias in list(metadata.get("semantic_aliases") or []) if str(alias).strip()
    }
    return bool(semantic_aliases.intersection(_FACTUAL_ALIAS_KEYS))


class NativeFactualMemoryBackend:
    backend_name = "native"

    def __init__(self, *, memory_index: MemoryIndex | None, enabled: bool) -> None:
        self._memory_index = memory_index or NullMemoryIndex()
        self._enabled = enabled

    async def upsert_session_facts(
        self,
        *,
        session_id: str,
        user_id: str | None,
        entity_id: str | None,
        compact: bool,
        facts: list[FactualMemoryCandidate],
    ) -> None:
        return None

    async def refresh_user_facts(
        self,
        *,
        user_id: str,
        session_facts: dict[str, list[FactualMemoryCandidate]],
    ) -> None:
        return None

    async def recall_session_facts(
        self,
        *,
        session_id: str,
        query: str | None,
        limit: int,
        prefer_fast: bool,
    ) -> list[FactualMemoryCandidate]:
        if not self._enabled or not (query or "").strip():
            return []
        hits = await self._memory_index.search(
            scope_id=f"session:{session_id}",
            query=query or "",
            limit=max(limit * 3, 8),
            use_reranker=not prefer_fast,
        )
        factual_hits = [hit for hit in hits if _is_factual_index_hit(hit)]
        return [_fact_from_memory_index_hit(hit, backend=self.backend_name) for hit in factual_hits]

    async def recall_user_facts(
        self,
        *,
        user_id: str,
        current_session_id: str | None,
        query: str | None,
        limit: int,
        prefer_fast: bool,
    ) -> list[FactualMemoryCandidate]:
        if not self._enabled or not (query or "").strip():
            return []
        hits = await self._memory_index.search(
            scope_id=f"user:{user_id}",
            query=query or "",
            limit=max(limit * 3, 10),
            use_reranker=not prefer_fast,
        )
        factual_hits = [hit for hit in hits if _is_factual_index_hit(hit)]
        return [_fact_from_memory_index_hit(hit, backend=self.backend_name) for hit in factual_hits]


class Mem0FactualMemoryBackend:
    backend_name = "mem0"

    def __init__(
        self,
        *,
        qdrant_path: str,
        history_db_path: str,
        embed_model: str,
        retrieval_limit: int,
        llm_model: str,
        llm_api_base: str | None,
        llm_api_key: str | None,
        memory: Any | None = None,
    ) -> None:
        self._qdrant_path = qdrant_path
        self._history_db_path = history_db_path
        self._embed_model = embed_model
        self._retrieval_limit = max(4, retrieval_limit)
        self._llm_model = llm_model
        self._llm_api_base = llm_api_base or ""
        self._llm_api_key = llm_api_key or "shadow-disabled"
        self._memory = memory
        self._available = memory is not None
        self._unavailable_reason = ""

        if self._memory is None:
            self._memory = self._build_memory()
            self._available = self._memory is not None

    @property
    def available(self) -> bool:
        return self._available

    @property
    def unavailable_reason(self) -> str:
        return self._unavailable_reason

    def _build_memory(self) -> Any | None:
        try:
            from mem0 import Memory
            from mem0.configs.base import MemoryConfig
            from mem0.embeddings.configs import EmbedderConfig
            from mem0.llms.configs import LlmConfig
            from mem0.vector_stores.configs import VectorStoreConfig
        except Exception as exc:  # pragma: no cover - import availability depends on extras
            self._unavailable_reason = f"mem0_import_error:{type(exc).__name__}"
            _LOGGER.warning(
                "mem0_shadow_backend_unavailable",
                reason=self._unavailable_reason,
            )
            return None

        try:
            qdrant_path = Path(self._qdrant_path)
            qdrant_path.mkdir(parents=True, exist_ok=True)
            history_db_path = Path(self._history_db_path)
            history_db_path.parent.mkdir(parents=True, exist_ok=True)
            config = MemoryConfig(
                vector_store=VectorStoreConfig(
                    provider="qdrant",
                    config={
                        "collection_name": "relationship_os_mem0_factual",
                        "embedding_model_dims": 384,
                        "path": str(qdrant_path),
                        "on_disk": True,
                    },
                ),
                embedder=EmbedderConfig(
                    provider="huggingface",
                    config={
                        "model": self._embed_model,
                        "embedding_dims": 384,
                        "model_kwargs": {"device": "cpu"},
                    },
                ),
                llm=LlmConfig(
                    provider="openai",
                    config={
                        "model": self._llm_model,
                        "api_key": self._llm_api_key,
                        "openai_base_url": self._llm_api_base,
                        "temperature": 0.1,
                        "max_tokens": 256,
                    },
                ),
                history_db_path=str(history_db_path),
            )
            return Memory(config=config)
        except Exception as exc:  # pragma: no cover - backend init depends on local env
            self._unavailable_reason = f"mem0_init_error:{type(exc).__name__}"
            _LOGGER.warning(
                "mem0_shadow_backend_init_failed",
                reason=self._unavailable_reason,
                error=str(exc),
            )
            return None

    def _scope_kwargs(
        self,
        *,
        session_id: str,
        user_id: str | None,
    ) -> dict[str, Any]:
        if user_id:
            return {"user_id": user_id, "run_id": session_id}
        return {"run_id": session_id}

    def _metadata_for_fact(self, fact: FactualMemoryCandidate) -> dict[str, Any]:
        return {
            "fact_id": fact.fact_id,
            "normalized_key": fact.normalized_key,
            "layer": fact.layer,
            "memory_kind": fact.memory_kind,
            "source_session_id": fact.source_session_id,
            "source_user_id": fact.source_user_id or "",
            "source_version": fact.source_version,
            "mention_count": max(1, int(fact.mention_count)),
            "confidence_score": float(fact.confidence_score),
            "importance_score": float(fact.importance_score),
            "retention_score": float(fact.retention_score),
            "retention_reason": fact.retention_reason or "",
            "context_tags": dict(fact.context_tags),
            "pinned": bool(fact.pinned),
            "backend": self.backend_name,
        }

    def _existing_fact(
        self,
        *,
        session_id: str,
        user_id: str | None,
        fact_id: str,
    ) -> dict[str, Any] | None:
        if not self._available or self._memory is None:
            return None
        response = self._memory.get_all(
            limit=1,
            filters={"fact_id": fact_id},
            **self._scope_kwargs(session_id=session_id, user_id=user_id),
        )
        results = list((response or {}).get("results") or [])
        return dict(results[0]) if results else None

    async def upsert_session_facts(
        self,
        *,
        session_id: str,
        user_id: str | None,
        entity_id: str | None,
        compact: bool,
        facts: list[FactualMemoryCandidate],
    ) -> None:
        if not self._available or self._memory is None:
            return
        for fact in facts:
            existing = self._existing_fact(
                session_id=session_id,
                user_id=user_id,
                fact_id=fact.fact_id,
            )
            if existing:
                if str(existing.get("memory") or "").strip() == fact.value.strip():
                    continue
                memory_id = str(existing.get("id") or "").strip()
                if memory_id:
                    self._memory.delete(memory_id)
            self._memory.add(
                [{"role": "assistant", "content": fact.value}],
                infer=False,
                metadata=self._metadata_for_fact(fact),
                **self._scope_kwargs(session_id=session_id, user_id=user_id),
            )

    async def refresh_user_facts(
        self,
        *,
        user_id: str,
        session_facts: dict[str, list[FactualMemoryCandidate]],
    ) -> None:
        if not self._available or self._memory is None:
            return
        for session_id, facts in session_facts.items():
            await self.upsert_session_facts(
                session_id=session_id,
                user_id=user_id,
                entity_id=None,
                compact=False,
                facts=facts,
            )

    def _fact_from_mem0_item(self, item: dict[str, Any]) -> FactualMemoryCandidate:
        metadata = dict(item.get("metadata") or {})
        value = str(item.get("memory") or "").strip()
        normalized_key = str(metadata.get("normalized_key") or value.casefold().strip())
        source_version_raw = metadata.get("source_version")
        source_version: int | None = None
        if source_version_raw is not None:
            try:
                source_version = int(source_version_raw)
            except (TypeError, ValueError):
                source_version = None
        return FactualMemoryCandidate(
            value=value,
            normalized_key=normalized_key,
            layer=str(metadata.get("layer") or "semantic_memory"),
            memory_kind=str(metadata.get("memory_kind") or "persistent"),
            source_session_id=str(metadata.get("source_session_id") or item.get("run_id") or ""),
            source_user_id=(
                str(metadata.get("source_user_id") or item.get("user_id") or "").strip() or None
            ),
            source_version=source_version,
            occurred_at=item.get("created_at"),
            last_seen_at=item.get("updated_at"),
            mention_count=max(1, int(metadata.get("mention_count", 1) or 1)),
            confidence_score=float(metadata.get("confidence_score", 0.0) or 0.0),
            importance_score=float(metadata.get("importance_score", 0.0) or 0.0),
            retention_score=float(metadata.get("retention_score", 0.0) or 0.0),
            retention_reason=str(metadata.get("retention_reason") or "").strip() or None,
            context_tags={
                str(key): str(value)
                for key, value in dict(metadata.get("context_tags") or {}).items()
                if value not in {None, ""}
            },
            pinned=bool(metadata.get("pinned", False)),
            backend=self.backend_name,
            fact_id=str(metadata.get("fact_id") or normalized_key),
        )

    async def recall_session_facts(
        self,
        *,
        session_id: str,
        query: str | None,
        limit: int,
        prefer_fast: bool,
    ) -> list[FactualMemoryCandidate]:
        if not self._available or self._memory is None or not (query or "").strip():
            return []
        response = self._memory.search(
            query=query or "",
            limit=max(limit * 3, self._retrieval_limit),
            rerank=not prefer_fast,
            run_id=session_id,
        )
        return [
            self._fact_from_mem0_item(dict(item))
            for item in list((response or {}).get("results") or [])
        ]

    async def recall_user_facts(
        self,
        *,
        user_id: str,
        current_session_id: str | None,
        query: str | None,
        limit: int,
        prefer_fast: bool,
    ) -> list[FactualMemoryCandidate]:
        if not self._available or self._memory is None or not (query or "").strip():
            return []
        response = self._memory.search(
            query=query or "",
            limit=max(limit * 3, self._retrieval_limit),
            rerank=not prefer_fast,
            user_id=user_id,
        )
        return [
            self._fact_from_mem0_item(dict(item))
            for item in list((response or {}).get("results") or [])
        ]
