# Design Direction 2: Technical Oceanic (Electric Slate)

A cool-toned, high-velocity engineering system combining deep maritime slate, razor-sharp cobalt accents, and hyper-legible geometric typography. Built for complex data topologies, runtime monitors, and developer consoles.

---

## 1. Moodboard

The visual mood evokes an underwater submarine control room or a satellite ground station operating at midnight. Surfaces feature deep, cool slate tones ranging from oceanic twilight `#0B1120` to dense graphite `#1E293B`. The palette communicates computational discipline, high bandwidth, and zero nonsense. It is neither sterile nor noisy, creating an environment where high-density metrics and operational state indicators can be scanned in milliseconds.

Accents are drawn from electric cobalt `#2563EB`, vibrant cyan `#06B6D4`, and emerald telemetry markers `#10B981`. These colors are applied with surgical discipline—never as ambient decorative wash, but strictly as directional signposts for active states, sorting toggles, and primary execution paths. Contrast between active indicators and structural surfaces is deliberately amplified to provide instantaneous clarity under varied workplace lighting.

Component edges carry a crisp mathematical finish with 6px to 8px radius geometry and micro-hairline borders tinted with translucent cyan-slate. Micro-transitions are snappy ($\le 140\text{ms}$), delivering crisp tactile feedback for high-frequency workflows.

---

## 2. Tokens JSON (W3C Design Tokens Format)

```json
{
  "color": {
    "canvas": {
      "default": {
        "$value": "#0B1120",
        "$type": "color"
      },
      "subtle": {
        "$value": "#0F172A",
        "$type": "color"
      },
      "inverse": {
        "$value": "#F8FAFC",
        "$type": "color"
      }
    },
    "surface": {
      "base": {
        "$value": "#131D33",
        "$type": "color"
      },
      "raised": {
        "$value": "#1E293B",
        "$type": "color"
      },
      "sunken": {
        "$value": "#0A0F1D",
        "$type": "color"
      },
      "overlay": {
        "$value": "#1E293B",
        "$type": "color"
      },
      "inverse": {
        "$value": "#F1F5F9",
        "$type": "color"
      }
    },
    "border": {
      "subtle": {
        "$value": "#1E293B",
        "$type": "color"
      },
      "default": {
        "$value": "#334155",
        "$type": "color"
      },
      "strong": {
        "$value": "#475569",
        "$type": "color"
      },
      "focus": {
        "$value": "#38BDF8",
        "$type": "color"
      }
    },
    "text": {
      "primary": {
        "$value": "#F8FAFC",
        "$type": "color"
      },
      "secondary": {
        "$value": "#94A3B8",
        "$type": "color"
      },
      "tertiary": {
        "$value": "#64748B",
        "$type": "color"
      },
      "inverse": {
        "$value": "#F8FAFC",
        "$type": "color"
      },
      "brand": {
        "$value": "#38BDF8",
        "$type": "color"
      }
    },
    "brand": {
      "primary": {
        "$value": "#2563EB",
        "$type": "color"
      },
      "hover": {
        "$value": "#1D4ED8",
        "$type": "color"
      },
      "active": {
        "$value": "#1E40AF",
        "$type": "color"
      },
      "subtle": {
        "$value": "rgba(37, 99, 235, 0.15)",
        "$type": "color"
      }
    },
    "neutral": {
      "50": {
        "$value": "#F8FAFC",
        "$type": "color"
      },
      "100": {
        "$value": "#F1F5F9",
        "$type": "color"
      },
      "200": {
        "$value": "#E2E8F0",
        "$type": "color"
      },
      "300": {
        "$value": "#CBD5E1",
        "$type": "color"
      },
      "400": {
        "$value": "#94A3B8",
        "$type": "color"
      },
      "500": {
        "$value": "#64748B",
        "$type": "color"
      },
      "600": {
        "$value": "#475569",
        "$type": "color"
      },
      "700": {
        "$value": "#334155",
        "$type": "color"
      },
      "800": {
        "$value": "#1E293B",
        "$type": "color"
      },
      "900": {
        "$value": "#0F172A",
        "$type": "color"
      },
      "950": {
        "$value": "#0B1120",
        "$type": "color"
      }
    },
    "feedback": {
      "success": {
        "$value": "#10B981",
        "$type": "color"
      },
      "success-subtle": {
        "$value": "rgba(16, 185, 129, 0.15)",
        "$type": "color"
      },
      "warning": {
        "$value": "#F59E0B",
        "$type": "color"
      },
      "warning-subtle": {
        "$value": "rgba(245, 158, 11, 0.15)",
        "$type": "color"
      },
      "danger": {
        "$value": "#DC2626",
        "$type": "color"
      },
      "danger-subtle": {
        "$value": "rgba(220, 38, 38, 0.15)",
        "$type": "color"
      },
      "info": {
        "$value": "#38BDF8",
        "$type": "color"
      },
      "info-subtle": {
        "$value": "rgba(56, 189, 248, 0.15)",
        "$type": "color"
      }
    }
  },
  "spacing": {
    "3xs": {
      "$value": "2px",
      "$type": "dimension"
    },
    "2xs": {
      "$value": "4px",
      "$type": "dimension"
    },
    "xs": {
      "$value": "8px",
      "$type": "dimension"
    },
    "sm": {
      "$value": "12px",
      "$type": "dimension"
    },
    "md": {
      "$value": "16px",
      "$type": "dimension"
    },
    "lg": {
      "$value": "24px",
      "$type": "dimension"
    },
    "xl": {
      "$value": "32px",
      "$type": "dimension"
    },
    "2xl": {
      "$value": "48px",
      "$type": "dimension"
    },
    "3xl": {
      "$value": "64px",
      "$type": "dimension"
    }
  },
  "typography": {
    "family": {
      "display": {
        "$value": "'Outfit', system-ui, -apple-system, sans-serif",
        "$type": "fontFamily"
      },
      "body": {
        "$value": "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
        "$type": "fontFamily"
      },
      "mono": {
        "$value": "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
        "$type": "fontFamily"
      }
    },
    "scale": {
      "xs": {
        "$value": "11px",
        "$type": "dimension"
      },
      "sm": {
        "$value": "13px",
        "$type": "dimension"
      },
      "base": {
        "$value": "15px",
        "$type": "dimension"
      },
      "lg": {
        "$value": "18px",
        "$type": "dimension"
      },
      "xl": {
        "$value": "22px",
        "$type": "dimension"
      },
      "2xl": {
        "$value": "28px",
        "$type": "dimension"
      },
      "3xl": {
        "$value": "36px",
        "$type": "dimension"
      }
    },
    "weight": {
      "regular": {
        "$value": "400",
        "$type": "fontWeight"
      },
      "medium": {
        "$value": "500",
        "$type": "fontWeight"
      },
      "semibold": {
        "$value": "600",
        "$type": "fontWeight"
      },
      "bold": {
        "$value": "700",
        "$type": "fontWeight"
      }
    },
    "lineHeight": {
      "tight": {
        "$value": "1.15",
        "$type": "number"
      },
      "snug": {
        "$value": "1.3",
        "$type": "number"
      },
      "normal": {
        "$value": "1.5",
        "$type": "number"
      },
      "relaxed": {
        "$value": "1.6",
        "$type": "number"
      }
    },
    "tracking": {
      "tight": {
        "$value": "-0.015em",
        "$type": "dimension"
      },
      "normal": {
        "$value": "0em",
        "$type": "dimension"
      },
      "wide": {
        "$value": "0.03em",
        "$type": "dimension"
      }
    }
  },
  "radius": {
    "none": {
      "$value": "0px",
      "$type": "dimension"
    },
    "xs": {
      "$value": "2px",
      "$type": "dimension"
    },
    "sm": {
      "$value": "4px",
      "$type": "dimension"
    },
    "md": {
      "$value": "6px",
      "$type": "dimension"
    },
    "lg": {
      "$value": "8px",
      "$type": "dimension"
    },
    "xl": {
      "$value": "12px",
      "$type": "dimension"
    },
    "full": {
      "$value": "9999px",
      "$type": "dimension"
    }
  },
  "elevation": {
    "none": {
      "$value": "none",
      "$type": "shadow"
    },
    "sm": {
      "$value": "0 1px 3px 0 rgba(0, 0, 0, 0.4)",
      "$type": "shadow"
    },
    "md": {
      "$value": "0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -2px rgba(0, 0, 0, 0.4)",
      "$type": "shadow"
    },
    "lg": {
      "$value": "0 10px 15px -3px rgba(0, 0, 0, 0.6), 0 4px 6px -4px rgba(0, 0, 0, 0.5)",
      "$type": "shadow"
    }
  },
  "motion": {
    "duration": {
      "instant": {
        "$value": "40ms",
        "$type": "duration"
      },
      "fast": {
        "$value": "100ms",
        "$type": "duration"
      },
      "normal": {
        "$value": "150ms",
        "$type": "duration"
      },
      "slow": {
        "$value": "220ms",
        "$type": "duration"
      }
    },
    "easing": {
      "standard": {
        "$value": "cubic-bezier(0.2, 0.8, 0.2, 1)",
        "$type": "cubicBezier"
      },
      "entrance": {
        "$value": "cubic-bezier(0, 0, 0.15, 1)",
        "$type": "cubicBezier"
      },
      "exit": {
        "$value": "cubic-bezier(0.3, 0, 1, 1)",
        "$type": "cubicBezier"
      }
    }
  }
}
```

---

## 3. Rationale

1. **Dark Mode Ergonomics for High Information Density**: Deep oceanic slate reduces eye strain in developer setups and multi-monitor operations, allowing engineers to parse logs and telemetry streams for hours without fatigue.
2. **Accessible Contrast in Dark Themes**: Text primary (`#F8FAFC`) on canvas (`#0B1120`) delivers a staggering **17.2:1 contrast ratio**. Secondary labels (`#94A3B8`) provide **6.7:1**, easily exceeding WCAG AA standards.
3. **High-Precision Data Scanning**: Compact typographic scaling (13px body with tabular JetBrains Mono figures) maximizes screen real estate for logs, telemetry matrices, and multi-column tables without clutter.
4. **Optical Compensation in Dark UI**: Letter-tracking is opened slightly (`tracking-wide: 0.03em` on micro-labels) to prevent optical shrinkage against deep dark backgrounds.

---

## 4. Component Sketches

### Button
- **Geometry**: 34px compact height, 14px horizontal padding.
- **Surface**: High-contrast cobalt fill `--color-brand-primary` (`#2563EB`) with crisp 1px inset highlight.
- **Radius**: `--radius-md` (6px).
- **Typography**: 13px SemiBold, `#F8FAFC`.
- **States**:
  - *Hover*: Shift to `#1D4ED8` with subtle drop elevation.
  - *Active*: Scale(0.98), `#1E40AF`.
  - *Focus*: 2px solid ring `--color-border-focus` (`#38BDF8`), offset 2px.

```
+---------------------------------------+
|  Execute Deployment Run               |  <-- Height: 34px, Radius: 6px
+---------------------------------------+
(Background: #2563EB, Text: #F8FAFC, Font: 13px SemiBold)
```

### Input
- **Geometry**: 36px height, dark sunken surface `--color-surface-sunken` (`#0A0F1D`).
- **Border**: 1px solid `--color-border-subtle` (`#1E293B`).
- **Focus**: Border shifts to vibrant cyan `--color-border-focus` (`#38BDF8`), zero blurry outer glow, clean 2px outline.
- **Typography**: 13px JetBrains Mono for code/parameters, `#F8FAFC`.

```
+---------------------------------------+
| >_ filter query: status == 'error'    |  <-- Surface: #0A0F1D, Border: #1E293B
+---------------------------------------+
(Focus Ring: 2px solid #38BDF8)
```

### Card
- **Structure**: Surface base `--color-surface-base` (`#131D33`), bordered by `--color-border-subtle` (`#1E293B`).
- **Padding**: 18px all around.
- **Corner Radius**: `--radius-md` (6px).
- **Header**: Tabular counter anchored right, clean unboxed typographic metadata.
- **Elevation**: `--elevation-sm`.

```
+-------------------------------------------------------------+
| Cluster Node Topology                    Latency: 14.2ms    |
|-------------------------------------------------------------|  <-- Hairline #1E293B
| Ingestion Rate: 48.2k msg/sec            Active Threads: 64 |
| Error Budget Remaining: 99.94%           Region: eu-west-1  |
+-------------------------------------------------------------+
```
