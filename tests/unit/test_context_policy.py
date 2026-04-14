from types import SimpleNamespace

from relationship_os.application.analyzers.context import (
    infer_appraisal,
    infer_attention,
    infer_bid_signal,
    infer_dialogue_act,
    infer_topic,
)


def test_infer_dialogue_act_uses_policy_tokens(monkeypatch) -> None:
    from relationship_os.application.analyzers import context as context_module

    monkeypatch.setattr(
        context_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "context_inference": {
                    "dialogue_act": {
                        "request_tokens_en": ["assistme"],
                        "request_tokens_zh": ["请搭把手"],
                    }
                }
            }
        ),
    )

    assert infer_dialogue_act("Could you assistme with this?") == "question"
    assert infer_dialogue_act("请搭把手看看") == "request"


def test_infer_bid_signal_uses_policy_tokens(monkeypatch) -> None:
    from relationship_os.application.analyzers import context as context_module

    monkeypatch.setattr(
        context_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "context_inference": {
                    "bid_signal": {
                        "connection_request_tokens_en": ["adrift"],
                        "soft_bid_tokens_en": ["quickupdate"],
                    }
                }
            }
        ),
    )

    assert infer_bid_signal("I feel adrift lately.") == "connection_request"
    assert infer_bid_signal("Just a quickupdate for you.") == "soft_bid"


def test_infer_topic_uses_policy_keyword_map(monkeypatch) -> None:
    from relationship_os.application.analyzers import context as context_module

    monkeypatch.setattr(
        context_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "context_inference": {
                    "topic_keywords": {
                        "finance": ["invoice", "budgetsheet"],
                    }
                }
            }
        ),
    )

    assert infer_topic("I need to review the invoice and budgetsheet.") == "finance"


def test_infer_attention_uses_policy_thresholds(monkeypatch) -> None:
    from relationship_os.application.analyzers import context as context_module

    monkeypatch.setattr(
        context_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "context_inference": {
                    "attention": {
                        "high_length_threshold": 20,
                        "focused_length_threshold": 10,
                        "high_tokens_en": ["rushnow"],
                    }
                }
            }
        ),
    )

    assert infer_attention("please rushnow") == "high"
    assert infer_attention("12345678901") == "focused"


def test_infer_appraisal_uses_policy_tokens(monkeypatch) -> None:
    from relationship_os.application.analyzers import context as context_module

    monkeypatch.setattr(
        context_module,
        "get_default_compiled_policy_set",
        lambda **_: SimpleNamespace(
            conscience_policy={
                "context_inference": {
                    "appraisal": {
                        "negative_tokens_en": ["bleak"],
                        "positive_tokens_en": ["glowing"],
                    }
                }
            }
        ),
    )

    assert infer_appraisal("Today feels bleak.") == "negative"
    assert infer_appraisal("Everything feels glowing.") == "positive"
