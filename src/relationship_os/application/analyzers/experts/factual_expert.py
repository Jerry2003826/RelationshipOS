"""Factual & Memory Expert — knowledge boundary and confidence analysis.

Produces:
    - knowledge_boundary_decision (L1)
"""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers.cognition import (
    build_knowledge_boundary_decision,
)


def build_factual_expert_plans(
    *,
    context_frame: Any,
    relationship_state: Any,
    confidence_assessment: Any,
    user_message: str,
    recalled_memory: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build plans from the factual / memory domain.

    Returns
    -------
    dict with key ``knowledge_boundary_decision``.
    """
    knowledge_boundary_decision = build_knowledge_boundary_decision(
        context_frame=context_frame,
        relationship_state=relationship_state,
        confidence_assessment=confidence_assessment,
        user_message=user_message,
        recalled_memory=recalled_memory,
    )
    return {
        "knowledge_boundary_decision": knowledge_boundary_decision,
    }
