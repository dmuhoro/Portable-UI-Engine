# UI-00 gap list (Sprint UI-04 T9)

**Date:** 2026-10-28  
**Branch:** `audit/ui-00-baseline`

`sprints/sprint-ui-00-baseline-audit.md` is not present in the tree. Gaps below are relative to the baseline expectations referenced by Sprint UI-04 and the Constitution (evidence-first, mechanical gates).

| Deliverable | Status | Evidence / notes |
| --- | --- | --- |
| Constitution | Present | `docs/CONSTITUTION.md` |
| ADRs 0001–0003 | Present | `docs/adr/0001-monorepo-structure.md`, `0002-tokens-as-source-of-truth.md`, `0003-design-gate-teardown-lab.md` |
| Architecture overview | Present | `docs/architecture/OVERVIEW.md` |
| Design lint gate | Present | `tools/design-lint/index.mjs` |
| Negative gate (gate can fail) | Present (UI-04) | `npm run test:negative-gate` + fixtures |
| Bundle size measured | Present (UI-04) | `docs/evidence/ui-04/bundle-size.md` |
| Quick-start proof | Present (UI-04) | `npm run test:quick-start` |
| Clean-clone script | Present (UI-04) | `scripts/verify-clean-clone.sh` |
| Scope guard | Present (UI-04) | `tools/scope-guard.mjs` (allowlist starts permissive `*`) |
| UI-00 scorecard / screenshots pack | Not backfilled | Explicitly out of UI-04 cut-line; do not invent screenshots |
| UI-00 axe REPORT artifact set | Partial | Showcase axe runs live in `npm test`; no separate UI-00 REPORT folder |

## Verdict

Baseline governance artifacts exist. UI-04 closes the mechanical trust gaps (CI triggers, negative gate, measured size, quick-start). Historical screenshot/scorecard packs are not fabricated.
