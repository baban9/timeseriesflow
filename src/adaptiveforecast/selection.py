"""Architecture recommendation result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adaptiveforecast.recipe import ModelRecipe
from adaptiveforecast.report import ProfileReport


@dataclass(frozen=True, slots=True)
class ArchitectureRecommendation:
    """Explainable, deterministic architecture recommendation output."""

    recommended_models: tuple[str, ...]
    reason: str
    reasons: dict[str, str] = field(default_factory=dict)
    candidates: tuple[ModelRecipe, ...] = field(default_factory=tuple)
    best_model: str | None = None
    profile: ProfileReport | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the public recommendation payload."""
        return {
            "recommended_models": list(self.recommended_models),
            "reason": self.reason,
            "reasons": dict(self.reasons),
            "best_model": self.best_model,
        }


@dataclass(frozen=True, slots=True)
class ArchitectureSelectionResult:
    """Full Profile-Aware Architecture Selection workflow result."""

    profile: ProfileReport
    recommendation: ArchitectureRecommendation
    gate_passed: bool
    gate_failures: tuple[str, ...] = field(default_factory=tuple)

    @property
    def best_model(self) -> str | None:
        return self.recommendation.best_model

    def to_dict(self) -> dict[str, Any]:
        payload = self.recommendation.to_dict()
        payload["gate_passed"] = self.gate_passed
        if self.gate_failures:
            payload["gate_failures"] = list(self.gate_failures)
        payload["profile"] = self.profile.to_dict()
        return payload
