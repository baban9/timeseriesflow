"""Pytest fixtures and helpers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from timeseriesflow.config import FlowConfig
from timeseriesflow.sources.schema import SourceSchema


@pytest.fixture(autouse=True)
def _reset_timeseriesflow_logging() -> None:
    """Keep package logging from conflicting with pytest caplog."""
    package_logger = logging.getLogger("timeseriesflow")
    previous_handlers = package_logger.handlers[:]
    previous_propagate = package_logger.propagate
    package_logger.handlers.clear()
    package_logger.propagate = True
    yield
    package_logger.handlers[:] = previous_handlers
    package_logger.propagate = previous_propagate


@pytest.fixture
def sample_df() -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for sensor in ("S1", "S2", "S3"):
        for hour in range(5):
            rows.append(
                {
                    "sensor_id": sensor,
                    "timestamp": base + timedelta(hours=hour),
                    "value": hour * 10 + len(sensor),
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def flow_config(tmp_path) -> FlowConfig:
    return FlowConfig(
        entity_column="sensor_id",
        checkpoint_dir=tmp_path / "checkpoints",
        show_progress=False,
        track_memory=False,
    )


@pytest.fixture
def sensor_schema() -> SourceSchema:
    return SourceSchema(
        required_columns=("sensor_id", "timestamp", "value"),
        optional_columns=("quality",),
    )


@pytest.fixture
def sample_sensor_df() -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for sensor in ("S1", "S2"):
        for hour in range(3):
            rows.append(
                {
                    "sensor_id": sensor,
                    "timestamp": base + timedelta(hours=hour),
                    "value": float(hour),
                    "quality": "good",
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def csv_path(tmp_path: Path, sample_sensor_df: pd.DataFrame) -> Path:
    path = tmp_path / "sensors.csv"
    sample_sensor_df.to_csv(path, index=False)
    return path


@pytest.fixture
def parquet_path(tmp_path: Path, sample_sensor_df: pd.DataFrame) -> Path:
    pytest.importorskip("pyarrow")
    path = tmp_path / "sensors.parquet"
    sample_sensor_df.to_parquet(path, index=False)
    return path
