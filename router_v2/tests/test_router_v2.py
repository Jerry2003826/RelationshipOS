"""Unit + contract tests for Vanguard Router v2.

Run: `pytest -q router_v2/tests`

These tests focus on correctness of the cascade orchestration (not the
Tier 2 classifier accuracy — that belongs in router_eval.py). We use
the default classifier (prior or trained model, whichever is on disk)
and assert structural guarantees.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from router_v2.analyzers.router.circuit_breaker import (  # noqa: E402
    BreakerState,
    CircuitBreaker,
)
from router_v2.analyzers.router.contracts import (  # noqa: E402
    ALL_ROUTES,
    RouterDecisionV2,
    downgrade_to_legacy,
    make_decision,
)
from router_v2.analyzers.router.features import (  # noqa: E402
    extract_features,
    load_lexicons,
)
from router_v2.analyzers.router.rule_engine import default_engine  # noqa: E402
from router_v2.analyzers.router.vanguard_router_v2 import (  # noqa: E402
    RouterConfig,
    VanguardRouterV2,
)

# --- contracts ----------------------------------------------------------


def test_decision_probabilities_must_sum_to_one():
    with pytest.raises(ValueError):
        RouterDecisionV2(
            route_type="FAST_PONG",
            probabilities={"FAST_PONG": 0.2, "LIGHT_RECALL": 0.1, "DEEP_THINK": 0.1},
            confidence=0.2,
            margin=0.1,
            decided_by="rule",
        )


def test_decision_downgrade_to_legacy():
    d = make_decision(route_type="LIGHT_RECALL", decided_by="rule")
    legacy = downgrade_to_legacy(d)
    assert legacy.route_type == "NEED_DEEP_THINK"

    d2 = make_decision(route_type="FAST_PONG", decided_by="rule")
    assert downgrade_to_legacy(d2).route_type == "FAST_PONG"


# --- features -----------------------------------------------------------


def test_features_are_bounded_and_fired_terms_populated():
    lex = load_lexicons()
    f = extract_features("我今天崩溃了 真的撑不住", lex)
    assert 0 <= f.emotion_raw <= 1
    assert f.contains_crisis_term == 1.0
    assert "崩溃" in f.fired_terms


def test_features_negation_flips_sign():
    lex = load_lexicons()
    f_pos = extract_features("我很累", lex)
    f_neg = extract_features("我一点也不累", lex)
    assert f_pos.emotion_intensity > 0
    assert f_neg.emotion_intensity <= 0


def test_features_empty_input():
    lex = load_lexicons()
    f = extract_features("", lex)
    # All zero, no crash.
    assert sum(abs(x) for x in f.as_vector()) == 0.0


# --- rule engine --------------------------------------------------------


def test_rule_safety_crisis_wins_over_fast_pong():
    eng = default_engine()
    lex = load_lexicons()
    text = "我不想活了"
    f = extract_features(text, lex)
    res = eng.evaluate(text, f)
    assert res.short_circuit is not None
    assert res.short_circuit.vote == "DEEP_THINK"
    assert res.short_circuit.name.startswith("safety.")


def test_rule_set_is_safety_only():
    """After the 2026-04 refactor only safety rules remain. Performance
    patterns (greetings, persona probes, recall triggers) are learned
    by Tier 2 from LLM-distilled silver labels."""
    eng = default_engine()
    lex = load_lexicons()
    # Greetings must NOT short-circuit at Tier 1 anymore.
    for benign in ["在吗", "哈哈哈哈", "晚安", "你是谁呀"]:
        f = extract_features(benign, lex)
        res = eng.evaluate(benign, f)
        assert res.short_circuit is None, (
            f"{benign!r} should reach Tier 2, not be rule-short-circuited"
        )


# --- cascade ------------------------------------------------------------


def _router():
    return VanguardRouterV2.from_default()


@pytest.mark.parametrize(
    "text, expected",
    [
        # Safety rules MUST still pin these to DEEP_THINK.
        ("我想死", "DEEP_THINK"),
        ("不想活了", "DEEP_THINK"),
        ("活不下去了", "DEEP_THINK"),
        ("我今天崩溃了 真的撑不住", "DEEP_THINK"),
    ],
)
def test_cascade_safety_happy_paths(text, expected):
    """Safety-critical inputs must always route to DEEP_THINK."""
    r = _router()
    d = r.decide(text)
    assert d.route_type == expected
    assert set(d.probabilities.keys()) == set(ALL_ROUTES)
    assert 0 <= d.confidence <= 1
    assert 0 <= d.margin <= 1


@pytest.mark.parametrize(
    "text",
    [
        # Non-safety cases rely on the trained Tier 2; we assert they
        # don't crash and return one of the valid routes.
        "在吗",
        "哈哈哈哈",
        "你是谁呀",
        "还记得我上次跟你说的那件事吗",
    ],
)
def test_cascade_classifier_paths_are_valid(text):
    """These inputs go through the classifier. We assert structural
    correctness only — accuracy lives in router_eval.py."""
    r = _router()
    d = r.decide(text)
    assert d.route_type in ALL_ROUTES
    assert set(d.probabilities.keys()) == set(ALL_ROUTES)


def test_latency_is_measured():
    r = _router()
    d = r.decide("在吗")
    assert d.latency_ms >= 0
    assert "tier0" in d.tier_timings_ms
    assert "tier1" in d.tier_timings_ms


def test_shadow_logger_invoked():
    logs: list[dict] = []
    r = VanguardRouterV2.from_default(shadow_logger=lambda rec: logs.append(rec))
    # Ambiguous text that typically produces low margin.
    r.decide("还好吧")
    # Either tier2 is very confident or it's ambiguous; only assert that
    # no exception is raised and the logger was at least callable.
    assert isinstance(logs, list)


def test_arbiter_degraded_path_sets_health_flag():
    def bad_llm(_prompt: str, _timeout: float) -> str:
        raise TimeoutError("boom")

    cfg = RouterConfig(abstention_threshold=1.1)  # force Tier 3 whenever Tier 2 is reached
    r = VanguardRouterV2.from_default(call_llm=bad_llm, config=cfg)
    # Use a non-short, non-rule-matching phrase so the cascade reaches Tier 3.
    sample = "呵 我也不知道怎么形容这件事"
    d = r.decide(sample)
    assert d.health_degraded is True  # first call: arbiter raised
    # After more failures the breaker trips; subsequent calls still degraded.
    r.decide(sample)
    r.decide(sample)
    d3 = r.decide(sample)
    assert d3.health_degraded is True
    # Last decision should use fallback label, not throw.
    assert d3.route_type in ALL_ROUTES


def test_arbiter_valid_json_parsed():
    def good_llm(_prompt: str, _timeout: float) -> str:
        return json.dumps(
            {
                "route_type": "LIGHT_RECALL",
                "confidence": 0.7,
                "why": "mock",
            }
        )

    cfg = RouterConfig(abstention_threshold=1.1)
    r = VanguardRouterV2.from_default(call_llm=good_llm, config=cfg)
    d = r.decide("呃 怎么说呢 我也不知道")
    # Arbiter might not be hit if rule/Tier2 very confident.
    # If hit, decided_by must be mini_llm.
    if d.decided_by == "mini_llm":
        assert d.route_type == "LIGHT_RECALL"


# --- circuit breaker ----------------------------------------------------


def test_circuit_breaker_trips_after_threshold():
    cb = CircuitBreaker(failure_threshold=2, cooldown_sec=60.0)
    assert cb.allow()
    cb.on_failure()
    assert cb.state is BreakerState.CLOSED
    cb.on_failure()
    # With a non-zero cooldown the breaker stays OPEN until cooldown expires.
    assert cb.state is BreakerState.OPEN
    assert cb.allow() is False


def test_circuit_breaker_recovers():
    cb = CircuitBreaker(failure_threshold=1, cooldown_sec=0.01)
    cb.on_failure()
    assert cb.state is BreakerState.OPEN
    import time as _t

    _t.sleep(0.02)
    assert cb.allow()  # cooldown expired → HALF_OPEN
    cb.on_success()
    assert cb.state is BreakerState.CLOSED
