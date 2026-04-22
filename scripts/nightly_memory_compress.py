#!/usr/bin/env python3
"""Nightly memory compression for RelationshipOS.

Reads the last 24h of shadow-log JSONL (emitted by ``JsonlShadowLogger``),
groups turns by user/session, asks an LLM to distill each group into a
short memory card, and writes the result to
``memory/compressed_YYYYMMDD.jsonl``.

The compressed cards become the long-term memory that LIGHT_RECALL /
DEEP_THINK routes can recall without replaying the raw turn stream.

Schema of each output row::

    {
      "date":        "2026-04-22",
      "user_id":     "u_abc",          # or "anonymous"
      "session_id":  "s_123",
      "turn_count":  7,
      "summary":     "<=120 字中文要点",
      "tags":        ["emotion", "plan"],
      "source":      "nightly_memory_compress"
    }

The LLM client is pluggable so unit tests run entirely offline.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

SummariseFn = Callable[[list[str]], dict]

_PROMPT_TEMPLATE = """你是一个中文对话记忆压缩器。
下面是同一个用户在一次会话里按时间顺序说的话。
请抽出对未来对话有用的长期记忆,输出一个 JSON:

  summary  —— 不超过 120 字的中文要点,只保留情感/事件/偏好
  tags     —— 从 [emotion, plan, preference, fact, risk] 里最多选 3 个

不要输出其它字段,不要展开细节。

对话:
{texts}
"""


@dataclass
class MemoryCard:
    date: str
    user_id: str
    session_id: str
    turn_count: int
    summary: str
    tags: list[str]

    def to_jsonl(self) -> str:
        return json.dumps(
            {
                "date": self.date,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "turn_count": self.turn_count,
                "summary": self.summary,
                "tags": self.tags,
                "source": "nightly_memory_compress",
            },
            ensure_ascii=False,
        )


VALID_TAGS = {"emotion", "plan", "preference", "fact", "risk"}


def _parse_ts(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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


def group_by_session(
    records: Iterable[dict],
    *,
    since: datetime | None = None,
) -> dict[tuple[str, str], list[str]]:
    """Return {(user_id, session_id) -> list of texts in ts order}."""
    rows: list[tuple[datetime, str, str, str]] = []
    for rec in records:
        text = str(rec.get("text") or "").strip()
        if not text:
            continue
        ts = _parse_ts(rec.get("ts"))
        if ts is None:
            ts = datetime(1970, 1, 1, tzinfo=UTC)
        if since is not None and ts < since:
            continue
        user_id = str(rec.get("user_id") or "anonymous")
        session_id = str(rec.get("session_id") or "default")
        rows.append((ts, user_id, session_id, text))
    rows.sort(key=lambda r: r[0])
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for _ts, user_id, session_id, text in rows:
        grouped[(user_id, session_id)].append(text)
    return grouped


def compress_group(
    texts: list[str],
    *,
    summarise_fn: SummariseFn,
) -> tuple[str, list[str]] | None:
    if not texts:
        return None
    try:
        raw = summarise_fn(texts)
    except Exception as exc:  # noqa: BLE001
        print(f"summarise failed: {exc}", file=sys.stderr)
        return None
    summary = str(raw.get("summary") or "").strip()
    if not summary:
        return None
    summary = summary[:240]  # hard cap for safety
    tags_in = raw.get("tags") or []
    if not isinstance(tags_in, list):
        tags_in = []
    tags = [str(t).strip().lower() for t in tags_in]
    tags = [t for t in tags if t in VALID_TAGS][:3]
    return summary, tags


def run(
    input_path: Path,
    output_path: Path,
    *,
    summarise_fn: SummariseFn,
    now: datetime | None = None,
    window_hours: int = 24,
) -> int:
    now = now or datetime.now(UTC)
    since = now - timedelta(hours=window_hours)
    date_str = now.strftime("%Y-%m-%d")
    grouped = group_by_session(_iter_jsonl(input_path), since=since)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        for (user_id, session_id), texts in grouped.items():
            result = compress_group(texts, summarise_fn=summarise_fn)
            if result is None:
                continue
            summary, tags = result
            card = MemoryCard(
                date=date_str,
                user_id=user_id,
                session_id=session_id,
                turn_count=len(texts),
                summary=summary,
                tags=tags,
            )
            f.write(card.to_jsonl() + "\n")
            count += 1
    return count


# ------------------------------------------------------------------ CLI


def _default_summarise_fn(model: str) -> SummariseFn:
    import litellm  # type: ignore[import-not-found]

    def call(texts: list[str]) -> dict:
        joined = "\n".join(f"- {t}" for t in texts)
        resp = litellm.completion(  # type: ignore[no-untyped-call]
            model=model,
            messages=[
                {"role": "system", "content": "只输出 JSON。"},
                {
                    "role": "user",
                    "content": _PROMPT_TEMPLATE.format(texts=joined),
                },
            ],
            temperature=0.0,
            max_tokens=240,
            response_format={"type": "json_object"},
        )
        content = resp["choices"][0]["message"]["content"]
        return json.loads(content)

    return call


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSONL path; defaults to memory/compressed_YYYYMMDD.jsonl",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("ROUTER_MEMORY_MODEL", "deepseek-chat"),
    )
    p.add_argument("--window-hours", type=int, default=24)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print group sizes but do not call the LLM.",
    )
    args = p.parse_args(argv)

    now = datetime.now(UTC)
    output = args.output or Path(f"memory/compressed_{now:%Y%m%d}.jsonl")

    if args.dry_run:
        grouped = group_by_session(
            _iter_jsonl(args.input),
            since=now - timedelta(hours=args.window_hours),
        )
        for (user_id, session_id), texts in grouped.items():
            print(f"{user_id}/{session_id}: {len(texts)} turns")
        print(f"total groups: {len(grouped)} -> {output}")
        return 0

    summarise_fn = _default_summarise_fn(args.model)
    n = run(
        args.input,
        output,
        summarise_fn=summarise_fn,
        now=now,
        window_hours=args.window_hours,
    )
    print(f"wrote {n} memory cards -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
