import asyncio

from relationship_os.application.runtime.user_profile_turn_updater import (
    UserProfileTurnUpdater,
)


def test_user_profile_turn_updater_restores_updates_and_persists_snapshot() -> None:
    calls = []

    class _UserService:
        async def get_user_index(self, *, user_id: str):  # type: ignore[no-untyped-def]
            calls.append(("get", user_id))
            return {
                "metadata": {
                    "profile_ema_128": {
                        "vector": [1.0] + [0.0] * 127,
                    }
                }
            }

        async def update_profile(self, *, user_id: str, metadata):  # type: ignore[no-untyped-def]
            calls.append(("update", user_id, metadata))

    prefix = asyncio.run(
        UserProfileTurnUpdater(user_service=_UserService()).update_for_turn(
            user_id="user-1",
            user_message="I like quiet late-night coding sessions.",
            readonly_probe_session=False,
        )
    )

    assert prefix is not None
    assert prefix.startswith("profile_vec(128d):")
    assert calls[0] == ("get", "user-1")
    assert calls[1][0:2] == ("update", "user-1")
    snapshot = calls[1][2]["profile_ema_128"]
    assert snapshot["dim"] == 128
    assert snapshot["turns_seen"] == 1
    assert snapshot["updated_at"]
    assert snapshot["prefix"] == prefix
    assert len(snapshot["vector"]) == 128


def test_user_profile_turn_updater_skips_readonly_or_empty_turns() -> None:
    calls = []

    class _UserService:
        async def get_user_index(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("get", kwargs))

        async def update_profile(self, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(("update", kwargs))

    updater = UserProfileTurnUpdater(user_service=_UserService())

    readonly_prefix = asyncio.run(
        updater.update_for_turn(
            user_id="user-1",
            user_message="hello",
            readonly_probe_session=True,
        )
    )
    empty_prefix = asyncio.run(
        updater.update_for_turn(
            user_id="user-1",
            user_message="   ",
            readonly_probe_session=False,
        )
    )
    anonymous_prefix = asyncio.run(
        updater.update_for_turn(
            user_id=None,
            user_message="hello",
            readonly_probe_session=False,
        )
    )

    assert readonly_prefix is None
    assert empty_prefix is None
    assert anonymous_prefix is None
    assert calls == []
