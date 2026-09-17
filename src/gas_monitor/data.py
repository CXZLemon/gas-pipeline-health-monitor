"""Data generation and validation helpers."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "timestamp",
    "component_id",
    "inlet_pressure",
    "outlet_pressure",
    "flow_rate",
    "temperature",
)


def generate_synthetic_data(
    n_hours: int = 24 * 14,
    component_ids: Iterable[str] = ("PIPE-001", "PIPE-002", "PIPE-003"),
    anomaly_ratio: float = 0.03,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate reproducible hourly gas-pipeline telemetry.

    The generated labels are only for learning and offline evaluation. They are
    not used when fitting the unsupervised detector.
    """
    if n_hours < 24:
        raise ValueError("n_hours must be at least 24")
    if not 0 < anomaly_ratio < 0.2:
        raise ValueError("anomaly_ratio must be between 0 and 0.2")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2026-01-01", periods=n_hours, freq="h")
    frames: list[pd.DataFrame] = []

    for component_index, component_id in enumerate(component_ids):
        hour = np.arange(n_hours)
        daily_phase = 2 * np.pi * (hour % 24) / 24
        weekly_phase = 2 * np.pi * hour / (24 * 7)

        base_flow = 72 + 8 * component_index
        flow_rate = (
            base_flow
            + 9 * np.sin(daily_phase - 0.8)
            + 3 * np.sin(weekly_phase)
            + rng.normal(0, 1.8, n_hours)
        )
        inlet_pressure = (
            6.2
            + 0.12 * component_index
            + 0.08 * np.sin(daily_phase + 0.4)
            + rng.normal(0, 0.025, n_hours)
        )
        temperature = (
            18
            + 5 * np.sin(daily_phase - 1.1)
            + 0.5 * component_index
            + rng.normal(0, 0.7, n_hours)
        )
        pressure_drop = 0.22 + 0.006 * flow_rate + rng.normal(0, 0.018, n_hours)
        outlet_pressure = inlet_pressure - pressure_drop

        frame = pd.DataFrame(
            {
                "timestamp": timestamps,
                "component_id": component_id,
                "inlet_pressure": inlet_pressure,
                "outlet_pressure": outlet_pressure,
                "flow_rate": flow_rate,
                "temperature": temperature,
                "is_injected_anomaly": 0,
                "anomaly_type": "normal",
            }
        )

        anomaly_count = max(1, int(n_hours * anomaly_ratio))
        anomaly_indices = rng.choice(
            np.arange(12, n_hours - 1), size=anomaly_count, replace=False
        )
        anomaly_types = rng.choice(
            ["leakage", "blockage", "sensor_drift"],
            size=anomaly_count,
            replace=True,
        )

        for row_index, anomaly_type in zip(anomaly_indices, anomaly_types):
            frame.loc[row_index, "is_injected_anomaly"] = 1
            frame.loc[row_index, "anomaly_type"] = anomaly_type
            if anomaly_type == "leakage":
                frame.loc[row_index, "outlet_pressure"] -= rng.uniform(0.55, 0.9)
                frame.loc[row_index, "flow_rate"] += rng.uniform(10, 18)
            elif anomaly_type == "blockage":
                frame.loc[row_index, "outlet_pressure"] -= rng.uniform(0.3, 0.6)
                frame.loc[row_index, "flow_rate"] -= rng.uniform(18, 28)
            else:
                frame.loc[row_index, "inlet_pressure"] += rng.uniform(0.7, 1.1)
                frame.loc[row_index, "temperature"] += rng.uniform(9, 15)

        frames.append(frame)

    result = pd.concat(frames, ignore_index=True)
    result["flow_rate"] = result["flow_rate"].clip(lower=1.0)
    result["outlet_pressure"] = result["outlet_pressure"].clip(lower=0.1)
    return result.sort_values(["component_id", "timestamp"]).reset_index(drop=True)


def validate_telemetry(data: pd.DataFrame) -> pd.DataFrame:
    """Validate user data and return a cleaned copy."""
    missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    cleaned = data.copy()
    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
    numeric_columns = [
        "inlet_pressure",
        "outlet_pressure",
        "flow_rate",
        "temperature",
    ]
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["component_id"] = cleaned["component_id"].astype(str).str.strip()
    cleaned = cleaned.dropna(subset=["timestamp", "component_id", *numeric_columns])
    cleaned = cleaned[cleaned["component_id"] != ""]
    if cleaned.empty:
        raise ValueError("No valid telemetry rows remain after cleaning")
    if (cleaned[["inlet_pressure", "outlet_pressure", "flow_rate"]] <= 0).any().any():
        raise ValueError("Pressure and flow values must be positive")

    return cleaned.sort_values(["component_id", "timestamp"]).reset_index(drop=True)

