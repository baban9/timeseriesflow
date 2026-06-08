"""Tests for checkpoint backends."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.checkpoint.io import append_jsonl_line
from timeseriesflow.checkpoint.models import CheckpointStatus
from timeseriesflow.exceptions import CheckpointError


@pytest.fixture
def checkpoint(tmp_path: Path) -> LocalCheckpoint:
    return LocalCheckpoint(tmp_path / "run-checkpoints")


def test_mark_completed_and_load(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("device-1", runtime_seconds=1.5, memory_delta_mb=2.0)

    assert checkpoint.is_completed("device-1") is True
    assert checkpoint.load_completed() == {"device-1"}
    assert checkpoint.load_failed() == set()


def test_mark_failed_and_load(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_failed("device-2", error=ValueError("timeout"))

    assert checkpoint.is_completed("device-2") is False
    assert checkpoint.load_failed() == {"device-2"}
    assert "device-2" not in checkpoint.load_completed()


def test_mark_completed_is_idempotent(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("device-1")
    checkpoint.mark_completed("device-1")
    checkpoint.mark_completed("device-1")

    summary = checkpoint.summary()
    assert summary.completed_count == 1
    assert summary.total_entries == 1


def test_mark_failed_after_completed_is_noop(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("device-1")
    checkpoint.mark_failed("device-1", error=RuntimeError("late failure"))

    assert checkpoint.is_completed("device-1") is True
    assert checkpoint.load_failed() == set()
    assert checkpoint.summary().total_entries == 1


def test_latest_status_wins_on_retry(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_failed("device-1", error="first failure")
    assert checkpoint.load_failed() == {"device-1"}

    checkpoint.mark_completed("device-1")
    assert checkpoint.is_completed("device-1") is True
    assert checkpoint.load_failed() == set()


def test_summary_counts(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("a")
    checkpoint.mark_completed("b")
    checkpoint.mark_failed("c", error="err")

    summary = checkpoint.summary()
    assert summary.completed_count == 2
    assert summary.failed_count == 1
    assert summary.total_entries == 3
    assert summary.tracked_entities == 3


def test_resume_skips_only_completed(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("done")
    checkpoint.mark_failed("retry-me", error="fail")

    completed = checkpoint.load_completed()
    failed = checkpoint.load_failed()

    assert "done" in completed
    assert "retry-me" in failed
    assert checkpoint.should_skip("done") is True
    assert checkpoint.should_skip("retry-me") is False


def test_append_only_jsonl_format(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("x", runtime_seconds=0.1)
    log_path = checkpoint.log_path

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["entity_id"] == "x"
    assert payload["status"] == CheckpointStatus.COMPLETED.value


def test_crash_safe_truncated_line_is_ignored(tmp_path: Path) -> None:
    log_path = tmp_path / "checkpoints.jsonl"
    append_jsonl_line(log_path, {"entity_id": "ok", "status": "completed", "recorded_at": "t"})
    log_path.open("a", encoding="utf-8").write('{"entity_id": "bad", "stat')

    checkpoint = LocalCheckpoint(tmp_path)
    assert checkpoint.load_completed() == {"ok"}


def test_corrupt_middle_line_raises(tmp_path: Path) -> None:
    log_path = tmp_path / "checkpoints.jsonl"
    append_jsonl_line(log_path, {"entity_id": "a", "status": "completed", "recorded_at": "t"})
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("{not valid json}\n")
    append_jsonl_line(log_path, {"entity_id": "b", "status": "completed", "recorded_at": "t"})

    checkpoint = LocalCheckpoint(tmp_path)
    with pytest.raises(CheckpointError, match="corrupt checkpoint entry"):
        checkpoint.load_completed()


def test_clear_removes_state(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("a")
    checkpoint.clear()
    assert checkpoint.load_completed() == set()
    assert checkpoint.summary().total_entries == 0


def test_state_cache_invalidated_on_write(checkpoint: LocalCheckpoint) -> None:
    checkpoint.mark_completed("a")
    assert checkpoint.is_completed("a") is True

    checkpoint.mark_completed("b")
    assert checkpoint.is_completed("b") is True
    assert checkpoint.load_completed() == {"a", "b"}


def test_entity_flow_resume_with_checkpoint(sample_df, tmp_path) -> None:
    from timeseriesflow import EntityContext, entity_flow

    @entity_flow(
        entity_key="sensor_id",
        time_key="timestamp",
        checkpoint_dir=tmp_path / "ckpt",
    )
    def count_rows(df, ctx: EntityContext) -> int:
        return len(df)

    first = count_rows.run(sample_df)
    assert first.processed == 3
    assert first.skipped == 0

    second = count_rows.run(sample_df)
    assert second.processed == 0
    assert second.skipped == 3
