from __future__ import annotations

import re

_STRIP_CHARS = "。！？；;，, "


def extract_hometown_from_text(text: str) -> str:
    stripped = str(text or "").strip(_STRIP_CHARS)
    if not stripped:
        return ""
    patterns = (
        re.compile(r"(?:从小在|从小从|从小)(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})(?:长大|出来的)"),
        re.compile(r"(?:在|从)(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})(?:长大|出来的)"),
        re.compile(r"(?P<place>[\u4e00-\u9fffA-Za-z]{2,10})长大"),
    )
    banned = {"这里", "那边", "老家", "外地", "小时候", "后来"}
    for pattern in patterns:
        match = pattern.search(stripped)
        if not match:
            continue
        place = str(match.group("place") or "").strip()
        if place and place not in banned:
            return place
    return ""


def extract_pet_name_from_text(text: str) -> str:
    stripped = str(text or "").strip(_STRIP_CHARS)
    if not stripped:
        return ""
    patterns = (
        re.compile(r"(?:猫|狗|宠物)[^，。！？；]{0,8}叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(r"我那只(?:猫|狗|宠物)叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})是我那只(?:猫|狗|宠物)"),
    )
    banned = {"宠物", "猫", "狗", "名字"}
    for pattern in patterns:
        match = pattern.search(stripped)
        if not match:
            continue
        name = str(match.group("name") or "").strip()
        if name and name not in banned:
            return name
    return ""


def extract_drink_preference_from_text(text: str) -> str:
    stripped = str(text or "").strip(_STRIP_CHARS)
    if not stripped:
        return ""
    patterns = (
        re.compile(r"(?P<drink>[\u4e00-\u9fffA-Za-z]{1,8}拿铁)"),
        re.compile(r"(?:常喝|爱喝|喜欢喝|平常还是会喝|平时会喝|一般喝)(?P<drink>[^，。！？；]{2,14})"),
        re.compile(r"喝(?P<drink>[^，。！？；]{2,14})(?:比较多|比较顺|比较习惯)?"),
    )
    for pattern in patterns:
        match = pattern.search(stripped)
        if not match:
            continue
        drink = str(match.group("drink") or "").strip()
        latte_match = re.search(r"([\u4e00-\u9fffA-Za-z]{1,8}拿铁)", drink)
        if latte_match:
            drink = str(latte_match.group(1) or "").strip()
        drink = re.sub(r"^(?:东西|喝的|饮料|咖啡|平常|平时|还是|总是|会|点|喝)+", "", drink).strip()
        if drink:
            return drink
    return ""


def extract_social_entity_token(value: str) -> str:
    text = value.strip()
    patterns = (
        re.compile(r"提到(?P<entity>[\u4e00-\u9fffA-Za-z0-9]{1,12})"),
        re.compile(
            r"(?P<entity>[\u4e00-\u9fffA-Za-z0-9]{1,12})是(?:[\u4e00-\u9fffA-Za-z0-9]{0,8})?(?:养的)?(?:猫|狗|宠物)"
        ),
    )
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            entity = str(match.group("entity") or "").strip()
            if entity:
                return entity
    return ""
