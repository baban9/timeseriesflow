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


def iter_entity_groups(
    df: pd.DataFrame,
    entity_column: str,
    *,
    sort_entities: bool = True,
    max_entities: int | None = None,
    skip: set[EntityId] | None = None,
) -> Iterator[tuple[EntityId, pd.DataFrame]]:
    """Yield (entity_id, entity_df) pairs using a single groupby pass.

    More efficient than repeated boolean masks when processing many entities.
    """
    entities = list_entities(df, entity_column, sort=sort_entities)
    if max_entities is not None:
        entities = entities[:max_entities]

    excluded = skip or set()
    if not entities:
        return

    grouped = df.groupby(entity_column, sort=False)
    for entity_id in entities:
        if entity_id in excluded:
            continue
        entity_df = grouped.get_group(entity_id).copy()
        yield entity_id, entity_df


def split_by_entity(
    df: pd.DataFrame,
    entity_column: str,
    *,
    sort_entities: bool = True,
    max_entities: int | None = None,
    skip: set[EntityId] | None = None,
) -> Iterator[tuple[EntityId, pd.DataFrame]]:
    """Yield (entity_id, entity_df) pairs from a multi-entity dataframe."""
    yield from iter_entity_groups(
        df,
        entity_column,
        sort_entities=sort_entities,
        max_entities=max_entities,
        skip=skip,
    )


def apply_entity_limit(config: FlowConfig, entities: list[EntityId]) -> list[EntityId]:
    """Apply max_entities limit from config."""
    if config.max_entities is None:
        return entities
    return entities[: config.max_entities]
