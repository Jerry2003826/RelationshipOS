from __future__ import annotations

import json
import re
from typing import Any

from relationship_os.application.llm import (
    _compose_friend_chat_structured_probe_reply as compose_friend_chat_structured_probe_reply,
)


def parse_friend_chat_structured_probe_reply(
    raw_text: str,
    *,
    fallback_probe_kind: str = "",
) -> tuple[str, dict[str, Any]] | None:
    raw = str(raw_text or "").strip()
    if not raw:
        return None
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    probe_kind = str(payload.get("probe_kind") or fallback_probe_kind or "").strip()
    reply = compose_friend_chat_structured_probe_reply(payload, probe_kind=probe_kind)
    if not reply:
        return None
    diagnostics = {
        "structured_probe_reply": True,
        "structured_probe_covered_fact_tokens": list(payload.get("covered_fact_tokens") or []),
        "structured_probe_covered_signal_ids": list(payload.get("covered_signal_ids") or []),
        "structured_probe_covered_disclosure_posture": str(
            payload.get("covered_disclosure_posture", "") or ""
        ).strip(),
        "structured_probe_violations": list(payload.get("violations") or []),
    }
    return reply, diagnostics
