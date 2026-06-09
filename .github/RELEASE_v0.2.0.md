# TimeSeriesFlow v0.2.0

Sparse time series profiling, entity grid alignment, and v0.2 release polish.

## Install

From git:

```bash
pip install git+https://github.com/baban9/timeseriesflow.git@v0.2.0
```

Development:

```bash
git clone https://github.com/baban9/timeseriesflow.git
cd timeseriesflow
git checkout v0.2.0
pip install -e ".[dev]"
```

## Highlights

- **Sparse profiling**: `coverage_ratio`, gap metrics, and calendar-grid alignment via `expected_freq`
- **Entity preprocessing**: `align_entity_to_grid` adds `was_observed` for per-bucket coverage
- **`insufficient_data` recipe**: routes very sparse entities before deep model suggestions
- **`Flow` deprecation warning**: use `@entity_flow` + `EntityRunner` for new projects

## Examples

```bash
python examples/sparse_device_profile.py
python examples/advise_and_process.py
```

## Documentation

- [Sparse time series](https://github.com/baban9/timeseriesflow/blob/v0.2.0/docs/sparse_series.md)
- [Golden path](https://github.com/baban9/timeseriesflow/blob/v0.2.0/docs/golden_path.md)
- [Combined workflow](https://github.com/baban9/timeseriesflow/blob/v0.2.0/docs/combined_workflow.md)
- [CHANGELOG](https://github.com/baban9/timeseriesflow/blob/v0.2.0/CHANGELOG.md)

## Full changelog

See [CHANGELOG.md](https://github.com/baban9/timeseriesflow/blob/v0.2.0/CHANGELOG.md#020---2026-06-08).
