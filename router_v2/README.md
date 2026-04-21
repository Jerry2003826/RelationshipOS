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

## 当前指标 (seeds 121 + silver 369 = 373 条训练集, self-eval)

| 指标 | 目标 | 实测 |
|---|---|---|
| 准确率 | — | 0.75 |
| Macro F1 | ≥ 0.85 | 0.71 |
| ECE | ≤ 0.05 | 0.04 |
| 规则命中率 | <5% | 2.1% |
| Tier 2 处理率 | — | 97.9% |
| p95 延迟 (不含 Tier 3) | ≤ 200ms | 0.29 ms |
| 模型大小 | ≤ 500 KB | 2.1 KiB |

三类 F1:FAST_PONG 0.86 / LIGHT_RECALL 0.52 / DEEP_THINK 0.75。
LIGHT_RECALL 是当前短板,线上影子日志继续补样本。
指标为训练集 self-eval, 373 条样本太少未划 held-out, 真实线上大概率更低。

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
│   ├── training_zh.jsonl       # 合并训练集 (373 条)
│   ├── train_tier2.py          # LogReg + Isotonic 校准
│   ├── router_eval.py          # Pareto eval 报告
│   └── build_labelled_set.py   # 影子日志 + seeds 合并
├── tests/test_router_v2.py     # 19 个单元/契约测试
├── docs/
│   ├── MIGRATION.md            # v1 → v2 迁移指南
│   └── blog_vanguard_router_v2.md  # 技术文章
└── .github/workflows/retrain_router.yml  # 周级自动回训
```
