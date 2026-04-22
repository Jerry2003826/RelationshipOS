#!/usr/bin/env python3
"""Merge human-reviewed silver labels into the tier-2 training set.

Usage::

    python scripts/merge_labels.py \
        --reviewed router_v2/training/data/silver_reviewed.jsonl \
        --training  router_v2/training/training_zh.jsonl \
        --output    router_v2/training/training_zh.jsonl

Behaviour:
  * Keeps every existing row in ``--training`` untouched.
  * Appends any reviewed row whose ``text`` is not already present.
  * Drops rows with invalid labels or missing text.
  * Stamps each appended row with ``source=human_review`` (unless the
    row already declares a source — we do not override that).
  * Preserves ``source`` / ``confidence`` / ``reason`` if present.

Keeping this merge step separate from ``review_labels.py`` means you
can review a batch, inspect the queue, and only fold it into training
when you are happy. It is also safe to rerun — ``text`` dedup makes the
operation idempotent.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path

VALID_LABELS = {"FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"}


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


def _normalise(rec: dict) -> dict | None:
    text = str(rec.get("text") or "").strip()
    label = str(rec.get("label") or "").strip().upper()
    if not text or label not in VALID_LABELS:
        return None
    out = {"text": text, "label": label}
    if "source" in rec and rec["source"]:
        out["source"] = str(rec["source"])
    else:
        out["source"] = "human_review"
    if "confidence" in rec:
        try:
            out["confidence"] = max(0.0, min(1.0, float(rec["confidence"])))
        except (TypeError, ValueError):
            pass
    if rec.get("reason"):
        out["reason"] = str(rec["reason"])[:60]
    return out


def merge(
    reviewed: Iterable[dict],
    training: Iterable[dict],
) -> tuple[list[dict], int, int]:
    """Return (merged_rows, kept_existing_count, appended_count)."""
    merged: list[dict] = []
    seen: set[str] = set()
    kept = 0
    for rec in training:
        text = str(rec.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        merged.append(rec)
        kept += 1
    appended = 0
    for rec in reviewed:
        norm = _normalise(rec)
        if norm is None:
            continue
        if norm["text"] in seen:
            continue
        seen.add(norm["text"])
        merged.append(norm)
        appended += 1
    return merged, kept, appended


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reviewed", type=Path, required=True)
    p.add_argument("--training", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print summary; do not write output.",
    )
    args = p.parse_args(argv)

    reviewed = list(_iter_jsonl(args.reviewed))
    training = list(_iter_jsonl(args.training))
    merged, kept, appended = merge(reviewed, training)

    print(
        f"reviewed={len(reviewed)} training={len(training)} "
        f"kept={kept} appended={appended} total={len(merged)}",
        file=sys.stderr,
    )
    if args.dry_run:
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
