"""Re-engagement assessment, planning, and message generation."""

from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers._utils import _compact, _contains_chinese
from relationship_os.domain.contracts import (
    ConversationCadencePlan,
    GuidancePlan,
    ProactiveFollowupDirective,
    ReengagementMatrixAssessment,
    ReengagementPlan,
    ReengagementStrategyCandidate,
    RuntimeCoordinationSnapshot,
    SessionRitualPlan,
    SomaticOrchestrationPlan,
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


def _render_reengagement_autonomy_line(
    *,
    reengagement_plan: ReengagementPlan,
    use_chinese: bool,
) -> str:
    if reengagement_plan.autonomy_signal == "explicit_opt_out":
        return (
            "不需要现在就回复。"
            if use_chinese
            else "No need to reply right away."
        )
    if reengagement_plan.autonomy_signal == "no_reply_required":
        return (
            "如果现在不想接也完全没关系。"
            if use_chinese
            else "No reply needed unless it genuinely helps."
        )
    if reengagement_plan.autonomy_signal == "light_invitation":
        return (
            "如果你想接回来，我们就从这里继续。"
            if use_chinese
            else "If it helps, we can pick it back up from here."
        )
    if reengagement_plan.autonomy_signal == "explicit_no_pressure":
        return (
            "没有要你立刻接住它的意思。"
            if use_chinese
            else "There is no pressure to pick this up immediately."
        )
    if reengagement_plan.autonomy_signal == "open_loop_without_demand":
        return (
            "只是先把线轻轻留在这里。"
            if use_chinese
            else "Just leaving the thread open, not demanding anything."
        )
    return ""


def _render_reengagement_somatic_line(
    *,
    reengagement_plan: ReengagementPlan,
    use_chinese: bool,
) -> str:
    if reengagement_plan.somatic_action == "take_one_slower_breath":
        return (
            "先让呼吸慢一格也可以。"
            if use_chinese
            else "You can let one breath slow down first."
        )
    if reengagement_plan.somatic_action == "drop_shoulders_and_exhale":
        return (
            "先把肩膀放下来，慢慢吐一口气也可以。"
            if use_chinese
            else "You can drop your shoulders and exhale once before we restart."
        )
    if reengagement_plan.somatic_action == "unclench_jaw_and_shoulders":
        return (
            "先把下巴和肩膀松一点也可以。"
            if use_chinese
            else "You can unclench your jaw and shoulders a little first."
        )
    return ""


def _render_somatic_orchestration_line(
    *,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    use_chinese: bool,
) -> str:
    if somatic_orchestration_plan.status != "active":
        return ""
    if somatic_orchestration_plan.body_anchor == "one_slower_breath":
        return (
            "先让一口气慢下来就可以。"
            if use_chinese
            else "You can let one breath slow down first."
        )
    if somatic_orchestration_plan.body_anchor == "drop_shoulders_and_exhale":
        return (
            "先把肩膀放下来，再慢慢吐一口气就可以。"
            if use_chinese
            else "You can drop your shoulders and exhale once first."
        )
    if somatic_orchestration_plan.body_anchor == "unclench_jaw_and_shoulders":
        return (
            "先把下巴和肩膀松一点就可以。"
            if use_chinese
            else "You can unclench your jaw and shoulders a little first."
        )
    return (
        "先让身体和节奏稳一格就可以。"
        if use_chinese
        else "You can let your body and pace settle one notch first."
    )


def _render_session_ritual_opening_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.opening_move == "warm_orientation":
        return (
            "我先轻轻定一下这轮的节奏。"
            if use_chinese
            else "Let me gently set the frame for this turn."
        )
    if session_ritual_plan.opening_move == "shared_context_bridge":
        return (
            "我先把我们刚才的上下文轻轻接回来。"
            if use_chinese
            else "Let me lightly reconnect the context we were holding."
        )
    if session_ritual_plan.opening_move == "attunement_repair":
        return (
            "我先把理解和连接接稳一点。"
            if use_chinese
            else "Let me steady the connection and understanding first."
        )
    if session_ritual_plan.opening_move == "clarity_frame":
        return (
            "我先把缺的那个关键点框出来。"
            if use_chinese
            else "Let me frame the one missing detail first."
        )
    if session_ritual_plan.opening_move == "regulate_first":
        return (
            "我先帮我们把节奏放慢一点。"
            if use_chinese
            else "Let me slow the pace down first."
        )
    if session_ritual_plan.opening_move == "reflective_restate":
        return (
            "我先把你现在的位置轻轻照一下。"
            if use_chinese
            else "Let me briefly reflect where you are before we move."
        )
    return ""


def _render_session_ritual_bridge_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.bridge_move == "frame_the_session":
        return (
            "这一拍我们只先把范围和步子定小一点。"
            if use_chinese
            else "For this touch, we can keep the frame small and the step light."
        )
    if session_ritual_plan.bridge_move == "resume_the_open_loop":
        return (
            "我先顺着上次停住的那一点轻轻接一下。"
            if use_chinese
            else "I'll lightly pick up the small open loop we paused on."
        )
    if session_ritual_plan.bridge_move == "repair_before_progress":
        return (
            "先把理解和连接放稳，再看要不要往前。"
            if use_chinese
            else "We can steady the understanding first, then decide whether to move."
        )
    if session_ritual_plan.bridge_move == "single_question_pause":
        return (
            "这一拍只放一个很小的问题口。"
            if use_chinese
            else "This touch only opens one very small question."
        )
    if session_ritual_plan.bridge_move == "ground_then_step":
        return (
            "先把节奏落下来，再看最小的下一步。"
            if use_chinese
            else "We can let the pace settle first, then look at the smallest next step."
        )
    if session_ritual_plan.bridge_move == "reflect_then_step":
        return (
            "我先照一下你现在的位置，再接下一步。"
            if use_chinese
            else "I'll reflect where you are first, then bridge to the next step."
        )
    if session_ritual_plan.bridge_move == "micro_step_bridge":
        return (
            "就先接一个最小、最容易做的动作。"
            if use_chinese
            else "We can bridge back with the smallest, easiest move."
        )
    return ""


def _render_session_ritual_closing_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.closing_move == "progress_invitation":
        return (
            "如果你愿意，我们下一拍就接最小的那一步。"
            if use_chinese
            else "If it helps, we can pick up the smallest next step from here."
        )
    if session_ritual_plan.closing_move == "resume_ping":
        return (
            "下一拍我们就从这条线轻轻接回来。"
            if use_chinese
            else "Next time, we can lightly pick the thread back up from here."
        )
    if session_ritual_plan.closing_move == "repair_soft_close":
        return (
            "这条线先放在这里，不需要你现在立刻接住。"
            if use_chinese
            else "We can leave the thread here without needing you to pick it up right now."
        )
    if session_ritual_plan.closing_move == "clarify_pause":
        return (
            "我们先停在这个问题上，等你愿意再补那一点信息。"
            if use_chinese
            else "We can pause here and wait for that one missing detail when you're ready."
        )
    if session_ritual_plan.closing_move == "grounding_close":
        return (
            "先把身体和节奏稳住就已经算往前了。"
            if use_chinese
            else "Letting your body and pace settle first already counts as forward motion."
        )
    if session_ritual_plan.closing_move == "boundary_safe_close":
        return (
            "你可以自己决定要不要接这一步。"
            if use_chinese
            else "You get to decide whether to pick this step up."
        )
    return ""


def _render_user_space_signal_line(
    *,
    user_space_signal: str,
    use_chinese: bool,
) -> str:
    if user_space_signal == "explicit_no_pressure":
        return (
            "这条线先放着也完全可以，不需要现在接住。"
            if use_chinese
            else "It is completely okay to leave this thread where it is for now."
        )
    if user_space_signal == "archive_light_thread":
        return (
            "我先把这条线轻轻留着，不往你这边推。"
            if use_chinese
            else "I'll leave this thread lightly parked without pushing it toward you."
        )
    if user_space_signal == "open_loop_without_demand":
        return (
            "我只把门轻轻开着，不会要求你现在回应。"
            if use_chinese
            else "I'll just leave the door lightly open without asking you to answer now."
        )
    return ""


def _render_continuity_anchor_line(
    *,
    session_ritual_plan: SessionRitualPlan,
    use_chinese: bool,
) -> str:
    if session_ritual_plan.continuity_anchor == "shared_context_resume":
        return (
            "我们就顺着刚才那条线最容易接上的地方继续。"
            if use_chinese
            else "We can pick this up from the easiest place on the thread we already had."
        )
    if session_ritual_plan.continuity_anchor == "repair_landing":
        return (
            "就先把这条线放在更稳、更好接住的位置。"
            if use_chinese
            else "We can leave the thread in a steadier place that's easier to return to."
        )
    if session_ritual_plan.continuity_anchor == "grounding_first":
        return (
            "先把节奏稳住，本身就算把这条线接住了。"
            if use_chinese
            else "Letting the pace settle first already counts as holding the thread."
        )
    if session_ritual_plan.continuity_anchor == "thread_left_open":
        return (
            "这条线我先替你轻轻留着，不需要现在接。"
            if use_chinese
            else "I'll leave this thread gently open for you without needing anything now."
        )
    return ""


def build_proactive_followup_message(
    *,
    recent_user_text: str,
    directive: ProactiveFollowupDirective,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot | None,
    question_mode: str = "default",
) -> str:
    if not directive.eligible or directive.status != "ready":
        return ""

    style = directive.style or "light_check_in"
    somatic_cue = (
        runtime_coordination_snapshot.somatic_cue
        if runtime_coordination_snapshot is not None
        else None
    )
    if _contains_chinese(recent_user_text):
        if style == "progress_nudge":
            if question_mode == "statement_only":
                return (
                    "我来轻轻跟进一下这条线。"
                    "如果现在有一点推进空间，只做一个最小动作就够。"
                )
            return (
                "我来轻轻跟进一下：上次那一步现在有一点推进空间了吗？"
                "如果还没开始，也只需要先做一个最小动作就够。"
            )
        if style == "grounded_check_in":
            stabilizer = "先放慢一点、把呼吸和节奏稳住" if somatic_cue else "先把节奏放慢一点"
            if question_mode == "statement_only":
                return (
                    f"我来轻轻接一下这条线。"
                    f"如果当下还是很绷，先{stabilizer}也可以，"
                    "然后只做一个最小、最稳的下一步。"
                )
            return (
                f"我来轻轻看看你现在怎么样。"
                f"如果当下还是很绷，先{stabilizer}也可以，"
                "然后只做一个最小、最稳的下一步。"
            )
        if question_mode == "statement_only":
            return (
                "我来做一个低压力的 continuity check-in。"
                "如果你愿意，我们就只接回上次最小、最容易推进的那一步。"
            )
        return (
            "我来做一个低压力的 continuity check-in。"
            "如果你愿意，我们就只接回上次最小、最容易推进的那一步。"
        )

    if style == "progress_nudge":
        if question_mode == "statement_only":
            return (
                "Quick check-in on the step we left open. If there is any room to move "
                "it, one tiny move is enough."
            )
        return (
            "Quick check-in on the step we left open: is there a tiny bit of movement "
            "available now? If not, the smallest next move still counts."
        )
    if style == "grounded_check_in":
        stabilizer = (
            "slow the pace and steady your breathing first"
            if somatic_cue
            else "slow the pace first"
        )
        if question_mode == "statement_only":
            return (
                "Gentle check-in: if things still feel tense, it is okay to "
                f"{stabilizer}, then choose one small, steady next step."
            )
        return (
            "Gentle check-in: if things still feel tense, it's okay to "
            f"{stabilizer}, then choose one small, steady next step."
        )
    if question_mode == "statement_only":
        return (
            "Light continuity check-in: we can reconnect to the smallest next step "
            "without adding pressure."
        )
    return (
        "Light continuity check-in: if you want to pick this back up, we can just "
        "reconnect to the smallest next step without adding pressure."
    )


def build_reengagement_output_units(
    *,
    recent_user_text: str,
    directive: ProactiveFollowupDirective,
    reengagement_plan: ReengagementPlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    runtime_coordination_snapshot: RuntimeCoordinationSnapshot | None,
    cadence_stage_label: str = "first_touch",
    cadence_stage_index: int = 1,
    cadence_stage_count: int = 1,
    stage_directive: dict[str, object] | None = None,
    stage_actuation: dict[str, object] | None = None,
) -> list[dict[str, str]]:
    if reengagement_plan.status != "ready" or not directive.eligible:
        return []

    use_chinese = _contains_chinese(recent_user_text)
    is_final_touch = (
        cadence_stage_label == "final_soft_close"
        or cadence_stage_index >= cadence_stage_count
    )
    effective_delivery_mode = str(
        (stage_directive or {}).get("delivery_mode") or reengagement_plan.delivery_mode
    )
    question_mode = str(
        (stage_directive or {}).get("question_mode") or "default"
    )
    allow_somatic_carryover = bool(
        (stage_directive or {}).get(
            "allow_somatic_carryover",
            somatic_orchestration_plan.allow_in_followup,
        )
    )
    effective_session_ritual_plan = SessionRitualPlan(
        phase=session_ritual_plan.phase,
        opening_move=str(
            (stage_actuation or {}).get("opening_move") or session_ritual_plan.opening_move
        ),
        bridge_move=str(
            (stage_actuation or {}).get("bridge_move") or session_ritual_plan.bridge_move
        ),
        closing_move=str(
            (stage_actuation or {}).get("closing_move") or session_ritual_plan.closing_move
        ),
        continuity_anchor=str(
            (stage_actuation or {}).get("continuity_anchor")
            or session_ritual_plan.continuity_anchor
        ),
        somatic_shortcut=(
            session_ritual_plan.somatic_shortcut
            if str((stage_actuation or {}).get("somatic_mode") or "none") != "none"
            else "none"
        ),
        micro_rituals=list(session_ritual_plan.micro_rituals),
        rationale=session_ritual_plan.rationale,
    )
    effective_somatic_mode = str(
        (stage_actuation or {}).get("somatic_mode")
        or (
            somatic_orchestration_plan.primary_mode
            if allow_somatic_carryover
            else "none"
        )
    )
    effective_somatic_orchestration_plan = SomaticOrchestrationPlan(
        status=(
            "active"
            if (
                somatic_orchestration_plan.status == "active"
                and effective_somatic_mode != "none"
                and allow_somatic_carryover
            )
            else "not_needed"
        ),
        cue=somatic_orchestration_plan.cue,
        primary_mode=effective_somatic_mode,
        body_anchor=str(
            (stage_actuation or {}).get("somatic_body_anchor")
            or (
                somatic_orchestration_plan.body_anchor
                if allow_somatic_carryover
                else "none"
            )
        ),
        followup_style=str(
            (stage_actuation or {}).get("followup_style")
            or (
                somatic_orchestration_plan.followup_style
                if allow_somatic_carryover
                else "none"
            )
        ),
        allow_in_followup=allow_somatic_carryover,
        micro_actions=(
            list(somatic_orchestration_plan.micro_actions)
            if allow_somatic_carryover and effective_somatic_mode != "none"
            else []
        ),
        phrasing_guardrails=(
            list(somatic_orchestration_plan.phrasing_guardrails)
            if allow_somatic_carryover and effective_somatic_mode != "none"
            else []
        ),
        rationale=somatic_orchestration_plan.rationale,
    )
    autonomy_line = _render_reengagement_autonomy_line(
        reengagement_plan=reengagement_plan,
        use_chinese=use_chinese,
    )
    ritual_opening_line = _render_session_ritual_opening_line(
        session_ritual_plan=effective_session_ritual_plan,
        use_chinese=use_chinese,
    )
    ritual_bridge_line = _render_session_ritual_bridge_line(
        session_ritual_plan=effective_session_ritual_plan,
        use_chinese=use_chinese,
    )
    ritual_closing_line = _render_session_ritual_closing_line(
        session_ritual_plan=effective_session_ritual_plan,
        use_chinese=use_chinese,
    )
    user_space_line = _render_user_space_signal_line(
        user_space_signal=str(
            (stage_actuation or {}).get("user_space_signal")
            or (stage_directive or {}).get("autonomy_mode")
            or "none"
        ),
        use_chinese=use_chinese,
    )
    continuity_anchor_line = _render_continuity_anchor_line(
        session_ritual_plan=effective_session_ritual_plan,
        use_chinese=use_chinese,
    )
    somatic_line = _render_reengagement_somatic_line(
        reengagement_plan=reengagement_plan,
        use_chinese=use_chinese,
    )
    orchestration_line = _render_somatic_orchestration_line(
        somatic_orchestration_plan=effective_somatic_orchestration_plan,
        use_chinese=use_chinese,
    )
    base_message = build_proactive_followup_message(
        recent_user_text=recent_user_text,
        directive=directive,
        runtime_coordination_snapshot=runtime_coordination_snapshot,
        question_mode=question_mode,
    )
    if not base_message:
        return []
    if is_final_touch:
        if use_chinese:
            content = (
                f"{ritual_opening_line} 我先把这条线轻轻放在这里。 "
                "如果你之后想接回来，我们就从最小、最容易接上的那一步继续。 "
                f"{ritual_bridge_line} {continuity_anchor_line} {user_space_line} "
                f"{autonomy_line} {ritual_closing_line}"
            ).strip()
        else:
            content = (
                f"{ritual_opening_line} I am going to leave this thread here gently. "
                "If you want to reconnect later, we can restart from the smallest easy step. "
                f"{ritual_bridge_line} {continuity_anchor_line} {user_space_line} "
                f"{autonomy_line} {ritual_closing_line}"
            ).strip()
        return [{"label": "soft_close", "content": content}]
    if effective_delivery_mode != "two_part_sequence":
        label = (
            reengagement_plan.segment_labels[0]
            if reengagement_plan.segment_labels
            else "check_in"
        )
        stage_prefix = ""
        if cadence_stage_label == "second_touch":
            stage_prefix = (
                "我再轻轻碰一下这条线。"
                if use_chinese
                else "One more light touch on the thread."
            )
        content_parts = [part for part in [stage_prefix, base_message] if part]
        if ritual_opening_line and ritual_opening_line not in base_message:
            content_parts.insert(0, ritual_opening_line)
        if ritual_bridge_line and ritual_bridge_line not in base_message:
            content_parts.insert(1 if ritual_opening_line else 0, ritual_bridge_line)
        if somatic_line and somatic_line not in base_message:
            content_parts.append(somatic_line)
        elif (
            orchestration_line
            and allow_somatic_carryover
            and orchestration_line not in base_message
        ):
            content_parts.append(orchestration_line)
        if continuity_anchor_line and continuity_anchor_line not in base_message:
            content_parts.append(continuity_anchor_line)
        if user_space_line and user_space_line not in base_message:
            content_parts.append(user_space_line)
        if autonomy_line and autonomy_line not in base_message:
            content_parts.append(autonomy_line)
        if ritual_closing_line and ritual_closing_line not in base_message:
            content_parts.append(ritual_closing_line)
        return [{"label": label, "content": " ".join(content_parts).strip()}]

    if use_chinese:
        if reengagement_plan.strategy_key in {
            "progress_micro_commitment",
            "repair_soft_progress_reentry",
            "resume_progress_bridge",
        }:
            reconnect_line = "我来轻轻接回一下我们上次停下来的那一步。"
            if cadence_stage_label == "second_touch":
                reconnect_line = "我再轻轻碰一下上次停下来的那一步。"
            second_line = "如果你愿意，现在只推进一个最小动作就够。"
            if reengagement_plan.pressure_mode == "repair_soft":
                second_line = "如果现在想接回来，我们就只接一个最小动作；不接也没关系。"
            return [
                {
                    "label": "reconnect",
                    "content": (
                        f"{ritual_opening_line} {ritual_bridge_line} {reconnect_line}".strip()
                        if reengagement_plan.strategy_key != "resume_progress_bridge"
                        else (
                            f"{ritual_opening_line} {ritual_bridge_line} "
                            "我先把之前停住的那一步轻轻接回来。"
                        ).strip()
                    ),
                },
                {
                    "label": "next_step",
                    "content": (
                        f"{second_line} {continuity_anchor_line} "
                        f"{user_space_line} {autonomy_line} {ritual_closing_line}"
                    ).strip(),
                },
            ]
        if reengagement_plan.ritual_mode == "grounding_reentry":
            return [
                {
                    "label": "grounding",
                    "content": (
                        somatic_line
                        or orchestration_line
                        or "先轻轻确认一下你现在的状态，节奏不需要快。"
                    ),
                },
                {
                    "label": "steady_step",
                    "content": (
                        "如果要继续，我们只接回一个最稳的小下一步就好。 "
                        f"{continuity_anchor_line} {user_space_line} "
                        f"{autonomy_line} {ritual_closing_line}"
                    ).strip(),
                },
            ]
        if reengagement_plan.strategy_key in {
            "resume_context_bridge",
            "repair_soft_resume_bridge",
        }:
            reanchor_line = "我先把我们刚才的上下文轻轻接回来。"
            if cadence_stage_label == "second_touch":
                reanchor_line = "我再把这条上下文线轻轻接回来一下。"
            second_line = "如果你想继续，我们就从最容易接上的那一步开始。"
            if reengagement_plan.pressure_mode == "repair_soft":
                second_line = "如果想接回来，我们就从最容易接上的那一步开始，不需要补很多背景。"
            return [
                {
                    "label": "re_anchor",
                    "content": (
                        f"{ritual_opening_line} {ritual_bridge_line} {reanchor_line}"
                    ).strip(),
                },
                {
                    "label": "continuity",
                    "content": (
                        f"{second_line} {continuity_anchor_line} "
                        f"{user_space_line} {autonomy_line} {ritual_closing_line}"
                    ).strip(),
                },
            ]
        return [
            {
                "label": "re_anchor",
                "content": (
                    f"{ritual_opening_line} {ritual_bridge_line} "
                    "我来把我们刚才的上下文轻轻接回来。"
                ).strip(),
            },
            {
                "label": "continuity",
                "content": (
                    "如果你愿意，我们只继续最小、最容易接上的那一步。 "
                    f"{continuity_anchor_line} {user_space_line} "
                    f"{autonomy_line} {ritual_closing_line}"
                ).strip(),
            },
        ]

    if reengagement_plan.strategy_key in {
        "progress_micro_commitment",
        "repair_soft_progress_reentry",
        "resume_progress_bridge",
    }:
        reconnect_line = "Quick re-anchor to the step we left open."
        if cadence_stage_label == "second_touch":
            reconnect_line = "One more gentle bridge back to the step we left open."
        second_line = "If you want to pick it back up now, one tiny move is enough."
        if reengagement_plan.pressure_mode == "repair_soft":
            second_line = (
                "If it helps, we can restart with one tiny move, and it is okay to "
                "leave it parked for now."
            )
        return [
            {
                "label": "reconnect",
                "content": (
                    f"{ritual_opening_line} {ritual_bridge_line} {reconnect_line}".strip()
                    if reengagement_plan.strategy_key != "resume_progress_bridge"
                    else (
                        f"{ritual_opening_line} {ritual_bridge_line} "
                        "Quick bridge back to the step we parked earlier."
                    ).strip()
                ),
            },
            {
                "label": "next_step",
                "content": (
                    f"{second_line} {continuity_anchor_line} "
                    f"{user_space_line} {autonomy_line} {ritual_closing_line}"
                ).strip(),
            },
        ]
    if reengagement_plan.ritual_mode == "grounding_reentry":
        return [
            {
                "label": "grounding",
                "content": (
                    somatic_line
                    or orchestration_line
                    or "Gentle check-in first: the pace does not need to be fast."
                ),
            },
            {
                "label": "steady_step",
                "content": (
                    "If you want to continue, we can reconnect to one steady next step. "
                    f"{continuity_anchor_line} {user_space_line} "
                    f"{autonomy_line} {ritual_closing_line}"
                ).strip(),
            },
        ]
    if reengagement_plan.strategy_key in {
        "resume_context_bridge",
        "repair_soft_resume_bridge",
    }:
        reanchor_line = "Quick bridge back to the thread we left open."
        if cadence_stage_label == "second_touch":
            reanchor_line = "One more light bridge back to the thread we left open."
        second_line = "If you want to resume, we can pick up the easiest next step from here."
        if reengagement_plan.pressure_mode == "repair_soft":
            second_line = (
                "If it helps, we can restart from the easiest safe point without "
                "re-explaining everything."
            )
        return [
            {
                "label": "re_anchor",
                "content": (
                    f"{ritual_opening_line} {ritual_bridge_line} {reanchor_line}"
                ).strip(),
            },
            {
                "label": "continuity",
                "content": (
                    f"{second_line} {continuity_anchor_line} "
                    f"{user_space_line} {autonomy_line} {ritual_closing_line}"
                ).strip(),
            },
        ]
    return [
        {
            "label": "re_anchor",
            "content": (
                f"{ritual_opening_line} {ritual_bridge_line} "
                "Quick continuity check-in to reconnect the thread."
            ).strip(),
        },
        {
            "label": "continuity",
            "content": (
                "If you want to resume, we can pick up the smallest next step "
                f"without pressure. {continuity_anchor_line} "
                f"{user_space_line} {autonomy_line} {ritual_closing_line}"
            ),
        },
    ]
