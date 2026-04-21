"""Vanguard Router v2 — 4-tier cascade.

Tier 0: feature extraction (RouterFeatures)
Tier 1: scored-rule engine, may short-circuit
Tier 2: calibrated classifier (logreg + isotonic) — always scored
Tier 3: mini-LLM arbiter, only when Tier 2 confidence < abstention
Fallback: rule-engine soft prior OR top-1 Tier 2 + health_degraded

Design invariants:
    * Always returns a valid RouterDecisionV2 — no exceptions leak.
    * Latency is measured in real monotonic wall-clock.
    * Shadow-log flag is set when any of:
        - Tier 1 short-circuit + Tier 2 disagrees
        - margin < 0.15
        - Tier 3 was invoked
    * Tier 3 is rate-limited by caller (via CircuitBreaker).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .circuit_breaker import BreakerOpenError, CircuitBreaker
from .contracts import ALL_ROUTES, RouterDecisionV2, RouteType, make_decision
from .features import Lexicons, RouterFeatures, extract_features, load_lexicons
from .mini_llm_arbiter import ArbiterError, LLMCallable, MiniLLMArbiter
from .rule_engine import RuleEngine, default_engine
from .tier2_classifier import PriorClassifier, Tier2Classifier, load_or_fallback

logger = logging.getLogger(__name__)


_DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "policies" / "router" / "model.joblib"


ShadowLogger = Callable[[dict], None]


@dataclass(slots=True)
class RouterConfig:
    """Runtime-tunable thresholds. Safe to hot-reload."""

    abstention_threshold: float = 0.60  # Tier 2 below this → Tier 3
    margin_threshold: float = 0.15  # below this → shadow-log
    enable_tier3: bool = True
    tier3_timeout_sec: float = 1.5
    tier3_max_latency_budget_ms: float = 1500.0
    shadow_log_sample_rate: float = 1.0  # 1.0 = log all ambiguous


@dataclass
class VanguardRouterV2:
    """Main router. Construct once per process; call `decide` per turn."""

    lexicons: Lexicons
    rule_engine: RuleEngine
    tier2: Tier2Classifier | PriorClassifier
    config: RouterConfig = field(default_factory=RouterConfig)
    arbiter: MiniLLMArbiter | None = None
    shadow_logger: ShadowLogger | None = None

    # --- convenience factory ------------------------------------------

    @classmethod
    def from_default(
        cls,
        *,
        call_llm: LLMCallable | None = None,
        model_path: Path = _DEFAULT_MODEL,
        config: RouterConfig | None = None,
        shadow_logger: ShadowLogger | None = None,
    ) -> VanguardRouterV2:
        lex = load_lexicons()
        engine = default_engine()
        tier2 = load_or_fallback(model_path)
        cfg = config or RouterConfig()
        arbiter = None
        if call_llm is not None and cfg.enable_tier3:
            breaker = CircuitBreaker(failure_threshold=3, cooldown_sec=30.0)
            arbiter = MiniLLMArbiter(
                call_llm=call_llm,
                breaker=breaker,
                timeout_sec=cfg.tier3_timeout_sec,
            )
        return cls(
            lexicons=lex,
            rule_engine=engine,
            tier2=tier2,
            config=cfg,
            arbiter=arbiter,
            shadow_logger=shadow_logger,
        )

    # --- main entry ---------------------------------------------------

    def decide(self, text: str) -> RouterDecisionV2:
        t0 = time.perf_counter()
        tier_timings: dict[str, float] = {}

        # Tier 0: features
        features = extract_features(text, self.lexicons)
        tier_timings["tier0"] = (time.perf_counter() - t0) * 1000

        # Tier 1: rules
        t1_start = time.perf_counter()
        rule_result = self.rule_engine.evaluate(text, features)
        tier_timings["tier1"] = (time.perf_counter() - t1_start) * 1000

        # Short-circuit path
        if rule_result.short_circuit is not None:
            sc = rule_result.short_circuit
            # Also compute Tier 2 (cheap) to detect disagreement → shadow log.
            t2_start = time.perf_counter()
            t2_probs = self.tier2.predict_proba(features)
            tier_timings["tier2"] = (time.perf_counter() - t2_start) * 1000

            t2_top = max(t2_probs, key=t2_probs.get)
            disagree = t2_top != sc.vote
            # Final probabilities: blend rule confidence with tier2 for
            # downstream abstention logic, keep rule class as argmax.
            probs = _fuse_probs(
                rule_class=sc.vote, rule_conf=sc.confidence, tier2=t2_probs, weight=0.75
            )
            latency = (time.perf_counter() - t0) * 1000
            decision = make_decision(
                route_type=sc.vote,
                probabilities=probs,
                decided_by="rule",
                rule_hits=rule_result.rule_hits,
                feature_scores=_top_feature_scores(self.tier2, features),
                reason=f"rule:{sc.name}",
                latency_ms=latency,
                tier_timings_ms=tier_timings,
            )
            # Mark for shadow log if Tier 2 disagrees.
            if disagree:
                self._shadow(text, features, decision, note="rule_tier2_disagree")
            return decision

        # Tier 2: classifier
        t2_start = time.perf_counter()
        t2_probs = self.tier2.predict_proba(features)
        tier_timings["tier2"] = (time.perf_counter() - t2_start) * 1000

        # Blend with rule soft prior if present.
        if rule_result.class_prior:
            t2_probs = _blend(t2_probs, rule_result.class_prior, weight=0.3)

        sorted_probs = sorted(t2_probs.values(), reverse=True)
        confidence = sorted_probs[0]
        margin = sorted_probs[0] - sorted_probs[1]
        top_class: RouteType = max(t2_probs, key=t2_probs.get)  # type: ignore[assignment]

        # Tier 3 only when ambiguous AND an arbiter is wired.
        if self.arbiter is not None and confidence < self.config.abstention_threshold:
            t3_start = time.perf_counter()
            try:
                arb = self.arbiter.arbitrate(text)
                tier_timings["tier3"] = (time.perf_counter() - t3_start) * 1000
                # Trust arbiter but keep Tier 2 distribution for explainability.
                probs = _overlay(t2_probs, arb.route_type, arb.confidence)
                latency = (time.perf_counter() - t0) * 1000
                decision = make_decision(
                    route_type=arb.route_type,
                    probabilities=probs,
                    decided_by="mini_llm",
                    rule_hits=rule_result.rule_hits,
                    feature_scores=_top_feature_scores(self.tier2, features),
                    reason=f"arbiter:{arb.why}",
                    latency_ms=latency,
                    tier_timings_ms=tier_timings,
                )
                # Shadow log Tier 3 turns for retraining.
                self._shadow(text, features, decision, note="tier3_called")
                return decision
            except (ArbiterError, BreakerOpenError) as exc:
                tier_timings["tier3"] = (time.perf_counter() - t3_start) * 1000
                logger.info("arbiter failed, falling back: %s", exc)
                latency = (time.perf_counter() - t0) * 1000
                decision = make_decision(
                    route_type=top_class,
                    probabilities=t2_probs,
                    decided_by="fallback",
                    rule_hits=rule_result.rule_hits,
                    feature_scores=_top_feature_scores(self.tier2, features),
                    reason="tier3_degraded",
                    margin=margin,
                    health_degraded=True,
                    latency_ms=latency,
                    tier_timings_ms=tier_timings,
                )
                self._shadow(text, features, decision, note="tier3_degraded")
                return decision

        # Pure Tier 2 path
        latency = (time.perf_counter() - t0) * 1000
        decision = make_decision(
            route_type=top_class,
            probabilities=t2_probs,
            decided_by="feature_clf",
            rule_hits=rule_result.rule_hits,
            feature_scores=_top_feature_scores(self.tier2, features),
            reason="tier2",
            margin=margin,
            latency_ms=latency,
            tier_timings_ms=tier_timings,
        )
        if margin < self.config.margin_threshold:
            self._shadow(text, features, decision, note="low_margin")
        return decision

    # --- helpers ------------------------------------------------------

    def _shadow(
        self,
        text: str,
        features: RouterFeatures,
        decision: RouterDecisionV2,
        *,
        note: str,
    ) -> None:
        if self.shadow_logger is None:
            return
        try:
            self.shadow_logger(
                {
                    "text": text,
                    "features": {
                        n: v
                        for n, v in zip(
                            RouterFeatures.feature_names(),
                            features.as_vector(),
                            strict=False,
                        )
                    },
                    "fired_terms": list(features.fired_terms),
                    "route_type": decision.route_type,
                    "probabilities": dict(decision.probabilities),
                    "decided_by": decision.decided_by,
                    "rule_hits": list(decision.rule_hits),
                    "confidence": decision.confidence,
                    "margin": decision.margin,
                    "latency_ms": decision.latency_ms,
                    "tier_timings_ms": dict(decision.tier_timings_ms),
                    "note": note,
                    "ts": time.time(),
                }
            )
        except Exception:  # noqa: BLE001
            logger.exception("shadow logger failed")


# --- fusion helpers -------------------------------------------------------


def _fuse_probs(
    *,
    rule_class: RouteType,
    rule_conf: float,
    tier2: dict[str, float],
    weight: float,
) -> dict[str, float]:
    """Return a distribution dominated by `rule_class` but informed by Tier 2."""
    rule_dist = {r: 0.0 for r in ALL_ROUTES}
    rule_dist[rule_class] = rule_conf
    leftover = 1.0 - rule_conf
    others = [r for r in ALL_ROUTES if r != rule_class]
    for r in others:
        rule_dist[r] = leftover / len(others)
    fused = {r: weight * rule_dist[r] + (1 - weight) * tier2[r] for r in ALL_ROUTES}
    total = sum(fused.values()) or 1.0
    return {r: fused[r] / total for r in ALL_ROUTES}


def _blend(t2: dict[str, float], prior: dict[str, float], *, weight: float) -> dict[str, float]:
    out = {r: (1 - weight) * t2.get(r, 0.0) + weight * prior.get(r, 0.0) for r in ALL_ROUTES}
    total = sum(out.values()) or 1.0
    return {r: out[r] / total for r in ALL_ROUTES}


def _overlay(t2: dict[str, float], cls: RouteType, conf: float) -> dict[str, float]:
    """Put `cls` at probability `conf`, renormalize the rest from t2."""
    mass = max(1.0 - conf, 1e-6)
    others = [r for r in ALL_ROUTES if r != cls]
    denom = sum(t2[r] for r in others) or 1.0
    out = {cls: conf}
    for r in others:
        out[r] = mass * (t2[r] / denom)
    total = sum(out.values()) or 1.0
    return {r: out[r] / total for r in ALL_ROUTES}


def _top_feature_scores(
    tier2: Tier2Classifier | PriorClassifier, features: RouterFeatures
) -> dict[str, float]:
    try:
        return tier2.top_features(features, k=5)
    except Exception:  # noqa: BLE001
        return {}
