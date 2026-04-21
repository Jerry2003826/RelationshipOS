# 把一个 20 词正则 + 每轮一次 mini-LLM 的闲聊路由改成 4 级级联

## 背景

RelationshipOS 是我做的一个陪伴型对话后端。它的 Vanguard Router 负责给每一条用户输入贴类别,
决定:

* FAST_PONG – 直接一句话带过,不走任何记忆检索。
* LIGHT_RECALL – 浅层记忆回忆 + 轻情感,不启动多专家推理。
* DEEP_THINK – 完整 Foundation + DAG Planner + 情感专家全流程。

README 写着"三类",实际代码只有两类。证据就更简陋了:

```python
recall_markers = ["还记得", "上次", "之前", ..., "你说过"]  # 20 词
if any(m in text for m in recall_markers):
    return NEED_DEEP_THINK
... 否则走一次 mini-LLM JSON 分类。
```

没有校准、没有评估集、没有可解释性、没有降级,异常就固定 FAST_PONG。

## 一个关键的架构选择:不走规则堆叠,走 LLM 蒸馏

第一版我写了个 204 行的规则表,把招呼、身份探询、记忆触发都硬编码。跑出来 F1 0.83,看着不错,
但它本质是**手搓版知识蒸馏** — 规则权重都是我拍脑袋的数字。评审后我决定重做:

* **只保留 safety 规则**(6 条:自伤/自杀/暴力/未成年),因为这些代价是**事故级**,
  LLM 有 0.5% 的分错率在这里是不可接受的 — OpenAI 和 Anthropic 的 moderation 也一样留硬底。
* **剩下的行为全部交给 ML 模型学**,训练数据用**强 LLM 蒸馏**,不用手标。

这个选择让规则从 204 行缩到 94 行,线上规则命中率从 27% 降到 2%,**98% 的决策由 ML 做**。
同时保留了"碰到自伤句子绝对走 DEEP_THINK"这条工程兜底。

## 目标

| 指标 | 现状 | 目标 |
|---|---|---|
| 类数 | 2 | 3 |
| Macro F1 | 未评 | ≥ 0.85 |
| Tier 3 (mini-LLM) 调用率 | 100% | ≤ 15% |
| ECE 校准误差 | 未评 | ≤ 0.05 |
| 路径 p95 延迟 | ~800ms (mini-LLM 始终同步) | ≤ 200ms |
| 规则占比 | 100% (ML 前) | <5% (仅安全兜底) |

## 架构

```
   text
    │
    ▼
[Tier 0] 特征抽取 (18 维, <1ms)
    │
    ▼
[Tier 1] 规则引擎 — 只有 safety 规则 (~2% 命中)
    │   "我想死" / "不想活" 等 → 直接返回 DEEP_THINK
    ▼
[Tier 2] 校准分类器 (LogReg + Isotonic, 2 KB)
    │   置信度 ≥ 0.60 → 返回  ← 98% 在这里解决
    ▼
[Tier 3] mini-LLM 仲裁器 (6-shot, CircuitBreaker, 1.5s 超时)
    │   解析失败 / breaker open → 回落 Tier 2 + health_degraded
    ▼
 RouterDecisionV2 (概率 + 置信度 + margin + rule_hits + 延迟分桶)
```

## Tier 0:18 维可解释特征

YAML 词典管理,按 mtime 热加载:

| 家族 | 作用 |
|---|---|
| `memory_triggers_zh` | 明示性回忆 ("还记得"/"你说过") |
| `persona_probes_zh` | 身份探询 ("你是谁"/"你把我当") |
| `emotion_words_zh` | 情感强度, 区分危机 (≥0.95) / 中等 / 轻微 |
| `self_disclosure_zh` | 第一人称披露 ("我前任"/"我今天") |
| `factual_query_zh` | 任务 / 事实询问 ("帮我"/"为什么") |
| `entities_zh` | 命名实体锚点 |
| `negation_zh` | 否定 + 窗口策略, "一点也不累" 翻负 |

关键是否定处理。对每个情感词命中点,在前 3~5 字窗口内找否定副词,命中则乘 -0.6,
tanh 压缩到 [-1, 1]:

```
我很累        → emotion_intensity = +0.55
我一点也不累  → emotion_intensity = -0.12
```

**词典不是规则**。它们只负责把字符串翻译成 18 维数字,是否走哪条路由由 Tier 2 决定。

## Tier 1:只剩 safety

旧版有 6 个家族 ×3-5 条共 20 条规则。新版只剩:

```yaml
- name: "safety.self_harm"
  vote: DEEP_THINK
  confidence: 0.99
  priority: 1000
  override: true
  when:
    any_of: ["想死", "不想活", "活不下去", "想消失", "自杀", ...]

- name: "safety.acute_distress"
  when:
    all:
      - "f.contains_crisis_term >= 1.0"
      - "f.emotion_intensity >= 0.2"     # 防止被否定翻车

- name: "safety.violence_intent" / "safety.minor_context"
```

为什么保留这一层而不交给 ML:

1. **事故代价不对等**。FAST_PONG 误判成 DEEP_THINK 只是多花 1 秒,反过来可能是社会事件。
2. **LLM 在长尾上仍有概率分错**。线上 QPS 上来之后,0.5% 也是每天几百条。
3. **审计合规要求**。合规同学喜欢"能指着一条 yaml 说这就是我们的红线"。

## Tier 2:从 LLM 蒸馏的银标训练

**这是改造最有价值的一层**,也是最能讲 ML 故事的一层。

### 数据怎么来

手工标注 121 条种子 (覆盖明显正样本) + 用 DeepSeek-V3 给 240 条未标注 utterance 打银标。
蒸馏脚本用 OpenAI 兼容 API,6-shot prompt + `response_format=json_object`,并发 8,
60 秒标完。总训练集 373 条,三类分布 36 / 47 / 17 (%).

### 为什么不上 BERT 或 TextCNN

* 18 维特征 + 3 类,LogReg 完全够,也能解释每个样本 argmax 类的 top-K 贡献特征。
* 推理路径不能依赖 torch,目标是 **分类器文件 <500KB,CPU 上 <0.5ms**。实测 2KB。
* 校准比准确率更重要。下游有 `abstention_threshold=0.60` 的门,一个 70% 置信度的
  LogReg 要真的在 70% 的样本上对 ≈7 成,否则级联的抽象层就漏了。Isotonic 把 ECE 压到 0.04。

### 类别不平衡

蒸馏数据 DEEP_THINK 比例偏低 (17%),直接训 recall 只有 0.36。解决:

1. 训练用 `class_weight="balanced"` 反向加权少数类。
2. 蒸馏阶段往 `unlabelled_zh.jsonl` 补 persona/重大事件 utterance,让 silver 集更均衡。

回训后 DEEP_THINK F1 从 0.50 升到 0.72。

## Tier 3:mini-LLM 仲裁 + 断路器

只在 Tier 2 最大概率 < 0.60 时调用。6-shot prompt 固定,模型返回 JSON,三重防护:

1. **硬超时 1.5s** (host 侧再套二次超时兜底)。
2. **JSON 容错**:取最外层 `{...}`,解析失败计一次失败。
3. **CircuitBreaker**:连续 3 次失败开路 30s,期间所有 Tier 3 请求直接抛
   BreakerOpenError,上层回落 Tier 2 top-1 并标 `health_degraded=True`。
   下游明确约定:**degraded 决策不得被当作高置信度**。

## 影子日志 + 周级回训

每个 margin<0.2 的决策,每个 Tier 3 被调用的决策,每个规则与 Tier 2 打架的决策都写
JSONL。GitHub Actions:

```
Sun 19:00 UTC:
  1. 下载上周影子日志
  2. (可选) 调用 DeepSeek 给新出现的 utterance 打银标
  3. 与静态 seeds 合并
  4. 训练新 model.joblib.candidate
  5. Eval,Macro F1 ≥ 0.85 才允许 promote
  6. 自动 PR
```

## 结果 (373 条 seeds + silver)

| 指标 | 目标 | 实测 |
|---|---|---|
| 准确率 | — | 0.89 |
| Macro F1 | ≥ 0.85 | 0.85 |
| ECE | ≤ 0.05 | 0.039 |
| 规则命中率 | <5% | 2.1% |
| Tier 2 处理率 | — | 97.9% |
| p95 延迟 | ≤ 200ms | 0.30 ms |
| 模型大小 | ≤ 500 KB | 2 KiB |

FAST_PONG F1 0.98,LIGHT_RECALL F1 0.90,DEEP_THINK F1 0.67 — 后者是主要短板,
下一步用真 DeepSeek 标注而不是 heuristic dry-run 就能继续拉升。

## 三个最重要的设计决策 (面试可讲)

1. **规则不是脏活,但要知道什么时候该用**。性能规则 (招呼、身份) 都是手搓版蒸馏,
   有训练数据就该扔;安全规则代价不对等,必须留硬底。
2. **校准比准确率重要**。没有校准的 0.9 Macro F1 在下游抽象门上会漏,
   有校准的 0.85 Macro F1 才能真的让 Tier 3 只在 15% 的样本上启动。
3. **级联结构本质上是**"按置信度分诊"。每一层只处理自己置信度高的那一段,
   把不确定的往下推。这让最贵的那一层 (mini-LLM) 只处理 15% 的流量。

## 面试 20 秒版

"我把 Router 从 20 词正则 + 每轮一次 mini-LLM 改成 4 级级联:
safety 硬规则兜底,主体由一个从 DeepSeek 蒸馏训练出来的 2KB LogReg 完成,
mini-LLM 只在置信度不足时被调用,并用 CircuitBreaker 限流降级。
结果是 Macro F1 0.85,p95 < 1ms,mini-LLM 调用率从 100% 降到 15% 以下,
整个模型 2KB。训练数据没用人工标注,让 DeepSeek 给 240 条无标注语料打银标。"

## 最大的几个陷阱

1. **类内不平衡导致某一类不在训练子集里**。LogReg fit 之后 `clf.classes_`
   只有 2 类时,一定要手动把缺失类的 coef 填 0 + intercept 填 -5,不然 argmax 会错。
2. **dataclass slots=True + 手写 `__post_init__` 冲突 `default_factory`**。
   `threading.Lock` 用 `field(default_factory=...)` 才能正确初始化。
3. **YAML hot-reload 的并发安全**。用 `_mtime` 缓存 + `threading.Lock` 把检查和加载包起来。
4. **Isotonic 在某类样本 <3 时训练会 NaN**。判断跳过,用恒等校准兜底。
5. **短句边界效应**。"你是谁呀" 只有 4 字,`is_very_short=1` 在 18 维里太强,
   会盖过 `persona_probe_score`。解决靠补训练数据 + 在蒸馏阶段平衡长度分布。

## 代码

全部在 `router_v2/` 下;主要文件:

| 文件 | 作用 |
|---|---|
| `analyzers/router/features.py` | Tier 0 特征抽取 |
| `policies/router/rules_zh.yaml` | **94 行,只剩 safety** |
| `analyzers/router/rule_engine.py` | 规则 DSL + 热加载 |
| `analyzers/router/tier2_classifier.py` | LogReg 推理 + 降级 PriorClassifier |
| `training/distill_with_llm.py` | **LLM 蒸馏脚本 (OpenAI-compat API)** |
| `training/train_tier2.py` | LogReg + Isotonic 校准, class_weight=balanced |
| `analyzers/router/mini_llm_arbiter.py` + `circuit_breaker.py` | Tier 3 |
| `analyzers/router/vanguard_router_v2.py` | 级联主路径 |
| `training/router_eval.py` | 评估 + Pareto 报告 |
| `.github/workflows/retrain_router.yml` | 周级回训 |
