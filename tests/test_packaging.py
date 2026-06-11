"""Verify editable install and wheel expose both top-level packages."""

from __future__ import annotations

import importlib
import subprocess
import sys
import zipfile
from pathlib import Path


def test_timeseriesflow_importable() -> None:
    mod = importlib.import_module("timeseriesflow")
    assert hasattr(mod, "__version__")
    assert mod.__version__


def test_adaptiveforecast_importable() -> None:
    mod = importlib.import_module("adaptiveforecast")
    assert hasattr(mod, "__version__")
    assert mod.__version__
    assert hasattr(mod, "ProfileAwareArchitectureSelection")


def test_wheel_includes_adaptiveforecast(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    outdir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(outdir)],
        cwd=root,
        check=True,
        capture_output=True,
    )
    wheels = sorted(outdir.glob("timeseriesflow-*.whl"))
    assert wheels, "expected a built wheel"
    with zipfile.ZipFile(wheels[-1]) as archive:
        names = archive.namelist()
    assert any(name.startswith("adaptiveforecast/") for name in names)
    assert any(name.startswith("timeseriesflow/") for name in names)
