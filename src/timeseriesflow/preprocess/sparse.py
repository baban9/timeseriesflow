"""Sparse series alignment for per-entity entity flows."""

from __future__ import annotations

import pandas as pd

from adaptiveforecast.preprocess import AggMethod, SparseGridResult, resample_to_grid


def align_entity_to_grid(
    df: pd.DataFrame,
    *,
    time_column: str,
    value_column: str,
    freq: str,
    agg: AggMethod = "mean",
) -> SparseGridResult:
    """Resample one entity frame to a regular grid with a ``was_observed`` flag."""
    return resample_to_grid(
        df,
        time_column=time_column,
        value_column=value_column,
        freq=freq,
        agg=agg,
        include_observed_flag=True,
    )
