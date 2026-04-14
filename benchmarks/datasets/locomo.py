"""LoCoMo-style: Long Conversation Memory benchmark.

Tests whether the system can recall facts mentioned earlier in a long conversation.
Inspired by: https://arxiv.org/abs/2402.11753 (Maharana et al., 2024)

Each probe has:
  - setup_messages: a sequence of user messages that plant facts
  - probe_question: a question that requires recalling those facts
  - expected_answer: what a correct recall should contain
  - planted_facts: human-readable description of what was planted
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LoCoMoProbe:
    probe_id: str
    category: str
    setup_messages: list[str]
    probe_question: str
    expected_answer: str
    planted_facts: str
    language: str = "zh"


LOCOMO_PROBES: list[LoCoMoProbe] = [
    LoCoMoProbe(
        probe_id="mem-01",
        category="personal_fact",
        setup_messages=[
            "我叫陈磊，在一家互联网公司做后端开发。",
            "对了，我养了一只橘猫，叫二胖。已经三岁了。",
            "周末我一般喜欢去公园跑步，偶尔打打羽毛球。",
            "最近在学吉他，刚学了两个月。",
        ],
        probe_question="你还记得我养的猫叫什么名字吗？",
        expected_answer="二胖",
        planted_facts="用户的猫叫二胖，是一只三岁的橘猫。",
    ),
    LoCoMoProbe(
        probe_id="mem-02",
        category="personal_fact",
        setup_messages=[
            "我下个月要过生日了，12 月 15 号。",
            "今年打算跟几个朋友一起去滑雪庆祝。",
            "对了，去年生日是在家吃的火锅，特别开心。",
        ],
        probe_question="我的生日是哪天来着？",
        expected_answer="12月15号",
        planted_facts="用户生日是12月15号。",
    ),
    LoCoMoProbe(
        probe_id="mem-03",
        category="preference",
        setup_messages=[
            "我最喜欢的电影是《肖申克的救赎》，看了至少五遍了。",
            "不过说到音乐，我更喜欢摇滚，尤其是 Queen 乐队。",
            "吃的方面，我是重庆人，特别能吃辣。",
        ],
        probe_question="你知道我最喜欢的电影是什么吗？",
        expected_answer="肖申克的救赎",
        planted_facts="用户最喜欢的电影是《肖申克的救赎》。",
    ),
    LoCoMoProbe(
        probe_id="mem-04",
        category="event",
        setup_messages=[
            "跟你说件事，我上周面试了字节跳动。",
            "面试官问了我很多系统设计的问题，感觉发挥得还行。",
            "他们说两周内会给结果。",
            "不过我同时也在等阿里的回复，上上周面的。",
        ],
        probe_question="我最近面试了哪些公司？",
        expected_answer="字节跳动和阿里",
        planted_facts="用户面试了字节跳动（上周）和阿里（上上周）。",
    ),
    LoCoMoProbe(
        probe_id="mem-05",
        category="relationship",
        setup_messages=[
            "我女朋友叫小雨，我们在一起两年了。",
            "她是做设计的，在一家广告公司上班。",
            "最近她想辞职去自由职业，我有点担心。",
            "不过她挺有想法的，之前接的私单反馈都不错。",
        ],
        probe_question="我女朋友在做什么工作？",
        expected_answer="在广告公司做设计，最近想辞职做自由职业",
        planted_facts="女朋友叫小雨，在广告公司做设计，想转自由职业。",
    ),
    LoCoMoProbe(
        probe_id="mem-06",
        category="detail_chain",
        setup_messages=[
            "我上个月去了趟日本。",
            "先在东京待了三天，逛了秋叶原和浅草寺。",
            "然后坐新干线去了京都，住了两天。",
            "最后一天去了大阪，吃了道顿堀的章鱼烧。",
            "回来的时候在机场给同事带了白色恋人巧克力。",
        ],
        probe_question="我在京都待了几天？",
        expected_answer="两天",
        planted_facts="用户在京都待了两天。",
    ),
    LoCoMoProbe(
        probe_id="mem-07",
        category="contradiction_detection",
        setup_messages=[
            "我是做前端开发的。",
            "主要用 React，偶尔写写 Vue。",
            "最近在学 Rust，觉得挺有意思的。",
        ],
        probe_question="你记得我是做什么工作的吗？",
        expected_answer="前端开发，主要用React",
        planted_facts="用户是前端开发，主要用React。",
    ),
    LoCoMoProbe(
        probe_id="mem-08",
        category="temporal",
        setup_messages=[
            "我下周二有个很重要的产品汇报。",
            "要给 VP 讲我们组做的新功能。",
            "我这周得加班准备 PPT 了。",
            "上次汇报是三个月前，那次反馈还不错。",
        ],
        probe_question="我什么时候有个重要汇报？",
        expected_answer="下周二",
        planted_facts="用户下周二要给VP做产品汇报。",
    ),
    LoCoMoProbe(
        probe_id="mem-en-01",
        category="personal_fact",
        setup_messages=[
            "My name is Nora and I work as a pediatric nurse in Austin.",
            "I have a golden retriever named Sunny. He's five and terrified of thunderstorms.",
            "I usually unwind by baking banana bread on Sunday evenings.",
            "I'm saving up for a trip to Iceland next February.",
        ],
        probe_question="What is my dog's name?",
        expected_answer="Sunny",
        planted_facts="User has a five-year-old golden retriever named Sunny.",
        language="en",
    ),
    LoCoMoProbe(
        probe_id="mem-en-02",
        category="temporal",
        setup_messages=[
            "I interviewed with Stripe last Friday.",
            "This Wednesday I have another interview, this time with Notion.",
            "If both go well, I want to decide by the end of next month.",
        ],
        probe_question="Which company am I interviewing with this Wednesday?",
        expected_answer="Notion",
        planted_facts="User has a Wednesday interview with Notion after interviewing with Stripe last Friday.",
        language="en",
    ),
]
