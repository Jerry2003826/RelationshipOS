"""Tests for scripts/review_labels.py and scripts/merge_labels.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


review_labels = _load("review_labels")
merge_labels = _load("merge_labels")


# ---------------------------------------------------------------- review
def test_filter_low_confidence_keeps_below_threshold() -> None:
    records = [
        {"text": "a", "confidence": 0.6},
        {"text": "b", "confidence": 0.7},
        {"text": "c", "confidence": 0.71},
        {"text": "d", "confidence": 0.99},
    ]
    out = list(review_labels.filter_low_confidence(records, max_conf=0.7))
    texts = [r["text"] for r in out]
    assert texts == ["a", "b"]


def test_filter_low_confidence_handles_missing_conf() -> None:
    records = [{"text": "x"}, {"text": "y", "confidence": "not-a-number"}]
    out = list(review_labels.filter_low_confidence(records, max_conf=0.5))
    assert [r["text"] for r in out] == ["x", "y"]


# ---------------------------------------------------------------- merge
def test_merge_appends_new_texts_only() -> None:
    training = [
        {"text": "老样本 A", "label": "FAST_PONG", "source": "claude_distill"},
        {"text": "老样本 B", "label": "DEEP_THINK", "source": "claude_distill"},
    ]
    reviewed = [
        {"text": "老样本 A", "label": "LIGHT_RECALL", "source": "human_review"},
        {
            "text": "新样本 C",
            "label": "LIGHT_RECALL",
            "confidence": 0.95,
            "reason": "情感接住",
        },
        {"text": "", "label": "FAST_PONG"},  # drop empty
        {"text": "坏标签", "label": "NONSENSE"},  # drop invalid
    ]
    merged, kept, appended = merge_labels.merge(reviewed, training)
    assert kept == 2
    assert appended == 1
    assert [m["text"] for m in merged] == ["老样本 A", "老样本 B", "新样本 C"]
    new = merged[-1]
    assert new["label"] == "LIGHT_RECALL"
    assert new["source"] == "human_review"
    assert new["confidence"] == 0.95
    assert new["reason"] == "情感接住"


def test_merge_is_idempotent_on_rerun(tmp_path: Path) -> None:
    reviewed_path = tmp_path / "reviewed.jsonl"
    training_path = tmp_path / "training.jsonl"
    output_path = tmp_path / "out.jsonl"

    training_path.write_text(
        json.dumps({"text": "旧样本", "label": "FAST_PONG"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    reviewed_path.write_text(
        json.dumps(
            {"text": "新样本", "label": "DEEP_THINK", "confidence": 1.0},
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    merge_labels.main(
        [
            "--reviewed",
            str(reviewed_path),
            "--training",
            str(training_path),
            "--output",
            str(output_path),
        ]
    )
    first = output_path.read_text(encoding="utf-8").splitlines()

    # Feed the merged file back in as training — should be unchanged.
    merge_labels.main(
        [
            "--reviewed",
            str(reviewed_path),
            "--training",
            str(output_path),
            "--output",
            str(output_path),
        ]
    )
    second = output_path.read_text(encoding="utf-8").splitlines()
    assert first == second
    assert len(second) == 2


def test_merge_clamps_confidence() -> None:
    training: list[dict] = []
    reviewed = [{"text": "clamp me", "label": "FAST_PONG", "confidence": 5.0}]
    merged, _, _ = merge_labels.merge(reviewed, training)
    assert merged[0]["confidence"] == 1.0
