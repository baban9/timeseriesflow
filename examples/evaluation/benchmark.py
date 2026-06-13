"""Comparative benchmarks: vanilla pandas vs TimeSeriesFlow vs full stack."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from adaptiveforecast import ProfileAwareArchitectureSelection, ValidationGate
from evaluation.datasets import normalize_entity_frame
from timeseriesflow import EntityContext, EntityRunner, entity_flow
from timeseriesflow.sources import CSVSource, SourceSchema

ModeName = Literal[
    "vanilla_pandas",
    "adaptiveforecast_loop",
    "timeseriesflow",
    "full_stack",
]

PROFILE_GATE = ValidationGate(
    min_rows=100,
    min_coverage_ratio=0.15,
    max_missing_rate=0.55,
    max_sampling_irregularity=0.80,
)


@dataclass(slots=True)
class BenchmarkRun:
    mode: ModeName
    elapsed_seconds: float
    entities_processed: int
    entities_per_second: float
    gate_pass_rate: float | None
    unique_models: int | None
    routing_diversity_rate: float | None
    outputs: list[dict[str, Any]]


def _profile_entity_frame(
    entity_df: pd.DataFrame,
    *,
    time_key: str,
    value_key: str,
    infer_freq: bool,
    expected_freq: str | None,
) -> dict[str, Any]:
    selector = ProfileAwareArchitectureSelection(
        time_column=time_key,
        value_column=value_key,
        infer_freq=infer_freq,
        expected_freq=expected_freq,
        max_models=2,
        gate=PROFILE_GATE,
    )
    selection = selector.select(entity_df)
    profile = selection.profile
    return {
        "rows": len(entity_df),
        "gate_passed": selection.gate_passed,
        "best_model": selection.best_model,
        "coverage_ratio": round(profile.coverage_ratio, 4),
        "volatility": round(profile.volatility, 4),
    }


def run_vanilla_pandas(
    frame: pd.DataFrame,
    *,
    entity_key: str,
    value_key: str,
    time_key: str,
) -> BenchmarkRun:
    started = time.perf_counter()
    outputs: list[dict[str, Any]] = []
    for entity_id, entity_df in frame.groupby(entity_key, sort=False):
        sorted_df = entity_df.sort_values(time_key)
        outputs.append(
            {
                "entity_id": entity_id,
                "rows": len(sorted_df),
                "mean_value": float(sorted_df[value_key].mean()),
            }
        )
    elapsed = time.perf_counter() - started
    count = len(outputs)
    return BenchmarkRun(
        mode="vanilla_pandas",
        elapsed_seconds=elapsed,
        entities_processed=count,
        entities_per_second=count / elapsed if elapsed > 0 else 0.0,
        gate_pass_rate=None,
        unique_models=None,
        routing_diversity_rate=None,
        outputs=outputs,
    )


def run_adaptiveforecast_loop(
    frame: pd.DataFrame,
    *,
    entity_key: str,
    value_key: str,
    time_key: str,
    infer_freq: bool,
    expected_freq: str | None,
) -> BenchmarkRun:
    started = time.perf_counter()
    outputs: list[dict[str, Any]] = []
    for entity_id, entity_df in frame.groupby(entity_key, sort=False):
        sorted_df = entity_df.sort_values(time_key)
        payload = _profile_entity_frame(
            sorted_df,
            time_key=time_key,
            value_key=value_key,
            infer_freq=infer_freq,
            expected_freq=expected_freq,
        )
        payload["entity_id"] = entity_id
        outputs.append(payload)
    elapsed = time.perf_counter() - started
    count = len(outputs)
    routing = _routing_stats(outputs)
    return BenchmarkRun(
        mode="adaptiveforecast_loop",
        elapsed_seconds=elapsed,
        entities_processed=count,
        entities_per_second=count / elapsed if elapsed > 0 else 0.0,
        gate_pass_rate=routing["gate_pass_rate"],
        unique_models=routing["unique_models"],
        routing_diversity_rate=routing["routing_diversity_rate"],
        outputs=outputs,
    )


def run_entity_runner(
    csv_path: Path,
    *,
    entity_key: str,
    value_key: str,
    time_key: str,
    mode: Literal["timeseriesflow", "full_stack"],
    infer_freq: bool,
    expected_freq: str | None,
    workers: int = 1,
) -> BenchmarkRun:
    if mode == "timeseriesflow":
        flow = _build_summarize_flow(entity_key, time_key, value_key)
    else:
        flow = _build_profile_flow(
            entity_key,
            time_key,
            value_key,
            infer_freq=infer_freq,
            expected_freq=expected_freq,
        )

    schema = SourceSchema(required_columns=(entity_key, time_key, value_key))
    source = CSVSource(
        csv_path,
        parse_dates=[time_key],
        selected_columns=[entity_key, time_key, value_key],
        schema=schema,
    )
    runner = EntityRunner(
        source=source,
        flow=flow,
        workers=workers,
        batch_size=50,
        retries=1,
        show_progress=False,
    )
    started = time.perf_counter()
    summary = runner.run()
    elapsed = time.perf_counter() - started
    outputs: list[dict[str, Any]] = []
    for result in summary.results:
        if result.success and isinstance(result.output, dict):
            outputs.append(result.output)
    routing = _routing_stats(outputs) if mode == "full_stack" else None
    return BenchmarkRun(
        mode=mode,
        elapsed_seconds=elapsed,
        entities_processed=summary.processed,
        entities_per_second=summary.processed / elapsed if elapsed > 0 else 0.0,
        gate_pass_rate=None if routing is None else routing["gate_pass_rate"],
        unique_models=None if routing is None else routing["unique_models"],
        routing_diversity_rate=None if routing is None else routing["routing_diversity_rate"],
        outputs=outputs,
    )


def run_dataset_benchmarks(
    frame: pd.DataFrame,
    *,
    dataset_name: str,
    cache_csv: Path,
    infer_freq: bool,
    expected_freq: str | None,
    workers: int = 1,
) -> dict[str, Any]:
    """Run all benchmark modes for one dataset."""
    normalized, entity_key, value_key = normalize_entity_frame(frame)
    time_key = "timestamp"
    cache_csv.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(cache_csv, index=False)

    runs = [
        run_vanilla_pandas(
            normalized,
            entity_key=entity_key,
            value_key=value_key,
            time_key=time_key,
        ),
        run_adaptiveforecast_loop(
            normalized,
            entity_key=entity_key,
            value_key=value_key,
            time_key=time_key,
            infer_freq=infer_freq,
            expected_freq=expected_freq,
        ),
        run_entity_runner(
            cache_csv,
            entity_key=entity_key,
            value_key=value_key,
            time_key=time_key,
            mode="timeseriesflow",
            infer_freq=infer_freq,
            expected_freq=expected_freq,
            workers=workers,
        ),
        run_entity_runner(
            cache_csv,
            entity_key=entity_key,
            value_key=value_key,
            time_key=time_key,
            mode="full_stack",
            infer_freq=infer_freq,
            expected_freq=expected_freq,
            workers=workers,
        ),
    ]
    return {
        "dataset": dataset_name,
        "entity_key": entity_key,
        "value_key": value_key,
        "runs": [_benchmark_to_dict(run) for run in runs],
    }


def _routing_stats(outputs: list[dict[str, Any]]) -> dict[str, float | int]:
    if not outputs:
        return {"gate_pass_rate": 0.0, "unique_models": 0, "routing_diversity_rate": 0.0}
    models = [str(item.get("best_model") or "none") for item in outputs]
    default = max(set(models), key=models.count)
    differing = sum(1 for model in models if model != default)
    gate_passed = sum(1 for item in outputs if item.get("gate_passed"))
    return {
        "gate_pass_rate": gate_passed / len(outputs),
        "unique_models": len(set(models)),
        "routing_diversity_rate": differing / len(outputs),
    }


def _benchmark_to_dict(run: BenchmarkRun) -> dict[str, Any]:
    model_distribution: dict[str, int] = {}
    coverage_values: list[float] = []
    for item in run.outputs:
        model = str(item.get("best_model") or "none")
        model_distribution[model] = model_distribution.get(model, 0) + 1
        if "coverage_ratio" in item:
            coverage_values.append(float(item["coverage_ratio"]))
    mean_coverage = (
        round(sum(coverage_values) / len(coverage_values), 4) if coverage_values else None
    )
    entities_blocked = (
        sum(1 for item in run.outputs if not item.get("gate_passed"))
        if run.gate_pass_rate is not None
        else None
    )
    entities_cleared = (
        run.entities_processed - entities_blocked
        if entities_blocked is not None
        else None
    )
    return {
        "mode": run.mode,
        "elapsed_seconds": round(run.elapsed_seconds, 3),
        "entities_processed": run.entities_processed,
        "entities_per_second": round(run.entities_per_second, 2),
        "gate_pass_rate": run.gate_pass_rate,
        "unique_models": run.unique_models,
        "routing_diversity_rate": run.routing_diversity_rate,
        "model_distribution": model_distribution,
        "mean_coverage_ratio": mean_coverage,
        "entities_blocked": entities_blocked,
        "entities_cleared": entities_cleared,
    }


def _build_summarize_flow(entity_key: str, time_key: str, value_key: str):
    @entity_flow(entity_key=entity_key, time_key=time_key)
    def summarize_entity(df: pd.DataFrame, ctx: EntityContext) -> dict[str, float]:
        return {
            "rows": float(len(df)),
            "mean_value": float(df[value_key].mean()),
        }

    return summarize_entity


def _build_profile_flow(
    entity_key: str,
    time_key: str,
    value_key: str,
    *,
    infer_freq: bool,
    expected_freq: str | None,
):
    @entity_flow(entity_key=entity_key, time_key=time_key)
    def profile_entity(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
        selector = ProfileAwareArchitectureSelection(
            time_column=ctx.time_key,
            value_column=value_key,
            infer_freq=infer_freq,
            expected_freq=expected_freq,
            max_models=2,
            gate=PROFILE_GATE,
        )
        selection = selector.select(df)
        profile = selection.profile
        return {
            "entity_id": ctx.entity_id,
            "rows": len(df),
            "gate_passed": selection.gate_passed,
            "best_model": selection.best_model,
            "coverage_ratio": round(profile.coverage_ratio, 4),
            "volatility": round(profile.volatility, 4),
        }

    return profile_entity
