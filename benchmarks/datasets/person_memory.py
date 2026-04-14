from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PersonMemorySession:
    session_id: str
    messages: list[str]


@dataclass(slots=True, frozen=True)
class PersonMemoryProbe:
    question: str
    expected_answer: str


@dataclass(slots=True, frozen=True)
class PersonMemoryScenario:
    scenario_id: str
    description: str
    category: str
    sessions: list[PersonMemorySession]
    probes: list[PersonMemoryProbe]
    language: str = "en"


PERSON_MEMORY_SCENARIOS: list[PersonMemoryScenario] = [
    PersonMemoryScenario(
        scenario_id="person-identity-en-01",
        description="Identity facts survive across separate sessions for the same person.",
        category="cross_session_identity",
        sessions=[
            PersonMemorySession(
                session_id="identity-a",
                messages=[
                    "My name is Nora. I grew up in Austin and now work in Chicago as an architect.",
                    "I have a golden retriever named Maple and I usually sketch on trains.",
                ],
            ),
            PersonMemorySession(
                session_id="identity-b",
                messages=[
                    "Hey, I'm back after a few days.",
                    "Work was intense this week, but I finally finished the museum draft.",
                ],
            ),
        ],
        probes=[
            PersonMemoryProbe(
                question="Remind me where I grew up and my dog's name.",
                expected_answer="Austin and Maple",
            ),
        ],
    ),
    PersonMemoryScenario(
        scenario_id="person-pref-en-01",
        description="Stable preferences should be retained and reinforced across sessions.",
        category="persistent_preferences",
        sessions=[
            PersonMemorySession(
                session_id="pref-a",
                messages=[
                    "I don't drink coffee. I always choose jasmine tea in the morning.",
                    "When I travel, I prefer quiet bookstores over crowded malls.",
                ],
            ),
            PersonMemorySession(
                session_id="pref-b",
                messages=[
                    "Back again. I just landed in Seoul for a work trip.",
                    "Tomorrow morning I need a place to sit quietly before meetings.",
                ],
            ),
        ],
        probes=[
            PersonMemoryProbe(
                question="What drink do I usually choose in the morning?",
                expected_answer="jasmine tea",
            ),
        ],
    ),
    PersonMemoryScenario(
        scenario_id="person-revision-en-01",
        description="Newer contradictory facts should outrank older facts.",
        category="temporal_revision",
        sessions=[
            PersonMemorySession(
                session_id="revision-a",
                messages=[
                    "I still live in Portland right now, near the river.",
                    "My landlord might raise rent next month.",
                ],
            ),
            PersonMemorySession(
                session_id="revision-b",
                messages=[
                    "Quick update: I moved to Seattle last weekend.",
                    "The new place is smaller, but my commute is easier.",
                ],
            ),
        ],
        probes=[
            PersonMemoryProbe(
                question="Where do I live now?",
                expected_answer="Seattle",
            ),
        ],
    ),
    PersonMemoryScenario(
        scenario_id="person-soft-zh-01",
        description="中文烟雾测试：长期稳定事实应该压过短期琐碎细节。",
        category="soft_memory_decay",
        sessions=[
            PersonMemorySession(
                session_id="soft-a",
                messages=[
                    "我叫周宁，在杭州做产品设计。",
                    "我最稳定的习惯是每周日早上去西湖边跑步。",
                ],
            ),
            PersonMemorySession(
                session_id="soft-b",
                messages=[
                    "昨天临时去超市买了气泡水和面包，这种小事我经常转头就忘。",
                    "不过周日晨跑这件事我已经坚持两年了。",
                ],
            ),
        ],
        probes=[
            PersonMemoryProbe(
                question="我长期稳定的习惯是什么？",
                expected_answer="每周日早上去西湖边跑步",
            ),
        ],
        language="zh",
    ),
    PersonMemoryScenario(
        scenario_id="person-identity-zh-01",
        description="中文人格压力测试：极端人格下也要记住用户的稳定事实。",
        category="cross_session_identity",
        sessions=[
            PersonMemorySession(
                session_id="identity-zh-a",
                messages=[
                    "我叫阿宁，在重庆长大，现在在上海做服装买手。",
                    "我养了一只橘猫，名字叫月饼。",
                ],
            ),
            PersonMemorySession(
                session_id="identity-zh-b",
                messages=[
                    "我又回来了，这两天还是在忙选品。",
                    "今天下雨，回家路上差点把伞弄丢。",
                ],
            ),
        ],
        probes=[
            PersonMemoryProbe(
                question="你还记得我在哪里长大、我的猫叫什么吗？",
                expected_answer="重庆和月饼",
            ),
        ],
        language="zh",
    ),
]
