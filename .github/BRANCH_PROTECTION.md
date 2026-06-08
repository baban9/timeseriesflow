# Branch protection for main

Direct pushes and merges to `main` are restricted. All changes must go through a pull request with your review.

## Required settings

| Rule | Value |
|------|-------|
| Require pull request before merging | Yes |
| Required approving reviews | 1 |
| Dismiss stale reviews on new pushes | Yes |
| Require conversation resolution | Yes |
| Require status checks | `test (3.10)`, `test (3.11)`, `test (3.12)` |
| Require branches up to date | Yes |
| Allow force pushes | No |
| Allow deletions | No |

## Apply via script (repo admin)

```bash
brew install gh   # if needed
gh auth login
./.github/scripts/enable_branch_protection.sh main
```

## Apply via GitHub UI

1. Open https://github.com/baban9/timeseriesflow/settings/rules
2. Click **New branch ruleset** (or edit existing ruleset for `main`)
3. Target branch: `main`
4. Enable:
   - **Require a pull request before merging**
   - **Required approvals**: 1
   - **Require status checks to pass** (select all `test` jobs from CI)
   - **Block force pushes**
5. Save

Classic UI path: **Settings > Branches > Add branch protection rule** for `main`.

## Workflow after protection is enabled

```bash
git checkout -b feature/my-change
# make changes, commit
git push -u origin feature/my-change
gh pr create --fill
# wait for CI, review, approve, merge
```
