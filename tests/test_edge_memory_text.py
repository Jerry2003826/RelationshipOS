from relationship_os.application.runtime.edge_memory_text import (
    is_low_signal_fallback_memory_value,
    ordered_text_terms,
    text_keywords,
)


def test_is_low_signal_fallback_memory_value_filters_metrics_and_system_summaries() -> None:
    assert is_low_signal_fallback_memory_value("")
    assert is_low_signal_fallback_memory_value("topic:work")
    assert is_low_signal_fallback_memory_value("quality:low")
    assert is_low_signal_fallback_memory_value("assistant: hello")
    assert not is_low_signal_fallback_memory_value("User likes oolong tea")


def test_text_keywords_extracts_non_stopword_terms_case_insensitively() -> None:
    assert text_keywords("Tell me what my dog named Mango likes after work.") == {
        "dog",
        "mango",
        "likes",
        "work",
    }
    assert ordered_text_terms("Dog dog Mango orange orange") == [
        "Dog",
        "dog",
        "Mango",
        "orange",
    ]
    assert text_keywords("猫 叫 月饼，在 北京 长大") == {"月饼", "北京", "长大"}
