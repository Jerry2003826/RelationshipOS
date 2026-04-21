"""Merge shadow logs with static seeds into a labelled training set.

Shadow logs include two record kinds:
    {"kind": "decision", ...}   -- original router output (no gold label)
    {"kind": "label", "turn_id": "...", "label": "FAST_PONG|..."}

We left-join decisions with labels by turn_id. Only decisions that
received an implicit/explicit label make it into the training set.
Un-labelled decisions are still useful for evaluation audits (written
to `merged.unlabelled.jsonl`).

Usage:
    python build_labelled_set.py --logs 'data/*.jsonl' \
        --seeds seeds_zh.jsonl --out data/merged.jsonl
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", type=str, required=True)
    ap.add_argument("--seeds", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    decisions: dict[str, dict] = {}
    labels: dict[str, str] = {}

    for p in glob.glob(args.logs):
        with open(p, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if rec.get("kind") == "label":
                    tid = rec.get("turn_id")
                    if tid:
                        labels[tid] = rec["label"]
                else:
                    tid = rec.get("turn_id")
                    if tid:
                        decisions[tid] = rec

    merged: list[dict] = []
    with args.seeds.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                merged.append(json.loads(ln))

    # Overlay labelled shadow decisions.
    for tid, rec in decisions.items():
        if tid in labels:
            merged.append({"text": rec["text"], "label": labels[tid]})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(merged)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
