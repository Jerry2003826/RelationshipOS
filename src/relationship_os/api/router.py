from fastapi import APIRouter

from relationship_os.api.routes import (
    console,
    evaluations,
    health,
    jobs,
    projectors,
    runtime,
    sessions,
    streams,
    ws,
)

api_router = APIRouter()
api_router.include_router(console.router)
api_router.include_router(evaluations.router)
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(projectors.router)
api_router.include_router(runtime.router)
api_router.include_router(sessions.router)
api_router.include_router(streams.router)
api_router.include_router(ws.router)
