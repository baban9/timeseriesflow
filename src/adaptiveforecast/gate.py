"""Validation gates for profile reports."""

from __future__ import annotations

from dataclasses import dataclass, field

from adaptiveforecast.exceptions import ValidationGateError
from adaptiveforecast.report import ProfileReport


@dataclass(frozen=True, slots=True)
class GateCheck:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    threshold: float | int | None = None
    observed: float | int | None = None


@dataclass(frozen=True, slots=True)
class GateResult:
    """Aggregate validation gate outcome."""

    passed: bool
    checks: tuple[GateCheck, ...] = field(default_factory=tuple)

    @property
    def failures(self) -> tuple[GateCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


class ValidationGate:
    """Validate whether a profile is suitable for forecasting.

    Gates are declarative thresholds applied to ``ProfileReport`` metrics.
    They do not train or evaluate forecasting models.
    """

    def __init__(
        self,
        *,
        min_rows: int = 30,
        max_missing_rate: float = 0.25,
        max_outlier_ratio: float = 0.20,
        max_spike_ratio: float = 0.15,
        max_flatline_ratio: float = 0.50,
        max_sampling_irregularity: float = 0.60,
    ) -> None:
        if min_rows < 1:
            raise ValidationGateError("min_rows must be at least 1")
        for name, value in (
            ("max_missing_rate", max_missing_rate),
            ("max_outlier_ratio", max_outlier_ratio),
            ("max_spike_ratio", max_spike_ratio),
            ("max_flatline_ratio", max_flatline_ratio),
            ("max_sampling_irregularity", max_sampling_irregularity),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValidationGateError(f"{name} must be between 0 and 1")
        self.min_rows = min_rows
        self.max_missing_rate = max_missing_rate
        self.max_outlier_ratio = max_outlier_ratio
        self.max_spike_ratio = max_spike_ratio
        self.max_flatline_ratio = max_flatline_ratio
        self.max_sampling_irregularity = max_sampling_irregularity

    def validate(self, report: ProfileReport) -> GateResult:
        """Run all configured gates against a profile report."""
        checks = (
            self._check_min_rows(report),
            self._check_max_rate(
                "missing_rate",
                report.missing_rate,
                self.max_missing_rate,
            ),
            self._check_max_rate(
                "outlier_ratio",
                report.outlier_ratio,
                self.max_outlier_ratio,
            ),
            self._check_max_rate(
                "spike_ratio",
                report.spike_ratio,
                self.max_spike_ratio,
            ),
            self._check_max_rate(
                "flatline_ratio",
                report.flatline_ratio,
                self.max_flatline_ratio,
            ),
            self._check_max_rate(
                "sampling_irregularity",
                report.sampling_irregularity,
                self.max_sampling_irregularity,
            ),
        )
        return GateResult(passed=all(check.passed for check in checks), checks=checks)

    def _check_min_rows(self, report: ProfileReport) -> GateCheck:
        passed = report.effective_row_count >= self.min_rows
        return GateCheck(
            name="min_rows",
            passed=passed,
            message=(
                f"effective rows {report.effective_row_count} >= {self.min_rows}"
                if passed
                else f"effective rows {report.effective_row_count} below minimum {self.min_rows}"
            ),
            threshold=self.min_rows,
            observed=report.effective_row_count,
        )

    def _check_max_rate(self, name: str, observed: float, threshold: float) -> GateCheck:
        passed = observed <= threshold
        return GateCheck(
            name=name,
            passed=passed,
            message=(
                f"{name} {observed:.3f} <= {threshold:.3f}"
                if passed
                else f"{name} {observed:.3f} exceeds maximum {threshold:.3f}"
            ),
            threshold=threshold,
            observed=observed,
        )
