from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from relationship_os.application.evaluation_service.summary_builder import build_summary
from relationship_os.application.evaluation_service.turn_record import TurnRecord

_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "summary_builder"


def _load_case(name: str) -> dict[str, object]:
    return json.loads((_FIXTURES_DIR / f"{name}.json").read_text())


@pytest.mark.parametrize(
    "fixture_name",
    [
        "minimal_session",
        "quality_degradation_session",
        "proactive_system3_rich_session",
        "last_turn_projection_session",
    ],
)
def test_build_summary_matches_snapshot(fixture_name: str) -> None:
    case = _load_case(fixture_name)
    actual = build_summary(
        session_id=str(case["session_id"]),
        turn_records=[TurnRecord(**item) for item in case["turn_records"]],
        event_count=int(case["event_count"]),
        started_at=case["started_at"],
        last_event_at=case["last_event_at"],
        started_metadata=dict(case["started_metadata"]),
    )
    assert actual == case["expected_summary"]


def test_build_summary_orchestrator_has_no_top_level_list_comp_walks() -> None:
    source = Path(
        "src/relationship_os/application/evaluation_service/summary_builder.py"
    ).read_text()
    module = ast.parse(source)
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_summary"
    )
    top_level_list_comp_assignments = [
        statement
        for statement in function.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) for target in statement.targets)
        and isinstance(statement.value, ast.ListComp)
    ]
    assert top_level_list_comp_assignments == []
