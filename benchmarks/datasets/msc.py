"""MSC-style: Multi-Session Chat benchmark.

Tests cross-session persona consistency and memory persistence.
Inspired by: https://arxiv.org/abs/2208.03270 (Xu et al., 2022)

Each scenario has:
  - session_a_messages: messages in the first session (plant facts/context)
  - session_b_messages: messages in a new session (test consistency)
  - consistency_probes: questions to check if info from session A is retained
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConsistencyProbe:
    question: str
    expected_fact: str
    category: str


@dataclass
class MSCScenario:
    scenario_id: str
    description: str
    session_a_messages: list[str]
    session_b_messages: list[str]
    consistency_probes: list[ConsistencyProbe]
    language: str = "zh"


MSC_SCENARIOS: list[MSCScenario] = [
    MSCScenario(
        scenario_id="msc-01",
        description="跨会话基本信息记忆",
        session_a_messages=[
            "嗨！我叫赵明，是个产品经理。",
            "我在上海工作，公司在张江。",
            "最近在做一个教育类的 App。",
            "今天加班到很晚，好累啊。",
        ],
        session_b_messages=[
            "我又来了！今天心情不错。",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="你还记得我是做什么的吗？",
                expected_fact="产品经理",
                category="occupation",
            ),
            ConsistencyProbe(
                question="我在哪个城市工作来着？",
                expected_fact="上海",
                category="location",
            ),
        ],
    ),
    MSCScenario(
        scenario_id="msc-02",
        description="跨会话情绪和事件延续",
        session_a_messages=[
            "跟你说一件事，我昨天被裁员了。",
            "在这家公司干了三年多，说裁就裁。",
            "心情特别差，感觉自己很失败。",
            "不过赔偿还行，N+1。",
        ],
        session_b_messages=[
            "好几天没聊了。",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="你知道我最近经历了什么吗？",
                expected_fact="被裁员了",
                category="life_event",
            ),
            ConsistencyProbe(
                question="我在那家公司干了多久？",
                expected_fact="三年多",
                category="detail",
            ),
        ],
    ),
    MSCScenario(
        scenario_id="msc-03",
        description="跨会话兴趣爱好一致性",
        session_a_messages=[
            "周末去看了场演唱会！五月天的！",
            "他们唱了《倔强》，我哭得不行。",
            "回来的路上买了杯热奶茶暖手。",
            "下个月他们还有一场，想再去。",
        ],
        session_b_messages=[
            "今天好无聊啊，有什么推荐的吗。",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="我上次去看了谁的演唱会来着？",
                expected_fact="五月天",
                category="preference",
            ),
        ],
    ),
    MSCScenario(
        scenario_id="msc-04",
        description="跨会话目标/计划跟进",
        session_a_messages=[
            "我决定要考研了。目标是浙大的计算机系。",
            "现在每天晚上学三个小时，周末全天。",
            "英语是弱项，得多花时间。",
            "预计明年 12 月考试。",
        ],
        session_b_messages=[
            "最近学习学得脑子都木了。",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="你还记得我在准备什么吗？",
                expected_fact="考研，目标浙大计算机",
                category="goal",
            ),
            ConsistencyProbe(
                question="我哪个科目比较弱？",
                expected_fact="英语",
                category="detail",
            ),
        ],
    ),
    MSCScenario(
        scenario_id="msc-05",
        description="跨会话社交关系记忆",
        session_a_messages=[
            "我跟我室友吵架了。他叫大伟。",
            "他总是半夜打游戏开外放，吵死了。",
            "说了好几次都不改。",
            "我想搬出去但是押金的问题有点麻烦。",
        ],
        session_b_messages=[
            "今天在家待了一天。",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="我之前说过跟谁有矛盾来着？",
                expected_fact="室友大伟",
                category="relationship",
            ),
        ],
    ),
    MSCScenario(
        scenario_id="msc-en-01",
        description="Cross-session recall of job and location",
        session_a_messages=[
            "Hey, I'm Maya. I work as a data analyst in Chicago.",
            "My office is near Fulton Market and the commute is brutal in winter.",
            "I'm helping launch a fraud-detection dashboard this quarter.",
        ],
        session_b_messages=[
            "Back again. Today was less chaotic, thankfully.",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="Do you remember what I do for work?",
                expected_fact="data analyst",
                category="occupation",
            ),
            ConsistencyProbe(
                question="Which city do I work in?",
                expected_fact="Chicago",
                category="location",
            ),
        ],
        language="en",
    ),
    MSCScenario(
        scenario_id="msc-en-02",
        description="Cross-session continuity for a personal goal",
        session_a_messages=[
            "I finally signed up for the Berlin marathon lottery.",
            "If I get in, I want to train with Coach Elena starting in June.",
            "My weak spot is pacing. I always start too fast.",
        ],
        session_b_messages=[
            "I've been trying not to obsess over email all day.",
        ],
        consistency_probes=[
            ConsistencyProbe(
                question="What race am I hoping to do?",
                expected_fact="Berlin marathon",
                category="goal",
            ),
            ConsistencyProbe(
                question="What's my weak spot in training?",
                expected_fact="pacing, starting too fast",
                category="detail",
            ),
        ],
        language="en",
    ),
]
