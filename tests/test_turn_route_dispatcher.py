from types import SimpleNamespace

import pytest

from relationship_os.application.analyzers.vanguard_router import RouterDecision
from relationship_os.application.runtime.turn_route_dispatcher import (
    TurnRouteRuntimeHost,
    dispatch_turn_route,
)
from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import SESSION_STARTED, USER_MESSAGE_RECEIVED


class _FakeRuntime:
    def __init__(self) -> None:
        self.profile_updates: list[dict[str, object]] = []
        self.fast_pong_calls: list[dict[str, object]] = []
        self.light_recall_calls: list[dict[str, object]] = []
        self.deep_analysis_calls: list[dict[str, object]] = []
        self.turn_events_calls: list[dict[str, object]] = []
        self.turn_reply_calls: list[dict[str, object]] = []
        self.proactive_artifacts_calls: list[dict[str, object]] = []
        self.proactive_events_calls: list[object] = []

    async def _generate_fast_pong_reply(self, **kwargs):  # type: ignore[no-untyped-def]
        self.fast_pong_calls.append(kwargs)
        return SimpleNamespace(
            events=[],
            assistant_response="fast reply",
            assistant_responses=["fast reply"],
            response_diagnostics={"route": "FAST_PONG"},
        )

    async def _update_user_profile_for_turn(self, **kwargs):  # type: ignore[no-untyped-def]
        self.profile_updates.append(kwargs)
        return "profile-prefix"

    async def _generate_light_recall_reply(self, **kwargs):  # type: ignore[no-untyped-def]
        self.light_recall_calls.append(kwargs)
        return SimpleNamespace(
            events=[],
            assistant_response="light reply",
            assistant_responses=["light reply"],
            response_diagnostics={"route": "LIGHT_RECALL"},
        )

    async def _build_turn_analysis(self, **kwargs):  # type: ignore[no-untyped-def]
        self.deep_analysis_calls.append(kwargs)
        return SimpleNamespace(kind="analysis")

    def _build_turn_events(self, **kwargs):  # type: ignore[no-untyped-def]
        self.turn_events_calls.append(kwargs)
        return []

    async def _generate_turn_reply(self, **kwargs):  # type: ignore[no-untyped-def]
        self.turn_reply_calls.append(kwargs)
        return SimpleNamespace(
            events=[],
            assistant_response="deep reply",
            assistant_responses=["deep reply"],
            response_diagnostics={"route": "DEEP_THINK"},
        )

    async def _build_proactive_artifacts(self, **kwargs):  # type: ignore[no-untyped-def]
        self.proactive_artifacts_calls.append(kwargs)
        return SimpleNamespace(kind="proactive")

    def _build_proactive_events(self, proactive_artifacts):  # type: ignore[no-untyped-def]
        self.proactive_events_calls.append(proactive_artifacts)
        return []


def test_turn_route_dispatcher_exposes_runtime_host_protocol() -> None:
    assert TurnRouteRuntimeHost.__name__ == "TurnRouteRuntimeHost"


def _turn_context() -> SimpleNamespace:
    return SimpleNamespace(
        prior_events=[],
        runtime_state={},
        user_id="user-1",
        transcript_messages=[],
        turn_index=0,
    )


@pytest.mark.asyncio
async def test_dispatch_turn_route_fast_pong_skips_profile_and_deep_analysis() -> None:
    runtime = _FakeRuntime()
    turn_input = TurnInput(text="ping")

    result = await dispatch_turn_route(
        runtime,
        router_decision=RouterDecision(
            route_type="FAST_PONG",
            reason="test",
            confidence=0.99,
        ),
        session_id="session-1",
        user_message="ping",
        generate_reply=True,
        turn_context=_turn_context(),
        turn_input=turn_input,
        metadata={"source": "test"},
        readonly_probe_session=False,
    )

    assert result.analysis is None
    assert result.analysis_ms == 0.0
    assert runtime.profile_updates == []
    assert runtime.deep_analysis_calls == []
    assert len(runtime.fast_pong_calls) == 1
    assert result.reply_artifacts.assistant_response == "fast reply"


@pytest.mark.asyncio
async def test_dispatch_turn_route_light_recall_skips_deep_analysis() -> None:
    runtime = _FakeRuntime()
    turn_input = TurnInput(text="remember this lightly")
    turn_context = _turn_context()

    result = await dispatch_turn_route(
        runtime,
        router_decision=RouterDecision(
            route_type="LIGHT_RECALL",
            reason="test",
            confidence=0.9,
        ),
        session_id="session-1",
        user_message="remember this lightly",
        generate_reply=True,
        turn_context=turn_context,
        turn_input=turn_input,
        metadata={"source": "test"},
        readonly_probe_session=False,
    )

    assert result.analysis is None
    assert result.analysis_ms == 0.0
    assert runtime.deep_analysis_calls == []
    assert runtime.profile_updates == [
        {
            "user_id": "user-1",
            "user_message": "remember this lightly",
            "readonly_probe_session": False,
        }
    ]
    assert runtime.light_recall_calls[0]["profile_prefix"] == "profile-prefix"
    assert [event.event_type for event in result.events] == [
        SESSION_STARTED,
        USER_MESSAGE_RECEIVED,
    ]
    assert result.reply_artifacts.assistant_response == "light reply"


@pytest.mark.asyncio
async def test_dispatch_turn_route_deep_think_runs_analysis_reply_and_proactive() -> None:
    runtime = _FakeRuntime()
    turn_input = TurnInput(text="think deeply")

    result = await dispatch_turn_route(
        runtime,
        router_decision=RouterDecision(
            route_type="DEEP_THINK",
            reason="test",
            confidence=0.8,
        ),
        session_id="session-1",
        user_message="think deeply",
        generate_reply=True,
        turn_context=_turn_context(),
        turn_input=turn_input,
        metadata={"source": "test"},
        readonly_probe_session=False,
    )

    assert result.analysis.kind == "analysis"
    assert len(runtime.profile_updates) == 1
    assert len(runtime.deep_analysis_calls) == 1
    assert len(runtime.turn_events_calls) == 1
    assert len(runtime.turn_reply_calls) == 1
    assert len(runtime.proactive_artifacts_calls) == 1
    assert len(runtime.proactive_events_calls) == 1
    assert result.reply_artifacts.assistant_response == "deep reply"


@pytest.mark.asyncio
async def test_dispatch_turn_route_deep_think_skips_proactive_for_readonly_probe() -> None:
    runtime = _FakeRuntime()
    turn_input = TurnInput(text="probe")

    result = await dispatch_turn_route(
        runtime,
        router_decision=RouterDecision(
            route_type="DEEP_THINK",
            reason="test",
            confidence=0.8,
        ),
        session_id="session-1",
        user_message="probe",
        generate_reply=True,
        turn_context=_turn_context(),
        turn_input=turn_input,
        metadata={"source": "test"},
        readonly_probe_session=True,
    )

    assert result.analysis.kind == "analysis"
    assert len(runtime.profile_updates) == 1
    assert len(runtime.deep_analysis_calls) == 1
    assert len(runtime.turn_reply_calls) == 1
    assert runtime.proactive_artifacts_calls == []
    assert runtime.proactive_events_calls == []
