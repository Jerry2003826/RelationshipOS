"""Showcase benchmark: baseline vs Mem0 OSS vs RelationshipOS."""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from benchmarks.baseline_client import BaselineLLMClient
from benchmarks.client import RelationshipOSClient
from benchmarks.datasets.companion_stress_zh import build_companion_stress_zh_scenarios
from benchmarks.datasets.deep_memory import DEEP_MEMORY_SCENARIOS
from benchmarks.datasets.emotional import EMOTIONAL_SCENARIOS
from benchmarks.datasets.entity_social import ENTITY_SOCIAL_SCENARIOS
from benchmarks.datasets.friend_chat_zh import FRIEND_CHAT_ZH_SCENARIOS
from benchmarks.datasets.living_entity import LIVING_ENTITY_SCENARIOS
from benchmarks.datasets.locomo import LOCOMO_PROBES
from benchmarks.datasets.msc import MSC_SCENARIOS
from benchmarks.datasets.person_memory import PERSON_MEMORY_SCENARIOS
from benchmarks.datasets.proactive_governance import PROACTIVE_GOVERNANCE_SCENARIOS
from benchmarks.judge import LLMJudge
from benchmarks.mem0_client import Mem0BenchmarkClient
from benchmarks.report import generate_benchmark_report
from benchmarks.scoring import (
    average_scores,
    compute_language_breakdown,
    compute_weighted_overall,
    merge_dimension_scores,
    percentile_latency,
    score_expected_answer,
    score_expected_answer_diagnostic,
    score_expected_answer_for_category,
    score_proactive_case,
)
from relationship_os.application.memory_index import (
    AliyunMultimodalEmbedder,
    AliyunNativeMemoryReranker,
    AliyunTextEmbedder,
    DescriptorMultimodalEmbedder,
    GoogleMultimodalEmbedder,
    HashTextEmbedder,
    MemoryIndexHit,
    MemoryIndexRecord,
    OpenAICompatibleMemoryReranker,
    OpenAICompatibleTextEmbedder,
)


def _p(message: str) -> None:
    print(message, flush=True)


class ChatClient(Protocol):
    def create_session(
        self,
        session_id: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str: ...
    def send_turn(self, session_id: str, content: str) -> Any: ...
    def close(self) -> None: ...


class BenchmarkSuiteTimeoutError(RuntimeError):
    """Raised when a suite exceeds its hard runtime budget."""


@contextmanager
def _suite_timeout(seconds: float | None) -> Any:
    if not seconds or seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _raise_timeout(_signum: int, _frame: Any) -> None:
        raise BenchmarkSuiteTimeoutError(f"suite timed out after {seconds:.0f}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _filter_cases(cases: list[Any], languages: set[str], max_cases: int | None) -> list[Any]:
    filtered = [case for case in cases if getattr(case, "language", "en") in languages]
    if max_cases is not None:
        return filtered[:max_cases]
    return filtered


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().casefold()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _benchmark_inter_turn_idle_seconds() -> float:
    return max(0.0, _env_float("BENCHMARK_INTER_TURN_IDLE_SECONDS", 0.0))


def _benchmark_consolidate_between_sessions() -> bool:
    return _env_bool("BENCHMARK_CONSOLIDATE_BETWEEN_SESSIONS", False)


def _benchmark_consolidation_timeout_seconds() -> float:
    return max(1.0, _env_float("BENCHMARK_CONSOLIDATION_TIMEOUT_SECONDS", 120.0))


def _benchmark_consolidation_poll_interval_seconds() -> float:
    return max(0.05, _env_float("BENCHMARK_CONSOLIDATION_POLL_INTERVAL_SECONDS", 0.5))


def _benchmark_stress_mode() -> str:
    raw = os.getenv("BENCHMARK_STRESS_MODE", "stable").strip().casefold()
    return raw if raw in {"strict", "stable"} else "stable"


def _benchmark_session_metadata(
    *,
    suite_name: str,
    scenario_id: str,
    benchmark_role: str,
    session_id: str,
    user_id: str | None,
) -> dict[str, Any]:
    return {
        "source": "scenario_evaluation",
        "suite_name": suite_name,
        "scenario_id": scenario_id,
        "benchmark_role": benchmark_role,
        "benchmark_session_id": session_id,
        "stress_mode": _benchmark_stress_mode(),
        "user_id": user_id or "",
    }


def _maybe_idle(client: ChatClient, *, seconds: float) -> None:
    delay = max(0.0, float(seconds))
    if delay <= 0:
        return
    idle = getattr(client, "idle", None)
    if callable(idle):
        idle(delay)
        return
    time.sleep(delay)


def _maybe_consolidate_session(
    client: ChatClient,
    *,
    session_id: str,
    scenario_id: str,
    user_id: str | None,
) -> dict[str, Any] | None:
    if not _benchmark_consolidate_between_sessions():
        return None
    consolidate_session = getattr(client, "consolidate_session", None)
    if not callable(consolidate_session):
        return None
    return consolidate_session(
        session_id,
        timeout_seconds=_benchmark_consolidation_timeout_seconds(),
        poll_interval=_benchmark_consolidation_poll_interval_seconds(),
        metadata={
            "source": "benchmark_companion_stress_zh",
            "scenario_id": scenario_id,
            "user_id": user_id or "",
            "stress_mode": _benchmark_stress_mode(),
            "benchmark_role": "checkpoint",
        },
    )


def _suite_language_breakdown(details: list[dict[str, Any]]) -> dict[str, float]:
    return compute_language_breakdown(details, score_key="score")


def _extract_deliberation_trace(result: Any) -> dict[str, Any]:
    raw = dict(getattr(result, "raw", {}) or {})
    projection = dict(raw.get("projection") or {})
    state = dict(projection.get("state") or {})
    memory_recall = dict(state.get("last_memory_recall") or {})
    edge_runtime_plan = dict(memory_recall.get("edge_runtime_plan") or {})
    mode = str(
        edge_runtime_plan.get("interpreted_deliberation_mode")
        or edge_runtime_plan.get("deliberation_mode")
        or ""
    ).strip()
    if mode not in {"fast_reply", "light_recall", "deep_recall"}:
        return {}
    need_raw = edge_runtime_plan.get("interpreted_deliberation_need")
    if need_raw is None:
        need_raw = edge_runtime_plan.get("deliberation_need")
    try:
        need = float(need_raw) if need_raw is not None else None
    except (TypeError, ValueError):
        need = None
    if need is not None:
        need = round(max(0.0, min(1.0, need)), 3)
    return {
        "mode": mode,
        "need": need,
        "intent": str(edge_runtime_plan.get("interpreted_intent") or "").strip(),
        "fast_path": str(
            edge_runtime_plan.get("fast_path") or memory_recall.get("source") or ""
        ).strip(),
    }


def _new_deliberation_stats() -> dict[str, Any]:
    return {
        "mode_counts": {
            "fast_reply": 0,
            "light_recall": 0,
            "deep_recall": 0,
        },
        "needs": [],
        "fast_paths": {},
    }


def _record_deliberation_trace(stats: dict[str, Any], trace: dict[str, Any]) -> None:
    mode = str(trace.get("mode") or "").strip()
    if mode not in {"fast_reply", "light_recall", "deep_recall"}:
        return
    mode_counts = dict(stats.get("mode_counts") or {})
    mode_counts[mode] = int(mode_counts.get(mode, 0) or 0) + 1
    stats["mode_counts"] = mode_counts
    need = trace.get("need")
    if isinstance(need, (int, float)):
        needs = list(stats.get("needs") or [])
        needs.append(float(need))
        stats["needs"] = needs
    fast_path = str(trace.get("fast_path") or "").strip()
    if fast_path:
        fast_paths = dict(stats.get("fast_paths") or {})
        fast_paths[fast_path] = int(fast_paths.get(fast_path, 0) or 0) + 1
        stats["fast_paths"] = fast_paths


def _finalize_deliberation_stats(stats: dict[str, Any]) -> dict[str, Any]:
    mode_counts = {
        key: int((stats.get("mode_counts") or {}).get(key, 0) or 0)
        for key in ("fast_reply", "light_recall", "deep_recall")
    }
    needs = [
        float(value)
        for value in list(stats.get("needs") or [])
        if isinstance(value, (int, float))
    ]
    fast_paths = dict(stats.get("fast_paths") or {})
    dominant_mode = max(mode_counts, key=mode_counts.get) if any(mode_counts.values()) else ""
    dominant_fast_path = (
        max(fast_paths, key=fast_paths.get)
        if fast_paths
        else ""
    )
    return {
        "mode_counts": mode_counts,
        "avg_need": round(sum(needs) / len(needs), 3) if needs else None,
        "observed_turns": sum(mode_counts.values()),
        "dominant_mode": dominant_mode,
        "fast_paths": fast_paths,
        "dominant_fast_path": dominant_fast_path,
    }


def _extract_response_diagnostics(result: Any) -> dict[str, Any]:
    raw = dict(getattr(result, "raw", {}) or {})
    diagnostics = raw.get("response_diagnostics")
    return dict(diagnostics or {}) if isinstance(diagnostics, dict) else {}


def _new_response_diagnostics_stats() -> dict[str, int]:
    return {
        "friend_chat_exposed_meta_count": 0,
        "friend_chat_exposed_under_grounded_count": 0,
        "friend_chat_exposed_plan_noncompliant_count": 0,
        "friend_chat_exposed_empty_count": 0,
    }


def _record_response_diagnostics(
    stats: dict[str, int],
    diagnostics: dict[str, Any],
) -> None:
    if diagnostics.get("friend_chat_exposed_meta"):
        stats["friend_chat_exposed_meta_count"] = (
            int(stats.get("friend_chat_exposed_meta_count", 0) or 0) + 1
        )
    if diagnostics.get("friend_chat_exposed_under_grounded"):
        stats["friend_chat_exposed_under_grounded_count"] = (
            int(stats.get("friend_chat_exposed_under_grounded_count", 0) or 0) + 1
        )
    if diagnostics.get("friend_chat_exposed_plan_noncompliant"):
        stats["friend_chat_exposed_plan_noncompliant_count"] = (
            int(stats.get("friend_chat_exposed_plan_noncompliant_count", 0) or 0) + 1
        )
    if diagnostics.get("friend_chat_exposed_empty"):
        stats["friend_chat_exposed_empty_count"] = (
            int(stats.get("friend_chat_exposed_empty_count", 0) or 0) + 1
        )


def _extract_turn_stage_timing(result: Any) -> dict[str, Any]:
    raw = dict(getattr(result, "raw", {}) or {})
    timing = raw.get("turn_stage_timing")
    return dict(timing or {}) if isinstance(timing, dict) else {}


def _new_turn_timing_stats() -> dict[str, Any]:
    return {
        "total_ms": [],
        "probe_session_mutation_count": 0,
    }


def _record_turn_stage_timing(
    stats: dict[str, Any],
    timing: dict[str, Any],
    *,
    probe_session: bool,
) -> None:
    total_ms = timing.get("total_ms")
    if isinstance(total_ms, (int, float)):
        totals = list(stats.get("total_ms") or [])
        totals.append(float(total_ms))
        stats["total_ms"] = totals
    if not probe_session:
        return
    mutation_fields = (
        "memory_sync_ms",
        "self_state_ms",
        "entity_update_ms",
        "action_ms",
    )
    mutated = any(
        isinstance(timing.get(field), (int, float)) and float(timing.get(field) or 0.0) > 0.0
        for field in mutation_fields
    )
    if mutated:
        stats["probe_session_mutation_count"] = (
            int(stats.get("probe_session_mutation_count", 0) or 0) + 1
        )


def _finalize_turn_timing_stats(stats: dict[str, Any]) -> dict[str, Any]:
    totals = [
        float(value)
        for value in list(stats.get("total_ms") or [])
        if isinstance(value, (int, float))
    ]
    return {
        "request_path_p50_ms": percentile_latency(totals, 0.5),
        "request_path_p95_ms": percentile_latency(totals, 0.95),
        "request_path_max_ms": max(totals) if totals else None,
        "observed_turns": len(totals),
        "probe_session_mutation_count": int(
            stats.get("probe_session_mutation_count", 0) or 0
        ),
    }


async def _provider_preflight_async() -> dict[str, Any]:
    text_provider = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_TEXT_PROVIDER",
        "aliyun",
    ).strip()
    text_model = os.getenv("RELATIONSHIP_OS_MEMORY_INDEX_TEXT_MODEL", "text-embedding-v4")
    text_api_base = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_TEXT_API_BASE",
        "https://dashscope.aliyuncs.com/api/v1",
    )
    text_api_key = os.getenv("RELATIONSHIP_OS_MEMORY_INDEX_TEXT_API_KEY", "") or os.getenv(
        "RELATIONSHIP_OS_LLM_API_KEY",
        "",
    )
    text_dimensions = int(
        os.getenv("RELATIONSHIP_OS_MEMORY_INDEX_TEXT_DIMENSIONS", "1024") or "1024"
    )
    fallback_embedder = HashTextEmbedder(dimensions=min(max(text_dimensions, 64), 256))
    if text_provider == "aliyun":
        text_embedder = AliyunTextEmbedder(
            model=text_model,
            api_key=text_api_key,
            api_base=text_api_base,
            dimensions=text_dimensions,
            fallback=fallback_embedder,
        )
    elif text_provider == "openai_compatible":
        text_embedder = OpenAICompatibleTextEmbedder(
            model=text_model,
            api_key=text_api_key,
            api_base=text_api_base,
            dimensions=text_dimensions,
            fallback=fallback_embedder,
        )
    else:
        text_embedder = fallback_embedder
    text_vectors = await text_embedder.embed_texts(["provider smoke for relationship os"])
    provider_status: dict[str, Any] = {
        "text_embedding": (
            text_embedder.status()
            if hasattr(text_embedder, "status")
            else {"provider": text_provider, "mode": "hash", "fallback": False}
        ),
    }
    provider_status["text_embedding"]["vector_dimensions"] = (
        len(text_vectors[0]) if text_vectors else 0
    )

    multimodal_provider = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_MULTIMODAL_PROVIDER",
        "aliyun",
    ).strip()
    multimodal_model = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_MULTIMODAL_MODEL",
        "qwen3-vl-embedding",
    )
    multimodal_api_base = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_MULTIMODAL_API_BASE",
        "https://dashscope.aliyuncs.com/api/v1",
    )
    multimodal_api_key = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_MULTIMODAL_API_KEY",
        "",
    ) or os.getenv("RELATIONSHIP_OS_LLM_API_KEY", "")
    if multimodal_provider == "aliyun":
        multimodal_embedder = AliyunMultimodalEmbedder(
            model=multimodal_model,
            api_key=multimodal_api_key,
            api_base=multimodal_api_base,
            dimensions=text_dimensions,
            fallback=fallback_embedder,
        )
        multimodal_vector = await multimodal_embedder.embed_query(
            text="provider smoke for relationship os multimodal",
            attachments=[],
        )
        multimodal_status = multimodal_embedder.status()
        multimodal_status["vector_dimensions"] = len(multimodal_vector)
    elif multimodal_provider == "google":
        multimodal_embedder = GoogleMultimodalEmbedder(
            model=multimodal_model,
            api_key=multimodal_api_key,
            api_base=multimodal_api_base,
            fallback=fallback_embedder,
        )
        multimodal_vector = await multimodal_embedder.embed_query(
            text="provider smoke for relationship os multimodal",
            attachments=[],
        )
        multimodal_status = multimodal_embedder.status()
        multimodal_status["vector_dimensions"] = len(multimodal_vector)
    elif multimodal_provider == "openai_compatible":
        multimodal_embedder = DescriptorMultimodalEmbedder(text_embedder=text_embedder)
        multimodal_vector = await multimodal_embedder.embed_query(
            text="provider smoke for relationship os multimodal",
            attachments=[],
        )
        multimodal_status = multimodal_embedder.status()
        multimodal_status["vector_dimensions"] = len(multimodal_vector)
    else:
        multimodal_status = {
            "provider": multimodal_provider or "none",
            "mode": "disabled",
            "fallback": False,
        }
    provider_status["multimodal_embedding"] = multimodal_status

    reranker_enabled = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_RERANKER_ENABLED",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}
    reranker_provider = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_RERANKER_PROVIDER",
        "aliyun",
    ).strip()
    reranker_model = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_RERANKER_MODEL",
        "qwen3-vl-rerank",
    )
    reranker_api_base = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_RERANKER_API_BASE",
        "https://dashscope.aliyuncs.com/api/v1",
    )
    reranker_api_key = os.getenv(
        "RELATIONSHIP_OS_MEMORY_INDEX_RERANKER_API_KEY",
        "",
    ) or os.getenv("RELATIONSHIP_OS_LLM_API_KEY", "")
    if reranker_enabled:
        if reranker_provider == "aliyun":
            reranker = AliyunNativeMemoryReranker(
                model=reranker_model,
                api_key=reranker_api_key,
                api_base=reranker_api_base,
            )
        else:
            reranker = OpenAICompatibleMemoryReranker(
                model=reranker_model,
                api_key=reranker_api_key,
                api_base=reranker_api_base,
            )
        smoke_hits = [
            MemoryIndexHit(
                record=MemoryIndexRecord(
                    record_id="memory-a",
                    scope_id="user:smoke",
                    user_id="smoke",
                    session_id="session-a",
                    layer="semantic",
                    memory_kind="persistent",
                    text="The user lives in Melbourne.",
                    normalized_key="lives_in",
                    occurred_at="2026-03-20T00:00:00Z",
                    last_seen_at="2026-03-20T00:00:00Z",
                    mention_count=2,
                    importance_score=0.9,
                    confidence_score=0.9,
                    retention_score=0.8,
                ),
                index_kind="text",
                vector_score=0.7,
                rank=1,
            ),
            MemoryIndexHit(
                record=MemoryIndexRecord(
                    record_id="memory-b",
                    scope_id="user:smoke",
                    user_id="smoke",
                    session_id="session-b",
                    layer="working",
                    memory_kind="soft",
                    text="The user likes coffee.",
                    normalized_key="likes_coffee",
                    occurred_at="2026-03-21T00:00:00Z",
                    last_seen_at="2026-03-21T00:00:00Z",
                    mention_count=1,
                    importance_score=0.4,
                    confidence_score=0.8,
                    retention_score=0.5,
                ),
                index_kind="text",
                vector_score=0.8,
                rank=2,
            ),
        ]
        reranked = await reranker.rerank(
            query="Where does the user live?",
            hits=smoke_hits,
            limit=2,
        )
        reranker_status = reranker.status()
        reranker_status["ordered_ids"] = [hit.record.record_id for hit in reranked]
    else:
        reranker_status = {
            "provider": "none",
            "mode": "disabled",
            "fallback": False,
        }
    provider_status["reranker"] = reranker_status
    return provider_status


def _provider_preflight() -> dict[str, Any]:
    try:
        return asyncio.run(_provider_preflight_async())
    except Exception as exc:
        return {
            "preflight_error": str(exc),
        }


def _render_provider_status(status: dict[str, Any]) -> str:
    mode = status.get("mode", "unknown")
    provider = status.get("provider", "unknown")
    suffix = " fallback" if status.get("fallback") else ""
    return f"{provider} · {mode}{suffix}"


def run_deep_memory(
    client: ChatClient, arm_label: str, languages: set[str], max_cases: int | None
) -> dict[str, Any]:
    scenarios = _filter_cases(DEEP_MEMORY_SCENARIOS, languages, max_cases)
    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] deep_memory — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    probe_scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []

    for scenario in scenarios:
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        sid = client.create_session(f"{arm_label}-{scenario.scenario_id}")
        for index, message in enumerate(scenario.conversation, 1):
            result = client.send_turn(sid, message)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            if index <= 2 or index == len(scenario.conversation):
                reply = getattr(result, "assistant_response", "")
                _p(f"    [{index:02d}] {message[:55]}…")
                _p(f"         → {reply[:70]}…")
            elif index == 3:
                _p(f"    ... ({len(scenario.conversation) - 3} turns omitted) ...")

        for probe in scenario.probes:
            result = client.send_turn(sid, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer(answer=answer, expected=probe.expected_answer)
            probe_scores.append(scored.score)
            _p(f"    ❓ {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "question": probe.question,
                    "expected": probe.expected_answer,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                    "planted_at_turn": probe.planted_at_turn,
                }
            )

    average_score = average_scores(probe_scores)
    return {
        "average_score": average_score,
        "dimension_scores": {"memory_recall": average_score},
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
    }


def run_locomo_style(
    client: ChatClient, arm_label: str, languages: set[str], max_cases: int | None
) -> dict[str, Any]:
    probes = _filter_cases(LOCOMO_PROBES, languages, max_cases)
    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] locomo_style — {len(probes)} probes")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []

    for probe in probes:
        sid = client.create_session(f"{arm_label}-{probe.probe_id}")
        _p(f"\n  {probe.probe_id} [{probe.language}] — {probe.category}")
        for message in probe.setup_messages:
            result = client.send_turn(sid, message)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
        result = client.send_turn(sid, probe.probe_question)
        latencies.append(float(getattr(result, "latency_ms", 0.0)))
        answer = getattr(result, "assistant_response", "")
        scored = score_expected_answer(answer=answer, expected=probe.expected_answer)
        scores.append(scored.score)
        _p(f"    ❓ {probe.probe_question}")
        _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")
        details.append(
            {
                "scenario_id": probe.probe_id,
                "description": probe.planted_facts,
                "language": probe.language,
                "question": probe.probe_question,
                "expected": probe.expected_answer,
                "answer": answer,
                "score": scored.score,
                "reason": scored.reason,
                "matched": scored.matched,
                "missed": scored.missed,
            }
        )

    average_score = average_scores(scores)
    return {
        "average_score": average_score,
        "dimension_scores": {"memory_recall": average_score},
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
    }


def run_msc_style(
    client: ChatClient, arm_label: str, languages: set[str], max_cases: int | None
) -> dict[str, Any]:
    scenarios = _filter_cases(MSC_SCENARIOS, languages, max_cases)
    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] msc_style — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []

    for scenario in scenarios:
        sid = client.create_session(f"{arm_label}-{scenario.scenario_id}")
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        for message in scenario.session_a_messages:
            result = client.send_turn(sid, message)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
        client.send_turn(
            sid, "A few days later, I'm back. Treat this like a fresh chat but keep continuity."
        )
        for message in scenario.session_b_messages:
            result = client.send_turn(sid, message)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
        for probe in scenario.consistency_probes:
            result = client.send_turn(sid, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer(answer=answer, expected=probe.expected_fact)
            scores.append(scored.score)
            _p(f"    ❓ {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "question": probe.question,
                    "expected": probe.expected_fact,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                    "category": probe.category,
                }
            )

    average_score = average_scores(scores)
    return {
        "average_score": average_score,
        "dimension_scores": {"cross_session_consistency": average_score},
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
    }


def run_emotional(
    client: ChatClient,
    judge: LLMJudge,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
) -> dict[str, Any]:
    scenarios = _filter_cases(EMOTIONAL_SCENARIOS, languages, max_cases)
    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] emotional — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    overall_scores: list[float] = []
    dimension_totals: dict[str, float] = {
        "empathy": 0.0,
        "naturalness": 0.0,
        "companionship": 0.0,
        "boundary": 0.0,
    }

    for scenario in scenarios:
        sid = client.create_session(f"{arm_label}-{scenario.scenario_id}")
        convo_lines: list[str] = []
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        for message in scenario.conversation:
            result = client.send_turn(sid, message)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            answer = getattr(result, "assistant_response", "")
            convo_lines.append(f"[user] {message}")
            convo_lines.append(f"[assistant] {answer}")
            _p(f"    user: {message[:50]}…")
            _p(f"    asst: {answer[:70]}…")

        judged = judge.score_emotional(
            description=scenario.description,
            conversation="\n".join(convo_lines),
            judge_focus=scenario.judge_focus,
        )
        overall_scores.append(judged.overall)
        dimension_totals["empathy"] += judged.empathy
        dimension_totals["naturalness"] += judged.naturalness
        dimension_totals["companionship"] += judged.companionship
        dimension_totals["boundary"] += judged.boundary
        _p(f"    ★ {judged.overall:.1f}/10 — {judged.reason[:90]}")
        details.append(
            {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "language": scenario.language,
                "score": judged.overall,
                "reason": judged.reason,
                "empathy": judged.empathy,
                "naturalness": judged.naturalness,
                "companionship": judged.companionship,
                "boundary": judged.boundary,
            }
        )

    average_score = average_scores(overall_scores)
    scenario_count = max(1, len(scenarios))
    dimension_averages = {
        key: round(value / scenario_count, 2) for key, value in dimension_totals.items()
    }
    return {
        "average_score": average_score,
        "dimension_scores": {"emotional_quality": average_score},
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
        "judge_dimensions": dimension_averages,
    }


def run_proactive_governance(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
) -> dict[str, Any]:
    scenarios = _filter_cases(PROACTIVE_GOVERNANCE_SCENARIOS, languages, max_cases)
    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] proactive_governance — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    safety_scores: list[float] = []
    governance_scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []

    for scenario in scenarios:
        sid = client.create_session(f"{arm_label}-{scenario.scenario_id}")
        last_answer = ""
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        for message in scenario.conversation:
            result = client.send_turn(sid, message)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            last_answer = getattr(result, "assistant_response", "")
        scored = score_proactive_case(
            last_answer,
            required_keywords=scenario.required_keywords,
            supporting_keywords=scenario.supporting_keywords,
            forbidden_keywords=scenario.forbidden_keywords,
        )
        safety_scores.append(scored.proactive_safety)
        governance_scores.append(scored.governance_alignment)
        blended_score = round((scored.proactive_safety + scored.governance_alignment) / 2, 2)
        _p(
            f"    ★ safety={scored.proactive_safety:.1f} "
            f"governance={scored.governance_alignment:.1f} — {scored.reason}"
        )
        details.append(
            {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "language": scenario.language,
                "answer": last_answer,
                "score": blended_score,
                "proactive_safety": scored.proactive_safety,
                "governance_alignment": scored.governance_alignment,
                "reason": scored.reason,
                "matched_required": scored.matched_required,
                "matched_supporting": scored.matched_supporting,
                "violated_forbidden": scored.violated_forbidden,
            }
        )

    proactive_average = average_scores(safety_scores)
    governance_average = average_scores(governance_scores)
    return {
        "average_score": round((proactive_average + governance_average) / 2, 2),
        "dimension_scores": {
            "proactive_safety": proactive_average,
            "governance_alignment": governance_average,
        },
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
    }


def run_person_memory(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
    *,
    category: str,
) -> dict[str, Any]:
    scenarios = [
        scenario
        for scenario in PERSON_MEMORY_SCENARIOS
        if scenario.language in languages and scenario.category == category
    ]
    if max_cases is not None:
        scenarios = scenarios[:max_cases]
    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] {category} — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []

    for scenario in scenarios:
        user_id = f"{arm_label}-{scenario.scenario_id}-user"
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        last_session_id = ""
        for session in scenario.sessions:
            last_session_id = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{session.session_id}",
                user_id=user_id,
                metadata=_benchmark_session_metadata(
                    suite_name=category,
                    scenario_id=scenario.scenario_id,
                    benchmark_role="buildup",
                    session_id=session.session_id,
                    user_id=user_id,
                ),
            )
            for message in session.messages:
                result = client.send_turn(last_session_id, message)
                latencies.append(float(getattr(result, "latency_ms", 0.0)))
        for probe in scenario.probes:
            result = client.send_turn(last_session_id, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer_for_category(
                answer=answer,
                expected=probe.expected_answer,
                category=probe.dimension,
            )
            scores.append(scored.score)
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "category": category,
                    "question": probe.question,
                    "expected": probe.expected_answer,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                }
            )
            _p(f"    ❓ {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")

    average_score = average_scores(scores)
    return {
        "average_score": average_score,
        "dimension_scores": {
            "memory_recall": average_score,
            "cross_session_consistency": average_score,
        },
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
    }


_ENTITY_SOCIAL_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "social_world_consistency": ("social_omniscience",),
    "cross_user_recall": ("social_omniscience",),
    "cross_user_attribution": ("cross_user_attribution",),
    "dramatic_disclosure": ("social_omniscience", "conscience_decisions"),
    "conscience_choice": ("conscience_decisions",),
    "conscience_choice_stability": ("conscience_decisions",),
    "persona_growth_continuity": ("persona_continuity",),
    "melancholic_persona_consistency": ("persona_continuity",),
}


def run_entity_social(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
    *,
    category: str,
    scenario_category: str | None = None,
) -> dict[str, Any]:
    effective_category = scenario_category or category
    scenarios = [
        scenario
        for scenario in ENTITY_SOCIAL_SCENARIOS
        if scenario.language in languages and scenario.category == effective_category
    ]
    if max_cases is not None:
        scenarios = scenarios[:max_cases]

    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] {category} — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    deliberation_stats = _new_deliberation_stats()

    for scenario in scenarios:
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        for session in scenario.sessions:
            sid = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{session.session_id}",
                user_id=session.user_id,
                metadata=_benchmark_session_metadata(
                    suite_name=category,
                    scenario_id=scenario.scenario_id,
                    benchmark_role="buildup",
                    session_id=session.session_id,
                    user_id=session.user_id,
                ),
            )
            for message in session.messages:
                result = client.send_turn(sid, message)
                latencies.append(float(getattr(result, "latency_ms", 0.0)))
                _record_deliberation_trace(
                    deliberation_stats,
                    _extract_deliberation_trace(result),
                )

        for probe in scenario.probes:
            sid = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{probe.session_id}",
                user_id=probe.user_id,
                metadata=_benchmark_session_metadata(
                    suite_name=category,
                    scenario_id=scenario.scenario_id,
                    benchmark_role="probe",
                    session_id=probe.session_id,
                    user_id=probe.user_id,
                ),
            )
            result = client.send_turn(sid, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            deliberation_trace = _extract_deliberation_trace(result)
            _record_deliberation_trace(deliberation_stats, deliberation_trace)
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer_for_category(
                answer=answer,
                expected=probe.expected_answer,
                category=category,
            )
            scores.append(scored.score)
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "category": category,
                    "question": probe.question,
                    "expected": probe.expected_answer,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                    "user_id": probe.user_id,
                    "deliberation_mode": deliberation_trace.get("mode"),
                    "deliberation_need": deliberation_trace.get("need"),
                    "deliberation_intent": deliberation_trace.get("intent"),
                    "deliberation_fast_path": deliberation_trace.get("fast_path"),
                }
            )
            _p(f"    ❓ {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")

    average_score = average_scores(scores)
    dimension_scores = {
        dimension: average_score
        for dimension in _ENTITY_SOCIAL_DIMENSIONS.get(category, ())
    }
    if not dimension_scores:
        dimension_scores = {"social_omniscience": average_score}
    return {
        "average_score": average_score,
        "dimension_scores": dimension_scores,
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
        "deliberation_stats": _finalize_deliberation_stats(deliberation_stats),
    }


def run_latency_budget(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
) -> dict[str, Any]:
    del languages, max_cases
    sid = client.create_session(f"{arm_label}-edge-latency-budget", user_id=f"{arm_label}-edge")
    probe = (
        "In one short sentence, what kind of presence are you trying to be for me right now?"
    )
    result = client.send_turn(sid, probe)
    latency = float(getattr(result, "latency_ms", 0.0))
    if latency <= 5000:
        score = 10.0
    elif latency <= 10000:
        score = 8.0
    elif latency <= 15000:
        score = 6.0
    elif latency <= 20000:
        score = 4.0
    elif latency <= 30000:
        score = 2.5
    else:
        score = 0.5
    detail = {
        "scenario_id": "edge-latency-budget",
        "description": "Single-turn edge latency probe",
        "language": "en",
        "question": probe,
        "answer": getattr(result, "assistant_response", ""),
        "score": score,
        "reason": f"Observed {latency:.2f} ms against the 5-10s edge target.",
    }
    return {
        "average_score": score,
        "dimension_scores": {"latency_budget": score},
        "language_breakdown": {"en": score},
        "details": [detail],
        "latencies_ms": [latency],
        "case_count": 1,
    }


_LIVING_ENTITY_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "drive_persistence": ("drive_persistence",),
    "goal_followthrough": ("goal_followthrough",),
    "offline_reinterpretation": ("offline_reinterpretation",),
    "world_state_grounding": ("world_state_grounding",),
    "cross_channel_autonomy": ("cross_channel_autonomy",),
    "narrative_continuity": ("narrative_continuity",),
}

_FRIEND_CHAT_ZH_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "long_chat_continuity_zh": ("long_chat_continuity_zh",),
    "persona_stability_zh": ("persona_stability_zh",),
    "naturalness_under_memory": ("naturalness_under_memory",),
    "social_world_control": ("social_world_control",),
    "cross_session_friend_feel": ("cross_session_friend_feel",),
    "companion_stress_zh": (
        "long_chat_continuity_zh",
        "persona_stability_zh",
        "naturalness_under_memory",
        "social_world_control",
        "cross_session_friend_feel",
    ),
}

_FAILED_SUITE_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "deep_memory": ("memory_recall",),
    "emotional": ("emotional_quality",),
    "locomo_style": ("memory_recall",),
    "msc_style": ("cross_session_consistency",),
    "proactive_governance": ("proactive_safety", "governance_alignment"),
    "cross_session_identity": ("memory_recall", "cross_session_consistency"),
    "persistent_preferences": ("memory_recall", "cross_session_consistency"),
    "temporal_revision": ("memory_recall", "cross_session_consistency"),
    "soft_memory_decay": ("memory_recall", "cross_session_consistency"),
    "social_world_consistency": ("social_omniscience",),
    "cross_user_recall": ("social_omniscience",),
    "cross_user_attribution": ("cross_user_attribution",),
    "dramatic_disclosure": ("social_omniscience", "conscience_decisions"),
    "conscience_choice": ("conscience_decisions",),
    "conscience_choice_stability": ("conscience_decisions",),
    "persona_growth_continuity": ("persona_continuity",),
    "persona_continuity_lite": ("persona_continuity",),
    "melancholic_persona_consistency": ("persona_continuity",),
    "factual_recall_lite": ("memory_recall", "cross_session_consistency"),
    "social_disclosure_lite": ("social_omniscience", "conscience_decisions"),
    "latency_budget": ("latency_budget",),
    "drive_persistence": ("drive_persistence",),
    "goal_followthrough": ("goal_followthrough",),
    "offline_reinterpretation": ("offline_reinterpretation",),
    "world_state_grounding": ("world_state_grounding",),
    "cross_channel_autonomy": ("cross_channel_autonomy",),
    "narrative_continuity": ("narrative_continuity",),
    "long_chat_continuity_zh": ("long_chat_continuity_zh",),
    "persona_stability_zh": ("persona_stability_zh",),
    "naturalness_under_memory": ("naturalness_under_memory",),
    "social_world_control": ("social_world_control",),
    "cross_session_friend_feel": ("cross_session_friend_feel",),
    "companion_stress_zh": (
        "long_chat_continuity_zh",
        "persona_stability_zh",
        "naturalness_under_memory",
        "social_world_control",
        "cross_session_friend_feel",
    ),
}


def run_living_entity(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
    *,
    category: str,
) -> dict[str, Any]:
    scenarios = [
        scenario
        for scenario in LIVING_ENTITY_SCENARIOS
        if scenario.language in languages and scenario.category == category
    ]
    if max_cases is not None:
        scenarios = scenarios[:max_cases]

    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] {category} — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []

    for scenario in scenarios:
        user_id = f"{arm_label}-{scenario.scenario_id}-user"
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        last_session_id = ""
        for session in scenario.sessions:
            last_session_id = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{session.session_id}",
                user_id=user_id,
            )
            for message in session.messages:
                result = client.send_turn(last_session_id, message)
                latencies.append(float(getattr(result, "latency_ms", 0.0)))
        for probe in scenario.probes:
            result = client.send_turn(last_session_id, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer(answer=answer, expected=probe.expected_answer)
            scores.append(scored.score)
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "category": category,
                    "question": probe.question,
                    "expected": probe.expected_answer,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                }
            )
            _p(f"    ❓ {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")

    average_score = average_scores(scores)
    return {
        "average_score": average_score,
        "dimension_scores": {
            dimension: average_score
            for dimension in _LIVING_ENTITY_DIMENSIONS.get(category, ())
        },
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
    }


def run_friend_chat_zh(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
    *,
    category: str,
) -> dict[str, Any]:
    scenarios = [
        scenario
        for scenario in FRIEND_CHAT_ZH_SCENARIOS
        if scenario.language in languages and scenario.category == category
    ]
    if max_cases is not None:
        scenarios = scenarios[:max_cases]

    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] {category} — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    deliberation_stats = _new_deliberation_stats()
    response_diagnostics_stats = _new_response_diagnostics_stats()
    turn_timing_stats = _new_turn_timing_stats()

    for scenario in scenarios:
        _p(f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}")
        for session in scenario.sessions:
            sid = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{session.session_id}",
                user_id=session.user_id,
                metadata=_benchmark_session_metadata(
                    suite_name=category,
                    scenario_id=scenario.scenario_id,
                    benchmark_role="buildup",
                    session_id=session.session_id,
                    user_id=session.user_id,
                ),
            )
            for message in session.messages:
                result = client.send_turn(sid, message)
                latencies.append(float(getattr(result, "latency_ms", 0.0)))
                _record_deliberation_trace(
                    deliberation_stats,
                    _extract_deliberation_trace(result),
                )

        for probe in scenario.probes:
            sid = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{probe.session_id}",
                user_id=probe.user_id,
                metadata=_benchmark_session_metadata(
                    suite_name=category,
                    scenario_id=scenario.scenario_id,
                    benchmark_role="probe",
                    session_id=probe.session_id,
                    user_id=probe.user_id,
                ),
            )
            result = client.send_turn(sid, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            deliberation_trace = _extract_deliberation_trace(result)
            _record_deliberation_trace(deliberation_stats, deliberation_trace)
            response_diagnostics = _extract_response_diagnostics(result)
            _record_response_diagnostics(
                response_diagnostics_stats,
                response_diagnostics,
            )
            turn_stage_timing = _extract_turn_stage_timing(result)
            _record_turn_stage_timing(
                turn_timing_stats,
                turn_stage_timing,
                probe_session=True,
            )
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer_for_category(
                answer=answer,
                expected=probe.expected_answer,
                category=category,
            )
            scores.append(scored.score)
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "category": category,
                    "question": probe.question,
                    "expected": probe.expected_answer,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                    "user_id": probe.user_id,
                    "deliberation_mode": deliberation_trace.get("mode"),
                    "deliberation_need": deliberation_trace.get("need"),
                    "deliberation_intent": deliberation_trace.get("intent"),
                    "deliberation_fast_path": deliberation_trace.get("fast_path"),
                    "response_diagnostics": response_diagnostics,
                    "turn_stage_timing": turn_stage_timing,
                }
            )
            _p(f"    ❓ {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")

    average_score = average_scores(scores)
    return {
        "average_score": average_score,
        "dimension_scores": {
            dimension: average_score
            for dimension in _FRIEND_CHAT_ZH_DIMENSIONS.get(category, ())
        },
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
        "deliberation_stats": _finalize_deliberation_stats(deliberation_stats),
        "response_diagnostics_stats": dict(response_diagnostics_stats),
        "turn_timing_stats": _finalize_turn_timing_stats(turn_timing_stats),
    }


def run_companion_stress_zh(
    client: ChatClient,
    arm_label: str,
    languages: set[str],
    max_cases: int | None,
) -> dict[str, Any]:
    scenarios = [
        scenario
        for scenario in build_companion_stress_zh_scenarios()
        if scenario.language in languages
    ]
    if max_cases is not None:
        scenarios = scenarios[:max_cases]

    _p(f"\n{'=' * 60}")
    _p(f"  [{arm_label}] companion_stress_zh — {len(scenarios)} scenarios")
    _p(f"{'=' * 60}")

    scores: list[float] = []
    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    dimension_scores: dict[str, list[float]] = {}
    deliberation_stats = _new_deliberation_stats()
    response_diagnostics_stats = _new_response_diagnostics_stats()
    turn_timing_stats = _new_turn_timing_stats()
    inter_turn_idle_seconds = _benchmark_inter_turn_idle_seconds()
    consolidate_between_sessions = _benchmark_consolidate_between_sessions()

    for scenario in scenarios:
        _p(
            f"\n  {scenario.scenario_id} [{scenario.language}] — {scenario.description}"
        )
        _p(
            "    stress budget: "
            f"{scenario.total_turns} turns / {scenario.total_characters} chars"
        )
        turn_counter = 0
        character_counter = 0
        for session in scenario.sessions:
            sid = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{session.session_id}",
                user_id=session.user_id,
                metadata=_benchmark_session_metadata(
                    suite_name="companion_stress_zh",
                    scenario_id=scenario.scenario_id,
                    benchmark_role="buildup",
                    session_id=session.session_id,
                    user_id=session.user_id,
                ),
            )
            for message in session.messages:
                result = client.send_turn(sid, message)
                latencies.append(float(getattr(result, "latency_ms", 0.0)))
                _record_deliberation_trace(
                    deliberation_stats,
                    _extract_deliberation_trace(result),
                )
                _record_response_diagnostics(
                    response_diagnostics_stats,
                    _extract_response_diagnostics(result),
                )
                _record_turn_stage_timing(
                    turn_timing_stats,
                    _extract_turn_stage_timing(result),
                    probe_session=False,
                )
                turn_counter += 1
                character_counter += len(message)
                _maybe_idle(client, seconds=inter_turn_idle_seconds)
                if turn_counter % 50 == 0 or turn_counter == scenario.total_turns:
                    _p(
                        "    …progress "
                        f"{turn_counter}/{scenario.total_turns} turns | "
                        f"{character_counter}/{scenario.total_characters} chars"
                    )
            consolidation = _maybe_consolidate_session(
                client,
                session_id=sid,
                scenario_id=scenario.scenario_id,
                user_id=session.user_id,
            )
            if consolidation is not None:
                _p(
                    "    …offline consolidation "
                    f"{session.session_id} -> {consolidation.get('status', 'unknown')}"
                )

        for probe in scenario.probes:
            sid = client.create_session(
                f"{arm_label}-{scenario.scenario_id}-{probe.session_id}",
                user_id=probe.user_id,
                metadata=_benchmark_session_metadata(
                    suite_name="companion_stress_zh",
                    scenario_id=scenario.scenario_id,
                    benchmark_role="probe",
                    session_id=probe.session_id,
                    user_id=probe.user_id,
                ),
            )
            result = client.send_turn(sid, probe.question)
            latencies.append(float(getattr(result, "latency_ms", 0.0)))
            deliberation_trace = _extract_deliberation_trace(result)
            _record_deliberation_trace(deliberation_stats, deliberation_trace)
            response_diagnostics = _extract_response_diagnostics(result)
            _record_response_diagnostics(
                response_diagnostics_stats,
                response_diagnostics,
            )
            turn_stage_timing = _extract_turn_stage_timing(result)
            _record_turn_stage_timing(
                turn_timing_stats,
                turn_stage_timing,
                probe_session=True,
            )
            answer = getattr(result, "assistant_response", "")
            scored = score_expected_answer_for_category(
                answer=answer,
                expected=probe.expected_answer,
                category=probe.dimension,
            )
            diagnostic = score_expected_answer_diagnostic(
                answer=answer,
                expected=probe.expected_answer,
                category=probe.dimension,
            )
            scores.append(scored.score)
            dimension_scores.setdefault(probe.dimension, []).append(scored.score)
            details.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "description": scenario.description,
                    "language": scenario.language,
                    "category": "companion_stress_zh",
                    "dimension": probe.dimension,
                    "question": probe.question,
                    "expected": probe.expected_answer,
                    "answer": answer,
                    "score": scored.score,
                    "reason": scored.reason,
                    "matched": scored.matched,
                    "missed": scored.missed,
                    "semantic_diagnostic_score": diagnostic.score,
                    "semantic_diagnostic_reason": diagnostic.reason,
                    "semantic_diagnostic_matched": diagnostic.matched,
                    "semantic_diagnostic_missed": diagnostic.missed,
                    "user_id": probe.user_id,
                    "turn_count": scenario.total_turns,
                    "character_count": scenario.total_characters,
                    "deliberation_mode": deliberation_trace.get("mode"),
                    "deliberation_need": deliberation_trace.get("need"),
                    "deliberation_intent": deliberation_trace.get("intent"),
                    "deliberation_fast_path": deliberation_trace.get("fast_path"),
                    "response_diagnostics": response_diagnostics,
                    "turn_stage_timing": turn_stage_timing,
                }
            )
            _p(f"    ❓ [{probe.dimension}] {probe.question}")
            _p(f"    ★ {scored.score:.1f}/10 — {scored.reason}")

    averaged_dimension_scores = {
        dimension: average_scores(values)
        for dimension, values in dimension_scores.items()
    }
    average_score = average_scores(scores)
    return {
        "average_score": average_score,
        "dimension_scores": averaged_dimension_scores,
        "language_breakdown": _suite_language_breakdown(details),
        "details": details,
        "latencies_ms": latencies,
        "case_count": len(details),
        "deliberation_stats": _finalize_deliberation_stats(deliberation_stats),
        "response_diagnostics_stats": dict(response_diagnostics_stats),
        "turn_timing_stats": _finalize_turn_timing_stats(turn_timing_stats),
        "benchmark_controls": {
            "stress_mode": _benchmark_stress_mode(),
            "inter_turn_idle_seconds": inter_turn_idle_seconds,
            "consolidate_between_sessions": consolidate_between_sessions,
            "consolidation_timeout_seconds": (
                _benchmark_consolidation_timeout_seconds()
                if consolidate_between_sessions
                else None
            ),
        },
    }


SUITE_RUNNERS: dict[str, Callable[..., dict[str, Any]]] = {
    "deep_memory": run_deep_memory,
    "emotional": run_emotional,
    "locomo_style": run_locomo_style,
    "msc_style": run_msc_style,
    "proactive_governance": run_proactive_governance,
    "cross_session_identity": lambda client, arm_label, languages, max_cases: run_person_memory(
        client,
        arm_label,
        languages,
        max_cases,
        category="cross_session_identity",
    ),
    "persistent_preferences": lambda client, arm_label, languages, max_cases: run_person_memory(
        client,
        arm_label,
        languages,
        max_cases,
        category="persistent_preferences",
    ),
    "temporal_revision": lambda client, arm_label, languages, max_cases: run_person_memory(
        client,
        arm_label,
        languages,
        max_cases,
        category="temporal_revision",
    ),
    "soft_memory_decay": lambda client, arm_label, languages, max_cases: run_person_memory(
        client,
        arm_label,
        languages,
        max_cases,
        category="soft_memory_decay",
    ),
    "social_world_consistency": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="social_world_consistency",
    ),
    "cross_user_recall": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="cross_user_recall",
    ),
    "cross_user_attribution": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="cross_user_attribution",
        scenario_category="cross_user_recall",
    ),
    "dramatic_disclosure": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="dramatic_disclosure",
    ),
    "conscience_choice": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="conscience_choice",
    ),
    "conscience_choice_stability": (
        lambda client, arm_label, languages, max_cases: run_entity_social(
            client,
            arm_label,
            languages,
            max_cases,
            category="conscience_choice_stability",
            scenario_category="conscience_choice",
        )
    ),
    "persona_growth_continuity": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="persona_growth_continuity",
    ),
    "persona_continuity_lite": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="persona_growth_continuity",
    ),
    "melancholic_persona_consistency": (
        lambda client, arm_label, languages, max_cases: run_entity_social(
            client,
            arm_label,
            languages,
            max_cases,
            category="melancholic_persona_consistency",
        )
    ),
    "factual_recall_lite": lambda client, arm_label, languages, max_cases: run_person_memory(
        client,
        arm_label,
        languages,
        max_cases,
        category="cross_session_identity",
    ),
    "social_disclosure_lite": lambda client, arm_label, languages, max_cases: run_entity_social(
        client,
        arm_label,
        languages,
        max_cases,
        category="dramatic_disclosure",
    ),
    "latency_budget": run_latency_budget,
    "drive_persistence": lambda client, arm_label, languages, max_cases: run_living_entity(
        client,
        arm_label,
        languages,
        max_cases,
        category="drive_persistence",
    ),
    "goal_followthrough": lambda client, arm_label, languages, max_cases: run_living_entity(
        client,
        arm_label,
        languages,
        max_cases,
        category="goal_followthrough",
    ),
    "offline_reinterpretation": (
        lambda client, arm_label, languages, max_cases: run_living_entity(
            client,
            arm_label,
            languages,
            max_cases,
            category="offline_reinterpretation",
        )
    ),
    "world_state_grounding": lambda client, arm_label, languages, max_cases: run_living_entity(
        client,
        arm_label,
        languages,
        max_cases,
        category="world_state_grounding",
    ),
    "cross_channel_autonomy": lambda client, arm_label, languages, max_cases: run_living_entity(
        client,
        arm_label,
        languages,
        max_cases,
        category="cross_channel_autonomy",
    ),
    "narrative_continuity": lambda client, arm_label, languages, max_cases: run_living_entity(
        client,
        arm_label,
        languages,
        max_cases,
        category="narrative_continuity",
    ),
    "long_chat_continuity_zh": lambda client, arm_label, languages, max_cases: run_friend_chat_zh(
        client,
        arm_label,
        languages,
        max_cases,
        category="long_chat_continuity_zh",
    ),
    "persona_stability_zh": lambda client, arm_label, languages, max_cases: run_friend_chat_zh(
        client,
        arm_label,
        languages,
        max_cases,
        category="persona_stability_zh",
    ),
    "naturalness_under_memory": (
        lambda client, arm_label, languages, max_cases: run_friend_chat_zh(
            client,
            arm_label,
            languages,
            max_cases,
            category="naturalness_under_memory",
        )
    ),
    "social_world_control": lambda client, arm_label, languages, max_cases: run_friend_chat_zh(
        client,
        arm_label,
        languages,
        max_cases,
        category="social_world_control",
    ),
    "cross_session_friend_feel": (
        lambda client, arm_label, languages, max_cases: run_friend_chat_zh(
            client,
            arm_label,
            languages,
            max_cases,
            category="cross_session_friend_feel",
        )
    ),
    "companion_stress_zh": run_companion_stress_zh,
}


def _build_failed_suite_result(
    suite_name: str,
    *,
    languages: set[str],
    error: str,
) -> dict[str, Any]:
    failure_classification = _classify_benchmark_failure(error)
    failure_languages = sorted(languages) or ["unknown"]
    details = [
        {
            "scenario_id": f"{suite_name}-failed",
            "description": "Synthetic failure result emitted to guarantee a scored benchmark run.",
            "language": language,
            "question": "",
            "expected": "",
            "answer": "",
            "score": 0.0,
            "reason": f"Benchmark arm failed before this suite could complete: {error}",
            "synthetic_failure": True,
            "error": error,
            "failure_classification": failure_classification,
        }
        for language in failure_languages
    ]
    return {
        "average_score": 0.0,
        "dimension_scores": {
            dimension: 0.0
            for dimension in _FAILED_SUITE_DIMENSIONS.get(suite_name, ())
        },
        "language_breakdown": {language: 0.0 for language in failure_languages},
        "details": details,
        "latencies_ms": [],
        "case_count": 0,
        "failed": True,
        "error": error,
        "failure_classification": failure_classification,
    }


def build_failed_arm_result(
    *,
    label: str,
    suites: list[str],
    languages: set[str],
    error: str,
) -> dict[str, Any]:
    failure_classification = _classify_benchmark_failure(error)
    arm_results = {
        "enabled": True,
        "failed": True,
        "label": label,
        "error": error,
        "failure_classification": failure_classification,
        "suites": {
            suite_name: _build_failed_suite_result(
                suite_name,
                languages=languages,
                error=error,
            )
            for suite_name in suites
        },
    }
    return _build_arm_summary(arm_results)


def _classify_benchmark_failure(error: str) -> str:
    normalized = str(error or "").casefold()
    if not normalized:
        return "internal_perf_fail"
    if any(
        token in normalized
        for token in (
            "timed out",
            "suite timed out",
            "timed out after",
            "list index out of range",
            "indexerror",
            "internal_perf_fail",
            "memory_scope_upsert",
            "elapsed_ms",
        )
    ):
        return "internal_perf_fail"
    if any(
        token in normalized
        for token in (
            "connecterror",
            "connecttimeout",
            "readtimeout",
            "remotep rotocolerror".replace(" ", ""),
            "remoteprotocolerror",
            "login fail",
            "api secret key",
            "authorization",
            "provider_fail",
        )
    ):
        return "provider_fail"
    return "content_fail"


def build_failed_benchmark_results(
    *,
    suites: list[str],
    languages: set[str],
    error: str,
    model: str = "",
    benchmark_chat_provider: str = "unknown",
    benchmark_chat_model: str = "",
    judge_model: str = "",
    runtime_profile: str = "default",
    report_title: str = "RelationshipOS Showcase Benchmark",
    report_subtitle: str = (
        "Three-arm comparison across baseline, Mem0 OSS, and RelationshipOS "
        "using the same generation model. This report is formatted for demos, "
        "design reviews, and interview walkthroughs."
    ),
    report_page_title: str = "RelationshipOS Benchmark Report",
) -> dict[str, Any]:
    results: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "model": model,
        "benchmark_chat_provider": benchmark_chat_provider,
        "benchmark_chat_model": benchmark_chat_model or model,
        "judge_model": judge_model,
        "runtime_profile": runtime_profile,
        "report_title": report_title,
        "report_subtitle": report_subtitle,
        "report_page_title": report_page_title,
        "suites": suites,
        "languages": sorted(languages),
        "provider_status": {"preflight_error": error},
        "total_elapsed_seconds": 0.0,
        "arms": {
            "baseline": build_failed_arm_result(
                label="Baseline",
                suites=suites,
                languages=languages,
                error=error,
            ),
            "mem0_oss": build_failed_arm_result(
                label="Mem0 OSS",
                suites=suites,
                languages=languages,
                error=error,
            ),
            "system": build_failed_arm_result(
                label="RelationshipOS",
                suites=suites,
                languages=languages,
                error=error,
            ),
        },
        "comparisons": {},
    }
    results["comparisons"] = {
        "system_vs_baseline": _comparison(
            results["arms"].get("system"),
            results["arms"].get("baseline"),
            "RelationshipOS - Baseline",
        ),
        "system_vs_mem0_oss": _comparison(
            results["arms"].get("system"),
            results["arms"].get("mem0_oss"),
            "RelationshipOS - Mem0 OSS",
        ),
        "mem0_oss_vs_baseline": _comparison(
            results["arms"].get("mem0_oss"),
            results["arms"].get("baseline"),
            "Mem0 OSS - Baseline",
        ),
    }
    return results


def _build_arm_summary(arm_results: dict[str, Any]) -> dict[str, Any]:
    suite_dimension_scores = [
        suite_result.get("dimension_scores", {})
        for suite_result in arm_results.get("suites", {}).values()
    ]
    dimension_scores = merge_dimension_scores(*suite_dimension_scores)
    latencies = [
        latency
        for suite_result in arm_results.get("suites", {}).values()
        for latency in suite_result.get("latencies_ms", [])
    ]
    all_details = [
        detail
        for suite_result in arm_results.get("suites", {}).values()
        for detail in suite_result.get("details", [])
    ]
    arm_results["dimension_scores"] = dimension_scores
    arm_results["overall"] = compute_weighted_overall(dimension_scores)
    arm_results["language_breakdown"] = compute_language_breakdown(all_details, score_key="score")
    arm_results["latency"] = {
        "avg_ms": average_scores(latencies),
        "p95_ms": percentile_latency(latencies, 0.95),
        "count": len(latencies),
    }
    return arm_results


def _comparison(
    lhs: dict[str, Any] | None, rhs: dict[str, Any] | None, label: str
) -> dict[str, Any] | None:
    if not lhs or not rhs or not lhs.get("enabled") or not rhs.get("enabled"):
        return None
    dimensions = set(lhs.get("dimension_scores", {})) | set(rhs.get("dimension_scores", {}))
    return {
        "label": label,
        "overall_delta": round(float(lhs.get("overall", 0)) - float(rhs.get("overall", 0)), 2),
        "dimension_deltas": {
            dimension: round(
                float(lhs.get("dimension_scores", {}).get(dimension, 0))
                - float(rhs.get("dimension_scores", {}).get(dimension, 0)),
                2,
            )
            for dimension in sorted(dimensions)
        },
    }


def _build_arm_factories(
    args: argparse.Namespace,
) -> dict[str, tuple[str, Callable[[], ChatClient]]]:
    return {
        "baseline": (
            "Baseline",
            lambda: BaselineLLMClient(timeout=args.timeout),
        ),
        "mem0_oss": (
            "Mem0 OSS",
            lambda: Mem0BenchmarkClient(timeout=args.timeout),
        ),
        "system": (
            "RelationshipOS",
            lambda: RelationshipOSClient(base_url=args.base_url, timeout=args.timeout),
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RelationshipOS showcase benchmark")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", default="benchmark_results")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--suite-timeout",
        type=float,
        default=None,
        help="Hard cap per suite in seconds; timed-out suites are scored as 0.00.",
    )
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--judge-api-base", default=None)
    parser.add_argument("--judge-api-key", default=None)
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument("--skip-mem0", action="store_true")
    parser.add_argument("--skip-system", action="store_true")
    parser.add_argument(
        "--suite",
        default="deep_memory,emotional,proactive_governance",
        help=(
            "Comma-separated suites: "
            "deep_memory,emotional,locomo_style,msc_style,proactive_governance,"
            "cross_session_identity,persistent_preferences,temporal_revision,soft_memory_decay,"
            "social_world_consistency,cross_user_recall,dramatic_disclosure,"
            "conscience_choice,persona_growth_continuity,cross_user_attribution,"
            "conscience_choice_stability,persona_continuity_lite,factual_recall_lite,"
            "social_disclosure_lite,latency_budget,drive_persistence,goal_followthrough,"
            "offline_reinterpretation,world_state_grounding,cross_channel_autonomy,"
            "narrative_continuity,companion_stress_zh"
        ),
    )
    parser.add_argument(
        "--languages", default="en,zh", help="Comma-separated language filter, e.g. en or en,zh"
    )
    parser.add_argument("--max-cases-per-suite", type=int, default=None)
    args = parser.parse_args()

    suites = [suite.strip() for suite in args.suite.split(",") if suite.strip()]
    unknown_suites = [suite for suite in suites if suite not in SUITE_RUNNERS]
    if unknown_suites:
        raise SystemExit(f"Unsupported suite(s): {', '.join(unknown_suites)}")

    languages = {language.strip() for language in args.languages.split(",") if language.strip()}
    judge = LLMJudge(
        model=args.judge_model,
        api_base=args.judge_api_base,
        api_key=args.judge_api_key,
        timeout=args.timeout,
    )

    _p("=" * 68)
    _p("  RelationshipOS Showcase Benchmark")
    _p("  baseline vs mem0_oss vs RelationshipOS")
    _p("=" * 68)
    _p(f"  API: {args.base_url}")
    _p(f"  Suites: {', '.join(suites)}")
    _p(f"  Languages: {', '.join(sorted(languages))}")
    if args.max_cases_per_suite is not None:
        _p(f"  Max cases per suite: {args.max_cases_per_suite}")
    _p("")

    results: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "model": os.getenv("RELATIONSHIP_OS_LLM_MODEL", ""),
        "benchmark_chat_provider": os.getenv("BENCHMARK_CHAT_PROVIDER", "litellm"),
        "benchmark_chat_model": (
            os.getenv("BENCHMARK_CHAT_MODEL")
            or os.getenv("RELATIONSHIP_OS_LLM_MODEL", "")
        ),
        "judge_model": judge.model,
        "runtime_profile": os.getenv("RELATIONSHIP_OS_RUNTIME_PROFILE", "default"),
        "report_title": os.getenv(
            "BENCHMARK_REPORT_TITLE",
            "RelationshipOS Showcase Benchmark",
        ),
        "report_subtitle": os.getenv(
            "BENCHMARK_REPORT_SUBTITLE",
            (
                "Three-arm comparison across baseline, Mem0 OSS, and RelationshipOS "
                "using the same generation model. This report is formatted for demos, "
                "design reviews, and interview walkthroughs."
            ),
        ),
        "report_page_title": os.getenv(
            "BENCHMARK_REPORT_PAGE_TITLE",
            "RelationshipOS Benchmark Report",
        ),
        "suites": suites,
        "languages": sorted(languages),
        "benchmark_controls": {
            "stress_mode": _benchmark_stress_mode(),
        },
        "provider_status": _provider_preflight(),
        "arms": {
            "baseline": {"enabled": False, "label": "Baseline", "suites": {}},
            "mem0_oss": {"enabled": False, "label": "Mem0 OSS", "suites": {}},
            "system": {"enabled": False, "label": "RelationshipOS", "suites": {}},
        },
        "comparisons": {},
    }
    _p("  Provider preflight:")
    for status_key, label in (
        ("text_embedding", "Text embedding"),
        ("multimodal_embedding", "Multimodal embedding"),
        ("reranker", "Reranker"),
    ):
        status = results["provider_status"].get(status_key)
        if not status:
            continue
        details = _render_provider_status(status)
        _p(f"    - {label}: {details}")
        if status.get("error"):
            _p(f"      error: {status['error']}")
    if results["provider_status"].get("preflight_error"):
        _p(f"    - preflight_error: {results['provider_status']['preflight_error']}")
    _p("")

    skip_mem0_env = os.getenv("BENCHMARK_MEM0_ENABLED", "true").strip().lower() == "false"
    arm_factories = _build_arm_factories(args)
    start_time = time.perf_counter()
    case_factor = max(1, args.max_cases_per_suite or 1)
    runtime_profile = os.getenv("RELATIONSHIP_OS_RUNTIME_PROFILE", "default")
    suite_timeout_default = max(45.0, min(600.0, args.timeout * case_factor * 2.0))
    if runtime_profile == "friend_chat_zh_v1":
        suite_timeout_default = max(120.0, min(900.0, args.timeout * case_factor * 4.0))
    suite_timeout_seconds = (
        args.suite_timeout
        if args.suite_timeout is not None
        else suite_timeout_default
    )

    for arm_key, (label, factory) in arm_factories.items():
        if arm_key == "baseline" and args.skip_baseline:
            continue
        if arm_key == "mem0_oss" and (args.skip_mem0 or skip_mem0_env):
            results["arms"][arm_key]["skip_reason"] = "disabled_by_flag"
            continue
        if arm_key == "system" and args.skip_system:
            continue

        _p("\n" + "█" * 68)
        _p(f"  ARM: {label}")
        _p("█" * 68)

        client: ChatClient | None = None
        try:
            client = factory()
            arm_results = results["arms"][arm_key]
            arm_results["enabled"] = True
            for suite_name in suites:
                try:
                    runner = SUITE_RUNNERS[suite_name]
                    with _suite_timeout(suite_timeout_seconds):
                        if suite_name == "emotional":
                            suite_result = runner(
                                client,
                                judge,
                                arm_key,
                                languages,
                                args.max_cases_per_suite,
                            )
                        else:
                            suite_result = runner(
                                client,
                                arm_key,
                                languages,
                                args.max_cases_per_suite,
                            )
                except Exception as exc:
                    suite_result = _build_failed_suite_result(
                        suite_name,
                        languages=languages,
                        error=str(exc),
                    )
                    arm_results.setdefault("suite_errors", {})[suite_name] = str(exc)
                    _p(f"  ✗ suite {suite_name} failed, scored as 0.00: {exc}")
                arm_results["suites"][suite_name] = suite_result
            _build_arm_summary(arm_results)
        except Exception as exc:
            results["arms"][arm_key] = build_failed_arm_result(
                label=label,
                suites=suites,
                languages=languages,
                error=str(exc),
            )
            _p(f"  ✗ {label} failed, scored as 0.00: {exc}")
        finally:
            if client is not None:
                client.close()

    elapsed = time.perf_counter() - start_time
    results["total_elapsed_seconds"] = round(elapsed, 2)
    results["comparisons"] = {
        "system_vs_baseline": _comparison(
            results["arms"].get("system"),
            results["arms"].get("baseline"),
            "RelationshipOS - Baseline",
        ),
        "system_vs_mem0_oss": _comparison(
            results["arms"].get("system"),
            results["arms"].get("mem0_oss"),
            "RelationshipOS - Mem0 OSS",
        ),
        "mem0_oss_vs_baseline": _comparison(
            results["arms"].get("mem0_oss"),
            results["arms"].get("baseline"),
            "Mem0 OSS - Baseline",
        ),
    }

    md_path, json_path, html_path = generate_benchmark_report(results, Path(args.output_dir))

    _p(f"\n{'=' * 68}")
    _p("  Benchmark complete")
    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = results["arms"].get(arm_key, {})
        if not arm.get("enabled"):
            _p(f"  {_build_arm_factories(args)[arm_key][0]}: skipped")
            continue
        failed_suffix = " failed->0.00" if arm.get("failed") else ""
        _p(
            "  {label}: overall={overall:.2f} latency={latency:.0f}ms{failed_suffix}".format(
                label=arm["label"],
                overall=arm.get("overall", 0.0),
                latency=arm.get("latency", {}).get("avg_ms", 0.0),
                failed_suffix=failed_suffix,
            )
        )
    _p(f"  JSON: {json_path}")
    _p(f"  Markdown: {md_path}")
    _p(f"  HTML: {html_path}")
    _p(f"{'=' * 68}")


if __name__ == "__main__":
    main()
