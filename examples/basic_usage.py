"""Basic TimeSeriesFlow usage example."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from timeseriesflow import Flow, FlowConfig, entity_processor


def build_sample_data() -> pd.DataFrame:
    base = datetime(2024, 6, 1, tzinfo=timezone.utc)
    rows = []
    for device_id in range(3):
        for minute in range(60):
            rows.append(
                {
                    "device_id": device_id,
                    "timestamp": base + timedelta(minutes=minute),
                    "reading": float(minute + device_id),
                }
            )
    return pd.DataFrame(rows)


@entity_processor
def compute_rolling_mean(df: pd.DataFrame, context) -> pd.DataFrame:
    """User-defined logic for one entity."""
    out = df.sort_values("timestamp").copy()
    out["rolling_mean"] = out["reading"].rolling(window=5, min_periods=1).mean()
    out["processed_by"] = str(context.entity_id)
    return out


def main() -> None:
    df = build_sample_data()
    config = FlowConfig(
        entity_column="device_id",
        checkpoint_dir=None,
        show_progress=True,
    )
    flow = Flow(compute_rolling_mean, config)
    output, summary = flow.run(df)

    print(f"Processed {summary.succeeded} entities")
    if output is not None:
        print(output.head())


if __name__ == "__main__":
    main()
