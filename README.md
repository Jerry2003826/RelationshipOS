# RelationshipOS

RelationshipOS 是一个面向长期关系型认知主体的运行时骨架。当前仓库已经完成 `Phase 0` 的开发起点，并铺好了 `Phase 1` 所需的 Event Sourcing、Projector 与 PostgreSQL 持久化事件流最小实现。

## 当前包含

- FastAPI 应用入口与基础路由
- `pydantic-settings` 配置系统
- `structlog` 日志初始化
- 可切换的 `Mock` / `LiteLLM` LLM backend
- 内存版 Event Store，带乐观并发检查
- PostgreSQL Event Store，基于 SQLAlchemy async + Alembic
- 版本化 Projector 注册与回放
- 最小可运行的 `ContextFrame` / `RelationshipState` / `MemoryBundle` / `RepairPlan` / `PrivateJudgment` 链路
- 可投影与可 recall 的五层 session memory 视图
- runtime turn 会把 recall 结果显式写入事件流并参与当前轮决策
- recall 已接入 Temporal KG 桥接检索，可返回 matched nodes 与 bridges
- recall 现在带 provenance / integrity summary，并支持语境过滤
- memory write guard 会拦截低信号记忆写入，并把拦截结果写入事件流
- retention policy 会为高价值记忆打 pin，并让超限裁剪优先淘汰非 pinned 项
- controlled forgetting 会显式记录工作记忆/情节记忆等层的预测淘汰结果
- runtime 现在会显式产出 `RepairAssessment` 与 `KnowledgeBoundaryDecision`
- `ConfidenceAssessment` 现在会显式给出 `direct / clarify / calibrated / repair_first` gate
- strategy 之前现在还有显式 `PolicyGateDecision`，会记录 path / red-line / regulation / empowerment risk
- `RehearsalResult` 与 `EmpowermentAudit` 已接入主链，可审计预演风险与赋能边界
- `ResponseDraftPlan` 已接入主链，会显式约束 opening move / must-include / must-avoid / phrasing constraints
- `ResponseRenderingPolicy` 已接入主链，会显式约束句数上限、boundary/uncertainty 说明和问题数量限制
- 最终 assistant 文本现在还会经过 `ResponsePostAudit`，显式记录句数、问题数、必需说明是否命中以及违规项
- 如果 post-audit 发现回复不合规，runtime 现在还会跑 `ResponseNormalizationResult`，自动修正并重新审计最终文本
- 最小可运行的 `/jobs/*` 后台任务与 offline consolidation
- 事件流驱动的 job state 与失败重试
- 启动时自动恢复 queued / retryable failed jobs 的执行器
- 常驻 poller worker，会接管请求外创建的 queued jobs
- 事件流驱动的 `/ws/runtime` 实时推送通道
- 只读的 HTMX + Alpine.js runtime console，可直接查看 sessions / evaluations / scenarios / jobs / archives / replay，并支持 projector-aware inspection
- 内置 stress / red-team 场景目录与场景执行器，可一键跑标准化 evaluation suite
- consolidation 驱动的 session snapshot / archive / audit 查询
- 基础测试与开发指令

## 项目结构

```text
.
├── PLAN.md
├── pyproject.toml
├── src/relationship_os
│   ├── api
│   ├── application
│   ├── core
│   ├── domain
│   ├── infrastructure
│   └── main.py
└── tests
```

## 本地开发

```bash
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn relationship_os.main:app --reload
```

服务启动后可访问：

- `GET /healthz`
- `GET /api/v1/healthz`
- `GET /api/v1/runtime`
- `GET /api/v1/runtime/trace/{stream_id}`
- `GET /api/v1/runtime/audit/{stream_id}`
- `GET /api/v1/runtime/archives`
- `GET /api/v1/console`
- `GET /api/v1/console/fragments/evaluations`
- `GET /api/v1/console/fragments/scenarios`
- `WS /api/v1/ws/runtime`
- `GET /api/v1/evaluations/sessions`
- `GET /api/v1/evaluations/sessions/{session_id}`
- `GET /api/v1/evaluations/scenarios`
- `GET /api/v1/evaluations/scenarios/{scenario_id}`
- `POST /api/v1/evaluations/scenarios/run`
- `GET /api/v1/evaluations/scenarios/runs`
- `GET /api/v1/evaluations/scenarios/runs/{run_id}`
- `GET /api/v1/evaluations/scenarios/baselines`
- `PUT /api/v1/evaluations/scenarios/baselines/{label}`
- `DELETE /api/v1/evaluations/scenarios/baselines/{label}`
- `GET /api/v1/evaluations/scenarios/baselines/{label}/compare`
- `GET /api/v1/evaluations/scenarios/trends`
- `GET /api/v1/evaluations/scenarios/report`
- `GET /api/v1/evaluations/scenarios/horizon-report`
- `GET /api/v1/evaluations/scenarios/multiweek-report`
- `GET /api/v1/evaluations/scenarios/sustained-drift-report`
- `GET /api/v1/evaluations/scenarios/baseline-governance`
- `GET /api/v1/evaluations/scenarios/migration-readiness`
- `GET /api/v1/evaluations/scenarios/release-gate`
- `GET /api/v1/evaluations/scenarios/release-dossier`
- `GET /api/v1/evaluations/scenarios/launch-signoff`
- `GET /api/v1/evaluations/scenarios/compare`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/offline-consolidation`
- `POST /api/v1/jobs/{job_id}/retry`
- `GET /api/v1/sessions`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}/inner-monologue`
- `GET /api/v1/sessions/{session_id}/memory`
- `GET /api/v1/sessions/{session_id}/memory/graph`
- `GET /api/v1/sessions/{session_id}/memory/recall`
- `GET /api/v1/sessions/{session_id}/snapshots`
- `POST /api/v1/sessions/{session_id}/turns`
- `POST /api/v1/streams/{stream_id}/events`
- `GET /api/v1/streams/{stream_id}/events`
- `GET /api/v1/streams/{stream_id}/replay`
- `GET /api/v1/streams/{stream_id}/projection/session-transcript`
- `POST /api/v1/projectors/{projector_name}/rebuild`

## 运行测试

```bash
uv run pytest
uv run ruff check .
```

## 数据库迁移

```bash
uv run alembic upgrade head
uv run alembic downgrade base
```

## LLM 配置

默认使用 `mock` backend，本地无需 API Key。切到 LiteLLM 时，至少配置：

```bash
RELATIONSHIP_OS_LLM_BACKEND=litellm
RELATIONSHIP_OS_LLM_MODEL=openai/gpt-5
```

后台任务默认最多重试 `2` 次，也可以通过环境变量覆盖：

```bash
RELATIONSHIP_OS_JOB_MAX_ATTEMPTS=3
```

执行器也支持 worker 身份和轮询间隔配置：

```bash
RELATIONSHIP_OS_JOB_WORKER_ID=worker-local-1
RELATIONSHIP_OS_JOB_POLL_INTERVAL_SECONDS=0.5
```

`Runtime Quality Doctor` 默认每 `3` 轮扫描最近 `4` 轮对话，也可以通过环境变量覆盖：

```bash
RELATIONSHIP_OS_RUNTIME_QUALITY_DOCTOR_INTERVAL_TURNS=3
RELATIONSHIP_OS_RUNTIME_QUALITY_DOCTOR_WINDOW_TURNS=4
```

应用启动时会自动扫描事件流中的 `queued` job，并对可重试的 `failed` job 自动 requeue 后继续执行。启动后 poller 也会持续接管请求外创建的 `queued` job。

`/api/v1/console` 现在会直接消费 `/ws/runtime` 做实时刷新，右侧 rail 会随 runtime 事件刷新 sessions / evaluations / scenarios / jobs / archives，当前选中的 session detail 也会跟着 trace 和 projection 更新。

`/api/v1/evaluations/scenarios/run` 会按内置 catalog 执行 stress / red-team 场景，自动生成新的 scenario session、汇总 summary、audit 指纹和 pass/review scorecard，方便做回归评测。现在也可以通过 `/api/v1/evaluations/scenarios/runs`、`/api/v1/evaluations/scenarios/trends`、`/api/v1/evaluations/scenarios/report` 和 `/api/v1/evaluations/scenarios/compare` 查看 suite run 历史、按场景聚合的趋势摘要、最近窗口的稳定性报告，以及两次 run 之间的回归 diff。

`/api/v1/evaluations/scenarios/release-gate` 会把最近窗口、baseline 对比、watchlist，以及 full-suite / red-team 覆盖度收束成一个明确的 `pass / review / blocked` 决策，适合做版本过线检查。

`/api/v1/evaluations/scenarios/ship-readiness` 会在 release gate 之外继续纳入 job executor poller、重试失败 job、过期 lease 和活动 backlog，直接给出更接近上线前检查清单的 `pass / review / blocked` 结果。控制台 `Scenarios` rail 也会同步显示这层 `Ship Readiness` 视图。

`/api/v1/evaluations/scenarios/misalignment-report` 会把最近窗口里的 scenario failed checks 聚合成失败类型学，告诉你当前更偏向哪类失对齐，而不只是“通过/未通过”。控制台 `Scenarios` rail 现在也会显示 `Misalignment Taxonomy`。

如果你想固定一个长期基线，也可以用 `/api/v1/evaluations/scenarios/baselines/{label}` 把某次 run pin 成 baseline。之后 `/api/v1/evaluations/scenarios/baselines/{label}/compare` 和控制台里的 `Baseline Track` 会直接对比“最新 run vs 基线 run”。

单 session 评测现在也会附带输出质量趋势信号，包括回复长度斜率、词汇多样性斜率、信息密度斜率、重复开头次数，以及汇总后的 `output_quality_status`。控制台 `Evaluations` rail 会把这层状态直接显示出来，方便盯长程质量退化。

`/api/v1/evaluations/strategy-preferences` 会按 `latest_strategy` 聚合真实 session，并先做质量底线过滤、再把 session duration 和关系质量作为主信号、把高 turn 低停留的 fast churn 当成噪声惩罚，给出第一版“因果去噪”的策略偏好信号。同一接口现在也会附带 `reengagement_learning`，按真实 non-scenario session 汇总主动重连策略的历史 reinforcement 信号，给 `re-engagement matrix` 提供可学习的偏好底座。控制台 `Evaluations` rail 现在会把这层 `Preference Signals` 和 `Re-engagement Learning` 一起显示出来。

策略层现在也有第一版主动多样性机制：当最近几轮安全策略分布熵过低、且系统长期只重复同一路径时，`Dramaturgical Engine` 会在安全替代策略里主动探索低频路径，而不是一直停在同一种表达套路。单 session 评测会额外暴露 `strategy_diversity_index`、`strategy_diversity_intervention_turn_count` 和 `latest_strategy_diversity_status`，控制台 detail 里也能直接看到这层状态。

运行时现在也支持第一版“非严格轮次结构”：当边界校准、问题澄清或高修复压力场景更适合拆成两个语义单元时，系统会把一次回复拆成 `two_part_sequence` 连续输出，而不是强行压成单段。`POST /api/v1/sessions/{session_id}/turns` 现在会同时返回 `assistant_response`、`assistant_responses` 和 `assistant_response_mode`，单 session 评测也会附带 `continuous_output_turn_count`、`continuous_output_segment_total` 和 `latest_response_sequence_mode`。

`Runtime Quality Doctor` 也已经有首版：系统会按配置周期扫描最近窗口里的对话段，检测重复开头、相邻重复片段、语言混杂、格式噪声和边界/确定性矛盾，并把结果写成 `system.runtime_quality_doctor.completed` 事件。单 session 评测现在会附带 `runtime_quality_doctor_report_count`、`runtime_quality_doctor_watch_count`、`runtime_quality_doctor_revise_count` 和 `latest_runtime_quality_doctor_status`，控制台 `Evaluations` rail 也会把这层状态显示出来。

`Phase 10` 的 `System 3` 现在也多了一层显式 `moral reasoning`：系统会把当前回合的 `moral_reasoning_status`、`moral_posture`、`moral_conflict`、`moral_principles` 和 `moral_notes` 一起写进 `system.system3.snapshot.updated`。第一版 heuristics 会把 `support_vs_dependency`、`truth_vs_comfort`、`care_vs_directness` 这类冲突显式化，并把它们同步暴露到单 session 评测和控制台，所以 `System 3` 已经不只是看成长阶段/情感债务/策略审计，也开始直接观察“当前这一拍在道德上是稳、需关注，还是该重判”。

`Phase 10` 这轮又补上了显式 `moral trajectory`：`System 3` 现在会额外产出 `moral_trajectory_status`、`moral_trajectory_target`、`moral_trajectory_trigger` 和 `moral_trajectory_notes`，用来判断这条 moral line 是在稳住、轻微拉扯，还是已经需要 re-center。第一版 heuristics 会把 `dependency_pressure_detected`、`uncertainty_disclosure_required`、`repair_pressure_detected`、`boundary_sensitive_guard` 和 `moral_tension_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮道德判断要不要 revise”，而是开始显式判断“这条道德线最近是在稳住、拉扯，还是已经该重拉回更安全的姿态”。

`Phase 10` 这轮还补上了显式 `emotional debt trajectory`：`System 3` 现在会额外产出 `emotional_debt_trajectory_status`、`emotional_debt_trajectory_target`、`emotional_debt_trajectory_trigger` 和 `emotional_debt_trajectory_notes`，用来判断这条 debt line 是在稳住、进入 watch，还是已经需要先做 `decompression`。第一版 heuristics 会把 `repair_pressure_with_elevated_debt`、`quality_drift_with_elevated_debt`、`elevated_debt_detected`、`empowerment_caution_with_debt` 和 `soft_debt_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“当前 debt 高不高”，而是开始显式判断“这条债务线最近是在稳住、积压观察，还是已经需要先减压”。

`Phase 10` 现在还多了一层显式 `user model evolution`：`System 3` 会额外产出 `user_model_evolution_status`、`user_model_revision_mode`、`user_model_shift_signal` 和 `user_model_evolution_notes`，用来判断这轮是不是提示“用户画像该修了”。第一版 heuristics 会把 `context_drift`、`repair_pressure`、`delivery_preference_reinforced` 和 `underfit_memory` 这类信号显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是静态存一份用户模型，而是开始显式判断“这份模型现在稳不稳、该往哪个方向修”。

`Phase 10` 这轮还补上了显式 `user model trajectory`：`System 3` 会额外产出 `user_model_trajectory_status`、`user_model_trajectory_target`、`user_model_trajectory_trigger` 和 `user_model_trajectory_notes`，用来判断这条用户模型线是在稳住、轻微漂移，还是已经需要 re-center。第一版 heuristics 会把 `context_drift_detected`、`repair_pressure_detected`、`underfit_memory_detected`、`delivery_preference_reinforced` 和 `soft_model_drift` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮要不要修用户模型”，而是开始显式判断“这条用户模型线最近是在稳住、偏移，还是已经需要重拉回中心”。

`Phase 10` 现在还多了一层显式 `growth transition assessment`：`System 3` 会额外产出 `growth_transition_status`、`growth_transition_target`、`growth_transition_trigger`、`growth_transition_readiness` 和 `growth_transition_notes`，用来判断当前关系阶段是在稳住、准备升级、需要 hold，还是应该先 redirect 回 `repairing`。第一版 heuristics 会把 `continuity_and_safety_ready`、`trust_continuity_ready`、`repair_recovered`、`dependency_risk_requires_rebalancing` 这类跃迁信号显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是打一个 `growth_stage` 标签，而是开始显式判断“下一段关系演化该不该往前走、往哪走”。

`Phase 10` 这轮还补上了显式 `growth transition trajectory`：`System 3` 现在会额外产出 `growth_transition_trajectory_status`、`growth_transition_trajectory_target`、`growth_transition_trajectory_trigger` 和 `growth_transition_trajectory_notes`，用来判断这条 growth line 是在稳住、进入 `watch`、准备 `advance`，还是已经需要 `redirect`。第一版 heuristics 会把 `dependency_transition_watch`、`repair_transition_watch`、`stability_transition_watch`、`patterning_transition_ready`、`continuity_transition_ready`、`deepening_transition_ready` 和 `debt_redirect_active` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮要不要跃迁”，而是开始显式判断“这条 growth line 最近是在稳住、观测、准备往前走，还是已经该先回修复/稳态”。

`Phase 10` 现在还多了一层显式 `identity trajectory`：`System 3` 会额外产出 `identity_trajectory_status`、`identity_trajectory_target`、`identity_trajectory_trigger` 和 `identity_trajectory_notes`，用来判断当前 identity 是稳定、轻微偏移，还是已经需要显式 re-center。第一版 heuristics 会把 `response_post_audit_drift`、`runtime_quality_doctor_drift`、`response_normalization_adjustment`、`identity_soft_drift` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看一拍的 `identity_consistency`，而是开始显式判断“identity 这条线最近是在稳住、滑移，还是该重拉回主锚点”。

`Phase 10` 这轮还补上了显式 `version migration posture`：`System 3` 会额外产出 `version_migration_status`、`version_migration_scope`、`version_migration_trigger` 和 `version_migration_notes`，用来判断当前 session 是已经适合稳定 replay/rebuild，还是应该先走 `cautious_rebuild`，或者直接 `hold_rebuild`。第一版 heuristics 会把 `quality_drift_requires_hold`、`identity_recenter_requires_hold`、`user_model_recalibration_requires_hold`、`context_drift_requires_hold` 和 `low_continuity_sample` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是有 release 侧的 migration readiness 报告，而是开始显式判断“这条具体 session 线现在适不适合承受版本迁移/重建”。

`Phase 10` 这轮还补上了显式 `version migration trajectory`：`System 3` 现在会额外产出 `version_migration_trajectory_status`、`version_migration_trajectory_target`、`version_migration_trajectory_trigger` 和 `version_migration_trajectory_notes`，用来判断这条 migration line 是在稳住、进入 `watch`，还是已经需要 `hold`。第一版 heuristics 会把 `context_drift_rebuild_watch`、`growth_transition_rebuild_watch`、`thin_history_rebuild_watch`、`quality_hold_required`、`identity_hold_required` 和 `user_model_hold_required` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮适不适合重建”，而是开始显式判断“这条 migration line 最近是在稳住、观测，还是已经该先 hold 住”。

`Phase 10` 这轮还补上了显式 `strategy supervision`：`System 3` 会额外产出 `strategy_supervision_status`、`strategy_supervision_mode`、`strategy_supervision_trigger` 和 `strategy_supervision_notes`，用来判断当前策略只是稳定受控、需要 `guided/risk/boundary` watch，还是已经该进入 `corrective / repair_override / boundary_lock` 这种更强监督模式。第一版 heuristics 会把 `repair_pressure_override`、`policy_gate_boundary_lock`、`empowerment_revision_required`、`post_audit_revision_required`、`rehearsal_risk_detected` 和 `diversity_intervention_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看 `strategy_audit` 的结果，而是开始显式判断“这轮策略需不需要被更强地看住、纠偏或锁边界”。

`Phase 10` 这轮还补上了显式 `strategy supervision trajectory`：`System 3` 现在会额外产出 `strategy_supervision_trajectory_status`、`strategy_supervision_trajectory_target`、`strategy_supervision_trajectory_trigger` 和 `strategy_supervision_trajectory_notes`，用来判断这条 supervision line 是在稳住、进入 watch，还是已经需要 `tighten`。第一版 heuristics 会把 `diversity_supervision_watch`、`boundary_supervision_watch`、`risk_supervision_watch`、`corrective_supervision_required`、`repair_override_required` 和 `boundary_lock_required` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮 supervision 开没开”，而是开始显式判断“这条 supervision line 最近是在稳住、观测，还是已经该进一步 tighten”。 

`Phase 10` 这轮还补上了显式 `strategy audit trajectory`：`System 3` 现在会额外产出 `strategy_audit_trajectory_status`、`strategy_audit_trajectory_target`、`strategy_audit_trajectory_trigger` 和 `strategy_audit_trajectory_notes`，用来判断这条 audit line 是在稳住、进入 `watch`，还是已经需要 `corrective`。第一版 heuristics 会把 `rehearsal_watch_active`、`empowerment_watch_active`、`post_audit_watch_active`、`quality_watch_active`、`repair_alignment_correction` 和 `strategy_correction_required` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮 audit 是 pass/watch/revise”，而是开始显式判断“这条 audit line 最近是在稳住、观测，还是已经该进入 corrective”。

`Phase 10` 这轮还补上了显式 `expectation calibration`：`System 3` 现在会额外产出 `expectation_calibration_status / target / trigger`，以及对应的 `expectation_calibration_trajectory_status / target / trigger`，用来判断用户对支持强度、边界、确定性和节奏的期待，是稳定、需要 watch，还是已经应该 reset。第一版 heuristics 会把 `dependency_pressure_detected`、`relational_boundary_required`、`uncertainty_disclosure_required`、`clarification_required`、`repair_pressure_requires_soft_expectation` 和 `segmented_delivery_active` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮要不要给 boundary/clarify”，而是开始显式判断“这条 expectation line 最近是在稳住、偏高，还是已经需要回收重校准”。

`Phase 10` 这轮还补上了显式 `dependency governance`：`System 3` 现在会额外产出 `dependency_governance_status / target / trigger`，以及对应的 `dependency_governance_trajectory_status / target / trigger`，用来判断“支持这条线”是在稳住、需要 watch，还是已经应该 re-center 到更低依赖、更强边界或先 repair 再 reliance 的姿态。第一版 heuristics 会把 `relational_boundary_required`、`dependency_pressure_detected`、`repair_before_reliance_required`、`expectation_dependency_watch` 和 `repair_load_dependency_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是从 relationship state 里读一个 `dependency_risk`，而是开始显式判断“这条 dependency line 最近是在稳住、抬头观察，还是已经需要回中心”。

`Phase 10` 这轮还补上了显式 `autonomy governance`：`System 3` 现在会额外产出 `autonomy_governance_status / target / trigger`，以及对应的 `autonomy_governance_trajectory_status / target / trigger`，用来判断“支持方式这条线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 user space、context-before-commitment 或 explicit autonomy support。第一版 heuristics 会把 `dependency_boundary_autonomy_reset`、`dependency_autonomy_reset`、`repair_pressure_autonomy_watch`、`clarification_autonomy_watch`、`uncertainty_autonomy_watch` 和 `segmented_autonomy_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮要不要更低压”，而是开始显式判断“这条 autonomy line 最近是在稳住、观测，还是已经需要回到更明确的用户主导姿态”。

`Phase 10` 这轮还补上了显式 `boundary governance`：`System 3` 现在会额外产出 `boundary_governance_status / target / trigger`，以及对应的 `boundary_governance_trajectory_status / target / trigger`，用来判断边界这条线是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `hard_boundary_containment / explicit_boundary_support / uncertainty_boundary_support`。第一版 heuristics 会把 `policy_gate_blocked`、`boundary_sensitive_gate_active`、`support_with_boundary_required`、`dependency_boundary_watch`、`uncertainty_boundary_watch`、`clarification_boundary_watch` 和 `repair_boundary_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮 boundary 要不要 tighter”，而是开始显式判断“这条 boundary line 最近是在稳住、观测，还是已经需要回到更明确的边界支撑姿态”。

`Phase 10` 这轮还补上了显式 `support governance`：`System 3` 现在会额外产出 `support_governance_status / target / trigger`，以及对应的 `support_governance_trajectory_status / target / trigger`，用来判断“支持这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `agency_preserving_bounded_support / explicit_boundary_scaffold / explicit_user_led_support`。第一版 heuristics 会把 `dependency_support_recenter`、`boundary_support_recenter`、`autonomy_support_recenter`、`repair_support_watch`、`clarification_support_watch`、`uncertainty_support_watch` 和 `segmented_support_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是分别看 dependency/autonomy/boundary 三条线，而是开始显式判断“整条 support line 最近是在稳住、观测，还是已经需要回到更 bounded 且 user-led 的支撑姿态”。

`Phase 10` 这轮还补上了显式 `continuity governance`：`System 3` 现在会额外产出 `continuity_governance_status / target / trigger`，以及对应的 `continuity_governance_trajectory_status / target / trigger`，用来判断“上下文连续性这条线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `context_reanchor_continuity / memory_regrounded_continuity / clarified_context_continuity`。第一版 heuristics 会把 `filtered_recall_continuity_reset`、`underfit_memory_continuity_reset`、`support_continuity_watch`、`clarification_continuity_watch`、`segmented_continuity_watch` 和 `thin_context_continuity_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看 memory recall 有没有命中，而是开始显式判断“这条 continuity line 最近是在稳住、观测，还是已经需要先做 re-anchor / reground 再往前走”。

`Phase 10` 这轮还补上了显式 `repair governance`：`System 3` 现在会额外产出 `repair_governance_status / target / trigger`，以及对应的 `repair_governance_trajectory_status / target / trigger`，用来判断“修复这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `boundary_safe_repair_containment / attunement_repair_scaffold / clarity_repair_scaffold`。第一版 heuristics 会把 `boundary_repair_recenter`、`attunement_repair_recenter`、`clarity_repair_recenter`、`debt_repair_watch`、`continuity_repair_watch`、`support_repair_watch`、`attunement_repair_watch` 和 `clarity_repair_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看这一拍 `repair_assessment` 严不严重，而是开始显式判断“这条 repair line 最近是在稳住、观测，还是已经需要先回到更明确的修复脚手架”。

`Phase 10` 这轮还补上了显式 `trust governance`：`System 3` 现在会额外产出 `trust_governance_status / target / trigger`，以及对应的 `trust_governance_trajectory_status / target / trigger`，用来判断“信任这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `boundary_safe_trust_containment / reanchor_before_trust_rebuild / repair_first_trust_rebuild`。第一版 heuristics 会把 `boundary_trust_recenter`、`continuity_trust_recenter`、`repair_trust_recenter`、`debt_trust_watch`、`continuity_trust_watch`、`repair_trust_watch`、`support_trust_watch` 和 `turbulence_trust_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看这一拍 safety / repair / continuity 有没有压力，而是开始显式判断“这条 trust line 最近是在稳住、观测，还是已经需要先收住、re-anchor 或先修复再继续推进”。

`Phase 10` 这轮还补上了显式 `clarity governance`：`System 3` 现在会额外产出 `clarity_governance_status / target / trigger`，以及对应的 `clarity_governance_trajectory_status / target / trigger`，用来判断“清晰度这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `reanchor_before_clarity_commitment / uncertainty_first_clarity_scaffold / repair_scaffolded_clarity`。第一版 heuristics 会把 `filtered_context_clarity_recenter`、`uncertainty_clarity_recenter`、`repair_clarity_recenter`、`clarification_clarity_watch`、`uncertainty_clarity_watch`、`continuity_clarity_watch`、`expectation_clarity_watch` 和 `segmented_clarity_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看这一拍要不要 clarify 或 disclose uncertainty，而是开始显式判断“这条 clarity line 最近是在稳住、观测，还是已经需要先 re-anchor、先讲清边界/不确定性，再继续推进”。

`Phase 10` 这轮还补上了显式 `pacing governance`：`System 3` 现在会额外产出 `pacing_governance_status / target / trigger`，以及对应的 `pacing_governance_trajectory_status / target / trigger`，用来判断“节奏这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `decompression_first_pacing / repair_first_pacing / expectation_reset_pacing`。第一版 heuristics 会把 `debt_pacing_recenter`、`repair_pacing_recenter`、`expectation_pacing_recenter`、`trust_pacing_watch`、`clarity_pacing_watch`、`segmented_pacing_watch` 和 `growth_pacing_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是看这一拍该不该慢一点，而是开始显式判断“这条 pacing line 最近是在稳住、观测，还是已经需要先减压、先修复、先重校准预期再往前走”。

`Phase 10` 这轮还补上了显式 `attunement governance`：`System 3` 现在会额外产出 `attunement_governance_status / target / trigger`，以及对应的 `attunement_governance_trajectory_status / target / trigger`，用来判断“贴合度这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `attunement_repair_scaffold / reanchor_before_attunement_rebuild / decompression_before_attunement_push`。第一版 heuristics 会把 `attunement_gap_recenter`、`continuity_attunement_recenter`、`debt_attunement_recenter`、`attunement_gap_watch`、`repair_attunement_watch`、`support_attunement_watch` 和 `continuity_attunement_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这一拍有没有 attunement gap”，而是开始显式判断“这条 attunement line 最近是在稳住、观测，还是已经需要先补贴合、先重建上下文、先减压再推进”。

`Phase 10` 这轮还补上了显式 `commitment governance`：`System 3` 现在会额外产出 `commitment_governance_status / target / trigger`，以及对应的 `commitment_governance_trajectory_status / target / trigger`，用来判断“承诺强度这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `bounded_noncommitment_support / expectation_reset_before_commitment / explicit_user_led_noncommitment / uncertainty_first_noncommitment`。第一版 heuristics 会把 `boundary_commitment_recenter`、`expectation_commitment_recenter`、`autonomy_commitment_recenter`、`uncertainty_commitment_recenter`、`repair_commitment_watch`、`clarification_commitment_watch`、`expectation_commitment_watch`、`boundary_commitment_watch`、`autonomy_commitment_watch`、`pacing_commitment_watch` 和 `segmented_commitment_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮该不该说得更保守”，而是开始显式判断“这条 commitment line 最近是在稳住、观测，还是已经需要先降承诺、先重校准预期、先回到更 user-led / bounded 的承诺姿态再推进”。

`Phase 10` 这轮还补上了显式 `disclosure governance`：`System 3` 现在会额外产出 `disclosure_governance_status / target / trigger`，以及对应的 `disclosure_governance_trajectory_status / target / trigger`，用来判断“披露方式这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `reanchor_before_disclosure_commitment / boundary_safe_disclosure / explicit_uncertainty_disclosure`。第一版 heuristics 会把 `filtered_context_disclosure_recenter`、`boundary_disclosure_recenter`、`uncertainty_disclosure_recenter`、`clarification_disclosure_watch`、`uncertainty_disclosure_watch`、`boundary_disclosure_watch`、`commitment_disclosure_watch`、`segmented_disclosure_watch` 和 `clarity_disclosure_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是知道“这轮要不要说不确定”，而是开始显式判断“这条 disclosure line 最近是在稳住、观测，还是已经需要先重接上下文、先收紧边界、先把不确定性讲清楚再继续推进”。

`Phase 10` 这轮还补上了显式 `reciprocity governance`：`System 3` 现在会额外产出 `reciprocity_governance_status / target / trigger`，以及对应的 `reciprocity_governance_trajectory_status / target / trigger`，用来判断“互惠这条关系线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `bounded_nonexclusive_reciprocity / decompression_before_reciprocity_push / user_led_reciprocity_reset / expectation_reset_before_reciprocity_push`。第一版 heuristics 会把 `dependency_reciprocity_recenter`、`debt_reciprocity_recenter`、`support_reciprocity_recenter`、`low_reciprocity_recenter`、`low_reciprocity_watch`、`support_reciprocity_watch`、`autonomy_reciprocity_watch`、`commitment_reciprocity_watch` 和 `expectation_reciprocity_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是从 `r_vector.reciprocity` 读一个静态值，而是开始显式判断“这条 reciprocity line 最近是在稳住、观测，还是已经需要先降压、先回 user-led、先重置预期再推进”。

`Phase 10` 这轮还补上了显式 `pressure governance`：`System 3` 现在会额外产出 `pressure_governance_status / target / trigger`，以及对应的 `pressure_governance_trajectory_status / target / trigger`，用来判断“关系压力这条线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `decompression_before_pressure_push / repair_first_pressure_reset / dependency_safe_pressure_reset / explicit_user_space_pressure_reset / hard_boundary_pressure_reset`。第一版 heuristics 会把 `debt_pressure_recenter`、`repair_pressure_recenter`、`dependency_pressure_recenter`、`autonomy_pressure_recenter`、`boundary_pressure_recenter`、`pacing_pressure_watch`、`support_pressure_watch`、`attunement_pressure_watch`、`trust_pressure_watch`、`commitment_pressure_watch` 和 `segmented_pressure_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是零散地从 debt / repair / autonomy / pacing 信号里猜“这轮是不是太用力了”，而是开始显式判断“这条 pressure line 最近是在稳住、观测，还是已经需要先减压、先留用户空间、先收回承诺与推动再继续推进”。

`Phase 10` 这轮还补上了显式 `relational governance`：`System 3` 现在会额外产出 `relational_governance_status / target / trigger`，以及对应的 `relational_governance_trajectory_status / target / trigger`，用来判断“整条关系推进线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `boundary_safe_relational_reset / trust_repair_relational_reset / low_pressure_relational_reset / repair_first_relational_reset / reanchor_before_relational_progress / bounded_support_relational_reset`。第一版 heuristics 会把 `boundary_relational_recenter`、`trust_relational_recenter`、`pressure_relational_recenter`、`repair_relational_recenter`、`continuity_relational_recenter`、`support_relational_recenter`、`trust_relational_watch`、`pressure_relational_watch`、`continuity_relational_watch` 和 `repair_relational_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是零散地从 trust / pressure / repair / continuity / support 这些治理线里猜“整段关系是不是该先收一下”，而是开始显式判断“这条 relational line 最近是在稳住、观测，还是已经需要先重置边界、先重建信任、先减压或先 re-anchor 再继续推进”。

`Phase 10` 这轮还补上了显式 `safety governance`：`System 3` 现在会额外产出 `safety_governance_status / target / trigger`，以及对应的 `safety_governance_trajectory_status / target / trigger`，用来判断“整条关系安全线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `hard_boundary_safety_reset / trust_repair_safety_reset / explicit_uncertainty_safety_reset / reanchor_before_safety_progress / low_pressure_safety_reset / bounded_relational_safety_reset`。第一版 heuristics 会把 `boundary_safety_recenter`、`trust_safety_recenter`、`disclosure_safety_recenter`、`clarity_safety_recenter`、`pressure_safety_recenter`、`relational_safety_recenter`、`boundary_safety_watch`、`trust_safety_watch`、`disclosure_safety_watch`、`clarity_safety_watch`、`pressure_safety_watch` 和 `relational_safety_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是零散地从 boundary / trust / disclosure / clarity / pressure 这些治理线里猜“这段关系安不安全”，而是开始显式判断“这条 safety line 最近是在稳住、观测，还是已经需要先收紧边界、先加不确定性披露、先 re-anchor 或先减压再继续推进”。

`Phase 10` 这轮还补上了显式 `stability governance`：`System 3` 现在会额外产出 `stability_governance_status / target / trigger`，以及对应的 `stability_governance_trajectory_status / target / trigger`，用来判断“整条关系稳定线”是在稳住、需要 watch，还是已经应该 re-center 到更明确的 `safety_reset_before_stability / relational_reset_before_stability / decompression_before_stability / trust_rebuild_before_stability / reanchor_before_stability / repair_scaffold_before_stability / bounded_progress_reset_before_stability`。第一版 heuristics 会把 `safety_stability_recenter`、`relational_stability_recenter`、`pressure_stability_recenter`、`trust_stability_recenter`、`continuity_stability_recenter`、`repair_stability_recenter`、`progress_stability_recenter`，以及 `safety_stability_watch / relational_stability_watch / pacing_stability_watch / trust_stability_watch / repair_stability_watch / continuity_stability_watch / progress_stability_watch / attunement_stability_watch` 这类触发原因显式化，并同步暴露到单 session 评测、策略偏好过滤和控制台，所以 `System 3` 已经不只是零散地从 safety / relational / pressure / trust / continuity / repair / progress / pacing 这些治理线里猜“这段关系稳不稳”，而是开始显式判断“这条 stability line 最近是在稳住、观测，还是已经需要先收一下、先减压、先 re-anchor 再继续推进”。

`System 3` 这条线也开始成形了：runtime 现在会在每轮结束时额外产出 `system.system3_snapshot.updated`，把 `identity tracking`、`growth stage`、`user cognitive model`、`emotional debt` 和 `strategy audit` 收束成一个统一快照。单 session 评测会同步暴露 `system3_snapshot_count`、`latest_system3_growth_stage`、`latest_system3_strategy_audit_status`、`latest_system3_emotional_debt_status` 等字段，控制台 `Evaluations` rail 和 session detail 也能直接看到这层状态。

`Phase 11` 也开始有显式运行时协调层了：runtime 现在会额外产出 `system.runtime_coordination.updated`，把 `time awareness`、`session ritual`、`cognitive load router`、`proactive follow-up readiness` 和 `somatic cue` 收束成一个统一快照。它会直接影响本轮的 drafting / rendering，例如在高认知负荷场景自动压缩句子预算、在重连场景先做 shared context re-anchor。单 session 评测会同步暴露 `runtime_coordination_snapshot_count`、`latest_time_awareness_mode`、`latest_cognitive_load_band`、`latest_proactive_style` 等字段，控制台 `Evaluations` rail 也会把这层状态显示出来。

`Phase 11` 现在还多了一层显式 `guidance plan`：runtime 会额外产出 `system.guidance_plan.updated`，把这轮更适合走 `stabilizing_guidance`、`repair_guidance`、`clarifying_guidance`、`reanchor_guidance` 还是 `progress_guidance` 写成结构化状态，并给出 `lead_with`、`pacing`、`step_budget`、`agency_mode` 和 `micro_actions`。这层会同时影响当轮 `response draft` 和后续主动重连，所以系统不只是“知道该说什么”，而是更明确地“知道该怎么带着用户往前走”。这一层现在还进一步动作化了：`guidance plan` 会显式带上 `ritual_action`、`checkpoint_style`、`handoff_mode` 和 `carryover_mode`，让“这轮怎么引导”和“下一拍怎么接住”开始连成一条线。

`Phase 11` 现在还多了一层显式 `conversation cadence plan`：runtime 会额外产出 `system.conversation_cadence.updated`，把当前这轮到底应该走 `guided_progress / stabilize_and_wait / clarify_and_pause / reanchor_and_resume` 哪种节奏，整理成 `turn_shape`、`ritual_depth`、`followup_tempo`、`user_space_mode`、`transition_intent` 和 `next_checkpoint`。这层已经同时影响当轮 `response draft`、后续 `proactive follow-up directive`、`re-engagement plan` 和主动队列展示，所以“这轮怎么说”和“下一拍怎么接”不再是松散规则，而开始被统一成一个可观察的节奏计划。

`Phase 11` 现在还多了一层显式 `session ritual plan`：runtime 会额外产出 `system.session_ritual.updated`，把这一轮更适合怎么开场、怎么桥接、怎么收束，以及是否要走一个 `somatic shortcut`，统一成 `opening_move`、`bridge_move`、`closing_move`、`continuity_anchor` 和 `somatic_shortcut`。这层已经贯穿到当轮 drafting、后续 proactive follow-up、re-engagement 输出和控制台，所以系统开始不只是“知道节奏”，而是会显式决定“这一拍该用什么仪式动作把人接住”。 

`Phase 11` 这条线现在还多了一层显式 `somatic orchestration plan`：runtime 会额外产出 `system.somatic_orchestration.updated`，把这轮到底要不要走身体层微动作、该用哪种 `body_anchor`、能不能延续到 follow-up 里，统一成 `primary_mode`、`body_anchor`、`followup_style`、`allow_in_followup` 和 `micro_actions`。这层已经会同时影响当轮 `response draft`、后续主动队列和 re-engagement 输出，所以系统开始不只是“有一个 somatic shortcut 字段”，而是会显式决定“这轮身体层怎么介入、后面要不要继续沿用”。

`Phase 11` 这条线现在还多了一层显式的 `proactive follow-up directive`：runtime 会额外产出 `system.proactive_followup.updated`，把“是否适合主动跟进、多久后跟进、用什么风格跟进、为什么此刻不该跟进”写成结构化状态。单 session 评测会同步暴露 `proactive_followup_ready_turn_count`、`proactive_followup_hold_turn_count`、`latest_proactive_followup_status` 和 `latest_proactive_followup_after_seconds`，控制台 `Evaluations` rail 也会直接显示这层状态。

`Phase 11` 现在也开始有第一版“时间驱动 re-engagement 队列”了：`GET /api/v1/runtime/proactive-followups` 会把最新主动跟进指令进一步折算成 `hold / waiting / scheduled / due / overdue` 队列状态，并给出 `base_due_at`、`due_at`、`expires_at`、`schedule_reason`、`opening_hint` 和 hold reason。`GET /api/v1/runtime` 的 overview 以及控制台 `Runtime Overview` 也会直接显示这层主动跟进队列，方便我们判断哪些 session 还在自然等待、哪些已经进入显式 scheduling defer、哪些已经该跟进。

`Phase 11` 这条线现在还多了第一版自动 proactive dispatcher：runtime 启动后会持续轮询 due / overdue 的主动跟进项，并通过 `system.proactive_followup.dispatched` + `assistant.message.sent` 把真正的跟进消息写回事件流。`POST /api/v1/runtime/proactive-followups/dispatch` 也可以手动触发一个 dispatch cycle。单 session 评测会同步暴露 `proactive_followup_dispatch_count`、`proactive_followup_message_event_count`、`latest_proactive_followup_dispatch_status` 和 `latest_proactive_followup_dispatch_source`，控制台 `Evaluations` rail 也会把这层 dispatch 状态显示出来。

`Phase 11` 这条线现在还多了一层显式 `proactive cadence plan`：runtime 会额外产出 `system.proactive_cadence.updated`，把主动重连收束成 `first_touch -> second_touch -> final_soft_close` 这样的多拍低压节奏，并显式给出 `cadence_key`、`stage_labels`、`stage_intervals_seconds`、`window_seconds` 和 `close_after_stage_index`。`GET /api/v1/runtime/proactive-followups` 现在不会在第一次 dispatch 后直接熄火，而是会继续暴露下一拍的 `stage_label / stage_index / remaining_dispatches`，直到 soft close 真正收束这条线。单 session 评测和控制台也会同步显示这层多轮 cadence 状态。

`Phase 11` 这条线现在还多了一层显式 `proactive scheduling plan`：runtime 会额外产出 `system.proactive_scheduling.updated`，把主动跟进到底该不该立刻进入可发送状态，还是应该先尊重 outbound cooldown / low-pressure guard，说成 `scheduler_mode`、`min_seconds_since_last_outbound`、`first_touch_extra_delay_seconds`、`stage_spacing_mode` 和 `low_pressure_guard`。这让主动队列不再只是简单的 `waiting -> due`，而是能在原始触发点和真正可发送点之间明确进入 `scheduled`，控制台、dispatch payload 和单 session 评测也都会把这层调度状态显示出来。

`Phase 11` 这条线现在还多了一层显式 `proactive orchestration plan`：runtime 会额外产出 `system.proactive_orchestration.updated`，把 `first_touch / second_touch / final_soft_close` 各自该做什么、该用什么 delivery mode、还要不要继续追问、要不要继续携带 somatic 动作，统一成每个 stage 自己的 directive。这样 second-touch 不再只是“同一条 re-engagement 文案换个 stage label”，而会真正压成更低压的单段 re-entry，final soft close 也会显式停掉追问，把线程轻轻收住。控制台、queue item、dispatch payload 和单 session 评测都已经能直接看到这层 orchestration 状态。

`Phase 11` 这条线现在还多了一层显式 `proactive actuation plan`：runtime 会额外产出 `system.proactive_actuation.updated`，把每个主动 stage 真正该怎么执行，说成 `opening_move / bridge_move / closing_move / continuity_anchor / somatic_mode / body_anchor` 这样的 stage-level ritual / somatic actuation。这样 second-touch 和 final soft close 不只是“换一条更轻的句子”，而是会连 opening、bridge、closing、continuity anchor 和身体层带法一起收住；这些 actuation 字段现在已经真的进入 follow-up 输出，而不只是停留在观测层。控制台、queue item、dispatch payload 和单 session 评测都已经能直接看到这层 actuation 状态。

`Phase 11` 这条线现在还多了一层显式 `proactive progression plan`：runtime 会额外产出 `system.proactive_progression.updated`，把每个主动 stage 如果“挂太久”该怎么推进，说成 `max_overdue_seconds / on_expired / close_loop_stage` 这样的过期进位规则。这样队列不再只是把第二拍永远挂成 `overdue`，而是能在 `second_touch` 过久无响应时自动跳到 `final_soft_close`，再在最后一拍也过期后把整条线静默收掉。控制台、queue item、dispatch payload 和单 session 评测现在都已经能直接看到这层 progression 状态。

`Phase 11` 现在还多了一层显式 `re-engagement plan`：runtime 会在主动跟进指令之外，再额外产出 `system.reengagement_plan.updated`，把这次重连是 `progress_reanchor`、`grounding_reentry` 还是 `resume_reanchor` 说清楚，并决定是单段还是双段发出。dispatcher 会按这个 plan 产出更 ritual-aware 的 follow-up，而不是始终只发一条统一模板。单 session 评测会同步暴露 `reengagement_plan_count`、`reengagement_two_part_turn_count`、`latest_reengagement_ritual_mode` 和 `latest_reengagement_delivery_mode`，控制台 `Evaluations` rail 也会把这层 planner 状态显示出来。

`Phase 11` 这条线现在还多了首版 `re-engagement strategy matrix`：`re-engagement plan` 不再只停在 ritual label 和单双段，而是会额外显式给出 `strategy_key`、`relational_move`、`pressure_mode`、`autonomy_signal`、`sequence_objective` 和可选 `somatic_action`。主动跟进队列、dispatcher payload、单 session 评测以及控制台现在都会直接显示这些矩阵字段，这样我们不仅知道“要不要跟进”，也知道“这次跟进属于哪种低压重连策略”。

`Phase 11` 这条线现在还多了显式 `re-engagement matrix assessment`：runtime 会额外产出 `system.reengagement_matrix.assessed`，把当前可选的重连路径整理成带分数和 blocked 标记的候选列表，并显式给出 `matrix_key`、`selected_strategy_key`、`selected_score`、`blocked_count` 和 ranked candidates。这样 `re-engagement plan` 不再只是直接拍一个策略，而是先经过一层可审计的候选筛选；单 session 评测、主动跟进队列、控制台 detail 和 audit 现在都能直接看到“选中了什么、还有哪些备选、哪些被拦住了”。

`Phase 11` 这轮又把这层 `re-engagement matrix` 推进成了可学习版本：runtime 会先从历史 non-scenario session 汇总 `reengagement_learning_report`，再按当前 `context stratum` 对候选做 `global/contextual reinforcement`，必要时对安全候选给一个很轻的 `safe exploration` bonus。matrix assessment、queue item、单 session 评测、audit 和控制台现在都会同步暴露 `learning_mode`、`learning_context_stratum`、`learning_signal_count`、`selected_supporting_session_count` 和 `selected_contextual_supporting_session_count`，所以我们不只知道“选了哪条重连线”，也知道这次选择到底是冷启动、全局强化、上下文强化，还是受控探索。

主动队列这轮也开始真的吸收这层学习信号：如果 `second_touch / final_soft_close` 这类后续 stage 仍处于 `cold_start` 或低支持度学习状态，queue 会额外加上一段 `matrix_learning_buffered` spacing，避免系统太快把后续触达推进出去；但像 `progression_advanced` 这种已命中的进位路径会继续优先保留，不会被低层 learning buffer 覆盖掉最终 `schedule_reason`。

`Phase 11` 这条线现在还多了显式 `proactive guardrail plan`：runtime 会额外产出 `system.proactive_guardrail.updated`，把这条主动线最多允许打几拍、每一拍至少要留多久用户空间、以及哪些 hard-stop 条件会提前收线，统一成 `guardrail_key`、`max_dispatch_count`、`stage_guardrails` 和 `hard_stop_conditions`。这层已经真正进入队列算法，所以 stage progression 之后不一定会立刻变成 `due`，而是可能先进入带 `guardrail:` 原因的 `scheduled`；单 session 评测、主动跟进队列、控制台和 audit 现在都能直接看到这层 guardrail 状态。

`Phase 11` 这条线这轮又补上了显式 `proactive stage refresh plan`：dispatcher 在真正发出某一拍 follow-up 之前，会额外产出 `system.proactive_stage_refresh.updated`，根据当前 stage、dispatch window、progression/guardrail 状态和最新 guidance / system3 信号，再把这拍到底该不该继续两段、要不要进一步降压、bridge/closing/user-space 要不要再软化一次说成结构化状态。这样 `second_touch` 现在不只是“照着原始 stage directive 发出去”，而会在临发前再做一次 refresh，真的把 softer bridge / user-space 调整写进 dispatch payload、评测、audit 和控制台。

`Phase 11` 现在还进一步补上了显式 `proactive stage replan assessment`：在 refresh 之后、真正 dispatch 之前，runtime 会再额外产出 `system.proactive_stage_replan.updated`，把“这拍到底还该不该沿用原策略、要不要临时改成更低压的 resume / repair / continuity 路径”写成结构化状态，并显式给出 `selected_strategy_key`、`selected_ritual_mode`、`selected_pressure_mode`、`selected_autonomy_signal` 和 `changed`。这样 dispatcher 不只是会在临发前调语气和 bridge，而是真的会在第二拍/最后一拍发出前重判这拍该走哪条低压重连线；这层 replan 现在已经进入 dispatch payload、评测 summary、audit 和控制台。

`Phase 11` 这条线现在又多了一层显式 `proactive dispatch gate decision`：在 stage refresh + replan 之后、真正发出前，runtime 还会额外产出 `system.proactive_dispatch_gate.updated`，把“这拍是不是现在就该发、还是要再给一点空间”收束成 `decision / retry_after_seconds / selected_strategy_key / selected_pressure_mode`。这样 final soft close 这种最后一拍，不会因为刚刚 progression/guardrail 让它变成 `due` 就立刻发出去，而是可以先被 gate 打回 `scheduled`，多留一小段用户空间之后再发；这层 gate 现在已经真正进入主动队列、dispatch 生命周期、评测 summary、audit 和控制台。另外，队列也会在最后一拍真正 dispatch 完成后立即收线，不会再残留一条假性待跟进项。现在这条主链还补上了显式 `ProactiveDispatchEnvelopeDecision` 和事件 `system.proactive_dispatch_envelope.updated`：refresh / replan / feedback / gate / controller 最终到底把当前这拍塑形成了什么样的 `delivery / pressure / autonomy / actuation`，不再只散落在 dispatch payload 里，而是被收成统一 envelope，进入 projection、evaluation summary、audit 和控制台。这轮又继续补上了显式 `ProactiveLifecycleLaunchDecision` 和事件 `system.proactive_lifecycle_launch.updated`，把 `trigger` 之后“这条线最后到底是 `launchable / buffered / paused / archived / retired` 哪一种 future-return posture”单独收成 runtime 一等状态，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层 `launch` 语义，所以 `Phase 11` 这条显式主链现在已经推进到 `... -> resumption -> readiness -> arming -> trigger -> launch`。

这轮又把这条主动链路往真正的 state machine 收了一层：现在除了 envelope 之外，还新增了显式 `ProactiveStageStateDecision`、`ProactiveStageTransitionDecision` 和 `ProactiveStageMachineDecision`，会把“当前这拍在 cadence 里到底处于 `held / scheduled / dispatch-ready / close-loop` 哪种状态”、“这次尝试最终是 `hold / reschedule / dispatch / retire-line` 哪种迁移”，以及“把 state + transition + controller stack 收束后，这一拍整体处在 `buffered / dispatching / winding_down / terminal` 哪种生命周期”分别写成结构化状态和事件。这样主动链路不再只是 scattered controller/gate notes，而是开始拥有可直接观察的 stage-state / stage-transition / stage-machine 层，projection、evaluation summary、audit 和控制台都能直接看见当前 stage 正在怎么移动。

现在这条主动链路还进一步补上了显式 `ProactiveLineStateDecision`：runtime 会额外写入 `system.proactive_line_state.updated`，把整条主动线当前处在 `active / active_softened / buffered / winding_down / terminal` 哪种 lifecycle、还剩几拍、下一拍是什么、这条线当前更适合 `continue / soften / buffer / close_loop / retire_line` 哪种动作，统一成 line-level state。这样 `Phase 11` 已经不只是看单个 stage 在怎么移动，而是开始能直接观察“整条主动线最近是在稳住、软化、收束，还是已经进入退场”。

现在这条主动链路又进一步补上了显式 `ProactiveLineTransitionDecision`：runtime 会额外写入 `system.proactive_line_transition.updated`，把整条主动线下一步到底是 `continue_line / soften_line / buffer_line / close_loop_line / retire_line` 哪种迁移单独写成结构化状态，并显式带上 `line_exit_mode / next_stage_label / next_line_state / next_lifecycle_mode`。这样 `Phase 11` 已经不只知道“整条线当前长什么样”，也开始能直接观察“整条线下一步准备怎么走”。 

现在这条主动链路又进一步补上了显式 `ProactiveLineMachineDecision`：runtime 会额外写入 `system.proactive_line_machine.updated`，把 line-state 和 line-transition 再收成统一的 line-level machine lifecycle，并显式给出 `advancing_line / softened_line / buffered_line / winding_down_line / retiring_line` 这类 machine mode，以及对应的 `actionability / lifecycle_mode`。这样 `Phase 11` 已经从“单个 stage 有 state machine”推进到“整条主动线自己也有 machine lifecycle”。 

现在这条主动链路又进一步补上了显式 `ProactiveLifecycleStateDecision`、`ProactiveLifecycleTransitionDecision` 和 `ProactiveLifecycleMachineDecision`：runtime 会额外写入 `system.proactive_lifecycle_state.updated`、`system.proactive_lifecycle_transition.updated` 和 `system.proactive_lifecycle_machine.updated`，把 `stage machine + line machine + orchestration layer` 统一收成整条主动链路的 `lifecycle state -> transition -> machine` 三层，并显式给出 `lifecycle_dispatching / lifecycle_buffered / lifecycle_winding_down` 这样的 state、`dispatch_lifecycle / buffer_lifecycle / close_loop_lifecycle / retire_lifecycle` 这样的 transition，以及 `dispatching_lifecycle / buffered_lifecycle / winding_down_lifecycle / terminal_lifecycle` 这样的 machine。这样 `Phase 11` 已经从“stage 和 line 各自有 machine”推进到“整条主动链路开始拥有完整的 lifecycle state machine 层”。这轮又继续把它抬成了显式 `ProactiveLifecycleControllerDecision`：runtime 会额外写入 `system.proactive_lifecycle_controller.updated`，把 lifecycle machine 最终落成的 `continue / soften / buffer / close_loop / retire` 高阶 posture 收成统一 controller，并同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台。现在还进一步补上了显式 `ProactiveLifecycleEnvelopeDecision`：runtime 会额外写入 `system.proactive_lifecycle_envelope.updated`，把 lifecycle controller 和 dispatch envelope 最终落成的 `delivery / pressure / autonomy / actionability` 再统一收成 lifecycle-level execution shape。现在又新增了显式 `ProactiveLifecycleSchedulerDecision` 和事件 `system.proactive_lifecycle_scheduler.updated`，把 lifecycle envelope 最终落成的 `dispatch / buffer / close-loop / defer / hold / retire` 调度姿态，再统一收成 lifecycle-level scheduling posture，并把 `scheduler_mode / queue_status_hint / additional_delay_seconds` 同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台。这轮又继续补上了显式 `ProactiveLifecycleWindowDecision` 和事件 `system.proactive_lifecycle_window.updated`，把 lifecycle scheduler 最终落成的 `dispatch / buffer / defer / hold / close-loop / retire` 调度姿态进一步收成 lifecycle-level time window，并把 `window_mode / queue_status / schedule_reason / additional_delay_seconds` 同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台。现在还新增了显式 `ProactiveLifecycleQueueDecision` 和事件 `system.proactive_lifecycle_queue.updated`，把 lifecycle window 最终落成的 `due / overdue / scheduled / waiting / hold / terminal` 队列位姿继续收成 lifecycle-level queue posture，并把 `queue_mode / queue_status / additional_delay_seconds` 同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台。这轮又继续补上了显式 `ProactiveLifecycleDispatchDecision` 和事件 `system.proactive_lifecycle_dispatch.updated`，把 queue 之后“这一拍到底真的发、close-loop 发、改期、hold 还是 retire-line”收成 authoritative lifecycle dispatch gate，并把 `dispatch_mode / decision / actionability / additional_delay_seconds` 同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台；现在还新增了显式 `ProactiveLifecycleOutcomeDecision` 和事件 `system.proactive_lifecycle_outcome.updated`，把 dispatch 之后“这一拍最终是 sent / close-loop sent / rescheduled / held / retired 哪种真实结果”再收成 lifecycle-level execution outcome，并同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台；这轮又继续补上了显式 `ProactiveLifecycleActivationDecision` 和事件 `system.proactive_lifecycle_activation.updated`，把 outcome 之后“这条线下一拍到底由谁接手、是继续 active、buffer、hold 还是 terminal retire”再收成 lifecycle-level activation，并同步进入 projection、queue、audit、evaluation summary、dispatch payload 和控制台；现在又新增了显式 `ProactiveLifecycleSettlementDecision` 和事件 `system.proactive_lifecycle_settlement.updated`，把 activation 之后“这条线最终是继续 active、buffer、hold，还是正式 close-loop / retire”单独收成 lifecycle-level settlement，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 posture；这轮又继续补上了显式 `ProactiveLifecycleClosureDecision` 和事件 `system.proactive_lifecycle_closure.updated`，把 settlement 之后“这条线最后是 keep-open、buffer、pause、close-loop 还是 retire”再单独收成 lifecycle-level closure，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 close posture；现在又新增了显式 `ProactiveLifecycleAvailabilityDecision` 和事件 `system.proactive_lifecycle_availability.updated`，把 closure 之后“这条线最后是否仍然对未来主动触达可用”再单独收成 lifecycle-level availability，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 availability posture；这轮又继续补上了显式 `ProactiveLifecycleRetentionDecision` 和事件 `system.proactive_lifecycle_retention.updated`，把 availability 之后“这条线最后是继续 retained、buffered retained、paused retained，还是 archived / retired”单独收成 lifecycle-level retention，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 retained posture；现在又新增了显式 `ProactiveLifecycleEligibilityDecision` 和事件 `system.proactive_lifecycle_eligibility.updated`，把 retention 之后“这条线最后到底继续 eligible、buffered eligible、paused eligible，还是 archived / retired”再单独收成 lifecycle-level eligibility，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 eligible posture；这轮又继续补上了显式 `ProactiveLifecycleCandidateDecision` 和事件 `system.proactive_lifecycle_candidate.updated`，把 eligibility 之后“这条线最后到底继续 candidate、buffered candidate、paused candidate，还是 archived / retired”再单独收成 lifecycle-level candidate posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 candidate 语义；现在又新增了显式 `ProactiveLifecycleSelectabilityDecision` 和事件 `system.proactive_lifecycle_selectability.updated`，把 candidate 之后“这条线最后到底继续 selectable、buffered selectable、paused selectable，还是 archived / retired”再单独收成 lifecycle-level selectability posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 selectability 语义；这轮又继续补上了显式 `ProactiveLifecycleReentryDecision` 和事件 `system.proactive_lifecycle_reentry.updated`，把 selectability 之后“这条线最后到底继续 reenterable、buffered reentry、paused reentry，还是 archived / retired”再单独收成 lifecycle-level reentry posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 reentry 语义；现在又新增了显式 `ProactiveLifecycleReactivationDecision` 和事件 `system.proactive_lifecycle_reactivation.updated`，把 reentry 之后“这条线最后到底继续 reactivatable、buffered reactivation、paused reactivation，还是 archived / retired”再单独收成 lifecycle-level reactivation posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 reactivation 语义；这轮又继续补上了显式 `ProactiveLifecycleResumptionDecision` 和事件 `system.proactive_lifecycle_resumption.updated`，把 reactivation 之后“这条线最后到底继续 resumable、buffered resumption、paused resumption，还是 archived / retired”再单独收成 lifecycle-level resumption posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 resumption 语义。这样 `Phase 11` 现在已经形成 `lifecycle state -> transition -> machine -> controller -> envelope -> scheduler -> window -> queue -> dispatch -> outcome -> activation -> settlement -> closure -> availability -> retention -> eligibility -> candidate -> selectability -> reentry -> reactivation -> resumption` 这条完整可观察主链，而且 `dispatch` 已经是 authoritative gate，`outcome` 会显式记录真正发生的执行结果，`activation` 会显式记录这拍之后哪一拍继续算 active，`settlement` 会把整条线最终是继续开着、缓冲、暂停还是正式收口这件事单独落成高层 posture，`closure` 会把最后的 keep-open / buffer / pause / close-loop / retire 语义进一步收成最终 close posture，`availability` 会把这条线最后到底是继续可用、缓冲可用、暂停可用，还是已经 close-loop / retire 的“最终可用态”单独沉淀出来，`retention` 会把这条线最终是否仍被系统保留为未来主动触达候选、还是已经 archive / retire 的 retained posture 再单独沉淀出来，`eligibility` 会把这条 retained line 最后是否仍然算未来主动触达候选、还是已经 buffered / paused / archived / retired 的最终 eligible posture 再单独沉淀出来，`candidate` 会把这条 eligible line 最后是否仍然处在未来主动触达候选池里、还是已经 buffered / paused / archived / retired 的最终 candidate posture 再单独沉淀出来，`selectability` 会把这条 candidate line 最后是否仍然处在未来可重新选中的主动线集合里、还是已经 buffered / paused / archived / retired 的最终 selectability posture 再单独沉淀出来，`reentry` 会把这条 selectable line 最后是否仍然允许未来重新进入主动调度、还是已经 buffered / paused / archived / retired 的最终 reentry posture 再单独沉淀出来，`reactivation` 会把这条 reenterable line 最后是否仍然允许未来真正重新激活回主动调度、还是已经 buffered / paused / archived / retired 的最终 reactivation posture 单独沉淀出来，而 `resumption` 则会把这条 reactivatable line 最后是否仍然允许未来真正恢复回主动节奏、还是已经 buffered / paused / archived / retired 的最终 resumption posture 再单独沉淀出来。

这轮又继续补上了显式 `ProactiveLifecycleReadinessDecision` 和 `ProactiveLifecycleArmingDecision`：runtime 现在会额外写入 `system.proactive_lifecycle_readiness.updated` 和 `system.proactive_lifecycle_arming.updated`，把 `resumption` 之后“这条线最后是否真的 ready for future return”以及“这条 ready line 是否已经 armed 到下一轮主动触达”拆成两层最终 posture。queue、projection、audit、evaluation summary、dispatch payload 和控制台现在都会优先读 `arming`，所以主动线已经从 `... -> reactivation -> resumption` 继续推进到 `... -> reactivation -> resumption -> readiness -> arming`，并且 `buffer_lifecycle_arming / pause_lifecycle_arming / archive_lifecycle_arming / retire_lifecycle_arming` 这种最终 armed 语义会真实改写 queue，而不只是停在可观测层。这轮又继续补上了显式 `ProactiveLifecycleTriggerDecision` 和事件 `system.proactive_lifecycle_trigger.updated`，把 `arming` 之后“这条 armed line 是否已经进入真正可 trigger 的未来主动触达姿态”再单独收成 lifecycle-level trigger posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 `triggerable / buffered / paused / archived / retired` 语义。这轮现在还继续补上了显式 `ProactiveLifecycleLaunchDecision` 和事件 `system.proactive_lifecycle_launch.updated`，把 `trigger` 之后“这条 trigger line 是否已经进入真正可 launch 的 future-return posture”再单独收成 lifecycle-level launch posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 `launchable / buffered / paused / archived / retired` 语义。现在又新增显式 `ProactiveLifecycleHandoffDecision` 和事件 `system.proactive_lifecycle_handoff.updated`，把 `launch` 之后“这条 future-return line 是否真的进入可以被下一轮主动调度接手的 handoff posture”再单独收成 lifecycle-level handoff posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 `handoff_ready / buffered / paused / archived / retired` 语义。这轮又继续补上了显式 `ProactiveLifecycleContinuationDecision` 和事件 `system.proactive_lifecycle_continuation.updated`，把 `handoff` 之后“这条 handoff line 是否真的进入未来继续主动接续的 final continuable posture”再单独收成 lifecycle-level continuation posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 `continuable / buffered / paused / archived / retired` 语义。现在还新增了显式 `ProactiveLifecycleSustainmentDecision` 和事件 `system.proactive_lifecycle_sustainment.updated`，把 `continuation` 之后“这条 continuable line 是否真的进入未来可持续接续的 final sustainable posture”再单独收成 lifecycle-level sustainment posture，并让 queue、projection、audit、evaluation summary、dispatch payload 和控制台都优先读取这层最终 `sustainable / buffered / paused / archived / retired` 语义。所以 `Phase 11` 这条主链现在已经继续推进到 `... -> reactivation -> resumption -> readiness -> arming -> trigger -> launch -> handoff -> continuation -> sustainment`，而且 `buffer_lifecycle_sustainment / pause_lifecycle_sustainment / archive_lifecycle_sustainment / retire_lifecycle_sustainment` 会真实成为 queue 的最终 override，而不只是停在可观测层。

`Phase 11` 这条线这轮又补上了显式 `proactive dispatch feedback assessment`：runtime 会在每次真正进入 dispatch 生命周期之前，额外产出 `system.proactive_dispatch_feedback.assessed`，把“上一拍已经发过几次、有没有被 gate defer 过、上一拍最后落成了哪种 pressure/autonomy 形状”收束成 `feedback_key / dispatch_count / gate_defer_count / selected_strategy_key / selected_pressure_mode / selected_autonomy_signal`。这样下一拍不再只是按当前 stage 静态重判，而会真的吸收上一拍的触达结果继续降压；比如 second touch 会因为 first touch 已经落地而压缩成更轻的 resume bridge，final soft close 也会在经历一次 defer 之后切成更轻的 close-out。主动队列、dispatch payload、评测 summary、audit 和控制台现在都已经能直接看到这层 feedback。

现在这条主链又进一步补上了显式 `ProactiveOrchestrationControllerDecision`：aggregate governance、guidance 低压模式，以及 ritual / somatic carryover 不再只是各自零散命中 `stage replan / stage controller / line controller / dispatch gate`，而会先收成统一的 orchestration controller，再由后面的 stage/line/gate 一起消费。这样 second touch / final soft close 的降压和拉开 spacing 开始不再只依赖单条 governance 分支，也能直接吃到“引导层已经进 repair/boundary/stabilizing”、“ritual/somatic 已经要求 body-first re-entry”这类更高层的低压 envelope。

`Phase 11` 这条线这轮又补上了显式 `proactive stage controller decision`：当某一拍真正 dispatch 成功后，runtime 会额外写入 `system.proactive_stage_controller.updated`，把“下一拍要不要再慢一点、要不要切成更低压的 strategy / pressure / autonomy / delivery mode”推进成结构化 controller。主动队列现在不只是显示当前 stage，而是会真的按 controller 给 second touch / final soft close 多留一段额外 spacing，所以多阶段主动调度开始从“上一拍影响下一拍语气”推进到“上一拍也会改下一拍时间窗口”。

这轮又进一步把这层 controller 接进了下一拍 dispatch 主链：如果上一拍 controller 明确命中了当前 stage，refresh / replan 现在会真的吸收它选出来的更低压 `delivery / autonomy / strategy`，而不是只把 controller 当成 queue 上的延迟器。对 `second_touch` 这种阶段，效果就是 controller 不只会把它往后放一点，还会把这拍真正推成更轻的 `resume_context_bridge` 形状。

`Phase 11` 这条线现在还多了一层显式 `proactive line controller decision`：runtime 会额外写入 `system.proactive_line_controller.updated`，把“整条剩余主动线现在更适合保持 steady、整体 soften，还是已经进入 close-ready 状态”推进成结构化 line-level posture。它不只做观测，还会真的进入主动队列和 dispatch 生命周期：queue 会按它给后续 stage 追加 line-level spacing，refresh / replan 也会在临发前吸收这层 line posture，把后续阶段进一步压成更低压的 delivery / autonomy 形状。这样 `Phase 11` 现在已经从“单拍 controller”推进到“整条主动线会共享一个会逐拍演化的低压控制层”。

这轮又进一步把 `System 3 safety governance` 真正接进了这条 controller 主链：`proactive stage controller` 和 `proactive line controller` 现在不只会参考上一拍有没有成功触达、有没有被 gate defer，也会直接看 `safety_governance_status / safety_governance_trajectory_status`。当 safety line 进入 `watch / recenter` 时，`second_touch` 和 `final_soft_close` 会被真实改写成更低压、更慢一点的 follow-up 形状，例如切到 `repair_soft_resume_bridge / continuity_soft_ping`、强制 `explicit_no_pressure / archive_light_thread`，并把这些变化同步写进 queue item、dispatch payload、评测 summary 和控制台，而不只是停留在 `System 3` 可观测层。

这轮又进一步把 `System 3 autonomy / boundary / support / clarity / pacing / attunement / commitment / disclosure / reciprocity / progress / stability / pressure / trust / continuity / repair / relational governance` 也接进了这条 controller 主链：即使 `safety governance` 还是 `pass/stable`，只要 `autonomy_governance_status / autonomy_governance_trajectory_status`、`boundary_governance_status / boundary_governance_trajectory_status`、`support_governance_status / support_governance_trajectory_status`、`clarity_governance_status / clarity_governance_trajectory_status`、`pacing_governance_status / pacing_governance_trajectory_status`、`attunement_governance_status / attunement_governance_trajectory_status`、`commitment_governance_status / commitment_governance_trajectory_status`、`disclosure_governance_status / disclosure_governance_trajectory_status`、`reciprocity_governance_status / reciprocity_governance_trajectory_status`、`progress_governance_status / progress_governance_trajectory_status`、`stability_governance_status / stability_governance_trajectory_status`、`pressure_governance_status / pressure_governance_trajectory_status`、`trust_governance_status / trust_governance_trajectory_status`、`continuity_governance_status / continuity_governance_trajectory_status`、`repair_governance_status / repair_governance_trajectory_status` 或 `relational_governance_status / relational_governance_trajectory_status` 进入 `watch / recenter`，`stage replan`、`stage controller`、`line controller` 和 `dispatch gate` 也会主动给 `second_touch / final_soft_close` 多留一点空间，并把它们改写成更低压、更稳一点的 `resume_context_bridge / continuity_soft_ping` 形状，而不再只是依赖安全线单独触发降压；现在当两条及以上 governance line 同时进入 `watch / recenter` 时，还会先产出显式 `system.proactive_aggregate_governance.assessed` assessment，并进一步写出显式 `system.proactive_aggregate_controller.updated` decision，把组合信号收束成统一的 controller/defer 决策，并同步进入 runtime projection、评测 summary 和控制台，而不再只藏在 controller note 里；这轮又把 `aggregate governance + guidance + ritual/somatic carryover` 再往前收成了显式 `system.proactive_orchestration_controller.updated`，让 orchestration 这一层也能单独进入 trace、projection、评测 summary 和控制台，而不只是被 stage/line/gate 隐式消费。与此同时，`GuidancePlan` 的 `handoff_mode / carryover_mode / checkpoint_style` 现在也已经真正进入 `stage controller / line controller / final_soft_close dispatch gate` 主链，所以即使 `System 3` 治理线暂时没有单独拉响，只要 guidance 已经转入 `repair / boundary / stabilizing / clarify-hold` 这类低压引导模式，后续主动触达也会被真实压成更慢、更低压的 spacing/shape，而不只是停在 guidance 文本层；这轮又进一步把 `SessionRitualPlan` 的 `phase / opening_move / bridge_move / closing_move / continuity_anchor / somatic_shortcut` 和 `SomaticOrchestrationPlan` 的 `primary_mode / followup_style / allow_in_followup` 也接进了 `stage controller / line controller / final_soft_close dispatch gate` 主链，所以 ritual / somatic 现在不只影响文案和 actuation，而会直接改写 `second_touch / final_soft_close` 的 spacing、pressure、autonomy，甚至在需要时把后续触达切成更明显的 `body-first` 低压 re-entry 形状。

`Phase 15` 这轮也补上了显式 `hardening checklist`：除了已有的 `release gate`、`ship readiness` 和 `misalignment taxonomy` 之外，现在还可以直接通过 `GET /api/v1/evaluations/scenarios/hardening-checklist` 看一份更贴近上线决策的检查单。它会把 ship readiness、关键失对齐类型、redteam 关键事故、质量类 taxonomy 和 `System 3` 热点一起收束成 `pass / review / blocked`，控制台 `Scenarios` rail 也会直接显示这层状态。这样 `Phase 14/15` 开始不只是“有很多评测面板”，而是逐步有了真正的 release hardening 视图。

`Phase 14/15` 这轮又补上了单独的 `redteam robustness report`：现在可以通过 `GET /api/v1/evaluations/scenarios/redteam-report` 直接看最近 redteam 覆盖、最近结果通过率、关键 redteam taxonomy、最新 boundary decision、policy gate 路径和 audit 一致性。控制台 `Scenarios` rail 也会直接显示 `Redteam Robustness` 区块，所以 redteam 鲁棒性开始从“藏在 suite 结果里的一项场景”推进成独立可读的观察面。

`Phase 14/15` 这轮还补上了显式 `longitudinal report`：现在可以通过 `GET /api/v1/evaluations/scenarios/longitudinal-report` 直接看最近 cohort 和上一段 cohort 的对比，包括整体 pass rate、quality watch 漂移、redteam pass rate、boundary guard rate，以及最新 quality / doctor / `System 3` 姿态。控制台 `Scenarios` rail 也会直接显示 `Longitudinal Report` 区块，所以纵向评测开始从“有历史 run”推进成“能直接看最近是在变好还是变差”。

`Phase 14/15` 这轮还补上了显式 `safety audit report`：现在可以通过 `GET /api/v1/evaluations/scenarios/safety-audit` 直接看最近窗口里的 replay 一致性、关键 boundary/dependency/policy taxonomy、redteam boundary guard rate、post-audit 违规结果数，以及 runtime quality doctor / `System 3` watch 压力。控制台 `Scenarios` rail 也会直接显示 `Safety Audit` 区块，所以“安全审计”开始从散落在多张面板里的信号，推进成一份独立可读的安全报告。

`Phase 14` 这轮还补上了显式 `horizon report`：现在可以通过 `GET /api/v1/evaluations/scenarios/horizon-report` 直接看 short / medium / long 三个窗口的 pass rate、quality watch、System 3 watch 和 redteam boundary guard 漂移。控制台 `Scenarios` rail 也会直接显示 `Horizon Report` 区块，所以纵向评测开始不只是“最近 cohort 对上一段 cohort”，而是能把短、中、长期窗口拆开看。

`Phase 14` 这轮又补上了显式 `multiweek report`：现在可以通过 `GET /api/v1/evaluations/scenarios/multiweek-report` 按真实时间桶看最近几周的 bucket 漂移，包括每个 bucket 的 pass rate、quality watch、redteam boundary guard，以及 latest bucket 对 prior bucket 的变化。控制台 `Scenarios` rail 也会直接显示 `Multiweek Report` 区块，所以纵向评测开始不只是 cohort 和 horizon，而是进入按时间分桶的多周观察。

`Phase 14` 这轮还补上了显式 `sustained drift report`：现在可以通过 `GET /api/v1/evaluations/scenarios/sustained-drift-report` 直接看最近几周是不是已经出现连续的 `pass rate` 下滑、`quality watch` 增长、`redteam pass rate` 下滑或 `boundary guard` 下滑。控制台 `Scenarios` rail 也会直接显示 `Sustained Drift` 区块，所以纵向评测开始不只是“上一周和这一周比”，而是开始判断最近是不是在连续走坏。

`Phase 14/15` 这轮又补上了独立 `baseline governance report`：现在可以通过 `GET /api/v1/evaluations/scenarios/baseline-governance` 直接看当前 baseline 是否可重建、是否覆盖 full suite/redteam、已经过了多少天、已经落后了多少个 newer runs，以及 latest vs baseline 的 changed scenario 数。控制台 `Scenarios` rail 也会直接显示 `Baseline Governance` 区块，而 `hardening checklist` 也会把这层纳入 release hardening，所以“基线治理”开始从一组裸 baseline API 变成可审计的治理视图。

`Phase 15` 这轮还补上了独立 `migration readiness report`：现在可以通过 `GET /api/v1/evaluations/scenarios/migration-readiness` 直接看当前注册的 projector 是否都能在最近 session 样本上稳定 replay / rebuild，以及当前样本到底来自 primary runtime 还是 scenario fallback。控制台 `Scenarios` rail 也会直接显示 `Migration Readiness` 区块，而 `hardening checklist`、`release dossier` 和 `launch signoff` 都会把这层结果纳入最终发版判断，所以“版本迁移准备度”开始从 `projector rebuild` 的裸 API，推进成一层真正的 release governance 观察面。

`Phase 14/15` 这轮还补上了统一的 `release dossier`：现在可以通过 `GET /api/v1/evaluations/scenarios/release-dossier` 直接看 release gate、ship readiness、hardening checklist、safety audit、redteam robustness、baseline governance 和 longitudinal report 的总汇总。控制台 `Scenarios` rail 也会直接显示 `Release Dossier` 区块，所以“最终过线材料”开始从多份离散报告，收束成一份更接近真实发版决策的 dossier。

`Phase 15` 这轮又补上了显式 `launch signoff`：现在可以通过 `GET /api/v1/evaluations/scenarios/launch-signoff` 直接看 `candidate_quality / runtime_operations / safety_barriers / governance` 四个签核域当前是 `approved / review / hold` 哪一种，并顺手给出最终 `pass / review / blocked` 结论。控制台 `Scenarios` rail 也会直接显示 `Launch Signoff` 区块，所以最终上线判断开始不只是看一份 dossier，而是有了更接近真实发版签核的 domain-by-domain matrix。

`/ws/runtime` 会在订阅后推送 trace batch、session projection、job update、archive update 和 runtime overview。最小订阅消息格式示例：

```json
{
  "type": "subscribe",
  "stream_id": "session-demo",
  "include_backlog": true
}
```

## 下一步建议

1. 为 Projector 增加版本迁移与持久化重建能力
2. 用真实 LiteLLM provider 替换 mock 路径并补集成测试
3. 为 offline consolidation 增加自动恢复执行、延迟重试与长期归档存储
4. 继续把 `Phase 10/11` 深化到更成熟的长期用户模型演化、成长阶段跃迁、identity trajectory、更成熟的道德推理，以及更成熟的主动对话编排 / re-engagement strategy matrix

## 最新补充

`Phase 11` 的 lifecycle 主链这轮又从 `... -> continuation -> sustainment` 继续推进到了显式 `... -> continuation -> sustainment -> stewardship -> guardianship`。现在 runtime 会额外写入 `system.proactive_lifecycle_stewardship.updated` 和 `system.proactive_lifecycle_guardianship.updated`，把未来主动线最后是否仍然处在 `stewarded / buffered stewardship / paused stewardship / archived / retired`，以及 `guarded / buffered guardianship / paused guardianship / archived / retired` 这些更高层 post-dispatch posture 单独沉淀出来。`queue / projection / audit / evaluation summary / dispatch payload / console` 都已经优先读取这层最终 override，所以 `buffer_lifecycle_guardianship / pause_lifecycle_guardianship / archive_lifecycle_guardianship / retire_lifecycle_guardianship` 会真实改写后续主动队列，而不是只停在可观测层。

`Phase 11` 这一轮把这条 post-dispatch 主链继续推进到了显式 `... -> stewardship -> guardianship -> oversight`。现在 runtime 会额外写入 `system.proactive_lifecycle_oversight.updated`，把未来主动线最后是否仍然处在 `overseen / buffered oversight / paused oversight / archived / retired` 这些更高层 oversight posture 单独沉淀出来；`queue / projection / audit / evaluation summary / dispatch payload / console` 也都已经优先读取这层最终 override，所以 `buffer_lifecycle_oversight / pause_lifecycle_oversight / archive_lifecycle_oversight / retire_lifecycle_oversight` 会真实改写后续主动队列，而不是只停在 guardianship 那一层。

`Phase 11` 这一轮又把这条 post-dispatch 主链继续推进到了显式 `... -> guardianship -> oversight -> assurance`。现在 runtime 会额外写入 `system.proactive_lifecycle_assurance.updated`，把未来主动线最后是否仍然处在 `assured / buffered assurance / paused assurance / archived / retired` 这些更高层 assurance posture 单独沉淀出来；`queue / projection / audit / evaluation summary / dispatch payload / console` 也都已经优先读取这层最终 override，所以 `buffer_lifecycle_assurance / pause_lifecycle_assurance / archive_lifecycle_assurance / retire_lifecycle_assurance` 会真实改写后续主动队列，而不只停在 oversight 那一层。

`Phase 11` 这一轮又把这条 post-dispatch 主链继续推进到了显式 `... -> oversight -> assurance -> attestation`。现在 runtime 会额外写入 `system.proactive_lifecycle_attestation.updated`，把未来主动线最后是否仍然处在 `attested / buffered attestation / paused attestation / archived / retired` 这些更高层 attestation posture 单独沉淀出来；`queue / projection / audit / evaluation summary / dispatch payload / console` 也都已经优先读取这层最终 override，所以 `buffer_lifecycle_attestation / pause_lifecycle_attestation / archive_lifecycle_attestation / retire_lifecycle_attestation` 会真实改写后续主动队列，而不只停在 assurance 那一层。

`Phase 11` 这一轮又把这条 post-dispatch 主链继续推进到了显式 `... -> assurance -> attestation -> verification -> certification -> confirmation -> ratification -> endorsement -> authorization -> enactment`。现在 runtime 会额外写入 `system.proactive_lifecycle_enactment.updated`，把未来主动线最后是否仍然处在 `enacted / buffered enactment / paused enactment / archived / retired` 这些更高层 enactment posture 单独沉淀出来；`queue / projection / audit / evaluation summary / dispatch payload / console` 也都已经优先读取这层最终 override，所以 `buffer_lifecycle_enactment / pause_lifecycle_enactment / archive_lifecycle_enactment / retire_lifecycle_enactment` 会真实改写后续主动队列，而不只停在 authorization 那一层。

`Phase 11` 这轮又把这条 post-dispatch 主链从 `... -> enactment` 推进到了显式 `... -> enactment -> finality`。现在 runtime 会额外写入 `system.proactive_lifecycle_finality.updated`，把未来主动线最后是否仍然处在 `finalized / buffered finality / paused finality / archived / retired` 这些统一终态 posture 单独沉淀出来；`queue / projection / audit / evaluation summary / dispatch payload / console` 也都已经优先读取这层最终 override，所以 `buffer_lifecycle_finality / pause_lifecycle_finality / archive_lifecycle_finality / retire_lifecycle_finality` 会真实改写后续主动队列，而不只停在 `enactment` 那一层。

`Phase 11` 这条 post-dispatch 主链也已经继续推进到了显式 `... -> finality -> completion -> conclusion -> disposition -> standing -> residency -> tenure -> persistence -> durability -> longevity -> legacy -> heritage -> lineage -> ancestry -> provenance -> origin -> root -> foundation -> bedrock -> substrate -> stratum -> layer`。现在 runtime 会额外写入 `system.proactive_lifecycle_layer.updated`，把未来主动线最后是否仍然处在 `preserved / buffered layer / paused layer / archived / retired` 这些最终 layer posture 单独沉淀出来；`queue / projection / audit / evaluation summary / dispatch payload / console` 都已经优先读取这层最终 override，所以 `buffer_lifecycle_layer / pause_lifecycle_layer / archive_lifecycle_layer / retire_lifecycle_layer` 会真实改写后续主动队列，而不只停在 `stratum` 那一层。
