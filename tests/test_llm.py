from relationship_os.application.llm import LiteLLMClient
from relationship_os.domain.llm import LLMMessage, LLMRequest, LLMResponse, LLMUsage


class FakeLiteLLMResponse:
    def __init__(self) -> None:
        self.model = "openai/gpt-5"
        self.choices = [
            {
                "message": {
                    "content": "hello from litellm",
                    "tool_calls": [],
                }
            }
        ]
        self.usage = LLMUsage(
            prompt_tokens=12,
            completion_tokens=8,
            total_tokens=20,
        )


def test_litellm_client_maps_success_response() -> None:
    client = LiteLLMClient(model="openai/gpt-5")
    client._load_completion_callable = lambda: (  # type: ignore[method-assign]
        lambda **_: FakeLiteLLMResponse()
    )

    response = __import__("asyncio").run(
        client.complete(LLMRequest(messages=[], model="openai/gpt-5"))
    )

    assert isinstance(response, LLMResponse)
    assert response.output_text == "hello from litellm"
    assert response.usage is not None
    assert response.failure is None


def test_litellm_client_maps_failure_response() -> None:
    client = LiteLLMClient(model="openai/gpt-5")

    def raise_timeout(**_: object) -> object:
        raise TimeoutError("timed out")

    client._load_completion_callable = lambda: raise_timeout  # type: ignore[method-assign]

    response = __import__("asyncio").run(
        client.complete(LLMRequest(messages=[], model="openai/gpt-5"))
    )

    assert response.failure is not None
    assert response.failure.error_type == "TimeoutError"
    assert response.failure.retryable is True


def test_litellm_client_merges_multiple_system_for_minimax() -> None:
    captured: dict[str, object] = {}
    client = LiteLLMClient(model="minimax/M2-her")

    def capture_completion(**kwargs: object) -> object:
        captured.update(kwargs)
        return FakeLiteLLMResponse()

    client._load_completion_callable = lambda: capture_completion  # type: ignore[method-assign]

    import asyncio

    asyncio.run(
        client.complete(
            LLMRequest(
                messages=[
                    LLMMessage(role="system", content="alpha"),
                    LLMMessage(role="system", content="beta"),
                    LLMMessage(role="user", content="hi"),
                ],
                model="minimax/M2-her",
            )
        )
    )
    messages = captured["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "alpha" in messages[0]["content"] and "beta" in messages[0]["content"]
    assert messages[1]["role"] == "user"


def test_litellm_client_leaves_system_messages_for_non_minimax() -> None:
    captured: dict[str, object] = {}
    client = LiteLLMClient(model="openai/gpt-5")

    def capture_completion(**kwargs: object) -> object:
        captured.update(kwargs)
        return FakeLiteLLMResponse()

    client._load_completion_callable = lambda: capture_completion  # type: ignore[method-assign]

    import asyncio

    asyncio.run(
        client.complete(
            LLMRequest(
                messages=[
                    LLMMessage(role="system", content="a"),
                    LLMMessage(role="system", content="b"),
                    LLMMessage(role="user", content="hi"),
                ],
                model="openai/gpt-5",
            )
        )
    )
    messages = captured["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 3
