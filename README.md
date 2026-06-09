# TimeSeriesFlow

[![CI](https://github.com/baban9/timeseriesflow/actions/workflows/ci.yml/badge.svg)](https://github.com/baban9/timeseriesflow/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/baban9/timeseriesflow/blob/main/LICENSE)
[![Release](https://img.shields.io/github/v/release/baban9/timeseriesflow?label=release)](https://github.com/baban9/timeseriesflow/releases)

Entity-based time-series processing for Python, plus **AdaptiveForecast** for profile-driven model architecture selection.

Write one function per entity (`sensor_id`, `device_id`, `customer_id`, ...). The framework handles grouping, retries, checkpointing, progress, memory tracking, and logging.

| Package | Role |
|---------|------|
| **timeseriesflow** | Per-entity processing, `EntityRunner`, CLI (`tsflow`), checkpoints |
| **adaptiveforecast** | Series profiling and forecasting architecture recommendations |

## What is AdaptiveForecast?

AdaptiveForecast answers one question before you train anything:

**Given this time series, which forecasting approach is worth trying first?**

It profiles volatility, trend, seasonality, gaps, spikes, and data quality, then returns ranked recommendations (`moving_average`, `exponential_smoothing`, `lstm`, ...). Rules are deterministic, not LLM-based.

| Situation | How it helps |
|-----------|--------------|
| Many sensors or devices | Pick a model family per entity, not one global default |
| Mixed data quality | `ValidationGate` flags series too short or noisy to forecast |
| Team handoffs | `reason` fields explain each recommendation |
| With TimeSeriesFlow | Profile inside `@entity_flow` ([combined workflow](docs/combined_workflow.md)) |

It does **not** train models or produce forecasts. It recommends architecture recipes only.

## Install

**v0.1.0** (from GitHub; PyPI publish planned for v0.2):

```bash
pip install git+https://github.com/baban9/timeseriesflow.git@v0.1.0
```

Development install:

```bash
git clone https://github.com/baban9/timeseriesflow.git
cd timeseriesflow
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Quick start

Recommended API: `@entity_flow` for logic, `EntityRunner` or `tsflow run` for production.

```python
import pandas as pd
from timeseriesflow import EntityContext, entity_flow

df = pd.DataFrame(
    {
        "sensor_id": ["S1", "S1", "S1", "S2", "S2", "S2"],
        "timestamp": pd.date_range("2024-01-01", periods=6, freq="h", tz="UTC"),
        "value": [1.0, 2.0, 3.0, 10.0, 11.0, 12.0],
    }
)

@entity_flow(entity_key="sensor_id", time_key="timestamp")
def process_sensor(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    return {
        "sensor_id": ctx.entity_id,
        "rows": len(df),
        "mean_value": float(df["value"].mean()),
    }

result = process_sensor.run(df)
print(f"succeeded={result.succeeded} failed={result.failed}")
print(result.outputs)
```

**Expected output:**

```
succeeded=2 failed=0
[{'sensor_id': 'S1', 'rows': 3, 'mean_value': 2.0}, {'sensor_id': 'S2', 'rows': 3, 'mean_value': 11.0}]
```

### CLI

```bash
tsflow run examples/basic_pipeline.py
tsflow validate examples/basic_pipeline.py
tsflow info
tsflow checkpoint-status --checkpoint-dir ./checkpoints
```

### AdaptiveForecast

```python
from adaptiveforecast import ProfileAwareArchitectureSelection

result = ProfileAwareArchitectureSelection(
    time_column="timestamp",
    value_column="value",
    max_models=3,
).select(df)

print(result.best_model)
print(result.recommendation.to_dict())
```

### Examples

```bash
python examples/advise_and_process.py          # TimeSeriesFlow + AdaptiveForecast
python examples/adaptiveforecast_profile.py  # profiling only
python examples/architecture_selection.py    # full selection workflow
```

> **Legacy API:** `Flow` + `FlowConfig` still works. New projects should use `@entity_flow`. Deprecation warning planned for v0.2.

## Features

**TimeSeriesFlow:** entity grouping, retries, JSONL checkpoints, Rich progress, memory tracking, `CSVSource` / `ParquetSource`, `tsflow` CLI.

**AdaptiveForecast:** series profiling, validation gate, seven recipes (`naive` through `cnn_lstm`), explainable `ModelAdvisor` rules.

## Documentation

| Topic | Link |
|-------|------|
| Golden path (recommended) | [docs/golden_path.md](docs/golden_path.md) |
| Combined TS + AdaptiveForecast | [docs/combined_workflow.md](docs/combined_workflow.md) |
| AdaptiveForecast intro | [docs/adaptiveforecast.md](docs/adaptiveforecast.md) |
| Sparse time series | [docs/sparse_series.md](docs/sparse_series.md) |
| Architecture selection | [docs/architecture_selection.md](docs/architecture_selection.md) |
| Getting started | [docs/getting_started.md](docs/getting_started.md) |
| EntityRunner | [docs/runner.md](docs/runner.md) |
| CLI | [docs/cli.md](docs/cli.md) |
| Public API | [docs/api.md](docs/api.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

## Development

```bash
pytest
ruff check src tests examples
mypy src
```

## Contributing

`main` is protected. Open a pull request with review; do not push directly to `main`.

```bash
git checkout -b feat/my-change
git push -u origin feat/my-change
gh pr create --fill
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [branch protection guide](.github/BRANCH_PROTECTION.md).

## License

MIT. See [LICENSE](LICENSE).
