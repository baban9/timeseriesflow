"""Memory usage tracking."""

from __future__ import annotations

from dataclasses import dataclass

import psutil


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """Point-in-time memory measurement."""

    rss_mb: float
    vms_mb: float

    @classmethod
    def capture(cls) -> MemorySnapshot:
        process = psutil.Process()
        mem = process.memory_info()
        return cls(rss_mb=mem.rss / (1024 * 1024), vms_mb=mem.vms / (1024 * 1024))


class MemoryTracker:
    """Track peak memory usage during entity processing."""

    def __init__(self) -> None:
        self._peak_rss_mb = 0.0
        self._enabled = True

    @property
    def peak_rss_mb(self) -> float:
        return self._peak_rss_mb

    def sample(self) -> MemorySnapshot:
        snapshot = MemorySnapshot.capture()
        if self._enabled:
            self._peak_rss_mb = max(self._peak_rss_mb, snapshot.rss_mb)
        return snapshot

    def reset(self) -> None:
        self._peak_rss_mb = 0.0

    def disable(self) -> None:
        self._enabled = False

    def enable(self) -> None:
        self._enabled = True
