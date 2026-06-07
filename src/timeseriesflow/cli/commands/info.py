"""tsflow info command."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import typer

from timeseriesflow import __version__
from timeseriesflow.cli.console import console, print_key_values, print_panel


def info_command(
    checkpoint_dir: Path | None = typer.Option(
        None,
        "--checkpoint-dir",
        "-c",
        help="Optional checkpoint directory to summarize.",
    ),
) -> None:
    """Show TimeSeriesFlow environment and tooling information.

    Example:

        tsflow info
        tsflow info --checkpoint-dir ./checkpoints
    """
    print_panel(
        "TimeSeriesFlow",
        "Entity-based time-series processing for Python.\n"
        "Write one function per entity; the framework handles the rest.",
    )

    print_key_values(
        "Environment",
        [
            ("Version", __version__),
            ("Python", sys.version.split()[0]),
            ("Platform", platform.platform()),
            ("Executable", sys.executable),
        ],
    )

    console.print()
    console.print("[accent]Quick start[/accent]")
    console.print("  [muted]tsflow run[/muted] examples/basic_pipeline.py")
    console.print("  [muted]tsflow validate[/muted] examples/basic_pipeline.py")
    console.print("  [muted]tsflow checkpoint-status[/muted] --checkpoint-dir ./checkpoints")

    if checkpoint_dir is None:
        return

    from timeseriesflow.checkpoint import LocalCheckpoint

    resolved = checkpoint_dir.expanduser().resolve()
    if not resolved.exists():
        console.print()
        console.print(f"[error]Checkpoint directory not found:[/error] {resolved}")
        raise typer.Exit(code=1)

    backend = LocalCheckpoint(resolved)
    summary = backend.summary()
    console.print()
    print_key_values(
        "Checkpoint summary",
        [
            ("Directory", str(resolved)),
            ("Completed", str(summary.completed_count)),
            ("Failed", str(summary.failed_count)),
            ("Log entries", str(summary.total_entries)),
        ],
    )
