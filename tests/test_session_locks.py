import asyncio

from relationship_os.application.runtime.session_locks import SessionLockRegistry


def test_session_lock_registry_reuses_locks_per_session() -> None:
    registry = SessionLockRegistry()

    first = asyncio.run(registry.get_lock("session-a"))
    second = asyncio.run(registry.get_lock("session-a"))
    other = asyncio.run(registry.get_lock("session-b"))

    assert first is second
    assert other is not first

