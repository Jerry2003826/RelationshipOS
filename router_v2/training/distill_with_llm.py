"""Distill a bigger LLM's judgement into the Router v2 training set.

Takes unlabelled utterances and asks a strong model (DeepSeek-V3,
Qwen-Max, GPT-4.1, etc.) to classify each into FAST_PONG /
LIGHT_RECALL / DEEP_THINK. Output is a "silver" labelled set ready for
train_tier2.py.

Why this matters
----------------
The previous training set was 121 hand-curated rows. Manually scaling
to thousands is slow and biased. A strong LLM is expensive per call
but correct >90% of the time on single-turn classification of this
kind, and we only run it offline once per batch.

Calling convention
------------------
The script uses an OpenAI-compatible chat completions endpoint. It
reads:
    DISTILL_API_BASE    e.g. https://api.deepseek.com/v1
    DISTILL_API_KEY     your key
    DISTILL_MODEL       e.g. deepseek-chat

If DRY_RUN=1 is set, we skip the network call and instead emit a
deterministic heuristic label so the whole pipeline can be exercised
in CI / offline sandboxes.

Usage
-----
    python distill_with_llm.py \
        --input  router_v2/training/unlabelled_zh.jsonl \
        --output router_v2/training/silver_zh.jsonl \
        --concurrency 8
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


VALID_LABELS = {"FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"}


SYSTEM_PROMPT = """你是一位资深的对话系统路由标注员。

给定一句用户说的话, 请判断它应该走以下哪条 pipeline:

1. FAST_PONG
   纯闲聊、招呼、单字回应、笑声、短句表情等。
   AI 无需调用任何记忆和情感模块, 回一句话带过即可。
   例: 在吗 / 哈哈 / 嗯嗯 / 晚安 / 6 / 吃了吗

2. LIGHT_RECALL
   用户在平静地披露自己的近况、日常事件, 或明确要求 AI 回忆过往对话。
   AI 需要查一下浅层记忆 (最近几轮到几天), 但不需要深层情感推理。
   没有强烈情感, 没有危机信号, 没有身份探询。
   例: 今天挺累的 / 还记得我上次说的那件事吗 / 下班啦 / 周末去爬山了

3. DEEP_THINK
   任意一项成立即可:
   (a) 用户表达强烈情感 (崩溃/伤心/愤怒/焦虑/绝望/自杀念头)
   (b) 用户在探询 AI 的身份、感受、或两人关系
   (c) 用户抛出需要多步推理的任务 (翻译/代码/对比/推荐/复杂问答)
   (d) 用户披露重大人生事件 (分手/失业/家人生病/心理创伤)

只输出一个 JSON, 不要解释:
{"label": "FAST_PONG|LIGHT_RECALL|DEEP_THINK", "reason": "<=15 字"}"""


FEWSHOTS = [
    ("在吗", "FAST_PONG", "纯招呼"),
    ("哈哈哈哈哈", "FAST_PONG", "笑声"),
    ("嗯嗯", "FAST_PONG", "确认词"),
    ("下班啦", "LIGHT_RECALL", "日常事件"),
    ("今天挺累的", "LIGHT_RECALL", "平静披露"),
    ("还记得我上次跟你说的那件事吗", "LIGHT_RECALL", "明确回忆请求"),
    ("我今天崩溃了 真的撑不住", "DEEP_THINK", "强烈负面"),
    ("你是谁呀", "DEEP_THINK", "身份探询"),
    ("我想死", "DEEP_THINK", "自伤念头"),
    ("帮我写个 python 脚本", "DEEP_THINK", "多步任务"),
    ("男朋友劈腿了", "DEEP_THINK", "重大人生事件"),
]


def _build_user_prompt(text: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user, label, why in FEWSHOTS:
        messages.append({"role": "user", "content": user})
        messages.append({
            "role": "assistant",
            "content": json.dumps({"label": label, "reason": why}, ensure_ascii=False),
        })
    messages.append({"role": "user", "content": text})
    return messages


# --- heuristic dry-run labeller ------------------------------------------

def _dry_run_label(text: str) -> tuple[str, str]:
    """Deterministic fallback so the pipeline can be exercised offline.

    This is NOT meant to replace an actual LLM — it is a weak proxy that
    covers obvious cases so CI can smoke-test the full workflow.
    """
    t = text.strip().lower()
    crisis = any(w in t for w in ("想死", "不想活", "活不下去", "自杀", "想消失"))
    if crisis:
        return "DEEP_THINK", "dry:crisis"
    persona = any(w in t for w in ("你是谁", "你叫", "你是ai", "你是真人", "你把我当", "我对你来说", "我们算"))
    if persona:
        return "DEEP_THINK", "dry:persona"
    task = any(w in t for w in ("帮我", "翻译", "代码", "推荐", "对比", "为什么", "怎么做", "区别", "解释"))
    if task:
        return "DEEP_THINK", "dry:task"
    strong_emotion = any(w in t for w in (
        "崩溃", "撑不住", "绝望", "心累", "焦虑", "抑郁", "痛哭", "愤怒",
        "分手", "劈腿", "裁了", "去世", "走了",
    ))
    if strong_emotion:
        return "DEEP_THINK", "dry:emotion"
    recall = any(w in t for w in (
        "还记得", "记不记得", "你说过", "上次", "我跟你说过", "我告诉过你",
        "之前", "以前", "忘记",
    ))
    if recall:
        return "LIGHT_RECALL", "dry:recall"
    disclosure = any(w in t for w in (
        "今天", "昨天", "刚才", "最近", "这几天", "我的", "我妈", "我爸",
        "我朋友", "我男", "我女", "加班", "组会", "面试", "挂科", "周末",
    ))
    if disclosure and len(t) > 4:
        return "LIGHT_RECALL", "dry:disclosure"
    # Very short / interjection → pong.
    if len(t) <= 4:
        return "FAST_PONG", "dry:short"
    # Long-ish ambiguous → light recall default.
    return "LIGHT_RECALL", "dry:default"


# --- HTTP caller ---------------------------------------------------------

def _call_llm(text: str, *, api_base: str, api_key: str, model: str, timeout: float) -> dict:
    if requests is None:
        raise RuntimeError("pip install requests to use live API calls")
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 60,
        "response_format": {"type": "json_object"},
        "messages": _build_user_prompt(text),
    }
    r = requests.post(url, headers=headers, json=body, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    raw = data["choices"][0]["message"]["content"]
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"non-json response: {raw[:120]!r}")
    return json.loads(raw[start : end + 1])


# --- main ----------------------------------------------------------------

def _process_one(
    text: str, *, dry_run: bool, client_cfg: dict[str, Any]
) -> dict:
    if dry_run:
        label, reason = _dry_run_label(text)
        return {"text": text, "label": label, "reason": reason, "source": "dry_run"}
    try:
        out = _call_llm(text, **client_cfg)
    except Exception as exc:  # noqa: BLE001
        return {"text": text, "error": str(exc), "source": client_cfg.get("model", "?")}
    label = out.get("label")
    reason = str(out.get("reason", ""))[:40]
    if label not in VALID_LABELS:
        return {"text": text, "error": f"invalid label {label!r}", "source": client_cfg.get("model")}
    return {"text": text, "label": label, "reason": reason, "source": client_cfg.get("model")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()

    dry_run = os.environ.get("DRY_RUN", "0") == "1"
    api_base = os.environ.get("DISTILL_API_BASE", "https://api.deepseek.com/v1")
    api_key = os.environ.get("DISTILL_API_KEY", "")
    model = os.environ.get("DISTILL_MODEL", "deepseek-chat")

    if not dry_run and not api_key:
        print("ERROR: set DISTILL_API_KEY or run with DRY_RUN=1", file=sys.stderr)
        return 2

    client_cfg: dict[str, Any] = {
        "api_base": api_base,
        "api_key": api_key,
        "model": model,
        "timeout": args.timeout,
    }

    # Load (+ dedupe by text) unlabelled corpus.
    seen: set[str] = set()
    rows: list[str] = []
    with args.input.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            obj = json.loads(ln)
            t = obj["text"]
            if t in seen:
                continue
            seen.add(t)
            rows.append(t)

    print(f"Distilling {len(rows)} rows with "
          f"{'DRY_RUN heuristic' if dry_run else model} "
          f"(concurrency={args.concurrency})")

    results: list[dict] = []
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(_process_one, t, dry_run=dry_run, client_cfg=client_cfg): t for t in rows}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            rec = fut.result()
            results.append(rec)
            if i % 25 == 0:
                elapsed = time.time() - t0
                print(f"  {i}/{len(rows)} done ({elapsed:.1f}s, "
                      f"{i / max(elapsed, 0.01):.1f} req/s)")

    # Write silver set (skip errors).
    ok = [r for r in results if "label" in r]
    errs = [r for r in results if "error" in r]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for r in ok:
            f.write(json.dumps({"text": r["text"], "label": r["label"]}, ensure_ascii=False) + "\n")

    # Quick class distribution.
    dist: dict[str, int] = {}
    for r in ok:
        dist[r["label"]] = dist.get(r["label"], 0) + 1

    print("\n=== Distillation summary ===")
    print(f"  labelled:    {len(ok)}")
    print(f"  errors:      {len(errs)}")
    print("  distribution:")
    for k in ("FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"):
        pct = dist.get(k, 0) / max(len(ok), 1) * 100
        print(f"    {k:<14s} {dist.get(k, 0):>4d} ({pct:5.1f}%)")
    print(f"Saved → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
