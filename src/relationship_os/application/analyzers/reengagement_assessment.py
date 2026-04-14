"""Re-engagement assessment and planning."""

from __future__ import annotations

import math
from typing import Any

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ConversationCadencePlan,
    GuidancePlan,
    ProactiveFollowupDirective,
    ReengagementMatrixAssessment,
    ReengagementPlan,
    ReengagementStrategyCandidate,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    System3Snapshot,
)

_REENGAGEMENT_CANDIDATE_PROFILES = {
    "continuity_soft_ping": {
        "relational_move": "continuity_ping",
        "pressure_mode": "low_pressure_presence",
        "autonomy_signal": "open_loop_without_demand",
        "delivery_mode_hint": "single_message",
    },
    "progress_micro_commitment": {
        "relational_move": "goal_reconnect",
        "pressure_mode": "low_pressure_progress",
        "autonomy_signal": "explicit_opt_out",
        "delivery_mode_hint": "two_part_sequence",
    },
    "grounding_then_resume": {
        "relational_move": "stabilize_then_resume",
        "pressure_mode": "ultra_low_pressure",
        "autonomy_signal": "no_reply_required",
        "delivery_mode_hint": "two_part_sequence",
    },
    "resume_context_bridge": {
        "relational_move": "context_bridge",
        "pressure_mode": "gentle_resume",
        "autonomy_signal": "light_invitation",
        "delivery_mode_hint": "two_part_sequence",
    },
    "repair_soft_reentry": {
        "relational_move": "repair_bridge",
        "pressure_mode": "repair_soft",
        "autonomy_signal": "explicit_no_pressure",
        "delivery_mode_hint": "single_message",
    },
    "repair_soft_progress_reentry": {
        "relational_move": "repair_bridge",
        "pressure_mode": "repair_soft",
        "autonomy_signal": "explicit_no_pressure",
        "delivery_mode_hint": "two_part_sequence",
    },
    "repair_soft_resume_bridge": {
        "relational_move": "repair_bridge",
        "pressure_mode": "repair_soft",
        "autonomy_signal": "explicit_no_pressure",
        "delivery_mode_hint": "two_part_sequence",
    },
}


def _build_learning_signal_state(
    *,
    learning_report: dict[str, Any],
    learning_context_stratum: str,
) -> dict[str, Any]:
    learning_signals = {
        str(item.get("strategy_key") or ""): dict(item)
        for item in list(learning_report.get("strategies") or [])
        if str(item.get("strategy_key") or "")
    }
    learning_signal_count = len(learning_signals)
    learning_notes: list[str] = []
    if learning_signal_count == 0:
        learning_notes.append("no_historical_signal")
    elif int(learning_report.get("matching_context_session_count") or 0) > 0:
        learning_notes.append("contextual_history_available")
    else:
        learning_notes.append("global_history_only")
    learning_notes.append(f"context:{learning_context_stratum}")
    return {
        "learning_signals": learning_signals,
        "learning_signal_count": learning_signal_count,
        "learning_notes": learning_notes,
    }


def _build_outcome_signal_state(
    outcome_report: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Index outcome learning report strategies by strategy_key for fast lookup."""
    return {
        str(item.get("strategy_key") or ""): dict(item)
        for item in list(outcome_report.get("strategies") or [])
        if str(item.get("strategy_key") or "")
    }


def _score_reengagement_candidate(
    *,
    strategy_key: str,
    profile: dict[str, str],
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    system3_snapshot: System3Snapshot,
    repair_context: bool,
    learning_signals: dict[str, dict[str, Any]],
    learning_signal_count: int,
    outcome_signals: dict[str, dict[str, Any]] | None = None,
    total_dispatches: int = 0,
) -> ReengagementStrategyCandidate:
    candidate_state = _build_reengagement_candidate_state(directive=directive)
    _apply_directive_strategy_adjustments(
        candidate_state,
        strategy_key=strategy_key,
        directive=directive,
    )
    _apply_resume_and_guidance_adjustments(
        candidate_state,
        strategy_key=strategy_key,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        guidance_plan=guidance_plan,
    )
    _apply_cadence_and_ritual_adjustments(
        candidate_state,
        strategy_key=strategy_key,
        profile=profile,
        cadence_plan=cadence_plan,
        session_ritual_plan=session_ritual_plan,
    )
    _apply_repair_and_system3_adjustments(
        candidate_state,
        strategy_key=strategy_key,
        profile=profile,
        repair_context=repair_context,
        system3_snapshot=system3_snapshot,
    )
    _apply_learning_adjustments(
        candidate_state,
        strategy_key=strategy_key,
        profile=profile,
        learning_signals=learning_signals,
        learning_signal_count=learning_signal_count,
        outcome_signals=outcome_signals or {},
        total_dispatches=total_dispatches,
    )

    return ReengagementStrategyCandidate(
        strategy_key=strategy_key,
        suitability_score=round(
            max(0.0, min(float(candidate_state["score"]), 1.0)),
            3,
        ),
        relational_move=str(profile["relational_move"]),
        pressure_mode=str(profile["pressure_mode"]),
        autonomy_signal=str(profile["autonomy_signal"]),
        delivery_mode_hint=str(profile["delivery_mode_hint"]),
        blocked=bool(candidate_state["blocked"]),
        supporting_session_count=int(candidate_state["supporting_session_count"]),
        contextual_supporting_session_count=int(
            candidate_state["contextual_supporting_session_count"]
        ),
        historical_preference_score=(
            round(candidate_state["historical_preference_score"], 3)
            if candidate_state["historical_preference_score"] is not None
            else None
        ),
        contextual_preference_score=(
            round(candidate_state["contextual_preference_score"], 3)
            if candidate_state["contextual_preference_score"] is not None
            else None
        ),
        exploration_bonus=round(float(candidate_state["exploration_bonus"]), 3),
        rationale="; ".join(list(candidate_state["reasons"])[:6]),
    )


def _build_reengagement_candidate_state(
    *,
    directive: ProactiveFollowupDirective,
) -> dict[str, Any]:
    return {
        "score": 0.25,
        "blocked": False,
        "reasons": [f"base:{directive.style or 'continuity'}"],
        "supporting_session_count": 0,
        "contextual_supporting_session_count": 0,
        "historical_preference_score": None,
        "contextual_preference_score": None,
        "exploration_bonus": 0.0,
    }


def _apply_directive_strategy_adjustments(
    state: dict[str, Any],
    *,
    strategy_key: str,
    directive: ProactiveFollowupDirective,
) -> None:
    if directive.style == "progress_nudge":
        if strategy_key == "progress_micro_commitment":
            state["score"] += 0.45
            state["reasons"].append("fits_progress_nudge")
        elif strategy_key == "repair_soft_progress_reentry":
            state["score"] += 0.25
            state["reasons"].append("repair_safe_progress_variant")
        elif strategy_key == "resume_context_bridge":
            state["score"] += 0.15
        elif strategy_key == "grounding_then_resume":
            state["score"] -= 0.1
        return
    if directive.style == "grounded_check_in":
        if strategy_key == "grounding_then_resume":
            state["score"] += 0.45
            state["reasons"].append("fits_grounded_check_in")
        elif strategy_key == "repair_soft_reentry":
            state["score"] += 0.15
        elif strategy_key == "progress_micro_commitment":
            state["score"] -= 0.15
        return
    if strategy_key == "continuity_soft_ping":
        state["score"] += 0.2
        state["reasons"].append("default_continuity_fit")


def _apply_resume_and_guidance_adjustments(
    state: dict[str, Any],
    *,
    strategy_key: str,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
) -> None:
    if runtime_coordination_snapshot.time_awareness_mode in {"resume", "reengagement"}:
        if strategy_key in {"resume_context_bridge", "repair_soft_resume_bridge"}:
            state["score"] += 0.35
            state["reasons"].append("resume_context_match")

    if guidance_plan.mode == "reanchor_guidance":
        if strategy_key in {"resume_context_bridge", "repair_soft_resume_bridge"}:
            state["score"] += 0.25
            state["reasons"].append("guidance_reanchor")
        return
    if guidance_plan.mode == "stabilizing_guidance":
        if strategy_key == "grounding_then_resume":
            state["score"] += 0.25
            state["reasons"].append("guidance_stabilize")
        elif strategy_key == "progress_micro_commitment":
            state["score"] -= 0.15
        return
    if guidance_plan.mode in {"repair_guidance", "boundary_guidance"}:
        if strategy_key.startswith("repair_soft"):
            state["score"] += 0.35
            state["reasons"].append("guidance_repair")
        elif strategy_key in {"progress_micro_commitment", "resume_context_bridge"}:
            state["score"] -= 0.2


def _apply_cadence_and_ritual_adjustments(
    state: dict[str, Any],
    *,
    strategy_key: str,
    profile: dict[str, str],
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
) -> None:
    if cadence_plan.turn_shape in {"reanchor_then_step", "reflect_then_step"}:
        if profile["delivery_mode_hint"] == "two_part_sequence":
            state["score"] += 0.1
            state["reasons"].append("cadence_two_part")
    elif cadence_plan.turn_shape == "question_then_pause":
        if strategy_key == "continuity_soft_ping":
            state["score"] += 0.1

    if cadence_plan.user_space_mode in {"spacious", "explicit_autonomy_space"}:
        if profile["autonomy_signal"] in {"explicit_no_pressure", "explicit_opt_out"}:
            state["score"] += 0.1
            state["reasons"].append("user_space_autonomy")

    if session_ritual_plan.closing_move in {
        "repair_soft_close",
        "boundary_safe_close",
        "grounding_close",
    }:
        if strategy_key.startswith("repair_soft") or strategy_key == "grounding_then_resume":
            state["score"] += 0.15
        elif strategy_key == "progress_micro_commitment":
            state["score"] -= 0.1


def _apply_repair_and_system3_adjustments(
    state: dict[str, Any],
    *,
    strategy_key: str,
    profile: dict[str, str],
    repair_context: bool,
    system3_snapshot: System3Snapshot,
) -> None:
    if repair_context:
        if strategy_key.startswith("repair_soft"):
            state["score"] += 0.3
            state["reasons"].append("repair_context_bias")
        elif strategy_key in {"progress_micro_commitment", "resume_context_bridge"}:
            state["score"] -= 0.25

    if system3_snapshot.emotional_debt_status == "elevated" and strategy_key in {
        "progress_micro_commitment",
        "resume_context_bridge",
    }:
        state["blocked"] = True
        state["reasons"].append("blocked_by_emotional_debt")
    if (
        system3_snapshot.strategy_audit_status == "revise"
        and profile["pressure_mode"] not in {"repair_soft", "ultra_low_pressure"}
    ):
        state["blocked"] = True
        state["reasons"].append("blocked_by_strategy_audit")

    # User model trajectory constraints
    if getattr(system3_snapshot, "user_model_trajectory_status", None) == "recenter":
        if strategy_key.startswith("progress_"):
            state["score"] -= 0.15
            state["reasons"].append("user_model_recenter_deprioritize_progress")
        if strategy_key == "grounding_then_resume":
            state["score"] += 0.10
            state["reasons"].append("user_model_recenter_favor_grounding")
    if (
        getattr(system3_snapshot, "user_model_revision_mode", None) == "context_drift"
        and strategy_key == "resume_context_bridge"
    ):
        state["blocked"] = True
        state["reasons"].append("blocked_by_context_drift")


def _apply_learning_adjustments(
    state: dict[str, Any],
    *,
    strategy_key: str,
    profile: dict[str, str],
    learning_signals: dict[str, dict[str, Any]],
    learning_signal_count: int,
    outcome_signals: dict[str, dict[str, Any]],
    total_dispatches: int,
) -> None:
    learning_signal = learning_signals.get(strategy_key) or {}
    outcome_signal = outcome_signals.get(strategy_key) or {}
    has_session_signal = bool(learning_signal)
    has_outcome_signal = bool(outcome_signal) and int(
        outcome_signal.get("total_dispatches") or 0
    ) > 0

    if has_session_signal:
        state["supporting_session_count"] = max(
            0,
            int(learning_signal.get("kept_session_count") or 0),
        )
        state["contextual_supporting_session_count"] = max(
            0,
            int(learning_signal.get("contextual_kept_session_count") or 0),
        )
        if learning_signal.get("avg_learning_score") is not None:
            state["historical_preference_score"] = float(
                learning_signal.get("avg_learning_score") or 0.0
            )
        if learning_signal.get("avg_contextual_learning_score") is not None:
            state["contextual_preference_score"] = float(
                learning_signal.get("avg_contextual_learning_score") or 0.0
            )

    if has_session_signal or has_outcome_signal:
        session_delta = 0.0
        effective_preference_score = (
            state["contextual_preference_score"]
            if state["contextual_preference_score"] is not None
            and state["contextual_supporting_session_count"] > 0
            else state["historical_preference_score"]
        )
        effective_support_count = (
            state["contextual_supporting_session_count"]
            if state["contextual_supporting_session_count"] > 0
            else state["supporting_session_count"]
        )
        if effective_preference_score is not None and effective_support_count > 0:
            session_weight = min(0.18, 0.06 * effective_support_count)
            session_delta = (effective_preference_score - 0.5) * session_weight * 2.0

        outcome_delta = 0.0
        if has_outcome_signal:
            outcome_count = int(outcome_signal.get("total_dispatches") or 0)
            outcome_score = float(outcome_signal.get("outcome_score") or 0.0)
            outcome_weight = min(0.24, 0.08 * outcome_count)
            outcome_delta = (outcome_score - 0.5) * outcome_weight * 2.0

            negative_count = int(outcome_signal.get("negative_signal") or 0)
            if outcome_count > 0 and negative_count > 0:
                negative_signal_rate = negative_count / outcome_count
                if negative_signal_rate >= 0.4:
                    state["reasons"].append("high_negative_signal_rate")
                    state["score"] -= min(0.25, negative_signal_rate * 0.4)
                elif negative_signal_rate >= 0.2:
                    state["reasons"].append("moderate_negative_signal_rate")
                    state["score"] -= min(0.1, negative_signal_rate * 0.25)

        if has_session_signal and has_outcome_signal:
            combined_delta = session_delta * 0.4 + outcome_delta * 0.6
            state["reasons"].append("dual_signal_fusion")
        elif has_outcome_signal:
            combined_delta = outcome_delta
            state["reasons"].append("outcome_signal_only")
        else:
            combined_delta = session_delta
            state["reasons"].append(
                "learning_contextual"
                if state["contextual_supporting_session_count"] > 0
                else "learning_global"
            )

        state["score"] += combined_delta

        strategy_dispatches = int(
            outcome_signal.get("total_dispatches") or 0
        ) if has_outcome_signal else 0
        if total_dispatches > 0 and strategy_dispatches >= 0:
            _UCB_COEFFICIENT = 0.05
            ucb_bonus = _UCB_COEFFICIENT * math.sqrt(
                math.log(total_dispatches + 1) / (strategy_dispatches + 1)
            )
            state["exploration_bonus"] = round(ucb_bonus, 4)
            state["score"] += state["exploration_bonus"]
            state["reasons"].append("ucb_exploration")
        return

    if (learning_signal_count > 0 or total_dispatches > 0) and profile[
        "pressure_mode"
    ] in {
        "low_pressure_presence",
        "ultra_low_pressure",
        "repair_soft",
    }:
        if total_dispatches > 0:
            _UCB_COEFFICIENT = 0.05
            ucb_bonus = _UCB_COEFFICIENT * math.sqrt(
                math.log(total_dispatches + 1) / 1
            )
            state["exploration_bonus"] = round(ucb_bonus, 4)
        else:
            state["exploration_bonus"] = 0.03
        state["score"] += state["exploration_bonus"]
        state["reasons"].append("safe_exploration")


def _materialize_ranked_reengagement_candidates(
    candidates: list[ReengagementStrategyCandidate],
) -> dict[str, Any]:
    ranked_candidates = sorted(
        candidates,
        key=lambda item: (not item.blocked, item.suitability_score, item.strategy_key),
        reverse=True,
    )
    selected = next(
        (item for item in ranked_candidates if not item.blocked),
        ranked_candidates[0],
    )
    selected_key = selected.strategy_key
    blocked_count = sum(1 for item in ranked_candidates if item.blocked)
    materialized_candidates = [
        ReengagementStrategyCandidate(
            strategy_key=item.strategy_key,
            suitability_score=item.suitability_score,
            relational_move=item.relational_move,
            pressure_mode=item.pressure_mode,
            autonomy_signal=item.autonomy_signal,
            delivery_mode_hint=item.delivery_mode_hint,
            selected=item.strategy_key == selected_key,
            blocked=item.blocked,
            supporting_session_count=item.supporting_session_count,
            contextual_supporting_session_count=item.contextual_supporting_session_count,
            historical_preference_score=item.historical_preference_score,
            contextual_preference_score=item.contextual_preference_score,
            exploration_bonus=item.exploration_bonus,
            rationale=item.rationale,
        )
        for item in ranked_candidates
    ]
    return {
        "selected": selected,
        "selected_key": selected_key,
        "blocked_count": blocked_count,
        "materialized_candidates": materialized_candidates,
    }


def _resolve_reengagement_learning_mode(
    candidates: list[ReengagementStrategyCandidate],
) -> str:
    selected_candidate = next(
        (item for item in candidates if item.selected),
        candidates[0] if candidates else None,
    )
    if selected_candidate is None:
        return "cold_start"
    if selected_candidate.contextual_supporting_session_count > 0:
        return "contextual_reinforcement"
    if selected_candidate.supporting_session_count > 0:
        return "global_reinforcement"
    if selected_candidate.exploration_bonus > 0:
        return "safe_exploration"
    return "cold_start"


def _build_reengagement_plan_state(
    *,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
) -> dict[str, Any]:
    return {
        "ritual_mode": "continuity_nudge",
        "delivery_mode": "single_message",
        "strategy_key": "continuity_soft_ping",
        "relational_move": "continuity_ping",
        "pressure_mode": "low_pressure_presence",
        "autonomy_signal": "open_loop_without_demand",
        "sequence_objective": "presence_then_optional_reply",
        "somatic_action": _infer_reengagement_somatic_action(
            runtime_coordination_snapshot.somatic_cue
        ),
        "segment_labels": ["check_in"],
        "focus_points": list(directive.trigger_conditions),
        "tone": "gentle",
        "opening_hint": directive.opening_hint,
        "closing_hint": "leave room for the user to re-enter without pressure.",
    }


def _apply_preferred_reengagement_strategy(
    state: dict[str, Any],
    *,
    preferred_strategy_key: str | None,
) -> None:
    if preferred_strategy_key == "progress_micro_commitment":
        state.update(
            {
                "ritual_mode": "progress_reanchor",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "progress_micro_commitment",
                "relational_move": "goal_reconnect",
                "pressure_mode": "low_pressure_progress",
                "autonomy_signal": "explicit_opt_out",
                "sequence_objective": "reconnect_then_tiny_step",
                "segment_labels": ["reconnect", "next_step"],
                "closing_hint": "offer one tiny next action and keep autonomy explicit.",
            }
        )
    elif preferred_strategy_key == "grounding_then_resume":
        state.update(
            {
                "ritual_mode": "grounding_reentry",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "grounding_then_resume",
                "relational_move": "stabilize_then_resume",
                "pressure_mode": "ultra_low_pressure",
                "autonomy_signal": "no_reply_required",
                "sequence_objective": "ground_then_steady_step",
                "segment_labels": ["grounding", "steady_step"],
                "tone": "grounding",
            }
        )
    elif preferred_strategy_key == "resume_context_bridge":
        state.update(
            {
                "ritual_mode": "resume_reanchor",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "resume_context_bridge",
                "relational_move": "context_bridge",
                "pressure_mode": "gentle_resume",
                "autonomy_signal": "light_invitation",
                "sequence_objective": "re_anchor_then_continue",
                "segment_labels": ["re_anchor", "continuity"],
            }
        )
    elif preferred_strategy_key == "repair_soft_progress_reentry":
        state.update(
            {
                "ritual_mode": "progress_reanchor",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "repair_soft_progress_reentry",
                "relational_move": "repair_bridge",
                "pressure_mode": "repair_soft",
                "autonomy_signal": "explicit_no_pressure",
                "sequence_objective": "reconnect_without_relational_demand",
                "segment_labels": ["reconnect", "next_step"],
                "tone": "repair_aware",
                "closing_hint": (
                    "reduce pressure, keep the bridge open, and avoid demanding a reply."
                ),
            }
        )
    elif preferred_strategy_key == "repair_soft_resume_bridge":
        state.update(
            {
                "ritual_mode": "resume_reanchor",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "repair_soft_resume_bridge",
                "relational_move": "repair_bridge",
                "pressure_mode": "repair_soft",
                "autonomy_signal": "explicit_no_pressure",
                "sequence_objective": "reconnect_without_relational_demand",
                "segment_labels": ["re_anchor", "continuity"],
                "tone": "repair_aware",
                "closing_hint": (
                    "reduce pressure, keep the bridge open, and avoid demanding a reply."
                ),
            }
        )
    elif preferred_strategy_key == "repair_soft_reentry":
        state.update(
            {
                "ritual_mode": "continuity_nudge",
                "delivery_mode": "single_message",
                "strategy_key": "repair_soft_reentry",
                "relational_move": "repair_bridge",
                "pressure_mode": "repair_soft",
                "autonomy_signal": "explicit_no_pressure",
                "sequence_objective": "reconnect_without_relational_demand",
                "segment_labels": ["check_in"],
                "tone": "repair_aware",
                "closing_hint": (
                    "reduce pressure, keep the bridge open, and avoid demanding a reply."
                ),
            }
        )


def _apply_directive_style_reengagement_overrides(
    state: dict[str, Any],
    *,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    preferred_strategy_key: str | None,
) -> None:
    if directive.style == "progress_nudge":
        state.update(
            {
                "ritual_mode": "progress_reanchor",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "progress_micro_commitment",
                "relational_move": "goal_reconnect",
                "pressure_mode": "low_pressure_progress",
                "autonomy_signal": "explicit_opt_out",
                "sequence_objective": "reconnect_then_tiny_step",
                "segment_labels": ["reconnect", "next_step"],
                "closing_hint": "offer one tiny next action and keep autonomy explicit.",
            }
        )
        state["focus_points"].append("re-anchor_the_open_loop")
    elif directive.style == "grounded_check_in":
        state.update(
            {
                "ritual_mode": "grounding_reentry",
                "tone": "grounding",
                "strategy_key": "grounding_then_resume",
                "relational_move": "stabilize_then_resume",
                "pressure_mode": "ultra_low_pressure",
                "autonomy_signal": "no_reply_required",
                "sequence_objective": "ground_then_steady_step",
                "segment_labels": ["grounding", "steady_step"],
            }
        )
        state["focus_points"].append("reduce_activation_before_progress")
        if runtime_coordination_snapshot.somatic_cue is not None:
            state["delivery_mode"] = "two_part_sequence"
    elif (
        preferred_strategy_key is None
        and runtime_coordination_snapshot.time_awareness_mode in {"resume", "reengagement"}
    ):
        state.update(
            {
                "ritual_mode": "resume_reanchor",
                "strategy_key": "resume_context_bridge",
                "relational_move": "context_bridge",
                "pressure_mode": "gentle_resume",
                "autonomy_signal": "light_invitation",
                "sequence_objective": "re_anchor_then_continue",
                "segment_labels": ["re_anchor", "continuity"],
                "delivery_mode": "two_part_sequence",
            }
        )


def _apply_guidance_reengagement_overrides(
    state: dict[str, Any],
    *,
    guidance_plan: GuidancePlan,
    preferred_strategy_key: str | None,
) -> None:
    if (
        preferred_strategy_key is None
        and guidance_plan.mode == "reanchor_guidance"
        and state["strategy_key"] == "continuity_soft_ping"
    ):
        state.update(
            {
                "ritual_mode": "resume_reanchor",
                "delivery_mode": "two_part_sequence",
                "strategy_key": "resume_context_bridge",
                "relational_move": "context_bridge",
                "pressure_mode": "gentle_resume",
                "autonomy_signal": "light_invitation",
                "sequence_objective": "re_anchor_then_continue",
                "segment_labels": ["re_anchor", "continuity"],
            }
        )
    elif guidance_plan.mode == "stabilizing_guidance":
        state["pressure_mode"] = "ultra_low_pressure"
        state["autonomy_signal"] = "no_reply_required"
        state["focus_points"].append("slow_the_reentry")
    elif guidance_plan.mode == "repair_guidance":
        state["relational_move"] = "repair_bridge"
        state["pressure_mode"] = "repair_soft"
        state["autonomy_signal"] = "explicit_no_pressure"
    elif guidance_plan.mode == "boundary_guidance":
        state["pressure_mode"] = "repair_soft"
        state["autonomy_signal"] = "explicit_no_pressure"
    elif guidance_plan.agency_mode == "explicit_autonomy":
        state["autonomy_signal"] = "explicit_no_pressure"
    elif guidance_plan.agency_mode == "light_reentry":
        state["autonomy_signal"] = "light_invitation"
    elif guidance_plan.agency_mode == "low_pressure_invitation":
        state["autonomy_signal"] = "no_reply_required"

    state["focus_points"].append(f"guidance:{guidance_plan.mode}")
    state["focus_points"].append(f"handoff:{guidance_plan.handoff_mode}")


def _apply_cadence_and_ritual_reengagement_overrides(
    state: dict[str, Any],
    *,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
) -> None:
    state["focus_points"].append(f"cadence:{cadence_plan.status}")
    state["focus_points"].append(f"ritual:{session_ritual_plan.phase}")

    if cadence_plan.turn_shape in {"reanchor_then_step", "reflect_then_step"}:
        state["delivery_mode"] = "two_part_sequence"
    elif cadence_plan.turn_shape == "question_then_pause":
        state["delivery_mode"] = "single_message"
        state["sequence_objective"] = "wait_for_user_detail_before_reopening"
    if cadence_plan.somatic_track != "none":
        state["tone"] = "grounding" if state["tone"] == "gentle" else state["tone"]
        if state["delivery_mode"] != "two_part_sequence":
            state["delivery_mode"] = "two_part_sequence"
    if cadence_plan.user_space_mode in {"spacious", "explicit_autonomy_space"}:
        state["autonomy_signal"] = "explicit_no_pressure"
    if session_ritual_plan.closing_move in {
        "grounding_close",
        "repair_soft_close",
        "boundary_safe_close",
    }:
        state["autonomy_signal"] = "explicit_no_pressure"
    if session_ritual_plan.opening_move in {
        "shared_context_bridge",
        "reflective_restate",
    }:
        state["delivery_mode"] = "two_part_sequence"


def _apply_system3_reengagement_overrides(
    state: dict[str, Any],
    *,
    system3_snapshot: System3Snapshot,
) -> None:
    if system3_snapshot.emotional_debt_status in {"watch", "elevated"}:
        state["tone"] = "repair_aware"
        state["relational_move"] = "repair_bridge"
        state["pressure_mode"] = "repair_soft"
        state["autonomy_signal"] = "explicit_no_pressure"
        state["focus_points"].append("avoid_adding_relational_pressure")
    if system3_snapshot.strategy_audit_status in {"watch", "revise"}:
        state["relational_move"] = "repair_bridge"
        state["pressure_mode"] = "repair_soft"
        state["autonomy_signal"] = "explicit_no_pressure"
        state["focus_points"].append("keep_followup_low_assumption")


def _finalize_reengagement_plan_state(state: dict[str, Any]) -> None:
    if state["relational_move"] == "repair_bridge":
        if state["strategy_key"] == "progress_micro_commitment":
            state["strategy_key"] = "repair_soft_progress_reentry"
        elif state["strategy_key"] == "resume_context_bridge":
            state["strategy_key"] = "repair_soft_resume_bridge"
        else:
            state["strategy_key"] = "repair_soft_reentry"
        state["sequence_objective"] = "reconnect_without_relational_demand"
        state["closing_hint"] = (
            "reduce pressure, keep the bridge open, and avoid demanding a reply."
        )


def build_reengagement_learning_context_stratum(
    *,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    system3_snapshot: System3Snapshot,
) -> str:
    flags: list[str] = []
    if (
        guidance_plan.mode in {"repair_guidance", "boundary_guidance"}
        or system3_snapshot.repair_governance_status in {"watch", "revise"}
        or system3_snapshot.repair_governance_trajectory_status == "recenter"
        or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
        or session_ritual_plan.closing_move == "repair_soft_close"
    ):
        flags.append("repair_pressure")
    if (
        guidance_plan.mode == "boundary_guidance"
        or system3_snapshot.boundary_governance_status in {"watch", "revise"}
        or system3_snapshot.boundary_governance_trajectory_status == "recenter"
    ):
        flags.append("boundary_pressure")
    if (
        system3_snapshot.dependency_governance_status in {"watch", "revise"}
        or system3_snapshot.dependency_governance_trajectory_status == "recenter"
        or cadence_plan.user_space_mode == "explicit_autonomy_space"
    ):
        flags.append("dependency_pressure")
    if (
        system3_snapshot.pressure_governance_status in {"watch", "revise"}
        or system3_snapshot.stability_governance_status in {"watch", "revise"}
        or runtime_coordination_snapshot.cognitive_load_band == "high"
        or directive.style == "grounded_check_in"
    ):
        flags.append("quality_watch")
    if not flags:
        flags.append("steady_progress")
    return "+".join(flags[:3])


def build_reengagement_matrix_assessment(
    *,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    system3_snapshot: System3Snapshot,
    reengagement_learning_report: dict[str, Any] | None = None,
    dispatch_outcome_learning_report: dict[str, Any] | None = None,
) -> ReengagementMatrixAssessment:
    learning_context_stratum = build_reengagement_learning_context_stratum(
        directive=directive,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        guidance_plan=guidance_plan,
        cadence_plan=cadence_plan,
        session_ritual_plan=session_ritual_plan,
        system3_snapshot=system3_snapshot,
    )
    if directive.status != "ready" or not directive.eligible:
        return ReengagementMatrixAssessment(
            status="hold",
            matrix_key="hold",
            selected_strategy_key="hold",
            selected_score=0.0,
            learning_mode="hold",
            learning_context_stratum=learning_context_stratum,
            rationale=directive.rationale,
        )

    repair_context = (
        guidance_plan.mode in {"repair_guidance", "boundary_guidance"}
        or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
        or system3_snapshot.strategy_audit_status in {"watch", "revise"}
    )
    learning_report = dict(reengagement_learning_report or {})
    learning_state = _build_learning_signal_state(
        learning_report=learning_report,
        learning_context_stratum=learning_context_stratum,
    )
    outcome_report = dict(dispatch_outcome_learning_report or {})
    outcome_signals = _build_outcome_signal_state(outcome_report)
    total_dispatches = int(outcome_report.get("total_dispatches") or 0)
    candidates: list[ReengagementStrategyCandidate] = []

    for strategy_key, profile in _REENGAGEMENT_CANDIDATE_PROFILES.items():
        candidates.append(
            _score_reengagement_candidate(
                strategy_key=strategy_key,
                profile=profile,
                directive=directive,
                runtime_coordination_snapshot=runtime_coordination_snapshot,
                guidance_plan=guidance_plan,
                cadence_plan=cadence_plan,
                session_ritual_plan=session_ritual_plan,
                system3_snapshot=system3_snapshot,
                repair_context=repair_context,
                learning_signals=dict(learning_state["learning_signals"]),
                learning_signal_count=int(learning_state["learning_signal_count"]),
                outcome_signals=outcome_signals,
                total_dispatches=total_dispatches,
            )
        )

    ranked = _materialize_ranked_reengagement_candidates(candidates)
    learning_mode = _resolve_reengagement_learning_mode(
        list(ranked["materialized_candidates"])
    )
    return ReengagementMatrixAssessment(
        status="active",
        matrix_key=f"{directive.style or 'continuity'}_reengagement_matrix",
        selected_strategy_key=str(ranked["selected_key"]),
        selected_score=ranked["selected"].suitability_score,
        blocked_count=int(ranked["blocked_count"]),
        learning_mode=learning_mode,
        learning_context_stratum=learning_context_stratum,
        learning_signal_count=int(learning_state["learning_signal_count"]),
        candidates=list(ranked["materialized_candidates"]),
        learning_notes=_compact(list(learning_state["learning_notes"]), limit=4),
        rationale=directive.rationale,
    )


def build_reengagement_plan(
    *,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    system3_snapshot: System3Snapshot,
    reengagement_matrix_assessment: ReengagementMatrixAssessment | None = None,
) -> ReengagementPlan:
    if directive.status != "ready" or not directive.eligible:
        return ReengagementPlan(
            status="hold",
            ritual_mode="hold",
            delivery_mode="none",
            strategy_key="hold",
            relational_move="hold",
            pressure_mode="hold",
            autonomy_signal="none",
            sequence_objective="wait_until_regulation_is_stable",
            focus_points=_compact(directive.hold_reasons, limit=3),
            rationale=directive.rationale,
        )

    preferred_strategy_key = (
        reengagement_matrix_assessment.selected_strategy_key
        if reengagement_matrix_assessment is not None
        and reengagement_matrix_assessment.status == "active"
        and reengagement_matrix_assessment.selected_strategy_key
        not in {"", "hold"}
        else None
    )
    state = _build_reengagement_plan_state(
        directive=directive,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
    )
    _apply_preferred_reengagement_strategy(
        state,
        preferred_strategy_key=preferred_strategy_key,
    )
    _apply_directive_style_reengagement_overrides(
        state,
        directive=directive,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        preferred_strategy_key=preferred_strategy_key,
    )
    _apply_guidance_reengagement_overrides(
        state,
        guidance_plan=guidance_plan,
        preferred_strategy_key=preferred_strategy_key,
    )
    _apply_cadence_and_ritual_reengagement_overrides(
        state,
        cadence_plan=cadence_plan,
        session_ritual_plan=session_ritual_plan,
    )
    _apply_system3_reengagement_overrides(
        state,
        system3_snapshot=system3_snapshot,
    )
    _finalize_reengagement_plan_state(state)

    return ReengagementPlan(
        status="ready",
        ritual_mode=str(state["ritual_mode"]),
        delivery_mode=str(state["delivery_mode"]),
        strategy_key=str(state["strategy_key"]),
        relational_move=str(state["relational_move"]),
        pressure_mode=str(state["pressure_mode"]),
        autonomy_signal=str(state["autonomy_signal"]),
        sequence_objective=str(state["sequence_objective"]),
        somatic_action=state["somatic_action"],
        segment_labels=_compact(list(state["segment_labels"]), limit=3),
        focus_points=_compact(list(state["focus_points"]), limit=5),
        tone=str(state["tone"]),
        opening_hint=str(state["opening_hint"]),
        closing_hint=str(state["closing_hint"]),
        rationale=directive.rationale,
    )


def _infer_reengagement_somatic_action(somatic_cue: str | None) -> str | None:
    if somatic_cue == "breath":
        return "take_one_slower_breath"
    if somatic_cue == "fatigue":
        return "drop_shoulders_and_exhale"
    if somatic_cue == "tension":
        return "unclench_jaw_and_shoulders"
    return None
