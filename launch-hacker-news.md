# Show HN: Portable UI Engine – Framework-Agnostic Web Components with Zero Runtime Dependencies

**Title:** Show HN: Portable UI Engine – Framework-Agnostic Web Components with Zero Dependencies & AI Gateway Contracts

---

## Post Body

Hey HN,

I built **Portable UI Engine** (`@universal-ui/engine`) because I got tired of re-writing the same dashboards, data grids, forms, and billing UI components every time I switched backend stacks or front-end frameworks.

As a solo engineer moving between Go, Python (FastAPI/Django), Rust, and Rails, I kept hitting the same wall: whenever I wanted a clean, responsive SaaS UI, I had to either pull in massive Node build toolchains (Vite, Webpack, Tailwind JIT, React/Vue hydration overhead) or settle for dated Bootstrap templates. When integrating HTMX or server-rendered HTML, front-end state management quickly became fragile.

So I spent the last few months building a **100% native Web Component UI engine** engineered specifically for portable execution in any web environment.

### 🌐 Live Showcase & Interactive Workbench
- **Demo Workbench:** [Portable UI Engine Live Showcase](https://ais-dev-pcysyufvntgq5ciwqii2cf-349849849289.europe-west2.run.app)
- **Isolated Component Sandbox:** [Sandbox Workbench (`sandbox.html`)](https://ais-dev-pcysyufvntgq5ciwqii2cf-349849849289.europe-west2.run.app/sandbox.html)
- **GitHub Repository:** [dmuhoro/Portable-UI-Engine](https://github.com/dmuhoro/Portable-UI-Engine)

---

### ⚡ What Makes It Different?

1. **Zero Runtime Dependencies**
   Built with pure Vanilla ES6+, Custom Elements v1, and Shadow DOM (`mode: 'open'`). No React, no Vue, no virtual DOM, no heavy bundlers required at runtime. Drop a single 18KB minified `<script>` tag or ESM import into any page and it works instantly.

2. **Style Isolation via CSS Variables**
   Every component uses Shadow DOM style encapsulation. Global CSS framework rules (Bootstrap, Tailwind, custom stylesheets) cannot leak into or break component layouts. Full design system token inheritance is handled cleanly via global CSS custom properties (`--color-primary`, `--radius-lg`, `--font-sans`).

3. **HTMX & Server-Rendered HTML Fallback (The HTMX Bridge)**
   While components natively react to JSON string attributes and JS object properties (`element.payload = {...}`), `<universal-data-table>` includes an automatic light-DOM HTML parser. If no JSON payload is passed, it scans its child light DOM for native `<table><thead>...` markup, ingests the cells programmatically, and renders the elite data grid instantly.

4. **WCAG 2.1 AA Enterprise Accessibility**
   Every interactive element includes strict ARIA semantics (`role="table"`, `role="columnheader"`, `aria-sort`, `aria-expanded`, `aria-live="polite"`), native keyboard navigation (Enter/Space triggers, focus outline indicators), and color contrast ratio verification.

5. **Frontier AI Gateway Component (`<universal-ai-bridge>`)**
   Includes a native AI bridge element that establishes standard streaming contracts with server-side AI endpoints (powered by Google Gemini 2.5 Flash / `@google/genai`). You can stream dynamic UI state updates directly from LLM structured outputs into your dashboards and data grids in real time.

6. **Low-Latency Hydration & FOUC Prevention**
   Utilizes a native `:not(:defined)` CSS skeleton baseline to prevent Flash of Unstyled Content during component boot. Includes instant `localStorage` theme state restoration across 6 built-in themes (Light, Dark, Corporate, Cyberpunk, Midnight, Emerald).

---

### 🚀 Quick Start Example

#### CDN / Single HTML File Setup:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@universal-ui/engine@2.0.0/theme.css">
  <script type="module" src="https://cdn.jsdelivr.net/npm/@universal-ui/engine@2.0.0/dist/engine.js"></script>
</head>
<body>
  <!-- Drop in a full SaaS Dashboard with zero JavaScript setup -->
  <universal-saas-dashboard id="dashboard"></universal-saas-dashboard>

  <script>
    document.addEventListener('DOMContentLoaded', () => {
      const db = document.getElementById('dashboard');
      db.state = {
        metrics: [
          { title: "Monthly Recurring Revenue", value: "$128,450.00", change: "+24.5%", trend: "upward", context: "vs Q2 target" },
          { title: "Active API Gateway Tokens", value: "8,940", change: "+14.2%", trend: "upward", context: "99.99% uptime" }
        ],
        tableHeaders: ["Service Endpoint", "Cluster", "Status", "Latency"],
        tableRows: [
          ["/api/v1/auth", "us-east-1", "Active", "12ms"],
          ["/api/v1/inference", "eu-west-1", "Active", "38ms"]
        ]
      };
    });
  </script>
</body>
</html>
```

#### HTMX Declarative Markup Example:
```html
<universal-data-table>
  <table>
    <thead>
      <tr><th>Endpoint</th><th>Protocol</th><th>Latency</th></tr>
    </thead>
    <tbody>
      <tr><td>/api/v1/token</td><td>HTTP/2</td><td>14ms</td></tr>
      <tr><td>/api/v1/stream</td><td>gRPC</td><td>8ms</td></tr>
    </tbody>
  </table>
</universal-data-table>
```

---

### 💬 Technical Feedback & Questions

I'd love to hear your thoughts!
- How are you managing UI component portability across non-Node backend stacks (Go, Rust, Python, Elixir)?
- What additional components or AI streaming patterns would make this engine even more useful for your projects?

Thanks for taking a look!

— Danny ([@dmuhoro](https://github.com/dmuhoro))
