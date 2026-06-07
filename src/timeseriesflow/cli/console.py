"""Rich console helpers for the tsflow CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

TSFLOW_THEME = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "muted": "dim",
        "accent": "bold cyan",
    }
)

console = Console(theme=TSFLOW_THEME)


def print_success(message: str) -> None:
    console.print(f"[success]✓[/success] {message}")


def print_error(message: str) -> None:
    console.print(f"[error]✗[/error] {message}")


def print_warning(message: str) -> None:
    console.print(f"[warning]![/warning] {message}")


def print_info(message: str) -> None:
    console.print(f"[info]→[/info] {message}")


def print_panel(title: str, body: str, *, style: str = "cyan") -> None:
    console.print(Panel(body.strip(), title=title, border_style=style))


def print_key_values(title: str, rows: list[tuple[str, str]]) -> None:
    table = Table(title=title, show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="muted")
    table.add_column("value")
    for key, value in rows:
        table.add_row(key, value)
    console.print(table)
