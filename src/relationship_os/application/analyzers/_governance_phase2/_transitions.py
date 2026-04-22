"""Phase 2 governance – review focus, outcomes, growth/version transitions, snapshot."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _clamp, _compact
from relationship_os.domain.contracts import System3Snapshot

from ._base import (
    _SYSTEM3_GOVERNANCE_DOMAIN_ORDER,
    _governance_kwargs,
    _GovernanceOutcome,
    _GrowthTransitionOutcome,
    _phase2_section,
    _System3Prelude,
    _VersionMigrationOutcome,
)
from ._domains_core import (
    _build_attunement_governance,
    _build_autonomy_governance,
    _build_boundary_governance,
    _build_clarity_governance,
    _build_continuity_governance,
    _build_dependency_governance,
    _build_pacing_governance,
    _build_repair_governance,
    _build_support_governance,
    _build_trust_governance,
)
from ._domains_safety import (
    _build_pressure_governance,
    _build_relational_governance,
    _build_safety_governance,
)
from ._domains_social import (
    _build_commitment_governance,
    _build_disclosure_governance,
    _build_reciprocity_governance,
)


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
