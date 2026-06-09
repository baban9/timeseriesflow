# Sparse time series

Many real sensors report irregularly: gaps, burst uploads, and missing calendar days.
TimeSeriesFlow and AdaptiveForecast v0.2 add calendar-aware profiling and grid alignment
so you can route models per entity without pretending every bucket was observed.

## Layer 1: sparse-aware profiling (AdaptiveForecast)

Pass an expected sampling grid to `ProfileAnalyzer` or `ProfileAwareArchitectureSelection`:

```python
from adaptiveforecast import ProfileAnalyzer, ValidationGate

analyzer = ProfileAnalyzer(
    time_column="timestamp",
    value_column="value",
    expected_freq="1h",  # or infer_freq=True
)
report = analyzer.analyze(df)
print(report.coverage_ratio, report.max_gap_seconds, report.span_days)
```

New profile fields:

| Field | Meaning |
|-------|---------|
| `coverage_ratio` | Share of grid slots with at least one reading |
| `max_gap_seconds` | Longest gap between consecutive timestamps |
| `observation_density` | Readings per calendar day across the span |
| `span_days` | Calendar span from first to last timestamp |
| `expected_freq` | Grid used for coverage (when set or inferred) |

`ValidationGate` accepts optional sparse thresholds:

```python
gate = ValidationGate(
    min_coverage_ratio=0.20,
    max_gap_seconds=14 * 86_400,
    max_missing_rate=0.85,
)
```

When coverage is very low, `ModelAdvisor` may return `insufficient_data` instead of deep models.

## Layer 2: entity preprocessing (TimeSeriesFlow)

Inside `@entity_flow`, align each entity to the same grid before profiling:

```python
from timeseriesflow.preprocess import align_entity_to_grid

grid = align_entity_to_grid(
    df,
    time_column=ctx.time_key,
    value_column="temperature",
    freq="1h",
)
aligned = grid.frame  # includes was_observed
```

`was_observed` is True when at least one raw reading fell in that bucket.

See `examples/sparse_device_profile.py` for a full per-device workflow.

## Recommended workflow

1. Load multi-entity data with TimeSeriesFlow sources or a DataFrame.
2. In `@entity_flow`, call `align_entity_to_grid` with your business frequency.
3. Run `ProfileAwareArchitectureSelection` with matching `expected_freq` and sparse gates.
4. Route training jobs from `best_model` and `gate_passed`.

## When not to resample

Skip grid alignment when:

- You only need row-level quality checks on raw uploads.
- The series is already regular at the target frequency.
- You model event streams where calendar grids do not apply.

For those cases, use `ProfileAnalyzer` without `expected_freq`.
