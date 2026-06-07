"""Deterministic recommendation rules for supported architectures."""

from __future__ import annotations

from dataclasses import dataclass

from adaptiveforecast.constants import SUPPORTED_RECIPES
from adaptiveforecast.report import ProfileReport


@dataclass(frozen=True, slots=True)
class RuleMatch:
    """A matched architecture rule."""

    model: str
    priority: int
    reason: str
    family: str
    parameters: dict[str, object]


def evaluate_rules(report: ProfileReport) -> list[RuleMatch]:
    """Evaluate all supported architecture rules deterministically."""
    matches: list[RuleMatch] = []

    if (
        report.trend_strength < 0.25
        and report.seasonality_strength < 0.25
        and report.volatility < 0.40
    ):
        matches.append(
            RuleMatch(
                model="naive",
                priority=10,
                reason="Stable series with weak trend and seasonality.",
                family="baseline",
                parameters={"strategy": "last_value"},
            )
        )

    if report.volatility < 0.45 and report.spike_ratio < 0.10 and report.flatline_ratio < 0.35:
        matches.append(
            RuleMatch(
                model="moving_average",
                priority=20,
                reason="Low volatility and few spikes suit a smoothed baseline.",
                family="baseline",
                parameters={"window": _suggested_window(report.row_count)},
            )
        )

    if (
        (report.trend_strength >= 0.20 or report.seasonality_strength >= 0.20)
        and report.volatility < 0.55
        and report.sampling_irregularity < 0.50
    ):
        matches.append(
            RuleMatch(
                model="exponential_smoothing",
                priority=30,
                reason="Trend or seasonality present with moderate volatility.",
                family="statistical",
                parameters={
                    "seasonal": report.seasonality_strength >= 0.20,
                    "trend": report.trend_strength >= 0.20,
                },
            )
        )

    if (
        report.effective_row_count >= 100
        and (report.seasonality_strength >= 0.30 or report.trend_strength >= 0.30)
        and report.volatility >= 0.25
    ):
        matches.append(
            RuleMatch(
                model="lstm",
                priority=40,
                reason="Sufficient history and structured temporal patterns for LSTM.",
                family="deep",
                parameters={"sequence_length": _suggested_sequence(report.row_count)},
            )
        )

    if (
        report.effective_row_count >= 60
        and report.effective_row_count < 250
        and (report.seasonality_strength >= 0.20 or report.trend_strength >= 0.20)
        and report.volatility < 0.70
    ):
        matches.append(
            RuleMatch(
                model="gru",
                priority=45,
                reason="Medium-length series with patterns suitable for a lighter recurrent model.",
                family="deep",
                parameters={"sequence_length": _suggested_sequence(report.row_count)},
            )
        )

    if (
        report.volatility >= 0.45
        and (report.spike_ratio >= 0.05 or report.outlier_ratio >= 0.05)
        and report.effective_row_count >= 80
    ):
        matches.append(
            RuleMatch(
                model="residual_lstm",
                priority=15,
                reason="High volatility with outliers or spikes; residual learning helps.",
                family="deep",
                parameters={
                    "residual_baseline": "moving_average",
                    "volatility_hint": round(report.volatility, 3),
                },
            )
        )

    if (
        report.volatility >= 0.50
        and report.spike_ratio >= 0.08
        and report.effective_row_count >= 120
    ):
        matches.append(
            RuleMatch(
                model="cnn_lstm",
                priority=5,
                reason="High volatility and frequent spikes detected.",
                family="deep",
                parameters={
                    "conv_filters": 32,
                    "spike_ratio_hint": round(report.spike_ratio, 3),
                },
            )
        )

    matches.sort(key=lambda match: (match.priority, match.model))
    return _dedupe_by_model(matches)


def build_summary_reason(matches: list[RuleMatch]) -> str:
    """Build a single summary reason from the top matched rules."""
    if not matches:
        return "No supported architecture matched; series may need preprocessing."
    primary = matches[0].reason
    if len(matches) == 1:
        return primary
    secondary = matches[1].reason.rstrip(".")
    return f"{primary} Also consider: {secondary.lower()}."


def _dedupe_by_model(matches: list[RuleMatch]) -> list[RuleMatch]:
    seen: set[str] = set()
    unique: list[RuleMatch] = []
    for match in matches:
        if match.model in seen:
            continue
        if match.model not in SUPPORTED_RECIPES:
            continue
        seen.add(match.model)
        unique.append(match)
    return unique


def _suggested_window(row_count: int) -> int:
    return int(max(3, min(28, row_count // 10)))


def _suggested_sequence(row_count: int) -> int:
    return int(max(12, min(96, row_count // 5)))
