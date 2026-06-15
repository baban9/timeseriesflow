"""Unit tests for executive verdict generation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from evaluation.commercial_kpis import attach_kpis_to_payload  # noqa: E402
from evaluation.verdict import attach_verdict_to_payload, build_verdict, status_label  # noqa: E402


def _sample_payload() -> dict:
    return {
        "datasets": [
            {
                "dataset": "Intel Berkeley Lab",
                "dataset_key": "intel",
                "summary": {"entities": 30, "rows": 10000, "span_days": 5.0},
                "runs": [
                    {
                        "mode": "vanilla_pandas",
                        "entities_per_second": 4000.0,
                        "elapsed_seconds": 0.01,
                        "gate_pass_rate": None,
                    },
                    {
                        "mode": "timeseriesflow",
                        "entities_per_second": 300.0,
                        "elapsed_seconds": 0.1,
                        "gate_pass_rate": None,
                    },
                    {
                        "mode": "adaptiveforecast_loop",
                        "entities_per_second": 60.0,
                        "elapsed_seconds": 0.5,
                        "gate_pass_rate": 0.9,
                        "routing_diversity_rate": 0.1,
                        "unique_models": 2,
                    },
                    {
                        "mode": "full_stack",
                        "entities_per_second": 50.0,
                        "elapsed_seconds": 0.6,
                        "gate_pass_rate": 0.9,
                        "routing_diversity_rate": 0.1,
                        "unique_models": 2,
                        "mean_coverage_ratio": 0.8,
                        "model_distribution": {"moving_average": 27, "none": 3},
                    },
                ],
            },
            {
                "dataset": "UCI Household Power",
                "dataset_key": "uci",
                "summary": {"entities": 3, "rows": 12000, "span_days": 2.8},
                "runs": [
                    {
                        "mode": "vanilla_pandas",
                        "entities_per_second": 1500.0,
                        "elapsed_seconds": 0.002,
                        "gate_pass_rate": None,
                    },
                    {
                        "mode": "timeseriesflow",
                        "entities_per_second": 200.0,
                        "elapsed_seconds": 0.015,
                        "gate_pass_rate": None,
                    },
                    {
                        "mode": "adaptiveforecast_loop",
                        "entities_per_second": 30.0,
                        "elapsed_seconds": 0.1,
                        "gate_pass_rate": 0.0,
                        "routing_diversity_rate": 0.0,
                        "unique_models": 1,
                    },
                    {
                        "mode": "full_stack",
                        "entities_per_second": 60.0,
                        "elapsed_seconds": 0.05,
                        "gate_pass_rate": 0.0,
                        "routing_diversity_rate": 0.0,
                        "unique_models": 1,
                        "mean_coverage_ratio": 1.0,
                        "model_distribution": {"none": 3},
                    },
                ],
            },
        ]
    }


def test_build_verdict_has_decision_table() -> None:
    payload = _sample_payload()
    attach_kpis_to_payload(payload)
    verdict = build_verdict(payload)
    assert verdict["executive_summary"]
    assert len(verdict["decision_table"]) >= 5
    assert verdict["product_verdicts"]["timeseriesflow"]["headline"]
    assert verdict["one_liners"]["adaptiveforecast"]


def test_attach_verdict_rewrites_conclusions() -> None:
    payload = _sample_payload()
    attach_kpis_to_payload(payload)
    attach_verdict_to_payload(payload)
    assert payload["verdict"]["use_when"]
    assert len(payload["conclusions"]) == 4
    assert payload["conclusions"][0].startswith("TimeSeriesFlow:")


def test_status_label() -> None:
    assert status_label("pass") == "Pass"
    assert status_label("not_tested") == "Not tested"
