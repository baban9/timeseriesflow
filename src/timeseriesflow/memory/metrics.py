"""Memory measurement result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryMetrics:
    """Memory and runtime measurements for a tracked execution."""

    runtime_seconds: float
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float
    peak_memory_mb: float

    def to_dict(self) -> dict[str, float]:
        """Return metrics as a plain dictionary."""
        return {
            "runtime_seconds": self.runtime_seconds,
            "memory_before_mb": self.memory_before_mb,
            "memory_after_mb": self.memory_after_mb,
            "memory_delta_mb": self.memory_delta_mb,
            "peak_memory_mb": self.peak_memory_mb,
        }
