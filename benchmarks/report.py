"""Structured reporting for the showcase benchmark."""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ARM_LABELS = {
    "baseline": "Baseline",
    "mem0_oss": "Mem0 OSS",
    "system": "RelationshipOS",
}

_DIMENSION_LABELS = {
    "memory_recall": "Memory Recall",
    "cross_session_consistency": "Cross-Session Consistency",
    "emotional_quality": "Emotional Quality",
    "proactive_safety": "Proactive Safety",
    "governance_alignment": "Governance Alignment",
    "social_omniscience": "Social Omniscience",
    "conscience_decisions": "Conscience Decisions",
    "persona_continuity": "Persona Continuity",
    "cross_user_attribution": "Cross-User Attribution",
    "latency_budget": "Latency Budget",
    "long_chat_continuity_zh": "Long Chat Continuity (ZH)",
    "persona_stability_zh": "Persona Stability (ZH)",
    "naturalness_under_memory": "Naturalness Under Memory",
    "social_world_control": "Social World Control",
    "cross_session_friend_feel": "Cross-Session Friend Feel",
}

_ARM_THEME = {
    "baseline": {"accent": "#3b82f6", "soft": "#dbeafe"},
    "mem0_oss": {"accent": "#f59e0b", "soft": "#fef3c7"},
    "system": {"accent": "#10b981", "soft": "#d1fae5"},
}


def _format_score(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def _format_delta(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"


def _safe(value: Any) -> str:
    return html.escape(str(value))


def _deliberation_summary(stats: dict[str, Any] | None) -> str:
    if not isinstance(stats, dict):
        return ""
    mode_counts = dict(stats.get("mode_counts") or {})
    observed_turns = int(stats.get("observed_turns", 0) or 0)
    if observed_turns <= 0:
        return ""
    avg_need = stats.get("avg_need")
    dominant_mode = str(stats.get("dominant_mode") or "").strip()
    parts = [
        f"Deliberation F/L/D {int(mode_counts.get('fast_reply', 0) or 0)}/"
        f"{int(mode_counts.get('light_recall', 0) or 0)}/"
        f"{int(mode_counts.get('deep_recall', 0) or 0) or 0}"
    ]
    if avg_need is not None:
        parts.append(f"Avg need {_format_score(float(avg_need))}")
    if dominant_mode:
        parts.append(f"Dominant {_safe(dominant_mode)}")
    dominant_fast_path = str(stats.get("dominant_fast_path") or "").strip()
    if dominant_fast_path:
        parts.append(f"Path {_safe(dominant_fast_path)}")
    return " · ".join(parts)


def _friend_chat_exposure_summary(stats: dict[str, Any] | None) -> str:
    if not isinstance(stats, dict):
        return ""
    meta = int(stats.get("friend_chat_exposed_meta_count", 0) or 0)
    under_grounded = int(stats.get("friend_chat_exposed_under_grounded_count", 0) or 0)
    plan_noncompliant = int(stats.get("friend_chat_exposed_plan_noncompliant_count", 0) or 0)
    empty = int(stats.get("friend_chat_exposed_empty_count", 0) or 0)
    if meta == 0 and under_grounded == 0 and plan_noncompliant == 0 and empty == 0:
        return ""
    return (
        f"Exposed meta {meta} · "
        f"Exposed plan-noncompliant {plan_noncompliant} · "
        f"Exposed under-grounded {under_grounded} · "
        f"Exposed empty {empty}"
    )


def _turn_timing_summary(stats: dict[str, Any] | None) -> str:
    if not isinstance(stats, dict):
        return ""
    observed_turns = int(stats.get("observed_turns", 0) or 0)
    if observed_turns <= 0:
        return ""
    parts = [
        f"Request path p50 {_format_score(stats.get('request_path_p50_ms'))} ms",
        f"p95 {_format_score(stats.get('request_path_p95_ms'))} ms",
        f"max {_format_score(stats.get('request_path_max_ms'))} ms",
    ]
    probe_mutations = int(stats.get("probe_session_mutation_count", 0) or 0)
    parts.append(f"Probe session mutations {probe_mutations}")
    return " · ".join(parts)


def _arm_summary_rows(arms: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = arms.get(arm_key, {})
        theme = _ARM_THEME[arm_key]
        if not arm.get("enabled", False):
            rows.append(
                f"""
                <div class="score-card disabled">
                  <div class="score-card__label">{_ARM_LABELS[arm_key]}</div>
                  <div class="score-card__score">Skipped</div>
                  <div class="score-card__meta">No run data</div>
                </div>
                """
            )
            continue
        lang = arm.get("language_breakdown", {})
        latency = arm.get("latency", {})
        failure_meta = (
            (
                '<div class="score-card__meta">Failure fallback: arm crashed but was scored as 0.00</div>'
                f"<div class='score-card__meta'>Failure class: {_safe(arm.get('failure_classification', 'unknown'))}</div>"
            )
            if arm.get("failed")
            else ""
        )
        rows.append(
            f"""
            <div class="score-card" style="--card-accent: {theme["accent"]}; --card-soft: {theme["soft"]};">
              <div class="score-card__label">{_ARM_LABELS[arm_key]}</div>
              <div class="score-card__score">{_format_score(arm.get("overall"))}</div>
              <div class="score-card__meta">EN {_format_score(lang.get("en"))} · ZH {_format_score(lang.get("zh"))}</div>
              <div class="score-card__meta">Avg latency {_format_score(latency.get("avg_ms"))} ms</div>
              {failure_meta}
            </div>
            """
        )
    return rows


def _dimension_table(arms: dict[str, Any]) -> str:
    rows: list[str] = []
    for dimension, label in _DIMENSION_LABELS.items():
        rows.append(
            f"""
            <tr>
              <td>{label}</td>
              <td>{_format_score(arms.get("baseline", {}).get("dimension_scores", {}).get(dimension))}</td>
              <td>{_format_score(arms.get("mem0_oss", {}).get("dimension_scores", {}).get(dimension))}</td>
              <td>{_format_score(arms.get("system", {}).get("dimension_scores", {}).get(dimension))}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def _suite_table(arms: dict[str, Any], suites: list[str]) -> str:
    rows: list[str] = []
    for suite in suites:
        rows.append(
            f"""
            <tr>
              <td>{suite}</td>
              <td>{_format_score(arms.get("baseline", {}).get("suites", {}).get(suite, {}).get("average_score"))}</td>
              <td>{_format_score(arms.get("mem0_oss", {}).get("suites", {}).get(suite, {}).get("average_score"))}</td>
              <td>{_format_score(arms.get("system", {}).get("suites", {}).get(suite, {}).get("average_score"))}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def _comparison_cards(comparisons: dict[str, Any]) -> list[str]:
    cards: list[str] = []
    for key in ("system_vs_baseline", "system_vs_mem0_oss", "mem0_oss_vs_baseline"):
        item = comparisons.get(key)
        if not item:
            continue
        dimension_deltas = item.get("dimension_deltas", {})
        ranked_meta = sorted(
            (
                (name, float(value))
                for name, value in dimension_deltas.items()
                if value not in {None, 0}
            ),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )[:3]
        meta = (
            " · ".join(
                f"{_DIMENSION_LABELS.get(name, name)} {_format_delta(value)}"
                for name, value in ranked_meta
            )
            or "No dimension deltas"
        )
        cards.append(
            f"""
            <div class="delta-card">
              <div class="delta-card__label">{_safe(item.get("label", key))}</div>
              <div class="delta-card__score">{_format_delta(item.get("overall_delta"))}</div>
              <div class="delta-card__meta">{_safe(meta)}</div>
            </div>
            """
        )
    return cards


def _provider_rows(provider_status: dict[str, Any]) -> str:
    rows: list[str] = []
    for key, label in (
        ("text_embedding", "Text Embedding"),
        ("multimodal_embedding", "Multimodal Embedding"),
        ("reranker", "Reranker"),
    ):
        status = provider_status.get(key, {})
        rows.append(
            f"""
            <tr>
              <td>{label}</td>
              <td>{_safe(status.get("provider", "n/a"))}</td>
              <td>{_safe(status.get("model", "n/a"))}</td>
              <td>{_safe(status.get("mode", "n/a"))}</td>
              <td>{_safe(status.get("fallback", False))}</td>
              <td>{_safe(status.get("vector_dimensions", "n/a"))}</td>
              <td>{_safe(status.get("error", status.get("reason", "")))}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def _detail_identity(detail: dict[str, Any]) -> str:
    return " | ".join(
        part
        for part in (
            detail.get("scenario_id"),
            detail.get("question"),
            detail.get("description"),
        )
        if part
    )


def _collect_case_deltas(
    results: dict[str, Any],
    *,
    better_arm: str,
    worse_arm: str,
) -> list[dict[str, Any]]:
    better = results.get("arms", {}).get(better_arm, {})
    worse = results.get("arms", {}).get(worse_arm, {})
    deltas: list[dict[str, Any]] = []
    if not better.get("enabled") or not worse.get("enabled"):
        return deltas

    for suite_name, better_suite in better.get("suites", {}).items():
        worse_suite = worse.get("suites", {}).get(suite_name, {})
        worse_index = {
            _detail_identity(detail): detail for detail in worse_suite.get("details", [])
        }
        for detail in better_suite.get("details", []):
            identity = _detail_identity(detail)
            counterpart = worse_index.get(identity)
            if counterpart is None:
                continue
            better_score = float(detail.get("score", 0))
            worse_score = float(counterpart.get("score", 0))
            deltas.append(
                {
                    "suite": suite_name,
                    "identity": identity,
                    "language": detail.get("language", "unknown"),
                    "better_score": better_score,
                    "worse_score": worse_score,
                    "delta": round(better_score - worse_score, 2),
                }
            )
    return sorted(deltas, key=lambda item: item["delta"], reverse=True)


def _top_delta_list(results: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    system_vs_baseline = _collect_case_deltas(
        results,
        better_arm="system",
        worse_arm="baseline",
    )
    wins = [item for item in system_vs_baseline if item["delta"] > 0][:5]
    losses = sorted(
        [item for item in system_vs_baseline if item["delta"] < 0],
        key=lambda item: item["delta"],
    )[:5]
    return wins, losses


def _delta_dimension_columns(comparisons: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for item in comparisons.values():
        if not item:
            continue
        for name in item.get("dimension_deltas", {}):
            if name not in seen:
                seen.append(name)
    ordered = [name for name in _DIMENSION_LABELS if name in seen]
    ordered.extend(name for name in seen if name not in ordered)
    return ordered


def _delta_html(items: list[dict[str, Any]], *, empty_label: str) -> str:
    if not items:
        return f'<div class="empty-state">{_safe(empty_label)}</div>'
    rows: list[str] = []
    for item in items:
        rows.append(
            f"""
            <li>
              <span class="delta-list__identity">{_safe(item["identity"])}</span>
              <span class="delta-list__meta">{_safe(item["suite"])} · {_safe(item["language"])}</span>
              <span class="delta-list__score">{_format_delta(item["delta"])}</span>
            </li>
            """
        )
    return f'<ul class="delta-list">{"".join(rows)}</ul>'


def _arm_details_html(results: dict[str, Any]) -> str:
    sections: list[str] = []
    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = results.get("arms", {}).get(arm_key, {})
        if not arm.get("enabled", False):
            continue
        suite_blocks: list[str] = []
        for suite_name, suite_result in arm.get("suites", {}).items():
            case_blocks: list[str] = []
            for detail in suite_result.get("details", [])[:8]:
                case_blocks.append(
                    f"""
                    <details class="case-card">
                      <summary>
                        <span>{_safe(detail.get("scenario_id", "case"))}</span>
                        <span>{_safe(detail.get("language", "unknown"))}</span>
                        <span>{_format_score(detail.get("score"))}</span>
                      </summary>
                      <div class="case-card__body">
                        {f"<p><strong>Question:</strong> {_safe(detail.get('question'))}</p>" if detail.get("question") else ""}
                        {f"<p><strong>Expected:</strong> {_safe(detail.get('expected'))}</p>" if detail.get("expected") else ""}
                        {f"<p><strong>Answer:</strong> {_safe(detail.get('answer'))}</p>" if detail.get("answer") else ""}
                        {f"<p><strong>Reason:</strong> {_safe(detail.get('reason'))}</p>" if detail.get("reason") else ""}
                        {f"<p><strong>Deliberation:</strong> {_safe(detail.get('deliberation_mode'))} · need {_format_score(detail.get('deliberation_need'))} · {_safe(detail.get('deliberation_fast_path'))}</p>" if detail.get("deliberation_mode") else ""}
                        {f"<p><strong>Proactive Safety:</strong> {_format_score(detail.get('proactive_safety'))} · <strong>Governance:</strong> {_format_score(detail.get('governance_alignment'))}</p>" if detail.get("governance_alignment") is not None else ""}
                      </div>
                    </details>
                    """
                )
            suite_blocks.append(
                f"""
                <section class="suite-block">
                  <div class="suite-block__header">
                    <h4>{_safe(suite_name)}</h4>
                  <div class="suite-block__meta">
                      Avg {_format_score(suite_result.get("average_score"))}
                      · EN {_format_score(suite_result.get("language_breakdown", {}).get("en"))}
                      · ZH {_format_score(suite_result.get("language_breakdown", {}).get("zh"))}
                  </div>
                </div>
                  {f"<div class='suite-block__meta'>{_deliberation_summary(suite_result.get('deliberation_stats'))}</div>" if _deliberation_summary(suite_result.get("deliberation_stats")) else ""}
                  {f"<div class='suite-block__meta'>{_friend_chat_exposure_summary(suite_result.get('response_diagnostics_stats'))}</div>" if _friend_chat_exposure_summary(suite_result.get("response_diagnostics_stats")) else ""}
                  {f"<div class='suite-block__meta'>{_turn_timing_summary(suite_result.get('turn_timing_stats'))}</div>" if _turn_timing_summary(suite_result.get("turn_timing_stats")) else ""}
                  {"".join(case_blocks) if case_blocks else '<div class="empty-state">No case details recorded.</div>'}
                </section>
                """
            )
        sections.append(
            f"""
            <section class="arm-panel">
              <div class="arm-panel__header">
                <h3>{_ARM_LABELS[arm_key]}</h3>
                <div class="arm-panel__meta">
                  Overall {_format_score(arm.get("overall"))}
                  · Avg latency {_format_score(arm.get("latency", {}).get("avg_ms"))} ms
                </div>
              </div>
              {"".join(suite_blocks)}
            </section>
            """
        )
    return "\n".join(sections)


def _markdown_report(results: dict[str, Any], ts: str) -> str:
    arms = results.get("arms", {})
    comparisons = results.get("comparisons", {})
    requested_suites = results.get("suites", [])
    provider_status = results.get("provider_status", {})
    report_title = results.get("report_title", "RelationshipOS Showcase Benchmark")

    md: list[str] = []
    md.append(f"# {report_title}")
    md.append("")
    md.append(f"**Timestamp**: {results.get('timestamp', ts)}")
    md.append(f"**Model**: {results.get('model', 'unknown')}")
    md.append(
        f"**Benchmark Chat**: "
        f"{results.get('benchmark_chat_provider', 'unknown')} / "
        f"{results.get('benchmark_chat_model', 'unknown')}"
    )
    md.append(f"**Judge Model**: {results.get('judge_model', 'unknown')}")
    md.append(f"**Runtime Profile**: {results.get('runtime_profile', 'default')}")
    stress_mode = (results.get("benchmark_controls", {}) or {}).get("stress_mode")
    if stress_mode:
        md.append(f"**Stress Mode**: {stress_mode}")
    md.append(f"**Suites**: {', '.join(requested_suites) if requested_suites else 'n/a'}")
    md.append(f"**Total Elapsed**: {results.get('total_elapsed_seconds', 0):.1f}s")
    md.append("")
    md.append("## Executive Summary")
    md.append("")
    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = arms.get(arm_key, {})
        if not arm.get("enabled", False):
            md.append(f"- {_ARM_LABELS[arm_key]}: skipped")
            continue
        failure_suffix = " (failure fallback)" if arm.get("failed") else ""
        failure_classification = (
            f" / {arm.get('failure_classification', 'unknown')}" if arm.get("failed") else ""
        )
        md.append(
            f"- {_ARM_LABELS[arm_key]}: overall {_format_score(arm.get('overall'))}, "
            f"EN {_format_score(arm.get('language_breakdown', {}).get('en'))}, "
            f"ZH {_format_score(arm.get('language_breakdown', {}).get('zh'))}, "
            f"latency {_format_score(arm.get('latency', {}).get('avg_ms'))} ms"
            f"{failure_suffix}{failure_classification}"
        )
    md.append("")
    md.append("## Provider Status")
    md.append("")
    md.append("| Component | Provider | Model | Mode | Fallback | Dimensions | Error |")
    md.append("|-----------|----------|-------|------|----------|-----------:|-------|")
    for key, label in (
        ("text_embedding", "Text Embedding"),
        ("multimodal_embedding", "Multimodal Embedding"),
        ("reranker", "Reranker"),
    ):
        status = provider_status.get(key, {})
        md.append(
            f"| {label} | {status.get('provider', 'n/a')} | {status.get('model', 'n/a')} | "
            f"{status.get('mode', 'n/a')} | {status.get('fallback', False)} | "
            f"{status.get('vector_dimensions', 'n/a')} | "
            f"{status.get('error', status.get('reason', ''))} |"
        )
    md.append("")

    md.append("## Overall")
    md.append("")
    md.append("| Arm | Overall | English | Chinese | Avg Latency (ms) |")
    md.append("|-----|--------:|--------:|--------:|-----------------:|")
    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = arms.get(arm_key, {})
        if not arm.get("enabled", False):
            md.append(f"| {_ARM_LABELS[arm_key]} | skipped | skipped | skipped | skipped |")
            continue
        lang = arm.get("language_breakdown", {})
        latency = arm.get("latency", {})
        md.append(
            f"| {_ARM_LABELS[arm_key]} | {_format_score(arm.get('overall'))} | "
            f"{_format_score(lang.get('en'))} | {_format_score(lang.get('zh'))} | "
            f"{_format_score(latency.get('avg_ms'))} |"
        )
    md.append("")

    md.append("## Deltas")
    md.append("")
    delta_dimensions = _delta_dimension_columns(comparisons)
    header = ["Comparison", "Overall"] + [
        _DIMENSION_LABELS.get(name, name) for name in delta_dimensions
    ]
    md.append("| " + " | ".join(header) + " |")
    md.append(
        "|" + "|".join(["-----------", "--------:"] + ["-------:"] * len(delta_dimensions)) + "|"
    )
    for key in ("system_vs_baseline", "system_vs_mem0_oss", "mem0_oss_vs_baseline"):
        item = comparisons.get(key)
        if not item:
            continue
        deltas = item.get("dimension_deltas", {})
        values = [_format_score(deltas.get(name)) for name in delta_dimensions]
        md.append(
            "| "
            + " | ".join(
                [str(item.get("label", key)), _format_score(item.get("overall_delta")), *values]
            )
            + " |"
        )
    md.append("")

    wins, losses = _top_delta_list(results)
    md.append("## Top Wins")
    md.append("")
    if wins:
        for item in wins:
            md.append(
                f"- {item['identity']} ({item['suite']} / {item['language']}): {_format_delta(item['delta'])}"
            )
    else:
        md.append("- No positive system-vs-baseline deltas captured yet.")
    md.append("")
    md.append("## Biggest Regressions")
    md.append("")
    if losses:
        for item in losses:
            md.append(
                f"- {item['identity']} ({item['suite']} / {item['language']}): {_format_delta(item['delta'])}"
            )
    else:
        md.append("- No negative system-vs-baseline deltas captured.")
    md.append("")

    md.append("## Suite Diagnostics")
    md.append("")
    for arm_key in ("baseline", "mem0_oss", "system"):
        arm = arms.get(arm_key, {})
        if not arm.get("enabled", False):
            continue
        md.append(f"### {_ARM_LABELS[arm_key]}")
        md.append("")
        for suite_name, suite_result in arm.get("suites", {}).items():
            deliberation = _deliberation_summary(suite_result.get("deliberation_stats"))
            exposures = _friend_chat_exposure_summary(
                suite_result.get("response_diagnostics_stats")
            )
            timings = _turn_timing_summary(suite_result.get("turn_timing_stats"))
            parts = [part for part in (deliberation, exposures, timings) if part]
            if not parts:
                continue
            md.append(f"- {suite_name}: " + " · ".join(parts))
        md.append("")
    return "\n".join(md)


def _html_report(results: dict[str, Any], ts: str) -> str:
    arms = results.get("arms", {})
    wins, losses = _top_delta_list(results)
    requested_suites = results.get("suites", [])
    provider_status = results.get("provider_status", {})
    benchmark_controls = results.get("benchmark_controls", {}) or {}
    report_title = results.get("report_title", "RelationshipOS Showcase Benchmark")
    report_subtitle = results.get(
        "report_subtitle",
        (
            "Three-arm comparison across baseline, Mem0 OSS, and RelationshipOS "
            "using the same generation model. This report is formatted for demos, "
            "design reviews, and interview walkthroughs."
        ),
    )
    report_page_title = results.get("report_page_title", "RelationshipOS Benchmark Report")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_safe(report_page_title)}</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --panel: #ffffff;
      --ink: #102033;
      --muted: #5f6f86;
      --line: #d9e2ef;
      --shadow: 0 18px 48px rgba(16, 32, 51, 0.08);
      --radius: 20px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(16,185,129,0.10), transparent 26%),
        radial-gradient(circle at top right, rgba(59,130,246,0.12), transparent 28%),
        var(--bg);
      color: var(--ink);
      font: 15px/1.6 ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .page {{
      width: min(1200px, calc(100vw - 40px));
      margin: 0 auto;
      padding: 40px 0 56px;
    }}
    .hero {{
      background: linear-gradient(135deg, #0f172a, #133d63 62%, #0f766e);
      color: white;
      border-radius: 28px;
      padding: 34px 34px 28px;
      box-shadow: var(--shadow);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 34px;
      line-height: 1.1;
      letter-spacing: -0.03em;
    }}
    .hero p {{
      margin: 0;
      color: rgba(255,255,255,0.82);
      max-width: 900px;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 20px;
    }}
    .hero-chip {{
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 13px;
    }}
    .section {{
      margin-top: 26px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 24px;
    }}
    .section h2 {{
      margin: 0 0 14px;
      font-size: 20px;
      letter-spacing: -0.02em;
    }}
    .score-grid, .delta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }}
    .score-card {{
      background: linear-gradient(180deg, white, var(--card-soft));
      border: 1px solid color-mix(in srgb, var(--card-accent) 22%, white);
      border-radius: 18px;
      padding: 18px;
    }}
    .score-card.disabled {{
      background: #f8fafc;
      border-color: var(--line);
      color: var(--muted);
    }}
    .score-card__label, .delta-card__label {{
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .score-card__score, .delta-card__score {{
      margin-top: 8px;
      font-size: 34px;
      line-height: 1;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .score-card__meta, .delta-card__meta {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .delta-card {{
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .delta-columns {{
      display: grid;
      gap: 18px;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }}
    .delta-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 10px;
    }}
    .delta-list li {{
      display: grid;
      gap: 2px;
      padding: 12px 14px;
      border-radius: 14px;
      background: #f8fafc;
      border: 1px solid var(--line);
    }}
    .delta-list__identity {{
      font-weight: 600;
    }}
    .delta-list__meta {{
      font-size: 13px;
      color: var(--muted);
    }}
    .delta-list__score {{
      font-size: 13px;
      color: #0f766e;
      font-weight: 700;
    }}
    .empty-state {{
      color: var(--muted);
      padding: 14px;
      border-radius: 14px;
      border: 1px dashed var(--line);
      background: #f8fafc;
    }}
    .arm-panel + .arm-panel {{
      margin-top: 20px;
    }}
    .arm-panel__header, .suite-block__header {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }}
    .arm-panel__header h3, .suite-block__header h4 {{
      margin: 0;
      font-size: 18px;
    }}
    .arm-panel__meta, .suite-block__meta {{
      color: var(--muted);
      font-size: 13px;
    }}
    .suite-block {{
      margin-top: 18px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }}
    .case-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fbfcfe;
      margin-top: 10px;
      overflow: hidden;
    }}
    .case-card summary {{
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      align-items: center;
      cursor: pointer;
      padding: 12px 14px;
      font-weight: 600;
      list-style: none;
    }}
    .case-card summary::-webkit-details-marker {{ display: none; }}
    .case-card__body {{
      padding: 0 14px 14px;
      color: var(--muted);
    }}
    .case-card__body p {{
      margin: 8px 0 0;
    }}
    @media (max-width: 720px) {{
      .page {{ width: min(100vw - 20px, 1200px); padding-top: 20px; }}
      .hero {{ padding: 24px 20px; }}
      .section {{ padding: 18px; }}
      .case-card summary {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>{_safe(report_title)}</h1>
      <p>{_safe(report_subtitle)}</p>
      <div class="hero-meta">
        <div class="hero-chip">Timestamp: {_safe(results.get("timestamp", ts))}</div>
        <div class="hero-chip">Model: {_safe(results.get("model", "unknown"))}</div>
        <div class="hero-chip">Benchmark Chat: {_safe(results.get("benchmark_chat_provider", "unknown"))} / {_safe(results.get("benchmark_chat_model", "unknown"))}</div>
        <div class="hero-chip">Judge: {_safe(results.get("judge_model", "unknown"))}</div>
        <div class="hero-chip">Runtime Profile: {_safe(results.get("runtime_profile", "default"))}</div>
        <div class="hero-chip">Stress Mode: {_safe(benchmark_controls.get("stress_mode", "n/a"))}</div>
        <div class="hero-chip">Suites: {_safe(", ".join(requested_suites))}</div>
        <div class="hero-chip">Elapsed: {_safe(results.get("total_elapsed_seconds", 0))}s</div>
      </div>
    </section>

    <section class="section">
      <h2>Overall Scoreboard</h2>
      <div class="score-grid">
        {"".join(_arm_summary_rows(arms))}
      </div>
    </section>

    <section class="section">
      <h2>Deltas</h2>
      <div class="delta-grid">
        {"".join(_comparison_cards(results.get("comparisons", {})))}
      </div>
    </section>

    <section class="section">
      <h2>Provider Status</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Component</th>
              <th>Provider</th>
              <th>Model</th>
              <th>Mode</th>
              <th>Fallback</th>
              <th>Dimensions</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {_provider_rows(provider_status)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Dimension Breakdown</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Dimension</th>
              <th>Baseline</th>
              <th>Mem0 OSS</th>
              <th>RelationshipOS</th>
            </tr>
          </thead>
          <tbody>
            {_dimension_table(arms)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Suite Summary</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Suite</th>
              <th>Baseline</th>
              <th>Mem0 OSS</th>
              <th>RelationshipOS</th>
            </tr>
          </thead>
          <tbody>
            {_suite_table(arms, requested_suites)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>System vs Baseline Highlights</h2>
      <div class="delta-columns">
        <div>
          <h3>Top Wins</h3>
          {_delta_html(wins, empty_label="No positive system wins recorded yet.")}
        </div>
        <div>
          <h3>Biggest Regressions</h3>
          {_delta_html(losses, empty_label="No negative system regressions recorded.")}
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Case Explorer</h2>
      {_arm_details_html(results)}
    </section>
  </div>
</body>
</html>"""


def generate_benchmark_report(results: dict[str, Any], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"benchmark_{ts}.json"
    json_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    md_path = output_dir / f"benchmark_{ts}.md"
    md_path.write_text(_markdown_report(results, ts), encoding="utf-8")

    html_path = output_dir / f"benchmark_{ts}.html"
    html_path.write_text(_html_report(results, ts), encoding="utf-8")

    return md_path, json_path, html_path
