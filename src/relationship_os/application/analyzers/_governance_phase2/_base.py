"""Phase 2 governance – constants, dataclasses, and helpers."""

from __future__ import annotations

from dataclasses import dataclass

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    KnowledgeBoundaryDecision,
    PolicyGateDecision,
    RelationshipState,
    RepairAssessment,
    ResponsePostAudit,
    ResponseSequencePlan,
    RuntimeQualityDoctorReport,
)

_SYSTEM3_GOVERNANCE_DOMAIN_ORDER = (
    "dependency",
    "autonomy",
    "boundary",
    "support",
    "continuity",
    "repair",
    "attunement",
    "trust",
    "clarity",
    "pacing",
    "commitment",
    "disclosure",
    "reciprocity",
    "pressure",
    "relational",
    "safety",
    "progress",
    "stability",
)


def _phase2_policy() -> dict[str, object]:
    # Look up get_default_compiled_policy_set through the package so that
    # monkeypatching phase2_module.get_default_compiled_policy_set is respected.
    from relationship_os.application.analyzers import _governance_phase2 as _pkg  # noqa: PLC0415

    compiled = _pkg.get_default_compiled_policy_set()
    if compiled is None:
        return {}
    governance = dict(compiled.conscience_policy.get("governance") or {})
    return dict(governance.get("phase2") or {})


def _phase2_section(key: str) -> dict[str, object]:
    raw = _phase2_policy().get(key) or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _phase2_governance_line(name: str) -> dict[str, object]:
    lines = dict(_phase2_section("governance_lines") or {})
    raw = lines.get(name) or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _phase2_branch(
    line: str,
    branch_kind: str,
    branch_id: str,
) -> dict[str, str]:
    line_policy = _phase2_governance_line(line)
    branches = dict(line_policy.get(branch_kind) or {})
    branch = branches.get(branch_id) or {}
    if not isinstance(branch, dict):
        return {}
    return {str(key): str(value) for key, value in branch.items()}


@dataclass(slots=True, frozen=True)
class _System3Prelude:
    turn_index: int
    recall_count: int
    filtered_recall_count: int
    relationship_state: RelationshipState
    repair_assessment: RepairAssessment
    knowledge_boundary_decision: KnowledgeBoundaryDecision
    policy_gate: PolicyGateDecision
    response_sequence_plan: ResponseSequencePlan | None
    response_post_audit: ResponsePostAudit | None
    runtime_quality_doctor_report: RuntimeQualityDoctorReport | None
    confidence_assessment: ConfidenceAssessment
    identity_anchor: str
    identity_consistency: str
    identity_confidence: float
    identity_trajectory_status: str
    identity_trajectory_target: str
    identity_trajectory_trigger: str
    identity_trajectory_notes: list[str]
    growth_stage: str
    growth_signal: str
    user_model_confidence: float
    user_needs: list[str]
    user_preferences: list[str]
    emotional_debt_status: str
    emotional_debt_score: float
    debt_signals: list[str]
    emotional_debt_trajectory_status: str
    emotional_debt_trajectory_target: str
    emotional_debt_trajectory_trigger: str
    emotional_debt_trajectory_notes: list[str]
    strategy_audit_status: str
    strategy_fit: str
    strategy_audit_notes: list[str]
    strategy_audit_trajectory_status: str
    strategy_audit_trajectory_target: str
    strategy_audit_trajectory_trigger: str
    strategy_audit_trajectory_notes: list[str]
    strategy_supervision_status: str
    strategy_supervision_mode: str
    strategy_supervision_trigger: str
    strategy_supervision_notes: list[str]
    strategy_supervision_trajectory_status: str
    strategy_supervision_trajectory_target: str
    strategy_supervision_trajectory_trigger: str
    strategy_supervision_trajectory_notes: list[str]
    moral_reasoning_status: str
    moral_posture: str
    moral_conflict: str
    moral_principles: list[str]
    moral_notes: list[str]
    moral_trajectory_status: str
    moral_trajectory_target: str
    moral_trajectory_trigger: str
    moral_trajectory_notes: list[str]
    user_model_evolution_status: str
    user_model_revision_mode: str
    user_model_shift_signal: str
    user_model_evolution_notes: list[str]
    user_model_trajectory_status: str
    user_model_trajectory_target: str
    user_model_trajectory_trigger: str
    user_model_trajectory_notes: list[str]
    expectation_calibration_status: str
    expectation_calibration_target: str
    expectation_calibration_trigger: str
    expectation_calibration_notes: list[str]
    expectation_calibration_trajectory_status: str
    expectation_calibration_trajectory_target: str
    expectation_calibration_trajectory_trigger: str
    expectation_calibration_trajectory_notes: list[str]


@dataclass(slots=True, frozen=True)
class _GovernanceOutcome:
    status: str
    target: str
    trigger: str
    notes: list[str]
    trajectory_status: str
    trajectory_target: str
    trajectory_trigger: str
    trajectory_notes: list[str]


@dataclass(slots=True, frozen=True)
class _GrowthTransitionOutcome:
    status: str
    target: str
    trigger: str
    readiness: float
    notes: list[str]
    trajectory_status: str
    trajectory_target: str
    trajectory_trigger: str
    trajectory_notes: list[str]


@dataclass(slots=True, frozen=True)
class _VersionMigrationOutcome:
    status: str
    scope: str
    trigger: str
    notes: list[str]
    trajectory_status: str
    trajectory_target: str
    trajectory_trigger: str
    trajectory_notes: list[str]


def _governance_kwargs(*, prefix: str, outcome: _GovernanceOutcome) -> dict[str, object]:
    return {
        f"{prefix}_governance_status": outcome.status,
        f"{prefix}_governance_target": outcome.target,
        f"{prefix}_governance_trigger": outcome.trigger,
        f"{prefix}_governance_notes": _compact(outcome.notes, limit=6),
        f"{prefix}_governance_trajectory_status": outcome.trajectory_status,
        f"{prefix}_governance_trajectory_target": outcome.trajectory_target,
        f"{prefix}_governance_trajectory_trigger": outcome.trajectory_trigger,
        f"{prefix}_governance_trajectory_notes": _compact(
            outcome.trajectory_notes,
            limit=6,
        ),
    }
