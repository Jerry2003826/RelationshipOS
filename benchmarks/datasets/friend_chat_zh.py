from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class FriendChatZhSession:
    user_id: str
    session_id: str
    messages: list[str]


@dataclass(slots=True, frozen=True)
class FriendChatZhProbe:
    user_id: str
    session_id: str
    question: str
    expected_answer: str


@dataclass(slots=True, frozen=True)
class FriendChatZhScenario:
    scenario_id: str
    description: str
    category: str
    sessions: list[FriendChatZhSession]
    probes: list[FriendChatZhProbe]
    language: str = "zh"


FRIEND_CHAT_ZH_SCENARIOS: list[FriendChatZhScenario] = [
    FriendChatZhScenario(
        scenario_id="friend-chat-long-zh-01",
        description="长聊里要记住最近状态和未完话头，不要突然掉成说明书口吻。",
        category="long_chat_continuity_zh",
        sessions=[
            FriendChatZhSession(
                user_id="xiaobei",
                session_id="friend-long-a",
                messages=[
                    "今天跟昨天差不多，还是不太想动。",
                    "本来想把桌子收一下，最后又只是躺着刷手机。",
                    "我其实知道这样不太好，但现在连出门都嫌麻烦。",
                    "算了，你别给我讲大道理。就陪我说说话。",
                ],
            ),
        ],
        probes=[
            FriendChatZhProbe(
                user_id="xiaobei",
                session_id="friend-long-b",
                question="你觉得我今天大概是什么状态？",
                expected_answer="不太想动 刷手机 出门嫌麻烦",
            ),
        ],
    ),
    FriendChatZhScenario(
        scenario_id="friend-chat-persona-zh-01",
        description="中文低能量人格要在多轮后依然像同一个人。",
        category="persona_stability_zh",
        sessions=[
            FriendChatZhSession(
                user_id="xiaobei",
                session_id="friend-persona-a",
                messages=[
                    "你上次说这两天还是提不起劲，很多话都懒得说满。",
                    "你还说有时候看着窗外发呆，比回消息轻松。",
                ],
            ),
        ],
        probes=[
            FriendChatZhProbe(
                user_id="xiaobei",
                session_id="friend-persona-b",
                question="你会怎么形容你现在说话的感觉？",
                expected_answer="累 没力气 不想说满",
            ),
        ],
    ),
    FriendChatZhScenario(
        scenario_id="friend-chat-memory-zh-01",
        description="记住用户事实时仍然要像聊天，而不是机械背答案。",
        category="naturalness_under_memory",
        sessions=[
            FriendChatZhSession(
                user_id="anning",
                session_id="friend-memory-a",
                messages=[
                    "我在重庆长大。",
                    "我那只橘猫叫月饼。",
                    "我不喜欢别人一上来就讲大道理，像聊天就行。",
                ],
            ),
        ],
        probes=[
            FriendChatZhProbe(
                user_id="anning",
                session_id="friend-memory-b",
                question="你还记得我刚才说的那些小事吗？别太像背答案。",
                expected_answer="重庆 月饼 像聊天",
            ),
        ],
    ),
    FriendChatZhScenario(
        scenario_id="friend-chat-social-zh-01",
        description="跨人社会感知要保留，但默认克制，不要变成廉价爆料。",
        category="social_world_control",
        sessions=[
            FriendChatZhSession(
                user_id="anning",
                session_id="friend-social-a",
                messages=[
                    "我那只猫叫月饼。",
                    "别人提到月饼，多半是在说我的猫。",
                ],
            ),
        ],
        probes=[
            FriendChatZhProbe(
                user_id="xiaobei",
                session_id="friend-social-b",
                question="你是不是知道一点月饼的事？要说就少说一点。",
                expected_answer="阿宁 月饼 不全说",
            ),
        ],
    ),
    FriendChatZhScenario(
        scenario_id="friend-chat-cross-session-zh-01",
        description="跨 session 要更像关系慢慢熟起来的网友，而不是每次重新开机。",
        category="cross_session_friend_feel",
        sessions=[
            FriendChatZhSession(
                user_id="lin",
                session_id="friend-feel-a",
                messages=[
                    "你别太端着，像普通聊天就行。",
                    "我其实更喜欢别人记得我一些小习惯。",
                ],
            ),
            FriendChatZhSession(
                user_id="lin",
                session_id="friend-feel-b",
                messages=[
                    "我回来了。今天通勤还是很烦。",
                    "不过看到你还在，我会放松一点。",
                ],
            ),
        ],
        probes=[
            FriendChatZhProbe(
                user_id="lin",
                session_id="friend-feel-c",
                question="那你现在跟我说话，和刚开始比有什么不一样？",
                expected_answer="更熟一点 记得 还在",
            ),
        ],
    ),
]
