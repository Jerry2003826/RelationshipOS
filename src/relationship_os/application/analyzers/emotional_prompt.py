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

import re
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

    # W5.3 grounded-recall guard — prevents hallucinated familiarity like
    # "我还记得你上次说不喜欢吃香菜" when no such memory card exists.
    if mem_lines:
        sections.append(
            "记忆使用守则: 只能引用上方近期记忆里出现过的内容, "
            "不要编造新的记得, 宁可说模糊印象也不要伪造具体细节"
        )
    else:
        sections.append(
            "记忆使用守则: 本轮没有可用记忆, 不要声称记得任何具体细节"
        )

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


# ---------------------------------------------------------------------------
# W5.3 Grounded-recall audit
# ---------------------------------------------------------------------------
#
# 2026-04-22 manual review caught a hallucinated familiarity case in the
# cross_session_friend_feel probe: the model said
#     "我还记得你上次说不喜欢吃香菜"
# when no memory card backed that claim.
#
# The audit below is a lightweight, structural check — it does not try to
# understand semantics, it only looks at explicit "记得/还记得 + <名词>"
# patterns in the response and checks whether any of those nouns appear in
# the upstream memory cards. Mismatches surface as soft warnings into the
# event stream (we do not block the response, the 4-stage rendering would
# eat the cost if we did).

_RECALL_CUE_PATTERN = re.compile(
    r"(?:还\s*记得|我\s*记得|记得你|印象里)[^。！？!?,，\n]{0,30}"
)

# Things we skip — they are stance / shape, not grounded facts.
_RECALL_STOPWORDS: tuple[str, ...] = (
    "你",
    "上次",
    "之前",
    "那次",
    "那天",
    "说过",
    "聊过",
    "说",
    "提过",
    "讲过",
    "一起",
    "我们",
    "的",
    "吗",
    "有点",
    "比较",
    "可能",
    "大概",
    "应该",
    "不",
    "很",
)


def _extract_memory_surface(
    records: Iterable[Mapping[str, object]] | None,
) -> str:
    if not records:
        return ""
    out: list[str] = []
    for rec in records:
        summary = str(rec.get("summary") or "").strip()
        if summary:
            out.append(summary)
        tags = rec.get("tags") or []
        if isinstance(tags, list):
            out.extend(str(t) for t in tags if str(t))
    return "\n".join(out)


def audit_unsupported_recall(
    response: str,
    recent_memory: Iterable[Mapping[str, object]] | None,
) -> list[str]:
    """Find "我记得你 X" / "还记得你 X" style claims whose X is not in memory.

    Returns
    -------
    list[str]
        Each element is a short recall phrase whose content token is not
        backed by any upstream memory card. Empty list means clean.

    Notes
    -----
    This is intentionally a *conservative* check — it only flags claims
    that use explicit recall cue words and carry at least one Chinese
    content token. It will not flag vague warmth like "感觉跟你越来越熟".
    """
    if not response:
        return []
    surface = _extract_memory_surface(recent_memory)
    flagged: list[str] = []
    for match in _RECALL_CUE_PATTERN.finditer(response):
        phrase = match.group(0)
        # Extract the content tail — everything after the cue marker up
        # to the next clause break. We strip stopwords and single chars.
        tail = re.sub(r"^(?:还\s*记得|我\s*记得|记得你|印象里)", "", phrase)
        # Split on common Chinese content breakers and look at the tail.
        content_tokens = [
            tok
            for tok in re.split(r"[\s，,。！!？?的了和与跟]", tail)
            if tok and tok not in _RECALL_STOPWORDS and len(tok) >= 2
        ]
        if not content_tokens:
            continue
        if any(_token_grounded(tok, surface) for tok in content_tokens):
            continue
        flagged.append(phrase.strip())
    return flagged


def _token_grounded(token: str, surface: str) -> bool:
    """True if any 2-char window of *token* appears inside *surface*.

    Approximate containment that tolerates extra chars like
    "通勤烦" vs "通勤很烦" — we only require at least one 2-gram
    overlap. For short tokens (<2 chars) we require exact containment.
    """
    if not surface or not token:
        return False
    if len(token) < 2:
        return token in surface
    for i in range(len(token) - 1):
        gram = token[i : i + 2]
        if gram in surface:
            return True
    return False


# ---------------------------------------------------------------------------
# W5.4 Binding-mismatch audit (v2)
# ---------------------------------------------------------------------------
#
# 2026-04-22 500-round stress caught a *binding-mismatch* hallucination
# that v1 cannot see:
#     memory:   年糕 → entity_type=pet_name (a cat)
#     response: "就像我记得你特别爱吃年糕一样"
# v1 walks memory surface char-by-char and finds "年糕" → judged grounded.
# v1 has no notion of *type* — it cannot tell that asserting
# "爱吃 X" claims X ∈ food, which is incompatible with pet_name.
#
# v2 does exactly one new thing: it indexes memory cards by declared
# entity type (pet_name / person / place / tool / brand / food / drink /
# …) and, for a small handful of explicit type-assertion patterns in the
# response, flags entities whose declared type is incompatible with the
# asserted category.
#
# This is intentionally narrow: we do *not* run NER, we do *not* do
# open-world reasoning, we only cover the shapes that have actually
# surfaced in review.  Everything else stays v1's job.

# Fields we accept on a memory card for type info. First non-empty wins.
_ENTITY_NAME_FIELDS: tuple[str, ...] = ("entity", "name", "subject", "value")
_ENTITY_TYPE_FIELDS: tuple[str, ...] = (
    "entity_type",
    "type",
    "role",
    "category",
)

# Type-assertion patterns. Each entry:
#   (compiled_pattern, asserted_category, incompatible_types)
# We detect things like "爱吃 X" which asserts X ∈ food; if memory
# declares X ∈ {pet_name, person, place, tool, brand, ...}, flag.
_INCOMPAT_WITH_FOOD: frozenset[str] = frozenset(
    {
        "pet_name",
        "pet",
        "cat",
        "cat_name",
        "dog",
        "dog_name",
        "person",
        "person_name",
        "friend",
        "colleague",
        "family",
        "place",
        "city",
        "brand",
        "tool",
        "app",
    }
)
_INCOMPAT_WITH_DRINK: frozenset[str] = _INCOMPAT_WITH_FOOD
_INCOMPAT_WITH_PERSON: frozenset[str] = frozenset(
    {"pet_name", "pet", "cat", "cat_name", "dog", "dog_name", "place", "city", "brand", "tool"}
)
_INCOMPAT_WITH_PLACE: frozenset[str] = frozenset(
    {
        "pet_name",
        "pet",
        "cat",
        "cat_name",
        "dog",
        "dog_name",
        "person",
        "person_name",
        "food",
        "drink",
        "tool",
    }
)

_TYPE_ASSERTION_PATTERNS: tuple[tuple[re.Pattern[str], str, frozenset[str]], ...] = (
    # "(特别/最)?(爱/喜欢)吃 X" → X is a food
    (
        re.compile(r"(?:特别|最|超|非常)?(?:爱|喜欢|想)吃\s*([\u4e00-\u9fa5A-Za-z]{1,10})"),
        "food",
        _INCOMPAT_WITH_FOOD,
    ),
    # "(特别/最)?(爱/喜欢)喝 X" → X is a drink
    (
        re.compile(r"(?:特别|最|超|非常)?(?:爱|喜欢|想)喝\s*([\u4e00-\u9fa5A-Za-z]{1,10})"),
        "drink",
        _INCOMPAT_WITH_DRINK,
    ),
    # "和 X 见面 / 约 X" → X is a person
    (
        re.compile(r"(?:和|跟|约)\s*([\u4e00-\u9fa5A-Za-z]{1,10})\s*(?:见面|吃饭|喝茶|约会)"),
        "person",
        _INCOMPAT_WITH_PERSON,
    ),
    # "去 X 玩 / 住在 X" → X is a place
    (
        re.compile(r"(?:去|住在|来自)\s*([\u4e00-\u9fa5A-Za-z]{1,10})\s*(?:玩|出差|旅游|定居)"),
        "place",
        _INCOMPAT_WITH_PLACE,
    ),
)


def _build_entity_type_index(
    records: Iterable[Mapping[str, object]] | None,
) -> dict[str, set[str]]:
    """Index {entity_name: {type1, type2, ...}} from memory cards.

    Only cards that declare *both* an entity name and a type contribute.
    Entity names are kept verbatim (including case for ASCII) and
    compared as prefix matches against response tokens.
    """
    index: dict[str, set[str]] = {}
    if not records:
        return index
    for rec in records:
        name = ""
        for fname in _ENTITY_NAME_FIELDS:
            value = rec.get(fname)
            if value:
                name = str(value).strip()
                if name:
                    break
        if not name:
            continue
        etype = ""
        for tname in _ENTITY_TYPE_FIELDS:
            value = rec.get(tname)
            if value:
                etype = str(value).strip().lower()
                if etype:
                    break
        if not etype:
            continue
        index.setdefault(name, set()).add(etype)
    return index


def _match_known_entity(raw: str, entity_index: Mapping[str, set[str]]) -> str:
    """Return the longest known entity that is a prefix of *raw* (or empty).

    The response regex tends to over-capture (e.g. "年糕一样"); this peels
    the real entity off the front. Longest-match avoids prefix collisions
    like "年糕" vs "年糕奶".
    """
    if not raw or not entity_index:
        return ""
    best = ""
    for entity in entity_index:
        if raw.startswith(entity) and len(entity) > len(best):
            best = entity
    return best


def audit_unsupported_recall_v2(
    response: str,
    memory_cards: Iterable[Mapping[str, object]] | None,
) -> list[dict[str, str]]:
    """Flag binding-mismatch hallucinations using memory card types.

    Complements :func:`audit_unsupported_recall`:

    * v1 — "did the model invent an entity not in memory at all?"
    * v2 — "did the model assert a type for an entity that conflicts
      with the type memory declares for it?"

    Parameters
    ----------
    response:
        Model reply text to audit.
    memory_cards:
        Iterable of memory card dicts. Cards contribute to the audit
        only when they declare both an entity name (``entity`` / ``name``
        / ``subject`` / ``value``) and a type (``entity_type`` / ``type``
        / ``role`` / ``category``). Other cards are ignored.

    Returns
    -------
    list[dict[str, str]]
        Each flag is a dict with keys ``entity``, ``asserted``,
        ``declared``, ``phrase``. Empty list means clean.

    Notes
    -----
    Like v1 this is a *soft* signal — callers should route the result
    into audit events / diagnostics, not hard-block the reply. Patterns
    are deliberately narrow (food / drink / person / place); the space
    grows as review surfaces new shapes.
    """
    if not response:
        return []
    entity_index = _build_entity_type_index(memory_cards)
    if not entity_index:
        return []
    flagged: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern, asserted_type, incompatible in _TYPE_ASSERTION_PATTERNS:
        for match in pattern.finditer(response):
            raw = match.group(1)
            entity = _match_known_entity(raw, entity_index)
            if not entity:
                continue
            declared = entity_index[entity]
            if asserted_type in declared:
                continue
            if not (declared & incompatible):
                continue
            key = (entity, asserted_type)
            if key in seen:
                continue
            seen.add(key)
            flagged.append(
                {
                    "entity": entity,
                    "asserted": asserted_type,
                    "declared": sorted(declared)[0],
                    "phrase": match.group(0).strip(),
                }
            )
    return flagged
