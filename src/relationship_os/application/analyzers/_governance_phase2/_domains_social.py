"""Phase 2 governance – social domain outcomes (commitment, disclosure, reciprocity)."""

from __future__ import annotations

from ._base import (
    _GovernanceOutcome,
    _phase2_branch,
    _System3Prelude,
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


