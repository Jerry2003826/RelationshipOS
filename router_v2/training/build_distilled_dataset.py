"""Build the distilled training/holdout/test split for Router v2.

Inputs:
    - seeds_zh.jsonl            (121 hand-written gold seeds)
    - silver_zh.jsonl           (369 LLM-distilled silver labels)
    - distilled_claude.jsonl    (767+ hand-distilled by Claude, 2026-04-22)

Outputs:
    - training_zh.jsonl         (stratified 70% train)
    - holdout_zh.jsonl          (stratified 15% dev)
    - test_zh.jsonl             (stratified 15% frozen test)

Design:
- Fully deterministic (seed=20260422).
- Dedup by exact-text.
- Stratified per-class split so tiny FAST_PONG/LIGHT_RECALL/DEEP_THINK
  classes keep balanced proportions across splits.
- "source" field is preserved so the eval script can report per-source
  agreement and catch any over-reliance on silver labels.

Usage:
    python -m router_v2.training.build_distilled_dataset \
        --in-dir router_v2/training --out-dir router_v2/training
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

SEED = 20260422
TRAIN_RATIO = 0.70
HOLDOUT_RATIO = 0.15
# test = 1 - TRAIN - HOLDOUT = 0.15


def _load(path: Path, tag: str) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec.setdefault("source", tag)
            rows.append(rec)
    return rows


def _dedup_by_text(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        t = r.get("text", "").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(r)
    return out


def _stratified_split(
    rows: list[dict], train_ratio: float, holdout_ratio: float, seed: int
) -> tuple[list[dict], list[dict], list[dict]]:
    rng = random.Random(seed)
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    train: list[dict] = []
    holdout: list[dict] = []
    test: list[dict] = []
    for _label, items in by_label.items():
        rng.shuffle(items)
        n = len(items)
        n_train = int(round(n * train_ratio))
        n_hold = int(round(n * holdout_ratio))
        # Guard edges on tiny classes.
        n_train = max(1, min(n_train, n - 2))
        n_hold = max(1, min(n_hold, n - n_train - 1))
        train.extend(items[:n_train])
        holdout.extend(items[n_train : n_train + n_hold])
        test.extend(items[n_train + n_hold :])
    rng.shuffle(train)
    rng.shuffle(holdout)
    rng.shuffle(test)
    return train, holdout, test


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", type=Path, default=Path("router_v2/training"))
    ap.add_argument("--out-dir", type=Path, default=Path("router_v2/training"))
    args = ap.parse_args()

    seeds = _load(args.in_dir / "seeds_zh.jsonl", "seed_gold")
    silver = _load(args.in_dir / "silver_zh.jsonl", "silver_llm")
    distilled = _load(args.in_dir / "distilled_claude.jsonl", "claude_distill")

    print(f"seeds    : {len(seeds):>4d}")
    print(f"silver   : {len(silver):>4d}")
    print(f"distilled: {len(distilled):>4d}")

    all_rows = seeds + silver + distilled
    unique = _dedup_by_text(all_rows)
    print(f"merged   : {len(all_rows):>4d}")
    print(f"deduped  : {len(unique):>4d}")

    # Class distribution after dedup.
    dist: dict[str, int] = defaultdict(int)
    src_dist: dict[str, int] = defaultdict(int)
    for r in unique:
        dist[r["label"]] += 1
        src_dist[r.get("source", "?")] += 1
    print("class dist:", dict(dist))
    print("source dist:", dict(src_dist))

    train, holdout, test = _stratified_split(unique, TRAIN_RATIO, HOLDOUT_RATIO, SEED)
    print(f"train    : {len(train):>4d}")
    print(f"holdout  : {len(holdout):>4d}")
    print(f"test     : {len(test):>4d}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write(args.out_dir / "training_zh.jsonl", train)
    _write(args.out_dir / "holdout_zh.jsonl", holdout)
    _write(args.out_dir / "test_zh.jsonl", test)
    print(f"wrote: {args.out_dir}/{{training,holdout,test}}_zh.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
