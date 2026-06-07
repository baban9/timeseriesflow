"""Entity flow processor protocol."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar, runtime_checkable

import pandas as pd

from timeseriesflow.api.context import EntityContext

EntityFlowCallable = Callable[[pd.DataFrame, EntityContext], Any]

F = TypeVar("F", bound=EntityFlowCallable)


@runtime_checkable
class EntityFlowProcessor(Protocol):
    """Callable that processes a single entity dataframe."""

    def __call__(self, df: pd.DataFrame, context: EntityContext) -> Any:
        """Process one entity and return an arbitrary result."""
        ...


def validate_entity_flow_processor(processor: EntityFlowProcessor) -> None:
    """Validate that the processor is callable."""
    if not callable(processor):
        raise TypeError("processor must be callable")
