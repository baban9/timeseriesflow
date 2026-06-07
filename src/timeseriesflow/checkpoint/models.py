"""Checkpoint data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from timeseriesflow.types import EntityId


class CheckpointStatus(str, Enum):
    """Status recorded for an entity checkpoint entry."""

    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CheckpointEntry:
    """Single append-only checkpoint record."""

    entity_id: EntityId
    status: CheckpointStatus
    recorded_at: str
    runtime_seconds: float = 0.0
    memory_delta_mb: float = 0.0
    attempts: int = 1
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "status": self.status.value,
            "recorded_at": self.recorded_at,
            "runtime_seconds": self.runtime_seconds,
            "memory_delta_mb": self.memory_delta_mb,
            "attempts": self.attempts,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointEntry:
        return cls(
            entity_id=data["entity_id"],
            status=CheckpointStatus(str(data["status"])),
            recorded_at=str(data["recorded_at"]),
            runtime_seconds=float(data.get("runtime_seconds", 0.0)),
            memory_delta_mb=float(data.get("memory_delta_mb", 0.0)),
            attempts=int(data.get("attempts", 1)),
            error_message=data.get("error_message"),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class CheckpointSummary:
    """Aggregate view of checkpoint state."""

    completed_count: int
    failed_count: int
    total_entries: int
    completed_entities: frozenset[EntityId]
    failed_entities: frozenset[EntityId]

    @property
    def tracked_entities(self) -> int:
        """Number of unique entities with at least one checkpoint entry."""
        return self.completed_count + self.failed_count
