"""Pipeline script loading and validation."""

from __future__ import annotations

import ast
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from timeseriesflow.cli.errors import CliError
from timeseriesflow.progress import RunSummary
from timeseriesflow.runner.runner import EntityRunner

ENTRY_POINT_NAMES = ("run", "create_runner", "runner", "main")


def resolve_pipeline_path(path: Path) -> Path:
    """Resolve and validate a pipeline script path."""
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise CliError(
            f"Pipeline file not found: {path}",
            hint="Check the path or run from your project root.",
        )
    if not resolved.is_file():
        raise CliError(f"Pipeline path is not a file: {resolved}")
    if resolved.suffix != ".py":
        raise CliError(
            f"Pipeline must be a Python file (.py): {resolved.name}",
            hint="Point tsflow at a .py script, for example examples/basic_pipeline.py",
        )
    return resolved


def check_syntax(path: Path) -> None:
    """Parse the file and raise CliError on syntax errors."""
    source = path.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise CliError(
            f"Syntax error in {path.name} at line {exc.lineno}: {exc.msg}",
            hint="Fix the Python syntax before running the pipeline.",
        ) from exc


def load_pipeline_module(path: Path) -> ModuleType:
    """Import a pipeline module from a file path."""
    check_syntax(path)
    module_name = f"tsflow_pipeline_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise CliError(f"Unable to load pipeline module: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise CliError(
            f"Failed to import pipeline {path.name}: {exc}",
            hint="Ensure imports and top-level code in the pipeline are valid.",
        ) from exc
    return module


def find_entry_point(module: ModuleType) -> str | None:
    """Return the name of the first available pipeline entry point."""
    for name in ENTRY_POINT_NAMES:
        if hasattr(module, name):
            return name
    return None


def validate_pipeline_module(module: ModuleType, *, path: Path) -> str:
    """Validate pipeline contract and optional hooks."""
    entry = find_entry_point(module)
    if entry is None:
        raise CliError(
            f"Pipeline {path.name} is missing an entry point.",
            hint=(
                "Define one of: run(), create_runner(), runner, or main(). "
                "See examples/basic_pipeline.py"
            ),
        )

    if hasattr(module, "validate") and callable(module.validate):
        try:
            module.validate()
        except Exception as exc:
            raise CliError(
                f"Pipeline validation failed: {exc}",
                hint="Fix the validate() function in your pipeline script.",
            ) from exc
    elif entry in {"create_runner", "runner"}:
        runner = resolve_runner(module, path=path)
        runner.source.validate()

    return entry


def resolve_runner(module: ModuleType, *, path: Path) -> EntityRunner:
    """Build an EntityRunner from a pipeline module."""
    if hasattr(module, "runner"):
        runner = module.runner
        if isinstance(runner, EntityRunner):
            return runner
        raise CliError(
            f"Pipeline {path.name} has 'runner' but it is not an EntityRunner.",
            hint="Set runner = EntityRunner(...) in your pipeline script.",
        )

    if hasattr(module, "create_runner") and callable(module.create_runner):
        try:
            runner = module.create_runner()
        except Exception as exc:
            raise CliError(
                f"create_runner() failed in {path.name}: {exc}",
                hint="Check source paths and pipeline configuration.",
            ) from exc
        if not isinstance(runner, EntityRunner):
            raise CliError(
                "create_runner() must return an EntityRunner instance.",
                hint="Return EntityRunner(source=..., flow=..., ...) from create_runner().",
            )
        return runner

    raise CliError(
        f"Pipeline {path.name} cannot be run as an EntityRunner.",
        hint="Add create_runner() or a module-level runner variable.",
    )


def execute_pipeline(module: ModuleType, *, path: Path) -> RunSummary | Any:
    """Execute a pipeline and return its result."""
    if hasattr(module, "run") and callable(module.run):
        try:
            return module.run()
        except Exception as exc:
            raise CliError(
                f"Pipeline run() failed: {exc}",
                hint="Check logs above or run with --verbose for details.",
            ) from exc

    if hasattr(module, "runner") or (
        hasattr(module, "create_runner") and callable(module.create_runner)
    ):
        runner = resolve_runner(module, path=path)
        try:
            return runner.run()
        except Exception as exc:
            raise CliError(
                f"Pipeline execution failed: {exc}",
                hint="Verify your source data and entity flow configuration.",
            ) from exc

    if hasattr(module, "main") and callable(module.main):
        try:
            return module.main()
        except Exception as exc:
            raise CliError(f"Pipeline main() failed: {exc}") from exc

    raise CliError(
        f"No executable entry point found in {path.name}.",
        hint="Add a run() function or create_runner() returning EntityRunner.",
    )
