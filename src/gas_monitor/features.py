"""Feature engineering for pipeline telemetry."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import validate_telemetry


MODEL_FEATURES = [
    "inlet_pressure",
    "outlet_pressure",
    "flow_rate",
    "temperature",
    "pressure_drop",
    "pressure_drop_ratio",
    "flow_change",
    "pressure_drop_rolling_mean",
    "pressure_drop_rolling_std",
    "hour_sin",
    "hour_cos",
]


def build_features(data: pd.DataFrame, rolling_window: int = 12) -> pd.DataFrame:
    """Clean telemetry and add domain-inspired time-series features."""
    if rolling_window < 2:
        raise ValueError("rolling_window must be at least 2")

    featured = validate_telemetry(data)
    featured["pressure_drop"] = (
        featured["inlet_pressure"] - featured["outlet_pressure"]
    )
    featured["pressure_drop_ratio"] = featured["pressure_drop"] / featured[
        "inlet_pressure"
    ].clip(lower=1e-6)

    grouped = featured.groupby("component_id", sort=False)
    featured["flow_change"] = grouped["flow_rate"].diff().abs().fillna(0.0)
    featured["pressure_drop_rolling_mean"] = grouped["pressure_drop"].transform(
        lambda values: values.rolling(rolling_window, min_periods=2).mean()
    )
    featured["pressure_drop_rolling_std"] = grouped["pressure_drop"].transform(
        lambda values: values.rolling(rolling_window, min_periods=2).std()
    )

    hour = featured["timestamp"].dt.hour + featured["timestamp"].dt.minute / 60
    featured["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    featured["hour_cos"] = np.cos(2 * np.pi * hour / 24)

    for column in MODEL_FEATURES:
        if featured[column].isna().any():
            featured[column] = featured[column].fillna(featured[column].median())

    return featured

