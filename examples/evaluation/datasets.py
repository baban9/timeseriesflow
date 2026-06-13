"""Public dataset loaders for evaluation runs."""

from __future__ import annotations

import gzip
import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

INTEL_LAB_URL = "https://db.csail.mit.edu/labdata/data.txt.gz"
INTEL_LAB_COLUMNS = (
    "date",
    "time",
    "epoch",
    "moteid",
    "temperature",
    "humidity",
    "light",
    "voltage",
)
ETT_H1_URL = "https://raw.githubusercontent.com/zhouhaoyi/ETDataset/main/ETT-small/ETTh1.csv"
UCI_HOUSEHOLD_URL = (
    "https://archive.ics.uci.edu/static/public/235/data.csv"
)
ETT_VALUE_COLUMNS = ("HUFL", "HULL", "MUFL", "MULL", "LUFL", "LULL", "OT")
UCI_SUBMETER_COLUMNS = ("sub_metering_1", "sub_metering_2", "sub_metering_3")


def load_intel_berkeley(
    cache_dir: Path,
    *,
    max_entities: int | None = None,
    max_rows_per_entity: int | None = None,
) -> pd.DataFrame:
    """Load Intel Berkeley Research Lab sensor network data."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    csv_path = cache_dir / "intel_berkeley_lab.csv"

    if not csv_path.exists():
        _download_intel_berkeley(csv_path)

    frame = pd.read_csv(csv_path, parse_dates=["timestamp"])
    return _apply_limits(frame, "moteid", max_entities, max_rows_per_entity)


def load_ett_hourly(
    cache_dir: Path,
    *,
    max_entities: int | None = None,
    max_rows_per_entity: int | None = None,
) -> pd.DataFrame:
    """Load ETT-small ETTh1 and melt load channels into entities."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    csv_path = cache_dir / "ett_h1_long.csv"
    if not csv_path.exists():
        _download_ett_hourly(csv_path)
    frame = pd.read_csv(csv_path, parse_dates=["timestamp"])
    return _apply_limits(frame, "entity_id", max_entities, max_rows_per_entity)


def load_uci_household(
    cache_dir: Path,
    *,
    max_entities: int | None = None,
    max_rows_per_entity: int | None = None,
) -> pd.DataFrame:
    """Load UCI household power sub-meter channels as entities."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    csv_path = cache_dir / "uci_household_long.csv"
    if not csv_path.exists():
        _download_uci_household(csv_path)
    frame = pd.read_csv(csv_path, parse_dates=["timestamp"])
    return _apply_limits(frame, "entity_id", max_entities, max_rows_per_entity)


def load_fixture(path: Path) -> pd.DataFrame:
    """Load a bundled CSV fixture for offline tests."""
    frame = pd.read_csv(path, parse_dates=["timestamp"])
    if "entity_id" in frame.columns:
        required = {"entity_id", "timestamp", "value"}
    else:
        required = {"moteid", "timestamp", "temperature"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"fixture missing columns: {sorted(missing)}")
    return frame


def normalize_entity_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """Return frame with entity_id/value columns and key names."""
    if "entity_id" in frame.columns and "value" in frame.columns:
        return frame, "entity_id", "value"
    if "moteid" in frame.columns and "temperature" in frame.columns:
        renamed = frame.rename(columns={"moteid": "entity_id", "temperature": "value"})
        return renamed, "entity_id", "value"
    raise ValueError("frame must contain entity_id/value or moteid/temperature")


def dataset_summary(
    frame: pd.DataFrame,
    *,
    entity_key: str | None = None,
) -> dict[str, object]:
    """Summarize a multi-entity frame."""
    if entity_key is None:
        if "entity_id" in frame.columns:
            entity_key = "entity_id"
        elif "moteid" in frame.columns:
            entity_key = "moteid"
        else:
            raise ValueError("could not infer entity key from frame")
    rows_per_entity = frame.groupby(entity_key).size()
    return {
        "entities": int(frame[entity_key].nunique()),
        "rows": len(frame),
        "median_rows_per_entity": float(rows_per_entity.median()),
        "min_rows_per_entity": int(rows_per_entity.min()),
        "max_rows_per_entity": int(rows_per_entity.max()),
        "span_days": float(
            (frame["timestamp"].max() - frame["timestamp"].min()).total_seconds() / 86_400
        ),
    }


def _apply_limits(
    frame: pd.DataFrame,
    entity_key: str,
    max_entities: int | None,
    max_rows_per_entity: int | None,
) -> pd.DataFrame:
    limited = frame
    if max_entities is not None:
        keep = sorted(limited[entity_key].unique())[:max_entities]
        limited = limited[limited[entity_key].isin(keep)]
    if max_rows_per_entity is not None:
        limited = (
            limited.groupby(entity_key, sort=False)
            .head(max_rows_per_entity)
            .reset_index(drop=True)
        )
    return limited


def _download_intel_berkeley(csv_path: Path) -> None:
    with urlopen(INTEL_LAB_URL, timeout=120) as response:
        payload = gzip.decompress(response.read())

    raw = pd.read_csv(
        io.BytesIO(payload),
        sep=r"\s+",
        header=None,
        names=list(INTEL_LAB_COLUMNS),
    )
    combined = raw["date"].astype(str) + " " + raw["time"].astype(str)
    raw["timestamp"] = pd.to_datetime(combined, format="mixed")
    raw = raw.drop(columns=["date", "time"])
    raw = raw.sort_values(["moteid", "timestamp"]).reset_index(drop=True)
    raw.to_csv(csv_path, index=False)


def _download_ett_hourly(csv_path: Path) -> None:
    with urlopen(ETT_H1_URL, timeout=120) as response:
        raw = pd.read_csv(io.BytesIO(response.read()))
    raw = raw.rename(columns={"date": "timestamp"})
    raw["timestamp"] = pd.to_datetime(raw["timestamp"])
    long_frame = raw.melt(
        id_vars=["timestamp"],
        value_vars=list(ETT_VALUE_COLUMNS),
        var_name="entity_id",
        value_name="value",
    )
    long_frame = long_frame.dropna(subset=["value"]).sort_values(["entity_id", "timestamp"])
    long_frame.to_csv(csv_path, index=False)


def _download_uci_household(csv_path: Path) -> None:
    with urlopen(UCI_HOUSEHOLD_URL, timeout=180) as response:
        payload = response.read()
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [name for name in archive.namelist() if name.endswith(".txt")]
            if not names:
                raise ValueError("UCI household zip did not contain a txt file")
            with archive.open(names[0]) as handle:
                raw = pd.read_csv(
                    handle,
                    sep=";",
                    na_values=["?"],
                    low_memory=False,
                )
    else:
        raw = pd.read_csv(io.BytesIO(payload), sep=",", na_values=["?"], low_memory=False)

    raw.columns = [str(column).strip() for column in raw.columns]
    column_map = {column.lower(): column for column in raw.columns}
    date_col = column_map.get("date")
    time_col = column_map.get("time")
    if date_col is None or time_col is None:
        raise ValueError(f"UCI household data missing Date/Time columns: {list(raw.columns)}")

    raw["timestamp"] = pd.to_datetime(
        raw[date_col].astype(str) + " " + raw[time_col].astype(str),
        format="mixed",
        dayfirst=True,
    )
    renamed = raw.rename(
        columns={
            column_map["sub_metering_1"]: "sub_metering_1",
            column_map["sub_metering_2"]: "sub_metering_2",
            column_map["sub_metering_3"]: "sub_metering_3",
        }
    )
    long_frame = renamed.melt(
        id_vars=["timestamp"],
        value_vars=list(UCI_SUBMETER_COLUMNS),
        var_name="entity_id",
        value_name="value",
    )
    long_frame = long_frame.dropna(subset=["value", "timestamp"])
    long_frame = long_frame.sort_values(["entity_id", "timestamp"]).reset_index(drop=True)
    long_frame.to_csv(csv_path, index=False)
