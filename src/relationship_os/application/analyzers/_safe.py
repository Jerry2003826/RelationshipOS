"""Fault-tolerant builder decorator for analyzer pipeline stages."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from relationship_os.core.logging import get_logger

_logger = get_logger("relationship_os.analyzers")


def safe_build[T](
    default_factory: Callable[[], T],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Wrap a builder so exceptions yield a safe default instead of crashing the pipeline.

    Usage::

        @safe_build(default_factory=lambda: ContextFrame(...))
        def build_context_frame(text: str) -> ContextFrame:
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                _logger.exception("builder_failed", builder=func.__name__)
                return default_factory()

        return wrapper

    return decorator
