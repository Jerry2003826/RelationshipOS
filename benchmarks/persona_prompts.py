"""Helpers for benchmark persona prompt overrides."""

from __future__ import annotations

import os
from pathlib import Path


def load_benchmark_persona(default_prompt: str) -> str:
    prompt_file = os.getenv("BENCHMARK_PERSONA_PROMPT_FILE", "").strip()
    if prompt_file:
        path = Path(prompt_file)
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text

    prompt = os.getenv("BENCHMARK_PERSONA_PROMPT", "").strip()
    if prompt:
        return prompt

    return default_prompt
