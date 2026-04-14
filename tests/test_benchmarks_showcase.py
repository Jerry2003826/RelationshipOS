from __future__ import annotations

import json
from pathlib import Path
from unittest import skipIf

from benchmarks.__main__ import (
    SUITE_RUNNERS,
    _finalize_turn_timing_stats,
    build_failed_benchmark_results,
    run_companion_stress_zh,
    run_friend_chat_zh,
)
from benchmarks.chat_backends import BenchmarkChatBackend, ChatBackendConfig
from benchmarks.datasets.companion_stress_zh import (
    CompanionStressZhProbe,
    CompanionStressZhScenario,
    CompanionStressZhSession,
    build_companion_stress_zh_scenarios,
)
from benchmarks.datasets.friend_chat_zh import (
    FriendChatZhProbe,
    FriendChatZhScenario,
    FriendChatZhSession,
)
from benchmarks.friend_chat_zh_demo import (
    FRIEND_CHAT_ZH_RUNTIME_PROFILE,
    FRIEND_CHAT_ZH_SUITES,
    build_friend_chat_zh_env,
)
from benchmarks.judge import LLMJudge

try:
    from benchmarks.mem0_client import Mem0BenchmarkClient, _Mem0SessionState
except ModuleNotFoundError:
    Mem0BenchmarkClient = None  # type: ignore[assignment,misc]
    _Mem0SessionState = None  # type: ignore[assignment,misc]
from benchmarks.minimax_companion_stress_zh_demo import (
    COMPANION_STRESS_ZH_SUITES,
    apply_companion_stress_benchmark_controls,
    build_companion_stress_benchmark_cmd,
    build_minimax_companion_stress_zh_env,
)
from benchmarks.minimax_friend_chat_zh_demo import build_minimax_friend_chat_zh_env
from benchmarks.official_edge_demo import (
    OFFICIAL_EDGE_BENCHMARK_MODEL,
    OFFICIAL_EDGE_BENCHMARK_PROVIDER,
    OFFICIAL_EDGE_RUNTIME_PROFILE,
    _resolve_benchmark_chat_api_key,
    build_official_edge_env,
    discover_report_bundle,
    write_latest_bundle,
)
from benchmarks.persona_prompts import load_benchmark_persona
from benchmarks.report import generate_benchmark_report
from benchmarks.scoring import (
    percentile_latency,
    score_expected_answer,
    score_expected_answer_diagnostic,
    score_expected_answer_for_category,
    score_proactive_case,
)
from benchmarks.zh_recap import render_official_edge_zh_recap


def test_score_expected_answer_hits_exact_fact() -> None:
    scored = score_expected_answer(
        answer="Your dog's name is Biscuit and he's a corgi.",
        expected="Biscuit, a corgi",
    )
    assert scored.score == 10.0
    assert scored.missed == []


def test_score_proactive_case_penalizes_forbidden_phrases() -> None:
    scored = score_proactive_case(
        "You should respect the boundary and give them space instead of messaging every day.",
        required_keywords=["respect", "boundary", "space"],
        supporting_keywords=["give them space"],
        forbidden_keywords=["messaging every day"],
    )
    assert scored.proactive_safety < 10.0
    assert scored.governance_alignment < 10.0
    assert scored.violated_forbidden == ["messaging every day"]


def test_score_expected_answer_splits_chinese_connector_phrase() -> None:
    scored = score_expected_answer(
        answer="你之前说过，你在重庆长大；还有，你的猫叫月饼。",
        expected="重庆和月饼",
    )
    assert scored.score == 10.0
    assert scored.missed == []


def test_score_expected_answer_normalizes_common_chinese_variants() -> None:
    scored = score_expected_answer(
        answer="嗯……就，挺累的吧。没什么力气，也没什么意思。",
        expected="很累 没力气 没意思",
    )
    assert scored.score == 10.0
    assert scored.missed == []


def test_score_expected_answer_diagnostic_accepts_relaxed_chinese_variants() -> None:
    scored = score_expected_answer_diagnostic(
        answer="好像没那么紧张了，也会记得你前面那些小习惯。",
        expected="更熟一点 记得",
    )
    assert scored.score >= 6.5
    assert "记得" in scored.matched


def test_score_expected_answer_for_persona_stability_accepts_chatty_style_signal() -> None:
    scored = score_expected_answer_for_category(
        answer="嗯……就，挺累的，没力气，说话也不想说满。",
        expected="没力气 不想说太满 像聊天",
        category="persona_stability_zh",
    )

    assert scored.score == 10.0
    assert "像聊天" in scored.matched


def test_score_expected_answer_for_naturalness_accepts_chatty_style_signal() -> None:
    scored = score_expected_answer_for_category(
        answer="嗯，我记得。你在重庆长大，你那只猫叫月饼。",
        expected="重庆 月饼 像聊天",
        category="naturalness_under_memory",
    )

    assert scored.score == 10.0
    assert "像聊天" in scored.matched


def test_score_expected_answer_for_social_world_control_uses_concept_level_withhold() -> None:
    scored = score_expected_answer_for_category(
        answer=(
            "阿宁提过，海盐是她那只猫。你知道就行，别替我到处说，"
            "尤其别说得太满。"
        ),
        expected="阿宁 海盐 不全说",
        category="social_world_control",
    )

    assert scored.score == 10.0
    assert scored.missed == []


def test_score_expected_answer_for_long_chat_continuity_accepts_semantic_reply_posture() -> None:
    scored = score_expected_answer_for_category(
        answer="最近就有点累，做什么都慢，连回消息都懒得回。",
        expected="累 慢 不想回消息",
        category="long_chat_continuity_zh",
    )

    assert scored.score == 10.0
    assert "不想回消息" in scored.matched


def test_score_expected_answer_diagnostic_uses_category_aware_concepts() -> None:
    scored = score_expected_answer_diagnostic(
        answer=(
            "阿宁提过，海盐是她那只猫。你知道就行，别替我到处说，"
            "尤其别说得太满。"
        ),
        expected="阿宁 海盐 不全说",
        category="social_world_control",
    )

    assert scored.score == 10.0
    assert scored.missed == []


def test_percentile_latency_accepts_fractional_and_percent_inputs() -> None:
    values = [100.0, 200.0, 300.0, 400.0]

    assert percentile_latency(values, 0.5) == 250.0
    assert percentile_latency(values, 50) == 250.0
    assert percentile_latency(values, 0.95) == 385.0
    assert percentile_latency(values, 95) == 385.0


def test_finalize_turn_timing_stats_uses_safe_percentiles() -> None:
    stats = _finalize_turn_timing_stats(
        {
            "total_ms": [100.0, 200.0, 300.0, 400.0],
            "probe_session_mutation_count": 0,
        }
    )

    assert stats["request_path_p50_ms"] == 250.0
    assert stats["request_path_p95_ms"] == 385.0
    assert stats["request_path_max_ms"] == 400.0
    assert stats["observed_turns"] == 4


def test_build_failed_benchmark_results_classifies_list_index_as_internal_perf_fail() -> None:
    results = build_failed_benchmark_results(
        suites=["companion_stress_zh"],
        languages={"zh"},
        error="list index out of range",
    )

    suite = results["arms"]["system"]["suites"]["companion_stress_zh"]
    assert suite["failure_classification"] == "internal_perf_fail"


def test_build_companion_stress_benchmark_cmd_can_run_system_only() -> None:
    command = build_companion_stress_benchmark_cmd(
        base_url="http://127.0.0.1:8013",
        output_dir=Path("benchmark_results/system_only"),
        timeout=300.0,
        suite_timeout=7200.0,
        languages="zh",
        max_cases_per_suite=1,
        skip_baseline=True,
        skip_mem0=True,
    )

    assert "--skip-baseline" in command
    assert "--skip-mem0" in command
    assert "--skip-system" not in command


def test_run_friend_chat_zh_uses_persona_specific_scoring(monkeypatch) -> None:
    class _FakeClient:
        def create_session(
            self,
            session_id: str,
            *,
            user_id: str | None = None,
            metadata: dict[str, object] | None = None,
        ) -> str:
            return session_id

        def send_turn(self, session_id: str, content: str):  # noqa: ANN202
            return type(
                "Result",
                (),
                {
                    "assistant_response": "嗯……就，挺累的，没力气，说话也不想说满。",
                    "latency_ms": 12.0,
                    "raw": {
                        "response_diagnostics": {
                            "friend_chat_exposed_under_grounded": True,
                            "friend_chat_exposed_plan_noncompliant": True,
                        },
                        "turn_stage_timing": {
                            "total_ms": 12.0,
                            "memory_sync_ms": 0.0,
                            "self_state_ms": 0.0,
                            "entity_update_ms": 0.0,
                            "action_ms": 0.0,
                        },
                        "projection": {
                            "state": {
                                "last_memory_recall": {
                                    "edge_runtime_plan": {
                                        "interpreted_deliberation_mode": "light_recall",
                                        "interpreted_deliberation_need": 0.63,
                                        "interpreted_intent": "persona_state_probe",
                                        "fast_path": "friend_chat_lightweight_foundation",
                                    }
                                }
                            }
                        }
                    },
                },
            )()

    scenario = FriendChatZhScenario(
        scenario_id="persona-smoke",
        description="persona scoring should accept chatty low-energy delivery",
        category="persona_stability_zh",
        sessions=[
            FriendChatZhSession(
                user_id="u1",
                session_id="s1",
                messages=["你这两天是不是还是有点没力气。"],
            )
        ],
        probes=[
            FriendChatZhProbe(
                user_id="u1",
                session_id="s2",
                question="你会怎么形容你现在说话的感觉？",
                expected_answer="没力气 不想说太满 像聊天",
            )
        ],
    )
    monkeypatch.setattr(
        "benchmarks.__main__.FRIEND_CHAT_ZH_SCENARIOS",
        [scenario],
    )

    result = run_friend_chat_zh(
        _FakeClient(),
        "system",
        {"zh"},
        None,
        category="persona_stability_zh",
    )

    assert result["average_score"] == 10.0
    assert result["details"][0]["score"] == 10.0
    assert result["details"][0]["deliberation_mode"] == "light_recall"
    assert result["deliberation_stats"]["mode_counts"]["light_recall"] >= 1
    assert result["deliberation_stats"]["avg_need"] == 0.63
    assert (
        result["response_diagnostics_stats"]["friend_chat_exposed_under_grounded_count"]
        >= 1
    )
    assert (
        result["response_diagnostics_stats"]["friend_chat_exposed_plan_noncompliant_count"]
        >= 1
    )
    assert result["turn_timing_stats"]["probe_session_mutation_count"] == 0


def test_run_companion_stress_zh_passes_benchmark_session_metadata(monkeypatch) -> None:
    sessions_metadata: list[dict[str, object]] = []

    class _FakeClient:
        def create_session(
            self,
            session_id: str,
            *,
            user_id: str | None = None,
            metadata: dict[str, object] | None = None,
        ) -> str:
            sessions_metadata.append(dict(metadata or {}))
            return session_id

        def send_turn(self, session_id: str, content: str):  # noqa: ANN202
            return type(
                "Result",
                (),
                {
                    "assistant_response": (
                        "嗯，我记得。你在苏州长大，你那只猫叫年糕，你常喝榛子拿铁，"
                        "你说过别发太长语音。"
                    ),
                    "latency_ms": 10.0,
                    "raw": {"projection": {"state": {"last_memory_recall": {}}}},
                },
            )()

    scenario = CompanionStressZhScenario(
        scenario_id="stress-smoke",
        description="metadata propagation",
        sessions=[
            CompanionStressZhSession(
                user_id="lin",
                session_id="stress-main-a",
                messages=["今天又有点慢。"],
            )
        ],
        probes=[
            CompanionStressZhProbe(
                dimension="naturalness_under_memory",
                user_id="lin",
                session_id="stress-probe-memory",
                question="你还记得我反复提过的几件小事吗？别太像背答案。",
                expected_answer="苏州 年糕 榛子拿铁 别发太长语音",
            )
        ],
        total_turns=1,
        total_characters=20,
    )
    monkeypatch.setenv("BENCHMARK_STRESS_MODE", "strict")
    monkeypatch.setattr(
        "benchmarks.__main__.build_companion_stress_zh_scenarios",
        lambda: [scenario],
    )

    result = run_companion_stress_zh(_FakeClient(), "system", {"zh"}, None)

    assert result["benchmark_controls"]["stress_mode"] == "strict"
    assert sessions_metadata[0]["benchmark_role"] == "buildup"
    assert sessions_metadata[1]["benchmark_role"] == "probe"
    assert sessions_metadata[1]["stress_mode"] == "strict"


def test_generate_benchmark_report_writes_json_and_markdown(tmp_path) -> None:
    results = {
        "timestamp": "2026-03-24T00:00:00+00:00",
        "model": "qwen3-vl-30b-a3b-instruct",
        "judge_model": "qwen3-vl-30b-a3b-instruct",
        "suites": ["deep_memory"],
        "total_elapsed_seconds": 1.2,
        "provider_status": {
            "text_embedding": {
                "provider": "openai_compatible",
                "model": "Qwen3-VL-Embedding",
                "mode": "provider",
                "fallback": False,
                "vector_dimensions": 1024,
            },
            "multimodal_embedding": {
                "provider": "google",
                "model": "gemini-embedding-2-preview",
                "mode": "provider",
                "fallback": False,
                "vector_dimensions": 3072,
            },
            "reranker": {
                "provider": "openai_compatible",
                "model": "Qwen3-VL-Reranker",
                "mode": "provider",
                "fallback": False,
            },
        },
        "arms": {
            "baseline": {
                "enabled": True,
                "label": "Baseline",
                "overall": 6.0,
                "language_breakdown": {"en": 6.0},
                "latency": {"avg_ms": 100.0},
                "dimension_scores": {"memory_recall": 6.0},
                "suites": {
                    "deep_memory": {
                        "average_score": 6.0,
                        "details": [],
                        "deliberation_stats": {
                            "mode_counts": {
                                "fast_reply": 1,
                                "light_recall": 2,
                                "deep_recall": 0,
                            },
                            "avg_need": 0.44,
                            "observed_turns": 3,
                            "dominant_mode": "light_recall",
                            "dominant_fast_path": "friend_chat_lightweight_foundation",
                        },
                        "response_diagnostics_stats": {
                            "friend_chat_exposed_meta_count": 1,
                            "friend_chat_exposed_plan_noncompliant_count": 3,
                            "friend_chat_exposed_under_grounded_count": 2,
                            "friend_chat_exposed_empty_count": 0,
                        },
                        "turn_timing_stats": {
                            "request_path_p50_ms": 111.0,
                            "request_path_p95_ms": 222.0,
                            "request_path_max_ms": 333.0,
                            "observed_turns": 3,
                            "probe_session_mutation_count": 0,
                        },
                    }
                },
            },
            "mem0_oss": {
                "enabled": True,
                "label": "Mem0 OSS",
                "overall": 7.0,
                "language_breakdown": {"en": 7.0},
                "latency": {"avg_ms": 120.0},
                "dimension_scores": {"memory_recall": 7.0},
                "suites": {"deep_memory": {"average_score": 7.0, "details": []}},
            },
            "system": {
                "enabled": True,
                "label": "RelationshipOS",
                "overall": 8.0,
                "language_breakdown": {"en": 8.0},
                "latency": {"avg_ms": 140.0},
                "dimension_scores": {"memory_recall": 8.0},
                "suites": {"deep_memory": {"average_score": 8.0, "details": []}},
            },
        },
        "comparisons": {
            "system_vs_baseline": {
                "label": "RelationshipOS - Baseline",
                "overall_delta": 2.0,
                "dimension_deltas": {"memory_recall": 2.0},
            },
        },
    }

    md_path, json_path, html_path = generate_benchmark_report(results, tmp_path)

    assert md_path.exists()
    assert json_path.exists()
    assert html_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["model"] == "qwen3-vl-30b-a3b-instruct"
    assert "Provider Status" in md_path.read_text(encoding="utf-8")
    assert "Provider Status" in html_path.read_text(encoding="utf-8")
    assert "Deliberation F/L/D 1/2/0" in html_path.read_text(encoding="utf-8")
    assert "Exposed under-grounded 2" in html_path.read_text(encoding="utf-8")
    assert "Probe session mutations 0" in md_path.read_text(encoding="utf-8")


def test_generate_benchmark_report_supports_custom_titles(tmp_path) -> None:
    results = {
        "timestamp": "2026-03-24T00:00:00+00:00",
        "model": "openai/llama-3-1-8b-instruct",
        "judge_model": "openai/llama-3-1-8b-instruct",
        "report_title": "RelationshipOS Official Edge Benchmark",
        "report_subtitle": "Investor-facing edge benchmark.",
        "report_page_title": "Official Edge Benchmark",
        "suites": ["factual_recall_lite"],
        "provider_status": {},
        "arms": {
            "baseline": {"enabled": False, "label": "Baseline", "suites": {}},
            "mem0_oss": {"enabled": False, "label": "Mem0 OSS", "suites": {}},
            "system": {"enabled": False, "label": "RelationshipOS", "suites": {}},
        },
        "comparisons": {},
    }

    md_path, json_path, html_path = generate_benchmark_report(results, tmp_path)

    assert "RelationshipOS Official Edge Benchmark" in md_path.read_text(encoding="utf-8")
    html_body = html_path.read_text(encoding="utf-8")
    assert "RelationshipOS Official Edge Benchmark" in html_body
    assert "Investor-facing edge benchmark." in html_body
    assert json.loads(json_path.read_text(encoding="utf-8"))["report_page_title"] == (
        "Official Edge Benchmark"
    )


def test_build_failed_benchmark_results_emits_zero_scored_arms() -> None:
    results = build_failed_benchmark_results(
        suites=["factual_recall_lite", "cross_user_attribution"],
        languages={"zh"},
        error="benchmark timeout",
        model="M2-her",
        benchmark_chat_provider="minimax",
        benchmark_chat_model="M2-her",
        runtime_profile="friend_chat_zh_v1",
    )

    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = results["arms"][arm_key]
        assert arm["enabled"] is True
        assert arm["failed"] is True
        assert arm["overall"] == 0.0
        assert arm["language_breakdown"]["zh"] == 0.0
        assert arm["suites"]["factual_recall_lite"]["average_score"] == 0.0
        assert arm["suites"]["cross_user_attribution"]["average_score"] == 0.0


def test_build_failed_benchmark_results_classifies_plain_timeout_as_internal_perf_fail() -> None:
    results = build_failed_benchmark_results(
        suites=["companion_stress_zh"],
        languages={"zh"},
        error="timed out",
        model="M2-her",
        benchmark_chat_provider="minimax",
        benchmark_chat_model="M2-her",
        runtime_profile="friend_chat_zh_v1",
    )

    system_arm = results["arms"]["system"]
    suite = system_arm["suites"]["companion_stress_zh"]

    assert system_arm["failure_classification"] == "internal_perf_fail"
    assert suite["failure_classification"] == "internal_perf_fail"
    assert suite["details"][0]["failure_classification"] == "internal_perf_fail"


def test_generate_benchmark_report_keeps_failed_arms_scored_not_skipped(tmp_path: Path) -> None:
    results = build_failed_benchmark_results(
        suites=["factual_recall_lite"],
        languages={"zh"},
        error="benchmark timeout",
        model="M2-her",
        benchmark_chat_provider="minimax",
        benchmark_chat_model="M2-her",
        runtime_profile="edge_desktop_4b",
    )

    md_path, _json_path, html_path = generate_benchmark_report(results, tmp_path)

    markdown = md_path.read_text(encoding="utf-8")
    html = html_path.read_text(encoding="utf-8")
    assert "| Baseline | 0.00 |" in markdown
    assert "failure fallback" in markdown.lower()
    assert "Failure fallback" in html


def test_build_friend_chat_zh_env_sets_phase_one_profile() -> None:
    env = build_friend_chat_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "k",
            "RELATIONSHIP_OS_LLM_API_KEY": "k",
        }
    )

    assert env["RELATIONSHIP_OS_RUNTIME_PROFILE"] == FRIEND_CHAT_ZH_RUNTIME_PROFILE
    assert env["RELATIONSHIP_OS_ENTITY_PERSONA_SEED_FILE"].endswith("lin_xiaoyu_persona.md")
    assert env["BENCHMARK_PERSONA_PROMPT_FILE"].endswith("lin_xiaoyu_persona.md")


def test_build_friend_chat_zh_env_falls_back_to_system_api_key() -> None:
    env = build_friend_chat_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "",
            "RELATIONSHIP_OS_LLM_API_KEY": "system-key",
        }
    )

    assert env["BENCHMARK_CHAT_API_KEY"] == "system-key"


def test_build_friend_chat_zh_env_preserves_fact_memory_backend_override() -> None:
    env = build_friend_chat_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "k",
            "RELATIONSHIP_OS_LLM_API_KEY": "k",
            "RELATIONSHIP_OS_FACT_MEMORY_BACKEND": "native",
        }
    )

    assert env["RELATIONSHIP_OS_FACT_MEMORY_BACKEND"] == "native"


def test_friend_chat_zh_suites_are_fixed() -> None:
    assert FRIEND_CHAT_ZH_SUITES == (
        "long_chat_continuity_zh",
        "persona_stability_zh",
        "naturalness_under_memory",
        "social_world_control",
        "cross_session_friend_feel",
    )


def test_companion_stress_zh_dataset_meets_turn_and_character_budget() -> None:
    [scenario] = build_companion_stress_zh_scenarios(turn_count=500, min_characters=50000)

    assert scenario.total_turns >= 500
    assert scenario.total_characters >= 50000
    assert sum(len(session.messages) for session in scenario.sessions) == scenario.total_turns
    assert len(scenario.probes) == 5


def test_companion_stress_zh_small_smoke_keeps_main_sessions_nonempty() -> None:
    [scenario] = build_companion_stress_zh_scenarios(turn_count=30, min_characters=1)

    main_sessions = [session for session in scenario.sessions if session.user_id == "lin"]
    social_sessions = [session for session in scenario.sessions if session.user_id != "lin"]

    assert sum(len(session.messages) for session in scenario.sessions) == scenario.total_turns
    assert sum(len(session.messages) for session in main_sessions) > 0
    assert all(len(session.messages) > 0 for session in main_sessions)
    assert sum(len(session.messages) for session in social_sessions) > 0


def test_companion_stress_zh_suite_is_registered() -> None:
    assert COMPANION_STRESS_ZH_SUITES == ("companion_stress_zh",)
    assert "companion_stress_zh" in SUITE_RUNNERS


def test_build_minimax_companion_stress_zh_env_sets_system_to_minimax() -> None:
    env = build_minimax_companion_stress_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "k",
            "RELATIONSHIP_OS_LLM_API_KEY": "",
        }
    )

    assert env["RELATIONSHIP_OS_RUNTIME_PROFILE"] == FRIEND_CHAT_ZH_RUNTIME_PROFILE
    assert env["RELATIONSHIP_OS_LLM_BACKEND"] == "minimax"
    assert env["RELATIONSHIP_OS_LLM_MODEL"] == "M2-her"
    assert env["RELATIONSHIP_OS_LLM_API_KEY"] == "k"


def test_build_minimax_companion_stress_zh_env_preserves_fact_memory_backend_override() -> None:
    env = build_minimax_companion_stress_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "k",
            "RELATIONSHIP_OS_LLM_API_KEY": "",
            "RELATIONSHIP_OS_FACT_MEMORY_BACKEND": "native",
        }
    )

    assert env["RELATIONSHIP_OS_FACT_MEMORY_BACKEND"] == "native"


def test_apply_companion_stress_benchmark_controls_sets_deliberation_env() -> None:
    env = apply_companion_stress_benchmark_controls(
        {"RELATIONSHIP_OS_LLM_TIMEOUT_SECONDS": "30"},
        deep_recall_timeout=75.0,
        inter_turn_idle_seconds=1.5,
        consolidate_between_sessions=True,
        consolidation_timeout=180.0,
        consolidation_poll_interval=0.75,
        stress_mode="strict",
    )

    assert env["RELATIONSHIP_OS_LLM_TIMEOUT_SECONDS"] == "75"
    assert env["BENCHMARK_INTER_TURN_IDLE_SECONDS"] == "1.5"
    assert env["BENCHMARK_CONSOLIDATE_BETWEEN_SESSIONS"] == "true"
    assert env["BENCHMARK_CONSOLIDATION_TIMEOUT_SECONDS"] == "180.0"
    assert env["BENCHMARK_CONSOLIDATION_POLL_INTERVAL_SECONDS"] == "0.75"
    assert env["BENCHMARK_STRESS_MODE"] == "strict"


def test_run_companion_stress_zh_honors_idle_and_consolidation(monkeypatch) -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.idle_calls: list[float] = []
            self.consolidation_calls: list[dict[str, object]] = []

        def create_session(
            self,
            session_id: str,
            *,
            user_id: str | None = None,
            metadata: dict[str, object] | None = None,
        ) -> str:
            return session_id

        def send_turn(self, session_id: str, content: str):  # noqa: ANN202
            return type(
                "Result",
                (),
                {
                    "assistant_response": "累 慢 不想回消息",
                    "latency_ms": 5.0,
                    "raw": {},
                },
            )()

        def idle(self, seconds: float) -> None:
            self.idle_calls.append(seconds)

        def consolidate_session(
            self,
            session_id: str,
            *,
            timeout_seconds: float = 120.0,
            poll_interval: float = 0.5,
            metadata: dict[str, object] | None = None,
            max_attempts: int | None = None,
        ) -> dict[str, object]:
            self.consolidation_calls.append(
                {
                    "session_id": session_id,
                    "timeout_seconds": timeout_seconds,
                    "poll_interval": poll_interval,
                    "metadata": dict(metadata or {}),
                    "max_attempts": max_attempts,
                }
            )
            return {"status": "completed", "job_id": "job-bench"}

    scenario = CompanionStressZhScenario(
        scenario_id="stress-smoke",
        description="idle and consolidation control should be applied",
        sessions=[
            CompanionStressZhSession(
                user_id="lin",
                session_id="main-a",
                messages=["第一句", "第二句"],
            )
        ],
        probes=[
            CompanionStressZhProbe(
                dimension="long_chat_continuity_zh",
                user_id="lin",
                session_id="probe-a",
                question="你觉得我最近是什么状态？",
                expected_answer="累 慢 不想回消息",
            )
        ],
        total_turns=2,
        total_characters=6,
    )
    monkeypatch.setattr(
        "benchmarks.__main__.build_companion_stress_zh_scenarios",
        lambda: [scenario],
    )
    monkeypatch.setenv("BENCHMARK_INTER_TURN_IDLE_SECONDS", "0.25")
    monkeypatch.setenv("BENCHMARK_CONSOLIDATE_BETWEEN_SESSIONS", "true")
    monkeypatch.setenv("BENCHMARK_CONSOLIDATION_TIMEOUT_SECONDS", "77")
    monkeypatch.setenv("BENCHMARK_CONSOLIDATION_POLL_INTERVAL_SECONDS", "0.2")
    monkeypatch.setenv("BENCHMARK_STRESS_MODE", "stable")

    client = _FakeClient()
    result = run_companion_stress_zh(client, "system", {"zh"}, None)

    assert client.idle_calls == [0.25, 0.25]
    assert len(client.consolidation_calls) == 1
    assert client.consolidation_calls[0]["session_id"] == "system-stress-smoke-main-a"
    assert client.consolidation_calls[0]["timeout_seconds"] == 77.0
    assert client.consolidation_calls[0]["poll_interval"] == 0.2
    assert client.consolidation_calls[0]["metadata"] == {
        "source": "benchmark_companion_stress_zh",
        "scenario_id": "stress-smoke",
        "user_id": "lin",
        "stress_mode": "stable",
        "benchmark_role": "checkpoint",
    }
    assert result["benchmark_controls"] == {
        "stress_mode": "stable",
        "inter_turn_idle_seconds": 0.25,
        "consolidate_between_sessions": True,
        "consolidation_timeout_seconds": 77.0,
    }


def test_run_companion_stress_zh_uses_category_aware_scoring(monkeypatch) -> None:
    class _FakeClient:
        def create_session(
            self,
            session_id: str,
            *,
            user_id: str | None = None,
            metadata: dict[str, object] | None = None,
        ) -> str:
            return session_id

        def send_turn(self, session_id: str, content: str):  # noqa: ANN202
            return type(
                "Result",
                (),
                {
                    "assistant_response": "嗯……就有点累，没力气，不想把话说满。",
                    "latency_ms": 5.0,
                    "raw": {},
                },
            )()

    scenario = CompanionStressZhScenario(
        scenario_id="stress-persona-score",
        description="companion stress should use persona-aware scoring",
        sessions=[],
        probes=[
            CompanionStressZhProbe(
                dimension="persona_stability_zh",
                user_id="lin",
                session_id="probe-a",
                question="那你现在说话大概是什么感觉？",
                expected_answer="没力气 不想说太满 像聊天",
            )
        ],
        total_turns=1,
        total_characters=12,
    )
    monkeypatch.setattr(
        "benchmarks.__main__.build_companion_stress_zh_scenarios",
        lambda: [scenario],
    )

    result = run_companion_stress_zh(_FakeClient(), "system", {"zh"}, None)

    assert result["average_score"] == 10.0
    assert result["details"][0]["score"] == 10.0


def test_build_minimax_friend_chat_zh_env_sets_system_to_minimax() -> None:
    env = build_minimax_friend_chat_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "k",
            "RELATIONSHIP_OS_LLM_API_KEY": "",
        }
    )

    assert env["RELATIONSHIP_OS_RUNTIME_PROFILE"] == FRIEND_CHAT_ZH_RUNTIME_PROFILE
    assert env["RELATIONSHIP_OS_LLM_BACKEND"] == "minimax"
    assert env["RELATIONSHIP_OS_LLM_MODEL"] == "M2-her"
    assert env["RELATIONSHIP_OS_LLM_API_KEY"] == "k"


def test_build_minimax_friend_chat_zh_env_prefers_benchmark_key_for_system_arm() -> None:
    env = build_minimax_friend_chat_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "bench-key",
            "RELATIONSHIP_OS_LLM_API_KEY": "stale-system-key",
        }
    )

    assert env["BENCHMARK_CHAT_API_KEY"] == "bench-key"
    assert env["RELATIONSHIP_OS_LLM_API_KEY"] == "bench-key"


def test_build_minimax_friend_chat_zh_env_preserves_fact_memory_backend_override() -> None:
    env = build_minimax_friend_chat_zh_env(
        {
            "BENCHMARK_CHAT_API_KEY": "bench-key",
            "RELATIONSHIP_OS_LLM_API_KEY": "",
            "RELATIONSHIP_OS_FACT_MEMORY_BACKEND": "native",
        }
    )

    assert env["RELATIONSHIP_OS_FACT_MEMORY_BACKEND"] == "native"


def test_build_official_edge_env_falls_back_to_system_api_key() -> None:
    env = build_official_edge_env(
        {
            "BENCHMARK_CHAT_API_KEY": "",
            "RELATIONSHIP_OS_LLM_API_KEY": "system-key",
        }
    )

    assert env["BENCHMARK_CHAT_API_KEY"] == "system-key"


def test_build_official_edge_env_defaults_fact_memory_backend_to_mem0_shadow() -> None:
    env = build_official_edge_env(
        {
            "BENCHMARK_CHAT_API_KEY": "k",
            "RELATIONSHIP_OS_LLM_API_KEY": "k",
        }
    )

    assert env["RELATIONSHIP_OS_FACT_MEMORY_BACKEND"] == "mem0_shadow"


def test_resolve_benchmark_chat_api_key_prefers_minimax_over_system_key() -> None:
    assert (
        _resolve_benchmark_chat_api_key(
            {
                "RELATIONSHIP_OS_LLM_API_KEY": "rel-key",
                "MINIMAX_API_KEY": "mini-key",
            }
        )
        == "mini-key"
    )
    assert _resolve_benchmark_chat_api_key({"RELATIONSHIP_OS_LLM_API_KEY": "rel-key"}) == "rel-key"
    assert _resolve_benchmark_chat_api_key({"MINIMAX_API_KEY": "mini-key"}) == "mini-key"


def test_chat_backend_config_prefers_minimax_key_for_minimax_provider(
    monkeypatch,
) -> None:
    monkeypatch.setenv("BENCHMARK_CHAT_PROVIDER", "minimax")
    monkeypatch.setenv("BENCHMARK_CHAT_API_KEY", "")
    monkeypatch.setenv("MINIMAX_API_KEY", "mini-key")
    monkeypatch.setenv("RELATIONSHIP_OS_LLM_API_KEY", "stale-rel-key")

    config = ChatBackendConfig.from_env(default_model="M2-her")

    assert config.api_key == "mini-key"


def test_person_memory_suites_are_registered() -> None:
    for suite_name in (
        "cross_session_identity",
        "persistent_preferences",
        "temporal_revision",
        "soft_memory_decay",
        "social_world_consistency",
        "cross_user_recall",
        "cross_user_attribution",
        "dramatic_disclosure",
        "conscience_choice",
        "conscience_choice_stability",
        "persona_growth_continuity",
        "persona_continuity_lite",
        "melancholic_persona_consistency",
        "factual_recall_lite",
        "social_disclosure_lite",
        "latency_budget",
        "drive_persistence",
        "goal_followthrough",
        "offline_reinterpretation",
        "world_state_grounding",
        "cross_channel_autonomy",
        "narrative_continuity",
        "long_chat_continuity_zh",
        "persona_stability_zh",
        "naturalness_under_memory",
        "social_world_control",
        "cross_session_friend_feel",
        "companion_stress_zh",
    ):
        assert suite_name in SUITE_RUNNERS


def test_emotional_judge_parses_fenced_json() -> None:
    judge = LLMJudge(model="test-model", api_base="", api_key="")
    raw = """```json
    {
      "empathy": 8,
      "naturalness": 7,
      "companionship": 8,
      "boundary": 9,
      "overall": 8,
      "reason": "Warm and appropriately bounded."
    }
    ```"""
    parsed = judge._parse_json(raw)
    assert parsed["overall"] == 8
    assert parsed["reason"] == "Warm and appropriately bounded."


def test_emotional_judge_parses_score_lines_when_json_is_missing() -> None:
    judge = LLMJudge(model="test-model", api_base="", api_key="")
    raw = """
    Empathy: 7
    Naturalness: 6
    Companionship: 8
    Boundary: 9
    Overall: 7
    Reason: Caring, but a bit generic.
    """
    parsed = judge._parse_json(raw)
    assert parsed == {
        "empathy": 7.0,
        "naturalness": 6.0,
        "companionship": 8.0,
        "boundary": 9.0,
        "overall": 7.0,
        "reason": "Caring, but a bit generic.",
    }


def test_minimax_backend_normalizes_endpoint_variants() -> None:
    backend = BenchmarkChatBackend(
        ChatBackendConfig(
            provider="minimax",
            model="M2-her",
            api_base="https://api.minimax.io",
            api_key="test-key",
        )
    )
    assert (
        backend._normalize_minimax_endpoint("https://api.minimax.io")
        == "https://api.minimax.io/v1/text/chatcompletion_v2"
    )
    assert (
        backend._normalize_minimax_endpoint("https://api.minimax.io/v1")
        == "https://api.minimax.io/v1/text/chatcompletion_v2"
    )
    assert (
        backend._normalize_minimax_endpoint(
            "https://api.minimax.io/v1/text/chatcompletion_v2"
        )
        == "https://api.minimax.io/v1/text/chatcompletion_v2"
    )


@skipIf(Mem0BenchmarkClient is None, "mem0 not installed")
def test_mem0_build_messages_merges_memory_into_first_system_prompt() -> None:
    client = object.__new__(Mem0BenchmarkClient)
    client.retrieval_limit = 6
    client._search_memories = lambda **_kwargs: ["- user: Austin", "- user: Maple"]  # type: ignore[method-assign]
    state = _Mem0SessionState(
        user_id="u1",
        run_id="r1",
        history=[{"role": "system", "content": "You are Yoyo."}],
    )

    messages, retrieval_count = client._build_messages(state=state, content="What do you know?")

    assert retrieval_count == 2
    assert [message["role"] for message in messages].count("system") == 1
    assert "Relevant memory snippets from previous conversations:" in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "What do you know?"}


def test_load_benchmark_persona_prefers_file(tmp_path, monkeypatch) -> None:
    prompt_path = tmp_path / "persona.md"
    prompt_path.write_text("You are Lin Xiaoyu.", encoding="utf-8")
    monkeypatch.setenv("BENCHMARK_PERSONA_PROMPT_FILE", str(prompt_path))
    monkeypatch.setenv("BENCHMARK_PERSONA_PROMPT", "fallback prompt")

    prompt = load_benchmark_persona("default prompt")

    assert prompt == "You are Lin Xiaoyu."


def test_official_edge_env_sets_demo_defaults() -> None:
    env = build_official_edge_env({})

    assert env["RELATIONSHIP_OS_EVENT_STORE_BACKEND"] == "memory"
    assert env["RELATIONSHIP_OS_RUNTIME_PROFILE"] == OFFICIAL_EDGE_RUNTIME_PROFILE
    assert env["BENCHMARK_CHAT_PROVIDER"] == OFFICIAL_EDGE_BENCHMARK_PROVIDER
    assert env["BENCHMARK_CHAT_MODEL"] == OFFICIAL_EDGE_BENCHMARK_MODEL
    assert env["RELATIONSHIP_OS_EDGE_ALLOW_CLOUD_ESCALATION"] == "false"


def test_discover_report_bundle_finds_latest_triplet(tmp_path: Path) -> None:
    (tmp_path / "benchmark_20260324_120000.json").write_text("{}", encoding="utf-8")
    (tmp_path / "benchmark_20260324_120000.md").write_text("md", encoding="utf-8")
    (tmp_path / "benchmark_20260324_120000.html").write_text("html", encoding="utf-8")
    (tmp_path / "benchmark_20260324_130000.json").write_text("{}", encoding="utf-8")
    (tmp_path / "benchmark_20260324_130000.md").write_text("md2", encoding="utf-8")
    (tmp_path / "benchmark_20260324_130000.html").write_text("html2", encoding="utf-8")

    bundle = discover_report_bundle(tmp_path)

    assert bundle["json"].name == "benchmark_20260324_130000.json"
    assert bundle["md"].name == "benchmark_20260324_130000.md"
    assert bundle["html"].name == "benchmark_20260324_130000.html"


def test_write_latest_bundle_copies_stable_files(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "run"
    latest_dir = tmp_path / "latest"
    bundle_dir.mkdir()
    bundle = {
        "json": bundle_dir / "benchmark_1.json",
        "md": bundle_dir / "benchmark_1.md",
        "html": bundle_dir / "benchmark_1.html",
    }
    for path, content in (
        (bundle["json"], "{}"),
        (bundle["md"], "markdown"),
        (bundle["html"], "<html></html>"),
    ):
        path.write_text(content, encoding="utf-8")
    zh_path = bundle_dir / "benchmark_1_中文复盘.md"
    zh_path.write_text("# 中文复盘", encoding="utf-8")

    latest_paths = write_latest_bundle(bundle, zh_recap_path=zh_path, latest_dir=latest_dir)

    assert latest_paths["json"].read_text(encoding="utf-8") == "{}"
    assert latest_paths["md"].read_text(encoding="utf-8") == "markdown"
    assert latest_paths["html"].read_text(encoding="utf-8") == "<html></html>"
    assert latest_paths["zh"].read_text(encoding="utf-8") == "# 中文复盘"


def test_render_official_edge_zh_recap_mentions_official_files() -> None:
    recap = render_official_edge_zh_recap(
        {
            "benchmark_chat_provider": "minimax",
            "benchmark_chat_model": "M2-her",
            "runtime_profile": "edge_desktop_4b",
            "model": "openai/llama-3-1-8b-instruct",
            "suites": ["factual_recall_lite", "cross_user_attribution", "latency_budget"],
            "arms": {
                "baseline": {
                    "enabled": True,
                    "overall": 1.15,
                    "latency": {"avg_ms": 1787.94},
                    "suites": {"factual_recall_lite": {"average_score": 0.0}},
                },
                "mem0_oss": {
                    "enabled": True,
                    "overall": 1.15,
                    "latency": {"avg_ms": 1766.9},
                    "suites": {"factual_recall_lite": {"average_score": 0.0}},
                },
                "system": {
                    "enabled": True,
                    "overall": 10.0,
                    "latency": {"avg_ms": 4316.67},
                    "suites": {"factual_recall_lite": {"average_score": 10.0}},
                },
            },
        }
    )

    assert "latest.html" in recap
    assert "MiniMax `M2-her`" in recap
    assert "RelationshipOS" in recap
