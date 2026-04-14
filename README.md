<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue" />
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
| **结构化 probe 渲染** | Benchmark probe 通过 JSON clause slots 渲染，slot-based coverage 重算 |
| **Policy 驱动** | 运行时决策从 Python if/else 迁到可配置的 policy 文件 |
| **可评测可回放** | 内建 benchmark / report / console，不是靠主观感觉 |

---

## Benchmark 成绩

最新 120-turn stable system-only benchmark（MiniMax M2-her，`friend_chat_zh_v1`）：

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
  → turn interpretation (intent / appraisal / emotional load / state guess)
  → deliberation routing (fast_reply / light_recall / deep_recall)
  → memory / digest foundation (fact_slot / narrative / relationship digest)
  → conscience / disclosure gating (attribution / scope / guard)
  → response draft + rendering
  → post-audit + fallback
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
│   │   ├── runtime_service.py   # 主运行时，turn orchestration
│   │   ├── memory_service.py    # recall / ranking / attribution / 跨人保护
│   │   ├── entity_service.py    # 人格 / 良心 / drive / narrative / world state
│   │   ├── llm.py              # 模型调用 / 结构化 probe / slot coverage / fallback
│   │   └── projectors/          # self_state / social_world / entity_persona ...
│   ├── core/                    # config / logging
│   ├── domain/                  # contracts / event types / models
│   └── main.py
└── tests/
    ├── test_llm.py              # 46 tests（结构化 probe / coverage / fallback）
    └── test_runtime_service.py  # cue building / prompt / probe detection
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

## 快速开始

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
uv run pytest tests/test_llm.py -q           # 46 tests，核心 probe pipeline
uv run pytest tests/test_runtime_service.py -q  # cue / prompt / probe detection
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

## 设计原则

- **先做"同一个人持续存在"，再做"会很多工具"**
- 脑子判断，嘴巴表达；结构化 state 可以硬，说出的话不要硬拼
- AI 先判断要不要动脑，系统只做轻度稳定和护栏
- Policy 可配置，但最终体验不能像规则机
- **Benchmark 必须可复现、可回归、可比较**

---

## 适合谁

- 想做 **AI 陪伴 / 长期人格 / 关系记忆** 系统的人
- 想研究"同一个 AI 是否能跨 session 像同一个人"的人
- 想做 **benchmark-driven runtime**，而不是只写 prompt 的人
- 想把"人格、记忆、社会归属、可评测"放进同一套系统的人

如果你只是想接一个聊天 SDK 或 IM bot，这个仓库可能比你需要的更重。  
如果你想做的是 **"像真人网友一样长期存在的 AI"**，这里就是主战场。
