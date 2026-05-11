from types import SimpleNamespace

from relationship_os.application.runtime.friend_chat_probe_messages import (
    build_friend_chat_compact_probe_messages,
)
from relationship_os.domain.llm import LLMMessage


def test_build_friend_chat_compact_probe_messages_without_media() -> None:
    messages = build_friend_chat_compact_probe_messages(
        runtime_card="contract",
        user_prompt="请回答",
        turn_input=None,
    )

    assert messages == [
        LLMMessage(role="system", content="contract"),
        LLMMessage(role="user", content="请回答"),
    ]


def test_build_friend_chat_compact_probe_messages_with_media_blocks() -> None:
    turn_input = SimpleNamespace(
        has_media=True,
        images=[SimpleNamespace(url="https://example.com/a.png", mime_type="image/png")],
        audio=SimpleNamespace(url="https://example.com/a.mp3", mime_type="audio/mpeg"),
    )

    messages = build_friend_chat_compact_probe_messages(
        runtime_card="contract",
        user_prompt="请回答",
        turn_input=turn_input,
    )

    assert len(messages) == 2
    assert messages[0].content == "contract"
    assert isinstance(messages[1].content, list)
    assert [block.type for block in messages[1].content] == ["text", "image_url", "audio_url"]
