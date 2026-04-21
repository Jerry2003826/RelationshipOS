# Router v1 → v2 迁移指南

## TL;DR

| 维度 | v1 | v2 |
|---|---|---|
| 类别数 | 2 (FAST_PONG / NEED_DEEP_THINK) | 3 (FAST_PONG / LIGHT_RECALL / DEEP_THINK) |
| 证据形式 | 20 个硬编码中文词 + 1 正则 + 1 次 mini-LLM JSON 调用 | 18 维特征 + 可热更的规则表 + 校准分类器 + 可选仲裁器 |
| 必调 mini-LLM | 每轮 1 次 | 只在 Tier 2 置信度 < 0.60 时触发 (≤15%) |
| 校准 | 无；mini-LLM 返回值直接当信任分 | 每类 IsotonicRegression,ECE ≤ 0.05 |
| 降级 | 异常时固定 FAST_PONG | CircuitBreaker + health_degraded 标记 |
| 可观测 | 只有 reason 字符串 | rule_hits / feature_scores / tier_timings_ms |
| 热更 | 改词需重启 | rules_zh.yaml 按 mtime 自动热加载 |
| 训练集 | 无 | seeds_zh.jsonl + 周级影子日志回训 |

## 代码变更

### 旧用法 (保留 ≥ 1 个 minor version)

```python
from relationship_os.application.analyzers.vanguard_router import VanguardRouter

router = VanguardRouter(...)
decision = await router.route(text)
if decision.route_type == "FAST_PONG":
    ...
```

### 新用法

```python
from relationship_os.application.analyzers.router.vanguard_router_v2 import (
    VanguardRouterV2,
)
from relationship_os.application.analyzers.router.shadow_logger import (
    JsonlShadowLogger,
)

router = VanguardRouterV2.from_default(
    call_llm=host_llm_client.fast_call,      # 可选；不传则只跑 Tier 0-2
    shadow_logger=JsonlShadowLogger("/var/log/router_shadow.jsonl"),
)

decision = router.decide(text)                # 同步；内部测得 <1ms
match decision.route_type:
    case "FAST_PONG":
        return pong_pipeline(text)
    case "LIGHT_RECALL":
        return light_pipeline(text, recent_memory=True)
    case "DEEP_THINK":
        return deep_pipeline(text)
```

### 灰度策略

1. **Week 0** — 部署 v2,保留旧 import 路径,仅启用 shadow 模式 (`enable_tier3=False`),
   用 `downgrade_to_legacy` 把 v2 决策降回 2 类交给旧 pipeline,只记 shadow 日志。
2. **Week 1** — 对比 v1 vs v2 在影子日志上的分布/延迟,通过 `router_eval.py`
   生成 Pareto 曲线。
3. **Week 2** — 把 10% 流量切到 v2 三类分流 (启用 Tier 3),监控:
   * FAST_PONG 回复 median 延迟是否 ↓
   * DEEP_THINK 误伤率 (用户反馈 + 人工抽检 200 条/天)
   * 降级率 (`health_degraded`) 应 <1%
4. **Week 3** — 100% 切换。legacy_shim 保留到 2026-Q4 删除。

### 导出运行时实现

`runtime_service.VanguardRouter` 改为:

```python
def decide_route(self, text: str) -> RouterDecisionV2:
    return self._v2.decide(text)
```

旧 `route()` 的 await 改写成同步 (v2 的热路径不做 I/O)。

## 数据迁移

* 影子日志格式见 `shadow_logger.py` 文件头。
* 已有线上日志如果仅含 `{route_type, text, ts}`,可通过 `build_labelled_set.py`
  的 `--seeds` 参数直接喂入作为弱监督标签。

## 已知不兼容

| 问题 | 影响面 | 规避 |
|---|---|---|
| 旧代码比较 `decision.route_type == "NEED_DEEP_THINK"` | 所有调度分支 | 使用 `downgrade_to_legacy(decision).route_type` 继续判 2 类 |
| 旧代码 `await router.route(...)` | 并发路径 | legacy_shim.VanguardRouter 仍是 async,直接换 import 即可 |
| 旧 reason 字符串 | 日志抽样/告警正则 | v2 reason 形如 `rule:safety.crisis` / `tier2` / `arbiter:<why>`,更新匹配即可 |

## 验收清单

- [ ] `pytest router_v2/tests -q` 全绿
- [ ] `router_eval.py --data <gold>` Macro F1 ≥ 0.85
- [ ] 影子日志写入正常,日均 ≥ 5k 条
- [ ] Tier 3 调用率 ≤ 15%
- [ ] p95 延迟 ≤ 200ms (含 Tier 3 超时)
- [ ] `health_degraded=True` 比例 < 1%
- [ ] CI retrain workflow 成功跑完一次
