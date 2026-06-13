"""Commercial and operational KPIs derived from benchmark results."""

from __future__ import annotations

from typing import Any


def enrich_run_metrics(run: dict[str, Any]) -> dict[str, Any]:
    """Add derived KPI fields to a serialized benchmark run."""
    enriched = dict(run)
    gate_pass = run.get("gate_pass_rate")
    if gate_pass is not None:
        enriched["training_waste_avoided_rate"] = round(1.0 - float(gate_pass), 4)
        entities = int(run.get("entities_processed") or 0)
        enriched["entities_blocked"] = int(round(entities * (1.0 - float(gate_pass))))
        enriched["entities_cleared"] = entities - enriched["entities_blocked"]
    return enriched


def compute_dataset_kpis(item: dict[str, Any]) -> dict[str, Any]:
    """Compute pitch-ready KPIs for one dataset."""
    full_stack = next(run for run in item["runs"] if run["mode"] == "full_stack")
    vanilla = next(run for run in item["runs"] if run["mode"] == "vanilla_pandas")
    af_loop = next(run for run in item["runs"] if run["mode"] == "adaptiveforecast_loop")

    gate_pass = float(full_stack.get("gate_pass_rate") or 0.0)
    entities = int(item["summary"]["entities"])
    blocked = int(round(entities * (1.0 - gate_pass)))

    return {
        "dataset": item.get("dataset") or item.get("dataset_key"),
        "entities": entities,
        "rows": int(item["summary"]["rows"]),
        "span_days": round(float(item["summary"]["span_days"]), 1),
        "gate_pass_rate": round(gate_pass, 4),
        "training_jobs_avoided_rate": round(1.0 - gate_pass, 4),
        "entities_blocked": blocked,
        "entities_cleared": entities - blocked,
        "routing_diversity_rate": round(float(full_stack.get("routing_diversity_rate") or 0.0), 4),
        "unique_models_assigned": int(full_stack.get("unique_models") or 0),
        "screening_throughput_eps": float(full_stack.get("entities_per_second") or 0.0),
        "vanilla_throughput_eps": float(vanilla.get("entities_per_second") or 0.0),
        "af_loop_throughput_eps": float(af_loop.get("entities_per_second") or 0.0),
        "mean_coverage_ratio": full_stack.get("mean_coverage_ratio"),
        "orchestration_overhead_vs_af": round(
            float(full_stack.get("elapsed_seconds") or 0.0)
            - float(af_loop.get("elapsed_seconds") or 0.0),
            3,
        ),
        "profiling_cost_factor_vs_vanilla": round(
            float(vanilla.get("entities_per_second") or 0.0)
            / float(full_stack.get("entities_per_second") or 1.0),
            1,
        ),
        "model_distribution": dict(full_stack.get("model_distribution") or {}),
    }


def compute_portfolio_summary(kpis: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate KPIs across datasets for executive summary."""
    total_entities = sum(item["entities"] for item in kpis)
    total_blocked = sum(item["entities_blocked"] for item in kpis)
    avg_gate_pass = sum(item["gate_pass_rate"] for item in kpis) / len(kpis) if kpis else 0.0
    avg_diversity = (
        sum(item["routing_diversity_rate"] for item in kpis) / len(kpis) if kpis else 0.0
    )
    avg_screening = (
        sum(item["screening_throughput_eps"] for item in kpis) / len(kpis) if kpis else 0.0
    )
    max_unique = max((item["unique_models_assigned"] for item in kpis), default=0)
    return {
        "datasets_evaluated": len(kpis),
        "total_entities": total_entities,
        "total_entities_blocked": total_blocked,
        "portfolio_training_jobs_avoided_rate": round(total_blocked / total_entities, 4)
        if total_entities
        else 0.0,
        "mean_gate_pass_rate": round(avg_gate_pass, 4),
        "mean_routing_diversity_rate": round(avg_diversity, 4),
        "mean_screening_throughput_eps": round(avg_screening, 2),
        "max_unique_models_assigned": max_unique,
    }


def attach_kpis_to_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Enrich benchmark payload with commercial KPIs."""
    datasets = payload["datasets"]
    for item in datasets:
        item["runs"] = [enrich_run_metrics(run) for run in item["runs"]]
    kpis = [compute_dataset_kpis(item) for item in datasets]
    payload["commercial_kpis"] = kpis
    payload["portfolio_summary"] = compute_portfolio_summary(kpis)
    payload["pitch_highlights"] = _build_pitch_highlights(kpis, payload["portfolio_summary"])
    return payload


def _build_pitch_highlights(
    kpis: list[dict[str, Any]],
    portfolio: dict[str, Any],
) -> list[str]:
    lines: list[str] = []
    blocked_rate = portfolio.get("portfolio_training_jobs_avoided_rate", 0.0)
    lines.append(
        f"Across {portfolio['datasets_evaluated']} datasets, "
        f"{100 * blocked_rate:.1f}% of entities would be blocked before model training."
    )
    lines.append(
        f"Mean routing diversity is {100 * portfolio['mean_routing_diversity_rate']:.1f}% "
        f"with up to {portfolio['max_unique_models_assigned']} unique architectures assigned."
    )
    lines.append(
        f"Full-stack screening averages {portfolio['mean_screening_throughput_eps']:.1f} entities per second."
    )
    for item in kpis:
        if item["training_jobs_avoided_rate"] >= 0.30:
            lines.append(
                f"{item['dataset']}: {100 * item['training_jobs_avoided_rate']:.0f}% training waste avoided "
                f"({item['entities_blocked']} of {item['entities']} entities blocked)."
            )
    return lines
