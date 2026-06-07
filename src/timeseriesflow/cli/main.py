"""TimeSeriesFlow CLI (tsflow)."""

from __future__ import annotations

import typer

from timeseriesflow import __version__
from timeseriesflow.cli.commands.checkpoint_status import checkpoint_status_command
from timeseriesflow.cli.commands.info import info_command
from timeseriesflow.cli.commands.run import run_command
from timeseriesflow.cli.commands.validate import validate_command
from timeseriesflow.cli.console import print_error
from timeseriesflow.cli.errors import CliError

app = typer.Typer(
    name="tsflow",
    help="[bold]TimeSeriesFlow[/bold] - entity-based time-series processing.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
)

app.command("run", help="Run a pipeline script.")(run_command)
app.command("validate", help="Validate a pipeline script without running it.")(validate_command)
app.command("info", help="Show environment and tooling information.")(info_command)
app.command(
    "checkpoint-status",
    help="Inspect checkpoint progress for a resumable run.",
)(checkpoint_status_command)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the installed version and exit.",
        is_eager=True,
    ),
) -> None:
    """TimeSeriesFlow command-line interface."""
    if version:
        typer.echo(f"tsflow {__version__}")
        raise typer.Exit()


def main() -> None:
    """CLI entry point."""
    try:
        app()
    except CliError as exc:
        print_error(exc.format())
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
