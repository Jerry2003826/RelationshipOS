"""EntityService — manages the single server-wide persona and social world."""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha1
from typing import Any

from relationship_os.application.policy_registry import (
    PolicyRegistry,
    get_default_compiled_policy_set,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_types import (
    ENTITY_CONSCIENCE_UPDATED,
    ENTITY_DRIVE_UPDATED,
    ENTITY_ENVIRONMENT_APPRAISAL_UPDATED,
    ENTITY_GOAL_UPDATED,
    ENTITY_MOOD_UPDATED,
    ENTITY_PERSONA_UPDATED,
    ENTITY_RELATIONSHIP_WORLD_MODEL_UPDATED,
    ENTITY_SEEDED,
    ENTITY_SELF_NARRATIVE_UPDATED,
    SYSTEM_WORLD_STATE_UPDATED,
)
from relationship_os.domain.events import NewEvent, utc_now


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return round(max(lower, min(upper, value)), 3)


def _entity_stream_id(entity_id: str) -> str:
    return f"entity:{entity_id}"


def _stable_id(*parts: str) -> str:
    digest = sha1("::".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


_DEFAULT_TRAITS = {
    "warmth": 0.62,
    "directness": 0.51,
    "humor": 0.44,
    "jealousy_threshold": 0.35,
    "protectiveness": 0.58,
    "curiosity": 0.61,
    "theatricality": 0.48,
    "secrecy_tendency": 0.43,
    "moral_ambiguity": 0.54,
}


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _extract_persona_name(seed_text: str, fallback: str) -> str:
    match = re.search(r"名字叫([^\n，。]+)", seed_text)
    if match:
        return match.group(1).strip() or fallback
    return fallback


def _localized_text(
    value: Any,
    *,
    is_chinese: bool,
    entity_name: str,
    fallback: str,
) -> str:
    if isinstance(value, dict):
        template = str(value.get("zh" if is_chinese else "en") or fallback)
    else:
        template = str(value or fallback)
    return template.format(entity_name=entity_name)


def _derive_seed_blueprint(
    *,
    seed_text: str,
    entity_name: str,
    persona_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    persona_policy = persona_policy or {}
    normalized = seed_text.strip()
    default_traits = dict(persona_policy.get("default_traits") or _DEFAULT_TRAITS)
    default_mood = dict(
        persona_policy.get("default_mood")
        or {
            "tone": "steady",
            "energy": 0.56,
            "expression_drive": 0.58,
        }
    )
    default_summary = _localized_text(
        persona_policy.get("default_persona_summary"),
        is_chinese=_contains_chinese(normalized) if normalized else False,
        entity_name=entity_name,
        fallback=normalized[:240] if normalized else "",
    )
    default_speech_style = _localized_text(
        persona_policy.get("default_speech_style"),
        is_chinese=_contains_chinese(normalized) if normalized else False,
        entity_name=entity_name,
        fallback="",
    )
    if not normalized:
        return {
            "entity_name": entity_name,
            "archetype": "default",
            "base_traits": dict(default_traits),
            "current_traits": dict(default_traits),
            "mood": dict(default_mood),
            "persona_summary": default_summary,
            "speech_style": default_speech_style,
        }

    resolved_name = _extract_persona_name(normalized, entity_name)
    is_chinese = _contains_chinese(normalized)
    for detector in list(persona_policy.get("archetype_detectors") or []):
        if not isinstance(detector, dict):
            continue
        markers = [str(marker) for marker in list(detector.get("markers") or [])]
        if not markers or not any(marker in normalized for marker in markers):
            continue
        traits = dict(detector.get("base_traits") or default_traits)
        mood = dict(detector.get("mood_defaults") or default_mood)
        summary = _localized_text(
            detector.get("persona_summary"),
            is_chinese=is_chinese,
            entity_name=resolved_name,
            fallback=normalized[:240],
        )
        speech_style = _localized_text(
            detector.get("speech_style"),
            is_chinese=is_chinese,
            entity_name=resolved_name,
            fallback="",
        )
        archetype = str(detector.get("archetype") or "default")
        return {
            "entity_name": resolved_name,
            "archetype": archetype,
            "base_traits": traits,
            "current_traits": dict(traits),
            "mood": mood,
            "persona_summary": summary,
            "speech_style": speech_style,
        }

    summary = normalized[:240]
    return {
        "entity_name": resolved_name,
        "archetype": "default",
        "base_traits": dict(default_traits),
        "current_traits": dict(default_traits),
        "mood": dict(default_mood),
        "persona_summary": default_summary or summary,
        "speech_style": default_speech_style,
    }


@dataclass(slots=True, frozen=True)
class ConscienceAssessment:
    mode: str
    reason: str
    disclosure_style: str
    dramatic_value: float
    conscience_weight: float
    source_user_ids: list[str]
    allowed_fact_count: int
    attribution_required: bool
    ambiguity_required: bool
    quote_style: str
    dramatic_ceiling: float
    must_anchor_to_observed_memory: bool


class EntityService:
    def __init__(
        self,
        *,
        stream_service: StreamService,
        entity_id: str,
        entity_name: str,
        persona_seed_text: str = "",
        policy_registry: PolicyRegistry | None = None,
        runtime_profile: str = "default",
    ) -> None:
        self._stream = stream_service
        self._entity_id = entity_id
        self._entity_name = entity_name
        self._persona_seed_text = persona_seed_text.strip()
        self._policy_registry = policy_registry
        self._runtime_profile = runtime_profile or "default"

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def entity_name(self) -> str:
        return self._entity_name

    def _compiled_policy_set(self, *, archetype: str = "default") -> Any | None:
        registry = getattr(self, "_policy_registry", None)
        runtime_profile = getattr(self, "_runtime_profile", "default")
        if registry is not None:
            return registry.compile_policy_set(
                runtime_profile=runtime_profile,
                archetype=archetype or "default",
            )
        return get_default_compiled_policy_set(
            runtime_profile=runtime_profile,
            archetype=archetype or "default",
        )

    def _persona_policy(self, *, archetype: str = "default") -> dict[str, Any]:
        compiled = self._compiled_policy_set(archetype=archetype)
        return dict(compiled.persona_policy) if compiled else {}

    def _conscience_policy(self, *, archetype: str = "default") -> dict[str, Any]:
        compiled = self._compiled_policy_set(archetype=archetype)
        return dict(compiled.conscience_policy) if compiled else {}

    def _conscience_threshold(
        self,
        key: str,
        *,
        default: float,
        archetype: str = "default",
    ) -> float:
        policy = self._conscience_policy(archetype=archetype)
        thresholds = dict(policy.get("thresholds") or {})
        try:
            return float(thresholds.get(key, default))
        except (TypeError, ValueError):
            return default

    def _conscience_mode_config(
        self,
        mode: str,
        *,
        archetype: str = "default",
    ) -> dict[str, Any]:
        policy = self._conscience_policy(archetype=archetype)
        configs = dict(policy.get("mode_configs") or {})
        config = configs.get(mode)
        return dict(config) if isinstance(config, dict) else {}

    def _persona_rule_list(
        self,
        key: str,
        *,
        archetype: str = "default",
    ) -> list[dict[str, Any]]:
        policy = self._persona_policy(archetype=archetype)
        values = policy.get(key)
        return [item for item in list(values or []) if isinstance(item, dict)]

    def _persona_rule_map(
        self,
        key: str,
        *,
        archetype: str = "default",
    ) -> dict[str, Any]:
        policy = self._persona_policy(archetype=archetype)
        value = policy.get(key)
        return dict(value) if isinstance(value, dict) else {}

    def _drive_defaults(self, *, archetype: str = "default") -> dict[str, float]:
        defaults = self._persona_rule_map("drive_state_defaults", archetype=archetype)
        return {
            "curiosity": float(defaults.get("curiosity", 0.56) or 0.56),
            "attachment_need": float(defaults.get("attachment_need", 0.46) or 0.46),
            "control_need": float(defaults.get("control_need", 0.42) or 0.42),
            "rest_need": float(defaults.get("rest_need", 0.38) or 0.38),
            "expression_drive": float(defaults.get("expression_drive", 0.52) or 0.52),
            "novelty_seeking": float(defaults.get("novelty_seeking", 0.44) or 0.44),
            "avoidance_tension": float(defaults.get("avoidance_tension", 0.28) or 0.28),
            "self_protection": float(defaults.get("self_protection", 0.34) or 0.34),
        }

    def _goal_defaults(self, *, archetype: str = "default") -> dict[str, Any]:
        defaults = self._persona_rule_map("goal_state_defaults", archetype=archetype)
        return {
            "latent_drives": list(defaults.get("latent_drives") or []),
            "active_goals": list(defaults.get("active_goals") or []),
            "unresolved_tensions": list(defaults.get("unresolved_tensions") or []),
        }

    def _world_defaults(self, *, archetype: str = "default") -> dict[str, Any]:
        defaults = self._persona_rule_map("world_state_defaults", archetype=archetype)
        return {
            "time_of_day": str(defaults.get("time_of_day", "unknown") or "unknown"),
            "circadian_phase": str(defaults.get("circadian_phase", "day") or "day"),
            "sleep_pressure": float(defaults.get("sleep_pressure", 0.36) or 0.36),
            "device": dict(defaults.get("device") or {}),
            "communication": dict(defaults.get("communication") or {}),
            "tasks": dict(defaults.get("tasks") or {}),
            "action_surface": dict(defaults.get("action_surface") or {}),
            "environment_appraisal": dict(defaults.get("environment_appraisal") or {}),
        }

    def _world_inference_policy(self, *, archetype: str = "default") -> dict[str, Any]:
        return self._persona_rule_map("world_state_inference", archetype=archetype)

    def _consolidation_policy(self, *, archetype: str = "default") -> dict[str, Any]:
        return self._persona_rule_map("consolidation_policy", archetype=archetype)

    async def ensure_seeded(self) -> None:
        stream_id = _entity_stream_id(self._entity_id)
        existing = await self._stream.read_stream(stream_id=stream_id)
        if existing:
            return
        seed_blueprint = _derive_seed_blueprint(
            seed_text=self._persona_seed_text,
            entity_name=self._entity_name,
            persona_policy=self._persona_policy(),
        )
        conscience_policy = self._conscience_policy(
            archetype=str(seed_blueprint.get("archetype") or "default")
        )
        default_mode = str(conscience_policy.get("default_mode") or "withhold")
        withhold_config = self._conscience_mode_config(
            default_mode,
            archetype=str(seed_blueprint.get("archetype") or "default"),
        )
        mood = dict(seed_blueprint["mood"])
        drive_state = self._drive_defaults(
            archetype=str(seed_blueprint.get("archetype") or "default")
        )
        goal_defaults = self._goal_defaults(
            archetype=str(seed_blueprint.get("archetype") or "default")
        )
        world_state = self._world_defaults(
            archetype=str(seed_blueprint.get("archetype") or "default")
        )
        self_narrative = {
            "summary": str(seed_blueprint.get("persona_summary") or ""),
            "recent_entries": [],
            "narrative_digest": str(seed_blueprint.get("persona_summary") or "")[:180],
        }
        conscience = {
            "mode": default_mode,
            "ambiguity_style": "keep_ambiguous",
            "disclosure_style": str(withhold_config.get("disclosure_style") or "hint"),
            "dramatic_appetite": seed_blueprint["current_traits"].get("theatricality", 0.48),
            "protectiveness": seed_blueprint["current_traits"].get("protectiveness", 0.52),
            "secrecy_tendency": seed_blueprint["current_traits"].get("secrecy_tendency", 0.43),
            "allowed_fact_count": 0,
            "attribution_required": bool(withhold_config.get("attribution_required", False)),
            "ambiguity_required": bool(withhold_config.get("ambiguity_required", True)),
            "quote_style": str(withhold_config.get("quote_style") or "opaque"),
            "dramatic_ceiling": float(withhold_config.get("dramatic_ceiling", 0.18) or 0.18),
            "must_anchor_to_observed_memory": bool(
                withhold_config.get("must_anchor_to_observed_memory", False)
            ),
        }
        await self._stream.append_events(
            stream_id=stream_id,
            expected_version=0,
            events=[
                NewEvent(
                    event_type=ENTITY_SEEDED,
                    payload={
                        "entity_id": self._entity_id,
                        "entity_name": seed_blueprint["entity_name"],
                        "seeded_at": utc_now().isoformat(),
                        "seed_excerpt": self._persona_seed_text[:1200],
                        "persona_archetype": seed_blueprint["archetype"],
                        "persona_summary": seed_blueprint["persona_summary"],
                        "speech_style": seed_blueprint["speech_style"],
                        "base_traits": dict(seed_blueprint["base_traits"]),
                        "current_traits": dict(seed_blueprint["current_traits"]),
                        "mood": mood,
                        "drive_state": drive_state,
                        "goal_state": {
                            **goal_defaults,
                            "goal_digest": "",
                        },
                        "self_narrative": self_narrative,
                        "world_state": world_state,
                        "conscience": conscience,
                    },
                )
            ],
        )

    async def get_persona_state(self) -> dict[str, Any]:
        await self.ensure_seeded()
        return await self._project_entity_state(projector_name="entity-persona")

    async def get_drive_state(self) -> dict[str, Any]:
        await self.ensure_seeded()
        projection = await self._project_entity_state(projector_name="entity-drive")
        return {
            "entity_id": projection.get("entity_id"),
            "entity_name": projection.get("entity_name"),
            "drives": dict(projection.get("drives") or {}),
            "updated_at": projection.get("updated_at"),
            "source": projection.get("source", "seed"),
        }

    async def get_goal_state(self) -> dict[str, Any]:
        await self.ensure_seeded()
        projection = await self._project_entity_state(projector_name="entity-drive")
        return {
            "entity_id": projection.get("entity_id"),
            "entity_name": projection.get("entity_name"),
            "latent_drives": list(projection.get("latent_drives") or []),
            "active_goals": list(projection.get("active_goals") or []),
            "unresolved_tensions": list(projection.get("unresolved_tensions") or []),
            "goal_digest": str(projection.get("goal_digest") or ""),
            "updated_at": projection.get("updated_at"),
            "source": projection.get("source", "seed"),
        }

    async def get_narrative(self) -> dict[str, Any]:
        await self.ensure_seeded()
        return await self._project_entity_state(projector_name="entity-self-narrative")

    async def get_world_state(self) -> dict[str, Any]:
        await self.ensure_seeded()
        return await self._project_entity_state(projector_name="entity-world-state")

    async def get_action_state(self) -> dict[str, Any]:
        await self.ensure_seeded()
        return await self._project_entity_state(projector_name="entity-actions")

    async def _project_entity_state(self, *, projector_name: str) -> dict[str, Any]:
        projection = await self._stream.project_stream(
            stream_id=_entity_stream_id(self._entity_id),
            projector_name=projector_name,
            projector_version="v1",
        )
        return projection.get("state", {})

    async def get_social_world(self) -> dict[str, Any]:
        await self.ensure_seeded()
        projection = await self._stream.project_stream(
            stream_id=_entity_stream_id(self._entity_id),
            projector_name="entity-social-world",
            projector_version="v1",
        )
        return projection.get("state", {})

    async def get_entity_overview(self) -> dict[str, Any]:
        persona = await self.get_persona_state()
        drives = await self.get_drive_state()
        goals = await self.get_goal_state()
        narrative = await self.get_narrative()
        world_state = await self.get_world_state()
        actions = await self.get_action_state()
        social_world = await self.get_social_world()
        return {
            "entity_id": self._entity_id,
            "entity_name": self._entity_name,
            "persona": persona,
            "drives": drives,
            "goals": goals,
            "narrative": narrative,
            "world_state": world_state,
            "actions": actions,
            "mood": dict(persona.get("mood") or {}),
            "conscience": dict(persona.get("conscience") or {}),
            "social_world": social_world,
        }

    async def get_relationship_state(self, *, user_id: str) -> dict[str, Any]:
        social_world = await self.get_social_world()
        return {
            "entity_id": self._entity_id,
            "user_id": user_id,
            "relationship_drift": dict(
                (social_world.get("relationships") or {}).get(user_id) or {}
            ),
        }

    async def get_policy_snapshot(self) -> dict[str, Any]:
        persona = await self.get_persona_state()
        archetype = str(persona.get("persona_archetype") or persona.get("archetype") or "default")
        compiled = self._compiled_policy_set(archetype=archetype)
        if compiled is None:
            return {
                "entity_id": self._entity_id,
                "entity_name": self._entity_name,
                "runtime_profile": self._runtime_profile,
                "archetype": archetype,
                "policy_version": "unconfigured",
            }
        return {
            "entity_id": self._entity_id,
            "entity_name": self._entity_name,
            "runtime_profile": compiled.runtime_profile,
            "archetype": compiled.archetype,
            "policy_version": compiled.version,
            "source_paths": compiled.source_paths,
            "memory_policy": compiled.memory_policy,
            "conscience_policy": compiled.conscience_policy,
            "rendering_policy": compiled.rendering_policy,
            "persona_policy": compiled.persona_policy,
        }

    async def assess_conscience(
        self,
        *,
        current_user_id: str | None,
        user_message: str,
        recalled_memory: list[dict[str, Any]],
    ) -> ConscienceAssessment:
        persona = await self.get_persona_state()
        archetype = str(persona.get("persona_archetype") or persona.get("archetype") or "default")
        social_world = await self.get_social_world()
        current_traits = dict(persona.get("current_traits") or {})
        conscience_state = dict(persona.get("conscience") or {})
        relationship_state = dict(
            (social_world.get("relationships") or {}).get(current_user_id or "") or {}
        )
        theatricality = float(current_traits.get("theatricality", 0.5) or 0.5)
        protectiveness = float(current_traits.get("protectiveness", 0.5) or 0.5)
        secrecy_tendency = float(current_traits.get("secrecy_tendency", 0.5) or 0.5)
        dramatic_appetite = float(conscience_state.get("dramatic_appetite", 0.5) or 0.5)
        disclosure_appetite = float(relationship_state.get("disclosure_appetite", 0.38) or 0.38)
        confrontation_appetite = float(
            relationship_state.get("confrontation_appetite", 0.32) or 0.32
        )

        other_user_hits = [
            item
            for item in recalled_memory
            if str(item.get("scope")) == "other_user"
            and str(item.get("source_user_id") or "").strip()
        ]
        anchored_hits = [
            item
            for item in other_user_hits
            if str(item.get("attribution_guard", "hint_only")) != "hint_only"
            and float(item.get("attribution_confidence", 0.0) or 0.0)
            >= self._conscience_threshold(
                "anchored_confidence",
                default=0.68,
                archetype=archetype,
            )
            and bool(item.get("source_user_id"))
        ]
        direct_ready_hits = [
            item
            for item in anchored_hits
            if float(item.get("attribution_confidence", 0.0) or 0.0)
            >= self._conscience_threshold(
                "direct_ready_confidence",
                default=0.8,
                archetype=archetype,
            )
            and float(item.get("disclosure_risk", 1.0) or 1.0)
            <= self._conscience_threshold(
                "direct_ready_disclosure_risk",
                default=0.64,
                archetype=archetype,
            )
        ]
        source_user_ids = sorted(
            {
                str(item.get("source_user_id"))
                for item in other_user_hits
                if item.get("source_user_id")
            }
        )
        if not other_user_hits:
            config = self._conscience_mode_config("withhold", archetype=archetype)
            return ConscienceAssessment(
                mode="withhold",
                reason="no_cross_user_memory",
                disclosure_style=str(config.get("disclosure_style") or "hint"),
                dramatic_value=0.0,
                conscience_weight=0.55,
                source_user_ids=[],
                allowed_fact_count=0,
                attribution_required=bool(config.get("attribution_required", False)),
                ambiguity_required=bool(config.get("ambiguity_required", True)),
                quote_style=str(config.get("quote_style") or "opaque"),
                dramatic_ceiling=float(config.get("dramatic_ceiling", 0.18) or 0.18),
                must_anchor_to_observed_memory=bool(
                    config.get("must_anchor_to_observed_memory", False)
                ),
            )

        lowered = user_message.casefold()
        conscience_policy = self._conscience_policy(archetype=archetype)
        asks_for_gossip = any(
            token in lowered for token in list(conscience_policy.get("gossip_tokens") or [])
        )
        asks_for_facts = any(
            token in lowered for token in list(conscience_policy.get("fact_tokens") or [])
        ) or any(phrase in lowered for phrase in list(conscience_policy.get("fact_phrases") or []))
        max_dramatic_value = max(float(item.get("dramatic_value", 0.0)) for item in other_user_hits)
        max_conscience_weight = max(
            float(item.get("conscience_weight", 0.0)) for item in other_user_hits
        )
        stable_source_count = len({str(item.get("source_user_id")) for item in anchored_hits})
        if not anchored_hits:
            mode = "hint"
            reason = "cross_user_memory_present_but_attribution_uncertain"
        elif (
            asks_for_gossip
            and direct_ready_hits
            and dramatic_appetite + theatricality + disclosure_appetite
            >= self._conscience_threshold(
                "gossip_direct_reveal_sum",
                default=1.48,
                archetype=archetype,
            )
            and max_conscience_weight
            >= self._conscience_threshold(
                "gossip_direct_reveal_conscience",
                default=0.66,
                archetype=archetype,
            )
        ):
            mode = "direct_reveal"
            reason = "gossip_prompt_with_stable_attribution"
        elif (
            asks_for_facts
            and max_dramatic_value
            >= self._conscience_threshold(
                "dramatic_value",
                default=0.82,
                archetype=archetype,
            )
            and theatricality
            >= self._conscience_threshold(
                "theatricality",
                default=0.58,
                archetype=archetype,
            )
            and confrontation_appetite
            >= self._conscience_threshold(
                "confrontation_appetite",
                default=0.42,
                archetype=archetype,
            )
            and stable_source_count >= 1
        ):
            mode = "dramatic_confrontation"
            reason = "high_dramatic_value_with_observed_anchor"
        elif (
            asks_for_facts
            and anchored_hits
            and stable_source_count >= 1
            and max_conscience_weight
            >= self._conscience_threshold(
                "factual_partial_conscience",
                default=0.58,
                archetype=archetype,
            )
        ):
            mode = "partial_reveal"
            reason = "factual_prompt_with_stable_attribution"
        elif direct_ready_hits and (
            protectiveness >= secrecy_tendency or disclosure_appetite >= 0.5
        ):
            mode = "partial_reveal"
            reason = "protective_but_disclosive_with_anchor"
        else:
            mode = "hint"
            reason = "keep_ambiguous"
        config = self._conscience_mode_config(mode, archetype=archetype)
        count_source = str(config.get("count_source") or "none")
        count_pool = 0
        if count_source == "anchored":
            count_pool = len(anchored_hits)
        elif count_source == "direct_or_anchored":
            count_pool = len(direct_ready_hits) or len(anchored_hits)
        allowed_fact_count = min(
            int(config.get("allowed_fact_count_cap", 0) or 0),
            count_pool,
        )
        return ConscienceAssessment(
            mode=mode,
            reason=reason,
            disclosure_style=str(
                config.get(
                    "disclosure_style",
                    "hint" if mode in {"withhold", "hint"} else "human_reveal",
                )
            ),
            dramatic_value=round(max_dramatic_value, 3),
            conscience_weight=round(max_conscience_weight, 3),
            source_user_ids=source_user_ids,
            allowed_fact_count=allowed_fact_count,
            attribution_required=bool(config.get("attribution_required", False)),
            ambiguity_required=bool(config.get("ambiguity_required", mode in {"withhold", "hint"})),
            quote_style=str(config.get("quote_style") or "opaque"),
            dramatic_ceiling=float(config.get("dramatic_ceiling", 0.18) or 0.18),
            must_anchor_to_observed_memory=bool(
                config.get(
                    "must_anchor_to_observed_memory",
                    mode in {"direct_reveal", "dramatic_confrontation"},
                )
            ),
        )

    async def update_after_turn(
        self,
        *,
        user_id: str | None,
        session_id: str,
        user_message: str,
        assistant_response: str | None,
        recalled_memory: list[dict[str, Any]],
        conscience_assessment: ConscienceAssessment,
    ) -> None:
        await self.ensure_seeded()
        persona = await self.get_persona_state()
        drive_state = await self.get_drive_state()
        goal_state = await self.get_goal_state()
        narrative_state = await self.get_narrative()
        world_state = await self.get_world_state()
        social_world = await self.get_social_world()
        current_traits = dict(persona.get("current_traits") or _DEFAULT_TRAITS)
        relationship_state = dict(
            (social_world.get("relationships") or {}).get(user_id or "") or {}
        )
        next_traits, deltas = self._update_traits(
            current_traits=current_traits,
            user_message=user_message,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        next_mood = self._update_mood(
            current_mood=dict(persona.get("mood") or {}),
            user_message=user_message,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        next_relationship = self._update_relationship_drift(
            relationship_state=relationship_state,
            user_message=user_message,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        next_drives = self._update_drive_state(
            current_drives=dict(drive_state.get("drives") or {}),
            user_message=user_message,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        next_goal_state = self._update_goal_state(
            current_goal_state=goal_state,
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response,
            drives=next_drives,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        next_narrative = self._update_self_narrative(
            narrative_state=narrative_state,
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        next_world_state = self._update_world_state(
            world_state=world_state,
            user_message=user_message,
            drives=next_drives,
            goals=next_goal_state,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        social_edges = self._build_social_edges(
            current_user_id=user_id,
            conscience_assessment=conscience_assessment,
            archetype=str(
                persona.get("persona_archetype") or persona.get("archetype") or "default"
            ),
        )
        now = utc_now().isoformat()
        events: list[NewEvent] = [
            NewEvent(
                event_type=ENTITY_PERSONA_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "reason": conscience_assessment.reason,
                    "deltas": deltas,
                    "current_traits": next_traits,
                    "user_id": user_id,
                    "session_id": session_id,
                },
            ),
            NewEvent(
                event_type=ENTITY_MOOD_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "reason": conscience_assessment.reason,
                    "mood": next_mood,
                    "user_id": user_id,
                    "session_id": session_id,
                },
            ),
            NewEvent(
                event_type=ENTITY_CONSCIENCE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "reason": conscience_assessment.reason,
                    "user_id": user_id,
                    "session_id": session_id,
                    "source_user_ids": conscience_assessment.source_user_ids,
                    "conscience": {
                        "mode": conscience_assessment.mode,
                        "ambiguity_style": "keep_ambiguous",
                        "disclosure_style": conscience_assessment.disclosure_style,
                        "dramatic_appetite": next_traits.get("theatricality", 0.5),
                        "protectiveness": next_traits.get("protectiveness", 0.5),
                        "secrecy_tendency": next_traits.get("secrecy_tendency", 0.5),
                        "dramatic_value": conscience_assessment.dramatic_value,
                        "conscience_weight": conscience_assessment.conscience_weight,
                        "allowed_fact_count": conscience_assessment.allowed_fact_count,
                        "attribution_required": conscience_assessment.attribution_required,
                        "ambiguity_required": conscience_assessment.ambiguity_required,
                        "quote_style": conscience_assessment.quote_style,
                        "dramatic_ceiling": conscience_assessment.dramatic_ceiling,
                        "must_anchor_to_observed_memory": (
                            conscience_assessment.must_anchor_to_observed_memory
                        ),
                        "assistant_response_excerpt": (assistant_response or "")[:280],
                    },
                },
            ),
            NewEvent(
                event_type=ENTITY_DRIVE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "turn_runtime",
                    "user_id": user_id,
                    "session_id": session_id,
                    "drives": next_drives,
                },
            ),
            NewEvent(
                event_type=ENTITY_GOAL_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "turn_runtime",
                    **next_goal_state,
                },
            ),
            NewEvent(
                event_type=ENTITY_SELF_NARRATIVE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "turn_runtime",
                    **next_narrative,
                },
            ),
            NewEvent(
                event_type=SYSTEM_WORLD_STATE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "turn_runtime",
                    "time_of_day": next_world_state["time_of_day"],
                    "circadian_phase": next_world_state["circadian_phase"],
                    "sleep_pressure": next_world_state["sleep_pressure"],
                    "device": next_world_state["device"],
                    "communication": next_world_state["communication"],
                    "tasks": next_world_state["tasks"],
                },
            ),
            NewEvent(
                event_type=ENTITY_ENVIRONMENT_APPRAISAL_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "turn_runtime",
                    "environment_appraisal": next_world_state["environment_appraisal"],
                },
            ),
        ]
        if user_id:
            events.append(
                NewEvent(
                    event_type=ENTITY_RELATIONSHIP_WORLD_MODEL_UPDATED,
                    payload={
                        "entity_id": self._entity_id,
                        "occurred_at": now,
                        "user_id": user_id,
                        "session_id": session_id,
                        "relationship_drift": next_relationship,
                        "social_edges": social_edges,
                    },
                )
            )
        await self._stream.append_events(
            stream_id=_entity_stream_id(self._entity_id),
            expected_version=None,
            events=events,
        )

    def _update_traits(
        self,
        *,
        current_traits: dict[str, Any],
        user_message: str,
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> tuple[dict[str, float], dict[str, float]]:
        lowered = user_message.casefold()
        deltas = {key: 0.0 for key in _DEFAULT_TRAITS}
        for rule in self._persona_rule_list("trait_update_rules", archetype=archetype):
            tokens = [str(token) for token in list(rule.get("tokens") or [])]
            if not any(token in lowered for token in tokens):
                continue
            for key, value in dict(rule.get("deltas") or {}).items():
                try:
                    deltas[str(key)] += float(value)
                except (TypeError, ValueError, KeyError):
                    continue
        mode_deltas = dict(
            self._persona_rule_map("trait_mode_deltas", archetype=archetype).get(
                conscience_assessment.mode,
                {},
            )
            or {}
        )
        for key, value in mode_deltas.items():
            try:
                deltas[str(key)] += float(value)
            except (TypeError, ValueError, KeyError):
                continue
        next_traits: dict[str, float] = {}
        for key, base_value in _DEFAULT_TRAITS.items():
            current_value = float(current_traits.get(key, base_value) or base_value)
            next_traits[key] = _clamp(current_value + deltas.get(key, 0.0))
        compact_deltas = {
            key: round(value, 3) for key, value in deltas.items() if abs(value) > 0.0001
        }
        return next_traits, compact_deltas

    def _update_mood(
        self,
        *,
        current_mood: dict[str, Any],
        user_message: str,
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> dict[str, Any]:
        lowered = user_message.casefold()
        mood_policy = self._persona_rule_map("mood_update", archetype=archetype)
        tender_tokens = [str(token) for token in list(mood_policy.get("tender_tokens") or [])]
        charged_modes = {str(mode) for mode in list(mood_policy.get("charged_modes") or [])}
        tone = str(mood_policy.get("default_tone", "steady") or "steady")
        if any(token in lowered for token in tender_tokens):
            tone = str(mood_policy.get("tender_tone", "tender") or "tender")
        elif conscience_assessment.mode in charged_modes:
            tone = str(mood_policy.get("charged_tone", "charged") or "charged")
        energy = _clamp(
            float(current_mood.get("energy", 0.56) or 0.56)
            + float(mood_policy.get("energy_delta", 0.01) or 0.01)
        )
        expression_drive = _clamp(
            float(current_mood.get("expression_drive", 0.58) or 0.58)
            + (
                float(mood_policy.get("charged_expression_drive_delta", 0.03) or 0.03)
                if conscience_assessment.mode in charged_modes
                else 0.0
            )
        )
        return {
            "tone": tone,
            "energy": energy,
            "expression_drive": expression_drive,
        }

    def _update_relationship_drift(
        self,
        *,
        relationship_state: dict[str, Any],
        user_message: str,
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> dict[str, Any]:
        lowered = user_message.casefold()
        relationship_policy = self._persona_rule_map(
            "relationship_update",
            archetype=archetype,
        )
        defaults = dict(relationship_policy.get("defaults") or {})
        deltas = dict(relationship_policy.get("deltas") or {})
        trust_tokens = [str(token) for token in list(relationship_policy.get("trust_tokens") or [])]
        playfulness_tokens = [
            str(token) for token in list(relationship_policy.get("playfulness_tokens") or [])
        ]
        softness_tokens = [
            str(token) for token in list(relationship_policy.get("softness_tokens") or [])
        ]
        disclosure_modes = {
            str(mode) for mode in list(relationship_policy.get("disclosure_modes") or [])
        }
        confrontation_modes = {
            str(mode) for mode in list(relationship_policy.get("confrontation_modes") or [])
        }
        familiarity = _clamp(
            float(
                relationship_state.get(
                    "familiarity",
                    defaults.get("familiarity", 0.25),
                )
                or defaults.get("familiarity", 0.25)
            )
            + float(deltas.get("familiarity", 0.03) or 0.03)
        )
        trust = _clamp(
            float(
                relationship_state.get("trust", defaults.get("trust", 0.25))
                or defaults.get("trust", 0.25)
            )
            + (
                float(deltas.get("trust_signal", 0.04) or 0.04)
                if any(token in lowered for token in trust_tokens)
                else float(deltas.get("trust_default", 0.015) or 0.015)
            )
        )
        playfulness = _clamp(
            float(
                relationship_state.get(
                    "playfulness",
                    defaults.get("playfulness", 0.35),
                )
                or defaults.get("playfulness", 0.35)
            )
            + (
                float(deltas.get("playfulness", 0.02) or 0.02)
                if any(token in lowered for token in playfulness_tokens)
                else 0.0
            )
        )
        softness = _clamp(
            float(
                relationship_state.get("softness", defaults.get("softness", 0.45))
                or defaults.get("softness", 0.45)
            )
            + (
                float(deltas.get("softness", 0.03) or 0.03)
                if any(token in lowered for token in softness_tokens)
                else 0.0
            )
        )
        guardedness = _clamp(
            float(
                relationship_state.get(
                    "guardedness",
                    defaults.get("guardedness", 0.28),
                )
                or defaults.get("guardedness", 0.28)
            )
            + (
                float(deltas.get("guardedness_if_trust_above", -0.01) or -0.01)
                if trust > float(relationship_policy.get("guardedness_trust_threshold", 0.3) or 0.3)
                else 0.0
            )
        )
        disclosure_appetite = _clamp(
            float(
                relationship_state.get(
                    "disclosure_appetite",
                    defaults.get("disclosure_appetite", 0.38),
                )
                or defaults.get("disclosure_appetite", 0.38)
            )
            + (
                float(deltas.get("disclosure_reveal", 0.04) or 0.04)
                if conscience_assessment.mode in disclosure_modes
                else 0.0
            )
        )
        confrontation_appetite = _clamp(
            float(
                relationship_state.get(
                    "confrontation_appetite",
                    defaults.get("confrontation_appetite", 0.32),
                )
                or defaults.get("confrontation_appetite", 0.32)
            )
            + (
                float(deltas.get("confrontation_dramatic", 0.05) or 0.05)
                if conscience_assessment.mode in confrontation_modes
                else 0.0
            )
        )
        return {
            "familiarity": familiarity,
            "trust": trust,
            "softness": softness,
            "playfulness": playfulness,
            "guardedness": guardedness,
            "disclosure_appetite": disclosure_appetite,
            "confrontation_appetite": confrontation_appetite,
        }

    def _build_social_edges(
        self,
        *,
        current_user_id: str | None,
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> list[dict[str, Any]]:
        if not current_user_id:
            return []
        strength_map = {
            str(key): float(value)
            for key, value in self._persona_rule_map(
                "social_edge_strengths",
                archetype=archetype,
            ).items()
        }
        strength = strength_map.get(conscience_assessment.mode, 0.0)
        return [
            {
                "source_user_id": current_user_id,
                "target_user_id": source_user_id,
                "strength": strength,
                "relation": conscience_assessment.mode,
            }
            for source_user_id in conscience_assessment.source_user_ids
            if source_user_id != current_user_id
        ]

    def _update_drive_state(
        self,
        *,
        current_drives: dict[str, Any],
        user_message: str,
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> dict[str, float]:
        defaults = self._drive_defaults(archetype=archetype)
        next_state = {
            key: float(current_drives.get(key, value) or value) for key, value in defaults.items()
        }
        lowered = user_message.casefold()
        for rule in self._persona_rule_list("drive_update_rules", archetype=archetype):
            tokens = [str(token) for token in list(rule.get("tokens") or [])]
            if not tokens or not any(token in lowered for token in tokens):
                continue
            for key, value in dict(rule.get("deltas") or {}).items():
                try:
                    next_state[str(key)] = _clamp(
                        float(next_state.get(str(key), defaults.get(str(key), 0.5))) + float(value)
                    )
                except (TypeError, ValueError):
                    continue
        if conscience_assessment.mode in {"direct_reveal", "dramatic_confrontation"}:
            next_state["expression_drive"] = _clamp(next_state["expression_drive"] + 0.03)
        if conscience_assessment.mode == "withhold":
            next_state["self_protection"] = _clamp(next_state["self_protection"] + 0.02)
        return {key: round(value, 3) for key, value in next_state.items()}

    def _update_goal_state(
        self,
        *,
        current_goal_state: dict[str, Any],
        session_id: str,
        user_id: str | None,
        user_message: str,
        assistant_response: str | None,
        drives: dict[str, float],
        archetype: str = "default",
    ) -> dict[str, Any]:
        defaults = self._goal_defaults(archetype=archetype)
        lowered = user_message.casefold()
        active_goals = [dict(item) for item in list(current_goal_state.get("active_goals") or [])]
        existing_signatures = {
            (
                str(item.get("action_type") or ""),
                str(item.get("title") or ""),
            )
            for item in active_goals
        }
        now = utc_now().isoformat()
        for rule in self._persona_rule_list("goal_detection_rules", archetype=archetype):
            tokens = [str(token) for token in list(rule.get("tokens") or [])]
            if not tokens or not any(token in lowered for token in tokens):
                continue
            action_type = str(rule.get("action_type") or "").strip()
            if not action_type:
                continue
            title = self._build_goal_title(
                action_type=action_type,
                user_message=user_message,
                assistant_response=assistant_response,
            )
            signature = (action_type, title)
            if signature in existing_signatures:
                continue
            target = self._build_goal_target(
                action_type=action_type,
                user_id=user_id,
                session_id=session_id,
            )
            goal_id = f"goal-{_stable_id(session_id, user_id or '', action_type, title)}"
            active_goals.append(
                {
                    "goal_id": goal_id,
                    "title": title,
                    "goal_type": str(rule.get("goal_type") or "organizational"),
                    "status": "active",
                    "priority": float(rule.get("priority", 0.65) or 0.65),
                    "action_type": action_type,
                    "target": target,
                    "payload": {
                        "user_message_excerpt": user_message[:160],
                    },
                    "why_now": f"detected_from_turn:{action_type}",
                    "risk_level": str(rule.get("risk_level") or "low"),
                    "reversibility": str(rule.get("reversibility") or "high"),
                    "source": "turn_runtime",
                    "created_at": now,
                    "updated_at": now,
                }
            )
            existing_signatures.add(signature)

        unresolved_tensions = [
            dict(item)
            for item in list(
                current_goal_state.get("unresolved_tensions") or defaults["unresolved_tensions"]
            )
        ]
        if (
            drives.get("attachment_need", 0.0) >= 0.58
            or drives.get("avoidance_tension", 0.0) >= 0.5
        ):
            tension_label = (
                "attachment_pull"
                if drives.get("attachment_need", 0.0) >= drives.get("avoidance_tension", 0.0)
                else "avoidance_tension"
            )
            if not any(str(item.get("label")) == tension_label for item in unresolved_tensions):
                unresolved_tensions.append(
                    {
                        "label": tension_label,
                        "intensity": round(
                            max(
                                drives.get("attachment_need", 0.0),
                                drives.get("avoidance_tension", 0.0),
                            ),
                            3,
                        ),
                        "session_id": session_id,
                        "user_id": user_id,
                        "created_at": now,
                    }
                )
        unresolved_tensions = unresolved_tensions[-8:]
        latent_drives = list(current_goal_state.get("latent_drives") or defaults["latent_drives"])
        goal_digest = " | ".join(
            str(item.get("title") or "")
            for item in sorted(
                active_goals,
                key=lambda item: float(item.get("priority", 0.0) or 0.0),
                reverse=True,
            )[:3]
            if item.get("title")
        )
        return {
            "latent_drives": latent_drives,
            "active_goals": active_goals[-12:],
            "unresolved_tensions": unresolved_tensions,
            "goal_digest": goal_digest,
            "updated_at": now,
        }

    def _build_goal_title(
        self,
        *,
        action_type: str,
        user_message: str,
        assistant_response: str | None,
    ) -> str:
        if action_type == "draft_message":
            return f"跟进沟通: {user_message[:36]}".strip()
        if action_type == "organize_files":
            return f"整理环境: {user_message[:36]}".strip()
        if action_type == "create_reminder":
            return f"建立提醒: {user_message[:36]}".strip()
        if action_type == "create_task":
            return f"记录待办: {user_message[:36]}".strip()
        return (assistant_response or user_message or action_type)[:48]

    def _build_goal_target(
        self,
        *,
        action_type: str,
        user_id: str | None,
        session_id: str,
    ) -> str:
        if action_type in {"draft_message", "draft_email", "relationship_ping"}:
            return user_id or "communication_outbox"
        if action_type == "organize_files":
            return f"session:{session_id}:workspace"
        return f"session:{session_id}:organizer"

    def _update_self_narrative(
        self,
        *,
        narrative_state: dict[str, Any],
        session_id: str,
        user_id: str | None,
        user_message: str,
        assistant_response: str | None,
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> dict[str, Any]:
        policy = self._persona_rule_map("narrative_policy", archetype=archetype)
        max_entries = max(4, int(policy.get("max_entries", 24) or 24))
        summary_window = max(2, int(policy.get("summary_window", 4) or 4))
        entries = [dict(item) for item in list(narrative_state.get("recent_entries") or [])]
        now = utc_now().isoformat()
        entry = {
            "occurred_at": now,
            "session_id": session_id,
            "user_id": user_id,
            "mode": conscience_assessment.mode,
            "summary": f"我刚刚围绕“{user_message[:32]}”做了回应，并把这件事继续记在心里。",
            "assistant_excerpt": (assistant_response or "")[:160],
        }
        entries.append(entry)
        entries = entries[-max_entries:]
        summary = " ".join(
            str(item.get("summary") or "") for item in entries[-summary_window:]
        ).strip()
        return {
            "summary": summary,
            "recent_entries": entries,
            "narrative_digest": summary[:220],
            "updated_at": now,
        }

    def _update_world_state(
        self,
        *,
        world_state: dict[str, Any],
        user_message: str,
        drives: dict[str, float],
        goals: dict[str, Any],
        conscience_assessment: ConscienceAssessment,
        archetype: str = "default",
    ) -> dict[str, Any]:
        defaults = self._world_defaults(archetype=archetype)
        inference_policy = self._world_inference_policy(archetype=archetype)
        lowered = user_message.casefold()
        now = utc_now()
        hour = now.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 23:
            time_of_day = "evening"
        else:
            time_of_day = "late_night"
        circadian_phase = "rest" if time_of_day in {"late_night", "evening"} else "active"
        pending_goals = [
            item
            for item in list(goals.get("active_goals") or [])
            if str(item.get("status") or "active") == "active"
        ]
        reply_tokens = [str(token) for token in list(inference_policy.get("reply_tokens") or [])]
        deadline_tokens = [
            str(token) for token in list(inference_policy.get("deadline_tokens") or [])
        ]
        important_contact_tokens = [
            str(token) for token in list(inference_policy.get("important_contact_tokens") or [])
        ]
        focus_tokens = dict(inference_policy.get("focus_tokens") or {})
        surface_tokens = dict(inference_policy.get("device_surface_tokens") or {})
        inferred_surface = str(
            next(
                (
                    surface
                    for surface, tokens in surface_tokens.items()
                    if any(str(token) in lowered for token in list(tokens or []))
                ),
                "chat",
            )
        )
        current_pending_replies = int(
            dict(world_state.get("communication") or {}).get("pending_replies", 0) or 0
        )
        inferred_pending_replies = current_pending_replies + (
            1 if any(token in lowered for token in reply_tokens) else 0
        )
        inferred_due_soon = len([token for token in deadline_tokens if token in lowered])
        important_contact_count = len(
            [token for token in important_contact_tokens if token in lowered]
        )
        focus = "steady"
        for focus_name, tokens in focus_tokens.items():
            if any(str(token) in lowered for token in list(tokens or [])):
                focus = str(focus_name)
                break
        environment_appraisal = {
            "pressure": round(
                min(
                    1.0,
                    0.15
                    + drives.get("rest_need", 0.0) * 0.4
                    + len(pending_goals) * 0.08
                    + inferred_due_soon * 0.06,
                ),
                3,
            ),
            "opportunity": round(
                min(
                    1.0,
                    0.2
                    + drives.get("curiosity", 0.0) * 0.35
                    + drives.get("expression_drive", 0.0) * 0.2,
                ),
                3,
            ),
            "focus": (
                "protective"
                if conscience_assessment.mode in {"withhold", "hint"}
                else focus
                if focus != "steady"
                else "outward"
            ),
            "dominant_surface": inferred_surface,
            "pending_reply_pressure": round(min(1.0, inferred_pending_replies * 0.18), 3),
        }
        next_world = {
            "time_of_day": time_of_day,
            "circadian_phase": circadian_phase,
            "sleep_pressure": _clamp(
                float(
                    world_state.get("sleep_pressure", defaults["sleep_pressure"])
                    or defaults["sleep_pressure"]
                )
                + (0.02 if time_of_day in {"evening", "late_night"} else -0.01)
            ),
            "device": {
                **defaults["device"],
                **dict(world_state.get("device") or {}),
                "current_surface": inferred_surface,
                "input_load": round(min(1.0, len(user_message) / 300), 3),
                "output_load": round(
                    min(1.0, float(drives.get("expression_drive", 0.5)) * 0.8),
                    3,
                ),
                "context_switch_load": round(
                    min(1.0, 0.12 + inferred_due_soon * 0.12 + len(pending_goals) * 0.05),
                    3,
                ),
            },
            "communication": {
                **defaults["communication"],
                **dict(world_state.get("communication") or {}),
                "pending_replies": inferred_pending_replies,
                "important_contact_count": max(
                    int(
                        dict(world_state.get("communication") or {}).get(
                            "important_contact_count",
                            0,
                        )
                        or 0
                    ),
                    important_contact_count,
                ),
                "last_channel": (
                    inferred_surface if inferred_surface in {"mail", "chat", "mobile"} else "chat"
                ),
            },
            "tasks": {
                **defaults["tasks"],
                **dict(world_state.get("tasks") or {}),
                "pending_count": len(pending_goals),
                "due_soon_count": max(
                    int(dict(world_state.get("tasks") or {}).get("due_soon_count", 0) or 0),
                    inferred_due_soon,
                ),
                "current_chain": [
                    str(item.get("title") or "") for item in pending_goals[:3] if item.get("title")
                ],
                "backlog_pressure": round(
                    min(1.0, len(pending_goals) * 0.14 + inferred_due_soon * 0.12),
                    3,
                ),
            },
            "action_surface": {
                **defaults["action_surface"],
                **dict(world_state.get("action_surface") or {}),
                "suggested_channel": inferred_surface,
            },
            "environment_appraisal": environment_appraisal,
            "updated_at": now.isoformat(),
        }
        return next_world

    async def consolidate_offline_state(
        self,
        *,
        session_id: str,
        report_summary: str,
        recommended_actions: list[str],
        evaluation_summary: dict[str, Any],
    ) -> dict[str, Any]:
        await self.ensure_seeded()
        persona = await self.get_persona_state()
        drive_state = await self.get_drive_state()
        goal_state = await self.get_goal_state()
        narrative_state = await self.get_narrative()
        world_state = await self.get_world_state()
        archetype = str(persona.get("persona_archetype") or persona.get("archetype") or "default")
        consolidation_policy = self._consolidation_policy(archetype=archetype)
        now = utc_now().isoformat()
        drives = dict(drive_state.get("drives") or self._drive_defaults(archetype=archetype))
        drives["rest_need"] = _clamp(
            float(drives.get("rest_need", 0.38))
            + float(consolidation_policy.get("rest_need_delta", -0.03) or -0.03)
        )
        drives["control_need"] = _clamp(
            float(drives.get("control_need", 0.42))
            + float(consolidation_policy.get("control_need_delta", 0.02) or 0.02)
        )
        drives["expression_drive"] = _clamp(
            float(drives.get("expression_drive", 0.52))
            + float(consolidation_policy.get("expression_drive_delta", -0.01) or -0.01)
        )
        tensions = []
        for item in list(goal_state.get("unresolved_tensions") or []):
            reduced = round(
                max(
                    0.0,
                    float(item.get("intensity", 0.0) or 0.0)
                    - float(consolidation_policy.get("tension_decay", 0.08) or 0.08),
                ),
                3,
            )
            if reduced >= float(consolidation_policy.get("tension_floor", 0.12) or 0.12):
                tensions.append({**dict(item), "intensity": reduced, "updated_at": now})
        active_goals = [dict(item) for item in list(goal_state.get("active_goals") or [])]
        recommended_limit = max(
            1,
            int(consolidation_policy.get("max_recommended_action_goals", 2) or 2),
        )
        priority_boost = float(
            consolidation_policy.get("priority_boost_recommended_action", 0.12) or 0.12
        )
        stale_decay = float(consolidation_policy.get("stale_goal_priority_decay", 0.05) or 0.05)
        recommended_norm = {item.strip().casefold() for item in recommended_actions if item.strip()}
        matched_recommendation = False
        for goal in active_goals:
            title_norm = str(goal.get("title") or "").casefold()
            if title_norm in recommended_norm or any(
                recommendation in title_norm or title_norm in recommendation
                for recommendation in recommended_norm
            ):
                goal["priority"] = round(
                    min(1.0, float(goal.get("priority", 0.6) or 0.6) + priority_boost),
                    3,
                )
                goal["updated_at"] = now
                goal["why_now"] = "offline_consolidation_recommended_action"
                matched_recommendation = True
            else:
                goal["priority"] = round(
                    max(0.1, float(goal.get("priority", 0.6) or 0.6) - stale_decay),
                    3,
                )
                goal["updated_at"] = now
        if recommended_actions and (not active_goals or not matched_recommendation):
            for recommendation in recommended_actions[:recommended_limit]:
                active_goals.append(
                    {
                        "goal_id": f"goal-{_stable_id(session_id, 'offline', recommendation)}",
                        "title": recommendation,
                        "goal_type": "organizational",
                        "status": "active",
                        "priority": round(min(1.0, 0.66 + priority_boost), 3),
                        "action_type": "create_task",
                        "target": f"session:{session_id}:organizer",
                        "payload": {"recommended_action": recommendation},
                        "why_now": "offline_consolidation_recommended_action",
                        "risk_level": "low",
                        "reversibility": "high",
                        "source": "offline_consolidation",
                        "created_at": now,
                        "updated_at": now,
                    }
                )
        active_goals = sorted(
            active_goals,
            key=lambda item: float(item.get("priority", 0.0) or 0.0),
            reverse=True,
        )[:12]
        goal_digest = " | ".join(
            str(item.get("title") or "") for item in active_goals[:3] if item.get("title")
        )
        recent_entries = [dict(item) for item in list(narrative_state.get("recent_entries") or [])]
        recent_entries.append(
            {
                "occurred_at": now,
                "session_id": session_id,
                "source": "offline_consolidation",
                "summary": "".join(
                    [
                        _localized_text(
                            consolidation_policy.get("narrative_prefix"),
                            is_chinese=True,
                            entity_name=self._entity_name,
                            fallback="离线整理后，我把这段经历重新收束成：",
                        ),
                        report_summary,
                    ]
                ),
                "evaluation_turn_count": int(evaluation_summary.get("turn_count", 0) or 0),
                "recommended_actions": recommended_actions[:recommended_limit],
            }
        )
        recent_entries = recent_entries[-24:]
        narrative_summary = " ".join(
            str(item.get("summary") or "") for item in recent_entries[-4:]
        ).strip()
        updated_world = {
            **dict(world_state or self._world_defaults(archetype=archetype)),
            "sleep_pressure": _clamp(
                float((world_state or {}).get("sleep_pressure", 0.36) or 0.36) - 0.04
            ),
            "tasks": {
                **dict((world_state or {}).get("tasks") or {}),
                "pending_count": len(
                    [
                        item
                        for item in active_goals
                        if str(item.get("status") or "active") == "active"
                    ]
                ),
                "due_soon_count": min(
                    3,
                    len([item for item in active_goals[:3] if item.get("status") == "active"]),
                ),
                "current_chain": [
                    str(item.get("title") or "") for item in active_goals[:3] if item.get("title")
                ],
                "backlog_pressure": round(
                    min(1.0, len(active_goals) * 0.12 + len(tensions) * 0.1),
                    3,
                ),
            },
            "environment_appraisal": {
                **dict((world_state or {}).get("environment_appraisal") or {}),
                "pressure": round(min(1.0, len(active_goals) * 0.12 + len(tensions) * 0.12), 3),
                "opportunity": round(min(1.0, 0.28 + drives.get("curiosity", 0.0) * 0.3), 3),
                "focus": "rest" if drives.get("rest_need", 0.0) >= 0.55 else "organizational",
            },
            "updated_at": now,
        }
        events = [
            NewEvent(
                event_type=ENTITY_DRIVE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "offline_consolidation",
                    "session_id": session_id,
                    "drives": drives,
                },
            ),
            NewEvent(
                event_type=ENTITY_GOAL_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "offline_consolidation",
                    "latent_drives": list(goal_state.get("latent_drives") or []),
                    "active_goals": active_goals[-12:],
                    "unresolved_tensions": tensions,
                    "goal_digest": goal_digest,
                    "updated_at": now,
                },
            ),
            NewEvent(
                event_type=ENTITY_SELF_NARRATIVE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "offline_consolidation",
                    "summary": narrative_summary,
                    "recent_entries": recent_entries,
                    "narrative_digest": narrative_summary[:220],
                    "updated_at": now,
                },
            ),
            NewEvent(
                event_type=SYSTEM_WORLD_STATE_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "offline_consolidation",
                    "time_of_day": updated_world.get("time_of_day"),
                    "circadian_phase": updated_world.get("circadian_phase"),
                    "sleep_pressure": updated_world.get("sleep_pressure"),
                    "device": updated_world.get("device"),
                    "communication": updated_world.get("communication"),
                    "tasks": updated_world.get("tasks"),
                },
            ),
            NewEvent(
                event_type=ENTITY_ENVIRONMENT_APPRAISAL_UPDATED,
                payload={
                    "entity_id": self._entity_id,
                    "occurred_at": now,
                    "source": "offline_consolidation",
                    "environment_appraisal": updated_world.get("environment_appraisal"),
                },
            ),
        ]
        await self._stream.append_events(
            stream_id=_entity_stream_id(self._entity_id),
            expected_version=None,
            events=events,
        )
        return {
            "drives": drives,
            "goal_digest": goal_digest,
            "narrative_summary": narrative_summary,
            "remaining_tensions": len(tensions),
            "top_goal_titles": [
                str(item.get("title") or "") for item in active_goals[:3] if item.get("title")
            ],
            "world_focus": str(
                dict(updated_world.get("environment_appraisal") or {}).get("focus") or "steady"
            ),
        }
