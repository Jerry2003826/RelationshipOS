import asyncio
from types import SimpleNamespace

from relationship_os.application.runtime.fast_pong_pipeline import FastPongPipeline
from relationship_os.domain.event_types import ASSISTANT_MESSAGE_SENT
from relationship_os.domain.llm import LLMResponse


def test_fast_pong_pipeline_skips_llm_when_reply_generation_disabled() -> None:
    class _LLMClient:
        async def complete(self, _request):  # type: ignore[no-untyped-def]
            raise AssertionError("generate_reply=False should not call the LLM")

    pipeline = FastPongPipeline(
        llm_client=_LLMClient(),
        llm_model="test-model",
        llm_temperature=0.2,
    )

    result = asyncio.run(
        pipeline.run(
            user_message="hi",
            generate_reply=False,
            turn_context=SimpleNamespace(transcript_messages=[]),
        )
    )

    assert result.assistant_response is None
    assert result.assistant_responses == []
    assert result.events == []


def test_fast_pong_pipeline_generates_brief_reply_with_recent_context() -> None:
    class _LLMClient:
        def __init__(self) -> None:
            self.requests = []

        async def complete(self, request):  # type: ignore[no-untyped-def]
            self.requests.append(request)
            return LLMResponse(model=request.model, output_text="嗯，在。", latency_ms=12)

    llm_client = _LLMClient()
    pipeline = FastPongPipeline(
        llm_client=llm_client,
        llm_model="test-model",
        llm_temperature=0.9,
        persona_text="Warm and concise.",
        entity_name="RelationshipOS",
        edge_max_completion_tokens=180,
    )

    result = asyncio.run(
        pipeline.run(
            user_message="在吗",
            generate_reply=True,
            turn_context=SimpleNamespace(
                transcript_messages=[
                    {"role": "user", "content": "刚刚有点累"},
                    {"role": "assistant", "content": "先慢一点。"},
                ]
            ),
        )
    )

    request = llm_client.requests[0]
    assert request.model == "test-model"
    assert request.temperature == 0.6
    assert request.max_tokens == 180
    assert "Recent Conversation" in request.messages[1].content
    assert result.assistant_response == "嗯，在。"
    assert result.response_diagnostics == {"fast_pong": True, "latency_ms": 12}
    assert result.events[0].event_type == ASSISTANT_MESSAGE_SENT
    assert result.events[0].payload == {"content": "嗯，在。"}

