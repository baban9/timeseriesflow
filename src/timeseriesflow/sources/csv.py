"""CSV file data source."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from timeseriesflow.exceptions import SourceLoadError
from timeseriesflow.sources.base import FileSource
from timeseriesflow.sources.schema import SourceSchema

ParseDatesArg = str | list[str] | dict[str, str | list[str]] | None


class CSVSource(FileSource):
    """Load time-series data from a CSV file.

    Attributes:
        path: Path to the CSV file.
        parse_dates: Columns to parse as datetimes, passed to ``pandas.read_csv``.
        selected_columns: Subset of columns to load. Must exist in the file.
        schema: Optional schema for required column validation.
        lazy: When True, loaded data is not cached in memory.
    """

    source_name = "CSVSource"

    def __init__(
        self,
        path: Path | str,
        *,
        parse_dates: ParseDatesArg = None,
        selected_columns: Sequence[str] | None = None,
        schema: SourceSchema | None = None,
        lazy: bool = False,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(
            path,
            selected_columns=selected_columns,
            schema=schema,
            lazy=lazy,
        )
        self.parse_dates = parse_dates
        self.encoding = encoding

    def _read_kwargs(self) -> dict[str, object]:
        kwargs: dict[str, object] = {"encoding": self.encoding}
        if self.selected_columns is not None:
            kwargs["usecols"] = self.selected_columns
        if self.parse_dates is not None:
            kwargs["parse_dates"] = self.parse_dates
        return kwargs

    def _peek_columns(self) -> list[str]:
        try:
            frame = pd.read_csv(self.path, nrows=0, encoding=self.encoding)
        except Exception as exc:
            raise SourceLoadError(
                self.source_name,
                f"unable to read CSV header from {self.path}",
                cause=exc,
            ) from exc
        return list(frame.columns)

    def _read_dataframe(self) -> pd.DataFrame:
        self._ensure_file_exists()
        try:
            return pd.read_csv(self.path, **self._read_kwargs())
        except Exception as exc:
            raise SourceLoadError(
                self.source_name,
                f"unable to read CSV file {self.path}",
                cause=exc,
            ) from exc
