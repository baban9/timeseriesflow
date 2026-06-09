"""Sparse device readings: grid alignment plus profile-aware model routing.

Run:
    python examples/sparse_device_profile.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from adaptiveforecast import ProfileAwareArchitectureSelection, ValidationGate
from timeseriesflow import EntityContext, entity_flow
from timeseriesflow.preprocess import align_entity_to_grid


def build_sparse_device_data() -> pd.DataFrame:
    """Synthetic IoT readings with gaps and irregular spacing."""
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rng = np.random.default_rng(7)
    rows: list[dict[str, object]] = []
    for device_id in ("S-01", "S-02"):
        cursor = base
        for _ in range(35):
            if rng.random() < 0.35:
                cursor += timedelta(hours=int(rng.integers(2, 30)))
                continue
            value = 18.0 + (5.0 if device_id == "S-02" else 0.0) + float(rng.normal(0, 0.5))
            rows.append(
                {
                    "device_id": device_id,
                    "timestamp": cursor,
                    "temperature": value,
                }
            )
            cursor += timedelta(hours=int(rng.integers(1, 6)))
    return pd.DataFrame(rows)


@entity_flow(entity_key="device_id", time_key="timestamp")
def sparse_profile_device(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    """Align sparse readings to an hourly grid, then profile and advise."""
    grid = align_entity_to_grid(
        df,
        time_column=ctx.time_key,
        value_column="temperature",
        freq="1h",
    )
    aligned = grid.frame

    selector = ProfileAwareArchitectureSelection(
        time_column=ctx.time_key,
        value_column="temperature",
        expected_freq="1h",
        max_models=2,
        gate=ValidationGate(
            min_rows=10,
            min_coverage_ratio=0.05,
            max_gap_seconds=30 * 86_400,
            max_missing_rate=0.95,
            max_sampling_irregularity=1.0,
        ),
    )
    selection = selector.select(aligned)

    ctx.logger.info(
        "device %s coverage=%.2f best_model=%s gate=%s",
        ctx.entity_id,
        grid.coverage_ratio,
        selection.best_model,
        selection.gate_passed,
    )

    return {
        "device_id": ctx.entity_id,
        "raw_rows": len(df),
        "grid_slots": grid.grid_slot_count,
        "coverage_ratio": round(grid.coverage_ratio, 3),
        "gate_passed": selection.gate_passed,
        "best_model": selection.best_model,
        "recommended_models": list(selection.recommendation.recommended_models),
        "reason": selection.recommendation.reason,
    }


def main() -> None:
    data = build_sparse_device_data()
    result = sparse_profile_device.run(data)

    print(f"Processed {result.processed} devices")
    print(f"Succeeded: {result.succeeded}, failed: {result.failed}\n")

    for output in result.outputs:
        print(
            f"{output['device_id']}: coverage={output['coverage_ratio']} "
            f"best_model={output['best_model']} gate={output['gate_passed']}"
        )
        print(f"  reason: {output['reason']}\n")


if __name__ == "__main__":
    main()
