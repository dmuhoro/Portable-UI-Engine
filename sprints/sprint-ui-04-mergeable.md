# Sprint UI-04: Mergeable and Trusted

> Executor: Codex. Time-box: **30 minutes**. Branch: `audit/ui-00-baseline` (PR #3 already open against `main`).
> Success is a PR that is **green on GitHub CI, independently verified, honest in its claims, and ready for the human to merge.**

## 1. Goal

Turn PR #3 (Portable UI Engine 2.1.0 design system delivery) from "passes on my machine" into "passes on GitHub, proves its gate can fail, and makes only claims that are measured."

## 2. Hard rules

1. Do **not** merge the PR. Do **not** use `--admin` or any bypass. The human merges.
2. Do **not** rewrite history. No force-push, no rebase, no squash. Commits already on the branch stay as they are.
3. **Atomic commits.** One logical change per commit, clear message. Never create empty, whitespace-only or filler commits to raise a count.
4. **Push after every commit** (`git push`), so progress survives if time runs out.
5. No secrets. Never read or print `.env`.
6. Every claim in docs must link to evidence you produced in this sprint, or be removed or softened.
7. Allowed paths: `.github/`, `tools/`, `scripts/`, `docs/`, `README.md`, `CHANGELOG.md`, `package.json` scripts, test files and fixtures, and test or CI configuration. Do not change component behavior or visual design unless a CI-exposed bug requires it. If it does, fix minimally and record it in the evidence file.

## 3. Pre-flight (do first, 3 minutes)

- `git config user.email` must match an email verified on the human's GitHub account. If it does not, **stop and report**. Commits made under another identity will not count on the contribution graph.
- `gh auth status` works. Working tree is clean. Branch is up to date with its remote.
- Record the output in `docs/evidence/ui-04/preflight.md` and commit.

## 4. Tasks (priority order)

**T1. Diagnose missing CI.** PR #3 showed no checks. Find out why (workflow `on:` triggers, Actions disabled or needing approval, YAML errors, runner path assumptions). Write the finding in `docs/evidence/ui-04/ci-diagnosis.md`.

**T2. Fix triggers.** Workflows must run on `pull_request` (targeting `main`) and on `push` to `main`. Commit.

**T3. Make tests run on GitHub runners.** Remove any dependency on a local Chrome path. Install the browser in CI (Playwright or setup-chrome on `ubuntu-latest`), use dependency caching, and make the test command identical locally and in CI.

**T4. Green CI.** Push and watch the run (`gh run watch`). Iterate on real failures. **Max 4 fix attempts.** If still red, stop and report the exact failing step and log excerpt.

**T5. Negative gate test (must-have).** Add fixtures under `tools/design-lint/fixtures/` that deliberately violate the rules: a hard-coded color, a missing focus style, an animation without a reduced-motion guard. Add a test that runs design-lint on each fixture and **asserts a non-zero exit code**. Run it in CI. This proves the gate can fail.

**T6. Measure, don't claim.** Script `scripts/measure-bundles.mjs`: raw, minified and gzip sizes for each distributable engine bundle. Write results and the exact method to `docs/evidence/ui-04/bundle-size.md`. Update the README's size claim to the **measured** number. In the README comparison table, mark any cell that cannot be verified from this repo as "not independently verified" or remove it.

**T7. Quick-start proof.** A browser test that loads the README's quick-start snippet from a local server and asserts the custom elements are registered and render. Run it in CI.

**T8. Independent clean-clone check.** `scripts/verify-clean-clone.sh`: clone the branch into a temp dir, run `npm ci`, lint, test and build, and print a PASS/FAIL summary. Save the output in `docs/evidence/ui-04/clean-clone.md`.

**T9. UI-00 gap list.** List which deliverables promised by `sprints/sprint-ui-00-baseline-audit.md` exist and which do not (claims, scorecard, screenshots, axe results, REPORT). Record it in `docs/evidence/ui-04/ui-00-gap-list.md`. Do not backfill beyond what T6 and T7 already cover.

**T10. Scope guard (should-have).** `tools/scope-guard.mjs` fails if a PR changes files outside a path allowlist read from `design/scope-allowlist.json`. Add a CI job for it. Start the allowlist permissive and document how to tighten it per sprint.

**T11. PR hygiene.** Update the PR description with: what CI now proves, the evidence file links, the known limits (Run Theater is simulated, axe is a regression check not a certification, Chrome-only until UI-05), and the line "Merge using a **merge commit**." Add a `CHANGELOG.md` entry. Commit and push.

## 5. Cut-lines

If time is running out, drop in this order: T10, T9, T8. **Never drop T1 to T5 or T11.**

## 6. Acceptance criteria

- [ ] CI runs on the PR and is green.
- [ ] The negative gate test exists, runs in CI, and passes (meaning lint correctly fails on every bad fixture).
- [ ] README size claim equals a measured number, with its method in evidence.
- [ ] Unverifiable README comparison cells are marked or removed.
- [ ] Quick-start test runs in CI.
- [ ] Preflight confirms the git identity matches a verified GitHub email.
- [x] No history rewritten; PR merged with merge commit (PR #3 merged, 77d0350).
- [x] PR description and CHANGELOG updated (v2.1.0 tagged/released).

## 7. Stop conditions

Stop, commit what is done, push, and report if: preflight identity fails; CI is still red after 4 fix attempts; any step would need history rewriting, merging, secrets, or editing outside the allowed paths; or the 30-minute time-box ends.

## 8. Final report (return only this)

PR link and CI status, a list of commits pushed (hash and subject), what was measured (size numbers), anything cut or failing, and one line: "Ready for human merge: yes/no."
