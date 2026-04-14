"""SelfStateProjector — tracks AI's relationship state with a user across sessions."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from relationship_os.domain.event_types import SELF_STATE_UPDATED
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector

_MAX_RECENT_SESSIONS = 5
_HOMETOWN_PATTERNS = (
    re.compile(r"在(?P<value>[\u4e00-\u9fffA-Za-z]{1,12})长大"),
    re.compile(r"老家在(?P<value>[\u4e00-\u9fffA-Za-z]{1,12})"),
    re.compile(r"grew up in (?P<value>[A-Za-z][A-Za-z\\s-]{1,24})", re.IGNORECASE),
)
_PET_PATTERNS = (
    re.compile(
        r"(?:我那只|我的)?(?P<kind>猫|狗|宠物)[^。！？!?,，]{0,12}?叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"
    ),
    re.compile(
        r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})是(?:我|她|他)那只(?P<kind>猫|狗|宠物)"
    ),
    re.compile(r"I have a .*? named (?P<name>[A-Za-z][A-Za-z\\s-]{0,20})", re.IGNORECASE),
)
_DRINK_TOKENS = ("拿铁", "咖啡", "奶茶", "茶", "美式", "卡布奇诺", "榛子", "drink")
_COMMUNICATION_TOKENS = (
    "别发",
    "语音",
    "长语音",
    "语音条",
    "大道理",
    "别讲",
    "别一下子",
    "别太长",
)
_LIVING_TOKENS = (
    "楼上",
    "拖椅子",
    "房间",
    "票据",
    "快递盒",
    "没叠的衣服",
    "公寓",
    "窗边",
)
_STATE_BUCKETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "tired",
        ("累", "没力气", "提不起劲", "提不起兴趣", "不想动", "蔫", "没意思", "低低的"),
    ),
    ("slow", ("慢", "磨蹭", "拖延", "做很久", "拖着", "磨着")),
    (
        "withdrawn",
        (
            "不想回消息",
            "不太想回消息",
            "不想看",
            "不想解释",
            "嫌麻烦",
            "不想出门",
            "刷手机",
            "发呆",
            "静音",
        ),
    ),
    ("cluttered", ("房间", "票据", "快递盒", "没叠的衣服", "收拾")),
)

_RELATIONSHIP_SIGNAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("still_here", ("还在",)),
    ("remembers_details", ("记得", "小习惯")),
    ("more_relaxed", ("放松", "松一点")),
    ("less_formal", ("端着", "普通聊天", "像聊天")),
)


def _collect_recent_session_texts(recent_sessions: list[dict[str, Any]]) -> list[str]:
    texts: list[str] = []
    for entry in recent_sessions[-_MAX_RECENT_SESSIONS:]:
        if not isinstance(entry, dict):
            continue
        for field in ("recent_user_messages", "user_state_markers", "relationship_markers"):
            for value in list(entry.get(field) or []):
                text = str(value).strip()
                if text:
                    texts.append(text)
    return texts


def _merge_unique_strings(*groups: list[str], limit: int = 6) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            text = str(value).strip()
            if not text:
                continue
            normalized = text.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            merged.append(text)
            if len(merged) >= limit:
                return merged
    return merged


def _extract_fact_slot_digest(
    recent_sessions: list[dict[str, Any]],
    *,
    previous_digest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hometown = ""
    pet_name = ""
    pet_kind = ""
    drink_preference = ""
    communication_preference = ""
    living_facts: list[str] = []
    texts = _collect_recent_session_texts(recent_sessions)

    for text in texts:
        if not hometown:
            for pattern in _HOMETOWN_PATTERNS:
                match = pattern.search(text)
                if match:
                    value = str(match.group("value") or "").strip("。！？!?,， ")
                    if value:
                        hometown = value
                        break
        if not pet_name:
            for pattern in _PET_PATTERNS:
                match = pattern.search(text)
                if match:
                    name = str(match.group("name") or "").strip("。！？!?,， ")
                    kind = str(match.groupdict().get("kind") or "宠物").strip()
                    if name:
                        pet_name = name
                        pet_kind = kind
                        break
        if not drink_preference and any(token in text for token in _DRINK_TOKENS):
            if "榛子拿铁" in text:
                drink_preference = "榛子拿铁"
            else:
                for token in ("拿铁", "奶茶", "美式", "卡布奇诺", "咖啡", "茶"):
                    if token in text:
                        drink_preference = token
                        break
                if not drink_preference:
                    drink_preference = text.strip("。！？!?,， ")
        if not communication_preference and any(token in text for token in _COMMUNICATION_TOKENS):
            if (
                ("语音" in text or "长语音" in text or "语音条" in text)
                and any(
                    token in text
                    for token in ("别发", "别给我发", "不爱", "怕", "不喜欢", "别太长", "太长")
                )
            ):
                communication_preference = "别发太长语音"
            elif "大道理" in text:
                communication_preference = "别讲大道理"
            else:
                communication_preference = text.strip("。！？!?,， ")
        if len(living_facts) < 2 and any(token in text for token in _LIVING_TOKENS):
            living_facts.append(text.strip("。！？!?,， "))

    previous = previous_digest or {}
    if not hometown:
        hometown = str(previous.get("hometown", "") or "").strip()
    if not pet_name:
        pet_name = str(previous.get("pet_name", "") or "").strip()
        if pet_name:
            pet_kind = str(previous.get("pet_kind", "") or "").strip() or pet_kind
    if not drink_preference:
        drink_preference = str(previous.get("drink_preference", "") or "").strip()
    if not communication_preference:
        communication_preference = str(
            previous.get("communication_preference", "") or ""
        ).strip()
    living_facts = _merge_unique_strings(
        living_facts,
        list(previous.get("living_facts") or []),
        limit=3,
    )

    stable_slots = _merge_unique_strings(
        list(previous.get("stable_slots") or []),
        [
        slot
        for slot, value in (
            ("hometown", hometown),
            ("pet", pet_name),
            ("drink_preference", drink_preference),
            ("communication_preference", communication_preference),
        )
        if value
        ],
        limit=6,
    )
    return {
        "hometown": hometown,
        "pet_name": pet_name,
        "pet_kind": pet_kind,
        "drink_preference": drink_preference,
        "communication_preference": communication_preference,
        "living_facts": living_facts[:3],
        "stable_slots": stable_slots,
    }


def _extract_narrative_digest(
    recent_sessions: list[dict[str, Any]],
    *,
    previous_digest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    joined = " ".join(_collect_recent_session_texts(recent_sessions))
    signals: list[str] = []
    for bucket, tokens in _STATE_BUCKETS:
        if any(token in joined for token in tokens):
            signals.append(bucket)
    markers: list[str] = []
    for entry in recent_sessions[-3:]:
        if not isinstance(entry, dict):
            continue
        markers.extend(
            str(value).strip()
            for value in list(entry.get("user_state_markers") or [])
            if str(value).strip()
        )
    previous = previous_digest or {}
    signals = _merge_unique_strings(
        signals,
        list(previous.get("signals") or []),
        limit=5,
    )
    markers = _merge_unique_strings(
        markers,
        list(previous.get("markers") or []),
        limit=6,
    )
    dominant_tone = "steady"
    previous_tone = str(previous.get("dominant_tone", "") or "").strip()
    if any(signal in signals for signal in ("tired", "withdrawn")):
        dominant_tone = "low_energy"
    elif "cluttered" in signals:
        dominant_tone = "disorganized"
    elif "slow" in signals:
        dominant_tone = "slowed"
    elif previous_tone:
        dominant_tone = previous_tone
    return {
        "signals": signals[:5],
        "markers": markers[:6],
        "dominant_tone": dominant_tone,
    }


def _extract_relationship_digest(
    recent_sessions: list[dict[str, Any]],
    *,
    total_interactions: int,
    previous_digest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    joined = " ".join(_collect_recent_session_texts(recent_sessions))
    signals: list[str] = []
    if total_interactions >= 2:
        signals.append("closer")
    if "还在" in joined or total_interactions >= 2:
        signals.append("still_here")
    if "记得" in joined or "小习惯" in joined or total_interactions >= 2:
        signals.append("remembers_details")
    if "放松" in joined or "松一点" in joined:
        signals.append("more_relaxed")
    elif "端着" in joined or total_interactions >= 4:
        signals.append("less_formal")
    for signal, tokens in _RELATIONSHIP_SIGNAL_RULES:
        if signal in signals:
            continue
        if any(token in joined for token in tokens):
            signals.append(signal)
    markers: list[str] = []
    for entry in recent_sessions[-3:]:
        if not isinstance(entry, dict):
            continue
        markers.extend(
            str(value).strip()
            for value in list(entry.get("relationship_markers") or [])
            if str(value).strip()
        )
    previous = previous_digest or {}
    signals = _merge_unique_strings(
        signals,
        list(previous.get("signals") or []),
        limit=6,
    )
    markers = _merge_unique_strings(
        markers,
        list(previous.get("markers") or []),
        limit=6,
    )
    if total_interactions >= 4:
        interaction_band = "warm"
    elif total_interactions >= 2:
        interaction_band = "warming"
    elif total_interactions >= 1:
        interaction_band = "early"
    else:
        interaction_band = "new"
    return {
        "signals": signals[:6],
        "markers": markers[:6],
        "interaction_band": interaction_band,
        "total_interactions": total_interactions,
    }


def _build_probe_snapshot(
    *,
    fact_slot_digest: dict[str, Any],
    narrative_digest: dict[str, Any],
    relationship_digest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "factual_slots": {
            "hometown": str(fact_slot_digest.get("hometown", "") or "").strip(),
            "pet_name": str(fact_slot_digest.get("pet_name", "") or "").strip(),
            "pet_kind": str(fact_slot_digest.get("pet_kind", "") or "").strip(),
            "drink_preference": str(fact_slot_digest.get("drink_preference", "") or "").strip(),
            "communication_preference": str(
                fact_slot_digest.get("communication_preference", "") or ""
            ).strip(),
            "living_facts": list(fact_slot_digest.get("living_facts") or [])[:3],
            "stable_slots": list(fact_slot_digest.get("stable_slots") or [])[:6],
        },
        "state_snapshot": {
            "signals": list(narrative_digest.get("signals") or [])[:6],
            "markers": list(narrative_digest.get("markers") or [])[:6],
            "dominant_tone": str(narrative_digest.get("dominant_tone", "") or "").strip(),
        },
        "relationship_snapshot": {
            "signals": list(relationship_digest.get("signals") or [])[:6],
            "markers": list(relationship_digest.get("markers") or [])[:6],
            "interaction_band": str(
                relationship_digest.get("interaction_band", "") or ""
            ).strip(),
            "total_interactions": int(relationship_digest.get("total_interactions", 0) or 0),
        },
        "social_snapshot": {
            "subject_token": "",
            "entity_token": "",
            "disclosure_posture": "",
            "source_user_id": "",
        },
    }


def _merge_unique_texts(*groups: list[str], limit: int = 6) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            text = str(value).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
            if len(merged) >= limit:
                return merged
    return merged


def _days_since(iso_ts: str | None) -> float | None:
    """Return fractional days since an ISO timestamp, or None."""
    if not iso_ts:
        return None
    try:
        then = datetime.fromisoformat(iso_ts)
        now = datetime.now(tz=UTC)
        delta = now - then
        return round(delta.total_seconds() / 86400, 1)
    except Exception:
        return None


class SelfStateProjector(Projector[dict[str, Any]]):
    """Projects a user stream into the AI's relationship self-state.

    Stream ID convention: ``user:{user_id}``

    Tracks:
    - When the AI last interacted with this person
    - Open threads (topics left unresolved)
    - Relationship tone in recent sessions
    - A rolling summary of recent sessions
    """

    name = "self-state"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "user_id": None,
            "last_interaction_at": None,
            "days_since_last_chat": None,
            "open_threads": [],
            "relationship_tone": None,
            "recent_sessions_summary": [],
            "total_interactions": 0,
            "fact_slot_digest": {
                "hometown": "",
                "pet_name": "",
                "pet_kind": "",
                "drink_preference": "",
                "communication_preference": "",
                "living_facts": [],
                "stable_slots": [],
            },
            "narrative_digest": {
                "signals": [],
                "markers": [],
                "dominant_tone": "steady",
            },
            "relationship_digest": {
                "signals": [],
                "markers": [],
                "interaction_band": "new",
                "total_interactions": 0,
            },
            "probe_snapshot": {
                "factual_slots": {},
                "state_snapshot": {},
                "relationship_snapshot": {},
                "social_snapshot": {},
            },
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        if event.event_type != SELF_STATE_UPDATED:
            return state

        p = event.payload
        snapshot = p.get("relationship_snapshot", {})
        session_id = p.get("session_id")
        occurred_at = p.get("occurred_at") or event.occurred_at.isoformat()

        open_threads = snapshot.get("open_threads") or state.get("open_threads") or []
        tone = snapshot.get("emotional_tone") or state.get("relationship_tone")
        user_id = p.get("user_id") or state.get("user_id")

        # Build rolling session summary entry
        user_message_excerpt = str(snapshot.get("user_message_excerpt") or "").strip()
        summary_entry: dict[str, Any] = {
            "session_id": session_id,
            "occurred_at": occurred_at,
            "last_topic": snapshot.get("last_topic"),
            "emotional_tone": snapshot.get("emotional_tone"),
            "my_stance": snapshot.get("my_stance"),
            "user_state_markers": list(snapshot.get("user_state_markers") or []),
            "relationship_markers": list(snapshot.get("relationship_markers") or []),
            "recent_user_messages": [user_message_excerpt] if user_message_excerpt else [],
        }
        recent = list(state.get("recent_sessions_summary") or [])
        existing = next(
            (entry for entry in recent if entry.get("session_id") == session_id),
            None,
        )
        if isinstance(existing, dict):
            summary_entry["last_topic"] = (
                summary_entry.get("last_topic") or existing.get("last_topic")
            )
            summary_entry["emotional_tone"] = (
                summary_entry.get("emotional_tone") or existing.get("emotional_tone")
            )
            summary_entry["my_stance"] = (
                summary_entry.get("my_stance") or existing.get("my_stance")
            )
            summary_entry["user_state_markers"] = _merge_unique_texts(
                list(existing.get("user_state_markers") or []),
                list(summary_entry.get("user_state_markers") or []),
                limit=8,
            )
            summary_entry["relationship_markers"] = _merge_unique_texts(
                list(existing.get("relationship_markers") or []),
                list(summary_entry.get("relationship_markers") or []),
                limit=8,
            )
            summary_entry["recent_user_messages"] = _merge_unique_texts(
                list(existing.get("recent_user_messages") or []),
                list(summary_entry.get("recent_user_messages") or []),
                limit=6,
            )
        recent = [s for s in recent if s.get("session_id") != session_id]
        recent.append(summary_entry)
        recent = recent[-_MAX_RECENT_SESSIONS:]
        total_interactions = state.get("total_interactions", 0) + 1

        days = _days_since(occurred_at)

        fact_slot_digest = _extract_fact_slot_digest(
            recent,
            previous_digest=dict(state.get("fact_slot_digest") or {}),
        )
        narrative_digest = _extract_narrative_digest(
            recent,
            previous_digest=dict(state.get("narrative_digest") or {}),
        )
        relationship_digest = _extract_relationship_digest(
            recent,
            total_interactions=total_interactions,
            previous_digest=dict(state.get("relationship_digest") or {}),
        )

        return {
            **state,
            "user_id": user_id,
            "last_interaction_at": occurred_at,
            "days_since_last_chat": days,
            "open_threads": open_threads,
            "relationship_tone": tone,
            "recent_sessions_summary": recent,
            "total_interactions": total_interactions,
            "fact_slot_digest": fact_slot_digest,
            "narrative_digest": narrative_digest,
            "relationship_digest": relationship_digest,
            "probe_snapshot": _build_probe_snapshot(
                fact_slot_digest=fact_slot_digest,
                narrative_digest=narrative_digest,
                relationship_digest=relationship_digest,
            ),
        }
