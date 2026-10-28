# Portable UI Engine

Portable UI Engine is a framework-agnostic design system built from native Web Components. It provides token-based themes, isolated component styles, browser-native accessibility behavior, and showcase applications for trying and reviewing the system.

## Try the showcase

```bash
npm install
npm run dev
```

Open the Vite server at `http://localhost:3000`, then visit:

- `/apps/docs/` — searchable component gallery and live token inspector.
- `/apps/teardown-lab/` — rubric assessment and candidate/baseline comparison.
- `/apps/run-theater/` — simulated operations dashboard. It does not connect to a production cluster.

## Use the engine

The engine registers the existing `universal-*` elements and the design-system primitives:

`<ui-button>`, `<ui-input>`, `<ui-checkbox>`, `<ui-select>`, `<ui-dialog>`, `<ui-tooltip>`, `<ui-toast>`, `<ui-tabs>`, and `<ui-menu>`.

Load the stylesheet and ESM bundle from a built distribution or package CDN:

```html
<link rel="stylesheet" href="./theme.css">
<script type="module" src="./engine.js"></script>

<ui-button variant="primary">Save changes</ui-button>
<ui-input label="Workspace name" name="workspace"></ui-input>
```

Components render inside open Shadow DOM roots and emit bubbling, composed `CustomEvent`s. For example, listen for `ui-button-click`, `ui-input-change`, `ui-select-change`, `ui-checkbox-change`, and `ui-tab-change` on the component or an ancestor. Properties such as `ui-select.options`, `ui-tabs.items`, and `ui-menu.items` accept arrays; their documented HTML attributes remain usable for simple values.

All primitive styling reads CSS custom properties generated from `packages/tokens/design-tokens.json`. The default theme is **Warm Precision**. **Technical Oceanic** and **Swiss Minimalist** are available through the theme controller:

```js
window.UniversalUI.setTheme('technical-oceanic');
window.UniversalUI.setTheme('swiss-minimalist');
```

Legacy theme names remain accepted: `light`, `dark`, `corporate`, `cyberpunk`, `midnight`, and `emerald` map to the corresponding design direction families.

## Repository layout

```text
packages/engine  distributable Web Components package
packages/tokens  W3C token source and generated CSS/TypeScript
elements/        engine primitive sources
apps/            component gallery, teardown lab, and run theater
tools/           design-system quality gates
design/          approved design directions, briefs, and compositions
docs/            architecture, ADRs, and evidence
```

## Development and verification

```bash
node packages/tokens/scripts/build-tokens.js  # regenerate CSS and token types
npm run lint                                   # strict TypeScript check
node tools/design-lint/index.mjs               # design gate
npm test                                       # component and showcase browser tests
npm run build                                  # engine bundles and showcase site
```

`npm run build:engine` builds both the repository distribution and the standalone `packages/engine` distribution. The browser test runner uses the installed Chrome executable; set `CHROME_PATH` when Chrome is installed elsewhere.

## Project rules

See [the Constitution](docs/CONSTITUTION.md), [architecture overview](docs/architecture/OVERVIEW.md), [ADRs](docs/adr/README.md), and [engineering conventions](AGENTS.md). Product decisions and implementation status are tracked in [sprints](sprints/README.md) and [the changelog](CHANGELOG.md).
