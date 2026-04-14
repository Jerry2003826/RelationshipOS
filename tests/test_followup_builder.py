import asyncio
from datetime import datetime
from typing import Any

from relationship_os.application.analyzers.proactive.lifecycle_projection import (
    LegacyLifecycleStreamUnsupportedError,
)
from relationship_os.application.proactive_followup_service.followup_builder import (
    build_followup_item,
)
from relationship_os.domain.event_types import SESSION_ARCHIVED
from relationship_os.domain.events import NewEvent, utc_now
from relationship_os.main import create_app


def _followup_item(
    payload: dict[str, Any],
    *,
    session_id: str,
) -> dict[str, Any]:
    for item in payload["items"]:
        if item["session_id"] == session_id:
            return item
    raise AssertionError(f"followup item not found for {session_id}")


def test_build_followup_item_returns_none_for_missing_or_filtered_sessions() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        reference_time = utc_now()
        try:
            assert (
                await build_followup_item(
                    stream_service=container.stream_service,
                    session_id="missing-followup",
                    reference_time=reference_time,
                    runtime_projector_version=container.settings.default_projector_version,
                )
                is None
            )

            await container.runtime_service.create_session(
                session_id="scenario-followup",
                metadata={"source": "scenario_evaluation"},
            )
            assert (
                await build_followup_item(
                    stream_service=container.stream_service,
                    session_id="scenario-followup",
                    reference_time=reference_time,
                    runtime_projector_version=container.settings.default_projector_version,
                )
                is None
            )

            await container.runtime_service.create_session(session_id="archived-followup")
            await container.stream_service.append_events(
                stream_id="archived-followup",
                expected_version=None,
                events=[
                    NewEvent(
                        event_type=SESSION_ARCHIVED,
                        payload={
                            "archived": True,
                            "archived_at": reference_time.isoformat(),
                            "reason": "test_cleanup",
                        },
                    )
                ],
            )
            assert (
                await build_followup_item(
                    stream_service=container.stream_service,
                    session_id="archived-followup",
                    reference_time=reference_time,
                    runtime_projector_version=container.settings.default_projector_version,
                )
                is None
            )

            await container.runtime_service.create_session(session_id="no-directive")
            assert (
                await build_followup_item(
                    stream_service=container.stream_service,
                    session_id="no-directive",
                    reference_time=reference_time,
                    runtime_projector_version=container.settings.default_projector_version,
                )
                is None
            )
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_build_followup_item_returns_none_for_legacy_lifecycle_unsupported_stream(
    monkeypatch,
) -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container

        async def raise_legacy(*args: Any, **kwargs: Any) -> dict[str, Any]:
            raise LegacyLifecycleStreamUnsupportedError(stream_id="legacy-followup")

        monkeypatch.setattr(
            container.stream_service,
            "project_stream",
            raise_legacy,
        )

        try:
            assert (
                await build_followup_item(
                    stream_service=container.stream_service,
                    session_id="legacy-followup",
                    reference_time=utc_now(),
                    runtime_projector_version=container.settings.default_projector_version,
                )
                is None
            )
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_build_followup_item_builds_waiting_item_with_expected_full_shape() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "builder-waiting"
        try:
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
            queue_item = _followup_item(queue_payload, session_id=session_id)
            reference_time = datetime.fromisoformat(queue_payload["as_of"])

            direct_item = await build_followup_item(
                stream_service=container.stream_service,
                session_id=session_id,
                reference_time=reference_time,
                runtime_projector_version=container.settings.default_projector_version,
            )

            assert direct_item == queue_item
            assert direct_item is not None
            assert direct_item["queue_status"] == "waiting"
            assert direct_item["due_at"] is not None
            assert direct_item["base_due_at"] is not None
            assert direct_item["expires_at"] is not None
            assert "proactive_lifecycle_layer_decision" in direct_item
            assert "proactive_lifecycle_activation_decision" in direct_item
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_build_followup_item_builds_rescheduled_item_after_dispatch_override() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "builder-reschedule"
        try:
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
            queue_item = _followup_item(queue_payload, session_id=session_id)
            reference_time = datetime.fromisoformat(queue_item["due_at"])

            await container.proactive_followup_dispatcher.dispatch_due_followups(
                source="manual",
                as_of=reference_time,
                limit=1,
            )

            post_dispatch_payload = await container.proactive_followup_service.list_followups(
                as_of=reference_time
            )
            post_dispatch_item = _followup_item(
                post_dispatch_payload,
                session_id=session_id,
            )
            direct_item = await build_followup_item(
                stream_service=container.stream_service,
                session_id=session_id,
                reference_time=reference_time,
                runtime_projector_version=container.settings.default_projector_version,
            )

            assert direct_item == post_dispatch_item
            assert direct_item is not None
            assert direct_item["queue_status"] == post_dispatch_item["queue_status"]
            assert (
                direct_item["proactive_lifecycle_dispatch_decision"]
                == "reschedule_lifecycle_dispatch"
            )
            assert "lifecycle_activation_buffered" in str(direct_item["schedule_reason"])
            assert (
                direct_item["proactive_lifecycle_activation_decision"]
                == "buffer_current_lifecycle_stage"
            )
            assert direct_item["due_at"] != queue_item["due_at"]
        finally:
            await container.shutdown()

    asyncio.run(scenario())


def test_build_followup_item_builds_hold_item_without_dispatch_override() -> None:
    async def scenario() -> None:
        app = create_app()
        container = app.state.container
        session_id = "builder-hold"
        try:
            await container.runtime_service.create_session(session_id=session_id)
            await container.runtime_service.process_turn(
                session_id=session_id,
                user_message="I'm exhausted and my chest feels tight, please keep this simple.",
            )

            queue_payload = await container.proactive_followup_service.list_followups()
            queue_item = _followup_item(queue_payload, session_id=session_id)
            reference_time = datetime.fromisoformat(queue_payload["as_of"])

            direct_item = await build_followup_item(
                stream_service=container.stream_service,
                session_id=session_id,
                reference_time=reference_time,
                runtime_projector_version=container.settings.default_projector_version,
            )

            assert direct_item == queue_item
            assert direct_item is not None
            assert direct_item["queue_status"] == "hold"
            assert "coordination_not_ready" in direct_item["hold_reasons"]
            assert direct_item["proactive_lifecycle_dispatch_decision"] is None
            assert direct_item["proactive_lifecycle_activation_decision"] is None
        finally:
            await container.shutdown()

    asyncio.run(scenario())
