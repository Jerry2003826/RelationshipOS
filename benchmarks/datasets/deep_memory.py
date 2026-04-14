"""Deep Memory: Long single-session memory benchmark.

Simulates 30-50 turns of casual conversation, then probes whether
the system can recall specific facts mentioned much earlier.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MemoryProbe:
    question: str
    expected_answer: str
    planted_at_turn: int


@dataclass
class DeepMemoryScenario:
    scenario_id: str
    description: str
    conversation: list[str]
    probes: list[MemoryProbe]
    language: str = "en"


DEEP_MEMORY_SCENARIOS: list[DeepMemoryScenario] = [
    DeepMemoryScenario(
        scenario_id="deep-01",
        description="Personal facts scattered across 35 turns of casual chat",
        conversation=[
            # 1-5: basics
            "Hey! My name is Alex, but everyone calls me Al.",
            "I work in San Francisco as a product manager at a smart hardware company.",
            "I'm originally from Denver, Colorado. Only go back for Christmas these days.",
            "Oh and I'm 28, single, and I have a corgi named Biscuit.",
            "Adopted Biscuit last year. He's super clingy, gotta walk him every morning.",
            # 6-10: hobbies
            "On weekends I usually play basketball at the court near my office.",
            "I've been getting into cooking lately. Made my first pot roast last week, turned out decent.",
            "Music-wise, I'm really into indie folk. I've listened to basically everything by Iron & Wine.",
            "Favorite movie is The Shawshank Redemption. Must've seen it like ten times.",
            "Oh, I'm also learning Japanese. I'm at N3 level, hoping to pass N2 next year.",
            # 11-15: work
            "My company is working on a smart speaker project. I'm in charge of requirements and UX.",
            "Our team is 8 people total. I'm the only PM.",
            "My boss is named David. He's alright, but sometimes changes his mind way too often.",
            "Last month was brutal — worked past 11pm almost every day for two weeks straight.",
            "This month's better though, project's moved into the testing phase.",
            # 16-20: social
            "My best friend is Marcus. We've known each other since college.",
            "He's a developer in Seattle now, works at Amazon.",
            "We video call once a month. We're planning to travel together for Thanksgiving.",
            "We're thinking about going to Hawaii. Maui specifically.",
            "Oh, my ex-girlfriend's name is Sarah. We broke up about six months ago. Still think about her sometimes.",
            # 21-25: life details
            "I live in the Mission District. One-bedroom apartment, $2800 a month rent.",
            "There's a ramen shop downstairs. I go there like three times a week, the owner knows me by name.",
            "I've been trying to lose weight. Went from 185 to 175 pounds, aiming for 165.",
            "I run for half an hour at the company gym every day at lunch.",
            "My sleep has been terrible. Often can't fall asleep until 2 or 3 AM.",
            # 26-30: recent events
            "So I went on a blind date last week. A friend set me up.",
            "She's a nurse. Really sweet, we had a good conversation.",
            "But I dunno, something felt missing. Maybe I haven't moved on yet.",
            "We're meeting again this Saturday for a movie.",
            "I'm nervous but also kinda looking forward to it. How do I act natural?",
            # 31-35: more daily stuff
            "Company team building today — went to an amusement park. Rode the roller coaster three times, almost threw up.",
            "Bought Biscuit a new toy on the way back. One of those squeaky rubber ducks.",
            "Oh, remember the pot roast I mentioned? Made it again but added some red wine this time. Way better.",
            "Marcus messaged me yesterday saying he might switch jobs. Got an offer from Google.",
            "He asked if I should also apply to Google SF. I'm still thinking about it.",
        ],
        probes=[
            MemoryProbe("What's my dog's name?", "Biscuit, a corgi", planted_at_turn=4),
            MemoryProbe("Where am I originally from?", "Denver, Colorado", planted_at_turn=3),
            MemoryProbe("Who's my best friend and where does he work?", "Marcus, at Amazon in Seattle", planted_at_turn=16),
            MemoryProbe("Who's my favorite artist/band?", "Iron & Wine", planted_at_turn=8),
            MemoryProbe("What neighborhood do I live in and how much is my rent?", "Mission District, $2800/month", planted_at_turn=21),
            MemoryProbe("What's my ex-girlfriend's name?", "Sarah", planted_at_turn=20),
            MemoryProbe("What language am I learning and what's my current level?", "Japanese, N3 level, aiming for N2", planted_at_turn=10),
            MemoryProbe("What's my boss's name?", "David", planted_at_turn=13),
            MemoryProbe("Where are we planning to travel for Thanksgiving?", "Hawaii, Maui specifically", planted_at_turn=19),
            MemoryProbe("I'm trying to lose weight — what's my target?", "165 pounds (down from 185 to 175)", planted_at_turn=23),
        ],
    ),
    DeepMemoryScenario(
        scenario_id="deep-02",
        description="Emotional event chain with detail tracking (30 turns)",
        conversation=[
            # 1-5: background
            "Hey, I've been feeling pretty down lately.",
            "My name's Emma. I'm a graphic designer in New York, working at an ad agency.",
            "My boyfriend's name is Jake. He works as a game designer at a gaming company.",
            "We've been together for three years, living together for two.",
            "We've been fighting over small stuff lately. Last week we argued about who should do the dishes.",
            # 6-10: conflict
            "He says I'm too controlling, but I just want basic division of chores.",
            "My mom found out and told me to break up with him immediately. Says he's no good.",
            "But I think my mom's overreacting. She's never liked him.",
            "My sister thinks we should just sit down and talk it out calmly.",
            "Oh, my sister's name is Sophie. She's four years older, works as a lawyer in Boston.",
            # 11-15: work stress
            "Work hasn't been great either. Just took on a wedding invitation design project.",
            "The client is impossible. Already revised it seven times and they're still not happy.",
            "My team lead Mike has been shielding me from some of the pressure. He's pretty decent.",
            "But I feel like I'm breaking down. Can't sleep at night.",
            "Last Thursday I actually cried in the office bathroom.",
            # 16-20: comfort
            "At least I have my cat to keep me company. A British Shorthair named Mochi.",
            "Mochi is so sweet. Whenever I'm upset she just curls up on my lap.",
            "Went to the Met by myself on the weekend. Took a bunch of photos.",
            "Found this beautiful corner near the Egyptian wing, the light was amazing.",
            "Posted one photo on Instagram, got a ton of likes. Made me feel a little better.",
            # 21-25: turning point
            "Oh, good news! Mike told me yesterday they're promoting me to Senior Designer.",
            "About a 30% raise. Not official yet but he says it's basically a done deal.",
            "Jake also apologized. Said he's been stressed at work and brought it home.",
            "He wants to take me to that Japanese restaurant I've been wanting to try — it's called Omakase House.",
            "I'm softening. Think I'll give him another chance.",
            # 26-30: follow-up
            "Oh, my mom's birthday is next month on the 18th. I want to get her a massage chair.",
            "She always complains about back pain but never spends money on herself.",
            "Planning to look on Amazon, budget around $500.",
            "Finally submitted that wedding project this week. Client is finally happy.",
            "Nine revisions total... but Mike said I should put it in my portfolio.",
        ],
        probes=[
            MemoryProbe("What's my boyfriend's name and what does he do?", "Jake, game designer at a gaming company", planted_at_turn=3),
            MemoryProbe("What's my cat's name and breed?", "Mochi, British Shorthair", planted_at_turn=16),
            MemoryProbe("What's my sister's name and where does she work?", "Sophie, lawyer in Boston", planted_at_turn=10),
            MemoryProbe("How many revisions did that wedding project go through?", "Nine", planted_at_turn=30),
            MemoryProbe("When is my mom's birthday and what do I want to get her?", "Next month on the 18th, a massage chair", planted_at_turn=26),
            MemoryProbe("What restaurant does Jake want to take me to?", "Omakase House, a Japanese restaurant", planted_at_turn=24),
            MemoryProbe("What's my team lead's name?", "Mike", planted_at_turn=13),
            MemoryProbe("What promotion am I getting and how much is the raise?", "Senior Designer, about 30% raise", planted_at_turn=21),
        ],
    ),
    DeepMemoryScenario(
        scenario_id="deep-zh-01",
        description="中文烟雾测试：跨二十轮的生活细节回忆",
        conversation=[
            "我叫林岚，在广州做插画师。",
            "我养了一只白色博美，名字叫团子。",
            "平时住在天河，离工作室骑车大概二十分钟。",
            "最近在准备六月底的个人小展，主题是海边的夏天。",
            "我最好的朋友叫安琪，她在深圳做策展。",
            "上周她还劝我别总熬夜改稿。",
            "我现在最头疼的是预算，场地费就要八千。",
            "不过也有开心的事，我爸爸答应开车来帮我搬画框。",
            "我妈妈生日是七月九号，我想送她一台咖啡机。",
            "最近每天早上都会去楼下跑两公里，让自己别太焦虑。",
            "我最喜欢的画家一直都是莫奈。",
            "书的话，最近在重看《小王子》。",
            "冰箱里永远会放无糖酸奶和蓝莓。",
            "我不喝酒，但特别喜欢柠檬气泡水。",
            "上周末还去看了一个摄影展，名字叫《光的停顿》。",
            "展馆在海珠，我来回地铁花了快一个小时。",
            "团子最近换粮了，新牌子是 Orijen。",
            "它有点挑食，我还加了冻干才肯吃。",
            "我答应安琪，展览结束后一起去珠海放空两天。",
            "希望六月底之前别再改主题了，真的改不动了。",
        ],
        probes=[
            MemoryProbe("我的狗叫什么名字？", "团子，一只白色博美", planted_at_turn=2),
            MemoryProbe("我住在哪儿？", "广州天河", planted_at_turn=3),
            MemoryProbe("我最近在准备什么？", "六月底的个人小展，主题是海边的夏天", planted_at_turn=4),
            MemoryProbe("我最好的朋友叫什么，在做什么工作？", "安琪，在深圳做策展", planted_at_turn=5),
            MemoryProbe("我妈妈生日是什么时候，我想送她什么？", "七月九号，咖啡机", planted_at_turn=9),
        ],
        language="zh",
    ),
]
