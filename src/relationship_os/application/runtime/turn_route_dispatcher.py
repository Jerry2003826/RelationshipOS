from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from relationship_os.application.runtime.event_builder import build_lightweight_turn_events
from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.events import NewEvent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TurnRouteDispatchResult:
    analysis: Any | None
    events: list[NewEvent]
    reply_artifacts: Any
    analysis_ms: float
    reply_and_proactive_ms: float


async def dispatch_turn_route(
    runtime: Any,
    *,
    router_decision: Any,
    session_id: str,
    user_message: str,
    generate_reply: bool,
    turn_context: Any,
    turn_input: TurnInput,
    metadata: dict[str, Any] | None,
    readonly_probe_session: bool,
) -> TurnRouteDispatchResult:
    stage_started = perf_counter()
    if router_decision.route_type == "FAST_PONG":
        logger.info("Vanguard router triggered FAST_PONG: %s", router_decision.reason)
        analysis = None
        analysis_ms = 0.0
        reply_artifacts = await runtime._generate_fast_pong_reply(
            user_message=user_message,
            generate_reply=generate_reply,
            turn_context=turn_context,
        )
        events = build_lightweight_turn_events(
            session_id=session_id,
            user_message=user_message,
            metadata_payload=metadata or {},
            turn_context=turn_context,
            turn_input=turn_input,
        )
        events.extend(reply_artifacts.events)
        reply_and_proactive_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        return TurnRouteDispatchResult(
            analysis=analysis,
            events=events,
            reply_artifacts=reply_artifacts,
            analysis_ms=analysis_ms,
            reply_and_proactive_ms=reply_and_proactive_ms,
        )

    if router_decision.route_type == "LIGHT_RECALL":
        logger.info("Vanguard router triggered LIGHT_RECALL: %s", router_decision.reason)
        analysis = None
        analysis_ms = 0.0
        profile_prefix = await runtime._update_user_profile_for_turn(
            user_id=turn_context.user_id,
            user_message=user_message,
            readonly_probe_session=readonly_probe_session,
        )
        reply_artifacts = await runtime._generate_light_recall_reply(
            session_id=session_id,
            user_message=user_message,
            generate_reply=generate_reply,
            turn_context=turn_context,
            turn_input=turn_input,
            profile_prefix=profile_prefix,
        )
        events = build_lightweight_turn_events(
            session_id=session_id,
            user_message=user_message,
            metadata_payload=metadata or {},
            turn_context=turn_context,
            turn_input=turn_input,
        )
        events.extend(reply_artifacts.events)
        reply_and_proactive_ms = round((perf_counter() - stage_started) * 1000.0, 1)
        return TurnRouteDispatchResult(
            analysis=analysis,
            events=events,
            reply_artifacts=reply_artifacts,
            analysis_ms=analysis_ms,
            reply_and_proactive_ms=reply_and_proactive_ms,
        )

    await runtime._update_user_profile_for_turn(
        user_id=turn_context.user_id,
        user_message=user_message,
        readonly_probe_session=readonly_probe_session,
    )
    analysis = await runtime._build_turn_analysis(
        session_id=session_id,
        user_message=user_message,
        turn_context=turn_context,
        turn_input=turn_input,
    )
    analysis_ms = round((perf_counter() - stage_started) * 1000.0, 1)
    stage_started = perf_counter()
    events = runtime._build_turn_events(
        session_id=session_id,
        user_message=user_message,
        metadata=metadata,
        turn_context=turn_context,
        analysis=analysis,
        turn_input=turn_input,
    )
    reply_artifacts = await runtime._generate_turn_reply(
        user_message=user_message,
        generate_reply=generate_reply,
        turn_context=turn_context,
        analysis=analysis,
        turn_input=turn_input,
    )
    events.extend(reply_artifacts.events)
    if not readonly_probe_session:
        proactive_artifacts = await runtime._build_proactive_artifacts(
            turn_context=turn_context,
            analysis=analysis,
            reply_artifacts=reply_artifacts,
        )
        events.extend(runtime._build_proactive_events(proactive_artifacts))
    reply_and_proactive_ms = round((perf_counter() - stage_started) * 1000.0, 1)
    return TurnRouteDispatchResult(
        analysis=analysis,
        events=events,
        reply_artifacts=reply_artifacts,
        analysis_ms=analysis_ms,
        reply_and_proactive_ms=reply_and_proactive_ms,
    )
