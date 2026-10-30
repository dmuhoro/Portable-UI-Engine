# Sprint UI-04 verification

**Date:** 2026-10-28  
**Branch:** `audit/ui-00-baseline`

## Commands

```bash
node packages/tokens/scripts/build-tokens.js
npm run check:version
npm run lint
node tools/design-lint/index.mjs
npm run test:negative-gate
npm run scope-guard -- --base origin/main
npm run build
npm test
npm run test:quick-start
npm run measure:bundles
```

## Proven

- Design-lint default mode passes on `elements/`.
- Negative fixtures under `tools/design-lint/fixtures/` each exit non-zero (`test:negative-gate`).
- README quick-start registers `ui-button` and `ui-input` with shadow roots (`test:quick-start`).
- Bundle sizes measured via `scripts/measure-bundles.mjs` and linked from README.
- CI workflow runs on `pull_request` → `main` and `push` → `main`, installs Chrome, runs gates above.
- Scope guard runs; allowlist currently permissive (`*`) pending per-sprint tightening.
- Showcase kill path no longer throws `EACCES` when terminating Vite in restricted environments.

## Not proven / known limits

- Firefox/WebKit CI (deferred to UI-05 stretch / later).
- Merge to `main` and `v2.1.0` tag require human/CI merge process after green checks.
- Run Theater remains simulated telemetry.
- axe checks are regression guards, not certification.
