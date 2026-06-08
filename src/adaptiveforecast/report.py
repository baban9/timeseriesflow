"""Profile report dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProfileReport:
    """Statistical profile of a univariate time series.

    All ratio and strength fields are normalized to the range [0.0, 1.0]
    unless noted otherwise.
    """

    row_count: int
    missing_rate: float
    volatility: float
    trend_strength: float
    seasonality_strength: float
    outlier_ratio: float
    spike_ratio: float
    flatline_ratio: float
    sampling_irregularity: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return profile metrics as a plain dictionary."""
        return {
            "row_count": self.row_count,
            "missing_rate": self.missing_rate,
            "volatility": self.volatility,
            "trend_strength": self.trend_strength,
            "seasonality_strength": self.seasonality_strength,
            "outlier_ratio": self.outlier_ratio,
            "spike_ratio": self.spike_ratio,
            "flatline_ratio": self.flatline_ratio,
            "sampling_irregularity": self.sampling_irregularity,
            "metadata": dict(self.metadata),
        }

    @property
    def is_empty(self) -> bool:
        return self.row_count == 0

    @property
    def effective_row_count(self) -> int:
        """Rows excluding missing values."""
        return max(0, round(self.row_count * (1.0 - self.missing_rate)))
