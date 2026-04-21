"""Phase 2 governance – public entry point."""

from __future__ import annotations

from relationship_os.domain.contracts import System3Snapshot

from ._base import _System3Prelude
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
    _build_progress_governance,
    _build_relational_governance,
    _build_safety_governance,
    _build_stability_governance,
)
from ._domains_social import (
    _build_commitment_governance,
    _build_disclosure_governance,
    _build_reciprocity_governance,
)
from ._transitions import (
    _build_core_governance_outcomes,
    _build_growth_transition,
    _build_phase2_snapshot,
    _build_review_focus,
    _build_version_migration,
)

def build_system3_phase2_snapshot(*, prelude: _System3Prelude) -> System3Snapshot:
    governance_outcomes = _build_core_governance_outcomes(prelude=prelude)
    growth_transition = _build_growth_transition(prelude=prelude)
    governance_outcomes["progress"] = _build_progress_governance(
        safety=governance_outcomes["safety"],
        pressure=governance_outcomes["pressure"],
        continuity=governance_outcomes["continuity"],
        commitment=governance_outcomes["commitment"],
        pacing=governance_outcomes["pacing"],
        growth_transition_status=growth_transition.status,
        expectation_calibration_status=prelude.expectation_calibration_status,
    )
    governance_outcomes["stability"] = _build_stability_governance(
        safety=governance_outcomes["safety"],
        relational=governance_outcomes["relational"],
        pressure=governance_outcomes["pressure"],
        trust=governance_outcomes["trust"],
        continuity=governance_outcomes["continuity"],
        repair=governance_outcomes["repair"],
        progress=governance_outcomes["progress"],
        pacing=governance_outcomes["pacing"],
        attunement=governance_outcomes["attunement"],
    )
    version_migration = _build_version_migration(
        prelude=prelude,
        growth_transition=growth_transition,
    )
    review_focus = _build_review_focus(
        prelude=prelude,
        governance_outcomes=governance_outcomes,
        growth_transition=growth_transition,
        version_migration=version_migration,
    )
    return _build_phase2_snapshot(
        prelude=prelude,
        governance_outcomes=governance_outcomes,
        growth_transition=growth_transition,
        version_migration=version_migration,
        review_focus=review_focus,
    )
