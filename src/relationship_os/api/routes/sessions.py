from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import AuthDep, ContainerDep
from relationship_os.api.errors import legacy_lifecycle_error_response
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
)
from relationship_os.application.runtime_service import SessionAlreadyExistsError
from relationship_os.domain.contracts.turn_input import Attachment, TurnInput

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    session_id: str | None = Field(
        default=None,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    user_id: str | None = Field(
        default=None,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Optional user identity. Links this session to a person-level profile.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttachmentPayload(BaseModel):
    type: str = Field(description="image | audio | file")
    url: str = ""
    mime_type: str = ""
    filename: str = ""


class TurnRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)
    attachments: list[AttachmentPayload] = Field(default_factory=list)
    generate_reply: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def list_sessions(container: ContainerDep) -> dict[str, object]:
    sessions = await container.runtime_service.list_sessions()
    return {"sessions": sessions}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: CreateSessionRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    try:
        return await container.runtime_service.create_session(
            session_id=payload.session_id,
            user_id=payload.user_id,
            metadata=payload.metadata,
        )
    except SessionAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        return await container.stream_service.project_stream(
            stream_id=session_id,
            projector_name="session-runtime",
            projector_version=container.settings.default_projector_version,
        )
    except LegacyLifecycleStreamUnsupportedError as exc:
        return legacy_lifecycle_error_response(exc)


@router.get("/{session_id}/inner-monologue")
async def get_inner_monologue_buffer(
    session_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    return await container.stream_service.project_stream(
        stream_id=session_id,
        projector_name="inner-monologue-buffer",
        projector_version="v1",
    )


@router.get("/{session_id}/snapshots")
async def get_session_snapshots(
    session_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    return await container.stream_service.project_stream(
        stream_id=session_id,
        projector_name="session-snapshots",
        projector_version="v1",
    )


@router.get("/{session_id}/memory")
async def get_session_memory(
    session_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    return await container.memory_service.get_session_memory(session_id=session_id)


@router.get("/{session_id}/memory/graph")
async def get_session_memory_graph(
    session_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    return await container.memory_service.get_session_temporal_kg(session_id=session_id)


@router.get("/{session_id}/memory/recall")
async def recall_session_memory(
    session_id: str,
    container: ContainerDep,
    query: str | None = None,
    limit: int = Query(default=5, ge=1, le=20),
    topic: str | None = None,
    appraisal: str | None = None,
    dialogue_act: str | None = None,
    include_filtered: bool = False,
) -> dict[str, object]:
    context_filters = {
        key: value
        for key, value in {
            "topic": topic,
            "appraisal": appraisal,
            "dialogue_act": dialogue_act,
        }.items()
        if value
    }
    return await container.memory_service.recall_session_memory(
        session_id=session_id,
        query=query,
        limit=limit,
        context_filters=context_filters,
        include_filtered=include_filtered,
    )


@router.post("/{session_id}/turns", status_code=status.HTTP_201_CREATED)
async def process_turn(
    session_id: str,
    payload: TurnRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    turn_input = TurnInput(
        text=payload.content,
        attachments=[
            Attachment(
                type=a.type,
                url=a.url,
                mime_type=a.mime_type,
                filename=a.filename,
            )
            for a in payload.attachments
        ],
    )
    try:
        result = await container.runtime_service.process_turn(
            session_id=session_id,
            turn_input=turn_input,
            generate_reply=payload.generate_reply,
            metadata=payload.metadata,
        )
    except LegacyLifecycleStreamUnsupportedError as exc:
        return legacy_lifecycle_error_response(exc)
    return {
        "session_id": result.session_id,
        "assistant_response": result.assistant_response,
        "assistant_responses": result.assistant_responses,
        "response_diagnostics": dict(result.response_diagnostics or {}),
        "assistant_response_mode": (
            (
                (result.runtime_projection.get("state", {}) or {}).get("response_sequence_plan")
                or {}
            ).get("mode")
        ),
        "events": [
            container.stream_service.serialize_event(event) for event in result.stored_events
        ],
        "projection": result.runtime_projection,
        "turn_stage_timing": dict(result.turn_stage_timing or {}),
    }
