# Component Design Brief: Dialog / Modal (`<ui-dialog>`)

A focus-trapped, accessible modal overlay component encapsulated in Shadow DOM. Built for critical user confirmations, multi-step configuration wizards, and detail inspect views.

---

## 1. Screenshot Description

- **Backdrop Scrim**: A semi-transparent overlay covering 100% of the viewport (`background: rgba(28, 25, 23, 0.45)` in light mode, `rgba(0, 0, 0, 0.7)` in dark mode) with subtle background blur (`backdrop-filter: blur(4px)`).
- **Dialog Container**: Centered horizontally and vertically in the viewport. Max width defaults to 540px (or 720px for large mode, 100vw on mobile). Corner radius is `var(--radius-lg, 8px)`.
- **Surface & Elevation**: Solid surface `var(--color-surface-base, #FFFFFF)` with 1px solid hairline border `var(--color-border-subtle)` and high-depth shadow `var(--elevation-lg)`.
- **Anatomy**:
  - **Header Zone**: Title (`var(--typography-scale-lg, 18px)`, bold/semibold) on the left, optional quiet unboxed category kicker above it, and a close button `(x)` on the right.
  - **Divider**: Hairline rule `var(--color-border-subtle)`.
  - **Body Content Zone**: Scrollable area (`overflow-y: auto`, max-height: `calc(100vh - 160px)`), padded with `var(--spacing-lg, 24px)`.
  - **Footer Action Zone**: Padded action row aligned right with a secondary "Cancel" button and primary action button (e.g. "Confirm Changes").

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-base)` | `#FFFFFF` | Dialog container background |
| **Color** | `var(--color-border-subtle)` | `#E7E5E4` | Modal border and dividers |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Dialog heading and primary copy |
| **Color** | `var(--color-text-secondary)` | `#57534E` | Body prose and description |
| **Spacing** | `var(--spacing-md)` | `16px` | Header and footer vertical padding |
| **Spacing** | `var(--spacing-lg)` | `24px` | Content body padding |
| **Spacing** | `var(--spacing-xs)` | `8px` | Footer action button gap |
| **Radius** | `var(--radius-lg)` | `8px` | Dialog card corner radius |
| **Elevation** | `var(--elevation-lg)` | `0 10px 15px -3px rgba(...)` | Outer modal drop shadow |
| **Motion** | `var(--motion-duration-normal)`| `180ms` | Modal entrance/exit animation |
| **Motion** | `var(--motion-easing-entrance)`| `cubic-bezier(0, 0, 0.2, 1)` | Slide/fade entrance curve |

---

## 3. Behavior Notes & State Machine

1. **Closed State**:
   - `display: none` or native `<dialog>` closed. Removed from accessibility tree.
2. **Opening Transition**:
   - Triggered via `.showModal()` or `open` attribute.
   - Backdrop fades in (`opacity: 0 -> 1`).
   - Dialog card scales gently from `0.96` to `1.0` and translates from `translateY(8px)` to `0`. Duration: 180ms.
3. **Focus Trap**:
   - Automatically moves initial focus to the first interactive element inside the dialog (or the close button).
   - Pressing `Tab` cycles strictly through focusable elements inside the modal; focus cannot escape to underlying background document elements.
4. **Body Scroll Lock**:
   - Document `body` style gets `overflow: hidden` while modal is open to prevent background scrolling.
5. **Dismissal Pathways**:
   - Clicking backdrop scrim (if `backdrop-dismiss="true"`).
   - Pressing `Escape` key.
   - Clicking close `(x)` button or cancel button.
6. **Closing Transition**:
   - Modal fades and translates down (`80ms`), after which backdrop closes and focus is restored to the origin element that triggered the dialog.
7. **Custom Events Dispatched**:
   - Dispatches `ui-dialog-open` and `ui-dialog-close` (`bubbles: true`, `composed: true`, `detail: { reason }`).

---

## 4. Acceptance Criteria

- [ ] **Native `<dialog>` Architecture**: Implemented using HTML5 `<dialog>` element inside Shadow DOM with standard `.showModal()` API for browser-native top-layer rendering.
- [ ] **Responsive Breakpoints**:
  - `320px`: Dialog transforms into a full-width bottom sheet or full-screen overlay with zero horizontal margin, height 100vh or max 90vh with sticky action footer.
  - `768px`: Centered modal with 480px width.
  - `1280px`: Centered modal with up to 580px width, padding 24px.
- [ ] **Scroll Containment**: Very long dialog content scrolls smoothly without scrolling background document.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **ARIA Semantics**:
  - `role="dialog"` or `role="alertdialog"` (for destructive actions).
  - `aria-modal="true"`.
  - `aria-labelledby="dialog-title-id"`.
  - `aria-describedby="dialog-desc-id"`.
- **Keyboard Navigation**:
  - `Escape` key immediately closes the dialog.
  - Strict circular `Tab` order: Tab on last element wraps to first; Shift+Tab on first element wraps to last.
  - Restores focus to the triggering element upon exit.
- **Screen Reader Announcements**:
  - Dialog title is read aloud immediately upon focus transition.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    dialog, .backdrop {
      animation: none !important;
      transition: none !important;
      transform: none !important;
    }
  }
  ```
