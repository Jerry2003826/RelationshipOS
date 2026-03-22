import asyncio
from dataclasses import dataclass, field
from typing import Literal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from relationship_os.api.routes.runtime import build_runtime_overview_payload
from relationship_os.application.container import RuntimeContainer
from relationship_os.application.job_service import JobNotFoundError
from relationship_os.domain.event_types import (
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_STARTED,
    SESSION_ARCHIVED,
    TRACE_EVENT_TYPES,
)
from relationship_os.domain.events import StoredEvent

router = APIRouter(prefix="/ws", tags=["ws"])

JOB_EVENT_TYPES = {
    BACKGROUND_JOB_SCHEDULED,
    BACKGROUND_JOB_REQUEUED,
    BACKGROUND_JOB_CLAIMED,
    BACKGROUND_JOB_HEARTBEAT,
    BACKGROUND_JOB_LEASE_EXPIRED,
    BACKGROUND_JOB_STARTED,
    BACKGROUND_JOB_COMPLETED,
    BACKGROUND_JOB_FAILED,
}


class RuntimeSubscribeRequest(BaseModel):
    type: Literal["subscribe"] = "subscribe"
    stream_id: str | None = None
    job_id: str | None = None
    event_types: list[str] = Field(default_factory=list)
    include_backlog: bool = False


@dataclass(slots=True)
class RuntimeSubscriptionState:
    active: bool = False
    stream_id: str | None = None
    job_id: str | None = None
    event_types: set[str] = field(default_factory=set)

    def apply(self, request: RuntimeSubscribeRequest) -> None:
        self.active = True
        self.stream_id = request.stream_id
        self.job_id = request.job_id
        self.event_types = {event_type for event_type in request.event_types if event_type}

    def to_dict(self) -> dict[str, object]:
        return {
            "stream_id": self.stream_id,
            "job_id": self.job_id,
            "event_types": sorted(self.event_types),
        }

    def matches_trace_event(self, event: StoredEvent) -> bool:
        if not self.active or event.event_type not in TRACE_EVENT_TYPES:
            return False
        if self.stream_id is not None and event.stream_id != self.stream_id:
            return False
        if self.job_id is not None and event.payload.get("job_id") != self.job_id:
            return False
        if self.event_types and event.event_type not in self.event_types:
            return False
        return True

    def matching_job_ids(self, events: list[StoredEvent]) -> list[str]:
        job_ids: set[str] = set()
        for event in events:
            job_id = event.payload.get("job_id")
            if not isinstance(job_id, str):
                continue
            if self.job_id is not None and job_id != self.job_id:
                continue
            if self.stream_id is not None and event.stream_id != self.stream_id:
                continue
            job_ids.add(job_id)
        return sorted(job_ids)


@router.websocket("/runtime")
async def runtime_websocket(websocket: WebSocket) -> None:
    container: RuntimeContainer = websocket.app.state.container
    broker_subscription = await container.stream_service.subscribe_runtime_events()
    if broker_subscription is None:
        await websocket.close(code=1011)
        return

    subscription_state = RuntimeSubscriptionState()
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "hello",
            "runtime": await build_runtime_overview_payload(container),
        }
    )

    sender_task = asyncio.create_task(
        _forward_runtime_updates(
            websocket=websocket,
            container=container,
            subscription=subscription_state,
            broker_subscription=broker_subscription,
        ),
        name="runtime-websocket-sender",
    )
    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            try:
                request = RuntimeSubscribeRequest.model_validate(message)
            except ValidationError as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "invalid runtime subscription message",
                        "errors": exc.errors(),
                    }
                )
                continue

            subscription_state.apply(request)
            await websocket.send_json(
                {
                    "type": "subscribed",
                    "subscription": subscription_state.to_dict(),
                }
            )
            if request.include_backlog:
                await _send_backlog_snapshot(
                    websocket=websocket,
                    container=container,
                    subscription=subscription_state,
                )
    except WebSocketDisconnect:
        return
    finally:
        sender_task.cancel()
        await asyncio.gather(sender_task, return_exceptions=True)
        await broker_subscription.close()


async def _forward_runtime_updates(
    *,
    websocket: WebSocket,
    container: RuntimeContainer,
    subscription: RuntimeSubscriptionState,
    broker_subscription,
) -> None:
    try:
        while True:
            batch = await broker_subscription.get()
            events = list(batch.events)
            if not subscription.active:
                continue

            trace_events = [
                container.stream_service.serialize_event(event)
                for event in events
                if subscription.matches_trace_event(event)
            ]
            if trace_events:
                await websocket.send_json(
                    {
                        "type": "trace_batch",
                        "stream_id": batch.stream_id,
                        "events": trace_events,
                    }
                )

            if subscription.stream_id == batch.stream_id:
                session_events = [
                    event
                    for event in events
                    if not subscription.event_types
                    or event.event_type in subscription.event_types
                    or event.event_type in TRACE_EVENT_TYPES
                ]
                if session_events:
                    projection = await container.stream_service.project_stream(
                        stream_id=batch.stream_id,
                        projector_name="session-runtime",
                        projector_version="v1",
                    )
                    await websocket.send_json(
                        {
                            "type": "session_projection",
                            "stream_id": batch.stream_id,
                            "projection": projection,
                        }
                    )

            for job_id in subscription.matching_job_ids(events):
                try:
                    job = await container.job_service.get_job(job_id=job_id)
                except JobNotFoundError:
                    continue
                await websocket.send_json({"type": "job_update", "job": job})

            archive_events = [
                container.stream_service.serialize_event(event)
                for event in events
                if event.event_type == SESSION_ARCHIVED
                and (
                    subscription.stream_id is None or event.stream_id == subscription.stream_id
                )
            ]
            for archive_event in archive_events:
                await websocket.send_json(
                    {
                        "type": "archive_update",
                        "stream_id": batch.stream_id,
                        "event": archive_event,
                    }
                )

            if any(event.event_type in JOB_EVENT_TYPES for event in events):
                await websocket.send_json(
                    {
                        "type": "runtime_overview",
                        "runtime": await build_runtime_overview_payload(container),
                    }
                )
    except WebSocketDisconnect:
        return
    except asyncio.CancelledError:
        return


async def _send_backlog_snapshot(
    *,
    websocket: WebSocket,
    container: RuntimeContainer,
    subscription: RuntimeSubscriptionState,
) -> None:
    stream_id = subscription.stream_id
    if stream_id is None and subscription.job_id is not None:
        try:
            job = await container.job_service.get_job(job_id=subscription.job_id)
        except JobNotFoundError:
            job = None
        else:
            stream_id = str(job["session_id"])
            await websocket.send_json({"type": "job_snapshot", "job": job})
    elif subscription.job_id is not None:
        try:
            job = await container.job_service.get_job(job_id=subscription.job_id)
        except JobNotFoundError:
            pass
        else:
            await websocket.send_json({"type": "job_snapshot", "job": job})

    if stream_id is None:
        return

    events = await container.stream_service.read_stream(stream_id=stream_id)
    trace = [
        container.stream_service.serialize_event(event)
        for event in events
        if subscription.matches_trace_event(event)
    ]
    await websocket.send_json(
        {
            "type": "trace_snapshot",
            "stream_id": stream_id,
            "trace": trace,
        }
    )
    projection = await container.stream_service.project_stream(
        stream_id=stream_id,
        projector_name="session-runtime",
        projector_version="v1",
    )
    await websocket.send_json(
        {
            "type": "session_projection",
            "stream_id": stream_id,
            "projection": projection,
        }
    )
