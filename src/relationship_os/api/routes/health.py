from fastapi import APIRouter
from sqlalchemy import text

from relationship_os.api.dependencies import ContainerDep

router = APIRouter(tags=["health"])


@router.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/healthz/ready")
async def readiness(container: ContainerDep) -> dict[str, object]:
    checks: dict[str, str] = {}
    if container.database_engine is not None:
        try:
            async with container.database_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {type(exc).__name__}"
    else:
        checks["database"] = "not_configured"

    checks["job_executor"] = "running" if container.job_executor.is_running else "stopped"
    checks["dispatcher"] = (
        "running" if container.proactive_followup_dispatcher.is_running else "stopped"
    )
    all_ok = all(v in ("ok", "running", "not_configured") for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
