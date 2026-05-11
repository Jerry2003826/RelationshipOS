from relationship_os.application.runtime.friend_chat_probe_contracts import (
    build_friend_chat_probe_runtime_checklist,
    build_friend_chat_probe_user_prompt,
    build_friend_chat_structured_probe_output_contract,
    build_friend_chat_structured_probe_payload,
)


def test_build_friend_chat_probe_runtime_checklist_includes_required_items() -> None:
    checklist = build_friend_chat_probe_runtime_checklist(
        {
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_disclosure_posture": "partial_withhold",
            "must_cover_required_items": True,
            "must_explicit_withhold": True,
        }
    )

    assert "执行清单" in checklist
    assert "阿宁 / 海盐" in checklist
    assert "partial_withhold" in checklist
    assert "有限披露边界" in checklist


def test_build_friend_chat_structured_probe_payload_keeps_kind_specific_snapshot() -> None:
    payload = build_friend_chat_structured_probe_payload(
        {
            "probe_kind": "relationship_reflection",
            "language": "zh",
            "required_signal_ids": ["closer", "closer", "still_here"],
            "relationship_snapshot": {"interaction_band": "warm", "total_interactions": 7},
        }
    )

    assert payload["required_signal_ids"] == ["closer", "still_here"]
    assert payload["relationship_snapshot"] == {
        "interaction_band": "warm",
        "total_interactions": 7,
    }


def test_build_friend_chat_probe_user_prompt_names_required_constraints() -> None:
    prompt = build_friend_chat_probe_user_prompt(
        user_message="你是不是知道一点阿宁和海盐的事？",
        probe_plan={
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_disclosure_posture": "partial_withhold",
        },
    )

    assert "原问题：你是不是知道一点阿宁和海盐的事？" in prompt
    assert "必答事实项：阿宁 / 海盐" in prompt
    assert "必答披露姿态ID：partial_withhold" in prompt


def test_build_friend_chat_structured_probe_output_contract_is_kind_specific() -> None:
    contract = build_friend_chat_structured_probe_output_contract({"probe_kind": "persona_state"})

    assert contract["probe_kind"] == "persona_state"
    assert "energy_clause" in contract
    assert "boundary_clause" not in contract
