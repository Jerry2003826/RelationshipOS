"""JSONL shadow logger.

Writes one JSON object per decision to an append-only file. Caller is
expected to rotate (by date / size) externally; this module keeps the
hot path simple.

Usage:
    logger = JsonlShadowLogger("/var/log/router_shadow.jsonl", sample_rate=1.0)
    router = VanguardRouterV2.from_default(shadow_logger=logger)

Implicit feedback:
    If the downstream turn resolves and we learn the "true" label
    (from latency proxy, user thumbs-up, or next-turn behaviour), call
    `logger.attach_label(turn_id, label)` to write a follow-up record.
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class JsonlShadowLogger:
    path: Path | str
    sample_rate: float = 1.0
    max_bytes_hint: int = 50 * 1024 * 1024  # advisory
    _lock: threading.Lock | None = None

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, record: dict) -> None:
        if self.sample_rate < 1.0 and random.random() > self.sample_rate:
            return
        record.setdefault("turn_id", _mk_turn_id())
        line = json.dumps(record, ensure_ascii=False, default=str)
        assert self._lock is not None
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def attach_label(self, turn_id: str, label: str, source: str = "implicit") -> None:
        """Write a side-record linking a prior decision to a resolved label."""
        rec = {
            "kind": "label",
            "turn_id": turn_id,
            "label": label,
            "source": source,
            "ts": time.time(),
        }
        line = json.dumps(rec, ensure_ascii=False)
        assert self._lock is not None
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")


def _mk_turn_id() -> str:
    # ~62 bits of entropy, compact.
    return f"{int(time.time()*1e6):x}{os.getpid():x}{random.randint(0, 0xFFFF):x}"
