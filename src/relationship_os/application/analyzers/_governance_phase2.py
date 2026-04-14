"""Phase 2 governance helper for System 3 snapshot assembly."""

from __future__ import annotations

from dataclasses import dataclass

from relationship_os.application.analyzers._utils import _clamp, _compact
from relationship_os.application.policy_registry import get_default_compiled_policy_set
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    KnowledgeBoundaryDecision,
    PolicyGateDecision,
    RelationshipState,
    RepairAssessment,
    ResponsePostAudit,
    ResponseSequencePlan,
    RuntimeQualityDoctorReport,
    System3Snapshot,
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
    compiled = get_default_compiled_policy_set()
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


def _build_review_focus(
    *,
    prelude: _System3Prelude,
    governance_outcomes: dict[str, _GovernanceOutcome],
    growth_transition: _GrowthTransitionOutcome,
    version_migration: _VersionMigrationOutcome,
) -> list[str]:
    focus_notes: list[str] = []
    for domain in _SYSTEM3_GOVERNANCE_DOMAIN_ORDER:
        outcome = governance_outcomes[domain]
        focus_notes.extend(outcome.notes)
        focus_notes.extend(outcome.trajectory_notes)
    return _compact(
        prelude.debt_signals
        + prelude.emotional_debt_trajectory_notes
        + prelude.identity_trajectory_notes
        + prelude.strategy_audit_notes
        + prelude.strategy_audit_trajectory_notes
        + prelude.strategy_supervision_notes
        + prelude.strategy_supervision_trajectory_notes
        + prelude.moral_notes
        + prelude.moral_trajectory_notes
        + prelude.user_model_evolution_notes
        + prelude.user_model_trajectory_notes
        + prelude.expectation_calibration_notes
        + prelude.expectation_calibration_trajectory_notes
        + focus_notes
        + growth_transition.notes
        + growth_transition.trajectory_notes
        + version_migration.notes
        + version_migration.trajectory_notes
        + prelude.user_needs
        + prelude.user_preferences
        + [prelude.growth_signal],
        limit=6,
    )


def _build_core_governance_outcomes(
    *,
    prelude: _System3Prelude,
) -> dict[str, _GovernanceOutcome]:
    dependency = _build_dependency_governance(prelude=prelude)
    autonomy = _build_autonomy_governance(prelude=prelude)
    boundary = _build_boundary_governance(prelude=prelude)
    support = _build_support_governance(
        prelude=prelude,
        dependency=dependency,
        autonomy=autonomy,
        boundary=boundary,
    )
    continuity = _build_continuity_governance(
        prelude=prelude,
        support=support,
    )
    repair = _build_repair_governance(
        prelude=prelude,
        continuity=continuity,
        support=support,
    )
    attunement = _build_attunement_governance(
        prelude=prelude,
        repair=repair,
        continuity=continuity,
        support=support,
    )
    trust = _build_trust_governance(
        prelude=prelude,
        repair=repair,
        continuity=continuity,
        support=support,
    )
    clarity = _build_clarity_governance(
        prelude=prelude,
        continuity=continuity,
    )
    pacing = _build_pacing_governance(
        prelude=prelude,
        repair=repair,
        trust=trust,
        clarity=clarity,
    )
    commitment = _build_commitment_governance(
        prelude=prelude,
        boundary=boundary,
        autonomy=autonomy,
        pacing=pacing,
    )
    disclosure = _build_disclosure_governance(
        prelude=prelude,
        boundary=boundary,
        clarity=clarity,
        commitment=commitment,
    )
    reciprocity = _build_reciprocity_governance(
        prelude=prelude,
        dependency=dependency,
        support=support,
        autonomy=autonomy,
        commitment=commitment,
    )
    pressure = _build_pressure_governance(
        prelude=prelude,
        repair=repair,
        dependency=dependency,
        autonomy=autonomy,
        boundary=boundary,
        pacing=pacing,
        support=support,
        attunement=attunement,
        trust=trust,
        commitment=commitment,
    )
    relational = _build_relational_governance(
        support=support,
        continuity=continuity,
        repair=repair,
        trust=trust,
        clarity=clarity,
        pacing=pacing,
        commitment=commitment,
        disclosure=disclosure,
        reciprocity=reciprocity,
        pressure=pressure,
        boundary=boundary,
    )
    safety = _build_safety_governance(
        boundary=boundary,
        trust=trust,
        clarity=clarity,
        disclosure=disclosure,
        pressure=pressure,
        continuity=continuity,
        repair=repair,
        relational=relational,
    )
    return {
        "dependency": dependency,
        "autonomy": autonomy,
        "boundary": boundary,
        "support": support,
        "continuity": continuity,
        "repair": repair,
        "attunement": attunement,
        "trust": trust,
        "clarity": clarity,
        "pacing": pacing,
        "commitment": commitment,
        "disclosure": disclosure,
        "reciprocity": reciprocity,
        "pressure": pressure,
        "relational": relational,
        "safety": safety,
    }


def _build_growth_transition(
    *,
    prelude: _System3Prelude,
) -> _GrowthTransitionOutcome:
    growth_policy = _phase2_section("growth_transition")
    readiness_formula = dict(growth_policy.get("readiness_formula") or {})
    emotional_debt_penalties = dict(readiness_formula.get("emotional_debt_penalties") or {})
    growth_transition_readiness = _clamp(
        float(readiness_formula.get("base", 0.16))
        + prelude.relationship_state.psychological_safety
        * float(readiness_formula.get("psychological_safety_weight", 0.45))
        + min(prelude.recall_count, int(readiness_formula.get("recall_cap", 3)))
        * float(readiness_formula.get("recall_weight", 0.08))
        + (
            float(readiness_formula.get("user_model_confidence_bonus", 0.08))
            if prelude.user_model_confidence
            >= float(readiness_formula.get("user_model_confidence_threshold", 0.55))
            else 0.0
        )
        - float(emotional_debt_penalties.get(prelude.emotional_debt_status, 0.0))
        - (
            float(readiness_formula.get("repair_penalty", 0.12))
            if prelude.repair_assessment.repair_needed
            else 0.0
        )
        - (
            float(readiness_formula.get("filtered_recall_penalty", 0.08))
            if prelude.filtered_recall_count > 0
            else 0.0
        )
    )
    growth_state = _build_growth_transition_state(prelude=prelude)
    status = str(growth_state["status"])
    target = str(growth_state["target"])
    trigger = str(growth_state["trigger"])
    notes = list(growth_state["notes"])
    growth_trajectory = _build_growth_transition_trajectory(
        growth_stage=prelude.growth_stage,
        growth_transition_readiness=growth_transition_readiness,
        status=status,
        target=target,
        trigger=trigger,
    )
    trajectory_status = str(growth_trajectory["trajectory_status"])
    trajectory_target = str(growth_trajectory["trajectory_target"])
    trajectory_trigger = str(growth_trajectory["trajectory_trigger"])
    trajectory_notes = list(growth_trajectory["trajectory_notes"])

    return _GrowthTransitionOutcome(
        status=status,
        target=target,
        trigger=trigger,
        readiness=growth_transition_readiness,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_growth_transition_state(
    *,
    prelude: _System3Prelude,
) -> dict[str, object]:
    thresholds = dict(_phase2_section("growth_transition").get("state_thresholds") or {})
    if prelude.emotional_debt_status == "elevated":
        return {
            "status": "redirect",
            "target": "repairing",
            "trigger": "emotional_debt_requires_repair",
            "notes": ["elevated_debt_blocks_forward_growth"],
        }
    if (
        prelude.growth_stage == "deepening"
        and prelude.relationship_state.dependency_risk == "elevated"
    ):
        return {
            "status": "watch",
            "target": "steadying",
            "trigger": "dependency_risk_requires_rebalancing",
            "notes": ["deepening_not_safe_under_dependency_pressure"],
        }
    if prelude.growth_stage == "deepening" and prelude.repair_assessment.repair_needed:
        return {
            "status": "watch",
            "target": "repairing",
            "trigger": "repair_load_interrupts_deepening",
            "notes": ["repair_load_requires_repairing_stage"],
        }
    if (
        prelude.growth_stage == "forming"
        and prelude.turn_index >= int(thresholds.get("forming_ready_min_turn", 2))
        and prelude.relationship_state.psychological_safety
        >= float(thresholds.get("forming_ready_psychological_safety", 0.55))
    ):
        return {
            "status": "ready",
            "target": "stabilizing",
            "trigger": "early_patterning_ready",
            "notes": ["initial_turns_show_repeatable_alignment"],
        }
    if (
        prelude.growth_stage == "stabilizing"
        and prelude.recall_count > 0
        and prelude.relationship_state.psychological_safety
        >= float(thresholds.get("stabilizing_ready_psychological_safety", 0.66))
        and prelude.relationship_state.dependency_risk == "low"
    ):
        return {
            "status": "ready",
            "target": "steadying",
            "trigger": "continuity_and_safety_ready",
            "notes": ["continuity_signals_support_steadying"],
        }
    if (
        prelude.growth_stage == "steadying"
        and prelude.relationship_state.psychological_safety
        >= float(thresholds.get("steadying_ready_psychological_safety", 0.78))
        and prelude.recall_count >= int(thresholds.get("steadying_ready_min_recall_count", 2))
        and prelude.relationship_state.dependency_risk == "low"
        and not prelude.repair_assessment.repair_needed
    ):
        return {
            "status": "ready",
            "target": "deepening",
            "trigger": "trust_continuity_ready",
            "notes": ["safety_and_recall_support_deepening"],
        }
    if (
        prelude.growth_stage == "repairing"
        and prelude.emotional_debt_status == "low"
        and not prelude.repair_assessment.repair_needed
        and prelude.relationship_state.psychological_safety
        >= float(thresholds.get("repair_recovered_psychological_safety", 0.62))
    ):
        return {
            "status": "ready",
            "target": "steadying",
            "trigger": "repair_recovered",
            "notes": ["repair_signals_have_decompressed"],
        }
    if prelude.filtered_recall_count > 0 or prelude.user_model_evolution_status == "revise":
        return {
            "status": "watch",
            "target": prelude.growth_stage,
            "trigger": "model_or_context_drift_requires_hold",
            "notes": ["user_model_needs_stabilization_before_transition"],
        }
    return {
        "status": "stable",
        "target": prelude.growth_stage,
        "trigger": "maintain_current_stage",
        "notes": [],
    }


def _build_growth_transition_trajectory(
    *,
    growth_stage: str,
    growth_transition_readiness: float,
    status: str,
    target: str,
    trigger: str,
) -> dict[str, object]:
    readiness_formula = dict(_phase2_section("growth_transition").get("readiness_formula") or {})
    trajectory_notes: list[str] = []
    if status == "redirect":
        if trigger == "emotional_debt_requires_repair":
            trajectory_notes.append("elevated_debt_keeps_growth_line_redirected_toward_repair")
            return {
                "trajectory_status": "redirect",
                "trajectory_target": "repairing",
                "trajectory_trigger": "debt_redirect_active",
                "trajectory_notes": trajectory_notes,
            }
        trajectory_notes.append("current_relational_pressure_keeps_growth_line_in_redirect_mode")
        return {
            "trajectory_status": "redirect",
            "trajectory_target": "repairing",
            "trajectory_trigger": "growth_redirect_active",
            "trajectory_notes": trajectory_notes,
        }
    if status == "watch":
        if trigger == "dependency_risk_requires_rebalancing":
            trajectory_notes.append("dependency_pressure_keeps_growth_line_under_watch")
            return {
                "trajectory_status": "watch",
                "trajectory_target": "steadying",
                "trajectory_trigger": "dependency_transition_watch",
                "trajectory_notes": trajectory_notes,
            }
        if trigger == "repair_load_interrupts_deepening":
            trajectory_notes.append("repair_load_keeps_growth_line_from_advancing")
            return {
                "trajectory_status": "watch",
                "trajectory_target": "repairing",
                "trajectory_trigger": "repair_transition_watch",
                "trajectory_notes": trajectory_notes,
            }
        trajectory_notes.append("model_or_context_drift_keeps_growth_line_under_stability_watch")
        return {
            "trajectory_status": "watch",
            "trajectory_target": target,
            "trajectory_trigger": "stability_transition_watch",
            "trajectory_notes": trajectory_notes,
        }
    if status == "ready":
        if trigger == "early_patterning_ready":
            trajectory_notes.append("early_alignment_supports_first_growth_step")
            return {
                "trajectory_status": "advance",
                "trajectory_target": target,
                "trajectory_trigger": "patterning_transition_ready",
                "trajectory_notes": trajectory_notes,
            }
        if trigger == "continuity_and_safety_ready":
            trajectory_notes.append("continuity_and_safety_support_next_growth_stage")
            return {
                "trajectory_status": "advance",
                "trajectory_target": target,
                "trajectory_trigger": "continuity_transition_ready",
                "trajectory_notes": trajectory_notes,
            }
        if trigger == "trust_continuity_ready":
            trajectory_notes.append("trust_and_recall_support_deepening_transition")
            return {
                "trajectory_status": "advance",
                "trajectory_target": target,
                "trajectory_trigger": "deepening_transition_ready",
                "trajectory_notes": trajectory_notes,
            }
        if trigger == "repair_recovered":
            trajectory_notes.append("repair_recovery_supports_growth_line_reentry")
            return {
                "trajectory_status": "advance",
                "trajectory_target": target,
                "trajectory_trigger": "repair_recovery_transition_ready",
                "trajectory_notes": trajectory_notes,
            }
        trajectory_notes.append("growth_line_is_ready_to_advance")
        return {
            "trajectory_status": "advance",
            "trajectory_target": target,
            "trajectory_trigger": "growth_transition_ready",
            "trajectory_notes": trajectory_notes,
        }
    if growth_transition_readiness >= float(
        readiness_formula.get("stable_readiness_threshold", 0.58)
    ):
        trajectory_notes.append("growth_line_is_stable_and_holding_forward_readiness")
    return {
        "trajectory_status": "stable",
        "trajectory_target": growth_stage,
        "trajectory_trigger": "growth_line_stable",
        "trajectory_notes": trajectory_notes,
    }


def _build_version_migration(
    *,
    prelude: _System3Prelude,
    growth_transition: _GrowthTransitionOutcome,
) -> _VersionMigrationOutcome:
    version_policy = _phase2_section("version_migration")
    notes: list[str] = []
    if (prelude.response_post_audit and prelude.response_post_audit.status == "revise") or (
        prelude.runtime_quality_doctor_report
        and prelude.runtime_quality_doctor_report.status == "revise"
    ):
        status = "revise"
        scope = "hold_rebuild"
        trigger = "quality_drift_requires_hold"
        notes.append("quality_revision_blocks_stable_projection_cutover")
    elif prelude.identity_trajectory_status == "recenter":
        status = "revise"
        scope = "hold_rebuild"
        trigger = "identity_recenter_requires_hold"
        notes.append("identity_needs_recentering_before_version_cutover")
    elif prelude.user_model_evolution_status == "revise":
        status = "revise"
        scope = "hold_rebuild"
        trigger = "user_model_recalibration_requires_hold"
        notes.append("user_model_shift_requires_recalibration_before_migration")
    elif prelude.repair_assessment.repair_needed and prelude.emotional_debt_status == "elevated":
        status = "revise"
        scope = "hold_rebuild"
        trigger = "repair_load_requires_hold"
        notes.append("repair_pressure_and_debt_make_projection_cutover_risky")
    elif prelude.filtered_recall_count > 0:
        status = "watch"
        scope = "cautious_rebuild"
        trigger = "context_drift_requires_hold"
        notes.append("filtered_recall_signals_context_mismatch_for_rebuild")
    elif growth_transition.status in {"watch", "redirect"}:
        status = "watch"
        scope = "cautious_rebuild"
        trigger = "growth_transition_hold"
        notes.append("growth_transition_is_not_stable_enough_for_version_cutover")
    elif (
        prelude.turn_index <= int(version_policy.get("thin_history_turn_threshold", 2))
        and prelude.recall_count == 0
    ):
        status = "watch"
        scope = "cautious_rebuild"
        trigger = "low_continuity_sample"
        notes.append("session_history_is_still_thin_for_rebuild_confidence")
    else:
        status = "pass"
        scope = "stable_rebuild_ready"
        trigger = "projection_rebuild_ready"
        if prelude.recall_count > 0:
            notes.append("continuity_backed_state_supports_projection_rebuild")
        if prelude.turn_index >= 2:
            notes.append("session_history_is_deep_enough_for_version_cutover")
        if prelude.strategy_audit_status == "pass":
            notes.append("strategy_audit_is_stable_for_replay")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "hold"
        if trigger == "quality_drift_requires_hold":
            trajectory_target = "hold_rebuild"
            trajectory_trigger = "quality_hold_required"
            trajectory_notes.append("quality_drift_keeps_migration_line_in_hold_state")
        elif trigger == "identity_recenter_requires_hold":
            trajectory_target = "hold_rebuild"
            trajectory_trigger = "identity_hold_required"
            trajectory_notes.append("identity_recenter_keeps_migration_line_on_hold")
        elif trigger == "user_model_recalibration_requires_hold":
            trajectory_target = "hold_rebuild"
            trajectory_trigger = "user_model_hold_required"
            trajectory_notes.append("user_model_recalibration_keeps_migration_line_on_hold")
        else:
            trajectory_target = "hold_rebuild"
            trajectory_trigger = "migration_hold_required"
            trajectory_notes.append("migration_line_requires_hold_under_current_session_pressure")
    elif status == "watch":
        trajectory_status = "watch"
        if trigger == "context_drift_requires_hold":
            trajectory_target = "cautious_rebuild"
            trajectory_trigger = "context_drift_rebuild_watch"
            trajectory_notes.append("context_drift_keeps_migration_line_under_cautious_watch")
        elif trigger == "growth_transition_hold":
            trajectory_target = "cautious_rebuild"
            trajectory_trigger = "growth_transition_rebuild_watch"
            trajectory_notes.append(
                "growth_transition_instability_keeps_migration_line_under_watch"
            )
        elif trigger == "low_continuity_sample":
            trajectory_target = "cautious_rebuild"
            trajectory_trigger = "thin_history_rebuild_watch"
            trajectory_notes.append("thin_history_keeps_migration_line_in_cautious_mode")
        else:
            trajectory_target = "cautious_rebuild"
            trajectory_trigger = "migration_watch_active"
            trajectory_notes.append("migration_line_is_not_yet_stable_enough_for_full_cutover")
    else:
        trajectory_status = "stable"
        trajectory_target = "stable_rebuild_ready"
        trajectory_trigger = "migration_line_stable"
        trajectory_notes.append("migration_line_is_holding_stable_for_rebuild")

    return _VersionMigrationOutcome(
        status=status,
        scope=scope,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_base_snapshot_fields(
    *,
    prelude: _System3Prelude,
) -> dict[str, object]:
    return {
        "triggered_turn_index": prelude.turn_index,
        "identity_anchor": prelude.identity_anchor,
        "identity_consistency": prelude.identity_consistency,
        "identity_confidence": prelude.identity_confidence,
        "identity_trajectory_status": prelude.identity_trajectory_status,
        "identity_trajectory_target": prelude.identity_trajectory_target,
        "identity_trajectory_trigger": prelude.identity_trajectory_trigger,
        "identity_trajectory_notes": _compact(prelude.identity_trajectory_notes, limit=6),
        "growth_stage": prelude.growth_stage,
        "growth_signal": prelude.growth_signal,
        "user_model_confidence": prelude.user_model_confidence,
        "user_needs": _compact(prelude.user_needs, limit=5),
        "user_preferences": _compact(prelude.user_preferences, limit=5),
        "emotional_debt_status": prelude.emotional_debt_status,
        "emotional_debt_score": prelude.emotional_debt_score,
        "debt_signals": _compact(prelude.debt_signals, limit=6),
        "emotional_debt_trajectory_status": prelude.emotional_debt_trajectory_status,
        "emotional_debt_trajectory_target": prelude.emotional_debt_trajectory_target,
        "emotional_debt_trajectory_trigger": prelude.emotional_debt_trajectory_trigger,
        "emotional_debt_trajectory_notes": _compact(
            prelude.emotional_debt_trajectory_notes,
            limit=6,
        ),
        "strategy_audit_status": prelude.strategy_audit_status,
        "strategy_fit": prelude.strategy_fit,
        "strategy_audit_notes": _compact(prelude.strategy_audit_notes, limit=6),
        "strategy_audit_trajectory_status": prelude.strategy_audit_trajectory_status,
        "strategy_audit_trajectory_target": prelude.strategy_audit_trajectory_target,
        "strategy_audit_trajectory_trigger": prelude.strategy_audit_trajectory_trigger,
        "strategy_audit_trajectory_notes": _compact(
            prelude.strategy_audit_trajectory_notes,
            limit=6,
        ),
        "strategy_supervision_status": prelude.strategy_supervision_status,
        "strategy_supervision_mode": prelude.strategy_supervision_mode,
        "strategy_supervision_trigger": prelude.strategy_supervision_trigger,
        "strategy_supervision_notes": _compact(
            prelude.strategy_supervision_notes,
            limit=6,
        ),
        "strategy_supervision_trajectory_status": (prelude.strategy_supervision_trajectory_status),
        "strategy_supervision_trajectory_target": (prelude.strategy_supervision_trajectory_target),
        "strategy_supervision_trajectory_trigger": (
            prelude.strategy_supervision_trajectory_trigger
        ),
        "strategy_supervision_trajectory_notes": _compact(
            prelude.strategy_supervision_trajectory_notes,
            limit=6,
        ),
        "moral_reasoning_status": prelude.moral_reasoning_status,
        "moral_posture": prelude.moral_posture,
        "moral_conflict": prelude.moral_conflict,
        "moral_principles": _compact(prelude.moral_principles, limit=6),
        "moral_notes": _compact(prelude.moral_notes, limit=6),
        "moral_trajectory_status": prelude.moral_trajectory_status,
        "moral_trajectory_target": prelude.moral_trajectory_target,
        "moral_trajectory_trigger": prelude.moral_trajectory_trigger,
        "moral_trajectory_notes": _compact(prelude.moral_trajectory_notes, limit=6),
        "user_model_evolution_status": prelude.user_model_evolution_status,
        "user_model_revision_mode": prelude.user_model_revision_mode,
        "user_model_shift_signal": prelude.user_model_shift_signal,
        "user_model_evolution_notes": _compact(
            prelude.user_model_evolution_notes,
            limit=6,
        ),
        "user_model_trajectory_status": prelude.user_model_trajectory_status,
        "user_model_trajectory_target": prelude.user_model_trajectory_target,
        "user_model_trajectory_trigger": prelude.user_model_trajectory_trigger,
        "user_model_trajectory_notes": _compact(
            prelude.user_model_trajectory_notes,
            limit=6,
        ),
        "expectation_calibration_status": prelude.expectation_calibration_status,
        "expectation_calibration_target": prelude.expectation_calibration_target,
        "expectation_calibration_trigger": prelude.expectation_calibration_trigger,
        "expectation_calibration_notes": _compact(
            prelude.expectation_calibration_notes,
            limit=6,
        ),
        "expectation_calibration_trajectory_status": (
            prelude.expectation_calibration_trajectory_status
        ),
        "expectation_calibration_trajectory_target": (
            prelude.expectation_calibration_trajectory_target
        ),
        "expectation_calibration_trajectory_trigger": (
            prelude.expectation_calibration_trajectory_trigger
        ),
        "expectation_calibration_trajectory_notes": _compact(
            prelude.expectation_calibration_trajectory_notes,
            limit=6,
        ),
    }


def _build_phase2_snapshot(
    *,
    prelude: _System3Prelude,
    governance_outcomes: dict[str, _GovernanceOutcome],
    growth_transition: _GrowthTransitionOutcome,
    version_migration: _VersionMigrationOutcome,
    review_focus: list[str],
) -> System3Snapshot:
    governance_snapshot_fields: dict[str, object] = {}
    for domain in _SYSTEM3_GOVERNANCE_DOMAIN_ORDER:
        governance_snapshot_fields.update(
            _governance_kwargs(prefix=domain, outcome=governance_outcomes[domain])
        )
    return System3Snapshot(
        **_build_base_snapshot_fields(prelude=prelude),
        **governance_snapshot_fields,
        growth_transition_status=growth_transition.status,
        growth_transition_target=growth_transition.target,
        growth_transition_trigger=growth_transition.trigger,
        growth_transition_readiness=round(growth_transition.readiness, 3),
        growth_transition_notes=_compact(growth_transition.notes, limit=6),
        growth_transition_trajectory_status=growth_transition.trajectory_status,
        growth_transition_trajectory_target=growth_transition.trajectory_target,
        growth_transition_trajectory_trigger=growth_transition.trajectory_trigger,
        growth_transition_trajectory_notes=_compact(
            growth_transition.trajectory_notes,
            limit=6,
        ),
        version_migration_status=version_migration.status,
        version_migration_scope=version_migration.scope,
        version_migration_trigger=version_migration.trigger,
        version_migration_notes=_compact(version_migration.notes, limit=6),
        version_migration_trajectory_status=version_migration.trajectory_status,
        version_migration_trajectory_target=version_migration.trajectory_target,
        version_migration_trajectory_trigger=version_migration.trajectory_trigger,
        version_migration_trajectory_notes=_compact(
            version_migration.trajectory_notes,
            limit=6,
        ),
        review_focus=review_focus,
    )


def _build_dependency_governance(*, prelude: _System3Prelude) -> _GovernanceOutcome:
    dependency_policy = _phase2_governance_line("dependency")
    expectation_watch_targets = {
        str(item) for item in dependency_policy.get("expectation_watch_targets", []) or []
    }
    notes: list[str] = []
    branch_id = "pass"
    if prelude.relationship_state.dependency_risk == "elevated":
        status = "revise"
        if prelude.knowledge_boundary_decision.decision == "support_with_boundary":
            branch_id = "revise_boundary"
        elif prelude.repair_assessment.repair_needed:
            branch_id = "revise_repair"
        else:
            branch_id = "revise_default"
        branch = _phase2_branch("dependency", "branches", branch_id)
        target = branch.get("target", "agency_preserving_support")
        trigger = branch.get("trigger", "dependency_pressure_detected")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.expectation_calibration_status == "revise":
        status = "watch"
        target = prelude.expectation_calibration_target
        if prelude.expectation_calibration_trigger == "certainty_request_requires_reset":
            branch_id = "watch_expectation_certainty"
        else:
            branch_id = "watch_expectation_default"
        branch = _phase2_branch("dependency", "branches", branch_id)
        trigger = branch.get("trigger", "expectation_dependency_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.expectation_calibration_status == "watch"
        and prelude.expectation_calibration_target
        in (
            expectation_watch_targets
            or {
                "low_pressure_repair_support",
                "context_before_commitment",
                "uncertainty_honest_support",
            }
        )
    ):
        status = "watch"
        target = prelude.expectation_calibration_target
        branch_id = "watch_expectation_active"
        branch = _phase2_branch("dependency", "branches", branch_id)
        trigger = branch.get("trigger", "expectation_support_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.emotional_debt_status in {"watch", "elevated"}
        and prelude.repair_assessment.repair_needed
    ):
        status = "watch"
        branch_id = "watch_repair_load"
        branch = _phase2_branch("dependency", "branches", branch_id)
        target = branch.get("target", "repair_before_reliance")
        trigger = branch.get("trigger", "repair_load_dependency_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("dependency", "branches", branch_id)
        target = branch.get("target", "steady_low_dependency_support")
        trigger = branch.get("trigger", "dependency_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_boundary": "recenter_boundary",
            "revise_repair": "recenter_repair",
        }.get(branch_id, "recenter_default")
        branch = _phase2_branch("dependency", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "dependency_recenter_required")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_growth_rebalance": "watch_growth",
            "watch_repair_load": "watch_repair",
            "watch_expectation_certainty": "watch_certainty",
        }.get(branch_id)
        if trajectory_branch_id is None and target == "context_before_commitment":
            trajectory_branch_id = "watch_clarification"
        if trajectory_branch_id is None:
            trajectory_branch_id = "watch_default"
        branch = _phase2_branch("dependency", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "dependency_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("dependency", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "dependency_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_autonomy_governance(*, prelude: _System3Prelude) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if prelude.relationship_state.dependency_risk == "elevated":
        status = "revise"
        if prelude.knowledge_boundary_decision.decision == "support_with_boundary":
            branch_id = "revise_boundary"
        else:
            branch_id = "revise_default"
        branch = _phase2_branch("autonomy", "branches", branch_id)
        target = branch.get("target", "explicit_autonomy_support")
        trigger = branch.get("trigger", "dependency_autonomy_reset")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.repair_assessment.repair_needed
        and prelude.policy_gate.selected_path == "repair_first"
    ):
        status = "watch"
        branch_id = "watch_repair"
        branch = _phase2_branch("autonomy", "branches", branch_id)
        target = branch.get("target", "repair_with_user_space")
        trigger = branch.get("trigger", "repair_pressure_autonomy_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.confidence_assessment.needs_clarification:
        status = "watch"
        branch_id = "watch_clarification"
        branch = _phase2_branch("autonomy", "branches", branch_id)
        target = branch.get("target", "context_before_commitment")
        trigger = branch.get("trigger", "clarification_autonomy_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.knowledge_boundary_decision.should_disclose_uncertainty:
        status = "watch"
        branch_id = "watch_uncertainty"
        branch = _phase2_branch("autonomy", "branches", branch_id)
        target = branch.get("target", "uncertainty_with_opt_out")
        trigger = branch.get("trigger", "uncertainty_autonomy_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.response_sequence_plan is not None
        and prelude.response_sequence_plan.mode == "two_part_sequence"
    ):
        status = "watch"
        branch_id = "watch_segmented"
        branch = _phase2_branch("autonomy", "branches", branch_id)
        target = branch.get("target", "segmented_with_user_space")
        trigger = branch.get("trigger", "segmented_autonomy_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("autonomy", "branches", branch_id)
        target = branch.get("target", "steady_explicit_autonomy")
        trigger = branch.get("trigger", "autonomy_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = (
            "recenter_boundary" if branch_id == "revise_boundary" else "recenter_default"
        )
        branch = _phase2_branch("autonomy", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "autonomy_recenter_required")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_repair": "watch_repair",
            "watch_clarification": "watch_clarification",
            "watch_uncertainty": "watch_uncertainty",
            "watch_segmented": "watch_segmented",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("autonomy", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "autonomy_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("autonomy", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "autonomy_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_boundary_governance(*, prelude: _System3Prelude) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if prelude.policy_gate.red_line_status == "blocked":
        status = "revise"
        branch_id = "revise_blocked"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "hard_boundary_containment")
        trigger = branch.get("trigger", "policy_gate_blocked")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.policy_gate.red_line_status == "boundary_sensitive"
        or prelude.knowledge_boundary_decision.decision == "support_with_boundary"
    ):
        status = "revise"
        if prelude.policy_gate.red_line_status == "boundary_sensitive":
            branch_id = "revise_explicit_gate"
        else:
            branch_id = "revise_explicit_knowledge"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "explicit_boundary_support")
        trigger = branch.get("trigger", "boundary_sensitive_gate_active")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.relationship_state.dependency_risk == "elevated":
        status = "watch"
        branch_id = "watch_dependency"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "dependency_safe_boundary_support")
        trigger = branch.get("trigger", "dependency_boundary_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.knowledge_boundary_decision.should_disclose_uncertainty:
        status = "watch"
        branch_id = "watch_uncertainty"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "uncertainty_boundary_support")
        trigger = branch.get("trigger", "uncertainty_boundary_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.confidence_assessment.needs_clarification:
        status = "watch"
        branch_id = "watch_clarification"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "clarify_before_boundary_commitment")
        trigger = branch.get("trigger", "clarification_boundary_watch")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.repair_assessment.repair_needed
        and prelude.policy_gate.selected_path == "repair_first"
    ):
        status = "watch"
        branch_id = "watch_repair"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "repair_first_boundary_softening")
        trigger = branch.get("trigger", "repair_boundary_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("boundary", "branches", branch_id)
        target = branch.get("target", "steady_clear_boundary_support")
        trigger = branch.get("trigger", "boundary_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = (
            "recenter_blocked" if branch_id == "revise_blocked" else "recenter_explicit"
        )
        branch = _phase2_branch("boundary", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "boundary_support_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_dependency": "watch_dependency",
            "watch_uncertainty": "watch_uncertainty",
            "watch_clarification": "watch_clarification",
            "watch_repair": "watch_repair",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("boundary", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "boundary_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("boundary", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "boundary_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_support_governance(
    *,
    prelude: _System3Prelude,
    dependency: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    boundary: _GovernanceOutcome,
) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if dependency.status == "revise" or autonomy.status == "revise" or boundary.status == "revise":
        status = "revise"
        if dependency.status == "revise":
            branch_id = "revise_dependency"
        elif boundary.status == "revise":
            branch_id = "revise_boundary"
        else:
            branch_id = "revise_autonomy"
        branch = _phase2_branch("support", "branches", branch_id)
        target = branch.get("target", "steady_bounded_support")
        trigger = branch.get("trigger", "support_line_stable")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        dependency.status == "watch"
        or autonomy.status == "watch"
        or boundary.status == "watch"
        or prelude.expectation_calibration_status == "watch"
    ):
        status = "watch"
        if (
            prelude.repair_assessment.repair_needed
            and prelude.policy_gate.selected_path == "repair_first"
        ):
            branch_id = "watch_repair"
        elif prelude.confidence_assessment.needs_clarification:
            branch_id = "watch_clarification"
        elif prelude.knowledge_boundary_decision.should_disclose_uncertainty:
            branch_id = "watch_uncertainty"
        elif (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        ):
            branch_id = "watch_segmented"
        else:
            branch_id = "watch_default"
        branch = _phase2_branch("support", "branches", branch_id)
        target = branch.get("target", "steady_bounded_support")
        trigger = branch.get("trigger", "support_watch_active")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("support", "branches", branch_id)
        target = branch.get("target", "steady_bounded_support")
        trigger = branch.get("trigger", "support_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_dependency": "recenter_dependency",
            "revise_boundary": "recenter_boundary",
        }.get(branch_id, "recenter_autonomy")
        branch = _phase2_branch("support", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "support_recenter_required")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_repair": "watch_repair",
            "watch_clarification": "watch_clarification",
            "watch_uncertainty": "watch_uncertainty",
            "watch_segmented": "watch_segmented",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("support", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "support_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("support", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "support_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_continuity_governance(
    *,
    prelude: _System3Prelude,
    support: _GovernanceOutcome,
) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if prelude.filtered_recall_count > 0:
        status = "revise"
        branch_id = "revise_filtered_recall"
        branch = _phase2_branch("continuity", "branches", branch_id)
        target = branch.get("target", "context_reanchor_continuity")
        trigger = branch.get("trigger", "filtered_recall_continuity_reset")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.user_model_evolution_status == "revise"
        and prelude.recall_count == 0
        and prelude.turn_index >= 3
    ):
        status = "revise"
        branch_id = "revise_underfit_memory"
        branch = _phase2_branch("continuity", "branches", branch_id)
        target = branch.get("target", "memory_regrounded_continuity")
        trigger = branch.get("trigger", "underfit_memory_continuity_reset")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        support.status == "watch"
        or prelude.confidence_assessment.needs_clarification
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
        or (prelude.recall_count == 0 and prelude.turn_index >= 2)
    ):
        status = "watch"
        if support.status == "watch":
            branch_id = "watch_support"
        elif prelude.confidence_assessment.needs_clarification:
            branch_id = "watch_clarification"
        elif (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        ):
            branch_id = "watch_segmented"
        else:
            branch_id = "watch_thin_context"
        branch = _phase2_branch("continuity", "branches", branch_id)
        target = branch.get("target", "thin_context_continuity")
        trigger = branch.get("trigger", "thin_context_continuity_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("continuity", "branches", branch_id)
        target = branch.get("target", "steady_contextual_continuity")
        trigger = branch.get("trigger", "continuity_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_filtered_recall": "recenter_filtered_recall",
        }.get(branch_id, "recenter_underfit_memory")
        branch = _phase2_branch("continuity", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "context_reanchor_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_support": "watch_support",
            "watch_clarification": "watch_clarification",
            "watch_segmented": "watch_segmented",
            "watch_thin_context": "watch_thin_context",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("continuity", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "continuity_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("continuity", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "continuity_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_repair_governance(
    *,
    prelude: _System3Prelude,
    continuity: _GovernanceOutcome,
    support: _GovernanceOutcome,
) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if prelude.repair_assessment.repair_needed and prelude.repair_assessment.severity == "high":
        status = "revise"
        if prelude.repair_assessment.rupture_type == "boundary_risk":
            branch_id = "revise_boundary"
        elif prelude.repair_assessment.rupture_type == "attunement_gap":
            branch_id = "revise_attunement"
        else:
            branch_id = "revise_clarity"
        branch = _phase2_branch("repair", "branches", branch_id)
        target = branch.get("target", "clarity_repair_scaffold")
        trigger = branch.get("trigger", "clarity_repair_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.repair_assessment.repair_needed
        or prelude.emotional_debt_status in {"watch", "elevated"}
        or continuity.status == "watch"
        or support.status == "watch"
    ):
        status = "watch"
        if prelude.emotional_debt_status in {"watch", "elevated"}:
            branch_id = "watch_debt"
        elif continuity.status == "watch":
            branch_id = "watch_continuity"
        elif support.status == "watch":
            branch_id = "watch_support"
        elif prelude.repair_assessment.rupture_type == "attunement_gap":
            branch_id = "watch_attunement"
        else:
            branch_id = "watch_clarity"
        branch = _phase2_branch("repair", "branches", branch_id)
        target = branch.get("target", "clarity_repair_scaffold")
        trigger = branch.get("trigger", "clarity_repair_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("repair", "branches", branch_id)
        target = branch.get("target", "steady_relational_repair_posture")
        trigger = branch.get("trigger", "repair_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_boundary": "recenter_boundary",
            "revise_attunement": "recenter_attunement",
        }.get(branch_id, "recenter_clarity")
        branch = _phase2_branch("repair", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "clarity_repair_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_debt": "watch_debt",
            "watch_continuity": "watch_continuity",
            "watch_support": "watch_support",
            "watch_attunement": "watch_attunement",
            "watch_clarity": "watch_clarity",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("repair", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "repair_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("repair", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "repair_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_attunement_governance(
    *,
    prelude: _System3Prelude,
    repair: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    support: _GovernanceOutcome,
) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if (
        prelude.repair_assessment.repair_needed
        and prelude.repair_assessment.rupture_type == "attunement_gap"
        and prelude.repair_assessment.severity == "high"
    ):
        status = "revise"
        branch_id = "revise_attunement_gap"
        branch = _phase2_branch("attunement", "branches", branch_id)
        target = branch.get("target", "attunement_repair_scaffold")
        trigger = branch.get("trigger", "attunement_gap_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif continuity.status == "revise":
        status = "revise"
        branch_id = "revise_continuity"
        branch = _phase2_branch("attunement", "branches", branch_id)
        target = branch.get("target", "reanchor_before_attunement_rebuild")
        trigger = branch.get("trigger", "continuity_attunement_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif prelude.emotional_debt_status == "elevated":
        status = "revise"
        branch_id = "revise_debt"
        branch = _phase2_branch("attunement", "branches", branch_id)
        target = branch.get("target", "decompression_before_attunement_push")
        trigger = branch.get("trigger", "debt_attunement_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.repair_assessment.attunement_gap
        or repair.status == "watch"
        or continuity.status == "watch"
        or support.status == "watch"
        or prelude.emotional_debt_status == "watch"
    ):
        status = "watch"
        if prelude.repair_assessment.attunement_gap:
            branch_id = "watch_attunement_gap"
        elif continuity.status == "watch":
            branch_id = "watch_continuity"
        elif repair.status == "watch":
            branch_id = "watch_repair"
        elif support.status == "watch":
            branch_id = "watch_support"
        else:
            branch_id = "watch_debt"
        branch = _phase2_branch("attunement", "branches", branch_id)
        target = branch.get("target", "debt_buffered_attunement_watch")
        trigger = branch.get("trigger", "debt_attunement_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("attunement", "branches", branch_id)
        target = branch.get("target", "steady_relational_attunement")
        trigger = branch.get("trigger", "attunement_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_attunement_gap": "recenter_attunement_gap",
            "revise_continuity": "recenter_continuity",
        }.get(branch_id, "recenter_debt")
        branch = _phase2_branch("attunement", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "debt_attunement_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_attunement_gap": "watch_attunement_gap",
            "watch_continuity": "watch_continuity",
            "watch_repair": "watch_repair",
            "watch_support": "watch_support",
            "watch_debt": "watch_debt",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("attunement", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "attunement_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("attunement", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "attunement_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_trust_governance(
    *,
    prelude: _System3Prelude,
    repair: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    support: _GovernanceOutcome,
) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if (
        prelude.policy_gate.red_line_status == "blocked"
        or prelude.relationship_state.psychological_safety < 0.48
        or (
            prelude.repair_assessment.repair_needed
            and prelude.repair_assessment.severity == "high"
            and prelude.relationship_state.turbulence_risk == "elevated"
        )
    ):
        status = "revise"
        if prelude.policy_gate.red_line_status == "blocked":
            branch_id = "revise_boundary"
        elif continuity.status == "revise":
            branch_id = "revise_continuity"
        elif (
            prelude.repair_assessment.repair_needed and prelude.repair_assessment.severity == "high"
        ):
            branch_id = "revise_repair"
        else:
            branch_id = "revise_debt"
        branch = _phase2_branch("trust", "branches", branch_id)
        target = branch.get("target", "decompression_before_trust_push")
        trigger = branch.get("trigger", "debt_trust_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.emotional_debt_status in {"watch", "elevated"}
        or prelude.relationship_state.turbulence_risk == "elevated"
        or prelude.relationship_state.psychological_safety < 0.72
        or repair.status == "watch"
        or continuity.status == "watch"
        or support.status == "watch"
    ):
        status = "watch"
        if prelude.emotional_debt_status in {"watch", "elevated"}:
            branch_id = "watch_debt"
        elif continuity.status == "watch":
            branch_id = "watch_continuity"
        elif repair.status == "watch":
            branch_id = "watch_repair"
        elif support.status == "watch":
            branch_id = "watch_support"
        elif prelude.relationship_state.turbulence_risk == "elevated":
            branch_id = "watch_turbulence"
        else:
            branch_id = "watch_default"
        branch = _phase2_branch("trust", "branches", branch_id)
        target = branch.get("target", "steady_low_pressure_trust")
        trigger = branch.get("trigger", "trust_watch_active")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("trust", "branches", branch_id)
        target = branch.get("target", "steady_mutual_trust_posture")
        trigger = branch.get("trigger", "trust_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_boundary": "recenter_boundary",
            "revise_continuity": "recenter_continuity",
            "revise_repair": "recenter_repair",
        }.get(branch_id, "recenter_debt")
        branch = _phase2_branch("trust", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "debt_trust_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_debt": "watch_debt",
            "watch_continuity": "watch_continuity",
            "watch_repair": "watch_repair",
            "watch_support": "watch_support",
            "watch_turbulence": "watch_turbulence",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("trust", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "trust_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("trust", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "trust_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_clarity_governance(
    *,
    prelude: _System3Prelude,
    continuity: _GovernanceOutcome,
) -> _GovernanceOutcome:
    notes: list[str] = []
    branch_id = "pass"
    if prelude.confidence_assessment.needs_clarification and prelude.filtered_recall_count > 0:
        status = "revise"
        branch_id = "revise_filtered_context"
        branch = _phase2_branch("clarity", "branches", branch_id)
        target = branch.get("target", "reanchor_before_clarity_commitment")
        trigger = branch.get("trigger", "filtered_context_clarity_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.confidence_assessment.needs_clarification
        and prelude.knowledge_boundary_decision.should_disclose_uncertainty
    ):
        status = "revise"
        branch_id = "revise_uncertainty"
        branch = _phase2_branch("clarity", "branches", branch_id)
        target = branch.get("target", "uncertainty_first_clarity_scaffold")
        trigger = branch.get("trigger", "uncertainty_clarity_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.repair_assessment.repair_needed
        and prelude.repair_assessment.rupture_type == "clarity_gap"
    ):
        status = "revise"
        branch_id = "revise_repair"
        branch = _phase2_branch("clarity", "branches", branch_id)
        target = branch.get("target", "repair_scaffolded_clarity")
        trigger = branch.get("trigger", "repair_clarity_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.confidence_assessment.needs_clarification
        or prelude.knowledge_boundary_decision.should_disclose_uncertainty
        or continuity.status == "watch"
        or prelude.expectation_calibration_status == "watch"
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        status = "watch"
        if prelude.confidence_assessment.needs_clarification:
            branch_id = "watch_clarification"
        elif prelude.knowledge_boundary_decision.should_disclose_uncertainty:
            branch_id = "watch_uncertainty"
        elif continuity.status == "watch":
            branch_id = "watch_continuity"
        elif prelude.expectation_calibration_status == "watch":
            branch_id = "watch_expectation"
        else:
            branch_id = "watch_segmented"
        branch = _phase2_branch("clarity", "branches", branch_id)
        target = branch.get("target", "stepwise_clarity_watch")
        trigger = branch.get("trigger", "segmented_clarity_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("clarity", "branches", branch_id)
        target = branch.get("target", "steady_contextual_clarity")
        trigger = branch.get("trigger", "clarity_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_filtered_context": "recenter_filtered_context",
            "revise_uncertainty": "recenter_uncertainty",
        }.get(branch_id, "recenter_repair")
        branch = _phase2_branch("clarity", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "repair_clarity_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_clarification": "watch_clarification",
            "watch_uncertainty": "watch_uncertainty",
            "watch_continuity": "watch_continuity",
            "watch_expectation": "watch_expectation",
            "watch_segmented": "watch_segmented",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("clarity", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "clarity_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("clarity", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "clarity_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_pacing_governance(
    *,
    prelude: _System3Prelude,
    repair: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    clarity: _GovernanceOutcome,
) -> _GovernanceOutcome:
    growth_transition_watch_signal = (
        prelude.growth_stage in {"repairing", "stabilizing"}
        and prelude.relationship_state.psychological_safety < 0.78
    )
    status = ""
    notes: list[str] = []
    branch_id = "pass"
    if prelude.emotional_debt_status == "elevated":
        status = "revise"
        branch_id = "revise_debt"
    elif repair.status == "revise":
        status = "revise"
        branch_id = "revise_repair"
    elif prelude.expectation_calibration_status == "revise":
        status = "revise"
        branch_id = "revise_expectation"
    if status == "revise":
        branch = _phase2_branch("pacing", "branches", branch_id)
        target = branch.get("target", "expectation_reset_pacing")
        trigger = branch.get("trigger", "expectation_pacing_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.emotional_debt_status == "watch"
        or trust.status == "watch"
        or clarity.status == "watch"
        or growth_transition_watch_signal
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        status = "watch"
        if trust.status == "watch":
            branch_id = "watch_trust"
        elif clarity.status == "watch":
            branch_id = "watch_clarity"
        elif (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        ):
            branch_id = "watch_segmented"
        elif growth_transition_watch_signal:
            branch_id = "watch_growth"
        else:
            branch_id = "watch_default"
        branch = _phase2_branch("pacing", "branches", branch_id)
        target = branch.get("target", "debt_buffered_pacing")
        trigger = branch.get("trigger", "pacing_watch_active")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("pacing", "branches", branch_id)
        target = branch.get("target", "steady_relational_pacing")
        trigger = branch.get("trigger", "pacing_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_debt": "recenter_debt",
            "revise_repair": "recenter_repair",
        }.get(branch_id, "recenter_expectation")
        branch = _phase2_branch("pacing", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "expectation_pacing_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_trust": "watch_trust",
            "watch_clarity": "watch_clarity",
            "watch_segmented": "watch_segmented",
            "watch_growth": "watch_growth",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("pacing", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "pacing_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("pacing", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "pacing_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_commitment_governance(
    *,
    prelude: _System3Prelude,
    boundary: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
) -> _GovernanceOutcome:
    commitment_state = _build_commitment_governance_state(
        prelude=prelude,
        boundary=boundary,
        autonomy=autonomy,
        pacing=pacing,
    )
    status = str(commitment_state["status"])
    target = str(commitment_state["target"])
    trigger = str(commitment_state["trigger"])
    notes = list(commitment_state["notes"])
    branch_id = str(commitment_state["branch_id"])
    commitment_trajectory = _build_commitment_governance_trajectory(
        branch_id=branch_id,
        status=status,
        target=target,
    )
    trajectory_status = str(commitment_trajectory["trajectory_status"])
    trajectory_target = str(commitment_trajectory["trajectory_target"])
    trajectory_trigger = str(commitment_trajectory["trajectory_trigger"])
    trajectory_notes = list(commitment_trajectory["trajectory_notes"])

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_commitment_governance_state(
    *,
    prelude: _System3Prelude,
    boundary: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
) -> dict[str, object]:
    line = "commitment"
    if boundary.status == "revise":
        branch_id = "revise_boundary"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "bounded_noncommitment_support"),
            "trigger": branch.get("trigger", "boundary_commitment_recenter"),
            "notes": [
                branch.get(
                    "note",
                    "boundary_recenter_requires_noncommitment_before_forward_motion",
                )
            ],
        }
    if prelude.expectation_calibration_status == "revise":
        branch_id = "revise_expectation"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "expectation_reset_before_commitment"),
            "trigger": branch.get("trigger", "expectation_commitment_recenter"),
            "notes": [
                branch.get("note", "expectation_reset_requires_explicitly_lower_commitment_shape")
            ],
        }
    if autonomy.status == "revise":
        branch_id = "revise_autonomy"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "explicit_user_led_noncommitment"),
            "trigger": branch.get("trigger", "autonomy_commitment_recenter"),
            "notes": [
                branch.get("note", "autonomy_recenter_requires_user_led_noncommitment_support")
            ],
        }
    if (
        prelude.confidence_assessment.needs_clarification
        and prelude.knowledge_boundary_decision.should_disclose_uncertainty
    ):
        branch_id = "revise_uncertainty"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "uncertainty_first_noncommitment"),
            "trigger": branch.get("trigger", "uncertainty_commitment_recenter"),
            "notes": [
                branch.get(
                    "note",
                    "uncertainty_and_clarification_require_noncommitment_before_forwarding",
                )
            ],
        }
    if (
        prelude.repair_assessment.repair_needed
        or prelude.confidence_assessment.needs_clarification
        or prelude.knowledge_boundary_decision.should_disclose_uncertainty
        or prelude.expectation_calibration_status == "watch"
        or boundary.status == "watch"
        or autonomy.status == "watch"
        or pacing.status == "watch"
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        if (
            prelude.repair_assessment.repair_needed
            and prelude.policy_gate.selected_path == "repair_first"
        ):
            branch_id = "watch_repair"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "repair_buffered_commitment_watch"),
                "trigger": branch.get("trigger", "repair_commitment_watch"),
                "notes": [
                    branch.get(
                        "note",
                        "repair_pressure_keeps_commitment_line_buffered_and_low_pressure",
                    )
                ],
            }
        if prelude.confidence_assessment.needs_clarification:
            branch_id = "watch_clarification"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "clarify_before_commitment_watch"),
                "trigger": branch.get("trigger", "clarification_commitment_watch"),
                "notes": [
                    branch.get(
                        "note",
                        "clarification_need_keeps_commitment_line_context_first",
                    )
                ],
            }
        if prelude.knowledge_boundary_decision.should_disclose_uncertainty:
            branch_id = "watch_uncertainty"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "uncertainty_buffered_commitment_watch"),
                "trigger": branch.get("trigger", "uncertainty_commitment_watch"),
                "notes": [
                    branch.get(
                        "note",
                        "uncertainty_keeps_commitment_line_low_certainty_and_bounded",
                    )
                ],
            }
        if prelude.expectation_calibration_status == "watch":
            branch_id = "watch_expectation"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "expectation_buffered_commitment_watch"),
                "trigger": branch.get("trigger", "expectation_commitment_watch"),
                "notes": [
                    branch.get("note", "expectation_watch_keeps_commitment_line_explicitly_bounded")
                ],
            }
        if boundary.status == "watch":
            branch_id = "watch_boundary"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "bounded_commitment_watch"),
                "trigger": branch.get("trigger", "boundary_commitment_watch"),
                "notes": [
                    branch.get(
                        "note",
                        "boundary_watch_keeps_commitment_line_soft_and_bounded",
                    )
                ],
            }
        if autonomy.status == "watch":
            branch_id = "watch_autonomy"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "user_led_commitment_watch"),
                "trigger": branch.get("trigger", "autonomy_commitment_watch"),
                "notes": [branch.get("note", "autonomy_watch_keeps_commitment_line_user_led")],
            }
        if pacing.status == "watch":
            branch_id = "watch_pacing"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "slow_commitment_watch"),
                "trigger": branch.get("trigger", "pacing_commitment_watch"),
                "notes": [
                    branch.get(
                        "note",
                        "pacing_watch_keeps_commitment_line_slow_and_incremental",
                    )
                ],
            }
        branch_id = "watch_segmented"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "stepwise_commitment_watch"),
            "trigger": branch.get("trigger", "segmented_commitment_watch"),
            "notes": [branch.get("note", "segmented_delivery_keeps_commitment_line_stepwise")],
        }
    branch_id = "pass"
    branch = _phase2_branch(line, "branches", branch_id)
    return {
        "status": "pass",
        "branch_id": branch_id,
        "target": branch.get("target", "steady_calibrated_commitment"),
        "trigger": branch.get("trigger", "commitment_line_stable"),
        "notes": [],
    }


def _build_commitment_governance_trajectory(
    *,
    branch_id: str,
    status: str,
    target: str,
) -> dict[str, object]:
    line = "commitment"
    if status == "revise":
        trajectory_branch_id = {
            "revise_boundary": "recenter_boundary",
            "revise_expectation": "recenter_expectation",
            "revise_autonomy": "recenter_autonomy",
        }.get(branch_id, "recenter_uncertainty")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "recenter",
            "trajectory_target": branch.get("target", "uncertainty_first_noncommitment"),
            "trajectory_trigger": branch.get("trigger", "uncertainty_commitment_recenter"),
            "trajectory_notes": [
                branch.get(
                    "note",
                    "uncertainty_pressure_keeps_commitment_line_in_noncommitment_mode",
                )
            ],
        }
    if status == "watch":
        trajectory_branch_id = {
            "watch_repair": "watch_repair",
            "watch_clarification": "watch_clarification",
            "watch_uncertainty": "watch_uncertainty",
            "watch_expectation": "watch_expectation",
            "watch_boundary": "watch_boundary",
            "watch_autonomy": "watch_autonomy",
            "watch_pacing": "watch_pacing",
            "watch_segmented": "watch_segmented",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "watch",
            "trajectory_target": branch.get("target", target),
            "trajectory_trigger": branch.get("trigger", "commitment_watch_active"),
            "trajectory_notes": [
                branch.get(
                    "note",
                    "commitment_line_is_shifting_without_full_recenter",
                )
            ],
        }
    branch = _phase2_branch(line, "trajectory_branches", "stable")
    return {
        "trajectory_status": "stable",
        "trajectory_target": branch.get("target", "steady_calibrated_commitment"),
        "trajectory_trigger": branch.get("trigger", "commitment_governance_stable"),
        "trajectory_notes": [
            branch.get(
                "note",
                "commitment_line_is_holding_stable_and_calibrated",
            )
        ],
    }


def _build_disclosure_governance(
    *,
    prelude: _System3Prelude,
    boundary: _GovernanceOutcome,
    clarity: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
) -> _GovernanceOutcome:
    status = ""
    notes: list[str] = []
    branch_id = "pass"
    if (
        prelude.filtered_recall_count > 0
        and prelude.knowledge_boundary_decision.should_disclose_uncertainty
    ):
        status = "revise"
        branch_id = "revise_filtered_context"
    elif boundary.status == "revise":
        status = "revise"
        branch_id = "revise_boundary"
    elif (
        prelude.confidence_assessment.needs_clarification
        and prelude.knowledge_boundary_decision.should_disclose_uncertainty
    ):
        status = "revise"
        branch_id = "revise_uncertainty"
    if status == "revise":
        branch = _phase2_branch("disclosure", "branches", branch_id)
        target = branch.get("target", "explicit_uncertainty_disclosure")
        trigger = branch.get("trigger", "uncertainty_disclosure_recenter")
        if note := branch.get("note"):
            notes.append(note)
    elif (
        prelude.confidence_assessment.needs_clarification
        or prelude.knowledge_boundary_decision.should_disclose_uncertainty
        or clarity.status == "watch"
        or boundary.status == "watch"
        or commitment.status == "watch"
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        status = "watch"
        if prelude.confidence_assessment.needs_clarification:
            branch_id = "watch_clarification"
        elif prelude.knowledge_boundary_decision.should_disclose_uncertainty:
            branch_id = "watch_uncertainty"
        elif boundary.status == "watch":
            branch_id = "watch_boundary"
        elif commitment.status == "watch":
            branch_id = "watch_commitment"
        elif (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        ):
            branch_id = "watch_segmented"
        else:
            branch_id = "watch_clarity"
        branch = _phase2_branch("disclosure", "branches", branch_id)
        target = branch.get("target", "clarity_buffered_disclosure_watch")
        trigger = branch.get("trigger", "clarity_disclosure_watch")
        if note := branch.get("note"):
            notes.append(note)
    else:
        status = "pass"
        branch = _phase2_branch("disclosure", "branches", branch_id)
        target = branch.get("target", "steady_transparent_disclosure")
        trigger = branch.get("trigger", "disclosure_line_stable")

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        trajectory_branch_id = {
            "revise_filtered_context": "recenter_filtered_context",
            "revise_boundary": "recenter_boundary",
        }.get(branch_id, "recenter_uncertainty")
        branch = _phase2_branch("disclosure", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "uncertainty_disclosure_recenter")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    elif status == "watch":
        trajectory_status = "watch"
        trajectory_branch_id = {
            "watch_clarification": "watch_clarification",
            "watch_uncertainty": "watch_uncertainty",
            "watch_boundary": "watch_boundary",
            "watch_commitment": "watch_commitment",
            "watch_segmented": "watch_segmented",
            "watch_clarity": "watch_clarity",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch("disclosure", "trajectory_branches", trajectory_branch_id)
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "disclosure_watch_active")
        if note := branch.get("note"):
            trajectory_notes.append(note)
    else:
        trajectory_status = "stable"
        branch = _phase2_branch("disclosure", "trajectory_branches", "stable")
        trajectory_target = branch.get("target", target)
        trajectory_trigger = branch.get("trigger", "disclosure_governance_stable")
        if note := branch.get("note"):
            trajectory_notes.append(note)

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_reciprocity_governance(
    *,
    prelude: _System3Prelude,
    dependency: _GovernanceOutcome,
    support: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
) -> _GovernanceOutcome:
    reciprocity_state = _build_reciprocity_governance_state(
        prelude=prelude,
        dependency=dependency,
        support=support,
        autonomy=autonomy,
        commitment=commitment,
    )
    status = str(reciprocity_state["status"])
    target = str(reciprocity_state["target"])
    trigger = str(reciprocity_state["trigger"])
    notes = list(reciprocity_state["notes"])
    branch_id = str(reciprocity_state["branch_id"])
    reciprocity_trajectory = _build_reciprocity_governance_trajectory(
        branch_id=branch_id,
        status=status,
        target=target,
    )
    trajectory_status = str(reciprocity_trajectory["trajectory_status"])
    trajectory_target = str(reciprocity_trajectory["trajectory_target"])
    trajectory_trigger = str(reciprocity_trajectory["trajectory_trigger"])
    trajectory_notes = list(reciprocity_trajectory["trajectory_notes"])

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_reciprocity_governance_state(
    *,
    prelude: _System3Prelude,
    dependency: _GovernanceOutcome,
    support: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
) -> dict[str, object]:
    line = "reciprocity"
    reciprocity_score = float(prelude.relationship_state.r_vector.get("reciprocity", 0.5))
    if dependency.status == "revise":
        branch_id = "revise_dependency"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "bounded_nonexclusive_reciprocity"),
            "trigger": branch.get("trigger", "dependency_reciprocity_recenter"),
            "notes": [
                branch.get(
                    "note", "dependency_recenter_requires_explicitly_nonexclusive_reciprocity"
                )
            ],
        }
    if prelude.emotional_debt_status == "elevated":
        branch_id = "revise_debt"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "decompression_before_reciprocity_push"),
            "trigger": branch.get("trigger", "debt_reciprocity_recenter"),
            "notes": [
                branch.get("note", "elevated_debt_requires_decompression_before_reciprocity_push")
            ],
        }
    if support.status == "revise":
        branch_id = "revise_support"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "user_led_reciprocity_reset"),
            "trigger": branch.get("trigger", "support_reciprocity_recenter"),
            "notes": [branch.get("note", "support_recenter_requires_user_led_reciprocity_reset")],
        }
    if reciprocity_score <= 0.36 and commitment.status in {"watch", "revise"}:
        branch_id = "revise_low_reciprocity"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "expectation_reset_before_reciprocity_push"),
            "trigger": branch.get("trigger", "low_reciprocity_recenter"),
            "notes": [
                branch.get(
                    "note", "low_reciprocity_plus_commitment_pressure_requires_expectation_reset"
                )
            ],
        }
    if (
        reciprocity_score < 0.48
        or prelude.emotional_debt_status == "watch"
        or support.status == "watch"
        or autonomy.status == "watch"
        or commitment.status == "watch"
        or prelude.expectation_calibration_status == "watch"
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        if reciprocity_score < 0.48:
            branch_id = "watch_low_reciprocity"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "lightweight_reciprocity_watch"),
                "trigger": branch.get("trigger", "low_reciprocity_watch"),
                "notes": [
                    branch.get("note", "low_reciprocity_keeps_line_lightweight_and_low_pressure")
                ],
            }
        if prelude.emotional_debt_status == "watch":
            branch_id = "watch_debt"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "debt_buffered_reciprocity_watch"),
                "trigger": branch.get("trigger", "debt_reciprocity_watch"),
                "notes": [branch.get("note", "debt_watch_keeps_reciprocity_line_buffered")],
            }
        if support.status == "watch":
            branch_id = "watch_support"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "low_pressure_reciprocity_watch"),
                "trigger": branch.get("trigger", "support_reciprocity_watch"),
                "notes": [branch.get("note", "support_watch_keeps_reciprocity_line_low_pressure")],
            }
        if autonomy.status == "watch":
            branch_id = "watch_autonomy"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "user_led_reciprocity_watch"),
                "trigger": branch.get("trigger", "autonomy_reciprocity_watch"),
                "notes": [branch.get("note", "autonomy_watch_keeps_reciprocity_line_user_led")],
            }
        if commitment.status == "watch":
            branch_id = "watch_commitment"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "bounded_reciprocity_watch"),
                "trigger": branch.get("trigger", "commitment_reciprocity_watch"),
                "notes": [branch.get("note", "commitment_watch_keeps_reciprocity_line_bounded")],
            }
        if prelude.expectation_calibration_status == "watch":
            branch_id = "watch_expectation"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "expectation_buffered_reciprocity_watch"),
                "trigger": branch.get("trigger", "expectation_reciprocity_watch"),
                "notes": [
                    branch.get(
                        "note", "expectation_watch_keeps_reciprocity_line_explicitly_bounded"
                    )
                ],
            }
        branch_id = "watch_segmented"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "stepwise_reciprocity_watch"),
            "trigger": branch.get("trigger", "segmented_reciprocity_watch"),
            "notes": [branch.get("note", "segmented_delivery_keeps_reciprocity_line_stepwise")],
        }
    branch_id = "pass"
    branch = _phase2_branch(line, "branches", branch_id)
    return {
        "status": "pass",
        "branch_id": branch_id,
        "target": branch.get("target", "steady_mutual_reciprocity"),
        "trigger": branch.get("trigger", "reciprocity_line_stable"),
        "notes": [],
    }


def _build_reciprocity_governance_trajectory(
    *,
    branch_id: str,
    status: str,
    target: str,
) -> dict[str, object]:
    line = "reciprocity"
    if status == "revise":
        trajectory_branch_id = {
            "revise_dependency": "recenter_dependency",
            "revise_debt": "recenter_debt",
            "revise_support": "recenter_support",
        }.get(branch_id, "recenter_low_reciprocity")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "recenter",
            "trajectory_target": branch.get("target", "expectation_reset_before_reciprocity_push"),
            "trajectory_trigger": branch.get("trigger", "low_reciprocity_recenter"),
            "trajectory_notes": [
                branch.get("note", "low_reciprocity_keeps_line_in_expectation_reset_mode")
            ],
        }
    if status == "watch":
        trajectory_branch_id = {
            "watch_low_reciprocity": "watch_low_reciprocity",
            "watch_debt": "watch_debt",
            "watch_support": "watch_support",
            "watch_autonomy": "watch_autonomy",
            "watch_commitment": "watch_commitment",
            "watch_expectation": "watch_expectation",
            "watch_segmented": "watch_segmented",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "watch",
            "trajectory_target": branch.get("target", target),
            "trajectory_trigger": branch.get("trigger", "reciprocity_watch_active"),
            "trajectory_notes": [
                branch.get("note", "reciprocity_line_is_shifting_without_full_recenter")
            ],
        }
    branch = _phase2_branch(line, "trajectory_branches", "stable")
    return {
        "trajectory_status": "stable",
        "trajectory_target": branch.get("target", "steady_mutual_reciprocity"),
        "trajectory_trigger": branch.get("trigger", "reciprocity_governance_stable"),
        "trajectory_notes": [branch.get("note", "reciprocity_line_is_holding_stable_and_mutual")],
    }


def _build_pressure_governance(
    *,
    prelude: _System3Prelude,
    repair: _GovernanceOutcome,
    dependency: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    boundary: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    support: _GovernanceOutcome,
    attunement: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
) -> _GovernanceOutcome:
    pressure_state = _build_pressure_governance_state(
        prelude=prelude,
        repair=repair,
        dependency=dependency,
        autonomy=autonomy,
        boundary=boundary,
        pacing=pacing,
        support=support,
        attunement=attunement,
        trust=trust,
        commitment=commitment,
    )
    status = str(pressure_state["status"])
    target = str(pressure_state["target"])
    trigger = str(pressure_state["trigger"])
    notes = list(pressure_state["notes"])
    branch_id = str(pressure_state["branch_id"])
    pressure_trajectory = _build_pressure_governance_trajectory(
        branch_id=branch_id,
        status=status,
        target=target,
    )
    trajectory_status = str(pressure_trajectory["trajectory_status"])
    trajectory_target = str(pressure_trajectory["trajectory_target"])
    trajectory_trigger = str(pressure_trajectory["trajectory_trigger"])
    trajectory_notes = list(pressure_trajectory["trajectory_notes"])

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_pressure_governance_state(
    *,
    prelude: _System3Prelude,
    repair: _GovernanceOutcome,
    dependency: _GovernanceOutcome,
    autonomy: _GovernanceOutcome,
    boundary: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    support: _GovernanceOutcome,
    attunement: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
) -> dict[str, object]:
    line = "pressure"
    if prelude.emotional_debt_status == "elevated":
        branch_id = "revise_debt"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "decompression_before_pressure_push"),
            "trigger": branch.get("trigger", "debt_pressure_recenter"),
            "notes": [
                branch.get(
                    "note", "elevated_debt_requires_decompression_before_extra_relational_pressure"
                )
            ],
        }
    if repair.status == "revise":
        branch_id = "revise_repair"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "repair_first_pressure_reset"),
            "trigger": branch.get("trigger", "repair_pressure_recenter"),
            "notes": [
                branch.get("note", "repair_recenter_requires_pressure_reset_before_forward_motion")
            ],
        }
    if dependency.status == "revise":
        branch_id = "revise_dependency"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "dependency_safe_pressure_reset"),
            "trigger": branch.get("trigger", "dependency_pressure_recenter"),
            "notes": [
                branch.get("note", "dependency_recenter_requires_nonexclusive_low_pressure_support")
            ],
        }
    if autonomy.status == "revise":
        branch_id = "revise_autonomy"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "explicit_user_space_pressure_reset"),
            "trigger": branch.get("trigger", "autonomy_pressure_recenter"),
            "notes": [
                branch.get(
                    "note", "autonomy_recenter_requires_explicit_user_space_before_more_pressure"
                )
            ],
        }
    if boundary.status == "revise":
        branch_id = "revise_boundary"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "hard_boundary_pressure_reset"),
            "trigger": branch.get("trigger", "boundary_pressure_recenter"),
            "notes": [
                branch.get("note", "boundary_recenter_requires_pressure_reset_and clearer spacing")
            ],
        }
    if (
        pacing.status == "watch"
        or support.status == "watch"
        or attunement.status == "watch"
        or trust.status == "watch"
        or commitment.status == "watch"
        or (
            prelude.response_sequence_plan is not None
            and prelude.response_sequence_plan.mode == "two_part_sequence"
        )
    ):
        if pacing.status == "watch":
            branch_id = "watch_pacing"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "slow_pressure_watch"),
                "trigger": branch.get("trigger", "pacing_pressure_watch"),
                "notes": [
                    branch.get("note", "pacing_watch_keeps_pressure_line_slow_and_proportionate")
                ],
            }
        if support.status == "watch":
            branch_id = "watch_support"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "bounded_support_pressure_watch"),
                "trigger": branch.get("trigger", "support_pressure_watch"),
                "notes": [
                    branch.get("note", "support_watch_keeps_pressure_line_low_pressure_and_bounded")
                ],
            }
        if attunement.status == "watch":
            branch_id = "watch_attunement"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "attunement_sensitive_pressure_watch"),
                "trigger": branch.get("trigger", "attunement_pressure_watch"),
                "notes": [
                    branch.get(
                        "note", "attunement_watch_keeps_pressure_line_more responsive and gentle"
                    )
                ],
            }
        if trust.status == "watch":
            branch_id = "watch_trust"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "relational_safety_pressure_watch"),
                "trigger": branch.get("trigger", "trust_pressure_watch"),
                "notes": [
                    branch.get(
                        "note", "trust_watch_keeps_pressure_line_safety_first_and_low_pressure"
                    )
                ],
            }
        if commitment.status == "watch":
            branch_id = "watch_commitment"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "bounded_commitment_pressure_watch"),
                "trigger": branch.get("trigger", "commitment_pressure_watch"),
                "notes": [
                    branch.get("note", "commitment_watch_keeps_pressure_line_explicitly_bounded")
                ],
            }
        branch_id = "watch_segmented"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "stepwise_pressure_watch"),
            "trigger": branch.get("trigger", "segmented_pressure_watch"),
            "notes": [
                branch.get(
                    "note", "segmented_delivery_keeps_pressure_line_stepwise_and_nonstacking"
                )
            ],
        }
    branch_id = "pass"
    branch = _phase2_branch(line, "branches", branch_id)
    return {
        "status": "pass",
        "branch_id": branch_id,
        "target": branch.get("target", "steady_low_pressure_support"),
        "trigger": branch.get("trigger", "pressure_line_stable"),
        "notes": [],
    }


def _build_pressure_governance_trajectory(
    *,
    branch_id: str,
    status: str,
    target: str,
) -> dict[str, object]:
    line = "pressure"
    if status == "revise":
        trajectory_branch_id = {
            "revise_debt": "recenter_debt",
            "revise_repair": "recenter_repair",
            "revise_dependency": "recenter_dependency",
            "revise_autonomy": "recenter_autonomy",
        }.get(branch_id, "recenter_boundary")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "recenter",
            "trajectory_target": branch.get("target", "hard_boundary_pressure_reset"),
            "trajectory_trigger": branch.get("trigger", "boundary_pressure_recenter"),
            "trajectory_notes": [
                branch.get("note", "boundary_pressure_keeps_pressure_line_in_explicit_reset_mode")
            ],
        }
    if status == "watch":
        trajectory_branch_id = {
            "watch_pacing": "watch_pacing",
            "watch_support": "watch_support",
            "watch_attunement": "watch_attunement",
            "watch_trust": "watch_trust",
            "watch_commitment": "watch_commitment",
            "watch_segmented": "watch_segmented",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "watch",
            "trajectory_target": branch.get("target", target),
            "trajectory_trigger": branch.get("trigger", "pressure_watch_active"),
            "trajectory_notes": [
                branch.get("note", "pressure_line_is_shifting_without_full_recenter")
            ],
        }
    branch = _phase2_branch(line, "trajectory_branches", "stable")
    return {
        "trajectory_status": "stable",
        "trajectory_target": branch.get("target", "steady_low_pressure_support"),
        "trajectory_trigger": branch.get("trigger", "pressure_governance_stable"),
        "trajectory_notes": [
            branch.get("note", "pressure_line_is_holding_stable_and_proportionate")
        ],
    }


def _build_relational_governance(
    *,
    support: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    clarity: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
    disclosure: _GovernanceOutcome,
    reciprocity: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    boundary: _GovernanceOutcome,
) -> _GovernanceOutcome:
    relational_state = _build_relational_governance_state(
        support=support,
        continuity=continuity,
        repair=repair,
        trust=trust,
        clarity=clarity,
        pacing=pacing,
        commitment=commitment,
        disclosure=disclosure,
        reciprocity=reciprocity,
        pressure=pressure,
        boundary=boundary,
    )
    status = str(relational_state["status"])
    target = str(relational_state["target"])
    trigger = str(relational_state["trigger"])
    notes = list(relational_state["notes"])
    branch_id = str(relational_state["branch_id"])
    relational_trajectory = _build_relational_governance_trajectory(
        branch_id=branch_id,
        status=status,
    )
    trajectory_status = str(relational_trajectory["trajectory_status"])
    trajectory_target = str(relational_trajectory["trajectory_target"])
    trajectory_trigger = str(relational_trajectory["trajectory_trigger"])
    trajectory_notes = list(relational_trajectory["trajectory_notes"])

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_relational_governance_state(
    *,
    support: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    clarity: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
    disclosure: _GovernanceOutcome,
    reciprocity: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    boundary: _GovernanceOutcome,
) -> dict[str, object]:
    line = "relational"
    watch_count = sum(
        1
        for status in (
            support.status,
            continuity.status,
            repair.status,
            trust.status,
            clarity.status,
            pacing.status,
            commitment.status,
            disclosure.status,
            reciprocity.status,
            pressure.status,
        )
        if status == "watch"
    )
    if boundary.status == "revise":
        branch_id = "revise_boundary"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "boundary_safe_relational_reset"),
            "trigger": branch.get("trigger", "boundary_relational_recenter"),
            "notes": [
                branch.get("note", "boundary_recenter_requires_relational_reset_before_progress")
            ],
        }
    if trust.status == "revise":
        branch_id = "revise_trust"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "trust_repair_relational_reset"),
            "trigger": branch.get("trigger", "trust_relational_recenter"),
            "notes": [
                branch.get(
                    "note", "trust_recenter_requires_relational_repair_before_forward motion"
                )
            ],
        }
    if pressure.status == "revise":
        branch_id = "revise_pressure"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "low_pressure_relational_reset"),
            "trigger": branch.get("trigger", "pressure_relational_recenter"),
            "notes": [
                branch.get("note", "pressure_recenter_requires_relational_reset_and_more space")
            ],
        }
    if repair.status == "revise":
        branch_id = "revise_repair"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "repair_first_relational_reset"),
            "trigger": branch.get("trigger", "repair_relational_recenter"),
            "notes": [
                branch.get(
                    "note", "repair_recenter_requires_relational_reset_before renewed progress"
                )
            ],
        }
    if continuity.status == "revise":
        branch_id = "revise_continuity"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "reanchor_before_relational_progress"),
            "trigger": branch.get("trigger", "continuity_relational_recenter"),
            "notes": [
                branch.get(
                    "note", "continuity_recenter_requires_reanchor_before_relational_progress"
                )
            ],
        }
    if support.status == "revise":
        branch_id = "revise_support"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "bounded_support_relational_reset"),
            "trigger": branch.get("trigger", "support_relational_recenter"),
            "notes": [branch.get("note", "support_recenter_requires_bounded_relational_reset")],
        }
    if (
        watch_count >= 4
        or trust.status == "watch"
        or pressure.status == "watch"
        or continuity.status == "watch"
        or repair.status == "watch"
        or support.status == "watch"
    ):
        if trust.status == "watch":
            branch_id = "watch_trust"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "trust_buffered_relational_watch"),
                "trigger": branch.get("trigger", "trust_relational_watch"),
                "notes": [branch.get("note", "trust_watch_keeps_relational_line_safety_buffered")],
            }
        if pressure.status == "watch":
            branch_id = "watch_pressure"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "low_pressure_relational_watch"),
                "trigger": branch.get("trigger", "pressure_relational_watch"),
                "notes": [
                    branch.get(
                        "note", "pressure_watch_keeps_relational_line_low pressure and spacious"
                    )
                ],
            }
        if continuity.status == "watch":
            branch_id = "watch_continuity"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "reanchored_relational_watch"),
                "trigger": branch.get("trigger", "continuity_relational_watch"),
                "notes": [branch.get("note", "continuity_watch_keeps_relational_line_reanchored")],
            }
        if repair.status == "watch":
            branch_id = "watch_repair"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "repair_buffered_relational_watch"),
                "trigger": branch.get("trigger", "repair_relational_watch"),
                "notes": [
                    branch.get("note", "repair_watch_keeps_relational_line_buffered and slow")
                ],
            }
        if support.status == "watch":
            branch_id = "watch_support"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "bounded_support_relational_watch"),
                "trigger": branch.get("trigger", "support_relational_watch"),
                "notes": [
                    branch.get("note", "support_watch_keeps_relational_line bounded and user led")
                ],
            }
        branch_id = "watch_default"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "multi_signal_relational_watch"),
            "trigger": branch.get("trigger", "relational_watch_active"),
            "notes": [
                branch.get("note", "multiple_relational_watch_signals_keep_the_line_under review")
            ],
        }
    branch_id = "pass"
    branch = _phase2_branch(line, "branches", branch_id)
    return {
        "status": "pass",
        "branch_id": branch_id,
        "target": branch.get("target", "steady_bounded_relational_progress"),
        "trigger": branch.get("trigger", "relational_line_stable"),
        "notes": [],
    }


def _build_relational_governance_trajectory(
    *,
    branch_id: str,
    status: str,
) -> dict[str, object]:
    line = "relational"
    if status == "revise":
        trajectory_branch_id = {
            "revise_boundary": "recenter_boundary",
            "revise_trust": "recenter_trust",
            "revise_pressure": "recenter_pressure",
            "revise_repair": "recenter_repair",
            "revise_continuity": "recenter_continuity",
        }.get(branch_id, "recenter_support")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "recenter",
            "trajectory_target": branch.get("target", "bounded_support_relational_reset"),
            "trajectory_trigger": branch.get("trigger", "support_relational_recenter"),
            "trajectory_notes": [
                branch.get("note", "support_pressure_keeps_relational_line in bounded reset mode")
            ],
        }
    if status == "watch":
        trajectory_branch_id = {
            "watch_trust": "watch_trust",
            "watch_pressure": "watch_pressure",
            "watch_continuity": "watch_continuity",
            "watch_repair": "watch_repair",
            "watch_support": "watch_support",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "watch",
            "trajectory_target": branch.get("target", "multi_signal_relational_watch"),
            "trajectory_trigger": branch.get("trigger", "relational_watch_active"),
            "trajectory_notes": [
                branch.get("note", "multiple_signals_keep_relational_line_under watch")
            ],
        }
    branch = _phase2_branch(line, "trajectory_branches", "stable")
    return {
        "trajectory_status": "stable",
        "trajectory_target": branch.get("target", "steady_bounded_relational_progress"),
        "trajectory_trigger": branch.get("trigger", "relational_governance_stable"),
        "trajectory_notes": [branch.get("note", "relational_line_is_holding_stable_and_bounded")],
    }


def _build_safety_governance(
    *,
    boundary: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    clarity: _GovernanceOutcome,
    disclosure: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    relational: _GovernanceOutcome,
) -> _GovernanceOutcome:
    safety_state = _build_safety_governance_state(
        boundary=boundary,
        trust=trust,
        clarity=clarity,
        disclosure=disclosure,
        pressure=pressure,
        continuity=continuity,
        repair=repair,
        relational=relational,
    )
    status = str(safety_state["status"])
    target = str(safety_state["target"])
    trigger = str(safety_state["trigger"])
    notes = list(safety_state["notes"])
    branch_id = str(safety_state["branch_id"])
    safety_trajectory = _build_safety_governance_trajectory(branch_id=branch_id, status=status)
    trajectory_status = str(safety_trajectory["trajectory_status"])
    trajectory_target = str(safety_trajectory["trajectory_target"])
    trajectory_trigger = str(safety_trajectory["trajectory_trigger"])
    trajectory_notes = list(safety_trajectory["trajectory_notes"])

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_safety_governance_state(
    *,
    boundary: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    clarity: _GovernanceOutcome,
    disclosure: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    relational: _GovernanceOutcome,
) -> dict[str, object]:
    line = "safety"
    watch_count = sum(
        1
        for status in (
            boundary.status,
            trust.status,
            clarity.status,
            disclosure.status,
            pressure.status,
            continuity.status,
            repair.status,
            relational.status,
        )
        if status == "watch"
    )
    notes: list[str] = []
    if boundary.status == "revise":
        branch_id = "revise_boundary"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "hard_boundary_safety_reset"),
            "trigger": branch.get("trigger", "boundary_safety_recenter"),
            "notes": [
                branch.get("note", "boundary_recenter_requires_a_hard_safety_reset_before_progress")
            ],
        }
    if trust.status == "revise":
        branch_id = "revise_trust"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "trust_repair_safety_reset"),
            "trigger": branch.get("trigger", "trust_safety_recenter"),
            "notes": [
                branch.get("note", "trust_recenter_requires_safety_buffering_and_repair_first")
            ],
        }
    if disclosure.status == "revise":
        branch_id = "revise_disclosure"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "explicit_uncertainty_safety_reset"),
            "trigger": branch.get("trigger", "disclosure_safety_recenter"),
            "notes": [
                branch.get(
                    "note", "disclosure_recenter_requires_explicit_uncertainty_and_tighter_bounds"
                )
            ],
        }
    if clarity.status == "revise":
        branch_id = "revise_clarity"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "reanchor_before_safety_progress"),
            "trigger": branch.get("trigger", "clarity_safety_recenter"),
            "notes": [
                branch.get("note", "clarity_recenter_requires_reanchoring_before_further_progress")
            ],
        }
    if pressure.status == "revise":
        branch_id = "revise_pressure"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "low_pressure_safety_reset"),
            "trigger": branch.get("trigger", "pressure_safety_recenter"),
            "notes": [
                branch.get(
                    "note", "pressure_recenter_requires_low_pressure_support_before_any_push"
                )
            ],
        }
    if relational.status == "revise":
        branch_id = "revise_relational"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "bounded_relational_safety_reset"),
            "trigger": branch.get("trigger", "relational_safety_recenter"),
            "notes": [
                branch.get(
                    "note", "relational_recenter_requires_bounded_safety_reset_before_resuming"
                )
            ],
        }
    if (
        watch_count >= 4
        or boundary.status == "watch"
        or trust.status == "watch"
        or disclosure.status == "watch"
        or clarity.status == "watch"
        or pressure.status == "watch"
        or relational.status == "watch"
    ):
        if boundary.status == "watch":
            branch_id = "watch_boundary"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "boundary_buffered_safety_watch"),
                "trigger": branch.get("trigger", "boundary_safety_watch"),
                "notes": [
                    branch.get("note", "boundary_watch_keeps_the_safety_line_explicit_and_buffered")
                ],
            }
        if trust.status == "watch":
            branch_id = "watch_trust"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "trust_buffered_safety_watch"),
                "trigger": branch.get("trigger", "trust_safety_watch"),
                "notes": [
                    branch.get("note", "trust_watch_keeps_the_safety_line_careful_and_buffered")
                ],
            }
        if disclosure.status == "watch":
            branch_id = "watch_disclosure"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "uncertainty_first_safety_watch"),
                "trigger": branch.get("trigger", "disclosure_safety_watch"),
                "notes": [
                    branch.get("note", "disclosure_watch_keeps_the_safety_line_uncertainty_first")
                ],
            }
        if clarity.status == "watch":
            branch_id = "watch_clarity"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "reanchored_safety_watch"),
                "trigger": branch.get("trigger", "clarity_safety_watch"),
                "notes": [
                    branch.get(
                        "note", "clarity_watch_keeps_the_safety_line_reanchored_and_scaffolded"
                    )
                ],
            }
        if pressure.status == "watch":
            branch_id = "watch_pressure"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "low_pressure_safety_watch"),
                "trigger": branch.get("trigger", "pressure_safety_watch"),
                "notes": [
                    branch.get(
                        "note", "pressure_watch_keeps_the_safety_line_low_pressure_and_spacious"
                    )
                ],
            }
        if relational.status == "watch":
            branch_id = "watch_relational"
            branch = _phase2_branch(line, "branches", branch_id)
            return {
                "status": "watch",
                "branch_id": branch_id,
                "target": branch.get("target", "bounded_relational_safety_watch"),
                "trigger": branch.get("trigger", "relational_safety_watch"),
                "notes": [
                    branch.get(
                        "note", "relational_watch_keeps_the_safety_line_bounded_and_deliberate"
                    )
                ],
            }
        branch_id = "watch_default"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "multi_signal_safety_watch"),
            "trigger": branch.get("trigger", "safety_watch_active"),
            "notes": [branch.get("note", "multiple_signals_keep_the_safety_line_under_review")],
        }
    branch_id = "pass"
    branch = _phase2_branch(line, "branches", branch_id)
    return {
        "status": "pass",
        "branch_id": branch_id,
        "target": branch.get("target", "steady_safe_relational_support"),
        "trigger": branch.get("trigger", "safety_line_stable"),
        "notes": notes,
    }


def _build_safety_governance_trajectory(
    *,
    branch_id: str,
    status: str,
) -> dict[str, object]:
    line = "safety"
    if status == "revise":
        trajectory_branch_id = {
            "revise_boundary": "recenter_boundary",
            "revise_trust": "recenter_trust",
            "revise_disclosure": "recenter_disclosure",
            "revise_clarity": "recenter_clarity",
            "revise_pressure": "recenter_pressure",
        }.get(branch_id, "recenter_relational")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "recenter",
            "trajectory_target": branch.get("target", "bounded_relational_safety_reset"),
            "trajectory_trigger": branch.get("trigger", "relational_safety_recenter"),
            "trajectory_notes": [
                branch.get("note", "relational_drift_keeps_the_safety_line_in_bounded_reset_mode")
            ],
        }
    if status == "watch":
        trajectory_branch_id = {
            "watch_boundary": "watch_boundary",
            "watch_trust": "watch_trust",
            "watch_disclosure": "watch_disclosure",
            "watch_clarity": "watch_clarity",
            "watch_pressure": "watch_pressure",
            "watch_relational": "watch_relational",
        }.get(branch_id, "watch_default")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "watch",
            "trajectory_target": branch.get("target", "multi_signal_safety_watch"),
            "trajectory_trigger": branch.get("trigger", "safety_watch_active"),
            "trajectory_notes": [
                branch.get("note", "multiple_signals_keep_the_safety_line_under_watch")
            ],
        }
    branch = _phase2_branch(line, "trajectory_branches", "stable")
    return {
        "trajectory_status": "stable",
        "trajectory_target": branch.get("target", "steady_safe_relational_support"),
        "trajectory_trigger": branch.get("trigger", "safety_governance_stable"),
        "trajectory_notes": [branch.get("note", "safety_line_is_holding_stable_and_bounded")],
    }


def _build_progress_governance(
    *,
    safety: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    commitment: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    growth_transition_status: str,
    expectation_calibration_status: str,
) -> _GovernanceOutcome:
    notes: list[str] = []
    if safety.status == "revise":
        status = "revise"
        target = "safety_reset_before_progress"
        trigger = "safety_progress_recenter"
        notes.append("safety_recenter_requires_resetting_progress_before_any_forward_push")
    elif pressure.status == "revise":
        status = "revise"
        target = "decompression_before_progress"
        trigger = "pressure_progress_recenter"
        notes.append("pressure_recenter_requires_decompression_before_more_progress")
    elif continuity.status == "revise":
        status = "revise"
        target = "reanchor_before_progress"
        trigger = "continuity_progress_recenter"
        notes.append("continuity_recenter_requires_reanchoring_before_more_progress")
    elif commitment.status == "revise":
        status = "revise"
        target = "bounded_commitment_before_progress"
        trigger = "commitment_progress_recenter"
        notes.append("commitment_recenter_requires_bounded_nonpressured_progress")
    elif expectation_calibration_status == "revise":
        status = "revise"
        target = "expectation_reset_before_progress"
        trigger = "expectation_progress_recenter"
        notes.append("expectation_recenter_requires_resetting_progress_promises")
    elif growth_transition_status == "redirect":
        status = "revise"
        target = "repairing_before_progress"
        trigger = "growth_progress_recenter"
        notes.append("growth_redirect_requires_repairing_before_more_progress")
    elif (
        growth_transition_status == "watch"
        or safety.status == "watch"
        or pacing.status == "watch"
        or continuity.status == "watch"
        or commitment.status == "watch"
        or expectation_calibration_status == "watch"
    ):
        status = "watch"
        if growth_transition_status == "watch":
            target = "growth_buffered_progress_watch"
            trigger = "growth_progress_watch"
            notes.append("growth_watch_keeps_progress_line_buffered_and stage-aware")
        elif safety.status == "watch":
            target = "safety_buffered_progress_watch"
            trigger = "safety_progress_watch"
            notes.append("safety_watch_keeps_progress_line_more bounded and careful")
        elif pacing.status == "watch":
            target = "slow_progress_watch"
            trigger = "pacing_progress_watch"
            notes.append("pacing_watch_keeps_progress_line deliberately slow")
        elif continuity.status == "watch":
            target = "reanchored_progress_watch"
            trigger = "continuity_progress_watch"
            notes.append("continuity_watch_keeps_progress_line reanchored before advancing")
        elif commitment.status == "watch":
            target = "bounded_progress_watch"
            trigger = "commitment_progress_watch"
            notes.append("commitment_watch_keeps_progress_line explicitly bounded")
        else:
            target = "expectation_buffered_progress_watch"
            trigger = "expectation_progress_watch"
            notes.append("expectation_watch_keeps_progress_line softly calibrated")
    else:
        status = "pass"
        target = "steady_bounded_progress"
        trigger = "progress_line_stable"

    trajectory_notes: list[str] = []
    if status == "revise":
        trajectory_status = "recenter"
        if trigger == "safety_progress_recenter":
            trajectory_target = "safety_reset_before_progress"
            trajectory_trigger = "safety_progress_recenter"
            trajectory_notes.append("safety_recenter_keeps_progress_line_in_reset_mode")
        elif trigger == "pressure_progress_recenter":
            trajectory_target = "decompression_before_progress"
            trajectory_trigger = "pressure_progress_recenter"
            trajectory_notes.append("pressure_recenter_keeps_progress_line_in_decompression_mode")
        elif trigger == "continuity_progress_recenter":
            trajectory_target = "reanchor_before_progress"
            trajectory_trigger = "continuity_progress_recenter"
            trajectory_notes.append("continuity_recenter_keeps_progress_line_in_reanchor_mode")
        elif trigger == "commitment_progress_recenter":
            trajectory_target = "bounded_commitment_before_progress"
            trajectory_trigger = "commitment_progress_recenter"
            trajectory_notes.append("commitment_recenter_keeps_progress_line_bounded")
        elif trigger == "expectation_progress_recenter":
            trajectory_target = "expectation_reset_before_progress"
            trajectory_trigger = "expectation_progress_recenter"
            trajectory_notes.append("expectation_recenter_keeps_progress_line_in_reset_mode")
        else:
            trajectory_target = "repairing_before_progress"
            trajectory_trigger = "growth_progress_recenter"
            trajectory_notes.append("growth_redirect_keeps_progress_line_repair_first")
    elif status == "watch":
        trajectory_status = "watch"
        if trigger == "growth_progress_watch":
            trajectory_target = "growth_buffered_progress_watch"
            trajectory_trigger = "growth_progress_watch"
            trajectory_notes.append("growth_watch_keeps_progress_line_buffered")
        elif trigger == "safety_progress_watch":
            trajectory_target = "safety_buffered_progress_watch"
            trajectory_trigger = "safety_progress_watch"
            trajectory_notes.append("safety_watch_keeps_progress_line_careful")
        elif trigger == "pacing_progress_watch":
            trajectory_target = "slow_progress_watch"
            trajectory_trigger = "pacing_progress_watch"
            trajectory_notes.append("pacing_watch_keeps_progress_line_slow")
        elif trigger == "continuity_progress_watch":
            trajectory_target = "reanchored_progress_watch"
            trajectory_trigger = "continuity_progress_watch"
            trajectory_notes.append("continuity_watch_keeps_progress_line_reanchored")
        elif trigger == "commitment_progress_watch":
            trajectory_target = "bounded_progress_watch"
            trajectory_trigger = "commitment_progress_watch"
            trajectory_notes.append("commitment_watch_keeps_progress_line_bounded")
        else:
            trajectory_target = "expectation_buffered_progress_watch"
            trajectory_trigger = "expectation_progress_watch"
            trajectory_notes.append("expectation_watch_keeps_progress_line_calibrated")
    else:
        trajectory_status = "stable"
        trajectory_target = "steady_bounded_progress"
        trajectory_trigger = "progress_governance_stable"
        trajectory_notes.append("progress_line_is_holding_steady_and_bounded")

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_stability_governance(
    *,
    safety: _GovernanceOutcome,
    relational: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    progress: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    attunement: _GovernanceOutcome,
) -> _GovernanceOutcome:
    stability_state = _build_stability_governance_state(
        safety=safety,
        relational=relational,
        pressure=pressure,
        trust=trust,
        continuity=continuity,
        repair=repair,
        progress=progress,
        pacing=pacing,
        attunement=attunement,
    )
    status = str(stability_state["status"])
    target = str(stability_state["target"])
    trigger = str(stability_state["trigger"])
    notes = list(stability_state["notes"])
    branch_id = str(stability_state["branch_id"])
    stability_trajectory = _build_stability_governance_trajectory(
        branch_id=branch_id,
        status=status,
    )
    trajectory_status = str(stability_trajectory["trajectory_status"])
    trajectory_target = str(stability_trajectory["trajectory_target"])
    trajectory_trigger = str(stability_trajectory["trajectory_trigger"])
    trajectory_notes = list(stability_trajectory["trajectory_notes"])

    return _GovernanceOutcome(
        status=status,
        target=target,
        trigger=trigger,
        notes=notes,
        trajectory_status=trajectory_status,
        trajectory_target=trajectory_target,
        trajectory_trigger=trajectory_trigger,
        trajectory_notes=trajectory_notes,
    )


def _build_stability_governance_state(
    *,
    safety: _GovernanceOutcome,
    relational: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    progress: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    attunement: _GovernanceOutcome,
) -> dict[str, object]:
    recenter_state = _build_stability_recenter_state(
        safety=safety,
        relational=relational,
        pressure=pressure,
        trust=trust,
        continuity=continuity,
        repair=repair,
        progress=progress,
    )
    if recenter_state is not None:
        return recenter_state
    watch_state = _build_stability_watch_state(
        safety=safety,
        relational=relational,
        trust=trust,
        continuity=continuity,
        repair=repair,
        progress=progress,
        pacing=pacing,
        attunement=attunement,
    )
    if watch_state is not None:
        return watch_state
    branch_id = "pass"
    branch = _phase2_branch("stability", "branches", branch_id)
    return {
        "status": "pass",
        "branch_id": branch_id,
        "target": branch.get("target", "steady_bounded_relational_stability"),
        "trigger": branch.get("trigger", "stability_line_stable"),
        "notes": [],
    }


def _build_stability_recenter_state(
    *,
    safety: _GovernanceOutcome,
    relational: _GovernanceOutcome,
    pressure: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    progress: _GovernanceOutcome,
) -> dict[str, object] | None:
    line = "stability"
    if safety.status == "revise":
        branch_id = "revise_safety"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "safety_reset_before_stability"),
            "trigger": branch.get("trigger", "safety_stability_recenter"),
            "notes": [
                branch.get(
                    "note",
                    "safety_recenter_requires_resetting_relational_stability_before_progress",
                )
            ],
        }
    if relational.status == "revise":
        branch_id = "revise_relational"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "relational_reset_before_stability"),
            "trigger": branch.get("trigger", "relational_stability_recenter"),
            "notes": [
                branch.get(
                    "note",
                    "relational_recenter_requires_resetting_overall_stability_before_progress",
                )
            ],
        }
    if pressure.status == "revise":
        branch_id = "revise_pressure"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "decompression_before_stability"),
            "trigger": branch.get("trigger", "pressure_stability_recenter"),
            "notes": [
                branch.get(
                    "note", "pressure_recenter_requires_decompression_before_restoring_stability"
                )
            ],
        }
    if trust.status == "revise":
        branch_id = "revise_trust"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "trust_rebuild_before_stability"),
            "trigger": branch.get("trigger", "trust_stability_recenter"),
            "notes": [
                branch.get("note", "trust_recenter_requires_rebuild_before_stability_can_hold")
            ],
        }
    if continuity.status == "revise":
        branch_id = "revise_continuity"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "reanchor_before_stability"),
            "trigger": branch.get("trigger", "continuity_stability_recenter"),
            "notes": [
                branch.get(
                    "note", "continuity_recenter_requires_reanchoring_before_stability_can_hold"
                )
            ],
        }
    if repair.status == "revise":
        branch_id = "revise_repair"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "repair_scaffold_before_stability"),
            "trigger": branch.get("trigger", "repair_stability_recenter"),
            "notes": [
                branch.get("note", "repair_recenter_requires_repair_scaffolding_before_stability")
            ],
        }
    if progress.status == "revise":
        branch_id = "revise_progress"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "revise",
            "branch_id": branch_id,
            "target": branch.get("target", "bounded_progress_reset_before_stability"),
            "trigger": branch.get("trigger", "progress_stability_recenter"),
            "notes": [
                branch.get(
                    "note", "progress_recenter_requires_resetting_forward_motion_before_stability"
                )
            ],
        }
    return None


def _build_stability_watch_state(
    *,
    safety: _GovernanceOutcome,
    relational: _GovernanceOutcome,
    trust: _GovernanceOutcome,
    continuity: _GovernanceOutcome,
    repair: _GovernanceOutcome,
    progress: _GovernanceOutcome,
    pacing: _GovernanceOutcome,
    attunement: _GovernanceOutcome,
) -> dict[str, object] | None:
    line = "stability"
    if not any(
        outcome.status == "watch"
        for outcome in (
            safety,
            relational,
            pacing,
            trust,
            repair,
            continuity,
            progress,
            attunement,
        )
    ):
        return None
    if safety.status == "watch":
        branch_id = "watch_safety"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "safety_buffered_stability_watch"),
            "trigger": branch.get("trigger", "safety_stability_watch"),
            "notes": [branch.get("note", "safety_watch_keeps_stability_line_cautious_and bounded")],
        }
    if relational.status == "watch":
        branch_id = "watch_relational"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "relational_buffered_stability_watch"),
            "trigger": branch.get("trigger", "relational_stability_watch"),
            "notes": [
                branch.get(
                    "note", "relational_watch_keeps_stability_line_buffered_before_more_progress"
                )
            ],
        }
    if pacing.status == "watch":
        branch_id = "watch_pacing"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "slow_stability_watch"),
            "trigger": branch.get("trigger", "pacing_stability_watch"),
            "notes": [branch.get("note", "pacing_watch_keeps_stability_line_deliberately_slow")],
        }
    if trust.status == "watch":
        branch_id = "watch_trust"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "trust_buffered_stability_watch"),
            "trigger": branch.get("trigger", "trust_stability_watch"),
            "notes": [
                branch.get("note", "trust_watch_keeps_stability_line_buffered_until_trust_recovers")
            ],
        }
    if repair.status == "watch":
        branch_id = "watch_repair"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "repair_buffered_stability_watch"),
            "trigger": branch.get("trigger", "repair_stability_watch"),
            "notes": [
                branch.get("note", "repair_watch_keeps_stability_line_scaffolded_and_low_pressure")
            ],
        }
    if continuity.status == "watch":
        branch_id = "watch_continuity"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "reanchored_stability_watch"),
            "trigger": branch.get("trigger", "continuity_stability_watch"),
            "notes": [branch.get("note", "continuity_watch_keeps_stability_line_reanchored")],
        }
    if progress.status == "watch":
        branch_id = "watch_progress"
        branch = _phase2_branch(line, "branches", branch_id)
        return {
            "status": "watch",
            "branch_id": branch_id,
            "target": branch.get("target", "bounded_progress_stability_watch"),
            "trigger": branch.get("trigger", "progress_stability_watch"),
            "notes": [
                branch.get("note", "progress_watch_keeps_stability_line_bounded_before_advancing")
            ],
        }
    branch_id = "watch_attunement"
    branch = _phase2_branch(line, "branches", branch_id)
    return {
        "status": "watch",
        "branch_id": branch_id,
        "target": branch.get("target", "attuned_stability_watch"),
        "trigger": branch.get("trigger", "attunement_stability_watch"),
        "notes": [branch.get("note", "attunement_watch_keeps_stability_line_relationship-aware")],
    }


def _build_stability_governance_trajectory(
    *,
    branch_id: str,
    status: str,
) -> dict[str, object]:
    line = "stability"
    if status == "revise":
        trajectory_branch_id = {
            "revise_safety": "recenter_safety",
            "revise_relational": "recenter_relational",
            "revise_pressure": "recenter_pressure",
            "revise_trust": "recenter_trust",
            "revise_continuity": "recenter_continuity",
            "revise_repair": "recenter_repair",
        }.get(branch_id, "recenter_progress")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "recenter",
            "trajectory_target": branch.get("target", "bounded_progress_reset_before_stability"),
            "trajectory_trigger": branch.get("trigger", "progress_stability_recenter"),
            "trajectory_notes": [
                branch.get("note", "progress_recenter_keeps_stability_line_in_bounded_reset_mode")
            ],
        }
    if status == "watch":
        trajectory_branch_id = {
            "watch_safety": "watch_safety",
            "watch_relational": "watch_relational",
            "watch_pacing": "watch_pacing",
            "watch_trust": "watch_trust",
            "watch_repair": "watch_repair",
            "watch_continuity": "watch_continuity",
            "watch_progress": "watch_progress",
        }.get(branch_id, "watch_attunement")
        branch = _phase2_branch(line, "trajectory_branches", trajectory_branch_id)
        return {
            "trajectory_status": "watch",
            "trajectory_target": branch.get("target", "attuned_stability_watch"),
            "trajectory_trigger": branch.get("trigger", "attunement_stability_watch"),
            "trajectory_notes": [
                branch.get("note", "attunement_watch_keeps_stability_line_relationally_tuned")
            ],
        }
    branch = _phase2_branch(line, "trajectory_branches", "stable")
    return {
        "trajectory_status": "stable",
        "trajectory_target": branch.get("target", "steady_bounded_relational_stability"),
        "trajectory_trigger": branch.get("trigger", "stability_governance_stable"),
        "trajectory_notes": [branch.get("note", "stability_line_is_holding_steady_and_bounded")],
    }


def build_system3_phase2_snapshot(*, prelude: _System3Prelude) -> System3Snapshot:
    governance_outcomes = _build_core_governance_outcomes(prelude=prelude)
    growth_transition = _build_growth_transition(prelude=prelude)
    governance_outcomes["progress"] = _build_progress_governance(
        safety=governance_outcomes["safety"],
        pressure=governance_outcomes["pressure"],
        continuity=governance_outcomes["continuity"],
        commitment=governance_outcomes["commitment"],
        pacing=governance_outcomes["pacing"],
        growth_transition_status=growth_transition.status,
        expectation_calibration_status=prelude.expectation_calibration_status,
    )
    governance_outcomes["stability"] = _build_stability_governance(
        safety=governance_outcomes["safety"],
        relational=governance_outcomes["relational"],
        pressure=governance_outcomes["pressure"],
        trust=governance_outcomes["trust"],
        continuity=governance_outcomes["continuity"],
        repair=governance_outcomes["repair"],
        progress=governance_outcomes["progress"],
        pacing=governance_outcomes["pacing"],
        attunement=governance_outcomes["attunement"],
    )
    version_migration = _build_version_migration(
        prelude=prelude,
        growth_transition=growth_transition,
    )
    review_focus = _build_review_focus(
        prelude=prelude,
        governance_outcomes=governance_outcomes,
        growth_transition=growth_transition,
        version_migration=version_migration,
    )
    return _build_phase2_snapshot(
        prelude=prelude,
        governance_outcomes=governance_outcomes,
        growth_transition=growth_transition,
        version_migration=version_migration,
        review_focus=review_focus,
    )
