"""Tests for the Flow execution engine."""

from __future__ import annotations

import pandas as pd
import pytest

from timeseriesflow import Flow, entity_processor
from timeseriesflow.config import FlowConfig
from timeseriesflow.exceptions import EntityProcessingError


@entity_processor
def add_mean_column(df: pd.DataFrame, context) -> pd.DataFrame:
    out = df.copy()
    out["entity_mean"] = out["value"].mean()
    out["entity_id_copy"] = context.entity_id
    return out


@entity_processor
def failing_processor(df: pd.DataFrame, context) -> pd.DataFrame:
    if context.entity_id == "S2":
        raise ValueError("simulated failure")
    out = df.copy()
    out["ok"] = True
    return out


def test_flow_run_success(sample_df: pd.DataFrame, flow_config: FlowConfig) -> None:
    flow = Flow(add_mean_column, flow_config)
    output, summary = flow.run(sample_df)

    assert output is not None
    assert len(output) == 15
    assert summary.succeeded == 3
    assert summary.failed == 0
    assert "entity_mean" in output.columns


def test_flow_run_with_failures(sample_df: pd.DataFrame, flow_config: FlowConfig) -> None:
    flow = Flow(failing_processor, flow_config)
    output, summary = flow.run(sample_df)

    assert output is not None
    assert len(output) == 10
    assert summary.succeeded == 2
    assert summary.failed == 1


def test_flow_fail_fast(sample_df: pd.DataFrame, flow_config: FlowConfig) -> None:
    flow_config.fail_fast = True
    flow = Flow(failing_processor, flow_config)
    with pytest.raises(EntityProcessingError):
        flow.run(sample_df)
