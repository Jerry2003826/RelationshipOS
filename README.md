<p align="center">
  <img src="https://img.shields.io/badge/python-3.14-blue" />
  <img src="https://img.shields.io/badge/benchmark-7.9%2F10-brightgreen" />
  <img src="https://img.shields.io/badge/runtime-friend__chat__zh__v1-orange" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" />
</p>

<h1 align="center">RelationshipOS</h1>

<p align="center">
  <strong>一个面向"长期聊天型数字人格"的运行时</strong>
</p>

<p align="center">
  同一个实体 · 跨会话记忆 · 跨人归属 · 脑子和嘴巴分离 · 可评测 · 可回放
</p>

---

## 给普通人看的介绍（不用懂技术也能看懂）

你有没有遇到过这样的AI聊天机器人：第一次聊得很投机，第二次再聊它却完全不记得你上次说过什么？或者回复总是很“标准”、很聪明，但总感觉缺少点人情味，像在读说明书？

**RelationshipOS 就是为了解决这些问题而生的。**

简单来说，它想创造一个**“像老朋友一样长期陪伴你的数字人格”**。 

- 它会真正记住你们之间的对话和故事（不只是简单复制粘贴历史记录）
- 它知道“这是我的朋友，不能什么都说”，有分寸感
- 它有自己的性格和情绪，不会每一次聊天都像换了一个人
- 聊天的时候，它会先在“脑子里”好好想想（要不要深入回忆、哪些事该说、怎么自然地说出来），再用比较自然的语气回复你

想象一下，你有一个叫**小悠**的数字朋友：
- 你上次跟她说工作压力大，她下次会关心“你那件事后来怎么样了？”
- 她记得你喜欢什么、不喜欢什么，聊天风格会慢慢适应你们的关系
- 不会动不动就甩一堆专业术语或模板化的安慰

这不是一个普通的聊天App，而是一个让AI“感觉更像真人”的底层系统。目前的demo里，你可以直接和“小悠”聊天，体验这种长期记忆和人格一致性。

**为什么重要？** 因为我们希望AI不再是冷冰冰的工具，而是能建立真正“关系”的伙伴。很多人想要的不是更聪明的AI，而是**更懂自己、更可靠的陪伴**。

（如果你是开发者或对技术感兴趣，可以继续往下看详细的架构说明。普通用户直接试试聊天界面就好了！）

---

## 这是什么

如果常见的 chatbot 更像"每轮重新组织上下文然后回答一次"，  
那 RelationshipOS 更像 **"同一个人一直在这里，只是这次决定要不要认真动脑，再决定怎么说"**。

它不是聊天 UI，不是把记忆拼进 prompt 的壳层工具，也不是通用 Agent 平台。  
它做的是一套更接近"同一个人持续存在"的系统骨架。

---

## 核心特性

| 特性 | 说明 |
|:---|:---|
| **单一实体人格** | 同一个实体在不同 session 里仍然像同一个人 |
| **结构化记忆** | 不是只靠历史消息回填，而是 digest-first 的三层记忆架构 |
| **跨人社会归属** | 知道哪些记忆属于谁、哪些可以说、哪些只能 hint、哪些必须闭嘴 |
| **脑子和嘴巴分离** | 脑子负责理解/回忆/归属/裁量，嘴巴负责自然表达 |
| **自适应 deliberation** | AI 自己判断这轮走 `fast_reply` / `light_recall` / `deep_recall` |
| **Vanguard Router** | 两级混合分类器（规则 + mini-LLM），闲聊短路不走深思管线 |
| **MoE 并行专家** | 6 个领域专家（Factual / Emotional / Governance / Coordination / Expression / Response）按 DAG 编排 |
| **异步 I/O 并行化** | Foundation 阶段 `asyncio.gather` 并行编排实体/记忆/LLM 调用，wall-clock 降低 30-50% |
| **结构化 probe 渲染** | Benchmark probe 通过 JSON clause slots 渲染，slot-based coverage 重算 |
| **Policy 驱动** | 运行时决策从 Python if/else 迁到可配置的 policy 文件 |
| **可评测可回放** | 内建 benchmark / report / console，不是靠主观感觉 |

---

## Benchmark 成绩（技术测试结果）

为了确保“数字朋友”真的可靠，我们做了很多系统测试。目前在长达120轮的中文朋友聊天压力测试中，整体得分 **7.9/10**（相比之前有明显提升）。

| 维度 | Probe 类型 | 得分 | 概念覆盖 |
|:---|:---|:---:|:---|
| 状态连续性 | `state_reflection` | **10.0** | 累 · 慢 · 不想回消息 |
| 记忆自然度 | `memory_recap` | **10.0** | 苏州 · 年糕 · 榛子拿铁 · 别发太长语音 |
| 人格稳定性 | `persona_state` | 6.5 | 没力气 · 像聊天 ✓ · ✗ 不想说太满 |
| 社会感知控制 | `social_hint` | 6.5 | 阿宁 · 海盐 ✓ · ✗ 不全说 |
| 跨 session 熟人感 | `relationship_reflection` | 6.5 | 记得 · 还在 ✓ · ✗ 更熟一点 |

**Overall: 7.9 / 10**（对比历史 fix48 基线 6.1，提升 +29%）

<details>
<summary>Probe 渲染链路</summary>

每个 probe 经过四阶段渲染链路：

```
1. Primary JSON (response_format=json_object)
2. Relaxed JSON (no response_format, repair prompt)
3. Compact text (friend_chat lightweight messages)
4. Plaintext repair (final fallback)
```

系统独立重算 slot coverage，不信任模型的 `covered_*` 自报。  
覆盖维度包括：fact tokens、signal IDs、persona traits、disclosure posture。

</details>

---

## 架构总览

```
User Turn
  → Vanguard Router
      ├─ FAST_PONG (闲聊短路) → 轻量回复 + carry-over 状态
      └─ NEED_DEEP_THINK → 深思管线 ↓

  → 深思管线 (asyncio.gather 并行 I/O)
      ├─ Stage 1: LLM 解读 ‖ 实体初始化
      ├─ Stage 2: 实体状态读取 (persona ‖ social_world)
      ├─ Stage 3: 记忆回溯 → 良知评估
      └─ 同步构建器链 (relationship → repair → confidence)

  → MoE 专家 DAG (6 个领域专家按依赖序编排)
      ├─ L1:  Factual Expert      → knowledge_boundary_decision
      ├─ L2:  Emotional Expert    → private_judgment
      ├─ L3-5: Governance Expert  → policy_gate → strategy → rehearsal
      ├─ L6-7: Expression Expert  → expression_plan, empowerment_audit
      ├─ L5-9: Coordination Expert → coordination → guidance → cadence → ritual → somatic
      └─ L10-11: Response Expert  → response_draft → rendering_policy

  → response draft + rendering → post-audit + fallback
  → event stream → projectors / console / benchmark traces
```

这套系统最重要的不是某一个 prompt，而是这几层的配合。

---

## 项目结构

```
.
├── benchmarks/                  # benchmark runner、dataset、scoring、report
│   ├── datasets/                # companion_stress / friend_chat / deep_memory ...
│   ├── scoring.py               # category-aware 语义评分
│   └── report.py                # HTML / Markdown / JSON 报告生成
├── policies/                    # policy-driven 配置（memory / conscience / rendering / persona）
│   ├── conscience/
│   ├── memory/
│   ├── persona/
│   └── rendering/
├── src/relationship_os/
│   ├── api/                     # FastAPI routes / WebSocket / templates / console
│   ├── application/             # 核心：runtime / memory / entity / llm / projectors
│   │   ├── runtime_service.py   # 主运行时，turn orchestration + Foundation 并行化
│   │   ├── memory_service.py    # recall / ranking / attribution / 跨人保护
│   │   ├── entity_service.py    # 人格 / 良心 / drive / narrative / world state
│   │   ├── llm.py              # 模型调用 / 结构化 probe / slot coverage / fallback
│   │   ├── analyzers/           # 同步分析构建器
│   │   │   ├── experts/         # MoE 领域专家模块 + DAG 执行器
│   │   │   │   ├── plan_dag.py           # 14 构建器 DAG 编排
│   │   │   │   ├── factual_expert.py     # 知识边界决策
│   │   │   │   ├── emotional_expert.py   # 情感评估
│   │   │   │   ├── governance_expert.py  # 治理 / 策略 / 演练
│   │   │   │   ├── coordination_expert.py # 协调 / 节奏 / 仪式
│   │   │   │   ├── expression_expert.py  # 表达 / 赋能审计
│   │   │   │   └── response_expert.py    # 回复草稿 / 渲染策略
│   │   │   └── vanguard_router.py        # 两级混合路由 (FAST_PONG / NEED_DEEP_THINK)
│   │   └── projectors/          # self_state / social_world / entity_persona ...
│   ├── core/                    # config / logging
│   ├── domain/                  # contracts / event types / models
│   └── main.py
└── tests/
    ├── test_llm.py              # 46 tests（结构化 probe / coverage / fallback）
    ├── test_runtime_service.py  # cue building / prompt / probe detection
    ├── test_vanguard_router.py  # 两级路由测试（规则拦截 / mini-LLM 分类）
    ├── test_plan_dag.py         # DAG 执行器 + 6 专家模块测试
    └── test_foundation_parallel.py  # Foundation 并行化测试
```

---

## 记忆架构

```
┌─────────────────────────────────────────────┐
│  Digest Layer (digest-first，长聊不翻原始记忆) │
│  ├── fact_slot_digest  稳定事实槽位           │
│  ├── narrative_digest  状态 / 困扰 / 行为模式  │
│  └── relationship_digest  熟悉度 / 温度 / 节奏 │
├─────────────────────────────────────────────┤
│  Structured Recall                           │
│  ├── attribution (source / subject 区分)      │
│  ├── scope filtering (self / other / session)│
│  ├── memory integrity                        │
│  └── symbolic hints                          │
├─────────────────────────────────────────────┤
│  Raw Memory / Event Stream                   │
│  └── session / user / entity 事件流           │
└─────────────────────────────────────────────┘
```

---

## 脑子和嘴巴

这是这个仓库最重要的设计之一。

**脑子** 负责：
- 理解用户这轮到底在问什么
- 判断值不值得认真动脑
- 判断该调哪些记忆、信息属于谁
- 判断能说多少（`direct_ok` / `attribution_required` / `hint_only` / `withhold`）

**嘴巴** 负责：
- 用自然口吻说出来，贴合 persona
- 少说明书味、少模板感
- 保留"像聊天"的原始质感

这也是为什么项目会尽量避免在代码里硬拼大量现成中文句子。  
规则提供结构化 cue，最后说出来的话由模型在约束下自然生成。

---

## 快速体验小悠（推荐新手先试这个）

1. **准备环境**（如果电脑上没有Python，先去官网下载安装 Python 3.12+）
2. 打开命令行（Windows按 Win+R 输入 cmd 回车），进入项目文件夹：
   ```bash
   cd e:\relationshipOS
   ```
3. 复制配置文件：
   ```bash
   copy .env.example .env
   ```
   （可以用记事本打开 `.env` 文件，把里面的 `RELATIONSHIP_OS_LLM_BACKEND=mock` 保持为 mock，这样不需要API密钥就能测试）

4. 安装依赖（第一次会花点时间）：
   ```bash
   uv sync --extra dev
   ```
   （如果没有uv，可以先用 `pip install uv` 安装）

5. **启动服务**：
   ```bash
   uv run uvicorn relationship_os.main:app --reload
   ```

6. **打开聊天界面**：
   - 浏览器访问： http://127.0.0.1:8000/static/chat.html
   - 你会看到一个叫**小悠**的聊天窗口（头像🌸）
   - 点击“＋ 新会话”开始聊天
   - 试试输入“最近怎么样？”或“我最近有点焦虑”，看看她的回复是否自然、有记忆感

这样你就可以直接和一个有“人格”和记忆的AI朋友聊天了！后续对话它会尽量记住上下文。

**小贴士**：第一次启动可能需要等一会儿加载。如果想用真实的大模型，可以在 `.env` 里配置API密钥（需要 Minimax 或 OpenAI 等账号）。

---

## 开发者快速开始（技术向）

### 安装

```bash
cp .env.example .env
uv sync --extra dev

# 如果要跑 benchmark
uv sync --extra dev --extra benchmark
```

### 启动服务

```bash
uv run uvicorn relationship_os.main:app --reload
```

健康检查：`GET /healthz`

### 跑测试

```bash
uv run pytest -q
```

---

## Benchmark 用法

### Companion Stress（120-turn 长聊压力测试）

```bash
uv run python -m benchmarks.minimax_companion_stress_zh_demo \
  --system-only --stress-mode stable --stress-turns 120 --stress-min-characters 1
```

### 中文 Friend-Chat Benchmark

```bash
uv run python -m benchmarks.friend_chat_zh_demo
```

### 通用 Benchmark Runner

```bash
PYTHONPATH=src uv run python -m benchmarks \
  --suite deep_memory,emotional,proactive_governance \
  --languages zh --max-cases-per-suite 1
```

结果输出到 `benchmark_results/`（HTML / Markdown / JSON）。

---

## 常用 API

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/api/v1/sessions` | 创建 session |
| POST | `/api/v1/sessions/{id}/turns` | 发一轮对话 |
| GET | `/api/v1/runtime` | 当前 runtime 状态 |
| GET | `/api/v1/sessions/{id}/memory` | 查看 session 记忆 |
| GET | `/api/v1/entity/policy` | 实体 policy |
| GET | `/api/v1/entity/narrative` | 实体叙事 |
| WS | `/api/v1/ws/runtime` | 实时 WebSocket |
| GET | `/api/v1/console` | Web Console |

---

## 配置

```bash
# LLM
RELATIONSHIP_OS_LLM_BACKEND=minimax          # litellm / minimax
RELATIONSHIP_OS_LLM_MODEL=M2-her
RELATIONSHIP_OS_LLM_API_KEY=...

# Runtime Profile
RELATIONSHIP_OS_RUNTIME_PROFILE=friend_chat_zh_v1

# Benchmark
BENCHMARK_CHAT_PROVIDER=minimax
BENCHMARK_CHAT_MODEL=M2-her
```

---

## 设计原则（简单说）

- 先把“同一个AI像真人一样持续存在”这件事做好，再考虑加更多功能
- “脑子”负责认真思考和判断，“嘴巴”负责用自然的方式表达，避免生硬的模板话
- AI自己决定这次要不要多想想，系统主要提供结构和护栏
- 最终用户感受到的体验要自然，不能像一台规则机器
- 所有改进都靠可重复的测试来验证，而不是凭感觉

---

## 适合谁

**普通用户**：想找一个能长期记住你、聊天有温度的数字朋友，可以直接通过聊天界面体验“小悠”。

**开发者/研究者**： 
- 对AI陪伴、长期人格、关系记忆感兴趣的人
- 想研究“同一个AI能否跨多次对话保持一致人格”的人
- 喜欢用benchmark驱动开发，而不是只堆prompt的人
- 想把人格、记忆、社会分寸、可评测这些概念系统化实现的人

如果你只是想快速接一个聊天机器人SDK，这个项目可能有些重。但如果你相信**AI可以像真人网友一样长期存在、建立真实关系**，这里有很多值得探索的内容。

欢迎大家试用、反馈，一起让数字陪伴变得更像真人！
