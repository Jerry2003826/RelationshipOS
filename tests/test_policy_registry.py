import json
from pathlib import Path

from relationship_os.application.policy_registry import PolicyRegistry


def test_policy_registry_merges_base_profile_and_archetype_overrides(tmp_path) -> None:
    policies = tmp_path / "policies"
    for group in ("memory", "conscience", "rendering", "persona"):
        (policies / group / "profiles").mkdir(parents=True, exist_ok=True)
        (policies / group / "archetypes").mkdir(parents=True, exist_ok=True)

    (policies / "memory" / "base.json").write_text(
        json.dumps(
            {
                "version": "memory-v1",
                "thresholds": {"pin": 0.7},
                "weights": {"scope_bonuses": {"session": 0.08}},
            }
        ),
        encoding="utf-8",
    )
    (policies / "memory" / "profiles" / "edge_desktop_4b.json").write_text(
        json.dumps({"thresholds": {"pin": 0.66}}),
        encoding="utf-8",
    )
    (policies / "memory" / "archetypes" / "melancholic.json").write_text(
        json.dumps({"weights": {"scope_bonuses": {"session": 0.11}}}),
        encoding="utf-8",
    )
    for group in ("conscience", "rendering", "persona"):
        (policies / group / "base.json").write_text(
            json.dumps({"version": f"{group}-v1"}),
            encoding="utf-8",
        )

    registry = PolicyRegistry(root_path=policies)
    compiled = registry.compile_policy_set(
        runtime_profile="edge_desktop_4b",
        archetype="melancholic",
    )

    assert compiled.runtime_profile == "edge_desktop_4b"
    assert compiled.archetype == "melancholic"
    assert compiled.memory_policy["thresholds"]["pin"] == 0.66
    assert compiled.memory_policy["weights"]["scope_bonuses"]["session"] == 0.11
    assert compiled.source_paths["memory"]


def test_policy_registry_merges_rendering_profile_runtime_behavior(tmp_path) -> None:
    policies = tmp_path / "policies"
    for group in ("memory", "conscience", "rendering", "persona"):
        (policies / group / "profiles").mkdir(parents=True, exist_ok=True)
        (policies / group / "archetypes").mkdir(parents=True, exist_ok=True)
        (policies / group / "base.json").write_text(
            json.dumps({"version": f"{group}-v1"}),
            encoding="utf-8",
        )

    (policies / "rendering" / "base.json").write_text(
        json.dumps(
            {
                "version": "rendering-v1",
                "runtime_behavior": {"edge_routing": {"large_user_message_threshold": 600}},
            }
        ),
        encoding="utf-8",
    )
    (policies / "rendering" / "profiles" / "edge_desktop_4b.json").write_text(
        json.dumps({"runtime_behavior": {"edge_routing": {"large_user_message_threshold": 420}}}),
        encoding="utf-8",
    )

    registry = PolicyRegistry(root_path=policies)
    compiled = registry.compile_policy_set(runtime_profile="edge_desktop_4b")

    assert (
        compiled.rendering_policy["runtime_behavior"]["edge_routing"][
            "large_user_message_threshold"
        ]
        == 420
    )


def test_policy_registry_merges_response_rendering_profile_overrides(tmp_path) -> None:
    policies = tmp_path / "policies"
    for group in ("memory", "conscience", "rendering", "persona"):
        (policies / group / "profiles").mkdir(parents=True, exist_ok=True)
        (policies / group / "archetypes").mkdir(parents=True, exist_ok=True)
        (policies / group / "base.json").write_text(
            json.dumps({"version": f"{group}-v1"}),
            encoding="utf-8",
        )

    (policies / "rendering" / "base.json").write_text(
        json.dumps(
            {
                "version": "rendering-v1",
                "response_rendering": {
                    "defaults": {"max_sentences": 4},
                    "clarify": {"max_sentences": 3},
                },
            }
        ),
        encoding="utf-8",
    )
    (policies / "rendering" / "profiles" / "edge_desktop_4b.json").write_text(
        json.dumps(
            {
                "response_rendering": {
                    "clarify": {"max_sentences": 2},
                }
            }
        ),
        encoding="utf-8",
    )

    registry = PolicyRegistry(root_path=policies)
    compiled = registry.compile_policy_set(runtime_profile="edge_desktop_4b")

    assert compiled.rendering_policy["response_rendering"]["defaults"]["max_sentences"] == 4
    assert compiled.rendering_policy["response_rendering"]["clarify"]["max_sentences"] == 2


def test_policy_registry_loads_friend_chat_profile_from_repo() -> None:
    registry = PolicyRegistry(root_path=Path("policies"))
    compiled = registry.compile_policy_set(runtime_profile="friend_chat_zh_v1")

    assert compiled.rendering_policy["response_rendering"]["defaults"]["max_sentences"] == 3
    assert compiled.persona_policy["action_policy"]["max_actions_per_turn"] == 0
    assert (
        compiled.conscience_policy["mode_configs"]["partial_reveal"]["allowed_fact_count_cap"] == 1
    )
