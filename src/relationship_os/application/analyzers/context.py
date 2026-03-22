"""L1 context alignment: dialogue act, bid signal, appraisal, topic, attention."""

from relationship_os.application.analyzers._utils import _contains_chinese
from relationship_os.domain.contracts import ContextFrame


def infer_dialogue_act(text: str) -> str:
    lowered = text.lower()
    if "?" in text or "？" in text:
        return "question"
    if any(token in lowered for token in ["help", "please", "need"]) or any(
        token in text for token in ["帮", "请", "需要"]
    ):
        return "request"
    if any(token in lowered for token in ["thanks", "thank you"]) or "谢谢" in text:
        return "appreciation"
    return "disclosure"


def infer_bid_signal(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["feel", "alone", "stuck", "worried"]) or any(
        token in text for token in ["难过", "担心", "孤独", "卡住"]
    ):
        return "connection_request"
    if any(token in lowered for token in ["share", "update"]) or any(
        token in text for token in ["分享", "更新"]
    ):
        return "soft_bid"
    return "low_signal"


def infer_appraisal(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["bad", "stuck", "angry", "sad", "anxious"]) or any(
        token in text for token in ["糟", "难过", "焦虑", "生气", "担心", "压力"]
    ):
        return "negative"
    if any(token in lowered for token in ["great", "excited", "happy", "good"]) or any(
        token in text for token in ["开心", "兴奋", "顺利", "高兴"]
    ):
        return "positive"
    return "neutral"


def infer_topic(text: str) -> str:
    lowered = text.lower()
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
    if len(text) > 160 or any(token in lowered for token in ["urgent", "asap"]) or any(
        token in text for token in ["马上", "紧急", "尽快"]
    ):
        return "high"
    if len(text) > 60:
        return "focused"
    return "normal"


def build_context_frame(text: str) -> ContextFrame:
    topic = infer_topic(text)
    common_ground = [topic]
    if _contains_chinese(text):
        common_ground.append("zh")
    return ContextFrame(
        dialogue_act=infer_dialogue_act(text),
        bid_signal=infer_bid_signal(text),
        common_ground=common_ground,
        appraisal=infer_appraisal(text),
        topic=topic,
        attention=infer_attention(text),
    )
