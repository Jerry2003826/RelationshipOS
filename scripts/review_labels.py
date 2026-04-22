#!/usr/bin/env python3
"""Human-review helper for silver labels.

Reads the JSONL produced by ``llm_prelabel.py``, filters to rows below a
confidence threshold, and writes a new JSONL ready for human review. An
optional ``--interactive`` mode lets the reviewer accept / override each
label from the terminal.

Usage::

    # pass 1 — just extract the ambiguous rows
    python scripts/review_labels.py \
        --input router_v2/training/data/silver_labels.jsonl \
        --output router_v2/training/data/silver_review_queue.jsonl \
        --max-conf 0.7

    # pass 2 — interactive review
    python scripts/review_labels.py \
        --input router_v2/training/data/silver_review_queue.jsonl \
        --output router_v2/training/data/silver_reviewed.jsonl \
        --interactive
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_LABELS = {"FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"}


def _iter_records(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def filter_low_confidence(
    records,
    *,
    max_conf: float,
):
    for rec in records:
        try:
            c = float(rec.get("confidence", 0.0))
        except (TypeError, ValueError):
            c = 0.0
        if c <= max_conf:
            yield rec


def _prompt_label(rec: dict) -> dict:
    text = rec.get("text", "")
    print(f"\nTEXT: {text}")
    print(f"  llm_label={rec.get('label')} conf={rec.get('confidence'):.2f}")
    print(f"  reason={rec.get('reason', '')}")
    print("  [1] FAST_PONG   [2] LIGHT_RECALL   [3] DEEP_THINK   [s] skip   [q] quit")
    raw = input("choice> ").strip().lower()
    mapping = {"1": "FAST_PONG", "2": "LIGHT_RECALL", "3": "DEEP_THINK"}
    if raw in mapping:
        rec = dict(rec)
        rec["label"] = mapping[raw]
        rec["confidence"] = 1.0
        rec["source"] = "human_review"
        return rec
    if raw == "s":
        return {}
    if raw == "q":
        raise KeyboardInterrupt
    # Unknown input -> skip
    return {}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-conf", type=float, default=0.7)
    p.add_argument("--interactive", action="store_true")
    args = p.parse_args(argv)

    records = list(_iter_records(args.input))
    if not args.interactive:
        filtered = list(
            filter_low_confidence(records, max_conf=args.max_conf)
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            for rec in filtered:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(
            f"wrote {len(filtered)}/{len(records)} low-confidence rows "
            f"(max_conf={args.max_conf}) -> {args.output}",
            file=sys.stderr,
        )
        return 0

    # Interactive mode: show every row and either keep the LLM label,
    # override it, or skip.
    kept: list[dict] = []
    try:
        for rec in records:
            out = _prompt_label(rec)
            if out:
                kept.append(out)
    except KeyboardInterrupt:
        print("\naborted by user", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for rec in kept:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"reviewed {len(kept)} rows -> {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
