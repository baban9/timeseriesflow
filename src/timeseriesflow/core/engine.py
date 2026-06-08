"""Core flow execution engine."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pandas as pd

from timeseriesflow.checkpoint import CheckpointBackend, LocalCheckpoint
from timeseriesflow.core.entity import iter_entity_groups, list_entities
from timeseriesflow.core.processor import EntityProcessor, call_processor, validate_processor
from timeseriesflow.exceptions import EntityProcessingError, FlowError
from timeseriesflow.logging import get_logger, setup_logging
from timeseriesflow.memory import MemoryTracker
from timeseriesflow.progress import ProgressTracker, RunSummary, build_summary
from timeseriesflow.types import EntityId, FlowEntityResult

if TYPE_CHECKING:
    from timeseriesflow.checkpoint import CheckpointStore
    from timeseriesflow.config import FlowConfig

logger = get_logger("engine")


class Flow:
    """Orchestrates entity-based time-series processing.

    .. note::
        Legacy API. Prefer ``@entity_flow`` with ``EntityRunner`` for new
        projects. ``Flow`` will emit a deprecation warning starting in v0.2.
    """

    def __init__(
        self,
        processor: EntityProcessor,
        config: FlowConfig,
        *,
        checkpoint: CheckpointBackend | CheckpointStore | None = None,
    ) -> None:
        validate_processor(processor)
        self.processor = processor
        self.config = config
        self.checkpoint = self._resolve_checkpoint(checkpoint)
        setup_logging(self.config.log_level)  # type: ignore[arg-type]

    def _resolve_checkpoint(
        self,
        checkpoint: CheckpointBackend | CheckpointStore | None,
    ) -> CheckpointBackend | None:
        if checkpoint is not None:
            if isinstance(checkpoint, CheckpointBackend):
                return checkpoint
            from timeseriesflow.checkpoint import FileCheckpointStore

            if isinstance(checkpoint, FileCheckpointStore):
                return checkpoint.backend
            raise TypeError("checkpoint must be CheckpointBackend or FileCheckpointStore")
        return self._build_checkpoint()

    def _build_checkpoint(self) -> CheckpointBackend | None:
        if self.config.checkpoint_dir is None:
            return None
        return LocalCheckpoint(self.config.checkpoint_dir)

    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame | None, RunSummary]:
        """Process all entities in df and return combined output plus summary."""
        start = time.perf_counter()
        entities = list_entities(
            df,
            self.config.entity_column,
            sort=self.config.sort_entities,
        )
        if self.config.max_entities is not None:
            entities = entities[: self.config.max_entities]

        completed: set[EntityId] = set()
        if self.config.resume and self.checkpoint is not None:
            completed = self.checkpoint.load_completed()
            if completed:
                logger.info("Resuming run; skipping %d completed entities", len(completed))

        pending = [entity_id for entity_id in entities if entity_id not in completed]
        skipped = len(entities) - len(pending)

        progress = ProgressTracker(enabled=self.config.show_progress)
        memory_tracker = MemoryTracker()
        if not self.config.track_memory:
            memory_tracker.disable()

        results: list[FlowEntityResult] = []
        output_frames: list[pd.DataFrame] = []

        progress.start(len(pending))
        try:
            for entity_id, entity_df in iter_entity_groups(
                df,
                self.config.entity_column,
                sort_entities=self.config.sort_entities,
                max_entities=self.config.max_entities,
                skip=completed,
            ):
                result = self._process_entity(entity_id, entity_df, memory_tracker)
                results.append(result)
                progress.advance(entity_id, success=result.success)

                if result.success and result.dataframe is not None:
                    output_frames.append(result.dataframe)
                elif result.failed and self.config.fail_fast:
                    raise EntityProcessingError(
                        entity_id=entity_id,
                        message="fail_fast enabled",
                        cause=result.error,
                    )
        finally:
            progress.stop()

        combined = pd.concat(output_frames, ignore_index=True) if output_frames else None
        total_duration = time.perf_counter() - start
        summary = build_summary(
            total_entities=len(entities),
            results=results,
            skipped=skipped,
            total_duration_seconds=total_duration,
            peak_memory_mb=memory_tracker.peak_rss_mb,
        )
        progress.print_summary(summary)
        logger.info(
            "Flow finished: %d succeeded, %d failed, %d skipped in %.2fs",
            summary.succeeded,
            summary.failed,
            summary.skipped,
            summary.total_duration_seconds,
        )
        return combined, summary

    def _process_entity(
        self,
        entity_id: EntityId,
        entity_df: pd.DataFrame,
        memory_tracker: MemoryTracker,
    ) -> FlowEntityResult:
        memory_tracker.reset()
        memory_tracker.sample()
        start = time.perf_counter()
        attempts = 0
        last_error: BaseException | None = None

        def _invoke() -> pd.DataFrame:
            nonlocal attempts
            attempts += 1
            return call_processor(
                self.processor,
                entity_df,
                entity_id,
                self.config.entity_column,
                attempts,
            )

        try:
            output = self.config.retry_policy.run(_invoke, entity_id=entity_id)
            duration = time.perf_counter() - start
            memory_tracker.sample()
            result = FlowEntityResult(
                entity_id=entity_id,
                success=True,
                dataframe=output,
                attempts=attempts,
                duration_seconds=duration,
                peak_memory_mb=memory_tracker.peak_rss_mb,
            )
            self._checkpoint(result)
            return result
        except BaseException as exc:
            duration = time.perf_counter() - start
            memory_tracker.sample()
            last_error = exc
            if not isinstance(exc, FlowError):
                logger.exception("Unexpected error processing entity %r", entity_id)
            else:
                logger.warning("Entity %r failed after %d attempt(s): %s", entity_id, attempts, exc)
            result = FlowEntityResult(
                entity_id=entity_id,
                success=False,
                error=last_error,
                attempts=max(attempts, 1),
                duration_seconds=duration,
                peak_memory_mb=memory_tracker.peak_rss_mb,
            )
            self._checkpoint(result)
            return result

    def _checkpoint(self, result: FlowEntityResult) -> None:
        if self.checkpoint is None:
            return
        if result.success:
            self.checkpoint.mark_completed(
                result.entity_id,
                runtime_seconds=result.duration_seconds,
                memory_delta_mb=result.peak_memory_mb,
                attempts=result.attempts,
                metadata=result.metadata,
            )
            return
        self.checkpoint.mark_failed(
            result.entity_id,
            error=result.error,
            runtime_seconds=result.duration_seconds,
            memory_delta_mb=result.peak_memory_mb,
            attempts=result.attempts,
            metadata=result.metadata,
        )
