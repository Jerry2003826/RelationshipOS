"""HTTP request logging and observability middleware."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing, method, path, and status code."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = uuid.uuid4().hex[:8]
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            structlog.get_logger().exception(
                "http_request_error",
                method=request.method,
                path=str(request.url.path),
            )
            raise
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        structlog.get_logger().info(
            "http_request",
            method=request.method,
            path=str(request.url.path),
            status=response.status_code,
            elapsed_ms=elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.clear_contextvars()
        return response
