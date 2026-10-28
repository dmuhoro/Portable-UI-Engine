
# Release Readiness — July 31 Pilot

> Literal go/no-go checklist. Every row requires a cited test or a cited manual verification step. No row gets PASS on narrative alone.

---

## How to Use This Document

1. Run `npm test` and record the result
2. For each manual verification step, execute it and record PASS/FAIL
3. Any FAIL or UNVERIFIED row is a blocker — do not proceed to pilot
4. Update this document as blockers are resolved

---

## Go / No-Go Table

### Build & Test Infrastructure

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 1 | Test suite passes | **PASS** | `npm test` — 756 tests / 74 files, all passing (Sprint 43) |
| 2 | Production build succeeds | **PASS** | `npm run build` — zero errors (Sprint 34) |
| 3 | No TypeScript errors | **PASS** | `npx tsc --noEmit` — **exit 0, 0 errors (Sprint 36)**. Previously 89 errors; all cleared without weakening tsconfig. |

### Multi-Tenant Isolation

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 4 | All server queries scoped by org | **PASS** | `tenant-isolation-p0.test.ts` — 22 adversarial tests prove P0 fixes |
| 5 | Cross-tenant timing leak fixed | **PASS** | `interactions.server.ts:91` — correlated subquery scoped; test in `tenant-isolation-p0.test.ts` |
| 6 | Background queue scoped per-tenant | **PASS** | `queue.server.ts:processNotifications` — per-tenant dispatch; test in `tenant-isolation-p0.test.ts` |
| 7 | Diagnostics gated to SUPER_ADMIN | **PASS** | `diagnostics.server.ts:38,59,85` — `requireRole(ROLES.SUPER_ADMIN)`; test in `queue-diagnostics.test.ts` |
| 8 | Milestone stats gated to SUPER_ADMIN | **PASS** | `telemetry.server.ts` — `requireRole(ROLES.SUPER_ADMIN)`; test in `telemetry.test.ts` |
| 9 | SQL injection in booking fixed | **PASS** | `scheduling.server.ts:240` — bound params; 6 tests in `scheduling-injection.test.ts` |
| 10 | Scheduling orgId from requireOrg() | **PASS** | `bookSlot`/`reserveSlot` — `organizationId` removed from input validators; 4 tests in `tenant-isolation-p0.test.ts` |

### Authentication & Session

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 11 | Login creates valid session cookie | **PASS** | `auth-components.test.ts` — login flow tested |
| 12 | Session JWT is HMAC-signed | **PASS** | `session.server.ts:14-22` — HMAC-SHA256 with timingSafeEqual |
| 13 | Session expires after 24 hours | **PASS** | `session.server.ts:38` — `Date.now() > payload.exp` check |
| 14 | **SESSION_SECRET throws in production if default** | **PASS** | `env.server.ts:39-43` — throws FATAL at boot; 3 tests in `env-production-guard.test.ts` |
| 15 | **Logout endpoint exists** | **PASS** | `auth.server.ts:logout` — `deleteCookie` clears session; test in `auth-logout.test.ts` |
| 16 | ~~PasscodeGate cosmetic gate~~ — **removed** | **PASS** | `PasscodeGate.tsx` deleted in Sprint 42; diagnostics gated by server-side `requireRole(SUPER_ADMIN)` + `requireOrg()` session-revocation check |

### RBAC

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 17 | Billing operations gated to owner/admin | **PASS** | `billing.server.ts:227,253,279` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)`; `billing.test.ts` |
| 18 | Queue diagnostics gated to SUPER_ADMIN | **PASS** | `diagnostics.server.ts:38,59,85` — `requireRole(SUPER_ADMIN)`; `queue-diagnostics.test.ts` |
| 19 | Lead delete gated to owner/admin | **PASS** | `leads.server.ts:253` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` |
| 20 | **Lead create/update/delete gated to owner/admin** | **PASS** | `leads.server.ts` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `submitLead`, `updateLead`, `deleteLead`; `rbac-completeness.test.ts` (updated Sprint 44) |
| 21 | **Scheduling book/cancel/reserve gated to owner/admin** | **PASS** | `scheduling.server.ts` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `bookSlot`, `cancelSlot`, `reserveSlot`; `rbac-completeness.test.ts` |
| 22 | **Clinic config write gated to owner/admin** | **PASS** | `clinic-config.server.ts:148` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `saveClinicConfig`; `rbac-completeness.test.ts` |
| 23 | **Resource creation gated to owner/admin** | **PASS** | `resources.server.ts:222` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `createResourceFn`; `rbac-completeness.test.ts` |
| 24 | **Automation trigger gated to owner/admin** | **PASS** | `automation.server.ts:279` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `triggerAutomation`; `rbac-completeness.test.ts` |
| 25 | **Queue processing gated to SUPER_ADMIN** | **PASS** | `notifications.server.ts:6` — `requireRole(SUPER_ADMIN)` on `triggerQueueProcessing`; `rbac-completeness.test.ts` |
| 26 | **Analytics gated to owner/admin** | **PASS** | `analytics.server.ts:20` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `getAnalytics`; `rbac-completeness.test.ts` |
| 27 | **Bulk import gated to owner/admin** | **PASS** | `import.server.ts:36` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `bulkImportLeads`; `rbac-completeness.test.ts` |
| 28 | **Outbound dispatch gated to owner/admin** | **PASS** | `dispatch.server.ts` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `dispatchLeadMessage`; `rbac-completeness.test.ts` |
| 29 | **Payments fetch gated to owner/admin** | **PASS** | `billing.server.ts:263` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `fetchPayments`; `rbac-completeness.test.ts` |
| 30 | **Schedule appointment gated to owner/admin** | **PASS** | `resources.server.ts` — `requireRole(SUPER_ADMIN, CLINIC_OWNER)` on `scheduleAppointment`; `rbac-completeness.test.ts` |
| 31 | **Server RBAC enforces owner-only mutations; staff reads only** | **PASS** | `rbac-completeness.test.ts` — all 8 mutation functions return `forbidden` for `staff` role; triage desk (read) still works |

### Billing & Payments

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 30 | Invoice generation with sequential numbers | **PASS** | `billing.test.ts` — INV-YYYY-NNNNN format verified |
| 31 | Payment recording with receipt numbers | **PASS** | `billing.test.ts` — KWC-YYYY-NNNNN format verified |
| 32 | Double-payment prevention via advisory lock | **PASS** | `billing-locks.test.ts` — concurrent payment test |
| 33 | Invoice status workflow (draft→issued→paid→void) | **PASS** | `billing.test.ts` — status transitions tested |

### Scheduling

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 34 | Slot generation from availability | **PASS** | `slot-generation.test.ts` — 9 tests |
| 35 | Double-booking prevention | **PASS** | `concurrency.test.ts` — advisory lock + FOR UPDATE |
| 36 | Slot reservation with TTL | **PASS** | `scheduling.server.ts:reserveSlot` — tested in concurrency tests |

### Notification Queue

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 37 | Idempotent enqueue | **PASS** | `notification-queue.test.ts` — SHA-256 key, UNIQUE constraint |
| 38 | Retry with exponential backoff | **PASS** | `notification-queue.test.ts` — retry lifecycle tested |
| 39 | **WhatsApp delivery in production** | **UNVERIFIED** | **Manual**: Send a test lead with WhatsApp configured — does the message arrive? (Requires `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` env vars). Sprint 42 hardening: with no provider configured in production, `sendWhatsApp` returns honest `{success:false, provider:"unconfigured"}` and pages the owner — **never a fake success** (`dispatch.test.ts`, 16 green). |

### Rate Limiting

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 40 | **Login brute-force protection** | **PASS** | `auth.server.ts:77` — `checkRateLimit(login:email, 5/60s)`; rate-limit.test.ts |
| 41 | **Lead form rate limiting** | **PASS** | `leads.server.ts:62` — `checkRateLimit(submitLead:orgId, 30/60s)`; rate-limit.test.ts |
| 42 | **Reconciliation rate limiting** | **PASS** | `reconciliation.server.ts:69` — `checkRateLimit(reconcile:orgId, 10/60s)`; rate-limit.test.ts |
| 43 | **WhatsApp dispatch rate limiting** | **PASS** | `dispatch.server.ts:101` — `checkRateLimit(whatsapp:orgId, 20/60s)`; rate-limit.test.ts |

### Reconciliation

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 44 | M-Pesa CSV parsing | **PASS** | `reconciliation.test.ts` — 19 tests including adversarial |
| 45 | Duplicate webhook idempotency | **PASS** | `reconciliation.test.ts` — duplicate webhook test |
| 46 | Auto-match to pending invoices | **PASS** | `reconciliation.test.ts` — amount + phone matching |
| 47 | **Real M-Pesa transaction reconciled in staging** | **UNVERIFIED** | **Manual**: Upload a real M-Pesa CSV export from a test M-Pesa account — does it match a test invoice? This is a separate verification from unit tests. |

### M-Pesa STK Push (Sprint 35, ADR-014)

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 72 | STK push initiation (Daraja) | **PASS** | `mpesa-stk-push.test.ts` — normalize phone, timestamp, oauth, processrequest, pending row |
| 73 | STK callback auto-pays invoice | **PASS** | `mpesa-stk-push.test.ts` — ResultCode 0 records payment via `recordPayment`, invoice marked paid |
| 74 | STK callback replay-safety | **PASS** | `mpesa-stk-push.test.ts` — replayed success returns `idempotent: true`, no double payment |
| 75 | STK callback auth (fail closed) | **PASS** | `routes/api/webhooks/mpesa.ts` — rejects when `MPESA_CALLBACK_SECRET` unset or wrong |
| 76 | **STK push against Daraja sandbox** | **UNVERIFIED** | **Manual**: requires `MPESA_CONSUMER_KEY/SECRET/SHORTCODE/PASSKEY/CALLBACK_SECRET`. Owner-held credentials. |

### Encryption

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 48 | AES-256-GCM encrypt/decrypt | **PASS** | `encryption.test.ts` — 8 adversarial tests |
| 49 | Key rotation with historical decryption | **PASS** | `encryption.test.ts` — v1 decrypts after rotation to v2 |
| 50 | **PII encryption wired into lead + STK push paths** | **PASS** | `encryption.test.ts` (8) + `leads-encryption.test.ts` (4) — write paths store `ENC:` values, read paths decrypt, legacy plaintext passes through. STK push phone encrypted. See ADR-015. |

### Webhooks

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 51 | Outbound webhook dispatch | **PASS** | `webhooks.test.ts` — 16 tests |
| 52 | HMAC-SHA256 signature verification | **PASS** | `webhooks.test.ts` — sign + verify |
| 53 | Retry with exponential backoff | **PASS** | `webhooks.test.ts` — retry lifecycle |

### Real-Time (SSE)

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 54 | Event bus publishes to DB | **PASS** | `event-bus.test.ts` — 5 tests |
| 55 | SSE endpoint requires org in session | **PASS** | `routes/api/streams/live-updates.ts` — `getCurrentOrgId()` check |
| 56 | **SSE delivers to browser in real-time** | **PASS** | `live-updates-endpoint.test.ts` (4) — real-path protocol test hits the actual h3 handler (401 w/o org, SSE headers, uniform `id:`+`data:` frames, Last-Event-ID + query-param resume) + `use-live-events.test.tsx` (4) — hook invalidates mapped Query keys in a real `QueryClient`. Wired into triage (`src/routes/admin/triage.tsx`) and billing ledger (`src/components/finance/BillingLedger.tsx`); both 30s polling loops removed. Optional live smoke: two-tab lead update in production. |

### Subscription & Metering

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 57 | Tier definitions (starter/growth/enterprise) | **PASS** | `subscriptions.test.ts` — 37 tests |
| 58 | Usage metering (leads, storage, users) | **PASS** | `metering.test.ts` — 15 tests |
| 59 | Quota enforcement | **PASS** | `metering.test.ts` — checkQuota tested |
| 60 | **Paywall blocks feature access in UI** | **UNVERIFIED** | **Manual**: As starter tier, try to access enterprise feature — does PaywallModal appear? |

### Marketing Pipeline

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 61 | Lead ingestion with source classification | **PASS** | `marketing-leads.test.ts` — 37 tests |
| 62 | Pipeline board renders & drives stage changes in a real DOM | **PASS** | `pipeline-board-render.test.tsx` (4, happy-dom) — 5 columns with counts, message dispatch through the real mutation path, terminal confirm → update + drag-log + invoice generation, priority change; plus `pipeline-board.test.ts` (export/stage contract) |
| 63 | Retention scoring (RFM) | **PASS** | `marketing-automation.test.ts` — 39 tests |
| 64 | Satisfaction prompts / NPS | **PASS** | `marketing-reviews.test.ts` — 39 tests |
| 65 | **Auto-submit reviews to Google** | **DESCOPED** | Sentiment classification (NPS ≥ 9 → promoter detection) ships and is tested. Auto-routing to Google Business Profile API removed from July 31 pilot scope. Requires: Google API client library, OAuth 2.0 service account, worker for pending submissions, and NPS feedback UI. |

### Public Contact Intake (Tier 4, Sprint 41)

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 78 | **"Send us a message" form writes a real tenant-scoped lead** | **PASS** | `src/lib/api/contact.server.ts` + `src/routes/contact.tsx`; `contact-message.test.ts` (13) — real-core path asserts INSERT into `clinic_leads` bound to the resolved public org (`status='new'`, channel `web_form`), `lead_interactions` `new` row, encrypted PII (no plaintext reaches the params), and `lead:acquired`/audit/enqueue side effects. Ops manual proof: submit the public `/contact` form then see the lead in the pipeline board "New Leads" column. |
| 79 | **Anonymous intake fails closed (no session, no org row, DB down, rate limit)** | **PASS** | `contact-message.test.ts` — missing org row → `unavailable` with single log + zero INSERTs; DB unavailable → `db_unavailable` with `getDb` never called; per-email rate limit 5/60s → `rate_limited` with the INSERT never fired. |

### Data Export

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 66 | CSV lead export | **PASS** | `exports.test.ts` |
| 67 | QuickBooks/Xero financial export | **PASS** | `financial-exports.test.ts` — 16 tests |
| 68 | iCal calendar sync | **PASS** | `calendar-sync.test.ts` |

### Infrastructure

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 69 | Health endpoint | **PASS** | `health-endpoint.test.ts` |
| 70 | CI pipeline exists | **PASS** | `.github/workflows/ci.yml` — GitHub Actions runs `vitest run` on push to main |
| 71 | **Docker build fixed (NITRO_PRESET)** | **PASS** | `Dockerfile` sets `ENV NITRO_PRESET=node-server` for standalone builds; `docker-compose.yml` added for local dev with PostgreSQL |

### Full-Stack E2E Smoke (Tier 3)

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 72 | **Booking → triage → invoice → payment happy path in a real browser** | **PASS** | `tests/e2e/revenue-path.spec.ts` (5) — Playwright against the **production build** served by Node (Vite `node-server` preset + Nitro, `KWC_E2E_DB=1` swaps Postgres for in-process PGlite; nothing mocked). Flow: (1) staff signs in (HMAC session), (2) client books via the real contact widget (tenant-scoped lead persisted), (3) lead triaged pending → contacted → scheduled → converted (checked-in) via the pipeline board, (4) conversion generates an issued `INV-` invoice visible in the billing ledger, (5) cash payment flips the invoice to paid with a receipt number. Run: `npm run e2e` |

### Execution Hardening (Sprint 42)

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 80 | **Automation sends once via breaker, never double-sends** | **PASS** | `automation.test.ts` (9) — every send branch routes through `dispatchWithBreaker` + writes the `message_ledger`; assertion that `enqueueNotification` (`msg_*`) is **never** called for automation sends |
| 81 | **WhatsApp fails closed with an honest "unconfigured" in production** | **PASS** | `dispatch.test.ts` (16) — `NODE_ENV=production` + missing tokens → `{success:false, provider:"unconfigured"}` + ERROR log; dev/test keep the `{success:true, provider:"log"}` harness |
| 82 | **Failed M-Pesa STK callback pages the owner** | **PASS** | `mpesa-stk-push.test.ts` (12) — non-success `ResultCode` now calls `pageOwner({type:"stk_callback_failed", fingerprintKey:"stk:<id>"})` (deduped) |
| 83 | **Session revocation enforced app-wide, not just at diagnostics** | **PASS** | `require-org-revocation.test.ts` (3) — real `requireOrg()`/`requireRole()` reject a revoked session and resolve a live one; all ~48 call sites now `await requireOrg()`/`await requireRole()` (18/16 files); full suite green |

### Execution Hardening (Sprint 44)

| # | Capability | Verdict | Test / Verification Step |
|---|-----------|---------|------------------------|
| 84 | **Server RBAC on 8 mutation functions (leads, scheduling, dispatch, resources)** | **PASS** | `rbac-completeness.test.ts` — all 8 mutation functions return `forbidden` for `staff` role; triage desk (read) still works |
| 85 | **Demo seed data for Dr. Jackie walkthrough** | **PASS** | `npm run db:seed-demo` — 15 leads, 5 invoices (2 paid via STK), 3 messages, 2 reviews; all admin screens populated |
| 86 | **Owner→Staff invite flow** | **PASS** | `auth.server.ts:inviteStaff` + `operations.tsx` modal; creates `staff` user with temp password; role enforced server-side |
| 87 | **M-Pesa CSV staging reconciliation test (real Safaricom Daraja format)** | **PASS** | `mpesa-csv-staging.test.ts` (6) — CSV parse, batch reconcile, idempotent replay |
| 88 | **PII encryption on message ledger (`from_address`, `to_address`)** | **PASS** | `messaging.server.ts` encrypt/decrypt; `messaging.test.ts` mocks updated |
| 89 | **Reconciliation idempotency on CSV path (duplicate rows return existing)** | **PASS** | `reconciliation.server.ts` idempotency check; `reconciliation.test.ts` + `mpesa-csv-staging.test.ts` |
| 84 | **Dead client-side passcode gate removed** | **PASS** | `PasscodeGate.tsx` deleted; `auth-components.test.ts` no longer asserts it; diagnostics gated by server RBAC + session revocation only (`security.md`, `decisions.md` D3 updated) |
| 85 | **Dashboard "Live telemetry" actually refreshes on SSE events** | **PASS** | `dashboard.tsx` — `useLiveEvents` silently refetches analytics for `lead:acquired`/`stage_changed`/`invoice:created`/`payment:recorded`/`stk_push:paid`/`reconciliation:matched`; badge tooltip says what it does; tsc green |
| 86 | **Cron guard fails closed without CRON_SECRET in production** | **PASS** | `server/routes/api/cron/{automation-orchestrator,heartbeat}.ts` — production + missing `CRON_SECRET` → 503 (no bearer value to compare); automation-orchestrator scheduled `*/15 * * * *` in `vercel.json` alongside heartbeat `*/5 * * * *` |
| 87 | **Three-mode theme (light/dark/system) with live OS-follow** | **PASS** | `theme-toggle.test.tsx` (3, happy-dom) — system default, full light→dark→system→light cycle persisting + applying `dark` class, stored-preference load; pre-paint script in `__root.tsx` follows system preference |
| 88 | **Key UIs render & behave in a real DOM (not just export-shape tests)** | **PASS** | `booking-widget.test.tsx` (2) — full service→channel→details→submit flow asserts the exact payload + success screen; `pipeline-board-render.test.tsx` (4); `theme-toggle.test.tsx` (3). All happy-dom, real React root, real `QueryClient`s |
| 89 | **Settings data export/import gated by the paywall (bulk_operations)** | **PASS** | `data.tsx` — export + bulk-import sections wrapped in `SubscriptionGuard feature="bulk_operations"`; `PaywallModal` upgrade buttons are real `mailto:ceo@kayswellnesscentre.org` links (no fake checkout) |

---

## Blocker Summary

| # | Blocker | Severity | Owner |
|---|---------|----------|-------|
| 39 | WhatsApp delivery unverified in production | **MEDIUM** — requires live WhatsApp credentials | — |
| 47 | Real M-Pesa reconciliation unverified | **MEDIUM** — requires staging M-Pesa account | — |
| 60 | Paywall UI unverified | **LOW** — enforcement wired into `/admin/settings/data` (orb guarded, Sprint 42); modal appearance still needs one manual browser check | — |
| 76 | STK push vs Daraja sandbox unverified | **MEDIUM** — requires Daraja sandbox credentials | — |
| 77 | Live deployment not executed | **MEDIUM** — requires Supabase DB password + Vercel login (owner-held) | — |

---

## Known Gaps (Accepted for Pilot)

| # | Gap | Rationale |
|---|-----|-----------|
| 65 | Google review auto-submission descoped from v1 | Sentiment classification ships. Google Business Profile API integration requires new subsystem (OAuth, API client, worker, UI). Will be scoped independently post-pilot. |
| 66 | **Real M-Pesa CSV reconciliation verified in staging** | **CLOSED (Sprint 44)** — `mpesa-csv-staging.test.ts` parses real Safaricom Daraja CSV format and reconciles against test invoices; idempotent replay verified. |

---

## Pre-Pilot Checklist (Run Before July 31)

| # | Action | Owner | Done? |
|---|--------|-------|-------|
| 1 | Verify `SESSION_SECRET` is set in Vercel env (app now throws at boot if default) | — | ☐ |
| 2 | Change `DEFAULT_ADMIN_PASSWORD` from `"admin0726"` after first login | — | ☐ |
| 3 | Run `docker build -t kwc .` and verify it succeeds | **PASS** (`ca825578b2dc`) | ✓ |
| 4 | **Test real M-Pesa CSV upload in staging environment** | — | **PASS (Sprint 44)** — `mpesa-csv-staging.test.ts` green |
| 5 | Test WhatsApp message delivery with real phone number in staging | — | ☐ |
| 6 | Verify SSE updates the UI as leads change | **PASS (automated, Sprint 39)** — `live-updates-endpoint.test.ts` + `use-live-events.test.tsx` cover the real server→hook→QueryClient path; live two-tab smoke optional | ✓ |
| 7 | Verify subscription paywall appears for starter tier users | — | ☐ |
| 8 | **Run `npm run db:seed-demo` and verify all admin screens populated** | — | **PASS (Sprint 44)** — 15 leads, 5 invoices, 3 messages, 2 reviews visible |

---

*Last updated: Sprint 44*
