"""Response Expert — draft plan and rendering policy (final fan-in).

Produces:
    - response_draft_plan (L10, aggregates 10 upstream plans)
    - response_rendering_policy (L11)
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.response import (
    build_response_draft_plan,
    build_response_rendering_policy,
)


def build_response_expert_plans(
    *,
    context_frame: Any,
    repair_plan: Any,
    confidence_assessment: Any,
    repair_assessment: Any,
    knowledge_boundary_decision: Any,
    policy_gate: Any,
    expression_plan: Any,
    rehearsal_result: Any,
    empowerment_audit: Any,
    runtime_coordination_snapshot: Any,
    guidance_plan: Any,
    conversation_cadence_plan: Any,
    session_ritual_plan: Any,
    somatic_orchestration_plan: Any,
    runtime_profile: Any,
    entity_persona: dict[str, Any],
) -> dict[str, Any]:
    """Build plans from the response domain (final fan-in).

    Returns
    -------
    dict with keys ``response_draft_plan``, ``response_rendering_policy``.
    """
    response_draft_plan = build_response_draft_plan(
        context_frame=context_frame,
        policy_gate=policy_gate,
        repair_plan=repair_plan,
        confidence_assessment=confidence_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        expression_plan=expression_plan,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        guidance_plan=guidance_plan,
        cadence_plan=conversation_cadence_plan,
        session_ritual_plan=session_ritual_plan,
        somatic_orchestration_plan=somatic_orchestration_plan,
    )

    response_rendering_policy = build_response_rendering_policy(
        context_frame=context_frame,
        confidence_assessment=confidence_assessment,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        response_draft_plan=response_draft_plan,
        empowerment_audit=empowerment_audit,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        runtime_profile=runtime_profile,
        archetype=str(
            entity_persona.get("persona_archetype", "default") or "default"
        ),
    )

    return {
        "response_draft_plan": response_draft_plan,
        "response_rendering_policy": response_rendering_policy,
    }
