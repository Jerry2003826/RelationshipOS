from __future__ import annotations

from typing import Any

from relationship_os.domain.llm import ContentBlock, LLMMessage


def build_friend_chat_compact_probe_messages(
    *,
    runtime_card: str,
    user_prompt: str,
    turn_input: Any | None,
) -> list[LLMMessage]:
    compact_messages = [LLMMessage(role="system", content=runtime_card)]
    if turn_input and turn_input.has_media:
        blocks: list[ContentBlock] = [ContentBlock(type="text", text=user_prompt)]
        for img in turn_input.images:
            if img.url:
                blocks.append(
                    ContentBlock(
                        type="image_url",
                        url=img.url,
                        mime_type=img.mime_type,
                    )
                )
        if turn_input.audio and turn_input.audio.url:
            blocks.append(
                ContentBlock(
                    type="audio_url",
                    url=turn_input.audio.url,
                    mime_type=turn_input.audio.mime_type,
                )
            )
        compact_messages.append(LLMMessage(role="user", content=blocks))
    else:
        compact_messages.append(LLMMessage(role="user", content=user_prompt))
    return compact_messages
