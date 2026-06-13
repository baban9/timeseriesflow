"""Evaluate TimeSeriesFlow and AdaptiveForecast on open sensor data.

Downloads the Intel Berkeley Research Lab dataset (54 motes, ~2.3M readings)
and measures:

1. EntityRunner throughput at different worker counts
2. Per-entity AdaptiveForecast routing diversity and gate outcomes

Run:
    python examples/open_data_evaluation.py
    python examples/open_data_evaluation.py --dataset fixture --workers 1 2
    python examples/open_data_evaluation.py --max-entities 20 --max-rows-per-entity 5000

Output:
    .evaluation_reports/open_data_report.json
    .evaluation_reports/open_data_report.txt
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from adaptiveforecast import ProfileAwareArchitectureSelection, ValidationGate  # noqa: E402
from evaluation.datasets import dataset_summary, load_fixture, load_intel_berkeley  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    PerformanceResult,
    summarize_performance,
    summarize_routing,
    usefulness_verdict,
)
from evaluation.report import format_report, write_report  # noqa: E402
from timeseriesflow import EntityContext, EntityRunner, entity_flow  # noqa: E402
from timeseriesflow.sources import CSVSource, SourceSchema  # noqa: E402

FIXTURE_PATH = ROOT / "examples" / "evaluation" / "fixtures" / "intel_sample.csv"
DEFAULT_CACHE = ROOT / ".evaluation_cache"
DEFAULT_OUTPUT = ROOT / ".evaluation_reports" / "open_data_report.json"


@entity_flow(entity_key="moteid", time_key="timestamp")
def summarize_mote(df: pd.DataFrame, ctx: EntityContext) -> dict[str, float]:
    """Lightweight per-mote stats for throughput benchmarks."""
    return {
        "rows": float(len(df)),
        "mean_temp": float(df["temperature"].mean()),
    }


@entity_flow(entity_key="moteid", time_key="timestamp")
def profile_mote(df: pd.DataFrame, ctx: EntityContext) -> dict[str, object]:
    """Profile one mote and return routing metadata."""
    selector = ProfileAwareArchitectureSelection(
        time_column=ctx.time_key,
        value_column="temperature",
        infer_freq=True,
        max_models=2,
        gate=ValidationGate(
            min_rows=100,
            min_coverage_ratio=0.15,
            max_missing_rate=0.55,
            max_sampling_irregularity=0.80,
        ),
    )
    selection = selector.select(df)
    profile = selection.profile
    return {
        "moteid": ctx.entity_id,
        "rows": len(df),
        "gate_passed": selection.gate_passed,
        "best_model": selection.best_model,
        "recommended_models": list(selection.recommendation.recommended_models),
        "reason": selection.recommendation.reason,
        "coverage_ratio": round(profile.coverage_ratio, 4),
        "volatility": round(profile.volatility, 4),
        "seasonality_strength": round(profile.seasonality_strength, 4),
        "trend_strength": round(profile.trend_strength, 4),
    }


def _write_temp_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _run_workers(
    csv_path: Path,
    *,
    workers: int,
    batch_size: int,
) -> PerformanceResult:
    schema = SourceSchema(required_columns=("moteid", "timestamp", "temperature"))
    source = CSVSource(
        csv_path,
        parse_dates=["timestamp"],
        selected_columns=["moteid", "timestamp", "temperature"],
        schema=schema,
    )
    runner = EntityRunner(
        source=source,
        flow=summarize_mote,
        workers=workers,
        batch_size=batch_size,
        retries=1,
        show_progress=False,
    )
    started = time.perf_counter()
    summary = runner.run()
    elapsed = time.perf_counter() - started
    rate = summary.processed / elapsed if elapsed > 0 else 0.0
    return PerformanceResult(
        workers=workers,
        elapsed_seconds=elapsed,
        entities_processed=summary.processed,
        entities_per_second=rate,
    )


def _run_routing_once(csv_path: Path, *, batch_size: int) -> list[dict[str, object]]:
    schema = SourceSchema(required_columns=("moteid", "timestamp", "temperature"))
    source = CSVSource(
        csv_path,
        parse_dates=["timestamp"],
        selected_columns=["moteid", "timestamp", "temperature"],
        schema=schema,
    )
    runner = EntityRunner(
        source=source,
        flow=profile_mote,
        workers=1,
        batch_size=batch_size,
        retries=1,
        show_progress=False,
    )
    summary = runner.run()
    outputs: list[dict[str, object]] = []
    for result in summary.results:
        if result.success and isinstance(result.output, dict):
            outputs.append(result.output)
    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open-data evaluation for TimeSeriesFlow")
    parser.add_argument(
        "--dataset",
        choices=("intel", "fixture"),
        default="intel",
        help="Dataset to use (fixture is offline-safe)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=[1, 4],
        help="Worker counts to benchmark",
    )
    parser.add_argument("--max-entities", type=int, default=None)
    parser.add_argument("--max-rows-per-entity", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--routing-only",
        action="store_true",
        help="Skip performance benchmark and only compute routing metrics",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.dataset == "fixture":
        frame = load_fixture(FIXTURE_PATH)
        dataset_name = "intel_sample_fixture"
    else:
        frame = load_intel_berkeley(
            args.cache_dir,
            max_entities=args.max_entities,
            max_rows_per_entity=args.max_rows_per_entity,
        )
        dataset_name = "intel_berkeley_lab"

    temp_csv = args.cache_dir / f"{dataset_name}_eval.csv"
    _write_temp_csv(frame, temp_csv)
    summary = dataset_summary(frame, entity_key="moteid")

    performance_payload: dict[str, object]
    if args.routing_only:
        performance_payload = {"runs": [], "speedup_vs_workers_1": {}}
    else:
        perf_results = [
            _run_workers(temp_csv, workers=workers, batch_size=args.batch_size)
            for workers in sorted(set(args.workers))
        ]
        performance_payload = summarize_performance(perf_results)

    routing_outputs = _run_routing_once(temp_csv, batch_size=args.batch_size)
    routing = summarize_routing(routing_outputs)
    verdict = usefulness_verdict(
        routing=routing,
        performance=performance_payload,
    )

    payload = {
        "dataset": {"name": dataset_name, **summary},
        "performance": performance_payload,
        "routing": {
            "gate_pass_rate": routing.gate_pass_rate,
            "model_distribution": routing.model_distribution,
            "unique_models_assigned": routing.unique_models_assigned,
            "routing_diversity_rate": routing.routing_diversity_rate,
            "default_model": routing.default_model,
            "entities_differing_from_default": routing.entities_differing_from_default,
            "insufficient_data_count": routing.insufficient_data_count,
            "mean_coverage_ratio": routing.mean_coverage_ratio,
        },
        "verdict": verdict,
        "sample_profiles": routing.profiles[:5],
    }

    write_report(args.output, payload)
    print(format_report(payload))
    print(f"\nWrote {args.output}")
    print(f"Wrote {args.output.with_suffix('.txt')}")


if __name__ == "__main__":
    main()
