# Kay's Wellness Centre — OS Access + End-to-End Screen Tour

> Who this is for: the clinic owner/operator ("Kay"), and whoever operates the
> deployment. This is not a marketing read — it is the honest operating manual
> for what you can access, what you will see on each screen, and what still needs
> owner-held credentials before every screen behaves "live".
>
> Last verified against `src/` on Sprint 42.

---

## 1. Accessing the OS

### 1.1 Where it runs

| Environment | How to run | Notes |
|-------------|-----------|-------|
| Local dev | `npm run dev` | Vite dev server, real Postgres (or `KWC_E2E_DB=1` for the embedded PGlite smoke build) |
| E2E smoke | `npm run build:e2e && npm run e2e` | Production build, PGlite swap, Playwright (`tests/e2e/revenue-path.spec.ts`) |
| Production | Vercel (deploy needs Supabase `DATABASE_URL` + owner login) | Not yet live — owner-held blocker |

`KWC_E2E_DB=1` is a **test-only** switch. Never set it in production.

### 1.2 Signing in

- URL: `<origin>/admin/login`
- Seeded default admin (first login, auto-created on request):
  - email `admin@kayswellnesscentre.org`
  - password `admin0726`  (`env.server.ts:7-8`)
- **Change the password before going live.** `DEFAULT_ADMIN_PASSWORD`
  defaults to a known value; the production env guard throws at boot if
  `SESSION_SECRET` is still the default (`env-production-guard.test.ts`).
- Passwords: PBKDF2 (100k iterations, SHA-512, 16-byte salt) — `auth.server.ts`.
- Session: HMAC-signed `kwc_session` cookie, 24 h expiry, `httpOnly` +
  `sameSite:'lax'`. Every tenant-scoped server call re-verifies the session row
  (`requireOrg()` → `isSessionActive()`), so logging out revokes the token
  app-wide, not just on the screen you logged out of.

### 1.3 Roles and tiers

- **Roles** (`permissions.server.ts`): `super_admin` (100) > `admin` (50) >
  `staff` (10). Finance, delete, data import, and diagnostics are owner/admin or
  `super_admin` only.
- **Subscription tiers** (`subscriptions.server.ts`): `starter` / `growth` /
  `enterprise`. Data export/import on `/admin/settings/data` is gated behind
  `bulk_operations` (Growth) via `SubscriptionGuard`; locked users see a paywall
  card whose upgrade button is a real `mailto:` to `ceo@kayswellnesscentre.org`
  (no fake checkout).

### 1.4 Seeded data & default org

- Single org in practice: slug `kays-wellness` (`contact.server.ts:33`). The
  schema and every scoped query stay multi-tenant (`organization_id` boundary).
- Data is encrypted at rest for lead `name`/`phone`/`email` (ADR-015) with
  per-org PBKDF2-derived AES-256-GCM keys.

---

## 2. End-to-end screen tour

Walk these in order — that is the whole money path.

### 2.1 Public site — the intake funnel

**`/` Home** — hero, specialties, the 1-hour foundational consultation
**booking widget** (`BookingWidget.tsx`). The widget has 3 steps:
1. pick a service (Continue stays disabled until you pick one),
2. pick a channel (In-Person / Telehealth / Home Visit),
3. enter name + email + language, submit → success screen.

> Booking behaviour, honestly: the widget writes a lead only when the visitor's
> browser already holds a valid session cookie (`requireOrg()`); a fully anonymous
> visitor's packet is parked in `localStorage` and retried on the next signed-in
> session (`kwc_pending_submissions`).

**`/contact`** — "Send us a message" writes a real tenant-scoped lead regardless
of cookie: slug resolution → rate limit (5/min per email) → PII encryption →
`lead:acquired` on the live bus → staff notification enqueued. Every failure is
surfaced to the visitor (nothing silently dropped).

**`/services`, `/resources`, `/our-story`, `/terms`, `/privacy-policy`** —
marketing pages; privacy page exposes the real contact mailbox.

### 2.2 Admin login

**`/admin/login`** — real server-side auth. Unauthenticated visits to any
`/admin/*` route redirect here. (The old client-side `"0726"` PasscodeGate is
gone — removed Sprint 42; only server-side RBAC + session revocation gate the
admin app now.)

### 2.3 Operations Dashboard

**`/admin/dashboard`** — "at a glance" KPIs:
- total leads / this week / this month, conversion velocity (30-day avg),
  triage→schedule rate, no-show %, revenue at risk;
- finance block only for owner/admin: accounts receivable, MRR this month,
  collection rate, top resource;
- pipeline distribution bar, revenue-per-resource, lead activity breakdown.

**Live telemetry is real, not just a badge**: the page subscribes to the SSE
stream and silently refetches when lead/scheduling/billing events arrive
(`lead:acquired`, `lead:stage_changed`, `lead:updated`, `invoice:created`,
`payment:recorded`, `stk_push:paid`, `reconciliation:matched`). Network status is
shown in the header.

### 2.4 Triage Console (the day job)

**`/admin/triage`** — the **pipeline board** (`PIPELINE_STAGES`: New / Triage Pending /
Scheduled / Checked-In / Dropped), drag & drop stage moves, inline priority
change, per-lead **Message** (follow-up) and **Confirm** (for scheduled leads),
activity timeline, and live lead events streamed over SSE. Terminal moves
(Checked-In / Dropped) require an explicit confirm dialog. Converting a
check-in generates the invoice automatically.

### 2.5 Finance

**`/admin/finance`** — invoice ledger (sequential `INV-` numbers), payments,
M-Pesa STK push per unpaid invoice (Daraja; owner-held credentials), and
reconciliation matching.

**`/admin/settings/billing`** — invoice/pay records, owner-only.

### 2.6 Settings

- **`/admin/settings/data`** — export CSV datasets (leads / invoices /
  interactions / audit trail) and bulk-import leads. Gated by `bulk_operations`
  (Growth tier) — on Starter you see the lock card instead.
- **`/admin/settings/operations`** — clinic configuration (availability,
  resources, automation).
- **`/admin/settings/developer`** — developer/API settings.
- **`/admin/settings/billing`** — see §2.5.

### 2.7 Diagnostics

- **`/admin/diagnostics`** — queue diagnostics, forcing retries of failed queue
  items (`getQueueTelemetry`, `forceRetryQueueItems`) — `super_admin` only, and
  hardened by the app-wide session-revocation check.
- **`/admin/system/diagnostics`** — system-level diagnostics. This route is
  intentionally reachable **without** a role check (asserted by
  `tenant-isolation-p0.test.ts`); it reports non-sensitive environment status.

---

## 3. Automation & owner paging (what runs without you)

- **Automation orchestrator** (`automation-orchestrator.ts`): walks every org,
  advances leads (untouched → triaged, stalled re-engagement, failed retries),
  and sends WhatsApp via `dispatchWithBreaker` — a circuit breaker, so repeated
  provider failures trip a timeout instead of hammering the API.
- **Heartbeat** (`heartbeat.ts`): every 5 min steps the real booking pipeline
  (book → verify → cancel) and pages the owner if it's broken.
- **Owner alerts** (`owner-alerts.server.ts`): deduped paging for automation
  failures, heartbeat breaks, and **(Sprint 42) failed M-Pesa STK callbacks** —
  a non-successful Daraja callback now pages the owner with the request id.
- Both cron endpoints require `Bearer CRON_SECRET`; in production an unconfigured
  `CRON_SECRET` makes the endpoint refuse to run (fail closed) rather than trust
  a dev secret. Vercel cron schedule: heartbeat `*/5 * * * *`,
  automation-orchestrator `*/15 * * * *` (`vercel.json`).

---

## 4. When it is NOT live (honest status)

These paths are **unit-tested but not yet live** because the credentials are
owner-held:

| Capability | What's missing | What happens instead |
|-----------|----------------|----------------------|
| WhatsApp delivery | `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` | In production `sendWhatsApp` returns `{success:false, provider:"unconfigured"}` — logged, breaker records failure, owner paged. No fake success. |
| M-Pesa real push | Daraja sandbox/live credentials | STK flow tested in unit tests; callbacks that fail page the owner. |
| Postgres / Vercel | Supabase DB password + owner login | App runs locally / E2E on PGlite; `DATABASE_URL` unset locally until provided. |
| Google Business Profile | Owner API consent | Descoped from pilot; sentiment/NPS classification ships instead. |

Until the WhatsApp token is set, message sends are **honestly reported as
failed** — the system never claims a message went out when it didn't.

---

## 5. Suggested first 30 minutes as operator

1. `npm run dev`, sign in with the seeded admin.
2. Open `/contact`, submit a test message → watch it appear on`/admin/triage`
   (and the dashboard counter bump) via the live SSE bus.
3. Open `/admin/triage` in a second tab → send a test booking from `/` → drag it
   to Scheduled → confirm message.
4. Open `/admin/diagnostics` to verify the queue is draining.
5. Set `WHATSAPP_TOKEN`/`WHATSAPP_PHONE_NUMBER_ID`/`CRON_SECRET`/Supabase
   `DATABASE_URL` to make the live paths real; then walk §2 end-to-end again.

---

*Companion docs: `docs/current-state.md`, `docs/architecture.md`,
`docs/release-readiness.md`, `docs/evidence/2026-08-28_*`.*