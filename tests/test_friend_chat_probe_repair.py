from relationship_os.application.runtime.friend_chat_probe_repair import (
    build_friend_chat_probe_repair_feedback,
    friend_chat_probe_persona_trait_semantics,
    friend_chat_probe_posture_semantics,
    friend_chat_probe_signal_semantics,
    render_friend_chat_probe_repair_feedback_lines,
)


def test_friend_chat_probe_semantics_describe_known_ids() -> None:
    assert "低能量" in friend_chat_probe_signal_semantics("tired")
    assert "轻轻带" in friend_chat_probe_posture_semantics("partial_withhold")
    assert "平常聊天" in friend_chat_probe_persona_trait_semantics("conversational")


def test_build_friend_chat_probe_repair_feedback_detects_missing_required_items() -> None:
    feedback = build_friend_chat_probe_repair_feedback(
        {
            "structured_probe_covered_fact_tokens": ["阿宁"],
            "structured_probe_covered_signal_ids": [],
            "structured_probe_covered_persona_traits": [],
            "structured_probe_covered_disclosure_posture": "",
            "friend_chat_exposed_plan_noncompliant": True,
        },
        {
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_signal_ids": ["tired"],
            "required_persona_traits": ["conversational"],
            "required_disclosure_posture": "partial_withhold",
            "must_cover_required_items": True,
        },
    )

    assert feedback is not None
    assert "plan_noncompliant" in feedback["reason_codes"]
    assert "missing_required_grounding" in feedback["reason_codes"]
    assert feedback["missing_fact_tokens"] == ["海盐"]
    assert feedback["missing_signal_ids"] == ["tired"]
    assert feedback["missing_persona_traits"] == ["conversational"]
    assert feedback["missing_disclosure_posture"] == "partial_withhold"


def test_render_friend_chat_probe_repair_feedback_lines_names_missing_items() -> None:
    lines = render_friend_chat_probe_repair_feedback_lines(
        {
            "reason_codes": ["missing_required_grounding"],
            "missing_fact_tokens": ["海盐"],
            "missing_signal_semantics": {"tired": "低能量"},
            "missing_disclosure_posture_semantics": "知道一点但不说满",
        }
    )

    assert lines[0] == "补救重点："
    assert any("海盐" in line for line in lines)
    assert any("tired 要表达成：低能量" in line for line in lines)
    assert any("披露姿态要表达成" in line for line in lines)
