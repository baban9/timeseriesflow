"""tsflow checkpoint-status command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from timeseriesflow.checkpoint import LocalCheckpoint
from timeseriesflow.cli.console import console, print_key_values, print_panel
from timeseriesflow.cli.errors import CliError


def checkpoint_status_command(
    checkpoint_dir: Path = typer.Option(
        ...,
        "--checkpoint-dir",
        "-c",
        help="Checkpoint directory to inspect.",
    ),
    show_entities: bool = typer.Option(
        False,
        "--show-entities",
        help="List completed and failed entity IDs.",
    ),
) -> None:
    """Show detailed checkpoint status for a resumable run.

    Example:

        tsflow checkpoint-status --checkpoint-dir ./checkpoints
    """
    resolved = checkpoint_dir.expanduser().resolve()
    if not resolved.exists():
        raise CliError(
            f"Checkpoint directory not found: {checkpoint_dir}",
            hint="Run a pipeline with checkpointing enabled first.",
        )

    backend = LocalCheckpoint(resolved)
    summary = backend.summary()

    if summary.total_entries == 0:
        print_panel(
            "Checkpoint status",
            f"No checkpoint data found in [accent]{resolved}[/accent].\n\n"
            "Run a pipeline with LocalCheckpoint to create checkpoints.",
            style="yellow",
        )
        return

    total_tracked = summary.tracked_entities
    completed_pct = (summary.completed_count / total_tracked * 100) if total_tracked else 0.0

    print_panel(
        "Checkpoint status",
        f"""Directory: [accent]{resolved}[/accent]
Completed: [success]{summary.completed_count}[/success]
Failed: [error]{summary.failed_count}[/error]
Total log entries: [muted]{summary.total_entries}[/muted]
Progress: [info]{completed_pct:.1f}%[/info] entities completed""",
    )

    print_key_values(
        "Counts",
        [
            ("Completed entities", str(summary.completed_count)),
            ("Failed entities", str(summary.failed_count)),
            ("Unique tracked", str(total_tracked)),
            ("Append-only entries", str(summary.total_entries)),
        ],
    )

    if not show_entities:
        console.print()
        console.print(
            "[muted]Tip:[/muted] add [accent]--show-entities[/accent] to list entity IDs."
        )
        return

    table = Table(title="Entity checkpoint state")
    table.add_column("Status", style="bold")
    table.add_column("Entity ID")

    for entity_id in sorted(summary.completed_entities, key=str):
        table.add_row("[success]completed[/success]", str(entity_id))
    for entity_id in sorted(summary.failed_entities, key=str):
        table.add_row("[error]failed[/error]", str(entity_id))

    console.print()
    console.print(table)
