"""Backward-compat shim for callers still importing the old router.

Old API (vanguard_router.py):

    from .vanguard_router import VanguardRouter, RouterDecision
    router = VanguardRouter(...)
    decision = await router.route(text)    # async
    decision.route_type  # "FAST_PONG" | "NEED_DEEP_THINK"

New API:

    from .vanguard_router_v2 import VanguardRouterV2
    router = VanguardRouterV2.from_default()
    decision = router.decide(text)         # sync
    decision.route_type  # 3 classes

This shim preserves the async signature and legacy two-class shape so
that `runtime_service` and other callers can switch imports without
code changes. It emits a DeprecationWarning on construction.
"""

from __future__ import annotations

import warnings
from typing import Any

from .contracts import RouterDecision, downgrade_to_legacy
from .vanguard_router_v2 import VanguardRouterV2


class VanguardRouter:
    """Legacy adapter; keeps the old async `route` method alive."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        warnings.warn(
            "VanguardRouter (legacy) is deprecated; switch to "
            "VanguardRouterV2.from_default().decide(text). "
            "This shim will be removed in 2026-Q4.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._impl = VanguardRouterV2.from_default()

    async def route(self, text: str) -> RouterDecision:
        """Async wrapper; the v2 router is synchronous so we just return
        a completed future-equivalent value."""
        decision = self._impl.decide(text)
        return downgrade_to_legacy(decision)
