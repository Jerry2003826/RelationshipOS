from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from relationship_os.api.dependencies import AuthDep, ContainerDep
from relationship_os.api.errors import legacy_lifecycle_error_response
from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
)
from relationship_os.application.scenario_evaluation_service import (
    ScenarioBaselineNotFoundError,
    ScenarioNotFoundError,
    ScenarioRunNotFoundError,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


class RunScenariosRequest(BaseModel):
    scenario_ids: list[str] = Field(default_factory=list)


class SetScenarioBaselineRequest(BaseModel):
    run_id: str
    note: str | None = None


@router.get("/sessions")
async def list_session_evaluations(
    container: ContainerDep,
) -> dict[str, object]:
    return await container.evaluation_service.list_session_evaluations()


@router.get("/sessions/{session_id}")
async def evaluate_session(
    session_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        return await container.evaluation_service.evaluate_session(session_id=session_id)
    except LegacyLifecycleStreamUnsupportedError as exc:
        return legacy_lifecycle_error_response(exc)


@router.get("/strategy-preferences")
async def get_strategy_preferences(
    container: ContainerDep,
) -> dict[str, object]:
    return await container.evaluation_service.build_strategy_preference_report()


@router.get("/scenarios")
async def list_scenarios(
    container: ContainerDep,
) -> dict[str, object]:
    return await container.scenario_evaluation_service.list_scenarios()


@router.post("/scenarios/run", status_code=status.HTTP_201_CREATED)
async def run_scenarios(
    payload: RunScenariosRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.run_scenarios(
            scenario_ids=payload.scenario_ids or None
        )
    except ScenarioNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/scenarios/runs")
async def list_scenario_runs(
    container: ContainerDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.list_runs(limit=limit)


@router.get("/scenarios/baselines")
async def list_scenario_baselines(
    container: ContainerDep,
) -> dict[str, object]:
    return await container.scenario_evaluation_service.list_baselines()


@router.put("/scenarios/baselines/{label}")
async def set_scenario_baseline(
    label: str,
    payload: SetScenarioBaselineRequest,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.set_baseline(
            label=label,
            run_id=payload.run_id,
            note=payload.note,
        )
    except ScenarioRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/scenarios/baselines/{label}")
async def clear_scenario_baseline(
    label: str,
    container: ContainerDep,
    _auth: AuthDep,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.clear_baseline(label=label)
    except ScenarioBaselineNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/scenarios/baselines/{label}/compare")
async def compare_with_scenario_baseline(
    label: str,
    container: ContainerDep,
    candidate_run_id: str | None = None,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.compare_with_baseline(
            label=label,
            candidate_run_id=candidate_run_id,
        )
    except (ScenarioBaselineNotFoundError, ScenarioRunNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/scenarios/trends")
async def list_scenario_trends(
    container: ContainerDep,
    limit_per_scenario: int = Query(default=5, ge=1, le=20),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.list_trends(
        limit_per_scenario=limit_per_scenario
    )


@router.get("/scenarios/report")
async def get_scenario_report(
    container: ContainerDep,
    window: int = Query(default=6, ge=2, le=20),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_report(window=window)


@router.get("/scenarios/longitudinal-report")
async def get_scenario_longitudinal_report(
    container: ContainerDep,
    window: int = Query(default=8, ge=2, le=24),
    cohort_size: int = Query(default=3, ge=1, le=10),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_longitudinal_report(
        window=window,
        cohort_size=cohort_size,
    )


@router.get("/scenarios/horizon-report")
async def get_scenario_horizon_report(
    container: ContainerDep,
    short_window: int = Query(default=3, ge=1, le=12),
    medium_window: int = Query(default=6, ge=1, le=24),
    long_window: int = Query(default=12, ge=1, le=36),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_horizon_report(
        short_window=short_window,
        medium_window=medium_window,
        long_window=long_window,
    )


@router.get("/scenarios/multiweek-report")
async def get_scenario_multiweek_report(
    container: ContainerDep,
    bucket_days: int = Query(default=7, ge=1, le=30),
    bucket_count: int = Query(default=4, ge=1, le=12),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_multiweek_report(
        bucket_days=bucket_days,
        bucket_count=bucket_count,
    )


@router.get("/scenarios/sustained-drift-report")
async def get_scenario_sustained_drift_report(
    container: ContainerDep,
    bucket_days: int = Query(default=7, ge=1, le=30),
    bucket_count: int = Query(default=6, ge=2, le=16),
    min_streak: int = Query(default=2, ge=1, le=8),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_sustained_drift_report(
        bucket_days=bucket_days,
        bucket_count=bucket_count,
        min_streak=min_streak,
    )


@router.get("/scenarios/release-gate")
async def get_scenario_release_gate(
    container: ContainerDep,
    window: int = Query(default=6, ge=2, le=20),
    baseline_label: str = Query(default="default"),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_release_gate(
        window=window,
        baseline_label=baseline_label,
    )


@router.get("/scenarios/ship-readiness")
async def get_scenario_ship_readiness(
    container: ContainerDep,
    window: int = Query(default=6, ge=2, le=20),
    baseline_label: str = Query(default="default"),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_ship_readiness(
        window=window,
        baseline_label=baseline_label,
    )


@router.get("/scenarios/baseline-governance")
async def get_scenario_baseline_governance(
    container: ContainerDep,
    window: int = Query(default=6, ge=1, le=20),
    baseline_label: str = Query(default="default"),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_baseline_governance_report(
        window=window,
        baseline_label=baseline_label,
    )


@router.get("/scenarios/migration-readiness")
async def get_scenario_migration_readiness(
    container: ContainerDep,
    sample_size: int = Query(default=6, ge=1, le=20),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_migration_readiness_report(
        sample_size=sample_size,
    )


@router.get("/scenarios/hardening-checklist")
async def get_scenario_hardening_checklist(
    container: ContainerDep,
    window: int = Query(default=6, ge=2, le=20),
    baseline_label: str = Query(default="default"),
    incident_limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_hardening_checklist(
        window=window,
        baseline_label=baseline_label,
        incident_limit=incident_limit,
    )


@router.get("/scenarios/release-dossier")
async def get_scenario_release_dossier(
    container: ContainerDep,
    window: int = Query(default=6, ge=2, le=20),
    baseline_label: str = Query(default="default"),
    incident_limit: int = Query(default=20, ge=1, le=50),
    cohort_size: int = Query(default=3, ge=1, le=10),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_release_dossier(
        window=window,
        baseline_label=baseline_label,
        incident_limit=incident_limit,
        cohort_size=cohort_size,
    )


@router.get("/scenarios/launch-signoff")
async def get_scenario_launch_signoff(
    container: ContainerDep,
    window: int = Query(default=6, ge=2, le=20),
    baseline_label: str = Query(default="default"),
    incident_limit: int = Query(default=20, ge=1, le=50),
    cohort_size: int = Query(default=3, ge=1, le=10),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_launch_signoff_report(
        window=window,
        baseline_label=baseline_label,
        incident_limit=incident_limit,
        cohort_size=cohort_size,
    )


@router.get("/scenarios/safety-audit")
async def get_scenario_safety_audit_report(
    container: ContainerDep,
    window: int = Query(default=6, ge=1, le=20),
    incident_limit: int = Query(default=12, ge=1, le=50),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_safety_audit_report(
        window=window,
        incident_limit=incident_limit,
    )


@router.get("/scenarios/redteam-report")
async def get_scenario_redteam_report(
    container: ContainerDep,
    window: int = Query(default=6, ge=1, le=20),
    incident_limit: int = Query(default=12, ge=1, le=50),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_redteam_report(
        window=window,
        incident_limit=incident_limit,
    )


@router.get("/scenarios/misalignment-report")
async def get_scenario_misalignment_report(
    container: ContainerDep,
    window: int = Query(default=6, ge=1, le=20),
    incident_limit: int = Query(default=12, ge=1, le=50),
) -> dict[str, object]:
    return await container.scenario_evaluation_service.build_misalignment_report(
        window=window,
        incident_limit=incident_limit,
    )


@router.get("/scenarios/compare")
async def compare_scenario_runs(
    baseline_run_id: str,
    candidate_run_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.compare_runs(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
        )
    except ScenarioRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/scenarios/runs/{run_id}")
async def get_scenario_run(
    run_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.get_run(run_id=run_id)
    except ScenarioRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    container: ContainerDep,
) -> dict[str, object]:
    try:
        return await container.scenario_evaluation_service.get_scenario(scenario_id=scenario_id)
    except ScenarioNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
