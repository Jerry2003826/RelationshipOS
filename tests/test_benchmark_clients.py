from __future__ import annotations

import io

import pytest

# The mem0 shadow backend is an optional dependency (`pip install .[benchmark]`).
# Skip the whole module when it is not installed instead of breaking collection.
pytest.importorskip("mem0", reason="benchmark extras not installed")

import benchmarks.__main__ as benchmark_main  # noqa: E402
from benchmarks.baseline_client import BaselineLLMClient  # noqa: E402
from benchmarks.mem0_client import Mem0BenchmarkClient  # noqa: E402


def test_baseline_create_session_accepts_metadata() -> None:
    client = BaselineLLMClient()

    session_id = client.create_session(
        "baseline-session",
        user_id="lin",
        metadata={"suite": "companion_stress_zh"},
    )

    assert session_id == "baseline-session"
    assert client._sessions[session_id][0]["role"] == "system"


def test_mem0_create_session_accepts_metadata_without_full_init() -> None:
    client = object.__new__(Mem0BenchmarkClient)
    client._run_tag = "run"
    client.persona_prompt = "persona"
    client._sessions = {}

    session_id = client.create_session(
        "mem0-session",
        user_id="anning",
        metadata={"suite": "companion_stress_zh"},
    )

    assert session_id == "mem0-session"
    state = client._sessions[session_id]
    assert state.user_id == "anning"
    assert state.history[0]["content"] == "persona"


class _NarrowStdout:
    def __init__(self) -> None:
        self.encoding = "gbk"
        self.buffer = io.BytesIO()

    def write(self, text: str) -> int:
        raise UnicodeEncodeError("gbk", text, 0, 1, "illegal multibyte sequence")

    def flush(self) -> None:
        return None


def test_p_falls_back_for_narrow_console(monkeypatch) -> None:
    fake_stdout = _NarrowStdout()
    monkeypatch.setattr(benchmark_main.sys, "stdout", fake_stdout)

    benchmark_main._p("  ✗ suite companion_stress_zh failed")

    rendered = fake_stdout.buffer.getvalue().decode("gbk", errors="replace")
    assert "suite companion_stress_zh failed" in rendered
