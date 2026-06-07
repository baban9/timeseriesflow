# Public API reference

## Developer API (recommended)

```python
from timeseriesflow import (
    entity_flow,
    EntityContext,
    EntityResult,
    EntityFlowResult,
    EntityFlow,
    ColumnValidationError,
)
```

### entity_flow decorator

```python
@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    return {"rows": len(df)}

flow_result = process_device.run(df)
```

### EntityContext

| Field | Description |
|-------|-------------|
| `entity_id` | Current entity identifier |
| `entity_key` | Configured entity column name |
| `time_key` | Configured time column name |
| `logger` | Entity-scoped logger |
| `metadata` | Optional user metadata dict |

### EntityResult

| Field | Description |
|-------|-------------|
| `entity_id` | Processed entity identifier |
| `success` | Whether processing succeeded |
| `runtime_seconds` | Wall-clock duration |
| `memory_delta_mb` | RSS memory increase during run |
| `output` | Processor return value on success |
| `error` | Exception on failure |

### EntityFlow

Direct usage without the decorator:

```python
flow = EntityFlow(processor, entity_key="device_id", time_key="timestamp")
result = flow.run(df)
```

Framework guarantees:

- Validates required columns before processing
- Sorts each entity frame by `time_key`
- Processes entities sequentially
- Never mutates the source dataframe
- Collects one `EntityResult` per entity

## Data sources

See [sources.md](sources.md) for full documentation.

```python
from timeseriesflow import CSVSource, ParquetSource, SourceSchema

schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
source = CSVSource("data.csv", parse_dates=["timestamp"], schema=schema)
source.validate()
df = source.load()
```

| Class | Description |
|-------|-------------|
| `BaseSource` | Abstract root for all sources |
| `TabularSource` | Abstract base for DataFrame sources (MongoDB extension point) |
| `FileSource` | Abstract base for filesystem sources |
| `CSVSource` | CSV loader with `parse_dates` and `selected_columns` |
| `ParquetSource` | Parquet loader with `selected_columns` |
| `SourceSchema` | Required and optional column validation |

| Exception | Description |
|-----------|-------------|
| `SourceError` | Base class for source errors |
| `SourceNotFoundError` | Path or location not found |
| `SourceSchemaError` | Schema or column validation failure |
| `SourceLoadError` | Read or engine failure |

## Checkpointing

See [checkpointing.md](checkpointing.md) for full documentation.

```python
from timeseriesflow import LocalCheckpoint, entity_flow

@entity_flow(
    entity_key="device_id",
    time_key="timestamp",
    checkpoint_dir="./.timeseriesflow/checkpoints",
)
def process_device(df, ctx):
    return {"rows": len(df)}
```

| Class | Description |
|-------|-------------|
| `CheckpointBackend` | Abstract checkpoint interface |
| `LocalCheckpoint` | Append-only JSONL backend on local disk |
| `CheckpointSummary` | Aggregate completed/failed counts |
| `CheckpointEntry` | Single checkpoint record |

| Method | Description |
|--------|-------------|
| `mark_completed(entity_id)` | Record success (idempotent) |
| `mark_failed(entity_id, error=...)` | Record failure |
| `is_completed(entity_id)` | Check latest status |
| `load_completed()` | Set of completed entity IDs |
| `load_failed()` | Set of failed entity IDs |
| `summary()` | Aggregate statistics |

## Memory tracking

See [memory.md](memory.md) for full documentation.

```python
from timeseriesflow import track_memory, MemoryTracker

@track_memory
def process():
    ...

print(process.last_metrics.to_dict())
```

| Class / function | Description |
|------------------|-------------|
| `MemoryTracker` | Scoped and peak memory tracking |
| `MemoryMetrics` | Result dataclass with `to_dict()` |
| `track_memory` | Decorator for function-level profiling |

## CLI (tsflow)

See [cli.md](cli.md) for full documentation.

```bash
tsflow run examples/basic_pipeline.py
tsflow validate examples/basic_pipeline.py
tsflow info
tsflow checkpoint-status --checkpoint-dir ./checkpoints
```

## EntityRunner

See [runner.md](runner.md) for full documentation.

```python
from timeseriesflow import EntityRunner, entity_flow, EntityContext
from timeseriesflow.sources import CSVSource
from timeseriesflow.checkpoint import LocalCheckpoint

runner = EntityRunner(
    source=CSVSource("data.csv", parse_dates=["timestamp"]),
    flow=process_device,
    checkpoint=LocalCheckpoint("./checkpoints"),
    batch_size=100,
    retries=3,
)
summary = runner.run()
```

## Legacy Flow API

```python
from timeseriesflow import (
    Flow,
    FlowConfig,
    EntityProcessor,
    entity_processor,
    RunContext,
    FlowEntityResult,
    RunSummary,
    RetryPolicy,
    CheckpointStore,
    FileCheckpointStore,
    MemoryTracker,
    MemorySnapshot,
    ProgressTracker,
    FlowError,
    EntityProcessingError,
    RetryExhaustedError,
    CheckpointError,
)
```

## Flow

```python
class Flow:
    def __init__(
        self,
        processor: EntityProcessor,
        config: FlowConfig,
        *,
        checkpoint: CheckpointBackend | CheckpointStore | None = None,
    ) -> None: ...

    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame | None, RunSummary]: ...
```

Main entry point. Processes all entities and returns combined output plus summary.

## FlowConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `entity_column` | `str` | required | Column identifying entities |
| `checkpoint_dir` | `Path \| None` | `None` | Directory for file checkpoints |
| `resume` | `bool` | `True` | Skip completed entities on restart |
| `fail_fast` | `bool` | `False` | Stop on first entity failure |
| `retry_policy` | `RetryPolicy` | default policy | Retry configuration |
| `show_progress` | `bool` | `True` | Rich progress bar |
| `track_memory` | `bool` | `True` | Peak memory tracking |
| `log_level` | `str` | `"INFO"` | Logging level |
| `sort_entities` | `bool` | `True` | Deterministic entity order |
| `max_entities` | `int \| None` | `None` | Limit entities processed |

## EntityProcessor

Protocol for user-defined processing functions:

```python
def my_processor(df: pd.DataFrame, context: RunContext) -> pd.DataFrame:
    ...
```

Use `@entity_processor` decorator for metadata marking (optional).

## RunContext

| Field | Description |
|-------|-------------|
| `entity_id` | Current entity identifier |
| `entity_column` | Configured entity column name |
| `attempt` | Current attempt number (1-indexed) |
| `started_at` | UTC timestamp when processing started |

Method: `elapsed_seconds() -> float`

## EntityResult (legacy Flow)

Per-entity outcome via `FlowEntityResult`: `success`, `dataframe`, `error`, `attempts`, `duration_seconds`, `peak_memory_mb`, `metadata`.

## RunSummary

Aggregate run statistics: `total_entities`, `processed`, `succeeded`, `failed`, `skipped`, `total_duration_seconds`, `peak_memory_mb`, `results`, `success_rate`.

## RetryPolicy

| Field | Default |
|-------|---------|
| `max_attempts` | 3 |
| `initial_delay_seconds` | 0.5 |
| `max_delay_seconds` | 30.0 |
| `exponential_base` | 2.0 |
| `jitter` | True |
| `retryable_exceptions` | TimeoutError, ConnectionError, OSError |

## CheckpointStore

Abstract interface:

- `load_completed_entities() -> set[EntityId]`
- `save(record: CheckpointRecord) -> None`
- `clear() -> None`

`FileCheckpointStore(directory: Path)` is the default file-based implementation.

## CLI

```bash
tsflow --version
tsflow info [--checkpoint-dir PATH]
```
