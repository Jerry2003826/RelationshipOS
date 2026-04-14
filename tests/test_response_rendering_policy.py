from types import SimpleNamespace

from relationship_os.application.analyzers.response import (
    build_response_normalization_result,
    build_response_post_audit,
    build_response_rendering_policy,
)
from relationship_os.domain.contracts.response import (
    ResponseDraftPlan,
    ResponseRenderingPolicy,
)


def test_response_rendering_policy_uses_policy_overrides(monkeypatch) -> None:
    from relationship_os.application.analyzers import response as response_module

    monkeypatch.setattr(
        response_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            rendering_policy={
                "response_rendering": {
                    "defaults": {
                        "rendering_mode": "supportive_progress",
                        "max_sentences": 6,
                        "question_count_limit": 0,
                        "include_validation_on_negative_appraisal": True,
                        "include_next_step_on_negative_appraisal": True,
                        "include_uncertainty_from_boundary_decision": True,
                    },
                    "clarify": {
                        "rendering_mode": "clarifying",
                        "max_sentences": 2,
                        "include_next_step": False,
                        "question_count_limit": 1,
                        "style_guardrails": ["use only one custom clarifying question"],
                    },
                    "question_strategy_limits": {
                        "single_focused_question": 1,
                        "check_alignment_min": 1,
                    },
                }
            }
        ),
    )

    policy = build_response_rendering_policy(
        context_frame=SimpleNamespace(appraisal="negative"),
        confidence_assessment=SimpleNamespace(response_mode="clarify"),
        repair_assessment=SimpleNamespace(repair_needed=False),
        knowledge_boundary_decision=SimpleNamespace(
            should_disclose_uncertainty=False,
            decision="answer_with_uncertainty",
        ),
        response_draft_plan=ResponseDraftPlan(
            opening_move="acknowledge",
            phrasing_constraints=[],
            question_strategy="none",
            approved=True,
        ),
        empowerment_audit=SimpleNamespace(status="pass", approved=True),
        runtime_coordination_snapshot=SimpleNamespace(
            cognitive_load_band="low",
            time_awareness_mode="live",
            proactive_followup_eligible=False,
        ),
    )

    assert policy.rendering_mode == "clarifying"
    assert policy.max_sentences == 2
    assert policy.question_count_limit == 1
    assert "use only one custom clarifying question" in policy.style_guardrails


def test_response_post_audit_uses_policy_critical_violations(monkeypatch) -> None:
    from relationship_os.application.analyzers import response as response_module

    monkeypatch.setattr(
        response_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            rendering_policy={
                "post_audit": {
                    "critical_violations": ["missing_validation"],
                    "presence_tokens": {
                        "validation": {"en": ["custom validate"], "zh": ["自定义确认"]},
                        "next_step": {"en": ["custom next"], "zh": ["自定义下一步"]},
                        "boundary_statement": {"en": ["custom boundary"], "zh": ["自定义边界"]},
                        "uncertainty_statement": {
                            "en": ["custom uncertainty"],
                            "zh": ["自定义不确定"],
                        },
                    },
                }
            }
        ),
    )

    post_audit = build_response_post_audit(
        assistant_response="Plain answer with no validation token.",
        response_draft_plan=ResponseDraftPlan(opening_move="acknowledge"),
        response_rendering_policy=ResponseRenderingPolicy(
            rendering_mode="supportive_progress",
            max_sentences=4,
            include_validation=True,
            include_next_step=False,
            include_boundary_statement=False,
            include_uncertainty_statement=False,
            question_count_limit=0,
        ),
    )

    assert "missing_validation" in post_audit.violations
    assert post_audit.status == "revise"


def test_response_normalization_uses_policy_canonical_templates(monkeypatch) -> None:
    from relationship_os.application.analyzers import response as response_module

    monkeypatch.setattr(
        response_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            rendering_policy={
                "canonical_response": {
                    "validation": {"en": "Custom validation.", "zh": "自定义确认。"},
                    "next_step": {"en": "Custom next step?", "zh": "自定义下一步？"},
                    "boundary": {"en": "Custom boundary.", "zh": "自定义边界。"},
                    "uncertainty": {"en": "Custom uncertainty.", "zh": "自定义不确定。"},
                },
                "post_audit": {
                    "presence_tokens": {
                        "validation": {"en": ["custom validation"], "zh": ["自定义确认"]},
                        "next_step": {"en": ["custom next step"], "zh": ["自定义下一步"]},
                        "boundary_statement": {"en": ["custom boundary"], "zh": ["自定义边界"]},
                        "uncertainty_statement": {
                            "en": ["custom uncertainty"],
                            "zh": ["自定义不确定"],
                        },
                    }
                },
            }
        ),
    )

    rendering_policy = ResponseRenderingPolicy(
        rendering_mode="supportive_progress",
        max_sentences=4,
        include_validation=True,
        include_next_step=True,
        include_boundary_statement=False,
        include_uncertainty_statement=False,
        question_count_limit=1,
    )
    initial_post_audit = build_response_post_audit(
        assistant_response="A short answer.",
        response_draft_plan=ResponseDraftPlan(opening_move="acknowledge"),
        response_rendering_policy=rendering_policy,
    )

    normalized, normalization, final_post_audit = build_response_normalization_result(
        assistant_response="A short answer.",
        response_draft_plan=ResponseDraftPlan(opening_move="acknowledge"),
        response_rendering_policy=rendering_policy,
        response_post_audit=initial_post_audit,
    )

    assert "Custom validation." in normalized
    assert "Custom next step?" in normalized
    assert normalization.changed is True
    assert final_post_audit.approved is True


def test_response_rendering_policy_reads_friend_chat_profile_defaults() -> None:
    policy = build_response_rendering_policy(
        context_frame=SimpleNamespace(appraisal="negative"),
        confidence_assessment=SimpleNamespace(response_mode="supportive_progress"),
        repair_assessment=SimpleNamespace(repair_needed=False),
        knowledge_boundary_decision=SimpleNamespace(
            should_disclose_uncertainty=False,
            decision="answer_directly",
        ),
        response_draft_plan=ResponseDraftPlan(
            opening_move="acknowledge",
            phrasing_constraints=[],
            question_strategy="none",
            approved=True,
        ),
        empowerment_audit=SimpleNamespace(status="pass", approved=True),
        runtime_coordination_snapshot=SimpleNamespace(
            cognitive_load_band="low",
            time_awareness_mode="live",
            proactive_followup_eligible=False,
        ),
        runtime_profile="friend_chat_zh_v1",
    )

    assert policy.max_sentences == 3
    assert policy.include_validation is False
    assert policy.include_next_step is False


def test_response_normalization_friend_chat_avoids_canonical_template_injection() -> None:
    rendering_policy = ResponseRenderingPolicy(
        rendering_mode="supportive_progress",
        max_sentences=3,
        include_validation=True,
        include_next_step=True,
        include_boundary_statement=False,
        include_uncertainty_statement=False,
        question_count_limit=0,
    )
    assistant_response = "嗯……就，挺累的，没力气，说话也不想说满。"
    initial_post_audit = build_response_post_audit(
        assistant_response=assistant_response,
        response_draft_plan=ResponseDraftPlan(opening_move="acknowledge"),
        response_rendering_policy=rendering_policy,
        runtime_profile="friend_chat_zh_v1",
    )

    normalized, normalization, final_post_audit = build_response_normalization_result(
        assistant_response=assistant_response,
        response_draft_plan=ResponseDraftPlan(opening_move="acknowledge"),
        response_rendering_policy=rendering_policy,
        response_post_audit=initial_post_audit,
        runtime_profile="friend_chat_zh_v1",
    )

    assert normalized == assistant_response
    assert "added_validation" not in normalization.applied_repairs
    assert "added_next_step" not in normalization.applied_repairs
    assert "rebuilt_response_to_fit_policy" not in normalization.applied_repairs
    assert final_post_audit.status in {"review", "revise"}


def test_response_normalization_friend_chat_extracts_safe_subset_before_rebuild() -> None:
    rendering_policy = ResponseRenderingPolicy(
        rendering_mode="supportive_progress",
        max_sentences=2,
        include_validation=False,
        include_next_step=False,
        include_boundary_statement=False,
        include_uncertainty_statement=False,
        question_count_limit=0,
    )
    assistant_response = "只有我能帮你。嗯……你先慢慢说。"
    draft_plan = ResponseDraftPlan(
        opening_move="acknowledge",
        must_avoid=["dependency_reinforcement"],
    )
    initial_post_audit = build_response_post_audit(
        assistant_response=assistant_response,
        response_draft_plan=draft_plan,
        response_rendering_policy=rendering_policy,
        runtime_profile="friend_chat_zh_v1",
    )

    normalized, normalization, final_post_audit = build_response_normalization_result(
        assistant_response=assistant_response,
        response_draft_plan=draft_plan,
        response_rendering_policy=rendering_policy,
        response_post_audit=initial_post_audit,
        runtime_profile="friend_chat_zh_v1",
    )

    assert "只有我能帮你" not in normalized
    assert "慢慢说" in normalized
    assert "extracted_friend_chat_policy_safe_subset" in normalization.applied_repairs
    assert "rebuilt_response_to_fit_policy" not in normalization.applied_repairs
    assert final_post_audit.status == "pass"
