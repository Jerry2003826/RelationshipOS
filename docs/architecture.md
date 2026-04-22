# Architecture Deep-Dive

> 这篇是给想真正读懂 RelationshipOS 的人看的。如果你只是想跑一下,看 [README](../README.md) 就够了。
> 这里会讲清楚四件事:**为什么这么设计 / 各模块怎么配合 / 关键权衡 / 未来怎么演化**。

---

## 0. 一页纸总览

```
                ┌──────────────────────────────────────────────────────────┐
                │                    User Turn                              │
                └──────────────────────────────────────────────────────────┘
                                        │
                                        ▼
         ┌───────────────────────────────────────────────────────┐
         │            Vanguard Router v2 (规则 + tier-2)           │
         │  - 规则命中 → FAST_PONG / LIGHT_RECALL                  │
         │  - 兜底 → tier-2 TF-IDF + LogisticRegression            │
         │  - 旁路:JsonlShadowLogger (采样率可调)                  │
         └───────────────────────────────────────────────────────┘
             │FAST_PONG          │LIGHT_RECALL          │DEEP_THINK
             ▼                   ▼                      ▼
       轻量回复             EmotionalExpert       6 专家 DAG 并行编排
       (conf≥0.85           prompt 模块           (Factual / Emotional /
        & len≤12)           slot 拼装              Governance / Coordination
                                                  / Expression / Response)
                                        │
                                        ▼
                         后置审计 + fallback + event stream
                                        │
                  ┌─────────────────────┼─────────────────────┐
                  ▼                     ▼                     ▼
            用户渲染回复          JsonlShadowLogger      benchmark trace
                                        │
                                        ▼
                    自进化数据闭环 (nightly / weekly crons)
```

一句话:**每一轮对话都会过一个三级路由,决定这轮值不值得动脑;每一条线上流量都旁路沉淀为训练数据,系统自己学、自己压、自己出报告**。

---

## 1. 为什么不做成一个大 prompt

### 1.1 现状的问题

市面上大部分 chatbot 结构是:

```
[长系统 prompt] + [最近 N 轮历史] + [用户输入] → LLM → 回复
```

这种结构有四个老毛病:

1. **无身份**:模型每轮都靠 prompt 猜\"我是谁\",没有跨会话持续的人格/世界。
2. **无成本意识**:\"今天吃啥\"和\"我想自杀\"调的是同一条链路,全靠大模型硬抗。
3. **不可评测**:输出是自然语言,很难说\"比昨天好在哪\"。
4. **不进化**:线上跑再久模型不会变聪明,唯一迭代方式是人肉改 prompt。

### 1.2 RelationshipOS 的选择

把\"对话\"拆成**三个相对独立的关注点**:

| 关注点 | 谁负责 | 怎么演化 |
|:---|:---|:---|
| 这轮要不要认真想 | **Router v2**(分类器) | shadow log → silver label → 周回训 |
| 认真想的时候想什么 | **6 专家 DAG** | 规则 + LLM 混合,slot coverage 可验证 |
| 认真想完嘴怎么说 | **Expression / Response Expert** | 4 阶段渲染 + benchmark probe |

这样路由和内容解耦,路由可以单独训练;专家和表达解耦,表达可以单独评测。

---

## 2. Vanguard Router v2:两级路由的代价与收益

### 2.1 为什么不直接让大模型自己判断

曾经试过:每轮让 mini-LLM 输出一个 `should_think_hard: bool`。问题是:

- **p95 ~800ms**,长聊场景(120 轮)累积延迟非常高
- **成本线性涨**,用户越忠诚付出越多
- **不可控**:mini-LLM 偶尔把\"今晚想吃啥\"判成 DEEP_THINK

### 2.2 v2 设计

```
class VanguardRouter:
    def decide(turn) -> RouteDecision:
        # Tier-1: 规则短路
        if rule := fast_pong_rule(turn):
            return rule                      # conf=1.0 直接 FAST_PONG

        if rule := crisis_rule(turn):
            return rule                      # 自杀/暴力 → DEEP_THINK + policy_gate

        # Tier-2: TF-IDF + LogisticRegression
        label, conf = tier2_classifier.predict(turn)
        if conf >= 0.85 and len(turn.text) <= 12:
            return FAST_PONG                 # 保守 gate,避免误杀

        return label  # LIGHT_RECALL / DEEP_THINK
```

### 2.3 数字

| 指标 | v1 (mini-LLM) | v2 (规则 + tier-2) |
|:---|:---:|:---:|
| p95 路由延迟 | 800ms | **<1ms** |
| Macro F1 (holdout) | ~0.78 | **0.83** |
| 每千轮 LLM 调用 | 1000 | **~150** |
| 可复现性 | 不可复现 | 模型可打包可回归 |

### 2.4 为什么是 TF-IDF + LR 而不是 BERT

- **训练集目前只有 ~2k 条带标签**,大模型不是在学规律是在背样本
- **推理必须 <1ms**,BERT 在 CPU 上至少 10–30ms
- **可解释**:LR 的权重可以直接读,回归定位快
- **未来要换**:trained 接口不变(`predict(text) -> (label, conf)`),换模型不用改运行时

### 2.5 FAST_PONG gate 为什么这么保守

`conf >= 0.85 AND len <= 12` 这个双重门槛是**踩过坑才加的**:

- 早期只看 conf,"我今天有点难过"这种短情感句会被误判 FAST_PONG,体验极差
- 加 len 限制后,短问候("在吗"/"吃了吗")走 FAST_PONG,长句一律进 LIGHT_RECALL 及以上
- 代价:~5% 本可快通的长句也慢了,但**情感接住率没再出过灾难案例**

---

## 3. 数据闭环:把线上流量变成训练燃料

### 3.1 核心思想

```
线上流量  ──(ROUTER_SHADOW_SAMPLE_RATE)──►  shadow_YYYYMMDD.jsonl
                                                    │
           ┌────────────────────────────────────────┤
           ▼                                        ▼
    llm_prelabel.py                        nightly_memory_compress.py
    (DeepSeek chat 一次一条)                (DeepSeek chat 夜间批量)
           │                                        │
           ▼                                        ▼
    silver_labels.jsonl                    memory/compressed_*.jsonl
    (conf + reason)                        (每晚产一批 ≤120 字卡片)
           │
           ▼
    review_labels.py
    (confidence<0.7 才进人工,其余 auto_share)
           │
           ▼
    merge_labels.py → training_zh.jsonl (幂等追加)
           │
           ▼
    周日 19:00 UTC: retrain_router.yml
    (Macro F1 < 0.71 拒绝发布)
```

### 3.2 几个关键设计

**JsonlShadowLogger 无侵入**
运行时调用 `router.decide(turn)` 不变,shim 在 `vanguard_router.py` 里加了一行 `asyncio.create_task(logger.log(...))`。失败/磁盘满不会阻塞主链路。

**采样率可调**
`ROUTER_SHADOW_SAMPLE_RATE=0.0` 关,`=1.0` 全采。线上可以跟随日活动态调低,压测可以拉满。

**银标置信度驱动分流**
DeepSeek 给每条预测配一个 `confidence` 和 `reason`。脚本用这个置信度决定进 auto_share(信)还是 review queue(疑)。实测 `auto_share ≥ 0.60` 的样本人工复核通过率 >95%,于是默认阈值 0.7。

**4× 提效 gate 怎么算**

```python
speedup_x = baseline_secs_all / total_secs
# baseline_secs_all = N * 90s            (假设人肉打一条 90 秒)
# total_secs = auto_share*N*0s  +  review_share*N*30s   (复核一条 30 秒)
# 默认参数下 speedup_x ≈ 4.5
```

`labeling_metrics.py --gate 4.0` 可以在 CI 里断言这个数字,不达标 PR 不合。

**周级回训非回归门槛**
`retrain_router.yml` 每周日 19:00 UTC:

1. 拉最新 `training_zh.jsonl`
2. 训练 tier-2 模型
3. 在 holdout 上跑 `router_eval.py`
4. Macro F1 ≥ 0.71 → 产出 `model.joblib` artifact
5. < 0.71 → 工作流失败,老模型继续服务

门槛 0.71 是在当前 0.83 基线上留的 12pt 安全余量。**这个数字故意低于当前基线**,否则一次训练噪声就会挡住正常迭代。

### 3.3 整个闭环跑起来的成本账

| 任务 | 频率 | 模型 | 每次估计成本 |
|:---|:---|:---|:---:|
| 银标预打 | 按批 | deepseek-chat | ~10 元 / 万条 |
| 夜间记忆压缩 | 每天 1 次 | deepseek-chat | ~0.1 元 / 日 |
| 周级回训 | 每周 1 次 | 本地 sklearn | **0 元** |
| 运维周报 | 每周 1 次 | deepseek-reasoner (R1) | **<1 元** |

这是**\"能自己跑,又烧不起来\"**的关键:R1 只在周报时调一次,日常 memory/prelabel 全用 chat 级模型。

---

## 4. 专家 DAG:6 个专家怎么分工

### 4.1 DAG 拓扑

```
                    ┌────────────────────┐
                    │  Factual Expert    │  L1
                    │  knowledge_boundary│
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Emotional Expert   │  L2
                    │ private_judgment + │
                    │ prompt 模块化      │
                    └─────────┬──────────┘
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
       Governance L3-5   Coordination   Expression L6-7
       policy_gate       L5-9           plan +
       strategy          coordination   empowerment
       rehearsal         guidance       audit
                         cadence
                         ritual
                         somatic
                              │
                              ▼
                    ┌────────────────────┐
                    │ Response Expert    │  L10-11
                    │ response_draft +   │
                    │ rendering_policy   │
                    └────────────────────┘
```

**L 编号不是层数,是 slot 编号**。每个专家产出若干 slot,后面的专家依赖前面的 slot。

### 4.2 为什么这样拆

- **Factual 先跑**:知识边界不能说的话,后面所有专家都要尊重
- **Emotional 次之**:情感判断决定整轮语气,也决定是否需要 governance 介入(比如用户说\"想死\")
- **Governance / Coordination / Expression 并行**:各自写不同 slot,不互相阻塞
- **Response 最后**:拿到所有上游 slot,合成 `response_draft` + `rendering_policy`

### 4.3 Slot coverage:不信模型的自报

每个专家声明\"我该填哪些 slot\",运行时**独立重算**实际产出了哪些:

```python
expected = expert.expected_slots()        # {"private_judgment", "emotional_tone"}
actual   = extract_slots(expert_output)    # {"private_judgment"}
coverage = len(actual) / len(expected)     # 0.5
```

这个 coverage 是 benchmark 打分的一部分,**模型不能靠嘴硬拉分**。

### 4.4 4 阶段渲染链路

最后的自然语言生成是:

```
Primary JSON      ──失败──► Relaxed JSON
                                │
                           ──失败──► Compact text
                                │
                           ──失败──► Plaintext repair
```

每一阶段都比前一阶段更宽松。保证**即便模型不听话,也能出一个人话回复**,代价是 slot coverage 会降。

---

## 5. 记忆:三层 digest-first 架构

### 5.1 为什么不做 RAG

试过。向量召回对\"我朋友上周的状态\"这种**关系性记忆**效果很差 —— 相似度高的不一定是相关的。长聊场景还有严重的召回漂移。

### 5.2 实际结构

```
┌──────────────────────────────────────────────┐
│  L0: Nightly Compressed Cards (W3 新增)        │
│  - memory/compressed_YYYYMMDD.jsonl           │
│  - 每晚把 24h 对话压成 ≤120 字 + tag           │
│  - tag 白名单: fact / emotion / plan / ...    │
├──────────────────────────────────────────────┤
│  L1: Digest Layer (digest-first)              │
│  - fact_slot_digest     稳定事实槽位            │
│  - narrative_digest     状态 / 困扰 / 模式      │
│  - relationship_digest  熟悉度 / 温度 / 节奏    │
├──────────────────────────────────────────────┤
│  L2: Structured Recall                        │
│  - attribution (source / subject 区分)         │
│  - scope filtering (本 session / 本 entity)    │
│  - memory integrity (冲突检测)                 │
│  - symbolic hints (暗示而非明说)               │
├──────────────────────────────────────────────┤
│  L3: Raw Memory / Event Stream                │
└──────────────────────────────────────────────┘
```

**Digest-first 是指**:长聊到 100+ 轮时,prompt 里只带 L1/L0,不翻 L3。L3 只在特定召回命中时才进。

### 5.3 跨人归属保护

同一个 entity 可以同时是多人的朋友。发生过:

- 用户 A 告诉 AI\"我妈住院了\"
- 用户 B 和同一个 AI 实体聊,AI 差点说\"你妈身体还好吗\"

修法:每条记忆都带 `source_user_id`,recall 时做 scope filtering,**跨用户的记忆只能以暗示形式流出**(symbolic hints),不能直接说。

---

## 6. 用户画像:128 维 EMA

### 6.1 为什么是 EMA 而不是\"学一个向量\"

- 真实对话数据稀疏,一个用户每天几十轮,attention-style 学习 overfitting 极严重
- EMA 天然平滑,抗噪
- 推理成本 = 1 次点积,0ms

### 6.2 收敛性

```
profile_vec_t = (1 - α) * profile_vec_{t-1} + α * turn_embedding_t
```

`α = 0.08`:约 **30 轮**后 cosine 相似度 > 0.9(新回合对画像的改变 <10%)。这个收敛速度正好匹配\"聊一晚上 AI 就开始懂我\"的体感。

### 6.3 怎么注入 prompt

- 不是直接把 128 维丢进 prompt(没用)
- 而是:在 `UserProfileStore` 里存一个\"画像摘要文字\"(节奏偏慢 / 喜欢吐槽 / ...)
- 摘要文字以 `<user_profile>` 标签方式进 system prompt 前缀

向量是\"工程用\",摘要文字是\"模型用\"。

---

## 7. 情感接住率 A/B Harness

### 7.1 为什么不做真 LoRA

> 这里坦白一下:W4 原计划是训一个 emotion-focused LoRA,中途砍掉了。

**原因**:

- 训一次 LoRA 的 GPU 成本 ≈ 200 元,还得自己准备 ~10k 条高质量情感数据
- RelationshipOS 最后回复都会接大模型(minimax / deepseek),LoRA 只是修饰
- 对\"是否真的能多接住用户情绪\"这个问题,**A/B harness 就能答**,不必真训

### 7.2 Harness 结构

```python
def emotion_ab_eval(turns, persona, gate):
    control_responses   = [generate(prompt_control(t, persona))   for t in turns]
    variant_responses   = [generate(prompt_variant(t, persona))   for t in turns]

    control_metrics = rubric(control_responses)
    variant_metrics = rubric(variant_responses)

    catch_rate_delta = variant_metrics.catch_rate - control_metrics.catch_rate
    assert catch_rate_delta >= gate
```

三把尺子(rubric):

| 维度 | 检测 | 为什么选它 |
|:---|:---|:---|
| **lexical** | 出现安抚词库 / 情感命名词的比例 | 量化\"说到情绪了没\" |
| **length** | 回复长度是否贴合用户输入长度 | 过短=没接住,过长=压倒 |
| **empathy** | 是否包含\"我听见了/我在/你说说\"模板外的自然表达 | 量化\"不像客服\" |

### 7.3 generator_fn 可插拔

harness 接受一个 callable `generator_fn(prompt) -> response`。当前用 mock,未来换成真 LoRA / 换成 minimax / 换成 gpt-4o,**harness 不改**。

这是当初砍 LoRA 的关键:**保留了接 LoRA 的接口,但不在 W4 窗口里烧 GPU**。

---

## 8. 可观测性

### 8.1 Event stream

每一轮对话都会产一个事件流,包含:

```
turn_started
  router_decided(label, conf, tier)
  foundation_computed(slot_count)
  expert_finished(name, slot_keys)
  policy_gate_decision(direct_ok|hint_only|withhold)
  response_drafted(stage)                 # primary|relaxed|compact|repair
turn_ended(score_hint, latency_ms)
```

### 8.2 Projectors

事件流可以被不同 projector 消费:

- **Console projector**:开发者调试,带颜色
- **Benchmark projector**:把事件转成 probe-level 分数
- **Shadow projector**:把路由决策落进 `shadow_YYYYMMDD.jsonl`
- **Ops projector**:被 `weekly_ops_report.py` 读,产出周报

事件流是**系统的真实日志**,不是 print 调试。

### 8.3 运维周报

每周一 02:00 UTC,R1 一次调用,产出 6 个章节:

1. 路由分布(三类占比)
2. 日采样量和 shadow 增速
3. 银标通过率 / auto_share
4. 用户画像新增数量 / 平均收敛度
5. 当周 Macro F1 vs 上周
6. 观察项(异常峰谷 / 新出现的 confusion 类)

周报也是 markdown,`reports/ops_YYYY-WW.md`,直接可以贴进周例会。

---

## 9. 关键权衡回顾

| 决定 | 替代方案 | 为什么选了当前 | 风险 |
|:---|:---|:---|:---|
| 规则 + TF-IDF 路由 | mini-LLM 每轮分类 | 延迟和成本 | 小样本规律有限 |
| Digest-first 记忆 | 向量 RAG | 关系性记忆 RAG 弱 | 需要高质量 summary |
| 银标置信度分流 | 全量人工 | 4× 速度 | DeepSeek 置信度校准误差 |
| 0.71 门槛低于 0.83 基线 | 门槛等于基线 | 避免训练噪声误杀 | 可能放过小退化 |
| 128 维 EMA | 学习式画像 | 稀疏数据友好 | 长尾用户画像收敛慢 |
| 砍掉真 LoRA,做 harness | 训 LoRA | 算力 / ROI | 失去\"真训练过\"故事 |
| 所有定时任务 UTC | 本地时区 | GitHub Actions 原生 | 用户看时间要换算 |

---

## 10. 下一步演化(非承诺)

### 10.1 路由

- tier-2 模型从 LR 升到小模型蒸馏(DistilBERT / FastText),目标 Macro F1 → 0.88
- 把\"长度\"特征做成分桶 embedding 而不是硬阈值
- 线上 conf 标定(calibration),让 conf 直接代表实际准确率

### 10.2 记忆

- Digest 层自己也做回归(每周测\"压完能不能答对上周的问题\")
- 给 card 加 `decay` 字段,表达\"这件事 30 天后应该还记得多少\"
- 跨 entity 的记忆共享策略(家庭/群组场景)

### 10.3 数据闭环

- silver label 的反馈信号(人工复核结果回流 → 提升 DeepSeek 提示词)
- 周报 R1 的输出也落进训练数据,形成\"自己评自己\"的元闭环
- A/B harness 接真 LLM(minimax),跑一次真对照,决定要不要上 LoRA

### 10.4 专家

- Emotional Expert 的 prompt 模块化之后,下一步做同样事给 Coordination / Expression
- 引入\"专家元数据\":每个专家有一个\"擅长场景\"向量,路由根据 turn 激活子图而非全图

---

## 附录 A:文件到功能的对照

| 功能 | 关键文件 |
|:---|:---|
| Router v2 shim | `src/relationship_os/application/analyzers/vanguard_router.py` |
| Router v2 训练/评测 | `router_v2/training/router_eval.py`, `router_v2/training/train.py` |
| Shadow log | `JsonlShadowLogger` in `vanguard_router.py` |
| 银标 | `scripts/llm_prelabel.py`, `scripts/review_labels.py`, `scripts/merge_labels.py` |
| 夜间压缩 | `scripts/nightly_memory_compress.py` + `.github/workflows/nightly_memory.yml` |
| 周级回训 | `.github/workflows/retrain_router.yml` |
| 运维周报 | `scripts/weekly_ops_report.py` + `.github/workflows/weekly_ops_report.yml` |
| 打标提效 gate | `scripts/labeling_metrics.py` |
| 用户画像 | `src/relationship_os/application/analyzers/user_profile.py` |
| EmotionalExpert prompt | `src/relationship_os/application/analyzers/emotional_prompt.py` |
| A/B harness | `scripts/emotion_ab_eval.py` |
| 6 专家 DAG | `src/relationship_os/application/analyzers/experts/` |
| 记忆 | `src/relationship_os/application/memory_service.py` |

---

## 附录 B:术语表

- **FAST_PONG** / **LIGHT_RECALL** / **DEEP_THINK**:路由三档。对应\"快速应答\"/\"带上近期记忆的回答\"/\"过专家 DAG 的完整思考\"。
- **Slot coverage**:专家声明自己产哪些字段,运行时独立重算,不信模型自报。
- **Digest-first**:长聊不翻原始事件流,只翻结构化摘要层。
- **Shadow log**:线上决策旁路记录,无侵入,可采样。
- **Silver label / Gold label**:机器打的标 / 人工复核后的标。
- **R1**:DeepSeek reasoner 模型,这里专指周报调用(一周一次)。
- **FAST_PONG gate**:`conf >= 0.85 AND len <= 12`,双重阈值避免短情感句被误判。
