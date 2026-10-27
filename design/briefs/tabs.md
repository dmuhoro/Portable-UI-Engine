# Component Design Brief: Tabs (`<ui-tabs>`)

An accessible, encapsulated tab navigation and panel-switching component inside Shadow DOM. Supports clean segmented controls, underline indicator styles, and responsive horizontal overflow scrolling.

---

## 1. Screenshot Description

- **Tab List Anatomy**: A horizontal row of single-line tab triggers (`role="tablist"`), separated by subtle spacing or housed inside a subtle segmented background track (`var(--color-surface-sunken)`).
- **Tab Trigger Variants**:
  - **Segmented / Inset**: Tabs sit inside a sunken container with 4px padding. The active tab has a solid raised surface (`var(--color-surface-base)`), 1px hairline border, and subtle shadow (`var(--elevation-sm)`).
  - **Underline / Editorial**: Transparent track with a 2px solid active bottom border indicator (`var(--color-brand-primary)` or `var(--color-text-primary)`), flush against a 1px subtle divider rule (`var(--color-border-subtle)`).
- **Tab Anatomy**: Optional leading icon, single-line text label (`whitespace: nowrap`), and optional count badge (e.g. `14`).
- **Tab Panels**: Content areas (`role="tabpanel"`) that render beneath the tab list, displaying the active pane while hiding inactive panels.
- **Horizontal Scrolling**: On narrow viewports ($<768\text{px}$), the tablist supports smooth touch scrolling with a subtle gradient mask at the edges to prevent clipped text.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-sunken)` | `#F3F1EC` | Segmented track background |
| **Color** | `var(--color-surface-base)` | `#FFFFFF` | Active tab pill background |
| **Color** | `var(--color-border-subtle)` | `#E7E5E4` | Baseline divider rule |
| **Color** | `var(--color-brand-primary)` | `#B45309` | Active underline indicator |
| **Color** | `var(--color-border-focus)` | `#B45309` | Focus indicator outline |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Active tab text color |
| **Color** | `var(--color-text-secondary)` | `#57534E` | Inactive tab text color |
| **Spacing** | `var(--spacing-3xs)`| `2px` | Segmented track internal padding |
| **Spacing** | `var(--spacing-xs)` | `8px` | Tab vertical padding |
| **Spacing** | `var(--spacing-md)` | `16px` | Tab horizontal padding |
| **Radius** | `var(--radius-sm)` | `4px` | Tab trigger & track corner radius |
| **Typography**| `var(--typography-scale-sm)` | `14px` | Tab label font size |
| **Typography**| `var(--typography-weight-medium)`| `500` | Tab label weight |
| **Motion** | `var(--motion-duration-fast)`| `120ms` | Active indicator transition |
| **Motion** | `var(--motion-easing-standard)`| `cubic-bezier(0.16, 1, 0.3, 1)` | State transition easing |

---

## 3. Behavior Notes & State Machine

1. **Active Tab Selection**:
   - Only one tab can be selected at a time (`aria-selected="true"`).
   - Inactive tabs have `aria-selected="false"` and `tabindex="-1"`.
   - The active tab has `tabindex="0"`.
2. **Hover State**:
   - Inactive tabs shift text color to `var(--color-text-primary)` with subtle background hover tint.
3. **Focus State (`:focus-visible`)**:
   - 2px outline in `var(--color-border-focus)` with a 2px offset.
4. **Keyboard Navigation Flow**:
   - Pressing `ArrowRight` or `ArrowDown` moves focus and selection to the next tab (wraps to first tab).
   - Pressing `ArrowLeft` or `ArrowUp` moves focus to the previous tab (wraps to last tab).
   - Pressing `Home` jumps to the first tab; `End` jumps to the last tab.
5. **Panel Association**:
   - Selecting a tab automatically un-hides the corresponding panel (`slot="panel"` matching `tab.id`) and hides all other panels.
6. **Custom Events Dispatched**:
   - Dispatches `ui-tab-change` (`bubbles: true`, `composed: true`, `detail: { activeIndex, tabId }`).

---

## 4. Acceptance Criteria

- [ ] **Single-Line Integrity**: Tab labels never wrap onto two lines. If text is long, it maintains single-line rendering and scrolls horizontally.
- [ ] **Touch Overflow**: On mobile viewports ($320\text{px}$), the tablist scrolls horizontally without showing jarring native browser scrollbars.
- [ ] **Dynamic Children Support**: Adding or removing `<ui-tab>` elements dynamically via JavaScript updates the keyboard index and ARIA properties automatically.
- [ ] **Responsive Breakpoints**:
  - `320px`: Touch targets expand to 40px height; track scrolls horizontally.
  - `768px`: Segmented tabs align left or span full container width.
  - `1280px`: Crisp alignment within header or workspace sub-navigation bars.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **WAI-ARIA Tabs Pattern**:
  - Container uses `role="tablist"`, `aria-label="Section navigation"`.
  - Individual tabs use `role="tab"`, `aria-selected="true|false"`, `aria-controls="panel-id"`, `id="tab-id"`.
  - Corresponding panels use `role="tabpanel"`, `aria-labelledby="tab-id"`, `tabindex="0"`.
- **Keyboard Traversal**:
  - roving tabindex pattern ensures only the active tab is in sequential tab flow.
  - Arrow keys navigate among tabs seamlessly.
- **Contrast**:
  - Active text achieves $\ge 7:1$ contrast; inactive text achieves $\ge 4.5:1$ contrast against track surface.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .active-indicator, .tab-trigger {
      transition: none !important;
      transform: none !important;
    }
  }
  ```
