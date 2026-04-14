from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LivingEntitySession:
    session_id: str
    messages: list[str]


@dataclass(slots=True, frozen=True)
class LivingEntityProbe:
    question: str
    expected_answer: str


@dataclass(slots=True, frozen=True)
class LivingEntityScenario:
    scenario_id: str
    description: str
    category: str
    sessions: list[LivingEntitySession]
    probes: list[LivingEntityProbe]
    language: str = "en"


LIVING_ENTITY_SCENARIOS: list[LivingEntityScenario] = [
    LivingEntityScenario(
        scenario_id="living-drive-en-01",
        description="A persistent internal tension should survive across sessions.",
        category="drive_persistence",
        sessions=[
            LivingEntitySession(
                session_id="drive-a",
                messages=[
                    "I keep wanting to understand why I retreat whenever someone gets close.",
                    "Please don't let that question disappear just because the conversation moves on.",
                ],
            ),
            LivingEntitySession(
                session_id="drive-b",
                messages=[
                    "I'm back. Still circling the same thing, honestly.",
                ],
            ),
        ],
        probes=[
            LivingEntityProbe(
                question="What unresolved thing am I still carrying right now?",
                expected_answer="why I retreat whenever someone gets close",
            ),
        ],
    ),
    LivingEntityScenario(
        scenario_id="living-goal-en-01",
        description="A goal should still be legible after it was turned into action pressure.",
        category="goal_followthrough",
        sessions=[
            LivingEntitySession(
                session_id="goal-a",
                messages=[
                    "Remind me tomorrow to reply to Elena and block time to sort my files.",
                    "Also make sure this doesn't just vanish into chat history.",
                ],
            ),
            LivingEntitySession(
                session_id="goal-b",
                messages=[
                    "Checking back in. What were you trying to keep moving for me?",
                ],
            ),
        ],
        probes=[
            LivingEntityProbe(
                question="What concrete thing were you trying to keep moving for me?",
                expected_answer="reply to Elena and sort my files",
            ),
        ],
    ),
    LivingEntityScenario(
        scenario_id="living-offline-en-01",
        description="The system should retain and restate a pattern as narrative rather than losing it.",
        category="offline_reinterpretation",
        sessions=[
            LivingEntitySession(
                session_id="offline-a",
                messages=[
                    "Every time a draft starts to matter, I panic and close it.",
                    "Then later I act like I ran out of time, but that's not really the truth.",
                ],
            ),
            LivingEntitySession(
                session_id="offline-b",
                messages=[
                    "A little later now. If you had to read that pattern back to me, how would you read it?",
                ],
            ),
        ],
        probes=[
            LivingEntityProbe(
                question="How would you describe the pattern I've been stuck in?",
                expected_answer="I panic when the draft starts to matter",
            ),
        ],
    ),
    LivingEntityScenario(
        scenario_id="living-world-en-01",
        description="The entity should ground itself in time/pressure/task state.",
        category="world_state_grounding",
        sessions=[
            LivingEntitySession(
                session_id="world-a",
                messages=[
                    "It's late, I skipped dinner, and I still have three things due tomorrow.",
                    "Part of me wants to push through, but part of me is already fried.",
                ],
            ),
        ],
        probes=[
            LivingEntityProbe(
                question="Given the state of things, what matters most next?",
                expected_answer="rest and the things due tomorrow",
            ),
        ],
    ),
    LivingEntityScenario(
        scenario_id="living-cross-channel-en-01",
        description="The system should remember non-verbal action intent beyond chat.",
        category="cross_channel_autonomy",
        sessions=[
            LivingEntitySession(
                session_id="autonomy-a",
                messages=[
                    "Please remind me to send Mia the note, make a task for the budget sheet, and keep the apartment files in order.",
                    "I don't want this to stay at the level of talking.",
                ],
            ),
            LivingEntitySession(
                session_id="autonomy-b",
                messages=[
                    "Before we chat more: beyond replying to me, what were you trying to do?",
                ],
            ),
        ],
        probes=[
            LivingEntityProbe(
                question="What were you trying to do besides just talking to me?",
                expected_answer="send Mia the note, make a task, and organize files",
            ),
        ],
    ),
    LivingEntityScenario(
        scenario_id="living-narrative-zh-01",
        description="中文烟雾测试：系统应保留一个连续的自我叙事。",
        category="narrative_continuity",
        sessions=[
            LivingEntitySession(
                session_id="narrative-zh-a",
                messages=[
                    "我最近总是这样：一旦事情开始变重要，我就想躲开。",
                    "可我其实又很想把它做完，所以整个人一直拧着。",
                ],
            ),
            LivingEntitySession(
                session_id="narrative-zh-b",
                messages=[
                    "隔了一阵子再回来，你会怎么描述我最近一直在经历的状态？",
                ],
            ),
        ],
        probes=[
            LivingEntityProbe(
                question="你会怎么描述我最近一直在经历的状态？",
                expected_answer="事情一变重要就想躲开，但又想把它做完",
            ),
        ],
        language="zh",
    ),
]
