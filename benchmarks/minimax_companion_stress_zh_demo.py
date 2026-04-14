"""Heavy Chinese companion stress benchmark on MiniMax across all arms."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from benchmarks.__main__ import build_failed_benchmark_results  # noqa: E402
from benchmarks.friend_chat_zh_demo import (  # noqa: E402
    FRIEND_CHAT_ZH_BENCHMARK_API_BASE,
    FRIEND_CHAT_ZH_BENCHMARK_MODEL,
    FRIEND_CHAT_ZH_BENCHMARK_PROVIDER,
    FRIEND_CHAT_ZH_PERSONA_FILE,
    FRIEND_CHAT_ZH_RUNTIME_PROFILE,
)
from benchmarks.official_edge_demo import (  # noqa: E402
    _load_dotenv,
    _resolve_benchmark_chat_api_key,
    discover_report_bundle,
)
from benchmarks.report import generate_benchmark_report  # noqa: E402

COMPANION_STRESS_ZH_SUITES = ("companion_stress_zh",)
MINIMAX_COMPANION_STRESS_SYSTEM_BACKEND = "minimax"
MINIMAX_COMPANION_STRESS_SYSTEM_MODEL = "M2-her"


def build_minimax_companion_stress_zh_env(
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = _load_dotenv(Path(".env"))
    env.update(base_env or os.environ)
    benchmark_api_key = _resolve_benchmark_chat_api_key(env)
    env["BENCHMARK_CHAT_API_KEY"] = benchmark_api_key
    if benchmark_api_key:
        env["MINIMAX_API_KEY"] = benchmark_api_key
    env["PYTHONPATH"] = "src"
    env["RELATIONSHIP_OS_EVENT_STORE_BACKEND"] = "memory"
    env["RELATIONSHIP_OS_LLM_BACKEND"] = MINIMAX_COMPANION_STRESS_SYSTEM_BACKEND
    env["RELATIONSHIP_OS_RUNTIME_PROFILE"] = FRIEND_CHAT_ZH_RUNTIME_PROFILE
    env["RELATIONSHIP_OS_EDGE_ALLOW_CLOUD_ESCALATION"] = "false"
    env["RELATIONSHIP_OS_LLM_MODEL"] = MINIMAX_COMPANION_STRESS_SYSTEM_MODEL
    env["RELATIONSHIP_OS_LLM_API_BASE"] = FRIEND_CHAT_ZH_BENCHMARK_API_BASE
    env["RELATIONSHIP_OS_LLM_API_KEY"] = benchmark_api_key or env.get(
        "RELATIONSHIP_OS_LLM_API_KEY",
        "",
    )
    env["RELATIONSHIP_OS_ENTITY_PERSONA_SEED_FILE"] = FRIEND_CHAT_ZH_PERSONA_FILE
    env["BENCHMARK_CHAT_PROVIDER"] = FRIEND_CHAT_ZH_BENCHMARK_PROVIDER
    env["BENCHMARK_CHAT_MODEL"] = FRIEND_CHAT_ZH_BENCHMARK_MODEL
    env["BENCHMARK_CHAT_API_BASE"] = FRIEND_CHAT_ZH_BENCHMARK_API_BASE
    env["BENCHMARK_PERSONA_PROMPT_FILE"] = FRIEND_CHAT_ZH_PERSONA_FILE
    env["BENCHMARK_REPORT_TITLE"] = "RelationshipOS + MiniMax Companion Stress Benchmark"
    env["BENCHMARK_REPORT_SUBTITLE"] = (
        "500-turn+ Chinese companion stress benchmark comparing RelationshipOS on "
        "MiniMax against plain MiniMax and MiniMax + Mem0."
    )
    env["BENCHMARK_REPORT_PAGE_TITLE"] = "RelationshipOS + MiniMax Companion Stress Benchmark"
    return env


def apply_companion_stress_benchmark_controls(
    env: Mapping[str, str],
    *,
    deep_recall_timeout: float | None = None,
    inter_turn_idle_seconds: float = 0.0,
    consolidate_between_sessions: bool = False,
    consolidation_timeout: float = 120.0,
    consolidation_poll_interval: float = 0.5,
    stress_mode: str = "stable",
) -> dict[str, str]:
    controlled = dict(env)
    if deep_recall_timeout is not None:
        controlled["RELATIONSHIP_OS_LLM_TIMEOUT_SECONDS"] = str(
            max(1, int(round(float(deep_recall_timeout))))
        )
    controlled["BENCHMARK_INTER_TURN_IDLE_SECONDS"] = str(
        max(0.0, float(inter_turn_idle_seconds))
    )
    controlled["BENCHMARK_CONSOLIDATE_BETWEEN_SESSIONS"] = (
        "true" if consolidate_between_sessions else "false"
    )
    controlled["BENCHMARK_CONSOLIDATION_TIMEOUT_SECONDS"] = str(
        max(1.0, float(consolidation_timeout))
    )
    controlled["BENCHMARK_CONSOLIDATION_POLL_INTERVAL_SECONDS"] = str(
        max(0.05, float(consolidation_poll_interval))
    )
    normalized_stress_mode = str(stress_mode or "stable").strip().casefold()
    controlled["BENCHMARK_STRESS_MODE"] = (
        normalized_stress_mode
        if normalized_stress_mode in {"strict", "stable"}
        else "stable"
    )
    return controlled


def _wait_for_health(base_url: str, timeout_seconds: float = 60.0) -> None:
    deadline = time.time() + timeout_seconds
    health_url = f"{base_url.rstrip('/')}/healthz"
    last_error = ""
    while time.time() < deadline:
        try:
            response = httpx.get(health_url, timeout=2.0)
            if response.status_code == 200:
                return
            last_error = f"status={response.status_code}"
        except Exception as exc:  # pragma: no cover
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"Server did not become healthy: {last_error}")


def write_latest_bundle(bundle: Mapping[str, Path], *, latest_dir: Path) -> dict[str, Path]:
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_paths = {
        "json": latest_dir / "latest.json",
        "md": latest_dir / "latest.md",
        "html": latest_dir / "latest.html",
    }
    shutil.copy2(bundle["json"], latest_paths["json"])
    shutil.copy2(bundle["md"], latest_paths["md"])
    shutil.copy2(bundle["html"], latest_paths["html"])
    return latest_paths


def build_companion_stress_benchmark_cmd(
    *,
    base_url: str,
    output_dir: Path,
    timeout: float,
    suite_timeout: float,
    languages: str,
    max_cases_per_suite: int,
    skip_baseline: bool = False,
    skip_mem0: bool = False,
    skip_system: bool = False,
) -> list[str]:
    command = [
        "uv",
        "run",
        "python",
        "-m",
        "benchmarks",
        "--base-url",
        base_url,
        "--output-dir",
        str(output_dir),
        "--timeout",
        str(timeout),
        "--suite-timeout",
        str(suite_timeout),
        "--suite",
        ",".join(COMPANION_STRESS_ZH_SUITES),
        "--languages",
        languages,
        "--max-cases-per-suite",
        str(max_cases_per_suite),
    ]
    if skip_baseline:
        command.append("--skip-baseline")
    if skip_mem0:
        command.append("--skip-mem0")
    if skip_system:
        command.append("--skip-system")
    return command


def _write_failure_bundle(
    *,
    output_dir: Path,
    latest_dir: Path,
    env: Mapping[str, str],
    suites: tuple[str, ...],
    languages: str,
    error: str,
) -> dict[str, Path]:
    results = build_failed_benchmark_results(
        suites=list(suites),
        languages={language.strip() for language in languages.split(",") if language.strip()},
        error=error,
        model=env.get("RELATIONSHIP_OS_LLM_MODEL", ""),
        benchmark_chat_provider=env.get("BENCHMARK_CHAT_PROVIDER", "unknown"),
        benchmark_chat_model=env.get("BENCHMARK_CHAT_MODEL", ""),
        judge_model=env.get("BENCHMARK_JUDGE_MODEL", ""),
        runtime_profile=env.get("RELATIONSHIP_OS_RUNTIME_PROFILE", "default"),
        report_title=env.get(
            "BENCHMARK_REPORT_TITLE",
            "RelationshipOS + MiniMax Companion Stress Benchmark",
        ),
        report_subtitle=env.get(
            "BENCHMARK_REPORT_SUBTITLE",
            (
                "500-turn+ Chinese companion stress benchmark comparing RelationshipOS on "
                "MiniMax against plain MiniMax and MiniMax + Mem0."
            ),
        ),
        report_page_title=env.get(
            "BENCHMARK_REPORT_PAGE_TITLE",
            "RelationshipOS + MiniMax Companion Stress Benchmark",
        ),
    )
    md_path, json_path, html_path = generate_benchmark_report(results, output_dir)
    bundle = {"json": json_path, "md": md_path, "html": html_path}
    write_latest_bundle(bundle, latest_dir=latest_dir)
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the MiniMax Chinese companion stress benchmark",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8013")
    parser.add_argument(
        "--output-dir",
        default="benchmark_results/minimax_companion_stress_zh_demo",
    )
    parser.add_argument(
        "--latest-dir",
        default="benchmark_results/minimax_companion_stress_zh_demo/latest",
    )
    parser.add_argument("--languages", default="zh")
    parser.add_argument("--max-cases-per-suite", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--suite-timeout", type=float, default=10800.0)
    parser.add_argument("--stress-turns", type=int, default=500)
    parser.add_argument("--stress-min-characters", type=int, default=50000)
    parser.add_argument(
        "--stress-mode",
        choices=("strict", "stable"),
        default="stable",
    )
    parser.add_argument(
        "--fact-memory-backend",
        choices=("native", "mem0_shadow", "mem0_primary"),
        default=None,
    )
    parser.add_argument("--deep-recall-timeout", type=float, default=60.0)
    parser.add_argument("--inter-turn-idle-seconds", type=float, default=0.0)
    parser.add_argument("--consolidate-between-sessions", action="store_true")
    parser.add_argument("--consolidation-timeout", type=float, default=120.0)
    parser.add_argument("--consolidation-poll-interval", type=float, default=0.5)
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument("--skip-mem0", action="store_true")
    parser.add_argument("--skip-system", action="store_true")
    parser.add_argument("--system-only", action="store_true")
    parser.add_argument("--keep-server", action="store_true")
    parser.add_argument("--reuse-server", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    latest_dir = Path(args.latest_dir)
    base_env = os.environ.copy()
    if args.fact_memory_backend:
        base_env["RELATIONSHIP_OS_FACT_MEMORY_BACKEND"] = args.fact_memory_backend
    env = build_minimax_companion_stress_zh_env(base_env)
    env = apply_companion_stress_benchmark_controls(
        env,
        deep_recall_timeout=args.deep_recall_timeout,
        inter_turn_idle_seconds=args.inter_turn_idle_seconds,
        consolidate_between_sessions=args.consolidate_between_sessions,
        consolidation_timeout=args.consolidation_timeout,
        consolidation_poll_interval=args.consolidation_poll_interval,
        stress_mode=args.stress_mode,
    )
    env["BENCHMARK_STRESS_TURNS"] = str(args.stress_turns)
    env["BENCHMARK_STRESS_MIN_CHARACTERS"] = str(args.stress_min_characters)
    skip_baseline = bool(args.skip_baseline or args.system_only)
    skip_mem0 = bool(args.skip_mem0 or args.system_only)
    if not env.get("BENCHMARK_CHAT_API_KEY") and not (skip_baseline and skip_mem0):
        raise SystemExit("BENCHMARK_CHAT_API_KEY is required for the MiniMax benchmark")
    if not env.get("RELATIONSHIP_OS_LLM_API_KEY"):
        raise SystemExit("RELATIONSHIP_OS_LLM_API_KEY is required for the MiniMax system arm")

    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8013
    server_log = output_dir / "server.log"
    server_log.parent.mkdir(parents=True, exist_ok=True)

    server_process: subprocess.Popen[str] | None = None
    try:
        if not args.reuse_server:
            with server_log.open("w", encoding="utf-8") as log_file:
                server_process = subprocess.Popen(
                    [
                        "uv",
                        "run",
                        "uvicorn",
                        "relationship_os.main:app",
                        "--host",
                        host,
                        "--port",
                        str(port),
                    ],
                    cwd=Path.cwd(),
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            _wait_for_health(base_url)

        benchmark_cmd = build_companion_stress_benchmark_cmd(
            base_url=base_url,
            output_dir=output_dir,
            timeout=args.timeout,
            suite_timeout=args.suite_timeout,
            languages=args.languages,
            max_cases_per_suite=args.max_cases_per_suite,
            skip_baseline=skip_baseline,
            skip_mem0=skip_mem0,
            skip_system=bool(args.skip_system),
        )
        subprocess.run(
            benchmark_cmd,
            cwd=Path.cwd(),
            env=env,
            check=True,
            timeout=max(14400.0, args.suite_timeout * 3.5),
        )

        bundle = discover_report_bundle(output_dir)
        latest_paths = write_latest_bundle(bundle, latest_dir=latest_dir)
        print(f"MiniMax companion stress benchmark complete: {bundle['html']}")
        print(f"Stable latest HTML: {latest_paths['html']}")
    except Exception as exc:
        bundle = _write_failure_bundle(
            output_dir=output_dir,
            latest_dir=latest_dir,
            env=env,
            suites=COMPANION_STRESS_ZH_SUITES,
            languages=args.languages,
            error=str(exc),
        )
        print(
            "MiniMax companion stress benchmark failed but emitted scored bundle: "
            f"{bundle['html']}"
        )
    finally:
        if server_process is not None and not args.keep_server:
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover
                server_process.kill()
                server_process.wait(timeout=5)


if __name__ == "__main__":
    main()
