"""Entity flow developer API example."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from timeseriesflow import EntityContext, entity_flow


def build_device_data() -> pd.DataFrame:
    base = datetime(2024, 6, 1, tzinfo=timezone.utc)
    rows = []
    for device_id in ("D-100", "D-200", "D-300"):
        for minute in range(10):
            rows.append(
                {
                    "device_id": device_id,
                    "timestamp": base + timedelta(minutes=minute),
                    "temperature": 20.0 + minute * 0.1,
                }
            )
    return pd.DataFrame(rows)


@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    """Process one device time series."""
    ctx.logger.info("processing device %s with %d rows", ctx.entity_id, len(df))
    return {
        "device_id": ctx.entity_id,
        "rows": len(df),
        "mean_temperature": float(df["temperature"].mean()),
        "first_reading": df["timestamp"].iloc[0].isoformat(),
    }


def main() -> None:
    df = build_device_data()
    flow_result = process_device.run(df)

    print(f"Processed {flow_result.processed} devices")
    print(f"Succeeded: {flow_result.succeeded}, failed: {flow_result.failed}")

    for output in flow_result.outputs:
        print(output)


if __name__ == "__main__":
    main()
