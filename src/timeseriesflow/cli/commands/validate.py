"""tsflow validate command."""

from __future__ import annotations

from pathlib import Path

import typer

from timeseriesflow.cli.console import print_error, print_info, print_success
from timeseriesflow.cli.errors import CliError
from timeseriesflow.cli.pipeline import (
    find_entry_point,
    load_pipeline_module,
    resolve_pipeline_path,
    validate_pipeline_module,
)


def validate_command(
    pipeline: Path = typer.Argument(
        ...,
        help="Path to a pipeline Python script.",
        exists=False,
        readable=True,
    ),
) -> None:
    """Validate a pipeline script without executing it.

    Checks syntax, imports, entry points, and optional validate() hooks.

    Example:

        tsflow validate examples/basic_pipeline.py
    """
    try:
        path = resolve_pipeline_path(pipeline)
        print_info(f"Validating [accent]{path}[/accent]")
        module = load_pipeline_module(path)
        entry = validate_pipeline_module(module, path=path)
    except CliError as exc:
        print_error(exc.format())
        raise typer.Exit(code=1) from exc

    print_success(f"Pipeline is valid (entry point: {entry}())")
