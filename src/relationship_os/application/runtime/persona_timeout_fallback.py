from __future__ import annotations

from typing import Any


def get_cached_persona_timeout_dialogue(entity_persona: Any) -> str:
    if entity_persona:
        archetype = entity_persona.get("persona_archetype", "default")
        if archetype == "tsundere":
            return "我才没有没话说呢，只是信号不好。再发一遍。"
        if archetype == "gentle":
            return "抱歉呀，我现在有点累了没听清，晚点再慢点跟我说好吗？"
    return "不好意思，信号有点差，我等会回复。"
