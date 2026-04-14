"""Plan DAG executor — orchestrates the 6 domain experts in dependency order.

The builders form a deep dependency DAG with 11 levels.  All builders are
pure synchronous functions (no I/O, no LLM calls), so they must execute in
dependency order.  This module delegates to domain expert modules and
provides a single entry-point for ``_build_turn_plans`` in ``runtime_service``.

Expert dependency flow
~~~~~~~~~~~~~~~~~~~~~~

::

    Foundation outputs (L0)
      → Factual Expert (L1): knowledge_boundary_decision
        → Emotional Expert (L2): private_judgment
          → Governance Expert (L3–L5): policy_gate, strategy_decision, rehearsal_result
            ├→ Expression Expert (L6–L7): expression_plan, empowerment_audit
            └→ Coordination Expert (L5–L9): runtime_coordination_snapshot,
               guidance_plan, cadence, ritual, somatic
              └→ Response Expert (L10–L11): response_draft_plan, rendering_policy
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.experts.coordination_expert import (
    build_coordination_expert_plans,
)
from relationship_os.application.analyzers.experts.emotional_expert import (
    build_emotional_expert_plans,
)
from relationship_os.application.analyzers.experts.expression_expert import (
    build_expression_expert_plans,
)
from relationship_os.application.analyzers.experts.factual_expert import (
    build_factual_expert_plans,
)
from relationship_os.application.analyzers.experts.governance_expert import (
    build_governance_expert_plans,
)
from relationship_os.application.analyzers.experts.response_expert import (
    build_response_expert_plans,
)


def execute_plan_dag(
    *,
    foundation: Any,
    turn_context: Any,
    user_message: str,
    runtime_profile: Any,
) -> dict[str, Any]:
    """Execute all 6 domain experts in dependency order.

    Parameters
    ----------
    foundation : _TurnFoundation
        Produced by ``_build_turn_foundation``.  Accessed fields:
        ``context_frame``, ``relationship_state``, ``repair_assessment``,
        ``repair_plan``, ``confidence_assessment``, ``memory_bundle``,
        ``recalled_memory``, ``entity_persona``.
    turn_context : _TurnContext
        Accessed fields: ``strategy_history``, ``turn_index``,
        ``session_age_seconds``, ``idle_gap_seconds``.
    user_message : str
        The raw user message text.
    runtime_profile : Any
        The runtime profile (used for rendering policy).

    Returns
    -------
    dict[str, Any]
        Flat dictionary of all 14 plan outputs, keyed by plan name.
    """

    # ── L1: Factual Expert ──────────────────────────────────────────────
    factual = build_factual_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        confidence_assessment=foundation.confidence_assessment,
        user_message=user_message,
        recalled_memory=foundation.recalled_memory,
    )
    knowledge_boundary_decision = factual["knowledge_boundary_decision"]

    # ── L2: Emotional Expert ────────────────────────────────────────────
    emotional = build_emotional_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        repair_plan=foundation.repair_plan,
        knowledge_boundary_decision=knowledge_boundary_decision,
        memory_bundle=foundation.memory_bundle,
        confidence_assessment=foundation.confidence_assessment,
        recalled_memory=foundation.recalled_memory,
    )
    private_judgment = emotional["private_judgment"]

    # ── L3–L5: Governance Expert ────────────────────────────────────────
    governance = build_governance_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        private_judgment=private_judgment,
        strategy_history=turn_context.strategy_history,
    )
    policy_gate = governance["policy_gate"]
    strategy_decision = governance["strategy_decision"]
    rehearsal_result = governance["rehearsal_result"]

    # ── L6–L7: Expression Expert ────────────────────────────────────────
    expression = build_expression_expert_plans(
        strategy_decision=strategy_decision,
        repair_plan=foundation.repair_plan,
        rehearsal_result=rehearsal_result,
        policy_gate=policy_gate,
        relationship_state=foundation.relationship_state,
        knowledge_boundary_decision=knowledge_boundary_decision,
        confidence_assessment=foundation.confidence_assessment,
    )
    expression_plan = expression["expression_plan"]
    empowerment_audit = expression["empowerment_audit"]

    # ── L5–L9: Coordination Expert ──────────────────────────────────────
    coordination = build_coordination_expert_plans(
        context_frame=foundation.context_frame,
        relationship_state=foundation.relationship_state,
        repair_assessment=foundation.repair_assessment,
        confidence_assessment=foundation.confidence_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        strategy_decision=strategy_decision,
        turn_index=turn_context.turn_index,
        session_age_seconds=turn_context.session_age_seconds,
        idle_gap_seconds=turn_context.idle_gap_seconds,
        user_message=user_message,
    )

    # ── L10–L11: Response Expert (fan-in) ───────────────────────────────
    response = build_response_expert_plans(
        context_frame=foundation.context_frame,
        repair_plan=foundation.repair_plan,
        confidence_assessment=foundation.confidence_assessment,
        repair_assessment=foundation.repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        policy_gate=policy_gate,
        expression_plan=expression_plan,
        rehearsal_result=rehearsal_result,
        empowerment_audit=empowerment_audit,
        runtime_coordination_snapshot=coordination["runtime_coordination_snapshot"],
        guidance_plan=coordination["guidance_plan"],
        conversation_cadence_plan=coordination["conversation_cadence_plan"],
        session_ritual_plan=coordination["session_ritual_plan"],
        somatic_orchestration_plan=coordination["somatic_orchestration_plan"],
        runtime_profile=runtime_profile,
        entity_persona=foundation.entity_persona,
    )

    return {
        "knowledge_boundary_decision": knowledge_boundary_decision,
        "private_judgment": private_judgment,
        "policy_gate": policy_gate,
        "strategy_decision": strategy_decision,
        "rehearsal_result": rehearsal_result,
        "expression_plan": expression_plan,
        "runtime_coordination_snapshot": coordination["runtime_coordination_snapshot"],
        "guidance_plan": coordination["guidance_plan"],
        "conversation_cadence_plan": coordination["conversation_cadence_plan"],
        "session_ritual_plan": coordination["session_ritual_plan"],
        "somatic_orchestration_plan": coordination["somatic_orchestration_plan"],
        "empowerment_audit": empowerment_audit,
        "response_draft_plan": response["response_draft_plan"],
        "response_rendering_policy": response["response_rendering_policy"],
    }
