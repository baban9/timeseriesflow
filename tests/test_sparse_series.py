"""Tests for sparse profiling and entity grid alignment."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from adaptiveforecast import (
    ModelAdvisor,
    ProfileAnalyzer,
    ValidationGate,
    infer_median_freq,
    resample_to_grid,
)
from adaptiveforecast.preprocess import SparseGridResult
from timeseriesflow.preprocess import align_entity_to_grid


def _sparse_hourly_frame(observations: int = 12, span_days: int = 30) -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rng = np.random.default_rng(1)
    rows: list[dict[str, object]] = []
    cursor = base
    end = base + timedelta(days=span_days)
    while cursor < end and len(rows) < observations:
        rows.append({"timestamp": cursor, "value": float(rng.normal(10, 1))})
        cursor += timedelta(hours=int(rng.integers(6, 48)))
    return pd.DataFrame(rows)


def test_resample_to_grid_coverage() -> None:
    df = _sparse_hourly_frame(observations=10, span_days=20)
    result = resample_to_grid(
        df,
        time_column="timestamp",
        value_column="value",
        freq="1h",
    )
    assert isinstance(result, SparseGridResult)
    assert result.grid_slot_count > result.observed_slot_count
    assert 0.0 < result.coverage_ratio < 1.0


def test_profile_analyzer_sparse_metrics() -> None:
    df = _sparse_hourly_frame(observations=15, span_days=25)
    report = ProfileAnalyzer(
        time_column="timestamp",
        value_column="value",
        expected_freq="1h",
    ).analyze(df)

    assert report.expected_freq == "1h"
    assert report.coverage_ratio < 1.0
    assert report.span_days > 1.0
    assert report.max_gap_seconds >= 3_600


def test_validation_gate_min_coverage() -> None:
    df = _sparse_hourly_frame(observations=8, span_days=30)
    report = ProfileAnalyzer(
        time_column="timestamp",
        value_column="value",
        expected_freq="1h",
    ).analyze(df)
    sparse_gate = dict(min_rows=5, max_missing_rate=0.99)
    strict = ValidationGate(min_coverage_ratio=0.50, **sparse_gate).validate(report)
    relaxed = ValidationGate(
        min_coverage_ratio=0.03,
        max_sampling_irregularity=1.0,
        **sparse_gate,
    ).validate(report)
    assert strict.passed is False
    assert any(check.name == "min_coverage_ratio" for check in strict.failures)
    coverage_check = next(
        check for check in relaxed.checks if check.name == "min_coverage_ratio"
    )
    assert coverage_check.passed is True


def test_model_advisor_insufficient_data_on_sparse_series() -> None:
    df = _sparse_hourly_frame(observations=6, span_days=40)
    report = ProfileAnalyzer(
        time_column="timestamp",
        value_column="value",
        expected_freq="1h",
    ).analyze(df)
    recommendation = ModelAdvisor().recommend(report)
    assert recommendation.recommended_models
    assert recommendation.recommended_models[0] == "insufficient_data"


def test_infer_median_freq_hourly() -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    times = [base + timedelta(hours=i) for i in range(5)]
    freq = infer_median_freq(pd.Series(times))
    assert freq is not None
    assert "h" in freq.lower()


def test_align_entity_to_grid_adds_observed_flag() -> None:
    df = _sparse_hourly_frame(observations=8, span_days=10)
    result = align_entity_to_grid(
        df,
        time_column="timestamp",
        value_column="value",
        freq="1h",
    )
    assert "was_observed" in result.frame.columns
    assert result.frame["was_observed"].dtype == bool
    assert result.frame["was_observed"].any()
    assert (~result.frame["was_observed"]).any()


def test_profile_report_to_dict_includes_sparse_fields() -> None:
    df = _sparse_hourly_frame(observations=10, span_days=15)
    report = ProfileAnalyzer(
        time_column="timestamp",
        value_column="value",
        expected_freq="1h",
    ).analyze(df)
    payload = report.to_dict()
    assert payload["coverage_ratio"] < 1.0
    assert payload["expected_freq"] == "1h"
