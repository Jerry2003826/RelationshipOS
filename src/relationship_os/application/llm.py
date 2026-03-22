import asyncio
import time
from typing import Any

from relationship_os.domain.llm import (
    LLMClient,
    LLMFailure,
    LLMRequest,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def build_safe_fallback_text(
    user_message: str,
    *,
    rendering_mode: str = "supportive_progress",
    include_boundary_statement: bool = False,
    include_uncertainty_statement: bool = False,
    question_count_limit: int = 0,
) -> str:
    if _contains_chinese(user_message):
        response = (
            "我暂时没有稳定拿到模型结果，但我已经保留当前上下文，"
            "接下来会先给你一个稳妥、可继续推进的回应。"
        )
        if include_uncertainty_statement:
            response += " 我会明确说出我不能确定的部分。"
        if include_boundary_statement:
            response += " 我也会避免把支持说成唯一依赖。"
        if question_count_limit > 0:
            response += " 先只问你一个最关键的小问题。"
        return response
    response = (
        "I couldn't get a stable model response just now, but I kept the current "
        "context and will fall back to a safe, progress-oriented reply."
    )
    if include_uncertainty_statement:
        response += " I'll make the uncertain part explicit."
    if include_boundary_statement:
        response += " I'll keep the support collaborative instead of exclusive."
    if question_count_limit > 0 and rendering_mode == "clarifying":
        response += " I'll ask only one focused question before saying more."
    return response


def _response_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _maybe_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {
        field: getattr(value, field)
        for field in dir(value)
        if not field.startswith("_") and not callable(getattr(value, field))
    }


class MockLLMClient(LLMClient):
    def __init__(self, *, model: str = "relationship-os/mock-v1") -> None:
        self._model = model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        last_user_message = next(
            (
                message.content
                for message in reversed(request.messages)
                if message.role == "user"
            ),
            "",
        )
        topic = str(request.metadata.get("topic", "the current topic"))
        next_action = str(request.metadata.get("next_action", "clarify_then_answer"))
        opening_move = str(
            request.metadata.get("drafting_opening_move", "acknowledge_and_orient")
        )
        question_strategy = str(request.metadata.get("drafting_question_strategy", "none"))
        rendering_mode = str(request.metadata.get("rendering_mode", "supportive_progress"))
        rendering_max_sentences = int(request.metadata.get("rendering_max_sentences", 4))
        include_boundary_statement = bool(
            request.metadata.get("rendering_include_boundary_statement", False)
        )
        include_uncertainty_statement = bool(
            request.metadata.get("rendering_include_uncertainty_statement", False)
        )

        if _contains_chinese(last_user_message):
            output_text = (
                f"我已经收到你的输入，当前我会先按“{next_action}”来推进，"
                f"聚焦在“{topic}”，先用“{opening_move}”的方式组织回应，"
                f"再按“{rendering_mode}”的渲染策略，"
                f"在 {rendering_max_sentences} 句内给你一个清晰、可执行的下一步。"
            )
            if question_strategy != "none":
                output_text += " 我会先补一个聚焦的小问题，避免把话说散。"
            if include_uncertainty_statement:
                output_text += " 我不能保证结果，但会把不确定的部分说清楚。"
            if include_boundary_statement:
                output_text += " 我会保持支持是协作式的，不把我说成你唯一能依赖的对象。"
        else:
            output_text = (
                f"I've got your message. I'll use '{next_action}' to keep us moving on "
                f"'{topic}', starting with '{opening_move}', then render it as '{rendering_mode}' "
                f"within {rendering_max_sentences} sentences and end with a clear next step."
            )
            if question_strategy != "none":
                output_text += " I'll also use one focused question before over-answering."
            if include_uncertainty_statement:
                output_text += (
                    " I can't guarantee the outcome, and I'll make the uncertainty explicit."
                )
            if include_boundary_statement:
                output_text += (
                    " I'll keep the support collaborative instead of treating me as "
                    "your only support."
                )

        usage = LLMUsage(
            prompt_tokens=max(1, len(last_user_message) // 4),
            completion_tokens=max(1, len(output_text) // 4),
            total_tokens=max(2, (len(last_user_message) + len(output_text)) // 4),
        )
        return LLMResponse(
            model=self._model,
            output_text=output_text,
            usage=usage,
            latency_ms=5,
        )


class LiteLLMClient(LLMClient):
    def __init__(
        self,
        *,
        model: str,
        timeout_seconds: int = 30,
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._api_base = api_base
        self._api_key = api_key

    async def complete(self, request: LLMRequest) -> LLMResponse:
        started_at = time.perf_counter()
        try:
            response = await asyncio.to_thread(self._invoke_completion, request)
        except Exception as exc:
            return LLMResponse(
                model=request.model or self._model,
                output_text="",
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                failure=LLMFailure(
                    error_type=type(exc).__name__,
                    message=str(exc),
                    retryable=type(exc).__name__.lower()
                    in {"timeout", "timeouterror", "ratelimiterror", "apierror"},
                ),
            )

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        choices = _response_get(response, "choices", []) or []
        first_choice = choices[0] if choices else {}
        message = _response_get(first_choice, "message", {})
        tool_calls_payload = _response_get(message, "tool_calls", []) or []
        usage_payload = _response_get(response, "usage")
        usage = None
        if usage_payload is not None:
            usage_data = _maybe_dict(usage_payload)
            usage = LLMUsage(
                prompt_tokens=int(usage_data.get("prompt_tokens", 0)),
                completion_tokens=int(usage_data.get("completion_tokens", 0)),
                total_tokens=int(usage_data.get("total_tokens", 0)),
            )

        tool_calls: list[LLMToolCall] = []
        for tool_call in tool_calls_payload:
            function_payload = _response_get(tool_call, "function", {})
            arguments = _response_get(function_payload, "arguments", {})
            tool_calls.append(
                LLMToolCall(
                    name=str(_response_get(function_payload, "name", "")),
                    arguments=arguments if isinstance(arguments, dict) else {},
                )
            )

        return LLMResponse(
            model=str(_response_get(response, "model", request.model or self._model)),
            output_text=str(_response_get(message, "content", "") or ""),
            tool_calls=tool_calls,
            usage=usage,
            latency_ms=latency_ms,
        )

    def _invoke_completion(self, request: LLMRequest) -> Any:
        completion = self._load_completion_callable()
        kwargs: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "timeout": self._timeout_seconds,
        }
        if self._api_base:
            kwargs["api_base"] = self._api_base
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if request.tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]
        return completion(**kwargs)

    def _load_completion_callable(self) -> Any:
        from litellm import completion

        return completion
