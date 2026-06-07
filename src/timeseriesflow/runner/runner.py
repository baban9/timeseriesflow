"""EntityRunner orchestration implementation."""

from __future__ import annotations

import time

import pandas as pd

from timeseriesflow.api.decorator import EntityFlowFunction
from timeseriesflow.api.flow import EntityFlow
from timeseriesflow.api.result import EntityResult
from timeseriesflow.checkpoint import CheckpointBackend
from timeseriesflow.core.entity import list_entities
from timeseriesflow.exceptions import EntityProcessingError
from timeseriesflow.logging import get_logger, setup_logging
from timeseriesflow.memory import MemoryTracker
from timeseriesflow.progress import ProgressTracker, RunSummary, build_summary
from timeseriesflow.retry import RetryPolicy
from timeseriesflow.sources.base import TabularSource
from timeseriesflow.types import EntityId

logger = get_logger("runner")


def _chunked(items: list[EntityId], size: int) -> list[list[EntityId]]:
    if size <= 0:
        raise ValueError("batch_size must be positive")
    return [items[index : index + size] for index in range(0, len(items), size)]


class EntityRunner:
    """End-to-end orchestrator for entity-based time-series processing.

    Loads data from a source, discovers entities, executes an entity flow
    in batches with retries, updates checkpoints, and tracks progress.

    Example:
        runner = EntityRunner(
            source=CSVSource("data.csv", parse_dates=["timestamp"]),
            flow=my_flow,
            checkpoint=LocalCheckpoint("./checkpoints"),
            batch_size=100,
            retries=3,
        )
        summary = runner.run()
    """

    def __init__(
        self,
        *,
        source: TabularSource,
        flow: EntityFlow | EntityFlowFunction,
        checkpoint: CheckpointBackend | None = None,
        batch_size: int = 100,
        retries: int = 3,
        resume: bool = True,
        fail_fast: bool = False,
        show_progress: bool = True,
        log_level: str = "INFO",
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if retries < 1:
            raise ValueError("retries must be at least 1")
        self.source = source
        self.flow = self._resolve_flow(flow)
        self.checkpoint = checkpoint
        self.batch_size = batch_size
        self.retries = retries
        self.resume = resume
        self.fail_fast = fail_fast
        self.show_progress = show_progress
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=retries, jitter=False)
        setup_logging(log_level)  # type: ignore[arg-type]
        self._logger = get_logger("runner")

    @staticmethod
    def _resolve_flow(flow: EntityFlow | EntityFlowFunction) -> EntityFlow:
        if isinstance(flow, EntityFlowFunction):
            return flow.flow
        if isinstance(flow, EntityFlow):
            return flow
        raise TypeError("flow must be EntityFlow or an @entity_flow decorated function")

    def run(self) -> RunSummary:
        """Load source data, process entities, and return run statistics."""
        start = time.perf_counter()
        memory_tracker = MemoryTracker()

        self._logger.info("Validating source %s", self.source.source_name)
        self.source.validate()
        df = self.source.load()
        memory_tracker.sample()

        entities = list_entities(df, self.flow.entity_key, sort=self.flow.sort_entities)
        completed = self._load_completed_entities()
        pending = [entity_id for entity_id in entities if entity_id not in completed]
        skipped = len(entities) - len(pending)

        if skipped:
            self._logger.info("Resuming run; skipping %d completed entities", skipped)

        progress = ProgressTracker(enabled=self.show_progress)
        results: list[EntityResult] = []
        total_retries = 0
        batches = _chunked(pending, self.batch_size)
        grouped = df.groupby(self.flow.entity_key, sort=False)

        progress.start(len(pending), description="EntityRunner")
        try:
            for batch_index, batch in enumerate(batches, start=1):
                self._logger.info(
                    "Processing batch %d/%d (%d entities)",
                    batch_index,
                    len(batches),
                    len(batch),
                )
                for entity_id in batch:
                    memory_tracker.sample()
                    entity_df = grouped.get_group(entity_id).copy()
                    result, retry_count = self._run_entity_with_retries(entity_df, entity_id)
                    total_retries += retry_count
                    results.append(result)
                    self._update_checkpoint(result)
                    progress.advance(entity_id, success=result.success)

                    if result.failed and self.fail_fast:
                        raise EntityProcessingError(
                            entity_id=entity_id,
                            message="fail_fast enabled",
                            cause=result.error,
                        )
        finally:
            progress.stop()

        total_duration = time.perf_counter() - start
        summary = build_summary(
            total_entities=len(entities),
            results=results,
            skipped=skipped,
            total_duration_seconds=total_duration,
            peak_memory_mb=memory_tracker.peak_rss_mb,
            batches_processed=len(batches),
            total_retries=total_retries,
        )
        progress.print_summary(summary)
        self._logger.info(
            "Run complete: %d succeeded, %d failed, %d skipped, %d retries in %.2fs",
            summary.succeeded,
            summary.failed,
            summary.skipped,
            summary.total_retries,
            summary.total_duration_seconds,
        )
        return summary

    def _load_completed_entities(self) -> set[EntityId]:
        if not self.resume or self.checkpoint is None:
            return set()
        return self.checkpoint.load_completed()

    def _run_entity_with_retries(
        self,
        entity_df: pd.DataFrame,
        entity_id: EntityId,
    ) -> tuple[EntityResult, int]:
        """Process one entity with retry handling. Returns result and retry count."""
        retry_count = 0
        last_result: EntityResult | None = None

        for attempt in range(1, self.retries + 1):
            result = self.flow.process_entity_frame(entity_df, entity_id)
            result.attempts = attempt
            if result.success:
                if attempt > 1:
                    self._logger.info("Entity %r succeeded on attempt %d", entity_id, attempt)
                return result, retry_count

            last_result = result
            if attempt >= self.retries:
                break

            retry_count += 1
            delay = self.retry_policy.delay_for_attempt(attempt + 1)
            self._logger.warning(
                "Entity %r failed attempt %d/%d: %s; retrying in %.2fs",
                entity_id,
                attempt,
                self.retries,
                result.error,
                delay,
            )
            if delay > 0:
                time.sleep(delay)

        assert last_result is not None
        self._logger.error(
            "Entity %r failed after %d attempt(s): %s",
            entity_id,
            self.retries,
            last_result.error,
        )
        return last_result, retry_count

    def _update_checkpoint(self, result: EntityResult) -> None:
        if self.checkpoint is None:
            return
        if result.success:
            self.checkpoint.mark_completed(
                result.entity_id,
                runtime_seconds=result.runtime_seconds,
                memory_delta_mb=result.memory_delta_mb,
                attempts=result.attempts,
            )
            return
        self.checkpoint.mark_failed(
            result.entity_id,
            error=result.error,
            runtime_seconds=result.runtime_seconds,
            memory_delta_mb=result.memory_delta_mb,
            attempts=result.attempts,
        )
