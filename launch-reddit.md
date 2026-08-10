# Portable UI Engine – Reddit Community Launch Scripts

This document contains tailored, direct developer-to-developer posts for Reddit target communities: **r/htmx**, **r/golang**, **r/rails**, and **r/webdev**.

---

## 1. r/htmx – "I built a Shadow DOM Web Component Engine that parses raw HTMX HTML tables automatically"

**Title:** I built a zero-dependency Web Component UI library that automatically parses light-DOM HTMX `<table>` markup

Hey r/htmx,

If you love HTMX like I do, you know the frustration of trying to make rich interactive UI components (like sortable data tables, metric grids, multi-step forms, and dashboards) look clean without pulling in React or complex front-end build pipelines.

I built **Portable UI Engine** (`@universal-ui/engine`) to solve this exact problem. It's a library of native Web Components with Shadow DOM style encapsulation and zero runtime dependencies.

### 🎯 Why HTMX devs will care:

1. **Native HTML Table Fallback (The HTMX Bridge):**
   You don't need to write client-side JavaScript. If you return standard HTML `<table>` markup from your backend endpoint, `<universal-data-table>` automatically ingests the light-DOM markup, parses the headers/cells, and renders a clean data grid with sorting, search filtering, and pagination.

```html
<!-- Your HTMX endpoint returns standard HTML markup inside the Web Component -->
<div id="table-container" hx-get="/api/servers" hx-trigger="load" hx-swap="outerHTML">
  <universal-data-table>
    <table>
      <thead>
        <tr><th>Server</th><th>Region</th><th>Status</th><th>Latency</th></tr>
      </thead>
      <tbody>
        <tr><td>Auth Node 01</td><td>us-east-1</td><td>Active</td><td>12ms</td></tr>
        <tr><td>Worker Node 04</td><td>eu-west-1</td><td>Active</td><td>28ms</td></tr>
      </tbody>
    </table>
  </universal-data-table>
</div>
```

2. **Style Isolation (Shadow DOM `mode: 'open'`):**
   Components won't leak CSS or mess with your global Tailwind/Bootstrap/Custom CSS. They inherit design tokens seamlessly through CSS variables (`--color-primary`, `--radius-lg`).

3. **Zero Runtime Dependencies:**
   One `<script>` tag (~18KB minified) and one `<link rel="stylesheet" href="theme.css">`. No npm build step required.

- **Live Sandbox Workbench:** [Try it live in sandbox.html](https://ais-dev-pcysyufvntgq5ciwqii2cf-349849849289.europe-west2.run.app/sandbox.html)
- **GitHub:** [dmuhoro/Portable-UI-Engine](https://github.com/dmuhoro/Portable-UI-Engine)

Would love your feedback on how this fits into your HTMX workflows!

---

## 2. r/golang – "Building rich admin dashboards in Go without Node/NPM build tools"

**Title:** Portable UI Engine: Drop-in Web Components for Go web apps (Zero Node/NPM required)

Hey Go devs,

When building web applications in Go (using `html/template`, Templ, Echo, Gin, or Fiber), adding responsive SaaS dashboards, data grids, or multi-step forms usually forces you to introduce Node, npm, Vite, or complex JavaScript bundlers into your Go repository.

I wanted a way to ship rich, modern UIs directly from Go templates or static embeds without touching Node build toolchains.

I built **Portable UI Engine** (`@universal-ui/engine`) – a collection of pure native Web Components with zero runtime dependencies.

### 📦 How it works in Go Templates:

1. Include the minified CSS and JS file from a CDN or embed them in your Go binary with `go:embed`.
2. Insert `<universal-saas-dashboard>` or `<universal-data-table>` into your `.html` template.
3. Pass JSON directly from your Go handler or let it parse server-rendered HTML markup.

```html
{{define "dashboard.html"}}
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="/static/theme.css">
  <script type="module" src="/static/engine.js"></script>
</head>
<body>
  <!-- Drop in the SaaS Dashboard -->
  <universal-saas-dashboard id="dashboard"></universal-saas-dashboard>

  <script>
    // Ingest data serialized directly from Go json.Marshal()
    document.getElementById('dashboard').state = {{ .DashboardJSON }};
  </script>
</body>
</html>
{{end}}
```

### ✨ Features:
- **Zero Dependencies:** Pure Vanilla JS (ES6+), Custom Elements v1, Shadow DOM.
- **WCAG 2.1 AA Compliant:** Keyboard navigation (Tab, Enter, Space) and full ARIA semantics built-in.
- **6 Built-in Themes:** Dark, Light, Corporate, Cyberpunk, Midnight, Emerald (stored in `localStorage`).
- **AI Gateway Ready:** Includes `<universal-ai-bridge>` for streaming Gemini structured outputs directly into your UI.

Check out the interactive workbench: [Portable UI Engine Live Workbench](https://ais-dev-pcysyufvntgq5ciwqii2cf-349849849289.europe-west2.run.app/sandbox.html)

---

## 3. r/rails – "Framework-agnostic Web Components for Hotwire & ERB templates"

**Title:** Native Web Component asset library for Rails (Hotwire/Turbo & ERB friendly, zero node bundlers)

Hey Rails devs,

Hotwire and Turbo have made Rails front-end development incredibly enjoyable again. However, when you need complex UI widgets like sortable data grids with multi-column filtering, metric card grids, or billing subscription cards, you often end up pulling heavy Stimulus controllers or React components into your asset pipeline.

I created **Portable UI Engine** (`@universal-ui/engine`) – a lightweight, framework-agnostic component library built on standard Web Components (Custom Elements v1 + Shadow DOM).

### 🚀 Integration with Rails ERB & Turbo:

```erb
<%# app/views/dashboard/index.html.erb %>
<div class="container">
  <universal-metric-grid payload='[
    {"title": "MRR Growth", "value": "$128,450.00", "change": "+24.5%", "trend": "upward", "context": "vs Q2 target"},
    {"title": "Active Subscriptions", "value": "4,120", "change": "+12.1%", "trend": "upward", "context": "vs last month"}
  ]'></universal-metric-grid>

  <universal-data-table style="margin-top: 24px;">
    <table>
      <thead>
        <tr><th>User</th><th>Email</th><th>Role</th><th>Status</th></tr>
      </thead>
      <tbody>
        <% @users.each do |user| %>
          <tr>
            <td><%= user.name %></td>
            <td><%= user.email %></td>
            <td><%= user.role %></td>
            <td><%= user.status %></td>
          </tr>
        <% end %>
      </tbody>
    </table>
  </universal-data-table>
</div>
```

Zero conflict with Turbo frame swaps, zero CSS leakage thanks to Shadow DOM isolation, and zero Node build step required.

- **Live Sandbox:** [sandbox.html](https://ais-dev-pcysyufvntgq5ciwqii2cf-349849849289.europe-west2.run.app/sandbox.html)
- **GitHub:** [dmuhoro/Portable-UI-Engine](https://github.com/dmuhoro/Portable-UI-Engine)

---

## 4. r/webdev – "Showcase: Portable UI Engine v2.0 – Zero-Dependency Web Component Library"

**Title:** Showwcase: Portable UI Engine – A framework-agnostic Web Component library with Shadow DOM & AI Gateway contracts

Hey r/webdev,

I wanted to share **Portable UI Engine v2.0**, an open-source library of highly portable, framework-agnostic Web Components designed to bridge the gap between heavy JS frameworks and non-JS backend stacks.

### 🛠️ What's in the Box?
- `<universal-app-shell>` – Responsive collateral layout shell with side drawer, topbar, and keyboard traps.
- `<universal-data-table>` – Reactive data grid supporting JSON props, search, sorting, and HTML table parsing.
- `<universal-form>` – Schema-driven form generator with client-side validation and sanitized custom events.
- `<universal-metric-grid>` – Analytics KPI card grid with trend badges and responsive flex layouts.
- `<universal-saas-dashboard>` – Complete administrative dashboard shell composed of metrics & table data.
- `<universal-billing-funnel>` – Tier comparison cards with modal checkout handlers.
- `<universal-ai-bridge>` – Real-time streaming gateway client for server-side LLM outputs (Gemini 2.5 Flash).

### 📐 Technical Architecture:
- **No Build Tools Required at Runtime:** Single CDN module import (`engine.js` / `engine.min.js`).
- **Encapsulated Styling:** Open Shadow DOM keeps styles completely isolated while allowing customization via CSS Custom Properties.
- **Accessibility:** Tested against WCAG 2.1 AA standards with full keyboard support and screen reader ARIA roles.
- **FOUC Prevention:** Includes `:not(:defined)` baseline skeleton animations for smooth low-latency hydration.

Check out the interactive live demo: [Portable UI Engine Showcase & Workbench](https://ais-dev-pcysyufvntgq5ciwqii2cf-349849849289.europe-west2.run.app)

Feedback and pull requests welcome on GitHub!
