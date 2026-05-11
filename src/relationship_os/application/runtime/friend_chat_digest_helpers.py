from __future__ import annotations

from typing import Any

from relationship_os.application.runtime.self_state_writer import (
    extract_relationship_markers_from_text,
    extract_state_markers_from_text,
)


def normalize_friend_chat_owner(item: dict[str, Any]) -> str:
    subject_hint = str(item.get("subject_hint", "") or "").strip()
    if subject_hint.startswith("other_user:"):
        owner = subject_hint.split(":", 1)[1].strip()
        if owner and owner != "unknown":
            if owner.casefold() == "anning":
                return "阿宁"
            return owner
    for field in ("subject_user_id", "source_user_id"):
        owner = str(item.get(field, "") or "").strip()
        if owner:
            if owner.casefold() == "anning":
                return "阿宁"
            return owner
    value = str(item.get("value", "") or "")
    for marker in ("阿宁", "小北", "林晓雨", "林"):
        if marker in value:
            return marker
    return "有人"


def normalize_friend_chat_narrative_digest(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "signals": [
                str(value).strip()
                for value in list(payload.get("signals") or [])
                if str(value).strip()
            ],
            "markers": [
                str(value).strip()
                for value in list(payload.get("markers") or [])
                if str(value).strip()
            ],
            "dominant_tone": str(payload.get("dominant_tone", "") or "").strip(),
        }
    text = str(payload or "").strip()
    return {
        "signals": [
            signal
            for signal, tokens in (
                ("tired", ("累", "没力气", "提不起劲", "提不起兴趣", "蔫", "没意思")),
                ("slow", ("慢", "磨蹭", "拖延")),
                (
                    "withdrawn",
                    ("不想回消息", "不太想回消息", "嫌麻烦", "刷手机", "发呆", "不想出门"),
                ),
                ("cluttered", ("房间", "票据", "快递盒", "没叠的衣服", "收拾")),
            )
            if any(token in text for token in tokens)
        ],
        "markers": extract_state_markers_from_text(text),
        "dominant_tone": (
            "low_energy" if any(token in text for token in ("累", "没力气", "蔫")) else ""
        ),
    }


def friend_chat_narrative_digest_values(digest: dict[str, Any]) -> list[str]:
    values = [
        f"state_signal:{str(value).strip()}"
        for value in list(digest.get("signals") or [])
        if str(value).strip()
    ]
    values.extend(
        f"state_marker:{str(value).strip()}"
        for value in list(digest.get("markers") or [])
        if str(value).strip()
    )
    dominant_tone = str(digest.get("dominant_tone", "") or "").strip()
    if dominant_tone:
        values.append(f"state_tone:{dominant_tone}")
    return values


def normalize_friend_chat_relationship_digest(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "signals": [
                str(value).strip()
                for value in list(payload.get("signals") or [])
                if str(value).strip()
            ],
            "markers": [
                str(value).strip()
                for value in list(payload.get("markers") or [])
                if str(value).strip()
            ],
            "interaction_band": str(payload.get("interaction_band", "") or "").strip(),
            "total_interactions": int(payload.get("total_interactions", 0) or 0),
        }
    text = str(payload or "").strip()
    return {
        "signals": [
            signal
            for signal, tokens in (
                ("closer", ("更熟", "熟一点")),
                ("still_here", ("还在",)),
                ("remembers_details", ("记得", "小习惯")),
                ("more_relaxed", ("放松", "松一点")),
                ("less_formal", ("端着", "普通聊天", "像聊天")),
            )
            if any(token in text for token in tokens)
        ],
        "markers": extract_relationship_markers_from_text(text),
        "interaction_band": "",
        "total_interactions": 0,
    }


def friend_chat_relationship_digest_values(digest: dict[str, Any]) -> list[str]:
    values = [
        f"relationship_signal:{str(value).strip()}"
        for value in list(digest.get("signals") or [])
        if str(value).strip()
    ]
    values.extend(
        f"relationship_marker:{str(value).strip()}"
        for value in list(digest.get("markers") or [])
        if str(value).strip()
    )
    interaction_band = str(digest.get("interaction_band", "") or "").strip()
    if interaction_band:
        values.append(f"relationship_band:{interaction_band}")
    total_interactions = int(digest.get("total_interactions", 0) or 0)
    if total_interactions > 0:
        values.append(f"relationship_interactions:{total_interactions}")
    return values
