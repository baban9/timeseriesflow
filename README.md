# TimeSeriesFlow

Entity-based time-series processing for Python, plus **AdaptiveForecast** for profile-driven model architecture selection. Write one function per entity; the framework handles grouping, retries, checkpointing, progress, memory tracking, and logging.

## Why TimeSeriesFlow

Most time-series pipelines repeat the same boilerplate:

- Split a large dataframe by entity (`sensor_id`, `device_id`, `customer_id`, ...)
- Process each entity in isolation
- Retry transient failures
- Resume after crashes
- Track progress and memory

TimeSeriesFlow is a focused framework for that pattern. It is not an orchestration platform or general pandas utility package.

**AdaptiveForecast** ships in the same install. It profiles univariate series and recommends explainable forecasting architectures (baseline, statistical, and deep learning recipes). It does not train models or generate model code.

## Install

```bash
pip install timeseriesflow
```

Development install:

```bash
pip install -e ".[dev]"
```

## CLI

```bash
tsflow run examples/basic_pipeline.py
tsflow validate examples/basic_pipeline.py
tsflow info
tsflow checkpoint-status --checkpoint-dir ./checkpoints
```

See [CLI documentation](docs/cli.md).

## Quick start (golden path)

Recommended API: `@entity_flow` for per-entity logic, `EntityRunner` for production runs.

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

Production pipeline with CLI:

```bash
tsflow run examples/basic_pipeline.py
```

Combined profiling + entity processing:

```bash
python examples/advise_and_process.py
```

See [Golden path](docs/golden_path.md) and [Combined workflow](docs/combined_workflow.md).

> **Legacy API:** `Flow` + `FlowConfig` still works for existing code. New projects should use `@entity_flow`. Deprecation warning planned for v0.2.

## AdaptiveForecast quick start

Profile a seasonal series and get ranked model recommendations:

```python
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from adaptiveforecast import ProfileAnalyzer, ModelAdvisor, ValidationGate

# Synthetic hourly series with trend + seasonality
base = datetime(2024, 1, 1, tzinfo=timezone.utc)
df = pd.DataFrame(
    {
        "timestamp": [base + timedelta(hours=i) for i in range(120)],
        "value": [10.0 + 3.0 * np.sin(i / 12.0) + 0.01 * i for i in range(120)],
    }
)

report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
gate = ValidationGate(min_rows=30).validate(report)
recommendation = ModelAdvisor(max_models=3).recommend(report)

print(f"seasonality_strength={report.seasonality_strength:.2f}")
print(f"gate_passed={gate.passed}")
print(f"best_model={recommendation.best_model}")
print(recommendation.to_dict())
```

**Expected output:**

```
seasonality_strength=0.82
gate_passed=True
best_model=moving_average
{'recommended_models': ['moving_average', 'exponential_smoothing', 'gru'],
 'reason': 'Low volatility and few spikes suit a smoothed baseline. Also consider: trend or seasonality present with moderate volatility.',
 'reasons': {'moving_average': 'Low volatility and few spikes suit a smoothed baseline.',
             'exponential_smoothing': 'Trend or seasonality present with moderate volatility.',
             'gru': 'Medium-length series with patterns suitable for a lighter recurrent model.'},
 'best_model': 'moving_average'}
```

For the full profile-to-selection workflow:

```python
from adaptiveforecast import ProfileAwareArchitectureSelection

result = ProfileAwareArchitectureSelection(
    time_column="timestamp",
    value_column="value",
    max_models=3,
).select(df)

print(result.best_model)          # moving_average
print(result.gate_passed)         # True
print(result.recommendation.to_dict())
```

Run the bundled examples:

```bash
python examples/adaptiveforecast_profile.py
python examples/architecture_selection.py
```

Supported recipes: `naive`, `moving_average`, `exponential_smoothing`, `lstm`, `gru`, `residual_lstm`, `cnn_lstm`.

See [AdaptiveForecast docs](docs/adaptiveforecast.md) and [architecture selection](docs/architecture_selection.md).

## Core concepts

| Concept | Description |
|---------|-------------|
| Entity | A logical unit of time-series data (sensor, device, customer, etc.) |
| `@entity_flow` | Decorator that defines per-entity processing logic |
| `EntityRunner` | Production orchestrator: sources, retries, checkpoints, CLI |
| `EntityContext` | Per-entity metadata: entity id, column names, logger |
| `Flow` (legacy) | Older orchestrator; use `@entity_flow` for new code |

### AdaptiveForecast concepts

| Concept | Description |
|---------|-------------|
| ProfileAnalyzer | Computes volatility, trend, seasonality, and data quality metrics |
| ProfileReport | Structured profile result for one series |
| ModelAdvisor | Deterministic rules that map a profile to candidate models |
| ValidationGate | Threshold checks before recommending architectures |
| ProfileAwareArchitectureSelection | End-to-end workflow from dataframe to best model pick |

## Features

### TimeSeriesFlow

- **Entity grouping**: automatic split and combine by entity column
- **Retries**: exponential backoff with configurable exception types
- **Checkpointing**: file-based resume via `FileCheckpointStore`
- **Progress**: Rich progress bar with per-entity status
- **Memory tracking**: peak RSS per run via psutil
- **Logging**: structured console logging
- **CLI**: `tsflow --version`, `tsflow info`

### AdaptiveForecast

- **Series profiling**: volatility, trend, seasonality, outliers, spikes, sampling quality
- **Architecture selection**: explainable, deterministic model recommendations
- **Validation gate**: skip or flag series that fail minimum data checks
- **Seven recipes**: from naive baselines to CNN-LSTM for volatile series

## Project layout

```
time-series-flow/
├── src/timeseriesflow/    # entity processing framework
├── src/adaptiveforecast/  # profiling and architecture selection
├── tests/                 # pytest suite
├── examples/              # runnable examples
├── docs/                  # architecture and API docs
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## Documentation

- [Golden path (recommended API)](docs/golden_path.md)
- [Combined workflow (TS + AdaptiveForecast)](docs/combined_workflow.md)
- [Getting started](docs/getting_started.md)
- [Data sources](docs/sources.md)
- [Checkpointing](docs/checkpointing.md)
- [EntityRunner](docs/runner.md)
- [Memory tracking](docs/memory.md)
- [CLI (tsflow)](docs/cli.md)
- [AdaptiveForecast](docs/adaptiveforecast.md)
- [Profile-Aware Architecture Selection](docs/architecture_selection.md)
- [Architecture](docs/architecture.md)
- [Public API](docs/api.md)
- [Implementation plan](docs/implementation_plan.md)

## Development

```bash
pytest
ruff check src tests examples
mypy src
```

## License

MIT. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
