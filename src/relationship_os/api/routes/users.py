"""Users API — person-centric identity and cross-session memory."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import AuthDep, ContainerDep
from relationship_os.application.user_service import UserAlreadyExistsError

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique identifier for the user.",
    )
    display_name: str | None = Field(default=None, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateUserRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=256)
    metadata: dict[str, Any] | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    """Create a new user identity stream."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    try:
        return await container.user_service.create_user(
            user_id=payload.user_id,
            display_name=payload.display_name,
            metadata=payload.metadata,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    """Return the user-index projection (id, display_name, linked sessions)."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    index = await container.user_service.get_user_index(user_id=user_id)
    if index.get("user_id") is None:
        raise HTTPException(status_code=404, detail=f"User {user_id!r} not found")
    return index


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    """Update user display_name or metadata."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    exists = await container.user_service.user_exists(user_id=user_id)
    if not exists:
        raise HTTPException(status_code=404, detail=f"User {user_id!r} not found")
    await container.user_service.update_profile(
        user_id=user_id,
        display_name=payload.display_name,
        metadata=payload.metadata,
    )
    return {"user_id": user_id, "updated": True}


@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    """Return all sessions linked to this user."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    session_ids = await container.user_service.get_user_sessions(user_id=user_id)
    return {"user_id": user_id, "session_ids": session_ids, "count": len(session_ids)}


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    """Return cross-session aggregated user profile (identity facts, preferences, history)."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    return await container.user_service.get_user_profile(user_id=user_id)


@router.get("/{user_id}/self-state")
async def get_self_state(
    user_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    """Return the AI's relationship self-state with this user (open threads, tone, last chat)."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    return await container.user_service.get_self_state(user_id=user_id)


@router.get("/{user_id}/relationship-state")
async def get_relationship_state(
    user_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    """Return the server-entity relationship drift for this user."""
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_relationship_state(user_id=user_id)


@router.get("/{user_id}/memory")
async def get_user_memory(
    user_id: str,
    container: ContainerDep,
    query: str = "",
    limit: int = 10,
) -> dict[str, object]:
    """Recall cross-session memory for this user."""
    if container.user_service is None:
        raise HTTPException(status_code=503, detail="UserService not available")
    results = await container.memory_service.recall_user_memory(
        user_id=user_id,
        query=query or None,
        limit=limit,
    )
    return results
