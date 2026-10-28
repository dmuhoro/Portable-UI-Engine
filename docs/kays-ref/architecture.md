# Architecture — Kay's Wellness Centre SaaS

> Auto-generated from source code. All claims verified against `src/` as of Sprint 41.

---

## 1. Stack

| Layer | Technology |
|-------|-----------|
| Framework | TanStack Start + TanStack Router (`@tanstack/react-start` v1.131.0) |
| Runtime | Vite + Nitro (preset: `vercel`) |
| Database | PostgreSQL via `postgres` v3.4.5 (raw `db.unsafe(sql, params)` — no ORM) |
| Styling | Tailwind CSS v4.1.6 |
| Validation | Zod v4.1.11 (schema definitions shared across client + server) |
| State | TanStack Query + TanStack Router stores + URL search params |
| Hosting | Vercel (`vercel.json` — security headers + immutable asset caching only) |

---

## 2. Request Lifecycle

```
Browser request
    ↓
src/routes/__root.tsx          ← Root layout: <Navbar>, <CommandPalette>, <SonnerToaster>
    ↓
TanStack Router                ← File-based route matching (src/routes/*.tsx)
    ↓
Client component               ← Calls createServerFn(...) handlers via useServerFn/useMutation
    ↓
TanStack Start server handler  ← Serialised function body + JSON input
    ↓
createServerFn handler         ← Actual server function (src/lib/*.server.ts files)
    ↓
requireOrg()                   ← Extracts orgId from kwc_session JWT cookie → { orgId, requestId, log }
    ↓
getDb()                        ← Returns postgres connection (from db.server.ts getDb())
    ↓
db.unsafe(sql, params)         ← Raw parameterised queries (no ORM layer)
    ↓
Response serialized back       ← JSON to client, TanStack Query caches
```

Key pattern: **every `createServerFn` handler independently calls `requireOrg()` to obtain the tenant-scoped `orgId`**, which must be explicitly bound in every SQL query. There is no global middleware that automatically injects tenant scope.

---

## 3. Server Files — One-Liner Reference

### Core Infrastructure (`src/lib/`)

| File | Purpose | Line reference |
|------|---------|----------------|
| `db.server.ts` | Postgres connection pool, `getDb()`, `withDb()`, `getConcurrentLock()`/`releaseConcurrentLock()`, `ensureSchema()` with full DDL (all table definitions live here) | `db.server.ts` |
| `env.server.ts` | Zod-validated env schema — `DATABASE_URL`, `SESSION_SECRET`, `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `ENCRYPTION_KEY` | `env.server.ts` |
| `config.server.ts` | Thin `getServerConfig()` wrapper — reads raw `process.env` (not `env.server.ts` Zod-validated) | `config.server.ts:12` |
| `logger.server.ts` | Structured logger with 50+ named event constants, `startTimer()`, `sanitizeMetadata()` (masks sensitive fields) | `logger.server.ts` |

### Auth & Tenant Isolation (`src/lib/`)

| File | Purpose |
|------|---------|
| `auth.server.ts` | `hashPassword()`, `verifyPassword()`, `login()` (createServerFn), `seedDefaultOrgAndAdmin()` — auto-seeds default org on first login |
| `auth-check.server.ts` | `getCurrentSession()` createServerFn — returns `{ userId, orgId, role, exp }` from cookie |
| `session.server.ts` | HMAC-signed base64url JWT stored in `kwc_session` cookie; `signToken()`, `verifyToken()`, `getSession()`, `getCurrentOrgId()`, `getCurrentUserRole()` |
| `tenant.server.ts` | `requireOrg()` — extracts `orgId` from session, throws `TenantError` if unauthenticated; returns `{ orgId, requestId, log }` |
| `permissions.server.ts` | `ROLES` constants (`super_admin`=100, `admin`=50, `staff`=10), `roleAtLeast()`, `requireRole()`, `canAccessFinance()`, `canAccessDataExport()`, `canDeleteData()` |

### Subscription & Metering (`src/lib/`)

| File | Purpose |
|------|---------|
| `subscriptions.server.ts` | Tier definitions (`starter`/`growth`/`enterprise`), `getOrgSubscription()`, `checkFeatureAccess()` |
| `metering.server.ts` | Usage tracking (leads, storage, users) against tier limits, `getUsageSnapshot()`, `checkQuota()`, `refreshUsageCounters()` |
| `trials.server.ts` | 14-day trial management — `getTrialStatus()`, `evaluateTrialAccess()` |
| `checkout.server.ts` | Checkout session lifecycle, payment provider webhook handlers |
| `billing.server.ts` | *(api/ version)* Invoice and payment CRUD with `INV-YYYY-NNNNN` / `KWC-YYYY-NNNNN` sequential numbering under `getConcurrentLock()` |

### Messaging & Queue (`src/lib/`)

| File | Purpose |
|------|---------|
| `messaging.server.ts` | `logMessage()` into `message_ledger`, `updateMessageStatus()`, `getConversationHistory()`, `getMessageStats()` |
| `queue.server.ts` | `enqueueNotification()`, `processQueue(batchSize, tenantId?)`, `processNotifications()` — background notification queue with idempotency keys |
| `fallback.server.ts` | Circuit-breaker channel fallback (webhook → whatsapp → sms) |
| `dispatch.server.ts` | *(api/ version)* `sendWhatsApp()` — direct Facebook Graph API call with `AbortSignal.timeout(10s)`, `formatMessage()` template helpers, `dispatchLeadMessage` createServerFn |
| `notifications.server.ts` | `triggerQueueProcessing` createServerFn — thin wrapper around `processNotifications()` |

### Integrations (`src/lib/`)

| File | Purpose |
|------|---------|
| `encryption.server.ts` | AES-256-GCM PII encryption with per-org derived keys via PBKDF2; `encryptPII()`, `decryptPII()`, `getKeyByVersion()`, `rotateOrgKey()` |
| `webhooks.server.ts` | `registerWebhook()`, `deliverWebhook()` with HMAC-SHA256 signing, retry with exponential backoff, circuit breaker |
| `event-bus.server.ts` | `publishEvent()` inserts into `live_events` table, `getRecentEvents()` for SSE long-polling |
| `audit.server.ts` | `recordAudit()` inserts into `audit_logs` table |
| `storage.server.ts` | Local filesystem file storage with org-scoped directories |

### Lead Pipeline (`src/lib/marketing/`)

| File | Purpose |
|------|---------|
| `leads.server.ts` | `createInboundLead()`, `getLeadPipeline()`, `updateLeadStage()`, `getLeadActivity()`, `getLeadSourceStats()` — full pipeline board with stage transitions (new → contacted → scheduled → checked_in → converted / lost) |
| `automation.server.ts` | Retention automation — `computeRetentionScores()`, `scheduleRetentionTask()`, `getEmptySlotCandidates()`, `generateRetentionCampaign()` — channels: whatsapp/sms/email |
| `reviews.server.ts` | Satisfaction & reputation — `sendSatisfactionPrompt()`, `processFeedbackResponse()`, `getReputationMetrics()`, `getReviewGuardConfig()` — NPS tracking, review gate before public review link |

### API Layer (`src/lib/api/`)

| File | Purpose |
|------|---------|
| `leads.server.ts` | `submitLead` (POST), `fetchLeads` (GET), `updateLeadStatus`, `deleteLead` — full CRUD for lead management |
| `billing.server.ts` | `generateInvoice`, `recordPayment`, `createInvoice` createServerFn — invoice + payment lifecycle with concurrent locks |
| `automation.server.ts` | `ensureAutomationState`, `updateAutomationStage`, `getLeadsNeedingFollowup`, `processAutomationBatch` — automation state machine |
| `dispatch.server.ts` | `dispatchLeadMessage` createServerFn — WhatsApp dispatch with message templates (confirmation, triage_followup, reminder) |
| `registration.server.ts` | `registerOrganization` createServerFn — org + admin user + default clinic config, provider/room resources and weekly availability in a single registration handler |
| `contact.server.ts` | `submitContactMessage` createServerFn (+ `ingestContactMessage` core) — **anonymous** public "Send us a message" intake; resolves the public org by slug (`PUBLIC_ORG_SLUG`, default `kays-wellness`) fail-closed, rate-limits per email, encrypts PII, writes `status='new'` channel `web_form` |
| `analytics.server.ts` | `getAnalytics` createServerFn — thin wrapper around `computeAnalytics()` |
| `resources.server.ts` | `getResources`, `createResource`, `updateResourceStatus`, `checkResourceConflict` — provider/room CRUD with conflict detection |
| `clinic-config.server.ts` | `getClinicConfig`, `updateClinicConfig` createServerFn — business hours, slot duration, triage timeout, custom keywords, timezone |
| `subscription.server.ts` | `getSubscription`, `getUsage`, `checkLeadQuota`, `checkStorageQuota` createServerFn — tier + usage queries |
| `notifications.server.ts` | `triggerQueueProcessing` createServerFn — manual queue drain endpoint |
| `diagnostics.server.ts` | `getServerStatus`, `getQueueTelemetry`, `forceRetryQueueItems`, `getFailedQueueItems` — **queue/diagnostics/retry functions gated behind `requireRole(ROLES.SUPER_ADMIN)`** |
| `interactions.server.ts` | `logInteraction`, `getLeadsWithPendingReplies` — org-scoped with correlated subquery (P0-1 fix) |
| `scheduling.server.ts` | `bookSlot` createServerFn — appointment booking with param-indexed UPDATE, lock-then-release pattern |

### Supporting Services (`src/lib/`)

| File | Purpose |
|------|---------|
| `analytics.server.ts` | `computeAnalytics()` — per-tenant lead/revenue metrics with source/stage breakdowns |
| `forecasting.server.ts` | `computeConversionVelocity()`, `computeRevenueAtRisk()`, `computePipelineForecast()` |
| `exports.server.ts` | `exportLeadsCsv` createServerFn — date-range filtered CSV export with audit logging |
| `financial-exports.server.ts` | QuickBooks/Xero CSV export with currency conversion |
| `reconciliation.server.ts` | M-Pesa/bank payment CSV parsing + auto-matching to invoices via fuzzy string + amount matching |
| `telemetry.server.ts` | Milestone tracking — `trackUserMilestone()`, `hasMilestone()`, **`getMilestoneStats()` gated behind `requireRole(ROLES.SUPER_ADMIN)`** |
| `import.server.ts` | `bulkImportLeads` createServerFn — CSV import |
| `seed.server.ts` | Static seed data — `MEDICAL_SERVICES` (12 items), `TRIAGE_SCRIPTS`, `MESSAGE_TEMPLATES` |

---

## 4. Auth Flow

```
1. User submits email + password
        ↓
2. auth.server.ts: login() createServerFn
        ↓
3. db.unsafe('SELECT ... FROM users WHERE email = $1', [email])
        ↓
4. verifyPassword(password, password_hash)
        ↓
5. signToken({ userId, orgId, role, exp })        ← session.server.ts
        ↓
6. setCookie('kwc_session', jwt, { httpOnly, secure, sameSite: 'lax', path: '/' })
        ↓
7. On subsequent requests: getSession()
        ↓
8. verifyToken(cookie) → { userId, orgId, role, exp }
        ↓
9. requireOrg() reads session → returns { orgId, requestId, log }
        ↓
10. requireRole(ROLES.ADMIN) checks role hierarchy → throws TenantError on failure
```

**Key properties:**
- JWT is HMAC-signed (`SESSION_SECRET`), stored as base64url in `httpOnly` cookie
- No refresh token — single-day expiry (`TOKEN_EXPIRY_MS = 86_400_000`)
- `seedDefaultOrgAndAdmin()` auto-runs on first login attempt if no users exist
- Role hierarchy: `super_admin` (100) > `admin` (50) > `staff` (10)

---

## 5. Tenant Isolation Pattern

Every `createServerFn` handler must:

```ts
const { orgId, log } = requireOrg();            // step 1: extract tenant
const db = await getDb();
const rows = await db.unsafe(
  `SELECT ... WHERE organization_id = $1`,       // step 2: bind orgId in every query
  [orgId, ...otherParams],
);
```

There is **no automatic tenant scoping** — each query must explicitly include `organization_id = $N`. This was the root cause of all 5 P0 SQL leak vulnerabilities fixed in this sprint.

**Fixed P0 issues (Sprint 34):**
- `interactions.server.ts:91` — correlated subquery in `getLeadsWithPendingReplies` was missing org filter
- `queue.server.ts:172` — `processQueue()` had no `tenantId` parameter; tenant scope was not passed to the batch SELECT
- `diagnostics.server.ts` — `getQueueTelemetry()`, `forceRetryQueueItems()`, `getFailedQueueItems()` were callable by any authenticated user without role check
- `telemetry.server.ts` — `getMilestoneStats()` was callable by any authenticated user without role check
- `scheduling.server.ts:240` — `bookSlot()` UPDATE used `${}` string interpolation for user-supplied values (SQL injection) and param array was silently truncated

---

## 6. Database Schema

All table DDL lives in `db.server.ts:ensureSchema()`. Key tables:

| Table | Tenant-scoped | Purpose |
|-------|:---:|---------|
| `organizations` | — | Org metadata, slug, timezone, settings |
| `users` | ✅ | Org users with role + password hash |
| `clinic_leads` | ✅ | Lead records with name, phone, email, service, channel, priority, status, appointment_timestamp, provider_id, room_id |
| `invoices` | ✅ | Financial documents linked to leads |
| `payments` | ✅ | Payment records against invoices |
| `message_ledger` | ✅ | All outbound message logs |
| `queue_notifications` | ✅ | Pending notification queue with idempotency keys |
| `automation_state` | ✅ | Per-lead automation stage machine |
| `satisfaction_prompts` | ✅ | NPS/feedback prompt tracking |
| `feedback_responses` | ✅ | Customer feedback + NPS scores |
| `review_submissions` | ✅ | Public review submission tracking |
| `clinic_configuration` | ✅ | Business hours, slot duration, triage timeout, custom keywords |
| `resources` | ✅ | Providers and rooms |
| `subscriptions` | ✅ | Org tier + status + expiry |
| `usage_counters` | ✅ | Monthly usage tracking per metered dimension |
| `webhook_registrations` | ✅ | Registered webhook endpoints |
| `live_events` | ✅ | Event bus for SSE real-time updates |
| `audit_logs` | ✅ | Audit trail for all mutations |
| `milestones` | ✅ | User milestone tracking |
| `org_api_keys` | ✅ | Per-org encryption key versions |
| `encryption_keys` | ✅ | AES-256-GCM key material per org |

---

## 7. Route Structure

### Public Routes (`src/routes/`)

| Route | File | Purpose |
|-------|------|---------|
| `/` | `index.tsx` | Landing page |
| `/services` | `services.tsx` | Service catalogue |
| `/our-story` | `our-story.tsx` | About page |
| `/resources` | `resources.tsx` | Public resource listing |
| `/contact` | `contact.tsx` | Contact form |
| `/register` | `register.tsx` | New org registration |
| `/privacy-policy` | `privacy-policy.tsx` | Privacy policy |
| `/terms` | `terms.tsx` | Terms of service |

### Admin Routes (`src/routes/admin/`)

| Route | File | Purpose |
|-------|------|---------|
| `/admin/login` | `admin/login.tsx` | Login page |
| `/admin/dashboard` | `admin/dashboard.tsx` | Main dashboard |
| `/admin/triage` | `admin/triage.tsx` | Lead triage queue |
| `/admin/finance` | `admin/finance.tsx` | Invoicing + payments |
| `/admin/diagnostics` | `admin/diagnostics.tsx` | System diagnostics (admin) |
| `/admin/settings/billing` | `admin/settings/billing.tsx` | Subscription & billing |
| `/admin/settings/operations` | `admin/settings/operations.tsx` | Clinic configuration |
| `/admin/settings/data` | `admin/settings/data.tsx` | Data export/import |
| `/admin/settings/developer` | `admin/settings/developer.tsx` | API keys & developer tools |
| `/admin/system/diagnostics` | `admin/system/diagnostics.tsx` | System-level diagnostics |

---

## 8. Build & Deploy

| Aspect | Detail |
|--------|--------|
| Build command | Vite + `@lovable.dev/vite-tanstack-config` |
| Deploy target | Vercel (Nitro `vercel` preset) |
| `vercel.json` | Security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`) + immutable asset caching (`_next/static/**`) |
| CI/CD | **CI present** — `.github/workflows/ci.yml` runs `npm ci && npm test` on push/PR to `main`; `.github/workflows/deploy.yml` handles deploy |
| Env vars required | `DATABASE_URL`, `SESSION_SECRET`, `ENCRYPTION_KEY`, `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |

---

## 9. Known Gaps

Gap rows are **open only if the claim still holds against `src/`**. Rows that were fixed since Sprint 34 are listed at the bottom as resolved, with evidence.

| Gap | Current Status | Evidence | Severity |
|-----|---------------|----------|----------|
| `config.server.ts` reads raw `process.env`, bypassing `env.server.ts` Zod validation | **Still open.** Thin `getServerConfig()` wrapper; currently exposes only `nodeEnv`, no secrets travel through it | `config.server.ts:19-25` | Low |
| No CSRF protection on `createServerFn` POST beyond `sameSite: 'lax'` | **Still open.** No Origin / Sec-Fetch-Site header enforcement exists on any server function | session cookie set with `sameSite: 'lax'` (`session.server.ts` / `auth.server.ts`) | Low |
| `processQueue()` default branch runs unscoped when `tenantId` omitted | **Still open, call-site mitigated.** The default batch SELECT omits the tenant filter; the only production caller (`processNotifications`) enumerates distinct `tenant_id` rows and passes `tenantId` per batch, and `triggerQueueProcessing` is gated to `SUPER_ADMIN` | `queue.server.ts:202-240`; release-readiness rows #6, #25 | Low |
| No idempotency on `registerOrganization` | **Still open.** Slug/email pre-checks are racy — a concurrent double-submit can race past the SELECT before the INSERT completes | `registration.server.ts:39-55` | Low |
| ~~No CI pipeline~~ | **Resolved.** `ci.yml` runs `npm ci && npm test` on push/PR to `main`; `deploy.yml` deploys | `.github/workflows/ci.yml`; release-readiness row #70 | — |
| ~~No rate limiting on `login()`~~ | **Resolved.** `checkRateLimit(login:${email}, 5, 60_000)` rejects brute-force attempts | `auth.server.ts:114`; release-readiness row #40 | — |

---

## 10. Test Infrastructure

| File | Tests | Focus |
|------|-------|-------|
| `src/__tests__/e2e-simulation.test.ts` | 15 | Full flow simulation: registration → lead → invoice → payment → queue |
| `src/__tests__/tenant-isolation-p0.test.ts` | 18 | Adversarial tests for all 5 P0 SQL leak fixes |
| `src/__tests__/scheduling-injection.test.ts` | 5 | SQL injection fix, param indexing, lock release |
| `src/__tests__/encryption.test.ts` | 8 | AES-256-GCM encrypt/decrypt, key rotation, dual-cache |
| `src/__tests__/reconciliation.test.ts` | 7+ | Payment auto-matching adversarial scenarios |
| `src/__tests__/queue-diagnostics.test.ts` | — | Queue diagnostics with SUPER_ADMIN role gate |
| `src/__tests__/telemetry.test.ts` | — | Milestone tracking with SUPER_ADMIN role gate |

**Total: 743 tests across 70 files (all passing as of Sprint 41) — see `npm test` and `tests/e2e/` (Playwright smoke against the production build) for the authoritative, always-current picture.**

---

*Last updated: Sprint 41 — Tier 4 Release Polish*
