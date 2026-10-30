# UI Engine Skill — Portable UI Engine

Use this skill whenever you build or change UI in a repo that consumes Portable UI Engine.

## Non-negotiables

1. Use **`ui-*` primitives** from `@universal-ui/engine` (or the mirrored `elements/` / `packages/engine` sources). Do not invent parallel components.
2. Style only through **design tokens** — CSS custom properties generated from `packages/tokens/design-tokens.json`. Never hard-code colors, spacing, radii, or motion durations.
3. Respect **Shadow DOM**: theme via custom properties on ancestors / `data-theme`; do not pierce internals except documented CSS parts.
4. Run **`npm run design:lint`** (or `node tools/design-lint/index.mjs`) before closing any UI task. The gate must pass.
5. Prefer evidence over claims: browser tests, axe checks, and sprint evidence files.

## Where things live

| Need | Path |
| --- | --- |
| Component inventory | `design/contracts/components.json` (`npm run manifest`) |
| Token source | `packages/tokens/design-tokens.json` |
| Generated CSS/TS | `packages/tokens/css/variables.css`, `packages/tokens/ts/tokens.ts` |
| Primitive source | `elements/ui-primitives.js` (mirrored under `packages/engine/elements/`) |
| Agent conventions | `AGENTS.md`, `docs/CONSTITUTION.md` |
| Consumption | `docs/consuming.md`, `examples/nextjs-consumer/` |

## Commands

```bash
node packages/tokens/scripts/build-tokens.js
npm run design:lint
npm run test:negative-gate   # proves the gate can fail
npm test
npm run test:quick-start
npm run test:manifest
npm run test:pack
npm run build:engine
```

## Forbidden vs correct

❌ `color: #ff0000` / `padding: 16px` / `transition: all 0.3s` without tokens or reduced-motion  
✅ `color: var(--color-text-primary)` / `padding: var(--spacing-md)` / motion tokens + `@media (prefers-reduced-motion: reduce)`

❌ New one-off `<button class="primary">` in product UI  
✅ `<ui-button variant="primary">Save</ui-button>`

## Copy-paste preamble for agents

```
You are working in the Portable UI Engine ecosystem.
Use ui-* primitives and packages/tokens only.
Never hard-code colors, spacing, or motion.
Run design-lint before finishing.
Consult design/contracts/components.json for the element inventory.
Follow docs/CONSTITUTION.md, ADRs, and docs/architecture/OVERVIEW.md.
```
