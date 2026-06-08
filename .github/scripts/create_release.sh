#!/usr/bin/env bash
# Create a GitHub release from an existing tag.
# Usage: ./.github/scripts/create_release.sh v0.1.0
set -euo pipefail

tag="${1:-v0.1.0}"
notes_file=".github/RELEASE_${tag#v}.md"

if [[ ! -f "$notes_file" ]]; then
  notes_file=".github/RELEASE_${tag}.md"
fi
if [[ ! -f "$notes_file" ]]; then
  echo "Release notes not found for tag $tag" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh && gh auth login" >&2
  exit 1
fi

gh release view "$tag" >/dev/null 2>&1 && {
  echo "Release $tag already exists. Edit at:"
  gh release view "$tag" --web
  exit 0
}

gh release create "$tag" \
  --title "TimeSeriesFlow ${tag}" \
  --notes-file "$notes_file"

echo "Published: https://github.com/baban9/timeseriesflow/releases/tag/${tag}"
