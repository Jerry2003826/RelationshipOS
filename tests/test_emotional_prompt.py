"""Tests for EmotionalExpert prompt builder (W4.1)."""

from __future__ import annotations

from relationship_os.application.analyzers.emotional_prompt import (
    VALID_EMOTION_TAGS,
    build_emotional_prompt,
    diff_prompts,
)


def test_minimal_prompt_has_all_required_sections() -> None:
    p = build_emotional_prompt(persona="你是贴心的数字人格")
    assert "你是贴心的数字人格" in p.text
    assert "LIGHT_RECALL" in p.text  # default route
    assert "要求" in p.text
    # No memory / profile / tags supplied, those sections must be absent
    assert "近期记忆" not in p.text
    assert "情感标签" not in p.text
    assert "用户画像" not in p.text


def test_full_prompt_includes_every_slot() -> None:
    p = build_emotional_prompt(
        persona="你是贴心的数字人格",
        user_profile_prefix="profile:[0.1,0.2,0.3]",
        recent_memory=[
            {"summary": "昨天加班很累", "tags": ["emotion"]},
            {"summary": "想换工作", "tags": ["plan"]},
        ],
        route="DEEP_THINK",
        emotion_tags=["tired", "sad"],
    )
    assert "你是贴心的数字人格" in p.text
    assert "DEEP_THINK" in p.text
    assert "tired" in p.text
    assert "sad" in p.text
    assert "profile:[0.1,0.2,0.3]" in p.text
    assert "昨天加班很累" in p.text
    assert "想换工作" in p.text
    assert p.route == "DEEP_THINK"
    assert p.emotion_tags == ["tired", "sad"]


def test_invalid_route_falls_back_to_light_recall() -> None:
    p = build_emotional_prompt(persona="x", route="BOGUS")
    assert p.route == "LIGHT_RECALL"
    assert "LIGHT_RECALL" in p.text


def test_invalid_tags_filtered_and_deduped() -> None:
    p = build_emotional_prompt(
        persona="x",
        emotion_tags=["tired", "TIRED", "unknown", "sad", "", " happy "],
    )
    # Dedup lowercased, whitespace-trimmed, invalid dropped
    assert p.emotion_tags == ["tired", "sad", "happy"]


def test_tag_cap_at_four() -> None:
    many = list(VALID_EMOTION_TAGS)[:8]
    p = build_emotional_prompt(persona="x", emotion_tags=many)
    assert len(p.emotion_tags) == 4


def test_memory_cards_capped() -> None:
    recs = [{"summary": f"卡{i}", "tags": ["emotion"]} for i in range(10)]
    p = build_emotional_prompt(
        persona="x", recent_memory=recs, max_memory_cards=2
    )
    assert "卡0" in p.text
    assert "卡1" in p.text
    assert "卡2" not in p.text


def test_memory_skips_empty_summary() -> None:
    recs = [
        {"summary": "", "tags": []},
        {"summary": "   ", "tags": []},
        {"summary": "真正的一条", "tags": ["emotion"]},
    ]
    p = build_emotional_prompt(persona="x", recent_memory=recs)
    assert "真正的一条" in p.text
    assert p.text.count("- ") == 1


def test_profile_prefix_truncated_when_too_long() -> None:
    long = "profile:" + ",".join(["0.123"] * 200)
    p = build_emotional_prompt(persona="x", user_profile_prefix=long)
    assert "..." in p.text
    # Ensure truncation protects budget
    assert any(
        len(s) <= 240 for s in p.sections if s.startswith("用户画像")
    )


def test_include_profile_vec_false_omits_section() -> None:
    p = build_emotional_prompt(
        persona="x",
        user_profile_prefix="profile:[0.1]",
        include_profile_vec=False,
    )
    assert "用户画像" not in p.text


def test_max_chars_hard_clip() -> None:
    big_recs = [{"summary": "累" * 500, "tags": []}]
    p = build_emotional_prompt(
        persona="x" * 500,
        recent_memory=big_recs,
        max_chars=200,
    )
    assert len(p.text) <= 200


def test_diff_prompts_identifies_differences() -> None:
    a = build_emotional_prompt(persona="你是贴心的数字人格")
    b = build_emotional_prompt(
        persona="你是贴心的数字人格", emotion_tags=["sad"]
    )
    d = diff_prompts(a, b)
    # B has extra emotion_tags section
    assert any("B only" in line and "sad" in line for line in d)


def test_route_hints_are_stable() -> None:
    for route in ("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"):
        p = build_emotional_prompt(persona="x", route=route)
        assert route in p.text


def test_output_is_deterministic() -> None:
    kwargs = dict(
        persona="你是贴心的数字人格",
        user_profile_prefix="profile:[0.1]",
        recent_memory=[{"summary": "a", "tags": []}],
        route="LIGHT_RECALL",
        emotion_tags=["sad"],
    )
    a = build_emotional_prompt(**kwargs)
    b = build_emotional_prompt(**kwargs)
    assert a.text == b.text
    assert a.sections == b.sections
