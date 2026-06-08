"""Tests for memory tracking."""

from __future__ import annotations

import logging

import pytest

from timeseriesflow.memory import MemoryMetrics, MemoryTracker, track_memory


def test_memory_tracker_measure_returns_metrics() -> None:
    tracker = MemoryTracker()
    with tracker.measure():
        data = bytearray(1024 * 1024)

    metrics = tracker.last_metrics
    assert metrics is not None
    assert metrics.runtime_seconds >= 0.0
    assert metrics.memory_before_mb >= 0.0
    assert metrics.memory_after_mb >= metrics.memory_before_mb
    assert metrics.memory_delta_mb >= 0.0
    assert metrics.peak_memory_mb >= metrics.memory_after_mb
    del data


def test_memory_metrics_to_dict() -> None:
    metrics = MemoryMetrics(
        runtime_seconds=1.2,
        memory_before_mb=100.0,
        memory_after_mb=120.0,
        memory_delta_mb=20.0,
        peak_memory_mb=125.0,
    )
    payload = metrics.to_dict()
    assert payload == {
        "runtime_seconds": 1.2,
        "memory_before_mb": 100.0,
        "memory_after_mb": 120.0,
        "memory_delta_mb": 20.0,
        "peak_memory_mb": 125.0,
    }


def test_memory_tracker_peak_sampling() -> None:
    tracker = MemoryTracker()
    tracker.sample()
    first_peak = tracker.peak_rss_mb
    _ = bytearray(512 * 1024)
    tracker.sample()
    assert tracker.peak_rss_mb >= first_peak


def test_memory_tracker_warning_threshold(caplog: pytest.LogCaptureFixture) -> None:
    tracker = MemoryTracker(warning_threshold_mb=0.0)
    with caplog.at_level(logging.WARNING, logger="timeseriesflow.memory"), tracker.measure():
        _ = bytearray(1024 * 1024)
    assert any("exceeded threshold" in record.message for record in caplog.records)


def test_memory_tracker_disabled_has_minimal_overhead() -> None:
    tracker = MemoryTracker(enabled=False)
    with tracker.measure():
        pass
    metrics = tracker.last_metrics
    assert metrics is not None
    assert metrics.memory_before_mb == 0.0
    assert metrics.memory_after_mb == 0.0
    assert metrics.memory_delta_mb == 0.0


@track_memory
def tracked_function() -> list[int]:
    return list(range(1000))


def test_track_memory_decorator() -> None:
    result = tracked_function()
    assert result == list(range(1000))
    metrics = tracked_function.last_metrics
    assert metrics is not None
    assert "runtime_seconds" in metrics.to_dict()
    assert metrics.memory_delta_mb >= 0.0


@track_memory(warning_threshold_mb=99999.0)
def tracked_with_options() -> int:
    return 42


def test_track_memory_decorator_with_options() -> None:
    assert tracked_with_options() == 42
    assert tracked_with_options.last_metrics is not None


def test_memory_tracker_start_finish() -> None:
    tracker = MemoryTracker()
    tracker.start()
    _ = [0] * 10_000
    metrics = tracker.finish()
    assert isinstance(metrics, MemoryMetrics)
    assert metrics.runtime_seconds >= 0.0
