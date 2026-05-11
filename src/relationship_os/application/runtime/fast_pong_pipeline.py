import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from relationship_os.domain.event_types import ASSISTANT_MESSAGE_SENT
from relationship_os.domain.events import NewEvent
from relationship_os.domain.llm import LLMClient, LLMMessage, LLMRequest

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FastPongReplyArtifacts:
    assistant_response: str | None
    assistant_responses: list[str]
    response_diagnostics: dict[str, Any]
    response_sequence_plan: Any | None
    response_post_audit: Any | None
    response_normalization: Any | None
    runtime_quality_doctor_report: Any | None
    events: list[NewEvent]


class FastPongPipeline:
    """Runs the ultra-light reply path without memory or expert analysis."""

    def __init__(
        self,
        *,
        llm_client: LLMClient,
        llm_model: str,
        llm_temperature: float,
        persona_text: str = "",
        entity_name: str = "Assistant",
        edge_max_completion_tokens: int = 260,
    ) -> None:
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._llm_temperature = llm_temperature
        self._persona_text = persona_text
        self._entity_name = entity_name
        self._edge_max_completion_tokens = max(64, edge_max_completion_tokens)

    async def run(
        self,
        *,
        user_message: str,
        generate_reply: bool,
        turn_context: Any,
    ) -> FastPongReplyArtifacts:
        if not generate_reply:
            return FastPongReplyArtifacts(
                assistant_response=None,
                assistant_responses=[],
                response_diagnostics={},
                response_sequence_plan=None,
                response_post_audit=None,
                response_normalization=None,
                runtime_quality_doctor_report=None,
                events=[],
            )

        recent_context = []
        for msg in turn_context.transcript_messages[-6:]:
            role = str(msg.get("role", "")).upper()
            content = msg.get("content", "")
            if role and content:
                recent_context.append(f"{role}: {content}")

        context_str = "\n".join(recent_context)
        system_prompt = (
            f"Your name is {self._entity_name}. "
            f"Keep your response extremely brief, casual, and human-like.\n"
            f"If appropriate, reply using a similar tone and length as the user.\n"
            f"Persona: {self._persona_text}"
        ).strip()

        messages = [LLMMessage(role="system", content=system_prompt)]
        if context_str:
            messages.append(
                LLMMessage(
                    role="user",
                    content=(
                        f"Recent Conversation:\n{context_str}"
                        f"\n\nUSER'S LATEST MESSAGE: {user_message}"
                    ),
                )
            )
        else:
            messages.append(LLMMessage(role="user", content=user_message))

        started = perf_counter()
        try:
            llm_response = await self._llm_client.complete(
                LLMRequest(
                    messages=messages,
                    model=self._llm_model,
                    temperature=min(0.6, float(self._llm_temperature)),
                    max_tokens=self._edge_max_completion_tokens,
                )
            )
            assistant_response = str(llm_response.output_text).strip()
            latency = llm_response.latency_ms
        except Exception as exc:
            logger.warning("Fast pong generation failed: %s", exc)
            assistant_response = "..."
            latency = int((perf_counter() - started) * 1000)

        events: list[NewEvent] = [
            NewEvent(
                event_type=ASSISTANT_MESSAGE_SENT,
                payload={"content": assistant_response},
            )
        ]

        return FastPongReplyArtifacts(
            assistant_response=assistant_response,
            assistant_responses=[assistant_response],
            response_diagnostics={"fast_pong": True, "latency_ms": latency},
            response_sequence_plan=None,
            response_post_audit=None,
            response_normalization=None,
            runtime_quality_doctor_report=None,
            events=events,
        )

