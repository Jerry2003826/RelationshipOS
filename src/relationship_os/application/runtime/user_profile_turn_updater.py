from __future__ import annotations

import logging
from typing import Any

from relationship_os.application.analyzers.user_profile import (
    UserProfileStore,
    format_profile_prefix,
)
from relationship_os.domain.events import utc_now

logger = logging.getLogger(__name__)


class UserProfileTurnUpdater:
    def __init__(
        self,
        *,
        user_service: Any = None,
        profile_store: UserProfileStore | None = None,
    ) -> None:
        self._user_service = user_service
        self._profile_store = profile_store or UserProfileStore()

    @property
    def profile_store(self) -> UserProfileStore:
        return self._profile_store

    async def restore_snapshot(self, *, user_id: str) -> None:
        user_service = self._user_service
        if user_service is None or not hasattr(user_service, "get_user_index"):
            return
        store = self._profile_store
        if store.get(user_id) is not None:
            return
        try:
            user_index = await user_service.get_user_index(user_id=user_id)
        except Exception:
            return
        metadata = user_index.get("metadata") if isinstance(user_index, dict) else None
        if not isinstance(metadata, dict):
            return
        profile_snapshot = metadata.get("profile_ema_128")
        if not isinstance(profile_snapshot, dict):
            return
        vector = profile_snapshot.get("vector")
        if isinstance(vector, list) and len(vector) == store.dim:
            store.load({user_id: vector})

    async def update_for_turn(
        self,
        *,
        user_id: str | None,
        user_message: str,
        readonly_probe_session: bool,
    ) -> str | None:
        if readonly_probe_session or not user_id or not user_message.strip():
            return None
        await self.restore_snapshot(user_id=user_id)
        store = self._profile_store
        vec = store.update(user_id, user_message)
        prefix = format_profile_prefix(vec, top_k=8)

        user_service = self._user_service
        if user_service is not None and hasattr(user_service, "update_profile"):
            try:
                await user_service.update_profile(
                    user_id=user_id,
                    metadata={
                        "profile_ema_128": {
                            "dim": int(vec.size),
                            "turns_seen": store.turns_seen(user_id),
                            "updated_at": utc_now().isoformat(),
                            "prefix": prefix,
                            "vector": [round(float(x), 6) for x in vec.tolist()],
                        }
                    },
                )
            except Exception:
                logger.warning("Failed to persist profile snapshot for user %s", user_id)
        return prefix
