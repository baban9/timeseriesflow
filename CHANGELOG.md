# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/baban9/timeseriesflow/releases/tag/v0.1.0
