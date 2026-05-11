from __future__ import annotations

from typing import Any

from relationship_os.application.user_service import _user_stream_id
from relationship_os.domain.event_types import SELF_STATE_UPDATED
from relationship_os.domain.events import NewEvent, utc_now


def normalize_state_reflection_fragment(candidate: str) -> str:
    text = str(candidate or "").strip("。！？；;，, ")
    if "不想回消息" in text:
        return "不想回消息"
    if "不太想回消息" in text or "懒得回消息" in text:
        return "不想回消息"
    if ("不太想回" in text or "不想回" in text or "懒得回" in text) and (
        "消息" in text or "回复" in text or "回你" in text or "拖着" in text
    ):
        return "不想回消息"
    if "回消息" in text and any(
        token in text for token in ("费劲", "拖到", "懒得", "不想", "打几个字就觉得累")
    ):
        return "不想回消息"
    if "不想说太满" in text or "不想说满" in text:
        return "不想说太满"
    if "慢" in text and any(token in text for token in ("状态", "慢慢", "做很久", "磨蹭", "拖")):
        return "慢"
    if "不太想动" in text:
        return "不太想动"
    if "刷手机" in text:
        return "刷手机"
    if "出门" in text and "嫌麻烦" in text:
        return "出门嫌麻烦"
    if "嫌麻烦" in text:
        return "嫌麻烦"
    if "发呆" in text:
        return "发呆"
    if "累" in text:
        return "累"
    if "没力气" in text:
        return "没力气"
    if "没意思" in text:
        return "没意思"
    return text


def extract_state_markers_from_text(text: str) -> list[str]:
    markers: list[str] = []
    raw_text = str(text or "")
    normalized = normalize_state_reflection_fragment(raw_text)
    if normalized != raw_text.strip("。！？；;，, "):
        markers.append(normalized)
    if "不太想动" in raw_text and "不太想动" not in markers:
        markers.append("不太想动")
    if "刷手机" in raw_text and "刷手机" not in markers:
        markers.append("刷手机")
    if "出门" in raw_text and "嫌麻烦" in raw_text and "出门嫌麻烦" not in markers:
        markers.append("出门嫌麻烦")
    if "不太想回消息" in raw_text and "不太想回消息" not in markers:
        markers.append("不太想回消息")
    if "不想回消息" in raw_text and "不想回消息" not in markers:
        markers.append("不想回消息")
    if "慢" in raw_text and "慢" not in markers:
        markers.append("慢")
    if "累" in raw_text and "累" not in markers:
        markers.append("累")
    if "没力气" in raw_text and "没力气" not in markers:
        markers.append("没力气")
    return markers[:3]


def extract_relationship_markers_from_text(text: str) -> list[str]:
    markers: list[str] = []
    raw_text = str(text or "")
    if "端着" in raw_text:
        markers.append("端着")
    if "普通聊天" in raw_text or "像聊天" in raw_text:
        markers.append("普通聊天")
    if "记得" in raw_text and "小习惯" in raw_text:
        markers.append("记得小习惯")
    elif "记得" in raw_text:
        markers.append("记得")
    if "还在" in raw_text:
        markers.append("还在")
    if "放松" in raw_text or "松一点" in raw_text:
        markers.append("放松一点")
    return markers[:4]


class SelfStateWriter:
    def __init__(self, *, stream_service: Any) -> None:
        self._stream_service = stream_service

    async def write(
        self,
        *,
        session_id: str,
        user_id: str,
        user_message: str,
        analysis: Any,
        reply_artifacts: Any,
    ) -> None:
        """Write a SELF_STATE_UPDATED event to the user stream after each turn."""
        del reply_artifacts

        ctx = analysis.context_frame
        topic = str(getattr(ctx, "topic", "")) or None
        appraisal = str(getattr(ctx, "appraisal", "")) or None
        emotional_tone: str | None = None
        my_stance: str | None = None

        rel = analysis.relationship_state
        if rel is not None:
            emotional_tone = str(getattr(rel, "emotional_tone", "") or "")
            if not emotional_tone:
                emotional_tone = None

        open_threads: list[str] = []
        if topic:
            open_threads.append(topic)

        strat = analysis.strategy_decision
        if strat is not None:
            my_stance = str(getattr(strat, "next_action", "") or "") or None

        relationship_snapshot = {
            "last_topic": topic,
            "emotional_tone": emotional_tone or appraisal,
            "open_threads": open_threads,
            "my_stance": my_stance,
            "user_state_markers": extract_state_markers_from_text(user_message),
            "relationship_markers": extract_relationship_markers_from_text(user_message),
            "user_message_excerpt": str(user_message or "").strip()[:220],
        }

        await self._stream_service.append_events(
            stream_id=_user_stream_id(user_id),
            expected_version=None,
            events=[
                NewEvent(
                    event_type=SELF_STATE_UPDATED,
                    payload={
                        "user_id": user_id,
                        "session_id": session_id,
                        "occurred_at": utc_now().isoformat(),
                        "relationship_snapshot": relationship_snapshot,
                    },
                )
            ],
        )
