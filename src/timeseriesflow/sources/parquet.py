"""Parquet file data source."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pandas as pd

from timeseriesflow.exceptions import SourceLoadError
from timeseriesflow.sources.base import FileSource
from timeseriesflow.sources.schema import SourceSchema


def _parquet_engine_available() -> bool:
    try:
        import pyarrow  # noqa: F401

        return True
    except ImportError:
        try:
            import fastparquet  # type: ignore[import-not-found]  # noqa: F401

            return True
        except ImportError:
            return False


def _read_parquet_column_names(path: Path) -> list[str]:
    """Read Parquet column names without loading the full dataset."""
    try:
        import pyarrow.parquet as pq

        return cast(list[str], pq.read_schema(path).names)  # type: ignore[no-untyped-call]
    except ImportError:
        pass
    except Exception:
        pass
    try:
        from fastparquet import ParquetFile

        return list(ParquetFile(path).columns)
    except ImportError:
        pass
    except Exception:
        pass
    return list(pd.read_parquet(path).columns)


class ParquetSource(FileSource):
    """Load time-series data from a Parquet file.

    Attributes:
        path: Path to the Parquet file.
        selected_columns: Subset of columns to load. Must exist in the file.
        schema: Optional schema for required column validation.
        lazy: When True, loaded data is not cached in memory.
    """

    source_name = "ParquetSource"

    def __init__(
        self,
        path: Path | str,
        *,
        selected_columns: Sequence[str] | None = None,
        schema: SourceSchema | None = None,
        lazy: bool = False,
    ) -> None:
        super().__init__(
            path,
            selected_columns=selected_columns,
            schema=schema,
            lazy=lazy,
        )

    def _ensure_engine(self) -> None:
        if not _parquet_engine_available():
            raise SourceLoadError(
                self.source_name,
                "parquet support requires pyarrow or fastparquet; "
                "install with: pip install timeseriesflow[parquet]",
            )

    def _peek_columns(self) -> list[str]:
        self._ensure_engine()
        self._ensure_file_exists()
        try:
            return _read_parquet_column_names(self.path)
        except Exception as exc:
            raise SourceLoadError(
                self.source_name,
                f"unable to read Parquet schema from {self.path}",
                cause=exc,
            ) from exc

    def _read_dataframe(self) -> pd.DataFrame:
        self._ensure_engine()
        self._ensure_file_exists()
        try:
            if self.selected_columns is not None:
                return pd.read_parquet(self.path, columns=self.selected_columns)
            return pd.read_parquet(self.path)
        except Exception as exc:
            raise SourceLoadError(
                self.source_name,
                f"unable to read Parquet file {self.path}",
                cause=exc,
            ) from exc
