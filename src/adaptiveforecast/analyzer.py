"""Time-series profile analysis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from adaptiveforecast.exceptions import ProfileAnalysisError
from adaptiveforecast.report import ProfileReport


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def _normalized_strength(value: float) -> float:
    return float(np.clip(abs(value), 0.0, 1.0))


class ProfileAnalyzer:
    """Analyze univariate time-series characteristics.

    Model-agnostic profiler that computes descriptive statistics used to
    recommend forecasting architectures. Does not fit or generate models.

    Example:
        analyzer = ProfileAnalyzer(time_column="timestamp", value_column="value")
        report = analyzer.analyze(df)
    """

    DEFAULT_SEASONAL_LAGS = (7, 12, 24, 30, 52, 168)

    def __init__(
        self,
        *,
        time_column: str | None = None,
        value_column: str,
        spike_sigma: float = 3.0,
        flatline_min_run: int = 3,
        seasonal_lags: tuple[int, ...] | None = None,
    ) -> None:
        if not value_column:
            raise ValueError("value_column must be a non-empty string")
        if spike_sigma <= 0:
            raise ValueError("spike_sigma must be positive")
        if flatline_min_run < 2:
            raise ValueError("flatline_min_run must be at least 2")
        self.time_column = time_column
        self.value_column = value_column
        self.spike_sigma = spike_sigma
        self.flatline_min_run = flatline_min_run
        self.seasonal_lags = seasonal_lags or self.DEFAULT_SEASONAL_LAGS

    def analyze(
        self,
        data: pd.DataFrame | pd.Series,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ProfileReport:
        """Compute a profile report for the given time series."""
        series, timestamps = self._prepare_inputs(data)
        row_count = len(series)

        if row_count == 0:
            return ProfileReport(
                row_count=0,
                missing_rate=0.0,
                volatility=0.0,
                trend_strength=0.0,
                seasonality_strength=0.0,
                outlier_ratio=0.0,
                spike_ratio=0.0,
                flatline_ratio=0.0,
                sampling_irregularity=0.0,
                metadata=metadata or {},
            )

        missing_rate = float(series.isna().mean())
        values = series.astype(float)
        observed = values.dropna()

        if observed.empty:
            raise ProfileAnalysisError("time series contains only missing values")

        return ProfileReport(
            row_count=row_count,
            missing_rate=missing_rate,
            volatility=self._volatility(observed),
            trend_strength=self._trend_strength(observed),
            seasonality_strength=self._seasonality_strength(observed),
            outlier_ratio=self._outlier_ratio(observed),
            spike_ratio=self._spike_ratio(observed),
            flatline_ratio=self._flatline_ratio(observed),
            sampling_irregularity=self._sampling_irregularity(timestamps),
            metadata=metadata or {},
        )

    def _prepare_inputs(
        self,
        data: pd.DataFrame | pd.Series,
    ) -> tuple[pd.Series, pd.Series | None]:
        if isinstance(data, pd.Series):
            series = data.copy()
            is_datetime_index = isinstance(series.index, pd.DatetimeIndex)
            series_timestamps = series.index.to_series() if is_datetime_index else None
            return series, series_timestamps

        if self.value_column not in data.columns:
            raise ProfileAnalysisError(
                f"value column {self.value_column!r} not found in dataframe"
            )

        frame = data.copy()
        timestamps: pd.Series | None = None
        if self.time_column is not None:
            if self.time_column not in frame.columns:
                raise ProfileAnalysisError(
                    f"time column {self.time_column!r} not found in dataframe"
                )
            timestamps = pd.to_datetime(frame[self.time_column], errors="coerce")
            frame = frame.sort_values(self.time_column)

        series = frame[self.value_column].reset_index(drop=True)
        if timestamps is not None:
            timestamps = timestamps.reset_index(drop=True)
        return series, timestamps

    def _volatility(self, values: pd.Series) -> float:
        mean = float(values.mean())
        std = float(values.std(ddof=0))
        if mean == 0.0:
            return _normalized_strength(std / (abs(float(values.iloc[0])) + 1e-9))
        cv = std / abs(mean)
        return _normalized_strength(cv / (cv + 1.0))

    def _trend_strength(self, values: pd.Series) -> float:
        if len(values) < 3:
            return 0.0
        x = np.arange(len(values), dtype=float)
        y = values.to_numpy(dtype=float)
        x_centered = x - x.mean()
        y_centered = y - y.mean()
        denom = float(np.sqrt(np.sum(x_centered**2) * np.sum(y_centered**2)))
        if denom == 0.0:
            return 0.0
        correlation = float(np.sum(x_centered * y_centered) / denom)
        return _normalized_strength(correlation)

    def _seasonality_strength(self, values: pd.Series) -> float:
        if len(values) < 8:
            return 0.0
        y = values.to_numpy(dtype=float)
        y = y - y.mean()
        denom = float(np.sum(y**2))
        if denom == 0.0:
            return 0.0

        strengths: list[float] = []
        for lag in self.seasonal_lags:
            if lag >= len(y):
                continue
            acf = float(np.sum(y[lag:] * y[:-lag]) / denom)
            strengths.append(abs(acf))
        if not strengths:
            return 0.0
        return _normalized_strength(max(strengths))

    def _outlier_ratio(self, values: pd.Series) -> float:
        if len(values) < 4:
            return 0.0
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0.0:
            return 0.0
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = ((values < lower) | (values > upper)).sum()
        return _safe_ratio(float(outliers), float(len(values)))

    def _spike_ratio(self, values: pd.Series) -> float:
        if len(values) < 3:
            return 0.0
        diffs = values.diff().dropna()
        if diffs.empty:
            return 0.0
        threshold = self.spike_sigma * float(diffs.std(ddof=0))
        if threshold == 0.0:
            return 0.0
        spikes = (diffs.abs() > threshold).sum()
        return _safe_ratio(float(spikes), float(len(diffs)))

    def _flatline_ratio(self, values: pd.Series) -> float:
        if len(values) < self.flatline_min_run:
            return 0.0
        arr = values.to_numpy(dtype=float)
        flatline_flags = np.zeros(len(arr), dtype=bool)
        run_length = 1
        for index in range(1, len(arr)):
            if arr[index] == arr[index - 1]:
                run_length += 1
            else:
                if run_length >= self.flatline_min_run:
                    flatline_flags[index - run_length : index] = True
                run_length = 1
        if run_length >= self.flatline_min_run:
            flatline_flags[len(arr) - run_length :] = True
        return _safe_ratio(float(flatline_flags.sum()), float(len(arr)))

    def _sampling_irregularity(self, timestamps: pd.Series | None) -> float:
        if timestamps is None:
            return 0.0
        valid = timestamps.dropna()
        if len(valid) < 3:
            return 0.0
        deltas = valid.sort_values().diff().dropna()
        if deltas.empty:
            return 0.0
        seconds = deltas.dt.total_seconds().astype(float)
        median = float(seconds.median())
        if median <= 0.0:
            return 1.0
        cv = float(seconds.std(ddof=0)) / median
        return _normalized_strength(cv / (cv + 1.0))
