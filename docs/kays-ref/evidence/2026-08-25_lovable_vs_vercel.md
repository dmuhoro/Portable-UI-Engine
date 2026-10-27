# Lovable vs Vercel — Comparison & UI Elevation Plan

> Analysis of the two live Kay's Wellness Centre surfaces (2026-08-25).

## What each link is

| | `kays-wellness-centre.lovable.app` | `kays-wellness-centre.vercel.app` |
|---|---|---|
| **Platform** | Lovable (AI app builder) — the design/reference prototype | Vercel — the actual production engine (this repo) |
| **Role** | Premium marketing + brand reference; public clinic site | Full clinic-ops SaaS: public marketing site + `/admin` operations (leads, scheduling, billing, M-Pesa, WhatsApp) |
| **Backend** | None visible (static/marketing) | Complete TanStack Start + Postgres engine (667+ tests) |
| **Content** | 4 service areas, 6 articles, 5 FAQs, clinic info | Same brand + full operational backend |

## MCP Connection (enabled by owner)

The lovable site exposes an MCP server at `/mcp` with 4 tools. All called successfully:

- `get_clinic_info` → name, founder (Dr. Jacqueline Mwanu MD MBChB MPH IHDiP), location
  (Rubis Gikambura, Dagoretti Rd, 1st Floor Room 9), phone +254 726 295 529,
  email ceo@kayswellnesscentre.org, 60-min consultations, telehealth + home visits
- `list_services` → 4 treatment areas (Digestive, Hormone/Endocrine, Autoimmune,
  Lifestyle/Metabolic) + 8 on-site offerings (Modern Lab, Dispensing Pharmacy,
  Home Care Visits, Consultations, Imaging, Functional Testing, Physiotherapy &
  Osteopathy, Lymphatic Drainage)
- `list_articles` → 6 wellness education articles (H. Pylori/fatigue, functional labs,
  metabolic movement, PCOS, Hashimoto's, vagus nerve)
- `search_faqs` → 5 FAQs (functional medicine, referral, insurance, consultation
  length, telehealth/home visits)

**Verification:** The vercel repo's contact/privacy pages already carry the correct clinic
info (Gikambura, Dagoretti, phone, email) — content is aligned. The MCP content is now
captured in this repo's evidence/docs for future use.

## UI Gap — What makes lovable "elite"

Design-token delta (lovable is a warmer, more editorial, premium refinement of the same
Afrocentric palette):

| Token | Lovable | Vercel repo (current) | Delta |
|---|---|---|---|
| `--background` | `#fdfcf8` (warm cream) | `#fcfdfd` (cool white) | warmer |
| `--foreground` | `#131e11` | `#1e352f` | deeper |
| `--accent` | `#d97c50` | `#c85a32` | softer terracotta |
| `--gold` | `#e3ad4b` | `#d4a373` | richer gold |
| `--muted` | `#f9f5ec` | `#f4f6f5` | warm cream |
| `--secondary` | `#f7eddc` | `#f7f5f0` | warm cream |
| `--terracotta` | `#cf6139` | `#c85a32` | slightly warmer |
| `--border` | `#e7e1d4` | `#e5ebe8` | warm sand |
| `--primary` | `#1f3326` | `#1e352f` | near-identical |
| `--sage` | `#a4c0a4` | `#a9bdb2` | near-identical |
| `--mint` | `#dceacf` | `#ddebe3` | near-identical |
| `--gradient-hero` | `#1a2e21→#3b5536→#c36c36` | `#1e352f→#34584e→#c85a32` | warmer mid-tone |
| `--gradient-soft` | `#fdf8ed→#f7e9d6` (warm) | `#fcfdfd→#f3f6f4` (cool) | warmer |
| Display font | CameraPlainVariable | Plus Jakarta Sans | editorial serif-ish |

**Strategy (Pareto):** the highest-leverage UI elevation is refining the design tokens to the
warmer editorial palette + ensuring the homepage/hero uses the gradient system effectively —
without rebuilding components. The admin operational UI (the real product) already shares the
same token system, so warming the tokens elevates the whole product, not just marketing.

## Evidence

- MCP tool outputs: `docs/evidence/2026-08-25_mcp_lovable_content.md`
- This analysis: `docs/evidence/2026-08-25_lovable_vs_vercel.md`