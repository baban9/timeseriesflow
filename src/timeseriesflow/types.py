"""Shared type definitions for TimeSeriesFlow."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypeAlias

import pandas as pd

EntityId: TypeAlias = Hashable


@dataclass(frozen=True, slots=True)
class RunContext:
    """Runtime context passed to each entity processor invocation."""

    entity_id: EntityId
    entity_column: str
    attempt: int
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def elapsed_seconds(self) -> float:
        """Return seconds elapsed since this entity run started."""
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()


@dataclass(slots=True)
class FlowEntityResult:
    """Outcome of processing a single entity via the legacy Flow engine."""

    entity_id: EntityId
    success: bool
    dataframe: pd.DataFrame | None = None
    error: BaseException | None = None
    attempts: int = 1
    duration_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def entity_key(self) -> str:
        """Alias for entity_column (developer API naming)."""
        return self.entity_column

    @property
    def runtime_seconds(self) -> float:
        """Alias for duration_seconds (developer API naming)."""
        return self.duration_seconds

    @property
    def memory_delta_mb(self) -> float:
        """Alias for peak_memory_mb (developer API naming)."""
        return self.peak_memory_mb

    @property
    def failed(self) -> bool:
        return not self.success
