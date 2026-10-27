# Component Design Brief: Menu / Dropdown Menu (`<ui-menu>`)

A floating contextual command menu and action dropdown encapsulated in Shadow DOM. Supports action items, keyboard shortcut badges, menu dividers, disabled items, submenus, and destructive options.

---

## 1. Screenshot Description

- **Visual Geometry**: A floating card with clean corner radius (`var(--radius-md, 6px)`), minimum width 180px, maximum width 280px.
- **Surface & Elevation**: Solid overlay surface `var(--color-surface-overlay, #FFFFFF)` in light mode (or `#1E293B` in dark mode), 1px solid hairline border `var(--color-border-subtle)`, and soft ambient elevation `var(--elevation-md)`.
- **Item Anatomy**: Each menu item is a horizontal row with 32px height (40px on mobile touch viewports), 8px vertical and 12px horizontal padding.
  - **Leading Icon Slot**: 16px icon slot with `var(--spacing-xs, 8px)` right gap.
  - **Label**: Single-line text in `var(--color-text-primary)` (`var(--typography-scale-sm, 14px)`).
  - **Trailing Shortcut / Affordance**: Monospaced shortcut hint (e.g. `⌘E`, `⇧⌘P`) in `var(--color-text-tertiary)` at 11px.
- **Dividers**: 1px horizontal rule `var(--color-border-subtle)` separating logical command groupings.
- **Destructive Items**: Red text `var(--color-feedback-danger)` with subtle danger hover tint.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-overlay)`| `#FFFFFF` | Menu popover background |
| **Color** | `var(--color-surface-sunken)` | `#F4F4F5` | Highlighted item row background |
| **Color** | `var(--color-border-subtle)` | `#E7E5E4` | Menu border & dividers |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Standard item text |
| **Color** | `var(--color-text-tertiary)` | `#78716C` | Keyboard shortcut text |
| **Color** | `var(--color-feedback-danger)` | `#B91C1C` | Destructive item text color |
| **Spacing** | `var(--spacing-2xs)` | `4px` | Menu internal vertical padding |
| **Spacing** | `var(--spacing-sm)` | `12px` | Item horizontal padding |
| **Spacing** | `var(--spacing-xs)` | `8px` | Icon-to-label gap |
| **Radius** | `var(--radius-md)` | `6px` | Menu outer corner radius |
| **Radius** | `var(--radius-xs)` | `2px` | Item hover highlight radius |
| **Elevation** | `var(--elevation-md)` | `0 4px 6px -1px rgba(...)` | Dropdown shadow |
| **Typography**| `var(--typography-scale-sm)` | `14px` | Item label font size |
| **Typography**| `var(--typography-family-mono)`| `JetBrains Mono` | Shortcut hint font family |
| **Motion** | `var(--motion-duration-fast)`| `100ms` | Menu entrance & highlight fade |

---

## 3. Behavior Notes & State Machine

1. **Closed State**:
   - `visibility: hidden; opacity: 0; pointer-events: none;`.
2. **Open Trigger**:
   - Click or `Enter`/`Space`/`ArrowDown` on the trigger element opens the menu directly aligned to the anchor edge.
   - Calculates collision with viewport edges to flip horizontally or vertically as needed.
3. **Item Navigation (Mouse & Keyboard)**:
   - Hovering mouse or using `ArrowDown`/`ArrowUp` moves active highlight immediately.
   - Highlight state applies `background: var(--color-surface-sunken)`.
   - Disabled items (`disabled="true"`) are skipped by arrow navigation and cannot be activated.
4. **Item Selection**:
   - Clicking an item or pressing `Enter` fires the item's action, closes the menu, and restores focus to the trigger.
5. **Dismissal**:
   - Pressing `Escape`, clicking outside the menu, or scrolling the page dismisses the menu and restores focus.
6. **Custom Events Dispatched**:
   - Dispatches `ui-menu-select` (`bubbles: true`, `composed: true`, `detail: { action, itemId }`).

---

## 4. Acceptance Criteria

- [ ] **Viewport Containment**: Menu popover never clips outside viewport edges or behind parent overflow containers.
- [ ] **Shortcut Alignment**: Keyboard shortcuts are right-aligned cleanly on a uniform column axis.
- [ ] **Responsive Breakpoints**:
  - `320px`: Menu displays as a bottom action sheet or expands item touch heights to 44px.
  - `768px`: Desktop dropdown aligned to trigger.
  - `1280px`: Full alignment across dense application toolbars.
- [ ] **Zero Dead Clicks**: Disabled items cannot be activated via mouse click or keyboard `Enter`.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **WAI-ARIA Menu Pattern**:
  - Trigger uses `aria-haspopup="menu"`, `aria-expanded="false|true"`.
  - Popover uses `role="menu"`, `aria-orientation="vertical"`.
  - Items use `role="menuitem"`, with optional `role="menuitemcheckbox"` or `role="menuitemradio"`.
  - Dividers use `role="separator"`.
- **Keyboard Navigation**:
  - `ArrowDown`: Moves focus to next non-disabled menu item (wraps to first).
  - `ArrowUp`: Moves focus to previous non-disabled menu item (wraps to last).
  - `Home` / `End`: Jumps to first / last item.
  - `Enter` / `Space`: Activates the currently highlighted item.
  - `Escape`: Closes menu immediately and returns focus to trigger button.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .menu-popover, .menu-item {
      transition: none !important;
      transform: none !important;
    }
  }
  ```
