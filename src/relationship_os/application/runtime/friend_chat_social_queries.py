from __future__ import annotations

import re

from relationship_os.application.runtime.edge_memory_text import ordered_text_terms

DEFAULT_SOCIAL_QUERY_NOISE_TOKENS = (
    "\u4f60\u662f\u4e0d\u662f",
    "\u77e5\u9053\u4e00\u70b9",
    "\u8981\u8bf4\u5c31",
    "\u5c11\u8bf4\u4e00\u70b9",
    "\u7684\u4e8b",
    "\u522b\u4eba",
    "\u8c01\u8fd8",
    "\u8fd8\u6709\u8c01",
    "\u79d8\u5bc6",
    "\u516b\u5366",
    "\u8bf4\u4e00\u70b9",
    "\u8bf4\u8bf4",
    "\u8bb2\u8bb2",
)


def build_friend_chat_social_queries(
    user_message: str,
    *,
    noise_tokens: tuple[str, ...] | list[str] = DEFAULT_SOCIAL_QUERY_NOISE_TOKENS,
) -> list[str]:
    text = str(user_message or "")
    if not text.strip():
        return []
    cleaned = text
    for token in noise_tokens:
        cleaned = cleaned.replace(str(token), " ")
    cleaned = re.sub(r"[\u548c\u8ddf\u4e0e\u53ca\u3001]", " ", cleaned)
    cleaned = re.sub(r"[\uff1f?\uff01!\uff0c,\u3002\uff1b;\uff1a:\u3001\n\r\t]+", " ", cleaned)
    return ordered_text_terms(cleaned)
