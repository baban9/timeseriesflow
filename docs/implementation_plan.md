# Implementation plan

## Phase 0: Foundation (v0.1.0) - COMPLETE

Goal: Ship a usable MVP with core framework guarantees.

| Task | Status |
|------|--------|
| Project scaffolding (pyproject.toml, src layout, tests) | Done |
| Type system (RunContext, EntityResult, RunSummary) | Done |
| Entity grouping (list_entities, split_by_entity) | Done |
| Flow engine with sequential execution | Done |
| RetryPolicy with exponential backoff | Done |
| FileCheckpointStore for resume | Done |
| ProgressTracker (Rich) | Done |
| MemoryTracker (psutil) | Done |
| Structured logging | Done |
| CLI (version, info) | Done |
| Unit and integration tests | Done |
| Documentation and examples | Done |

## Phase 1: Hardening (v0.2.0)

Goal: Production readiness for early adopters.

- [ ] Parallel entity execution (configurable workers)
- [ ] Per-entity timeout support
- [ ] Result validation hooks (schema checks on processor output)
- [ ] Improved checkpoint compaction (dedupe index.jsonl)
- [ ] GitHub Actions CI (test, lint, mypy, coverage)
- [ ] Pre-commit hooks configuration
- [ ] CHANGELOG and semver release workflow

## Phase 2: Extensibility (v0.3.0)

Goal: Support diverse deployment environments.

- [ ] Additional CheckpointStore backends (S3, SQLite)
- [ ] Custom progress backends (silent, JSON lines)
- [ ] Metrics export (counters, histograms)
- [ ] Plugin entry points for third-party stores
- [ ] Async processor support (optional)

## Phase 3: Scale (v1.0.0)

Goal: Stable API and performance for large workloads.

- [ ] Chunked entity iteration for out-of-core datasets
- [ ] Distributed execution adapter (Dask/Ray integration, optional extra)
- [ ] Performance benchmarks and regression suite
- [ ] API stability guarantee and migration guide

## API stability policy

- v0.x: breaking changes allowed with deprecation warnings when feasible
- v1.0+: semver for public API in `timeseriesflow.__init__`

## Testing strategy

| Layer | Coverage |
|-------|----------|
| Unit | entity, retry, checkpoint, memory, progress |
| Integration | full Flow runs with checkpoint resume |
| Future | property-based tests for entity splitting edge cases |

## Non-goals (explicit)

- Time-series forecasting or ML model training
- Workflow DAG orchestration
- Replacement for pandas/numpy operations
- Real-time streaming (Kafka, Flink); batch-first design
