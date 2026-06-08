# Combined workflow: TimeSeriesFlow + AdaptiveForecast

TimeSeriesFlow splits work by entity (`device_id`, `sensor_id`, etc.). AdaptiveForecast profiles each entity's series and recommends which forecasting architecture fits it best. Together they answer: **for every entity in my fleet, what model family should we train?**

This does not train models. It returns explainable recommendations you plug into your own training pipeline.

New to AdaptiveForecast? Read [What is AdaptiveForecast?](adaptiveforecast.md#what-is-adaptiveforecast).

## Pattern

```
Multi-entity dataframe
        |
        v
   @entity_flow  (one function per device/sensor/customer)
        |
        v
ProfileAwareArchitectureSelection.select(entity_df)
        |
        v
Per-entity recommendation (best_model, reasons, gate status)
```

## Example

```python
from adaptiveforecast import ProfileAwareArchitectureSelection
from timeseriesflow import EntityContext, entity_flow

@entity_flow(entity_key="device_id", time_key="timestamp")
def advise_and_process(df, ctx: EntityContext) -> dict[str, object]:
    selection = ProfileAwareArchitectureSelection(
        time_column=ctx.time_key,
        value_column="temperature",
        max_models=2,
    ).select(df)

    return {
        "device_id": ctx.entity_id,
        "best_model": selection.best_model,
        "gate_passed": selection.gate_passed,
        "recommended_models": list(selection.recommendation.recommended_models),
        "reason": selection.recommendation.reason,
    }

result = advise_and_process.run(multi_device_df)
for output in result.outputs:
    print(output)
```

## Runnable script

```bash
python examples/advise_and_process.py
```

## Production run with EntityRunner

Wrap the same decorated function in `EntityRunner` to add CSV loading, retries, and checkpoints:

```python
from timeseriesflow import EntityRunner
from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.sources import CSVSource

runner = EntityRunner(
    source=CSVSource("devices.csv", parse_dates=["timestamp"]),
    flow=advise_and_process,
    checkpoint=LocalCheckpoint("./checkpoints"),
)
summary = runner.run()
```

## Output fields

| Field | Description |
|-------|-------------|
| `best_model` | Top recommended recipe name |
| `recommended_models` | Ranked list of candidates |
| `reason` | Human-readable explanation |
| `gate_passed` | Whether the series passed validation thresholds |

See [architecture selection](architecture_selection.md) for recipe details and rule behavior.
