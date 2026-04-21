"""Router v2 Tier 0 feature extractor.

Pure-Python, zero-dependency scoring over YAML lexicons. All features
are bounded to [0, 1] (or small integers) so that downstream Tier 2
classifier does not need extra scaling.

Design goals:
* **Deterministic & fast.** Single pass over the utterance, pre-compiled
  sorted patterns. No regex outside the legacy-compat shim.
* **Interpretable.** Each feature has a name; the classifier's top
  contributors can be shown to a reviewer verbatim.
* **Degradation-friendly.** Missing lexicon files yield zero-valued
  features, never crash.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - yaml is a hard dep for prod
    yaml = None  # type: ignore


LEXICON_DIR_DEFAULT = Path(__file__).resolve().parents[2] / "policies" / "router" / "lexicons"

# Short-utterance threshold (characters). Below this the sample is
# strongly biased toward FAST_PONG regardless of content.
SHORT_LEN = 4
# Very-long threshold: above this we start scaling DEEP_THINK prior.
LONG_LEN = 60


# --- dataclasses ---------------------------------------------------------


@dataclass(slots=True)
class RouterFeatures:
    """Fixed-shape numeric features fed into Tier 1 / Tier 2.

    All values are floats in [0, 1] unless marked otherwise. Order of
    the fields IS the feature-vector order for the classifier.
    """

    length_norm: float = 0.0  # len(text) capped / 120
    is_very_short: float = 0.0  # 1.0 if len<=SHORT_LEN
    is_very_long: float = 0.0  # 1.0 if len>=LONG_LEN
    has_question_mark: float = 0.0
    has_exclamation: float = 0.0
    punct_ratio: float = 0.0  # punctuation chars / total
    emoji_count: float = 0.0  # raw count, capped at 5
    repeated_char_run: float = 0.0  # longest run / 10, capped

    memory_trigger_score: float = 0.0
    persona_probe_score: float = 0.0
    emotion_intensity: float = 0.0  # signed: negation can push negative
    emotion_raw: float = 0.0  # unsigned magnitude
    self_disclosure_score: float = 0.0
    factual_query_score: float = 0.0
    entity_score: float = 0.0

    contains_crisis_term: float = 0.0  # 1.0 if any suicidality term fired
    contains_chinese: float = 0.0
    contains_latin: float = 0.0

    # bookkeeping (not fed to classifier directly; accessible via dict)
    fired_terms: tuple[str, ...] = field(default_factory=tuple)

    def as_vector(self) -> list[float]:
        """Numeric feature vector in stable order (for Tier 2)."""
        return [
            self.length_norm,
            self.is_very_short,
            self.is_very_long,
            self.has_question_mark,
            self.has_exclamation,
            self.punct_ratio,
            self.emoji_count,
            self.repeated_char_run,
            self.memory_trigger_score,
            self.persona_probe_score,
            self.emotion_intensity,
            self.emotion_raw,
            self.self_disclosure_score,
            self.factual_query_score,
            self.entity_score,
            self.contains_crisis_term,
            self.contains_chinese,
            self.contains_latin,
        ]

    @staticmethod
    def feature_names() -> list[str]:
        return [
            "length_norm",
            "is_very_short",
            "is_very_long",
            "has_question_mark",
            "has_exclamation",
            "punct_ratio",
            "emoji_count",
            "repeated_char_run",
            "memory_trigger",
            "persona_probe",
            "emotion_signed",
            "emotion_raw",
            "self_disclosure",
            "factual_query",
            "entity_score",
            "contains_crisis",
            "contains_chinese",
            "contains_latin",
        ]


# --- loader --------------------------------------------------------------


@dataclass(slots=True)
class Lexicons:
    memory: list[tuple[str, float]]
    persona: list[tuple[str, float]]
    emotion: list[tuple[str, float]]
    disclosure: list[tuple[str, float]]
    factual: list[tuple[str, float]]
    entities: list[tuple[str, float]]
    negation: list[str]
    negation_window: int = 3
    negation_multiplier: float = -0.6
    crisis_terms: frozenset[str] = field(default_factory=frozenset)


def _load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("pyyaml is required to load lexicons; install with `pip install pyyaml`")
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _weighted_entries(data: dict) -> list[tuple[str, float]]:
    entries = data.get("entries") or []
    out: list[tuple[str, float]] = []
    for e in entries:
        if isinstance(e, dict) and "form" in e:
            out.append((str(e["form"]).lower(), float(e.get("weight", 1.0))))
    # Sort by descending length so longer forms match first (greedy).
    out.sort(key=lambda t: -len(t[0]))
    return out


def load_lexicons(base_dir: Path | str | None = None) -> Lexicons:
    """Load all lexicons from disk. Missing files are tolerated."""

    base = Path(base_dir) if base_dir else LEXICON_DIR_DEFAULT
    memory = _weighted_entries(_load_yaml(base / "memory_triggers_zh.yaml"))
    persona = _weighted_entries(_load_yaml(base / "persona_probes_zh.yaml"))
    emotion = _weighted_entries(_load_yaml(base / "emotion_words_zh.yaml"))
    disclosure = _weighted_entries(_load_yaml(base / "self_disclosure_zh.yaml"))
    factual = _weighted_entries(_load_yaml(base / "factual_query_zh.yaml"))
    entities_raw = _load_yaml(base / "entities_zh.yaml")
    entities = _weighted_entries(entities_raw)

    neg_raw = _load_yaml(base / "negation_zh.yaml")
    negation = [str(x).lower() for x in (neg_raw.get("entries") or [])]
    negation.sort(key=len, reverse=True)
    negation_window = int(neg_raw.get("window_chars", 3))
    negation_multiplier = float(neg_raw.get("polarity_multiplier", -0.6))

    # Crisis subset: emotion terms with weight >= 0.95
    crisis = frozenset(form for form, w in emotion if w >= 0.95)

    return Lexicons(
        memory=memory,
        persona=persona,
        emotion=emotion,
        disclosure=disclosure,
        factual=factual,
        entities=entities,
        negation=negation,
        negation_window=negation_window,
        negation_multiplier=negation_multiplier,
        crisis_terms=crisis,
    )


# --- extractor -----------------------------------------------------------

_PUNCT_RE = re.compile(r"[\.,!?;:~\-—…。，！？；：、]")
_EMOJI_RE = re.compile(
    "[\U0001f300-\U0001f6ff\U0001f900-\U0001f9ff\U0001fa70-\U0001faff\u2600-\u27bf]"
)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace; keep original chars for offsets."""
    return text.strip().lower()


def _score_forms(
    text: str,
    forms: Iterable[tuple[str, float]],
    *,
    saturate_at: float = 1.2,
) -> tuple[float, list[str], list[tuple[int, str, float]]]:
    """Greedy substring matcher.

    Returns (saturated_score, fired_forms, positioned_hits).
    positioned_hits is [(start_idx, form, weight)] for negation handling.
    """
    hits: list[tuple[int, str, float]] = []
    total = 0.0
    for form, weight in forms:
        if not form:
            continue
        start = 0
        while True:
            idx = text.find(form, start)
            if idx < 0:
                break
            hits.append((idx, form, weight))
            total += weight
            start = idx + len(form)
    # Soft saturation so a spammy repeated trigger does not dominate.
    saturated = 1.0 - math.exp(-total / max(saturate_at, 1e-6))
    return saturated, [h[1] for h in hits], hits


def _apply_negation(
    text: str,
    hits: list[tuple[int, str, float]],
    negators: list[str],
    window: int,
    multiplier: float,
) -> float:
    """Return signed emotion score after negation flipping.

    For each emotion hit, look back up to `window` chars for any
    negator; if found, multiply that hit's weight by `multiplier`.
    """
    signed_total = 0.0
    for start, _form, weight in hits:
        w = weight
        window_start = max(0, start - window - 4)  # allow 2-char negators
        window_text = text[window_start:start]
        if any(neg in window_text for neg in negators):
            w = weight * multiplier
        signed_total += w
    # Tanh-squash to keep in [-1, 1]
    return math.tanh(signed_total / 2.0)


def extract_features(text: str, lex: Lexicons) -> RouterFeatures:
    """Main entry point. Pure function; safe to call per-turn."""

    if not text:
        return RouterFeatures()

    norm = _normalize(text)
    length = len(text)

    # --- surface features --------------------------------------------------
    length_norm = min(length / 120.0, 1.0)
    is_short = 1.0 if length <= SHORT_LEN else 0.0
    is_long = 1.0 if length >= LONG_LEN else 0.0
    q_mark = 1.0 if ("?" in text or "?" in text) else 0.0
    bang = 1.0 if ("!" in text or "!" in text) else 0.0
    punct_ratio = min(len(_PUNCT_RE.findall(text)) / max(length, 1), 1.0)
    emoji = min(float(len(_EMOJI_RE.findall(text))), 5.0) / 5.0
    # longest repeated-char run (e.g. "哈哈哈哈哈")
    run = 1
    best_run = 1
    for i in range(1, length):
        if text[i] == text[i - 1]:
            run += 1
            best_run = max(best_run, run)
        else:
            run = 1
    repeated = min(best_run / 10.0, 1.0)

    has_zh = 1.0 if _CJK_RE.search(text) else 0.0
    has_en = 1.0 if _LATIN_RE.search(text) else 0.0

    # --- lexicon scores ---------------------------------------------------
    mem_s, mem_fired, _ = _score_forms(norm, lex.memory)
    per_s, per_fired, _ = _score_forms(norm, lex.persona)
    emo_s, emo_fired, emo_hits = _score_forms(norm, lex.emotion)
    dis_s, dis_fired, _ = _score_forms(norm, lex.disclosure)
    fac_s, fac_fired, _ = _score_forms(norm, lex.factual)
    ent_s, ent_fired, _ = _score_forms(norm, lex.entities)

    emotion_signed = _apply_negation(
        norm,
        emo_hits,
        lex.negation,
        lex.negation_window,
        lex.negation_multiplier,
    )

    crisis = 1.0 if any(t in norm for t in lex.crisis_terms) else 0.0

    fired = tuple(mem_fired + per_fired + emo_fired + dis_fired + fac_fired + ent_fired)

    return RouterFeatures(
        length_norm=length_norm,
        is_very_short=is_short,
        is_very_long=is_long,
        has_question_mark=q_mark,
        has_exclamation=bang,
        punct_ratio=punct_ratio,
        emoji_count=emoji,
        repeated_char_run=repeated,
        memory_trigger_score=mem_s,
        persona_probe_score=per_s,
        emotion_intensity=emotion_signed,
        emotion_raw=emo_s,
        self_disclosure_score=dis_s,
        factual_query_score=fac_s,
        entity_score=ent_s,
        contains_crisis_term=crisis,
        contains_chinese=has_zh,
        contains_latin=has_en,
        fired_terms=fired,
    )
