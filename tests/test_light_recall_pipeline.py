import asyncio
from types import SimpleNamespace

from relationship_os.application.runtime.light_recall_pipeline import LightRecallPipeline
from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import MEMORY_RECALL_PERFORMED


def test_light_recall_pipeline_uses_fast_person_recall_without_reply_generation() -> None:
    class _MemoryService:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def recall_person_memory(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            return {
                "results": [{"summary": "User likes quiet evening walks.", "tags": ["habit"]}],
                "conscience": {"mode": "allow"},
            }

    class _LLMClient:
        async def complete(self, _request):  # type: ignore[no-untyped-def]
            raise AssertionError("generate_reply=False should not call the LLM")

    memory_service = _MemoryService()
    pipeline = LightRecallPipeline(
        memory_service=memory_service,
        llm_client=_LLMClient(),
        llm_model="test-model",
        llm_temperature=0.2,
    )
    turn_context = SimpleNamespace(user_id="user-1", transcript_messages=[])

    result = asyncio.run(
        pipeline.run(
            session_id="session-1",
            user_message="Do you remember what helps me unwind?",
            generate_reply=False,
            turn_context=turn_context,
            turn_input=TurnInput(text="Do you remember what helps me unwind?"),
            profile_prefix="calm, low-pressure",
        )
    )

    assert memory_service.calls[0]["prefer_fast"] is True
    assert memory_service.calls[0]["enable_entity_vector_search"] is False
    assert memory_service.calls[0]["include_factual_shadow"] is True
    assert result.assistant_response is None
    assert result.response_diagnostics["route"] == "LIGHT_RECALL"
    assert result.response_diagnostics["profile_prefix_injected"] is True
    assert result.events[0].event_type == MEMORY_RECALL_PERFORMED
    assert result.events[0].payload["memory_cards"][0]["summary"] == (
        "User likes quiet evening walks."
    )


def test_light_recall_pipeline_detects_chinese_emotion_cues() -> None:
    pipeline = LightRecallPipeline(
        memory_service=object(),
        llm_client=object(),
        llm_model="test-model",
        llm_temperature=0.2,
    )

    assert "tired" in pipeline._light_recall_emotion_tags("今天真的有点累")
    assert "anxious" in pipeline._light_recall_emotion_tags("我有点焦虑")
    assert "happy" in pipeline._light_recall_emotion_tags("刚刚挺开心的")
