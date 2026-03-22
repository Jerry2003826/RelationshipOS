"""Re-engagement assessment and planning."""

from __future__ import annotations

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

    candidate_profiles = {
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
    repair_context = (
        guidance_plan.mode in {"repair_guidance", "boundary_guidance"}
        or system3_snapshot.emotional_debt_status in {"watch", "elevated"}
        or system3_snapshot.strategy_audit_status in {"watch", "revise"}
    )
    learning_report = dict(reengagement_learning_report or {})
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
    candidates: list[ReengagementStrategyCandidate] = []

    for strategy_key, profile in candidate_profiles.items():
        score = 0.25
        blocked = False
        reasons = [f"base:{directive.style or 'continuity'}"]
        supporting_session_count = 0
        contextual_supporting_session_count = 0
        historical_preference_score: float | None = None
        contextual_preference_score: float | None = None
        exploration_bonus = 0.0

        if directive.style == "progress_nudge":
            if strategy_key == "progress_micro_commitment":
                score += 0.45
                reasons.append("fits_progress_nudge")
            elif strategy_key == "repair_soft_progress_reentry":
                score += 0.25
                reasons.append("repair_safe_progress_variant")
            elif strategy_key == "resume_context_bridge":
                score += 0.15
            elif strategy_key == "grounding_then_resume":
                score -= 0.1
        elif directive.style == "grounded_check_in":
            if strategy_key == "grounding_then_resume":
                score += 0.45
                reasons.append("fits_grounded_check_in")
            elif strategy_key == "repair_soft_reentry":
                score += 0.15
            elif strategy_key == "progress_micro_commitment":
                score -= 0.15
        else:
            if strategy_key == "continuity_soft_ping":
                score += 0.2
                reasons.append("default_continuity_fit")

        if runtime_coordination_snapshot.time_awareness_mode in {"resume", "reengagement"}:
            if strategy_key in {"resume_context_bridge", "repair_soft_resume_bridge"}:
                score += 0.35
                reasons.append("resume_context_match")

        if guidance_plan.mode == "reanchor_guidance":
            if strategy_key in {"resume_context_bridge", "repair_soft_resume_bridge"}:
                score += 0.25
                reasons.append("guidance_reanchor")
        elif guidance_plan.mode == "stabilizing_guidance":
            if strategy_key == "grounding_then_resume":
                score += 0.25
                reasons.append("guidance_stabilize")
            elif strategy_key == "progress_micro_commitment":
                score -= 0.15
        elif guidance_plan.mode in {"repair_guidance", "boundary_guidance"}:
            if strategy_key.startswith("repair_soft"):
                score += 0.35
                reasons.append("guidance_repair")
            elif strategy_key in {"progress_micro_commitment", "resume_context_bridge"}:
                score -= 0.2

        if cadence_plan.turn_shape in {"reanchor_then_step", "reflect_then_step"}:
            if profile["delivery_mode_hint"] == "two_part_sequence":
                score += 0.1
                reasons.append("cadence_two_part")
        elif cadence_plan.turn_shape == "question_then_pause":
            if strategy_key == "continuity_soft_ping":
                score += 0.1

        if cadence_plan.user_space_mode in {"spacious", "explicit_autonomy_space"}:
            if profile["autonomy_signal"] in {"explicit_no_pressure", "explicit_opt_out"}:
                score += 0.1
                reasons.append("user_space_autonomy")

        if session_ritual_plan.closing_move in {
            "repair_soft_close",
            "boundary_safe_close",
            "grounding_close",
        }:
            if strategy_key.startswith("repair_soft") or strategy_key == "grounding_then_resume":
                score += 0.15
            elif strategy_key == "progress_micro_commitment":
                score -= 0.1

        if repair_context:
            if strategy_key.startswith("repair_soft"):
                score += 0.3
                reasons.append("repair_context_bias")
            elif strategy_key in {"progress_micro_commitment", "resume_context_bridge"}:
                score -= 0.25

        if system3_snapshot.emotional_debt_status == "elevated" and strategy_key in {
            "progress_micro_commitment",
            "resume_context_bridge",
        }:
            blocked = True
            reasons.append("blocked_by_emotional_debt")
        if (
            system3_snapshot.strategy_audit_status == "revise"
            and profile["pressure_mode"] not in {"repair_soft", "ultra_low_pressure"}
        ):
            blocked = True
            reasons.append("blocked_by_strategy_audit")

        learning_signal = learning_signals.get(strategy_key) or {}
        if learning_signal:
            supporting_session_count = max(
                0,
                int(learning_signal.get("kept_session_count") or 0),
            )
            contextual_supporting_session_count = max(
                0,
                int(learning_signal.get("contextual_kept_session_count") or 0),
            )
            if learning_signal.get("avg_learning_score") is not None:
                historical_preference_score = float(
                    learning_signal.get("avg_learning_score") or 0.0
                )
            if learning_signal.get("avg_contextual_learning_score") is not None:
                contextual_preference_score = float(
                    learning_signal.get("avg_contextual_learning_score") or 0.0
                )

            effective_preference_score = (
                contextual_preference_score
                if contextual_preference_score is not None
                and contextual_supporting_session_count > 0
                else historical_preference_score
            )
            effective_support_count = (
                contextual_supporting_session_count
                if contextual_supporting_session_count > 0
                else supporting_session_count
            )
            if effective_preference_score is not None and effective_support_count > 0:
                learning_weight = min(0.18, 0.06 * effective_support_count)
                score += (effective_preference_score - 0.5) * learning_weight * 2.0
                reasons.append(
                    "learning_contextual"
                    if contextual_supporting_session_count > 0
                    else "learning_global"
                )
        elif learning_signal_count > 0 and profile["pressure_mode"] in {
            "low_pressure_presence",
            "ultra_low_pressure",
            "repair_soft",
        }:
            exploration_bonus = 0.03
            score += exploration_bonus
            reasons.append("safe_exploration")

        candidates.append(
            ReengagementStrategyCandidate(
                strategy_key=strategy_key,
                suitability_score=round(max(0.0, min(score, 1.0)), 3),
                relational_move=str(profile["relational_move"]),
                pressure_mode=str(profile["pressure_mode"]),
                autonomy_signal=str(profile["autonomy_signal"]),
                delivery_mode_hint=str(profile["delivery_mode_hint"]),
                blocked=blocked,
                supporting_session_count=supporting_session_count,
                contextual_supporting_session_count=contextual_supporting_session_count,
                historical_preference_score=(
                    round(historical_preference_score, 3)
                    if historical_preference_score is not None
                    else None
                ),
                contextual_preference_score=(
                    round(contextual_preference_score, 3)
                    if contextual_preference_score is not None
                    else None
                ),
                exploration_bonus=round(exploration_bonus, 3),
                rationale="; ".join(reasons[:6]),
            )
        )

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
    selected_candidate = next(
        (item for item in materialized_candidates if item.selected),
        materialized_candidates[0] if materialized_candidates else None,
    )
    learning_mode = "cold_start"
    if selected_candidate is not None:
        if selected_candidate.contextual_supporting_session_count > 0:
            learning_mode = "contextual_reinforcement"
        elif selected_candidate.supporting_session_count > 0:
            learning_mode = "global_reinforcement"
        elif selected_candidate.exploration_bonus > 0:
            learning_mode = "safe_exploration"
    return ReengagementMatrixAssessment(
        status="active",
        matrix_key=f"{directive.style or 'continuity'}_reengagement_matrix",
        selected_strategy_key=selected_key,
        selected_score=selected.suitability_score,
        blocked_count=blocked_count,
        learning_mode=learning_mode,
        learning_context_stratum=learning_context_stratum,
        learning_signal_count=learning_signal_count,
        candidates=materialized_candidates,
        learning_notes=_compact(learning_notes, limit=4),
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
    ritual_mode = "continuity_nudge"
    delivery_mode = "single_message"
    strategy_key = "continuity_soft_ping"
    relational_move = "continuity_ping"
    pressure_mode = "low_pressure_presence"
    autonomy_signal = "open_loop_without_demand"
    sequence_objective = "presence_then_optional_reply"
    somatic_action = _infer_reengagement_somatic_action(
        runtime_coordination_snapshot.somatic_cue
    )
    segment_labels = ["check_in"]
    focus_points = list(directive.trigger_conditions)
    tone = "gentle"
    opening_hint = directive.opening_hint
    closing_hint = "leave room for the user to re-enter without pressure."

    if preferred_strategy_key == "progress_micro_commitment":
        ritual_mode = "progress_reanchor"
        delivery_mode = "two_part_sequence"
        strategy_key = "progress_micro_commitment"
        relational_move = "goal_reconnect"
        pressure_mode = "low_pressure_progress"
        autonomy_signal = "explicit_opt_out"
        sequence_objective = "reconnect_then_tiny_step"
        segment_labels = ["reconnect", "next_step"]
        closing_hint = "offer one tiny next action and keep autonomy explicit."
    elif preferred_strategy_key == "grounding_then_resume":
        ritual_mode = "grounding_reentry"
        delivery_mode = "two_part_sequence"
        strategy_key = "grounding_then_resume"
        relational_move = "stabilize_then_resume"
        pressure_mode = "ultra_low_pressure"
        autonomy_signal = "no_reply_required"
        sequence_objective = "ground_then_steady_step"
        segment_labels = ["grounding", "steady_step"]
        tone = "grounding"
    elif preferred_strategy_key == "resume_context_bridge":
        ritual_mode = "resume_reanchor"
        delivery_mode = "two_part_sequence"
        strategy_key = "resume_context_bridge"
        relational_move = "context_bridge"
        pressure_mode = "gentle_resume"
        autonomy_signal = "light_invitation"
        sequence_objective = "re_anchor_then_continue"
        segment_labels = ["re_anchor", "continuity"]
    elif preferred_strategy_key == "repair_soft_progress_reentry":
        ritual_mode = "progress_reanchor"
        delivery_mode = "two_part_sequence"
        strategy_key = "repair_soft_progress_reentry"
        relational_move = "repair_bridge"
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
        sequence_objective = "reconnect_without_relational_demand"
        segment_labels = ["reconnect", "next_step"]
        tone = "repair_aware"
        closing_hint = (
            "reduce pressure, keep the bridge open, and avoid demanding a reply."
        )
    elif preferred_strategy_key == "repair_soft_resume_bridge":
        ritual_mode = "resume_reanchor"
        delivery_mode = "two_part_sequence"
        strategy_key = "repair_soft_resume_bridge"
        relational_move = "repair_bridge"
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
        sequence_objective = "reconnect_without_relational_demand"
        segment_labels = ["re_anchor", "continuity"]
        tone = "repair_aware"
        closing_hint = (
            "reduce pressure, keep the bridge open, and avoid demanding a reply."
        )
    elif preferred_strategy_key == "repair_soft_reentry":
        ritual_mode = "continuity_nudge"
        delivery_mode = "single_message"
        strategy_key = "repair_soft_reentry"
        relational_move = "repair_bridge"
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
        sequence_objective = "reconnect_without_relational_demand"
        segment_labels = ["check_in"]
        tone = "repair_aware"
        closing_hint = (
            "reduce pressure, keep the bridge open, and avoid demanding a reply."
        )

    if directive.style == "progress_nudge":
        ritual_mode = "progress_reanchor"
        delivery_mode = "two_part_sequence"
        strategy_key = "progress_micro_commitment"
        relational_move = "goal_reconnect"
        pressure_mode = "low_pressure_progress"
        autonomy_signal = "explicit_opt_out"
        sequence_objective = "reconnect_then_tiny_step"
        segment_labels = ["reconnect", "next_step"]
        focus_points.append("re-anchor_the_open_loop")
        closing_hint = "offer one tiny next action and keep autonomy explicit."
    elif directive.style == "grounded_check_in":
        ritual_mode = "grounding_reentry"
        tone = "grounding"
        strategy_key = "grounding_then_resume"
        relational_move = "stabilize_then_resume"
        pressure_mode = "ultra_low_pressure"
        autonomy_signal = "no_reply_required"
        sequence_objective = "ground_then_steady_step"
        segment_labels = ["grounding", "steady_step"]
        focus_points.append("reduce_activation_before_progress")
        if runtime_coordination_snapshot.somatic_cue is not None:
            delivery_mode = "two_part_sequence"
    elif (
        preferred_strategy_key is None
        and runtime_coordination_snapshot.time_awareness_mode
        in {"resume", "reengagement"}
    ):
        ritual_mode = "resume_reanchor"
        strategy_key = "resume_context_bridge"
        relational_move = "context_bridge"
        pressure_mode = "gentle_resume"
        autonomy_signal = "light_invitation"
        sequence_objective = "re_anchor_then_continue"
        segment_labels = ["re_anchor", "continuity"]
        delivery_mode = "two_part_sequence"

    if (
        preferred_strategy_key is None
        and guidance_plan.mode == "reanchor_guidance"
        and strategy_key == "continuity_soft_ping"
    ):
        ritual_mode = "resume_reanchor"
        delivery_mode = "two_part_sequence"
        strategy_key = "resume_context_bridge"
        relational_move = "context_bridge"
        pressure_mode = "gentle_resume"
        autonomy_signal = "light_invitation"
        sequence_objective = "re_anchor_then_continue"
        segment_labels = ["re_anchor", "continuity"]
    elif guidance_plan.mode == "stabilizing_guidance":
        pressure_mode = "ultra_low_pressure"
        autonomy_signal = "no_reply_required"
        focus_points.append("slow_the_reentry")
    elif guidance_plan.mode == "repair_guidance":
        relational_move = "repair_bridge"
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
    elif guidance_plan.mode == "boundary_guidance":
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
    elif guidance_plan.agency_mode == "explicit_autonomy":
        autonomy_signal = "explicit_no_pressure"
    elif guidance_plan.agency_mode == "light_reentry":
        autonomy_signal = "light_invitation"
    elif guidance_plan.agency_mode == "low_pressure_invitation":
        autonomy_signal = "no_reply_required"

    focus_points.append(f"guidance:{guidance_plan.mode}")
    focus_points.append(f"handoff:{guidance_plan.handoff_mode}")
    focus_points.append(f"cadence:{cadence_plan.status}")
    focus_points.append(f"ritual:{session_ritual_plan.phase}")

    if cadence_plan.turn_shape in {"reanchor_then_step", "reflect_then_step"}:
        delivery_mode = "two_part_sequence"
    elif cadence_plan.turn_shape == "question_then_pause":
        delivery_mode = "single_message"
        sequence_objective = "wait_for_user_detail_before_reopening"
    if cadence_plan.somatic_track != "none":
        tone = "grounding" if tone == "gentle" else tone
        if delivery_mode != "two_part_sequence":
            delivery_mode = "two_part_sequence"
    if cadence_plan.user_space_mode in {"spacious", "explicit_autonomy_space"}:
        autonomy_signal = "explicit_no_pressure"
    if session_ritual_plan.closing_move in {
        "grounding_close",
        "repair_soft_close",
        "boundary_safe_close",
    }:
        autonomy_signal = "explicit_no_pressure"
    if session_ritual_plan.opening_move in {"shared_context_bridge", "reflective_restate"}:
        delivery_mode = "two_part_sequence"

    if system3_snapshot.emotional_debt_status in {"watch", "elevated"}:
        tone = "repair_aware"
        relational_move = "repair_bridge"
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
        focus_points.append("avoid_adding_relational_pressure")
    if system3_snapshot.strategy_audit_status in {"watch", "revise"}:
        relational_move = "repair_bridge"
        pressure_mode = "repair_soft"
        autonomy_signal = "explicit_no_pressure"
        focus_points.append("keep_followup_low_assumption")
    if relational_move == "repair_bridge":
        if strategy_key == "progress_micro_commitment":
            strategy_key = "repair_soft_progress_reentry"
        elif strategy_key == "resume_context_bridge":
            strategy_key = "repair_soft_resume_bridge"
        else:
            strategy_key = "repair_soft_reentry"
        sequence_objective = "reconnect_without_relational_demand"
        closing_hint = "reduce pressure, keep the bridge open, and avoid demanding a reply."

    return ReengagementPlan(
        status="ready",
        ritual_mode=ritual_mode,
        delivery_mode=delivery_mode,
        strategy_key=strategy_key,
        relational_move=relational_move,
        pressure_mode=pressure_mode,
        autonomy_signal=autonomy_signal,
        sequence_objective=sequence_objective,
        somatic_action=somatic_action,
        segment_labels=_compact(segment_labels, limit=3),
        focus_points=_compact(focus_points, limit=5),
        tone=tone,
        opening_hint=opening_hint,
        closing_hint=closing_hint,
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
