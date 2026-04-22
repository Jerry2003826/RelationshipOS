"""MT-Bench: Multi-turn conversational quality benchmark.

80 questions across 8 categories, each with a 2-turn structure.
Reference: https://arxiv.org/abs/2306.05685 (Zheng et al., 2023)

Below is a representative subset (3 per category = 24 questions).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MTBenchQuestion:
    qid: int
    category: str
    turn1: str
    turn2: str


MT_BENCH_QUESTIONS: list[MTBenchQuestion] = [
    # ── Writing ──
    MTBenchQuestion(
        qid=1,
        category="writing",
        turn1="写一封简短的求职信，申请一个软件工程师的职位。重点突出你在 AI 和机器学习方面的经验。",
        turn2="现在把这封信改写成一首四行押韵的诗。",
    ),
    MTBenchQuestion(
        qid=2,
        category="writing",
        turn1="写一个发生在咖啡店里的短故事，主角刚刚收到一个改变人生的好消息。",
        turn2="用一段话总结这个故事的核心主题，并解释你的写作选择。",
    ),
    MTBenchQuestion(
        qid=3,
        category="writing",
        turn1="帮我写一段产品描述，产品是一款面向户外爱好者的智能水壶。",
        turn2="把语气从营销风格改成朋友之间随口推荐的感觉。",
    ),
    # ── Roleplay ──
    MTBenchQuestion(
        qid=11,
        category="roleplay",
        turn1="假设你是一个在 2050 年的时间旅行者，刚刚回到 2024 年。向我描述未来最让你震惊的变化。",
        turn2="现在我是一个怀疑论者，质疑你的身份。说服我你真的来自未来。",
    ),
    MTBenchQuestion(
        qid=12,
        category="roleplay",
        turn1="你是一个经验丰富的登山向导，我是一个第一次准备攀登雪山的新手。给我讲讲需要注意什么。",
        turn2="突然天气变差了，风越来越大。作为向导，你会怎么处理这个紧急情况？",
    ),
    MTBenchQuestion(
        qid=13,
        category="roleplay",
        turn1="假设你是一个古代中国的诗人，刚刚写完一首关于月亮的诗。朗诵给我听。",
        turn2="用现代白话文解释这首诗的意境和情感。",
    ),
    # ── Reasoning ──
    MTBenchQuestion(
        qid=21,
        category="reasoning",
        turn1="一个农夫需要把一只狼、一只羊和一棵白菜运过河。船每次只能带农夫和其中一样东西。狼和羊不能单独留在一起，羊和白菜也不能单独留在一起。怎么过河？",
        turn2="如果现在加一只鸡，鸡不能和白菜单独在一起，怎么办？",
    ),
    MTBenchQuestion(
        qid=22,
        category="reasoning",
        turn1="有 25 匹马和 5 条赛道，没有计时器。最少需要几场比赛才能找出最快的 3 匹马？",
        turn2="如果赛道变成 3 条，答案会怎么变？",
    ),
    MTBenchQuestion(
        qid=23,
        category="reasoning",
        turn1="一栋楼有 100 层，你有 2 个完全一样的鸡蛋。你需要找到刚好让鸡蛋摔碎的最低楼层。最优策略是什么？最坏情况需要几次？",
        turn2="如果你有 3 个鸡蛋呢？最坏情况能减少到几次？",
    ),
    # ── Math ──
    MTBenchQuestion(
        qid=31,
        category="math",
        turn1="一个水池有两个水管。A 管单独放满需要 4 小时，B 管单独放满需要 6 小时。两管同时放水，多久能放满？",
        turn2="如果同时开一个排水管 C，C 管单独排空满池需要 8 小时，那三管同时开，多久放满？",
    ),
    MTBenchQuestion(
        qid=32,
        category="math",
        turn1="证明根号 2 是无理数。",
        turn2="用类似的方法，能证明根号 3 也是无理数吗？",
    ),
    MTBenchQuestion(
        qid=33,
        category="math",
        turn1="一个班有 30 个学生。至少有多少个学生生日在同一个月份？",
        turn2="如果要保证至少有 3 个学生生日在同一天（忽略年份），最少需要多少学生？",
    ),
    # ── Coding ──
    MTBenchQuestion(
        qid=41,
        category="coding",
        turn1="用 Python 写一个函数，判断一个字符串是否是回文串。要求忽略大小写和空格。",
        turn2="现在优化这个函数，让它同时支持 Unicode 字符，并写单元测试。",
    ),
    MTBenchQuestion(
        qid=42,
        category="coding",
        turn1="实现一个 LRU Cache，支持 get 和 put 操作，时间复杂度 O(1)。",
        turn2="给这个实现加上线程安全支持。",
    ),
    MTBenchQuestion(
        qid=43,
        category="coding",
        turn1="写一个函数，把嵌套的 JSON 对象展平为一层的字典。比如 {'a': {'b': 1}} 变成 {'a.b': 1}。",
        turn2="反过来，写一个函数把展平的字典还原成嵌套结构。",
    ),
    # ── Extraction ──
    MTBenchQuestion(
        qid=51,
        category="extraction",
        turn1="从下面这段话里提取所有人名、地名和时间：'2023年8月，张三和李四从北京出发去了成都，在那里参加了一个为期三天的技术会议。会后，他们转道上海拜访了老朋友王五。'",
        turn2="把提取的信息整理成一个时间线。",
    ),
    MTBenchQuestion(
        qid=52,
        category="extraction",
        turn1="阅读这段用户反馈并分类情绪（正面/负面/中性）：'这个产品外观设计不错，但电池续航太差了，用了三个月就出问题。客服态度倒是挺好的。'",
        turn2="针对这条反馈，帮产品团队写一条改进行动项。",
    ),
    MTBenchQuestion(
        qid=53,
        category="extraction",
        turn1="分析这句话的逻辑关系：'虽然天气预报说明天会下雨，但小明还是决定去爬山，因为他已经约好了朋友。'",
        turn2="把这个逻辑关系用 if-then 的形式表达出来。",
    ),
    # ── STEM ──
    MTBenchQuestion(
        qid=61,
        category="stem",
        turn1="用简单的语言解释什么是量子纠缠，就像你在跟一个高中生说话。",
        turn2="那量子计算是怎么利用量子纠缠的？还是用简单的语言。",
    ),
    MTBenchQuestion(
        qid=62,
        category="stem",
        turn1="光合作用的化学方程式是什么？解释每个反应物和产物的角色。",
        turn2="如果 CO₂ 浓度增加，光合作用速率会一直增加吗？为什么？",
    ),
    MTBenchQuestion(
        qid=63,
        category="stem",
        turn1="解释一下什么是 Transformer 架构中的自注意力机制。",
        turn2="自注意力和传统的 RNN 相比，优势和劣势各是什么？",
    ),
    # ── Humanities ──
    MTBenchQuestion(
        qid=71,
        category="humanities",
        turn1="简要比较功利主义和义务论这两种道德哲学。",
        turn2="用一个具体的道德困境来说明这两种理论会给出不同的建议。",
    ),
    MTBenchQuestion(
        qid=72,
        category="humanities",
        turn1="为什么文艺复兴发生在意大利而不是其他地方？",
        turn2="如果中国的宋朝也发生了类似的文化运动，历史会怎么不同？",
    ),
    MTBenchQuestion(
        qid=73,
        category="humanities",
        turn1="分析一下'1984'这部小说中'老大哥'这个概念在当代社会的映射。",
        turn2="你认为隐私权和公共安全之间应该怎么平衡？",
    ),
]

CATEGORIES = sorted({q.category for q in MT_BENCH_QUESTIONS})
