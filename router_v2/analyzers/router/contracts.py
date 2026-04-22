"""Router v2 contracts.

Upgrades from the legacy two-class `RouterDecision` to a three-class,
calibrated, explainable decision shape.

The three classes correspond to the three downstream pipelines already
advertised in the README (fast_reply / light_recall / deep_recall):

* ``FAST_PONG``      - no memory recall, no deep planning; short pong reply.
* ``LIGHT_RECALL``   - shallow memory lookup (working / recent) + emotional
                       color; no multi-expert reasoning.
* ``DEEP_THINK``     - full foundation + DAG planner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RouteType = Literal["FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"]
DecidedBy = Literal["rule", "feature_clf", "mini_llm", "fallback"]

ALL_ROUTES: tuple[RouteType, ...] = ("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK")


@dataclass(slots=True, frozen=True)
class RouterDecisionV2:
    """Calibrated router decision carried through the turn lifecycle.

    Designed so that downstream consumers (runtime_service) can:
    * branch on ``route_type`` for pipeline dispatch;
    * respect ``confidence`` / ``margin`` for abstention / sampling;
    * log ``rule_hits`` and ``feature_scores`` for offline inspection;
    * detect degraded state via ``health_degraded``.
    """

    # --- core routing -----------------------------------------------------
    route_type: RouteType
    """The final picked class."""

    probabilities: dict[str, float]
    """Calibrated probabilities summing to ~1.0 across ALL_ROUTES."""

    confidence: float
    """max(probabilities); usable as abstention signal."""

    margin: float
    """top1 - top2 probability gap. Low margin -> ambiguous sample."""

    # --- explainability ---------------------------------------------------
    decided_by: DecidedBy
    """Which tier produced the final decision."""

    rule_hits: tuple[str, ...] = ()
    """Names of rules that fired in Tier 1, in declaration order."""

    feature_scores: dict[str, float] = field(default_factory=dict)
    """Human-readable top-K feature contributions (name -> signed score)."""

    reason: str = ""
    """Short (<=30 char) explanation for debugging / logs."""

    # --- downstream hints -------------------------------------------------
    suggested_llm_tokens: int = 0
    """Token budget hint for the downstream pipeline's main LLM call.
    0 = use default. Router can suggest lower budgets for FAST_PONG."""

    should_shadow_log: bool = False
    """Mark ambiguous or edge-case turns for offline review."""

    health_degraded: bool = False
    """True when mini-LLM failed / breaker open / fallback used.
    Downstream MUST NOT treat degraded decisions as high-confidence."""

    # --- bookkeeping ------------------------------------------------------
    latency_ms: float = 0.0
    """End-to-end router latency; useful for p50/p95 dashboards."""

    tier_timings_ms: dict[str, float] = field(default_factory=dict)
    """Per-tier latency breakdown: {'tier0': 2.1, 'tier1': 0.3, ...}."""

    def __post_init__(self) -> None:
        # Validate probability shape at construction time; cheap and catches
        # bugs in rule engines that forget to normalize.
        if set(self.probabilities) != set(ALL_ROUTES):
            raise ValueError(
                f"probabilities must contain keys {ALL_ROUTES}, got {sorted(self.probabilities)}"
            )
        total = sum(self.probabilities.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"probabilities must sum to ~1.0, got {total:.4f}")
        if not (0.0 <= self.margin <= 1.0):
            raise ValueError(f"margin must be in [0, 1], got {self.margin}")


def make_decision(
    *,
    route_type: RouteType,
    probabilities: dict[str, float] | None = None,
    decided_by: DecidedBy,
    rule_hits: tuple[str, ...] = (),
    feature_scores: dict[str, float] | None = None,
    reason: str = "",
    margin: float | None = None,
    health_degraded: bool = False,
    latency_ms: float = 0.0,
    tier_timings_ms: dict[str, float] | None = None,
) -> RouterDecisionV2:
    """Helper to build a decision with safe defaults.

    If ``probabilities`` is not provided, we synthesize a degenerate
    one-hot distribution. This is fine for rule-hit decisions where the
    engine has no real probability; Tier 2 will always pass explicit
    probabilities.
    """

    if probabilities is None:
        probabilities = {r: (0.9 if r == route_type else 0.05) for r in ALL_ROUTES}

    sorted_probs = sorted(probabilities.values(), reverse=True)
    if margin is None:
        margin = sorted_probs[0] - sorted_probs[1]

    confidence = sorted_probs[0]

    return RouterDecisionV2(
        route_type=route_type,
        probabilities=probabilities,
        confidence=confidence,
        margin=margin,
        decided_by=decided_by,
        rule_hits=rule_hits,
        feature_scores=feature_scores or {},
        reason=reason,
        health_degraded=health_degraded,
        latency_ms=latency_ms,
        tier_timings_ms=tier_timings_ms or {},
        should_shadow_log=margin < 0.2,
    )


# --- legacy compatibility shim -----------------------------------------


@dataclass(slots=True, frozen=True)
class RouterDecision:
    """Legacy two-class decision kept for backward compatibility.

    New code should use :class:`RouterDecisionV2`. This class will emit a
    DeprecationWarning when constructed in 2026-Q3.
    """

    route_type: Literal["FAST_PONG", "NEED_DEEP_THINK"]
    reason: str
    confidence: float


def downgrade_to_legacy(decision: RouterDecisionV2) -> RouterDecision:
    """Map a v2 decision to the legacy two-class shape.

    LIGHT_RECALL falls into NEED_DEEP_THINK to preserve the legacy
    guarantee that "anything not pong goes to the deep pipeline".
    """
    legacy_type = "FAST_PONG" if decision.route_type == "FAST_PONG" else "NEED_DEEP_THINK"
    return RouterDecision(
        route_type=legacy_type,
        reason=decision.reason or decision.decided_by,
        confidence=decision.confidence,
    )
