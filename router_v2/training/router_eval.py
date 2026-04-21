"""Offline evaluation harness for Vanguard Router v2.

Reads a labelled JSONL (same format as training data), runs the full
cascade against each row, and reports:

    * Confusion matrix
    * Macro / per-class F1
    * Tier coverage: % decisions resolved at each tier
    * Latency distribution (p50/p95/p99)
    * Pareto point: (Macro F1, % Tier 3 calls)

Usage:
    python router_eval.py --data router_v2/training/seeds_zh.jsonl \
        --model router_v2/policies/router/model.joblib

Optionally writes a CSV of per-row decisions for ad-hoc inspection.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from router_v2.analyzers.router.contracts import ALL_ROUTES
from router_v2.analyzers.router.vanguard_router_v2 import VanguardRouterV2


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    return rows


def _quantile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    xs2 = sorted(xs)
    k = max(0, min(len(xs2) - 1, int(q * (len(xs2) - 1))))
    return xs2[k]


def _f1(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    p = tp / (tp + fp)
    r = tp / (tp + fn)
    return 2 * p * r / (p + r) if (p + r) else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--dump-csv", type=Path, default=None)
    ap.add_argument(
        "--mock-llm", action="store_true",
        help="Attach a deterministic mock arbiter to exercise Tier 3.",
    )
    args = ap.parse_args()

    rows = _load_jsonl(args.data)

    call_llm = None
    if args.mock_llm:
        def call_llm(prompt: str, timeout: float) -> str:  # noqa: ARG001
            # Deterministic: pick LIGHT_RECALL with confidence 0.55.
            return json.dumps(
                {"route_type": "LIGHT_RECALL", "confidence": 0.55, "why": "mock"},
                ensure_ascii=False,
            )

    router = VanguardRouterV2.from_default(call_llm=call_llm)

    # Warm-up pass (first call pays import amortization costs)
    for r in rows[:3]:
        router.decide(r["text"])

    cm: dict[tuple[str, str], int] = defaultdict(int)
    tier_counter: Counter[str] = Counter()
    latencies: list[float] = []
    tier2_ece_buckets: list[tuple[float, int]] = []
    shadow_logged = 0
    decisions = []

    t_start = time.perf_counter()
    for r in rows:
        d = router.decide(r["text"])
        label = r["label"]
        cm[(label, d.route_type)] += 1
        tier_counter[d.decided_by] += 1
        latencies.append(d.latency_ms)
        if d.should_shadow_log:
            shadow_logged += 1
        tier2_ece_buckets.append((d.confidence, int(label == d.route_type)))
        decisions.append({
            "text": r["text"],
            "gold": label,
            "pred": d.route_type,
            "decided_by": d.decided_by,
            "conf": round(d.confidence, 3),
            "margin": round(d.margin, 3),
            "latency_ms": round(d.latency_ms, 3),
            "rule_hits": list(d.rule_hits),
        })
    wall = time.perf_counter() - t_start

    # Per-class metrics.
    class_metrics: dict[str, dict[str, float]] = {}
    total_correct = 0
    for c in ALL_ROUTES:
        tp = cm[(c, c)]
        fp = sum(cm[(o, c)] for o in ALL_ROUTES if o != c)
        fn = sum(cm[(c, o)] for o in ALL_ROUTES if o != c)
        support = sum(cm[(c, o)] for o in ALL_ROUTES)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        class_metrics[c] = {
            "precision": precision,
            "recall": recall,
            "f1": _f1(tp, fp, fn),
            "support": support,
        }
        total_correct += tp
    macro_f1 = sum(m["f1"] for m in class_metrics.values()) / len(ALL_ROUTES)
    accuracy = total_correct / max(len(rows), 1)

    # Report.
    print("=== Router v2 eval report ===")
    print(f"N = {len(rows)}  wall={wall * 1000:.1f}ms")
    print(f"Accuracy      : {accuracy:.3f}")
    print(f"Macro F1      : {macro_f1:.3f}")
    print()
    print("Per-class:")
    print(f"  {'class':<14s} {'P':>6s} {'R':>6s} {'F1':>6s} {'n':>5s}")
    for c in ALL_ROUTES:
        m = class_metrics[c]
        print(f"  {c:<14s} {m['precision']:6.3f} {m['recall']:6.3f} {m['f1']:6.3f} {int(m['support']):>5d}")
    print()
    print("Confusion matrix (rows=gold, cols=pred):")
    header = "          " + "".join(f" {c:>12s}" for c in ALL_ROUTES)
    print(header)
    for c in ALL_ROUTES:
        vals = "".join(f" {cm[(c, o)]:>12d}" for o in ALL_ROUTES)
        print(f"  {c:<8s}" + vals)
    print()
    print("Tier coverage:")
    for tier, n in tier_counter.most_common():
        print(f"  {tier:<12s} {n:>4d} ({n / len(rows) * 100:5.1f}%)")
    print()
    print("Latency:")
    print(f"  p50={_quantile(latencies, 0.5):.2f}ms  p95={_quantile(latencies, 0.95):.2f}ms  p99={_quantile(latencies, 0.99):.2f}ms")
    print(f"Shadow-logged turns: {shadow_logged} ({shadow_logged / len(rows) * 100:.1f}%)")

    # Pareto point.
    t3_rate = tier_counter.get("mini_llm", 0) / max(len(rows), 1)
    print()
    print(f"Pareto → Macro F1={macro_f1:.3f}  Tier3%={t3_rate * 100:.1f}%")

    if args.dump_csv:
        import csv
        args.dump_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.dump_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(decisions[0].keys()))
            w.writeheader()
            w.writerows(decisions)
        print(f"Dumped → {args.dump_csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
