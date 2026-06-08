"""tsflow run command."""

from __future__ import annotations

from pathlib import Path

import typer

from timeseriesflow.cli.console import console, print_error, print_info, print_panel, print_success
from timeseriesflow.cli.errors import CliError
from timeseriesflow.cli.pipeline import (
    execute_pipeline,
    load_pipeline_module,
    resolve_pipeline_path,
)
from timeseriesflow.logging import setup_logging
from timeseriesflow.progress import RunSummary


def run_command(
    pipeline: Path = typer.Argument(
        ...,
        help="Path to a pipeline Python script.",
        exists=False,
        readable=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable debug logging.",
    ),
) -> None:
    """Run an entity processing pipeline.

    Example:

        tsflow run examples/basic_pipeline.py
    """
    setup_logging("DEBUG" if verbose else "INFO")

    try:
        path = resolve_pipeline_path(pipeline)
        print_info(f"Loading pipeline [accent]{path}[/accent]")
        module = load_pipeline_module(path)
        result = execute_pipeline(module, path=path)
    except CliError as exc:
        print_error(exc.format())
        raise typer.Exit(code=1) from exc

    if isinstance(result, RunSummary):
        print_panel(
            "Run complete",
            f"""[success]{result.succeeded}[/success] succeeded
[error]{result.failed}[/error] failed
[muted]{result.skipped}[/muted] skipped
[info]{result.total_retries}[/info] retries
[muted]{result.total_duration_seconds:.2f}s[/muted] elapsed
[muted]{result.peak_memory_mb:.1f} MB[/muted] peak memory""",
            style="green" if result.failed == 0 else "yellow",
        )
    else:
        print_success(f"Pipeline finished: {path.name}")

    console.print("[muted]Tip:[/muted] use [accent]tsflow validate[/accent] before running in CI.")
