from fastapi import status
from fastapi.responses import JSONResponse

from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
)


def legacy_lifecycle_error_response(
    exc: LegacyLifecycleStreamUnsupportedError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=exc.response_detail(),
    )
