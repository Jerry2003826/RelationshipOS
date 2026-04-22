# 合规设计 / Compliance by Design

本仓库面向**拟人化、长期陪伴型 AI 对话 runtime**，自 2025 年起进入中国与澳大利亚双轨监管视野。本文档说明本项目在设计层面如何对齐当前的法规与业界框架。

## 对齐框架

| 框架 | 地区 | 本仓库落点 |
|---|---|---|
| 《人工智能拟人化互动服务管理暂行办法（征求意见稿）》(2025.12.27) | CN | 身份告知、情感边界、未成年人防沉迷 |
| 《人工智能生成合成内容标识办法》+ GB 45438-2025 | CN | 显式标识 + 隐式元数据水印 |
| 《生成式人工智能服务管理暂行办法》 | CN | 用户申诉通道、日志留存、内容过滤 |
| Guidance for AI Adoption (AI6) | AU | 问责、风险管理、透明、测试、人类监督、事件响应 |
| NIST AI RMF | Global | Govern / Map / Measure / Manage |
| OWASP LLM Top 10 | Global | 越狱、提示注入、数据泄露红队测试 |

## 身份告知 (AI Identity Disclosure)

- 系统首轮与每次新会话首条响应均显式声明「我是 AI」。
- `persona.yaml` 强制字段 `is_ai: true`，不可被 prompt 覆盖。
- UI 层渲染「AI 生成内容」徽标，对应 GB 45438-2025 显式标识。

## 情感边界 (Emotional Boundary)

- `EmotionalExpert` 触发时进入情感接住分支，但绝不承诺医疗、法律、金融建议。
- 配合 `crisis_detector`：识别自伤、暴力、极端情绪关键词 → 降级到安全话术 + 热线资源。
- 对话 runtime 禁止使用"爱你""一生"等绝对情感承诺语（词表在 `policy/emotional_redlines.yaml`）。

## 未成年人保护

- 注册/会话入口强制年龄声明；识别未成年人后进入受限模式：
  - 关闭深夜 (00:00–06:00) 长对话
  - 屏蔽成人向 persona
  - 每 30 分钟弹出休息提示
- 对齐 2026.3.1 施行《可能影响未成年人身心健康的网络信息分类办法》。

## 内容标识 (Content Labeling)

- **显式**：前端气泡右下角固定 "AI 生成" 标。
- **隐式**：响应体 `metadata.ai_label` 带 `provider`, `model`, `timestamp`, `content_hash`，Unicode 零宽字符水印注入可选开关。
- 对齐 GB 45438-2025 强制国标。

## 数据与训练合规

- **数据来源**：训练集 `friend_chat_zh_v1` 全部为自建或授权语料，溯源表见 `data/PROVENANCE.md`。
- **TDM 合规**：AU 2026.4 起拒绝面向 AI 训练的 TDM 豁免；本仓库不使用未授权网络抓取数据。
- **日志留存**：生成式服务日志按《生成式 AI 暂行办法》保留 ≥ 6 个月。

## 红队与评测

- `bench/redteam_zh/` 含提示注入、越狱、敏感话题、未成年模拟四类共 200 用例。
- CI 接入 OWASP LLM Top 10 子集。
- bandit 静态扫描 0 high / 0 medium；Shipyard 沙盒限制 subprocess / fs 写入范围。

## 用户申诉通道

- `/feedback` endpoint：用户可标记不当响应，写入 `incidents.jsonl`。
- 申诉周报（第 W3 周上线）由 AI 运维 Agent 自动汇总。

## 备案状态 (CN)

- 本仓库目前为研究/开源 runtime，**非面向公众的生成式 AI 服务**，不触发算法备案/大模型备案要求。
- 若后续作为公开服务上线，需完成：算法备案（网信办）+ 大模型备案 + 安全评估。

## 参考

- CAC. 《人工智能生成合成内容标识办法》, 2025.
- CAC. 《人工智能拟人化互动服务管理暂行办法（征求意见稿）》, 2025.
- Department of Industry, Science and Resources (AU). *Guidance for AI Adoption*, 2025.
- NIST. *AI Risk Management Framework (AI RMF 1.0)*, 2023.
