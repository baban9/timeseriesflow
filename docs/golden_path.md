# Golden path (recommended API)

For new projects, use this two-layer pattern:

1. **`@entity_flow`** to define per-entity processing logic
2. **`EntityRunner`** to load data, retry failures, checkpoint progress, and report stats

The legacy `Flow` + `FlowConfig` API remains available but is not recommended for new code. It emits a deprecation warning as of v0.2.

## When to use each API

| API | Use when |
|-----|----------|
| `@entity_flow` + `EntityRunner` | Production pipelines, CLI scripts, resumable batch jobs |
| `@entity_flow` + `.run(df)` | Notebooks, tests, small in-memory runs |
| `Flow` + `FlowConfig` | Maintaining existing code only (legacy) |

## Developer layer: @entity_flow

```python
from timeseriesflow import EntityContext, entity_flow

@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df, ctx: EntityContext) -> dict[str, object]:
    return {"device_id": ctx.entity_id, "rows": len(df)}
```

`entity_key` and `entity_column` are equivalent parameter names.

## Production layer: EntityRunner

```python
from timeseriesflow import EntityRunner
from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.sources import CSVSource

runner = EntityRunner(
    source=CSVSource("data.csv", parse_dates=["timestamp"]),
    flow=process_device,
    checkpoint=LocalCheckpoint("./checkpoints"),
    batch_size=100,
    retries=3,
)
summary = runner.run()
```

Or use the CLI:

```bash
tsflow run examples/basic_pipeline.py
```

## Naming aliases

The developer API and legacy API use different field names. Aliases bridge both:

| Developer API | Legacy Flow API |
|---------------|-----------------|
| `entity_key` | `entity_column` |
| `runtime_seconds` | `duration_seconds` |
| `memory_delta_mb` | `peak_memory_mb` |
| `EntityResult` | `FlowEntityResult` |

## Next steps

- [Combined workflow](combined_workflow.md): profile and recommend models per entity
- [EntityRunner](runner.md): batching, retries, checkpoints
- [CLI](cli.md): `tsflow run` and `tsflow validate`
