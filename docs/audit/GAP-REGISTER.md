# GAP REGISTER

| id | severity | gap | evidence | effort | owner | deps |
|---|---|---|---|---|---|---|
| G-001 | blocker | Next.js consumer build fails in CI (missing JSX types for ui-*) | docs/audit/evidence/ci_nextjs_failure.txt | S | design/frontend | none |
| G-002 | blocker | PR #5 CI failing; not review-ready/mergeable | gh pr checks 5 | S | design/frontend | G-001 |
| G-003 | major | No release/tag for UI-05 changes | CHANGELOG [Unreleased], no new tag | S | ops/release | G-002 |
| G-004 | major | tasks/MASTER-TODO.md not fully swept | tasks/MASTER-TODO.md | XS | design/frontend | none |
| G-005 | minor | Stash referenced in docs but missing; state unclear | git stash list empty | XS | design/frontend | none |
