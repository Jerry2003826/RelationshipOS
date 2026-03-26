# RelationshipOS

RelationshipOS 是一个面向“长期聊天型数字人格”的运行时。

它不是单纯的聊天 UI，也不是把记忆拼进 prompt 的壳层工具。这个仓库在做的是一套更接近“同一个人持续存在”的系统骨架：同一个实体、跨会话记忆、跨人归属、脑子和嘴巴分离、长期叙事、可评测、可回放。

当前项目已经能稳定支撑两类场景：

- 对外演示型 benchmark
- 中文“像真人网友”的长聊实验

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
- 内建 benchmark、report、回放和控制台

一句话说，它更像“人格 runtime”，不是“聊天插件集合”。

## 当前能力

- FastAPI API 服务
- Event-sourced runtime
- Projector / replay / archive / audit
- Session / stream / runtime trace
- LLM backend 抽象
- 结构化 memory recall 与 memory write guard
- Cross-user social memory 与 conscience gating
- Response draft / rendering / post-audit / normalization
- Offline consolidation 与后台 jobs
- Runtime console
- 中文 friend-chat benchmark
- 官方 edge benchmark

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

## 快速开始

### 1. 安装

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

## 常用入口

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
- `GET /api/v1/users`

### Jobs / Evaluation

- `GET /api/v1/jobs`
- `POST /api/v1/jobs/offline-consolidation`
- `GET /api/v1/evaluations/scenarios`
- `POST /api/v1/evaluations/scenarios/run`

## 开发命令

```bash
uv run ruff check .
uv run pytest
```

只跑重点测试：

```bash
PYTHONPATH=src uv run pytest -q tests/test_runtime_service.py
PYTHONPATH=src uv run pytest -q tests/test_benchmarks_showcase.py
```

## Benchmark

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

## 设计原则

- 先做“同一个人持续存在”，再做“会很多工具”
- 脑子负责判断，嘴巴负责表达
- 结构化 state 可以硬，最终说出来的话尽量不要硬拼
- policy 可以配置，但最终体验不能像规则机
- benchmark 必须可复现、可回归、可比较

## 当前已知边界

- 一期重点仍是聊天体验，不是强自主外部执行
- benchmark 链路已经比较稳定，但外部 provider 的 key / 限流仍可能影响横向对比
- 项目里仍有少量极底层的通用兜底文案，正在继续往 cue-driven + LLM rendering 收口

## 适合谁看这个仓库

- 想做 AI 陪伴 / 长期人格 / 关系记忆系统的人
- 想研究“同一个 AI 是否能跨 session 像同一个人”的人
- 想做 benchmark-driven runtime，而不是只写 prompt 的人

如果你只是想接一个聊天 SDK 或 IM bot，这个仓库可能比你需要的更重。  
如果你想做的是“像真人网友一样长期存在的 AI”，这里就是主战场。
