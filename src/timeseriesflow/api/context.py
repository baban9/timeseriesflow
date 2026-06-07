"""Runtime context for entity flow processors."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from timeseriesflow.types import EntityId


@dataclass(frozen=True, slots=True)
class EntityContext:
    """Context passed to each entity processor invocation.

    Attributes:
        entity_id: Identifier of the entity being processed.
        entity_key: Column name used to group entities.
        time_key: Column name used to order time-series rows.
        logger: Logger scoped to this entity.
        metadata: Optional user-defined metadata for the run.
    """

    entity_id: EntityId
    entity_key: str
    time_key: str
    logger: logging.Logger
    metadata: dict[str, Any] = field(default_factory=dict)
