# Checkpointing

TimeSeriesFlow checkpointing lets long entity runs resume safely after interruption. A 10-hour run can restart and skip entities that already completed.

## Overview

```
CheckpointBackend (abstract)
    |
    +-- LocalCheckpoint (JSONL on disk)
    +-- SQLiteCheckpoint (future)
    +-- RedisCheckpoint (future)
    +-- S3Checkpoint (future)
```

## Quick start

```python
from pathlib import Path
from timeseriesflow import entity_flow, EntityContext
from timeseriesflow.checkpoint import LocalCheckpoint

@entity_flow(
    entity_key="device_id",
    time_key="timestamp",
    checkpoint_dir=Path("./.timeseriesflow/checkpoints"),
)
def process_device(df, ctx: EntityContext):
    return {"rows": len(df)}

result = process_device.run(df)
print(result.skipped)  # entities skipped on resume
```

Or pass a backend directly:

```python
from timeseriesflow.checkpoint import LocalCheckpoint

checkpoint = LocalCheckpoint("./.timeseriesflow/checkpoints")
```

## LocalCheckpoint storage

Layout:

```
checkpoint_dir/
    checkpoints.jsonl
```

Each line is one append-only JSON event:

```json
{"entity_id":"device-1","status":"completed","recorded_at":"2026-06-07T12:00:00+00:00","runtime_seconds":1.2,"memory_delta_mb":0.5,"attempts":1,"error_message":null,"metadata":{}}
```

## API

### CheckpointBackend methods

| Method | Description |
|--------|-------------|
| `mark_completed(entity_id, ...)` | Record success (idempotent) |
| `mark_failed(entity_id, error=..., ...)` | Record failure |
| `is_completed(entity_id)` | True when latest status is completed |
| `load_completed()` | Set of completed entity IDs |
| `load_failed()` | Set of entities whose latest status is failed |
| `summary()` | Aggregate `CheckpointSummary` |
| `should_skip(entity_id)` | True when entity should be skipped on resume |

### CheckpointSummary

| Field | Description |
|-------|-------------|
| `completed_count` | Unique completed entities |
| `failed_count` | Unique failed entities |
| `total_entries` | Total JSONL lines (including history) |
| `completed_entities` | Frozenset of completed IDs |
| `failed_entities` | Frozenset of failed IDs |

## Design properties

### Crash-safe writes

Each append calls `flush()` and `os.fsync()` so committed lines survive process crashes and power loss. A crash mid-write may produce a truncated final line, which is ignored on read.

### Append-only

Records are never updated in place. Status changes append a new line. The latest line per entity wins. This gives an audit trail and avoids rewrite corruption.

### Skip completed entities

On resume, only entities in `load_completed()` are skipped. Failed entities are retried on the next run.

### Idempotent behavior

- `mark_completed` is a no-op when the entity is already completed.
- `mark_failed` is a no-op when the entity is already completed.
- Duplicate completed marks do not create extra entries.

## Performance considerations

| Topic | Guidance |
|-------|----------|
| Write cost | One fsync per entity completion. Suitable for entity-granular batch jobs over hours. |
| Read cost | Cold start scans the full JSONL file once and caches latest state in memory. |
| Memory | In-memory index holds one entry per unique entity ID. |
| Scale limit | JSONL scan is O(total entries). For millions of entities, use a future indexed backend. |
| Long runs | At 1 entity/sec for 10 hours (~36k entities), JSONL remains practical (~few MB). |
| Batching | Per-entity fsync trades throughput for durability. Future backends may offer batch commit options. |

## Future backends

### SQLiteCheckpoint

Indexed lookups, transactional writes, compact storage. Same `CheckpointBackend` interface.

### RedisCheckpoint

Low-latency shared state for distributed workers. Useful when multiple processes claim entities.

### S3Checkpoint

Durable remote storage for cloud runs. Append via multipart or companion index object.

All future backends implement the same methods so flows and decorators require no code changes.

## Legacy compatibility

`FileCheckpointStore` and `CheckpointStore` remain available and delegate to `LocalCheckpoint`. Existing `Flow` configs using `checkpoint_dir` continue to work.

## Integration with Flow

```python
from timeseriesflow import Flow, FlowConfig
from timeseriesflow.checkpoint import LocalCheckpoint

config = FlowConfig(entity_column="sensor_id", checkpoint_dir=Path("./ckpt"))
flow = Flow(processor, config)

# Or inject a backend directly:
flow = Flow(processor, config, checkpoint=LocalCheckpoint("./ckpt"))
```

## Error handling

Checkpoint I/O errors raise `CheckpointError`. Corrupt middle lines in JSONL raise on load. Truncated final lines from crashes are tolerated.
