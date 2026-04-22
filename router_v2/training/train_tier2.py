"""Train Tier 2 calibrated classifier.

Inputs:
    --data JSONL file with {"text": str, "label": one of ALL_ROUTES}
    --out  path to write model.joblib

Pipeline:
    1. Extract RouterFeatures for every row.
    2. Stratified 80/20 split.
    3. LogisticRegression (multinomial, liblinear → lbfgs) with L2.
    4. Per-class IsotonicRegression calibration on the val split
       (one-vs-rest, Platt-then-isotonic style).
    5. Persist as pickle dict (not joblib) to keep the inference side
       dependency-free. File name stays `.joblib` for continuity.

Evaluation:
    Prints macro-F1, per-class precision/recall, Expected Calibration
    Error (15-bin), and a rule-short-circuit coverage estimate.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from collections.abc import Iterable
from pathlib import Path

# Make router_v2 importable when run as a script.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import classification_report, f1_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from router_v2.analyzers.router.contracts import ALL_ROUTES  # noqa: E402
from router_v2.analyzers.router.features import (  # noqa: E402
    RouterFeatures,
    extract_features,
    load_lexicons,
)


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            rows.append(json.loads(ln))
    return rows


def _vectorize(rows: Iterable[dict], lex) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for r in rows:
        feat = extract_features(r["text"], lex)
        X.append(feat.as_vector())
        y.append(r["label"])
    return np.asarray(X, dtype=np.float32), np.asarray(y)


def _expected_calibration_error(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    """ECE over max-prob predictions."""
    confs = probs.max(axis=1)
    preds = probs.argmax(axis=1)
    correct = (preds == labels).astype(np.float32)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(confs)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (confs > lo) & (confs <= hi)
        if mask.sum() == 0:
            continue
        acc = correct[mask].mean()
        conf = confs[mask].mean()
        ece += mask.sum() / n * abs(acc - conf)
    return float(ece)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--C", type=float, default=1.0, help="LogReg inverse-reg strength")
    args = ap.parse_args()

    lex = load_lexicons()
    rows = _load_jsonl(args.data)
    if len(rows) < 30:
        print(f"WARN: only {len(rows)} rows; training will generalize poorly", file=sys.stderr)

    X, y = _vectorize(rows, lex)
    classes = list(ALL_ROUTES)

    # Stratified split when possible.
    try:
        X_tr, X_va, y_tr, y_va = train_test_split(
            X, y, test_size=0.2, random_state=args.seed, stratify=y
        )
    except ValueError:
        X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, random_state=args.seed)

    clf = LogisticRegression(
        C=args.C,
        solver="lbfgs",
        max_iter=2000,
        random_state=args.seed,
        class_weight="balanced",  # compensate for class imbalance in silver labels
    )
    clf.fit(X_tr, y_tr)

    # Align class order with ALL_ROUTES.
    # If some class is missing from the training data, pad with a near-zero row.
    n_feat = X.shape[1]
    coef = np.zeros((len(classes), n_feat), dtype=np.float32)
    intercept = np.zeros(len(classes), dtype=np.float32)
    for k, c in enumerate(classes):
        if c in clf.classes_:
            idx = list(clf.classes_).index(c)
            coef[k] = clf.coef_[idx]
            intercept[k] = clf.intercept_[idx]
        else:
            # Bias strongly negative so missing class is never argmax.
            intercept[k] = -5.0

    # Per-class isotonic calibration using val split.
    probs_va_raw = clf.predict_proba(X_va)
    # Reorder columns to ALL_ROUTES.
    reordered = np.zeros_like(probs_va_raw)
    for k, c in enumerate(classes):
        if c in clf.classes_:
            reordered[:, k] = probs_va_raw[:, list(clf.classes_).index(c)]
    calibrators: list[IsotonicRegression | None] = []
    for k, c in enumerate(classes):
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        y_bin = (y_va == c).astype(np.float32)
        if y_bin.sum() < 3 or y_bin.sum() == len(y_bin):
            calibrators.append(None)
            continue
        iso.fit(reordered[:, k], y_bin)
        calibrators.append(iso)

    # Metrics.
    y_pred = clf.predict(X_va)
    macro_f1 = f1_score(y_va, y_pred, average="macro", labels=classes)
    report = classification_report(y_va, y_pred, labels=classes, digits=3)

    # Post-calibration ECE.
    cal_probs = np.copy(reordered)
    for k in range(len(classes)):
        if calibrators[k] is not None:
            cal_probs[:, k] = calibrators[k].predict(cal_probs[:, k])
    # Renormalize.
    row_sum = cal_probs.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    cal_probs = cal_probs / row_sum
    label_idx = np.asarray([classes.index(lbl) for lbl in y_va])
    ece = _expected_calibration_error(cal_probs, label_idx)

    metrics = {
        "macro_f1": float(macro_f1),
        "ece": ece,
        "n_train": int(len(X_tr)),
        "n_val": int(len(X_va)),
        "classes": classes,
    }

    print("=== Tier 2 training report ===")
    print(report)
    print(f"Macro F1 (val):          {macro_f1:.4f}")
    print(f"Expected Calib Error:    {ece:.4f}")
    print(f"Train/Val size:          {len(X_tr)}/{len(X_va)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    blob = {
        "coef": coef,
        "intercept": intercept,
        "classes": classes,
        "feat_names": RouterFeatures.feature_names(),
        "calibrator": calibrators,
        "version": time.strftime("%Y.%m.%d.%H%M"),
        "metrics": metrics,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with args.out.open("wb") as f:
        pickle.dump(blob, f)
    print(f"Saved model → {args.out} ({args.out.stat().st_size / 1024:.1f} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
