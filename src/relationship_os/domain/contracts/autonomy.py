from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class DriveState:
    curiosity: float
    attachment_need: float
    control_need: float
    rest_need: float
    expression_drive: float
    novelty_seeking: float
    avoidance_tension: float
    self_protection: float
    updated_at: str | None = None
    source: str = "seed"


@dataclass(slots=True, frozen=True)
class GoalRecord:
    goal_id: str
    title: str
    goal_type: str
    status: str
    priority: float
    action_type: str
    target: str
    payload: dict[str, Any] = field(default_factory=dict)
    why_now: str = ""
    risk_level: str = "low"
    reversibility: str = "high"
    source: str = "runtime"
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True, frozen=True)
class GoalState:
    latent_drives: list[str] = field(default_factory=list)
    active_goals: list[GoalRecord] = field(default_factory=list)
    unresolved_tensions: list[dict[str, Any]] = field(default_factory=list)
    goal_digest: str = ""
    updated_at: str | None = None
    source: str = "seed"


@dataclass(slots=True, frozen=True)
class SelfNarrative:
    summary: str
    recent_entries: list[dict[str, Any]] = field(default_factory=list)
    narrative_digest: str = ""
    updated_at: str | None = None
    source: str = "seed"


@dataclass(slots=True, frozen=True)
class WorldState:
    time_of_day: str
    circadian_phase: str
    sleep_pressure: float
    device: dict[str, Any] = field(default_factory=dict)
    communication: dict[str, Any] = field(default_factory=dict)
    tasks: dict[str, Any] = field(default_factory=dict)
    action_surface: dict[str, Any] = field(default_factory=dict)
    environment_appraisal: dict[str, Any] = field(default_factory=dict)
    updated_at: str | None = None
    source: str = "seed"


@dataclass(slots=True, frozen=True)
class ActionIntent:
    intent_id: str
    goal_id: str
    action_type: str
    target: str
    why_now: str
    payload: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"
    reversibility: str = "high"
    surface: str = "device"


@dataclass(slots=True, frozen=True)
class ActionPlan:
    action_id: str
    intent_id: str
    goal_id: str
    action_type: str
    target: str
    payload: dict[str, Any] = field(default_factory=dict)
    why_now: str = ""
    risk_level: str = "low"
    reversibility: str = "high"
    surface: str = "device"


@dataclass(slots=True, frozen=True)
class ExecutionGateDecision:
    action_id: str
    approved: bool
    status: str
    reason: str
    confirmation_required: bool
    risk_level: str


@dataclass(slots=True, frozen=True)
class ExecutionReceipt:
    action_id: str
    status: str
    surface: str
    adapter: str
    result: dict[str, Any] = field(default_factory=dict)
    occurred_at: str | None = None
