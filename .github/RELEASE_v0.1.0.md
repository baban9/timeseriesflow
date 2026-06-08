# TimeSeriesFlow v0.1.0

First public release of TimeSeriesFlow and AdaptiveForecast.

## Install

```bash
pip install timeseriesflow
```

Development install:

```bash
git clone https://github.com/baban9/timeseriesflow.git
cd timeseriesflow
pip install -e ".[dev]"
```

## Quick start

```python
from timeseriesflow import EntityContext, entity_flow

@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df, ctx: EntityContext) -> dict[str, object]:
    return {"device_id": ctx.entity_id, "rows": len(df)}

result = process_device.run(df)
```

## Highlights

- **TimeSeriesFlow**: `@entity_flow`, `EntityRunner`, checkpoints, `tsflow` CLI
- **AdaptiveForecast**: profile-aware architecture selection (7 recipes)
- **Combined workflow**: per-entity profiling example at `examples/advise_and_process.py`

## Documentation

- [Golden path](https://github.com/baban9/timeseriesflow/blob/main/docs/golden_path.md)
- [Combined workflow](https://github.com/baban9/timeseriesflow/blob/main/docs/combined_workflow.md)
- [CHANGELOG](https://github.com/baban9/timeseriesflow/blob/main/CHANGELOG.md)

## Full changelog

See [CHANGELOG.md](https://github.com/baban9/timeseriesflow/blob/main/CHANGELOG.md#010---2026-06-08).
