"""Pytest fixtures and helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from timeseriesflow.config import FlowConfig


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
