from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from relationship_os.application.analyzers.proactive.lifecycle_phase_specs import (
    LIFECYCLE_PHASE_SPECS,
    LifecyclePhaseSpec,
)
from relationship_os.domain.event_types import (
    PROACTIVE_LIFECYCLE_EVENT_PREFIX,
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
)
from relationship_os.domain.events import StoredEvent

LEGACY_LIFECYCLE_STREAM_ERROR = "legacy_lifecycle_stream_unsupported"
LEGACY_LIFECYCLE_STREAM_DETAIL = (
    "session contains legacy proactive lifecycle events; snapshot migration required"
)


class LegacyLifecycleStreamUnsupportedError(RuntimeError):
    def __init__(self, *, stream_id: str) -> None:
        super().__init__(LEGACY_LIFECYCLE_STREAM_DETAIL)
        self.stream_id = stream_id

    def response_detail(self) -> dict[str, str]:
        return {
            "error": LEGACY_LIFECYCLE_STREAM_ERROR,
            "detail": LEGACY_LIFECYCLE_STREAM_DETAIL,
        }


def is_legacy_lifecycle_event_type(event_type: str) -> bool:
    return (
        event_type.startswith(PROACTIVE_LIFECYCLE_EVENT_PREFIX)
        and event_type != PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED
    )


def has_legacy_lifecycle_events(events: list[StoredEvent]) -> bool:
    return any(is_legacy_lifecycle_event_type(event.event_type) for event in events)


def ensure_snapshot_only_lifecycle_events(events: list[StoredEvent]) -> None:
    if not events:
        return
    if has_legacy_lifecycle_events(events):
        raise LegacyLifecycleStreamUnsupportedError(stream_id=events[0].stream_id)


def iter_snapshot_phase_records(
    snapshot_payload: dict[str, Any],
) -> Iterator[tuple[LifecyclePhaseSpec, dict[str, Any]]]:
    phase_map = {
        str(record.get("phase") or ""): dict(record)
        for record in list(snapshot_payload.get("phases") or [])
        if isinstance(record, dict)
    }
    for spec in LIFECYCLE_PHASE_SPECS:
        record = phase_map.get(spec.phase)
        if record is not None:
            yield spec, record


def build_snapshot_phase_payload(
    spec: LifecyclePhaseSpec,
    record: dict[str, Any],
) -> dict[str, Any]:
    attrs = dict(record.get("attrs") or {})
    payload = dict(attrs)
    payload["status"] = record.get("status")
    if spec.key_field:
        payload[spec.key_field] = record.get("key")
    if spec.mode_field:
        payload[spec.mode_field] = record.get("mode")
    payload["decision"] = record.get("decision")
    payload["actionability"] = record.get("actionability")
    payload["changed"] = bool(record.get("changed", False))
    if spec.notes_field:
        payload[spec.notes_field] = list(record.get("notes") or [])
    payload["active_sources"] = [str(item) for item in list(record.get("active_sources") or [])]
    payload["rationale"] = str(record.get("rationale") or "")
    return payload


def iter_snapshot_phase_payloads(
    snapshot_payload: dict[str, Any],
) -> Iterator[tuple[LifecyclePhaseSpec, dict[str, Any]]]:
    for spec, record in iter_snapshot_phase_records(snapshot_payload):
        yield spec, build_snapshot_phase_payload(spec, record)


def snapshot_phase_payload_map(
    snapshot_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        spec.state_field: payload
        for spec, payload in iter_snapshot_phase_payloads(snapshot_payload)
    }


def apply_snapshot_to_turn_record(
    turn_record: Any,
    snapshot_payload: dict[str, Any],
) -> None:
    for spec, payload in iter_snapshot_phase_payloads(snapshot_payload):
        setattr(turn_record, spec.state_field, dict(payload))


def apply_snapshot_to_runtime_state(
    state: dict[str, Any],
    snapshot_payload: dict[str, Any],
) -> dict[str, Any]:
    next_state = {
        **state,
        "proactive_lifecycle_snapshot": dict(snapshot_payload),
        "proactive_lifecycle_snapshot_count": int(
            state.get("proactive_lifecycle_snapshot_count", 0)
        )
        + 1,
    }
    for spec, payload in iter_snapshot_phase_payloads(snapshot_payload):
        next_state[spec.state_field] = dict(payload)
        next_state[spec.count_field] = int(next_state.get(spec.count_field, 0)) + 1
    return next_state
