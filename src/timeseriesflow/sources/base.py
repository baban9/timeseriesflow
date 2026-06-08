"""Abstract base classes for data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pandas as pd

from timeseriesflow.exceptions import SourceNotFoundError, SourceSchemaError
from timeseriesflow.sources.schema import SourceSchema

if TYPE_CHECKING:
    from collections.abc import Sequence


class BaseSource(ABC):
    """Abstract base for all TimeSeriesFlow data sources.

    Subclasses must implement ``validate`` and ``load``. File-based sources
    should extend ``FileSource``. Document stores such as MongoDB should extend
    ``TabularSource`` directly without assuming a filesystem path.
    """

    source_name: str = "source"

    def __init__(
        self,
        *,
        schema: SourceSchema | None = None,
        lazy: bool = False,
    ) -> None:
        self.schema = schema
        self.lazy = lazy
        self._cached_frame: pd.DataFrame | None = None

    @property
    def is_loaded(self) -> bool:
        """Return True when data has been loaded and cached."""
        return self._cached_frame is not None

    @abstractmethod
    def validate(self) -> None:
        """Validate configuration, connectivity, and schema without full load."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load data and return a pandas DataFrame."""

    def clear_cache(self) -> None:
        """Clear any cached dataframe from memory."""
        self._cached_frame = None

    def _cache_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optionally cache a loaded dataframe based on lazy setting."""
        if not self.lazy:
            self._cached_frame = df
        return df

    def _get_cached_or_load(self) -> pd.DataFrame:
        """Return cached data or invoke ``load``."""
        if self._cached_frame is not None:
            return cast(pd.DataFrame, self._cached_frame.copy(deep=True))
        return self.load()

    def _validate_schema_columns(self, columns: Sequence[str]) -> None:
        """Validate column names against the configured schema."""
        if self.schema is None:
            return
        try:
            self.schema.validate_columns(list(columns), source=self.source_name)
        except SourceSchemaError:
            raise


class TabularSource(BaseSource):
    """Base class for sources that materialize a pandas DataFrame.

    Future document sources (for example ``MongoSource``) should subclass
    this type and implement ``_read_dataframe`` plus source-specific
    validation logic.
    """

    @abstractmethod
    def _read_dataframe(self) -> pd.DataFrame:
        """Read and return the raw dataframe from the underlying store."""

    def load(self) -> pd.DataFrame:
        """Load, validate schema, cache, and return the dataframe."""
        if self._cached_frame is not None:
            return cast(pd.DataFrame, self._cached_frame.copy(deep=True))
        try:
            df = self._read_dataframe()
        except SourceNotFoundError:
            raise
        except Exception as exc:
            from timeseriesflow.exceptions import SourceLoadError

            raise SourceLoadError(self.source_name, "unable to read data", cause=exc) from exc
        if self.schema is not None:
            self.schema.validate_dataframe(df, source=self.source_name)
        return self._cache_frame(df)


class FileSource(TabularSource):
    """Base class for filesystem-backed tabular sources."""

    def __init__(
        self,
        path: Path | str,
        *,
        selected_columns: Sequence[str] | None = None,
        schema: SourceSchema | None = None,
        lazy: bool = False,
    ) -> None:
        super().__init__(schema=schema, lazy=lazy)
        self.path = Path(path)
        self.selected_columns = list(selected_columns) if selected_columns is not None else None

    def validate(self) -> None:
        """Check file existence and validate schema from a lightweight peek."""
        self._ensure_file_exists()
        columns = self._peek_columns()
        self._validate_selected_columns(columns)
        self._validate_schema_columns(columns)

    def _ensure_file_exists(self) -> None:
        if not self.path.exists():
            raise SourceNotFoundError(self.source_name, self.path)
        if not self.path.is_file():
            raise SourceNotFoundError(self.source_name, self.path)

    def _validate_selected_columns(self, available: Sequence[str]) -> None:
        if self.selected_columns is None:
            return
        missing = [column for column in self.selected_columns if column not in available]
        if missing:
            raise SourceSchemaError(
                self.source_name,
                "selected columns are not present in source",
                missing=missing,
            )

    @abstractmethod
    def _peek_columns(self) -> list[str]:
        """Return column names without loading the full dataset."""
