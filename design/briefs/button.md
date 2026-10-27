# Component Design Brief: Button (`<ui-button>`)

A framework-agnostic interactive trigger component encapsulated inside Shadow DOM. Supports primary, secondary, outline, ghost, and danger variants across compact, standard, and large sizes.

---

## 1. Screenshot Description

- **Visual Geometry**: A compact rectilinear container with controlled border-radius (`var(--radius-sm, 4px)`), featuring precise horizontal and vertical padding ($2:1$ ratio). Height defaults to 36px in standard mode, 30px in compact mode, and 44px in large/mobile-touch mode.
- **Visual Variants**:
  - **Primary**: Solid high-contrast background (`var(--color-brand-primary)` or `var(--color-text-primary)`), crisp contrast text (`var(--color-surface-base)` or `var(--color-text-inverse)`), no external border.
  - **Secondary / Subtle**: Low-contrast neutral fill (`var(--color-surface-sunken)`), text in `var(--color-text-primary)`, hairline border in `var(--color-border-subtle)`.
  - **Outline**: Transparent background, 1px solid structural border (`var(--color-border-default)`), text in `var(--color-text-primary)`.
  - **Ghost**: Zero background and zero border in resting state, activates subtle background tint on hover.
  - **Danger**: Destructive action fill (`var(--color-feedback-danger)`), white text.
- **Affordance Slots**: Left icon slot (`slot="icon-start"`), label container, right icon slot (`slot="icon-end"`), and optional loading indicator spinner.
- **Typography**: Single-line text (`whitespace: nowrap; text-overflow: ellipsis; overflow: hidden;`), medium weight (`var(--typography-weight-medium, 500)`), tight letter tracking.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-brand-primary)` | `#1C1917` | Primary button fill background |
| **Color** | `var(--color-brand-hover)` | `#292524` | Primary hover state background |
| **Color** | `var(--color-brand-active)` | `#44403C` | Primary active state background |
| **Color** | `var(--color-text-inverse)` | `#FFFFFF` | Text color on solid dark buttons |
| **Color** | `var(--color-surface-sunken)` | `#F4F4F5` | Secondary button background |
| **Color** | `var(--color-border-default)` | `#D6D3D1` | Outline button border |
| **Color** | `var(--color-border-focus)` | `#B45309` | High-visibility focus ring |
| **Color** | `var(--color-feedback-danger)` | `#B91C1C` | Destructive variant background |
| **Spacing** | `var(--spacing-2xs)` | `4px` | Icon-to-text gap |
| **Spacing** | `var(--spacing-xs)` | `8px` | Vertical padding (standard size) |
| **Spacing** | `var(--spacing-md)` | `16px` | Horizontal padding (standard size) |
| **Radius** | `var(--radius-sm)` | `4px` | Corner radius for outer shell |
| **Typography**| `var(--typography-family-body)`| `system-ui` | Button font family |
| **Typography**| `var(--typography-scale-sm)` | `14px` | Text font size (standard size) |
| **Typography**| `var(--typography-weight-medium)`| `500` | Text font weight |
| **Motion** | `var(--motion-duration-fast)`| `120ms` | Transition duration for state shifts |
| **Motion** | `var(--motion-easing-standard)`| `cubic-bezier(0.16, 1, 0.3, 1)` | State transition easing curve |

---

## 3. Behavior Notes & State Machine

1. **Default State**:
   - Cursor: `pointer`. Display: `inline-flex`. Align items: `center`. Justify content: `center`.
   - Box-sizing: `border-box`. User-select: `none`.
2. **Hover State**:
   - Micro-shift in surface tone ($\le 120\text{ms}$). No layout-shifting geometry transforms.
   - Opacity remains 1.0; background shifts to variant-specific hover token.
3. **Focus State (`:focus-visible`)**:
   - 2px solid ring (`var(--color-border-focus)`) with a 2px offset (`outline-offset: 2px`).
   - Never suppressed by `outline: none` unless replaced with equal or higher contrast visual indicator.
4. **Active State (`:active`)**:
   - Micro-compression via `transform: scale(0.98)`. Background shifts to active token.
5. **Disabled State (`disabled` attribute / property)**:
   - `pointer-events: none; opacity: 0.45; cursor: not-allowed;`
   - Removed from sequential focus navigation if `disabled` attribute is present.
6. **Loading State (`loading` attribute / property)**:
   - Replaces or prefixes `slot="icon-start"` with an SVG spinner ring.
   - Prevents duplicate clicks (`aria-busy="true"`). Label text remains readable.
7. **Custom Events Dispatched**:
   - When clicked, dispatches native `click` or custom `ui-button-click` (`bubbles: true`, `composed: true`, `detail: { originalEvent, variant }`).

---

## 4. Acceptance Criteria

- [ ] **Shadow DOM Isolation**: All internal styles reside inside shadow root. No external stylesheet can break internal padding or icon layout.
- [ ] **CSS Variable Inheritance**: Changing `--color-brand-primary` on a parent ancestor immediately re-themes the button without re-mounting.
- [ ] **Single-Line Truncation**: When placed inside a narrow container (e.g. 100px width), long text truncates gracefully with an ellipsis instead of wrapping into two lines.
- [ ] **Responsive Breakpoints**:
  - `320px`: Touch target expands to minimum 44px vertical height (`touch-action: manipulation`).
  - `768px`: Standard 36px desktop ergonomic height.
  - `1280px`: Full alignment within dense desktop grids.
- [ ] **Zero Dead Clicks**: Disabled and loading states reliably prevent form submissions and custom event firing.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **Keyboard Operation**: Triggerable by both `Enter` and `Space` keys. Focus indicators visible across all background surfaces.
- **ARIA Semantics**:
  - Shadow host maps to `role="button"` (or encapsulates a native `<button>` element inside shadow root for automatic browser a11y tree integration).
  - Dynamic `aria-disabled="true"` when disabled.
  - Dynamic `aria-busy="true"` and `aria-live="polite"` when in loading state.
- **Contrast Compliance**: Minimum **4.5:1** contrast ratio between label text and button background across all standard variants in both light and dark modes.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    :host, button {
      transition: none !important;
      transform: none !important;
    }
  }
  ```
