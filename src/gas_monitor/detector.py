"""Unsupervised anomaly detection model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import MODEL_FEATURES, build_features


@dataclass(frozen=True)
class DetectionMetrics:
    precision: float
    recall: float
    f1: float

    def as_dict(self) -> dict[str, float]:
        return {"precision": self.precision, "recall": self.recall, "f1": self.f1}


def _risk_score(raw_scores: np.ndarray) -> np.ndarray:
    minimum = float(raw_scores.min())
    maximum = float(raw_scores.max())
    if np.isclose(minimum, maximum):
        return np.zeros_like(raw_scores)
    return 100 * (raw_scores - minimum) / (maximum - minimum)


def detect_anomalies(
    data: pd.DataFrame,
    contamination: float = 0.03,
    rolling_window: int = 12,
    random_state: int = 42,
) -> tuple[pd.DataFrame, Pipeline, DetectionMetrics | None]:
    """Fit Isolation Forest and return scored rows, model, and optional metrics."""
    if not 0 < contamination <= 0.2:
        raise ValueError("contamination must be in (0, 0.2]")

    featured = build_features(data, rolling_window=rolling_window)
    matrix = featured[MODEL_FEATURES]
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "detector",
                IsolationForest(
                    n_estimators=250,
                    contamination=contamination,
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    predictions = model.fit_predict(matrix)
    decision = model.decision_function(matrix)

    scored = featured.copy()
    scored["is_anomaly"] = (predictions == -1).astype(int)
    scored["anomaly_score"] = -decision
    scored["risk_score"] = _risk_score(scored["anomaly_score"].to_numpy())

    metrics = None
    if "is_injected_anomaly" in scored.columns:
        truth = scored["is_injected_anomaly"].astype(int)
        predicted = scored["is_anomaly"]
        metrics = DetectionMetrics(
            precision=float(precision_score(truth, predicted, zero_division=0)),
            recall=float(recall_score(truth, predicted, zero_division=0)),
            f1=float(f1_score(truth, predicted, zero_division=0)),
        )

    return scored, model, metrics

