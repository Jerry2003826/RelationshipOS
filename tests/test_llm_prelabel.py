"""Tests for scripts/llm_prelabel.py — no network, mock label_fn."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "llm_prelabel",
    Path(__file__).resolve().parents[1] / "scripts" / "llm_prelabel.py",
)
assert _SPEC and _SPEC.loader
llm_prelabel = importlib.util.module_from_spec(_SPEC)
sys.modules["llm_prelabel"] = llm_prelabel
_SPEC.loader.exec_module(llm_prelabel)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_valid_label_roundtrip(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(inp, [{"turn_id": "t1", "text": "你今天还好吗"}])

    def fn(text: str) -> dict:
        return {"label": "LIGHT_RECALL", "confidence": 0.82, "reason": "情感接住"}

    n = llm_prelabel.run(inp, out, label_fn=fn)
    assert n == 1
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["label"] == "LIGHT_RECALL"
    assert rows[0]["confidence"] == 0.82
    assert rows[0]["source"] == "llm_prelabel"
    assert rows[0]["turn_id"] == "t1"


def test_invalid_label_rejected(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(inp, [{"turn_id": "t1", "text": "嗨"}])

    def fn(text: str) -> dict:
        return {"label": "NONSENSE", "confidence": 0.99}

    n = llm_prelabel.run(inp, out, label_fn=fn)
    assert n == 0
    assert out.read_text(encoding="utf-8") == ""


def test_duplicate_text_deduped(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(
        inp,
        [
            {"turn_id": "a", "text": "你好呀"},
            {"turn_id": "b", "text": "你好呀"},
        ],
    )

    calls: list[str] = []

    def fn(text: str) -> dict:
        calls.append(text)
        return {"label": "FAST_PONG", "confidence": 0.9}

    n = llm_prelabel.run(inp, out, label_fn=fn)
    assert n == 1
    assert calls == ["你好呀"]


def test_confidence_clamped(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(
        inp,
        [
            {"turn_id": "t1", "text": "第一句"},
            {"turn_id": "t2", "text": "第二句"},
        ],
    )

    answers = [
        {"label": "DEEP_THINK", "confidence": 2.5},
        {"label": "FAST_PONG", "confidence": -1.0},
    ]
    idx = {"i": 0}

    def fn(text: str) -> dict:
        a = answers[idx["i"]]
        idx["i"] += 1
        return a

    n = llm_prelabel.run(inp, out, label_fn=fn)
    assert n == 2
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["confidence"] == 1.0
    assert rows[1]["confidence"] == 0.0


def test_skip_label_kind_rows(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(
        inp,
        [
            {"kind": "label", "text": "已标注", "label": "FAST_PONG"},
            {"turn_id": "t2", "text": "新消息"},
        ],
    )

    def fn(text: str) -> dict:
        assert text == "新消息"
        return {"label": "LIGHT_RECALL", "confidence": 0.7}

    n = llm_prelabel.run(inp, out, label_fn=fn)
    assert n == 1


def test_short_text_filtered(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(
        inp,
        [
            {"turn_id": "t1", "text": "嗨"},
            {"turn_id": "t2", "text": "你今天还好吗"},
        ],
    )

    def fn(text: str) -> dict:
        return {"label": "FAST_PONG", "confidence": 0.9}

    n = llm_prelabel.run(inp, out, label_fn=fn, min_text_len=3)
    assert n == 1


def test_label_fn_exception_swallowed(tmp_path: Path) -> None:
    inp = tmp_path / "shadow.jsonl"
    out = tmp_path / "silver.jsonl"
    _write_jsonl(
        inp,
        [
            {"turn_id": "t1", "text": "会炸的一条"},
            {"turn_id": "t2", "text": "正常的一条"},
        ],
    )

    def fn(text: str) -> dict:
        if "炸" in text:
            raise RuntimeError("boom")
        return {"label": "DEEP_THINK", "confidence": 0.8}

    n = llm_prelabel.run(inp, out, label_fn=fn)
    assert n == 1
