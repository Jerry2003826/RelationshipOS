import asyncio
from types import SimpleNamespace

from relationship_os.application.runtime.memory_scope_syncer import MemoryScopeSyncer


def test_memory_scope_syncer_refreshes_default_profile_memory_scope() -> None:
    class _MemoryService:
        def __init__(self) -> None:
            self.refreshes: list[dict[str, object]] = []

        async def refresh_memory_scope(self, **kwargs):  # type: ignore[no-untyped-def]
            self.refreshes.append(kwargs)

    memory_service = _MemoryService()
    syncer = MemoryScopeSyncer(
        memory_service=memory_service,
        entity_service=None,
        entity_id="entity:test",
        runtime_profile="default",
    )

    asyncio.run(
        syncer.sync_after_turn(
            session_id="session-1",
            user_id="user-1",
            turn_index=3,
            user_message_text="hello",
            analysis=SimpleNamespace(edge_runtime_plan={}),
        )
    )

    assert memory_service.refreshes == [
        {"session_id": "session-1", "user_id": "user-1"}
    ]


def test_memory_scope_syncer_skips_edge_probe_messages() -> None:
    class _MemoryService:
        async def upsert_memory_scope(self, **_kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("edge probe messages should not upsert memory scope")

    syncer = MemoryScopeSyncer(
        memory_service=_MemoryService(),
        entity_service=object(),
        entity_id="entity:test",
        runtime_profile="edge_desktop_4b",
        is_presence_probe=lambda text: text == "presence?",
    )

    asyncio.run(
        syncer.sync_after_turn(
            session_id="session-1",
            user_id="user-1",
            turn_index=3,
            user_message_text="presence?",
            analysis=SimpleNamespace(edge_runtime_plan={}),
        )
    )

