"""EmotionalExpert prompt builder (W4.1).

Takes the artefacts already produced upstream — user profile prefix,
recent memory cards (PR #10 output), the shadow-log route (PR #7), and
a few emotion tags — and composes a single system prompt that the main
LLM consumes on the LIGHT_RECALL / DEEP_THINK path.

Everything is a pure function: no LLM call, no hidden state, no I/O.
That makes the A/B harness (PR #14) trivial to wire up — swap the
prompt, hold everything else constant.

Design goals
------------
* **Composable slots.** Each input has a clear responsibility and is
  optional. Missing slots degrade cleanly instead of printing literal
  ``None``.
* **Deterministic order.** Sections are always emitted in the same
  order so A/B diffs stay tiny.
* **Byte budget.** The final prompt is clipped to ``max_chars`` (default
  1600 chars ~ 800 tokens) because the context window has to hold the
  user turn, memory, and response on top.
* **No personas baked in.** Whoever ships this module supplies the
  persona string; the prompt just provides scaffolding.

Example
-------
>>> build_emotional_prompt(
...     persona="你是贴心的数字人格",
...     user_profile_prefix="profile:[0.12,0.03,...]",
...     recent_memory=[{"summary": "昨天说加班很累", "tags": ["emotion"]}],
...     route="LIGHT_RECALL",
...     emotion_tags=["sad", "tired"],
... )
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

VALID_ROUTES = {"FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"}
VALID_EMOTION_TAGS = {
    "happy",
    "sad",
    "angry",
    "tired",
    "anxious",
    "lonely",
    "excited",
    "confused",
    "grateful",
    "regretful",
}

_ROUTE_HINT = {
    "FAST_PONG": "用一到两句中文回复, 只做轻量回应, 不引用记忆",
    "LIGHT_RECALL": (
        "用 2 到 4 句中文回复, 优先用最近一次记忆卡片, 先接住情绪再给内容"
    ),
    "DEEP_THINK": (
        "用 3 到 6 句中文回复, 允许引用多条记忆卡片, 先共情再给分析或建议"
    ),
}


@dataclass
class EmotionalPrompt:
    """Structured output — keeps the raw slots for the A/B harness."""

    persona: str
    route: str
    emotion_tags: list[str]
    sections: list[str] = field(default_factory=list)
    text: str = ""

    def to_system_prompt(self) -> str:
        return self.text


def _normalise_tags(tags: Iterable[str] | None) -> list[str]:
    if not tags:
        return []
    out: list[str] = []
    for t in tags:
        t2 = str(t).strip().lower()
        if t2 in VALID_EMOTION_TAGS and t2 not in out:
            out.append(t2)
    return out[:4]


def _format_memory_lines(
    records: Iterable[Mapping[str, object]] | None,
    *,
    max_cards: int,
) -> list[str]:
    if not records:
        return []
    lines: list[str] = []
    for rec in records:
        if len(lines) >= max_cards:
            break
        summary = str(rec.get("summary") or "").strip()
        if not summary:
            continue
        tags = rec.get("tags") or []
        tag_str = ""
        if isinstance(tags, list) and tags:
            safe = [str(t) for t in tags if str(t)]
            if safe:
                tag_str = f" [{', '.join(safe[:3])}]"
        lines.append(f"- {summary}{tag_str}")
    return lines


def build_emotional_prompt(
    *,
    persona: str,
    user_profile_prefix: str | None = None,
    recent_memory: Iterable[Mapping[str, object]] | None = None,
    route: str = "LIGHT_RECALL",
    emotion_tags: Iterable[str] | None = None,
    max_memory_cards: int = 3,
    max_chars: int = 1600,
    include_profile_vec: bool = True,
) -> EmotionalPrompt:
    """Compose the system prompt for the EmotionalExpert path.

    Parameters deliberately mirror the upstream artefacts already in
    the codebase (user_profile.format_profile_prefix, PR #10 memory
    cards, PR #7 route names).
    """
    route = route.strip().upper()
    if route not in VALID_ROUTES:
        route = "LIGHT_RECALL"
    tags = _normalise_tags(emotion_tags)

    sections: list[str] = []

    persona_clean = (persona or "").strip()
    if persona_clean:
        sections.append(persona_clean)

    sections.append(f"本轮路由: {route} — {_ROUTE_HINT[route]}")

    if tags:
        sections.append(f"情感标签: {', '.join(tags)}")

    if include_profile_vec and user_profile_prefix:
        # Hard ceiling protects token budget; profile prefix is already
        # supposed to be <200 chars but we do not trust the caller.
        prefix = user_profile_prefix.strip()
        if len(prefix) > 220:
            prefix = prefix[:217] + "..."
        sections.append(f"用户画像: {prefix}")

    mem_lines = _format_memory_lines(recent_memory, max_cards=max_memory_cards)
    if mem_lines:
        sections.append("近期记忆:\n" + "\n".join(mem_lines))

    sections.append(
        "要求: 中文回复, 先接住情绪再给内容, 不要输出标签或元信息"
    )

    text = "\n\n".join(sections)
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."

    return EmotionalPrompt(
        persona=persona_clean,
        route=route,
        emotion_tags=tags,
        sections=sections,
        text=text,
    )


def diff_prompts(a: EmotionalPrompt, b: EmotionalPrompt) -> list[str]:
    """Return the section-level diff for A/B reporting."""
    out: list[str] = []
    for sec in a.sections:
        if sec not in b.sections:
            out.append(f"- A only: {sec[:80]}")
    for sec in b.sections:
        if sec not in a.sections:
            out.append(f"+ B only: {sec[:80]}")
    return out
