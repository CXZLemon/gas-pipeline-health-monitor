"""Run the complete data-to-database demo without the web UI."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gas_monitor.data import generate_synthetic_data  # noqa: E402
from gas_monitor.detector import detect_anomalies  # noqa: E402
from gas_monitor.storage import TelemetryRepository, create_database_engine  # noqa: E402


def main() -> None:
    raw_data = generate_synthetic_data()
    scored, _, metrics = detect_anomalies(raw_data)

    outputs = PROJECT_ROOT / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    result_path = outputs / "pipeline_anomaly_results.csv"
    scored.to_csv(result_path, index=False, encoding="utf-8-sig")

    engine = create_database_engine()
    repository = TelemetryRepository(engine)
    repository.save(raw_data)

    print(f"Processed rows: {len(scored)}")
    print(f"Detected anomalies: {int(scored['is_anomaly'].sum())}")
    if metrics is not None:
        print(
            "Offline metrics: "
            f"precision={metrics.precision:.3f}, "
            f"recall={metrics.recall:.3f}, f1={metrics.f1:.3f}"
        )
    print(f"Database rows: {repository.count()}")
    print(f"Result file: {result_path}")


if __name__ == "__main__":
    main()

