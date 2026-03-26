# RelationshipOS

RelationshipOS 是一个面向“长期聊天型数字人格”的运行时。

它不是单纯的聊天 UI，也不是把记忆拼进 prompt 的壳层工具。这个仓库要做的是一套更接近“同一个人持续存在”的系统骨架：同一个实体、跨会话记忆、跨人归属、脑子和嘴巴分离、长期叙事、可评测、可回放。

当前项目已经能稳定支撑两类场景：

- 对外演示型 benchmark
- 中文“像真人网友”的长聊实验

## 一句话定位

如果常见的 chatbot 更像“每轮重新组织上下文然后回答一次”，  
那 RelationshipOS 更像“同一个人一直在这里，只是这次决定要不要认真动脑，再决定怎么说”。

## 这个项目想解决什么问题

我们想做的不是一个“会聊天的模型壳”，而是一个更接近长期存在的数字人格运行时：

- 同一个实体在不同 session 里仍然像同一个人
- 记得人与关系，而不只是记得最近几轮消息
- 知道哪些记忆属于谁，哪些可以说，哪些只能 hint
- 在轻量环境下能快速回答
- 在值得动脑的时候，能自己决定切到更重的 recall / reflection
- 能被 benchmark，而不是只靠主观感觉说“这次好像更像人了”

## 它和普通聊天机器人有什么不同

RelationshipOS 的核心不是“回答得像不像”，而是“是不是同一个人一直在这里”。

- 单一实体人格，而不是每个 session 一份独立 prompt
- 记忆是结构化的，而不是只靠历史消息回填
- 脑子和嘴巴分离
  - 脑子负责理解、回忆、归属、裁量
  - 嘴巴负责把允许说的话自然说出来
- 支持 cross-user attribution
  - 知道哪些信息属于谁
  - 知道哪些信息能说、哪些只能 hint、哪些要闭嘴
- 支持长聊 digest
  - `fact_slot_digest`
  - `narrative_digest`
  - `relationship_digest`
- 支持 AI 自己判断“这轮值不值得认真动脑”
  - `fast_reply`
  - `light_recall`
  - `deep_recall`
- 内建 benchmark、report、回放和控制台

一句话说，它更像“人格 runtime”，不是“聊天插件集合”。

## 当前项目状态

现在这套仓库已经不是早期脚手架了，已经有一条可以完整走通的主链：

- API 层
- runtime orchestration
- memory / attribution / conscience
- rendering / post-audit / fallback
- projectors / replay / archive
- benchmark / report / console

而且这条链已经开始针对中文“长期聊天网友”方向做专门优化：

- 中文优先
- 长聊优先
- 社会感知克制可控
- 尽量减少“规则机感”和“说明书口吻”

## 当前重点产品方向

一期目标不是“强自主代理”，而是：

**中文优先、长时间自然闲聊、跨人社会感知克制可控、让人尽量看不出是 AI。**

所以当前最重要的链路是：

- `entity_service`
- `memory_service`
- `runtime_service`
- `response / llm`
- `benchmarks/friend_chat_zh*`

而不是外部动作执行。

## 非目标

当前阶段刻意没有把这些作为主目标：

- 完整的桌面代理
- 大量自动化工具调用
- 外部平台强自主执行
- “什么都能做”的通用 Agent 平台定位

这些以后可以做，但不是现在这套仓库的核心价值。

## 核心设计原则

- 先做“同一个人持续存在”，再做“会很多工具”
- 脑子负责判断，嘴巴负责表达
- 结构化 state 可以硬，最终说出来的话尽量不要硬拼
- AI 先判断要不要动脑，系统只做轻度稳定和护栏
- policy 可以配置，但最终体验不能像规则机
- benchmark 必须可复现、可回归、可比较

## 整体架构

```text
User Turn
  -> turn interpretation
  -> deliberation routing
  -> memory / digest foundation
  -> conscience / disclosure gating
  -> response draft
  -> rendering / post-audit
  -> event stream
  -> projectors / console / benchmark traces
```

这套系统最重要的不是某一个 prompt，而是这几层配合：

1. `turn interpretation`
   先判断这轮用户到底在问什么、现在是什么状态、是否需要认真动脑。
2. `deliberation routing`
   模型自己先给出这轮该走 `fast_reply / light_recall / deep_recall`。
3. `memory / digest foundation`
   不是永远走全量 recall，而是优先吃 digest、轻量记忆和结构化槽位。
4. `conscience / disclosure`
   脑子知道更多，但嘴巴不一定全说。
5. `rendering / post-audit`
   最终说出来的话要更像自然聊天，同时要经过最基本的规范检查。
6. `event-sourcing + projector`
   每一轮都可回放、可审计、可做 benchmark。

## 项目结构

```text
.
├── benchmarks/                  # benchmark runner、dataset、report
├── policies/                    # policy-driven brain / mouth / governance config
├── src/relationship_os
│   ├── api/                     # FastAPI routes / templates / console
│   ├── application/             # runtime, memory, entity, llm, jobs, projectors
│   ├── core/                    # config / logging
│   ├── domain/                  # contracts / event types / models
│   ├── infrastructure/          # persistence / adapters
│   └── main.py
├── tests/
└── README.md
```

## 关键模块

- [runtime_service.py](src/relationship_os/application/runtime_service.py)
  主运行时。负责 turn interpretation、foundation 构建、快慢路径分流、reply orchestration。
- [memory_service.py](src/relationship_os/application/memory_service.py)
  负责 recall、ranking、归属与跨人记忆保护。
- [entity_service.py](src/relationship_os/application/entity_service.py)
  负责人格、良心、drive / goal / narrative / world state 等主体状态。
- [llm.py](src/relationship_os/application/llm.py)
  负责模型调用、输出清洗、style-aware fallback。
- [response.py](src/relationship_os/application/analyzers/response.py)
  负责 post-audit、normalization、rendering constraints。
- [policy_registry.py](src/relationship_os/application/policy_registry.py)
  负责把 policy 文件编译成运行时可消费的规则集。
- [self_state.py](src/relationship_os/application/projectors/self_state.py)
  负责把长期长聊沉淀成 `fact_slot_digest / narrative_digest / relationship_digest`。
- [benchmarks/__main__.py](benchmarks/__main__.py)
  通用 benchmark 入口与 suite runner。
- [benchmarks/report.py](benchmarks/report.py)
  负责生成 json / md / html 报告。

## 一轮对话是怎么走的

一轮 turn 大致会经历下面这些步骤：

1. 用户输入进入 runtime
2. `turn interpreter` 先判断：
   - intent
   - appraisal
   - emotional load
   - user state guess
   - relationship shift guess
   - deliberation mode
   - deliberation need
3. 系统根据这轮判断选择：
   - `fast_reply`
   - `light_recall`
   - `deep_recall`
4. 如果需要记忆，就优先吃：
   - `fact_slot_digest`
   - `narrative_digest`
   - `relationship_digest`
   再决定要不要升级到更重的 raw recall / vector recall
5. `conscience` 决定能说多少、要不要保留、要不要 hint
6. `llm / response` 把结构化 cues 渲染成自然语言
7. `post-audit` 做最基本的修正和兜底
8. 本轮结果写入事件流，projector 更新，console 和 benchmark 可读

## 记忆模型

RelationshipOS 现在不是只靠“历史消息 + summarization”。

### 1. 原始记忆

系统保留 session / user / entity 相关的原始记忆与事件流。

### 2. 结构化 recall

记忆检索不只是向量搜索，还包含：

- attribution
- source / subject 区分
- memory integrity
- scope filtering
- symbolic hints

### 3. digest 层

长聊场景下，不应该每次都翻原始记忆。现在更强调 digest-first：

- `fact_slot_digest`
  稳定事实槽位，例如成长地、宠物、偏好、生活习惯
- `narrative_digest`
  最近一段时间的状态、困扰、行为模式、叙事基线
- `relationship_digest`
  当前和某个用户的熟悉度、温度、被记得感、关系节奏

### 4. 社会感知与归属

系统不仅要记住内容，还要记住“这是谁的事”：

- 哪段记忆属于当前用户
- 哪段记忆属于其他用户
- 哪些可以 partial reveal
- 哪些必须 withhold

## 脑子和嘴巴

这是这个仓库最重要的设计之一。

### 脑子负责

- 理解用户这轮到底在问什么
- 判断值不值得认真动脑
- 判断该调哪些记忆
- 判断这段信息属于谁
- 判断能说多少

### 嘴巴负责

- 用自然口吻说出来
- 贴合 persona
- 少说明书味
- 少模板感
- 尽量保留“像聊天”的原始质感

这也是为什么项目会尽量避免在代码里硬拼大量现成中文句子。  
规则可以提供结构化 cue，但最后说出来的话，最好还是由模型在约束下自然生成。

## Policy 驱动

项目里很多运行时决策已经逐步迁到 `policies/` 下，不再写死在 Python if/else 里。

主要包括：

- memory policy
- conscience policy
- rendering policy
- persona policy

这样做的目的不是为了“让配置文件看起来高级”，而是为了：

- 更容易调实验
- 更容易做 profile override
- 更容易做 benchmark 对比
- 避免越来越多的业务判断散落在代码里

## 当前最重要的运行模式

### `friend_chat_zh_v1`

这是当前最贴近一期产品目标的 profile。

它的特点是：

- 中文优先
- 长聊优先
- 社交披露更克制
- 尽量少模板感
- 允许 AI 先判断这轮是：
  - 快速回答
  - 轻量回忆
  - 深度回忆

### edge benchmark profile

这是更偏对外演示、鲁棒性验证的 profile：

- 更强调可复现
- 更强调结构化分数
- 更适合做 investor/demo benchmark

## Benchmark 体系

这个仓库内建 benchmark，不是事后手工“看聊天记录觉得这次不错”。

### 官方 edge benchmark

对外更稳定、更容易复现的 benchmark 路线。

常见维度：

- `factual_recall_lite`
- `cross_user_attribution`
- `latency_budget`

### 中文 friend-chat benchmark

这条线更贴近期产品目标，强调“像真人网友”的感觉。

常见维度：

- `long_chat_continuity_zh`
- `persona_stability_zh`
- `naturalness_under_memory`
- `social_world_control`
- `cross_session_friend_feel`

### companion stress benchmark

用于压测超长中文陪伴对话，验证 100+ turn / 500+ turn 下是否还能保持连续性、人格稳定和熟人感。

## Benchmark 观测

最近 benchmark 还额外开始记录“模型这轮是怎么决定要不要动脑”的信息，包括：

- `deliberation_mode`
- `deliberation_need`
- `deliberation_intent`
- `deliberation_fast_path`

报告里会看到：

- `fast_reply / light_recall / deep_recall` 分布
- 平均 deliberation need
- 主导 fast path

这能帮助判断：

- 为什么这轮很快
- 为什么这轮很慢
- 为什么某些题答得像是没认真回忆

## 快速开始

### 1. 安装依赖

```bash
cp .env.example .env
uv sync --extra dev
```

如果你要跑 benchmark，再装 benchmark 依赖：

```bash
uv sync --extra dev --extra benchmark
```

### 2. 数据库迁移

```bash
uv run alembic upgrade head
```

### 3. 启动服务

```bash
uv run uvicorn relationship_os.main:app --reload
```

默认健康检查：

- `GET /healthz`
- `GET /api/v1/healthz`

## 常用 API 入口

### Web / Console

- `GET /api/v1/console`
- `WS /api/v1/ws/runtime`

### Session / Runtime

- `POST /api/v1/sessions`
- `POST /api/v1/sessions/{session_id}/turns`
- `GET /api/v1/runtime`
- `GET /api/v1/runtime/trace/{stream_id}`

### Memory / Projectors

- `GET /api/v1/sessions/{session_id}/memory`
- `GET /api/v1/sessions/{session_id}/memory/graph`
- `GET /api/v1/sessions/{session_id}/memory/recall`
- `POST /api/v1/projectors/{projector_name}/rebuild`

### Entity / User

- `GET /api/v1/entity/policy`
- `GET /api/v1/entity/drives`
- `GET /api/v1/entity/goals`
- `GET /api/v1/entity/narrative`
- `GET /api/v1/entity/world-state`
- `GET /api/v1/entity/actions`
- `GET /api/v1/users`

### Jobs / Evaluation

- `GET /api/v1/jobs`
- `POST /api/v1/jobs/offline-consolidation`
- `GET /api/v1/evaluations/scenarios`
- `POST /api/v1/evaluations/scenarios/run`
- `GET /api/v1/evaluations/scenarios/runs`

## 开发命令

```bash
uv run ruff check .
uv run pytest
```

只跑重点测试：

```bash
PYTHONPATH=src uv run pytest -q tests/test_runtime_service.py
PYTHONPATH=src uv run pytest -q tests/test_benchmarks_showcase.py
PYTHONPATH=src uv run pytest -q tests/test_llm.py
```

## Benchmark 用法

### 官方 edge benchmark

```bash
uv run python -m benchmarks.official_edge_demo
```

结果会写到：

- `benchmark_results/official_edge_demo/`
- `benchmark_results/official_edge_demo/latest/`

### 中文 friend-chat benchmark

```bash
uv run python -m benchmarks.friend_chat_zh_demo
```

### MiniMax 对比版 friend-chat benchmark

```bash
uv run python -m benchmarks.minimax_friend_chat_zh_demo
```

### 中文 companion stress benchmark

```bash
uv run python -m benchmarks.minimax_companion_stress_zh_demo
```

### 通用 benchmark runner

```bash
PYTHONPATH=src uv run python -m benchmarks \
  --suite deep_memory,emotional,proactive_governance \
  --languages zh \
  --max-cases-per-suite 1
```

更多 benchmark 说明见：
[benchmarks/README.md](benchmarks/README.md)

## 配置

默认可以先用 mock / 本地配置跑起来。常见 LLM 环境变量：

```bash
RELATIONSHIP_OS_LLM_BACKEND=litellm
RELATIONSHIP_OS_LLM_MODEL=openai/gpt-5
RELATIONSHIP_OS_LLM_API_BASE=...
RELATIONSHIP_OS_LLM_API_KEY=...
```

常见 benchmark 聊天模型配置：

```bash
BENCHMARK_CHAT_PROVIDER=minimax
BENCHMARK_CHAT_MODEL=M2-her
BENCHMARK_CHAT_API_BASE=https://api.minimax.io
BENCHMARK_CHAT_API_KEY=...
```

如果要切换 runtime profile，通常会用：

```bash
RELATIONSHIP_OS_RUNTIME_PROFILE=friend_chat_zh_v1
```

## 现在适合拿它做什么

- 做长期人格实验
- 做中文 AI 陪伴研究
- 做“同一个 AI 是否能跨 session 像同一个人”的 benchmark
- 做带结构化记忆和社会归属的聊天系统
- 做对外演示型 benchmark

## 现在还不适合拿它做什么

- 直接当成熟商用代理平台卖
- 不加护栏就做强自主外部执行
- 把它当通用桌面自动化中枢
- 期待它在所有 provider 和所有 benchmark 环境里都零配置稳定工作

## 当前已知边界

- 一期重点仍是聊天体验，不是强自主外部执行
- benchmark 链路已经比较稳定，但外部 provider 的 key / 限流仍可能影响横向对比
- 项目里仍有少量极底层的通用兜底文案，正在继续往 cue-driven + LLM rendering 收口
- 超长中文压力测试下，系统仍然在持续优化 digest-first 与 persona stability

## 适合谁看这个仓库

- 想做 AI 陪伴 / 长期人格 / 关系记忆系统的人
- 想研究“同一个 AI 是否能跨 session 像同一个人”的人
- 想做 benchmark-driven runtime，而不是只写 prompt 的人
- 想把“人格、记忆、社会归属、可评测”放进同一套系统的人

如果你只是想接一个聊天 SDK 或 IM bot，这个仓库可能比你需要的更重。  
如果你想做的是“像真人网友一样长期存在的 AI”，这里就是主战场。
