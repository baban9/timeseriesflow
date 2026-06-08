"""Memory usage tracking with psutil."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psutil

from timeseriesflow.logging import get_logger
from timeseriesflow.memory.metrics import MemoryMetrics


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """Point-in-time memory measurement."""

    rss_mb: float
    vms_mb: float

    @classmethod
    def capture(cls) -> MemorySnapshot:
        """Capture current process memory usage."""
        process = psutil.Process()
        mem = process.memory_info()
        return cls(rss_mb=mem.rss / (1024 * 1024), vms_mb=mem.vms / (1024 * 1024))


class MemoryTracker:
    """Track memory usage and runtime with minimal overhead.

    Supports two modes:

    1. **Peak sampling** via ``sample()`` for long-running loops (EntityRunner, Flow).
    2. **Scoped measurement** via ``measure()`` or ``start()`` / ``finish()`` for
       before/after/delta metrics on a code block.

    Attributes:
        warning_threshold_mb: Log a warning when ``memory_delta_mb`` exceeds this value.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        warning_threshold_mb: float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._enabled = enabled
        self.warning_threshold_mb = warning_threshold_mb
        self._logger = logger or get_logger("memory")
        self._peak_rss_mb = 0.0
        self._before: MemorySnapshot | None = None
        self._start_time: float | None = None
        self._last_metrics: MemoryMetrics | None = None

    @property
    def peak_rss_mb(self) -> float:
        """Peak RSS observed via ``sample()`` during this tracker lifetime."""
        return self._peak_rss_mb

    @property
    def last_metrics(self) -> MemoryMetrics | None:
        """Metrics from the most recent scoped measurement."""
        return self._last_metrics

    def sample(self) -> MemorySnapshot | None:
        """Sample current memory and update peak. Returns None when disabled."""
        if not self._enabled:
            return None
        snapshot = MemorySnapshot.capture()
        self._peak_rss_mb = max(self._peak_rss_mb, snapshot.rss_mb)
        return snapshot

    def start(self) -> None:
        """Begin a scoped measurement."""
        if not self._enabled:
            self._before = None
            self._start_time = time.perf_counter()
            return
        self._before = MemorySnapshot.capture()
        self._start_time = time.perf_counter()
        self._peak_rss_mb = max(self._peak_rss_mb, self._before.rss_mb)

    def finish(self) -> MemoryMetrics:
        """End a scoped measurement and return metrics."""
        runtime_seconds = time.perf_counter() - (self._start_time or time.perf_counter())
        if not self._enabled or self._before is None:
            metrics = MemoryMetrics(
                runtime_seconds=runtime_seconds,
                memory_before_mb=0.0,
                memory_after_mb=0.0,
                memory_delta_mb=0.0,
                peak_memory_mb=self._peak_rss_mb,
            )
            self._last_metrics = metrics
            return metrics

        after = MemorySnapshot.capture()
        self._peak_rss_mb = max(self._peak_rss_mb, after.rss_mb)
        before_mb = self._before.rss_mb
        after_mb = after.rss_mb
        delta_mb = max(0.0, after_mb - before_mb)
        metrics = MemoryMetrics(
            runtime_seconds=runtime_seconds,
            memory_before_mb=before_mb,
            memory_after_mb=after_mb,
            memory_delta_mb=delta_mb,
            peak_memory_mb=self._peak_rss_mb,
        )
        self._last_metrics = metrics
        self._log_metrics(metrics)
        self._maybe_warn(metrics)
        return metrics

    @contextmanager
    def measure(self) -> Iterator[MemoryTracker]:
        """Context manager for scoped memory measurement."""
        self.start()
        try:
            yield self
        finally:
            self.finish()

    def reset(self) -> None:
        """Reset peak memory and last metrics."""
        self._peak_rss_mb = 0.0
        self._last_metrics = None
        self._before = None
        self._start_time = None

    def disable(self) -> None:
        """Disable sampling and measurement."""
        self._enabled = False

    def enable(self) -> None:
        """Enable sampling and measurement."""
        self._enabled = True

    def _log_metrics(self, metrics: MemoryMetrics) -> None:
        self._logger.debug(
            "memory tracked: runtime=%.3fs before=%.1fMB after=%.1fMB delta=%.1fMB peak=%.1fMB",
            metrics.runtime_seconds,
            metrics.memory_before_mb,
            metrics.memory_after_mb,
            metrics.memory_delta_mb,
            metrics.peak_memory_mb,
        )

    def _maybe_warn(self, metrics: MemoryMetrics) -> None:
        if self.warning_threshold_mb is None:
            return
        if metrics.memory_delta_mb >= self.warning_threshold_mb:
            self._logger.warning(
                "memory delta %.1f MB exceeded threshold %.1f MB",
                metrics.memory_delta_mb,
                self.warning_threshold_mb,
            )
