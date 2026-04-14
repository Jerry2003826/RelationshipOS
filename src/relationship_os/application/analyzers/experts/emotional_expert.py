"""Emotional & Social Expert — private judgment and inner assessment.

Produces:
    - private_judgment (L2, depends on factual expert's knowledge_boundary_decision)
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.cognition import build_private_judgment


def build_emotional_expert_plans(
    *,
    context_frame: Any,
    relationship_state: Any,
    repair_assessment: Any,
    repair_plan: Any,
    knowledge_boundary_decision: Any,
    memory_bundle: Any,
    confidence_assessment: Any,
    recalled_memory: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build plans from the emotional / social domain.

    Returns
    -------
    dict with key ``private_judgment``.
    """
    private_judgment = build_private_judgment(
        context_frame=context_frame,
        relationship_state=relationship_state,
        repair_assessment=repair_assessment,
        repair_plan=repair_plan,
        knowledge_boundary_decision=knowledge_boundary_decision,
        memory_bundle=memory_bundle,
        confidence_assessment=confidence_assessment,
        recalled_memory=recalled_memory,
    )
    return {
        "private_judgment": private_judgment,
    }
