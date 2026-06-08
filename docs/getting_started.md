# Getting started

## Installation

```bash
pip install timeseriesflow
```

For development:

```bash
git clone https://github.com/baban9/timeseriesflow.git
cd timeseriesflow
pip install -e ".[dev]"
```

## Golden path (recommended)

1. Define a per-entity function with `@entity_flow`.
2. Run in-memory with `.run(df)` or in production with `EntityRunner` / `tsflow run`.

See [golden_path.md](golden_path.md) for the full guide.

### Step 1: Define an entity flow

```python
import pandas as pd
from timeseriesflow import EntityContext, entity_flow

@entity_flow(entity_key="sensor_id", time_key="timestamp")
def process_sensor(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    return {"sensor_id": ctx.entity_id, "rows": len(df)}

result = process_sensor.run(df)
print(result.succeeded, result.failed)
```

`entity_key` and `entity_column` are equivalent.

### Step 2: Production run with EntityRunner

```python
from timeseriesflow import EntityRunner
from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.sources import CSVSource

runner = EntityRunner(
    source=CSVSource("data.csv", parse_dates=["timestamp"]),
    flow=process_sensor,
    checkpoint=LocalCheckpoint("./checkpoints"),
    retries=3,
)
summary = runner.run()
```

Or use the CLI:

```bash
tsflow run examples/basic_pipeline.py
tsflow validate examples/basic_pipeline.py
```

## Combined workflow with AdaptiveForecast

Profile each entity and recommend a forecasting architecture:

```bash
python examples/advise_and_process.py
```

See [combined_workflow.md](combined_workflow.md).

## Legacy Flow API

`Flow` + `FlowConfig` remains for existing code. A deprecation warning is planned for v0.2.

```python
from timeseriesflow import Flow, FlowConfig, entity_processor

config = FlowConfig(entity_column="sensor_id", show_progress=False)
output, summary = Flow(process_entity, config).run(df)
```

See `examples/basic_usage.py` for a legacy example.

## Checkpointing and resume

```python
from timeseriesflow.checkpoint import LocalCheckpoint

@entity_flow(
    entity_key="device_id",
    time_key="timestamp",
    checkpoint_dir="./checkpoints",
)
def process_device(df, ctx):
    return {"rows": len(df)}
```

On restart, completed entities are skipped automatically.

## CLI

```bash
tsflow --version
tsflow info
tsflow checkpoint-status --checkpoint-dir ./checkpoints
```
