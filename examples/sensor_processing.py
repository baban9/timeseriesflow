"""Sensor anomaly flagging example."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from timeseriesflow import Flow, FlowConfig, RetryPolicy, entity_processor


def build_sensor_data(n_sensors: int = 5, points: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for sensor_id in range(n_sensors):
        baseline = rng.normal(50, 5, size=points)
        for i, value in enumerate(baseline):
            rows.append(
                {
                    "sensor_id": f"S-{sensor_id:03d}",
                    "timestamp": base + timedelta(minutes=i),
                    "temperature": float(value),
                }
            )
    return pd.DataFrame(rows)


@entity_processor
def flag_anomalies(df: pd.DataFrame, context) -> pd.DataFrame:
    out = df.copy()
    mean = out["temperature"].mean()
    std = out["temperature"].std()
    if std == 0:
        out["z_score"] = 0.0
    else:
        out["z_score"] = (out["temperature"] - mean) / std
    out["is_anomaly"] = out["z_score"].abs() > 2.5
    out["sensor"] = context.entity_id
    return out


def main() -> None:
    df = build_sensor_data()
    config = FlowConfig(
        entity_column="sensor_id",
        checkpoint_dir=None,
        retry_policy=RetryPolicy(max_attempts=2),
        show_progress=True,
    )
    flow = Flow(flag_anomalies, config)
    output, summary = flow.run(df)

    if output is not None:
        anomalies = output[output["is_anomaly"]]
        print(f"Anomalies detected: {len(anomalies)} across {summary.succeeded} sensors")


if __name__ == "__main__":
    main()
