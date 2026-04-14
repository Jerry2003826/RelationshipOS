from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LifecyclePhaseSpec:
    phase: str
    order: int
    event_type: str
    state_field: str
    count_field: str
    key_field: str | None
    mode_field: str | None
    notes_field: str | None


LIFECYCLE_PHASE_ORDER = (
    "state",
    "transition",
    "machine",
    "controller",
    "envelope",
    "scheduler",
    "window",
    "queue",
    "dispatch",
    "outcome",
    "resolution",
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

POST_DISPATCH_PHASE_ORDER = (
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


def lifecycle_event_type(phase: str) -> str:
    return f"system.proactive_lifecycle_{phase}.updated"


def lifecycle_state_field(phase: str) -> str:
    return f"proactive_lifecycle_{phase}_decision"


def lifecycle_count_field(phase: str) -> str:
    return f"{lifecycle_state_field(phase)}_count"


def lifecycle_key_field(phase: str) -> str:
    return f"{phase}_key"


def lifecycle_mode_field(phase: str) -> str | None:
    if phase == "controller":
        return None
    return f"{phase}_mode"


def lifecycle_notes_field(phase: str) -> str:
    return f"{phase}_notes"


LIFECYCLE_PHASE_SPECS = tuple(
    LifecyclePhaseSpec(
        phase=phase,
        order=index,
        event_type=lifecycle_event_type(phase),
        state_field=lifecycle_state_field(phase),
        count_field=lifecycle_count_field(phase),
        key_field=lifecycle_key_field(phase),
        mode_field=lifecycle_mode_field(phase),
        notes_field=lifecycle_notes_field(phase),
    )
    for index, phase in enumerate(LIFECYCLE_PHASE_ORDER, start=1)
)

LIFECYCLE_PHASE_SPEC_BY_PHASE = {
    spec.phase: spec for spec in LIFECYCLE_PHASE_SPECS
}
LIFECYCLE_PHASE_SPEC_BY_EVENT_TYPE = {
    spec.event_type: spec for spec in LIFECYCLE_PHASE_SPECS
}
LIFECYCLE_LEGACY_EVENT_TYPES = frozenset(
    spec.event_type for spec in LIFECYCLE_PHASE_SPECS
)
