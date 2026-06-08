# TimeSeriesFlow v0.1.0

First public release of **TimeSeriesFlow** and **AdaptiveForecast**.

## Install

From git (PyPI publish planned for v0.2):

```bash
pip install git+https://github.com/baban9/timeseriesflow.git@v0.1.0
```

Development install:

```bash
git clone https://github.com/baban9/timeseriesflow.git
cd timeseriesflow
git checkout v0.1.0
pip install -e ".[dev]"
```

Requires **Python 3.10+**.

## Quick start

```python
from timeseriesflow import EntityContext, entity_flow

@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df, ctx: EntityContext) -> dict[str, object]:
    return {"device_id": ctx.entity_id, "rows": len(df)}

result = process_device.run(df)
print(result.outputs)
```

Production pipeline:

```bash
tsflow run examples/basic_pipeline.py
```

## Highlights

- **TimeSeriesFlow**: `@entity_flow`, `EntityRunner`, checkpoints, `tsflow` CLI
- **AdaptiveForecast**: profile-aware architecture selection (7 recipes)
- **Combined workflow**: per-entity profiling in `examples/advise_and_process.py`
- **Golden path docs**: recommended API for new projects

## Documentation

- [Golden path (recommended API)](https://github.com/baban9/timeseriesflow/blob/v0.1.0/docs/golden_path.md)
- [Combined workflow (TS + AdaptiveForecast)](https://github.com/baban9/timeseriesflow/blob/v0.1.0/docs/combined_workflow.md)
- [AdaptiveForecast intro](https://github.com/baban9/timeseriesflow/blob/v0.1.0/docs/adaptiveforecast.md)
- [CHANGELOG](https://github.com/baban9/timeseriesflow/blob/v0.1.0/CHANGELOG.md)

## Full changelog

See [CHANGELOG.md](https://github.com/baban9/timeseriesflow/blob/v0.1.0/CHANGELOG.md#010---2026-06-08).
