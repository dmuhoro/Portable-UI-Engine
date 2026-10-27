# Showcase App Composition: Component Gallery (`apps/docs`)

A modern, high-density component gallery and design system documentation portal. Designed for rapid component discovery, token exploration, and live interactive state inspection across responsive breakpoints.

---

## 1. Visual Look & Feel and Layout Architecture

The documentation layout adheres to a crisp, high-contrast architectural structure. The canvas relies on `var(--color-canvas-default)` with clean 1px hairline dividers (`var(--color-border-subtle)`). The interface prioritizes scannable content density without visual clutter, adhering strictly to the Anti-Slop Constitution (zero decorative badges, clean unboxed metadata, and high-contrast typography).

```
+--------------------------------------------------------------------------------------------------------+
| [Portable UI Engine]             Components   Tokens   Patterns   Guides                 [Export Bundle] |  <-- Top Bar (3-Zone)
+--------------------------------------------------------------------------------------------------------+
|                                                                                                        |
|  DESIGN SYSTEM EXPLORER                                                                                |
|  Framework-Agnostic Web Components with Shadow DOM Encapsulation                                       |
|                                                                                                        |
|  +---------------------------------------+  +-------------------------------------------------------+  |
|  | Search 24 components by keyword...     |  | [ All ] [ Forms ] [ Overlays ] [ Navigation ] [ Feedback ] |  |  <-- Filter Bar
|  +---------------------------------------+  +-------------------------------------------------------+  |
|                                                                                                        |
|  +---------------------------+  +---------------------------+  +---------------------------+           |
|  | Button (<ui-button>)      |  | Input (<ui-input>)        |  | Select (<ui-select>)      |           |
|  |---------------------------|  |---------------------------|  |---------------------------|           |
|  |   [ Primary Action ]      |  |  +---------------------+  |  |  +---------------------+  |           |
|  |   [ Secondary Action ]    |  |  | Enter value...      |  |  |  | Select option...  v |  |           |
|  |   [ Destructive Action ]  |  |  +---------------------+  |  |  +---------------------+  |           |
|  |                           |  |                           |  |                           |           |
|  | WCAG AAA · 5 Variants     |  | ARIA Validated · Clearable|  | Combobox · Searchable     |           |  <-- 3-Col Grid
|  +---------------------------+  +---------------------------+  +---------------------------+           |
|                                                                                                        |
|  +---------------------------+  +---------------------------+  +---------------------------+           |
|  | Dialog (<ui-dialog>)      |  | Tabs (<ui-tabs>)          |  | Toast (<ui-toast>)        |           |
|  |---------------------------|  |---------------------------|  |---------------------------|           |
|  |  +---------------------+  |  |  [ General | API | Logs ] |  |  +---------------------+  |           |
|  |  | Modal Content Body  |  |  |  -----------------------  |  |  | (v) Changes saved   |  |           |
|  |  +---------------------+  |  |  Active Pane Body Content |  |  +---------------------+  |           |
|  |                           |  |                           |  |                           |           |
|  | Focus-Trapped · Top Layer |  | Roving Tabindex · Nav     |  | Live Region · Auto-Dismiss|           |
|  +---------------------------+  +---------------------------+  +---------------------------+           |
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Token Mappings

| Component Region | Token CSS Custom Property | Token Fallback Value | Rationale |
| :--- | :--- | :--- | :--- |
| **Page Canvas** | `var(--color-canvas-default)` | `#F9F8F6` | Warm, low-fatigue backdrop field |
| **Header Bar** | `var(--color-surface-base)` | `#FFFFFF` | Clear structural separation from canvas |
| **Dividers & Rules** | `var(--color-border-subtle)` | `#E7E5E4` | 1px hairline border gridlines |
| **Component Cards** | `var(--color-surface-base)` | `#FFFFFF` | Isolated white surface for component previews |
| **Card Borders** | `var(--color-border-subtle)` | `#E7E5E4` | Crisp 1px perimeter box |
| **Card Corner Radius**| `var(--radius-md)` | `6px` | Structured container geometry |
| **Filter Track** | `var(--color-surface-sunken)` | `#F3F1EC` | Segmented filter control background |
| **Search Input** | `var(--color-surface-base)` | `#FFFFFF` | High-contrast search container |
| **Display Heading** | `var(--typography-family-display)` | `'Plus Jakarta Sans', sans-serif` | Clean geometric brand display |
| **Metadata Text** | `var(--color-text-secondary)` | `#57534E` | Unboxed typographic metadata |
| **Focus Indicator** | `var(--color-border-focus)` | `#B45309` | High-contrast 2px accessibility focus ring |

---

## 3. Responsive Breakpoint Layouts

### 1280px (Desktop Wide)
- **Top Bar**: Full 3-zone layout with brand wordmark on left, 4 navigation links centered, and primary action button on right (`gap-8`, height 56px).
- **Workspace Grid**: 3-column component card grid with 24px gutter (`gap: var(--spacing-lg)`).
- **Interactive Search**: Search input on left (380px fixed width), category segmented control on right (`display: flex; justify-content: space-between`).
- **Token Inspector Drawer**: Right-hand collapsible panel (340px width) displaying live token values and token JSON export.

### 768px (Tablet)
- **Top Bar**: Brand wordmark on left; primary action button on right; navigation links collapse into a clean drawer or horizontal subnav.
- **Workspace Grid**: 2-column component card grid with 16px gutter (`gap: var(--spacing-md)`).
- **Interactive Search**: Search input spans full width with horizontal-scrolling category chips below it.
- **Card Padding**: Scaled to 16px inset.

### 320px (Mobile)
- **Top Bar**: Compact height (48px); brand title truncated if necessary; icon action trigger on right.
- **Workspace Grid**: Single 1-column card stack with 12px gutter.
- **Touch Targets**: All interactive controls within preview cards expand to $\ge 44\text{px}$ minimum height.
- **Search Bar**: Sticky below header with 100% width. Category filter tabs scroll smoothly horizontally without visible scrollbars.

---

## 4. Shadow DOM Architecture & Implementation Notes

- **Preview Isolation**: Each component card in the gallery houses a native Web Component inside its own Shadow DOM root. Global CSS overrides from the documentation application cannot leak into or alter the component's internal styles.
- **Live Theme Switching**: The documentation page dynamically mutates CSS custom properties on `:root` or `html[data-theme]`, instantly propagating tokens through all Shadow DOM roots.
- **Interactive State Inspection**: Each card includes interactive toggles for `:hover`, `:focus-visible`, and `[disabled]` states that set component attributes directly.

---

## 5. Token Export Configuration

```json
{
  "docsLayout": {
    "grid": {
      "desktopColumns": 3,
      "tabletColumns": 2,
      "mobileColumns": 1,
      "gutter": "var(--spacing-lg)"
    },
    "card": {
      "surface": "var(--color-surface-base)",
      "border": "1px solid var(--color-border-subtle)",
      "radius": "var(--radius-md)",
      "padding": "var(--spacing-lg)"
    }
  }
}
```
