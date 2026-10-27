# Component Design Brief: Input (`<ui-input>`)

A text input field component encapsulated in Shadow DOM with support for leading/trailing affordance icons, clearable trigger, field prefix/suffix, character counter, and inline validation messaging.

---

## 1. Screenshot Description

- **Visual Geometry**: Clean rectangular input box with subtle corner radius (`var(--radius-sm, 4px)`). Height is 38px in standard desktop mode and 44px on mobile viewports. Horizontal padding is 12px inset.
- **Surface & Borders**: Base background is `var(--color-surface-base, #FFFFFF)` in light mode or `var(--color-surface-sunken, #0A0F1D)` in dark mode. Structural hairline border is 1px solid `var(--color-border-subtle, #E7E5E4)` in resting state.
- **Prefix / Suffix / Slots**: Supports `slot="prefix"` (e.g. `$`, `https://`), `slot="leading-icon"`, inner native `<input>`, `slot="trailing-icon"`, and a quick clear `(x)` button.
- **Helper & Validation Text**: Directly beneath the field container sits a quiet unboxed helper label or error message (`var(--typography-scale-xs, 12px)`). In error state, the border shifts to `var(--color-feedback-danger)` and the error text renders with a warning glyph.
- **Typography**: 14px regular font (`var(--typography-scale-sm)`), left-aligned with optical vertical centering.

---

## 2. Tokens Needed

| Token Category | Token Variable | Fallback Value | Purpose in Component |
| :--- | :--- | :--- | :--- |
| **Color** | `var(--color-surface-base)` | `#FFFFFF` | Input background fill |
| **Color** | `var(--color-surface-sunken)` | `#F4F4F5` | Disabled / read-only fill |
| **Color** | `var(--color-border-subtle)` | `#E7E5E4` | Resting state border |
| **Color** | `var(--color-border-focus)` | `#B45309` | Active focus indicator border |
| **Color** | `var(--color-feedback-danger)` | `#B91C1C` | Validation error border and text |
| **Color** | `var(--color-text-primary)` | `#1C1917` | Typed value text color |
| **Color** | `var(--color-text-secondary)` | `#57534E` | Label and helper text color |
| **Color** | `var(--color-text-tertiary)` | `#78716C` | Placeholder text color |
| **Spacing** | `var(--spacing-xs)` | `8px` | Vertical internal padding |
| **Spacing** | `var(--spacing-sm)` | `12px` | Horizontal internal inset |
| **Spacing** | `var(--spacing-2xs)` | `4px` | Label-to-input gap |
| **Radius** | `var(--radius-sm)` | `4px` | Shell corner radius |
| **Typography**| `var(--typography-family-body)`| `system-ui` | Value and placeholder font |
| **Typography**| `var(--typography-scale-sm)` | `14px` | Value font size |
| **Typography**| `var(--typography-scale-xs)` | `12px` | Helper / error font size |
| **Motion** | `var(--motion-duration-fast)`| `120ms` | Focus border transition |
| **Motion** | `var(--motion-easing-standard)`| `cubic-bezier(0.16, 1, 0.3, 1)` | Focus transition easing |

---

## 3. Behavior Notes & State Machine

1. **Default State**:
   - Border is 1px solid `var(--color-border-subtle)`. Placeholder text renders with minimum 4.5:1 contrast against surface base.
2. **Hover State**:
   - Border shifts to `var(--color-border-default)` to signal interactivity without triggering full focus.
3. **Focus State (`:focus-within`)**:
   - The container border shifts to `var(--color-border-focus)` with an optional 1px outer ring or shadow.
   - Native input outline is reset inside shadow root so only the styled container outline renders.
4. **Invalid / Error State (`invalid` or `error` attribute)**:
   - Border transitions to `var(--color-feedback-danger, #B91C1C)`.
   - Focus ring inherits danger color.
   - Inline error message below the input becomes visible with `aria-live="polite"`.
5. **Disabled State (`disabled` attribute)**:
   - Background shifts to `var(--color-surface-sunken)`.
   - Opacity is reduced to 0.6. Input is non-editable and skipped during tab navigation.
6. **Custom Events Dispatched**:
   - Dispatches `ui-input-change` on change (`detail: { value, name, isValid }`).
   - Dispatches `ui-input-submit` when `Enter` key is pressed.

---

## 4. Acceptance Criteria

- [ ] **Shadow DOM Encapsulation**: Form autofill and browser-specific password reveals do not misalign internal slot icons.
- [ ] **Responsive Breakpoints**:
  - `320px`: Touch target increases to 44px minimum height. Inset remains 12px.
  - `768px`: Desktop 38px height.
  - `1280px`: Seamless alignment inside multi-column form layouts.
- [ ] **Clearable Trigger**: When `clearable="true"` and input has value, clicking clear button empties value, re-focuses field, and fires `ui-input-change`.
- [ ] **No Overflow on Long Input**: Value scrolls horizontally within input bounds without wrapping or breaking layout.

---

## 5. Keyboard & Accessibility (WCAG 2.1 AA)

- **Keyboard Operation**: Tab reaches inner `<input>`. Focus rings remain visible in high-contrast modes.
- **ARIA Semantics**:
  - Inner input linked via `aria-describedby` to helper/error element.
  - `aria-invalid="true"` when in invalid state.
  - Required fields marked with `aria-required="true"`.
- **Contrast**:
  - Placeholder: $\ge 4.5:1$ against field background.
  - Value text: $\ge 7:1$ against field background.
- **Reduced-Motion Support**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .input-container {
      transition: none !important;
    }
  }
  ```
