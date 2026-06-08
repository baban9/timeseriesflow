"""Tests for cross-API naming aliases."""

from __future__ import annotations

import pandas as pd

from timeseriesflow import EntityContext, entity_flow
from timeseriesflow.api.naming import resolve_entity_column_name
from timeseriesflow.api.result import EntityResult
from timeseriesflow.types import FlowEntityResult


def test_resolve_entity_column_name_prefers_either_alias() -> None:
    assert resolve_entity_column_name(entity_key="device_id") == "device_id"
    assert resolve_entity_column_name(entity_column="device_id") == "device_id"


def test_resolve_entity_column_name_rejects_mismatch() -> None:
    try:
        resolve_entity_column_name(entity_key="a", entity_column="b")
    except ValueError as exc:
        assert "must match" in str(exc)
    else:
        raise AssertionError("expected ValueError")


@entity_flow(entity_column="sensor_id", time_key="timestamp")
def process_with_entity_column(df: pd.DataFrame, ctx: EntityContext) -> dict[str, str]:
    assert ctx.entity_column == "sensor_id"
    assert ctx.entity_key == "sensor_id"
    return {"entity": str(ctx.entity_id)}


def test_entity_flow_accepts_entity_column_alias(sample_df: pd.DataFrame) -> None:
    result = process_with_entity_column.run(sample_df)
    assert result.succeeded == 3


def test_entity_result_duration_aliases() -> None:
    result = EntityResult(
        entity_id="S1",
        success=True,
        runtime_seconds=1.5,
        memory_delta_mb=2.0,
    )
    assert result.duration_seconds == 1.5
    assert result.peak_memory_mb == 2.0


def test_flow_entity_result_runtime_aliases() -> None:
    result = FlowEntityResult(
        entity_id="S1",
        success=True,
        duration_seconds=1.5,
        peak_memory_mb=2.0,
    )
    assert result.runtime_seconds == 1.5
    assert result.memory_delta_mb == 2.0
