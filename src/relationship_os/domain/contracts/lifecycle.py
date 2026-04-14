from dataclasses import dataclass, field


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
class LifecyclePhaseRecord:
    phase: str
    order: int
    status: str | None = None
    key: str | None = None
    mode: str | None = None
    decision: str | None = None
    actionability: str | None = None
    changed: bool = False
    notes: list[str] = field(default_factory=list)
    active_sources: list[str] = field(default_factory=list)
    rationale: str = ""
    attrs: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class LifecycleSnapshot:
    schema_version: int
    emission_id: str
    lifecycle_key: str
    current_stage_label: str | None
    current_stage_index: int | None
    stage_count: int | None
    dispatched: bool
    message_event_count: int
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "lifecycle"
    phases: list[LifecyclePhaseRecord] = field(default_factory=list)
