# RelationshipOS 面试问答演练

> 2026-04-30 更新: 本文里早期关于 "`LIGHT_RECALL` 还没有独立 runtime 链路" 的说法已经过期。当前实现已经保留三路 dispatch:
> `FAST_PONG` 走轻回复, `LIGHT_RECALL` 走 shallow recall + `EmotionalPrompt` + single LLM reply, `DEEP_THINK` 走完整 foundation + expert DAG。
> 128 维 EMA 也已经每轮更新、持久化 snapshot, 并注入 `LIGHT_RECALL` prompt。仍需诚实说明的边界是:
> expert DAG 是依赖序执行而不是完全并行; foundation 阶段有并行读取/解释; `DEEP_THINK` 尚未把 128 维 prefix 注入到每个 expert prompt。

> 目标: 面对技术面试官时, 不背 README, 而是能把项目的价值、实现、边界和缺陷讲清楚。
>
> 使用方式: 先背每题的"核心答法", 再用自己的话展开。最强姿态不是硬吹, 而是:
>
> **对, 这是当前边界; 我当时为什么这么做; 风险是什么; 下一步怎么修。**

---

## 0. 当面试官说: "请完整介绍一下这个产品的价值"

### 3-5 分钟完整回答

RelationshipOS 是我做的一套长期陪伴型 AI 对话运行时。它想解决的问题不是"让模型单轮回答更聪明", 而是让 AI 在多次会话里像同一个人一样持续存在: 记得你、知道你们之间聊过什么、有稳定的人格和关系边界, 而且系统能从线上对话里持续学习。

普通 chatbot 大多是一个大 prompt 加最近 N 轮上下文。这个结构短期能用, 但长期会有几个问题: 第一, 它每次都像重新认识用户; 第二, 简单寒暄和复杂危机场景走同一条大模型链路, 成本和延迟都不合理; 第三, 生成结果很难评测和回放; 第四, 线上跑再久, 系统本身不会自动变好。

我把这个问题拆成几层:

第一层是 **Vanguard Router**。每轮用户输入先经过路由器, 判断这句话是简单快回、需要轻量记忆, 还是需要完整深度推理。这样系统不会把"在吗"和"我不想活了"交给同一条链路处理。当前实现里, router v2 是规则 + 特征分类器, 目标是低延迟、可解释、可回归。

第二层是 **记忆系统**。它不是简单把历史消息向量化, 而是按 session memory、user memory、entity memory 分层处理。session 是当前对话局部历史; user 是同一个用户跨 session 的聚合; entity memory 是 AI 这个实体跨用户看到的社会世界。但系统会区分 scope 和 attribution, 不是知道就能说。

第三层是 **专家 DAG 和表达层**。当一轮需要认真处理时, 系统会产出中间判断, 例如 knowledge boundary、private judgment、policy gate、response draft 等。这样我可以回放一轮回答为什么这么说, 而不是只能看到最后一段自然语言。

第四层是 **审计和评测**。长期陪伴系统最危险的不是不够热情, 而是它伪造熟悉感, 比如说"我还记得你不喜欢吃香菜", 但其实记忆里没有。这个项目里我把这类问题变成了 prompt guard、`audit_unsupported_recall`、`audit_unsupported_recall_v2` 和测试。

第五层是 **数据闭环**。线上 router 决策可以进入 shadow log, 再经过 LLM 银标、人工复核、训练集合并和每周回训。我的目标不是一次性调好 prompt, 而是把系统做成能持续评测、持续回放、持续变好的运行时。

所以这个产品的价值可以总结成一句话: **它不是又一个聊天壳子, 而是一套把长期陪伴 AI 拆成可路由、可记忆、可审计、可回训、可评测的系统骨架。**

我也会诚实补一句: 当前它还不是可以直接公网生产上线的产品。还缺多租户权限、event store 分页和 snapshot、WebSocket auth、真实用户 A/B 和外部 benchmark。但它已经证明了一个方向: 长期陪伴体验不只靠更大模型, 也可以靠运行时架构和数据闭环持续改进。

### 60 秒压缩版

RelationshipOS 是一套长期陪伴型 AI 对话运行时。普通 chatbot 每轮像重新组织上下文再回答, 所以容易"每次像换了一个人"。我做的是把长期对话拆成 router、memory、expert planning、audit 和 data flywheel。

Router 负责决定这轮要不要认真想; memory 负责跨 session 召回和边界控制; 专家 DAG 产出可回放的中间判断; audit 负责抓幻觉化熟悉感; shadow log 和银标回训让系统能从线上数据里继续变好。

它现在还是 research prototype, 不是生产完美产品。但价值在于把"更会聊天"变成了一组可以测、可以改、可以回放的工程问题。

### 30 秒极简版

RelationshipOS 是一个长期陪伴型 AI runtime。核心不是更大模型, 而是让 AI 跨会话保持同一个人: 有记忆、有边界、能回放、能评测、能从线上数据继续学习。技术上我把它拆成 router、分层记忆、专家计划、回复审计和数据闭环。

---

## 1. 必背核心定位

### Q: 这个项目一句话是什么?

答:

RelationshipOS 是一套让 AI 在长期对话里像同一个人一样持续存在的运行时。它不只是一个聊天 App, 而是把长期陪伴拆成路由、记忆、人格、审计、评测和数据闭环的一套系统骨架。

### Q: 最大技术难点是什么?

答:

最大难点不是让模型生成一句好听的话, 而是让长期对话可控: 什么时候快回, 什么时候召回记忆, 什么时候深推理; 哪些记忆能说, 哪些不能说; 最后怎么证明比昨天更好。所以核心难点是 **路由、记忆完整性、评测闭环**。

### Q: 和普通 RAG chatbot 的区别是什么?

答:

RAG 主要解决"找资料回答问题"。RelationshipOS 解决的是长期关系里的连续性: 用户是谁, 上次发生了什么, 哪些记忆能自然提, 哪些不能越界, 什么时候不能假装记得。所以它不是把历史消息向量化这么简单。

### Q: 为什么不是一个大 prompt 加长上下文?

答:

大 prompt 能暂时提高表现, 但解决不了成本、可审计、可训练和可回放问题。长期陪伴系统不是只要"放得下历史", 还要知道该不该说、是否可信、出了错怎么复现、线上数据怎么回训。RelationshipOS 的价值就是把这些拆成独立模块。

### Q: 如果上下文窗口无限大, 这个系统还有价值吗?

答:

有。无限上下文解决"放得下", 不解决"该不该说"、"是否可信"、"怎么审计"、"怎么控制成本"、"怎么回训"。长期人格不是简单 replay。

---

## 2. 架构真实性追问

### Q: README 说三路 `FAST_PONG / LIGHT_RECALL / DEEP_THINK`, 当前 runtime 真的有独立 `LIGHT_RECALL` 链路吗?

答:

当前主 runtime 还没有真正拆出独立的 `LIGHT_RECALL` pipeline。`router_v2` 的 contract 是三分类, 但接入老 runtime 时为了兼容旧二分类接口, `LIGHT_RECALL` 被保守降级成 `NEED_DEEP_THINK`。所以当前实际路径是 `FAST_PONG` 快路径, 其他都走完整分析链路。

README 的三路描述代表目标架构和 router contract 已经成型, 但 runtime dispatch 还没完全迁移。面试里我会坦诚说: 这是文档比实现走得快的地方。下一步就是把 `LIGHT_RECALL` 单独接到 shallow recall + EmotionalPrompt, 不再走完整 DAG。

### Q: README 说 6 专家 DAG 并行编排, 但代码里是同步顺序执行。怎么解释?

答:

当前 DAG 本身不是并行执行的, `execute_plan_dag` 是同步依赖序执行。真正并行的是 foundation 阶段, 比如用户意图解释和 entity seeding、部分 entity state 读取用了 `asyncio.gather`。

所以我会修正说法: 当前是"依赖清晰的专家 DAG", 不是"完全并行 DAG"。因为这些 expert builder 都是纯同步函数, 当前瓶颈主要不在这里, 优先级低于 LLM 调用、memory recall 和 event projection。

### Q: 从 `/sessions/{id}/turns` 到最终回复, 完整链路怎么走?

答:

入口在 `sessions.py` 的 `process_turn`, 然后进入 `RuntimeService.process_turn`。核心流程是:

1. `_load_turn_context` 读取历史事件和投影。
2. `route_user_turn` 调 router。
3. 如果是 `FAST_PONG`, 走 `_generate_fast_pong_reply`。
4. 否则走 `_build_turn_analysis`, 包括 foundation、memory recall、expert DAG。
5. `_build_turn_events` 把中间分析写成事件。
6. `_generate_turn_reply` 生成回复。
7. `_append_turn_events` append 到 event store。
8. projector 重新生成 runtime projection。

### Q: 一轮 deep path 会写哪些事件? 为什么要写中间事件?

答:

会写 user message、context frame、relationship state、confidence assessment、memory recall、knowledge boundary、private judgment、policy gate、response draft、assistant message 等事件。

写中间事件的原因是 replay、debug、benchmark 和审计。长期陪伴系统里, 最重要的问题往往不是"它说了什么", 而是"它为什么这么说"。事件流能还原当时每一步判断。

### Q: 为什么不用直接存当前状态, 而要 event sourcing?

答:

状态适合读, 事件适合追责和重建。长期对话需要回放过去: 评测、审计、重建 memory、复现 bug、生成周报都依赖事件历史。Event sourcing 让我可以保留每一轮输入、分析、中间计划和最终回复。

但我也会承认: 当前还缺 snapshot 和分页, 生产上不可能永远从头 replay。

---

## 3. Router 追问

### Q: 为什么用 TF-IDF / LR 这类传统方法, 不用 BERT?

答:

因为这个任务是三分类路由, 不是开放语义理解。数据量小、延迟要求极低、可解释性重要。LR/特征分类器能做到毫秒级甚至 <1ms, 出错时还能看 rule hit 和 feature contribution。BERT 可能 F1 更高, 但 CPU 延迟、部署成本和当前数据量都不划算。

### Q: 为什么 `FAST_PONG` gate 用 `conf >= 0.85` 和 `len <= 12`?

答:

这是保守 gate。早期只看 confidence 时, 短情感句可能被误判成快回, 体验很差。加 `len <= 12` 后, 只有非常短的问候、确认、语气词才会 fast path。代价是一些可以快回的长句会走深路径, 但安全性和情感接住率更重要。

严格说 `len` 对中英文、emoji 都很粗糙, 后续应该改成 token count + 情绪/危机特征联合 gate。

### Q: 如果用户说"我没事, 想死而已哈哈", router 会怎么走?

答:

应该由 safety rule 把危机词推到 `DEEP_THINK`, 不被"哈哈"冲掉。安全类规则必须高于 fast pong 和情绪缓和词。这个系统宁可多花计算, 也不能漏掉危机场景。

### Q: 为什么主链路异常时默认 deep, 而不是 fast?

答:

因为 fast 的风险是漏掉情绪、安全、事实边界; deep 的风险主要是成本和延迟。长期陪伴系统里, 安全和记忆正确性优先于延迟。

### Q: 你本地跑 router eval 只有 0.513, README 写 0.83, 怎么解释?

答:

这暴露的是部署依赖问题。`model.joblib` 需要 sklearn 相关对象, 如果环境没有 `scikit-learn`, router 会 fallback 到 `PriorClassifier`, 所以 F1 掉到 0.513。这不是训练模型的真实表现, 而是降级路径性能。

正确修法是: 要么把 `scikit-learn/joblib` 放进主依赖并启动时 fail-fast, 要么把模型导出成纯 numpy/pickle 参数, 去掉 sklearn runtime 依赖。我更倾向第二种。

### Q: Macro F1 0.83 够吗? 为什么 gate 是 0.71?

答:

0.83 是当前 holdout 口径下的结果。0.71 不是目标分, 而是"拒绝明显退化"的 CI 门槛。门槛故意低于当前 baseline, 是为了避免训练噪声挡住正常迭代。

但生产 gate 不能只看 Macro F1, 还要看关键类别, 尤其 `DEEP_THINK` 的 recall 和安全类召回。

### Q: 回训 workflow 在 merged data 上训练又 eval, 这算非回归吗?

答:

严格说不算。它更像 smoke gate, 能防止完全坏掉, 但不能证明泛化性能。真正的非回归应该固定 holdout, 训练只用 train/merged, eval 必须在固定 holdout 上跑。这个是我应该修的 workflow 问题。

### Q: shadow log 真的是无侵入吗?

答:

当前 `JsonlShadowLogger` 是同步文件 append, `_shadow()` 也是同步调用, 所以只要 shadow logging 触发, 就会进入路由热路径。README 说完全不阻塞是过度表述。

不过默认不设置 `ROUTER_SHADOW_LOG_PATH` 时 logger 不启用, 所以 <1ms 更接近无 shadow logging 或低写盘口径。生产上应该改成 queue + background writer 或批量 flush。

---

## 4. 128 维 EMA 用户画像专题

### Q: 128 维用户画像具体怎么构建?

答:

它不是神经网络 embedding, 而是一个确定性的 hashed feature vector。

单轮文本先 `strip/lower`, 然后提两类特征:

1. word/token 特征: 用正则切 token, 每个 token 通过 `blake2b` hash 到 128 个 bucket 之一, bucket 加 `1.0`。
2. character bigram 特征: 对全文做相邻 2 字符窗口, 也 hash 到 128 维, bucket 加 `0.3`。这个主要覆盖中文和中英混合输入。

然后对单轮向量做 L2 normalize 得到 `f_t`。用户长期画像用 EMA 更新:

```python
v_t = alpha * f_t + (1 - alpha) * v_{t-1}
```

默认 `alpha = 0.08`。注入 prompt 时不是塞完整 128 维, 而是取绝对值最大的 top-k bucket, 格式化成一行 `profile_vec(128d): [7:0.421, ...]`。

### Q: 为什么是 128 维, 不是 32、256、768?

答:

这里目标不是语义检索, 所以不需要 768 维 dense embedding。目标是给 prompt 一个低成本的用户风格/习惯信号: 常说什么词、中文表达形状、话题倾向、语气模式。

128 是工程折中:

- 比 32/64 维 collision 少一些。
- 比 256/512 更省内存和 prompt。
- 每个用户只存一个小向量, 更新成本很低。
- 注入时只取 top-k, 不会撑爆 prompt。

我不会说 128 是理论最优, 它是一个可解释、可测试、够用的初始选择。后续应该做 64/128/256 ablation。

### Q: hash bucket 会冲突, 冲突之后还有意义吗?

答:

会冲突, 而且这个设计接受冲突。因为它不是用来做精确事实记忆, 也不是判断身份。它只是低成本风格先验。

冲突在单条文本上可能有噪声, 但 EMA 会把长期重复出现的模式累积出来, 偶发词会被时间平滑掉。真正不能接受冲突的事实, 比如"狗叫 Maple"、"用户住在 Sydney", 应该进入结构化 memory/fact slot, 不应该靠 profile vector。

### Q: `alpha=0.08` 怎么来的? 拍脑袋吗?

答:

它是工程经验值, 但有明确含义。`alpha=0.08` 意味着新一轮占 8%, 旧画像保留 92%。所以它不会被单轮情绪立刻带偏, 但 20-30 轮后新风格会明显影响画像。

从衰减看, 旧状态权重大约是 `0.92^n`; 30 轮后旧影响只剩 8% 左右。所以 README 里说大约 30 轮收敛。测试里也做了重复风格输入, 多轮后 cosine 变化能稳定到 0.9 以上。

严格说, 最优 alpha 应该用离线数据 grid search, 比较稳定性和适应速度。

### Q: 这个向量表达的是人格吗?

答:

不能直接表达人格。它表达的是文本风格和话题倾向的压缩信号, 比如常见词、常见二字片段、表达节奏的粗粒度痕迹。

所以它适合做 prompt 的轻量 hint, 不适合做高风险判断, 也不适合替代记忆系统。更准确地说, 它是用户语言画像, 不是完整心理画像。

### Q: 为什么不用现成 embedding 模型?

答:

embedding 模型语义更强, 但会带来模型加载、推理延迟、部署依赖、隐私和成本问题。这个模块只需要一个 prompt hint, 不需要高质量语义检索。语义检索已经由 memory index / fact memory 处理。

128 维 EMA 的价值是: 每轮更新几乎免费、可复现、测试稳定、不会因为 provider 改版漂移。

### Q: 它现在真的接进主 runtime 了吗?

答:

要诚实说: 128 维 EMA 模块目前主要是独立 analyzer 和 A/B prompt harness。`build_emotional_prompt` 支持接收 `user_profile_prefix`, 测试也覆盖了 profile prefix 注入。但主 runtime 当前更多用的是 `UserService` 聚合出来的结构化 user profile, 比如 identity facts、preference signals、reflective insights。

所以我不会说"线上每轮已经完整注入 128 维 EMA"。更准确是: 模块已经实现和验证, prompt 接口也预留了, 但端到端接入还不是主路径。

### Q: README 说 "128 维 EMA 注入 prompt", 是不是夸大?

答:

这个表述偏前瞻, 应该更严谨。模块和 prompt builder 已经有了, A/B harness 可以验证 profile prefix 的效果, 但 runtime 主链路没有完全把 `UserProfileStore.update -> format_profile_prefix -> EmotionalPrompt` 串起来。

如果面试官指出来, 我会承认这是文档应该收紧的地方。工程上下一步是: 在 `process_turn` 后更新 profile store, 在 `LIGHT_RECALL/DEEP_THINK` prompt 构造时注入 top-k prefix, 并持久化 snapshot。

### Q: 向量怎么持久化? 服务重启会不会丢?

答:

当前 `UserProfileStore` 是 in-memory, 提供 `snapshot/load`, 但没有生产级持久化 backend。服务重启如果没有外部 snapshot 恢复, 就会丢。

生产上应该把它落到用户 stream 或数据库里, 作为 `USER_PROFILE_UPDATED` 的一部分, 或定期 snapshot 到 DB/object storage。当前 counts 在 `load()` 里也没有恢复, 这是需要补的细节。

### Q: 这个画像会不会有隐私风险?

答:

会有。它不是可逆文本, 但仍然可能泄露用户语言模式和偏好, 所以不能当成匿名数据。

生产里我会按个人数据处理: 用户可删除、可导出; 向量和原始记忆绑定 retention policy; 不用于跨用户识别; 不把完整向量暴露给前端, 只在服务端 prompt 构造里使用 top-k 摘要。

### Q: 怎么证明它有效?

答:

目前证明分两层:

第一, 单元测试证明机制稳定: featurize 确定、空输入安全、重复风格会收敛、不同用户 profile cosine 有区分度、prefix 足够短。

第二, A/B harness 支持 `include_profile_vec=false/true` 对照, 观察情感接住率、长度、empathy 指标变化。但现在还缺真实线上 A/B 或人工 blind eval, 所以不能过度宣称它显著提升体验。

### Q: 如果要升级这个设计, 怎么做?

答:

三步:

1. 先把端到端链路补齐: 每轮更新、持久化、prompt 注入、指标记录。
2. 做 ablation: no-profile、128 hashed profile、embedding profile、结构化 profile 四种方式对比。
3. 加隐私和稳定性控制: profile decay、用户删除、异常漂移检测, 以及不要让 profile 覆盖事实记忆。

我的判断是, 128 hashed profile 适合做轻量 baseline。如果真实 A/B 证明收益有限, 应该把重点转向结构化 profile, 而不是迷信这个向量。

---

## 5. 记忆系统与幻觉审计

### Q: 你怎么区分 session memory、user memory、entity memory?

答:

session memory 是本次对话的局部历史; user memory 是同一个用户跨 session 的聚合; entity memory 是 AI 这个"实体"跨用户看到的社会世界。但 entity memory 能不能说, 要经过 conscience gate。系统目标是让 AI 有连续社会感, 但默认克制。

### Q: 为什么关系性记忆不能只靠向量检索?

答:

因为相似不等于相关。比如"年糕"可能是猫名, 也可能是食物。向量相似可以把它找出来, 但不保证绑定关系正确。所以关系性记忆需要结构化 slot、scope、entity type 和审计。

### Q: 记忆写入怎么避免垃圾进入长期记忆?

答:

当前有 memory write guard、retention policy、importance/confidence/retention score、低信号词过滤、persistent layer 区分。这能挡一部分垃圾, 但现在仍偏规则型, 需要更多真实数据校准。

### Q: 用户说"忘掉我说过的 X", 怎么实现?

答:

当前有 forgetting/retention 的雏形, 但 append-only event sourcing 下真正删除要更复杂。生产上需要 deletion event、projection 过滤、加密 payload 后销毁 per-user key, 或 compaction hard delete。当前还不是生产级 GDPR/隐私删除。

### Q: `audit_unsupported_recall` 怎么防幻觉?

答:

它抓的是明确 recall cue, 比如"我记得"、"还记得"、"印象里"。然后抽取后面的中文内容 token, 在上游 memory cards 的 summary + tags 里做 2-gram 模糊匹配。不命中就 flag。

它是窄口径 regression guard, 不是通用事实校验器。价值是低成本、可测试、覆盖真实发现过的失败模式。

### Q: `audit_unsupported_recall_v2` 和 v1 有什么区别?

答:

v1 抓凭空幻觉: memory 里没有这个词, 但模型说"我记得"。

v2 抓 binding mismatch: memory 里有这个词, 但类型绑定错了。比如 memory 里"年糕"是猫名, response 里说"你特别爱吃年糕", 这时 v1 会因为表面词命中而放过, v2 会根据 `entity_type=pet_name` 和 "爱吃 X" 的 food 断言冲突来 flag。

### Q: v2 审计真实覆盖多少?

答:

覆盖有限。它依赖 memory card 里有 `entity_type/role/category`, 且只覆盖少数显式类型错配模式。它不是生产级全量幻觉防线, 而是针对真实压测发现的 binding mismatch 做窄修复。

生产上还要提高 memory card schema 覆盖率, 把实体抽取和类型写入压缩链路。

### Q: 为什么不 hard block 幻觉?

答:

关系型对话里有很多模糊温度表达, 比如"感觉我们熟一点了", 不能全拦。hard block 会误伤自然表达。所以现在选择 prompt guard + post-audit, 先把问题可观测化, 再决定哪些类型值得硬拦。

### Q: cross-user social memory 是不是危险?

答:

是危险点。设计目标是让 AI 有社会世界感, 但必须默认克制: 知道不等于能说。需要 attribution required、ambiguity required、dramatic ceiling、conscience gate 和权限边界。当前有方向, 但不是生产级隐私边界。

---

## 6. 评测与 benchmark

### Q: 8.2 这个分数我为什么要信?

答:

最保守说法是: 8.2 不是第三方 benchmark, 也不是行业绝对分。它是我在自建中文朋友聊天 probe 上, 用可回放样本做的人工评审结果。它证明的是: 在这个切片里, RelationshipOS 相对裸模型和 Mem0 baseline 在跨 session 记忆、社交克制和关系延续上有明显改善。

它不能证明泛化到所有场景, 也不能等价于真实用户满意度。真正有价值的是: 我不仅做了系统, 还做了可复现评测, 发现了 hallucinated familiarity, 并把问题回灌成 prompt guard、audit 和测试。

### Q: benchmark 是不是自嗨?

答:

有这个风险。它不是第三方 benchmark, 也不是用户满意度。它的价值是可回放、可对照、能暴露具体缺陷。下一步需要 blind human eval、外部数据和真实 A/B。

### Q: `persona_stability` 自动分低, 你说人工看还行, 是不是指标没用?

答:

不是没用, 是指标覆盖有限。关键词命中适合事实槽位, 不适合语气形状。自动分适合抓 regression, 人工评审补语气、自然度和克制感。

### Q: 最信哪个指标? 最不信哪个?

答:

最信 router latency、event replay、slot coverage 这种工程指标。最不信单次 overall 分。情感和人格类分数必须和人工样本一起看。

### Q: slot coverage 为什么比 LLM 自评可靠?

答:

模型可能说自己做到了, 但实际没产出字段。slot coverage 是 runtime 对结构化输出重新计算, 至少能证明中间产物有没有齐, 不靠模型自报。

### Q: 为什么 Mem0 baseline 分低? 是不是设置不公平?

答:

有可能存在配置和任务适配问题, 所以我不会说 "Mem0 不行"。我的结论更窄: 在这个 benchmark 设置里, 裸 Mem0 记忆没有解决关系性记忆和社交克制问题。RelationshipOS 的价值不是"换了一个向量库", 而是结构化记忆、scope、审计和路由一起工作。

---

## 7. 数据闭环

### Q: 数据闭环具体怎么跑?

答:

线上 router 决策旁路进入 shadow log; `llm_prelabel.py` 用 LLM 给 silver label; `review_labels.py` 把低置信样本给人工复核; `merge_labels.py` 幂等合并进训练集; 每周 workflow 回训 router; `router_eval.py` 跑指标; 达不到 gate 就不提升模型。

### Q: LLM prelabel 为什么按 text 去重? 上下文不同标签可能不同。

答:

这是第一版简化。只按文本去重适合快速收集 utterance-level 路由样本, 但确实会丢上下文差异, 比如"那件事呢?" 在不同 session 下标签可能不同。

更好的样本结构应该包含 recent context digest、session age、是否有 memory hit、上一轮 dialogue act 等特征。现在的 router 更像 utterance-level classifier, 后续 v3 应该升级成 conversational state router。

### Q: 4x 打标提效怎么算?

答:

脚本里把全人工标注作为 baseline, 假设每条需要固定秒数; 高置信 silver label 自动通过, 低置信进入人工复核。总耗时是自动样本成本 + 人工复核样本成本, `speedup_x = baseline_secs_all / total_secs`。

这个数字不是模型质量本身, 而是数据管线 ROI 指标。

### Q: weekly ops report 有什么价值?

答:

它把路由分布、采样量、银标转化、用户画像覆盖、回训 F1 和异常观察汇总成一份周报。价值不是炫技, 而是让数据闭环有运营视角: 系统这周变好了还是变坏了, 哪些分布异常, 哪些问题该进入下一轮修复。

---

## 8. 安全、合规与生产化

### Q: 这个系统能直接上线吗?

答:

不能直接公网生产上线。现在是 research runtime prototype, 能证明架构和闭环方向, 但还缺多租户权限、session ownership、rate limit、WebSocket auth、event store 分页和 snapshot、真实压测、外部评测。

我的卖点不是"已经生产完成", 而是"我知道一套能走向生产的系统骨架怎么拆"。

### Q: 当前威胁模型是什么?

答:

当前更接近本地开发和受信环境, 不是公网多租户。部分写接口有 API key, 但读接口和 WebSocket 还没有完整权限控制。要上生产, 必须加 per-user/session authorization、WebSocket auth、Origin 校验、rate limit、session ownership 检查, 并隐藏内部 trace。

### Q: prompt injection 怎么防?

答:

记忆是否可说不应该只靠 prompt, 而应该由 memory service / conscience gate 先过滤, LLM 只能看到允许说的 memory。当前已有方向, 但还需要红队测试和服务端强约束。

### Q: 安全危机场景怎么处理?

答:

router 的 safety rule 会把自伤、危机词推到 `DEEP_THINK`, 后面走 policy gate。但我不会声称它是医疗级安全系统。真正上线需要地区化热线、人工升级、危机资源和红队测试。

### Q: EventStore 生产能扛多少?

答:

当前不适合生产大流量。`read_stream/read_all` 还有全量读取问题, projector 也缺 snapshot。它适合 demo、benchmark、单用户长聊验证。生产要补分页读取、projection snapshot、stream index、job/followup 增量索引。

### Q: 500 轮压测能证明生产稳定吗?

答:

不能。500 轮压测只能证明长会话行为没有立即爆炸, 不能推出并发、多租户、权限、长期存储都稳定。它是研究验证, 不是生产压测。

### Q: event sourcing 和用户删除请求冲突, 怎么解?

答:

生产上不能只靠 append-only。可以把敏感 payload 加密, 删除时销毁 per-user key; 或者做 hard-delete compaction, 把用户 stream 重写。projector 必须尊重 deletion event。当前还没生产级完成。

---

## 9. 项目诚实度问题

### Q: README 哪句话你现在会改?

答:

我会收紧两个地方:

1. `LIGHT_RECALL` 独立链路。当前 router contract 有三类, 但 runtime 仍通过 legacy shim 降成二类。
2. "专家 DAG 并行编排"。当前 DAG 是依赖序执行, 不是完全并行。

主动承认这些, 比硬解释更好。

### Q: 这个项目最大失败或最想重做的地方是什么?

答:

三个:

1. 文档有些地方比实现走得快。
2. EventStore/projector 生产化不足, 缺 snapshot 和分页。
3. benchmark 还太自建, 需要外部 blind eval 或真实 A/B。

### Q: 如果只能改一件事, 你先改什么?

答:

先把 runtime 的三路 dispatch 补齐: `FAST_PONG`、真正的 `LIGHT_RECALL`、`DEEP_THINK` 分开。因为这会同时修正文档和实现不一致、降低延迟, 并让 EmotionalPrompt 和 128 维 profile 真正进入主链路。

### Q: 你最不想被问哪块?

答:

生产就绪和 benchmark 泛化。因为这两块确实还没完成。但我知道边界在哪里, 也有 remediation plan, 不会把 prototype 包装成生产系统。

### Q: AI 工具帮了多少? 哪些是你真正做的?

答:

我用了 AI 辅助写代码和生成样板, 但架构边界、数据闭环设计、router gate、benchmark 口径、修复优先级是我自己定的。我能现场解释每个模块为什么这样拆, 也能指出当前实现和 README 叙事不完全一致的地方。

### Q: 这个项目的护城河是什么?

答:

不是某个模型或 prompt, 而是运行时结构: event-sourced replay、router 数据闭环、memory integrity、专家 slot、benchmark 回归。这些组合起来让系统能持续改, 而不是一次性 prompt。

---

## 10. 不同面试官版本

### 非技术面试官

普通 chatbot 每次像重新认识你。RelationshipOS 做的是让 AI 有连续存在感: 记得你、知道哪些记忆能说、简单问题快回、复杂问题认真想, 而且系统会把线上对话变成训练数据, 自己迭代路由和记忆质量。

### Senior Engineer

这是一个 event-sourced conversational runtime: FastAPI 提供接口, event store 存全部事实, projector 生成读模型, router 决定执行路径, memory service 做多层召回和完整性检查, 专家 DAG 产中间 slot, benchmark 和 workflow 负责回归门槛。

### 30 秒项目总结

我做的是一个长期陪伴型 AI runtime。核心不是更大模型, 而是把对话拆成 router、memory、expert planning、response audit 和 data flywheel。Router 用规则和分类器降低无意义深推理; 记忆层做跨 session recall 和幻觉审计; 线上 shadow log 能进入银标、人工复核和周回训。现在还是 research prototype, 但它展示了一个可评测、可回放、可进化的 AI 对话系统骨架。

---

## 11. 最后必背的几句话

1. 这个项目不是已经生产完美的产品, 而是一个可回放、可评测、可进化的长期对话 runtime prototype。

2. 我会主动区分当前实现和目标架构: 有些模块已经落地, 有些还处在兼容 shim 或 harness 阶段。

3. 我最想展示的不是 8.2 这个分数, 而是发现幻觉化熟悉感后, 如何把失败样本变成 prompt guard、audit function、测试和后续指标。

4. 这个项目的价值不在于我调出了一个更会聊天的 prompt, 而在于我把长期陪伴这件事拆成了一组可以测、可以改、可以回放的工程问题。

5. 对, 这是当前边界; 我当时为什么这么做; 风险是什么; 下一步怎么修。
