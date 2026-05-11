from types import SimpleNamespace

from relationship_os.application.runtime.reply_prompt_sections import (
    build_reply_drafting_lines,
    build_reply_guidance_lines,
    build_reply_rendering_lines,
)


def _analysis() -> SimpleNamespace:
    return SimpleNamespace(
        response_draft_plan=SimpleNamespace(
            opening_move="ack",
            structure=["one", "two"],
            must_include=["care"],
            must_avoid=["lecture"],
            phrasing_constraints=["plain"],
            question_strategy="optional",
        ),
        response_rendering_policy=SimpleNamespace(
            rendering_mode="friend",
            max_sentences=4,
            include_validation=True,
            include_next_step=False,
            include_boundary_statement=False,
            include_uncertainty_statement=True,
            question_count_limit=1,
            style_guardrails=["warm", "short"],
        ),
        guidance_plan=SimpleNamespace(
            mode="steady",
            lead_with="answer",
            pacing="slow",
            step_budget=1,
            agency_mode="user_led",
            ritual_action="none",
            checkpoint_style="light",
            handoff_mode="soft",
            carryover_mode="resume",
            micro_actions=["breathe", "start"],
        ),
        conversation_cadence_plan=SimpleNamespace(
            status="stable",
            turn_shape="short",
            followup_tempo="low",
            user_space_mode="open",
        ),
        session_ritual_plan=SimpleNamespace(
            phase="middle",
            opening_move="none",
            bridge_move="bridge",
            closing_move="none",
            somatic_shortcut="shoulders",
        ),
        somatic_orchestration_plan=SimpleNamespace(
            status="available",
            primary_mode="ground",
            body_anchor="feet",
            followup_style="gentle",
        ),
    )


def test_build_reply_drafting_and_rendering_lines_match_runtime_prompt_surface() -> None:
    analysis = _analysis()

    assert build_reply_drafting_lines(analysis) == [
        "- opening_move: ack",
        "- structure: one, two",
        "- must_include: care",
        "- must_avoid: lecture",
        "- phrasing_constraints: plain",
        "- question_strategy: optional",
    ]
    assert build_reply_rendering_lines(analysis) == [
        "- rendering_mode: friend",
        "- max_sentences: 4",
        "- include_validation: True",
        "- include_next_step: False",
        "- include_boundary_statement: False",
        "- include_uncertainty_statement: True",
        "- question_count_limit: 1",
        "- style_guardrails: warm, short",
    ]


def test_build_reply_guidance_lines_includes_cadence_ritual_and_somatic_context() -> None:
    assert build_reply_guidance_lines(_analysis()) == [
        "- mode: steady",
        "- lead_with: answer",
        "- pacing: slow",
        "- step_budget: 1",
        "- agency_mode: user_led",
        "- ritual_action: none",
        "- checkpoint_style: light",
        "- handoff_mode: soft",
        "- carryover_mode: resume",
        "- micro_actions: breathe, start",
        "- cadence_status: stable",
        "- cadence_turn_shape: short",
        "- cadence_followup_tempo: low",
        "- cadence_user_space_mode: open",
        "- ritual_phase: middle",
        "- ritual_opening_move: none",
        "- ritual_bridge_move: bridge",
        "- ritual_closing_move: none",
        "- ritual_somatic_shortcut: shoulders",
        "- somatic_orchestration_status: available",
        "- somatic_orchestration_mode: ground",
        "- somatic_orchestration_body_anchor: feet",
        "- somatic_orchestration_followup_style: gentle",
    ]
