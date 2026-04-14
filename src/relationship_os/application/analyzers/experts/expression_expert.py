"""Expression & Empowerment Expert — tone, goals, and agency audit.

Produces:
    - expression_plan (L6)
    - empowerment_audit (L7)
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.expression import (
    build_empowerment_audit,
    build_expression_plan,
)


def build_expression_expert_plans(
    *,
    strategy_decision: Any,
    repair_plan: Any,
    rehearsal_result: Any,
    policy_gate: Any,
    relationship_state: Any,
    knowledge_boundary_decision: Any,
    confidence_assessment: Any,
) -> dict[str, Any]:
    """Build plans from the expression / empowerment domain.

    Returns
    -------
    dict with keys ``expression_plan``, ``empowerment_audit``.
    """
    expression_plan = build_expression_plan(
        strategy_decision,
        repair_plan,
        rehearsal_result,
    )

    empowerment_audit = build_empowerment_audit(
        policy_gate=policy_gate,
        relationship_state=relationship_state,
        knowledge_boundary_decision=knowledge_boundary_decision,
        confidence_assessment=confidence_assessment,
        expression_plan=expression_plan,
        rehearsal_result=rehearsal_result,
    )

    return {
        "expression_plan": expression_plan,
        "empowerment_audit": empowerment_audit,
    }
