"""Entity grouping and iteration utilities."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

import pandas as pd

from timeseriesflow.types import EntityId

if TYPE_CHECKING:
    from timeseriesflow.config import FlowConfig


def list_entities(df: pd.DataFrame, entity_column: str, *, sort: bool = True) -> list[EntityId]:
    """Return unique entity identifiers from a dataframe."""
    if entity_column not in df.columns:
        raise KeyError(f"entity column {entity_column!r} not found in dataframe")
    entities = df[entity_column].dropna().unique().tolist()
    if sort:
        try:
            entities = sorted(entities, key=lambda value: (type(value).__name__, value))
        except TypeError:
            entities = sorted(entities, key=str)
    return entities


def split_by_entity(
    df: pd.DataFrame,
    entity_column: str,
    *,
    sort_entities: bool = True,
    max_entities: int | None = None,
) -> Iterator[tuple[EntityId, pd.DataFrame]]:
    """Yield (entity_id, entity_df) pairs from a multi-entity dataframe."""
    entities = list_entities(df, entity_column, sort=sort_entities)
    if max_entities is not None:
        entities = entities[:max_entities]
    for entity_id in entities:
        mask = df[entity_column] == entity_id
        entity_df = df.loc[mask].copy()
        yield entity_id, entity_df


def apply_entity_limit(config: FlowConfig, entities: list[EntityId]) -> list[EntityId]:
    """Apply max_entities limit from config."""
    if config.max_entities is None:
        return entities
    return entities[: config.max_entities]
