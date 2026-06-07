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

## Your first flow

1. Prepare a pandas DataFrame with an entity column and time-series columns.
2. Write a processor function that accepts `(df, context)` and returns a DataFrame.
3. Create a `FlowConfig` with the entity column name.
4. Run `Flow(processor, config).run(df)`.

See `examples/basic_usage.py` for a complete runnable script.

## Checkpointing and resume

Set `checkpoint_dir` in `FlowConfig` to enable file-based checkpoints:

```python
from pathlib import Path
from timeseriesflow import Flow, FlowConfig

config = FlowConfig(
    entity_column="sensor_id",
    checkpoint_dir=Path("./.timeseriesflow/checkpoints"),
    resume=True,
)
```

On restart, successfully completed entities are skipped automatically.

## Retries

Configure retry behavior with `RetryPolicy`:

```python
from timeseriesflow import RetryPolicy, FlowConfig

config = FlowConfig(
    entity_column="device_id",
    retry_policy=RetryPolicy(max_attempts=5, initial_delay_seconds=1.0),
)
```

By default, `TimeoutError`, `ConnectionError`, and `OSError` are retried.

## CLI

```bash
timeseriesflow version
timeseriesflow info --checkpoint-dir ./.timeseriesflow/checkpoints
```
