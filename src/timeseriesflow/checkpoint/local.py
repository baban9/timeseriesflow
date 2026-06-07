"""Local filesystem checkpoint backend using append-only JSONL."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from timeseriesflow.checkpoint.backend import CheckpointBackend
from timeseriesflow.checkpoint.io import append_jsonl_line, iter_jsonl_entries
from timeseriesflow.checkpoint.models import (
    CheckpointEntry,
    CheckpointStatus,
    CheckpointSummary,
)
from timeseriesflow.exceptions import CheckpointError
from timeseriesflow.types import EntityId


class LocalCheckpoint(CheckpointBackend):
    """Append-only JSONL checkpoint store on the local filesystem.

    Storage layout::

        checkpoint_dir/
            checkpoints.jsonl

    Each line is one immutable checkpoint event. The latest line per entity
    determines current status. Writes are fsynced for crash safety.

    Performance notes:
        - Cold start loads scan the full JSONL file once and cache state.
        - Each mark_* call appends one line and fsyncs (durable, low volume).
        - For very large runs (millions of entities), consider future
          SQLiteCheckpoint or RedisCheckpoint backends with indexed lookups.
    """

    LOG_FILENAME = "checkpoints.jsonl"

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.log_path = self.directory / self.LOG_FILENAME
        self._latest: dict[EntityId, CheckpointEntry] | None = None
        self._total_entries: int | None = None

    def mark_completed(
        self,
        entity_id: EntityId,
        *,
        runtime_seconds: float = 0.0,
        memory_delta_mb: float = 0.0,
        attempts: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a completed entry. No-op when the entity is already completed."""
        if self.is_completed(entity_id):
            return
        entry = self._build_entry(
            entity_id=entity_id,
            status=CheckpointStatus.COMPLETED,
            runtime_seconds=runtime_seconds,
            memory_delta_mb=memory_delta_mb,
            attempts=attempts,
            metadata=metadata,
        )
        self._append(entry)

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
        """Append a failed entry. No-op when the entity is already completed."""
        if self.is_completed(entity_id):
            return
        error_message = str(error) if error is not None else None
        entry = self._build_entry(
            entity_id=entity_id,
            status=CheckpointStatus.FAILED,
            runtime_seconds=runtime_seconds,
            memory_delta_mb=memory_delta_mb,
            attempts=attempts,
            error_message=error_message,
            metadata=metadata,
        )
        self._append(entry)

    def is_completed(self, entity_id: EntityId) -> bool:
        entry = self._state().get(entity_id)
        return entry is not None and entry.status == CheckpointStatus.COMPLETED

    def load_completed(self) -> set[EntityId]:
        return {
            entity_id
            for entity_id, entry in self._state().items()
            if entry.status == CheckpointStatus.COMPLETED
        }

    def load_failed(self) -> set[EntityId]:
        return {
            entity_id
            for entity_id, entry in self._state().items()
            if entry.status == CheckpointStatus.FAILED
        }

    def summary(self) -> CheckpointSummary:
        completed = self.load_completed()
        failed = self.load_failed()
        total_entries = self._entry_count()
        return CheckpointSummary(
            completed_count=len(completed),
            failed_count=len(failed),
            total_entries=total_entries,
            completed_entities=frozenset(completed),
            failed_entities=frozenset(failed),
        )

    def clear(self) -> None:
        """Remove all checkpoint data (primarily for tests)."""
        self._latest = {}
        self._total_entries = 0
        if self.log_path.exists():
            self.log_path.unlink()

    def _build_entry(
        self,
        *,
        entity_id: EntityId,
        status: CheckpointStatus,
        runtime_seconds: float,
        memory_delta_mb: float,
        attempts: int,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CheckpointEntry:
        return CheckpointEntry(
            entity_id=entity_id,
            status=status,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            runtime_seconds=runtime_seconds,
            memory_delta_mb=memory_delta_mb,
            attempts=attempts,
            error_message=error_message,
            metadata=metadata or {},
        )

    def _append(self, entry: CheckpointEntry) -> None:
        append_jsonl_line(self.log_path, entry.to_dict())
        state = self._state()
        state[entry.entity_id] = entry
        if self._total_entries is None:
            self._total_entries = 0
        self._total_entries += 1

    def _entry_count(self) -> int:
        if self._total_entries is None:
            self._total_entries = sum(1 for _ in iter_jsonl_entries(self.log_path))
        return self._total_entries

    def _state(self) -> dict[EntityId, CheckpointEntry]:
        if self._latest is None:
            self._latest = self._load_state_from_disk()
        return self._latest

    def _load_state_from_disk(self) -> dict[EntityId, CheckpointEntry]:
        latest: dict[EntityId, CheckpointEntry] = {}
        entry_count = 0
        for raw in iter_jsonl_entries(self.log_path):
            entry_count += 1
            try:
                entry = CheckpointEntry.from_dict(raw)
            except (KeyError, ValueError, TypeError) as exc:
                raise CheckpointError("invalid checkpoint entry in log") from exc
            latest[entry.entity_id] = entry
        self._total_entries = entry_count
        return latest
