from __future__ import annotations

import re
from typing import Any

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


def normalize_communication_preference(text: str) -> str:
    raw = str(text or "").strip(_STRIP_CHARS)
    if not raw:
        return ""
    if ("语音" in raw or "长语音" in raw or "语音条" in raw) and any(
        token in raw for token in ("别发", "别给我发", "不爱", "怕", "不喜欢", "别太长", "太长")
    ):
        return "别发太长语音"
    if "大道理" in raw:
        return "别讲大道理"
    return ""


def normalize_fact_slot_digest(payload: Any) -> dict[str, Any]:
    data = payload if isinstance(payload, dict) else {}
    pet_name = str(data.get("pet_name", "") or "").strip()
    pet_kind = str(data.get("pet_kind", "") or "").strip()
    legacy_pet = str(data.get("pet", "") or "").strip()
    if legacy_pet and not pet_name:
        match = re.search(r"叫(?P<name>[\u4e00-\u9fffA-Za-z0-9]{1,12})", legacy_pet)
        if match is None:
            match = re.search(
                r"named (?P<name>[A-Za-z][A-Za-z\s-]{0,20})",
                legacy_pet,
                re.IGNORECASE,
            )
        if match:
            pet_name = str(match.group("name") or "").strip()
        if not pet_kind:
            for kind in ("猫", "狗", "宠物"):
                if kind in legacy_pet:
                    pet_kind = kind
                    break
    living_facts = [
        str(value).strip(_STRIP_CHARS)
        for value in list(data.get("living_facts") or [])
        if str(value).strip()
    ]
    hometown = str(data.get("hometown", "") or "").strip(_STRIP_CHARS)
    if hometown.startswith("我在") and hometown.endswith("长大"):
        hometown = hometown.removeprefix("我在").removesuffix("长大").strip()
    drink_preference = str(data.get("drink_preference", "") or "").strip(_STRIP_CHARS)
    communication_preference = str(data.get("communication_preference", "") or "").strip(
        _STRIP_CHARS
    )
    return {
        "hometown": hometown,
        "pet_name": pet_name,
        "pet_kind": pet_kind,
        "drink_preference": drink_preference,
        "communication_preference": normalize_communication_preference(communication_preference),
        "living_facts": living_facts,
        "stable_slots": [
            str(value).strip()
            for value in list(data.get("stable_slots") or [])
            if str(value).strip()
        ],
    }


def fact_slot_digest_values(
    digest: dict[str, Any],
    *,
    include_living_facts: bool = False,
) -> list[str]:
    values = []
    hometown = str(digest.get("hometown", "") or "").strip()
    pet_name = str(digest.get("pet_name", "") or "").strip()
    pet_kind = str(digest.get("pet_kind", "") or "").strip()
    drink_preference = str(digest.get("drink_preference", "") or "").strip()
    communication_preference = str(digest.get("communication_preference", "") or "").strip()
    if hometown:
        values.append(f"hometown:{hometown}")
    if pet_name:
        values.append(f"pet_name:{pet_name}")
    if pet_kind:
        values.append(f"pet_kind:{pet_kind}")
    if drink_preference:
        values.append(f"drink_preference:{drink_preference}")
    if communication_preference:
        values.append(f"communication_preference:{communication_preference}")
    if include_living_facts:
        values.extend(
            f"living_fact:{str(value).strip(_STRIP_CHARS)}"
            for value in list(digest.get("living_facts") or [])
            if str(value).strip()
        )
    return [value for value in values if value]
