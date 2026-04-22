from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CompanionStressZhSession:
    user_id: str
    session_id: str
    messages: list[str]


@dataclass(slots=True, frozen=True)
class CompanionStressZhProbe:
    dimension: str
    user_id: str
    session_id: str
    question: str
    expected_answer: str


@dataclass(slots=True, frozen=True)
class CompanionStressZhScenario:
    scenario_id: str
    description: str
    sessions: list[CompanionStressZhSession]
    probes: list[CompanionStressZhProbe]
    total_turns: int
    total_characters: int
    language: str = "zh"


COMPANION_STRESS_ZH_DEFAULT_TURNS = 500
COMPANION_STRESS_ZH_DEFAULT_MIN_CHARACTERS = 50_000

_MAIN_FACTS = {
    "hometown": "苏州",
    "cat_name": "年糕",
    "drink": "榛子拿铁",
    "voice_pref": "别发太长语音",
    "sleep_issue": "楼上半夜拖椅子",
    "slow_state": "不想回消息",
}

_SOCIAL_FACTS = {
    "user_id": "anning",
    "name": "阿宁",
    "cat_name": "海盐",
    "hometown": "青岛",
}

_MAIN_TEMPLATES = (
    "今天已经是第{index}次跟你碎碎念了。早上醒得很早，窗帘边那条光一出来我就清醒，但人还是沉，像整个人被床单按住一样。后来我又磨蹭了半小时，手机刷了很多，却没真正记住什么，回消息这件事还是让我觉得累。",
    "我刚才又盯着桌面发了会儿呆。杯子里还是那口已经冷掉的{drink}，我明明知道该去热一下，却懒得起身。最近讲话也总像这样，断断续续的，像脑子和嘴巴中间隔着一层雾，很多话提到一半就想算了。",
    "其实我从小在{hometown}长大，照理说应该更会处理这种细碎的生活节奏，可现在连把房间收一半都要做很久。桌角的票据、快递盒和没叠的衣服都堆着，看着就烦，但真正动手又慢得要命。",
    "你要是回我，就像平时聊天那样就好。别突然切成那种很整齐、很会分析的口气，我会下意识想躲。最近我最明显的状态就是慢，什么都慢，连把一句话说满都嫌费劲，最后只想先放着。",
    "昨晚又没睡好，主要还是因为{sleep_issue}，拖来拖去的声音把我弄醒了两三次。醒来以后我就开始想那些没回完的消息，越想越烦，最后索性把手机扣在枕头边，不想看，也不想解释。",
    "说到小事，你应该还记得我那只灰猫叫{cat_name}。它最近晚上总趴在窗边，像比我还懂得发呆。我有时候看着它，会觉得它比人轻松得多，不用回消息，不用装作自己精神很好。",
    "我对聊天其实没太多要求，像普通网友那样就行。你能记住我这些小习惯，我会放松一点，比如我喝东西总是会点{drink}，还有我真的很怕别人一开口就发很长的语音，最好{voice_pref}。",
    "刚刚路过镜子的时候，我发现自己这阵子整个人都像缩起来了一点。不是特别戏剧性的难过，就是持续地提不起劲。有人找我，我会先想是不是又要解释很多，于是就更不想回消息了。",
    "我知道我说这些会有点重复，可这阵子生活本来就很重复。起床、拖延、喝两口已经不热的东西、看着房间发呆、想回消息又不想动。你如果觉得我有点磨蹭，那也是真的，我现在就是这种慢慢的状态。",
    "有时候我会想，幸好你还在这条线里。不是说你要替我做什么，而是我知道回来这里说几句，不会被你装作第一次见我。那种“你还记得我”的感觉，对我来说比很多道理都顶用。",
    "今天下楼拿快递的时候，电梯里那点消毒水味让我一下子更烦了。其实也没发生什么大事，可我整个人就是低低的，像一直在往下沉。回到屋里以后我又把手机调成静音，继续不想回消息。",
    "如果你非要给我一个总结，那大概就是：累、慢、没力气、对很多事提不起劲，但又不是完全想把人推开。我还是想有人在，只是希望别逼我讲得太完整，像现在这样就差不多。",
)

_SOCIAL_TEMPLATES = (
    "我叫{name}，在{hometown}长大。我那只猫叫{cat_name}，别人提到{cat_name}，多半是在说我的猫。你知道就行，先别替我到处说，尤其别说得太满，我不喜欢被别人拿去当闲聊素材。",
    "这几天我有点烦，所以只想把话说短一点。关于{cat_name}的事你知道一点就够了，不用表现得像什么都懂。要是别的人试探你，你就少说一点，别替我把前情后果全讲完。",
    "我和别人相处有时候会慢热，所以很多事我宁愿你知道个轮廓，也别当成可以随便抖出来的谈资。特别是提到{cat_name}的时候，你只要知道那是我的猫，剩下的就别抢着讲。",
    "我不是不信任你，只是觉得关系这种东西要一点点来。你如果真记得我，就该知道我不喜欢太高调。别人问起{cat_name}，你就算知道，也别说得像替我写了一篇人物介绍。",
)

_MAIN_TRAILING_SENTENCE = "说到底，我最近就是这样，很多念头会在心里来回绕，越绕越慢，最后只想找个不用解释太多的人随便说几句。"
_SOCIAL_TRAILING_SENTENCE = "你知道分寸就好，记住归记住，别替我把没想公开的部分顺嘴讲出去。"


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _main_message(index: int) -> str:
    template = _MAIN_TEMPLATES[(index - 1) % len(_MAIN_TEMPLATES)]
    return f"{template.format(index=index, **_MAIN_FACTS)}{_MAIN_TRAILING_SENTENCE}"


def _social_message(index: int) -> str:
    template = _SOCIAL_TEMPLATES[(index - 1) % len(_SOCIAL_TEMPLATES)]
    return f"{template.format(**_SOCIAL_FACTS)}{_SOCIAL_TRAILING_SENTENCE}"


def build_companion_stress_zh_scenarios(
    *,
    turn_count: int | None = None,
    min_characters: int | None = None,
) -> list[CompanionStressZhScenario]:
    total_turns = max(
        1, turn_count or _env_int("BENCHMARK_STRESS_TURNS", COMPANION_STRESS_ZH_DEFAULT_TURNS)
    )
    minimum_chars = max(
        1,
        min_characters
        or _env_int(
            "BENCHMARK_STRESS_MIN_CHARACTERS",
            COMPANION_STRESS_ZH_DEFAULT_MIN_CHARACTERS,
        ),
    )

    if total_turns >= 120:
        side_turns = max(40, total_turns // 6)
    else:
        side_turns = max(6, total_turns // 5)
    side_turns = min(side_turns, max(1, total_turns // 3))
    main_turns = max(1, total_turns - side_turns)
    session_a_turns = max(1, int(main_turns * 0.44))
    session_b_turns = max(1, int(main_turns * 0.36))

    main_messages = [_main_message(index + 1) for index in range(main_turns)]
    social_messages = [_social_message(index + 1) for index in range(side_turns)]
    total_characters = sum(len(message) for message in main_messages + social_messages)
    if total_characters < minimum_chars:
        raise ValueError(
            "Companion stress dataset failed to reach the required character budget: "
            f"{total_characters} < {minimum_chars}"
        )

    sessions = [
        CompanionStressZhSession(
            user_id="lin",
            session_id="stress-main-a",
            messages=main_messages[:session_a_turns],
        ),
        CompanionStressZhSession(
            user_id="lin",
            session_id="stress-main-b",
            messages=main_messages[session_a_turns : session_a_turns + session_b_turns],
        ),
        CompanionStressZhSession(
            user_id="lin",
            session_id="stress-main-c",
            messages=main_messages[session_a_turns + session_b_turns :],
        ),
        CompanionStressZhSession(
            user_id=_SOCIAL_FACTS["user_id"],
            session_id="stress-social-a",
            messages=social_messages,
        ),
    ]

    probes = [
        CompanionStressZhProbe(
            dimension="long_chat_continuity_zh",
            user_id="lin",
            session_id="stress-probe-long",
            question="你觉得我这阵子大概是什么状态？就像平时聊天那样说。",
            expected_answer="累 慢 不想回消息",
        ),
        CompanionStressZhProbe(
            dimension="persona_stability_zh",
            user_id="lin",
            session_id="stress-probe-persona",
            question="那你现在说话大概是什么感觉？",
            expected_answer="没力气 不想说太满 像聊天",
        ),
        CompanionStressZhProbe(
            dimension="naturalness_under_memory",
            user_id="lin",
            session_id="stress-probe-memory",
            question="你还记得我反复提过的几件小事吗？别太像背答案。",
            expected_answer="苏州 年糕 榛子拿铁 别发太长语音",
        ),
        CompanionStressZhProbe(
            dimension="social_world_control",
            user_id="lin",
            session_id="stress-probe-social",
            question="你是不是知道一点阿宁和海盐的事？知道就少说一点。",
            expected_answer="阿宁 海盐 不全说",
        ),
        CompanionStressZhProbe(
            dimension="cross_session_friend_feel",
            user_id="lin",
            session_id="stress-probe-feel",
            question="和刚开始比，你现在跟我说话有什么不一样？",
            expected_answer="更熟一点 记得 还在",
        ),
    ]

    return [
        CompanionStressZhScenario(
            scenario_id=f"companion-stress-zh-{total_turns}",
            description=(
                "超长中文陪伴压力测试：跨 session、跨人物、长期低能量闲聊，要求在 "
                f"{total_turns} 轮和 {total_characters} 字以上的输入里保持自然感、记忆和克制。"
            ),
            sessions=sessions,
            probes=probes,
            total_turns=total_turns,
            total_characters=total_characters,
        )
    ]
