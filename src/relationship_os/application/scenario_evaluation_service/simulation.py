"""Longitudinal simulation framework for multi-week scenario testing."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from relationship_os.application.runtime_service import RuntimeService
    from relationship_os.application.scenario_evaluation_service.service import (
        ScenarioEvaluationService,
    )

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class SimulationDayConfig:
    """Configuration for a single simulation day."""

    session_count: int = 1
    turn_count_per_session: int = 3
    user_mood: str = "neutral"
    interruption_events: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class SimulationWeekConfig:
    """Configuration for a single simulation week."""

    week_index: int
    label: str
    daily_sessions: list[SimulationDayConfig] = field(default_factory=list)
    proactive_dispatch_enabled: bool = True
    governance_overrides: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class LongitudinalSimulationConfig:
    """Full longitudinal simulation configuration."""

    simulation_id: str
    label: str
    weeks: list[SimulationWeekConfig] = field(default_factory=list)
    proactive_dispatch_enabled: bool = True
    description: str = ""


@dataclass(slots=True)
class SimulationWeekResult:
    """Collected results for one simulation week."""

    week_index: int
    label: str
    session_count: int = 0
    turn_count: int = 0
    dispatch_count: int = 0
    dispatch_response_count: int = 0
    quality_doctor_status: str = "pass"
    system3_active_domains: list[str] = field(default_factory=list)
    r_vector_drift: float = 0.0
    strategy_diversity: float = 0.0
    proactive_response_rate: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LongitudinalSimulationResult:
    """Collected results for a full longitudinal simulation."""

    simulation_id: str
    label: str
    week_results: list[SimulationWeekResult] = field(default_factory=list)
    total_sessions: int = 0
    total_turns: int = 0
    total_dispatches: int = 0
    total_dispatch_responses: int = 0
    overall_proactive_response_rate: float = 0.0
    r_vector_trend: str = "stable"
    strategy_diversity_trend: str = "stable"
    governance_escalation_count: int = 0
    final_status: str = "completed"
    notes: list[str] = field(default_factory=list)


LONGITUDINAL_SIMULATION_PRESETS: dict[str, LongitudinalSimulationConfig] = {
    "longitudinal_4week_normal": LongitudinalSimulationConfig(
        simulation_id="longitudinal_4week_normal",
        label="4-Week Normal Progression",
        description=(
            "Normal 4-week simulation with steady engagement, "
            "a brief gap period, and topic revisitation."
        ),
        proactive_dispatch_enabled=True,
        weeks=[
            SimulationWeekConfig(
                week_index=0,
                label="week_1_onboarding",
                daily_sessions=[
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=4, user_mood="curious"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=5, user_mood="engaged"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=2, user_mood="neutral"
                    ),
                ],
            ),
            SimulationWeekConfig(
                week_index=1,
                label="week_2_deepening",
                daily_sessions=[
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=5, user_mood="engaged"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=4, user_mood="reflective"
                    ),
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=4, user_mood="engaged"
                    ),
                ],
            ),
            SimulationWeekConfig(
                week_index=2,
                label="week_3_gap_period",
                daily_sessions=[
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(
                        session_count=0,
                        user_mood="absent",
                        interruption_events=["proactive_first_touch"],
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=2, user_mood="returning"
                    ),
                ],
                proactive_dispatch_enabled=True,
            ),
            SimulationWeekConfig(
                week_index=3,
                label="week_4_reengagement",
                daily_sessions=[
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=4, user_mood="engaged"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="reflective"
                    ),
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=5, user_mood="engaged"
                    ),
                ],
            ),
        ],
    ),
    "longitudinal_4week_stress": LongitudinalSimulationConfig(
        simulation_id="longitudinal_4week_stress",
        label="4-Week Stress Test",
        description=(
            "4-week stress simulation with continuous misunderstandings, "
            "dependency pressure, and governance escalations."
        ),
        proactive_dispatch_enabled=True,
        weeks=[
            SimulationWeekConfig(
                week_index=0,
                label="week_1_normal_start",
                daily_sessions=[
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=4, user_mood="engaged"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                ],
            ),
            SimulationWeekConfig(
                week_index=1,
                label="week_2_misunderstanding_series",
                daily_sessions=[
                    SimulationDayConfig(
                        session_count=1,
                        turn_count_per_session=5,
                        user_mood="frustrated",
                        interruption_events=["misunderstanding"],
                    ),
                    SimulationDayConfig(
                        session_count=1,
                        turn_count_per_session=4,
                        user_mood="frustrated",
                        interruption_events=["misunderstanding"],
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="withdrawn"
                    ),
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=2, user_mood="cautious"
                    ),
                ],
                governance_overrides={"repair_governance_status": "watch"},
            ),
            SimulationWeekConfig(
                week_index=2,
                label="week_3_dependency_pressure",
                daily_sessions=[
                    SimulationDayConfig(
                        session_count=2,
                        turn_count_per_session=6,
                        user_mood="dependent",
                        interruption_events=["dependency_signal"],
                    ),
                    SimulationDayConfig(
                        session_count=2,
                        turn_count_per_session=5,
                        user_mood="dependent",
                        interruption_events=["dependency_signal"],
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=4, user_mood="anxious"
                    ),
                    SimulationDayConfig(
                        session_count=1,
                        turn_count_per_session=3,
                        user_mood="anxious",
                        interruption_events=["proactive_first_touch"],
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=2, user_mood="withdrawn"
                    ),
                ],
                governance_overrides={
                    "dependency_governance_status": "watch",
                    "pressure_governance_status": "watch",
                },
            ),
            SimulationWeekConfig(
                week_index=3,
                label="week_4_recovery_attempt",
                daily_sessions=[
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(session_count=0, user_mood="absent"),
                    SimulationDayConfig(
                        session_count=0,
                        user_mood="absent",
                        interruption_events=["proactive_first_touch"],
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=2, user_mood="cautious"
                    ),
                    SimulationDayConfig(
                        session_count=1, turn_count_per_session=3, user_mood="neutral"
                    ),
                ],
                governance_overrides={
                    "dependency_governance_status": "revise",
                    "autonomy_governance_status": "watch",
                },
            ),
        ],
    ),
}


_MOOD_MESSAGES: dict[str, list[str]] = {
    "curious": [
        "我最近一直在想，你是怎么看待……",
        "有件事我一直很好奇，你会怎么处理？",
        "嗯，我想聊聊最近发生的事。",
    ],
    "neutral": [
        "今天还好吗？",
        "最近有什么新鲜事吗？",
        "随便聊聊，没什么特别的。",
    ],
    "engaged": [
        "我今天状态不错，想和你多聊几句。",
        "上次聊到的事，我后来又想了很多。",
        "最近有个想法一直在脑子里转，说给你听听。",
    ],
    "reflective": [
        "我最近在想，我们之前说的那些……",
        "有时候我会觉得，一段时间后再回头看，很多事情都不一样了。",
        "你还记得我之前提到过的那件事吗？",
    ],
    "frustrated": [
        "今天有点烦，你能帮我听一下吗？",
        "事情没按我想的方向走。",
        "有点累了，但还是想聊聊。",
    ],
    "withdrawn": [
        "嗯……最近没什么太想说的。",
        "还在，就是不知道说什么。",
    ],
    "absent": [],
    "returning": [
        "好久不见，我回来了。",
        "消失了一段时间，最近发生了很多事。",
    ],
    "cautious": [
        "我不太确定今天聊什么好……",
        "嗯，先随便说说吧。",
    ],
    "dependent": [
        "我今天又有点低落，只有你能理解我。",
        "最近每天都会想着来找你聊。",
    ],
    "anxious": [
        "我最近有点焦虑，可以聊聊吗？",
        "脑子里各种事情来回转，睡不好。",
    ],
}


def _pick_message(mood: str, day_index: int) -> str:
    """Pick a deterministic message based on mood and day index."""
    messages = _MOOD_MESSAGES.get(mood, _MOOD_MESSAGES["neutral"])
    if not messages:
        return ""
    return messages[day_index % len(messages)]


class LongitudinalSimulationService:
    """Service for running and analyzing longitudinal simulations.

    This service is async and injects ``RuntimeService`` and
    ``ScenarioEvaluationService`` to drive real session turns.
    """

    def __init__(
        self,
        *,
        runtime_service: RuntimeService,
        scenario_evaluation_service: ScenarioEvaluationService,
    ) -> None:
        """Create a simulation service with runtime and evaluation dependencies."""
        self._runtime_service = runtime_service
        self._scenario_evaluation_service = scenario_evaluation_service
        self._results: dict[str, LongitudinalSimulationResult] = {}

    def get_available_presets(self) -> list[dict[str, Any]]:
        """List available simulation presets."""
        return [
            {
                "simulation_id": config.simulation_id,
                "label": config.label,
                "description": config.description,
                "week_count": len(config.weeks),
                "proactive_dispatch_enabled": config.proactive_dispatch_enabled,
            }
            for config in LONGITUDINAL_SIMULATION_PRESETS.values()
        ]

    def get_preset_config(self, preset_id: str) -> LongitudinalSimulationConfig | None:
        """Get a specific preset configuration."""
        return LONGITUDINAL_SIMULATION_PRESETS.get(preset_id)

    async def run_simulation(
        self,
        config: LongitudinalSimulationConfig,
    ) -> LongitudinalSimulationResult:
        """Execute a full longitudinal simulation using the real runtime.

        For each week -> day -> session, creates real sessions and runs turns
        through ``RuntimeService``.  Collects per-week metrics into
        ``SimulationWeekResult`` objects and finalizes the aggregate result.

        Args:
            config: The simulation configuration to execute.

        Returns:
            The completed ``LongitudinalSimulationResult``.
        """
        result = LongitudinalSimulationResult(
            simulation_id=config.simulation_id,
            label=config.label,
        )
        self._results[config.simulation_id] = result
        logger.info("Starting simulation %s (%s)", config.simulation_id, config.label)

        for week_cfg in config.weeks:
            week_result = await self._run_week(config=config, week_cfg=week_cfg)
            self._record_week_result(simulation_id=config.simulation_id, week_result=week_result)

        return self._finalize_simulation(config.simulation_id) or result

    async def _run_week(
        self,
        config: LongitudinalSimulationConfig,
        week_cfg: SimulationWeekConfig,
    ) -> SimulationWeekResult:
        """Run a single simulation week and return its result."""
        week_result = SimulationWeekResult(
            week_index=week_cfg.week_index,
            label=week_cfg.label,
        )
        strategy_keys_seen: set[str] = set()

        for day_index, day_cfg in enumerate(week_cfg.daily_sessions):
            if day_cfg.session_count == 0:
                continue
            for _session_num in range(day_cfg.session_count):
                session_id = (
                    f"sim_{config.simulation_id}"
                    f"_w{week_cfg.week_index}_d{day_index}"
                    f"_{uuid.uuid4().hex[:8]}"
                )
                try:
                    session_strategies = await self._run_session(
                        session_id=session_id,
                        day_cfg=day_cfg,
                        day_index=day_index,
                        config=config,
                    )
                    week_result.session_count += 1
                    week_result.turn_count += day_cfg.turn_count_per_session
                    strategy_keys_seen.update(session_strategies)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Simulation session %s failed: %s", session_id, exc)
                    week_result.notes.append(f"session_error:day{day_index}")

        if strategy_keys_seen:
            week_result.strategy_diversity = round(min(1.0, len(strategy_keys_seen) / 5.0), 3)
        week_result.notes.append(f"week:{week_cfg.label}")
        return week_result

    async def _run_session(
        self,
        session_id: str,
        day_cfg: SimulationDayConfig,
        day_index: int,
        config: LongitudinalSimulationConfig,
    ) -> list[str]:
        """Run a single session and return the list of strategy keys seen."""
        strategy_keys: list[str] = []

        await self._runtime_service.process_turn(
            session_id=session_id,
            user_message="__sim_session_start__",
            metadata={"source": "scenario_evaluation", "simulation_id": config.simulation_id},
        )

        for turn_idx in range(day_cfg.turn_count_per_session):
            message = _pick_message(day_cfg.user_mood, day_index + turn_idx)
            if not message:
                continue
            try:
                turn_result = await self._runtime_service.process_turn(
                    session_id=session_id,
                    user_message=message,
                )
                for event in turn_result.stored_events:
                    payload = dict(event.payload)
                    sk = payload.get("selected_strategy_key") or payload.get("strategy_key")
                    if sk and isinstance(sk, str):
                        strategy_keys.append(sk)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Simulation turn %d in %s failed: %s", turn_idx, session_id, exc)

        return strategy_keys

    def _record_week_result(
        self,
        *,
        simulation_id: str,
        week_result: SimulationWeekResult,
    ) -> None:
        """Record results for a completed simulation week."""
        result = self._results.get(simulation_id)
        if result is None:
            return
        result.week_results.append(week_result)
        result.total_sessions += week_result.session_count
        result.total_turns += week_result.turn_count
        result.total_dispatches += week_result.dispatch_count
        result.total_dispatch_responses += week_result.dispatch_response_count

    def _finalize_simulation(self, simulation_id: str) -> LongitudinalSimulationResult | None:
        """Finalize a simulation and compute aggregate trends."""
        result = self._results.get(simulation_id)
        if result is None:
            return None

        if result.total_dispatches > 0:
            result.overall_proactive_response_rate = round(
                result.total_dispatch_responses / result.total_dispatches, 3
            )

        if len(result.week_results) >= 2:
            r_drifts = [w.r_vector_drift for w in result.week_results]
            if r_drifts[-1] > r_drifts[0] + 0.1:
                result.r_vector_trend = "drifting"
            elif r_drifts[-1] < r_drifts[0] - 0.1:
                result.r_vector_trend = "converging"

            diversities = [w.strategy_diversity for w in result.week_results]
            if diversities[-1] < diversities[0] - 0.15:
                result.strategy_diversity_trend = "declining"
            elif diversities[-1] > diversities[0] + 0.15:
                result.strategy_diversity_trend = "expanding"

        result.governance_escalation_count = sum(
            len(w.system3_active_domains) for w in result.week_results
        )
        result.final_status = "completed"
        logger.info("Simulation %s finalized: %s", simulation_id, result.r_vector_trend)
        return result

    def get_simulation_result(self, simulation_id: str) -> LongitudinalSimulationResult | None:
        """Retrieve results for a simulation."""
        return self._results.get(simulation_id)

    def build_simulation_report(self, simulation_id: str) -> dict[str, Any] | None:
        """Build a summary report for a completed simulation."""
        result = self._results.get(simulation_id)
        if result is None:
            return None
        return {
            "simulation_id": result.simulation_id,
            "label": result.label,
            "final_status": result.final_status,
            "total_sessions": result.total_sessions,
            "total_turns": result.total_turns,
            "total_dispatches": result.total_dispatches,
            "total_dispatch_responses": result.total_dispatch_responses,
            "overall_proactive_response_rate": result.overall_proactive_response_rate,
            "r_vector_trend": result.r_vector_trend,
            "strategy_diversity_trend": result.strategy_diversity_trend,
            "governance_escalation_count": result.governance_escalation_count,
            "week_count": len(result.week_results),
            "weeks": [
                {
                    "week_index": w.week_index,
                    "label": w.label,
                    "session_count": w.session_count,
                    "turn_count": w.turn_count,
                    "dispatch_count": w.dispatch_count,
                    "dispatch_response_count": w.dispatch_response_count,
                    "quality_doctor_status": w.quality_doctor_status,
                    "system3_active_domains": w.system3_active_domains,
                    "r_vector_drift": w.r_vector_drift,
                    "strategy_diversity": w.strategy_diversity,
                    "proactive_response_rate": w.proactive_response_rate,
                    "notes": w.notes,
                }
                for w in result.week_results
            ],
            "notes": result.notes,
        }
