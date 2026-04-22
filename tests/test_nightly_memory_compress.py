"""Tests for scripts/nightly_memory_compress.py — offline."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "nightly_memory_compress",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "nightly_memory_compress.py",
)
assert _SPEC and _SPEC.loader
nightly = importlib.util.module_from_spec(_SPEC)
sys.modules["nightly_memory_compress"] = nightly
_SPEC.loader.exec_module(nightly)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_group_by_session_sorts_and_partitions(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    _write_jsonl(
        inp,
        [
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-22T10:00:00+00:00",
                "text": "第二",
            },
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-22T09:00:00+00:00",
                "text": "第一",
            },
            {
                "user_id": "u2",
                "session_id": "s1",
                "ts": "2026-04-22T09:30:00+00:00",
                "text": "另一用户",
            },
        ],
    )
    records = list(nightly._iter_jsonl(inp))
    grouped = nightly.group_by_session(records)
    assert grouped[("u1", "s1")] == ["第一", "第二"]
    assert grouped[("u2", "s1")] == ["另一用户"]


def test_group_by_session_applies_since_filter(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    _write_jsonl(
        inp,
        [
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-20T09:00:00+00:00",
                "text": "太久以前",
            },
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-22T09:00:00+00:00",
                "text": "昨天",
            },
        ],
    )
    since = datetime(2026, 4, 21, tzinfo=UTC)
    grouped = nightly.group_by_session(
        nightly._iter_jsonl(inp), since=since
    )
    assert grouped == {("u1", "s1"): ["昨天"]}


def test_compress_group_clamps_tags_and_summary() -> None:
    def fn(texts: list[str]) -> dict:
        return {
            "summary": "他今天很累,想抱抱",
            "tags": ["emotion", "plan", "unknown", "risk", "fact"],
        }

    result = nightly.compress_group(["累"], summarise_fn=fn)
    assert result is not None
    summary, tags = result
    assert summary == "他今天很累,想抱抱"
    # unknown filtered, capped at 3
    assert tags == ["emotion", "plan", "risk"]


def test_compress_group_rejects_empty_summary() -> None:
    def fn(texts: list[str]) -> dict:
        return {"summary": "", "tags": ["emotion"]}

    assert nightly.compress_group(["x"], summarise_fn=fn) is None


def test_compress_group_swallows_exception() -> None:
    def fn(texts: list[str]) -> dict:
        raise RuntimeError("boom")

    assert nightly.compress_group(["x"], summarise_fn=fn) is None


def test_run_writes_one_card_per_group(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "compressed.jsonl"
    _write_jsonl(
        inp,
        [
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-22T09:00:00+00:00",
                "text": "累",
            },
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-22T10:00:00+00:00",
                "text": "想休息",
            },
            {
                "user_id": "u2",
                "session_id": "s9",
                "ts": "2026-04-22T11:00:00+00:00",
                "text": "工作压力",
            },
        ],
    )

    def fn(texts: list[str]) -> dict:
        return {"summary": "要点:" + ";".join(texts), "tags": ["emotion"]}

    now = datetime(2026, 4, 22, 12, 0, tzinfo=UTC)
    n = nightly.run(inp, out, summarise_fn=fn, now=now, window_hours=24)
    assert n == 2
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    by_key = {(r["user_id"], r["session_id"]): r for r in rows}
    u1 = by_key[("u1", "s1")]
    assert u1["turn_count"] == 2
    assert u1["date"] == "2026-04-22"
    assert u1["tags"] == ["emotion"]
    assert u1["source"] == "nightly_memory_compress"
    assert "累" in u1["summary"]
    assert ("u2", "s9") in by_key


def test_run_skips_empty_text(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "compressed.jsonl"
    _write_jsonl(
        inp,
        [
            {"user_id": "u1", "session_id": "s1", "text": ""},
            {"user_id": "u1", "session_id": "s1", "text": "   "},
        ],
    )

    def fn(texts: list[str]) -> dict:
        raise AssertionError("should not be called")

    n = nightly.run(inp, out, summarise_fn=fn, now=datetime.now(UTC))
    assert n == 0


def test_run_creates_output_directory(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "nested" / "dir" / "compressed.jsonl"
    _write_jsonl(
        inp,
        [
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2026-04-22T10:00:00+00:00",
                "text": "hi",
            }
        ],
    )

    def fn(texts: list[str]) -> dict:
        return {"summary": "招呼", "tags": ["emotion"]}

    now = datetime(2026, 4, 22, 12, 0, tzinfo=UTC)
    n = nightly.run(inp, out, summarise_fn=fn, now=now)
    assert n == 1
    assert out.exists()
