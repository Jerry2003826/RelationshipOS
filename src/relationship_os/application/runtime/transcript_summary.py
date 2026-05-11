from __future__ import annotations


def summarize_early_messages(messages: list[dict[str, str]]) -> str:
    """Compress early conversation into key facts for small-model context."""
    lines: list[str] = []
    for msg in messages:
        role = msg.get("role", "")
        content = (msg.get("content") or "").strip()
        if not content or role == "system":
            continue
        tag = "User" if role == "user" else "You"
        truncated = content[:80] + ("…" if len(content) > 80 else "")
        lines.append(f"{tag}: {truncated}")
    if len(lines) > 30:
        lines = lines[:15] + ["..."] + lines[-15:]
    return "\n".join(lines)
