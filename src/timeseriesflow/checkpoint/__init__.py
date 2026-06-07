"""Checkpoint storage backends."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from timeseriesflow.exceptions import CheckpointError
from timeseriesflow.types import EntityId


@dataclass(slots=True)
class CheckpointRecord:
    """Persisted state for a completed entity."""

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
    """Abstract checkpoint store for resumable flow runs."""

    @abstractmethod
    def load_completed_entities(self) -> set[EntityId]:
        """Return entity IDs that have already completed successfully."""

    @abstractmethod
    def save(self, record: CheckpointRecord) -> None:
        """Persist checkpoint for a completed entity."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all checkpoint data."""


def _entity_key(entity_id: EntityId) -> str:
    return str(entity_id).replace("/", "_").replace("\\", "_")


class FileCheckpointStore(CheckpointStore):
    """File-based checkpoint store using JSON lines."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self._index_path = self.directory / "index.jsonl"

    def _record_path(self, entity_id: EntityId) -> Path:
        return self.directory / f"{_entity_key(entity_id)}.json"

    def load_completed_entities(self) -> set[EntityId]:
        completed: set[EntityId] = set()
        if not self._index_path.exists():
            return completed
        try:
            with self._index_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("success"):
                        completed.add(data["entity_id"])
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckpointError(f"failed to read checkpoint index at {self._index_path}") from exc
        return completed

    def save(self, record: CheckpointRecord) -> None:
        payload = asdict(record)
        record_path = self._record_path(record.entity_id)
        try:
            record_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            with self._index_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")
        except OSError as exc:
            raise CheckpointError(f"failed to write checkpoint for entity {record.entity_id!r}") from exc

    def clear(self) -> None:
        if not self.directory.exists():
            return
        for path in self.directory.glob("*"):
            if path.is_file():
                path.unlink()


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
