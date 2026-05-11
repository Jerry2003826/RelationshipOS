from __future__ import annotations

from typing import Any

from relationship_os.application.analyzers import build_runtime_quality_doctor_report


class RuntimeQualityDoctorRunner:
    def __init__(self, *, interval_turns: int, window_turns: int) -> None:
        self._interval_turns = max(0, interval_turns)
        self._window_turns = max(2, window_turns)

    def build_report(
        self,
        *,
        user_message: str,
        turn_context: Any,
        assistant_responses: list[str],
    ) -> Any | None:
        should_run_quality_doctor = (
            self._interval_turns > 0 and turn_context.turn_index % self._interval_turns == 0
        )
        if not should_run_quality_doctor:
            return None
        return build_runtime_quality_doctor_report(
            transcript_messages=turn_context.transcript_messages,
            user_message=user_message,
            assistant_responses=assistant_responses,
            triggered_turn_index=turn_context.turn_index,
            window_turns=self._window_turns,
        )
