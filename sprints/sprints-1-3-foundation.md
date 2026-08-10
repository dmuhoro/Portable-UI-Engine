# 🏗️ Sprints 1–3: Architectural Foundation & Core Primitives

This log documents the foundational phase of **Portable UI Engine**, establishing native Web Component architectures, design token inheritance, schema-driven form engines, and composite dashboard layouts.

---

## 📌 Sprint 1: Design Tokens & Layout Scaffolding

### 🎯 Objectives
* Establish a framework-agnostic CSS Design Token system (`theme.css`).
* Build `<universal-app-shell>` for top-level SaaS layout framing with responsive drawer controls.
* Build `<universal-data-table>` for searchable, paginated tabular data presentation.

### 📐 Technical Deliverables & Key Contracts

#### 1. CSS Custom Properties Design System (`theme.css`)
Centralized token registry defining neutral colors, primary accent scales, typographic sizes, border radii, shadows, and spacing scales.

```css
:root {
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-light: #eff6ff;
  --color-bg-app: #f8fafc;
  --color-bg-surface: #ffffff;
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-border: #e2e8f0;
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --radius-md: 6px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
```

#### 2. App Shell Primitive (`<universal-app-shell>`)
* **Shadow DOM**: Mode `open`.
* **Slots**:
  * `brand`: Top-left brand logo and title.
  * `header-actions`: Top-right user toolbar controls.
  * `drawer`: Left-hand navigation sidebar.
  * `default`: Main workspace content view.
* **Public Methods**: `toggleDrawer()`, `openDrawer()`, `closeDrawer()`.

#### 3. Data Table Primitive (`<universal-data-table>`)
* **Contract**:
  ```json
  {
    "headers": ["Name", "Email", "Role", "Status"],
    "rows": [
      ["Elena Rostova", "elena@corp.internal", "Principal Engineer", "Active"],
      ["Marcus Vance", "marcus@corp.internal", "Product Designer", "Pending"]
    ]
  }
  ```
* **Features**: Dynamic client-side search filtering, column sorting, pagination controls, and automated status badge styling (`Active` -> green, `Pending` -> amber, `Inactive` -> red).

---

## 📌 Sprint 2: Responsive Layout Shifts & Schema-Driven Forms

### 🎯 Objectives
* Build `<universal-form>` for dynamic HTML5 form rendering driven purely by JSON schema definitions.
* Enhance mobile responsiveness across Shadow DOM boundaries with CSS container queries and media query fallbacks.

### 📐 Technical Deliverables & Key Contracts

#### Schema-Driven Form Primitive (`<universal-form>`)
* **JSON Schema Signature**:
  ```json
  [
    {
      "name": "full_name",
      "type": "text",
      "label": "Full Name",
      "required": true,
      "placeholder": "e.g. Alex Morgan"
    },
    {
      "name": "role",
      "type": "select",
      "label": "User Role",
      "required": true,
      "options": ["Admin", "Engineer", "Designer"],
      "defaultValue": "Engineer"
    }
  ]
  ```
* **Supported Field Types**: `text`, `email`, `number`, `select`, `textarea`, `checkbox`.
* **Event Emission**: Dispatches `app-form-submit` containing sanitized `formData` map on valid submission.

---

## 📌 Sprint 3: SaaS Layout Templates & Composite State Architecture

### 🎯 Objectives
* Build `<universal-metric-grid>` for rendering KPI cards with trend indicators.
* Build `<universal-saas-dashboard>` as a master composite element orchestrating sub-primitives.
* Establish standard state propagation pipelines.

### 📐 Technical Deliverables & Key Contracts

#### 1. Metric Grid Primitive (`<universal-metric-grid>`)
* **JSON Payload Signature**:
  ```json
  [
    {
      "title": "Total Revenue",
      "value": "$52,840.00",
      "change": "+14.2%",
      "trend": "upward",
      "context": "vs last month"
    }
  ]
  ```
* **Visual Rendering**: Flex/Grid layout with color-coded trend pill badges (`upward` -> green arrow, `downward` -> red arrow, `neutral` -> gray dash).

#### 2. SaaS Dashboard Primitive (`<universal-saas-dashboard>`)
* **Master State Contract**:
  ```json
  {
    "metrics": [...],
    "tableHeaders": ["Member", "Role", "Status"],
    "tableRows": [...]
  }
  ```
* **Architecture**: Internal Shadow DOM contains nested instances of `<universal-metric-grid>` and `<universal-data-table>`. When state property is updated, state is safely propagated to children.
