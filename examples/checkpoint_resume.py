"""Checkpoint resume example for long entity runs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from timeseriesflow import EntityContext, entity_flow
from timeseriesflow.checkpoint import LocalCheckpoint


def build_data(devices: int = 5, points: int = 100) -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for device_id in range(devices):
        for minute in range(points):
            rows.append(
                {
                    "device_id": f"D-{device_id:03d}",
                    "timestamp": base + timedelta(minutes=minute),
                    "value": float(minute),
                }
            )
    return pd.DataFrame(rows)


@entity_flow(
    entity_key="device_id",
    time_key="timestamp",
    checkpoint_dir=Path("./.timeseriesflow/checkpoints"),
)
def process_device(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    return {"device_id": ctx.entity_id, "rows": len(df)}


def inspect_checkpoint() -> None:
    checkpoint = LocalCheckpoint(Path("./.timeseriesflow/checkpoints"))
    summary = checkpoint.summary()
    print(f"Completed: {summary.completed_count}, failed: {summary.failed_count}")
    print(f"Total log entries: {summary.total_entries}")


def main() -> None:
    df = build_data(devices=3, points=10)
    result = process_device.run(df)
    print(f"Processed: {result.processed}, skipped: {result.skipped}")
    inspect_checkpoint()


if __name__ == "__main__":
    main()
