"""Governance & Strategy Expert — policy, strategy, and rehearsal.

Produces:
    - policy_gate (L3)
    - strategy_decision (L4)
    - rehearsal_result (L5)
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.strategy import (
    build_policy_gate,
    build_rehearsal_result,
    build_strategy_decision,
)


def build_governance_expert_plans(
    *,
    context_frame: Any,
    relationship_state: Any,
    repair_assessment: Any,
    confidence_assessment: Any,
    knowledge_boundary_decision: Any,
    private_judgment: Any,
    strategy_history: list[Any],
) -> dict[str, Any]:
    """Build plans from the governance / strategy domain.

    Returns
    -------
    dict with keys ``policy_gate``, ``strategy_decision``, ``rehearsal_result``.
    """
    policy_gate = build_policy_gate(
        context_frame=context_frame,
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
        confidence_assessment=confidence_assessment,
        private_judgment=private_judgment,
    )

    strategy_decision = build_strategy_decision(
        policy_gate=policy_gate,
        private_judgment=private_judgment,
        context_frame=context_frame,
        repair_assessment=repair_assessment,
        confidence_assessment=confidence_assessment,
        relationship_state=relationship_state,
        strategy_history=strategy_history,
    )

    rehearsal_result = build_rehearsal_result(
        strategy_decision=strategy_decision,
        policy_gate=policy_gate,
        repair_assessment=repair_assessment,
        knowledge_boundary_decision=knowledge_boundary_decision,
    )

    return {
        "policy_gate": policy_gate,
        "strategy_decision": strategy_decision,
        "rehearsal_result": rehearsal_result,
    }
