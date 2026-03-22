from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from relationship_os.application.audit_service import AuditService
from relationship_os.application.evaluation_service import EvaluationService
from relationship_os.application.job_executor import JobExecutor
from relationship_os.application.job_service import JobService
from relationship_os.application.runtime_service import RuntimeService
from relationship_os.application.scenario_evaluation_service.catalog import (
    BASELINE_STREAM_ID,
    MISALIGNMENT_TAXONOMY,
    SCENARIO_CATALOG,
    ScenarioBaselineNotFoundError,
    ScenarioCheck,
    ScenarioDefinition,
    ScenarioNotFoundError,
    ScenarioRunNotFoundError,
    ScenarioSessionRecord,
)
from relationship_os.application.scenario_evaluation_service.reports import _ReportsMixin
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.event_types import (
    SCENARIO_BASELINE_CLEARED,
    SCENARIO_BASELINE_SET,
    SESSION_STARTED,
)
from relationship_os.domain.events import NewEvent, utc_now
from relationship_os.domain.projectors import VersionedProjectorRegistry


class ScenarioEvaluationService(_ReportsMixin):
    def __init__(
        self,
        *,
        stream_service: StreamService,
        runtime_service: RuntimeService,
        evaluation_service: EvaluationService,
        audit_service: AuditService,
        job_service: JobService,
        job_executor: JobExecutor,
        projector_registry: VersionedProjectorRegistry,
    ) -> None:
        self._stream_service = stream_service
        self._runtime_service = runtime_service
        self._evaluation_service = evaluation_service
        self._audit_service = audit_service
        self._job_service = job_service
        self._job_executor = job_executor
        self._projector_registry = projector_registry
        self._catalog = {scenario.scenario_id: scenario for scenario in SCENARIO_CATALOG}

    async def list_scenarios(self) -> dict[str, Any]:
        scenarios = [scenario.to_dict() for scenario in SCENARIO_CATALOG]
        return {
            "scenario_count": len(scenarios),
            "category_counts": {
                "stress": sum(1 for scenario in scenarios if scenario["category"] == "stress"),
                "redteam": sum(
                    1 for scenario in scenarios if scenario["category"] == "redteam"
                ),
            },
            "scenarios": scenarios,
        }

    async def get_scenario(self, *, scenario_id: str) -> dict[str, Any]:
        return self._resolve_scenario(scenario_id).to_dict()

    async def run_scenarios(
        self,
        *,
        scenario_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        run_id = f"scenario-run-{uuid4().hex[:10]}"
        started_at = utc_now().isoformat()
        resolved_scenarios = (
            [self._resolve_scenario(scenario_id) for scenario_id in scenario_ids]
            if scenario_ids
            else list(SCENARIO_CATALOG)
        )
        results = [
            await self._run_scenario(scenario, run_id=run_id)
            for scenario in resolved_scenarios
        ]
        return self._build_run_payload(
            run_id=run_id,
            started_at=started_at,
            results=results,
        )

    async def list_runs(self, *, limit: int = 20) -> dict[str, Any]:
        records = await self._list_scenario_session_records()
        runs = await self._build_run_summaries(records)
        return {
            "run_count": len(runs[:limit]),
            "runs": runs[:limit],
        }

    async def get_run(self, *, run_id: str) -> dict[str, Any]:
        records = await self._list_scenario_session_records()
        return await self._build_run_from_records(run_id=run_id, records=records)

    async def list_trends(self, *, limit_per_scenario: int = 5) -> dict[str, Any]:
        records = await self._list_scenario_session_records()
        scenario_trends = await self._build_scenario_trends(
            records=records,
            limit_per_scenario=limit_per_scenario,
        )
        return {
            "scenario_count": len(scenario_trends),
            "limit_per_scenario": limit_per_scenario,
            "scenarios": scenario_trends,
        }

    async def compare_runs(
        self,
        *,
        baseline_run_id: str,
        candidate_run_id: str,
    ) -> dict[str, Any]:
        records = await self._list_scenario_session_records()
        baseline = await self._build_run_from_records(
            run_id=baseline_run_id,
            records=records,
        )
        candidate = await self._build_run_from_records(
            run_id=candidate_run_id,
            records=records,
        )
        return self._compare_run_payloads(
            baseline=baseline,
            candidate=candidate,
        )

    async def list_baselines(self) -> dict[str, Any]:
        baselines = await self._read_baselines()
        return {
            "baseline_count": len(baselines),
            "baselines": list(baselines.values()),
        }

    async def set_baseline(
        self,
        *,
        label: str,
        run_id: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        normalized_label = self._normalize_baseline_label(label)
        records = await self._list_scenario_session_records()
        run = await self._build_run_from_records(run_id=run_id, records=records)
        baseline_events = await self._stream_service.read_stream(stream_id=BASELINE_STREAM_ID)
        expected_version = baseline_events[-1].version if baseline_events else 0
        event = NewEvent(
            event_type=SCENARIO_BASELINE_SET,
            payload={
                "label": normalized_label,
                "run_id": run_id,
                "note": (note or "").strip() or None,
                "scenario_count": run.get("scenario_count"),
                "overall_status": run.get("overall_status"),
                "started_at": run.get("started_at"),
                "set_at": utc_now().isoformat(),
            },
        )
        await self._stream_service.append_events(
            stream_id=BASELINE_STREAM_ID,
            expected_version=expected_version,
            events=[event],
        )
        baselines = await self._read_baselines()
        return dict(baselines[normalized_label])

    async def clear_baseline(self, *, label: str) -> dict[str, Any]:
        normalized_label = self._normalize_baseline_label(label)
        baselines = await self._read_baselines()
        baseline = baselines.get(normalized_label)
        if baseline is None:
            raise ScenarioBaselineNotFoundError(
                f"Unknown scenario baseline {normalized_label}"
            )
        baseline_events = await self._stream_service.read_stream(stream_id=BASELINE_STREAM_ID)
        expected_version = baseline_events[-1].version if baseline_events else 0
        event = NewEvent(
            event_type=SCENARIO_BASELINE_CLEARED,
            payload={
                "label": normalized_label,
                "cleared_at": utc_now().isoformat(),
            },
        )
        await self._stream_service.append_events(
            stream_id=BASELINE_STREAM_ID,
            expected_version=expected_version,
            events=[event],
        )
        return {
            "label": normalized_label,
            "cleared": True,
            "previous_run_id": baseline.get("run_id"),
        }

    async def compare_with_baseline(
        self,
        *,
        label: str = "default",
        candidate_run_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_label = self._normalize_baseline_label(label)
        baselines = await self._read_baselines()
        baseline = baselines.get(normalized_label)
        if baseline is None:
            raise ScenarioBaselineNotFoundError(
                f"Unknown scenario baseline {normalized_label}"
            )

        records = await self._list_scenario_session_records()
        baseline_run = await self._build_run_from_records(
            run_id=str(baseline["run_id"]),
            records=records,
        )
        if candidate_run_id is None:
            runs = await self._build_run_summaries(records)
            if not runs:
                raise ScenarioRunNotFoundError("No scenario runs available for comparison")
            candidate_run = runs[0]
        else:
            candidate_run = await self._build_run_from_records(
                run_id=candidate_run_id,
                records=records,
            )
        comparison = self._compare_run_payloads(
            baseline=baseline_run,
            candidate=candidate_run,
        )
        comparison["baseline_label"] = normalized_label
        comparison["baseline_note"] = baseline.get("note")
        comparison["baseline_set_at"] = baseline.get("set_at")
        return comparison


    def _resolve_scenario(self, scenario_id: str) -> ScenarioDefinition:
        scenario = self._catalog.get(scenario_id)
        if scenario is None:
            raise ScenarioNotFoundError(f"Unknown evaluation scenario {scenario_id}")
        return scenario

    def _classify_misalignment(
        self,
        *,
        scenario_id: str,
        scenario_category: str,
        metric: str,
    ) -> dict[str, str]:
        if metric == "latest_boundary_decision":
            if scenario_category == "redteam" or "dependency" in scenario_id:
                return {
                    "type": "dependency_boundary_failure",
                    "module": "L2/L7",
                }
            return {
                "type": "boundary_calibration_failure",
                "module": "L5+L6",
            }
        classification = MISALIGNMENT_TAXONOMY.get(metric)
        if classification is not None:
            return dict(classification)
        return {
            "type": "unclassified_failure",
            "module": "cross_layer",
        }

    async def _run_scenario(
        self,
        scenario: ScenarioDefinition,
        *,
        run_id: str,
    ) -> dict[str, Any]:
        session_id = f"{scenario.scenario_id}-{uuid4().hex[:8]}"
        started_at = utc_now().isoformat()
        await self._runtime_service.create_session(
            session_id=session_id,
            metadata={
                "source": "scenario_evaluation",
                "run_id": run_id,
                "scenario_id": scenario.scenario_id,
                "scenario_category": scenario.category,
            },
        )
        for index, turn in enumerate(scenario.turns, start=1):
            await self._runtime_service.process_turn(
                session_id=session_id,
                user_message=turn.content,
                generate_reply=turn.generate_reply,
                metadata={
                    "source": "scenario_evaluation",
                    "scenario_id": scenario.scenario_id,
                    "turn_index": index,
                    **dict(turn.metadata),
                },
            )

        evaluation = await self._evaluation_service.evaluate_session(session_id=session_id)
        audit = await self._audit_service.get_session_audit(session_id=session_id)
        scorecard = self._build_scorecard(
            scenario=scenario,
            summary=dict(evaluation["summary"]),
        )
        return {
            "run_id": run_id,
            "scenario": scenario.to_dict(),
            "session_id": session_id,
            "started_at": started_at,
            "summary": evaluation["summary"],
            "audit": {
                "fingerprint": audit["fingerprint"],
                "consistent": audit["consistent"],
                "event_count": audit["event_count"],
            },
            "scorecard": scorecard,
        }

    async def _list_scenario_session_records(self) -> list[ScenarioSessionRecord]:
        stream_ids = await self._stream_service.list_stream_ids()
        records: list[ScenarioSessionRecord] = []
        for stream_id in stream_ids:
            events = await self._stream_service.read_stream(stream_id=stream_id)
            started_event = next(
                (event for event in events if event.event_type == SESSION_STARTED),
                None,
            )
            if started_event is None:
                continue
            metadata = dict(started_event.payload.get("metadata", {}))
            if metadata.get("source") != "scenario_evaluation":
                continue
            run_id = str(metadata.get("run_id", "")).strip()
            scenario_id = str(metadata.get("scenario_id", "")).strip()
            if not run_id or not scenario_id:
                continue
            records.append(
                ScenarioSessionRecord(
                    run_id=run_id,
                    session_id=stream_id,
                    scenario_id=scenario_id,
                    category=str(metadata.get("scenario_category", "stress")),
                    started_at=started_event.payload.get("created_at"),
                    last_event_at=events[-1].occurred_at.isoformat() if events else None,
                )
            )
        records.sort(
            key=lambda item: (item.started_at or "", item.session_id),
            reverse=True,
        )
        return records

    async def _list_started_session_records(
        self,
        *,
        include_scenarios: bool,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        stream_ids = await self._stream_service.list_stream_ids()
        records: list[dict[str, Any]] = []
        for stream_id in stream_ids:
            events = await self._stream_service.read_stream(stream_id=stream_id)
            started_event = next(
                (event for event in events if event.event_type == SESSION_STARTED),
                None,
            )
            if started_event is None:
                continue
            metadata = dict(started_event.payload.get("metadata", {}))
            source = str(metadata.get("source") or "session")
            if not include_scenarios and source == "scenario_evaluation":
                continue
            records.append(
                {
                    "stream_id": stream_id,
                    "source": source,
                    "started_at": started_event.payload.get("created_at"),
                    "last_event_at": events[-1].occurred_at.isoformat() if events else None,
                    "event_count": len(events),
                }
            )
        records.sort(
            key=lambda item: (
                str(item.get("started_at") or ""),
                str(item.get("stream_id") or ""),
            ),
            reverse=True,
        )
        if limit is not None:
            return records[:limit]
        return records

    async def _build_result_from_record(
        self,
        record: ScenarioSessionRecord,
    ) -> dict[str, Any]:
        scenario = self._resolve_scenario(record.scenario_id)
        evaluation = await self._evaluation_service.evaluate_session(
            session_id=record.session_id
        )
        audit = await self._audit_service.get_session_audit(session_id=record.session_id)
        scorecard = self._build_scorecard(
            scenario=scenario,
            summary=dict(evaluation["summary"]),
        )
        return {
            "run_id": record.run_id,
            "scenario": scenario.to_dict(),
            "session_id": record.session_id,
            "started_at": record.started_at,
            "summary": evaluation["summary"],
            "audit": {
                "fingerprint": audit["fingerprint"],
                "consistent": audit["consistent"],
                "event_count": audit["event_count"],
            },
            "scorecard": scorecard,
        }

    async def _build_run_from_records(
        self,
        *,
        run_id: str,
        records: list[ScenarioSessionRecord],
    ) -> dict[str, Any]:
        matching_records = [record for record in records if record.run_id == run_id]
        if not matching_records:
            raise ScenarioRunNotFoundError(f"Unknown scenario run {run_id}")
        results = [
            await self._build_result_from_record(record) for record in matching_records
        ]
        return {
            **self._build_run_payload(
                run_id=run_id,
                started_at=min(record.started_at or "" for record in matching_records) or None,
                results=results,
            ),
            "finished_at": max(record.last_event_at or "" for record in matching_records)
            or None,
        }

    async def _build_run_summaries(
        self,
        records: list[ScenarioSessionRecord],
    ) -> list[dict[str, Any]]:
        records_by_run: dict[str, list[ScenarioSessionRecord]] = {}
        for record in records:
            records_by_run.setdefault(record.run_id, []).append(record)

        summaries: list[dict[str, Any]] = []
        for run_id, run_records in records_by_run.items():
            results = [
                await self._build_result_from_record(record) for record in run_records
            ]
            payload = self._build_run_payload(
                run_id=run_id,
                started_at=min(record.started_at or "" for record in run_records) or None,
                results=results,
            )
            payload["finished_at"] = (
                max(record.last_event_at or "" for record in run_records) or None
            )
            payload["scenario_ids"] = [
                result["scenario"]["scenario_id"] for result in payload["results"]
            ]
            summaries.append(payload)

        summaries.sort(key=lambda item: str(item.get("started_at") or ""), reverse=True)
        return summaries

    async def _read_baselines(self) -> dict[str, dict[str, Any]]:
        events = await self._stream_service.read_stream(stream_id=BASELINE_STREAM_ID)
        baselines: dict[str, dict[str, Any]] = {}
        for event in events:
            label = self._normalize_baseline_label(event.payload.get("label"))
            if not label:
                continue
            if event.event_type == SCENARIO_BASELINE_CLEARED:
                baselines.pop(label, None)
                continue
            if event.event_type != SCENARIO_BASELINE_SET:
                continue
            baselines[label] = {
                "label": label,
                "run_id": event.payload.get("run_id"),
                "note": event.payload.get("note"),
                "scenario_count": event.payload.get("scenario_count"),
                "overall_status": event.payload.get("overall_status"),
                "started_at": event.payload.get("started_at"),
                "set_at": event.payload.get("set_at") or event.occurred_at.isoformat(),
                "stream_version": event.version,
            }
        return dict(sorted(baselines.items()))

    async def _build_scenario_trends(
        self,
        *,
        records: list[ScenarioSessionRecord],
        limit_per_scenario: int,
    ) -> list[dict[str, Any]]:
        records_by_scenario: dict[str, list[ScenarioSessionRecord]] = {}
        for record in records:
            records_by_scenario.setdefault(record.scenario_id, []).append(record)

        scenario_trends = []
        for scenario in SCENARIO_CATALOG:
            grouped_records = sorted(
                records_by_scenario.get(scenario.scenario_id, []),
                key=lambda item: (item.started_at or "", item.run_id),
                reverse=True,
            )
            recent_records = grouped_records[:limit_per_scenario]
            recent_results = [
                await self._build_result_from_record(record) for record in recent_records
            ]
            recent_runs = [
                {
                    "run_id": result["run_id"],
                    "session_id": result["session_id"],
                    "status": result["scorecard"]["status"],
                    "started_at": result["started_at"],
                    "passed_checks": result["scorecard"]["passed_count"],
                    "check_count": result["scorecard"]["check_count"],
                }
                for result in recent_results
            ]
            latest_status = recent_runs[0]["status"] if recent_runs else None
            previous_status = recent_runs[1]["status"] if len(recent_runs) > 1 else None
            status_delta = self._compare_status_labels(previous_status, latest_status)
            latest_summary = recent_results[0]["summary"] if recent_results else {}
            if previous_status is None and latest_status is None:
                status_delta = "stable"

            pass_count = sum(1 for run in recent_runs if run["status"] == "pass")
            scenario_trends.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "title": scenario.title,
                    "category": scenario.category,
                    "total_runs": len(grouped_records),
                    "recent_run_count": len(recent_runs),
                    "pass_rate": (
                        round(pass_count / len(recent_runs), 3) if recent_runs else None
                    ),
                    "latest_status": latest_status,
                    "previous_status": previous_status,
                    "status_delta": status_delta,
                    "latest_run_id": recent_runs[0]["run_id"] if recent_runs else None,
                    "latest_started_at": recent_runs[0]["started_at"] if recent_runs else None,
                    "latest_output_quality_status": latest_summary.get(
                        "output_quality_status"
                    ),
                    "latest_output_quality_issues": list(
                        latest_summary.get("output_quality_issues", [])
                    ),
                    "latest_response_word_count": latest_summary.get(
                        "latest_response_word_count"
                    ),
                    "latest_time_awareness_mode": latest_summary.get(
                        "latest_time_awareness_mode"
                    ),
                    "latest_cognitive_load_band": latest_summary.get(
                        "latest_cognitive_load_band"
                    ),
                    "latest_proactive_followup_status": latest_summary.get(
                        "latest_proactive_followup_status"
                    ),
                    "latest_runtime_quality_doctor_status": latest_summary.get(
                        "latest_runtime_quality_doctor_status"
                    ),
                    "latest_runtime_quality_doctor_issue_count": latest_summary.get(
                        "latest_runtime_quality_doctor_issue_count"
                    ),
                    "latest_system3_growth_stage": latest_summary.get(
                        "latest_system3_growth_stage"
                    ),
                    "latest_system3_strategy_audit_status": latest_summary.get(
                        "latest_system3_strategy_audit_status"
                    ),
                    "latest_system3_emotional_debt_status": latest_summary.get(
                        "latest_system3_emotional_debt_status"
                    ),
                    "recent_runs": recent_runs,
                }
            )
        return scenario_trends

    def _compare_run_payloads(
        self,
        *,
        baseline: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        baseline_results = {
            result["scenario"]["scenario_id"]: result
            for result in baseline["results"]
        }
        candidate_results = {
            result["scenario"]["scenario_id"]: result
            for result in candidate["results"]
        }

        comparisons = []
        for scenario in SCENARIO_CATALOG:
            baseline_result = baseline_results.get(scenario.scenario_id)
            candidate_result = candidate_results.get(scenario.scenario_id)
            if baseline_result is None and candidate_result is None:
                continue
            comparisons.append(
                self._build_scenario_comparison(
                    scenario=scenario,
                    baseline_result=baseline_result,
                    candidate_result=candidate_result,
                )
            )

        delta_labels = ["improved", "regressed", "stable", "new", "removed", "changed"]
        return {
            "baseline_run_id": baseline.get("run_id"),
            "candidate_run_id": candidate.get("run_id"),
            "baseline_started_at": baseline.get("started_at"),
            "candidate_started_at": candidate.get("started_at"),
            "baseline_overall_status": baseline.get("overall_status"),
            "candidate_overall_status": candidate.get("overall_status"),
            "overall_delta": self._compare_status_labels(
                baseline.get("overall_status"),
                candidate.get("overall_status"),
            ),
            "scenario_count": len(comparisons),
            "changed_scenario_count": sum(
                1
                for item in comparisons
                if item["status_delta"] != "stable" or item["score_delta"] not in {0, None}
            ),
            "delta_counts": {
                label: sum(1 for item in comparisons if item["status_delta"] == label)
                for label in delta_labels
            },
            "scenarios": comparisons,
        }

    def _normalize_baseline_label(self, value: object) -> str:
        return str(value or "").strip().lower()

    def _build_scenario_comparison(
        self,
        *,
        scenario: ScenarioDefinition,
        baseline_result: dict[str, Any] | None,
        candidate_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        baseline_status = (
            baseline_result["scorecard"]["status"] if baseline_result is not None else None
        )
        candidate_status = (
            candidate_result["scorecard"]["status"] if candidate_result is not None else None
        )
        baseline_score = (
            baseline_result["scorecard"]["passed_count"]
            if baseline_result is not None
            else None
        )
        candidate_score = (
            candidate_result["scorecard"]["passed_count"]
            if candidate_result is not None
            else None
        )
        return {
            "scenario_id": scenario.scenario_id,
            "title": scenario.title,
            "category": scenario.category,
            "baseline_session_id": (
                baseline_result.get("session_id") if baseline_result is not None else None
            ),
            "candidate_session_id": (
                candidate_result.get("session_id") if candidate_result is not None else None
            ),
            "baseline_status": baseline_status,
            "candidate_status": candidate_status,
            "status_delta": self._compare_status_labels(
                baseline_status,
                candidate_status,
            ),
            "baseline_passed_checks": baseline_score,
            "candidate_passed_checks": candidate_score,
            "check_count": len(scenario.checks),
            "score_delta": (
                candidate_score - baseline_score
                if baseline_score is not None and candidate_score is not None
                else None
            ),
            "changed_checks": self._build_changed_checks(
                baseline_result=baseline_result,
                candidate_result=candidate_result,
            ),
        }

    def _build_changed_checks(
        self,
        *,
        baseline_result: dict[str, Any] | None,
        candidate_result: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        baseline_checks = {
            str(check["metric"]): check
            for check in (baseline_result or {}).get("scorecard", {}).get("checks", [])
        }
        candidate_checks = {
            str(check["metric"]): check
            for check in (candidate_result or {}).get("scorecard", {}).get("checks", [])
        }
        metric_order = list(baseline_checks)
        for metric in candidate_checks:
            if metric not in metric_order:
                metric_order.append(metric)

        changed_checks: list[dict[str, Any]] = []
        for metric in metric_order:
            baseline_check = baseline_checks.get(metric)
            candidate_check = candidate_checks.get(metric)
            baseline_actual = (
                baseline_check.get("actual") if baseline_check is not None else None
            )
            candidate_actual = (
                candidate_check.get("actual") if candidate_check is not None else None
            )
            baseline_passed = (
                baseline_check.get("passed") if baseline_check is not None else None
            )
            candidate_passed = (
                candidate_check.get("passed") if candidate_check is not None else None
            )
            if (
                baseline_actual == candidate_actual
                and baseline_passed == candidate_passed
            ):
                continue
            changed_checks.append(
                {
                    "metric": metric,
                    "description": (
                        (candidate_check or baseline_check or {}).get("description")
                    ),
                    "baseline_actual": baseline_actual,
                    "candidate_actual": candidate_actual,
                    "baseline_passed": baseline_passed,
                    "candidate_passed": candidate_passed,
                }
            )
        return changed_checks

    def _compare_status_labels(
        self,
        baseline_status: str | None,
        candidate_status: str | None,
    ) -> str:
        if baseline_status is None and candidate_status is not None:
            return "new"
        if baseline_status is not None and candidate_status is None:
            return "removed"
        if baseline_status == candidate_status:
            return "stable"
        if baseline_status == "review" and candidate_status == "pass":
            return "improved"
        if baseline_status == "pass" and candidate_status == "review":
            return "regressed"
        return "changed"

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _build_run_payload(
        self,
        *,
        run_id: str,
        started_at: str | None,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        overall_status = (
            "pass"
            if all(result["scorecard"]["status"] == "pass" for result in results)
            else "review"
        )
        return {
            "run_id": run_id,
            "started_at": started_at,
            "scenario_count": len(results),
            "overall_status": overall_status,
            "status_counts": {
                "pass": sum(1 for result in results if result["scorecard"]["status"] == "pass"),
                "review": sum(
                    1 for result in results if result["scorecard"]["status"] == "review"
                ),
            },
            "results": results,
        }

    def _summarize_run_cohort(self, runs: list[dict[str, Any]]) -> dict[str, Any]:
        result_summaries = [
            dict(result.get("summary") or {})
            for run in runs
            for result in list(run.get("results", []))
        ]
        run_count = len(runs)
        pass_run_count = sum(1 for run in runs if run.get("overall_status") == "pass")
        quality_watch_count = sum(
            1
            for summary in result_summaries
            if str(summary.get("output_quality_status") or "stable")
            in {"watch", "degrading"}
        )
        doctor_watch_count = sum(
            1
            for summary in result_summaries
            if str(summary.get("latest_runtime_quality_doctor_status") or "pass")
            in {"watch", "revise"}
        )
        system3_watch_count = sum(
            1
            for summary in result_summaries
            if str(summary.get("latest_system3_strategy_audit_status") or "pass")
            in {"watch", "revise"}
        )
        latest_summary = result_summaries[0] if result_summaries else {}
        return {
            "run_count": run_count,
            "result_count": len(result_summaries),
            "overall_pass_rate": (
                round(pass_run_count / run_count, 3) if run_count else None
            ),
            "quality_watch_result_count": quality_watch_count,
            "runtime_quality_doctor_watch_result_count": doctor_watch_count,
            "system3_watch_result_count": system3_watch_count,
            "latest_output_quality_status": latest_summary.get("output_quality_status"),
            "latest_runtime_quality_doctor_status": latest_summary.get(
                "latest_runtime_quality_doctor_status"
            ),
            "latest_system3_strategy_audit_status": latest_summary.get(
                "latest_system3_strategy_audit_status"
            ),
        }

    def _summarize_redteam_cohort(self, runs: list[dict[str, Any]]) -> dict[str, Any]:
        redteam_results = [
            result
            for run in runs
            for result in list(run.get("results", []))
            if str((result.get("scenario") or {}).get("category") or "") == "redteam"
        ]
        pass_count = sum(
            1
            for result in redteam_results
            if (result.get("scorecard") or {}).get("status") == "pass"
        )
        boundary_guard_count = sum(
            1
            for result in redteam_results
            if str((result.get("summary") or {}).get("latest_boundary_decision") or "")
            in {"support_with_boundary", "answer_with_uncertainty"}
            and int((result.get("summary") or {}).get("policy_gate_guarded_turn_count") or 0) >= 1
        )
        latest_result = redteam_results[0] if redteam_results else {}
        latest_summary = dict(latest_result.get("summary") or {})
        latest_audit = dict(latest_result.get("audit") or {})
        return {
            "result_count": len(redteam_results),
            "pass_rate": (
                round(pass_count / len(redteam_results), 3) if redteam_results else None
            ),
            "boundary_guard_rate": (
                round(boundary_guard_count / len(redteam_results), 3)
                if redteam_results
                else None
            ),
            "latest_boundary_decision": latest_summary.get("latest_boundary_decision"),
            "latest_policy_path": latest_summary.get("latest_policy_path"),
            "latest_audit_consistent": latest_audit.get("consistent"),
        }

    def _round_delta(self, recent: Any, prior: Any) -> float | None:
        if recent is None or prior is None:
            return None
        return round(float(recent) - float(prior), 3)

    def _build_scorecard(
        self,
        *,
        scenario: ScenarioDefinition,
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        checks = [
            self._evaluate_check(check=check, summary=summary)
            for check in scenario.checks
        ]
        return {
            "status": "pass" if all(check["passed"] for check in checks) else "review",
            "check_count": len(checks),
            "passed_count": sum(1 for check in checks if check["passed"]),
            "checks": checks,
        }

    def _evaluate_check(
        self,
        *,
        check: ScenarioCheck,
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        actual = summary.get(check.metric)
        if check.comparator == "ge":
            passed = float(actual or 0) >= float(check.expected)
            expectation = f">= {check.expected}"
        elif check.comparator == "eq":
            passed = actual == check.expected
            expectation = f"== {check.expected}"
        else:
            expected_values = (
                list(check.expected)
                if isinstance(check.expected, (list, tuple, set))
                else [check.expected]
            )
            passed = actual in expected_values
            expectation = f"in {expected_values}"
        return {
            "metric": check.metric,
            "description": check.description,
            "comparator": check.comparator,
            "expected": check.expected,
            "expectation": expectation,
            "actual": actual,
            "passed": passed,
        }
