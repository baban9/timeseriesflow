# Publishing releases

## GitHub Release

After CI is green on `main`:

```bash
git tag v0.2.0
git push origin v0.2.0
./.github/scripts/create_release.sh v0.2.0
```

Or with GitHub CLI:

```bash
gh release create v0.2.0 --title "TimeSeriesFlow v0.2.0" --notes-file .github/RELEASE_v0.2.0.md
```

## PyPI trusted publishing (one-time setup)

1. Create a PyPI account and register the project name `timeseriesflow` (first upload claims the name).
2. On [pypi.org](https://pypi.org/manage/account/publishing/), add a trusted publisher:
   - **PyPI project name:** `timeseriesflow`
   - **Owner:** `baban9`
   - **Repository:** `timeseriesflow`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. In GitHub repo **Settings > Environments**, create environment `pypi` (no secrets required for trusted publishing).
4. Push a version tag (`v0.2.0`). The [Publish workflow](../.github/workflows/publish.yml) runs on tag push.

Verify:

```bash
pip install timeseriesflow==0.2.0
python -c "import timeseriesflow, adaptiveforecast; print(timeseriesflow.__version__, adaptiveforecast.__version__)"
```

## Version bumps

Keep these in sync before tagging:

- `pyproject.toml` `version`
- `src/timeseriesflow/__init__.py` `__version__`
- `src/adaptiveforecast/__init__.py` `__version__`
- `CHANGELOG.md` new section
- `.github/RELEASE_vX.Y.Z.md` release notes
