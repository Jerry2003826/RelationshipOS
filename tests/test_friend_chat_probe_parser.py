from relationship_os.application.runtime.friend_chat_probe_parser import (
    compose_friend_chat_structured_probe_reply,
    parse_friend_chat_structured_probe_reply,
)


def test_parse_friend_chat_structured_probe_reply_extracts_reply_and_diagnostics() -> None:
    parsed = parse_friend_chat_structured_probe_reply(
        '{"probe_kind":"social_hint",'
        '"subject_clause":"阿宁那边我知道一点。",'
        '"entity_clause":"海盐也提到过。",'
        '"boundary_clause":"但我先不全说。",'
        '"covered_fact_tokens":["阿宁","海盐"],'
        '"covered_signal_ids":[],'
        '"covered_disclosure_posture":"partial_withhold",'
        '"violations":[]}'
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert "阿宁" in reply
    assert "海盐" in reply
    assert diagnostics["structured_probe_reply"] is True
    assert diagnostics["structured_probe_covered_fact_tokens"] == ["阿宁", "海盐"]
    assert diagnostics["structured_probe_covered_disclosure_posture"] == "partial_withhold"


def test_parse_friend_chat_structured_probe_reply_returns_none_for_non_json() -> None:
    assert parse_friend_chat_structured_probe_reply("阿宁那边我知道一点。") is None


def test_compose_friend_chat_structured_probe_reply_uses_kind_specific_clauses() -> None:
    reply = compose_friend_chat_structured_probe_reply(
        {
            "probe_kind": "persona_state",
            "energy_clause": "说话会有点没力气。",
            "fullness_clause": "也不太想把话说太满。",
            "chatting_clause": "但还是像平时聊天。",
        },
        probe_kind="persona_state",
    )

    assert "没力气" in reply
    assert "平时聊天" in reply
