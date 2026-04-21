"""Phase 2 governance – core domain outcomes (dependency through pacing)."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _clamp, _compact

from ._base import (
    _GovernanceOutcome,
    _System3Prelude,
    _phase2_branch,
    _phase2_governance_line,
    _phase2_section,
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


