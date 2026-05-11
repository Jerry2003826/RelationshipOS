import asyncio
from types import SimpleNamespace

from relationship_os.application.runtime.post_turn_effects import PostTurnEffects


def test_post_turn_effects_runs_entity_update_and_action_execution() -> None:
    calls: dict[str, list[dict[str, object]]] = {"entity": [], "action": []}

    class _EntityService:
        async def update_after_turn(self, **kwargs):  # type: ignore[no-untyped-def]
            calls["entity"].append(kwargs)

        async def get_persona_state(self):  # type: ignore[no-untyped-def]
            return {"persona_archetype": "steady_friend"}

        async def get_goal_state(self):  # type: ignore[no-untyped-def]
            return {"goal": "stay_present"}

        async def get_world_state(self):  # type: ignore[no-untyped-def]
            return {"weather": "quiet"}

    class _ActionService:
        async def plan_and_execute(self, **kwargs):  # type: ignore[no-untyped-def]
            calls["action"].append(kwargs)

    analysis = SimpleNamespace(
        recalled_memory=["memory-card"],
        conscience_assessment={"mode": "allow", "reason": "safe"},
    )
    reply_artifacts = SimpleNamespace(assistant_response="我在。")

    timings = asyncio.run(
        PostTurnEffects(
            entity_service=_EntityService(),
            action_service=_ActionService(),
            entity_id="entity:test",
        ).run_entity_and_action_effects(
            readonly_probe_session=False,
            analysis=analysis,
            turn_context=SimpleNamespace(user_id="lin"),
            session_id="session-1",
            user_message="在吗",
            reply_artifacts=reply_artifacts,
        )
    )

    assert calls["entity"][0]["recalled_memory"] == ["memory-card"]
    assert calls["entity"][0]["conscience_assessment"].mode == "allow"
    assert calls["action"][0]["entity_id"] == "entity:test"
    assert calls["action"][0]["archetype"] == "steady_friend"
    assert timings.entity_update_ms >= 0
    assert timings.action_ms >= 0


def test_post_turn_effects_skips_mutations_for_probe_sessions() -> None:
    class _EntityService:
        async def update_after_turn(self, **_kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("probe sessions should not update entity state")

    class _ActionService:
        async def plan_and_execute(self, **_kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("probe sessions should not execute actions")

    timings = asyncio.run(
        PostTurnEffects(
            entity_service=_EntityService(),
            action_service=_ActionService(),
            entity_id="entity:test",
        ).run_entity_and_action_effects(
            readonly_probe_session=True,
            analysis=SimpleNamespace(recalled_memory=[], conscience_assessment={}),
            turn_context=SimpleNamespace(user_id="lin"),
            session_id="session-1",
            user_message="在吗",
            reply_artifacts=SimpleNamespace(assistant_response="嗯。"),
        )
    )

    assert timings.entity_update_ms >= 0
    assert timings.action_ms >= 0

