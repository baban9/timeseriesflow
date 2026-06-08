"""Verify editable install exposes both top-level packages."""

from __future__ import annotations

import importlib


def test_timeseriesflow_importable() -> None:
    mod = importlib.import_module("timeseriesflow")
    assert hasattr(mod, "__version__")
    assert mod.__version__


def test_adaptiveforecast_importable() -> None:
    mod = importlib.import_module("adaptiveforecast")
    assert hasattr(mod, "__version__")
    assert mod.__version__
    assert hasattr(mod, "ProfileAwareArchitectureSelection")
