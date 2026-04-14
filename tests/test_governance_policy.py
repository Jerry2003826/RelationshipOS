from types import SimpleNamespace

from relationship_os.domain.contracts import (
    ContextFrame,
    KnowledgeBoundaryDecision,
    MemoryBundle,
    PolicyGateDecision,
    RelationshipState,
    RepairAssessment,
    StrategyDecision,
)


def test_runtime_quality_doctor_uses_policy_thresholds(monkeypatch) -> None:
    from relationship_os.application.analyzers import governance as governance_module

    monkeypatch.setattr(
        governance_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "runtime_quality_doctor": {
                        "repetitive_openings_threshold": 4,
                        "revise_issue_count_threshold": 4,
                    }
                }
            }
        ),
    )

    report = governance_module.build_runtime_quality_doctor_report(
        transcript_messages=[
            {"role": "assistant", "content": "I hear you and I want to help."},
            {"role": "assistant", "content": "I hear you and I want to help."},
        ],
        user_message="Can you keep going?",
        assistant_responses=["I hear you and I want to help."],
        triggered_turn_index=3,
        window_turns=3,
    )

    assert "repetitive_openings" not in report.issues


def test_growth_user_context_uses_policy_thresholds(monkeypatch) -> None:
    from relationship_os.application.analyzers import governance as governance_module

    monkeypatch.setattr(
        governance_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "growth_user_context": {
                        "forming_turn_threshold": 0,
                        "stabilizing_turn_threshold": 1,
                        "deepening_psychological_safety_threshold": 0.6,
                        "deepening_min_recall_count": 0,
                    }
                }
            }
        ),
    )

    payload = governance_module._build_growth_user_context(
        turn_index=4,
        recent_user_text="Can we keep this gentle?",
        context_frame=ContextFrame(
            dialogue_act="support",
            bid_signal="connection_request",
            common_ground=[],
            appraisal="negative",
            topic="relationship",
            attention="focused",
        ),
        relationship_state=RelationshipState(
            r_vector={},
            tom_inference="",
            psychological_safety=0.65,
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
        confidence_assessment=SimpleNamespace(needs_clarification=False),
        response_sequence_plan=None,
        memory_bundle=MemoryBundle(
            working_memory=["prefers gentle pacing"],
            episodic_memory=[],
            semantic_memory=[],
            relational_memory=[],
            reflective_memory=[],
        ),
        recall_count=0,
        filtered_recall_count=0,
        emotional_debt_status="low",
    )

    assert payload["growth_stage"] == "deepening"


def test_strategy_audit_uses_policy_status_tables(monkeypatch) -> None:
    from relationship_os.application.analyzers import governance as governance_module

    monkeypatch.setattr(
        governance_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "strategy_audit": {
                        "watch_statuses": {
                            "empowerment": ["pass"],
                            "post_audit": ["review"],
                            "quality_doctor": ["watch"],
                            "emotional_debt": ["elevated"],
                            "rehearsal_risk": ["high"],
                        }
                    }
                }
            }
        ),
    )

    payload = governance_module._build_strategy_audit(
        repair_assessment=RepairAssessment(
            repair_needed=False,
            rupture_type="none",
            severity="low",
            urgency="low",
            attunement_gap=False,
            evidence=[],
        ),
        knowledge_boundary_decision=KnowledgeBoundaryDecision(
            decision="answer_directly",
            boundary_type="none",
            can_answer=True,
            should_disclose_uncertainty=False,
            confidence_level="high",
            rationale="",
            missing_information=[],
        ),
        policy_gate=PolicyGateDecision(
            selected_path="supportive_planning",
            red_line_status="clear",
            timing_mode="present",
            regulation_mode="steady",
            empowerment_risk="low",
            safe_to_proceed=True,
            rationale="",
            safety_flags=[],
        ),
        strategy_decision=StrategyDecision(
            strategy="collaborative_planning",
            rationale="",
            safety_ok=True,
            source_strategy="planning_partner",
            diversity_status="stable",
            diversity_entropy=0.1,
            explored_strategy=False,
            recent_strategy_counts={},
            alternatives_considered=[],
        ),
        rehearsal_result=SimpleNamespace(projected_risk_level="low"),
        empowerment_audit=SimpleNamespace(status="pass"),
        response_post_audit=None,
        runtime_quality_doctor_report=None,
        emotional_debt_status="low",
    )

    assert payload["strategy_audit_status"] == "watch"


def test_phase2_growth_transition_uses_policy_thresholds(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "growth_transition": {
                            "state_thresholds": {
                                "forming_ready_min_turn": 2,
                                "forming_ready_psychological_safety": 0.5,
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        emotional_debt_status="low",
        growth_stage="forming",
        turn_index=2,
        user_model_confidence=0.4,
        relationship_state=SimpleNamespace(
            psychological_safety=0.51,
            dependency_risk="low",
        ),
        recall_count=0,
        repair_assessment=SimpleNamespace(repair_needed=False),
        filtered_recall_count=0,
        user_model_evolution_status="pass",
    )

    outcome = phase2_module._build_growth_transition(prelude=prelude)
    assert outcome.status == "ready"
    assert outcome.target == "stabilizing"


def test_phase2_version_migration_uses_policy_thresholds(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "version_migration": {
                            "thin_history_turn_threshold": 1,
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        response_post_audit=None,
        runtime_quality_doctor_report=None,
        identity_trajectory_status="stable",
        user_model_evolution_status="pass",
        repair_assessment=SimpleNamespace(repair_needed=False),
        emotional_debt_status="low",
        filtered_recall_count=0,
        turn_index=2,
        recall_count=0,
        strategy_audit_status="pass",
    )
    growth_transition = SimpleNamespace(status="stable")

    outcome = phase2_module._build_version_migration(
        prelude=prelude,
        growth_transition=growth_transition,
    )
    assert outcome.status == "pass"
    assert outcome.scope == "stable_rebuild_ready"


def test_phase2_dependency_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "dependency": {
                                "branches": {
                                    "pass": {
                                        "target": "custom_low_dependency",
                                        "trigger": "custom_dependency_stable",
                                    }
                                },
                                "trajectory_branches": {
                                    "stable": {
                                        "target": "custom_low_dependency",
                                        "trigger": "custom_dependency_stable",
                                        "note": "custom dependency stable note",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        relationship_state=SimpleNamespace(dependency_risk="low"),
        knowledge_boundary_decision=SimpleNamespace(decision="answer_directly"),
        repair_assessment=SimpleNamespace(repair_needed=False),
        expectation_calibration_status="pass",
        expectation_calibration_target="steady",
        expectation_calibration_trigger="steady",
        emotional_debt_status="low",
    )

    outcome = phase2_module._build_dependency_governance(prelude=prelude)
    assert outcome.target == "custom_low_dependency"
    assert outcome.trigger == "custom_dependency_stable"
    assert "custom dependency stable note" in outcome.trajectory_notes


def test_phase2_support_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "support": {
                                "branches": {
                                    "watch_uncertainty": {
                                        "target": "custom_uncertain_support",
                                        "trigger": "custom_uncertainty_watch",
                                        "note": "custom uncertainty note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_uncertainty": {
                                        "target": "custom_uncertain_support",
                                        "trigger": "custom_uncertainty_watch",
                                        "note": "custom uncertainty trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        expectation_calibration_status="watch",
        repair_assessment=SimpleNamespace(repair_needed=False),
        policy_gate=SimpleNamespace(selected_path="supportive_planning"),
        confidence_assessment=SimpleNamespace(needs_clarification=False),
        knowledge_boundary_decision=SimpleNamespace(should_disclose_uncertainty=True),
        response_sequence_plan=None,
    )
    dependency = SimpleNamespace(status="pass")
    autonomy = SimpleNamespace(status="pass")
    boundary = SimpleNamespace(status="pass")

    outcome = phase2_module._build_support_governance(
        prelude=prelude,
        dependency=dependency,
        autonomy=autonomy,
        boundary=boundary,
    )
    assert outcome.target == "custom_uncertain_support"
    assert outcome.trigger == "custom_uncertainty_watch"
    assert "custom uncertainty note" in outcome.notes
    assert "custom uncertainty trajectory" in outcome.trajectory_notes


def test_phase2_continuity_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "continuity": {
                                "branches": {
                                    "watch_segmented": {
                                        "target": "custom_stepwise_continuity",
                                        "trigger": "custom_segmented_continuity_watch",
                                        "note": "custom segmented continuity note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_segmented": {
                                        "target": "custom_stepwise_continuity",
                                        "trigger": "custom_segmented_continuity_watch",
                                        "note": "custom segmented continuity trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        filtered_recall_count=0,
        user_model_evolution_status="pass",
        recall_count=3,
        turn_index=4,
        confidence_assessment=SimpleNamespace(needs_clarification=False),
        response_sequence_plan=SimpleNamespace(mode="two_part_sequence"),
    )
    support = SimpleNamespace(status="pass")

    outcome = phase2_module._build_continuity_governance(prelude=prelude, support=support)
    assert outcome.target == "custom_stepwise_continuity"
    assert outcome.trigger == "custom_segmented_continuity_watch"
    assert "custom segmented continuity note" in outcome.notes
    assert "custom segmented continuity trajectory" in outcome.trajectory_notes


def test_phase2_trust_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "trust": {
                                "branches": {
                                    "watch_turbulence": {
                                        "target": "custom_stabilizing_trust",
                                        "trigger": "custom_turbulence_trust_watch",
                                        "note": "custom turbulence trust note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_turbulence": {
                                        "target": "custom_stabilizing_trust",
                                        "trigger": "custom_turbulence_trust_watch",
                                        "note": "custom turbulence trust trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        policy_gate=SimpleNamespace(red_line_status="clear"),
        relationship_state=SimpleNamespace(psychological_safety=0.8, turbulence_risk="elevated"),
        repair_assessment=SimpleNamespace(repair_needed=False, severity="low"),
        emotional_debt_status="low",
    )
    repair = SimpleNamespace(status="pass")
    continuity = SimpleNamespace(status="pass")
    support = SimpleNamespace(status="pass")

    outcome = phase2_module._build_trust_governance(
        prelude=prelude,
        repair=repair,
        continuity=continuity,
        support=support,
    )
    assert outcome.target == "custom_stabilizing_trust"
    assert outcome.trigger == "custom_turbulence_trust_watch"
    assert "custom turbulence trust note" in outcome.notes
    assert "custom turbulence trust trajectory" in outcome.trajectory_notes


def test_phase2_clarity_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "clarity": {
                                "branches": {
                                    "watch_expectation": {
                                        "target": "custom_expectation_clarity",
                                        "trigger": "custom_expectation_clarity_watch",
                                        "note": "custom expectation clarity note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_expectation": {
                                        "target": "custom_expectation_clarity",
                                        "trigger": "custom_expectation_clarity_watch",
                                        "note": "custom expectation clarity trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        confidence_assessment=SimpleNamespace(needs_clarification=False),
        filtered_recall_count=0,
        knowledge_boundary_decision=SimpleNamespace(should_disclose_uncertainty=False),
        repair_assessment=SimpleNamespace(repair_needed=False, rupture_type="none"),
        expectation_calibration_status="watch",
        response_sequence_plan=None,
    )
    continuity = SimpleNamespace(status="pass")

    outcome = phase2_module._build_clarity_governance(prelude=prelude, continuity=continuity)
    assert outcome.target == "custom_expectation_clarity"
    assert outcome.trigger == "custom_expectation_clarity_watch"
    assert "custom expectation clarity note" in outcome.notes
    assert "custom expectation clarity trajectory" in outcome.trajectory_notes


def test_phase2_commitment_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "commitment": {
                                "branches": {
                                    "watch_pacing": {
                                        "target": "custom_slow_commitment",
                                        "trigger": "custom_pacing_commitment_watch",
                                        "note": "custom pacing commitment note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_pacing": {
                                        "target": "custom_slow_commitment",
                                        "trigger": "custom_pacing_commitment_watch",
                                        "note": "custom pacing commitment trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        expectation_calibration_status="pass",
        confidence_assessment=SimpleNamespace(needs_clarification=False),
        knowledge_boundary_decision=SimpleNamespace(should_disclose_uncertainty=False),
        repair_assessment=SimpleNamespace(repair_needed=False),
        response_sequence_plan=None,
        policy_gate=SimpleNamespace(selected_path="supportive_planning"),
    )
    boundary = SimpleNamespace(status="pass")
    autonomy = SimpleNamespace(status="pass")
    pacing = SimpleNamespace(status="watch")

    outcome = phase2_module._build_commitment_governance(
        prelude=prelude,
        boundary=boundary,
        autonomy=autonomy,
        pacing=pacing,
    )
    assert outcome.target == "custom_slow_commitment"
    assert outcome.trigger == "custom_pacing_commitment_watch"
    assert "custom pacing commitment note" in outcome.notes
    assert "custom pacing commitment trajectory" in outcome.trajectory_notes


def test_phase2_disclosure_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "disclosure": {
                                "branches": {
                                    "watch_commitment": {
                                        "target": "custom_softened_disclosure",
                                        "trigger": "custom_commitment_disclosure_watch",
                                        "note": "custom commitment disclosure note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_commitment": {
                                        "target": "custom_softened_disclosure",
                                        "trigger": "custom_commitment_disclosure_watch",
                                        "note": "custom commitment disclosure trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        filtered_recall_count=0,
        confidence_assessment=SimpleNamespace(needs_clarification=False),
        knowledge_boundary_decision=SimpleNamespace(should_disclose_uncertainty=False),
        response_sequence_plan=None,
    )
    boundary = SimpleNamespace(status="pass")
    clarity = SimpleNamespace(status="pass")
    commitment = SimpleNamespace(status="watch")

    outcome = phase2_module._build_disclosure_governance(
        prelude=prelude,
        boundary=boundary,
        clarity=clarity,
        commitment=commitment,
    )
    assert outcome.target == "custom_softened_disclosure"
    assert outcome.trigger == "custom_commitment_disclosure_watch"
    assert "custom commitment disclosure note" in outcome.notes
    assert "custom commitment disclosure trajectory" in outcome.trajectory_notes


def test_phase2_reciprocity_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "reciprocity": {
                                "branches": {
                                    "watch_commitment": {
                                        "target": "custom_bounded_reciprocity",
                                        "trigger": "custom_commitment_reciprocity_watch",
                                        "note": "custom commitment reciprocity note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_commitment": {
                                        "target": "custom_bounded_reciprocity",
                                        "trigger": "custom_commitment_reciprocity_watch",
                                        "note": "custom commitment reciprocity trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        relationship_state=SimpleNamespace(r_vector={"reciprocity": 0.6}),
        emotional_debt_status="low",
        expectation_calibration_status="pass",
        response_sequence_plan=None,
    )
    dependency = SimpleNamespace(status="pass")
    support = SimpleNamespace(status="pass")
    autonomy = SimpleNamespace(status="pass")
    commitment = SimpleNamespace(status="watch")

    outcome = phase2_module._build_reciprocity_governance(
        prelude=prelude,
        dependency=dependency,
        support=support,
        autonomy=autonomy,
        commitment=commitment,
    )
    assert outcome.target == "custom_bounded_reciprocity"
    assert outcome.trigger == "custom_commitment_reciprocity_watch"
    assert "custom commitment reciprocity note" in outcome.notes
    assert "custom commitment reciprocity trajectory" in outcome.trajectory_notes


def test_phase2_pressure_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "pressure": {
                                "branches": {
                                    "watch_attunement": {
                                        "target": "custom_attuned_pressure",
                                        "trigger": "custom_attunement_pressure_watch",
                                        "note": "custom attunement pressure note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_attunement": {
                                        "target": "custom_attuned_pressure",
                                        "trigger": "custom_attunement_pressure_watch",
                                        "note": "custom attunement pressure trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    prelude = SimpleNamespace(
        emotional_debt_status="low",
        response_sequence_plan=None,
    )
    repair = SimpleNamespace(status="pass")
    dependency = SimpleNamespace(status="pass")
    autonomy = SimpleNamespace(status="pass")
    boundary = SimpleNamespace(status="pass")
    pacing = SimpleNamespace(status="pass")
    support = SimpleNamespace(status="pass")
    attunement = SimpleNamespace(status="watch")
    trust = SimpleNamespace(status="pass")
    commitment = SimpleNamespace(status="pass")

    outcome = phase2_module._build_pressure_governance(
        prelude=prelude,
        repair=repair,
        dependency=dependency,
        autonomy=autonomy,
        boundary=boundary,
        pacing=pacing,
        support=support,
        attunement=attunement,
        trust=trust,
        commitment=commitment,
    )
    assert outcome.target == "custom_attuned_pressure"
    assert outcome.trigger == "custom_attunement_pressure_watch"
    assert "custom attunement pressure note" in outcome.notes
    assert "custom attunement pressure trajectory" in outcome.trajectory_notes


def test_phase2_relational_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "relational": {
                                "branches": {
                                    "watch_trust": {
                                        "target": "custom_trust_relational_watch",
                                        "trigger": "custom_trust_relational_watch",
                                        "note": "custom trust relational note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_trust": {
                                        "target": "custom_trust_relational_watch",
                                        "trigger": "custom_trust_relational_watch",
                                        "note": "custom trust relational trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    outcome = phase2_module._build_relational_governance(
        support=SimpleNamespace(status="pass"),
        continuity=SimpleNamespace(status="pass"),
        repair=SimpleNamespace(status="pass"),
        trust=SimpleNamespace(status="watch"),
        clarity=SimpleNamespace(status="pass"),
        pacing=SimpleNamespace(status="pass"),
        commitment=SimpleNamespace(status="pass"),
        disclosure=SimpleNamespace(status="pass"),
        reciprocity=SimpleNamespace(status="pass"),
        pressure=SimpleNamespace(status="pass"),
        boundary=SimpleNamespace(status="pass"),
    )

    assert outcome.target == "custom_trust_relational_watch"
    assert outcome.trigger == "custom_trust_relational_watch"
    assert "custom trust relational note" in outcome.notes
    assert "custom trust relational trajectory" in outcome.trajectory_notes


def test_phase2_safety_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "safety": {
                                "branches": {
                                    "watch_boundary": {
                                        "target": "custom_boundary_safety_watch",
                                        "trigger": "custom_boundary_safety_watch",
                                        "note": "custom boundary safety note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_boundary": {
                                        "target": "custom_boundary_safety_watch",
                                        "trigger": "custom_boundary_safety_watch",
                                        "note": "custom boundary safety trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    outcome = phase2_module._build_safety_governance(
        boundary=SimpleNamespace(status="watch"),
        trust=SimpleNamespace(status="pass"),
        clarity=SimpleNamespace(status="pass"),
        disclosure=SimpleNamespace(status="pass"),
        pressure=SimpleNamespace(status="pass"),
        continuity=SimpleNamespace(status="pass"),
        repair=SimpleNamespace(status="pass"),
        relational=SimpleNamespace(status="pass"),
    )

    assert outcome.target == "custom_boundary_safety_watch"
    assert outcome.trigger == "custom_boundary_safety_watch"
    assert "custom boundary safety note" in outcome.notes
    assert "custom boundary safety trajectory" in outcome.trajectory_notes


def test_phase2_stability_governance_uses_policy_branches(monkeypatch) -> None:
    from relationship_os.application.analyzers import _governance_phase2 as phase2_module

    monkeypatch.setattr(
        phase2_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "governance": {
                    "phase2": {
                        "governance_lines": {
                            "stability": {
                                "branches": {
                                    "watch_progress": {
                                        "target": "custom_progress_stability_watch",
                                        "trigger": "custom_progress_stability_watch",
                                        "note": "custom progress stability note",
                                    }
                                },
                                "trajectory_branches": {
                                    "watch_progress": {
                                        "target": "custom_progress_stability_watch",
                                        "trigger": "custom_progress_stability_watch",
                                        "note": "custom progress stability trajectory",
                                    }
                                },
                            }
                        }
                    }
                }
            }
        ),
    )

    outcome = phase2_module._build_stability_governance(
        safety=SimpleNamespace(status="pass"),
        relational=SimpleNamespace(status="pass"),
        pressure=SimpleNamespace(status="pass"),
        trust=SimpleNamespace(status="pass"),
        continuity=SimpleNamespace(status="pass"),
        repair=SimpleNamespace(status="pass"),
        progress=SimpleNamespace(status="watch"),
        pacing=SimpleNamespace(status="pass"),
        attunement=SimpleNamespace(status="pass"),
    )

    assert outcome.target == "custom_progress_stability_watch"
    assert outcome.trigger == "custom_progress_stability_watch"
    assert "custom progress stability note" in outcome.notes
    assert "custom progress stability trajectory" in outcome.trajectory_notes
