# Component Design Brief: Toast / Notification (`<ui-toast>`)

A transient, non-modal status notification component encapsulated in Shadow DOM. Built for asynchronous operation updates, background job completions, and transient error notifications.

---

## 1. Screenshot Description

- **Visual Geometry**: Compact horizontal notification card measuring 360px max width (100% minus 32px on mobile viewports) with corner radius `var(--radius-md, 6px)`.
- **Placement**: Fixed floating container pinned to the bottom-right (desktop) or top-center (mobile), stacked vertically with an 8px gap.
- **Surface & Elevation**: Solid high-contrast surface `var(--color-surface-base, #FFFFFF)` with 1px solid hairline border `var(--color-border-subtle)` and elevation `var(--elevation-lg)`.
- **Anatomy**:
  - **Status Icon**: Left-aligned semantic glyph (e.g. check circle for success, warning triangle, or danger octagon).
  - **Message Content**: Single-line or two-line text block with bold title (`var(--typography-scale-sm, 14px)`) and secondary body copy (`var(--typography-scale-xs, 12px)`).
  - **Action Button Slot**: Optional quiet text button on the right (e.g. "Undo", "View Details").
  - **Close Button**: Compact `(x)` trigger for manual dismissal.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-base)` | `#FFFFFF` | Toast card background |
| **Color** | `var(--color-border-subtle)` | `#E7E5E4` | Toast outer border |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Toast title and copy |
| **Color** | `var(--color-text-secondary)` | `#57534E` | Secondary description text |
| **Color** | `var(--color-feedback-success)`| `#15803D` | Success status glyph color |
| **Color** | `var(--color-feedback-danger)` | `#B91C1C` | Error status glyph color |
| **Spacing** | `var(--spacing-sm)` | `12px` | Internal vertical padding |
| **Spacing** | `var(--spacing-md)` | `16px` | Internal horizontal padding |
| **Spacing** | `var(--spacing-xs)` | `8px` | Icon-to-text gap |
| **Radius** | `var(--radius-md)` | `6px` | Outer card corner radius |
| **Elevation** | `var(--elevation-lg)` | `0 10px 15px -3px rgba(...)` | Outer shadow |
| **Motion** | `var(--motion-duration-normal)`| `180ms` | Slide-in & slide-out transition |
| **Motion** | `var(--motion-easing-entrance)`| `cubic-bezier(0, 0, 0.2, 1)` | Slide entrance curve |

---

## 3. Behavior Notes & State Machine

1. **Entrance Transition**:
   - Slides up from bottom (or down from top) while fading in (`translateY(12px) -> 0`, `opacity: 0 -> 1`) in 180ms.
2. **Auto-Dismiss Timer**:
   - Automatically begins countdown (default 4000ms for info/success, 8000ms or persistent for errors).
   - Pauses countdown when the user hovers pointer over the toast or focuses any control inside the toast.
   - Resumes countdown when pointer leaves.
3. **Manual Dismissal**:
   - Clicking close button or pressing `Escape` triggers instant exit animation.
4. **Exit Transition**:
   - Fades out and translates slightly downward (`80ms`), after which the DOM node is cleanly removed.
5. **Stacking Behavior**:
   - Maximum 4 concurrent toasts visible. If a 5th arrives, the oldest is pushed out immediately.
6. **Custom Events Dispatched**:
   - Dispatches `ui-toast-show` and `ui-toast-dismiss` (`bubbles: true`, `composed: true`, `detail: { id, status }`).

---

## 4. Acceptance Criteria

- [ ] **Non-Blocking Interaction**: Toast container does not block clicks on elements situated outside its bounding box.
- [ ] **Stack Overflow Governance**: New toasts smoothly push existing toasts upward without clipping or jitter.
- [ ] **Responsive Breakpoints**:
  - `320px`: Width spans 100% of viewport minus 16px margins, docked at top of screen below topbar.
  - `768px`: Docked bottom-right with 360px width.
  - `1280px`: Docked bottom-right with 380px width, 24px viewport margin.
- [ ] **No Arrival Clutter**: Transient feedback only; never triggers automatically on initial page load.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **ARIA Semantics & Live Regions**:
  - Container uses `aria-live="polite"` for informational toasts.
  - Container uses `aria-live="assertive"` and `role="alert"` for critical errors.
  - All interactive action buttons inside the toast are keyboard focusable via `Tab`.
- **Keyboard Access**:
  - Global shortcut (e.g. `Ctrl+Alt+M`) or normal tab flow allows moving focus into the active toast stack.
  - `Escape` dismisses the currently focused toast.
- **Color Independence**:
  - Every status pairs a distinct icon and descriptive text label with the color token (never conveys state by color alone).
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .toast-item {
      transition: none !important;
      transform: none !important;
      animation: none !important;
    }
  }
  ```
