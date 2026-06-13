"""Tests for open-data evaluation helpers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURE = EXAMPLES / "evaluation" / "fixtures" / "intel_sample.csv"


def test_fixture_loads() -> None:
    sys.path.insert(0, str(EXAMPLES))
    from evaluation.datasets import dataset_summary, load_fixture

    frame = load_fixture(FIXTURE)
    summary = dataset_summary(frame)
    assert summary["entities"] == 3
    assert summary["rows"] == 428


def test_metrics_and_report_format() -> None:
    sys.path.insert(0, str(EXAMPLES))
    from evaluation.metrics import (
        PerformanceResult,
        summarize_performance,
        summarize_routing,
        usefulness_verdict,
    )
    from evaluation.report import format_report

    performance = summarize_performance(
        [
            PerformanceResult(1, 2.0, 10, 5.0),
            PerformanceResult(4, 1.0, 10, 10.0),
        ]
    )
    routing = summarize_routing(
        [
            {"best_model": "naive", "gate_passed": True, "coverage_ratio": 0.9},
            {"best_model": "lstm", "gate_passed": True, "coverage_ratio": 0.8},
            {"best_model": "naive", "gate_passed": False, "coverage_ratio": 0.4},
        ]
    )
    verdict = usefulness_verdict(routing=routing, performance=performance)
    text = format_report(
        {
            "dataset": {"name": "test", "entities": 3, "rows": 100, "median_rows_per_entity": 33},
            "performance": performance,
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
        }
    )
    assert "Open data evaluation report" in text
    assert "naive" in text


def test_open_data_evaluation_fixture_script(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(EXAMPLES / "open_data_evaluation.py"),
            "--dataset",
            "fixture",
            "--workers",
            "1",
            "2",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert "Open data evaluation report" in completed.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["dataset"]["name"] == "intel_sample_fixture"
    assert payload["routing"]["unique_models_assigned"] >= 1
    assert output.with_suffix(".txt").exists()
