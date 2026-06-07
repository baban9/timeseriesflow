"""Profile-Aware Architecture Selection example."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from adaptiveforecast import ModelAdvisor, ProfileAnalyzer, ProfileAwareArchitectureSelection


def build_volatile_spiky_series(points: int = 200) -> pd.DataFrame:
    """Synthetic series with high volatility and frequent spikes."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rng = np.random.default_rng(42)
    rows = []
    value = 0.0
    for i in range(points):
        shock = float(rng.normal(0, 2.5))
        if i % 17 == 0:
            shock += 15.0
        value += shock
        rows.append({"timestamp": base + timedelta(hours=i), "value": value})
    return pd.DataFrame(rows)


def main() -> None:
    df = build_volatile_spiky_series()
    selector = ProfileAwareArchitectureSelection(
        time_column="timestamp",
        value_column="value",
        max_models=3,
    )
    result = selector.select(df)

    print("Profile-Aware Architecture Selection")
    print(json.dumps(result.recommendation.to_dict(), indent=2))
    print(f"\nBest model: {result.best_model}")
    print(f"Gate passed: {result.gate_passed}")

    # Direct advisor usage
    profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor(max_models=2).recommend(profile)
    print("\nDirect advisor output:")
    print(json.dumps(recommendation.to_dict(), indent=2))


if __name__ == "__main__":
    main()
