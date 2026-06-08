"""EntityFlow execution engine."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pandas as pd

from timeseriesflow.api.context import EntityContext
from timeseriesflow.api.processor import EntityFlowProcessor, validate_entity_flow_processor
from timeseriesflow.api.result import EntityFlowResult, EntityResult
from timeseriesflow.api.validation import validate_required_columns
from timeseriesflow.checkpoint import CheckpointBackend, LocalCheckpoint
from timeseriesflow.core.entity import iter_entity_groups, list_entities
from timeseriesflow.logging import get_logger
from timeseriesflow.memory import MemorySnapshot
from timeseriesflow.types import EntityId

if TYPE_CHECKING:
    pass

logger = get_logger("entity_flow")


class EntityFlow:
    """Orchestrates entity-based processing for the developer API.

    Validates input columns, splits by entity, sorts each entity by time,
    and invokes the processor sequentially without mutating the source
    dataframe. Supports resumable runs via an optional checkpoint backend.
    """

    def __init__(
        self,
        processor: EntityFlowProcessor,
        *,
        entity_key: str,
        time_key: str,
        sort_entities: bool = True,
        checkpoint: CheckpointBackend | None = None,
        checkpoint_dir: Path | str | None = None,
        resume: bool = True,
    ) -> None:
        validate_entity_flow_processor(processor)
        if not entity_key:
            raise ValueError("entity_key must be a non-empty string")
        if not time_key:
            raise ValueError("time_key must be a non-empty string")
        self.processor = processor
        self.entity_key = entity_key
        self.time_key = time_key
        self.sort_entities = sort_entities
        self.resume = resume
        self.checkpoint = checkpoint or self._build_checkpoint(checkpoint_dir)
        self._logger = get_logger("entity_flow")

    def _build_checkpoint(self, checkpoint_dir: Path | str | None) -> CheckpointBackend | None:
        if checkpoint_dir is None:
            return None
        return LocalCheckpoint(checkpoint_dir)

    def run(self, df: pd.DataFrame) -> EntityFlowResult:
        """Process all entities and collect results.

        Args:
            df: Multi-entity input dataframe. Never mutated by this method.

        Returns:
            EntityFlowResult containing one EntityResult per processed entity.
        """
        validate_required_columns(df, entity_key=self.entity_key, time_key=self.time_key)
        source_snapshot = df.copy(deep=False)

        completed: set[EntityId] = set()
        if self.resume and self.checkpoint is not None:
            completed = self.checkpoint.load_completed()
            if completed:
                self._logger.info("Resuming run; skipping %d completed entities", len(completed))

        all_entities = list_entities(df, self.entity_key, sort=self.sort_entities)
        skipped = sum(1 for entity_id in all_entities if entity_id in completed)

        collected: list[EntityResult] = []

        for entity_id, entity_df in iter_entity_groups(
            df,
            self.entity_key,
            sort_entities=self.sort_entities,
            skip=completed,
        ):
            result = self._process_entity_frame(entity_df, entity_id)
            collected.append(result)
            self._record_checkpoint(result)

        if not df.equals(source_snapshot):
            raise RuntimeError("source dataframe was mutated during entity flow run")

        return EntityFlowResult(results=collected, skipped=skipped)

    def _record_checkpoint(self, result: EntityResult) -> None:
        if self.checkpoint is None:
            return
        if result.success:
            self.checkpoint.mark_completed(
                result.entity_id,
                runtime_seconds=result.runtime_seconds,
                memory_delta_mb=result.memory_delta_mb,
            )
            return
        self.checkpoint.mark_failed(
            result.entity_id,
            error=result.error,
            runtime_seconds=result.runtime_seconds,
            memory_delta_mb=result.memory_delta_mb,
        )

    def process_entity(self, source_df: pd.DataFrame, entity_id: EntityId) -> EntityResult:
        """Process a single entity from a multi-entity dataframe."""
        entity_df = self._prepare_entity_frame(source_df, entity_id)
        return self._process_entity_frame(entity_df, entity_id)

    def process_entity_frame(self, entity_df: pd.DataFrame, entity_id: EntityId) -> EntityResult:
        """Process a pre-split entity dataframe (used by EntityRunner)."""
        return self._process_entity_frame(self._sort_entity_frame(entity_df), entity_id)

    def _process_entity_frame(self, entity_df: pd.DataFrame, entity_id: EntityId) -> EntityResult:
        """Run the processor on a single entity frame."""
        entity_df = self._sort_entity_frame(entity_df)
        context = EntityContext(
            entity_id=entity_id,
            entity_key=self.entity_key,
            time_key=self.time_key,
            logger=get_logger(f"entity_flow.{entity_id}"),
        )

        start_memory = MemorySnapshot.capture()
        start_time = time.perf_counter()

        try:
            output = self.processor(entity_df, context)
            runtime_seconds = time.perf_counter() - start_time
            end_memory = MemorySnapshot.capture()
            memory_delta_mb = max(0.0, end_memory.rss_mb - start_memory.rss_mb)
            self._logger.debug(
                "Entity %r processed in %.3fs (memory delta %.2f MB)",
                entity_id,
                runtime_seconds,
                memory_delta_mb,
            )
            return EntityResult(
                entity_id=entity_id,
                success=True,
                runtime_seconds=runtime_seconds,
                memory_delta_mb=memory_delta_mb,
                output=output,
            )
        except BaseException as exc:
            runtime_seconds = time.perf_counter() - start_time
            end_memory = MemorySnapshot.capture()
            memory_delta_mb = max(0.0, end_memory.rss_mb - start_memory.rss_mb)
            self._logger.warning("Entity %r failed: %s", entity_id, exc)
            return EntityResult(
                entity_id=entity_id,
                success=False,
                runtime_seconds=runtime_seconds,
                memory_delta_mb=memory_delta_mb,
                error=exc,
            )

    def _prepare_entity_frame(self, source_df: pd.DataFrame, entity_id: EntityId) -> pd.DataFrame:
        """Extract and sort a single entity frame without mutating the source."""
        grouped = source_df.groupby(self.entity_key, sort=False)
        entity_df = grouped.get_group(entity_id).copy()
        return self._sort_entity_frame(entity_df)

    def _sort_entity_frame(self, entity_df: pd.DataFrame) -> pd.DataFrame:
        return cast(
            pd.DataFrame,
            entity_df.sort_values(self.time_key).reset_index(drop=True),
        )
