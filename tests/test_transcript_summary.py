from relationship_os.application.runtime.transcript_summary import summarize_early_messages


def test_summarize_early_messages_skips_system_and_truncates_long_content() -> None:
    summary = summarize_early_messages(
        [
            {"role": "system", "content": "hidden"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "x" * 81},
            {"role": "assistant", "content": "   "},
        ]
    )

    assert summary == "User: hello\nYou: " + ("x" * 80) + "…"


def test_summarize_early_messages_keeps_head_and_tail_when_long() -> None:
    messages = [{"role": "user", "content": f"message-{index}"} for index in range(31)]

    summary = summarize_early_messages(messages)

    lines = summary.splitlines()
    assert len(lines) == 31
    assert lines[0] == "User: message-0"
    assert lines[14] == "User: message-14"
    assert lines[15] == "..."
    assert lines[16] == "User: message-16"
    assert lines[-1] == "User: message-30"
