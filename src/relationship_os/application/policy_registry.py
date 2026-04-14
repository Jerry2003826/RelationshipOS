from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def _load_structured_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        payload = json.loads(text)
    elif path.suffix in {".yaml", ".yml"} and yaml is not None:
        payload = yaml.safe_load(text) or {}
    else:
        return {}
    return payload if isinstance(payload, dict) else {}


@dataclass(slots=True, frozen=True)
class CompiledPolicySet:
    version: str
    runtime_profile: str
    archetype: str
    memory_policy: dict[str, Any]
    conscience_policy: dict[str, Any]
    rendering_policy: dict[str, Any]
    persona_policy: dict[str, Any]
    source_paths: dict[str, list[str]]


class PolicyRegistry:
    def __init__(self, *, root_path: str | Path) -> None:
        self._root_path = Path(root_path)
        self._cache: dict[tuple[str, str], CompiledPolicySet] = {}

    @property
    def root_path(self) -> Path:
        return self._root_path

    def reload(self) -> None:
        self._cache.clear()

    def compile_policy_set(
        self,
        *,
        runtime_profile: str = "default",
        archetype: str = "default",
    ) -> CompiledPolicySet:
        cache_key = (runtime_profile or "default", archetype or "default")
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        compiled_groups: dict[str, dict[str, Any]] = {}
        source_paths: dict[str, list[str]] = {}
        versions: list[str] = []
        for group in ("memory", "conscience", "rendering", "persona"):
            merged, paths = self._load_group(
                group=group,
                runtime_profile=cache_key[0],
                archetype=cache_key[1],
            )
            compiled_groups[group] = merged
            source_paths[group] = paths
            versions.append(str(merged.get("version", "v1")))

        compiled = CompiledPolicySet(
            version="|".join(versions),
            runtime_profile=cache_key[0],
            archetype=cache_key[1],
            memory_policy=compiled_groups["memory"],
            conscience_policy=compiled_groups["conscience"],
            rendering_policy=compiled_groups["rendering"],
            persona_policy=compiled_groups["persona"],
            source_paths=source_paths,
        )
        self._cache[cache_key] = compiled
        return compiled

    def snapshot(
        self,
        *,
        runtime_profile: str = "default",
        archetype: str = "default",
    ) -> dict[str, Any]:
        compiled = self.compile_policy_set(
            runtime_profile=runtime_profile,
            archetype=archetype,
        )
        return {
            "version": compiled.version,
            "runtime_profile": compiled.runtime_profile,
            "archetype": compiled.archetype,
            "source_paths": compiled.source_paths,
            "memory_policy": compiled.memory_policy,
            "conscience_policy": compiled.conscience_policy,
            "rendering_policy": compiled.rendering_policy,
            "persona_policy": compiled.persona_policy,
        }

    def _load_group(
        self,
        *,
        group: str,
        runtime_profile: str,
        archetype: str,
    ) -> tuple[dict[str, Any], list[str]]:
        group_root = self._root_path / group
        merged: dict[str, Any] = {}
        used_paths: list[str] = []
        for candidate in (
            group_root / "base.json",
            group_root / "base.yaml",
            group_root / "base.yml",
            group_root / "profiles" / f"{runtime_profile}.json",
            group_root / "profiles" / f"{runtime_profile}.yaml",
            group_root / "profiles" / f"{runtime_profile}.yml",
            group_root / "archetypes" / f"{archetype}.json",
            group_root / "archetypes" / f"{archetype}.yaml",
            group_root / "archetypes" / f"{archetype}.yml",
        ):
            payload = _load_structured_file(candidate)
            if not payload:
                continue
            merged = _deep_merge(merged, payload)
            used_paths.append(str(candidate))
        return merged, used_paths


_DEFAULT_POLICY_REGISTRY: PolicyRegistry | None = None
_DEFAULT_RUNTIME_PROFILE = "default"


def configure_default_policy_registry(
    *,
    registry: PolicyRegistry,
    runtime_profile: str,
) -> None:
    global _DEFAULT_POLICY_REGISTRY, _DEFAULT_RUNTIME_PROFILE
    _DEFAULT_POLICY_REGISTRY = registry
    _DEFAULT_RUNTIME_PROFILE = runtime_profile or "default"


def get_default_compiled_policy_set(
    *,
    runtime_profile: str | None = None,
    archetype: str = "default",
) -> CompiledPolicySet | None:
    if _DEFAULT_POLICY_REGISTRY is None:
        return None
    return _DEFAULT_POLICY_REGISTRY.compile_policy_set(
        runtime_profile=runtime_profile or _DEFAULT_RUNTIME_PROFILE,
        archetype=archetype or "default",
    )
