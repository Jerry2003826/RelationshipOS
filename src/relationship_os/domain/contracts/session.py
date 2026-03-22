from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class SessionDirective:
    should_reply: bool
    next_action: str
    response_style: str
    focus_points: list[str]


@dataclass(slots=True, frozen=True)
class InnerMonologueEntry:
    stage: str
    summary: str
    confidence: float


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
