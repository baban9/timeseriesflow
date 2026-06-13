"""Unit tests for commercial KPI derivation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from evaluation.commercial_kpis import (  # noqa: E402
    attach_kpis_to_payload,
    compute_dataset_kpis,
    compute_portfolio_summary,
    enrich_run_metrics,
)


def _sample_payload() -> dict:
    return {
        "datasets": [
            {
                "dataset": "intel",
                "summary": {"entities": 10, "rows": 1000, "span_days": 5.0},
                "runs": [
                    {
                        "mode": "vanilla_pandas",
                        "entities_per_second": 100.0,
                        "elapsed_seconds": 0.1,
                        "gate_pass_rate": None,
                    },
                    {
                        "mode": "adaptiveforecast_loop",
                        "entities_per_second": 50.0,
                        "elapsed_seconds": 0.2,
                        "gate_pass_rate": 0.7,
                    },
                    {
                        "mode": "full_stack",
                        "entities_per_second": 45.0,
                        "elapsed_seconds": 0.22,
                        "gate_pass_rate": 0.7,
                        "routing_diversity_rate": 0.2,
                        "unique_models": 2,
                        "mean_coverage_ratio": 0.85,
                        "model_distribution": {"arima": 7, "ets": 3},
                    },
                ],
            }
        ]
    }


def test_enrich_run_metrics() -> None:
    run = enrich_run_metrics({"gate_pass_rate": 0.7, "entities_processed": 10})
    assert run["training_waste_avoided_rate"] == 0.3
    assert run["entities_blocked"] == 3
    assert run["entities_cleared"] == 7


def test_compute_dataset_kpis() -> None:
    payload = _sample_payload()
    kpi = compute_dataset_kpis(payload["datasets"][0])
    assert kpi["training_jobs_avoided_rate"] == 0.3
    assert kpi["entities_blocked"] == 3
    assert kpi["unique_models_assigned"] == 2


def test_attach_kpis_to_payload() -> None:
    payload = _sample_payload()
    attach_kpis_to_payload(payload)
    assert len(payload["commercial_kpis"]) == 1
    assert payload["portfolio_summary"]["total_entities"] == 10
    assert len(payload["pitch_highlights"]) >= 1


def test_portfolio_summary() -> None:
    kpis = [compute_dataset_kpis(item) for item in _sample_payload()["datasets"]]
    summary = compute_portfolio_summary(kpis)
    assert summary["datasets_evaluated"] == 1
    assert summary["portfolio_training_jobs_avoided_rate"] == 0.3
