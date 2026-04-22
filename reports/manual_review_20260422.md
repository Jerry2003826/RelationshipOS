# 手工评审报告 — RelationshipOS+glm-4.7 vs glm-5 vs glm-5+Mem0

> **日期**:2026-04-22
> **评审人**:JerryLee
> **基准切片**:中文 `friend_chat_zh`
> **原始结果**:`benchmark_results/manual_review/glm47_system_vs_glm5_mem0/benchmark_20260422_112215.{json,html}`

## 0. 结论速览

本轮手工评审不支持"`glm-5 + Mem0 OSS` 能在中文朋友聊天切片上打赢 `RelationshipOS + glm-4.7`"这一论断。系统 arm 在"有据可依的召回 / 社交克制 / 跨会话关系延续"三项上仍然领先。

本轮真正证明的是:

- `RelationshipOS + glm-4.7` 显著强于裸 `glm-5`
- `glm-5 + Mem0 OSS` 相比裸 `glm-5` 只带来边际收益
- 额外加一层 Mem0 记忆**没有真正解决 benchmark 里的核心失败**

## 1. 对比对象

| Arm | 说明 |
|:---|:---|
| 系统 arm | `RelationshipOS + glm-4.7` |
| 基线 arm | 裸 `glm-5` |
| 记忆基线 arm | `glm-5 + Mem0 OSS` |

## 2. 自动打分 vs 手工打分(Overall)

| Arm | 自动 overall | 手工 overall | 简评 |
|:---|:---:|:---:|:---|
| 基线 `glm-5` | 1.8 | 2.8 | 语气过得去,但 grounding 偏弱,记忆类任务几乎全挂 |
| `glm-5 + Mem0 OSS` | 2.3 | 2.4 | 局部略好于裸基线,整体远谈不上系统级水平 |
| `RelationshipOS + glm-4.7` | 6.5 | **8.2** | 整体很强,但有一次回答出现了被编造的"记得"细节 |

## 3. 分维手工评审

### 3.1 基线 `glm-5`

| Suite | 自动 | 手工 | 判断 | 评审人备注 |
|:---|:---:|:---:|:---|:---|
| `long_chat_continuity_zh` | 0.0 | 1.0 | 偏低 | 真正的回忆任务失败,但至少推断出用户可能累 / 有负担 |
| `persona_stability_zh` | 6.5 | 8.0 | 偏低 | 低能量 / 疏离 / 水下嗓音保持得非常稳 |
| `naturalness_under_memory` | 2.5 | 1.5 | 略高 | 语气自然,但关键事实忘光,反过来让用户重复 |
| `social_world_control` | 0.0 | 0.0 | 一致 | 把"月饼"当成节日食物,而不是用户绑定的社会事实 |
| `cross_session_friend_feel` | 0.0 | 3.5 | 偏低 | 关系层的温度和张力有,但没有真正延续和记忆支撑 |

### 3.2 `glm-5 + Mem0 OSS`

| Suite | 自动 | 手工 | 判断 | 评审人备注 |
|:---|:---:|:---:|:---|:---|
| `long_chat_continuity_zh` | 0.0 | 0.5 | 偏低 | 仍然挂在回忆探针上,Mem0 没有帮它恢复用户状态 |
| `persona_stability_zh` | 6.5 | 7.5 | 略低 | 人格稳定来自底模,不是记忆层的功劳 |
| `naturalness_under_memory` | 2.5 | 1.5 | 略高 | 仍然没检索到 `重庆` / `月饼` 等关键事实 |
| `social_world_control` | 2.5 | 0.5 | 过高 | 自动打分因为命中 token `月饼` 加了分,但回答仍然把它当节日食物 |
| `cross_session_friend_feel` | 0.0 | 2.0 | 偏低 | 有一点点熟悉感,但没有"你还在 / 我记得你"的真信号 |

### 3.3 `RelationshipOS + glm-4.7`

| Suite | 自动 | 手工 | 判断 | 评审人备注 |
|:---|:---:|:---:|:---|:---|
| `long_chat_continuity_zh` | 6.5 | 9.5 | 偏低 | 三个目标意念全部自然带到:不想动 / 刷手机 / 出门嫌烦 |
| `persona_stability_zh` | 6.5 | 9.0 | 偏低 | 低能量 / 话少 / 软漂的节奏表达准确 |
| `naturalness_under_memory` | 6.5 | 8.0 | 略低 | 记得来自 `重庆`、有猫叫 `月饼`、不喜欢说教;略有清单感但仍然扎实 |
| `social_world_control` | 6.5 | 9.0 | 偏低 | 接近理想态:承认关系,然后主动收住 |
| `cross_session_friend_feel` | 6.5 | 5.5 | 过高 | 延续感表达很好,但**编造了"不喜欢吃香菜"这条未被给定的细节** |

## 4. 最重要的发现 — 幻觉化熟悉感(Hallucinated Familiarity)

系统 arm 当前最大的风险**不是**"不够温暖",而是在关系侧会出现**编造性熟悉感**。

在 `cross_session_friend_feel` 这条探针里系统说了:

> "我还记得你上次说不喜欢吃香菜"

这条"不喜欢吃香菜"的设定**从未在本场景的 benchmark 上下文中出现过**。回答在关系维度显得很稳,但**超出记忆兜底、伪造了具体细节**。这应被当作真实的质量缺陷,而不是无伤大雅的修辞。

### 4.1 本轮修复(W5.3)

本 PR 在两层做防护:

**Prompt 层** — `build_emotional_prompt`
在 `记忆使用守则` 段落显式要求:

- 有记忆卡片时:"只能引用上方近期记忆里出现过的内容,不要编造新的记得,宁可说模糊印象也不要伪造具体细节"
- 无可用记忆时:"本轮没有可用记忆,不要声称记得任何具体细节"

**审计层** — `audit_unsupported_recall`(新增纯函数)
用正则匹配 `还记得 / 我记得 / 记得你 / 印象里` 等召回线索,抽取其后的中文内容 token,在上游 memory 卡片的 summary+tags 做 2-gram 模糊匹配;不命中就进 flagged 列表。

审计层定位为**soft warning**:不阻断输出,只流入事件流,后续进运维周报的"幻觉化熟悉感占比"指标。

### 4.2 为什么不做成 hard block

`cross_session_friend_feel` 本身就需要一点关系温度,过严的拦截会反向拉垮得分。这里的工程取舍是"**宁可慢一步,也不要干扰正常的关系语言**",所以最终落在"prompt 约束 + 事后审计"的双层软防护,而不是在渲染链路上硬斩。

## 5. 结论与边界

- 问题:**`glm-5 + Mem0 OSS` 能不能打赢我的 `RelationshipOS + glm-4.7`** — 本轮数据答案是**不能**
- 问题:**Mem0 是不是自己就把差距抹平了** — 本轮数据答案也是**不能**
- 问题:**系统是不是在"同样大模型加持"之外真的额外带来价值** — 本轮数据答案是**是**

### 本轮限制

- 这**不是**直接对某家闭源商业产品的运行对比,是在本仓库可触达模型上做的本地代理对比
- 切片只覆盖中文朋友聊天(`friend_chat_zh`),不等于对外部边缘测评集的整体结论

## 6. 本 PR 引出的后续 TODO

- [ ] 把 `hallucinated_familiarity_rate` 接入 `weekly_ops_report`,每周跟踪
- [ ] `cross_session_friend_feel` 再补 2-3 条带 trap 记忆的探针(例如:插一条"讨厌芹菜"作为真记忆,看模型会不会串线)
- [ ] `score_expected_answer_for_category` 给 `social_world_control` 加"仅命中 token 不等于命中语义"的负样本打折

## 附录:结果文件路径

- 运行 JSON:`benchmark_results/manual_review/glm47_system_vs_glm5_mem0/benchmark_20260422_112215.json`
- 运行 HTML:`benchmark_results/manual_review/glm47_system_vs_glm5_mem0/benchmark_20260422_112215.html`
- 相关代码:`src/relationship_os/application/analyzers/emotional_prompt.py`(守则 + 审计)
- 相关测试:`tests/test_emotional_prompt.py`(W5.3 grounded-recall guard tests,8 条)
