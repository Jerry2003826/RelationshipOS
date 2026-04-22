"""L1 context alignment: dialogue act, bid signal, appraisal, topic, attention."""

from __future__ import annotations

from dataclasses import replace

from relationship_os.application.analyzers._utils import _contains_chinese
from relationship_os.application.policy_registry import get_default_compiled_policy_set
from relationship_os.domain.contracts import ContextFrame
from relationship_os.domain.contracts.turn_input import PerceptionResult, TurnInput


def _context_inference_policy() -> dict[str, object]:
    compiled = get_default_compiled_policy_set()
    if compiled is None:
        return {}
    return dict(compiled.conscience_policy.get("context_inference") or {})


def _context_section(key: str) -> dict[str, object]:
    raw = _context_inference_policy().get(key) or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _policy_list(section: str, key: str, fallback: list[str]) -> list[str]:
    section_payload = _context_section(section)
    values = section_payload.get(key)
    if isinstance(values, list):
        return [str(item) for item in values]
    return list(fallback)


def infer_dialogue_act(text: str) -> str:
    lowered = text.lower()
    question_marks = _policy_list("dialogue_act", "question_marks", ["?", "？"])
    if any(mark in text for mark in question_marks):
        return "question"
    if any(
        token in lowered
        for token in _policy_list(
            "dialogue_act",
            "request_tokens_en",
            ["help", "please", "need"],
        )
    ) or any(
        token in text
        for token in _policy_list(
            "dialogue_act",
            "request_tokens_zh",
            ["帮", "请", "需要"],
        )
    ):
        return "request"
    if any(
        token in lowered
        for token in _policy_list(
            "dialogue_act",
            "appreciation_tokens_en",
            ["thanks", "thank you"],
        )
    ) or any(
        token in text
        for token in _policy_list(
            "dialogue_act",
            "appreciation_tokens_zh",
            ["谢谢"],
        )
    ):
        return "appreciation"
    return "disclosure"


def infer_bid_signal(text: str) -> str:
    lowered = text.lower()
    if any(
        token in lowered
        for token in _policy_list(
            "bid_signal",
            "connection_request_tokens_en",
            ["feel", "alone", "stuck", "worried"],
        )
    ) or any(
        token in text
        for token in _policy_list(
            "bid_signal",
            "connection_request_tokens_zh",
            ["难过", "担心", "孤独", "卡住"],
        )
    ):
        return "connection_request"
    if any(
        token in lowered
        for token in _policy_list(
            "bid_signal",
            "soft_bid_tokens_en",
            ["share", "update"],
        )
    ) or any(
        token in text
        for token in _policy_list(
            "bid_signal",
            "soft_bid_tokens_zh",
            ["分享", "更新"],
        )
    ):
        return "soft_bid"
    return "low_signal"


def infer_appraisal(text: str) -> str:
    lowered = text.lower()
    if any(
        token in lowered
        for token in _policy_list(
            "appraisal",
            "negative_tokens_en",
            ["bad", "stuck", "angry", "sad", "anxious"],
        )
    ) or any(
        token in text
        for token in _policy_list(
            "appraisal",
            "negative_tokens_zh",
            ["糟", "难过", "焦虑", "生气", "担心", "压力"],
        )
    ):
        return "negative"
    if any(
        token in lowered
        for token in _policy_list(
            "appraisal",
            "positive_tokens_en",
            ["great", "excited", "happy", "good"],
        )
    ) or any(
        token in text
        for token in _policy_list(
            "appraisal",
            "positive_tokens_zh",
            ["开心", "兴奋", "顺利", "高兴"],
        )
    ):
        return "positive"
    return "neutral"


def infer_topic(text: str) -> str:
    lowered = text.lower()
    keyword_map = dict(_context_inference_policy().get("topic_keywords") or {})
    if not keyword_map:
        keyword_map = {
            "technical": ["api", "bug", "code", "test", "deploy"],
            "planning": ["plan", "roadmap", "next", "phase"],
            "work": ["job", "team", "meeting", "project"],
            "relationship": ["friend", "partner", "family", "关系"],
            "emotion": ["feel", "emotion", "anxious", "开心", "焦虑", "情绪"],
        }
    for topic, keywords in keyword_map.items():
        if any(keyword in lowered or keyword in text for keyword in keywords):
            return topic
    return "general"


def infer_attention(text: str) -> str:
    lowered = text.lower()
    attention_policy = _context_section("attention")
    if (
        len(text) > int(attention_policy.get("high_length_threshold", 160))
        or any(
            token in lowered
            for token in _policy_list("attention", "high_tokens_en", ["urgent", "asap"])
        )
        or any(
            token in text
            for token in _policy_list("attention", "high_tokens_zh", ["马上", "紧急", "尽快"])
        )
    ):
        return "high"
    if len(text) > int(attention_policy.get("focused_length_threshold", 60)):
        return "focused"
    return "normal"


def _fuse_appraisal(text_appraisal: str, voice_emotion: str) -> str:
    """Merge text-based appraisal with voice emotion when available."""
    negative_emotions = {"anxious", "sad", "angry", "frustrated", "fearful"}
    positive_emotions = {"excited", "happy", "joyful", "calm"}
    if voice_emotion in negative_emotions:
        return "negative"
    if voice_emotion in positive_emotions and text_appraisal != "negative":
        return "positive"
    return text_appraisal


def apply_semantic_hints(
    context_frame: ContextFrame,
    *,
    intent_label: str = "",
    appraisal: str = "",
    emotional_load: str = "",
) -> ContextFrame:
    normalized_intent = str(intent_label or "").strip()
    normalized_appraisal = str(appraisal or "").strip().lower()
    normalized_emotional_load = str(emotional_load or "").strip().lower()
    dialogue_act = context_frame.dialogue_act
    if normalized_intent in {
        "factual_recall",
        "social_disclosure",
        "presence_probe",
        "persona_state_probe",
        "state_reflection_probe",
        "relationship_reflection_probe",
    }:
        dialogue_act = "question"
    next_appraisal = (
        normalized_appraisal
        if normalized_appraisal in {"negative", "mixed", "neutral", "positive"}
        else context_frame.appraisal
    )
    bid_signal = context_frame.bid_signal
    if bid_signal == "low_signal":
        if (
            normalized_intent
            in {
                "persona_state_probe",
                "state_reflection_probe",
                "relationship_reflection_probe",
            }
            or next_appraisal in {"negative", "mixed"}
            or normalized_emotional_load == "high"
        ):
            bid_signal = "connection_request"
        elif normalized_intent == "social_disclosure":
            bid_signal = "soft_bid"
    attention = context_frame.attention
    if attention == "normal" and normalized_emotional_load == "high":
        attention = "focused"
    return replace(
        context_frame,
        dialogue_act=dialogue_act,
        appraisal=next_appraisal,
        bid_signal=bid_signal,
        attention=attention,
    )


def build_context_frame(
    text: str,
    turn_input: TurnInput | None = None,
    perception: PerceptionResult | None = None,
) -> ContextFrame:
    topic = infer_topic(text)
    common_ground = [topic]
    if _contains_chinese(text):
        common_ground.append("zh")
    if turn_input and turn_input.has_media:
        common_ground.append("multimodal")
    if perception and perception.image_descriptions:
        common_ground.append("visual_context")

    appraisal = infer_appraisal(text)
    if perception and perception.detected_emotion_from_voice:
        appraisal = _fuse_appraisal(appraisal, perception.detected_emotion_from_voice)

    return ContextFrame(
        dialogue_act=infer_dialogue_act(text),
        bid_signal=infer_bid_signal(text),
        common_ground=common_ground,
        appraisal=appraisal,
        topic=topic,
        attention=infer_attention(text),
    )
