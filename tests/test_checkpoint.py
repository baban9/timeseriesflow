"""Tests for legacy checkpoint store compatibility."""

from __future__ import annotations

from timeseriesflow.checkpoint import FileCheckpointStore, LocalCheckpoint, build_checkpoint_record


def test_file_checkpoint_store_roundtrip(tmp_path) -> None:
    store = FileCheckpointStore(tmp_path / "ckpt")
    record = build_checkpoint_record(
        entity_id="sensor-1",
        success=True,
        attempts=1,
        duration_seconds=0.5,
        peak_memory_mb=12.3,
        metadata={"rows": 100},
    )
    store.save(record)

    completed = store.load_completed_entities()
    assert "sensor-1" in completed
    assert isinstance(store.backend, LocalCheckpoint)


def test_file_checkpoint_store_clear(tmp_path) -> None:
    store = FileCheckpointStore(tmp_path / "ckpt")
    record = build_checkpoint_record(
        entity_id="sensor-1",
        success=True,
        attempts=1,
        duration_seconds=0.5,
        peak_memory_mb=12.3,
    )
    store.save(record)
    store.clear()
    assert store.load_completed_entities() == set()
