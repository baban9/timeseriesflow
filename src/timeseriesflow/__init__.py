"""TimeSeriesFlow: entity-based time-series processing framework."""

from timeseriesflow.checkpoint import CheckpointStore, FileCheckpointStore
from timeseriesflow.config import FlowConfig
from timeseriesflow.core.engine import Flow
from timeseriesflow.core.processor import EntityProcessor, entity_processor
from timeseriesflow.exceptions import (
    CheckpointError,
    EntityProcessingError,
    FlowError,
    RetryExhaustedError,
)
from timeseriesflow.memory import MemoryTracker, MemorySnapshot
from timeseriesflow.progress import ProgressTracker, RunSummary
from timeseriesflow.retry import RetryPolicy
from timeseriesflow.types import EntityId, EntityResult, RunContext

__all__ = [
    "CheckpointError",
    "CheckpointStore",
    "EntityId",
    "EntityProcessingError",
    "EntityProcessor",
    "EntityResult",
    "FileCheckpointStore",
    "Flow",
    "FlowConfig",
    "FlowError",
    "MemorySnapshot",
    "MemoryTracker",
    "ProgressTracker",
    "RetryExhaustedError",
    "RetryPolicy",
    "RunContext",
    "RunSummary",
    "entity_processor",
]

__version__ = "0.1.0"
