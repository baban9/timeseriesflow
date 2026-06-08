"""AdaptiveForecast: model-agnostic time-series profiling and architecture advice."""

from adaptiveforecast.advisor import ModelAdvisor
from adaptiveforecast.analyzer import ProfileAnalyzer
from adaptiveforecast.constants import SUPPORTED_RECIPES
from adaptiveforecast.exceptions import (
    AdaptiveForecastError,
    ProfileAnalysisError,
    ValidationGateError,
)
from adaptiveforecast.gate import GateCheck, GateResult, ValidationGate
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
    "ValidationGate",
    "ValidationGateError",
]

__version__ = "0.1.0"
