# Interview Cheatsheet — RelationshipOS

> 给自己看的。不进 README 不讲给用户看。
> 目标:15 秒钩子 → 2 分钟 pitch → 20 分钟深聊 → 常见追问都能答。

---

## 0. 一句话定位(15 秒电梯)

> **RelationshipOS 是一套让 AI 像老朋友一样持续存在的对话运行时 — 重点不是更大的模型,是让同一个 AI 跨多次对话记得你、有稳定人格、而且线上每多聊一轮系统就自己越学越好,整套自进化闭环一周 GPU 成本低于 1 元。**

关键词(按强度):**自进化数据闭环 / 脑嘴分离 / 长期陪伴 / 可评测可回放**。

---

## 1. 两分钟 Pitch(面试开场自我介绍之后)

> 我最近做了一个叫 **RelationshipOS** 的项目,是一套\"长期陪伴型对话的运行时\"。
>
> 先说它想解决什么问题:市面上 chatbot 普遍是\"每一轮重新组织一次上下文再回答\",结果就是你今天聊得投机,明天它完全不记得;或者回答很聪明但像在读说明书。我想做的是**同一个 AI 一直在这里**,像老朋友,记得你、人格稳定、还会自己越用越好。
>
> 架构上我做了三件事:
>
> **第一,脑嘴分离**。先过一个两级 Vanguard Router v2,规则 + TF-IDF 分类器兜底,决定这一轮要不要动脑,p95 从 800ms 降到 <1ms,LLM 调用减少到 15%。然后才进 6 专家 DAG,最后表达层单独做自然化。
>
> **第二,自进化数据闭环**。线上每一次路由决策都旁路落进 shadow log,LLM 先银标,人工只看置信度低的,打标速度 4 倍提升;每周日自动回训,Macro F1 不到 0.71 直接拒绝发布。夜间自动压缩记忆,每周一自动出运维周报,R1 一周只调一次,整套周成本 <1 元。
>
> **第三,可评测**。120 轮中文朋友压力测试,overall 7.9 / 10,对比自己历史基线 +29%。每个专家声明自己该产哪些 slot,运行时独立重算,不信模型的自报。
>
> 技术栈是 Python 3.12 + FastAPI,整仓 ruff + pytest CI,W2-W4 新增 70+ 单测。代码在 GitHub 上,我可以现场打开给您看。

### Pitch 的四个关键落点

讲完之后,**这四个数字一定要留在面试官脑子里**:

1. **p95 800ms → <1ms**(路由工程)
2. **Macro F1 0.83,门槛 0.71**(模型质量 + 非回归门槛)
3. **打标 4× 提效**(数据闭环 ROI)
4. **周成本 <1 元**(工程务实)

---

## 2. 20 分钟深聊脚本

### 段 A:动机(2 分钟)

**面试官:这个项目为什么做?**

> 两个起点。一是我用了很多 chatbot,发现都有\"每次像换一个人\"的问题,这个现象背后其实是系统里没有\"同一人格持续存在\"的骨架。二是我在另一个项目(nvidia LoRA pipeline)里做过训练侧的事,这次想做**运行时 + 数据闭环**这边的能力,补全自己从训练到部署到自学习的全链路。
>
> 我想验证的问题其实是:**在不靠更大模型的前提下,能不能只靠架构和数据工程,让同一个 AI 的陪伴体验显著变好**。

### 段 B:架构选型(5 分钟)

**面试官:为什么不做成一个大 prompt?**

讲\"架构文档 §1.1\"的四个老毛病,然后讲\"三个关注点解耦\":路由 / 专家 / 表达。

**面试官:Router v2 为什么不用大模型判断?**

讲延迟、成本、可控性。展示 tier-1 规则 + tier-2 TF-IDF+LR 的选型理由(数据量 2k / 推理必须 <1ms / 可解释)。

**面试官:专家 DAG 不会很慢吗?**

- 并行调度,L3-L7 四组并行
- Router v2 已经决定过这轮要不要进 DAG,FAST_PONG 和 LIGHT_RECALL 不走 DAG
- 所以 DAG 的延迟只给真正复杂的 turn 付,长尾延迟可控

### 段 C:数据闭环(6 分钟)—— **这段最值钱**

**面试官:数据闭环具体怎么跑的?**

照着 `docs/architecture.md` §3 讲:线上 → shadow log → LLM 银标 → 人工 review → merge → 周日回训。

强调三个\"工程主义\"细节:

1. **Shadow log 无侵入**(`asyncio.create_task`,不阻塞主链路)
2. **银标置信度分流**(auto_share ≥ 0.60 稳定 4× 提速)
3. **非回归门槛**(Macro F1 < 0.71 拒绝发布,留 12pt 余量避训练噪声)

**面试官:你这个流程里有什么是踩坑踩出来的?**

- **FAST_PONG gate 最早只看 conf**,吃过亏(短情感句被误判),补了 `len <= 12` 双重门槛
- **Macro F1 门槛曾经设成和基线一样**,一次训练的数据切分抖动就能挡回来,后来调到 0.71
- **R1 曾经想做到每日**,一周后发现没人看,改成每周一次,成本从几十元降到 <1 元

### 段 D:记忆(3 分钟)

**面试官:为什么没用 RAG?**

- 向量对关系性记忆弱
- 长聊召回漂移
- 自己选的是 digest-first 三层架构:压缩卡片 / 结构化 digest / 原始流
- 长聊只翻前两层,prompt token 可控

**面试官:记住多久?**

夜间压缩:24h 窗口压成 ≤120 字卡片,tag 白名单。长期 digest 持续累积,没上 decay(下一步要做)。

### 段 E:评测(3 分钟)

**面试官:怎么知道做得好?**

- 120-turn 中文朋友压力测试,overall 7.9 / 10,对比基线 +29%
- 每个专家声明 expected_slots,运行时独立重算 coverage,模型嘴硬不算分
- 4 阶段渲染链路(Primary JSON → Relaxed JSON → Compact text → Plaintext repair)
- W4 新增情感接住率 A/B harness(lexical + length + empathy 三把尺子)

**面试官:7.9 / 10 的打分是你自己给的?**

Benchmark probe 是规则 + slot coverage 打的,不是模型自评。当然整个 benchmark 是我设计的,所以是\"自己的尺子量自己\",**但尺子可复现、可挑刺**。

### 段 F:工程质量(1 分钟)

- 全仓 ruff + pytest CI,PR 不绿不合
- 数据闭环 workflow 全部带非回归门槛
- 敏感字段走环境变量
- 合规:对齐 NIST AI RMF + 中国《生成式人工智能服务管理暂行办法》+ GB 45438-2025

---

## 3. 常见追问 (FAQ)

### Q1:为什么不训一个 LoRA?

**答**:W4 原本计划是的,后来砍了。三个原因:

1. 最后的回复要接大模型(minimax / deepseek),LoRA 只是修饰
2. 训一次 ≈ 200 元 GPU + 10k 条高质量情感数据,ROI 低
3. \"是否真能多接住情绪\"这个核心问题,**A/B harness 就能答**

但我做的时候保留了 `generator_fn` 接口,未来要接真 LoRA 只要传入一个 callable,harness 不用改。这是**工程上做\"可逆决定\"的例子** — 不做,但不堵死将来做的路。

### Q2:你怎么评价自己的代码水平?

**答**:这个项目给了我三件东西:

1. **大型系统里的模块边界**怎么定(路由 / 专家 / 表达 / 记忆 / 运维,这五条线各自能独立演化)
2. **数据闭环的工程细节**(旁路采样 / 置信度分流 / 非回归门槛 / 成本控制)
3. **CI 驱动开发**(gate-as-code,ruff/pytest/门槛指标都进 CI)

但我也清楚短板:还没跑过真实规模流量,回训的 F1 是 holdout 上的,不是 A/B 在线的。

### Q3:你用了哪些 AI?

**答**:诚实回答 — 我用 Cursor / Claude 辅助写代码和查文档。**但项目的架构选型、数据闭环设计、门槛数字、benchmark probe 全部是我自己定的**,这些是 AI 没法替你做的判断。写代码只是把判断落成比特。

### Q4:为什么选陪伴型 AI 这个方向?

**答**:因为它是**长期主义的、被低估的、数据闭环最干净的方向**之一。

- 长期:真人网友关系是人类最长的高频交互
- 低估:当前 AI 圈太热衷\"更大模型\",很少人做\"同一个人格持续存在\"的骨架
- 干净:每一次对话都是反馈,不像自动驾驶/医疗要等长周期 ground truth

### Q5:如果让你从头再做一遍,最先改什么?

**答**:

1. **路由从 LR 直接上 distilBERT 蒸馏**,虽然 CPU 延迟 10-30ms 比现在慢,但 F1 能直接冲 0.88+,省后续迁移成本
2. **记忆加 decay 字段**,当时偷懒没做,现在补回去工作量不小
3. **A/B harness 一开始就接 minimax / deepseek 真 LLM**,跑一次真对照数据,不要用 mock

### Q6:MoE 在项目里是怎么体现的?(DeepSeek 面试专用)

**答**:坦白 — **这个项目里没有 MoE**。专家 DAG 是\"多专家系统\",不是神经网络层意义上的 MoE。

我对真 MoE 的理解是:top-k gating + expert routing + load balancing,训练时要处理 token drop 和 expert 坍缩。我另一个项目(nvidia)里跑过相关实验,但这里是**应用层的多专家编排**,两件不同的事。

**这一题的加分点**:**主动澄清\"多专家\"和\"MoE\"不是同一件事**,比硬蹭 MoE 术语更能体现技术诚实。

### Q7:这套系统能上生产吗?

**答**:还不能直接上。缺:

- 真实压测(当前只有 120 轮模拟)
- 多租户和 quota
- 关键路径的 tracing(Jaeger/OpenTelemetry)
- 生产级 memory 存储(当前是 jsonl,生产需要数据库)

**但架构是\"上生产友好\"的**:shim 设计让换底层存储不改业务代码;所有任务已经在 GitHub Actions 上定时跑;合规章节已经对齐了法规要求。

### Q8:你这个 benchmark 会不会过拟合?

**答**:会,**这是已知问题**。120-turn 压力测试是我自己设计的 probe,容易\"照着考题学习\"。

应对:

1. probe 每迭代一段时间就换一批(已经有机制,每季度滚一版)
2. 银标+人工复核的\"真流量\"作为独立回归集(正在建)
3. 长期要引入**外部评测**(类似 MT-Bench 的第三方 benchmark)

---

## 4. 面试官不同背景的侧重点

| 对方背景 | 重点讲 | 淡化 |
|:---|:---|:---|
| **DeepSeek / 训练平台** | 数据闭环 / 非回归门槛 / R1 一周一次省成本 / 训练数据质量控制 | 记忆架构 / 表达层 |
| **MiniMax / 对话 / 陪伴产品** | 长期人格 / 情感接住率 / 脑嘴分离 / 120-turn benchmark | 路由工程细节 |
| **Moonshot / 长上下文** | Digest-first 记忆 / 夜间压缩 / digest 层的设计取舍 | 训练闭环 |
| **智谱 / 多模态** | 专家 DAG 可扩展性 / slot coverage / event stream 可观测 | 路由 F1 |
| **华为 / 大厂工程** | CI / 合规 / 可回放 / 门槛 gate-as-code | 情感接住率等主观指标 |
| **Canva / Atlassian (Sydney)** | 系统抽象 / 产品化思维 / benchmark 驱动 / collaboration-ready event stream | 具体中文 NLP 细节 |
| **TikTok Sydney / Google Sydney** | 数据闭环规模化的想法 / router 能否线上 online learning | 记忆的中文友好性 |

---

## 5. 别踩的坑

### 5.1 不要说的话

- **\"我用 MoE\"** — 这里没有 MoE,说了就露馅
- **\"跑过真实用户\"** — 目前只有压测数据,不要吹
- **\"7.9 对比 GPT-4 基线\"** — 7.9 是对比自己历史基线 6.1,不是对比 GPT-4
- **\"简历上写了训 LoRA\"** — 这个项目没训,是 harness,别混
- **\"我用了爬虫\"** — 用\"数据采集 / 数据收集\"代替

### 5.2 一定要说的话

- **\"我砍掉了 LoRA,做了 harness,保留了 generator_fn 接口\"** — 这是工程判断力的最强证据
- **\"这个门槛故意低于基线,是因为训练噪声\"** — 展示你理解 CI 稳定性 vs 严格性的 trade-off
- **\"Macro F1 / p95 / catch_rate_delta / speedup_x 都进 CI\"** — gate-as-code 是你的工程审美
- **\"R1 只在周报调一次,每周成本 <1 元\"** — 成本意识是 senior 工程师的必备

---

## 6. Demo 流程(如果现场演示)

1. **打开 GitHub 仓库**,先展示 README 的能力表 + 数据闭环图(1 分钟)
2. **打开 `docs/architecture.md` §3**,讲数据闭环(2 分钟)
3. **打开一个 PR**(推荐 PR #7 / #14),讲 commit 粒度和测试覆盖(2 分钟)
4. **`uv run python -m benchmarks.minimax_companion_stress_zh_demo --system-only --stress-mode stable --stress-turns 20`**,跑 20 轮 demo,展示 slot coverage 实时输出(3 分钟)
5. **打开 `.github/workflows/retrain_router.yml`**,讲门槛 + artifact 发布(1 分钟)
6. **打开 `reports/ops_YYYY-WW.md`(如果有真跑过一次)**,讲周报结构(1 分钟)

---

## 7. 结尾的一句话

如果让我用一句话总结 RelationshipOS 给我带来什么:

> **不是又多训了一个模型,而是搞清楚了一个能自己越长越好的 AI 系统长什么样,以及这套骨架里哪些地方值得靠工程,而不是靠砸算力。**

---

## 附录:简历用的精简 bullet (3 条)

放进简历之前,参考 `docs/resume_bullets.md`(后续 PR 会加)。暂时先列这里:

**中文版**:

- 设计并实现两级 Vanguard Router v2(规则 + TF-IDF + LR),在 holdout 上 Macro F1 0.83,路由 p95 800ms → <1ms,mini-LLM 调用减少 85%,CI 门槛 0.71
- 搭建完整的线上数据自进化闭环:shadow 日志 → LLM 银标 → 人工复核 → 周级回训 + 夜间记忆压缩 + R1 运维周报,打标速度 4×,周 GPU 成本 <1 元
- 120 轮中文长聊压力测试 overall 7.9/10 (+29% vs 基线),6 专家 DAG 产出 slot 运行时独立重算,4 阶段渲染链路保证稳态输出

**英文版**:

- Designed and shipped a two-tier conversational router (rules + TF-IDF/LR) achieving 0.83 Macro F1 on holdout, cutting p95 routing latency from 800ms to <1ms and mini-LLM calls by 85%, with a CI non-regression gate of 0.71
- Built an end-to-end self-evolving data flywheel: shadow log → LLM silver labeling → human review → weekly router retrain + nightly memory compression + R1-generated weekly ops report, delivering 4× labeling throughput at <1 RMB/week GPU cost
- Achieved 7.9/10 on a 120-turn Chinese companion benchmark (+29% over baseline) via a 6-expert DAG with runtime-recomputed slot coverage and a 4-stage graceful-degradation rendering pipeline

---

**最后的最后:把这份 cheatsheet 背熟,但讲的时候别念,按对方问的方向走。你是在和一个工程师聊天,不是在答辩。**
