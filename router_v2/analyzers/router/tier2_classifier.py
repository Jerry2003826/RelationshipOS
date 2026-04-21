"""Tier 2 calibrated classifier loader.

The training script writes:
    model.joblib  -- dict with:
        'coef':        (n_classes, n_features) numpy array
        'intercept':   (n_classes,) numpy array
        'classes':     list[str] matching ALL_ROUTES ordering
        'feat_names':  list[str]
        'calibrator':  list of per-class IsotonicRegression or None
        'version':     str
        'metrics':     dict
        'trained_at':  iso timestamp

At inference we need only numpy — joblib is optional; fall back to
pickle so the router stays deployable in trimmed containers.
"""

from __future__ import annotations

import logging
import math
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import ALL_ROUTES
from .features import RouterFeatures

logger = logging.getLogger(__name__)

try:
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    np = None  # type: ignore


def _softmax(x: list[float]) -> list[float]:
    m = max(x)
    exps = [math.exp(v - m) for v in x]
    s = sum(exps)
    return [e / s for e in exps]


@dataclass(slots=True)
class Tier2Classifier:
    """Thin wrapper that exposes `predict_proba` + `top_features`."""

    coef: Any  # numpy array or list[list[float]]
    intercept: Any  # numpy array or list[float]
    classes: list[str]
    feat_names: list[str]
    calibrators: list[Any] | None  # per-class isotonic OR None
    version: str = "0.0.0"

    @classmethod
    def load(cls, path: Path) -> Tier2Classifier:
        with path.open("rb") as f:
            blob = pickle.load(f)
        return cls(
            coef=blob["coef"],
            intercept=blob["intercept"],
            classes=list(blob["classes"]),
            feat_names=list(blob["feat_names"]),
            calibrators=blob.get("calibrator"),
            version=str(blob.get("version", "0.0.0")),
        )

    # --- inference -------------------------------------------------------

    def predict_proba(self, features: RouterFeatures) -> dict[str, float]:
        x = features.as_vector()
        # Compute logits = W @ x + b
        logits = []
        for k in range(len(self.classes)):
            row = self.coef[k] if np is None else self.coef[k]
            z = float(self.intercept[k])
            for j, xj in enumerate(x):
                z += float(row[j]) * xj
            logits.append(z)
        probs = _softmax(logits)

        # Per-class isotonic calibration, then renormalize.
        if self.calibrators is not None:
            cal = []
            for k, raw_p in enumerate(probs):
                c = self.calibrators[k] if k < len(self.calibrators) else None
                if c is None:
                    cal.append(raw_p)
                else:
                    cal.append(float(c.predict([raw_p])[0]))
            total = sum(cal) or 1.0
            probs = [v / total for v in cal]

        return {self.classes[k]: float(probs[k]) for k in range(len(self.classes))}

    def top_features(self, features: RouterFeatures, k: int = 5) -> dict[str, float]:
        """Return top-k signed feature contributions for the *argmax* class."""
        probs = self.predict_proba(features)
        arg = max(probs, key=probs.get)
        cls_idx = self.classes.index(arg)
        row = self.coef[cls_idx]
        contribs = []
        x = features.as_vector()
        for j, name in enumerate(self.feat_names):
            contribs.append((name, float(row[j]) * float(x[j])))
        contribs.sort(key=lambda t: -abs(t[1]))
        return {name: val for name, val in contribs[:k]}


# --- graceful fallback ----------------------------------------------------


@dataclass(slots=True)
class PriorClassifier:
    """Used when no trained model is available.

    Produces a probability distribution from the rule-engine soft prior
    (or a broad uniform) so the cascade still has something to consume.
    """

    def predict_proba(self, features: RouterFeatures) -> dict[str, float]:
        # Simple heuristic: weigh persona/memory/emotion features.
        scores = {
            "FAST_PONG": 0.3
            + 0.5 * features.is_very_short
            - 0.4 * features.memory_trigger_score
            - 0.4 * features.persona_probe_score
            - 0.4 * features.emotion_raw,
            "LIGHT_RECALL": 0.3
            + 0.5 * features.memory_trigger_score
            + 0.3 * features.self_disclosure_score
            - 0.4 * features.persona_probe_score,
            "DEEP_THINK": 0.3
            + 0.5 * features.emotion_raw
            + 0.4 * features.persona_probe_score
            + 0.3 * features.factual_query_score
            + 0.3 * features.contains_crisis_term,
        }
        # Clip and softmax.
        vals = [max(scores[k], -2.0) for k in ALL_ROUTES]
        probs = _softmax(vals)
        return {k: float(probs[i]) for i, k in enumerate(ALL_ROUTES)}

    def top_features(self, features: RouterFeatures, k: int = 5) -> dict[str, float]:
        # Static explanation.
        ranked = [
            ("memory_trigger", features.memory_trigger_score),
            ("persona_probe", features.persona_probe_score),
            ("emotion_raw", features.emotion_raw),
            ("self_disclosure", features.self_disclosure_score),
            ("factual_query", features.factual_query_score),
        ]
        ranked.sort(key=lambda t: -t[1])
        return {n: v for n, v in ranked[:k] if v > 0}


def load_or_fallback(model_path: Path) -> Tier2Classifier | PriorClassifier:
    if model_path.exists():
        try:
            return Tier2Classifier.load(model_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to load tier2 model %s: %s", model_path, exc)
    return PriorClassifier()
