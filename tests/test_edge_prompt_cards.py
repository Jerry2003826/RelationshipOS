from types import SimpleNamespace

from relationship_os.application.runtime.edge_prompt_cards import (
    build_edge_entity_card,
    build_edge_memory_card,
    build_edge_output_card,
    build_edge_recent_turns_card,
)


def _analysis() -> SimpleNamespace:
    return SimpleNamespace(
        entity_persona={
            "entity_name": "",
            "persona_archetype": "gentle",
            "current_traits": {"warmth": 0.8, "directness": 0.4},
            "mood": {"tone": "calm", "energy": "low"},
            "persona_summary": "quietly supportive",
            "speech_style": "plain",
        },
        response_rendering_policy=SimpleNamespace(
            rendering_mode="grounded",
            max_sentences=4,
        ),
        response_draft_plan=SimpleNamespace(question_strategy="ask_once"),
        guidance_plan=SimpleNamespace(lead_with="answer"),
        conscience_assessment={"mode": "disclose", "quote_style": "soft"},
    )


def test_build_edge_entity_and_memory_cards_match_runtime_prompt_surface() -> None:
    assert build_edge_entity_card(_analysis(), entity_name="RelationshipOS") == (
        "Entity card:\n"
        "- name=RelationshipOS\n"
        "- archetype=gentle\n"
        "- traits=warmth=0.8, directness=0.4, humor=0.5, theatricality=0.5\n"
        "- mood=tone=calm, energy=low\n"
        "- summary=quietly supportive\n"
        "- speech_style=plain"
    )

    assert build_edge_memory_card([]) == "Memory card:\n- none"
    assert build_edge_memory_card(
        [
            {
                "scope": "self_user",
                "source_user_id": "u1",
                "subject_user_id": "u1",
                "attribution_guard": "safe",
                "value": "likes tea",
            }
        ]
    ) == "Memory card:\n- [self_user] from=u1 subject=u1 guard=safe likes tea"


def test_build_edge_recent_turns_and_output_cards_are_parameterized() -> None:
    recent = build_edge_recent_turns_card(
        all_transcript=[
            {"role": "system", "content": "ignored but rendered as You"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "x" * 121},
        ],
        recent_turn_count=2,
    )

    assert recent == "Recent turns:\n- User: hello\n- You: " + ("x" * 120) + "…"
    assert build_edge_output_card(
        _analysis(),
        routing_mode="factual_recall",
        is_friend_chat_profile=False,
    ) == (
        "Output card:\n"
        "- mode=factual_recall\n"
        "- max_sentences=2\n"
        "- anchor=answer concrete facts first\n"
        "- question_strategy=ask_once"
    )
