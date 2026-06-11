# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-06-09

### Fixed

- PyPI wheel now includes the `adaptiveforecast` package (was missing in 0.2.0)

## [0.2.0] - 2026-06-08

### Added

- **Sparse time series support** (AdaptiveForecast + TimeSeriesFlow)
  - Calendar-aware profile fields: `coverage_ratio`, `max_gap_seconds`, `observation_density`, `span_days`, `expected_freq`
  - `ProfileAnalyzer` options: `expected_freq`, `infer_freq`, `grid_agg`
  - `ValidationGate` sparse thresholds: `min_coverage_ratio`, `max_gap_seconds`
  - `insufficient_data` recipe for very sparse series
  - `resample_to_grid`, `infer_median_freq`, `SparseGridResult` in `adaptiveforecast.preprocess`
  - `timeseriesflow.preprocess.align_entity_to_grid` with `was_observed` flag
  - `examples/sparse_device_profile.py` and [docs/sparse_series.md](docs/sparse_series.md)

### Changed

- Package versions bumped to **0.2.0** (`timeseriesflow`, `adaptiveforecast`)
- Legacy `Flow` now emits a `DeprecationWarning`; prefer `@entity_flow` + `EntityRunner`
- Deep model rules require minimum `coverage_ratio` when profiling on a calendar grid

### Notes

- Recommended API: `@entity_flow` + `EntityRunner` ([Golden path](docs/golden_path.md))
- Sparse workflow: [docs/sparse_series.md](docs/sparse_series.md)

## [0.1.0] - 2026-06-08

### Added

- **TimeSeriesFlow**: entity-based time-series processing framework
  - `@entity_flow` developer API with `EntityContext`, `EntityResult`, `EntityFlow`
  - `EntityRunner` for production runs with data sources, retries, and checkpoints
  - `CSVSource`, `ParquetSource`, and `SourceSchema` data loaders
  - `LocalCheckpoint` append-only JSONL checkpoint backend
  - Memory tracking, Rich progress, structured logging
  - `tsflow` CLI (`run`, `validate`, `info`, `checkpoint-status`)
- **AdaptiveForecast**: profile-driven architecture selection
  - `ProfileAnalyzer`, `ModelAdvisor`, `ValidationGate`
  - `ProfileAwareArchitectureSelection` flagship workflow
  - Seven supported recipes from naive baselines to CNN-LSTM
- Combined per-entity profiling example (`examples/advise_and_process.py`)
- GitHub Actions CI (pytest, ruff, mypy, example smoke tests)
- Documentation under `docs/`

### Notes

- Recommended API: `@entity_flow` + `EntityRunner` (see [Golden path](docs/golden_path.md))
- Legacy `Flow` + `FlowConfig` remains supported; deprecation warning planned for v0.2

[0.2.1]: https://github.com/baban9/timeseriesflow/releases/tag/v0.2.1
[0.2.0]: https://github.com/baban9/timeseriesflow/releases/tag/v0.2.0
[0.1.0]: https://github.com/baban9/timeseriesflow/releases/tag/v0.1.0
