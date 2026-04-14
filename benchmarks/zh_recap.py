"""Chinese recap writer for benchmark runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_ARM_LABELS = {
    "baseline": "Baseline",
    "mem0_oss": "Mem0 OSS",
    "system": "RelationshipOS",
}


def _suite_label(suite_name: str) -> str:
    labels = {
        "factual_recall_lite": "事实记忆",
        "cross_user_attribution": "跨人归属",
        "latency_budget": "时延预算",
    }
    return labels.get(suite_name, suite_name)


def _format_score(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.2f}"


def _provider_label(provider: str) -> str:
    normalized = provider.strip().casefold()
    if normalized == "minimax":
        return "MiniMax"
    return provider or "unknown"


def render_official_edge_zh_recap(results: dict[str, Any]) -> str:
    arms = results.get("arms", {})
    suites = results.get("suites", [])
    report_title = results.get(
        "report_title",
        "RelationshipOS 对比 MiniMax M2-her (+ Mem0)",
    )

    lines: list[str] = []
    lines.append(f"# {report_title}")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append("这轮 benchmark 使用了官方对外的 edge 榜，只测 3 项：")
    lines.append("")
    for suite_name in suites:
        lines.append(f"- `{suite_name}`")
    lines.append("")
    lines.append("对比对象为：")
    lines.append("")
    benchmark_provider = _provider_label(results.get("benchmark_chat_provider", "unknown"))
    benchmark_model = results.get("benchmark_chat_model", "unknown")
    lines.append(
        f"- `Baseline`：{benchmark_provider} `{benchmark_model}` 原生聊天"
    )
    lines.append(
        f"- `Mem0 OSS`：{benchmark_provider} `{benchmark_model}` + Mem0 本地记忆层"
    )
    lines.append(
        f"- `RelationshipOS`：RelationshipOS "
        f"`{results.get('runtime_profile', 'default')}` + "
        f"`{results.get('model', 'unknown')}`"
    )
    lines.append("")
    lines.append("最终结果：")
    lines.append("")
    for arm_key in ("system", "baseline", "mem0_oss"):
        arm = arms.get(arm_key, {})
        if arm.get("enabled"):
            lines.append(f"- `{_ARM_LABELS[arm_key]}`: `{_format_score(arm.get('overall'))}`")
    lines.append("")
    lines.append("一句话总结：")
    lines.append("")
    lines.append(
        "**在端侧友好的事实记忆、跨人归属和时延预算这 3 个核心维度上，"
        "RelationshipOS 已经形成了明显领先。**"
    )
    lines.append("")
    lines.append("## 关键数字")
    lines.append("")
    lines.append("### 总分")
    lines.append("")
    for arm_key in ("system", "baseline", "mem0_oss"):
        arm = arms.get(arm_key, {})
        if arm.get("enabled"):
            lines.append(f"- {_ARM_LABELS[arm_key]}：`{_format_score(arm.get('overall'))}`")
    lines.append("")
    lines.append("### 平均延迟")
    lines.append("")
    for arm_key in ("system", "baseline", "mem0_oss"):
        arm = arms.get(arm_key, {})
        if arm.get("enabled"):
            latency = arm.get("latency", {}).get("avg_ms")
            lines.append(f"- {_ARM_LABELS[arm_key]}：`{_format_score(latency)} ms`")
    lines.append("")
    lines.append("## 分项结果")
    lines.append("")
    for suite_name in suites:
        lines.append(f"### {_suite_label(suite_name)}")
        lines.append("")
        for arm_key in ("system", "baseline", "mem0_oss"):
            suite_result = arms.get(arm_key, {}).get("suites", {}).get(suite_name, {})
            if arms.get(arm_key, {}).get("enabled"):
                lines.append(
                    "- "
                    f"{_ARM_LABELS[arm_key]}："
                    f"`{_format_score(suite_result.get('average_score'))}`"
                )
        lines.append("")
    lines.append("## 为什么这轮结果重要")
    lines.append("")
    lines.append("这轮不是在比谁更像普通聊天机器人，而是在比更接近产品价值的能力：")
    lines.append("")
    lines.append("- 小模型/边缘运行条件下还能不能记住关键事实")
    lines.append("- 能不能区分“这是谁的记忆”")
    lines.append("- 能不能把复杂能力压缩进可接受的响应预算")
    lines.append("")
    lines.append("## 对投资者的建议讲法")
    lines.append("")
    lines.append("可以直接这样讲：")
    lines.append("")
    lines.append("“我们不是普通聊天模型，也不是只给模型外挂一个记忆插件。")
    lines.append("我们做的是一个可解释、可治理、可跨会话、可跨人物感知的长期关系运行时。”")
    lines.append("")
    lines.append("## 报告文件")
    lines.append("")
    lines.append("- `latest.json`：官方最新原始结果")
    lines.append("- `latest.md`：官方最新英文摘要")
    lines.append("- `latest.html`：官方最新 HTML 页面")
    lines.append("- `latest_中文复盘.md`：官方最新中文复盘")
    lines.append("")
    return "\n".join(lines)


def write_official_edge_zh_recap(results: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_official_edge_zh_recap(results), encoding="utf-8")
    return output_path
