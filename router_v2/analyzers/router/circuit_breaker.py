"""Minimal synchronous circuit breaker for Tier 3 arbiter calls.

States:
    * CLOSED   – calls pass through.
    * OPEN     – fast-fail for `cooldown_sec`.
    * HALF_OPEN – after cooldown, allow one probe. Success → CLOSED.

Designed to be dependency-free so it can ship with the router
regardless of whether the host process has its own resilience stack.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class BreakerOpenError(RuntimeError):
    """Raised when the breaker is open; caller should fall back."""


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3      # consecutive failures to trip
    cooldown_sec: float = 30.0      # time in OPEN before a probe attempt
    _state: BreakerState = BreakerState.CLOSED
    _failures: int = 0
    _opened_at: float = 0.0

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    # --- introspection ----------------------------------------------------

    @property
    def state(self) -> BreakerState:
        with self._lock:
            self._maybe_half_open_locked()
            return self._state

    # --- call gating ------------------------------------------------------

    def allow(self) -> bool:
        with self._lock:
            self._maybe_half_open_locked()
            return self._state is not BreakerState.OPEN

    def _maybe_half_open_locked(self) -> None:
        if self._state is BreakerState.OPEN:
            if (time.time() - self._opened_at) >= self.cooldown_sec:
                self._state = BreakerState.HALF_OPEN

    def on_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = BreakerState.CLOSED

    def on_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if (
                self._state is BreakerState.HALF_OPEN
                or self._failures >= self.failure_threshold
            ):
                self._state = BreakerState.OPEN
                self._opened_at = time.time()
