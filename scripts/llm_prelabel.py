#!/usr/bin/env python3
"""LLM-assisted silver-label generator for router shadow logs.

Usage::

    python scripts/llm_prelabel.py \
        --input router_v2/training/data/shadow.jsonl \
        --output router_v2/training/data/silver_labels.jsonl \
        --model deepseek-chat

Reads a JSONL shadow log (emitted by JsonlShadowLogger), asks the LLM to
pick one of FAST_PONG / LIGHT_RECALL / DEEP_THINK per turn, and writes a
new JSONL where each line carries ``text``, ``label``, ``confidence``,
``source=llm_prelabel``. Confidence <0.7 rows will be surfaced by
``review_labels.py`` for human review.

The LLM client is provided via a small pluggable callable so this file
stays testable without a real network call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

LabelFn = Callable[[str], dict]

_PROMPT_TEMPLATE = """你是一个对话路由标注员。根据下面这条中文用户消息，判断它应该走哪条路径：

FAST_PONG    —— 简单招呼、语气词、共情确认，不需要任何记忆或推理
LIGHT_RECALL —— 需要近期记忆/用户画像/情感接住，但不需要深度规划
DEEP_THINK   —— 事实追问、人格盘问、危机语气、复杂情感或策略问题

只输出一个 JSON，字段：
  label       —— 上面三选一
  confidence  —— 0.0 ~ 1.0
  reason      —— 不超过 20 字的中文说明

消息：{text}
"""


@dataclass
class PrelabelRecord:
    text: str
    label: str
    confidence: float
    reason: str
    turn_id: str | None = None

    def to_jsonl(self) -> str:
        return json.dumps(
            {
                "text": self.text,
                "label": self.label,
                "confidence": self.confidence,
                "reason": self.reason,
                "turn_id": self.turn_id,
                "source": "llm_prelabel",
            },
            ensure_ascii=False,
        )


VALID_LABELS = {"FAST_PONG", "LIGHT_RECALL", "DEEP_THINK"}


def prelabel_record(
    text: str,
    *,
    turn_id: str | None,
    label_fn: LabelFn,
) -> PrelabelRecord | None:
    try:
        raw = label_fn(text)
    except Exception as exc:  # noqa: BLE001
        print(f"prelabel failed for {turn_id}: {exc}", file=sys.stderr)
        return None
    label = str(raw.get("label", "")).strip().upper()
    if label not in VALID_LABELS:
        return None
    try:
        conf = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    reason = str(raw.get("reason", ""))[:60]
    return PrelabelRecord(
        text=text, label=label, confidence=conf, reason=reason, turn_id=turn_id
    )


def run(
    input_path: Path,
    output_path: Path,
    *,
    label_fn: LabelFn,
    min_text_len: int = 1,
) -> int:
    seen_texts: set[str] = set()
    count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as fin, output_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("kind") == "label":
                continue  # Already labelled by an earlier tool.
            text = str(rec.get("text") or "").strip()
            if len(text) < min_text_len or text in seen_texts:
                continue
            seen_texts.add(text)
            out = prelabel_record(
                text,
                turn_id=rec.get("turn_id"),
                label_fn=label_fn,
            )
            if out is None:
                continue
            fout.write(out.to_jsonl() + "\n")
            count += 1
    return count


# ------------------------------------------------------------------ CLI


def _default_label_fn(model: str) -> LabelFn:
    """Return a label_fn that calls DeepSeek / OpenAI-compatible API.

    Skips network entirely and raises if keys are missing. Callers can
    mock this in tests.
    """
    # Imported lazily so unit tests do not need the litellm stack.
    import litellm  # type: ignore[import-not-found]

    def call(text: str) -> dict:
        resp = litellm.completion(  # type: ignore[no-untyped-call]
            model=model,
            messages=[
                {"role": "system", "content": "只输出 JSON。"},
                {
                    "role": "user",
                    "content": _PROMPT_TEMPLATE.format(text=text),
                },
            ],
            temperature=0.0,
            max_tokens=120,
            response_format={"type": "json_object"},
        )
        content = resp["choices"][0]["message"]["content"]
        return json.loads(content)

    return call


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--model",
        default=os.environ.get("ROUTER_PRELABEL_MODEL", "deepseek-chat"),
    )
    p.add_argument("--min-text-len", type=int, default=2)
    args = p.parse_args(argv)

    label_fn = _default_label_fn(args.model)
    n = run(
        args.input,
        args.output,
        label_fn=label_fn,
        min_text_len=args.min_text_len,
    )
    print(f"wrote {n} silver labels -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
