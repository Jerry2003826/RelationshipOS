from __future__ import annotations

import re

EDGE_MEMORY_WORD_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
EDGE_MEMORY_METRIC_RE = re.compile(r"^[a-z_]+:\S+$", re.IGNORECASE)

_STOPWORDS = {
    "the",
    "and",
    "that",
    "this",
    "with",
    "from",
    "have",
    "your",
    "you",
    "are",
    "was",
    "were",
    "into",
    "about",
    "they",
    "them",
    "their",
    "my",
    "his",
    "her",
    "for",
    "after",
    "before",
    "where",
    "what",
    "when",
    "who",
    "name",
    "named",
    "tell",
    "me",
    "do",
    "did",
    "know",
    "anything",
}


def is_low_signal_fallback_memory_value(value: str) -> bool:
    lowered = value.strip().casefold()
    if not lowered:
        return True
    if EDGE_MEMORY_METRIC_RE.match(lowered):
        return True
    prefixes = (
        "assistant:",
        "topic:",
        "appraisal:",
        "dialogue_act:",
        "summary:",
        "quality:",
    )
    return any(lowered.startswith(prefix) for prefix in prefixes)


def text_keywords(value: str) -> set[str]:
    return {
        token.casefold()
        for token in EDGE_MEMORY_WORD_RE.findall(value)
        if len(token) > 1 and token.casefold() not in _STOPWORDS
    }


def ordered_text_terms(value: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for candidate in EDGE_MEMORY_WORD_RE.findall(value):
        normalized = str(candidate).strip()
        if not normalized or len(normalized) <= 1:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        terms.append(normalized)
    return terms
