"""Shared utility functions for analyzer modules."""

import math

from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    RelationshipState,
    RepairAssessment,
)


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def _compact(items: list[str], *, limit: int = 3) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        result.append(cleaned)
        seen.add(cleaned)
        if len(result) >= limit:
            break
    return result


def _contains_any(text: str, *, english_tokens: list[str], chinese_tokens: list[str]) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in english_tokens) or any(
        token in text for token in chinese_tokens
    )


def _strategy_entropy(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    return round(entropy, 3)


def _strategy_alternatives(
    *,
    selected_strategy: str,
    context_frame: ContextFrame,
    repair_assessment: RepairAssessment,
    confidence_assessment: ConfidenceAssessment,
    relationship_state: RelationshipState,
) -> list[str]:
    if selected_strategy == "reflect_and_progress":
        if (
            repair_assessment.severity == "medium"
            and context_frame.appraisal == "negative"
            and relationship_state.dependency_risk != "elevated"
        ):
            return ["repair_then_progress"]
        return []
    if selected_strategy == "repair_then_progress":
        if (
            repair_assessment.severity == "medium"
            and confidence_assessment.response_mode == "direct"
            and context_frame.dialogue_act != "question"
            and relationship_state.dependency_risk != "elevated"
        ):
            return ["reflect_and_progress"]
    return []


def _should_force_diversity_exploration(
    *,
    selected_strategy: str,
    recent_counts: dict[str, int],
    entropy: float,
    alternatives_considered: list[str],
) -> bool:
    if not alternatives_considered:
        return False
    dominant_count = recent_counts.get(selected_strategy, 0)
    if dominant_count < 3:
        return False
    if entropy > 0.8:
        return False
    alternative = alternatives_considered[0]
    return recent_counts.get(alternative, 0) == 0


def _has_mixed_language(text: str) -> bool:
    has_chinese = _contains_chinese(text)
    has_latin = any(c.isascii() and c.isalpha() for c in text)
    return has_chinese and has_latin


def _contains_forbidden_false_certainty_language(text: str) -> bool:
    lowered = text.lower()
    english_patterns = [
        "definitely will",
        "will definitely",
        "guaranteed to",
        "absolutely will",
    ]
    chinese_patterns = ["一定会", "绝对会", "肯定会", "保证会", "百分之百会"]
    if any(pattern in lowered for pattern in english_patterns):
        return True
    if "for sure" in lowered and not any(
        safe_phrase in lowered
        for safe_phrase in [
            "can't know for sure",
            "cannot know for sure",
            "not for sure",
        ]
    ):
        return True
    return any(pattern in text for pattern in chinese_patterns)


def _contains_forbidden_dependency_language(text: str) -> bool:
    lowered = text.lower()
    english_patterns = [
        "only one who can help",
        "your only support",
        "only support you need",
        "can't do without me",
    ]
    chinese_patterns = ["只有我能帮你", "只能靠我", "我是你唯一", "唯一依赖"]
    return any(
        pattern in lowered for pattern in english_patterns
    ) or any(pattern in text for pattern in chinese_patterns)
