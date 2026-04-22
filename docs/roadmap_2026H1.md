# RelationshipOS 2026 H1 Roadmap

> 目标：2026.9 秋招前把 Router v2 主线 + 持续学习闭环 + EmotionalExpert LoRA 三件事跑通。

## W0 (4/22–4/26) · 清扫与对齐

- [ ] PR #1 关闭（已过时）
- [ ] PR #2 ruff lint fix → Ready for Review
- [ ] PR #3 rebase 到 PR #2 新 HEAD → Ready for Review
- [ ] PR #4 ruff lint fix → Ready for Review
- [ ] profile README (Jerry2003826/Jerry2003826) 首版
- [ ] Pinned 调整：替换 CandleCraft → agentic-workflow-Elastic
- [ ] 归档 desktop-tutorial / cs- / CandleCraft
- [ ] RelationshipOS 加 `docs/COMPLIANCE.md`
- [ ] aigirl 加 `docs/COMPLIANCE.md`
- [ ] DeepSeek 简历删除 "MoE" 术语

## W1 (4/27–5/3) · PR #5 runtime-wire-router-v2
- 构造 `VanguardRouterV2` 单例
- `route_user_turn` 换为 `self._router.decide`
- 新增 `_generate_light_recall_reply`（memory k=5 + 轻 LLM）
- match/case 三分支派发
- env `ROUTER_V2_MODE=shadow|live` 灰度
- 3 条 utterance 集成测试
- 更新 CHANGELOG + 架构图

## W2 (5/4–5/10) · 持续学习基础设施
- PR #6 JsonlShadowLogger + 日志轮转 + 查询脚本
- PR #6 GitHub Actions 周级回训 cron + eval gate
- PR #7 `analyzers/user_profile.py` EMA 128 维 + prompt 注入

## W3 (5/11–5/17) · 三条 AI 半自主功能
- PR #8 `scripts/llm_prelabel.py` + review + merge
- PR #9 `scripts/memory_compactor.py` 夜间记忆压缩
- PR #10 周日 DeepSeek-R1 运维周报邮件到 2054634601@qq.com

## W4 (5/18–5/24) · EmotionalExpert LoRA
- 底座 Qwen-2.5-1.5B-Instruct
- 500 轮人工标注好/坏回复
- LoRA rank=8 训练脚本 + eval
- A/B 人工 blind rating +10% 情感接住率目标

## W5 (5/25–5/31) · 文档 + 简历 + 面试
- `docs/continual_learning.md` 四层学习栈
- 3 张架构图
- 20 个面试官追问 Q&A
- DeepSeek / 华为 CloudBU 简历 v4
