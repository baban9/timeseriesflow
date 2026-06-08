"""entity_flow decorator for the developer API."""

from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, cast

import pandas as pd

from timeseriesflow.api.flow import EntityFlow
from timeseriesflow.api.naming import resolve_entity_column_name
from timeseriesflow.api.processor import EntityFlowCallable, EntityFlowProcessor
from timeseriesflow.api.result import EntityFlowResult

if TYPE_CHECKING:
    from timeseriesflow.checkpoint import CheckpointBackend

F = TypeVar("F", bound=EntityFlowCallable)


class EntityFlowFunction:
    """Callable wrapper that exposes EntityFlow.run on a decorated function."""

    def __init__(self, func: EntityFlowCallable, flow: EntityFlow) -> None:
        self._func = func
        self._flow = flow
        functools.update_wrapper(self, func)

    @property
    def flow(self) -> EntityFlow:
        """Underlying EntityFlow instance."""
        return self._flow

    @property
    def entity_key(self) -> str:
        """Entity column configured on this flow."""
        return self._flow.entity_key

    @property
    def entity_column(self) -> str:
        """Alias for entity_key (legacy Flow API naming)."""
        return self._flow.entity_key

    @property
    def time_key(self) -> str:
        """Time column configured on this flow."""
        return self._flow.time_key

    def run(self, df: pd.DataFrame) -> EntityFlowResult:
        """Execute the flow over a multi-entity dataframe."""
        return self._flow.run(df)

    def __call__(self, df: pd.DataFrame, ctx: Any = None) -> Any:
        """Direct call is reserved for internal/testing use with explicit context."""
        if ctx is None:
            raise TypeError(
                "call .run(df) to process a multi-entity dataframe; "
                "the processor signature is (entity_df, ctx)"
            )
        return self._func(df, ctx)


def entity_flow(
    *,
    entity_key: str | None = None,
    entity_column: str | None = None,
    time_key: str,
    sort_entities: bool = True,
    checkpoint: CheckpointBackend | None = None,
    checkpoint_dir: Path | str | None = None,
    resume: bool = True,
) -> Callable[[F], EntityFlowFunction]:
    """Decorate a function as an entity flow processor.

    Use ``entity_key`` or ``entity_column`` (same meaning).

    Example:
        @entity_flow(entity_key="device_id", time_key="timestamp")
        def process_device(df, ctx):
            return {"rows": len(df)}

        results = process_device.run(multi_entity_df)
    """
    resolved_entity_key = resolve_entity_column_name(
        entity_key=entity_key,
        entity_column=entity_column,
    )

    def decorator(func: F) -> EntityFlowFunction:
        flow = EntityFlow(
            cast(EntityFlowProcessor, func),
            entity_key=resolved_entity_key,
            time_key=time_key,
            sort_entities=sort_entities,
            checkpoint=checkpoint,
            checkpoint_dir=checkpoint_dir,
            resume=resume,
        )
        wrapper = EntityFlowFunction(func, flow)
        cast(Any, wrapper).__entity_flow__ = True
        return wrapper

    return decorator
