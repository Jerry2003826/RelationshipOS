"""Shared governance domain specification tables for proactive dispatch.

All three proactive pipeline files (controllers_stage, controllers_line,
dispatch_gate) previously maintained identical copies of the governance flag
spec and the matching/building helpers. This module is the single source of
truth for those definitions.
"""

from __future__ import annotations

from relationship_os.domain.contracts import System3Snapshot

# ---------------------------------------------------------------------------
# Governance domain flag specs
#
# Each entry: (domain_name, recenter_blocker_flags, watch_blocker_flags)
#
# The blocker logic means: a domain's recenter/watch flag is only set when
# none of the higher-priority domain flags in the blocker tuple are already
# active.  This encodes a priority ordering among governance domains.
# ---------------------------------------------------------------------------

GOVERNANCE_DOMAIN_FLAG_SPECS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("safety", (), ("safety_recenter_active",)),
    (
        "autonomy",
        ("safety_recenter_active",),
        ("safety_recenter_active", "autonomy_recenter_active"),
    ),
    (
        "boundary",
        ("safety_recenter_active", "autonomy_recenter_active"),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
        ),
    ),
    (
        "support",
        ("safety_recenter_active", "autonomy_recenter_active", "boundary_recenter_active"),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
        ),
    ),
    (
        "clarity",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
        ),
    ),
    (
        "pacing",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
        ),
    ),
    (
        "attunement",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
        ),
    ),
    (
        "commitment",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
        ),
    ),
    (
        "disclosure",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
        ),
    ),
    (
        "reciprocity",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
        ),
    ),
    (
        "progress",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
            "progress_recenter_active",
        ),
    ),
    (
        "stability",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
            "progress_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "autonomy_watch_active",
            "boundary_watch_active",
            "support_watch_active",
            "clarity_watch_active",
            "pacing_watch_active",
            "attunement_watch_active",
            "commitment_watch_active",
            "disclosure_watch_active",
            "reciprocity_watch_active",
            "progress_watch_active",
            "stability_recenter_active",
        ),
    ),
    (
        "pressure",
        (
            "safety_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "stability_recenter_active",
        ),
        (
            "safety_recenter_active",
            "boundary_watch_active",
            "support_watch_active",
            "clarity_watch_active",
            "pacing_watch_active",
            "attunement_watch_active",
            "commitment_watch_active",
            "stability_recenter_active",
            "pressure_recenter_active",
        ),
    ),
    (
        "trust",
        (
            "safety_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "stability_recenter_active",
            "pressure_recenter_active",
        ),
        (
            "safety_recenter_active",
            "boundary_watch_active",
            "support_watch_active",
            "clarity_watch_active",
            "pacing_watch_active",
            "attunement_watch_active",
            "commitment_watch_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
        ),
    ),
    (
        "continuity",
        (
            "safety_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
        ),
        (
            "safety_recenter_active",
            "boundary_watch_active",
            "support_watch_active",
            "clarity_watch_active",
            "pacing_watch_active",
            "attunement_watch_active",
            "commitment_watch_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
            "continuity_recenter_active",
        ),
    ),
    (
        "repair",
        (
            "safety_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
            "continuity_recenter_active",
        ),
        (
            "safety_recenter_active",
            "boundary_watch_active",
            "support_watch_active",
            "clarity_watch_active",
            "pacing_watch_active",
            "attunement_watch_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
            "continuity_recenter_active",
            "repair_recenter_active",
        ),
    ),
    (
        "relational",
        (
            "safety_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
            "continuity_recenter_active",
            "repair_recenter_active",
        ),
        (
            "safety_recenter_active",
            "boundary_watch_active",
            "support_watch_active",
            "clarity_watch_active",
            "pacing_watch_active",
            "attunement_watch_active",
            "stability_recenter_active",
            "pressure_recenter_active",
            "trust_recenter_active",
            "continuity_recenter_active",
            "repair_recenter_active",
            "relational_recenter_active",
        ),
    ),
    (
        "moral",
        ("safety_recenter_active",),
        ("safety_recenter_active", "moral_recenter_active"),
    ),
    (
        "growth_transition",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
            "progress_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
            "progress_recenter_active",
            "growth_transition_recenter_active",
        ),
    ),
    (
        "version_migration",
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
            "progress_recenter_active",
            "growth_transition_recenter_active",
        ),
        (
            "safety_recenter_active",
            "autonomy_recenter_active",
            "boundary_recenter_active",
            "support_recenter_active",
            "clarity_recenter_active",
            "pacing_recenter_active",
            "attunement_recenter_active",
            "commitment_recenter_active",
            "disclosure_recenter_active",
            "reciprocity_recenter_active",
            "progress_recenter_active",
            "growth_transition_recenter_active",
            "version_migration_recenter_active",
        ),
    ),
)


def matches_governance_signal(
    system3_snapshot: System3Snapshot,
    domain: str,
    *,
    status: str,
    trajectory: str,
) -> bool:
    """Return True if the given domain matches the requested governance status/trajectory."""
    return (
        getattr(system3_snapshot, f"{domain}_governance_status", None) == status
        or getattr(system3_snapshot, f"{domain}_governance_trajectory_status", None) == trajectory
    )


# ---------------------------------------------------------------------------
# Governance delay tables
#
# These tables provide the single source of truth for dispatch timing values
# used across controllers_stage, controllers_line, dispatch_gate, and
# controllers_aggregate.  Each entry format is documented per table.
# ---------------------------------------------------------------------------

# Per-domain stage-spacing delays for second_touch and final_soft_close.
# Format: (domain, recenter_delay_seconds, watch_delay_seconds)
# Used by controllers_stage.py for both second_touch and final_soft_close stage
# spacing specs (the values are identical for both stages in the original design).
GOVERNANCE_STAGE_DELAY_SPECS: tuple[tuple[str, int, int], ...] = (
    ("safety", 7200, 5400),
    ("autonomy", 6000, 4200),
    ("boundary", 5700, 3900),
    ("support", 5100, 3300),
    ("clarity", 4800, 3000),
    ("pacing", 4500, 2700),
    ("attunement", 4950, 3150),
    ("commitment", 5250, 3450),
    ("disclosure", 5250, 3450),
    ("reciprocity", 5250, 3450),
    ("progress", 5250, 3450),
    ("stability", 5400, 3600),
    ("pressure", 4500, 2700),
    ("trust", 3600, 2100),
    ("continuity", 3000, 1800),
    ("repair", 2700, 1500),
    ("relational", 2400, 1200),
)

# Dispatch gate deferral delays by stage.
# Format: (domain, recenter_high, recenter_low, watch_high, watch_low)
# Used by dispatch_gate.py when deciding how long to defer a dispatch when
# a governance domain is active.
GOVERNANCE_GATE_DELAY_SPECS_BY_STAGE: dict[
    str, tuple[tuple[str, int, int, int, int], ...]
] = {
    "first_touch": (
        ("safety", 7200, 5400, 5400, 3600),
        ("autonomy", 6000, 4200, 4200, 3000),
        ("boundary", 5700, 3900, 3900, 2700),
        ("support", 5100, 3300, 3300, 2400),
        ("clarity", 4800, 3000, 3000, 2100),
        ("pacing", 4500, 2700, 2700, 1800),
        ("attunement", 4950, 3150, 3150, 2100),
        ("commitment", 5250, 3450, 3450, 2400),
        ("disclosure", 5250, 3450, 3450, 2400),
        ("reciprocity", 5250, 3450, 3450, 2400),
        ("progress", 5250, 3450, 3450, 2400),
        ("stability", 5400, 3600, 3600, 2400),
        ("pressure", 4500, 2700, 2700, 1800),
        ("trust", 3600, 2100, 2100, 1500),
        ("continuity", 3000, 1800, 1800, 1200),
        ("repair", 2700, 1500, 1500, 900),
        ("relational", 2400, 1200, 1200, 600),
    ),
    "second_touch": (
        ("safety", 7200, 5400, 5400, 3600),
        ("autonomy", 6000, 4200, 4200, 3000),
        ("boundary", 5700, 3900, 3900, 2700),
        ("support", 5100, 3300, 3300, 2400),
        ("clarity", 4800, 3000, 3000, 2100),
        ("pacing", 4500, 2700, 2700, 1800),
        ("attunement", 4950, 3150, 3150, 2100),
        ("commitment", 5250, 3450, 3450, 2400),
        ("disclosure", 5250, 3450, 3450, 2400),
        ("reciprocity", 5250, 3450, 3450, 2400),
        ("progress", 5250, 3450, 3450, 2400),
        ("stability", 5400, 3600, 3600, 2400),
        ("pressure", 4500, 2700, 2700, 1800),
        ("trust", 3600, 2100, 2100, 1500),
        ("continuity", 3000, 1800, 1800, 1200),
        ("repair", 2700, 1500, 1500, 900),
        ("relational", 2400, 1200, 1200, 600),
    ),
    "final_soft_close": (
        ("safety", 7200, 5400, 5400, 3600),
        ("autonomy", 6000, 4200, 4200, 3000),
        ("boundary", 5700, 3900, 3900, 2700),
        ("support", 5100, 3300, 3300, 2400),
        ("clarity", 4800, 3000, 3000, 2100),
        ("pacing", 4500, 2700, 2700, 1800),
        ("attunement", 4950, 3150, 3150, 2100),
        ("commitment", 5250, 3450, 3450, 2400),
        ("disclosure", 5250, 3450, 3450, 2400),
        ("reciprocity", 5250, 3450, 3450, 2400),
        ("progress", 5250, 3450, 3450, 2400),
        ("stability", 5400, 3600, 3600, 2400),
        ("pressure", 4500, 2700, 2700, 1800),
        ("trust", 3600, 2100, 2100, 1500),
        ("continuity", 3000, 1800, 1800, 1200),
        ("repair", 2700, 1500, 1500, 900),
        ("relational", 2400, 1200, 1200, 600),
    ),
}

# Aggregate controller delays (used by controllers_aggregate.py).
# Format: {(next_stage_label, kind): (stage_delay, line_delay)}
# 'kind' is 'recenter' or 'default'.
GOVERNANCE_AGGREGATE_DELAY_TABLE: dict[tuple[str, str], tuple[int, int]] = {
    ("second_touch", "recenter"): (6300, 3900),
    ("second_touch", "default"): (4050, 2700),
    ("final_soft_close", "recenter"): (5700, 0),
    ("final_soft_close", "default"): (3900, 0),
    ("first_touch", "recenter"): (0, 3900),
    ("first_touch", "default"): (0, 2700),
}

# Aggregate controller stage-transition strategy parameters.
# Format: {(next_stage_label, kind):
#   (strategy_key, pressure_mode, autonomy_signal, delivery_mode, note)}
GOVERNANCE_AGGREGATE_STRATEGY_TABLE: dict[
    tuple[str, str],
    tuple[str, str, str, str, str],
] = {
    ("second_touch", "recenter"): (
        "repair_soft_resume_bridge",
        "repair_soft",
        "explicit_no_pressure",
        "single_message",
        "space_out_second_touch",
    ),
    ("second_touch", "default"): (
        "resume_context_bridge",
        "gentle_resume",
        "explicit_no_pressure",
        "single_message",
        "space_out_second_touch",
    ),
    ("final_soft_close", "recenter"): (
        "continuity_soft_ping",
        "archive_light_presence",
        "archive_light_thread",
        "single_message",
        "leave_more_breathing_room_before_close",
    ),
    ("final_soft_close", "default"): (
        "continuity_soft_ping",
        "archive_light_presence",
        "archive_light_thread",
        "single_message",
        "leave_more_breathing_room_before_close",
    ),
}

# Dispatch retry delay for final_soft_close governance.
# Format: {(is_recenter, is_elevated): retry_after_seconds}
GOVERNANCE_AGGREGATE_RETRY_TABLE: dict[tuple[bool, bool], int] = {
    (True, True): 3000,
    (True, False): 2100,
    (False, True): 2100,
    (False, False): 1500,
}


def build_governance_signal_flags(
    system3_snapshot: System3Snapshot,
) -> dict[str, bool]:
    """Build a flat flag dict from the canonical governance domain spec table.

    Returns a mapping like ``{"safety_recenter_active": True, "safety_watch_active": False, ...}``
    for every domain in ``GOVERNANCE_DOMAIN_FLAG_SPECS``.
    """
    flags: dict[str, bool] = {}
    for domain, recenter_blockers, watch_blockers in GOVERNANCE_DOMAIN_FLAG_SPECS:
        recenter_key = f"{domain}_recenter_active"
        watch_key = f"{domain}_watch_active"
        recenter_active = not any(flags.get(k, False) for k in recenter_blockers) and (
            matches_governance_signal(
                system3_snapshot,
                domain,
                status="revise",
                trajectory="recenter",
            )
        )
        flags[recenter_key] = recenter_active
        flags[watch_key] = (
            not recenter_active
            and not any(flags.get(k, False) for k in watch_blockers)
            and matches_governance_signal(
                system3_snapshot,
                domain,
                status="watch",
                trajectory="watch",
            )
        )
    return flags
