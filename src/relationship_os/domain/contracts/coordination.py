from dataclasses import dataclass, field


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
