"""Smoke tests for the legacy Flow engine."""

from __future__ import annotations

import pandas as pd

from timeseriesflow import Flow, FlowConfig, entity_processor
from timeseriesflow.core.engine import Flow as EngineFlow
from timeseriesflow.progress import RunSummary


@entity_processor
def _identity(df: pd.DataFrame, context) -> pd.DataFrame:
    return df


def test_flow_engine_imports_run_summary() -> None:
    """Flow.run must return RunSummary without import errors."""
    assert EngineFlow.__module__ == "timeseriesflow.core.engine"
    assert RunSummary.__module__ == "timeseriesflow.progress"


def test_flow_run_returns_summary(sample_df: pd.DataFrame) -> None:
    config = FlowConfig(entity_column="sensor_id", show_progress=False)
    flow = Flow(_identity, config)
    output, summary = flow.run(sample_df)
    assert output is not None
    assert summary.succeeded == 3
    assert summary.failed == 0
