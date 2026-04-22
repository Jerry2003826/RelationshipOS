from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import AuthDep, ContainerDep
from relationship_os.api.errors import legacy_lifecycle_error_response
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
)
from relationship_os.domain.event_store import OptimisticConcurrencyError
from relationship_os.domain.events import NewEvent, StoredEvent
from relationship_os.domain.projectors import UnknownProjectorError

router = APIRouter(prefix="/streams", tags=["streams"])


class AppendEventItem(BaseModel):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AppendEventsRequest(BaseModel):
    expected_version: int | None = None
    events: list[AppendEventItem] = Field(max_length=50)


class StoredEventResponse(BaseModel):
    event_id: str
    stream_id: str
    version: int
    event_type: str
    payload: dict[str, Any]
    metadata: dict[str, Any]
    occurred_at: datetime

    @classmethod
    def from_event(cls, event: StoredEvent) -> "StoredEventResponse":
        return cls(
            event_id=str(event.event_id),
            stream_id=event.stream_id,
            version=event.version,
            event_type=event.event_type,
            payload=event.payload,
            metadata=event.metadata,
            occurred_at=event.occurred_at,
        )


class ReplayStreamResponse(BaseModel):
    stream_id: str
    projector: dict[str, str]
    event_count: int
    events: list[dict[str, Any]]
    projection: dict[str, Any]
    fingerprint: str
    consistent: bool


@router.post("/{stream_id}/events", status_code=status.HTTP_201_CREATED)
async def append_events(
    stream_id: str,
    payload: AppendEventsRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, list[StoredEventResponse]]:
    try:
        stored_events = await container.stream_service.append_events(
            stream_id=stream_id,
            expected_version=payload.expected_version,
            events=[
                NewEvent(
                    event_type=item.event_type,
                    payload=item.payload,
                    metadata=item.metadata,
                )
                for item in payload.events
            ],
        )
    except OptimisticConcurrencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return {"events": [StoredEventResponse.from_event(event) for event in stored_events]}


@router.get("/{stream_id}/events")
async def read_stream(
    stream_id: str,
    container: ContainerDep,
) -> dict[str, list[StoredEventResponse]]:
    events = await container.stream_service.read_stream(stream_id=stream_id)
    return {"events": [StoredEventResponse.from_event(event) for event in events]}


@router.get("/{stream_id}/replay")
async def replay_stream(
    stream_id: str,
    container: ContainerDep,
    projector_name: str = "session-transcript",
    version: str = "v1",
) -> ReplayStreamResponse:
    try:
        replay = await container.stream_service.replay_stream(
            stream_id=stream_id,
            projector_name=projector_name,
            projector_version=version,
        )
        return ReplayStreamResponse(**replay)
    except UnknownProjectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LegacyLifecycleStreamUnsupportedError as exc:
        return legacy_lifecycle_error_response(exc)


@router.get("/{stream_id}/projection/{projector_name}")
async def project_stream(
    stream_id: str,
    projector_name: str,
    container: ContainerDep,
    version: str = "v1",
) -> dict[str, object]:
    try:
        return await container.stream_service.project_stream(
            stream_id=stream_id,
            projector_name=projector_name,
            projector_version=version,
        )
    except UnknownProjectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except LegacyLifecycleStreamUnsupportedError as exc:
        return legacy_lifecycle_error_response(exc)
