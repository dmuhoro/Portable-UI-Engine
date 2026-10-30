# Consuming Portable UI Engine

## Install paths

- **npm workspace / local package:** `npm install @universal-ui/engine` (from `packages/engine` once published)
- **Git branch:** `npm install github:dmuhoro/Portable-UI-Engine#main` then import from the package path, or depend on `file:./packages/engine` inside this monorepo
- **CDN / static:** serve `theme.css` + `dist/engine.js` (ESM) or `dist/engine.min.js` (IIFE)

Package contract (verified by `npm run test:pack`):

- `exports["."].import` → `dist/engine.js`
- `exports["./theme.css"]` → `theme.css`
- `sideEffects` marked so bundlers keep registration entrypoints

Tokens package: `@universal-ui/tokens` exports generated CSS (`./css`) and TypeScript (`.`).

## Semver and breaking changes

Current release line: **2.1.0**.

- Patch: bug fixes, a11y, docs, evidence — no intentional API breaks
- Minor: new `ui-*` elements, additive attributes/events, new themes
- Major: rename/remove public tags, change event names, or remove CSS custom properties consumed by public styles

Machine-readable inventory: `design/contracts/components.json` (`npm run manifest`).

## Theming

Three design directions ship as token themes:

1. **Warm Precision** (default) — `data-theme="warm-precision"`
2. **Technical Oceanic** — `window.UniversalUI.setTheme('technical-oceanic')`
3. **Swiss Minimalist** — `window.UniversalUI.setTheme('swiss-minimalist')`

Legacy aliases (`light`, `dark`, `corporate`, `cyberpunk`, `midnight`, `emerald`) map onto these families. Prefer CSS custom properties from `packages/tokens`; never hard-code colors or spacing in product UI.

## Plain HTML

```html
<link rel="stylesheet" href="./theme.css">
<script type="module" src="./dist/engine.js"></script>

<ui-button variant="primary">Save changes</ui-button>
<ui-input label="Workspace name" name="workspace"></ui-input>
```

Listen for composed events: `ui-button-click`, `ui-input-change`, `ui-select-change`, `ui-checkbox-change`, `ui-tab-change`.

## Next.js / React 19

See `examples/nextjs-consumer/`.

1. Import `@universal-ui/engine/theme.css` in a server layout (CSS only).
2. Dynamically `import('@universal-ui/engine')` inside a `"use client"` loader (`useEffect`) so Custom Elements never run during SSR.
3. Add JSX intrinsic typings for `ui-*` tags (see `examples/nextjs-consumer/uie.d.ts`).
4. Treat custom events as DOM events (`addEventListener`), not React `onClick` props on the host.

`next build` for the example is enforced in CI.

**Offline note:** If `npm install` fails with `ENETUNREACH`/missing `next` binary in offline environments, use cached deps or a local workaround. See `examples/nextjs-consumer/README.md`.

## SSR notes / pitfalls

- Custom Elements and Shadow DOM are browser APIs — registering during SSR throws or no-ops incorrectly.
- Hydration: render the custom element tags on the server as empty hosts; the client upgrade attaches shadow roots after import.
- Do not import `engine.js` from a Server Component.

## Known limits

- Run Theater telemetry is **simulated** — not a production cluster connection.
- Automated axe checks are regression guards, not a WCAG certification.
- Browser CI is Chromium-first; Firefox/WebKit are follow-up work.
- Legacy `universal-*` elements remain for compatibility; new product UI should use `ui-*` + tokens.
- Package is not yet published to the public npm registry; consume via git/workspace/tarball until publish automation lands.
