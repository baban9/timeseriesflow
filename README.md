# TimeSeriesFlow

Entity-based time-series processing for Python. Write one function per entity; the framework handles grouping, retries, checkpointing, progress, memory tracking, and logging.

## Why TimeSeriesFlow

Most time-series pipelines repeat the same boilerplate:

- Split a large dataframe by entity (`sensor_id`, `device_id`, `customer_id`, ...)
- Process each entity in isolation
- Retry transient failures
- Resume after crashes
- Track progress and memory

TimeSeriesFlow is a focused framework for that pattern. It is not a forecasting library, orchestration platform, or general pandas utility package.

## Install

```bash
pip install timeseriesflow
```

Development install:

```bash
pip install -e ".[dev]"
```

## Quick start

```python
import pandas as pd
from timeseriesflow import Flow, FlowConfig, entity_processor

@entity_processor
def process_entity(df: pd.DataFrame, context) -> pd.DataFrame:
    out = df.copy()
    out["rolling_mean"] = out["value"].rolling(5).mean()
    return out

config = FlowConfig(entity_column="sensor_id")
flow = Flow(process_entity, config)
output, summary = flow.run(df)

print(summary.succeeded, summary.failed)
```

## Core concepts

| Concept | Description |
|---------|-------------|
| Entity | A logical unit of time-series data (sensor, device, customer, etc.) |
| EntityProcessor | Your function: `(entity_df, context) -> entity_df` |
| Flow | Orchestrator that groups, runs, retries, and aggregates results |
| FlowConfig | Run settings: entity column, checkpoint dir, retry policy, etc. |
| RunContext | Per-entity metadata: entity id, attempt number, timestamps |

## Features

- **Entity grouping**: automatic split and combine by entity column
- **Retries**: exponential backoff with configurable exception types
- **Checkpointing**: file-based resume via `FileCheckpointStore`
- **Progress**: Rich progress bar with per-entity status
- **Memory tracking**: peak RSS per run via psutil
- **Logging**: structured console logging
- **CLI**: `timeseriesflow version`, `timeseriesflow info`

## Project layout

```
time-series-flow/
├── src/timeseriesflow/   # package source
├── tests/                # pytest suite
├── examples/             # runnable examples
├── docs/                 # architecture and API docs
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## Documentation

- [Getting started](docs/getting_started.md)
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
