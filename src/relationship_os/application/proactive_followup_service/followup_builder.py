from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from relationship_os.application.analyzers import build_proactive_stage_state_decision
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
)
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    SESSION_STARTED,
    USER_MESSAGE_RECEIVED,
)
from relationship_os.domain.events import StoredEvent

if TYPE_CHECKING:
    from relationship_os.application.stream_service import StreamService

_QUEUE_PRIORITY = {
    "overdue": 0,
    "due": 1,
    "scheduled": 2,
    "waiting": 3,
    "hold": 4,
}

_GENERIC_LIFECYCLE_PHASES = (
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


def _parse_datetime(value: object | None) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@dataclass(frozen=True)
class _FollowupContext:
    state: dict[str, Any]
    session: dict[str, Any]
    session_source: str
    directive: dict[str, Any]
    guidance_plan: dict[str, Any]
    conversation_cadence_plan: dict[str, Any]
    session_ritual_plan: dict[str, Any]
    somatic_orchestration_plan: dict[str, Any]
    proactive_cadence_plan: dict[str, Any]
    reengagement_matrix_assessment: dict[str, Any]
    selected_matrix_candidate: dict[str, Any]
    reengagement_plan: dict[str, Any]
    proactive_scheduling_plan: dict[str, Any]
    proactive_guardrail_plan: dict[str, Any]
    proactive_orchestration_plan: dict[str, Any]
    proactive_actuation_plan: dict[str, Any]
    proactive_progression_plan: dict[str, Any]
    events: list[StoredEvent]
    latest_proactive_event: StoredEvent | None
    latest_proactive_scheduling_event: StoredEvent | None
    latest_proactive_orchestration_event: StoredEvent | None
    latest_proactive_actuation_event: StoredEvent | None
    latest_proactive_progression_event: StoredEvent | None
    latest_proactive_dispatch_gate_event: StoredEvent | None
    latest_proactive_dispatch_feedback_event: StoredEvent | None
    latest_proactive_stage_controller_event: StoredEvent | None
    latest_proactive_line_controller_event: StoredEvent | None
    latest_session_event: StoredEvent | None
    latest_user_event: StoredEvent | None
    latest_assistant_event: StoredEvent | None
    directive_time: datetime
    dispatch_events_for_directive: list[StoredEvent]
    dispatched_stage_count: int
    stage_labels: list[str]
    stage_intervals_seconds: list[int]
    close_after_stage_index: int
    max_dispatch_count: int
    stage_index_by_label: dict[str, int]
    close_loop_stage: str


@dataclass(frozen=True)
class _FollowupLatestEvents:
    latest_proactive_event: StoredEvent | None
    latest_proactive_scheduling_event: StoredEvent | None
    latest_proactive_orchestration_event: StoredEvent | None
    latest_proactive_actuation_event: StoredEvent | None
    latest_proactive_progression_event: StoredEvent | None
    latest_proactive_dispatch_gate_event: StoredEvent | None
    latest_proactive_dispatch_feedback_event: StoredEvent | None
    latest_proactive_stage_controller_event: StoredEvent | None
    latest_proactive_line_controller_event: StoredEvent | None
    latest_session_event: StoredEvent | None
    latest_user_event: StoredEvent | None
    latest_assistant_event: StoredEvent | None


@dataclass(frozen=True)
class _FollowupStageMetadata:
    directive_time: datetime
    dispatch_events_for_directive: list[StoredEvent]
    dispatched_stage_count: int
    stage_labels: list[str]
    stage_intervals_seconds: list[int]
    close_after_stage_index: int
    max_dispatch_count: int
    stage_index_by_label: dict[str, int]
    close_loop_stage: str


@dataclass(frozen=True)
class _StageResolution:
    directive_status: str
    window_seconds: int
    current_stage_index: int
    current_stage_label: str
    current_stage_directive: dict[str, Any] | None
    current_stage_actuation: dict[str, Any] | None
    current_stage_progression: dict[str, Any] | None
    current_stage_guardrail: dict[str, Any] | None
    due_at: datetime | None
    base_due_at: datetime | None
    expires_at: datetime | None
    seconds_until_due: int | None
    seconds_overdue: int | None
    window_remaining_seconds: int | None
    schedule_reason: str | None
    scheduling_deferred_until: datetime | None
    progression_advanced: bool
    progression_reason: str | None
    queue_status: str


@dataclass(frozen=True)
class _StagePayloadSelection:
    current_stage_label: str
    current_stage_directive: dict[str, Any] | None
    current_stage_actuation: dict[str, Any] | None
    current_stage_progression: dict[str, Any] | None
    current_stage_guardrail: dict[str, Any] | None


@dataclass(frozen=True)
class _StageScheduleSnapshot:
    payload: _StagePayloadSelection
    due_at: datetime | None
    base_due_at: datetime | None
    expires_at: datetime | None
    seconds_until_due: int | None
    seconds_overdue: int | None
    window_remaining_seconds: int | None
    schedule_reason: str | None
    scheduling_deferred_until: datetime | None
    queue_status: str


@dataclass(frozen=True)
class _StageProgressionAdvance:
    next_stage_index: int
    progression_anchor_at: datetime
    progression_reason: str


@dataclass(frozen=True)
class _QueueOverrideState:
    due_at: datetime | None
    expires_at: datetime | None
    seconds_until_due: int | None
    seconds_overdue: int | None
    window_remaining_seconds: int | None
    schedule_reason: str | None
    scheduling_deferred_until: datetime | None
    queue_status: str
    skip_dispatch_override: bool = False


@dataclass(frozen=True)
class _LifecyclePhaseOverride:
    phase: str
    decision: str
    stage_label: str
    delay_seconds: int


@dataclass(frozen=True)
class _LifecyclePhaseOverrideSpec:
    phase: str
    match_blockers: tuple[str, ...]
    action_blockers: tuple[str, ...] = ()
    terminate_decisions: tuple[str, ...] = ()
    hold_decisions: tuple[str, ...] = ()
    buffer_decisions: tuple[str, ...] = ()
    skip_decisions: tuple[str, ...] = ()
    stage_label_key: str = "active_stage_label"
    match_stage_label: bool = True
    buffer_reason_tag: str | None = None
    buffer_remove_tag: str | None = None


@dataclass(frozen=True)
class _ProjectedFollowupStateBundle:
    projections: dict[str, dict[str, Any]]
    projected_stage_state: dict[str, Any]
    projected_line_state: dict[str, Any]
    projected_line_transition: dict[str, Any]
    projected_line_machine: dict[str, Any]
    projected_lifecycle_state: dict[str, Any]
    projected_lifecycle_transition: dict[str, Any]
    projected_lifecycle_machine: dict[str, Any]
    projected_lifecycle_envelope: dict[str, Any]
    projected_lifecycle_scheduler: dict[str, Any]
    projected_lifecycle_window: dict[str, Any]
    projected_lifecycle_queue: dict[str, Any]
    projected_lifecycle_dispatch: dict[str, Any]
    projected_lifecycle_outcome: dict[str, Any]
    projected_lifecycle_resolution: dict[str, Any]
    lifecycle_phase_overrides: dict[str, _LifecyclePhaseOverride]
    projected_dispatch_envelope: dict[str, Any]
    runtime_coordination_snapshot: dict[str, Any]
    lifecycle_controller_projection: dict[str, Any]


@dataclass(frozen=True)
class _FollowupPayloadBundle:
    dispatch_gate_payload: dict[str, Any]
    dispatch_feedback_payload: dict[str, Any]
    stage_controller_payload: dict[str, Any]
    line_controller_payload: dict[str, Any]


@dataclass(frozen=True)
class _ResolvedFollowupQueueBundle:
    due_at: datetime | None
    base_due_at: datetime | None
    expires_at: datetime | None
    seconds_until_due: int | None
    seconds_overdue: int | None
    window_remaining_seconds: int | None
    schedule_reason: str | None
    scheduling_deferred_until: datetime | None
    queue_status: str
    proactive_stage_state: dict[str, Any]


@dataclass(frozen=True)
class _FollowupAssemblyBundle:
    session_id: str
    context: _FollowupContext
    stage_resolution: _StageResolution
    projected: _ProjectedFollowupStateBundle
    payloads: _FollowupPayloadBundle
    queue: _ResolvedFollowupQueueBundle


def _default_lifecycle_phase_override_spec(
    phase: str,
    *,
    match_blockers: tuple[str, ...] = (),
    action_blockers: tuple[str, ...] = (),
    terminate_decisions: tuple[str, ...] | None = None,
    hold_decisions: tuple[str, ...] | None = None,
    buffer_decisions: tuple[str, ...] | None = None,
    skip_decisions: tuple[str, ...] | None = None,
    stage_label_key: str = "active_stage_label",
    match_stage_label: bool = True,
    buffer_reason_tag: str | None = None,
    buffer_remove_tag: str | None = None,
) -> _LifecyclePhaseOverrideSpec:
    return _LifecyclePhaseOverrideSpec(
        phase=phase,
        match_blockers=match_blockers,
        action_blockers=action_blockers,
        terminate_decisions=terminate_decisions
        or (f"archive_lifecycle_{phase}", f"retire_lifecycle_{phase}"),
        hold_decisions=hold_decisions or (f"pause_lifecycle_{phase}",),
        buffer_decisions=buffer_decisions or (f"buffer_lifecycle_{phase}",),
        skip_decisions=skip_decisions or (f"keep_lifecycle_{phase}",),
        stage_label_key=stage_label_key,
        match_stage_label=match_stage_label,
        buffer_reason_tag=buffer_reason_tag or f"lifecycle_{phase}_buffered",
        buffer_remove_tag=buffer_remove_tag,
    )


def _build_foundation_phase_override_specs() -> tuple[_LifecyclePhaseOverrideSpec, ...]:
    phase_blockers = {
        "layer": (),
        "stratum": ("layer",),
        "substrate": ("layer", "stratum"),
        "bedrock": ("layer", "stratum", "substrate"),
        "foundation": ("layer", "stratum", "substrate", "bedrock"),
    }
    return (
        _default_lifecycle_phase_override_spec(
            "layer",
            buffer_remove_tag="lifecycle_stratum_buffered",
        ),
        _default_lifecycle_phase_override_spec(
            "stratum",
            match_blockers=phase_blockers["stratum"],
            buffer_remove_tag="lifecycle_substrate_buffered",
        ),
        *(
            _default_lifecycle_phase_override_spec(
                phase,
                match_blockers=phase_blockers[phase],
            )
            for phase in ("substrate", "bedrock", "foundation")
        ),
    )


def _build_heritage_phase_override_specs() -> tuple[_LifecyclePhaseOverrideSpec, ...]:
    layer_chain = ("layer", "stratum", "substrate", "bedrock", "foundation")
    root_blockers = layer_chain
    origin_blockers = root_blockers + ("root",)
    provenance_blockers = origin_blockers + ("origin",)
    ancestry_blockers = provenance_blockers + ("provenance",)
    heritage_blockers = ancestry_blockers + ("ancestry", "lineage")
    legacy_blockers = heritage_blockers + ("heritage",)
    longevity_blockers = legacy_blockers + ("legacy",)
    durability_blockers = longevity_blockers + ("longevity",)
    persistence_blockers = durability_blockers + ("durability",)
    tenure_blockers = persistence_blockers + ("persistence",)
    residency_blockers = tenure_blockers + ("tenure",)
    standing_blockers = residency_blockers + ("residency",)
    disposition_blockers = standing_blockers + ("standing",)
    return (
        _default_lifecycle_phase_override_spec("root", match_blockers=root_blockers),
        _default_lifecycle_phase_override_spec(
            "origin",
            match_blockers=origin_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "provenance",
            match_blockers=provenance_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "ancestry",
            match_blockers=ancestry_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "lineage",
            match_blockers=ancestry_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "heritage",
            match_blockers=heritage_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "legacy",
            match_blockers=legacy_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "longevity",
            match_blockers=longevity_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "durability",
            match_blockers=durability_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "persistence",
            match_blockers=persistence_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "tenure",
            match_blockers=tenure_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "residency",
            match_blockers=residency_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "standing",
            match_blockers=standing_blockers,
        ),
        _default_lifecycle_phase_override_spec(
            "disposition",
            match_blockers=disposition_blockers,
            skip_decisions=("complete_lifecycle_disposition",),
        ),
    )


def _build_certification_phase_override_specs() -> tuple[_LifecyclePhaseOverrideSpec, ...]:
    return (
        _default_lifecycle_phase_override_spec(
            "conclusion",
            match_blockers=("disposition",),
            skip_decisions=("complete_lifecycle_conclusion",),
        ),
        _default_lifecycle_phase_override_spec(
            "completion",
            match_blockers=("conclusion",),
            skip_decisions=("complete_lifecycle_completion",),
        ),
        _default_lifecycle_phase_override_spec(
            "finality",
            match_blockers=("completion",),
            skip_decisions=("finalize_lifecycle_finality",),
        ),
        _default_lifecycle_phase_override_spec(
            "enactment",
            match_blockers=("finality",),
            skip_decisions=("enact_lifecycle_enactment",),
        ),
        _default_lifecycle_phase_override_spec(
            "authorization",
            match_blockers=("enactment",),
            hold_decisions=(),
            buffer_decisions=(),
            skip_decisions=(),
            match_stage_label=False,
        ),
        _default_lifecycle_phase_override_spec(
            "endorsement",
            match_blockers=("authorization",),
            skip_decisions=("endorse_lifecycle_endorsement",),
        ),
        _default_lifecycle_phase_override_spec(
            "ratification",
            match_blockers=("endorsement",),
            skip_decisions=("ratify_lifecycle_ratification",),
        ),
        _default_lifecycle_phase_override_spec(
            "confirmation",
            match_blockers=("ratification",),
            skip_decisions=("confirm_lifecycle_confirmation",),
        ),
        _default_lifecycle_phase_override_spec(
            "certification",
            match_blockers=("confirmation",),
            skip_decisions=("certify_lifecycle_certification",),
        ),
        _default_lifecycle_phase_override_spec(
            "verification",
            match_blockers=("certification",),
            skip_decisions=("verify_lifecycle_verification",),
        ),
    )


def _build_stewardship_phase_override_specs() -> tuple[_LifecyclePhaseOverrideSpec, ...]:
    return (
        _default_lifecycle_phase_override_spec(
            "attestation",
            action_blockers=("verification",),
            skip_decisions=("attest_lifecycle_attestation",),
        ),
        _default_lifecycle_phase_override_spec(
            "assurance",
            action_blockers=("attestation",),
            skip_decisions=("assure_lifecycle_assurance",),
        ),
        _default_lifecycle_phase_override_spec(
            "oversight",
            action_blockers=("attestation", "assurance"),
            skip_decisions=("oversee_lifecycle_oversight",),
        ),
        _default_lifecycle_phase_override_spec(
            "guardianship",
            action_blockers=("assurance", "oversight"),
            skip_decisions=("guard_lifecycle_guardianship",),
        ),
        _default_lifecycle_phase_override_spec(
            "stewardship",
            action_blockers=("assurance", "oversight", "guardianship"),
            skip_decisions=("steward_lifecycle_stewardship",),
        ),
        _default_lifecycle_phase_override_spec(
            "sustainment",
            action_blockers=("guardianship", "stewardship"),
            skip_decisions=("sustain_lifecycle_sustainment",),
        ),
        _default_lifecycle_phase_override_spec(
            "continuation",
            action_blockers=("sustainment",),
            skip_decisions=("keep_lifecycle_continuation",),
        ),
    )


def _build_activation_phase_override_specs() -> tuple[_LifecyclePhaseOverrideSpec, ...]:
    return (
        _default_lifecycle_phase_override_spec(
            "handoff",
            match_blockers=("continuation",),
        ),
        _default_lifecycle_phase_override_spec(
            "launch",
            match_blockers=("handoff",),
        ),
        _default_lifecycle_phase_override_spec(
            "trigger",
            match_blockers=("launch",),
        ),
        _default_lifecycle_phase_override_spec(
            "arming",
            match_blockers=("trigger",),
        ),
        _default_lifecycle_phase_override_spec(
            "readiness",
            match_blockers=("arming",),
        ),
        _default_lifecycle_phase_override_spec(
            "resumption",
            match_blockers=("readiness",),
        ),
        _default_lifecycle_phase_override_spec(
            "reactivation",
            match_blockers=("resumption",),
        ),
        _default_lifecycle_phase_override_spec(
            "reentry",
            match_blockers=("reactivation",),
        ),
        _default_lifecycle_phase_override_spec(
            "selectability",
            match_blockers=("reentry",),
            skip_decisions=("keep_lifecycle_selectable",),
        ),
        _default_lifecycle_phase_override_spec(
            "candidate",
            match_blockers=("selectability",),
        ),
        _default_lifecycle_phase_override_spec(
            "eligibility",
            match_blockers=("candidate",),
            skip_decisions=("keep_lifecycle_eligible",),
        ),
        _default_lifecycle_phase_override_spec(
            "retention",
            match_blockers=("eligibility",),
            skip_decisions=("retain_lifecycle_retention",),
        ),
        _default_lifecycle_phase_override_spec(
            "availability",
            match_blockers=("retention",),
            terminate_decisions=(
                "close_loop_lifecycle_availability",
                "retire_lifecycle_availability",
            ),
            skip_decisions=("keep_lifecycle_available",),
        ),
        _default_lifecycle_phase_override_spec(
            "closure",
            match_blockers=("availability",),
            terminate_decisions=(
                "close_loop_lifecycle_closure",
                "retire_lifecycle_closure",
            ),
            skip_decisions=("keep_open_lifecycle_closure",),
        ),
        _default_lifecycle_phase_override_spec(
            "settlement",
            match_blockers=("closure",),
            terminate_decisions=(
                "close_lifecycle_settlement",
                "retire_lifecycle_settlement",
            ),
            hold_decisions=("hold_lifecycle_settlement",),
            skip_decisions=("keep_lifecycle_active",),
        ),
        _default_lifecycle_phase_override_spec(
            "activation",
            match_blockers=("settlement",),
            terminate_decisions=("retire_lifecycle_line",),
            hold_decisions=("hold_current_lifecycle_stage",),
            buffer_decisions=("buffer_current_lifecycle_stage",),
            skip_decisions=("activate_next_lifecycle_stage",),
        ),
        _default_lifecycle_phase_override_spec(
            "resolution",
            match_blockers=("settlement",),
            action_blockers=("activation",),
            terminate_decisions=("retire_lifecycle_resolution",),
            hold_decisions=("hold_lifecycle_resolution",),
            buffer_decisions=("buffer_lifecycle_resolution",),
            skip_decisions=("continue_lifecycle_resolution",),
            stage_label_key="current_stage_label",
        ),
    )


def _build_lifecycle_phase_override_specs() -> tuple[_LifecyclePhaseOverrideSpec, ...]:
    return (
        *_build_foundation_phase_override_specs(),
        *_build_heritage_phase_override_specs(),
        *_build_certification_phase_override_specs(),
        *_build_stewardship_phase_override_specs(),
        *_build_activation_phase_override_specs(),
    )


_LIFECYCLE_PHASE_OVERRIDE_SPECS = _build_lifecycle_phase_override_specs()


async def build_followup_item(
    *,
    stream_service: StreamService,
    session_id: str,
    reference_time: datetime,
    runtime_projector_version: str,
) -> dict[str, Any] | None:
    """Build a single followup item for a session.

    Extracted from ProactiveFollowupService._build_followup_item to keep
    the service class thin while preserving all original logic.
    """
    resolved_inputs = await _resolve_followup_inputs(
        stream_service=stream_service,
        session_id=session_id,
        reference_time=reference_time,
        runtime_projector_version=runtime_projector_version,
    )
    if resolved_inputs is None:
        return None
    context, stage_resolution = resolved_inputs
    projected = _collect_projected_followup_state_bundle(context.state)
    payloads = _collect_followup_payload_bundle(context)
    queue = _resolve_followup_queue_bundle(
        context=context,
        stage_resolution=stage_resolution,
        projected=projected,
        payloads=payloads,
        reference_time=reference_time,
    )
    if queue is None:
        return None
    return _assemble_followup_item(
        _FollowupAssemblyBundle(
            session_id=session_id,
            context=context,
            stage_resolution=stage_resolution,
            projected=projected,
            payloads=payloads,
            queue=queue,
        )
    )


async def _resolve_followup_inputs(
    *,
    stream_service: StreamService,
    session_id: str,
    reference_time: datetime,
    runtime_projector_version: str,
) -> tuple[_FollowupContext, _StageResolution] | None:
    context = await _load_followup_context(
        stream_service=stream_service,
        session_id=session_id,
        reference_time=reference_time,
        runtime_projector_version=runtime_projector_version,
    )
    if context is None:
        return None
    stage_resolution = _resolve_followup_stage(
        context=context,
        reference_time=reference_time,
    )
    if stage_resolution is None:
        return None
    return context, stage_resolution


def _collect_projected_followup_state_bundle(
    state: dict[str, Any],
) -> _ProjectedFollowupStateBundle:
    projections = _collect_projected_followup_state(state)
    return _ProjectedFollowupStateBundle(
        projections=projections,
        projected_stage_state=projections["proactive_stage_state_decision"],
        projected_line_state=projections["proactive_line_state_decision"],
        projected_line_transition=projections["proactive_line_transition_decision"],
        projected_line_machine=projections["proactive_line_machine_decision"],
        projected_lifecycle_state=projections["proactive_lifecycle_state_decision"],
        projected_lifecycle_transition=projections["proactive_lifecycle_transition_decision"],
        projected_lifecycle_machine=projections["proactive_lifecycle_machine_decision"],
        projected_lifecycle_envelope=projections["proactive_lifecycle_envelope_decision"],
        projected_lifecycle_scheduler=projections["proactive_lifecycle_scheduler_decision"],
        projected_lifecycle_window=projections["proactive_lifecycle_window_decision"],
        projected_lifecycle_queue=projections["proactive_lifecycle_queue_decision"],
        projected_lifecycle_dispatch=projections["proactive_lifecycle_dispatch_decision"],
        projected_lifecycle_outcome=projections["proactive_lifecycle_outcome_decision"],
        projected_lifecycle_resolution=projections["proactive_lifecycle_resolution_decision"],
        lifecycle_phase_overrides=_collect_followup_lifecycle_phase_overrides(projections),
        projected_dispatch_envelope=dict(state.get("proactive_dispatch_envelope_decision") or {}),
        runtime_coordination_snapshot=dict(state.get("runtime_coordination_snapshot") or {}),
        lifecycle_controller_projection=dict(
            state.get("proactive_lifecycle_controller_decision") or {}
        ),
    )


def _collect_followup_payload_bundle(
    context: _FollowupContext,
) -> _FollowupPayloadBundle:
    return _FollowupPayloadBundle(
        dispatch_gate_payload=_event_payload(context.latest_proactive_dispatch_gate_event),
        dispatch_feedback_payload=_event_payload(context.latest_proactive_dispatch_feedback_event),
        stage_controller_payload=_event_payload(context.latest_proactive_stage_controller_event),
        line_controller_payload=_event_payload(context.latest_proactive_line_controller_event),
    )


def _resolve_followup_queue_bundle(
    *,
    context: _FollowupContext,
    stage_resolution: _StageResolution,
    projected: _ProjectedFollowupStateBundle,
    payloads: _FollowupPayloadBundle,
    reference_time: datetime,
) -> _ResolvedFollowupQueueBundle | None:
    lifecycle_override_state = _resolve_followup_lifecycle_queue_override(
        phase_overrides=projected.lifecycle_phase_overrides,
        current_stage_label=stage_resolution.current_stage_label,
        reference_time=reference_time,
        base_due_at=stage_resolution.base_due_at,
        due_at=stage_resolution.due_at,
        expires_at=stage_resolution.expires_at,
        schedule_reason=stage_resolution.schedule_reason,
        scheduling_deferred_until=stage_resolution.scheduling_deferred_until,
        queue_status=stage_resolution.queue_status,
        seconds_until_due=stage_resolution.seconds_until_due,
        seconds_overdue=stage_resolution.seconds_overdue,
        window_remaining_seconds=stage_resolution.window_remaining_seconds,
        window_seconds=stage_resolution.window_seconds,
    )
    if lifecycle_override_state is None:
        return None
    dispatch_override_state = _resolve_followup_dispatch_queue_override(
        projected_lifecycle_dispatch=projected.projected_lifecycle_dispatch,
        projected_lifecycle_queue=projected.projected_lifecycle_queue,
        current_stage_label=stage_resolution.current_stage_label,
        reference_time=reference_time,
        base_due_at=stage_resolution.base_due_at,
        due_at=lifecycle_override_state.due_at,
        expires_at=lifecycle_override_state.expires_at,
        schedule_reason=lifecycle_override_state.schedule_reason,
        scheduling_deferred_until=lifecycle_override_state.scheduling_deferred_until,
        queue_status=lifecycle_override_state.queue_status,
        seconds_until_due=lifecycle_override_state.seconds_until_due,
        seconds_overdue=lifecycle_override_state.seconds_overdue,
        window_remaining_seconds=lifecycle_override_state.window_remaining_seconds,
        window_seconds=stage_resolution.window_seconds,
        skip_lifecycle_dispatch_override=lifecycle_override_state.skip_dispatch_override,
    )
    if dispatch_override_state is None:
        return None
    proactive_stage_state = _resolve_followup_proactive_stage_state(
        projected_stage_state=projected.projected_stage_state,
        projected_dispatch_envelope=projected.projected_dispatch_envelope,
        current_stage_label=stage_resolution.current_stage_label,
        current_stage_index=stage_resolution.current_stage_index,
        max_dispatch_count=context.max_dispatch_count,
        queue_status=dispatch_override_state.queue_status,
        schedule_reason=dispatch_override_state.schedule_reason,
        current_stage_progression=stage_resolution.current_stage_progression,
        progression_advanced=stage_resolution.progression_advanced,
        current_stage_directive=stage_resolution.current_stage_directive,
        reengagement_plan=context.reengagement_plan,
        dispatch_gate_payload=payloads.dispatch_gate_payload,
        stage_controller_payload=payloads.stage_controller_payload,
        line_controller_payload=payloads.line_controller_payload,
        state=context.state,
    )
    return _ResolvedFollowupQueueBundle(
        due_at=dispatch_override_state.due_at,
        base_due_at=stage_resolution.base_due_at,
        expires_at=dispatch_override_state.expires_at,
        seconds_until_due=dispatch_override_state.seconds_until_due,
        seconds_overdue=dispatch_override_state.seconds_overdue,
        window_remaining_seconds=dispatch_override_state.window_remaining_seconds,
        schedule_reason=dispatch_override_state.schedule_reason,
        scheduling_deferred_until=dispatch_override_state.scheduling_deferred_until,
        queue_status=dispatch_override_state.queue_status,
        proactive_stage_state=proactive_stage_state,
    )


def _assemble_followup_item(bundle: _FollowupAssemblyBundle) -> dict[str, Any]:
    return {
        **_build_followup_overview_fields(bundle),
        **_build_followup_dispatch_and_line_fields(bundle),
        **_build_followup_lifecycle_core_fields(bundle),
        **_build_followup_generic_lifecycle_fields(bundle.projected),
        **_build_followup_schedule_and_timing_fields(bundle),
    }


def _resolve_followup_dispatch_queue_override(
    *,
    projected_lifecycle_dispatch: dict[str, Any],
    projected_lifecycle_queue: dict[str, Any],
    current_stage_label: str,
    reference_time: datetime,
    base_due_at: datetime | None,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    scheduling_deferred_until: datetime | None,
    queue_status: str,
    seconds_until_due: int | None,
    seconds_overdue: int | None,
    window_remaining_seconds: int | None,
    window_seconds: int,
    skip_lifecycle_dispatch_override: bool,
) -> _QueueOverrideState | None:
    lifecycle_dispatch_decision = str(projected_lifecycle_dispatch.get("decision") or "")
    lifecycle_dispatch_stage_label = str(
        projected_lifecycle_dispatch.get("current_stage_label") or ""
    )
    lifecycle_dispatch_delay_seconds = max(
        0,
        int(projected_lifecycle_dispatch.get("additional_delay_seconds") or 0),
    )
    dispatch_applies = (
        not skip_lifecycle_dispatch_override
        and lifecycle_dispatch_stage_label == current_stage_label
    )
    if dispatch_applies and lifecycle_dispatch_decision == "retire_lifecycle_dispatch":
        return None
    if dispatch_applies and lifecycle_dispatch_decision == "hold_lifecycle_dispatch":
        queue_status = "hold"
        seconds_until_due = None
        seconds_overdue = None
        window_remaining_seconds = None
    elif dispatch_applies and lifecycle_dispatch_decision == "reschedule_lifecycle_dispatch":
        if due_at is not None:
            due_at = due_at + timedelta(seconds=lifecycle_dispatch_delay_seconds)
            if expires_at is not None:
                expires_at = due_at + timedelta(seconds=window_seconds)
            scheduling_deferred_until = due_at
            if schedule_reason:
                if "lifecycle_dispatch_rescheduled" not in schedule_reason:
                    schedule_reason = f"{schedule_reason} | lifecycle_dispatch_rescheduled"
            else:
                schedule_reason = "lifecycle_dispatch_rescheduled"
            (
                queue_status,
                seconds_until_due,
                seconds_overdue,
                window_remaining_seconds,
            ) = _resolve_queue_status(
                reference_time=reference_time,
                base_due_at=base_due_at,
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                window_seconds=window_seconds,
            )
        else:
            queue_status = "scheduled"
    elif dispatch_applies and lifecycle_dispatch_decision in {
        "dispatch_lifecycle_now",
        "close_loop_lifecycle_dispatch",
    }:
        (
            queue_status,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        ) = _resolve_queue_status(
            reference_time=reference_time,
            base_due_at=base_due_at,
            due_at=due_at,
            expires_at=expires_at,
            schedule_reason=schedule_reason,
            window_seconds=window_seconds,
        )
        if queue_status not in {"due", "overdue"}:
            queue_status = (
                "overdue"
                if str(projected_lifecycle_queue.get("queue_status") or "") == "overdue"
                else "due"
            )
    return _QueueOverrideState(
        due_at=due_at,
        expires_at=expires_at,
        seconds_until_due=seconds_until_due,
        seconds_overdue=seconds_overdue,
        window_remaining_seconds=window_remaining_seconds,
        schedule_reason=schedule_reason,
        scheduling_deferred_until=scheduling_deferred_until,
        queue_status=queue_status,
    )


def _resolve_followup_proactive_stage_state(
    *,
    projected_stage_state: dict[str, Any],
    projected_dispatch_envelope: dict[str, Any],
    current_stage_label: str,
    current_stage_index: int,
    max_dispatch_count: int,
    queue_status: str,
    schedule_reason: str | None,
    current_stage_progression: dict[str, Any] | None,
    progression_advanced: bool,
    current_stage_directive: dict[str, Any] | None,
    reengagement_plan: dict[str, Any],
    dispatch_gate_payload: dict[str, Any],
    stage_controller_payload: dict[str, Any],
    line_controller_payload: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    if (
        projected_stage_state.get("stage_label") == current_stage_label
        and projected_stage_state.get("queue_status") == queue_status
    ):
        return projected_stage_state
    matching_envelope = (
        projected_dispatch_envelope
        if projected_dispatch_envelope.get("stage_label") == current_stage_label
        else {}
    )
    return asdict(
        build_proactive_stage_state_decision(
            stage_label=current_stage_label,
            stage_index=current_stage_index,
            stage_count=max_dispatch_count,
            queue_status=queue_status,
            schedule_reason=schedule_reason,
            progression_action=str((current_stage_progression or {}).get("on_expired") or "none"),
            progression_advanced=progression_advanced,
            line_state=str(line_controller_payload.get("line_state") or "steady"),
            current_stage_delivery_mode=str(
                (current_stage_directive or {}).get("delivery_mode") or "single_message"
            ),
            current_stage_autonomy_mode=str(
                (current_stage_directive or {}).get("autonomy_mode") or "light_invitation"
            ),
            current_reengagement_delivery_mode=str(
                reengagement_plan.get("delivery_mode") or "single_message"
            ),
            selected_strategy_key=str(
                matching_envelope.get("selected_strategy_key")
                or reengagement_plan.get("strategy_key")
                or "none"
            ),
            selected_pressure_mode=str(
                matching_envelope.get("selected_pressure_mode")
                or reengagement_plan.get("pressure_mode")
                or "none"
            ),
            selected_autonomy_signal=str(
                matching_envelope.get("selected_autonomy_signal")
                or reengagement_plan.get("autonomy_signal")
                or "none"
            ),
            dispatch_envelope_key=matching_envelope.get("envelope_key"),
            dispatch_envelope_decision=matching_envelope.get("decision"),
            dispatch_gate_decision=str(dispatch_gate_payload.get("decision") or ""),
            aggregate_controller_decision=str(
                dict(state.get("proactive_aggregate_controller_decision") or {}).get("decision")
                or ""
            ),
            orchestration_controller_decision=str(
                dict(state.get("proactive_orchestration_controller_decision") or {}).get("decision")
                or ""
            ),
            stage_controller_decision=str(stage_controller_payload.get("decision") or ""),
            line_controller_decision=str(line_controller_payload.get("decision") or ""),
        )
    )


async def _load_followup_context(
    *,
    stream_service: StreamService,
    session_id: str,
    reference_time: datetime,
    runtime_projector_version: str,
) -> _FollowupContext | None:
    try:
        state, events = await _load_followup_state_and_events(
            stream_service=stream_service,
            session_id=session_id,
            runtime_projector_version=runtime_projector_version,
        )
    except LegacyLifecycleStreamUnsupportedError:
        return None
    session_details = _resolve_followup_session_details(state)
    if session_details is None:
        return None
    session, session_source = session_details
    plan_state = _extract_followup_plan_state(state)
    directive = plan_state["directive"]
    if not directive:
        return None
    latest_events = _collect_followup_latest_events(events)
    stage_metadata = _resolve_followup_stage_metadata(
        events=events,
        reference_time=reference_time,
        directive=directive,
        proactive_cadence_plan=plan_state["proactive_cadence_plan"],
        proactive_guardrail_plan=plan_state["proactive_guardrail_plan"],
        proactive_orchestration_plan=plan_state["proactive_orchestration_plan"],
        proactive_progression_plan=plan_state["proactive_progression_plan"],
        latest_proactive_event=latest_events.latest_proactive_event,
    )
    if stage_metadata is None:
        return None
    return _FollowupContext(
        state=state,
        session=session,
        session_source=session_source,
        directive=directive,
        guidance_plan=plan_state["guidance_plan"],
        conversation_cadence_plan=plan_state["conversation_cadence_plan"],
        session_ritual_plan=plan_state["session_ritual_plan"],
        somatic_orchestration_plan=plan_state["somatic_orchestration_plan"],
        proactive_cadence_plan=plan_state["proactive_cadence_plan"],
        reengagement_matrix_assessment=plan_state["reengagement_matrix_assessment"],
        selected_matrix_candidate=plan_state["selected_matrix_candidate"],
        reengagement_plan=plan_state["reengagement_plan"],
        proactive_scheduling_plan=plan_state["proactive_scheduling_plan"],
        proactive_guardrail_plan=plan_state["proactive_guardrail_plan"],
        proactive_orchestration_plan=plan_state["proactive_orchestration_plan"],
        proactive_actuation_plan=plan_state["proactive_actuation_plan"],
        proactive_progression_plan=plan_state["proactive_progression_plan"],
        events=events,
        latest_proactive_event=latest_events.latest_proactive_event,
        latest_proactive_scheduling_event=latest_events.latest_proactive_scheduling_event,
        latest_proactive_orchestration_event=latest_events.latest_proactive_orchestration_event,
        latest_proactive_actuation_event=latest_events.latest_proactive_actuation_event,
        latest_proactive_progression_event=latest_events.latest_proactive_progression_event,
        latest_proactive_dispatch_gate_event=latest_events.latest_proactive_dispatch_gate_event,
        latest_proactive_dispatch_feedback_event=latest_events.latest_proactive_dispatch_feedback_event,
        latest_proactive_stage_controller_event=latest_events.latest_proactive_stage_controller_event,
        latest_proactive_line_controller_event=latest_events.latest_proactive_line_controller_event,
        latest_session_event=latest_events.latest_session_event,
        latest_user_event=latest_events.latest_user_event,
        latest_assistant_event=latest_events.latest_assistant_event,
        directive_time=stage_metadata.directive_time,
        dispatch_events_for_directive=stage_metadata.dispatch_events_for_directive,
        dispatched_stage_count=stage_metadata.dispatched_stage_count,
        stage_labels=stage_metadata.stage_labels,
        stage_intervals_seconds=stage_metadata.stage_intervals_seconds,
        close_after_stage_index=stage_metadata.close_after_stage_index,
        max_dispatch_count=stage_metadata.max_dispatch_count,
        stage_index_by_label=stage_metadata.stage_index_by_label,
        close_loop_stage=stage_metadata.close_loop_stage,
    )


async def _load_followup_state_and_events(
    *,
    stream_service: StreamService,
    session_id: str,
    runtime_projector_version: str,
) -> tuple[dict[str, Any], list[StoredEvent]]:
    projection, events = await asyncio.gather(
        stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version=runtime_projector_version,
        ),
        stream_service.read_stream(stream_id=session_id),
    )
    return dict(projection["state"]), events


def _resolve_followup_session_details(
    state: dict[str, Any],
) -> tuple[dict[str, Any], str] | None:
    session = dict(state.get("session") or {})
    if not session.get("started"):
        return None
    session_source = str((session.get("metadata") or {}).get("source") or "session")
    if session_source == "scenario_evaluation":
        return None
    archive_status = dict(state.get("archive_status") or {})
    if archive_status.get("archived"):
        return None
    return session, session_source


def _extract_followup_plan_state(state: dict[str, Any]) -> dict[str, Any]:
    reengagement_matrix_assessment = dict(state.get("reengagement_matrix_assessment") or {})
    return {
        "directive": dict(state.get("proactive_followup_directive") or {}),
        "guidance_plan": dict(state.get("guidance_plan") or {}),
        "conversation_cadence_plan": dict(state.get("conversation_cadence_plan") or {}),
        "session_ritual_plan": dict(state.get("session_ritual_plan") or {}),
        "somatic_orchestration_plan": dict(state.get("somatic_orchestration_plan") or {}),
        "proactive_cadence_plan": dict(state.get("proactive_cadence_plan") or {}),
        "reengagement_matrix_assessment": reengagement_matrix_assessment,
        "selected_matrix_candidate": _selected_matrix_candidate(reengagement_matrix_assessment),
        "reengagement_plan": dict(state.get("reengagement_plan") or {}),
        "proactive_scheduling_plan": dict(state.get("proactive_scheduling_plan") or {}),
        "proactive_guardrail_plan": dict(state.get("proactive_guardrail_plan") or {}),
        "proactive_orchestration_plan": dict(state.get("proactive_orchestration_plan") or {}),
        "proactive_actuation_plan": dict(state.get("proactive_actuation_plan") or {}),
        "proactive_progression_plan": dict(state.get("proactive_progression_plan") or {}),
    }


def _collect_followup_latest_events(
    events: list[StoredEvent],
) -> _FollowupLatestEvents:
    return _FollowupLatestEvents(
        latest_proactive_event=_latest_event(
            events,
            event_type=PROACTIVE_FOLLOWUP_UPDATED,
        ),
        latest_proactive_scheduling_event=_latest_event(
            events,
            event_type=PROACTIVE_SCHEDULING_UPDATED,
        ),
        latest_proactive_orchestration_event=_latest_event(
            events,
            event_type=PROACTIVE_ORCHESTRATION_UPDATED,
        ),
        latest_proactive_actuation_event=_latest_event(
            events,
            event_type=PROACTIVE_ACTUATION_UPDATED,
        ),
        latest_proactive_progression_event=_latest_event(
            events,
            event_type=PROACTIVE_PROGRESSION_UPDATED,
        ),
        latest_proactive_dispatch_gate_event=_latest_event(
            events,
            event_type=PROACTIVE_DISPATCH_GATE_UPDATED,
        ),
        latest_proactive_dispatch_feedback_event=_latest_event(
            events,
            event_type=PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
        ),
        latest_proactive_stage_controller_event=_latest_event(
            events,
            event_type=PROACTIVE_STAGE_CONTROLLER_UPDATED,
        ),
        latest_proactive_line_controller_event=_latest_event(
            events,
            event_type=PROACTIVE_LINE_CONTROLLER_UPDATED,
        ),
        latest_session_event=_latest_event(
            events,
            event_type=SESSION_STARTED,
        ),
        latest_user_event=_latest_event(events, event_type=USER_MESSAGE_RECEIVED),
        latest_assistant_event=_latest_event(
            events,
            event_type=ASSISTANT_MESSAGE_SENT,
        ),
    )


def _resolve_followup_stage_metadata(
    *,
    events: list[StoredEvent],
    reference_time: datetime,
    directive: dict[str, Any],
    proactive_cadence_plan: dict[str, Any],
    proactive_guardrail_plan: dict[str, Any],
    proactive_orchestration_plan: dict[str, Any],
    proactive_progression_plan: dict[str, Any],
    latest_proactive_event: StoredEvent | None,
) -> _FollowupStageMetadata | None:
    directive_time = (
        latest_proactive_event.occurred_at
        if latest_proactive_event is not None
        else (events[-1].occurred_at if events else reference_time)
    )
    dispatch_events_for_directive = [
        event
        for event in events
        if event.event_type == PROACTIVE_FOLLOWUP_DISPATCHED
        and latest_proactive_event is not None
        and event.occurred_at >= latest_proactive_event.occurred_at
    ]
    if dispatch_events_for_directive:
        latest_dispatch_payload = dict(dispatch_events_for_directive[-1].payload)
        if (
            int(
                latest_dispatch_payload.get(
                    "proactive_cadence_remaining_after_dispatch",
                    1,
                )
                or 0
            )
            <= 0
        ):
            return None
    dispatched_stage_count = len(dispatch_events_for_directive)
    stage_labels = [
        str(item)
        for item in list(proactive_cadence_plan.get("stage_labels") or [])
        if str(item).strip()
    ]
    stage_intervals_seconds = [
        max(0, int(item))
        for item in list(proactive_cadence_plan.get("stage_intervals_seconds") or [])
    ]
    close_after_stage_index = max(
        0,
        int(proactive_cadence_plan.get("close_after_stage_index") or 0),
    )
    if not stage_labels:
        stage_labels = ["first_touch"]
        stage_intervals_seconds = [max(0, int(directive.get("trigger_after_seconds") or 0))]
        close_after_stage_index = 1
    max_dispatch_count = max(
        1,
        int(proactive_guardrail_plan.get("max_dispatch_count") or close_after_stage_index),
    )
    if close_after_stage_index > 0:
        max_dispatch_count = min(max_dispatch_count, close_after_stage_index)
    if dispatched_stage_count >= max_dispatch_count:
        return None
    stage_index_by_label = {label: index + 1 for index, label in enumerate(stage_labels)}
    close_loop_stage = str(
        proactive_progression_plan.get("close_loop_stage")
        or proactive_orchestration_plan.get("close_loop_stage")
        or stage_labels[-1]
    )
    return _FollowupStageMetadata(
        directive_time=directive_time,
        dispatch_events_for_directive=dispatch_events_for_directive,
        dispatched_stage_count=dispatched_stage_count,
        stage_labels=stage_labels,
        stage_intervals_seconds=stage_intervals_seconds,
        close_after_stage_index=close_after_stage_index,
        max_dispatch_count=max_dispatch_count,
        stage_index_by_label=stage_index_by_label,
        close_loop_stage=close_loop_stage,
    )


def _resolve_followup_stage(
    *,
    context: _FollowupContext,
    reference_time: datetime,
) -> _StageResolution | None:
    current_stage_index = context.dispatched_stage_count + 1
    current_stage_payload = _select_followup_stage_payload(
        context=context,
        current_stage_index=current_stage_index,
    )
    current_stage_directive = None
    current_stage_actuation = None
    current_stage_progression = None
    current_stage_guardrail = None

    due_at: datetime | None = None
    base_due_at: datetime | None = None
    expires_at: datetime | None = None
    seconds_until_due: int | None = None
    seconds_overdue: int | None = None
    window_remaining_seconds: int | None = None
    schedule_reason: str | None = None
    scheduling_deferred_until: datetime | None = None
    progression_anchor_at: datetime | None = None
    progression_advanced = False
    progression_reason: str | None = None
    progression_applied_actions: list[str] = []
    schedule_snapshot: _StageScheduleSnapshot | None = None

    window_seconds = 0
    directive_status = str(context.directive.get("status") or "hold")
    queue_status = "hold"
    if directive_status == "ready" and bool(context.directive.get("eligible")):
        window_seconds = max(
            0,
            int(
                context.proactive_cadence_plan.get("window_seconds")
                or context.directive.get("window_seconds")
                or 0
            ),
        )
        while current_stage_index <= context.max_dispatch_count:
            schedule_snapshot = _build_stage_schedule_snapshot(
                context=context,
                reference_time=reference_time,
                current_stage_index=current_stage_index,
                window_seconds=window_seconds,
                progression_anchor_at=progression_anchor_at,
            )
            if schedule_snapshot.queue_status != "overdue":
                break
            progression_advance = _resolve_followup_stage_progression_advance(
                context=context,
                reference_time=reference_time,
                current_stage_index=current_stage_index,
                schedule_snapshot=schedule_snapshot,
                progression_applied_actions=progression_applied_actions,
            )
            if progression_advance is None:
                break
            progression_advanced = True
            if progression_advance.next_stage_index <= current_stage_index:
                return None
            if progression_advance.next_stage_index > context.max_dispatch_count:
                return None
            progression_reason = progression_advance.progression_reason
            current_stage_index = progression_advance.next_stage_index
            progression_anchor_at = progression_advance.progression_anchor_at

        if current_stage_index > context.max_dispatch_count:
            return None
        current_stage_payload = (
            schedule_snapshot.payload
            if schedule_snapshot is not None
            else _select_followup_stage_payload(
                context=context,
                current_stage_index=current_stage_index,
            )
        )
        current_stage_directive = current_stage_payload.current_stage_directive
        current_stage_actuation = current_stage_payload.current_stage_actuation
        current_stage_progression = current_stage_payload.current_stage_progression
        current_stage_guardrail = current_stage_payload.current_stage_guardrail
        if schedule_snapshot is not None:
            due_at = schedule_snapshot.due_at
            base_due_at = schedule_snapshot.base_due_at
            expires_at = schedule_snapshot.expires_at
            seconds_until_due = schedule_snapshot.seconds_until_due
            seconds_overdue = schedule_snapshot.seconds_overdue
            window_remaining_seconds = schedule_snapshot.window_remaining_seconds
            schedule_reason = schedule_snapshot.schedule_reason
            scheduling_deferred_until = schedule_snapshot.scheduling_deferred_until
            queue_status = schedule_snapshot.queue_status

    return _StageResolution(
        directive_status=directive_status,
        window_seconds=window_seconds,
        current_stage_index=current_stage_index,
        current_stage_label=current_stage_payload.current_stage_label,
        current_stage_directive=current_stage_directive,
        current_stage_actuation=current_stage_actuation,
        current_stage_progression=current_stage_progression,
        current_stage_guardrail=current_stage_guardrail,
        due_at=due_at,
        base_due_at=base_due_at,
        expires_at=expires_at,
        seconds_until_due=seconds_until_due,
        seconds_overdue=seconds_overdue,
        window_remaining_seconds=window_remaining_seconds,
        schedule_reason=schedule_reason,
        scheduling_deferred_until=scheduling_deferred_until,
        progression_advanced=progression_advanced,
        progression_reason=progression_reason,
        queue_status=queue_status,
    )


def _select_followup_stage_payload(
    *,
    context: _FollowupContext,
    current_stage_index: int,
) -> _StagePayloadSelection:
    current_stage_label = context.stage_labels[
        min(current_stage_index - 1, len(context.stage_labels) - 1)
    ]
    return _StagePayloadSelection(
        current_stage_label=current_stage_label,
        current_stage_directive=_stage_entry(
            context.proactive_orchestration_plan.get("stage_directives"),
            current_stage_label,
        ),
        current_stage_actuation=_stage_entry(
            context.proactive_actuation_plan.get("stage_actuations"),
            current_stage_label,
        ),
        current_stage_progression=_stage_entry(
            context.proactive_progression_plan.get("stage_progressions"),
            current_stage_label,
        ),
        current_stage_guardrail=_stage_entry(
            context.proactive_guardrail_plan.get("stage_guardrails"),
            current_stage_label,
        ),
    )


def _build_stage_schedule_snapshot(
    *,
    context: _FollowupContext,
    reference_time: datetime,
    current_stage_index: int,
    window_seconds: int,
    progression_anchor_at: datetime | None,
) -> _StageScheduleSnapshot:
    payload = _select_followup_stage_payload(
        context=context,
        current_stage_index=current_stage_index,
    )
    trigger_after_seconds = context.stage_intervals_seconds[
        min(
            current_stage_index - 1,
            len(context.stage_intervals_seconds) - 1,
        )
    ]
    (
        base_due_at,
        due_at,
        expires_at,
        seconds_until_due,
        seconds_overdue,
        window_remaining_seconds,
        schedule_reason,
        scheduling_deferred_until,
    ) = _compute_stage_schedule(
        reference_time=reference_time,
        directive_time=context.directive_time,
        dispatch_events_for_directive=context.dispatch_events_for_directive,
        latest_assistant_event=context.latest_assistant_event,
        proactive_scheduling_plan=context.proactive_scheduling_plan,
        trigger_after_seconds=trigger_after_seconds,
        window_seconds=window_seconds,
        progression_anchor_at=progression_anchor_at,
    )
    due_at, expires_at, schedule_reason = _apply_matrix_learning_spacing(
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        window_seconds=window_seconds,
        current_stage_label=payload.current_stage_label,
        reengagement_matrix_assessment=context.reengagement_matrix_assessment,
    )
    due_at, expires_at, schedule_reason = _apply_stage_guardrail(
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        latest_user_event=context.latest_user_event,
        dispatch_events_for_directive=context.dispatch_events_for_directive,
        current_stage_guardrail=payload.current_stage_guardrail,
    )
    due_at, expires_at, schedule_reason = _apply_stage_controller(
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        window_seconds=window_seconds,
        current_stage_label=payload.current_stage_label,
        latest_stage_controller_event=context.latest_proactive_stage_controller_event,
    )
    due_at, expires_at, schedule_reason = _apply_line_controller(
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        window_seconds=window_seconds,
        current_stage_label=payload.current_stage_label,
        latest_line_controller_event=context.latest_proactive_line_controller_event,
    )
    due_at, expires_at, schedule_reason = _apply_dispatch_gate(
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        window_seconds=window_seconds,
        current_stage_label=payload.current_stage_label,
        dispatch_events_for_directive=context.dispatch_events_for_directive,
        latest_dispatch_gate_event=context.latest_proactive_dispatch_gate_event,
    )
    (
        queue_status,
        seconds_until_due,
        seconds_overdue,
        window_remaining_seconds,
    ) = _resolve_queue_status(
        reference_time=reference_time,
        base_due_at=base_due_at,
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        window_seconds=window_seconds,
    )
    return _StageScheduleSnapshot(
        payload=payload,
        due_at=due_at,
        base_due_at=base_due_at,
        expires_at=expires_at,
        seconds_until_due=seconds_until_due,
        seconds_overdue=seconds_overdue,
        window_remaining_seconds=window_remaining_seconds,
        schedule_reason=schedule_reason,
        scheduling_deferred_until=scheduling_deferred_until,
        queue_status=queue_status,
    )


def _resolve_followup_stage_progression_advance(
    *,
    context: _FollowupContext,
    reference_time: datetime,
    current_stage_index: int,
    schedule_snapshot: _StageScheduleSnapshot,
    progression_applied_actions: list[str],
) -> _StageProgressionAdvance | None:
    max_overdue_seconds = max(
        0,
        int(
            (schedule_snapshot.payload.current_stage_progression or {}).get("max_overdue_seconds")
            or 0
        ),
    )
    if (
        schedule_snapshot.expires_at is None
        or reference_time <= schedule_snapshot.expires_at + timedelta(seconds=max_overdue_seconds)
    ):
        return None
    expired_action = str(
        (schedule_snapshot.payload.current_stage_progression or {}).get("on_expired")
        or "close_line"
    )
    if expired_action == "close_line":
        return _StageProgressionAdvance(
            next_stage_index=current_stage_index,
            progression_anchor_at=schedule_snapshot.expires_at
            + timedelta(seconds=max_overdue_seconds),
            progression_reason="",
        )
    if expired_action == "jump_to_close_loop":
        next_stage_index = context.stage_index_by_label.get(
            context.close_loop_stage,
            context.close_after_stage_index,
        )
    else:
        next_stage_index = min(
            current_stage_index + 1,
            context.close_after_stage_index,
        )
    next_stage_label = context.stage_labels[
        min(next_stage_index - 1, len(context.stage_labels) - 1)
    ]
    progression_applied_actions.append(
        f"{schedule_snapshot.payload.current_stage_label}:{expired_action}->{next_stage_label}"
    )
    return _StageProgressionAdvance(
        next_stage_index=next_stage_index,
        progression_anchor_at=schedule_snapshot.expires_at + timedelta(seconds=max_overdue_seconds),
        progression_reason=" | ".join(progression_applied_actions),
    )


def _collect_projected_followup_state(
    state: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    keys = [
        "proactive_stage_state_decision",
        "proactive_line_state_decision",
        "proactive_line_transition_decision",
        "proactive_line_machine_decision",
        "proactive_lifecycle_state_decision",
        "proactive_lifecycle_transition_decision",
        "proactive_lifecycle_machine_decision",
        "proactive_lifecycle_envelope_decision",
        "proactive_lifecycle_scheduler_decision",
        "proactive_lifecycle_window_decision",
        "proactive_lifecycle_queue_decision",
        "proactive_lifecycle_dispatch_decision",
        "proactive_lifecycle_outcome_decision",
        "proactive_lifecycle_resolution_decision",
        "proactive_dispatch_envelope_decision",
        *[f"proactive_lifecycle_{phase}_decision" for phase in _GENERIC_LIFECYCLE_PHASES],
    ]
    return {key: dict(state.get(key) or {}) for key in keys}


def _collect_followup_lifecycle_phase_overrides(
    projected: dict[str, dict[str, Any]],
) -> dict[str, _LifecyclePhaseOverride]:
    overrides: dict[str, _LifecyclePhaseOverride] = {}
    for spec in _LIFECYCLE_PHASE_OVERRIDE_SPECS:
        phase_projection = projected[f"proactive_lifecycle_{spec.phase}_decision"]
        overrides[spec.phase] = _LifecyclePhaseOverride(
            phase=spec.phase,
            decision=str(phase_projection.get("decision") or ""),
            stage_label=str(phase_projection.get(spec.stage_label_key) or ""),
            delay_seconds=max(
                0,
                int(phase_projection.get("additional_delay_seconds") or 0),
            ),
        )
    return overrides


def _apply_followup_buffer_queue_override(
    *,
    reason_tag: str,
    remove_reason_tag: str | None,
    delay_seconds: int,
    reference_time: datetime,
    base_due_at: datetime | None,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    scheduling_deferred_until: datetime | None,
    window_seconds: int,
) -> tuple[
    datetime | None,
    datetime | None,
    int | None,
    int | None,
    int | None,
    str | None,
    datetime | None,
    str,
]:
    if due_at is not None:
        due_at = due_at + timedelta(seconds=delay_seconds)
        if expires_at is not None:
            expires_at = due_at + timedelta(seconds=window_seconds)
        scheduling_deferred_until = due_at
    had_schedule_reason = bool(schedule_reason)
    if remove_reason_tag is not None and schedule_reason:
        schedule_reason = " | ".join(
            part for part in str(schedule_reason).split(" | ") if part != remove_reason_tag
        )
    if had_schedule_reason:
        if reason_tag not in str(schedule_reason):
            schedule_reason = f"{schedule_reason} | {reason_tag}"
    else:
        schedule_reason = reason_tag
    (
        queue_status,
        seconds_until_due,
        seconds_overdue,
        window_remaining_seconds,
    ) = _resolve_queue_status(
        reference_time=reference_time,
        base_due_at=base_due_at,
        due_at=due_at,
        expires_at=expires_at,
        schedule_reason=schedule_reason,
        window_seconds=window_seconds,
    )
    if queue_status not in {"scheduled", "waiting"}:
        queue_status = "scheduled"
    return (
        due_at,
        expires_at,
        seconds_until_due,
        seconds_overdue,
        window_remaining_seconds,
        schedule_reason,
        scheduling_deferred_until,
        queue_status,
    )


def _resolve_followup_lifecycle_queue_override(
    *,
    phase_overrides: dict[str, _LifecyclePhaseOverride],
    current_stage_label: str,
    reference_time: datetime,
    base_due_at: datetime | None,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    scheduling_deferred_until: datetime | None,
    queue_status: str,
    seconds_until_due: int | None,
    seconds_overdue: int | None,
    window_remaining_seconds: int | None,
    window_seconds: int,
) -> _QueueOverrideState | None:
    matched: dict[str, bool] = {}
    skip_dispatch_override = False
    for spec in _LIFECYCLE_PHASE_OVERRIDE_SPECS:
        override = phase_overrides[spec.phase]
        matches_current_stage = (
            spec.match_stage_label and override.stage_label == current_stage_label
        )
        raw_match = (
            override.decision in spec.terminate_decisions or matches_current_stage
        ) and not any(matched.get(phase, False) for phase in spec.match_blockers)
        matched[spec.phase] = raw_match
        if not raw_match or any(matched.get(phase, False) for phase in spec.action_blockers):
            continue
        if override.decision in spec.terminate_decisions:
            return None
        if override.decision in spec.hold_decisions:
            queue_status = "hold"
            seconds_until_due = None
            seconds_overdue = None
            window_remaining_seconds = None
            skip_dispatch_override = True
            continue
        if override.decision in spec.buffer_decisions:
            (
                due_at,
                expires_at,
                seconds_until_due,
                seconds_overdue,
                window_remaining_seconds,
                schedule_reason,
                scheduling_deferred_until,
                queue_status,
            ) = _apply_followup_buffer_queue_override(
                reason_tag=str(spec.buffer_reason_tag),
                remove_reason_tag=spec.buffer_remove_tag,
                delay_seconds=override.delay_seconds,
                reference_time=reference_time,
                base_due_at=base_due_at,
                due_at=due_at,
                expires_at=expires_at,
                schedule_reason=schedule_reason,
                scheduling_deferred_until=scheduling_deferred_until,
                window_seconds=window_seconds,
            )
            skip_dispatch_override = True
            continue
        if override.decision in spec.skip_decisions:
            skip_dispatch_override = True
    return _QueueOverrideState(
        due_at=due_at,
        expires_at=expires_at,
        seconds_until_due=seconds_until_due,
        seconds_overdue=seconds_overdue,
        window_remaining_seconds=window_remaining_seconds,
        schedule_reason=schedule_reason,
        scheduling_deferred_until=scheduling_deferred_until,
        queue_status=queue_status,
        skip_dispatch_override=skip_dispatch_override,
    )


def _event_payload(event: StoredEvent | None) -> dict[str, Any]:
    return dict(event.payload if event is not None else {})


def _build_followup_overview_fields(
    bundle: _FollowupAssemblyBundle,
) -> dict[str, Any]:
    context = bundle.context
    stage_resolution = bundle.stage_resolution
    queue = bundle.queue
    return {
        "session_id": bundle.session_id,
        "session_source": context.session_source,
        "queue_status": queue.queue_status,
        "directive_status": stage_resolution.directive_status,
        "style": context.directive.get("style"),
        "eligible": bool(context.directive.get("eligible")),
        "guidance_mode": context.guidance_plan.get("mode"),
        "guidance_pacing": context.guidance_plan.get("pacing"),
        "guidance_agency_mode": context.guidance_plan.get("agency_mode"),
        "guidance_ritual_action": context.guidance_plan.get("ritual_action"),
        "guidance_handoff_mode": context.guidance_plan.get("handoff_mode"),
        "guidance_carryover_mode": context.guidance_plan.get("carryover_mode"),
        "cadence_status": context.conversation_cadence_plan.get("status"),
        "cadence_turn_shape": context.conversation_cadence_plan.get("turn_shape"),
        "cadence_followup_tempo": context.conversation_cadence_plan.get("followup_tempo"),
        "cadence_user_space_mode": context.conversation_cadence_plan.get("user_space_mode"),
        "cadence_transition_intent": context.conversation_cadence_plan.get("transition_intent"),
        "cadence_next_checkpoint": context.conversation_cadence_plan.get("next_checkpoint"),
        "ritual_phase": context.session_ritual_plan.get("phase"),
        "ritual_opening_move": context.session_ritual_plan.get("opening_move"),
        "ritual_bridge_move": context.session_ritual_plan.get("bridge_move"),
        "ritual_closing_move": context.session_ritual_plan.get("closing_move"),
        "ritual_continuity_anchor": context.session_ritual_plan.get("continuity_anchor"),
        "ritual_somatic_shortcut": context.session_ritual_plan.get("somatic_shortcut"),
        "somatic_orchestration_status": context.somatic_orchestration_plan.get("status"),
        "somatic_orchestration_mode": context.somatic_orchestration_plan.get("primary_mode"),
        "somatic_orchestration_body_anchor": context.somatic_orchestration_plan.get("body_anchor"),
        "somatic_orchestration_followup_style": (
            context.somatic_orchestration_plan.get("followup_style")
        ),
        "somatic_orchestration_allow_in_followup": (
            context.somatic_orchestration_plan.get("allow_in_followup")
        ),
        "reengagement_matrix_key": context.reengagement_matrix_assessment.get("matrix_key"),
        "reengagement_matrix_selected_strategy": context.reengagement_matrix_assessment.get(
            "selected_strategy_key"
        ),
        "reengagement_matrix_selected_score": context.reengagement_matrix_assessment.get(
            "selected_score"
        ),
        "reengagement_matrix_blocked_count": int(
            context.reengagement_matrix_assessment.get("blocked_count") or 0
        ),
        "reengagement_matrix_learning_mode": context.reengagement_matrix_assessment.get(
            "learning_mode"
        ),
        "reengagement_matrix_learning_context_stratum": (
            context.reengagement_matrix_assessment.get("learning_context_stratum")
        ),
        "reengagement_matrix_learning_signal_count": int(
            context.reengagement_matrix_assessment.get("learning_signal_count") or 0
        ),
        "reengagement_matrix_selected_supporting_session_count": int(
            context.selected_matrix_candidate.get("supporting_session_count") or 0
        ),
        "reengagement_matrix_selected_contextual_supporting_session_count": int(
            context.selected_matrix_candidate.get("contextual_supporting_session_count") or 0
        ),
        "reengagement_ritual_mode": context.reengagement_plan.get("ritual_mode"),
        "reengagement_delivery_mode": context.reengagement_plan.get("delivery_mode"),
        "reengagement_strategy_key": context.reengagement_plan.get("strategy_key"),
        "reengagement_relational_move": context.reengagement_plan.get("relational_move"),
        "reengagement_pressure_mode": context.reengagement_plan.get("pressure_mode"),
        "reengagement_autonomy_signal": context.reengagement_plan.get("autonomy_signal"),
        "reengagement_sequence_objective": context.reengagement_plan.get("sequence_objective"),
        "reengagement_somatic_action": context.reengagement_plan.get("somatic_action"),
    }


def _build_followup_dispatch_and_line_fields(
    bundle: _FollowupAssemblyBundle,
) -> dict[str, Any]:
    payloads = bundle.payloads
    queue = bundle.queue
    projected = bundle.projected
    return {
        "proactive_dispatch_gate_key": payloads.dispatch_gate_payload.get("gate_key"),
        "proactive_dispatch_gate_decision": payloads.dispatch_gate_payload.get("decision"),
        "proactive_dispatch_gate_retry_after_seconds": int(
            payloads.dispatch_gate_payload.get("retry_after_seconds") or 0
        ),
        "proactive_dispatch_gate_strategy_key": payloads.dispatch_gate_payload.get(
            "selected_strategy_key"
        ),
        "proactive_dispatch_feedback_key": payloads.dispatch_feedback_payload.get("feedback_key"),
        "proactive_dispatch_feedback_changed": bool(
            payloads.dispatch_feedback_payload.get("changed")
        ),
        "proactive_dispatch_feedback_dispatch_count": int(
            payloads.dispatch_feedback_payload.get("dispatch_count") or 0
        ),
        "proactive_dispatch_feedback_gate_defer_count": int(
            payloads.dispatch_feedback_payload.get("gate_defer_count") or 0
        ),
        "proactive_dispatch_feedback_strategy_key": payloads.dispatch_feedback_payload.get(
            "selected_strategy_key"
        ),
        "proactive_dispatch_feedback_pressure_mode": payloads.dispatch_feedback_payload.get(
            "selected_pressure_mode"
        ),
        "proactive_dispatch_feedback_autonomy_signal": payloads.dispatch_feedback_payload.get(
            "selected_autonomy_signal"
        ),
        "proactive_dispatch_feedback_delivery_mode": payloads.dispatch_feedback_payload.get(
            "selected_delivery_mode"
        ),
        "proactive_dispatch_feedback_sequence_objective": payloads.dispatch_feedback_payload.get(
            "selected_sequence_objective"
        ),
        "proactive_dispatch_feedback_prior_stage_label": payloads.dispatch_feedback_payload.get(
            "prior_stage_label"
        ),
        "proactive_stage_state_key": queue.proactive_stage_state.get("state_key"),
        "proactive_stage_state_mode": queue.proactive_stage_state.get("state_mode"),
        "proactive_stage_state_source": queue.proactive_stage_state.get("primary_source"),
        "proactive_stage_state_queue_status": queue.proactive_stage_state.get("queue_status"),
        "proactive_stage_state_changed": bool(queue.proactive_stage_state.get("changed")),
        "proactive_stage_controller_key": payloads.stage_controller_payload.get("controller_key"),
        "proactive_stage_controller_decision": payloads.stage_controller_payload.get("decision"),
        "proactive_stage_controller_changed": bool(
            payloads.stage_controller_payload.get("changed")
        ),
        "proactive_stage_controller_target_stage_label": payloads.stage_controller_payload.get(
            "target_stage_label"
        ),
        "proactive_stage_controller_additional_delay_seconds": int(
            payloads.stage_controller_payload.get("additional_delay_seconds") or 0
        ),
        "proactive_stage_controller_strategy_key": payloads.stage_controller_payload.get(
            "selected_strategy_key"
        ),
        "proactive_stage_controller_pressure_mode": payloads.stage_controller_payload.get(
            "selected_pressure_mode"
        ),
        "proactive_stage_controller_autonomy_signal": payloads.stage_controller_payload.get(
            "selected_autonomy_signal"
        ),
        "proactive_stage_controller_delivery_mode": payloads.stage_controller_payload.get(
            "selected_delivery_mode"
        ),
        "proactive_line_controller_key": payloads.line_controller_payload.get("controller_key"),
        "proactive_line_controller_line_state": payloads.line_controller_payload.get("line_state"),
        "proactive_line_controller_decision": payloads.line_controller_payload.get("decision"),
        "proactive_line_controller_changed": bool(payloads.line_controller_payload.get("changed")),
        "proactive_line_controller_affected_stage_labels": list(
            payloads.line_controller_payload.get("affected_stage_labels") or []
        ),
        "proactive_line_controller_additional_delay_seconds": int(
            payloads.line_controller_payload.get("additional_delay_seconds") or 0
        ),
        "proactive_line_controller_pressure_mode": payloads.line_controller_payload.get(
            "selected_pressure_mode"
        ),
        "proactive_line_controller_autonomy_signal": payloads.line_controller_payload.get(
            "selected_autonomy_signal"
        ),
        "proactive_line_controller_delivery_mode": payloads.line_controller_payload.get(
            "selected_delivery_mode"
        ),
        "proactive_line_state_key": projected.projected_line_state.get("line_key"),
        "proactive_line_state_mode": projected.projected_line_state.get("line_state"),
        "proactive_line_state_lifecycle": projected.projected_line_state.get("lifecycle_mode"),
        "proactive_line_state_actionability": projected.projected_line_state.get("actionability"),
        "proactive_line_transition_key": projected.projected_line_transition.get("transition_key"),
        "proactive_line_transition_mode": projected.projected_line_transition.get(
            "transition_mode"
        ),
        "proactive_line_transition_exit_mode": projected.projected_line_transition.get(
            "line_exit_mode"
        ),
        "proactive_line_machine_key": projected.projected_line_machine.get("machine_key"),
        "proactive_line_machine_mode": projected.projected_line_machine.get("machine_mode"),
        "proactive_line_machine_lifecycle": projected.projected_line_machine.get("lifecycle_mode"),
        "proactive_line_machine_actionability": projected.projected_line_machine.get(
            "actionability"
        ),
    }


def _build_followup_lifecycle_core_fields(
    bundle: _FollowupAssemblyBundle,
) -> dict[str, Any]:
    projected = bundle.projected
    return {
        **_build_followup_lifecycle_identity_fields(projected),
        **_build_followup_lifecycle_controller_fields(projected),
        **_build_followup_lifecycle_phase_fields(projected),
        **_build_followup_lifecycle_result_fields(projected),
    }


def _build_followup_lifecycle_projection_fields(
    *,
    prefix: str,
    projection: dict[str, Any],
    scalar_fields: tuple[tuple[str, str], ...],
    int_fields: tuple[tuple[str, str], ...] = (),
) -> dict[str, Any]:
    fields = {
        f"{prefix}_{field_name}": projection.get(source_key)
        for field_name, source_key in scalar_fields
    }
    fields.update(
        {
            f"{prefix}_{field_name}": int(projection.get(source_key) or 0)
            for field_name, source_key in int_fields
        }
    )
    return fields


def _build_followup_lifecycle_identity_fields(
    projected: _ProjectedFollowupStateBundle,
) -> dict[str, Any]:
    return {
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_state",
            projection=projected.projected_lifecycle_state,
            scalar_fields=(
                ("key", "state_key"),
                ("mode", "state_mode"),
                ("lifecycle", "lifecycle_mode"),
                ("actionability", "actionability"),
            ),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_transition",
            projection=projected.projected_lifecycle_transition,
            scalar_fields=(
                ("key", "transition_key"),
                ("mode", "transition_mode"),
                ("exit_mode", "lifecycle_exit_mode"),
            ),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_machine",
            projection=projected.projected_lifecycle_machine,
            scalar_fields=(
                ("key", "machine_key"),
                ("mode", "machine_mode"),
                ("lifecycle", "lifecycle_mode"),
                ("actionability", "actionability"),
            ),
        ),
    }


def _build_followup_lifecycle_controller_fields(
    projected: _ProjectedFollowupStateBundle,
) -> dict[str, Any]:
    return _build_followup_lifecycle_projection_fields(
        prefix="proactive_lifecycle_controller",
        projection=projected.lifecycle_controller_projection,
        scalar_fields=(
            ("key", "controller_key"),
            ("state", "lifecycle_state"),
            ("decision", "decision"),
        ),
        int_fields=(("delay_seconds", "additional_delay_seconds"),),
    )


def _build_followup_lifecycle_phase_fields(
    projected: _ProjectedFollowupStateBundle,
) -> dict[str, Any]:
    return {
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_envelope",
            projection=projected.projected_lifecycle_envelope,
            scalar_fields=(
                ("key", "envelope_key"),
                ("state", "lifecycle_state"),
                ("mode", "envelope_mode"),
                ("decision", "decision"),
                ("actionability", "actionability"),
            ),
            int_fields=(("delay_seconds", "additional_delay_seconds"),),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_scheduler",
            projection=projected.projected_lifecycle_scheduler,
            scalar_fields=(
                ("key", "scheduler_key"),
                ("state", "lifecycle_state"),
                ("mode", "scheduler_mode"),
                ("decision", "decision"),
                ("actionability", "actionability"),
                ("queue_status", "queue_status_hint"),
            ),
            int_fields=(("delay_seconds", "additional_delay_seconds"),),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_window",
            projection=projected.projected_lifecycle_window,
            scalar_fields=(
                ("key", "window_key"),
                ("state", "lifecycle_state"),
                ("mode", "window_mode"),
                ("decision", "decision"),
                ("queue_status", "queue_status"),
            ),
            int_fields=(("delay_seconds", "additional_delay_seconds"),),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_queue",
            projection=projected.projected_lifecycle_queue,
            scalar_fields=(
                ("key", "queue_key"),
                ("state", "lifecycle_state"),
                ("mode", "queue_mode"),
                ("decision", "decision"),
                ("queue_status", "queue_status"),
            ),
            int_fields=(("delay_seconds", "additional_delay_seconds"),),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_dispatch",
            projection=projected.projected_lifecycle_dispatch,
            scalar_fields=(
                ("key", "dispatch_key"),
                ("state", "lifecycle_state"),
                ("mode", "dispatch_mode"),
                ("decision", "decision"),
                ("actionability", "actionability"),
            ),
            int_fields=(("delay_seconds", "additional_delay_seconds"),),
        ),
    }


def _build_followup_lifecycle_result_fields(
    projected: _ProjectedFollowupStateBundle,
) -> dict[str, Any]:
    return {
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_outcome",
            projection=projected.projected_lifecycle_outcome,
            scalar_fields=(
                ("key", "outcome_key"),
                ("status", "status"),
                ("mode", "outcome_mode"),
                ("decision", "decision"),
                ("actionability", "actionability"),
            ),
            int_fields=(("message_event_count", "message_event_count"),),
        ),
        **_build_followup_lifecycle_projection_fields(
            prefix="proactive_lifecycle_resolution",
            projection=projected.projected_lifecycle_resolution,
            scalar_fields=(
                ("key", "resolution_key"),
                ("status", "status"),
                ("mode", "resolution_mode"),
                ("decision", "decision"),
                ("actionability", "actionability"),
                ("queue_override_status", "queue_override_status"),
            ),
            int_fields=(("remaining_stage_count", "remaining_stage_count"),),
        ),
    }


def _build_followup_schedule_and_timing_fields(
    bundle: _FollowupAssemblyBundle,
) -> dict[str, Any]:
    context = bundle.context
    stage_resolution = bundle.stage_resolution
    queue = bundle.queue
    projected = bundle.projected
    return {
        **_build_followup_scheduling_fields(
            context=context,
            stage_resolution=stage_resolution,
        ),
        **_build_followup_orchestration_fields(
            context=context,
            stage_resolution=stage_resolution,
        ),
        **_build_followup_progression_and_cadence_fields(
            context=context,
            stage_resolution=stage_resolution,
            queue=queue,
        ),
        **_build_followup_directive_runtime_fields(
            context=context,
            projected=projected,
        ),
        **_build_followup_timestamp_fields(context=context),
    }


def _build_followup_scheduling_fields(
    *,
    context: _FollowupContext,
    stage_resolution: _StageResolution,
) -> dict[str, Any]:
    return {
        "proactive_scheduling_status": context.proactive_scheduling_plan.get("status"),
        "proactive_scheduling_mode": context.proactive_scheduling_plan.get("scheduler_mode"),
        "proactive_scheduling_min_seconds_since_last_outbound": int(
            context.proactive_scheduling_plan.get("min_seconds_since_last_outbound") or 0
        ),
        "proactive_scheduling_first_touch_extra_delay_seconds": int(
            context.proactive_scheduling_plan.get("first_touch_extra_delay_seconds") or 0
        ),
        "proactive_scheduling_stage_spacing_mode": context.proactive_scheduling_plan.get(
            "stage_spacing_mode"
        ),
        "proactive_scheduling_low_pressure_guard": context.proactive_scheduling_plan.get(
            "low_pressure_guard"
        ),
        "proactive_guardrail_key": context.proactive_guardrail_plan.get("guardrail_key"),
        "proactive_guardrail_max_dispatch_count": context.max_dispatch_count,
        "proactive_guardrail_stage_min_seconds_since_last_user": int(
            (stage_resolution.current_stage_guardrail or {}).get("min_seconds_since_last_user") or 0
        ),
        "proactive_guardrail_stage_min_seconds_since_last_dispatch": int(
            (stage_resolution.current_stage_guardrail or {}).get("min_seconds_since_last_dispatch")
            or 0
        ),
        "proactive_guardrail_stage_on_guardrail_hit": (
            (stage_resolution.current_stage_guardrail or {}).get("on_guardrail_hit")
        ),
        "proactive_guardrail_hard_stop_conditions": list(
            context.proactive_guardrail_plan.get("hard_stop_conditions") or []
        ),
    }


def _build_followup_orchestration_fields(
    *,
    context: _FollowupContext,
    stage_resolution: _StageResolution,
) -> dict[str, Any]:
    return {
        "proactive_orchestration_key": context.proactive_orchestration_plan.get(
            "orchestration_key"
        ),
        "proactive_orchestration_stage_objective": (
            (stage_resolution.current_stage_directive or {}).get("objective")
        ),
        "proactive_orchestration_stage_delivery_mode": (
            (stage_resolution.current_stage_directive or {}).get("delivery_mode")
        ),
        "proactive_orchestration_stage_question_mode": (
            (stage_resolution.current_stage_directive or {}).get("question_mode")
        ),
        "proactive_orchestration_stage_autonomy_mode": (
            (stage_resolution.current_stage_directive or {}).get("autonomy_mode")
        ),
        "proactive_orchestration_stage_closing_style": (
            (stage_resolution.current_stage_directive or {}).get("closing_style")
        ),
        "proactive_actuation_key": context.proactive_actuation_plan.get("actuation_key"),
        "proactive_actuation_opening_move": (
            (stage_resolution.current_stage_actuation or {}).get("opening_move")
        ),
        "proactive_actuation_bridge_move": (
            (stage_resolution.current_stage_actuation or {}).get("bridge_move")
        ),
        "proactive_actuation_closing_move": (
            (stage_resolution.current_stage_actuation or {}).get("closing_move")
        ),
        "proactive_actuation_continuity_anchor": (
            (stage_resolution.current_stage_actuation or {}).get("continuity_anchor")
        ),
        "proactive_actuation_somatic_mode": (
            (stage_resolution.current_stage_actuation or {}).get("somatic_mode")
        ),
        "proactive_actuation_somatic_body_anchor": (
            (stage_resolution.current_stage_actuation or {}).get("somatic_body_anchor")
        ),
        "proactive_actuation_followup_style": (
            (stage_resolution.current_stage_actuation or {}).get("followup_style")
        ),
        "proactive_actuation_user_space_signal": (
            (stage_resolution.current_stage_actuation or {}).get("user_space_signal")
        ),
    }


def _build_followup_progression_and_cadence_fields(
    *,
    context: _FollowupContext,
    stage_resolution: _StageResolution,
    queue: _ResolvedFollowupQueueBundle,
) -> dict[str, Any]:
    return {
        "proactive_progression_key": context.proactive_progression_plan.get("progression_key"),
        "proactive_progression_close_loop_stage": context.close_loop_stage,
        "proactive_progression_stage_action": (
            (stage_resolution.current_stage_progression or {}).get("on_expired")
        ),
        "proactive_progression_max_overdue_seconds": int(
            (stage_resolution.current_stage_progression or {}).get("max_overdue_seconds") or 0
        ),
        "proactive_progression_advanced": stage_resolution.progression_advanced,
        "proactive_progression_reason": stage_resolution.progression_reason,
        "trigger_after_seconds": int(context.directive.get("trigger_after_seconds") or 0),
        "window_seconds": int(context.directive.get("window_seconds") or 0),
        "proactive_cadence_key": context.proactive_cadence_plan.get("cadence_key"),
        "proactive_cadence_status": context.proactive_cadence_plan.get("status"),
        "proactive_cadence_stage_index": stage_resolution.current_stage_index,
        "proactive_cadence_stage_label": stage_resolution.current_stage_label,
        "proactive_cadence_stage_count": context.max_dispatch_count,
        "proactive_cadence_remaining_dispatches": max(
            0,
            context.max_dispatch_count - (stage_resolution.current_stage_index - 1),
        ),
        "proactive_cadence_next_interval_seconds": (
            context.stage_intervals_seconds[
                min(
                    stage_resolution.current_stage_index - 1,
                    len(context.stage_intervals_seconds) - 1,
                )
            ]
            if context.stage_intervals_seconds
            else 0
        ),
        "proactive_cadence_dispatched_stage_count": context.dispatched_stage_count,
        "due_at": queue.due_at.isoformat() if queue.due_at is not None else None,
        "base_due_at": (queue.base_due_at.isoformat() if queue.base_due_at is not None else None),
        "expires_at": (queue.expires_at.isoformat() if queue.expires_at is not None else None),
        "seconds_until_due": queue.seconds_until_due,
        "seconds_overdue": queue.seconds_overdue,
        "window_remaining_seconds": queue.window_remaining_seconds,
        "schedule_reason": queue.schedule_reason,
        "scheduling_deferred_until": (
            queue.scheduling_deferred_until.isoformat()
            if queue.scheduling_deferred_until is not None
            else None
        ),
    }


def _build_followup_directive_runtime_fields(
    *,
    context: _FollowupContext,
    projected: _ProjectedFollowupStateBundle,
) -> dict[str, Any]:
    return {
        "opening_hint": context.directive.get("opening_hint"),
        "rationale": context.directive.get("rationale"),
        "trigger_conditions": list(context.directive.get("trigger_conditions") or []),
        "hold_reasons": list(context.directive.get("hold_reasons") or []),
        "scheduling_notes": list(context.proactive_scheduling_plan.get("scheduling_notes") or []),
        "time_awareness_mode": projected.runtime_coordination_snapshot.get("time_awareness_mode"),
        "cognitive_load_band": projected.runtime_coordination_snapshot.get("cognitive_load_band"),
        "proactive_style": projected.runtime_coordination_snapshot.get("proactive_style"),
        "somatic_cue": projected.runtime_coordination_snapshot.get("somatic_cue"),
        "turn_count": int(context.state.get("turn_count") or 0),
    }


def _build_followup_timestamp_fields(
    *,
    context: _FollowupContext,
) -> dict[str, Any]:
    return {
        "started_at": (
            context.latest_session_event.occurred_at.isoformat()
            if context.latest_session_event is not None
            else context.session.get("created_at")
        ),
        "last_user_message_at": (
            context.latest_user_event.occurred_at.isoformat()
            if context.latest_user_event is not None
            else None
        ),
        "last_assistant_message_at": (
            context.latest_assistant_event.occurred_at.isoformat()
            if context.latest_assistant_event is not None
            else None
        ),
        "directive_updated_at": context.directive_time.isoformat(),
        "scheduling_updated_at": (
            context.latest_proactive_scheduling_event.occurred_at.isoformat()
            if context.latest_proactive_scheduling_event is not None
            else None
        ),
        "orchestration_updated_at": (
            context.latest_proactive_orchestration_event.occurred_at.isoformat()
            if context.latest_proactive_orchestration_event is not None
            else None
        ),
        "actuation_updated_at": (
            context.latest_proactive_actuation_event.occurred_at.isoformat()
            if context.latest_proactive_actuation_event is not None
            else None
        ),
        "progression_updated_at": (
            context.latest_proactive_progression_event.occurred_at.isoformat()
            if context.latest_proactive_progression_event is not None
            else None
        ),
        "dispatch_gate_updated_at": (
            context.latest_proactive_dispatch_gate_event.occurred_at.isoformat()
            if context.latest_proactive_dispatch_gate_event is not None
            else None
        ),
        "dispatch_feedback_updated_at": (
            context.latest_proactive_dispatch_feedback_event.occurred_at.isoformat()
            if context.latest_proactive_dispatch_feedback_event is not None
            else None
        ),
        "stage_controller_updated_at": (
            context.latest_proactive_stage_controller_event.occurred_at.isoformat()
            if context.latest_proactive_stage_controller_event is not None
            else None
        ),
        "line_controller_updated_at": (
            context.latest_proactive_line_controller_event.occurred_at.isoformat()
            if context.latest_proactive_line_controller_event is not None
            else None
        ),
        "last_event_at": (context.events[-1].occurred_at.isoformat() if context.events else None),
    }


def _build_followup_generic_lifecycle_fields(
    projected: _ProjectedFollowupStateBundle,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for phase in _GENERIC_LIFECYCLE_PHASES:
        phase_projection = projected.projections[f"proactive_lifecycle_{phase}_decision"]
        fields[f"proactive_lifecycle_{phase}_key"] = phase_projection.get(f"{phase}_key")
        fields[f"proactive_lifecycle_{phase}_status"] = phase_projection.get("status")
        fields[f"proactive_lifecycle_{phase}_mode"] = phase_projection.get(f"{phase}_mode")
        fields[f"proactive_lifecycle_{phase}_decision"] = phase_projection.get("decision")
        fields[f"proactive_lifecycle_{phase}_actionability"] = phase_projection.get("actionability")
        fields[f"proactive_lifecycle_{phase}_active_stage_label"] = phase_projection.get(
            "active_stage_label"
        )
        fields[f"proactive_lifecycle_{phase}_queue_override_status"] = phase_projection.get(
            "queue_override_status"
        )
        fields[f"proactive_lifecycle_{phase}_remaining_stage_count"] = int(
            phase_projection.get("remaining_stage_count") or 0
        )
    return fields


def _latest_event(
    events: list[StoredEvent],
    *,
    event_type: str,
) -> StoredEvent | None:
    return next(
        (event for event in reversed(events) if event.event_type == event_type),
        None,
    )


def sort_key(item: dict[str, Any]) -> tuple[object, ...]:
    """Sort key for followup items — used by the service layer."""
    queue_status = str(item.get("queue_status") or "hold")
    due_at = _parse_datetime(item.get("due_at"))
    last_event_at = _parse_datetime(item.get("last_event_at"))
    return (
        _QUEUE_PRIORITY.get(queue_status, 99),
        due_at.timestamp() if due_at is not None else float("inf"),
        -int(item.get("turn_count") or 0),
        -(last_event_at.timestamp() if last_event_at is not None else 0.0),
        str(item.get("session_id") or ""),
    )


def _stage_entry(
    items: object,
    stage_label: str,
) -> dict[str, Any] | None:
    for item in list(items or []):
        candidate = dict(item)
        if str(candidate.get("stage_label") or "") == stage_label:
            return candidate
    return None


def _selected_matrix_candidate(
    reengagement_matrix_assessment: dict[str, Any],
) -> dict[str, Any]:
    selected_strategy_key = str(reengagement_matrix_assessment.get("selected_strategy_key") or "")
    for item in list(reengagement_matrix_assessment.get("candidates") or []):
        candidate = dict(item)
        if bool(candidate.get("selected")):
            return candidate
        if (
            selected_strategy_key
            and str(candidate.get("strategy_key") or "") == selected_strategy_key
        ):
            return candidate
    return {}


def _compute_stage_schedule(
    *,
    reference_time: datetime,
    directive_time: datetime,
    dispatch_events_for_directive: list[StoredEvent],
    latest_assistant_event: StoredEvent | None,
    proactive_scheduling_plan: dict[str, Any],
    trigger_after_seconds: int,
    window_seconds: int,
    progression_anchor_at: datetime | None,
) -> tuple[
    datetime | None,
    datetime | None,
    datetime | None,
    int | None,
    int | None,
    int | None,
    str | None,
    datetime | None,
]:
    seconds_until_due: int | None = None
    seconds_overdue: int | None = None
    window_remaining_seconds: int | None = None
    schedule_reason: str | None = None
    scheduling_deferred_until: datetime | None = None

    if progression_anchor_at is not None:
        base_due_at = progression_anchor_at
        due_at = progression_anchor_at
        expires_at = due_at + timedelta(seconds=window_seconds)
        if window_seconds == 0 or reference_time <= expires_at:
            window_remaining_seconds = max(
                0,
                int((expires_at - reference_time).total_seconds()),
            )
            schedule_reason = "progression_advanced"
        else:
            seconds_overdue = max(
                0,
                int((reference_time - expires_at).total_seconds()),
            )
            schedule_reason = "progression_advanced"
        return (
            base_due_at,
            due_at,
            expires_at,
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
            schedule_reason,
            scheduling_deferred_until,
        )

    base_time = (
        dispatch_events_for_directive[-1].occurred_at
        if dispatch_events_for_directive
        else directive_time
    )
    base_due_at = base_time + timedelta(seconds=trigger_after_seconds)
    due_at = base_due_at
    min_seconds_since_last_outbound = max(
        0,
        int(proactive_scheduling_plan.get("min_seconds_since_last_outbound") or 0),
    )
    outbound_reference_time = (
        dispatch_events_for_directive[-1].occurred_at
        if dispatch_events_for_directive
        else (
            latest_assistant_event.occurred_at
            if latest_assistant_event is not None
            else directive_time
        )
    )
    if min_seconds_since_last_outbound > 0:
        scheduling_deferred_until = outbound_reference_time + timedelta(
            seconds=min_seconds_since_last_outbound
        )
        if scheduling_deferred_until > due_at:
            due_at = scheduling_deferred_until
            schedule_reason = "respect_outbound_cooldown"
    expires_at = due_at + timedelta(seconds=window_seconds)
    return (
        base_due_at,
        due_at,
        expires_at,
        seconds_until_due,
        seconds_overdue,
        window_remaining_seconds,
        schedule_reason,
        scheduling_deferred_until,
    )


def _apply_matrix_learning_spacing(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    reengagement_matrix_assessment: dict[str, Any],
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or current_stage_label == "first_touch":
        return due_at, expires_at, schedule_reason
    if "progression_advanced" in str(schedule_reason or ""):
        return due_at, expires_at, schedule_reason

    learning_mode = str(reengagement_matrix_assessment.get("learning_mode") or "cold_start")
    if learning_mode == "contextual_reinforcement":
        return due_at, expires_at, schedule_reason

    selected_candidate = _selected_matrix_candidate(reengagement_matrix_assessment)
    contextual_supporting_session_count = max(
        0,
        int(selected_candidate.get("contextual_supporting_session_count") or 0),
    )
    if contextual_supporting_session_count > 0:
        return due_at, expires_at, schedule_reason

    supporting_session_count = max(
        0,
        int(selected_candidate.get("supporting_session_count") or 0),
    )
    buffer_seconds = 0
    if supporting_session_count <= 0:
        buffer_seconds = 1800 if current_stage_label == "second_touch" else 3600
    elif supporting_session_count == 1:
        buffer_seconds = 900 if current_stage_label == "second_touch" else 1800
    elif learning_mode == "safe_exploration":
        buffer_seconds = 600 if current_stage_label == "second_touch" else 1200

    if buffer_seconds <= 0:
        return due_at, expires_at, schedule_reason

    adjusted_due_at = due_at + timedelta(seconds=buffer_seconds)
    adjusted_expires_at = adjusted_due_at + timedelta(seconds=window_seconds)
    adjusted_reason = (
        f"{schedule_reason} | matrix_learning_buffered"
        if schedule_reason
        else "matrix_learning_buffered"
    )
    return adjusted_due_at, adjusted_expires_at, adjusted_reason


def _apply_stage_guardrail(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    latest_user_event: StoredEvent | None,
    dispatch_events_for_directive: list[StoredEvent],
    current_stage_guardrail: dict[str, Any] | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or not current_stage_guardrail:
        return due_at, expires_at, schedule_reason

    guardrail_due_at = due_at
    reasons: list[str] = []
    min_seconds_since_last_user = max(
        0,
        int(current_stage_guardrail.get("min_seconds_since_last_user") or 0),
    )
    if latest_user_event is not None and min_seconds_since_last_user > 0:
        user_ready_at = latest_user_event.occurred_at + timedelta(
            seconds=min_seconds_since_last_user
        )
        if user_ready_at > guardrail_due_at:
            guardrail_due_at = user_ready_at
            reasons.append("user_space")

    min_seconds_since_last_dispatch = max(
        0,
        int(current_stage_guardrail.get("min_seconds_since_last_dispatch") or 0),
    )
    if dispatch_events_for_directive and min_seconds_since_last_dispatch > 0:
        dispatch_ready_at = dispatch_events_for_directive[-1].occurred_at + timedelta(
            seconds=min_seconds_since_last_dispatch
        )
        if dispatch_ready_at > guardrail_due_at:
            guardrail_due_at = dispatch_ready_at
            reasons.append("dispatch_spacing")

    if guardrail_due_at <= due_at:
        return due_at, expires_at, schedule_reason

    delay_extension = guardrail_due_at - due_at
    adjusted_expires_at = expires_at + delay_extension if expires_at is not None else None
    guardrail_reason = f"guardrail:{'+'.join(reasons) or 'defer'}"
    adjusted_reason = (
        f"{schedule_reason}|{guardrail_reason}" if schedule_reason else guardrail_reason
    )
    return guardrail_due_at, adjusted_expires_at, adjusted_reason


def _apply_dispatch_gate(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    dispatch_events_for_directive: list[StoredEvent],
    latest_dispatch_gate_event: StoredEvent | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or latest_dispatch_gate_event is None:
        return due_at, expires_at, schedule_reason

    if (
        dispatch_events_for_directive
        and latest_dispatch_gate_event.occurred_at <= dispatch_events_for_directive[-1].occurred_at
    ):
        return due_at, expires_at, schedule_reason

    payload = dict(latest_dispatch_gate_event.payload)
    if str(payload.get("stage_label") or "") != current_stage_label:
        return due_at, expires_at, schedule_reason
    if str(payload.get("decision") or "dispatch") != "defer":
        return due_at, expires_at, schedule_reason

    retry_after_seconds = max(0, int(payload.get("retry_after_seconds") or 0))
    if retry_after_seconds <= 0:
        return due_at, expires_at, schedule_reason

    gate_anchor_at = max(latest_dispatch_gate_event.occurred_at, due_at)
    gate_due_at = gate_anchor_at + timedelta(seconds=retry_after_seconds)
    adjusted_expires_at = gate_due_at + timedelta(seconds=window_seconds)
    gate_reason = f"dispatch_gate:{payload.get('gate_key') or 'defer'}"
    adjusted_reason = f"{schedule_reason}|{gate_reason}" if schedule_reason else gate_reason
    return gate_due_at, adjusted_expires_at, adjusted_reason


def _apply_stage_controller(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    latest_stage_controller_event: StoredEvent | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or latest_stage_controller_event is None:
        return due_at, expires_at, schedule_reason

    payload = dict(latest_stage_controller_event.payload)
    if str(payload.get("status") or "") not in {"active", "terminal"}:
        return due_at, expires_at, schedule_reason
    if str(payload.get("target_stage_label") or "") != current_stage_label:
        return due_at, expires_at, schedule_reason
    if str(payload.get("decision") or "") != "slow_next_stage":
        return due_at, expires_at, schedule_reason

    additional_delay_seconds = max(
        0,
        int(payload.get("additional_delay_seconds") or 0),
    )
    if additional_delay_seconds <= 0:
        return due_at, expires_at, schedule_reason

    adjusted_due_at = due_at + timedelta(seconds=additional_delay_seconds)
    adjusted_expires_at = adjusted_due_at + timedelta(seconds=window_seconds)
    controller_reason = f"controller:{payload.get('controller_key') or 'slow_next_stage'}"
    reasons = [reason for reason in [schedule_reason, controller_reason] if reason]
    return adjusted_due_at, adjusted_expires_at, " | ".join(reasons) or None


def _apply_line_controller(
    *,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
    current_stage_label: str,
    latest_line_controller_event: StoredEvent | None,
) -> tuple[datetime | None, datetime | None, str | None]:
    if due_at is None or latest_line_controller_event is None:
        return due_at, expires_at, schedule_reason

    if current_stage_label == "final_soft_close" and "progression_advanced" in str(
        schedule_reason or ""
    ):
        return due_at, expires_at, schedule_reason

    payload = dict(latest_line_controller_event.payload)
    if str(payload.get("status") or "") not in {"active", "terminal"}:
        return due_at, expires_at, schedule_reason
    if current_stage_label not in list(payload.get("affected_stage_labels") or []):
        return due_at, expires_at, schedule_reason
    if str(payload.get("decision") or "") not in {
        "soften_remaining_line",
        "retire_after_close_loop",
    }:
        return due_at, expires_at, schedule_reason

    additional_delay_seconds = max(
        0,
        int(payload.get("additional_delay_seconds") or 0),
    )
    if additional_delay_seconds <= 0:
        return due_at, expires_at, schedule_reason

    adjusted_due_at = due_at + timedelta(seconds=additional_delay_seconds)
    adjusted_expires_at = adjusted_due_at + timedelta(seconds=window_seconds)
    controller_reason = (
        f"line_controller:{payload.get('controller_key') or 'soften_remaining_line'}"
    )
    reasons = [reason for reason in [schedule_reason, controller_reason] if reason]
    return adjusted_due_at, adjusted_expires_at, " | ".join(reasons) or None


def _resolve_queue_status(
    *,
    reference_time: datetime,
    base_due_at: datetime | None,
    due_at: datetime | None,
    expires_at: datetime | None,
    schedule_reason: str | None,
    window_seconds: int,
) -> tuple[str, int | None, int | None, int | None]:
    seconds_until_due: int | None = None
    seconds_overdue: int | None = None
    window_remaining_seconds: int | None = None

    if base_due_at is not None and reference_time < base_due_at:
        seconds_until_due = max(
            0,
            int((base_due_at - reference_time).total_seconds()),
        )
        window_remaining_seconds = window_seconds
        return ("waiting", seconds_until_due, seconds_overdue, window_remaining_seconds)

    if (
        base_due_at is not None
        and due_at is not None
        and base_due_at < due_at
        and reference_time < due_at
    ):
        seconds_until_due = max(
            0,
            int((due_at - reference_time).total_seconds()),
        )
        window_remaining_seconds = window_seconds
        return (
            "scheduled",
            seconds_until_due,
            seconds_overdue,
            window_remaining_seconds,
        )

    if window_seconds == 0 or (expires_at is not None and reference_time <= expires_at):
        window_remaining_seconds = (
            max(
                0,
                int((expires_at - reference_time).total_seconds()),
            )
            if expires_at is not None
            else window_seconds
        )
        return ("due", seconds_until_due, seconds_overdue, window_remaining_seconds)

    if expires_at is None:
        return ("hold", seconds_until_due, seconds_overdue, window_remaining_seconds)

    seconds_overdue = max(
        0,
        int((reference_time - expires_at).total_seconds()),
    )
    return ("overdue", seconds_until_due, seconds_overdue, window_remaining_seconds)
