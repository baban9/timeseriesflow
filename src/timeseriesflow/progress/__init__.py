"""Progress tracking and run summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn

from timeseriesflow.types import EntityId, FlowEntityResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from timeseriesflow.api.result import EntityResult


@dataclass(slots=True)
class RunSummary:
    """Aggregate statistics for a completed entity run."""

    total_entities: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    total_duration_seconds: float
    peak_memory_mb: float
    results: list[Any] = field(default_factory=list)
    batches_processed: int = 0
    total_retries: int = 0

    @property
    def success_rate(self) -> float:
        if self.processed == 0:
            return 0.0
        return self.succeeded / self.processed


class ProgressTracker:
    """Rich-based progress display for entity processing."""

    def __init__(self, *, enabled: bool = True, console: Console | None = None) -> None:
        self.enabled = enabled
        self.console = console or Console()
        self._progress: Progress | None = None
        self._task_id: int | None = None

    def start(self, total: int, description: str = "Processing entities") -> None:
        if not self.enabled:
            return
        self._progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(description, total=total)

    def advance(self, entity_id: EntityId, *, success: bool) -> None:
        if not self.enabled or self._progress is None or self._task_id is None:
            return
        status = "ok" if success else "fail"
        self._progress.update(
            self._task_id,
            advance=1,
            description=f"Processing entities ({entity_id!r} {status})",
        )

    def stop(self) -> None:
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
            self._task_id = None

    def print_summary(self, summary: RunSummary) -> None:
        if not self.enabled:
            return
        self.console.print(
            f"\n[bold]Run complete[/bold]: "
            f"{summary.succeeded}/{summary.processed} succeeded, "
            f"{summary.failed} failed, "
            f"{summary.skipped} skipped "
            f"({summary.total_duration_seconds:.2f}s, "
            f"peak {summary.peak_memory_mb:.1f} MB)"
        )


def build_summary(
    *,
    total_entities: int,
    results: Sequence["FlowEntityResult | EntityResult"],
    skipped: int,
    total_duration_seconds: float,
    peak_memory_mb: float,
    batches_processed: int = 0,
    total_retries: int = 0,
) -> RunSummary:
    succeeded = sum(1 for result in results if result.success)
    failed = sum(1 for result in results if result.failed)
    return RunSummary(
        total_entities=total_entities,
        processed=len(results),
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        total_duration_seconds=total_duration_seconds,
        peak_memory_mb=peak_memory_mb,
        results=list(results),
        batches_processed=batches_processed,
        total_retries=total_retries,
    )
