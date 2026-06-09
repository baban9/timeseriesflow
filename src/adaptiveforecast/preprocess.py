"""Sparse series grid alignment for profiling and entity pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

AggMethod = Literal["mean", "last", "sum"]


@dataclass(frozen=True, slots=True)
class SparseGridResult:
    """Output of aligning irregular readings to an expected time grid."""

    frame: pd.DataFrame
    time_column: str
    value_column: str
    freq: str
    grid_slot_count: int
    observed_slot_count: int
    coverage_ratio: float

    def to_dict(self) -> dict[str, object]:
        return {
            "time_column": self.time_column,
            "value_column": self.value_column,
            "freq": self.freq,
            "grid_slot_count": self.grid_slot_count,
            "observed_slot_count": self.observed_slot_count,
            "coverage_ratio": self.coverage_ratio,
        }


def infer_median_freq(timestamps: pd.Series) -> str | None:
    """Infer a pandas frequency string from the median timestamp gap."""
    valid = pd.to_datetime(timestamps, errors="coerce").dropna().sort_values()
    if len(valid) < 2:
        return None
    deltas = valid.diff().dropna()
    if deltas.empty:
        return None
    median_delta = pd.Timedelta(deltas.median())
    if pd.isna(median_delta) or median_delta <= pd.Timedelta(0):
        return None
    offset = pd.tseries.frequencies.to_offset(median_delta)
    return str(offset.freqstr)


def resample_to_grid(
    data: pd.DataFrame,
    *,
    time_column: str,
    value_column: str,
    freq: str,
    agg: AggMethod = "mean",
    include_observed_flag: bool = False,
) -> SparseGridResult:
    """Align irregular readings to a regular time grid.

    Empty buckets become NaN in ``value_column``. Coverage is the fraction of
    grid slots with at least one observed reading.
    """
    if time_column not in data.columns:
        raise ValueError(f"time column {time_column!r} not found")
    if value_column not in data.columns:
        raise ValueError(f"value column {value_column!r} not found")

    frame = data[[time_column, value_column]].copy()
    frame[time_column] = pd.to_datetime(frame[time_column], errors="coerce")
    frame = frame.dropna(subset=[time_column]).sort_values(time_column)
    if frame.empty:
        empty = pd.DataFrame(columns=[time_column, value_column])
        return SparseGridResult(
            frame=empty,
            time_column=time_column,
            value_column=value_column,
            freq=freq,
            grid_slot_count=0,
            observed_slot_count=0,
            coverage_ratio=0.0,
        )

    indexed = frame.set_index(time_column)
    observed_flags = ~indexed[value_column].isna()
    resampled_values = indexed[value_column].resample(freq).agg(agg)
    resampled_observed = observed_flags.resample(freq).max().fillna(False).astype(bool)

    out = resampled_values.reset_index()
    out.columns = [time_column, value_column]
    grid_slot_count = len(out)
    observed_slot_count = int(resampled_observed.sum())
    coverage_ratio = float(observed_slot_count / grid_slot_count) if grid_slot_count else 0.0

    if include_observed_flag:
        out["was_observed"] = resampled_observed.reset_index(drop=True)

    return SparseGridResult(
        frame=out,
        time_column=time_column,
        value_column=value_column,
        freq=freq,
        grid_slot_count=grid_slot_count,
        observed_slot_count=observed_slot_count,
        coverage_ratio=coverage_ratio,
    )
