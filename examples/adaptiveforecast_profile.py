"""AdaptiveForecast profiling and architecture recommendation example."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from adaptiveforecast import ModelAdvisor, ProfileAnalyzer, ValidationGate


def build_seasonal_series(points: int = 120) -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(points):
        rows.append(
            {
                "timestamp": base + timedelta(hours=i),
                "value": 10.0 + 3.0 * np.sin(i / 12.0) + 0.01 * i,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    df = build_seasonal_series()
    analyzer = ProfileAnalyzer(time_column="timestamp", value_column="value")
    report = analyzer.analyze(df, metadata={"source": "synthetic_seasonal"})

    print("Profile report:")
    for key, value in report.to_dict().items():
        if key != "metadata":
            print(f"  {key}: {value}")

    gate = ValidationGate(min_rows=30)
    gate_result = gate.validate(report)
    print(f"\nValidation gate passed: {gate_result.passed}")

    if gate_result.passed:
        recommendation = ModelAdvisor(max_models=3).recommend(report)
        print("\nArchitecture recommendation:")
        print(recommendation.to_dict())


if __name__ == "__main__":
    main()
