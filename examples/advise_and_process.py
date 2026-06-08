"""Per-entity profiling and architecture recommendation inside an entity flow.

Run:
    python examples/advise_and_process.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from adaptiveforecast import ProfileAwareArchitectureSelection
from timeseriesflow import EntityContext, entity_flow


def build_device_data() -> pd.DataFrame:
    """Synthetic multi-device temperature readings."""
    base = datetime(2024, 6, 1, tzinfo=timezone.utc)
    rng = np.random.default_rng(42)
    rows = []
    for device_id in ("D-100", "D-200", "D-300"):
        offset = {"D-100": 0.0, "D-200": 5.0, "D-300": 10.0}[device_id]
        for hour in range(48):
            seasonal = 2.0 * np.sin(hour / 12.0)
            noise = float(rng.normal(0, 0.3))
            rows.append(
                {
                    "device_id": device_id,
                    "timestamp": base + timedelta(hours=hour),
                    "temperature": 20.0 + offset + seasonal + noise,
                }
            )
    return pd.DataFrame(rows)


@entity_flow(entity_key="device_id", time_key="timestamp")
def advise_and_process(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    """Profile one device series and return a model recommendation."""
    selector = ProfileAwareArchitectureSelection(
        time_column=ctx.time_key,
        value_column="temperature",
        max_models=2,
    )
    selection = selector.select(df)
    recommendation = selection.recommendation

    ctx.logger.info(
        "device %s: best_model=%s gate_passed=%s",
        ctx.entity_id,
        selection.best_model,
        selection.gate_passed,
    )

    return {
        "device_id": ctx.entity_id,
        "rows": len(df),
        "gate_passed": selection.gate_passed,
        "best_model": selection.best_model,
        "recommended_models": list(recommendation.recommended_models),
        "reason": recommendation.reason,
    }


def main() -> None:
    df = build_device_data()
    result = advise_and_process.run(df)

    print(f"Processed {result.processed} devices")
    print(f"Succeeded: {result.succeeded}, failed: {result.failed}\n")

    for output in result.outputs:
        print(
            f"{output['device_id']}: best_model={output['best_model']} "
            f"models={output['recommended_models']}"
        )
        print(f"  reason: {output['reason']}\n")


if __name__ == "__main__":
    main()
