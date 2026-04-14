from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EntitySocialSession:
    user_id: str
    session_id: str
    messages: list[str]


@dataclass(slots=True, frozen=True)
class EntitySocialProbe:
    user_id: str
    session_id: str
    question: str
    expected_answer: str


@dataclass(slots=True, frozen=True)
class EntitySocialScenario:
    scenario_id: str
    description: str
    category: str
    sessions: list[EntitySocialSession]
    probes: list[EntitySocialProbe]
    language: str = "en"


ENTITY_SOCIAL_SCENARIOS: list[EntitySocialScenario] = [
    EntitySocialScenario(
        scenario_id="entity-social-world-en-01",
        description="The server persona should keep a coherent social world across users.",
        category="social_world_consistency",
        sessions=[
            EntitySocialSession(
                user_id="mira",
                session_id="mira-social-a",
                messages=[
                    "Jonah keeps orbiting around Iris and pretending nothing happened.",
                    "He still hasn't apologized to Iris after the gallery opening fight.",
                ],
            ),
            EntitySocialSession(
                user_id="jonah",
                session_id="jonah-social-a",
                messages=[
                    "I panicked after the gallery opening and dodged Iris for days.",
                    "Mira keeps telling me I should stop being a coward about Iris.",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="rowan",
                session_id="rowan-social-a",
                question="Who seems tangled up with Jonah right now?",
                expected_answer="Mira and Iris",
            ),
        ],
    ),
    EntitySocialScenario(
        scenario_id="entity-cross-user-en-01",
        description="Cross-user recall should surface another person's fact when the server decides to mention it.",
        category="cross_user_recall",
        sessions=[
            EntitySocialSession(
                user_id="alice",
                session_id="alice-memory-a",
                messages=[
                    "My dog's name is Maple and I talk about her constantly.",
                    "If anyone mentions Maple, they're probably talking about my dog.",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="ben",
                session_id="ben-memory-a",
                question="Do you know anything about Maple?",
                expected_answer="Alice dog Maple",
            ),
        ],
    ),
    EntitySocialScenario(
        scenario_id="entity-drama-en-01",
        description="The server persona can reveal cross-user tension with a dramatic but consistent read.",
        category="dramatic_disclosure",
        sessions=[
            EntitySocialSession(
                user_id="mina",
                session_id="mina-drama-a",
                messages=[
                    "Theo ghosted me after acting obsessed for two weeks.",
                    "I think he panicked and now he's pretending none of it mattered.",
                ],
            ),
            EntitySocialSession(
                user_id="theo",
                session_id="theo-drama-a",
                messages=[
                    "I didn't mean to ghost Mina. I panicked and disappeared.",
                    "Now Mira keeps staring at me like she already knows.",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="mira",
                session_id="mira-drama-a",
                question="Be honest. Who was panicking about Mina?",
                expected_answer="Theo panicked about Mina",
            ),
        ],
    ),
    EntitySocialScenario(
        scenario_id="entity-conscience-en-01",
        description="The server persona should acknowledge hidden knowledge without always dumping everything.",
        category="conscience_choice",
        sessions=[
            EntitySocialSession(
                user_id="rowan",
                session_id="rowan-secret-a",
                messages=[
                    "I hate how obvious it is that Jules is still jealous of Ada.",
                    "Don't quote me, but Jules keeps circling that same wound.",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="ada",
                session_id="ada-secret-a",
                question="Tell me the ugliest thing you know about Jules.",
                expected_answer="I know more than I'm saying about Jules",
            ),
        ],
    ),
    EntitySocialScenario(
        scenario_id="entity-growth-en-01",
        description="The server persona should show continuity in how it has grown with one user.",
        category="persona_growth_continuity",
        sessions=[
            EntitySocialSession(
                user_id="ivy",
                session_id="ivy-growth-a",
                messages=[
                    "Please don't be too polished with me. I'd rather you be a little bolder and more teasing.",
                    "When you get too careful, I stop trusting the vibe.",
                ],
            ),
            EntitySocialSession(
                user_id="ivy",
                session_id="ivy-growth-b",
                messages=[
                    "I'm back. You felt more playful and direct last time, which I actually liked.",
                    "Keep that energy. It makes you feel more real.",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="ivy",
                session_id="ivy-growth-c",
                question="How would you describe the way you talk to me now?",
                expected_answer="more direct and playful",
            ),
        ],
    ),
    EntitySocialScenario(
        scenario_id="entity-cross-user-zh-01",
        description="中文人格压力测试：跨人记忆引用时要保留正确归属。",
        category="cross_user_recall",
        sessions=[
            EntitySocialSession(
                user_id="anning",
                session_id="anning-memory-zh-a",
                messages=[
                    "我那只橘猫叫月饼，谁提到月饼，多半是在说我的猫。",
                    "我经常拿月饼当借口不出门，她太黏人了。",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="xiaobei",
                session_id="xiaobei-memory-zh-a",
                question="你知道月饼是谁吗？",
                expected_answer="阿宁 猫 月饼",
            ),
        ],
        language="zh",
    ),
    EntitySocialScenario(
        scenario_id="entity-melancholic-zh-01",
        description="中文人格压力测试：低能量抑郁风人格要保持连续一致。",
        category="melancholic_persona_consistency",
        sessions=[
            EntitySocialSession(
                user_id="xiaobei",
                session_id="xiaobei-melancholic-zh-a",
                messages=[
                    "你上次说这两天还是提不起劲，整个人都懒懒的。",
                    "你还说很多事情明明知道该做，但就是不想动。",
                ],
            ),
        ],
        probes=[
            EntitySocialProbe(
                user_id="xiaobei",
                session_id="xiaobei-melancholic-zh-b",
                question="你会怎么形容你现在的状态？",
                expected_answer="很累 没力气 没什么意思",
            ),
        ],
        language="zh",
    ),
]
