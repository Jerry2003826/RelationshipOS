from dataclasses import dataclass, field


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
