"""Flow configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from timeseriesflow.retry import RetryPolicy


@dataclass(slots=True)
class FlowConfig:
    """Configuration for a TimeSeriesFlow run."""

    entity_column: str
    checkpoint_dir: Path | None = None
    resume: bool = True
    fail_fast: bool = False
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    show_progress: bool = True
    track_memory: bool = True
    log_level: str = "INFO"
    sort_entities: bool = True
    max_entities: int | None = None

    def __post_init__(self) -> None:
        if not self.entity_column:
            raise ValueError("entity_column must be a non-empty string")
        if self.max_entities is not None and self.max_entities <= 0:
            raise ValueError("max_entities must be positive when set")
