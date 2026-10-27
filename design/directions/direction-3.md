# Design Direction 3: Swiss Minimalist (High-Contrast Editorial)

A razor-sharp, zero-radius typographic grid system inspired by the International Typographic Style (Swiss Style) and classic European technical broadsheets. Built on stark black/white contrast, asymmetric grid divisions, and pure structural hierarchy.

---

## 1. Moodboard

The visual mood draws from the timeless precision of Josef Müller-Brockmann, Armin Hofmann, and mid-century technical standards manuals. The canvas is uncompromising: stark optic white `#FFFFFF`, pitch black `#000000`, and pure neutral grays (`#F4F4F5` to `#18181B`). There are no decorative color tints, warm undertones, or cool blue washes. Every element exists solely to convey information with maximum semantic contrast and typographic balance.

Geometry is unapologetically sharp: zero border radii (`0px`) throughout all components, creating clean rectilinear intersections and razor grid lines. Containers are defined by crisp 1px solid structural borders rather than drop shadows or blurry gradients. Cards do not float in illusory three-dimensional space; they assemble like modular architectural blocks into a continuous structural frame.

Typography dominates the hierarchy. Bold sans-serif display headings paired with high-legibility body type and monospaced tabular data create instant visual rhythm. Interactive controls rely on high-contrast surface inversions—black buttons that turn optic white with black outlines on hover, clean toggle borders, and unboxed metadata separated by slashes (`/`) or middle dots (`·`).

---

## 2. Tokens JSON (W3C Design Tokens Format)

```json
{
  "color": {
    "canvas": {
      "default": { "$value": "#FFFFFF", "$type": "color" },
      "subtle": { "$value": "#F4F4F5", "$type": "color" },
      "inverse": { "$value": "#000000", "$type": "color" }
    },
    "surface": {
      "base": { "$value": "#FFFFFF", "$type": "color" },
      "raised": { "$value": "#FAFAFA", "$type": "color" },
      "sunken": { "$value": "#F4F4F5", "$type": "color" },
      "overlay": { "$value": "#FFFFFF", "$type": "color" },
      "inverse": { "$value": "#18181B", "$type": "color" }
    },
    "border": {
      "subtle": { "$value": "#E4E4E7", "$type": "color" },
      "default": { "$value": "#D4D4D8", "$type": "color" },
      "strong": { "$value": "#18181B", "$type": "color" },
      "focus": { "$value": "#000000", "$type": "color" }
    },
    "text": {
      "primary": { "$value": "#000000", "$type": "color" },
      "secondary": { "$value": "#52525B", "$type": "color" },
      "tertiary": { "$value": "#71717A", "$type": "color" },
      "inverse": { "$value": "#FFFFFF", "$type": "color" },
      "brand": { "$value": "#000000", "$type": "color" }
    },
    "brand": {
      "primary": { "$value": "#000000", "$type": "color" },
      "hover": { "$value": "#27272A", "$type": "color" },
      "active": { "$value": "#3F3F46", "$type": "color" },
      "subtle": { "$value": "#F4F4F5", "$type": "color" }
    },
    "neutral": {
      "50": { "$value": "#FAFAFA", "$type": "color" },
      "100": { "$value": "#F4F4F5", "$type": "color" },
      "200": { "$value": "#E4E4E7", "$type": "color" },
      "300": { "$value": "#D4D4D8", "$type": "color" },
      "400": { "$value": "#A1A1AA", "$type": "color" },
      "500": { "$value": "#71717A", "$type": "color" },
      "600": { "$value": "#52525B", "$type": "color" },
      "700": { "$value": "#3F3F46", "$type": "color" },
      "800": { "$value": "#27272A", "$type": "color" },
      "900": { "$value": "#18181B", "$type": "color" },
      "950": { "$value": "#09090B", "$type": "color" }
    },
    "feedback": {
      "success": { "$value": "#166534", "$type": "color" },
      "success-subtle": { "$value": "#F0FDF4", "$type": "color" },
      "warning": { "$value": "#9A3412", "$type": "color" },
      "warning-subtle": { "$value": "#FFF7ED", "$type": "color" },
      "danger": { "$value": "#991B1B", "$type": "color" },
      "danger-subtle": { "$value": "#FEF2F2", "$type": "color" },
      "info": { "$value": "#1E40AF", "$type": "color" },
      "info-subtle": { "$value": "#EFF6FF", "$type": "color" }
    }
  },
  "spacing": {
    "3xs": { "$value": "2px", "$type": "dimension" },
    "2xs": { "$value": "4px", "$type": "dimension" },
    "xs": { "$value": "8px", "$type": "dimension" },
    "sm": { "$value": "12px", "$type": "dimension" },
    "md": { "$value": "16px", "$type": "dimension" },
    "lg": { "$value": "24px", "$type": "dimension" },
    "xl": { "$value": "32px", "$type": "dimension" },
    "2xl": { "$value": "48px", "$type": "dimension" },
    "3xl": { "$value": "64px", "$type": "dimension" }
  },
  "typography": {
    "family": {
      "display": { "$value": "'Bricolage Grotesque', 'Public Sans', system-ui, sans-serif", "$type": "fontFamily" },
      "body": { "$value": "'Public Sans', system-ui, -apple-system, sans-serif", "$type": "fontFamily" },
      "mono": { "$value": "'JetBrains Mono', ui-monospace, monospace", "$type": "fontFamily" }
    },
    "scale": {
      "xs": { "$value": "12px", "$type": "dimension" },
      "sm": { "$value": "14px", "$type": "dimension" },
      "base": { "$value": "16px", "$type": "dimension" },
      "lg": { "$value": "20px", "$type": "dimension" },
      "xl": { "$value": "24px", "$type": "dimension" },
      "2xl": { "$value": "32px", "$type": "dimension" },
      "3xl": { "$value": "44px", "$type": "dimension" }
    },
    "weight": {
      "regular": { "$value": "400", "$type": "fontWeight" },
      "medium": { "$value": "500", "$type": "fontWeight" },
      "semibold": { "$value": "600", "$type": "fontWeight" },
      "bold": { "$value": "700", "$type": "fontWeight" }
    },
    "lineHeight": {
      "tight": { "$value": "1.1", "$type": "number" },
      "snug": { "$value": "1.25", "$type": "number" },
      "normal": { "$value": "1.45", "$type": "number" },
      "relaxed": { "$value": "1.6", "$type": "number" }
    },
    "tracking": {
      "tight": { "$value": "-0.03em", "$type": "dimension" },
      "normal": { "$value": "0em", "$type": "dimension" },
      "wide": { "$value": "0.04em", "$type": "dimension" }
    }
  },
  "radius": {
    "none": { "$value": "0px", "$type": "dimension" },
    "xs": { "$value": "0px", "$type": "dimension" },
    "sm": { "$value": "0px", "$type": "dimension" },
    "md": { "$value": "0px", "$type": "dimension" },
    "lg": { "$value": "0px", "$type": "dimension" },
    "xl": { "$value": "0px", "$type": "dimension" },
    "full": { "$value": "0px", "$type": "dimension" }
  },
  "elevation": {
    "none": { "$value": "none", "$type": "shadow" },
    "sm": { "$value": "none", "$type": "shadow" },
    "md": { "$value": "none", "$type": "shadow" },
    "lg": { "$value": "none", "$type": "shadow" }
  },
  "motion": {
    "duration": {
      "instant": { "$value": "0ms", "$type": "duration" },
      "fast": { "$value": "80ms", "$type": "duration" },
      "normal": { "$value": "120ms", "$type": "duration" },
      "slow": { "$value": "180ms", "$type": "duration" }
    },
    "easing": {
      "standard": { "$value": "linear", "$type": "cubicBezier" },
      "entrance": { "$value": "linear", "$type": "cubicBezier" },
      "exit": { "$value": "linear", "$type": "cubicBezier" }
    }
  }
}
```

---

## 3. Rationale

1. **Uncompromised Information Fidelity**: By eliminating faux 3D shadows and rounded corners, screen pixels map 100% to usable content. Grids lock together without micro-gaps or awkward corner radii overlap.
2. **Absolute Maximum Contrast**: Pure black `#000000` text on optic white `#FFFFFF` achieves a **21:1 contrast ratio**, the absolute theoretical maximum of the WCAG luminance scale. Secondary text (`#52525B`) delivers **7.4:1**, far exceeding all accessibility standards.
3. **Speed of Perception**: Instant state toggling (linear 80ms or 0ms transitions) means controls don't lag behind operator motor actions. Ideal for technical documentation, benchmarking laboratories, and high-cadence analytical consoles.
4. **Architectural Grid Discipline**: Everything adheres to crisp 1px borders (`#18181B` or `#D4D4D8`). Tables and forms assemble into structural broadsheet layouts that feel authoritative, permanent, and serious.

---

## 4. Component Sketches

### Button
- **Geometry**: 36px height, 16px horizontal padding.
- **Radius**: `0px` (strict right angles).
- **Surface**: Solid `#000000`, Text `#FFFFFF`.
- **Border**: 1px solid `#000000`.
- **States**:
  - *Hover*: Inverse surface—Background `#FFFFFF`, Text `#000000`, 1px solid `#000000` border.
  - *Focus*: 2px solid `#000000` offset outline.

```
+---------------------------------------+
|  EXPORT AUDIT LOG                     |  <-- Height: 36px, Radius: 0px
+---------------------------------------+
(Background: #000000, Text: #FFFFFF, Sharp 90-degree corners)
```

### Input
- **Geometry**: 38px height, 12px inset.
- **Radius**: `0px`.
- **Surface**: Clean `#FFFFFF`, 1px solid `#18181B`.
- **Focus**: Thick 2px solid `#000000` border, zero outer glow or blur.
- **Typography**: 14px Regular, Public Sans.

```
+---------------------------------------+
| Search components by keyword...       |  <-- Sharp 0px corners, Border: #18181B
+---------------------------------------+
(Focus State: Solid 2px #000000 line)
```

### Card
- **Structure**: Razor-sharp box (`0px` radius), 1px solid structural border `#18181B`.
- **Padding**: 24px desktop, 16px mobile.
- **Header**: Black structural accent banner or hairline rule `#18181B`.
- **Elevation**: None. Separation achieved through border geometry and whitespace.

```
+-------------------------------------------------------------+
| SPECIFICATION 04 / COMPONENT REPOSITORY                     |
|-------------------------------------------------------------|  <-- Solid 1px #18181B
| Total Components: 24                      Coverage: 100%    |
| Standard: W3C Design Tokens               WCAG Level: AAA   |
+-------------------------------------------------------------+
```
