import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from relationship_os.application.analyzers.emotional_prompt import (
    audit_unsupported_recall,
    audit_unsupported_recall_v2,
    build_emotional_prompt,
)
from relationship_os.application.memory_index import MemoryMediaAttachment
from relationship_os.domain.contracts.turn_input import TurnInput
from relationship_os.domain.event_types import (
    ASSISTANT_MESSAGE_SENT,
    MEMORY_RECALL_PERFORMED,
    RESPONSE_POST_AUDITED,
)
from relationship_os.domain.events import NewEvent
from relationship_os.domain.llm import LLMClient, LLMMessage, LLMRequest

logger = logging.getLogger(__name__)


class UnavailableLightRecallMemoryService:
    async def recall_person_memory(self, **_kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("Light recall memory service is unavailable")


@dataclass(slots=True)
class LightRecallReplyArtifacts:
    assistant_response: str | None
    assistant_responses: list[str]
    response_diagnostics: dict[str, Any]
    response_sequence_plan: Any | None
    response_post_audit: Any | None
    response_normalization: Any | None
    runtime_quality_doctor_report: Any | None
    events: list[NewEvent]


class LightRecallPipeline:
    """Runs the shallow memory path without invoking the deep expert DAG."""

    def __init__(
        self,
        *,
        memory_service: Any,
        llm_client: LLMClient,
        llm_model: str,
        llm_temperature: float,
        persona_text: str = "",
        entity_name: str = "Assistant",
        edge_max_memory_items: int = 3,
        edge_max_completion_tokens: int = 260,
    ) -> None:
        self._memory_service = memory_service
        self._llm_client = llm_client
        self._llm_model = llm_model
        self._llm_temperature = llm_temperature
        self._persona_text = persona_text
        self._entity_name = entity_name
        self._edge_max_memory_items = max(1, edge_max_memory_items)
        self._edge_max_completion_tokens = max(64, edge_max_completion_tokens)

    async def run(
        self,
        *,
        session_id: str,
        user_message: str,
        generate_reply: bool,
        turn_context: Any,
        turn_input: TurnInput | None = None,
        profile_prefix: str | None = None,
    ) -> LightRecallReplyArtifacts:
        memory_recall: dict[str, Any] = {"results": [], "recall_count": 0}
        recall_started = perf_counter()
        try:
            memory_recall = await self._memory_service.recall_person_memory(
                session_id=session_id,
                user_id=turn_context.user_id,
                query=user_message,
                limit=min(3, self._edge_max_memory_items),
                attachments=[
                    MemoryMediaAttachment(
                        type=attachment.type,
                        url=attachment.url,
                        mime_type=attachment.mime_type,
                        filename=attachment.filename,
                    )
                    for attachment in (turn_input.attachments if turn_input else [])
                ],
                enable_vector_search=True,
                enable_entity_vector_search=False,
                prefer_fast=True,
                include_factual_shadow=True,
            )
        except Exception:
            logger.warning("LIGHT_RECALL memory recall failed for session %s", session_id)
        recall_ms = round((perf_counter() - recall_started) * 1000.0, 1)
        memory_cards = self._light_recall_cards(memory_recall)
        memory_results = [
            dict(item)
            for item in list(memory_recall.get("results") or [])[: len(memory_cards) or 3]
            if isinstance(item, dict)
        ]

        base_events: list[NewEvent] = [
            NewEvent(
                event_type=MEMORY_RECALL_PERFORMED,
                payload={
                    "route": "LIGHT_RECALL",
                    "query": user_message[:240],
                    "recall_count": len(memory_cards),
                    "results": memory_results,
                    "conscience": dict(memory_recall.get("conscience") or {}),
                    "memory_cards": memory_cards,
                    "latency_ms": recall_ms,
                    "profile_prefix_injected": bool(profile_prefix),
                },
            )
        ]

        if not generate_reply:
            return LightRecallReplyArtifacts(
                assistant_response=None,
                assistant_responses=[],
                response_diagnostics={
                    "route": "LIGHT_RECALL",
                    "memory_card_count": len(memory_cards),
                    "profile_prefix_injected": bool(profile_prefix),
                    "recall_ms": recall_ms,
                },
                response_sequence_plan=None,
                response_post_audit=None,
                response_normalization=None,
                runtime_quality_doctor_report=None,
                events=base_events,
            )

        persona = f"Your name is {self._entity_name}.\n{self._persona_text}".strip()
        prompt = build_emotional_prompt(
            persona=persona,
            user_profile_prefix=profile_prefix,
            recent_memory=memory_cards,
            route="LIGHT_RECALL",
            emotion_tags=self._light_recall_emotion_tags(user_message),
            max_memory_cards=3,
            include_profile_vec=bool(profile_prefix),
        )

        recent_context = []
        for msg in turn_context.transcript_messages[-6:]:
            role = str(msg.get("role", "")).upper()
            content = msg.get("content", "")
            if role and content:
                recent_context.append(f"{role}: {content}")
        user_content = user_message
        if recent_context:
            user_content = (
                "Recent Conversation:\n"
                + "\n".join(recent_context)
                + f"\n\nUSER'S LATEST MESSAGE: {user_message}"
            )

        started = perf_counter()
        try:
            llm_response = await self._llm_client.complete(
                LLMRequest(
                    messages=[
                        LLMMessage(role="system", content=prompt.to_system_prompt()),
                        LLMMessage(role="user", content=user_content),
                    ],
                    model=self._llm_model,
                    temperature=min(0.7, float(self._llm_temperature)),
                    max_tokens=self._edge_max_completion_tokens,
                )
            )
            assistant_response = str(llm_response.output_text).strip()
            latency = llm_response.latency_ms
        except Exception:
            logger.warning("LIGHT_RECALL reply generation failed for session %s", session_id)
            assistant_response = "I'm here with you. I can keep this light and grounded."
            latency = int((perf_counter() - started) * 1000)

        unsupported = audit_unsupported_recall(assistant_response, memory_cards)
        binding_mismatches = audit_unsupported_recall_v2(assistant_response, memory_cards)
        response_audit = {
            "route": "LIGHT_RECALL",
            "status": "warn" if unsupported or binding_mismatches else "pass",
            "unsupported_recall": unsupported,
            "binding_mismatches": binding_mismatches,
        }
        base_events.extend(
            [
                NewEvent(
                    event_type=ASSISTANT_MESSAGE_SENT,
                    payload={"content": assistant_response},
                ),
                NewEvent(
                    event_type=RESPONSE_POST_AUDITED,
                    payload=response_audit,
                ),
            ]
        )

        return LightRecallReplyArtifacts(
            assistant_response=assistant_response,
            assistant_responses=[assistant_response],
            response_diagnostics={
                "route": "LIGHT_RECALL",
                "memory_card_count": len(memory_cards),
                "profile_prefix_injected": bool(profile_prefix),
                "recall_ms": recall_ms,
                "latency_ms": latency,
                "unsupported_recall_count": len(unsupported),
                "binding_mismatch_count": len(binding_mismatches),
            },
            response_sequence_plan=None,
            response_post_audit=response_audit,
            response_normalization=None,
            runtime_quality_doctor_report=None,
            events=base_events,
        )

    def _light_recall_cards(self, memory_recall: dict[str, Any]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for item in list(memory_recall.get("results") or [])[:3]:
            if not isinstance(item, dict):
                continue
            summary = str(
                item.get("summary")
                or item.get("value")
                or item.get("content")
                or item.get("text")
                or ""
            ).strip()
            if not summary:
                continue
            card = {
                "summary": summary[:260],
                "tags": list(item.get("tags") or item.get("categories") or [])[:3],
            }
            for key in ("entity", "entity_type", "category", "subject", "name", "type", "role"):
                if item.get(key):
                    card[key] = item[key]
            cards.append(card)
        return cards

    def _light_recall_emotion_tags(self, user_message: str) -> list[str]:
        text = user_message.lower()
        tags: list[str] = []
        cues = [
            ("tired", ("tired", "exhausted", "累", "疲", "困")),
            ("anxious", ("anxious", "worried", "焦虑", "紧张", "怕")),
            ("sad", ("sad", "down", "难过", "低落", "伤心")),
            ("angry", ("angry", "mad", "生气", "烦", "火")),
            ("confused", ("confused", "lost", "迷茫", "不知道")),
            ("happy", ("happy", "glad", "开心", "高兴")),
        ]
        for tag, terms in cues:
            if any(term in text for term in terms):
                tags.append(tag)
        return tags[:4]
