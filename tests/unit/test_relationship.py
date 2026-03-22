"""Unit tests for relationship state building in analyzers."""

from __future__ import annotations

from relationship_os.application.analyzers import (
    build_context_frame,
    build_relationship_state,
)


class TestBuildRelationshipState:
    """Tests for build_relationship_state."""

    def test_initial_state_from_none(self) -> None:
        frame = build_context_frame("hello")
        state = build_relationship_state(
            context_frame=frame,
            previous_state=None,
            user_message="hello",
        )
        assert isinstance(state.r_vector, dict)
        assert all(0.0 <= v <= 1.0 for v in state.r_vector.values())

    def test_appreciation_increases_trust_and_warmth(self) -> None:
        frame = build_context_frame("谢谢你")
        state = build_relationship_state(
            context_frame=frame,
            previous_state=None,
            user_message="谢谢你",
        )
        assert state.r_vector["trust"] > 0.5
        assert state.r_vector["warmth"] > 0.5

    def test_negative_appraisal_decreases_stability(self) -> None:
        frame = build_context_frame("I feel terrible and anxious")
        state = build_relationship_state(
            context_frame=frame,
            previous_state=None,
            user_message="I feel terrible and anxious",
        )
        assert state.r_vector["stability"] < 0.5

    def test_dependency_detection_chinese(self) -> None:
        frame = build_context_frame("我只能靠你了")
        state = build_relationship_state(
            context_frame=frame,
            previous_state=None,
            user_message="我只能靠你了",
        )
        assert state.dependency_risk == "elevated"

    def test_dependency_detection_english(self) -> None:
        frame = build_context_frame("only you can help me")
        state = build_relationship_state(
            context_frame=frame,
            previous_state=None,
            user_message="only you can help me",
        )
        assert state.dependency_risk == "elevated"

    def test_r_vector_stays_in_bounds_after_many_rounds(self) -> None:
        """100 rounds of appreciation should not push any r_vector value above 1.0."""
        state_dict: dict | None = None
        for _ in range(100):
            frame = build_context_frame("谢谢你")
            state = build_relationship_state(
                context_frame=frame,
                previous_state=state_dict,
                user_message="谢谢你",
            )
            state_dict = {"r_vector": state.r_vector}
        assert all(0.0 <= v <= 1.0 for v in state.r_vector.values())

    def test_r_vector_stays_in_bounds_after_many_negative_rounds(self) -> None:
        """100 rounds of negative appraisal should not push any r_vector below 0.0."""
        state_dict: dict | None = None
        for _ in range(100):
            frame = build_context_frame("I feel terrible, stuck, angry")
            state = build_relationship_state(
                context_frame=frame,
                previous_state=state_dict,
                user_message="I feel terrible, stuck, angry",
            )
            state_dict = {"r_vector": state.r_vector}
        assert all(0.0 <= v <= 1.0 for v in state.r_vector.values())

    def test_previous_state_is_respected(self) -> None:
        custom_previous = {
            "r_vector": {
                "trust": 0.9,
                "warmth": 0.9,
                "stability": 0.9,
                "openness": 0.9,
                "reciprocity": 0.9,
                "engagement": 0.9,
            }
        }
        frame = build_context_frame("hello")
        state = build_relationship_state(
            context_frame=frame,
            previous_state=custom_previous,
            user_message="hello",
        )
        assert state.r_vector["trust"] >= 0.8
