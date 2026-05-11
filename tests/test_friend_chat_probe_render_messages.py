from types import SimpleNamespace

from relationship_os.application.runtime.friend_chat_probe_render_messages import (
    build_friend_chat_plaintext_probe_repair_messages,
    build_friend_chat_probe_runtime_card,
    build_friend_chat_social_repair_messages,
    build_friend_chat_structured_probe_messages,
    build_friend_chat_structured_probe_repair_messages,
    coerce_friend_chat_structured_probe_response,
)


def test_build_friend_chat_structured_probe_messages_requests_json() -> None:
    messages = build_friend_chat_structured_probe_messages(
        user_message="你现在说话是什么状态？",
        probe_plan={"probe_kind": "persona_state", "required_persona_traits": ["low_energy"]},
    )

    assert messages[0].role == "system"
    assert "JSON" in messages[0].content
    assert "probe_answer_plan" in messages[1].content
    assert "output_contract" in messages[1].content


def test_build_friend_chat_probe_runtime_card_includes_plan_and_repair_feedback() -> None:
    card = build_friend_chat_probe_runtime_card(
        probe_plan={
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_disclosure_posture": "partial_withhold",
        },
        repair_feedback={"missing_fact_tokens": ["海盐"]},
    )

    assert "Benchmark probe reply contract" in card
    assert "probe_answer_plan" in card
    assert "补救重点" in card
    assert "海盐" in card


def test_build_friend_chat_structured_probe_repair_messages_includes_feedback() -> None:
    messages = build_friend_chat_structured_probe_repair_messages(
        user_message="你现在说话是什么状态？",
        probe_plan={"probe_kind": "persona_state"},
        invalid_output="{}",
        repair_feedback={"reason_codes": ["missing_required_grounding"]},
    )

    assert "repair_feedback" in messages[1].content
    assert "重做" in messages[0].content


def test_build_friend_chat_plaintext_probe_repair_messages_uses_prompt_and_feedback() -> None:
    messages = build_friend_chat_plaintext_probe_repair_messages(
        user_message="你是不是知道一点阿宁的事？",
        probe_plan={"probe_kind": "social_hint", "required_fact_tokens": ["阿宁"]},
        repair_feedback={"missing_fact_tokens": ["阿宁"]},
    )

    assert "不要输出 JSON" in messages[0].content
    assert "阿宁" in messages[1].content


def test_build_friend_chat_social_repair_messages_uses_social_cues() -> None:
    messages = build_friend_chat_social_repair_messages(
        user_message="你是不是知道一点阿宁和海盐的事？",
        social_cues={
            "subject_token": "阿宁",
            "entity_token": "海盐",
            "disclosure_posture": "partial",
            "subject_entity_relation": "海盐是阿宁的猫",
        },
    )

    assert messages is not None
    assert "社交边界回复" in messages[0].content
    assert "阿宁" in messages[1].content
    assert "海盐" in messages[1].content


def test_coerce_friend_chat_structured_probe_response_parses_json_response() -> None:
    response = SimpleNamespace(
        model="m",
        output_text=(
            '{"probe_kind":"persona_state","energy_clause":"说话会有点没力气。",'
            '"fullness_clause":"也不太想把话说太满。","chatting_clause":"但还是像平时聊天。"}'
        ),
        tool_calls=[],
        usage=None,
        latency_ms=1,
        diagnostics={},
        failure=None,
    )

    coerced = coerce_friend_chat_structured_probe_response(response, probe_kind="persona_state")

    assert coerced is not None
    assert "没力气" in coerced.output_text
    assert coerced.diagnostics["structured_probe_reply"] is True
