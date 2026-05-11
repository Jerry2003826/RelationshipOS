from relationship_os.application.runtime.friend_chat_digest_helpers import (
    friend_chat_narrative_digest_values,
    friend_chat_relationship_digest_values,
    normalize_friend_chat_narrative_digest,
    normalize_friend_chat_owner,
    normalize_friend_chat_relationship_digest,
)


def test_normalize_friend_chat_owner_prefers_explicit_subject_hint() -> None:
    assert normalize_friend_chat_owner({"subject_hint": "other_user:anning"}) == "阿宁"
    assert normalize_friend_chat_owner({"value": "阿宁提到过海盐"}) == "阿宁"
    assert normalize_friend_chat_owner({}) == "有人"


def test_normalize_friend_chat_narrative_digest_from_text() -> None:
    digest = normalize_friend_chat_narrative_digest("最近有点累，做什么都慢，也不太想回消息。")

    assert "tired" in digest["signals"]
    assert "slow" in digest["signals"]
    assert "withdrawn" in digest["signals"]


def test_friend_chat_narrative_digest_values_flattens_signals_and_tone() -> None:
    values = friend_chat_narrative_digest_values(
        {"signals": ["tired"], "markers": ["慢"], "dominant_tone": "low_energy"}
    )

    assert values == ["state_signal:tired", "state_marker:慢", "state_tone:low_energy"]


def test_normalize_friend_chat_relationship_digest_from_text() -> None:
    digest = normalize_friend_chat_relationship_digest("现在更熟一点，至少还在，也记得那些小习惯。")

    assert "closer" in digest["signals"]
    assert "still_here" in digest["signals"]
    assert "remembers_details" in digest["signals"]


def test_friend_chat_relationship_digest_values_flattens_counters() -> None:
    values = friend_chat_relationship_digest_values(
        {
            "signals": ["closer"],
            "markers": ["还在"],
            "interaction_band": "warm",
            "total_interactions": 7,
        }
    )

    assert values == [
        "relationship_signal:closer",
        "relationship_marker:还在",
        "relationship_band:warm",
        "relationship_interactions:7",
    ]
