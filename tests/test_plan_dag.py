"""Tests for the plan DAG executor and domain expert modules."""

from types import SimpleNamespace

from relationship_os.application.analyzers.experts import (
    build_coordination_expert_plans,
    build_emotional_expert_plans,
    build_expression_expert_plans,
    build_factual_expert_plans,
    build_governance_expert_plans,
    build_response_expert_plans,
    execute_plan_dag,
)
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    RelationshipState,
    RepairAssessment,
    RepairPlan,
)


def _make_minimal_foundation(**overrides):
    """Create a minimal _TurnFoundation-like object for testing."""
    defaults = {
        "context_frame": ContextFrame(
            dialogue_act="statement",
            bid_signal="low_signal",
            common_ground=["general"],
            appraisal="neutral",
            topic="general",
            attention="normal",
        ),
        "recalled_memory": [],
        "memory_recall": {"results": []},
        "entity_persona": {"persona_archetype": "default"},
        "entity_social_world": {},
        "conscience_assessment": {
            "mode": "withhold",
            "reason": "none",
            "disclosure_style": "hint",
            "dramatic_value": 0.0,
            "conscience_weight": 0.55,
            "source_user_ids": [],
        },
        "edge_runtime_plan": {},
        "relationship_state": RelationshipState(
            r_vector={},
            tom_inference="neutral",
            psychological_safety="moderate",
            emotional_contagion="none",
            turbulence_risk="low",
            tipping_point_risk="low",
            dependency_risk="low",
        ),
        "repair_assessment": RepairAssessment(
            repair_needed=False,
            rupture_type="none",
            severity="none",
            urgency="none",
            attunement_gap=0.0,
            evidence=[],
        ),
        "confidence_assessment": ConfidenceAssessment(
            level="moderate",
            score=0.7,
            reason="standard_turn",
            response_mode="standard",
            should_disclose_uncertainty=False,
            needs_clarification=False,
            risk_flags=[],
        ),
        "memory_bundle": SimpleNamespace(
            working_memory=[],
            episodic_memory=[],
            semantic_memory=[],
            relational_memory=[],
            reflective_memory=[],
        ),
        "memory_write_guard": {},
        "memory_retention_policy": {},
        "memory_forgetting": {},
        "repair_plan": RepairPlan(
            rupture_detected=False,
            rupture_type="none",
            urgency="none",
            recommended_actions=[],
        ),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_minimal_turn_context(**overrides):
    """Create a minimal _TurnContext-like object for testing."""
    defaults = {
        "session_id": "test-session",
        "user_id": "test-user",
        "turn_index": 1,
        "session_age_seconds": 60.0,
        "idle_gap_seconds": 10.0,
        "transcript_messages": [],
        "strategy_history": [],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── DAG executor tests ─────────────────────────────────────────────────


def test_execute_plan_dag_returns_all_14_fields():
    foundation = _make_minimal_foundation()
    turn_context = _make_minimal_turn_context()

    result = execute_plan_dag(
        foundation=foundation,
        turn_context=turn_context,
        user_message="Hello",
        runtime_profile="default",
    )

    expected_keys = {
        "knowledge_boundary_decision",
        "private_judgment",
        "policy_gate",
        "strategy_decision",
        "rehearsal_result",
        "expression_plan",
        "runtime_coordination_snapshot",
        "guidance_plan",
        "conversation_cadence_plan",
        "session_ritual_plan",
        "somatic_orchestration_plan",
        "empowerment_audit",
        "response_draft_plan",
        "response_rendering_policy",
    }
    assert set(result.keys()) == expected_keys


def test_execute_plan_dag_produces_typed_outputs():
    foundation = _make_minimal_foundation()
    turn_context = _make_minimal_turn_context()

    result = execute_plan_dag(
        foundation=foundation,
        turn_context=turn_context,
        user_message="How are you doing?",
        runtime_profile="default",
    )

    assert result["policy_gate"].selected_path is not None
    assert result["strategy_decision"].strategy is not None
    assert result["response_rendering_policy"].rendering_mode is not None


def test_execute_plan_dag_is_deterministic():
    foundation = _make_minimal_foundation()
    turn_context = _make_minimal_turn_context()

    result1 = execute_plan_dag(
        foundation=foundation,
        turn_context=turn_context,
        user_message="Hello",
        runtime_profile="default",
    )
    result2 = execute_plan_dag(
        foundation=foundation,
        turn_context=turn_context,
        user_message="Hello",
        runtime_profile="default",
    )

    for key in result1:
        assert result1[key] == result2[key], f"Non-deterministic output for {key}"


def test_execute_plan_dag_handles_empty_recalled_memory():
    foundation = _make_minimal_foundation(recalled_memory=[])
    turn_context = _make_minimal_turn_context()

    result = execute_plan_dag(
        foundation=foundation,
        turn_context=turn_context,
        user_message="What do you know?",
        runtime_profile="default",
    )

    assert result["knowledge_boundary_decision"] is not None


def test_execute_plan_dag_handles_high_severity_repair():
    foundation = _make_minimal_foundation(
        repair_assessment=RepairAssessment(
            repair_needed=True,
            rupture_type="withdrawal",
            severity="high",
            urgency="high",
            attunement_gap=0.8,
            evidence=["user expressed hurt"],
        ),
    )
    turn_context = _make_minimal_turn_context()

    result = execute_plan_dag(
        foundation=foundation,
        turn_context=turn_context,
        user_message="I feel like you don't care",
        runtime_profile="default",
    )

    assert result["knowledge_boundary_decision"] is not None


# ── Individual expert tests ─────────────────────────────────────────────


def test_factual_expert_returns_knowledge_boundary_decision():
    foundation = _make_minimal_foundation()
    result = build_factual_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        confidence_assessment=foundation.confidence_assessment,
        user_message="What's my dog's name?",
        recalled_memory=[],
    )
    assert "knowledge_boundary_decision" in result
    assert result["knowledge_boundary_decision"].decision is not None


def test_emotional_expert_returns_private_judgment():
    foundation = _make_minimal_foundation()
    result = build_emotional_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        repair_plan=foundation.repair_plan,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        memory_bundle=foundation.memory_bundle,
        confidence_assessment=foundation.confidence_assessment,
        recalled_memory=[],
    )
    assert "private_judgment" in result
    assert result["private_judgment"].summary is not None


def test_governance_expert_returns_three_plans():
    foundation = _make_minimal_foundation()
    result = build_governance_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        private_judgment=SimpleNamespace(
            summary="neutral",
            rationale="standard turn",
            confidence=0.7,
        ),
        strategy_history=[],
    )
    assert {"policy_gate", "strategy_decision", "rehearsal_result"} == set(result.keys())


def test_coordination_expert_returns_five_plans():
    foundation = _make_minimal_foundation()
    governance = build_governance_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        private_judgment=SimpleNamespace(
            summary="neutral",
            rationale="standard turn",
            confidence=0.7,
        ),
        strategy_history=[],
    )
    result = build_coordination_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        policy_gate=governance["policy_gate"],
        strategy_decision=governance["strategy_decision"],
        turn_index=1,
        session_age_seconds=60.0,
        idle_gap_seconds=10.0,
        user_message="Hello",
    )
    expected = {
        "runtime_coordination_snapshot",
        "guidance_plan",
        "conversation_cadence_plan",
        "session_ritual_plan",
        "somatic_orchestration_plan",
    }
    assert expected == set(result.keys())


def test_expression_expert_returns_two_plans():
    foundation = _make_minimal_foundation()
    result = build_expression_expert_plans(
        strategy_decision=SimpleNamespace(
            strategy="supportive",
            rationale="standard",
            safety_ok=True,
            source_strategy="default",
            diversity_status="acceptable",
            diversity_entropy=0.5,
            explored_strategy=None,
            recent_strategy_counts={},
            alternatives_considered=[],
        ),
        repair_plan=foundation.repair_plan,
        rehearsal_result=SimpleNamespace(
            predicted_user_impact="neutral",
            projected_risk_level="low",
            likely_user_response="neutral",
            failure_modes=[],
            recommended_adjustments=[],
            approved=True,
        ),
        policy_gate=SimpleNamespace(
            selected_path="standard",
            red_line_status="clear",
            timing_mode="normal",
            regulation_mode="standard",
            empowerment_risk="low",
            safe_to_proceed=True,
            rationale="standard",
            safety_flags=[],
        ),
        relationship_state=foundation.relationship_state,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        confidence_assessment=foundation.confidence_assessment,
    )
    assert {"expression_plan", "empowerment_audit"} == set(result.keys())


def test_response_expert_returns_two_plans():
    foundation = _make_minimal_foundation()
    # Build upstream plans via governance + expression experts
    governance = build_governance_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        private_judgment=SimpleNamespace(
            summary="neutral",
            rationale="standard turn",
            confidence=0.7,
        ),
        strategy_history=[],
    )
    coordination = build_coordination_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        policy_gate=governance["policy_gate"],
        strategy_decision=governance["strategy_decision"],
        turn_index=1,
        session_age_seconds=60.0,
        idle_gap_seconds=10.0,
        user_message="Hello",
    )
    expression = build_expression_expert_plans(
        strategy_decision=governance["strategy_decision"],
        repair_plan=foundation.repair_plan,
        rehearsal_result=governance["rehearsal_result"],
        policy_gate=governance["policy_gate"],
        relationship_state=foundation.relationship_state,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        confidence_assessment=foundation.confidence_assessment,
    )

    result = build_response_expert_plans(
        context_frame=foundation.context_frame,
        repair_plan=foundation.repair_plan,
        confidence_assessment=foundation.confidence_assessment,
        repair_assessment=foundation.repair_assessment,
        knowledge_boundary_decision=SimpleNamespace(
            decision="can_answer",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="moderate",
            rationale="standard",
            missing_information=[],
        ),
        policy_gate=governance["policy_gate"],
        expression_plan=expression["expression_plan"],
        rehearsal_result=governance["rehearsal_result"],
        empowerment_audit=expression["empowerment_audit"],
        runtime_coordination_snapshot=coordination["runtime_coordination_snapshot"],
        guidance_plan=coordination["guidance_plan"],
        conversation_cadence_plan=coordination["conversation_cadence_plan"],
        session_ritual_plan=coordination["session_ritual_plan"],
        somatic_orchestration_plan=coordination["somatic_orchestration_plan"],
        runtime_profile="default",
        entity_persona={"persona_archetype": "default"},
    )
    assert {"response_draft_plan", "response_rendering_policy"} == set(result.keys())
