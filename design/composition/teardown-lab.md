# Showcase App Composition: Rubric UI Teardown Lab (`apps/teardown-lab`)

An analytical benchmarking and component evaluation laboratory. Designed for engineering leads and design system maintainers to conduct systematic rubrics, measure compliance against accessibility criteria, and execute side-by-side component comparisons.

---

## 1. Visual Look & Feel and Layout Architecture

The Teardown Lab aesthetic balances scientific laboratory rigor with high-contrast editorial clarity. It features an asymmetric split layout: a sticky evaluation benchmark scorecard on the left, a multi-criteria rubric evaluation matrix in the center, and a live side-by-side comparison bench on the right.

```
+--------------------------------------------------------------------------------------------------------+
| [Teardown Lab]                  Rubrics   Evaluations   Comparisons   Export             [New Audit]   |  <-- Top Bar
+--------------------------------------------------------------------------------------------------------+
|                                                                                                        |
|  AUDIT: PORTABLE-UI-ENGINE CORE v2.0                                                                   |
|  Target Component: <ui-button> · Benchmark Standard: WCAG 2.1 AA + Shadow DOM Isolation               |
|                                                                                                        |
|  +---------------------------+  +-------------------------------------------------------------------+  |
|  | OVERALL COMPLIANCE SCORE  |  | RUBRIC EVALUATION CRITERIA                                        |  |
|  |                           |  |-------------------------------------------------------------------|  |
|  |   98.4%                   |  | [x] 1. Keyboard Operability (Enter + Space triggers)       Passed |  |
|  |   GRADE: AAA EXCELLENCE   |  |     Focus ring visible, no tab traps, roving tabindex             |  |
|  |                           |  |                                                                   |  |
|  | Contrast Ratio:  11.4:1   |  | [x] 2. Shadow DOM Style Isolation                         Passed |  |
|  | Touch Target:    44x44px  |  |     Zero leakage from outer Tailwind / Bootstrap rules            |  |
|  | Motion Budget:   120ms    |  |                                                                   |  |
|  | FOUC Latency:    0ms      |  | [x] 3. Color Contrast Discipline                          Passed |  |
|  |                           |  |     Text primary 11.4:1, Secondary 5.8:1, Focus ring 4.5:1        |  |
|  | [ Generate Audit PDF ]    |  |                                                                   |  |
|  +---------------------------+  | [x] 4. Reduced-Motion Grace                               Passed |  |
|                                 |     @media (prefers-reduced-motion) disables animations           |  |
|                                 +-------------------------------------------------------------------+  |
|                                                                                                        |
|  +--------------------------------------------------------------------------------------------------+  |
|  | SIDE-BY-SIDE BENCHMARK COMPARISON                                                                |  |
|  |--------------------------------------------------------------------------------------------------|  |
|  |  Engine Candidate (<ui-button>)              |  Legacy Baseline (<button class="btn">)          |  |
|  |  -------------------------------------------  |  -----------------------------------------------  |  |
|  |  [ Primary Action ] (18KB zero-dep)           |  [ Primary Action ] (142KB React bundle)          |  |
|  |  Render Latency: 0.8ms                        |  Render Latency: 12.4ms (Hydration cost)          |  |
|  |  CSS Leak Resistance: 100% (Shadow DOM)       |  CSS Leak Resistance: 0% (Global scope collision) |  |
|  +--------------------------------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Token Mappings

| Component Region | Token CSS Custom Property | Token Fallback Value | Purpose in Rubric UI |
| :--- | :--- | :--- | :--- |
| **Canvas** | `var(--color-canvas-default)` | `#F9F8F6` | Primary reading background |
| **Scorecard Card** | `var(--color-surface-base)` | `#FFFFFF` | Isolated benchmark score container |
| **Score Number** | `var(--typography-family-mono)` | `'JetBrains Mono', monospace` | Tabular numeric telemetry value |
| **Pass Status Marker**| `var(--color-feedback-success)` | `#15803D` | Clear semantic pass indicator |
| **Fail Status Marker**| `var(--color-feedback-danger)` | `#B91C1C` | Critical defect indicator |
| **Criteria Border** | `var(--color-border-subtle)` | `#E7E5E4` | Hairline list dividers |
| **Comparison Surface**| `var(--color-surface-sunken)` | `#F3F1EC` | Contrast backdrop for comparison bench |
| **Interactive Check** | `var(--color-brand-primary)` | `#B45309` | Active rubric checklist toggle |

---

## 3. Responsive Breakpoint Layouts

### 1280px (Desktop Wide)
- **Top Row**: 320px sticky scorecard on left; remaining space dedicated to the dynamic rubric criteria table.
- **Bottom Row**: Full-width split comparison bench (50% candidate component, 50% baseline comparison) with synchronized interaction mirrors.
- **Typography**: 36px tabular score numerals (`tabular-nums font-mono`).

### 768px (Tablet)
- **Top Row**: Scorecard and rubric criteria stack vertically. Scorecard displays as a horizontal 4-column metric strip across the top.
- **Criteria List**: 16px row padding with touch-friendly check toggles.
- **Comparison Bench**: Stacked 2-card layout with tab toggle (`Candidate` vs `Baseline`).

### 320px (Mobile)
- **Scorecard**: Compact 2x2 metric grid with 24px score numerals.
- **Criteria Rows**: Expand to 44px tap targets. Secondary descriptions collapse into expandable accordion rows.
- **Comparison Bench**: Displays single selected component with a quick toggle button to switch between Candidate and Baseline.

---

## 4. Shadow DOM Architecture & Implementation Notes

- **Encapsulated Verification**: The candidate component under test runs in an isolated Shadow DOM container with deliberate style pollution injected into the light DOM document (e.g. global `button { background: red !important; }`) to actively verify that shadow styles resist global bleed.
- **Automated Score Computation**: Checkbox toggles dispatch custom events (`ui-rubric-toggle`) that dynamically recalculate the overall compliance score in real time.

---

## 5. Token Configuration JSON

```json
{
  "rubricLayout": {
    "scorecard": {
      "surface": "var(--color-surface-base)",
      "border": "1px solid var(--color-border-subtle)",
      "radius": "var(--radius-md)",
      "metricFont": "var(--typography-family-mono)"
    },
    "criteria": {
      "itemHeight": "48px",
      "divider": "1px solid var(--color-border-subtle)",
      "successColor": "var(--color-feedback-success)",
      "dangerColor": "var(--color-feedback-danger)"
    }
  }
}
```
