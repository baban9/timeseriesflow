"""Public dataset loaders for evaluation runs."""

from __future__ import annotations

import gzip
import io
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
    if max_entities is not None:
        keep = sorted(frame["moteid"].unique())[:max_entities]
        frame = frame[frame["moteid"].isin(keep)]
    if max_rows_per_entity is not None:
        frame = (
            frame.groupby("moteid", sort=False)
            .head(max_rows_per_entity)
            .reset_index(drop=True)
        )
    return frame


def load_fixture(path: Path) -> pd.DataFrame:
    """Load a bundled CSV fixture for offline tests."""
    frame = pd.read_csv(path, parse_dates=["timestamp"])
    required = {"moteid", "timestamp", "temperature"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"fixture missing columns: {sorted(missing)}")
    return frame


def dataset_summary(frame: pd.DataFrame) -> dict[str, object]:
    """Summarize a multi-entity frame."""
    rows_per_entity = frame.groupby("moteid").size()
    return {
        "entities": int(frame["moteid"].nunique()),
        "rows": len(frame),
        "median_rows_per_entity": float(rows_per_entity.median()),
        "min_rows_per_entity": int(rows_per_entity.min()),
        "max_rows_per_entity": int(rows_per_entity.max()),
        "span_days": float(
            (frame["timestamp"].max() - frame["timestamp"].min()).total_seconds() / 86_400
        ),
    }


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
