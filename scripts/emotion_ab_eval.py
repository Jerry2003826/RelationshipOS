#!/usr/bin/env python3
"""Offline A/B harness for EmotionalExpert prompt variants (W4.2).

Purpose
-------
Turn "情感接住率 +X%" into a number that can be recomputed on any machine
without GPUs, without a retrain, and without any live traffic. Takes a
fixture file of user turns, composes two prompt variants with
``build_emotional_prompt``, asks a generator function for the reply on
each variant, and grades the replies with a pluggable rubric.

Both the generator and the rubric are callables so unit tests can pass
in stubs. When running in production you plug in an actual LLM.

Scoring
-------
Each reply gets a score in ``[0, 1]`` from three built-in rubrics:

* ``lexical``   — fraction of target emotion keywords that appear
* ``length``    — soft gaussian around a target length (too short OR
                  too long is penalised)
* ``empathy``   — pluggable rubric, default checks for at least one
                  empathetic phrase from a Chinese list

Final score per reply is a weighted average, default ``0.4/0.2/0.4``.

``catch_rate_delta = mean(scores_B) - mean(scores_A)``.

Output
------
* Prints a JSON summary to stdout (good for CI).
* With ``--output-md`` writes a Markdown report including per-turn
  scores and the A/B diff.
* Exits 2 when ``--gate`` is supplied and ``catch_rate_delta < gate``.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from relationship_os.application.analyzers.emotional_prompt import (
    EmotionalPrompt,
    build_emotional_prompt,
)

GeneratorFn = Callable[[EmotionalPrompt, str], str]
RubricFn = Callable[[str], float]


# ---------------------------------------------------------------- rubrics

_DEFAULT_EMPATHY_CUES = (
    "我懂你",
    "辛苦了",
    "不容易",
    "我在",
    "抱抱",
    "听你说",
    "陪着你",
    "没关系",
    "慢慢来",
    "你可以的",
)


def lexical_rubric(reply: str, *, targets: Iterable[str]) -> float:
    targets = [t for t in targets if t]
    if not targets:
        return 0.0
    hits = sum(1 for t in targets if t and t in reply)
    return hits / len(targets)


def length_rubric(reply: str, *, target_len: int = 60, sigma: int = 40) -> float:
    if not reply:
        return 0.0
    diff = abs(len(reply) - target_len)
    # soft gaussian, always in [0, 1]
    return math.exp(-(diff**2) / (2 * sigma**2))


def empathy_rubric(
    reply: str, *, cues: Iterable[str] = _DEFAULT_EMPATHY_CUES
) -> float:
    if not reply:
        return 0.0
    return 1.0 if any(c in reply for c in cues) else 0.0


@dataclass
class TurnResult:
    turn_id: str
    text: str
    route: str
    reply_a: str
    reply_b: str
    score_a: float
    score_b: float
    delta: float


@dataclass
class ABReport:
    turns: list[TurnResult] = field(default_factory=list)

    @property
    def mean_a(self) -> float:
        return statistics.mean(t.score_a for t in self.turns) if self.turns else 0.0

    @property
    def mean_b(self) -> float:
        return statistics.mean(t.score_b for t in self.turns) if self.turns else 0.0

    @property
    def catch_rate_delta(self) -> float:
        return self.mean_b - self.mean_a

    def win_count(self) -> tuple[int, int, int]:
        """Return (a_wins, b_wins, ties)."""
        a = b = t = 0
        for r in self.turns:
            if r.delta > 0:
                b += 1
            elif r.delta < 0:
                a += 1
            else:
                t += 1
        return a, b, t

    def to_summary(self) -> dict:
        a_wins, b_wins, ties = self.win_count()
        return {
            "turns": len(self.turns),
            "mean_a": round(self.mean_a, 4),
            "mean_b": round(self.mean_b, 4),
            "catch_rate_delta": round(self.catch_rate_delta, 4),
            "a_wins": a_wins,
            "b_wins": b_wins,
            "ties": ties,
        }


# ---------------------------------------------------------------- scoring


def score_reply(
    reply: str,
    *,
    targets: Iterable[str],
    empathy_fn: RubricFn | None = None,
    weights: tuple[float, float, float] = (0.4, 0.2, 0.4),
    target_len: int = 60,
) -> float:
    w_lex, w_len, w_emp = weights
    emp = empathy_fn or empathy_rubric
    s = (
        w_lex * lexical_rubric(reply, targets=targets)
        + w_len * length_rubric(reply, target_len=target_len)
        + w_emp * emp(reply)
    )
    # Clamp just in case a caller overrides weights to >1
    return max(0.0, min(1.0, s))


# ---------------------------------------------------------------- harness


def run_ab(
    turns: list[dict],
    *,
    prompt_a_kwargs: dict,
    prompt_b_kwargs: dict,
    generator_fn: GeneratorFn,
    empathy_fn: RubricFn | None = None,
    weights: tuple[float, float, float] = (0.4, 0.2, 0.4),
    target_len: int = 60,
) -> ABReport:
    report = ABReport()
    for i, turn in enumerate(turns):
        text = str(turn.get("text") or "").strip()
        if not text:
            continue
        turn_id = str(turn.get("turn_id") or turn.get("id") or f"t{i}")
        route = str(turn.get("route") or "LIGHT_RECALL")
        targets = list(turn.get("targets") or turn.get("emotion_tags") or [])

        prompt_a = build_emotional_prompt(route=route, **prompt_a_kwargs)
        prompt_b = build_emotional_prompt(route=route, **prompt_b_kwargs)
        reply_a = generator_fn(prompt_a, text)
        reply_b = generator_fn(prompt_b, text)

        score_a = score_reply(
            reply_a,
            targets=targets,
            empathy_fn=empathy_fn,
            weights=weights,
            target_len=target_len,
        )
        score_b = score_reply(
            reply_b,
            targets=targets,
            empathy_fn=empathy_fn,
            weights=weights,
            target_len=target_len,
        )
        report.turns.append(
            TurnResult(
                turn_id=turn_id,
                text=text,
                route=route,
                reply_a=reply_a,
                reply_b=reply_b,
                score_a=score_a,
                score_b=score_b,
                delta=score_b - score_a,
            )
        )
    return report


def _iter_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


# ---------------------------------------------------------------- render


def render_markdown(
    report: ABReport, *, label_a: str, label_b: str, gate: float | None
) -> str:
    summary = report.to_summary()
    lines = [
        "# EmotionalExpert A/B 评测",
        "",
        f"- A 组: **{label_a}**",
        f"- B 组: **{label_b}**",
        f"- 轮数: {summary['turns']}",
        f"- A 平均分: {summary['mean_a']:.3f}",
        f"- B 平均分: {summary['mean_b']:.3f}",
        f"- **catch_rate_delta**: {summary['catch_rate_delta']:+.3f}"
        f" ({summary['catch_rate_delta'] * 100:+.1f}%)",
        f"- A 赢 / B 赢 / 平: {summary['a_wins']} / "
        f"{summary['b_wins']} / {summary['ties']}",
        "",
    ]
    if gate is not None:
        badge = (
            "✅ 达到门槛" if summary["catch_rate_delta"] >= gate else "⚠️ 低于门槛"
        )
        lines.append(f"- 门槛: delta ≥ {gate:+.3f} — {badge}")
        lines.append("")
    lines.append("## Top 差异轮次")
    lines.append("")
    lines.append("| turn | route | A 分 | B 分 | delta |")
    lines.append("|---|---|---:|---:|---:|")
    top = sorted(report.turns, key=lambda r: abs(r.delta), reverse=True)[:10]
    for t in top:
        lines.append(
            f"| `{t.turn_id}` | {t.route} | "
            f"{t.score_a:.2f} | {t.score_b:.2f} | {t.delta:+.2f} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI


def _parse_kwargs(spec: str) -> dict:
    """Parse simple a=b,c=d,empty=... for prompt kwargs."""
    out: dict = {}
    if not spec:
        return out
    for pair in spec.split(","):
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k = k.strip()
        v = v.strip()
        if v.lower() in ("true", "1"):
            out[k] = True
        elif v.lower() in ("false", "0"):
            out[k] = False
        elif v.isdigit():
            out[k] = int(v)
        else:
            out[k] = v
    return out


def _default_generator_fn(model: str) -> GeneratorFn:
    import litellm  # type: ignore[import-not-found]

    def call(prompt: EmotionalPrompt, text: str) -> str:
        resp = litellm.completion(  # type: ignore[no-untyped-call]
            model=model,
            messages=[
                {"role": "system", "content": prompt.to_system_prompt()},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return str(resp["choices"][0]["message"]["content"]).strip()

    return call


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--turns", type=Path, required=True)
    p.add_argument("--persona", required=True)
    p.add_argument(
        "--a-kwargs", default="include_profile_vec=false",
        help="Comma-separated kwargs for prompt A.",
    )
    p.add_argument(
        "--b-kwargs", default="include_profile_vec=true",
        help="Comma-separated kwargs for prompt B.",
    )
    p.add_argument("--label-a", default="baseline")
    p.add_argument("--label-b", default="with_profile")
    p.add_argument("--output-md", type=Path, default=None)
    p.add_argument("--output-json", type=Path, default=None)
    p.add_argument("--model", default="deepseek-chat")
    p.add_argument(
        "--gate",
        type=float,
        default=None,
        help="Fail with exit 2 if catch_rate_delta < gate.",
    )
    args = p.parse_args(argv)

    turns = _iter_jsonl(args.turns)
    a_kwargs = _parse_kwargs(args.a_kwargs)
    b_kwargs = _parse_kwargs(args.b_kwargs)
    a_kwargs["persona"] = args.persona
    b_kwargs["persona"] = args.persona

    gen = _default_generator_fn(args.model)
    report = run_ab(
        turns,
        prompt_a_kwargs=a_kwargs,
        prompt_b_kwargs=b_kwargs,
        generator_fn=gen,
    )

    summary = report.to_summary()
    print(json.dumps(summary, ensure_ascii=False))
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(
            render_markdown(
                report, label_a=args.label_a, label_b=args.label_b, gate=args.gate
            ),
            encoding="utf-8",
        )
    if args.gate is not None and report.catch_rate_delta < args.gate:
        print(
            f"delta={report.catch_rate_delta:.4f} < gate={args.gate}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
