"""Schema definitions for data source validation."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from timeseriesflow.exceptions import SourceSchemaError


@dataclass(frozen=True, slots=True)
class SourceSchema:
    """Expected column requirements for a data source.

    Attributes:
        required_columns: Columns that must be present after loading.
        optional_columns: Columns that may be present but are not required.
    """

    required_columns: tuple[str, ...] = field(default_factory=tuple)
    optional_columns: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.required_columns and not self.optional_columns:
            raise ValueError("SourceSchema must define at least one column")

    @property
    def all_known_columns(self) -> tuple[str, ...]:
        """Return required and optional columns combined."""
        return self.required_columns + self.optional_columns

    def validate_columns(self, available: list[str], *, source: str) -> None:
        """Validate that all required columns are available.

        Args:
            available: Column names present in the source.
            source: Source name used in error messages.

        Raises:
            SourceSchemaError: When required columns are missing.
        """
        missing = [column for column in self.required_columns if column not in available]
        if missing:
            raise SourceSchemaError(
                source,
                "required columns are not present",
                missing=missing,
            )

    def validate_dataframe(self, df: pd.DataFrame, *, source: str) -> None:
        """Validate a loaded dataframe against this schema."""
        self.validate_columns(list(df.columns), source=source)
