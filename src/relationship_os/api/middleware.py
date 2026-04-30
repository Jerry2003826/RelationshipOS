"""HTTP request logging and observability middleware."""

import json
import time
import uuid
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RequestGuardMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies and deeply nested JSON payloads."""

    def __init__(
        self,
        app,
        *,
        max_request_bytes: int = 1_000_000,
        max_json_depth: int = 32,
    ) -> None:
        super().__init__(app)
        self._max_request_bytes = max(0, max_request_bytes)
        self._max_json_depth = max(0, max_json_depth)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method.upper() not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if (
            self._max_request_bytes > 0
            and content_length is not None
            and content_length.isdigit()
            and int(content_length) > self._max_request_bytes
        ):
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return await call_next(request)

        body = await request.body()
        if self._max_request_bytes > 0 and len(body) > self._max_request_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )

        if body and self._max_json_depth > 0:
            try:
                value = json.loads(body)
            except json.JSONDecodeError:
                return await call_next(request)
            if _json_depth(value) > self._max_json_depth:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request JSON too deeply nested"},
                )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply a simple in-process fixed-window rate limit for write requests."""

    def __init__(
        self,
        app,
        *,
        max_requests: int = 0,
        window_seconds: float = 60.0,
    ) -> None:
        super().__init__(app)
        self._max_requests = max(0, max_requests)
        self._window_seconds = max(1.0, window_seconds)
        self._buckets: dict[str, tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if (
            self._max_requests <= 0
            or request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}
            or request.url.path.endswith("/healthz")
        ):
            return await call_next(request)

        key = self._rate_limit_key(request)
        now = time.monotonic()
        window_start, count = self._buckets.get(key, (now, 0))
        if now - window_start >= self._window_seconds:
            window_start = now
            count = 0
        if count >= self._max_requests:
            retry_after = max(1, int(self._window_seconds - (now - window_start)))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        self._buckets[key] = (window_start, count + 1)
        return await call_next(request)

    def _rate_limit_key(self, request: Request) -> str:
        identity = (
            request.headers.get("x-user-id")
            or request.headers.get("x-api-key")
            or (request.client.host if request.client else "")
            or "anonymous"
        )
        return f"{identity}:{_extract_session_scope(request.url.path)}"


def _extract_session_scope(path: str) -> str:
    marker = "/sessions/"
    if marker not in path:
        return "*"
    tail = path.split(marker, 1)[1]
    session_id = tail.split("/", 1)[0].strip()
    return session_id or "*"


def _json_depth(value: Any) -> int:
    if isinstance(value, dict):
        if not value:
            return 1
        return 1 + max(_json_depth(item) for item in value.values())
    if isinstance(value, list):
        if not value:
            return 1
        return 1 + max(_json_depth(item) for item in value)
    return 0


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing, method, path, and status code."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
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
