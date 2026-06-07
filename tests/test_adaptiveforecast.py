"""Tests for adaptiveforecast profiling and advisory."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from adaptiveforecast import (
    ModelAdvisor,
    ProfileAnalysisError,
    ProfileAnalyzer,
    ValidationGate,
)


def _make_frame(
    values: list[float],
    *,
    timestamps: list[datetime] | None = None,
    missing_at: list[int] | None = None,
) -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    times = timestamps or [base + timedelta(hours=i) for i in range(len(values))]
    series = pd.Series(values, dtype=float)
    if missing_at:
        for index in missing_at:
            series.iloc[index] = np.nan
    return pd.DataFrame({"timestamp": times, "value": series})


def test_profile_analyzer_row_count_and_missing_rate() -> None:
    df = _make_frame([1.0, 2.0, np.nan, 4.0], missing_at=[2])
    analyzer = ProfileAnalyzer(time_column="timestamp", value_column="value")
    report = analyzer.analyze(df)

    assert report.row_count == 4
    assert report.missing_rate == pytest.approx(0.25)


def test_profile_analyzer_trend_strength() -> None:
    df = _make_frame([float(i) for i in range(50)])
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    assert report.trend_strength > 0.8


def test_profile_analyzer_seasonality_strength() -> None:
    values = [float(np.sin(i / 3.0)) for i in range(90)]
    df = _make_frame(values)
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    assert report.seasonality_strength > 0.2


def test_profile_analyzer_flatline_ratio() -> None:
    df = _make_frame([5.0] * 20)
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    assert report.flatline_ratio > 0.5


def test_profile_analyzer_spike_ratio() -> None:
    values = [0.0] * 20
    values[10] = 100.0
    df = _make_frame(values)
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    assert report.spike_ratio > 0.0


def test_profile_analyzer_sampling_irregularity() -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    times = [base, base + timedelta(hours=1), base + timedelta(hours=5)]
    df = _make_frame([1.0, 2.0, 3.0], timestamps=times)
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    assert report.sampling_irregularity > 0.0


def test_profile_report_to_dict() -> None:
    df = _make_frame([1.0, 2.0, 3.0])
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    payload = report.to_dict()
    assert set(payload) >= {
        "row_count",
        "missing_rate",
        "volatility",
        "trend_strength",
        "seasonality_strength",
        "outlier_ratio",
        "spike_ratio",
        "flatline_ratio",
        "sampling_irregularity",
    }


def test_profile_analyzer_series_input() -> None:
    series = pd.Series([1.0, 2.0, 3.0, 4.0])
    report = ProfileAnalyzer(value_column="value").analyze(series)
    assert report.row_count == 4


def test_profile_analyzer_all_missing_raises() -> None:
    df = _make_frame([np.nan, np.nan], missing_at=[0, 1])
    with pytest.raises(ProfileAnalysisError):
        ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)


def test_validation_gate_passes_clean_series() -> None:
    df = _make_frame([float(i) for i in range(40)])
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    result = ValidationGate(min_rows=30).validate(report)
    assert result.passed is True
    assert not result.failures


def test_validation_gate_fails_short_series() -> None:
    df = _make_frame([1.0, 2.0, 3.0])
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    result = ValidationGate(min_rows=10).validate(report)
    assert result.passed is False
    assert any(check.name == "min_rows" for check in result.failures)


def test_model_advisor_recommends_seasonal_recipes() -> None:
    values = [float(np.sin(i / 2.0)) for i in range(120)]
    df = _make_frame(values)
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor().recommend(report)
    assert recommendation.recommended_models
    assert "exponential_smoothing" in recommendation.recommended_models or "lstm" in recommendation.recommended_models


def test_model_advisor_recipes_are_metadata_only() -> None:
    df = _make_frame([float(i) for i in range(50)])
    report = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor().recommend(report)
    assert recommendation.candidates
    for recipe in recommendation.candidates:
        assert recipe.name
        assert recipe.family
        assert recipe.rationale
        assert isinstance(recipe.to_dict(), dict)
