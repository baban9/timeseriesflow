"""Executive verdict and decision table for the comparative evaluation report."""

from __future__ import annotations

from typing import Any, Literal

VerdictStatus = Literal["pass", "partial", "fail", "not_tested", "na"]

_STATUS_LABEL = {
    "pass": "Pass",
    "partial": "Partial",
    "fail": "Fail",
    "not_tested": "Not tested",
    "na": "N/A",
}


def _run(item: dict[str, Any], mode: str) -> dict[str, Any]:
    for run in item["runs"]:
        if run["mode"] == mode:
            return run
    raise KeyError(mode)


def _mean_orchestration_tax(datasets: list[dict[str, Any]]) -> float:
    ratios: list[float] = []
    for item in datasets:
        vanilla = _run(item, "vanilla_pandas")
        tsflow = _run(item, "timeseriesflow")
        vanilla_eps = float(vanilla.get("entities_per_second") or 0.0)
        tsflow_eps = float(tsflow.get("entities_per_second") or 0.0)
        if tsflow_eps > 0:
            ratios.append(vanilla_eps / tsflow_eps)
    return sum(ratios) / len(ratios) if ratios else 0.0


def _full_stack_vs_af_overhead(datasets: list[dict[str, Any]]) -> float:
    deltas: list[float] = []
    for item in datasets:
        af = _run(item, "adaptiveforecast_loop")
        full = _run(item, "full_stack")
        af_sec = float(af.get("elapsed_seconds") or 0.0)
        full_sec = float(full.get("elapsed_seconds") or 0.0)
        deltas.append(full_sec - af_sec)
    return sum(deltas) / len(deltas) if deltas else 0.0


def build_verdict(payload: dict[str, Any]) -> dict[str, Any]:
    """Derive a clear effectiveness verdict from benchmark payload."""
    datasets: list[dict[str, Any]] = payload.get("datasets") or []
    kpis: list[dict[str, Any]] = payload.get("commercial_kpis") or []
    portfolio: dict[str, Any] = payload.get("portfolio_summary") or {}

    total_entities = int(portfolio.get("total_entities") or 0)
    total_blocked = int(portfolio.get("total_entities_blocked") or 0)
    mean_diversity = float(portfolio.get("mean_routing_diversity_rate") or 0.0)
    max_unique_models = int(portfolio.get("max_unique_models_assigned") or 0)
    mean_screening_eps = float(portfolio.get("mean_screening_throughput_eps") or 0.0)

    orch_tax = _mean_orchestration_tax(datasets)
    fs_af_overhead = _full_stack_vs_af_overhead(datasets)

    any_gate_blocks = total_blocked > 0
    any_routing = mean_diversity > 0.05 or max_unique_models > 1
    all_blocked_datasets = [
        kpi["dataset"]
        for kpi in kpis
        if float(kpi.get("gate_pass_rate") or 0.0) == 0.0 and int(kpi.get("entities") or 0) > 0
    ]
    cleared_datasets = [
        kpi["dataset"]
        for kpi in kpis
        if float(kpi.get("gate_pass_rate") or 0.0) > 0.0
    ]

    tsflow_status: VerdictStatus = "partial"
    if orch_tax <= 15 and total_entities >= 10:
        tsflow_status = "pass"
    elif orch_tax > 50:
        tsflow_status = "fail"

    af_screening_status: VerdictStatus = "pass" if any_gate_blocks else "partial"
    af_routing_status: VerdictStatus = "pass" if any_routing else "partial"

    decision_table = [
        {
            "criterion": "Faster than pandas for the same lightweight stats task",
            "vanilla_pandas": "pass",
            "timeseriesflow": _orchestration_row_status(orch_tax),
            "adaptiveforecast_loop": "fail",
            "full_stack": "fail",
            "note": (
                f"TimeSeriesFlow adds a mean {orch_tax:.1f}x slowdown on stats-only work; "
                "profiling dominates full-stack cost."
            ),
        },
        {
            "criterion": "Blocks unfit entities before model training",
            "vanilla_pandas": "na",
            "timeseriesflow": "na",
            "adaptiveforecast_loop": af_screening_status,
            "full_stack": af_screening_status,
            "note": (
                f"{total_blocked} of {total_entities} entities blocked portfolio-wide. "
                + (
                    f"All entities blocked on: {', '.join(all_blocked_datasets)}."
                    if all_blocked_datasets
                    else "No dataset had 100% gate failure."
                )
            ),
        },
        {
            "criterion": "Assigns different model families per entity",
            "vanilla_pandas": "na",
            "timeseriesflow": "na",
            "adaptiveforecast_loop": af_routing_status,
            "full_stack": af_routing_status,
            "note": (
                f"Mean routing diversity {100 * mean_diversity:.1f}%; "
                f"up to {max_unique_models} unique families assigned."
            ),
        },
        {
            "criterion": "Forecast accuracy better than a single global model",
            "vanilla_pandas": "na",
            "timeseriesflow": "na",
            "adaptiveforecast_loop": "not_tested",
            "full_stack": "not_tested",
            "note": "Phase 2 backtest not run. No MAE or sMAPE in this report.",
        },
        {
            "criterion": "Production batch ops (checkpoints, parallel workers, retries)",
            "vanilla_pandas": "fail",
            "timeseriesflow": "not_tested",
            "adaptiveforecast_loop": "na",
            "full_stack": "not_tested",
            "note": "Benchmark used workers=1 and did not exercise checkpoint resume.",
        },
        {
            "criterion": "Screening throughput for nightly fleet batches",
            "vanilla_pandas": "na",
            "timeseriesflow": "na",
            "adaptiveforecast_loop": _throughput_row_status(mean_screening_eps),
            "full_stack": _throughput_row_status(mean_screening_eps),
            "note": f"Mean full-stack screening: {mean_screening_eps:.1f} entities/s.",
        },
    ]

    af_status: VerdictStatus = (
        "partial" if af_screening_status == "pass" or af_routing_status == "pass" else "fail"
    )
    product_verdicts = {
        "timeseriesflow": {
            "headline": _tsflow_headline(tsflow_status, orch_tax),
            "effective_for": [
                "Structured per-entity batch runs with retries and progress hooks",
                "Teams that outgrow ad-hoc groupby loops but do not need profiling yet",
            ],
            "not_effective_for": [
                "Beating pandas on simple mean and row-count aggregates",
                "Proving forecast quality (orchestration only in this benchmark)",
            ],
            "status": tsflow_status,
        },
        "adaptiveforecast": {
            "headline": _af_headline(af_screening_status, af_routing_status, all_blocked_datasets),
            "effective_for": [
                "Screening entities that fail quality gates before training spend",
                "Routing labels when entity patterns differ within a fleet",
            ],
            "not_effective_for": [
                "Replacing pandas for raw speed on simple statistics",
                "Claims of better forecasts without a Phase 2 accuracy backtest",
            ],
            "status": af_status,
        },
        "full_stack": {
            "headline": _full_stack_headline(
                any_gate_blocks,
                any_routing,
                mean_screening_eps,
                fs_af_overhead,
            ),
            "effective_for": [
                "Nightly screening plus orchestration on heterogeneous entity fleets",
                "Workflows that need both gate outcomes and batch runner structure",
            ],
            "not_effective_for": [
                "Small homogeneous fleets where a single model and a pandas loop suffice",
                "Latency-sensitive paths that only need lightweight aggregates",
            ],
            "status": "partial",
        },
    }

    use_when = [
        "Entity count is large enough that manual loops, retries, and progress matter",
        "Entity quality varies and some series should be blocked before training",
        "A single global model family is risky and per-entity routing is required",
        "You accept profiling overhead in exchange for screening and orchestration",
    ]
    avoid_when = [
        "You only need exploratory mean, count, or simple aggregates on a small fleet",
        "All entities are homogeneous and pass the same model family",
        "You must prove forecast accuracy gains (not measured in Phase 1)",
        "Raw pandas throughput is the primary success metric",
    ]

    one_liners = {
        "timeseriesflow": product_verdicts["timeseriesflow"]["headline"],
        "adaptiveforecast": product_verdicts["adaptiveforecast"]["headline"],
        "full_stack": product_verdicts["full_stack"]["headline"],
    }

    executive_summary = _executive_summary(
        total_entities=total_entities,
        cleared_datasets=cleared_datasets,
        all_blocked_datasets=all_blocked_datasets,
        mean_screening_eps=mean_screening_eps,
        orch_tax=orch_tax,
    )

    return {
        "executive_summary": executive_summary,
        "product_verdicts": product_verdicts,
        "decision_table": decision_table,
        "use_when": use_when,
        "avoid_when": avoid_when,
        "one_liners": one_liners,
        "metrics": {
            "mean_orchestration_tax_vs_pandas": round(orch_tax, 1),
            "mean_full_stack_overhead_vs_af_seconds": round(fs_af_overhead, 3),
            "mean_screening_throughput_eps": mean_screening_eps,
        },
    }


def attach_verdict_to_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Add verdict block and replace conclusions with product one-liners."""
    verdict = build_verdict(payload)
    payload["verdict"] = verdict
    payload["conclusions"] = [
        f"TimeSeriesFlow: {verdict['one_liners']['timeseriesflow']}",
        f"AdaptiveForecast: {verdict['one_liners']['adaptiveforecast']}",
        f"Full stack: {verdict['one_liners']['full_stack']}",
        verdict["executive_summary"],
    ]
    return payload


def _orchestration_row_status(tax: float) -> VerdictStatus:
    if tax <= 10:
        return "partial"
    if tax <= 25:
        return "partial"
    return "fail"


def _throughput_row_status(eps: float) -> VerdictStatus:
    if eps >= 100:
        return "pass"
    if eps >= 30:
        return "partial"
    return "fail"


def _tsflow_headline(status: VerdictStatus, tax: float) -> str:
    if status == "pass":
        return (
            f"Effective as an orchestration layer ({tax:.0f}x slower than pandas on the same "
            "lightweight stats task; acceptable overhead for batch structure)."
        )
    return (
        f"Orchestration overhead is material ({tax:.0f}x vs pandas on stats-only work); "
        "use when batch reliability matters, not for raw speed."
    )


def _af_headline(
    screening: VerdictStatus,
    routing: VerdictStatus,
    all_blocked: list[str],
) -> str:
    parts: list[str] = []
    if screening == "pass":
        parts.append("screening blocks unfit entities before training")
    if routing == "pass":
        parts.append("routing assigns multiple model families where patterns differ")
    if all_blocked:
        parts.append(
            f"on {all_blocked[0]} all entities failed gates "
            "(short span slice; screening-only outcome)"
        )
    if not parts:
        return (
            "Not yet demonstrated effective on these datasets; "
            "no strong screening or routing signal."
        )
    headline = "Partially effective: " + "; ".join(parts) + "."
    return headline + " Forecast accuracy was not tested."


def _full_stack_headline(
    any_blocks: bool,
    any_routing: bool,
    screening_eps: float,
    overhead_sec: float,
) -> str:
    value_parts: list[str] = []
    if any_blocks:
        value_parts.append("combines screening with batch orchestration")
    if any_routing:
        value_parts.append("delivers per-entity routing in one pass")
    if not value_parts:
        return (
            "Not recommended as default: adds profiling cost without clear screening "
            "or routing benefit on these slices."
        )
    return (
        f"Partially effective when {' and '.join(value_parts)} "
        f"at ~{screening_eps:.0f} entities/s "
        f"(+{overhead_sec:.2f}s mean vs AdaptiveForecast-only loop). "
        "Not faster than pandas; value is operational plus screening, not speed."
    )


def _executive_summary(
    *,
    total_entities: int,
    cleared_datasets: list[str],
    all_blocked_datasets: list[str],
    mean_screening_eps: float,
    orch_tax: float,
) -> str:
    cleared = ", ".join(cleared_datasets) if cleared_datasets else "none"
    blocked_note = ""
    if all_blocked_datasets:
        blocked_note = (
            f" {', '.join(all_blocked_datasets)} blocked every entity under current gates "
            "(screening worked; not a deployment-ready forecast slice)."
        )
    return (
        f"Across {total_entities} entities, TimeSeriesFlow is an orchestration layer "
        f"(~{orch_tax:.0f}x pandas on stats-only work), AdaptiveForecast adds screening "
        f"and routing on {cleared}, and forecast accuracy remains unmeasured.{blocked_note} "
        f"Full-stack screening averages {mean_screening_eps:.0f} entities/s."
    )


def status_label(status: VerdictStatus) -> str:
    return _STATUS_LABEL[status]
