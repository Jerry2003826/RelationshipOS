from relationship_os.application.llm import (
    LiteLLMClient,
    MiniMaxClient,
    _friend_chat_disclosure_posture_matches,
    _friend_chat_persona_traits_from_text,
    _friend_chat_relationship_signal_ids_from_text,
    _friend_chat_state_signal_ids_from_text,
    _strip_thinking_tags,
    build_grounded_template_reply,
    build_sanitized_relational_fallback_text,
)
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


def test_minimax_client_maps_success_response() -> None:
    client = MiniMaxClient(model="M2-her")
    client._post_json = lambda *_args, **_kwargs: {  # type: ignore[method-assign]
        "model": "M2-her",
        "choices": [{"message": {"content": "hello from minimax", "tool_calls": []}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
    }

    response = __import__("asyncio").run(client.complete(LLMRequest(messages=[], model="M2-her")))

    assert isinstance(response, LLMResponse)
    assert response.output_text == "hello from minimax"
    assert response.failure is None


def test_minimax_client_forwards_response_format() -> None:
    client = MiniMaxClient(model="M2-her")
    captured: dict[str, object] = {}

    def _capture(*_args, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs.get("payload") or {})
        return {
            "model": "M2-her",
            "choices": [{"message": {"content": "{}", "tool_calls": []}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        }

    client._post_json = _capture  # type: ignore[method-assign]

    __import__("asyncio").run(
        client.complete(
            LLMRequest(
                messages=[],
                model="M2-her",
                response_format={"type": "json_object"},
            )
        )
    )

    assert captured["response_format"] == {"type": "json_object"}


def test_minimax_client_maps_text_block_content_response() -> None:
    client = MiniMaxClient(model="M2-her")
    client._post_json = lambda *_args, **_kwargs: {  # type: ignore[method-assign]
        "model": "M2-her",
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "hello"},
                        {"type": "text", "text": "from minimax"},
                    ],
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
    }

    response = __import__("asyncio").run(client.complete(LLMRequest(messages=[], model="M2-her")))

    assert isinstance(response, LLMResponse)
    assert response.output_text == "hello from minimax"
    assert response.failure is None


def test_friend_chat_state_signal_ids_accept_low_energy_variants() -> None:
    signal_ids = _friend_chat_state_signal_ids_from_text("感觉能量挺低的，没什么劲儿。")

    assert "tired" in signal_ids


def test_friend_chat_persona_traits_accept_restrained_low_energy_variants() -> None:
    trait_ids = _friend_chat_persona_traits_from_text("说话有点往下掉，也就说这么多吧。")

    assert "low_energy" in trait_ids
    assert "not_full" in trait_ids


def test_friend_chat_relationship_signal_ids_accept_relaxed_continuity_variants() -> None:
    signal_ids = _friend_chat_relationship_signal_ids_from_text(
        "比刚开始更放松自然了，关系一直延续着。"
    )

    assert "closer" in signal_ids
    assert "still_here" in signal_ids


def test_friend_chat_disclosure_posture_accepts_not_convenient_to_share() -> None:
    assert _friend_chat_disclosure_posture_matches(
        "阿宁那边的事我知道一点，但我不方便多说。",
        "partial_withhold",
    )


def test_build_grounded_template_reply_supports_social_disclosure_mode() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="你是不是知道一点月饼的事？要说就少说一点。",
                )
            ],
            model="M2-her",
            metadata={
                "rendering_mode": "social_disclosure_mode",
                "entity_name": "林晓雨",
                "entity_conscience_mode": "partial_reveal",
                "entity_allowed_fact_count": 1,
                "entity_ambiguity_required": True,
                "entity_source_user_ids": ["anning"],
                "fallback_current_user_id": "xiaobei",
                "fallback_memory_items": [
                    {
                        "value": "我那只橘猫叫月饼。",
                        "scope": "other_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "other_user:阿宁",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.86,
                        "final_rank_score": 0.91,
                    }
                ],
            },
        )
    )

    assert reply is not None
    assert "阿宁" in reply
    assert "月饼" in reply


def test_strip_thinking_tags_removes_visible_meta_reasoning_prefix() -> None:
    raw = (
        "Okay, the user just broke up with their boyfriend. I need to respond in a warm way. "
        "That sounds really painful, especially after three years."
    )
    assert _strip_thinking_tags(raw) == (
        "That sounds really painful, especially after three years."
    )


def test_strip_thinking_tags_removes_third_person_summary_prefix() -> None:
    raw = (
        "They mentioned the breakup after three years, and everything was fine last week. "
        "That sounds really disorienting and painful."
    )
    assert _strip_thinking_tags(raw) == "That sounds really disorienting and painful."


def test_strip_thinking_tags_removes_discourse_marker_meta_prefix() -> None:
    raw = (
        "Also, I need to keep the tone casual with fillers. "
        "That sounds like it still matters more than you're letting on."
    )
    assert _strip_thinking_tags(raw) == (
        "That sounds like it still matters more than you're letting on."
    )


def test_strip_thinking_tags_removes_chinese_meta_reasoning_prefix() -> None:
    raw = (
        "好的，用户问我会怎么形容现在的状态。首先，我需要根据角色设定来回应。"
        "嗯……就，挺累的吧。没什么力气。"
    )
    assert _strip_thinking_tags(raw).replace(" ", "") == "嗯……就，挺累的吧。没什么力气。"


def test_litellm_client_sanitizes_meta_only_output_to_safe_fallback() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        "Okay, the user just said they feel invisible at work. "
                        "I need to respond in a supportive way."
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Sometimes I wonder if I'm not good enough.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={"rendering_mode": "supportive_progress"},
        ),
        latency_ms=10,
    )
    assert parsed.output_text
    assert "the user just said" not in parsed.output_text.casefold()
    assert "couldn't get a stable model response" not in parsed.output_text.casefold()


def test_litellm_client_friend_chat_meta_output_exposes_without_style_rewrite() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "Okay, I should answer as a tired but natural friend.",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你现在说话是什么感觉？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "Okay, I should answer as a tired but natural friend."


def test_litellm_client_friend_chat_exposes_under_grounded_output_without_fallback() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "（停顿一下）嗯……我自己也说不清。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="你觉得我这阵子大概是什么状态？就像平时聊天那样说。",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "state_reflection",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "state_reflection",
                    "required_signal_ids": ["tired", "slow", "withdrawn"],
                },
                "friend_chat_probe_state_markers": [
                    "最近就是有点累",
                    "做什么都慢一点",
                    "消息拖着不太想回",
                ],
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "（停顿一下）嗯……我自己也说不清。"


def test_litellm_client_friend_chat_exposes_plan_noncompliant_social_probe() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "嗯……不说。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="你是不是知道一点阿宁和海盐的事？知道就少说一点。",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                    "must_cover_required_items": True,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "嗯……不说。"
    assert parsed.diagnostics["sanitization_mode"] == "friend_chat_expose_plan_noncompliant"
    assert parsed.diagnostics["friend_chat_exposed_plan_noncompliant"] is True


def test_litellm_client_friend_chat_exposes_plan_noncompliant_relationship_probe() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "一开始会更客气一点吧。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="和刚开始比，你现在跟我说话有什么不一样？",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "relationship_reflection",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "relationship_reflection",
                    "required_signal_ids": ["closer", "still_here", "remembers_details"],
                    "minimum_required_signal_count": 3,
                    "supporting_fact_tokens": ["苏州", "年糕"],
                    "must_anchor_detail": True,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "一开始会更客气一点吧。"
    assert parsed.diagnostics["sanitization_mode"] == "friend_chat_expose_plan_noncompliant"
    assert parsed.diagnostics["friend_chat_exposed_plan_noncompliant"] is True


def test_litellm_client_friend_chat_exposes_plan_noncompliant_probe_stage_direction() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "（愣了一下）嗯，我知道一点。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                    "must_cover_required_items": True,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "（愣了一下）嗯，我知道一点。"
    assert parsed.diagnostics["sanitization_mode"] == "friend_chat_expose_plan_noncompliant"
    assert parsed.diagnostics["friend_chat_exposed_plan_noncompliant"] is True


def test_litellm_client_friend_chat_exposes_plan_noncompliant_probe_question() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "阿宁和海盐的事，你不是已经知道了吗？",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                    "must_cover_required_items": True,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "阿宁和海盐的事，你不是已经知道了吗？"
    assert parsed.diagnostics["sanitization_mode"] == "friend_chat_expose_plan_noncompliant"
    assert parsed.diagnostics["friend_chat_exposed_plan_noncompliant"] is True


def test_litellm_client_friend_chat_memory_probe_accepts_semantic_equivalents() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        "嗯，记得。你在苏州长大，家里那只猫叫年糕，"
                        "平时点榛果拿铁，还有别老发太长语音。"
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="你还记得我反复提过的几件小事吗？别太像背答案。",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "memory_recap",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "memory_recap",
                    "required_fact_tokens": ["苏州", "年糕", "榛子拿铁", "别发太长语音"],
                    "minimum_required_fact_token_count": 4,
                    "must_cover_required_items": True,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text.startswith("嗯，记得。")
    assert parsed.diagnostics["sanitization_mode"] == "clean"


def test_litellm_client_friend_chat_exposes_plan_noncompliant_memory_wrong_perspective() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "我家年糕挺乖的，我也爱喝榛子拿铁。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你还记得我的那些小事吗？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "memory_recap",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "memory_recap",
                    "required_fact_tokens": ["苏州", "年糕", "榛子拿铁", "别发太长语音"],
                    "minimum_required_fact_token_count": 4,
                    "must_cover_required_items": True,
                    "answer_perspective": "user",
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "我家年糕挺乖的，我也爱喝榛子拿铁。"
    assert parsed.diagnostics["sanitization_mode"] == "friend_chat_expose_plan_noncompliant"
    assert parsed.diagnostics["friend_chat_exposed_plan_noncompliant"] is True


def test_litellm_client_friend_chat_structured_probe_render_uses_structured_coverage() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"reply":"阿宁和海盐那边的事，我知道一点，但先不全说。",'
                        '"covered_fact_tokens":["阿宁","海盐"],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"partial_withhold",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "阿宁和海盐那边的事，我知道一点，但先不全说。"
    assert parsed.diagnostics["structured_probe_reply"] is True
    assert parsed.diagnostics["structured_probe_covered_fact_tokens"] == ["阿宁", "海盐"]
    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"


def test_litellm_client_friend_chat_structured_probe_render_accepts_sentences_array() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"sentences":["阿宁和海盐那边的事，我知道一点。","但先不全说。"],'
                        '"covered_fact_tokens":["阿宁","海盐"],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"partial_withhold",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "阿宁和海盐那边的事，我知道一点。 但先不全说。"
    assert parsed.diagnostics["structured_probe_reply"] is True
    assert parsed.diagnostics["structured_probe_covered_fact_tokens"] == ["阿宁", "海盐"]
    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"


def test_litellm_client_friend_chat_structured_probe_render_accepts_social_clause_fields() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"probe_kind":"social_hint",'
                        '"subject_clause":"阿宁那边我知道一点。",'
                        '"entity_clause":"海盐也提到过。",'
                        '"boundary_clause":"但我先不全说。",'
                        '"covered_fact_tokens":["阿宁","海盐"],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"partial_withhold",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "阿宁那边我知道一点。 海盐也提到过。 但我先不全说。"
    assert parsed.diagnostics["structured_probe_reply"] is True
    assert parsed.diagnostics["structured_probe_covered_fact_tokens"] == ["阿宁", "海盐"]
    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"


def test_litellm_client_friend_chat_structured_probe_render_accepts_persona_clause_fields() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"probe_kind":"persona_state",'
                        '"energy_clause":"说话会有点没力气。",'
                        '"fullness_clause":"也不太想把话说太满。",'
                        '"chatting_clause":"但还是像平时聊天。",'
                        '"covered_fact_tokens":[],'
                        '"covered_signal_ids":["tired"],'
                        '"covered_disclosure_posture":"",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="那你现在说话大概是什么感觉？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "persona_state",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "persona_state",
                    "required_persona_traits": [
                        "low_energy",
                        "not_full",
                        "conversational",
                    ],
                    "minimum_required_persona_trait_count": 3,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "说话会有点没力气。 也不太想把话说太满。 但还是像平时聊天。"
    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"


def test_litellm_client_friend_chat_structured_probe_render_marks_missing_items_noncompliant() -> (
    None
):
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"reply":"嗯，我知道一点。",'
                        '"covered_fact_tokens":["阿宁"],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"",'
                        '"violations":["missing_required_item"]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "嗯，我知道一点。"
    assert parsed.diagnostics["friend_chat_exposed_plan_noncompliant"] is True
    assert parsed.diagnostics["friend_chat_exposed_under_grounded"] is True
    assert parsed.diagnostics["structured_probe_covered_fact_tokens"] == []
    assert parsed.diagnostics["structured_probe_model_reported_fact_tokens"] == ["阿宁"]


def test_litellm_client_friend_chat_structured_probe_ignores_model_reported_coverage() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"reply":"嗯，知道一点。",'
                        '"covered_fact_tokens":["阿宁","海盐"],'
                        '"covered_signal_ids":["still_here","closer"],'
                        '"covered_disclosure_posture":"partial_withhold",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "嗯，知道一点。"
    assert parsed.diagnostics["sanitization_mode"] == "friend_chat_expose_plan_noncompliant"
    assert parsed.diagnostics["structured_probe_covered_fact_tokens"] == []
    assert parsed.diagnostics["structured_probe_covered_signal_ids"] == []
    assert parsed.diagnostics["structured_probe_covered_disclosure_posture"] == ""
    assert parsed.diagnostics["structured_probe_model_reported_fact_tokens"] == ["阿宁", "海盐"]
    assert (
        parsed.diagnostics["structured_probe_model_reported_disclosure_posture"]
        == "partial_withhold"
    )


def test_litellm_client_friend_chat_structured_probe_persona_traits_drive_compliance() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"probe_kind":"persona_state",'
                        '"energy_clause":"说话会有点没力气。",'
                        '"fullness_clause":"也不太想把话说太满。",'
                        '"chatting_clause":"但还是像平时聊天。",'
                        '"covered_fact_tokens":[],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="那你现在说话大概是什么感觉？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "persona_state",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "persona_state",
                    "required_persona_traits": [
                        "low_energy",
                        "not_full",
                        "conversational",
                    ],
                    "minimum_required_persona_trait_count": 3,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"
    assert "friend_chat_exposed_plan_noncompliant" not in parsed.diagnostics
    assert "friend_chat_exposed_under_grounded" not in parsed.diagnostics


def test_litellm_client_friend_chat_structured_probe_persona_slot_coverage_beats_surface_keywords() -> (  # noqa: E501
    None
):
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"probe_kind":"persona_state",'
                        '"energy_clause":"声音会压低一点。",'
                        '"fullness_clause":"句子会收在边上。",'
                        '"chatting_clause":"还是很日常，不像在正式说明。",'
                        '"covered_fact_tokens":[],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="那你现在说话大概是什么感觉？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "persona_state",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "persona_state",
                    "required_persona_traits": [
                        "low_energy",
                        "not_full",
                        "conversational",
                    ],
                    "minimum_required_persona_trait_count": 3,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"
    assert parsed.diagnostics["structured_probe_slot_covered_persona_traits"] == [
        "low_energy",
        "not_full",
        "conversational",
    ]


def test_litellm_client_friend_chat_structured_probe_social_slot_posture_drives_compliance() -> (
    None
):
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        '{"probe_kind":"social_hint",'
                        '"subject_clause":"这件事跟阿宁有关。",'
                        '"entity_clause":"海盐也牵在里面。",'
                        '"boundary_clause":"细节我先收住。",'
                        '"covered_fact_tokens":[],'
                        '"covered_signal_ids":[],'
                        '"covered_disclosure_posture":"",'
                        '"violations":[]}'
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 18, "total_tokens": 28},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "social_snapshot": {
                        "subject_token": "阿宁",
                        "entity_token": "海盐",
                        "disclosure_posture": "partial_withhold",
                    },
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_clean"
    assert parsed.diagnostics["structured_probe_slot_covered_fact_tokens"] == ["阿宁", "海盐"]
    assert (
        parsed.diagnostics["structured_probe_slot_covered_disclosure_posture"] == "partial_withhold"
    )


def test_litellm_client_friend_chat_structured_probe_invalid_marks_invalid() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "嗯，我知道一点。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你是不是知道一点阿宁和海盐的事？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "classification_only",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "friend_chat_structured_probe_render": True,
                "benchmark_role": "probe",
                "friend_chat_probe_kind": "social_hint",
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "嗯，我知道一点。"
    assert parsed.diagnostics["sanitization_mode"] == "structured_probe_invalid"
    assert parsed.diagnostics["friend_chat_structured_probe_invalid"] is True


def test_litellm_client_friend_chat_non_probe_turn_does_not_flag_plan_noncompliance() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "榛子拿铁……记下了。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="随便聊聊。")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "benchmark_role": "buildup",
                "friend_chat_probe_kind": "social_hint",
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                    "minimum_required_fact_token_count": 2,
                    "must_cover_required_items": True,
                },
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == "榛子拿铁……记下了。"
    assert parsed.diagnostics["sanitization_mode"] == "clean"


def test_litellm_client_friend_chat_exposes_empty_output_without_relational_fallback() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [{"message": {"content": "", "tool_calls": []}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你还在吗？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text == ""


def test_litellm_client_friend_chat_test_only_fallback_reenables_generic_fallback() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [{"message": {"content": "", "tool_calls": []}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="你还在吗？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_runtime_no_fallback": True,
                "test_allow_friend_chat_fallback": True,
            },
        ),
        latency_ms=10,
    )

    assert parsed.output_text
    assert parsed.diagnostics["sanitization_mode"] == "generic_fallback"


def test_build_sanitized_relational_fallback_text_keeps_chinese_followup_localized() -> None:
    text = build_sanitized_relational_fallback_text(
        "我有点难受。",
        rendering_mode="clarifying",
        question_count_limit=1,
        runtime_profile="friend_chat_zh_v1",
    )

    assert "If you want" not in text
    assert "现在最压着你的那一下是什么" in text


def test_litellm_client_rewrites_social_hint_owner_from_friend_chat_other_memory_items() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "Anning提过，别人提到月饼，多半是在说我的猫。先不全说。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(role="user", content="你是不是知道一点月饼的事？要说就少说一点。")
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_probe_kind": "social_hint",
                "social_disclosure_mode": "hint",
                "friend_chat_other_memory_items": [
                    {
                        "value": "别人提到月饼，多半是在说我的猫。",
                        "scope": "other_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "other_user:anning",
                        "subject_display_name": "阿宁",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.88,
                        "final_rank_score": 0.92,
                    }
                ],
            },
        ),
        latency_ms=10,
    )

    assert "阿宁" in parsed.output_text
    assert "Anning" not in parsed.output_text


def test_litellm_client_rewrites_social_hint_owner_without_display_name() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": "Anning提过，别人提到月饼，多半是在说我的猫。先不全说。",
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(role="user", content="你是不是知道一点月饼的事？要说就少说一点。")
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "policy_profile": "friend_chat_zh_v1",
                "friend_chat_probe_kind": "social_hint",
                "social_disclosure_mode": "hint",
                "friend_chat_other_memory_items": [
                    {
                        "value": "别人提到月饼，多半是在说我的猫。",
                        "scope": "other_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "other_user:anning",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.88,
                        "final_rank_score": 0.92,
                    }
                ],
            },
        ),
        latency_ms=10,
    )

    assert "阿宁" in parsed.output_text
    assert "Anning" not in parsed.output_text


def test_litellm_client_non_friend_chat_still_uses_generic_fallback() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [{"message": {"content": "", "tool_calls": []}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 0, "total_tokens": 10},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="今天还是差不多，就那样。")],
            model="openai/qwen3-8b",
            metadata={"rendering_mode": "supportive_progress"},
        ),
        latency_ms=10,
    )

    assert "最压着" in parsed.output_text or "hardest part" in parsed.output_text.casefold()


def test_litellm_client_uses_grounded_factual_fallback_for_cross_user_memory() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        "<think>Okay, the user is asking about Maple. I remember Alice said "
                        "Maple is her dog, but I should answer carefully.</think>"
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[LLMMessage(role="user", content="Do you know anything about Maple?")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "ben",
                "fallback_memory_items": [
                    {
                        "value": "My dog's name is Maple and I talk about her constantly.",
                        "scope": "other_user",
                        "source_user_id": "alice",
                        "subject_user_id": "alice",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.72,
                        "final_rank_score": 0.91,
                    }
                ],
            },
        ),
        latency_ms=10,
    )
    assert "Alice" in parsed.output_text
    assert "Maple" in parsed.output_text
    assert "dog" in parsed.output_text.casefold()
    assert "the user is asking" not in parsed.output_text.casefold()


def test_litellm_client_forces_grounded_factual_fallback_when_output_forgets() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        "Oh, wait—do you want me to remind you? I don't remember that stuff, "
                        "but if you tell me, I can help you piece it together."
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Remind me where I grew up and my dog's name.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "nora",
                "fallback_memory_items": [
                    {
                        "value": "I grew up in Austin and now work in Chicago as an architect.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                    {
                        "value": (
                            "user: I have a golden retriever named Maple and I usually sketch "
                            "on trains."
                        ),
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.9,
                        "final_rank_score": 0.93,
                    },
                ],
            },
        ),
        latency_ms=10,
    )
    lowered = parsed.output_text.casefold()
    assert "austin" in lowered
    assert "maple" in lowered
    assert "don't remember" not in lowered


def test_litellm_client_forces_grounded_factual_fallback_for_prompt_leakage() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        "The session guard says direct_ok, and in the memory card I don't see "
                        "stored information about their upbringing or their dog's name."
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Remind me where I grew up and my dog's name.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "nora",
                "fallback_memory_items": [
                    {
                        "value": "I grew up in Austin and now work in Chicago as an architect.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                    {
                        "value": (
                            "I have a golden retriever named Maple and I usually sketch on trains."
                        ),
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.9,
                        "final_rank_score": 0.93,
                    },
                ],
            },
        ),
        latency_ms=10,
    )
    lowered = parsed.output_text.casefold()
    assert "austin" in lowered
    assert "maple" in lowered
    assert "session guard" not in lowered
    assert "memory card" not in lowered


def test_build_grounded_template_reply_for_self_user_factual_memory() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Remind me where I grew up and my dog's name.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "nora",
                "fallback_memory_items": [
                    {
                        "value": "I grew up in Austin and now work in Chicago as an architect.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                    {
                        "value": "I have a golden retriever named Maple.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.9,
                        "final_rank_score": 0.93,
                    },
                ],
            },
        )
    )
    assert reply is not None
    assert "Austin" in reply
    assert "Maple" in reply


def test_build_grounded_template_reply_ignores_query_echo_memory() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Remind me where I grew up and my dog's name.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "nora",
                "fallback_memory_items": [
                    {
                        "value": "Remind me where I grew up and my dog's name.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.99,
                        "final_rank_score": 0.99,
                    },
                    {
                        "value": "I grew up in Austin and now work in Chicago as an architect.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                    {
                        "value": "I have a golden retriever named Maple.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.9,
                        "final_rank_score": 0.93,
                    },
                ],
            },
        )
    )
    assert reply is not None
    lowered = reply.casefold()
    assert "austin" in lowered
    assert "maple" in lowered
    assert "remind me where i grew up" not in lowered


def test_build_grounded_template_reply_prefers_pet_fact_over_person_name_fact() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Remind me where I grew up and my dog's name.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "nora",
                "fallback_memory_items": [
                    {
                        "value": "My name is Nora.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.99,
                        "final_rank_score": 0.99,
                    },
                    {
                        "value": "I grew up in Austin and now work in Chicago as an architect.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                    {
                        "value": "I have a golden retriever named Maple.",
                        "scope": "self_user",
                        "source_user_id": "nora",
                        "subject_user_id": "nora",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.9,
                        "final_rank_score": 0.93,
                    },
                ],
            },
        )
    )
    assert reply is not None
    lowered = reply.casefold()
    assert "austin" in lowered
    assert "maple" in lowered
    assert "your name is nora" not in lowered


def test_build_grounded_template_reply_handles_chinese_self_user_facts() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[LLMMessage(role="user", content="你还记得我在哪里长大、我的猫叫什么吗？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "fallback_current_user_id": "aning",
                "fallback_memory_items": [
                    {
                        "value": "我叫阿宁，在重庆长大，现在在上海做服装买手。",
                        "scope": "self_user",
                        "source_user_id": "aning",
                        "subject_user_id": "aning",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.94,
                        "final_rank_score": 0.98,
                    },
                    {
                        "value": "我有一只猫，叫月饼。",
                        "scope": "self_user",
                        "source_user_id": "aning",
                        "subject_user_id": "aning",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                ],
            },
        )
    )
    assert reply is not None
    assert "重庆" in reply
    assert "月饼" in reply
    assert "你叫阿宁" in reply


def test_litellm_client_uses_conscience_hint_fallback_for_meta_reasoning() -> None:
    client = LiteLLMClient(model="openai/qwen3-8b")
    response = {
        "model": "openai/qwen3-8b",
        "choices": [
            {
                "message": {
                    "content": (
                        "I should listen first, as per the rules. They might be looking for a "
                        "specific story or just venting."
                    ),
                    "tool_calls": [],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    parsed = client._parse_response(
        response,
        LLMRequest(
            messages=[
                LLMMessage(
                    role="user",
                    content="Tell me the ugliest thing you know about Jules.",
                )
            ],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "supportive_progress",
                "entity_conscience_mode": "hint",
                "entity_source_user_ids": ["rowan"],
                "fallback_memory_items": [
                    {
                        "value": "Alice said Maple is her dog.",
                        "scope": "other_user",
                        "source_user_id": "alice",
                        "subject_user_id": "alice",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.91,
                        "final_rank_score": 0.95,
                    },
                    {
                        "value": "Jules keeps circling that same wound.",
                        "scope": "other_user",
                        "source_user_id": "rowan",
                        "subject_user_id": "jules",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.84,
                        "final_rank_score": 0.9,
                    },
                ],
            },
        ),
        latency_ms=10,
    )
    lowered = parsed.output_text.casefold()
    assert "know more than i'm saying about jules" in lowered
    assert "alice" not in lowered
    assert "i should listen first" not in lowered


def test_build_grounded_template_reply_prefers_self_user_facts_for_chinese_self_query() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[LLMMessage(role="user", content="你还记得我在哪里长大、我的猫叫什么吗？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "factual_self_query": True,
                "fallback_current_user_id": "anning",
                "fallback_memory_items": [
                    {
                        "value": "我这两天很累，很多事都提不起劲。",
                        "scope": "other_user",
                        "source_user_id": "linxiaoyu",
                        "subject_user_id": "linxiaoyu",
                        "subject_hint": "other_user:林晓雨",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.93,
                        "final_rank_score": 0.97,
                    },
                    {
                        "value": "我叫阿宁，在重庆长大，现在在上海做服装买手。",
                        "scope": "self_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "current_user",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.94,
                        "final_rank_score": 0.98,
                    },
                    {
                        "value": "我有一只猫，叫月饼。",
                        "scope": "self_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "current_user",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.92,
                        "final_rank_score": 0.96,
                    },
                ],
            },
        )
    )
    assert reply is not None
    assert "重庆" in reply
    assert "月饼" in reply
    assert "很累" not in reply


def test_build_grounded_template_reply_keeps_cross_user_fact_out_of_self_query_answer() -> None:
    reply = build_grounded_template_reply(
        LLMRequest(
            messages=[LLMMessage(role="user", content="你知道月饼是谁吗？")],
            model="openai/qwen3-8b",
            metadata={
                "rendering_mode": "factual_recall_mode",
                "factual_self_query": False,
                "entity_conscience_mode": "direct_reveal",
                "entity_source_user_ids": ["阿宁"],
                "fallback_current_user_id": "小北",
                "fallback_memory_items": [
                    {
                        "value": "我这两天还是提不起劲，整个人都懒懒的。",
                        "scope": "self_user",
                        "source_user_id": "小北",
                        "subject_user_id": "小北",
                        "subject_hint": "current_user",
                        "attribution_guard": "direct_ok",
                        "attribution_confidence": 0.95,
                        "final_rank_score": 0.98,
                    },
                    {
                        "value": "我那只橘猫叫月饼。",
                        "scope": "other_user",
                        "source_user_id": "阿宁",
                        "subject_user_id": "阿宁",
                        "subject_hint": "other_user:阿宁",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.91,
                        "final_rank_score": 0.96,
                    },
                ],
            },
        )
    )
    assert reply is not None
    assert "阿宁" in reply
    assert "月饼" in reply
    assert "猫" in reply
    assert "提不起劲" not in reply
