# Component Design Brief: Select (`<ui-select>`)

A custom dropdown select component encapsulated in Shadow DOM. Supports single selection, searchable filtering, multi-select tag ingestion, custom option rendering, and keyboard combobox navigation.

---

## 1. Screenshot Description

- **Trigger Surface**: A rectangular trigger container styled identically to `<ui-input>`, featuring 38px height (44px on mobile), 12px inset padding, and corner radius `var(--radius-sm, 4px)`.
- **Trigger Anatomy**: Selected value label (or placeholder if empty) on the left; trailing chevron indicator on the right that rotates 180 degrees smoothly when the popover opens.
- **Dropdown Menu Popover**: Floats directly beneath (or above if near viewport bottom) the trigger. Surface uses `var(--color-surface-overlay, #FFFFFF)` with hairline border `var(--color-border-subtle)` and elevation `var(--elevation-md)`.
- **Options List**: Max height capped at 240px with a subtle custom scrollbar. Each option row has 32px height, 10px horizontal padding, and displays a checkmark indicator for the currently selected item.
- **Empty / Search State**: Optional top search input for filtering $>8$ options, with quiet unboxed "No matching options found" state when empty.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-base)` | `#FFFFFF` | Trigger resting background |
| **Color** | `var(--color-surface-overlay)`| `#FFFFFF` | Options popover background |
| **Color** | `var(--color-surface-sunken)` | `#F4F4F5` | Hovered option row background |
| **Color** | `var(--color-border-subtle)` | `#E7E5E4` | Trigger and popover borders |
| **Color** | `var(--color-border-focus)` | `#B45309` | Active focus indicator border |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Selected value and option labels |
| **Color** | `var(--color-text-tertiary)` | `#78716C` | Placeholder text |
| **Color** | `var(--color-brand-primary)` | `#B45309` | Selected option checkmark & highlight |
| **Spacing** | `var(--spacing-xs)` | `8px` | Popover internal vertical padding |
| **Spacing** | `var(--spacing-sm)` | `12px` | Trigger horizontal padding |
| **Radius** | `var(--radius-sm)` | `4px` | Trigger and popover corner radius |
| **Elevation** | `var(--elevation-md)` | `0 4px 6px -1px rgba(...)` | Popover drop shadow |
| **Typography**| `var(--typography-scale-sm)` | `14px` | Value and option font size |
| **Motion** | `var(--motion-duration-fast)`| `120ms` | Chevron rotation & menu fade duration |
| **Motion** | `var(--motion-easing-standard)`| `cubic-bezier(0.16, 1, 0.3, 1)` | Menu open/close easing |

---

## 3. Behavior Notes & State Machine

1. **Resting State**:
   - Closed dropdown. Chevron points downwards (`transform: rotate(0deg)`).
2. **Open / Expanded State**:
   - Click or `Space`/`Enter`/`ArrowDown` toggles open state.
   - Popover calculates viewport collisions (`position: absolute` or modern CSS anchor positioning) and opens downwards or flips upwards.
   - Chevron rotates 180 degrees (`transform: rotate(180deg)`).
3. **Option Hover / Active Focus**:
   - Navigating via mouse or arrow keys updates the active item visually via `var(--color-surface-sunken)`.
   - Selected option maintains a bold indicator or checkmark glyph.
4. **Click Outside**:
   - Native document listener closes the popover immediately and returns focus to trigger if clicked outside.
5. **Disabled State**:
   - `disabled="true"` locks trigger, reduces opacity to 0.5, and prevents popover expansion.
6. **Custom Events Dispatched**:
   - Dispatches `ui-select-change` (`bubbles: true`, `composed: true`, `detail: { value, label, index }`).

---

## 4. Acceptance Criteria

- [ ] **Viewport Clipping Prevention**: Popover never renders off-screen or gets clipped by parent `overflow: hidden` containers (uses top-level popover API or smart collision flipping).
- [ ] **Responsive Breakpoints**:
  - `320px`: Trigger height 44px; popover options expand to 40px touch targets.
  - `768px`: Desktop 38px trigger height.
  - `1280px`: Full alignment inside form matrices.
- [ ] **Typeahead Filtering**: Typing letters while focused immediately highlights matching options.
- [ ] **Zero Layout Shift**: Opening the dropdown does not alter sibling layout geometry in document flow.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **Combobox Pattern**:
  - Trigger uses `role="combobox"`, `aria-haspopup="listbox"`, `aria-expanded="false|true"`.
  - Dropdown options container uses `role="listbox"`.
  - Individual options use `role="option"`, `aria-selected="true|false"`.
  - Trigger maintains `aria-activedescendant="option-id"` pointing to currently focused option.
- **Keyboard Navigation**:
  - `Enter` / `Space` / `ArrowDown`: Opens menu if closed; selects highlighted option if open.
  - `ArrowUp` / `ArrowDown`: Moves active descendant through visible options.
  - `Escape`: Closes popover and returns focus to trigger without altering selection.
  - `Home` / `End`: Jumps to first / last option.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .chevron, .popover {
      transition: none !important;
      transform: none !important;
    }
  }
  ```
