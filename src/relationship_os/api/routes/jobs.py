from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import AuthDep, ContainerDep
from relationship_os.application.job_service import (
    JobNotFoundError,
    JobRetryNotAllowedError,
    SessionNotFoundError,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CreateOfflineConsolidationJobRequest(BaseModel):
    session_id: str = Field(max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    metadata: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int | None = Field(default=None, ge=1, le=10)


@router.get("")
async def list_jobs(
    container: ContainerDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    session_id: str | None = None,
) -> dict[str, object]:
    return await container.job_service.list_jobs(
        status=status_filter,
        session_id=session_id,
    )


@router.post("/offline-consolidation", status_code=status.HTTP_202_ACCEPTED)
async def create_offline_consolidation_job(
    payload: CreateOfflineConsolidationJobRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    try:
        job = await container.job_service.create_offline_consolidation_job(
            session_id=payload.session_id,
            metadata=payload.metadata,
            max_attempts=payload.max_attempts,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    await container.job_executor.schedule_job(job_id=str(job["job_id"]))
    return {"job": job}


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        job = await container.job_service.get_job(job_id=job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return {"job": job}


@router.post("/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_job(
    job_id: str,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    try:
        job = await container.job_service.retry_job(job_id=job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except JobRetryNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    await container.job_executor.schedule_job(job_id=job_id)
    return {"job": job}
