"""Supported forecasting architecture identifiers."""

from __future__ import annotations

SUPPORTED_RECIPES: tuple[str, ...] = (
    "insufficient_data",
    "naive",
    "moving_average",
    "exponential_smoothing",
    "lstm",
    "gru",
    "residual_lstm",
    "cnn_lstm",
)

BASELINE_RECIPES: frozenset[str] = frozenset({"naive", "moving_average"})
STATISTICAL_RECIPES: frozenset[str] = frozenset({"exponential_smoothing"})
DEEP_RECIPES: frozenset[str] = frozenset({"lstm", "gru", "residual_lstm", "cnn_lstm"})
