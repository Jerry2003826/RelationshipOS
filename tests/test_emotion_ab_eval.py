"""Tests for scripts/emotion_ab_eval.py — no network."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "emotion_ab_eval",
    Path(__file__).resolve().parents[1] / "scripts" / "emotion_ab_eval.py",
)
assert _SPEC and _SPEC.loader
abm = importlib.util.module_from_spec(_SPEC)
sys.modules["emotion_ab_eval"] = abm
_SPEC.loader.exec_module(abm)


# ----------------------------------------------------------- rubrics


def test_lexical_rubric_counts_hits() -> None:
    assert abm.lexical_rubric("我很累想休息", targets=["累", "休息"]) == 1.0
    assert abm.lexical_rubric("我很累", targets=["累", "休息"]) == 0.5
    assert abm.lexical_rubric("随便说点什么", targets=["累"]) == 0.0


def test_lexical_rubric_empty_targets() -> None:
    assert abm.lexical_rubric("xxx", targets=[]) == 0.0


def test_length_rubric_peak_at_target() -> None:
    s_peak = abm.length_rubric("x" * 60, target_len=60)
    s_short = abm.length_rubric("x", target_len=60)
    s_long = abm.length_rubric("x" * 300, target_len=60)
    assert s_peak > 0.99
    assert s_short < s_peak
    assert s_long < s_peak


def test_length_rubric_empty() -> None:
    assert abm.length_rubric("", target_len=60) == 0.0


def test_empathy_rubric_hit_miss() -> None:
    assert abm.empathy_rubric("辛苦了,我懂你") == 1.0
    assert abm.empathy_rubric("直接讲事实就行") == 0.0


def test_score_reply_combines_rubrics() -> None:
    # reply contains both target keyword and empathy cue, length near 60
    reply = "辛苦了,我知道你最近很累,我陪着你慢慢走,不急,你随时跟我说。"
    score = abm.score_reply(reply, targets=["累"], target_len=len(reply))
    assert 0.9 <= score <= 1.0


def test_score_reply_clamps_to_unit() -> None:
    reply = "我很累,辛苦了,我懂你,累累累累累"
    # extreme weights > 1 — still clamped
    score = abm.score_reply(
        reply, targets=["累"], weights=(10.0, 10.0, 10.0)
    )
    assert score == 1.0


# ----------------------------------------------------------- harness


def _make_gen(replies_by_mode: dict[str, str]):
    """Returns a fake generator that picks a reply based on whether
    the prompt has 用户画像 section (B) or not (A)."""

    def gen(prompt, text):
        mode = "b" if "用户画像" in prompt.text else "a"
        return replies_by_mode[mode]

    return gen


def test_run_ab_scores_both_variants() -> None:
    turns = [
        {
            "turn_id": "t1",
            "text": "我今天很累",
            "route": "LIGHT_RECALL",
            "emotion_tags": ["tired"],
            "targets": ["累"],
        }
    ]
    gen = _make_gen(
        {
            "a": "嗯知道了。",
            "b": "辛苦了,我知道你今天很累,陪着你慢慢来。",
        }
    )
    report = abm.run_ab(
        turns,
        prompt_a_kwargs={"persona": "p", "include_profile_vec": False},
        prompt_b_kwargs={
            "persona": "p",
            "include_profile_vec": True,
            "user_profile_prefix": "profile:[0.1]",
        },
        generator_fn=gen,
    )
    assert len(report.turns) == 1
    r = report.turns[0]
    assert r.score_b > r.score_a
    assert r.delta > 0
    assert report.catch_rate_delta > 0


def test_run_ab_skips_empty_text() -> None:
    turns = [{"text": "", "route": "LIGHT_RECALL"}, {"text": "   "}]
    gen = _make_gen({"a": "", "b": ""})
    report = abm.run_ab(
        turns,
        prompt_a_kwargs={"persona": "p"},
        prompt_b_kwargs={"persona": "p"},
        generator_fn=gen,
    )
    assert report.turns == []


def test_report_win_count_and_summary() -> None:
    gen = _make_gen({"a": "短", "b": "辛苦了陪着你"})
    turns = [
        {"turn_id": f"t{i}", "text": "累", "emotion_tags": [], "targets": ["累"]}
        for i in range(3)
    ]
    report = abm.run_ab(
        turns,
        prompt_a_kwargs={"persona": "p", "include_profile_vec": False},
        prompt_b_kwargs={
            "persona": "p",
            "include_profile_vec": True,
            "user_profile_prefix": "x",
        },
        generator_fn=gen,
    )
    a_wins, b_wins, ties = report.win_count()
    assert b_wins == 3
    assert a_wins == 0
    summary = report.to_summary()
    assert summary["turns"] == 3
    assert summary["b_wins"] == 3
    assert summary["catch_rate_delta"] > 0


def test_render_markdown_has_all_fields() -> None:
    gen = _make_gen({"a": "短", "b": "辛苦了,陪着你"})
    turns = [
        {"turn_id": "t1", "text": "累", "targets": ["累"]},
        {"turn_id": "t2", "text": "难过", "targets": ["难过"]},
    ]
    report = abm.run_ab(
        turns,
        prompt_a_kwargs={"persona": "p", "include_profile_vec": False},
        prompt_b_kwargs={
            "persona": "p",
            "include_profile_vec": True,
            "user_profile_prefix": "x",
        },
        generator_fn=gen,
    )
    md = abm.render_markdown(
        report, label_a="baseline", label_b="with_profile", gate=0.05
    )
    assert "EmotionalExpert A/B 评测" in md
    assert "baseline" in md
    assert "with_profile" in md
    assert "catch_rate_delta" in md
    assert "Top 差异" in md
    assert "t1" in md


def test_render_markdown_gate_badge() -> None:
    report = abm.ABReport()
    # mean_b - mean_a = 0 — below gate
    md_low = abm.render_markdown(report, label_a="a", label_b="b", gate=0.10)
    assert "⚠️" in md_low

    # Inject a winning turn
    report.turns.append(
        abm.TurnResult(
            turn_id="t",
            text="x",
            route="LIGHT_RECALL",
            reply_a="",
            reply_b="",
            score_a=0.1,
            score_b=0.5,
            delta=0.4,
        )
    )
    md_hi = abm.render_markdown(report, label_a="a", label_b="b", gate=0.10)
    assert "✅" in md_hi


def test_parse_kwargs_handles_types() -> None:
    out = abm._parse_kwargs("include_profile_vec=true,max_memory_cards=2,note=hi")
    assert out == {
        "include_profile_vec": True,
        "max_memory_cards": 2,
        "note": "hi",
    }


def test_main_end_to_end_with_stub_generator(tmp_path: Path, monkeypatch) -> None:
    turns_path = tmp_path / "turns.jsonl"
    rows = [
        {"turn_id": "t1", "text": "我很累", "targets": ["累"]},
        {"turn_id": "t2", "text": "今天难过", "targets": ["难过"]},
    ]
    with turns_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def fake_gen_factory(model: str):
        def gen(prompt, text):
            if "用户画像" in prompt.text:
                return f"辛苦了, 陪着你, 关于 {text} 我懂你。"
            return "嗯。"

        return gen

    monkeypatch.setattr(abm, "_default_generator_fn", fake_gen_factory)

    md_path = tmp_path / "report.md"
    json_path = tmp_path / "summary.json"
    rc = abm.main(
        [
            "--turns",
            str(turns_path),
            "--persona",
            "你是贴心的数字人格",
            "--a-kwargs",
            "include_profile_vec=false",
            "--b-kwargs",
            "include_profile_vec=true,user_profile_prefix=profile:[0.1]",
            "--output-md",
            str(md_path),
            "--output-json",
            str(json_path),
            "--gate",
            "0.1",
        ]
    )
    assert rc == 0
    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["turns"] == 2
    assert summary["catch_rate_delta"] > 0.1
    assert md_path.exists()
    assert "EmotionalExpert A/B" in md_path.read_text(encoding="utf-8")


def test_main_exits_nonzero_below_gate(
    tmp_path: Path, monkeypatch
) -> None:
    turns_path = tmp_path / "turns.jsonl"
    turns_path.write_text(
        json.dumps({"text": "累", "targets": ["累"]}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    def fake_gen_factory(model: str):
        def gen(prompt, text):
            return "嗯。"  # identical for A and B → delta = 0

        return gen

    monkeypatch.setattr(abm, "_default_generator_fn", fake_gen_factory)
    rc = abm.main(
        [
            "--turns",
            str(turns_path),
            "--persona",
            "p",
            "--gate",
            "0.1",
        ]
    )
    assert rc == 2
