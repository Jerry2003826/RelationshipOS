from __future__ import annotations

from typing import Any

from relationship_os.domain.event_types import (
    PROACTIVE_DISPATCH_OUTCOME_RECORDED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    USER_MESSAGE_RECEIVED,
)


class DispatchOutcomeRecorder:
    def __init__(self, *, proactive_dispatch_handler: Any) -> None:
        self._proactive_dispatch_handler = proactive_dispatch_handler

    async def maybe_record(
        self,
        *,
        session_id: str,
        prior_events: list[Any],
    ) -> None:
        """Auto-record 'responded' outcome when user replies after a proactive dispatch."""
        if not prior_events:
            return
        last_dispatch = next(
            (e for e in reversed(prior_events) if e.event_type == PROACTIVE_FOLLOWUP_DISPATCHED),
            None,
        )
        if last_dispatch is None:
            return
        already_recorded = any(
            e.event_type == PROACTIVE_DISPATCH_OUTCOME_RECORDED
            and e.occurred_at > last_dispatch.occurred_at
            for e in prior_events
        )
        if already_recorded:
            return
        user_reply_after_dispatch = next(
            (
                e
                for e in prior_events
                if e.event_type == USER_MESSAGE_RECEIVED
                and e.occurred_at > last_dispatch.occurred_at
            ),
            None,
        )
        if user_reply_after_dispatch is None:
            return
        response_latency = max(
            0.0,
            (user_reply_after_dispatch.occurred_at - last_dispatch.occurred_at).total_seconds(),
        )
        await self._proactive_dispatch_handler.record_dispatch_outcome(
            session_id=session_id,
            outcome_type="responded",
            response_latency_seconds=response_latency,
        )
