from __future__ import annotations

from typing import Any


def build_reply_drafting_lines(analysis: Any) -> list[str]:
    return [
        f"- opening_move: {analysis.response_draft_plan.opening_move}",
        f"- structure: {', '.join(analysis.response_draft_plan.structure)}",
        f"- must_include: {', '.join(analysis.response_draft_plan.must_include)}",
        f"- must_avoid: {', '.join(analysis.response_draft_plan.must_avoid)}",
        "- phrasing_constraints: " + ", ".join(analysis.response_draft_plan.phrasing_constraints),
        f"- question_strategy: {analysis.response_draft_plan.question_strategy}",
    ]


def build_reply_rendering_lines(analysis: Any) -> list[str]:
    return [
        f"- rendering_mode: {analysis.response_rendering_policy.rendering_mode}",
        f"- max_sentences: {analysis.response_rendering_policy.max_sentences}",
        f"- include_validation: {analysis.response_rendering_policy.include_validation}",
        f"- include_next_step: {analysis.response_rendering_policy.include_next_step}",
        (
            "- include_boundary_statement: "
            f"{analysis.response_rendering_policy.include_boundary_statement}"
        ),
        (
            "- include_uncertainty_statement: "
            f"{analysis.response_rendering_policy.include_uncertainty_statement}"
        ),
        f"- question_count_limit: {analysis.response_rendering_policy.question_count_limit}",
        "- style_guardrails: " + ", ".join(analysis.response_rendering_policy.style_guardrails),
    ]


def build_reply_guidance_lines(analysis: Any) -> list[str]:
    return [
        f"- mode: {analysis.guidance_plan.mode}",
        f"- lead_with: {analysis.guidance_plan.lead_with}",
        f"- pacing: {analysis.guidance_plan.pacing}",
        f"- step_budget: {analysis.guidance_plan.step_budget}",
        f"- agency_mode: {analysis.guidance_plan.agency_mode}",
        f"- ritual_action: {analysis.guidance_plan.ritual_action}",
        f"- checkpoint_style: {analysis.guidance_plan.checkpoint_style}",
        f"- handoff_mode: {analysis.guidance_plan.handoff_mode}",
        f"- carryover_mode: {analysis.guidance_plan.carryover_mode}",
        f"- micro_actions: {', '.join(analysis.guidance_plan.micro_actions)}",
        f"- cadence_status: {analysis.conversation_cadence_plan.status}",
        f"- cadence_turn_shape: {analysis.conversation_cadence_plan.turn_shape}",
        f"- cadence_followup_tempo: {analysis.conversation_cadence_plan.followup_tempo}",
        f"- cadence_user_space_mode: {analysis.conversation_cadence_plan.user_space_mode}",
        f"- ritual_phase: {analysis.session_ritual_plan.phase}",
        f"- ritual_opening_move: {analysis.session_ritual_plan.opening_move}",
        f"- ritual_bridge_move: {analysis.session_ritual_plan.bridge_move}",
        f"- ritual_closing_move: {analysis.session_ritual_plan.closing_move}",
        f"- ritual_somatic_shortcut: {analysis.session_ritual_plan.somatic_shortcut}",
        f"- somatic_orchestration_status: {analysis.somatic_orchestration_plan.status}",
        f"- somatic_orchestration_mode: {analysis.somatic_orchestration_plan.primary_mode}",
        (
            "- somatic_orchestration_body_anchor: "
            f"{analysis.somatic_orchestration_plan.body_anchor}"
        ),
        (
            "- somatic_orchestration_followup_style: "
            f"{analysis.somatic_orchestration_plan.followup_style}"
        ),
    ]
