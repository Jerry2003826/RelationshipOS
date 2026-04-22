"""Tests for scripts/labeling_metrics.py — no network."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "labeling_metrics",
    Path(__file__).resolve().parents[1] / "scripts" / "labeling_metrics.py",
)
assert _SPEC and _SPEC.loader
lm = importlib.util.module_from_spec(_SPEC)
sys.modules["labeling_metrics"] = lm
_SPEC.loader.exec_module(lm)


def test_compute_metrics_all_high_confidence() -> None:
    silver = [{"confidence": 0.9} for _ in range(10)]
    m = lm.compute_metrics(silver=silver)
    assert m["silver_total"] == 10
    assert m["auto_accepted"] == 10
    assert m["human_reviewed"] == 0
    # total = 10 * 2 = 20, baseline = 10 * 60 = 600, speedup = 30x
    assert m["total_secs"] == 20.0
    assert m["baseline_secs_all"] == 600.0
    assert m["speedup_x"] == 30.0


def test_compute_metrics_mixed_confidence_hits_four_x() -> None:
    # 60% auto, 40% human; defaults: baseline=60, auto=2, human=20
    silver = [{"confidence": 0.9}] * 6 + [{"confidence": 0.5}] * 4
    m = lm.compute_metrics(silver=silver)
    assert m["auto_accepted"] == 6
    assert m["human_reviewed"] == 4
    # total = 6*2 + 4*20 = 92; baseline = 600; speedup ≈ 6.52x
    assert m["speedup_x"] >= 4.0


def test_compute_metrics_all_low_confidence_no_speedup_gate() -> None:
    silver = [{"confidence": 0.1} for _ in range(10)]
    m = lm.compute_metrics(silver=silver)
    # everything goes to human: total = 200, baseline = 600, speedup = 3.0x
    assert m["auto_accepted"] == 0
    assert m["human_reviewed"] == 10
    assert m["speedup_x"] == 3.0


def test_compute_metrics_empty_silver() -> None:
    m = lm.compute_metrics(silver=[])
    assert m["silver_total"] == 0
    assert m["speedup_x"] == 0.0
    assert m["avg_silver_conf"] == 0.0


def test_compute_metrics_handles_missing_confidence() -> None:
    silver = [{}, {"confidence": "n/a"}, {"confidence": 0.95}]
    m = lm.compute_metrics(silver=silver)
    assert m["auto_accepted"] == 1
    assert m["human_reviewed"] == 2


def test_compute_metrics_counts_human_reviewed_rows() -> None:
    silver = [{"confidence": 0.5}, {"confidence": 0.5}]
    reviewed = [
        {"source": "human_review"},
        {"source": "human_review"},
        {"source": "llm_prelabel"},  # ignored
    ]
    m = lm.compute_metrics(silver=silver, reviewed=reviewed)
    assert m["human_kept"] == 2


def test_render_markdown_gate_flags() -> None:
    silver = [{"confidence": 0.1}] * 10  # 3.0x
    m = lm.compute_metrics(silver=silver)
    md = lm.render_markdown(m, gate=4.0)
    assert "⚠️" in md
    assert "低于 4.0" in md

    silver_hi = [{"confidence": 0.95}] * 10
    m_hi = lm.compute_metrics(silver=silver_hi)
    md_hi = lm.render_markdown(m_hi, gate=4.0)
    assert "✅" in md_hi


def test_main_exits_nonzero_below_gate(tmp_path: Path) -> None:
    silver_path = tmp_path / "silver.jsonl"
    with silver_path.open("w", encoding="utf-8") as f:
        for _ in range(10):
            f.write(json.dumps({"confidence": 0.1}) + "\n")

    out_json = tmp_path / "m.json"
    rc = lm.main(
        [
            "--silver",
            str(silver_path),
            "--output-json",
            str(out_json),
            "--gate",
            "4.0",
        ]
    )
    assert rc == 2
    m = json.loads(out_json.read_text(encoding="utf-8"))
    assert m["speedup_x"] == 3.0


def test_main_empty_silver_is_not_failure(tmp_path: Path) -> None:
    silver_path = tmp_path / "silver.jsonl"
    silver_path.write_text("", encoding="utf-8")
    rc = lm.main(["--silver", str(silver_path), "--gate", "4.0"])
    assert rc == 0


def test_main_writes_markdown(tmp_path: Path) -> None:
    silver_path = tmp_path / "silver.jsonl"
    with silver_path.open("w", encoding="utf-8") as f:
        for _ in range(10):
            f.write(json.dumps({"confidence": 0.95}) + "\n")
    md_path = tmp_path / "out.md"
    rc = lm.main(
        [
            "--silver",
            str(silver_path),
            "--output-md",
            str(md_path),
            "--gate",
            "4.0",
        ]
    )
    assert rc == 0
    text = md_path.read_text(encoding="utf-8")
    assert "提速" in text
    assert "✅" in text
