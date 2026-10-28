# Portable UI Engine Architecture

Portable UI Engine is a small monorepo for an independently distributable Web Component engine, design tokens, internal quality tools, and browser-based showcase apps.

## Boundaries

```text
packages/tokens -> generated CSS custom properties and TypeScript token map
elements/       -> source for new engine primitives
packages/engine -> standalone package mirror and distributable bundle
apps/*          -> browser demos consuming the engine and tokens
tools/*         -> lint and design-system quality gates
design/         -> approved specifications and interaction contracts
```

The root `engine.js` remains the backward-compatible registration entry point for the existing `universal-*` components. New primitives are registered under the `ui-*` names in the design briefs. The standalone `packages/engine` package mirrors the source needed to build and run without reaching outside that package.

## Component runtime

- Components extend `HTMLElement` and attach open Shadow DOM roots.
- Public state is exposed through attributes or typed JavaScript properties.
- Component events are `CustomEvent`s with `{ bubbles: true, composed: true }`.
- Component styles consume CSS custom properties from the generated token contract.
- Native browser controls are used where they provide robust semantics, top-layer behavior, and focus management.
- Engine code has no framework runtime dependency; the root workspace also contains development and showcase dependencies.

## Token flow

1. Warm Precision is the canonical token source in `packages/tokens/design-tokens.json`.
2. Technical Oceanic and Swiss Minimalist are complete theme token sets in `packages/tokens/themes/`.
3. `packages/tokens/scripts/build-tokens.js` generates the semantic CSS variables, compatibility aliases, and TypeScript token map.
4. The generated token contract is applied after legacy global styles in `theme.css` so design themes take precedence.
5. Showcase apps consume the same stylesheet and engine entry used by integrations.

## Builds and quality gates

`build.js` creates ESM and minified IIFE bundles for both the root package and `packages/engine`. Vite builds the browser showcase into `dist/site` without deleting engine bundles. CI regenerates tokens, runs strict TypeScript checking, runs the design lint, executes component and browser showcase tests, and builds both distributions and the showcase site.

See [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md) and the [ADRs](docs/adr/README.md) for recorded decisions.
