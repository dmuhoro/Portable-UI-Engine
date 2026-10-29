# Sprint 38 — Production Go-Live: Env Wiring, API Fixes, UI Parity

## Summary

Took the product from "reachable but blocked" to a **fully operational production deployment**.
Set all Vercel env vars, fixed two production-only bugs (Nitro lazy-handler 500s and the
unbundled `postgres` driver), made `/api/health` report real connectivity, seeded the default
organization + admin in the Supabase database, verified the login flow end-to-end in production,
and aligned the Vercel site's UI/copy with the Lovable deploy.

**695 tests / 62 files — all passing.** `tsc --noEmit` exit 0. ESLint 0 errors. Production build
passes. All changes deployed and verified live on https://kays-wellness-centre.vercel.app.
Tier 1 (Part 7): WhatsApp credentialed + live-delivered, M-Pesa STK trigger wired into billing,
circuit-breaker dispatch on both hot paths, message-ledger audit trail.

## Part 1 — Production Database Connection (unblocked)

### Root cause of the long-standing DB blocker

- The direct host `db.yztalvyiixvlyxrlfnqn.supabase.co` is **IPv6-only** and unreachable from
  Vercel serverless (IPv4).
- The CLI's linked project revealed the **correct pooler host**: `aws-1-eu-west-1.pooler.supabase.com`
  (note **`aws-1`**, not `aws-0`). Earlier attempts used the wrong pooler host.
- The owner's new password `lGfPktZNw1NB5MmX` authenticates successfully against the transaction
  pooler on port **6543**.

Working connection string:
`postgresql://postgres.yztalvyiixvlyxrlfnqn:<password>@aws-1-eu-west-1.pooler.supabase.com:6543/postgres`

### Env vars set in Vercel (all 12, via project-scoped token)

`DATABASE_URL`, `SESSION_SECRET` (generated), `NODE_ENV=production`,
`DEFAULT_ADMIN_EMAIL=admin@kayswellnesscentre.org`, `DEFAULT_ADMIN_PASSWORD` (generated),
`MPESA_BASE_URL`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`,
`MPESA_PASSKEY`, `MPESA_CALLBACK_URL`, `MPESA_CALLBACK_SECRET`. All applied to
production/preview/development.

## Part 2 — Production Bug Fixes (deployed)

### Bug 1: "Invalid lazy handler" 500 on every `/api/*` route

- **Symptom:** after the Sprint 37 route fix, all API routes returned
  `{"error":true,"status":500,"unhandled":true}` while static pages rendered 200.
- **Root cause:** Nitro 3 beta's Vercel web-format build wraps each route in a lazy handler that
  resolves only the module's **default export** (the SSR renderer worked because it uses
  `export default`). Our route files exported only **named** `GET`/`POST` handlers, so h3's
  `toEventHandler()` returned `undefined` → `TypeError: Invalid lazy handler` on every request.
- **Fix:** each of the 6 route handlers (`health`, `calendar-sync`, `automation-orchestrator`,
  `live-updates`, `webhooks/mpesa`, `webhooks/whatsapp`) now also exports a **default eventHandler**
  that dispatches on the HTTP method to the existing named handler.
- **Verified:** `/api/health` returns proper JSON; `/api/webhooks/mpesa` GET → 405;
  `/api/webhooks/whatsapp` GET → 403 (verification rejects bad token).

### Bug 2: "Cannot find package 'postgres'" on every DB access

- **Root cause:** `db.server.ts` imported postgres via an obfuscated dynamic import
  (`["p","o","s",...].join("")`). This hid the specifier from the **server** bundler too, so the
  driver stayed externalized and the serverless runtime couldn't find it — every DB-backed feature
  crashed in production while working locally.
- **Fix:** literal `import("postgres")` in `db.server.ts`, plus a client-environment
  `rollupOptions.external: ["postgres"]` in `vite.config.ts` so the browser bundle still excludes it.
- **Verified:** `postgres.mjs` is now bundled in `.vercel/output/functions/__server.func/_libs/`;
  `/api/health` returns `{"status":"healthy","dbAvailable":true,...}` from the deployed function.

### Improvement: `/api/health` now actively pings the DB

- Previously the health endpoint read a passive module flag that only turned true after any DB
  query — a cold serverless instance always reported "unhealthy". Added `pingDb()` to `db.server.ts`
  (runs `SELECT 1`, updates availability state, records errors). Health now reports true
  connectivity. Tests updated to mock `pingDb()`.

## Part 3 — Seeded + Verified Production Data

- Ran the schema hydrate against the production pooler → **28 tables created** (all tenants).
- `seedDefaultOrgAndAdmin()` created:
  - Org: **Kay's Wellness Centre** (`kays-wellness`) — Africa/Nairobi
  - Admin: `admin@kayswellnesscentre.org` (password stored in Vercel env)
  - Default clinic availability (Mon–Sat)
- **Login verified end-to-end in production** via the `/_serverFn/*` RPC endpoint:
  status 200, `set-cookie` present, `{ success: true, user: { role: "admin" } }`.

> Note: the RPC endpoint requires the seroval cross-JSON payload envelope `{t, f, m}` — a raw JSON
> body is not parseable by TanStack's seroval deserializer. This is client-framework behavior, not
> a bug.

## Part 4 — Lovable UI Parity (permanent)

### The mismatch

The Vercel deploy rendered differently from the Lovable reference for two reasons:

1. **Theme:** the theme hook + inline init script defaulted to the OS color-scheme preference, so a
   dark-mode system rendered the whole site dark. Lovable always renders light.
2. **Copy:** home + services carried the older "Premium Functional Medicine / Nairobi" content
   (7 executive protocols). Lovable's live site is "Holistic Medical Care in Kenya".

### Fixes (per owner decision: match Lovable)

- **Theme:** `use-theme.ts` `getInitialTheme()` and the `__root.tsx` inline init script now default
  to **light**, respecting an explicit stored choice only.
- **Home page:** 3 hero slides (Root-Cause Medicine, Whole-Person Care, Global Mission), "Our
  Focus / Care for the whole person" with 4 areas (Digestive Health, Hormone & Endocrine,
  Autoimmune Care, Lifestyle Diseases), "Global Mission / Shifting the culture of healthcare",
  "Start Your Journey", "From firefighting illness to true wellness" CTA. Removed the
  Specialty-modal grid to match Lovable's structure.
- **Services page:** "Whole-Person, Whole-System Care", Specialized Treatments (4 conditions),
  "Functional Medicine, Delivered", Clinic Offerings.
- **Titles/OG/Twitter meta** updated on `__root`, home, and services.

### Verified

Built output + live production: home and services render the Lovable copy, no `dark` class in SSR,
title "Kay's Wellness Centre — Holistic Medical Care in Kenya".

## Part 5 — Branded Image Parity (permanent)

### The mismatch

After copy + theme matched, the Vercel site still differed visually: home, our-story and resources
rendered **generic Unsplash stock photos** while Lovable served the clinic's own **branded imagery**
(`hero-clinic-CjGQtwC_.jpg`, `dr-jackie-BPEGanEG.jpg`, `team-1-BpnzEXNC.jpg`,
`wellness-1-CgFIaApR.jpg`). The repo's `src/assets/` already contained these exact images (added in
the Sprint-6 asset hot-patch) but they were **never imported** — every route hard-coded Unsplash URLs.

### Fixes

- Wired the local images in via Vite asset imports (`import heroClinic from "@/assets/hero-clinic.jpg"`):
  - `index.tsx`: `hero-clinic.jpg` (right-side hero image) + `dr-jackie.jpg` (mission section).
  - `our-story.tsx`: `dr-jackie.jpg` (founder hero) + `team-1/2/3.jpg` (specialist cards).
  - `resources.tsx`: `wellness-1/2/3.jpg` (article cards).
- **HeroCarousel re-layouted to match Lovable:** removed the dark photo-overlay backgrounds (text on
  photo with white heading); Lovable renders light text on the plain page background. Badge now uses
  `glass border-warm` + `text-primary`, description uses `text-muted-foreground`, matching Lovable's
  markup exactly.
- **og:image / twitter:image** now point to the stable
  `https://kays-wellness-centre.vercel.app/og/hero-clinic.jpg` (copied to `public/og/` so it is never
  content-hashed) instead of an Unsplash URL.

### Verified

- MD5 of every local `src/assets/*.jpg` is **byte-identical** to the image Lovable serves (hero,
  dr-jackie, team-1/2/3, wellness-1/2/3).
- Built output emits the **same hashed filenames as Lovable** (`hero-clinic-CjGQtwC_.jpg`,
  `dr-jackie-BPEGanEG.jpg`, `team-1-BpnzEXNC.jpg`, `wellness-1-CgFIaApR.jpg`, …).
- Local `nitro preview` of the built output: home, our-story and resources serve only the branded
  local images; **zero** Unsplash references remain in `src/` or the built HTML.
- **Live production (deployment `dpl_2eWDgruP43Uimh9Btb2KnRpeQRng`, READY):** served images are
  byte-identical to the repo (MD5-verified over HTTPS); home/our-story/resources carry only branded
  local images with zero Unsplash; hero badge renders `glass border-warm` with
  "From firefighting illness to striving for true wellness."; og:image resolves
  (`/og/hero-clinic.jpg`, MD5 matches); `/api/health` healthy.
- 683 tests green, tsc 0, eslint 0 errors, build passes.

## Part 6 — Elite "Warm Midnight Forest" Dark Theme (designed)

### The mismatch

After copy, theme default and branded images matched Lovable, the **dark mode** was still the
generic dark-green palette the site shipped with — the "dark appearance" the owner could still see
when toggling. Lovable itself has no dark mode (light-only), so this was designed from scratch to be
**elite, premium and worth a monthly subscription** — not a default Tailwind dark.

### Design intent

"Warm Midnight Forest": a warm, deep charcoal-forest green ground carrying the brand's
savannah-olive DNA, with **luminous sage-olive** primary, **burnished terracotta ember** accent and
**warm gold** highlights. Designed so light and dark feel like one continuous brand, not two
unrelated UIs.

### Token set (`src/styles.css`)

- `--background: #10150f` (deep warm forest), `--foreground: #eef0e8` (warm parchment)
- `--card: #161c15`, `--popover: #1a2219` (layered warm forest-floor surfaces)
- `--primary: #9dbf8a` (luminous sage-olive), `--accent: #e08953` (terracotta ember),
  `--gold: #e6b45c` (warm gold)
- `--border: #26332c`, `--ring: #e08953` (warm focus ring)
- Dark-tuned `--gradient-hero`, `--gradient-warm`, `--gradient-glass`, shadows.

### Premium system additions

- `color-scheme: light` / `dark` so native controls + scrollbars match the theme.
- Theme-aware `.glass` border (`--glass-border`), dark `text-gradient` (sage→gold→terracotta).
- Slim on-theme scrollbars, accent-tinted `::selection`, visible premium `:focus-visible` ring.
- Smooth cross-fade on theme toggle via a transient `.theme-transition` class.
- **40+ `dark:text-*-400` variants** so status colors (red/amber/emerald/sky/violet) stay legible
  on the dark ground.
- Theme-token swap for all hardcoded `gray-*` (OnboardingWizard, BillingLedger).
- Refined Operations Dashboard: "At a glance." header, live-telemetry indicator, card-lift hover.

### Verified

- **Light theme byte-identical to Lovable** in compiled CSS (`:root` tokens unchanged, MD5-compared).
- Compiled CSS contains the new `.dark` palette + `dark:text-*-400` rules (`:is(.dark *)`).
- SSR home renders light by default (no `dark` class) — same as Lovable.
- 683 tests green, tsc 0, eslint 0 errors, build passes.

## Part 7 — Tier 1: Real WhatsApp Delivery, M-Pesa STK from Billing, Breakered Dispatch + Ledger

Continuation of the sprint after the owner-approved go-live snapshot (deploy `dpl_2eWDgruP43Uimh9Btb2KnRpeQRng`).
Closes the two "fake protection" gaps from the pilot plan: notifications were sending even when the
only real channel was down (no honest fallback), and STK initiation existed server-side but had no
UI trigger.

### 7.1 WhatsApp credentials live (Vercel)

- `WHATSAPP_TOKEN` (Token A) + `WHATSAPP_PHONE_NUMBER_ID` (`1217627134774899`) set across
  production/preview/development (Vercel env count raised 12 → **14**).
- **Live send verified with real credentials:** message to `254703939236` delivered
  (`wamid.HBgMMjU0NzAzOTM5MjM2FQIAERgSRjlFMURDRjhFQTk2MEEyNDI1AA==`).
- **Caveat (owner follow-up):** Token A is a short-lived token expiring **2026-08-27T17:00:00 UTC**.
  Convert to a permanent WhatsApp system-user token (`whatsapp_business_messaging` +
  `whatsapp_business_management`) before that time or live delivery silently degrades to the log
  provider. The WABA `1107993174991094` is a test account and the test number is `NOT_VERIFIED` —
  production patient-facing delivery needs the verified clinic number.

### 7.2 M-Pesa STK push UI trigger (Billing)

- `BillingLedger` now renders an emerald **M-Pesa** button on every unpaid/not-void invoice row.
  It opens a new `StkPrompt` modal: patient phone pre-filled from the decrypted `lead_phone`
  (fallback manual entry when empty), account reference derived from the invoice number, and a
  "Send STK Push" action calling `initiateStkPush`. Success → toast + query invalidation; every
  failure status maps to a human message. Paid/void rows show no trigger.

### 7.3 Circuit breaker on the live dispatch path

- New `dispatchWithBreaker(orgId, recipient, message)` in `src/lib/api/dispatch.server.ts`:
  short-circuits to an honest failure when `getAvailableChannels` reports every channel
  circuit-open, otherwise calls `sendWithFallback` with **whatsapp** primary. The SMS branch of the
  send adapter **returns `false`** — there is no SMS provider, and the code refuses to claim a
  fallback that doesn't exist (fail closed, never fail open / no fake protection).
- Both live entry points now route through the breaker instead of calling raw `sendWhatsApp`:
  - `dispatchLeadMessage` (`dispatch.server.ts`)
  - `dispatchNotification` (queue worker, `queue.server.ts`)
  - `queue.server.ts` uses a dynamic `await import` for `dispatchWithBreaker` to avoid deepening the
    existing circular `queue ↔ dispatch` module coupling.

### 7.4 Message ledger audit trail

- Both hot paths call `logMessage` after delivery: `direction: "outbound"`, status `sent`/`failed`,
  and metadata tagged with `eventType`/`messageType` + `provider`. A ledger write failure is
  caught and logged — it never breaks the actual dispatch (no silent drop, no false record).

### 7.5 Tests (real path, not mocks of mocks)

- `dispatch-breaker-wiring.test.ts` asserts `dispatchNotification` (the queue worker's production
  send) calls `dispatchWithBreaker` and never raw `sendWhatsApp`, writes `sent`/`failed` ledger
  rows, survives a ledger outage, and skips cleanly when a lead has no phone.
- `dispatch.test.ts` gains `dispatchWithBreaker` unit coverage: whatsapp-primary routing, fail-closed
  on all-open circuits, honest failure propagation, and no fake SMS success.
- `billing-stk-ui.test.tsx` (new, per-file `happy-dom` + real QueryClient): renders `BillingLedger`,
  finds the M-Pesa button on an unpaid invoice, opens the STK modal (phone pre-filled), dispatches
  the click that calls `initiateStkPush` with the exact invoice payload, and confirms paid invoices
  show **no** trigger.
- **695 tests / 62 files green**, `tsc --noEmit` exit 0, eslint 0 errors (14 pre-existing warnings
  in untouched files), `vite build` passes.

### 7.6 Docs

- `src/lib/api/billing.server.ts` `getInvoices` decrypts `lead_phone` (PII at rest) for the STK
  prompt — already documented per the deliverables contract; no DB contract change.

## Files Changed

- `src/lib/db.server.ts`: static-analyzable `import("postgres")`, new `pingDb()`.
- `server/routes/api/*.ts` (6 files): default method-dispatch exports.
- `src/__tests__/health-endpoint.test.ts`: mock `pingDb()`.
- `vite.config.ts`: client-env `external: ["postgres"]`.
- `src/hooks/use-theme.ts`, `src/routes/__root.tsx`: light theme default + meta.
- `src/routes/index.tsx`, `src/routes/services.tsx`, `src/components/site/HeroCarousel.tsx`:
  Lovable-aligned copy.
- `src/routes/index.tsx`, `src/routes/our-story.tsx`, `src/routes/resources.tsx`,
  `src/components/site/HeroCarousel.tsx`: branded local image imports (Part 5).
- `src/routes/__root.tsx`: og/twitter image → stable `/og/hero-clinic.jpg`.
- `public/og/hero-clinic.jpg`: new, stable social-share image.
- `src/styles.css`: elite dark token set, `--glass-border`, color-scheme, scrollbars, selection,
  focus ring, `.theme-transition`, dark `text-gradient` (Part 6).
- `src/hooks/use-theme.ts`: transient cross-fade class on toggle (Part 6).
- `src/components/**`, `src/routes/admin/**`: 40+ `dark:text-*-400` status variants + gray→token
  swaps + dashboard header polish (Part 6).
- `src/lib/api/mpesa.server.ts`: server-side STK push init + callback (pre-existing, Part 0).
- `src/components/finance/BillingLedger.tsx`: `StkPrompt` modal + M-Pesa trigger on unpaid rows
  (Part 7.2).
- `src/lib/api/dispatch.server.ts`: `dispatchWithBreaker` + breaker-wired `dispatchLeadMessage` +
  ledger (Part 7.3/7.4).
- `src/lib/queue.server.ts`: `dispatchNotification` via breaker + ledger, dynamic imports
  (Part 7.3/7.4).
- `vitest.config.ts`: test include now `**/*.test.{ts,tsx}` (Part 7.5).
- `src/__tests__/dispatch-breaker-wiring.test.ts`, `src/__tests__/billing-stk-ui.test.tsx`: new
  tests (Part 7.5); `src/__tests__/dispatch.test.ts` extended with breaker coverage.

## Commits

1. `fix(deploy)`: default method-dispatch exports for all API routes (Invalid lazy handler fix)
2. `fix(health)`: active DB ping in `/api/health`
3. `fix(deploy)`: bundle postgres driver into serverless output
4. `fix(ui)`: align Vercel production site with the Lovable deploy — holistic copy + light theme
5. `fix(ui)`: replace Unsplash stock photos with local branded assets — full Lovable image parity
6. `feat(ui)`: elite "Warm Midnight Forest" dark theme + full dark-mode parity
7. `feat(payments)`: M-Pesa STK push trigger in the billing ledger (StkPrompt modal + process)
8. `feat(notifications)`: breakered dispatch on live paths — dispatchWithBreaker + honest SMS
9. `feat(notifications)`: message-ledger audit trail on dispatch and queue worker paths
10. `test(payments)`: STK UI trigger render test + breaker/ledger wiring tests (695 green)

## Status

- [x] DB connected in production (`/api/health` healthy)
- [x] All API routes functional (health, webhooks, calendar, SSE, cron)
- [x] Org + admin seeded; login verified in production
- [x] Vercel UI matches Lovable (copy + theme)
- [x] Vercel UI matches Lovable (branded images — no Unsplash)
- [x] Elite dark mode designed + dark-mode parity across all components
- [x] WhatsApp credentialed on Vercel; live send delivered with real token
- [x] M-Pesa STK push triggerable from the billing ledger UI
- [x] Circuit-breaker dispatch + message ledger wired on both live dispatch paths
- [x] 695 tests green, tsc 0, eslint 0 errors, build passes

## Owner Follow-ups

- Convert the short-lived WhatsApp token to a **permanent system-user token** before
  **2026-08-27T17:00:00 UTC**; verify the production clinic WhatsApp number (`NOT_VERIFIED` today).
- Tier 2 backlog ready: 3-mode theme toggle (Light/Dark/System) and the rest of the pilot milestone.