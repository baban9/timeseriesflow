"""Abstract checkpoint backend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from timeseriesflow.checkpoint.models import CheckpointSummary
from timeseriesflow.types import EntityId


class CheckpointBackend(ABC):
    """Abstract checkpoint backend for resumable entity processing.

    File, database, and remote backends (SQLite, Redis, S3) should subclass
    this interface without changing caller code.
    """

    @abstractmethod
    def mark_completed(
        self,
        entity_id: EntityId,
        *,
        runtime_seconds: float = 0.0,
        memory_delta_mb: float = 0.0,
        attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record successful completion for an entity (idempotent)."""

    @abstractmethod
    def mark_failed(
        self,
        entity_id: EntityId,
        *,
        error: BaseException | str | None = None,
        runtime_seconds: float = 0.0,
        memory_delta_mb: float = 0.0,
        attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record failure for an entity."""

    @abstractmethod
    def is_completed(self, entity_id: EntityId) -> bool:
        """Return True when the entity latest status is completed."""

    @abstractmethod
    def load_completed(self) -> set[EntityId]:
        """Return entity IDs whose latest status is completed."""

    @abstractmethod
    def load_failed(self) -> set[EntityId]:
        """Return entity IDs whose latest status is failed."""

    @abstractmethod
    def summary(self) -> CheckpointSummary:
        """Return aggregate checkpoint statistics."""

    def should_skip(self, entity_id: EntityId) -> bool:
        """Return True when an entity should be skipped on resume."""
        return self.is_completed(entity_id)
