# Public API reference

## Top-level exports

```python
from timeseriesflow import (
    Flow,
    FlowConfig,
    EntityProcessor,
    entity_processor,
    RunContext,
    EntityResult,
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
        checkpoint_store: CheckpointStore | None = None,
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

## EntityResult

Per-entity outcome with `success`, `dataframe`, `error`, `attempts`, `duration_seconds`, `peak_memory_mb`, `metadata`.

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
timeseriesflow version
timeseriesflow info [--checkpoint-dir PATH]
```
