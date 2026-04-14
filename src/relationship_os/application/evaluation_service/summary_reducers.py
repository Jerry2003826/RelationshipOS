"""Single-pass reducers for evaluation session summaries."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from relationship_os.application.evaluation_service.summary_specs import (
    COLLECTION_SPECS,
    COUNT_OUTPUT_SPECS,
    LAST_TURN_ASSIGNMENTS,
    LATEST_DEFAULTS,
    LATEST_OUTPUT_SPECS,
    SUM_SPECS,
)
from relationship_os.application.evaluation_service.turn_record import (
    TurnRecord,
    _content_tokens,
    _distribution_entropy,
    _series_slope,
    _tokenize_text,
)

_MISSING = object()
_SAFE_GLOBALS: dict[str, Any] = {
    "__builtins__": {},
    "bool": bool,
    "dict": dict,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "next": next,
    "str": str,
}


def _compile_turn_expr(expression: str) -> Callable[[Any], Any]:
    if expression == "turn":
        return lambda turn: turn
    code = compile(expression, "<summary-turn-expr>", "eval")

    def _evaluate(turn: Any) -> Any:
        scope = dict(_SAFE_GLOBALS)
        scope["turn"] = turn
        return eval(code, scope, {"turn": turn})

    return _evaluate


def _compile_env_expr(expression: str) -> Callable[[dict[str, Any]], Any]:
    code = compile(expression, "<summary-last-turn-expr>", "eval")

    def _evaluate(env: dict[str, Any]) -> Any:
        scope = dict(_SAFE_GLOBALS)
        scope.update(env)
        return eval(code, scope, env)

    return _evaluate


def _spec_owner(name: str) -> str:
    if name.startswith("proactive_"):
        return "proactive"
    if name.startswith("system3_"):
        return "system3"
    if name.startswith("strategy_") or name in {
        "diversity_intervention_turns",
        "diversity_watch_turns",
        "strategy_names",
    }:
        return "strategy"
    return "core"


@dataclass(frozen=True, slots=True)
class _CompiledCollectionSpec:
    name: str
    source: str
    owner: str
    element_fn: Callable[[Any], Any]
    filter_fns: tuple[Callable[[Any], Any], ...]


@dataclass(frozen=True, slots=True)
class _CompiledCountOutputSpec:
    output_key: str
    mode: str
    source: str
    filter_fns: tuple[Callable[[Any], Any], ...]


@dataclass(frozen=True, slots=True)
class _CompiledSumSpec:
    output_key: str
    source: str
    term_fn: Callable[[Any], Any]
    filter_fns: tuple[Callable[[Any], Any], ...]


@dataclass(frozen=True, slots=True)
class _CompiledLatestOutputSpec:
    output_key: str
    variable: str
    default: Any
    round_digits: int | None


def _compile_collection_specs() -> tuple[_CompiledCollectionSpec, ...]:
    compiled: list[_CompiledCollectionSpec] = []
    for spec in COLLECTION_SPECS:
        compiled.append(
            _CompiledCollectionSpec(
                name=spec.name,
                source=spec.source,
                owner=_spec_owner(spec.name),
                element_fn=_compile_turn_expr(spec.element_expr),
                filter_fns=tuple(_compile_turn_expr(expr) for expr in spec.filter_exprs),
            )
        )
    return tuple(compiled)


def _compile_count_output_specs() -> tuple[_CompiledCountOutputSpec, ...]:
    compiled: list[_CompiledCountOutputSpec] = []
    for spec in COUNT_OUTPUT_SPECS:
        compiled.append(
            _CompiledCountOutputSpec(
                output_key=spec.output_key,
                mode=spec.mode,
                source=spec.source,
                filter_fns=tuple(_compile_turn_expr(expr) for expr in spec.filter_exprs),
            )
        )
    return tuple(compiled)


def _compile_sum_specs() -> tuple[_CompiledSumSpec, ...]:
    compiled: list[_CompiledSumSpec] = []
    for spec in SUM_SPECS:
        compiled.append(
            _CompiledSumSpec(
                output_key=spec.output_key,
                source=spec.source,
                term_fn=_compile_turn_expr(spec.term_expr),
                filter_fns=tuple(_compile_turn_expr(expr) for expr in spec.filter_exprs),
            )
        )
    return tuple(compiled)


def _compile_latest_output_specs() -> tuple[_CompiledLatestOutputSpec, ...]:
    compiled: list[_CompiledLatestOutputSpec] = []
    for spec in LATEST_OUTPUT_SPECS:
        compiled.append(
            _CompiledLatestOutputSpec(
                output_key=spec.output_key,
                variable=spec.variable,
                default=LATEST_DEFAULTS[spec.variable],
                round_digits=spec.round_digits,
            )
        )
    return tuple(compiled)


def _compile_last_turn_assignments() -> tuple[tuple[str, Callable[[dict[str, Any]], Any]], ...]:
    return tuple(
        (target, _compile_env_expr(expression))
        for target, expression in LAST_TURN_ASSIGNMENTS
    )


_COLLECTION_SPECS = _compile_collection_specs()
_COUNT_OUTPUT_SPECS = _compile_count_output_specs()
_SUM_SPECS = _compile_sum_specs()
_LATEST_OUTPUT_SPECS = _compile_latest_output_specs()
_LAST_TURN_ASSIGNMENTS = _compile_last_turn_assignments()


@dataclass(slots=True)
class CoreReducer:
    counts: dict[str, int] = field(default_factory=dict)
    safety_scores: list[float] = field(default_factory=list)

    def record_collection(self, *, name: str, value: Any) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1
        if name == "safety_scores":
            self.safety_scores.append(float(value))

    def get_count(self, name: str) -> int:
        return int(self.counts.get(name, 0))

    def avg_psychological_safety(self) -> float | None:
        if not self.safety_scores:
            return None
        return round(mean(self.safety_scores), 3)


@dataclass(slots=True)
class StrategyReducer:
    counts: dict[str, int] = field(default_factory=dict)
    strategy_names: list[str] = field(default_factory=list)

    def record_collection(self, *, name: str, value: Any) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1
        if name == "strategy_names":
            self.strategy_names.append(str(value))

    def get_count(self, name: str) -> int:
        return int(self.counts.get(name, 0))

    def strategy_diversity_index(self) -> float:
        return _distribution_entropy(self.strategy_names)

    def unique_strategy_count(self) -> int:
        return len(set(self.strategy_names))


@dataclass(slots=True)
class ProactiveReducer:
    counts: dict[str, int] = field(default_factory=dict)

    def record_collection(self, *, name: str, value: Any) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1

    def get_count(self, name: str) -> int:
        return int(self.counts.get(name, 0))


@dataclass(slots=True)
class System3Reducer:
    counts: dict[str, int] = field(default_factory=dict)

    def record_collection(self, *, name: str, value: Any) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1

    def get_count(self, name: str) -> int:
        return int(self.counts.get(name, 0))


@dataclass(slots=True)
class OutputQualityAccumulator:
    seen_content_tokens: set[str] = field(default_factory=set)
    word_counts: list[int] = field(default_factory=list)
    lexical_diversities: list[float] = field(default_factory=list)
    information_densities: list[float] = field(default_factory=list)
    opening_counts: dict[str, int] = field(default_factory=dict)

    def consume(self, turn: TurnRecord) -> None:
        if not turn.assistant_message:
            return
        tokens = _tokenize_text(turn.assistant_message)
        if not tokens:
            return
        content_tokens = _content_tokens(tokens)
        token_set = set(tokens)
        content_set = set(content_tokens)
        novel_content_tokens = content_set - self.seen_content_tokens
        information_density = (
            round(len(novel_content_tokens) / len(content_set), 3)
            if content_set
            else round(len(token_set) / len(tokens), 3)
        )
        if content_set:
            self.seen_content_tokens.update(content_set)
        opening_signature = " ".join(tokens[:3])
        if opening_signature:
            self.opening_counts[opening_signature] = (
                self.opening_counts.get(opening_signature, 0) + 1
            )
        self.word_counts.append(len(tokens))
        self.lexical_diversities.append(round(len(token_set) / len(tokens), 3))
        self.information_densities.append(information_density)

    def finalize(self) -> dict[str, Any]:
        if not self.word_counts:
            return {
                "assessed_turn_count": 0,
                "avg_response_word_count": None,
                "latest_response_word_count": None,
                "response_length_slope": 0.0,
                "avg_response_lexical_diversity": None,
                "latest_response_lexical_diversity": None,
                "response_lexical_diversity_slope": 0.0,
                "avg_response_information_density": None,
                "latest_response_information_density": None,
                "response_information_density_slope": 0.0,
                "repeated_opening_turn_count": 0,
                "output_quality_issue_count": 0,
                "output_quality_issues": [],
                "output_quality_status": "stable",
            }

        repeated_opening_turn_count = sum(
            count for count in self.opening_counts.values() if count > 1
        )
        issues: list[str] = []
        if len(self.word_counts) >= 3:
            latest_word_count = self.word_counts[-1]
            first_word_count = self.word_counts[0]
            if latest_word_count >= max(
                first_word_count + 12,
                int(first_word_count * 1.75),
            ):
                if _series_slope(self.word_counts) >= 4.0:
                    issues.append("length_bloat")
            if self.lexical_diversities[0] - self.lexical_diversities[-1] >= 0.2:
                if _series_slope(self.lexical_diversities) <= -0.05:
                    issues.append("lexical_diversity_drop")
            if self.information_densities[0] - self.information_densities[-1] >= 0.2:
                if _series_slope(self.information_densities) <= -0.05:
                    issues.append("information_density_drop")
        if repeated_opening_turn_count >= 2:
            issues.append("template_repetition")

        if len(issues) >= 2:
            status = "degrading"
        elif issues:
            status = "watch"
        else:
            status = "stable"

        return {
            "assessed_turn_count": len(self.word_counts),
            "avg_response_word_count": round(mean(self.word_counts), 3),
            "latest_response_word_count": self.word_counts[-1],
            "response_length_slope": _series_slope(self.word_counts),
            "avg_response_lexical_diversity": round(mean(self.lexical_diversities), 3),
            "latest_response_lexical_diversity": self.lexical_diversities[-1],
            "response_lexical_diversity_slope": _series_slope(self.lexical_diversities),
            "avg_response_information_density": round(
                mean(self.information_densities),
                3,
            ),
            "latest_response_information_density": self.information_densities[-1],
            "response_information_density_slope": _series_slope(
                self.information_densities
            ),
            "repeated_opening_turn_count": repeated_opening_turn_count,
            "output_quality_issue_count": len(issues),
            "output_quality_issues": issues,
            "output_quality_status": status,
        }


@dataclass(slots=True)
class SessionSummaryAccumulator:
    core: CoreReducer = field(default_factory=CoreReducer)
    strategy: StrategyReducer = field(default_factory=StrategyReducer)
    proactive: ProactiveReducer = field(default_factory=ProactiveReducer)
    system3: System3Reducer = field(default_factory=System3Reducer)
    output_quality: OutputQualityAccumulator = field(default_factory=OutputQualityAccumulator)
    sum_totals: dict[str, float | int] = field(default_factory=dict)
    inline_count_totals: dict[str, int] = field(default_factory=dict)
    turn_count: int = 0
    last_turn: TurnRecord | None = None

    def consume(self, turn: TurnRecord) -> None:
        self.turn_count += 1
        self.last_turn = turn

        context: dict[str, Any] = {"turn_records": turn}
        for spec in _COLLECTION_SPECS:
            source_value = context.get(spec.source, _MISSING)
            if source_value is _MISSING:
                context[spec.name] = _MISSING
                continue
            if not all(bool(filter_fn(source_value)) for filter_fn in spec.filter_fns):
                context[spec.name] = _MISSING
                continue
            element = spec.element_fn(source_value)
            context[spec.name] = element
            self._record_collection(owner=spec.owner, name=spec.name, value=element)

        for spec in _SUM_SPECS:
            source_value = context.get(spec.source, _MISSING)
            if source_value is _MISSING:
                continue
            if not all(bool(filter_fn(source_value)) for filter_fn in spec.filter_fns):
                continue
            self.sum_totals[spec.output_key] = (
                self.sum_totals.get(spec.output_key, 0)
                + spec.term_fn(source_value)
            )

        for spec in _COUNT_OUTPUT_SPECS:
            if spec.mode != "inline_collection":
                continue
            source_value = context.get(spec.source, _MISSING)
            if source_value is _MISSING:
                continue
            if not all(bool(filter_fn(source_value)) for filter_fn in spec.filter_fns):
                continue
            self.inline_count_totals[spec.output_key] = (
                self.inline_count_totals.get(spec.output_key, 0) + 1
            )

        self.output_quality.consume(turn)

    def to_summary(
        self,
        *,
        session_id: str,
        event_count: int,
        started_at: str | None,
        last_event_at: str | None,
        started_metadata: dict[str, Any],
        session_duration_seconds: float,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "session_id": session_id,
            "session_source": str(started_metadata.get("source", "session") or "session"),
            "event_count": event_count,
            "started_at": started_at,
            "last_event_at": last_event_at,
            "session_duration_seconds": session_duration_seconds,
            "bid_turn_toward_rate": self._bid_rate(),
            "strategy_diversity_index": self.strategy.strategy_diversity_index(),
        }
        summary["avg_seconds_per_turn"] = (
            round(session_duration_seconds / max(self.turn_count, 1), 3)
            if self.turn_count
            else None
        )
        summary["avg_psychological_safety"] = self.core.avg_psychological_safety()

        for spec in _COUNT_OUTPUT_SPECS:
            summary[spec.output_key] = self._resolve_count_output(spec)

        for spec in _SUM_SPECS:
            summary[spec.output_key] = self.sum_totals.get(spec.output_key, 0)

        latest_values = self._latest_values()
        for spec in _LATEST_OUTPUT_SPECS:
            value = spec.default
            if self.last_turn is not None:
                value = latest_values[spec.variable]
            if spec.round_digits is not None:
                value = round(float(value), spec.round_digits)
            summary[spec.output_key] = value

        quality_summary = self.output_quality.finalize()
        summary["output_quality_assessed_turn_count"] = quality_summary["assessed_turn_count"]
        summary["avg_response_word_count"] = quality_summary["avg_response_word_count"]
        summary["latest_response_word_count"] = quality_summary["latest_response_word_count"]
        summary["response_length_slope"] = quality_summary["response_length_slope"]
        summary["avg_response_lexical_diversity"] = quality_summary[
            "avg_response_lexical_diversity"
        ]
        summary["latest_response_lexical_diversity"] = quality_summary[
            "latest_response_lexical_diversity"
        ]
        summary["response_lexical_diversity_slope"] = quality_summary[
            "response_lexical_diversity_slope"
        ]
        summary["avg_response_information_density"] = quality_summary[
            "avg_response_information_density"
        ]
        summary["latest_response_information_density"] = quality_summary[
            "latest_response_information_density"
        ]
        summary["response_information_density_slope"] = quality_summary[
            "response_information_density_slope"
        ]
        summary["repeated_opening_turn_count"] = quality_summary[
            "repeated_opening_turn_count"
        ]
        summary["output_quality_issue_count"] = quality_summary["output_quality_issue_count"]
        summary["output_quality_issues"] = quality_summary["output_quality_issues"]
        summary["output_quality_status"] = quality_summary["output_quality_status"]
        return summary

    def _record_collection(self, *, owner: str, name: str, value: Any) -> None:
        if owner == "core":
            self.core.record_collection(name=name, value=value)
        elif owner == "strategy":
            self.strategy.record_collection(name=name, value=value)
        elif owner == "proactive":
            self.proactive.record_collection(name=name, value=value)
        elif owner == "system3":
            self.system3.record_collection(name=name, value=value)
        else:
            raise ValueError(f"Unknown reducer owner: {owner}")

    def _collection_count(self, name: str) -> int:
        owner = _spec_owner(name)
        if owner == "core":
            return self.core.get_count(name)
        if owner == "strategy":
            return self.strategy.get_count(name)
        if owner == "proactive":
            return self.proactive.get_count(name)
        if owner == "system3":
            return self.system3.get_count(name)
        return 0

    def _resolve_count_output(self, spec: _CompiledCountOutputSpec) -> int:
        if spec.mode == "collection":
            if spec.source == "turn_records":
                return self.turn_count
            return self._collection_count(spec.source)
        if spec.mode == "inline_collection":
            return int(self.inline_count_totals.get(spec.output_key, 0))
        if spec.mode == "unique_collection":
            if spec.source == "strategy_names":
                return self.strategy.unique_strategy_count()
            raise ValueError(f"Unsupported unique collection source: {spec.source}")
        raise ValueError(f"Unsupported count spec mode: {spec.mode}")

    def _bid_rate(self) -> float:
        bid_turn_count = self._collection_count("bid_turns")
        responded_bid_count = self._collection_count("responded_bids")
        if bid_turn_count == 0:
            return 1.0
        return round(responded_bid_count / bid_turn_count, 3)

    def _latest_values(self) -> dict[str, Any]:
        values: dict[str, Any] = dict(LATEST_DEFAULTS)
        if self.last_turn is None:
            return values
        values["last_turn"] = self.last_turn
        for target, assignment_fn in _LAST_TURN_ASSIGNMENTS:
            values[target] = assignment_fn(values)
        values.pop("last_turn", None)
        return values
