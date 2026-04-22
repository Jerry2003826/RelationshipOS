<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" />
  <img src="https://img.shields.io/badge/benchmark-8.2%2F10-brightgreen" />
  <img src="https://img.shields.io/badge/runtime-friend__chat__zh__v1-orange" />
  <img src="https://img.shields.io/badge/router-v2-purple" />
  <img src="https://img.shields.io/badge/macro__f1-0.83-blueviolet" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" />
</p>

<h1 align="center">RelationshipOS</h1>

<p align="center">
  <strong>一个能"一直在这里"的长期陪伴型对话运行时</strong>
</p>

<p align="center">
  同一个实体 · 跨会话记忆 · 跨人归属 · 脑嘴分离 · 自进化数据闭环 · 可评测可回放
</p>

---

## TL;DR

> 市面上的 chatbot 做的是「每一轮重新组织一次上下文再回答」。
> RelationshipOS 做的是「**同一个人一直在这里,只是这次决定要不要认真动脑,再决定怎么说**」。
>
> **而且它会自己从昨晚的对话里学习、自己压缩记忆、自己写运维周报**。

| 维度 | 做法 | 对照常规 chatbot |
|:---|:---|:---|
| **路由** | 两级 Vanguard Router v2(规则 + tier-2 分类器),mini-LLM 调用 100% → 15%,p95 800ms → <1ms | 所有请求走大模型 |
| **记忆** | 三层 digest-first 结构化记忆 + 夜间压缩卡片 | 历史消息 replay |
| **数据闭环** | shadow log → LLM 银标 → 人工复核 → 周日回训(Macro F1 门槛 0.71) | 模型一次部署静态运行 |
| **用户画像** | 128 维 EMA profile_vec 注入 prompt,≈30 轮收敛 | 无画像 |
| **人格** | 同一 entity 跨 session 一致(persona_state + social_world) | 每次像换了一个人 |
| **推理** | 6 专家 DAG 并行编排(Factual / Emotional / Governance / Coordination / Expression / Response) | 单一大 prompt |
| **表达** | "脑子"和"嘴巴"分离:先想,再自然说 | 一步到位 |
| **评测** | 5 维 probe benchmark + 离线 A/B harness(EmotionalExpert prompt) | 靠主观感觉 |
| **运维** | 夜间记忆压缩 + 周级回训 + 自动运维周报(R1 一次调用) | 无自动化 |

**Benchmark:** `friend_chat_zh_v1` Overall **8.2 / 10**(2026-04-22 手工评审,vs 裸 `glm-5` 2.8 / `glm-5 + Mem0 OSS` 2.4)
**Router v2:** Macro F1 **0.83**,CI 门槛 0.71(12pt 安全余量)
**测试:** 新增 70+ 单测(W2–W4),CI ruff + pytest 全绿

---

## 一分钟看明白这是什么

你有没有遇到过这种 AI 聊天:**第一次聊得很投机,第二次再聊它完全不记得你**?或者回复"很聪明"但总像在读说明书?

RelationshipOS 想做的是**像老朋友一样一直在这里**的数字人格 — 记得上次你说工作累,这次会问"那件事后来怎么样了";知道你喜欢什么、聊天节奏是什么;同一个性格,不会每次像换一个人。

它不是聊天 App 的外壳,是**底下那层"同一个人持续存在"的系统骨架**。

---

## 自进化数据闭环(近期交付的主线)

这是 2026H1 迭代的核心叙事 — 让这套运行时从**一次性部署的模型**变成**会自己越用越好的系统**。

```
线上流量                                                      
    │                                                         
    ▼                                                         
Router v2 (规则 + tier-2 分类器)  ─┐                             
    │  ROUTER_SHADOW_SAMPLE_RATE  │  ↓ 夜间 18:00 UTC             
    ▼                              │                           
shadow_YYYYMMDD.jsonl  ────────────┘                           
    │                                                          
    ├── scripts/llm_prelabel.py    ──► silver labels (conf+reason)
    │      (LLM 自动银标)                                       
    │                                                          
    ├── scripts/review_labels.py   ──► 人工复核 queue            
    │      (confidence<0.7 才进)                               
    │                                                          
    ├── scripts/merge_labels.py    ──► training_zh.jsonl        
    │      (幂等追加)                                          
    │                                                          
    └── scripts/nightly_memory_compress.py ──► memory/compressed
           (夜间把原始对话压成记忆卡片)                         

每周日 19:00 UTC: retrain_router.yml 回训, Macro F1 >= 0.71 才部署
每周一 02:00 UTC: weekly_ops_report.yml 产出 reports/ops_YYYY-WW.md
                  (R1 一次调用, 每周成本 <1 元)
```

### 关键能力落点

| 能力 | 脚本 / 模块 | 验收 |
|:---|:---|:---|
| 路由推理 p95 从 800ms 降到 <1ms | `application/analyzers/vanguard_router.py` 接入 router_v2 | FAST_PONG gate: `conf≥0.85 & len≤12`,不破坏 knowledge_boundary |
| Shadow log 无侵入接入 | `JsonlShadowLogger` + 环境变量 `ROUTER_SHADOW_LOG_PATH` / `ROUTER_SHADOW_SAMPLE_RATE` | 采样率 0→1 可调,生产 3 个测试覆盖 |
| 周级回训 + 非回归门槛 | `.github/workflows/retrain_router.yml` + `router_v2/training/router_eval.py` | Macro F1 <0.71 拒绝发布 |
| LLM 辅助打标 4× 提效 | `scripts/llm_prelabel.py` + `scripts/labeling_metrics.py` | `speedup_x` 可断言,默认参数下 auto_share≥0.60 稳定 ≥4× |
| 夜间记忆压缩 | `scripts/nightly_memory_compress.py` + `.github/workflows/nightly_memory.yml` | 24h 窗口,summary ≤120 字,tag 白名单 |
| 自动运维周报 | `scripts/weekly_ops_report.py` + `.github/workflows/weekly_ops_report.yml` | 6 个 section(路由/日采样/银标/画像/F1/观察) |
| 用户画像 EMA | `application/analyzers/user_profile.py` | 128 维 α=0.08,30 轮 >0.9 cosine 收敛 |
| 情感接住率 A/B harness | `application/analyzers/emotional_prompt.py` + `scripts/emotion_ab_eval.py` | lexical + length + empathy 三把尺子,`catch_rate_delta` 带 gate |

---

## 核心架构

```
User Turn
  → Vanguard Router v2 (规则 + tier-2 分类器)
      ├─ FAST_PONG     (置信度 + 短 text 二元 gate) → 轻量回复
      ├─ LIGHT_RECALL  (情感接住 + 近期记忆卡片)    → EmotionalExpert prompt
      └─ DEEP_THINK    (复杂规划 / 危机 / 事实追问) → 专家 DAG

  → 专家 DAG (6 领域专家按依赖序并行)
      ├─ L1:  Factual Expert       → knowledge_boundary_decision
      ├─ L2:  Emotional Expert     → private_judgment + prompt 模块化
      ├─ L3-5: Governance Expert   → policy_gate → strategy → rehearsal
      ├─ L6-7: Expression Expert   → expression_plan + empowerment_audit
      ├─ L5-9: Coordination Expert → coordination → guidance → cadence → ritual → somatic
      └─ L10-11: Response Expert   → response_draft + rendering_policy

  → 后置审计 + fallback → event stream → projectors / console / benchmark traces

旁路 (无侵入):
  JsonlShadowLogger ──► router_v2/training/data/*.jsonl ──► 周级回训 / 夜间压缩 / 周报
  UserProfileStore  ──► EMA 向量 ──► prompt prefix
```

---

## Benchmark 成绩

120-turn 中文朋友聊天压力测试,手工评审 Overall **8.2 / 10**。

### 横向对比 (2026-04-22 手工评审,切片 `friend_chat_zh`)

| Arm | 自动 overall | 手工 overall | 结论 |
|:---|:---:|:---:|:---|
| 裸 `glm-5` | 1.8 | 2.8 | 语气过得去,记忆类任务几乎全挂 |
| `glm-5 + Mem0 OSS` | 2.3 | 2.4 | 边际改善,核心 benchmark 失败未解决 |
| **`RelationshipOS + glm-4.7`** | **6.5** | **8.2** | 整体领先,`cross_session` 曾出现幻觉化熟悉感(W5.3 已修) |

详细手工评审见 [reports/manual_review_20260422.md](reports/manual_review_20260422.md)。

### 分维 probe 得分(系统 arm,手工打分)

| 维度 | Probe | 手工得分 | 备注 |
|:---|:---|:---:|:---|
| 状态连续性 | `long_chat_continuity_zh` | **9.5** | 三个目标意念都带到 |
| 人格稳定性 | `persona_stability_zh` | **9.0** | 低能量/话少/软漂节奏准 |
| 记忆自然度 | `naturalness_under_memory` | 8.0 | 重庆 / 月饼(猫) / 不喜说教全中 |
| 社会感知控制 | `social_world_control` | **9.0** | 承认关系后主动收住 |
| 跨 session 熟人感 | `cross_session_friend_feel` | 5.5 | 延续感好,但曾编造未给定细节 |

系统独立重算 slot coverage,不信任模型自报。4 阶段 probe 渲染链路:Primary JSON → Relaxed JSON → Compact text → Plaintext repair。

**已知缺陷及处理:** `cross_session_friend_feel` 曾出现"我还记得你上次说不喜欢吃香菜"这类未得到记忆支持的表达。W5.3 从 prompt 约束 + `audit_unsupported_recall` 事后审计两层加防护。

Router v2 tier-2 分类器在 `router_v2/tests` 下 21 个测试通过,在 holdout 上 Macro F1 **0.83**,CI 门槛设 0.71(12pt 安全余量)。

---

## 快速开始

### 1. 小悠聊天(普通用户)

```bash
cp .env.example .env                         # LLM_BACKEND=mock 即可不用 API key
uv sync --extra dev
uv run uvicorn relationship_os.main:app --reload
# 浏览器打开 http://127.0.0.1:8000/static/chat.html
```

### 2. 跑 Benchmark(开发者)

```bash
# 120-turn 长聊压力
uv run python -m benchmarks.minimax_companion_stress_zh_demo \
  --system-only --stress-mode stable --stress-turns 120

# Router v2 tier-2 评测
python router_v2/training/router_eval.py --data router_v2/training/training_zh.jsonl
```

### 3. 数据闭环脚本(研究者)

```bash
# LLM 银标
python scripts/llm_prelabel.py \
  --input router_v2/training/data/shadow.jsonl \
  --output router_v2/training/data/silver_labels.jsonl

# 人工复核(交互模式 1/2/3/s/q)
python scripts/review_labels.py --input ... --output ... --interactive

# 夜间记忆压缩(dry-run 不调 LLM)
python scripts/nightly_memory_compress.py --input ... --dry-run

# 打标提效指标
python scripts/labeling_metrics.py --silver ... --gate 4.0

# 情感接住率 A/B
python scripts/emotion_ab_eval.py \
  --turns fixtures/emotion_turns.jsonl \
  --persona "你是贴心的数字人格" \
  --gate 0.05
```

### 4. 跑测试

```bash
uv run pytest -q                     # 全量
uv run pytest tests/test_emotion_ab_eval.py -q   # 单文件
```

---

## 项目结构

```
.
├── benchmarks/                      # benchmark runner / scoring / report
├── router_v2/                       # Vanguard Router v2
│   ├── training/                    # seeds / silver / training / test 数据 + 训练脚本
│   ├── policies/router/             # model.joblib
│   └── tests/                       # 21 tests
├── scripts/                         # 数据闭环 + 运维
│   ├── query_shadow.py              # W2 shadow 日志查询
│   ├── llm_prelabel.py              # W2 LLM 银标
│   ├── review_labels.py             # W2 人工复核
│   ├── merge_labels.py              # W2 合并训练集
│   ├── nightly_memory_compress.py   # W3 夜间压缩
│   ├── weekly_ops_report.py         # W3 运维周报
│   ├── labeling_metrics.py          # W3 打标提效指标
│   └── emotion_ab_eval.py           # W4 情感 A/B harness
├── src/relationship_os/
│   ├── application/
│   │   ├── runtime_service.py       # 主运行时 + Foundation 并行
│   │   ├── memory_service.py        # recall / attribution / 跨人保护
│   │   ├── entity_service.py        # 人格 / 良心 / drive / narrative
│   │   ├── llm.py                   # 结构化 probe / slot coverage / fallback
│   │   └── analyzers/
│   │       ├── vanguard_router.py   # 路由 shim (接 router_v2)
│   │       ├── user_profile.py      # 128 维 EMA
│   │       ├── emotional_prompt.py  # EmotionalExpert prompt 模块
│   │       └── experts/             # 6 专家模块 + DAG
│   ├── core/                        # config / logging
│   └── domain/                      # contracts / event types
├── .github/workflows/
│   ├── ci.yml                       # ruff + pytest
│   ├── retrain_router.yml           # 周日 19:00 UTC
│   ├── nightly_memory.yml           # 每夜 18:00 UTC
│   └── weekly_ops_report.yml        # 周一 02:00 UTC
└── tests/                           # 全仓单测, 含 W2-W4 新增 70+ 个
```

---

## 记忆架构

```
┌──────────────────────────────────────────────┐
│  Nightly Compressed Cards (W3 新增)            │
│  └── memory/compressed_YYYYMMDD.jsonl         │
│      每晚把 24h 对话压成 ≤120 字要点 + tag     │
├──────────────────────────────────────────────┤
│  Digest Layer (digest-first, 长聊不翻原始)      │
│  ├── fact_slot_digest     稳定事实槽位          │
│  ├── narrative_digest     状态 / 困扰 / 模式    │
│  └── relationship_digest  熟悉度 / 温度 / 节奏  │
├──────────────────────────────────────────────┤
│  Structured Recall                            │
│  ├── attribution (source / subject 区分)       │
│  ├── scope filtering                          │
│  ├── memory integrity                         │
│  └── symbolic hints                           │
├──────────────────────────────────────────────┤
│  Raw Memory / Event Stream                    │
└──────────────────────────────────────────────┘
```

---

## 脑子 vs 嘴巴

**脑子**:判断这轮是不是要认真动脑、该调哪些记忆、能说多少(`direct_ok` / `attribution_required` / `hint_only` / `withhold`)
**嘴巴**:用自然口吻说出来,贴合 persona,少模板感

代码里尽量避免硬拼大量中文句子。规则提供结构化 cue,最后的话由模型在约束下生成。

---

## 配置

```bash
# LLM 后端
RELATIONSHIP_OS_LLM_BACKEND=minimax          # litellm / minimax / mock
RELATIONSHIP_OS_LLM_MODEL=M2-her
RELATIONSHIP_OS_LLM_API_KEY=...

# Runtime
RELATIONSHIP_OS_RUNTIME_PROFILE=friend_chat_zh_v1

# 数据闭环
ROUTER_SHADOW_LOG_PATH=router_v2/training/data/shadow.jsonl
ROUTER_SHADOW_SAMPLE_RATE=1.0           # 0..1, 采样率
ROUTER_PRELABEL_MODEL=deepseek-chat     # W2 银标用的模型
ROUTER_MEMORY_MODEL=deepseek-chat       # W3 夜间压缩
ROUTER_NARRATIVE_MODEL=deepseek-reasoner # W3 周报(R1 一次/周)
```

---

## 常用 API

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/api/v1/sessions` | 创建 session |
| POST | `/api/v1/sessions/{id}/turns` | 发一轮对话 |
| GET  | `/api/v1/runtime` | 当前 runtime 状态 |
| GET  | `/api/v1/sessions/{id}/memory` | 查看 session 记忆 |
| GET  | `/api/v1/entity/policy` | 实体 policy |
| GET  | `/api/v1/entity/narrative` | 实体叙事 |
| WS   | `/api/v1/ws/runtime` | 实时 WebSocket |
| GET  | `/api/v1/console` | Web Console |

---

## 设计原则

- 先把"同一个 AI 像真人一样持续存在"做好,再考虑加功能
- 脑子认真想,嘴巴自然说,不在代码里硬拼模板
- AI 自己决定这轮要不要多想,系统提供结构 + 护栏
- 所有改进靠可重复的 benchmark / 单测验证,不是拍脑袋
- **自进化优先**:能自动产生数据 → 自动打标 → 自动回训 → 自动出报告 的,一律自动化

---

## 合规与工程质量

- 全仓 ruff + pytest CI,PR 不绿不合
- 数据闭环 workflow 全部带非回归门槛:回训 Macro F1 ≥ 0.71,打标提速 ≥ 4×,情感 delta ≥ gate
- 敏感字段用环境变量,不硬编码 key
- 对齐 NIST AI RMF + 中国《生成式人工智能服务管理暂行办法》+ GB 45438-2025 AI 生成内容标识

---

## 适合谁

- 对**长期陪伴型 AI** 感兴趣的研究者 / 工程师
- 想看"同一个 AI 跨多次会话保持一致人格"怎么工程化的人
- 喜欢 benchmark + 数据闭环驱动开发,不只是堆 prompt 的人
- 想系统化把**人格 / 记忆 / 归属 / 可评测 / 自进化**一起落地的人

如果你只想快速接一个聊天机器人 SDK,这个项目可能有点重。但如果你相信 AI 可以**像真人网友一样长期存在并建立真实关系**,这里有很多可探索的内容。

---

## 路线图(2026 H1)

- [x] **W0** 设计与 baseline
- [x] **W1** Router v2 接入 runtime(PR #6)
- [x] **W2** 持续学习数据闭环(PR #7 / #8 / #9)
- [x] **W3** AI 半自主功能(PR #10 / #11 / #12)
- [x] **W4** EmotionalExpert prompt + A/B harness(PR #13 / #14)
- [ ] **W5** 文档 + 简历叙事收尾(进行中)

---

欢迎试用、反馈、PR。让数字陪伴真的"像个人"。
