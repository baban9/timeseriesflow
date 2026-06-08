# Branch protection for main

Direct pushes and merges to `main` are restricted. All changes must go through a pull request with your review.

## Fix: "This ruleset does not target any resources"

This warning means the ruleset has **no branch target**. GitHub will not apply it until you add one.

### In the rulesets UI

1. Open https://github.com/baban9/timeseriesflow/settings/rules
2. Edit your ruleset (or create **New branch ruleset**)
3. Find **Target branches** (or **Ruleset targets** / **Branch targeting**)
4. Click **Add target** or **Add inclusion**
5. Choose one of:
   - **Include default branch**, or
   - **Include by ref name** and enter `main` (full form: `refs/heads/main`)
6. Confirm the warning **"does not target any resources"** is gone
7. Set **Enforcement status** to **Active** (not "Disabled" or evaluate-only)
8. Under **Rules**, enable:
   - **Require a pull request before merging** (1 approval)
   - **Require status checks to pass**: `test (3.10)`, `test (3.11)`, `test (3.12)`
   - **Block force pushes**
9. Click **Create** or **Save changes**

### Common mistakes

| Mistake | Fix |
|---------|-----|
| Rules defined but no branch target | Add `main` under Target branches |
| Enforcement disabled | Set to **Active** |
| Wrong branch pattern | Use `main` or `refs/heads/main`, not empty string |
| Saved ruleset without clicking Add | Target must appear in the inclusion list |

## Apply via script (recommended)

```bash
gh auth login
cd /path/to/timeseriesflow
./.github/scripts/enable_branch_protection.sh main
```

The script creates a ruleset with `refs/heads/main` in `conditions.ref_name.include`.

## Classic branch protection (alternative)

If rulesets are confusing, use the older UI:

1. https://github.com/baban9/timeseriesflow/settings/branches
2. **Add branch protection rule**
3. Branch name pattern: `main`
4. Enable PR reviews (1) and required status checks

## Required rules summary

| Rule | Value |
|------|-------|
| Target branch | `refs/heads/main` |
| Require pull request | Yes |
| Required approving reviews | 1 |
| Dismiss stale reviews on new pushes | Yes |
| Require conversation resolution | Yes |
| Require status checks | `test (3.10)`, `test (3.11)`, `test (3.12)` |
| Require branches up to date | Yes |
| Allow force pushes | No |
| Allow deletions | No |

## Workflow after protection is enabled

```bash
git checkout -b feature/my-change
# make changes, commit
git push -u origin feature/my-change
gh pr create --fill
# wait for CI, review, approve, merge
```
