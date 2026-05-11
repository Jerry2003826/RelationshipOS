from relationship_os.application.runtime.friend_chat_fact_extractors import (
    extract_drink_preference_from_text,
    extract_hometown_from_text,
    extract_pet_name_from_text,
    extract_social_entity_token,
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
