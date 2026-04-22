from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from relationship_os.api.router import api_router
from relationship_os.application.container import RuntimeContainer, build_container
from relationship_os.core.config import Settings, get_settings
from relationship_os.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger("relationship_os.lifecycle")
    container: RuntimeContainer = app.state.container
    recovery_report = await container.job_executor.recover_jobs(
        source="startup",
        include_failed_retries=True,
    )
    await container.job_executor.start()
    proactive_report = await container.proactive_followup_dispatcher.dispatch_due_followups(
        source="startup",
    )
    await container.proactive_followup_dispatcher.start()
    logger.info(
        "runtime_started",
        app=container.settings.app_name,
        env=container.settings.env,
        event_store_backend=container.settings.event_store_backend,
        job_recovery=recovery_report,
        proactive_followups=proactive_report,
    )
    yield
    await container.shutdown()
    logger.info("runtime_stopped", app=container.settings.app_name)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security response headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    container = build_container(resolved_settings)

    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.container = container

    origins = [o.strip() for o in resolved_settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(SecurityHeadersMiddleware)

    from relationship_os.api.middleware import RequestLoggingMiddleware

    app.add_middleware(RequestLoggingMiddleware)

    if resolved_settings.env == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],
        )

    @app.get("/healthz", include_in_schema=False)
    async def root_healthz() -> dict[str, str]:
        return {"status": "ok"}

    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(api_router, prefix=resolved_settings.api_prefix)
    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "relationship_os.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
