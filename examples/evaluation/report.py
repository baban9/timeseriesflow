"""Format evaluation results for console and JSON export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def format_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    dataset = payload["dataset"]
    lines.append("Open data evaluation report")
    lines.append("=" * 40)
    lines.append(f"Dataset: {dataset['name']}")
    lines.append(f"Entities: {dataset['entities']}, rows: {dataset['rows']}")
    lines.append(f"Median rows/entity: {dataset['median_rows_per_entity']:.0f}")
    lines.append("")

    lines.append("Performance (EntityRunner)")
    for run in payload["performance"]["runs"]:
        lines.append(
            f"  workers={run['workers']}: "
            f"{run['entities_per_second']:.1f} entities/sec "
            f"({run['elapsed_seconds']:.2f}s)"
        )
    speedup = payload["performance"].get("speedup_vs_workers_1", {})
    if speedup:
        formatted = ", ".join(f"{workers}x={factor}" for workers, factor in speedup.items())
        lines.append(f"  Speedup vs workers=1: {formatted}")
    lines.append("")

    routing = payload["routing"]
    lines.append("AdaptiveForecast routing")
    lines.append(f"  Gate pass rate: {routing['gate_pass_rate']:.1%}")
    lines.append(f"  Unique models assigned: {routing['unique_models_assigned']}")
    lines.append(
        f"  Entities differing from modal model ({routing['default_model']}): "
        f"{routing['entities_differing_from_default']} "
        f"({routing['routing_diversity_rate']:.1%})"
    )
    lines.append(f"  Mean coverage ratio: {routing['mean_coverage_ratio']:.3f}")
    lines.append("  Model distribution:")
    for model, count in sorted(routing["model_distribution"].items()):
        lines.append(f"    {model}: {count}")
    lines.append("")

    verdict = payload["verdict"]
    lines.append(f"Verdict: {verdict['summary']}")
    if verdict["signals"]:
        lines.append("Signals:")
        for signal in verdict["signals"]:
            lines.append(f"  + {signal}")
    if verdict["gaps"]:
        lines.append("Gaps:")
        for gap in verdict["gaps"]:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    path.with_suffix(".txt").write_text(format_report(payload) + "\n", encoding="utf-8")
