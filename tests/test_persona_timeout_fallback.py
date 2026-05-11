from relationship_os.application.runtime.persona_timeout_fallback import (
    get_cached_persona_timeout_dialogue,
)


def test_persona_timeout_fallback_uses_archetype_specific_copy() -> None:
    assert (
        get_cached_persona_timeout_dialogue({"persona_archetype": "tsundere"})
        == "我才没有没话说呢，只是信号不好。再发一遍。"
    )
    assert (
        get_cached_persona_timeout_dialogue({"persona_archetype": "gentle"})
        == "抱歉呀，我现在有点累了没听清，晚点再慢点跟我说好吗？"
    )


def test_persona_timeout_fallback_uses_default_copy_without_known_archetype() -> None:
    assert get_cached_persona_timeout_dialogue(None) == "不好意思，信号有点差，我等会回复。"
    assert (
        get_cached_persona_timeout_dialogue({"persona_archetype": "default"})
        == "不好意思，信号有点差，我等会回复。"
    )
