"""Coordination & Rhythm Expert — turn timing, guidance, cadence, and somatic plans.

Produces:
    - runtime_coordination_snapshot (L5, parallel with governance's rehearsal_result)
    - guidance_plan (L6)
    - conversation_cadence_plan (L7)
    - session_ritual_plan (L8)
    - somatic_orchestration_plan (L9)
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.coordination import (
    build_conversation_cadence_plan,
    build_guidance_plan,
    build_runtime_coordination_snapshot,
    build_session_ritual_plan,
    build_somatic_orchestration_plan,
)


def build_coordination_expert_plans(
    *,
    context_frame: Any,
    relationship_state: Any,
    repair_assessment: Any,
    confidence_assessment: Any,
    knowledge_boundary_decision: Any,
    policy_gate: Any,
    strategy_decision: Any,
    turn_index: int,
    session_age_seconds: float,
    idle_gap_seconds: float,
    user_message: str,
) -> dict[str, Any]:
    """Build plans from the coordination / rhythm domain.

    Returns
    -------
    dict with keys ``runtime_coordination_snapshot``, ``guidance_plan``,
    ``conversation_cadence_plan``, ``session_ritual_plan``,
    ``somatic_orchestration_plan``.
    """
    runtime_coordination_snapshot = build_runtime_coordination_snapshot(
        turn_index=turn_index,
        session_age_seconds=session_age_seconds,
        idle_gap_seconds=idle_gap_seconds,
        user_message=user_message,
        context_frame=context_frame,
        relationship_state=relationship_state,
        confidence_assessment=confidence_assessment,
        repair_assessment=repair_assessment,
        strategy_decision=strategy_decision,
    )

    guidance_plan = build_guidance_plan(
        context_frame=context_frame,
        repair_assessment=repair_assessment,
        confidence_assessment=confidence_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
    )

    conversation_cadence_plan = build_conversation_cadence_plan(
        context_frame=context_frame,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        guidance_plan=guidance_plan,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
    )

    session_ritual_plan = build_session_ritual_plan(
        context_frame=context_frame,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        guidance_plan=guidance_plan,
        cadence_plan=conversation_cadence_plan,
        repair_assessment=repair_assessment,
    )

    somatic_orchestration_plan = build_somatic_orchestration_plan(
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        guidance_plan=guidance_plan,
        cadence_plan=conversation_cadence_plan,
        session_ritual_plan=session_ritual_plan,
    )

    return {
        "runtime_coordination_snapshot": runtime_coordination_snapshot,
        "guidance_plan": guidance_plan,
        "conversation_cadence_plan": conversation_cadence_plan,
        "session_ritual_plan": session_ritual_plan,
        "somatic_orchestration_plan": somatic_orchestration_plan,
    }
