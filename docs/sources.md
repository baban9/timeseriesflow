# Data sources

TimeSeriesFlow provides a data source abstraction for loading tabular time-series data before entity processing.

## Overview

```
BaseSource (abstract)
    |
    TabularSource (abstract, returns DataFrame)
    |
    +-- FileSource (abstract, filesystem-backed)
    |       |
    |       +-- CSVSource
    |       +-- ParquetSource
    |
    +-- MongoSource (future, extends TabularSource directly)
```

File-based sources share path handling, file existence checks, and column peeking. Document stores such as MongoDB will extend `TabularSource` without inheriting from `FileSource`, so the public API stays stable when new backends are added.

## Quick start

```python
from timeseriesflow.sources import CSVSource, SourceSchema

schema = SourceSchema(required_columns=("sensor_id", "timestamp", "value"))
source = CSVSource(
    "data/sensors.csv",
    parse_dates=["timestamp"],
    selected_columns=["sensor_id", "timestamp", "value"],
    schema=schema,
)

source.validate()
df = source.load()
```

## CSVSource

| Parameter | Description |
|-----------|-------------|
| `path` | Path to the CSV file |
| `parse_dates` | Columns parsed as datetimes (passed to pandas) |
| `selected_columns` | Subset of columns to load |
| `schema` | Optional `SourceSchema` for validation |
| `lazy` | When True, skip in-memory caching after load |

```python
from timeseriesflow.sources import CSVSource, SourceSchema

source = CSVSource(
    "readings.csv",
    parse_dates=["timestamp"],
    selected_columns=["device_id", "timestamp", "value"],
    schema=SourceSchema(required_columns=("device_id", "timestamp", "value")),
)
```

## ParquetSource

| Parameter | Description |
|-----------|-------------|
| `path` | Path to the Parquet file |
| `selected_columns` | Subset of columns to load |
| `schema` | Optional `SourceSchema` for validation |
| `lazy` | When True, skip in-memory caching after load |

Requires `pyarrow` or `fastparquet`:

```bash
pip install timeseriesflow[parquet]
```

```python
from timeseriesflow.sources import ParquetSource, SourceSchema

source = ParquetSource(
    "readings.parquet",
    selected_columns=["device_id", "timestamp", "value"],
    schema=SourceSchema(required_columns=("device_id", "timestamp", "value")),
)
```

## SourceSchema

Define required and optional columns for validation:

```python
from timeseriesflow.sources import SourceSchema

schema = SourceSchema(
    required_columns=("sensor_id", "timestamp", "value"),
    optional_columns=("quality",),
)
```

Validation runs during `validate()` (column peek) and `load()` (full dataframe).

## Methods

### validate()

Checks configuration and schema without loading the full dataset where possible:

- File existence for `CSVSource` and `ParquetSource`
- Selected columns exist in the source
- Required schema columns are present

### load()

Reads data into a pandas DataFrame, validates schema, and optionally caches the result.

### clear_cache()

Clears an in-memory cached dataframe. Useful when `lazy=False`.

### is_loaded

Property indicating whether data is currently cached.

## Error types

| Exception | When raised |
|-----------|-------------|
| `SourceNotFoundError` | File path does not exist |
| `SourceSchemaError` | Missing required or selected columns |
| `SourceLoadError` | Read failure or missing parquet engine |

All source errors inherit from `SourceError`, which inherits from `FlowError`.

## Lazy loading

Set `lazy=True` to load data without caching it in memory. Future versions may extend this with chunked and deferred loading APIs while keeping `validate()` and `load()` stable.

## Future: MongoSource

The intended extension point:

```python
class MongoSource(TabularSource):
    source_name = "MongoSource"

    def __init__(
        self,
        uri: str,
        database: str,
        collection: str,
        *,
        selected_columns: list[str] | None = None,
        schema: SourceSchema | None = None,
        lazy: bool = False,
    ) -> None:
        ...

    def validate(self) -> None:
        # connectivity + collection existence + schema peek
        ...

    def _read_dataframe(self) -> pd.DataFrame:
        # query collection into a DataFrame
        ...
```

Because `MongoSource` extends `TabularSource` rather than `FileSource`, it reuses schema validation, caching, and the `load()` contract without filesystem assumptions.

## Integration with entity flows

```python
from timeseriesflow import entity_flow, EntityContext
from timeseriesflow.sources import CSVSource, SourceSchema

schema = SourceSchema(required_columns=("device_id", "timestamp", "temperature"))

@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df, ctx: EntityContext):
    return {"rows": len(df)}

source = CSVSource("devices.csv", parse_dates=["timestamp"], schema=schema)
source.validate()
result = process_device.run(source.load())
```

See `examples/sources_usage.py` for a runnable script.
