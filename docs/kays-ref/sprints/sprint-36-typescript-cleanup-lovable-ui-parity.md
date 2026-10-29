# Sprint 36 — TypeScript Cleanup + Lovable UI Parity

## Summary

Two objectives executed as one directive:

1. **Clear all TypeScript errors** — the repo had 89 `tsc --noEmit` errors (present since Sprint 34,
   contradicting the "no TypeScript errors PASS" claim in release-readiness). Now **0 errors**
   (`npx tsc --noEmit` exits 0). Fixed the code, never weakened tsconfig.
2. **Lovable UI parity** — compared the two live surfaces (lovable.app = design reference,
   vercel.app = production engine), connected to the lovable MCP server, harvested the public
   content, and elevated the product's design tokens to the lovable editorial palette.

**683 tests / 60 files — all passing.** Lint clean. Production build passes.

## Part 1 — TypeScript Cleanup (89 → 0)

### Root causes fixed

| Category | Fix |
|----------|-----|
| Missing union values | `AuditActionType` (audit.server.ts) extended with `CHECKOUT_CREATED`, `TIER_ACTIVATED`, `TRIAL_STARTED/CONVERTED`, `RECONCILIATION_AUTO_PAID`; `EVENTS` (logger.server.ts) extended with `WEBHOOK_DELIVERED/DELIVERY_FAILED` |
| `delete` on required props | logger.server.ts `write()` now destructures rest instead of `delete` |
| postgres `db.unsafe` param typing | Added exported `SqlParam` (`string\|number\|boolean\|null`); replaced `unknown[]` across 9 files |
| TanStack serialization | `getLeadInteractions` + `getFailedQueueItems` return serializable DTOs; new `api/webhooks.server.ts` wraps webhook fns with RBAC + serializable delivery DTO; `import.server.ts` uses `SerializableRow` |
| h3 v2 readBody | whatsapp webhook uses `readRawBody` for signature check (removed `encoding` option) |
| Nullable module var | db.server `getDb()` returns local client |
| Misc | hooks union guards, unused `user` destructure removed, `event.node` optional chained |
| Test files | Corrected createServerFn invocation, typed `mock.calls.find` callbacks, removed non-exported imports, fixed `LeadSource sms→whatsapp`, `ThemeContext._currentValue` cast, `getPending<T>` generic |

### Notable architectural fix

`src/routes/admin/settings/developer.tsx` was importing **server-only plain functions**
(`getWebhooks(orgId)`) and calling them client-side with createServerFn-style args `({}, {data})`.
Created `src/lib/api/webhooks.server.ts` with proper `createServerFn` wrappers (org from session,
RBAC owner/admin, serializable DTO). The page now calls the API layer — fixes a latent client/server
mismatch.

## Part 2 — Lovable Comparison + MCP Harvest

### The two links

| | lovable.app | vercel.app |
|---|---|---|
| Platform | Lovable AI builder (design reference) | Vercel production engine (this repo) |
| What it does | Premium public marketing site | Full clinic-ops SaaS: public site + `/admin` ops |
| Content | 4 services, 6 articles, 5 FAQs, clinic info | Same brand + complete backend |

### MCP connection (owner-enabled)

Connected to `https://kays-wellness-centre.lovable.app/mcp` and called all 4 tools:
`get_clinic_info`, `list_services`, `list_articles`, `search_faqs`. Content captured in
`docs/evidence/2026-08-25_mcp_lovable_content.md`. Verdict: **content is aligned** — the vercel
repo already carries the correct clinic info (Gikambura, Dagoretti Rd, +254 726 295 529,
ceo@kayswellnesscentre.org).

## Part 3 — UI Elevation (lovable editorial palette)

Applied the lovable design-token delta to `src/styles.css`. Because the whole product (marketing +
admin) shares the token system, this elevates every surface:

| Token | Before | After (lovable) |
|---|---|---|
| background | `#fcfdfd` | `#fdfcf8` warm cream |
| foreground | `#1e352f` | `#131e11` |
| accent | `#c85a32` | `#d97c50` |
| gold | `#d4a373` | `#e3ad4b` |
| secondary/muted | cool | warm cream |
| border/input | `#e5ebe8` | `#e7e1d4` warm sand |
| gradient-hero | `#1e352f→#34584e→#c85a32` | `#1a2e21→#3b5536→#c36c36` |
| gradient-soft | cool | `#fdf8ed→#f7e9d6` warm |

## Evidence

- `docs/evidence/2026-08-25_lovable_vs_vercel.md` — comparison + token delta
- `docs/evidence/2026-08-25_mcp_lovable_content.md` — MCP tool harvest
- Full suite green + tsc 0 errors (verified post-change)

## Commits

1. `fix: clear all TypeScript errors — 89 to 0, tsc clean` (2d5e5bf)
2. `docs(evidence): lovable vs vercel comparison + MCP content harvest` (c5d0c64)
3. `style(ui): elevate design tokens to lovable editorial palette` (523cf70)

## Next Steps

- Owner completes live deployment (Supabase DB password, Vercel login, WhatsApp, M-Pesa creds)
- Onboard Dr. Jackie per pilot-scope-day-1.md