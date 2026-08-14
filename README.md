# 🚀 Portable UI Engine (`@universal-ui/engine`)

> **Framework-Agnostic, Zero-Dependency Native Web Component & Design System Asset Library**
> *Ship high-performance, style-isolated UI components directly to the browser with zero build steps, zero node_modules bloat, and 100% Shadow DOM encapsulation.*

---

## ⚡ The 10-Second Quick Start

Simply drop our unified engine script and CSS design tokens into any HTML file or server-rendered template (Express, Django, Rails, Laravel, Go, Rust):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <!-- 1. Load Global CSS Design Tokens -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@universal-ui/engine/theme.css" />
  <!-- 2. Single-Line Engine Script Import -->
  <script type="module" src="https://cdn.jsdelivr.net/npm/@universal-ui/engine/engine.js"></script>
</head>
<body>

  <!-- 3. Use Native Custom Elements Anywhere -->
  <universal-app-shell drawer-open>
    <a href="#" slot="brand"><strong>SaaS Control Center</strong></a>
    
    <universal-metric-grid id="metrics"></universal-metric-grid>
  </universal-app-shell>

  <script>
    document.getElementById('metrics').payload = [
      { "title": "Total Revenue", "value": "$52,840.00", "change": "+14.2%", "trend": "upward", "context": "vs last month" },
      { "title": "Active Subscriptions", "value": "1,420", "change": "-2.1%", "trend": "downward", "context": "vs last week" }
    ];
  </script>
</body>
</html>
```

---

## 🏆 Why Portable UI Engine? (The Competitive Edge)

| Feature | React / Shadcn UI | Material UI / Ant Design | **@universal-ui/engine** |
| :--- | :---: | :---: | :---: |
| **Framework Agnostic** | ❌ React Only | ❌ Framework Locked | **✅ Vanilla JS, Any Backend or JS Frame** |
| **Bundle Footprint** | ⚠️ Heavy (React + DOM + Deps) | ❌ 100KB+ CSS/JS | **⚡ < 15KB Minified & Gzipped** |
| **Style Isolation** | ⚠️ CSS-in-JS / Global Pollution | ❌ Global Style Clashes | **✅ 100% Shadow DOM Encapsulation** |
| **Build Dependency** | ❌ Complex Transpilation Needed | ❌ Webpack / Vite Required | **✅ Native ESM Execution (No Build)** |
| **Data-Driven Props** | ⚠️ Manual Prop Drilling | ⚠️ Complex State Hookups | **✅ Standard JSON Payloads & Setters** |

---

## 🧩 Component Contracts Matrix

### 1. `<universal-app-shell>`
Responsive SaaS grid layout featuring sticky header, auto-collapsing navigation drawer, slot projection, and backdrop support.

* **Observed Attributes**: `drawer-open` (boolean attribute)
* **Slots**:
  * `brand`: Top-left branding area
  * `header-actions`: Top-right toolbar buttons / theme selectors
  * `drawer`: Navigation menu links
  * `default`: Main workspace content view
* **Custom Events**:
  * `drawer-toggle`: Emitted when drawer toggles open/closed. `e.detail = { open: boolean, isMobile: boolean }`

---

### 2. `<universal-form>`
Dynamic schema-driven form element with HTML5 client validation and real-time input error display.

* **Properties / Attributes**:
  * `schema` (Array | JSON String): Array of field objects defining name, type (`text` | `email` | `number` | `select` | `textarea` | `checkbox`), label, required, placeholder, options.
  * `title` (String): Header title text.
  * `submit-label` (String): Submit button text label.
* **Custom Events**:
  * `app-form-submit`: Emitted on valid submit. `e.detail = { formData: { key: value } }`
* **Public Methods**:
  * `getFormData()`: Returns raw key-value form object.
  * `validate()`: Runs form validation and returns `boolean`.
  * `reset()`: Resets all input fields and clears error state.

---

### 3. `<universal-data-table>`
Data grid with multi-column sorting, search filtering, paginated controls, CSV export, and selectable rows.

* **Properties / Attributes**:
  * `payload` (Object | JSON String): `{ headers: Array<String>, rows: Array<Array<String|Number>> }`
* **Custom Events**:
  * `row-select`: Emitted when row checkbox is toggled. `e.detail = { selectedRows: Array }`
  * `table-search`: Emitted on search query change. `e.detail = { query: String }`

---

### 4. `<universal-metric-grid>`
Analytics card grid displaying metric values, contextual captions, and automatic trend color badges (`--color-success`, `--color-danger`).

* **Properties / Attributes**:
  * `payload` (Array | JSON String): `[{ title, value, change, trend: "upward"|"downward", context }]`

---

### 5. `<universal-saas-dashboard>`
Composite dashboard orchestrator that syncs `<universal-metric-grid>` and `<universal-data-table>`.

* **Properties / Attributes**:
  * `state` (Object | JSON String): `{ metrics: [...], tableHeaders: [...], tableRows: [...] }`
* **Deep Setter**: Setting `dashboard.state = newMasterData` automatically forwards state updates to child elements synchronously.

---

### 6. `<universal-billing-funnel>`
Commercial multi-step subscription wizard (Plan Selection -> Billing Details -> Confirmation).

* **Properties / Attributes**:
  * `plans` (Array | JSON String): `[{ id, name, price, features: [], popular: boolean }]`
* **Custom Events**:
  * `app-checkout-complete`: Emitted on successful purchase. `e.detail = { transactionId, timestamp, plan, payment }`

---

### 7. `<universal-toast>`
Fixed viewport notification manager that renders auto-dismissing toast popups.

* **Observed Attributes**: `position` (`top-right` | `top-left` | `bottom-right` | `bottom-left`), `duration` (number in ms, default `4000`)
* **Properties**:
  * `toasts` (Array): Array of `{ id, type: 'success'|'danger'|'warning'|'info', title, message, duration }`
* **Public Methods**:
  * `showToast({ type, title, message, duration })`: Appends a toast to the active list.
  * `clearAll()`: Removes all active toast popups immediately.
* **Custom Events**:
  * `toast-dismiss`: Emitted when a toast is closed manually or via timer expiry. `e.detail = { toastId, type }`

---

### 8. `<universal-modal-dialog>`
Accessible modal overlay with body scroll lock, keyboard focus trapping, Escape dismissal, and header/body/footer slots.

* **Observed Attributes**: `open` (boolean attribute), `title` (string header), `size` (`sm` | `md` | `lg`)
* **Slots**:
  * `header`: Custom title header replace slot
  * `default`: Main modal body content
  * `footer`: Action buttons slot (e.g. Confirm, Cancel)
* **Public Methods**:
  * `open()`: Displays the modal and traps keyboard focus.
  * `close()`: Closes the modal and restores document scroll/focus.
* **Custom Events**:
  * `modal-open`: Emitted when the modal opens. `e.detail = { timestamp }`
  * `modal-close`: Emitted when the modal closes via backdrop click, Escape, or close button. `e.detail = { reason: 'backdrop'|'escape'|'button' }`

---

### 9. `<universal-badge-cloud>`
Responsive badge/chip grouping component with removable tags and click events.

* **Observed Attributes**: `removable` (boolean attribute), `variant` (`default` | `primary` | `outline`)
* **Properties**:
  * `tags` (Array | JSON String): `["JavaScript", "Web Components"]` or `[{ id, label, color }]`
* **Custom Events**:
  * `tag-remove`: Emitted when the close (`×`) icon on a tag is clicked. `e.detail = { removedTag, remainingTags: Array }`
  * `tag-click`: Emitted when a tag item is clicked. `e.detail = { tag }`

---

## 🎨 Theming & Design System Overrides

Customize visual tokens globally by overriding CSS variables on `:root` or via the `UniversalUI` JavaScript manager:

```javascript
import { UniversalUI } from './engine.js';

// Switch to a built-in theme preset:
// 'light' | 'dark' | 'corporate' | 'cyberpunk' | 'midnight' | 'emerald'
UniversalUI.setTheme('cyberpunk');

// Or override specific tokens on the fly:
UniversalUI.setTheme('dark', {
  '--color-primary': '#ff0055',
  '--color-primary-hover': '#e6004c',
  '--radius-md': '12px'
});
```

---

## 🛠️ Build & Development Commands

```bash
# Install local dev dependencies
npm install

# Start local preview server on port 3000
npm run dev

# Run esbuild production bundle (dist/engine.min.js)
npm run build:engine

# Lint TypeScript declarations
npm run lint
```

---

## 📄 License

MIT © Portable UI Engine Team. Open-source software.
