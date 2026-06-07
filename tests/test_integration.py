"""Integration tests across modules."""

from __future__ import annotations

import pandas as pd

from timeseriesflow import Flow, entity_processor
from timeseriesflow.config import FlowConfig


@entity_processor
def resample_hourly(df: pd.DataFrame, context) -> pd.DataFrame:
    out = df.set_index("timestamp").sort_index()
    out = out[["value"]].resample("2h").mean().reset_index()
    out["sensor_id"] = context.entity_id
    return out


def test_end_to_end_with_checkpoint_resume(sample_df: pd.DataFrame, tmp_path) -> None:
    checkpoint_dir = tmp_path / "checkpoints"
    config = FlowConfig(
        entity_column="sensor_id",
        checkpoint_dir=checkpoint_dir,
        show_progress=False,
        track_memory=False,
        max_entities=2,
    )
    flow = Flow(resample_hourly, config)
    output, summary = flow.run(sample_df)

    assert output is not None
    assert summary.processed == 2
    assert summary.succeeded == 2

    flow2 = Flow(resample_hourly, config)
    output2, summary2 = flow2.run(sample_df)
    assert summary2.skipped == 2
    assert summary2.processed == 0
    assert output2 is None
