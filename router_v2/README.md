# router_v2 — Vanguard Router 重写

旧 Vanguard Router (`src/relationship_os/application/analyzers/vanguard_router.py`) 只有 20 词正则
+ 一次 mini-LLM JSON 分类,无校准、无评估、无降级。这个目录是它的完整替代。

## 快速开始

```bash
pip install scikit-learn numpy pyyaml pytest

# 训练 Tier 2 (输出 model.joblib ≈ 2KB)
python router_v2/training/train_tier2.py \
    --data router_v2/training/training_zh.jsonl \
    --out  router_v2/policies/router/model.joblib

# 端到端评估
python router_v2/training/router_eval.py \
    --data router_v2/training/training_zh.jsonl \
    --dump-csv router_v2/training/eval_dump.csv

# 单元测试
python -m pytest router_v2/tests -q
```

Python API:

```python
from router_v2.analyzers.router.vanguard_router_v2 import VanguardRouterV2
from router_v2.analyzers.router.shadow_logger import JsonlShadowLogger

router = VanguardRouterV2.from_default(
    call_llm=my_fast_llm_client,            # 可选; 不传则跑纯 Tier 0-2
    shadow_logger=JsonlShadowLogger("/var/log/router_shadow.jsonl"),
)

decision = router.decide("还记得我上次说的那件事吗")
# decision.route_type  -> "LIGHT_RECALL"
# decision.confidence  -> 0.93
# decision.decided_by  -> "rule"
# decision.rule_hits   -> ("memory.explicit_recall",)
```

## 当前指标 (v2.1 · 2026-04-22 · 1091 条样本 · 70/15/15 分层划分)

数据:seeds 121 + silver 252 + **self-distilled 718 = 1091 条**,
按 seed=20260422 做 **70/15/15 分层划分** → train 764 / holdout 164 / **test 163 (冻结)**。
下表全部在**从未见过的 test split** 上测。

| 指标 | 目标 | v2.0 (self-eval) | **v2.1 (held-out test)** |
|---|---|---|---|
| 准确率 | — | 0.75 | **0.877** |
| Macro F1 | ≥ 0.85 | 0.71 | **0.876** |
| ECE | ≤ 0.05 | 0.04 | 0.058 |
| 规则命中率 | <5% | 2.1% | 1.8% |
| Tier 2 处理率 | — | 97.9% | 98.2% |
| p95 延迟 (不含 Tier 3) | ≤ 200ms | 0.29 ms | **0.31 ms** |
| 模型大小 | ≤ 500 KB | 2.1 KiB | 2.3 KiB |

三类 test F1:

| 类别 | P | R | F1 | n |
|---|---|---|---|---|
| FAST_PONG | 0.909 | 0.833 | **0.870** | 48 |
| LIGHT_RECALL | 0.875 | 0.918 | **0.896** | 61 |
| DEEP_THINK | 0.855 | 0.870 | **0.862** | 54 |

LIGHT_RECALL 从 v2.0 的 F1 0.52 提升到 **0.896**,
主要靠 (1) 718 条自蒸馏样本强化 casual-update 语域,
(2) 新增 `advice_seeking` / `continuity` 两类词典+特征用于区分
"向 AI 求规划" (DEEP) vs "向 AI 汇报/共享生活" (LIGHT)。

## 数据蒸馏故事

原始训练集只有 373 条, LIGHT_RECALL 仅 97 条, F1 长期卡 0.52。
**v2.1 做法:** 用一个强 LLM (Claude) 做老师,
按 3 类均衡手写 **767 条真人朋友聊天语料**, 覆盖:

- **LIGHT_RECALL (313):** 刚下班/按你说的/你还记得/今天终于…
- **DEEP_THINK (226):** 帮我分析/该不该辞职/两个 offer 选哪个/是不是我一直错了…
- **FAST_PONG (228):** 嗯/哈哈/晚安/在吗?/+1…
- **硬负样本:** 刻意造型似另一类但实际是本类的边缘样本,
  例如 "想你了 怎么办" (LIGHT 而非 DEEP)、
  "好累" 对比 "累成狗怎么办"、英文混入、emoji-only。

去重后 1091 条,按 seed 固定的分层划分,**test 集从训练起就冻结**,
保证 held-out 指标不会再被优化流程污染 (Goodhart)。
数据源标注在每条样本的 `source` 字段 (seed_gold / silver_llm / claude_distill),
方便后续只用真实线上影子日志复训。

## 特征向量 (20 维, 全部 [0,1])

表层 (8): 长度、超短、超长、问号、感叹、标点比、emoji 数、重复字;
词典 (7): memory_trigger / persona_probe / emotion_raw / self_disclosure / factual_query / entity / emotion_signed(带否定);
**v2.1 新增 (2): `advice_seeking` / `continuity`** — 专门分离 DEEP vs LIGHT;
语种/危机 (3): contains_crisis / contains_chinese / contains_latin。

## 目录结构

```
router_v2/
├── analyzers/router/
│   ├── contracts.py            # RouterDecisionV2 + downgrade_to_legacy
│   ├── features.py             # Tier 0 特征抽取 (18 维)
│   ├── rule_engine.py          # Tier 1 规则引擎 + 热加载
│   ├── tier2_classifier.py     # Tier 2 模型 + PriorClassifier 降级
│   ├── mini_llm_arbiter.py     # Tier 3 6-shot 仲裁器
│   ├── circuit_breaker.py      # 独立无依赖的断路器
│   ├── shadow_logger.py        # JSONL 影子日志
│   ├── vanguard_router_v2.py   # 级联主路径
│   └── legacy_shim.py          # 向后兼容的 async route()
├── policies/router/
│   ├── rules_zh.yaml           # 规则 (scored DSL)
│   ├── model.joblib            # 训练好的 Tier 2 (run train_tier2.py 生成)
│   └── lexicons/*.yaml         # 6 个词典
├── training/
│   ├── seeds_zh.jsonl          # 121 条金标种子
│   ├── silver_zh.jsonl         # 369 条人工银标
│   ├── distilled_claude.jsonl  # 767 条自蒸馏样本 (v2.1)
│   ├── training_zh.jsonl       # 764 条 train (70%)
│   ├── holdout_zh.jsonl        # 164 条 holdout (15%)
│   ├── test_zh.jsonl           # 163 条冻结 test (15%)
│   ├── build_distilled_dataset.py  # 70/15/15 分层划分
│   ├── train_tier2.py          # LogReg + Isotonic 校准
│   ├── router_eval.py          # Pareto eval 报告
│   └── build_labelled_set.py   # 影子日志 + seeds 合并
├── tests/test_router_v2.py     # 19 个单元/契约测试
├── docs/
│   ├── MIGRATION.md            # v1 → v2 迁移指南
│   └── blog_vanguard_router_v2.md  # 技术文章
└── .github/workflows/retrain_router.yml  # 周级自动回训
```
