#!/usr/bin/env bash
# Protect main: PR required, 1 approval, CI must pass.
# Tries repository ruleset API first, falls back to classic branch protection.
# Requires: gh auth login (repo admin)
set -euo pipefail

REPO="${GITHUB_REPO:-baban9/timeseriesflow}"
BRANCH="${1:-main}"
RULESET_NAME="${RULESET_NAME:-Protect main}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh && gh auth login" >&2
  exit 1
fi

echo "Protecting ${REPO} branch ${BRANCH} ..."

# Remove broken rulesets with no targets (optional cleanup by name)
existing_id="$(gh api "/repos/${REPO}/rulesets" --jq ".[] | select(.name==\"${RULESET_NAME}\") | .id" 2>/dev/null | head -1 || true)"
if [[ -n "${existing_id}" ]]; then
  echo "Deleting existing ruleset id=${existing_id} ..."
  gh api --method DELETE "/repos/${REPO}/rulesets/${existing_id}" >/dev/null 2>&1 || true
fi

echo "Creating ruleset with branch target refs/heads/${BRANCH} ..."

gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/${REPO}/rulesets" \
  --input - <<EOF
{
  "name": "${RULESET_NAME}",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/${BRANCH}"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "test (3.10)"},
          {"context": "test (3.11)"},
          {"context": "test (3.12)"}
        ]
      }
    },
    {
      "type": "non_fast_forward"
    },
    {
      "type": "deletion"
    }
  ]
}
EOF

echo ""
echo "Done. Ruleset targets refs/heads/${BRANCH} with:"
echo "  - Pull request + 1 approval"
echo "  - CI: test (3.10), test (3.11), test (3.12)"
echo "  - No force push, no branch delete"
echo ""
echo "Verify: https://github.com/${REPO}/settings/rules"
