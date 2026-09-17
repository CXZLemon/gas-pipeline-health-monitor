import numpy as np

from gas_monitor.data import generate_synthetic_data
from gas_monitor.features import MODEL_FEATURES, build_features


def test_features_are_complete_and_finite():
    data = generate_synthetic_data(n_hours=72, component_ids=("P1", "P2"))
    featured = build_features(data, rolling_window=6)

    assert set(MODEL_FEATURES).issubset(featured.columns)
    assert np.isfinite(featured[MODEL_FEATURES].to_numpy()).all()
    assert (featured["pressure_drop"] == featured["inlet_pressure"] - featured["outlet_pressure"]).all()

