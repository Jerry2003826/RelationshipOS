from relationship_os.application.runtime.runtime_behavior_policy import (
    runtime_behavior_bool,
    runtime_behavior_int,
    runtime_behavior_list,
    runtime_behavior_map,
)


def test_runtime_behavior_list_stringifies_and_filters_blank_values() -> None:
    policy = {"tokens": ["a", "", 3, " b "]}

    assert runtime_behavior_list(policy, "tokens", ("fallback",)) == ("a", "3", " b ")
    assert runtime_behavior_list(policy, "missing", ("fallback",)) == ("fallback",)
    assert runtime_behavior_list({"tokens": []}, "tokens", ("fallback",)) == ("fallback",)


def test_runtime_behavior_map_int_and_bool_use_safe_fallbacks() -> None:
    policy = {
        "mapping": {"x": 1},
        "bad_mapping": ["x"],
        "count": "7",
        "bad_count": "many",
        "enabled": "yes",
        "disabled": "off",
        "native_bool": True,
    }

    assert runtime_behavior_map(policy, "mapping") == {"x": 1}
    assert runtime_behavior_map(policy, "bad_mapping") == {}
    assert runtime_behavior_int(policy, "count", 3) == 7
    assert runtime_behavior_int(policy, "bad_count", 3) == 3
    assert runtime_behavior_bool(policy, "enabled", False) is True
    assert runtime_behavior_bool(policy, "disabled", True) is False
    assert runtime_behavior_bool(policy, "native_bool", False) is True
    assert runtime_behavior_bool(policy, "missing", True) is True
