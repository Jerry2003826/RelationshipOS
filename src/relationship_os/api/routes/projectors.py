from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import get_container
from relationship_os.application.container import RuntimeContainer
from relationship_os.domain.projectors import UnknownProjectorError

router = APIRouter(prefix="/projectors", tags=["projectors"])
ContainerDep = Annotated[RuntimeContainer, Depends(get_container)]


class RebuildProjectionRequest(BaseModel):
    version: str = "v1"
    stream_ids: list[str] = Field(default_factory=list)


@router.post("/{projector_name}/rebuild")
async def rebuild_projection(
    projector_name: str,
    payload: RebuildProjectionRequest,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        return await container.stream_service.rebuild_projection(
            projector_name=projector_name,
            projector_version=payload.version,
            stream_ids=payload.stream_ids or None,
        )
    except UnknownProjectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
