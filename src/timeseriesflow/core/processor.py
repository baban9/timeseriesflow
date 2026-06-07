"""Entity processor protocol and decorator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeVar, runtime_checkable

import pandas as pd

from timeseriesflow.types import EntityId, RunContext

F = TypeVar("F", bound=Callable[..., pd.DataFrame])


@runtime_checkable
class EntityProcessor(Protocol):
    """Callable that processes a single entity dataframe."""

    def __call__(self, df: pd.DataFrame, context: RunContext) -> pd.DataFrame:
        """Transform entity-scoped input data into output data."""
        ...


def entity_processor(func: F) -> F:
    """Mark a function as an entity processor (metadata only, no wrapping)."""
    func.__timeseriesflow_processor__ = True  # type: ignore[attr-defined]
    return func


def validate_processor(processor: EntityProcessor) -> None:
    """Validate that processor is callable with expected signature."""
    if not callable(processor):
        raise TypeError("processor must be callable")


def call_processor(
    processor: EntityProcessor,
    df: pd.DataFrame,
    entity_id: EntityId,
    entity_column: str,
    attempt: int,
) -> pd.DataFrame:
    """Invoke processor with a fresh RunContext."""
    context = RunContext(
        entity_id=entity_id,
        entity_column=entity_column,
        attempt=attempt,
    )
    return processor(df, context)
