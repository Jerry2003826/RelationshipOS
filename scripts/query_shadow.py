#!/usr/bin/env python3
"""Query the router shadow-log JSONL.

Usage::

    python scripts/query_shadow.py path/to/shadow.jsonl \
        --route FAST_PONG \
        --min-conf 0.9 \
        --since 2026-04-01

Prints matching records one per line. Designed for spot-checking and for
feeding labelled subsets into ``router_v2/training/build_labelled_set.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def _parse_since(value: str | None) -> float | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.timestamp()


def iter_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def filter_records(
    records: list[dict],
    *,
    route: str | None,
    min_conf: float,
    since_ts: float | None,
    only_shadow: bool,
) -> list[dict]:
    out: list[dict] = []
    for rec in records:
        if rec.get("kind") == "label":
            continue
        if route is not None and rec.get("route_type") != route:
            continue
        if rec.get("confidence", 0.0) < min_conf:
            continue
        if since_ts is not None and rec.get("ts", 0.0) < since_ts:
            continue
        if only_shadow and not rec.get("note", "").startswith("shadow"):
            # The router only calls the logger for ambiguous / shadow cases,
            # so this filter is usually a no-op — kept for forward compat.
            continue
        out.append(rec)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument(
        "--route",
        choices=("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"),
        default=None,
    )
    p.add_argument("--min-conf", type=float, default=0.0)
    p.add_argument("--since", type=str, default=None)
    p.add_argument("--only-shadow", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args(argv)

    if not args.path.exists():
        print(f"shadow log not found: {args.path}", file=sys.stderr)
        return 2

    records = iter_records(args.path)
    filtered = filter_records(
        records,
        route=args.route,
        min_conf=args.min_conf,
        since_ts=_parse_since(args.since),
        only_shadow=args.only_shadow,
    )
    if args.limit:
        filtered = filtered[: args.limit]
    for rec in filtered:
        print(json.dumps(rec, ensure_ascii=False))
    print(
        f"# total={len(records)} matched={len(filtered)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
