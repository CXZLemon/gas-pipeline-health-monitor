from sqlalchemy import create_engine

from gas_monitor.data import generate_synthetic_data
from gas_monitor.storage import TelemetryRepository


def test_repository_round_trip(tmp_path):
    database_path = tmp_path / "telemetry.db"
    engine = create_engine(f"sqlite:///{database_path}", future=True)
    repository = TelemetryRepository(engine)
    data = generate_synthetic_data(n_hours=48, component_ids=("P1", "P2"))

    saved = repository.save(data)
    loaded = repository.load(component_id="P1")

    assert saved == len(data)
    assert repository.count() == len(data)
    assert len(loaded) == 48
    assert set(loaded["component_id"]) == {"P1"}

