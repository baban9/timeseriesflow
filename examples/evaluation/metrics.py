"""Aggregate evaluation metrics from entity run outputs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PerformanceResult:
    workers: int
    elapsed_seconds: float
    entities_processed: int
    entities_per_second: float


@dataclass(slots=True)
class RoutingResult:
    entities_profiled: int
    gate_pass_rate: float
    model_distribution: dict[str, int]
    unique_models_assigned: int
    routing_diversity_rate: float
    default_model: str | None
    entities_differing_from_default: int
    insufficient_data_count: int
    mean_coverage_ratio: float
    profiles: list[dict[str, Any]] = field(default_factory=list)


def summarize_performance(results: list[PerformanceResult]) -> dict[str, object]:
    baseline = results[0]
    speedups: dict[str, float] = {}
    for item in results[1:]:
        if baseline.entities_per_second > 0:
            speedups[str(item.workers)] = round(
                item.entities_per_second / baseline.entities_per_second,
                2,
            )
    return {
        "runs": [
            {
                "workers": item.workers,
                "elapsed_seconds": round(item.elapsed_seconds, 3),
                "entities_per_second": round(item.entities_per_second, 2),
            }
            for item in results
        ],
        "speedup_vs_workers_1": speedups,
    }


def summarize_routing(outputs: list[dict[str, object]]) -> RoutingResult:
    if not outputs:
        return RoutingResult(
            entities_profiled=0,
            gate_pass_rate=0.0,
            model_distribution={},
            unique_models_assigned=0,
            routing_diversity_rate=0.0,
            default_model=None,
            entities_differing_from_default=0,
            insufficient_data_count=0,
            mean_coverage_ratio=0.0,
        )

    models = [str(item.get("best_model") or "none") for item in outputs]
    distribution = dict(Counter(models))
    default_model = Counter(models).most_common(1)[0][0]
    differing = sum(1 for model in models if model != default_model)
    gate_passed = sum(1 for item in outputs if item.get("gate_passed"))
    coverage_values = [
        float(item["coverage_ratio"])
        for item in outputs
        if item.get("coverage_ratio") is not None
    ]

    return RoutingResult(
        entities_profiled=len(outputs),
        gate_pass_rate=gate_passed / len(outputs),
        model_distribution=distribution,
        unique_models_assigned=len(distribution),
        routing_diversity_rate=differing / len(outputs),
        default_model=default_model,
        entities_differing_from_default=differing,
        insufficient_data_count=distribution.get("insufficient_data", 0),
        mean_coverage_ratio=sum(coverage_values) / len(coverage_values) if coverage_values else 0.0,
        profiles=outputs,
    )


def usefulness_verdict(
    *,
    routing: RoutingResult,
    performance: dict[str, object],
) -> dict[str, object]:
    """Heuristic verdict on when the stack adds practical value."""
    signals: list[str] = []
    gaps: list[str] = []

    if routing.unique_models_assigned >= 3:
        signals.append("Per-entity model routing spans 3+ architectures.")
    elif routing.unique_models_assigned >= 2:
        signals.append("Some entities receive different model recommendations.")
    else:
        gaps.append("Most entities map to one model; global default may suffice.")

    if routing.routing_diversity_rate >= 0.25:
        rate_text = f"{routing.routing_diversity_rate:.0%} of entities differ from modal."
        signals.append(rate_text)
    else:
        gaps.append("Low routing diversity; heterogeneous routing benefit is limited.")

    if routing.insufficient_data_count > 0 or routing.gate_pass_rate < 0.9:
        signals.append(
            "Quality gates flag entities that should not proceed to training unchanged."
        )
    else:
        gaps.append("Nearly all entities pass gates; screening value is low on this slice.")

    speedup = performance.get("speedup_vs_workers_1", {})
    if speedup and max(speedup.values(), default=1.0) >= 1.5:
        signals.append("Parallel workers improve throughput on this workload.")
    else:
        gaps.append("Parallel workers show modest gains; CPU may be light per entity.")

    useful = len(signals) >= 2
    return {
        "useful_on_this_dataset": useful,
        "signals": signals,
        "gaps": gaps,
        "summary": (
            "Framework adds practical value for multi-entity profiling and routing on this data."
            if useful
            else "Framework helps operationally, but routing diversity is limited on this slice."
        ),
    }
