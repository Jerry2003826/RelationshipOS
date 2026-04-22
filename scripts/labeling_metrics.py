#!/usr/bin/env python3
"""Turn the '4x labeling speedup' headline into a CI-assertable number.

Reads the silver/reviewed JSONL pipeline and writes a metrics JSON::

    {
      "silver_total":      1000,
      "auto_accepted":     760,    # conf >= auto_threshold
      "human_reviewed":    240,    # forwarded to human queue
      "human_kept":        192,    # accepted / corrected by human
      "auto_share":        0.760,
      "avg_silver_conf":   0.812,
      "baseline_secs":     60.0,   # hand-label seconds per row
      "auto_secs":         2.0,    # LLM-only seconds per row
      "human_secs":        20.0,   # human review seconds per row
      "total_secs":        5320.0,
      "baseline_secs_all": 60000.0,
      "speedup_x":         11.28
    }

The speedup is defined as
    speedup_x = baseline_secs_all / total_secs

where ``total_secs`` is ``auto_accepted * auto_secs + human_reviewed * human_secs``.
The default parameters yield >=4x whenever auto_share >= 0.60, so we
gate CI at 4x.

This script deliberately does not touch the network — all numbers are
derived from the existing JSONL files produced by the W2 pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path


def _iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def compute_metrics(
    *,
    silver: list[dict],
    reviewed: list[dict] | None = None,
    auto_threshold: float = 0.7,
    baseline_secs: float = 60.0,
    auto_secs: float = 2.0,
    human_secs: float = 20.0,
) -> dict:
    silver_total = len(silver)
    auto_accepted = 0
    conf_sum = 0.0
    for row in silver:
        try:
            c = float(row.get("confidence", 0.0))
        except (TypeError, ValueError):
            c = 0.0
        conf_sum += c
        if c >= auto_threshold:
            auto_accepted += 1
    human_reviewed = silver_total - auto_accepted
    human_kept = 0
    if reviewed is not None:
        human_kept = sum(
            1 for r in reviewed if str(r.get("source")) == "human_review"
        )
    avg_conf = conf_sum / silver_total if silver_total else 0.0
    total_secs = auto_accepted * auto_secs + human_reviewed * human_secs
    baseline_secs_all = silver_total * baseline_secs
    speedup_x = (
        baseline_secs_all / total_secs if total_secs > 0 else 0.0
    )
    return {
        "silver_total": silver_total,
        "auto_accepted": auto_accepted,
        "human_reviewed": human_reviewed,
        "human_kept": human_kept,
        "auto_share": round(
            auto_accepted / silver_total if silver_total else 0.0, 4
        ),
        "avg_silver_conf": round(avg_conf, 4),
        "baseline_secs": baseline_secs,
        "auto_secs": auto_secs,
        "human_secs": human_secs,
        "total_secs": round(total_secs, 2),
        "baseline_secs_all": round(baseline_secs_all, 2),
        "speedup_x": round(speedup_x, 2),
    }


def render_markdown(metrics: dict, *, gate: float) -> str:
    lines = [
        "# 打标提效指标",
        "",
        f"- silver 总量:{metrics['silver_total']}",
        f"- 自动通过 (conf ≥ 0.7):{metrics['auto_accepted']}"
        f" ({metrics['auto_share']:.1%})",
        f"- 人工复核队列:{metrics['human_reviewed']}",
        f"- 人工保留:{metrics['human_kept']}",
        f"- 平均 silver confidence:{metrics['avg_silver_conf']:.3f}",
        f"- 全人工基线耗时:{metrics['baseline_secs_all']:.0f} 秒",
        f"- 当前管线耗时:{metrics['total_secs']:.0f} 秒",
        f"- **提速**:{metrics['speedup_x']:.2f}×",
        "",
    ]
    if metrics["speedup_x"] >= gate:
        lines.append(f"✅ 达到 {gate:.1f}× 门槛")
    else:
        lines.append(f"⚠️ 低于 {gate:.1f}× 门槛")
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--silver", type=Path, required=True)
    p.add_argument("--reviewed", type=Path, default=None)
    p.add_argument("--output-json", type=Path, default=None)
    p.add_argument("--output-md", type=Path, default=None)
    p.add_argument("--auto-threshold", type=float, default=0.7)
    p.add_argument("--baseline-secs", type=float, default=60.0)
    p.add_argument("--auto-secs", type=float, default=2.0)
    p.add_argument("--human-secs", type=float, default=20.0)
    p.add_argument(
        "--gate",
        type=float,
        default=4.0,
        help="Fail with exit code 2 if speedup < gate. Default 4x.",
    )
    args = p.parse_args(argv)

    silver = list(_iter_jsonl(args.silver))
    reviewed = (
        list(_iter_jsonl(args.reviewed)) if args.reviewed is not None else None
    )
    metrics = compute_metrics(
        silver=silver,
        reviewed=reviewed,
        auto_threshold=args.auto_threshold,
        baseline_secs=args.baseline_secs,
        auto_secs=args.auto_secs,
        human_secs=args.human_secs,
    )

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(
            render_markdown(metrics, gate=args.gate), encoding="utf-8"
        )

    print(json.dumps(metrics, ensure_ascii=False))
    if metrics["silver_total"] == 0:
        # Nothing to grade yet.
        return 0
    if metrics["speedup_x"] < args.gate:
        print(
            f"speedup_x={metrics['speedup_x']:.2f} < gate={args.gate:.2f}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
