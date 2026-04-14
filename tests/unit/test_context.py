"""Unit tests for context inference functions in analyzers."""

from __future__ import annotations

import pytest

from relationship_os.application.analyzers import (
    apply_semantic_hints,
    build_context_frame,
    infer_appraisal,
    infer_attention,
    infer_bid_signal,
    infer_dialogue_act,
    infer_topic,
)


class TestInferDialogueAct:
    """Tests for infer_dialogue_act."""

    def test_question_mark_returns_question(self) -> None:
        assert infer_dialogue_act("你能帮我吗？") == "question"

    def test_english_question_mark(self) -> None:
        assert infer_dialogue_act("Can you help me?") == "question"

    def test_request_chinese_keywords(self) -> None:
        assert infer_dialogue_act("请帮我看看这段代码") == "request"

    def test_request_english_keywords(self) -> None:
        assert infer_dialogue_act("I need help with deployment") == "request"

    def test_appreciation_chinese(self) -> None:
        assert infer_dialogue_act("谢谢你今天陪我") == "appreciation"

    def test_appreciation_english(self) -> None:
        assert infer_dialogue_act("thank you so much") == "appreciation"

    def test_default_disclosure(self) -> None:
        assert infer_dialogue_act("今天天气不错") == "disclosure"

    def test_empty_string(self) -> None:
        assert infer_dialogue_act("") == "disclosure"

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("what time is it?", "question"),
            ("帮我检查一下", "request"),
            ("thanks!", "appreciation"),
            ("我昨天去了公园", "disclosure"),
        ],
    )
    def test_varied_inputs(self, text: str, expected: str) -> None:
        assert infer_dialogue_act(text) == expected


class TestInferAppraisal:
    """Tests for infer_appraisal."""

    def test_negative_english(self) -> None:
        assert infer_appraisal("I feel stuck and anxious") == "negative"

    def test_negative_chinese(self) -> None:
        assert infer_appraisal("我很焦虑，压力很大") == "negative"

    def test_positive_english(self) -> None:
        assert infer_appraisal("Everything is great today") == "positive"

    def test_positive_chinese(self) -> None:
        assert infer_appraisal("今天很开心") == "positive"

    def test_neutral_default(self) -> None:
        assert infer_appraisal("我在写代码") == "neutral"

    def test_empty_string(self) -> None:
        assert infer_appraisal("") == "neutral"


class TestInferBidSignal:
    """Tests for infer_bid_signal."""

    def test_connection_request_english(self) -> None:
        assert infer_bid_signal("I feel alone and worried") == "connection_request"

    def test_connection_request_chinese(self) -> None:
        assert infer_bid_signal("我很孤独，有点担心") == "connection_request"

    def test_soft_bid(self) -> None:
        assert infer_bid_signal("I want to share an update") == "soft_bid"

    def test_low_signal_default(self) -> None:
        assert infer_bid_signal("ok") == "low_signal"


class TestInferTopic:
    """Tests for infer_topic."""

    def test_technical(self) -> None:
        assert infer_topic("there's a bug in the API") == "technical"

    def test_planning(self) -> None:
        assert infer_topic("let's plan the next phase") == "planning"

    def test_emotion_chinese(self) -> None:
        assert infer_topic("我最近情绪不太好") == "emotion"

    def test_general_default(self) -> None:
        assert infer_topic("hello") == "general"


class TestInferAttention:
    """Tests for infer_attention."""

    def test_high_urgent(self) -> None:
        assert infer_attention("this is urgent, please help asap") == "high"

    def test_high_long_text(self) -> None:
        assert infer_attention("x" * 200) == "high"

    def test_focused_medium_text(self) -> None:
        assert infer_attention("x" * 80) == "focused"

    def test_normal_short_text(self) -> None:
        assert infer_attention("hi") == "normal"


class TestBuildContextFrame:
    """Tests for build_context_frame."""

    def test_returns_context_frame_with_all_fields(self) -> None:
        frame = build_context_frame("我有点焦虑，想推进计划")
        assert frame.dialogue_act in {"question", "request", "appreciation", "disclosure"}
        assert frame.bid_signal in {"connection_request", "soft_bid", "low_signal"}
        assert frame.appraisal in {"positive", "negative", "neutral"}
        assert frame.topic in {
            "technical", "planning", "work", "relationship", "emotion", "general",
        }
        assert frame.attention in {"high", "focused", "normal"}
        assert isinstance(frame.common_ground, list)

    def test_chinese_text_adds_zh_common_ground(self) -> None:
        frame = build_context_frame("你好世界")
        assert "zh" in frame.common_ground

    def test_english_text_no_zh(self) -> None:
        frame = build_context_frame("hello world")
        assert "zh" not in frame.common_ground

    def test_topic_in_common_ground(self) -> None:
        frame = build_context_frame("let's plan the next phase")
        assert frame.topic in frame.common_ground


class TestApplySemanticHints:
    def test_promotes_probe_to_question_and_connection_request(self) -> None:
        frame = build_context_frame("我在写代码")
        updated = apply_semantic_hints(
            frame,
            intent_label="state_reflection_probe",
            appraisal="negative",
            emotional_load="high",
        )

        assert updated.dialogue_act == "question"
        assert updated.bid_signal == "connection_request"
        assert updated.appraisal == "negative"
        assert updated.attention == "focused"

    def test_social_probe_becomes_soft_bid(self) -> None:
        frame = build_context_frame("我在写代码")
        updated = apply_semantic_hints(
            frame,
            intent_label="social_disclosure",
            appraisal="neutral",
            emotional_load="low",
        )

        assert updated.dialogue_act == "question"
        assert updated.bid_signal == "soft_bid"
