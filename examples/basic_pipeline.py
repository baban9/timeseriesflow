"""Basic pipeline for tsflow run examples.

Run:
    tsflow run examples/basic_pipeline.py
    tsflow validate examples/basic_pipeline.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from timeseriesflow import EntityContext, EntityRunner, entity_flow
from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.progress import RunSummary
from timeseriesflow.sources import CSVSource, SourceSchema

PIPELINE_DIR = Path(__file__).resolve().parent
DATA_PATH = PIPELINE_DIR / "data" / "sample_devices.csv"
CHECKPOINT_DIR = PIPELINE_DIR / ".checkpoints" / "basic_pipeline"

SCHEMA = SourceSchema(required_columns=("device_id", "timestamp", "value"))


@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    """Compute a simple summary for one device."""
    return {
        "device_id": ctx.entity_id,
        "rows": len(df),
        "mean_value": float(df["value"].mean()),
    }


def create_runner(*, show_progress: bool = True) -> EntityRunner:
    """Build the EntityRunner for this pipeline."""
    return EntityRunner(
        source=CSVSource(
            DATA_PATH,
            parse_dates=["timestamp"],
            schema=SCHEMA,
        ),
        flow=process_device,
        checkpoint=LocalCheckpoint(CHECKPOINT_DIR),
        batch_size=10,
        retries=2,
        show_progress=show_progress,
    )


def validate() -> None:
    """Validate source data and schema without running the flow."""
    source = CSVSource(DATA_PATH, parse_dates=["timestamp"], schema=SCHEMA)
    source.validate()


def run() -> RunSummary:
    """Execute the pipeline and return run statistics."""
    return create_runner().run()


def main() -> RunSummary:
    """Alias for scripts that call main()."""
    return run()


if __name__ == "__main__":
    summary = run()
    print(f"Processed {summary.processed} devices, skipped {summary.skipped}")
