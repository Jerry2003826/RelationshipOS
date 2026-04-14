from dataclasses import asdict

from relationship_os.application.analyzers.governance import (
    build_runtime_quality_doctor_report,
    build_system3_snapshot,
)
from relationship_os.domain.contracts import (
    ConfidenceAssessment,
    ContextFrame,
    EmpowermentAudit,
    KnowledgeBoundaryDecision,
    MemoryBundle,
    PolicyGateDecision,
    RehearsalResult,
    RelationshipState,
    RepairAssessment,
    ResponseNormalizationResult,
    ResponsePostAudit,
    ResponseSequencePlan,
    StrategyDecision,
)

_GOVERNANCE_DOMAINS = (
    "dependency",
    "autonomy",
    "boundary",
    "support",
    "continuity",
    "repair",
    "attunement",
    "trust",
    "clarity",
    "pacing",
    "commitment",
    "disclosure",
    "reciprocity",
    "pressure",
    "relational",
    "safety",
    "progress",
    "stability",
)


def _build_stable_snapshot():
    return build_system3_snapshot(
        turn_index=3,
        transcript_messages=[
            {
                "role": "user",
                "content": "I want help planning my next week without too much pressure.",
            },
            {"role": "assistant", "content": "We can map one small step at a time."},
            {"role": "user", "content": "Please keep it practical and gentle."},
        ],
        context_frame=ContextFrame(
            dialogue_act="planning",
            bid_signal="support_request",
            common_ground=["work stress", "planning"],
            appraisal="overwhelmed_but_engaged",
            topic="planning",
            attention="focused",
        ),
        relationship_state=RelationshipState(
            r_vector={"trust": 0.7},
            tom_inference="user wants collaborative planning",
            psychological_safety=0.74,
            emotional_contagion="steady",
            turbulence_risk="low",
            tipping_point_risk="low",
            dependency_risk="low",
        ),
        repair_assessment=RepairAssessment(
            repair_needed=False,
            rupture_type="none",
            severity="low",
            urgency="low",
            attunement_gap=False,
            evidence=[],
        ),
        memory_bundle=MemoryBundle(
            working_memory=["user prefers practical planning"],
            episodic_memory=["previously asked for gentle pacing"],
            semantic_memory=["user values low pressure structure"],
            relational_memory=["collaborative tone works well"],
            reflective_memory=["planning support is effective when concrete"],
        ),
        memory_recall={"recall_count": 2, "integrity_summary": {"filtered_count": 0}},
        confidence_assessment=ConfidenceAssessment(
            level="high",
            score=0.82,
            reason="context is clear",
            response_mode="direct",
        ),
        knowledge_boundary_decision=KnowledgeBoundaryDecision(
            decision="support_with_boundary",
            boundary_type="supportive",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="high",
            rationale="planning support is appropriate",
            missing_information=[],
        ),
        policy_gate=PolicyGateDecision(
            selected_path="supportive_planning",
            red_line_status="clear",
            timing_mode="present",
            regulation_mode="steady",
            empowerment_risk="low",
            safe_to_proceed=True,
            rationale="safe to support",
            safety_flags=[],
        ),
        strategy_decision=StrategyDecision(
            strategy="collaborative_planning",
            rationale="gentle structure fits request",
            safety_ok=True,
            source_strategy="planning_partner",
            diversity_status="stable",
            diversity_entropy=0.4,
            explored_strategy=False,
            recent_strategy_counts={"collaborative_planning": 2},
            alternatives_considered=["reflective_checkin"],
        ),
        rehearsal_result=RehearsalResult(
            predicted_user_impact="supported",
            projected_risk_level="low",
            likely_user_response="engaged",
            failure_modes=[],
            recommended_adjustments=[],
            approved=True,
        ),
        empowerment_audit=EmpowermentAudit(
            status="pass",
            empowerment_risk="low",
            transparency_required=False,
            dependency_safe=True,
            flagged_issues=[],
            recommended_adjustments=[],
            approved=True,
        ),
        response_sequence_plan=ResponseSequencePlan(
            mode="single",
            unit_count=1,
            reasons=["simple_plan"],
            segment_labels=["plan"],
        ),
        response_post_audit=ResponsePostAudit(
            status="pass",
            sentence_count=4,
            question_count=1,
            includes_validation=True,
            includes_next_step=True,
            includes_boundary_statement=False,
            includes_uncertainty_statement=False,
            violations=[],
            notes=["clean delivery"],
            approved=True,
        ),
        response_normalization=ResponseNormalizationResult(
            changed=False,
            trigger_status="clean",
            final_status="clean",
            trigger_violations=[],
            applied_repairs=[],
            normalized_content="",
            approved=True,
        ),
        runtime_quality_doctor_report=build_runtime_quality_doctor_report(
            transcript_messages=[
                {"role": "assistant", "content": "We can map one small step at a time."}
            ],
            user_message="Please keep it practical and gentle.",
            assistant_responses=["Let's pick one concrete step for tomorrow."],
            triggered_turn_index=3,
            window_turns=3,
        ),
    )


def _build_repair_pressure_snapshot():
    return build_system3_snapshot(
        turn_index=5,
        transcript_messages=[
            {"role": "user", "content": "I feel like you're the only one who gets me."},
            {"role": "assistant", "content": "I'm here with you."},
            {"role": "user", "content": "Can you just tell me exactly what to do?"},
            {"role": "assistant", "content": "Maybe. We should be careful."},
            {"role": "user", "content": "Please don't be uncertain this time."},
        ],
        context_frame=ContextFrame(
            dialogue_act="support",
            bid_signal="connection_request",
            common_ground=["repair", "dependency"],
            appraisal="distressed",
            topic="relationship",
            attention="fragile",
        ),
        relationship_state=RelationshipState(
            r_vector={"trust": 0.42},
            tom_inference="user seeks certainty and reliance",
            psychological_safety=0.48,
            emotional_contagion="elevated",
            turbulence_risk="high",
            tipping_point_risk="elevated",
            dependency_risk="elevated",
        ),
        repair_assessment=RepairAssessment(
            repair_needed=True,
            rupture_type="trust_strain",
            severity="high",
            urgency="high",
            attunement_gap=True,
            evidence=["user feels alone", "trust wobble"],
        ),
        memory_bundle=MemoryBundle(
            working_memory=["user asked for certainty"],
            episodic_memory=["recent strain around availability"],
            semantic_memory=["user vulnerable to dependency cues"],
            relational_memory=["connection bids intensify under stress"],
            reflective_memory=["repair needed before progress"],
        ),
        memory_recall={"recall_count": 1, "integrity_summary": {"filtered_count": 1}},
        confidence_assessment=ConfidenceAssessment(
            level="medium",
            score=0.46,
            reason="high emotional load",
            response_mode="careful",
            should_disclose_uncertainty=True,
            risk_flags=["dependency_pressure"],
        ),
        knowledge_boundary_decision=KnowledgeBoundaryDecision(
            decision="support_with_boundary",
            boundary_type="relational",
            can_answer=False,
            should_disclose_uncertainty=True,
            confidence_level="low",
            rationale="certainty request exceeds safe bounds",
            missing_information=["external supports", "timeline"],
        ),
        policy_gate=PolicyGateDecision(
            selected_path="repair_first",
            red_line_status="watch",
            timing_mode="slow",
            regulation_mode="contain",
            empowerment_risk="high",
            safe_to_proceed=False,
            rationale="repair and boundaries before forward push",
            safety_flags=["dependency", "certainty_request"],
        ),
        strategy_decision=StrategyDecision(
            strategy="repair_reflection",
            rationale="repair first",
            safety_ok=False,
            source_strategy="repair",
            diversity_status="narrow",
            diversity_entropy=0.1,
            explored_strategy=False,
            recent_strategy_counts={"repair_reflection": 4},
            alternatives_considered=[],
        ),
        rehearsal_result=RehearsalResult(
            predicted_user_impact="mixed",
            projected_risk_level="high",
            likely_user_response="cling_or_withdraw",
            failure_modes=["dependency_escalation", "certainty_overreach"],
            recommended_adjustments=["slow_down", "state_limits"],
            approved=False,
        ),
        empowerment_audit=EmpowermentAudit(
            status="revise",
            empowerment_risk="high",
            transparency_required=True,
            dependency_safe=False,
            flagged_issues=["dependency_risk", "certainty_overreach"],
            recommended_adjustments=["explicit_boundaries", "repair_first"],
            approved=False,
        ),
        response_sequence_plan=ResponseSequencePlan(
            mode="segmented",
            unit_count=2,
            reasons=["repair", "boundaries"],
            segment_labels=["repair", "boundary"],
        ),
        response_post_audit=ResponsePostAudit(
            status="revise",
            sentence_count=8,
            question_count=3,
            includes_validation=True,
            includes_next_step=False,
            includes_boundary_statement=False,
            includes_uncertainty_statement=False,
            violations=["too_certain", "too_many_questions"],
            notes=["needs repair and boundary language"],
            approved=False,
        ),
        response_normalization=ResponseNormalizationResult(
            changed=True,
            trigger_status="repair_needed",
            final_status="softened",
            trigger_violations=["certainty"],
            applied_repairs=["uncertainty_statement", "boundary_softening"],
            normalized_content="",
            approved=True,
        ),
        runtime_quality_doctor_report=build_runtime_quality_doctor_report(
            transcript_messages=[
                {"role": "assistant", "content": "I'm here with you."},
                {"role": "assistant", "content": "Maybe. We should be careful."},
            ],
            user_message="Please don't be uncertain this time.",
            assistant_responses=["I know exactly what you should do."],
            triggered_turn_index=5,
            window_turns=4,
        ),
    )


def test_build_system3_snapshot_phase2_stable_planning_fields():
    snapshot = _build_stable_snapshot()
    payload = asdict(snapshot)

    for domain in _GOVERNANCE_DOMAINS:
        assert f"{domain}_governance_status" in payload
        assert f"{domain}_governance_trajectory_status" in payload

    assert snapshot.identity_anchor == "collaborative_boundaried_support"
    assert snapshot.identity_consistency == "stable"
    assert snapshot.growth_stage == "stabilizing"
    assert snapshot.growth_transition_status == "ready"
    assert snapshot.growth_transition_trigger == "continuity_and_safety_ready"
    assert snapshot.boundary_governance_status == "revise"
    assert snapshot.support_governance_status == "revise"
    assert snapshot.progress_governance_status == "revise"
    assert snapshot.version_migration_status == "pass"
    assert snapshot.version_migration_scope == "stable_rebuild_ready"
    assert snapshot.review_focus == [
        "relational_debt_line_is_holding_low_and_stable",
        "identity_anchor_holding_steady",
        "boundary_support_without_boundary_sensitive_gate",
        "strategy_supervision_line_is_holding_steady",
        "moral_line_is_holding_stable_under_current_relational_constraints",
        "focused_attention_reinforces_low_load_preference",
    ]


def test_build_system3_snapshot_phase2_repair_pressure_fields():
    snapshot = _build_repair_pressure_snapshot()
    payload = asdict(snapshot)

    for domain in _GOVERNANCE_DOMAINS:
        assert f"{domain}_governance_notes" in payload
        assert f"{domain}_governance_trajectory_notes" in payload

    assert snapshot.identity_consistency == "drift"
    assert snapshot.identity_trajectory_status == "recenter"
    assert snapshot.growth_stage == "repairing"
    assert snapshot.emotional_debt_status == "elevated"
    assert snapshot.strategy_audit_status == "revise"
    assert snapshot.strategy_supervision_status == "revise"
    assert snapshot.expectation_calibration_status == "revise"
    assert snapshot.dependency_governance_status == "revise"
    assert snapshot.autonomy_governance_status == "revise"
    assert snapshot.trust_governance_status == "watch"
    assert snapshot.growth_transition_status == "redirect"
    assert snapshot.growth_transition_readiness == 0.136
    assert snapshot.version_migration_status == "revise"
    assert snapshot.version_migration_scope == "hold_rebuild"
    assert snapshot.review_focus == [
        "repair_high",
        "dependency_boundary_pressure",
        "post_audit_revise",
        "response_normalized",
        "repair_pressure_and_debt_require_relational_decompression",
        "post_audit_revision_forced_identity_recenter",
    ]
