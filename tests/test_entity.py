"""Tests for entity grouping utilities."""

from __future__ import annotations

import pandas as pd
import pytest

from timeseriesflow.core.entity import list_entities, split_by_entity


def test_list_entities_sorted(sample_df: pd.DataFrame) -> None:
    entities = list_entities(sample_df, "sensor_id")
    assert entities == ["S1", "S2", "S3"]


def test_list_entities_missing_column(sample_df: pd.DataFrame) -> None:
    with pytest.raises(KeyError):
        list_entities(sample_df, "missing")


def test_split_by_entity(sample_df: pd.DataFrame) -> None:
    groups = list(split_by_entity(sample_df, "sensor_id"))
    assert len(groups) == 3
    assert all(len(frame) == 5 for _, frame in groups)


def test_split_by_entity_max_limit(sample_df: pd.DataFrame) -> None:
    groups = list(split_by_entity(sample_df, "sensor_id", max_entities=2))
    assert len(groups) == 2
