"""Tests for the 128-dim EMA user profile vector."""

from __future__ import annotations

import numpy as np

from relationship_os.application.analyzers.user_profile import (
    DIM,
    UserProfileStore,
    cosine,
    featurize,
    format_profile_prefix,
)


def test_featurize_returns_unit_vector_of_correct_shape():
    vec = featurize("我今天心情不错，想找人聊天")
    assert vec.shape == (DIM,)
    assert 0.99 <= float(np.linalg.norm(vec)) <= 1.001


def test_featurize_handles_empty_and_whitespace():
    assert float(np.linalg.norm(featurize(""))) == 0.0
    assert float(np.linalg.norm(featurize("   \n\t"))) == 0.0


def test_featurize_is_deterministic():
    a = featurize("你还记得我上次说的那件事吗")
    b = featurize("你还记得我上次说的那件事吗")
    assert np.allclose(a, b)


def test_ema_converges_on_repeated_user_style():
    store = UserProfileStore()
    uid = "user-42"
    msgs = [
        "今天加班加到十点真的累",
        "老板又临时加需求烦死了",
        "周末必须躺平一整天",
        "累到不想说话",
        "这个 sprint 压力也太大",
    ]
    for _ in range(40):
        for m in msgs:
            store.update(uid, m)

    v1 = store.get(uid)
    assert v1 is not None
    # Final 10 updates should barely move the vector.
    before = v1.copy()
    for m in msgs[:10]:
        store.update(uid, m)
    after = store.get(uid)
    assert after is not None
    assert cosine(before, after) > 0.9


def test_different_users_produce_different_profiles():
    store = UserProfileStore()
    for _ in range(20):
        store.update("jerry", "在澳洲读 IT 想做 AI agent 后端")
        store.update("lin", "产品经理喜欢追剧和买手办")
    a = store.get("jerry")
    b = store.get("lin")
    assert a is not None and b is not None
    assert cosine(a, b) < 0.95  # clearly separated styles


def test_snapshot_roundtrip():
    store = UserProfileStore()
    store.update("u1", "hello there")
    store.update("u2", "另一个用户的语气完全不一样啊")
    snap = store.snapshot()
    new_store = UserProfileStore()
    new_store.load(snap)
    assert np.allclose(store.get("u1"), new_store.get("u1"))
    assert np.allclose(store.get("u2"), new_store.get("u2"))


def test_format_profile_prefix_is_one_line_and_compact():
    vec = featurize("随便一句话")
    s = format_profile_prefix(vec, top_k=8)
    assert s.startswith("profile_vec(128d):")
    assert "\n" not in s
    assert len(s) < 200


def test_turns_seen_counter():
    store = UserProfileStore()
    assert store.turns_seen("x") == 0
    store.update("x", "hi")
    store.update("x", "again")
    assert store.turns_seen("x") == 2
    assert store.turns_seen("y") == 0
