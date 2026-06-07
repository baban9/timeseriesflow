"""Tests for the tsflow CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from typer.testing import CliRunner

from timeseriesflow.cli.main import app

runner = CliRunner()
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
PIPELINE = EXAMPLES / "basic_pipeline.py"


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "tsflow" in result.stdout


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "validate" in result.stdout
    assert "checkpoint-status" in result.stdout


def test_cli_info() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "TimeSeriesFlow" in result.stdout
    assert "Quick start" in result.stdout


def test_cli_validate_pipeline() -> None:
    result = runner.invoke(app, ["validate", str(PIPELINE)])
    assert result.exit_code == 0
    assert "valid" in result.stdout.lower()


def test_cli_run_pipeline() -> None:
    result = runner.invoke(app, ["run", str(PIPELINE)])
    assert result.exit_code == 0
    assert "Run complete" in result.stdout or "finished" in result.stdout.lower()


def test_cli_validate_missing_file() -> None:
    result = runner.invoke(app, ["validate", "missing_pipeline.py"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "✗" in result.stdout


def test_cli_validate_invalid_entry_point(tmp_path: Path) -> None:
    bad_pipeline = tmp_path / "bad.py"
    bad_pipeline.write_text("def nothing(): pass\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(bad_pipeline)])
    assert result.exit_code == 1
    assert "entry point" in result.stdout.lower()


def test_cli_checkpoint_status_empty(tmp_path: Path) -> None:
    checkpoint_dir = tmp_path / "ckpt"
    checkpoint_dir.mkdir()
    result = runner.invoke(
        app,
        ["checkpoint-status", "--checkpoint-dir", str(checkpoint_dir)],
    )
    assert result.exit_code == 0
    assert "No checkpoint data" in result.stdout or "Checkpoint status" in result.stdout


def test_cli_checkpoint_status_with_data(tmp_path: Path) -> None:
    from timeseriesflow.checkpoint import LocalCheckpoint

    checkpoint_dir = tmp_path / "ckpt"
    backend = LocalCheckpoint(checkpoint_dir)
    backend.mark_completed("device-1")
    backend.mark_failed("device-2", error="test")

    result = runner.invoke(
        app,
        ["checkpoint-status", "--checkpoint-dir", str(checkpoint_dir), "--show-entities"],
    )
    assert result.exit_code == 0
    assert "device-1" in result.stdout
    assert "device-2" in result.stdout


def test_cli_run_help() -> None:
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "pipeline" in result.stdout.lower()
