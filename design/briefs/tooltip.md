# Component Design Brief: Tooltip (`<ui-tooltip>`)

A non-interactive, lightweight contextual hint popover encapsulated in Shadow DOM. Designed to provide brief descriptions for icons, truncated labels, and keyboard shortcuts without obstructing user flow.

---

## 1. Screenshot Description

- **Visual Geometry**: Compact pill/box with small corner radius (`var(--radius-xs, 2px)` to `var(--radius-sm, 4px)`), max width 260px.
- **Surface & Text**: High-contrast inverted surface (`var(--color-surface-inverse, #1C1917)` in light mode, `#F1F5F9` in dark mode) with crisp inverse text (`var(--color-text-inverse)`), micro-typography at 12px (`var(--typography-scale-xs)`).
- **Pointer Arrow**: Optional 4px equilateral triangle arrow pointing toward the triggering anchor target.
- **Elevation**: Subtle soft shadow (`var(--elevation-sm)`), 1px subtle boundary border to maintain separation across complex backgrounds.
- **Keyboard Shortcut Display**: Supports an optional right-aligned monospaced shortcut indicator (e.g. `⌘K`, `Esc`).

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-inverse)` | `#1C1917` | Tooltip bubble background |
| **Color** | `var(--color-text-inverse)` | `#FAF8F5` | Tooltip text color |
| **Color** | `var(--color-border-subtle)` | `#292524` | Tooltip outline border |
| **Spacing** | `var(--spacing-2xs)` | `4px` | Vertical padding |
| **Spacing** | `var(--spacing-xs)` | `8px` | Horizontal padding |
| **Radius** | `var(--radius-xs)` | `2px` | Bubble corner radius |
| **Elevation** | `var(--elevation-sm)` | `0 1px 2px 0 rgba(...)` | Outer shadow |
| **Typography**| `var(--typography-scale-xs)` | `12px` | Label font size |
| **Typography**| `var(--typography-family-mono)`| `JetBrains Mono` | Keyboard shortcut token font |
| **Motion** | `var(--motion-duration-fast)`| `100ms` | Fade-in / fade-out duration |

---

## 3. Behavior Notes & State Machine

1. **Resting State**:
   - Hidden from view (`visibility: hidden; opacity: 0; pointer-events: none;`).
2. **Hover Intent (Mouse)**:
   - Activates after a deliberate hover delay of 300ms (`delay-show`) to prevent visual jitter when sweeping the cursor across dense icon toolbars.
   - Once open, hovering adjacent tooltip triggers shows them instantly (0ms delay) within a 500ms grace window.
3. **Keyboard Focus (`focusin`)**:
   - Displays immediately (0ms delay) when the parent trigger receives keyboard focus.
4. **Dismissal**:
   - Closes immediately on `focusout`, mouse leave, scroll event, or when the user presses `Escape`.
5. **Positioning Engine**:
   - Positions relative to trigger (`top`, `bottom`, `left`, `right`). Automatically flips to opposite side if encroaching on viewport boundaries.

---

## 4. Acceptance Criteria

- [ ] **No Pointer Interference**: Tooltip bubble has `pointer-events: none` and does not block cursor interactions with underlying elements.
- [ ] **Hover Delay Buffer**: Moving cursor rapidly across multiple toolbar items does not cause flickering flashcards.
- [ ] **Viewport Boundary Clamping**: Tooltip remains fully visible within screen margins, clamping horizontally at 320px, 768px, and 1280px viewports.
- [ ] **Touch Device Grace**: On touch devices (screens lacking hover capability: `@media (hover: none)`), tooltips are suppressed or activated strictly via explicit long-press or tap to prevent sticky trapped popups.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **ARIA Semantics**:
  - Tooltip container uses `role="tooltip"`.
  - Trigger element contains `aria-describedby="tooltip-id"`.
- **Keyboard Dismissal**:
  - Pressing `Escape` while tooltip is visible dismisses the tooltip without moving focus or closing parent dialogs (WCAG 1.4.13 Content on Hover or Focus).
- **Persistent on Hover**:
  - If the user moves the pointer over the tooltip itself, it remains visible until the pointer moves away.
- **Contrast**:
  - Inverted text on dark surface delivers $>11:1$ contrast ratio.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .tooltip-bubble {
      transition: none !important;
      transform: none !important;
    }
  }
  ```
