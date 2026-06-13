# Open-data evaluation

This guide explains how to test whether TimeSeriesFlow and AdaptiveForecast add practical value on real public sensor data.

## Goal

Answer three questions with evidence:

1. **Throughput**: Does `EntityRunner(workers=N)` process many entities faster?
2. **Routing**: Do entities receive different model recommendations, or would one global default suffice?
3. **Screening**: Do quality gates block entities that should not proceed to training unchanged?

## Primary dataset: Intel Berkeley Research Lab

| Property | Value |
|----------|-------|
| Source | [MIT CSAIL labdata](https://db.csail.mit.edu/labdata/labdata.html) |
| Entities | 54 wireless sensor motes |
| Rows | ~2.3 million readings |
| Signals | Temperature, humidity, light, voltage |
| Sampling | ~31 seconds, irregular gaps |

This dataset matches the framework sweet spot: many entities, real gaps, mixed signal quality.

## Other datasets to try later

| Dataset | Entities | Why |
|---------|----------|-----|
| [Building Data Genome 2](https://github.com/buds-lab/building-data-genome-project-2) | 3,000+ meters | Energy forecasting at scale |
| [ETT (Zhou et al.)](https://github.com/zhouhaoyi/ETDataset) | Multivariate channels | Regular hourly industrial data |
| [Open Power System (TAMU)](https://github.com/tamu-engineering-research/Open-source-power-dataset) | Zonal grid areas | Decarbonized grid forecasting |

## Run the evaluation

From the repo root:

```bash
python examples/open_data_evaluation.py
```

Quick offline run (bundled fixture, no download):

```bash
python examples/open_data_evaluation.py --dataset fixture --workers 1 2
```

Subset for faster iteration:

```bash
python examples/open_data_evaluation.py --max-entities 20 --max-rows-per-entity 5000
```

Outputs:

- `.evaluation_reports/open_data_report.json`
- `.evaluation_reports/open_data_report.txt`

## What the report contains

### Performance

Lightweight per-entity processing at `workers=1` vs `workers=N`. Reports entities/sec and speedup.

### Routing

Full AdaptiveForecast profiling per mote:

- Gate pass rate
- Model distribution (`naive`, `moving_average`, `lstm`, `insufficient_data`, ...)
- Share of entities that differ from the modal recommendation
- Mean `coverage_ratio` on inferred calendar grids

### Verdict

Heuristic summary of when the stack is useful on the slice you ran.

## How to read results

**Framework is likely useful when:**

- 3+ distinct model families are assigned across entities
- 25%+ of entities differ from the most common recommendation
- Gates block a meaningful share of low-quality entities
- Parallel workers give 1.5x+ speedup on profiling-heavy flows

**Framework adds less when:**

- All entities map to the same model
- All entities pass gates with similar profiles
- Per-entity work is tiny and parallel speedup is flat

## Interpreting for product decisions

| Finding | Implication |
|---------|-------------|
| High routing diversity | Per-entity model routing is justified |
| Low routing diversity | Focus on batch processing and gates, not routing |
| Low gate pass rate | Screening saves wasted training jobs |
| High gate pass rate | Advisor is informative but screening is optional |
| Strong worker speedup | Ship parallel `EntityRunner` in production paths |

## Reproduce in CI

Tests use the fixture at `examples/evaluation/fixtures/intel_sample.csv` (no network).

```bash
pytest tests/test_open_data_evaluation.py -q
```

## Suggested next datasets for a fuller study

1. Intel Berkeley (included): routing + sparse gaps
2. BDG2 subset: scale test at 500+ meters
3. ETT hourly: compare against mostly regular industrial data

Publish results as a short report in `.evaluation_reports/` and link key numbers in README or release notes when pitching the framework.
