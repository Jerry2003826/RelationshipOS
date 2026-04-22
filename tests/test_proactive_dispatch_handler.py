import asyncio
from datetime import datetime
from typing import Any

from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_FOLLOWUP_DISPATCHED,
    PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_LINE_MACHINE_UPDATED,
    PROACTIVE_LINE_STATE_UPDATED,
    PROACTIVE_LINE_TRANSITION_UPDATED,
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_MACHINE_UPDATED,
    PROACTIVE_STAGE_REFRESH_UPDATED,
    PROACTIVE_STAGE_REPLAN_UPDATED,
    PROACTIVE_STAGE_STATE_UPDATED,
    PROACTIVE_STAGE_TRANSITION_UPDATED,
    SESSION_ARCHIVED,
)
from relationship_os.domain.events import NewEvent, utc_now
from relationship_os.main import create_app

_COMMON_DISPATCH_EVENT_TYPES = [
    PROACTIVE_STAGE_REFRESH_UPDATED,
    PROACTIVE_AGGREGATE_GOVERNANCE_ASSESSED,
    PROACTIVE_AGGREGATE_CONTROLLER_UPDATED,
    PROACTIVE_ORCHESTRATION_CONTROLLER_UPDATED,
    PROACTIVE_STAGE_REPLAN_UPDATED,
    PROACTIVE_STAGE_CONTROLLER_UPDATED,
    PROACTIVE_LINE_CONTROLLER_UPDATED,
    PROACTIVE_DISPATCH_FEEDBACK_ASSESSED,
    PROACTIVE_DISPATCH_GATE_UPDATED,
    PROACTIVE_DISPATCH_ENVELOPE_UPDATED,
    PROACTIVE_STAGE_STATE_UPDATED,
    PROACTIVE_STAGE_TRANSITION_UPDATED,
    PROACTIVE_STAGE_MACHINE_UPDATED,
    PROACTIVE_LINE_STATE_UPDATED,
    PROACTIVE_LINE_TRANSITION_UPDATED,
    PROACTIVE_LINE_MACHINE_UPDATED,
]


async def _create_ready_session(
    container: Any,
    *,
    session_id: str,
) -> dict[str, Any]:
    await container.runtime_service.create_session(session_id=session_id)
    await container.runtime_service.process_turn(
        session_id=session_id,
        user_message="I'm exhausted and my chest feels tight, please keep this simple.",
    )
    await container.runtime_service.process_turn(
        session_id=session_id,
        user_message="Let's keep moving on the roadmap and make one steady next step.",
    )
    queue_payload = await container.proactive_followup_service.list_followups()
    return _queue_item_for(queue_payload, session_id=session_id)


async def _dispatch_at_due_time(
    container: Any,
    *,
    session_id: str,
    queue_item: dict[str, Any],
    source: str = "manual",
) -> dict[str, Any]:
    due_at = datetime.fromisoformat(queue_item["due_at"])
    due_payload = await container.proactive_followup_service.list_followups(as_of=due_at)
    due_item = _queue_item_for(due_payload, session_id=session_id)
    return await container.runtime_service.dispatch_proactive_followup(
        session_id=session_id,
        source=source,
        queue_item=due_item,
    )


def _queue_item_for(payload: dict[str, Any], *, session_id: str) -> dict[str, Any]:
    for item in payload["items"]:
        if item["session_id"] == session_id:
            return item
    raise AssertionError(f"missing queue item for {session_id}")


def test_build_system3_snapshot_model_projects_expected_fields() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        try:
            handler = container.runtime_service._proactive_dispatch_handler
            state: dict[str, Any] = {
                "triggered_turn_index": 7,
                "identity_anchor": "collaborative_reflective_support",
                "identity_consistency": "adaptive",
                "identity_confidence": 0.81,
                "identity_trajectory_status": "adjusting",
                "identity_trajectory_target": "calibrated_support",
                "identity_trajectory_trigger": "context_shift",
                "identity_trajectory_notes": ["identity_note"],
                "growth_stage": "working_alliance",
                "growth_signal": "steady_progress",
                "user_model_confidence": 0.77,
                "user_needs": ["clarity", "rest"],
                "user_preferences": ["gentle_pacing"],
                "emotional_debt_status": "elevated",
                "emotional_debt_score": 0.34,
                "debt_signals": ["fatigue"],
                "emotional_debt_trajectory_status": "recovering",
                "emotional_debt_trajectory_target": "lower_debt",
                "emotional_debt_trajectory_trigger": "supportive_turn",
                "emotional_debt_trajectory_notes": ["debt_note"],
                "strategy_audit_status": "review",
                "strategy_fit": "guarded",
                "strategy_audit_notes": ["strategy_note"],
                "strategy_audit_trajectory_status": "recovering",
                "strategy_audit_trajectory_target": "aligned_strategy_path",
                "strategy_audit_trajectory_trigger": "strategy_guard",
                "strategy_audit_trajectory_notes": ["strategy_trajectory_note"],
                "strategy_supervision_status": "review",
                "strategy_supervision_mode": "watchful_supervision",
                "strategy_supervision_trigger": "strategy_drift",
                "strategy_supervision_notes": ["supervision_note"],
                "strategy_supervision_trajectory_status": "recovering",
                "strategy_supervision_trajectory_target": "steady_supervision",
                "strategy_supervision_trajectory_trigger": "supervision_line",
                "strategy_supervision_trajectory_notes": ["supervision_trajectory_note"],
                "moral_reasoning_status": "review",
                "moral_posture": "repair_care",
                "moral_conflict": "tension",
                "moral_principles": ["care", "autonomy"],
                "moral_notes": ["moral_note"],
                "moral_trajectory_status": "recovering",
                "moral_trajectory_target": "steady_progress_care",
                "moral_trajectory_trigger": "repair_move",
                "moral_trajectory_notes": ["moral_trajectory_note"],
                "user_model_evolution_status": "review",
                "user_model_revision_mode": "active_revision",
                "user_model_shift_signal": "emerging_shift",
                "user_model_evolution_notes": ["model_note"],
                "user_model_trajectory_status": "recovering",
                "user_model_trajectory_target": "steady_refinement",
                "user_model_trajectory_trigger": "model_shift",
                "user_model_trajectory_notes": ["model_trajectory_note"],
                "expectation_calibration_status": "review",
                "expectation_calibration_target": "bounded_progress",
                "expectation_calibration_trigger": "expectation_shift",
                "expectation_calibration_notes": ["expectation_note"],
                "expectation_calibration_trajectory_status": "recovering",
                "expectation_calibration_trajectory_target": "bounded_progress",
                "expectation_calibration_trajectory_trigger": "expectation_line",
                "expectation_calibration_trajectory_notes": ["expectation_trajectory_note"],
                "growth_transition_status": "review",
                "growth_transition_target": "deepening",
                "growth_transition_trigger": "earned_progress",
                "growth_transition_readiness": 0.62,
                "growth_transition_notes": ["growth_note"],
                "growth_transition_trajectory_status": "recovering",
                "growth_transition_trajectory_target": "deepening",
                "growth_transition_trajectory_trigger": "growth_line",
                "growth_transition_trajectory_notes": ["growth_trajectory_note"],
                "version_migration_status": "review",
                "version_migration_scope": "projection_upgrade",
                "version_migration_trigger": "schema_shift",
                "version_migration_notes": ["migration_note"],
                "version_migration_trajectory_status": "recovering",
                "version_migration_trajectory_target": "projection_upgrade",
                "version_migration_trajectory_trigger": "migration_line",
                "version_migration_trajectory_notes": ["migration_trajectory_note"],
                "review_focus": ["dependency", "continuity"],
            }
            for domain in (
                "dependency",
                "autonomy",
                "boundary",
                "support",
                "continuity",
                "repair",
                "attunement",
                "trust",
                "clarity",
                "pacing",
                "commitment",
                "disclosure",
                "reciprocity",
                "pressure",
                "relational",
                "safety",
                "progress",
                "stability",
            ):
                state[f"{domain}_governance_status"] = "review"
                state[f"{domain}_governance_target"] = f"{domain}_target"
                state[f"{domain}_governance_trigger"] = f"{domain}_trigger"
                state[f"{domain}_governance_notes"] = [f"{domain}_note"]
                state[f"{domain}_governance_trajectory_status"] = "recovering"
                state[f"{domain}_governance_trajectory_target"] = f"{domain}_trajectory_target"
                state[f"{domain}_governance_trajectory_trigger"] = f"{domain}_trajectory_trigger"
                state[f"{domain}_governance_trajectory_notes"] = [f"{domain}_trajectory_note"]

            snapshot = handler._build_system3_snapshot_model(state)

            scalar_fields = (
                "triggered_turn_index",
                "identity_anchor",
                "identity_consistency",
                "identity_confidence",
                "growth_stage",
                "growth_signal",
                "user_model_confidence",
                "emotional_debt_status",
                "emotional_debt_score",
                "strategy_audit_status",
                "strategy_fit",
                "strategy_supervision_status",
                "strategy_supervision_mode",
                "strategy_supervision_trigger",
                "moral_reasoning_status",
                "moral_posture",
                "moral_conflict",
                "user_model_evolution_status",
                "user_model_revision_mode",
                "user_model_shift_signal",
                "expectation_calibration_status",
                "expectation_calibration_target",
                "expectation_calibration_trigger",
                "growth_transition_status",
                "growth_transition_target",
                "growth_transition_trigger",
                "growth_transition_readiness",
                "version_migration_status",
                "version_migration_scope",
                "version_migration_trigger",
            )
            list_fields = (
                "identity_trajectory_notes",
                "user_needs",
                "user_preferences",
                "debt_signals",
                "emotional_debt_trajectory_notes",
                "strategy_audit_notes",
                "strategy_audit_trajectory_notes",
                "strategy_supervision_notes",
                "strategy_supervision_trajectory_notes",
                "moral_principles",
                "moral_notes",
                "moral_trajectory_notes",
                "user_model_evolution_notes",
                "user_model_trajectory_notes",
                "expectation_calibration_notes",
                "expectation_calibration_trajectory_notes",
                "growth_transition_notes",
                "growth_transition_trajectory_notes",
                "version_migration_notes",
                "version_migration_trajectory_notes",
                "review_focus",
            )
            trajectory_prefixes = (
                "identity_trajectory",
                "emotional_debt_trajectory",
                "strategy_audit_trajectory",
                "strategy_supervision_trajectory",
                "moral_trajectory",
                "user_model_trajectory",
                "expectation_calibration_trajectory",
                "growth_transition_trajectory",
                "version_migration_trajectory",
            )

            for field in scalar_fields:
                assert getattr(snapshot, field) == state[field]
            for field in list_fields:
                assert getattr(snapshot, field) == state[field]
            for prefix in trajectory_prefixes:
                assert getattr(snapshot, f"{prefix}_status") == state[f"{prefix}_status"]
                assert getattr(snapshot, f"{prefix}_target") == state[f"{prefix}_target"]
                assert getattr(snapshot, f"{prefix}_trigger") == state[f"{prefix}_trigger"]
                assert getattr(snapshot, f"{prefix}_notes") == state[f"{prefix}_notes"]
            for domain in (
                "dependency",
                "autonomy",
                "boundary",
                "support",
                "continuity",
                "repair",
                "attunement",
                "trust",
                "clarity",
                "pacing",
                "commitment",
                "disclosure",
                "reciprocity",
                "pressure",
                "relational",
                "safety",
                "progress",
                "stability",
            ):
                assert (
                    getattr(snapshot, f"{domain}_governance_status")
                    == state[f"{domain}_governance_status"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_target")
                    == state[f"{domain}_governance_target"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_trigger")
                    == state[f"{domain}_governance_trigger"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_notes")
                    == state[f"{domain}_governance_notes"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_trajectory_status")
                    == state[f"{domain}_governance_trajectory_status"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_trajectory_target")
                    == state[f"{domain}_governance_trajectory_target"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_trajectory_trigger")
                    == state[f"{domain}_governance_trajectory_trigger"]
                )
                assert (
                    getattr(snapshot, f"{domain}_governance_trajectory_notes")
                    == state[f"{domain}_governance_trajectory_notes"]
                )
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_session_not_found() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        try:
            result = await container.runtime_service.dispatch_proactive_followup(
                session_id="missing-dispatch",
                source="manual",
            )
            assert result == {
                "session_id": "missing-dispatch",
                "dispatched": False,
                "reason": "session_not_found",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_session_archived() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "archived-dispatch"
        try:
            await container.runtime_service.create_session(session_id=session_id)
            await container.stream_service.append_events(
                stream_id=session_id,
                expected_version=None,
                events=[
                    NewEvent(
                        event_type=SESSION_ARCHIVED,
                        payload={
                            "archived": True,
                            "archived_at": utc_now().isoformat(),
                            "reason": "test_cleanup",
                        },
                    )
                ],
            )
            result = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
            )
            assert result == {
                "session_id": session_id,
                "dispatched": False,
                "reason": "session_archived",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_missing_directive() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "missing-directive-dispatch"
        try:
            await container.runtime_service.create_session(session_id=session_id)
            result = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
            )
            assert result == {
                "session_id": session_id,
                "dispatched": False,
                "reason": "missing_directive",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_directive_not_ready() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "directive-not-ready"
        try:
            await container.runtime_service.create_session(session_id=session_id)
            await container.runtime_service.process_turn(
                session_id=session_id,
                user_message="I'm exhausted and my chest feels tight, please keep this simple.",
            )
            result = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
            )
            assert result == {
                "session_id": session_id,
                "dispatched": False,
                "reason": "directive_not_ready",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_queue_not_actionable() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "queue-not-actionable"
        try:
            await _create_ready_session(container, session_id=session_id)
            result = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
                queue_item={"queue_status": "scheduled"},
            )
            assert result == {
                "session_id": session_id,
                "dispatched": False,
                "reason": "queue_not_actionable",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_already_dispatched_for_requested_stage() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "already-dispatched"
        try:
            initial_item = await _create_ready_session(container, session_id=session_id)
            await _dispatch_at_due_time(
                container,
                session_id=session_id,
                queue_item=initial_item,
            )
            queue_payload = await container.proactive_followup_service.list_followups(
                as_of=datetime.fromisoformat(initial_item["due_at"])
            )
            rescheduled_item = _queue_item_for(queue_payload, session_id=session_id)
            due_payload = await container.proactive_followup_service.list_followups(
                as_of=datetime.fromisoformat(rescheduled_item["due_at"])
            )
            due_item = _queue_item_for(due_payload, session_id=session_id)
            sent_result = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
                queue_item=due_item,
            )
            assert sent_result["dispatched"] is True

            repeated = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
                queue_item={**due_item, "queue_status": "due"},
            )
            assert repeated == {
                "session_id": session_id,
                "dispatched": False,
                "reason": "already_dispatched_for_requested_stage",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_returns_requested_stage_beyond_cadence() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "beyond-cadence"
        try:
            await _create_ready_session(container, session_id=session_id)
            result = await container.runtime_service.dispatch_proactive_followup(
                session_id=session_id,
                source="manual",
                queue_item={
                    "queue_status": "due",
                    "proactive_cadence_stage_index": 99,
                    "proactive_cadence_stage_label": "ghost",
                },
            )
            assert result == {
                "session_id": session_id,
                "dispatched": False,
                "reason": "requested_stage_beyond_cadence",
            }
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_builds_skipped_reschedule_result_and_projection() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "skipped-reschedule"
        try:
            queue_item = await _create_ready_session(container, session_id=session_id)
            result = await _dispatch_at_due_time(
                container,
                session_id=session_id,
                queue_item=queue_item,
            )

            assert result["dispatched"] is False
            assert result["reason"] == "lifecycle_dispatch_rescheduled"
            assert result["lifecycle_dispatch"]["decision"] == "reschedule_lifecycle_dispatch"
            assert result["lifecycle_outcome"]["decision"] == "lifecycle_dispatch_rescheduled"
            event_types = [event["event_type"] for event in result["events"]]
            assert event_types == _COMMON_DISPATCH_EVENT_TYPES + [
                PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED
            ]
            queue_payload = await container.proactive_followup_service.list_followups(
                as_of=datetime.fromisoformat(queue_item["due_at"])
            )
            queue_projection = _queue_item_for(queue_payload, session_id=session_id)
            assert result["projection"]["state"]["last_proactive_followup_dispatch"] is None
            assert queue_projection["queue_status"] == "scheduled"
            assert (
                queue_projection["proactive_lifecycle_dispatch_decision"]
                == "reschedule_lifecycle_dispatch"
            )
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_dispatch_builds_sent_result_and_projection() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "sent-dispatch"
        try:
            queue_item = await _create_ready_session(container, session_id=session_id)
            skipped = await _dispatch_at_due_time(
                container,
                session_id=session_id,
                queue_item=queue_item,
            )
            assert skipped["reason"] == "lifecycle_dispatch_rescheduled"

            rescheduled_payload = await container.proactive_followup_service.list_followups(
                as_of=datetime.fromisoformat(queue_item["due_at"])
            )
            rescheduled_item = _queue_item_for(rescheduled_payload, session_id=session_id)
            sent = await _dispatch_at_due_time(
                container,
                session_id=session_id,
                queue_item=rescheduled_item,
            )

            assert sent["dispatched"] is True
            assert sent["assistant_response"] == sent["dispatch"]["content"]
            event_types = [event["event_type"] for event in sent["events"]]
            assert event_types[: len(_COMMON_DISPATCH_EVENT_TYPES)] == _COMMON_DISPATCH_EVENT_TYPES
            assert event_types[len(_COMMON_DISPATCH_EVENT_TYPES)] == PROACTIVE_FOLLOWUP_DISPATCHED
            assert event_types[-1] == PROACTIVE_LIFECYCLE_SNAPSHOT_UPDATED
            assert ASSISTANT_MESSAGE_SENT in event_types
            assert (
                sent["projection"]["state"]["last_proactive_followup_dispatch"]["content"]
                == sent["dispatch"]["content"]
            )
            assert sent["lifecycle_outcome"]["decision"] == "lifecycle_close_loop_sent"
        finally:
            await container.shutdown()

    asyncio.run(scenario())
