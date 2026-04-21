"""Tier 1 rule engine.

Evaluates a small scored-rule YAML against `RouterFeatures` + raw text
and returns either a short-circuit decision or a soft-vote bundle for
Tier 2 to consume.

Grammar supported in `when:`
    - "contains:<form>"                 (auto if when is a bare string)
    - "f.<attr> <op> <number>"          where op ∈ {<, <=, >, >=, ==, !=}
    - any_of: [<form>, ...]             (shortcut for OR of contains)
    - all: [<cond>, ...]
    - any: [<cond>, ...]
    - not: <cond>

The parser is intentionally tiny (~60 LOC) — richer DSLs are more
powerful but harder for policy owners to review.
"""

from __future__ import annotations

import operator
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

from .contracts import ALL_ROUTES, RouteType
from .features import RouterFeatures


_OPS: dict[str, Callable[[Any, Any], bool]] = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}

_F_EXPR = re.compile(
    r"^\s*f\.(?P<attr>[a-zA-Z_]+)\s*(?P<op><=|>=|==|!=|<|>)\s*(?P<num>-?\d+(\.\d+)?)\s*$"
)


@dataclass(slots=True)
class RuleVote:
    """One rule's contribution."""

    name: str
    vote: RouteType
    confidence: float
    priority: int
    override: bool


@dataclass(slots=True)
class RuleEngineResult:
    """Bundle returned to the cascade dispatcher."""

    # If set, engine wants to short-circuit: use this vote directly.
    short_circuit: RuleVote | None = None
    # All matched votes (may include short_circuit) for explainability.
    all_votes: list[RuleVote] = field(default_factory=list)
    # Soft class prior in [0, 1]^3 derived from non-override votes.
    class_prior: dict[str, float] = field(default_factory=dict)

    @property
    def rule_hits(self) -> tuple[str, ...]:
        return tuple(v.name for v in self.all_votes)


# --- condition evaluator --------------------------------------------------

def _eval_condition(cond: Any, features: RouterFeatures, text_lower: str) -> bool:
    if cond is None:
        return False
    if isinstance(cond, str):
        if cond.startswith("contains:"):
            return cond[len("contains:"):].lower() in text_lower
        m = _F_EXPR.match(cond)
        if m:
            attr = m.group("attr")
            op = _OPS[m.group("op")]
            num = float(m.group("num"))
            val = getattr(features, attr, None)
            if val is None:
                return False
            return bool(op(float(val), num))
        # Bare string → substring match (shortcut).
        return cond.lower() in text_lower
    if isinstance(cond, dict):
        if "all" in cond:
            return all(_eval_condition(c, features, text_lower) for c in cond["all"])
        if "any" in cond:
            return any(_eval_condition(c, features, text_lower) for c in cond["any"])
        if "any_of" in cond:
            return any(str(f).lower() in text_lower for f in cond["any_of"])
        if "not" in cond:
            return not _eval_condition(cond["not"], features, text_lower)
    return False


# --- engine ---------------------------------------------------------------

@dataclass(slots=True)
class RuleEngine:
    rules_path: Path
    _rules: list[dict] = field(default_factory=list)
    _confidence_threshold: float = 0.88
    _soft_weight: float = 1.0
    _mtime: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self._reload_if_changed()

    # --- hot reload -------------------------------------------------------

    def _reload_if_changed(self) -> None:
        try:
            mtime = self.rules_path.stat().st_mtime
        except FileNotFoundError:
            self._rules = []
            return
        if mtime == self._mtime:
            return
        with self._lock:
            if mtime == self._mtime:
                return
            self._load()
            self._mtime = mtime

    def _load(self) -> None:
        if yaml is None:
            raise RuntimeError("pyyaml required for rule engine")
        with self.rules_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._confidence_threshold = float(data.get("confidence_threshold", 0.88))
        self._soft_weight = float(data.get("soft_vote_weight", 1.0))
        rules = list(data.get("rules") or [])
        # Higher priority first.
        rules.sort(key=lambda r: -int(r.get("priority", 0)))
        self._rules = rules

    # --- evaluation -------------------------------------------------------

    def evaluate(self, text: str, features: RouterFeatures) -> RuleEngineResult:
        self._reload_if_changed()
        text_lower = text.lower()
        result = RuleEngineResult()
        # initialize prior
        prior = {r: 0.0 for r in ALL_ROUTES}
        short_circuit: RuleVote | None = None

        for rule in self._rules:
            cond = rule.get("when")
            if not _eval_condition(cond, features, text_lower):
                continue
            vote_cls = rule.get("vote")
            if vote_cls not in ALL_ROUTES:
                continue
            conf = float(rule.get("confidence", 0.8))
            override = bool(rule.get("override", False))
            rv = RuleVote(
                name=str(rule.get("name", "unnamed")),
                vote=vote_cls,  # type: ignore[arg-type]
                confidence=conf,
                priority=int(rule.get("priority", 0)),
                override=override,
            )
            result.all_votes.append(rv)
            if short_circuit is None and override and conf >= self._confidence_threshold:
                short_circuit = rv
            # Accumulate soft prior (override rules also contribute).
            prior[vote_cls] += conf * self._soft_weight

        # Normalize prior (if any votes cast); else leave empty for Tier 2 to
        # use a uniform prior.
        total = sum(prior.values())
        if total > 0:
            result.class_prior = {k: v / total for k, v in prior.items()}
        result.short_circuit = short_circuit
        return result


# --- convenience factory --------------------------------------------------

_DEFAULT_RULES = (
    Path(__file__).resolve().parents[2] / "policies" / "router" / "rules_zh.yaml"
)


def default_engine() -> RuleEngine:
    return RuleEngine(rules_path=_DEFAULT_RULES)
