"""API routes for longitudinal simulation."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import ContainerDep
from relationship_os.application.scenario_evaluation_service.simulation import (
    LONGITUDINAL_SIMULATION_PRESETS,
    LongitudinalSimulationConfig,
    SimulationDayConfig,
    SimulationWeekConfig,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


class RunSimulationRequest(BaseModel):
    """Request body for running a simulation."""

    preset_id: str | None = Field(
        default=None,
        description="ID of a predefined preset to run (e.g. 'longitudinal_4week_normal')",
    )
    simulation_id: str | None = Field(
        default=None,
        description="Custom simulation ID (only needed when not using a preset)",
    )
    label: str | None = None
    description: str | None = None
    week_count: int | None = Field(default=None, ge=1, le=12)
    turns_per_day: int | None = Field(default=None, ge=1, le=10)
    run_in_background: bool = Field(
        default=True,
        description="When True, simulation runs asynchronously and result is fetched later",
    )


@router.get("/presets")
async def list_simulation_presets(
    container: ContainerDep,
) -> dict[str, Any]:
    """List all available longitudinal simulation presets."""
    return {
        "presets": container.longitudinal_simulation_service.get_available_presets(),
        "preset_count": len(LONGITUDINAL_SIMULATION_PRESETS),
    }


@router.get("/presets/{preset_id}")
async def get_simulation_preset(
    preset_id: str,
    container: ContainerDep,
) -> dict[str, Any]:
    """Get details for a specific simulation preset."""
    cfg = container.longitudinal_simulation_service.get_preset_config(preset_id)
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_id}' not found",
        )
    return {
        "simulation_id": cfg.simulation_id,
        "label": cfg.label,
        "description": cfg.description,
        "week_count": len(cfg.weeks),
        "proactive_dispatch_enabled": cfg.proactive_dispatch_enabled,
        "weeks": [
            {
                "week_index": w.week_index,
                "label": w.label,
                "day_count": len(w.daily_sessions),
                "governance_overrides": w.governance_overrides,
            }
            for w in cfg.weeks
        ],
    }


@router.post("/run")
async def run_simulation(
    request: RunSimulationRequest,
    container: ContainerDep,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Run a longitudinal simulation.

    When ``run_in_background=True`` (default), the simulation is queued
    as a background task and this endpoint returns immediately.  Poll
    ``GET /simulations/{simulation_id}`` for the result.

    When ``run_in_background=False``, the simulation runs synchronously.
    Only use this for short simulations or testing.
    """
    if request.preset_id:
        cfg = container.longitudinal_simulation_service.get_preset_config(request.preset_id)
        if cfg is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{request.preset_id}' not found",
            )
    else:
        sim_id = request.simulation_id or f"custom_{id(request)}"
        turns = request.turns_per_day or 3
        week_count = request.week_count or 2
        cfg = LongitudinalSimulationConfig(
            simulation_id=sim_id,
            label=request.label or sim_id,
            description=request.description or "",
            weeks=[
                SimulationWeekConfig(
                    week_index=i,
                    label=f"week_{i + 1}",
                    daily_sessions=[
                        SimulationDayConfig(
                            session_count=1,
                            turn_count_per_session=turns,
                            user_mood="neutral",
                        )
                        for _ in range(5)
                    ],
                )
                for i in range(week_count)
            ],
        )

    if request.run_in_background:
        background_tasks.add_task(
            container.longitudinal_simulation_service.run_simulation,
            cfg,
        )
        return {
            "simulation_id": cfg.simulation_id,
            "status": "queued",
            "label": cfg.label,
            "week_count": len(cfg.weeks),
            "message": (
                f"Simulation '{cfg.simulation_id}' queued. "
                f"Poll GET /simulations/{cfg.simulation_id} for result."
            ),
        }

    result = await container.longitudinal_simulation_service.run_simulation(cfg)
    report = container.longitudinal_simulation_service.build_simulation_report(
        result.simulation_id
    )
    return {
        "simulation_id": result.simulation_id,
        "status": "completed",
        "report": report,
    }


@router.get("/{simulation_id}")
async def get_simulation_result(
    simulation_id: str,
    container: ContainerDep,
) -> dict[str, Any]:
    """Get the result/report for a completed simulation."""
    report = container.longitudinal_simulation_service.build_simulation_report(simulation_id)
    if report is None:
        result = container.longitudinal_simulation_service.get_simulation_result(simulation_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation '{simulation_id}' not found",
            )
        return {"simulation_id": simulation_id, "status": result.final_status}
    return {"simulation_id": simulation_id, "status": report["final_status"], "report": report}


@router.get("/{simulation_id}/drift")
async def get_simulation_drift_report(
    simulation_id: str,
    container: ContainerDep,
) -> dict[str, Any]:
    """Get a drift analysis report for a completed simulation.

    Analyzes r_vector drift, strategy diversity trends, governance escalation
    frequency, and proactive response rate trends across simulation weeks.
    """
    report = container.longitudinal_simulation_service.build_simulation_report(simulation_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found or not completed",
        )
    drift_report = container.scenario_evaluation_service.build_simulation_drift_report(report)
    return drift_report
