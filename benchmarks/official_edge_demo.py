"""Official edge benchmark runner for investor demos."""

from __future__ import annotations

import argparse
import json
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
from benchmarks.report import generate_benchmark_report  # noqa: E402
from benchmarks.zh_recap import write_official_edge_zh_recap  # noqa: E402

OFFICIAL_EDGE_SUITES = (
    "factual_recall_lite",
    "cross_user_attribution",
    "latency_budget",
)
OFFICIAL_EDGE_RUNTIME_PROFILE = "edge_desktop_4b"
OFFICIAL_EDGE_SYSTEM_MODEL = "openai/llama-3-1-8b-instruct"
OFFICIAL_EDGE_BENCHMARK_PROVIDER = "minimax"
OFFICIAL_EDGE_BENCHMARK_MODEL = "M2-her"
OFFICIAL_EDGE_BENCHMARK_API_BASE = "https://api.minimax.io"


def _load_dotenv(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        loaded[key.strip()] = value.strip().strip('"').strip("'")
    return loaded


def _resolve_benchmark_chat_api_key(env: Mapping[str, str]) -> str:
    return (
        str(env.get("BENCHMARK_CHAT_API_KEY", "")).strip()
        or str(env.get("MINIMAX_API_KEY", "")).strip()
        or str(env.get("RELATIONSHIP_OS_LLM_API_KEY", "")).strip()
        or str(env.get("OPENAI_API_KEY", "")).strip()
    )


def _resolve_fact_memory_backend(env: Mapping[str, str]) -> str:
    backend = str(env.get("RELATIONSHIP_OS_FACT_MEMORY_BACKEND", "")).strip()
    return backend or "mem0_shadow"


def build_official_edge_env(base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    env = _load_dotenv(Path(".env"))
    env.update(base_env or os.environ)
    env["BENCHMARK_CHAT_API_KEY"] = _resolve_benchmark_chat_api_key(env)
    if env["BENCHMARK_CHAT_API_KEY"]:
        env["MINIMAX_API_KEY"] = env["BENCHMARK_CHAT_API_KEY"]
    env["PYTHONPATH"] = "src"
    env["RELATIONSHIP_OS_EVENT_STORE_BACKEND"] = "memory"
    env["RELATIONSHIP_OS_LLM_BACKEND"] = "litellm"
    env["RELATIONSHIP_OS_RUNTIME_PROFILE"] = OFFICIAL_EDGE_RUNTIME_PROFILE
    env["RELATIONSHIP_OS_FACT_MEMORY_BACKEND"] = _resolve_fact_memory_backend(env)
    env["RELATIONSHIP_OS_EDGE_ALLOW_CLOUD_ESCALATION"] = "false"
    env["RELATIONSHIP_OS_LLM_MODEL"] = OFFICIAL_EDGE_SYSTEM_MODEL
    env["BENCHMARK_CHAT_PROVIDER"] = OFFICIAL_EDGE_BENCHMARK_PROVIDER
    env["BENCHMARK_CHAT_MODEL"] = OFFICIAL_EDGE_BENCHMARK_MODEL
    env["BENCHMARK_CHAT_API_BASE"] = OFFICIAL_EDGE_BENCHMARK_API_BASE
    env["BENCHMARK_REPORT_TITLE"] = "RelationshipOS Official Edge Benchmark"
    env["BENCHMARK_REPORT_SUBTITLE"] = (
        "Official investor-facing edge benchmark for RelationshipOS vs "
        "MiniMax M2-her and MiniMax M2-her + Mem0."
    )
    env["BENCHMARK_REPORT_PAGE_TITLE"] = "RelationshipOS Official Edge Benchmark"
    return env


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


def discover_report_bundle(output_dir: Path) -> dict[str, Path]:
    json_candidates = sorted(output_dir.glob("benchmark_*.json"))
    if not json_candidates:
        raise FileNotFoundError(f"No benchmark JSON found under {output_dir}")
    json_path = json_candidates[-1]
    stem = json_path.stem
    md_path = output_dir / f"{stem}.md"
    html_path = output_dir / f"{stem}.html"
    if not md_path.exists() or not html_path.exists():
        raise FileNotFoundError(f"Incomplete benchmark bundle for {stem}")
    return {
        "json": json_path,
        "md": md_path,
        "html": html_path,
    }


def write_latest_bundle(
    bundle: Mapping[str, Path],
    *,
    zh_recap_path: Path,
    latest_dir: Path,
) -> dict[str, Path]:
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_paths = {
        "json": latest_dir / "latest.json",
        "md": latest_dir / "latest.md",
        "html": latest_dir / "latest.html",
        "zh": latest_dir / "latest_中文复盘.md",
    }
    shutil.copy2(bundle["json"], latest_paths["json"])
    shutil.copy2(bundle["md"], latest_paths["md"])
    shutil.copy2(bundle["html"], latest_paths["html"])
    shutil.copy2(zh_recap_path, latest_paths["zh"])
    return latest_paths


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
        report_title=env.get("BENCHMARK_REPORT_TITLE", "RelationshipOS Official Edge Benchmark"),
        report_subtitle=env.get(
            "BENCHMARK_REPORT_SUBTITLE",
            (
                "Official investor-facing edge benchmark for RelationshipOS vs "
                "MiniMax M2-her and MiniMax M2-her + Mem0."
            ),
        ),
        report_page_title=env.get(
            "BENCHMARK_REPORT_PAGE_TITLE",
            "RelationshipOS Official Edge Benchmark",
        ),
    )
    md_path, json_path, html_path = generate_benchmark_report(results, output_dir)
    bundle = {"json": json_path, "md": md_path, "html": html_path}
    zh_recap_path = output_dir / f"{json_path.stem}_中文复盘.md"
    write_official_edge_zh_recap(results, zh_recap_path)
    write_latest_bundle(bundle, zh_recap_path=zh_recap_path, latest_dir=latest_dir)
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the official RelationshipOS edge demo benchmark"
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--output-dir", default="benchmark_results/official_edge_demo")
    parser.add_argument("--latest-dir", default="benchmark_results/official_edge_demo/latest")
    parser.add_argument("--languages", default="en")
    parser.add_argument("--max-cases-per-suite", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--keep-server", action="store_true")
    parser.add_argument("--reuse-server", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    latest_dir = Path(args.latest_dir)
    env = build_official_edge_env()
    if not env.get("BENCHMARK_CHAT_API_KEY"):
        raise SystemExit("BENCHMARK_CHAT_API_KEY is required for the official MiniMax benchmark")
    if not env.get("RELATIONSHIP_OS_LLM_API_KEY"):
        raise SystemExit("RELATIONSHIP_OS_LLM_API_KEY is required for the official system arm")

    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8010
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

        benchmark_cmd = [
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
            str(args.timeout),
            "--suite",
            ",".join(OFFICIAL_EDGE_SUITES),
            "--languages",
            args.languages,
            "--max-cases-per-suite",
            str(args.max_cases_per_suite),
        ]
        subprocess.run(
            benchmark_cmd,
            cwd=Path.cwd(),
            env=env,
            check=True,
            timeout=max(900.0, args.timeout * max(1, len(OFFICIAL_EDGE_SUITES)) * 2.0),
        )

        bundle = discover_report_bundle(output_dir)
        results = json.loads(bundle["json"].read_text(encoding="utf-8"))
        zh_recap_path = output_dir / f"{bundle['json'].stem}_中文复盘.md"
        write_official_edge_zh_recap(results, zh_recap_path)
        latest_paths = write_latest_bundle(
            bundle,
            zh_recap_path=zh_recap_path,
            latest_dir=latest_dir,
        )

        print(f"Official edge benchmark complete: {bundle['html']}")
        print(f"Stable latest HTML: {latest_paths['html']}")
        print(f"Stable latest Chinese recap: {latest_paths['zh']}")
    except Exception as exc:
        bundle = _write_failure_bundle(
            output_dir=output_dir,
            latest_dir=latest_dir,
            env=env,
            suites=OFFICIAL_EDGE_SUITES,
            languages=args.languages,
            error=str(exc),
        )
        print(f"Official edge benchmark failed but emitted scored bundle: {bundle['html']}")
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
