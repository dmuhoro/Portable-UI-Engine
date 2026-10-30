# Portable-UI-Engine Index (READ-ONLY AUDIT)
**Branch:** audit/readiness-20261030  
**PR under review:** #5 (feat/ui-05-consumable → main)  
**Audit date:** 2026-10-30  

## Purpose
Portable UI Engine is a design-system/engine repo publishing web components (`ui-*`), tokens, and consumption tooling. It is meant to be consumed by product repos via package exports/manifest/guide.

## Groups (count)
See `index.json` for full lists.

## Packages
- `packages/engine/` - engine package (exports, types, built assets)
- `packages/tokens/` - tokens package (exports, CSS vars)

## Apps
- `apps/docs/`, `apps/run-theater/`, `apps/pattern-foundry/`, `apps/commit-garden/`

## Tools
- `tools/design-lint/`, `tools/scope-guard.mjs`

## Scripts (gates)
- `scripts/test-manifest.mjs`, `scripts/test-pack-import.mjs`, `scripts/test-quick-start.mjs`, `scripts/test-negative-gate*`, `scripts/verify-clean-clone.sh`, `scripts/generate-manifest.mjs`

## Design
- `design/contracts/components.json` (manifest), `design/scope-allowlist.json`, directions/briefs/compositions

## Consumption
- `examples/nextjs-consumer/` (Next.js App Router proof)
- `docs/consuming.md`, `docs/agent/UI-ENGINE-SKILL.md`

## CI
- `.github/workflows/ci.yml` (UI-04/UI-05 gates)

## Software Factory
- Local checkout exists at `/home/daniel-muhoro/workspace/projects/Software-Factory/` (read-only inspection not yet done).
