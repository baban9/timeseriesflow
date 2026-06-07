"""Forecasting architecture recipe definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelRecipe:
    """Recommended forecasting architecture (metadata only, no model code).

    Attributes:
        name: Architecture identifier (for example ``ets`` or ``sarima``).
        family: High-level model family (baseline, statistical, ml, ensemble).
        rationale: Human-readable reason for the recommendation.
        priority: Lower values indicate higher recommendation priority.
        parameters: Suggested configuration hints for downstream tooling.
        tags: Searchable capability tags.
    """

    name: str
    family: str
    rationale: str
    priority: int = 100
    parameters: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "rationale": self.rationale,
            "priority": self.priority,
            "parameters": dict(self.parameters),
            "tags": list(self.tags),
        }
