#!/usr/bin/env bash
# Enable branch protection on main: PR required, 1 approval, CI must pass.
# Requires: gh auth login (repo admin)
set -euo pipefail

REPO="${GITHUB_REPO:-baban9/timeseriesflow}"
BRANCH="${1:-main}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh && gh auth login" >&2
  exit 1
fi

echo "Applying branch protection to ${REPO}@${BRANCH} ..."

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "test (3.10)",
      "test (3.11)",
      "test (3.12)"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true
}
EOF

echo ""
echo "Done. main now requires:"
echo "  - Pull request before merge"
echo "  - At least 1 approving review"
echo "  - CI checks: test (3.10), test (3.11), test (3.12)"
echo ""
echo "Verify: https://github.com/${REPO}/settings/branches"
