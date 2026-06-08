# AdaptiveForecast

## What is AdaptiveForecast?

AdaptiveForecast is a model-agnostic profiling and recommendation layer for univariate time series. You give it a dataframe with a timestamp column and a value column. It returns a structured profile of that series and a ranked list of forecasting architectures to try.

The goal is to remove guesswork at the start of a forecasting project. Instead of defaulting every series to LSTM or every series to ARIMA, you get a data-driven starting point with plain-language reasons.

AdaptiveForecast ships inside the `timeseriesflow` package:

```bash
pip install timeseriesflow
```

```python
import adaptiveforecast
```

It has no training dependencies (no PyTorch, sklearn, or statsmodels required).

## The problem it solves

Forecasting pipelines often fail in two predictable ways:

1. **Wrong model for the data.** A stable, seasonal series does not need a deep model. A spiky, volatile series will crush a naive baseline.
2. **One model for every entity.** In multi-device or multi-sensor data, each entity can have different length, noise, and seasonality. A single global choice wastes accuracy or compute.

AdaptiveForecast profiles each series independently and recommends from a fixed catalog of seven recipes. Recommendations are explainable and repeatable: the same profile always yields the same ranking.

## When to use it

Use AdaptiveForecast when you need to:

- **Screen many series** before batch training (sensors, SKUs, customers, meters)
- **Route entities** to different model families in a downstream training pipeline
- **Document decisions** for reviewers or operators (`reason`, `reasons`, `best_model`)
- **Reject bad inputs early** with `ValidationGate` (too few rows, extreme missing rate)
- **Combine with TimeSeriesFlow** to profile inside per-entity jobs ([combined workflow](combined_workflow.md))

Do not use it when you need:

- Point forecasts or confidence intervals (use your trainer of choice after selection)
- Multivariate or hierarchical models (AdaptiveForecast is univariate today)
- Auto-tuned hyperparameters (recipes are architecture-level, not hyperparameter search)

## How it works

```
Raw series (timestamp + value)
        |
        v
  ProfileAnalyzer  -->  ProfileReport (volatility, trend, seasonality, ...)
        |
        v
  ValidationGate   -->  pass / fail (optional thresholds)
        |
        v
  ModelAdvisor     -->  ArchitectureRecommendation (ranked recipes + reasons)
```

The flagship entry point runs all three steps:

```python
from adaptiveforecast import ProfileAwareArchitectureSelection

result = ProfileAwareArchitectureSelection(
    time_column="timestamp",
    value_column="value",
).select(df)

print(result.best_model)
print(result.recommendation.to_dict())
```

See [architecture_selection.md](architecture_selection.md) for rule details and recipe catalog.

## Quick start

```python
from adaptiveforecast import ProfileAnalyzer, ModelAdvisor, ValidationGate

report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)

if ValidationGate(min_rows=30).validate(report).passed:
    recommendation = ModelAdvisor(max_models=3).recommend(report)
    print(recommendation.to_dict())
```

## Supported recipes

| Recipe | Family | Typical use |
|--------|--------|-------------|
| `naive` | baseline | Stable series, weak trend and seasonality |
| `moving_average` | baseline | Low volatility, few spikes |
| `exponential_smoothing` | statistical | Trend or seasonality, moderate noise |
| `lstm` | deep | Long history, structured temporal patterns |
| `gru` | deep | Medium length, moderate complexity |
| `residual_lstm` | deep | High volatility with outliers |
| `cnn_lstm` | deep | Frequent spikes and high volatility |

## ProfileReport metrics

| Metric | Description |
|--------|-------------|
| `row_count` | Total rows |
| `missing_rate` | Fraction of missing values |
| `volatility` | Normalized variability (0-1) |
| `trend_strength` | Linear trend strength (0-1) |
| `seasonality_strength` | Autocorrelation seasonality proxy (0-1) |
| `outlier_ratio` | IQR outlier fraction |
| `spike_ratio` | Large first-difference fraction |
| `flatline_ratio` | Repeated-value segment fraction |
| `sampling_irregularity` | Timestamp interval irregularity (0-1) |

## Components

| Class | Role |
|-------|------|
| `ProfileAnalyzer` | Compute profile metrics |
| `ProfileReport` | Structured analysis result |
| `ModelAdvisor` | Deterministic architecture recommendations |
| `ValidationGate` | Threshold checks before forecasting |
| `ProfileAwareArchitectureSelection` | Full workflow (profile, gate, advise) |
| `ArchitectureRecommendation` | Explainable output payload |
| `ModelRecipe` | Metadata-only recipe |

## Examples

```bash
python examples/adaptiveforecast_profile.py
python examples/architecture_selection.py
python examples/advise_and_process.py   # with TimeSeriesFlow per entity
```

## Design principles

- Model-agnostic: no sklearn, statsmodels, or torch dependency
- Deterministic rule-based recommendations (no LLM)
- No dynamic code generation
- Complements TimeSeriesFlow entity processing

## Related docs

- [Profile-Aware Architecture Selection](architecture_selection.md)
- [Combined workflow with TimeSeriesFlow](combined_workflow.md)
- [Golden path](golden_path.md)
