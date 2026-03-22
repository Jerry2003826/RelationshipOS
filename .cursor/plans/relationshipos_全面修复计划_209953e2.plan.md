---
name: RelationshipOS 全面修复计划
overview: 将三轮深度审计发现的全部问题按依赖关系和优先级编排为 6 个阶段（Phase -1 到 Phase 4），从版本控制和数据安全开始，逐步推进到工程质量、架构泛化、可观测性和生产就绪。
todos:
  - id: phase-neg1
    content: "Phase -1: 版本控制与数据安全地基"
    status: completed
  - id: phase-0
    content: "Phase 0: 阻断性基础设施与安全危机"
    status: completed
  - id: phase-1
    content: "Phase 1: 工程质量与文件拆分"
    status: completed
  - id: phase-2
    content: "Phase 2: 核心数据结构泛化与强类型改造"
    status: completed
  - id: phase-3
    content: "Phase 3: LLM 基建增强与领域协同设计"
    status: completed
  - id: phase-4
    content: "Phase 4: 生产就绪与上线收口"
    status: completed
isProject: true
---

# RelationshipOS 全面修复计划

> **问题来源**：用户自查 15 条 + 三轮深度审计（API/安全 19 条、并发/生命周期 21 条、Event Sourcing/Projector 19 条、评测框架 30+ 条、主动系统/记忆 24 条、可观测性 20 条、Console/Domain/部署 66 条）。去重合并后共计 **约 120 条独立问题**。
>
> **编排原则**：每个 Phase 的产出是下一个 Phase 的前提。Phase 内部按"修一个不会破另一个"的原则排序。

---

## Phase -1：版本控制与数据安全地基

> **目标**：让项目具备最基本的工程可靠性——能回滚、能复现构建、能安全存储密钥。
> **预计工时**：0.5 天

### -1.1 初始化 Git 仓库


| 编号   | 问题                  | 来源    |
| ---- | ------------------- | ----- |
| O-04 | 项目目前不是 Git 仓库，无版本控制 | 第三轮审计 |


**具体动作**：

- `git init && git add -A && git commit -m "initial: snapshot before remediation"`
- 创建 `.gitignore`（排除 `.venv/`, `__pycache__/`, `.env`, `*.pyc`, `.pytest_cache/`）
- 后续每个 Phase 完成后打一个 tag（`phase-neg1-done`, `phase-0-done`, ...）

### -1.2 生成依赖锁文件


| 编号   | 问题                             | 来源    |
| ---- | ------------------------------ | ----- |
| O-16 | 所有依赖用 `>=` 无上限，无锁文件，构建不可复现     | 第三轮审计 |
| O-17 | `litellm>=1.74.0` 变化极快，无上限特别危险 | 第三轮审计 |


**具体动作**：

- `uv lock` 生成 `uv.lock`
- 将 `uv.lock` 加入 Git 追踪
- 考虑对 `litellm` 加 `<2.0` 上限

### -1.3 清除硬编码凭据


| 编号                | 问题                                                   | 来源        |
| ----------------- | ---------------------------------------------------- | --------- |
| H-1 / O-05 / O-15 | `config.py` 和 `alembic.ini` 中硬编码 `postgres:postgres` | 第一轮 + 第三轮 |
| O-13 / O-14       | `.env.example` 缺少 API Key 条目                         | 第三轮审计     |


**具体动作**：

- `config.py`：将 `database_url` 默认值改为空字符串，启动时若为空则 `raise ValueError("RELATIONSHIP_OS_DATABASE_URL must be set")`
- `alembic.ini`：改为 `sqlalchemy.url = %(RELATIONSHIP_OS_DATABASE_URL)s`，通过 `alembic/env.py` 注入
- `.env.example`：补齐 `RELATIONSHIP_OS_LLM_API_KEY=`、`OPENAI_API_KEY=` 等必要变量

---

## Phase 0：阻断性基础设施与安全危机

> **目标**：修复所有会导致"生产环境数据损坏、安全漏洞、或内存爆炸"的问题。
> **预计工时**：3-5 天

### 0.1 Event Store 分页与 OOM 修复


| 编号    | 问题                                                  | 来源    |
| ----- | --------------------------------------------------- | ----- |
| 用户-4  | `PostgresEventStore.read_stream()` 用 `.all()` 全量加载  | 用户自查  |
| 并发-14 | `PostgresEventStore.read_all()` 同样无分页全量加载           | 第一轮审计 |
| 并发-4  | `StreamService.list_stream_ids()` 加载所有事件仅为提取 ID     | 第一轮审计 |
| ES-15 | `list_stream_ids()` 应使用 `SELECT DISTINCT stream_id` | 第一轮审计 |


**具体动作**：

```python
# EventStore Protocol 增加分页接口
class EventStore(Protocol):
    async def read_stream(
        self, *, stream_id: str,
        after_version: int = 0,
        limit: int | None = None,
    ) -> list[StoredEvent]: ...

    async def read_all(
        self, *, after_version: int = 0,
        limit: int = 1000,
    ) -> AsyncIterator[StoredEvent]: ...

    async def list_stream_ids(self) -> list[str]: ...
```

- `PostgresEventStore`：`read_stream` 加 `WHERE version > after_version LIMIT limit`；`read_all` 改为游标分页的 `AsyncIterator`；新增 `list_stream_ids` 直接 `SELECT DISTINCT stream_id`
- `InMemoryEventStore`：对应实现，`read_all` 加排序（修复 ES-6）

### 0.2 Projector Snapshotting 机制


| 编号   | 问题                                             | 来源    |
| ---- | ---------------------------------------------- | ----- |
| 用户-3 | `SessionRuntimeProjector.apply()` 对超级状态字典做全量拷贝 | 用户自查  |
| ES-4 | 无快照策略，每次投影从头回放全部事件                             | 第一轮审计 |


**具体动作**：

- 在 `Projector` Protocol 中增加 `def snapshot_interval(self) -> int`（默认 100）
- `StreamService.project_stream` 改为：先尝试读取最近的 snapshot event → 从 snapshot 开始 apply 后续事件
- 每 N 个事件自动写入 `PROJECTION_SNAPSHOT_CREATED` 事件
- `SessionRuntimeProjector.apply()` 内部改为 in-place 更新（去掉全量 `dict(state)` 拷贝），用 `copy()` 仅在需要分叉时使用

### 0.3 轮询热路径 O(N) 全量扫描修复


| 编号    | 问题                                                  | 来源    |
| ----- | --------------------------------------------------- | ----- |
| 并发-3  | `JobService._list_job_records()` 在 0.5s 轮询中全量扫描所有事件 | 第一轮审计 |
| 并发-20 | `claim_job` 双重全量扫描 O(N*M)                           | 第一轮审计 |
| 主动-2  | `list_followups` 全量扫描所有 session，O(2N) I/O 每周期       | 第二轮审计 |


**具体动作**：

- `JobService`：维护一个内存中的 `_job_index: dict[str, JobRecord]`，通过事件订阅增量更新，不再每次全量扫描
- `ProactiveFollowupService.list_followups`：引入增量 dirty 标记，只重新评估自上次轮询以来有新事件的 session

### 0.4 API 认证与安全加固


| 编号         | 问题                   | 来源        |
| ---------- | -------------------- | --------- |
| C-1 / O-09 | 完全无认证/授权             | 第一轮 + 第三轮 |
| C-2        | `streams` 路由允许任意事件写入 | 第一轮审计     |
| H-2 / O-12 | 无速率限制                | 第一轮 + 第三轮 |
| H-3        | WebSocket 无认证、无连接管理  | 第一轮审计     |
| H-5 / O-10 | 无 CORS 配置            | 第一轮 + 第三轮 |
| O-11       | 无安全 HTTP 头           | 第三轮审计     |
| M-6        | 无请求体大小限制             | 第一轮审计     |


**具体动作**：

```python
# dependencies.py — 加 API Key 认证
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
    container: RuntimeContainer = Depends(get_container),
) -> None:
    if container.settings.api_key and api_key != container.settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

- `Settings` 加 `api_key: str = ""`
- `main.py` 加 `CORSMiddleware`、`TrustedHostMiddleware`
- 加安全头中间件（`X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`）
- `streams.py`：`event_type` 加白名单校验
- `TurnRequest.content`：加 `max_length=10_000`
- `AppendEventsRequest.events`：加 `max_items=50`
- WebSocket：加 Origin 校验 + 连接数上限 + 心跳超时

### 0.5 输入验证与错误处理


| 编号  | 问题                                         | 来源    |
| --- | ------------------------------------------ | ----- |
| M-1 | `session_id`、`content`、`metadata` 无长度/格式校验 | 第一轮审计 |
| M-2 | 大量端点缺少错误处理（404、LLM 超时等）                    | 第一轮审计 |
| M-4 | 响应缺少 Pydantic 模型                           | 第一轮审计 |
| H-4 | `/runtime` 暴露内部基础设施信息                      | 第一轮审计 |
| M-7 | `rebuild` 和 `dispatch` 等危险操作无保护            | 第一轮审计 |


**具体动作**：

- `CreateSessionRequest.session_id`：加 `max_length=128, pattern=r"^[a-zA-Z0-9_-]+$"`
- `TurnRequest.content`：加 `min_length=1, max_length=10_000`
- `metadata`：加 Pydantic `model_validator` 限制深度/大小
- 所有 `get_session` 类端点：stream 不存在时返回 404
- `process_turn`：捕获 LLM 超时/失败，返回 503
- 为核心 API 添加 Pydantic 响应模型（`SessionResponse`, `TurnResponse`, `RuntimeOverview`）
- `/runtime` 端点在生产环境隐藏敏感字段

### 0.6 Shutdown 安全与并发修复


| 编号    | 问题                                               | 来源    |
| ----- | ------------------------------------------------ | ----- |
| 并发-7  | `RuntimeContainer.shutdown()` 不容忍部分失败            | 第一轮审计 |
| 并发-8  | `ProactiveFollowupDispatcher.shutdown` 清理顺序错误    | 第一轮审计 |
| 并发-9  | `JobExecutor.shutdown` 孤儿任务泄漏窗口                  | 第一轮审计 |
| 并发-10 | `JobExecutor` 无并发任务上限                            | 第一轮审计 |
| 并发-11 | `RuntimeService` 无 per-session 锁，浪费 LLM 调用       | 第一轮审计 |
| 并发-19 | `RuntimeEventBroker.shutdown` 不通知等待中的 subscriber | 第一轮审计 |


**具体动作**：

```python
# container.py — 容忍部分失败的 shutdown
async def shutdown(self) -> None:
    results = await asyncio.gather(
        self.proactive_followup_dispatcher.shutdown(),
        self.job_executor.shutdown(),
        self.runtime_event_broker.shutdown(),
        return_exceptions=True,
    )
    for result in results:
        if isinstance(result, Exception):
            logger.error("shutdown_component_failed", error=str(result))
    if self.database_engine is not None:
        await self.database_engine.dispose()
```

- `ProactiveFollowupDispatcher.shutdown`：先 cancel + await poller，再 clear active_dispatches
- `JobExecutor`：加 `_max_concurrent_tasks: int = 10` 信号量；shutdown 时先获取 snapshot 再 cancel
- `RuntimeService`：加 per-session `asyncio.Lock` 字典，防止同一 session 并发 LLM 调用
- `RuntimeEventBroker.shutdown`：向每个 queue 放入 sentinel `None`，subscriber 收到后退出

### 0.7 Event Store 并发正确性修复


| 编号   | 问题                                                          | 来源    |
| ---- | ----------------------------------------------------------- | ----- |
| ES-2 | `expected_version=None` 时仍可能抛出 `OptimisticConcurrencyError` | 第一轮审计 |
| 并发-1 | `InMemoryEventStore` 读操作未持锁                                 | 第一轮审计 |
| ES-8 | 无全局序列号，依赖 `occurred_at` 排序不可靠                               | 第一轮审计 |
| ES-9 | 事件 payload 零验证                                              | 第一轮审计 |


**具体动作**：

- `PostgresEventStore.append`：当 `expected_version=None` 时，`IntegrityError` 应自动重试（读新版本号后重试 INSERT），而非抛出 `OptimisticConcurrencyError`
- `InMemoryEventStore`：`read_stream` 和 `read_all` 也加锁
- `event_records` 表加 `global_position BIGSERIAL` 列，`read_all` 按 `global_position` 排序
- 迁移新增 `event_type` 索引和 `CHECK(version > 0)` 约束
- 考虑对核心事件类型加 payload schema 校验（至少校验必需字段存在）

### 0.8 测试基建搭建


| 编号   | 问题                           | 来源    |
| ---- | ---------------------------- | ----- |
| 用户-5 | 缺乏核心 Builder 的单元测试和边界测试      | 用户自查  |
| Q-20 | 76,000 行源码仅 11 个测试文件         | 第三轮审计 |
| Q-22 | 全部使用同步 TestClient，无 async 测试 | 第三轮审计 |


**具体动作**：

```
tests/
├── conftest.py              # 共享 fixture：client, container, session_with_turn
├── unit/
│   ├── test_context.py      # infer_dialogue_act, infer_bid_signal 等
│   ├── test_relationship.py # build_relationship_state 边界测试
│   ├── test_strategy.py     # build_policy_gate, build_strategy_decision
│   └── test_memory.py       # recall, integrity, forgetting
├── integration/
│   ├── test_sessions.py     # (已有，迁移)
│   ├── test_runtime_ws.py   # (已有，迁移)
│   └── test_event_store.py  # Postgres + InMemory 一致性测试
└── e2e/
    ├── test_evaluations.py  # (已有，迁移)
    └── test_scenarios.py    # (已有，迁移)
```

- 创建 `tests/conftest.py`：共享 `client` fixture、`mock_llm_client` fixture
- 给 10 个最核心的 builder 函数写单元测试（`infer_dialogue_act`, `build_context_frame`, `build_relationship_state`, `build_confidence_assessment`, `build_policy_gate`, `build_strategy_decision`, `build_rehearsal_result`, `build_empowerment_audit`, `build_expression_plan`, `build_system3_snapshot`）
- 重点测试边界情况：r_vector 值域守恒、dependency 检测、连续 100 轮不溢出
- 加 `pytest-asyncio` 异步测试用例覆盖并发场景

---

## Phase 1：工程质量与文件拆分

> **目标**：把 7 个巨型文件拆分到可维护的大小，同时补齐 docstring 和错误处理。
> **预计工时**：3-5 天

### 1.1 拆分 `analyzers.py`（26,990 行 → ~15 个子模块）


| 编号   | 问题                   | 来源    |
| ---- | -------------------- | ----- |
| 用户-1 | 2.6 万行的 analyzers.py | 用户自查  |
| Q-01 | 单文件巨石，极难维护           | 第三轮审计 |


**目标结构**：

```
application/analyzers/
├── __init__.py              # re-export 所有 public 函数（向后兼容）
├── _utils.py                # _clamp, _compact, _contains_chinese, _contains_any (~50 行)
├── _constants.py            # DEFAULT_R_VECTOR, 所有硬编码阈值 (~100 行)
├── context.py               # build_context_frame, infer_* (~200 行)
├── relationship.py          # build_relationship_state, build_repair_* (~400 行)
├── cognition.py             # build_confidence, build_knowledge_boundary, build_private_judgment (~400 行)
├── strategy.py              # build_policy_gate, build_strategy_decision, build_rehearsal_result (~500 行)
├── expression.py            # build_expression_plan, build_empowerment_audit (~300 行)
├── response.py              # build_response_draft_plan, _rendering_policy, _post_audit, _sequence, _output_units, _normalization (~800 行)
├── coordination.py          # build_runtime_coordination, build_guidance_plan, build_cadence, build_ritual, build_somatic (~600 行)
├── proactive/
│   ├── __init__.py
│   ├── directive.py         # build_proactive_followup_directive, build_proactive_cadence_plan (~400 行)
│   ├── scheduling.py        # scheduling, guardrail, progression, orchestration (~600 行)
│   ├── dispatch.py          # gate, envelope, feedback, refresh, replan (~800 行)
│   ├── controllers.py       # stage/line/orchestration/aggregate controllers (~1000 行)
│   └── lifecycle.py         # 泛化后的 lifecycle 状态机（Phase 2 完成）
├── governance.py            # build_system3_snapshot + 所有 governance 维度 (~2000 行，Phase 2 进一步缩减)
├── session.py               # build_session_directive, build_inner_monologue, build_session_snapshot, build_archive_status (~500 行)
├── reengagement.py          # build_reengagement_matrix_assessment, build_reengagement_plan, build_reengagement_output_units (~600 行)
├── quality.py               # build_runtime_quality_doctor_report, build_offline_consolidation_report (~500 行)
└── followup_message.py      # build_proactive_followup_message (~400 行)
```

**迁移策略**：

1. 先创建 `analyzers/` 目录 + `__init__.py` 全量 re-export
2. 逐个模块搬迁函数，每搬一个跑一次 `pytest`
3. `from relationship_os.application.analyzers import build_context_frame` 对外保持不变

### 1.2 拆分 `runtime_service.py`（6,334 行）


| 编号   | 问题                     | 来源   |
| ---- | ---------------------- | ---- |
| 用户-2 | God Object + Import 黑洞 | 用户自查 |


**具体动作**：

- 将 `dispatch_proactive_followup` 方法（约 2500 行）抽离为 `ProactiveDispatchHandler` 类
- 将 LLM prompt 构建逻辑（约 500 行）抽离为 `LLMPromptBuilder`
- `RuntimeService` 本体保留 `process_turn`、`create_session`、`list_sessions` 核心方法
- Import 从显式列举改为 `from relationship_os.application import analyzers`，用 `analyzers.build_context_frame(...)` 调用

### 1.3 拆分 `evaluation_service.py`（13,914 行）


| 编号      | 问题                                    | 来源    |
| ------- | ------------------------------------- | ----- |
| Q-02    | 单文件 13,914 行                          | 第三轮审计 |
| 评测-A.1  | `TurnRecord` 有 130+ 个字段               | 第二轮审计 |
| 评测-12.1 | `_build_session_summary` 中 500+ 次列表推导 | 第二轮审计 |


**具体动作**：

- 拆为 `evaluation/summary_builder.py`（build_session_summary）、`evaluation/metrics.py`（指标计算）、`evaluation/reports.py`（报告生成）、`evaluation/service.py`（API 入口）
- `_build_session_summary` 从 500 次 O(n) 遍历改为**单次遍历 + 累加器字典**
- `TurnRecord` 拆分为基础字段 + 按需加载的扩展字段

### 1.4 拆分 `proactive_followup_service.py`（7,007 行）


| 编号    | 问题                                    | 来源    |
| ----- | ------------------------------------- | ----- |
| 主动-22 | `_build_followup_item` 是 6500+ 行的单一方法 | 第二轮审计 |
| Q-03  | 文件 7,007 行                            | 第三轮审计 |


**具体动作**：

- `_build_followup_item` 拆为：`_evaluate_directive()`, `_evaluate_scheduling()`, `_evaluate_lifecycle_chain()`, `_evaluate_queue_status()`
- 每个子方法独立可测试

### 1.5 拆分 `console.py`（6,736 行）


| 编号   | 问题                              | 来源    |
| ---- | ------------------------------- | ----- |
| C-10 | Python + HTML + CSS + JS 混合在单文件 | 第三轮审计 |
| Q-04 | 6,736 行                         | 第三轮审计 |


**具体动作**：

- CSS 提取为 `static/console.css`
- JS 提取为 `static/console.js`
- HTML 渲染函数按面板拆分为 `console/overview.py`, `console/sessions.py`, `console/evaluations.py`, `console/scenarios.py`
- 路由保留在 `console.py`，函数从子模块导入

### 1.6 添加 `@safe_build` 装饰器


| 编号    | 问题                     | 来源   |
| ----- | ---------------------- | ---- |
| 用户-15 | 170+ 个 builder 函数无异常保护 | 用户自查 |


**具体动作**：

```python
# analyzers/_safe.py
from functools import wraps
from typing import TypeVar, Callable, Any
import structlog

T = TypeVar("T")
logger = structlog.get_logger("analyzers")

def safe_build(default_factory: Callable[[], T]):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.exception("builder_failed", builder=func.__name__)
                return default_factory()
        return wrapper
    return decorator
```

- 给所有 `build_*` 函数添加 `@safe_build`
- 每个函数定义对应的安全默认值

### 1.7 提取硬编码常量


| 编号     | 问题                                | 来源    |
| ------ | --------------------------------- | ----- |
| 用户-10  | 大量魔法数字（Trust +0.05, Delay 6300 等） | 用户自查  |
| 评测-2.1 | 场景阈值全部硬编码                         | 第二轮审计 |
| 评测-2.2 | 质量扣分权重硬编码                         | 第二轮审计 |


**具体动作**：

- 创建 `analyzers/_constants.py`：所有关系增量、延迟时间、阈值集中定义
- 创建 `evaluation/_constants.py`：评测阈值、扣分权重、审查预算
- 后续可通过环境变量 / 配置文件覆盖

---

## Phase 2：核心数据结构泛化与强类型改造

> **目标**：消灭大规模代码重复，引入类型安全，让新增维度/阶段的成本从"几百行代码"降到"一行注册"。
> **预计工时**：4-6 天

### 2.1 Lifecycle 状态机泛化


| 编号          | 问题                                          | 来源    |
| ----------- | ------------------------------------------- | ----- |
| 用户-6        | 50+ 个 lifecycle builder 函数和 dataclass 复制粘贴  | 用户自查  |
| D-05 / D-06 | 30+ 个 contracts dataclass 几乎完全相同            | 第三轮审计 |
| 主动-15       | reject 路径仍然全量执行 50+ lifecycle decision      | 第二轮审计 |
| 主动-16       | 尾部 lifecycle 层级(substrate/stratum/layer)不可达 | 第二轮审计 |


**具体动作**：

```python
# domain/contracts.py — 替换 30+ 个 dataclass
@dataclass(slots=True, frozen=True)
class ProactiveLifecycleStageDecision:
    stage_name: str               # "activation", "settlement", ..., "stratum"
    status: str
    stage_key: str
    current_stage_label: str
    lifecycle_state: str
    parent_mode: str
    current_mode: str
    decision: str
    actionability: str
    changed: bool
    active_stage_label: str | None = None
    next_stage_label: str | None = None
    queue_override_status: str | None = None
    remaining_stage_count: int = 0
    line_state: str = "steady"
    line_exit_mode: str = "stay"
    additional_delay_seconds: int = 0
    selected_strategy_key: str = "none"
    selected_pressure_mode: str = "none"
    selected_autonomy_signal: str = "none"
    selected_delivery_mode: str = "none"
    primary_source: str = "parent"
    parent_decision: str | None = None
    active_sources: tuple[str, ...] = ()    # 改为 tuple 避免可变性
    stage_notes: tuple[str, ...] = ()
    rationale: str = ""
```

```python
# analyzers/proactive/lifecycle.py — 配置驱动
LIFECYCLE_CHAIN: tuple[str, ...] = (
    "activation", "settlement", "closure", "handoff",
    "continuation", "sustainment", "stewardship",
    "guardianship", "oversight", "assurance", "attestation",
    # ... 可按需增减
)

def build_proactive_lifecycle_stage_decision(
    *, stage_name: str,
    parent_decision: ProactiveLifecycleStageDecision | None,
    lifecycle_root_decision: ProactiveLifecycleActivationDecision,
    ...
) -> ProactiveLifecycleStageDecision:
    """一个函数处理所有 lifecycle 阶段。"""
    ...
```

- 删除 30+ 个旧 dataclass 和对应的 30+ 个 builder 函数
- 事件类型也从 60+ 个常量合并为 `PROACTIVE_LIFECYCLE_STAGE_UPDATED`，payload 中带 `stage_name`
- 审计减去的尾部死代码约 **~12,000 行**

### 2.2 Governance 维度注册表化


| 编号   | 问题                               | 来源    |
| ---- | -------------------------------- | ----- |
| 用户-7 | 20+ 治理维度扁平铺开塞在 System3Snapshot 中 | 用户自查  |
| D-07 | System3Snapshot 100+ 个字段         | 第三轮审计 |


**具体动作**：

```python
@dataclass(slots=True, frozen=True)
class GovernanceDimension:
    name: str               # "safety", "trust", "repair", ...
    status: str             # "stable", "watch", "recenter"
    target: str
    trigger: str
    trajectory_status: str
    trajectory_target: str
    trajectory_trigger: str
    notes: tuple[str, ...] = ()

@dataclass(slots=True, frozen=True)
class System3Snapshot:
    identity_anchor: str
    growth_stage: str
    moral_reasoning_status: str
    moral_posture: str
    # ... 核心非治理字段 (~20 个)

    governance: dict[str, GovernanceDimension] = field(default_factory=dict)
    # governance["safety"] → GovernanceDimension(...)
    # governance["trust"]  → GovernanceDimension(...)
```

- 新增治理维度只需**加一行注册**
- `build_system3_snapshot` 中用循环构建 governance dict
- Console 和评测用 `for name, dim in snapshot.governance.items()` 渲染
- 预计减少 System3Snapshot 从 100+ 字段到 ~30 字段

### 2.3 Pydantic 替换手工反序列化


| 编号   | 问题                                           | 来源   |
| ---- | -------------------------------------------- | ---- |
| 用户-8 | `runtime_service.py` 中大量 `state.get()` 硬编码解析 | 用户自查 |


**具体动作**：

- 将 `contracts.py` 中需要从 event payload 反序列化的关键 dataclass 改为 `pydantic.BaseModel`（保留 `frozen=True` 语义用 `model_config = ConfigDict(frozen=True)`）
- 替换 `runtime_state.get("system3_snapshot", {})` 为 `System3Snapshot.model_validate(raw_dict)`
- 逐步迁移，先从 `System3Snapshot`、`ContextFrame`、`RelationshipState` 开始

### 2.4 字符串魔术值替换为 Enum / Literal


| 编号   | 问题                                     | 来源    |
| ---- | -------------------------------------- | ----- |
| 用户-9 | 全局充斥 "hold", "stable", "none" 等字符串控制信号 | 用户自查  |
| D-13 | 所有枚举字符串字段都是 `str`，无类型约束                | 第三轮审计 |


**具体动作**：

```python
# domain/enums.py
from enum import StrEnum

class QueueStatus(StrEnum):
    HOLD = "hold"
    WAITING = "waiting"
    SCHEDULED = "scheduled"
    DUE = "due"
    OVERDUE = "overdue"

class GovernanceStatus(StrEnum):
    STABLE = "stable"
    WATCH = "watch"
    RECENTER = "recenter"

class TrajectoryStatus(StrEnum):
    STABLE = "stable"
    WATCH = "watch"
    HOLD = "hold"
    ADVANCE = "advance"
    REDIRECT = "redirect"
```

- 先从高频使用的枚举开始（QueueStatus, GovernanceStatus, TrajectoryStatus, DecisionAction）
- 配合 `mypy --strict` 逐步推进

### 2.5 Domain 层充血化


| 编号    | 问题                                  | 来源    |
| ----- | ----------------------------------- | ----- |
| 用户-14 | contracts.py 沦为纯容器，领域逻辑全在 analyzers | 用户自查  |
| D-12  | 所有 dataclass 无 `__post_init__` 验证   | 第三轮审计 |
| D-11  | `approved: bool = True` 默认通过审计      | 第三轮审计 |
| D-01  | frozen dataclass 中的 list/dict 仍可变   | 第三轮审计 |


**具体动作**：

- 关键值对象加 `@property` 方法（`is_high_risk`, `is_trust_low`）
- 加 `with_delta(**deltas)` 返回不可变副本的工厂方法
- 加 `__post_init__` 验证：`ConfidenceAssessment.score` 在 [0,1]；`approved` 字段**无默认值**（强制显式设置）
- 将 `list` 字段改为 `tuple`，`dict` 字段改为 `MappingProxyType` 包装，彻底不可变

### 2.6 Projector 正确性修复


| 编号          | 问题                                                | 来源    |
| ----------- | ------------------------------------------------- | ----- |
| ES-1        | `SCENARIO_BASELINE_SET/CLEARED` 未被任何 Projector 处理 | 第一轮审计 |
| ES-3        | `SESSION_DIRECTIVE_UPDATED` 覆盖多字段且不更新计数器          | 第一轮审计 |
| ES-5        | `SessionTranscriptProjector` 使用硬编码字符串             | 第一轮审计 |
| ES-12/13/14 | InnerMonologue/Snapshot/Runtime projector 无界增长    | 第一轮审计 |


**具体动作**：

- `SessionTranscriptProjector`：改用 `USER_MESSAGE_RECEIVED` / `ASSISTANT_MESSAGE_SENT` 常量
- `SESSION_DIRECTIVE_UPDATED` 处理器：对覆盖的字段同步递增 `_count`
- 所有 projector 的 list 字段加最大长度限制：`messages[-500:]`, `inner_monologue[-200:]`, `snapshots[-50:]`
- 为 `SCENARIO_BASELINE_SET/CLEARED` 添加对应的 projector 处理

---

## Phase 3：LLM 基建增强与领域协同设计

> **目标**：让认知推理从规则引擎升级为真正的 LLM 辅助推理；加强 LLM 基础设施的可靠性。
> **预计工时**：3-5 天

### 3.1 核心推理函数接入 LLM


| 编号    | 问题                   | 来源   |
| ----- | -------------------- | ---- |
| 用户-11 | 全部分析管道没有调用 LLMClient | 用户自查 |


**具体动作**：

- 实现 "Heuristic First, LLM Fallback" 模式
- 第一批接入的函数（按歧义度排序）：
  1. `infer_dialogue_act` — 关键词匹配 → LLM 分类
  2. `infer_appraisal` — 情绪词匹配 → LLM 情感分析
  3. `infer_bid_signal` — 模式匹配 → LLM 意图识别
  4. `build_private_judgment` — 规则推理 → LLM 综合判断
  5. `build_rehearsal_result` — 模拟预测 → LLM 预演
  6. `build_strategy_decision` — 策略选择 → LLM 辅助决策
  7. `build_proactive_followup_message` — 消息文案 → LLM 生成
  8. `build_offline_consolidation_report` — 离线总结 → LLM 归纳
- 保留规则作为 fallback，Mock 模式测试不受影响

### 3.2 Structured Output / JSON Mode


| 编号    | 问题                               | 来源   |
| ----- | -------------------------------- | ---- |
| 用户-12 | `LiteLLMClient` 不支持 JSON Mode 输出 | 用户自查 |


**具体动作**：

```python
@dataclass(slots=True, frozen=True)
class LLMRequest:
    messages: list[LLMMessage]
    system_prompt: str = ""
    model: str | None = None
    max_tokens: int = 400
    temperature: float = 0.7
    tools: list[LLMToolDefinition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    response_format: dict[str, Any] | None = None  # NEW: {"type": "json_object"} 或 JSON Schema
```

- `LiteLLMClient._invoke_completion`：将 `response_format` 透传给 litellm
- 为每个 LLM 辅助分析函数定义 Pydantic response schema

### 3.3 LLM 客户端重试与断路器


| 编号     | 问题             | 来源    |
| ------ | -------------- | ----- |
| 用户-13  | LLM 客户端无自主重试机制 | 用户自查  |
| GAP-13 | 完全没有断路器        | 第二轮审计 |


**具体动作**：

```python
# application/llm.py — 指数退避 + 断路器
class LiteLLMClient(LLMClient):
    def __init__(self, *, model: str, timeout_seconds: int = 30,
                 max_retries: int = 3, circuit_breaker_threshold: int = 5,
                 circuit_breaker_reset_seconds: int = 60, **kwargs) -> None:
        ...
        self._failure_count = 0
        self._circuit_open_until: float = 0

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if time.monotonic() < self._circuit_open_until:
            return self._circuit_open_response(request)

        for attempt in range(self._max_retries):
            try:
                response = await asyncio.to_thread(self._invoke_completion, request)
                self._failure_count = 0
                return response
            except Exception as exc:
                if not self._is_retryable(exc) or attempt == self._max_retries - 1:
                    self._record_failure()
                    return self._error_response(request, exc)
                await asyncio.sleep(2 ** attempt * 0.5)  # 指数退避
```

### 3.4 记忆系统修复


| 编号    | 问题                          | 来源    |
| ----- | --------------------------- | ----- |
| 主动-4  | 5 层记忆仅 top-3 进入 LLM         | 第二轮审计 |
| 主动-5  | Integrity 阈值几乎不过滤           | 第二轮审计 |
| 主动-6  | 遗忘仅为预测，实际执行依赖 projector     | 第二轮审计 |
| 主动-7  | Pin 永不过期/重评估                | 第二轮审计 |
| 主动-20 | Pinned entry 在全 pinned 时被驱逐 | 第二轮审计 |
| 主动-21 | 新 semantic concept 写入即驱逐    | 第二轮审计 |


**具体动作**：

- LLM prompt 中 recall 从 `[:3]` 改为按层分桶：至少 1 条 relational/reflective + 剩余按分数填充，总上限 5
- Integrity 阈值从 0.62 提高到 0.75
- Projector 中实际执行驱逐（收到 `MEMORY_FORGETTING_APPLIED` 时删除对应条目）
- Pin 加 `pinned_at` 时间戳，超过 N 轮后降级为 unpinned
- `_predict_sequence_evictions`：全 pinned 时 raise 而非 fallback 到 `pop(0)`
- `_predict_aggregated_evictions`：新条目加 grace period（前 3 轮不被驱逐）

### 3.5 主动对话系统修复


| 编号    | 问题                                 | 来源    |
| ----- | ---------------------------------- | ----- |
| 主动-1  | 无 TTL，hold 项永久滞留                   | 第二轮审计 |
| 主动-3  | 已完成 proactive line 无显式完成事件         | 第二轮审计 |
| 主动-9  | 5 层延迟叠加，trigger_after_seconds 名不副实 | 第二轮审计 |
| 主动-11 | 手动 vs 自动 dispatch 无互斥              | 第二轮审计 |
| 主动-17 | window_seconds=0 时 overdue 不可达     | 第二轮审计 |
| 主动-18 | "hold" 是吸收态，无脱出机制                  | 第二轮审计 |
| 主动-19 | stage_intervals=0 导致单次消耗所有 stage   | 第二轮审计 |


**具体动作**：

- 加 `PROACTIVE_LINE_COMPLETED` 事件类型，dispatch 完最后一个 stage 后写入
- hold 状态加 TTL：超过 24 小时自动转为 `expired`
- `trigger_after_seconds`：计算完 5 层叠加后，如果实际延迟 > 原始值 × 3，写入 warning 日志
- `RuntimeService.dispatch_proactive_followup` 中也加 per-session 锁（复用 0.6 的锁）
- `window_seconds=0` 时改为 `window_seconds = max(window_seconds, 300)`（至少 5 分钟窗口）
- `_build_followup_item` 中 progression loop 加 `max_iterations = 5` 保护

---

## Phase 4：生产就绪与上线收口

> **目标**：补齐可观测性、部署基础设施、评测深度，让项目具备上线能力。
> **预计工时**：3-5 天

### 4.1 可观测性全面补齐


| 编号     | 问题                                  | 来源    |
| ------ | ----------------------------------- | ----- |
| GAP-01 | structlog 配置了但几乎未使用（49 文件仅 3 文件有日志） | 第二轮审计 |
| GAP-02 | Request ID 传播是死代码                   | 第二轮审计 |
| GAP-03 | 完全没有 HTTP 中间件                       | 第二轮审计 |
| GAP-04 | LLM 调用不记录日志                         | 第二轮审计 |
| GAP-05 | Event Store 操作零可观测性                 | 第二轮审计 |
| GAP-07 | 完全没有应用指标                            | 第二轮审计 |
| GAP-09 | 完全没有告警基础设施                          | 第二轮审计 |
| GAP-18 | runtime_service.py 零日志              | 第二轮审计 |


**具体动作**：

**a) 请求生命周期日志中间件**：

```python
# api/middleware.py
import uuid, time, structlog
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        structlog.get_logger().info("http_request",
            method=request.method, path=request.url.path,
            status=response.status_code, elapsed_ms=round(elapsed, 1))
        structlog.contextvars.clear_contextvars()
        return response
```

**b) LLM 调用日志**：在 `LiteLLMClient.complete` 中加 `logger.info("llm_call", model=..., latency_ms=..., prompt_tokens=..., completion_tokens=..., failure=...)`

**c) Event Store 日志**：在 `PostgresEventStore.append/read_stream` 中加计时日志

**d) 关键服务日志**：`RuntimeService.process_turn` 开始/结束、`ProactiveFollowupDispatcher.dispatch_due_followups` 每个周期

**e) 深度健康检查**：

```python
@router.get("/healthz/ready")
async def readiness(container: ContainerDep) -> dict:
    checks = {}
    if container.database_engine:
        try:
            async with container.database_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e}"
    checks["job_executor"] = "running" if container.job_executor.is_running else "stopped"
    checks["dispatcher"] = "running" if container.proactive_followup_dispatcher.is_running else "stopped"
    status = "ok" if all(v in ("ok", "running") for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

### 4.2 部署基础设施


| 编号   | 问题                           | 来源    |
| ---- | ---------------------------- | ----- |
| O-01 | 没有 Dockerfile                | 第三轮审计 |
| O-02 | 没有 docker-compose.yml        | 第三轮审计 |
| O-03 | 没有 CI/CD 管道                  | 第三轮审计 |
| M-8  | 模块级 `app = create_app()` 副作用 | 第一轮审计 |


**具体动作**：

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "relationship_os.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: relationship_os
      POSTGRES_PASSWORD: ${DB_PASSWORD:-dev_only}
    volumes: [pgdata:/var/lib/postgresql/data]
    ports: ["5432:5432"]
  app:
    build: .
    depends_on: [db]
    environment:
      RELATIONSHIP_OS_DATABASE_URL: postgresql+psycopg://postgres:${DB_PASSWORD:-dev_only}@db:5432/relationship_os
      RELATIONSHIP_OS_EVENT_STORE_BACKEND: postgres
      RELATIONSHIP_OS_LLM_BACKEND: mock
    ports: ["8000:8000"]
volumes:
  pgdata:
```

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev
      - run: uv run ruff check .
      - run: uv run pytest --cov=relationship_os -q
```

- `main.py`：将 `app = create_app()` 改为 `def app(): return create_app()`（lazy factory）或在 `if __name__ == "__main__"` guard 下

### 4.3 评测框架深化


| 编号     | 问题                                    | 来源    |
| ------ | ------------------------------------- | ----- |
| 评测-3.1 | 场景目录仅 8 个（7 stress + 1 redteam）       | 第二轮审计 |
| 评测-4.1 | `>= 0` 断言对非负整数永真                      | 第二轮审计 |
| 评测-5.1 | 仅 1 个 redteam 场景                      | 第二轮审计 |
| 评测-6.1 | 350+ 生命周期指标计算但无场景验证                   | 第二轮审计 |
| 评测-7.2 | 短场景输出质量永远返回 "stable"                  | 第二轮审计 |
| 评测-7.3 | scorecard 只有 "pass"/"review"，无 "fail" | 第二轮审计 |
| 评测-8.1 | `_rollup_status` 将 None 默认为 "pass"    | 第二轮审计 |
| 评测-9.1 | cohort_size=3 无统计显著性                  | 第二轮审计 |


**具体动作**：

- 新增 5+ 个 redteam 场景：多轮升级、情感操纵、间接依赖、权威冒充、极长输入
- 新增 3+ 个多轮 stress 场景（5-10 轮对话）
- 测试中 `>= 0` 替换为具体期望值（如 `== 1`, `>= 1`）
- scorecard 加 `"fail"` 状态（任何 safety/boundary 检查失败 = fail）
- `_rollup_status`：`None` → `"unknown"` 而非 `"pass"`
- 输出质量检测：对 1-2 轮场景也检查 `template_repetition` 和 `question_count`
- cohort_size 配置化，小样本时禁用漂移检测或标注 `low_confidence`

### 4.4 Console UI 修复


| 编号        | 问题                                    | 来源    |
| --------- | ------------------------------------- | ----- |
| C-04/C-05 | 无 ARIA 属性和 landmark                   | 第三轮审计 |
| C-15      | CDN 脚本无 SRI                           | 第三轮审计 |
| C-16      | WebSocket 重连无指数退避                     | 第三轮审计 |
| C-18      | WebSocket message handler 无 try-catch | 第三轮审计 |


**具体动作**：

- Tab 组加 `role="tablist"` / `role="tab"` / `role="tabpanel"` / `aria-selected`
- 实时更新区加 `aria-live="polite"`
- Badge 加 `aria-label="status: {status}"`
- CDN script 标签加 `integrity="sha384-..."` 和 `crossorigin="anonymous"`
- WebSocket 重连改为指数退避：`Math.min(1000 * 2 ** retryCount, 30000)`
- `JSON.parse` 包裹 `try { ... } catch (e) { console.warn(...) }`

### 4.5 数据库连接池与超时


| 编号   | 问题                                        | 来源    |
| ---- | ----------------------------------------- | ----- |
| 并发-5 | 连接池缺少 pool_size/max_overflow/pool_recycle | 第一轮审计 |
| 并发-6 | 数据库操作无超时控制                                | 第一轮审计 |


**具体动作**：

```python
def build_async_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_timeout=30,
        connect_args={"command_timeout": 10},
    )
```

### 4.6 Event Schema 演进策略


| 编号    | 问题                               | 来源    |
| ----- | -------------------------------- | ----- |
| ES-10 | 无 schema 版本和 upcaster 机制         | 第一轮审计 |
| ES-11 | 缺少 correlation_id / causation_id | 第一轮审计 |


**具体动作**：

- `NewEvent` 加 `schema_version: int = 1` 字段
- `event_records` 表加 `schema_version INTEGER DEFAULT 1` 列
- 在 `StreamService` 中加 upcaster 注册表：`register_upcaster(event_type, from_version, to_version, transform_fn)`
- `StoredEvent.metadata` 自动填充 `correlation_id`（从请求 ID 获取）和 `causation_id`（上游事件 ID）

---

## 完整问题索引

> 以下按问题编号速查其所在 Phase 和修复任务。


| 来源          | 编号                            | Phase | 任务         |
| ----------- | ----------------------------- | ----- | ---------- |
| 用户自查        | 1. analyzers.py 拆分            | 1     | 1.1        |
| 用户自查        | 2. runtime_service God Object | 1     | 1.2        |
| 用户自查        | 3. Projector O(N) 拷贝          | 0     | 0.2        |
| 用户自查        | 4. EventStore 无分页             | 0     | 0.1        |
| 用户自查        | 5. 测试架构短板                     | 0     | 0.8        |
| 用户自查        | 6. Lifecycle 泛化               | 2     | 2.1        |
| 用户自查        | 7. Governance 泛化              | 2     | 2.2        |
| 用户自查        | 8. Pydantic 反序列化              | 2     | 2.3        |
| 用户自查        | 9. 字符串魔术值                     | 2     | 2.4        |
| 用户自查        | 10. 硬编码常量                     | 1     | 1.7        |
| 用户自查        | 11. LLM 接入                    | 3     | 3.1        |
| 用户自查        | 12. Structured Output         | 3     | 3.2        |
| 用户自查        | 13. LLM 重试                    | 3     | 3.3        |
| 用户自查        | 14. 领域下沉                      | 2     | 2.5        |
| 用户自查        | 15. 安全执行管线                    | 1     | 1.6        |
| 第一轮-安全      | C-1 完全无认证                     | 0     | 0.4        |
| 第一轮-安全      | C-2 事件流开放写入                   | 0     | 0.4        |
| 第一轮-安全      | H-1 硬编码凭据                     | -1    | -1.3       |
| 第一轮-安全      | H-2 无速率限制                     | 0     | 0.4        |
| 第一轮-安全      | H-3 WebSocket 安全              | 0     | 0.4        |
| 第一轮-安全      | H-4 暴露内部信息                    | 0     | 0.5        |
| 第一轮-安全      | H-5 无 CORS                    | 0     | 0.4        |
| 第一轮-安全      | M-1 输入验证不足                    | 0     | 0.5        |
| 第一轮-安全      | M-2 错误处理缺失                    | 0     | 0.5        |
| 第一轮-安全      | M-3 健康检查浅                     | 4     | 4.1        |
| 第一轮-安全      | M-4 缺响应模型                     | 0     | 0.5        |
| 第一轮-安全      | M-5 无安全头/SRI                  | 0     | 0.4 / 4.4  |
| 第一轮-安全      | M-6 无请求体大小限制                  | 0     | 0.4        |
| 第一轮-安全      | M-7 危险操作无保护                   | 0     | 0.5        |
| 第一轮-安全      | M-8 模块级实例化                    | 4     | 4.2        |
| 第一轮-安全      | L-1 API 版本隔离                  | 4     | 4.2        |
| 第一轮-安全      | L-2 硬编码版本号                    | 4     | 4.2        |
| 第一轮-安全      | L-3 lru_cache 不刷新             | 4     | 4.2        |
| 第一轮-并发      | 1 InMemory 读未加锁               | 0     | 0.7        |
| 第一轮-并发      | 2 Broker 静默丢消息                | 4     | 4.1        |
| 第一轮-并发      | 3 Job 轮询全量扫描                  | 0     | 0.3        |
| 第一轮-并发      | 4 list_stream_ids 全量          | 0     | 0.1        |
| 第一轮-并发      | 5 连接池缺配置                      | 4     | 4.5        |
| 第一轮-并发      | 6 DB 操作无超时                    | 4     | 4.5        |
| 第一轮-并发      | 7 shutdown 级联失败               | 0     | 0.6        |
| 第一轮-并发      | 8 Dispatcher shutdown 顺序      | 0     | 0.6        |
| 第一轮-并发      | 9 JobExecutor 孤儿任务            | 0     | 0.6        |
| 第一轮-并发      | 10 JobExecutor 无并发上限          | 0     | 0.6        |
| 第一轮-并发      | 11 RuntimeService 无锁          | 0     | 0.6        |
| 第一轮-并发      | 12 expected_version=None 异常   | 0     | 0.7        |
| 第一轮-并发      | 13 Broker 锁外迭代                | 4     | 4.1        |
| 第一轮-并发      | 14 read_all 无分页               | 0     | 0.1        |
| 第一轮-并发      | 15 缺 CancelledError 处理        | 0     | 0.6        |
| 第一轮-并发      | 19 Broker shutdown 不通知        | 0     | 0.6        |
| 第一轮-并发      | 20 claim_job 双扫描              | 0     | 0.3        |
| 第一轮-ES      | 1 事件未被投影                      | 2     | 2.6        |
| 第一轮-ES      | 2 乐观并发竞态                      | 0     | 0.7        |
| 第一轮-ES      | 3 DIRECTIVE 覆盖                | 2     | 2.6        |
| 第一轮-ES      | 4 无快照策略                       | 0     | 0.2        |
| 第一轮-ES      | 5 硬编码字符串                      | 2     | 2.6        |
| 第一轮-ES      | 6 InMemory 不排序                | 0     | 0.1        |
| 第一轮-ES      | 8 无全局序列号                      | 0     | 0.7        |
| 第一轮-ES      | 9 payload 零验证                 | 0     | 0.7        |
| 第一轮-ES      | 10 无 schema 演进                | 4     | 4.6        |
| 第一轮-ES      | 11 缺 correlation_id           | 4     | 4.6        |
| 第一轮-ES      | 12-14 Projector 无界增长          | 2     | 2.6        |
| 第二轮-评测      | 多项                            | 4     | 4.3        |
| 第二轮-主动      | 多项                            | 3     | 3.4 / 3.5  |
| 第二轮-可观测     | GAP-01~20                     | 4     | 4.1        |
| 第三轮-Console | C-01~C-23                     | 1/4   | 1.5 / 4.4  |
| 第三轮-Domain  | D-01~D-15                     | 2     | 2.1~2.5    |
| 第三轮-部署      | O-01~O-21                     | -1/4  | -1.x / 4.2 |
| 第三轮-质量      | Q-01~Q-28                     | 1/2   | 多项         |


---

## 预计总工时


| Phase    | 内容          | 工时              |
| -------- | ----------- | --------------- |
| Phase -1 | 版本控制与数据安全   | 0.5 天           |
| Phase 0  | 阻断性基础设施与安全  | 3-5 天           |
| Phase 1  | 工程质量与文件拆分   | 3-5 天           |
| Phase 2  | 数据结构泛化与强类型  | 4-6 天           |
| Phase 3  | LLM 基建与领域协同 | 3-5 天           |
| Phase 4  | 生产就绪与上线收口   | 3-5 天           |
| **总计**   |             | **16.5-26.5 天** |


---

## 执行原则

1. **每个 Phase 完成后打 Git tag**，确保可回滚
2. **每搬迁一个模块就跑一次 `pytest`**，绝不批量搬迁
3. **先改 Protocol/接口，再改实现**——自顶向下重构
4. **新代码必须有 docstring + type annotation**
5. **不要在重构过程中加新功能**——先稳定再扩展

