# Sprint UI-05: Consumable (Lite)

> Executor: Codex. Time-box: **25 minutes**. Starts **only after the human has merged PR #3 into `main`** (using a merge commit).
> Branch: `feat/ui-05-consumable`, created from the updated `main`. Output: a new PR for human review.

## 1. Goal

Make the engine usable by a product repo and by AI agents without hand-holding: a machine-readable component manifest, a correct package contract, a proven Next.js consumption path, and an agent skill file.

## 2. Hard rules

1. Do **not** merge. Do **not** use `--admin`. Never rewrite history. No force-push.
2. Atomic commits, one logical change each. No empty or filler commits.
3. Push after every commit.
4. No secrets.
5. Do not change component behavior or visual design. If a consumption test exposes a real bug, fix it minimally in its own commit and record it in the evidence file.
6. Claims in docs must be backed by a test or evidence file you produced.
7. Allowed paths: `tools/`, `scripts/`, `docs/`, `examples/`, `design/contracts/`, `packages/*/package.json` (exports and metadata only), `README.md`, `CHANGELOG.md`, `AGENTS.md` (append a pointer only), CI config, tests.

## 3. Step 0: sync and release (3 minutes)

- Confirm PR #3 is merged: `git checkout main && git pull`. If it is not merged, **stop and report**.
- Confirm `git config user.email` matches a verified GitHub email. If not, stop and report.
- Tag `v2.1.0` on `main` and create a GitHub release with notes taken from `CHANGELOG.md` (`gh release create v2.1.0 --notes-file ...`). Only if CI on `main` is green.
- `git checkout -b feat/ui-05-consumable`.

## 4. Tasks (priority order)

**T1. Components manifest.** Produce a machine-readable manifest of every registered element: tag name, attributes and types, events (with detail shape), slots, CSS custom properties consumed, CSS parts, and keyboard behavior. Use the Custom Elements Manifest format if practical, otherwise `components.json` with a documented schema. Combine introspection (registered elements and `observedAttributes` in a headless browser) with hand-written metadata in `design/contracts/*.json`. Add a script `npm run manifest` and a test that **fails if any registered element is missing from the manifest.**

**T2. Package contract.** For `packages/engine` and `packages/tokens`: correct `exports` map (ESM, with types), `types`, `sideEffects`, `files`, `version`. Add a test that runs `npm pack`, installs the tarball into a temp project, imports the package, and asserts the elements register.

**T3. Next.js consumption proof (must-have).** Create `examples/nextjs-consumer/`, a minimal Next.js App Router app that:
- installs the engine from the packed tarball or workspace,
- registers the elements only on the client (a small `"use client"` loader pattern that avoids SSR errors),
- includes typed JSX declarations so `ui-*` elements type-check,
- renders at least a button, input, dialog and tabs,
- passes `next build`.
Add a CI job for it. Record the SSR and hydration pitfalls you hit in `docs/consuming.md`.

**T4. Agent skill file.** `docs/agent/UI-ENGINE-SKILL.md`, written for coding agents (Opencode, Codex, Claude). It must state: use `ui-*` primitives and generated tokens only; never hard-code colors, spacing or motion; where the manifest lives; run `design-lint` before closing any UI task; forbidden patterns with a correct and incorrect example each; and a copy-paste prompt preamble. Append a pointer to it in `AGENTS.md`.

**T5. Consumption guide.** `docs/consuming.md`: install paths (npm or git, CDN), semver and breaking-change policy, theming with the three themes, using the components from plain HTML, Next.js and React 19 (props, events), SSR notes, and an honest "known limits" section.

**T6. Cross-browser CI (stretch).** Run the component tests on Firefox and WebKit as well as Chromium. If a browser fails, record the failures in evidence, mark the job allowed-to-fail, and open a GitHub issue per distinct failure. Do not fix them in this sprint.

**T7. Visual regression baseline (stretch).** Screenshot snapshots for each primitive in each theme with a Playwright snapshot test, plus CI wiring. Baselines are committed.

**T8. Close.** Update `CHANGELOG.md`, write `docs/evidence/ui-05/VERIFICATION.md` (commands run, outputs, what is and is not proven), open the PR, ensure CI is green.

## 5. Cut-lines

Drop in this order: T7, T6, T5 (shorten, don't delete). **Never drop T1 to T4 or T8.**

## 6. Acceptance criteria

- [ ] `v2.1.0` tag and release exist (or a clear reason is reported).
- [ ] Manifest exists, and a test fails when an element is missing.
- [ ] Packed-tarball import test passes in CI.
- [ ] `examples/nextjs-consumer` builds in CI.
- [ ] Agent skill file exists, `AGENTS.md` points to it.
- [ ] CI is green on the PR; the PR is open and not merged.
- [ ] No history rewritten.

## 7. Stop conditions

Stop, commit, push and report if: PR #3 is not merged; the git identity check fails; CI is red after 4 fix attempts; a step needs history rewriting, merging, secrets, or edits outside the allowed paths; or the 25-minute time-box ends.

## 8. Final report (return only this)

PR link and CI status, commits pushed (hash and subject), what was cut or failing, the manifest path, and one line: "Ready for human merge: yes/no."
