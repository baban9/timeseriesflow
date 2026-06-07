"""Model-agnostic forecasting architecture advisor."""

from __future__ import annotations

from adaptiveforecast.recipe import ModelRecipe
from adaptiveforecast.report import ProfileReport
from adaptiveforecast.rules import RuleMatch, build_summary_reason, evaluate_rules
from adaptiveforecast.selection import ArchitectureRecommendation


class ModelAdvisor:
    """Recommend candidate forecasting architectures from a profile report.

    Profile-Aware Architecture Selection uses deterministic rules over profile
    metrics. Returns explainable metadata only; no model code is generated.
    """

    def __init__(self, *, max_models: int = 3) -> None:
        if max_models < 1:
            raise ValueError("max_models must be at least 1")
        self.max_models = max_models

    def recommend(self, profile: ProfileReport) -> ArchitectureRecommendation:
        """Recommend architectures for a profile report.

        Args:
            profile: Output from ``ProfileAnalyzer.analyze``.

        Returns:
            ``ArchitectureRecommendation`` with ranked model names and reasons.
        """
        if profile.is_empty or profile.effective_row_count == 0:
            return ArchitectureRecommendation(
                recommended_models=(),
                reason="Insufficient data for architecture selection.",
                reasons={},
                candidates=(),
                best_model=None,
                profile=profile,
            )

        matches = evaluate_rules(profile)
        selected = matches[: self.max_models]
        recipes = tuple(_match_to_recipe(match) for match in selected)
        model_names = tuple(recipe.name for recipe in recipes)
        reasons = {match.model: match.reason for match in selected}

        return ArchitectureRecommendation(
            recommended_models=model_names,
            reason=build_summary_reason(selected),
            reasons=reasons,
            candidates=recipes,
            best_model=model_names[0] if model_names else None,
            profile=profile,
        )

    def recommend_models(self, profile: ProfileReport) -> list[ModelRecipe]:
        """Return candidate recipes (backward-compatible helper)."""
        return list(self.recommend(profile).candidates)


def _match_to_recipe(match: RuleMatch) -> ModelRecipe:
    return ModelRecipe(
        name=match.model,
        family=match.family,
        rationale=match.reason,
        priority=match.priority,
        parameters=dict(match.parameters),
        tags=_tags_for_model(match.model),
    )


def _tags_for_model(model: str) -> tuple[str, ...]:
    mapping: dict[str, tuple[str, ...]] = {
        "naive": ("baseline", "simple"),
        "moving_average": ("baseline", "smooth"),
        "exponential_smoothing": ("statistical", "smoothing"),
        "lstm": ("deep", "recurrent"),
        "gru": ("deep", "recurrent"),
        "residual_lstm": ("deep", "recurrent", "robust"),
        "cnn_lstm": ("deep", "recurrent", "convolutional", "robust"),
    }
    return mapping.get(model, ("supported",))
