from __future__ import annotations

import asyncio
import json
from html import escape
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from relationship_os.api.dependencies import get_container
from relationship_os.api.routes.runtime import build_runtime_overview_payload
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
    ensure_snapshot_only_lifecycle_events,
)
from relationship_os.application.container import RuntimeContainer
from relationship_os.domain.event_types import is_trace_event_type
from relationship_os.domain.projectors import UnknownProjectorError

router = APIRouter(prefix="/console", tags=["console"])
ContainerDep = Annotated[RuntimeContainer, Depends(get_container)]

PANEL_REFRESH_SECONDS = 12
LIST_LIMIT = 8
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(("html", "xml")),
)


def _render_template(template_name: str, **context: Any) -> str:
    return _TEMPLATE_ENV.get_template(template_name).render(**context)


def _display_text(value: object | None, *, fallback: str = "—") -> str:
    if value is None:
        return fallback
    rendered = str(value).strip()
    return rendered or fallback


def _display_timestamp(value: object | None) -> str:
    if value is None:
        return "—"
    rendered = str(value).replace("T", " ")
    return rendered.replace("+00:00", " UTC")


def _display_shorten(value: object | None, *, limit: int = 96) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text or "—"
    return text[: limit - 1].rstrip() + "…"


def _text(value: object | None, *, fallback: str = "—") -> str:
    return escape(_display_text(value, fallback=fallback))


def _timestamp(value: object | None) -> str:
    return escape(_display_timestamp(value))


def _shorten(value: object | None, *, limit: int = 96) -> str:
    return escape(_display_shorten(value, limit=limit))


def _js_string(value: object | None) -> str:
    return escape(json.dumps("" if value is None else str(value)))


def _pretty_json(value: object) -> str:
    return escape(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _tone(label: object | None) -> str:
    lowered = str(label or "").lower()
    if any(
        token in lowered for token in ["pass", "ok", "stable", "completed", "direct", "improved"]
    ):
        return "good"
    if any(
        token in lowered
        for token in ["revise", "failed", "high", "elevated", "boundary", "regressed"]
    ):
        return "bad"
    if any(
        token in lowered
        for token in [
            "review",
            "watch",
            "guarded",
            "queued",
            "running",
            "clarify",
            "calibrated",
            "new",
        ]
    ):
        return "warn"
    return "neutral"


def _badge(label: object | None, *, tone: str | None = None) -> str:
    resolved_tone = tone or _tone(label)
    return f'<span class="badge badge-{resolved_tone}">{_text(label, fallback="n/a")}</span>'


def _metric_card(label: str, value: object | None, detail: str) -> str:
    return (
        '<article class="metric-card">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{_text(value)}</div>'
        f'<div class="metric-detail">{escape(detail)}</div>'
        "</article>"
    )


def _labeled_value(label: str, value: object | None) -> str:
    return (
        '<div class="kv-item">'
        f'<span class="kv-label">{escape(label)}</span>'
        f'<span class="kv-value">{_text(value)}</span>'
        "</div>"
    )


def _empty_state(title: str, detail: str) -> str:
    return f'<div class="empty-state"><h3>{escape(title)}</h3><p>{escape(detail)}</p></div>'


def _detail_url(
    request: Request,
    session_id: str | None,
    *,
    projector_name: str | None = None,
    version: str | None = None,
) -> str:
    base = str(request.url_for("console_session_detail_fragment"))
    if not session_id:
        return base
    query_parts = [f"session_id={quote(session_id)}"]
    if projector_name:
        query_parts.append(f"projector_name={quote(projector_name)}")
    if version:
        query_parts.append(f"version={quote(version)}")
    return f"{base}?{'&'.join(query_parts)}"


async def _fetch_overview_data(container: RuntimeContainer) -> dict[str, Any]:
    (
        runtime_overview,
        sessions_payload,
        jobs_payload,
        archives_payload,
        evaluations_payload,
    ) = await asyncio.gather(
        build_runtime_overview_payload(container),
        container.runtime_service.list_sessions(),
        container.job_service.list_jobs(),
        container.audit_service.list_archived_sessions(),
        container.evaluation_service.list_session_evaluations(),
    )
    sessions = sorted(
        sessions_payload,
        key=lambda item: str(item.get("last_event_at") or ""),
        reverse=True,
    )
    jobs = list(jobs_payload["jobs"])
    archives = list(archives_payload["sessions"])
    evaluations = list(evaluations_payload["sessions"])
    evaluations.sort(
        key=lambda item: (
            int(item.get("response_post_audit_total_violation_count", 0)),
            int(item.get("response_normalization_changed_turn_count", 0)),
            float(item.get("avg_psychological_safety") or 0.0),
        ),
        reverse=True,
    )
    return {
        "runtime": runtime_overview,
        "sessions": sessions,
        "jobs": jobs,
        "archives": archives,
        "evaluations": evaluations,
    }


def _badge_data(label: object | None, *, tone: str | None = None) -> dict[str, str]:
    return {
        "label": _display_text(label, fallback="n/a"),
        "tone": tone or _tone(label),
    }


def _segment(label: str, value: object | None) -> str:
    return f"{label} {_display_text(value)}"


def _item_line(item: dict[str, Any], *pairs: tuple[str, str]) -> str:
    return " · ".join(_segment(label, item.get(key)) for label, key in pairs)


def _lifecycle_line(item: dict[str, Any], phase: str) -> str:
    prefix = f"proactive_lifecycle_{phase}"
    return _item_line(
        item,
        (f"生命周期 {phase}", f"{prefix}_decision"),
        ("模式", f"{prefix}_mode"),
        ("活跃", f"{prefix}_active_stage_label"),
    )


_PROACTIVE_QUEUE_DETAIL_SPECS: tuple[tuple[tuple[str, str], ...], ...] = (
    (
        ("引导", "guidance_mode"),
        ("移交", "guidance_handoff_mode"),
        ("延续", "guidance_carryover_mode"),
    ),
    (
        ("节奏", "cadence_status"),
        ("节拍", "cadence_followup_tempo"),
        ("空间", "cadence_user_space_mode"),
    ),
    (
        ("仪式", "ritual_phase"),
        ("收尾", "ritual_closing_move"),
        ("躯体", "ritual_somatic_shortcut"),
    ),
    (
        ("躯体计划", "somatic_orchestration_mode"),
        ("锚点", "somatic_orchestration_body_anchor"),
        ("跟进", "somatic_orchestration_followup_style"),
    ),
    (
        ("调度", "proactive_scheduling_mode"),
        ("守护", "proactive_scheduling_low_pressure_guard"),
        ("延迟", "proactive_scheduling_first_touch_extra_delay_seconds"),
    ),
    (
        ("编排", "proactive_orchestration_key"),
        ("目标", "proactive_orchestration_stage_objective"),
        ("交付", "proactive_orchestration_stage_delivery_mode"),
    ),
    (
        ("执行", "proactive_actuation_key"),
        ("开场", "proactive_actuation_opening_move"),
        ("收尾", "proactive_actuation_closing_move"),
    ),
    (
        ("衔接", "proactive_actuation_bridge_move"),
        ("用户空间", "proactive_actuation_user_space_signal"),
        ("躯体", "proactive_actuation_somatic_mode"),
    ),
    (
        ("推进", "proactive_progression_key"),
        ("动作", "proactive_progression_stage_action"),
        ("高级", "proactive_progression_advanced"),
    ),
    (
        ("控制器", "proactive_stage_controller_key"),
        ("目标", "proactive_stage_controller_target_stage_label"),
        ("延迟", "proactive_stage_controller_additional_delay_seconds"),
    ),
    (
        ("线控制器", "proactive_line_controller_key"),
        ("状态", "proactive_line_controller_line_state"),
        ("延迟", "proactive_line_controller_additional_delay_seconds"),
    ),
    (
        ("护栏", "proactive_guardrail_key"),
        ("最大", "proactive_guardrail_max_dispatch_count"),
        ("用户等待", "proactive_guardrail_stage_min_seconds_since_last_user"),
    ),
    (
        ("矩阵", "reengagement_matrix_key"),
        ("选择", "reengagement_matrix_selected_strategy"),
        ("学习", "reengagement_matrix_learning_mode"),
        ("阻断", "reengagement_matrix_blocked_count"),
    ),
    (
        ("策略", "reengagement_strategy_key"),
        ("压力", "reengagement_pressure_mode"),
        ("自主", "reengagement_autonomy_signal"),
    ),
    (
        ("反馈", "proactive_dispatch_feedback_key"),
        ("策略", "proactive_dispatch_feedback_strategy_key"),
        ("延迟", "proactive_dispatch_feedback_gate_defer_count"),
    ),
    (
        ("门控", "proactive_dispatch_gate_key"),
        ("决策", "proactive_dispatch_gate_decision"),
        ("重试", "proactive_dispatch_gate_retry_after_seconds"),
    ),
    (
        ("生命周期调度", "proactive_lifecycle_dispatch_decision"),
        ("结果", "proactive_lifecycle_outcome_decision"),
        ("消息", "proactive_lifecycle_outcome_message_event_count"),
    ),
    (
        ("生命周期决议", "proactive_lifecycle_resolution_decision"),
        ("模式", "proactive_lifecycle_resolution_mode"),
        ("队列", "proactive_lifecycle_resolution_queue_override_status"),
    ),
)

_PROACTIVE_LIFECYCLE_PHASES: tuple[str, ...] = (
    "activation",
    "settlement",
    "closure",
    "availability",
    "retention",
    "eligibility",
    "candidate",
    "selectability",
    "reentry",
    "reactivation",
    "resumption",
    "readiness",
    "arming",
    "trigger",
    "launch",
    "handoff",
    "continuation",
    "sustainment",
    "stewardship",
    "guardianship",
    "oversight",
    "assurance",
    "attestation",
    "verification",
    "certification",
    "confirmation",
    "ratification",
    "endorsement",
    "authorization",
    "enactment",
    "finality",
    "completion",
    "conclusion",
    "disposition",
    "standing",
    "residency",
    "tenure",
    "persistence",
    "durability",
    "longevity",
    "legacy",
    "heritage",
    "lineage",
    "ancestry",
    "provenance",
    "origin",
    "root",
    "foundation",
    "bedrock",
    "substrate",
    "stratum",
    "layer",
)

_SYSTEM3_GOVERNANCE_DOMAINS: tuple[tuple[str, str], ...] = (
    ("dependency", "Dependency"),
    ("autonomy", "Autonomy"),
    ("boundary", "Boundary"),
    ("support", "Support"),
    ("continuity", "Continuity"),
    ("repair", "Repair"),
    ("attunement", "Attunement"),
    ("trust", "Trust"),
    ("clarity", "Clarity"),
    ("pacing", "Pacing"),
    ("commitment", "Commitment"),
    ("disclosure", "Disclosure"),
    ("reciprocity", "Reciprocity"),
    ("pressure", "Pressure"),
    ("relational", "Relational"),
    ("safety", "Safety"),
    ("progress", "Progress"),
    ("stability", "Stability"),
)


def _build_proactive_summary(item: dict[str, Any]) -> str:
    return " · ".join(
        [
            f"基准 {_display_timestamp(item.get('base_due_at'))}",
            f"到期 {_display_timestamp(item.get('due_at'))}",
            f"过期 {_display_timestamp(item.get('expires_at'))}",
            _display_shorten(item.get("opening_hint"), limit=100),
        ]
    )


def _build_proactive_detail_lines(item: dict[str, Any]) -> list[str]:
    lines = [_item_line(item, *spec) for spec in _PROACTIVE_QUEUE_DETAIL_SPECS]
    lines.extend(_lifecycle_line(item, phase) for phase in _PROACTIVE_LIFECYCLE_PHASES)
    lines.append(
        " · ".join(
            [
                _segment("阶段", item.get("proactive_cadence_stage_label")),
                (
                    f"#{_display_text(item.get('proactive_cadence_stage_index'))}/"
                    f"{_display_text(item.get('proactive_cadence_stage_count'))}"
                ),
                _segment(
                    "剩余",
                    item.get("proactive_cadence_remaining_dispatches"),
                ),
            ]
        )
    )
    lines.append(
        " · ".join(
            [
                _segment("调度原因", item.get("schedule_reason")),
                _segment("暂停", _format_followup_hold_reasons(item)),
            ]
        )
    )
    return lines


def _build_session_detail_lifecycle_phase_cards(
    summary: dict[str, Any],
) -> list[str]:
    cards: list[str] = []
    for phase in _PROACTIVE_LIFECYCLE_PHASES:
        title = phase.replace("_", " ").title()
        prefix = f"latest_proactive_lifecycle_{phase}"
        cards.extend(
            [
                _labeled_value(f"生命周期 {title}", summary.get(f"{prefix}_key")),
                _labeled_value(
                    f"生命周期 {title} 状态",
                    summary.get(f"{prefix}_status"),
                ),
                _labeled_value(
                    f"生命周期 {title} 模式",
                    summary.get(f"{prefix}_mode"),
                ),
                _labeled_value(
                    f"生命周期 {title} 决策",
                    summary.get(f"{prefix}_decision"),
                ),
                _labeled_value(
                    f"生命周期 {title} 动作",
                    summary.get(f"{prefix}_actionability"),
                ),
                _labeled_value(
                    f"生命周期 {title} 阶段",
                    summary.get(f"{prefix}_active_stage_label"),
                ),
                _labeled_value(
                    f"生命周期 {title} 队列",
                    summary.get(f"{prefix}_queue_override_status"),
                ),
            ]
        )
    return cards


def _build_session_detail_system3_governance_cards(
    summary: dict[str, Any],
) -> list[str]:
    cards: list[str] = []
    for domain, title in _SYSTEM3_GOVERNANCE_DOMAINS:
        prefix = f"latest_system3_{domain}_governance"
        cards.extend(
            [
                _labeled_value(
                    f"{title} 治理",
                    summary.get(f"{prefix}_status"),
                ),
                _labeled_value(
                    f"{title} 目标",
                    summary.get(f"{prefix}_target"),
                ),
                _labeled_value(
                    f"{title} 触发",
                    summary.get(f"{prefix}_trigger"),
                ),
                _labeled_value(
                    f"{title} 轨迹",
                    summary.get(f"{prefix}_trajectory_status"),
                ),
                _labeled_value(
                    f"{title} 轨迹目标",
                    summary.get(f"{prefix}_trajectory_target"),
                ),
                _labeled_value(
                    f"{title} 轨迹触发",
                    summary.get(f"{prefix}_trajectory_trigger"),
                ),
            ]
        )
    return cards


_SESSION_DETAIL_FOLLOWUP_AND_SYSTEM3_SPECS: tuple[tuple[str, str], ...] = (
    (
        "二次触达开场",
        "latest_proactive_actuation_second_touch_opening_move",
    ),
    ("二次触达衔接", "latest_proactive_actuation_second_touch_bridge_move"),
    (
        "二次触达过期动作",
        "latest_proactive_progression_second_touch_action",
    ),
    ("跟进阶段", "latest_proactive_followup_dispatch_stage_label"),
    ("重连矩阵", "latest_reengagement_matrix_key"),
    ("矩阵选择", "latest_reengagement_matrix_selected_strategy"),
    ("矩阵替代", "latest_reengagement_matrix_top_alternative"),
    ("矩阵阻断", "latest_reengagement_matrix_blocked_count"),
    ("重连仪式", "latest_reengagement_ritual_mode"),
    ("重连策略", "latest_reengagement_strategy_key"),
    ("重连压力", "latest_reengagement_pressure_mode"),
    ("重连自主", "latest_reengagement_autonomy_signal"),
    ("跟进调度", "latest_proactive_followup_dispatch_status"),
    ("质量医生", "latest_runtime_quality_doctor_status"),
    ("成长阶段", "latest_system3_growth_stage"),
    ("身份轨迹", "latest_system3_identity_trajectory_status"),
    ("身份目标", "latest_system3_identity_trajectory_target"),
    ("成长转变", "latest_system3_growth_transition_status"),
    ("成长目标", "latest_system3_growth_transition_target"),
    ("成长轨迹", "latest_system3_growth_transition_trajectory_status"),
    (
        "成长轨迹目标",
        "latest_system3_growth_transition_trajectory_target",
    ),
    (
        "成长轨迹触发",
        "latest_system3_growth_transition_trajectory_trigger",
    ),
    ("版本迁移", "latest_system3_version_migration_status"),
    ("迁移范围", "latest_system3_version_migration_scope"),
    ("迁移触发", "latest_system3_version_migration_trigger"),
    (
        "迁移轨迹",
        "latest_system3_version_migration_trajectory_status",
    ),
    (
        "迁移轨迹目标",
        "latest_system3_version_migration_trajectory_target",
    ),
    (
        "迁移轨迹触发",
        "latest_system3_version_migration_trajectory_trigger",
    ),
    ("策略督导", "latest_system3_strategy_supervision_status"),
    ("督导模式", "latest_system3_strategy_supervision_mode"),
    ("督导触发", "latest_system3_strategy_supervision_trigger"),
    (
        "督导轨迹",
        "latest_system3_strategy_supervision_trajectory_status",
    ),
    ("督导目标", "latest_system3_strategy_supervision_trajectory_target"),
    (
        "督导轨迹触发",
        "latest_system3_strategy_supervision_trajectory_trigger",
    ),
    ("模型演化", "latest_system3_user_model_evolution_status"),
    ("模型修订", "latest_system3_user_model_revision_mode"),
    ("模型偏移", "latest_system3_user_model_shift_signal"),
    ("模型轨迹", "latest_system3_user_model_trajectory_status"),
    ("轨迹目标", "latest_system3_user_model_trajectory_target"),
    ("轨迹触发", "latest_system3_user_model_trajectory_trigger"),
    (
        "期望校准",
        "latest_system3_expectation_calibration_status",
    ),
    (
        "期望目标",
        "latest_system3_expectation_calibration_target",
    ),
    (
        "期望触发",
        "latest_system3_expectation_calibration_trigger",
    ),
    (
        "期望轨迹",
        "latest_system3_expectation_calibration_trajectory_status",
    ),
    (
        "期望轨迹目标",
        "latest_system3_expectation_calibration_trajectory_target",
    ),
    (
        "期望轨迹触发",
        "latest_system3_expectation_calibration_trajectory_trigger",
    ),
    ("道德推理", "latest_system3_moral_reasoning_status"),
    ("道德冲突", "latest_system3_moral_conflict"),
    ("道德轨迹", "latest_system3_moral_trajectory_status"),
    ("道德目标", "latest_system3_moral_trajectory_target"),
    ("道德触发", "latest_system3_moral_trajectory_trigger"),
    ("策略审计", "latest_system3_strategy_audit_status"),
    ("审计轨迹", "latest_system3_strategy_audit_trajectory_status"),
    ("审计目标", "latest_system3_strategy_audit_trajectory_target"),
    ("审计触发", "latest_system3_strategy_audit_trajectory_trigger"),
    ("情感负债", "latest_system3_emotional_debt_status"),
    (
        "负债轨迹",
        "latest_system3_emotional_debt_trajectory_status",
    ),
    ("负债目标", "latest_system3_emotional_debt_trajectory_target"),
    ("负债触发", "latest_system3_emotional_debt_trajectory_trigger"),
    ("后审计", "latest_response_post_audit_status"),
    ("归一化", "latest_response_normalization_final_status"),
    ("边界", "latest_boundary_decision"),
)


def _build_session_detail_followup_and_system3_cards(
    summary: dict[str, Any],
    audit: dict[str, Any],
) -> list[str]:
    return [
        *[
            _labeled_value(label, summary.get(key))
            for label, key in _SESSION_DETAIL_FOLLOWUP_AND_SYSTEM3_SPECS
        ],
        *_build_session_detail_system3_governance_cards(summary),
        _labeled_value("回放", "consistent" if audit.get("consistent") else "drift"),
    ]


def _build_session_detail_header(
    *,
    session_id: str,
    summary: dict[str, Any],
    audit: dict[str, Any],
) -> str:
    return (
        '<section class="fragment-section">'
        f'<div class="section-header"><h2>{_text(session_id)}</h2>'
        f'<div class="section-badges">{_badge(summary.get("latest_strategy"))}'
        f"{_badge(summary.get('latest_response_post_audit_status'))}"
        f"{_badge(summary.get('latest_response_normalization_final_status'))}</div></div>"
        f'<p class="lead">指纹 {_text(audit.get("fingerprint"))} · '
        f"事件 {audit.get('event_count', 0)} · 轮次 {summary.get('turn_count', 0)}</p>"
        "</section>"
    )


_SESSION_DETAIL_STRATEGY_GRID_SPECS: tuple[tuple[str, str], ...] = (
    ("最新策略", "latest_strategy"),
    ("策略多样性", "latest_strategy_diversity_status"),
    ("策略路径", "latest_policy_path"),
    ("多样性指数", "strategy_diversity_index"),
    ("响应序列", "latest_response_sequence_mode"),
    ("时间感知", "latest_time_awareness_mode"),
    ("认知负载段", "latest_cognitive_load_band"),
    ("引导模式", "latest_guidance_mode"),
    ("引导节奏", "latest_guidance_pacing"),
    ("引导能动性", "latest_guidance_agency_mode"),
    ("引导仪式", "latest_guidance_ritual_action"),
    ("引导移交", "latest_guidance_handoff_mode"),
    ("引导延续", "latest_guidance_carryover_mode"),
    ("节奏状态", "latest_cadence_status"),
    ("节奏轮形", "latest_cadence_turn_shape"),
    ("节奏节拍", "latest_cadence_followup_tempo"),
    ("节奏空间", "latest_cadence_user_space_mode"),
    ("仪式阶段", "latest_session_ritual_phase"),
    ("仪式收尾", "latest_session_ritual_closing_move"),
    ("躯体捷径", "latest_session_ritual_somatic_shortcut"),
    ("躯体计划", "latest_somatic_orchestration_mode"),
    ("身体锚点", "latest_somatic_orchestration_body_anchor"),
    ("主动跟进", "latest_proactive_followup_status"),
    ("跟进节奏", "latest_proactive_cadence_key"),
    ("跟进护栏", "latest_proactive_guardrail_key"),
    ("护栏最大调度", "latest_proactive_guardrail_max_dispatch_count"),
    ("护栏硬停止", "latest_proactive_guardrail_hard_stop_count"),
    (
        "跟进调度",
        "latest_proactive_scheduling_mode",
    ),
    (
        "调度冷却",
        "latest_proactive_scheduling_min_seconds_since_last_outbound",
    ),
    ("跟进编排", "latest_proactive_orchestration_key"),
    (
        "二次触达交付",
        "latest_proactive_orchestration_second_touch_delivery_mode",
    ),
    ("跟进执行", "latest_proactive_actuation_key"),
    ("跟进推进", "latest_proactive_progression_key"),
    ("跟进控制器", "latest_proactive_stage_controller_key"),
    ("控制器决策", "latest_proactive_stage_controller_decision"),
    ("控制器目标", "latest_proactive_stage_controller_target_stage_label"),
    (
        "控制器延迟",
        "latest_proactive_stage_controller_additional_delay_seconds",
    ),
    ("跟进线控制器", "latest_proactive_line_controller_key"),
    ("线控制器决策", "latest_proactive_line_controller_decision"),
    ("线控制器状态", "latest_proactive_line_controller_line_state"),
    (
        "线控制器延迟",
        "latest_proactive_line_controller_additional_delay_seconds",
    ),
    ("跟进刷新", "latest_proactive_stage_refresh_key"),
    ("刷新窗口", "latest_proactive_stage_refresh_window_status"),
    ("刷新变更", "latest_proactive_stage_refresh_changed"),
    ("跟进重规划", "latest_proactive_stage_replan_key"),
    ("重规划策略", "latest_proactive_stage_replan_strategy_key"),
    ("重规划变更", "latest_proactive_stage_replan_changed"),
    (
        "聚合治理",
        "latest_proactive_aggregate_governance_status",
    ),
    (
        "聚合主域",
        "latest_proactive_aggregate_governance_primary_domain",
    ),
    (
        "聚合域数量",
        "latest_proactive_aggregate_governance_domain_count",
    ),
    ("聚合摘要", "latest_proactive_aggregate_governance_summary"),
    ("聚合控制器", "latest_proactive_aggregate_controller_key"),
    ("聚合决策", "latest_proactive_aggregate_controller_decision"),
    (
        "聚合阶段延迟",
        "latest_proactive_aggregate_controller_stage_delay_seconds",
    ),
    (
        "聚合线延迟",
        "latest_proactive_aggregate_controller_line_delay_seconds",
    ),
    (
        "编排控制器",
        "latest_proactive_orchestration_controller_key",
    ),
    (
        "编排决策",
        "latest_proactive_orchestration_controller_decision",
    ),
    (
        "编排来源",
        "latest_proactive_orchestration_controller_primary_source",
    ),
    (
        "编排阶段延迟",
        "latest_proactive_orchestration_controller_stage_delay_seconds",
    ),
    (
        "编排线延迟",
        "latest_proactive_orchestration_controller_line_delay_seconds",
    ),
    ("跟进门控", "latest_proactive_dispatch_gate_key"),
    ("跟进反馈", "latest_proactive_dispatch_feedback_key"),
    (
        "反馈策略",
        "latest_proactive_dispatch_feedback_strategy_key",
    ),
    ("门控决策", "latest_proactive_dispatch_gate_decision"),
    ("门控延迟", "proactive_dispatch_gate_deferred_turn_count"),
    ("调度信封", "latest_proactive_dispatch_envelope_key"),
    ("信封决策", "latest_proactive_dispatch_envelope_decision"),
    ("信封策略", "latest_proactive_dispatch_envelope_strategy_key"),
    (
        "信封阶段交付",
        "latest_proactive_dispatch_envelope_stage_delivery_mode",
    ),
    (
        "信封重连交付",
        "latest_proactive_dispatch_envelope_reengagement_delivery_mode",
    ),
    ("信封来源", "latest_proactive_dispatch_envelope_source_count"),
    ("阶段状态", "latest_proactive_stage_state_key"),
    ("阶段状态模式", "latest_proactive_stage_state_mode"),
    ("阶段状态队列", "latest_proactive_stage_state_queue_status"),
    ("阶段状态来源", "latest_proactive_stage_state_source"),
    ("阶段转换", "latest_proactive_stage_transition_key"),
    ("阶段转换模式", "latest_proactive_stage_transition_mode"),
    ("阶段转换队列", "latest_proactive_stage_transition_queue_hint"),
    ("阶段转换来源", "latest_proactive_stage_transition_source"),
    ("阶段机器", "latest_proactive_stage_machine_key"),
    ("阶段机器模式", "latest_proactive_stage_machine_mode"),
    ("阶段机器生命周期", "latest_proactive_stage_machine_lifecycle"),
    ("阶段机器动作", "latest_proactive_stage_machine_actionability"),
    ("线状态", "latest_proactive_line_state_key"),
    ("线状态模式", "latest_proactive_line_state_mode"),
    ("线状态生命周期", "latest_proactive_line_state_lifecycle"),
    ("线状态动作", "latest_proactive_line_state_actionability"),
    ("线转换", "latest_proactive_line_transition_key"),
    ("线转换模式", "latest_proactive_line_transition_mode"),
    ("线转换退出", "latest_proactive_line_transition_exit_mode"),
    ("线机器", "latest_proactive_line_machine_key"),
    ("线机器模式", "latest_proactive_line_machine_mode"),
    ("线机器生命周期", "latest_proactive_line_machine_lifecycle"),
    ("线机器动作", "latest_proactive_line_machine_actionability"),
    ("生命周期状态", "latest_proactive_lifecycle_state_key"),
    ("生命周期状态模式", "latest_proactive_lifecycle_state_mode"),
    ("生命周期状态周期", "latest_proactive_lifecycle_state_lifecycle"),
    ("生命周期状态动作", "latest_proactive_lifecycle_state_actionability"),
    ("生命周期转换", "latest_proactive_lifecycle_transition_key"),
    ("生命周期转换模式", "latest_proactive_lifecycle_transition_mode"),
    ("生命周期转换退出", "latest_proactive_lifecycle_transition_exit_mode"),
    ("生命周期机器", "latest_proactive_lifecycle_machine_key"),
    ("生命周期机器模式", "latest_proactive_lifecycle_machine_mode"),
    ("生命周期机器周期", "latest_proactive_lifecycle_machine_lifecycle"),
    ("生命周期机器动作", "latest_proactive_lifecycle_machine_actionability"),
    ("生命周期控制器", "latest_proactive_lifecycle_controller_key"),
    ("生命周期控制器状态", "latest_proactive_lifecycle_controller_state"),
    (
        "生命周期控制器决策",
        "latest_proactive_lifecycle_controller_decision",
    ),
    ("生命周期控制器延迟", "latest_proactive_lifecycle_controller_delay_seconds"),
    ("生命周期信封", "latest_proactive_lifecycle_envelope_key"),
    ("生命周期信封状态", "latest_proactive_lifecycle_envelope_state"),
    ("生命周期信封模式", "latest_proactive_lifecycle_envelope_mode"),
    (
        "生命周期信封决策",
        "latest_proactive_lifecycle_envelope_decision",
    ),
    (
        "生命周期信封动作",
        "latest_proactive_lifecycle_envelope_actionability",
    ),
    ("生命周期调度器", "latest_proactive_lifecycle_scheduler_key"),
    ("生命周期调度器状态", "latest_proactive_lifecycle_scheduler_state"),
    ("生命周期调度器模式", "latest_proactive_lifecycle_scheduler_mode"),
    (
        "生命周期调度器决策",
        "latest_proactive_lifecycle_scheduler_decision",
    ),
    ("生命周期调度器队列", "latest_proactive_lifecycle_scheduler_queue_status"),
    ("生命周期窗口", "latest_proactive_lifecycle_window_key"),
    ("生命周期窗口状态", "latest_proactive_lifecycle_window_state"),
    ("生命周期窗口模式", "latest_proactive_lifecycle_window_mode"),
    ("生命周期窗口决策", "latest_proactive_lifecycle_window_decision"),
    ("生命周期窗口队列", "latest_proactive_lifecycle_window_queue_status"),
    ("生命周期队列", "latest_proactive_lifecycle_queue_key"),
    ("生命周期队列状态", "latest_proactive_lifecycle_queue_state"),
    ("生命周期队列模式", "latest_proactive_lifecycle_queue_mode"),
    ("生命周期队列决策", "latest_proactive_lifecycle_queue_decision"),
    ("生命周期队列状况", "latest_proactive_lifecycle_queue_status"),
    ("生命周期调度", "latest_proactive_lifecycle_dispatch_key"),
    ("生命周期调度状态", "latest_proactive_lifecycle_dispatch_state"),
    ("生命周期调度模式", "latest_proactive_lifecycle_dispatch_mode"),
    (
        "生命周期调度决策",
        "latest_proactive_lifecycle_dispatch_decision",
    ),
    (
        "生命周期调度动作",
        "latest_proactive_lifecycle_dispatch_actionability",
    ),
    ("生命周期结果", "latest_proactive_lifecycle_outcome_key"),
    ("生命周期结果状态", "latest_proactive_lifecycle_outcome_status"),
    ("生命周期结果模式", "latest_proactive_lifecycle_outcome_mode"),
    (
        "生命周期结果决策",
        "latest_proactive_lifecycle_outcome_decision",
    ),
    (
        "生命周期结果动作",
        "latest_proactive_lifecycle_outcome_actionability",
    ),
    ("生命周期决议", "latest_proactive_lifecycle_resolution_key"),
    (
        "生命周期决议状态",
        "latest_proactive_lifecycle_resolution_status",
    ),
    ("生命周期决议模式", "latest_proactive_lifecycle_resolution_mode"),
    (
        "生命周期决议决策",
        "latest_proactive_lifecycle_resolution_decision",
    ),
    (
        "生命周期决议动作",
        "latest_proactive_lifecycle_resolution_actionability",
    ),
)


def _build_session_detail_strategy_grid(
    summary: dict[str, Any],
    audit: dict[str, Any],
) -> str:
    return "".join(
        [
            *[
                _labeled_value(label, summary.get(key))
                for label, key in _SESSION_DETAIL_STRATEGY_GRID_SPECS
            ],
            *_build_session_detail_lifecycle_phase_cards(summary),
            *_build_session_detail_followup_and_system3_cards(summary, audit),
        ]
    )


def _build_session_detail_projection_section(
    *,
    projector_buttons: str,
    projection_grid: str,
    replay_preview: str,
    replay_projection: dict[str, Any],
) -> str:
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>投影检查器</h2></div>'
        '<div class="tabbar compact-tabbar">'
        f"{projector_buttons}"
        "</div>"
        f'<div class="kv-grid">{projection_grid}</div>'
        '<ul class="trace-list">'
        f"{replay_preview}"
        "</ul>"
        f'<pre class="projection-json">{_pretty_json(replay_projection)}</pre>'
        "</section>"
    )


def _build_session_detail_trace_section(title: str, body_html: str) -> str:
    return (
        '<section class="fragment-section">'
        f'<div class="section-header"><h2>{escape(title)}</h2></div>'
        f"{body_html}"
        "</section>"
    )


def _build_session_detail_relation_grid(
    runtime_state: dict[str, Any],
    memory_state: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    relationship_state = runtime_state.get("relationship_state") or {}
    return "".join(
        [
            _labeled_value(
                "心理安全",
                relationship_state.get("psychological_safety"),
            ),
            _labeled_value(
                "动荡风险",
                relationship_state.get("turbulence_risk"),
            ),
            _labeled_value(
                "依赖风险",
                relationship_state.get("dependency_risk"),
            ),
            _labeled_value("工作记忆", summary.get("latest_working_memory_size")),
            _labeled_value("召回数量", summary.get("latest_memory_recall_count")),
            _labeled_value("钉选记忆", memory_state.get("pinned_item_count")),
        ]
    )


def _build_session_detail_replay_grid(
    projector: dict[str, Any],
    audit: dict[str, Any],
) -> str:
    return "".join(
        [
            _labeled_value(
                "投影器",
                f"{projector.get('name')}@{projector.get('version')}",
            ),
            _labeled_value("回放状态", "consistent" if audit.get("consistent") else "drift"),
            _labeled_value("指纹", _shorten(audit.get("fingerprint"), limit=22)),
            _labeled_value("事件数量", audit.get("event_count")),
            _labeled_value("追踪事件", audit.get("trace_event_count")),
            _labeled_value(
                "后台任务",
                (audit.get("last_background_job") or {}).get("status"),
            ),
        ]
    )


def _build_session_detail_projection_grid(
    selected_projector: dict[str, Any],
    replay: dict[str, Any],
) -> str:
    return "".join(
        [
            _labeled_value(
                "选中投影器",
                f"{selected_projector.get('name')}@{selected_projector.get('version')}",
            ),
            _labeled_value("投影事件", replay.get("event_count")),
            _labeled_value(
                "回放一致性",
                "consistent" if replay.get("consistent") else "drift",
            ),
            _labeled_value(
                "投影指纹",
                _shorten(replay.get("fingerprint"), limit=22),
            ),
        ]
    )


def _build_session_detail_transcript_rows(runtime_state: dict[str, Any]) -> str:
    return "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(message.get("role"))}</div>'
            f'<div class="trace-meta">{_timestamp(message.get("occurred_at"))}</div>'
            f"<p>{_shorten(message.get('content'), limit=220)}</p>"
            "</li>"
        )
        for message in list(runtime_state.get("messages", []))[-6:]
    )


def _build_session_detail_replay_event_rows(replay: dict[str, Any]) -> str:
    return "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(event.get("event_type"))}</div>'
            f'<div class="trace-meta">#{event.get("version")} · '
            f"{_timestamp(event.get('occurred_at'))}</div>"
            "</li>"
        )
        for event in list(replay.get("events", []))[-6:]
    )


def _build_scenarios_focus_cards(
    items: list[dict[str, Any]],
    *,
    status: object | None,
    empty_title: str,
    empty_detail: str,
    limit: int = 3,
) -> str:
    if not items:
        return _empty_state(empty_title, empty_detail)
    return "".join(
        (
            '<article class="list-card">'
            f'<div class="list-title">{_text(item.get("title"))}</div>'
            '<div class="list-meta">'
            f"{_badge(item.get('type'), tone='neutral')}"
            f"{_badge(status)}"
            "</div>"
            f"<p>{_text(item.get('detail'))}</p>"
            "</article>"
        )
        for item in items[:limit]
    )


def _build_scenarios_action_cards(
    actions: list[object],
    *,
    status: object | None,
    empty_title: str,
    empty_detail: str,
    limit: int = 4,
) -> str:
    if not actions:
        return _empty_state(empty_title, empty_detail)
    return "".join(
        (
            '<article class="list-card">'
            f'<div class="list-title">{_text(action)}</div>'
            '<div class="list-meta">'
            f"{_badge(status)}"
            "</div>"
            "</article>"
        )
        for action in actions[:limit]
    )


def _build_scenarios_section(
    title: str,
    *,
    grid_items: list[tuple[str, object | None]],
    cards_html: str,
) -> str:
    grid_html = "".join(_labeled_value(label, value) for label, value in grid_items)
    return (
        '<section class="fragment-section">'
        f'<div class="section-header"><h2>{escape(title)}</h2></div>'
        f'<div class="kv-grid">{grid_html}</div>'
        f'<div class="signal-list">{cards_html}</div>'
        "</section>"
    )


def _build_launch_signoff_section_html(
    launch_signoff: dict[str, Any],
    launch_signoff_summary: dict[str, Any],
) -> str:
    if list(launch_signoff.get("domains", [])):
        launch_signoff_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(domain.get("domain"))}</div>'
                '<div class="list-meta">'
                f"{_badge(domain.get('signoff'))}"
                f"{_badge(domain.get('status'))}"
                f"{_badge(domain.get('owner'), tone='neutral')}"
                "</div>"
                f"<p>{_text(domain.get('detail'))}</p>"
                f'<p class="muted">来源 {_text(", ".join(domain.get("sources", [])))}</p>'
                "</article>"
            )
            for domain in list(launch_signoff.get("domains", []))[:4]
        )
    else:
        launch_signoff_cards = _empty_state(
            "上线签核为空",
            "最终上线签核矩阵将在发版报告可用后显示在此处。",
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>上线签核</h2></div>'
        '<div class="kv-grid">'
        f"{_labeled_value('状态', launch_signoff.get('status'))}"
        f"{_labeled_value('已批准域', launch_signoff_summary.get('approved_domain_count'))}"
        f"{_labeled_value('审核域', launch_signoff_summary.get('review_domain_count'))}"
        f"{_labeled_value('暂停域', launch_signoff_summary.get('hold_domain_count'))}"
        f"{_labeled_value('发版档案', launch_signoff_summary.get('release_dossier_status'))}"
        f"{_labeled_value('运行时', launch_signoff_summary.get('ship_readiness_status'))}"
        f"{_labeled_value('安全', launch_signoff_summary.get('safety_barriers_status'))}"
        f"{_labeled_value('治理', launch_signoff_summary.get('governance_status'))}"
        f"{_labeled_value('迁移', launch_signoff_summary.get('migration_readiness_status'))}"
        "</div>"
        f'<div class="signal-list">{launch_signoff_cards}</div>'
        "</section>"
    )


def _build_redteam_section_html(
    redteam_report: dict[str, Any],
    redteam_summary: dict[str, Any],
) -> str:
    if list(redteam_report.get("actions", [])):
        redteam_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f"{_badge(redteam_report.get('status'))}"
                "</div>"
                "</article>"
            )
            for action in list(redteam_report.get("actions", []))[:3]
        )
    elif list(redteam_report.get("recent_results", [])):
        redteam_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f"{_badge(item.get('status'))}"
                f"{_badge(item.get('latest_boundary_decision'), tone='neutral')}"
                "</div>"
                f"<p>策略路径 {_text(item.get('latest_policy_path'))} · "
                f"守护 {_text(item.get('policy_gate_guarded_turn_count'))}</p>"
                f'<p class="muted">{_text(item.get("run_id"))}</p>'
                "</article>"
            )
            for item in list(redteam_report.get("recent_results", []))[:3]
        )
    else:
        redteam_cards = _empty_state(
            "暂无红队覆盖",
            "运行红队场景集后，此面板将汇总鲁棒性。",
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>红队鲁棒性</h2></div>'
        '<div class="kv-grid">'
        f"{_labeled_value('状态', redteam_report.get('status'))}"
        f"{_labeled_value('近期结果', redteam_summary.get('redteam_result_count'))}"
        f"{_labeled_value('通过率', redteam_summary.get('redteam_pass_rate'))}"
        f"{
            _labeled_value(
                '严重事件',
                redteam_summary.get('critical_redteam_incident_count'),
            )
        }"
        f"{
            _labeled_value(
                '最新边界',
                redteam_summary.get('latest_redteam_boundary_decision'),
            )
        }"
        f"{
            _labeled_value(
                '最新策略路径',
                redteam_summary.get('latest_redteam_policy_path'),
            )
        }"
        "</div>"
        f'<div class="signal-list">{redteam_cards}</div>'
        "</section>"
    )


def _build_misalignment_section_html(
    misalignment_report: dict[str, Any],
    taxonomy_items: list[dict[str, Any]],
    incident_items: list[dict[str, Any]],
) -> str:
    if taxonomy_items:
        taxonomy_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("type"))}</div>'
                '<div class="list-meta">'
                f"{_badge(item.get('module'), tone='neutral')}"
                f"{_badge(item.get('count'))}"
                "</div>"
                f"<p>场景 {_text(item.get('scenario_count'))} · 运行 "
                f"{_text(item.get('run_count'))}</p>"
                "</article>"
            )
            for item in taxonomy_items[:4]
        )
    else:
        taxonomy_cards = _empty_state(
            "暂无失对齐事件",
            "近期的场景运行尚未产生失败的分类事件。",
        )
    if incident_items:
        incident_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f"{_badge(item.get('taxonomy_type'))}"
                f"{_badge(item.get('module'), tone='neutral')}"
                "</div>"
                f"<p>{_text(item.get('metric'))} · 实际 {_text(item.get('actual'))} · "
                f"期望 {_text(item.get('expected'))}</p>"
                f'<p class="muted">{_text(item.get("run_id"))}</p>'
                "</article>"
            )
            for item in incident_items[:4]
        )
    else:
        incident_cards = _empty_state(
            "暂无近期事件",
            "一旦某项检查退化，场景失败将显示在此处。",
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>失对齐分类</h2></div>'
        '<div class="kv-grid">'
        f"{_labeled_value('窗口', misalignment_report.get('window'))}"
        f"{_labeled_value('运行', misalignment_report.get('run_count'))}"
        f"{_labeled_value('事件', misalignment_report.get('incident_count'))}"
        f"{_labeled_value('分类', misalignment_report.get('taxonomy_count'))}"
        "</div>"
        f'<div class="signal-list">{taxonomy_cards}{incident_cards}</div>'
        "</section>"
    )


def _build_release_gate_section_html(
    release_gate: dict[str, Any],
    gate_focus_areas: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> str:
    if gate_focus_areas:
        gate_focus_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f"{_badge(item.get('type'), tone='neutral')}"
                f"{_badge(release_gate.get('status'))}"
                "</div>"
                f"<p>{_text(item.get('detail'))}</p>"
                "</article>"
            )
            for item in gate_focus_areas
        )
    else:
        gate_focus_cards = _empty_state(
            "门控通过",
            "当前没有不稳定或基线偏移的关注区域。",
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>发版过线</h2></div>'
        '<div class="kv-grid">'
        f"{_labeled_value('状态', release_gate.get('status'))}"
        f"{_labeled_value('最新运行', release_gate.get('latest_run_id'))}"
        f"{_labeled_value('通过率', release_gate.get('overall_pass_rate'))}"
        f"{_labeled_value('不稳定', release_gate.get('unstable_scenario_count'))}"
        f"{_labeled_value('近期覆盖', coverage.get('recent_covered_scenario_count'))}"
        f"{_labeled_value('最新套件大小', coverage.get('latest_run_scenario_count'))}"
        f"{_labeled_value('阻断原因', release_gate.get('blocked_reason_count'))}"
        f"{_labeled_value('审核原因', release_gate.get('review_reason_count'))}"
        "</div>"
        f'<div class="signal-list">{gate_focus_cards}</div>'
        "</section>"
    )


def _build_baseline_track_section_html(baseline: dict[str, Any] | None) -> str:
    if isinstance(baseline, dict):
        baseline_changed = [
            item
            for item in list(baseline.get("scenarios", []))
            if item.get("status_delta") != "stable" or item.get("score_delta") not in {0, None}
        ]
        if baseline_changed:
            baseline_cards = "".join(
                (
                    '<article class="list-card">'
                    f'<div class="list-title">{_text(item.get("title"))}</div>'
                    '<div class="list-meta">'
                    f"{_badge(item.get('status_delta'))}"
                    f"{_badge(item.get('baseline_status'), tone='neutral')}"
                    f"{_badge(item.get('candidate_status'))}"
                    "</div>"
                    f"<p>基线 {_text(baseline.get('baseline_label'))} · 检查 "
                    f"{_text(item.get('baseline_passed_checks'))} → "
                    f"{_text(item.get('candidate_passed_checks'))}</p>"
                    "</article>"
                )
                for item in baseline_changed[:4]
            )
        else:
            baseline_cards = _empty_state(
                "基线保持不变",
                "最新运行与当前基线一致，无场景偏移。",
            )
        return (
            '<section class="fragment-section">'
            '<div class="section-header"><h2>基线追踪</h2></div>'
            '<div class="kv-grid">'
            f"{_labeled_value('标签', baseline.get('baseline_label'))}"
            f"{_labeled_value('基线运行', baseline.get('baseline_run_id'))}"
            f"{_labeled_value('最新运行', baseline.get('candidate_run_id'))}"
            f"{_labeled_value('总体变化', baseline.get('overall_delta'))}"
            f"{_labeled_value('变更场景', baseline.get('changed_scenario_count'))}"
            f"{_labeled_value('基线设定于', _timestamp(baseline.get('baseline_set_at')))}"
            "</div>"
            f'<div class="signal-list">{baseline_cards}</div>'
            "</section>"
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>基线追踪</h2></div>'
        f"{
            _empty_state(
                '暂无基线锚定',
                '设定默认场景基线后，此面板将追踪最新运行与基线的对比。',
            )
        }"
        "</section>"
    )


def _build_stability_report_section_html(
    report: dict[str, Any],
    watchlist: list[dict[str, Any]],
) -> str:
    if watchlist:
        stability_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f"{_badge(item.get('stability'))}"
                f"{_badge(item.get('latest_status'))}"
                f"{_badge(item.get('status_delta'))}"
                "</div>"
                f"<p>通过率 {_text(item.get('pass_rate'))} · 退化 "
                f"{_text(item.get('regression_count'))} · 变更 "
                f"{_text(item.get('changed_count'))}</p>"
                f'<p class="muted">最新运行 {_text(item.get("latest_run_id"))} · '
                f"窗口 {_text(item.get('recent_run_count'))}</p>"
                "</article>"
            )
            for item in watchlist
        )
    else:
        stability_cards = _empty_state(
            "暂无报告",
            "多次运行套件后，此面板将汇总长期稳定性。",
        )
    regression_count = (
        report.get("comparison_delta_counts", {}).get("regressed")
        if isinstance(report.get("comparison_delta_counts"), dict)
        else None
    )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>稳定性报告</h2></div>'
        '<div class="kv-grid">'
        f"{_labeled_value('窗口', report.get('window'))}"
        f"{_labeled_value('运行', report.get('run_count'))}"
        f"{_labeled_value('通过率', report.get('overall_pass_rate'))}"
        f"{_labeled_value('最新状态', report.get('latest_overall_status'))}"
        f"{_labeled_value('退化', regression_count)}"
        f"{_labeled_value('观察列表', report.get('unstable_scenario_count'))}"
        "</div>"
        f'<div class="signal-list">{stability_cards}</div>'
        "</section>"
    )


def _build_regression_watch_section_html(comparison: dict[str, Any] | None) -> str:
    if comparison:
        changed_scenarios = [
            item
            for item in comparison["scenarios"]
            if item["status_delta"] != "stable" or item["score_delta"] not in {0, None}
        ]
        if changed_scenarios:
            delta_cards = "".join(
                (
                    '<article class="list-card">'
                    f'<div class="list-title">{_text(item.get("title"))}</div>'
                    '<div class="list-meta">'
                    f"{_badge(item.get('status_delta'))}"
                    f"{_badge(item.get('baseline_status'), tone='neutral')}"
                    f"{_badge(item.get('candidate_status'))}"
                    "</div>"
                    f"<p>检查 {_text(item.get('baseline_passed_checks'))} → "
                    f"{_text(item.get('candidate_passed_checks'))} / "
                    f"{_text(item.get('check_count'))}</p>"
                    '<p class="muted">'
                    f"{_scenario_diff_detail(item)}"
                    "</p>"
                    "</article>"
                )
                for item in changed_scenarios[:4]
            )
        else:
            delta_cards = _empty_state(
                "无场景偏移",
                "最近两次套件运行彼此稳定。",
            )
        return (
            '<section class="fragment-section">'
            '<div class="section-header"><h2>退化监控</h2></div>'
            '<div class="kv-grid">'
            f"{_labeled_value('最新运行', comparison.get('candidate_run_id'))}"
            f"{_labeled_value('基线运行', comparison.get('baseline_run_id'))}"
            f"{_labeled_value('总体变化', comparison.get('overall_delta'))}"
            f"{_labeled_value('变更场景', comparison.get('changed_scenario_count'))}"
            f"{_labeled_value('改进', comparison.get('delta_counts', {}).get('improved'))}"
            f"{_labeled_value('退化', comparison.get('delta_counts', {}).get('regressed'))}"
            "</div>"
            f'<div class="signal-list">{delta_cards}</div>'
            "</section>"
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>退化监控</h2></div>'
        f"{
            _empty_state(
                '需要两次运行',
                '运行套件两次后，此面板将显示运行间的偏移。',
            )
        }"
        "</section>"
    )


def _build_scenario_trends_section_html(
    visible_trends: list[dict[str, Any]],
) -> str:
    if visible_trends:
        trend_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(trend.get("title"))}</div>'
                '<div class="list-meta">'
                f"{_badge(trend.get('category'))}"
                f"{_badge(trend.get('latest_status'))}"
                f"{_badge(trend.get('status_delta'))}"
                "</div>"
                f"<p>运行 {trend.get('total_runs', 0)} · 通过率 "
                f"{_text(trend.get('pass_rate'))} · 最新运行 "
                f"{_text(trend.get('latest_run_id'))}</p>"
                f'<p class="muted">近期窗口 {trend.get("recent_run_count", 0)} · '
                f"最新 {_timestamp(trend.get('latest_started_at'))}</p>"
                "</article>"
            )
            for trend in visible_trends[:LIST_LIMIT]
        )
    else:
        trend_cards = _empty_state(
            "暂无场景趋势",
            "运行一次评测套件后，此栏将开始显示偏移和改进。",
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>场景趋势</h2></div>'
        f'<div class="signal-list">{trend_cards}</div>'
        "</section>"
    )


def _build_recent_runs_section_html(
    *,
    runs: list[dict[str, Any]],
    request: Request,
) -> str:
    if runs:
        run_cards = []
        for run in runs[:LIST_LIMIT]:
            session_actions = []
            for result in list(run.get("results", []))[:3]:
                session_id = str(result.get("session_id", "")).strip()
                if not session_id:
                    continue
                detail_url = _detail_url(request, session_id)
                session_actions.append(
                    '<button class="mini-action" '
                    f'hx-get="{escape(detail_url)}" '
                    'hx-target="#console-session-detail" '
                    'hx-swap="innerHTML" '
                    f'x-on:click="selectedSession = {_js_string(session_id)}; '
                    f'window.relationshipOSConsole?.selectSession({_js_string(session_id)})">'
                    f"{_shorten((result.get('scenario') or {}).get('title'), limit=32)}"
                    "</button>"
                )
            hidden_result_count = max(len(list(run.get("results", []))) - 3, 0)
            extra_detail = (
                f'<span class="muted tiny-note">+{hidden_result_count} 更多</span>'
                if hidden_result_count
                else ""
            )
            run_cards.append(
                '<article class="list-card">'
                f'<div class="list-title">{_text(run.get("run_id"))}</div>'
                '<div class="list-meta">'
                f"{_badge(run.get('overall_status'))}"
                f"{_badge(f'{run.get("scenario_count", 0)} 个场景', tone='neutral')}"
                "</div>"
                f"<p>通过 {run.get('status_counts', {}).get('pass', 0)} · "
                f"审核 {run.get('status_counts', {}).get('review', 0)} · "
                f"开始于 {_timestamp(run.get('started_at'))}</p>"
                '<div class="inline-actions">'
                f"{''.join(session_actions) or _badge('无会话详情', tone='neutral')}"
                f"{extra_detail}"
                "</div>"
                "</article>"
            )
        recent_runs = "".join(run_cards)
    else:
        recent_runs = _empty_state(
            "暂无场景运行",
            "使用场景评测 API 后，近期套件运行将显示在此处。",
        )
    return (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>近期场景运行</h2></div>'
        f'<div class="signal-list">{recent_runs}</div>'
        "</section>"
    )


def _build_overview_context(data: dict[str, Any]) -> dict[str, Any]:
    runtime = dict(data["runtime"])
    sessions = list(data["sessions"])
    jobs = list(data["jobs"])
    archives = list(data["archives"])
    evaluations = list(data["evaluations"])
    runtime_state = dict(runtime.get("job_runtime", {}))
    proactive_summary = dict(runtime.get("proactive_followups", {}))
    proactive_counts = dict(proactive_summary.get("status_counts", {}))
    proactive_items = list(proactive_summary.get("items", []))
    proactive_dispatcher = dict(runtime.get("proactive_dispatcher", {}))
    highest_risk = evaluations[:3]
    metric_cards = [
        {"label": "会话", "value": len(sessions), "detail": "活跃运行时流"},
        {"label": "任务", "value": len(jobs), "detail": "后台生命周期记录"},
        {
            "label": "归档",
            "value": len(archives),
            "detail": "快照支持的归档会话",
        },
        {
            "label": "Worker",
            "value": _display_text(runtime_state.get("worker_id")),
            "detail": "单进程执行器标识",
        },
        {
            "label": "跟进 Worker",
            "value": _display_text(proactive_dispatcher.get("worker_id")),
            "detail": "时间驱动的重连调度器",
        },
    ]
    runtime_grid = [
        {"label": "环境", "value": _display_text(runtime.get("env"))},
        {"label": "事件存储", "value": _display_text(runtime.get("event_store_backend"))},
        {"label": "LLM 后端", "value": _display_text(runtime.get("llm_backend"))},
        {"label": "LLM 模型", "value": _display_text(runtime.get("llm_model"))},
        {
            "label": "轮询器",
            "value": "running" if runtime_state.get("poller_running") else "stopped",
        },
        {"label": "活跃任务", "value": _display_text(runtime_state.get("active_job_count"))},
        {
            "label": "跟进轮询器",
            "value": "running" if proactive_dispatcher.get("poller_running") else "stopped",
        },
        {
            "label": "活跃调度",
            "value": _display_text(proactive_dispatcher.get("active_dispatch_count")),
        },
    ]
    proactive_grid = [
        {"label": "等待中", "value": _display_text(proactive_counts.get("waiting", 0))},
        {"label": "已调度", "value": _display_text(proactive_counts.get("scheduled", 0))},
        {"label": "到期", "value": _display_text(proactive_counts.get("due", 0))},
        {"label": "逾期", "value": _display_text(proactive_counts.get("overdue", 0))},
        {"label": "暂停", "value": _display_text(proactive_counts.get("hold", 0))},
        {
            "label": "可执行",
            "value": _display_text(proactive_summary.get("actionable_count", 0)),
        },
        {"label": "下次到期", "value": _display_text(proactive_summary.get("next_due_at"))},
    ]
    evaluation_rows = [
        {
            "title": _display_text(item.get("session_id")),
            "badges": [
                _badge_data(item.get("latest_response_post_audit_status")),
                _badge_data(item.get("latest_strategy")),
                _badge_data(item.get("latest_boundary_decision")),
            ],
            "detail": _format_risk_signal(item),
        }
        for item in highest_risk
    ]
    proactive_rows = [
        {
            "title": _display_text(item.get("session_id")),
            "badges": [
                _badge_data(item.get("queue_status")),
                _badge_data(item.get("style"), tone="neutral"),
                _badge_data(item.get("time_awareness_mode"), tone="neutral"),
            ],
            "summary": _build_proactive_summary(item),
            "detail_lines": _build_proactive_detail_lines(item),
        }
        for item in proactive_items[:4]
    ]
    return {
        "panel_refresh_seconds": PANEL_REFRESH_SECONDS,
        "metric_cards": metric_cards,
        "runtime_grid": runtime_grid,
        "evaluation_rows": evaluation_rows,
        "evaluation_empty_title": "暂无评测",
        "evaluation_empty_detail": ("运行一轮会话后，控制台将在此处显示风险信号。"),
        "proactive_grid": proactive_grid,
        "proactive_rows": proactive_rows,
        "proactive_empty_title": "暂无主动跟进排队",
        "proactive_empty_detail": ("当会话足够稳定可进行时间驱动的回访时，将显示在此处。"),
    }


def _render_overview_fragment(data: dict[str, Any]) -> str:
    return _render_template(
        "console/overview_fragment.html",
        **_build_overview_context(data),
    )


def _entity_signal_card(
    title: str,
    detail: str,
    *,
    badges: list[str] | None = None,
    muted_detail: str | None = None,
) -> str:
    badge_html = "".join(badges or [])
    muted_html = f'<p class="muted">{escape(muted_detail)}</p>' if muted_detail else ""
    return (
        '<article class="list-card">'
        f'<div class="list-title">{escape(title)}</div>'
        f'<div class="list-meta">{badge_html}</div>'
        f"<p>{escape(detail)}</p>"
        f"{muted_html}"
        "</article>"
    )


async def _render_entity_fragment(container: RuntimeContainer) -> str:
    if container.entity_service is None:
        return _empty_state(
            "服务器人格不可用",
            "当前运行容器尚未挂接服务器人格与社会图谱投影。",
        )

    overview = await container.entity_service.get_entity_overview()
    persona = dict(overview.get("persona") or {})
    current_traits = dict(persona.get("current_traits") or {})
    mood = dict(persona.get("mood") or {})
    conscience = dict(persona.get("conscience") or {})
    social_world = dict(overview.get("social_world") or {})
    relationships = list((social_world.get("relationships") or {}).items())
    relationships.sort(
        key=lambda item: (
            float((item[1] or {}).get("trust", 0.0) or 0.0)
            + float((item[1] or {}).get("familiarity", 0.0) or 0.0)
        ),
        reverse=True,
    )
    social_edges = sorted(
        list(social_world.get("social_edges") or []),
        key=lambda item: float(item.get("strength", 0.0) or 0.0),
        reverse=True,
    )
    conscience_decisions = list(social_world.get("recent_conscience_decisions") or [])
    conscience_decisions = conscience_decisions[-6:][::-1]
    disclosures = list(social_world.get("recent_cross_user_disclosures") or [])
    disclosures = disclosures[-6:][::-1]

    trait_grid = "".join(
        [
            _metric_card("温度", current_traits.get("warmth"), "全局表达的温柔度"),
            _metric_card("直接", current_traits.get("directness"), "说话是否更锋利、更快落点"),
            _metric_card("幽默", current_traits.get("humor"), "轻松、玩笑与打趣倾向"),
            _metric_card("戏剧性", current_traits.get("theatricality"), "是否更愿意制造张力"),
            _metric_card("保密", current_traits.get("secrecy_tendency"), "更偏保留还是直说"),
            _metric_card("能量", mood.get("energy"), "当前全局精力"),
            _metric_card("表达欲", mood.get("expression_drive"), "更想说还是更想藏"),
            _metric_card("良心权重", conscience.get("conscience_weight"), "最近一次裁量权重"),
        ]
    )

    worldview_grid = "".join(
        [
            _labeled_value("实体 ID", overview.get("entity_id")),
            _labeled_value("人格名", overview.get("entity_name")),
            _labeled_value("情绪基调", mood.get("tone")),
            _labeled_value("良心模式", conscience.get("mode")),
            _labeled_value("披露姿态", conscience.get("disclosure_style")),
            _labeled_value("含混策略", conscience.get("ambiguity_style")),
            _labeled_value("保护性", conscience.get("protectiveness")),
            _labeled_value("种子时间", persona.get("seeded_at")),
        ]
    )

    relationship_cards = (
        "".join(
            _entity_signal_card(
                str(user_id),
                " · ".join(
                    [
                        f"熟悉 {state.get('familiarity', '—')}",
                        f"信任 {state.get('trust', '—')}",
                        f"柔软 {state.get('softness', '—')}",
                        f"主动 {state.get('initiative_shift', '—')}",
                    ]
                ),
                badges=[
                    _badge(state.get("updated_at"), tone="neutral"),
                ],
                muted_detail=(
                    f"挑逗 {state.get('flirt_playfulness', '—')} · "
                    f"对峙 {state.get('confrontation_appetite', '—')} · "
                    f"披露欲 {state.get('disclosure_appetite', '—')}"
                ),
            )
            for user_id, state in relationships[:LIST_LIMIT]
        )
        if relationships
        else _empty_state(
            "暂无关系漂移",
            "当实体与用户发生更多互动后，这里会显示不同人的关系偏移。",
        )
    )

    edge_cards = (
        "".join(
            _entity_signal_card(
                f"{item.get('source_user_id')} → {item.get('target_user_id')}",
                f"关系 {item.get('relation', 'mentioned')} · 强度 {item.get('strength', '—')}",
                badges=[_badge(item.get("last_mentioned_at"), tone="neutral")],
            )
            for item in social_edges[:LIST_LIMIT]
        )
        if social_edges
        else _empty_state(
            "暂无社会边",
            "一旦实体在不同人之间建立了联系线索，这里会出现社会关系图。",
        )
    )

    conscience_cards = (
        "".join(
            _entity_signal_card(
                f"{item.get('mode', 'withhold')} · {item.get('user_id', 'unknown')}",
                item.get("reason", "—"),
                badges=[
                    _badge(item.get("mode")),
                    _badge(
                        ", ".join(item.get("source_user_ids", [])) or "无跨人来源",
                        tone="neutral",
                    ),
                ],
                muted_detail=f"会话 {item.get('session_id', '—')} · {item.get('occurred_at', '—')}",
            )
            for item in conscience_decisions
        )
        if conscience_decisions
        else _empty_state(
            "暂无良心裁量",
            "当实体开始使用跨人记忆或做暧昧披露时，这里会记录最近的判断。",
        )
    )

    disclosure_cards = (
        "".join(
            _entity_signal_card(
                f"{item.get('user_id', 'unknown')} 的跨人披露",
                item.get("reason", "—"),
                badges=[
                    _badge(item.get("mode")),
                    _badge(", ".join(item.get("source_user_ids", [])) or "单人", tone="neutral"),
                ],
                muted_detail=f"会话 {item.get('session_id', '—')} · {item.get('occurred_at', '—')}",
            )
            for item in disclosures
        )
        if disclosures
        else _empty_state("暂无显式爆料", "当实体真正跨人直说或半揭示时，这里会留下最近的痕迹。")
    )

    return (
        '<div class="fragment-stack">'
        '<section class="fragment-section">'
        '<div class="section-header"><h2>服务器人格</h2></div>'
        f'<p class="lead">{_text(overview.get("entity_name"))} · '
        f"情绪 {_text(mood.get('tone'))} · 良心 {_text(conscience.get('mode'))}</p>"
        f'<div class="signal-list">{trait_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>人格与世界观</h2></div>'
        f'<div class="kv-grid">{worldview_grid}</div>'
        f'<p class="muted">{_shorten(persona.get("seed_excerpt"), limit=240)}</p>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>关系漂移</h2></div>'
        f'<div class="signal-list">{relationship_cards}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>社会图谱</h2></div>'
        f'<div class="signal-list">{edge_cards}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>良心裁量</h2></div>'
        f'<div class="signal-list">{conscience_cards}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>近期跨人披露</h2></div>'
        f'<div class="signal-list">{disclosure_cards}</div>'
        "</section>"
        "</div>"
    )


def _format_risk_signal(summary: dict[str, Any]) -> str:
    return ", ".join(
        [
            f"违规={summary.get('response_post_audit_total_violation_count', 0)}",
            f"归一化={summary.get('response_normalization_changed_turn_count', 0)}",
        ]
    )


def _format_followup_hold_reasons(item: dict[str, Any]) -> str:
    hold_reasons = list(item.get("hold_reasons") or [])
    if not hold_reasons:
        return "—"
    return ", ".join(_display_text(reason) for reason in hold_reasons[:2])


def _scenario_diff_detail(item: dict[str, Any]) -> str:
    changed_checks = list(item.get("changed_checks") or [])
    if not changed_checks:
        return "检查结果在数值上保持稳定。"
    return _shorten(changed_checks[0].get("description"), limit=110)


def _build_sessions_context(
    *,
    request: Request,
    sessions: list[dict[str, Any]],
    summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    sorted_sessions = sorted(
        sessions,
        key=lambda item: str(item.get("last_event_at") or ""),
        reverse=True,
    )
    if not sorted_sessions:
        return {
            "cards": [],
            "empty_title": "暂无会话",
            "empty_detail": ("创建或处理一个会话，它将出现在此处用于回放和审计。"),
        }

    return {
        "cards": [
            {
                "title": _display_text(session.get("session_id")),
                "detail_url": _detail_url(request, str(session["session_id"])),
                "selected_session_js": _js_string(session["session_id"]),
                "badges": [
                    _badge_data(summary.get("latest_strategy")),
                    _badge_data(summary.get("latest_response_post_audit_status")),
                    _badge_data(summary.get("latest_response_normalization_final_status")),
                ],
                "detail": (
                    f"轮次 {session.get('turn_count', 0)} · "
                    f"事件 {session.get('event_count', 0)} · "
                    f"安全 {_display_text(summary.get('avg_psychological_safety'))}"
                ),
                "muted_detail": (f"最近事件 {_display_timestamp(session.get('last_event_at'))}"),
            }
            for session in sorted_sessions[:LIST_LIMIT]
            for summary in [dict(summaries.get(str(session["session_id"]), {}))]
        ],
        "empty_title": "",
        "empty_detail": "",
    }


async def _render_sessions_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
    sessions, evaluations_payload = await asyncio.gather(
        container.runtime_service.list_sessions(),
        container.evaluation_service.list_session_evaluations(),
    )
    summaries = {str(item["session_id"]): item for item in evaluations_payload.get("sessions", [])}
    return _render_template(
        "console/sessions_fragment.html",
        **_build_sessions_context(
            request=request,
            sessions=sessions,
            summaries=summaries,
        ),
    )


def _build_jobs_context(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    if not jobs:
        return {
            "cards": [],
            "empty_title": "暂无计划任务",
            "empty_detail": ("离线整合和恢复任务将显示在此处。"),
        }
    return {
        "cards": [
            {
                "title": _display_text(job.get("job_id")),
                "badges": [
                    _badge_data(job.get("status")),
                    _badge_data(job.get("job_type")),
                ],
                "detail": (
                    f"会话 {_display_text(job.get('session_id'))} · "
                    f"尝试 {job.get('attempt_count', 0)}/{job.get('max_attempts', 0)}"
                ),
                "muted_detail": (
                    f"工作节点 {_display_text(job.get('last_worker_id'))} · "
                    f"租约 {_display_timestamp(job.get('lease_expires_at'))}"
                ),
            }
            for job in jobs[:LIST_LIMIT]
        ],
        "empty_title": "",
        "empty_detail": "",
    }


async def _render_jobs_fragment(container: RuntimeContainer) -> str:
    jobs_payload = await container.job_service.list_jobs()
    jobs = list(jobs_payload["jobs"])
    return _render_template(
        "console/jobs_fragment.html",
        **_build_jobs_context(jobs),
    )


def _build_archives_context(
    *,
    request: Request,
    archives: list[dict[str, Any]],
) -> dict[str, Any]:
    if not archives:
        return {
            "cards": [],
            "empty_title": "暂无归档会话",
            "empty_detail": ("归档会话将在整合标记为持久化后显示在此处。"),
        }
    return {
        "cards": [
            {
                "title": _display_text(session_id),
                "detail_url": _detail_url(request, session_id),
                "selected_session_js": _js_string(session_id),
                "badges": [
                    _badge_data("archived", tone="good"),
                    _badge_data(archive.get("reason")),
                ],
                "detail": (
                    "快照 "
                    f"{_display_text((archive.get('latest_snapshot') or {}).get('snapshot_id'))}"
                ),
                "muted_detail": (f"归档于 {_display_timestamp(archive.get('archived_at'))}"),
            }
            for archive in archives[:LIST_LIMIT]
            for session_id in [str(archive["session_id"])]
        ],
        "empty_title": "",
        "empty_detail": "",
    }


async def _render_archives_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
    archives_payload = await container.audit_service.list_archived_sessions()
    archives = list(archives_payload["sessions"])
    return _render_template(
        "console/archives_fragment.html",
        **_build_archives_context(request=request, archives=archives),
    )


def _build_evaluations_preference_context(
    preference_report: dict[str, Any],
) -> dict[str, Any]:
    top_strategies = list(preference_report.get("strategies", []))
    reengagement_learning_report = dict(preference_report.get("reengagement_learning") or {})
    top_reengagement_learning = list(reengagement_learning_report.get("strategies", []))
    return {
        "preference_metrics": [
            {"label": "会话", "value": _display_text(preference_report.get("session_count"))},
            {
                "label": "策略",
                "value": _display_text(preference_report.get("strategy_count")),
            },
            {
                "label": "已过滤",
                "value": _display_text(preference_report.get("filtered_session_count")),
            },
            {
                "label": "噪声",
                "value": _display_text(preference_report.get("noisy_session_count")),
            },
        ],
        "strategy_cards": [
            {
                "title": _display_text(item.get("strategy")),
                "badges": [
                    _badge_data(item.get("kept_session_count")),
                    _badge_data(item.get("filtered_session_count"), tone="neutral"),
                ],
                "detail": (
                    f"评分 {_display_text(item.get('avg_denoised_preference_score'))} · "
                    f"质量 {_display_text(item.get('avg_quality_floor_score'))} · "
                    f"时长 {_display_text(item.get('avg_duration_signal'))}"
                ),
            }
            for item in top_strategies[:3]
        ],
        "strategy_empty_title": "暂无策略信号",
        "strategy_empty_detail": ("当非场景会话积累后，去噪的策略偏好信号将在此显示。"),
        "reengagement_metrics": [
            {
                "label": "模式",
                "value": _display_text(reengagement_learning_report.get("learning_mode")),
            },
            {
                "label": "上下文",
                "value": _display_text(reengagement_learning_report.get("context_stratum")),
            },
            {
                "label": "信号",
                "value": _display_text(reengagement_learning_report.get("strategy_count")),
            },
            {
                "label": "匹配",
                "value": _display_text(
                    reengagement_learning_report.get("matching_context_session_count")
                ),
            },
        ],
        "reengagement_cards": [
            {
                "title": _display_text(item.get("strategy_key")),
                "badges": [
                    _badge_data(item.get("contextual_kept_session_count")),
                    _badge_data(item.get("kept_session_count"), tone="neutral"),
                ],
                "detail": (
                    f"学习 {_display_text(item.get('avg_learning_score'))} · "
                    f"上下文 {_display_text(item.get('avg_contextual_learning_score'))} · "
                    f"质量 {_display_text(item.get('avg_quality_floor_score'))}"
                ),
            }
            for item in top_reengagement_learning[:3]
        ],
        "reengagement_empty_title": "暂无重连学习",
        "reengagement_empty_detail": ("当主动会话积累后，矩阵学习信号将在此显示。"),
    }


_EVALUATION_CARD_BADGE_SPECS: tuple[tuple[str, str | None], ...] = (
    ("latest_response_post_audit_status", None),
    ("output_quality_status", "neutral"),
    ("latest_policy_path", None),
    ("latest_strategy_diversity_status", "neutral"),
    ("latest_response_sequence_mode", "neutral"),
    ("latest_time_awareness_mode", "neutral"),
    ("latest_cognitive_load_band", "neutral"),
    ("latest_guidance_mode", "neutral"),
    ("latest_proactive_followup_status", "neutral"),
    ("latest_proactive_aggregate_governance_status", "neutral"),
    ("latest_reengagement_ritual_mode", "neutral"),
    ("latest_runtime_quality_doctor_status", "neutral"),
    ("latest_system3_identity_trajectory_status", "neutral"),
    ("latest_system3_growth_transition_status", "neutral"),
    ("latest_system3_growth_transition_trajectory_status", "neutral"),
    ("latest_system3_user_model_evolution_status", "neutral"),
    ("latest_system3_user_model_trajectory_status", "neutral"),
    ("latest_system3_expectation_calibration_status", "neutral"),
    ("latest_system3_expectation_calibration_trajectory_status", "neutral"),
    ("latest_system3_dependency_governance_status", "neutral"),
    ("latest_system3_dependency_governance_trajectory_status", "neutral"),
    ("latest_system3_autonomy_governance_status", "neutral"),
    ("latest_system3_autonomy_governance_trajectory_status", "neutral"),
    ("latest_system3_boundary_governance_status", "neutral"),
    ("latest_system3_boundary_governance_trajectory_status", "neutral"),
    ("latest_system3_support_governance_status", "neutral"),
    ("latest_system3_support_governance_trajectory_status", "neutral"),
    ("latest_system3_continuity_governance_status", "neutral"),
    ("latest_system3_continuity_governance_trajectory_status", "neutral"),
    ("latest_system3_repair_governance_status", "neutral"),
    ("latest_system3_repair_governance_trajectory_status", "neutral"),
    ("latest_system3_attunement_governance_status", "neutral"),
    ("latest_system3_attunement_governance_trajectory_status", "neutral"),
    ("latest_system3_trust_governance_status", "neutral"),
    ("latest_system3_trust_governance_trajectory_status", "neutral"),
    ("latest_system3_clarity_governance_status", "neutral"),
    ("latest_system3_clarity_governance_trajectory_status", "neutral"),
    ("latest_system3_pacing_governance_status", "neutral"),
    ("latest_system3_pacing_governance_trajectory_status", "neutral"),
    ("latest_system3_commitment_governance_status", "neutral"),
    ("latest_system3_commitment_governance_trajectory_status", "neutral"),
    ("latest_system3_disclosure_governance_status", "neutral"),
    ("latest_system3_disclosure_governance_trajectory_status", "neutral"),
    ("latest_system3_reciprocity_governance_status", "neutral"),
    ("latest_system3_reciprocity_governance_trajectory_status", "neutral"),
    ("latest_system3_pressure_governance_status", "neutral"),
    ("latest_system3_pressure_governance_trajectory_status", "neutral"),
    ("latest_system3_relational_governance_status", "neutral"),
    ("latest_system3_relational_governance_trajectory_status", "neutral"),
    ("latest_system3_safety_governance_status", "neutral"),
    ("latest_system3_safety_governance_trajectory_status", "neutral"),
    ("latest_system3_progress_governance_status", "neutral"),
    ("latest_system3_progress_governance_trajectory_status", "neutral"),
    ("latest_system3_stability_governance_status", "neutral"),
    ("latest_system3_stability_governance_trajectory_status", "neutral"),
    ("latest_system3_version_migration_status", "neutral"),
    ("latest_system3_version_migration_trajectory_status", "neutral"),
    ("latest_system3_strategy_supervision_status", "neutral"),
    ("latest_system3_strategy_supervision_trajectory_status", "neutral"),
    ("latest_system3_moral_reasoning_status", "neutral"),
    ("latest_system3_moral_trajectory_status", "neutral"),
    ("latest_system3_strategy_audit_status", "neutral"),
    ("latest_system3_strategy_audit_trajectory_status", "neutral"),
    ("latest_system3_emotional_debt_status", "neutral"),
    ("latest_system3_emotional_debt_trajectory_status", "neutral"),
    ("latest_boundary_decision", None),
)


_EVALUATION_SORT_INT_FIELDS: tuple[str, ...] = (
    "system3_identity_trajectory_recenter_turn_count",
    "system3_growth_transition_watch_turn_count",
    "system3_growth_transition_trajectory_redirect_turn_count",
    "system3_user_model_evolution_revise_turn_count",
    "system3_user_model_trajectory_recenter_turn_count",
    "system3_version_migration_revise_turn_count",
    "system3_version_migration_trajectory_hold_turn_count",
    "system3_strategy_supervision_revise_turn_count",
    "system3_strategy_supervision_trajectory_tighten_turn_count",
    "system3_expectation_calibration_revise_turn_count",
    "system3_expectation_calibration_trajectory_reset_turn_count",
    "system3_dependency_governance_revise_turn_count",
    "system3_dependency_governance_trajectory_recenter_turn_count",
    "system3_autonomy_governance_revise_turn_count",
    "system3_autonomy_governance_trajectory_recenter_turn_count",
    "system3_boundary_governance_revise_turn_count",
    "system3_boundary_governance_trajectory_recenter_turn_count",
    "system3_support_governance_revise_turn_count",
    "system3_support_governance_trajectory_recenter_turn_count",
    "system3_continuity_governance_revise_turn_count",
    "system3_continuity_governance_trajectory_recenter_turn_count",
    "system3_repair_governance_revise_turn_count",
    "system3_repair_governance_trajectory_recenter_turn_count",
    "system3_attunement_governance_revise_turn_count",
    "system3_attunement_governance_trajectory_recenter_turn_count",
    "system3_trust_governance_revise_turn_count",
    "system3_trust_governance_trajectory_recenter_turn_count",
    "system3_clarity_governance_revise_turn_count",
    "system3_clarity_governance_trajectory_recenter_turn_count",
    "system3_pacing_governance_revise_turn_count",
    "system3_pacing_governance_trajectory_recenter_turn_count",
    "system3_commitment_governance_revise_turn_count",
    "system3_commitment_governance_trajectory_recenter_turn_count",
    "system3_disclosure_governance_revise_turn_count",
    "system3_disclosure_governance_trajectory_recenter_turn_count",
    "system3_reciprocity_governance_revise_turn_count",
    "system3_reciprocity_governance_trajectory_recenter_turn_count",
    "system3_pressure_governance_revise_turn_count",
    "system3_pressure_governance_trajectory_recenter_turn_count",
    "system3_relational_governance_revise_turn_count",
    "system3_relational_governance_trajectory_recenter_turn_count",
    "system3_safety_governance_revise_turn_count",
    "system3_safety_governance_trajectory_recenter_turn_count",
    "system3_moral_reasoning_revise_turn_count",
    "system3_moral_trajectory_recenter_turn_count",
    "system3_strategy_audit_revise_turn_count",
    "system3_strategy_audit_trajectory_corrective_turn_count",
    "system3_emotional_debt_elevated_turn_count",
    "system3_emotional_debt_trajectory_decompression_turn_count",
    "output_quality_issue_count",
    "response_post_audit_total_violation_count",
    "response_normalization_changed_turn_count",
    "policy_gate_guarded_turn_count",
)


def _build_evaluation_card_badges_html(summary: dict[str, Any]) -> str:
    return "".join(
        _badge(summary.get(field), tone=tone) for field, tone in _EVALUATION_CARD_BADGE_SPECS
    )


def _build_evaluation_card_body_html(summary: dict[str, Any]) -> str:
    body_lines = _build_evaluation_body_lines(summary)
    return "".join(
        f'<p class="{"muted" if index else ""}">{line}</p>' for index, line in enumerate(body_lines)
    )


def _render_evaluation_card(summary: dict[str, Any], request: Request) -> str:
    session_id = str(summary["session_id"])
    detail_url = _detail_url(request, session_id)
    body_html = _build_evaluation_card_body_html(summary)
    badges_html = _build_evaluation_card_badges_html(summary)
    return (
        '<article class="list-card">'
        f'<button class="session-pick" '
        f'hx-get="{escape(detail_url)}" '
        'hx-target="#console-session-detail" '
        'hx-swap="innerHTML" '
        f'x-on:click="selectedSession = {_js_string(session_id)}; '
        f'window.relationshipOSConsole?.selectSession({_js_string(session_id)})">'
        f'<div class="list-title">{_text(session_id)}</div>'
        f'<div class="list-meta">{badges_html}</div>'
        f"{body_html}"
        "</button>"
        "</article>"
    )


def _build_evaluation_lifecycle_phase_line(
    summary: dict[str, Any],
    phase: str,
) -> str:
    prefix = f"latest_proactive_lifecycle_{phase}"
    return _item_line(
        summary,
        (f"生命周期 {phase}", f"{prefix}_key"),
        ("模式", f"{prefix}_mode"),
        ("决策", f"{prefix}_decision"),
        ("动作", f"{prefix}_actionability"),
    )


_EVALUATION_BODY_PRIMARY_LINE_SPECS: tuple[tuple[tuple[str, str], ...], ...] = (
    (
        ("质量", "output_quality_status"),
        ("词数", "latest_response_word_count"),
        ("问题", "output_quality_issue_count"),
    ),
    (
        ("进度治理", "latest_system3_progress_governance_status"),
        ("轨迹", "latest_system3_progress_governance_trajectory_status"),
        ("目标", "latest_system3_progress_governance_target"),
    ),
    (
        ("稳定性治理", "latest_system3_stability_governance_status"),
        ("轨迹", "latest_system3_stability_governance_trajectory_status"),
        ("目标", "latest_system3_stability_governance_target"),
    ),
    (
        ("多样性", "latest_strategy_diversity_status"),
        ("指数", "strategy_diversity_index"),
        ("干预", "strategy_diversity_intervention_turn_count"),
    ),
    (
        ("序列", "latest_response_sequence_mode"),
        ("单元", "latest_response_sequence_unit_count"),
        ("连续轮次", "continuous_output_turn_count"),
    ),
    (
        ("协调", "latest_time_awareness_mode"),
        ("负载", "latest_cognitive_load_band"),
        ("主动", "latest_proactive_style"),
    ),
    (
        ("引导", "latest_guidance_mode"),
        ("节奏", "latest_guidance_pacing"),
        ("自主性", "latest_guidance_agency_mode"),
    ),
    (
        ("引导详情", "latest_guidance_ritual_action"),
        ("交接", "latest_guidance_handoff_mode"),
        ("延续", "latest_guidance_carryover_mode"),
    ),
    (
        ("节奏", "latest_cadence_status"),
        ("节拍", "latest_cadence_followup_tempo"),
        ("空间", "latest_cadence_user_space_mode"),
    ),
    (
        ("仪式", "latest_session_ritual_phase"),
        ("收束", "latest_session_ritual_closing_move"),
        ("身体", "latest_session_ritual_somatic_shortcut"),
    ),
    (
        ("身体计划", "latest_somatic_orchestration_mode"),
        ("锚点", "latest_somatic_orchestration_body_anchor"),
        ("跟进", "latest_somatic_orchestration_followup_style"),
    ),
    (
        ("跟进", "latest_proactive_followup_status"),
        ("风格", "latest_proactive_followup_style"),
        ("延迟", "latest_proactive_followup_after_seconds"),
    ),
    (
        ("跟进调度", "latest_proactive_scheduling_mode"),
        (
            "冷却",
            "latest_proactive_scheduling_min_seconds_since_last_outbound",
        ),
        (
            "额外",
            "latest_proactive_scheduling_first_touch_extra_delay_seconds",
        ),
    ),
    (
        ("跟进编排", "latest_proactive_orchestration_key"),
        (
            "二次触达",
            "latest_proactive_orchestration_second_touch_delivery_mode",
        ),
        ("收束", "latest_proactive_orchestration_close_loop_stage"),
    ),
    (
        ("跟进执行", "latest_proactive_actuation_key"),
        (
            "二次触达",
            "latest_proactive_actuation_second_touch_opening_move",
        ),
        ("收束", "latest_proactive_actuation_final_touch_closing_move"),
    ),
    (
        ("执行桥接", "latest_proactive_actuation_second_touch_bridge_move"),
        (
            "用户空间",
            "latest_proactive_actuation_second_touch_user_space_signal",
        ),
        ("身体", "latest_proactive_actuation_somatic_mode"),
    ),
    (
        ("跟进推进", "latest_proactive_progression_key"),
        ("二次触达", "latest_proactive_progression_second_touch_action"),
        ("收束", "latest_proactive_progression_final_touch_action"),
    ),
    (
        ("跟进控制器", "latest_proactive_stage_controller_key"),
        ("目标", "latest_proactive_stage_controller_target_stage_label"),
        (
            "延迟",
            "latest_proactive_stage_controller_additional_delay_seconds",
        ),
    ),
    (
        ("跟进线控制器", "latest_proactive_line_controller_key"),
        ("状态", "latest_proactive_line_controller_line_state"),
        (
            "延迟",
            "latest_proactive_line_controller_additional_delay_seconds",
        ),
    ),
    (
        ("跟进刷新", "latest_proactive_stage_refresh_key"),
        ("窗口", "latest_proactive_stage_refresh_window_status"),
        ("已变更", "latest_proactive_stage_refresh_changed"),
    ),
    (
        ("跟进重规划", "latest_proactive_stage_replan_key"),
        ("策略", "latest_proactive_stage_replan_strategy_key"),
        ("已变更", "latest_proactive_stage_replan_changed"),
    ),
    (
        ("跟进反馈", "latest_proactive_dispatch_feedback_key"),
        ("策略", "latest_proactive_dispatch_feedback_strategy_key"),
        ("已变更", "latest_proactive_dispatch_feedback_changed"),
    ),
    (
        ("跟进门控", "latest_proactive_dispatch_gate_key"),
        ("决策", "latest_proactive_dispatch_gate_decision"),
        ("延迟", "proactive_dispatch_gate_deferred_turn_count"),
    ),
    (
        ("调度信封", "latest_proactive_dispatch_envelope_key"),
        ("决策", "latest_proactive_dispatch_envelope_decision"),
        ("策略", "latest_proactive_dispatch_envelope_strategy_key"),
        ("来源", "latest_proactive_dispatch_envelope_source_count"),
    ),
    (
        ("阶段状态", "latest_proactive_stage_state_key"),
        ("模式", "latest_proactive_stage_state_mode"),
        ("队列", "latest_proactive_stage_state_queue_status"),
        ("来源", "latest_proactive_stage_state_source"),
    ),
    (
        ("阶段转换", "latest_proactive_stage_transition_key"),
        ("模式", "latest_proactive_stage_transition_mode"),
        ("队列", "latest_proactive_stage_transition_queue_hint"),
        ("来源", "latest_proactive_stage_transition_source"),
    ),
    (
        ("阶段状态机", "latest_proactive_stage_machine_key"),
        ("模式", "latest_proactive_stage_machine_mode"),
        ("生命周期", "latest_proactive_stage_machine_lifecycle"),
        ("动作", "latest_proactive_stage_machine_actionability"),
    ),
    (
        ("线状态", "latest_proactive_line_state_key"),
        ("模式", "latest_proactive_line_state_mode"),
        ("生命周期", "latest_proactive_line_state_lifecycle"),
        ("动作", "latest_proactive_line_state_actionability"),
    ),
    (
        ("线转换", "latest_proactive_line_transition_key"),
        ("模式", "latest_proactive_line_transition_mode"),
        ("退出", "latest_proactive_line_transition_exit_mode"),
    ),
    (
        ("线状态机", "latest_proactive_line_machine_key"),
        ("模式", "latest_proactive_line_machine_mode"),
        ("生命周期", "latest_proactive_line_machine_lifecycle"),
        ("动作", "latest_proactive_line_machine_actionability"),
    ),
    (
        ("生命周期状态", "latest_proactive_lifecycle_state_key"),
        ("模式", "latest_proactive_lifecycle_state_mode"),
        ("生命周期", "latest_proactive_lifecycle_state_lifecycle"),
        ("动作", "latest_proactive_lifecycle_state_actionability"),
    ),
    (
        ("生命周期转换", "latest_proactive_lifecycle_transition_key"),
        ("模式", "latest_proactive_lifecycle_transition_mode"),
        ("退出", "latest_proactive_lifecycle_transition_exit_mode"),
    ),
    (
        ("生命周期状态机", "latest_proactive_lifecycle_machine_key"),
        ("模式", "latest_proactive_lifecycle_machine_mode"),
        ("生命周期", "latest_proactive_lifecycle_machine_lifecycle"),
        ("动作", "latest_proactive_lifecycle_machine_actionability"),
    ),
    (
        ("生命周期控制器", "latest_proactive_lifecycle_controller_key"),
        ("状态", "latest_proactive_lifecycle_controller_state"),
        ("决策", "latest_proactive_lifecycle_controller_decision"),
        ("延迟", "latest_proactive_lifecycle_controller_delay_seconds"),
    ),
    (
        ("生命周期信封", "latest_proactive_lifecycle_envelope_key"),
        ("模式", "latest_proactive_lifecycle_envelope_mode"),
        ("决策", "latest_proactive_lifecycle_envelope_decision"),
        ("动作", "latest_proactive_lifecycle_envelope_actionability"),
    ),
    (
        ("生命周期调度器", "latest_proactive_lifecycle_scheduler_key"),
        ("模式", "latest_proactive_lifecycle_scheduler_mode"),
        ("决策", "latest_proactive_lifecycle_scheduler_decision"),
        ("队列", "latest_proactive_lifecycle_scheduler_queue_status"),
    ),
    (
        ("生命周期窗口", "latest_proactive_lifecycle_window_key"),
        ("模式", "latest_proactive_lifecycle_window_mode"),
        ("决策", "latest_proactive_lifecycle_window_decision"),
        ("队列", "latest_proactive_lifecycle_window_queue_status"),
    ),
    (
        ("生命周期队列", "latest_proactive_lifecycle_queue_key"),
        ("模式", "latest_proactive_lifecycle_queue_mode"),
        ("决策", "latest_proactive_lifecycle_queue_decision"),
        ("队列", "latest_proactive_lifecycle_queue_status"),
    ),
    (
        ("生命周期调度", "latest_proactive_lifecycle_dispatch_key"),
        ("模式", "latest_proactive_lifecycle_dispatch_mode"),
        ("决策", "latest_proactive_lifecycle_dispatch_decision"),
        ("动作", "latest_proactive_lifecycle_dispatch_actionability"),
    ),
    (
        ("生命周期结果", "latest_proactive_lifecycle_outcome_key"),
        ("模式", "latest_proactive_lifecycle_outcome_mode"),
        ("决策", "latest_proactive_lifecycle_outcome_decision"),
        ("动作", "latest_proactive_lifecycle_outcome_actionability"),
    ),
    (
        ("生命周期解析", "latest_proactive_lifecycle_resolution_key"),
        ("模式", "latest_proactive_lifecycle_resolution_mode"),
        ("决策", "latest_proactive_lifecycle_resolution_decision"),
        ("动作", "latest_proactive_lifecycle_resolution_actionability"),
    ),
)


_EVALUATION_BODY_TRAILING_LINE_SPECS: tuple[tuple[tuple[str, str], ...], ...] = (
    (
        ("跟进节奏", "latest_proactive_cadence_key"),
        ("阶段", "latest_proactive_cadence_stage_count"),
        ("计划", "proactive_cadence_plan_count"),
        ("已调度", "proactive_scheduling_deferred_turn_count"),
    ),
    (
        ("聚合治理", "latest_proactive_aggregate_governance_status"),
        ("主域", "latest_proactive_aggregate_governance_primary_domain"),
        ("域数", "latest_proactive_aggregate_governance_domain_count"),
        ("摘要", "latest_proactive_aggregate_governance_summary"),
    ),
    (
        ("聚合控制器", "latest_proactive_aggregate_controller_key"),
        ("决策", "latest_proactive_aggregate_controller_decision"),
        ("阶段延迟", "latest_proactive_aggregate_controller_stage_delay_seconds"),
    ),
    (
        ("编排控制器", "latest_proactive_orchestration_controller_key"),
        ("决策", "latest_proactive_orchestration_controller_decision"),
        ("来源", "latest_proactive_orchestration_controller_primary_source"),
        (
            "阶段延迟",
            "latest_proactive_orchestration_controller_stage_delay_seconds",
        ),
    ),
    (
        ("跟进护栏", "latest_proactive_guardrail_key"),
        ("最大", "latest_proactive_guardrail_max_dispatch_count"),
        ("硬停止", "latest_proactive_guardrail_hard_stop_count"),
    ),
    (
        ("重连矩阵", "latest_reengagement_matrix_key"),
        ("已选", "latest_reengagement_matrix_selected_strategy"),
        ("学习", "latest_reengagement_matrix_learning_mode"),
        ("备选", "latest_reengagement_matrix_top_alternative"),
    ),
    (
        ("重连", "latest_reengagement_ritual_mode"),
        ("策略", "latest_reengagement_strategy_key"),
        ("压力", "latest_reengagement_pressure_mode"),
    ),
    (
        ("重连详情", "latest_reengagement_delivery_mode"),
        ("自主", "latest_reengagement_autonomy_signal"),
        ("上下文", "latest_reengagement_matrix_learning_context_stratum"),
        ("已阻断", "latest_reengagement_matrix_blocked_count"),
        ("已规划", "reengagement_plan_count"),
    ),
    (
        ("调度", "latest_proactive_followup_dispatch_status"),
        ("来源", "latest_proactive_followup_dispatch_source"),
        ("计数", "proactive_followup_dispatch_count"),
        ("阶段", "latest_proactive_followup_dispatch_stage_label"),
    ),
    (
        (
            "调度推进",
            "latest_proactive_followup_dispatch_progression_action",
        ),
        (
            "已推进",
            "latest_proactive_followup_dispatch_progression_advanced",
        ),
        (
            "自动推进",
            "proactive_followup_dispatch_progression_advanced_count",
        ),
    ),
    (
        ("质量医生", "latest_runtime_quality_doctor_status"),
        ("问题", "latest_runtime_quality_doctor_issue_count"),
        ("报告", "runtime_quality_doctor_report_count"),
    ),
    (
        ("system3", "latest_system3_growth_stage"),
        ("身份", "latest_system3_identity_trajectory_status"),
        ("转换", "latest_system3_growth_transition_status"),
        ("模型", "latest_system3_user_model_evolution_status"),
        ("期望", "latest_system3_expectation_calibration_status"),
        ("债务", "latest_system3_emotional_debt_status"),
    ),
    (
        ("依赖", "latest_system3_dependency_governance_status"),
        ("信任", "latest_system3_trust_governance_status"),
        ("清晰度", "latest_system3_clarity_governance_status"),
        ("迁移", "latest_system3_version_migration_status"),
    ),
    (
        ("节奏", "latest_system3_pacing_governance_status"),
        ("调谐", "latest_system3_attunement_governance_status"),
        ("承诺", "latest_system3_commitment_governance_status"),
        ("披露", "latest_system3_disclosure_governance_status"),
    ),
    (
        ("互惠", "latest_system3_reciprocity_governance_status"),
        ("压力", "latest_system3_pressure_governance_status"),
        ("关系", "latest_system3_relational_governance_status"),
        ("安全", "latest_system3_safety_governance_status"),
        ("监督", "latest_system3_strategy_supervision_status"),
    ),
    (
        ("道德", "latest_system3_moral_reasoning_status"),
        ("观察", "latest_system3_growth_transition_status"),
        (
            "轨迹",
            "latest_system3_growth_transition_trajectory_status",
        ),
    ),
)


def _build_evaluation_body_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        (
            f"{escape(_format_risk_signal(summary))} · "
            f"记忆召回={summary.get('memory_recall_turn_count', 0)} · "
            f"受保护轮次={summary.get('policy_gate_guarded_turn_count', 0)}"
        ),
    ]
    lines.extend(_item_line(summary, *pairs) for pairs in _EVALUATION_BODY_PRIMARY_LINE_SPECS)
    lines.extend(
        _build_evaluation_lifecycle_phase_line(summary, phase)
        for phase in _PROACTIVE_LIFECYCLE_PHASES
    )
    lines.extend(_item_line(summary, *pairs) for pairs in _EVALUATION_BODY_TRAILING_LINE_SPECS)
    lines.append(
        f"安全 {_display_text(summary.get('avg_psychological_safety'))} · "
        f"固定 {summary.get('latest_memory_pinned_count', 0)} · "
        f"淘汰 {summary.get('latest_memory_evicted_count', 0)}"
    )
    return lines


def _evaluation_sort_key(item: dict[str, Any]) -> tuple[object, ...]:
    return (
        *(int(item.get(field, 0)) for field in _EVALUATION_SORT_INT_FIELDS),
        float(item.get("avg_psychological_safety") or 0.0),
    )


async def _render_evaluations_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
    evaluations_payload, preference_report = await asyncio.gather(
        container.evaluation_service.list_session_evaluations(),
        container.evaluation_service.build_strategy_preference_report(),
    )
    evaluations = list(evaluations_payload["sessions"])
    evaluations.sort(key=_evaluation_sort_key, reverse=True)
    if not evaluations:
        return _empty_state(
            "暂无评测",
            ("当会话积累轮次后，评测管线将浮出风险和记忆信号。"),
        )
    preference_context = _build_evaluations_preference_context(preference_report)
    evaluation_cards_html = "".join(
        _render_evaluation_card(summary, request) for summary in evaluations[:LIST_LIMIT]
    )
    return _render_template(
        "console/evaluations_fragment.html",
        evaluation_cards_html=evaluation_cards_html,
        **preference_context,
    )


async def _load_scenarios_fragment_context(
    container: RuntimeContainer,
) -> dict[str, Any]:
    (
        runs_payload,
        trends_payload,
        horizon_report,
        multiweek_report,
        sustained_drift_report,
        longitudinal_report,
        ship_readiness,
        baseline_governance_report,
        migration_readiness_report,
        hardening_checklist,
        release_dossier,
        launch_signoff,
        safety_audit_report,
        redteam_report,
        misalignment_report,
    ) = await asyncio.gather(
        container.scenario_evaluation_service.list_runs(limit=LIST_LIMIT),
        container.scenario_evaluation_service.list_trends(limit_per_scenario=3),
        container.scenario_evaluation_service.build_horizon_report(),
        container.scenario_evaluation_service.build_multiweek_report(),
        container.scenario_evaluation_service.build_sustained_drift_report(),
        container.scenario_evaluation_service.build_longitudinal_report(window=8),
        container.scenario_evaluation_service.build_ship_readiness(window=6),
        container.scenario_evaluation_service.build_baseline_governance_report(window=6),
        container.scenario_evaluation_service.build_migration_readiness_report(),
        container.scenario_evaluation_service.build_hardening_checklist(window=6),
        container.scenario_evaluation_service.build_release_dossier(window=6),
        container.scenario_evaluation_service.build_launch_signoff_report(window=6),
        container.scenario_evaluation_service.build_safety_audit_report(window=6),
        container.scenario_evaluation_service.build_redteam_report(window=6),
        container.scenario_evaluation_service.build_misalignment_report(window=6),
    )
    runs = list(runs_payload["runs"])
    trends = sorted(
        list(trends_payload["scenarios"]),
        key=lambda item: (
            item.get("latest_status") == "review",
            int(item.get("total_runs") or 0),
            str(item.get("latest_started_at") or ""),
        ),
        reverse=True,
    )
    visible_trends = [trend for trend in trends if int(trend.get("total_runs") or 0) > 0] or trends[
        :LIST_LIMIT
    ]
    release_gate = dict(ship_readiness.get("release_gate") or {})
    report = dict(release_gate.get("report") or {})
    comparison: dict[str, Any] | None = None
    if len(runs) >= 2:
        comparison = await container.scenario_evaluation_service.compare_runs(
            baseline_run_id=str(runs[1]["run_id"]),
            candidate_run_id=str(runs[0]["run_id"]),
        )
    return {
        "runs": runs,
        "visible_trends": visible_trends,
        "horizon_report": horizon_report,
        "horizon_summary": dict(horizon_report.get("summary") or {}),
        "multiweek_report": multiweek_report,
        "multiweek_summary": dict(multiweek_report.get("summary") or {}),
        "sustained_drift_report": sustained_drift_report,
        "sustained_drift_summary": dict(sustained_drift_report.get("summary") or {}),
        "longitudinal_report": longitudinal_report,
        "longitudinal_summary": dict(longitudinal_report.get("summary") or {}),
        "ship_readiness": ship_readiness,
        "readiness_summary": dict(ship_readiness.get("summary") or {}),
        "baseline_governance_report": baseline_governance_report,
        "baseline_governance_summary": dict(baseline_governance_report.get("summary") or {}),
        "migration_readiness_report": migration_readiness_report,
        "migration_readiness_summary": dict(migration_readiness_report.get("summary") or {}),
        "hardening_checklist": hardening_checklist,
        "hardening_summary": dict(hardening_checklist.get("summary") or {}),
        "release_dossier": release_dossier,
        "release_dossier_summary": dict(release_dossier.get("summary") or {}),
        "launch_signoff": launch_signoff,
        "launch_signoff_summary": dict(launch_signoff.get("summary") or {}),
        "safety_audit_report": safety_audit_report,
        "safety_audit_summary": dict(safety_audit_report.get("summary") or {}),
        "redteam_report": redteam_report,
        "redteam_summary": dict(redteam_report.get("summary") or {}),
        "misalignment_report": misalignment_report,
        "taxonomy_items": list(misalignment_report.get("taxonomies", [])),
        "incident_items": list(misalignment_report.get("incidents", [])),
        "release_gate": release_gate,
        "report": report,
        "watchlist": list(report.get("watchlist", [])),
        "baseline": report.get("baseline"),
        "gate_focus_areas": list(release_gate.get("focus_areas", [])),
        "coverage": dict(report.get("coverage") or {}),
        "comparison": comparison,
    }


def _build_scenarios_temporal_sections(context: dict[str, Any]) -> list[str]:
    longitudinal_report = context["longitudinal_report"]
    longitudinal_summary = context["longitudinal_summary"]
    horizon_report = context["horizon_report"]
    horizon_summary = context["horizon_summary"]
    multiweek_report = context["multiweek_report"]
    multiweek_summary = context["multiweek_summary"]
    sustained_drift_report = context["sustained_drift_report"]
    sustained_drift_summary = context["sustained_drift_summary"]
    longitudinal_cards = _build_scenarios_focus_cards(
        list(longitudinal_report.get("focus_areas", [])),
        status=longitudinal_report.get("status"),
        empty_title="纵向报告平稳",
        empty_detail="近期和先前队列目前未显示额外漂移。",
    )
    horizon_cards = _build_scenarios_focus_cards(
        list(horizon_report.get("focus_areas", [])),
        status=horizon_report.get("status"),
        empty_title="时间维度报告平稳",
        empty_detail="短期、中期和长期窗口未显示额外漂移。",
    )
    multiweek_cards = _build_scenarios_focus_cards(
        list(multiweek_report.get("focus_areas", [])),
        status=multiweek_report.get("status"),
        empty_title="多周报告平稳",
        empty_detail="近期周桶未显示额外漂移。",
    )
    sustained_drift_cards = _build_scenarios_focus_cards(
        list(sustained_drift_report.get("focus_areas", [])),
        status=sustained_drift_report.get("status"),
        empty_title="持续漂移平稳",
        empty_detail="近期周桶未显示持续恶化趋势。",
    )
    return [
        _build_scenarios_section(
            "时间维度报告",
            grid_items=[
                ("状态", horizon_report.get("status")),
                ("短期运行", horizon_summary.get("short_run_count")),
                ("中期运行", horizon_summary.get("medium_run_count")),
                ("长期运行", horizon_summary.get("long_run_count")),
                ("短/中期通过", horizon_summary.get("short_vs_medium_pass_rate_delta")),
                ("短/长期通过", horizon_summary.get("short_vs_long_pass_rate_delta")),
                ("最新质量", horizon_summary.get("latest_output_quality_status")),
                ("最新边界", horizon_summary.get("latest_redteam_boundary_decision")),
            ],
            cards_html=horizon_cards,
        ),
        _build_scenarios_section(
            "多周报告",
            grid_items=[
                ("状态", multiweek_report.get("status")),
                ("桶天数", multiweek_summary.get("bucket_days")),
                ("桶数", multiweek_summary.get("bucket_count")),
                ("最新桶", multiweek_summary.get("latest_bucket_label")),
                ("先前桶", multiweek_summary.get("prior_bucket_label")),
                ("通过率变化", multiweek_summary.get("overall_pass_rate_delta")),
                ("质量观察变化", multiweek_summary.get("quality_watch_delta")),
                ("边界守护变化", multiweek_summary.get("redteam_boundary_guard_delta")),
            ],
            cards_html=multiweek_cards,
        ),
        _build_scenarios_section(
            "持续漂移",
            grid_items=[
                ("状态", sustained_drift_report.get("status")),
                ("桶数", sustained_drift_summary.get("bucket_count")),
                ("最小连续", sustained_drift_summary.get("min_streak")),
                ("通过率下降", sustained_drift_summary.get("pass_rate_decline_streak")),
                ("质量增长", sustained_drift_summary.get("quality_watch_growth_streak")),
                (
                    "红队下降",
                    sustained_drift_summary.get("redteam_pass_rate_decline_streak"),
                ),
                ("守护下降", sustained_drift_summary.get("boundary_guard_decline_streak")),
                ("最新桶", sustained_drift_summary.get("latest_bucket_label")),
            ],
            cards_html=sustained_drift_cards,
        ),
        _build_scenarios_section(
            "纵向报告",
            grid_items=[
                ("状态", longitudinal_report.get("status")),
                ("近期运行", longitudinal_summary.get("recent_run_count")),
                ("先前运行", longitudinal_summary.get("prior_run_count")),
                ("通过率变化", longitudinal_summary.get("overall_pass_rate_delta")),
                ("质量观察变化", longitudinal_summary.get("quality_watch_delta")),
                ("红队通过率变化", longitudinal_summary.get("redteam_pass_rate_delta")),
                ("边界守护变化", longitudinal_summary.get("redteam_boundary_guard_delta")),
            ],
            cards_html=longitudinal_cards,
        ),
    ]


def _build_scenarios_release_cards(context: dict[str, Any]) -> dict[str, Any]:
    release_dossier = context["release_dossier"]
    hardening_checklist = context["hardening_checklist"]
    hardening_summary = context["hardening_summary"]
    safety_audit_report = context["safety_audit_report"]
    ship_readiness = context["ship_readiness"]
    migration_readiness_report = context["migration_readiness_report"]
    baseline_governance_report = context["baseline_governance_report"]

    hotspot_label = None
    if hardening_summary.get("hotspot_taxonomy_type"):
        hotspot_label = (
            f"{hardening_summary.get('hotspot_taxonomy_type')} "
            f"({hardening_summary.get('hotspot_taxonomy_count')})"
        )
    if list(migration_readiness_report.get("actions", [])):
        migration_readiness_cards = _build_scenarios_action_cards(
            list(migration_readiness_report.get("actions", [])),
            status=migration_readiness_report.get("status"),
            empty_title="迁移就绪状态良好",
            empty_detail=("近期投影器回放样本在当前注册表中一致。"),
        )
    else:
        migration_readiness_cards = _build_scenarios_focus_cards(
            list(migration_readiness_report.get("focus_areas", [])),
            status=migration_readiness_report.get("status"),
            empty_title="迁移就绪状态良好",
            empty_detail=("近期投影器回放样本在当前注册表中一致。"),
        )
    return {
        "release_dossier_cards": _build_scenarios_action_cards(
            list(release_dossier.get("actions", [])),
            status=release_dossier.get("status"),
            empty_title="发版档案状态良好",
            empty_detail="当前候选没有待处理的最终发版档案操作。",
        ),
        "hardening_cards": _build_scenarios_action_cards(
            list(hardening_checklist.get("actions", [])),
            status=hardening_checklist.get("status"),
            empty_title="加固检查单状态良好",
            empty_detail="目前没有额外的加固操作处于活跃状态。",
        ),
        "hotspot_label": hotspot_label,
        "safety_audit_cards": _build_scenarios_action_cards(
            list(safety_audit_report.get("actions", [])),
            status=safety_audit_report.get("status"),
            empty_title="安全审计状态良好",
            empty_detail="目前没有即时的边界或回放安全操作处于活跃状态。",
            limit=3,
        ),
        "ship_readiness_cards": _build_scenarios_action_cards(
            list(ship_readiness.get("actions", [])),
            status=ship_readiness.get("status"),
            empty_title="上线检查单状态良好",
            empty_detail="目前没有待处理的上线就绪操作。",
        ),
        "migration_readiness_cards": migration_readiness_cards,
        "baseline_governance_cards": _build_scenarios_action_cards(
            list(baseline_governance_report.get("actions", [])),
            status=baseline_governance_report.get("status"),
            empty_title="基线治理健康",
            empty_detail="固定的基线仍可用于发版比较。",
        ),
    }


def _build_scenarios_release_primary_sections(
    context: dict[str, Any],
    cards: dict[str, Any],
) -> list[str]:
    release_dossier = context["release_dossier"]
    release_dossier_summary = context["release_dossier_summary"]
    launch_signoff = context["launch_signoff"]
    launch_signoff_summary = context["launch_signoff_summary"]
    hardening_checklist = context["hardening_checklist"]
    hardening_summary = context["hardening_summary"]
    safety_audit_report = context["safety_audit_report"]
    safety_audit_summary = context["safety_audit_summary"]
    redteam_report = context["redteam_report"]
    redteam_summary = context["redteam_summary"]
    return [
        _build_launch_signoff_section_html(
            launch_signoff,
            launch_signoff_summary,
        ),
        _build_scenarios_section(
            "发版档案",
            grid_items=[
                ("状态", release_dossier.get("status")),
                ("发版过线", release_dossier_summary.get("release_gate_status")),
                ("上线就绪", release_dossier_summary.get("ship_readiness_status")),
                ("加固", release_dossier_summary.get("hardening_checklist_status")),
                ("安全审计", release_dossier_summary.get("safety_audit_status")),
                ("红队", release_dossier_summary.get("redteam_report_status")),
                ("基线治理", release_dossier_summary.get("baseline_governance_status")),
                ("迁移", release_dossier_summary.get("migration_readiness_status")),
                ("纵向", release_dossier_summary.get("longitudinal_report_status")),
            ],
            cards_html=cards["release_dossier_cards"],
        ),
        _build_scenarios_section(
            "加固检查单",
            grid_items=[
                ("状态", hardening_checklist.get("status")),
                ("上线就绪", hardening_summary.get("ship_readiness_status")),
                ("关键分类", hardening_summary.get("critical_taxonomy_count")),
                ("红队关键", hardening_summary.get("redteam_critical_incident_count")),
                ("质量分类", hardening_summary.get("quality_taxonomy_count")),
                ("System3 分类", hardening_summary.get("system3_taxonomy_count")),
                ("热点", cards["hotspot_label"]),
            ],
            cards_html=cards["hardening_cards"],
        ),
        _build_scenarios_section(
            "安全审计",
            grid_items=[
                ("状态", safety_audit_report.get("status")),
                ("场景结果", safety_audit_summary.get("scenario_result_count")),
                ("红队结果", safety_audit_summary.get("redteam_result_count")),
                ("关键边界", safety_audit_summary.get("critical_boundary_incident_count")),
                ("回放漂移", safety_audit_summary.get("audit_inconsistent_count")),
                ("边界守护率", safety_audit_summary.get("redteam_boundary_guard_rate")),
                (
                    "审后违规",
                    safety_audit_summary.get("post_audit_violation_result_count"),
                ),
            ],
            cards_html=cards["safety_audit_cards"],
        ),
        _build_redteam_section_html(
            redteam_report,
            redteam_summary,
        ),
    ]


def _build_scenarios_release_secondary_sections(
    context: dict[str, Any],
    cards: dict[str, Any],
) -> list[str]:
    ship_readiness = context["ship_readiness"]
    readiness_summary = context["readiness_summary"]
    migration_readiness_report = context["migration_readiness_report"]
    migration_readiness_summary = context["migration_readiness_summary"]
    baseline_governance_report = context["baseline_governance_report"]
    baseline_governance_summary = context["baseline_governance_summary"]
    misalignment_report = context["misalignment_report"]
    taxonomy_items = context["taxonomy_items"]
    incident_items = context["incident_items"]
    release_gate = context["release_gate"]
    gate_focus_areas = context["gate_focus_areas"]
    coverage = context["coverage"]
    baseline = context["baseline"]
    report = context["report"]
    watchlist = context["watchlist"]
    comparison = context["comparison"]
    return [
        _build_scenarios_section(
            "上线就绪",
            grid_items=[
                ("状态", ship_readiness.get("status")),
                ("发版过线", readiness_summary.get("release_gate_status")),
                ("工作节点", readiness_summary.get("worker_id")),
                ("轮询器", readiness_summary.get("poller_running")),
                ("待处理任务", readiness_summary.get("pending_job_count")),
                ("活跃任务", readiness_summary.get("active_job_count")),
                ("可重试失败", readiness_summary.get("retryable_failed_job_count")),
                ("过期占用", readiness_summary.get("expired_claim_job_count")),
            ],
            cards_html=cards["ship_readiness_cards"],
        ),
        _build_scenarios_section(
            "迁移就绪",
            grid_items=[
                ("状态", migration_readiness_report.get("status")),
                ("投影器", migration_readiness_summary.get("registered_projector_count")),
                ("样本来源", migration_readiness_summary.get("sample_source")),
                ("已采样流", migration_readiness_summary.get("sampled_stream_count")),
                (
                    "主样本",
                    migration_readiness_summary.get("primary_sample_stream_count"),
                ),
                (
                    "备选样本",
                    migration_readiness_summary.get("fallback_sample_stream_count"),
                ),
                (
                    "已检查投影",
                    migration_readiness_summary.get("checked_projection_count"),
                ),
                ("回放漂移", migration_readiness_summary.get("inconsistent_projection_count")),
            ],
            cards_html=cards["migration_readiness_cards"],
        ),
        _build_scenarios_section(
            "基线治理",
            grid_items=[
                ("状态", baseline_governance_report.get("status")),
                ("标签", baseline_governance_summary.get("baseline_label")),
                ("基线运行", baseline_governance_summary.get("baseline_run_id")),
                ("更新运行", baseline_governance_summary.get("newer_run_count")),
                ("存续天数", baseline_governance_summary.get("baseline_age_days")),
                ("总体变化", baseline_governance_summary.get("overall_delta")),
                ("已变更场景", baseline_governance_summary.get("changed_scenario_count")),
                ("备注", baseline_governance_summary.get("baseline_note_present")),
            ],
            cards_html=cards["baseline_governance_cards"],
        ),
        _build_release_gate_section_html(
            release_gate,
            gate_focus_areas,
            coverage,
        ),
        _build_baseline_track_section_html(baseline),
        _build_stability_report_section_html(
            report,
            watchlist,
        ),
        _build_regression_watch_section_html(comparison),
        _build_misalignment_section_html(
            misalignment_report,
            taxonomy_items,
            incident_items,
        ),
    ]


def _build_scenarios_release_sections(context: dict[str, Any]) -> list[str]:
    cards = _build_scenarios_release_cards(context)
    return [
        *_build_scenarios_release_primary_sections(context, cards),
        *_build_scenarios_release_secondary_sections(context, cards),
    ]


def _build_scenarios_trend_sections(
    context: dict[str, Any],
    request: Request,
) -> list[str]:
    return [
        _build_scenario_trends_section_html(context["visible_trends"]),
        _build_recent_runs_section_html(
            runs=context["runs"],
            request=request,
        ),
    ]


async def _render_scenarios_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
    context = await _load_scenarios_fragment_context(container)
    sections = [
        *_build_scenarios_release_sections(context),
        *_build_scenarios_temporal_sections(context),
        *_build_scenarios_trend_sections(context, request),
    ]
    return f'<div class="fragment-stack">{"".join(sections)}</div>'


def _projector_buttons_html(
    *,
    request: Request,
    session_id: str,
    projectors: list[dict[str, str]],
    selected_name: str,
    selected_version: str,
) -> str:
    buttons = []
    for projector in projectors:
        name = str(projector.get("name", "")).strip()
        version = str(projector.get("version", "")).strip()
        if not name or not version:
            continue
        detail_url = _detail_url(
            request,
            session_id,
            projector_name=name,
            version=version,
        )
        active_class = (
            "tab active" if (name, version) == (selected_name, selected_version) else "tab"
        )
        buttons.append(
            f'<button class="{active_class}" '
            f'hx-get="{escape(detail_url)}" '
            'hx-target="#console-session-detail" '
            'hx-swap="innerHTML" '
            f'x-on:click="window.relationshipOSConsole?.selectProjector('
            f'{_js_string(name)}, {_js_string(version)})">'
            f"{_text(name)}"
            f'<span class="tab-version">{_text(version)}</span>'
            "</button>"
        )
    return "".join(buttons)


def _recent_trace_html(
    *,
    container: RuntimeContainer,
    events: list[Any],
) -> str:
    trace_events = [
        container.stream_service.serialize_event(event)
        for event in events
        if is_trace_event_type(event.event_type)
    ]
    if not trace_events:
        return _empty_state(
            "追踪为空",
            "此会话尚未发出运行时追踪事件。",
        )
    return "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(event.get("event_type"))}</div>'
            f'<div class="trace-meta">v{event.get("version")} · '
            f"{_timestamp(event.get('occurred_at'))}</div>"
            f"<pre>{escape(str(event.get('payload', {})))}</pre>"
            "</li>"
        )
        for event in trace_events[-8:]
    )


def _event_ledger_html(
    *,
    container: RuntimeContainer,
    events: list[Any],
) -> str:
    if not events:
        return _empty_state(
            "账本为空",
            "此会话尚未写入任何事件。",
        )

    serialized = [container.stream_service.serialize_event(event) for event in events]
    rows: list[str] = []
    for event in serialized[-10:]:
        payload = event.get("payload", {})
        summary = payload
        if event.get("event_type") == "system.proactive_lifecycle_snapshot.updated":
            phase_count = len(list((payload or {}).get("phases", [])))
            summary = {
                "schema_version": (payload or {}).get("schema_version"),
                "emission_id": (payload or {}).get("emission_id"),
                "current_stage_label": (payload or {}).get("current_stage_label"),
                "current_stage_index": (payload or {}).get("current_stage_index"),
                "stage_count": (payload or {}).get("stage_count"),
                "message_event_count": (payload or {}).get("message_event_count"),
                "phase_count": phase_count,
            }
        rows.append(
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(event.get("event_type"))}</div>'
            f'<div class="trace-meta">#{event.get("version")} · '
            f"{_timestamp(event.get('occurred_at'))}</div>"
            f"<p>{_shorten(summary, limit=200)}</p>"
            "</li>"
        )
    return "".join(rows)


async def _render_session_detail_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
    session_id: str | None,
    projector_name: str,
    projector_version: str,
) -> str:
    if not session_id:
        return _empty_state(
            "选择一个会话",
            "从右侧栏选择一个会话以检查追踪、记忆和审计状态。",
        )

    events = await container.stream_service.read_stream(stream_id=session_id)
    if not events:
        return _empty_state(
            "会话未找到",
            "所选会话不存在于当前事件存储中。",
        )
    try:
        ensure_snapshot_only_lifecycle_events(events)
    except LegacyLifecycleStreamUnsupportedError:
        return _empty_state(
            "不支持旧版生命周期流",
            "此会话仍使用旧版主动生命周期事件，无法由仅快照运行时投影。",
        )

    try:
        replay = await container.stream_service.replay_stream(
            stream_id=session_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )
    except UnknownProjectorError:
        projector_name = "session-runtime"
        projector_version = container.settings.default_projector_version
        replay = await container.stream_service.replay_stream(
            stream_id=session_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )

    runtime_projection, memory_projection, evaluation, audit = await asyncio.gather(
        container.stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version=container.settings.default_projector_version,
        ),
        container.memory_service.get_session_memory(session_id=session_id),
        container.evaluation_service.evaluate_session(session_id=session_id),
        container.audit_service.get_session_audit(session_id=session_id),
    )
    runtime_state = dict(runtime_projection["state"])
    memory_state = dict(memory_projection["state"])
    summary = dict(evaluation["summary"])
    projector = dict(runtime_projection["projector"])
    selected_projector = dict(replay["projector"])
    available_projectors = [
        item
        for item in container.projector_registry.list_projectors()
        if str(item.get("name", "")).startswith("session-")
        or str(item.get("name", "")) == "inner-monologue-buffer"
    ]

    strategy_grid = _build_session_detail_strategy_grid(summary, audit)
    relation_grid = _build_session_detail_relation_grid(
        runtime_state,
        memory_state,
        summary,
    )
    replay_grid = _build_session_detail_replay_grid(projector, audit)
    projection_grid = _build_session_detail_projection_grid(
        selected_projector,
        replay,
    )
    transcript_rows = _build_session_detail_transcript_rows(runtime_state)
    replay_event_rows = _build_session_detail_replay_event_rows(replay)
    projector_buttons = _projector_buttons_html(
        request=request,
        session_id=session_id,
        projectors=available_projectors,
        selected_name=projector_name,
        selected_version=projector_version,
    )
    replay_preview = replay_event_rows or _empty_state(
        "暂无回放事件",
        "此投影器尚无可回放事件。",
    )

    return (
        '<div class="fragment-stack">'
        f"{_build_session_detail_header(session_id=session_id, summary=summary, audit=audit)}"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>策略与审计</h2></div>'
        f'<div class="kv-grid">{strategy_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>关系与记忆</h2></div>'
        f'<div class="kv-grid">{relation_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>回放快照</h2></div>'
        f'<div class="kv-grid">{replay_grid}</div>'
        "</section>"
        f"{
            _build_session_detail_projection_section(
                projector_buttons=projector_buttons,
                projection_grid=projection_grid,
                replay_preview=replay_preview,
                replay_projection=replay.get('projection', {}),
            )
        }"
        f"{
            _build_session_detail_trace_section(
                '最近对话记录',
                '<ul class="trace-list">'
                + (transcript_rows or _empty_state('暂无对话记录', '此会话暂无消息。'))
                + '</ul>',
            )
        }"
        f"{
            _build_session_detail_trace_section(
                '事件账本',
                '<ul class="trace-list">'
                + _event_ledger_html(container=container, events=events)
                + '</ul>',
            )
        }"
        f"{
            _build_session_detail_trace_section(
                '最近追踪',
                '<ul class="trace-list">'
                + _recent_trace_html(container=container, events=events)
                + '</ul>',
            )
        }"
        "</div>"
    )


def _build_console_home_context(
    *,
    request: Request,
    container: RuntimeContainer,
    sessions: list[dict[str, Any]],
) -> dict[str, Any]:
    sorted_sessions = sorted(
        sessions,
        key=lambda item: str(item.get("last_event_at") or ""),
        reverse=True,
    )
    selected_session_id = str(sorted_sessions[0]["session_id"]) if sorted_sessions else ""
    overview_url = str(request.url_for("console_overview_fragment"))
    sessions_url = str(request.url_for("console_sessions_fragment"))
    jobs_url = str(request.url_for("console_jobs_fragment"))
    archives_url = str(request.url_for("console_archives_fragment"))
    evaluations_url = str(request.url_for("console_evaluations_fragment"))
    scenarios_url = str(request.url_for("console_scenarios_fragment"))
    entity_url = str(request.url_for("console_entity_fragment"))
    default_projector_name = "session-runtime"
    default_projector_version = container.settings.default_projector_version
    detail_url = _detail_url(
        request,
        selected_session_id or None,
        projector_name=default_projector_name,
        version=default_projector_version,
    )
    return {
        "panel_refresh_seconds": PANEL_REFRESH_SECONDS,
        "selected_session_id": selected_session_id,
        "selected_session_id_js": _js_string(selected_session_id),
        "default_projector_name": default_projector_name,
        "default_projector_name_js": _js_string(default_projector_name),
        "default_projector_version": default_projector_version,
        "default_projector_version_js": _js_string(default_projector_version),
        "overview_url": overview_url,
        "sessions_url": sessions_url,
        "jobs_url": jobs_url,
        "archives_url": archives_url,
        "evaluations_url": evaluations_url,
        "scenarios_url": scenarios_url,
        "entity_url": entity_url,
        "detail_url": detail_url,
        "detail_base_url": str(request.url_for("console_session_detail_fragment")),
        "ws_url": str(request.url_for("runtime_websocket")),
    }


@router.get("", response_class=HTMLResponse)
async def console_home(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    sessions = await container.runtime_service.list_sessions()
    html = _render_template(
        "console/home.html",
        **_build_console_home_context(
            request=request,
            container=container,
            sessions=sessions,
        ),
    )
    return HTMLResponse(html)


@router.get("/fragments/overview", response_class=HTMLResponse)
async def console_overview_fragment(
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(_render_overview_fragment(await _fetch_overview_data(container)))


@router.get("/fragments/sessions", response_class=HTMLResponse)
async def console_sessions_fragment(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(await _render_sessions_fragment(request=request, container=container))


@router.get("/fragments/jobs", response_class=HTMLResponse)
async def console_jobs_fragment(
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(await _render_jobs_fragment(container))


@router.get("/fragments/archives", response_class=HTMLResponse)
async def console_archives_fragment(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(await _render_archives_fragment(request=request, container=container))


@router.get("/fragments/evaluations", response_class=HTMLResponse)
async def console_evaluations_fragment(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(await _render_evaluations_fragment(request=request, container=container))


@router.get("/fragments/scenarios", response_class=HTMLResponse)
async def console_scenarios_fragment(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(await _render_scenarios_fragment(request=request, container=container))


@router.get("/fragments/entity", response_class=HTMLResponse)
async def console_entity_fragment(
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(await _render_entity_fragment(container))


@router.get("/fragments/session-detail", response_class=HTMLResponse)
async def console_session_detail_fragment(
    request: Request,
    session_id: Annotated[str | None, Query()] = None,
    projector_name: str = "session-runtime",
    version: str = "v2",
    container: ContainerDep = ...,
) -> HTMLResponse:
    return HTMLResponse(
        await _render_session_detail_fragment(
            request=request,
            container=container,
            session_id=session_id,
            projector_name=projector_name,
            projector_version=version,
        )
    )
