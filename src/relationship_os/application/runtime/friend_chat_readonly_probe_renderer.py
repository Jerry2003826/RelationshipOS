from __future__ import annotations

import logging
from typing import Any

from relationship_os.application.runtime.friend_chat_probe_contracts import (
    build_friend_chat_probe_user_prompt,
)
from relationship_os.application.runtime.friend_chat_probe_messages import (
    build_friend_chat_compact_probe_messages,
)
from relationship_os.application.runtime.friend_chat_probe_render_messages import (
    build_friend_chat_plaintext_probe_repair_messages,
    build_friend_chat_probe_runtime_card,
    build_friend_chat_structured_probe_messages,
    build_friend_chat_structured_probe_repair_messages,
    coerce_friend_chat_structured_probe_response,
)
from relationship_os.application.runtime.friend_chat_probe_repair import (
    build_friend_chat_probe_repair_feedback,
)
from relationship_os.domain.llm import LLMClient, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


async def render_friend_chat_readonly_probe_response(
    *,
    llm_client: LLMClient,
    llm_model: str,
    user_message: str,
    probe_plan: dict[str, Any],
    llm_metadata: dict[str, Any],
) -> LLMResponse:
    probe_kind = str(probe_plan.get("probe_kind", "") or "").strip()
    logger.info("friend_chat_structured_probe_render_attempted probe_kind=%s", probe_kind)
    primary_response = await llm_client.complete(
        LLMRequest(
            messages=build_friend_chat_structured_probe_messages(
                user_message=user_message,
                probe_plan=probe_plan,
            ),
            model=llm_model,
            temperature=0.0,
            max_tokens=220,
            response_format={"type": "json_object"},
            metadata={
                **llm_metadata,
                "rendering_mode": "classification_only",
                "friend_chat_structured_probe_render": True,
            },
        )
    )
    normalized_primary = coerce_friend_chat_structured_probe_response(
        primary_response,
        probe_kind=probe_kind,
    )
    primary_repair_feedback = (
        build_friend_chat_probe_repair_feedback(
            dict(normalized_primary.diagnostics or {}),
            probe_plan,
        )
        if normalized_primary is not None
        else None
    )
    if normalized_primary is not None:
        if primary_repair_feedback is None:
            logger.info(
                "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
                probe_kind,
                "json_object",
            )
            return normalized_primary
        logger.info(
            "friend_chat_structured_probe_regrounding_attempted "
            "probe_kind=%s stage=%s reasons=%s",
            probe_kind,
            "json_object",
            ",".join(primary_repair_feedback.get("reason_codes") or []),
        )

    logger.info("friend_chat_structured_probe_relaxed_repair_attempted probe_kind=%s", probe_kind)
    repair_response = await llm_client.complete(
        LLMRequest(
            messages=build_friend_chat_structured_probe_repair_messages(
                user_message=user_message,
                probe_plan=probe_plan,
                invalid_output=primary_response.output_text,
                repair_feedback=primary_repair_feedback,
            ),
            model=llm_model,
            temperature=0.0,
            max_tokens=220,
            metadata={
                **llm_metadata,
                "rendering_mode": "classification_only",
                "friend_chat_structured_probe_render": True,
                "friend_chat_structured_probe_repair": True,
                "friend_chat_structured_probe_relaxed_response_format": True,
            },
        )
    )
    normalized_repair = coerce_friend_chat_structured_probe_response(
        repair_response,
        probe_kind=probe_kind,
    )
    repair_repair_feedback = (
        build_friend_chat_probe_repair_feedback(
            dict(normalized_repair.diagnostics or {}),
            probe_plan,
        )
        if normalized_repair is not None
        else primary_repair_feedback
    )
    if normalized_repair is not None:
        if repair_repair_feedback is None:
            logger.info(
                "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
                probe_kind,
                "relaxed_json",
            )
            return LLMResponse(
                model=normalized_repair.model,
                output_text=normalized_repair.output_text,
                tool_calls=normalized_repair.tool_calls,
                usage=normalized_repair.usage,
                latency_ms=int(primary_response.latency_ms or 0)
                + int(normalized_repair.latency_ms or 0),
                diagnostics={
                    **dict(normalized_repair.diagnostics or {}),
                    "structured_probe_repaired": True,
                    "structured_probe_relaxed_response_format": True,
                },
            )
        logger.info(
            "friend_chat_structured_probe_regrounding_attempted "
            "probe_kind=%s stage=%s reasons=%s",
            probe_kind,
            "relaxed_json",
            ",".join(repair_repair_feedback.get("reason_codes") or []),
        )

    runtime_card = build_friend_chat_probe_runtime_card(
        probe_plan=probe_plan,
        repair_feedback=repair_repair_feedback or primary_repair_feedback,
    )
    compact_probe_messages = build_friend_chat_compact_probe_messages(
        runtime_card=runtime_card,
        user_prompt=build_friend_chat_probe_user_prompt(
            user_message=user_message,
            probe_plan=probe_plan,
        ),
        turn_input=None,
    )
    logger.info("friend_chat_structured_probe_compact_repair_attempted probe_kind=%s", probe_kind)
    compact_response = await llm_client.complete(
        LLMRequest(
            messages=compact_probe_messages,
            model=llm_model,
            temperature=0.0,
            max_tokens=260,
            metadata={
                **llm_metadata,
                "benchmark_role": "probe",
                "friend_chat_probe_answer_plan": probe_plan,
                "friend_chat_structured_probe_compact_repair": True,
            },
        )
    )
    if compact_response.failure is None and str(compact_response.output_text or "").strip():
        logger.info(
            "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
            probe_kind,
            "compact_text",
        )
        return LLMResponse(
            model=compact_response.model,
            output_text=compact_response.output_text,
            tool_calls=compact_response.tool_calls,
            usage=compact_response.usage,
            latency_ms=int(primary_response.latency_ms or 0)
            + int(repair_response.latency_ms or 0)
            + int(compact_response.latency_ms or 0),
            diagnostics={
                **dict(compact_response.diagnostics or {}),
                "structured_probe_repaired": True,
                "structured_probe_compact_repair": True,
            },
        )

    logger.info("friend_chat_structured_probe_plaintext_repair_attempted probe_kind=%s", probe_kind)
    plaintext_repair_response = await llm_client.complete(
        LLMRequest(
            messages=build_friend_chat_plaintext_probe_repair_messages(
                user_message=user_message,
                probe_plan=probe_plan,
                repair_feedback=repair_repair_feedback or primary_repair_feedback,
            ),
            model=llm_model,
            temperature=0.0,
            max_tokens=220,
            metadata={
                **llm_metadata,
                "benchmark_role": "probe",
                "friend_chat_probe_answer_plan": probe_plan,
                "friend_chat_structured_probe_plaintext_repair": True,
            },
        )
    )
    if (
        plaintext_repair_response.failure is None
        and str(plaintext_repair_response.output_text or "").strip()
    ):
        logger.info(
            "friend_chat_structured_probe_render_succeeded probe_kind=%s stage=%s",
            probe_kind,
            "plaintext_repair",
        )
        return LLMResponse(
            model=plaintext_repair_response.model,
            output_text=plaintext_repair_response.output_text,
            tool_calls=plaintext_repair_response.tool_calls,
            usage=plaintext_repair_response.usage,
            latency_ms=int(primary_response.latency_ms or 0)
            + int(repair_response.latency_ms or 0)
            + int(plaintext_repair_response.latency_ms or 0),
            diagnostics={
                **dict(plaintext_repair_response.diagnostics or {}),
                "structured_probe_repaired": True,
                "structured_probe_plaintext_repair": True,
            },
        )

    if repair_response.failure is not None:
        return repair_response
    return primary_response
