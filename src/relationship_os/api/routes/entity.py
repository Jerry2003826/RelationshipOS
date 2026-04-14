"""Entity API — server-wide persona and social-world state."""

from fastapi import APIRouter, HTTPException

from relationship_os.api.dependencies import ContainerDep

router = APIRouter(prefix="/entity", tags=["entity"])


@router.get("")
async def get_entity_overview(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_entity_overview()


@router.get("/persona")
async def get_entity_persona(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_persona_state()


@router.get("/mood")
async def get_entity_mood(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    persona = await container.entity_service.get_persona_state()
    return {
        "entity_id": container.entity_service.entity_id,
        "entity_name": container.entity_service.entity_name,
        "mood": persona.get("mood", {}),
    }


@router.get("/drives")
async def get_entity_drives(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_drive_state()


@router.get("/goals")
async def get_entity_goals(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_goal_state()


@router.get("/narrative")
async def get_entity_narrative(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_narrative()


@router.get("/world-state")
async def get_entity_world_state(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_world_state()


@router.get("/actions")
async def get_entity_actions(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_action_state()


@router.get("/social-graph")
async def get_entity_social_graph(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_social_world()


@router.get("/conscience")
async def get_entity_conscience(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    persona = await container.entity_service.get_persona_state()
    return {
        "entity_id": container.entity_service.entity_id,
        "entity_name": container.entity_service.entity_name,
        "conscience": persona.get("conscience", {}),
    }


@router.get("/policy")
async def get_entity_policy(container: ContainerDep) -> dict[str, object]:
    if container.entity_service is None:
        raise HTTPException(status_code=503, detail="EntityService not available")
    return await container.entity_service.get_policy_snapshot()
