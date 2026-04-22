"""Phase 2 governance package for System 3 snapshot assembly.

All symbols previously at the top level of the single-file module are
re-exported here so that existing ``from ... import`` and attribute-based
access (e.g. ``phase2_module._build_*``) continue to work unchanged.
"""

from __future__ import annotations

# Re-expose get_default_compiled_policy_set as a module-level attribute so
# that monkeypatching ``phase2_module.get_default_compiled_policy_set = X``
# in tests works correctly.  _base._phase2_policy() looks this up via the
# package module at call time, so the patched value is always used.
from relationship_os.application.policy_registry import get_default_compiled_policy_set

from ._base import (
    _SYSTEM3_GOVERNANCE_DOMAIN_ORDER,
    _governance_kwargs,
    _GovernanceOutcome,
    _GrowthTransitionOutcome,
    _phase2_branch,
    _phase2_governance_line,
    _phase2_policy,
    _phase2_section,
    _System3Prelude,
    _VersionMigrationOutcome,
)
from ._domains_core import (
    _build_attunement_governance,
    _build_autonomy_governance,
    _build_boundary_governance,
    _build_clarity_governance,
    _build_continuity_governance,
    _build_dependency_governance,
    _build_pacing_governance,
    _build_repair_governance,
    _build_support_governance,
    _build_trust_governance,
)
from ._domains_safety import (
    _build_pressure_governance,
    _build_pressure_governance_state,
    _build_pressure_governance_trajectory,
    _build_progress_governance,
    _build_relational_governance,
    _build_relational_governance_state,
    _build_relational_governance_trajectory,
    _build_safety_governance,
    _build_safety_governance_state,
    _build_safety_governance_trajectory,
    _build_stability_governance,
    _build_stability_governance_state,
    _build_stability_governance_trajectory,
    _build_stability_recenter_state,
    _build_stability_watch_state,
)
from ._domains_social import (
    _build_commitment_governance,
    _build_commitment_governance_state,
    _build_commitment_governance_trajectory,
    _build_disclosure_governance,
    _build_reciprocity_governance,
    _build_reciprocity_governance_state,
    _build_reciprocity_governance_trajectory,
)
from ._public import build_system3_phase2_snapshot
from ._transitions import (
    _build_base_snapshot_fields,
    _build_core_governance_outcomes,
    _build_growth_transition,
    _build_growth_transition_state,
    _build_growth_transition_trajectory,
    _build_phase2_snapshot,
    _build_review_focus,
    _build_version_migration,
)

__all__ = [
    "get_default_compiled_policy_set",
    "_SYSTEM3_GOVERNANCE_DOMAIN_ORDER",
    "_System3Prelude",
    "_GovernanceOutcome",
    "_GrowthTransitionOutcome",
    "_VersionMigrationOutcome",
    "_phase2_policy",
    "_phase2_section",
    "_phase2_governance_line",
    "_phase2_branch",
    "_governance_kwargs",
    "_build_review_focus",
    "_build_core_governance_outcomes",
    "_build_growth_transition",
    "_build_growth_transition_state",
    "_build_growth_transition_trajectory",
    "_build_version_migration",
    "_build_base_snapshot_fields",
    "_build_phase2_snapshot",
    "_build_dependency_governance",
    "_build_autonomy_governance",
    "_build_boundary_governance",
    "_build_support_governance",
    "_build_continuity_governance",
    "_build_repair_governance",
    "_build_attunement_governance",
    "_build_trust_governance",
    "_build_clarity_governance",
    "_build_pacing_governance",
    "_build_commitment_governance",
    "_build_commitment_governance_state",
    "_build_commitment_governance_trajectory",
    "_build_disclosure_governance",
    "_build_reciprocity_governance",
    "_build_reciprocity_governance_state",
    "_build_reciprocity_governance_trajectory",
    "_build_pressure_governance",
    "_build_pressure_governance_state",
    "_build_pressure_governance_trajectory",
    "_build_relational_governance",
    "_build_relational_governance_state",
    "_build_relational_governance_trajectory",
    "_build_safety_governance",
    "_build_safety_governance_state",
    "_build_safety_governance_trajectory",
    "_build_progress_governance",
    "_build_stability_governance",
    "_build_stability_governance_state",
    "_build_stability_recenter_state",
    "_build_stability_watch_state",
    "_build_stability_governance_trajectory",
    "build_system3_phase2_snapshot",
]
