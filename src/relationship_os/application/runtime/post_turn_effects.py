import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class PostTurnEffectTimings:
    entity_update_ms: float
    action_ms: float


class PostTurnEffects:
    """Runs best-effort side effects after turn events are safely appended."""

    def __init__(
        self,
        *,
        entity_service: Any = None,
        action_service: Any = None,
        entity_id: str = "server",
    ) -> None:
        self._entity_service = entity_service
        self._action_service = action_service
        self._entity_id = entity_id

    async def run_entity_and_action_effects(
        self,
        *,
        readonly_probe_session: bool,
        analysis: Any | None,
        turn_context: Any,
        session_id: str,
        user_message: str,
        reply_artifacts: Any,
    ) -> PostTurnEffectTimings:
        stage_started = perf_counter()
        if not readonly_probe_session and self._entity_service is not None and analysis is not None:
            try:
                await self._entity_service.update_after_turn(
                    user_id=turn_context.user_id,
                    session_id=session_id,
                    user_message=user_message,
                    assistant_response=reply_artifacts.assistant_response,
                    recalled_memory=analysis.recalled_memory,
                    conscience_assessment=build_entity_service_assessment(analysis),
                )
            except Exception:
                logger.warning(
                    "Failed to update entity state for session %s",
                    session_id,
                    exc_info=True,
                )
        entity_update_ms = round((perf_counter() - stage_started) * 1000.0, 1)

        stage_started = perf_counter()
        if (
            not readonly_probe_session
            and self._action_service is not None
            and self._entity_service is not None
        ):
            try:
                persona_state = await self._entity_service.get_persona_state()
                goal_state = await self._entity_service.get_goal_state()
                world_state = await self._entity_service.get_world_state()
                await self._action_service.plan_and_execute(
                    entity_id=self._entity_id,
                    user_id=turn_context.user_id,
                    session_id=session_id,
                    user_message=user_message,
                    assistant_response=reply_artifacts.assistant_response,
                    archetype=str(
                        persona_state.get("persona_archetype")
                        or persona_state.get("archetype")
                        or "default"
                    ),
                    goal_state=goal_state,
                    world_state=world_state,
                )
            except Exception:
                logger.warning(
                    "Failed to plan or execute entity actions for session %s",
                    session_id,
                    exc_info=True,
                )
        action_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        return PostTurnEffectTimings(
            entity_update_ms=entity_update_ms,
            action_ms=action_ms,
        )


def build_entity_service_assessment(analysis: Any) -> Any:
    from relationship_os.application.entity_service import ConscienceAssessment

    return ConscienceAssessment(
        mode=str(analysis.conscience_assessment.get("mode", "withhold")),
        reason=str(analysis.conscience_assessment.get("reason", "")),
        disclosure_style=str(analysis.conscience_assessment.get("disclosure_style", "hint")),
        dramatic_value=float(analysis.conscience_assessment.get("dramatic_value", 0.0) or 0.0),
        conscience_weight=float(
            analysis.conscience_assessment.get("conscience_weight", 0.55) or 0.55
        ),
        source_user_ids=list(analysis.conscience_assessment.get("source_user_ids") or []),
        allowed_fact_count=int(analysis.conscience_assessment.get("allowed_fact_count", 0) or 0),
        attribution_required=bool(
            analysis.conscience_assessment.get("attribution_required", False)
        ),
        ambiguity_required=bool(analysis.conscience_assessment.get("ambiguity_required", True)),
        quote_style=str(analysis.conscience_assessment.get("quote_style", "opaque")),
        dramatic_ceiling=float(
            analysis.conscience_assessment.get("dramatic_ceiling", 0.18) or 0.18
        ),
        must_anchor_to_observed_memory=bool(
            analysis.conscience_assessment.get(
                "must_anchor_to_observed_memory",
                False,
            )
        ),
    )
