# tsflow CLI

The `tsflow` command-line interface runs and validates entity processing pipelines with Rich output and beginner-friendly error messages.

## Install

```bash
pip install timeseriesflow
tsflow --version
```

## Commands

| Command | Description |
|---------|-------------|
| `tsflow run` | Execute a pipeline script |
| `tsflow validate` | Check a pipeline without running it |
| `tsflow info` | Show environment and quick-start tips |
| `tsflow checkpoint-status` | Inspect checkpoint progress |

## Run a pipeline

```bash
tsflow run examples/basic_pipeline.py
```

With debug logging:

```bash
tsflow run examples/basic_pipeline.py --verbose
```

## Validate a pipeline

```bash
tsflow validate examples/basic_pipeline.py
```

Validation checks:

- File exists and is valid Python
- Module imports successfully
- Entry point is present (`run`, `create_runner`, `runner`, or `main`)
- Optional `validate()` hook or source schema when applicable

## Environment info

```bash
tsflow info
tsflow info --checkpoint-dir ./checkpoints
```

## Checkpoint status

```bash
tsflow checkpoint-status --checkpoint-dir ./checkpoints
tsflow checkpoint-status --checkpoint-dir ./checkpoints --show-entities
```

## Writing a pipeline script

Pipelines are plain Python files. Define at least one entry point:

```python
from timeseriesflow import EntityRunner, entity_flow, EntityContext
from timeseriesflow.sources import CSVSource
from timeseriesflow.checkpoint import LocalCheckpoint

@entity_flow(entity_key="device_id", time_key="timestamp")
def process_device(df, ctx: EntityContext):
    return {"rows": len(df)}

def create_runner() -> EntityRunner:
    return EntityRunner(
        source=CSVSource("data.csv", parse_dates=["timestamp"]),
        flow=process_device,
        checkpoint=LocalCheckpoint("./checkpoints"),
    )

def validate() -> None:
    CSVSource("data.csv", parse_dates=["timestamp"]).validate()

def run():
    return create_runner().run()
```

Entry points (first match wins at runtime):

1. `run()` - recommended
2. `create_runner()` / `runner` - returns `EntityRunner`
3. `main()` - legacy scripts

Optional `validate()` runs during `tsflow validate`.

See `examples/basic_pipeline.py` for a complete example.

## Output

- Rich panels for run summaries
- Colored success, warning, and error messages
- Actionable hints when something fails

## Backward compatibility

The `timeseriesflow` command alias points to the same CLI as `tsflow`.
