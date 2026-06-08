"""Result types for the entity flow developer API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from timeseriesflow.types import EntityId


@dataclass(slots=True)
class EntityResult:
    """Outcome of processing a single entity.

    Attributes:
        entity_id: Identifier of the processed entity.
        success: Whether processing completed without error.
        runtime_seconds: Wall-clock duration of the entity run.
        memory_delta_mb: RSS memory increase during processing.
        output: Value returned by the processor on success.
        error: Exception instance when processing failed.
    """

    entity_id: EntityId
    success: bool
    runtime_seconds: float
    memory_delta_mb: float
    output: Any = None
    error: BaseException | None = None
    attempts: int = 1

    @property
    def duration_seconds(self) -> float:
        """Alias for runtime_seconds (legacy Flow API naming)."""
        return self.runtime_seconds

    @property
    def peak_memory_mb(self) -> float:
        """Alias for memory_delta_mb (legacy Flow API naming)."""
        return self.memory_delta_mb

    @property
    def failed(self) -> bool:
        """Return True when processing did not succeed."""
        return not self.success


@dataclass(slots=True)
class EntityFlowResult:
    """Collected results from an EntityFlow run."""

    results: list[EntityResult] = field(default_factory=list)
    skipped: int = 0

    @property
    def processed(self) -> int:
        """Number of entities processed in this run."""
        return len(self.results)

    @property
    def succeeded(self) -> int:
        """Number of entities that completed successfully."""
        return sum(1 for result in self.results if result.success)

    @property
    def failed(self) -> int:
        """Number of entities that failed."""
        return sum(1 for result in self.results if result.failed)

    @property
    def outputs(self) -> list[Any]:
        """Outputs from successful entities only, in processing order."""
        return [result.output for result in self.results if result.success]

    def by_entity(self, entity_id: EntityId) -> EntityResult | None:
        """Return the result for a specific entity, if present."""
        for result in self.results:
            if result.entity_id == entity_id:
                return result
        return None
