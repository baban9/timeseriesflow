"""Legacy checkpoint store compatibility layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from timeseriesflow.checkpoint.local import LocalCheckpoint
from timeseriesflow.types import EntityId


@dataclass(slots=True)
class CheckpointRecord:
    """Persisted state for a completed entity (legacy format)."""

    entity_id: EntityId
    success: bool
    attempts: int
    duration_seconds: float
    peak_memory_mb: float
    completed_at: str
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointRecord:
        return cls(
            entity_id=data["entity_id"],
            success=bool(data["success"]),
            attempts=int(data["attempts"]),
            duration_seconds=float(data["duration_seconds"]),
            peak_memory_mb=float(data["peak_memory_mb"]),
            completed_at=str(data["completed_at"]),
            metadata=dict(data.get("metadata", {})),
        )


class CheckpointStore(ABC):
    """Legacy abstract checkpoint store for resumable flow runs."""

    @abstractmethod
    def load_completed_entities(self) -> set[EntityId]:
        """Return entity IDs that have already completed successfully."""

    @abstractmethod
    def save(self, record: CheckpointRecord) -> None:
        """Persist checkpoint for a completed entity."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all checkpoint data."""


class FileCheckpointStore(CheckpointStore):
    """Legacy file checkpoint store backed by ``LocalCheckpoint``."""

    def __init__(self, directory: Path) -> None:
        self._backend = LocalCheckpoint(directory)

    def load_completed_entities(self) -> set[EntityId]:
        return self._backend.load_completed()

    def save(self, record: CheckpointRecord) -> None:
        if record.success:
            self._backend.mark_completed(
                record.entity_id,
                runtime_seconds=record.duration_seconds,
                memory_delta_mb=record.peak_memory_mb,
                attempts=record.attempts,
                metadata=record.metadata,
            )
            return
        self._backend.mark_failed(
            record.entity_id,
            runtime_seconds=record.duration_seconds,
            memory_delta_mb=record.peak_memory_mb,
            attempts=record.attempts,
            metadata={**record.metadata, "completed_at": record.completed_at},
        )

    def clear(self) -> None:
        self._backend.clear()

    @property
    def backend(self) -> LocalCheckpoint:
        """Underlying checkpoint backend."""
        return self._backend


def build_checkpoint_record(
    *,
    entity_id: EntityId,
    success: bool,
    attempts: int,
    duration_seconds: float,
    peak_memory_mb: float,
    metadata: dict[str, Any] | None = None,
) -> CheckpointRecord:
    return CheckpointRecord(
        entity_id=entity_id,
        success=success,
        attempts=attempts,
        duration_seconds=duration_seconds,
        peak_memory_mb=peak_memory_mb,
        completed_at=datetime.now(timezone.utc).isoformat(),
        metadata=metadata or {},
    )
