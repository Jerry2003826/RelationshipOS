import asyncio
from datetime import datetime

from fastapi import APIRouter, Query

from relationship_os.api.dependencies import AuthDep, ContainerDep
from relationship_os.application.container import RuntimeContainer
from relationship_os.domain.event_types import is_trace_event_type

router = APIRouter(prefix="/runtime", tags=["runtime"])


def _public_projectors(container: RuntimeContainer) -> list[dict[str, str]]:
    preferred_by_name: dict[str, dict[str, str]] = {}
    for projector in container.projector_registry.list_projectors():
        name = str(projector.get("name") or "")
        version = str(projector.get("version") or "")
        current = preferred_by_name.get(name)
        if current is None or (current.get("version") != "v1" and version == "v1"):
            preferred_by_name[name] = {
                "name": name,
                "version": version,
            }
    return [preferred_by_name[name] for name in sorted(preferred_by_name)]


async def build_runtime_overview_payload(
    container: RuntimeContainer,
) -> dict[str, object]:
    job_runtime, proactive_followups, proactive_dispatcher = await asyncio.gather(
        container.job_executor.get_runtime_state(),
        container.proactive_followup_service.list_followups(limit=4),
        container.proactive_followup_dispatcher.get_runtime_state(),
    )
    return {
        "app": container.settings.app_name,
        "env": container.settings.env,
        "event_store_backend": container.settings.event_store_backend,
        "llm_backend": container.settings.llm_backend,
        "llm_model": container.settings.llm_model,
        "projectors": _public_projectors(container),
        "job_runtime": job_runtime,
        "proactive_followups": proactive_followups,
        "proactive_dispatcher": proactive_dispatcher,
    }


@router.get("")
async def get_runtime_overview(
    container: ContainerDep,
) -> dict[str, object]:
    return await build_runtime_overview_payload(container)


@router.get("/trace/{stream_id}")
async def get_runtime_trace(
    stream_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    events = await container.stream_service.read_stream(stream_id=stream_id)
    trace = [
        container.stream_service.serialize_event(event)
        for event in events
        if is_trace_event_type(event.event_type)
    ]
    return {
        "stream_id": stream_id,
        "trace": trace,
    }


@router.get("/audit/{stream_id}")
async def get_runtime_audit(
    stream_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    return await container.audit_service.get_session_audit(session_id=stream_id)


@router.get("/archives")
async def list_archived_sessions(
    container: ContainerDep,
) -> dict[str, object]:
    return await container.audit_service.list_archived_sessions()


@router.get("/proactive-followups")
async def list_proactive_followups(
    container: ContainerDep,
    as_of: datetime | None = None,
    include_hold: bool = True,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    return await container.proactive_followup_service.list_followups(
        as_of=as_of,
        include_hold=include_hold,
        limit=limit,
    )


@router.post("/proactive-followups/dispatch")
async def dispatch_due_proactive_followups(
    container: ContainerDep,
    _auth: AuthDep,
    as_of: datetime | None = None,
    limit: int | None = None,
) -> dict[str, object]:
    return await container.proactive_followup_dispatcher.dispatch_due_followups(
        source="manual",
        as_of=as_of,
        limit=limit,
    )
