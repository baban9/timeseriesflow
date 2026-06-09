"""Calendar and gap metrics for sparse time series."""

from __future__ import annotations

import pandas as pd


def calendar_metrics(timestamps: pd.Series) -> tuple[float, float, float]:
    """Return span_days, max_gap_seconds, observation_density.

    observation_density is non-null readings per calendar day across the span.
    """
    valid = pd.to_datetime(timestamps, errors="coerce").dropna().sort_values()
    if len(valid) < 2:
        return 0.0, 0.0, float(len(valid))

    span_seconds = (valid.iloc[-1] - valid.iloc[0]).total_seconds()
    span_days = max(span_seconds / 86_400.0, 1.0 / 86_400.0)
    deltas = pd.to_timedelta(valid.diff().dropna())
    max_gap_seconds = float(deltas.max().total_seconds()) if not deltas.empty else 0.0
    observation_density = float(len(valid) / span_days)
    return span_days, max_gap_seconds, observation_density
