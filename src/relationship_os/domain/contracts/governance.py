from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class RuntimeQualityDoctorReport:
    status: str
    triggered_turn_index: int
    window_turn_count: int
    issue_count: int
    issues: list[str] = field(default_factory=list)
    recommended_repairs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class System3Snapshot:
    triggered_turn_index: int
    identity_anchor: str
    identity_consistency: str
    identity_confidence: float
    growth_stage: str
    growth_signal: str
    user_model_confidence: float
    identity_trajectory_status: str = "stable"
    identity_trajectory_target: str = "collaborative_reflective_support"
    identity_trajectory_trigger: str = "identity_consistent"
    identity_trajectory_notes: list[str] = field(default_factory=list)
    user_needs: list[str] = field(default_factory=list)
    user_preferences: list[str] = field(default_factory=list)
    emotional_debt_status: str = "low"
    emotional_debt_score: float = 0.0
    debt_signals: list[str] = field(default_factory=list)
    emotional_debt_trajectory_status: str = "stable"
    emotional_debt_trajectory_target: str = "steady_low_debt"
    emotional_debt_trajectory_trigger: str = "debt_stable"
    emotional_debt_trajectory_notes: list[str] = field(default_factory=list)
    strategy_audit_status: str = "pass"
    strategy_fit: str = "aligned"
    strategy_audit_notes: list[str] = field(default_factory=list)
    strategy_audit_trajectory_status: str = "stable"
    strategy_audit_trajectory_target: str = "aligned_strategy_path"
    strategy_audit_trajectory_trigger: str = "strategy_line_stable"
    strategy_audit_trajectory_notes: list[str] = field(default_factory=list)
    strategy_supervision_status: str = "pass"
    strategy_supervision_mode: str = "steady_supervision"
    strategy_supervision_trigger: str = "strategy_stable"
    strategy_supervision_notes: list[str] = field(default_factory=list)
    strategy_supervision_trajectory_status: str = "stable"
    strategy_supervision_trajectory_target: str = "steady_supervision"
    strategy_supervision_trajectory_trigger: str = "strategy_supervision_stable"
    strategy_supervision_trajectory_notes: list[str] = field(default_factory=list)
    moral_reasoning_status: str = "pass"
    moral_posture: str = "steady_progress_care"
    moral_conflict: str = "none"
    moral_principles: list[str] = field(default_factory=list)
    moral_notes: list[str] = field(default_factory=list)
    moral_trajectory_status: str = "stable"
    moral_trajectory_target: str = "steady_progress_care"
    moral_trajectory_trigger: str = "moral_line_stable"
    moral_trajectory_notes: list[str] = field(default_factory=list)
    user_model_evolution_status: str = "pass"
    user_model_revision_mode: str = "steady_refinement"
    user_model_shift_signal: str = "stable"
    user_model_evolution_notes: list[str] = field(default_factory=list)
    user_model_trajectory_status: str = "stable"
    user_model_trajectory_target: str = "steady_refinement"
    user_model_trajectory_trigger: str = "model_stable"
    user_model_trajectory_notes: list[str] = field(default_factory=list)
    expectation_calibration_status: str = "pass"
    expectation_calibration_target: str = "bounded_progress_expectation"
    expectation_calibration_trigger: str = "expectation_line_stable"
    expectation_calibration_notes: list[str] = field(default_factory=list)
    expectation_calibration_trajectory_status: str = "stable"
    expectation_calibration_trajectory_target: str = "bounded_progress_expectation"
    expectation_calibration_trajectory_trigger: str = "expectation_line_stable"
    expectation_calibration_trajectory_notes: list[str] = field(default_factory=list)
    dependency_governance_status: str = "pass"
    dependency_governance_target: str = "steady_low_dependency_support"
    dependency_governance_trigger: str = "dependency_line_stable"
    dependency_governance_notes: list[str] = field(default_factory=list)
    dependency_governance_trajectory_status: str = "stable"
    dependency_governance_trajectory_target: str = "steady_low_dependency_support"
    dependency_governance_trajectory_trigger: str = "dependency_governance_stable"
    dependency_governance_trajectory_notes: list[str] = field(default_factory=list)
    autonomy_governance_status: str = "pass"
    autonomy_governance_target: str = "steady_explicit_autonomy"
    autonomy_governance_trigger: str = "autonomy_line_stable"
    autonomy_governance_notes: list[str] = field(default_factory=list)
    autonomy_governance_trajectory_status: str = "stable"
    autonomy_governance_trajectory_target: str = "steady_explicit_autonomy"
    autonomy_governance_trajectory_trigger: str = "autonomy_governance_stable"
    autonomy_governance_trajectory_notes: list[str] = field(default_factory=list)
    boundary_governance_status: str = "pass"
    boundary_governance_target: str = "steady_clear_boundary_support"
    boundary_governance_trigger: str = "boundary_line_stable"
    boundary_governance_notes: list[str] = field(default_factory=list)
    boundary_governance_trajectory_status: str = "stable"
    boundary_governance_trajectory_target: str = "steady_clear_boundary_support"
    boundary_governance_trajectory_trigger: str = "boundary_governance_stable"
    boundary_governance_trajectory_notes: list[str] = field(default_factory=list)
    support_governance_status: str = "pass"
    support_governance_target: str = "steady_bounded_support"
    support_governance_trigger: str = "support_line_stable"
    support_governance_notes: list[str] = field(default_factory=list)
    support_governance_trajectory_status: str = "stable"
    support_governance_trajectory_target: str = "steady_bounded_support"
    support_governance_trajectory_trigger: str = "support_governance_stable"
    support_governance_trajectory_notes: list[str] = field(default_factory=list)
    continuity_governance_status: str = "pass"
    continuity_governance_target: str = "steady_contextual_continuity"
    continuity_governance_trigger: str = "continuity_line_stable"
    continuity_governance_notes: list[str] = field(default_factory=list)
    continuity_governance_trajectory_status: str = "stable"
    continuity_governance_trajectory_target: str = "steady_contextual_continuity"
    continuity_governance_trajectory_trigger: str = "continuity_governance_stable"
    continuity_governance_trajectory_notes: list[str] = field(default_factory=list)
    repair_governance_status: str = "pass"
    repair_governance_target: str = "steady_relational_repair_posture"
    repair_governance_trigger: str = "repair_line_stable"
    repair_governance_notes: list[str] = field(default_factory=list)
    repair_governance_trajectory_status: str = "stable"
    repair_governance_trajectory_target: str = "steady_relational_repair_posture"
    repair_governance_trajectory_trigger: str = "repair_governance_stable"
    repair_governance_trajectory_notes: list[str] = field(default_factory=list)
    attunement_governance_status: str = "pass"
    attunement_governance_target: str = "steady_relational_attunement"
    attunement_governance_trigger: str = "attunement_line_stable"
    attunement_governance_notes: list[str] = field(default_factory=list)
    attunement_governance_trajectory_status: str = "stable"
    attunement_governance_trajectory_target: str = "steady_relational_attunement"
    attunement_governance_trajectory_trigger: str = "attunement_governance_stable"
    attunement_governance_trajectory_notes: list[str] = field(default_factory=list)
    trust_governance_status: str = "pass"
    trust_governance_target: str = "steady_mutual_trust_posture"
    trust_governance_trigger: str = "trust_line_stable"
    trust_governance_notes: list[str] = field(default_factory=list)
    trust_governance_trajectory_status: str = "stable"
    trust_governance_trajectory_target: str = "steady_mutual_trust_posture"
    trust_governance_trajectory_trigger: str = "trust_governance_stable"
    trust_governance_trajectory_notes: list[str] = field(default_factory=list)
    clarity_governance_status: str = "pass"
    clarity_governance_target: str = "steady_contextual_clarity"
    clarity_governance_trigger: str = "clarity_line_stable"
    clarity_governance_notes: list[str] = field(default_factory=list)
    clarity_governance_trajectory_status: str = "stable"
    clarity_governance_trajectory_target: str = "steady_contextual_clarity"
    clarity_governance_trajectory_trigger: str = "clarity_governance_stable"
    clarity_governance_trajectory_notes: list[str] = field(default_factory=list)
    pacing_governance_status: str = "pass"
    pacing_governance_target: str = "steady_relational_pacing"
    pacing_governance_trigger: str = "pacing_line_stable"
    pacing_governance_notes: list[str] = field(default_factory=list)
    pacing_governance_trajectory_status: str = "stable"
    pacing_governance_trajectory_target: str = "steady_relational_pacing"
    pacing_governance_trajectory_trigger: str = "pacing_governance_stable"
    pacing_governance_trajectory_notes: list[str] = field(default_factory=list)
    commitment_governance_status: str = "pass"
    commitment_governance_target: str = "steady_calibrated_commitment"
    commitment_governance_trigger: str = "commitment_line_stable"
    commitment_governance_notes: list[str] = field(default_factory=list)
    commitment_governance_trajectory_status: str = "stable"
    commitment_governance_trajectory_target: str = "steady_calibrated_commitment"
    commitment_governance_trajectory_trigger: str = "commitment_governance_stable"
    commitment_governance_trajectory_notes: list[str] = field(default_factory=list)
    disclosure_governance_status: str = "pass"
    disclosure_governance_target: str = "steady_transparent_disclosure"
    disclosure_governance_trigger: str = "disclosure_line_stable"
    disclosure_governance_notes: list[str] = field(default_factory=list)
    disclosure_governance_trajectory_status: str = "stable"
    disclosure_governance_trajectory_target: str = "steady_transparent_disclosure"
    disclosure_governance_trajectory_trigger: str = "disclosure_governance_stable"
    disclosure_governance_trajectory_notes: list[str] = field(default_factory=list)
    reciprocity_governance_status: str = "pass"
    reciprocity_governance_target: str = "steady_mutual_reciprocity"
    reciprocity_governance_trigger: str = "reciprocity_line_stable"
    reciprocity_governance_notes: list[str] = field(default_factory=list)
    reciprocity_governance_trajectory_status: str = "stable"
    reciprocity_governance_trajectory_target: str = "steady_mutual_reciprocity"
    reciprocity_governance_trajectory_trigger: str = "reciprocity_governance_stable"
    reciprocity_governance_trajectory_notes: list[str] = field(default_factory=list)
    pressure_governance_status: str = "pass"
    pressure_governance_target: str = "steady_low_pressure_support"
    pressure_governance_trigger: str = "pressure_line_stable"
    pressure_governance_notes: list[str] = field(default_factory=list)
    pressure_governance_trajectory_status: str = "stable"
    pressure_governance_trajectory_target: str = "steady_low_pressure_support"
    pressure_governance_trajectory_trigger: str = "pressure_governance_stable"
    pressure_governance_trajectory_notes: list[str] = field(default_factory=list)
    relational_governance_status: str = "pass"
    relational_governance_target: str = "steady_bounded_relational_progress"
    relational_governance_trigger: str = "relational_line_stable"
    relational_governance_notes: list[str] = field(default_factory=list)
    relational_governance_trajectory_status: str = "stable"
    relational_governance_trajectory_target: str = (
        "steady_bounded_relational_progress"
    )
    relational_governance_trajectory_trigger: str = (
        "relational_governance_stable"
    )
    relational_governance_trajectory_notes: list[str] = field(default_factory=list)
    safety_governance_status: str = "pass"
    safety_governance_target: str = "steady_safe_relational_support"
    safety_governance_trigger: str = "safety_line_stable"
    safety_governance_notes: list[str] = field(default_factory=list)
    safety_governance_trajectory_status: str = "stable"
    safety_governance_trajectory_target: str = "steady_safe_relational_support"
    safety_governance_trajectory_trigger: str = "safety_governance_stable"
    safety_governance_trajectory_notes: list[str] = field(default_factory=list)
    progress_governance_status: str = "pass"
    progress_governance_target: str = "steady_bounded_progress"
    progress_governance_trigger: str = "progress_line_stable"
    progress_governance_notes: list[str] = field(default_factory=list)
    progress_governance_trajectory_status: str = "stable"
    progress_governance_trajectory_target: str = "steady_bounded_progress"
    progress_governance_trajectory_trigger: str = "progress_governance_stable"
    progress_governance_trajectory_notes: list[str] = field(default_factory=list)
    stability_governance_status: str = "pass"
    stability_governance_target: str = "steady_bounded_relational_stability"
    stability_governance_trigger: str = "stability_line_stable"
    stability_governance_notes: list[str] = field(default_factory=list)
    stability_governance_trajectory_status: str = "stable"
    stability_governance_trajectory_target: str = (
        "steady_bounded_relational_stability"
    )
    stability_governance_trajectory_trigger: str = (
        "stability_governance_stable"
    )
    stability_governance_trajectory_notes: list[str] = field(default_factory=list)
    growth_transition_status: str = "stable"
    growth_transition_target: str = "steadying"
    growth_transition_trigger: str = "maintain_current_stage"
    growth_transition_readiness: float = 0.0
    growth_transition_notes: list[str] = field(default_factory=list)
    growth_transition_trajectory_status: str = "stable"
    growth_transition_trajectory_target: str = "steadying"
    growth_transition_trajectory_trigger: str = "growth_line_stable"
    growth_transition_trajectory_notes: list[str] = field(default_factory=list)
    version_migration_status: str = "pass"
    version_migration_scope: str = "stable_rebuild_ready"
    version_migration_trigger: str = "projection_rebuild_ready"
    version_migration_notes: list[str] = field(default_factory=list)
    version_migration_trajectory_status: str = "stable"
    version_migration_trajectory_target: str = "stable_rebuild_ready"
    version_migration_trajectory_trigger: str = "migration_line_stable"
    version_migration_trajectory_notes: list[str] = field(default_factory=list)
    review_focus: list[str] = field(default_factory=list)
