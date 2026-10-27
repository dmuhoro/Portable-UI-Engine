# Sprint UI-04 CI Diagnosis

**Date:** 2026-10-27  
**PR:** [#3](https://github.com/dmuhoro/Portable-UI-Engine/pull/3)

## Findings

1. Repository Actions are enabled. `gh api repos/dmuhoro/Portable-UI-Engine/actions/permissions --jq '{enabled, allowed_actions}'` returned `{"allowed_actions":"all","enabled":true}`.
2. PR #3 is open, targets `main`, and its status check rollup is empty. `gh run list --branch audit/ui-00-baseline` returns no runs.
3. The PR branch contains `.github/workflows/ci.yml`, but `git show origin/main:.github/workflows/ci.yml` fails because that file does not exist on `main`; GitHub's workflow lookup by `ci.yml` also returned 404. GitHub cannot start the newly introduced `pull_request` workflow from a PR before that workflow exists on the base branch.
4. The workflow's declared event filters already meet the requested contract: `pull_request` targeting `main`, and `push` to `main`. No trigger defect was found.
5. The test setup hard-codes `/usr/bin/google-chrome` in the Web Test Runner config and showcase browser script. The CI job does not provision Chrome or pass a discovered browser path.

## Gate boundary

The workflow must enter `main` before GitHub can register it for PR events. Sprint UI-04 forbids merging and requires the human to merge. Therefore a green GitHub check for PR #3 cannot be demonstrated from the current branch without the prohibited merge. The browser provisioning and path fixes are made separately so the workflow is ready to execute once registered.
