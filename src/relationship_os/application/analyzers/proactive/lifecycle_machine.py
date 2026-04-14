from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any
from uuid import uuid4

import relationship_os.domain.contracts.lifecycle as lifecycle_contracts
from relationship_os.application.analyzers._utils import _compact
from relationship_os.application.analyzers.proactive.lifecycle import (
    build_proactive_lifecycle_outcome_decision,
    build_proactive_lifecycle_resolution_decision,
)
from relationship_os.application.analyzers.proactive.lifecycle_phase_specs import (
    LIFECYCLE_PHASE_ORDER,
    LIFECYCLE_PHASE_SPEC_BY_PHASE,
    POST_DISPATCH_PHASE_ORDER,
)

DecisionPayload = dict[str, Any]


@dataclass(frozen=True, slots=True)
class _PostDispatchCaseSpec:
    mode: str
    decision: str
    actionability: str
    queue_override_status: str | None


@dataclass(frozen=True, slots=True)
class _PostDispatchPhaseSpec:
    phase: str
    previous_phase: str
    active: _PostDispatchCaseSpec
    buffer: _PostDispatchCaseSpec
    pause: _PostDispatchCaseSpec
    close: _PostDispatchCaseSpec
    retire: _PostDispatchCaseSpec
    mode_note_from_previous: bool = False


_ACTIVE_CASE_ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("activation", "active_lifecycle_activation", "activate_next_lifecycle_stage", "activate"),
    ("settlement", "active_lifecycle_settlement", "keep_lifecycle_active", "activate"),
    ("closure", "open_lifecycle_closure", "keep_open_lifecycle_closure", "continue"),
    ("availability", "open_lifecycle_availability", "keep_lifecycle_available", "continue"),
    ("retention", "retained_lifecycle_retention", "retain_lifecycle_retention", "continue"),
    ("eligibility", "eligible_lifecycle_eligibility", "keep_lifecycle_eligible", "continue"),
    ("candidate", "candidate_lifecycle_candidate", "keep_lifecycle_candidate", "continue"),
    (
        "selectability",
        "selectable_lifecycle_selectability",
        "keep_lifecycle_selectable",
        "continue",
    ),
    ("reentry", "reenterable_lifecycle_reentry", "keep_lifecycle_reentry", "continue"),
    (
        "reactivation",
        "reactivatable_lifecycle_reactivation",
        "keep_lifecycle_reactivation",
        "continue",
    ),
    ("resumption", "resumable_lifecycle_resumption", "keep_lifecycle_resumption", "continue"),
    ("readiness", "ready_lifecycle_readiness", "keep_lifecycle_readiness", "continue"),
    ("arming", "armed_lifecycle_arming", "keep_lifecycle_arming", "continue"),
    ("trigger", "triggerable_lifecycle_trigger", "keep_lifecycle_trigger", "continue"),
    ("launch", "launchable_lifecycle_launch", "keep_lifecycle_launch", "continue"),
    ("handoff", "handoff_ready_lifecycle_handoff", "keep_lifecycle_handoff", "continue"),
    (
        "continuation",
        "continuable_lifecycle_continuation",
        "keep_lifecycle_continuation",
        "continue",
    ),
    (
        "sustainment",
        "sustainable_lifecycle_sustainment",
        "sustain_lifecycle_sustainment",
        "sustain",
    ),
    (
        "stewardship",
        "stewarded_lifecycle_stewardship",
        "steward_lifecycle_stewardship",
        "steward",
    ),
    ("guardianship", "guarded_lifecycle_guardianship", "guard_lifecycle_guardianship", "guard"),
    ("oversight", "overseen_lifecycle_oversight", "oversee_lifecycle_oversight", "oversee"),
    ("assurance", "assured_lifecycle_assurance", "assure_lifecycle_assurance", "assure"),
    ("attestation", "attested_lifecycle_attestation", "attest_lifecycle_attestation", "attest"),
    ("verification", "verified_lifecycle_verification", "verify_lifecycle_verification", "verify"),
    (
        "certification",
        "certified_lifecycle_certification",
        "certify_lifecycle_certification",
        "certify",
    ),
    (
        "confirmation",
        "confirmed_lifecycle_confirmation",
        "confirm_lifecycle_confirmation",
        "confirm",
    ),
    ("ratification", "ratified_lifecycle_ratification", "ratify_lifecycle_ratification", "ratify"),
    ("endorsement", "endorsed_lifecycle_endorsement", "endorse_lifecycle_endorsement", "endorse"),
    (
        "authorization",
        "authorized_lifecycle_authorization",
        "authorize_lifecycle_authorization",
        "authorize",
    ),
    ("enactment", "enacted_lifecycle_enactment", "enact_lifecycle_enactment", "enact"),
    ("finality", "finalized_lifecycle_finality", "finalize_lifecycle_finality", "finalize"),
    ("completion", "completed_lifecycle_completion", "complete_lifecycle_completion", "complete"),
    ("conclusion", "completed_lifecycle_conclusion", "complete_lifecycle_conclusion", "complete"),
    (
        "disposition",
        "completed_lifecycle_disposition",
        "complete_lifecycle_disposition",
        "complete",
    ),
    ("standing", "standing_lifecycle_standing", "keep_lifecycle_standing", "keep"),
    ("residency", "resident_lifecycle_residency", "keep_lifecycle_residency", "keep"),
    ("tenure", "tenured_lifecycle_tenure", "keep_lifecycle_tenure", "keep"),
    ("persistence", "persistent_lifecycle_persistence", "keep_lifecycle_persistence", "keep"),
    ("durability", "durable_lifecycle_durability", "keep_lifecycle_durability", "keep"),
    ("longevity", "enduring_lifecycle_longevity", "keep_lifecycle_longevity", "keep"),
    ("legacy", "lasting_lifecycle_legacy", "keep_lifecycle_legacy", "keep"),
    ("heritage", "preserved_lifecycle_heritage", "keep_lifecycle_heritage", "keep"),
    ("lineage", "preserved_lifecycle_lineage", "keep_lifecycle_lineage", "keep"),
    ("ancestry", "preserved_lifecycle_ancestry", "keep_lifecycle_ancestry", "keep"),
    ("provenance", "preserved_lifecycle_provenance", "keep_lifecycle_provenance", "keep"),
    ("origin", "preserved_lifecycle_origin", "keep_lifecycle_origin", "keep"),
    ("root", "preserved_lifecycle_root", "keep_lifecycle_root", "keep"),
    ("foundation", "preserved_lifecycle_foundation", "keep_lifecycle_foundation", "keep"),
    ("bedrock", "preserved_lifecycle_bedrock", "keep_lifecycle_bedrock", "keep"),
    ("substrate", "preserved_lifecycle_substrate", "keep_lifecycle_substrate", "keep"),
    ("stratum", "preserved_lifecycle_stratum", "keep_lifecycle_stratum", "keep"),
    ("layer", "preserved_lifecycle_layer", "keep_lifecycle_layer", "keep"),
)

_ACTIVE_CASE_BY_PHASE = {
    phase: _PostDispatchCaseSpec(
        mode=mode,
        decision=decision,
        actionability=actionability,
        queue_override_status=None,
    )
    for phase, mode, decision, actionability in _ACTIVE_CASE_ROWS
}

_MODE_NOTE_PHASES = frozenset(
    {
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
    }
)


def _buffer_case(phase: str) -> _PostDispatchCaseSpec:
    decision = (
        "buffer_current_lifecycle_stage"
        if phase == "activation"
        else f"buffer_lifecycle_{phase}"
    )
    return _PostDispatchCaseSpec(
        mode=f"buffered_lifecycle_{phase}",
        decision=decision,
        actionability="buffer",
        queue_override_status="scheduled",
    )


def _pause_case(phase: str) -> _PostDispatchCaseSpec:
    if phase == "activation":
        return _PostDispatchCaseSpec(
            mode="hold_lifecycle_activation",
            decision="hold_current_lifecycle_stage",
            actionability="hold",
            queue_override_status="hold",
        )
    if phase == "settlement":
        return _PostDispatchCaseSpec(
            mode="hold_lifecycle_settlement",
            decision="hold_lifecycle_settlement",
            actionability="hold",
            queue_override_status="hold",
        )
    return _PostDispatchCaseSpec(
        mode=f"paused_lifecycle_{phase}",
        decision=f"pause_lifecycle_{phase}",
        actionability="pause",
        queue_override_status="hold",
    )


def _close_case(phase: str) -> _PostDispatchCaseSpec:
    if phase == "settlement":
        return _PostDispatchCaseSpec(
            mode="close_loop_lifecycle_settlement",
            decision="close_lifecycle_settlement",
            actionability="close_loop",
            queue_override_status="terminal",
        )
    if phase == "closure":
        return _PostDispatchCaseSpec(
            mode="close_loop_lifecycle_closure",
            decision="close_loop_lifecycle_closure",
            actionability="close_loop",
            queue_override_status="terminal",
        )
    if phase == "availability":
        return _PostDispatchCaseSpec(
            mode="closed_lifecycle_availability",
            decision="close_loop_lifecycle_availability",
            actionability="close_loop",
            queue_override_status="terminal",
        )
    return _PostDispatchCaseSpec(
        mode=f"archived_lifecycle_{phase}",
        decision=f"archive_lifecycle_{phase}",
        actionability="archive",
        queue_override_status="terminal",
    )


def _retire_case(phase: str) -> _PostDispatchCaseSpec:
    if phase == "activation":
        return _PostDispatchCaseSpec(
            mode="terminal_lifecycle_activation",
            decision="retire_lifecycle_line",
            actionability="retire",
            queue_override_status="terminal",
        )
    if phase == "settlement":
        return _PostDispatchCaseSpec(
            mode="terminal_lifecycle_settlement",
            decision="retire_lifecycle_settlement",
            actionability="retire",
            queue_override_status="terminal",
        )
    if phase == "closure":
        return _PostDispatchCaseSpec(
            mode="terminal_lifecycle_closure",
            decision="retire_lifecycle_closure",
            actionability="retire",
            queue_override_status="terminal",
        )
    return _PostDispatchCaseSpec(
        mode=f"retired_lifecycle_{phase}",
        decision=f"retire_lifecycle_{phase}",
        actionability="retire",
        queue_override_status="terminal",
    )


_PREVIOUS_PHASE_BY_PHASE: dict[str, str] = {}
_previous_phase = "resolution"
for _phase in POST_DISPATCH_PHASE_ORDER:
    _PREVIOUS_PHASE_BY_PHASE[_phase] = _previous_phase
    _previous_phase = _phase

_POST_DISPATCH_SPECS = {
    phase: _PostDispatchPhaseSpec(
        phase=phase,
        previous_phase=_PREVIOUS_PHASE_BY_PHASE[phase],
        active=_ACTIVE_CASE_BY_PHASE[phase],
        buffer=_buffer_case(phase),
        pause=_pause_case(phase),
        close=_close_case(phase),
        retire=_retire_case(phase),
        mode_note_from_previous=phase in _MODE_NOTE_PHASES,
    )
    for phase in POST_DISPATCH_PHASE_ORDER
}


def build_proactive_lifecycle_post_dispatch_chain(
    *,
    lifecycle_dispatch_decision: Any,
    lifecycle_queue_decision: Any,
    line_state_decision: Any,
    line_transition_decision: Any,
    dispatched: bool,
    message_event_count: int,
) -> dict[str, Any]:
    outcome_decision = build_proactive_lifecycle_outcome_decision(
        lifecycle_dispatch_decision=lifecycle_dispatch_decision,
        dispatched=dispatched,
        message_event_count=message_event_count,
    )
    resolution_decision = build_proactive_lifecycle_resolution_decision(
        lifecycle_outcome_decision=outcome_decision,
        lifecycle_queue_decision=lifecycle_queue_decision,
        line_state_decision=line_state_decision,
        line_transition_decision=line_transition_decision,
    )

    decisions: dict[str, Any] = {
        "outcome": outcome_decision,
        "resolution": resolution_decision,
    }
    previous_phase = "resolution"
    previous_decision = resolution_decision
    for phase in POST_DISPATCH_PHASE_ORDER:
        current_decision = _build_post_dispatch_decision(
            phase=phase,
            previous_phase=previous_phase,
            previous_decision=previous_decision,
        )
        decisions[phase] = current_decision
        previous_phase = phase
        previous_decision = current_decision
    return decisions


def build_proactive_lifecycle_snapshot(
    *,
    decisions: dict[str, Any],
    emission_id: str | None = None,
) -> lifecycle_contracts.LifecycleSnapshot:
    payloads = {
        phase: _decision_payload(decision)
        for phase, decision in decisions.items()
        if phase in LIFECYCLE_PHASE_SPEC_BY_PHASE
    }
    phase_records = [
        _build_phase_record(phase=phase, payload=payloads[phase])
        for phase in LIFECYCLE_PHASE_ORDER
        if phase in payloads
    ]
    top_level = _build_snapshot_top_level(payloads)
    return lifecycle_contracts.LifecycleSnapshot(
        schema_version=2,
        emission_id=emission_id or f"lifecycle-{uuid4().hex}",
        lifecycle_key=str(top_level.get("lifecycle_key") or "snapshot"),
        current_stage_label=_optional_str(top_level.get("current_stage_label")),
        current_stage_index=_optional_int(top_level.get("current_stage_index")),
        stage_count=_optional_int(top_level.get("stage_count")),
        dispatched=bool(top_level.get("dispatched")),
        message_event_count=int(top_level.get("message_event_count") or 0),
        selected_strategy_key=str(
            top_level.get("selected_strategy_key") or "none"
        ),
        selected_pressure_mode=str(
            top_level.get("selected_pressure_mode") or "none"
        ),
        selected_autonomy_signal=str(
            top_level.get("selected_autonomy_signal") or "none"
        ),
        selected_delivery_mode=str(
            top_level.get("selected_delivery_mode") or "none"
        ),
        primary_source=str(top_level.get("primary_source") or "lifecycle"),
        phases=phase_records,
    )


def _decision_payload(decision: Any) -> DecisionPayload:
    if is_dataclass(decision):
        return asdict(decision)
    return dict(decision)


def _build_post_dispatch_decision(
    *,
    phase: str,
    previous_phase: str,
    previous_decision: Any,
) -> Any:
    spec = _POST_DISPATCH_SPECS[phase]
    payload = _decision_payload(previous_decision)
    case_name = _resolve_case_name(phase=phase, payload=payload)
    if phase == "activation" and case_name == "active" and not payload.get(
        "next_stage_label"
    ):
        case_name = "retire"
    case = getattr(spec, case_name)
    current_stage_label = str(payload.get("current_stage_label") or "unknown")
    lifecycle_state = str(payload.get("lifecycle_state") or "active")
    previous_mode_field = f"{previous_phase}_mode"
    previous_mode = str(payload.get(previous_mode_field) or case.mode)
    line_state = str(payload.get("line_state") or "steady")
    line_exit_mode = str(payload.get("line_exit_mode") or "stay")
    additional_delay_seconds = max(
        0,
        int(payload.get("additional_delay_seconds") or 0),
    )
    next_stage_label = _optional_str(payload.get("next_stage_label"))
    active_stage_label = _optional_str(
        payload.get("active_stage_label")
    ) or current_stage_label
    remaining_stage_count = max(
        0,
        int(payload.get("remaining_stage_count") or 0),
    )

    if phase == "activation":
        active_stage_label = current_stage_label
        if case_name == "active" and next_stage_label:
            active_stage_label = next_stage_label
    if case_name in {"close", "retire"}:
        active_stage_label = None
        next_stage_label = None
        remaining_stage_count = 0

    notes = [
        str(item)
        for item in list(payload.get(f"{previous_phase}_notes") or [])
    ]
    if spec.mode_note_from_previous and previous_mode:
        notes.append(f"{previous_phase}:{previous_mode}")
    if line_state:
        notes.append(f"line:{line_state}")
    if line_exit_mode:
        notes.append(f"exit:{line_exit_mode}")
    if phase == "activation":
        if next_stage_label:
            notes.append(f"next:{next_stage_label}")
    elif active_stage_label:
        notes.append(f"active:{active_stage_label}")

    changed = bool(
        payload.get("changed")
        or case.decision != spec.pause.decision
        or active_stage_label != current_stage_label
    )
    decision_class = _decision_class_for_phase(phase)
    return decision_class(
        status=_status_for_case(case_name=case_name),
        **{
            f"{phase}_key": (
                f"{current_stage_label}_{case.decision}_"
                f"{payload.get('selected_strategy_key') or 'none'}"
            ),
            "current_stage_label": current_stage_label,
            "lifecycle_state": lifecycle_state,
            previous_mode_field: previous_mode,
            f"{phase}_mode": case.mode,
            "decision": case.decision,
            "actionability": case.actionability,
            "changed": changed,
            "active_stage_label": active_stage_label,
            "next_stage_label": next_stage_label,
            "queue_override_status": case.queue_override_status,
            "remaining_stage_count": remaining_stage_count,
            "line_state": line_state,
            "line_exit_mode": line_exit_mode,
            "additional_delay_seconds": additional_delay_seconds,
            "selected_strategy_key": str(payload.get("selected_strategy_key") or "none"),
            "selected_pressure_mode": str(payload.get("selected_pressure_mode") or "none"),
            "selected_autonomy_signal": str(payload.get("selected_autonomy_signal") or "none"),
            "selected_delivery_mode": str(payload.get("selected_delivery_mode") or "none"),
            "primary_source": str(payload.get("primary_source") or previous_phase),
            f"{previous_phase}_decision": _optional_str(payload.get("decision")),
            "active_sources": _compact(
                [str(item) for item in list(payload.get("active_sources") or [])],
                limit=8,
            ),
            f"{phase}_notes": _compact(notes, limit=10),
            "rationale": _build_phase_rationale(
                phase=phase,
                previous_phase=previous_phase,
                decision=case.decision,
            ),
        },
    )


def _resolve_case_name(*, phase: str, payload: DecisionPayload) -> str:
    previous_decision = str(payload.get("decision") or "")
    previous_status = str(payload.get("status") or "")
    queue_override_status = str(payload.get("queue_override_status") or "")
    actionability = str(payload.get("actionability") or "")
    line_exit_mode = str(payload.get("line_exit_mode") or "stay")

    if phase == "activation":
        if previous_decision == "continue_lifecycle_resolution":
            return "active"
        if previous_decision == "buffer_lifecycle_resolution":
            return "buffer"
        if previous_decision == "hold_lifecycle_resolution":
            return "pause"
        return "retire"
    if phase == "settlement":
        if previous_decision == "activate_next_lifecycle_stage":
            return "active"
        if previous_decision == "buffer_current_lifecycle_stage":
            return "buffer"
        if previous_decision == "hold_current_lifecycle_stage":
            return "pause"
        if line_exit_mode == "close_loop":
            return "close"
        return "retire"
    if previous_status == "scheduled" or queue_override_status == "scheduled":
        return "buffer"
    if previous_status == "hold" or queue_override_status == "hold":
        return "pause"
    if queue_override_status == "terminal":
        if actionability == "retire":
            return "retire"
        return "close"
    return "active"


def _status_for_case(*, case_name: str) -> str:
    if case_name == "active":
        return "active"
    if case_name == "buffer":
        return "scheduled"
    if case_name == "pause":
        return "hold"
    return "terminal"


def _decision_class_for_phase(phase: str) -> type[Any]:
    class_name = f"ProactiveLifecycle{phase.title().replace('_', '')}Decision"
    return getattr(lifecycle_contracts, class_name)


def _build_phase_rationale(
    *,
    phase: str,
    previous_phase: str,
    decision: str,
) -> str:
    return (
        f"The proactive lifecycle {phase} projects the {previous_phase} posture "
        f"into {decision}."
    )


def _build_phase_record(
    *,
    phase: str,
    payload: DecisionPayload,
) -> lifecycle_contracts.LifecyclePhaseRecord:
    spec = LIFECYCLE_PHASE_SPEC_BY_PHASE[phase]
    notes = list(payload.get(spec.notes_field) or []) if spec.notes_field else []
    key = payload.get(spec.key_field) if spec.key_field else None
    mode = payload.get(spec.mode_field) if spec.mode_field else None
    attrs = {
        key_name: value
        for key_name, value in payload.items()
        if key_name
        not in {
            "status",
            spec.key_field,
            spec.mode_field,
            "decision",
            "actionability",
            "changed",
            spec.notes_field,
            "active_sources",
            "rationale",
        }
    }
    return lifecycle_contracts.LifecyclePhaseRecord(
        phase=phase,
        order=spec.order,
        status=_optional_str(payload.get("status")),
        key=_optional_str(key),
        mode=_optional_str(mode),
        decision=_optional_str(payload.get("decision")),
        actionability=_optional_str(payload.get("actionability")),
        changed=bool(payload.get("changed", False)),
        notes=[str(item) for item in notes],
        active_sources=[
            str(item) for item in list(payload.get("active_sources") or [])
        ],
        rationale=str(payload.get("rationale") or ""),
        attrs=attrs,
    )


def _build_snapshot_top_level(payloads: dict[str, DecisionPayload]) -> dict[str, Any]:
    state_payload = payloads.get("state", {})
    outcome_payload = payloads.get("outcome", {})
    latest_payload = next(reversed(payloads.values()), {})
    return {
        "lifecycle_key": state_payload.get("state_key")
        or payloads.get("dispatch", {}).get("dispatch_key")
        or "snapshot",
        "current_stage_label": state_payload.get("current_stage_label")
        or latest_payload.get("current_stage_label"),
        "current_stage_index": state_payload.get("current_stage_index")
        or payloads.get("transition", {}).get("current_stage_index"),
        "stage_count": state_payload.get("stage_count")
        or payloads.get("transition", {}).get("stage_count"),
        "dispatched": bool(outcome_payload.get("dispatched")),
        "message_event_count": int(outcome_payload.get("message_event_count") or 0),
        "selected_strategy_key": _pick_latest_value(
            payloads,
            "selected_strategy_key",
            default="none",
        ),
        "selected_pressure_mode": _pick_latest_value(
            payloads,
            "selected_pressure_mode",
            default="none",
        ),
        "selected_autonomy_signal": _pick_latest_value(
            payloads,
            "selected_autonomy_signal",
            default="none",
        ),
        "selected_delivery_mode": _pick_latest_value(
            payloads,
            "selected_delivery_mode",
            default="none",
        ),
        "primary_source": _pick_latest_value(
            payloads,
            "primary_source",
            default="lifecycle",
        ),
    }


def _pick_latest_value(
    payloads: dict[str, DecisionPayload],
    key: str,
    *,
    default: Any = None,
) -> Any:
    for payload in reversed(tuple(payloads.values())):
        value = payload.get(key)
        if value not in {None, ""}:
            return value
    return default


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
