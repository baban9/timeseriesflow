"""AdaptiveForecast: profile univariate series and recommend forecasting architectures.

AdaptiveForecast analyzes one numeric time series at a time (volatility, trend,
seasonality, data quality) and returns ranked, explainable model recommendations
(naive through CNN-LSTM). It does not train models or produce forecasts.

Typical uses: per-sensor model routing, pre-training screening, and combined
runs with TimeSeriesFlow ``@entity_flow``. See docs/adaptiveforecast.md.
"""

from adaptiveforecast.advisor import ModelAdvisor
from adaptiveforecast.analyzer import ProfileAnalyzer
from adaptiveforecast.constants import SUPPORTED_RECIPES
from adaptiveforecast.exceptions import (
    AdaptiveForecastError,
    ProfileAnalysisError,
    ValidationGateError,
)
from adaptiveforecast.gate import GateCheck, GateResult, ValidationGate
from adaptiveforecast.preprocess import SparseGridResult, infer_median_freq, resample_to_grid
from adaptiveforecast.recipe import ModelRecipe
from adaptiveforecast.report import ProfileReport
from adaptiveforecast.selection import ArchitectureRecommendation, ArchitectureSelectionResult
from adaptiveforecast.selection_workflow import ProfileAwareArchitectureSelection

__all__ = [
    "SUPPORTED_RECIPES",
    "AdaptiveForecastError",
    "ArchitectureRecommendation",
    "ArchitectureSelectionResult",
    "GateCheck",
    "GateResult",
    "ModelAdvisor",
    "ModelRecipe",
    "ProfileAnalysisError",
    "ProfileAnalyzer",
    "ProfileAwareArchitectureSelection",
    "ProfileReport",
    "SparseGridResult",
    "ValidationGate",
    "ValidationGateError",
    "infer_median_freq",
    "resample_to_grid",
]

__version__ = "0.2.2"
