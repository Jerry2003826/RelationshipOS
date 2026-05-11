from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from starlette.requests import HTTPConnection

from relationship_os.application.container import RuntimeContainer
from relationship_os.domain.event_types import SESSION_STARTED

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_ADMIN_KEY_HEADER = APIKeyHeader(name="X-Admin-Key", auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthContext:
    api_key: str | None = None
    admin_key: str | None = None
    user_id: str | None = None
    is_admin: bool = False


def get_container(connection: HTTPConnection) -> RuntimeContainer:
    """Extract the runtime container from the application state."""
    return connection.app.state.container


_CONTAINER_DEP = Depends(get_container)


async def verify_api_key(
    api_key: str | None = Security(_API_KEY_HEADER),
    admin_key: str | None = Security(_ADMIN_KEY_HEADER),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
    container: RuntimeContainer = _CONTAINER_DEP,
) -> AuthContext:
    """Reject the request when an API key is configured but not provided or wrong."""
    configured = container.settings.api_key
    if configured and api_key != configured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    user_id = x_user_id.strip() if x_user_id and x_user_id.strip() else None
    configured_admin_key = container.settings.admin_api_key
    if configured_admin_key:
        is_admin = admin_key == configured_admin_key
    else:
        is_admin = user_id is None
    return AuthContext(
        api_key=api_key,
        admin_key=admin_key,
        user_id=user_id,
        is_admin=is_admin,
    )


def require_admin(auth: AuthContext) -> None:
    if not auth.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API key required",
        )


async def get_stream_owner(
    *,
    container: RuntimeContainer,
    stream_id: str,
) -> str | None:
    if stream_id.startswith("user:"):
        owner = stream_id.split(":", 1)[1].strip()
        return owner or None

    events = await container.stream_service.read_stream(stream_id=stream_id, limit=50)
    for event in events:
        if event.event_type != SESSION_STARTED:
            continue
        owner = event.payload.get("user_id")
        if isinstance(owner, str) and owner.strip():
            return owner.strip()
    return None


async def assert_stream_access(
    *,
    container: RuntimeContainer,
    stream_id: str,
    auth: AuthContext,
) -> None:
    if auth.is_admin or auth.user_id is None:
        return
    owner = await get_stream_owner(container=container, stream_id=stream_id)
    if owner is not None and owner != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden stream",
        )


async def assert_session_access(
    *,
    container: RuntimeContainer,
    session_id: str,
    auth: AuthContext,
) -> None:
    await assert_stream_access(container=container, stream_id=session_id, auth=auth)


def assert_user_access(*, user_id: str, auth: AuthContext) -> None:
    if auth.is_admin or auth.user_id is None or auth.user_id == user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden user",
    )


ContainerDep = Annotated[RuntimeContainer, Depends(get_container)]
AuthDep = Annotated[AuthContext, Depends(verify_api_key)]
