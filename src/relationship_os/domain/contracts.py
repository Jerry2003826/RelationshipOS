from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ContextFrame:
    dialogue_act: str
    bid_signal: str
    common_ground: list[str]
    appraisal: str
    topic: str
    attention: str


@dataclass(slots=True, frozen=True)
class RelationshipState:
    r_vector: dict[str, float]
    tom_inference: str
    psychological_safety: float
    emotional_contagion: str
    turbulence_risk: str
    tipping_point_risk: str
    dependency_risk: str


@dataclass(slots=True, frozen=True)
class MemoryBundle:
    working_memory: list[str] = field(default_factory=list)
    episodic_memory: list[str] = field(default_factory=list)
    semantic_memory: list[str] = field(default_factory=list)
    relational_memory: list[str] = field(default_factory=list)
    reflective_memory: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RepairPlan:
    rupture_detected: bool
    rupture_type: str
    urgency: str
    recommended_actions: list[str]


@dataclass(slots=True, frozen=True)
class RepairAssessment:
    repair_needed: bool
    rupture_type: str
    severity: str
    urgency: str
    attunement_gap: bool
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class KnowledgeBoundaryDecision:
    decision: str
    boundary_type: str
    can_answer: bool
    should_disclose_uncertainty: bool
    confidence_level: str
    rationale: str
    missing_information: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class PrivateJudgment:
    summary: str
    rationale: str
    confidence: float


@dataclass(slots=True, frozen=True)
class ConfidenceAssessment:
    level: str
    score: float
    reason: str
    response_mode: str = "direct"
    should_disclose_uncertainty: bool = False
    needs_clarification: bool = False
    risk_flags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class StrategyDecision:
    strategy: str
    rationale: str
    safety_ok: bool
    source_strategy: str | None = None
    diversity_status: str = "stable"
    diversity_entropy: float = 0.0
    explored_strategy: bool = False
    recent_strategy_counts: dict[str, int] = field(default_factory=dict)
    alternatives_considered: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class PolicyGateDecision:
    selected_path: str
    red_line_status: str
    timing_mode: str
    regulation_mode: str
    empowerment_risk: str
    safe_to_proceed: bool
    rationale: str
    safety_flags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RehearsalResult:
    predicted_user_impact: str
    projected_risk_level: str
    likely_user_response: str
    failure_modes: list[str] = field(default_factory=list)
    recommended_adjustments: list[str] = field(default_factory=list)
    approved: bool = True


@dataclass(slots=True, frozen=True)
class EmpowermentAudit:
    status: str
    empowerment_risk: str
    transparency_required: bool
    dependency_safe: bool
    flagged_issues: list[str] = field(default_factory=list)
    recommended_adjustments: list[str] = field(default_factory=list)
    approved: bool = True


@dataclass(slots=True, frozen=True)
class ResponseDraftPlan:
    opening_move: str
    structure: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    must_avoid: list[str] = field(default_factory=list)
    phrasing_constraints: list[str] = field(default_factory=list)
    question_strategy: str = "none"
    approved: bool = True


@dataclass(slots=True, frozen=True)
class ResponseRenderingPolicy:
    rendering_mode: str
    max_sentences: int
    include_validation: bool
    include_next_step: bool
    include_boundary_statement: bool
    include_uncertainty_statement: bool
    question_count_limit: int
    style_guardrails: list[str] = field(default_factory=list)
    approved: bool = True


@dataclass(slots=True, frozen=True)
class ResponseSequencePlan:
    mode: str
    unit_count: int
    reasons: list[str] = field(default_factory=list)
    segment_labels: list[str] = field(default_factory=list)


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


@dataclass(slots=True, frozen=True)
class RuntimeCoordinationSnapshot:
    triggered_turn_index: int
    time_awareness_mode: str
    idle_gap_seconds: float
    session_age_seconds: float
    ritual_phase: str
    cognitive_load_band: str
    response_budget_mode: str
    proactive_followup_eligible: bool
    proactive_style: str
    somatic_cue: str | None = None
    coordination_notes: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class GuidancePlan:
    mode: str
    lead_with: str
    pacing: str
    step_budget: int
    agency_mode: str
    ritual_action: str = ""
    checkpoint_style: str = ""
    handoff_mode: str = ""
    carryover_mode: str = ""
    micro_actions: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ConversationCadencePlan:
    status: str
    turn_shape: str
    ritual_depth: str
    somatic_track: str = "none"
    followup_tempo: str = "none"
    user_space_mode: str = "balanced_space"
    transition_intent: str = ""
    next_checkpoint: str = ""
    cadence_actions: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class SessionRitualPlan:
    phase: str
    opening_move: str
    bridge_move: str
    closing_move: str
    continuity_anchor: str = ""
    somatic_shortcut: str = "none"
    micro_rituals: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class SomaticOrchestrationPlan:
    status: str
    cue: str
    primary_mode: str
    body_anchor: str
    followup_style: str
    allow_in_followup: bool
    micro_actions: list[str] = field(default_factory=list)
    phrasing_guardrails: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveFollowupDirective:
    eligible: bool
    status: str
    style: str
    trigger_after_seconds: int
    window_seconds: int
    rationale: str
    opening_hint: str
    trigger_conditions: list[str] = field(default_factory=list)
    hold_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ProactiveCadencePlan:
    status: str
    cadence_key: str
    stage_labels: list[str] = field(default_factory=list)
    stage_intervals_seconds: list[int] = field(default_factory=list)
    window_seconds: int = 0
    close_after_stage_index: int = 0
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ReengagementPlan:
    status: str
    ritual_mode: str
    delivery_mode: str
    strategy_key: str = "none"
    relational_move: str = "none"
    pressure_mode: str = "none"
    autonomy_signal: str = "none"
    sequence_objective: str = ""
    somatic_action: str | None = None
    segment_labels: list[str] = field(default_factory=list)
    focus_points: list[str] = field(default_factory=list)
    tone: str = "gentle"
    opening_hint: str = ""
    closing_hint: str = ""
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ReengagementStrategyCandidate:
    strategy_key: str
    suitability_score: float
    relational_move: str
    pressure_mode: str
    autonomy_signal: str
    delivery_mode_hint: str
    selected: bool = False
    blocked: bool = False
    supporting_session_count: int = 0
    contextual_supporting_session_count: int = 0
    historical_preference_score: float | None = None
    contextual_preference_score: float | None = None
    exploration_bonus: float = 0.0
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ReengagementMatrixAssessment:
    status: str
    matrix_key: str
    selected_strategy_key: str
    selected_score: float
    blocked_count: int = 0
    learning_mode: str = "cold_start"
    learning_context_stratum: str = "steady_progress"
    learning_signal_count: int = 0
    candidates: list[ReengagementStrategyCandidate] = field(default_factory=list)
    learning_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveSchedulingPlan:
    status: str
    scheduler_mode: str
    min_seconds_since_last_outbound: int
    first_touch_extra_delay_seconds: int = 0
    stage_spacing_mode: str = "standard"
    low_pressure_guard: str = "none"
    scheduling_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageDirective:
    stage_label: str
    objective: str
    delivery_mode: str
    question_mode: str
    autonomy_mode: str
    closing_style: str
    allow_somatic_carryover: bool = False
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveOrchestrationPlan:
    status: str
    orchestration_key: str
    close_loop_stage: str
    stage_directives: list[ProactiveStageDirective] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageActuation:
    stage_label: str
    opening_move: str
    bridge_move: str
    closing_move: str
    continuity_anchor: str
    somatic_mode: str
    somatic_body_anchor: str
    followup_style: str
    user_space_signal: str
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveActuationPlan:
    status: str
    actuation_key: str
    stage_actuations: list[ProactiveStageActuation] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageProgressionDirective:
    stage_label: str
    max_overdue_seconds: int
    on_expired: str
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveProgressionPlan:
    status: str
    progression_key: str
    close_loop_stage: str
    stage_progressions: list[ProactiveStageProgressionDirective] = field(
        default_factory=list
    )
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageGuardrail:
    stage_label: str
    min_seconds_since_last_user: int
    min_seconds_since_last_dispatch: int
    on_guardrail_hit: str
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveGuardrailPlan:
    status: str
    guardrail_key: str
    max_dispatch_count: int
    stage_guardrails: list[ProactiveStageGuardrail] = field(default_factory=list)
    hard_stop_conditions: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveAggregateGovernanceAssessment:
    status: str
    primary_domain: str | None
    active_domains: list[str] = field(default_factory=list)
    domain_count: int = 0
    summary: str = "clear"
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveAggregateControllerDecision:
    status: str
    controller_key: str
    current_stage_label: str
    next_stage_label: str | None
    decision: str
    changed: bool
    stage_additional_delay_seconds: int = 0
    line_additional_delay_seconds: int = 0
    dispatch_retry_after_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_domain: str | None = None
    active_domains: list[str] = field(default_factory=list)
    controller_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveOrchestrationControllerDecision:
    status: str
    controller_key: str
    current_stage_label: str
    next_stage_label: str | None
    decision: str
    changed: bool
    stage_additional_delay_seconds: int = 0
    line_additional_delay_seconds: int = 0
    dispatch_retry_after_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str | None = None
    active_sources: list[str] = field(default_factory=list)
    controller_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageRefreshPlan:
    status: str
    refresh_key: str
    stage_label: str
    dispatch_window_status: str
    changed: bool
    refreshed_delivery_mode: str
    refreshed_question_mode: str
    refreshed_autonomy_mode: str
    refreshed_opening_move: str
    refreshed_bridge_move: str
    refreshed_closing_move: str
    refreshed_continuity_anchor: str
    refreshed_somatic_mode: str
    refreshed_user_space_signal: str
    refresh_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageReplanAssessment:
    status: str
    replan_key: str
    stage_label: str
    dispatch_window_status: str
    changed: bool
    selected_strategy_key: str
    selected_ritual_mode: str
    selected_delivery_mode: str
    selected_relational_move: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_sequence_objective: str
    selected_somatic_action: str | None = None
    replan_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveDispatchGateDecision:
    status: str
    gate_key: str
    stage_label: str
    dispatch_window_status: str
    decision: str
    changed: bool
    retry_after_seconds: int
    selected_strategy_key: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    gate_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveDispatchEnvelopeDecision:
    status: str
    envelope_key: str
    stage_label: str
    decision: str
    changed: bool
    selected_strategy_key: str
    selected_ritual_mode: str
    selected_reengagement_delivery_mode: str
    selected_relational_move: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_sequence_objective: str
    selected_somatic_action: str | None = None
    selected_stage_delivery_mode: str = "single_message"
    selected_stage_question_mode: str = "statement_only"
    selected_stage_autonomy_mode: str = "light_invitation"
    selected_stage_objective: str = ""
    selected_stage_closing_style: str = "none"
    selected_opening_move: str = "none"
    selected_bridge_move: str = "none"
    selected_closing_move: str = "none"
    selected_continuity_anchor: str = "none"
    selected_somatic_mode: str = "none"
    selected_somatic_body_anchor: str = "none"
    selected_followup_style: str = "none"
    selected_user_space_signal: str = "none"
    dispatch_retry_after_seconds: int = 0
    active_sources: list[str] = field(default_factory=list)
    envelope_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageStateDecision:
    status: str
    state_key: str
    stage_label: str
    stage_index: int
    stage_count: int
    queue_status: str
    state_mode: str
    changed: bool
    selected_strategy_key: str = "none"
    selected_stage_delivery_mode: str = "none"
    selected_reengagement_delivery_mode: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    line_state: str = "steady"
    progression_action: str = "none"
    progression_advanced: bool = False
    dispatch_envelope_key: str | None = None
    dispatch_envelope_decision: str | None = None
    primary_source: str | None = None
    controller_decision: str | None = None
    state_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageTransitionDecision:
    status: str
    transition_key: str
    stage_label: str
    stage_index: int
    stage_count: int
    current_state_key: str
    current_state_mode: str
    transition_mode: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_queue_status_hint: str = "hold"
    stage_exit_mode: str = "stay"
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    line_state: str = "steady"
    progression_action: str = "none"
    progression_advanced: bool = False
    dispatch_gate_decision: str | None = None
    dispatch_envelope_decision: str | None = None
    primary_source: str = "cadence"
    controller_decision: str | None = None
    transition_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageMachineDecision:
    status: str
    machine_key: str
    stage_label: str
    stage_index: int
    stage_count: int
    current_state_key: str
    current_state_mode: str
    transition_key: str
    transition_mode: str
    queue_status: str
    machine_mode: str
    lifecycle_mode: str
    actionability: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_queue_status_hint: str = "hold"
    stage_exit_mode: str = "stay"
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    line_state: str = "steady"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    machine_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveDispatchFeedbackAssessment:
    status: str
    feedback_key: str
    stage_label: str
    dispatch_count: int
    prior_stage_label: str | None
    gate_defer_count: int
    changed: bool
    selected_strategy_key: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_delivery_mode: str
    selected_sequence_objective: str
    feedback_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveStageControllerDecision:
    status: str
    controller_key: str
    trigger_stage_label: str
    target_stage_label: str | None
    decision: str
    changed: bool
    additional_delay_seconds: int
    selected_strategy_key: str
    selected_pressure_mode: str
    selected_autonomy_signal: str
    selected_delivery_mode: str
    controller_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLineControllerDecision:
    status: str
    controller_key: str
    trigger_stage_label: str
    line_state: str
    decision: str
    changed: bool
    affected_stage_labels: list[str] = field(default_factory=list)
    additional_delay_seconds: int = 0
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    controller_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLineStateDecision:
    status: str
    line_key: str
    current_stage_label: str
    current_stage_index: int
    stage_count: int
    remaining_stage_count: int
    line_state: str
    lifecycle_mode: str
    actionability: str
    changed: bool
    current_stage_machine_mode: str
    current_stage_transition_mode: str
    next_stage_label: str | None = None
    close_loop_stage: str | None = None
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    line_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLineTransitionDecision:
    status: str
    transition_key: str
    current_line_key: str
    current_stage_label: str
    current_stage_index: int
    stage_count: int
    line_state: str
    lifecycle_mode: str
    transition_mode: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_line_state: str | None = None
    next_lifecycle_mode: str | None = None
    line_exit_mode: str = "stay"
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    transition_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLineMachineDecision:
    status: str
    machine_key: str
    current_line_key: str
    current_stage_label: str
    current_stage_index: int
    stage_count: int
    transition_key: str
    transition_mode: str
    line_state: str
    lifecycle_mode: str
    machine_mode: str
    actionability: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_line_state: str | None = None
    next_lifecycle_mode: str | None = None
    line_exit_mode: str = "stay"
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    machine_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleStateDecision:
    status: str
    state_key: str
    current_stage_label: str
    current_stage_index: int
    stage_count: int
    stage_machine_key: str
    stage_machine_mode: str
    line_machine_key: str
    line_machine_mode: str
    line_state: str
    state_mode: str
    lifecycle_mode: str
    actionability: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_line_state: str | None = None
    next_line_lifecycle_mode: str | None = None
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    state_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleTransitionDecision:
    status: str
    transition_key: str
    current_state_key: str
    current_stage_label: str
    current_stage_index: int
    stage_count: int
    state_mode: str
    lifecycle_mode: str
    transition_mode: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_line_state: str | None = None
    next_line_lifecycle_mode: str | None = None
    lifecycle_exit_mode: str = "stay"
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    transition_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleMachineDecision:
    status: str
    machine_key: str
    current_state_key: str
    current_stage_label: str
    current_stage_index: int
    stage_count: int
    transition_key: str
    transition_mode: str
    stage_machine_key: str
    stage_machine_mode: str
    line_machine_key: str
    line_machine_mode: str
    line_state: str
    state_mode: str
    lifecycle_mode: str
    machine_mode: str
    actionability: str
    changed: bool
    next_stage_label: str | None = None
    next_stage_index: int | None = None
    next_line_state: str | None = None
    next_line_lifecycle_mode: str | None = None
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    machine_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleControllerDecision:
    status: str
    controller_key: str
    current_stage_label: str
    lifecycle_state: str
    decision: str
    changed: bool
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    controller_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleEnvelopeDecision:
    status: str
    envelope_key: str
    current_stage_label: str
    lifecycle_state: str
    envelope_mode: str
    decision: str
    actionability: str
    changed: bool
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    envelope_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleSchedulerDecision:
    status: str
    scheduler_key: str
    current_stage_label: str
    lifecycle_state: str
    lifecycle_envelope_mode: str
    scheduler_mode: str
    decision: str
    queue_status_hint: str
    actionability: str
    changed: bool
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    scheduler_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleWindowDecision:
    status: str
    window_key: str
    current_stage_label: str
    lifecycle_state: str
    scheduler_mode: str
    window_mode: str
    decision: str
    queue_status: str
    schedule_reason: str
    actionability: str
    changed: bool
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    window_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleQueueDecision:
    status: str
    queue_key: str
    current_stage_label: str
    lifecycle_state: str
    window_mode: str
    queue_mode: str
    decision: str
    queue_status: str
    actionability: str
    changed: bool
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    queue_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleDispatchDecision:
    status: str
    dispatch_key: str
    current_stage_label: str
    lifecycle_state: str
    queue_mode: str
    dispatch_mode: str
    decision: str
    actionability: str
    changed: bool
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "cadence"
    controller_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    dispatch_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleOutcomeDecision:
    status: str
    outcome_key: str
    current_stage_label: str
    lifecycle_state: str
    dispatch_mode: str
    outcome_mode: str
    decision: str
    actionability: str
    dispatched: bool
    message_event_count: int = 0
    changed: bool = True
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "dispatch"
    dispatch_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    outcome_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleResolutionDecision:
    status: str
    resolution_key: str
    current_stage_label: str
    lifecycle_state: str
    outcome_mode: str
    resolution_mode: str
    decision: str
    actionability: str
    changed: bool
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    next_stage_label: str | None = None
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "outcome"
    outcome_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    resolution_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleActivationDecision:
    status: str
    activation_key: str
    current_stage_label: str
    lifecycle_state: str
    resolution_mode: str
    activation_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "resolution"
    resolution_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    activation_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleSettlementDecision:
    status: str
    settlement_key: str
    current_stage_label: str
    lifecycle_state: str
    activation_mode: str
    settlement_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "activation"
    activation_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    settlement_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleClosureDecision:
    status: str
    closure_key: str
    current_stage_label: str
    lifecycle_state: str
    settlement_mode: str
    closure_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "settlement"
    settlement_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    closure_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleAvailabilityDecision:
    status: str
    availability_key: str
    current_stage_label: str
    lifecycle_state: str
    closure_mode: str
    availability_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "closure"
    closure_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    availability_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleRetentionDecision:
    status: str
    retention_key: str
    current_stage_label: str
    lifecycle_state: str
    availability_mode: str
    retention_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "availability"
    availability_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    retention_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleEligibilityDecision:
    status: str
    eligibility_key: str
    current_stage_label: str
    lifecycle_state: str
    retention_mode: str
    eligibility_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "retention"
    retention_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    eligibility_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleCandidateDecision:
    status: str
    candidate_key: str
    current_stage_label: str
    lifecycle_state: str
    eligibility_mode: str
    candidate_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "eligibility"
    eligibility_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    candidate_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleSelectabilityDecision:
    status: str
    selectability_key: str
    current_stage_label: str
    lifecycle_state: str
    candidate_mode: str
    selectability_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "candidate"
    candidate_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    selectability_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleReentryDecision:
    status: str
    reentry_key: str
    current_stage_label: str
    lifecycle_state: str
    selectability_mode: str
    reentry_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "selectability"
    selectability_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    reentry_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleReactivationDecision:
    status: str
    reactivation_key: str
    current_stage_label: str
    lifecycle_state: str
    reentry_mode: str
    reactivation_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "reentry"
    reentry_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    reactivation_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleResumptionDecision:
    status: str
    resumption_key: str
    current_stage_label: str
    lifecycle_state: str
    reactivation_mode: str
    resumption_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "reactivation"
    reactivation_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    resumption_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleReadinessDecision:
    status: str
    readiness_key: str
    current_stage_label: str
    lifecycle_state: str
    resumption_mode: str
    readiness_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "resumption"
    resumption_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    readiness_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleArmingDecision:
    status: str
    arming_key: str
    current_stage_label: str
    lifecycle_state: str
    readiness_mode: str
    arming_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "readiness"
    readiness_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    arming_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleTriggerDecision:
    status: str
    trigger_key: str
    current_stage_label: str
    lifecycle_state: str
    arming_mode: str
    trigger_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "arming"
    arming_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    trigger_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleLaunchDecision:
    status: str
    launch_key: str
    current_stage_label: str
    lifecycle_state: str
    trigger_mode: str
    launch_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "trigger"
    trigger_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    launch_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleHandoffDecision:
    status: str
    handoff_key: str
    current_stage_label: str
    lifecycle_state: str
    launch_mode: str
    handoff_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "launch"
    launch_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    handoff_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleContinuationDecision:
    status: str
    continuation_key: str
    current_stage_label: str
    lifecycle_state: str
    handoff_mode: str
    continuation_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "handoff"
    handoff_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    continuation_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleSustainmentDecision:
    status: str
    sustainment_key: str
    current_stage_label: str
    lifecycle_state: str
    continuation_mode: str
    sustainment_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "continuation"
    continuation_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    sustainment_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleStewardshipDecision:
    status: str
    stewardship_key: str
    current_stage_label: str
    lifecycle_state: str
    sustainment_mode: str
    stewardship_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "sustainment"
    sustainment_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    stewardship_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleGuardianshipDecision:
    status: str
    guardianship_key: str
    current_stage_label: str
    lifecycle_state: str
    stewardship_mode: str
    guardianship_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "stewardship"
    stewardship_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    guardianship_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleOversightDecision:
    status: str
    oversight_key: str
    current_stage_label: str
    lifecycle_state: str
    guardianship_mode: str
    oversight_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "guardianship"
    guardianship_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    oversight_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleAssuranceDecision:
    status: str
    assurance_key: str
    current_stage_label: str
    lifecycle_state: str
    oversight_mode: str
    assurance_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "oversight"
    oversight_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    assurance_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleAttestationDecision:
    status: str
    attestation_key: str
    current_stage_label: str
    lifecycle_state: str
    assurance_mode: str
    attestation_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "assurance"
    assurance_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    attestation_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleVerificationDecision:
    status: str
    verification_key: str
    current_stage_label: str
    lifecycle_state: str
    attestation_mode: str
    verification_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "attestation"
    attestation_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    verification_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleCertificationDecision:
    status: str
    certification_key: str
    current_stage_label: str
    lifecycle_state: str
    verification_mode: str
    certification_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "verification"
    verification_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    certification_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleConfirmationDecision:
    status: str
    confirmation_key: str
    current_stage_label: str
    lifecycle_state: str
    certification_mode: str
    confirmation_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "certification"
    certification_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    confirmation_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleRatificationDecision:
    status: str
    ratification_key: str
    current_stage_label: str
    lifecycle_state: str
    confirmation_mode: str
    ratification_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "confirmation"
    confirmation_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    ratification_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleEndorsementDecision:
    status: str
    endorsement_key: str
    current_stage_label: str
    lifecycle_state: str
    ratification_mode: str
    endorsement_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "ratification"
    ratification_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    endorsement_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleAuthorizationDecision:
    status: str
    authorization_key: str
    current_stage_label: str
    lifecycle_state: str
    endorsement_mode: str
    authorization_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "endorsement"
    endorsement_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    authorization_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleEnactmentDecision:
    status: str
    enactment_key: str
    current_stage_label: str
    lifecycle_state: str
    authorization_mode: str
    enactment_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "authorization"
    authorization_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    enactment_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleFinalityDecision:
    status: str
    finality_key: str
    current_stage_label: str
    lifecycle_state: str
    enactment_mode: str
    finality_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "enactment"
    enactment_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    finality_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleCompletionDecision:
    status: str
    completion_key: str
    current_stage_label: str
    lifecycle_state: str
    finality_mode: str
    completion_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "finality"
    finality_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    completion_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleConclusionDecision:
    status: str
    conclusion_key: str
    current_stage_label: str
    lifecycle_state: str
    completion_mode: str
    conclusion_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "completion"
    completion_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    conclusion_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleDispositionDecision:
    status: str
    disposition_key: str
    current_stage_label: str
    lifecycle_state: str
    conclusion_mode: str
    disposition_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "conclusion"
    conclusion_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    disposition_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleStandingDecision:
    status: str
    standing_key: str
    current_stage_label: str
    lifecycle_state: str
    disposition_mode: str
    standing_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "disposition"
    disposition_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    standing_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleResidencyDecision:
    status: str
    residency_key: str
    current_stage_label: str
    lifecycle_state: str
    standing_mode: str
    residency_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "standing"
    standing_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    residency_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleTenureDecision:
    status: str
    tenure_key: str
    current_stage_label: str
    lifecycle_state: str
    residency_mode: str
    tenure_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "residency"
    residency_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    tenure_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecyclePersistenceDecision:
    status: str
    persistence_key: str
    current_stage_label: str
    lifecycle_state: str
    tenure_mode: str
    persistence_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "tenure"
    tenure_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    persistence_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleDurabilityDecision:
    status: str
    durability_key: str
    current_stage_label: str
    lifecycle_state: str
    persistence_mode: str
    durability_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "persistence"
    persistence_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    durability_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleLongevityDecision:
    status: str
    longevity_key: str
    current_stage_label: str
    lifecycle_state: str
    durability_mode: str
    longevity_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "durability"
    durability_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    longevity_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleLegacyDecision:
    status: str
    legacy_key: str
    current_stage_label: str
    lifecycle_state: str
    longevity_mode: str
    legacy_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "longevity"
    longevity_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    legacy_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleHeritageDecision:
    status: str
    heritage_key: str
    current_stage_label: str
    lifecycle_state: str
    legacy_mode: str
    heritage_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "legacy"
    legacy_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    heritage_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleLineageDecision:
    status: str
    lineage_key: str
    current_stage_label: str
    lifecycle_state: str
    heritage_mode: str
    lineage_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "heritage"
    heritage_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    lineage_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleAncestryDecision:
    status: str
    ancestry_key: str
    current_stage_label: str
    lifecycle_state: str
    lineage_mode: str
    ancestry_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "lineage"
    lineage_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    ancestry_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleProvenanceDecision:
    status: str
    provenance_key: str
    current_stage_label: str
    lifecycle_state: str
    ancestry_mode: str
    provenance_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "ancestry"
    ancestry_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    provenance_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleOriginDecision:
    status: str
    origin_key: str
    current_stage_label: str
    lifecycle_state: str
    provenance_mode: str
    origin_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "provenance"
    provenance_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    origin_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleRootDecision:
    status: str
    root_key: str
    current_stage_label: str
    lifecycle_state: str
    origin_mode: str
    root_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "origin"
    origin_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    root_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleFoundationDecision:
    status: str
    foundation_key: str
    current_stage_label: str
    lifecycle_state: str
    root_mode: str
    foundation_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "root"
    root_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    foundation_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleBedrockDecision:
    status: str
    bedrock_key: str
    current_stage_label: str
    lifecycle_state: str
    foundation_mode: str
    bedrock_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "foundation"
    foundation_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    bedrock_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleSubstrateDecision:
    status: str
    substrate_key: str
    current_stage_label: str
    lifecycle_state: str
    bedrock_mode: str
    substrate_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "bedrock"
    bedrock_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    substrate_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleStratumDecision:
    status: str
    stratum_key: str
    current_stage_label: str
    lifecycle_state: str
    substrate_mode: str
    stratum_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "substrate"
    substrate_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    stratum_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ProactiveLifecycleLayerDecision:
    status: str
    layer_key: str
    current_stage_label: str
    lifecycle_state: str
    stratum_mode: str
    layer_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "stratum"
    stratum_decision: str | None = None
    active_sources: list[str] = field(default_factory=list)
    layer_notes: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ResponsePostAudit:
    status: str
    sentence_count: int
    question_count: int
    includes_validation: bool
    includes_next_step: bool
    includes_boundary_statement: bool
    includes_uncertainty_statement: bool
    violations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    approved: bool = True


@dataclass(slots=True, frozen=True)
class ResponseNormalizationResult:
    changed: bool
    trigger_status: str
    final_status: str
    trigger_violations: list[str] = field(default_factory=list)
    applied_repairs: list[str] = field(default_factory=list)
    normalized_content: str = ""
    approved: bool = True


@dataclass(slots=True, frozen=True)
class ExpressionPlan:
    tone: str
    goals: list[str]
    include_question: bool
    avoid: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class SessionDirective:
    should_reply: bool
    next_action: str
    response_style: str
    focus_points: list[str]


@dataclass(slots=True, frozen=True)
class OfflineConsolidationReport:
    summary: str
    reinforced_memories: list[str] = field(default_factory=list)
    relationship_signals: list[str] = field(default_factory=list)
    drift_flags: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    archive_candidate: bool = False
    source_turn_count: int = 0


@dataclass(slots=True, frozen=True)
class SessionSnapshot:
    snapshot_id: str
    created_at: str
    source_job_id: str
    summary: str
    fingerprint: str
    turn_count: int
    event_count: int
    latest_strategy: str | None = None
    working_memory_size: int = 0
    archive_candidate: bool = False


@dataclass(slots=True, frozen=True)
class ArchiveStatus:
    archived: bool
    archived_at: str | None = None
    reason: str | None = None
    snapshot_id: str | None = None


@dataclass(slots=True, frozen=True)
class InnerMonologueEntry:
    stage: str
    summary: str
    confidence: float
