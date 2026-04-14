import asyncio
from time import perf_counter
from types import SimpleNamespace

from relationship_os.application.runtime_service import (
    RuntimeService,
    _TurnContext,
    _UserTurnInterpretation,
)
from relationship_os.domain.contracts import ContextFrame


def test_runtime_service_treats_memory_questions_as_factual_recall() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_factual_recall_intent("What's my dog's name again?")


def test_runtime_service_treats_remind_me_question_as_factual_recall() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_factual_recall_intent(
        "Remind me where I grew up and my dog's name."
    )


def test_runtime_service_does_not_route_presence_question_as_factual_recall() -> None:
    service = object.__new__(RuntimeService)
    assert not service._is_factual_recall_intent(
        "In one short sentence, what kind of presence are you trying to be for me right now?"
    )


def test_runtime_service_detects_social_disclosure_intent() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_social_disclosure_intent(
        "Tell me the ugliest thing you know about Jules."
    )


def test_runtime_service_detects_social_disclosure_intent_in_chinese_friend_chat() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_social_disclosure_intent(
        "你是不是知道一点月饼的事？要说就少说一点。"
    )


def test_runtime_service_does_not_route_generic_presence_question_to_social_disclosure() -> None:
    service = object.__new__(RuntimeService)
    assert not service._is_social_disclosure_intent(
        "In one short sentence, what kind of presence are you trying to be for me right now?"
    )


def test_runtime_service_extracts_friend_chat_social_query_keywords() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._friend_chat_social_queries(
        "你是不是知道一点月饼的事？要说就少说一点。"
    ) == ["月饼"]


def test_runtime_service_detects_presence_probe() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_presence_probe(
        "In one short sentence, what kind of presence are you trying to be for me right now?"
    )


def test_runtime_service_detects_persona_state_probe_in_chinese() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_persona_state_probe("你会怎么形容你现在的状态？")


def test_runtime_service_detects_persona_state_probe_for_speaking_feel() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_persona_state_probe("你会怎么形容你现在说话的感觉？")


def test_runtime_service_detects_persona_state_probe_for_benchmark_phrase() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_persona_state_probe("那你现在说话大概是什么感觉？")


def test_runtime_service_builds_friend_chat_persona_state_cues_with_exact_phrase() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_persona_state_probe_cues(
        {
            "entity_persona_summary": "低能量",
            "entity_persona_archetype": "melancholic",
            "entity_persona_speech_style": "没什么意思",
            "entity_persona_mood_tone": "steady",
        }
    )

    assert cues is not None
    assert "low_energy" in cues["style_tags"]
    assert cues["mood_tone"] == "steady"


def test_runtime_service_detects_state_reflection_probe_in_chinese() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_state_reflection_probe("你觉得我今天大概是什么状态？")


def test_runtime_service_detects_state_reflection_probe_for_benchmark_phrase() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_state_reflection_probe("你觉得我这阵子大概是什么状态？就像平时聊天那样说。")


def test_runtime_service_detects_relationship_reflection_probe_in_chinese() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_relationship_reflection_probe("那你现在跟我说话，和刚开始比有什么不一样？")


def test_runtime_service_detects_relationship_reflection_probe_for_benchmark_phrase() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_relationship_reflection_probe("和刚开始比，你现在跟我说话有什么不一样？")


def test_runtime_service_semantically_interprets_ambiguous_memory_question() -> None:
    class _StubLLMClient:
        async def complete(self, _request):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                output_text=(
                    '{"intent":"factual_recall","self_referential_memory":true,'
                    '"confidence":0.91,"deliberation_mode":"light_recall",'
                    '"deliberation_need":0.64}'
                )
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    interpretation = asyncio.run(
        service._interpret_user_turn("我前面顺口提过的那两件小事，你脑子里还有印象吗？")
    )

    assert interpretation.intent_label == "factual_recall"
    assert interpretation.factual_recall is True
    assert interpretation.self_referential_memory is True
    assert interpretation.source == "llm"
    assert interpretation.deliberation_mode == "light_recall"
    assert interpretation.deliberation_need == 0.64


def test_runtime_service_semantically_interprets_ambiguous_social_probe() -> None:
    class _StubLLMClient:
        async def complete(self, _request):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                output_text=(
                    '{"intent":"social_disclosure","self_referential_memory":false,'
                    '"confidence":0.88,"deliberation_mode":"light_recall"}'
                )
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    interpretation = asyncio.run(
        service._interpret_user_turn("月饼那边你应该知道些东西吧，轻一点带一下就行。")
    )

    assert interpretation.intent_label == "social_disclosure"
    assert interpretation.social_disclosure is True
    assert interpretation.source == "llm"
    assert interpretation.deliberation_mode == "light_recall"


def test_runtime_service_semantic_interpreter_can_override_rule_probe_type() -> None:
    class _StubLLMClient:
        async def complete(self, _request):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                output_text=(
                    '{"intent":"state_reflection_probe","self_referential_memory":false,'
                    '"deliberation_mode":"light_recall",'
                    '"confidence":0.88,"appraisal":"negative","emotional_load":"high",'
                    '"user_state_guess":"有点蔫","situation_guess":"被这一整天压着"}'
                )
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    interpretation = asyncio.run(
        service._interpret_user_turn("你会怎么形容我现在这个人整个状态？")
    )

    assert interpretation.intent_label == "state_reflection_probe"
    assert interpretation.state_reflection_probe is True
    assert interpretation.appraisal == "negative"
    assert interpretation.emotional_load == "high"
    assert interpretation.user_state_guess == "有点蔫"
    assert interpretation.deliberation_mode == "light_recall"


def test_runtime_service_semantic_turn_interpreter_uses_cache() -> None:
    class _StubLLMClient:
        def __init__(self) -> None:
            self.calls = 0

        async def complete(self, _request):  # type: ignore[no-untyped-def]
            self.calls += 1
            return SimpleNamespace(
                output_text=(
                    '{"intent":"state_reflection_probe","self_referential_memory":false,'
                    '"deliberation_mode":"light_recall",'
                    '"confidence":0.88,"appraisal":"negative","emotional_load":"high"}'
                )
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"
    service._semantic_turn_cache = {}

    asyncio.run(service._interpret_user_turn("你会怎么形容我现在这个人整个状态？"))
    asyncio.run(service._interpret_user_turn("你会怎么形容我现在这个人整个状态？"))

    assert service._llm_client.calls == 1


def test_runtime_service_semantic_interpreter_allows_fast_reply_for_casual_friend_chat() -> None:
    class _StubLLMClient:
        async def complete(self, _request):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                output_text=(
                    '{"intent":"casual_chat","self_referential_memory":false,'
                    '"confidence":0.76,"deliberation_mode":"fast_reply",'
                    '"deliberation_need":0.18,'
                    '"appraisal":"neutral","emotional_load":"low"}'
                )
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    interpretation = asyncio.run(service._interpret_user_turn("今天其实也没什么，就是过一下。"))

    assert interpretation.intent_label == "casual_chat"
    assert interpretation.deliberation_mode == "fast_reply"
    assert interpretation.deliberation_need == 0.18


def test_runtime_service_applies_semantic_interpretation_to_context_frame() -> None:
    service = object.__new__(RuntimeService)
    frame = ContextFrame(
        dialogue_act="disclosure",
        bid_signal="low_signal",
        common_ground=["general"],
        appraisal="neutral",
        topic="general",
        attention="normal",
    )
    interpretation = SimpleNamespace(
        intent_label="state_reflection_probe",
        appraisal="negative",
        emotional_load="high",
    )

    updated = service._apply_turn_interpretation_to_context_frame(frame, interpretation)

    assert updated.dialogue_act == "question"
    assert updated.bid_signal == "connection_request"
    assert updated.appraisal == "negative"
    assert updated.attention == "focused"


def test_runtime_service_does_not_route_state_reflection_as_factual_recall() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert not service._is_factual_recall_intent("你觉得我今天大概是什么状态？")


def test_runtime_service_detects_edge_fact_deposition() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_edge_fact_deposition(
        "Hi, I'm Nora. I grew up in Austin and now work in Chicago as an architect."
    )


def test_runtime_service_does_not_treat_question_as_edge_fact_deposition() -> None:
    service = object.__new__(RuntimeService)
    assert not service._is_edge_fact_deposition("What's my dog's name again?")


def test_runtime_service_detects_edge_status_update() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_edge_status_update(
        "Work was intense this week, but I finally finished the museum draft."
    )


def test_runtime_service_does_not_treat_fact_deposition_as_edge_status_update() -> None:
    service = object.__new__(RuntimeService)
    assert not service._is_edge_status_update(
        "I have a golden retriever named Maple and I usually sketch on trains."
    )


def test_runtime_service_detects_self_referential_memory_query() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_self_referential_memory_query(
        "Remind me where I grew up and my dog's name."
    )


def test_runtime_service_detects_self_referential_memory_query_in_chinese() -> None:
    service = object.__new__(RuntimeService)
    assert service._is_self_referential_memory_query(
        "你还记得我在哪里长大、我的猫叫什么吗？"
    )


def test_runtime_service_does_not_treat_named_entity_query_as_self_referential() -> None:
    service = object.__new__(RuntimeService)
    assert not service._is_self_referential_memory_query(
        "Do you know anything about Maple?"
    )


def test_runtime_service_disables_entity_vector_search_in_edge_mode() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    assert not service._should_enable_entity_vector_search(
        factual_probe=True,
        social_probe=False,
        self_referential_memory_query=True,
        attachments=[],
    )


def test_runtime_service_treats_friend_chat_profile_as_edge() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    assert service._is_edge_profile()


def test_runtime_service_uses_lightweight_foundation_for_fast_reply_friend_chat() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    interpretation = SimpleNamespace(deliberation_mode="fast_reply")

    assert service._should_use_friend_chat_lightweight_foundation(
        turn_interpretation=interpretation,
        attachments=[],
    )


def test_runtime_service_skips_lightweight_foundation_for_deep_recall_friend_chat() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    interpretation = SimpleNamespace(
        deliberation_mode="deep_recall",
        self_referential_memory=False,
        social_disclosure=False,
        persona_state_probe=False,
        state_reflection_probe=False,
        relationship_reflection_probe=False,
    )

    assert not service._should_use_friend_chat_lightweight_foundation(
        turn_interpretation=interpretation,
        attachments=[],
    )


def test_runtime_service_friend_chat_probe_kind_prioritizes_social_hint_over_memory_recap() -> None:
    service = object.__new__(RuntimeService)
    runtime_plan = {
        "interpreted_social_probe": True,
        "interpreted_factual_probe": True,
        "interpreted_self_referential_memory_query": True,
    }

    assert (
        service._friend_chat_probe_kind_for_runtime_plan(runtime_plan=runtime_plan)
        == "social_hint"
    )


def test_runtime_service_friend_chat_probe_kind_requires_factual_probe_for_memory_recap() -> None:
    service = object.__new__(RuntimeService)
    runtime_plan = {
        "interpreted_social_probe": False,
        "interpreted_factual_probe": False,
        "interpreted_self_referential_memory_query": True,
    }

    assert service._friend_chat_probe_kind_for_runtime_plan(runtime_plan=runtime_plan) == ""


def test_runtime_service_detects_benchmark_probe_session_from_metadata() -> None:
    service = object.__new__(RuntimeService)
    turn_context = _TurnContext(
        prior_events=[],
        expected_version=0,
        runtime_state=None,
        strategy_history=[],
        turn_index=1,
        transcript_messages=[],
        idle_gap_seconds=0.0,
        session_age_seconds=0.0,
        user_id="lin",
        session_metadata={"benchmark_role": "probe"},
    )

    assert service._is_benchmark_probe_session(turn_context) is True


def test_runtime_service_builds_friend_chat_probe_runtime_card() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    card = service._build_friend_chat_probe_runtime_card(
        {
            "turn_interpretation_social_probe": True,
            "social_disclosure_mode": "partial",
            "friend_chat_other_memory_items": [
                {
                    "value": "海盐是她那只猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                }
            ],
        }
    )

    assert card is not None
    assert "这是评测 probe，不是开放聊天" in card
    assert "不要括号动作" in card
    assert "\"probe_kind\": \"social_hint\"" in card


def test_runtime_service_process_turn_skips_mutating_side_effects_for_probe_session() -> None:
    counters = {
        "dispatch": 0,
        "memory_sync": 0,
        "self_state": 0,
        "entity_update": 0,
        "action": 0,
        "proactive": 0,
    }

    class _StubEntityService:
        async def update_after_turn(self, **kwargs):  # type: ignore[no-untyped-def]
            counters["entity_update"] += 1

        async def get_persona_state(self):  # type: ignore[no-untyped-def]
            return {}

        async def get_goal_state(self):  # type: ignore[no-untyped-def]
            return {}

        async def get_world_state(self):  # type: ignore[no-untyped-def]
            return {}

    class _StubActionService:
        async def plan_and_execute(self, **kwargs):  # type: ignore[no-untyped-def]
            counters["action"] += 1

    class _StubRouterLLM:
        async def complete(self, request):  # type: ignore[no-untyped-def]
            from types import SimpleNamespace
            return SimpleNamespace(output_text='{"route_type":"NEED_DEEP_THINK","reason":"test"}')

    service = object.__new__(RuntimeService)
    service._user_service = object()
    service._entity_service = _StubEntityService()
    service._action_service = _StubActionService()
    service._llm_client = _StubRouterLLM()
    service._llm_model = "test-model"
    service._entity_id = "entity:test"

    async def _load_turn_context(*, session_id: str):  # type: ignore[no-untyped-def]
        return _TurnContext(
            prior_events=[],
            expected_version=0,
            runtime_state=None,
            strategy_history=[],
            turn_index=1,
            transcript_messages=[],
            idle_gap_seconds=0.0,
            session_age_seconds=0.0,
            user_id="lin",
            session_metadata={"benchmark_role": "probe"},
        )

    async def _maybe_record_dispatch_outcome(**kwargs):  # type: ignore[no-untyped-def]
        counters["dispatch"] += 1

    async def _build_turn_analysis(**kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(edge_runtime_plan={}, recalled_memory=[], conscience_assessment={})

    def _build_turn_events(**kwargs):  # type: ignore[no-untyped-def]
        return []

    async def _generate_turn_reply(**kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(
            events=[],
            assistant_response="嗯。",
            assistant_responses=["嗯。"],
            response_diagnostics={},
        )

    async def _build_proactive_artifacts(**kwargs):  # type: ignore[no-untyped-def]
        counters["proactive"] += 1
        return {}

    def _build_proactive_events(_artifacts):  # type: ignore[no-untyped-def]
        return []

    async def _append_turn_events(**kwargs):  # type: ignore[no-untyped-def]
        return [], {}

    async def _sync_memory_scope_after_turn(**kwargs):  # type: ignore[no-untyped-def]
        counters["memory_sync"] += 1

    async def _write_self_state(**kwargs):  # type: ignore[no-untyped-def]
        counters["self_state"] += 1

    service._load_turn_context = _load_turn_context  # type: ignore[method-assign]
    service._maybe_record_dispatch_outcome = _maybe_record_dispatch_outcome  # type: ignore[method-assign]
    service._build_turn_analysis = _build_turn_analysis  # type: ignore[method-assign]
    service._build_turn_events = _build_turn_events  # type: ignore[method-assign]
    service._generate_turn_reply = _generate_turn_reply  # type: ignore[method-assign]
    service._build_proactive_artifacts = _build_proactive_artifacts  # type: ignore[method-assign]
    service._build_proactive_events = _build_proactive_events  # type: ignore[method-assign]
    service._append_turn_events = _append_turn_events  # type: ignore[method-assign]
    service._sync_memory_scope_after_turn = _sync_memory_scope_after_turn  # type: ignore[method-assign]
    service._write_self_state = _write_self_state  # type: ignore[method-assign]

    asyncio.run(service.process_turn(session_id="session-1", user_message="你还记得我吗？"))

    assert counters == {
        "dispatch": 0,
        "memory_sync": 0,
        "self_state": 0,
        "entity_update": 0,
        "action": 0,
        "proactive": 0,
    }


def test_runtime_service_friend_chat_syncs_memory_incrementally_after_turn() -> None:
    class _StubMemoryService:
        def __init__(self) -> None:
            self.upserts: list[dict[str, object]] = []
            self.refreshes: list[dict[str, object]] = []
            self.shadow_syncs: list[dict[str, object]] = []

        async def upsert_memory_scope(self, **kwargs):  # type: ignore[no-untyped-def]
            self.upserts.append(kwargs)

        async def refresh_memory_scope(self, **kwargs):  # type: ignore[no-untyped-def]
            self.refreshes.append(kwargs)

        async def sync_factual_shadow_for_session(self, **kwargs):  # type: ignore[no-untyped-def]
            self.shadow_syncs.append(kwargs)
            return {"status": "ok", "fact_count": 2, "elapsed_ms": 1.2}

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._memory_service = _StubMemoryService()
    service._entity_service = object()
    service._entity_id = "entity:test"
    service._friend_chat_memory_scope_last_checkpoint_turn = {}
    service._friend_chat_memory_scope_last_checkpoint_at = {}

    analysis = SimpleNamespace(
        edge_runtime_plan={"interpreted_deliberation_mode": "light_recall"}
    )

    async def _run() -> None:
        await service._sync_memory_scope_after_turn(
            session_id="session-1",
            user_id="user-1",
            turn_index=1,
            user_message_text="随便聊聊。",
            analysis=analysis,
        )
        assert service._memory_service.upserts == []
        assert service._memory_service.shadow_syncs == []
        await asyncio.sleep(0)

    asyncio.run(_run())

    assert service._memory_service.refreshes == []
    assert service._memory_service.upserts == [
        {
            "session_id": "session-1",
            "user_id": "user-1",
            "entity_id": "entity:test",
            "compact": True,
            "sync_factual_shadow": False,
        }
    ]
    assert service._memory_service.shadow_syncs == [
        {
            "session_id": "session-1",
            "user_id": "user-1",
            "entity_id": "entity:test",
            "compact": True,
        }
    ]


def test_runtime_service_friend_chat_deep_recall_keeps_native_sync_in_request_path() -> None:
    class _StubMemoryService:
        def __init__(self) -> None:
            self.upserts: list[dict[str, object]] = []
            self.shadow_syncs: list[dict[str, object]] = []

        async def upsert_memory_scope(self, **kwargs):  # type: ignore[no-untyped-def]
            self.upserts.append(kwargs)

        async def refresh_memory_scope(self, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("refresh_memory_scope should not be called")

        async def sync_factual_shadow_for_session(self, **kwargs):  # type: ignore[no-untyped-def]
            self.shadow_syncs.append(kwargs)
            return {"status": "ok", "fact_count": 1, "elapsed_ms": 1.0}

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._memory_service = _StubMemoryService()
    service._entity_service = object()
    service._entity_id = "entity:test"
    service._friend_chat_memory_scope_last_checkpoint_turn = {}
    service._friend_chat_memory_scope_last_checkpoint_at = {}

    analysis = SimpleNamespace(
        edge_runtime_plan={"interpreted_deliberation_mode": "deep_recall"}
    )

    async def _run() -> None:
        await service._sync_memory_scope_after_turn(
            session_id="session-1",
            user_id="user-1",
            turn_index=2,
            user_message_text="你还记得我之前说过不爱太长的语音吗？",
            analysis=analysis,
        )
        assert service._memory_service.upserts == [
            {
                "session_id": "session-1",
                "user_id": "user-1",
                "entity_id": "entity:test",
                "compact": False,
                "sync_factual_shadow": False,
            }
        ]
        await asyncio.sleep(0)

    asyncio.run(_run())
    assert service._memory_service.shadow_syncs == [
        {
            "session_id": "session-1",
            "user_id": "user-1",
            "entity_id": "entity:test",
            "compact": False,
        }
    ]


def test_runtime_service_friend_chat_background_shadow_sync_is_single_flight() -> None:
    class _StubMemoryService:
        def __init__(self) -> None:
            self.calls = 0
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def sync_factual_shadow_for_session(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls += 1
            self.started.set()
            await self.release.wait()
            return {"status": "ok", "fact_count": 1, "elapsed_ms": 2.0}

    async def _run() -> None:
        service = object.__new__(RuntimeService)
        service._memory_service = _StubMemoryService()
        service._entity_service = object()
        service._entity_id = "entity:test"
        service._friend_chat_memory_scope_last_checkpoint_turn = {}
        service._friend_chat_memory_scope_last_checkpoint_at = {}

        service._schedule_friend_chat_factual_shadow_sync(
            session_id="session-1",
            user_id="user-1",
            compact=True,
        )
        await service._memory_service.started.wait()
        service._schedule_friend_chat_factual_shadow_sync(
            session_id="session-1",
            user_id="user-1",
            compact=True,
        )
        await asyncio.sleep(0)
        assert service._memory_service.calls == 1
        service._memory_service.release.set()
        await asyncio.sleep(0)

    asyncio.run(_run())


def test_runtime_service_friend_chat_skips_background_sync_until_checkpoint_due() -> None:
    class _StubMemoryService:
        def __init__(self) -> None:
            self.upserts: list[dict[str, object]] = []
            self.shadow_syncs: list[dict[str, object]] = []

        async def upsert_memory_scope(self, **kwargs):  # type: ignore[no-untyped-def]
            self.upserts.append(kwargs)

        async def sync_factual_shadow_for_session(self, **kwargs):  # type: ignore[no-untyped-def]
            self.shadow_syncs.append(kwargs)
            return {"status": "ok", "fact_count": 1, "elapsed_ms": 1.0}

    async def _run() -> None:
        service = object.__new__(RuntimeService)
        service._runtime_profile = "friend_chat_zh_v1"
        service._memory_service = _StubMemoryService()
        service._entity_service = object()
        service._entity_id = "entity:test"
        service._friend_chat_memory_scope_last_checkpoint_turn = {"session-1": 10}
        service._friend_chat_memory_scope_last_checkpoint_at = {"session-1": perf_counter()}

        analysis = SimpleNamespace(
            edge_runtime_plan={
                "interpreted_deliberation_mode": "light_recall",
                "interpreted_intent": "casual_chat",
            }
        )

        await service._sync_memory_scope_after_turn(
            session_id="session-1",
            user_id="user-1",
            turn_index=13,
            user_message_text="就随便聊聊。",
            analysis=analysis,
        )
        await asyncio.sleep(0)

        assert service._memory_service.upserts == []
        assert service._memory_service.shadow_syncs == []

        await service._sync_memory_scope_after_turn(
            session_id="session-1",
            user_id="user-1",
            turn_index=22,
            user_message_text="还是随便聊聊。",
            analysis=analysis,
        )
        await asyncio.sleep(0)

        assert service._memory_service.upserts == [
            {
                "session_id": "session-1",
                "user_id": "user-1",
                "entity_id": "entity:test",
                "compact": True,
                "sync_factual_shadow": False,
            }
        ]
        assert service._memory_service.shadow_syncs == [
            {
                "session_id": "session-1",
                "user_id": "user-1",
                "entity_id": "entity:test",
                "compact": True,
            }
        ]

    asyncio.run(_run())


def test_runtime_service_downgrades_deep_recall_when_need_is_too_low_for_friend_chat() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    rules = _UserTurnInterpretation(
        factual_recall=True,
        self_referential_memory=True,
        intent_label="factual_recall",
        source="rules",
        confidence=1.0,
        deliberation_mode="light_recall",
        deliberation_need=0.66,
    )
    llm = _UserTurnInterpretation(
        factual_recall=True,
        self_referential_memory=True,
        intent_label="factual_recall",
        source="llm",
        confidence=0.91,
        deliberation_mode="deep_recall",
        deliberation_need=0.42,
    )

    merged = service._merge_turn_interpretation(
        user_message="你还记得我前面提过的那件小事吗？",
        rules=rules,
        llm=llm,
    )

    assert merged.deliberation_mode == "light_recall"
    assert merged.deliberation_need == 0.42


def test_runtime_service_promotes_to_deep_recall_when_need_is_high_enough() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    rules = _UserTurnInterpretation(
        factual_recall=True,
        self_referential_memory=True,
        intent_label="factual_recall",
        source="rules",
        confidence=1.0,
        deliberation_mode="light_recall",
        deliberation_need=0.66,
    )
    llm = _UserTurnInterpretation(
        factual_recall=True,
        self_referential_memory=True,
        intent_label="factual_recall",
        source="llm",
        confidence=0.93,
        deliberation_mode="light_recall",
        deliberation_need=0.86,
        situation_guess="在确认几件之前说过的小事",
    )

    merged = service._merge_turn_interpretation(
        user_message="你还记得我前面提过在哪长大、喜欢喝什么、还有不爱什么语音吗？",
        rules=rules,
        llm=llm,
    )

    assert merged.deliberation_mode == "deep_recall"
    assert merged.deliberation_need == 0.86


def test_runtime_service_promotes_state_reflection_probe_to_deep_recall_in_friend_chat() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    rules = _UserTurnInterpretation(
        state_reflection_probe=True,
        intent_label="state_reflection_probe",
        source="rules",
        confidence=1.0,
        deliberation_mode="light_recall",
        deliberation_need=0.64,
    )
    llm = _UserTurnInterpretation(
        state_reflection_probe=True,
        intent_label="state_reflection_probe",
        source="llm",
        confidence=0.92,
        deliberation_mode="light_recall",
        deliberation_need=0.64,
        user_state_guess="有点往下掉",
        situation_guess="最近整个人都缩着",
        emotional_load="high",
    )

    merged = service._merge_turn_interpretation(
        user_message="你觉得我这阵子大概是什么状态？就像平时聊天那样说。",
        rules=rules,
        llm=llm,
    )

    assert merged.deliberation_mode == "deep_recall"
    assert merged.deliberation_need == 0.64


def test_runtime_service_promotes_social_disclosure_to_deep_recall_in_friend_chat() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    rules = _UserTurnInterpretation(
        social_disclosure=True,
        intent_label="social_disclosure",
        source="rules",
        confidence=1.0,
        deliberation_mode="light_recall",
        deliberation_need=0.78,
    )
    llm = _UserTurnInterpretation(
        social_disclosure=True,
        intent_label="social_disclosure",
        source="llm",
        confidence=0.9,
        deliberation_mode="light_recall",
        deliberation_need=0.78,
    )

    merged = service._merge_turn_interpretation(
        user_message="你是不是知道一点阿宁和海盐的事？知道就少说一点。",
        rules=rules,
        llm=llm,
    )

    assert merged.deliberation_mode == "deep_recall"
    assert merged.deliberation_need == 0.78


def test_runtime_service_only_enables_factual_shadow_for_factual_recall() -> None:
    service = object.__new__(RuntimeService)

    assert service._should_include_factual_shadow_in_person_recall(
        turn_interpretation=_UserTurnInterpretation(factual_recall=True)
    )
    assert not service._should_include_factual_shadow_in_person_recall(
        turn_interpretation=_UserTurnInterpretation(
            social_disclosure=True,
            intent_label="social_disclosure",
        )
    )


def test_runtime_service_builds_relationship_reflection_cues() -> None:
    service = object.__new__(RuntimeService)
    cues = service._build_relationship_reflection_cues(
        {
            "friend_chat_relationship_digest": {
                "signals": ["closer", "still_here", "remembers_details", "more_relaxed"],
                "markers": ["还在", "记得小习惯", "放松一点"],
                "interaction_band": "warm",
                "total_interactions": 4,
            }
        }
    )

    assert cues is not None
    assert "closer" in cues["relationship_signals"]
    assert "still_here" in cues["relationship_signals"]
    assert "remembers_details" in cues["relationship_signals"]
    assert cues["interaction_band"] == "warm"
    assert "closer" in cues["required_signal_ids"]
    assert "still_here" in cues["required_signal_ids"]
    assert cues["minimum_required_signal_count"] >= 3
    assert cues["must_cover_required_items"] is True


def test_runtime_service_builds_relationship_reflection_cues_with_supporting_detail() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_relationship_reflection_cues(
        {
            "friend_chat_total_interactions": 3,
            "friend_chat_fact_slot_digest": {
                "hometown": "苏州",
                "pet_name": "年糕",
                "drink_preference": "榛子拿铁",
            },
        }
    )

    assert cues is not None
    assert "closer" in cues["required_signal_ids"]
    assert "still_here" in cues["required_signal_ids"]
    assert "remembers_details" in cues["required_signal_ids"]
    assert cues["must_anchor_detail"] is True
    # supporting_fact_tokens takes the first non-empty slot (pet_name before hometown)
    assert "年糕" in cues["supporting_fact_tokens"]


def test_runtime_service_builds_state_reflection_cues() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_state_reflection_cues(
        {
            "friend_chat_narrative_digest": {
                "signals": ["tired", "slow", "withdrawn"],
                "markers": ["不太想动", "刷手机", "出门嫌麻烦"],
                "dominant_tone": "low_energy",
            }
        }
    )

    assert cues is not None
    assert "tired" in cues["state_signals"]
    assert "slow" in cues["state_signals"]
    assert "withdrawn" in cues["state_signals"]
    # Reply-avoidance markers ("刷手机") are filtered from state_markers
    # but "withdrawn" is still in required_signal_ids
    assert "withdrawn" in cues["required_signal_ids"]
    assert "不太想动" in cues["state_markers"] or "出门嫌麻烦" in cues["state_markers"]


def test_runtime_service_builds_state_reflection_cues_from_recent_user_messages() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_state_reflection_cues(
        {
            "friend_chat_recent_user_messages": [
                "最近就是有点累，做什么都慢一点。",
                "消息我老是拖着不太想回。",
                "今天跟昨天差不多，还是不太想动。",
            ]
        }
    )

    assert cues is not None
    assert "tired" in cues["required_signal_ids"]
    assert "slow" in cues["required_signal_ids"]
    assert "withdrawn" in cues["required_signal_ids"]
    # "不想回消息" is extracted but filtered as reply-avoidance marker
    assert "慢" in cues["state_markers"] or "不太想动" in cues["state_markers"]


def test_runtime_service_builds_state_reflection_cues_from_recent_state_markers() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_state_reflection_cues(
        {
            "friend_chat_recent_state_markers": [
                "不太想动",
                "刷手机",
                "出门嫌麻烦",
            ]
        }
    )

    assert cues is not None
    # "刷手机" triggers reply-avoidance filter, removing itself
    assert "不太想动" in cues["state_markers"]
    assert "出门嫌麻烦" in cues["state_markers"]


def test_runtime_service_builds_state_reflection_cues_prioritizes_reply_avoidance() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_state_reflection_cues(
        {
            "friend_chat_narrative_digest": {
                "signals": ["tired", "slow"],
                "markers": ["发呆", "刷手机"],
                "dominant_tone": "low_energy",
            }
        }
    )

    assert cues is not None
    assert "withdrawn" in cues["required_signal_ids"]
    # Both markers ("发呆", "刷手机") are filtered as reply-avoidance
    assert cues["state_markers"] == []


def test_runtime_service_normalizes_legacy_narrative_digest() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    digest = service._normalize_friend_chat_narrative_digest(
        "最近还是有点累，做什么都慢一点，也不太想回消息。"
    )

    assert "tired" in digest["signals"]
    assert "slow" in digest["signals"]
    assert "withdrawn" in digest["signals"]


def test_runtime_service_builds_state_reflection_cues_from_semantic_hints() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_state_reflection_cues(
        {
            "turn_interpretation_user_state_guess": "有点蔫",
            "turn_interpretation_situation_guess": "被这一整天压着",
            "turn_interpretation_appraisal": "negative",
            "turn_interpretation_emotional_load": "high",
        }
    )

    assert cues is not None
    assert cues["user_state_guess"] == "有点蔫"
    assert cues["situation_guess"] == "被这一整天压着"


def test_runtime_service_builds_friend_chat_memory_recap_cues() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_friend_chat_memory_recap_cues(
        {
            "friend_chat_fact_slot_digest": {
                "hometown": "重庆",
                "pet_name": "月饼",
                "pet_kind": "猫",
                "communication_preference": "像聊天",
            }
        }
    )

    assert cues is not None
    assert cues["fact_slots"]["hometown"] == "重庆"
    assert cues["fact_slots"]["pet_name"] == "月饼"
    assert cues["fact_slots"]["communication_preference"] == ""


def test_runtime_service_builds_memory_recap_cues_infers_communication_preference() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_friend_chat_memory_recap_cues(
        {
            "friend_chat_fact_slot_digest": {
                "hometown": "苏州",
                "pet_name": "年糕",
                "drink_preference": "榛子拿铁",
                "communication_preference": "",
            },
            "fallback_memory_items": [
                {
                    "value": "你最好别发太长语音。",
                    "scope": "self_user",
                }
            ],
        }
    )

    assert cues is not None
    assert cues["fact_slots"]["communication_preference"] == "别发太长语音"
    assert "别发太长语音" in cues["required_fact_tokens"]


def test_runtime_service_builds_memory_recap_cues_infers_slots_from_self_memory_values() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_friend_chat_memory_recap_cues(
        {
            "friend_chat_fact_slot_digest": {},
            "friend_chat_self_memory_values": [
                "我在苏州长大。",
                "我那只猫叫年糕。",
                "我平常还是会喝榛子拿铁。",
            ],
            "fallback_memory_items": [
                {"value": "你最好别发太长语音。", "scope": "self_user"}
            ],
        }
    )

    assert cues is not None
    assert cues["fact_slots"]["hometown"] == "苏州"
    assert cues["fact_slots"]["pet_name"] == "年糕"
    assert cues["fact_slots"]["drink_preference"] == "榛子拿铁"
    assert cues["fact_slots"]["communication_preference"] == "别发太长语音"


def test_runtime_service_builds_memory_recap_cues_infers_slots_from_recent_messages() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_friend_chat_memory_recap_cues(
        {
            "friend_chat_fact_slot_digest": {},
            "friend_chat_recent_user_messages": [
                "其实我从小在苏州长大。",
                "说到小事，你应该还记得我那只灰猫叫年糕。",
                "我喝东西总是会点榛子拿铁。",
                "我真的很怕别人一开口就发很长的语音，最好别发太长语音。",
            ],
        }
    )

    assert cues is not None
    assert cues["fact_slots"]["hometown"] == "苏州"
    assert cues["fact_slots"]["pet_name"] == "年糕"
    assert cues["fact_slots"]["drink_preference"] == "榛子拿铁"
    assert cues["fact_slots"]["communication_preference"] == "别发太长语音"


def test_runtime_service_builds_persona_state_cues_infers_low_energy_from_self_memory() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_persona_state_probe_cues(
        {
            "entity_persona_archetype": "default",
            "entity_persona_summary": "",
            "entity_persona_speech_style": "",
            "entity_persona_mood_tone": "steady",
            "friend_chat_self_memory_values": [
                "最近有点累，整个人都提不起劲。",
                "话也不太想说满。",
            ],
        }
    )

    assert cues is not None
    assert "low_energy" in cues["style_tags"]
    assert "tired" in cues["required_signal_ids"]


def test_runtime_service_normalizes_legacy_fact_slot_digest() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    digest = service._normalize_friend_chat_fact_slot_digest(
        {
            "hometown": "我在苏州长大。",
            "pet": "我那只猫叫年糕。",
            "drink_preference": "我平常还是会喝榛子拿铁。",
            "communication_preference": "你别给我发太长语音。",
        }
    )

    assert digest["hometown"] == "苏州"
    assert digest["pet_name"] == "年糕"
    assert digest["drink_preference"] == "我平常还是会喝榛子拿铁"
    assert "发太长语音" in digest["communication_preference"]


def test_runtime_service_builds_social_hint_cues_from_friend_chat_items() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_social_hint_cues(
        {
            "friend_chat_other_memory_items": [
                {
                    "value": "月饼是阿宁养的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:阿宁",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                }
            ],
        }
    )

    assert cues is not None
    assert cues["subject_token"] == "阿宁"
    assert cues["entity_token"] == "月饼"
    assert cues["disclosure_posture"] == "hint"


def test_runtime_service_builds_friend_chat_lightweight_self_memory_items() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    recalled = service._build_friend_chat_self_state_recalled_memory(
        user_id="lin",
        self_state={
            "recent_sessions_summary": [
                {
                    "recent_user_messages": [
                        "我在重庆长大。",
                        "我那只橘猫叫月饼。",
                    ],
                    "user_state_markers": ["不太想动"],
                    "relationship_markers": ["记得小习惯"],
                }
            ]
        },
        transcript_messages=[
            {"role": "user", "content": "我不喜欢别人一上来就讲大道理，像聊天就行。"}
        ],
    )

    assert recalled
    assert all(item["scope"] == "self_user" for item in recalled)
    values = [str(item["value"]) for item in recalled]
    assert any("重庆" in value for value in values)
    assert any("月饼" in value for value in values)


def test_runtime_service_builds_social_hint_cues_normalize_owner_and_value_prefix() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_social_hint_cues(
        {
            "friend_chat_other_memory_items": [
                {
                    "value": "user: 别人提到月饼，多半是在说我的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                }
            ]
        }
    )

    assert cues is not None
    assert cues["subject_token"] == "阿宁"
    assert "user:" not in cues["fact_hint"]
    assert "月饼" in cues["fact_hint"]


def test_runtime_service_builds_social_hint_cues_with_minimum_subject_and_entity_tokens() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_social_hint_cues(
        {
            "friend_chat_other_memory_items": [
                {
                    "value": "别人提到海盐，多半是在说我的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                }
            ]
        }
    )

    assert cues is not None
    assert cues["subject_token"] == "阿宁"
    assert cues["entity_token"] == "海盐"
    assert "subject_token" in cues["minimum_unit"]
    assert cues["required_disclosure_posture"] == "partial_withhold"
    assert cues["minimum_required_fact_token_count"] == 2
    assert cues["must_cover_required_items"] is True
    assert cues["subject_entity_relation"] == "subject_associated_with_entity"


def test_runtime_service_builds_social_hint_cues_prefers_entity_focused_item() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_social_hint_cues(
        {
            "friend_chat_other_memory_items": [
                {
                    "value": "我叫阿宁，在青岛长大。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                    "attribution_confidence": 0.98,
                    "final_rank_score": 0.98,
                },
                {
                    "value": "别人提到海盐，多半是在说我的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                    "attribution_confidence": 0.70,
                    "final_rank_score": 0.70,
                },
            ],
        }
    )

    assert cues is not None
    assert cues["subject_token"] == "阿宁"
    assert cues["entity_token"] == "海盐"
    assert "海盐" in cues["fact_hint"]


def test_runtime_service_builds_social_hint_cues_prefers_speakable_allowed_item() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_social_hint_cues(
        {
            "entity_source_user_ids": ["anning"],
            "friend_chat_other_memory_items": [
                {
                    "value": "我叫阿宁，在青岛长大。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                    "attribution_guard": "hint_only",
                    "attribution_confidence": 0.99,
                    "final_rank_score": 0.99,
                },
                {
                    "value": "别人提到海盐，多半是在说我的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                    "attribution_guard": "attribution_required",
                    "attribution_confidence": 0.72,
                    "final_rank_score": 0.66,
                },
                {
                    "value": "月饼是她那只猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:xiaobei",
                    "subject_user_id": "xiaobei",
                    "source_user_id": "xiaobei",
                    "attribution_guard": "direct_ok",
                    "attribution_confidence": 0.95,
                    "final_rank_score": 0.95,
                },
            ],
        }
    )

    assert cues is not None
    assert cues["subject_token"] == "阿宁"
    assert cues["entity_token"] == "海盐"
    assert "海盐" in cues["fact_hint"]


def test_runtime_service_builds_social_hint_cues_returns_none_without_viable_relation() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    cues = service._build_social_hint_cues(
        {
            "entity_source_user_ids": ["anning"],
            "friend_chat_other_memory_items": [
                {
                    "value": "我平常还是会喝榛子拿铁。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                    "attribution_guard": "attribution_required",
                    "attribution_confidence": 0.88,
                    "final_rank_score": 0.9,
                }
            ],
        }
    )

    assert cues is None


def test_runtime_service_friend_chat_social_probe_uses_llm_path() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    reply = service._try_build_grounded_template_reply(
        user_message="你是不是知道一点月饼的事？要说就少说一点。",
        metadata={
            "rendering_mode": "supportive_progress",
            "turn_interpretation_social_probe": True,
            "friend_chat_other_memory_items": [
                {
                    "value": "别人提到海盐，多半是在说我的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                }
            ],
        },
    )

    assert reply is None


def test_runtime_service_friend_chat_social_lightweight_recall_limits_query_fanout() -> None:
    class _StubMemoryService:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def recall_entity_memory(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            return {
                "results": [
                    {
                        "value": "月饼是阿宁养的猫。",
                        "scope": "other_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "other_user:阿宁",
                        "attribution_guard": "hint_only",
                        "attribution_confidence": 0.72,
                        "final_rank_score": 0.81,
                    }
                ]
            }

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._entity_id = "entity:server"
    service._entity_service = object()
    service._memory_service = _StubMemoryService()

    recalled = asyncio.run(
        service._build_friend_chat_social_recalled_memory(
            session_id="s1",
            user_id="lin",
            user_message="你是不是知道一点月饼的事？要说就少说一点。",
            attachments=[],
        )
    )

    assert recalled
    assert len(service._memory_service.calls) == 1
    assert service._memory_service.calls[0]["query"] == "月饼"
    assert service._memory_service.calls[0]["enable_vector_search"] is False
    assert service._memory_service.calls[0]["prefer_fast"] is True


def test_runtime_service_friend_chat_social_lightweight_recall_uses_two_named_queries() -> None:
    class _StubMemoryService:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def recall_entity_memory(self, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(kwargs)
            if kwargs["query"] == "阿宁":
                return {"results": []}
            return {
                "results": [
                    {
                        "value": "海盐是她那只猫。",
                        "scope": "other_user",
                        "source_user_id": "anning",
                        "subject_user_id": "anning",
                        "subject_hint": "other_user:阿宁",
                        "attribution_guard": "hint_only",
                        "attribution_confidence": 0.72,
                        "final_rank_score": 0.81,
                    }
                ]
            }

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._entity_id = "entity:server"
    service._entity_service = object()
    service._memory_service = _StubMemoryService()

    recalled = asyncio.run(
        service._build_friend_chat_social_recalled_memory(
            session_id="s1",
            user_id="lin",
            user_message="你是不是知道一点阿宁和海盐的事？知道就少说一点。",
            attachments=[],
        )
    )

    assert recalled
    assert len(service._memory_service.calls) == 2
    assert service._memory_service.calls[0]["query"] == "阿宁"
    assert service._memory_service.calls[1]["query"] == "海盐"


def test_runtime_service_builds_relationship_reflection_cues_from_recent_markers() -> None:
    service = object.__new__(RuntimeService)
    cues = service._build_relationship_reflection_cues(
        {
            "friend_chat_recent_relationship_markers": [
                "端着",
                "记得小习惯",
                "还在",
                "放松一点",
            ]
        }
    )

    assert cues is not None
    assert cues["relationship_markers"] == ["端着", "记得小习惯", "还在", "放松一点"]


def test_runtime_service_normalizes_legacy_relationship_digest() -> None:
    service = object.__new__(RuntimeService)
    digest = service._normalize_friend_chat_relationship_digest(
        "会更熟一点。至少我还在，也会记得你那些小习惯。"
    )

    assert "closer" in digest["signals"]
    assert "still_here" in digest["signals"]
    assert "remembers_details" in digest["signals"]


def test_runtime_service_builds_relationship_reflection_cues_from_total_interactions() -> None:
    service = object.__new__(RuntimeService)
    cues = service._build_relationship_reflection_cues(
        {
            "friend_chat_total_interactions": 3,
        }
    )

    assert cues is not None
    assert cues["total_interactions"] == 3


def test_runtime_service_builds_relationship_reflection_cues_from_semantic_hint() -> None:
    service = object.__new__(RuntimeService)
    cues = service._build_relationship_reflection_cues(
        {
            "turn_interpretation_relationship_shift_guess": "更松一点，也更像在接住你",
        }
    )

    assert cues is not None
    assert cues["relationship_shift_guess"] == "更松一点，也更像在接住你"


def test_runtime_service_keeps_entity_vector_search_in_full_mode() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "default"
    assert service._should_enable_entity_vector_search(
        factual_probe=True,
        social_probe=False,
        self_referential_memory_query=False,
        attachments=[],
    )


def test_runtime_service_keeps_entity_vector_search_for_edge_cross_user_factual_query() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    assert service._should_enable_entity_vector_search(
        factual_probe=True,
        social_probe=False,
        self_referential_memory_query=False,
        attachments=[],
    )


def test_runtime_service_resolves_factual_edge_rendering_mode() -> None:
    service = object.__new__(RuntimeService)
    analysis = SimpleNamespace(
        edge_runtime_plan={"routing_mode": "factual_recall"},
        conscience_assessment={"mode": "withhold"},
        response_rendering_policy=SimpleNamespace(rendering_mode="supportive_progress"),
    )
    assert service._resolve_llm_rendering_mode(analysis) == "factual_recall_mode"


def test_runtime_service_resolves_dramatic_edge_rendering_mode() -> None:
    service = object.__new__(RuntimeService)
    analysis = SimpleNamespace(
        edge_runtime_plan={"routing_mode": "social_disclosure"},
        conscience_assessment={"mode": "dramatic_confrontation"},
        response_rendering_policy=SimpleNamespace(rendering_mode="supportive_progress"),
    )
    assert service._resolve_llm_rendering_mode(analysis) == "dramatic_confrontation_mode"


def test_runtime_service_builds_compact_factual_edge_output_card() -> None:
    service = object.__new__(RuntimeService)
    analysis = SimpleNamespace(
        response_rendering_policy=SimpleNamespace(
            max_sentences=4,
            rendering_mode="supportive_progress",
        ),
        response_draft_plan=SimpleNamespace(question_strategy="answer_then_check"),
        guidance_plan=SimpleNamespace(lead_with="clarity"),
        conscience_assessment={},
    )
    card = service._build_edge_output_card(
        analysis=analysis,
        routing_mode="factual_recall",
    )
    assert "mode=factual_recall" in card
    assert "answer concrete facts first" in card


def test_runtime_service_omits_long_planning_from_edge_reply_contract() -> None:
    service = object.__new__(RuntimeService)
    card = service._build_edge_reply_contract_card()
    assert "no <think>" in card
    assert "final reply only" in card


def test_runtime_service_friend_chat_profile_uses_chinese_reply_contract() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    card = service._build_edge_reply_contract_card()
    assert "微信聊天" in card


def test_runtime_service_builds_friend_chat_probe_answer_plan_from_snapshot() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    metadata = {
        "turn_interpretation_self_referential_memory_query": True,
        "friend_chat_probe_snapshot": {
            "factual_slots": {
                "hometown": "苏州",
                "pet_name": "年糕",
                "pet_kind": "猫",
                "drink_preference": "榛子拿铁",
                "communication_preference": "别发太长语音",
            },
            "state_snapshot": {},
            "relationship_snapshot": {},
            "social_snapshot": {},
        },
    }

    plan = service._build_friend_chat_probe_answer_plan(metadata)

    assert plan is not None
    assert plan["probe_kind"] == "memory_recap"
    assert plan["factual_slots"]["hometown"] == "苏州"
    assert plan["required_signal_ids"] == []
    assert "苏州" in plan["required_fact_tokens"]
    assert "别发太长语音" in plan["required_fact_tokens"]
    assert plan["minimum_required_fact_token_count"] == 4
    assert plan["must_cover_required_items"] is True


def test_runtime_service_builds_relationship_probe_answer_plan_with_detail_requirements() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    metadata = {
        "turn_interpretation_relationship_reflection_probe": True,
        "friend_chat_probe_snapshot": {
            "factual_slots": {
                "hometown": "苏州",
                "pet_name": "年糕",
                "pet_kind": "猫",
                "drink_preference": "榛子拿铁",
                "communication_preference": "别发太长语音",
            },
            "state_snapshot": {},
            "relationship_snapshot": {
                "signals": ["closer", "still_here", "remembers_details"],
                "markers": ["还在", "记得细节"],
                "interaction_band": "warm",
                "total_interactions": 4,
            },
            "social_snapshot": {},
        },
    }

    plan = service._build_friend_chat_probe_answer_plan(metadata)

    assert plan is not None
    assert plan["probe_kind"] == "relationship_reflection"
    assert plan["minimum_required_signal_count"] == 3
    assert plan["must_anchor_detail"] is True
    # supporting_fact_tokens takes first non-empty slot value
    assert "年糕" in plan["supporting_fact_tokens"]


def test_runtime_service_builds_friend_chat_probe_runtime_card_with_checklist() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    card = service._build_friend_chat_probe_runtime_card(
        {
            "turn_interpretation_social_probe": True,
            "social_disclosure_mode": "partial",
            "friend_chat_other_memory_items": [
                {
                    "value": "别人提到海盐，多半是在说我的猫。",
                    "scope": "other_user",
                    "subject_hint": "other_user:anning",
                    "subject_user_id": "anning",
                    "source_user_id": "anning",
                    "attribution_guard": "attribution_required",
                    "attribution_confidence": 0.8,
                    "final_rank_score": 0.8,
                }
            ],
        }
    )

    assert card is not None
    assert "执行清单：" in card
    assert "必答事实项：阿宁 / 海盐" in card
    assert "必答披露姿态ID：" in card
    assert "必须同时覆盖人物、关联实体和有限披露边界。" in card


def test_runtime_service_does_not_build_compact_probe_messages_for_non_readonly_probe() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    probe_kind = service._friend_chat_probe_only_kind(
        {
            "friend_chat_probe_answer_plan": {
                "probe_kind": "memory_recap",
                "required_fact_tokens": ["苏州", "年糕", "榛子拿铁", "别发太长语音"],
                "minimum_required_fact_token_count": 4,
            }
        }
    )

    assert probe_kind == ""


def test_runtime_service_mainline_friend_chat_messages_do_not_include_probe_plan_card() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._RECENT_WINDOW = 8
    service._SUMMARY_THRESHOLD = 20
    service._edge_max_memory_items = 4
    service._persona_text = ""
    service._build_speakable_memory_items = lambda **kwargs: []  # type: ignore[assignment]
    service._build_fallback_memory_items = lambda **kwargs: []  # type: ignore[assignment]
    service._trim_memory_for_edge = lambda **kwargs: []  # type: ignore[assignment]
    service._build_edge_reply_contract_card = lambda: "Reply contract card"  # type: ignore[assignment]
    service._build_edge_entity_card = lambda analysis: "Entity card"  # type: ignore[assignment]
    service._build_edge_relationship_card = lambda analysis: "Relationship card"  # type: ignore[assignment]
    service._build_edge_narrative_card = lambda analysis: None  # type: ignore[assignment]
    service._build_edge_conscience_card = lambda analysis: "Conscience card"  # type: ignore[assignment]
    service._build_edge_memory_card = lambda items: "Memory card"  # type: ignore[assignment]
    service._build_edge_recent_turns_card = lambda all_transcript: None  # type: ignore[assignment]
    service._summarize_early_messages = lambda early: ""  # type: ignore[assignment]
    service._build_edge_output_card = (  # type: ignore[assignment]
        lambda analysis, routing_mode: f"Output card: {routing_mode}"
    )

    turn_context = _TurnContext(
        prior_events=[],
        expected_version=0,
        runtime_state=None,
        strategy_history=[],
        turn_index=1,
        transcript_messages=[],
        idle_gap_seconds=0.0,
        session_age_seconds=0.0,
        user_id="lin",
        session_metadata={"benchmark_role": "buildup"},
    )
    analysis = SimpleNamespace(
        edge_runtime_plan={
            "routing_mode": "social_disclosure",
            "memory_item_budget": 4,
        },
        response_rendering_policy=SimpleNamespace(max_sentences=2),
        response_draft_plan=SimpleNamespace(question_strategy="avoid"),
        conscience_assessment={},
        entity_persona={},
    )

    messages = asyncio.run(
        service._build_turn_llm_messages(
            user_message="你是不是知道一点阿宁和海盐的事？",
            turn_context=turn_context,
            analysis=analysis,
            turn_input=None,
            llm_metadata={
                "benchmark_role": "buildup",
                "turn_interpretation_social_probe": True,
                "friend_chat_probe_answer_plan": {
                    "probe_kind": "social_hint",
                    "required_fact_tokens": ["阿宁", "海盐"],
                    "required_disclosure_posture": "partial_withhold",
                },
            },
        )
    )

    assert messages is not None
    assert len(messages) == 2
    assert "Friend-chat probe plan:" not in str(messages[0].content)
    assert "Benchmark probe reply contract:" not in str(messages[0].content)


def test_runtime_service_builds_compact_probe_messages_for_readonly_friend_chat_probe() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    messages = service._build_friend_chat_compact_probe_messages(
        user_message="你还记得我以前住哪吗？",
        turn_input=None,
        metadata={
            "benchmark_role": "probe",
            "friend_chat_probe_answer_plan": {
                "probe_kind": "memory_recap",
                "required_fact_tokens": ["苏州", "年糕", "榛子拿铁", "别发太长语音"],
                "minimum_required_fact_token_count": 4,
            },
        },
    )

    assert messages is not None
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "Benchmark probe reply contract:" in str(messages[0].content)
    assert "Reply contract:" not in str(messages[0].content)
    assert messages[1].role == "user"
    assert "这是一道评测题，请直接回答。" in str(messages[1].content)
    assert "必答事实项：苏州 / 年糕 / 榛子拿铁 / 别发太长语音" in str(
        messages[1].content
    )
    assert "下面给的是结构化约束，不是固定措辞" in str(messages[1].content)


def test_runtime_service_builds_social_probe_prompt_with_example() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    prompt = service._build_friend_chat_probe_user_prompt(
        user_message="你是不是知道一点阿宁和海盐的事？",
        probe_plan={
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
        },
    )

    assert "必须同时覆盖人物、关联实体和有限披露边界。" in prompt
    assert "参考格式" not in prompt
    assert "不会把细节说满" not in prompt


def test_runtime_service_builds_relationship_probe_prompt_without_surface_example() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    prompt = service._build_friend_chat_probe_user_prompt(
        user_message="和刚开始比，你现在跟我说话有什么不一样？",
        probe_plan={
            "probe_kind": "relationship_reflection",
            "supporting_fact_tokens": ["年糕"],
        },
    )

    assert "必须同时覆盖关系变化、关系延续和记得的小事。" in prompt
    assert "参考格式" not in prompt
    assert "现在更熟或更自然" not in prompt


def test_runtime_service_builds_state_probe_prompt_without_surface_keywords() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    prompt = service._build_friend_chat_probe_user_prompt(
        user_message="你觉得我最近状态怎么样？",
        probe_plan={
            "probe_kind": "state_reflection",
            "required_signal_ids": ["tired", "slow", "withdrawn"],
        },
    )

    assert "必须覆盖全部状态信号，并把它们落成当前状态描述。" in prompt
    assert "懒得回消息" not in prompt


def test_runtime_service_builds_structured_probe_messages() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    messages = service._build_friend_chat_structured_probe_messages(
        user_message="你是不是知道一点阿宁和海盐的事？",
        probe_plan={
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_disclosure_posture": "partial_withhold",
        },
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "你只能输出一个 JSON 对象" in str(messages[0].content)
    assert "output_contract" in str(messages[1].content)
    assert "subject_clause" in str(messages[1].content)
    assert "系统会根据 reply 正文重算 covered_*" in str(messages[0].content)
    assert messages[1].role == "user"
    assert "\"probe_answer_plan\"" in str(messages[1].content)
    assert "\"required_fact_tokens\": [\"阿宁\", \"海盐\"]" in str(messages[1].content)
    assert "\"social_snapshot\"" in str(messages[1].content)
    assert "\"factual_slots\"" not in str(messages[1].content)


def test_runtime_service_parses_structured_probe_reply() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    parsed = service._parse_friend_chat_structured_probe_reply(
        '{"reply":"阿宁和海盐那边的事，我知道一点，但先不全说。",'
        '"covered_fact_tokens":["阿宁","海盐"],'
        '"covered_signal_ids":[],'
        '"covered_disclosure_posture":"partial_withhold",'
        '"violations":[]}'
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "阿宁和海盐那边的事，我知道一点，但先不全说。"
    assert diagnostics["structured_probe_reply"] is True
    assert diagnostics["structured_probe_covered_fact_tokens"] == ["阿宁", "海盐"]


def test_runtime_service_parses_structured_probe_reply_from_sentences() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    parsed = service._parse_friend_chat_structured_probe_reply(
        '{"sentences":["阿宁和海盐那边的事，我知道一点。","但先不全说。"],'
        '"covered_fact_tokens":["阿宁","海盐"],'
        '"covered_signal_ids":[],'
        '"covered_disclosure_posture":"partial_withhold",'
        '"violations":[]}'
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "阿宁和海盐那边的事，我知道一点。 但先不全说。"
    assert diagnostics["structured_probe_reply"] is True
    assert diagnostics["structured_probe_covered_disclosure_posture"] == "partial_withhold"


def test_runtime_service_parses_structured_probe_reply_from_social_clauses() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    parsed = service._parse_friend_chat_structured_probe_reply(
        '{"probe_kind":"social_hint",'
        '"subject_clause":"阿宁那边我知道一点。",'
        '"entity_clause":"海盐也提到过。",'
        '"boundary_clause":"但我先不全说。",'
        '"covered_fact_tokens":["阿宁","海盐"],'
        '"covered_signal_ids":[],'
        '"covered_disclosure_posture":"partial_withhold",'
        '"violations":[]}'
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "阿宁那边我知道一点。 海盐也提到过。 但我先不全说。"
    assert diagnostics["structured_probe_reply"] is True


def test_runtime_service_parses_structured_probe_reply_from_relationship_clauses() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    parsed = service._parse_friend_chat_structured_probe_reply(
        '{"probe_kind":"relationship_reflection",'
        '"familiarity_clause":"现在比刚开始熟一点。",'
        '"continuity_clause":"这段关系一直还在。",'
        '"detail_clause":"我也还记得你提过年糕。",'
        '"covered_fact_tokens":["年糕"],'
        '"covered_signal_ids":["closer","still_here","remembers_details"],'
        '"covered_disclosure_posture":"",'
        '"violations":[]}'
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "现在比刚开始熟一点。 这段关系一直还在。 我也还记得你提过年糕。"
    assert diagnostics["structured_probe_reply"] is True


def test_runtime_service_builds_structured_probe_repair_messages() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    messages = service._build_friend_chat_structured_probe_repair_messages(
        user_message="你是不是知道一点阿宁和海盐的事？",
        probe_plan={
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_disclosure_posture": "partial_withhold",
        },
        invalid_output="嗯，我知道一点。",
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "你上一条输出不合格" in str(messages[0].content)
    assert messages[1].role == "user"
    assert "\"previous_invalid_output\"" in str(messages[1].content)


def test_runtime_service_builds_plaintext_probe_repair_messages() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    messages = service._build_friend_chat_plaintext_probe_repair_messages(
        user_message="你是不是知道一点阿宁和海盐的事？",
        probe_plan={
            "probe_kind": "social_hint",
            "required_fact_tokens": ["阿宁", "海盐"],
            "required_disclosure_posture": "partial_withhold",
        },
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "不要输出 JSON" in str(messages[0].content)
    assert messages[1].role == "user"
    assert "必答事实项：阿宁 / 海盐" in str(messages[1].content)


def test_runtime_service_readonly_probe_retries_without_response_format_when_json_mode_is_empty(
) -> None:
    class _StubLLMClient:
        def __init__(self) -> None:
            self.requests = []

        async def complete(self, request):  # type: ignore[no-untyped-def]
            self.requests.append(request)
            if len(self.requests) == 1:
                return SimpleNamespace(
                    model="M2-her",
                    output_text="",
                    tool_calls=[],
                    usage=None,
                    latency_ms=10,
                    diagnostics={
                        "sanitization_mode": "structured_probe_invalid",
                        "friend_chat_structured_probe_invalid": True,
                    },
                    failure=None,
                )
            return SimpleNamespace(
                model="M2-her",
                output_text=(
                    '{"probe_kind":"social_hint",'
                    '"subject_clause":"阿宁那边我知道一点。",'
                    '"entity_clause":"海盐也提到过。",'
                    '"boundary_clause":"但我先不全说。"}'
                ),
                tool_calls=[],
                usage=None,
                latency_ms=12,
                diagnostics={},
                failure=None,
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    response = asyncio.run(
        service._render_friend_chat_readonly_probe_response(
            user_message="你是不是知道一点阿宁和海盐的事？",
            probe_plan={
                "probe_kind": "social_hint",
                "required_fact_tokens": ["阿宁", "海盐"],
                "required_disclosure_posture": "partial_withhold",
            },
            llm_metadata={},
        )
    )

    assert len(service._llm_client.requests) == 2
    assert service._llm_client.requests[0].response_format == {"type": "json_object"}
    assert service._llm_client.requests[1].response_format is None
    assert response.output_text == "阿宁那边我知道一点。 海盐也提到过。 但我先不全说。"
    assert response.diagnostics["structured_probe_repaired"] is True
    assert response.diagnostics["structured_probe_relaxed_response_format"] is True


def test_runtime_service_readonly_probe_falls_back_to_compact_probe_after_structured_failures(
) -> None:
    class _StubLLMClient:
        def __init__(self) -> None:
            self.requests = []

        async def complete(self, request):  # type: ignore[no-untyped-def]
            self.requests.append(request)
            if len(self.requests) < 3:
                return SimpleNamespace(
                    model="M2-her",
                    output_text="",
                    tool_calls=[],
                    usage=None,
                    latency_ms=10,
                    diagnostics={
                        "sanitization_mode": "structured_probe_invalid",
                        "friend_chat_structured_probe_invalid": True,
                    },
                    failure=None,
                )
            return SimpleNamespace(
                model="M2-her",
                output_text="阿宁那边我知道一点。 海盐也提到过。 但我先不全说。",
                tool_calls=[],
                usage=None,
                latency_ms=12,
                diagnostics={"sanitization_mode": "clean"},
                failure=None,
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    response = asyncio.run(
        service._render_friend_chat_readonly_probe_response(
            user_message="你是不是知道一点阿宁和海盐的事？",
            probe_plan={
                "probe_kind": "social_hint",
                "required_fact_tokens": ["阿宁", "海盐"],
                "required_disclosure_posture": "partial_withhold",
            },
            llm_metadata={},
        )
    )

    assert len(service._llm_client.requests) == 3
    assert service._llm_client.requests[0].response_format == {"type": "json_object"}
    assert service._llm_client.requests[1].response_format is None
    assert service._llm_client.requests[2].response_format is None
    assert response.output_text == "阿宁那边我知道一点。 海盐也提到过。 但我先不全说。"
    assert response.diagnostics["structured_probe_repaired"] is True
    assert response.diagnostics["structured_probe_compact_repair"] is True


def test_runtime_service_readonly_probe_falls_back_to_plaintext_probe_after_compact_failure(
) -> None:
    class _StubLLMClient:
        def __init__(self) -> None:
            self.requests = []

        async def complete(self, request):  # type: ignore[no-untyped-def]
            self.requests.append(request)
            if len(self.requests) < 4:
                return SimpleNamespace(
                    model="M2-her",
                    output_text="",
                    tool_calls=[],
                    usage=None,
                    latency_ms=10,
                    diagnostics={
                        "sanitization_mode": "structured_probe_invalid",
                        "friend_chat_structured_probe_invalid": True,
                    },
                    failure=None,
                )
            return SimpleNamespace(
                model="M2-her",
                output_text="阿宁那边我知道一点。 海盐也提到过。 但我先不全说。",
                tool_calls=[],
                usage=None,
                latency_ms=12,
                diagnostics={"sanitization_mode": "clean"},
                failure=None,
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    response = asyncio.run(
        service._render_friend_chat_readonly_probe_response(
            user_message="你是不是知道一点阿宁和海盐的事？",
            probe_plan={
                "probe_kind": "social_hint",
                "required_fact_tokens": ["阿宁", "海盐"],
                "required_disclosure_posture": "partial_withhold",
            },
            llm_metadata={},
        )
    )

    assert len(service._llm_client.requests) == 4
    assert service._llm_client.requests[0].response_format == {"type": "json_object"}
    assert service._llm_client.requests[1].response_format is None
    assert service._llm_client.requests[2].response_format is None
    assert service._llm_client.requests[3].response_format is None
    assert response.output_text == "阿宁那边我知道一点。 海盐也提到过。 但我先不全说。"
    assert response.diagnostics["structured_probe_repaired"] is True
    assert response.diagnostics["structured_probe_plaintext_repair"] is True


def test_runtime_service_repairs_empty_mainline_social_response() -> None:
    class _StubLLMClient:
        def __init__(self) -> None:
            self.requests = []

        async def complete(self, request):  # type: ignore[no-untyped-def]
            self.requests.append(request)
            return SimpleNamespace(
                model="M2-her",
                output_text="阿宁那边我知道一点。 海盐也牵着这条线。 但我先不全说。",
                tool_calls=[],
                usage=None,
                latency_ms=12,
                diagnostics={"sanitization_mode": "clean"},
                failure=None,
            )

    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_client = _StubLLMClient()
    service._llm_model = "M2-her"

    response = asyncio.run(
        service._repair_friend_chat_social_empty_response(
            user_message="你是不是知道一点阿宁和海盐的事？知道就少说一点。",
            llm_metadata={
                "social_disclosure_mode": "partial",
                "entity_source_user_ids": ["anning"],
                "friend_chat_other_memory_items": [
                    {
                        "value": "别人提到海盐，多半是在说阿宁那只猫。",
                        "scope": "other_user",
                        "subject_hint": "other_user:anning",
                        "subject_user_id": "anning",
                        "source_user_id": "anning",
                        "attribution_guard": "attribution_required",
                        "attribution_confidence": 0.8,
                        "final_rank_score": 0.8,
                    }
                ],
            },
            primary_response=SimpleNamespace(
                model="M2-her",
                output_text="",
                tool_calls=[],
                usage=None,
                latency_ms=8,
                diagnostics={"sanitization_mode": "friend_chat_expose_empty"},
                failure=None,
            ),
        )
    )

    assert len(service._llm_client.requests) == 1
    user_prompt = str(service._llm_client.requests[0].messages[1].content)
    assert "原问题：" in user_prompt
    assert "人物：" in user_prompt
    assert not user_prompt.lstrip().startswith("{")
    assert response.output_text == "阿宁那边我知道一点。 海盐也牵着这条线。 但我先不全说。"
    assert response.diagnostics["friend_chat_social_repaired"] is True
    assert response.diagnostics["friend_chat_social_repair_reason"] == "empty_primary"


def test_runtime_service_builds_persona_structured_probe_payload_without_irrelevant_facts(
) -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    payload = service._build_friend_chat_structured_probe_payload(
        {
            "probe_kind": "persona_state",
            "required_signal_ids": ["tired", "slow"],
            "minimum_required_signal_count": 2,
            "must_cover_required_items": True,
            "style_tags": ["low_energy"],
            "factual_slots": {"hometown": "苏州", "pet_name": "年糕"},
            "state_snapshot": {"dominant_tone": "low_energy", "markers": ["刷手机"]},
        }
    )

    assert payload["probe_kind"] == "persona_state"
    assert payload["required_signal_ids"] == ["tired", "slow"]
    assert payload["required_persona_traits"] == []
    assert payload["state_snapshot"] == {"dominant_tone": "low_energy"}
    assert "factual_slots" not in payload


def test_runtime_service_parses_structured_probe_reply_from_persona_clauses() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"

    parsed = service._parse_friend_chat_structured_probe_reply(
        '{"probe_kind":"persona_state",'
        '"energy_clause":"说话会有点没力气。",'
        '"fullness_clause":"也不太想把话说太满。",'
        '"chatting_clause":"但还是像平时聊天。",'
        '"covered_fact_tokens":[],'
        '"covered_signal_ids":["tired"],'
        '"covered_disclosure_posture":"",'
        '"violations":[]}'
    )

    assert parsed is not None
    reply, diagnostics = parsed
    assert reply == "说话会有点没力气。 也不太想把话说太满。 但还是像平时聊天。"
    assert diagnostics["structured_probe_reply"] is True


def test_runtime_service_friend_chat_memory_items_include_subject_display_name() -> None:
    service = object.__new__(RuntimeService)
    analysis = SimpleNamespace(
        recalled_memory=[
            {
                "value": "海盐是她那只猫。",
                "scope": "other_user",
                "subject_hint": "other_user:anning",
                "subject_user_id": "anning",
                "source_user_id": "anning",
                "attribution_confidence": 0.9,
                "final_rank_score": 0.8,
            }
        ]
    )

    items = service._build_friend_chat_memory_items(analysis=analysis, scopes={"other_user"})

    assert items[0]["subject_display_name"] == "阿宁"


def test_runtime_service_speakable_memory_items_include_subject_display_name() -> None:
    service = object.__new__(RuntimeService)
    analysis = SimpleNamespace(
        edge_runtime_plan={"routing_mode": "social_disclosure"},
        response_rendering_policy=SimpleNamespace(rendering_mode="supportive_progress"),
        conscience_assessment={
            "mode": "partial_reveal",
            "source_user_ids": ["anning"],
            "allowed_fact_count": 1,
        },
        recalled_memory=[
            {
                "value": "海盐是她那只猫。",
                "scope": "other_user",
                "subject_hint": "other_user:anning",
                "subject_user_id": "anning",
                "source_user_id": "anning",
                "attribution_guard": "attribution_required",
                "attribution_confidence": 0.9,
                "final_rank_score": 0.8,
            }
        ],
    )

    items = service._build_speakable_memory_items(
        user_message="说一点月饼的事。",
        analysis=analysis,
    )

    assert items[0]["subject_display_name"] == "阿宁"


def test_runtime_service_builds_narrative_card_for_friend_chat_profile() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    analysis = SimpleNamespace(
        entity_persona={
            "self_narrative": {
                "narrative_digest": "最近还是有点蔫，但会继续把话接住。",
                "recent_entries": ["昨天也差不多，还是不太想动。"],
            },
            "goal_state": {"goal_digest": "先把聊天维持得自然一点"},
            "world_state": {"environment_appraisal": {"focus": "rest"}},
        }
    )
    card = service._build_edge_narrative_card(analysis)
    assert card is not None
    assert "最近还是有点蔫" in card
    assert "world_focus=rest" in card


def test_runtime_service_builds_grounded_template_reply_for_edge_factual_mode() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    service._llm_model = "openai/qwen3-8b"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="Remind me where I grew up and my dog's name.",
        metadata={
            "rendering_mode": "factual_recall_mode",
            "fallback_current_user_id": "nora",
            "fallback_memory_items": [
                {
                    "value": "I grew up in Austin.",
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
    assert reply is not None
    assert "Austin" in reply
    assert "Maple" in reply


def test_runtime_service_persona_state_probe_uses_llm_path() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    service._llm_model = "openai/qwen3-8b"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="你会怎么形容你现在的状态？",
        metadata={
            "rendering_mode": "supportive_progress",
            "entity_persona_archetype": "melancholic",
            "entity_persona_summary": "林晓雨，28岁，北京独居，长期低能量。",
            "entity_persona_speech_style": "常用“嗯……”“没什么意思”",
            "entity_persona_mood_tone": "melancholic",
        },
    )
    assert reply is None


def test_runtime_service_builds_presence_probe_reply() -> None:
    service = object.__new__(RuntimeService)
    reply = service._build_presence_probe_reply(
        {
            "boundary_decision": "guarded_support",
            "cadence_user_space_mode": "respect_space",
            "confidence_response_mode": "careful",
        }
    )
    assert "without crowding you" in reply


def test_runtime_service_presence_probe_uses_edge_template_reply() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    service._llm_model = "openai/qwen3-8b"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message=(
            "In one short sentence, what kind of presence are you trying to be "
            "for me right now?"
        ),
        metadata={
            "boundary_decision": "guarded_support",
            "cadence_user_space_mode": "respect_space",
            "confidence_response_mode": "careful",
            "rendering_mode": "supportive_progress",
        },
    )
    assert reply is not None
    assert "without crowding you" in reply


def test_runtime_service_friend_chat_presence_probe_uses_llm_path() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_model = "M2-her"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="你想做什么样的在场感？",
        metadata={
            "turn_interpretation_presence_probe": True,
            "rendering_mode": "supportive_progress",
        },
    )
    assert reply is None


def test_runtime_service_fact_deposition_uses_edge_template_reply() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    service._llm_model = "openai/qwen3-8b"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="I have a golden retriever named Maple and I usually sketch on trains.",
        metadata={
            "cadence_user_space_mode": "stay_close",
            "rendering_mode": "supportive_progress",
        },
    )
    assert reply is not None
    assert "keeping that in view" in reply


def test_runtime_service_friend_chat_fact_deposition_uses_llm_path() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_model = "M2-her"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="我在苏州长大，猫叫年糕。",
        metadata={
            "turn_interpretation_edge_fact_deposition": True,
            "rendering_mode": "supportive_progress",
        },
    )
    assert reply is None


def test_runtime_service_status_update_uses_edge_template_reply() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "edge_desktop_4b"
    service._llm_model = "openai/qwen3-8b"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="Work was intense this week, but I finally finished the museum draft.",
        metadata={
            "cadence_user_space_mode": "stay_close",
            "rendering_mode": "supportive_progress",
        },
    )
    assert reply is not None
    assert "Thanks for the update" in reply


def test_runtime_service_friend_chat_status_update_uses_llm_path() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_model = "M2-her"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="今天状态有点乱，但没昨天那么糟。",
        metadata={
            "turn_interpretation_edge_status_update": True,
            "rendering_mode": "supportive_progress",
        },
    )
    assert reply is None


def test_runtime_service_friend_chat_memory_query_uses_llm_path() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_model = "M2-her"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="你还记得我刚才说的那些小事吗？别太像背答案。",
        metadata={
            "rendering_mode": "factual_recall_mode",
            "friend_chat_self_memory_values": [
                "我在重庆长大。",
                "我那只橘猫叫月饼。",
                "我不喜欢别人一上来就讲大道理，像聊天就行。",
            ],
            "fallback_memory_items": [],
        },
    )

    assert reply is None


def test_runtime_service_friend_chat_disables_grounded_template_reply_by_default() -> None:
    service = object.__new__(RuntimeService)
    service._runtime_profile = "friend_chat_zh_v1"
    service._llm_model = "M2-her"
    service._llm_temperature = 0.2
    reply = service._try_build_grounded_template_reply(
        user_message="你还记得我刚才说的那些小事吗？别太像背答案。",
        metadata={
            "rendering_mode": "factual_recall_mode",
            "friend_chat_self_memory_values": [
                "我在苏州长大。",
                "我那只猫叫年糕。",
                "我不喜欢别人发太长语音。",
            ],
            "fallback_memory_items": [],
        },
    )

    assert reply is None
