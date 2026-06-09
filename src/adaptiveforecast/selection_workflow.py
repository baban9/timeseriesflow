"""Profile-Aware Architecture Selection workflow."""

from __future__ import annotations

from typing import Any

import pandas as pd

from adaptiveforecast.advisor import ModelAdvisor
from adaptiveforecast.analyzer import ProfileAnalyzer
from adaptiveforecast.gate import ValidationGate
from adaptiveforecast.selection import ArchitectureRecommendation, ArchitectureSelectionResult


class ProfileAwareArchitectureSelection:
    """Flagship workflow: profile, advise, validate, and select the best model.

    Workflow::

        Time Series -> ProfileAnalyzer -> ModelAdvisor -> Candidate Models
        -> ValidationGate -> Best Model
    """

    def __init__(
        self,
        *,
        analyzer: ProfileAnalyzer | None = None,
        advisor: ModelAdvisor | None = None,
        gate: ValidationGate | None = None,
        time_column: str | None = None,
        value_column: str = "value",
        max_models: int = 3,
        expected_freq: str | None = None,
        infer_freq: bool = False,
    ) -> None:
        self.analyzer = analyzer or ProfileAnalyzer(
            time_column=time_column,
            value_column=value_column,
            expected_freq=expected_freq,
            infer_freq=infer_freq,
        )
        self.advisor = advisor or ModelAdvisor(max_models=max_models)
        self.gate = gate or ValidationGate()

    def select(
        self,
        data: pd.DataFrame | pd.Series,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ArchitectureSelectionResult:
        """Run the full profile-aware architecture selection workflow."""
        profile = self.analyzer.analyze(data, metadata=metadata)
        gate_result = self.gate.validate(profile)

        if not gate_result.passed:
            return ArchitectureSelectionResult(
                profile=profile,
                recommendation=ArchitectureRecommendation(
                    recommended_models=(),
                    reason="Validation gate failed; resolve data quality issues before modeling.",
                    reasons={},
                    candidates=(),
                    best_model=None,
                    profile=profile,
                ),
                gate_passed=False,
                gate_failures=tuple(check.name for check in gate_result.failures),
            )

        recommendation = self.advisor.recommend(profile)
        return ArchitectureSelectionResult(
            profile=profile,
            recommendation=recommendation,
            gate_passed=True,
        )
