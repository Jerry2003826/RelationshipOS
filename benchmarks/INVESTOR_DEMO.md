# Investor Demo Script

## What To Open

1. `benchmark_results/official_edge_demo/latest/latest.html`
2. `benchmark_results/official_edge_demo/latest/latest_中文复盘.md`

## 30-Second Positioning

“RelationshipOS 不是普通聊天模型，也不是给聊天模型外挂一层记忆。  
它是一个长期关系运行时。它能在小模型和 edge 约束下，稳定地记住关键事实、区分记忆归属，并把复杂能力压缩进可演示的时延预算。” 

## 3-5 Minute Flow

### 1. 先讲 benchmark 设计

- Baseline：MiniMax `M2-her`
- Memory baseline：MiniMax `M2-her + Mem0`
- System：RelationshipOS edge runtime

### 2. 只强调 3 个指标

- `factual_recall_lite`
- `cross_user_attribution`
- `latency_budget`

### 3. 解释为什么这 3 项是产品价值

- 能不能记住事实
- 能不能分清“这是谁的记忆”
- 能不能在 edge 预算里跑出来

### 4. 结尾口径

“所以我们的优势不是更会聊天，而是更像一个可持续运行的关系系统。” 

## 风险控制

- 不做现场自由提问 benchmark
- 不把 full runtime/Postgres 榜当成主舞台
- 不切换实验模型
- 默认只用官方 edge 榜和官方最新 HTML 页面
