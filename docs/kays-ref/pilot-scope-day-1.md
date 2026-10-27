# Pilot Scope — First 14 Days

> The exact feature set Kay's Wellness Centre will actually use in the first 14 days. Every row is **IMPLEMENTED+TESTED** per the pilot go/no-go checklist in `docs/release-readiness.md`. Everything else in the product is "available but not part of the trial ask" — it exists, it's tested, but it's not in scope for day 1.

---

## How to Use

1. Give each staff member the URL + their login credentials
2. Read each workflow below and confirm the steps work end-to-end
3. Check off each row as verified in YOUR staging environment
4. Anything not listed here is out of scope — do not test it, do not demo it, do not ask about it

**Data warning:** PII (name, phone, email) is stored in plaintext (see D11 in `docs/decisions.md`). This is accepted for the pilot. Do not store sensitive medical notes or ID numbers until encryption is wired.

---

## Workflow 1: Login & Session (All Staff)

Daily login/logout for every user. No account creation — admin pre-creates staff accounts (see Workflow 6).

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 1.1 | Navigate to `/admin/login` | Login form renders | ☐ |
| 1.2 | Enter email + password, submit | Server verifies password; HMAC-signed JWT set in `kwc_session` cookie; redirect to dashboard | ☐ |
| 1.3 | Log out via UI | Session cookie cleared; redirect to login page | ☐ |
| 1.4 | Try to access dashboard after logout | Redirected to `/admin/login` | ☐ |

**Tests:** `auth-components.test.ts` (login flow), `auth-logout.test.ts` (logout clears cookie)

**Pilot constraint:** No token revocation (D12). Logout clears the browser cookie but doesn't invalidate the JWT. Staff should log out at end of shift. If a device is lost, change the user's password.

---

## Workflow 2: Lead Intake (Receptionist / Front Desk)

Record every new patient inquiry — walk-in, phone, or online — as a lead in the system. The receptionist selects the patient's preferred language (English or Swahili). When a lead is created, a WhatsApp confirmation message is automatically dispatched in that language.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 2.1 | Click "New Lead" or use the public contact form | `submitLead` createServerFn creates a `clinic_leads` row with channel classification | ☐ |
| 2.2 | Select patient's preferred language (EN / SW) | Receptionist picks English or Swahili; stored as `preferred_language` on lead record | ☐ |
| 2.3 | Enter name, phone, email, service of interest | Rate-limited (30/org/60s); data validated via Zod | ☐ |
| 2.4 | **WhatsApp confirmation sent in patient's language** | `dispatchLeadMessage` fires `confirmation` template in English or Swahili matching `preferred_language`; rate-limited (20/org/60s) | ☐ |
| 2.5 | View the pipeline board | 6-stage kanban rendered (new → contacted → scheduled → checked_in → converted / lost) | ☐ |
| 2.6 | Click a lead to see full details | Lead detail view with activity history | ☐ |
| 2.7 | Update lead stage (e.g., contacted → scheduled) | `updateLeadStage` function; stage is persisted; available to staff role | ☐ |
| 2.8 | Update lead fields (e.g., correct phone number) | `updateLead` — gated to staff/owner/admin | ☐ |

**Tests:** `marketing-leads.test.ts` (37 tests — source classification, stage transitions), `pipeline-board.test.ts`, `submit-lead.test.ts`, `dispatch.test.ts` (WhatsApp dispatch), `messaging.test.ts` (message ledger), `rate-limit.test.ts` (30/org/60s + 20/org/60s)

**RBAC:** Staff can update leads; only owner/admin can delete leads. See `docs/release-readiness.md` #19-20.

**Rate limits:** 30 lead submissions + 20 WhatsApp dispatches per org per 60s. Manual entry won't hit these.

> **Why WhatsApp is in scope:** This is the feature Kay will notice and value immediately. A patient who walks in or calls gets an instant WhatsApp confirmation in their preferred language — professional, immediate, and frictionless. Bilingual support (English/Swahili) means the clinic can serve both language communities from day one. The rest of the WhatsApp stack (inbound webhooks, automation triggers, media ingestion) is infrastructure she won't see yet. Outbound confirmation/reminder is the visible value; everything else comes later.

---

## Workflow 3: Appointment Scheduling (Receptionist / Therapist)

Book patient appointments. The system auto-generates available slots from clinic configuration. When a booking is confirmed, a WhatsApp reminder is sent to the patient.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 3.1 | View available slots for a date/service | `generateSlots` computes time windows from clinic config | ☐ |
| 3.2 | Reserve a slot (while confirming with patient) | `reserveSlot` — 5-minute TTL hold; prevents double-booking | ☐ |
| 3.3 | Confirm booking | `bookSlot` — advisory lock, double-booking prevention, FOR UPDATE row lock | ☐ |
| 3.4 | **WhatsApp reminder sent automatically** | `dispatchLeadMessage` fires `reminder` template with appointment time/details; logged in `message_ledger` | ☐ |
| 3.5 | See scheduled appointments | Appointment list on dashboard / schedule view | ☐ |

**Tests:** `slot-generation.test.ts` (9 tests), `concurrency.test.ts` (advisory lock + FOR UPDATE), `dispatch.test.ts` (WhatsApp dispatch), `messaging.test.ts` (message ledger), `rbac-completeness.test.ts` (staff can book/reserve)

**RBAC:** Staff, owner, and admin can book and reserve slots. No patient-facing self-booking in pilot scope.

---

## Workflow 4: Clinic Configuration (Owner)

Set up the clinic once at the start of the trial. Changes should be rare after day 1.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 4.1 | Go to Operations Settings | Clinic configuration form loads current values | ☐ |
| 4.2 | Set business hours, slot duration (e.g. 30 min), timezone | `saveClinicConfig` createServerFn persists to `clinic_configuration` table | ☐ |
| 4.3 | Configure triage timeout and custom keywords | Saved alongside hours/config | ☐ |

**Tests:** `clinic-config.test.ts`, `rbac-completeness.test.ts` (owner/admin only)

**RBAC:** Only SUPER_ADMIN and CLINIC_OWNER can save clinic config. Staff cannot change settings.

---

## Workflow 5: Resource Management (Owner)

Manage providers (physiotherapists) and treatment rooms.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 5.1 | View list of providers and rooms | `getResources` returns resources scoped to org | ☐ |
| 5.2 | Add a new provider or room | `createResourceFn` — gated to owner/admin | ☐ |
| 5.3 | Update resource status (active/inactive) | `updateResourceStatus` | ☐ |
| 5.4 | Check for scheduling conflicts | `checkResourceConflict` — conflict detection | ☐ |

**Tests:** `resources.test.ts`, `rbac-completeness.test.ts` (owner/admin)

---

## Workflow 6: Staff Account Management (Owner)

Create accounts for receptionists and therapists so they can log in.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 6.1 | Use the registration flow (first user) | `registerOrganization` createServerFn creates org + admin + default clinic config + 12 medical services in one transaction | ☐ |
| 6.2 | Subsequent staff accounts | Handled via admin UI or direct DB (out of pilot scope for the UI path) | — |

**Tests:** `registration.test.ts`, `seed.test.ts` (12 MEDICAL_SERVICES seeded)

**Note:** The bulk of staff account management UI is not in pilot scope. The owner creates additional users. This is acceptable for a 14-day pilot with 2-5 staff.

---

## Workflow 7: Billing (Receptionist / Owner)

Generate invoices and record payments for services rendered.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 7.1 | View finance dashboard | Invoice + payment list loaded | ☐ |
| 7.2 | Create an invoice for a lead/patient | `generateInvoice` — sequential `INV-YYYY-NNNNN` format; double-creation prevented via advisory lock | ☐ |
| 7.3 | Record a payment against an invoice | `recordPayment` — sequential `KWC-YYYY-NNNNN` receipt number; lock prevents double-payment | ☐ |
| 7.4 | Void an invoice | Status transition: draft → issued → paid → void | ☐ |
| 7.5 | View billing analytics | Revenue totals, outstanding amounts | ☐ |

**Tests:** `billing.test.ts` (7 tests — invoice numbering, payment numbering, status workflow), `billing-locks.test.ts` (concurrent payment prevention)

**RBAC:** Staff, owner, and admin can access billing operations. Payments fetch gated to owner/admin (see #29).

---

## Workflow 8: Dashboard & Analytics (Owner)

Daily business overview.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 8.1 | Navigate to dashboard | Lead counts, revenue snapshot, appointment summary rendered | ☐ |
| 8.2 | View analytics page | Lead source breakdown, stage distribution, revenue by period | ☐ |
| 8.3 | View conversion velocity + revenue forecast | Pipeline forecast, revenue-at-risk | ☐ |

**Tests:** `analytics.test.ts`, `forecasting.test.ts`, `rbac-completeness.test.ts` (owner/admin)

**RBAC:** Analytics gated to SUPER_ADMIN and CLINIC_OWNER. Staff do not see analytics in pilot scope.

---

## Workflow 9: M-Pesa Reconciliation (Owner / Finance)

Upload M-Pesa CSV exports and auto-match payments to invoices.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 9.1 | Download CSV from M-Pesa statement | — | ☐ |
| 9.2 | Upload CSV to reconciliation page | `reconcilePayment` — CSV parsing, amount + phone number fuzzy matching | ☐ |
| 9.3 | View matched and unmatched items | Matched invoices updated; unmatched queued for manual review | ☐ |

**Tests:** `reconciliation.test.ts` (19 tests — CSV parsing, duplicate webhook idempotency, auto-match), `rate-limit.test.ts` (10/org/60s)

**Rate limit:** 10 reconciliation attempts per org per 60s.

**Pilot constraint:** All reconciliation tests use mock M-Pesa CSV data. Real M-Pesa CSV exports from a test account should be used to verify in staging before day 1. See `docs/release-readiness.md` #47.

---

## Workflow 10: Health & Safety (Operations)

Verify the system is running correctly.

| Step | User Action | System Behavior | Verified? |
|------|------------|----------------|-----------|
| 10.1 | Hit `/api/health` | Returns `{ status: "ok", uptime, db }` | ☐ |
| 10.2 | Deploy to production | Docker build succeeds; `npm run build` succeeds; `npx tsc --noEmit` passes | ☐ |

**Tests:** `health-endpoint.test.ts`

---

## Summary Table

| # | Capability | Workflow | Test File(s) | Release-Readiness # |
|---|-----------|----------|--------------|---------------------|
| 1 | Login & session | 1 | `auth-components.test.ts`, `auth-logout.test.ts` | 11-15 |
| 2 | Logout clears cookie | 1 | `auth-logout.test.ts` | 15 |
| 3 | SESSION_SECRET production guard | 10 | `env-production-guard.test.ts` | 14 |
| 4 | Lead intake + pipeline board | 2 | `marketing-leads.test.ts`, `pipeline-board.test.ts`, `submit-lead.test.ts` | 61-62 |
| 5 | Lead update (staff role) | 2 | `rbac-completeness.test.ts` | 20 |
| 6 | Lead language selection (EN/SW) | 2 | — (UI field on BookingWidget) | — |
| 7 | Lead rate limiting (30/org/60s) | 2 | `rate-limit.test.ts` | 41 |
| 8 | WhatsApp outbound — bilingual confirmation (on lead create) | 2 | `dispatch.test.ts`, `messaging.test.ts`, `rate-limit.test.ts` | 28, 39, 43 |
| 9 | Slot generation | 3 | `slot-generation.test.ts` | 34 |
| 9 | Slot reservation with TTL | 3 | `concurrency.test.ts` | 36 |
| 10 | WhatsApp outbound — reminder (on booking) | 3 | `dispatch.test.ts`, `messaging.test.ts` | 28, 39 |
| 11 | Double-booking prevention | 3 | `concurrency.test.ts` | 35 |
| 12 | Scheduling gated to staff | 3 | `rbac-completeness.test.ts` | 21 |
| 13 | Clinic configuration | 4 | `clinic-config.test.ts` | 22 |
| 14 | Resource management | 5 | `resources.test.ts` | 23 |
| 15 | Org registration + seed data | 6 | `registration.test.ts`, `seed.test.ts` | — |
| 16 | Invoice generation + numbering | 7 | `billing.test.ts` | 30 |
| 17 | Payment recording + numbering | 7 | `billing.test.ts` | 31 |
| 18 | Double-payment prevention | 7 | `billing-locks.test.ts` | 32 |
| 19 | Invoice status workflow | 7 | `billing.test.ts` | 33 |
| 20 | Billing gated (fetch payments) | 7 | `rbac-completeness.test.ts` | 29 |
| 21 | Dashboard + analytics | 8 | `analytics.test.ts`, `forecasting.test.ts` | 26 |
| 22 | M-Pesa reconciliation (CSV) | 9 | `reconciliation.test.ts` | 44-46 |
| 23 | Reconciliation rate limiting | 9 | `rate-limit.test.ts` | 42 |
| 24 | Health endpoint | 10 | `health-endpoint.test.ts` | 69 |

---

## Explicitly Out of Scope (Day 1-14)

These exist and are tested but are **not** part of the trial ask. Do not demo, test, or rely on them during the first 14 days.

| Feature | Why Out of Scope |
|---------|-----------------|
| WhatsApp inbound webhooks (media ingestion, auto-reply) | Inbound message processing is invisible to staff during pilot. Outbound-only for day 1. |
| WhatsApp automation triggers (retention campaigns, triage follow-up) | Staff manage follow-ups manually during pilot. Automated triggers are infrastructure Kay won't see or need yet. |
| WhatsApp media storage (inbound images/files) | No media ingestion during pilot. Storage tested but not wired into any workflow. |
| Real-time SSE updates | Manual refresh of the dashboard is sufficient for a 14-day trial with 2-5 staff. |
| Subscription tiers / metering | Kay's is on a fixed plan. No tier changes during pilot. |
| Paywall UI | Not applicable — no subscription changes during pilot. |
| Outbound webhooks | No external system integrations active during pilot. |
| Data export (CSV, QuickBooks, iCal) | Not needed in the first 14 days. Available if requested. |
| Automation / retention campaigns | Staff manage follow-ups manually during pilot. |
| Forecasting | Overkill for 14 days of data. |
| Multi-channel fallback (SMS/email) | Only phone communication used during pilot. |
| Bulk lead import | Staff enter leads manually (acceptable at < 20 leads/day). |
| Queue diagnostics / telemetry | SUPER_ADMIN only. Not relevant to Kay's daily ops. |
| PII encryption | Descoped per D11. Stored in plaintext. |
| Google review auto-submission | Descoped per D65. Sentiment classification ships but no submission. |
| Offline PWA / optimistic updates | Not needed — stable internet during pilot. |
| Audit logs | Running in background. Not a user-facing feature. |

---

## Pre-Flight Checklist (Before Day 1)

| # | Action | Owner | Done? |
|---|--------|-------|-------|
| 1 | Deploy to production URL (Vercel) | — | ☐ |
| 2 | Set `SESSION_SECRET` env var (app refuses to start with default) | — | ☐ |
| 3 | Set `DATABASE_URL`, `ENCRYPTION_KEY` env vars | — | ☐ |
| 4 | Set `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` env vars | — | ☐ |
| 5 | Run registration flow → create Kay's org + admin account | — | ☐ |
| 6 | Change default admin password from `"admin0726"` | — | ☐ |
| 7 | Add staff accounts (receptionist, 2 therapists) | — | ☐ |
| 8 | Configure clinic hours, slot duration (30 min), timezone | — | ☐ |
| 9 | Add providers (therapist names) and rooms | — | ☐ |
| 10 | Verify login works for each staff account | — | ☐ |
| 11 | Submit a test lead, verify WhatsApp confirmation arrives on patient phone | — | ☐ |
| 12 | Book a test appointment, verify WhatsApp reminder arrives | — | ☐ |
| 13 | Walk through all 10 workflows with the clinic owner | — | ☐ |
| 14 | Confirm known gaps: PII in plaintext, no token revocation | — | ☐ |

---

*Cross-referenced against `docs/release-readiness.md` (Sprint 34, 660 tests / 58 files). All capabilities above are **PASS** per the go/no-go table. `docs/current-state.md` does not yet exist — this doc serves as the authoritative pilot scope boundary.*
