"""
Long-horizon Chinese companion stress run against a live RelationshipOS HTTP API.

Example:
  export PYTHONPATH=src
  uv run python -m benchmarks.minimax_companion_stress_zh_demo \\
    --base-url http://127.0.0.1:8013 \\
    --output-dir benchmark_results/cloud_companion_stress_zh_smoke \\
    --latest-dir benchmark_results/cloud_companion_stress_zh_smoke/latest \\
    --languages zh \\
    --max-cases-per-suite 1 \\
    --timeout 300 \\
    --suite-timeout 3600 \\
    --stress-turns 60 \\
    --stress-min-characters 6000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float,
) -> tuple[int, Any]:
    data = None
    hdrs = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        data = payload
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.getcode() or 200
            if not raw:
                return status, None
            return status, json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body) if err_body else None
        except json.JSONDecodeError:
            parsed = err_body
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {parsed}") from e


def _zh_user_payload(turn_index: int, min_chars: int) -> str:
    """Build a long Chinese user turn to stress digest / context handling."""
    base = (
        f"第{turn_index}轮。我在做长期陪伴压测。"
        "请用自然口语回复，可以简短问一个跟进问题。"
        "主题：日常生活、情绪支持、边界与节奏。"
    )
    filler = "我们在慢慢聊，不着急把话说满。"
    out = base
    while len(out) < min_chars:
        out += filler
    return out[: max(min_chars, len(base))]


def run_suite(args: argparse.Namespace) -> dict[str, Any]:
    api_prefix = args.api_prefix.rstrip("/")
    base = args.base_url.rstrip("/")
    hdrs: dict[str, str] = {}
    if args.api_key:
        hdrs["X-API-Key"] = args.api_key

    suite_started = time.perf_counter()
    out_dir = Path(args.output_dir)
    latest_dir = Path(args.latest_dir) if args.latest_dir else None
    out_dir.mkdir(parents=True, exist_ok=True)
    if latest_dir is not None:
        latest_dir.mkdir(parents=True, exist_ok=True)

    status, _ = _http_json("GET", f"{base}/healthz", timeout=min(30.0, args.timeout), headers=hdrs)
    if status != 200:
        raise RuntimeError(f"healthz unexpected status {status}")

    status, created = _http_json(
        "POST",
        f"{base}{api_prefix}/sessions",
        body={"metadata": {"benchmark": "minimax_companion_stress_zh", "languages": args.languages}},
        headers=hdrs,
        timeout=args.timeout,
    )
    if status not in (200, 201) or not isinstance(created, dict):
        raise RuntimeError(f"create session failed: {status} {created}")
    session_id = str(created.get("session_id") or "")
    if not session_id:
        raise RuntimeError(f"could not parse session_id from {created!r}")

    turns: list[dict[str, Any]] = []
    assistant_chars = 0
    user_chars = 0
    # Keep under API max message length (10_000) while scaling with desired assistant volume.
    min_user_chars = min(
        10_000,
        max(400, args.stress_min_characters // max(1, args.stress_turns)),
    )

    for i in range(1, args.stress_turns + 1):
        if time.perf_counter() - suite_started > args.suite_timeout:
            raise TimeoutError("suite-timeout exceeded")
        content = _zh_user_payload(i, min_user_chars)
        t0 = time.perf_counter()
        status, turn_resp = _http_json(
            "POST",
            f"{base}{api_prefix}/sessions/{session_id}/turns",
            body={"content": content, "generate_reply": True, "metadata": {}},
            headers=hdrs,
            timeout=args.timeout,
        )
        elapsed = time.perf_counter() - t0
        if status not in (200, 201):
            raise RuntimeError(f"turn {i} failed: {status} {turn_resp}")
        if not isinstance(turn_resp, dict):
            raise RuntimeError(f"turn {i} bad response type")
        reply = str(turn_resp.get("assistant_response") or "")
        assistant_chars += len(reply)
        user_chars += len(content)
        turns.append(
            {
                "turn": i,
                "user_chars": len(content),
                "assistant_chars": len(reply),
                "elapsed_seconds": round(elapsed, 3),
            }
        )

    suite_elapsed = time.perf_counter() - suite_started
    report: dict[str, Any] = {
        "suite": "minimax_companion_stress_zh",
        "started_at": _utc_iso(),
        "base_url": base,
        "api_prefix": api_prefix,
        "session_id": session_id,
        "languages": args.languages,
        "stress_turns": args.stress_turns,
        "stress_min_characters": args.stress_min_characters,
        "user_total_characters": user_chars,
        "assistant_total_characters": assistant_chars,
        "suite_elapsed_seconds": round(suite_elapsed, 3),
        "turns": turns,
        # Cumulative user input (Chinese stress volume); not model output length.
        "min_characters_met": user_chars >= args.stress_min_characters,
    }

    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if latest_dir is not None:
        (latest_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="MiniMax companion stress (ZH) via HTTP API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8013")
    parser.add_argument("--api-prefix", default="/api/v1")
    parser.add_argument("--api-key", default="", help="Optional X-API-Key for the HTTP API")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--latest-dir", default="")
    parser.add_argument("--languages", default="zh")
    parser.add_argument(
        "--max-cases-per-suite",
        type=int,
        default=1,
        help="Ignored for now; kept for CLI parity with README examples.",
    )
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--suite-timeout", type=float, default=3600.0)
    parser.add_argument("--stress-turns", type=int, default=60)
    parser.add_argument("--stress-min-characters", type=int, default=6000)
    args = parser.parse_args()

    try:
        report = run_suite(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({k: report[k] for k in report if k != "turns"}, ensure_ascii=False, indent=2))
    if not report["min_characters_met"]:
        print(
            f"WARNING: user_total_characters {report['user_total_characters']} "
            f"< threshold {report['stress_min_characters']}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
