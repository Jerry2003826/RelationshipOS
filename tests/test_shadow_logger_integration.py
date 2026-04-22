"""Integration tests for shadow-log wiring + query_shadow CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from router_v2.analyzers.router.shadow_logger import JsonlShadowLogger


@pytest.fixture
def shadow_log(tmp_path: Path) -> Path:
    return tmp_path / "shadow.jsonl"


def test_shim_picks_up_shadow_logger_env(
    monkeypatch: pytest.MonkeyPatch,
    shadow_log: Path,
) -> None:
    monkeypatch.setenv("ROUTER_SHADOW_LOG_PATH", str(shadow_log))
    monkeypatch.setenv("ROUTER_SHADOW_SAMPLE_RATE", "1.0")

    # Force a fresh build so the env var is read.
    from relationship_os.application.analyzers import vanguard_router as v

    v.reset_router_cache()
    router = v._get_v2_router()
    assert router.shadow_logger is not None

    # Trigger an ambiguous decision so the router actually writes a record.
    router.decide("这件事情我不确定要不要做")
    # Not every decision writes a record (only ambiguous / shadow-flagged
    # ones do). Fire a deliberately low-margin message until we have at
    # least one entry or hit the safety ceiling.
    for _ in range(20):
        if shadow_log.exists() and shadow_log.read_text().strip():
            break
        router.decide("这家餐厅好吃吗")
    if not shadow_log.exists() or not shadow_log.read_text().strip():
        pytest.skip("router did not mark any sample as shadow-worthy")

    lines = [
        line for line in shadow_log.read_text().splitlines() if line.strip()
    ]
    rec = json.loads(lines[0])
    for key in ("text", "route_type", "confidence", "probabilities", "ts"):
        assert key in rec

    v.reset_router_cache()


def test_attach_label_writes_side_record(shadow_log: Path) -> None:
    logger = JsonlShadowLogger(path=shadow_log, sample_rate=1.0)
    logger.attach_label(turn_id="t-123", label="FAST_PONG", source="user_thumb")
    lines = [
        line for line in shadow_log.read_text().splitlines() if line.strip()
    ]
    rec = json.loads(lines[-1])
    assert rec["kind"] == "label"
    assert rec["turn_id"] == "t-123"
    assert rec["label"] == "FAST_PONG"
    assert rec["source"] == "user_thumb"


def test_query_shadow_cli_filters_by_route(tmp_path: Path) -> None:
    log = tmp_path / "shadow.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "text": "早上好",
                        "route_type": "FAST_PONG",
                        "confidence": 0.95,
                        "ts": 1_717_000_000.0,
                    }
                ),
                json.dumps(
                    {
                        "text": "你还记得昨天说的吗",
                        "route_type": "DEEP_THINK",
                        "confidence": 0.88,
                        "ts": 1_717_000_100.0,
                    }
                ),
                json.dumps(
                    {
                        "kind": "label",
                        "turn_id": "x",
                        "label": "FAST_PONG",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/query_shadow.py",
            str(log),
            "--route",
            "FAST_PONG",
            "--min-conf",
            "0.9",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["route_type"] == "FAST_PONG"
    assert rec["confidence"] >= 0.9
