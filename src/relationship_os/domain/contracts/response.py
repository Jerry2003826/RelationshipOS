from dataclasses import dataclass, field


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
