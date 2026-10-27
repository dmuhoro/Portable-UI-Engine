# Current State — Kay's Wellness Centre

> Orientation doc. Read this **and** `docs/architecture.md` before starting any task
> (AGENTS.md rule 6). Anything marked **ASPIRATIONAL** below is not yet real on the live
> path — do not build on top of it silently.
>
> Last verified against `src/` on Sprint 44.

---

## 1. What this product is

A **marketing site + clinic operating system** in one TanStack Start app. The public site
(`/`, `/services`, `/contact`, `/register`, …) generates **leads**; the admin app
(`/admin/*`) runs the clinic: a 6-stage **pipeline board** (new → contacted → scheduled →
checked_in → converted → lost), **invoicing/payments** (`INV-` / `KWC-` sequential numbers),
**scheduling**, WhatsApp **notification queue**, **M-Pesa reconciliation + STK push**,
retention **automation**, and an **SSE real-time bus** for live admin updates.

Today the app is single-tenant in practice (default org `kays-wellness` is auto-seeded on
first login), but the schema, authorization, and queries are fully **multi-tenant**
(`organization_id` is an explicit, non-optional boundary on every scoped query).

## 2. Where the live data path starts

- **Booking widget** (`src/components/site/BookingWidget.tsx` → `useClinicOSSubmit` →
  `submitLead`): a lead is written to `clinic_leads` **only when the visitor's browser holds
  a valid session cookie** — `submitLead` calls `requireOrg()`, which throws `TenantError`
  for a genuinely anonymous visitor. In the E2E smoke the staff member is signed in, so the
  widget-created lead always lands; for a true public visitor with no cookie the packet is
  parked in `localStorage` (`kwc_pending_submissions`) and retried on the next session.
- **"Send us a message" form** (`src/routes/contact.tsx` → `submitContactMessage` in
  `src/lib/api/contact.server.ts`): **writes a real tenant-scoped lead** since Sprint 41.
  Anonymous visitors don't need a cookie — the fn resolves the public org by slug
  (`PUBLIC_ORG_SLUG`, default `kays-wellness`), fails closed if missing, rate-limits per
  email (5/60s), encrypts `name`/`email` (ADR-015), and inserts `status='new'`,
  `channel='web_form'`, `service='Contact Message'` with the free-text message kept in
  `raw_payload`. It records a `lead_interactions` `new` row, publishes `lead:acquired`
  (live triage desk), audits `LEAD_INGESTED`, and enqueues the staff notification. Every
  non-success return is surfaced to the caller — nothing is silently dropped.
- **Marketing pipeline intake** (`src/lib/marketing/leads.server.ts` `ingestInboundLead`):
  writes `status='new'` + records a `lead_interactions` row, publishes `lead:acquired` for
  the SSE bus, audits `LEAD_INGESTED`, and stores the payload (including any free-text
  message) in `raw_payload`. Correction notice: it stores PII **plaintext**; the ADR-015
  encrypted paths are `submitLead`/`encryptLeadPII` and the public `submitContactMessage`
  intake (see §4).

## 3. Getting it running and proving it green

| Command | Meaning |
|---------|---------|
| `npm run dev` | Vite dev server |
| `npm test` | full Vitest unit suite (756 tests / 74 files as of Sprint 43) |
| `npx tsc --noEmit` | typecheck — must be exit 0 |
| `npm run build` | production build (Nitro `vercel` preset) |
| `npm run build:e2e && npm run e2e` | Playwright smoke against the **production build** (5 tests, `tests/e2e/revenue-path.spec.ts`) with Postgres swapped for embedded PGlite (`KWC_E2E_DB=1`) |
| `npx eslint <files>` | lint touched files |

`KWC_E2E_DB=1` switches the Vite root alias from `db.server` → `db.e2e.server.ts` (PGlite,
data dir `.kwc-e2e-pglite/`). **Never set it in production**; the prod preset stays on real
Postgres. `db.schema.server.ts` holds the single source-of-truth DDL shared by both.

## 4. Security posture (what is real, not aspirational)

- **PII encryption (ADR-015):** lead `name`/`phone`/`email` are AES-256-GCM encrypted on
  write (`encryptLeadPII`) and decrypted on read (`decryptLeadRows`, billing ledger). Keys
  are per-org, versioned, PBKDF2-derived (`org_api_keys`/`encryption_keys`). Legacy plaintext
  rows pass through read paths unchanged. **Counter-example to know:** `ingestInboundLead`
  writes plaintext (see §2) — a real inconsistency, not a solved one.
- **Tenant isolation:** every mutation binds `organization_id`; 22 adversarial tests prove the
  5 P0 SQL-leak fixes (`tenant-isolation-p0.test.ts`). No automatic scoping middleware —
  each query names the column explicitly.
- **RBAC:** `requireRole()` gates on `super_admin`(100) > `admin`(50) > `staff`(10). Finance,
  delete, bulk-import, and diagnostics are owner/admin or `SUPER_ADMIN`-only
  (`rbac-completeness.test.ts`).
- **Rate limits:** login (5/60s), `submitLead` (30/60s per org), WhatsApp dispatch (20/60s),
  reconciliation (10/60s), all via `checkRateLimit` (in-process Map).
- **Session:** HMAC-signed `kwc_session` cookie, 24 h expiry, `httpOnly` + `sameSite:'lax'`.
  **Revocation is enforced app-wide (Sprint 42):** every tenant-scoped call — including every
  `requireRole()` gate — re-verifies the `user_sessions` row via `requireOrg()` →
  `isSessionActive()` (fail closed on DB hiccup); logout removes the row. Dead client-side
  `PasscodeGate` deleted; only server RBAC + revocation gate the admin app.
  `SESSION_SECRET` and default-env guards throw at boot in production (`env.server.ts`,
  `env-production-guard.test.ts`).
- **WhatsApp honesty (Sprint 42):** automation messages route through `dispatchWithBreaker`
  and never double-send via the notification queue; with no provider configured in production,
  sends are **honestly reported as failed** (`provider:"unconfigured"`), the breaker records
  the failure, and the owner is paged — no fake successes.
- **M-Pesa paging (Sprint 42):** a failed STK callback pages the owner (deduped).
- **Cron guards (Sprint 42):** production cron endpoints refuse to run without `CRON_SECRET`
  (503, fail closed); automation orchestrator scheduled `*/15 * * * *` on Vercel.
- **Committed production fixes:** converted check-ins generate invoices (`mutateAsync` in
  `PipelineBoard.tsx`); billing ledger decrypts `lead_name` + `lead_phone`.

## 5. Known gaps and blockers (real, current)

See `docs/architecture.md` §9 for the source-verified gap table (open: `config.server.ts`
Zod bypass, no CSRF headers on server fns, `processQueue` unscoped default branch mitigated
at the call site, `registerOrganization` idempotency race) and `docs/release-readiness.md`
for the literal go/no-go blocker list.

## 6. **ASPIRATIONAL** — explicitly not yet real on the live path

- **WhatsApp delivery in production** — requires live `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID`; only unit-tested so far. (Sprint 42: unconfigured production sends now **fail closed and honestly**, so no message is ever claimed sent.)
- **STK push against Daraja sandbox** — callback flow is tested; live credentials owner-held.
- **Subscription paywall UI** — metering/quota logic tested; gating wired into `/admin/settings/data` (Sprint 42); the modal appearance/flow still needs one manual browser check.
- **Live deployment** — Vercel deploy needs the Supabase DB password + owner login. (Deploy checklist: set `SESSION_SECRET`, `CRON_SECRET`, `WHATSAPP_TOKEN`, `MPESA_*`, change default admin password.)
- **Google review auto-submission** — descoped from pilot (sentiment/NPS classification ships instead).

> **Closed by Sprint 44:**
> - **M-Pesa reconciliation against a real transaction** — `mpesa-csv-staging.test.ts` parses real Safaricom Daraja CSV format and reconciles against test invoices; idempotent replay verified.
> - **Server RBAC on mutation paths** — `submitLead`, `updateLead`, `deleteLead`, `bookSlot`, `cancelSlot`, `reserveSlot`, `scheduleAppointment`, `dispatchLeadMessage` now `requireRole(SUPER_ADMIN, CLINIC_OWNER)`; staff reads only.
> - **PII encryption on message ledger** — `from_address`/`to_address` encrypted at rest; decrypted on read.
> - **Demo seed data** — `npm run db:seed-demo` populates 15 leads, 5 invoices (2 paid), 3 messages, 2 reviews for Dr. Jackie walkthrough.
> - **Owner→Staff invite** — `auth.server.ts:inviteStaff` + `operations.tsx` modal; creates `staff` user with temp password; role enforced server-side.

## 7. Doc index

- `docs/architecture.md` — authoritative system map (stack, auth, tenant isolation, schema, routes, gaps).
- `docs/db-contracts.md` — table semantics + tenant-scoping contract. **Must be updated in the same change as any tenant-scoping edit.**
- `docs/release-readiness.md` — go/no-go checklist (every row is PASS/FAIL with a citation).
- `docs/kwc-os-access-guide.md` — operator access instructions + end-to-end screen tour (Sprint 42).
- `docs/sprints/` — per-sprint change logs; newest is `sprint-43-verification-and-production-golive-readiness.md`.
- `docs/evidence/` — run logs backing the checklist rows.
- `docs/adr/` — formal ADRs (013–016); older decisions in `docs/decisions.md`.