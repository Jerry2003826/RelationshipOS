from dataclasses import dataclass
from types import SimpleNamespace

from relationship_os.application.runtime.proactive_event_builder import build_proactive_events
from relationship_os.domain.event_types import (
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_FOLLOWUP_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
)


@dataclass
class _Value:
    value: str


def test_build_proactive_events_maps_artifacts_in_runtime_order() -> None:
    artifacts = SimpleNamespace(
        system3_snapshot=_Value("system3"),
        proactive_followup_directive=_Value("followup"),
        proactive_cadence_plan=_Value("cadence"),
        proactive_aggregate_governance_assessment=_Value("governance"),
        reengagement_matrix_assessment=_Value("matrix"),
        reengagement_plan=_Value("reengagement"),
        proactive_scheduling_plan=_Value("scheduling"),
        proactive_orchestration_plan=_Value("orchestration"),
        proactive_actuation_plan=_Value("actuation"),
        proactive_progression_plan=_Value("progression"),
        proactive_guardrail_plan=_Value("guardrail"),
    )

    events = build_proactive_events(artifacts)

    assert events[0].event_type == SYSTEM3_SNAPSHOT_UPDATED
    assert events[0].payload == {"value": "system3"}
    assert events[1].event_type == PROACTIVE_FOLLOWUP_UPDATED
    assert events[1].payload == {"value": "followup"}
    assert events[8].event_type == PROACTIVE_ACTUATION_UPDATED
    assert events[8].payload == {"value": "actuation"}
    assert len(events) == 11
