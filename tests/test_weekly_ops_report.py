"""Tests for scripts/weekly_ops_report.py — offline."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "weekly_ops_report",
    Path(__file__).resolve().parents[1] / "scripts" / "weekly_ops_report.py",
)
assert _SPEC and _SPEC.loader
wor = importlib.util.module_from_spec(_SPEC)
sys.modules["weekly_ops_report"] = wor
_SPEC.loader.exec_module(wor)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_collect_shadow_stats_counts_routes_and_days() -> None:
    records = [
        {
            "ts": "2026-04-20T09:00:00+00:00",
            "route": "FAST_PONG",
            "user_id": "u1",
        },
        {
            "ts": "2026-04-20T10:00:00+00:00",
            "route": "DEEP_THINK",
            "user_id": "u2",
        },
        {
            "ts": "2026-04-21T10:00:00+00:00",
            "route": "LIGHT_RECALL",
            "user_id": "u1",
        },
        # Outside window, should be ignored
        {"ts": "2026-04-10T10:00:00+00:00", "route": "FAST_PONG"},
        # Invalid label, should be ignored for route_counts
        {
            "ts": "2026-04-21T11:00:00+00:00",
            "route": "UNKNOWN",
            "user_id": "u3",
        },
    ]
    since = datetime(2026, 4, 19, tzinfo=UTC)
    until = datetime(2026, 4, 22, tzinfo=UTC)
    routes, per_day, users = wor.collect_shadow_stats(
        records, since=since, until=until
    )
    assert routes["FAST_PONG"] == 1
    assert routes["LIGHT_RECALL"] == 1
    assert routes["DEEP_THINK"] == 1
    assert "UNKNOWN" not in routes
    assert per_day["2026-04-20"] == 2
    assert per_day["2026-04-21"] == 2
    assert users == {"u1", "u2", "u3"}


def test_collect_silver_stats_threshold() -> None:
    records = [
        {"confidence": 0.9},
        {"confidence": 0.7},
        {"confidence": 0.69},
        {"confidence": "n/a"},
        {},
    ]
    total, high = wor.collect_silver_stats(records, high_conf_threshold=0.7)
    assert total == 5
    assert high == 2


def test_build_stats_end_to_end(tmp_path: Path) -> None:
    shadow = tmp_path / "shadow.jsonl"
    silver = tmp_path / "silver.jsonl"
    metrics = tmp_path / "metrics.json"
    _write_jsonl(
        shadow,
        [
            {
                "ts": "2026-04-18T10:00:00+00:00",
                "route": "FAST_PONG",
                "user_id": "u1",
            },
            {
                "ts": "2026-04-21T10:00:00+00:00",
                "route": "DEEP_THINK",
                "user_id": "u2",
            },
        ],
    )
    _write_jsonl(
        silver,
        [
            {"confidence": 0.92},
            {"confidence": 0.5},
        ],
    )
    metrics.write_text(json.dumps({"macro_f1": 0.835}), encoding="utf-8")

    now = datetime(2026, 4, 22, tzinfo=UTC)
    stats = wor.build_stats(
        shadow_path=shadow,
        silver_path=silver,
        metrics_path=metrics,
        now=now,
    )
    assert stats.route_counts["FAST_PONG"] == 1
    assert stats.route_counts["DEEP_THINK"] == 1
    assert stats.silver_total == 2
    assert stats.silver_high_conf == 1
    assert stats.silver_rate == 0.5
    assert stats.macro_f1 == 0.835
    assert stats.profile_users == 2
    assert stats.total == 2
    assert stats.week.startswith("2026-W")


def test_build_stats_missing_metrics(tmp_path: Path) -> None:
    shadow = tmp_path / "shadow.jsonl"
    _write_jsonl(shadow, [])
    stats = wor.build_stats(
        shadow_path=shadow,
        silver_path=None,
        metrics_path=tmp_path / "nope.json",
        now=datetime(2026, 4, 22, tzinfo=UTC),
    )
    assert stats.macro_f1 is None
    assert stats.total == 0


def test_render_markdown_has_all_sections() -> None:
    stats = wor.WeeklyStats(
        week="2026-W17",
        since="2026-04-15",
        until="2026-04-22",
    )
    stats.route_counts.update(
        {"FAST_PONG": 40, "LIGHT_RECALL": 30, "DEEP_THINK": 30}
    )
    stats.per_day_counts.update({"2026-04-20": 50, "2026-04-21": 50})
    stats.silver_total = 10
    stats.silver_high_conf = 7
    stats.profile_users = 3
    stats.macro_f1 = 0.82

    md = wor.render_markdown(stats, narrative="系统平稳,无异常。")
    assert "运维周报 2026-W17" in md
    assert "路由分布" in md
    assert "FAST_PONG" in md
    assert "日均采样量" in md
    assert "2026-04-20" in md
    assert "银标转化" in md
    assert "70.0%" in md
    assert "用户画像覆盖" in md
    assert "回训健康度" in md
    assert "0.820" in md
    assert "✅" in md
    assert "一周观察" in md
    assert "系统平稳" in md


def test_render_markdown_flags_low_f1() -> None:
    stats = wor.WeeklyStats(
        week="2026-W17", since="2026-04-15", until="2026-04-22"
    )
    stats.macro_f1 = 0.60
    md = wor.render_markdown(stats)
    assert "⚠️" in md
    assert "0.600" in md


def test_render_markdown_without_narrative_omits_section() -> None:
    stats = wor.WeeklyStats(
        week="2026-W17", since="2026-04-15", until="2026-04-22"
    )
    md = wor.render_markdown(stats)
    assert "一周观察" not in md
