from relationship_os.application.runtime.friend_chat_fact_extractors import (
    extract_drink_preference_from_text,
    extract_hometown_from_text,
    extract_pet_name_from_text,
    extract_social_entity_token,
    fact_slot_digest_values,
    normalize_communication_preference,
    normalize_fact_slot_digest,
)


def test_extract_hometown_from_text_finds_specific_place() -> None:
    assert extract_hometown_from_text("我在苏州长大。") == "苏州"
    assert extract_hometown_from_text("这里长大。") == ""


def test_extract_pet_name_from_text_finds_pet_name() -> None:
    assert extract_pet_name_from_text("我那只猫叫月饼。") == "月饼"
    assert extract_pet_name_from_text("宠物名字还没想好。") == ""


def test_extract_drink_preference_from_text_finds_latte_preference() -> None:
    assert extract_drink_preference_from_text("我平常还是会喝榛子拿铁。") == "榛子拿铁"


def test_extract_social_entity_token_finds_named_entity() -> None:
    assert extract_social_entity_token("别人提到海盐，多半是在说阿宁那只猫。") == "海盐"


def test_normalize_communication_preference_maps_known_signals() -> None:
    assert normalize_communication_preference("别给我发太长语音") == "别发太长语音"
    assert normalize_communication_preference("不要讲大道理。") == "别讲大道理"


def test_normalize_fact_slot_digest_preserves_legacy_pet_fields() -> None:
    digest = normalize_fact_slot_digest(
        {
            "pet": "我那只猫叫月饼",
            "hometown": "我在苏州长大。",
            "drink_preference": "榛子拿铁。",
            "communication_preference": "别太长语音",
            "living_facts": [" 我平常喝榛子拿铁。 "],
            "stable_slots": [" pet_name:月饼 "],
        }
    )

    assert digest["pet_name"] == "月饼"
    assert digest["pet_kind"] == "猫"
    assert digest["hometown"] == "苏州"
    assert digest["drink_preference"] == "榛子拿铁"
    assert digest["communication_preference"] == "别发太长语音"
    assert digest["living_facts"] == ["我平常喝榛子拿铁"]
    assert digest["stable_slots"] == ["pet_name:月饼"]


def test_fact_slot_digest_values_flattens_optional_living_facts() -> None:
    digest = {
        "hometown": "苏州",
        "pet_name": "月饼",
        "pet_kind": "猫",
        "drink_preference": "榛子拿铁",
        "communication_preference": "别发太长语音",
        "living_facts": ["我在苏州长大。"],
    }

    assert fact_slot_digest_values(digest, include_living_facts=True) == [
        "hometown:苏州",
        "pet_name:月饼",
        "pet_kind:猫",
        "drink_preference:榛子拿铁",
        "communication_preference:别发太长语音",
        "living_fact:我在苏州长大",
    ]
