"""Command-line interface for TimeSeriesFlow."""

from __future__ import annotations

from pathlib import Path

import typer

from timeseriesflow import __version__

app = typer.Typer(
    name="timeseriesflow",
    help="Entity-based time-series processing framework.",
    no_args_is_help=True,
)


@app.command("version")
def version() -> None:
    """Print the installed package version."""
    typer.echo(f"timeseriesflow {__version__}")


@app.command("info")
def info(
    checkpoint_dir: Path | None = typer.Option(
        None,
        "--checkpoint-dir",
        "-c",
        help="Checkpoint directory to inspect.",
    ),
) -> None:
    """Show framework info and optional checkpoint status."""
    typer.echo(f"TimeSeriesFlow v{__version__}")
    typer.echo("Entity-based time-series processing framework")
    if checkpoint_dir is None:
        return
    if not checkpoint_dir.exists():
        typer.echo(f"Checkpoint directory not found: {checkpoint_dir}")
        raise typer.Exit(code=1)
    index = checkpoint_dir / "index.jsonl"
    if not index.exists():
        typer.echo(f"No checkpoints in {checkpoint_dir}")
        return
    lines = index.read_text(encoding="utf-8").strip().splitlines()
    typer.echo(f"Checkpoint entries: {len(lines)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
