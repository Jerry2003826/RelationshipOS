from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True, frozen=True)
class ContentBlock:
    """A single block inside a multimodal message."""

    type: str  # "text" | "image_url" | "audio_url" | "file"
    text: str | None = None
    url: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class LLMMessage:
    role: str
    content: str | list[ContentBlock] = ""

    @property
    def text(self) -> str:
        """Extract plain text regardless of content format."""
        if isinstance(self.content, str):
            return self.content
        return " ".join(block.text for block in self.content if block.type == "text" and block.text)


@dataclass(slots=True, frozen=True)
class LLMToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class LLMToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(slots=True, frozen=True)
class LLMFailure:
    error_type: str
    message: str
    retryable: bool = False


@dataclass(slots=True, frozen=True)
class LLMRequest:
    messages: list[LLMMessage]
    model: str
    temperature: float = 0.2
    max_tokens: int = 400
    tools: list[LLMToolDefinition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    response_format: dict[str, Any] | None = None
    web_search_options: dict[str, Any] | None = None


@dataclass(slots=True, frozen=True)
class LLMResponse:
    model: str
    output_text: str
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    usage: LLMUsage | None = None
    latency_ms: int | None = None
    failure: LLMFailure | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


class LLMClient(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
