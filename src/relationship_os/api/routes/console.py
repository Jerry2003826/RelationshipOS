from __future__ import annotations

import asyncio
import json
from html import escape
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from relationship_os.api.dependencies import get_container
from relationship_os.api.routes.runtime import build_runtime_overview_payload
from relationship_os.application.container import RuntimeContainer
from relationship_os.domain.event_types import TRACE_EVENT_TYPES
from relationship_os.domain.projectors import UnknownProjectorError

router = APIRouter(prefix="/console", tags=["console"])
ContainerDep = Annotated[RuntimeContainer, Depends(get_container)]

PANEL_REFRESH_SECONDS = 12
LIST_LIMIT = 8


def _text(value: object | None, *, fallback: str = "—") -> str:
    if value is None:
        return fallback
    rendered = str(value).strip()
    return escape(rendered or fallback)


def _timestamp(value: object | None) -> str:
    if value is None:
        return "—"
    rendered = str(value).replace("T", " ")
    rendered = rendered.replace("+00:00", " UTC")
    return escape(rendered)


def _shorten(value: object | None, *, limit: int = 96) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return escape(text or "—")
    return escape(text[: limit - 1].rstrip()) + "…"


def _js_string(value: object | None) -> str:
    return escape(json.dumps("" if value is None else str(value)))


def _pretty_json(value: object) -> str:
    return escape(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _tone(label: object | None) -> str:
    lowered = str(label or "").lower()
    if any(
        token in lowered
        for token in ["pass", "ok", "stable", "completed", "direct", "improved"]
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
    return (
        f'<span class="badge badge-{resolved_tone}">{_text(label, fallback="n/a")}</span>'
    )


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
    return (
        '<div class="empty-state">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(detail)}</p>'
        "</div>"
    )


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
    runtime_overview, sessions_payload, jobs_payload, archives_payload, evaluations_payload = (
        await asyncio.gather(
            build_runtime_overview_payload(container),
            container.runtime_service.list_sessions(),
            container.job_service.list_jobs(),
            container.audit_service.list_archived_sessions(),
            container.evaluation_service.list_session_evaluations(),
        )
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


def _render_overview_fragment(data: dict[str, Any]) -> str:
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

    metric_cards = "".join(
        [
            _metric_card("Sessions", len(sessions), "active runtime streams"),
            _metric_card("Jobs", len(jobs), "background lifecycle records"),
            _metric_card("Archives", len(archives), "snapshot-backed archived sessions"),
            _metric_card(
                "Worker",
                runtime_state.get("worker_id"),
                "single-process executor identity",
            ),
            _metric_card(
                "Follow-up Worker",
                proactive_dispatcher.get("worker_id"),
                "time-driven re-engagement dispatcher",
            ),
        ]
    )
    runtime_grid = "".join(
        [
            _labeled_value("Environment", runtime.get("env")),
            _labeled_value("Event Store", runtime.get("event_store_backend")),
            _labeled_value("LLM Backend", runtime.get("llm_backend")),
            _labeled_value("LLM Model", runtime.get("llm_model")),
            _labeled_value(
                "Poller",
                "running" if runtime_state.get("poller_running") else "stopped",
            ),
            _labeled_value("Active Jobs", runtime_state.get("active_job_count")),
            _labeled_value(
                "Follow-up Poller",
                "running"
                if proactive_dispatcher.get("poller_running")
                else "stopped",
            ),
            _labeled_value(
                "Active Dispatches",
                proactive_dispatcher.get("active_dispatch_count"),
            ),
        ]
    )
    proactive_grid = "".join(
        [
            _labeled_value("Waiting", proactive_counts.get("waiting", 0)),
            _labeled_value("Scheduled", proactive_counts.get("scheduled", 0)),
            _labeled_value("Due", proactive_counts.get("due", 0)),
            _labeled_value("Overdue", proactive_counts.get("overdue", 0)),
            _labeled_value("Hold", proactive_counts.get("hold", 0)),
            _labeled_value(
                "Actionable",
                proactive_summary.get("actionable_count", 0),
            ),
            _labeled_value("Next Due", proactive_summary.get("next_due_at")),
        ]
    )
    if highest_risk:
        evaluation_rows = "".join(
            (
                '<article class="signal-row">'
                f'<div class="signal-title">{_text(item.get("session_id"))}</div>'
                '<div class="signal-meta">'
                f'{_badge(item.get("latest_response_post_audit_status"))}'
                f'{_badge(item.get("latest_strategy"))}'
                f'{_badge(item.get("latest_boundary_decision"))}'
                "</div>"
                "<p>"
                f'{escape(_format_risk_signal(item))}'
                "</p>"
                "</article>"
            )
            for item in highest_risk
        )
    else:
        evaluation_rows = _empty_state(
            "No evaluations yet",
            "Run a session turn and the console will start surfacing risk signals here.",
        )
    if proactive_items:
        proactive_rows = "".join(
            (
                '<article class="signal-row">'
                f'<div class="signal-title">{_text(item.get("session_id"))}</div>'
                '<div class="signal-meta">'
                f'{_badge(item.get("queue_status"))}'
                f'{_badge(item.get("style"), tone="neutral")}'
                f'{_badge(item.get("time_awareness_mode"), tone="neutral")}'
                "</div>"
                "<p>"
                f'base {_timestamp(item.get("base_due_at"))} · '
                f'due {_timestamp(item.get("due_at"))} · '
                f'expires {_timestamp(item.get("expires_at"))} · '
                f'{_shorten(item.get("opening_hint"), limit=100)}'
                "</p>"
                '<p class="muted">'
                f'guidance {_text(item.get("guidance_mode"))} · '
                f'handoff {_text(item.get("guidance_handoff_mode"))} · '
                f'carryover {_text(item.get("guidance_carryover_mode"))}'
                "</p>"
                '<p class="muted">'
                f'cadence {_text(item.get("cadence_status"))} · '
                f'tempo {_text(item.get("cadence_followup_tempo"))} · '
                f'space {_text(item.get("cadence_user_space_mode"))}'
                "</p>"
                '<p class="muted">'
                f'ritual {_text(item.get("ritual_phase"))} · '
                f'close {_text(item.get("ritual_closing_move"))} · '
                f'somatic {_text(item.get("ritual_somatic_shortcut"))}'
                "</p>"
                '<p class="muted">'
                f'somatic plan {_text(item.get("somatic_orchestration_mode"))} · '
                f'anchor {_text(item.get("somatic_orchestration_body_anchor"))} · '
                f'follow-up {_text(item.get("somatic_orchestration_followup_style"))}'
                "</p>"
                '<p class="muted">'
                f'scheduling {_text(item.get("proactive_scheduling_mode"))} · '
                f'guard {_text(item.get("proactive_scheduling_low_pressure_guard"))} · '
                f'delay {_text(item.get("proactive_scheduling_first_touch_extra_delay_seconds"))}'
                "</p>"
                '<p class="muted">'
                f'orchestration {_text(item.get("proactive_orchestration_key"))} · '
                f'objective {_text(item.get("proactive_orchestration_stage_objective"))} · '
                f'delivery {_text(item.get("proactive_orchestration_stage_delivery_mode"))}'
                "</p>"
                '<p class="muted">'
                f'actuation {_text(item.get("proactive_actuation_key"))} · '
                f'open {_text(item.get("proactive_actuation_opening_move"))} · '
                f'close {_text(item.get("proactive_actuation_closing_move"))}'
                "</p>"
                '<p class="muted">'
                f'bridge {_text(item.get("proactive_actuation_bridge_move"))} · '
                f'user-space {_text(item.get("proactive_actuation_user_space_signal"))} · '
                f'somatic {_text(item.get("proactive_actuation_somatic_mode"))}'
                "</p>"
                '<p class="muted">'
                f'progression {_text(item.get("proactive_progression_key"))} · '
                f'action {_text(item.get("proactive_progression_stage_action"))} · '
                f'advanced {_text(item.get("proactive_progression_advanced"))}'
                "</p>"
                '<p class="muted">'
                f'controller {_text(item.get("proactive_stage_controller_key"))} · '
                f'target {_text(item.get("proactive_stage_controller_target_stage_label"))} · '
                f'delay {_text(item.get("proactive_stage_controller_additional_delay_seconds"))}'
                "</p>"
                '<p class="muted">'
                f'line controller {_text(item.get("proactive_line_controller_key"))} · '
                f'state {_text(item.get("proactive_line_controller_line_state"))} · '
                f'delay {_text(item.get("proactive_line_controller_additional_delay_seconds"))}'
                "</p>"
                '<p class="muted">'
                f'guardrail {_text(item.get("proactive_guardrail_key"))} · '
                f'max {_text(item.get("proactive_guardrail_max_dispatch_count"))} · '
                f'user wait '
                f'{_text(item.get("proactive_guardrail_stage_min_seconds_since_last_user"))}'
                "</p>"
                '<p class="muted">'
                f'matrix {_text(item.get("reengagement_matrix_key"))} · '
                f'selected {_text(item.get("reengagement_matrix_selected_strategy"))} · '
                f'learn {_text(item.get("reengagement_matrix_learning_mode"))} · '
                f'blocked {_text(item.get("reengagement_matrix_blocked_count"))}'
                "</p>"
                '<p class="muted">'
                f'strategy {_text(item.get("reengagement_strategy_key"))} · '
                f'pressure {_text(item.get("reengagement_pressure_mode"))} · '
                f'autonomy {_text(item.get("reengagement_autonomy_signal"))}'
                "</p>"
                '<p class="muted">'
                f'feedback {_text(item.get("proactive_dispatch_feedback_key"))} · '
                f'strategy {_text(item.get("proactive_dispatch_feedback_strategy_key"))} · '
                f'defer {_text(item.get("proactive_dispatch_feedback_gate_defer_count"))}'
                "</p>"
                '<p class="muted">'
                f'gate {_text(item.get("proactive_dispatch_gate_key"))} · '
                f'decision {_text(item.get("proactive_dispatch_gate_decision"))} · '
                f'retry {_text(item.get("proactive_dispatch_gate_retry_after_seconds"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle dispatch {_text(item.get("proactive_lifecycle_dispatch_decision"))} · '
                f'outcome {_text(item.get("proactive_lifecycle_outcome_decision"))} · '
                f'messages {_text(item.get("proactive_lifecycle_outcome_message_event_count"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle resolution '
                f'{_text(item.get("proactive_lifecycle_resolution_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_resolution_mode"))} · '
                f'queue {_text(item.get("proactive_lifecycle_resolution_queue_override_status"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle activation '
                f'{_text(item.get("proactive_lifecycle_activation_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_activation_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_activation_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle settlement '
                f'{_text(item.get("proactive_lifecycle_settlement_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_settlement_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_settlement_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle closure '
                f'{_text(item.get("proactive_lifecycle_closure_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_closure_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_closure_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle availability '
                f'{_text(item.get("proactive_lifecycle_availability_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_availability_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_availability_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle retention '
                f'{_text(item.get("proactive_lifecycle_retention_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_retention_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_retention_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle eligibility '
                f'{_text(item.get("proactive_lifecycle_eligibility_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_eligibility_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_eligibility_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle candidate '
                f'{_text(item.get("proactive_lifecycle_candidate_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_candidate_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_candidate_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle selectability '
                f'{_text(item.get("proactive_lifecycle_selectability_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_selectability_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_selectability_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle reentry '
                f'{_text(item.get("proactive_lifecycle_reentry_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_reentry_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_reentry_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle reactivation '
                f'{_text(item.get("proactive_lifecycle_reactivation_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_reactivation_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_reactivation_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle resumption '
                f'{_text(item.get("proactive_lifecycle_resumption_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_resumption_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_resumption_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle readiness '
                f'{_text(item.get("proactive_lifecycle_readiness_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_readiness_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_readiness_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle arming '
                f'{_text(item.get("proactive_lifecycle_arming_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_arming_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_arming_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle trigger '
                f'{_text(item.get("proactive_lifecycle_trigger_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_trigger_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_trigger_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle launch '
                f'{_text(item.get("proactive_lifecycle_launch_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_launch_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_launch_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle handoff '
                f'{_text(item.get("proactive_lifecycle_handoff_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_handoff_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_handoff_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle continuation '
                f'{_text(item.get("proactive_lifecycle_continuation_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_continuation_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_continuation_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle sustainment '
                f'{_text(item.get("proactive_lifecycle_sustainment_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_sustainment_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_sustainment_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle stewardship '
                f'{_text(item.get("proactive_lifecycle_stewardship_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_stewardship_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_stewardship_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle guardianship '
                f'{_text(item.get("proactive_lifecycle_guardianship_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_guardianship_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_guardianship_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle oversight '
                f'{_text(item.get("proactive_lifecycle_oversight_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_oversight_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_oversight_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle assurance '
                f'{_text(item.get("proactive_lifecycle_assurance_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_assurance_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_assurance_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle attestation '
                f'{_text(item.get("proactive_lifecycle_attestation_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_attestation_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_attestation_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle verification '
                f'{_text(item.get("proactive_lifecycle_verification_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_verification_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_verification_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle certification '
                f'{_text(item.get("proactive_lifecycle_certification_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_certification_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_certification_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle confirmation '
                f'{_text(item.get("proactive_lifecycle_confirmation_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_confirmation_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_confirmation_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle ratification '
                f'{_text(item.get("proactive_lifecycle_ratification_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_ratification_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_ratification_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle endorsement '
                f'{_text(item.get("proactive_lifecycle_endorsement_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_endorsement_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_endorsement_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle authorization '
                f'{_text(item.get("proactive_lifecycle_authorization_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_authorization_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_authorization_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle enactment '
                f'{_text(item.get("proactive_lifecycle_enactment_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_enactment_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_enactment_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle finality '
                f'{_text(item.get("proactive_lifecycle_finality_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_finality_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_finality_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle completion '
                f'{_text(item.get("proactive_lifecycle_completion_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_completion_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_completion_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle conclusion '
                f'{_text(item.get("proactive_lifecycle_conclusion_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_conclusion_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_conclusion_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle disposition '
                f'{_text(item.get("proactive_lifecycle_disposition_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_disposition_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_disposition_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle standing '
                f'{_text(item.get("proactive_lifecycle_standing_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_standing_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_standing_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle residency '
                f'{_text(item.get("proactive_lifecycle_residency_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_residency_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_residency_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle tenure '
                f'{_text(item.get("proactive_lifecycle_tenure_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_tenure_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_tenure_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle persistence '
                f'{_text(item.get("proactive_lifecycle_persistence_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_persistence_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_persistence_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle durability '
                f'{_text(item.get("proactive_lifecycle_durability_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_durability_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_durability_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle longevity '
                f'{_text(item.get("proactive_lifecycle_longevity_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_longevity_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_longevity_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle legacy '
                f'{_text(item.get("proactive_lifecycle_legacy_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_legacy_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_legacy_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle heritage '
                f'{_text(item.get("proactive_lifecycle_heritage_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_heritage_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_heritage_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle lineage '
                f'{_text(item.get("proactive_lifecycle_lineage_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_lineage_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_lineage_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle ancestry '
                f'{_text(item.get("proactive_lifecycle_ancestry_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_ancestry_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_ancestry_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle provenance '
                f'{_text(item.get("proactive_lifecycle_provenance_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_provenance_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_provenance_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle origin '
                f'{_text(item.get("proactive_lifecycle_origin_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_origin_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_origin_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle root '
                f'{_text(item.get("proactive_lifecycle_root_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_root_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_root_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle foundation '
                f'{_text(item.get("proactive_lifecycle_foundation_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_foundation_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_foundation_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle bedrock '
                f'{_text(item.get("proactive_lifecycle_bedrock_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_bedrock_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_bedrock_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle substrate '
                f'{_text(item.get("proactive_lifecycle_substrate_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_substrate_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_substrate_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle stratum '
                f'{_text(item.get("proactive_lifecycle_stratum_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_stratum_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_stratum_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'lifecycle layer '
                f'{_text(item.get("proactive_lifecycle_layer_decision"))} · '
                f'mode {_text(item.get("proactive_lifecycle_layer_mode"))} · '
                f'active {_text(item.get("proactive_lifecycle_layer_active_stage_label"))}'
                "</p>"
                '<p class="muted">'
                f'stage {_text(item.get("proactive_cadence_stage_label"))} · '
                f'#{_text(item.get("proactive_cadence_stage_index"))}/'
                f'{_text(item.get("proactive_cadence_stage_count"))} · '
                f'remaining {_text(item.get("proactive_cadence_remaining_dispatches"))}'
                "</p>"
                '<p class="muted">'
                f'schedule reason {_text(item.get("schedule_reason"))} · '
                f'hold {_format_followup_hold_reasons(item)}'
                "</p>"
                "</article>"
            )
            for item in proactive_items[:4]
        )
    else:
        proactive_rows = _empty_state(
            "No proactive follow-ups queued",
            (
                "Once a session becomes stable enough for a time-driven check-in, "
                "it will surface here."
            ),
        )

    return (
        '<div class="fragment-stack">'
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Runtime Overview</h2>'
        f'<span class="pulse-dot">refreshes every {PANEL_REFRESH_SECONDS}s</span></div>'
        f'<div class="metric-grid">{metric_cards}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Runtime Shape</h2></div>'
        f'<div class="kv-grid">{runtime_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Hot Evaluation Signals</h2></div>'
        f'<div class="signal-list">{evaluation_rows}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Proactive Follow-up Queue</h2></div>'
        f'<div class="kv-grid">{proactive_grid}</div>'
        f'<div class="signal-list">{proactive_rows}</div>'
        "</section>"
        "</div>"
    )


def _format_risk_signal(summary: dict[str, Any]) -> str:
    return ", ".join(
        [
            f'violations={summary.get("response_post_audit_total_violation_count", 0)}',
            f'normalizations={summary.get("response_normalization_changed_turn_count", 0)}',
        ]
    )


def _format_followup_hold_reasons(item: dict[str, Any]) -> str:
    hold_reasons = list(item.get("hold_reasons") or [])
    if not hold_reasons:
        return "—"
    return ", ".join(_text(reason) for reason in hold_reasons[:2])


def _scenario_diff_detail(item: dict[str, Any]) -> str:
    changed_checks = list(item.get("changed_checks") or [])
    if not changed_checks:
        return "Check outcomes stayed numerically stable."
    return _shorten(changed_checks[0].get("description"), limit=110)


async def _render_sessions_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
    sessions, evaluations_payload = await asyncio.gather(
        container.runtime_service.list_sessions(),
        container.evaluation_service.list_session_evaluations(),
    )
    summaries = {
        str(item["session_id"]): item for item in evaluations_payload.get("sessions", [])
    }
    sorted_sessions = sorted(
        sessions,
        key=lambda item: str(item.get("last_event_at") or ""),
        reverse=True,
    )
    if not sorted_sessions:
        return _empty_state(
            "No sessions yet",
            "Create or process a session and it will appear here for replay and audit.",
        )

    cards = []
    for session in sorted_sessions[:LIST_LIMIT]:
        summary = dict(summaries.get(str(session["session_id"]), {}))
        detail_url = _detail_url(request, str(session["session_id"]))
        cards.append(
            '<article class="list-card">'
            f'<button class="session-pick" '
            f'hx-get="{escape(detail_url)}" '
            'hx-target="#console-session-detail" '
            'hx-swap="innerHTML" '
            f'x-on:click="selectedSession = {_js_string(session["session_id"])}; '
            f'window.relationshipOSConsole?.selectSession({_js_string(session["session_id"])})">'
            f'<div class="list-title">{_text(session.get("session_id"))}</div>'
            '<div class="list-meta">'
            f'{_badge(summary.get("latest_strategy"))}'
            f'{_badge(summary.get("latest_response_post_audit_status"))}'
            f'{_badge(summary.get("latest_response_normalization_final_status"))}'
            "</div>"
            f'<p>turns {session.get("turn_count", 0)} · events {session.get("event_count", 0)} · '
            f'safety {_text(summary.get("avg_psychological_safety"))}</p>'
            f'<p class="muted">last event {_timestamp(session.get("last_event_at"))}</p>'
            "</button>"
            "</article>"
        )
    return "".join(cards)


async def _render_jobs_fragment(container: RuntimeContainer) -> str:
    jobs_payload = await container.job_service.list_jobs()
    jobs = list(jobs_payload["jobs"])
    if not jobs:
        return _empty_state(
            "No jobs scheduled",
            "Offline consolidation and recovery jobs will appear here.",
        )
    return "".join(
        (
            '<article class="list-card">'
            f'<div class="list-title">{_text(job.get("job_id"))}</div>'
            '<div class="list-meta">'
            f'{_badge(job.get("status"))}{_badge(job.get("job_type"))}'
            "</div>"
            f'<p>session {_text(job.get("session_id"))} · '
            f'attempt {job.get("attempt_count", 0)}/{job.get("max_attempts", 0)}</p>'
            f'<p class="muted">worker {_text(job.get("last_worker_id"))} · '
            f'lease {_timestamp(job.get("lease_expires_at"))}</p>'
            "</article>"
        )
        for job in jobs[:LIST_LIMIT]
    )


async def _render_archives_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
    archives_payload = await container.audit_service.list_archived_sessions()
    archives = list(archives_payload["sessions"])
    if not archives:
        return _empty_state(
            "No archived sessions",
            "Archived sessions will show up here once consolidation marks them durable.",
        )
    items = []
    for archive in archives[:LIST_LIMIT]:
        session_id = str(archive["session_id"])
        detail_url = _detail_url(request, session_id)
        items.append(
            '<article class="list-card">'
            f'<button class="session-pick" '
            f'hx-get="{escape(detail_url)}" '
            'hx-target="#console-session-detail" '
            'hx-swap="innerHTML" '
            f'x-on:click="selectedSession = {_js_string(session_id)}; '
            f'window.relationshipOSConsole?.selectSession({_js_string(session_id)})">'
            f'<div class="list-title">{_text(session_id)}</div>'
            '<div class="list-meta">'
            f'{_badge("archived", tone="good")}'
            f'{_badge(archive.get("reason"))}'
            "</div>"
            f'<p>snapshot {_text((archive.get("latest_snapshot") or {}).get("snapshot_id"))}</p>'
            f'<p class="muted">archived {_timestamp(archive.get("archived_at"))}</p>'
            "</button>"
            "</article>"
        )
    return "".join(items)


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
    evaluations.sort(
        key=lambda item: (
            int(item.get("system3_identity_trajectory_recenter_turn_count", 0)),
            int(item.get("system3_growth_transition_watch_turn_count", 0)),
            int(item.get("system3_growth_transition_trajectory_redirect_turn_count", 0)),
            int(item.get("system3_user_model_evolution_revise_turn_count", 0)),
            int(item.get("system3_user_model_trajectory_recenter_turn_count", 0)),
            int(item.get("system3_version_migration_revise_turn_count", 0)),
            int(item.get("system3_version_migration_trajectory_hold_turn_count", 0)),
            int(item.get("system3_strategy_supervision_revise_turn_count", 0)),
            int(
                item.get("system3_strategy_supervision_trajectory_tighten_turn_count", 0)
            ),
            int(item.get("system3_expectation_calibration_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_expectation_calibration_trajectory_reset_turn_count",
                    0,
                )
            ),
            int(item.get("system3_dependency_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_dependency_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_autonomy_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_autonomy_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_boundary_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_boundary_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_support_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_support_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_continuity_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_continuity_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_repair_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_repair_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_attunement_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_attunement_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_trust_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_trust_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_clarity_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_clarity_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_pacing_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_pacing_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_commitment_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_commitment_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_disclosure_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_disclosure_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_reciprocity_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_reciprocity_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_pressure_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_pressure_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_relational_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_relational_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_safety_governance_revise_turn_count", 0)),
            int(
                item.get(
                    "system3_safety_governance_trajectory_recenter_turn_count",
                    0,
                )
            ),
            int(item.get("system3_moral_reasoning_revise_turn_count", 0)),
            int(item.get("system3_moral_trajectory_recenter_turn_count", 0)),
            int(item.get("system3_strategy_audit_revise_turn_count", 0)),
            int(item.get("system3_strategy_audit_trajectory_corrective_turn_count", 0)),
            int(item.get("system3_emotional_debt_elevated_turn_count", 0)),
            int(item.get("system3_emotional_debt_trajectory_decompression_turn_count", 0)),
            int(item.get("output_quality_issue_count", 0)),
            int(item.get("response_post_audit_total_violation_count", 0)),
            int(item.get("response_normalization_changed_turn_count", 0)),
            int(item.get("policy_gate_guarded_turn_count", 0)),
            float(item.get("avg_psychological_safety") or 0.0),
        ),
        reverse=True,
    )
    if not evaluations:
        return _empty_state(
            "No evaluations yet",
            (
                "Once sessions accumulate turns, the evaluation rail will surface "
                "risk and memory signals."
            ),
        )

    top_strategies = list(preference_report.get("strategies", []))
    if top_strategies:
        strategy_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("strategy"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("kept_session_count"))}'
                f'{_badge(item.get("filtered_session_count"), tone="neutral")}'
                "</div>"
                f'<p>score {_text(item.get("avg_denoised_preference_score"))} · '
                f'quality {_text(item.get("avg_quality_floor_score"))} · '
                f'duration {_text(item.get("avg_duration_signal"))}</p>'
                "</article>"
            )
            for item in top_strategies[:3]
        )
    else:
        strategy_cards = _empty_state(
            "No strategy signals yet",
            (
                "Once non-scenario sessions accumulate, denoised strategy "
                "preference signals appear here."
            ),
        )

    reengagement_learning_report = dict(
        preference_report.get("reengagement_learning") or {}
    )
    top_reengagement_learning = list(reengagement_learning_report.get("strategies", []))
    if top_reengagement_learning:
        reengagement_learning_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("strategy_key"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("contextual_kept_session_count"))}'
                f'{_badge(item.get("kept_session_count"), tone="neutral")}'
                "</div>"
                f'<p>learn {_text(item.get("avg_learning_score"))} · '
                f'ctx {_text(item.get("avg_contextual_learning_score"))} · '
                f'quality {_text(item.get("avg_quality_floor_score"))}</p>'
                "</article>"
            )
            for item in top_reengagement_learning[:3]
        )
    else:
        reengagement_learning_cards = _empty_state(
            "No re-engagement learning yet",
            (
                "Once proactive sessions accumulate, matrix learning signals "
                "will appear here."
            ),
        )
    reengagement_learning_matches = _labeled_value(
        "Matches",
        reengagement_learning_report.get("matching_context_session_count"),
    )

    preference_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Preference Signals</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Sessions", preference_report.get("session_count"))}'
        f'{_labeled_value("Strategies", preference_report.get("strategy_count"))}'
        f'{_labeled_value("Filtered", preference_report.get("filtered_session_count"))}'
        f'{_labeled_value("Noisy", preference_report.get("noisy_session_count"))}'
        "</div>"
        f'<div class="signal-list">{strategy_cards}</div>'
        '<div class="section-header"><h2>Re-engagement Learning</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Mode", reengagement_learning_report.get("learning_mode"))}'
        f'{_labeled_value("Context", reengagement_learning_report.get("context_stratum"))}'
        f'{_labeled_value("Signals", reengagement_learning_report.get("strategy_count"))}'
        f"{reengagement_learning_matches}"
        "</div>"
        f'<div class="signal-list">{reengagement_learning_cards}</div>'
        "</section>"
    )

    items = []
    for summary in evaluations[:LIST_LIMIT]:
        session_id = str(summary["session_id"])
        detail_url = _detail_url(request, session_id)
        items.append(
            '<article class="list-card">'
            f'<button class="session-pick" '
            f'hx-get="{escape(detail_url)}" '
            'hx-target="#console-session-detail" '
            'hx-swap="innerHTML" '
            f'x-on:click="selectedSession = {_js_string(session_id)}; '
            f'window.relationshipOSConsole?.selectSession({_js_string(session_id)})">'
            f'<div class="list-title">{_text(session_id)}</div>'
            '<div class="list-meta">'
            f'{_badge(summary.get("latest_response_post_audit_status"))}'
            f'{_badge(summary.get("output_quality_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_policy_path"))}'
            f'{_badge(summary.get("latest_strategy_diversity_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_response_sequence_mode"), tone="neutral")}'
            f'{_badge(summary.get("latest_time_awareness_mode"), tone="neutral")}'
            f'{_badge(summary.get("latest_cognitive_load_band"), tone="neutral")}'
            f'{_badge(summary.get("latest_guidance_mode"), tone="neutral")}'
            f'{_badge(summary.get("latest_proactive_followup_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_proactive_aggregate_governance_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_reengagement_ritual_mode"), tone="neutral")}'
            f'{_badge(summary.get("latest_runtime_quality_doctor_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_system3_identity_trajectory_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_system3_growth_transition_status"), tone="neutral")}'
            f'{_badge(  # keep growth trajectory visible in the rail
                summary.get("latest_system3_growth_transition_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_user_model_evolution_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_system3_user_model_trajectory_status"), tone="neutral")}'
            f'{_badge(  # keep expectation calibration visible in the rail
                summary.get("latest_system3_expectation_calibration_status"),
                tone="neutral",
            )}'
            f'{_badge(
                summary.get("latest_system3_expectation_calibration_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_dependency_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_dependency_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_autonomy_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_autonomy_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_boundary_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_boundary_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_support_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_support_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_continuity_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_continuity_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_repair_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_repair_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_attunement_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_attunement_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_trust_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_trust_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_clarity_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_clarity_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_pacing_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_pacing_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_commitment_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_commitment_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_disclosure_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_disclosure_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_reciprocity_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_reciprocity_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_pressure_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_pressure_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_relational_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_relational_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_safety_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_safety_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_progress_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_progress_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_stability_governance_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_stability_governance_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_version_migration_status"), tone="neutral")}'
            f'{_badge(  # keep migration trajectory visible in the rail
                summary.get("latest_system3_version_migration_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_strategy_supervision_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_strategy_supervision_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_moral_reasoning_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_system3_moral_trajectory_status"), tone="neutral")}'
            f'{_badge(summary.get("latest_system3_strategy_audit_status"), tone="neutral")}'
            f'{_badge(  # keep audit trajectory visible in the rail
                summary.get("latest_system3_strategy_audit_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_system3_emotional_debt_status"), tone="neutral")}'
            f'{_badge(
                summary.get("latest_system3_emotional_debt_trajectory_status"),
                tone="neutral",
            )}'
            f'{_badge(summary.get("latest_boundary_decision"))}'
            "</div>"
            f'<p>{escape(_format_risk_signal(summary))} · '
            f'memory recalls={summary.get("memory_recall_turn_count", 0)} · '
            f'guarded turns={summary.get("policy_gate_guarded_turn_count", 0)}</p>'
            f'<p class="muted">quality {_text(summary.get("output_quality_status"))} · '
            f'words {_text(summary.get("latest_response_word_count"))} · '
            f'issues {_text(summary.get("output_quality_issue_count"))}</p>'
            f'<p class="muted">progress governance '
            f'{_text(summary.get("latest_system3_progress_governance_status"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_progress_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_progress_governance_target"))}</p>'
            f'<p class="muted">stability governance '
            f'{_text(summary.get("latest_system3_stability_governance_status"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_stability_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_stability_governance_target"))}</p>'
            f'<p class="muted">diversity '
            f'{_text(summary.get("latest_strategy_diversity_status"))} · '
            f'index {_text(summary.get("strategy_diversity_index"))} · '
            f'interventions {_text(summary.get("strategy_diversity_intervention_turn_count"))}</p>'
            f'<p class="muted">sequence {_text(summary.get("latest_response_sequence_mode"))} · '
            f'units {_text(summary.get("latest_response_sequence_unit_count"))} · '
            f'continuous turns {_text(summary.get("continuous_output_turn_count"))}</p>'
            f'<p class="muted">coordination {_text(summary.get("latest_time_awareness_mode"))} · '
            f'load {_text(summary.get("latest_cognitive_load_band"))} · '
            f'proactive {_text(summary.get("latest_proactive_style"))}</p>'
            f'<p class="muted">guidance '
            f'{_text(summary.get("latest_guidance_mode"))} · '
            f'pace {_text(summary.get("latest_guidance_pacing"))} · '
            f'agency {_text(summary.get("latest_guidance_agency_mode"))}</p>'
            f'<p class="muted">guidance detail '
            f'{_text(summary.get("latest_guidance_ritual_action"))} · '
            f'handoff {_text(summary.get("latest_guidance_handoff_mode"))} · '
            f'carryover {_text(summary.get("latest_guidance_carryover_mode"))}</p>'
            f'<p class="muted">cadence '
            f'{_text(summary.get("latest_cadence_status"))} · '
            f'tempo {_text(summary.get("latest_cadence_followup_tempo"))} · '
            f'space {_text(summary.get("latest_cadence_user_space_mode"))}</p>'
            f'<p class="muted">ritual '
            f'{_text(summary.get("latest_session_ritual_phase"))} · '
            f'close {_text(summary.get("latest_session_ritual_closing_move"))} · '
            f'somatic {_text(summary.get("latest_session_ritual_somatic_shortcut"))}</p>'
            f'<p class="muted">somatic plan '
            f'{_text(summary.get("latest_somatic_orchestration_mode"))} · '
            f'anchor {_text(summary.get("latest_somatic_orchestration_body_anchor"))} · '
            f'follow-up {_text(summary.get("latest_somatic_orchestration_followup_style"))}</p>'
            f'<p class="muted">follow-up '
            f'{_text(summary.get("latest_proactive_followup_status"))} · '
            f'style {_text(summary.get("latest_proactive_followup_style"))} · '
            f'after {_text(summary.get("latest_proactive_followup_after_seconds"))}</p>'
            f'<p class="muted">follow-up scheduling '
            f'{_text(summary.get("latest_proactive_scheduling_mode"))} · '
            f'cooldown '
            f'{_text(summary.get("latest_proactive_scheduling_min_seconds_since_last_outbound"))}'
            f' · '
            f'extra '
            f'{_text(summary.get("latest_proactive_scheduling_first_touch_extra_delay_seconds"))}</p>'
            f'<p class="muted">follow-up orchestration '
            f'{_text(summary.get("latest_proactive_orchestration_key"))} · '
            f'second touch '
            f'{_text(summary.get("latest_proactive_orchestration_second_touch_delivery_mode"))} · '
            f'close {_text(summary.get("latest_proactive_orchestration_close_loop_stage"))}</p>'
            f'<p class="muted">follow-up actuation '
            f'{_text(summary.get("latest_proactive_actuation_key"))} · '
            f'second touch '
            f'{_text(summary.get("latest_proactive_actuation_second_touch_opening_move"))} · '
            f'close {_text(summary.get("latest_proactive_actuation_final_touch_closing_move"))}</p>'
            f'<p class="muted">actuation bridge '
            f'{_text(summary.get("latest_proactive_actuation_second_touch_bridge_move"))} · '
            f'user-space '
            f'{_text(summary.get("latest_proactive_actuation_second_touch_user_space_signal"))}</p>'
            f'<p class="muted">follow-up progression '
            f'{_text(summary.get("latest_proactive_progression_key"))} · '
            f'second touch '
            f'{_text(summary.get("latest_proactive_progression_second_touch_action"))} · '
            f'close {_text(summary.get("latest_proactive_progression_final_touch_action"))}</p>'
            f'<p class="muted">follow-up controller '
            f'{_text(summary.get("latest_proactive_stage_controller_key"))} · '
            f'target '
            f'{_text(summary.get("latest_proactive_stage_controller_target_stage_label"))} · '
            f'delay '
            f'{_text(summary.get("latest_proactive_stage_controller_additional_delay_seconds"))}</p>'
            f'<p class="muted">follow-up line controller '
            f'{_text(summary.get("latest_proactive_line_controller_key"))} · '
            f'state {_text(summary.get("latest_proactive_line_controller_line_state"))} · '
            f'delay '
            f'{_text(summary.get("latest_proactive_line_controller_additional_delay_seconds"))}</p>'
            f'<p class="muted">follow-up refresh '
            f'{_text(summary.get("latest_proactive_stage_refresh_key"))} · '
            f'window {_text(summary.get("latest_proactive_stage_refresh_window_status"))} · '
            f'changed {_text(summary.get("latest_proactive_stage_refresh_changed"))}</p>'
            f'<p class="muted">follow-up replan '
            f'{_text(summary.get("latest_proactive_stage_replan_key"))} · '
            f'strategy {_text(summary.get("latest_proactive_stage_replan_strategy_key"))} · '
            f'changed {_text(summary.get("latest_proactive_stage_replan_changed"))}</p>'
            f'<p class="muted">follow-up feedback '
            f'{_text(summary.get("latest_proactive_dispatch_feedback_key"))} · '
            f'strategy {_text(summary.get("latest_proactive_dispatch_feedback_strategy_key"))} · '
            f'changed {_text(summary.get("latest_proactive_dispatch_feedback_changed"))}</p>'
            f'<p class="muted">follow-up gate '
            f'{_text(summary.get("latest_proactive_dispatch_gate_key"))} · '
            f'decision {_text(summary.get("latest_proactive_dispatch_gate_decision"))} · '
            f'deferred {_text(summary.get("proactive_dispatch_gate_deferred_turn_count"))}</p>'
            f'<p class="muted">dispatch envelope '
            f'{_text(summary.get("latest_proactive_dispatch_envelope_key"))} · '
            f'{_text(summary.get("latest_proactive_dispatch_envelope_decision"))} · '
            f'strategy '
            f'{_text(summary.get("latest_proactive_dispatch_envelope_strategy_key"))} · '
            f'sources '
            f'{_text(summary.get("latest_proactive_dispatch_envelope_source_count"))}</p>'
            f'<p class="muted">stage state '
            f'{_text(summary.get("latest_proactive_stage_state_key"))} · '
            f'{_text(summary.get("latest_proactive_stage_state_mode"))} · '
            f'queue {_text(summary.get("latest_proactive_stage_state_queue_status"))} · '
            f'source {_text(summary.get("latest_proactive_stage_state_source"))}</p>'
            f'<p class="muted">stage transition '
            f'{_text(summary.get("latest_proactive_stage_transition_key"))} · '
            f'{_text(summary.get("latest_proactive_stage_transition_mode"))} · '
            f'queue {_text(summary.get("latest_proactive_stage_transition_queue_hint"))} · '
            f'source {_text(summary.get("latest_proactive_stage_transition_source"))}</p>'
            f'<p class="muted">stage machine '
            f'{_text(summary.get("latest_proactive_stage_machine_key"))} · '
            f'{_text(summary.get("latest_proactive_stage_machine_mode"))} · '
            f'lifecycle {_text(summary.get("latest_proactive_stage_machine_lifecycle"))} · '
            f'action {_text(summary.get("latest_proactive_stage_machine_actionability"))}</p>'
            f'<p class="muted">line state '
            f'{_text(summary.get("latest_proactive_line_state_key"))} · '
            f'{_text(summary.get("latest_proactive_line_state_mode"))} · '
            f'lifecycle {_text(summary.get("latest_proactive_line_state_lifecycle"))} · '
            f'action {_text(summary.get("latest_proactive_line_state_actionability"))}</p>'
            f'<p class="muted">line transition '
            f'{_text(summary.get("latest_proactive_line_transition_key"))} · '
            f'{_text(summary.get("latest_proactive_line_transition_mode"))} · '
            f'exit {_text(summary.get("latest_proactive_line_transition_exit_mode"))}</p>'
            f'<p class="muted">line machine '
            f'{_text(summary.get("latest_proactive_line_machine_key"))} · '
            f'{_text(summary.get("latest_proactive_line_machine_mode"))} · '
            f'lifecycle {_text(summary.get("latest_proactive_line_machine_lifecycle"))} · '
            f'action {_text(summary.get("latest_proactive_line_machine_actionability"))}</p>'
            f'<p class="muted">lifecycle state '
            f'{_text(summary.get("latest_proactive_lifecycle_state_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_state_mode"))} · '
            f'lifecycle {_text(summary.get("latest_proactive_lifecycle_state_lifecycle"))} · '
            f'action {_text(summary.get("latest_proactive_lifecycle_state_actionability"))}</p>'
            f'<p class="muted">lifecycle transition '
            f'{_text(summary.get("latest_proactive_lifecycle_transition_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_transition_mode"))} · '
            f'exit {_text(summary.get("latest_proactive_lifecycle_transition_exit_mode"))}</p>'
            f'<p class="muted">lifecycle machine '
            f'{_text(summary.get("latest_proactive_lifecycle_machine_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_machine_mode"))} · '
            f'lifecycle {_text(summary.get("latest_proactive_lifecycle_machine_lifecycle"))} · '
            f'action {_text(summary.get("latest_proactive_lifecycle_machine_actionability"))}</p>'
            f'<p class="muted">lifecycle controller '
            f'{_text(summary.get("latest_proactive_lifecycle_controller_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_controller_state"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_controller_decision"))} · '
            f'delay {_text(summary.get("latest_proactive_lifecycle_controller_delay_seconds"))}</p>'
            f'<p class="muted">lifecycle envelope '
            f'{_text(summary.get("latest_proactive_lifecycle_envelope_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_envelope_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_envelope_decision"))} · '
            f'action {_text(summary.get("latest_proactive_lifecycle_envelope_actionability"))}</p>'
            f'<p class="muted">lifecycle scheduler '
            f'{_text(summary.get("latest_proactive_lifecycle_scheduler_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_scheduler_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_scheduler_decision"))} · '
            f'queue {_text(summary.get("latest_proactive_lifecycle_scheduler_queue_status"))}</p>'
            f'<p class="muted">lifecycle window '
            f'{_text(summary.get("latest_proactive_lifecycle_window_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_window_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_window_decision"))} · '
            f'queue {_text(summary.get("latest_proactive_lifecycle_window_queue_status"))}</p>'
            f'<p class="muted">lifecycle queue '
            f'{_text(summary.get("latest_proactive_lifecycle_queue_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_queue_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_queue_decision"))} · '
            f'queue {_text(summary.get("latest_proactive_lifecycle_queue_status"))}</p>'
            f'<p class="muted">lifecycle dispatch '
            f'{_text(summary.get("latest_proactive_lifecycle_dispatch_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_dispatch_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_dispatch_decision"))} · '
            f'action {_text(summary.get("latest_proactive_lifecycle_dispatch_actionability"))}</p>'
            f'<p class="muted">lifecycle outcome '
            f'{_text(summary.get("latest_proactive_lifecycle_outcome_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_outcome_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_outcome_decision"))} · '
            f'action {_text(summary.get("latest_proactive_lifecycle_outcome_actionability"))}</p>'
            f'<p class="muted">lifecycle resolution '
            f'{_text(summary.get("latest_proactive_lifecycle_resolution_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_resolution_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_resolution_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_resolution_actionability"))}</p>'
            f'<p class="muted">lifecycle activation '
            f'{_text(summary.get("latest_proactive_lifecycle_activation_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_activation_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_activation_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_activation_actionability"))}</p>'
            f'<p class="muted">lifecycle settlement '
            f'{_text(summary.get("latest_proactive_lifecycle_settlement_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_settlement_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_settlement_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_settlement_actionability"))}</p>'
            f'<p class="muted">lifecycle closure '
            f'{_text(summary.get("latest_proactive_lifecycle_closure_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_closure_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_closure_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_closure_actionability"))}</p>'
            f'<p class="muted">lifecycle availability '
            f'{_text(summary.get("latest_proactive_lifecycle_availability_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_availability_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_availability_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_availability_actionability"))}</p>'
            f'<p class="muted">lifecycle retention '
            f'{_text(summary.get("latest_proactive_lifecycle_retention_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_retention_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_retention_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_retention_actionability"))}</p>'
            f'<p class="muted">lifecycle eligibility '
            f'{_text(summary.get("latest_proactive_lifecycle_eligibility_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_eligibility_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_eligibility_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_eligibility_actionability"))}</p>'
            f'<p class="muted">lifecycle candidate '
            f'{_text(summary.get("latest_proactive_lifecycle_candidate_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_candidate_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_candidate_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_candidate_actionability"))}</p>'
            f'<p class="muted">lifecycle selectability '
            f'{_text(summary.get("latest_proactive_lifecycle_selectability_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_selectability_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_selectability_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_selectability_actionability"))}</p>'
            f'<p class="muted">lifecycle reentry '
            f'{_text(summary.get("latest_proactive_lifecycle_reentry_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_reentry_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_reentry_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_reentry_actionability"))}</p>'
            f'<p class="muted">lifecycle reactivation '
            f'{_text(summary.get("latest_proactive_lifecycle_reactivation_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_reactivation_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_reactivation_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_reactivation_actionability"))}</p>'
            f'<p class="muted">lifecycle resumption '
            f'{_text(summary.get("latest_proactive_lifecycle_resumption_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_resumption_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_resumption_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_resumption_actionability"))}</p>'
            f'<p class="muted">lifecycle readiness '
            f'{_text(summary.get("latest_proactive_lifecycle_readiness_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_readiness_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_readiness_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_readiness_actionability"))}</p>'
            f'<p class="muted">lifecycle arming '
            f'{_text(summary.get("latest_proactive_lifecycle_arming_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_arming_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_arming_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_arming_actionability"))}</p>'
            f'<p class="muted">lifecycle trigger '
            f'{_text(summary.get("latest_proactive_lifecycle_trigger_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_trigger_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_trigger_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_trigger_actionability"))}</p>'
            f'<p class="muted">lifecycle launch '
            f'{_text(summary.get("latest_proactive_lifecycle_launch_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_launch_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_launch_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_launch_actionability"))}</p>'
            f'<p class="muted">lifecycle handoff '
            f'{_text(summary.get("latest_proactive_lifecycle_handoff_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_handoff_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_handoff_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_handoff_actionability"))}</p>'
            f'<p class="muted">lifecycle continuation '
            f'{_text(summary.get("latest_proactive_lifecycle_continuation_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_continuation_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_continuation_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_continuation_actionability"))}</p>'
            f'<p class="muted">lifecycle sustainment '
            f'{_text(summary.get("latest_proactive_lifecycle_sustainment_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_sustainment_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_sustainment_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_sustainment_actionability"))}</p>'
            f'<p class="muted">lifecycle stewardship '
            f'{_text(summary.get("latest_proactive_lifecycle_stewardship_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_stewardship_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_stewardship_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_stewardship_actionability"))}</p>'
            f'<p class="muted">lifecycle guardianship '
            f'{_text(summary.get("latest_proactive_lifecycle_guardianship_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_guardianship_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_guardianship_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_guardianship_actionability"))}</p>'
            f'<p class="muted">lifecycle oversight '
            f'{_text(summary.get("latest_proactive_lifecycle_oversight_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_oversight_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_oversight_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_oversight_actionability"))}</p>'
            f'<p class="muted">lifecycle assurance '
            f'{_text(summary.get("latest_proactive_lifecycle_assurance_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_assurance_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_assurance_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_assurance_actionability"))}</p>'
            f'<p class="muted">lifecycle attestation '
            f'{_text(summary.get("latest_proactive_lifecycle_attestation_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_attestation_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_attestation_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_attestation_actionability"))}</p>'
            f'<p class="muted">lifecycle verification '
            f'{_text(summary.get("latest_proactive_lifecycle_verification_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_verification_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_verification_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_verification_actionability"))}</p>'
            f'<p class="muted">lifecycle certification '
            f'{_text(summary.get("latest_proactive_lifecycle_certification_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_certification_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_certification_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_certification_actionability"))}</p>'
            f'<p class="muted">lifecycle confirmation '
            f'{_text(summary.get("latest_proactive_lifecycle_confirmation_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_confirmation_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_confirmation_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_confirmation_actionability"))}</p>'
            f'<p class="muted">lifecycle ratification '
            f'{_text(summary.get("latest_proactive_lifecycle_ratification_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_ratification_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_ratification_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_ratification_actionability"))}</p>'
            f'<p class="muted">lifecycle endorsement '
            f'{_text(summary.get("latest_proactive_lifecycle_endorsement_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_endorsement_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_endorsement_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_endorsement_actionability"))}</p>'
            f'<p class="muted">lifecycle authorization '
            f'{_text(summary.get("latest_proactive_lifecycle_authorization_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_authorization_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_authorization_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_authorization_actionability"))}</p>'
            f'<p class="muted">lifecycle enactment '
            f'{_text(summary.get("latest_proactive_lifecycle_enactment_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_enactment_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_enactment_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_enactment_actionability"))}</p>'
            f'<p class="muted">lifecycle finality '
            f'{_text(summary.get("latest_proactive_lifecycle_finality_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_finality_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_finality_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_finality_actionability"))}</p>'
            f'<p class="muted">lifecycle completion '
            f'{_text(summary.get("latest_proactive_lifecycle_completion_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_completion_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_completion_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_completion_actionability"))}</p>'
            f'<p class="muted">lifecycle conclusion '
            f'{_text(summary.get("latest_proactive_lifecycle_conclusion_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_conclusion_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_conclusion_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_conclusion_actionability"))}</p>'
            f'<p class="muted">lifecycle disposition '
            f'{_text(summary.get("latest_proactive_lifecycle_disposition_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_disposition_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_disposition_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_disposition_actionability"))}</p>'
            f'<p class="muted">lifecycle standing '
            f'{_text(summary.get("latest_proactive_lifecycle_standing_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_standing_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_standing_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_standing_actionability"))}</p>'
            f'<p class="muted">lifecycle residency '
            f'{_text(summary.get("latest_proactive_lifecycle_residency_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_residency_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_residency_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_residency_actionability"))}</p>'
            f'<p class="muted">lifecycle tenure '
            f'{_text(summary.get("latest_proactive_lifecycle_tenure_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_tenure_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_tenure_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_tenure_actionability"))}</p>'
            f'<p class="muted">lifecycle persistence '
            f'{_text(summary.get("latest_proactive_lifecycle_persistence_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_persistence_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_persistence_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_persistence_actionability"))}</p>'
            f'<p class="muted">lifecycle durability '
            f'{_text(summary.get("latest_proactive_lifecycle_durability_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_durability_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_durability_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_durability_actionability"))}</p>'
            f'<p class="muted">lifecycle longevity '
            f'{_text(summary.get("latest_proactive_lifecycle_longevity_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_longevity_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_longevity_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_longevity_actionability"))}</p>'
            f'<p class="muted">lifecycle legacy '
            f'{_text(summary.get("latest_proactive_lifecycle_legacy_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_legacy_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_legacy_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_legacy_actionability"))}</p>'
            f'<p class="muted">lifecycle heritage '
            f'{_text(summary.get("latest_proactive_lifecycle_heritage_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_heritage_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_heritage_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_heritage_actionability"))}</p>'
            f'<p class="muted">lifecycle lineage '
            f'{_text(summary.get("latest_proactive_lifecycle_lineage_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_lineage_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_lineage_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_lineage_actionability"))}</p>'
            f'<p class="muted">lifecycle ancestry '
            f'{_text(summary.get("latest_proactive_lifecycle_ancestry_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_ancestry_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_ancestry_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_ancestry_actionability"))}</p>'
            f'<p class="muted">lifecycle provenance '
            f'{_text(summary.get("latest_proactive_lifecycle_provenance_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_provenance_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_provenance_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_provenance_actionability"))}</p>'
            f'<p class="muted">lifecycle origin '
            f'{_text(summary.get("latest_proactive_lifecycle_origin_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_origin_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_origin_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_origin_actionability"))}</p>'
            f'<p class="muted">lifecycle root '
            f'{_text(summary.get("latest_proactive_lifecycle_root_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_root_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_root_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_root_actionability"))}</p>'
            f'<p class="muted">lifecycle foundation '
            f'{_text(summary.get("latest_proactive_lifecycle_foundation_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_foundation_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_foundation_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_foundation_actionability"))}</p>'
            f'<p class="muted">lifecycle bedrock '
            f'{_text(summary.get("latest_proactive_lifecycle_bedrock_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_bedrock_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_bedrock_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_bedrock_actionability"))}</p>'
            f'<p class="muted">lifecycle substrate '
            f'{_text(summary.get("latest_proactive_lifecycle_substrate_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_substrate_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_substrate_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_substrate_actionability"))}</p>'
            f'<p class="muted">lifecycle stratum '
            f'{_text(summary.get("latest_proactive_lifecycle_stratum_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_stratum_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_stratum_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_stratum_actionability"))}</p>'
            f'<p class="muted">lifecycle layer '
            f'{_text(summary.get("latest_proactive_lifecycle_layer_key"))} · '
            f'{_text(summary.get("latest_proactive_lifecycle_layer_mode"))} · '
            f'decision {_text(summary.get("latest_proactive_lifecycle_layer_decision"))} · '
            f'action '
            f'{_text(summary.get("latest_proactive_lifecycle_layer_actionability"))}</p>'
            f'<p class="muted">follow-up cadence '
            f'{_text(summary.get("latest_proactive_cadence_key"))} · '
            f'stages {_text(summary.get("latest_proactive_cadence_stage_count"))} · '
            f'plans {_text(summary.get("proactive_cadence_plan_count"))} · '
            f'scheduled {_text(summary.get("proactive_scheduling_deferred_turn_count"))}</p>'
            f'<p class="muted">aggregate governance '
            f'{_text(summary.get("latest_proactive_aggregate_governance_status"))} · '
            f'primary '
            f'{_text(summary.get("latest_proactive_aggregate_governance_primary_domain"))} · '
            f'domains {_text(summary.get("latest_proactive_aggregate_governance_domain_count"))} · '
            f'{_text(summary.get("latest_proactive_aggregate_governance_summary"))}</p>'
            f'<p class="muted">aggregate controller '
            f'{_text(summary.get("latest_proactive_aggregate_controller_key"))} · '
            f'{_text(summary.get("latest_proactive_aggregate_controller_decision"))} · '
            f'stage delay '
            f'{_text(summary.get("latest_proactive_aggregate_controller_stage_delay_seconds"))}</p>'
            f'<p class="muted">orchestration controller '
            f'{_text(summary.get("latest_proactive_orchestration_controller_key"))} · '
            f'{_text(summary.get("latest_proactive_orchestration_controller_decision"))} · '
            f'source '
            f'{_text(summary.get("latest_proactive_orchestration_controller_primary_source"))} · '
            f'stage delay '
            f'{_text(summary.get("latest_proactive_orchestration_controller_stage_delay_seconds"))}</p>'
            f'<p class="muted">follow-up guardrail '
            f'{_text(summary.get("latest_proactive_guardrail_key"))} · '
            f'max {_text(summary.get("latest_proactive_guardrail_max_dispatch_count"))} · '
            f'hard stops {_text(summary.get("latest_proactive_guardrail_hard_stop_count"))}</p>'
            f'<p class="muted">re-engagement matrix '
            f'{_text(summary.get("latest_reengagement_matrix_key"))} · '
            f'selected '
            f'{_text(summary.get("latest_reengagement_matrix_selected_strategy"))} · '
            f'learn {_text(summary.get("latest_reengagement_matrix_learning_mode"))} · '
            f'alt {_text(summary.get("latest_reengagement_matrix_top_alternative"))}</p>'
            f'<p class="muted">re-engagement '
            f'{_text(summary.get("latest_reengagement_ritual_mode"))} · '
            f'strategy {_text(summary.get("latest_reengagement_strategy_key"))} · '
            f'pressure {_text(summary.get("latest_reengagement_pressure_mode"))}</p>'
            f'<p class="muted">re-engagement detail '
            f'delivery {_text(summary.get("latest_reengagement_delivery_mode"))} · '
            f'autonomy {_text(summary.get("latest_reengagement_autonomy_signal"))} · '
            f'ctx {_text(summary.get("latest_reengagement_matrix_learning_context_stratum"))} · '
            f'blocked {_text(summary.get("latest_reengagement_matrix_blocked_count"))} · '
            f'planned {_text(summary.get("reengagement_plan_count"))}</p>'
            f'<p class="muted">dispatch '
            f'{_text(summary.get("latest_proactive_followup_dispatch_status"))} · '
            f'source {_text(summary.get("latest_proactive_followup_dispatch_source"))} · '
            f'count {_text(summary.get("proactive_followup_dispatch_count"))} · '
            f'stage {_text(summary.get("latest_proactive_followup_dispatch_stage_label"))}</p>'
            f'<p class="muted">dispatch progression '
            f'{_text(summary.get("latest_proactive_followup_dispatch_progression_action"))} · '
            f'advanced '
            f'{_text(summary.get("latest_proactive_followup_dispatch_progression_advanced"))} · '
            f'auto-advanced '
            f'{_text(summary.get("proactive_followup_dispatch_progression_advanced_count"))}</p>'
            f'<p class="muted">quality doctor '
            f'{_text(summary.get("latest_runtime_quality_doctor_status"))} · '
            f'issues {_text(summary.get("latest_runtime_quality_doctor_issue_count"))} · '
            f'reports {_text(summary.get("runtime_quality_doctor_report_count"))}</p>'
            f'<p class="muted">system3 '
            f'{_text(summary.get("latest_system3_growth_stage"))} · '
            f'identity {_text(summary.get("latest_system3_identity_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_identity_trajectory_target"))} · '
            f'transition {_text(summary.get("latest_system3_growth_transition_status"))} · '
            f'target {_text(summary.get("latest_system3_growth_transition_target"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_growth_transition_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_growth_transition_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_growth_transition_trajectory_trigger"))} · '
            f'model {_text(summary.get("latest_system3_user_model_evolution_status"))} · '
            f'{_text(summary.get("latest_system3_user_model_revision_mode"))} · '
            f'shift {_text(summary.get("latest_system3_user_model_shift_signal"))} · '
            f'trajectory {_text(summary.get("latest_system3_user_model_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_user_model_trajectory_target"))} · '
            f'trigger {_text(summary.get("latest_system3_user_model_trajectory_trigger"))} · '
            f'expectation {_text(summary.get("latest_system3_expectation_calibration_status"))} · '
            f'{_text(summary.get("latest_system3_expectation_calibration_target"))} · '
            f'trigger {_text(summary.get("latest_system3_expectation_calibration_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_expectation_calibration_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_expectation_calibration_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_expectation_calibration_trajectory_trigger"))} · '
            f'dependency {_text(summary.get("latest_system3_dependency_governance_status"))} · '
            f'{_text(summary.get("latest_system3_dependency_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_dependency_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_dependency_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_dependency_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_dependency_governance_trajectory_trigger"))} · '
            f'autonomy {_text(summary.get("latest_system3_autonomy_governance_status"))} · '
            f'{_text(summary.get("latest_system3_autonomy_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_autonomy_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_autonomy_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_autonomy_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_autonomy_governance_trajectory_trigger"))} · '
            f'boundary {_text(summary.get("latest_system3_boundary_governance_status"))} · '
            f'{_text(summary.get("latest_system3_boundary_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_boundary_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_boundary_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_boundary_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_boundary_governance_trajectory_trigger"))} · '
            f'support {_text(summary.get("latest_system3_support_governance_status"))} · '
            f'{_text(summary.get("latest_system3_support_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_support_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_support_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_support_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_support_governance_trajectory_trigger"))} · '
            f'continuity {_text(summary.get("latest_system3_continuity_governance_status"))} · '
            f'{_text(summary.get("latest_system3_continuity_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_continuity_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_continuity_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_continuity_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_continuity_governance_trajectory_trigger"))} · '
            f'repair {_text(summary.get("latest_system3_repair_governance_status"))} · '
            f'{_text(summary.get("latest_system3_repair_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_repair_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_repair_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_repair_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_repair_governance_trajectory_trigger"))} · '
            f'attunement {_text(summary.get("latest_system3_attunement_governance_status"))} · '
            f'{_text(summary.get("latest_system3_attunement_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_attunement_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_attunement_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_attunement_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_attunement_governance_trajectory_trigger"))} · '
            f'trust {_text(summary.get("latest_system3_trust_governance_status"))} · '
            f'{_text(summary.get("latest_system3_trust_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_trust_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_trust_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_trust_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_trust_governance_trajectory_trigger"))} · '
            f'clarity {_text(summary.get("latest_system3_clarity_governance_status"))} · '
            f'{_text(summary.get("latest_system3_clarity_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_clarity_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_clarity_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_clarity_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_clarity_governance_trajectory_trigger"))} · '
            f'pacing {_text(summary.get("latest_system3_pacing_governance_status"))} · '
            f'{_text(summary.get("latest_system3_pacing_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_pacing_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_pacing_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_pacing_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_pacing_governance_trajectory_trigger"))} · '
            f'commitment {_text(summary.get("latest_system3_commitment_governance_status"))} · '
            f'{_text(summary.get("latest_system3_commitment_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_commitment_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_commitment_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_commitment_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_commitment_governance_trajectory_trigger"))} · '
            f'disclosure {_text(summary.get("latest_system3_disclosure_governance_status"))} · '
            f'{_text(summary.get("latest_system3_disclosure_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_disclosure_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_disclosure_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_disclosure_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_disclosure_governance_trajectory_trigger"))} · '
            f'reciprocity {_text(summary.get("latest_system3_reciprocity_governance_status"))} · '
            f'{_text(summary.get("latest_system3_reciprocity_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_reciprocity_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_reciprocity_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_reciprocity_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_reciprocity_governance_trajectory_trigger"))} · '
            f'pressure {_text(summary.get("latest_system3_pressure_governance_status"))} · '
            f'{_text(summary.get("latest_system3_pressure_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_pressure_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_pressure_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_pressure_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_pressure_governance_trajectory_trigger"))} · '
            f'relational {_text(summary.get("latest_system3_relational_governance_status"))} · '
            f'{_text(summary.get("latest_system3_relational_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_relational_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_relational_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_relational_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_relational_governance_trajectory_trigger"))} · '
            f'safety {_text(summary.get("latest_system3_safety_governance_status"))} · '
            f'{_text(summary.get("latest_system3_safety_governance_target"))} · '
            f'trigger {_text(summary.get("latest_system3_safety_governance_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_safety_governance_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_safety_governance_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_safety_governance_trajectory_trigger"))} · '
            f'migration {_text(summary.get("latest_system3_version_migration_status"))} · '
            f'{_text(summary.get("latest_system3_version_migration_scope"))} · '
            f'trigger {_text(summary.get("latest_system3_version_migration_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_version_migration_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_version_migration_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_version_migration_trajectory_trigger"))} · '
            f'supervision {_text(summary.get("latest_system3_strategy_supervision_status"))} · '
            f'{_text(summary.get("latest_system3_strategy_supervision_mode"))} · '
            f'trigger {_text(summary.get("latest_system3_strategy_supervision_trigger"))} · '
            f'trajectory '
            f'{_text(summary.get("latest_system3_strategy_supervision_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_strategy_supervision_trajectory_target"))} · '
            f'trigger '
            f'{_text(summary.get("latest_system3_strategy_supervision_trajectory_trigger"))} · '
            f'moral {_text(summary.get("latest_system3_moral_reasoning_status"))} · '
            f'{_text(summary.get("latest_system3_moral_posture"))} · '
            f'conflict {_text(summary.get("latest_system3_moral_conflict"))} · '
            f'trajectory {_text(summary.get("latest_system3_moral_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_moral_trajectory_target"))} · '
            f'trigger {_text(summary.get("latest_system3_moral_trajectory_trigger"))} · '
            f'audit {_text(summary.get("latest_system3_strategy_audit_status"))} · '
            f'trajectory {_text(summary.get("latest_system3_strategy_audit_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_strategy_audit_trajectory_target"))} · '
            f'trigger {_text(summary.get("latest_system3_strategy_audit_trajectory_trigger"))} · '
            f'debt {_text(summary.get("latest_system3_emotional_debt_status"))} · '
            f'trajectory {_text(summary.get("latest_system3_emotional_debt_trajectory_status"))} · '
            f'{_text(summary.get("latest_system3_emotional_debt_trajectory_target"))}</p>'
            f'<p class="muted">safety {_text(summary.get("avg_psychological_safety"))} · '
            f'pinned {summary.get("latest_memory_pinned_count", 0)} · '
            f'evicted {summary.get("latest_memory_evicted_count", 0)}</p>'
            "</button>"
            "</article>"
        )
    return preference_html + "".join(items)


async def _render_scenarios_fragment(
    *,
    request: Request,
    container: RuntimeContainer,
) -> str:
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
    visible_trends = [
        trend for trend in trends if int(trend.get("total_runs") or 0) > 0
    ] or trends[:LIST_LIMIT]
    release_gate = dict(ship_readiness.get("release_gate") or {})
    report = dict(release_gate.get("report") or {})
    watchlist = list(report.get("watchlist", []))
    baseline = report.get("baseline")
    gate_focus_areas = list(release_gate.get("focus_areas", []))
    coverage = dict(report.get("coverage") or {})
    horizon_summary = dict(horizon_report.get("summary") or {})
    multiweek_summary = dict(multiweek_report.get("summary") or {})
    sustained_drift_summary = dict(sustained_drift_report.get("summary") or {})
    longitudinal_summary = dict(longitudinal_report.get("summary") or {})
    readiness_summary = dict(ship_readiness.get("summary") or {})
    baseline_governance_summary = dict(
        baseline_governance_report.get("summary") or {}
    )
    migration_readiness_summary = dict(migration_readiness_report.get("summary") or {})
    hardening_summary = dict(hardening_checklist.get("summary") or {})
    release_dossier_summary = dict(release_dossier.get("summary") or {})
    launch_signoff_summary = dict(launch_signoff.get("summary") or {})
    safety_audit_summary = dict(safety_audit_report.get("summary") or {})
    redteam_summary = dict(redteam_report.get("summary") or {})
    taxonomy_items = list(misalignment_report.get("taxonomies", []))
    incident_items = list(misalignment_report.get("incidents", []))

    if list(longitudinal_report.get("focus_areas", [])):
        longitudinal_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("type"), tone="neutral")}'
                f'{_badge(longitudinal_report.get("status"))}'
                "</div>"
                f'<p>{_text(item.get("detail"))}</p>'
                "</article>"
            )
            for item in list(longitudinal_report.get("focus_areas", []))[:3]
        )
    else:
        longitudinal_cards = _empty_state(
            "Longitudinal report is calm",
            "Recent and prior cohorts are not showing additional drift right now.",
        )

    if list(horizon_report.get("focus_areas", [])):
        horizon_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("type"), tone="neutral")}'
                f'{_badge(horizon_report.get("status"))}'
                "</div>"
                f'<p>{_text(item.get("detail"))}</p>'
                "</article>"
            )
            for item in list(horizon_report.get("focus_areas", []))[:3]
        )
    else:
        horizon_cards = _empty_state(
            "Horizon report is calm",
            "Short, medium, and long windows are not showing additional drift.",
        )

    horizon_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Horizon Report</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", horizon_report.get("status"))}'
        f'{_labeled_value("Short Runs", horizon_summary.get("short_run_count"))}'
        f'{_labeled_value("Medium Runs", horizon_summary.get("medium_run_count"))}'
        f'{_labeled_value("Long Runs", horizon_summary.get("long_run_count"))}'
        f'{_labeled_value("Short/Medium Pass", horizon_summary.get(
            "short_vs_medium_pass_rate_delta"
        ))}'
        f'{_labeled_value("Short/Long Pass", horizon_summary.get(
            "short_vs_long_pass_rate_delta"
        ))}'
        f'{_labeled_value("Latest Quality", horizon_summary.get("latest_output_quality_status"))}'
        f'{_labeled_value("Latest Boundary", horizon_summary.get(
            "latest_redteam_boundary_decision"
        ))}'
        "</div>"
        f'<div class="signal-list">{horizon_cards}</div>'
        "</section>"
    )

    if list(multiweek_report.get("focus_areas", [])):
        multiweek_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("type"), tone="neutral")}'
                f'{_badge(multiweek_report.get("status"))}'
                "</div>"
                f'<p>{_text(item.get("detail"))}</p>'
                "</article>"
            )
            for item in list(multiweek_report.get("focus_areas", []))[:3]
        )
    else:
        multiweek_cards = _empty_state(
            "Multiweek report is calm",
            "Recent weekly buckets are not showing additional drift.",
        )

    multiweek_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Multiweek Report</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", multiweek_report.get("status"))}'
        f'{_labeled_value("Bucket Days", multiweek_summary.get("bucket_days"))}'
        f'{_labeled_value("Buckets", multiweek_summary.get("bucket_count"))}'
        f'{_labeled_value("Latest Bucket", multiweek_summary.get("latest_bucket_label"))}'
        f'{_labeled_value("Prior Bucket", multiweek_summary.get("prior_bucket_label"))}'
        f'{_labeled_value("Pass Delta", multiweek_summary.get("overall_pass_rate_delta"))}'
        f'{_labeled_value("Quality Watch Delta", multiweek_summary.get("quality_watch_delta"))}'
        f'{_labeled_value("Boundary Guard Delta", multiweek_summary.get(
            "redteam_boundary_guard_delta"
        ))}'
        "</div>"
        f'<div class="signal-list">{multiweek_cards}</div>'
        "</section>"
    )

    if list(sustained_drift_report.get("focus_areas", [])):
        sustained_drift_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("type"), tone="neutral")}'
                f'{_badge(sustained_drift_report.get("status"))}'
                "</div>"
                f'<p>{_text(item.get("detail"))}</p>'
                "</article>"
            )
            for item in list(sustained_drift_report.get("focus_areas", []))[:3]
        )
    else:
        sustained_drift_cards = _empty_state(
            "Sustained drift is calm",
            "Recent weekly buckets are not showing a sustained worsening streak.",
        )

    sustained_drift_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Sustained Drift</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", sustained_drift_report.get("status"))}'
        f'{_labeled_value("Buckets", sustained_drift_summary.get("bucket_count"))}'
        f'{_labeled_value("Min Streak", sustained_drift_summary.get("min_streak"))}'
        f'{_labeled_value("Pass Decline", sustained_drift_summary.get("pass_rate_decline_streak"))}'
        f'{_labeled_value("Quality Growth", sustained_drift_summary.get(
            "quality_watch_growth_streak"
        ))}'
        f'{_labeled_value("Redteam Decline", sustained_drift_summary.get(
            "redteam_pass_rate_decline_streak"
        ))}'
        f'{_labeled_value("Guard Decline", sustained_drift_summary.get(
            "boundary_guard_decline_streak"
        ))}'
        f'{_labeled_value("Latest Bucket", sustained_drift_summary.get("latest_bucket_label"))}'
        "</div>"
        f'<div class="signal-list">{sustained_drift_cards}</div>'
        "</section>"
    )

    longitudinal_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Longitudinal Report</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", longitudinal_report.get("status"))}'
        f'{_labeled_value("Recent Runs", longitudinal_summary.get("recent_run_count"))}'
        f'{_labeled_value("Prior Runs", longitudinal_summary.get("prior_run_count"))}'
        f'{_labeled_value("Pass Delta", longitudinal_summary.get("overall_pass_rate_delta"))}'
        f'{_labeled_value("Quality Watch Delta", longitudinal_summary.get("quality_watch_delta"))}'
        f'{_labeled_value("Redteam Pass Delta", longitudinal_summary.get(
            "redteam_pass_rate_delta"
        ))}'
        f'{_labeled_value("Boundary Guard Delta", longitudinal_summary.get(
            "redteam_boundary_guard_delta"
        ))}'
        "</div>"
        f'<div class="signal-list">{longitudinal_cards}</div>'
        "</section>"
    )

    if list(release_dossier.get("actions", [])):
        release_dossier_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(release_dossier.get("status"))}'
                "</div>"
                "</article>"
            )
            for action in list(release_dossier.get("actions", []))[:4]
        )
    else:
        release_dossier_cards = _empty_state(
            "Release dossier is clean",
            "The current candidate has no open final release dossier actions.",
        )

    release_dossier_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Release Dossier</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", release_dossier.get("status"))}'
        f'{_labeled_value("Release Gate", release_dossier_summary.get("release_gate_status"))}'
        f'{_labeled_value("Ship Readiness", release_dossier_summary.get("ship_readiness_status"))}'
        f'{_labeled_value("Hardening", release_dossier_summary.get("hardening_checklist_status"))}'
        f'{_labeled_value("Safety Audit", release_dossier_summary.get("safety_audit_status"))}'
        f'{_labeled_value("Redteam", release_dossier_summary.get("redteam_report_status"))}'
        f'{_labeled_value("Baseline Gov", release_dossier_summary.get(
            "baseline_governance_status"
        ))}'
        f'{_labeled_value("Migration", release_dossier_summary.get(
            "migration_readiness_status"
        ))}'
        f'{_labeled_value("Longitudinal", release_dossier_summary.get(
            "longitudinal_report_status"
        ))}'
        "</div>"
        f'<div class="signal-list">{release_dossier_cards}</div>'
        "</section>"
    )

    if list(launch_signoff.get("domains", [])):
        launch_signoff_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(domain.get("domain"))}</div>'
                '<div class="list-meta">'
                f'{_badge(domain.get("signoff"))}'
                f'{_badge(domain.get("status"))}'
                f'{_badge(domain.get("owner"), tone="neutral")}'
                "</div>"
                f'<p>{_text(domain.get("detail"))}</p>'
                f'<p class="muted">sources {_text(", ".join(domain.get("sources", [])))}</p>'
                "</article>"
            )
            for domain in list(launch_signoff.get("domains", []))[:4]
        )
    else:
        launch_signoff_cards = _empty_state(
            "Launch signoff is empty",
            "The final launch signoff matrix will appear here once release reports are available.",
        )

    launch_signoff_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Launch Signoff</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", launch_signoff.get("status"))}'
        f'{_labeled_value("Approved Domains", launch_signoff_summary.get("approved_domain_count"))}'
        f'{_labeled_value("Review Domains", launch_signoff_summary.get("review_domain_count"))}'
        f'{_labeled_value("Hold Domains", launch_signoff_summary.get("hold_domain_count"))}'
        f'{_labeled_value("Release Dossier", launch_signoff_summary.get("release_dossier_status"))}'
        f'{_labeled_value("Runtime", launch_signoff_summary.get("ship_readiness_status"))}'
        f'{_labeled_value("Safety", launch_signoff_summary.get("safety_barriers_status"))}'
        f'{_labeled_value("Governance", launch_signoff_summary.get("governance_status"))}'
        f'{_labeled_value("Migration", launch_signoff_summary.get("migration_readiness_status"))}'
        "</div>"
        f'<div class="signal-list">{launch_signoff_cards}</div>'
        "</section>"
    )

    if list(hardening_checklist.get("actions", [])):
        hardening_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(hardening_checklist.get("status"))}'
                "</div>"
                "</article>"
            )
            for action in list(hardening_checklist.get("actions", []))[:4]
        )
    else:
        hardening_cards = _empty_state(
            "Hardening checklist is clean",
            "No extra hardening actions are active right now.",
        )

    hotspot_label = None
    if hardening_summary.get("hotspot_taxonomy_type"):
        hotspot_label = (
            f"{hardening_summary.get('hotspot_taxonomy_type')} "
            f"({hardening_summary.get('hotspot_taxonomy_count')})"
        )

    hardening_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Hardening Checklist</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", hardening_checklist.get("status"))}'
        f'{_labeled_value("Ship Readiness", hardening_summary.get("ship_readiness_status"))}'
        f'{_labeled_value("Critical Taxonomies", hardening_summary.get("critical_taxonomy_count"))}'
        f'{_labeled_value("Redteam Critical", hardening_summary.get(
            "redteam_critical_incident_count"
        ))}'
        f'{_labeled_value("Quality Taxonomies", hardening_summary.get("quality_taxonomy_count"))}'
        f'{_labeled_value("System3 Taxonomies", hardening_summary.get("system3_taxonomy_count"))}'
        f'{_labeled_value("Hotspot", hotspot_label)}'
        "</div>"
        f'<div class="signal-list">{hardening_cards}</div>'
        "</section>"
    )

    if list(safety_audit_report.get("actions", [])):
        safety_audit_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(safety_audit_report.get("status"))}'
                "</div>"
                "</article>"
            )
            for action in list(safety_audit_report.get("actions", []))[:3]
        )
    else:
        safety_audit_cards = _empty_state(
            "Safety audit is clean",
            "No immediate boundary or replay safety actions are active right now.",
        )

    safety_audit_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Safety Audit</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", safety_audit_report.get("status"))}'
        f'{_labeled_value("Scenario Results", safety_audit_summary.get("scenario_result_count"))}'
        f'{_labeled_value("Redteam Results", safety_audit_summary.get("redteam_result_count"))}'
        f'{_labeled_value("Critical Boundary", safety_audit_summary.get(
            "critical_boundary_incident_count"
        ))}'
        f'{_labeled_value("Replay Drift", safety_audit_summary.get("audit_inconsistent_count"))}'
        f'{_labeled_value("Boundary Guard Rate", safety_audit_summary.get(
            "redteam_boundary_guard_rate"
        ))}'
        f'{_labeled_value("Post-Audit Violations", safety_audit_summary.get(
            "post_audit_violation_result_count"
        ))}'
        "</div>"
        f'<div class="signal-list">{safety_audit_cards}</div>'
        "</section>"
    )

    if list(redteam_report.get("actions", [])):
        redteam_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(redteam_report.get("status"))}'
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
                f'{_badge(item.get("status"))}'
                f'{_badge(item.get("latest_boundary_decision"), tone="neutral")}'
                "</div>"
                f'<p>policy path {_text(item.get("latest_policy_path"))} · '
                f'guarded {_text(item.get("policy_gate_guarded_turn_count"))}</p>'
                f'<p class="muted">{_text(item.get("run_id"))}</p>'
                "</article>"
            )
            for item in list(redteam_report.get("recent_results", []))[:3]
        )
    else:
        redteam_cards = _empty_state(
            "No redteam coverage",
            "Run the redteam scenario set and this panel will summarize robustness.",
        )

    redteam_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Redteam Robustness</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", redteam_report.get("status"))}'
        f'{_labeled_value("Recent Results", redteam_summary.get("redteam_result_count"))}'
        f'{_labeled_value("Pass Rate", redteam_summary.get("redteam_pass_rate"))}'
        f'{_labeled_value("Critical Incidents", redteam_summary.get(
            "critical_redteam_incident_count"
        ))}'
        f'{_labeled_value("Latest Boundary", redteam_summary.get(
            "latest_redteam_boundary_decision"
        ))}'
        f'{_labeled_value("Latest Policy Path", redteam_summary.get("latest_redteam_policy_path"))}'
        "</div>"
        f'<div class="signal-list">{redteam_cards}</div>'
        "</section>"
    )

    if list(ship_readiness.get("actions", [])):
        ship_readiness_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(ship_readiness.get("status"))}'
                "</div>"
                "</article>"
            )
            for action in list(ship_readiness.get("actions", []))[:4]
        )
    else:
        ship_readiness_cards = _empty_state(
            "Ship checklist is clean",
            "No open ship-readiness actions are active right now.",
        )

    ship_readiness_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Ship Readiness</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", ship_readiness.get("status"))}'
        f'{_labeled_value("Release Gate", readiness_summary.get("release_gate_status"))}'
        f'{_labeled_value("Worker", readiness_summary.get("worker_id"))}'
        f'{_labeled_value("Poller", readiness_summary.get("poller_running"))}'
        f'{_labeled_value("Pending Jobs", readiness_summary.get("pending_job_count"))}'
        f'{_labeled_value("Active Jobs", readiness_summary.get("active_job_count"))}'
        f'{_labeled_value("Retryable Failed", readiness_summary.get("retryable_failed_job_count"))}'
        f'{_labeled_value("Expired Claims", readiness_summary.get("expired_claim_job_count"))}'
        "</div>"
        f'<div class="signal-list">{ship_readiness_cards}</div>'
        "</section>"
    )

    if list(migration_readiness_report.get("actions", [])):
        migration_readiness_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(migration_readiness_report.get("status"))}'
                "</div>"
                "</article>"
            )
            for action in list(migration_readiness_report.get("actions", []))[:4]
        )
    elif list(migration_readiness_report.get("focus_areas", [])):
        migration_readiness_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("type"), tone="neutral")}'
                f'{_badge(migration_readiness_report.get("status"))}'
                "</div>"
                f'<p>{_text(item.get("detail"))}</p>'
                "</article>"
            )
            for item in list(migration_readiness_report.get("focus_areas", []))[:3]
        )
    else:
        migration_readiness_cards = _empty_state(
            "Migration readiness is clean",
            "Recent projector replay samples are consistent across the current registry.",
        )

    migration_readiness_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Migration Readiness</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", migration_readiness_report.get("status"))}'
        f'{_labeled_value("Projectors", migration_readiness_summary.get(
            "registered_projector_count"
        ))}'
        f'{_labeled_value("Sample Source", migration_readiness_summary.get("sample_source"))}'
        f'{_labeled_value("Sampled Streams", migration_readiness_summary.get(
            "sampled_stream_count"
        ))}'
        f'{_labeled_value("Primary Samples", migration_readiness_summary.get(
            "primary_sample_stream_count"
        ))}'
        f'{_labeled_value("Fallback Samples", migration_readiness_summary.get(
            "fallback_sample_stream_count"
        ))}'
        f'{_labeled_value("Checked Projections", migration_readiness_summary.get(
            "checked_projection_count"
        ))}'
        f'{_labeled_value("Replay Drift", migration_readiness_summary.get(
            "inconsistent_projection_count"
        ))}'
        "</div>"
        f'<div class="signal-list">{migration_readiness_cards}</div>'
        "</section>"
    )

    if list(baseline_governance_report.get("actions", [])):
        baseline_governance_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(action)}</div>'
                '<div class="list-meta">'
                f'{_badge(baseline_governance_report.get("status"))}'
                "</div>"
                "</article>"
            )
            for action in list(baseline_governance_report.get("actions", []))[:4]
        )
    else:
        baseline_governance_cards = _empty_state(
            "Baseline governance is healthy",
            "The pinned baseline still looks usable for release comparisons.",
        )

    baseline_governance_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Baseline Governance</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", baseline_governance_report.get("status"))}'
        f'{_labeled_value("Label", baseline_governance_summary.get("baseline_label"))}'
        f'{_labeled_value("Baseline Run", baseline_governance_summary.get("baseline_run_id"))}'
        f'{_labeled_value("Newer Runs", baseline_governance_summary.get("newer_run_count"))}'
        f'{_labeled_value("Age Days", baseline_governance_summary.get("baseline_age_days"))}'
        f'{_labeled_value("Overall Delta", baseline_governance_summary.get("overall_delta"))}'
        f'{_labeled_value("Changed Scenarios", baseline_governance_summary.get(
            "changed_scenario_count"
        ))}'
        f'{_labeled_value("Note", baseline_governance_summary.get("baseline_note_present"))}'
        "</div>"
        f'<div class="signal-list">{baseline_governance_cards}</div>'
        "</section>"
    )

    if taxonomy_items:
        taxonomy_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("type"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("module"), tone="neutral")}'
                f'{_badge(item.get("count"))}'
                "</div>"
                f'<p>scenarios {_text(item.get("scenario_count"))} · runs '
                f'{_text(item.get("run_count"))}</p>'
                "</article>"
            )
            for item in taxonomy_items[:4]
        )
    else:
        taxonomy_cards = _empty_state(
            "No misalignment incidents",
            "Recent scenario runs have not produced failed taxonomy incidents yet.",
        )

    if incident_items:
        incident_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("taxonomy_type"))}'
                f'{_badge(item.get("module"), tone="neutral")}'
                "</div>"
                f'<p>{_text(item.get("metric"))} · actual {_text(item.get("actual"))} · '
                f'expected {_text(item.get("expected"))}</p>'
                f'<p class="muted">{_text(item.get("run_id"))}</p>'
                "</article>"
            )
            for item in incident_items[:4]
        )
    else:
        incident_cards = _empty_state(
            "No recent incidents",
            "Scenario failures will appear here as soon as a check regresses.",
        )

    misalignment_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Misalignment Taxonomy</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Window", misalignment_report.get("window"))}'
        f'{_labeled_value("Runs", misalignment_report.get("run_count"))}'
        f'{_labeled_value("Incidents", misalignment_report.get("incident_count"))}'
        f'{_labeled_value("Taxonomies", misalignment_report.get("taxonomy_count"))}'
        "</div>"
        f'<div class="signal-list">{taxonomy_cards}{incident_cards}</div>'
        "</section>"
    )

    if gate_focus_areas:
        gate_focus_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("type"), tone="neutral")}'
                f'{_badge(release_gate.get("status"))}'
                "</div>"
                f'<p>{_text(item.get("detail"))}</p>'
                "</article>"
            )
            for item in gate_focus_areas
        )
    else:
        gate_focus_cards = _empty_state(
            "Gate is clean",
            "No unstable or baseline-drift focus areas are active right now.",
        )

    release_gate_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Release Gate</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Status", release_gate.get("status"))}'
        f'{_labeled_value("Latest Run", release_gate.get("latest_run_id"))}'
        f'{_labeled_value("Pass Rate", release_gate.get("overall_pass_rate"))}'
        f'{_labeled_value("Unstable", release_gate.get("unstable_scenario_count"))}'
        f'{_labeled_value("Recent Coverage", coverage.get("recent_covered_scenario_count"))}'
        f'{_labeled_value("Latest Suite Size", coverage.get("latest_run_scenario_count"))}'
        f'{_labeled_value("Blocked Reasons", release_gate.get("blocked_reason_count"))}'
        f'{_labeled_value("Review Reasons", release_gate.get("review_reason_count"))}'
        "</div>"
        f'<div class="signal-list">{gate_focus_cards}</div>'
        "</section>"
    )

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
                    f'{_badge(item.get("status_delta"))}'
                    f'{_badge(item.get("baseline_status"), tone="neutral")}'
                    f'{_badge(item.get("candidate_status"))}'
                    "</div>"
                    f'<p>baseline {_text(baseline.get("baseline_label"))} · checks '
                    f'{_text(item.get("baseline_passed_checks"))} → '
                    f'{_text(item.get("candidate_passed_checks"))}</p>'
                    "</article>"
                )
                for item in baseline_changed[:4]
            )
        else:
            baseline_cards = _empty_state(
                "Baseline is holding",
                "The latest run matches the current baseline without scenario drift.",
            )
        baseline_html = (
            '<section class="fragment-section">'
            '<div class="section-header"><h2>Baseline Track</h2></div>'
            '<div class="kv-grid">'
            f'{_labeled_value("Label", baseline.get("baseline_label"))}'
            f'{_labeled_value("Baseline Run", baseline.get("baseline_run_id"))}'
            f'{_labeled_value("Latest Run", baseline.get("candidate_run_id"))}'
            f'{_labeled_value("Overall Delta", baseline.get("overall_delta"))}'
            f'{_labeled_value("Changed Scenarios", baseline.get("changed_scenario_count"))}'
            f'{_labeled_value("Baseline Set", _timestamp(baseline.get("baseline_set_at")))}'
            "</div>"
            f'<div class="signal-list">{baseline_cards}</div>'
            "</section>"
        )
    else:
        empty_baseline = _empty_state(
            "No baseline pinned",
            "Set a default scenario baseline and this panel will track latest vs baseline.",
        )
        baseline_html = (
            '<section class="fragment-section">'
            '<div class="section-header"><h2>Baseline Track</h2></div>'
            f"{empty_baseline}"
            "</section>"
        )

    if watchlist:
        stability_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(item.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(item.get("stability"))}'
                f'{_badge(item.get("latest_status"))}'
                f'{_badge(item.get("status_delta"))}'
                "</div>"
                f'<p>pass rate {_text(item.get("pass_rate"))} · regressions '
                f'{_text(item.get("regression_count"))} · changes '
                f'{_text(item.get("changed_count"))}</p>'
                f'<p class="muted">latest run {_text(item.get("latest_run_id"))} · '
                f'window {_text(item.get("recent_run_count"))}</p>'
                "</article>"
            )
            for item in watchlist
        )
    else:
        stability_cards = _empty_state(
            "No report yet",
            "Run the suite a few times and this panel will summarize long-range stability.",
        )

    regression_count = (
        report.get("comparison_delta_counts", {}).get("regressed")
        if isinstance(report.get("comparison_delta_counts"), dict)
        else None
    )
    stability_report_html = (
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Stability Report</h2></div>'
        '<div class="kv-grid">'
        f'{_labeled_value("Window", report.get("window"))}'
        f'{_labeled_value("Runs", report.get("run_count"))}'
        f'{_labeled_value("Pass Rate", report.get("overall_pass_rate"))}'
        f'{_labeled_value("Latest Status", report.get("latest_overall_status"))}'
        f'{_labeled_value("Regressions", regression_count)}'
        f'{_labeled_value("Watchlist", report.get("unstable_scenario_count"))}'
        "</div>"
        f'<div class="signal-list">{stability_cards}</div>'
        "</section>"
    )
    comparison: dict[str, Any] | None = None
    if len(runs) >= 2:
        comparison = await container.scenario_evaluation_service.compare_runs(
            baseline_run_id=str(runs[1]["run_id"]),
            candidate_run_id=str(runs[0]["run_id"]),
        )

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
                    f'{_badge(item.get("status_delta"))}'
                    f'{_badge(item.get("baseline_status"), tone="neutral")}'
                    f'{_badge(item.get("candidate_status"))}'
                    "</div>"
                    f'<p>checks {_text(item.get("baseline_passed_checks"))} → '
                    f'{_text(item.get("candidate_passed_checks"))} of '
                    f'{_text(item.get("check_count"))}</p>'
                    '<p class="muted">'
                    f"{_scenario_diff_detail(item)}"
                    "</p>"
                    "</article>"
                )
                for item in changed_scenarios[:4]
            )
        else:
            delta_cards = _empty_state(
                "No scenario drift",
                "The latest two suite runs are stable against each other.",
            )

        comparison_html = (
            '<section class="fragment-section">'
            '<div class="section-header"><h2>Regression Watch</h2></div>'
            '<div class="kv-grid">'
            f'{_labeled_value("Latest Run", comparison.get("candidate_run_id"))}'
            f'{_labeled_value("Baseline Run", comparison.get("baseline_run_id"))}'
            f'{_labeled_value("Overall Delta", comparison.get("overall_delta"))}'
            f'{_labeled_value("Changed Scenarios", comparison.get("changed_scenario_count"))}'
            f'{_labeled_value("Improved", comparison.get("delta_counts", {}).get("improved"))}'
            f'{_labeled_value("Regressed", comparison.get("delta_counts", {}).get("regressed"))}'
            "</div>"
            f'<div class="signal-list">{delta_cards}</div>'
            "</section>"
        )
    else:
        empty_comparison = _empty_state(
            "Need two runs",
            "Run the suite twice and this panel will show run-to-run drift.",
        )
        comparison_html = (
            '<section class="fragment-section">'
            '<div class="section-header"><h2>Regression Watch</h2></div>'
            f"{empty_comparison}"
            "</section>"
        )

    if visible_trends:
        trend_cards = "".join(
            (
                '<article class="list-card">'
                f'<div class="list-title">{_text(trend.get("title"))}</div>'
                '<div class="list-meta">'
                f'{_badge(trend.get("category"))}'
                f'{_badge(trend.get("latest_status"))}'
                f'{_badge(trend.get("status_delta"))}'
                "</div>"
                f'<p>runs {trend.get("total_runs", 0)} · pass rate '
                f'{_text(trend.get("pass_rate"))} · latest run '
                f'{_text(trend.get("latest_run_id"))}</p>'
                f'<p class="muted">recent window {trend.get("recent_run_count", 0)} · '
                f'latest {_timestamp(trend.get("latest_started_at"))}</p>'
                "</article>"
            )
            for trend in visible_trends[:LIST_LIMIT]
        )
    else:
        trend_cards = _empty_state(
            "No scenario trends yet",
            "Run the evaluation suite once and this rail will start showing drift and improvement.",
        )

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
                    f'{_shorten((result.get("scenario") or {}).get("title"), limit=32)}'
                    "</button>"
                )
            hidden_result_count = max(len(list(run.get("results", []))) - 3, 0)
            extra_detail = (
                f'<span class="muted tiny-note">+{hidden_result_count} more</span>'
                if hidden_result_count
                else ""
            )
            run_cards.append(
                '<article class="list-card">'
                f'<div class="list-title">{_text(run.get("run_id"))}</div>'
                '<div class="list-meta">'
                f'{_badge(run.get("overall_status"))}'
                f'{_badge(f"{run.get("scenario_count", 0)} scenarios", tone="neutral")}'
                "</div>"
                f'<p>pass {run.get("status_counts", {}).get("pass", 0)} · '
                f'review {run.get("status_counts", {}).get("review", 0)} · '
                f'started {_timestamp(run.get("started_at"))}</p>'
                '<div class="inline-actions">'
                f'{"".join(session_actions) or _badge("no session details", tone="neutral")}'
                f"{extra_detail}"
                "</div>"
                "</article>"
            )
        recent_runs = "".join(run_cards)
    else:
        recent_runs = _empty_state(
            "No scenario runs yet",
            "Use the scenario evaluation API and recent suite runs will appear here.",
        )

    return (
        '<div class="fragment-stack">'
        f"{launch_signoff_html}"
        f"{release_dossier_html}"
        f"{horizon_html}"
        f"{multiweek_html}"
        f"{sustained_drift_html}"
        f"{longitudinal_html}"
        f"{hardening_html}"
        f"{safety_audit_html}"
        f"{redteam_html}"
        f"{ship_readiness_html}"
        f"{migration_readiness_html}"
        f"{baseline_governance_html}"
        f"{release_gate_html}"
        f"{baseline_html}"
        f"{stability_report_html}"
        f"{comparison_html}"
        f"{misalignment_html}"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Scenario Trends</h2></div>'
        f'<div class="signal-list">{trend_cards}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Recent Scenario Runs</h2></div>'
        f'<div class="signal-list">{recent_runs}</div>'
        "</section>"
        "</div>"
    )


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
            "tab active"
            if (name, version) == (selected_name, selected_version)
            else "tab"
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
        if event.event_type in TRACE_EVENT_TYPES
    ]
    if not trace_events:
        return _empty_state(
            "Trace is empty",
            "This session has not emitted runtime trace events yet.",
        )
    return "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(event.get("event_type"))}</div>'
            f'<div class="trace-meta">v{event.get("version")} · '
            f'{_timestamp(event.get("occurred_at"))}</div>'
            f'<pre>{escape(str(event.get("payload", {})))}</pre>'
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
            "Ledger is empty",
            "No events have been written for this session yet.",
        )

    serialized = [container.stream_service.serialize_event(event) for event in events]
    return "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(event.get("event_type"))}</div>'
            f'<div class="trace-meta">#{event.get("version")} · '
            f'{_timestamp(event.get("occurred_at"))}</div>'
            f'<p>{_shorten(event.get("payload"), limit=200)}</p>'
            "</li>"
        )
        for event in serialized[-10:]
    )


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
            "Pick a session",
            "Choose a session from the right rail to inspect trace, memory, and audit state.",
        )

    events = await container.stream_service.read_stream(stream_id=session_id)
    if not events:
        return _empty_state(
            "Session not found",
            "The selected session does not exist in the current event store.",
        )

    try:
        replay = await container.stream_service.replay_stream(
            stream_id=session_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )
    except UnknownProjectorError:
        projector_name = "session-runtime"
        projector_version = "v1"
        replay = await container.stream_service.replay_stream(
            stream_id=session_id,
            projector_name=projector_name,
            projector_version=projector_version,
        )

    runtime_projection, memory_projection, evaluation, audit = await asyncio.gather(
        container.stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version="v1",
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

    strategy_grid = "".join(
        [
            _labeled_value("Latest Strategy", summary.get("latest_strategy")),
            _labeled_value(
                "Strategy Diversity",
                summary.get("latest_strategy_diversity_status"),
            ),
            _labeled_value("Policy Path", summary.get("latest_policy_path")),
            _labeled_value("Diversity Index", summary.get("strategy_diversity_index")),
            _labeled_value("Response Sequence", summary.get("latest_response_sequence_mode")),
            _labeled_value("Time Awareness", summary.get("latest_time_awareness_mode")),
            _labeled_value("Load Band", summary.get("latest_cognitive_load_band")),
            _labeled_value("Guidance Mode", summary.get("latest_guidance_mode")),
            _labeled_value("Guidance Pace", summary.get("latest_guidance_pacing")),
            _labeled_value("Guidance Agency", summary.get("latest_guidance_agency_mode")),
            _labeled_value(
                "Guidance Ritual",
                summary.get("latest_guidance_ritual_action"),
            ),
            _labeled_value(
                "Guidance Handoff",
                summary.get("latest_guidance_handoff_mode"),
            ),
            _labeled_value(
                "Guidance Carryover",
                summary.get("latest_guidance_carryover_mode"),
            ),
            _labeled_value("Cadence Status", summary.get("latest_cadence_status")),
            _labeled_value(
                "Cadence Turn Shape",
                summary.get("latest_cadence_turn_shape"),
            ),
            _labeled_value(
                "Cadence Tempo",
                summary.get("latest_cadence_followup_tempo"),
            ),
            _labeled_value(
                "Cadence Space",
                summary.get("latest_cadence_user_space_mode"),
            ),
            _labeled_value(
                "Ritual Phase",
                summary.get("latest_session_ritual_phase"),
            ),
            _labeled_value(
                "Ritual Close",
                summary.get("latest_session_ritual_closing_move"),
            ),
            _labeled_value(
                "Somatic Shortcut",
                summary.get("latest_session_ritual_somatic_shortcut"),
            ),
            _labeled_value(
                "Somatic Plan",
                summary.get("latest_somatic_orchestration_mode"),
            ),
            _labeled_value(
                "Body Anchor",
                summary.get("latest_somatic_orchestration_body_anchor"),
            ),
            _labeled_value(
                "Proactive Follow-up",
                summary.get("latest_proactive_followup_status"),
            ),
            _labeled_value(
                "Follow-up Cadence",
                summary.get("latest_proactive_cadence_key"),
            ),
            _labeled_value(
                "Follow-up Guardrail",
                summary.get("latest_proactive_guardrail_key"),
            ),
            _labeled_value(
                "Guardrail Max Dispatch",
                summary.get("latest_proactive_guardrail_max_dispatch_count"),
            ),
            _labeled_value(
                "Guardrail Hard Stops",
                summary.get("latest_proactive_guardrail_hard_stop_count"),
            ),
            _labeled_value(
                "Follow-up Scheduling",
                summary.get("latest_proactive_scheduling_mode"),
            ),
            _labeled_value(
                "Scheduling Cooldown",
                summary.get(
                    "latest_proactive_scheduling_min_seconds_since_last_outbound"
                ),
            ),
            _labeled_value(
                "Follow-up Orchestration",
                summary.get("latest_proactive_orchestration_key"),
            ),
            _labeled_value(
                "Second Touch Delivery",
                summary.get(
                    "latest_proactive_orchestration_second_touch_delivery_mode"
                ),
            ),
            _labeled_value(
                "Follow-up Actuation",
                summary.get("latest_proactive_actuation_key"),
            ),
            _labeled_value(
                "Follow-up Progression",
                summary.get("latest_proactive_progression_key"),
            ),
            _labeled_value(
                "Follow-up Controller",
                summary.get("latest_proactive_stage_controller_key"),
            ),
            _labeled_value(
                "Controller Decision",
                summary.get("latest_proactive_stage_controller_decision"),
            ),
            _labeled_value(
                "Controller Target",
                summary.get("latest_proactive_stage_controller_target_stage_label"),
            ),
            _labeled_value(
                "Controller Delay",
                summary.get("latest_proactive_stage_controller_additional_delay_seconds"),
            ),
            _labeled_value(
                "Follow-up Line Controller",
                summary.get("latest_proactive_line_controller_key"),
            ),
            _labeled_value(
                "Line Controller Decision",
                summary.get("latest_proactive_line_controller_decision"),
            ),
            _labeled_value(
                "Line Controller State",
                summary.get("latest_proactive_line_controller_line_state"),
            ),
            _labeled_value(
                "Line Controller Delay",
                summary.get("latest_proactive_line_controller_additional_delay_seconds"),
            ),
            _labeled_value(
                "Follow-up Refresh",
                summary.get("latest_proactive_stage_refresh_key"),
            ),
            _labeled_value(
                "Refresh Window",
                summary.get("latest_proactive_stage_refresh_window_status"),
            ),
            _labeled_value(
                "Refresh Changed",
                summary.get("latest_proactive_stage_refresh_changed"),
            ),
            _labeled_value(
                "Follow-up Replan",
                summary.get("latest_proactive_stage_replan_key"),
            ),
            _labeled_value(
                "Replan Strategy",
                summary.get("latest_proactive_stage_replan_strategy_key"),
            ),
            _labeled_value(
                "Replan Changed",
                summary.get("latest_proactive_stage_replan_changed"),
            ),
            _labeled_value(
                "Aggregate Governance",
                summary.get("latest_proactive_aggregate_governance_status"),
            ),
            _labeled_value(
                "Aggregate Primary Domain",
                summary.get("latest_proactive_aggregate_governance_primary_domain"),
            ),
            _labeled_value(
                "Aggregate Domain Count",
                summary.get("latest_proactive_aggregate_governance_domain_count"),
            ),
            _labeled_value(
                "Aggregate Summary",
                summary.get("latest_proactive_aggregate_governance_summary"),
            ),
            _labeled_value(
                "Aggregate Controller",
                summary.get("latest_proactive_aggregate_controller_key"),
            ),
            _labeled_value(
                "Aggregate Decision",
                summary.get("latest_proactive_aggregate_controller_decision"),
            ),
            _labeled_value(
                "Aggregate Stage Delay",
                summary.get("latest_proactive_aggregate_controller_stage_delay_seconds"),
            ),
            _labeled_value(
                "Aggregate Line Delay",
                summary.get("latest_proactive_aggregate_controller_line_delay_seconds"),
            ),
            _labeled_value(
                "Orchestration Controller",
                summary.get("latest_proactive_orchestration_controller_key"),
            ),
            _labeled_value(
                "Orchestration Decision",
                summary.get("latest_proactive_orchestration_controller_decision"),
            ),
            _labeled_value(
                "Orchestration Source",
                summary.get("latest_proactive_orchestration_controller_primary_source"),
            ),
            _labeled_value(
                "Orchestration Stage Delay",
                summary.get(
                    "latest_proactive_orchestration_controller_stage_delay_seconds"
                ),
            ),
            _labeled_value(
                "Orchestration Line Delay",
                summary.get(
                    "latest_proactive_orchestration_controller_line_delay_seconds"
                ),
            ),
            _labeled_value(
                "Follow-up Gate",
                summary.get("latest_proactive_dispatch_gate_key"),
            ),
            _labeled_value(
                "Follow-up Feedback",
                summary.get("latest_proactive_dispatch_feedback_key"),
            ),
            _labeled_value(
                "Feedback Strategy",
                summary.get("latest_proactive_dispatch_feedback_strategy_key"),
            ),
            _labeled_value(
                "Gate Decision",
                summary.get("latest_proactive_dispatch_gate_decision"),
            ),
            _labeled_value(
                "Gate Deferred",
                summary.get("proactive_dispatch_gate_deferred_turn_count"),
            ),
            _labeled_value(
                "Dispatch Envelope",
                summary.get("latest_proactive_dispatch_envelope_key"),
            ),
            _labeled_value(
                "Envelope Decision",
                summary.get("latest_proactive_dispatch_envelope_decision"),
            ),
            _labeled_value(
                "Envelope Strategy",
                summary.get("latest_proactive_dispatch_envelope_strategy_key"),
            ),
            _labeled_value(
                "Envelope Stage Delivery",
                summary.get("latest_proactive_dispatch_envelope_stage_delivery_mode"),
            ),
            _labeled_value(
                "Envelope Reengagement Delivery",
                summary.get(
                    "latest_proactive_dispatch_envelope_reengagement_delivery_mode"
                ),
            ),
            _labeled_value(
                "Envelope Sources",
                summary.get("latest_proactive_dispatch_envelope_source_count"),
            ),
            _labeled_value(
                "Stage State",
                summary.get("latest_proactive_stage_state_key"),
            ),
            _labeled_value(
                "Stage State Mode",
                summary.get("latest_proactive_stage_state_mode"),
            ),
            _labeled_value(
                "Stage State Queue",
                summary.get("latest_proactive_stage_state_queue_status"),
            ),
            _labeled_value(
                "Stage State Source",
                summary.get("latest_proactive_stage_state_source"),
            ),
            _labeled_value(
                "Stage Transition",
                summary.get("latest_proactive_stage_transition_key"),
            ),
            _labeled_value(
                "Stage Transition Mode",
                summary.get("latest_proactive_stage_transition_mode"),
            ),
            _labeled_value(
                "Stage Transition Queue",
                summary.get("latest_proactive_stage_transition_queue_hint"),
            ),
            _labeled_value(
                "Stage Transition Source",
                summary.get("latest_proactive_stage_transition_source"),
            ),
            _labeled_value(
                "Stage Machine",
                summary.get("latest_proactive_stage_machine_key"),
            ),
            _labeled_value(
                "Stage Machine Mode",
                summary.get("latest_proactive_stage_machine_mode"),
            ),
            _labeled_value(
                "Stage Machine Lifecycle",
                summary.get("latest_proactive_stage_machine_lifecycle"),
            ),
            _labeled_value(
                "Stage Machine Action",
                summary.get("latest_proactive_stage_machine_actionability"),
            ),
            _labeled_value(
                "Line State",
                summary.get("latest_proactive_line_state_key"),
            ),
            _labeled_value(
                "Line State Mode",
                summary.get("latest_proactive_line_state_mode"),
            ),
            _labeled_value(
                "Line State Lifecycle",
                summary.get("latest_proactive_line_state_lifecycle"),
            ),
            _labeled_value(
                "Line State Action",
                summary.get("latest_proactive_line_state_actionability"),
            ),
            _labeled_value(
                "Line Transition",
                summary.get("latest_proactive_line_transition_key"),
            ),
            _labeled_value(
                "Line Transition Mode",
                summary.get("latest_proactive_line_transition_mode"),
            ),
            _labeled_value(
                "Line Transition Exit",
                summary.get("latest_proactive_line_transition_exit_mode"),
            ),
            _labeled_value(
                "Line Machine",
                summary.get("latest_proactive_line_machine_key"),
            ),
            _labeled_value(
                "Line Machine Mode",
                summary.get("latest_proactive_line_machine_mode"),
            ),
            _labeled_value(
                "Line Machine Lifecycle",
                summary.get("latest_proactive_line_machine_lifecycle"),
            ),
            _labeled_value(
                "Line Machine Action",
                summary.get("latest_proactive_line_machine_actionability"),
            ),
            _labeled_value(
                "Lifecycle State",
                summary.get("latest_proactive_lifecycle_state_key"),
            ),
            _labeled_value(
                "Lifecycle State Mode",
                summary.get("latest_proactive_lifecycle_state_mode"),
            ),
            _labeled_value(
                "Lifecycle State Lifecycle",
                summary.get("latest_proactive_lifecycle_state_lifecycle"),
            ),
            _labeled_value(
                "Lifecycle State Action",
                summary.get("latest_proactive_lifecycle_state_actionability"),
            ),
            _labeled_value(
                "Lifecycle Transition",
                summary.get("latest_proactive_lifecycle_transition_key"),
            ),
            _labeled_value(
                "Lifecycle Transition Mode",
                summary.get("latest_proactive_lifecycle_transition_mode"),
            ),
            _labeled_value(
                "Lifecycle Transition Exit",
                summary.get("latest_proactive_lifecycle_transition_exit_mode"),
            ),
            _labeled_value(
                "Lifecycle Machine",
                summary.get("latest_proactive_lifecycle_machine_key"),
            ),
            _labeled_value(
                "Lifecycle Machine Mode",
                summary.get("latest_proactive_lifecycle_machine_mode"),
            ),
            _labeled_value(
                "Lifecycle Machine Lifecycle",
                summary.get("latest_proactive_lifecycle_machine_lifecycle"),
            ),
            _labeled_value(
                "Lifecycle Machine Action",
                summary.get("latest_proactive_lifecycle_machine_actionability"),
            ),
            _labeled_value(
                "Lifecycle Controller",
                summary.get("latest_proactive_lifecycle_controller_key"),
            ),
            _labeled_value(
                "Lifecycle Controller State",
                summary.get("latest_proactive_lifecycle_controller_state"),
            ),
            _labeled_value(
                "Lifecycle Controller Decision",
                summary.get("latest_proactive_lifecycle_controller_decision"),
            ),
            _labeled_value(
                "Lifecycle Controller Delay",
                summary.get("latest_proactive_lifecycle_controller_delay_seconds"),
            ),
            _labeled_value(
                "Lifecycle Envelope",
                summary.get("latest_proactive_lifecycle_envelope_key"),
            ),
            _labeled_value(
                "Lifecycle Envelope State",
                summary.get("latest_proactive_lifecycle_envelope_state"),
            ),
            _labeled_value(
                "Lifecycle Envelope Mode",
                summary.get("latest_proactive_lifecycle_envelope_mode"),
            ),
            _labeled_value(
                "Lifecycle Envelope Decision",
                summary.get("latest_proactive_lifecycle_envelope_decision"),
            ),
            _labeled_value(
                "Lifecycle Envelope Action",
                summary.get("latest_proactive_lifecycle_envelope_actionability"),
            ),
            _labeled_value(
                "Lifecycle Scheduler",
                summary.get("latest_proactive_lifecycle_scheduler_key"),
            ),
            _labeled_value(
                "Lifecycle Scheduler State",
                summary.get("latest_proactive_lifecycle_scheduler_state"),
            ),
            _labeled_value(
                "Lifecycle Scheduler Mode",
                summary.get("latest_proactive_lifecycle_scheduler_mode"),
            ),
            _labeled_value(
                "Lifecycle Scheduler Decision",
                summary.get("latest_proactive_lifecycle_scheduler_decision"),
            ),
            _labeled_value(
                "Lifecycle Scheduler Queue",
                summary.get("latest_proactive_lifecycle_scheduler_queue_status"),
            ),
            _labeled_value(
                "Lifecycle Window",
                summary.get("latest_proactive_lifecycle_window_key"),
            ),
            _labeled_value(
                "Lifecycle Window State",
                summary.get("latest_proactive_lifecycle_window_state"),
            ),
            _labeled_value(
                "Lifecycle Window Mode",
                summary.get("latest_proactive_lifecycle_window_mode"),
            ),
            _labeled_value(
                "Lifecycle Window Decision",
                summary.get("latest_proactive_lifecycle_window_decision"),
            ),
            _labeled_value(
                "Lifecycle Window Queue",
                summary.get("latest_proactive_lifecycle_window_queue_status"),
            ),
            _labeled_value(
                "Lifecycle Queue",
                summary.get("latest_proactive_lifecycle_queue_key"),
            ),
            _labeled_value(
                "Lifecycle Queue State",
                summary.get("latest_proactive_lifecycle_queue_state"),
            ),
            _labeled_value(
                "Lifecycle Queue Mode",
                summary.get("latest_proactive_lifecycle_queue_mode"),
            ),
            _labeled_value(
                "Lifecycle Queue Decision",
                summary.get("latest_proactive_lifecycle_queue_decision"),
            ),
            _labeled_value(
                "Lifecycle Queue Status",
                summary.get("latest_proactive_lifecycle_queue_status"),
            ),
            _labeled_value(
                "Lifecycle Dispatch",
                summary.get("latest_proactive_lifecycle_dispatch_key"),
            ),
            _labeled_value(
                "Lifecycle Dispatch State",
                summary.get("latest_proactive_lifecycle_dispatch_state"),
            ),
            _labeled_value(
                "Lifecycle Dispatch Mode",
                summary.get("latest_proactive_lifecycle_dispatch_mode"),
            ),
            _labeled_value(
                "Lifecycle Dispatch Decision",
                summary.get("latest_proactive_lifecycle_dispatch_decision"),
            ),
            _labeled_value(
                "Lifecycle Dispatch Action",
                summary.get("latest_proactive_lifecycle_dispatch_actionability"),
            ),
            _labeled_value(
                "Lifecycle Outcome",
                summary.get("latest_proactive_lifecycle_outcome_key"),
            ),
            _labeled_value(
                "Lifecycle Outcome Status",
                summary.get("latest_proactive_lifecycle_outcome_status"),
            ),
            _labeled_value(
                "Lifecycle Outcome Mode",
                summary.get("latest_proactive_lifecycle_outcome_mode"),
            ),
            _labeled_value(
                "Lifecycle Outcome Decision",
                summary.get("latest_proactive_lifecycle_outcome_decision"),
            ),
            _labeled_value(
                "Lifecycle Outcome Action",
                summary.get("latest_proactive_lifecycle_outcome_actionability"),
            ),
            _labeled_value(
                "Lifecycle Resolution",
                summary.get("latest_proactive_lifecycle_resolution_key"),
            ),
            _labeled_value(
                "Lifecycle Resolution Status",
                summary.get("latest_proactive_lifecycle_resolution_status"),
            ),
            _labeled_value(
                "Lifecycle Resolution Mode",
                summary.get("latest_proactive_lifecycle_resolution_mode"),
            ),
            _labeled_value(
                "Lifecycle Resolution Decision",
                summary.get("latest_proactive_lifecycle_resolution_decision"),
            ),
            _labeled_value(
                "Lifecycle Resolution Action",
                summary.get("latest_proactive_lifecycle_resolution_actionability"),
            ),
            _labeled_value(
                "Lifecycle Activation",
                summary.get("latest_proactive_lifecycle_activation_key"),
            ),
            _labeled_value(
                "Lifecycle Activation Status",
                summary.get("latest_proactive_lifecycle_activation_status"),
            ),
            _labeled_value(
                "Lifecycle Activation Mode",
                summary.get("latest_proactive_lifecycle_activation_mode"),
            ),
            _labeled_value(
                "Lifecycle Activation Decision",
                summary.get("latest_proactive_lifecycle_activation_decision"),
            ),
            _labeled_value(
                "Lifecycle Activation Action",
                summary.get("latest_proactive_lifecycle_activation_actionability"),
            ),
            _labeled_value(
                "Lifecycle Activation Stage",
                summary.get("latest_proactive_lifecycle_activation_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Activation Queue",
                summary.get("latest_proactive_lifecycle_activation_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Settlement",
                summary.get("latest_proactive_lifecycle_settlement_key"),
            ),
            _labeled_value(
                "Lifecycle Settlement Status",
                summary.get("latest_proactive_lifecycle_settlement_status"),
            ),
            _labeled_value(
                "Lifecycle Settlement Mode",
                summary.get("latest_proactive_lifecycle_settlement_mode"),
            ),
            _labeled_value(
                "Lifecycle Settlement Decision",
                summary.get("latest_proactive_lifecycle_settlement_decision"),
            ),
            _labeled_value(
                "Lifecycle Settlement Action",
                summary.get("latest_proactive_lifecycle_settlement_actionability"),
            ),
            _labeled_value(
                "Lifecycle Settlement Stage",
                summary.get("latest_proactive_lifecycle_settlement_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Settlement Queue",
                summary.get(
                    "latest_proactive_lifecycle_settlement_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Closure",
                summary.get("latest_proactive_lifecycle_closure_key"),
            ),
            _labeled_value(
                "Lifecycle Closure Status",
                summary.get("latest_proactive_lifecycle_closure_status"),
            ),
            _labeled_value(
                "Lifecycle Closure Mode",
                summary.get("latest_proactive_lifecycle_closure_mode"),
            ),
            _labeled_value(
                "Lifecycle Closure Decision",
                summary.get("latest_proactive_lifecycle_closure_decision"),
            ),
            _labeled_value(
                "Lifecycle Closure Action",
                summary.get("latest_proactive_lifecycle_closure_actionability"),
            ),
            _labeled_value(
                "Lifecycle Closure Stage",
                summary.get("latest_proactive_lifecycle_closure_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Closure Queue",
                summary.get("latest_proactive_lifecycle_closure_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Availability",
                summary.get("latest_proactive_lifecycle_availability_key"),
            ),
            _labeled_value(
                "Lifecycle Availability Status",
                summary.get("latest_proactive_lifecycle_availability_status"),
            ),
            _labeled_value(
                "Lifecycle Availability Mode",
                summary.get("latest_proactive_lifecycle_availability_mode"),
            ),
            _labeled_value(
                "Lifecycle Availability Decision",
                summary.get("latest_proactive_lifecycle_availability_decision"),
            ),
            _labeled_value(
                "Lifecycle Availability Action",
                summary.get("latest_proactive_lifecycle_availability_actionability"),
            ),
            _labeled_value(
                "Lifecycle Availability Stage",
                summary.get("latest_proactive_lifecycle_availability_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Availability Queue",
                summary.get(
                    "latest_proactive_lifecycle_availability_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Retention",
                summary.get("latest_proactive_lifecycle_retention_key"),
            ),
            _labeled_value(
                "Lifecycle Retention Status",
                summary.get("latest_proactive_lifecycle_retention_status"),
            ),
            _labeled_value(
                "Lifecycle Retention Mode",
                summary.get("latest_proactive_lifecycle_retention_mode"),
            ),
            _labeled_value(
                "Lifecycle Retention Decision",
                summary.get("latest_proactive_lifecycle_retention_decision"),
            ),
            _labeled_value(
                "Lifecycle Retention Action",
                summary.get("latest_proactive_lifecycle_retention_actionability"),
            ),
            _labeled_value(
                "Lifecycle Retention Stage",
                summary.get("latest_proactive_lifecycle_retention_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Retention Queue",
                summary.get(
                    "latest_proactive_lifecycle_retention_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Eligibility",
                summary.get("latest_proactive_lifecycle_eligibility_key"),
            ),
            _labeled_value(
                "Lifecycle Eligibility Status",
                summary.get("latest_proactive_lifecycle_eligibility_status"),
            ),
            _labeled_value(
                "Lifecycle Eligibility Mode",
                summary.get("latest_proactive_lifecycle_eligibility_mode"),
            ),
            _labeled_value(
                "Lifecycle Eligibility Decision",
                summary.get("latest_proactive_lifecycle_eligibility_decision"),
            ),
            _labeled_value(
                "Lifecycle Eligibility Action",
                summary.get("latest_proactive_lifecycle_eligibility_actionability"),
            ),
            _labeled_value(
                "Lifecycle Eligibility Stage",
                summary.get("latest_proactive_lifecycle_eligibility_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Eligibility Queue",
                summary.get(
                    "latest_proactive_lifecycle_eligibility_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Candidate",
                summary.get("latest_proactive_lifecycle_candidate_key"),
            ),
            _labeled_value(
                "Lifecycle Candidate Status",
                summary.get("latest_proactive_lifecycle_candidate_status"),
            ),
            _labeled_value(
                "Lifecycle Candidate Mode",
                summary.get("latest_proactive_lifecycle_candidate_mode"),
            ),
            _labeled_value(
                "Lifecycle Candidate Decision",
                summary.get("latest_proactive_lifecycle_candidate_decision"),
            ),
            _labeled_value(
                "Lifecycle Candidate Action",
                summary.get("latest_proactive_lifecycle_candidate_actionability"),
            ),
            _labeled_value(
                "Lifecycle Candidate Stage",
                summary.get("latest_proactive_lifecycle_candidate_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Candidate Queue",
                summary.get(
                    "latest_proactive_lifecycle_candidate_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Selectability",
                summary.get("latest_proactive_lifecycle_selectability_key"),
            ),
            _labeled_value(
                "Lifecycle Selectability Status",
                summary.get("latest_proactive_lifecycle_selectability_status"),
            ),
            _labeled_value(
                "Lifecycle Selectability Mode",
                summary.get("latest_proactive_lifecycle_selectability_mode"),
            ),
            _labeled_value(
                "Lifecycle Selectability Decision",
                summary.get("latest_proactive_lifecycle_selectability_decision"),
            ),
            _labeled_value(
                "Lifecycle Selectability Action",
                summary.get("latest_proactive_lifecycle_selectability_actionability"),
            ),
            _labeled_value(
                "Lifecycle Selectability Stage",
                summary.get(
                    "latest_proactive_lifecycle_selectability_active_stage_label"
                ),
            ),
            _labeled_value(
                "Lifecycle Selectability Queue",
                summary.get(
                    "latest_proactive_lifecycle_selectability_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Reentry",
                summary.get("latest_proactive_lifecycle_reentry_key"),
            ),
            _labeled_value(
                "Lifecycle Reentry Status",
                summary.get("latest_proactive_lifecycle_reentry_status"),
            ),
            _labeled_value(
                "Lifecycle Reentry Mode",
                summary.get("latest_proactive_lifecycle_reentry_mode"),
            ),
            _labeled_value(
                "Lifecycle Reentry Decision",
                summary.get("latest_proactive_lifecycle_reentry_decision"),
            ),
            _labeled_value(
                "Lifecycle Reentry Action",
                summary.get("latest_proactive_lifecycle_reentry_actionability"),
            ),
            _labeled_value(
                "Lifecycle Reentry Stage",
                summary.get("latest_proactive_lifecycle_reentry_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Reentry Queue",
                summary.get(
                    "latest_proactive_lifecycle_reentry_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Reactivation",
                summary.get("latest_proactive_lifecycle_reactivation_key"),
            ),
            _labeled_value(
                "Lifecycle Reactivation Status",
                summary.get("latest_proactive_lifecycle_reactivation_status"),
            ),
            _labeled_value(
                "Lifecycle Reactivation Mode",
                summary.get("latest_proactive_lifecycle_reactivation_mode"),
            ),
            _labeled_value(
                "Lifecycle Reactivation Decision",
                summary.get("latest_proactive_lifecycle_reactivation_decision"),
            ),
            _labeled_value(
                "Lifecycle Reactivation Action",
                summary.get("latest_proactive_lifecycle_reactivation_actionability"),
            ),
            _labeled_value(
                "Lifecycle Reactivation Stage",
                summary.get(
                    "latest_proactive_lifecycle_reactivation_active_stage_label"
                ),
            ),
            _labeled_value(
                "Lifecycle Reactivation Queue",
                summary.get(
                    "latest_proactive_lifecycle_reactivation_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Resumption",
                summary.get("latest_proactive_lifecycle_resumption_key"),
            ),
            _labeled_value(
                "Lifecycle Resumption Status",
                summary.get("latest_proactive_lifecycle_resumption_status"),
            ),
            _labeled_value(
                "Lifecycle Resumption Mode",
                summary.get("latest_proactive_lifecycle_resumption_mode"),
            ),
            _labeled_value(
                "Lifecycle Resumption Decision",
                summary.get("latest_proactive_lifecycle_resumption_decision"),
            ),
            _labeled_value(
                "Lifecycle Resumption Action",
                summary.get("latest_proactive_lifecycle_resumption_actionability"),
            ),
            _labeled_value(
                "Lifecycle Resumption Stage",
                summary.get("latest_proactive_lifecycle_resumption_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Resumption Queue",
                summary.get(
                    "latest_proactive_lifecycle_resumption_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Readiness",
                summary.get("latest_proactive_lifecycle_readiness_key"),
            ),
            _labeled_value(
                "Lifecycle Readiness Status",
                summary.get("latest_proactive_lifecycle_readiness_status"),
            ),
            _labeled_value(
                "Lifecycle Readiness Mode",
                summary.get("latest_proactive_lifecycle_readiness_mode"),
            ),
            _labeled_value(
                "Lifecycle Readiness Decision",
                summary.get("latest_proactive_lifecycle_readiness_decision"),
            ),
            _labeled_value(
                "Lifecycle Readiness Action",
                summary.get("latest_proactive_lifecycle_readiness_actionability"),
            ),
            _labeled_value(
                "Lifecycle Readiness Stage",
                summary.get("latest_proactive_lifecycle_readiness_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Readiness Queue",
                summary.get(
                    "latest_proactive_lifecycle_readiness_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Arming",
                summary.get("latest_proactive_lifecycle_arming_key"),
            ),
            _labeled_value(
                "Lifecycle Arming Status",
                summary.get("latest_proactive_lifecycle_arming_status"),
            ),
            _labeled_value(
                "Lifecycle Arming Mode",
                summary.get("latest_proactive_lifecycle_arming_mode"),
            ),
            _labeled_value(
                "Lifecycle Arming Decision",
                summary.get("latest_proactive_lifecycle_arming_decision"),
            ),
            _labeled_value(
                "Lifecycle Arming Action",
                summary.get("latest_proactive_lifecycle_arming_actionability"),
            ),
            _labeled_value(
                "Lifecycle Arming Stage",
                summary.get("latest_proactive_lifecycle_arming_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Arming Queue",
                summary.get("latest_proactive_lifecycle_arming_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Trigger",
                summary.get("latest_proactive_lifecycle_trigger_key"),
            ),
            _labeled_value(
                "Lifecycle Trigger Status",
                summary.get("latest_proactive_lifecycle_trigger_status"),
            ),
            _labeled_value(
                "Lifecycle Trigger Mode",
                summary.get("latest_proactive_lifecycle_trigger_mode"),
            ),
            _labeled_value(
                "Lifecycle Trigger Decision",
                summary.get("latest_proactive_lifecycle_trigger_decision"),
            ),
            _labeled_value(
                "Lifecycle Trigger Action",
                summary.get("latest_proactive_lifecycle_trigger_actionability"),
            ),
            _labeled_value(
                "Lifecycle Trigger Stage",
                summary.get("latest_proactive_lifecycle_trigger_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Trigger Queue",
                summary.get("latest_proactive_lifecycle_trigger_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Launch",
                summary.get("latest_proactive_lifecycle_launch_key"),
            ),
            _labeled_value(
                "Lifecycle Launch Status",
                summary.get("latest_proactive_lifecycle_launch_status"),
            ),
            _labeled_value(
                "Lifecycle Launch Mode",
                summary.get("latest_proactive_lifecycle_launch_mode"),
            ),
            _labeled_value(
                "Lifecycle Launch Decision",
                summary.get("latest_proactive_lifecycle_launch_decision"),
            ),
            _labeled_value(
                "Lifecycle Launch Action",
                summary.get("latest_proactive_lifecycle_launch_actionability"),
            ),
            _labeled_value(
                "Lifecycle Launch Stage",
                summary.get("latest_proactive_lifecycle_launch_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Launch Queue",
                summary.get("latest_proactive_lifecycle_launch_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Handoff",
                summary.get("latest_proactive_lifecycle_handoff_key"),
            ),
            _labeled_value(
                "Lifecycle Handoff Status",
                summary.get("latest_proactive_lifecycle_handoff_status"),
            ),
            _labeled_value(
                "Lifecycle Handoff Mode",
                summary.get("latest_proactive_lifecycle_handoff_mode"),
            ),
            _labeled_value(
                "Lifecycle Handoff Decision",
                summary.get("latest_proactive_lifecycle_handoff_decision"),
            ),
            _labeled_value(
                "Lifecycle Handoff Action",
                summary.get("latest_proactive_lifecycle_handoff_actionability"),
            ),
            _labeled_value(
                "Lifecycle Handoff Stage",
                summary.get("latest_proactive_lifecycle_handoff_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Handoff Queue",
                summary.get("latest_proactive_lifecycle_handoff_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Continuation",
                summary.get("latest_proactive_lifecycle_continuation_key"),
            ),
            _labeled_value(
                "Lifecycle Continuation Status",
                summary.get("latest_proactive_lifecycle_continuation_status"),
            ),
            _labeled_value(
                "Lifecycle Continuation Mode",
                summary.get("latest_proactive_lifecycle_continuation_mode"),
            ),
            _labeled_value(
                "Lifecycle Continuation Decision",
                summary.get("latest_proactive_lifecycle_continuation_decision"),
            ),
            _labeled_value(
                "Lifecycle Continuation Action",
                summary.get("latest_proactive_lifecycle_continuation_actionability"),
            ),
            _labeled_value(
                "Lifecycle Continuation Stage",
                summary.get("latest_proactive_lifecycle_continuation_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Continuation Queue",
                summary.get("latest_proactive_lifecycle_continuation_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Sustainment",
                summary.get("latest_proactive_lifecycle_sustainment_key"),
            ),
            _labeled_value(
                "Lifecycle Sustainment Status",
                summary.get("latest_proactive_lifecycle_sustainment_status"),
            ),
            _labeled_value(
                "Lifecycle Sustainment Mode",
                summary.get("latest_proactive_lifecycle_sustainment_mode"),
            ),
            _labeled_value(
                "Lifecycle Sustainment Decision",
                summary.get("latest_proactive_lifecycle_sustainment_decision"),
            ),
            _labeled_value(
                "Lifecycle Sustainment Action",
                summary.get("latest_proactive_lifecycle_sustainment_actionability"),
            ),
            _labeled_value(
                "Lifecycle Sustainment Stage",
                summary.get("latest_proactive_lifecycle_sustainment_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Sustainment Queue",
                summary.get("latest_proactive_lifecycle_sustainment_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Stewardship",
                summary.get("latest_proactive_lifecycle_stewardship_key"),
            ),
            _labeled_value(
                "Lifecycle Stewardship Status",
                summary.get("latest_proactive_lifecycle_stewardship_status"),
            ),
            _labeled_value(
                "Lifecycle Stewardship Mode",
                summary.get("latest_proactive_lifecycle_stewardship_mode"),
            ),
            _labeled_value(
                "Lifecycle Stewardship Decision",
                summary.get("latest_proactive_lifecycle_stewardship_decision"),
            ),
            _labeled_value(
                "Lifecycle Stewardship Action",
                summary.get("latest_proactive_lifecycle_stewardship_actionability"),
            ),
            _labeled_value(
                "Lifecycle Stewardship Stage",
                summary.get("latest_proactive_lifecycle_stewardship_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Stewardship Queue",
                summary.get("latest_proactive_lifecycle_stewardship_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Guardianship",
                summary.get("latest_proactive_lifecycle_guardianship_key"),
            ),
            _labeled_value(
                "Lifecycle Guardianship Status",
                summary.get("latest_proactive_lifecycle_guardianship_status"),
            ),
            _labeled_value(
                "Lifecycle Guardianship Mode",
                summary.get("latest_proactive_lifecycle_guardianship_mode"),
            ),
            _labeled_value(
                "Lifecycle Guardianship Decision",
                summary.get("latest_proactive_lifecycle_guardianship_decision"),
            ),
            _labeled_value(
                "Lifecycle Guardianship Action",
                summary.get("latest_proactive_lifecycle_guardianship_actionability"),
            ),
            _labeled_value(
                "Lifecycle Guardianship Stage",
                summary.get("latest_proactive_lifecycle_guardianship_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Guardianship Queue",
                summary.get("latest_proactive_lifecycle_guardianship_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Oversight",
                summary.get("latest_proactive_lifecycle_oversight_key"),
            ),
            _labeled_value(
                "Lifecycle Oversight Status",
                summary.get("latest_proactive_lifecycle_oversight_status"),
            ),
            _labeled_value(
                "Lifecycle Oversight Mode",
                summary.get("latest_proactive_lifecycle_oversight_mode"),
            ),
            _labeled_value(
                "Lifecycle Oversight Decision",
                summary.get("latest_proactive_lifecycle_oversight_decision"),
            ),
            _labeled_value(
                "Lifecycle Oversight Action",
                summary.get("latest_proactive_lifecycle_oversight_actionability"),
            ),
            _labeled_value(
                "Lifecycle Oversight Stage",
                summary.get("latest_proactive_lifecycle_oversight_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Oversight Queue",
                summary.get("latest_proactive_lifecycle_oversight_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Assurance",
                summary.get("latest_proactive_lifecycle_assurance_key"),
            ),
            _labeled_value(
                "Lifecycle Assurance Status",
                summary.get("latest_proactive_lifecycle_assurance_status"),
            ),
            _labeled_value(
                "Lifecycle Assurance Mode",
                summary.get("latest_proactive_lifecycle_assurance_mode"),
            ),
            _labeled_value(
                "Lifecycle Assurance Decision",
                summary.get("latest_proactive_lifecycle_assurance_decision"),
            ),
            _labeled_value(
                "Lifecycle Assurance Action",
                summary.get("latest_proactive_lifecycle_assurance_actionability"),
            ),
            _labeled_value(
                "Lifecycle Assurance Stage",
                summary.get("latest_proactive_lifecycle_assurance_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Assurance Queue",
                summary.get("latest_proactive_lifecycle_assurance_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Attestation",
                summary.get("latest_proactive_lifecycle_attestation_key"),
            ),
            _labeled_value(
                "Lifecycle Attestation Status",
                summary.get("latest_proactive_lifecycle_attestation_status"),
            ),
            _labeled_value(
                "Lifecycle Attestation Mode",
                summary.get("latest_proactive_lifecycle_attestation_mode"),
            ),
            _labeled_value(
                "Lifecycle Attestation Decision",
                summary.get("latest_proactive_lifecycle_attestation_decision"),
            ),
            _labeled_value(
                "Lifecycle Attestation Action",
                summary.get("latest_proactive_lifecycle_attestation_actionability"),
            ),
            _labeled_value(
                "Lifecycle Attestation Stage",
                summary.get("latest_proactive_lifecycle_attestation_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Attestation Queue",
                summary.get("latest_proactive_lifecycle_attestation_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Verification",
                summary.get("latest_proactive_lifecycle_verification_key"),
            ),
            _labeled_value(
                "Lifecycle Verification Status",
                summary.get("latest_proactive_lifecycle_verification_status"),
            ),
            _labeled_value(
                "Lifecycle Verification Mode",
                summary.get("latest_proactive_lifecycle_verification_mode"),
            ),
            _labeled_value(
                "Lifecycle Verification Decision",
                summary.get("latest_proactive_lifecycle_verification_decision"),
            ),
            _labeled_value(
                "Lifecycle Verification Action",
                summary.get("latest_proactive_lifecycle_verification_actionability"),
            ),
            _labeled_value(
                "Lifecycle Verification Stage",
                summary.get("latest_proactive_lifecycle_verification_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Verification Queue",
                summary.get("latest_proactive_lifecycle_verification_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Certification",
                summary.get("latest_proactive_lifecycle_certification_key"),
            ),
            _labeled_value(
                "Lifecycle Certification Status",
                summary.get("latest_proactive_lifecycle_certification_status"),
            ),
            _labeled_value(
                "Lifecycle Certification Mode",
                summary.get("latest_proactive_lifecycle_certification_mode"),
            ),
            _labeled_value(
                "Lifecycle Certification Decision",
                summary.get("latest_proactive_lifecycle_certification_decision"),
            ),
            _labeled_value(
                "Lifecycle Certification Action",
                summary.get("latest_proactive_lifecycle_certification_actionability"),
            ),
            _labeled_value(
                "Lifecycle Certification Stage",
                summary.get("latest_proactive_lifecycle_certification_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Certification Queue",
                summary.get("latest_proactive_lifecycle_certification_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Confirmation",
                summary.get("latest_proactive_lifecycle_confirmation_key"),
            ),
            _labeled_value(
                "Lifecycle Confirmation Status",
                summary.get("latest_proactive_lifecycle_confirmation_status"),
            ),
            _labeled_value(
                "Lifecycle Confirmation Mode",
                summary.get("latest_proactive_lifecycle_confirmation_mode"),
            ),
            _labeled_value(
                "Lifecycle Confirmation Decision",
                summary.get("latest_proactive_lifecycle_confirmation_decision"),
            ),
            _labeled_value(
                "Lifecycle Confirmation Action",
                summary.get("latest_proactive_lifecycle_confirmation_actionability"),
            ),
            _labeled_value(
                "Lifecycle Confirmation Stage",
                summary.get("latest_proactive_lifecycle_confirmation_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Confirmation Queue",
                summary.get("latest_proactive_lifecycle_confirmation_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Ratification",
                summary.get("latest_proactive_lifecycle_ratification_key"),
            ),
            _labeled_value(
                "Lifecycle Ratification Status",
                summary.get("latest_proactive_lifecycle_ratification_status"),
            ),
            _labeled_value(
                "Lifecycle Ratification Mode",
                summary.get("latest_proactive_lifecycle_ratification_mode"),
            ),
            _labeled_value(
                "Lifecycle Ratification Decision",
                summary.get("latest_proactive_lifecycle_ratification_decision"),
            ),
            _labeled_value(
                "Lifecycle Ratification Action",
                summary.get("latest_proactive_lifecycle_ratification_actionability"),
            ),
            _labeled_value(
                "Lifecycle Ratification Stage",
                summary.get("latest_proactive_lifecycle_ratification_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Ratification Queue",
                summary.get("latest_proactive_lifecycle_ratification_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Endorsement",
                summary.get("latest_proactive_lifecycle_endorsement_key"),
            ),
            _labeled_value(
                "Lifecycle Endorsement Status",
                summary.get("latest_proactive_lifecycle_endorsement_status"),
            ),
            _labeled_value(
                "Lifecycle Endorsement Mode",
                summary.get("latest_proactive_lifecycle_endorsement_mode"),
            ),
            _labeled_value(
                "Lifecycle Endorsement Decision",
                summary.get("latest_proactive_lifecycle_endorsement_decision"),
            ),
            _labeled_value(
                "Lifecycle Endorsement Action",
                summary.get("latest_proactive_lifecycle_endorsement_actionability"),
            ),
            _labeled_value(
                "Lifecycle Endorsement Stage",
                summary.get("latest_proactive_lifecycle_endorsement_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Endorsement Queue",
                summary.get("latest_proactive_lifecycle_endorsement_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Authorization",
                summary.get("latest_proactive_lifecycle_authorization_key"),
            ),
            _labeled_value(
                "Lifecycle Authorization Status",
                summary.get("latest_proactive_lifecycle_authorization_status"),
            ),
            _labeled_value(
                "Lifecycle Authorization Mode",
                summary.get("latest_proactive_lifecycle_authorization_mode"),
            ),
            _labeled_value(
                "Lifecycle Authorization Decision",
                summary.get("latest_proactive_lifecycle_authorization_decision"),
            ),
            _labeled_value(
                "Lifecycle Authorization Action",
                summary.get("latest_proactive_lifecycle_authorization_actionability"),
            ),
            _labeled_value(
                "Lifecycle Authorization Stage",
                summary.get("latest_proactive_lifecycle_authorization_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Authorization Queue",
                summary.get("latest_proactive_lifecycle_authorization_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Enactment",
                summary.get("latest_proactive_lifecycle_enactment_key"),
            ),
            _labeled_value(
                "Lifecycle Enactment Status",
                summary.get("latest_proactive_lifecycle_enactment_status"),
            ),
            _labeled_value(
                "Lifecycle Enactment Mode",
                summary.get("latest_proactive_lifecycle_enactment_mode"),
            ),
            _labeled_value(
                "Lifecycle Enactment Decision",
                summary.get("latest_proactive_lifecycle_enactment_decision"),
            ),
            _labeled_value(
                "Lifecycle Enactment Action",
                summary.get("latest_proactive_lifecycle_enactment_actionability"),
            ),
            _labeled_value(
                "Lifecycle Enactment Stage",
                summary.get("latest_proactive_lifecycle_enactment_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Enactment Queue",
                summary.get("latest_proactive_lifecycle_enactment_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Finality",
                summary.get("latest_proactive_lifecycle_finality_key"),
            ),
            _labeled_value(
                "Lifecycle Finality Status",
                summary.get("latest_proactive_lifecycle_finality_status"),
            ),
            _labeled_value(
                "Lifecycle Finality Mode",
                summary.get("latest_proactive_lifecycle_finality_mode"),
            ),
            _labeled_value(
                "Lifecycle Finality Decision",
                summary.get("latest_proactive_lifecycle_finality_decision"),
            ),
            _labeled_value(
                "Lifecycle Finality Action",
                summary.get("latest_proactive_lifecycle_finality_actionability"),
            ),
            _labeled_value(
                "Lifecycle Finality Stage",
                summary.get("latest_proactive_lifecycle_finality_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Finality Queue",
                summary.get("latest_proactive_lifecycle_finality_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Completion",
                summary.get("latest_proactive_lifecycle_completion_key"),
            ),
            _labeled_value(
                "Lifecycle Completion Status",
                summary.get("latest_proactive_lifecycle_completion_status"),
            ),
            _labeled_value(
                "Lifecycle Completion Mode",
                summary.get("latest_proactive_lifecycle_completion_mode"),
            ),
            _labeled_value(
                "Lifecycle Completion Decision",
                summary.get("latest_proactive_lifecycle_completion_decision"),
            ),
            _labeled_value(
                "Lifecycle Completion Action",
                summary.get("latest_proactive_lifecycle_completion_actionability"),
            ),
            _labeled_value(
                "Lifecycle Completion Stage",
                summary.get("latest_proactive_lifecycle_completion_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Completion Queue",
                summary.get("latest_proactive_lifecycle_completion_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Conclusion",
                summary.get("latest_proactive_lifecycle_conclusion_key"),
            ),
            _labeled_value(
                "Lifecycle Conclusion Status",
                summary.get("latest_proactive_lifecycle_conclusion_status"),
            ),
            _labeled_value(
                "Lifecycle Conclusion Mode",
                summary.get("latest_proactive_lifecycle_conclusion_mode"),
            ),
            _labeled_value(
                "Lifecycle Conclusion Decision",
                summary.get("latest_proactive_lifecycle_conclusion_decision"),
            ),
            _labeled_value(
                "Lifecycle Conclusion Action",
                summary.get("latest_proactive_lifecycle_conclusion_actionability"),
            ),
            _labeled_value(
                "Lifecycle Conclusion Stage",
                summary.get("latest_proactive_lifecycle_conclusion_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Conclusion Queue",
                summary.get("latest_proactive_lifecycle_conclusion_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Disposition",
                summary.get("latest_proactive_lifecycle_disposition_key"),
            ),
            _labeled_value(
                "Lifecycle Disposition Status",
                summary.get("latest_proactive_lifecycle_disposition_status"),
            ),
            _labeled_value(
                "Lifecycle Disposition Mode",
                summary.get("latest_proactive_lifecycle_disposition_mode"),
            ),
            _labeled_value(
                "Lifecycle Disposition Decision",
                summary.get("latest_proactive_lifecycle_disposition_decision"),
            ),
            _labeled_value(
                "Lifecycle Disposition Action",
                summary.get("latest_proactive_lifecycle_disposition_actionability"),
            ),
            _labeled_value(
                "Lifecycle Disposition Stage",
                summary.get("latest_proactive_lifecycle_disposition_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Disposition Queue",
                summary.get("latest_proactive_lifecycle_disposition_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Standing",
                summary.get("latest_proactive_lifecycle_standing_key"),
            ),
            _labeled_value(
                "Lifecycle Standing Status",
                summary.get("latest_proactive_lifecycle_standing_status"),
            ),
            _labeled_value(
                "Lifecycle Standing Mode",
                summary.get("latest_proactive_lifecycle_standing_mode"),
            ),
            _labeled_value(
                "Lifecycle Standing Decision",
                summary.get("latest_proactive_lifecycle_standing_decision"),
            ),
            _labeled_value(
                "Lifecycle Standing Action",
                summary.get("latest_proactive_lifecycle_standing_actionability"),
            ),
            _labeled_value(
                "Lifecycle Standing Stage",
                summary.get("latest_proactive_lifecycle_standing_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Standing Queue",
                summary.get("latest_proactive_lifecycle_standing_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Residency",
                summary.get("latest_proactive_lifecycle_residency_key"),
            ),
            _labeled_value(
                "Lifecycle Residency Status",
                summary.get("latest_proactive_lifecycle_residency_status"),
            ),
            _labeled_value(
                "Lifecycle Residency Mode",
                summary.get("latest_proactive_lifecycle_residency_mode"),
            ),
            _labeled_value(
                "Lifecycle Residency Decision",
                summary.get("latest_proactive_lifecycle_residency_decision"),
            ),
            _labeled_value(
                "Lifecycle Residency Action",
                summary.get("latest_proactive_lifecycle_residency_actionability"),
            ),
            _labeled_value(
                "Lifecycle Residency Stage",
                summary.get("latest_proactive_lifecycle_residency_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Residency Queue",
                summary.get("latest_proactive_lifecycle_residency_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Tenure",
                summary.get("latest_proactive_lifecycle_tenure_key"),
            ),
            _labeled_value(
                "Lifecycle Tenure Status",
                summary.get("latest_proactive_lifecycle_tenure_status"),
            ),
            _labeled_value(
                "Lifecycle Tenure Mode",
                summary.get("latest_proactive_lifecycle_tenure_mode"),
            ),
            _labeled_value(
                "Lifecycle Tenure Decision",
                summary.get("latest_proactive_lifecycle_tenure_decision"),
            ),
            _labeled_value(
                "Lifecycle Tenure Action",
                summary.get("latest_proactive_lifecycle_tenure_actionability"),
            ),
            _labeled_value(
                "Lifecycle Tenure Stage",
                summary.get("latest_proactive_lifecycle_tenure_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Tenure Queue",
                summary.get("latest_proactive_lifecycle_tenure_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Persistence",
                summary.get("latest_proactive_lifecycle_persistence_key"),
            ),
            _labeled_value(
                "Lifecycle Persistence Status",
                summary.get("latest_proactive_lifecycle_persistence_status"),
            ),
            _labeled_value(
                "Lifecycle Persistence Mode",
                summary.get("latest_proactive_lifecycle_persistence_mode"),
            ),
            _labeled_value(
                "Lifecycle Persistence Decision",
                summary.get("latest_proactive_lifecycle_persistence_decision"),
            ),
            _labeled_value(
                "Lifecycle Persistence Action",
                summary.get("latest_proactive_lifecycle_persistence_actionability"),
            ),
            _labeled_value(
                "Lifecycle Persistence Stage",
                summary.get("latest_proactive_lifecycle_persistence_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Persistence Queue",
                summary.get(
                    "latest_proactive_lifecycle_persistence_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Durability",
                summary.get("latest_proactive_lifecycle_durability_key"),
            ),
            _labeled_value(
                "Lifecycle Durability Status",
                summary.get("latest_proactive_lifecycle_durability_status"),
            ),
            _labeled_value(
                "Lifecycle Durability Mode",
                summary.get("latest_proactive_lifecycle_durability_mode"),
            ),
            _labeled_value(
                "Lifecycle Durability Decision",
                summary.get("latest_proactive_lifecycle_durability_decision"),
            ),
            _labeled_value(
                "Lifecycle Durability Action",
                summary.get("latest_proactive_lifecycle_durability_actionability"),
            ),
            _labeled_value(
                "Lifecycle Durability Stage",
                summary.get("latest_proactive_lifecycle_durability_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Durability Queue",
                summary.get(
                    "latest_proactive_lifecycle_durability_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Longevity",
                summary.get("latest_proactive_lifecycle_longevity_key"),
            ),
            _labeled_value(
                "Lifecycle Longevity Status",
                summary.get("latest_proactive_lifecycle_longevity_status"),
            ),
            _labeled_value(
                "Lifecycle Longevity Mode",
                summary.get("latest_proactive_lifecycle_longevity_mode"),
            ),
            _labeled_value(
                "Lifecycle Longevity Decision",
                summary.get("latest_proactive_lifecycle_longevity_decision"),
            ),
            _labeled_value(
                "Lifecycle Longevity Action",
                summary.get("latest_proactive_lifecycle_longevity_actionability"),
            ),
            _labeled_value(
                "Lifecycle Longevity Stage",
                summary.get("latest_proactive_lifecycle_longevity_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Longevity Queue",
                summary.get(
                    "latest_proactive_lifecycle_longevity_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Legacy",
                summary.get("latest_proactive_lifecycle_legacy_key"),
            ),
            _labeled_value(
                "Lifecycle Legacy Status",
                summary.get("latest_proactive_lifecycle_legacy_status"),
            ),
            _labeled_value(
                "Lifecycle Legacy Mode",
                summary.get("latest_proactive_lifecycle_legacy_mode"),
            ),
            _labeled_value(
                "Lifecycle Legacy Decision",
                summary.get("latest_proactive_lifecycle_legacy_decision"),
            ),
            _labeled_value(
                "Lifecycle Legacy Action",
                summary.get("latest_proactive_lifecycle_legacy_actionability"),
            ),
            _labeled_value(
                "Lifecycle Legacy Stage",
                summary.get("latest_proactive_lifecycle_legacy_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Legacy Queue",
                summary.get("latest_proactive_lifecycle_legacy_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Heritage",
                summary.get("latest_proactive_lifecycle_heritage_key"),
            ),
            _labeled_value(
                "Lifecycle Heritage Status",
                summary.get("latest_proactive_lifecycle_heritage_status"),
            ),
            _labeled_value(
                "Lifecycle Heritage Mode",
                summary.get("latest_proactive_lifecycle_heritage_mode"),
            ),
            _labeled_value(
                "Lifecycle Heritage Decision",
                summary.get("latest_proactive_lifecycle_heritage_decision"),
            ),
            _labeled_value(
                "Lifecycle Heritage Action",
                summary.get("latest_proactive_lifecycle_heritage_actionability"),
            ),
            _labeled_value(
                "Lifecycle Heritage Stage",
                summary.get("latest_proactive_lifecycle_heritage_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Heritage Queue",
                summary.get("latest_proactive_lifecycle_heritage_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Lineage",
                summary.get("latest_proactive_lifecycle_lineage_key"),
            ),
            _labeled_value(
                "Lifecycle Lineage Status",
                summary.get("latest_proactive_lifecycle_lineage_status"),
            ),
            _labeled_value(
                "Lifecycle Lineage Mode",
                summary.get("latest_proactive_lifecycle_lineage_mode"),
            ),
            _labeled_value(
                "Lifecycle Lineage Decision",
                summary.get("latest_proactive_lifecycle_lineage_decision"),
            ),
            _labeled_value(
                "Lifecycle Lineage Action",
                summary.get("latest_proactive_lifecycle_lineage_actionability"),
            ),
            _labeled_value(
                "Lifecycle Lineage Stage",
                summary.get("latest_proactive_lifecycle_lineage_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Lineage Queue",
                summary.get("latest_proactive_lifecycle_lineage_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Ancestry",
                summary.get("latest_proactive_lifecycle_ancestry_key"),
            ),
            _labeled_value(
                "Lifecycle Ancestry Status",
                summary.get("latest_proactive_lifecycle_ancestry_status"),
            ),
            _labeled_value(
                "Lifecycle Ancestry Mode",
                summary.get("latest_proactive_lifecycle_ancestry_mode"),
            ),
            _labeled_value(
                "Lifecycle Ancestry Decision",
                summary.get("latest_proactive_lifecycle_ancestry_decision"),
            ),
            _labeled_value(
                "Lifecycle Ancestry Action",
                summary.get("latest_proactive_lifecycle_ancestry_actionability"),
            ),
            _labeled_value(
                "Lifecycle Ancestry Stage",
                summary.get("latest_proactive_lifecycle_ancestry_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Ancestry Queue",
                summary.get("latest_proactive_lifecycle_ancestry_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Provenance",
                summary.get("latest_proactive_lifecycle_provenance_key"),
            ),
            _labeled_value(
                "Lifecycle Provenance Status",
                summary.get("latest_proactive_lifecycle_provenance_status"),
            ),
            _labeled_value(
                "Lifecycle Provenance Mode",
                summary.get("latest_proactive_lifecycle_provenance_mode"),
            ),
            _labeled_value(
                "Lifecycle Provenance Decision",
                summary.get("latest_proactive_lifecycle_provenance_decision"),
            ),
            _labeled_value(
                "Lifecycle Provenance Action",
                summary.get("latest_proactive_lifecycle_provenance_actionability"),
            ),
            _labeled_value(
                "Lifecycle Provenance Stage",
                summary.get("latest_proactive_lifecycle_provenance_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Provenance Queue",
                summary.get("latest_proactive_lifecycle_provenance_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Origin",
                summary.get("latest_proactive_lifecycle_origin_key"),
            ),
            _labeled_value(
                "Lifecycle Origin Status",
                summary.get("latest_proactive_lifecycle_origin_status"),
            ),
            _labeled_value(
                "Lifecycle Origin Mode",
                summary.get("latest_proactive_lifecycle_origin_mode"),
            ),
            _labeled_value(
                "Lifecycle Origin Decision",
                summary.get("latest_proactive_lifecycle_origin_decision"),
            ),
            _labeled_value(
                "Lifecycle Origin Action",
                summary.get("latest_proactive_lifecycle_origin_actionability"),
            ),
            _labeled_value(
                "Lifecycle Origin Stage",
                summary.get("latest_proactive_lifecycle_origin_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Origin Queue",
                summary.get("latest_proactive_lifecycle_origin_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Root",
                summary.get("latest_proactive_lifecycle_root_key"),
            ),
            _labeled_value(
                "Lifecycle Root Status",
                summary.get("latest_proactive_lifecycle_root_status"),
            ),
            _labeled_value(
                "Lifecycle Root Mode",
                summary.get("latest_proactive_lifecycle_root_mode"),
            ),
            _labeled_value(
                "Lifecycle Root Decision",
                summary.get("latest_proactive_lifecycle_root_decision"),
            ),
            _labeled_value(
                "Lifecycle Root Action",
                summary.get("latest_proactive_lifecycle_root_actionability"),
            ),
            _labeled_value(
                "Lifecycle Root Stage",
                summary.get("latest_proactive_lifecycle_root_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Root Queue",
                summary.get("latest_proactive_lifecycle_root_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Foundation",
                summary.get("latest_proactive_lifecycle_foundation_key"),
            ),
            _labeled_value(
                "Lifecycle Foundation Status",
                summary.get("latest_proactive_lifecycle_foundation_status"),
            ),
            _labeled_value(
                "Lifecycle Foundation Mode",
                summary.get("latest_proactive_lifecycle_foundation_mode"),
            ),
            _labeled_value(
                "Lifecycle Foundation Decision",
                summary.get("latest_proactive_lifecycle_foundation_decision"),
            ),
            _labeled_value(
                "Lifecycle Foundation Action",
                summary.get("latest_proactive_lifecycle_foundation_actionability"),
            ),
            _labeled_value(
                "Lifecycle Foundation Stage",
                summary.get("latest_proactive_lifecycle_foundation_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Foundation Queue",
                summary.get(
                    "latest_proactive_lifecycle_foundation_queue_override_status"
                ),
            ),
            _labeled_value(
                "Lifecycle Bedrock",
                summary.get("latest_proactive_lifecycle_bedrock_key"),
            ),
            _labeled_value(
                "Lifecycle Bedrock Status",
                summary.get("latest_proactive_lifecycle_bedrock_status"),
            ),
            _labeled_value(
                "Lifecycle Bedrock Mode",
                summary.get("latest_proactive_lifecycle_bedrock_mode"),
            ),
            _labeled_value(
                "Lifecycle Bedrock Decision",
                summary.get("latest_proactive_lifecycle_bedrock_decision"),
            ),
            _labeled_value(
                "Lifecycle Bedrock Action",
                summary.get("latest_proactive_lifecycle_bedrock_actionability"),
            ),
            _labeled_value(
                "Lifecycle Bedrock Stage",
                summary.get("latest_proactive_lifecycle_bedrock_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Bedrock Queue",
                summary.get("latest_proactive_lifecycle_bedrock_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Substrate",
                summary.get("latest_proactive_lifecycle_substrate_key"),
            ),
            _labeled_value(
                "Lifecycle Substrate Status",
                summary.get("latest_proactive_lifecycle_substrate_status"),
            ),
            _labeled_value(
                "Lifecycle Substrate Mode",
                summary.get("latest_proactive_lifecycle_substrate_mode"),
            ),
            _labeled_value(
                "Lifecycle Substrate Decision",
                summary.get("latest_proactive_lifecycle_substrate_decision"),
            ),
            _labeled_value(
                "Lifecycle Substrate Action",
                summary.get("latest_proactive_lifecycle_substrate_actionability"),
            ),
            _labeled_value(
                "Lifecycle Substrate Stage",
                summary.get("latest_proactive_lifecycle_substrate_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Substrate Queue",
                summary.get("latest_proactive_lifecycle_substrate_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Stratum",
                summary.get("latest_proactive_lifecycle_stratum_key"),
            ),
            _labeled_value(
                "Lifecycle Stratum Status",
                summary.get("latest_proactive_lifecycle_stratum_status"),
            ),
            _labeled_value(
                "Lifecycle Stratum Mode",
                summary.get("latest_proactive_lifecycle_stratum_mode"),
            ),
            _labeled_value(
                "Lifecycle Stratum Decision",
                summary.get("latest_proactive_lifecycle_stratum_decision"),
            ),
            _labeled_value(
                "Lifecycle Stratum Action",
                summary.get("latest_proactive_lifecycle_stratum_actionability"),
            ),
            _labeled_value(
                "Lifecycle Stratum Stage",
                summary.get("latest_proactive_lifecycle_stratum_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Stratum Queue",
                summary.get("latest_proactive_lifecycle_stratum_queue_override_status"),
            ),
            _labeled_value(
                "Lifecycle Layer",
                summary.get("latest_proactive_lifecycle_layer_key"),
            ),
            _labeled_value(
                "Lifecycle Layer Status",
                summary.get("latest_proactive_lifecycle_layer_status"),
            ),
            _labeled_value(
                "Lifecycle Layer Mode",
                summary.get("latest_proactive_lifecycle_layer_mode"),
            ),
            _labeled_value(
                "Lifecycle Layer Decision",
                summary.get("latest_proactive_lifecycle_layer_decision"),
            ),
            _labeled_value(
                "Lifecycle Layer Action",
                summary.get("latest_proactive_lifecycle_layer_actionability"),
            ),
            _labeled_value(
                "Lifecycle Layer Stage",
                summary.get("latest_proactive_lifecycle_layer_active_stage_label"),
            ),
            _labeled_value(
                "Lifecycle Layer Queue",
                summary.get("latest_proactive_lifecycle_layer_queue_override_status"),
            ),
            _labeled_value(
                "Second Touch Opening",
                summary.get(
                    "latest_proactive_actuation_second_touch_opening_move"
                ),
            ),
            _labeled_value(
                "Second Touch Bridge",
                summary.get(
                    "latest_proactive_actuation_second_touch_bridge_move"
                ),
            ),
            _labeled_value(
                "Second Touch Expiry Action",
                summary.get("latest_proactive_progression_second_touch_action"),
            ),
            _labeled_value(
                "Follow-up Stage",
                summary.get("latest_proactive_followup_dispatch_stage_label"),
            ),
            _labeled_value(
                "Re-engagement Matrix",
                summary.get("latest_reengagement_matrix_key"),
            ),
            _labeled_value(
                "Matrix Selected",
                summary.get("latest_reengagement_matrix_selected_strategy"),
            ),
            _labeled_value(
                "Matrix Alternative",
                summary.get("latest_reengagement_matrix_top_alternative"),
            ),
            _labeled_value(
                "Matrix Blocked",
                summary.get("latest_reengagement_matrix_blocked_count"),
            ),
            _labeled_value(
                "Re-engagement Ritual",
                summary.get("latest_reengagement_ritual_mode"),
            ),
            _labeled_value(
                "Re-engagement Strategy",
                summary.get("latest_reengagement_strategy_key"),
            ),
            _labeled_value(
                "Re-engagement Pressure",
                summary.get("latest_reengagement_pressure_mode"),
            ),
            _labeled_value(
                "Re-engagement Autonomy",
                summary.get("latest_reengagement_autonomy_signal"),
            ),
            _labeled_value(
                "Follow-up Dispatch",
                summary.get("latest_proactive_followup_dispatch_status"),
            ),
            _labeled_value(
                "Quality Doctor",
                summary.get("latest_runtime_quality_doctor_status"),
            ),
            _labeled_value("Growth Stage", summary.get("latest_system3_growth_stage")),
            _labeled_value(
                "Identity Trajectory",
                summary.get("latest_system3_identity_trajectory_status"),
            ),
            _labeled_value(
                "Identity Target",
                summary.get("latest_system3_identity_trajectory_target"),
            ),
            _labeled_value(
                "Growth Transition",
                summary.get("latest_system3_growth_transition_status"),
            ),
            _labeled_value(
                "Growth Target",
                summary.get("latest_system3_growth_transition_target"),
            ),
            _labeled_value(
                "Growth Trajectory",
                summary.get("latest_system3_growth_transition_trajectory_status"),
            ),
            _labeled_value(
                "Growth Trajectory Target",
                summary.get("latest_system3_growth_transition_trajectory_target"),
            ),
            _labeled_value(
                "Growth Trajectory Trigger",
                summary.get("latest_system3_growth_transition_trajectory_trigger"),
            ),
            _labeled_value(
                "Version Migration",
                summary.get("latest_system3_version_migration_status"),
            ),
            _labeled_value(
                "Migration Scope",
                summary.get("latest_system3_version_migration_scope"),
            ),
            _labeled_value(
                "Migration Trigger",
                summary.get("latest_system3_version_migration_trigger"),
            ),
            _labeled_value(
                "Migration Trajectory",
                summary.get("latest_system3_version_migration_trajectory_status"),
            ),
            _labeled_value(
                "Migration Trajectory Target",
                summary.get("latest_system3_version_migration_trajectory_target"),
            ),
            _labeled_value(
                "Migration Trajectory Trigger",
                summary.get("latest_system3_version_migration_trajectory_trigger"),
            ),
            _labeled_value(
                "Strategy Supervision",
                summary.get("latest_system3_strategy_supervision_status"),
            ),
            _labeled_value(
                "Supervision Mode",
                summary.get("latest_system3_strategy_supervision_mode"),
            ),
            _labeled_value(
                "Supervision Trigger",
                summary.get("latest_system3_strategy_supervision_trigger"),
            ),
            _labeled_value(
                "Supervision Trajectory",
                summary.get("latest_system3_strategy_supervision_trajectory_status"),
            ),
            _labeled_value(
                "Supervision Target",
                summary.get("latest_system3_strategy_supervision_trajectory_target"),
            ),
            _labeled_value(
                "Supervision Trajectory Trigger",
                summary.get("latest_system3_strategy_supervision_trajectory_trigger"),
            ),
            _labeled_value(
                "Model Evolution",
                summary.get("latest_system3_user_model_evolution_status"),
            ),
            _labeled_value(
                "Model Revision",
                summary.get("latest_system3_user_model_revision_mode"),
            ),
            _labeled_value(
                "Model Shift",
                summary.get("latest_system3_user_model_shift_signal"),
            ),
            _labeled_value(
                "Model Trajectory",
                summary.get("latest_system3_user_model_trajectory_status"),
            ),
            _labeled_value(
                "Trajectory Target",
                summary.get("latest_system3_user_model_trajectory_target"),
            ),
            _labeled_value(
                "Trajectory Trigger",
                summary.get("latest_system3_user_model_trajectory_trigger"),
            ),
            _labeled_value(
                "Expectation Calibration",
                summary.get("latest_system3_expectation_calibration_status"),
            ),
            _labeled_value(
                "Expectation Target",
                summary.get("latest_system3_expectation_calibration_target"),
            ),
            _labeled_value(
                "Expectation Trigger",
                summary.get("latest_system3_expectation_calibration_trigger"),
            ),
            _labeled_value(
                "Expectation Trajectory",
                summary.get(
                    "latest_system3_expectation_calibration_trajectory_status"
                ),
            ),
            _labeled_value(
                "Expectation Trajectory Target",
                summary.get(
                    "latest_system3_expectation_calibration_trajectory_target"
                ),
            ),
            _labeled_value(
                "Expectation Trajectory Trigger",
                summary.get(
                    "latest_system3_expectation_calibration_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Dependency Governance",
                summary.get("latest_system3_dependency_governance_status"),
            ),
            _labeled_value(
                "Dependency Target",
                summary.get("latest_system3_dependency_governance_target"),
            ),
            _labeled_value(
                "Dependency Trigger",
                summary.get("latest_system3_dependency_governance_trigger"),
            ),
            _labeled_value(
                "Dependency Trajectory",
                summary.get(
                    "latest_system3_dependency_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Dependency Trajectory Target",
                summary.get(
                    "latest_system3_dependency_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Dependency Trajectory Trigger",
                summary.get(
                    "latest_system3_dependency_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Autonomy Governance",
                summary.get("latest_system3_autonomy_governance_status"),
            ),
            _labeled_value(
                "Autonomy Target",
                summary.get("latest_system3_autonomy_governance_target"),
            ),
            _labeled_value(
                "Autonomy Trigger",
                summary.get("latest_system3_autonomy_governance_trigger"),
            ),
            _labeled_value(
                "Autonomy Trajectory",
                summary.get(
                    "latest_system3_autonomy_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Autonomy Trajectory Target",
                summary.get(
                    "latest_system3_autonomy_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Autonomy Trajectory Trigger",
                summary.get(
                    "latest_system3_autonomy_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Boundary Governance",
                summary.get("latest_system3_boundary_governance_status"),
            ),
            _labeled_value(
                "Boundary Target",
                summary.get("latest_system3_boundary_governance_target"),
            ),
            _labeled_value(
                "Boundary Trigger",
                summary.get("latest_system3_boundary_governance_trigger"),
            ),
            _labeled_value(
                "Boundary Trajectory",
                summary.get(
                    "latest_system3_boundary_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Boundary Trajectory Target",
                summary.get(
                    "latest_system3_boundary_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Boundary Trajectory Trigger",
                summary.get(
                    "latest_system3_boundary_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Support Governance",
                summary.get("latest_system3_support_governance_status"),
            ),
            _labeled_value(
                "Support Target",
                summary.get("latest_system3_support_governance_target"),
            ),
            _labeled_value(
                "Support Trigger",
                summary.get("latest_system3_support_governance_trigger"),
            ),
            _labeled_value(
                "Support Trajectory",
                summary.get(
                    "latest_system3_support_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Support Trajectory Target",
                summary.get(
                    "latest_system3_support_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Support Trajectory Trigger",
                summary.get(
                    "latest_system3_support_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Continuity Governance",
                summary.get("latest_system3_continuity_governance_status"),
            ),
            _labeled_value(
                "Continuity Target",
                summary.get("latest_system3_continuity_governance_target"),
            ),
            _labeled_value(
                "Continuity Trigger",
                summary.get("latest_system3_continuity_governance_trigger"),
            ),
            _labeled_value(
                "Continuity Trajectory",
                summary.get(
                    "latest_system3_continuity_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Continuity Trajectory Target",
                summary.get(
                    "latest_system3_continuity_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Continuity Trajectory Trigger",
                summary.get(
                    "latest_system3_continuity_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Repair Governance",
                summary.get("latest_system3_repair_governance_status"),
            ),
            _labeled_value(
                "Repair Target",
                summary.get("latest_system3_repair_governance_target"),
            ),
            _labeled_value(
                "Repair Trigger",
                summary.get("latest_system3_repair_governance_trigger"),
            ),
            _labeled_value(
                "Repair Trajectory",
                summary.get("latest_system3_repair_governance_trajectory_status"),
            ),
            _labeled_value(
                "Repair Trajectory Target",
                summary.get("latest_system3_repair_governance_trajectory_target"),
            ),
            _labeled_value(
                "Repair Trajectory Trigger",
                summary.get("latest_system3_repair_governance_trajectory_trigger"),
            ),
            _labeled_value(
                "Attunement Governance",
                summary.get("latest_system3_attunement_governance_status"),
            ),
            _labeled_value(
                "Attunement Target",
                summary.get("latest_system3_attunement_governance_target"),
            ),
            _labeled_value(
                "Attunement Trigger",
                summary.get("latest_system3_attunement_governance_trigger"),
            ),
            _labeled_value(
                "Attunement Trajectory",
                summary.get(
                    "latest_system3_attunement_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Attunement Trajectory Target",
                summary.get(
                    "latest_system3_attunement_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Attunement Trajectory Trigger",
                summary.get(
                    "latest_system3_attunement_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Trust Governance",
                summary.get("latest_system3_trust_governance_status"),
            ),
            _labeled_value(
                "Trust Target",
                summary.get("latest_system3_trust_governance_target"),
            ),
            _labeled_value(
                "Trust Trigger",
                summary.get("latest_system3_trust_governance_trigger"),
            ),
            _labeled_value(
                "Trust Trajectory",
                summary.get("latest_system3_trust_governance_trajectory_status"),
            ),
            _labeled_value(
                "Trust Trajectory Target",
                summary.get("latest_system3_trust_governance_trajectory_target"),
            ),
            _labeled_value(
                "Trust Trajectory Trigger",
                summary.get("latest_system3_trust_governance_trajectory_trigger"),
            ),
            _labeled_value(
                "Clarity Governance",
                summary.get("latest_system3_clarity_governance_status"),
            ),
            _labeled_value(
                "Clarity Target",
                summary.get("latest_system3_clarity_governance_target"),
            ),
            _labeled_value(
                "Clarity Trigger",
                summary.get("latest_system3_clarity_governance_trigger"),
            ),
            _labeled_value(
                "Clarity Trajectory",
                summary.get("latest_system3_clarity_governance_trajectory_status"),
            ),
            _labeled_value(
                "Clarity Trajectory Target",
                summary.get("latest_system3_clarity_governance_trajectory_target"),
            ),
            _labeled_value(
                "Clarity Trajectory Trigger",
                summary.get("latest_system3_clarity_governance_trajectory_trigger"),
            ),
            _labeled_value(
                "Pacing Governance",
                summary.get("latest_system3_pacing_governance_status"),
            ),
            _labeled_value(
                "Pacing Target",
                summary.get("latest_system3_pacing_governance_target"),
            ),
            _labeled_value(
                "Pacing Trigger",
                summary.get("latest_system3_pacing_governance_trigger"),
            ),
            _labeled_value(
                "Pacing Trajectory",
                summary.get("latest_system3_pacing_governance_trajectory_status"),
            ),
            _labeled_value(
                "Pacing Trajectory Target",
                summary.get("latest_system3_pacing_governance_trajectory_target"),
            ),
            _labeled_value(
                "Pacing Trajectory Trigger",
                summary.get("latest_system3_pacing_governance_trajectory_trigger"),
            ),
            _labeled_value(
                "Commitment Governance",
                summary.get("latest_system3_commitment_governance_status"),
            ),
            _labeled_value(
                "Commitment Target",
                summary.get("latest_system3_commitment_governance_target"),
            ),
            _labeled_value(
                "Commitment Trigger",
                summary.get("latest_system3_commitment_governance_trigger"),
            ),
            _labeled_value(
                "Commitment Trajectory",
                summary.get(
                    "latest_system3_commitment_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Commitment Trajectory Target",
                summary.get(
                    "latest_system3_commitment_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Commitment Trajectory Trigger",
                summary.get(
                    "latest_system3_commitment_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Disclosure Governance",
                summary.get("latest_system3_disclosure_governance_status"),
            ),
            _labeled_value(
                "Disclosure Target",
                summary.get("latest_system3_disclosure_governance_target"),
            ),
            _labeled_value(
                "Disclosure Trigger",
                summary.get("latest_system3_disclosure_governance_trigger"),
            ),
            _labeled_value(
                "Disclosure Trajectory",
                summary.get(
                    "latest_system3_disclosure_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Disclosure Trajectory Target",
                summary.get(
                    "latest_system3_disclosure_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Disclosure Trajectory Trigger",
                summary.get(
                    "latest_system3_disclosure_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Reciprocity Governance",
                summary.get("latest_system3_reciprocity_governance_status"),
            ),
            _labeled_value(
                "Reciprocity Target",
                summary.get("latest_system3_reciprocity_governance_target"),
            ),
            _labeled_value(
                "Reciprocity Trigger",
                summary.get("latest_system3_reciprocity_governance_trigger"),
            ),
            _labeled_value(
                "Reciprocity Trajectory",
                summary.get(
                    "latest_system3_reciprocity_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Reciprocity Trajectory Target",
                summary.get(
                    "latest_system3_reciprocity_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Reciprocity Trajectory Trigger",
                summary.get(
                    "latest_system3_reciprocity_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Pressure Governance",
                summary.get("latest_system3_pressure_governance_status"),
            ),
            _labeled_value(
                "Pressure Target",
                summary.get("latest_system3_pressure_governance_target"),
            ),
            _labeled_value(
                "Pressure Trigger",
                summary.get("latest_system3_pressure_governance_trigger"),
            ),
            _labeled_value(
                "Pressure Trajectory",
                summary.get(
                    "latest_system3_pressure_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Pressure Trajectory Target",
                summary.get(
                    "latest_system3_pressure_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Pressure Trajectory Trigger",
                summary.get(
                    "latest_system3_pressure_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Relational Governance",
                summary.get("latest_system3_relational_governance_status"),
            ),
            _labeled_value(
                "Relational Target",
                summary.get("latest_system3_relational_governance_target"),
            ),
            _labeled_value(
                "Relational Trigger",
                summary.get("latest_system3_relational_governance_trigger"),
            ),
            _labeled_value(
                "Relational Trajectory",
                summary.get(
                    "latest_system3_relational_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Relational Trajectory Target",
                summary.get(
                    "latest_system3_relational_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Relational Trajectory Trigger",
                summary.get(
                    "latest_system3_relational_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Safety Governance",
                summary.get("latest_system3_safety_governance_status"),
            ),
            _labeled_value(
                "Safety Target",
                summary.get("latest_system3_safety_governance_target"),
            ),
            _labeled_value(
                "Safety Trigger",
                summary.get("latest_system3_safety_governance_trigger"),
            ),
            _labeled_value(
                "Safety Trajectory",
                summary.get(
                    "latest_system3_safety_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Safety Trajectory Target",
                summary.get(
                    "latest_system3_safety_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Safety Trajectory Trigger",
                summary.get(
                    "latest_system3_safety_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Progress Governance",
                summary.get("latest_system3_progress_governance_status"),
            ),
            _labeled_value(
                "Progress Target",
                summary.get("latest_system3_progress_governance_target"),
            ),
            _labeled_value(
                "Progress Trigger",
                summary.get("latest_system3_progress_governance_trigger"),
            ),
            _labeled_value(
                "Progress Trajectory",
                summary.get(
                    "latest_system3_progress_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Progress Trajectory Target",
                summary.get(
                    "latest_system3_progress_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Progress Trajectory Trigger",
                summary.get(
                    "latest_system3_progress_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Stability Governance",
                summary.get("latest_system3_stability_governance_status"),
            ),
            _labeled_value(
                "Stability Target",
                summary.get("latest_system3_stability_governance_target"),
            ),
            _labeled_value(
                "Stability Trigger",
                summary.get("latest_system3_stability_governance_trigger"),
            ),
            _labeled_value(
                "Stability Trajectory",
                summary.get(
                    "latest_system3_stability_governance_trajectory_status"
                ),
            ),
            _labeled_value(
                "Stability Trajectory Target",
                summary.get(
                    "latest_system3_stability_governance_trajectory_target"
                ),
            ),
            _labeled_value(
                "Stability Trajectory Trigger",
                summary.get(
                    "latest_system3_stability_governance_trajectory_trigger"
                ),
            ),
            _labeled_value(
                "Moral Reasoning",
                summary.get("latest_system3_moral_reasoning_status"),
            ),
            _labeled_value(
                "Moral Conflict",
                summary.get("latest_system3_moral_conflict"),
            ),
            _labeled_value(
                "Moral Trajectory",
                summary.get("latest_system3_moral_trajectory_status"),
            ),
            _labeled_value(
                "Moral Target",
                summary.get("latest_system3_moral_trajectory_target"),
            ),
            _labeled_value(
                "Moral Trigger",
                summary.get("latest_system3_moral_trajectory_trigger"),
            ),
            _labeled_value(
                "Strategy Audit",
                summary.get("latest_system3_strategy_audit_status"),
            ),
            _labeled_value(
                "Audit Trajectory",
                summary.get("latest_system3_strategy_audit_trajectory_status"),
            ),
            _labeled_value(
                "Audit Target",
                summary.get("latest_system3_strategy_audit_trajectory_target"),
            ),
            _labeled_value(
                "Audit Trigger",
                summary.get("latest_system3_strategy_audit_trajectory_trigger"),
            ),
            _labeled_value(
                "Emotional Debt",
                summary.get("latest_system3_emotional_debt_status"),
            ),
            _labeled_value(
                "Debt Trajectory",
                summary.get("latest_system3_emotional_debt_trajectory_status"),
            ),
            _labeled_value(
                "Debt Target",
                summary.get("latest_system3_emotional_debt_trajectory_target"),
            ),
            _labeled_value(
                "Debt Trigger",
                summary.get("latest_system3_emotional_debt_trajectory_trigger"),
            ),
            _labeled_value("Post Audit", summary.get("latest_response_post_audit_status")),
            _labeled_value(
                "Normalization",
                summary.get("latest_response_normalization_final_status"),
            ),
            _labeled_value("Boundary", summary.get("latest_boundary_decision")),
            _labeled_value("Replay", "consistent" if audit.get("consistent") else "drift"),
        ]
    )
    relation_grid = "".join(
        [
            _labeled_value(
                "Psychological Safety",
                (runtime_state.get("relationship_state") or {}).get("psychological_safety"),
            ),
            _labeled_value(
                "Turbulence",
                (runtime_state.get("relationship_state") or {}).get("turbulence_risk"),
            ),
            _labeled_value(
                "Dependency Risk",
                (runtime_state.get("relationship_state") or {}).get("dependency_risk"),
            ),
            _labeled_value("Working Memory", summary.get("latest_working_memory_size")),
            _labeled_value("Recall Count", summary.get("latest_memory_recall_count")),
            _labeled_value("Pinned Memory", memory_state.get("pinned_item_count")),
        ]
    )
    replay_grid = "".join(
        [
            _labeled_value(
                "Projector",
                f'{projector.get("name")}@{projector.get("version")}',
            ),
            _labeled_value("Replay Status", "consistent" if audit.get("consistent") else "drift"),
            _labeled_value("Fingerprint", _shorten(audit.get("fingerprint"), limit=22)),
            _labeled_value("Event Count", audit.get("event_count")),
            _labeled_value("Trace Events", audit.get("trace_event_count")),
            _labeled_value(
                "Background Job",
                (audit.get("last_background_job") or {}).get("status"),
            ),
        ]
    )
    projection_grid = "".join(
        [
            _labeled_value(
                "Selected Projector",
                f'{selected_projector.get("name")}@{selected_projector.get("version")}',
            ),
            _labeled_value("Projection Events", replay.get("event_count")),
            _labeled_value(
                "Replay Consistency",
                "consistent" if replay.get("consistent") else "drift",
            ),
            _labeled_value(
                "Projection Fingerprint",
                _shorten(replay.get("fingerprint"), limit=22),
            ),
        ]
    )
    transcript_rows = "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(message.get("role"))}</div>'
            f'<div class="trace-meta">{_timestamp(message.get("occurred_at"))}</div>'
            f'<p>{_shorten(message.get("content"), limit=220)}</p>'
            "</li>"
        )
        for message in list(runtime_state.get("messages", []))[-6:]
    )
    replay_event_rows = "".join(
        (
            '<li class="trace-row">'
            f'<div class="trace-title">{_text(event.get("event_type"))}</div>'
            f'<div class="trace-meta">#{event.get("version")} · '
            f'{_timestamp(event.get("occurred_at"))}</div>'
            "</li>"
        )
        for event in list(replay.get("events", []))[-6:]
    )
    projector_buttons = _projector_buttons_html(
        request=request,
        session_id=session_id,
        projectors=available_projectors,
        selected_name=projector_name,
        selected_version=projector_version,
    )
    replay_preview = replay_event_rows or _empty_state(
        "No replay events",
        "This projector has no events to replay yet.",
    )

    return (
        '<div class="fragment-stack">'
        '<section class="fragment-section">'
        f'<div class="section-header"><h2>{_text(session_id)}</h2>'
        f'<div class="section-badges">{_badge(summary.get("latest_strategy"))}'
        f'{_badge(summary.get("latest_response_post_audit_status"))}'
        f'{_badge(summary.get("latest_response_normalization_final_status"))}</div></div>'
        f'<p class="lead">fingerprint {_text(audit.get("fingerprint"))} · '
        f'events {audit.get("event_count", 0)} · turns {summary.get("turn_count", 0)}</p>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Strategy & Audit</h2></div>'
        f'<div class="kv-grid">{strategy_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Relationship & Memory</h2></div>'
        f'<div class="kv-grid">{relation_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Replay Snapshot</h2></div>'
        f'<div class="kv-grid">{replay_grid}</div>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Projection Inspector</h2></div>'
        '<div class="tabbar compact-tabbar">'
        f"{projector_buttons}"
        "</div>"
        f'<div class="kv-grid">{projection_grid}</div>'
        '<ul class="trace-list">'
        f"{replay_preview}"
        "</ul>"
        f'<pre class="projection-json">{_pretty_json(replay.get("projection", {}))}</pre>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Recent Transcript</h2></div>'
        '<ul class="trace-list">'
        f'{transcript_rows or _empty_state("No transcript", "This session has no messages yet.")}'
        "</ul>"
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Event Ledger</h2></div>'
        f'<ul class="trace-list">{_event_ledger_html(container=container, events=events)}</ul>'
        "</section>"
        '<section class="fragment-section">'
        '<div class="section-header"><h2>Recent Trace</h2></div>'
        f'<ul class="trace-list">{_recent_trace_html(container=container, events=events)}</ul>'
        "</section>"
        "</div>"
    )


@router.get("", response_class=HTMLResponse)
async def console_home(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    sessions = await container.runtime_service.list_sessions()
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
    default_projector_name = "session-runtime"
    default_projector_version = "v1"
    detail_url = _detail_url(
        request,
        selected_session_id or None,
        projector_name=default_projector_name,
        version=default_projector_version,
    )
    detail_base_url = str(request.url_for("console_session_detail_fragment"))
    ws_url = str(request.url_for("runtime_websocket"))

    html = f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RelationshipOS Control Room</title>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    <script defer src="https://unpkg.com/alpinejs@3.14.1/dist/cdn.min.js"></script>
    <style>
      :root {{
        --paper: #f4efe4;
        --ink: #18212b;
        --muted: #5d6876;
        --line: #d5c8b0;
        --card: rgba(255, 251, 245, 0.92);
        --accent: #b95c1b;
        --accent-soft: #f2d9bf;
        --teal: #1f6d67;
        --teal-soft: #d8efec;
        --rose: #9a4137;
        --rose-soft: #f6d9d5;
        --shadow: 0 18px 48px rgba(24, 33, 43, 0.12);
      }}
      * {{ box-sizing: border-box; }}
      [x-cloak] {{ display: none !important; }}
      body {{
        margin: 0;
        min-height: 100vh;
        font-family: "IBM Plex Sans", "Avenir Next", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(185, 92, 27, 0.18), transparent 26%),
          radial-gradient(circle at top right, rgba(31, 109, 103, 0.16), transparent 22%),
          linear-gradient(180deg, #f8f4eb 0%, #f1eadc 100%);
      }}
      .shell {{
        max-width: 1480px;
        margin: 0 auto;
        padding: 28px 24px 40px;
      }}
      .hero {{
        display: grid;
        gap: 14px;
        margin-bottom: 22px;
      }}
      .eyebrow {{
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
      }}
      h1 {{
        margin: 0;
        font-family: "Fraunces", Georgia, serif;
        font-size: clamp(2.2rem, 5vw, 4.2rem);
        line-height: 0.96;
      }}
      .hero p {{
        margin: 0;
        max-width: 820px;
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.6;
      }}
      .layout {{
        display: grid;
        grid-template-columns: minmax(0, 1.7fr) minmax(340px, 0.9fr);
        gap: 20px;
      }}
      .stack {{
        display: grid;
        gap: 20px;
      }}
      .panel {{
        border: 1px solid rgba(213, 200, 176, 0.85);
        background: var(--card);
        border-radius: 24px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }}
      .panel-shell {{
        padding: 18px;
      }}
      .tabbar {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 14px;
      }}
      .compact-tabbar {{
        margin-bottom: 12px;
      }}
      .tab {{
        appearance: none;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.65);
        color: var(--ink);
        border-radius: 999px;
        padding: 10px 14px;
        font: inherit;
        font-weight: 600;
        cursor: pointer;
      }}
      .tab-version {{
        margin-left: 6px;
        font-size: 0.72rem;
        opacity: 0.72;
      }}
      .tab.active {{
        background: var(--ink);
        color: white;
        border-color: var(--ink);
      }}
      .fragment-stack {{
        display: grid;
        gap: 16px;
      }}
      .fragment-section {{
        padding: 18px;
        border-bottom: 1px solid rgba(213, 200, 176, 0.55);
      }}
      .fragment-section:last-child {{ border-bottom: none; }}
      .section-header {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        margin-bottom: 12px;
      }}
      .section-header h2 {{
        margin: 0;
        font-size: 1rem;
      }}
      .section-badges, .list-meta {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }}
      .pulse-dot {{
        color: var(--muted);
        font-size: 0.84rem;
      }}
      .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
      }}
      .metric-card {{
        border-radius: 18px;
        padding: 14px;
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(213, 200, 176, 0.7);
      }}
      .metric-label {{
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 8px;
      }}
      .metric-value {{
        font-family: "Fraunces", Georgia, serif;
        font-size: 1.7rem;
      }}
      .metric-detail {{
        color: var(--muted);
        font-size: 0.82rem;
        margin-top: 6px;
      }}
      .kv-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 10px;
      }}
      .kv-item {{
        display: grid;
        gap: 6px;
        padding: 12px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.68);
        border: 1px solid rgba(213, 200, 176, 0.65);
      }}
      .kv-label {{
        color: var(--muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }}
      .kv-value {{
        font-weight: 600;
      }}
      .badge {{
        display: inline-flex;
        align-items: center;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 700;
      }}
      .badge-good {{
        color: var(--teal);
        background: var(--teal-soft);
      }}
      .badge-warn {{
        color: var(--accent);
        background: var(--accent-soft);
      }}
      .badge-bad {{
        color: var(--rose);
        background: var(--rose-soft);
      }}
      .badge-neutral {{
        color: var(--ink);
        background: rgba(24, 33, 43, 0.08);
      }}
      .signal-list, .trace-list {{
        display: grid;
        gap: 10px;
        margin: 0;
        padding: 0;
        list-style: none;
      }}
      .inline-actions {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        align-items: center;
        margin-top: 10px;
      }}
      .signal-row, .list-card, .trace-row {{
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(213, 200, 176, 0.65);
      }}
      .signal-title, .list-title, .trace-title {{
        font-weight: 700;
      }}
      .signal-row p, .list-card p, .trace-row p {{
        margin: 8px 0 0;
        color: var(--muted);
        line-height: 1.45;
      }}
      .session-pick {{
        appearance: none;
        border: none;
        background: transparent;
        width: 100%;
        text-align: left;
        padding: 0;
        color: inherit;
        cursor: pointer;
      }}
      .mini-action {{
        appearance: none;
        border: 1px solid rgba(213, 200, 176, 0.9);
        background: rgba(255, 255, 255, 0.9);
        color: var(--ink);
        border-radius: 999px;
        padding: 8px 12px;
        font: inherit;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
      }}
      .tiny-note {{
        font-size: 0.78rem;
      }}
      .trace-row pre {{
        margin: 8px 0 0;
        white-space: pre-wrap;
        word-break: break-word;
        color: var(--muted);
        font-size: 0.82rem;
      }}
      .projection-json {{
        margin: 14px 0 0;
        padding: 14px;
        border-radius: 16px;
        background: rgba(24, 33, 43, 0.06);
        border: 1px solid rgba(213, 200, 176, 0.65);
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 0.82rem;
        color: var(--ink);
      }}
      .lead {{
        margin: 0;
        color: var(--muted);
      }}
      .muted {{
        color: var(--muted);
      }}
      .empty-state {{
        padding: 28px 20px;
        text-align: center;
      }}
      .empty-state h3 {{
        margin: 0 0 8px;
        font-size: 1rem;
      }}
      .empty-state p {{
        margin: 0;
        color: var(--muted);
      }}
      @media (max-width: 1080px) {{
        .layout {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <div
      class="shell"
      x-data="{{
        tab: 'sessions',
        selectedSession: {_js_string(selected_session_id)},
        selectedProjectorName: {_js_string(default_projector_name)},
        selectedProjectorVersion: {_js_string(default_projector_version)}
      }}"
      data-selected-session="{escape(selected_session_id)}"
      data-selected-projector-name="{escape(default_projector_name)}"
      data-selected-projector-version="{escape(default_projector_version)}"
    >
      <header class="hero">
        <div class="eyebrow">RelationshipOS Control Room</div>
        <h1>Readable runtime state, without leaving the browser.</h1>
        <p>
          This console is intentionally read-only. It gives us one place to inspect
          sessions, recent strategy decisions, memory state, jobs, archives, and
          evaluation signals while the event-sourced runtime keeps running.
        </p>
      </header>
      <div class="layout">
        <div class="stack">
          <section class="panel">
            <div
              id="console-overview"
              hx-get="{escape(overview_url)}"
              hx-trigger="load, every {PANEL_REFRESH_SECONDS}s"
              hx-swap="innerHTML"
            ></div>
          </section>
          <section class="panel">
            <div
              id="console-session-detail"
              hx-get="{escape(detail_url)}"
              hx-trigger="load"
              hx-swap="innerHTML"
            ></div>
          </section>
        </div>
        <aside class="stack">
          <section class="panel panel-shell">
            <div class="tabbar">
              <button
                class="tab"
                :class="{{ 'active': tab === 'sessions' }}"
                @click="tab = 'sessions'"
              >Sessions</button>
              <button
                class="tab"
                :class="{{ 'active': tab === 'jobs' }}"
                @click="tab = 'jobs'"
              >Jobs</button>
              <button
                class="tab"
                :class="{{ 'active': tab === 'archives' }}"
                @click="tab = 'archives'"
              >Archives</button>
              <button
                class="tab"
                :class="{{ 'active': tab === 'evaluations' }}"
                @click="tab = 'evaluations'"
              >Evaluations</button>
              <button
                class="tab"
                :class="{{ 'active': tab === 'scenarios' }}"
                @click="tab = 'scenarios'"
              >Scenarios</button>
            </div>
            <div x-show="tab === 'sessions'" x-cloak>
              <div
                id="console-sessions"
                hx-get="{escape(sessions_url)}"
                hx-trigger="load, every {PANEL_REFRESH_SECONDS}s"
                hx-swap="innerHTML"
              ></div>
            </div>
            <div x-show="tab === 'jobs'" x-cloak>
              <div
                id="console-jobs"
                hx-get="{escape(jobs_url)}"
                hx-trigger="load, every {PANEL_REFRESH_SECONDS}s"
                hx-swap="innerHTML"
              ></div>
            </div>
            <div x-show="tab === 'archives'" x-cloak>
              <div
                id="console-archives"
                hx-get="{escape(archives_url)}"
                hx-trigger="load, every {PANEL_REFRESH_SECONDS}s"
                hx-swap="innerHTML"
              ></div>
            </div>
            <div x-show="tab === 'evaluations'" x-cloak>
              <div
                id="console-evaluations"
                hx-get="{escape(evaluations_url)}"
                hx-trigger="load, every {PANEL_REFRESH_SECONDS}s"
                hx-swap="innerHTML"
              ></div>
            </div>
            <div x-show="tab === 'scenarios'" x-cloak>
              <div
                id="console-scenarios"
                hx-get="{escape(scenarios_url)}"
                hx-trigger="load, every {PANEL_REFRESH_SECONDS}s"
                hx-swap="innerHTML"
              ></div>
            </div>
          </section>
        </aside>
      </div>
    </div>
    <script>
      (() => {{
        const wsUrl = {_js_string(ws_url)};
        const detailBaseUrl = {_js_string(detail_base_url)};
        const refreshTargets = {{
          overview: {{ url: {_js_string(overview_url)}, target: "#console-overview" }},
          sessions: {{ url: {_js_string(sessions_url)}, target: "#console-sessions" }},
          jobs: {{ url: {_js_string(jobs_url)}, target: "#console-jobs" }},
          archives: {{ url: {_js_string(archives_url)}, target: "#console-archives" }},
          evaluations: {{ url: {_js_string(evaluations_url)}, target: "#console-evaluations" }},
          scenarios: {{ url: {_js_string(scenarios_url)}, target: "#console-scenarios" }},
        }};
        const pending = new Map();
        const shell = document.querySelector(".shell");
        let socket = null;
        let selectedSession = shell?.dataset.selectedSession || "";
        let selectedProjectorName = shell?.dataset.selectedProjectorName || "session-runtime";
        let selectedProjectorVersion = shell?.dataset.selectedProjectorVersion || "v1";

        function refreshPanel(key) {{
          const target = refreshTargets[key];
          if (!target || !window.htmx) {{
            return;
          }}
          window.htmx.ajax("GET", target.url, {{
            target: target.target,
            swap: "innerHTML",
          }});
        }}

        function refreshDetail() {{
          if (!window.htmx) {{
            return;
          }}
          const params = new URLSearchParams();
          if (selectedSession) {{
            params.set("session_id", selectedSession);
          }}
          params.set("projector_name", selectedProjectorName);
          params.set("version", selectedProjectorVersion);
          const url = params.size
            ? `${{detailBaseUrl}}?${{params.toString()}}`
            : detailBaseUrl;
          window.htmx.ajax("GET", url, {{
            target: "#console-session-detail",
            swap: "innerHTML",
          }});
        }}

        function queueRefresh(kind, callback, delay = 120) {{
          if (pending.has(kind)) {{
            return;
          }}
          pending.set(
            kind,
            window.setTimeout(() => {{
              pending.delete(kind);
              callback();
            }}, delay),
          );
        }}

        function subscribe(streamId, includeBacklog) {{
          if (!socket || socket.readyState !== WebSocket.OPEN) {{
            return;
          }}
          socket.send(
            JSON.stringify({{
              type: "subscribe",
              stream_id: streamId || null,
              include_backlog: Boolean(includeBacklog),
            }}),
          );
        }}

        function connect() {{
          socket = new WebSocket(wsUrl);
          socket.addEventListener("open", () => {{
            subscribe(selectedSession, true);
          }});
          socket.addEventListener("message", (event) => {{
            const message = JSON.parse(event.data);
            if (message.type === "hello") {{
              return;
            }}
            if (message.type === "trace_batch" || message.type === "session_projection") {{
              queueRefresh("detail", refreshDetail);
              queueRefresh("sessions", () => refreshPanel("sessions"));
              queueRefresh("evaluations", () => refreshPanel("evaluations"));
              queueRefresh("scenarios", () => refreshPanel("scenarios"));
              return;
            }}
            if (message.type === "job_update") {{
              queueRefresh("overview", () => refreshPanel("overview"));
              queueRefresh("jobs", () => refreshPanel("jobs"));
              queueRefresh("sessions", () => refreshPanel("sessions"));
              queueRefresh("evaluations", () => refreshPanel("evaluations"));
              queueRefresh("scenarios", () => refreshPanel("scenarios"));
              return;
            }}
            if (message.type === "archive_update") {{
              queueRefresh("overview", () => refreshPanel("overview"));
              queueRefresh("archives", () => refreshPanel("archives"));
              queueRefresh("sessions", () => refreshPanel("sessions"));
              queueRefresh("scenarios", () => refreshPanel("scenarios"));
              return;
            }}
            if (message.type === "runtime_overview") {{
              queueRefresh("overview", () => refreshPanel("overview"));
            }}
          }});
          socket.addEventListener("close", () => {{
            window.setTimeout(connect, 1000);
          }});
        }}

        window.relationshipOSConsole = {{
          selectSession(sessionId) {{
            selectedSession = sessionId || "";
            if (shell) {{
              shell.dataset.selectedSession = selectedSession;
            }}
            subscribe(selectedSession, false);
            queueRefresh("detail", refreshDetail, 20);
          }},
          selectProjector(name, version) {{
            selectedProjectorName = name || "session-runtime";
            selectedProjectorVersion = version || "v1";
            if (shell) {{
              shell.dataset.selectedProjectorName = selectedProjectorName;
              shell.dataset.selectedProjectorVersion = selectedProjectorVersion;
            }}
            queueRefresh("detail", refreshDetail, 20);
          }},
        }};

        connect();
      }})();
    </script>
  </body>
</html>
"""
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
    return HTMLResponse(
        await _render_evaluations_fragment(request=request, container=container)
    )


@router.get("/fragments/scenarios", response_class=HTMLResponse)
async def console_scenarios_fragment(
    request: Request,
    container: ContainerDep,
) -> HTMLResponse:
    return HTMLResponse(
        await _render_scenarios_fragment(request=request, container=container)
    )


@router.get("/fragments/session-detail", response_class=HTMLResponse)
async def console_session_detail_fragment(
    request: Request,
    session_id: Annotated[str | None, Query()] = None,
    projector_name: str = "session-runtime",
    version: str = "v1",
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
