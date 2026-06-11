"""EntityRunner benchmark example.

Run:
    python examples/runner_benchmark.py

Measures throughput for batched entity processing with checkpointing disabled.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from timeseriesflow import EntityContext, EntityRunner, entity_flow
from timeseriesflow.sources import CSVSource, SourceSchema


def build_dataset(path: Path, *, devices: int, points: int) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for device_id in range(devices):
        for minute in range(points):
            rows.append(
                {
                    "device_id": f"D-{device_id:06d}",
                    "timestamp": base + timedelta(minutes=minute),
                    "value": float(minute + device_id),
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


@entity_flow(entity_key="device_id", time_key="timestamp")
def lightweight_summary(df: pd.DataFrame, ctx: EntityContext) -> dict[str, float]:
    return {
        "rows": float(len(df)),
        "mean": float(df["value"].mean()),
    }


def run_benchmark(*, devices: int, points: int, batch_size: int, workers: int) -> None:
    data_dir = Path("./.benchmark_data")
    data_dir.mkdir(exist_ok=True)
    csv_path = data_dir / f"devices_{devices}x{points}.csv"

    if not csv_path.exists():
        print(f"Building dataset: {devices} devices x {points} points")
        build_dataset(csv_path, devices=devices, points=points)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(
        csv_path,
        parse_dates=["timestamp"],
        selected_columns=["device_id", "timestamp", "value"],
        schema=schema,
    )

    runner = EntityRunner(
        source=source,
        flow=lightweight_summary,
        batch_size=batch_size,
        workers=workers,
        retries=1,
        show_progress=False,
    )

    started = time.perf_counter()
    summary = runner.run()
    elapsed = time.perf_counter() - started

    entities_per_sec = summary.processed / elapsed if elapsed > 0 else 0.0
    print(f"Devices: {devices}, points per device: {points}, workers: {workers}")
    print(f"Processed: {summary.processed}, batches: {summary.batches_processed}")
    print(f"Elapsed: {elapsed:.2f}s, throughput: {entities_per_sec:.1f} entities/sec")
    print(f"Peak memory: {summary.peak_memory_mb:.1f} MB")


def main() -> None:
    for workers in (1, 4):
        print(f"\n--- workers={workers} ---")
        run_benchmark(devices=500, points=20, batch_size=100, workers=workers)


if __name__ == "__main__":
    main()
