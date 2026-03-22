from dataclasses import dataclass, field


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
