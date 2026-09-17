from gas_monitor.data import generate_synthetic_data
from gas_monitor.detector import detect_anomalies


def test_detector_returns_scores_and_metrics():
    data = generate_synthetic_data(n_hours=120, component_ids=("P1", "P2"), seed=11)
    scored, model, metrics = detect_anomalies(data, contamination=0.04)

    assert len(scored) == len(data)
    assert {"is_anomaly", "anomaly_score", "risk_score"}.issubset(scored.columns)
    assert 0 <= scored["risk_score"].min() <= scored["risk_score"].max() <= 100
    assert scored["is_anomaly"].sum() > 0
    assert metrics is not None
    assert 0 <= metrics.f1 <= 1
    assert hasattr(model, "predict")

