from __future__ import annotations

from typing import Any

from relationship_os.application.policy_registry import get_default_compiled_policy_set


def load_runtime_behavior_policy(runtime_profile: str) -> dict[str, Any]:
    compiled = get_default_compiled_policy_set(
        runtime_profile=runtime_profile,
        archetype="default",
    )
    if compiled is None:
        return {}
    return dict(compiled.rendering_policy.get("runtime_behavior") or {})


def runtime_behavior_list(
    policy: dict[str, Any],
    key: str,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    values = policy.get(key)
    if not isinstance(values, list):
        return fallback
    compiled = tuple(str(value) for value in values if str(value).strip())
    return compiled or fallback


def runtime_behavior_map(policy: dict[str, Any], key: str) -> dict[str, Any]:
    value = policy.get(key)
    return dict(value) if isinstance(value, dict) else {}


def runtime_behavior_int(policy: dict[str, Any], key: str, fallback: int) -> int:
    value = policy.get(key)
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def runtime_behavior_bool(policy: dict[str, Any], key: str, fallback: bool) -> bool:
    value = policy.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return fallback
