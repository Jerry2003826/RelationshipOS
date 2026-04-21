"""Mem0 OSS benchmark arm: local memory layer + same generation model."""

from __future__ import annotations

import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from mem0 import Memory
from mem0.configs.base import MemoryConfig
from mem0.embeddings.configs import EmbedderConfig
from mem0.llms.configs import LlmConfig
from mem0.vector_stores.configs import VectorStoreConfig

from benchmarks.baseline_client import BARE_PERSONA
from benchmarks.chat_backends import (
    BenchmarkChatBackend,
    ChatBackendConfig,
    resolve_benchmark_api_base,
    resolve_benchmark_api_key,
)
from benchmarks.persona_prompts import load_benchmark_persona

_DEFAULT_EMBED_DIMENSIONS = {
    "intfloat/multilingual-e5-small": 384,
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
}


@dataclass(slots=True)
class Mem0TurnResult:
    user_message: str
    assistant_response: str
    latency_ms: float
    retrieval_count: int


@dataclass(slots=True)
class _Mem0SessionState:
    user_id: str
    run_id: str
    history: list[dict[str, str]]


class Mem0BenchmarkClient:
    """Three-arm benchmark baseline backed by Mem0 OSS and local Qdrant."""

    def __init__(
        self,
        model: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
        max_context_turns: int = 20,
        retrieval_limit: int = 6,
        embed_model: str | None = None,
        qdrant_path: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        provider = os.getenv("BENCHMARK_CHAT_PROVIDER", "litellm")
        self.model = (
            model
            or os.getenv("BENCHMARK_CHAT_MODEL", "")
            or os.getenv("RELATIONSHIP_OS_LLM_MODEL", "")
        )
        self.api_base = api_base or resolve_benchmark_api_base(
            provider=provider,
            default_api_base=os.getenv("RELATIONSHIP_OS_LLM_API_BASE", ""),
        )
        self.api_key = api_key or resolve_benchmark_api_key(
            provider=provider,
            default_api_key=os.getenv("RELATIONSHIP_OS_LLM_API_KEY", ""),
        )
        self.max_context_turns = max_context_turns
        self.retrieval_limit = retrieval_limit
        self.embed_model = embed_model or os.getenv(
            "BENCHMARK_MEM0_EMBED_MODEL",
            "intfloat/multilingual-e5-small",
        )
        self.qdrant_path = qdrant_path or os.getenv(
            "BENCHMARK_MEM0_QDRANT_PATH",
            "benchmark_results/.mem0/qdrant",
        )
        self.history_db_path = str(Path(self.qdrant_path).parent / "history.db")
        self._run_tag = uuid.uuid4().hex[:8]
        self.persona_prompt = load_benchmark_persona(BARE_PERSONA)
        self._memory = self._build_memory()
        self._sessions: dict[str, _Mem0SessionState] = {}
        self._chat_backend = BenchmarkChatBackend(
            ChatBackendConfig.from_env(
                default_model=self.model,
                default_api_base=self.api_base,
                default_api_key=self.api_key,
                timeout=timeout,
            )
        )

    def _build_memory(self) -> Memory:
        qdrant_path = Path(self.qdrant_path)
        qdrant_path.mkdir(parents=True, exist_ok=True)
        Path(self.history_db_path).parent.mkdir(parents=True, exist_ok=True)
        embedding_dims = int(
            os.getenv(
                "BENCHMARK_MEM0_EMBED_DIMS",
                str(_DEFAULT_EMBED_DIMENSIONS.get(self.embed_model, 384)),
            )
        )
        collection_slug = re.sub(r"[^a-z0-9]+", "_", self.embed_model.casefold()).strip("_")[:40]

        config = MemoryConfig(
            vector_store=VectorStoreConfig(
                provider="qdrant",
                config={
                    "collection_name": f"benchmark_mem0_{collection_slug}_{embedding_dims}",
                    "embedding_model_dims": embedding_dims,
                    "path": str(qdrant_path),
                    "on_disk": True,
                },
            ),
            embedder=EmbedderConfig(
                provider="huggingface",
                config={
                    "model": self.embed_model,
                    "embedding_dims": embedding_dims,
                    "model_kwargs": {"device": "cpu"},
                },
            ),
            llm=LlmConfig(
                provider="openai",
                config={
                    "model": self.model,
                    "api_key": self.api_key,
                    "openai_base_url": self.api_base,
                    "temperature": 0.1,
                    "max_tokens": 512,
                    "top_p": 0.7,
                },
            ),
            history_db_path=self.history_db_path,
        )
        return Memory(config=config)

    def create_session(
        self,
        session_id: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        _ = metadata
        resolved_user_id = user_id or f"{self._run_tag}:{session_id}"
        state = _Mem0SessionState(
            user_id=resolved_user_id,
            run_id=session_id,
            history=[{"role": "system", "content": self.persona_prompt}],
        )
        self._sessions[session_id] = state
        return session_id

    def _search_memories(self, *, state: _Mem0SessionState, query: str) -> list[str]:
        search_result = (
            self._memory.search(
                query=query,
                user_id=state.user_id,
                run_id=state.run_id,
                limit=self.retrieval_limit,
                rerank=False,
            )
            or {"results": []}
        )
        seen: set[str] = set()
        lines: list[str] = []
        for item in search_result.get("results", []):
            memory_text = str(item.get("memory", "")).strip()
            if not memory_text or memory_text in seen:
                continue
            seen.add(memory_text)
            role = item.get("role")
            prefix = f"{role}: " if role else ""
            lines.append(f"- {prefix}{memory_text}")
        return lines

    def _build_messages(
        self, *, state: _Mem0SessionState, content: str
    ) -> tuple[list[dict[str, str]], int]:
        retrieval_lines = self._search_memories(state=state, query=content)
        messages = [dict(item) for item in state.history]
        if retrieval_lines:
            memory_block = (
                "Relevant memory snippets from previous conversations:\n"
                + "\n".join(retrieval_lines[: self.retrieval_limit])
            )
            if messages and messages[0].get("role") == "system":
                base_content = messages[0].get("content", "").strip()
                messages[0]["content"] = f"{base_content}\n\n{memory_block}".strip()
            else:
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": memory_block,
                    },
                )
        messages.append({"role": "user", "content": content})
        return messages, len(retrieval_lines)

    def send_turn(self, session_id: str, content: str) -> Mem0TurnResult:
        state = self._sessions.setdefault(
            session_id,
            _Mem0SessionState(
                user_id=f"{self._run_tag}:{session_id}",
                run_id=session_id,
                history=[{"role": "system", "content": self.persona_prompt}],
            ),
        )
        messages, retrieval_count = self._build_messages(state=state, content=content)

        t0 = time.perf_counter()
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                reply, _raw = self._chat_backend.complete(messages)
                break
            except Exception as exc:
                last_exc = exc
                wait = 1.0 * (attempt + 1)
                print(f"    ⚠ mem0 LLM error, retry in {wait:.0f}s: {exc}", flush=True)
                time.sleep(wait)
        else:
            raise last_exc  # type: ignore[misc]
        latency = (time.perf_counter() - t0) * 1000

        state.history.append({"role": "user", "content": content})
        state.history.append({"role": "assistant", "content": reply})
        if len(state.history) > 1 + self.max_context_turns * 2:
            state.history = [state.history[0]] + state.history[-(self.max_context_turns * 2) :]

        self._memory.add(
            [
                {"role": "user", "content": content},
                {"role": "assistant", "content": reply},
            ],
            user_id=state.user_id,
            run_id=state.run_id,
            infer=False,
            metadata={"source": "benchmark_mem0"},
        )

        return Mem0TurnResult(
            user_message=content,
            assistant_response=reply,
            latency_ms=latency,
            retrieval_count=retrieval_count,
        )

    def close(self) -> None:
        self._sessions.clear()
