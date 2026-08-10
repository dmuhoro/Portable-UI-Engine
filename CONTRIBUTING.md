# 🛠️ Contributing to Portable UI Engine (`@universal-ui/engine`)

Thank you for your interest in contributing to the **Portable UI Engine**! We build framework-agnostic, zero-dependency, high-performance UI primitives using native Web Components (Custom Elements) and Shadow DOM.

---

## 📜 The Golden Rules of the Engine

To maintain high code quality, extreme performance, and portable browser execution, all custom elements submitted to `@universal-ui/engine` must adhere strictly to these engineering constraints:

1. **Zero External Dependencies**: Never add NPM runtime dependencies (e.g., React, jQuery, Lodash, Moment, Tailwind runtime scripts). All components must run on standard ES6+ browser APIs.
2. **Shadow DOM Encapsulation (`mode: 'open'`)**: Every visual element MUST encapsulate its markup and styles using `this.attachShadow({ mode: 'open' })`. Global application CSS must not break component layouts, and component styles must never leak into the host DOM.
3. **CSS Variable Design Tokens**: Hardcoded HEX or RGB colors inside components are strictly prohibited. Always consume design tokens defined in `theme.css` (e.g., `var(--color-primary)`, `var(--color-bg-surface)`, `var(--font-sans)`, `var(--radius-md)`).
4. **Data-Driven Props & Attributes**: Components must ingest data via standard HTML attributes or JavaScript properties (JSON strings or arrays/objects). Always wrap `JSON.parse()` calls inside `try / catch` blocks to prevent page crashes.
5. **Native Event Emissions**: Components communicate state changes upwards by dispatching standard `CustomEvent` instances configured with `{ bubbles: true, composed: true }`.

---

## 💻 Local Development Setup

Follow these steps to set up your local development environment:

### 1. Fork and Clone the Repository

```bash
git clone https://github.com/dmuhoro/Portable-UI-Engine.git
cd Portable-UI-Engine
```

### 2. Install Dev Dependencies

```bash
npm install
```

### 3. Launch Local Preview Server

Start the Vite development server with hot reload:

```bash
npm run dev
```
Open `http://localhost:3000` in your browser to view the interactive showcase and test bench.

### 4. Build and Verify Production Bundles

Compile both the ES Module (`dist/engine.js`) and minified IIFE CDN wrapper (`dist/engine.min.js`) using `esbuild`:

```bash
npm run build:engine
```

Validate TypeScript type definitions and code rules:

```bash
npm run lint
```

---

## 📐 Pull Request (PR) Quality Gate Checklist

Before opening a Pull Request, verify that your contribution satisfies the following requirements:

| Checklist Item | Requirement Details | Status |
| :--- | :--- | :---: |
| **Vanilla Architecture** | Class extends `HTMLElement` with no external runtime libraries | [ ] |
| **Shadow DOM Mode** | `this.attachShadow({ mode: 'open' })` initialized in constructor | [ ] |
| **Design Tokens Used** | All colors, radii, fonts, and spacing use `var(--color-*)` tokens | [ ] |
| **Defensive JSON Parsing** | All stringified attributes use `try/catch` and render error states | [ ] |
| **Event Composition** | Custom events use `{ bubbles: true, composed: true }` | [ ] |
| **Cross-Browser Test** | Component tested in Chrome, Firefox, and Safari | [ ] |
| **Custom Element Check** | Guarded registration: `if (!customElements.get('element-tag'))` | [ ] |

---

## 🧱 Creating a New Component

To create a new component, copy the blueprint boilerplate from `elements/template-primitive.js`:

```bash
cp elements/template-primitive.js elements/universal-my-component.js
```

Export and register your new component inside `engine.js`:

```javascript
import './elements/universal-my-component.js';
```

Thank you for helping us make web UI portable, fast, and framework-free! 🚀
