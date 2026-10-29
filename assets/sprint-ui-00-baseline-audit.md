# Sprint UI-00: Baseline Audit of Portable-UI-Engine

> Task document for Opencode running under Software Factory.
> Rename this file to match the repo's existing `sprints/` naming convention before starting.

## 1. Goal

Produce an evidence-backed baseline of the current Portable-UI-Engine: what it really is, what its README claims versus what is true, and how it scores against a design-quality rubric. **No product code changes in this sprint.**

## 2. Context

- Repo: `github.com/dmuhoro/Portable-UI-Engine` (package name `@universal-ui/engine`).
- Zero-dependency Web Components with Shadow DOM, design tokens in `theme.css`, six components (`app-shell`, `form`, `data-table`, `metric-grid`, `saas-dashboard`, `billing-funnel`), six theme presets, an AI bridge, build via `build.js` / `vite.config.ts`, QA script `qa-pressure-test.js`, and a `tests/` folder.
- Downstream plan (do not start it here): monorepo restructure, token pipeline, new primitives, accessibility work, docs site, Teardown Lab, and a design gate in Software Factory. This audit is the baseline all of that is measured against.
- Read `README.md`, `CONTRIBUTING.md`, `ai-generator-prompt.md`, `sprints/`, `tests/` and `elements/` first. Do not rely on this document's description of them.

## 3. Hard rules

1. **Read-only on existing source.** Do not edit, move or delete anything under `src/`, `elements/`, `tests/`, or any root `.js`, `.css`, `.html`, `.json` or `.ts` file.
2. All new files go under `audit/`. Audit tooling is installed only inside `audit/` with its own `package.json`. Do not change the root `package.json` or lockfile.
3. Work on branch `audit/ui-00-baseline`. Open a PR. **Never merge it. Never use `--admin` or any bypass.**
4. No secrets. Do not read, print or commit `.env` contents. Only `.env.example` may be read.
5. Do not publish, deploy, tag or release anything.
6. Every claim in a report must link to an evidence file or a command output saved in `audit/`. No evidence, no claim.
7. Commit in small steps with clear messages, one per task.

## 4. Out of scope

Fixing anything found, refactoring, adding components, changing themes, changing the README, restructuring the repo, launching the HN or Reddit drafts.

## 5. Tasks

**T1. Inventory.** Map the repo: every component, its attributes, slots and events, theme presets, scripts, tests, sprints, open issue and open PR (read them). Output `audit/inventory.md`.

**T2. Verify the README claims.** For each claim in the README, mark `verified`, `false` or `unverifiable`, with evidence. At minimum check:
- Bundle size claim ("under 15KB minified and gzipped"): run the build, measure raw, minified and gzip sizes of the real output.
- "Zero dependencies" and "zero build steps": check `package.json`, imports and the CDN quick-start path.
- "100% Shadow DOM encapsulation": check every component.
- The comparison table: list which cells cannot be verified from the repo alone.
- The quick-start snippet: does it work as written when served locally?
Output `audit/claims.md`.

**T3. Run the existing quality checks.** Run the repo's own tests, `qa-pressure-test.js`, lint and build. Record exact commands, exit codes, outputs and failures in `audit/checks.md`. Do not fix failures.

**T4. Rubric v1.** Write `audit/rubric-v1.md`: a machine-readable and human-readable rubric for judging UI quality. Score each criterion 0 to 4 with a written anchor for each level. Required criteria:
- Visual hierarchy and layout
- Typography scale and rhythm
- Color and contrast (WCAG AA)
- Spacing system consistency
- Interaction states (hover, focus, active, disabled, loading, error, empty)
- Motion (purposeful, reduced-motion respected)
- Keyboard operability and focus management
- Screen-reader semantics (roles, names, labels, live regions)
- Responsiveness (320, 768, 1280 px)
- Theming and token discipline (no hard-coded values)
- API contract clarity and documentation
- Performance and bundle weight
Also emit `audit/rubric-v1.json` with the same content.

**T5. Capture screenshots.** For every component, in light and dark and in each of the six theme presets, at 320, 768 and 1280 px wide. Use a headless browser installed under `audit/`. Save to `audit/screenshots/<component>/<theme>-<width>.png` and produce an index.

**T6. Accessibility audit.** Run axe-core against each component page and the sandbox. Test keyboard-only flows for the form, data table, app shell drawer and billing funnel. Save raw JSON under `audit/a11y/` and a summary in `audit/a11y/SUMMARY.md`. Note specifically: label association across shadow boundaries, native form participation, focus traps, and `prefers-reduced-motion`.

**T7. Token and contrast audit.** Extract every token from `theme.css` and the theme presets. Compute contrast ratios for text and surface pairs in every theme and flag AA failures. List hard-coded colors, sizes and radii found inside components that bypass tokens. Output `audit/tokens.md` and `audit/contrast.json`.

**T8. Score.** Apply the rubric to each component and to the system as a whole. Output `audit/scorecard.json` and `audit/scorecard.md`. Each score cites evidence from T2 to T7.

**T9. Report.** Write `audit/REPORT.md`:
- One-paragraph verdict on what the engine is today.
- Claims table (from T2).
- Scorecard summary.
- Top 10 findings ranked by impact on the "elite design quality" goal, each with evidence and a suggested fix.
- Risks for adopting this in Next.js apps (SSR, hydration, React event and prop interop, Tailwind not reaching shadow roots, form association).
- Recommended order of work for the next sprints.
- Open questions for the human. These are listed, not blocking.

**T10. Run log.** `audit/RUN-LOG.md`: model used, start and end time, commands run, anything skipped and why.

## 6. Acceptance criteria

- [ ] All files in section 7 exist and are non-empty.
- [ ] `git diff main --stat` shows changes **only** under `audit/`.
- [ ] Every README claim has a status and evidence.
- [ ] The bundle size figure is measured and reported with its exact method.
- [ ] Every component has screenshots for all themes and widths, or a documented reason one is missing.
- [ ] Every component has an axe result file.
- [ ] Every score in the scorecard cites at least one evidence file.
- [ ] Failures in existing checks are recorded, not hidden or fixed.
- [ ] A PR is open on `audit/ui-00-baseline` and is not merged.

## 7. Deliverables

```
audit/
  package.json            (audit tooling only)
  inventory.md
  claims.md
  checks.md
  rubric-v1.md
  rubric-v1.json
  screenshots/
  a11y/
  tokens.md
  contrast.json
  scorecard.md
  scorecard.json
  REPORT.md
  RUN-LOG.md
```

## 8. Gates and evidence

| Gate | Evidence |
|---|---|
| Scope | `git diff main --stat` limited to `audit/` |
| Reproducibility | Every command and its output logged in `checks.md` or `RUN-LOG.md` |
| Claims | `claims.md` complete, with measured sizes |
| Coverage | Screenshot index and axe results present for every component |
| Honesty | Failures and skipped items are listed, not omitted |

## 9. Stop conditions

Stop and report, without improvising, if:
- A gate fails twice after a genuine fix attempt to the audit tooling (not the product code).
- The build or tests cannot run at all. Record why and continue with the remaining tasks that don't depend on them.
- Anything would require editing existing source, touching secrets, merging, or publishing.
- You are about to exceed your model's context or rate limits. Commit your progress, write the state into `RUN-LOG.md`, and stop cleanly so the next run can resume.

## 10. Final report back to the human

When done, return only: the PR link, a five-line summary of the verdict, the three highest-impact findings, anything not completed, and the open questions.
