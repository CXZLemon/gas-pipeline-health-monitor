import pandas as pd
import pytest

from gas_monitor.data import REQUIRED_COLUMNS, generate_synthetic_data, validate_telemetry


def test_synthetic_data_is_reproducible_and_labeled():
    first = generate_synthetic_data(n_hours=48, component_ids=("P1",), seed=7)
    second = generate_synthetic_data(n_hours=48, component_ids=("P1",), seed=7)

    pd.testing.assert_frame_equal(first, second)
    assert set(REQUIRED_COLUMNS).issubset(first.columns)
    assert first["is_injected_anomaly"].sum() >= 1


def test_validation_rejects_missing_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_telemetry(pd.DataFrame({"timestamp": ["2026-01-01"]}))

