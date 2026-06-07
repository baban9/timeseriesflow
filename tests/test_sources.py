"""Tests for the data source abstraction layer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from timeseriesflow.exceptions import SourceLoadError, SourceNotFoundError, SourceSchemaError
from timeseriesflow.sources import CSVSource, ParquetSource, SourceSchema


def test_csv_source_load(csv_path: Path, sensor_schema: SourceSchema) -> None:
    source = CSVSource(
        csv_path,
        parse_dates=["timestamp"],
        schema=sensor_schema,
    )
    source.validate()
    df = source.load()

    assert len(df) == 6
    assert list(df.columns) == ["sensor_id", "timestamp", "value", "quality"]
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert source.is_loaded is True


def test_csv_source_selected_columns(csv_path: Path) -> None:
    source = CSVSource(
        csv_path,
        selected_columns=["sensor_id", "value"],
        parse_dates=None,
    )
    source.validate()
    df = source.load()

    assert list(df.columns) == ["sensor_id", "value"]


def test_csv_source_missing_file(tmp_path: Path) -> None:
    source = CSVSource(tmp_path / "missing.csv")
    with pytest.raises(SourceNotFoundError, match="CSVSource not found"):
        source.validate()


def test_csv_source_schema_validation_error(csv_path: Path) -> None:
    schema = SourceSchema(required_columns=("sensor_id", "missing_column"))
    source = CSVSource(csv_path, schema=schema)

    with pytest.raises(SourceSchemaError, match="missing column"):
        source.validate()


def test_csv_source_selected_column_missing(csv_path: Path) -> None:
    source = CSVSource(csv_path, selected_columns=["sensor_id", "not_a_column"])
    with pytest.raises(SourceSchemaError, match="selected columns"):
        source.validate()


def test_csv_source_lazy_does_not_cache(csv_path: Path) -> None:
    source = CSVSource(csv_path, lazy=True)
    source.load()
    assert source.is_loaded is False


def test_csv_source_caches_when_not_lazy(csv_path: Path) -> None:
    source = CSVSource(csv_path, lazy=False)
    first = source.load()
    second = source.load()
    pd.testing.assert_frame_equal(first, second)
    assert source.is_loaded is True
    source.clear_cache()
    assert source.is_loaded is False


def test_parquet_source_load(parquet_path: Path, sensor_schema: SourceSchema) -> None:
    source = ParquetSource(parquet_path, schema=sensor_schema)
    source.validate()
    df = source.load()

    assert len(df) == 6
    assert "sensor_id" in df.columns


def test_parquet_source_selected_columns(parquet_path: Path) -> None:
    source = ParquetSource(parquet_path, selected_columns=["sensor_id", "value"])
    source.validate()
    df = source.load()

    assert list(df.columns) == ["sensor_id", "value"]


def test_parquet_source_missing_file(tmp_path: Path) -> None:
    source = ParquetSource(tmp_path / "missing.parquet")
    with pytest.raises(SourceNotFoundError, match="ParquetSource not found"):
        source.validate()


def test_parquet_source_schema_validation_error(parquet_path: Path) -> None:
    schema = SourceSchema(required_columns=("value", "extra_column"))
    source = ParquetSource(parquet_path, schema=schema)

    with pytest.raises(SourceSchemaError):
        source.validate()


def test_parquet_source_requires_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "data.parquet"
    path.write_bytes(b"not parquet")
    source = ParquetSource(path)

    monkeypatch.setattr(
        "timeseriesflow.sources.parquet._parquet_engine_available",
        lambda: False,
    )
    with pytest.raises(SourceLoadError, match="parquet support requires"):
        source.validate()


def test_source_schema_requires_columns() -> None:
    with pytest.raises(ValueError, match="at least one column"):
        SourceSchema()


def test_csv_load_informative_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_bytes(b"\xff\xfe\x00 invalid content")
    source = CSVSource(path)

    with pytest.raises(SourceLoadError, match="CSVSource load failed"):
        source.load()
