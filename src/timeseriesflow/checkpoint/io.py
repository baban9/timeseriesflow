"""Crash-safe JSONL I/O utilities."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from timeseriesflow.exceptions import CheckpointError


def append_jsonl_line(path: Path, payload: dict[str, Any]) -> None:
    """Append one JSON line and fsync to disk for crash safety.

    Uses append-only writes so a crash mid-run loses at most the in-flight
    line rather than corrupting prior checkpoint records.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, default=str, separators=(",", ":")) + "\n"
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise CheckpointError(f"failed to append checkpoint entry to {path}") from exc


def iter_jsonl_entries(path: Path) -> Iterator[dict[str, Any]]:
    """Yield parsed JSON objects from a JSONL file.

    Skips blank lines and tolerates a truncated final line from a crash
    during write.
    """
    if not path.exists():
        return

    last_nonempty_line = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                last_nonempty_line = line_number
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    if line_number == last_nonempty_line:
                        continue
                    raise CheckpointError(
                        f"corrupt checkpoint entry at {path}:{line_number}"
                    ) from exc
                if not isinstance(data, dict):
                    raise CheckpointError(
                        f"checkpoint entry at {path}:{line_number} must be a JSON object"
                    )
                yield data
    except OSError as exc:
        raise CheckpointError(f"failed to read checkpoint file {path}") from exc
