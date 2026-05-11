from types import SimpleNamespace

from relationship_os.application.runtime.runtime_quality_doctor_runner import (
    RuntimeQualityDoctorRunner,
)


def test_runtime_quality_doctor_runner_skips_when_not_due_or_disabled() -> None:
    turn_context = SimpleNamespace(turn_index=3, transcript_messages=[])

    disabled = RuntimeQualityDoctorRunner(interval_turns=0, window_turns=2)
    not_due = RuntimeQualityDoctorRunner(interval_turns=5, window_turns=2)

    assert (
        disabled.build_report(
            user_message="hello",
            turn_context=turn_context,
            assistant_responses=["hi"],
        )
        is None
    )
    assert (
        not_due.build_report(
            user_message="hello",
            turn_context=turn_context,
            assistant_responses=["hi"],
        )
        is None
    )


def test_runtime_quality_doctor_runner_builds_report_when_due() -> None:
    turn_context = SimpleNamespace(
        turn_index=4,
        transcript_messages=[
            {"role": "assistant", "content": "same opening here"},
            {"role": "assistant", "content": "same opening again"},
        ],
    )

    report = RuntimeQualityDoctorRunner(interval_turns=2, window_turns=3).build_report(
        user_message="hello",
        turn_context=turn_context,
        assistant_responses=["same opening third"],
    )

    assert report is not None
    assert report.triggered_turn_index == 4
    assert report.window_turn_count == 3
