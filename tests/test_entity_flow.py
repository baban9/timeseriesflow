"""Tests for the entity flow developer API."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from timeseriesflow import (
    EntityContext,
    EntityFlow,
    EntityFlowResult,
    entity_flow,
)
from timeseriesflow.exceptions import ColumnValidationError


@entity_flow(entity_key="sensor_id", time_key="timestamp")
def count_rows(df: pd.DataFrame, ctx: EntityContext) -> dict[str, int | str]:
    ctx.logger.debug("processing entity %s", ctx.entity_id)
    return {"rows": len(df), "entity": str(ctx.entity_id)}


@entity_flow(entity_key="sensor_id", time_key="timestamp")
def record_first_timestamp(df: pd.DataFrame, ctx: EntityContext) -> object:
    return df["timestamp"].iloc[0]


@entity_flow(entity_key="sensor_id", time_key="timestamp")
def failing_on_s2(df: pd.DataFrame, ctx: EntityContext) -> dict[str, int]:
    if ctx.entity_id == "S2":
        raise ValueError("simulated failure")
    return {"rows": len(df)}


def test_entity_flow_basic_run(sample_df: pd.DataFrame) -> None:
    result = count_rows.run(sample_df)

    assert isinstance(result, EntityFlowResult)
    assert result.processed == 3
    assert result.succeeded == 3
    assert result.failed == 0
    assert all(item["rows"] == 5 for item in result.outputs)


def test_entity_flow_result_by_entity(sample_df: pd.DataFrame) -> None:
    result = count_rows.run(sample_df)
    entity_result = result.by_entity("S1")

    assert entity_result is not None
    assert entity_result.success is True
    assert entity_result.output == {"rows": 5, "entity": "S1"}
    assert entity_result.runtime_seconds >= 0.0
    assert entity_result.memory_delta_mb >= 0.0
    assert entity_result.error is None


def test_entity_flow_sorts_by_time_key() -> None:
    df = pd.DataFrame(
        {
            "sensor_id": ["A", "A", "A"],
            "timestamp": pd.to_datetime(["2024-01-03", "2024-01-01", "2024-01-02"]),
            "value": [3, 1, 2],
        }
    )
    flow_result = record_first_timestamp.run(df)
    first = flow_result.by_entity("A")

    assert first is not None
    assert first.output == pd.Timestamp("2024-01-01")


def test_entity_flow_validates_required_columns(sample_df: pd.DataFrame) -> None:
    bad_df = sample_df.drop(columns=["timestamp"])
    with pytest.raises(ColumnValidationError, match="timestamp"):
        count_rows.run(bad_df)


def test_entity_flow_does_not_mutate_source(sample_df: pd.DataFrame) -> None:
    original = sample_df.copy(deep=True)
    count_rows.run(sample_df)
    pd.testing.assert_frame_equal(sample_df, original)


def test_entity_flow_failure_is_collected(sample_df: pd.DataFrame) -> None:
    result = failing_on_s2.run(sample_df)

    assert result.succeeded == 2
    assert result.failed == 1
    failed = result.by_entity("S2")
    assert failed is not None
    assert failed.success is False
    assert isinstance(failed.error, ValueError)


def test_entity_context_exposes_logger(sample_df: pd.DataFrame, caplog: pytest.LogCaptureFixture) -> None:
    @entity_flow(entity_key="sensor_id", time_key="timestamp")
    def log_entity(df: pd.DataFrame, ctx: EntityContext) -> None:
        assert ctx.entity_key == "sensor_id"
        assert ctx.time_key == "timestamp"
        assert isinstance(ctx.logger, logging.Logger)
        ctx.logger.info("entity=%s", ctx.entity_id)

    with caplog.at_level(logging.INFO, logger="timeseriesflow.entity_flow.S1"):
        log_entity.run(sample_df)

    assert any("entity=S1" in record.message for record in caplog.records)


def test_entity_flow_class_direct_usage(sample_df: pd.DataFrame) -> None:
    def processor(df: pd.DataFrame, ctx: EntityContext) -> int:
        return len(df)

    flow = EntityFlow(processor, entity_key="sensor_id", time_key="timestamp")
    result = flow.run(sample_df)

    assert result.processed == 3
    assert result.outputs == [5, 5, 5]


def test_entity_flow_rejects_empty_keys() -> None:
    def processor(df: pd.DataFrame, ctx: EntityContext) -> None:
        return None

    with pytest.raises(ValueError, match="entity_key"):
        EntityFlow(processor, entity_key="", time_key="timestamp")

    with pytest.raises(ValueError, match="time_key"):
        EntityFlow(processor, entity_key="id", time_key="")


def test_decorator_exposes_flow_metadata() -> None:
    assert count_rows.entity_key == "sensor_id"
    assert count_rows.time_key == "timestamp"
    assert isinstance(count_rows.flow, EntityFlow)
