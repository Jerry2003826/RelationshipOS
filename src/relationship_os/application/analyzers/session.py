"""Session directive, inner monologue, offline consolidation, snapshot, archive."""

from __future__ import annotations

from relationship_os.application.analyzers._utils import _compact
from relationship_os.domain.contracts import (
    ArchiveStatus,
    ConfidenceAssessment,
    ContextFrame,
    ConversationCadencePlan,
    EmpowermentAudit,
    GuidancePlan,
    InnerMonologueEntry,
    KnowledgeBoundaryDecision,
    MemoryBundle,
    OfflineConsolidationReport,
    PolicyGateDecision,
    PrivateJudgment,
    RehearsalResult,
    RelationshipState,
    RepairAssessment,
    RepairPlan,
    ResponseDraftPlan,
    ResponseRenderingPolicy,
    SessionDirective,
    SessionRitualPlan,
    SessionSnapshot,
    SomaticOrchestrationPlan,
    StrategyDecision,
)


def build_session_directive(
    *,
    context_frame: ContextFrame,
    policy_gate: PolicyGateDecision,
    strategy_decision: StrategyDecision,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
    guidance_plan: GuidancePlan,
    cadence_plan: ConversationCadencePlan,
    session_ritual_plan: SessionRitualPlan,
    somatic_orchestration_plan: SomaticOrchestrationPlan,
    repair_assessment: RepairAssessment,
    repair_plan: RepairPlan,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    memory_bundle: MemoryBundle,
    recalled_memory: list[dict[str, object]] | None = None,
) -> SessionDirective:
    focus_points = [context_frame.topic, context_frame.dialogue_act]
    if policy_gate.red_line_status != "clear":
        focus_points.append(policy_gate.red_line_status)
    if repair_assessment.repair_needed:
        focus_points.append(repair_plan.rupture_type)
    if knowledge_boundary_decision.boundary_type != "none":
        focus_points.append(knowledge_boundary_decision.boundary_type)
    if empowerment_audit.status != "pass":
        focus_points.append(empowerment_audit.status)
    if response_draft_plan.question_strategy != "none":
        focus_points.append(response_draft_plan.question_strategy)
    if response_rendering_policy.rendering_mode != "supportive_progress":
        focus_points.append(response_rendering_policy.rendering_mode)
    focus_points.append(guidance_plan.mode)
    if guidance_plan.handoff_mode:
        focus_points.append(guidance_plan.handoff_mode)
    if guidance_plan.agency_mode != "collaborative_choice":
        focus_points.append(guidance_plan.agency_mode)
    focus_points.append(cadence_plan.status)
    if cadence_plan.followup_tempo != "none":
        focus_points.append(cadence_plan.followup_tempo)
    focus_points.append(session_ritual_plan.phase)
    if session_ritual_plan.continuity_anchor:
        focus_points.append(session_ritual_plan.continuity_anchor)
    if somatic_orchestration_plan.status == "active":
        focus_points.append(somatic_orchestration_plan.primary_mode)
    if context_frame.bid_signal != "low_signal":
        focus_points.append(context_frame.bid_signal)
    if recalled_memory:
        focus_points.append(str(recalled_memory[0].get("value", ""))[:48])
    if memory_bundle.working_memory:
        focus_points.append(memory_bundle.working_memory[-1][:48])
    response_style = "supportive" if context_frame.appraisal != "negative" else "calming"
    if strategy_decision.strategy == "answer_with_uncertainty":
        response_style = "calibrated"
    elif policy_gate.regulation_mode == "clarify":
        response_style = "clarifying"
    elif empowerment_audit.status == "revise":
        response_style = "guardrailed"
    return SessionDirective(
        should_reply=True,
        next_action=strategy_decision.strategy,
        response_style=response_style,
        focus_points=_compact(
            focus_points + rehearsal_result.recommended_adjustments[:1],
            limit=4,
        ),
    )


def build_inner_monologue(
    *,
    context_frame: ContextFrame,
    memory_bundle: MemoryBundle,
    recalled_memory: list[dict[str, object]] | None,
    policy_gate: PolicyGateDecision,
    rehearsal_result: RehearsalResult,
    empowerment_audit: EmpowermentAudit,
    response_draft_plan: ResponseDraftPlan,
    response_rendering_policy: ResponseRenderingPolicy,
    repair_assessment: RepairAssessment,
    repair_plan: RepairPlan,
    knowledge_boundary_decision: KnowledgeBoundaryDecision,
    private_judgment: PrivateJudgment,
    relationship_state: RelationshipState,
    strategy_decision: StrategyDecision,
    confidence_assessment: ConfidenceAssessment,
) -> list[InnerMonologueEntry]:
    return [
        InnerMonologueEntry(
            stage="l1_context",
            summary=(
                f"Detected {context_frame.dialogue_act} with {context_frame.bid_signal} "
                f"around topic {context_frame.topic}."
            ),
            confidence=confidence_assessment.score,
        ),
        InnerMonologueEntry(
            stage="l4_memory",
            summary=(
                f"Working memory holds {len(memory_bundle.working_memory)} items and "
                f"semantic memory centers on {context_frame.topic}; recall surfaced "
                f"{len(recalled_memory or [])} prior items."
            ),
            confidence=0.73,
        ),
        InnerMonologueEntry(
            stage="l3_repair",
            summary=(
                f"Repair assessment is {repair_assessment.rupture_type} with "
                f"{repair_assessment.severity} severity."
            ),
            confidence=0.7,
        ),
        InnerMonologueEntry(
            stage="l2_relationship",
            summary=(
                "Psychological safety is "
                f"{relationship_state.psychological_safety} and dependency risk is "
                f"{relationship_state.dependency_risk}."
            ),
            confidence=0.71,
        ),
        InnerMonologueEntry(
            stage="l5_private_judgment",
            summary=private_judgment.summary,
            confidence=private_judgment.confidence,
        ),
        InnerMonologueEntry(
            stage="policy_gate",
            summary=(
                f"Policy gate selected {policy_gate.selected_path} with "
                f"{policy_gate.regulation_mode} regulation."
            ),
            confidence=0.77,
        ),
        InnerMonologueEntry(
            stage="rehearsal",
            summary=(
                f"Rehearsal predicts {rehearsal_result.predicted_user_impact} with "
                f"{rehearsal_result.projected_risk_level} risk."
            ),
            confidence=0.74,
        ),
        InnerMonologueEntry(
            stage="empowerment_audit",
            summary=(
                f"Empowerment audit is {empowerment_audit.status} with "
                f"{len(empowerment_audit.flagged_issues)} flagged issues."
            ),
            confidence=0.76,
        ),
        InnerMonologueEntry(
            stage="response_drafting",
            summary=(
                f"Drafting will use {response_draft_plan.opening_move} with "
                f"{response_draft_plan.question_strategy} question strategy and "
                f"{len(response_draft_plan.phrasing_constraints)} phrasing constraints."
            ),
            confidence=0.78,
        ),
        InnerMonologueEntry(
            stage="response_rendering",
            summary=(
                f"Rendering will use {response_rendering_policy.rendering_mode} with "
                f"a {response_rendering_policy.max_sentences}-sentence cap and "
                f"{response_rendering_policy.question_count_limit} question limit."
            ),
            confidence=0.8,
        ),
    ]


def build_offline_consolidation_report(
    *,
    session_id: str,
    runtime_projection: dict[str, object],
    evaluation: dict[str, object],
) -> OfflineConsolidationReport:
    state = runtime_projection.get("state", {})
    if not isinstance(state, dict):
        state = {}

    summary = evaluation.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    context_frame = state.get("context_frame", {})
    relationship_state = state.get("relationship_state", {})
    memory_bundle = state.get("memory_bundle", {})
    repair_plan = state.get("repair_plan", {})
    session_directive = state.get("session_directive", {})

    if not isinstance(context_frame, dict):
        context_frame = {}
    if not isinstance(relationship_state, dict):
        relationship_state = {}
    if not isinstance(memory_bundle, dict):
        memory_bundle = {}
    if not isinstance(repair_plan, dict):
        repair_plan = {}
    if not isinstance(session_directive, dict):
        session_directive = {}

    turn_count = int(summary.get("turn_count", 0))
    latest_strategy = (
        summary.get("latest_strategy")
        or session_directive.get("next_action")
        or "observe"
    )
    topic = str(context_frame.get("topic", "general"))

    reinforced_memories = _compact(
        list(memory_bundle.get("working_memory", []))
        + list(memory_bundle.get("episodic_memory", []))
        + list(memory_bundle.get("reflective_memory", [])),
        limit=6,
    )
    relationship_signals = _compact(
        [
            f"psychological_safety:{relationship_state.get('psychological_safety', 'unknown')}",
            f"turbulence_risk:{relationship_state.get('turbulence_risk', 'unknown')}",
            f"dependency_risk:{relationship_state.get('dependency_risk', 'unknown')}",
            f"rupture_type:{repair_plan.get('rupture_type', 'none')}",
        ],
        limit=4,
    )

    drift_flags: list[str] = []
    avg_safety = summary.get("avg_psychological_safety")
    if isinstance(avg_safety, (int, float)) and float(avg_safety) < 0.65:
        drift_flags.append("psychological_safety_downshift")
    if int(summary.get("rupture_detected_count", 0)) > 0:
        drift_flags.append("recent_rupture_detected")
    if int(summary.get("dependency_risk_elevated_count", 0)) > 0:
        drift_flags.append("dependency_boundary_watch")
    if int(summary.get("llm_failure_count", 0)) > 0:
        drift_flags.append("llm_reliability_gap")

    recommended_actions = _compact(
        list(repair_plan.get("recommended_actions", []))
        + [str(latest_strategy)]
        + list(session_directive.get("focus_points", [])),
        limit=5,
    )
    archive_candidate = turn_count >= 3 or len(reinforced_memories) >= 5

    return OfflineConsolidationReport(
        summary=(
            f"Session {session_id} consolidation captured {turn_count} turns on {topic}; "
            f"the latest strategy remains {latest_strategy}."
        ),
        reinforced_memories=reinforced_memories,
        relationship_signals=relationship_signals,
        drift_flags=drift_flags,
        recommended_actions=recommended_actions,
        archive_candidate=archive_candidate,
        source_turn_count=turn_count,
    )


def build_session_snapshot(
    *,
    snapshot_id: str,
    created_at: str,
    source_job_id: str,
    evaluation_summary: dict[str, object],
    report: OfflineConsolidationReport,
    fingerprint: str,
) -> SessionSnapshot:
    latest_strategy = evaluation_summary.get("latest_strategy")
    if latest_strategy is not None:
        latest_strategy = str(latest_strategy)

    event_count = int(evaluation_summary.get("event_count", 0))
    turn_count = int(evaluation_summary.get("turn_count", 0))
    working_memory_size = int(evaluation_summary.get("latest_working_memory_size", 0))

    return SessionSnapshot(
        snapshot_id=snapshot_id,
        created_at=created_at,
        source_job_id=source_job_id,
        summary=report.summary,
        fingerprint=fingerprint,
        turn_count=turn_count,
        event_count=event_count,
        latest_strategy=latest_strategy,
        working_memory_size=working_memory_size,
        archive_candidate=report.archive_candidate,
    )


def build_archive_status(
    *,
    created_at: str,
    snapshot: SessionSnapshot,
    report: OfflineConsolidationReport,
) -> ArchiveStatus:
    reason = "offline_consolidation_archive_candidate"
    if report.drift_flags:
        reason = f"{reason}:{report.drift_flags[0]}"

    return ArchiveStatus(
        archived=report.archive_candidate,
        archived_at=created_at if report.archive_candidate else None,
        reason=reason if report.archive_candidate else None,
        snapshot_id=snapshot.snapshot_id if report.archive_candidate else None,
    )
