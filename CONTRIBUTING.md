# Contributing to TimeSeriesFlow

Thank you for your interest in contributing. This project aims to be a focused, production-quality framework for entity-based time-series processing.

## Getting started

1. Fork and clone the repository.
2. Create a virtual environment (Python 3.10+).
3. Install in editable mode with dev dependencies:

```bash
pip install -e ".[dev]"
```

4. Run the test suite:

```bash
pytest
```

## Code standards

- Full type hints on public and internal APIs
- mypy strict mode must pass for `src/timeseriesflow`
- ruff for linting and import sorting
- Keep changes focused; avoid scope creep
- Add tests for new behavior

## Branch policy

`main` is protected. **Direct pushes and merges to `main` are not allowed.**

All changes must go through a pull request with at least one approving review and passing CI. See [.github/BRANCH_PROTECTION.md](.github/BRANCH_PROTECTION.md).

```bash
git checkout -b feat/my-change
# commit your work
git push -u origin feat/my-change
gh pr create --fill
```

## Pull request process

1. Open an issue for large changes before implementing.
2. Use a descriptive branch name (e.g. `feat/checkpoint-s3-backend`).
3. Ensure CI checks pass locally: `pytest`, `ruff check`, `mypy src`.
4. Update docs when public API or behavior changes.
5. Write a clear PR description with motivation and test plan.
6. Wait for review and approval before merging.

## What belongs in TimeSeriesFlow

In scope:

- Entity grouping and execution
- Retries, checkpointing, progress, memory, logging
- Extensible backends (checkpoint stores, future executors)

Out of scope:

- Forecasting models
- Workflow orchestration (Airflow, Prefect, etc.)
- General-purpose pandas helpers

## Code of conduct

Be respectful and constructive. We welcome contributors of all experience levels.

## Questions

Open a GitHub issue with the `question` label or start a discussion thread.
