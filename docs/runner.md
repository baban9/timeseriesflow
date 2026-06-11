# EntityRunner

`EntityRunner` is the top-level orchestrator that connects data sources, entity flows, checkpoints, retries, and progress tracking into a single production-ready entry point.

## Overview

```
CSVSource / ParquetSource
        |
        v
   EntityRunner.run()
        |
        +-- validate + load source
        +-- discover entities
        +-- skip completed (checkpoint)
        +-- process in batches
        +-- retry failures
        +-- update checkpoints
        +-- track progress (Rich)
        |
        v
    RunSummary
```

## Quick start

```python
from timeseriesflow import EntityRunner, entity_flow, EntityContext
from timeseriesflow.sources import CSVSource, SourceSchema
from timeseriesflow.checkpoint import LocalCheckpoint

schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))

@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df, ctx: EntityContext):
    return {"rows": len(df)}

runner = EntityRunner(
    source=CSVSource("data.csv", parse_dates=["timestamp"], schema=schema),
    flow=process_device,
    checkpoint=LocalCheckpoint("./checkpoints"),
    batch_size=100,
    workers=4,
    retries=3,
)

summary = runner.run()
print(summary.success_rate, summary.total_retries)
```

## Constructor parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `source` | required | `TabularSource` (CSV, Parquet, future Mongo) |
| `flow` | required | `EntityFlow` or `@entity_flow` function |
| `checkpoint` | `None` | Optional `CheckpointBackend` for resume |
| `batch_size` | `100` | Entities processed per batch |
| `workers` | `1` | Parallel entity workers per batch (`1` = sequential) |
| `retries` | `3` | Attempts per entity before marking failed |
| `resume` | `True` | Skip entities already in checkpoint |
| `fail_fast` | `False` | Stop on first entity failure |
| `show_progress` | `True` | Rich progress bar |
| `log_level` | `"INFO"` | Structured logging level |
| `retry_policy` | auto | Custom `RetryPolicy` for backoff between retries |

## RunSummary

Returned by `runner.run()`:

| Field | Description |
|-------|-------------|
| `total_entities` | All entities in source |
| `processed` | Entities processed this run |
| `succeeded` | Successful entities |
| `failed` | Failed entities |
| `skipped` | Skipped via checkpoint resume |
| `total_duration_seconds` | Wall-clock run time |
| `peak_memory_mb` | Peak RSS during run |
| `batches_processed` | Number of batches executed |
| `total_retries` | Extra retry attempts across all entities |
| `results` | List of `EntityResult` per processed entity |
| `success_rate` | `succeeded / processed` |

## Responsibilities

### Load source

Calls `source.validate()` then `source.load()`. Schema and file checks run before any entity processing.

### Discover entities

Uses the flow `entity_key` to list unique entities from the loaded dataframe.

### Execute flow

Calls `flow.process_entity(df, entity_id)` for each pending entity. Sorting by time column is handled inside the flow.

### Manage retries

On failure, retries up to `retries` times with configurable backoff via `RetryPolicy`. Only the final outcome is checkpointed.

### Update checkpoints

On success: `checkpoint.mark_completed(...)`. On final failure: `checkpoint.mark_failed(...)`.

### Track progress

Rich progress bar shows per-entity status. Structured logs record batch boundaries, retries, and completion stats.

## Batch processing

`batch_size` controls how many entities are grouped per batch for logging and operational clarity. All entity data is loaded once; batches do not reload the source.

For very large datasets, combine `lazy=True` on the source with future chunked source APIs.

## Parallel workers

Set `workers` greater than `1` to process entities in a batch concurrently with a thread pool.

```python
runner = EntityRunner(
    source=source,
    flow=process_device,
    batch_size=100,
    workers=8,
)
```

Notes:

- Default is `workers=1` (sequential), matching prior behavior.
- Effective concurrency per batch is `min(workers, batch_size)`.
- Checkpoints and progress updates are thread-safe.
- Best for I/O-bound or per-entity pandas work. CPU-heavy pure Python may still be limited by the GIL.
- Processor functions must be thread-safe if they share mutable global state.

## Failure handling

- Retries: transient processor failures are retried with backoff.
- Checkpoint: final failures are recorded and retried on the next run (not skipped like completed entities).
- Fail fast: set `fail_fast=True` to raise `EntityProcessingError` on the first final failure.

## Benchmark

See `examples/runner_benchmark.py` for a throughput measurement script:

```bash
python examples/runner_benchmark.py
```

## When to use EntityRunner vs EntityFlow.run()

| Use case | API |
|----------|-----|
| Full pipeline from file/source with resume | `EntityRunner` |
| In-memory dataframe already loaded | `flow.run(df)` |
| Legacy checkpoint/retry Flow engine | `Flow(config)` |
