"""Data source abstraction example."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from timeseriesflow import entity_flow, EntityContext
from timeseriesflow.sources import CSVSource, ParquetSource, SourceSchema


def write_sample_csv(path: Path) -> None:
    base = datetime(2024, 6, 1, tzinfo=timezone.utc)
    rows = []
    for device_id in ("D-1", "D-2"):
        for minute in range(5):
            rows.append(
                {
                    "device_id": device_id,
                    "timestamp": base + timedelta(minutes=minute),
                    "temperature": 20.0 + minute,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


@entity_flow(entity_key="device_id", time_key="timestamp")
def summarize_device(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    return {
        "device_id": ctx.entity_id,
        "rows": len(df),
        "mean_temperature": float(df["temperature"].mean()),
    }


def run_with_csv(path: Path) -> None:
    schema = SourceSchema(required_columns=("device_id", "timestamp", "temperature"))
    source = CSVSource(
        path,
        parse_dates=["timestamp"],
        selected_columns=["device_id", "timestamp", "temperature"],
        schema=schema,
    )
    source.validate()
    df = source.load()
    result = summarize_device.run(df)
    print("CSV:", result.outputs)


def run_with_parquet(path: Path) -> None:
    schema = SourceSchema(required_columns=("device_id", "timestamp", "temperature"))
    source = ParquetSource(
        path,
        selected_columns=["device_id", "timestamp", "temperature"],
        schema=schema,
    )
    source.validate()
    df = source.load()
    result = summarize_device.run(df)
    print("Parquet:", result.outputs)


def main() -> None:
    data_dir = Path("./.example_data")
    data_dir.mkdir(exist_ok=True)

    csv_path = data_dir / "devices.csv"
    write_sample_csv(csv_path)
    run_with_csv(csv_path)

    try:
        parquet_path = data_dir / "devices.parquet"
        pd.read_csv(csv_path, parse_dates=["timestamp"]).to_parquet(parquet_path, index=False)
        run_with_parquet(parquet_path)
    except ImportError:
        print("Skipping Parquet example; install pyarrow: pip install timeseriesflow[parquet]")


if __name__ == "__main__":
    main()
