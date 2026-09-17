"""Small SQLAlchemy repository for SQLite or MySQL."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, create_engine, text


DEFAULT_DATABASE_URL = "sqlite:///data/pipeline_monitor.db"


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create an engine; create the local SQLite directory when needed."""
    url = database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if url.startswith("sqlite:///"):
        database_path = Path(url.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, future=True)


class TelemetryRepository:
    """Persist and query telemetry using parameterized SQL."""

    TABLE_NAME = "pipeline_telemetry"

    def __init__(self, engine: Engine):
        self.engine = engine

    def save(self, data: pd.DataFrame, if_exists: str = "replace") -> int:
        if if_exists not in {"replace", "append", "fail"}:
            raise ValueError("if_exists must be replace, append, or fail")
        data.to_sql(
            self.TABLE_NAME,
            self.engine,
            if_exists=if_exists,
            index=False,
            chunksize=1000,
        )
        return len(data)

    def load(self, component_id: str | None = None) -> pd.DataFrame:
        query = f"SELECT * FROM {self.TABLE_NAME}"
        params: dict[str, str] = {}
        if component_id is not None:
            query += " WHERE component_id = :component_id"
            params["component_id"] = component_id
        query += " ORDER BY component_id, timestamp"
        with self.engine.connect() as connection:
            return pd.read_sql(text(query), connection, params=params)

    def count(self) -> int:
        query = text(f"SELECT COUNT(*) AS row_count FROM {self.TABLE_NAME}")
        with self.engine.connect() as connection:
            return int(connection.execute(query).scalar_one())

