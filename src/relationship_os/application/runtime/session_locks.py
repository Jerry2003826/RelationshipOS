import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class SessionLockRegistry:
    """Owns per-session locks so RuntimeService stays focused on turn orchestration."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._guard = asyncio.Lock()

    async def get_lock(self, session_id: str) -> asyncio.Lock:
        async with self._guard:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[session_id] = lock
            return lock

    @asynccontextmanager
    async def locked(self, session_id: str) -> AsyncIterator[None]:
        lock = await self.get_lock(session_id)
        async with lock:
            yield
