from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from starlette.requests import HTTPConnection

from relationship_os.application.container import RuntimeContainer

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_container(connection: HTTPConnection) -> RuntimeContainer:
    """Extract the runtime container from the application state."""
    return connection.app.state.container


_CONTAINER_DEP = Depends(get_container)


async def verify_api_key(
    api_key: str | None = Security(_API_KEY_HEADER),
    container: RuntimeContainer = _CONTAINER_DEP,
) -> None:
    """Reject the request when an API key is configured but not provided or wrong."""
    configured = container.settings.api_key
    if configured and api_key != configured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


ContainerDep = Annotated[RuntimeContainer, Depends(get_container)]
AuthDep = Annotated[None, Depends(verify_api_key)]
