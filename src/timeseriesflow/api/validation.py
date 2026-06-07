"""Input validation for entity flows."""

from __future__ import annotations

import pandas as pd

from timeseriesflow.exceptions import ColumnValidationError


def validate_required_columns(
    df: pd.DataFrame,
    *,
    entity_key: str,
    time_key: str,
) -> None:
    """Ensure the dataframe contains required entity and time columns.

    Args:
        df: Input dataframe to validate.
        entity_key: Column identifying entities.
        time_key: Column identifying timestamps.

    Raises:
        ColumnValidationError: If any required column is missing.
    """
    missing = [column for column in (entity_key, time_key) if column not in df.columns]
    if missing:
        raise ColumnValidationError(
            f"missing required column(s): {', '.join(repr(column) for column in missing)}"
        )
