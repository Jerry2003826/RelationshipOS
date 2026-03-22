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
