"""Tests for Profile-Aware Architecture Selection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from adaptiveforecast import (
    SUPPORTED_RECIPES,
    ModelAdvisor,
    ProfileAnalyzer,
    ProfileAwareArchitectureSelection,
)


def _volatile_spiky_frame(points: int = 200) -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rng = np.random.default_rng(7)
    rows = []
    value = 0.0
    for i in range(points):
        jump = float(rng.normal(0, 3.0))
        if i % 15 == 0:
            jump += 20.0
        value += jump
        rows.append({"timestamp": base + timedelta(hours=i), "value": value})
    return pd.DataFrame(rows)


def _stable_frame(points: int = 40) -> pd.DataFrame:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = [
        {"timestamp": base + timedelta(hours=i), "value": 1.0 + 0.01 * i}
        for i in range(points)
    ]
    return pd.DataFrame(rows)


def test_recommend_returns_explainable_output() -> None:
    df = _volatile_spiky_frame()
    profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor(max_models=2).recommend(profile)

    payload = recommendation.to_dict()
    assert "recommended_models" in payload
    assert "reason" in payload
    assert "reasons" in payload
    assert payload["recommended_models"]
    assert payload["reason"]
    for model in payload["recommended_models"]:
        assert model in payload["reasons"]


def test_volatile_spiky_series_recommends_deep_models() -> None:
    df = _volatile_spiky_frame()
    profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor(max_models=3).recommend(profile)

    models = set(recommendation.recommended_models)
    deep_models = {"cnn_lstm", "residual_lstm", "lstm", "gru"}
    assert models & deep_models
    reason = recommendation.reason.lower()
    assert "spike" in reason or "volatility" in reason or "temporal" in reason


def test_recommendations_are_deterministic() -> None:
    df = _volatile_spiky_frame()
    profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    first = ModelAdvisor(max_models=3).recommend(profile)
    second = ModelAdvisor(max_models=3).recommend(profile)
    assert first.recommended_models == second.recommended_models
    assert first.reason == second.reason
    assert first.best_model == second.best_model


def test_only_supported_recipes_recommended() -> None:
    df = _volatile_spiky_frame()
    profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor(max_models=5).recommend(profile)
    for model in recommendation.recommended_models:
        assert model in SUPPORTED_RECIPES


def test_best_model_is_first_recommendation() -> None:
    df = _stable_frame(points=80)
    profile = ProfileAnalyzer(time_column="timestamp", value_column="value").analyze(df)
    recommendation = ModelAdvisor(max_models=3).recommend(profile)
    if recommendation.recommended_models:
        assert recommendation.best_model == recommendation.recommended_models[0]


def test_profile_aware_selection_workflow() -> None:
    df = _volatile_spiky_frame()
    selector = ProfileAwareArchitectureSelection(
        time_column="timestamp",
        value_column="value",
        max_models=2,
    )
    result = selector.select(df)

    assert result.gate_passed is True
    assert result.best_model is not None
    assert result.recommendation.recommended_models


def test_workflow_blocks_when_gate_fails() -> None:
    df = _stable_frame(points=5)
    selector = ProfileAwareArchitectureSelection(
        time_column="timestamp",
        value_column="value",
        max_models=2,
    )
    result = selector.select(df)

    assert result.gate_passed is False
    assert result.recommendation.recommended_models == ()
    assert result.gate_failures


def test_selection_result_to_dict_includes_gate_status() -> None:
    df = _volatile_spiky_frame()
    result = ProfileAwareArchitectureSelection(
        time_column="timestamp",
        value_column="value",
    ).select(df)
    payload = result.to_dict()
    assert payload["gate_passed"] is True
    assert "profile" in payload
