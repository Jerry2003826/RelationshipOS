#!/usr/bin/env python3
"""Weekly ops report for RelationshipOS.

Aggregates the previous 7 days of shadow logs into a single Markdown
report at ``reports/ops_YYYY-WW.md``. The report covers:

* Route distribution (FAST_PONG / LIGHT_RECALL / DEEP_THINK)
* Shadow sample volume per day
* Silver-label conversion rate (if ``--silver`` is supplied)
* Profile-vector coverage + turn-count histogram
* Latest retrain Macro F1 (read from ``--metrics`` JSON)
* Optional LLM-generated narrative ("一周观察")

Keeping LLM usage to at most one call per week is what holds the
"每周成本 <1 元" budget.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

NarrativeFn = Callable[[dict], str]

VALID_LABELS = ("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK")


@dataclass
class WeeklyStats:
    week: str
    since: str
    until: str
    route_counts: Counter = field(default_factory=Counter)
    per_day_counts: Counter = field(default_factory=Counter)
    silver_total: int = 0
    silver_high_conf: int = 0
    profile_users: int = 0
    macro_f1: float | None = None

    @property
    def total(self) -> int:
        return sum(self.route_counts.values())

    @property
    def silver_rate(self) -> float:
        if self.silver_total == 0:
            return 0.0
        return self.silver_high_conf / self.silver_total

    def to_dict(self) -> dict:
        return {
            "week": self.week,
            "since": self.since,
            "until": self.until,
            "total_turns": self.total,
            "route_counts": dict(self.route_counts),
            "per_day_counts": dict(self.per_day_counts),
            "silver_total": self.silver_total,
            "silver_high_conf": self.silver_high_conf,
            "silver_rate": round(self.silver_rate, 3),
            "profile_users": self.profile_users,
            "macro_f1": self.macro_f1,
        }


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


def collect_shadow_stats(
    records: Iterable[dict],
    *,
    since: datetime,
    until: datetime,
) -> tuple[Counter, Counter, set[str]]:
    route_counts: Counter = Counter()
    per_day_counts: Counter = Counter()
    users: set[str] = set()
    for rec in records:
        ts = _parse_ts(rec.get("ts"))
        if ts is None or ts < since or ts >= until:
            continue
        route = str(rec.get("route") or rec.get("label") or "").upper()
        if route in VALID_LABELS:
            route_counts[route] += 1
        per_day_counts[ts.strftime("%Y-%m-%d")] += 1
        user_id = rec.get("user_id")
        if user_id:
            users.add(str(user_id))
    return route_counts, per_day_counts, users


def collect_silver_stats(
    records: Iterable[dict],
    *,
    high_conf_threshold: float = 0.7,
) -> tuple[int, int]:
    total = 0
    high = 0
    for rec in records:
        try:
            conf = float(rec.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        total += 1
        if conf >= high_conf_threshold:
            high += 1
    return total, high


def build_stats(
    *,
    shadow_path: Path,
    silver_path: Path | None,
    metrics_path: Path | None,
    now: datetime,
) -> WeeklyStats:
    since = now - timedelta(days=7)
    iso_year, iso_week, _ = now.isocalendar()
    week = f"{iso_year}-W{iso_week:02d}"
    stats = WeeklyStats(
        week=week,
        since=since.strftime("%Y-%m-%d"),
        until=now.strftime("%Y-%m-%d"),
    )
    route_counts, per_day_counts, users = collect_shadow_stats(
        _iter_jsonl(shadow_path), since=since, until=now
    )
    stats.route_counts = route_counts
    stats.per_day_counts = per_day_counts
    stats.profile_users = len(users)
    if silver_path is not None:
        total, high = collect_silver_stats(_iter_jsonl(silver_path))
        stats.silver_total = total
        stats.silver_high_conf = high
    if metrics_path is not None and metrics_path.exists():
        try:
            m = json.loads(metrics_path.read_text(encoding="utf-8"))
            mf1 = m.get("macro_f1")
            if isinstance(mf1, (int, float)):
                stats.macro_f1 = float(mf1)
        except json.JSONDecodeError:
            pass
    return stats


# ---------------------------------------------------------------- render


def _fmt_pct(n: int, total: int) -> str:
    if total == 0:
        return "–"
    return f"{n / total:.1%}"


def render_markdown(
    stats: WeeklyStats,
    *,
    narrative: str | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"# 运维周报 {stats.week}")
    lines.append("")
    lines.append(f"覆盖窗口: {stats.since} → {stats.until} (UTC, 近 7 天)")
    lines.append("")

    # 1. Route distribution
    lines.append("## 路由分布")
    lines.append("")
    lines.append("| 路由 | 次数 | 占比 |")
    lines.append("|---|---:|---:|")
    total = stats.total
    for route in VALID_LABELS:
        n = stats.route_counts.get(route, 0)
        lines.append(f"| `{route}` | {n} | {_fmt_pct(n, total)} |")
    lines.append(f"| **合计** | **{total}** | 100% |")
    lines.append("")

    # 2. Daily volume
    lines.append("## 日均采样量")
    lines.append("")
    lines.append("| 日期 | 采样条数 |")
    lines.append("|---|---:|")
    for day in sorted(stats.per_day_counts):
        lines.append(f"| {day} | {stats.per_day_counts[day]} |")
    if not stats.per_day_counts:
        lines.append("| (无数据) | 0 |")
    lines.append("")

    # 3. Silver conversion
    lines.append("## 银标转化")
    lines.append("")
    lines.append(f"- silver 总量:{stats.silver_total}")
    lines.append(
        f"- conf ≥ 0.7 占比:{stats.silver_high_conf} / {stats.silver_total}"
        f" = {stats.silver_rate:.1%}"
    )
    lines.append("")

    # 4. Profile coverage
    lines.append("## 用户画像覆盖")
    lines.append(f"- 本周出现的独立 user_id 数:{stats.profile_users}")
    lines.append("")

    # 5. Retrain health
    lines.append("## 回训健康度")
    if stats.macro_f1 is None:
        lines.append("- 本周未收到回训指标 (metrics.json 缺失或无效)")
    else:
        gate_ok = stats.macro_f1 >= 0.71
        badge = "✅ 达到 0.71 门槛" if gate_ok else "⚠️ 低于 0.71 门槛"
        lines.append(f"- 最新 Macro F1:{stats.macro_f1:.3f} — {badge}")
    lines.append("")

    # 6. Narrative
    if narrative:
        lines.append("## 一周观察")
        lines.append("")
        lines.append(narrative.strip())
        lines.append("")

    lines.append("---")
    lines.append(
        "_由 `scripts/weekly_ops_report.py` 自动生成。_"
    )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI


def _default_narrative_fn(model: str) -> NarrativeFn:
    import litellm  # type: ignore[import-not-found]

    def call(ctx: dict) -> str:
        prompt = (
            "下面是一个中文对话系统最近一周的运维数据。"
            "请用不超过 180 字的中文写 3 点观察,"
            "聚焦异常趋势、风险与建议,不要输出 JSON。\n\n"
            f"{json.dumps(ctx, ensure_ascii=False, indent=2)}"
        )
        resp = litellm.completion(  # type: ignore[no-untyped-call]
            model=model,
            messages=[
                {"role": "system", "content": "你是冷静的 SRE。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=320,
        )
        return str(resp["choices"][0]["message"]["content"]).strip()

    return call


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--shadow", type=Path, required=True)
    p.add_argument("--silver", type=Path, default=None)
    p.add_argument("--metrics", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument(
        "--model",
        default="deepseek-reasoner",
        help="Only used when --narrative is passed; default = R1.",
    )
    p.add_argument(
        "--narrative",
        action="store_true",
        help="Call the LLM once to add the 一周观察 section.",
    )
    args = p.parse_args(argv)

    now = datetime.now(UTC)
    stats = build_stats(
        shadow_path=args.shadow,
        silver_path=args.silver,
        metrics_path=args.metrics,
        now=now,
    )

    narrative: str | None = None
    if args.narrative:
        try:
            fn = _default_narrative_fn(args.model)
            narrative = fn(stats.to_dict())
        except Exception as exc:  # noqa: BLE001
            print(f"narrative skipped: {exc}", file=sys.stderr)

    output = args.output or Path(f"reports/ops_{stats.week}.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_markdown(stats, narrative=narrative), encoding="utf-8"
    )
    print(f"wrote ops report -> {output}")
    return 0


if __name__ == "__main__":
    # defaultdict kept imported for future use
    _ = defaultdict
    raise SystemExit(main())
