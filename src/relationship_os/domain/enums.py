"""Domain-level string enumerations for type-safe status values.

These enums use StrEnum so they are JSON-serializable and backward-compatible
with existing string comparisons (e.g., ``status == "stable"`` still works).
"""

from enum import StrEnum


class QueueStatus(StrEnum):
    """Proactive follow-up queue status."""

    HOLD = "hold"
    WAITING = "waiting"
    SCHEDULED = "scheduled"
    DUE = "due"
    OVERDUE = "overdue"
    EXPIRED = "expired"


class GovernanceStatus(StrEnum):
    """System 3 governance dimension status."""

    STABLE = "stable"
    WATCH = "watch"
    RECENTER = "recenter"


class TrajectoryStatus(StrEnum):
    """Governance trajectory status."""

    STABLE = "stable"
    WATCH = "watch"
    HOLD = "hold"
    ADVANCE = "advance"
    REDIRECT = "redirect"


class RepairSeverity(StrEnum):
    """Repair assessment severity level."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceLevel(StrEnum):
    """Confidence assessment level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DialogueAct(StrEnum):
    """Inferred dialogue act from user input."""

    QUESTION = "question"
    REQUEST = "request"
    APPRECIATION = "appreciation"
    DISCLOSURE = "disclosure"


class Appraisal(StrEnum):
    """Inferred emotional appraisal."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class BidSignal(StrEnum):
    """Inferred relational bid signal."""

    CONNECTION_REQUEST = "connection_request"
    SOFT_BID = "soft_bid"
    LOW_SIGNAL = "low_signal"


class AttentionLevel(StrEnum):
    """Inferred attention level from message length and urgency."""

    HIGH = "high"
    FOCUSED = "focused"
    NORMAL = "normal"


class DependencyRisk(StrEnum):
    """Relationship dependency risk level."""

    LOW = "low"
    ELEVATED = "elevated"


class AuditStatus(StrEnum):
    """Empowerment or post-audit status."""

    PASS = "pass"
    WATCH = "watch"
    REVISE = "revise"
