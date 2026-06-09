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
        min_coverage_ratio: float = 0.0,
        max_gap_seconds: float | None = None,
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
        if not 0.0 <= min_coverage_ratio <= 1.0:
            raise ValidationGateError("min_coverage_ratio must be between 0 and 1")
        if max_gap_seconds is not None and max_gap_seconds <= 0:
            raise ValidationGateError("max_gap_seconds must be positive when set")
        self.min_rows = min_rows
        self.max_missing_rate = max_missing_rate
        self.max_outlier_ratio = max_outlier_ratio
        self.max_spike_ratio = max_spike_ratio
        self.max_flatline_ratio = max_flatline_ratio
        self.max_sampling_irregularity = max_sampling_irregularity
        self.min_coverage_ratio = min_coverage_ratio
        self.max_gap_seconds = max_gap_seconds

    def validate(self, report: ProfileReport) -> GateResult:
        """Run all configured gates against a profile report."""
        checks: list[GateCheck] = [
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
        ]
        if self.min_coverage_ratio > 0.0:
            checks.append(self._check_min_coverage(report))
        if self.max_gap_seconds is not None:
            checks.append(self._check_max_gap(report))
        return GateResult(passed=all(check.passed for check in checks), checks=tuple(checks))

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

    def _check_min_coverage(self, report: ProfileReport) -> GateCheck:
        passed = report.coverage_ratio >= self.min_coverage_ratio
        return GateCheck(
            name="min_coverage_ratio",
            passed=passed,
            message=(
                f"coverage_ratio {report.coverage_ratio:.3f} >= {self.min_coverage_ratio:.3f}"
                if passed
                else (
                    f"coverage_ratio {report.coverage_ratio:.3f} below minimum "
                    f"{self.min_coverage_ratio:.3f}"
                )
            ),
            threshold=self.min_coverage_ratio,
            observed=report.coverage_ratio,
        )

    def _check_max_gap(self, report: ProfileReport) -> GateCheck:
        assert self.max_gap_seconds is not None
        passed = report.max_gap_seconds <= self.max_gap_seconds
        return GateCheck(
            name="max_gap_seconds",
            passed=passed,
            message=(
                f"max_gap_seconds {report.max_gap_seconds:.1f} <= {self.max_gap_seconds:.1f}"
                if passed
                else (
                    f"max_gap_seconds {report.max_gap_seconds:.1f} exceeds maximum "
                    f"{self.max_gap_seconds:.1f}"
                )
            ),
            threshold=self.max_gap_seconds,
            observed=report.max_gap_seconds,
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
