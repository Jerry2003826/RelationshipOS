"""Phase 2 governance – safety outcomes (pressure/relational/safety/progress/stability)."""

from __future__ import annotations

from ._base import (
    _GovernanceOutcome,
    _phase2_branch,
    _System3Prelude,
)


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
