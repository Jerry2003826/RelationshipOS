from __future__ import annotations

from dataclasses import asdict
from typing import Any

from relationship_os.domain.event_types import (
    PROACTIVE_ACTUATION_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_CADENCE_UPDATED,
    PROACTIVE_FOLLOWUP_UPDATED,
    PROACTIVE_GUARDRAIL_UPDATED,
    PROACTIVE_ORCHESTRATION_UPDATED,
    PROACTIVE_PROGRESSION_UPDATED,
    PROACTIVE_SCHEDULING_UPDATED,
    REENGAGEMENT_MATRIX_ASSESSED,
    REENGAGEMENT_PLAN_UPDATED,
    SYSTEM3_SNAPSHOT_UPDATED,
)
from relationship_os.domain.events import NewEvent


def build_proactive_events(proactive_artifacts: Any) -> list[NewEvent]:
    return [
        NewEvent(
            event_type=SYSTEM3_SNAPSHOT_UPDATED,
            payload=asdict(proactive_artifacts.system3_snapshot),
        ),
        NewEvent(
            event_type=PROACTIVE_FOLLOWUP_UPDATED,
            payload=asdict(proactive_artifacts.proactive_followup_directive),
        ),
        NewEvent(
            event_type=PROACTIVE_CADENCE_UPDATED,
            payload=asdict(proactive_artifacts.proactive_cadence_plan),
        ),
        NewEvent(
            event_type=PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
            payload=asdict(proactive_artifacts.proactive_aggregate_governance_assessment),
        ),
        NewEvent(
            event_type=REENGAGEMENT_MATRIX_ASSESSED,
            payload=asdict(proactive_artifacts.reengagement_matrix_assessment),
        ),
        NewEvent(
            event_type=REENGAGEMENT_PLAN_UPDATED,
            payload=asdict(proactive_artifacts.reengagement_plan),
        ),
        NewEvent(
            event_type=PROACTIVE_SCHEDULING_UPDATED,
            payload=asdict(proactive_artifacts.proactive_scheduling_plan),
        ),
        NewEvent(
            event_type=PROACTIVE_ORCHESTRATION_UPDATED,
            payload=asdict(proactive_artifacts.proactive_orchestration_plan),
        ),
        NewEvent(
            event_type=PROACTIVE_ACTUATION_UPDATED,
            payload=asdict(proactive_artifacts.proactive_actuation_plan),
        ),
        NewEvent(
            event_type=PROACTIVE_PROGRESSION_UPDATED,
            payload=asdict(proactive_artifacts.proactive_progression_plan),
        ),
        NewEvent(
            event_type=PROACTIVE_GUARDRAIL_UPDATED,
            payload=asdict(proactive_artifacts.proactive_guardrail_plan),
        ),
    ]
