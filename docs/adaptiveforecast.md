# AdaptiveForecast

Model-agnostic time-series profiling and Profile-Aware Architecture Selection.

AdaptiveForecast analyzes univariate series characteristics and recommends explainable forecasting architectures. It does **not** train models or generate model code.

## Flagship feature

**Profile-Aware Architecture Selection** runs the full workflow from raw series to a ranked best model recommendation. See [architecture_selection.md](architecture_selection.md).

```python
from adaptiveforecast import ProfileAwareArchitectureSelection

result = ProfileAwareArchitectureSelection(
    time_column="timestamp",
    value_column="value",
).select(df)

print(result.recommendation.to_dict())
```

## Quick start

```python
from adaptiveforecast import ProfileAnalyzer, ModelAdvisor, ValidationGate

report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)

if ValidationGate(min_rows=30).validate(report).passed:
    recommendation = ModelAdvisor(max_models=3).recommend(report)
    print(recommendation.to_dict())
```

## Supported recipes

`naive`, `moving_average`, `exponential_smoothing`, `lstm`, `gru`, `residual_lstm`, `cnn_lstm`

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
| `ProfileAwareArchitectureSelection` | Full flagship workflow |
| `ArchitectureRecommendation` | Explainable output payload |
| `ModelRecipe` | Metadata-only recipe |

## Examples

```bash
python examples/adaptiveforecast_profile.py
python examples/architecture_selection.py
```

## Design principles

- Model-agnostic: no sklearn, statsmodels, or torch dependency
- Deterministic rule-based recommendations (no LLM)
- No dynamic code generation
- Complements TimeSeriesFlow entity processing
