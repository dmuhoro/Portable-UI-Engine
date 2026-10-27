# Component Design Brief: Checkbox (`<ui-checkbox>`)

A high-precision binary and indeterminate selection control encapsulated in Shadow DOM. Built for multi-row data table selection, settings lists, and agreement flows.

---

## 1. Screenshot Description

- **Visual Geometry**: A compact square box measuring 18px $\times$ 18px (22px on touch viewports) with a micro-radius (`var(--radius-xs, 2px)`).
- **Label Alignment**: Label text sits horizontally adjacent to the checkbox, separated by an 8px gap (`var(--spacing-xs)`), vertically aligned to the top cap-height of the checkbox frame.
- **States & Visual Markings**:
  - **Unchecked**: Crisp 1px solid hairline border (`var(--color-border-default)`), hollow background (`var(--color-surface-base)`).
  - **Checked**: Filled with solid brand accent (`var(--color-brand-primary)`), displaying a white crisp checkmark SVG glyph (`stroke-width: 2.5`).
  - **Indeterminate**: Filled with brand accent, displaying a horizontal minus line (`stroke-width: 2.5`) to signal mixed descendant states.
  - **Description Subtext**: Optional secondary text below the primary label rendered in `var(--color-text-secondary)` at 12px.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-base)` | `#FFFFFF` | Unchecked box background |
| **Color** | `var(--color-brand-primary)` | `#1C1917` | Checked/indeterminate background |
| **Color** | `var(--color-text-inverse)` | `#FFFFFF` | Checkmark glyph stroke color |
| **Color** | `var(--color-border-default)` | `#D6D3D1` | Unchecked box border |
| **Color** | `var(--color-border-focus)` | `#B45309` | High-visibility focus ring |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Label text color |
| **Color** | `var(--color-text-secondary)` | `#57534E` | Description subtext color |
| **Spacing** | `var(--spacing-xs)` | `8px` | Gap between box and label |
| **Spacing** | `var(--spacing-3xs)`| `2px` | Subtext vertical margin |
| **Radius** | `var(--radius-xs)` | `2px` | Box corner radius |
| **Typography**| `var(--typography-scale-sm)` | `14px` | Label font size |
| **Typography**| `var(--typography-scale-xs)` | `12px` | Subtext font size |
| **Motion** | `var(--motion-duration-fast)`| `100ms` | Checkmark stroke draw transition |

---

## 3. Behavior Notes & State Machine

1. **Unchecked State**:
   - Resting hollow border. Checkmark glyph opacity: 0.
2. **Hover State**:
   - Box border shifts to `var(--color-border-strong)`. Background gets subtle tint.
3. **Checked State**:
   - Box fills with `var(--color-brand-primary)`. Checkmark icon fades and scales in (`scale(1)`, `opacity: 1`).
4. **Indeterminate State**:
   - Set programmatically via property `indeterminate = true`. Renders horizontal dash icon. Toggling transitions directly to checked or unchecked.
5. **Focus State (`:focus-visible`)**:
   - Outer 2px solid ring (`var(--color-border-focus)`) with a 2px offset surrounds the 18px checkbox box.
6. **Disabled State (`disabled`)**:
   - Reduced opacity (0.45). Cursor is `not-allowed`. Clicks are ignored.
7. **Custom Events Dispatched**:
   - Dispatches `ui-checkbox-change` (`bubbles: true`, `composed: true`, `detail: { checked, indeterminate, value }`).

---

## 4. Acceptance Criteria

- [ ] **Click Target Expansion**: Clicking anywhere on the associated label text toggles the checkbox state.
- [ ] **Indeterminate Property Binding**: Setting `checkbox.indeterminate = true` visually updates the icon without changing the underlying `checked` boolean until clicked.
- [ ] **Touch Target Ergonomics**:
  - At `320px`, the invisible tap target area expands to at least 44px $\times$ 44px via `::before` pseudo-element.
- [ ] **Data Table Batch Selection**: Works seamlessly inside table header cells for "Select All" actions.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **Keyboard Operation**:
  - Focusable via `Tab`.
  - Toggled via `Space` key.
- **ARIA Semantics**:
  - Uses native `<input type="checkbox">` hidden inside shadow root or `role="checkbox"`.
  - `aria-checked="true|false|mixed"` (where `"mixed"` maps to indeterminate state).
  - Linked to label via `aria-labelledby` or `<label>` encapsulation.
- **Color Independence**: The checkmark glyph and solid fill provide visual indication beyond color alone (passes WCAG 1.4.1 Use of Color).
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .checkmark, .box {
      transition: none !important;
      transform: none !important;
    }
  }
  ```
