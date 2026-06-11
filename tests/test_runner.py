"""Tests for EntityRunner."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from timeseriesflow import EntityContext, EntityRunner, entity_flow
from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.exceptions import EntityProcessingError
from timeseriesflow.progress import RunSummary
from timeseriesflow.retry import RetryPolicy
from timeseriesflow.sources import CSVSource, SourceSchema


def _write_csv(path: Path, devices: int = 5, points: int = 3) -> None:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for device_id in range(devices):
        for minute in range(points):
            rows.append(
                {
                    "device_id": f"D-{device_id:03d}",
                    "timestamp": base + timedelta(minutes=minute),
                    "value": float(minute),
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


@entity_flow(entity_key="device_id", time_key="timestamp")
def count_rows(df: pd.DataFrame, ctx: EntityContext) -> dict[str, int]:
    return {"rows": len(df)}


_flaky_state: dict[str, int] = {}


@entity_flow(entity_key="device_id", time_key="timestamp")
def flaky_once(df: pd.DataFrame, ctx: EntityContext) -> dict[str, int]:
    key = str(ctx.entity_id)
    _flaky_state[key] = _flaky_state.get(key, 0) + 1
    if _flaky_state[key] == 1:
        raise RuntimeError("transient failure")
    return {"rows": len(df)}


@entity_flow(entity_key="device_id", time_key="timestamp")
def always_fail(df: pd.DataFrame, ctx: EntityContext) -> dict[str, int]:
    raise ValueError("permanent failure")


_parallel_lock = threading.Lock()
_parallel_active = 0
_parallel_peak = 0


@entity_flow(entity_key="device_id", time_key="timestamp")
def slow_count_rows(df: pd.DataFrame, ctx: EntityContext) -> dict[str, int]:
    global _parallel_active, _parallel_peak
    with _parallel_lock:
        _parallel_active += 1
        _parallel_peak = max(_parallel_peak, _parallel_active)
    try:
        time.sleep(0.05)
        return {"rows": len(df)}
    finally:
        with _parallel_lock:
            _parallel_active -= 1


def test_entity_runner_basic(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=3)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    runner = EntityRunner(
        source=source,
        flow=count_rows,
        batch_size=2,
        retries=1,
        show_progress=False,
    )
    summary = runner.run()

    assert isinstance(summary, RunSummary)
    assert summary.total_entities == 3
    assert summary.processed == 3
    assert summary.succeeded == 3
    assert summary.failed == 0
    assert summary.batches_processed == 2


def test_entity_runner_checkpoint_resume(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=4)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    checkpoint = LocalCheckpoint(tmp_path / "ckpt")

    runner = EntityRunner(
        source=source,
        flow=count_rows,
        checkpoint=checkpoint,
        batch_size=10,
        show_progress=False,
    )
    first = runner.run()
    assert first.succeeded == 4

    second = EntityRunner(
        source=source,
        flow=count_rows,
        checkpoint=checkpoint,
        show_progress=False,
    ).run()
    assert second.skipped == 4
    assert second.processed == 0


def test_entity_runner_retries(tmp_path: Path) -> None:
    _flaky_state.clear()
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=1)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    runner = EntityRunner(
        source=source,
        flow=flaky_once,
        retries=3,
        retry_policy=RetryPolicy(max_attempts=3, initial_delay_seconds=0.01, jitter=False),
        show_progress=False,
    )
    summary = runner.run()

    assert summary.succeeded == 1
    assert summary.total_retries == 1


def test_entity_runner_failure_recorded(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=2)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    checkpoint = LocalCheckpoint(tmp_path / "ckpt")
    runner = EntityRunner(
        source=source,
        flow=always_fail,
        checkpoint=checkpoint,
        retries=1,
        show_progress=False,
    )
    summary = runner.run()

    assert summary.failed == 2
    assert summary.succeeded == 0
    assert len(checkpoint.load_failed()) == 2


def test_entity_runner_fail_fast(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=3)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    runner = EntityRunner(
        source=source,
        flow=always_fail,
        retries=1,
        fail_fast=True,
        show_progress=False,
    )
    with pytest.raises(EntityProcessingError):
        runner.run()


def test_entity_runner_invalid_batch_size(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=1)
    source = CSVSource(csv_path, parse_dates=["timestamp"])
    with pytest.raises(ValueError, match="batch_size"):
        EntityRunner(source=source, flow=count_rows, batch_size=0)


def test_entity_runner_parallel_workers(tmp_path: Path) -> None:
    global _parallel_peak
    _parallel_peak = 0
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=8)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    runner = EntityRunner(
        source=source,
        flow=slow_count_rows,
        workers=4,
        batch_size=8,
        show_progress=False,
    )
    summary = runner.run()

    assert summary.succeeded == 8
    assert _parallel_peak >= 2


def test_entity_runner_parallel_checkpoint_resume(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=6)

    schema = SourceSchema(required_columns=("device_id", "timestamp", "value"))
    source = CSVSource(csv_path, parse_dates=["timestamp"], schema=schema)
    checkpoint = LocalCheckpoint(tmp_path / "ckpt")
    runner = EntityRunner(
        source=source,
        flow=count_rows,
        checkpoint=checkpoint,
        workers=3,
        batch_size=3,
        show_progress=False,
    )
    first = runner.run()
    assert first.succeeded == 6

    second = EntityRunner(
        source=source,
        flow=count_rows,
        checkpoint=checkpoint,
        workers=3,
        show_progress=False,
    ).run()
    assert second.skipped == 6
    assert second.processed == 0


def test_entity_runner_invalid_workers(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=1)
    source = CSVSource(csv_path, parse_dates=["timestamp"])
    with pytest.raises(ValueError, match="workers"):
        EntityRunner(source=source, flow=count_rows, workers=0)


def test_entity_runner_success_rate(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path, devices=2)
    source = CSVSource(csv_path, parse_dates=["timestamp"])
    summary = EntityRunner(source=source, flow=count_rows, show_progress=False).run()
    assert summary.success_rate == 1.0
