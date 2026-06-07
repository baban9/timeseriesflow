# Profile-Aware Architecture Selection

The flagship AdaptiveForecast workflow that analyzes time-series characteristics and recommends deterministic, explainable forecasting architectures.

## Workflow

```
Time Series
    |
    v
Profile Analyzer
    |
    v
Model Advisor
    |
    v
Candidate Models
    |
    v
Validation Gate
    |
    v
Best Model
```

## Quick start

```python
from adaptiveforecast import ProfileAwareArchitectureSelection

selector = ProfileAwareArchitectureSelection(
    time_column="timestamp",
    value_column="value",
    max_models=3,
)
result = selector.select(df)

print(result.recommendation.to_dict())
print(result.best_model)
```

Example output:

```json
{
  "recommended_models": ["cnn_lstm", "residual_lstm"],
  "reason": "High volatility and frequent spikes detected.",
  "reasons": {
    "cnn_lstm": "High volatility and frequent spikes detected.",
    "residual_lstm": "High volatility with outliers or spikes; residual learning helps."
  },
  "best_model": "cnn_lstm"
}
```

## Supported recipes

| Model | Family | When recommended |
|-------|--------|------------------|
| `naive` | baseline | Weak trend and seasonality, stable series |
| `moving_average` | baseline | Low volatility, few spikes |
| `exponential_smoothing` | statistical | Trend or seasonality with moderate volatility |
| `lstm` | deep | Long history with structured temporal patterns |
| `gru` | deep | Medium-length series with moderate complexity |
| `residual_lstm` | deep | High volatility with outliers or spikes |
| `cnn_lstm` | deep | High volatility and frequent spikes |

## ModelAdvisor.recommend(profile)

Returns an ``ArchitectureRecommendation`` with:

| Field | Description |
|-------|-------------|
| `recommended_models` | Ranked model names (deterministic) |
| `reason` | Summary explanation |
| `reasons` | Per-model explanation map |
| `best_model` | Top recommendation |
| `candidates` | Full ``ModelRecipe`` metadata |

```python
from adaptiveforecast import ProfileAnalyzer, ModelAdvisor

profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
recommendation = ModelAdvisor(max_models=2).recommend(profile)
```

## Design principles

- **Explainable**: every recommendation includes human-readable reasons
- **Deterministic**: same profile always yields the same ranking
- **No LLM**: rule-based logic in ``rules.py``
- **No model code**: metadata and configuration hints only
- **Model-agnostic**: no training or inference in this module

## Validation gate

The workflow runs ``ValidationGate`` before recommending architectures. If the gate fails, no models are recommended and ``gate_failures`` lists failed checks.

Override thresholds:

```python
from adaptiveforecast import ValidationGate, ProfileAwareArchitectureSelection

selector = ProfileAwareArchitectureSelection(
    gate=ValidationGate(min_rows=50, max_missing_rate=0.10),
    time_column="timestamp",
    value_column="value",
)
```

## Example script

```bash
python examples/architecture_selection.py
```

## Rule customization

Rules live in ``adaptiveforecast/rules.py``. Each rule maps profile thresholds to a supported recipe with a fixed priority for deterministic ordering.
