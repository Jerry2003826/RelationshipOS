import asyncio
import logging
from collections.abc import Callable
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)


class MemoryScopeSyncer:
    """Coordinates best-effort memory scope sync after a completed turn."""

    def __init__(
        self,
        *,
        memory_service: Any,
        entity_service: Any = None,
        entity_id: str = "server",
        runtime_profile: str = "default",
        checkpoint_turns: dict[str, int] | None = None,
        checkpoint_times: dict[str, float] | None = None,
        factual_shadow_tasks: dict[str, asyncio.Task[None]] | None = None,
        background_tasks: dict[str, asyncio.Task[None]] | None = None,
        background_pending: dict[str, dict[str, Any]] | None = None,
        is_presence_probe: Callable[[str], bool] | None = None,
        is_edge_fact_deposition: Callable[[str], bool] | None = None,
        is_edge_status_update: Callable[[str], bool] | None = None,
    ) -> None:
        self._memory_service = memory_service
        self._entity_service = entity_service
        self._entity_id = entity_id
        self._runtime_profile = runtime_profile
        self._checkpoint_turns = checkpoint_turns if checkpoint_turns is not None else {}
        self._checkpoint_times = checkpoint_times if checkpoint_times is not None else {}
        self._factual_shadow_tasks = (
            factual_shadow_tasks if factual_shadow_tasks is not None else {}
        )
        self._background_tasks = background_tasks if background_tasks is not None else {}
        self._background_pending = background_pending if background_pending is not None else {}
        self._is_presence_probe = is_presence_probe or (lambda _text: False)
        self._is_edge_fact_deposition = is_edge_fact_deposition or (lambda _text: False)
        self._is_edge_status_update = is_edge_status_update or (lambda _text: False)

    async def sync_after_turn(
        self,
        *,
        session_id: str,
        user_id: str | None,
        turn_index: int,
        user_message_text: str,
        analysis: Any,
    ) -> None:
        if self._is_friend_chat_profile():
            deliberation_mode = str(
                analysis.edge_runtime_plan.get(
                    "interpreted_deliberation_mode",
                    analysis.edge_runtime_plan.get("deliberation_mode", "light_recall"),
                )
                or "light_recall"
            )
            compact = deliberation_mode != "deep_recall"
            if deliberation_mode == "deep_recall":
                await self._memory_service.upsert_memory_scope(
                    session_id=session_id,
                    user_id=user_id,
                    entity_id=self._entity_id_if_available(),
                    compact=compact,
                    sync_factual_shadow=False,
                )
                self._checkpoint_turns[session_id] = turn_index
                self._checkpoint_times[session_id] = perf_counter()
                self.schedule_factual_shadow_sync(
                    session_id=session_id,
                    user_id=user_id,
                    compact=compact,
                )
            else:
                should_sync, sync_reason, required_gap = self.should_checkpoint(
                    session_id=session_id,
                    turn_index=turn_index,
                    analysis=analysis,
                )
                if not should_sync:
                    logger.info(
                        "friend_chat_memory_scope_sync_skipped "
                        "session_id=%s user_id=%s turn_index=%s reason=%s",
                        session_id,
                        user_id,
                        turn_index,
                        sync_reason,
                    )
                    return
                self.queue_background_memory_scope_sync(
                    session_id=session_id,
                    user_id=user_id,
                    turn_index=turn_index,
                    compact=compact,
                    required_gap=required_gap,
                )
            return
        if self._is_edge_profile():
            if (
                self._is_presence_probe(user_message_text)
                or self._is_edge_fact_deposition(user_message_text)
                or self._is_edge_status_update(user_message_text)
            ):
                return
            await self._memory_service.upsert_memory_scope(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id_if_available(),
                compact=True,
            )
            return
        await self._memory_service.refresh_memory_scope(
            session_id=session_id,
            user_id=user_id,
        )

    def friend_chat_memory_scope_required_gap(self, *, analysis: Any) -> int:
        intent = str(
            analysis.edge_runtime_plan.get("interpreted_intent")
            or analysis.edge_runtime_plan.get("intent")
            or ""
        ).strip()
        if intent in {
            "factual_recall",
            "fact_deposition",
            "social_disclosure",
            "persona_state_probe",
            "state_reflection_probe",
            "relationship_reflection_probe",
        }:
            return 4
        return 12

    def should_checkpoint(
        self,
        *,
        session_id: str,
        turn_index: int,
        analysis: Any,
    ) -> tuple[bool, str, int]:
        required_gap = self.friend_chat_memory_scope_required_gap(analysis=analysis)
        last_turn = self._checkpoint_turns.get(session_id)
        if last_turn is None:
            return True, "initial", required_gap
        turns_since = max(0, turn_index - last_turn)
        if turns_since >= required_gap:
            return True, f"turn_gap_{required_gap}", required_gap
        last_at = self._checkpoint_times.get(session_id)
        if last_at is not None and (perf_counter() - last_at) >= 120.0 and turns_since >= 2:
            return True, "time_gap", required_gap
        return False, "checkpoint_not_due", required_gap

    def should_checkpoint_pending(
        self,
        *,
        session_id: str,
        turn_index: int,
        required_gap: int,
    ) -> bool:
        last_turn = self._checkpoint_turns.get(session_id)
        if last_turn is None:
            return True
        turns_since = max(0, turn_index - last_turn)
        if turns_since >= required_gap:
            return True
        last_at = self._checkpoint_times.get(session_id)
        if last_at is not None and (perf_counter() - last_at) >= 120.0 and turns_since >= 2:
            return True
        return False

    def schedule_factual_shadow_sync(
        self,
        *,
        session_id: str,
        user_id: str | None,
        compact: bool,
    ) -> None:
        if not hasattr(self._memory_service, "sync_factual_shadow_for_session"):
            return
        existing = self._factual_shadow_tasks.get(session_id)
        if existing is not None and not existing.done():
            logger.info(
                "friend_chat_factual_shadow_sync_skipped session_id=%s user_id=%s reason=in_flight",
                session_id,
                user_id,
            )
            return

        async def _runner() -> None:
            result = await self._memory_service.sync_factual_shadow_for_session(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id_if_available(),
                compact=compact,
            )
            logger.info(
                "friend_chat_factual_shadow_sync_result session_id=%s user_id=%s status=%s "
                "fact_count=%s elapsed_ms=%s",
                session_id,
                user_id,
                result.get("status"),
                result.get("fact_count"),
                result.get("elapsed_ms"),
            )

        task = asyncio.create_task(_runner())
        self._factual_shadow_tasks[session_id] = task

        def _cleanup(done_task: asyncio.Task[None]) -> None:
            current = self._factual_shadow_tasks.get(session_id)
            if current is done_task:
                self._factual_shadow_tasks.pop(session_id, None)
            try:
                done_task.result()
            except Exception:
                logger.warning(
                    "friend_chat_factual_shadow_sync_task_failed session_id=%s user_id=%s",
                    session_id,
                    user_id,
                    exc_info=True,
                )

        task.add_done_callback(_cleanup)

    def queue_background_memory_scope_sync(
        self,
        *,
        session_id: str,
        user_id: str | None,
        turn_index: int,
        compact: bool,
        required_gap: int,
    ) -> None:
        existing = self._background_tasks.get(session_id)
        if existing is not None and not existing.done():
            queued = self._background_pending.get(session_id) or {
                "session_id": session_id,
                "user_id": user_id,
                "turn_index": turn_index,
                "compact": compact,
                "required_gap": required_gap,
            }
            queued["compact"] = bool(queued.get("compact", True)) and compact
            if user_id:
                queued["user_id"] = user_id
            queued["turn_index"] = max(int(queued.get("turn_index", 0) or 0), turn_index)
            queued["required_gap"] = min(
                int(queued.get("required_gap", required_gap) or required_gap),
                required_gap,
            )
            self._background_pending[session_id] = queued
            logger.info(
                "friend_chat_memory_scope_sync_queued "
                "session_id=%s user_id=%s turn_index=%s compact=%s required_gap=%s "
                "reason=in_flight",
                session_id,
                user_id,
                turn_index,
                compact,
                required_gap,
            )
            return

        self.start_background_memory_scope_sync(
            session_id=session_id,
            user_id=user_id,
            trigger_turn_index=turn_index,
            compact=compact,
            required_gap=required_gap,
        )

    def start_background_memory_scope_sync(
        self,
        *,
        session_id: str,
        user_id: str | None,
        trigger_turn_index: int,
        compact: bool,
        required_gap: int,
    ) -> None:
        async def _runner() -> None:
            started = perf_counter()
            await self._memory_service.upsert_memory_scope(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id_if_available(),
                compact=compact,
                sync_factual_shadow=False,
            )
            shadow_result = await self._memory_service.sync_factual_shadow_for_session(
                session_id=session_id,
                user_id=user_id,
                entity_id=self._entity_id_if_available(),
                compact=compact,
            )
            elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
            self._checkpoint_turns[session_id] = trigger_turn_index
            self._checkpoint_times[session_id] = perf_counter()
            logger.info(
                "friend_chat_memory_scope_sync_result session_id=%s user_id=%s "
                "trigger_turn_index=%s compact=%s elapsed_ms=%.1f shadow_status=%s "
                "shadow_fact_count=%s shadow_elapsed_ms=%s",
                session_id,
                user_id,
                trigger_turn_index,
                compact,
                elapsed_ms,
                shadow_result.get("status"),
                shadow_result.get("fact_count"),
                shadow_result.get("elapsed_ms"),
            )

        task = asyncio.create_task(_runner())
        self._background_tasks[session_id] = task

        def _cleanup(done_task: asyncio.Task[None]) -> None:
            current = self._background_tasks.get(session_id)
            if current is done_task:
                self._background_tasks.pop(session_id, None)
            try:
                done_task.result()
            except Exception:
                logger.warning(
                    "friend_chat_memory_scope_sync_task_failed session_id=%s user_id=%s",
                    session_id,
                    user_id,
                    exc_info=True,
                )
            pending = self._background_pending.pop(session_id, None)
            if pending is not None:
                pending_turn_index = int(pending.get("turn_index", 0) or 0)
                pending_required_gap = int(
                    pending.get("required_gap", required_gap) or required_gap
                )
                if self.should_checkpoint_pending(
                    session_id=session_id,
                    turn_index=pending_turn_index,
                    required_gap=pending_required_gap,
                ):
                    self.start_background_memory_scope_sync(
                        session_id=session_id,
                        user_id=str(pending.get("user_id") or "") or None,
                        trigger_turn_index=pending_turn_index,
                        compact=bool(pending.get("compact", True)),
                        required_gap=pending_required_gap,
                    )
                else:
                    logger.info(
                        "friend_chat_memory_scope_sync_skipped "
                        "session_id=%s user_id=%s turn_index=%s "
                        "reason=checkpoint_not_due_after_completion",
                        session_id,
                        str(pending.get("user_id") or "") or None,
                        pending_turn_index,
                    )

        task.add_done_callback(_cleanup)

    def _entity_id_if_available(self) -> str | None:
        return self._entity_id if self._entity_service is not None else None

    def _is_edge_profile(self) -> bool:
        return self._runtime_profile in {"edge_desktop_4b", "friend_chat_zh_v1"}

    def _is_friend_chat_profile(self) -> bool:
        return self._runtime_profile == "friend_chat_zh_v1"

