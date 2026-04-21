from dataclasses import dataclass, field


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
    actuation_from_preset: bool = False


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
    stage_progressions: list[ProactiveStageProgressionDirective] = field(default_factory=list)
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
class StageParameterProfile:
    """Learned parameters for a specific proactive stage."""

    stage_label: str
    learned_extra_delay_seconds: int = 0
    learned_delivery_mode: str = "none"
    learned_pressure_mode: str = "none"
    confidence: float = 0.0
    sample_count: int = 0
