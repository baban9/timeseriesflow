"""AdaptiveForecast exceptions."""


class AdaptiveForecastError(Exception):
    """Base exception for AdaptiveForecast."""


class ProfileAnalysisError(AdaptiveForecastError):
    """Raised when time-series profiling fails."""


class ValidationGateError(AdaptiveForecastError):
    """Raised when validation gate configuration is invalid."""
