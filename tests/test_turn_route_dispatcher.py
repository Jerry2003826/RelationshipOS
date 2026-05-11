from types import SimpleNamespace

import pytest

from relationship_os.application.analyzers.vanguard_router import RouterDecision
from relationship_os.application.runtime.turn_route_dispatcher import dispatch_turn_route
from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import SESSION_STARTED, USER_MESSAGE_RECEIVED


class _FakeRuntime:
    def __init__(self) -> None:
        self.profile_updates: list[dict[str, object]] = []
        self.light_recall_calls: list[dict[str, object]] = []
        self.deep_analysis_calls = 0

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

    async def _build_turn_analysis(self, **_kwargs):  # type: ignore[no-untyped-def]
        self.deep_analysis_calls += 1
        raise AssertionError("LIGHT_RECALL must not build deep analysis")


@pytest.mark.asyncio
async def test_dispatch_turn_route_light_recall_skips_deep_analysis() -> None:
    runtime = _FakeRuntime()
    turn_input = TurnInput(text="remember this lightly")
    turn_context = SimpleNamespace(
        prior_events=[],
        runtime_state={},
        user_id="user-1",
        transcript_messages=[],
        turn_index=0,
    )

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
    assert runtime.deep_analysis_calls == 0
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
