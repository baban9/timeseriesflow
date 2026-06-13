"""Tests for comparative LaTeX report generation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_comparative_report_fixture(tmp_path: Path) -> None:
    output_dir = tmp_path / "report"
    subprocess.run(
        [
            sys.executable,
            str(EXAMPLES / "generate_comparative_report.py"),
            "--datasets",
            "fixture",
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "MPLCONFIGDIR": "/tmp/mpl",
        },
    )
    payload = json.loads((output_dir / "comparative_report.json").read_text(encoding="utf-8"))
    assert len(payload["datasets"]) == 1
    assert (output_dir / "comparative_report.tex").exists()
    assert (output_dir / "figures" / "throughput_comparison.png").exists()
